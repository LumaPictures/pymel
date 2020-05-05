"""
Maya-related functions, which are useful to both `api` and `core`, including `mayaInit` which ensures
that maya is initialized in standalone mode.
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import zip
from builtins import object
import os.path
import sys
import glob
import inspect
import pprint
import maya
import maya.OpenMaya as om
import maya.utils

import pymel.util
import pymel.util.py2to3 as util2to3

from pymel.util import picklezip, shellOutput, subpackages, refreshEnviron, universalmethod
from collections import namedtuple
import pymel.versions as versions
from pymel.mayautils import getUserPrefsDir
from pymel.versions import shortName, installName
from . import plogging

from future.utils import PY2

# There are FOUR different ways maya might be started, all of which are
# subtly different, that need to be considered / tested:
#
# 1) Normal gui
# 2) maya -prompt
# 3) Render
# 4) mayapy (or just straight up python)

_logger = plogging.getLogger(__name__)
try:
    import pickle as pickle
except:
    _logger.warning("using pickle instead of cPickle: load performance will be affected")
    import pickle

#from maya.cmds import encodeString

isInitializing = False
# Setting this to False will make finalize() do nothing
finalizeEnabled = True
_finalizeCalled = False

_mayaExitCallbackId = None
_mayaUninitialized = False
_atExitCallbackInstalled = False


def _moduleJoin(*args):
    """
    Joins with the base pymel directory.
    :rtype: string
    """
    moduleDir = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))
    return os.path.realpath(os.path.join(moduleDir, *args))


def mayaStartupHasRun():
    """
    Returns True if maya.app.startup has already finished, False otherwise.
    """
    return 'maya.app.startup.gui' in sys.modules or 'maya.app.startup.batch' in sys.modules


def mayaStartupHasStarted():
    """
    Returns True if maya.app.startup has begun running, False otherwise.

    It's possible that maya.app.startup is in the process of running (ie,
    in maya.app.startup.basic, calling executeUserSetup) - unlike mayaStartup,
    this will attempt to detect if this is the case.
    """
    return hasattr(maya, 'stringTable')


def setupFormatting():
    import pprint
    import maya.utils

    def myResultCallback(obj):
        return pprint.pformat(obj)
    maya.utils.formatGuiResult = myResultCallback
    # prevent auto-completion generator from getting confused
    maya.utils.formatGuiResult.__module__ = 'maya.utils'

# def loadDynamicLibs():
#    """
#    due to a bug in maya.app.commands many functions do not return any value the first time they are run,
#    especially in standalone mode.  this function forces the loading of all dynamic libraries, which is
#    a very fast and memory-efficient process, which begs the question: why bother dynamically loading?
#
#    this function can only be run after maya.standalone is initialized
#    """
#
#    commandListPath = os.path.realpath( os.environ[ 'MAYA_LOCATION' ] )
#    commandListPath = os.path.join( commandListPath, libdir, 'commandList' )
#
#    import maya.cmds
#    assert hasattr( maya.cmds, 'dynamicLoad'), "maya.standalone must be initialized before running this function"
#    file = open( commandListPath, 'r' )
#    libraries = set( [ line.split()[1] for line in file] )
#    for library in libraries:
#        try:
#            maya.cmds.dynamicLoad(library)
#        except RuntimeError:
#            _logger.debug("Error dynamically loading maya library: %s" % library)

# Will test initialize maya standalone if necessary (like if scripts are run from an exernal interpeter)
# returns True if Maya is available, False either


def mayaInit(forversion=None):
    global _mayaUninitialized
    _mayaUninitialized = False

    result = _mayaInit(forversion=forversion)

    if om.MGlobal.mayaState() == om.MGlobal.kLibraryApp:  # mayapy only
        if pymel_options['fix_mayapy_segfault']:
            fixMayapySegFault()

    return result


def _mayaInit(forversion=None):
    # type: (Any) -> bool
    """ Try to init Maya standalone module, use when running pymel from an external Python inerpreter,
    it is possible to pass the desired Maya version number to define which Maya to initialize


    Part of the complexity of initializing maya in standalone mode is that maya does not populate os.environ when
    parsing Maya.env.  If we initialize normally, the env's are available via maya (via the shell), but not in python
    via os.environ.

    Note: the following example assumes that MAYA_SCRIPT_PATH is not set in your shell environment prior to launching
    python or mayapy.

    >>> import maya.standalone            #doctest: +SKIP
    >>> maya.standalone.initialize()      #doctest: +SKIP
    >>> import maya.mel as mm             #doctest: +SKIP
    >>> print(mm.eval("getenv MAYA_SCRIPT_PATH"))    #doctest: +SKIP
    /Network/Servers/sv-user.luma-pictures.com/luma .....
    >>> import os                         #doctest: +SKIP
    >>> 'MAYA_SCRIPT_PATH' in os.environ  #doctest: +SKIP
    False

    The solution lies in `refreshEnviron`, which copies the environment from the shell to os.environ after maya.standalone
    initializes.

    Returns
    -------
    bool
        returns True if maya.cmds required initializing ( in other words, we are in a standalone python interpreter )

    """
    _logger.debug("startup.mayaInit: called")
    setupFormatting()

    global isInitializing

    # test that Maya actually is loaded and that commands have been initialized,for the requested version

    aboutExists = False
    try:
        from maya.cmds import about
        aboutExists = True
    except ImportError:
        pass

    if aboutExists and mayaStartupHasStarted():
        # if this succeeded, we're initialized
        _logger.debug("startup.mayaInit: maya already started - exiting")
        isInitializing = False
        return False

    _logger.debug("startup.mayaInit: running")

    # for use with pymel compatible maya package
    oldSkipSetup = os.environ.get('MAYA_SKIP_USERSETUP_PY')
    os.environ['MAYA_SKIP_USERSETUP_PY'] = 'on'
    try:
        if not aboutExists and 'maya.standalone' not in sys.modules:
            try:
                _logger.debug("startup.mayaInit: running standalone.initialize")
                import maya.standalone  # @UnresolvedImport
                maya.standalone.initialize(name="python")
            except ImportError as e:
                raise ImportError("%s: pymel was unable to intialize maya.standalone" % e)

        try:
            from maya.cmds import about
        except Exception:
            _logger.error("maya.standalone was successfully initialized, but pymel failed to import maya.cmds (or it was not populated)")
            raise
    finally:
        if oldSkipSetup is None:
            del os.environ['MAYA_SKIP_USERSETUP_PY']
        else:
            os.environ['MAYA_SKIP_USERSETUP_PY'] = oldSkipSetup

    if not mayaStartupHasRun():
        _logger.debug("running maya.app.startup")
        # If we're in 'maya -prompt' mode, and a plugin loads pymel, then we
        # can have a state where maya.standalone has been initialized, but
        # the python startup code hasn't yet been run...
        if about(batch=True):
            import maya.app.startup.batch
        else:
            import maya.app.startup.gui

    # return True, meaning we had to initialize maya standalone
    isInitializing = True
    return True


def initMEL():
    if 'PYMEL_SKIP_MEL_INIT' in os.environ or pymel_options.get('skip_mel_init', False):
        _logger.info("Skipping MEL initialization")
        return

    _logger.debug("initMEL")
    mayaVersion = versions.installName()
    prefsDir = getUserPrefsDir()
    if prefsDir is None:
        _logger.error("could not initialize user preferences: MAYA_APP_DIR not set")
    elif not os.path.isdir(prefsDir):
        _logger.error("could not initialize user preferences: %s does not exist" % prefsDir)

    # TODO : use cmds.internalVar to get paths
    # got this startup sequence from autodesk support
    startup = [
        #'defaultRunTimeCommands.mel',  # sourced automatically
        # os.path.join( prefsDir, 'userRunTimeCommands.mel'), # sourced automatically
        'createPreferencesOptVars.mel',
        'createGlobalOptVars.mel',
        os.path.join(prefsDir, 'userPrefs.mel') if prefsDir else None,
        'initialStartup.mel',
        #$HOME/Documents/maya/projects/default/workspace.mel
        'initialPlugins.mel',
        #'initialGUI.mel', #GUI
        #'initialLayout.mel', #GUI
        # os.path.join( prefsDir, 'windowPrefs.mel'), #GUI
        # os.path.join( prefsDir, 'menuSetPrefs.mel'), #GUI
        #'hotkeySetup.mel', #GUI
        'namedCommandSetup.mel',
        os.path.join(prefsDir, 'userNamedCommands.mel') if prefsDir else None,
        #'initAfter.mel', #GUI
        os.path.join(prefsDir, 'pluginPrefs.mel') if prefsDir else None
    ]
    if pymel_options.get('skip_initial_plugins', False):
        # initialPlugins.mel is not sourced when running maya -batch, but has been included
        # in the pymel startup sequence since time immemorial. see pymel.conf for more info
        _logger.info("Skipping loading Initial Plugins")
        startup.remove('initialPlugins.mel')

    import maya.mel

    callbacks = om.MCallbackIdArray()
    toDelete = []

    # initialStartup.mel will run a `file -f -new`.  This is dangerous, for
    # obvoius resons, so we disable all file news while we run these...
    def rejectNewCallback(boolPtr_retCode, clientData):
        om.MScriptUtil.setBool(boolPtr_retCode, False)

    callbacks.append(om.MSceneMessage.addCheckCallback(
        om.MSceneMessage.kBeforeNewCheck, rejectNewCallback))

    try:
        # additionally, userPrefs.mel will apparently create a bunch of ikSolver
        # nodes (apparently just to set some global ik prefs?)
        # make sure we clean those up...
        def logIkSolverCreation(nodeObj, clientData):
            toDelete.append(om.MObjectHandle(nodeObj))

        callbacks.append(om.MDGMessage.addNodeAddedCallback(
            logIkSolverCreation, "ikSolver"))

        for f in startup:
            _logger.debug("running: %s" % f)
            if f is not None:
                if os.path.isabs(f) and not os.path.exists(f):
                    _logger.warning("Maya startup file %s does not exist" % f)
                else:
                    if PY2:
                        # need to encode backslashes (used for windows paths)
                        if isinstance(f, unicode):
                            encoding = 'unicode_escape'
                        else:
                            encoding = 'string_escape'
                        f = f.encode(encoding)
                    else:
                        # encoding to unicode_escape should add escape
                        # sequences, but also make sure everything is in basic
                        # ascii - so if we decode utf-8 (or ascii), it should
                        # give us a string which is escaped
                        f = f.encode('unicode_escape').decode('utf-8')
                    maya.mel.eval('source "%s"' % f)

    except Exception as e:
        _logger.error("could not perform Maya initialization sequence: failed "
                      "on %s: %s" % (f, e))
    finally:
        om.MMessage.removeCallbacks(callbacks)

        # clean up the created ik solvers
        dgMod = om.MDGModifier()
        for objHandle in toDelete:
            if objHandle.isValid():
                dgMod.deleteNode(objHandle.object())
        dgMod.doIt()

    try:
        # make sure it exists
        res = maya.mel.eval('whatIs "userSetup.mel"')
        if res != 'Unknown':
            maya.mel.eval('source "userSetup.mel"')
    except RuntimeError:
        pass

    _logger.debug("done running mel files")


def initAE():
    try:
        pkg = __import__('AETemplates')
    except ImportError:
        return False
    except Exception:
        import traceback
        traceback.print_exc()
        return False
    else:
        # import subpackages
        for data in subpackages(pkg):
            pass
    return True


def finalize():
    global finalizeEnabled
    global _finalizeCalled
    if not finalizeEnabled or _finalizeCalled:
        return
    _logger.debug('finalizing')
    # Set this to true HERE, as in running userSetup.py,
    # we could end up in here again, inside the initial finalize...
    _finalizeCalled = True

    global isInitializing
    if isInitializing:
        # this module is not encapsulated into functions, but it should already
        # be imported, so it won't run again
        assert 'maya.app.startup.basic' in sys.modules, \
            "something is very wrong. maya.app.startup.basic should be imported by now"
        import maya.app.startup.basic
        maya.app.startup.basic.executeUserSetup()

    state = om.MGlobal.mayaState()
    if state == om.MGlobal.kLibraryApp:  # mayapy only
        initMEL()
        if pymel_options['fix_linux_mayapy_segfault']:
            fixMayapy2011SegFault()
    elif state == om.MGlobal.kInteractive:
        initAE()


def fixMayapySegFault():
    # first, install a maya exit callback that will let us know if uninitialize
    # has already been called...
    def mayaExitCallback(data):
        global _mayaUninitialized
        _mayaUninitialized = True
        import maya.cmds
        # Turn off undo, because maya seems to have a bug where uninitialize()
        # will crash if undo is on, and certain custom conditions have been
        # created - ie, from the command line:

        # mayapy -c 'import maya.standalone
        # maya.standalone.initialize()
        # import maya.cmds as cmds
        # import maya.OpenMaya as om
        # om.MGlobal.executeCommand("""
        # global proc int _pymel_undoOrRedoAvailable()
        # {
        #     return (isTrue("UndoAvailable") || isTrue("RedoAvailable"));
        # }
        # """, False, False)
        # cmds.condition("UndoOrRedoAvailable", initialize=True,
        #                d=["UndoAvailable", "RedoAvailable"],
        #                s="_pymel_undoOrRedoAvailable")
        # cmds.setAttr("persp.tx", 20)
        # print "uninitializing..."
        # maya.standalone.uninitialize()'; echo $?
        # # Seg fault - 139
        maya.cmds.undoInfo(state=False)

    global _mayaExitCallbackId
    if _mayaExitCallbackId is not None:
        om.MMessage.removeCallback(_mayaExitCallbackId)
        if hasattr(_mayaExitCallbackId, 'disown'):
            _mayaExitCallbackId.disown()

    om.MSceneMessage.addCallback(om.MSceneMessage.kMayaExiting,
                                 mayaExitCallback)

    # Now, install a python atexit handler
    def uninitializeMayaOnPythonExit():
        if not _mayaUninitialized:
            import maya.standalone  # @UnresolvedImport
            maya.standalone.uninitialize()
            # These fixed some hangs on exit (specifically, from pymel unittests)
            # in maya 2016.51 (Ext 2, SP1)
            sys.stdout.flush()
            sys.stderr.flush()
            sys.__stdout__.flush()
            sys.__stderr__.flush()

    global _atExitCallbackInstalled
    if not _atExitCallbackInstalled:
        import atexit
        atexit.register(uninitializeMayaOnPythonExit)
        _atExitCallbackInstalled = True

_fixMayapy2011SegFault_applied = False

# Have all the checks inside here, in case people want to insert this in their
# userSetup... it's currently not always on
def fixMayapy2011SegFault():
    # this bug showed up in 2011 + 2012, was apparently fixed in 2013, then
    # showed up again in 2014...
    import platform
    if platform.system() == 'Linux':
        if om.MGlobal.mayaState() == om.MGlobal.kLibraryApp:  # mayapy only
            global _fixMayapy2011SegFault_applied
            if _fixMayapy2011SegFault_applied:
                return

            _fixMayapy2011SegFault_applied = True

            # In linux maya 2011, once maya has been initialized, if you try
            # to do a 'normal' sys.exit, it will crash with a segmentation
            # fault..
            # do a 'hard' os._exit to avoid this

            # note that, since there is no built-in support to tell from
            # within atexit functions what the exit code is, we cannot
            # guarantee returning the "correct" exit code... for instance,
            # if someone does:
            #    raise SystemExit(300)
            # we will instead return a 'normal' exit code of 0
            # ... but in general, the return code is a LOT more reliable now,
            # since it used to ALWAYS return non-zero...

            import sys
            import atexit

            # First, wrap sys.exit to store the exit code...
            _orig_exit = sys.exit

            # This is just in case anybody else needs to access the
            # original exit function...
            if not hasattr(sys, '_orig_exit'):
                sys._orig_exit = _orig_exit

            def exit(status):
                sys._exit_status = status
                _orig_exit(status)
            sys.exit = exit

            def hardExit():
                # run all the other exit handlers registered with
                # atexit, then hard exit... this is easy, because
                # atexit._run_exitfuncs pops funcs off the stack as it goes...
                # so all we need to do is call it again
                import sys
                atexit._run_exitfuncs()
                try:
                    print("pymel: hard exiting to avoid mayapy crash...")
                except Exception:
                    pass
                import os
                import sys

                exitStatus = getattr(sys, '_exit_status', None)
                if exitStatus is None:
                    last_value = getattr(sys, 'last_value', None)
                    if last_value is not None:
                        if isinstance(last_value, SystemExit):
                            try:
                                exitStatus = last_value.args[0]
                            except Exception:
                                pass
                        if exitStatus is None:
                            exitStatus = 1
                if exitStatus is None:
                    exitStatus = 0
                os._exit(exitStatus)
            atexit.register(hardExit)

# Fix for non US encodings in Maya


def encodeFix():
    if mayaInit():
        from maya.cmds import about

        mayaEncode = about(cs=True)
        pyEncode = sys.getdefaultencoding()     # Encoding tel que defini par sitecustomize
        if mayaEncode != pyEncode:             # s'il faut redefinir l'encoding
            # reload (sys)                       # attention reset aussi sys.stdout et sys.stderr
            # sys.setdefaultencoding(newEncode)
            #del sys.setdefaultencoding
            # print "# Encoding changed from '"+pyEncode+'" to "'+newEncode+"' #"
            if not about(b=True):              # si pas en batch, donc en mode UI, redefinir stdout et stderr avec encoding Maya
                import maya.utils
                try:
                    import maya.app.baseUI
                    import codecs
                    # Replace sys.stdin with a GUI version that will request input from the user
                    sys.stdin = codecs.getreader(mayaEncode)(maya.app.baseUI.StandardInput())
                    # Replace sys.stdout and sys.stderr with versions that can output to Maya's GUI
                    sys.stdout = codecs.getwriter(mayaEncode)(maya.utils.Output())
                    sys.stderr = codecs.getwriter(mayaEncode)(maya.utils.Output(error=1))
                except ImportError:
                    _logger.debug("Unable to import maya.app.baseUI")


#===============================================================================
# Cache utilities
#===============================================================================


def getImportableObject(importableName):
    import importlib
    if '.' in importableName:
        modulename, objName = importableName.rsplit('.', 1)
    else:
        # if no module, it's in builtins
        modulename = 'builtins'
        if PY2:
            modulename = '__builtin__'
        objName = importableName
    moduleobj = importlib.import_module(modulename)
    return getattr(moduleobj, objName)


def getImportableName(obj):
    module = inspect.getmodule(obj)
    import builtins
    if PY2:
        import __builtin__ as builtins
    if module == builtins:
        return obj.__name__
    return '{}.{}'.format(module.__name__, obj.__name__)


def _pickledump(data, filename, protocol=-1):
    with open(filename, mode='wb') as file:
        pickle.dump(data, file, protocol)


def _pickleload(filename):
    with open(filename, mode='rb') as file:
        res = pickle.load(file)
    return res

# NOTE: currently, there is no support for pymel to read or write formats
# other than the current.  This is here for documentation, and in case we want
# to add that ability at some point in the future.

# (1, 0) - initial version, that used "eval" instead of exec - didn't contain
#          explicit version
# (1, 1) - version that uses "exec" - ie, data = [...]; has a version as well
# (1, 2) - like (1, 2), but has potential unicode characters in utf-8 encoding,
#          and builtin types are now encoded as '<type bool>' instead of
#          '<type __builtin__.bool>'
PY_CACHE_FORMAT_VERSION = (1, 2)


# In python3, the PrettyPrinter will wrap long strings to match the width.
# The string wrapping in some cases looks better, but in many cases it
# results in strings with only a few characters per line, ie:
#                                                               foo: "This "
#                                                                    "is "
#                                                                    "bad."
# So, we use a custom PrettyPrinter to override string wrapping (giving results
# like we used to get in python2)

# Thanks to Martijn Pieters:
#   https://stackoverflow.com/a/31485450/920545

class NoStringWrappingPrettyPrinter(pprint.PrettyPrinter):
    def _format(self, object, *args):
        if isinstance(object, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super()._format(object, *args)
            finally:
                self._width = width
        else:
            super()._format(object, *args)

py_pformat = NoStringWrappingPrettyPrinter().pformat

if PY2:
    # just use the normal PrettyPrinter
    py_pformat = pprint.pformat

def _pyformatdump(data):
    strdata = 'version = {!r}\n\ndata = {}'.format(PY_CACHE_FORMAT_VERSION,
                                                   py_pformat(data))
    if PY2:
        if not isinstance(strdata, unicode):
            return strdata
    return strdata.encode('utf-8')

def _pycodeload(code):
    globs = {}
    exec(code, globs)
    # we ignore globs['version'] for now... there for potential future changes
    return globs['data']


def _pydump(data, filename):
    with open(filename, mode='wb') as file:
        file.write(_pyformatdump(data))


def _pyload(filename):
    with open(filename, mode='rb') as file:
        text = file.read()
    return _pycodeload(compile(text, filename, "exec"))


def _getpycbytes(source):
    import py_compile
    import tempfile

    # tried using NamedTemporaryFile, but got perm errors from
    # py_compile.compile
    pyfd, pyPath = tempfile.mkstemp(suffix='.py', prefix="py_cache_temp")
    try:
        with os.fdopen(pyfd, "wb") as pyf:
            pyf.write(source)
        pycfd, pycPath = tempfile.mkstemp(suffix='.pyc',
                                          prefix="pyc_cache_temp")
        os.close(pycfd)
        try:
            py_compile.compile(pyPath, pycPath, doraise=True)
            with open(pycPath, 'rb') as pycf:
                return pycf.read()
        finally:
            os.remove(pycPath)
    finally:
        os.remove(pyPath)


def _pyczipdump(data, filename, pyc=True):
    import zipfile
    inZipPath = os.path.basename(filename)
    if inZipPath.lower().endswith('.zip'):
        inZipPath = inZipPath[:-len('.zip')]

    bytes = _pyformatdump(data)
    if pyc:
        bytes = _getpycbytes(bytes)
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inZipPath, bytes)


def _pyzipdump(data, filename):
    return _pyczipdump(data, filename, pyc=False)


def _pyzipload(filename):
    import zipimport
    importer = zipimport.zipimporter(filename)
    moduleName = os.path.basename(filename).split('.')[0]
    return _pycodeload(importer.get_code(moduleName))


CacheFormat = namedtuple('CacheFormat', ['ext', 'reader', 'writer'])


class PymelCache(object):
    # override these
    NAME = ''   # ie, 'mayaApi'
    DESC = ''   # ie, 'the API cache' - used in error messages, etc

    FORMATS = [
        CacheFormat('.py', _pyload, _pydump),
        CacheFormat('.pyc.zip', _pyzipload, _pyczipdump),
        CacheFormat('.py.zip', _pyzipload, _pyzipdump),
        CacheFormat('.bin', _pickleload, _pickledump),
        CacheFormat('.zip', picklezip.load, picklezip.dump),
    ]
    EXTENSIONS = {x.ext: x for x in FORMATS}
    DEFAULT_EXT = '.py'

    # whether to add the version to the filename when writing out the cache
    USE_VERSION = True

    _lastReadPath = None
    _lastWritePath = None

    def fromRawData(self, rawData):
        '''If a subclass needs to modify data as it is read from the cache
        on disk, do it here'''
        return rawData

    def toRawData(self, data):
        '''If a subclass needs to modify data before it is written to the cache
        on disk, do it here'''
        if PY2:
            # the written out .py cache will not include 'u' prefixes, which
            # makes it easier to diff to python-3-built caches; initially, just
            # using this is caches where we think it's unlikely to affect client
            # code
            isUnicode = lambda x: isinstance(x, unicode)
            data = pymel.util.deepPatch(data, isUnicode, util2to3.trystr)
        return data

    def read(self, path=None, ext=None, ignoreError=False):
        if path is not None and ext is None:
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = None
        if ext is None:
            formats = self.FORMATS
        else:
            formats = [self.EXTENSIONS[ext]]

        for format in formats:
            # if the user provided an explicit ext (or path with ext), we want
            # to use that EXACTLY (ie, might differ in case) - otherwise, we
            # use the standard ext from format.ext
            if path is not None:
                formatPath = path
            else:
                formatPath = self.path(ext=format.ext)

            if not os.path.isfile(formatPath):
                _logger.debug(self._actionMessage('Unable to open', 'from nonexistant path', formatPath))
                continue

            func = format.reader
            _logger.debug(self._actionMessage('Loading', 'from', formatPath))
            try:
                finalData = self.fromRawData(func(formatPath))
            except Exception as e:
                self._errorMsg('read', 'from', formatPath, e)
                if not ignoreError:
                    raise
            else:
                self._lastReadPath = formatPath
                return finalData

    def write(self, data, path=None, ext=None, ignoreError=False):
        import copy
        # when writing data, we dont' actually want to modify the passed in
        # data, as it may be in use... so we make a deepcopy
        data = copy.deepcopy(data)

        if path is not None and ext is None:
            ext = os.path.splitext(path)[1]
        if not ext:
            ext = self.DEFAULT_EXT
        if not path:
            path = self.path(ext=ext)
        format = self.EXTENSIONS[ext]
        func = format.writer
        _logger.info(self._actionMessage('Saving', 'to', path))

        try:
            func(self.toRawData(data), path)
        except Exception as e:
            self._errorMsg('write', 'to', path, e)
            if not ignoreError:
                raise
        else:
            self._lastWritePath = path

    @universalmethod
    def path(self, version=None, ext=None):
        if ext is None:
            ext = self.DEFAULT_EXT
        if self.USE_VERSION:
            if version is not None:
                short_version = str(version)
            elif hasattr(self, 'version'):
                short_version = str(self.version)
            else:
                short_version = shortName()
        else:
            short_version = ''

        newPath = _moduleJoin('cache', self.NAME + short_version)
        return newPath + ext

    @classmethod
    def allVersions(cls, allowEmpty=False):
        import itertools
        import re

        # unlikely they'll have a path with PLACEHOLDER, but better safe than
        # sorry...
        placeholderBase = 'PLACEHOLDER'
        i = 0
        for i in itertools.count():
            placeholder = placeholderBase + str(i)
            fullPath = cls.path(placeholder)
            if fullPath.count(placeholder) == 1:
                break
        dirname, filePattern = os.path.split(fullPath)
        filePattern = re.escape(filePattern)
        filePattern = filePattern.replace(placeholder, '(.*)')
        filePatternRe = re.compile('^' + filePattern + '$')
        versions = []
        for filename in os.listdir(dirname):
            if not os.path.isfile(os.path.join(dirname, filename)):
                continue
            match = filePatternRe.match(filename)
            if match:
                version = match.group(1)
                if allowEmpty or version != '':
                    versions.append(version)
        return sorted(versions)

    @classmethod
    def _actionMessage(cls, action, direction, location):
        '''_actionMessage('eat', 'at', 'Joes') =>
            "eat cls.DESC at 'Joes'"
        '''
        description = cls.DESC
        if description:
            description = ' ' + description
        return "%s%s %s %r" % (action, description, direction, location)

    @classmethod
    def _errorMsg(cls, action, direction, path, error):
        '''_errorMessage('eat', 'at', 'Joes') =>
            'Unable to eat cls.DESC at Joes: error.msg'
        '''
        actionMsg = cls._actionMessage(action, direction, path)
        _logger.raiseLog(_logger.WARNING,
                         "Unable to %s: %s" % (actionMsg, error))
        import traceback
        _logger.debug(traceback.format_exc())


# Considered using named_tuple, but wanted to make data stored in cache
# have as few dependencies as possible - ie, just a simple tuple
class SubItemCache(PymelCache):

    '''Used to store various maya information

    ie, api / cmd data parsed from docs

    To implement, create a subclass, which overrides at least the NAME, DESC,
    and _CACHE_NAMES attributes, and implements the rebuild method.

    Then to access data, you should initialize an instance, then call build;
    build will load the data from the cache file if possible, or call rebuild
    to build the data from scratch if not.  If the data had to be rebuilt,
    a new file cache will be saved.

    The data may then be accessed through attributes on the instance, with
    the names given in _CACHE_NAMES.

    >>> class NodeCache(SubItemCache):
    ...     NAME = 'mayaNodes'
    ...     DESC = 'the maya nodes cache'
    ...     _CACHE_NAMES = ['nodeTypes']
    ...     AUTO_SAVE = False
    ...     def rebuild(self):
    ...         import maya.cmds
    ...         self.nodeTypes = maya.cmds.allNodeTypes(includeAbstract=True)
    >>> cacheInst = NodeCache()
    >>> cacheInst.build()
    >>> 'polyCube' in cacheInst.nodeTypes
    True
    '''
    # Provides a front end for a pickled file, which should contain a
    # tuple of items; each item in the tuple is associated with a name from
    # _CACHE_NAMES

    # override this with a list of names for the items within the cache
    _CACHE_NAMES = []

    # Set this to the initialization contructor for each cache item;
    # if a given cache name is not present in ITEM_TYPES, DEFAULT_TYPE is
    # used
    # These are the types that the contents will 'appear' to be to the end user
    # (ie, the types returned by contents).
    # Should be constructors which can either take no arguments, or
    # a single argument to initialize an instance.
    ITEM_TYPES = {}
    DEFAULT_TYPE = dict
    AUTO_SAVE = True

    def __init__(self):
        for name in self._CACHE_NAMES:
            self.initVal(name)

    @classmethod
    def cacheNames(cls):
        return tuple(cls._CACHE_NAMES)

    @classmethod
    def itemType(cls, name):
        return cls.ITEM_TYPES.get(name, cls.DEFAULT_TYPE)

    @classmethod
    def itemIndex(cls, name):
        return cls._CACHE_NAMES.index(name)

    def initVal(self, name):
        itemType = self.itemType(name)
        if itemType is None:
            val = None
        else:
            val = itemType()
        setattr(self, name, val)

    def build(self):
        """
        Used to rebuild cache, either by loading from a cache file, or
        rebuilding from scratch.
        """
        data = self.load()
        if data is None:
            self.rebuild()
            if self.AUTO_SAVE:
                self.save()

    # override this...
    def rebuild(self):
        """Rebuild cache from scratch

        Unlike 'build', this does not attempt to load a cache file, but always
        rebuilds it by parsing the docs, etc.
        """
        pass

    def update(self, obj, cacheNames=None):
        '''Update all the various data from the given object, which should
        either be a dictionary, a list or tuple with the right number of items,
        or an object with the caches stored in attributes on it.
        '''
        if cacheNames is None:
            cacheNames = self.cacheNames()

        if isinstance(obj, dict):
            for key, val in obj.items():
                setattr(self, key, val)
        elif isinstance(obj, (list, tuple)):
            if len(obj) != len(cacheNames):
                raise ValueError('length of update object (%d) did not match '
                                 'length of cache names (%d)' %
                                 (len(obj), len(cacheNames)))
            for newVal, name in zip(obj, cacheNames):
                setattr(self, name, newVal)
        else:
            for cacheName in cacheNames:
                setattr(self, cacheName, getattr(obj, cacheName))

    def load(self):
        '''Attempts to load the data from the cache on file.

        If it succeeds, it will update itself, and return the loaded items;
        if it fails, it will return None
        '''
        data = self.read(ignoreError=True)
        if data is not None:
            data = tuple(data)
            self.update(data, cacheNames=self._CACHE_NAMES)
        return data

    def save(self, obj=None, ext=None):
        '''Saves the cache

        Will optionally update the caches from the given object (which may be
        a dictionary, or an object with the caches stored in attributes on it)
        before saving
        '''
        if obj is not None:
            self.update(obj)
        data = self.contents()
        self.write(data, ext=ext)

    # was called 'caches'
    def contents(self):
        return tuple(getattr(self, x) for x in self.cacheNames())

#===============================================================================
# Config stuff
#===============================================================================


def getConfigFile():
    return plogging.getConfigFile()


def parsePymelConfig():
    if PY2:
        import ConfigParser as configparser
    else:
        import configparser

    types = {
        'skip_mel_init': 'boolean',
        'check_attr_before_lock': 'boolean',
        'fix_mayapy_segfault': 'boolean',
        'fix_linux_mayapy_segfault': 'boolean',
    }
    defaults = {
        'skip_mel_init': 'off',
        'check_attr_before_lock': 'off',
        'preferred_python_qt_binding': 'pyqt',
        # want to use the "better" fix_mayapy_segfault now that uninitialize is
        # available
        'fix_mayapy_segfault': 'on',
        'fix_linux_mayapy_segfault': 'off',
        'deleted_pynode_name_access': 'warn_deprecated',
    }

    config = configparser.ConfigParser(defaults)
    config.read(getConfigFile())

    d = {}
    for option in config.options('pymel'):
        getter = getattr(config, 'get' + types.get(option, ''))
        d[option] = getter('pymel', option)

    # just to standardize this setting to be lowercase
    d['preferred_python_qt_binding'] = d['preferred_python_qt_binding'].lower()

    return d

pymel_options = parsePymelConfig()


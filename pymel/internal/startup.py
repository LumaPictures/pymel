"""
Maya-related functions, which are useful to both `api` and `core`, including `mayaInit` which ensures
that maya is initialized in standalone mode.
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import os.path
import sys
import maya
import maya.OpenMaya as om
import maya.utils

from pymel.util import subpackages
import pymel.versions as versions
from pymel.mayautils import getUserPrefsDir
from . import plogging

from future.utils import PY2

_logger = plogging.getLogger(__name__)

# There are FOUR different ways maya might be started, all of which are
# subtly different, that need to be considered / tested:
#
# 1) Normal gui
# 2) maya -prompt
# 3) Render
# 4) mayapy (or just straight up python)

isInitializing = False
# Setting this to False will make finalize() do nothing
finalizeEnabled = True
_finalizeCalled = False

_mayaExitCallbackId = None
_mayaUninitialized = False
_atExitCallbackInstalled = False


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


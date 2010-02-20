"""
Maya-related functions, which are useful to both `api` and `core`, including `mayaInit` which ensures
that maya is initialized in standalone mode.
"""
from __future__ import with_statement
import os.path, sys, glob, inspect
import maya
import maya.OpenMaya as om
import maya.utils

from pymel.util import picklezip, shellOutput
import pymel.versions as versions
from pymel.mayautils import getUserPrefsDir
from pymel.versions import shortName, installName
import plogging

_logger = plogging.getLogger(__name__)
try:
    import cPickle as pickle
except:
    _logger.warning("using pickle instead of cPickle: load performance will be affected")
    import pickle

#from maya.cmds import encodeString

isInitializing = False
# Setting this to False will make finalize() do nothing
finalizeEnabled = True
_finalizeFinished = False

# tells whether this maya package has been modified to work with pymel
pymelMayaPackage = hasattr(maya.utils, 'shellLogHandler') or versions.current() >= versions.v2011


def _moduleJoin(*args):
    """
    Joins with the base pymel directory.
    :rtype: string
    """
    moduleDir = os.path.dirname( os.path.dirname( sys.modules[__name__].__file__ ) )
    return os.path.realpath(os.path.join( moduleDir, *args))


def mayaStartupHasRun():
    """
    Returns True if maya.app.startup has run, False otherwise.
    """
    return 'maya.app.startup.gui' in sys.modules or 'maya.app.startup.batch' in sys.modules

def refreshEnviron():
    """
    copy the shell environment into python's environment, as stored in os.environ
    """
    exclude = ['SHLVL']

    if os.name == 'posix':
        cmd = '/usr/bin/env'
    else:
        cmd = 'set'

    cmdOutput = shellOutput(cmd)
    #print "ENV", cmdOutput
    # use splitlines rather than split('\n') for better handling of different
    # newline characters on various os's
    for line in cmdOutput.splitlines():
        # need the check for '=' in line b/c on windows (and perhaps on other systems? orenouard?), an extra empty line may be appended
        if '=' in line:
            var, val = line.split('=', 1)  # split at most once, so that lines such as 'smiley==)' will work
            if not var.startswith('_') and var not in exclude:
                    os.environ[var] = val

def setupFormatting():
    import pprint
    import maya.utils
    def myResultCallback(obj):
        return pprint.pformat(obj)
    maya.utils.formatGuiResult = myResultCallback
    # prevent auto-completion generator from getting confused
    maya.utils.formatGuiResult.__module__ = 'maya.utils'

#def loadDynamicLibs():
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
def mayaInit(forversion=None) :
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
    >>> print mm.eval("getenv MAYA_SCRIPT_PATH")    #doctest: +SKIP
    /Network/Servers/sv-user.luma-pictures.com/luma .....
    >>> import os                         #doctest: +SKIP
    >>> 'MAYA_SCRIPT_PATH' in os.environ  #doctest: +SKIP
    False

    The solution lies in `refreshEnviron`, which copies the environment from the shell to os.environ after maya.standalone
    initializes.

    :rtype: bool
    :return: returns True if maya.cmds required initializing ( in other words, we are in a standalone python interpreter )

    """
    setupFormatting()

    global isInitializing

    # test that Maya actually is loaded and that commands have been initialized,for the requested version

    try :
        from maya.cmds import about
        # if this succeeded, we're initialized
        isInitializing = False
        return False
    except:
        pass

    # for use with pymel compatible maya package
    os.environ['MAYA_SKIP_USERSETUP_PY'] = 'on'

    # reload env vars, define MAYA_ENV_VERSION in the Maya.env to avoid unneeded reloads
    sep = os.path.pathsep

    if not sys.modules.has_key('maya.standalone'):
        try :
            import maya.standalone #@UnresolvedImport
            maya.standalone.initialize(name="python")

            if versions.current() < versions.v2009:
                refreshEnviron()

        except ImportError, e:
            raise e, str(e) + ": pymel was unable to intialize maya.standalone"

    try:
        from maya.cmds import about
    except Exception, e:
        raise e, str(e) + ": maya.standalone was successfully initialized, but pymel failed to import maya.cmds"

    # return True, meaning we had to initialize maya standalone
    isInitializing = True
    return True

def initMEL():
    if 'PYMEL_SKIP_MEL_INIT' in os.environ or pymel_options.get( 'skip_mel_init', False ) :
        _logger.info( "Skipping MEL initialization" )
        return

    _logger.debug( "initMEL" )
    mayaVersion = versions.installName()
    prefsDir = getUserPrefsDir()
    if prefsDir is None:
        _logger.error( "could not initialize user preferences: MAYA_APP_DIR not set" )
    elif not os.path.isdir(prefsDir):
        _logger.error( "could not initialize user preferences: %s does not exist" % prefsDir  )

    # TODO : use cmds.internalVar to get paths
    # got this startup sequence from autodesk support
    startup = [
        #'defaultRunTimeCommands.mel',  # sourced automatically
        #os.path.join( prefsDir, 'userRunTimeCommands.mel'), # sourced automatically
        'createPreferencesOptVars.mel',
        'createGlobalOptVars.mel',
        os.path.join( prefsDir, 'userPrefs.mel') if prefsDir else None,
        'initialStartup.mel',
        #$HOME/Documents/maya/projects/default/workspace.mel
        'initialPlugins.mel',
        #'initialGUI.mel', #GUI
        #'initialLayout.mel', #GUI
        #os.path.join( prefsDir, 'windowPrefs.mel'), #GUI
        #os.path.join( prefsDir, 'menuSetPrefs.mel'), #GUI
        #'hotkeySetup.mel', #GUI
        'namedCommandSetup.mel',
        os.path.join( prefsDir, 'userNamedCommands.mel' ) if prefsDir else None,
        #'initAfter.mel', #GUI
        os.path.join( prefsDir, 'pluginPrefs.mel' )  if prefsDir else None
    ]
    try:
        for f in startup:
            _logger.debug("running: %s" % f)
            if f is not None:
                if os.path.isabs(f) and not os.path.exists(f):
                    _logger.warning( "Maya startup file %s does not exist" % f )
                else:
                    # need to encode backslashes (used for windows paths)
                    if isinstance(f, unicode):
                        encoding = 'unicode_escape'
                    else:
                        encoding = 'string_escape'
                    #import pymel.core.language as lang
                    #lang.mel.source( f.encode(encoding)  )
                    import maya.mel
                    maya.mel.eval( 'source "%s"' % f.encode(encoding) )

    except Exception, e:
        _logger.error( "could not perform Maya initialization sequence: failed on %s: %s" % ( f, e) )

    try:
        # make sure it exists
        res = maya.mel.eval('whatIs "userSetup.mel"')
        if res != 'Unknown':
            maya.mel.eval( 'source "userSetup.mel"')
    except RuntimeError: pass

    _logger.debug("done running mel files")


def _makeAEProc(modname, classname, procname):
    contents = '''global proc %(procname)s( string $nodeName ){
    python("import %(__name__)s;%(__name__)s._aeLoader('%(modname)s','%(classname)s','" + $nodeName + "')");}'''
    d = locals().copy()
    d['__name__'] = __name__
    import maya.mel as mm
    mm.eval( contents % d )

def _aeLoader(modname, classname, nodename):
    mod = __import__(modname, globals(), locals(), [classname], -1)
    try:
        f = getattr(mod,classname)
        f(nodename)
    except Exception:
        print "failed to load python attribute editor template '%s.%s'" % (modname, classname)
        import traceback
        traceback.print_exc()

def initAE():
    try:
        pkg = __import__('AETemplates')
    except ImportError:
        return
    except Exception:
        import traceback
        traceback.print_exc()
        return

    from pymel.core.uitypes import AETemplate

    if hasattr(pkg, '__path__'):
        completed = []
        for pth in pkg.__path__:
            realpath = os.path.realpath(pth)
            if realpath not in completed:
                files = glob.glob( os.path.join(realpath,'AE*Template.py'))
                for fname in files:
                    name = os.path.basename(fname)[:-3]
                    _makeAEProc( 'AETemplates.'+name, name, name)
                completed.append(realpath)
    for name, obj in inspect.getmembers(pkg, lambda x: inspect.isclass(x) and issubclass(x,AETemplate) ):
        try:
            nodeType = obj.nodeType()
        except:
            continue
        else:
            _makeAEProc( 'AETemplates', name, 'AE'+nodeType+'Template')

def finalize():
    global finalizeEnabled
    global _finalizeFinished
    if not finalizeEnabled or _finalizeFinished:
        return
    state = om.MGlobal.mayaState()
    if state == om.MGlobal.kLibraryApp: # mayapy only
        global isInitializing
        if pymelMayaPackage and isInitializing:
            # this module is not encapsulated into functions, but it should already
            # be imported, so it won't run again
            assert 'maya.app.startup.basic' in sys.modules, \
                "something is very wrong. maya.app.startup.basic should be imported by now"
            import maya.app.startup.basic
            maya.app.startup.basic.executeUserSetup()
        initMEL()
    elif state == om.MGlobal.kInteractive:
        initAE()
    _finalizeFinished = True

# Fix for non US encodings in Maya
def encodeFix():
    if mayaInit() :
        from maya.cmds import about

        mayaEncode = about(cs=True)
        pyEncode = sys.getdefaultencoding()     # Encoding tel que defini par sitecustomize
        if mayaEncode != pyEncode :             # s'il faut redefinir l'encoding
            #reload (sys)                       # attention reset aussi sys.stdout et sys.stderr
            #sys.setdefaultencoding(newEncode)
            #del sys.setdefaultencoding
            #print "# Encoding changed from '"+pyEncode+'" to "'+newEncode+"' #"
            if not about(b=True) :              # si pas en batch, donc en mode UI, redefinir stdout et stderr avec encoding Maya
                import maya.utils
                try :
                    import maya.app.baseUI
                    # Replace sys.stdin with a GUI version that will request input from the user
                    sys.stdin = codecs.getreader(mayaEncode)(maya.app.baseUI.StandardInput())
                    # Replace sys.stdout and sys.stderr with versions that can output to Maya's GUI
                    sys.stdout = codecs.getwriter(mayaEncode)(maya.utils.Output())
                    sys.stderr = codecs.getwriter(mayaEncode)(maya.utils.Output( error=1 ))
                except ImportError :
                    _logger.debug("Unable to import maya.app.baseUI")


def _dump( data, filename, protocol = -1):
    with open(filename, mode='wb') as file:
        pickle.dump( data, file, protocol)

def _load(filename):
    with open(filename, mode='rb') as file:
        res = pickle.load(file)
        return res


def loadCache( filePrefix, description='', useVersion=True, compressed=True):
    if useVersion:
        short_version = shortName()
    else:
        short_version = ''
    newPath = _moduleJoin( 'cache', filePrefix+short_version )

    if compressed:
        newPath += '.zip'
        func = picklezip.load
    else:
        newPath += '.bin'
        func = _load

    if description:
        description = ' ' + description

    #_logger.info("Loading%s from '%s'" % ( description, newPath ))

    try:
        return func(newPath)
    except Exception, e:
        _logger.error("Unable to load%s from '%s': %s" % (description, newPath, e))



def writeCache( data, filePrefix, description='', useVersion=True, compressed=True):

    if useVersion:
        short_version = shortName()
    else:
        short_version = ''

    newPath = _moduleJoin( 'cache', filePrefix+short_version )
    if compressed:
        newPath += '.zip'
        func = picklezip.dump
    else:
        newPath += '.bin'
        func = _dump

    if description:
        description = ' ' + description

    _logger.info("Saving%s to '%s'" % ( description, newPath ))

    try :
        func( data, newPath, 2)
    except Exception, e:
        _logger.error("Unable to write%s to '%s': %s" % (description, newPath, e))


def getConfigFile():
    return plogging.getConfigFile()

def parsePymelConfig():
    import ConfigParser

    types = { 'skip_mel_init' : 'boolean' }
    defaults = {'skip_mel_init' : 'off' }

    config = ConfigParser.ConfigParser(defaults)
    config.read( getConfigFile() )

    d = {}
    for option in config.options('pymel'):
        getter = getattr( config, 'get' + types.get(option, '') )
        d[option] = getter( 'pymel', option )
    return d

pymel_options = parsePymelConfig()

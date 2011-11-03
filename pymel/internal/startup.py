"""
Maya-related functions, which are useful to both `api` and `core`, including `mayaInit` which ensures
that maya is initialized in standalone mode.
"""
from __future__ import with_statement
import os.path, sys, glob, inspect
import maya
import maya.OpenMaya as om
import maya.utils

from pymel.util import picklezip, shellOutput, subpackages, refreshEnviron, namedtuple
import pymel.versions as versions
from pymel.mayautils import getUserPrefsDir
from pymel.versions import shortName, installName
import plogging


# There are FOUR different ways maya might be started, all of which are
# subtly different, that need to be considered / tested:
#
# 1) Normal gui
# 2) maya -prompt
# 3) Render
# 4) mayapy (or just straight up python)

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
_finalizeCalled = False

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

    aboutExists = False
    try :
        from maya.cmds import about
        aboutExists = True
    except ImportError:
        pass
    
    if aboutExists and mayaStartupHasStarted():        
        # if this succeeded, we're initialized
        isInitializing = False
        return False

    _logger.debug( "startup.mayaInit running" )
    # for use with pymel compatible maya package
    os.environ['MAYA_SKIP_USERSETUP_PY'] = 'on'

    if not aboutExists and not sys.modules.has_key('maya.standalone'):
        try :
            import maya.standalone #@UnresolvedImport
            maya.standalone.initialize(name="python")

            if versions.current() < versions.v2009:
                refreshEnviron()
                
        except ImportError, e:
            raise e, str(e) + ": pymel was unable to intialize maya.standalone"

    try:
        from maya.cmds import about
    except Exception:
        _logger.error("maya.standalone was successfully initialized, but pymel failed to import maya.cmds (or it was not populated)")
        raise

    if not mayaStartupHasRun():
        _logger.debug( "running maya.app.startup" )
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
    if pymelMayaPackage and isInitializing:
        # this module is not encapsulated into functions, but it should already
        # be imported, so it won't run again
        assert 'maya.app.startup.basic' in sys.modules, \
            "something is very wrong. maya.app.startup.basic should be imported by now"
        import maya.app.startup.basic
        maya.app.startup.basic.executeUserSetup()

    state = om.MGlobal.mayaState()
    if state == om.MGlobal.kLibraryApp: # mayapy only
        initMEL()
        #fixMayapy2011SegFault()
    elif state == om.MGlobal.kInteractive:
        initAE()


# Have all the checks inside here, in case people want to insert this in their
# userSetup... it's currently not always on
def fixMayapy2011SegFault():
    if versions.current() >= versions.v2011:
        import platform
        if platform.system() == 'Linux':
            if om.MGlobal.mayaState() == om.MGlobal.kLibraryApp: # mayapy only
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
                if not hasattr('sys', '_orig_exit'):
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
                        print "pymel: hard exiting to avoid mayapy crash..."
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
                                except Exception: pass
                            if exitStatus is None:
                                exitStatus = 1
                    if exitStatus is None:
                        exitStatus = 0
                    os._exit(exitStatus)
                atexit.register(hardExit)

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
                    import codecs
                    # Replace sys.stdin with a GUI version that will request input from the user
                    sys.stdin = codecs.getreader(mayaEncode)(maya.app.baseUI.StandardInput())
                    # Replace sys.stdout and sys.stderr with versions that can output to Maya's GUI
                    sys.stdout = codecs.getwriter(mayaEncode)(maya.utils.Output())
                    sys.stderr = codecs.getwriter(mayaEncode)(maya.utils.Output( error=1 ))
                except ImportError :
                    _logger.debug("Unable to import maya.app.baseUI")


#===============================================================================
# Cache utilities
#===============================================================================

def _dump( data, filename, protocol = -1):
    with open(filename, mode='wb') as file:
        pickle.dump( data, file, protocol)

def _load(filename):
    with open(filename, mode='rb') as file:
        res = pickle.load(file)
        return res

class PymelCache(object):
    # override these
    NAME = ''   # ie, 'mayaApi'
    DESC = ''   # ie, 'the API cache' - used in error messages, etc
    COMPRESSED = True
    
    # whether to add the version to the filename when writing out the cache
    USE_VERSION = True

    def read(self):
        newPath = self.path()
        if self.COMPRESSED:
            func = picklezip.load
        else:
            func = _load
    
        _logger.debug(self._actionMessage('Loading', 'from', newPath))
    
        try:
            return func(newPath)
        except Exception, e:
            self._errorMsg('read', 'from', newPath, e)

    def write(self, data):
        newPath = self.path()
        if self.COMPRESSED:
            func = picklezip.dump
        else:
            func = _dump
    
        _logger.info(self._actionMessage('Saving', 'to', newPath))
    
        try :
            func( data, newPath, 2)
        except Exception, e:
            self._errorMsg('write', 'to', newPath, e)
            
    def path(self):
        if self.USE_VERSION:
            if hasattr(self, 'version'):
                short_version = str(self.version)
            else:
                short_version = shortName()
        else:
            short_version = ''
    
        newPath = _moduleJoin( 'cache', self.NAME+short_version )
        if self.COMPRESSED:
            newPath += '.zip'
        else:
            newPath += '.bin'
        return newPath
                        
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
        _logger.error("Unable to %s: %s" % (actionMsg, error))
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
    ...     COMPRESSED = False
    ...     _CACHE_NAMES = ['nodeTypes']
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
    # If the value needs to be converted before pickling, specify an entry
    # in STORAGE_TYPES
    # Both should be constructors which can either take no arguments, or
    # a single argument to initialize an instance.
    ITEM_TYPES = {}
    STORAGE_TYPES = {}
    DEFAULT_TYPE = dict
    
    def __init__(self):
        for name in self._CACHE_NAMES:
            self.initVal(name)
            
    def cacheNames(self):
        return tuple(self._CACHE_NAMES)
            
    def initVal(self, name):
        itemType = self.itemType(name)
        if itemType is None:
            val = None
        else:
            val = itemType()
        setattr(self, name, val)
            
    def itemType(self, name):
        return self.ITEM_TYPES.get(name, self.DEFAULT_TYPE)
    
    def build(self):
        """
        Used to rebuild cache, either by loading from a cache file, or rebuilding from scratch.
        """
        data = self.load()
        if data is None:
            self.rebuild()
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
            for key, val in obj.iteritems():
                setattr(self, key, val)
        elif isinstance(obj, (list, tuple)):
            if len(obj) != len(cacheNames):
                raise ValueError('length of update object (%d) did not match length of cache names (%d)' % (len(obj), len(cacheNames)))
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
        data = self.read()
        if data is not None:
            data = list(data)
            # if STORAGE_TYPES, need to convert back from the storage type to
            # the 'normal' type
            if self.STORAGE_TYPES:
                for name in self.STORAGE_TYPES:
                    index = self._CACHE_NAMES.index(name)
                    val = data[index]
                    val = self.itemType(name)(val)
                    data[index] = val 
            data = tuple(data)
            self.update(data, cacheNames=self._CACHE_NAMES)
        return data
    
    def save(self, obj=None):
        '''Saves the cache
        
        Will optionally update the caches from the given object (which may be
        a dictionary, or an object with the caches stored in attributes on it)
        before saving
        '''
        if obj is not None:
            self.update(obj)
        data = self.contents()
        if self.STORAGE_TYPES:
            newData = []
            for name, val in zip(self._CACHE_NAMES, data):
                if name in self.STORAGE_TYPES:
                    val = self.STORAGE_TYPES[name](val)
                newData.append(val)
            data = tuple(newData)
                
        self.write(data)            
            
    # was called 'caches' 
    def contents(self):
        return tuple( getattr(self, x) for x in self.cacheNames() )
                
#===============================================================================
# Config stuff
#===============================================================================

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

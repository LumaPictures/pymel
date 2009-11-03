"""
Maya-related functions, which are useful to both `api` and `core`, including `mayaInit` which ensures
that maya is initialized in standalone mode.
"""

import re, os.path, sys, platform

from pwarnings import *
import plogging

from pymel.util import path as _path, shellOutput

from version import Version, parseVersionStr
import maya
from maya.OpenMaya import MGlobal

_logger = plogging.getLogger(__name__)
try:
    import cPickle as pickle
except:
    _logger.warning("using pickle instead of cPickle: load performance will be affected")
    import pickle

#from maya.cmds import encodeString

if os.name == 'nt' :
    # There are also cases where platform.system fails completely on Vista
    mayabin = 'maya.exe'
    libdir = 'bin'
    system = 'Windows'
else :
    mayabin = 'maya.bin'
    system = platform.system()
    if system == 'Darwin':
        libdir = 'MacOS'
    else:
        libdir = 'lib'
    
sep = os.path.pathsep

isInitializing = False
    
# tells whether this maya package has been modified to work with pymel
pymelMayaPackage = hasattr(maya, 'pymelCompatible')
        

def _moduleDir():
    """
    Returns the base pymel directory.
    :rtype: string
    """
    return os.path.dirname( os.path.dirname( sys.modules[__name__].__file__ ) )

# A source command that will search for the Python script "file" in the specified path
# (using the system path if none is provided) path and tries to call execfile() on it
def source (file, searchPath=None, recurse=False) :
    """Looks for a python script in the specified path (uses system path if no path is specified)
        and executes it if it's found """
    filepath = unicode(file)
    filename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)
    
    if searchPath is None :
        searchPath=sys.path
    if isinstance(searchPath, basestring ):
        searchPath = [searchPath]
    itpath = iter(searchPath)
    _logger.debug("looking for file as: "+filepath)
    while not os.path.exists(filepath) :
        try :
            p = os.path.abspath(os.path.realpath(itpath.next()))
            filepath = os.path.join(p, filename)
            _logger.debug('looking for file as: '+filepath)
            if recurse and not filepath.exists() :
                itsub = os.walk(p)
                while not os.path.exists(filepath) :
                    try :
                        root, dirs, files = itsub.next()
                        itdirs = iter(dirs)
                        while not os.path.exists(filepath) :
                            try :
                                filepath = os.path.join(root, itdirs.next(), filename)
                                _logger.debug('looking for file as: '+filepath)
                            except :
                                pass
                    except :
                        pass
        except :
            raise ValueError, "File '"+filename+"' not found in path"
            # In case the raise exception is replaced by a warning don't forget to return here
            return
    # _logger.debug("Executing: "+filepath)
    return execfile(filepath)

def getMayaLocation(version=None):
    """ Remember to pass the FULL version (with extension if any) to this function! """
    try:
        loc = os.path.realpath( os.environ['MAYA_LOCATION'] )
    except:
        loc = os.path.dirname( os.path.dirname( sys.executable ) )
    # get the path of a different maya version than current
    if version:
        # note that a recursive loop between getMayaLocation / getMayaVersion
        # is avoided because getMayaVersion always calls getMayaLocation with
        # version == None
        actual_long_version = Version.installName()
        actual_short_version = Version.shortName()
        if version != actual_long_version:
            short_version = parseVersionStr(version, extension=False)
            if version == short_version :
                try_version = actual_long_version.replace(actual_short_version, short_version)
            else :
                try_version = version
            try_loc = loc.replace( actual_long_version, try_version )
            if os.path.exists(try_loc) :
                loc = try_loc
            else :
                _logger.warn("No Maya found for version %s" % version )
                loc = None
                
    return loc


def mayaIsRunning():
    """
    Returns True if maya.cmds have  False otherwise.
    
    Early in interactive startup it is possible for commands to exist but for Maya to not yet be initialized.
    
    :rtype: bool
    """
    
    # Implementation is essentially just a wrapper for getRunningMayaVersionString -
    # this function was included for clearer / more readable code
    
    try :
        from maya.cmds import about
        about(version=True)
        return True
    except :
        return False

def mayaStartupHasRun():
    """
    Returns True if maya.app.startup has run, False otherwise.
    """
    return 'maya.app.startup.gui' in sys.modules or 'maya.app.startup.batch' in sys.modules
    
def getMayaExecutable(version=None, commandLine=True):
    """Returns the path string to the maya executable for the given version; if version is None, then returns the path
    string for the current maya version.
    
    If commandLine is True and we are running on windows, will return the path to mayabatch.exe, instead of maya.exe"""
    
    
    filename = "maya"
    
    if commandLine and os.name == "nt":
        filename += "batch"    
        
    if os.name == "nt":
        filename += ".exe"
        
    fullPath = os.path.join(getMayaLocation(version), 'bin', filename )
    
    if os.path.isfile(fullPath):
        return fullPath
    else:
        # if all else fails... check sys.executable
        binaryRoot, binaryExtension = os.path.splitext(os.path.basename(sys.executable))
        if binaryRoot == "python":
            # sys.executable was the python binary
            raise RuntimeError("Unable to locate maya executable - try setting 'MAYA_LOCATION' environment variable")
        return sys.executable
    

    
def getMayaAppDir():
    if not os.environ.has_key('MAYA_APP_DIR') :
        home = os.environ.get('HOME', None)
        if not home :
            return None
        else :
            return os.path.join(home, 'maya')
    return os.environ['MAYA_APP_DIR']


def mayaDocsLocation(version=None):
    docLocation = None
    if (version == None or version == Version.installName() ) and mayaIsRunning():
        # Return the doc location for the running version of maya
        from maya.cmds import showHelp
        docLocation = showHelp("", q=True, docs=True)
        
        # Older implementations had no trailing slash, but the result returned by
        # showHelp has a trailing slash... so eliminate any trailing slashes for
        # consistency
        while docLocation != "" and os.path.basename(docLocation) == "":
            docLocation = os.path.dirname(docLocation)
                
    # Want the docs for a different version, or maya isn't initialized yet
    if not docLocation or not os.path.isdir(docLocation):
        docLocation = getMayaLocation(version) # use original version
        if docLocation is None :
            docLocation = getMayaLocation(None)
            _logger.warning("Could not find an installed Maya for exact version %s, using first installed Maya location found in %s" % (version, docLocation) )

        if version:
            short_version = parseVersionStr(version, extension=False)
        else:
            short_version = Version.shortName()
        if system == 'Darwin':
            docLocation = os.path.dirname(os.path.dirname(docLocation))
            
        docLocation = os.path.join(docLocation , 'docs/Maya%s/en_US' % short_version)

    return docLocation

def refreshEnviron():
    """
    copy the shell environment into python's environment, as stored in os.environ
    """ 
    exclude = ['SHLVL'] 
    
    if system in ('Darwin', 'Linux'):
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

def recurseMayaScriptPath(roots=[], verbose=False, excludeRegex=None, errors='warn'):
    """
    Given a path or list of paths, recurses through directories appending to the MAYA_SCRIPT_PATH
    environment variable
    
    :Parameters:
        roots
            a single path or list of paths to recurse. if left to its default, will use the current 
            MAYA_SCRIPT_PATH values
            
        verobse : bool
            verbose on or off
            
        excludeRegex : str
            string to be compiled to a regular expression of paths to skip.  This regex only needs to match
            the folder name
        
    """
    
    regex = '[.]|(obsolete)'

    if excludeRegex:
        assert isinstance(excludeRegex, basestring), "please pass a regular expression as a string" 
        regex = regex + '|' + excludeRegex
    
    includeRegex =  "(?!(" + regex + "))" # add a negative lookahead assertion
        
#    try:
#        excludeRegex = re.compile(  regex  ) 
#        
#    except Exception, e:
#        _logger.error(e)
    
    #print "------------starting--------------"
    #for x in os.environ.get(envVariableName, '').split(':'): print x
    
    try :
        from maya.cmds import about
        if about(batch=1):
            refreshEnviron() 
    except ImportError:
        pass

    #print "---------"
    #for x in os.environ.get(envVariableName, '').split(':'): print x

    ## if passed an rootsument  then only expand the rootsument string 

    if roots:
        if isinstance( roots, list) or isinstance( roots, tuple):
            rootVars = list(roots)
        else:
            rootVars = [roots]
    ##  else expand the whole  environment  currently set 
    else:
        rootVars = os.environ["MAYA_SCRIPT_PATH"].split(os.path.pathsep)
        
    varList = rootVars[:]
    
    _logger.info("Recursing Maya script path")
    _logger.debug( "Only directories which match %s will be traversed" % includeRegex )
    for rootVar in rootVars:
        root = _path( rootVar )
        if re.match( includeRegex, root.name ):
            _logger.debug( "Searching for all valid script directories below %s" % rootVar )
            # TODO: fix walkdirs so we can pass our regular expression directly to it. this will prevent us from descending into directories whose parents have failed
            for f in root.walkdirs( errors=errors, regex=includeRegex ):
                try:
                    if len(f.files("*.mel")):            
                        if f not in varList:
                            _logger.debug("Appending script path directory %s" % f)
                            varList.append( str(f) )
                        
                except OSError: pass
    
    if varList > rootVars:
        os.environ["MAYA_SCRIPT_PATH"] = os.path.pathsep.join( varList )
        _logger.info("Added %d directories to Maya script path" % (len(varList) - len(rootVars)) )

    else:
        _logger.info("Maya script path recursion did not find any paths to add")


def loadDynamicLibs():
    """
    due to a bug in maya.app.commands many functions do not return any value the first time they are run,
    especially in standalone mode.  this function forces the loading of all dynamic libraries, which is
    a very fast and memory-efficient process, which begs the question: why bother dynamically loading?
    
    this function can only be run after maya.standalone is initialized
    """
            
    commandListPath = os.path.realpath( os.environ[ 'MAYA_LOCATION' ] )
    commandListPath = os.path.join( commandListPath, libdir, 'commandList' )

    import maya.cmds
    assert hasattr( maya.cmds, 'dynamicLoad'), "maya.standalone must be initialized before running this function"
    file = open( commandListPath, 'r' )
    libraries = set( [ line.split()[1] for line in file] )
    for library in libraries:
        try:
            maya.cmds.dynamicLoad(library)
        except RuntimeError:
            _logger.debug("Error dynamically loading maya library: %s" % library)

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
    global isInitializing
    
    # test that Maya actually is loaded and that commands have been initialized,for the requested version

    try :
        from maya.cmds import about
        # if this succeeded, we're initialized
        isInitializing = False
        if not pymelMayaPackage: 
            loadDynamicLibs() # fixes that should be run on a standard maya package
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
            
            #if Version.current < Version.v2009:
            #    refreshEnviron()

        except ImportError, e:
            raise e, str(e) + ": pymel was unable to intialize maya.standalone"

    try:
        from maya.cmds import about
    except Exception, e:
        raise e, str(e) + ": maya.standalone was successfully initialized, but pymel failed to import maya.cmds"
    
    # return True, meaning we had to initialize maya standalone
    isInitializing = True
    if not pymelMayaPackage: 
        loadDynamicLibs() # fixes that should be run on a standard maya package
    return True

def initMEL():
    if 'PYMEL_SKIP_MEL_INIT' in os.environ or pymel_options.get( 'skip_mel_init', False ) :
        _logger.info( "Skipping MEL initialization" )
        return
    
    _logger.debug( "initMEL" )        
    import maya.mel
    
    mayaVersion = Version.installName()
    try:
        prefsDir = os.path.join( getMayaAppDir(), mayaVersion, 'prefs' )
    except:
        _logger.error( "could not perform maya initialization sequence: MAYA_APP_DIR not set" )
    else:
        # TODO : use cmds.internalVar to get paths
        # got this startup sequence from autodesk support
        startup = [   
            #'defaultRunTimeCommands.mel',  # sourced automatically
            #os.path.join( prefsDir, 'userRunTimeCommands.mel'), # sourced automatically
            'createPreferencesOptVars.mel',
            'createGlobalOptVars.mel',
            os.path.join( prefsDir, 'userPrefs.mel'),
            'initialStartup.mel',
            #$HOME/Documents/maya/projects/default/workspace.mel
            'initialPlugins.mel',
            #'initialGUI.mel', #GUI
            #'initialLayout.mel', #GUI
            #os.path.join( prefsDir, 'windowPrefs.mel'), #GUI
            #os.path.join( prefsDir, 'menuSetPrefs.mel'), #GUI
            #'hotkeySetup.mel', #GUI
            'namedCommandSetup.mel',
            os.path.join( prefsDir, 'userNamedCommands.mel' ),
            #'initAfter.mel', #GUI
            os.path.join( prefsDir, 'pluginPrefs.mel' ),
        ]
        try:
            for f in startup:
                if isinstance(f, unicode):
                    encoding = 'unicode_escape'
                else:
                    encoding = 'string_escape'
                # need to encode backslashes (used for windows paths)
                maya.mel.eval( 'source "%s"' % f.encode(encoding) )
                
        except Exception, e:
            _logger.error( "could not perform maya initialization sequence: failed on %s: %s" % ( f, e) )
        
    try:
        # make sure it exists
        res = maya.mel.eval('whatIs "userSetup.mel"')
        if res != 'Unknown':
            maya.mel.eval( 'source "userSetup.mel"')
    except RuntimeError: pass


def finalize():
    if MGlobal.mayaState() in [MGlobal.kBatch, MGlobal.kLibraryApp]:
        global isInitializing
        if pymelMayaPackage and isInitializing:
            import maya.app.startup.common
            maya.app.startup.common.executeUserSetup()
        initMEL()
        
                       
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

def loadCache( filePrefix, description='', useVersion=True):
    if useVersion:
        short_version = Version.shortName()
    else:
        short_version = ''
    newPath = os.path.join( _moduleDir(),  filePrefix+short_version+'.bin' )
    
    if description:
        description = ' ' + description
    try :
        file = open(newPath, mode='rb')
        try :
            return pickle.load(file)
        except Exception, e:
            _logger.warn("Unable to load%s from '%s': %s" % (description,file.name, e))
        
        file.close()
    except Exception, e:
        _logger.warn("Unable to open '%s' for reading%s: %s" % ( newPath, description, e ))

 
def writeCache( data, filePrefix, description='', useVersion=True):
    _logger.debug("writing cache")
    
    if useVersion:
        short_version = Version.shortName()
    else:
        short_version = ''
    newPath = os.path.join( _moduleDir(),  filePrefix+short_version+'.bin' )

    if description:
        description = ' ' + description
    
    _logger.info("Saving%s to '%s'" % ( description, newPath ))
    try :
        file = open(newPath, mode='wb')
        try :
            pickle.dump( data, file, 2)
            _logger.debug("done")
        except:
            _logger.debug("Unable to write%s to '%s'" % (description,file.name))
        file.close()
    except :
        _logger.debug("Unable to open '%s' for writing%s" % ( newPath, description ))
                 

def getConfigFile():
    return plogging.getConfigFile()

def parsePymelConfig():
    import ConfigParser

    types = { '0_7_compatibility_mode' : 'boolean',
              'skip_mel_init' : 'boolean' }
    
    defaults = { '0_7_compatibility_mode' : 'off',
                 'skip_mel_init' : 'off' }
    
    config = ConfigParser.ConfigParser(defaults)
    config.read( getConfigFile() )
    
    d = {}
    for option in config.options('pymel'):
        getter = getattr( config, 'get' + types.get(option, '') ) 
        d[option] = getter( 'pymel', option )
    return d

def executeDeferred(func):
    """
    This is a wrap for maya.utils.executeDeferred.  Maya's version does not execute at all when in batch mode, so this
    function does a simple check to see if we're in batch or interactive mode.  In interactive it runs maya.utils.executeDeferred,
    and if we're in batch mode, it just executes the function.
    
    Use this function in your userSetup.py file if:
        1. you are importing pymel there
        2. you want to execute some code that relies on maya.cmds
        3. you want your userSetup.py to work in both interactive and standalone mode
    
    Example userSetup.py file::
    
        from pymel import *
        def delayedStartup():
           print "executing a command"
           pymel.about(apiVersion=1)
        pymel.mayahook.executeDeferred( delayedStartup )
       
    Takes a single parameter which should be a callable function.
    
    """
    import maya.utils
    import maya.OpenMaya
    if maya.OpenMaya.MGlobal.mayaState() == maya.OpenMaya.MGlobal.kInteractive:
        maya.utils.executeDeferred(func)
    else:
        func()
   

pymel_options = parsePymelConfig() 

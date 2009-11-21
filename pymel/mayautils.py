import os, sys, re, platform
import versions
import internal as _internal
_logger = _internal.getLogger(__name__) 
from pymel.util import path as _path, shellOutput, picklezip


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
        actual_long_version = versions.installName()
        actual_short_version = versions.shortName()
        if version != actual_long_version:
            short_version = versions.parseVersionStr(version, extension=False)
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
    
        from pymel.all import *
        def delayedStartup():
           print "executing a command"
           pymel.about(apiVersion=1)
        mayautils.executeDeferred( delayedStartup )
       
    Takes a single parameter which should be a callable function.
    
    """
    import maya.utils
    import maya.OpenMaya
    if maya.OpenMaya.MGlobal.mayaState() == maya.OpenMaya.MGlobal.kInteractive:
        maya.utils.executeDeferred(func)
    else:
        func()

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
    app_dir = os.environ.get('MAYA_APP_DIR',None)
    if app_dir is None :
        if system == 'Window':
            app_dir = os.environ.get('USERPROFILE',os.environ.get('HOME',None))
            if app_dir is None:
                return
            
            # Vista or newer... version() returns "6.x.x"
            if int(platform.version().split('.')[0]) > 5:
                app_dir = os.path.join( app_dir, 'Documents')
            else:
                app_dir = os.path.join( app_dir, 'My Documents')
        else:
            app_dir = os.environ.get('HOME',None)
            if app_dir is None:
                return
            
        if system == 'Darwin':
            app_dir = os.path.join( app_dir, 'Library/Preferences/Autodesk/maya' )    
        else:
            app_dir = os.path.join( app_dir, 'maya' )
            
    return app_dir


def mayaDocsLocation(version=None):
    docLocation = None
    if (version == None or version == versions.installName() ) and mayaIsRunning():
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
            short_version = versions.parseVersionStr(version, extension=False)
        else:
            short_version = versions.shortName()
        if system == 'Darwin':
            docLocation = os.path.dirname(os.path.dirname(docLocation))
            
        docLocation = os.path.join(docLocation , 'docs/Maya%s/en_US' % short_version)

    return os.path.realpath(docLocation)

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
    
    _logger.debug("Recursing Maya script path")
    _logger.debug( "Only directories which match %s will be traversed" % includeRegex )
    for rootVar in rootVars:
        root = _path( rootVar )
        if re.match( includeRegex, root.name ) and root.exists():
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


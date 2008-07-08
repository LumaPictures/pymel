import re, os, sys, platform

import envparse

#from maya.cmds import encodeString

# is this still needed ?
if os.name == 'nt' :
    maya = 'maya.exe'
    sep = ';'
else :
    maya = 'maya.bin'
    sep = ':'
    
# A source commande that will search for the Python script "file" in the specified path
# (using the system path if none is provided) path and tries to call execfile() on it
def source (file, searchPath=None, recurse=False) :
    """Looks for a python script in the specified path (uses system path if no path is specified)
        and executes it if it's found """
    filepath = os.path(file)
    filename = filepath.basename()
    if searchPath is None :
        searchPath=sys.path
    if not util.isIterable(searchPath) :
        searchPath = list((searchPath,))
    itpath = iter(searchPath)
    #print "looking for file as: "+filepath
    while not filepath.exists() :
        try :
            p = os.path(itpath.next()).realpath().abspath()
            filepath = filepath.joinpath(p, filename)
            #print 'looking for file as: '+filepath
            if recurse and not filepath.exists() :
                itsub = os.walk(p)
                while not filepath.exists() :
                    try :
                        root, dirs, files = itsub.next()
                        itdirs = iter(dirs)
                        while not filepath.exists() :
                            try :
                                filepath = filepath.joinpath(Path(root), os.path(itdirs.next()), filename)
                                #print 'looking for file as: '+filepath
                            except :
                                pass
                    except :
                        pass
        except :
            raise ValueError, "File '"+filename+"' not found in path"
            # In case the raise exception is replaced by a warning don't forget to return here
            return
    # print "Executing: "+filepath
    return execfile(filepath)


def getMayaLocation(version=None):
    try:
        loc = os.environ['MAYA_LOCATION']
    except:
        loc = os.path.dirname( os.path.dirname( sys.executable ) )
    
    # get the path of a different maya version than current
    if version:
        currentVersion = getMayaVersion()
        if currentVersion != version:
            loc = loc.replace( currentVersion, version )
    return loc

def getMayaVersion(extension=True):
    """ Returns the maya version (ie 2008), with extension (known one : x64 for 64 bit cuts) if extension=True """
    
    try :
        from maya.cmds import about
        versionStr = about(version=True)
    except :
        versionStr = getMayaLocation()
    
    # problem with service packs addition, must be able to match things such as :
    # '2008 Service Pack 1 x64', '2008x64', '2008', '8.5'
    ma = re.search( "((?:maya)?(?P<base>[\d.]+)(?:(?:[ ].*[ ])|(?:-))?(?P<ext>x[\d.]+)?)", versionStr)
    version = ma.group('base')
    if extension and (ma.group('ext') is not None) :
        version += "-"+ma.group('ext')
    return version

def mayaDocsLocation( version=None ):
    #docLocation = path.path( os.environ.get("MAYA_LOCATION", '/Applications/Autodesk/maya%s/Maya.app/Contents' % version) )
    
    docLocation = getMayaLocation(version) # use original version
    if version == None :
        version = getMayaVersion(extension=False)
    
    
    import platform
    if platform.system() == 'Darwin':
        docLocation = os.path.dirname( os.path.dirname( docLocation ) )
    docLocation = os.path.join( docLocation , 'docs/Maya%s/en_US' % version )
    return docLocation
                      
# parse the Maya.env file and set the environement variablas and python path accordingly
def parseMayaenv(envLocation=None, version=None) :
    """ parse the Maya.env file and set the environement variablas and python path accordingly.
        You can specify a location for the Maya.env file or the Maya version"""
    name = 'Maya.env'

        
    envPath = None
    if envLocation :
        envPath = envLocation
        if not os.path.isfile(envPath) :
            envPath = os.path.join(envPath, name)
            
    # no Maya.env specified, we look for it in MAYA_APP_DIR
    if not envPath or not envPath.isfile() :
        if not os.environ.has_key('MAYA_APP_DIR') :
            home = os.environ.get('HOME', None)
            if not home :
                warnings.warn("Neither HOME nor MAYA_APP_DIR is set, unable to find location of Maya.env", ExecutionWarning)
                return False
            else :
                maya_app_dir = os.path.join(home, 'maya')
        else :
            maya_app_dir = os.environ['MAYA_APP_DIR']
        # try to find which version of Maya should be initialized
        if not version :
            # try to query version, will only work if reparsing env from a working Maya
            version = getMayaVersion(extension=True)
            if version is None:
                # if run from Maya provided mayapy / python interpreter, can guess version
                print "Unable to determine which verson of Maya should be initialized, trying for Maya.env in %s" % maya_app_dir
        # look first for Maya.env in 'version' subdir of MAYA_APP_DIR, then directly in MAYA_APP_DIR
        if version and os.path.isfile(os.path.join(maya_app_dir, version, name)) :
            envPath = os.path.join(maya_app_dir, version, name)
        else :
            envPath = os.path.join(maya_app_dir, name)

    # finally if we have a possible Maya.env, parse it
    if os.path.isfile(envPath) :
        try :
            envFile = open(envPath)
        except :
            warnings.warn ("Unable to open Maya.env file %s" % envPath, ExecutionWarning)
            return False
        success = False
        try :
            envTxt = envFile.read()
            envVars = envparse.parse(envTxt)
            # update env vars
            for v in envVars :
                #print "%s was set or modified" % v
                os.environ[v] = envVars[v]
            # add to syspath
            if envVars.has_key('PYTHONPATH') :
                #print "sys.path will be updated"
                plist = os.environ['PYTHONPATH'].split(sep)
                for p in plist :
                    if not p in sys.path :
                        sys.path.append(p)
            success = True
        finally :
            envFile.close()
            return success
    else :
        if version :
            print"Found no suitable Maya.env file for Maya version %s" % version
        else :
            print"Found no suitable Maya.env file"
        return False

def _addEnv( env, value ):
    if os.name == 'nt' :
        sep = ';'
    else :
        sep = ':'
    if env not in os.environ:
        os.environ[env] = value
    else:
        os.environ[env] = sep.join( os.environ[env].split(sep) + [value] )
                    
# Will test initialize maya standalone if necessary (like if scripts are run from an exernal interpeter)
# returns True if Maya is available, False either
def mayaInit(forversion=None) :
    """ Try to init Maya standalone module, use when running pymel from an external Python inerpreter,
    it is possible to pass the desired Maya version number to define which Maya to initialize """

    # test that Maya actually is loaded and that commands have been initialized,for the requested version        
    try :
        from maya.cmds import about        
        version = eval("about(version=True)");
    except :
        version = None

    if forversion :
        if version == forversion :
            return True
        else :
            print "Maya is already initialized as version %s, initializing it for a different version %s" % (version, forversion)
    elif version :
            return True
                
    # reload env vars, define MAYA_ENV_VERSION in the Maya.env to avoid unneeded reloads
    envVersion = os.environ.get('MAYA_ENV_VERSION', None)
    
    if (forversion and envVersion!=forversion) or not envVersion :
        if not parseMayaenv(version=forversion) :
            print "Could not read or parse Maya.env file"
    
    # add necessary environment variables and paths for importing maya.cmds, a la mayapy
    # currently just for osx
    if platform.system() == 'Darwin' :
        frameworks = os.path.join( os.environ['MAYA_LOCATION'], 'Frameworks' )    
        _addEnv( 'DYLD_FRAMEWORK_PATH', frameworks )
        
        # this *must* be set prior to launching python
        #_addEnv( 'DYLD_LIBRARY_PATH', os.path.join( os.environ['MAYA_LOCATION'], 'MacOS' ) )
        # in lieu of setting PYTHONHOME like mayapy which must be set before the interpretter is launched, we can add the maya site-packages to sys.path
        try:
            pydir = os.path.join(frameworks, 'Python.framework/Versions/Current')
            mayapyver = os.path.split( os.path.realpath(pydir) )[-1]
            #print os.path.join( pydir, 'lib/python%s/site-packages' % mayapyver )
            sys.path.append(  os.path.join( pydir, 'lib/python%s/site-packages' % mayapyver ) )
        except:
            pass    
        
    if not sys.modules.has_key('maya.standalone') or version != forversion:
        try :
            import maya.standalone #@UnresolvedImport
            maya.standalone.initialize(name="python")
        except :
            pass

    try :
        from maya.cmds import about    
        reload(maya.cmds) #@UnresolvedImport
        version = eval("about(version=True)")
        return (forversion and version==forversion) or version
    except :
        return False

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
                    print "Unable to import maya.app.baseUI"    
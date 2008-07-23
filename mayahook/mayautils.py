import re, os, sys, platform, commands

import envparse

#from maya.cmds import encodeString

# is this still needed ?
if os.name == 'nt' :
    maya = 'maya.exe'
    sep = os.path.pathsep
else :
    maya = 'maya.bin'
    sep = os.path.pathsep

SYSTEM = platform.system()

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
        loc = os.path.realpath( os.environ['MAYA_LOCATION'] )
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

def refreshEnviron():
    exclude = ['SHLVL'] 
    if platform.system() in [ 'Darwin', 'Linux' ]: envcmd = '/usr/bin/env' 
    else:  envcmd = 'set' 
    for line in commands.getoutput(envcmd).split( '\n' ): 
            var, val = line.split('=') 
            if not var.startswith('_') and var not in exclude: 
                    os.environ[var] = val 
                                         
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

def _addEnv( env, value, put=False ):
    sep = os.path.pathsep
    if env not in os.environ:
        print "adding", env, value
        os.environ[env] = value
    else:
        splitEnv = os.environ[env].split(sep)
        if value not in splitEnv:
            splitEnv.append(value)
            print "adding", env, value
            os.environ[env] = sep.join( splitEnv )
    
    # i believe os.putenv is triggered by modifying os.environ, so this should not be necessary ?
    if put :
        os.putenv(env, os.environ[env])



def recurseMayaScriptPath(roots=[], verbose=False):
    """
    Given a path or list of paths, recurses through directories appending to the MAYA_SCRIPT_PATH
    environment variable
    :param roots: a single path or list of paths to recurse. if left to its default, will use the current 
        MAYA_SCRIPT_PATH values as the roots.
    """
    import path
    
    envVariableName = "MAYA_SCRIPT_PATH"
    
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
        rootVars = os.environ[envVariableName].split(os.path.pathsep)
        
    varList = rootVars[:]
    
    if verbose:
        print "\n###############################"
        print "  Recursing Maya Script Path :\n"
    for rootVar in rootVars:
        root = path.path( rootVar )
        for f in root.walkdirs( errors='ignore'):
            try:
                if not f.startswith( '.' ) and len(f.files("*.mel")):            
                    if f not in varList:
                        if verbose: print "     --> Adding : ", f
                        varList.append( str(f) )
            except OSError: pass
    
    if varList > rootVars:
        os.environ[envVariableName] = ':'.join( varList )
        if verbose:
            print "\nMaya Script Path Recursion:  DONE! "
            print "#######################################"
    else:
        if verbose:
            print "\nMaya Script Path Recursion: Nothing To do"
            print "#######################################"



def setMayaDefaultEnvs(version):
    """
    sets environment variables to their maya defaults
    """
    
    if SYSTEM == 'Darwin':
        share = '/Users/Shared/Autodesk'
    
    # single value variables
    try:
        mayaloc = os.environ['MAYA_LOCATION']
    except:
        mayaloc = os.path.dirname( os.path.dirname( sys.executable ) )
        os.environ['MAYA_LOCATION'] = mayaloc
        
    try:
        appdir = os.environ['MAYA_APP_DIR']
    except KeyError:
        appdir = os.environ['HOME']
        os.environ['MAYA_APP_DIR'] = os.path.join( appdir, 'maya' )

    # list variables
    
    
    # MAYA_PLUG_IN_PATH
    try:
        pluginPaths = [ os.environ['MAYA_PLUG_IN_PATH'] ]
    except KeyError:
        pluginPaths = []
    pluginPaths.append( os.path.join(appdir, version, 'plug-ins') )
    pluginPaths.append( os.path.join(appdir, 'plug-ins') )
    pluginPaths.append( os.path.join(share, version, 'plug-ins') )
    pluginPaths.append( os.path.join(share, 'plug-ins') )
    pluginPaths.append( os.path.join(mayaloc, 'plug-ins') ) 
    os.environ['MAYA_PLUG_IN_PATH'] =  os.path.pathsep.join( pluginPaths )


    # MAYA_MODULE_PATH
    try:
        modulePaths = [ os.environ['MAYA_MODULE_PATH'] ]
    except KeyError:
        modulePaths = []
    modulePaths.append( os.path.join(appdir, version, 'modules') )
    modulePaths.append( os.path.join(appdir, 'modules') )
    modulePaths.append( os.path.join(mayaloc, 'modules') )
    os.environ['MAYA_MODULE_PATH'] =  os.path.pathsep.join( modulePaths )
    
    # MAYA_SCRIPT_PATH
    try:
        scriptPaths = [ os.environ['MAYA_SCRIPT_PATH'] ]
    except KeyError:
        scriptPaths = []
    scriptPaths.append( os.path.join(appdir, version, 'scripts') )
    scriptPaths.append( os.path.join(appdir, 'scripts') )
    scriptPaths.append( os.path.join(appdir, version, 'presets') )
    scriptPaths.append( os.path.join(share, version, 'scripts') )
    scriptPaths.append( os.path.join(share, 'scripts') )
    try:
        # only added if it exists
        scriptPaths.append( os.environ['MAYA_SHELF_PATH'] )
    except KeyError: pass
    if system == 'Darwin':
        scriptPaths.append( os.path.join(mayaloc, 'MacOS', 'scripts') ) 
    
    scriptPaths.append( os.path.join(appdir, version, 'prefs', 'shelves' ) ) 
    scriptPaths.append( os.path.join(appdir, version, 'prefs', 'markingMenus' ) ) 
    scriptPaths.append( os.path.join(appdir, version, 'prefs', 'scripts' ) ) 
    
    scriptPaths.append( os.path.join(mayaloc, 'scripts') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'startup') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'others') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'AETemplates') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'unsupported') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'paintEffects') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'fluidEffects') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'hair') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'cloth') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'live') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'fur') ) 
    scriptPaths.append( os.path.join(mayaloc, 'scripts', 'muscle') ) 
    os.environ['MAYA_SCRIPT_PATH'] =  os.path.pathsep.join( scriptPaths )
      

         
# Will test initialize maya standalone if necessary (like if scripts are run from an exernal interpeter)
# returns True if Maya is available, False either
def mayaInit(forversion=None) :
    """ Try to init Maya standalone module, use when running pymel from an external Python inerpreter,
    it is possible to pass the desired Maya version number to define which Maya to initialize """

    # test that Maya actually is loaded and that commands have been initialized,for the requested version        
    try :
        from maya.cmds import about        
        runningVersion = eval("about(version=True)");
    except :
        runningVersion = None

    if forversion :
        if runningVersion == forversion :
            # maya is initialized and its the version we want. we're done
            return True
        else :
            print "Maya is already initialized as version %s, initializing it for a different version %s" % (runningVersion, forversion)
    elif runningVersion :
        print "Maya is already initialized as version %s" % (runningVersion)
        return True
                
    # reload env vars, define MAYA_ENV_VERSION in the Maya.env to avoid unneeded reloads
    sep = os.path.pathsep
    mayaVersion = getMayaVersion(extension=True)
    pythonVersion = { '8.5' : '2.4',
                      '2008' : '2.5'}[getMayaVersion(extension=False)]
                      
    envVersion = os.environ.get('MAYA_ENV_VERSION', None)
    
#    if (forversion and envVersion!=forversion) or not envVersion :
#        # NOTE : is it even possible to change versions during a session? PYTHONHOME will likely point to an incompatible version of python
#        if not parseMayaenv(version=forversion) :
#            print "Could not read or parse Maya.env file"
#        #setMayaDefaultEnvs(forversion)
    
    # now we should have correct en vars
    envVersion = os.environ.get('MAYA_ENV_VERSION', mayaVersion)
    mayaLocation = os.environ['MAYA_LOCATION']
    system = platform.system()
    
    
    # add necessary environment variables and paths for importing maya.cmds, a la mayapy
#    if system == 'Darwin' :
#        frameworks = os.path.join( mayaLocation, 'Frameworks' )    
#        _addEnv( 'DYLD_FRAMEWORK_PATH', frameworks )
#        
#        # this *must* be set prior to launching python
#        _addEnv( 'DYLD_LIBRARY_PATH', os.path.join( mayaLocation, 'MacOS' ) )
#        
#        pyhomeReal = os.environ.get('PYTHONHOME')
#        pyhomeMaya = os.path.join( frameworks, 'Python.framework/Versions/Current' )
#        #print pyhomeReal, pyhomeMaya
#        if pyhomeReal is None or not os.path.samefile( pyhomeReal, pyhomeMaya ):
#            pydir = os.path.join( pyhomeMaya, 'lib/python%s/site-packages' % pythonVersion )
#            print "adding", pydir
#            sys.path.append(  pydir  )
#
#        
#    elif system == 'Linux' :
#        # TODO : seems to fail (not taken into account by the import maya.standalone
#        # even with using putenv, guess it must be set before Python is started
#        libdir = os.path.join( mayaLocation, 'lib' )
#        _addEnv( 'LD_LIBRARY_PATH', libdir, put=True )
#        
#        pyhomeReal = os.environ.get('PYTHONHOME', '')
#        pyhomeMaya = mayaLocation
#        
#        if not os.path.samefile( pyhomeReal, pyhomeMaya ):
#            pydir = os.path.join( pyhomeMaya, 'lib/python%s/site-packages' % pythonVersion )
#            print "adding", pydir
#            sys.path.append(  pydir  )
#  
#
#    else :
#        # TOTO: do something for Windows here 
#        print "Nothing planned for platform: %s" % (system)
                    
    if not sys.modules.has_key('maya.standalone') or version != forversion:
        try :
            import maya.standalone #@UnresolvedImport
            maya.standalone.initialize(name="python")
            refreshEnviron()
        except ImportError:
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
import sys, os.path, re, shutil
from collections import defaultdict
from pprint import pprint

assert sys.version_info > (2,5), "pymel version 1.0 is only supported for Maya2008/python2.5 or later"

IMPORT_RE = re.compile( '(\s*import\s+(?:[a-zA-Z0-9_.,\s]+,\s*)?)(pymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*)((?:\s*,\s*[a-zA-Z][a-zA-Z0-9_.,\s]+)?(?:\s+as\s+([a-zA-Z][a-zA-Z0-9_]+))?(?:\s*))$' )
FROM_RE = re.compile( '(\s*from\s+)(pymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*)((?:\s+import\s+([*]|(?:[a-zA-Z0-9_.,\s]+)))(?:\s*))$' )
#([a-zA-Z][a-zA-Z_.]+)([a-zA-Z][a-zA-Z_.]+)

LOGNAME = 'pymel_upgrade.log'
BACKUPEXT = '.pmbak'

last_logfile = None

def _getMayaAppDir():
    if not os.environ.has_key('MAYA_APP_DIR') :
        home = os.environ.get('HOME', os.environ.get('USERPROFILE', None) )
        if not home :
            return None
        else :
            if sys.platform == 'darwin':
                return os.path.join(home, 'Library/Preferences/Autodesk/maya')
            else:
                return os.path.join(home, 'maya')
    return os.environ['MAYA_APP_DIR']

def _parseVersionStr(versionStr, extension=False):
    """
    >>> from pymel.all import *
    >>> version._parseVersionStr('2008 Service Pack1 x64')
    '2008'
    >>> version._parseVersionStr('2008 Service Pack1 x64', extension=True)
    '2008-x64'
    >>> version._parseVersionStr('2008x64', extension=True)
    '2008-x64'
    >>> version._parseVersionStr('8.5', extension=True)
    '8.5'
    >>> version._parseVersionStr('2008 Extension 2')
    '2008'
    >>> version._parseVersionStr('/Applications/Autodesk/maya2009/Maya.app/Contents', extension=True)
    '2009'
    >>> version._parseVersionStr('C:\Program Files (x86)\Autodesk\Maya2008', extension=True)
    '2008'

    """
    # problem with service packs addition, must be able to match things such as :
    # '2008 Service Pack 1 x64', '2008x64', '2008', '8.5'

    # NOTE: we're using the same regular expression (_parseVersionStr) to parse both the crazy human readable
    # maya versions as returned by about, and the maya location directory.  to handle both of these i'm afraid 
    # the regular expression might be getting unwieldy

    ma = re.search( "((?:maya)?(?P<base>[\d.]{3,})(?:(?:[ ].*[ ])|(?:-))?(?P<ext>x[\d.]+)?)", versionStr)
    version = ma.group('base')

    if extension and (ma.group('ext') is not None) :
        version += "-"+ma.group('ext')
    return version

def _getMayaLocation(version=None):
    """ Remember to pass the FULL version (with extension if any) to this function! """
    try:
        loc = os.path.realpath( os.environ['MAYA_LOCATION'] )
    except:
        loc = os.path.dirname( os.path.dirname( sys.executable ) )
                
    return loc

def _setupScriptPaths2():
    
    appDir = _getMayaAppDir()
    assert appDir
    
    mayaVersion = _parseVersionStr(_getMayaLocation())
    assert mayaVersion
    
    
    
    for subdirs in [    (mayaVersion, 'prefs', 'scripts'), 
                        (mayaVersion, 'scripts'), 
                        ('scripts',) ]:
        dir = os.path.join( appDir, *subdirs)
        print "adding to sys.path", dir
        sys.path.append( dir )
    
    
def setupScriptPaths():
    """
    Add Maya-specific directories to sys.path
    """
    # Per-version prefs scripts dir (eg .../maya8.5/prefs/scripts)
    #
    prefsDir = cmds.internalVar( userPrefDir=True )
    sys.path.append( os.path.join( prefsDir, 'scripts' ) )
    
    # Per-version scripts dir (eg .../maya8.5/scripts)
    #
    scriptDir = cmds.internalVar( userScriptDir=True )
    sys.path.append( os.path.dirname(scriptDir) )
    
    # User application dir (eg .../maya/scripts)
    #
    appDir = cmds.internalVar( userAppDir=True )
    sys.path.append( os.path.join( appDir, 'scripts' ) )

objects = [ 
           ( 'Version',
             re.compile('([a-zA-Z_][a-zA-Z0-9_.]+[.])?(Version[.])'), 
                       ( 'pymel',
                         'pymel.version',
                         'pymel.mayahook', 
                         'pymel.mayahook.version' ),
            'version' )
           ]

def _getLogfile(logfile, read=True):
    if logfile is None:
        global last_logfile
        if last_logfile:
            logfile = last_logfile
    
    if logfile is None:
        baseDir = _getMayaAppDir()
        if not baseDir:
            baseDir = os.curdir
        logfile = logfile = os.path.join(baseDir, LOGNAME)
        if read and not os.path.isfile( logfile ):
            raise ValueError, "could not find an existing %s. please pass the path to this file, which was generated during when upgrading" % LOGNAME
    return os.path.realpath(logfile)

def upgradeFile(filepath, test=True):
    f = open(filepath)
    lines = f.readlines()
    f.close()
    modified = False
    uses_pymel = False
    pymel_namespaces =  defaultdict(set)
    rev_pymel_namespaces =  defaultdict(set)
    for i, line in enumerate(lines):
        m = IMPORT_RE.match(line)
        mode = None
        if not m:
            m = FROM_RE.match(line)
            mode = 'from'
        else:
            mode = 'import'
        if m:
            uses_pymel = True
            
            start, pymel_module, end, details = m.groups()

            if pymel_module == 'pymel':
                lines[i] = start + 'pymel.pm' + end
                modified = True
                
            if details:
                details = details.strip()
                
#                print mode, pymel_module, details
#                if mode == 'import':
#                    curr_namespaces[details].add(pymel_module)
#                    curr_pymel_namespaces[pymel_module].add( details )
#                else: # 'from'
#                    details = '' if details == '*' else details
#                    for detail in details.split(','):
#                        curr_namespaces[detail].add(pymel_module)
            
            if mode == 'import':
                if details:
                    pymel_namespaces[pymel_module].add(details)     # pymel.version -> version
                    # import pymel.mayahook as mayahook
                    # 'mayahook' -> 'pymel.mayahook'
                    rev_pymel_namespaces[details].add(pymel_module) 
                else:
                    # 'import pymel'
                    pymel_namespaces[pymel_module].add(pymel_module)
                    
                    # import pymel.mayahook
                    # 'pymel.mayahook' -> 'pymel.mayahook'
                    rev_pymel_namespaces[pymel_module].add(pymel_module)
            
            elif mode == 'from':
                details = '' if details == '*' else details
                for detail in details.split(','):
                    if detail:
                        module = pymel_module + '.' + detail
                    else:
                        module = pymel_module
                    pymel_namespaces[pymel_module].add(detail)
                    
                    # from pymel import mayahook
                    # 'mayahook' -> 'pymel.mayahook'
                    
                    # from pymel import *
                    # '' -> 'pymel'
                    rev_pymel_namespaces[detail].add(module) 
                    
        if uses_pymel:
            for obj, reg, obj_namespaces, replace in objects:
                parts = reg.split(line)
                if len(parts) > 1:
                    #print parts
                    for j in range(0, len(parts), 3):
                        try:
                            ns = parts[j+1]
                        except IndexError, err:
                            pass
                        else:
                            ns = ns if ns else ''
                            parts[j+1] = ns
                            #print "checking namespace", `ns`, 'against', dict(rev_pymel_namespaces)
                            for namespace, orig_namespaces in rev_pymel_namespaces.iteritems():
                                if namespace == '' or ns == namespace or ns.startswith(namespace + '.'):
                                    for orig_namespace in orig_namespaces:
                                        if namespace == '':
                                            expanded_ns = orig_namespace + '.' + ns
                                        else:
                                            expanded_ns = ns.replace(namespace, orig_namespace)
                                        #print 'expanded', expanded_ns
                                        if expanded_ns.rstrip('.') in obj_namespaces:
                                            #print "found namespace", `ns`, `expanded_ns`
                                            try:
                                                pmns = list(pymel_namespaces['pymel'])[0]
                                            except IndexError:
                                                print "warning: %s: no pymel namespace was found" % filepath
                                            else:
                                                if pmns =='':
                                                    parts[j+1] = replace + '.'
                                                else:
                                                    parts[j+1] = pmns + '.' + replace + '.'
                                                parts[j+2] = None
                                            
                                            break
                    lines[i] = ''.join( [ x for x in parts if x is not None] )
                    #print 'before:', `line`
                    #print 'after: ', `lines[i]`

                                
    success = True                           
            
    if modified:
        if not test:
            tmpfile = filepath + '.tmp'
            try:
                f = open(tmpfile, 'w')
                f.writelines(lines)
            except (IOError, OSError), err:
                print "error writing temporary file: %s: %s" % ( tmpfile, err)
                success = False
            finally:
                f.close()
            
            if success:
                try:
                    os.rename(filepath, filepath + BACKUPEXT)
                except (IOError, OSError), err:
                    print "error backing up file %s to %s.pmbak: %s" % ( filepath, filepath, err)
                    success = False
                else:
                    try:
                        os.rename(tmpfile, filepath)
                    except (IOError, OSError), err:
                        print "error renaming temp file: %s" % ( err)
                        success = False
                        print "attempting to restore original file"
                        try:
                            os.rename(filepath + BACKUPEXT, filepath)
                        except OSError, err:
                            print "could not restore original: %s" % ( err)

    return modified, success

def upgrade(logdir=None, test=True, excludeFolderRegex=None, excludeFileRegex=None, verbose=False):
    if 'maya.app.startup.gui' not in sys.modules and 'maya.app.startup.batch' not in sys.modules:
        print "warning: in order for the python search path to be accurate, it is advisable to run this from within a Maya GUI or an initialized standalone session"
        _setupScriptPaths2()
    
    if test:
        print "running in test mode. set test=False to enable file editing"
    
    if excludeFolderRegex:
        assert isinstance(excludeFolderRegex, basestring), "excludeFolderRegex must be a string"
    if excludeFileRegex:
        assert isinstance(excludeFileRegex, basestring), "excludeFileRegex must be a string"
    

    logfile = os.path.join(_getLogfile(logdir, read=False))
    
    try:
        log = open(logfile, 'w' )
    except (IOError, OSError), err:
        print "could not create log file at %s. please pass a writable directory to 'logdir' keyword: %s" % ( logdir, err)
        return
    
    global last_logfile
    last_logfile = logfile
    
    try:
        for path in sys.path + os.environ['MAYA_SCRIPT_PATH'].split(os.pathsep):
        #for path in ['/Volumes/luma/_globalSoft/dev/chad/python/pymel']:
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith('.py') and not f.startswith('.'):
                        if not excludeFileRegex or not re.match( excludeFileRegex, file ):
                            fpath = os.path.join(root,f)
                            modified, stat = upgradeFile( fpath, test )
                            if modified and stat:
                                print 'needs upgrading:' if test else 'upgraded:', fpath
                                if not test:
                                    log.write( fpath + '\n' )
                        elif verbose:
                            print "skipping", os.path.join(root,f)
                            
                #print 'before',  root, dirs
                
                # dirs must be modified in-place
                i = 0
                tmpdirs = dirs[:]
                for dir in tmpdirs:
                    #print '\t', `dir`
                    if dir.startswith('.') or dir == 'pymel' \
                            or not os.path.isfile(os.path.join(root, dir, '__init__.py')) \
                            or ( excludeFolderRegex and re.match( excludeFolderRegex, dir ) ):
                        del dirs[i]
                        if verbose:
                            print "skipping", os.path.join(root, dir)
                    else:
                        i += 1
                #print 'after', root, dirs
                
    except Exception, err:
        import traceback
        traceback.print_exc()
    finally:
        if not test:
            print "writing log to %s" % logfile
        log.close()
    print "done"

def revertFile(filepath):
    backup = filepath + BACKUPEXT
    if os.path.isfile(backup):
        try:
            os.rename(backup, filepath )
            print "restored", filepath
        except (IOError, OSError), err:
            print "error restoring file %s.pmbak to %s: %s" % ( filepath, filepath, err)
            return False
    else:
        print "warning: backup file does not exist: %s" % backup
    return True
     
def revert(logfile=None):
    log = open(_getLogfile(logfile), 'r' )
    try:
        for file in log:
            file = file.rstrip()
            if file:
                revertFile(file)
    except Exception, err:
        import traceback
        traceback.print_exc()
    finally:
        log.close()


def cleanup(logfile=None):
    log = open(_getLogfile(logfile), 'r' )
    try:
        for file in log:
            file = file.rstrip()
            if file:
                try:
                    os.remove(file + BACKUPEXT)
                except (IOError, OSError), err:
                    print "error removing file %s.pmbak: %s" % ( file, err)

    except Exception, err:
        import traceback
        traceback.print_exc()
    finally:
        log.close()


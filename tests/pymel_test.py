#!/usr/bin/env mayapy

#nosetests --with-doctest -v pymel --exclude '(windows)|(tools)|(arrays)|(example1)'

#import doctest
from __future__ import with_statement

import sys, platform, os, shutil, time, inspect, tempfile, doctest

# tee class adapted from http://shallowsky.com/blog/programming/python-tee.html
class Tee(object):
    def __init__(self, _fd1, _fd2) :
        self.fd1 = _fd1
        self.fd2 = _fd2

    def __del__(self) :
        self.close()
            
    def close(self):
        for toClose in (self.fd1, self.fd2):
            if toClose not in (sys.stdout, sys.stderr,
                               sys.__stdout__, sys.__stderr__, None):
                toClose.close()
        self.fd1 = self.fd2 = None

    def write(self, text) :
        self.fd1.write(text)
        self.fd2.write(text)

    def flush(self) :
        self.fd1.flush()
        self.fd2.flush()

#stderrsav = sys.stderr
#outputlog = open(logfilename, "w")
#sys.stderr = tee(stderrsav, outputlog)

try:
    import nose
except ImportError, e:
    print "To run pymel's tests you must have nose installed: http://code.google.com/p/python-nose"
    raise e

# TODO: use mayautils.getMayaAppDir()
if os.name == 'nt':
    app_dir = os.environ['USERPROFILE']
    
    # Vista or newer... version() returns "6.x.x"
    if int(platform.version().split('.')[0]) > 5:
        app_dir = os.path.join( app_dir, 'Documents')
    else:
        app_dir = os.path.join( app_dir, 'My Documents')
else:
    app_dir = os.environ['HOME']
    
if platform.system() == 'Darwin':
    app_dir = os.path.join( app_dir, 'Library/Preferences/Autodesk/maya' )    
else:
    app_dir = os.path.join( app_dir, 'maya' )

backup_dir = app_dir + '.bak'

DELETE_BACKUP_ARG = '--delete-maya-user-backup'

class RemoveBackupError(Exception): pass

def nose_test(module=None, extraArgs=None, pymelDir=None):
    """
    Run pymel unittests / doctests
    """
    if pymelDir:
        os.chdir(pymelDir)
            
    os.environ['MAYA_PSEUDOTRANS_MODE']='5'
    os.environ['MAYA_PSEUDOTRANS_VALUE']=','
    
    noseKwArgs={}
    noseArgv = "dummyArg0 --with-doctest -vv".split()
    if module is None:
        #module = 'pymel' # if you don't set a module, nose will search the cwd
        excludes = r'''^windows
                    \Wall\.py$
                    ^tools
                    ^example1
                    ^testing
                    ^eclipseDebug
                    ^pmcmds
                    ^testPa
                    ^maya
                    ^maintenance
                    ^pymel_test
                    ^TestPymel
                    ^testPassContribution$'''.split()

        # default inGui to false - if we are in gui, we should be able to query
        # (definitively) that we are, but same may not be true from command line
        inGui = False
        try:
            import maya.cmds
            inGui = not maya.cmds.about(batch=1)
        except Exception: pass

        # if we're not in gui mode, disable the gui tests
        if not inGui:
            excludes.extend('^test_uitypes ^test_windows'.split())
         
        noseArgv += ['--exclude', '|'.join( [ '(%s)' % x for x in excludes ] )  ]
           
    if inspect.ismodule(module):
        noseKwArgs['module']=module
    elif module:
        noseArgv.append(module)
    if extraArgs is not None:
        noseArgv.extend(extraArgs)
    noseKwArgs['argv'] = noseArgv
    
    with DocTestPatcher():
        print noseKwArgs
        nose.main( **noseKwArgs)

def backupAndTest(extraNoseArgs):
    if os.path.isdir(backup_dir):
        print "backup dir %r already exists - aborting" % backup_dir
    else:
        print "backing up Maya user directory %s to %s" % ( app_dir, backup_dir )
        shutil.move( app_dir, backup_dir )
    
        try:
            nose_test( extraArgs=extraNoseArgs )
        except Exception, e:
            print e
        finally:
            try:
                removeBackup()
            except RemoveBackupError:
                # on windows, maya never seems to exit cleanly unless the
                # process is completely exited - it keeps open access to
                # 'mayaLog', with the result that you can't delete the
                # backup_dir.  only way I know of around this is to delete
                # backup_dir in a completely separate process...
                print "initial Maya user directory restore failed - trying from separate process"                
                
                os.spawnl(os.P_NOWAIT,
                          sys.executable, os.path.basename(sys.executable),
                          __file__, DELETE_BACKUP_ARG)

def removeBackup():
    assert os.path.isdir(backup_dir), "Maya user backup does not exist: %s" % backup_dir
    
    print "restoring Maya user directory", app_dir

    tempdir = os.path.join(tempfile.gettempdir(), 'maya')
    if os.path.exists(tempdir):
        shutil.rmtree( tempdir )
    try:            
        shutil.move(app_dir, tempdir)
    except Exception, e:
            print('Error moving "%s" to temp dir for removal: "%s": %s' %
                   (app_dir, tempdir, e))
    
    else:
        try:
            shutil.rmtree( tempdir )
        except Exception, e:
            print('Error deleting "%s" - manually delete and rename/move "%s": %s' %
                   (tempdir, backup_dir, e))
        else:
            shutil.move( backup_dir, app_dir )
            print "done"
    
def removeBackupLoop(retryTime=.1, printFailure=False):
    assert os.path.isdir(backup_dir), "Maya user backup does not exist: %s" % backup_dir
    
    print "restoring Maya user directory", app_dir

    lastException = None
    start = time.time()
    while os.path.isdir( app_dir ):
        # Check elapsed time AFTER trying to delete dir -
        # otherwise, if some other thread gets priority while we are
        # sleeping, and it's a while before the thread wakes up, we might
        # check once when almost no time has passed, sleep, wake up after
        # a lot of time has passed, and not check again...
        try:
            tempdir = os.path.join(tempfile.gettempdir(), 'maya')
            if os.path.exists(tempdir):
                shutil.rmtree( tempdir )
            shutil.move(app_dir, tempdir)
            shutil.rmtree( tempdir )
        except Exception, e:
            lastException = e
            # print("print - unable to delete '%s' - elapsed time: %f" %
            #        (app_dir, time.time() - start))
            time.sleep(.2)
        else:
            lastException = None
            
        if time.time() - start > retryTime:
            break

    if lastException is not None:
        if printFailure:
            print('Error deleting "%s" - manually delete and rename/move "%s": %s' %
                   (app_dir, backup_dir, lastException))
        raise RemoveBackupError
    else:  
        shutil.move( backup_dir, app_dir )
        print "done"

class DocTestPatcher(object):
    """
    When finding docstrings from a module, DocTestFinder does a test to ensure that objects
    in the namespace are actually from that module. Unfortunately, our LazyLoadModule causes
    some problems with this.  Eventually, we may experiment with setting the LazyLoadModule
    and original module's dict's to be the same... for now, we use this class to override
    DocTestFinder._from_module to return the results we want.
    
    Also, the doctest will override the 'wantFile' setting for ANY .py file,
    even it it matches the 'exclude' - it does this so that it can search all
    python files for docs to add to the doctests.
    
    Unfortunately, if some modules are simply loaded, they can affect things -
    ie, if pymel.all is loaded, it will trigger the lazy-loading of all class
    objects, which will make our lazy-loading tests fail.
    
    To get around this, override the Doctest plugin object's wantFile to also
    exclude the 'excludes'.
    """
    def __enter__(self):
        self.set_from_module()
        self.set_wantFile()
        
    def set_from_module(self):
        self.orig_from_module = doctest.DocTestFinder.__dict__['_from_module']
        
        def _from_module(docTestFinder_self, module, object):
            """
            Return true if the given object is defined in the given
            module.
            """
            # We only have problems with functions...
            if inspect.isfunction(object):
                if 'LazyLoad' in module.__class__.__name__:
                    if module.__name__ == object.__module__:
                        return True
            return self.orig_from_module(docTestFinder_self, module, object)
        doctest.DocTestFinder._from_module = _from_module
        
    def set_wantFile(self):
        import nose
#        if nose.__versioninfo__ > (1,0,0):
#            self.orig_wantFile = None
#            return 

        import nose.plugins.doctests
        self.orig_wantFile = nose.plugins.doctests.Doctest.__dict__['wantFile']
        
        def wantFile(self, file):
            """Override to select all modules and any file ending with
            configured doctest extension.
            """
            # Check if it's a desired file type
            if ( (file.endswith('.py') or (self.extension
                                           and anyp(file.endswith, self.extension)) )
                 # ...and that it isn't excluded
                 and (not self.conf.exclude
                      or not filter(None, 
                                    [exc.search(file)
                                     for exc in self.conf.exclude]))):
                return True
            return None

        nose.plugins.doctests.Doctest.wantFile = wantFile
        
    def __exit__(self, *args, **kwargs):
        doctest.DocTestFinder._from_module = self.orig_from_module
        if self.orig_wantFile is not None:
            import nose.plugins.doctests
            nose.plugins.doctests.Doctest.wantFile = self.orig_wantFile

if __name__ == '__main__':
    if DELETE_BACKUP_ARG not in sys.argv:
        #backupAndTest(sys.argv[1:])
        oldPath = os.getcwd()
        testsDir = os.path.dirname(os.path.abspath(sys.argv[0]) )
        pymelRoot = os.path.dirname( testsDir )
        noseArgs = sys.argv[1:]

        # make sure our cwd is the pymel project working directory
        os.chdir( pymelRoot )

        pypath = os.environ['PYTHONPATH'].split(os.pathsep)
        # add the test dir to the python path - that way,
        # we can do 'pymel_test test_general' in order to run just the tests
        # in test_general
        sys.path.append(testsDir)
        pypath.append(testsDir)

        # ...and add this copy of pymel to the python path, highest priority,
        # to make sure it overrides any 'builtin' pymel/maya packages
        sys.path.insert(0, pymelRoot)
        pypath.insert(0, pymelRoot)

        os.environ['PYTHONPATH'] = os.pathsep.join(pypath)

        nose_test(extraArgs=noseArgs)
        os.chdir(oldPath)
    else:
        # Maya may take some time to shut down / finish writing to files - 
        # give it 2 seconds
        #removeBackupLoop(retryTime=2, printFailure=True)
        removeBackup()

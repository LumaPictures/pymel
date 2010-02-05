"""
This module provides functions for upgrading scripts from pymel 0.9 to 1.0.  It
fixes two types non-compatible code:
    - pymel.all is now the main entry-point for loading all pymel modules
        - import pymel         --> import pymel.all as pymel
        - import pymel as pm   --> import pymel.all as pm
        - from pymel import *  --> from pymel.all import *
    - pymel.mayahook.versions.Version is now pymel.versions

To use, run this in a script editor tab::

    import pymel.tools.upgradeScripts
    pymel.tools.upgradeScripts.upgrade()

This will print out all the modules that will be upgraded.  If everything looks good
run the following to perform the upgrade::

    pymel.tools.upgradeScripts.upgrade(test=False)

Once you're sure that the upgrade went smoothly, run::

    pymel.tools.upgradeScripts.cleanup()

This will delete the backup files.

If you need to undo the changes, run::

    pymel.tools.upgradeScripts.undo()

Keep in mind that this will restore files to their state at the time that you ran
``upgrade``.  If you made edits to the files after running ``upgrade`` they will
be lost.
"""


import sys, os.path, re, shutil
from collections import defaultdict
import pymel.core # we don't use this, but it ensures that maya and sys.path are properly initialized

#IMPORT_RE = re.compile( '(\s*import\s+(?:[a-zA-Z0-9_.,\s]+,\s*)?)(pymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*)((?:\s*,\s*[a-zA-Z][a-zA-Z0-9_.,\s]+)?(?:\s+as\s+([a-zA-Z][a-zA-Z0-9_]+))?(?:\s*))$' )
#IMPORT_RE = re.compile( r'(\s*import\s+(?:.*))(\bpymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*)(?:\s+as\s+([a-zA-Z][a-zA-Z0-9_]+))?(.*)$' )
IMPORT_RE = re.compile( r'(?P<start>\s*import\s+.*)(?P<pymel>\bpymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*\b)(?P<end>(?:\s+as\s+(?P<details>[a-zA-Z][a-zA-Z0-9_]+))?(?:.|\s)*)$' )
FROM_RE = re.compile( r'(?P<start>\s*from\s+)(?P<pymel>pymel(?:[.][a-zA-Z][a-zA-Z0-9_]+)*)(?P<end>(?:\s+import\s+(?P<details>[*]|(?:[a-zA-Z0-9_.,\s]+)))(?:\s*))$' )
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

objects = [
           ( 'Version',
             re.compile('([a-zA-Z_][a-zA-Z0-9_.]+[.])?(Version[.])([a-zA-Z_][a-zA-Z0-9_]*)'),
            ('pymel',
             'pymel.version',
             'pymel.internal',
             'pymel.internal.version' ),
            'versions',
            { 'current' : 'current()',
             'v85sp1' : 'v85_SP1',
             'v2008sp1' : 'v2008_SP1',
             'v2008ext2' : 'v2008_EXT2',
             'v2009ext1' : 'v2009_EXT1',
             'v2009sp1a' : 'v2009_SP1A'
            }
            )
           ]

PREFIX = 1
OBJECT = 2
SUFFIX = 3

class LogError(ValueError):pass

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
            raise LogError, "could not find an existing %s. please pass the path to this file, which was generated during upgrade" % LOGNAME
    return os.path.realpath(logfile)

def upgradeFile(filepath, test=True):
    """
    upgrade a single file
    """
    try:
        f = open(filepath)
        lines = f.readlines()
        f.close()
    except Exception, e:
        print str(e)
        return False, False

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
            #start, pymel_module, end, details = m.groups()
            d= m.groupdict()
            start = d['start']
            pymel_module = d['pymel']
            end = d['end']
            details = d['details']

            if pymel_module == 'pymel.all':
                print "skipping. already uses 'pymel.all':",  filepath
                return False, True

            uses_pymel = True

            if pymel_module == 'pymel':
                # import pymel, foo  -->  import pymel.all as pymel, foo
                # import pymel as pm, foo  -->  import pymel.all as pm, foo
                # from pymel import foo  -->  from pymel.all import foo
                as_name = ' as pymel' if mode == 'import' and not details else ''
                lines[i] = start + 'pymel.all' + as_name + end
                modified = True

            if details:
                details = details.strip()

            if mode == 'import':
                if details:
                    pymel_namespaces[pymel_module].add(details)     # pymel.version -> version
                    # import pymel.internal as internal
                    # 'internal' -> 'pymel.internal'
                    rev_pymel_namespaces[details].add(pymel_module)
                else:
                    # 'import pymel'
                    pymel_namespaces[pymel_module].add(pymel_module)

                    # import pymel.internal
                    # 'pymel.internal' -> 'pymel.internal'
                    rev_pymel_namespaces[pymel_module].add(pymel_module)

            elif mode == 'from':
                details = '' if details == '*' else details
                for detail in details.split(','):
                    if detail:
                        module = pymel_module + '.' + detail
                    else:
                        module = pymel_module
                    pymel_namespaces[pymel_module].add(detail)

                    # from pymel import internal
                    # 'internal' -> 'pymel.internal'

                    # from pymel import *
                    # '' -> 'pymel'
                    rev_pymel_namespaces[detail].add(module)

        if uses_pymel:
            for obj, reg, obj_namespaces, replace, attr_remap in objects:
                parts = reg.split(line)
                if len(parts) > 1:
                    #print parts
                    for j in range(0, len(parts)-1, 4):
                        try:
                            ns = parts[j+PREFIX]
                        except IndexError, err:
                            pass
                        else:
                            ns = ns if ns else ''
                            #print '\t', `ns`
                            parts[j+PREFIX] = ns
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
                                                    parts[j+PREFIX] = replace + '.'
                                                else:
                                                    parts[j+PREFIX] = pmns + '.' + replace + '.'
                                                parts[j+OBJECT] = None

                                            attr = parts[j+SUFFIX]
                                            parts[j+SUFFIX] = attr_remap.get(attr, attr)
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
                f.close()
            except (IOError, OSError), err:
                print "error writing temporary file: %s: %s" % ( tmpfile, err)
                success = False

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

def upgrade(logdir=None, test=True, excludeFolderRegex=None, excludeFileRegex=None, verbose=False, force=False):
    """
    search PYTHONPATH (aka. sys.path) and MAYA_SCRIPT_PATH for python files using
    pymel that should be upgraded

    Keywords
    --------

    :param logdir:
        directory to which to write the log of modified files
    :param test:
        when run in test mode (default) no files are changed
    :param excludeFolderRegex:
        a regex string which should match against a directory's basename, without parent path
    :param excludeFileRegex:
        a regex string which should match against a file's basename, without parent path or extension
    :param verbose:
        print more information during conversion
    :param force:
        by default, `upgrade` will skip files which already have already been processed,
        as determined by the existence of a backup file with a .pmbak extension. setting
        force to True will ignore this precaution
    """

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

    completed = []
    try:
        for path in sys.path + os.environ['MAYA_SCRIPT_PATH'].split(os.pathsep):
        #for path in ['/Volumes/luma/_globalSoft/dev/chad/python/pymel']:
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith('.py') and not f.startswith('.'):
                        if not excludeFileRegex or not re.match( excludeFileRegex, f[:-3] ):
                            fpath = os.path.realpath(os.path.join(root,f))
                            if fpath not in completed:
                                if os.path.exists(fpath+BACKUPEXT) and not force:
                                    print "file has already been converted. skipping: %s  (use force=True to force conversion)" % fpath
                                    if not test:
                                        # keep as part of the log so that undo will work
                                        log.write( fpath + '\n' )
                                else:
                                    modified, stat = upgradeFile( fpath, test )
                                    if modified and stat:
                                        print 'needs upgrading:' if test else 'upgraded:', fpath
                                        if not test:
                                            log.write( fpath + '\n' )
                                completed.append(fpath)
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

    if test:
        print "test complete"
        print "to upgrade the listed files run:\nupgrade(test=False)"
    else:
        print "upgrade complete. the original files have been renamed with a %s extension\n" % BACKUPEXT
        print "to remove the backed-up original files run:\ncleanup(%r)\n" % logfile
        print "to restore the original files run:\nundo(%r)" % logfile

def undoFile(filepath):
    """
    undo a single file
    """
    backup = filepath + BACKUPEXT
    if os.path.isfile(backup):
        try:
            os.rename(backup, filepath )
            print "restored", filepath
        except (IOError, OSError), err:
            print "error restoring file %s.pmbak to %s: %s" % ( filepath, filepath, err)
            return False
    else:
        print "error restoring %s: backup file does not exist: %s. skipping" % ( filepath, backup)
    return True

def _findbackups():
    undofiles = []
    for path in sys.path + os.environ['MAYA_SCRIPT_PATH'].split(os.pathsep):
        for root, dirs, files in os.walk(path):
            #print root
            for f in files:
                if f.endswith('.py' + BACKUPEXT) and not f.startswith('.'):
                    fpath = os.path.realpath(os.path.join(root,f.rstrip(BACKUPEXT)))
                    #print "adding", fpath
                    undofiles.append(fpath)
            i = 0
            tmpdirs = dirs[:]
            for dir in tmpdirs:
                #print '\t', `dir`
                if dir.startswith('.') or dir == 'pymel' \
                        or not os.path.isfile(os.path.join(root, dir, '__init__.py')):
                    del dirs[i]
                else:
                    i += 1
    return undofiles

def _getbackups(logfile, force):
    try:
        log = open(_getLogfile(logfile), 'r' )
    except LogError, e:
        if force:
            undofiles = _findbackups()
        else:
            raise LogError, str(e) + '.\nif you lost your logfile, set force=True to search sys.path for *.pmbak files to restore instead.'
    else:
        undofiles = [ x.rstrip() for x in log.readlines() if x]
        log.close()
    return undofiles

def undo(logfile=None, force=False):
    """
    undo converted files to their original state and remove backups

    :param logfile:
        the logfile containing the list of files to restore.  if None, the logfile
        will be determined in this order:
            1. last used logfile (module must have remained loaded since running upgrade)
            2. MAYA_APP_DIR
            3. current working directory
    :param force:
        if you've lost the original logfile, setting force to True will cause the function
        to recurse sys.path looking for backup files to restore instead of using the log.
        if your sys.path is setup exactly as it was during upgrade, all files should
        be restored, but without the log it is impossible to be certain.
    """
    undofiles = _getbackups(logfile, force)

    try:
        for file in undofiles:
            undoFile(file)
        print 'done'
    except Exception, err:
        import traceback
        traceback.print_exc()



def cleanup(logfile=None, force=False):
    """
    remove backed-up files.  run this when you are certain that the upgrade went
    smoothly and you no longer need the original backups.

    :param logfile:
    the logfile containing the list of files to restore.  if None, the logfile
    will be determined in this order:
        1. last used logfile (module must have remained loaded since running upgrade)
        2. MAYA_APP_DIR
        3. current working directory
    :param force:
        if you've lost the original logfile, setting force to True will cause the function
        to recurse sys.path looking for backup files to cleanup instead of using the log.
        if your sys.path is setup exactly as it was during upgrade, all files should
        be restored, but without the log it is impossible to be certain.
    """
    undofiles = _getbackups(logfile, force)

    try:
        for file in undofiles:
            bkup = file + BACKUPEXT
            try:
                print "removing", bkup
                os.remove(bkup)
            except (IOError, OSError), err:
                print "error removing file %s: %s" % ( bkup, err)
        print 'done'
    except Exception, err:
        import traceback
        traceback.print_exc()



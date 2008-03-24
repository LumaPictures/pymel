"""File Sequence Management

FileSequence allows the manipulation of a sequence of files as an entity.  A sequence of files is a set of files related by a common prefix and numbers in the name.

Example:

/tmp/untitled1_001.iff
/tmp/untitled1_002.iff
/tmp/untitled1_004.iff

Could be used as:

fs = getSequences('/tmp')[0]
fs.getMissing()
>> 3
fs.copy('/home/me/files')

"""

import pymel.util.path
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
import re
from functools import wraps
import sys

def getSequences(dir):
    """ returns an iterable of all the fileSequences found in directory dir """
    files = path.path(dir).files()
    return _getSequences( files )

def _iterwrap(f):
    @wraps(f)
    def wrapper(self, *args,**kwds):
        return (f(fl, *args,**kwds) for fl in self)
    return wrapper
def _fileIndex(file):
    ns = re.findall(r'\d+', file)
    return int(ns[-1])
    

class FileSequence( list ):
    def __init__( self, files ):
        try:
            self.link = _iterwrap(path.path.link)
            self.symlink = _iterwrap(path.path.symlink)
            self.readlink = _iterwrap(path.path.readlink)
            self.readlinkabs = _iterwrap(path.path.readlinkabs)
            self.statvfs = _iterwrap(path.path.statvfs)
            self.pathconf = _iterwrap(path.path.pathconf)
            self.chown = _iterwrap(path.path.chown)
        except: pass
        self.extend(files)

    def copy(self, target_folder):
        """ copy this sequence to the target folder
        returns a FileSequence of the copied group
        """
        for f in self:
            f.copy( target_folder )
        return FileSequence( [ path.path(target_folder) / f.basename() for f in self ] )

    def move(self, target_folder):
        """ move this sequence to the target folder,
            returns a FileSequence of the moved files
        """
        for f in self:
            f.move( target_folder )
        return FileSequence( [ path.path(target_folder) / f.basename() for f in self ] )

    def asSet(self):
        """ return sequence as a set of indexes """
        return set([ _fileIndex(f) for f in self])

    def missing(self):
        """ return a list of path.path of files which seem to be
            missing from this sequence """
        have = self.asSet()
        fullSet = set( range( 1, max(have) + 1 ) )
        return list(fullSet - have)

    def emptyFiles(self):
        """ return the files which are 0 bytes """
        return [f for f in self if not f.exists() or f.getsize() == 0]
    
    isabs = _iterwrap(path.path.isabs)
    abspath = _iterwrap(path.path.abspath)
    normcase = _iterwrap(path.path.normcase)
    normpath = _iterwrap(path.path.normpath)
    realpath = _iterwrap(path.path.realpath)
    expanduser = _iterwrap(path.path.expanduser)
    expandvars = _iterwrap(path.path.expandvars)
    dirname = _iterwrap(path.path.dirname)
    basename = _iterwrap(path.path.basename)
    expand = _iterwrap(path.path.expand)
    splitpath = _iterwrap(path.path.splitpath)
    splitdrive = _iterwrap(path.path.splitdrive)
    splitext = _iterwrap(path.path.splitext)
    stripext = _iterwrap(path.path.stripext)
    splitunc = _iterwrap(path.path.splitunc)
    joinpath = _iterwrap(path.path.joinpath)
    splitall = _iterwrap(path.path.splitall)
    relpath = _iterwrap(path.path.relpath)
    relpathto = _iterwrap(path.path.relpathto)
    listdir = _iterwrap(path.path.listdir)
    dirs = _iterwrap(path.path.dirs)
    files = _iterwrap(path.path.files)
    walk = _iterwrap(path.path.walk)
    walkdirs = _iterwrap(path.path.walkdirs)
    walkfiles = _iterwrap(path.path.walkfiles)
    fnmatch = _iterwrap(path.path.fnmatch)
    glob = _iterwrap(path.path.glob)
    open = _iterwrap(path.path.open)
    bytes = _iterwrap(path.path.bytes)
    write_bytes = _iterwrap(path.path.bytes)
    text = _iterwrap(path.path.text)
    write_text = _iterwrap(path.path.write_text)
    lines = _iterwrap(path.path.lines)
    write_lines = _iterwrap(path.path.write_lines)
    read_md5 = _iterwrap(path.path.read_md5)
    exists = _iterwrap(path.path.exists)
    isdir = _iterwrap(path.path.isdir)
    isfile = _iterwrap(path.path.isfile)
    islink = _iterwrap(path.path.islink)
    ismount = _iterwrap(path.path.ismount)
    getatime = _iterwrap(path.path.getatime)
    getmtime = _iterwrap(path.path.getmtime)
    getctime = _iterwrap(path.path.getctime)
    getsize = _iterwrap(path.path.getsize)
    access = _iterwrap(path.path.access)
    stat = _iterwrap(path.path.stat)
    lstat = _iterwrap(path.path.lstat)
    get_owner = _iterwrap(path.path.get_owner)
    utime = _iterwrap(path.path.utime)
    chmod = _iterwrap(path.path.chmod)
    rename = _iterwrap(path.path.rename)
    renames = _iterwrap(path.path.renames)
    mkdir = _iterwrap(path.path.mkdir)
    makedirs = _iterwrap(path.path.makedirs)
    rmdir = _iterwrap(path.path.rmdir)
    removedirs = _iterwrap(path.path.removedirs)
    touch = _iterwrap(path.path.touch)
    remove = _iterwrap(path.path.remove)
    unlink = _iterwrap(path.path.unlink)
#    copyfile = _iterwrap(path.path.copyfile)
#    copymode = _iterwrap(path.path.copymode)
#    copystat = _iterwrap(path.path.copystat)
#    copy = _iterwrap(path.path.copy)
#    copy2 = _iterwrap(path.path.copy2)
#    copytree = _iterwrap(path.path.copytree)
#    move = _iterwrap(path.path.move)
    rmtree = _iterwrap(path.path.rmtree)


def _getSequences( filelist ):
    def try_int(s):
        try: return int(s)
        except: return s
    # files are partitioned by prefix before last number in name,
    # sorted secondly by last number in name
    partition = defaultdict(list)
    for s in sorted(filelist , key=path.path.basename):
        ns = re.findall(r'\d+', s)
        if len(ns):
            ix = ns[-1]
            prefix = s[0: s.rfind(ix)]
            partition[prefix].append(s)
    return [FileSequence(l) for l in partition.values()]


import unittest

class TestFileSequence(unittest.TestCase):
    def testGetSequences(self):
        testFiles = [ 'untitled2_003.blah','tst1.002.iff', 'tst1.001.iff', 'tst1.004.iff',
                      'tst3.001.iff','tst3.003.iff',
                      'untitled2_001.blah', 'untitled2_002.blah']
        
        partition = _getSequences( [path.path(f) for f in testFiles] )
        self.assertEqual( 3, len(partition) )
        
        
if __name__ == '__main__':
    unittest.main()

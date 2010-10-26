"""
Commonly used utilities
"""

import os, re, sys, platform, pkgutil
from re import escape
from path import path
#-----------------------------------------------
#  Pymel Internals
#-----------------------------------------------


def capitalize(s):
    """
    Python's string 'capitalize' method is NOT equiv. to mel's capitalize, which preserves
    capital letters.

        >>> capitalize( 'fooBAR' )
        'FooBAR'
        >>> 'fooBAR'.capitalize()
        'Foobar'

    :rtype: string
    """
    return s[0].upper() + s[1:]

def uncapitalize(s, preserveAcronymns=False):
    """preserveAcronymns enabled ensures that 'NTSC' does not become 'nTSC'

    :rtype: string

    """
    try:
        if preserveAcronymns and s[0:2].isupper():
            return s
    except IndexError: pass

    return s[0].lower() + s[1:]

def unescape( s ):
    """
    :rtype: string
    """
    chars = [ r'"', r"'" ]
    for char in chars:
        tokens = re.split( r'(\\*)' + char,  s )
        for i in range(1,len(tokens),2 ):
            if tokens[i]:
                tokens[i] = tokens[i][:-1]+'"'
        s = ''.join(tokens)
    return s

def cacheProperty(getter, attr_name, fdel=None, doc=None):
    """a property type for getattr functions that only need to be called once per instance.
        future calls to getattr for this property will return the previous non-null value.
        attr_name is the name of an attribute in which to store the cached values"""
    def fget(obj):
        val = None

        if hasattr(obj,attr_name):
            val = getattr(obj, attr_name)
            #print "cacheProperty: retrieving cache: %s.%s = %s" % (obj, attr_name, val)

        if val is None:
            #print "cacheProperty: running getter: %s.%s" %  (obj, attr_name)
            val = getter(obj)
            #print "cacheProperty: caching: %s.%s = %s" % (obj, attr_name, val)
            setattr(obj, attr_name, val )
        return val

    def fset(obj, val):
        #print "cacheProperty: setting attr %s.%s=%s" % (obj, attr_name, val)
        setattr(obj, attr_name, val)

    return property( fget, fset, fdel, doc)

def timer( command='pass', number=10, setup='import pymel' ):
    import timeit
    t = timeit.Timer(command, setup)
    time = t.timeit(number=number)
    print "command took %.2f sec to execute" % time
    return time

def toZip( directory, zipFile ):
    """Sample for storing directory to a ZipFile"""
    import zipfile

    zipFile = path(zipFile)
    if zipFile.exists(): zipFile.remove()

    z = zipfile.ZipFile(
        zipFile, 'w', compression=zipfile.ZIP_DEFLATED
    )
    if not directory.endswith(os.sep):
        directory += os.sep

    directory = path(directory)

    for subdir in directory.dirs('[a-z]*') + [directory]:
        print "adding ", subdir
        for fname in subdir.files('[a-z]*'):
            archiveName = fname.replace( directory, '' )
            z.write( fname, archiveName, zipfile.ZIP_DEFLATED )
    z.close()
    return zipFile

def interpreterBits():
    """
    Returns the number of bits of the architecture the interpreter was compiled on
    (ie, 32 or 64).

    :rtype: `int`
    """
    # NOTE: platform.architecture()[0] returns '64bit' on OSX 10.6 (Snow Leopard)
    # even when Maya is running in 32-bit mode. The struct technique
    # is more reliable.
    return struct.calcsize("P") * 8    
    return int(re.match(r"([0-9]+)(bit)?", platform.architecture()[0]).group(1))

def subpackages(packagemod):
    """
    Given a module object, returns an iterator which yields a tuple (modulename, moduleobject, ispkg)
    for the given module and all it's submodules/subpackages.
    """
    modpkgs = []
    modpkgs_names = set()
    if hasattr(packagemod, '__path__'):
        yield packagemod.__name__, packagemod, True
        for importer, modname, ispkg in pkgutil.walk_packages(packagemod.__path__, packagemod.__name__+'.'):
            if modname not in sys.modules:
                try:
                    mod = importer.find_module(modname).load_module(modname)
                except Exception, e:
                    print "error importing %s: %s" %  ( modname, e)
            else:
                mod = sys.modules[modname]
            yield modname, mod, ispkg
    else:
        yield packagemod.__name__, packagemod, False

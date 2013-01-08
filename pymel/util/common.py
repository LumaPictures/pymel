"""
Commonly used utilities
"""

import os
import re
import sys
import platform
import pkgutil
import inspect
from re import escape
from path import path
#-----------------------------------------------
#  Pymel Internals
#-----------------------------------------------

#===============================================================================
# Strings
#===============================================================================

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

#===============================================================================
# Deprecated types
#===============================================================================

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

#===============================================================================
# System
#===============================================================================

def timer( command='pass', number=10, setup='import pymel' ):
    import timeit
    t = timeit.Timer(command, setup)
    time = t.timeit(number=number)
    print "command took %.2f sec to execute" % time
    return time

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

#===============================================================================
# Filesystem
#===============================================================================

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

#===============================================================================
# inspection
#===============================================================================

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


def isClassRunningFrame(cls, frameRecord, methodFilter=None):
    '''Whether the given frameRecord is running code from a method in the given class

    Make sure to delete the frameRecord object after calling this (or else you
    create cyclical references - see docs for the inspect module)

    This is not foolproof - for instance, if the name of a method has been
    modified, it may not work - but should work in most cases
    '''
    frameCode = frameRecord[0].f_code
    del frameRecord

    for methodName, methodObj in inspect.getmembers(cls, inspect.ismethod):
        if methodFilter is not None:
            # think it's possible these two names may be different... for instance,
            # if you were to do:
            # class MyClass(object):
            #     def func1(self): pass
            #     func2 = func1
            passed = False
            for nameToCheck in methodName, methodObj.__name__:
                if isinstance(methodFilter, re._pattern_type):
                    passed = bool(methodFilter.search(nameToCheck))
                else:
                    passed = (nameToCheck == methodFilter)
                if passed:
                    break
            if not passed:
                continue
        if methodObj.im_func.func_code == frameCode:
            return True
    return False


def isClassRunningStack(cls, stack=None, methodFilter=None):
    '''Whether the stack is running from "inside" a method on the given class

    Parameters
    ----------
    cls : class object
        The class that we wish to check to see if we're inside one of it's
        methods
    stack : list of frame-record objects, or None
        a list of frame-record objects representing the execution context to
        check; if not given, uses the current execution stack; if passing in an
        explicit stack, make sure to delete it after calling this (see docs for
        the inspect module)
    methodFilter : str or re._pattern_type
        if you only wish to return true if the stack is running inside a specifc
        function, you may set this to the name of the function; or, if you want
        to a apply a a filter by name, pass a compiled regular expression that
        matches method names
    '''
    if stack is None:
        stack = inspect.stack()
    try:
        for frameRecord in stack:
            try:
                if isClassRunningFrame(cls, frameRecord,
                                       methodFilter=methodFilter):
                    return True
            finally:
                del frameRecord
    finally:
        del stack
    return False

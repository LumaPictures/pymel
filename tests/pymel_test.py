#!/usr/bin/env mayapy

#nosetests --with-doctest -v pymel --exclude '(windows)|(tools)|(arrays)|(example1)'

#import doctest

import sys, platform, os, shutil, time, inspect, tempfile, doctest, re

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
    print "To run pymel's tests you must have nose installed"
    raise e

# Get the 'new' version of unittest
if sys.version_info >= (2, 7, 0):
    import unittest
else:
    import unittest2 as unittest

import argparse

def getParser():
    testsDir = os.path.dirname(os.path.abspath(sys.argv[0]))
    pymelRoot = os.path.dirname( testsDir )

    parser = argparse.ArgumentParser(description='Run the pymel tests')
    parser.add_argument('extra_args', nargs='*', help='args to pass to nose or unit/unit2')
    parser.add_argument('--app-dir', help='''make the tests use the given dir as
        the MAYA_APP_DIR (ie, the base maya settings folder)''')
    #parser.add_argument('--test', help='''specific TestCase or test function to
        #run; if given, will be run using the "new" unittest"''')
    parser.add_argument('--tests-dir', help='''The directory that contains the test modules''',
        default=testsDir)
    parser.add_argument('--pymel-root', help='''The directory that contains the test modules''',
        default=pymelRoot)
    return parser

_PYTHON_DOT_NAME_RE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(\.[A-Za-z_][A-Za-z_0-9]*)+')

def isPythonDottedName(name):
    return bool(_PYTHON_DOT_NAME_RE.match(name))

def moduleObjNameSplit(moduleName):
    '''Returns the name split into the module part and the object name part
    '''
    import imp
    currentPath = None
    split = moduleName.split('.')
    moduleParts = []
    for name in split:
        try:
            currentPath = [imp.find_module(name, currentPath)[1]]
        except ImportError:
            break
        moduleParts.append(name)
    return '.'.join(moduleParts), '.'.join(split[len(moduleParts):])

def nose_test(argv, module=None, pymelDir=None):
    """
    Run pymel unittests / doctests
    """
    arg0 = argv[0]
    extraArgs = argv[1:]

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
                    ^testPassContribution$
                    ^test_main$
                    '''.split()

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

    with UnittestDescriptionDisabler():
        with DocTestPatcher():
            print "running nose:", noseKwArgs
            nose.main( **noseKwArgs)

def unit2_test(argv, **kwargs):
    # insert the verbose flag
    argv[1:1] = ['--verbose']

    kwargs['module'] = None
    kwargs['argv'] = argv

    if sys.version_info < (2, 7, 0):
        # if we try to specify a specific method, unittest2 checks to see if it
        # is an unbound method on a unittest2.TestCase; if it is on a
        # unittest.TestCase, it will not work; therefore, install unittest2 as
        # unittest
        sys.modules['unittest'] = sys.modules['unittest2']

    print "running unittest:", kwargs
    with UnittestDescriptionDisabler():
        unittest.main(**kwargs)


class UnittestDescriptionDisabler(object):
    """Disables printing of the test "descriptions" in the unittest results

    The description is the first line of the docstring - but it makes it harder
    to parse results, or quickly identify the failing test, so we disable
    printing them - ie, we want:
    """

    # initally, tried to set the default for TextTestRunner(descriptions=False)
    # While this worked for unittest, for nose, it disabled TOO much - ie,
    # doctests, generators, etc

    # now just making it so that _testMethodDoc is always None...
    def __enter__(self):
        from unittest import TestCase
        old_init = TestCase.__dict__['__init__']
        self._old_init = old_init

        def newInit(self, *args, **kwargs):
            result = old_init(self, *args, **kwargs)
            self._testMethodDoc = None
            return result

        TestCase.__init__ = newInit

    def __exit__(self, exc_type, exc_val, exc_tb):
        from unittest import TestCase
        TestCase.__init__ = self._old_init


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

def main(argv):
    parser = getParser()
    parsed = parser.parse_args(argv[1:])

    if parsed.app_dir:
        if not os.path.exists(parsed.app_dir):
            os.makedirs(parsed.app_dir)
        os.environ['MAYA_APP_DIR'] = parsed.app_dir

    testsDir = parsed.tests_dir
    pymelRoot = parsed.pymel_root

    pypath = os.environ.get('PYTHONPATH', '').split(os.pathsep)
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

    oldPath = os.getcwd()
    # make sure our cwd is the pymel project working directory
    os.chdir( pymelRoot )
    try:
        # Try to guess whether we were given an arg which is a TestCase or
        # test method/function, and if so, run new unittest (because it can
        # easily handle specific TestCase/method/function)... else run nose
        # (because it's what the test suite was originally set up to use)
        useNose = True
        if parsed.extra_args:
            name = parsed.extra_args[-1]
            if isPythonDottedName(name):
                modulePart, objPart = moduleObjNameSplit(name)
                if modulePart and objPart:
                    useNose = False

        argv = [argv[0]] + parsed.extra_args
        if useNose:
            nose_test(argv)
        else:
            unit2_test(argv)
    finally:
        os.chdir(oldPath)

if __name__ == '__main__':
    main(sys.argv)

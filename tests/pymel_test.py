#!/usr/bin/env mayapy

#nosetests --with-doctest -v pymel --exclude '(windows)|(tools)|(arrays)|(example1)'

#import doctest

import doctest
import inspect
import os
import pipes
import re
import sys

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

import unittest
import argparse
import inspect

RUNNERS = ('pytest', 'unittest', 'nose')
DEFAULT_RUNNER = 'pytest'

THIS_FILE = os.path.abspath(inspect.getsourcefile(lambda: None))

def getParser():
    testsDir = os.path.dirname(THIS_FILE)
    pymelRoot = os.path.dirname(testsDir)

    parser = argparse.ArgumentParser(description='Run the pymel tests')
    parser.add_argument('--runner', default=DEFAULT_RUNNER, choices=RUNNERS)
    parser.add_argument('--gui', action='store_true', help='''Launch a gui
        sesssion of Maya to run the tests in''')
    parser.add_argument('--gui-stdout', action='store_true', help='''If on,
        then before the tests run, the "standard" stdout and stderr will be 
        restored, so the tests print to the console, NOT the gui script 
        editor''')
    parser.add_argument('--app-dir', help='''make the tests use the given dir as
        the MAYA_APP_DIR (ie, the base maya settings folder)''')
    #parser.add_argument('--test', help='''specific TestCase or test function to
        #run; if given, will be run using the "new" unittest"''')
    parser.add_argument('--tests-dir', help='''The directory that contains 
        the test modules''', default=testsDir)
    parser.add_argument('--pymel-root', help='''The directory that contains 
        the test modules''', default=pymelRoot)
    return parser

_PYTHON_DOT_NAME_RE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(\.[A-Za-z_][A-Za-z_0-9]*)+')

# testPa and testPassContribution are maya commands, not unittests... while
# the test_main functions are functions that are run when a test module is
# "executed" them - running them would effectively run all the tests in that
# module twice
EXCLUDE_TEST_NAMES = tuple('''testPa
    testPassContribution
    test_main'''.split())

EXCLUDE_TEST_MODULES = tuple('''windows
    pymel/all.py
    pymel/tools
    examples/example1.py
    pymel/util/testing.py
    eclipseDebug.py
    pymel/internal/pmcmds.py
    maya
    maintenance
    extras
    docs
    tests/pymel_test.py
    tests/TestPymel.py'''.split())

EXCLUDE_TEST_GUI_MODULES = tuple('''tests/test_uitypes.py
    tests/test_windows.py'''.split())

def rstripstr(orig, tostrip):
    if tostrip and orig.endswith(tostrip):
        return orig[:-len(tostrip)]
    return orig

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

def inGui():
    try:
        import maya.cmds
        return not maya.cmds.about(batch=1)
    except Exception:
        # default inGui to false - if we are in gui, we should be able to query
        # (definitively) that we are, but same may not be true from command line
        return False

def get_exclude_modules():
    exclude_modules = EXCLUDE_TEST_MODULES
    # if we're not in gui mode, disable the gui tests
    if not inGui():
        exclude_modules += EXCLUDE_TEST_GUI_MODULES
    return exclude_modules

def isMayaOutput(stream):
    if inspect.isclass(stream):
        streamCls = stream
    else:
        streamCls = type(stream)
    return streamCls.__name__ == 'Output' and streamCls.__module__ == 'maya'

def nose_test(argv, module=None, pymelDir=None):
    """
    Run pymel unittests / doctests
    """
    import nose

    arg0 = argv[0]
    extraArgs = argv[1:]

    if pymelDir:
        os.chdir(pymelDir)

    noseKwArgs={}
    noseArgv = "dummyArg0 --with-doctest -vv".split()
    if module is None:
        excludes = []
        exclude_modules = get_exclude_modules()
        # we can use regexp with nose, and I'm not sure exactly how the test
        # names will be formatted - examples.example1 or example1? - so just
        # matching against the last module
        exclude_modules = [rstripstr(x.split('/')[-1], '.py')
                           for x in exclude_modules]
        excludes.extend('(?:^|\.){}(?:$|\.)'.format(m) for m in exclude_modules)

        excludes.extend('^{}$'.format(t) for t in EXCLUDE_TEST_NAMES)
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

def pytest_test(argv, **kwargs):
    import pytest
    argv[0] = 'pytest'
    argv[1:1] = ['-vv', '--doctest-modules'] # verbose
    origStdOut = sys.stdout
    wrappedStdout = None
    if inGui():
        # maya's own stdout redirection messes with pytest's... disable it
        argv.insert(1, '--capture=no')

        # also, pytest will try to query if sys.stdout is a tty, but Maya's
        # output redirector has no "isatty" method...
        stdoutType = type(sys.stdout)
        if isMayaOutput(stdoutType) and not hasattr(stdoutType, 'isatty'):
            # maya.Output is a compiled / builtin object, so we can't assign
            # to it's "isatty" or it's __class__ - so use a proxy class..
            from pymel.util.utilitytypes import proxyClass
            _ProxyMayaOutput = proxyClass(stdoutType, '_ProxyMayaOutput',
                                          dataAttrName='_mayaOutput')
            class ProxyMayaOutput(_ProxyMayaOutput):
                def __init__(self, toWrap):
                    self._mayaOutput = toWrap
                def isatty(self):
                    return False
            wrappedStdout = ProxyMayaOutput(sys.stdout)

    exclude_modules = get_exclude_modules()
    argv.extend('--ignore={}'.format(x) for x in exclude_modules)

    # the test excludes are handled by conftest.py, since I couldn't find
    # a way to exclude them from the "command line"
    print " ".join(pipes.quote(x) for x in argv)

    if wrappedStdout is not None:
        sys.stdout = wrappedStdout
    try:
        pytest.main(args=argv[1:])
    finally:
        if wrappedStdout is not None:
            sys.stdout = origStdOut

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
    parsed, extra_args = parser.parse_known_args(argv[1:])

    saved_stdout = None
    saved_stderr = None
    if parsed.gui_stdout:
        if isMayaOutput(sys.stderr):
            print "Redirecting sys.stderr to sys.__stderr__..."
            saved_stderr = sys.stderr
            sys.stderr = sys.__stderr__
        if isMayaOutput(sys.stdout):
            print "Redirecting sys.stdout to sys.__stdout__..."
            saved_stdout = sys.stdout
            sys.stdout = sys.__stdout__
    try:
        testsDir = parsed.tests_dir
        pymelRoot = parsed.pymel_root

        # setup environ vars - need to do this before launch the gui subprocess

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
        # These will make maya surround all "translated" strings with ","... and I
        # believe make it always use the english (or perhaps the raw, before-lookup)
        # value. In any case, it makes the tests more consitent, regardless of
        # language, and some of the doctests (ie, pymel.core.language) require it
        os.environ['MAYA_PSEUDOTRANS_MODE']='5'
        os.environ['MAYA_PSEUDOTRANS_VALUE']=','

        if parsed.app_dir:
            if not os.path.exists(parsed.app_dir):
                os.makedirs(parsed.app_dir)
            os.environ['MAYA_APP_DIR'] = parsed.app_dir

        if parsed.gui:
            import subprocess

            newArgs = list(argv)
            newArgs.remove('--gui')

            # assume that argv[0] is mayapy, and look for maya(.exe) relative to it
            mayaBinDir = os.path.dirname(argv[0])
            mayaBin = os.path.join(mayaBinDir, 'maya')
            if os.name == 'nt':
                mayaBin += '.exe'
            newArgs[0] = mayaBin

            pyCmd = 'import sys; sys.argv = {!r}; execfile({!r})'.format(newArgs,
                                                                         THIS_FILE)
            melCmd = 'python("{}")'.format(pyCmd.replace('\\', '\\\\')
                                           .replace('"', r'\"'))
            mayaArgs = [mayaBin, '-command', melCmd]
            print mayaArgs
            sys.exit(subprocess.call(mayaArgs))

        argv = [argv[0]] + extra_args

        oldPath = os.getcwd()
        # make sure our cwd is the pymel project working directory
        os.chdir( pymelRoot )

        try:
            if parsed.runner == 'nose':
                nose_test(argv)
            elif parsed.runner == 'unittest':
                unit2_test(argv)
            elif parsed.runner == 'pytest':
                pytest_test(argv)
            else:
                raise ValueError("unrecognized runner: {}".format(parsed.runner))
        finally:
            os.chdir(oldPath)
    finally:
        if saved_stdout is not None:
            sys.stdout = saved_stdout
            print "...restored maya gui sys.stdout"
        if saved_stderr is not None:
            sys.stderr = saved_stderr
            print "...restored maya gui sys.stderr"

if __name__ == '__main__':
    main(sys.argv)

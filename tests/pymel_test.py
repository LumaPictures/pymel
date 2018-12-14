#!/usr/bin/env mayapy

import os
import pipes
import re
import sys

import argparse
import inspect

THIS_FILE = os.path.abspath(inspect.getsourcefile(lambda: None))


def getParser():
    testsDir = os.path.dirname(THIS_FILE)
    pymelRoot = os.path.dirname(testsDir)

    parser = argparse.ArgumentParser(description='Run the pymel tests')
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
    parser.add_argument('--pymel-root', help='''The base directory of the pymel
        source repository''', default=pymelRoot)
    parser.add_argument('-W', '--warnings-as-errors', action='store_true',
                        help="Treat DeprecationWarning and FutureWarning as"
                             " errors")
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
    pymel/cache
    pymel/tools
    examples/example1.py
    pymel/util/testing.py
    eclipseDebug.py
    pymel/internal/pmcmds.py
    maya
    maintenance
    extras
    docs
    pymel_modules
    tests/pymel_test.py
    tests/TestPymel.py'''.split())

EXCLUDE_TEST_GUI_MODULES = tuple('''tests/test_uitypes.py
    tests/test_windows.py'''.split())


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


def pytest_test(argv, warnings_as_errors=False):
    import pytest
    import warnings

    argv[0] = 'pytest'
    argv[1:1] = ['-vv', '--doctest-modules']  # verbose

    if warnings_as_errors:
        # TODO: possibly get rid of our own flag entirely, and require
        # pytest >= 3.1?

        # what we do depends on pytest version - pytest >= 3.1 has it's own
        # controls for handling warnings, and trying to handle them ourselves
        # will get overridden by pytest
        pytest_ver = pytest.__version__.split('.')
        pytest_ver = tuple(int(x) if x.isdigit() else x for x in pytest_ver)
        if pytest_ver >= (3, 1):
            argv.extend(['-W', 'error::PendingDeprecationWarning'])
            argv.extend(['-W', 'error::DeprecationWarning'])
            argv.extend(['-W', 'error::FutureWarning'])
        else:
            warnings.simplefilter("error", PendingDeprecationWarning)
            warnings.simplefilter("error", DeprecationWarning)
            warnings.simplefilter("error", FutureWarning)

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
        # value. In any case, it makes the tests more consistent, regardless of
        # language, and some of the doctests (ie, pymel.core.language) require it
        os.environ['MAYA_PSEUDOTRANS_MODE'] = '5'
        os.environ['MAYA_PSEUDOTRANS_VALUE'] = ','

        if parsed.app_dir:
            if not os.path.exists(parsed.app_dir):
                os.makedirs(parsed.app_dir)
            os.environ['MAYA_APP_DIR'] = parsed.app_dir

        if parsed.gui:
            import subprocess

            newArgs = list(argv)
            newArgs.remove('--gui')

            # assume that sys.executable is mayapy, and look for maya(.exe) relative to it
            mayaBinDir = os.path.dirname(sys.executable)
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

        import pymel
        print "using pymel from: %s" % inspect.getsourcefile(pymel)

        try:
            pytest_test(argv, warnings_as_errors=parsed.warnings_as_errors)
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

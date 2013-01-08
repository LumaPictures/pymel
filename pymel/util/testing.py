import sys
import os
import types
import doctest
import modulefinder
import traceback
import inspect
from StringIO import StringIO
from unittest import *

import pymel.util
from warnings import warn

TEST_MAIN_FUNC_NAME = "test_main"
SUITE_FUNC_NAME = "suite"

def doctestFriendly(func):
    """
    Decorator which prepares maya to run doctests.
    """
    def prepForDoctest(*args, **kwargs):
        result = None
        if (sys.displayhook != sys.__displayhook__
            or sys.stdout != sys.__stdout__):
            save_displayhook = sys.displayhook
            # reset doctest.master, so we don't get spammed with
            # *** DocTestRunner.merge: '...' in both testers; summing outcomes.
            # messages...
            try:
                savedMaster = doctest.master
            except AttributeError:
                savedMaster = None

            # Note - for python 2.4 (ie, maya 8.5) compatability, can't use
            # try/except/raise - must separate
            try:
                sys.displayhook = sys.__displayhook__
                doctest.master = None
                try:
                    result = func(*args, **kwargs)
                except:
                    raise
            finally:
                sys.displayhook = save_displayhook
                doctest.master = savedMaster
        else:
            result = func(*args, **kwargs)
        return result
    return prepForDoctest

@doctestFriendly
def doctestobj(*args, **kwargs):
    """
    Wrapper for doctest.run_docstring_examples that works in maya gui.
    """
    return doctest.run_docstring_examples(*args, **kwargs)

@doctestFriendly
def doctestmod(*args, **kwargs):
    """
    Wrapper for doctest.testmod that works in maya gui.
    """
    return doctest.testmod(*args, **kwargs)

#def isDocTestable(path):
#    finder = moduleFinder.ModuleFinder()
#    finder.find_all_submodules(path)

class MayaTestRunner(TextTestRunner):
    def __init__(self, stream=sys.stdout, descriptions=True, verbosity=2):
        super(MayaTestRunner, self).__init__(stream=stream,
                                             descriptions=descriptions,
                                             verbosity=verbosity)

    @doctestFriendly
    def run(self, *args, **kwargs):
        super(MayaTestRunner, self).run(*args, **kwargs)

def addFuncToModule(func, module):
    if not hasattr(module, func.__name__):
        setattr(module, func.__name__, func)

def startsWithDoubleUnderscore(testcase):
    return testcase.__name__.startswith("__")

def setupUnittestModule(moduleName, suiteFuncName = SUITE_FUNC_NAME, testMainName=TEST_MAIN_FUNC_NAME,
                        filterTestCases=startsWithDoubleUnderscore):
    """
    Add basic unittest functions to the given module.

    Will add a 'suite' function that returns a suite object for the module,
    and a 'test_main' function which runs the suite.

    If a filterTestCases function is given, then this is applied to all objects in the module which
    inherit from TestCase, and if it returns true, removes them from the module dictionary,
    so that they are not automatically loaded.

    By default, it will filter all TestCases whose name starts with a double-underscore, ie
    '__AbstractTestCase'

    Will then call 'test_main' if moduleName == '__main__'
    """
    module = sys.modules[moduleName]
    def theSuite():
        return findTestCases(module)
    theSuite.__name__ = suiteFuncName

    def test_main():
        return MayaTestRunner().run(theSuite())
    test_main.__name__ = testMainName

    addFuncToModule(theSuite, module)
    addFuncToModule(test_main, module)

    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, (type, types.ClassType)) and
            issubclass(obj, TestCase) and
            filterTestCases and
            filterTestCases(obj)):
            delattr(module, name)

    if moduleName == '__main__':
        test_main()

# Make this import / initialize pymel!
#class MayaTestRunner(TextTestRunner):
#    '''
#    Test runner for unittests that require maya.
#    '''
#
#    # For now, just calls standard TextTestRunner with different defaults
#    def __init__

class TestCaseExtended(TestCase):
    # Set this to True if you want to create a TestCase that you DON'T
    # want run (ie, an abstract class you wish to derive from, etc)
    DO_NOT_LOAD = False

    #def addTestFunc(self, function):
    def assertNoError(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except:
            self.fail("Exception raised:\n%s" % traceback.format_exc())

    def assertIteration(self, iterable, expectedResults,
                        orderMatters=True,
                        onlyMembershipMatters=False):
        """
        Asserts that the iterable yields the expectedResults.

        'expectedResults' should be a sequence of items, where each item matches
        an item returned while iterating 'iterable'.

        If onlyMembershipMatters is True, then as long as the results of
        iterable are containined within expectedResults, and every member of
        expectedResults is returned by iterable at least once, the test will
        pass. (Ie, onlyMembershipMatters will override orderMatters.)

        If onlyMembershipMatters is False and orderMatters is True, then the
        items in expectedResults should match the order of items returned by the
        iterable.

        If onlyMembershipMatters is False and orderMatters is False, the
        assertion will pass as long as there is a one-to-one correspondence
        between the items of expectedResults and the items returned by
        iterable. Note that in this case, duplicate return values from the
        iterable will still need duplicate results in the expectedResults.

        Examples:

        # orderMatters=True, onlyMembershipMatters=False by default

        #################################################
        ## orderMatters=True, onlyMembershipMatters=False
        #################################################

        # will PASS
        assertIteration( "foo", ['f', 'o', 'o'])

        # will FAIL - last 'o' not present in expectedResults
        assertIteration( "foo", ['f', 'o'])

        # will FAIL - 'x' not present in iterable
        assertIteration( "foo", ['f', 'o', 'o', 'x'])

        # will FAIL - order incorrect
        assertIteration( "foo", ['o', 'f', 'o'])

        #################################################



        #################################################
        ## orderMatters=True, onlyMembershipMatters=True
        #################################################

        # will PASS - if onlyMembershipMatters, duplicate entries are ignored
        assertIteration( "foo", ['f', 'o', 'o'], onlyMemberShipMatters=True)

        #will PASS
        assertIteration( "foo", ['f', 'o'], onlyMemberShipMatters=True)

        #will FAIL - 'o' not present in expectedResults
        assertIteration( "foo", ['f'], onlyMemberShipMatters=True)

        # will FAIL - 'x' not present in iterable
        assertIteration( "foo", ['f', 'o', 'x'], onlyMemberShipMatters=True)

        # will PASS - order irrelevant
        assertIteration( "foo", ['o', 'f', 'o'], onlyMemberShipMatters=True)
        #################################################



        #################################################
        ## orderMatters=False, onlyMembershipMatters=False
        #################################################

        # will PASS
        assertIteration( "foo", ['f', 'o', 'o'], orderMatters=False)

        #will FAIL - second 'o' not in expectedResults
        assertIteration( "foo", ['f', 'o'], orderMatters=False)

        # will FAIL - 'x' not present in iterable
        assertIteration( "foo", ['f', 'o', 'o', 'x'], orderMatters=False))

        # will PASS - order irrelevant
        assertIteration( "foo", ['o', 'f', 'o'], orderMatters=False)
        #################################################
        """

        expectedResults = list(expectedResults)
        if onlyMembershipMatters:
            unmatchedResults = set(expectedResults)
        else:
            unmatchedResults = list(expectedResults)
        for item in iterable:
            notInExpectedResultsFormat = \
                "iterable '%s' contained item '%s', not found in %s '%s'"

            if onlyMembershipMatters:
                self.assertTrue(item in expectedResults,
                                notInExpectedResultsFormat % (iterable, item, "expectedResults", expectedResults))
            else:
                self.assertTrue(item in unmatchedResults,
                                notInExpectedResultsFormat % (iterable, item, "unmatched expectedResults", unmatchedResults))

                # should do above test even if orderMatters, since that way we will get a Fail (as opposed to an Error)
                # if len(unmatchedResults)==0
                if orderMatters:
                    self.assertEqual(item, unmatchedResults[0], "iterable returned '%s' when '%s' was expected" % (item, unmatchedResults[0]))
            if item in unmatchedResults:
                unmatchedResults.remove(item)

        message = "iterable '%s' did not contain expected item(s): %s" % (iterable, [str(x) for x in unmatchedResults])
        self.assertEqual(len(unmatchedResults), 0, message)

    def assertVectorsEqual(self, v1, v2, places=5):
        for p1, p2 in zip(v1, v2):
            try:
                self.assertAlmostEqual(p1, p2, places=places)
            except AssertionError:
                self.fail('%r not equal to %r to %s places' % (v1, v2, places))


# TODO: move to util.math?
def permutations(sequence, length=None):
    """Given a sequence, will return an iterator over the possible permutations.

    If length is 'None', the permutations will default to having the same length
    as the sequence; otherwise, the returned permtuations will have the given length.

    Note that every element in the sequence is considered unique, so that there may be
    'duplicate' permutations if there are duplicate elements in seq, ie:

    perumutations("aa") -> ['a', 'a'] and ['a', 'a']
    """

    if length is None:
        length = len(sequence)
    elif length < 0 or length > len(sequence):
        raise ValueError("Permutation length '%i' invalid for %s" % (length, sequence))

    if length==0: yield []

    else:
        for i in xrange(len(sequence)):
            for subpermutation in permutations(sequence[:i] + sequence[i+1:], length - 1):
                yield [sequence[i]] + subpermutation


def isOneToOne(dict):
    """
    Tests if the given dictionary is one to one (if dict[x]==dict[y], x==y)
    """
    return len(set(dict.itervalues())) == len(dict)

def isEquivalenceRelation(inputs, outputs, dict):
    """
    Tests if the given dictionary defines an equivalence relation from between inputs and outputs.

    Technically, tests if the dict is bijective: ie, one-to-one (if dict[x]==dict[y], x==y) and
    onto (for every y in outputs, exists an x such that dict[x] == y)
    """
    inputs = set(inputs)
    output = set(outputs)
    if len(inputs) == len(outputs) and \
        set(dict.iterkeys()) == inputs and \
        set(dict.itervalues()) == outputs:

        return True
    else:
        return False

class SuiteFromModule(TestSuite):
    def __init__(self, module, testImport=True):
        """
        Set testImport to True to have the suite automatically contain a test case that
        checks if we were able to find any tests in the given module.
        """
        super(SuiteFromModule, self).__init__()
        self._importError = None

        if isinstance(module, basestring):
            self.moduleName = module
            self.module = self._importTestModule()
        elif isinstance(module, types.ModuleType):
            self.moduleName = module.__name__
            self.module = module

        if self._importError is None and self.module:
            try:
                importedSuite = self._importSuite()
                if not importedSuite.countTestCases():
                    self._importError = "Imported suite (from %s.%s) had no test cases" % (self.module.__name__, self.suiteFuncName)
            except:
                self._importError = traceback.format_exc()

        if not self._importError:
            self.addTest(importedSuite)

        if testImport:
            self.addTest(self._makeImportTestCase())

    def _importTestModule(self):
        module = None
        try:
            module = __import__(self.moduleName)

            # if moduleName is 'package.module', __import__ returns package!
            packagePath = self.moduleName.split('.')
            for subModule in packagePath[1:]:
                module = getattr(module, subModule)
        except:
            self._importError = traceback.format_exc()
            module = None
        return module

    def _importSuite(self):
        return TestSuite()

    def _makeImportTestCase(suite_self):
        class TestSuiteImport(TestCaseExtended):
            def runTest(testCase_self):
                testCase_self.assertTrue(suite_self._importError is None, "Failed to create a test suite from module '%s':\n%s" % (suite_self.moduleName, suite_self._importError))
            runTest.__doc__ = """Try to create a %s from module '%s'""" % (suite_self.__class__.__name__, suite_self.moduleName)
        return TestSuiteImport()


class UnittestSuiteFromModule(SuiteFromModule):
    def __init__(self, moduleName, suiteFuncName=SUITE_FUNC_NAME, **kwargs):
        self.suiteFuncName = suiteFuncName
        super(UnittestSuiteFromModule, self).__init__(moduleName, **kwargs)

    def _importSuite(self):
        theSuite = None
        suiteFunc = getattr(self.module, self.suiteFuncName, None)
        if isinstance(suiteFunc, TestSuite):
            theSuite = suiteFunc
        elif callable(suiteFunc):
            theSuite = suiteFunc()

        if not theSuite:
            theSuite = findTestCases(self.module)
        if not theSuite:
            theSuite = TestSuite()
        return theSuite



class DoctestSuiteFromModule(SuiteFromModule):
    def __init__(self, moduleName, packageRecurse=False, alreadyRecursed = None, **kwargs):
        if alreadyRecursed is None:
            alreadyRecursed = []
        self.alreadyRecursed = alreadyRecursed
        self.packageRecurse = packageRecurse
        super(DoctestSuiteFromModule, self).__init__(moduleName, **kwargs)

    def _importSuite(self):
        theSuite = None

        if self.module not in self.alreadyRecursed:
            self.alreadyRecursed.append(self.module)
            try:
                theSuite = doctest.DocTestSuite(self.module)
            except ValueError:
                # will raise a value error if it found no tests...
                theSuite = None

            if self.packageRecurse:
                # if the module is a pacakge, for each directory in it's search path...
                for path in getattr(self.module, '__path__', []):

                    # ...add all submodules!
                    for name in os.listdir(path):
                        newPath = os.path.join(path, name)
                        basename, ext = os.path.splitext(name)
                        if ( (os.path.isfile(newPath) and ext in ('.py', '.pyo', '.pyc') and basename != '__init__')
                             or (os.path.isdir(newPath) and os.path.isfile(os.path.join(newPath, '__init__.py'))) ):
                            newModuleName = self.moduleName + "." + basename

                            newSuite = DoctestSuiteFromModule(newModuleName, testImport=False, packageRecurse=True, alreadyRecursed=self.alreadyRecursed)
                            if newSuite.countTestCases():
                                theSuite.addTest(newSuite)
        if not theSuite:
            theSuite = TestSuite()
        return theSuite

def setCompare(iter1, iter2):
    """
    Compares two groups of objects, returning the sets:
        onlyIn1, inBoth, onlyIn2
    """
    s1 = set(iter1)
    s2 = set(iter2)
    intersect = s1 & s2
    return s1 - intersect, intersect, s2 - intersect

def suite():
    theSuite = TestSuite()
    unittestMods = findUnittestModules()
    for testMod in unittestMods:
        theSuite.addTest(UnittestSuiteFromModule(testMod))
    doctests = DoctestSuiteFromModule('pymel', packageRecurse=True)
    if doctests.countTestCases():
        theSuite.addTest(doctests)
    return theSuite

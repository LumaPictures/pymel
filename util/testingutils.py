import sys
from unittest import *

#def makeModuleSuite(moduleName, classPrefix='Test'):
#    """
#    Will look for classes whose name start with the given classPrefix (default: 'Test'),
#    and return a test suite that runs all tests on all the found classes.
#    """ 
#    mod = sys.modules[moduleName]
#    testClasses  = findTestCases
#    
#    suite = TestSuite()
#    for testClass in testClasses:
#        suite.addTest(makeSuite(testClass))
#    return suite
#
def addFuncToModule(func, module):
    setattr(module, func.__name__, func) 
    
def setupUnittestModule(moduleName):
    """
    Add basic unittest functions to the given module.
     
    Will add a 'suite' function that returns a suite object for the module,
    and a 'test_main' function which runs the suite.
    
    Will then call 'test_main' if moduleName == '__main__'
    """
    module = sys.modules[moduleName]
    def suite():
        return findTestCases(module)
    
    def test_main():
        TextTestRunner(stream=sys.stdout, verbosity=2).run(suite())
    
    addFuncToModule(suite, module)
    addFuncToModule(test_main, module)
    
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
    #def addTestFunc(self, function):
    def assertNoError(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except:
            self.fail()
    
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
                
#class VariableStringElement(object):
#    """
#    Used to contruct a string with variable elements for testing purposes.
#    
#    As an example, if 'Maya 2008 Extension 2 x64, Cut Number 200802242349' is a
#    complete maya version string, the various elements might be 'versionNum',
#    'extension', 'bits', and 'cut'.
#    
#    To make the 'cut' VariableStringElement, we might call the constructor as
#    follows:
#    
#        cut = VariableStringElement([200802242349, '200802242349-whee',
#                                       '200700000000-0000'],
#                                      prefixes=["Cut Number "],
#                                      seperatorPrefixes=[", "])
#    
#    then calling 'for x in cut.iterValues(firstElement=False): print x' would yield:
#    
#        ', Cut Number 200802242349'
#        ', Cut Number 200802242349-whee'
#        ', Cut Number 200700000000-0000'
#        
#    You may also 'nest' VariableStringElement objects, ie:
#    """
#    
#    def __init__(values, prefixes=("",), suffixes=("",),
#                 seperatorPrefixes=(" ",)):
#        """
#        values - a sequence of the possible values for the variable portion of
#            the element
#        prefix - possible values for the string that will be prefixed to the
#            value
#        suffix - possible values for the string that will be appended to the
#            value
#        seperatorPrefix - if this VersionStringElement is NOT the first in the
#            complete maya string, this holds the possible values to be placed
#            before the element, to seperate it from the previous
#            VersionStringElement
#        """ 
#        
#        self.values = values
#        self.prefixes = prefixes
#        self.suffixes = suffixes
#        self.seperatorPrefixes = seperatorPrefixes
#        
#    def iterValues(firstElement=False):
#        """
#        An iterator function which will yield all the possible values for this
#           VersionStringElement.
#
#        If firstElement is True, then the possible values for seperatorPrefixes
#            will not be attached to the front of the returned string; otherwise,
#            they will be.
#        """
#        for value in self.values:
#            for prefix in self.prefixes:
#                for suffix in self.suffixes:
#                    result = prefix + value + suffix
#                    if firstElement: yield result
#                    else:
#                        for seperator in self.seperatorPrefixes:
#                            yield seperator + result

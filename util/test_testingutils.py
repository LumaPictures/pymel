import unittest, sys
import testingutils

class TestTestCaseExtended(testingutils.TestCaseExtended):
    def addTestFun
    
    #################################################
    ## orderMatters=True, onlyMembershipMatters=False
    #################################################
    def testOrderMatters_standard_SHOULD_PASS(self):
        # will PASS
        self.assertIteration( "foo", ['f', 'o', 'o'], orderMatters=True, onlyMembershipMatters=False)

    def testOnlyMembershipMatters_noDupInResults_SHOULD_PASS(self):
        # will FAIL - last 'o' not present in expectedResults
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o'], orderMatters=True, onlyMembershipMatters=False)

    def testOnlyMembershipMatters_noDupInResults_SHOULD_FAIL(self):
        # will FAIL - last 'o' not present in expectedResults
        self.assertIteration("foo", ['f', 'o'], orderMatters=True, onlyMembershipMatters=False)

    def testOrderMatters_notInExpected_SHOULD_PASS(self):
        # will FAIL - last 'o' not present in expectedResults
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f'], orderMatters=True, onlyMembershipMatters=False)

    def testOrderMatters_notInExpected_SHOULD_FAIL(self):
        # will FAIL - last 'o' not present in expectedResults
        self.assertIteration("foo", ['f'], orderMatters=True, onlyMembershipMatters=False)
    
    def testOrderMatters_notInIterable_SHOULD_PASS(self):
        # will FAIL - 'x' not present in iterable
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'x'], orderMatters=True, onlyMembershipMatters=False)

    def testOrderMatters_notInIterable_SHOULD_FAIL(self):
        # will FAIL - 'x' not present in iterable
        self.assertIteration("foo", ['f', 'o', 'o', 'x'], orderMatters=True, onlyMembershipMatters=False)

    def testOrderMatters_wrongOrder_SHOULD_PASS(self):
        # will FAIL - order incorrect
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'f', 'o'], orderMatters=True, onlyMembershipMatters=False)

    def testOrderMatters_wrongOrder_SHOULD_FAIL(self):
        # will FAIL - order incorrect
        self.assertIteration("foo", ['o', 'f', 'o'], orderMatters=True, onlyMembershipMatters=False)
    #################################################


    #################################################
    ## orderMatters=True, onlyMembershipMatters=True
    #################################################
    def testOnlyMembershipMatters_standard_SHOULD_PASS(self):
        # will PASS - if onlyMembershipMatters, duplicate entries are ignored
        self.assertIteration( "foo", ['f', 'o', 'o'], orderMatters=True, onlyMembershipMatters=True)        

    def testOnlyMembershipMatters_noDupInResults_SHOULD_PASS(self):
        #will PASS
        self.assertIteration( "foo", ['f', 'o'], orderMatters=True, onlyMembershipMatters=True)

        #will FAIL - 'o' not present in expectedResults
        assertIteration( "foo", ['f'], orderMatters=True, onlyMembershipMatters=True)

        # will FAIL - 'x' not present in iterable
        assertIteration( "foo", ['f', 'o', 'x'], orderMatters=True, onlyMembershipMatters=True)

        # will PASS - order irrelevant
        assertIteration( "foo", ['o', 'f', 'o'], orderMatters=True, onlyMembershipMatters=True)        
    #################################################

#
#        
#        #################################################
#        ## orderMatters=False, onlyMembershipMatters=False
#        #################################################
#
#        # will PASS
#        assertIteration( "foo", ['f', 'o', 'o'], orderMatters=False)        
#
#        #will FAIL - second 'o' not in expectedResults
#        assertIteration( "foo", ['f', 'o'], orderMatters=False)
#
#        # will FAIL - 'x' not present in iterable
#        assertIteration( "foo", ['f', 'o', 'o', 'x'], orderMatters=False))
#
#        # will PASS - order irrelevant
#        assertIteration( "foo", ['o', 'f', 'o'], orderMatters=False)
#        #################################################
class TestPermutations(testingutils.TestCaseExtended):
    
    def doPermuteTest(self, sequence, length, expectedResults):
        self.assertIteration(testingutils.permutations(sequence, length), expectedResults, orderMatters=False)
        
    def testEmptyStr(self):
        self.doPermuteTest("", None, [[]])
        
    def testEmptyList(self):
        self.doPermuteTest([], None, [[]])
    
    def testEmptyTuple(self):
        self.doPermuteTest(tuple(), None, [[]])

    def testSingleElementList(self):
        """Test the permutation works on a list of length 1"""
        self.doPermuteTest([1], None, [[1]])
        
    def testTwoElementList(self):
        """Test the permutation works on a list of length 2"""
        self.doPermuteTest([1, 2], None, [[2, 1], [1, 2]])
        
    def testThreeElementList(self):
        """Test the permutation works on a list of length 3"""
        self.doPermuteTest([1, 2, 3], None,
                      [[1, 2, 3], [1, 3, 2],
                       [2, 1, 3], [2, 3, 1],
                       [3, 1, 2], [3, 2, 1]])
        
    def testRepeatedElements(self):
        """Test that repeated elements are handled correctly."""
        self.doPermuteTest("aa", None, [['a','a'],['a','a']])
        
    def testMisc(self):
        """Miscellaneous tests for validity."""
        testObj = object()
        argsAndExpectedResults = \
            (('bar', None,
              [['b', 'a', 'r'], ['b', 'r', 'a'],
               ['a', 'b', 'r'], ['a', 'r', 'b'],
               ['r', 'b', 'a'], ['r', 'a', 'b']]),
             ('bar', 3,
              [['b', 'a', 'r'], ['b', 'r', 'a'],
               ['a', 'b', 'r'], ['a', 'r', 'b'], 
               ['r', 'b', 'a'], ['r', 'a', 'b']]),
             ('bar', 2,
              [['b', 'a'], ['b', 'r'],
               ['a', 'b'], ['a', 'r'],
               ['r', 'b'], ['r', 'a']]),
             ('bar', 1, [['b'], ['a'], ['r']]),
             ('bar', 0, [[]]),
             ('foo', None,
              [['f', 'o', 'o'], ['f', 'o', 'o'],
               ['o', 'f', 'o'], ['o', 'o', 'f'],
               ['o', 'f', 'o'], ['o', 'o', 'f']]),
             (['foo', 1, testObj, 'bar'], None,
              [['foo', 1, testObj, 'bar'], ['foo', 1, 'bar', testObj],
               ['foo', testObj, 1, 'bar'], ['foo', testObj, 'bar', 1],
               ['foo', 'bar', 1, testObj], ['foo', 'bar', testObj, 1],
               [1, 'foo', testObj, 'bar'], [1, 'foo', 'bar', testObj],
               [1, testObj, 'foo', 'bar'], [1, testObj, 'bar', 'foo'],
               [1, 'bar', 'foo', testObj], [1, 'bar', testObj, 'foo'],
               [testObj, 'foo', 1, 'bar'], [testObj, 'foo', 'bar', 1],
               [testObj, 1, 'foo', 'bar'], [testObj, 1, 'bar', 'foo'],
               [testObj, 'bar', 'foo', 1], [testObj, 'bar', 1, 'foo'],
               ['bar', 'foo', 1, testObj], ['bar', 'foo', testObj, 1],
               ['bar', 1, 'foo', testObj], ['bar', 1, testObj, 'foo'],
               ['bar', testObj, 'foo', 1], ['bar', testObj, 1, 'foo']]),
             ((2.6,), 1, [[2.6]]),
             (([], 3.8, 1, {}, 'fun', 'yeeha'), 2,
              [[[], 3.8], [[], 1], [[], {}], [[], 'fun'], [[], 'yeeha'],
               [3.8, []], [3.8, 1], [3.8, {}], [3.8, 'fun'], [3.8, 'yeeha'],
               [1, []], [1, 3.8], [1, {}], [1, 'fun'], [1, 'yeeha'],
               [{}, []], [{}, 3.8], [{}, 1], [{}, 'fun'], [{}, 'yeeha'],
               ['fun', []], ['fun', 3.8], ['fun', 1], ['fun', {}], ['fun', 'yeeha'],
               ['yeeha', []], ['yeeha', 3.8], ['yeeha', 1], ['yeeha', {}], ['yeeha', 'fun']]))
        for seq, length, results in argsAndExpectedResults:
            self.doPermuteTest(seq, length, results)

testCaseExtendedSuite = unittest.TestLoader().loadTestsFromTestCase(TestTestCaseExtended)
permutationsSuite = unittest.TestLoader().loadTestsFromTestCase(TestPermutations)

allSuite = unittest.TestSuite([testCaseExtendedSuite, permutationsSuite])

def main():
    unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(allSuite)
    
if __name__ == '__main__':
    main()


        
        

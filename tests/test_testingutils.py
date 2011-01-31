import sys, unittest
import pymel.util.testing as testingutils

class TestAssertIteration(testingutils.TestCaseExtended):
    #################################################
    ## orderMatters=True, onlyMembershipMatters=False
    #################################################
    def test_defaults_01_exact(self):
        self.assertIteration( "foo", ['f', 'o', 'o'])

    def test_defaults_02_noRepeatedElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o'])

    def test_defaults_03_missingUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'o'])

    def test_defaults_04_missingNonUniqueElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f'])
    
    def test_defaults_05_extraUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'f'])

    def test_defaults_06_extraNonUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'o'])
                
    def test_defaults_07_extraNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'x'])

    def test_defaults_08_nonUniqueElementReplacedWithNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'x'])

    def test_defaults_09_nonUniqueElementReplacedWithUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'f'])
    
    def test_defaults_10_wrongOrder(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'f', 'o'])
        
    def test_defaults_11_noRepeatedElementsWrongOrder(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'f'])



    #################################################
    ## orderMatters=True, onlyMembershipMatters=True
    #################################################
    def test_onlyMembership_01_exact(self):
        self.assertIteration( "foo", ['f', 'o', 'o'], onlyMembershipMatters=True)

    def test_onlyMembership_02_noRepeatedElements(self):
        self.assertIteration("foo", ['f', 'o'], onlyMembershipMatters=True)

    def test_onlyMembership_03_missingUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'o'], onlyMembershipMatters=True)

    def test_onlyMembership_04_missingNonUniqueElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f'], onlyMembershipMatters=True)
    
    def test_onlyMembership_05_extraUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'o', 'f'], onlyMembershipMatters=True)

    def test_onlyMembership_06_extraNonUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'o', 'o'], onlyMembershipMatters=True)
                
    def test_onlyMembership_07_extraNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'x'], onlyMembershipMatters=True)

    def test_onlyMembership_08_nonUniqueElementReplacedWithNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'x'], onlyMembershipMatters=True)

    def test_onlyMembership_09_nonUniqueElementReplacedWithUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'f'], onlyMembershipMatters=True)
    
    def test_onlyMembership_10_wrongOrder(self):
        self.assertIteration("foo", ['o', 'f', 'o'], onlyMembershipMatters=True)
        
    def test_onlyMembership_11_noRepeatedElementsWrongOrder(self):
        self.assertIteration("foo", ['o', 'f'], onlyMembershipMatters=True)



    #################################################
    ## orderMatters=False, onlyMembershipMatters=True
    #################################################
    def test_unorderedOnlyMembership_01_exact(self):
        self.assertIteration( "foo", ['f', 'o', 'o'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_02_noRepeatedElements(self):
        self.assertIteration("foo", ['f', 'o'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_03_missingUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'o'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_04_missingNonUniqueElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f'], orderMatters=False, onlyMembershipMatters=True)
    
    def test_unorderedOnlyMembership_05_extraUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'o', 'f'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_06_extraNonUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'o', 'o'], orderMatters=False, onlyMembershipMatters=True)
                
    def test_unorderedOnlyMembership_07_extraNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'x'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_08_nonUniqueElementReplacedWithNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'x'], orderMatters=False, onlyMembershipMatters=True)

    def test_unorderedOnlyMembership_09_nonUniqueElementReplacedWithUniqueElement(self):
        self.assertIteration("foo", ['f', 'o', 'f'], orderMatters=False, onlyMembershipMatters=True)
    
    def test_unorderedOnlyMembership_10_wrongOrder(self):
        self.assertIteration("foo", ['o', 'f', 'o'], orderMatters=False, onlyMembershipMatters=True)
        
    def test_unorderedOnlyMembership_11_noRepeatedElementsWrongOrder(self):
        self.assertIteration("foo", ['o', 'f'], orderMatters=False, onlyMembershipMatters=True)


    
    #################################################
    ## orderMatters=False, onlyMembershipMatters=False
    #################################################
    def test_unordered_01_exact(self):
        self.assertIteration( "foo", ['f', 'o', 'o'], orderMatters=False)

    def test_unordered_02_noRepeatedElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o'], orderMatters=False)

    def test_unordered_03_missingUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'o'], orderMatters=False)

    def test_unordered_04_missingNonUniqueElements(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f'], orderMatters=False)
    
    def test_unordered_05_extraUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'f'], orderMatters=False)

    def test_unordered_06_extraNonUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'o'], orderMatters=False)
                
    def test_unordered_07_extraNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'o', 'x'], orderMatters=False)

    def test_unordered_08_nonUniqueElementReplacedWithNewElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'x'], orderMatters=False)

    def test_unordered_09_nonUniqueElementReplacedWithUniqueElement(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['f', 'o', 'f'], orderMatters=False)
    
    def test_unordered_10_wrongOrder(self):
        self.assertIteration("foo", ['o', 'f', 'o'], orderMatters=False)
        
    def test_unordered_11_noRepeatedElementsWrongOrder(self):
        self.assertRaises(self.failureException, self.assertIteration, "foo", ['o', 'f'], orderMatters=False)



        
class TestPermutations(testingutils.TestCaseExtended):
    
    def doPermuteTest(self, sequence, length, expectedResults):
        self.assertIteration(testingutils.permutations(sequence, length), expectedResults, orderMatters=False)
        
    def testEmptyStr(self):
        self.doPermuteTest("", None, [[]])
        
    def testEmptyList(self):
        self.doPermuteTest([], None, [[]])
    
    def testEmptyTuple(self):
        self.doPermuteTest(tuple(), None, [[]])

    def test1ElementList(self):
        """Test the permutation works on a list of length 1"""
        self.doPermuteTest([1], None, [[1]])
        
    def test2ElementList(self):
        """Test the permutation works on a list of length 2"""
        self.doPermuteTest([1, 2], None, [[2, 1], [1, 2]])
        
    def test3ElementList(self):
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

testCaseExtendedSuite = unittest.TestLoader().loadTestsFromTestCase(TestAssertIteration)
permutationsSuite = unittest.TestLoader().loadTestsFromTestCase(TestPermutations)

def suite():
    return unittest.TestSuite([testCaseExtendedSuite, permutationsSuite])



def test_main():
    unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite())
    
if __name__ == '__main__':
    test_main()


        
        

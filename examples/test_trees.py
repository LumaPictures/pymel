import sys, os, inspect, unittest
from trees import *

# Test case: several tests that share the same setup (here same Maya scene for testing for instance)
# Warning: unittest runs test in their name alphabetic order, so if a specific order is desire it must
# appear in the name

class testCase_typeTrees(unittest.TestCase):
    def setUp(self):
        self.types = ('dependNode', ('FurAttractors', ('FurCurveAttractors', 'FurDescription', 'FurGlobals'), 'abstractBaseCreate'))
        self.tree = Tree( self.types )
    def test01_parentMethod(self):
        """ Test the parent method on type tree """
        pass     
    def tearDown(self):
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testCase_typeTrees))
    return suite        

if __name__ == '__main__':
    unittest.main()
    
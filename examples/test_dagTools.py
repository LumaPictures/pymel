import sys, os, inspect, unittest
from dagTools import *

# Test case: several tests that share the same setup (here same Maya scene for testing for instance)
# Warning: unittest runs test in their name alphabetic order, so if a specific order is desire it must
# appear in the name

class testCase_typeChecking(unittest.TestCase):

    def setUp(self):
        # define a list of objects to create either as a callable or a maya types
        obj = ['pointLight', 'locator', 'transform', 'mesh', 'camera', 'objectSet', 'lambert', 'multiplyDivide', 'polyCube', spaceLocator, polyCube] #@UndefinedVariable
        # expected results
        self.expected = {}
        self.expected['isDag'] = [True, True, True, True, True, False, False, False, False, True, [True, False]]
        # store the list of created objects
        sl = []
        # store the types for checking
        pt = []
        mt = []
        # Create the objects for testing
        for k in obj :
            c = cPt = cMt = []
            # AMcommands.MayaCmds().has_key(k) no good, confusion between types and commands
            # ie polyCube command and polyCube type
            if callable(k) :
                c = k()
            else :
                c = createNode(k) #@UndefinedVariable
            if not util.isIterable(c) :
                c = [c]
            cPt = map(type, c)
            cMt = map(nodeType, c) #@UndefinedVariable
            sl += c
            pt += cPt
            mt += cMt
        self.objects = sl
        self.pymelTypes = pt
        self.mayaTypes = mt
        
    def test01_isDagOnObjects(self):
        # excepted result
        expect = util.expandListArgs(self.expected['isDag'])
        # tests
        objTest = isDag(self.objects)
        self.assertEqual(objTest, expect)
        
    def test02_isDagOnMayaTypes(self):
        expect = util.expandListArgs(self.expected['isDag'])         
        mayatypeTest = isDag(map(nodeType, self.objects)) #@UndefinedVariable
        self.assertEqual(mayatypeTest, expect)
        
    def test03_isDagOnPymelTypes(self):
        expect = util.expandListArgs(self.expected['isDag'])         
        pymeltypeTest = isDag(map(type, self.objects))
        self.assertEqual(pymeltypeTest, expect)
        
    def test04_isDagOnNames(self):
        expect = util.expandListArgs(self.expected['isDag'])      
        nameTest = isDag(map(str, self.objects))
        self.assertEqual(nameTest, expect)
        
    def test05_isDagOnPymelTypesNames(self):        
        expect = util.expandListArgs(self.expected['isDag']) 
        pymeltypenameTest = isDag(map(lambda x:unicode(type(x).__name__), self.objects))
        self.assertEqual(pymeltypenameTest, expect)
        
    def tearDown(self):
        # cleaning
        delete(self.objects) #@UndefinedVariable
        

class testCase_hierarchyTrees(unittest.TestCase):
    def setUp(self):
        pass
    def test01_asHierarchy(self):
        # check this : self.assertRaises(ValueError, self.ls.asHierarchy, <arguments>)
        pass
    def tearDown(self):
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testCase_typeChecking))
    suite.addTest(unittest.makeSuite(testCase_hierarchyTrees))
    return suite        

if __name__ == '__main__':
    unittest.main()
    
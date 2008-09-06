from pymel.util.testingutils import TestCaseExtended, setupUnittestModule
from .. import utilitytypes

class BasicSingleton(utilitytypes.Singleton): pass

class DictSingleton(utilitytypes.Singleton, dict) : pass

class TestSingleton(TestCaseExtended):
    def setUp(self):
        DictSingleton().clear()
        
    def testReused(self):
        self.assertTrue(BasicSingleton() is BasicSingleton())
    
    def testCanInitialize(self):
        DictSingleton({'A':1})
        self.assertTrue('A' in DictSingleton())
    
    def testReset(self):
        oldInst = DictSingleton({'A':1})
        self.assertTrue(DictSingleton({}) is not oldInst)
        self.assertFalse('A' in DictSingleton())
        
setupUnittestModule(__name__)

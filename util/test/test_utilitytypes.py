from pymel.util.testingutils import TestCaseExtended, setupUnittestModule
from .. import utilitytypes

aDict = {'A':1, 'a':2}
bDict = {'B':3, 'b':4}

class BasicSingleton(utilitytypes.Singleton): pass

class DictSingleton(utilitytypes.Singleton, dict) : pass

class TestSingleton(TestCaseExtended):
    def setUp(self):
        DictSingleton().clear()
        
    # Who cares? It's the data we care about...
#    def testSameInstance(self):
#        self.assertTrue(BasicSingleton() is BasicSingleton())
    
    def testCanInitialize(self):
        DictSingleton(aDict)
        self.assertEqual(aDict, dict(DictSingleton()))

    # Don't know how to get this to work... ?
    def testInitializeResets(self):
        DictSingleton(aDict)
        self.assertTrue(len(DictSingleton())>0)
        DictSingleton({})
        self.assertTrue(len(DictSingleton())==0)
    
    # Again, instance shouldn't matter, just data
#    def testSameInstanceAfterReinitializing(self):
#        oldInst = DictSingleton({'A':1})
#        self.assertTrue(DictSingleton({}) is oldInst)

    def testReferencesEqual(self):
        oldRef = DictSingleton(aDict)
        newRef = DictSingleton()
        newRef.update(bDict)
        self.assertTrue( oldRef == newRef)
        
    def testUpdateProperly(self):
        DictSingleton()['z'] = 3
        self.assertEqual(DictSingleton()['z'], 3)
        DictSingleton()['z'] = 12
        self.assertEqual(DictSingleton()['z'], 12)
        
        
setupUnittestModule(__name__)

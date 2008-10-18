from testingutils import TestCaseExtended, setupUnittestModule
from pymel.util import utilitytypes

aDict = {'A':1, 'a':2}
bDict = {'B':3, 'b':4}

class BasicSingleton(object):
    __metaclass__ = utilitytypes.Singleton

class DictSingleton(dict) :
    __metaclass__ = utilitytypes.Singleton
    


class TestBasicSingleton(TestCaseExtended):
    # Override this attribute in derived classes!
    # Also, should use self.testClass (as
    # opposed to just 'testClass') in derived classes,
    # in case other classes derive from them...
    testClass = BasicSingleton
    
    def setUp(self):
        self.testClass = self.__class__.testClass

    def testSameInstance(self):
        self.assertTrue(self.testClass() is self.testClass())

class __AbstractTestDict(TestBasicSingleton):
        
    def testCanInitialize(self):
        self.testClass(aDict)
        self.assertEqual(aDict, dict(self.testClass()))

    def testReferencesEqual(self):
        oldRef = self.testClass(aDict)
        newRef = self.testClass()
        self.assertTrue( oldRef == newRef)

class TestDictSingleton(__AbstractTestDict):
    testClass = DictSingleton
    def setUp(self):
        super(TestDictSingleton, self).setUp()
        self.testClass().clear()

    def testInitializeResets(self):
        self.testClass(aDict)
        self.assertTrue(len(self.testClass())>0)
        self.testClass({})
        self.assertTrue(len(self.testClass())==0)

    def testSameInstanceAfterReinitializing(self):
        oldInst = self.testClass({'A':1})
        self.assertTrue(self.testClass({}) is oldInst)        

    def testCanUpdate(self):
        self.testClass()['z'] = 3
        self.assertEqual(self.testClass()['z'], 3)
        self.testClass()['z'] = 12
        self.assertEqual(self.testClass()['z'], 12)
        
    def testNoClearOnUpdate(self):
        self.testClass()['a'] = "foobar"
        self.assertEqual(self.testClass()['a'], "foobar")
        self.testClass()['fuzzy'] = "bear"
        self.assertEqual(self.testClass()['a'], "foobar")
                
class TestFrozenDict(__AbstractTestDict):
    # In the case of static classes, need to create a new class
    # on each setup...
    
    def setUp(self):
        self._makeNewFrozenDictClass()
        
    def _makeNewFrozenDictClass(self, initialValue=None):
        class FrozenDict(dict):
            __metaclass__ = utilitytypes.metaStatic
        self.testClass = FrozenDict
            
    def _doInit(self, initialValue=None):
        if initialValue:
            return self.testClass(initialValue)
        else:
            return self.testClass()
        
    def _doAssignation(self, key, value):
        self.testClass()[key] = value

    def testNoReinitialization(self):
        self._doInit(aDict)
        self.assertRaises(TypeError, self._doInit, aDict)

    def testNoErrorIfNoArgs(self):
        self._doInit(aDict)
        self.assertNoError(self._doInit)
        self.assertNoError(self._doInit)
    
    def testNoAssignation(self):
        self.assertRaises(TypeError, self._doAssignation, 'A', 3)
        
    def testHidden(self):
        shouldBeHidden = ('clear', 'update', 'pop', 'popitem', '__setitem__', '__delitem__', 'append', 'extend' )
        for hidden in shouldBeHidden:
            self.assertFalse(hasattr(self.testClass(), hidden))
    
        
setupUnittestModule(__name__)

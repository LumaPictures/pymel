import unittest
from pymel.util.testing import TestCaseExtended, setupUnittestModule, TestCase
from pymel.util import utilitytypes
from pymel.util.enum import Enum

aDict = {'A':1, 'a':2}
bDict = {'B':3, 'b':4}

class BasicSingleton(object):
    __metaclass__ = utilitytypes.Singleton

class DictSingleton(dict) :
    __metaclass__ = utilitytypes.Singleton



class TestBasicSingleton(TestCaseExtended):
    # Override this attribute in derived classes!
    # Also, should use self.theClass (as
    # opposed to just 'theClass') in derived classes,
    # in case other classes derive from them...
    theClass = BasicSingleton

    def testSameInstance(self):
        self.assertTrue(self.theClass() is self.theClass())

class __AbstractTestDict(TestBasicSingleton):

    def testCanInitialize(self):
        self.theClass(aDict)
        self.assertEqual(aDict, dict(self.theClass()))

    def testReferencesEqual(self):
        oldRef = self.theClass(aDict)
        newRef = self.theClass()
        self.assertTrue( oldRef == newRef)

class TestDictSingleton(__AbstractTestDict):
    theClass = DictSingleton
    def setUp(self):
        super(TestDictSingleton, self).setUp()
        self.theClass().clear()

    def testInitializeResets(self):
        self.theClass(aDict)
        self.assertTrue(len(self.theClass())>0)
        self.theClass({})
        self.assertTrue(len(self.theClass())==0)

    def testSameInstanceAfterReinitializing(self):
        oldInst = self.theClass({'A':1})
        self.assertTrue(self.theClass({}) is oldInst)

    def testCanUpdate(self):
        self.theClass()['z'] = 3
        self.assertEqual(self.theClass()['z'], 3)
        self.theClass()['z'] = 12
        self.assertEqual(self.theClass()['z'], 12)

    def testNoClearOnUpdate(self):
        self.theClass()['a'] = "foobar"
        self.assertEqual(self.theClass()['a'], "foobar")
        self.theClass()['fuzzy'] = "bear"
        self.assertEqual(self.theClass()['a'], "foobar")


class TestEnum(unittest.TestCase):
    def testEquality(self):
        enum1 = Enum('enum', {'foo': 1, 'bar':7})
        enum2 = Enum('enum', {'foo': 1, 'bar': 7})
        enum3 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum4 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum5 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'baz'})
        enum6 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'baz'})

        self.assertEqual(enum1, enum2)
        self.assertIsNot(enum1, enum2)
        self.assertEqual(enum1, enum1)
        self.assertNotEqual(enum1, enum3)
        self.assertNotEqual(enum1, enum4)
        self.assertNotEqual(enum1, enum5)
        self.assertNotEqual(enum1, enum6)

        self.assertEqual(enum3, enum4)
        self.assertIsNot(enum3, enum4)
        self.assertNotEqual(enum3, enum1)
        self.assertNotEqual(enum3, enum2)
        self.assertNotEqual(enum3, enum5)
        self.assertNotEqual(enum3, enum6)

        self.assertEqual(enum5, enum6)
        self.assertIsNot(enum5, enum6)
        self.assertNotEqual(enum5, enum1)
        self.assertNotEqual(enum5, enum2)
        self.assertNotEqual(enum5, enum3)
        self.assertNotEqual(enum5, enum4)

    def testHash(self):
        enum1 = Enum('enum', {'foo': 1, 'bar':7})
        enum2 = Enum('enum', {'foo': 1, 'bar': 7})
        enum3 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum4 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum5 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'baz'})
        enum6 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'baz'})

        self.assertEqual(hash(enum1), hash(enum2))
        self.assertIsNot(enum1, enum2)
        self.assertEqual(hash(enum1), hash(enum1))
        self.assertNotEqual(hash(enum1), hash(enum3))
        self.assertNotEqual(hash(enum1), hash(enum4))
        self.assertNotEqual(hash(enum1), hash(enum5))
        self.assertNotEqual(hash(enum1), hash(enum6))

        self.assertEqual(hash(enum3), hash(enum4))
        self.assertIsNot(enum3, enum4)
        self.assertNotEqual(hash(enum3), hash(enum1))
        self.assertNotEqual(hash(enum3), hash(enum2))
        self.assertNotEqual(hash(enum3), hash(enum5))
        self.assertNotEqual(hash(enum3), hash(enum6))

        self.assertEqual(hash(enum5), hash(enum6))
        self.assertIsNot(enum5, enum6)
        self.assertNotEqual(hash(enum5), hash(enum1))
        self.assertNotEqual(hash(enum5), hash(enum2))
        self.assertNotEqual(hash(enum5), hash(enum3))
        self.assertNotEqual(hash(enum5), hash(enum4))

        self.assertEqual(len({enum1, enum2, enum3, enum4, enum5, enum6}), 3)

    def testConstructionMethods(self):
        enum1 = Enum('enum', {'Red': 0, 'Green': 1, 'Blue': 2})
        enum2 = Enum('enum', ('Red', 'Green', 'Blue'))
        enum3 = Enum('enum', [('Green', 1), ('Blue', 2), ('Red', 0)])

        self.assertEqual(enum1, enum2)
        self.assertEqual(enum1, enum3)
        self.assertEqual(enum2, enum3)

    def testConstructionMultiKeys(self):
        enum1 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum2 = Enum('enum', [('foo', 1), ('bar', 7), ('baz', 7)],
                     multiKeys=True)
        enum3 = Enum('enum', [('foo', 1), ('baz', 7), ('bar', 7)],
                     multiKeys=True)
        self.assertEqual(enum1, enum2)
        self.assertEqual(enum1[7], 'bar')
        self.assertEqual(enum2[7], 'bar')
        self.assertNotEqual(enum1, enum3)
        self.assertNotEqual(enum2, enum3)
        self.assertEqual(enum3[7], 'baz')

    def testRepr(self):
        enum1 = Enum('enum', {'foo': 1, 'bar': 7, 'baz': 7},
                     multiKeys=True, defaultKeys={7:'bar'})
        enum2 = Enum('enum', [('foo', 1), ('bar', 7), ('baz', 7)],
                     multiKeys=True)
        enum3 = Enum('enum', [('foo', 1), ('baz', 7), ('bar', 7)],
                     multiKeys=True)
        enum4 = Enum('enum', ['foo', 'bar', 'baz'])

        # test that the reprs give us back the same thing
        enum5 = eval(repr(enum1), {'Enum': Enum})
        self.assertEqual(enum1, enum5)
        self.assertEqual(enum5[7], 'bar')

        enum6 = eval(repr(enum2), {'Enum': Enum})
        self.assertEqual(enum2, enum6)
        self.assertEqual(enum6[7], 'bar')

        enum7 = eval(repr(enum3), {'Enum': Enum})
        self.assertEqual(enum3, enum7)
        self.assertEqual(enum7[7], 'baz')

        enum8 = eval(repr(enum4), {'Enum': Enum})
        self.assertEqual(enum4, enum8)
        self.assertEqual(enum8[2], 'baz')


class TestFrozenDict(__AbstractTestDict):
    # In the case of static classes, need to create a new class
    # on each setup...

    def setUp(self):
        self._makeNewFrozenDictClass()

    def _makeNewFrozenDictClass(self, initialValue=None):
        class FrozenDict(dict):
            __metaclass__ = utilitytypes.metaStatic
        self.theClass = FrozenDict

    def _doInit(self, initialValue=None):
        if initialValue:
            return self.theClass(initialValue)
        else:
            return self.theClass()

    def _doAssignation(self, key, value):
        self.theClass()[key] = value

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
            self.assertFalse(hasattr(self.theClass(), hidden))

class TestEquivalencePairs(TestCaseExtended):
    def testInitPairs(self):
        ep = utilitytypes.EquivalencePairs( ((1,'foo'), (2,'bar')) )
        self.assertEqual(ep[1], 'foo')
        self.assertEqual(ep[2], 'bar')
        self.assertEqual(ep['foo'], 1)
        self.assertEqual(ep['bar'], 2)

    def testInitDict(self):
        ep = utilitytypes.EquivalencePairs( {1:'foo', 2:'bar'} )
        self.assertEqual(ep[1], 'foo')
        self.assertEqual(ep[2], 'bar')
        self.assertEqual(ep['foo'], 1)
        self.assertEqual(ep['bar'], 2)

    def testInitEquivPairs(self):
        otherEp = utilitytypes.EquivalencePairs( {1:'foo', 2:'bar'} )
        ep = utilitytypes.EquivalencePairs(otherEp)
        self.assertEqual(ep[1], 'foo')
        self.assertEqual(ep[2], 'bar')
        self.assertEqual(ep['foo'], 1)
        self.assertEqual(ep['bar'], 2)

    def testOverwritePairs(self):
        ep = utilitytypes.EquivalencePairs({1:'a', 2:'b'})
        self.assertEqual(ep[1], 'a')
        self.assertEqual(ep[2], 'b')
        self.assertEqual(ep['a'], 1)
        self.assertEqual(ep['b'], 2)
        ep[1] = 2
        self.assertRaises(KeyError, self._getIndex, ep, 'a')
        self.assertRaises(KeyError, self._getIndex, ep, 'b')
        self.assertEqual(ep[1], 2)
        self.assertEqual(ep[2], 1)

    def _getIndex(self, indexableObj, index):
        return indexableObj[index]

class TestProxyClass(TestCase):
    class MyClass(object):
        "MyClass's doc string!"
        data = 3.14

        def __init__(self, id):
            self.id = id

        @classmethod
        def clsMeth(cls):
            return cls

        @staticmethod
        def statMeth():
            return 'static'

        def instMeth(self):
            return (self, self.id)

    def test_wrapData(self):
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        self.assertEqual(Wrapped.data, self.MyClass.data)
        self.assertEqual(Wrapped('foo').data, self.MyClass('foo').data)

    def test_classMethod(self):
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        self.assertEqual(Wrapped.clsMeth(), self.MyClass.clsMeth())

    def test_staticMethod(self):
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        self.assertEqual(Wrapped.statMeth(), self.MyClass.statMeth())

    def test_instMethod(self):
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        wrappedResult = Wrapped('bar').instMeth()
        myClassResult = self.MyClass('bar').instMeth()
        self.assertEqual(wrappedResult[0].__class__, myClassResult[0].__class__)
        self.assertEqual(wrappedResult[1], myClassResult[1])

    def test_docString(self):
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        self.assertEqual(Wrapped.__doc__, self.MyClass.__doc__)

    def test_immutable(self):

        Wrapped = utilitytypes.proxyClass(''.__class__, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        self.assertEqual(Wrapped('Fun times were had by all')[3:7],
                         'Fun times were had by all'[3:7])


    def test_unboundMethod(self):
        """
        We should be able to do MyProxyClass.wrappedMethod(myProxyClassInst)
        """
        Wrapped = utilitytypes.proxyClass(self.MyClass, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        wrapInst = Wrapped('bar')
        wrappedResult = Wrapped.instMeth(wrapInst)
        myClassResult = self.MyClass('bar').instMeth()
        self.assertEqual(wrappedResult[0].__class__, myClassResult[0].__class__)
        self.assertEqual(wrappedResult[1], myClassResult[1])

    def test_unboundMethodDescriptor(self):
        """
        Some built-in types have fun things called method descriptors...
        ...they're like methods, but not!
        """
        Wrapped = utilitytypes.proxyClass(''.__class__, 'Wrapped',
                                          dataAttrName='_data', makeDefaultInit=True)
        theString = 'Fun times were had by all!'
        wrapInst = Wrapped(theString)
        self.assertEqual(Wrapped.__len__(wrapInst), len(theString))

setupUnittestModule(__name__)

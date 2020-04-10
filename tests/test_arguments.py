from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import numbers
import unittest

import pymel.util.arguments as arguments

class testCase_mergeCascadingDicts(unittest.TestCase):
    def test_simpleAdd(self):
        orig = {1:'a'}
        arguments.mergeCascadingDicts( {2:'b'}, orig )
        self.assertEqual(orig, {1:'a',2:'b'})

    def test_subAdd(self):
        orig = {1:{'meat':'deinonychus'}}
        arguments.mergeCascadingDicts( {1:{'plants':'stegosaurus'}}, orig )
        self.assertEqual(orig, {1:{'plants':'stegosaurus', 'meat':'deinonychus'}})

    def test_simpleRemove(self):
        orig = {1:'a'}
        arguments.mergeCascadingDicts( {1:arguments.RemovedKey('old')}, orig )
        self.assertEqual(orig, {})

    def test_subRemove(self):
        orig = {1:{'plants':'stegosaurus'}}
        arguments.mergeCascadingDicts( {1:{'plants':arguments.RemovedKey('old')}}, orig )
        self.assertEqual(orig, {1:{}})

    def test_simpleUpdate(self):
        orig = {1:'a'}
        arguments.mergeCascadingDicts( {1:'b'}, orig )
        self.assertEqual(orig, {1:'b'})

    def test_subUpdate(self):
        orig = {1:{'meat':'deinonychus'}}
        arguments.mergeCascadingDicts( {1:{'meat':'trex'}}, orig )
        self.assertEqual(orig, {1:{'meat':'trex'}})

    def test_simpleListReplace(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList}
        arguments.mergeCascadingDicts( {1:{0:'samuel', 1:'jackson'}}, orig )
        self.assertEqual(orig, {1:{0:'samuel', 1:'jackson'}})
        self.assertTrue(origList is not orig[1])

    def test_subListReplace(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:{'a':origList}}
        arguments.mergeCascadingDicts( {1:{'a':{0:'samuel', 1:'jackson'}}}, orig )
        self.assertEqual(orig, {1:{'a':{0:'samuel', 1:'jackson'}}})
        self.assertTrue(origList is not orig[1]['a'])

    def test_simpleListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList}
        arguments.mergeCascadingDicts( {1:{0:'samuel', 1:'jackson'}}, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, {1:['samuel', 'jackson', 'Fer']})
        self.assertTrue(origList is orig[1])

    def test_subListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:{'a':origList}}
        arguments.mergeCascadingDicts( {1:{'a':{0:'samuel', 1:'jackson'}}}, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, {1:{'a':['samuel', 'jackson', 'Fer']}})
        self.assertTrue(origList is orig[1]['a'])

    def test_subListListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:[origList, 'extra']}
        arguments.mergeCascadingDicts( {1:{0:{0:'samuel', 1:'jackson'}}}, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, {1:[['samuel', 'jackson', 'Fer'], 'extra']})
        self.assertTrue(origList is orig[1][0])

    def test_simpleListRemove(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList}
        arguments.mergeCascadingDicts( {1:{0:arguments.RemovedKey('old')}}, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, {1:['mother', 'Fer']})
        self.assertTrue(origList is orig[1])

class testCase_compareCascadingDicts(unittest.TestCase):
    def test_simpleAdd(self):
        orig = {1:'a'}
        new = {1:'a',2:'b'}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set([2]))
        self.assertEqual(diff, {2:'b'})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_subAdd(self):
        orig = {1:{'meat':'deinonychus'}}
        new = {1:{'plants':'stegosaurus', 'meat':'deinonychus'}}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{'plants':'stegosaurus'}})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_simpleRemove(self):
        orig = {1:'a'}
        new = {}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set())
        self.assertEqual(only1, set([1]))
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:arguments.RemovedKey('a')})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_subRemove(self):
        orig = {1:{'plants':'stegosaurus'}}
        new = {1:{}}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{'plants':arguments.RemovedKey('stegosaurus')}})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_simpleUpdate(self):
        orig = {1:'a'}
        new = {1:'b'}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:'b'})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_subUpdate(self):
        orig = {1:{'meat':'deinonychus'}}
        new = {1:{'meat':'trex'}}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{'meat':'trex'}})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, new)

    def test_simpleListReplace(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList, 'foo':'bar'}
        new = {1:{0:'samuel', 1:'jackson'}, 'foo':'bar'}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1, 'foo']))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        print('diff:', diff)
        self.assertEqual(diff, {1:{0:'samuel', 1:'jackson', 2:arguments.RemovedKey('Fer')}})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, {1:{0:'samuel', 1:'jackson', 2:arguments.RemovedKey('Fer')}, 'foo':'bar'})
        self.assertTrue(origList is not orig[1])

    def test_subListReplace(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:{'a':origList}, 'foo':'bar'}
        new = {1:{'a':{0:'samuel', 1:'jackson'}}, 'foo':'bar'}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1, 'foo']))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{'a':{0:'samuel', 1:'jackson', 2:arguments.RemovedKey('Fer')}}})
        arguments.mergeCascadingDicts( diff, orig )
        self.assertEqual(orig, {1:{'a':{0:'samuel', 1:'jackson', 2:arguments.RemovedKey('Fer')}}, 'foo':'bar'})
        self.assertTrue(origList is not orig[1]['a'])

    def test_simpleListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList}
        new = {1:['samuel', 'jackson', 'Fer']}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{0:'samuel', 1:'jackson'}})
        arguments.mergeCascadingDicts( diff, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, new)
        self.assertTrue(origList is orig[1])

    def test_subListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:{'a':origList}}
        new = {1:{'a':['samuel', 'jackson', 'Fer']}}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{'a':{0:'samuel', 1:'jackson'}}})
        arguments.mergeCascadingDicts( diff, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, new)
        self.assertTrue(origList is orig[1]['a'])

    def test_subListListUpdate(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:[origList, 'extra']}
        new = {1:[['samuel', 'jackson', 'Fer'], 'extra']}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{0:{0:'samuel', 1:'jackson'}}})
        arguments.mergeCascadingDicts( diff, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, new)
        self.assertTrue(origList is orig[1][0])

    def test_simpleListRemove(self):
        origList = ['bad', 'mother', 'Fer']
        orig = {1:origList}
        new = {1:['bad', 'mother']}
        both, only1, only2, diff = arguments.compareCascadingDicts(orig, new)
        self.assertEqual(both, set([1]))
        self.assertEqual(only1, set())
        self.assertEqual(only2, set())
        self.assertEqual(diff, {1:{2:arguments.RemovedKey('Fer')}})
        arguments.mergeCascadingDicts( diff, orig,
                                       allowDictToListMerging=True )
        self.assertEqual(orig, new)
        self.assertTrue(origList is orig[1])

class testCase_deepPatch(unittest.TestCase):
    def assertDeepPatch(self, input, predicate, changer, expectedResult,
                        expectedAltered, expectSameObj):
        '''Tests both deepPatch and deepPatchAltered'''
        import copy

        inputCopy = copy.deepcopy(input)

        result, altered = arguments.deepPatchAltered(input, predicate, changer)
        self.assertEqual(result, expectedResult)
        self.assertIs(altered, expectedAltered)

        # could use self.assertTrue, but using assertIs / assertIsNot gives nicer
        # error message
        if expectSameObj:
            self.assertIs(result, input)
        else:
            self.assertIsNot(result, input)

        resultCopy = arguments.deepPatch(inputCopy, predicate, changer)

        self.assertEqual(result, resultCopy)
        return result

    def test_simpleText(self):
        # isstr / addsuffix
        isstr = lambda x: isinstance(x, str)
        addsuffix = lambda x: x + 'suffix'

        foobar = 'foobar'
        self.assertDeepPatch(foobar, isstr, addsuffix,
                             'foobarsuffix', True, False)

        mylist = [3, 7]
        self.assertDeepPatch(mylist, isstr, addsuffix,
                             mylist, False, True)

        # hasfoo, swapfoo
        hasfoo = lambda x: isinstance(x, str) and 'foo' in x
        swapfoo = lambda x: x.replace('foo', 'bar')

        self.assertDeepPatch(foobar, hasfoo, swapfoo,
                             'barbar', True, False)

        seven = 7
        self.assertDeepPatch(seven, hasfoo, swapfoo,
                             seven, False, True)

        class DummyClass(object):
            def __eq__(self, other):
                return type(other) == type(self)

            def __ne__(self, other):
                return not self == other

        dummy = DummyClass()
        self.assertDeepPatch(dummy, hasfoo, swapfoo,
                             dummy, False, True)

        onlybar = 'only bar'
        self.assertDeepPatch(onlybar, hasfoo, swapfoo,
                             onlybar, False, True)

    def test_simpleList(self):
        # isstr / addsuffix
        isstr = lambda x: isinstance(x, str)
        addsuffix = lambda x: x + 'suffix'

        foobar = 'foobar'
        mylist = [foobar]
        self.assertDeepPatch(mylist, isstr, addsuffix,
                             ['foobarsuffix'], True, True)

        mylist = [2, 8]
        self.assertDeepPatch(mylist, isstr, addsuffix,
                             mylist, False, True)

        mylist = [3.7, 'blah']
        self.assertDeepPatch(mylist, isstr, addsuffix,
                             [3.7, 'blahsuffix'], True, True)

        # isnum / add3
        isnum = lambda x: isinstance(x, numbers.Number)
        add3 = lambda x: x + 3

        mylist = []
        self.assertDeepPatch(mylist, isnum, add3,
                             mylist, False, True)

        mylist = [3, 'some str', 8.4, 'other str', -5]
        self.assertDeepPatch(mylist, isnum, add3,
                             [6, 'some str', 11.4, 'other str', -2], True, True)

    def test_simpleTuple(self):
        # isstr / addsuffix
        isstr = lambda x: isinstance(x, str)
        addsuffix = lambda x: x + 'suffix'

        foobar = 'foobar'
        mytuple = (foobar,)
        self.assertDeepPatch(mytuple, isstr, addsuffix,
                             ('foobarsuffix',), True, False)

        mytuple = (2, 8)
        self.assertDeepPatch(mytuple, isstr, addsuffix,
                             mytuple, False, True)

        mytuple = (3.7, 'blah')
        self.assertDeepPatch(mytuple, isstr, addsuffix,
                             (3.7, 'blahsuffix'), True, False)

        # isnum / add3
        isnum = lambda x: isinstance(x, numbers.Number)
        add3 = lambda x: x + 3

        mytuple = ()
        self.assertDeepPatch(mytuple, isnum, add3,
                             mytuple, False, True)

        mytuple = (3, 'some str', 8.4, 'other str', -5)
        self.assertDeepPatch(
            mytuple, isnum, add3,
            (6, 'some str', 11.4, 'other str', -2), True, False)

    def test_simpleDict(self):
        # isstr / addsuffix
        isstr = lambda x: isinstance(x, str)
        addsuffix = lambda x: x + 'suffix'

        mydict = {}
        self.assertDeepPatch(mydict, isstr, addsuffix,
                             mydict, False, True)

        mydict = {2.8: isstr}
        self.assertDeepPatch(mydict, isstr, addsuffix,
                             mydict, False, True)

        mydict = {7: 'foo'}
        self.assertDeepPatch(mydict, isstr, addsuffix,
                             {7: 'foosuffix'}, True, True)

        mydict = {'7': True}
        self.assertDeepPatch(mydict, isstr, addsuffix,
                             {'7suffix': True}, True, True)

        mydict = {'foo': 'bar'}
        self.assertDeepPatch(mydict, isstr, addsuffix,
                             {'foosuffix': 'barsuffix'}, True, True)

        mydict = {
            'some': 'thing',
            'other': 8,
            2.8: 'result',
        }
        self.assertDeepPatch(
            mydict, isstr, addsuffix,
            {
                'somesuffix': 'thingsuffix',
                'othersuffix': 8,
                2.8: 'resultsuffix',
            }, True, True)

        # check that altering a key to be the same as another (before it is
        # altered) works
        mydict = {
            '': 1,
            'suffix': 2,
        }
        self.assertDeepPatch(
            mydict, isstr, addsuffix,
            {
                'suffix': 1,
                'suffixsuffix': 2,
            }, True, True)

    def test_complexDict(self):
        # isnum / add3
        isnum = lambda x: isinstance(x, numbers.Number)
        add3 = lambda x: x + 3
        
        mydict = {
            3: [5, 'foo', '3'],
            (2, 'blah'): {
                'seven': add3,
                8: 5.0
            },
            3.8: set([7, 2.8, 'stuff']),
            0: ('foo', 8, [7, 9, (8, 5, 'gobble')]),
        }
        mydictcopy = dict(mydict)

        result = self.assertDeepPatch(
            mydict, isnum, add3,
            {
                6: [8, 'foo', '3'],
                (5, 'blah'): {
                    'seven': add3,
                    11: 8.0
                },
                6.8: set([10, 5.8, 'stuff']),
                3: ('foo', 11, [10, 12, (11, 8, 'gobble')]),
            }, True, True)

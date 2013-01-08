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
        print 'diff:', diff
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

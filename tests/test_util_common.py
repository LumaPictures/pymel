'''
Created on Oct 16, 2012

@author: paulm
'''

import unittest

import pymel.util.common as util

class testCase_isClassRunningStack(unittest.TestCase):
    def test_frame1of1(self):
        class Different(object):
            pass
        
        class Alike(object):
            def methodCheckForDifferent(self):
                pass
            def methodCheckForAlike(self):
                pass
            def methodCheckForTheClass(self):
                pass
            
        class TheClass(object):
            def methodCheckForDifferent(self):
                return util.isClassRunningStack(Different)
            def methodCheckForAlike(self):
                return util.isClassRunningStack(Alike)
        def methodCheckForTheClass(self):
            return util.isClassRunningStack(TheClass)
        TheClass.methodCheckForTheClass = methodCheckForTheClass
        
        self.assertFalse(TheClass().methodCheckForDifferent())
        self.assertFalse(TheClass().methodCheckForAlike())
        self.assertTrue(TheClass().methodCheckForTheClass())
        
    def test_frame1of2(self):
        class Different(object):
            pass
        
        class Alike(object):
            def methodCheckForDifferent(self):
                pass
            def methodCheckForAlike(self):
                pass
            def methodCheckForTheClass(self):
                pass
            
        class TheClass(object):
            def methodCheckForDifferent(self):
                return util.isClassRunningStack(Different)
            def methodCheckForAlike(self):
                return util.isClassRunningStack(Alike)
        def methodCheckForTheClass(self):
            return util.isClassRunningStack(TheClass)
        TheClass.methodCheckForTheClass = methodCheckForTheClass
        
        def outerFuncDifferent():
            return TheClass().methodCheckForDifferent()
        def outerFuncAlike():
            return TheClass().methodCheckForAlike()
        def outerFuncTheClass():
            return TheClass().methodCheckForTheClass()
        
        self.assertFalse(outerFuncDifferent())
        self.assertFalse(outerFuncAlike())
        self.assertTrue(outerFuncTheClass())

    def test_frame2of2(self):
        class Different(object):
            pass
        
        class Alike(object):
            def methodCheckRunner(self):
                pass
            
        class TheClass(object):
            def methodCheckRunner(self, innerCheckFunc):
                return innerCheckFunc()
        
        def innerFuncDifferent():
            return util.isClassRunningStack(Different)
        def innerFuncAlike():
            return util.isClassRunningStack(Alike)
        def innerFuncTheClass():
            return util.isClassRunningStack(TheClass)
        
        self.assertFalse(TheClass().methodCheckRunner(innerFuncDifferent))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncAlike))
        self.assertTrue(TheClass().methodCheckRunner(innerFuncTheClass))
                 
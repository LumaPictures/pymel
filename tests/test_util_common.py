'''
Created on Oct 16, 2012

@author: paulm
'''
import re
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

    def test_frame2of2_filtered_str(self):
        class Different(object):
            pass

        class Alike(object):
            def methodCheckRunner(self):
                pass

        class TheClass(object):
            def methodCheckRunner(self, innerCheckFunc):
                return innerCheckFunc()
            def anotherMethod(self):
                pass

        def innerFuncDifferent_filterPass():
            return util.isClassRunningStack(Different, methodFilter='methodCheckRunner')
        def innerFuncAlike_filterPass():
            return util.isClassRunningStack(Alike, methodFilter='methodCheckRunner')
        def innerFuncTheClass_filterPass():
            return util.isClassRunningStack(TheClass, methodFilter='methodCheckRunner')

        def innerFuncDifferent_filterFail():
            return util.isClassRunningStack(Different, methodFilter='anotherMethod')
        def innerFuncAlike_filterFail():
            return util.isClassRunningStack(Alike, methodFilter='anotherMethod')
        def innerFuncTheClass_filterFail():
            return util.isClassRunningStack(TheClass, methodFilter='anotherMethod')


        self.assertFalse(TheClass().methodCheckRunner(innerFuncDifferent_filterPass))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncAlike_filterPass))
        self.assertTrue(TheClass().methodCheckRunner(innerFuncTheClass_filterPass))

        self.assertFalse(TheClass().methodCheckRunner(innerFuncDifferent_filterFail))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncAlike_filterFail))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncTheClass_filterFail))

    def test_frame2of2_filtered_re(self):
        class Different(object):
            pass

        class Alike(object):
            def methodCheckRunner(self):
                pass

        class TheClass(object):
            def methodCheckRunner(self, innerCheckFunc):
                return innerCheckFunc()
            def anotherMethod(self):
                pass

        passRe = re.compile('Check|Foo')
        failRe = re.compile('nother')

        def innerFuncDifferent_filterPass():
            return util.isClassRunningStack(Different, methodFilter=passRe)
        def innerFuncAlike_filterPass():
            return util.isClassRunningStack(Alike, methodFilter=passRe)
        def innerFuncTheClass_filterPass():
            return util.isClassRunningStack(TheClass, methodFilter=passRe)

        def innerFuncDifferent_filterFail():
            return util.isClassRunningStack(Different, methodFilter=failRe)
        def innerFuncAlike_filterFail():
            return util.isClassRunningStack(Alike, methodFilter=failRe)
        def innerFuncTheClass_filterFail():
            return util.isClassRunningStack(TheClass, methodFilter=failRe)


        self.assertFalse(TheClass().methodCheckRunner(innerFuncDifferent_filterPass))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncAlike_filterPass))
        self.assertTrue(TheClass().methodCheckRunner(innerFuncTheClass_filterPass))

        self.assertFalse(TheClass().methodCheckRunner(innerFuncDifferent_filterFail))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncAlike_filterFail))
        self.assertFalse(TheClass().methodCheckRunner(innerFuncTheClass_filterFail))


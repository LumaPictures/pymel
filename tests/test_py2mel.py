import unittest

import maya.mel as mel
import pymel.core as pm
import pymel.versions as versions

import pymel.tools.py2mel as py2mel

WRAPPED_CMDS = {}

class MyClassNoArgs(object):
    def noArgs(self):
        return "foo"

    def oneArg(self, arg1):
        return arg1 * 2

    def oneKwarg(self, kwarg1='default'):
        return kwarg1 * 2

    def oneArgOneKwarg(self, arg1, kwarg1='default'):
        return arg1 + kwarg1

    def oneArgTwoKwarg(self, arg1, kwarg1='ate', kwarg2='trex'):
        return '%s %s %s!' % (arg1, kwarg1, kwarg2)

class testCaseClassWrap(unittest.TestCase):
    def wrapClass(self, toWrap, cmdName, *args, **kwargs):
        global WRAPPED_CMDS
        if cmdName not in WRAPPED_CMDS:
            py2mel.py2melCmd(toWrap, commandName=cmdName, *args, **kwargs)
            WRAPPED_CMDS[cmdName] = toWrap
        elif WRAPPED_CMDS[cmdName] != toWrap:
            raise RuntimeError('error - already another command called %s' % cmdName)

    def assertMelError(self, cmd):
        # in maya 2014, a RuntimeError is raised... yay!
        self.assertRaises(RuntimeError, mel.eval, cmd)

    def test_autoName(self):
        self.wrapClass(MyClassNoArgs, None)
        self.assertEqual(mel.eval('''MyClassNoArgs -noArgs'''), 'foo')

    def test_noArgs(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertEqual(mel.eval('''myCls -noArgs'''), 'foo')

    def test_oneArg(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertEqual(mel.eval('''myCls -oneArg stuff'''), 'stuffstuff')

    def test_oneKwarg(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertEqual(mel.eval('''myCls -oneKwarg goober'''), 'goobergoober')

    def test_oneKwarg_notEnoughArgsErr(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertMelError('''myCls -oneKwarg''')

    def test_oneArgOneKwarg(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertEqual(mel.eval('''myCls -oneArgOneKwarg stuff thing'''), 'stuffthing')

    def test_oneArgOneKwarg_notEnoughArgsErr(self):
        self.wrapClass(MyClassNoArgs, 'myCls')
        self.assertMelError('''myCls -oneArgOneKwarg''')
        self.assertMelError('''myCls -oneArgOneKwarg stuff''')

    def test_nameTooShort(self):
        class ShortFuncCls(object):
            def go(self):
                return 'Manitoba'
        self.wrapClass(ShortFuncCls, 'myShort')
        self.assertEqual(mel.eval('''myShort -goxx'''), 'Manitoba')
        self.assertEqual(mel.eval('''myShort -g'''), 'Manitoba')

    def test_excludeFlag(self):
        self.wrapClass(MyClassNoArgs, 'myCls2', excludeFlags=['oneKwarg'])
        self.assertEqual(mel.eval('''myCls2 -oneArg stuff'''), 'stuffstuff')
        self.assertMelError('''myCls2 -oneKwarg goober''')

    def test_excludeFlagArg(self):
        self.wrapClass(MyClassNoArgs, 'myCls3', excludeFlagArgs={'oneKwarg':['kwarg1']})
        self.assertEqual(mel.eval('''myCls3 -oneKwarg'''), 'defaultdefault')
        self.assertMelError('''myCls3 -oneKwarg goober''')

    def test_excludeFlagArg_orderChanged(self):
        self.wrapClass(MyClassNoArgs, 'myCls4', excludeFlagArgs={'oneArgTwoKwarg':['kwarg1']})
        self.assertMelError('''myCls4 -oneArgTwoKwarg foo''')
        self.assertEqual(mel.eval('''myCls4 -oneArgTwoKwarg "Little Bo PeeP" Batman'''), 'Little Bo PeeP ate Batman!')
        self.assertMelError('''myCls4 -oneArgTwoKwarg defenestrated You Spiderman''')

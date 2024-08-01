from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import unittest, sys

import maya.mel
import pymel.core

from pymel.tools.mel2py import mel2pyStr

class TestStrings(unittest.TestCase):
    def assertMelAndPyStringsEqual(self, melString, verbose=False):
        if verbose:
            print("Original mel string:")
            print(melString)

        #melCmd = '$tempStringVar = %s; print $tempStringVar; $tempStringVar = $tempStringVar;' % melString
        melCmd = '$tempStringVar = %s;' % melString
        if verbose:
            print("Mel assignment command:")
            print(melCmd)
        strFromMMEval = maya.mel.eval(melCmd)

        if verbose:
            print("Decoded through maya.mel:")
            print(strFromMMEval)

        pyCmd = mel2pyStr(melCmd)
        if verbose:
            print("Python assignment command:")
            print(pyCmd)
        exec_globals = {}
        exec(pyCmd, exec_globals)
        strFromPy2Mel = exec_globals['tempStringVar']

        if verbose:
            print("Decoded through py2mel:")
            print(strFromPy2Mel)

        self.assertEqual(strFromMMEval, strFromPy2Mel)

    def testBackslashQuoteStrings(self):
        melStrs = [r'''"\\"''',         # "\\" - mel string for: \
                   r'''"\""''',         # "\"" - mel string for: "
                   r'''"\"\""''',       # "\"\"" - mel string for: ""
                   r'''"\\\""''',       # "\\\"" - mel string for: \"
                   r'''"\"\\"''',       # "\"\\" - mel string for: "\
                   r'''"\\\\\""''',     # "\\\\\"" - mel string for: \\"
                   r'''"\\\\\\\""''']   # "\\\\\\\"" - mel string for: \\\"
        for melStr in melStrs:
            self.assertMelAndPyStringsEqual(melStr)

    def test_basics(self):
        self.assertEqual(
            mel2pyStr('polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;'),
            'from pymel.all import *\npolyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1, ax=(0, 1, 0), cuv=4, ch=1)\n')

#testingutils.setupUnittestModule(__name__)


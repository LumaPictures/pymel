import unittest, sys

import maya.mel
import pymel.util.test.testingutils as testingutils

from pymel.tools.mel2py import mel2pyStr



class TestStrings(testingutils.TestCaseExtended):
    def assertMelAndPyStringsEqual(self, melString, verbose=False):
        if verbose:
            print "Original mel string:"
            print melString
            
        #melCmd = '$tempStringVar = %s; print $tempStringVar; $tempStringVar = $tempStringVar;' % melString
        melCmd = '$tempStringVar = %s;' % melString
        strFromMMEval = maya.mel.eval(melCmd)
    
        if verbose:
            print "Decoded through maya.mel:"
            print strFromMMEval
            
        exec mel2pyStr(melCmd)
        strFromPy2Mel = tempStringVar
        
        if verbose:
            print "Decoded through py2mel:"
            print strFromPy2Mel
        
        self.assertEqual(strFromMMEval, strFromPy2Mel)
    
    def testBackslashQuoteStrings(self):
        melStrs = [r'''"\\"''',         # "\\" - mel string for: \
                   r'''"\""''',         # "\"" - mel string for: "
                   r'''"\"\""''',       # "\"\"" - mel string for: "" 
                   r'''"\\\""''',       # "\\\"" - mel string for: \"
                   r'''"\"\\"''',       # "\"\\" - mel string for: "\
                   r'''"\\\\\""''',     # "\\\\\"" - mel string for: \\"
                   r'''"\\\\\\\""''']   # "\\\\\\\"" - mel string for: \\\"
        for str in melStrs:
            self.assertMelAndPyStringsEqual(str)

testingutils.setupUnittestModule(__name__)


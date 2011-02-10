import unittest, sys

import maya.mel

from pymel.tools.mel2py import mel2pyStr



class TestStrings(unittest.TestCase):
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
        for melStr in melStrs:
            self.assertMelAndPyStringsEqual(melStr)

#testingutils.setupUnittestModule(__name__)


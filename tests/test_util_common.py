'''
Created on Oct 16, 2012

@author: paulm
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# used to have tests for util.isClassRunningStack, but it turned out
# inspect.stack() could cause crashes in some cases...

import unittest
from pymel.util.scanf import (sscanf, fscanf, CharacterBufferFromIterable,
                              makeCharBuffer, handleWhitespace, handleChar,
                              handleDecimalInt, handleString, CappedBuffer,
                              IncompleteCaptureError, FormatError, compile)


class ScanfTests(unittest.TestCase):

    def bufferFromString(self, s):
        return CharacterBufferFromIterable(s)

    def testBufferFromString(self):
        b = self.bufferFromString("hello")
        for letter in list('hello'):
            self.assertEqual(letter, b.getch())
        self.assertEqual('', b.getch())

    def testCharacterSetScanning(self):
        b = makeCharBuffer("+++-+++++1234")
        self.assertEqual("+++", b.scanCharacterSet(set("+")))
        self.assertEqual("", b.scanCharacterSet(set("+")))
        self.assertEqual("-", b.scanCharacterSet(set("-")))
        self.assertEqual("+", b.scanCharacterSet(set("+"), 1))

    def testPredicateScanning(self):
        b = makeCharBuffer("+++-+++++1234")
        self.assertEqual("+++", b.scanPredicate(lambda ch: ch == '+'))

    def testUngetch(self):
        b = self.bufferFromString("ong")
        b.ungetch('y')
        self.assertEqual('y', b.getch())
        self.assertEqual('o', b.getch())
        b.ungetch('u')
        self.assertEqual('u', b.getch())
        self.assertEqual('n', b.getch())
        self.assertEqual('g', b.getch())
        self.assertEqual('', b.getch())

    def testRepeatedGetchOnEmptyStreamIsOk(self):
        b = self.bufferFromString("")
        self.assertEqual('', b.getch())
        self.assertEqual('', b.getch())

    def testCappedBuffer(self):
        b = CappedBuffer(self.bufferFromString("supercalifragilisticexpialidocious"), 5)
        self.assertEqual("s", b.getch())
        self.assertEqual("u", b.getch())
        self.assertEqual("p", b.getch())
        self.assertEqual("e", b.getch())
        self.assertEqual("r", b.getch())
        self.assertEqual('', b.getch())
        self.assertEqual('', b.getch())
        b.ungetch('r')
        self.assertEqual("r", b.getch())
        self.assertEqual('', b.getch())

    def testWhitespaceScanning(self):
        b = self.bufferFromString("    42\n43")
        self.assertEqual("    ", handleWhitespace(b))
        self.assertEqual("", handleWhitespace(b))
        self.assertEqual("4", b.getch())

    def testDecimalDigitScanning(self):
        b = self.bufferFromString("42 43!44")
        self.assertEqual(42, handleDecimalInt(b))
        self.assertEqual(" ", handleWhitespace(b))
        self.assertEqual(43, handleDecimalInt(b))

        b2 = self.bufferFromString("-1-2+3-4")
        self.assertEqual(-1, handleDecimalInt(b2))
        self.assertEqual(-2, handleDecimalInt(b2))
        self.assertEqual(3, handleDecimalInt(b2))
        self.assertEqual(-4, handleDecimalInt(b2))
        self.assertRaises(FormatError, handleDecimalInt, b2)

    def testCharacter(self):
        b = self.bufferFromString("hi!")
        self.assertEqual("h", handleChar(b))
        self.assertEqual("i", handleChar(b))
        self.assertEqual("!", handleChar(b))
        self.assertRaises(FormatError, handleChar, b)

    def testString(self):
        b = self.bufferFromString("-42 + 1 equals -41")
        self.assertEqual("-42", handleString(b))
        handleWhitespace(b)
        self.assertEqual("+", handleString(b))
        handleWhitespace(b)
        self.assertEqual("1", handleString(b))
        handleWhitespace(b)
        self.assertEqual("equals", handleString(b))
        handleWhitespace(b)
        self.assertEqual("-41", handleString(b))

    def testIntegerScanning(self):
        self.assertEqual((42, 43),
                          sscanf("   42\n   43  ", "%d %d"))
        self.assertEqual((8,), sscanf("10", "%o"))
        self.assertEqual((8,), sscanf("010", "%o"))
        self.assertEqual((15,), sscanf("F", "%x"))
        self.assertEqual((15,), sscanf("f", "%x"))
        self.assertEqual((15,), sscanf("0xF", "%x"))
        self.assertEqual((15,), sscanf("0XF", "%x"))
        self.assertEqual((15,), sscanf("0Xf", "%x"))
        self.assertEqual((-1, -2, 3, -4), sscanf("-1-2+3-4", "%d%d%d%d"))

    def testWordScanning(self):
        self.assertEqual(("hello", "world"),
                          sscanf("   hello world", "%s %s"))

    def testSuppression(self):
        self.assertEqual((), sscanf(" hello world", "%*s %*s"))
        self.assertEqual(("happy",),
                          sscanf("hello happy world", "%*s %s %*s"))
        self.assertEqual((), sscanf("h", "%*c"))

    def testWidth(self):
        self.assertEqual(("00010",), sscanf("00010101010111", "%5c"))
        self.assertEqual(("xy",), sscanf("xyz", "%2s"))
        self.assertEqual(("xy",), sscanf("              xyz", "%2s"))
        self.assertEqual(("  ",), sscanf("              xyz", "%2c"))

    def testFscanf(self):
        import io
        b = io.StringIO("hello world")
        self.assertEqual(("hello", " ", "world"), fscanf(b, "%s%c%s"))
        # Check that calling fscanf() twice doesn't
        # drop the last character
        b2 = io.StringIO("hello world")
        self.assertEqual(("hello",), fscanf(b2, "%s"))
        self.assertEqual((" ",), fscanf(b2, "%c"))
        self.assertEqual(("world",), fscanf(b2, "%s"))

    def testSkipLeadingSpaceOnScanning(self):
        """Ralph Heinkel reported a bug where floats weren't being
        parsed properly if there were leading whitespace for %f.
        This case checks that"""
        self.assertEqual((42.0,),
                          sscanf("    42.0", "%f"))

    def testFloats(self):
        self.assertEqual((3.14,
                           10.,
                           .001,
                           1e100,
                           3.14e-10,
                           0e0,), sscanf("""3.14
                           10.
                           .001
                           1e100
                           3.14e-10
                           0e0""", "%f %f %f %f %f %f"))

    def testMoreSimpleScanningExamples(self):
        self.assertEqual((192, 168, 1, 1),
                          sscanf("192.168.1.1", "%d.%d.%d.%d"))
        self.assertEqual(("a", "b", "c"),
                          sscanf("  ab   c  ", "%1s%1s%s"))
        self.assertEqual(("hello", " ", "world"),
                          sscanf("hello world", "%s%c%s"))
        self.assertRaises(IncompleteCaptureError,
                          sscanf, "192.168.1.1", "%d %d %d %d")
        self.assertEqual(("danny",),
                          sscanf("hi danny", "hi %s"))
        self.assertEqual(("danny",),
                          sscanf("  hi danny", "  hi %s"))
        self.assertEqual(("a", "b", 3),
                          sscanf("ab3", "%c%c%d"))
        # this case is weird, but it happens in C too!
        self.assertRaises(IncompleteCaptureError,
                          sscanf, "  hi danny", "hi %s")

        # The example that's used in
        # 'http://docs.python.org/lib/node109.html'
        self.assertEqual(("/usr/bin/sendmail", 0, 4),
                          sscanf("/usr/bin/sendmail - 0 errors, 4 warnings",
                                 "%s - %d errors, %d warnings"))

    def testErroneousFormats(self):
        self.assertRaises(FormatError, compile, "%")
        self.assertRaises(FormatError, compile, "% ")
        self.assertRaises(FormatError, compile, "%*")
        self.assertRaises(FormatError, compile, "%*z")
        self.assertRaises(FormatError, compile, "% d")
        self.assertRaises(FormatError, compile, "%* d")

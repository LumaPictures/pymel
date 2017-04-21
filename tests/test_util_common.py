'''
Created on Oct 16, 2012

@author: paulm
'''

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
            self.assertEquals(letter, b.getch())
        self.assertEquals('', b.getch())

    def testCharacterSetScanning(self):
        b = makeCharBuffer("+++-+++++1234")
        self.assertEquals("+++", b.scanCharacterSet(set("+")))
        self.assertEquals("", b.scanCharacterSet(set("+")))
        self.assertEquals("-", b.scanCharacterSet(set("-")))
        self.assertEquals("+", b.scanCharacterSet(set("+"), 1))

    def testPredicateScanning(self):
        b = makeCharBuffer("+++-+++++1234")
        self.assertEquals("+++", b.scanPredicate(lambda ch: ch == '+'))

    def testUngetch(self):
        b = self.bufferFromString("ong")
        b.ungetch('y')
        self.assertEquals('y', b.getch())
        self.assertEquals('o', b.getch())
        b.ungetch('u')
        self.assertEquals('u', b.getch())
        self.assertEquals('n', b.getch())
        self.assertEquals('g', b.getch())
        self.assertEquals('', b.getch())

    def testRepeatedGetchOnEmptyStreamIsOk(self):
        b = self.bufferFromString("")
        self.assertEquals('', b.getch())
        self.assertEquals('', b.getch())

    def testCappedBuffer(self):
        b = CappedBuffer(self.bufferFromString("supercalifragilisticexpialidocious"), 5)
        self.assertEquals("s", b.getch())
        self.assertEquals("u", b.getch())
        self.assertEquals("p", b.getch())
        self.assertEquals("e", b.getch())
        self.assertEquals("r", b.getch())
        self.assertEquals('', b.getch())
        self.assertEquals('', b.getch())
        b.ungetch('r')
        self.assertEquals("r", b.getch())
        self.assertEquals('', b.getch())

    def testWhitespaceScanning(self):
        b = self.bufferFromString("    42\n43")
        self.assertEquals("    ", handleWhitespace(b))
        self.assertEquals("", handleWhitespace(b))
        self.assertEquals("4", b.getch())

    def testDecimalDigitScanning(self):
        b = self.bufferFromString("42 43!44")
        self.assertEquals(42, handleDecimalInt(b))
        self.assertEquals(" ", handleWhitespace(b))
        self.assertEquals(43, handleDecimalInt(b))

        b2 = self.bufferFromString("-1-2+3-4")
        self.assertEquals(-1, handleDecimalInt(b2))
        self.assertEquals(-2, handleDecimalInt(b2))
        self.assertEquals(3, handleDecimalInt(b2))
        self.assertEquals(-4, handleDecimalInt(b2))
        self.assertRaises(FormatError, handleDecimalInt, b2)

    def testCharacter(self):
        b = self.bufferFromString("hi!")
        self.assertEquals("h", handleChar(b))
        self.assertEquals("i", handleChar(b))
        self.assertEquals("!", handleChar(b))
        self.assertRaises(FormatError, handleChar, b)

    def testString(self):
        b = self.bufferFromString("-42 + 1 equals -41")
        self.assertEquals("-42", handleString(b))
        handleWhitespace(b)
        self.assertEquals("+", handleString(b))
        handleWhitespace(b)
        self.assertEquals("1", handleString(b))
        handleWhitespace(b)
        self.assertEquals("equals", handleString(b))
        handleWhitespace(b)
        self.assertEquals("-41", handleString(b))

    def testIntegerScanning(self):
        self.assertEquals((42, 43),
                          sscanf("   42\n   43  ", "%d %d"))
        self.assertEquals((8,), sscanf("10", "%o"))
        self.assertEquals((8,), sscanf("010", "%o"))
        self.assertEquals((15,), sscanf("F", "%x"))
        self.assertEquals((15,), sscanf("f", "%x"))
        self.assertEquals((15,), sscanf("0xF", "%x"))
        self.assertEquals((15,), sscanf("0XF", "%x"))
        self.assertEquals((15,), sscanf("0Xf", "%x"))
        self.assertEquals((-1, -2, 3, -4), sscanf("-1-2+3-4", "%d%d%d%d"))

    def testWordScanning(self):
        self.assertEquals(("hello", "world"),
                          sscanf("   hello world", "%s %s"))

    def testSuppression(self):
        self.assertEquals((), sscanf(" hello world", "%*s %*s"))
        self.assertEquals(("happy",),
                          sscanf("hello happy world", "%*s %s %*s"))
        self.assertEquals((), sscanf("h", "%*c"))

    def testWidth(self):
        self.assertEquals(("00010",), sscanf("00010101010111", "%5c"))
        self.assertEquals(("xy",), sscanf("xyz", "%2s"))
        self.assertEquals(("xy",), sscanf("              xyz", "%2s"))
        self.assertEquals(("  ",), sscanf("              xyz", "%2c"))

    def testFscanf(self):
        import StringIO
        b = StringIO.StringIO("hello world")
        self.assertEquals(("hello", " ", "world"), fscanf(b, "%s%c%s"))
        # Check that calling fscanf() twice doesn't
        # drop the last character
        b2 = StringIO.StringIO("hello world")
        self.assertEquals(("hello",), fscanf(b2, "%s"))
        self.assertEquals((" ",), fscanf(b2, "%c"))
        self.assertEquals(("world",), fscanf(b2, "%s"))

    def testSkipLeadingSpaceOnScanning(self):
        """Ralph Heinkel reported a bug where floats weren't being
        parsed properly if there were leading whitespace for %f.
        This case checks that"""
        self.assertEquals((42.0,),
                          sscanf("    42.0", "%f"))

    def testFloats(self):
        self.assertEquals((3.14,
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
        self.assertEquals((192, 168, 1, 1),
                          sscanf("192.168.1.1", "%d.%d.%d.%d"))
        self.assertEquals(("a", "b", "c"),
                          sscanf("  ab   c  ", "%1s%1s%s"))
        self.assertEquals(("hello", " ", "world"),
                          sscanf("hello world", "%s%c%s"))
        self.assertRaises(IncompleteCaptureError,
                          sscanf, "192.168.1.1", "%d %d %d %d")
        self.assertEquals(("danny",),
                          sscanf("hi danny", "hi %s"))
        self.assertEquals(("danny",),
                          sscanf("  hi danny", "  hi %s"))
        self.assertEquals(("a", "b", 3),
                          sscanf("ab3", "%c%c%d"))
        # this case is weird, but it happens in C too!
        self.assertRaises(IncompleteCaptureError,
                          sscanf, "  hi danny", "hi %s")

        # The example that's used in
        # 'http://docs.python.org/lib/node109.html'
        self.assertEquals(("/usr/bin/sendmail", 0, 4),
                          sscanf("/usr/bin/sendmail - 0 errors, 4 warnings",
                                 "%s - %d errors, %d warnings"))

    def testErroneousFormats(self):
        self.assertRaises(FormatError, compile, "%")
        self.assertRaises(FormatError, compile, "% ")
        self.assertRaises(FormatError, compile, "%*")
        self.assertRaises(FormatError, compile, "%*z")
        self.assertRaises(FormatError, compile, "% d")
        self.assertRaises(FormatError, compile, "%* d")

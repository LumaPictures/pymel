from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import unittest

import pymel.util.path
from pymel.util.path import path

class TestPath(unittest.TestCase):
    def test_misc(self):
        thisFile = path(__file__)
        self.assertTrue(thisFile.exists())
        self.assertTrue(thisFile.isfile())
        self.assertFalse(thisFile.isdir())
        self.assertIn(thisFile.basename(), (path('test_util_path.py'),
                                            path('test_util_path.pyc')))
        self.assertEqual(thisFile.namebase, 'test_util_path')
        self.assertIn(thisFile.ext, ('.py', '.pyc'))

        thisDir = thisFile.dirname()
        self.assertEqual(thisDir, os.path.dirname(str(thisFile)))

        self.assertTrue(thisDir.exists())
        self.assertFalse(thisDir.isfile())
        self.assertTrue(thisDir.isdir())
        self.assertEqual(thisDir.basename(), 'tests')
        self.assertEqual(thisDir.namebase, 'tests')
        self.assertEqual(thisDir.ext, '')

        files = thisDir.files()
        self.assertIn(thisFile, files)

        noExist = path('slartybartfast_fasdfjlkfjl')
        self.assertFalse(noExist.exists())
        self.assertFalse(noExist.isfile())
        self.assertFalse(noExist.isdir())




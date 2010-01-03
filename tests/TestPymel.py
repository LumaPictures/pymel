#!/usr/bin/env mayapy

import unittest
import os
"""
This module is for integrating pymel tests into a larger unittest framework.
If you just wish to test pymel, use pymel_test instead.
"""

import sys
import inspect

gCantRun = False
try:
    import nose
except ImportError:
    gCantRun = True
    print('** nose module required for this test **')

if not gCantRun:
    thisDir = os.path.dirname(inspect.getsourcefile( lambda:None ))
    try:
        import pymel_test
    except ImportError:
        sys.path.append(thisDir)
        try:
            import pymel_test
        except ImportError:
            gCantRun = True
            import traceback
            print('** error importing pymel_test: **')
            traceback.print_exc()
            
if not gCantRun:
    class TestPymel(unittest.TestCase):
        pymelDir = os.path.dirname(thisDir)
        def testPymel(self):
           pymel_test.nose_test(pymelDir=self.pymelDir)

    if __name__ == '__main__':
        #from pymel import core
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPymel)
        unittest.TextTestRunner(verbosity=2).run(suite)
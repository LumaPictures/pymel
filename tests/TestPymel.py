#!/usr/bin/env mayapy

import unittest
import os
import sys
import inspect

gCantRun = False
try:
    import nose
except ImportError:
    gCantRun = True
    print('** nose module required for this test **')

##
# Stub to integrate Pymel nose tests into 
# Maya python unittest framework
#

def nose_test(module=None, extraArgs=None,pymelDir=None):
    """
    Run pymel unittests / doctests
    All the preamble taken from pymel_test.py
    """

    if pymelDir:
        os.chdir(pymelDir)
    
    noseKwArgs={}
    noseArgv = "dummyArg0 --with-doctest -v".split()
    if module is None:
        exclusion = '^windows ^tools ^example1 ^testingutils ^pmcmds ^testPa ^maya ^maintainence ^pymel_test ^TestPymel'
        noseArgv += ['--exclude', '|'.join( [ '(%s)' % x for x in exclusion.split() ] )  ]
           
    if inspect.ismodule(module):
        noseKwArgs['module']=module
    elif module:
        noseArgv.append(module)
    if extraArgs is not None:
        noseArgv.extend(extraArgs)
    noseKwArgs['argv'] = noseArgv
    nose.main( **noseKwArgs)

class TestPymel(unittest.TestCase):
    pymelDir = '/path/to/top_of_pymel'
    def testPymel(self):
        nose_test(pymelDir=self.pymelDir)


if gCantRun is True:
    del TestPymel


if __name__ == '__main__':
    #from pymel import core
    import unittest
    import TestPymel
    os.environ['MAYA_PSEUDOTRANS_MODE']='5'
    os.environ['MAYA_PSEUDOTRANS_VALUE']=','
    TestPymel.TestPymel.pymelDir = os.path.dirname( os.path.dirname(sys.argv[0]) )
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPymel.TestPymel)
    unittest.TextTestRunner(verbosity=2).run(suite)
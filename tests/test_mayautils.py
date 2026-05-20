#import testingutils
import unittest
import pymel.versions
import inspect
import maya.cmds as cmds

class TestGetMayaVersion(unittest.TestCase):

    versions = ['6', '6.0', '7', '7.0', '8', '8.0', '8.5', '2008', '2009']
    extensions = [1, 2, 2008]
    servicePacks = [1, 2, 3009]
    bits = [32, 64, 1, 16]
    cuts = ['200802242349', '32', '200802242349-3040-2']

    def runTest(self):
        #testingutils.permutations([versions, extensions, servicePacks, bits, cuts])
        pass

    def test_hasVersionConstant(self):
        versions = set([x[1] for x in inspect.getmembers(pymel.versions)
                        if x[0][0] == 'v' and x[0][1].isdigit()])
        currentVersion = cmds.about(api=True)
        self.assertIn(currentVersion, versions)


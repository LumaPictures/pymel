#import testingutils
import unittest
import pymel.internal.startup

class TestGetMayaVersion(unittest.TestCase):
    
    versions = ['6', '6.0', '7', '7.0', '8', '8.0', '8.5', '2008', '2009']
    extensions = [1, 2, 2008]
    servicePacks = [1, 2, 3009]
    bits = [32, 64, 1, 16]
    cuts = ['200802242349', '32', '200802242349-3040-2']
    
    def runTest(self):
        #testingutils.permutations([versions, extensions, servicePacks, bits, cuts])
        pass

    
    

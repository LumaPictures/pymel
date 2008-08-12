import sys, os, inspect, unittest

#import pymel
#import pymel.core.factories as _factories
#import maya.cmds as cmds
#
#
#
#
#
#   
#def testNodeCmds(verbose=False):
#  
#    #emptyFunctions = []
#    
#    for funcName in _factories.nodeCommandList:
#        _factories.testNodeCmd( funcName, _factories.cmdlist[funcName], verbose )
#         
#    print "done"
#    #print emptyFunctions


class testCase_attributes(unittest.TestCase):

    def setUp(self):
        self.sphere1, hist = polySphere()
        self.cube1, hist = polyCube()
        self.grp1 = group(self.sphere1, self.cube1)
        self.grp2 = duplicate(self.grp1)[0]
        self.sphere2, self.cube2 = self.grp2.getChildren()
        
    def test01_isDagOnObjects(self):
        self.sphere2.t.tx.parent()
        self.assertEqual( self.sphere2.t.tx.parent(), self.sphere2.t )
        
    def tearDown(self):
        # cleaning
        delete(self.grp1,self.grp2)
        
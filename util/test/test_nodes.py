import sys, os, inspect, unittest
from pymel import *
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


class testCase_nodesAndAttributes(unittest.TestCase):

    def setUp(self):
        self.sphere1, hist = polySphere()
        self.cube1, hist = polyCube()
        self.grp1 = group(self.sphere1, self.cube1)
        
        #duplicate
        self.grp2 = duplicate(self.grp1)[0]
        self.sphere2, self.cube2 = self.grp2.getChildren()
        
        #instance
        self.grp3 = instance(self.grp1)[0]
        self.sphere3, self.cube3 = self.grp3.getChildren()
        
    def test01_attribute_parent_equality(self):
        self.assertEqual( self.sphere2.t.tx.parent(), self.sphere2.t )
        
    def test02_attribute_duplicate_inequality(self):
        self.assert_( self.sphere1.t != self.sphere2.t )
        
    def test03_attribute_instance_equality(self):
        self.assertEqual( self.sphere1.t, self.sphere3.t )
    
    def test04_attribute_cascading(self):
        self.sphere1.primaryVisibility.set(1)
        shape = self.sphere1.getShape()
        self.assertEqual( self.sphere1.primaryVisibility, shape.primaryVisibility )
    
    def test05_dagNode_addParent(self):
        sphere = polySphere()[0]
        cube = polyCube()[0]
        torus = polyTorus()[0]
        sphere | cube | torus
        print torus.fullPath()
        
    #def test05_dagNode_getParent(self):
    def test_instances(self):
        self.assert_( self.sphere1.isInstance( self.sphere3) )   
        
    def tearDown(self):
        # cleaning
        delete(self.grp1,self.grp2, self.grp3)

suite = unittest.TestLoader().loadTestsFromTestCase(testCase_nodesAndAttributes)
unittest.TextTestRunner(verbosity=2).run(suite)

     
import sys, os, inspect, unittest
from testingutils import setupUnittestModule
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
        
        self.light = spotLight()
        self.newobjs = []

    def tearDown(self):
        # cleaning
        delete(self.grp1,self.grp2, self.grp3, self.light, *self.newobjs )
        
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
    def test06_instances(self):
        self.assert_( self.sphere1.isInstanced() )   
        self.assert_( self.sphere1.isInstanceOf( self.sphere3 ) )   
    
    def test_parentsAndChildren(self):
        shape = self.sphere1.getShape()
        self.assertEqual( shape, self.sphere1.childAtIndex(0) )
        shape.hasParent( self.sphere1 )
        self.assert_( shape.hasParent(self.sphere1) )
        self.assert_( self.sphere1.hasChild(shape) )
        
    
    def test07_units(self):
        startLinear = currentUnit( q=1, linear=1)
        
        #cam = PyNode('persp')
        # change units from default
        currentUnit(linear='meter')
        
        testPairs = [ ('persp.translate', 'getTranslation', 'setTranslation', datatypes.Vector([3.0,2.0,1.0]) ),  # Distance datatypes.Vector
                      ('persp.shutterAngle' , 'getShutterAngle', 'setShutterAngle', 144.0 ),  # Angle
                      ('persp.verticalShake' , 'getVerticalShake', 'setVerticalShake', 1.0 ),  # Unitless
                      ('persp.focusDistance', 'getFocusDistance', 'setFocusDistance', 5.0 ),  # Distance
                      ('%s.penumbraAngle' % self.light, 'getPenumbra', 'setPenumbra', 5.0 ),  # Angle with renamed api method ( getPenumbraAngle --> getPenumbra )
                      
                     ]
        print
        for attrName, getMethodName, setMethodName, realValue in testPairs:
            at = PyNode(attrName)
            node = at.node()
            getter = getattr( node, getMethodName )
            setter = getattr( node, setMethodName )
            print repr(at)
            print "Real Value:", repr(realValue)
            # set attribute using "safe" method
            at.set( realValue )
            # get attribute using wrapped api method
            gotValue = getter()
            print "Got Value:", repr(gotValue)
            # compare
            self.assertEqual( realValue, gotValue )
            
            # set using wrapped api method
            setter( realValue )
            # get attribute using "safe" method
            gotValue = at.get()
            # compare
            self.assertEqual( realValue, gotValue )
        
        # reset units
        currentUnit(linear=startLinear)
    
    def test_components(self):
        import pymel.examples.setVertexColor
        pymel.examples.setVertexColor.doIt( self.sphere1 )

    def test_examples(self):
        import pymel.examples.example1
        import pymel.examples.example2
        
    def test_classCreation(self):
        self.newobjs.append( Joint() )
        self.newobjs.append( Transform() )


class testCase_listHistory(unittest.TestCase):

    def setUp(self):
        self.sphere1, self.sphere1Maker = polySphere()
        self.sphere1Shape = self.sphere1.getShape()
        self.cube1 = polyCube()[0]
        self.cube1Shape = self.cube1.getShape()
        
        # Delete cube's construction history
        delete(self.cube1, ch=1)
        
        # Connect sphere up to cube
        self.sphere1Shape.outMesh >> self.cube1Shape.inMesh
        
        self.justSphereShape = set([self.sphere1Shape])
        self.justPolySphere = set([self.sphere1Maker])
        self.justCubeShape = set([self.cube1Shape])
        self.polySphereAndShape = self.justSphereShape | self.justPolySphere
        self.polySphereAndShapeAndCubeShape = self.polySphereAndShape | self.justCubeShape
        self.shapes = self.justSphereShape | self.justCubeShape

    def tearDown(self):
        # cleaning
        delete(self.sphere1)
        delete(self.cube1)
                
    def test_listHistory(self):
        hist = set(self.sphere1.listHistory())
        self.assertEqual(self.polySphereAndShape, hist)
        
        hist = set(self.cube1.listHistory())
        self.assertEqual(self.polySphereAndShapeAndCubeShape, hist)

    def test_listHistoryType(self):
        hist = set(self.sphere1.listHistory(type='dagNode'))
        self.assertEqual(self.justSphereShape, hist)

        hist = set(self.sphere1.listHistory(type='mesh'))
        self.assertEqual(self.justSphereShape, hist)
        
        hist = set(self.cube1.listHistory(type='dagNode'))
        self.assertEqual(self.shapes, hist)

        hist = set(self.cube1.listHistory(type='mesh'))
        self.assertEqual(self.shapes, hist)
        

    def test_listHistoryExactType(self):        
        hist = set(self.sphere1.listHistory(exactType='dagNode'))
        self.assertEqual(set(), hist)
        
        hist = set(self.sphere1.listHistory(exactType='mesh'))
        self.assertEqual(self.justSphereShape, hist)
        
        hist = set(self.cube1.listHistory(exactType='dagNode'))
        self.assertEqual(set(), hist)
        
        hist = set(self.cube1.listHistory(exactType='mesh'))
        self.assertEqual(self.shapes, hist)        
    
    def test_listFuture(self):
        fut = set(self.sphere1Maker.listFuture())
        self.assertEqual(self.polySphereAndShapeAndCubeShape, fut)
        
    def test_listFutureType(self):
        fut = set(self.sphere1Maker.listFuture(type='dagNode'))
        self.assertEqual(self.shapes, fut)

        fut = set(self.sphere1Maker.listFuture(type='mesh'))
        self.assertEqual(self.shapes, fut)

    def test_listFutureExactType(self):
        fut = set(self.sphere1Maker.listFuture(exactType='dagNode'))
        self.assertEqual(set(), fut)

        fut = set(self.sphere1Maker.listFuture(exactType='mesh'))
        self.assertEqual(self.shapes, fut)

                
#    def test_transform(self):
#        s, h = polySphere()
#        g = group(s)
#        s.setTranslation( [0,10,20] )
#        s.getTranslation(objectSpace=1)
#        # Result: [0.0, 10.0, 20.0] # 
#        s.getTranslation('object')
#        # Result: [0.0, 10.0, 20.0] # 
#        s.getTranslation(worldSpace=1)
#        # Result: [10.0, 10.0, 20.0] # 
#        s.getTranslation('world')
#        # Result: [10.0, 10.0, 20.0] # 


#suite = unittest.TestLoader().loadTestsFromTestCase(testCase_nodesAndAttributes)
#suite.addTest(unittest.TestLoader().loadTestsFromTestCase(testCase_listHistory))
#unittest.TextTestRunner(verbosity=2).run(suite)
setupUnittestModule(__name__)


     
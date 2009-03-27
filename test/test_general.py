import sys, os, inspect, unittest
#from testingutils import setupUnittestModule
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
        
        currentTime( 1 )
        setKeyframe( self.light.intensity )
        currentTime( 10 )
        self.light.intensity.set(10)
        setKeyframe( self.light.intensity )
        currentTime( 1 )

        self.anim = self.light.intensity.inputs()[0]
        
        self.newobjs = []
        
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
        
        self.sphere2 | self.grp1
        # Should now have grp2 | sphere2 | grp1 | cube1
        self.assertEqual(self.cube1.getParent(0), self.cube1)
        self.assertEqual(self.cube1.getParent(generations=1), self.grp1)
        self.assertEqual(self.cube1.getParent(2), self.sphere2)
        self.assertEqual(self.cube1.getParent(generations=3), self.grp2)
        self.assertEqual(self.cube1.getParent(-1), self.grp2)
        self.assertEqual(self.cube1.getParent(generations=-2), self.sphere2)
        self.assertEqual(self.cube1.getParent(-3), self.grp1)
        self.assertEqual(self.cube1.getParent(generations=-4), self.cube1)
        self.assertEqual(self.cube1.getParent(-5), None)
        self.assertEqual(self.cube1.getParent(generations=4), None)
        self.assertEqual(self.cube1.getParent(-63), None)
        self.assertEqual(self.cube1.getParent(generations=32), None)
    
    def test07_units(self):
        startLinear = currentUnit( q=1, linear=1)
        startAngular = currentUnit( q=1, angle=1)
        startTime = currentUnit( q=1, time=1)
        #cam = PyNode('persp')
        
        # change to units that differ from api internal units
        
        currentUnit(linear='meter')
        currentUnit(angle='deg')
        currentUnit(time='120fps')
        
        testPairs = [ ('persp.translate', 'getTranslation', 'setTranslation', datatypes.Vector([3.0,2.0,1.0]) ),  # Distance Vector
                      ('persp.shutterAngle' , 'getShutterAngle', 'setShutterAngle', 144.0 ),  # Angle
                      ('persp.verticalFilmAperture' , 'getVerticalFilmAperture', 'setVerticalFilmAperture', 2.0 ),  # Unitless
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
        
        
        self.assert_( self.anim.keyTimeValue[1].keyTime.get() == self.anim.getTime(1) )
        self.anim.setTime(1, 5.0)
        self.assert_( self.anim.keyTimeValue[1].keyTime.get() == self.anim.getTime(1) )
        # reset units
        currentUnit(linear=startLinear)
        currentUnit(angle=startAngular)
        currentUnit(time=startTime)
    
    def test_components(self):
        import pymel.examples.setVertexColor
        pymel.examples.setVertexColor.doIt( self.sphere1 )

    def test_examples(self):
        import pymel.examples.example1
        import pymel.examples.example2
        
    def test_classCreation(self):
        self.newobjs.append( Joint() )
        self.newobjs.append( Transform() )


     
    def test_transform_translation(self):
        SCENE.persp.setTranslation( [10,20,30], 'world')

        self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([10.0, 20.0, 30.0]) )
        SCENE.persp.setTranslation( [1,2,3], 'world', relative=1)

        self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([11.0, 22.0, 33.0]) )
        
        if mayahook.Version.current > mayahook.Version.v85sp1:
            undo()
            self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([10.0, 20.0, 30.0]) )

    def test_transform_scale(self):

        SCENE.persp.setScale( [10,20,30] )

        self.assert_( SCENE.persp.getScale() == [10.0, 20.0, 30.0] )
        SCENE.persp.setScale( [1,2,3], relative=1)

        self.assert_( SCENE.persp.getScale() == [10.0, 40.0, 90.0] )
        
        if mayahook.Version.current > mayahook.Version.v85sp1:
            undo()
            self.assert_( SCENE.persp.getScale() == [10.0, 20.0, 30.0] )

    def test_transform_rotation(self):
        SCENE.persp.setRotation( [10,20,0], 'world')
        print repr( SCENE.persp.getRotation( 'world' ) )
        self.assert_( SCENE.persp.getRotation( 'world' ).isEquivalent( datatypes.EulerRotation([10.0, 20.0, 0.0])) )
        SCENE.persp.setRotation( [0,90,0], 'world', relative=1)

        self.assert_( SCENE.persp.getRotation( 'world' ).isEquivalent( datatypes.EulerRotation([10.0, 110.0, 0.0])) )
        
        if mayahook.Version.current > mayahook.Version.v85sp1:
            undo()
            self.assert_( SCENE.persp.getRotation( 'world' ).isEquivalent( datatypes.EulerRotation([10.0, 20.0, 00.0])) )
        
    def test_immutability(self):

        c1 = polyCube()[0]
        c2 = polyCube()[0]
        
        nodeHash1 = c1.__hash__()
        nodeHash2 = c2.__hash__()
        
        attrHash1 = c1.translate.__hash__()
        attrHash2 = c2.translate.__hash__()
        
        self.assert_ ( nodeHash1 != nodeHash2 )
        self.assert_ ( attrHash1 != attrHash2 )
        
        c1.rename( 'funfun' )
        c2.rename( 'yumyum' )

        self.assert_( nodeHash1 == c1.__hash__() )
        self.assert_( nodeHash2 == c2.__hash__() )
        self.assert_( attrHash1 == c1.translate.__hash__() )
        self.assert_( attrHash2 == c2.translate.__hash__() )
        
        
    def tearDown(self):
        newFile(f=1)
        
class testCase_apiUndo(unittest.TestCase):
    
    def setUp(self):
        
        # reset all undo queues
        cmds.undoInfo(state=0)
        setAttr( 'persp.focalLength', 35 )
        setAttr( 'top.focalLength', 35 )
        factories.apiUndo.flushUndo()
        cmds.undoInfo(state=1)
        
    def test_undo(self):
        self.assert_( len(factories.apiUndo.undo_queue) == 0 )
        
        SCENE.top.setFocalLength(20)
        self.assert_( len(factories.apiUndo.undo_queue) == 1 )
        
        
        undoInfo(stateWithoutFlush=0)#--------------------------------
        
        SCENE.persp.setFocalLength(20)
        self.assert_( len(factories.apiUndo.undo_queue) == 1 )
        
        undoInfo(stateWithoutFlush=1)#--------------------------------
        
        undo() # undo top focal length back to 35
        
        self.assert_( SCENE.top.getFocalLength() == 35.0 )
        self.assert_( SCENE.persp.getFocalLength() == 20.0 )
        
        redo()
        
        self.assert_( SCENE.top.getFocalLength() == 20.0 )
        self.assert_( SCENE.persp.getFocalLength() == 20.0 )
        self.assert_( len(factories.apiUndo.undo_queue) == 1 )
        
        # clear maya's undo queue
        # we override undoInfo in system to flush the cache 
        undoInfo( state=0)
        undoInfo( state=1)  

        self.assert_( len(factories.apiUndo.undo_queue) == 0 )
        
        SCENE.top.setFocalLength(200)
        undo()
        
        self.assert_( SCENE.persp.getFocalLength() == 20.0 )
        self.assert_( SCENE.top.getFocalLength() == 20.0 )
        
        self.assert_( len(factories.apiUndo.undo_queue) == 0 )

#    def tearDown(self):
#        
#        # reset all undo queues
#        cmds.undoInfo(state=0)
#        setAttr( 'persp.focalLength', 35 )
#        setAttr( 'top.focalLength', 35 )
#        factories.apiUndo.flushUndo()
#        cmds.undoInfo(state=1)

    def tearDown(self):
        # cleaning
        newFile(f=1)
        
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
#setupUnittestModule(__name__)

     
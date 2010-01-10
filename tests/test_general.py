import sys, os, inspect, unittest
#from testingutils import setupUnittestModule
from pymel.all import *
import pymel.core.nodetypes as nodetypes
#import pymel
import pymel.internal.factories as _factories
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
#    for funcName in _internal.nodeCommandList:
#        _internal.testNodeCmd( funcName, _internal.cmdlist[funcName], verbose )
#         
#    print "done"
#    #print emptyFunctions



def _makeAllAttrTypes(nodeName):
    res = cmds.sphere(n=nodeName)
    cmds.addAttr(ln='short2Attr',at='short2')
    cmds.addAttr(ln='short2a',p='short2Attr',at='short')
    cmds.addAttr(ln='short2b',p='short2Attr',at='short')
    
    cmds.addAttr(ln='short3Attr',at='short3')
    cmds.addAttr(ln='short3a',p='short3Attr',at='short')
    cmds.addAttr(ln='short3b',p='short3Attr',at='short')
    cmds.addAttr(ln='short3c',p='short3Attr',at='short')
    
    cmds.addAttr(ln='long2Attr',at='long2')
    cmds.addAttr(ln='long2a',p='long2Attr',at='long')
    cmds.addAttr(ln='long2b',p='long2Attr',at='long')
    
    cmds.addAttr(ln='long3Attr',at='long3')
    cmds.addAttr(ln='long3a',p='long3Attr',at='long')
    cmds.addAttr(ln='long3b',p='long3Attr',at='long')
    cmds.addAttr(ln='long3c',p='long3Attr',at='long')
    
    cmds.addAttr(ln='float2Attr',at='float2')
    cmds.addAttr(ln='float2a',p='float2Attr',at="float")
    cmds.addAttr(ln='float2b',p='float2Attr',at="float")
    
    cmds.addAttr(ln='float3Attr',at='float3')
    cmds.addAttr(ln='float3a',p='float3Attr',at="float")
    cmds.addAttr(ln='float3b',p='float3Attr',at="float")
    cmds.addAttr(ln='float3c',p='float3Attr',at="float")
    
    cmds.addAttr(ln='double2Attr',at='double2')
    cmds.addAttr(ln='double2a',p='double2Attr',at='double')
    cmds.addAttr(ln='double2b',p='double2Attr',at='double')
    
    cmds.addAttr(ln='double3Attr',at='double3')
    cmds.addAttr(ln='double3a',p='double3Attr',at='double')
    cmds.addAttr(ln='double3b',p='double3Attr',at='double')
    cmds.addAttr(ln='double3c',p='double3Attr',at='double')
    
    cmds.addAttr(ln='Int32ArrayAttr',dt='Int32Array')
    cmds.addAttr(ln='doubleArrayAttr',dt='doubleArray')
    cmds.addAttr(ln='pointArrayAttr',dt='pointArray')
    cmds.addAttr(ln='vectorArrayAttr',dt='vectorArray')
    
    cmds.addAttr(ln='stringArrayAttr',dt='stringArray')
    cmds.addAttr(ln='stringAttr',dt="string")
    cmds.addAttr(ln='matrixAttr',dt="matrix")
    
    # non numeric
    cmds.addAttr(ln='sphereAttr',dt='sphere')
    cmds.addAttr(ln='coneAttr',dt='cone')
    cmds.addAttr(ln='meshAttr',dt='mesh')
    cmds.addAttr(ln='latticeAttr',dt='lattice')
    cmds.addAttr(ln='spectrumRGBAttr',dt='spectrumRGB')
    cmds.addAttr(ln='reflectanceRGBAttr',dt='reflectanceRGB')
    cmds.addAttr(ln='componentListAttr',dt='componentList')
    cmds.addAttr(ln='attrAliasAttr',dt='attributeAlias')
    cmds.addAttr(ln='curveAttr',dt='nurbsCurve')
    cmds.addAttr(ln='surfaceAttr',dt='nurbsSurface')
    cmds.addAttr(ln='trimFaceAttr',dt='nurbsTrimface')
    cmds.addAttr(ln='polyFaceAttr',dt='polyFaces')
    
def test_maya_setAttr():
    """
    sanity check: make sure we know how to set and get attributes via maya's 
    setAttr.  this serves mostly to document all the inconsistencies in setAttr
    so that we can sort them out in our own wrap.  it will also alert us to
    any changes that Autodesk makes.
    """

    _makeAllAttrTypes('node')
    
    # compound
    cmds.setAttr( 'node.short2Attr', 1, 2 )
    assert cmds.getAttr( 'node.short2Attr' )        == [(1, 2)]
    
    cmds.setAttr( 'node.short3Attr', 1, 2, 3 )
    assert cmds.getAttr( 'node.short3Attr' )        == [(1, 2,3)]
    
    cmds.setAttr( 'node.long2Attr', 1, 2 )
    assert cmds.getAttr( 'node.long2Attr' )         == [(1, 2)]
    
    cmds.setAttr( 'node.long3Attr', 1, 2, 3 )
    assert cmds.getAttr( 'node.long3Attr' )         == [(1, 2,3)]
    
    cmds.setAttr( 'node.float2Attr', 1, 2 )
    assert cmds.getAttr( 'node.float2Attr' )        == [(1.0, 2.0)]
    
    cmds.setAttr( 'node.float3Attr', 1, 2, 3 )
    assert cmds.getAttr( 'node.float3Attr' )        == [(1.0, 2.0, 3.0)]
    
    cmds.setAttr( 'node.double2Attr', 1, 2 )
    assert cmds.getAttr( 'node.double2Attr' )       == [(1.0, 2.0)]
    
    cmds.setAttr( 'node.double3Attr', 1, 2, 3 )
    assert cmds.getAttr( 'node.double3Attr' )       == [(1.0, 2.0, 3.0)]
    
    # array
    cmds.setAttr( 'node.Int32ArrayAttr', (1, 2, 3, 4), type='Int32Array' )
    assert cmds.getAttr( 'node.Int32ArrayAttr' ) == [1, 2, 3, 4]
    
    cmds.setAttr( 'node.doubleArrayAttr', (1, 2, 3, 4), type='doubleArray' )
    assert cmds.getAttr( 'node.doubleArrayAttr' )   == [1.0, 2.0, 3.0, 4.0]
    
    # complex array
    cmds.setAttr( 'node.pointArrayAttr', 2, (1,2,3,4), "", (1,2,3,4), type='pointArray' )
    assert cmds.getAttr( 'node.pointArrayAttr' )    == [(1.0, 2.0, 3.0, 4.0), (1.0, 2.0, 3.0, 4.0)]
    
    cmds.setAttr( 'node.vectorArrayAttr', 2, (1,2,3), "", (1,2,3), type='vectorArray' )
    assert cmds.getAttr( 'node.vectorArrayAttr' )   == [1.0, 2.0, 3.0, 1.0, 2.0, 3.0]
    
    # string array
    cmds.setAttr( 'node.stringArrayAttr', 3, 'one', 'two', 'three', type='stringArray' )
    assert cmds.getAttr( 'node.stringArrayAttr' )   == [u'one', u'two', u'three'] 
    
    cmds.setAttr( 'node.stringAttr', 'one', type='string' )
    assert cmds.getAttr( 'node.stringAttr' )        == u'one'
    
    # non-numeric: can't get
    cmds.setAttr( 'node.sphereAttr', 1.0, type='sphere' )
    #assert cmds.getAttr( 'node.sphereAttr' )        == 1.0
    
    cmds.setAttr( 'node.coneAttr', 45, 45, type='cone' )
    #assert cmds.getAttr( 'node.coneAttr' )        == 1.0
    
    cmds.setAttr( 'node.reflectanceRGBAttr', 1,1,1, type='reflectanceRGB' )
    #assert cmds.getAttr( 'node.reflectanceRGBAttr' )        == 1.0
    # TODO : finish non-numeric
    
def test_setAttr():

    _makeAllAttrTypes('node2')
    for typ, val in [
        ('short2',  (1,2)),
        ('short3',  (1,2,3)),
        ('long2',   (1,2)),
        ('long3',   (1,2,3)),
        ('float2',  (1.0,2.0)),
        ('float3',  (1.0,2.0,3.0)),
        ('double2', (1.0,2.0)),
        ('double3', datatypes.Vector(1.0,2.0,3.0)),
        
        ('Int32Array', [1,2,3,4]),
        ('doubleArray', [1,2,3,4]),
        
        ('vectorArray', [datatypes.Vector([1,2,3]), datatypes.Vector([1,2,3])] ),
        ('pointArray', [datatypes.Point([1,2,3]), datatypes.Point([1,2,3])] ),
        
        ('stringArray', ['one', 'two', 'three']),
        ('string', 'one') ]:
        
        def testSetAttr(*args):
            at = 'node2.' + typ + 'Attr'
            setAttr(at, val)
            newval = getAttr(at)
            assert newval == val, "setAttr %s: returned value %r is not equal to input value %r" % (typ, newval, val)
        
        testSetAttr.__name__ = 'test_setAttr_' + typ
        testSetAttr.description = 'test_setAttr_' + typ
        #print typ
        #testSetAttr()
        yield testSetAttr
            
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
        
        cmds.aliasAttr( 'myalias', self.sphere1.name() + '.scaleX' )
        
    def test_attribute_parent_equality(self):
        self.assertEqual( self.sphere2.t.tx.parent(), self.sphere2.t )
        
    def test_attribute_duplicate_inequality(self):
        self.assert_( self.sphere1.t != self.sphere2.t )
        
    def test_attribute_instance_equality(self):
        self.assertEqual( self.sphere1.t, self.sphere3.t )
    
    def test_attribute_cascading(self):
        self.sphere1.primaryVisibility.set(1)
        shape = self.sphere1.getShape()
        self.assertEqual( self.sphere1.primaryVisibility, shape.primaryVisibility )
     
    def test_attribute_aliases(self):
        self.assert_( isinstance(PyNode(self.sphere1.name() + '.myalias'), Attribute ) )
        self.assert_( isinstance(self.sphere1.attr('myalias'), Attribute) )
        res1 = self.sphere1.listAttr(alias=1)
        res2 = self.sphere1.listAliases()
        self.assertEqual( res1[0], res2[0][1] )
        
    def test_pmcmds_objectErrors(self):
        self.assertRaises( MayaSubObjectError, setAttr, 'foo.bar', 0 )
        self.assertRaises( MayaSubObjectError, getAttr, 'foo.bar' )
        self.assertRaises( MayaNodeError, listConnections, 'foobar' )
        
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
    
#    def test_components(self):
#        import pymel.examples.setVertexColor
#        pymel.examples.setVertexColor.doIt( self.sphere1 )
#
#    def test_examples(self):
#        import pymel.examples.example1
#        import pymel.examples.example2
        
    def test_classCreation(self):
        self.newobjs.append( Joint() )
        self.newobjs.append( Transform() )


     
    def test_transform_translation(self):
        SCENE.persp.setTranslation( [10,20,30], 'world')

        self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([10.0, 20.0, 30.0]) )
        SCENE.persp.setTranslation( [1,2,3], 'world', relative=1)

        self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([11.0, 22.0, 33.0]) )
        
        undo()
        self.assert_( SCENE.persp.getTranslation( 'world' ) == datatypes.Vector([10.0, 20.0, 30.0]) )

    def test_transform_scale(self):

        SCENE.persp.setScale( [10,20,30] )

        self.assert_( SCENE.persp.getScale() == [10.0, 20.0, 30.0] )
        SCENE.persp.setScale( [1,2,3], relative=1)

        self.assert_( SCENE.persp.getScale() == [10.0, 40.0, 90.0] )
        
        undo()
        self.assert_( SCENE.persp.getScale() == [10.0, 20.0, 30.0] )

    def test_transform_rotation(self):
        SCENE.persp.setRotation( [10,20,0], 'world')
        print repr( SCENE.persp.getRotation( 'world' ) )
        self.assert_( SCENE.persp.getRotation( 'world' ).isEquivalent( datatypes.EulerRotation([10.0, 20.0, 0.0])) )
        SCENE.persp.setRotation( [0,90,0], 'world', relative=1)

        self.assert_( SCENE.persp.getRotation( 'world' ).isEquivalent( datatypes.EulerRotation([10.0, 110.0, 0.0])) )

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
        
    def test_pynode_instantiation(self):
        plug = SCENE.persp.__apimfn__().findPlug('translateX')
        obj = SCENE.persp.__apimobject__()
        dag = SCENE.persp.__apimdagpath__()
        PyNode(obj).name()
        PyNode(plug).name()
        PyNode(dag).name()
        
              
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

class testCase_duplicateShape(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.poly = polyCube(name='singleShapePoly')[0]
        self.curve = circle(name='singleShapeCurve')[0]
        tempShapeTransform = polyCone()[0]
        self.subd = polyToSubdiv(tempShapeTransform,
                                 constructionHistory=False,
                                 name='singleShapeSubd')[0]
        delete(tempShapeTransform)
        #self.noShape = createNode('transform', name='noShapeTransform')
        
        #one transform, multiple shapes
        self.multiShape = polyCube(name='multiShape')[0]
        self.multiShape.getShape().rename('multiShapePolyShape')
        tempShapeTransform = polyToSubdiv(self.multiShape,
                                          constructionHistory=False,
                                          name='multiShapeSubd')[0]
        parent(tempShapeTransform.getShape(), self.multiShape, shape=True,
               addObject=True, relative=True)
        delete(tempShapeTransform)
        tempShapeTransform = circle(name='multiShapeCurve')[0]
        parent(tempShapeTransform.getShape(), self.multiShape, shape=True,
               addObject=True, relative=True)
        delete(tempShapeTransform)

    def tearDown(self):
        for node in (self.multiShape, self.poly, self.curve, self.subd):
            delete(node)
            
    def test_singleShapes(self):
        for shapeTransform in (self.poly, self.curve, self.subd):
            self.assertEqual(len(shapeTransform.getChildren(shapes=1)), 1)
            self.assertRaises(TypeError, duplicate, shapeTransform, addShape=True)
            self.assertEqual(len(shapeTransform.getChildren(shapes=1)), 1)
            origShape = shapeTransform.getShape()
            shapeDup = duplicate(origShape, addShape=True)
            self.assertEqual(len(shapeTransform.getChildren(shapes=1)), 2)
            self.assertEqual(len(shapeDup), 1)
            shapeDup = shapeDup[0]
            self.assertDupeShape(origShape, shapeDup)
            
    def test_multiShape(self):
        origShapes = self.multiShape.getChildren(shapes=1)
        oldNumChildren = len(origShapes)
        self.assertRaises(TypeError, duplicate, self.multiShape, addShape=True)
        self.assertEqual(len(self.multiShape.getChildren(shapes=1)),
                             oldNumChildren)
        for origShape in origShapes:
            shapeDup = duplicate(origShape, addShape=True)
            self.assertEqual(len(self.multiShape.getChildren(shapes=1)),
                             oldNumChildren + 1)
            oldNumChildren += 1
            self.assertEqual(len(shapeDup), 1)
            shapeDup = shapeDup[0]
            self.assertDupeShape(origShape, shapeDup)
    
    def assertDupeShape(self, origShape, shapeDup):
            self.assertTrue(shapeDup.__class__ == origShape.__class__)
            
            # As of Maya 2009, shapeCompare doesn't handle subdivs, and always
            #    returns 1 for curves
            if not isinstance(origShape, (Subdiv, NurbsCurve)):
                if shapeCompare(origShape, shapeDup) != 0:
                    self.fail("shapes do not compare equal: %r, %r)" %
                              (origShape, shapeDup))
            self.assertFalse(origShape.isInstanceOf(shapeDup))

class test_PyNodeWraps(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def assertPyNode(self, obj, nodeType=PyNode):
        self.assert_(isinstance(obj, nodeType),
                     '%r was not a %s object' % (obj, nodeType.__name__))
        
    def assertPyNodes(self, objs, nodeType=PyNode):
        for obj in objs:
            self.assertPyNode(obj, nodeType)
                        
    def test_addAttr_QParent(self):
        cmds.polyCube()
        cmds.addAttr( longName='sampson', numberOfChildren=5, attributeType='compound' )
        cmds.addAttr( longName='homeboy', attributeType='matrix', parent='sampson' )
        cmds.addAttr( longName='midge', attributeType='message', parent='sampson' )
        cmds.addAttr( longName='damien', attributeType='double', parent='sampson' )
        cmds.addAttr( longName='elizabeth', attributeType='double', parent='sampson' )
        cmds.addAttr( longName='sweetpea', attributeType='double', parent='sampson' )
        node = cmds.ls(sl=1)[0]
        self.assertPyNode(addAttr(node + '.sweetpea', q=1, parent=1), Attribute)
        
    def test_skinCluster_QGeometry(self):
        cube = cmds.polyCube()[0]
        j1 = cmds.joint(p=(0,0,-1))
        cmds.joint(p=(0,0,1))
        skin = skinCluster(cube, j1)[0]
        self.assertPyNodes(skin.getGeometry(), DependNode)
        
    def test_addDynamic(self):
        # Create an emitter
        cmds.emitter( pos=(0, 0, 0), type='omni', r=100, sro=0, nuv=0, cye='none', cyi=1, spd=1, srn=0, nsp=1, tsp=0, mxd=0, mnd=0, dx=1, dy=0, dz=0, sp=0 )
        # Result: emitter1 #
        
        # Get the emitter to emit particles
        cmds.particle()
        # Result: particle2
        cmds.connectDynamic( 'particle1', em='emitter1' )
        
        # Create a particle to use as the source of the emitter
        cmds.particle( p=((6.0, 0, 7.0), (6.0, 0, 2.0)), c=1 )
        # Result: particle2
        
        # Use particle2 as a source of the emitter
        self.assertPyNodes(addDynamic( 'emitter1', 'particle2' ), PyNode)

    def test_addPP(self):
        cmds.emitter( n='myEmitter1' )
        cmds.particle( n='myParticle1' )
        cmds.connectDynamic( 'myParticle1', em='myEmitter1' )
        cmds.select( 'myParticle1' )
        cmds.emitter( n='myEmitter2' )
        cmds.particle( n='myParticle2' )
        cmds.connectDynamic( 'myParticle2', em='myEmitter2' )
        self.assertPyNodes(addPP( 'myEmitter2', atr='rate' ))
    
    def test_animLayer(self):
        self.assertEqual(animLayer(q=1, root=1), None)
        cmds.animLayer("layer1")
        rootLayer = animLayer(q=1, root=1)
        self.assertPyNode(rootLayer)
        self.assertEqual(animLayer(rootLayer, q=1, parent=1), None)
        self.assertPyNode(animLayer("layer1", q=1, parent=1))
        self.assertEqual(animLayer("layer1", q=1, children=1), [])
        self.assertPyNodes(animLayer(rootLayer, q=1, children=1))
        self.assertEqual(animLayer("layer1", q=1, attribute=1), [])
        self.assertEqual(animLayer("layer1", q=1,  blendNodes=1), [])
        cmds.animLayer("layer1", e=1, attribute=('persp.tx', 'persp.ry'))
        self.assertPyNodes(animLayer("layer1", q=1, attribute=1), Attribute)
        cmds.select('persp')
        self.assertPyNodes(animLayer(q=1, bestAnimLayer=1))
        self.assertEqual(animLayer("layer1", q=1,  animCurves=1), [])
        cmds.setKeyframe('persp', animLayer='layer1')
        self.assertPyNodes(animLayer("layer1", q=1,  animCurves=1))
        self.assertEqual(animLayer('layer1', q=1, bac=1), [])
        cmds.setKeyframe('persp', animLayer='BaseAnimation')
        self.assertPyNodes(animLayer('layer1', q=1, bac=1))
        self.assertPyNodes(animLayer("layer1", q=1,  blendNodes=1))
        self.assertEqual(animLayer("persp.tz", q=1,  bestLayer=1), None)
        self.assertPyNode(animLayer("persp.tx", q=1,  bestLayer=1))
        cmds.select('side')
        self.assertEqual(animLayer(q=1,  affectedLayers=1), [])
        cmds.select('persp')
        self.assertPyNodes(animLayer(q=1,  affectedLayers=1))
        
for cmdName in ('''aimConstraint geometryConstraint normalConstraint
                   orientConstraint parentConstraint pointConstraint
                   pointOnPolyConstraint poleVectorConstraint
                   scaleConstraint tangentConstraint''').split():
    melCmd = getattr(cmds, cmdName, None)
    if not melCmd: continue
    pyCmd = globals()[cmdName]
    def testConstraint(self):
        cmds.polyCube(name='cube1')
        cmds.circle(name='circle1')
        constr = melCmd( 'circle1', 'cube1')[0]
        self.assertPyNodes(pyCmd(constr, q=1, targetList=1))
        self.assertPyNodes(pyCmd(constr, q=1, weightAliasList=1), Attribute)
        if 'worldUpObject' in _factories.cmdlist[cmdName]['flags']:
            self.assertEqual(pyCmd(constr, q=1, worldUpObject=1), None)
            cmds.polySphere(name='sphere1')
            melCmd(constr, e=1, worldUpType='object', worldUpObject='sphere1')
            self.assertPyNode(pyCmd(constr, q=1, worldUpObject=1))
    testName = "test_" + cmdName
    testConstraint.__name__ = testName
    setattr(test_PyNodeWraps, testName, testConstraint)
        
        
#suite = unittest.TestLoader().loadTestsFromTestCase(testCase_nodesAndAttributes)
#suite.addTest(unittest.TestLoader().loadTestsFromTestCase(testCase_listHistory))
#unittest.TextTestRunner(verbosity=2).run(suite)
#setupUnittestModule(__name__)

     
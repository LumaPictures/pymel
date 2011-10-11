import sys, os, inspect, unittest
#from testingutils import setupUnittestModule
from pymel.core import *
import pymel.core as pm 
import pymel.versions as versions
import pymel.internal.factories as factories
import pymel.internal.pmcmds as pmcmds
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
#import pymel
#import maya.cmds as cmds

# Name mangling happens if we try to use __name inside a UnitTest class...
from maya.app.commands import __makeStubFunc as _makeStubFunc
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


# Todo - add missing attribute types (ie, message, boolean, datatype forms of
# double2, float3, etc

def _makeAllAttrTypes(nodeName):
    cmds.sphere(n=nodeName)
    
    attributeTypesToNames = {}
    dataTypesToNames = {}
    namesToType = {}
    
    def doAttrAdd(**kwargs):
        name = kwargs.get('ln', kwargs.get('longName'))
        dt = kwargs.get('dt', kwargs.get('dataType'))

        if dt is not None:
            dataTypesToNames.setdefault(dt, []).append(name)
            namesToType[name] = ('dt', dt)
        else:
            at = kwargs.get('at', kwargs.get('attributeType'))
            if at is None:
                at = 'double'
            attributeTypesToNames.setdefault(dt, []).append(name)
            namesToType[name] = ('at', at)
        cmds.addAttr(**kwargs)
    
    # compound numeric types    
    doAttrAdd(ln='short2Attr',at='short2')
    doAttrAdd(ln='short2a',p='short2Attr',at='short')
    doAttrAdd(ln='short2b',p='short2Attr',at='short')
    
    doAttrAdd(ln='short3Attr',at='short3')
    doAttrAdd(ln='short3a',p='short3Attr',at='short')
    doAttrAdd(ln='short3b',p='short3Attr',at='short')
    doAttrAdd(ln='short3c',p='short3Attr',at='short')
    
    doAttrAdd(ln='long2Attr',at='long2')
    doAttrAdd(ln='long2a',p='long2Attr',at='long')
    doAttrAdd(ln='long2b',p='long2Attr',at='long')
    
    doAttrAdd(ln='long3Attr',at='long3')
    doAttrAdd(ln='long3a',p='long3Attr',at='long')
    doAttrAdd(ln='long3b',p='long3Attr',at='long')
    doAttrAdd(ln='long3c',p='long3Attr',at='long')
    
    doAttrAdd(ln='float2Attr',at='float2')
    doAttrAdd(ln='float2a',p='float2Attr',at="float")
    doAttrAdd(ln='float2b',p='float2Attr',at="float")
    
    doAttrAdd(ln='float3Attr',at='float3')
    doAttrAdd(ln='float3a',p='float3Attr',at="float")
    doAttrAdd(ln='float3b',p='float3Attr',at="float")
    doAttrAdd(ln='float3c',p='float3Attr',at="float")
    
    doAttrAdd(ln='double2Attr',at='double2')
    doAttrAdd(ln='double2a',p='double2Attr',at='double')
    doAttrAdd(ln='double2b',p='double2Attr',at='double')
    
    doAttrAdd(ln='double3Attr',at='double3')
    doAttrAdd(ln='double3a',p='double3Attr',at='double')
    doAttrAdd(ln='double3b',p='double3Attr',at='double')
    doAttrAdd(ln='double3c',p='double3Attr',at='double')
    
    # Array Attributes 
    
    doAttrAdd(ln='Int32ArrayAttr',dt='Int32Array')
    doAttrAdd(ln='doubleArrayAttr',dt='doubleArray')
    doAttrAdd(ln='pointArrayAttr',dt='pointArray')
    doAttrAdd(ln='vectorArrayAttr',dt='vectorArray')
    
    doAttrAdd(ln='stringArrayAttr',dt='stringArray')
    doAttrAdd(ln='stringAttr',dt="string")

    # Matrix
    
    doAttrAdd(ln='matrixAttr',dt="matrix")
    
    # non numeric
    doAttrAdd(ln='sphereAttr',dt='sphere')
    doAttrAdd(ln='coneAttr',dt='cone')
    doAttrAdd(ln='meshAttr',dt='mesh')
    doAttrAdd(ln='latticeAttr',dt='lattice')
    doAttrAdd(ln='spectrumRGBAttr',dt='spectrumRGB')
    doAttrAdd(ln='reflectanceRGBAttr',dt='reflectanceRGB')
    doAttrAdd(ln='componentListAttr',dt='componentList')
    doAttrAdd(ln='attrAliasAttr',dt='attributeAlias')
    doAttrAdd(ln='curveAttr',dt='nurbsCurve')
    doAttrAdd(ln='surfaceAttr',dt='nurbsSurface')
    doAttrAdd(ln='trimFaceAttr',dt='nurbsTrimface')
    doAttrAdd(ln='polyFaceAttr',dt='polyFaces')
    
    return attributeTypesToNames, dataTypesToNames, namesToType
    
class testCase_mayaSetAttr(unittest.TestCase):
    """
    sanity check: make sure we know how to set and get attributes via maya's 
    setAttr.  this serves mostly to document all the inconsistencies in setAttr
    so that we can sort them out in our own wrap.  it will also alert us to
    any changes that Autodesk makes.
    """
    
    def setUp(self):
        _makeAllAttrTypes('node')
    
    def test_short2(self):
        # compound
        cmds.setAttr( 'node.short2Attr', 1, 2 )
        assert cmds.getAttr( 'node.short2Attr' )        == [(1, 2)]
        
    def test_short3(self):
        cmds.setAttr( 'node.short3Attr', 1, 2, 3 )
        assert cmds.getAttr( 'node.short3Attr' )        == [(1, 2,3)]
    
    def test_long2(self):
        cmds.setAttr( 'node.long2Attr', 1, 2 )
        assert cmds.getAttr( 'node.long2Attr' )         == [(1, 2)]
    
    def test_long3(self):
        cmds.setAttr( 'node.long3Attr', 1, 2, 3 )
        assert cmds.getAttr( 'node.long3Attr' )         == [(1, 2,3)]
        
    def test_float2(self):
        cmds.setAttr( 'node.float2Attr', 1, 2 )
        assert cmds.getAttr( 'node.float2Attr' )        == [(1.0, 2.0)]
    
    def test_float(self):
        cmds.setAttr( 'node.float3Attr', 1, 2, 3 )
        assert cmds.getAttr( 'node.float3Attr' )        == [(1.0, 2.0, 3.0)]
        
    def test_double2(self):
        cmds.setAttr( 'node.double2Attr', 1, 2 )
        assert cmds.getAttr( 'node.double2Attr' )       == [(1.0, 2.0)]
        
    def test_double3(self):
        cmds.setAttr( 'node.double3Attr', 1, 2, 3 )
        assert cmds.getAttr( 'node.double3Attr' )       == [(1.0, 2.0, 3.0)]

    def test_int32Array(self):
        # array
        cmds.setAttr( 'node.Int32ArrayAttr', (1, 2, 3, 4), type='Int32Array' )
        assert cmds.getAttr( 'node.Int32ArrayAttr' ) == [1, 2, 3, 4]
        
    def test_doubleArray(self):
        cmds.setAttr( 'node.doubleArrayAttr', (1, 2, 3, 4), type='doubleArray' )
        assert cmds.getAttr( 'node.doubleArrayAttr' )   == [1.0, 2.0, 3.0, 4.0]
    
    def test_pointArray(self):
        if versions.current() < versions.v2011:
            # complex array
            cmds.setAttr( 'node.pointArrayAttr', 2, (1,2,3,4), "", (1,2,3,4), type='pointArray' )
            assert cmds.getAttr( 'node.pointArrayAttr' )    == [(1.0, 2.0, 3.0, 4.0), (1.0, 2.0, 3.0, 4.0)]
        else:
            cmds.setAttr( 'node.pointArrayAttr', 2, (1,2,3,4), (1,2,3,4), type='pointArray' )
            assert cmds.getAttr( 'node.pointArrayAttr' )    == [(1.0, 2.0, 3.0, 4.0), (1.0, 2.0, 3.0, 4.0)]
            
    def test_vectorArray(self):
        if versions.current() < versions.v2011:
            cmds.setAttr( 'node.vectorArrayAttr', 2, (1,2,3), "", (1,2,3), type='vectorArray' )
            assert cmds.getAttr( 'node.vectorArrayAttr' )   == [1.0, 2.0, 3.0, 1.0, 2.0, 3.0]
        else:
            cmds.setAttr( 'node.vectorArrayAttr', 2, (1,2,3), (1,2,3), type='vectorArray' )
            assert cmds.getAttr( 'node.vectorArrayAttr' )   == [(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)]
    
    def test_stringArray(self):
        # string array
        cmds.setAttr( 'node.stringArrayAttr', 3, 'one', 'two', 'three', type='stringArray' )
        assert cmds.getAttr( 'node.stringArrayAttr' )   == [u'one', u'two', u'three'] 
    
    def test_string(self):
        cmds.setAttr( 'node.stringAttr', 'one', type='string' )
        assert cmds.getAttr( 'node.stringAttr' )        == u'one'
    
    if versions.current() >= versions.v2011:
        def test_matrix(self):
            # matrix
            # Fails in versions < 2011
            cmds.setAttr( 'node.matrixAttr', 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, type='matrix' )
            assert cmds.getAttr( 'node.matrixAttr' )   == [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0] 
    
    def test_sphere(self):
        # non-numeric: can't get
        cmds.setAttr( 'node.sphereAttr', 1.0, type='sphere' )
        #assert cmds.getAttr( 'node.sphereAttr' )        == 1.0
        
    def test_cone(self):
        cmds.setAttr( 'node.coneAttr', 45, 45, type='cone' )
        #assert cmds.getAttr( 'node.coneAttr' )        == 1.0
        
    def test_reflectanceRGB(self):
        cmds.setAttr( 'node.reflectanceRGBAttr', 1,1,1, type='reflectanceRGB' )
        #assert cmds.getAttr( 'node.reflectanceRGBAttr' )        == 1.0
        # TODO : finish non-numeric
    
def test_pymel_setAttr():

    _makeAllAttrTypes('node2')
    for data in [
        ('short2',  (1,2)),
        ('short3',  (1,2,3)),
        ('long2',   (1,2)),
        ('long3',   (1,2,3)),
        ('float2',  (1.0,2.0)),
        ('float3',  (1.0,2.0,3.0)),
        ('double2', (1.0,2.0)),
        ('double3', datatypes.Vector(1.0,2.0,3.0), [1,2,3] ),
        
        ('Int32Array', [1,2,3,4]),
        ('doubleArray', [1,2,3,4]),
        
        ('vectorArray', [datatypes.Vector([1,2,3]), datatypes.Vector([1,0,0])],
                        [[1,2,3], [1,0,0]] ),
        ('pointArray', [datatypes.Point([1,2,3]), datatypes.Point([2,4,6])],
                        [[1,2,3,1], [2,4,6,1]] ),
        
        ('stringArray', ['one', 'two', 'three']),
        ('string', 'one'),
        ('matrix', datatypes.Matrix(),
                        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0] )]:
        typ = data[0]
        mainVal = data[1]
        
        for i, val in enumerate(data[1:]):
            def testSetAttr(*args):
                at = 'node2.' + typ + 'Attr'
                setAttr(at, val)
                newval = getAttr(at)
                assert newval == mainVal, "setAttr %s: returned value %r is not equal to input value %r" % (typ, newval, mainVal)
            
            testSetAttr.__name__ = 'test_setAttr_' + typ + '_' + str(i) 
            testSetAttr.description = testSetAttr.__name__
            #print typ
            #testSetAttr()
            yield testSetAttr,
            
class testCase_enumAttr(unittest.TestCase):
    def setUp(self):
        self.node = cmds.createNode('transform')
        self.attrName = 'testEnum'
        self.attr = '%s.%s' % (self.node, self.attrName)
        cmds.addAttr(self.node, at='enum', longName=self.attrName,
                     enumName='First:Second:Third', keyable=True)
        
    def test_setString(self):
        print "self.attr:", self.attr
        setAttr(self.attr, 'Second')
        self.assertEqual(1, getAttr(self.attr))
        setAttr(self.attr, 'Third', asString=1)
        self.assertEqual(2, getAttr(self.attr))
        self.assertRaises(MayaAttributeEnumError, setAttr, self.attr, 'foo')
            
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
        fromPyNode = pm.PyNode(self.sphere1.name() + '.myalias')
        self.assertTrue( isinstance(fromPyNode, pm.Attribute ) )
        fromAttr = self.sphere1.attr('myalias')
        self.assertTrue( isinstance(fromAttr, pm.Attribute) )
        
        res1 = self.sphere1.listAttr(alias=1)
        res2 = self.sphere1.listAliases()
        self.assertEqual( res1[0], res2[0][1] )
        self.assertEqual(fromPyNode, res1[0])
        self.assertEqual(fromAttr, fromPyNode)

    def test_multi_compound_attribute_aliases(self):
        remap = pm.createNode('remapValue')
        attr = remap.attr('value')[0].value_Position
        attr.setAlias('alfred')
        
        fromPyNode = pm.PyNode(remap.name() + '.alfred')
        self.assertTrue( isinstance(fromPyNode, pm.Attribute ) )
        fromAttr = remap.attr('alfred')
        self.assertTrue( isinstance(fromAttr, pm.Attribute) )
        
        res1 = remap.listAttr(alias=1)
        res2 = remap.listAliases()
        self.assertEqual( res1[0], res2[0][1] )
        self.assertEqual(fromPyNode, res1[0])
        self.assertEqual(fromAttr, fromPyNode)

    def test_pmcmds_objectErrors(self):
        self.assertRaises( MayaAttributeError, setAttr, 'foo.bar', 0 )
        self.assertRaises( MayaAttributeError, getAttr, 'foo.bar' )
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
        self.newobjs.append( nt.Joint() )
        self.newobjs.append( nt.Transform() )


     
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
        #print repr( SCENE.persp.getRotation( 'world' ) )
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
            if not isinstance(origShape, (nt.Subdiv, nt.NurbsCurve)):
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
        skin = pm.skinCluster(cube, j1)
        self.assertPyNodes(skin.getGeometry(), nt.DependNode)
        
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
        
    def test_annotate(self):
        cmds.sphere( name='mySphere' )
        self.assertPyNode(annotate( 'mySphere', tx='my annotation text', p=(5, 6, 5) ))
        
    def test_arclen(self):
        circle(name='curve1')
        self.assertPyNode(arclen('curve1', ch=True))
        self.assertPyNode(arclen('curve1'), float)
        
    def test_arcLengthDimension(self):
        cmds.curve( d=3, p=((-9.3, 0, 3.2), (-4.2, 0, 5.0), (6.0, 0, 8.6), (2.1, 0, -1.9)), k=(0, 0, 0, 1, 2, 2));
        self.assertPyNode(arcLengthDimension( 'curveShape1.u[0.5]' ))
        
    def test_arrayMapper(self):
        particle( p=[(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9)] )
        self.assertPyNode(arrayMapper( target='particle1', destAttr='rampPosition', inputV='ageNormalized', type='ramp' ))
        
    if not cmds.about(batch=1):
        
        def test_art3dPaintCtx(self):
            polyCube()
            polyCube()
            select('pCube1', 'pCube2')
            from maya.mel import eval as mel
            mel("Art3dPaintTool")
            mel("art3dPaintAssignFileTextures color")
            self.assertPyNodes(art3dPaintCtx('art3dPaintContext', q=1, shn=1))
            self.assertPyNodes(art3dPaintCtx('art3dPaintContext', q=1, hnm=1))
        
        def test_artAttrCtx(self):
            polyCube()
            polyCube()
            select('pCube1', 'pCube2')
            if not cmds.artAttrCtx('artAttrCtx1', exists=1):
                cmds.artAttrCtx('artAttrCtx1')
            cmds.setToolTo('artAttrCtx1')
            self.assertPyNodes(artAttrCtx('artAttrCtx1', q=1, paintNodeArray=1))
        
for cmdName in ('''aimConstraint geometryConstraint normalConstraint
                   orientConstraint parentConstraint pointConstraint
                   pointOnPolyConstraint poleVectorConstraint
                   scaleConstraint tangentConstraint''').split():
    melCmd = getattr(cmds, cmdName, None)
    if not melCmd: continue
    pyCmd = globals()[cmdName]
    def constraintTest(self):
        cmds.polyCube(name='cube1')
        cmds.circle(name='circle1')
        constr = melCmd( 'circle1', 'cube1')[0]
        self.assertPyNodes(pyCmd(constr, q=1, targetList=1))
        self.assertPyNodes(pyCmd(constr, q=1, weightAliasList=1), Attribute)
        if 'worldUpObject' in factories.cmdlist[cmdName]['flags']:
            self.assertEqual(pyCmd(constr, q=1, worldUpObject=1), None)
            cmds.polySphere(name='sphere1')
            melCmd(constr, e=1, worldUpType='object', worldUpObject='sphere1')
            self.assertPyNode(pyCmd(constr, q=1, worldUpObject=1))
    testName = "test_" + cmdName
    constraintTest.__name__ = testName
    setattr(test_PyNodeWraps, testName, constraintTest)
    
    # Delete the function from the module level after we're done, so
    # nosetests won't find the "original" non-method function, and
    # try to run it as a test!
    del globals()['constraintTest']
        
class test_commands(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.dependNode = cmds.createNode('displayLayer')
        self.group = cmds.group('persp')
        
    def test_duplicate(self):
        # make sure that we get proper dag nodes, even when the result will contain non-unique names
        self.assert_( duplicate(self.group) )
        
        # ensure it works with depend nodes too
        self.assert_( duplicate(self.dependNode) )
        
class test_plugins(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        if cmds.pluginInfo('Fur', q=1, loaded=1):
            cmds.unloadPlugin('Fur')
            cmds.file(new=1, f=1)
        # Currently, PyNode classes for node types defined in 'default'
        # plugins are always created when pymel starts up, even if the plugin
        # wasn't loaded... so we need to make sure we delete 'FurGlobals' if it
        # was made
        if 'FurGlobals' in nt.__dict__:
            del nt.__dict__['FurGlobals']
        if 'FurGlobals' in nt.__class__.__dict__:
            delattr(nt.__class__, 'FurGlobals')
        # Also, 'unload' pymel.all if present - if it's there, it will cause
        # any new PyNodes to skip lazy loading
        sys.modules.pop('pymel.all', None)
        
    def test01_load(self):
        self.assert_( 'FurGlobals' not in nt.__dict__ )
        loadPlugin('Fur')
        self.assert_( 'FurGlobals' not in nt.__dict__ )
        # lazy loader exists
        self.assert_( 'FurGlobals' in nt.__class__.__dict__ )
        # after accessing, the lazy loader should generate the class
        nt.FurGlobals
        self.assert_( 'FurGlobals' in nt.__dict__ )
        
    def test02_unload(self):
        loadPlugin('Fur')
        unloadPlugin('Fur')
        self.assert_( 'FurGlobals' not in nt.__dict__ )
        # after accessing, the lazy loader should generate the class
        self.assertRaises(AttributeError, getattr, nt, 'FurGlobals')
        self.assert_( 'FurGlobals' not in nt.__dict__ )
        self.assert_( 'FurGlobals' not in nt.__class__.__dict__ )

class test_move(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def test_relativeMove(self):
        cube = pm.polyCube()[0]
        pm.move(1,0,0, xyz=True, r=1)
        self.assertEqual(cube.getTranslation(), dt.Vector(1,0,0))
        pm.move(0,1,0, xyz=True, r=1)
        self.assertEqual(cube.getTranslation(), dt.Vector(1,1,0))
        pm.move(0,0,1, xyz=True, r=1)
        self.assertEqual(cube.getTranslation(), dt.Vector(1,1,1))
        
class test_lazyDocs(unittest.TestCase):
    # Test can't be reliably run if pymel.all is imported... re-stubbing
    # doesn't work
#    def test_stubMethodDocs(self):
#        origCmd = cmd = cmds.filter
#        try:
#            # if maya.cmds.filter has already been 'de-stubbed', re-stub it
#            if not cmd.__name__ == 'stubFunc':
#                # maya.cmds.dynamicLoad will fail if a library has already been
#                # loaded, so we could just feed in a dummy library..
#                cmd = _makeStubFunc('filter', 'Devices.dll')
#                cmds.filter = cmd
#            self.assertTrue('Creates or modifies a filter node' in 
#                            pm.nt.Filter.__doc__)
#        finally:
#            if cmds.filter != origCmd:
#                cmds.filter = origCmd
                
    def test_getCmdName(self):
        cmd = cmds.filter
        if not cmd.__name__ == 'stubFunc':
            # maya.cmds.dynamicLoad will fail if a library has already been
            # loaded, so we could just feed in a dummy library..
            cmd = _makeStubFunc('filter', 'Devices.dll')
        self.assertEqual(pmcmds.getCmdName(cmd), 'filter')
        
         

class test_hasAttr(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.loc = pm.spaceLocator()
    
    def test_transformAttr(self):
        self.assertTrue(pm.hasAttr(self.loc, 'tx', checkShape=False))
        self.assertTrue(pm.hasAttr(self.loc, 'tx', checkShape=True))
        self.assertTrue(self.loc.hasAttr('tx', checkShape=False))
        self.assertTrue(self.loc.hasAttr('tx', checkShape=True))

    def test_shapeAttr(self):
        self.assertFalse(pm.hasAttr(self.loc, 'localPositionX', checkShape=False))
        self.assertTrue(pm.hasAttr(self.loc, 'localPositionX', checkShape=True))
        self.assertFalse(self.loc.hasAttr('localPositionX', checkShape=False))
        self.assertTrue(self.loc.hasAttr('localPositionX', checkShape=True))

    def test_badAttr(self):
        self.assertFalse(pm.hasAttr(self.loc, 'foobar', checkShape=False))
        self.assertFalse(pm.hasAttr(self.loc, 'foobar', checkShape=True))
        self.assertFalse(self.loc.hasAttr('foobar', checkShape=False))
        self.assertFalse(self.loc.hasAttr('foobar', checkShape=True))


#suite = unittest.TestLoader().loadTestsFromTestCase(testCase_nodesAndAttributes)
#suite.addTest(unittest.TestLoader().loadTestsFromTestCase(testCase_listHistory))
#unittest.TextTestRunner(verbosity=2).run(suite)
#setupUnittestModule(__name__)

     
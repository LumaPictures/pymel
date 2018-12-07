import sys, os, inspect, unittest, logging
import types
import maya.OpenMaya as om
#from testingutils import setupUnittestModule
from pymel.core import *
import pymel.core as pm
import pymel.core.general
import pymel.versions as versions
import pymel.internal.factories as factories
import pymel.internal.pmcmds as pmcmds
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
import tempfile
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
        cmds.setAttr( 'node.pointArrayAttr', 2, (1,2,3,4), (1,2,3,4), type='pointArray' )
        assert cmds.getAttr( 'node.pointArrayAttr' )    == [(1.0, 2.0, 3.0, 4.0), (1.0, 2.0, 3.0, 4.0)]

    def test_vectorArray(self):
        cmds.setAttr( 'node.vectorArrayAttr', 2, (1,2,3), (1,2,3), type='vectorArray' )
        assert cmds.getAttr( 'node.vectorArrayAttr' )   == [(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)]

    def test_stringArray(self):
        # string array
        cmds.setAttr( 'node.stringArrayAttr', 3, 'one', 'two', 'three', type='stringArray' )
        assert cmds.getAttr( 'node.stringArrayAttr' )   == [u'one', u'two', u'three']

    def test_string(self):
        cmds.setAttr( 'node.stringAttr', 'one', type='string' )
        assert cmds.getAttr( 'node.stringAttr' )        == u'one'

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

def addPymelSetAttrTests():
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
            def testSetAttr(self):
                at = 'node.' + typ + 'Attr'
                setAttr(at, val)
                newval = getAttr(at)
                assert newval == mainVal, "setAttr %s: returned value %r is not equal to input value %r" % (typ, newval, mainVal)

            testSetAttr.__name__ = 'test_setAttr_' + typ + '_' + str(i)
            testSetAttr.description = testSetAttr.__name__
            setattr(testCase_mayaSetAttr, testSetAttr.__name__, testSetAttr)
addPymelSetAttrTests()

class testCase_mayaLockAttr(unittest.TestCase):

    def setUp(self):
        self.temp = os.path.join(tempfile.gettempdir(), 'referencesTest')
        if not os.path.isdir(self.temp):
            os.makedirs(self.temp)
        print "created temp dir: %s" % self.temp

        # Refs:
        #  sphere.ma
        #    (no refs)

        #  master.ma
        #    :sphere1 => sphere.ma
        #    :sphere2 => sphere.ma


        # create sphere file
        print "sphere file"
#        cmds.file(new=1, f=1)
        pm.newFile(f=1)
        sphere = pm.polySphere()[0]

        pm.addAttr(sphere, ln='zombieAttr1')
        pm.addAttr(sphere, ln='zombieAttr2')
        cmds.setAttr('%s.v' % sphere, lock=1)
        cmds.setAttr('%s.zombieAttr1' % sphere, lock=1)

        self.sphereFile = pm.saveAs( os.path.join( self.temp, 'sphere.ma' ), f=1 )

        print "master file"
        pm.newFile(f=1)
        self.sphereRef1 = pm.createReference( self.sphereFile, namespace='sphere1' )
        self.sphereRef2 = pm.createReference( self.sphereFile, namespace='sphere2' )
        self.sphere1 = pm.PyNode('sphere1:pSphere1')
        self.sphere2 = pm.PyNode('sphere2:pSphere1')
        self.sphere1.attr('translateY').set(2)
        self.sphere2.attr('translateY').set(4)

        self.cube = pm.polyCube()[0]
        pm.addAttr(self.cube, ln='zombieAttr1')
        pm.addAttr(self.cube, ln='zombieAttr2')
        cmds.setAttr('%s.v' % self.cube, lock=1)
        cmds.setAttr('%s.zombieAttr1' % self.cube, lock=1)

        self.masterFile = pm.saveAs(os.path.join(self.temp, 'master.ma'), f=1)

    def test_isLocked(self):
        nodes = [self.cube, self.sphere1, self.sphere2]
        attrs = ['v', 'zombieAttr1', 'zombieAttr2', 'rotateX']
        for node in nodes:
            for attr in attrs:
                pmAttr = getattr(node, attr)
                strAttr = '%s.%s' % (node, attr)
                self.assertEqual(pmAttr.isLocked(), cmds.getAttr(strAttr, lock=1))

    def test_lock(self):
        node = self.cube
        lockedAttrs = ['v', 'zombieAttr1']
        unlockedAttrs = ['zombieAttr2', 'rotateX']

        for attr in lockedAttrs:
            pmAttr = getattr(node, attr)
            strAttr = '%s.%s' % (node, attr)
            pmAttr.lock()
            self.assertTrue(cmds.getAttr(strAttr, lock=1))
            pmAttr.unlock()
            self.assertFalse(cmds.getAttr(strAttr, lock=1))
            pmAttr.lock()

        for attr in unlockedAttrs:
            pmAttr = getattr(node, attr)
            strAttr = '%s.%s' % (node, attr)
            pmAttr.unlock()
            self.assertFalse(cmds.getAttr(strAttr, lock=1))
            pmAttr.lock()
            self.assertTrue(cmds.getAttr(strAttr, lock=1))
            pmAttr.unlock()

    def test_lockRefs(self):
        nodes = [self.sphere1, self.sphere2]
        attrs = ['v', 'zombieAttr1', 'zombieAttr2', 'rotateX']
        for node in nodes:
            for attr in attrs:
                pmAttr = getattr(node, attr)
                lock = pmAttr.isLocked()

                # Check references
                self.assertRaises(AttributeError, pmAttr.lock, checkReference=True)
                self.assertEqual(pmAttr.isLocked(), lock)

                # Don't check references
                pmAttr.setLocked(not lock, checkReference=False)
                self.assertEqual(pmAttr.isLocked(), not lock)
                pmAttr.setLocked(lock, checkReference=False)

                # Don't check references (default)
                pmAttr.setLocked(not lock)
                self.assertEqual(pmAttr.isLocked(), not lock)
                pmAttr.setLocked(lock)

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

    def test_attribute_indexed_equality(self):
        self.assertEqual( self.sphere1.pnts[5], self.sphere3.pnts[5] )
        self.assertNotEqual(self.sphere1.pnts[5], self.sphere3.pnts[10])

    def test_attribute_indexed_parent_equality(self):
        self.assertEqual( self.sphere1.pnts[5].px, self.sphere3.pnts[5].px )
        self.assertNotEqual(self.sphere1.pnts[5].px, self.sphere3.pnts[10].px)

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

    def test_muteAttr(self):
        self.sphere1.t.setKey()

        self.assertEqual(self.sphere1.tx.isMuted(), cmds.mute(str(self.sphere1.tx), q=1))
        self.sphere1.tx.mute()
        self.assertTrue(self.sphere1.tx.isMuted())
        self.assertEqual(self.sphere1.tx.isMuted(), cmds.mute(str(self.sphere1.tx), q=1))
        self.sphere1.tx.unmute()
        self.assertFalse(self.sphere1.tx.isMuted())
        self.assertEqual(self.sphere1.tx.isMuted(), cmds.mute(str(self.sphere1.tx), q=1))

        self.assertRaises(RuntimeError, self.sphere1.t.isMuted)
        self.sphere1.t.mute()
        for attr in self.sphere1.t.getChildren():
            self.assertTrue(attr.isMuted())
            self.assertEqual(attr.isMuted(), cmds.mute(str(attr), q=1))
        self.sphere1.t.unmute()
        for attr in self.sphere1.t.getChildren():
            self.assertFalse(attr.isMuted())
            self.assertEqual(attr.isMuted(), cmds.mute(str(attr), q=1))

    def tearDown(self):
        newFile(f=1)

class testCase_apiUndo(unittest.TestCase):

    def setUp(self):
        # ensure undo callbacks are set up
        import pymel.internal.factories
        if pymel.internal.factories.apiUndo.undoStateCallbackId is None:
            pymel.internal.factories.apiUndo.installUndoStateCallbacks()

        self.origUndoState = cmds.undoInfo(q=1, state=1)
        # reset all undo queues
        cmds.undoInfo(state=0)
        for chunksClosed in xrange(100):
            chunkName = cmds.undoInfo(q=1, chunkName=1)
            if not chunkName:
                break
            print "closing chunk: {}".format(chunkName)
            cmds.undoInfo(closeChunk=1)
        else:
            print "WARNING - hit maximum number of open undo chunks: {}".format(chunksClosed + 1)

        setAttr( 'persp.focalLength', 35 )
        setAttr( 'top.focalLength', 35 )
        factories.apiUndo.flushUndo()
        cmds.undoInfo(state=1)

    def test_undoRedoAvailable_newFile(self):
        # try to start from as clean a place as possible... other tests might
        # conceivable put us in a "bad state" - ie, running
        # test_transform_translation would leave the scene with
        #   UndoAvailable=1, RedoAvailable=1, UndoOrRedoAvailable=1
        # then do a new file command in it's tearDown, and leave us in a state
        # where:
        #   UndoAvailable=0, RedoAvailable=0, UndoOrRedoAvailable=1
        cmds.undoInfo(state=0)
        cmds.undoInfo(state=1)
        cmds.file(new=1, force=1)
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        cmds.condition('UndoOrRedoAvailable', e=1, state=False)
        self.assertFalse(cmds.isTrue('UndoOrRedoAvailable'))

        # check what happens if UndoAvailable=1, RedoAvailable=0, and we do
        # a newFile...
        SCENE.top.setFocalLength(20)
        self.assertTrue(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertTrue(cmds.isTrue('UndoOrRedoAvailable'))
        cmds.file(new=1, force=1)
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertFalse(cmds.isTrue('UndoOrRedoAvailable'))

        # check what happens if UndoAvailable=0, RedoAvailable=1, and we do
        # a newFile...
        SCENE.top.setFocalLength(20)
        cmds.undo()
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertTrue(cmds.isTrue('RedoAvailable'))
        self.assertTrue(cmds.isTrue('UndoOrRedoAvailable'))
        cmds.file(new=1, force=1)
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertFalse(cmds.isTrue('UndoOrRedoAvailable'))

        # check what happens if UndoAvailable=1, RedoAvailable=1, and we do
        # a newFile...
        SCENE.top.setFocalLength(20)
        SCENE.persp.setFocalLength(20)
        cmds.undo()
        self.assertTrue(cmds.isTrue('UndoAvailable'))
        self.assertTrue(cmds.isTrue('RedoAvailable'))
        self.assertTrue(cmds.isTrue('UndoOrRedoAvailable'))
        cmds.file(new=1, force=1)
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertFalse(cmds.isTrue('UndoOrRedoAvailable'))

    def _do_undo_test(self, module):
        self.assertTrue(module.undoInfo(q=1, state=1))
        self.assertFalse(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertFalse(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 35)
        self.assertEqual(SCENE.persp.getFocalLength(), 35)
        self.assertEqual(len(factories.apiUndo.undo_queue), 0)

        SCENE.top.setFocalLength(20)
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20)
        self.assertEqual(SCENE.persp.getFocalLength(), 35)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        module.undoInfo(stateWithoutFlush=0)  #--------------------------------
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20)
        self.assertEqual(SCENE.persp.getFocalLength(), 35)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        SCENE.persp.setFocalLength(20)
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20)
        self.assertEqual(SCENE.persp.getFocalLength(), 20)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        module.undoInfo(stateWithoutFlush=1)  #--------------------------------
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20)
        self.assertEqual(SCENE.persp.getFocalLength(), 20)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        module.undo()  # undo top focal length back to 35
        self.assertFalse(module.isTrue('UndoAvailable'))
        self.assertTrue(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 35.0)
        self.assertEqual(SCENE.persp.getFocalLength(), 20.0)
        self.assertEqual(len(factories.apiUndo.undo_queue), 0)

        module.redo()
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20.0)
        self.assertEqual(SCENE.persp.getFocalLength(), 20.0)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        # clear maya's undo queue
        # we override undoInfo in system to flush the cache
        module.undoInfo(state=0)
        module.undoInfo(state=1)
        self.assertFalse(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertFalse(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20.0)
        self.assertEqual(SCENE.persp.getFocalLength(), 20.0)
        self.assertEqual(len(factories.apiUndo.undo_queue), 0)

        SCENE.top.setFocalLength(200)
        self.assertTrue(module.isTrue('UndoAvailable'))
        self.assertFalse(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 200.0)
        self.assertEqual(SCENE.persp.getFocalLength(), 20.0)
        self.assertEqual(len(factories.apiUndo.undo_queue), 1)

        module.undo()
        self.assertFalse(module.isTrue('UndoAvailable'))
        self.assertTrue(module.isTrue('RedoAvailable'))
        self.assertTrue(module.isTrue('UndoOrRedoAvailable'))
        self.assertEqual(SCENE.top.getFocalLength(), 20.0)
        self.assertEqual(SCENE.persp.getFocalLength(), 20.0)
        self.assertEqual(len(factories.apiUndo.undo_queue), 0)

    def test_undo_pm(self):
        self._do_undo_test(pm)

    def test_undo_cmds(self):
        self._do_undo_test(cmds)

    def tearDown(self):
        # cleaning
        if self.origUndoState != cmds.undoInfo(q=1, state=1):
            cmds.undoInfo(state=self.origUndoState)
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

class testCase_duplicate(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def test_duplicate(self):
        # make sure that we get proper dag nodes, even when the result will contain non-unique names
        group = cmds.group('persp')
        self.assert_( duplicate(group) )

        # ensure it works with depend nodes too
        dependNode = cmds.createNode('displayLayer')
        self.assert_( duplicate(dependNode) )

    def test_sameOrder(self):
        # Test when we have two nodes with similar names under the same parent,
        # that they're returned in the right order...

        # we create children under the nodes we will duplicate, just so that
        # we can identify which top-level-node is which...
        catParent = pm.createNode('transform', name='parent1')
        pm.createNode('transform', name='cat', parent=catParent)
        dogParent = pm.createNode('transform', name='parent2')
        pm.createNode('transform', name='dog', parent=dogParent)

        dupes = pm.duplicate(dogParent, catParent)

        parentRe = re.compile(r'^\|parent[0-9]$')
        self.assertTrue(parentRe.match(dupes[0].longName()))
        self.assertTrue(parentRe.match(dupes[1].longName()))
        self.assertEqual(dupes[0].getChildren()[0].nodeName(), 'dog')
        self.assertEqual(dupes[1].getChildren()[0].nodeName(), 'cat')

    def test_dupeParentAndChild(self):
        # Test that if one of the args to duplicate is a child of another arg,
        # that pymel can deal
        t1 = pm.nt.Transform(name='foobar')
        t2 = pm.nt.Transform(name='stuff', parent='foobar')
        dupes = pm.duplicate(t1, t2)
        self.assertEqual(dupes[0].longName(), '|foobar1')
        self.assertEqual(dupes[1].longName(), '|foobar1|stuff')
        self.assertEqual(dupes[0], dupes[1].getParent())

    def test_shapeSameName(self):
        # Test that if we dupe a transform that has a shape with an identical
        # name, that pymel can deal
        trans = pm.polySphere(name='Alfred')[0]
        shape = trans.getShape()
        shape.rename(trans.nodeName())
        dupes = pm.duplicate(trans)
        self.assertEqual(dupes[0].longName(), '|Alfred1')
        self.assertEqual(dupes[0].getShape().longName(), '|Alfred1|Alfred1')

    def test_underworld(self):
        camTrans, camShape = pm.camera()
        camTrans.rename('CamNewton')
        imageTrans, imageShape = pm.imagePlane(camera=camShape)
        imageTrans.rename('zeImage')

        self.assertEqual(imageShape.longName(),
                         '|CamNewton|CamNewtonShape->|zeImage|zeImageShape')

        dupes = pm.duplicate(imageTrans)
        self.assertEqual(dupes[0].longName(),
                         '|CamNewton|CamNewtonShape->|zeImage1')


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

class test_ParticleComponent(unittest.TestCase):
    def setUp(self):
        self.partTr, self.partShape = pm.particle(p=[(0, 0, 0), (1, 2, 3)])

    def test_attr_position(self):
        self.assertEqual(self.partShape.pt[0].position, [0, 0, 0])
        self.assertEqual(self.partShape.pt[1].position, [1, 2, 3])

    def tearDown(self):
        pm.delete([self.partShape, self.partTr])

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
        self.assertNotIn( 'FurGlobals', nt.__dict__ )
        loadPlugin('Fur')
        self.assertIn( 'FurGlobals', nt.__dict__ )

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

class test_parent(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.sphere = pm.polySphere()[0]
        self.cube = pm.polyCube()[0]
        self.cone = pm.polyCone()[0]

    def test_parent_world2obj(self):
        self.assertEqual(self.sphere.getParent(), None)
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)

    def test_parent_world2world_1(self):
        self.assertEqual(self.sphere.getParent(), None)
        pm.parent(self.sphere, None)
        self.assertEqual(self.sphere.getParent(), None)

    def test_parent_world2world_2(self):
        self.assertEqual(self.sphere.getParent(), None)
        pm.parent(self.sphere, w=1)
        self.assertEqual(self.sphere.getParent(), None)

    def test_parent_world2world_3(self):
        self.assertEqual(self.sphere.getParent(), None)
        pm.parent(self.sphere, world=True)
        self.assertEqual(self.sphere.getParent(), None)

    def test_parent_obj2obj(self):
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)
        pm.parent(self.sphere, self.cone)
        self.assertEqual(self.sphere.getParent(), self.cone)

    def test_parent_obj2sameObj(self):
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)

    def test_parent_obj2world(self):
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)
        pm.parent(self.sphere, None)
        self.assertEqual(self.sphere.getParent(), None)

    def test_parent_multiWorld2obj(self):
        self.assertEqual(self.sphere.getParent(), None)
        self.assertEqual(self.cube.getParent(), None)
        pm.parent(self.sphere, self.cube, self.cone)
        self.assertEqual(self.sphere.getParent(), self.cone)
        self.assertEqual(self.cube.getParent(), self.cone)

    def test_parent_multiWorld2obj_sel(self):
        self.assertEqual(self.sphere.getParent(), None)
        self.assertEqual(self.cube.getParent(), None)
        pm.select(self.sphere, self.cube, self.cone)
        pm.parent()
        self.assertEqual(self.sphere.getParent(), self.cone)
        self.assertEqual(self.cube.getParent(), self.cone)

    # these tests are here because removeObject flag is a special case that has
    # to be specially handled, and there was a bug introduced at one point
    # because of it

    def test_parent_removeObject_one(self):
        pm.parent(self.sphere, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)
        result = pm.parent(self.sphere, removeObject=True)
        self.assertIs(result, None)
        self.assertEqual(self.sphere.exists(), False)

    def test_parent_removeObject_many(self):
        pm.parent(self.sphere, self.cube)
        pm.parent(self.cone, self.cube)
        self.assertEqual(self.sphere.getParent(), self.cube)
        self.assertEqual(self.cone.getParent(), self.cube)
        result = pm.parent(self.sphere, self.cone, removeObject=True)
        self.assertIs(result, None)
        self.assertFalse(self.sphere.exists())
        self.assertFalse(self.cone.exists())

    def test_parent_to_nonexistent_object(self):
        with self.assertRaises(pm.MayaNodeError):
            pm.parent(self.sphere, 'does_not_exist')

    def test_parent_with_iterables(self):
        """Make sure that parent works with any grouping of args"""
        def makeCubesAndGrp():
            cmds.file(new=1, f=1)
            cubes = []
            for x in range(10):
                cubes.append(pm.polyCube()[0])
            group = pm.group(empty=True)
            return cubes, group

        cubes, group = makeCubesAndGrp()
        res1 = pm.parent(cubes[:4], group)
        self.assertEqual(cubes[:4], res1)
        res2 = pm.parent(cubes, group)
        self.assertEqual(cubes[4:], res2)

        cubes, group = makeCubesAndGrp()
        res1 = pm.parent(cubes[:4] + [group])
        self.assertEqual(cubes[:4], res1)
        res2 = pm.parent(cubes, group)
        self.assertEqual(cubes[4:], res2)

        cubes, group = makeCubesAndGrp()
        res1 = pm.parent(cubes[0], cubes[1], cubes[2], cubes[3], group)
        self.assertEqual(cubes[:4], res1)
        res2 = pm.parent(cubes, group)
        self.assertEqual(cubes[4:], res2)

        cubes, group = makeCubesAndGrp()
        res1 = pm.parent(cubes[0], cubes[1], [cubes[2], cubes[3], group])
        self.assertEqual(cubes[:4], res1)
        res2 = pm.parent(cubes, group)
        self.assertEqual(cubes[4:], res2)

        cubes, group = makeCubesAndGrp()
        res1 = pm.parent([cubes[0], cubes[1]], cubes[2], [cubes[3], group])
        self.assertEqual(cubes[:4], res1)
        res2 = pm.parent(cubes, group)
        self.assertEqual(cubes[4:], res2)


# TODO: make test cases for all combinations of
#  origNode - not instanced, direct-instanced, indirect-instanced
#  newParentNode - not instanced, direct-instanced, indirect-instanced
#  cmds.parent, pm.parent
#  relative=True/False

class test_parent_instance(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.A1 = cmds.createNode('transform', name='A1')
        self.A2 = cmds.createNode('transform', name='A2')
        self.B1 = cmds.createNode('transform', name='B1')
        self.B2 = cmds.createNode('transform', name='B2')
        self.nonInstParent = cmds.createNode('transform', name='nonInstParent')

        self.instParentA1 = cmds.createNode('transform', name='instParentA',
                                            parent=self.A1)
        cmds.parent(self.instParentA1, self.A2, addObject=True)
        self.instParentA1 = '{}|instParentA'.format(self.A1)
        self.instParentA2 = '{}|instParentA'.format(self.A2)
        self.assertTrue(cmds.objExists(self.instParentA1))
        self.assertTrue(cmds.objExists(self.instParentA2))

        self.instParentB1 = cmds.createNode('transform', name='instParentB',
                                            parent=self.B1)
        cmds.parent(self.instParentB1, self.B2, addObject=True)
        self.instParentB1 = '{}|instParentB'.format(self.B1)
        self.instParentB2 = '{}|instParentB'.format(self.B2)
        self.assertTrue(cmds.objExists(self.instParentB1))
        self.assertTrue(cmds.objExists(self.instParentB2))

        instSphere = cmds.polySphere()[0]
        cmds.parent(instSphere, self.instParentB1)
        self.instSphereB1 = '{}|{}'.format(self.instParentB1, instSphere)
        self.instSphereB2 = '{}|{}'.format(self.instParentB2, instSphere)
        self.assertTrue(cmds.objExists(self.instSphereB1))
        self.assertTrue(cmds.objExists(self.instSphereB2))

        self.nonInstCube = cmds.polyCube()[0]

    def test_cmds_parent_nonInst_to_nonInst(self):
        orig = pm.PyNode(self.nonInstCube)
        parent = pm.PyNode(self.nonInstParent)
        self.assertFalse(orig.isInstanced())
        self.assertFalse(parent.isInstanced())
        cmds.parent(self.nonInstCube, self.nonInstParent, r=1)
        self.assertFalse(orig.isInstanced())
        self.assertTrue(orig.__apimdagpath__().isValid())
        # getting instanceNumber will trigger usage of dag path
        self.assertEqual(orig.instanceNumber(), 0)


    def test_cmds_parent_nonInst_to_inst(self):
        orig = pm.PyNode(self.nonInstCube)
        parent = pm.PyNode(self.instParentA1)
        self.assertFalse(orig.isInstanced())
        self.assertTrue(parent.isInstanced())
        cmds.parent(self.nonInstCube, self.instParentA1, r=1)
        self.assertTrue(orig.isInstanced())
        self.assertRaises(pm.MayaInstanceError, orig.__apimdagpath__)
        # getting instanceNumber will trigger usage of dag path
        self.assertRaises(pm.MayaInstanceError, orig.instanceNumber)
        # if we delete the other inst, we should be able to use it again
        pm.delete(self.A2)
        self.assertFalse(orig.isInstanced())
        self.assertTrue(orig.__apimdagpath__().isValid())
        self.assertEqual(orig.instanceNumber(), 0)

    def test_cmds_parent_inst_to_nonInst(self):
        orig = pm.PyNode(self.instSphereB1)
        parent = pm.PyNode(self.nonInstParent)
        self.assertTrue(orig.isInstanced())
        self.assertFalse(parent.isInstanced())
        cmds.parent(self.instSphereB1, self.nonInstParent, r=1)
        # Ok... so it seems that even if you specify r=1, when parenting an
        # indirectly-instanced object (ie, one that only has one node as a
        # direct parent... but that parent, or one of it's ancestors, has
        # multiple parents), it still creates multiple transforms, so the number
        # of instances is preserved.
        #
        # In my case, I start with this hierarchy:
        #
        #     B1   B2          nonInstParent
        #      |____|
        #        |
        #    instParentB
        #        |
        #      pSphere1
        #
        # ...and then if I do parent(pShere1, nonInstParent, r=1), I get:
        #
        #     B1   B2          nonInstParent
        #      |____|             __|____
        #        |               |       |
        #    instParentB    transform1   |
        #                        |_______|
        #                            |
        #                         pSphere1
        #
        # That is, pShere is parented directly under nonInstParent once, and
        # under a newly-created transform1 once. Transform1 will always be zero,
        # so it doesn't serve much of a purpose... and I can't think of why
        # you'd ever want some objects directly parented, and some with extra
        # transforms... so this seems like a bug... but we're stuck with it.
        #
        # For completeness, if you do parent(pShere1, nonInstParent), you get:
        #
        #     B1   B2          nonInstParent
        #      |____|             __|_______
        #        |               |          |
        #    instParentB    transform1   transform2
        #                        |__________|
        #                            |
        #                         pSphere1
        #
        # ...which is at least consistent...
        #
        self.assertTrue(orig.isInstanced())
        self.assertRaises(pm.MayaInstanceError, orig.__apimdagpath__)
        # getting instanceNumber will trigger usage of dag path
        self.assertRaises(pm.MayaInstanceError, orig.instanceNumber)
        # if we delete the other inst, we should be able to use it again
        pm.delete('{}|transform1'.format(self.nonInstParent))
        self.assertFalse(orig.isInstanced())
        self.assertTrue(orig.__apimdagpath__().isValid())
        self.assertEqual(orig.instanceNumber(), 0)

    def test_cmds_parent_inst_to_inst(self):
        orig = pm.PyNode(self.instSphereB1)
        parent = pm.PyNode(self.instParentA2)
        self.assertTrue(orig.isInstanced())
        self.assertTrue(parent.isInstanced())
        cmds.parent(self.instSphereB1, self.instParentA2, r=1)
        self.assertTrue(orig.isInstanced())
        self.assertRaises(pm.MayaInstanceError, orig.__apimdagpath__)
        # getting instanceNumber will trigger usage of dag path
        self.assertRaises(pm.MayaInstanceError, orig.instanceNumber)
        # we end up with FOUR instances... see note in test_cmds_parent_inst_to_nonInst
        pm.delete(self.A1)
        pm.delete('{}|transform1'.format(self.instParentA2))
        self.assertFalse(orig.isInstanced())
        self.assertTrue(orig.__apimdagpath__().isValid())
        self.assertEqual(orig.instanceNumber(), 0)


    def test_pm_parent_nonInst_to_nonInst(self):
        orig = pm.PyNode(self.nonInstCube)
        parent = pm.PyNode(self.nonInstParent)
        self.assertFalse(orig.isInstanced())
        self.assertFalse(parent.isInstanced())
        pm.parent(orig, parent, r=1)
        self.assertFalse(orig.isInstanced())
        self.assertTrue(orig.__apimdagpath__().isValid())
        # getting instanceNumber will trigger usage of dag path
        self.assertEqual(orig.instanceNumber(), 0)


    def test_pm_parent_nonInst_to_inst(self):
        orig = pm.PyNode(self.nonInstCube)
        parent = pm.PyNode(self.instParentA1)
        self.assertFalse(orig.isInstanced())
        self.assertTrue(parent.isInstanced())
        pm.parent(orig, parent, r=1)
        self.assertTrue(orig.isInstanced())
        self.assertEqual(orig.getParent(), parent)

    def test_pm_parent_inst_to_nonInst(self):
        orig = pm.PyNode(self.instSphereB1)
        parent = pm.PyNode(self.nonInstParent)
        self.assertTrue(orig.isInstanced())
        self.assertFalse(parent.isInstanced())
        pm.parent(orig, parent, r=1)
        self.assertTrue(orig.isInstanced())
        self.assertEqual(orig.getParent(), parent)

    def test_pm_parent_inst_to_inst(self):
        orig = pm.PyNode(self.instSphereB1)
        parent = pm.PyNode(self.instParentA2)
        self.assertTrue(orig.isInstanced())
        self.assertTrue(parent.isInstanced())
        pm.parent(orig, parent, r=1)
        self.assertTrue(orig.isInstanced())
        self.assertEqual(orig.getParent(), parent)


class test_spaceLocator(unittest.TestCase):
    def test_nonUniqueName(self):
        cmds.file(f=1, new=1)
        loc1 = cmds.spaceLocator(name='theLoc')
        cmds.group(loc1, name='theGroup')
        self.assertEqual(cmds.ls('*theLoc', long=True), ['|theGroup|theLoc'])
        loc2 = pm.spaceLocator(name='theLoc')
        self.assertEqual(type(loc2), pm.nt.Transform)
        self.assertEqual(loc2.fullPath(), '|theLoc')

    def test_position(self):
        cmds.file(f=1, new=1)
        locTrans = pm.spaceLocator(name='theLoc', position=(1,2,3))
        locShape = locTrans.getShape()
        self.assertEqual(type(locShape), pm.nt.Locator)
        self.assertEqual(locTrans.getTranslation(), pm.dt.Vector(0,0,0))
        self.assertEqual(locShape.attr('localPosition').get(),
                         pm.dt.Vector(1,2,3))

        # Ok, this is lame - in create mode, position set's the local position
        # (on the shape) - but in edit mode, it sets the translation (on the
        # transform).  I'm not going to bother testing what seems like a bug
        # / mistake...
        # pm.spaceLocator(locShape, e=1, position=(4,5,6))
        # self.assertEqual(locTrans.getTranslation(), pm.dt.Vector(0,0,0))
        # self.assertEqual(locShape.attr('localPosition').get(),
        #                  pm.dt.Vector(4,5,6))

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

    # assert that we can get a docstring for every class and method
    def test_LazyDocString_evaluation(self):
        def iterDocObjs(module):
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, '__doc__'):
                    yield '{}.{}'.format(module.__name__ , name), obj
                if inspect.isclass(obj):
                    # we don't recurse, we only go 2 levels deep for simplicity
                    # this should get most things, good enough for testing,
                    # and we don't have to worry about recursion
                    for name2, obj2 in inspect.getmembers(obj):
                        yield '{}.{}.{}'.format(module.__name__, name, name2), obj2

        for module in (pm, pm.nt):
            for name, obj in iterDocObjs(module):
                # we just want to make sure this doesn't error
                try:
                    str(obj.__doc__)
                except Exception:
                    print "errored getting docstring for {}".format(name)
                    raise


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

    def test_AttributeSpec(self):
        self.loc.addAttr('spangle')
        self.assertTrue(pm.hasAttr(self.loc, 'spangle'))
        attrSpec = self.loc.attrSpec('spangle')
        self.assertTrue(pm.hasAttr(self.loc, attrSpec))
        txAttrSpec = pm.nt.Transform.attrSpec('tx')
        self.assertTrue(pm.hasAttr(self.loc, txAttrSpec))
        otherAttrSpec = pm.nt.Time.attrSpec('outTime')
        self.assertFalse(pm.hasAttr(self.loc, otherAttrSpec))


class test_setEnums(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.loc = pm.spaceLocator()
        # if you don't specify enumName when the attribute is created, maya
        # doesn't think it's an enum when you try to set the enums later...
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName='foo:bar')
        self.enumAttr = self.loc.attr('testEnumAttr')

    def test_string_noIndices(self):
        self.enumAttr.setEnums('first:second:third')
        self.assertEqual(self.enumAttr.getEnums(),
                         {'first':0, 'second':1, 'third':2})

    def test_string_allIndices(self):
        self.enumAttr.setEnums('giraffe=1:gazelle=5:lion=3')
        self.assertEqual(self.enumAttr.getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':3})

    def test_string_partialIndices(self):
        self.enumAttr.setEnums('giraffe=1:gazelle=5:lion')
        self.assertEqual(self.enumAttr.getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':6})

    def test_list_noIndices(self):
        self.enumAttr.setEnums(['giraffe', 'gazelle', 'lion'])
        self.assertEqual(self.enumAttr.getEnums(),
                         {'giraffe':0, 'gazelle':1, 'lion':2})

    def test_list_allIndices(self):
        self.enumAttr.setEnums(['giraffe=1', 'gazelle=5', 'lion=3'])
        self.assertEqual(self.enumAttr.getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':3})

    def test_list_partialIndices(self):
        self.enumAttr.setEnums(['giraffe=1', 'gazelle=5', 'lion'])
        self.assertEqual(self.enumAttr.getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':6})

    def test_dict(self):
        newEnums = {'giraffe':1, 'gazelle':5, 'lion':3}
        self.enumAttr.setEnums({'giraffe':1, 'gazelle':5, 'lion':3})
        self.assertEqual(self.enumAttr.getEnums(), newEnums)

class test_addAttr(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.loc = pm.spaceLocator()

    def test_enumName_string_noIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName='first:second:third')
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'first':0, 'second':1, 'third':2})

    def test_enumName_string_allIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName='giraffe=1:gazelle=5:lion=3')
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':3})

    def test_enumName_string_partialIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName='giraffe=1:gazelle=5:lion')
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':6})

    def test_enumName_list_noIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName=['giraffe', 'gazelle', 'lion'])
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'giraffe':0, 'gazelle':1, 'lion':2})

    def test_enumName_list_allIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName=['giraffe=1', 'gazelle=5', 'lion=3'])
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':3})

    def test_enumName_list_partialIndices(self):
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName=['giraffe=1', 'gazelle=5', 'lion'])
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(),
                         {'giraffe':1, 'gazelle':5, 'lion':6})

    def test_enumName_dict(self):
        newEnums = {'giraffe':1, 'gazelle':5, 'lion':3}
        self.loc.addAttr('testEnumAttr', attributeType='enum',
                         enumName={'giraffe':1, 'gazelle':5, 'lion':3})
        self.assertEqual(self.loc.attr('testEnumAttr').getEnums(), newEnums)

    def test_type_double(self):
        self.loc.addAttr('autoDouble', type='double')
        self.assertEqual(pm.addAttr(self.loc + '.autoDouble', query=1,
                                    attributeType=1),
                         'double')
        self.assertEqual(pm.addAttr(self.loc + '.autoDouble', query=1,
                                    dataType=1),
                         'TdataNumeric')

    def test_type_mesh(self):
        self.loc.addAttr('autoMesh', type='mesh')
        self.assertEqual(pm.addAttr(self.loc + '.autoMesh', query=1,
                                    attributeType=1),
                         'typed')
        self.assertEqual(pm.addAttr(self.loc + '.autoMesh', query=1,
                                    dataType=1),
                         'mesh')

    def test_type_vector(self):
        self.loc.addAttr('autoVec', type=pm.dt.Vector)
        self.assertEqual([x.attrName() for x in self.loc.listAttr()
                         if 'autoVec' in x.attrName()],
                         [u'autoVec', u'autoVecX',
                          u'autoVecY', u'autoVecZ'])

    def test_type_float3Color(self):
        self.loc.addAttr('autoFloat3Col', type='float3', usedAsColor=1)
        self.assertEqual([x.attrName() for x in self.loc.listAttr()
                         if 'autoFloat3Col' in x.attrName()],
                         [u'autoFloat3Col', u'autoFloat3ColR',
                          u'autoFloat3ColG', u'autoFloat3ColB'])

    def test_type_long2(self):
        self.loc.addAttr('autoLong2', type='long2',
                         childSuffixes=['_first', '_second'])
        self.assertEqual([x.attrName() for x in self.loc.listAttr()
                         if 'autoLong2' in x.attrName()],
                         [u'autoLong2', u'autoLong2_first',
                          u'autoLong2_second'])


class test_deleteAttr(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.node = pm.createNode('transform', name='daNode')
        self.assertFalse(self.node.hasAttr('foobar'))
        self.node.addAttr('foobar')
        self.attr = self.node.attr('foobar')

    def test_nodeattr_str(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr('daNode.foobar')
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_node_str_attr_str(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr('daNode', at='foobar')
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_node_obj_attr_str(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr(self.node, attribute='foobar')
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_attr_obj(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr(self.attr)
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_node_str_attr_spec(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr('daNode', attribute=self.node.attrSpec('foobar'))
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_node_obj_attr_spec(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        pm.deleteAttr(self.node, at=self.node.attrSpec('foobar'))
        self.assertFalse(self.node.hasAttr('foobar'))


class test_Attribute_iterDescendants(unittest.TestCase):
    # FIXME: to prevent this test from changing over time it might be a good idea to create
    # custom MPxNode type with known attributes
    # See also: test_nodetypes.testCase_listAttr
    def setUp(self):
        pm.newFile(f=1)
        self.cube1 = pm.polyCube(ch=0)[0]
        self.cube2 = pm.polyCube(ch=0)[0]
        self.cube3 = pm.polyCube(ch=0)[0]
        self.blend = pm.blendShape(self.cube2, self.cube3, self.cube1)[0]

    def test_multi(self):
        results = sorted(x.name() for x in
                         self.blend.attr('weight').iterDescendants())
        expected = [u'blendShape1.weight[0]', u'blendShape1.weight[1]']
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('weight').iterDescendants(levels=1))
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('weight').iterDescendants(levels=2))
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('weight').iterDescendants(levels=0))
        self.assertEqual(results, [])

    def test_compound(self):
        results = sorted(x.name() for x in
                         self.blend.attr('baseOrigin').iterDescendants())
        expected = [u'blendShape1.baseOriginX',
                    u'blendShape1.baseOriginY',
                    u'blendShape1.baseOriginZ']
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('baseOrigin').iterDescendants(levels=1))
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('baseOrigin').iterDescendants(levels=2))
        self.assertEqual(results, expected)

        results = sorted(x.name() for x in
                         self.blend.attr('baseOrigin').iterDescendants(levels=0))
        self.assertEqual(results, [])


    def test_multiCompound(self):
        results = set(x.name() for x in
                      self.blend.attr('inputTarget').iterDescendants())
        expected = {
            u'blendShape1.inputTarget[0]',
            u'blendShape1.inputTarget[0].baseWeights',
            u'blendShape1.inputTarget[0].inputTargetGroup',
            u'blendShape1.inputTarget[0].inputTargetGroup[0]',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000]',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputGeomTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputPointsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].normalizationId',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].targetWeights',
            u'blendShape1.inputTarget[0].inputTargetGroup[1]',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000]',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputComponentsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputGeomTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputPointsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].normalizationId',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].targetWeights',
            u'blendShape1.inputTarget[0].normalizationGroup',
            u'blendShape1.inputTarget[0].paintTargetIndex',
            u'blendShape1.inputTarget[0].paintTargetWeights',
        }
        self.assertTrue(results.issuperset(expected))
        self.assertNotIn(u'blendShape1.inputTarget[-1].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget', results)

        results = sorted(x.name() for x in
                         self.blend.attr('inputTarget').iterDescendants(levels=1))
        expected = [u'blendShape1.inputTarget[0]']
        self.assertEqual(results, expected)

        results = set(x.name() for x in
                      self.blend.attr('inputTarget').iterDescendants(levels=2))
        expected = {
            u'blendShape1.inputTarget[0]',
            u'blendShape1.inputTarget[0].baseWeights',
            u'blendShape1.inputTarget[0].inputTargetGroup',
            u'blendShape1.inputTarget[0].normalizationGroup',
            u'blendShape1.inputTarget[0].paintTargetIndex',
            u'blendShape1.inputTarget[0].paintTargetWeights',
        }
        self.assertTrue(results.issuperset(expected))
        self.assertNotIn(u'blendShape1.inputTarget[-1].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1]', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].inputTargetGroup[0]', results)

        results = sorted(x.name() for x in
                         self.blend.attr('inputTarget').iterDescendants(levels=0))
        self.assertEqual(results, [])

class test_Attribute_minMax(unittest.TestCase):
    def setUp(self):
        self.cube = pm.polyCube()[0]
        self.cube.addAttr('boundedSingle', minValue=0.0, softMinValue=10.0, softMaxValue=20.0, maxValue=30.0)
        self.cube.addAttr('boundedMulti', multi=True, minValue=0.0, softMinValue=10.0, softMaxValue=20.0, maxValue=30.0)

        self.cube.addAttr('unboundedSingle')
        self.cube.addAttr('unboundedMulti', multi=True)

        self.boundedSingle = self.cube.attr('boundedSingle')
        self.boundedMulti = self.cube.attr('boundedMulti')
        self.boundedElem = self.boundedMulti[0]

        self.unboundedSingle = self.cube.attr('unboundedSingle')
        self.unboundedMulti = self.cube.attr('unboundedMulti')
        self.unboundedElem = self.unboundedMulti[0]

    def tearDown(self):
        pm.delete(self.cube)

    def setTest(self, attr, val):
        attr.set(val)
        self.assertEqual(attr.get(), val)

    def setBoundsTest(self, attr):
        self.assertRaises(RuntimeError, attr.set, -5.0)
        self.setTest(attr, 0.0)
        self.setTest(attr, 5.0)
        self.setTest(attr, 10.0)
        self.setTest(attr, 15.0)
        self.setTest(attr, 20.0)
        self.setTest(attr, 25.0)
        self.setTest(attr, 30.0)
        self.assertRaises(RuntimeError, attr.set, 35.0)

    def test_set_single(self):
        self.setBoundsTest(self.boundedSingle)

    def test_set_elem(self):
        self.setBoundsTest(self.boundedElem)

    def getBoundsTest(self, attr):
        self.assertEqual(attr.getMin(), 0.0)
        self.assertEqual(attr.getSoftMin(), 10.0)
        self.assertEqual(attr.getSoftMax(), 20.0)
        self.assertEqual(attr.getMax(), 30.0)

    def test_getBounds_boundedSingle(self):
        self.getBoundsTest(self.boundedSingle)

    def test_getBounds_boundedMulti(self):
        self.getBoundsTest(self.boundedMulti)

    def test_getBounds_boundedElem(self):
        self.getBoundsTest(self.boundedElem)

    def getNoBoundsTest(self, attr):
        self.assertEqual(attr.getMin(), None)
        self.assertEqual(attr.getSoftMin(), None)
        self.assertEqual(attr.getSoftMax(), None)
        self.assertEqual(attr.getMax(), None)

    def test_getBounds_unboundedSingle(self):
        self.getNoBoundsTest(self.unboundedSingle)

    def test_getBounds_unboundedMulti(self):
        self.getNoBoundsTest(self.unboundedMulti)

    def test_getBounds_unboundedElem(self):
        self.getNoBoundsTest(self.unboundedElem)

class test_Attribute_getSetAttrCmds(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.loc = pm.spaceLocator()

    def test_float(self):
        attr = self.loc.attr('translateX')
        attr.set(5.5)
        attrCmds = [x.strip() for x in attr.getSetAttrCmds()]
        self.assertEqual(attrCmds, ['setAttr ".tx" 5.5;'])

    def test_string(self):
        self.loc.addAttr('myString', dataType='string')
        attr = self.loc.attr('myString')
        attr.set('foo')
        attrCmds = [x.strip() for x in attr.getSetAttrCmds()]
        self.assertEqual(attrCmds, ['setAttr ".myString" -type "string" "foo";'])

    def test_float3(self):
        attr = self.loc.attr('rotate')
        attr.set((1.0, 2.0, 33.3))
        attrCmds = [x.strip() for x in attr.getSetAttrCmds()]
        self.assertEqual(attrCmds, [
            'setAttr ".r" -type "double3" 1 2 33.3 ;',
        ])

    def test_intMulti(self):
        self.loc.addAttr('myIntMulti', attributeType='long', multi=True)
        attr = self.loc.attr('myIntMulti')
        attr[0].set(1)
        attr[1].set(5)
        attr[5].set(7)
        attrCmds = [x.strip() for x in attr.getSetAttrCmds()]
        self.assertEqual(attrCmds, [
            'setAttr -s 3 ".myIntMulti";',
            'setAttr ".myIntMulti[0]" 1;',
            'setAttr ".myIntMulti[1]" 5;',
            'setAttr ".myIntMulti[5]" 7;',
        ])

class test_Attribute_getDefault(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)

    def test_float(self):
        tx = pm.Attribute('persp.translateX')
        self.assertEqual(tx.getDefault(), 0.0)
        sz = pm.Attribute('persp.scaleZ')
        self.assertEqual(sz.getDefault(), 1.0)

    def test_compound_float(self):
        t = pm.Attribute('persp.translate')
        self.assertEqual(t.getDefault(), [0.0, 0.0, 0.0])
        s = pm.Attribute('persp.scale')
        self.assertEqual(s.getDefault(), [1.0, 1.0, 1.0])

    def test_bool(self):
        attr = pm.Attribute('persp.maxRotLimitEnable')
        self.assertEqual(attr.getDefault(), [0.0, 0.0, 0.0])
        attr = pm.Attribute('persp.maxRotXLimitEnable')
        self.assertEqual(attr.getDefault(), 0.0)

    def test_enum(self):
        attr = pm.Attribute('persp.rotateOrder')
        self.assertEqual(attr.getDefault(), 0.0)

    def test_nonNumeric(self):
        attr = pm.Attribute('persp.xformMatrix')
        self.assertIs(attr.getDefault(), None)
        attr = pm.Attribute('persp.specifiedManipLocation')
        self.assertIs(attr.getDefault(), None)


class test_AttributeSpec(unittest.TestCase):
    def assertWorldMatrix(self, attrSpec):
        self.assertTrue(attrSpec.isWorldSpace())
        self.assertTrue(attrSpec.isReadable())
        self.assertFalse(attrSpec.isWritable())
        self.assertTrue(attrSpec.isArray())
        self.assertEqual(attrSpec.name(), 'worldMatrix')
        self.assertEqual(attrSpec.shortName(), 'wm')
        self.assertIsNone(attrSpec.parent())

    def test_create_str(self):
        attrSpec = pm.AttributeSpec('persp.worldMatrix')
        self.assertWorldMatrix(attrSpec)

    def test_create_Attribute(self):
        attr = pm.PyNode('persp').attr('worldMatrix')
        attrSpec = pm.AttributeSpec(attr)
        self.assertWorldMatrix(attrSpec)

    def test_create_AttributeSpec(self):
        attrSpecOrig = pm.AttributeSpec('persp.wm')
        attrSpec = pm.AttributeSpec(attrSpecOrig)
        self.assertWorldMatrix(attrSpec)

    def test_create_mplug(self):
        sel = om.MSelectionList()
        sel.add('persp.worldMatrix')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        attrSpec = pm.AttributeSpec(mplug)
        self.assertWorldMatrix(attrSpec)

    def test_create_mobject(self):
        sel = om.MSelectionList()
        sel.add('persp.worldMatrix')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        mobj = mplug.attribute()
        attrSpec = pm.AttributeSpec(mobj)
        self.assertWorldMatrix(attrSpec)


class test_exists(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, force=1)

    def test_depend_node(self):
        node = pm.createNode('time')
        self.assertTrue(node.exists())
        cmds.delete(node.name())
        self.assertFalse(node.exists())

    def test_dag_node(self):
        node = pm.createNode('transform')
        self.assertTrue(node.exists())
        cmds.delete(node.name())
        self.assertFalse(node.exists())

    def test_attribute(self):
        node = pm.createNode('transform')
        attr = node.attr('tx')
        self.assertTrue(attr.exists())
        cmds.delete(node.name())
        self.assertFalse(attr.exists())

    def test_dyn_attribute(self):
        # test node deletion
        node = pm.createNode('transform')
        cmds.addAttr(node.name(), longName='foobar')
        attr = node.attr('foobar')
        self.assertTrue(attr.exists())
        cmds.delete(node.name())
        self.assertFalse(attr.exists())

        # test attr deletion
        node = pm.createNode('transform')
        cmds.addAttr(node.name(), longName='foobar')
        attr = node.attr('foobar')
        self.assertTrue(attr.exists())
        cmds.deleteAttr(attr.name())
        self.assertFalse(attr.exists())
        cmds.delete(node.name())
        self.assertFalse(attr.exists())

        # test deletion of both
        node = pm.createNode('transform')
        cmds.addAttr(node.name(), longName='foobar')
        attr = node.attr('foobar')
        self.assertTrue(attr.exists())
        cmds.deleteAttr(attr.name())
        cmds.delete(node.name())
        self.assertFalse(attr.exists())


class CapturingHandler(logging.Handler):
    '''Log handler that just records emitted messages'''
    def __init__(self, *args, **kwargs):
        super(CapturingHandler, self).__init__(*args, **kwargs)
        self.capturedMessagesByLevel = {}

    def emit(self, record):
        messages = self.capturedMessagesByLevel.setdefault(record.levelno, [])
        messages.append(record.msg)


class test_deletedNameAccess(unittest.TestCase):

    class SetOptionAndCatchWarnings(object):
        '''Temporarily set deleted_pynode_name_access, and catch warnings
        emitted using the given logger'''
        def __init__(self, newOption, logger=pymel.core.general._logger):
            self.oldOption = None
            self.newOption = newOption
            self.logger = logger
            self.capturingHandler = CapturingHandler(logging.DEBUG)
            self.capturedWarnings = self.capturingHandler.capturedMessagesByLevel.setdefault(logging.WARN, [])
            self.emittedWarnings = []

        def __enter__(self):
            from pymel.internal.startup import pymel_options
            self.oldOption = pymel_options['deleted_pynode_name_access']
            pymel_options['deleted_pynode_name_access'] = self.newOption
            self.logger.addHandler(self.capturingHandler)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            from pymel.internal.startup import pymel_options
            pymel_options['deleted_pynode_name_access'] = self.oldOption
            self.logger.removeHandler(self.capturingHandler)

    def setUp(self):
        cmds.file(new=1, f=1)
        self.name = 'test_obj'
        self.deleted_node = pm.createNode('transform', name=self.name)
        pm.delete(self.deleted_node)
        self.assertFalse(self.deleted_node.exists())

    def test_ignore(self):
        capturer = self.SetOptionAndCatchWarnings('ignore')
        with capturer:
            self.assertEqual(self.deleted_node.name(), self.name)
            self.assertEqual(len(capturer.capturedWarnings), 0)

        # make a joint with the same name
        joint = pm.createNode('joint', name='test_obj')
        self.assertTrue(joint.exists())

        with capturer:
            # delete the original, already-deleted, node
            pm.delete(self.deleted_node)
            self.assertEqual(len(capturer.capturedWarnings), 0)

        # check that the joint was deleted
        self.assertFalse(joint.exists())

    def test_warn(self):
        capturer = self.SetOptionAndCatchWarnings('warn')
        with capturer:
            self.assertEqual(self.deleted_node.name(), self.name)
        self.assertEqual(len(capturer.capturedWarnings), 1)
        self.assertIn('no longer exists', capturer.capturedWarnings[0])

        # make a joint with the same name
        joint = pm.createNode('joint', name='test_obj')
        self.assertTrue(joint.exists())

        with capturer:
            # delete the original, already-deleted, node
            pm.delete(self.deleted_node)
        self.assertEqual(len(capturer.capturedWarnings), 2)
        self.assertIn('no longer exists', capturer.capturedWarnings[1])

        # check that the joint was deleted
        self.assertFalse(joint.exists())

    def test_error(self):
        capturer = self.SetOptionAndCatchWarnings('error')
        with capturer:
            self.assertRaises(pymel.core.DeletedMayaNodeError,
                              self.deleted_node.name)
        self.assertEqual(len(capturer.capturedWarnings), 0)

        # make a joint with the same name
        joint = pm.createNode('joint', name='test_obj')
        self.assertTrue(joint.exists())

        with capturer:
            # delete the original, already-deleted, node
            self.assertRaises(pymel.core.DeletedMayaNodeError,
                              pm.delete, self.deleted_node)
        self.assertEqual(len(capturer.capturedWarnings), 0)

        # check that the joint was NOT deleted
        self.assertTrue(joint.exists())

#suite = unittest.TestLoader().loadTestsFromTestCase(testCase_nodesAndAttributes)
#suite.addTest(unittest.TestLoader().loadTestsFromTestCase(testCase_listHistory))
#unittest.TextTestRunner(verbosity=2).run(suite)
#setupUnittestModule(__name__)



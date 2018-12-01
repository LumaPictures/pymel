import sys
import os
import unittest
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.OpenMayaFX as omfx

import pymel.versions
from pymel.util.testing import TestCaseExtended

if not hasattr(cmds, 'about'):
    import maya.standalone
    maya.standalone.initialize()

#===============================================================================
# Current Bugs
#===============================================================================

# For CURRENT bugs, we PASS is the bug is still present, and FAIL if it goes
# away... this may be counter-intuitive, but it acts as an alert if a bug is
# fixed (so we can possibly get rid of yucky work-around code...)

# Bug report 378211
class TestConstraintAngleOffsetQuery(TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        for cmdName in ('aimConstraint', 'orientConstraint'):
            cube1 = cmds.polyCube()[0]
            cube2 = cmds.polyCube()[0]

            cmd = getattr(cmds, cmdName)
            constraint = cmd(cube1, cube2)[0]

            setVals = (12, 8, 7)
            cmd(constraint, e=1, offset=setVals)
            getVals = tuple(cmd(constraint, q=1, offset=1))

            # self.assertVectorsEqual(setVals, getVals)

            # check that things are BAD!
            try:
                self.assertVectorsEqual(setVals, getVals)
            except AssertionError:
                pass
            else:
                self.fail("TestConstraintAngleOffsetQuery was fixed! Huzzah!")

# Bug report 378192
class TestEmptyMFnNurbsCurve(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        shapeStr = cmds.createNode('nurbsCurve', n="RigWorldShape")
        selList = om.MSelectionList()
        selList.add(shapeStr)
        node = om.MObject()
        selList.getDependNode(0, node)

        mnc = om.MFnNurbsCurve()
        self.assertTrue(mnc.hasObj(node))
#         try:
#             mnc.setObject(node)
#         except Exception:
#             self.fail("MFnNurbs curve doesn't work with empty curve object")

        # check that things are BAD!
        try:
            mnc.setObject(node)
        except Exception:
            pass
        else:
            self.fail("MFnNurbs curve now works with empty curve objects! Yay!")



# Bug report 344037
class TestSurfaceRangeDomain(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        try:
            # create a nurbs sphere
            mySphere = cmds.sphere()[0]
            # a default sphere should have u/v
            # parameter ranges of 0:4/0:8

            # The following selections should
            # result in one of these:
            desiredResults = ('nurbsSphere1.u[2:3][0:8]',
                              'nurbsSphere1.u[2:3][*]',
                              'nurbsSphere1.u[2:3]',
                              'nurbsSphere1.uv[2:3][0:8]',
                              'nurbsSphere1.uv[2:3][*]',
                              'nurbsSphere1.uv[2:3]',
                              'nurbsSphere1.v[0:8][2:3]',
                              'nurbsSphere1.v[*][2:3]')


            # Passes
            cmds.select('nurbsSphere1.u[2:3][*]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Passes
            cmds.select('nurbsSphere1.v[*][2:3]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Fails! - returns 'nurbsSphere1.u[2:3][0:1]'
            cmds.select('nurbsSphere1.u[2:3]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Fails! - returns 'nurbsSphere1.u[2:3][0:1]'
            cmds.select('nurbsSphere1.uv[2:3][*]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # The following selections should
            # result in one of these:
            desiredResults = ('nurbsSphere1.u[0:4][2:3]',
                              'nurbsSphere1.u[*][2:3]',
                              'nurbsSphere1.uv[0:4][2:3]',
                              'nurbsSphere1.uv[*][2:3]',
                              'nurbsSphere1.v[2:3][0:4]',
                              'nurbsSphere1.v[2:3][*]',
                              'nurbsSphere1.v[2:3]')

            # Passes
            cmds.select('nurbsSphere1.u[*][2:3]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Passes
            cmds.select('nurbsSphere1.v[2:3][*]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Fails! - returns 'nurbsSphereShape1.u[0:1][2:3]'
            cmds.select('nurbsSphere1.v[2:3]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)

            # Fails! - returns 'nurbsSphereShape1.u[0:4][0:1]'
            cmds.select('nurbsSphere1.uv[*][2:3]')
            self.assertTrue(cmds.ls(sl=1)[0] in desiredResults)
        except AssertionError:
            pass
        else:
            # check that things are BAD!
            self.fail("Nurbs surface range domain bug fixed!")


# Bug report 345384

# This bug only seems to affect windows (or at least, Win x64 -
# haven't tried on 32-bit).
class TestMMatrixMEulerRotationSetAttr(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        # We expect it to fail on windows, and pass on other operating systems...
        shouldPass = os.name != 'nt'
        try:
            class InfoBaseClass(object):
                # These two are just so we can trace what's going on...
                def __getattribute__(self, name):
                    # don't just use 'normal' repr, as that will
                    # call __getattribute__!
                    print "__getattribute__(%s, %r)" % (object.__repr__(self), name)
                    return super(InfoBaseClass, self).__getattribute__(name)
                def __setattr__(self, name, val):
                    print "__setattr__(%r, %r, %r)" % (self, name, val)
                    return super(InfoBaseClass, self).__setattr__(name, val)

            class MyClass1(InfoBaseClass):
                def __init__(self):
                    self._bar = 'not set'

                def _setBar(self, val):
                    print "setting bar to:", val
                    self._bar = val
                def _getBar(self):
                    print "getting bar..."
                    return self._bar
                bar = property(_getBar, _setBar)

            foo1 = MyClass1()
            # works like we expect...
            foo1.bar = 7
            print "foo1.bar:", foo1.bar
            self.assertTrue(foo1.bar == 7)

            class MyClass2(MyClass1, om.MMatrix): pass

            foo2 = MyClass2()
            foo2.bar = 7
            # Here, on windows, MMatrix's __setattr__ takes over, and
            # (after presumabably determining it didn't need to do
            # whatever special case thing it was designed to do)
            # instead of calling the super's __setattr__, which would
            # use the property, inserts it into the object's __dict__
            # manually
            print "foo2.bar:", foo2.bar
            self.assertTrue(foo2.bar == 7)

            # Starting in Maya2018 (at least on windows?), many wrapped datatypes
            # define a __setattr__ which will work in the "general" case tested
            # above, but will still take precedence if a "_swig_property" is
            # defined - ie, MEulerRotation.order.  Check to see if the apicls has
            # any properties, and ensure that our property still overrides theirs...
            class MyEulerClass1(InfoBaseClass):
                def _setOrder(self, val):
                    print "setting order to:", val
                    self._order = val
                def _getOrder(self):
                    print "getting order..."
                    return self._order
                order = property(_getOrder, _setOrder)

            er1 = MyEulerClass1()
            # works like we expect...
            er1.order = "new order"
            print "er1.order:", er1.order
            self.assertTrue(er1.order == "new order")

            class MyEulerClass2(MyEulerClass1, om.MEulerRotation): pass

            er2 = MyEulerClass2()
            er2.order = "does it work?"
            print "er2.order:", er2.order
            self.assertTrue(er2.order == "does it work?")

        except Exception:
            if shouldPass:
                raise
            else:
                print("MMatrix/MEulerRotation setattr bug is still around...")
        else:
            if not shouldPass:
                self.fail("MMatrix/MEulerRotation setattr bug seems to have"
                          " been fixed!")
            else:
                print("MMatrix/MEulerRotation still functions properly on {},"
                      " as expected".format(os.name))


# Introduced in maya 2014
# Change request #: BSPR-12597
class TestShapeParentInstance(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        try:
            import maya.cmds as cmds

            def getShape(trans):
                return cmds.listRelatives(trans, children=True, shapes=True)[0]

            cmds.file(new=1, f=1)
            shapeTransform = cmds.polyCube(name='singleShapePoly')[0]
            origShape = getShape(shapeTransform)
            dupeTransform1 = cmds.duplicate(origShape, parentOnly=1)[0]
            cmds.parent(origShape, dupeTransform1, shape=True, addObject=True, relative=True)
            dupeTransform2 = cmds.duplicate(dupeTransform1)[0]
            cmds.delete(dupeTransform1)
            dupeShape = getShape(dupeTransform2)

            # In maya 2014, this raises:
            # Error: Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Source is not connected.
            # Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Destination attribute must be writable.
            # Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Destination attribute must be writable.
            # Traceback (most recent call last):
            # File "<maya console>", line 13, in <module>
            # RuntimeError: Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Source is not connected.
            # Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Destination attribute must be writable.
            # Connection not made: 'singleShapePolyShape2.instObjGroups[1]' -> 'initialShadingGroup.dagSetMembers[2]'. Destination attribute must be writable. #

            cmds.parent(dupeShape, shapeTransform, shape=True, addObject=True, relative=True)
        except Exception:
            pass
        else:
            self.fail("ShapeParentInstance bug fixed!")

# This test gives inconsistent results - the bug will show up (meaning the
# unittest "passes") if the test is run by itself (or just this module is run),
# but the bug will not show up (meaning the unittest "fails") if the entire test
# suite is run
@unittest.skip("inconsistent results")
class TestUndoRedoConditionNewFile(unittest.TestCase):
    CONDITION = '_pymel_test_UndoRedoAvailable'

    def setUp(self):
        self.origUndoState = cmds.undoInfo(q=1, state=1)
        # flush the undo queue
        cmds.undoInfo(state=0)
        cmds.undoInfo(state=1)
        cmds.file(new=1, f=1)

        # there seems to be a bug with cmds.scriptJob(listConditions=1) where
        # it returns none from a non-gui session
        import maya.api.OpenMaya as om2
        if self.CONDITION in om2.MConditionMessage.getConditionNames():
            cmds.condition(self.CONDITION, delete=True)

        om.MGlobal.executeCommand('''
        global proc int _test_UndoOrRedoAvailable_proc()
        {
            return (isTrue("UndoAvailable") || isTrue("RedoAvailable"));
        }
        ''', False, False)

        cmds.condition(self.CONDITION, initialize=True,
                       d=['UndoAvailable', 'RedoAvailable'],
                       s='_test_UndoOrRedoAvailable_proc')

    def tearDown(self):
        try:
            cmds.condition(self.CONDITION, delete=True)
        finally:
            if self.origUndoState != cmds.undoInfo(q=1, state=1):
                cmds.undoInfo(state=self.origUndoState)


    def _doTest(self):
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertFalse(cmds.isTrue(self.CONDITION))

        cmds.setAttr('persp.tx', 10)
        cmds.setAttr('top.tx', 10)
        self.assertTrue(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertTrue(cmds.isTrue(self.CONDITION))

        cmds.undo()
        self.assertTrue(cmds.isTrue('UndoAvailable'))
        self.assertTrue(cmds.isTrue('RedoAvailable'))
        self.assertTrue(cmds.isTrue(self.CONDITION))

        # after doing a new file, does UndoOrRedoAvailable reset properly?
        cmds.file(new=1, force=1)
        self.assertFalse(cmds.isTrue('UndoAvailable'))
        self.assertFalse(cmds.isTrue('RedoAvailable'))
        self.assertFalse(cmds.isTrue(self.CONDITION),
            'expected failure here')

    def runTest(self):
        try:
            self._doTest()
        except AssertionError as e:
            if e.args[0] != 'expected failure here':
                raise
        else:
            # check that things are BAD!
            self.fail("UndoRedoCondition with newFile bug fixed!")


class TestScriptJobListConditions(unittest.TestCase):
    def _doTest(self):
        # this seems to return None in non-gui mayapy sessions
        conditions = cmds.scriptJob(listConditions=1)
        self.assertIsNot(conditions, None, 'expected failure here')
        self.assertIn('MayaInitialized', conditions)
        self.assertIn('UndoAvailable', conditions)

    def runTest(self):
        # we only get failures in non-gui
        expectFailure = om.MGlobal.mayaState() not in \
                        (om.MGlobal.kInteractive, om.MGlobal.kBaseUIMode)
        try:
            self._doTest()
        except Exception as e:
            if not expectFailure:
                raise
            if not isinstance(e, AssertionError) or e.args[0] != 'expected failure here':
                raise
        else:
            if expectFailure:
                # check that things are BAD!
                self.fail("scriptJob(listConditions=1) bug fixed!")


#===============================================================================
# Current bugs that will cause Maya to CRASH (and so are commented out!)
#===============================================================================

# This is commented out as it will cause a CRASH - uncomment out (or just
# copy/ paste the relevant code into the script editor) to test if it's still
# causing a crash...

# If you're copy / pasting into a script editor, in order for a crash to occur,
# all lines must be executed at once - if you execute one at a time, there will
# be no crash

# Also, I'm making the code in each of the test functions self-contained (ie,
# has all imports, etc) for easy copy-paste testing...

# class TestSubdivSelectCrash(unittest.TestCase):
#    def testCmds(self):
#        import maya.cmds as cmds
#        cmds.file(new=1, f=1)
#        polyCube = cmds.polyCube()[0]
#        subd = cmds.polyToSubdiv(polyCube)[0]
#        cmds.select(subd + '.sme[*][*]')
#
#    def testApi(self):
#        import maya.cmds as cmds
#        import maya.OpenMaya as om
#
#        polyCube = cmds.polyCube()[0]
#        subd = cmds.polyToSubdiv(polyCube)[0]
#        selList = om.MSelectionList()
#        selList.add(subd + '.sme[*][*]')



#===============================================================================
# FIXED (Former) Bugs
#===============================================================================

# Fixed in Maya 2009! yay!
class TestConstraintVectorQuery(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def _doTestForConstraintType(self, constraintType):
        cmd = getattr(cmds, constraintType)

        if constraintType == 'tangentConstraint':
            target = cmds.circle()[0]
        else:
            target = cmds.polyCube()[0]
        constrained = cmds.polyCube()[0]

        constr = cmd(target, constrained)[0]

        self.assertEqual(cmd(constr, q=1, worldUpVector=1), [0,1,0])
        self.assertEqual(cmd(constr, q=1, upVector=1), [0,1,0])
        self.assertEqual(cmd(constr, q=1, aimVector=1), [1,0,0])

    def test_aimConstraint(self):
        self._doTestForConstraintType('aimConstraint')

    def test_normalConstraint(self):
        self._doTestForConstraintType('normalConstraint')

    def test_tangentConstraint(self):
        self._doTestForConstraintType('tangentConstraint')

# Fixed ! Yay!  (...though I've only check on win64...)
# (not sure when... was fixed by time of 2011 Hotfix 1 - api 201101,
# and still broken in 2009 SP1a - api 200906)
class TestMatrixSetAttr(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        res = cmds.sphere(n='node')
        cmds.addAttr(ln='matrixAttr',dt="matrix")

    def runTest(self):
        cmds.setAttr( 'node.matrixAttr', 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, type='matrix' )

# Bug report 345382
# Fixed ! Yay!  (...though I've only check on win64...)
# (not sure when... was fixed by time of 2011 Hotfix 1 - api 201101,
# and still broken in 2009 SP1a - api 200906)
class TestFluidMFnCreation(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        fluid = cmds.createNode('fluidShape')
        selList = om.MSelectionList()
        selList.add(fluid)
        dag = om.MDagPath()
        selList.getDagPath(0, dag)
        omfx.MFnFluid(dag)

# nucleus node fixed in 2014
# symmetryConstraint fixed in 2015
# transferAttributes fixed <= 2016.5
# jointFFd still broken as of 2019
class TestMFnCompatibility(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)

    def assertInheritMFn(self, nodeType, parentNodeType, mfnEnumName, mfnType):
        if parentNodeType:
            if isinstance(parentNodeType, tuple):
                parentNodeType, concreteParentType = parentNodeType
            else:
                concreteParentType = parentNodeType
            self.assertTrue(
                parentNodeType in cmds.nodeType(nodeType, isTypeName=1,
                                                inherited=True),
                "{} did not have parent {}".format(nodeType, parentNodeType))
            self.assertInheritMFn(concreteParentType, None, mfnEnumName,
                                  mfnType)

        mfnEnum = getattr(om.MFn, mfnEnumName)

        nodeInstName = cmds.createNode(nodeType)
        selList = om.MSelectionList()
        selList.add(nodeInstName)
        mobj = om.MObject()
        selList.getDependNode(0, mobj)

        self.assertTrue(mobj.hasFn(mfnEnum),
                        "{} did not have {}".format(nodeType, mfnEnumName))

        try:
            mfnType(mobj)
        except Exception, e:
            self.fail("{} did not support {}".format(nodeType,
                                                     mfnType.__name__))

    def assertNotInheritMFn(self, nodeType, parentNodeType, mfnEnumName,
                            mfnType):
        try:
            self.assertInheritMFn(nodeType, parentNodeType, mfnEnumName,
                                  mfnType)
        except AssertionError as e:
            # this is expected... swallow it
            pass
        else:
            self.fail("{} passed inheritance test (for {} / {}), when it was"
                      " expceted to fail".format(nodeType, mfnEnumName,
                                                 mfnType.__name__))

    def test_nucleus_MFnDagNode(self):
        self.assertInheritMFn('nucleus', ('dagNode', 'transform'), 'kDagNode',
                              om.MFnDagNode)

    def test_nucleus_MFnTransform(self):
        self.assertInheritMFn('nucleus', 'transform', 'kTransform',
                              om.MFnTransform)

    def test_symmetryConstraint_MFnDagNode(self):
        self.assertInheritMFn('symmetryConstraint', ('dagNode', 'transform'),
                              'kDagNode', om.MFnDagNode)

    def test_symmetryConstraint_MFnTransform(self):
        self.assertInheritMFn('symmetryConstraint', 'transform', 'kTransform',
                              om.MFnTransform)

    def test_jointFfd_ffd(self):
        self.assertInheritMFn('jointFfd', 'ffd', 'kFFD', oma.MFnLatticeDeformer)

    def test_jointFfd_geometryFilter(self):
        self.assertNotInheritMFn(
            'jointFfd', ('geometryFilter', 'softMod'),
            'kGeometryFilt', oma.MFnGeometryFilter)

    def test_transferAttributes_weightGeometryFilter(self):
        self.assertInheritMFn(
            'transferAttributes', ('weightGeometryFilter', 'softMod'),
            'kWeightGeometryFilt', oma.MFnWeightGeometryFilter)

    def test_transferAttributes_geometryFilter(self):
        self.assertInheritMFn(
            'transferAttributes', ('geometryFilter', 'softMod'),
            'kGeometryFilt', oma.MFnGeometryFilter)

    # These probably aren't strictly considered "bugs" by autodesk, though I
    # think they should be...
    def test_hikHandle_ikHandle(self):
        self.assertNotInheritMFn('hikHandle', 'ikHandle', 'kIkHandle',
                                 oma.MFnIkHandle)


# Fixed in 2014! yay!
class TestGroupUniqueness(unittest.TestCase):
    '''Test to check whether cmds.group returns a unique name
    '''
    def setUp(self):
        cmds.file(new=1, f=1)

    def runTest(self):
        cmds.select(cl=1)
        cmds.group(n='foo', empty=1)
        cmds.group(n='bar')
        cmds.select(cl=1)
        res = cmds.group(n='foo', empty=1)
        sameNames = cmds.ls(res)
        if len(sameNames) < 1:
            self.fail('cmds.group did not return a valid name')
        elif len(sameNames) > 1:
            self.fail('cmds.group did not return a unique name')



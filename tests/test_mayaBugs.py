import sys
import unittest
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaFX as fx

from pymel.util.testing import TestCaseExtended

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
            self.assertVectorsEqual(setVals, getVals)

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
        try:
            mnc.setObject(node)
        except Exception:
            self.fail("MFnNurbs curve doesn't work with empty curve object")

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
        fx.MFnFluid(dag)
        
# Bug report 344037
class TestSurfaceRangeDomain(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        
    def runTest(self):
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


# Bug report 345384 

# This bug only seems to affect windows (or at least, Win x64 -
# haven't tried on 32-bit).
class TestMMatrixSetAttr(unittest.TestCase):
    def setUp(self):
        # pymel essentially fixes this bug by wrapping
        # the api's __setattr__... so undo this before testing
        if 'pymel.internal.factories' in sys.modules:
            factories = sys.modules['pymel.internal.factories']
            self.origSetAttr = factories.MetaMayaTypeWrapper._originalApiSetAttrs.get(om.MMatrix, None)
        else:
            self.origSetAttr = None
        if self.origSetAttr:
            self.fixedSetAttr = om.MMatrix.__setattr__
            om.MMatrix.__setattr__ = self.origSetAttr
        cmds.file(new=1, f=1)
        
    def runTest(self):
        class MyClass1(object):
            def __init__(self):
                self._bar = 'not set'
            
            def _setBar(self, val):
                print "setting bar to:", val
                self._bar = val
            def _getBar(self):
                print "getting bar..."
                return self._bar
            bar = property(_getBar, _setBar)
        
            # These two are just so we can trace what's going on...
            def __getattribute__(self, name): 
                # don't just use 'normal' repr, as that will
                # call __getattribute__!
                print "__getattribute__(%s, %r)" % (object.__repr__(self), name)
                return super(MyClass1, self).__getattribute__(name)
            def __setattr__(self, name, val):
                print "__setattr__(%r, %r, %r)" % (self, name, val)
                return super(MyClass1, self).__setattr__(name, val)
        
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
        
    def tearDown(self):
        # Restore the 'fixed' __setattr__'s
        if self.origSetAttr:
            om.MMatrix.__setattr__ = self.fixedSetAttr
        
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
        



# This is commented out as it will cause a CRASH - uncomment out (or just
# copy/ paste the relevant code into the script editor) to test if it's still
# causing a crash...

# If you're copy / pasting into a script editor, in order for a crash to occur,
# all lines must be executed at once - if you execute one at a time, there will
# be no crash

# Also, I'm making the code in each of the test functions self-contained (ie,
# has all imports, etc) for easy copy-paste testing...

#class TestSubdivSelectCrash(unittest.TestCas):
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

      
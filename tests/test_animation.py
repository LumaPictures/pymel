import sys
import unittest
import traceback

import maya.cmds as cmds

import pymel.core as pm
import pymel.util as util
import pymel.util.testing as testing

class TestConstraintVectorQuery(testing.TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)

    def _doTestForConstraintType(self, constraintType):
        cmd = getattr(pm, constraintType)

        if constraintType == 'tangentConstraint':
            target = cmds.circle()[0]
        else:
            target = cmds.polyCube()[0]
        constrained = cmds.polyCube()[0]

        constr = cmd(target, constrained)
        print constr

        self.assertVectorsEqual(cmd(constr, q=1, worldUpVector=1), [0,1,0])
        self.assertVectorsEqual(constr.getWorldUpVector(), [0,1,0])

        self.assertVectorsEqual(cmd(constr, q=1, upVector=1), [0,1,0])
        self.assertVectorsEqual(constr.getUpVector(), [0,1,0])

        self.assertVectorsEqual(cmd(constr, q=1, aimVector=1), [1,0,0])
        self.assertVectorsEqual(constr.getAimVector(), [1,0,0])

    def test_aimConstraint(self):
        self._doTestForConstraintType('aimConstraint')

    def test_normalConstraint(self):
        self._doTestForConstraintType('normalConstraint')

    def test_tangentConstraint(self):
        self._doTestForConstraintType('tangentConstraint')


class TestConstraintWeightSyntax(unittest.TestCase):
    CONSTRAINTS =[
        'aimConstraint',
        'geometryConstraint',
        'normalConstraint',
        'orientConstraint',
        'parentConstraint',
        'pointConstraint',
        'pointOnPolyConstraint',
        'poleVectorConstraint',
        'scaleConstraint',
        'tangentConstraint',
    ]

    def setUp(self):
        cmds.file(new=1, f=1)

    def doWeightQueryTest(self, constraintCmd):
        if constraintCmd == pm.tangentConstraint:
            parentMaker = pm.circle
        else:
            parentMaker = pm.polyCube

        self.parent1 = parentMaker(name='parent1')[0]
        self.parent1.translateX.set(10)
        self.parent1.rotateX.set(10)
        self.parent1.scaleX.set(2)

        self.parent2 = parentMaker(name='parent2')[0]
        self.parent2.translateY.set(10)
        self.parent2.rotateY.set(10)
        self.parent2.scaleY.set(2)

        self.parent3 = parentMaker(name='parent3')[0]
        self.parent3.translateZ.set(10)
        self.parent3.rotateZ.set(10)
        self.parent3.scaleZ.set(2)

        if constraintCmd == pm.poleVectorConstraint:
            joint1 = pm.createNode('joint')
            joint1.translate.set((0, 0, -20))
            joint2 = pm.createNode('joint', parent=joint1)
            joint2.translate.set((10, 10, 0))
            joint3 = pm.createNode('joint', parent=joint2)
            joint3.translate.set((10, -10, 0))
            ikHandle, ikEffector = pm.ikHandle(sj=joint1, ee=joint3)
            self.child = ikHandle
        else:
            self.child = pm.polyCube(name='child')[0]

        constraint = constraintCmd([self.parent1, self.parent2, self.parent3,
                                    self.child])
        constraint.setWeight(1.0, self.parent1)
        constraint.setWeight(2.0, self.parent2)
        constraint.setWeight(3.0, self.parent3)

        self.assertEqual(constraintCmd(constraint, q=1, weight=self.parent1),
                         1.0)
        self.assertEqual(constraintCmd(constraint, q=1, weight=(self.parent1,
                                                                self.parent2)),
                         [1.0, 2.0])
        self.assertEqual(constraintCmd(constraint, q=1, weight=[self.parent1,
                                                                self.parent2]),
                         [1.0, 2.0])
        self.assertEqual(constraintCmd(constraint, q=1, weight=[]),
                         [1.0, 2.0, 3.0])
        self.assertEqual(constraintCmd(constraint, q=1, weight=True),
                         [1.0, 2.0, 3.0])

    @classmethod
    def makeConstraintWeightText(cls, constraintCmdName):
        constraintCmd = getattr(pm, constraintCmdName)
        def testConstraintWeightSyntax(self):
            self.doWeightQueryTest(constraintCmd)

        testConstraintWeightSyntax.__name__ += '_{}'.format(constraintCmdName)
        setattr(cls, testConstraintWeightSyntax.__name__,
                testConstraintWeightSyntax)
        return testConstraintWeightSyntax

for constraint in TestConstraintWeightSyntax.CONSTRAINTS:
    TestConstraintWeightSyntax.makeConstraintWeightText(constraint)


class TestTimeRange(testing.TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.cube = cmds.polyCube()[0]
        for i in xrange(1,21,2):
            cmds.currentTime(i)
            pm.setAttr(self.cube + '.tx', i)
            pm.setKeyframe(self.cube + '.tx')

    def tearDown(self):
        cmds.delete(self.cube)

    @classmethod
    def addTest(cls, func, flag, val, expected):
        # define the test
        def test(self):
            kwargs = {'query':1, 'attribute':'tx', 'keyframeCount':1, flag:val}
            try:
                result = pm.keyframe(self.cube, **kwargs)
            except Exception:
                trace = traceback.format_exc()
                self.fail('Error executing keyframe for %s=%r:\n%s' % (flag, val, trace))
            self.assertEqual(result, expected,
                             "Wrong value for %s=%r - expected %r, got %r" % (flag, val, expected, result))

        # name the test...
        if isinstance(val, basestring):
            valPieces = val.split(':')
        elif isinstance(val, slice):
            valPieces = (val.start, val.stop)
        elif isinstance(val, (list, tuple)):
            valPieces = val
        else:
            valPieces = [val]
        valPieces = ["BLANK" if x == "" else x for x in valPieces]
        if len(valPieces) == 1:
            valName = '%s' % valPieces[0]
        else:
            valName = '%s_%s' % tuple(valPieces)
        valName = '%s_%s' % (type(val).__name__, valName)
        testName = 'test_%s_%s_%s' % (func.__name__, flag, valName)
        test.__name__ = testName

        # add the test to the class
        setattr(cls, testName, test)

    @classmethod
    def addKeyframeTimeTests(cls):
        for val, expected in [
                              ((4,),         0),
                              ((9,),         1),
                              ((None,),     10),
                              ((4,4),        0),
                              ((4,9),        3),
                              ((4,None),     8),
                              ((9,9),        1),
                              ((9,None),     6),
                              ((None,4),     2),
                              ((None,9),     5),
                              ((None,None), 10),

                              ([4,],         0),
                              ([9,],         1),
                              ([None,],     10),
                              ([4,4],        0),
                              ([4,9],        3),
                              ([4,None],     8),
                              ([9,9],        1),
                              ([9,None],     6),
                              ([None,4],     2),
                              ([None,9],     5),
                              ([None,None], 10),


                              ('4:4',        0),
                              ('4:9',        3),
                              ('4:',         8),
                              ('9:9',        1),
                              ('9:',         6),
                              (':4',         2),
                              (':9',         5),
                              (':',         10),

                              (slice(4),          2),
                              (slice(9),          5),
                              (slice(None),      10),
                              (slice(4,4),        0),
                              (slice(4,9),        3),
                              (slice(4,None),     8),
                              (slice(9,9),        1),
                              (slice(9,None),     6),
                              (slice(None,4),     2),
                              (slice(None,9),     5),
                              (slice(None,None), 10),

                              (4,            0),
                              (9,            1),
                             ]:
            cls.addTest(pm.keyframe, 'time', val, expected)
            cls.addTest(pm.keyframe, 't', val, expected)

    @classmethod
    def addKeyframeIndexTests(cls):
        for val, expected in [
                              ((2,),         1),
                              ((8,),         1),
                              ((10,),        0),
                              ((None,),     10),
                              ((10,10),      0),
                              ((2,2),        1),
                              ((2,8),        7),
                              ((2,None),     8),
                              ((8,8),        1),
                              ((8,None),     2),
                              ((None,2),     3),
                              ((None,8),     9),
                              ((None,None), 10),

                              ([2,],         1),
                              ([8,],         1),
                              ([None,],     10),
                              ([10,10],      0),
                              ([2,2],        1),
                              ([2,8],        7),
                              ([2,None],     8),
                              ([8,8],        1),
                              ([8,None],     2),
                              ([None,2],     3),
                              ([None,8],     9),
                              ([None,None], 10),


                              ('10:10',      0),
                              ('2:2',        1),
                              ('2:8',        7),
                              ('2:',         8),
                              ('8:8',        1),
                              ('8:',         2),
                              (':2',         3),
                              (':8',         9),
                              (':',         10),

                              (slice(2),          3),
                              (slice(8),          9),
                              (slice(None),      10),
                              (slice(2,2),        1),
                              (slice(2,8),        7),
                              (slice(2,None),     8),
                              (slice(8,8),        1),
                              (slice(8,None),     2),
                              (slice(None,2),     3),
                              (slice(None,8),     9),
                              (slice(None,None), 10),

                              (4,            1),
                              (9,            1),
                             ]:
            cls.addTest(pm.keyframe, 'index', val, expected)

TestTimeRange.addKeyframeTimeTests()
TestTimeRange.addKeyframeIndexTests()

class TestJoint(testing.TestCaseExtended):

    def setUp(self):
        cmds.file(new=1, f=1)

    def test_angleX(self):
        joint = pm.joint(angleX=31.5)
        self.assertEqual(pm.joint(joint, q=1, angleX=1), 31.5)
        pm.joint(joint, e=1, angleX=20.2)
        self.assertEqual(pm.joint(joint, q=1, angleX=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(ax=31.5)
        self.assertEqual(pm.joint(joint, q=1, ax=1), 31.5)
        pm.joint(joint, e=1, ax=20.2)
        self.assertEqual(pm.joint(joint, q=1, ax=1), 20.2)
        pm.delete(joint)

    def test_angleY(self):
        joint = pm.joint(angleY=31.5)
        self.assertEqual(pm.joint(joint, q=1, angleY=1), 31.5)
        pm.joint(joint, e=1, angleY=20.2)
        self.assertEqual(pm.joint(joint, q=1, angleY=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(ay=31.5)
        self.assertEqual(pm.joint(joint, q=1, ay=1), 31.5)
        pm.joint(joint, e=1, ay=20.2)
        self.assertEqual(pm.joint(joint, q=1, ay=1), 20.2)
        pm.delete(joint)

    def test_angleZ(self):
        joint = pm.joint(angleZ=31.5)
        self.assertEqual(pm.joint(joint, q=1, angleZ=1), 31.5)
        pm.joint(joint, e=1, angleZ=20.2)
        self.assertEqual(pm.joint(joint, q=1, angleZ=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(az=31.5)
        self.assertEqual(pm.joint(joint, q=1, az=1), 31.5)
        pm.joint(joint, e=1, az=20.2)
        self.assertEqual(pm.joint(joint, q=1, az=1), 20.2)
        pm.delete(joint)

    def test_radius(self):
        joint = pm.joint(radius=31.5)
        self.assertEqual(pm.joint(joint, q=1, radius=1), 31.5)
        pm.joint(joint, e=1, radius=20.2)
        self.assertEqual(pm.joint(joint, q=1, radius=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(rad=31.5)
        self.assertEqual(pm.joint(joint, q=1, rad=1), 31.5)
        pm.joint(joint, e=1, rad=20.2)
        self.assertEqual(pm.joint(joint, q=1, rad=1), 20.2)
        pm.delete(joint)

    def test_stiffnessX(self):
        joint = pm.joint(stiffnessX=31.5)
        self.assertEqual(pm.joint(joint, q=1, stiffnessX=1), 31.5)
        pm.joint(joint, e=1, stiffnessX=20.2)
        self.assertEqual(pm.joint(joint, q=1, stiffnessX=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(stx=31.5)
        self.assertEqual(pm.joint(joint, q=1, stx=1), 31.5)
        pm.joint(joint, e=1, stx=20.2)
        self.assertEqual(pm.joint(joint, q=1, stx=1), 20.2)
        pm.delete(joint)

    def test_stiffnessY(self):
        joint = pm.joint(stiffnessY=31.5)
        self.assertEqual(pm.joint(joint, q=1, stiffnessY=1), 31.5)
        pm.joint(joint, e=1, stiffnessY=20.2)
        self.assertEqual(pm.joint(joint, q=1, stiffnessY=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(sty=31.5)
        self.assertEqual(pm.joint(joint, q=1, sty=1), 31.5)
        pm.joint(joint, e=1, sty=20.2)
        self.assertEqual(pm.joint(joint, q=1, sty=1), 20.2)
        pm.delete(joint)

    def test_stiffnessZ(self):
        joint = pm.joint(stiffnessZ=31.5)
        self.assertEqual(pm.joint(joint, q=1, stiffnessZ=1), 31.5)
        pm.joint(joint, e=1, stiffnessZ=20.2)
        self.assertEqual(pm.joint(joint, q=1, stiffnessZ=1), 20.2)
        pm.delete(joint)

        joint = pm.joint(stz=31.5)
        self.assertEqual(pm.joint(joint, q=1, stz=1), 31.5)
        pm.joint(joint, e=1, stz=20.2)
        self.assertEqual(pm.joint(joint, q=1, stz=1), 20.2)
        pm.delete(joint)


class test_ikHandle(unittest.TestCase):
    def test_nonUniqueName(self):
        cmds.file(f=1, new=1)

        j1 = cmds.createNode('joint', name='j1')
        j2 = cmds.createNode('joint', name='j2', parent=j1)
        j3 = cmds.createNode('joint', name='j3', parent=j2)
        j4 = cmds.createNode('joint', name='j4', parent=j3)
        cmds.select(j1, j4)
        ikh1 = pm.ikHandle(name='ikh')
        self.assertEqual(len(ikh1), 2)
        self.assertTrue(isinstance(ikh1[0], pm.nt.IkHandle))
        self.assertTrue(isinstance(ikh1[1], pm.nt.IkEffector))
        self.assertEqual(ikh1[0].nodeName(), 'ikh')

        pm.group(ikh1, name='theGroup')

        self.assertEqual(cmds.ls('*ikh', long=True), ['|theGroup|ikh'])

        j3 = cmds.createNode('joint', name='j3')
        j4 = cmds.createNode('joint', name='j4', parent=j3)
        cmds.select(j3, j4)
        ikh2 = pm.ikHandle(name='ikh')

        self.assertEqual(len(ikh2), 2)
        self.assertTrue(isinstance(ikh2[0], pm.nt.IkHandle))
        self.assertTrue(isinstance(ikh2[1], pm.nt.IkEffector))
        self.assertEqual(ikh2[0].nodeName(), 'ikh')


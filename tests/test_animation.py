import sys
import unittest
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



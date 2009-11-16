import unittest
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaFX as fx

class testCase_fluidMFn(unittest.TestCase):
    def setUp(self):
        cmds.file(new=1, f=1)
        
    def runTest(self):
        fluid = cmds.createNode('fluidShape')
        selList = om.MSelectionList()
        selList.add(fluid)
        dag = om.MDagPath()
        selList.getDagPath(0, dag)
        fx.MFnFluid(dag)
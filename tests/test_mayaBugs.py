import unittest
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaFX as fx

# Bug report 345382
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


        
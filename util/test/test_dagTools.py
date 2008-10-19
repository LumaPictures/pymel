import sys, os, os.path, inspect, unittest
from pymel.examples.dagTools import *
import pymel.util as util
from pymel.util.trees import *

# TODO: check this out, get it working!

# Test case: several tests that share the same setup (here same Maya scene for testing for instance)
# Warning: unittest runs test in their name alphabetic order, so if a specific order is desire it must
# appear in the name

class testCase_typeChecking(unittest.TestCase):

    def setUp(self):
        # define a list of objects to create either as a callable or a maya types
        obj = ['pointLight', 'locator', 'transform', 'mesh', 'camera', 'objectSet', 'lambert', 'multiplyDivide', 'polyCube', spaceLocator, polyCube] #@UndefinedVariable
        # expected results
        self.expected = {}
        self.expected['isDag'] = [True, True, True, True, True, False, False, False, False, True, [True, False]]
        # store the list of created objects
        sl = []
        # store the types for checking
        pt = []
        mt = []
        # Create the objects for testing
        for k in obj :
            c = cPt = cMt = []
            # AMcommands.MayaCmds().has_key(k) no good, confusion between types and commands
            # ie polyCube command and polyCube type
            if callable(k) :
                c = k()
            else :
                c = createNode(k) #@UndefinedVariable
            if not util.isIterable(c) :
                c = [c]
            cPt = map(type, c)
            cMt = map(nodeType, c) #@UndefinedVariable
            sl += c
            pt += cPt
            mt += cMt
        self.objects = sl
        self.pymelTypes = pt
        self.mayaTypes = mt
        
    def test01_isDagOnObjects(self):
        # excepted result
        expect = util.expandArgs(self.expected['isDag'])
        # tests
        objTest = isDag(self.objects)
        self.assertEqual(objTest, expect)
        
    def test02_isDagOnMayaTypes(self):
        expect = util.expandArgs(self.expected['isDag'])         
        mayatypeTest = isDag(map(nodeType, self.objects)) #@UndefinedVariable
        self.assertEqual(mayatypeTest, expect)
        
    def test03_isDagOnPymelTypes(self):
        expect = util.expandArgs(self.expected['isDag'])         
        pymeltypeTest = isDag(map(type, self.objects))
        self.assertEqual(pymeltypeTest, expect)
        
    def test04_isDagOnNames(self):
        expect = util.expandArgs(self.expected['isDag'])      
        nameTest = isDag(map(str, self.objects))
        self.assertEqual(nameTest, expect)
        
    def test05_isDagOnPymelTypesNames(self):        
        expect = util.expandArgs(self.expected['isDag']) 
        pymeltypenameTest = isDag(map(lambda x:unicode(type(x).__name__), self.objects))
        self.assertEqual(pymeltypenameTest, expect)
        
    def tearDown(self):
        # cleaning
        delete(self.objects) #@UndefinedVariable
       
       
class testCase_hierarchyTrees(unittest.TestCase):
    def setUp(self):

        cmds.file(os.path.join(util.moduleDir(), "examples", "skel.ma"), f=True, typ="mayaAscii",o=True)
        select ('FBX_Hips', replace=True, hierarchy=True)
        self.sel = ls(selection=True)
        self.tree = Tree(Joint('FBX_Hips'), Tree(Joint('FBX_Spine'), Tree(Joint('FBX_Spine1'), Tree(Joint('FBX_Spine2'), Tree(Joint('FBX_Spine3'), Tree(Joint('FBX_Neck'), Tree(Joint('FBX_Neck1'), Tree(Joint('FBX_Head'), \
                    Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))), Tree(Joint('FBX_NeckRoll'))), Tree(Joint('FBX_LeftShoulder'), Tree(Joint('FBX_LeftArm'), Tree(Joint('FBX_LeftForeArm'), Tree(Joint('FBX_LeftHand'), \
                    Tree(Joint('FBX_LeftHandThumb1'), Tree(Joint('FBX_LeftHandThumb2'), Tree(Joint('FBX_LeftHandThumb3'), Tree(Joint('FBX_LeftHandThumb4'))))), Tree(Joint('FBX_LeftHandMiddle0'), Tree(Joint('FBX_LeftHandMiddle1'), \
                    Tree(Joint('FBX_LeftHandMiddle2'), Tree(Joint('FBX_LeftHandMiddle3'), Tree(Joint('FBX_LeftHandMiddle4')))))), Tree(Joint('FBX_LeftHandRoll'))), Tree(Joint('FBX_LeftElbowRoll'), Tree(Joint('FBX_LeftElbowRoll_End'))), \
                    Tree(Joint('FBX_LeftForeArmRoll')), Tree(Joint('FBX_LeftForeArmRoll1'))), Tree(Joint('FBX_LeftArmRoll')))), Tree(Joint('FBX_RightShoulder'), Tree(Joint('FBX_RightArm'), Tree(Joint('FBX_RightForeArm'), Tree(Joint('FBX_RightHand'), \
                    Tree(Joint('FBX_RightHandThumb1'), Tree(Joint('FBX_RightHandThumb2'), Tree(Joint('FBX_RightHandThumb3'), Tree(Joint('FBX_RightHandThumb4'))))), Tree(Joint('FBX_RightHandMiddle0'), Tree(Joint('FBX_RightHandMiddle1'), \
                    Tree(Joint('FBX_RightHandMiddle2'), Tree(Joint('FBX_RightHandMiddle3'), Tree(Joint('FBX_RightHandMiddle4')))))), Tree(Joint('FBX_RightHandRoll'))), Tree(Joint('FBX_RightElbowRoll'), Tree(Joint('FBX_RightElbowRoll_End'))), \
                    Tree(Joint('FBX_RightForeArmRoll')), Tree(Joint('FBX_RightForeArmRoll1'))), Tree(Joint('FBX_RightArmRoll')))))))), Tree(Joint('FBX_LeftUpLeg'), Tree(Joint('FBX_LeftLeg'), Tree(Joint('FBX_LeftFoot'), Tree(Joint('FBX_LeftToeBase'), \
                    Tree(Joint('FBX_LeftToes_End'))), Tree(Joint('FBX_LeftFootRoll'))), Tree(Joint('FBX_LeftKneeRoll'), Tree(Joint('FBX_LeftKneeRoll_End')))), Tree(Joint('FBX_LeftUpLegRoll'))), Tree(Joint('FBX_RightUpLeg'), Tree(Joint('FBX_RightLeg'), \
                    Tree(Joint('FBX_RightFoot'), Tree(Joint('FBX_RightToeBase'), Tree(Joint('FBX_RightToes_End'))), Tree(Joint('FBX_RightFootRoll'))), Tree(Joint('FBX_RightKneeRoll'), Tree(Joint('FBX_RightKneeRoll_End')))), Tree(Joint('FBX_RightUpLegRoll')))) # 

    def test01_build(self) :
        """ Check asHierarchy build """
        skel = asHierarchy (self.sel)
        self.assertEqual(self.tree, skel)
    def test02_iterate(self):
        """ Test preorder iterator """
        self.assertEqual(self.sel, [k for k in self.tree])            
    def test03_findMethod(self):
        """ Check if the find method returns correct sub tree for every objects of the hierarchy tree """
        for obj in self.sel :
            select (obj, replace=True, hierarchy=True)
            sub=asHierarchy (ls(selection=True))
            self.assertEqual(self.tree.find(obj), sub)
    def test04_parentObjectMethod(self):
        """ Check if the parent method returns correct object for every objects of the hierarchy tree """
        for obj in self.sel :
            parents = listRelatives (obj, parent=True)
            if parents :
                p = parents[0]
            else :
                p = None
            self.assertEqual(self.tree.parent(obj), p)       
    def test05_parentSubtreeMethod(self):
        """ Check if the parent method returns correct subtree for every subtree of the hierarchy tree """
        for obj in self.sel :
            parents = listRelatives (obj, parent=True)
            if parents :
                select (parents[0], replace=True, hierarchy=True)
                subParent = asHierarchy (ls(selection=True))
            else :
                subParent =  None            
            select (obj, replace=True, hierarchy=True)
            sub=asHierarchy (ls(selection=True))
            self.assertEqual(self.tree.parent(sub), subParent)             
    def tearDown(self):
        select ('FBX_Hips', replace=True, hierarchy=True)
        delete (ls(selection=True))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testCase_typeChecking))
    suite.addTest(unittest.makeSuite(testCase_hierarchyTrees))
    return suite        

if __name__ == '__main__':
    unittest.main()
    
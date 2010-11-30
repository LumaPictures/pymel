import unittest
import tempfile
import shutil
from pymel.all import *

class testCase_references(unittest.TestCase):

    def setUp(self):
        print "getting temp dir"
        self.temp = os.path.join(tempfile.gettempdir(), 'referencesTest')
        if not os.path.isdir(self.temp):
            os.makedirs(self.temp)
        
        # create sphere file
        print "sphere file"
#        cmds.file(new=1, f=1)
        newFile(f=1)
        sphere = polySphere()
        # We will use this to test failed ref edits...
        addAttr(sphere, ln='zombieAttr')
        self.sphereFile = saveAs( os.path.join( self.temp, 'sphere.ma' ), f=1 )
        
        # create cube file
        print "cube file"
        newFile(f=1)
        polyCube()
        createReference( self.sphereFile, namespace='sphere' )
        PyNode('sphere:pSphere1').attr('translateX').set(2)
        self.cubeFile = saveAs( os.path.join( self.temp, 'cube.ma' ), f=1 )
        
        # create cone file
        print "cone file"
        newFile(f=1)
        polyCone()
        createReference( self.cubeFile, namespace='cubeInCone' )
        PyNode('cubeInCone:pCube1').attr('translateZ').set(2)
        PyNode('cubeInCone:sphere:pSphere1').attr('translateZ').set(2)
        self.coneFile = saveAs( os.path.join( self.temp, 'cone.ma' ), f=1 )
        
        print "master file"
        newFile(f=1)
        self.sphereRef1 = createReference( self.sphereFile, namespace='sphere1' )
        PyNode('sphere1:pSphere1').attr('translateY').set(2)
        self.sphereRef2 = createReference( self.sphereFile, namespace='sphere2' )
        PyNode('sphere2:pSphere1').attr('translateY').set(4)
        self.cubeRef1 = createReference( self.cubeFile, namespace='cube1' )
        PyNode('cube1:sphere:pSphere1').attr('translateY').set(6)
        PyNode('cube1:pCube1').attr('translateY').set(6)
        self.coneRef1 = createReference( self.coneFile, namespace='cone1' )
        
    def test_iterRefs_depth(self):
        # Test that each subsequent ref is either a child of the previous ref,
        # or the sibling of of some ref higher in the stack'''
        refStack = []
        for ref in iterReferences(recursive=True):
            splitNS = ref.fullNamespace.split(':')
            if len(splitNS) <= len(refStack):
                refStack = refStack[:len(splitNS) - 1]
            
            self.assertEqual(splitNS[:-1], refStack)
            refStack.append(ref.namespace)

    def test_iterRefs_breadth(self):
        # Test that each subsequent ref is has a recursive depth >= the
        # previous ref
        refDepth = 0
        for ref in iterReferences(recursive=True, recurseType='breadth'):
            splitNS = ref.fullNamespace.split(':')
            thisDepth = len(splitNS)
            self.assertTrue(thisDepth >= refDepth)
            refDepth = thisDepth

    def test_basic_file_cmds(self):
        print "Exporting all", os.path.join( self.temp, 'all.ma' )
        expFile = exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)
        print "Importing"
        impFile = importFile( expFile )
        print "Exporting all" 
        exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)
        print "Exporting animation"
        exportAnim( os.path.join( self.temp, 'anim.ma' ), force=1)
        select(SCENE.persp)
        print "Exporting selected animation"
        exportSelectedAnim( os.path.join( self.temp, 'selAnim.ma' ), force=1)
    
    def test_file_reference(self):
        self.assert_( isinstance( self.sphereRef1, FileReference ) )
        self.assert_( isinstance( self.sphereRef1.refNode, PyNode ) )
        self.assert_( self.sphereRef1.namespace == 'sphere1' )
        self.assert_( self.sphereRef1.isLoaded() )
        self.sphereRef1.unload()
        self.assert_( self.sphereRef1.isDeferred() )
        self.sphereRef1.load()
        self.sphereRef1.exportAnim( os.path.join( self.temp, 'refAnim.ma' ), force=1 )
        select( self.sphereRef1.nodes() )
        self.sphereRef1.exportSelectedAnim( os.path.join( self.temp, 'selRefAnim.ma' ), force=1 )
        self.sphereRef1.remove()
        self.sphereRef2.importContents()

    def test_file_reference_creation(self):
        for ref in listReferences(recursive=True):
            self.assertEqual(ref, FileReference(PyNode(ref.refNode)))
            self.assertEqual(ref, FileReference(str(ref.refNode)))
            self.assertEqual(ref, FileReference(Path(ref.withCopyNumber())))
            self.assertEqual(ref, FileReference(str(ref.withCopyNumber())))
            self.assertEqual(ref, FileReference(namespace=ref.fullNamespace))

    def test_failed_ref_edits(self):
        # Animate the zombieAttrs
        for transform in [x.getParent() for x in ls(type='mesh')]:
            try:
                zombie = transform.attr('zombieAttr')
            except MayaAttributeError:
                continue
            zombie.setKey(t=1, v=1)
            zombie.setKey(t=2, v=2)
            zombie.setKey(t=3, v=4)
        self.masterFile = saveAs( os.path.join( self.temp, 'master.ma' ), f=1 )
        
        openFile(self.sphereFile, f=1)
        SCENE.pSphere1.zombieAttr.delete()
        saveFile(f=1)
        
        # deleting the attr should give some failed ref edits...
        openFile(self.masterFile, f=1)
        
        sphereRefs = [x for x in listReferences(recursive=True)
                      if x.path.endswith('sphere.ma')]
        for ref in sphereRefs:
            print "testing failed ref edits on: %s" % ref
            self.assertEqual(1, len(referenceQuery(ref,successfulEdits=False,failedEdits=True,es=True)))
            self.assertEqual(1, len(cmds.referenceQuery(str(ref.refNode), successfulEdits=False,failedEdits=True,es=True)))
        
    def tearDown(self):
        newFile(f=1)
        shutil.rmtree(self.temp, ignore_errors =True)
        
class testCase_fileInfo(unittest.TestCase):
    def setUp(self):
        newFile(f=1)
        cmds.fileInfo('testKey', 'testValue')
        
    def test_get(self):
        default = "the default value!"
        self.assertEqual(fileInfo.get('NoWayDoIExist', default), default)
        self.assertEqual(fileInfo.get('NoWayDoIExist'), None)
        self.assertEqual(fileInfo.get('testKey'), cmds.fileInfo('testKey', q=1)[0])
        
    def test_getitem(self):
        self.assertRaises(KeyError, lambda: fileInfo['NoWayDoIExist'])
        self.assertEqual(fileInfo['testKey'], cmds.fileInfo('testKey', q=1)[0])

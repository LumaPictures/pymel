import unittest
from pymel import *

class testCase_references(unittest.TestCase):

    def setUp(self):
        self.temp = util.getTempDir()
        
        # create sphere file
        newFile(f=1)
        polySphere()
        self.sphereFile = saveAs( os.path.join( self.temp, 'sphere.ma' ), f=1 )
        
        # create cube file
        newFile(f=1)
        polyCube()
        createReference( self.sphereFile, namespace='sphere' )
        self.cubeFile = saveAs( os.path.join( self.temp, 'cube.ma' ), f=1 )
        
        newFile(f=1)
        self.sphereRef1 = createReference( self.sphereFile, namespace='sphere1' )
        self.sphereRef2 = createReference( self.sphereFile, namespace='sphere2' )
        self.cubeRef1 = createReference( self.cubeFile, namespace='cube1' )

    def test_basic_file_cmds(self):
        
        expFile = exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)

        impFile = importFile( expFile ) 
        exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)
        exportAnim( os.path.join( self.temp, 'anim.ma' ), force=1)
        select(SCENE.persp)
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
        
    def tearDown(self):
        newFile(f=1)


class testCase_references(unittest.TestCase):

    def setUp(self):
        # create sphere file
        newFile(f=1)
        polySphere()
        self.sphereFile = saveAs( os.path.join( temp, 'sphere.ma' ), f=1 )
        
        # create sphere file
        newFile(f=1)
        polyCube()
        createReference( sphereFile, namespace='sphere' )
        self.cubeFile = saveAs( os.path.join( temp, 'cube.ma' ), f=1 )
        
        newFile(f=1)
        self.sphereRef1 = createReference( sphereFile, namespace='sphere1' )
        self.sphereRef2 = createReference( sphereFile, namespace='sphere2' )
        self.cubeRef1 = createReference( cubeFile, namespace='cube1' )

    
    
    def tearDown(self):
        newFile(f=1)
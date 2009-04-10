import unittest

from pymel import *
from pymel.tools.pymelControlPanel import getClassHierarchy
from pymel.core.factories import ApiEnumsToPyComponents

def getFundamentalTypes():
    classList = sorted( list( set( [ key[0] for key in api.apiToMelData.keys()] ) ) )
    leaves = [ util.capitalize(x.key) for x in factories.nodeHierarchy.leaves() ]
    return sorted( set(classList).intersection(leaves) )

EXCEPTIONS = ['MotionPath','OldBlindDataBase', 'TextureToGeom']
 
class testCase_attribs(unittest.TestCase):
    def setUp(self):
        newFile(f=1)
        self.sphere1, hist = polySphere()
        
        class AttributeData(object):
            node = self.sphere1
            
            def __init__(self, name, **initArgs):
                self.name = name
                self.initArgs = initArgs
                
            def add(self):
                addAttr(self.node, longName=self.name, **self.initArgs)
        
        self.newAttrs = [
                        AttributeData('multiByte', multi=True, attributeType='byte'),
                        AttributeData('compound', attributeType='compound', numberOfChildren=3),
                        AttributeData('compound_multiFloat', attributeType='float', multi=True, parent='compound'),
                        AttributeData('compound_double', attributeType='double', parent='compound'),
                        AttributeData('compound_compound', attributeType='compound', numberOfChildren=2, parent='compound'),
                        AttributeData('compound_compound_matrix', attributeType='matrix', parent='compound_compound'),
                        AttributeData('compound_compound_long', attributeType='long', parent='compound_compound'),
                        ]

        for attr in self.newAttrs:
            attr.add()
            
        self.newAttrs = dict([(newAttr.name, Attribute(str(self.sphere1) + "." + newAttr.name)) for newAttr in self.newAttrs ])
        
        self.setMultiElement = self.newAttrs['multiByte'][1]
        self.setMultiElement.set(1)
        
        self.unsetMultiElement = self.newAttrs['multiByte'][3]
        
    def tearDown(self):
        delete(self.sphere1)
        
    def test_newAttrsExists(self):
        for attr in self.newAttrs.itervalues():
#            print "Testing existence of:", attr.name()
            self.assertTrue(attr.exists())
            
    def test_setMultiElementExists(self):
        self.assertTrue(self.setMultiElement.exists())
            
    def test_unsetMultiElementExists(self):
        self.assertFalse(self.unsetMultiElement.exists())
        
    def test_getParent(self):
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(), self.newAttrs['compound_compound'])
                
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(0), self.newAttrs['compound_compound_long'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=1), self.newAttrs['compound_compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(2), self.newAttrs['compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=3), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-1), self.newAttrs['compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=-2), self.newAttrs['compound_compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-3), self.newAttrs['compound_compound_long'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=-4), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-5), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=4), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-63), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=32), None)        

     
def testInvertibles():
    classList = getFundamentalTypes()
    print classList
    for pynodeName in classList:
        try:
            pynode = getattr( core.nodetypes, pynodeName )
        except AttributeError:
            print "could not find", pynodeName
            continue
        
        if not issubclass( pynode, PyNode ) or pynodeName in EXCEPTIONS:
            continue

        if issubclass(pynode, GeometryShape):
            if pynode == Mesh :
                obj = polyCube()[0].getShape()
                obj.createColorSet( 'thingie' )
            elif pynode == Subdiv:
                obj = polyToSubdiv( polyCube()[0].getShape())[0].getShape()
            elif pynode == NurbsSurface:
                obj = sphere()[0].getShape()
            elif pynode == NurbsCurve:
                obj = circle()[0].getShape()
            else:
                print "skipping shape", pynode
                continue
        else:
            obj = createNode( util.uncapitalize(pynodeName) )
        
        print repr(obj)
    
        for className, apiClassName in getClassHierarchy(pynodeName):
            
            if apiClassName not in api.apiClassInfo:
                continue
            
            #print className, apiClassName
            
            classInfo = api.apiClassInfo[apiClassName]
            invertibles = classInfo['invertibles']
            #print invertibles
    
                            
            for setMethod, getMethod in invertibles:
                info = classInfo['methods'][setMethod]
                try:
                    setMethod = info[0]['pymelName']
                except KeyError: pass
                
                setMethod, data = factories._getApiOverrideNameAndData( className, setMethod )
                try:
                    overloadIndex = data['overloadIndex']
                    info = info[overloadIndex]
                except (KeyError, TypeError): pass
                else:
                    # test if this invertible has been broken in pymelControlPanel
                    if not info['inverse']:
                        continue
                    
                    try:
                        setter = getattr( pynode, setMethod )                      
                    except AttributeError: pass
                    else:
                        def getType(type):
                            typeMap = {   'bool' : True,
                                'double' : 2.5, # min required for setFocalLength
                                'double3' : ( 1.0, 2.0, 3.0),
                                'MEulerRotation' : ( 1.0, 2.0, 3.0),
                                'float': 2.5,
                                'MFloatArray': [1.1, 2.2, 3.3],
                                'MString': 'thingie',
                                'float2': (.1, .2),
                                'MPoint' : [1,2,3],
                                'short': 1,
                                'MColor' : [1,0,0],
                                'MColorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0] ),
                                'MVector' : [1,0,0],
                                'MVectorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0] ),
                                'int' : 1,
                                'MIntArray': [1,2,3],
                                'MSpace.Space' : 'world'
                            }
                            if '.' in type:
                                return 1 # take a dumb guess at an enum
                            else:
                                return typeMap[type]
                            
                        inArgs = [ arg for arg in info['inArgs'] if arg not in info['defaults'] ]
                        types = [ str(info['types'][arg]) for arg in inArgs ]
                        try:
                            if apiClassName == 'MFnMesh' and setMethod == 'setUVs':
                                args = [ [.1]*obj.numUVs(), [.2]*obj.numUVs() ]
                            elif apiClassName == 'MFnMesh' and setMethod == 'setColors':
                                args = [ [ [.5,.5,.5] ]*obj.numColors() ]
                            elif apiClassName == 'MFnMesh' and setMethod == 'setColor':
                                obj.setColors( [ [.5,.5,.5] ]*obj.numVertices() )
                                args = [ 1, [1,0,0] ] 
                            elif apiClassName == 'MFnMesh' and setMethod in ['setFaceVertexColors', 'setVertexColors']:
                                obj.createColorSet(setMethod + '_ColorSet' )
                                args = [ ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]), [1, 2, 3] ]
                            
                            elif apiClassName == 'MFnNurbsCurve' and setMethod == 'setKnot':
                                args = [ 6, 4.5 ]
                            else:
                                args = [ getType(typ) for typ in types ]
                            descr =  '%s.%s(%s)' % ( pynodeName, setMethod, ', '.join( [ repr(x) for x in args] ) )
    #                            try:
    #                                setter( obj, *args )
    #                            except Exception, e:
    #                                print str(e)
                            args = [obj] + args
                            def checkSetter( setter, args ):
                                setter( *args )
                                if Version.current > Version.v85sp1:
                                    mel.undo()
                            checkSetter.description = descr
                            yield checkSetter, setter, args
                        except KeyError, msg:
                            print str(msg)
        try: 
            delete( obj )
        except:
            pass

# TODO: add tests for slices

def makePynodeCreationTests(compCreator):
    """
    Outputs a function suitable for use as a unittest test that test creation of components.
    
    For every component in self.compNames / compObjs, it will call 'compCreator(self, compName, compObj)'.
    compCreator should try to create a component, and raise an exception if it fails.
    
    If any component cannot be created, the test will fail, and output a list of the components that
    could not be made in the fail message.
    """
    
    def test_makePyNodes(self):
        failedComps = []
        for compType in self.compNames:
            compName = self.compNames[compType]
            compObj = self.compObjs[compType]
            try:
                compCreator(self, compName, compObj)
            except:
                failedComps.append("%s (%s)" % (compName, compObj.apiTypeStr() ))                
            
        if failedComps:
            self.fail('Could not create following components:\n   ' + '\n   '.join(failedComps))
            
    return test_makePyNodes

class testCase_components(unittest.TestCase):
    @classmethod     
    def getComponentTypes(cls):
        mfnCompBase = api.MFnComponent()
        mfnCompTypes = (api.MFnSingleIndexedComponent(),
                        api.MFnDoubleIndexedComponent(),
                        api.MFnTripleIndexedComponent(),
                        api.MFnUint64SingleIndexedComponent())
        
        componentTypes = {}
        for compType in mfnCompTypes + (mfnCompBase,):
            componentTypes[compType.type()] = []

        for apiEnum in api.ApiEnumsToApiTypes():
            if mfnCompBase.hasObj(apiEnum):
                for compType in mfnCompTypes:
                    if compType.hasObj(apiEnum):
                        break
                else:
                    compType = mfnCompBase
                componentTypes[compType.type()].append(apiEnum)
                    
        return componentTypes
    
    @classmethod
    def printComponentTypes(cls):
        # Output
#        kComponent :
#             kCurveParamComponent
#             kIsoparmComponent
#             kPivotComponent
#             kEdgeComponent
#             kSurfaceRangeComponent
#             kDecayRegionCapComponent
#             kSetGroupComponent
#        kSingleIndexedComponent :
#             kCurveCVComponent
#             kCurveEPComponent
#             kCurveKnotComponent
#             kMeshEdgeComponent
#             kMeshPolygonComponent
#             kMeshVertComponent
#             kDynParticleSetComponent
#             kMeshMapComponent
#             kSubdivMapComponent
#        kDoubleIndexedComponent :
#             kSurfaceCVComponent
#             kSurfaceEPComponent
#             kSurfaceKnotComponent
#             kMeshVtxFaceComponent
#             kSurfaceFaceComponent
#        kTripleIndexedComponent :
#             kLatticeComponent
#        kUint64SingleIndexedComponent :
#             kSubdivCVComponent
#             kSubdivEdgeComponent
#             kSubdivFaceComponent        
        compTypes = cls.getComponentTypes()
        for compType, compList in compTypes.iteritems():
            print api.ApiEnumsToApiTypes()[compType], ":"
            for exactComp in compList:
                print "    ", api.ApiEnumsToApiTypes()[exactComp]
    
    def setUp(self):
        self.nodes = {}
        self.compNames = {}

        self.nodes['cube'] = cmds.polyCube()[0]
        self.compNames['meshVtx'] = self.nodes['cube'] + ".vtx[2]"
        self.compNames['meshEdge'] = self.nodes['cube'] + ".e[1]"
        #self.compNames['meshEdge'] = self.nodes['cube'] + ".edge[1]"   # This just gets the plug, not a kEdgeComponent
        self.compNames['meshFace'] = self.nodes['cube'] + ".f[4]"
        self.compNames['meshUV'] = self.nodes['cube'] + ".map[3]"
        self.compNames['meshVtxFace'] = self.nodes['cube'] + ".vtxFace[3][0]"
        self.compNames['pviot'] = self.nodes['cube'] + ".rotatePivot"

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compNames['subdCV'] = self.nodes['subd'] + ".smp[0][2]"
        self.compNames['subdEdge'] = self.nodes['subd'] + ".sme[256][1]"
        self.compNames['subdFace'] = self.nodes['subd'] + ".smf[256][0]"
        self.compNames['subdUV'] = self.nodes['subd'] + ".smm[95]"

        self.nodes['curve'] = cmds.circle()[0]
        self.compNames['curveCV'] = self.nodes['curve'] + ".cv[6]"
        self.compNames['curvePt'] = self.nodes['curve'] + ".u[7.26580365007639]"
        self.compNames['curveEP'] = self.nodes['curve'] + ".ep[7]"
        self.compNames['curveKnot'] = self.nodes['curve'] + ".knot[1]"

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compNames['nurbsCV'] = self.nodes['sphere'] + ".cv[2][1]"
        self.compNames['nurbsIso'] = self.nodes['sphere'] + ".v[5.27974050577565]"
        #self.compNames['nurbsPt'] = self.nodes['sphere'] + ".uv[2.50132435444908][5.1327452105745]"  # Also results in kIsoparmComponent
        self.compNames['nurbsPatch'] = self.nodes['sphere'] + ".sf[1][1]"
        self.compNames['nurbsEP'] = self.nodes['sphere'] + ".ep[1][5]"
        self.compNames['nurbsKnot'] = self.nodes['sphere'] + ".knot[1][5]"
        self.compNames['nurbsRange'] = self.nodes['sphere'] + ".u[2:3]"

        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'])[1]
        self.compNames['lattice'] = self.nodes['lattice'] + ".pt[0][1][0]"
        
        self.compObjs = {}
        for compType, compName in self.compNames.iteritems():
            self.compObjs[compType] = api.toApiObject(compName)[1]
        
    def tearDown(self):
        for node in self.nodes.itervalues():
            if cmds.objExists(node):
                cmds.delete(node)
            
    def test_allCompsRepresented(self):
        unableToCreate = ('kEdgeComponent',
                          'kDecayRegionCapComponent',
                          'kSetGroupComponent',
                          'kDynParticleSetComponent',
                          )
        compTypesDict = self.getComponentTypes()
        flatCompTypes = set()
        for typesList in compTypesDict.itervalues():
            flatCompTypes.update(typesList)
        flatCompTypes = flatCompTypes - set([api.ApiTypesToApiEnums()[x] for x in unableToCreate])
        
        for compMobj in self.compObjs.itervalues():
            #print compMobj.apiTypeStr(), comp
            flatCompTypes.remove(compMobj.apiType())
             
        
        if flatCompTypes:
            failMsg = "component types not tested:\n"
            for x in flatCompTypes:
                failMsg += "    " + api.ApiEnumsToApiTypes()[x] + "\n"
            self.fail(failMsg)

    # Need seperate tests for PyNode / Component, b/c was bug where
    # Component('pCube1.vtx[3]') would actually return a Component
    # object, instead of a MeshVertex object, and fail, while
    # PyNode('pCube1.vtx[3]') would succeed
    
    @makePynodeCreationTests
    def test_makeComps_PyNode(self, compName, compObj):
        PyNode(compName)
        
    @makePynodeCreationTests
    def test_makeComps_Component(self, compName, compObj):
        Component(compName)

    @makePynodeCreationTests
    def test_makeCompFromObject(self, compName, compObj):
        if compObj.apiType() in ApiEnumsToPyComponents():
            node = compName.split('.')[0]
            pymelClass = ApiEnumsToPyComponents()[compObj.apiType()]
            pymelObj = pymelClass(node)
            self.assertEqual(pymelObj.__class__, pymelClass)
            
    @makePynodeCreationTests
    def test_makeCompFromNodeDotComptypeIndex(self, compName, compObj):
        """
        if compName is 'cubeShape1.vtx[1]', will try:
        cubeShape1 = PyNode('cubeShape1')
        cubeShape1.vtx[1]
        """
        nodeName = compName.split('.')[0]
        exec '%s = PyNode(%r)' % (nodeName, nodeName)
        exec compName


    
#def test_units():
#    startLinear = currentUnit( q=1, linear=1)
#    
#    #cam = PyNode('persp')
#    # change units from default
#    currentUnit(linear='meter')
#    
#    light = directionalLight()
#    
#    testPairs = [ ('persp.translate', 'getTranslation', 'setTranslation', datatypes.Vector([3.0,2.0,1.0]) ),  # Distance datatypes.Vector
#                  ('persp.shutterAngle' , 'getShutterAngle', 'setShutterAngle', 144.0 ),  # Angle
#                  ('persp.verticalShake' , 'getVerticalShake', 'setVerticalShake', 1.0 ),  # Unitless
#                  ('persp.focusDistance', 'getFocusDistance', 'setFocusDistance', 5.0 ),  # Distance
#                  ('%s.penumbraAngle' % light, 'getPenumbra', 'setPenumbra', 5.0 ),  # Angle with renamed api method ( getPenumbraAngle --> getPenumbra )
#                  
#                 ]
#
#    for attrName, getMethodName, setMethodName, realValue in testPairs:
#        at = PyNode(attrName)
#        node = at.node()
#        getter = getattr( node, getMethodName )
#        setter = getattr( node, setMethodName )
#
#
#        descr =  '%s / %s / %s' % ( attrName, getMethodName, setMethodName )
#        
#        def checkUnits( *args ):
#            print repr(at)
#            print "Real Value:", repr(realValue)
#            # set attribute using "safe" method
#            at.set( realValue )
#            # get attribute using wrapped api method
#            gotValue = getter()
#            print "Got Value:", repr(gotValue)
#            # compare
#            self.assertEqual( realValue, gotValue )
#            
#            # set using wrapped api method
#            setter( realValue )
#            # get attribute using "safe" method
#            gotValue = at.get()
#            # compare
#            self.assertEqual( realValue, gotValue )
#        checkUnits.description = descr
#        yield checkUnits
#                            
#    # reset units
#    currentUnit(linear=startLinear)
#    delete( light )
#                    #print types

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

class ComponentData(object):
    """
    Stores data handy for creating / testing a component.
    """
    def __init__(self, nodeName, compName, indices, sliceIndices=None):
        self.nodeName = nodeName
        self.compName = compName
        self.indices = indices
        if isinstance(self.indices, (int, float, basestring)):
            self.indices = (self.indices,)
        self.sliceIndices = sliceIndices
        
        if self.indices:
            compObjStr = self.indexedComp()
        else:
            compObjStr = self.fullComp()
        self._compObj = api.toApiObject(compObjStr)[1]    
        
    def fullComp(self):
        return self.nodeName + "." + self.compName
    
    def _makeIndicesString(self, indexObjs):
        return ''.join(['[%s]' % x for x in indexObjs])
    
    def indexedComp(self):
        if not self.indices:
            raise ValueError("no indices stored - %s" % self.fullComp())
        return self.fullComp() + self._makeIndicesString(self.indices)
    
    def slicedComp(self):
        if not self.sliceIndices:
            raise ValueError("no slices stored - %s" % self.fullComp())
        return self.fullComp() + self._makeIndicesString(self.sliceIndices)
    
    def typeEnum(self):
        return self._compObj.apiType()

    def typeName(self):
        return self._compObj.apiTypeStr()


def makePynodeCreationTests(compCreator):
    """
    Outputs a function suitable for use as a unittest test that test creation of components.
    
    For every component in self.compNames / compObjs, it will call 'compCreator(self, componentData)'.
    compCreator should try to create a component; if it succeeds, it should return an object which 
    evaluates as false; if it fails, it should return a string to print, identifying the component
    it failed to make.
    
    If any component cannot be created, the test will fail, and output a list of the components that
    could not be made in the fail message.
    """
    
    def test_makePyNodes(self):
        failedComps = []
        for compDatum in self.compData.itervalues():
            result = compCreator(self, compDatum)
            if result:
                failedComps.append(result)                
            
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
        newFile(f=1)

        self.nodes = {}
        self.compData= {}

        self.nodes['cube'] = cmds.polyCube()[0]
        self.compData['meshVtx'] = ComponentData(self.nodes['cube'], "vtx", 2)
        self.compData['meshVtx'] = ComponentData(self.nodes['cube'], "vtx", 2)
        self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "e", 1)
        #self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "edge", 1)   # This just gets the plug, not a kEdgeComponent
        self.compData['meshFace'] = ComponentData(self.nodes['cube'], "f", 4)
        self.compData['meshUV'] = ComponentData(self.nodes['cube'], "map", 3)
        self.compData['meshVtxFace'] = ComponentData(self.nodes['cube'], "vtxFace", (3,0))
        self.compData['pivot'] = ComponentData(self.nodes['cube'], "rotatePivot", None)

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compData['subdCV'] = ComponentData(self.nodes['subd'], "smp", (0,2))
        self.compData['subdEdge'] = ComponentData(self.nodes['subd'], "sme", (256,1))
        self.compData['subdFace'] = ComponentData(self.nodes['subd'], "smf", (256,0))
        self.compData['subdUV'] = ComponentData(self.nodes['subd'], "smm", 95)

        self.nodes['curve'] = cmds.circle()[0]
        self.compData['curveCV'] = ComponentData(self.nodes['curve'], "cv", 6)
        self.compData['curvePt'] = ComponentData(self.nodes['curve'], "u", 7.26580365007639)
        self.compData['curveEP'] = ComponentData(self.nodes['curve'], "ep", 7)
        self.compData['curveKnot'] = ComponentData(self.nodes['curve'], "knot", 1)

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compData['nurbsCV'] = ComponentData(self.nodes['sphere'], "cv", (2,1))
        self.compData['nurbsIso'] = ComponentData(self.nodes['sphere'], "v", 5.27974050577565)
        #self.compData['nurbsPt'] = ComponentData(self.nodes['sphere'], "uv", (2.50132435444908,5.1327452105745))  # Also results in kIsoparmComponent
        self.compData['nurbsPatch'] = ComponentData(self.nodes['sphere'], "sf", (1,1))
        self.compData['nurbsEP'] = ComponentData(self.nodes['sphere'], "ep", (1,5))
        self.compData['nurbsKnot'] = ComponentData(self.nodes['sphere'], "knot", (1,5))
        self.compData['nurbsRange'] = ComponentData(self.nodes['sphere'], "u", '2:3')

        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'])[1]
        self.compData['lattice'] = ComponentData(self.nodes['lattice'], "pt", (0,1,0))
        
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
        
        for compDatum in self.compData.itervalues():
            flatCompTypes.remove(compDatum.typeEnum())
        
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
    def test_makeIndexedComps_PyNode(self, compData):
        if compData.indices:
            execString = 'PyNode(%r)' % compData.indexedComp()
            try:
                exec execString
            except:
                return execString
        
    @makePynodeCreationTests
    def test_makeIndexedComps_Component(self, compData):
        if compData.indices:
            execString = 'Component(%r)' % compData.indexedComp()
            try:
                exec execString
            except:
                return execString

    @makePynodeCreationTests
    def test_makeCompFromObject(self, compData):
        """
        ie, MeshVertexComponent('pCube1')
        """
        pymelClass = ApiEnumsToPyComponents().get(compData.typeEnum(), None)
        if pymelClass:
            try:
                pymelObj = pymelClass(compData.nodeName)
            except:
                return '%s(%r)' % (pymelClass.__name__, compData.nodeName)
            else:
                self.assertEqual(pymelObj.__class__, pymelClass)
            
    @makePynodeCreationTests
    def test_node_dot_comptypeIndex(self, compData):
        """
        if 'cubeShape1.vtx[1]', will try:
        cubeShape1 = PyNode('cubeShape1')
        cubeShape1.vtx[1]
        """
        if compData.indices:
            exec '%s = PyNode(%r)' % (compData.nodeName, compData.nodeName)
            try:
                exec compData.indexedComp()
            except:
                return compData.indexedComp()


    
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

import unittest
import itertools

from pymel import *
from pymel.tools.pymelControlPanel import getClassHierarchy
from pymel.core.factories import ApiEnumsToPyComponents
from testingutils import TestCaseExtended


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
# add check of length of indices
# test tricky / extended slices: ie, [:3], [:-1], [-3:-1], [5:1:-2], etc
# Add tests for ranges of float parameters: ie, 'nurbsSphere1.v[5.657][3.1:4.2]'

class ComponentData(object):
    """
    Stores data handy for creating / testing a component.
    """
    def __init__(self, nodeName, compName, indices, melCompName=None, pythonIndices=None):
        self.nodeName = nodeName
        self.compName = compName
        if melCompName is None:
            melCompName = compName
        self.melCompName = melCompName
        self.indices = indices
        if isinstance(self.indices, (int, float, basestring)):
            self.indices = (self.indices,)
        if pythonIndices is None:
            pythonIndices = []
        if isinstance(pythonIndices, (int, float, basestring)):
            pythonIndices = [pythonIndices]
        self.pythonIndices = pythonIndices
        
        if indices:
            # just want the first one, since all we need in a component
            # mobject of the right type
            for x in self.melIndexedComps():
                compObjStr = x
                break 
        else:
            compObjStr = self.melUnindexedComp()
        self._compObj = api.toApiObject(compObjStr)[1]    
        
    def unindexedComp(self):
        return self.nodeName + "." + self.compName
    
    def melUnindexedComp(self):
        return self.nodeName + "." + self.melCompName
    
    def _makeIndicesString(self, indexObj):
        return ''.join(['[%s]' % x for x in indexObj.index])
    
    def indexedComps(self):
        if not self.indices:
            raise ValueError("no indices stored - %s" % self.unindexedComp())
        else:
            for index in itertools.chain(self.indices, self.pythonIndices):
                yield self.unindexedComp() + self._makeIndicesString(index)
    
    def melIndexedComps(self):
        if not self.indices:
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in self.indices:
                yield self.melUnindexedComp() + self._makeIndicesString(index)
    
    def indexSizes(self):
        for index in self.indices:
            yield index.size
    
    def typeEnum(self):
        return self._compObj.apiType()

    def typeName(self):
        return self._compObj.apiTypeStr()
    
class IndexData(object):
    def __init__(self, index, size=None):
        if isinstance(index, (list, tuple)):
            self.index = index
        else:
            self.index = (index,)
        self.size = size


def makeComponentCreationTests(evalStringCreator):
    """
    Outputs a function suitable for use as a unittest test that tests creation of components.
    
    For every ComponentData item in in self.compData, it will call
        'evalStringCreator(self, componentData)'
    evalStringCreator should output
        evalStrings
    where evalStrings is a list of strings, each of which when called like:
        eval(anEvalString)
    evaluates to a component.
    
    The function returns
        (successfulComps, failedComps)
    where each item of successfulComps is a successfully created component
    object, and each item of failedComps is the evalString that was not made.
    
    If any component cannot be created, the test will fail, and output a list of the components that
    could not be made in the fail message.
    """
    
    def test_makeComponents(self):
        successfulComps = []
        failedComps = []
        for componentData in self.compData.itervalues():
            evalStrings = evalStringCreator(self, componentData)
            for evalString in evalStrings:
                try:
                    eval(evalString)
                except Exception:
                    failedComps.append(evalString)
                else:
                    successfulComps.append(evalString)
        if failedComps:
            self.fail('Could not create following components:\n   ' + '\n   '.join(failedComps))
            
    return test_makeComponents

def melIndexedCompEvalStringCreator(evalStringCreator):
    def newMelIndexedCompEvalStringCreator(self, compData):
        if compData.indices:
            return [evalStringCreator(self, x)
                     for x in compData.melIndexedComps()]
        else:
            return []
    return newMelIndexedCompEvalStringCreator

def indexedCompEvalStringCreator(evalStringCreator):
    def newIndexedCompEvalStringCreator(self, compData):
        if compData.indices:
            return [evalStringCreator(self, x)
                     for x in compData.indexedComps()]
        else:
            return []
    return newIndexedCompEvalStringCreator
        
def melUnindexedCompEvalStringCreator(evalStringCreator):
    def newMelUnindexedCompEvalStringCreator(self, compData):
        return [evalStringCreator(self, compData.melUnindexedComp())]
    return newMelUnindexedCompEvalStringCreator
        
def unindexedCompEvalStringCreator(evalStringCreator):
    def newUnindexedCompEvalStringCreator(self, compData):
        return [evalStringCreator(self, compData.unindexedComp())]
    return newUnindexedCompEvalStringCreator

def getEvalStringFunctions(theObj):
    returnDict = {}
    for propName in dir(theObj):
        evalStringId = '_evalStrings'
        if propName.endswith(evalStringId):
            returnDict[propName] = getattr(theObj, propName)
    return returnDict

class testCase_components(unittest.TestCase):
    def setUp(self):
        newFile(f=1)

        self.nodes = {}
        self.compData= {}

        self.nodes['cube'] = cmds.polyCube()[0]
        self.compData['meshVtx'] = ComponentData(self.nodes['cube'], "vtx",
                                            [IndexData(2), IndexData('2:4')],
                                            pythonIndices = [IndexData(':-1')])
        self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "e",
                                                  [IndexData(1)])
        #self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "edge", 1)   # This just gets the plug, not a kEdgeComponent
        self.compData['meshFace'] = ComponentData(self.nodes['cube'], "f",
                                                  [IndexData(4)])
        self.compData['meshUV'] = ComponentData(self.nodes['cube'], "map",
                                                  [IndexData(3)])
        self.compData['meshVtxFace'] = ComponentData(self.nodes['cube'], "vtxFace",
                                                  [IndexData((3,0))])
        self.compData['rotatePivot'] = ComponentData(self.nodes['cube'], "rotatePivot", [])

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compData['subdCV'] = ComponentData(self.nodes['subd'], "smp",
                                                  [IndexData((0,2))])
        self.compData['subdEdge'] = ComponentData(self.nodes['subd'], "sme",
                                                  [IndexData((256,1))])
        self.compData['subdFace'] = ComponentData(self.nodes['subd'], "smf",
                                                  [IndexData((256,0))])
        self.compData['subdUV'] = ComponentData(self.nodes['subd'], "smm",
                                                  [IndexData(95)])
        self.compData['scalePivot'] = ComponentData(self.nodes['cube'], "scalePivot", [])
        
        self.nodes['curve'] = cmds.circle()[0]
        self.compData['curveCV'] = ComponentData(self.nodes['curve'], "cv",
                                                  [IndexData(6)])
        self.compData['curvePt'] = ComponentData(self.nodes['curve'], "u", 
                                                  [IndexData(7.26580365007639)])        
        self.compData['curveEP'] = ComponentData(self.nodes['curve'], "ep",
                                                  [IndexData(7)])
        self.compData['curveKnot'] = ComponentData(self.nodes['curve'], "knot",
                                                  [IndexData(1)])

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compData['nurbsCV'] = ComponentData(self.nodes['sphere'], "cv",
                                                  [IndexData((2,1))])
        self.compData['nurbsIsoU'] = ComponentData(self.nodes['sphere'], "u",
                                                  [IndexData(5)])
        self.compData['nurbsIsoV'] = ComponentData(self.nodes['sphere'], "vIsoparm",
                                                  [IndexData(5.27974050577565)],
                                                   melCompName="v")
        self.compData['nurbsIsoUV'] = ComponentData(self.nodes['sphere'], "uv",
                                                  [IndexData((1, 4.8))])
        self.compData['nurbsPatch'] = ComponentData(self.nodes['sphere'], "sf",
                                                  [IndexData((1,1))])
        self.compData['nurbsEP'] = ComponentData(self.nodes['sphere'], "ep",
                                                  [IndexData((1,5))])
        self.compData['nurbsKnot'] = ComponentData(self.nodes['sphere'], "knot",
                                                  [IndexData((1,5))])
        self.compData['nurbsRange'] = ComponentData(self.nodes['sphere'], "u",
                                                  [IndexData('2:3')])

        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'])[1]
        self.compData['lattice'] = ComponentData(self.nodes['lattice'], "pt",
                                                  [IndexData((0,1,0))])
        
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
        compTypesDict = api.getComponentTypes()
        flatCompTypes = set()
        for typesList in compTypesDict.itervalues():
            flatCompTypes.update(typesList)
        flatCompTypes = flatCompTypes - set([api.ApiTypesToApiEnums()[x] for x in unableToCreate])
        
        notFoundCompTypes = set(flatCompTypes)
        for compDatum in self.compData.itervalues():
            testedType = compDatum.typeEnum()
            self.assert_(testedType in flatCompTypes)
            notFoundCompTypes.discard(testedType)
        
        if notFoundCompTypes:
            failMsg = "component types not tested:\n"
            for x in notFoundCompTypes:
                failMsg += "    " + api.ApiEnumsToApiTypes()[x] + "\n"
            self.fail(failMsg)

    # Need separate tests for PyNode / Component, b/c was bug where
    # Component('pCube1.vtx[3]') would actually return a Component
    # object, instead of a MeshVertex object, and fail, while
    # PyNode('pCube1.vtx[3]') would succeed

    def pyNodeMaker(self, compString):
        return 'PyNode(%r)' % compString
    
    indexed_PyNode_evalStrings = melIndexedCompEvalStringCreator(pyNodeMaker)
    unindexedComp_PyNode_evalStrings = melUnindexedCompEvalStringCreator(pyNodeMaker)

    def componentMaker(self, compString):
        return 'Component(%r)' % compString
    
    indexed_Component_evalStrings = melIndexedCompEvalStringCreator(componentMaker)
    unindexedComp_Component_evalStrings = melUnindexedCompEvalStringCreator(componentMaker)

    def object_evalStrings(self, compData):
        """
        ie, MeshVertexComponent('pCube1')
        """
        pymelClass = ApiEnumsToPyComponents()[compData.typeEnum()]
        return ['%s(%r)' % (pymelClass.__name__, compData.nodeName)]
    
    @indexedCompEvalStringCreator
    def node_dot_comptypeIndex_evalStrings(self, compString):
        """
        if 'cubeShape1.vtx[1]', will try:
        cubeShape1 = PyNode('cubeShape1')
        cubeShape1.vtx[1]
        """
        compSplit = compString.split('.')
        nodeName = compSplit[0]
        compName = '.'.join(compSplit[1:])
        return 'PyNode(%r).%s' % (nodeName, compName)

    def test_objectComponentsClassEqual(self):
        successfulComps = []
        failedComps = []
        for componentData in self.compData.itervalues():
            for compString in self.object_evalStrings(componentData):
                try:
                    pymelObj = eval(compString)
                except Exception:
                    failedComps.append(compString)
                else:
                    className = compString.split('(')[0]
                    pymelClass = eval(className)
                    if pymelObj.__class__ == pymelClass:
                        successfulComps.append(compString)
                    else:
                        failedComps.append(compString)
        if failedComps:
            self.fail('Following components wrong class (or not created):\n   ' + '\n   '.join(failedComps))
                    
    def getComponentStrings(self):
        componentStrings = []
        for componentData in self.compData.itervalues():
            for evalStringFunc in getEvalStringFunctions(self.__class__).itervalues():
                componentStrings.extend(evalStringFunc(self, componentData))
        return componentStrings
    
    def test_componentSelection(self):
        failedSelections = []
        selectionUnequal = []
        print "I'm here!"
        for compString in self.getComponentStrings():
            print "compString:", compString
            try:
                pymelObj = eval(compString)
            except Exception:
                failedSelections.append(compString)
            else:
                try:
                    print "selecting:", pymelObj.name()
                    #cmds.select(pymelObj.name())
                    if pymelObj != ls(sl=1)[0]:
                        selectionUnequal.append(compString)
                except:
                    failedSelections.append(compString)
        if failedComps or selectionUnequal:
            failMsg = 'Following components unselectable (or not created):\n   ' + '\n   '.join(failedSelections)
            failMsg += 'Following components selection not equal to orignal:\n   ' + '\n   '.join(selectionUnequal)

for propName, evalStringFunc in \
        getEvalStringFunctions(testCase_components).iteritems():
    evalStringId = '_evalStrings'
    if propName.endswith(evalStringId):
        baseName = propName[:-len(evalStringId)].capitalize()
        newFuncName = 'test_' + baseName + '_ComponentCreation'
        setattr(testCase_components, newFuncName,
            makeComponentCreationTests(evalStringFunc))

class testCase_sets(TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.cube = polyCube()[0]
        self.sphere = sphere()[0]

    def assertSetSelect(self, setClass, *items): 
        """
        Generator function which tests the given set type by: 
        selects the items, saves the list of the selected items, makes a set
        from the selected items, selects the items in the set, then compares
        the results to the initial selection.
        """
        select(items)
        initialSel = cmds.ls(sl=1)
        if issubclass(setClass, ObjectSet):
            mySet = sets(initialSel)
        else:
            mySet = SelectionSet(initialSel)
        self.assertNoError(select, mySet)
        self.assertIteration(initialSel, cmds.ls(sl=1),
                             orderMatters=False)
        
    def test_ObjectSet_singleObject(self):
        self.assertSetSelect(ObjectSet, self.cube)
        
    def test_ObjectSet_multiObject(self):
        self.assertSetSelect(ObjectSet, self.cube, self.sphere)
        
    def test_ObjectSet_vertices(self):
        self.assertSetSelect(ObjectSet, self.cube.vtx[1:3])
    
    def test_ObjectSet_mixedObjectsComponents(self):
        self.assertSetSelect(ObjectSet, self.cube.edges[4:6], self.sphere)
    
    def test_SelectionSet_singleObject(self):
        self.assertSetSelect(SelectionSet, self.cube)
        
    def test_SelectionSet_multiObject(self):
        self.assertSetSelect(SelectionSet, self.cube, self.sphere)
        
    def test_SelectionSet_vertices(self):
        self.assertSetSelect(SelectionSet, self.cube.vtx[1:3])
    
    def test_SelectionSet_mixedObjectsComponents(self):
        self.assertSetSelect(SelectionSet, self.cube.edges[4:6], self.sphere)
    
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

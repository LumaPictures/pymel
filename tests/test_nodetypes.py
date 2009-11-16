import unittest
import itertools
import re

from pymel.all import *
from pymel.tools.pymelControlPanel import getClassHierarchy
from pymel.core.factories import ApiEnumsToPyComponents
import pymel.mayahook as mayahook
from testingutils import TestCaseExtended


VERBOSE = False

def getFundamentalTypes():
    classList = sorted( list( set( [ key[0] for key in api.apiToMelData.keys()] ) ) )
    #leaves = [ util.capitalize(x.key) for x in factories.nodeHierarchy.leaves() ]
    leaves = [ util.capitalize(node) for node, parents, children in factories.nodeHierarchy if not children ]
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
        
    def test_comparison(self):
        for attr in self.newAttrs.itervalues():
            self.assertEqual(attr, PyNode(attr.name()))
            
    def test_comparisonOtherObject(self):
        self.assertNotEqual(self.newAttrs['compound'], self.sphere1)

     
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
# test tricky / extended slices: ie, [:3], [:-1], [-3:-1], [5:1:-2], etc
# test multi-index slices, ie: [1:2, 5:9:2]
# Add tests for ranges of float parameters: ie, 'nurbsSphere1.v[5.657][3.1:4.2]'
# Add tests for double-indexed nurbs suface: 'nurbsSphere1.v[1.1:2.2][3.3:4.4]'
# check that indexing uses mel-style ranges (ie, inclusive)
# Continuous components with negative indices - ie, nurbsSurf[-3.3][-2]

class ComponentData(object):
    """
    Stores data handy for creating / testing a component.
    """
    def __init__(self, pymelType, nodeName, compName, indices,
                 melCompName=None,
                 pythonIndices=None, melIndices=None, neverUnindexed=False):
        self.pymelType = pymelType
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
        if melIndices is None:
            melIndices = []
        if isinstance(melIndices, (int, float, basestring)):
            melIndices = [melIndices]            
        self.melIndices = melIndices
        self.neverUnindexed = neverUnindexed
        
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
        if not self.hasPyIndices():
            raise ValueError("no indices stored - %s" % self.unindexedComp())
        else:
            # yield partial indices as well...
            for index in itertools.chain(self.indices, self.pythonIndices):
                if len(index.index):
                    for partialIndexLen in xrange(1, len(index.index)):
                        yield self.unindexedComp() + self._makeIndicesString(IndexData(index.index[:partialIndexLen]))
                yield self.unindexedComp() + self._makeIndicesString(index)
    
    def melIndexedComps(self):
        if not self.hasMelIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in itertools.chain(self.indices, self.melIndices):
                yield self.melUnindexedComp() + self._makeIndicesString(index)
    
    def hasPyIndices(self):
        return self.indices or self.pythonIndices
    
    def hasMelIndices(self):
        return self.indices or self.melIndices
    
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
                if VERBOSE:
                    print "trying to create:", evalString, "...",
                # Currently, a bug with adding '___.sme[*]' to any
                # MSelectionList - causes may to crash. thus, for now, just
                # auto fail tests making .sme[*]
                try:
                    eval(evalString)
                except Exception:
                    if VERBOSE:
                        print "FAILED"
                    failedComps.append(evalString)
                else:
                    if VERBOSE:
                        print "ok"
                    successfulComps.append(evalString)
        if failedComps:
            self.fail('Could not create following components:\n   ' + '\n   '.join(failedComps))
            
    return test_makeComponents

class MakeEvalStringCreator(object):
    """
    Used to transform a 'compString evalString creator' function to a
    a 'compData evalString creator' function.
    
    The generated 'compData evalString creator' is a function of the form:
       compDataEvalStringCreator(testCase, compDataObject)
    It takes a testCase_components object and a ComponentData object,
    and returns a list of strings, each of which can be fed as an argument
    to eval to generate a component.
    
    The input function, the 'compString evalString creator', is of the form:
        compStringEvalStringCreator(testCase, compString)
    It takes a testCase_components object and a component string, such as
       'myCube.vtx[1]'
    and returns a single string, which may be fed to eval to generate a
    component.
    
    melOrPymel determines whether mel-style or pymel-style syntax will be used.
    (in general, pymel-style indices are similar to mel-style, but can allow
    things such as [:-1].  Also, different component names may be used - for
    instance, the mel-syntax 'myNurbsSphere.v' will result in a v-isoparm,
    whereas PyNode('myNurbsSphere').v will give you the visibility attribute,
    so PyNode('myNurbsSphere').vIsoparm must be used. )
    
    If indexed is True, then the returned components will have an index. In this
    case, only compData which have associated index data (of the correct mel-or-
    pymel syntax type) will generate evalStrings.
    
    If indexed is False, then returned components will not have an index.
    In this case, alwaysMakeUnindexed will control whether given compData
    objects generate an evalString - if alwaysMakeUnindexed, all compData will
    be used, whereas as if it is false, only compData which have no index data
    for the given synatx will generate evalStrings.
    In addtion, if a ComponentData object has it's neverUnindexed property set
    to True, then no unindexed comp will be returned.
    """
    def __init__(self, melOrPymel, indexed=True, alwaysMakeUnindexed=False):
        self.melOrPymel = melOrPymel
        self.indexed = indexed
        self.alwaysMakeUnindexed = alwaysMakeUnindexed
        
    def __call__(self, evalStringCreator):
        def wrappedEvalStringCreator(testCase, compData):
            strings = []
            compDataStringFunc = None
            if self.indexed:
                if self.melOrPymel == 'mel':
                    if compData.hasMelIndices():
                        compDataStringFunc = compData.melIndexedComps
                elif self.melOrPymel == 'pymel':
                    if compData.hasPyIndices():
                        compDataStringFunc = compData.indexedComps
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, x)
                               for x in compDataStringFunc()]
            elif not compData.neverUnindexed:
                if self.melOrPymel == 'mel':
                    if self.alwaysMakeUnindexed or not compData.hasMelIndices():
                        compDataStringFunc = compData.melUnindexedComp
                elif self.melOrPymel == 'pymel':
                    if self.alwaysMakeUnindexed or not compData.hasPyIndices():
                        compDataStringFunc = compData.unindexedComp
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, compDataStringFunc())]
            # get rid of any empty strings
            return [x for x in strings if x]
        return wrappedEvalStringCreator

#def melIndexedCompEvalStringCreator(evalStringCreator):
#    def newMelIndexedCompEvalStringCreator(self, compData):
#        if compData.hasMelIndices():
#            return [evalStringCreator(self, x)
#                     for x in compData.melIndexedComps()]
#        else:
#            return []
#    return newMelIndexedCompEvalStringCreator
#
#def indexedCompEvalStringCreator(evalStringCreator):
#    def newIndexedCompEvalStringCreator(self, compData):
#        if compData.hasPyIndices():
#            return [evalStringCreator(self, x)
#                     for x in compData.indexedComps()]
#        else:
#            return []
#    return newIndexedCompEvalStringCreator
#        
#def melUnindexedCompEvalStringCreator(evalStringCreator):
#    def newMelUnindexedCompEvalStringCreator(self, compData):
#        if not compData.hasMelIndices():
#            return [evalStringCreator(self, compData.melUnindexedComp())]
#        else:
#            return []
#    return newMelUnindexedCompEvalStringCreator
#        
#def unindexedCompEvalStringCreator(evalStringCreator, allowIndexedComps=False):
#    def newUnindexedCompEvalStringCreator(self, compData):
#        if not compData.hasPyIndices():
#            return [evalStringCreator(self, compData.unindexedComp())]
#        else:
#            return []
#    return newUnindexedCompEvalStringCreator

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
        self.compData['meshVtx'] = ComponentData(MeshVertex,
                                                 self.nodes['cube'], "vtx",
                                            [IndexData(2), IndexData('2:4')],
                                            pythonIndices = [IndexData(':-1')])
        self.compData['meshEdge'] = ComponentData(MeshEdge,
                                                  self.nodes['cube'], "e",
                                                  [IndexData(1)])
        #self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "edge", 1)   # This just gets the plug, not a kEdgeComponent
        self.compData['meshFace'] = ComponentData(MeshFace,
                                                  self.nodes['cube'], "f",
                                                  [IndexData(4)])
        self.compData['meshUV'] = ComponentData(MeshUV,
                                                self.nodes['cube'], "map",
                                                [IndexData(3)])
        self.compData['meshVtxFace'] = ComponentData(MeshVertexFace,
                                                     self.nodes['cube'], "vtxFace",
                                                     [IndexData((3,0))])
        self.compData['rotatePivot'] = ComponentData(Pivot,
                                                     self.nodes['cube'],
                                                     "rotatePivot", [])

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compData['subdCV'] = ComponentData(SubdVertex,
                                                self.nodes['subd'], "smp",
                                                [IndexData((0,2))])
        self.compData['subdEdge'] = ComponentData(SubdEdge,
                                                  self.nodes['subd'], "sme",
                                                  [IndexData((256,1))])
        self.compData['subdFace'] = ComponentData(SubdFace,
                                                  self.nodes['subd'], "smf",
                                                  [IndexData((256,0))])
        self.compData['subdUV'] = ComponentData(SubdUV,
                                                self.nodes['subd'], "smm",
                                                [IndexData(10)])
        self.compData['scalePivot'] = ComponentData(Pivot,
                                                    self.nodes['subd'],
                                                    "scalePivot", [])
        
        self.nodes['curve'] = cmds.circle()[0]
        self.compData['curveCV'] = ComponentData(NurbsCurveCV,
                                                 self.nodes['curve'], "cv",
                                                 [IndexData(6)])
        self.compData['curvePt'] = ComponentData(NurbsCurveParameter,
                                                 self.nodes['curve'], "u", 
                                                 [IndexData(7.26580365007639)])        
        self.compData['curveEP'] = ComponentData(NurbsCurveEP,
                                                 self.nodes['curve'], "ep",
                                                 [IndexData(7)])
        self.compData['curveKnot'] = ComponentData(NurbsCurveKnot,
                                                   self.nodes['curve'], "knot",
                                                   [IndexData(1)])

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compData['nurbsCV'] = ComponentData(NurbsSurfaceCV,
                                                 self.nodes['sphere'], "cv",
                                                 [IndexData((2,1))])
        self.compData['nurbsIsoU'] = ComponentData(NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "u",
                                                   [IndexData(4),
                                                    IndexData(2.1,1.8)],
                                                   neverUnindexed=True)
        self.compData['nurbsIsoV'] = ComponentData(NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "vIsoparm",
                                                   [IndexData(5.27974050577565),
                                                    IndexData(3,1.3)],
                                                   melCompName="v",
                                                   neverUnindexed=True)
        self.compData['nurbsIsoUV'] = ComponentData(NurbsSurfaceIsoparm,
                                                    self.nodes['sphere'], "uv",
                                                    [IndexData((1, 4.8))],
                                                    neverUnindexed=True)
        self.compData['nurbsPatch'] = ComponentData(NurbsSurfaceFace,
                                                    self.nodes['sphere'], "sf",
                                                    [IndexData((1,1))])
        self.compData['nurbsEP'] = ComponentData(NurbsSurfaceEP,
                                                 self.nodes['sphere'], "ep",
                                                 [IndexData((1,5))])
        self.compData['nurbsKnot'] = ComponentData(NurbsSurfaceKnot,
                                                   self.nodes['sphere'], "knot",
                                                   [IndexData((1,5))])
        self.compData['nurbsRange'] = ComponentData(NurbsSurfaceRange,
                                                    self.nodes['sphere'], "u",
                                                    [IndexData('2:3')])

        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'])[1]
        self.compData['lattice'] = ComponentData(LatticePoint,
                                                 self.nodes['lattice'], "pt",
                                                 [IndexData((0,1,0))])
        self.nodes['polySphere'] = cmds.polySphere()[0]
        # Done in effort to prevent crash which happens after making a subd,
        # then adding any subd edges to an MSelectionList
        # see http://groups.google.com/group/python_inside_maya/browse_thread/thread/9415d03bac9e712b/0b94edb468fbe6bd
        cmds.refresh()
        import maya.utils
        maya.utils.processIdleEvents()
        # While the above works to prevent the crash in GUI mode,
        # unfortunately, I can't find anything that works in batch mode...
        # the following are various things I've tried...
        # Unfortunately, nothing is working so far...
#        cmds.refresh()
#        subdPyNode = PyNode(self.nodes['subd']).getShape()
#        subdPyNode.__apimfn__().updateSubdSurface()

#        cmds.createNode('mesh')
#        cmds.undo()
#        edgeIt = api.MItSubdEdge(subdPyNode.__apimobject__())
#        while not edgeIt.isDone():
#            edgeIt.index()
#            edgeIt.next()
        
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

    def compsEqual(self, comp1, comp2, failOnEmpty=True,
                   alreadySelected=False):
        """
        Compares two components for equality.
        
        Comps are compared through selection - they are selected,
        the selection is listed (with filterExpand), then the
        resulting lengths are compared, then the results are put into
        a set... the sets are then compared for equality.
        
        It will also return False if either component is empty, if failOnEmpty
        is True (default). 
        """
        if failOnEmpty:
            if not comp1: return False
            if not comp2: return False
        if alreadySelected:
            comp1Sel = comp1
            comp2Sel = comp2
        else:
            select(comp1)
            comp1Sel = filterExpand(sm=(x for x in xrange(74)))
            select(comp2)
            comp2Sel = filterExpand(sm=(x for x in xrange(74)))
        if failOnEmpty:
            if not comp1Sel: return False
            if not comp2Sel: return False
        else:
            # filterExpand may return None,
            # in which case set(None) would raise an error
            if not comp1Sel or not comp2Sel:
                return comp1Sel == comp2Sel
        if len(comp1Sel) != len(comp2Sel): return False
        return set(comp1Sel) == set(comp2Sel)
    
    # Need separate tests for PyNode / Component, b/c was bug where
    # Component('pCube1.vtx[3]') would actually return a Component
    # object, instead of a MeshVertex object, and fail, while
    # PyNode('pCube1.vtx[3]') would succeed

    def pyNodeMaker(self, compString):
        return 'PyNode(%r)' % compString
    
    # cubeShape1.vtx[1] => PyNode('cubeShape1.vtx[1]')
    indexed_PyNode_evalStrings = MakeEvalStringCreator('mel', indexed=True)(pyNodeMaker)
    # cubeShape1.vtx[1] => PyNode('cubeShape1.vtx')
    unindexedComp_PyNode_evalStrings = MakeEvalStringCreator('mel', indexed=False)(pyNodeMaker)

    def componentMaker(self, compString):
        return 'Component(%r)' % compString
    
    # cubeShape1.vtx[1] => Component('cubeShape1.vtx[1]')
    indexed_Component_evalStrings = MakeEvalStringCreator('mel', indexed=True)(componentMaker)
    # cubeShape1.vtx[1] => Component('cubeShape1.vtx')
    unindexedComp_Component_evalStrings = MakeEvalStringCreator('mel', indexed=False)(componentMaker)

    def object_evalStrings(self, compData):
        """
        ie, MeshVertexComponent('pCube1')
        """
        # Can't do Pivot('pCube1'), as we don't know whether we want scalePivot or rotatePivot
        if compData.pymelType == Pivot:
            return []
        pymelClass = compData.pymelType
        return ['%s(%r)' % (pymelClass.__name__, compData.nodeName)]
    
    def node_dot_comptypeMaker(self, compString):
        # node.scalePivot / node.rotatePivot returns the ATTRIBUTE,
        # so skip these.
        # (we can get the component by doing node.comp('scalePivot')
        if compString.endswith('Pivot'):
            return ''
        nodeName, compName = compString.split('.', 1)
        return 'PyNode(%r).%s' % (nodeName, compName)
    
    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    node_dot_comptypeIndex_evalStrings = MakeEvalStringCreator('pymel', indexed=True)(node_dot_comptypeMaker)
    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx
    node_dot_comptype_evalStrings = MakeEvalStringCreator('pymel', indexed=False, alwaysMakeUnindexed=True)(node_dot_comptypeMaker)

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx
    @MakeEvalStringCreator('pymel', indexed=False, alwaysMakeUnindexed=True)
    def node_dot_compFunc_evalStrings(self, compString):
        nodeName, compName = compString.split('.', 1)
        return 'PyNode(%r).comp(%r)' % (nodeName, compName)

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    @MakeEvalStringCreator('pymel', indexed=True)
    def node_dot_compFuncIndex_evalStrings(self, compString):
        nodeName, compNameAndIndex = compString.split('.', 1)
        indexSplit = compNameAndIndex.find('[')
        compName = compNameAndIndex[:indexSplit]
        indexString = compNameAndIndex[indexSplit:]
        return 'PyNode(%r).comp(%r)%s' % (nodeName, compName, indexString)
        
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
                    
    def getComponentStrings(self, returnCompData=False, evalStringFuncs=None):
        """
        Return a list of all component strings made using this object's
        component data.
        
        If evalStringFuncs is given, it should be an iterable which returns
        evalString functions.
        
        Otherwise, the eval string function returned by
        getEvalStringFunctions(self.__class__).itervalues()
        will be used.
        """
        if evalStringFuncs is None:
            evalStringFuncs = getEvalStringFunctions(self.__class__).values()
        componentStrings = set()
        for componentData in self.compData.itervalues():
            for evalStringFunc in evalStringFuncs:
                newStrings = evalStringFunc(self, componentData)
                if returnCompData:
                    newStrings = [(x, componentData) for x in newStrings]
                componentStrings.update(newStrings)
        return list(componentStrings)
    
    def test_componentSelection(self):
        failedCreation  = []
        failedSelections = []
        for compString in self.getComponentStrings():
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                if ((compString.startswith('SubdEdge') or
                     compString.endswith("comp(u'sme')") or
                     compString.endswith('.sme'))
                    and api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                    api.MGlobal.kLibraryApp)):
                    print "Auto-failing %r to avoid crash..." % compString
                    raise Exception('selecting .sme[*][*] causes a crash...')   
                pymelObj = eval(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "selecting...",
                try:
                    # There's a bug - if you add x.sme[*][*] to an
                    # MSelectionList immediately
                    # after creating the component, without any idle events
                    # run in between, Maya crashes...
                    # In gui mode, we process idle events after creation,
                    # but we can't do that in batch... so if we're
                    # in batch, just fail x.sme[*][*]...
                    if (isinstance(pymelObj, SubdEdge) and
                        pymelObj.currentDimension() == 0 and
                        api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                    api.MGlobal.kLibraryApp)):
                        print "Auto-failing %r to avoid crash..." % compString
                        raise Exception('selecting .sme[*][*] causes a crash...')
                    select(pymelObj, r=1)
                except Exception:
#                        import traceback
#                        traceback.print_exc()
                    failedSelections.append(compString)
                if VERBOSE:
                    print "done!"
                    printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"

        if failedCreation or failedSelections:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedSelections:
                failMsgs.append('Following components unselectable:\n   ' + '\n   '.join(failedSelections))
            self.fail('\n\n'.join(failMsgs))

    def test_component_repr(self):
        failedCreation  = []
        failedRepr = []
        
        for compString in self.getComponentStrings():
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                if ((compString.startswith('SubdEdge') or
                     compString.endswith("comp(u'sme')") or
                     compString.endswith('.sme'))
                    and api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                    api.MGlobal.kLibraryApp)):
                    print "Auto-failing %r to avoid crash..." % compString
                    raise Exception('selecting .sme[*][*] causes a crash...')                
                pymelObj = eval(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "getting repr...",
                try:
                    # There's a bug - if you add x.sme[*][*] to an
                    # MSelectionList immediately
                    # after creating the component, without any idle events
                    # run in between, Maya crashes...
                    # In gui mode, we process idle events after creation,
                    # but we can't do that in batch... so if we're
                    # in batch, just fail x.sme[*][*]...
                    if (isinstance(pymelObj, SubdEdge) and
                        pymelObj.currentDimension() == 0 and
                        api.MGlobal.mayaState in (api.MGlobal.kBatch,
                                                  api.MGlobal.kLibraryApp)):
                        print "Auto-failing %r to avoid crash..." % compString
                        raise Exception('selecting .sme[*][*] causes a crash...')                    
                    str = repr(pymelObj)
                except Exception:
                    failedRepr.append(compString)
                else:
                    if VERBOSE:
                        print "done!"
                        printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"                                

        if failedCreation or failedRepr:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedRepr:
                failMsgs.append('Following components un-repr-able:\n   ' + '\n   '.join(failedRepr))
            self.fail('\n\n'.join(failMsgs))

    def test_componentIteration(self):
        failedCreation  = []
        failedIterations = []
        failedSelections = []
        iterationUnequal = []
        
        for compString in self.getComponentStrings():
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                if ((compString.startswith('SubdEdge') or
                     compString.endswith("comp(u'sme')") or
                     compString.endswith('.sme'))
                    and api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                    api.MGlobal.kLibraryApp)):
                    print "Auto-failing %r to avoid crash..." % compString
                    raise Exception('selecting .sme[*][*] causes a crash...')   
                pymelObj = eval(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                # only test iteration for discrete components!
                if not isinstance(pymelObj, DiscreteComponent):
                    continue
                
                if VERBOSE:
                    print "iterating...",
                try:
                    iteration = [x for x in pymelObj]
                    iterationString = repr(iteration)
                except Exception:
#                        import traceback
#                        traceback.print_exc()
                    failedIterations.append(compString)
                else:
                    if VERBOSE:
                        print "comparing (using selection)...",
                    try:
                        select(iteration)
                    except Exception:
                        failedSelections.append(iterationString)
                    else:
                        iterSel = filterExpand(sm=(x for x in xrange(74)))
                        try:
                            select(pymelObj)
                        except Exception:
                            failedSelections.append(compString)
                        else:
                            compSel = filterExpand(sm=(x for x in xrange(74)))
                            if not self.compsEqual(iterSel, compSel, alreadySelected=True):
                                iterationUnequal.append(compString)
                            if VERBOSE:
                                print "done!"
                                printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"                                

        if failedCreation or failedIterations or failedSelections or iterationUnequal:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedIterations:
                failMsgs.append('Following components uniterable:\n   ' + '\n   '.join(failedIterations))
            if failedSelections:
                failMsgs.append('Following components unselectable:\n   ' + '\n   '.join(failedSelections))
            if iterationUnequal:
                failMsgs.append('Following components iteration not equal to orignal:\n   ' + '\n   '.join(iterationUnequal))
            self.fail('\n\n'.join(failMsgs))

    def test_componentTypes(self):
        def getCompAttrName(compString):
            dotSplit = compString.split('.')
            if len(dotSplit) > 1:
                return re.split(r'\W+', dotSplit[1])[0]
                
        failedCreation  = []
        failedComparisons = []
        for compString, compData in self.getComponentStrings(returnCompData=True):
            try:
                pymelObj = eval(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if pymelObj.__class__ != compData.pymelType:
                        failedComparisons.append(compString +
                            ' - expected: %s got: %s' % (compData.pymelType,
                                                         pymelObj.__class__))
                        
        if failedCreation or failedComparisons:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedComparisons:
                failMsgs.append('Following components type wrong:\n   ' + '\n   '.join(failedComparisons))
            self.fail('\n\n'.join(failMsgs))
            
    def test_multiComponentName(self):
        compMobj = api.MFnSingleIndexedComponent().create(api.MFn.kMeshVertComponent)
        mfnComp = api.MFnSingleIndexedComponent(compMobj)
        mfnComp.addElement(0)
        mfnComp.addElement(1)
        mfnComp.addElement(2)
        mfnComp.addElement(5)
        mfnComp.addElement(7)
        mfnComp.addElement(9)
        mfnComp.addElement(11)
        myVerts = MeshVertex(self.nodes['polySphere'], compMobj)
        self.assertEqual(str(myVerts), 'pSphere1.vtx[0:2,5:11:2]')

    def test_mixedPivot(self):
        select(self.nodes['cube'] + '.rotatePivot', r=1)
        select(self.nodes['cube'] + '.scalePivot', add=1)
        cubeName = self.nodes['cube']
        self.assertEqual(set(cmds.ls(sl=1)),
                         set(['%s.%s' % (cubeName, pivot) for pivot in ('rotatePivot', 'scalePivot')]))
        
    def test_mixedIsoparm(self):
        select(self.nodes['sphere'] + '.u[1]', r=1)
        select(self.nodes['sphere'] + '.v[0]', add=1)
        select(self.nodes['sphere'] + '.uv[2][1]', add=1)
        nameAliases = set(x % self.nodes['sphere'] for x in [
                           # aliases for .u[1]
                           '%s.u[1]',
                           '%s.u[1][*]',
                           '%s.u[1][0:8]',
                           '%s.uv[1]',
                           '%s.uv[1][*]',
                           '%s.uv[1][0:8]',
                           # aliases for .v[0]
                           '%s.v[0]',
                           '%s.v[0][*]',
                           '%s.v[0][0:4]',
                           '%s.uv[*][0]',
                           '%s.uv[0:4][0]',
                           # aliases for .uv[2][1]
                           '%s.u[2][1]',
                           '%s.v[1][2]',
                           '%s.uv[2][1]'])
        selected = set(cmds.ls(sl=1))
        self.assertTrue(selected.issubset(nameAliases))

    def test_nurbsIsoPrintedRange(self):
        # Maya has a bug -running:
        # 
        # import maya.cmds as cmds
        # cmds.sphere()
        # cmds.select('nurbsSphere1.uv[*][*]')
        # print cmds.ls(sl=1)
        # cmds.select('nurbsSphere1.u[*][*]')
        # print cmds.ls(sl=1)
        # 
        # Gives two different results:
        # [u'nurbsSphere1.u[0:4][0:1]']
        # [u'nurbsSphere1.u[0:4][0:8]']
        sphereShape = PyNode(self.nodes['sphere']).getShape().name()
        nameAliases = [x % sphereShape for x in [
                           '%s.u[*]',
                           '%s.u[*][*]',
                           '%s.u[0:4][0:8]',
                           '%s.uv[*]',
                           '%s.uv[*][*]',
                           '%s.uv[0:4][0:8]',
                           '%s.v[*]',
                           '%s.v[*][*]',
                           '%s.v[0:8][0:4]']]
        pynodeStr = str(PyNode(self.nodes['sphere']).uv)
        self.assertTrue(pynodeStr in nameAliases,
                        '%s not equivalent to %s.uv[0:4][0:8]' % (pynodeStr,sphereShape))
        
    def test_meshVertConnnectedFaces(self):
        # For a standard cube, vert 3 should be connected to
        # faces 0,1,4
        desiredFaceStrings = ['%s.f[%d]' % (self.nodes['cube'], x) for x in (0,1,4)] 
        connectedFaces = PyNode(self.nodes['cube']).vtx[3].connectedFaces()
        self.assertTrue(self.compsEqual(desiredFaceStrings, connectedFaces))

    def test_indiceChecking(self):
        # Check for a DiscreteComponent...
        cube = PyNode(self.nodes['cube'])
        cube.vtx[2]
        cube.vtx[7]
        cube.vtx[-8]
        cube.vtx[-8:7]
        self.assertRaises(IndexError, cube.vtx.__getitem__, 8)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(0,8))
        self.assertRaises(IndexError, cube.vtx.__getitem__, -9)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(-9,7))
        self.assertRaises(IndexError, cube.vtx.__getitem__, 'foo')
        self.assertRaises(IndexError, cube.vtx.__getitem__, 5.2)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(0,5.2))

        # Check for a ContinuousComponent...
        sphere = PyNode(self.nodes['sphere'])
        sphere.u[2]
        sphere.u[4]
        sphere.u[0]
        sphere.u[0:4]
        self.assertRaises(IndexError, sphere.u.__getitem__, 4.1)
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(0,5))
        self.assertRaises(IndexError, sphere.u.__getitem__, -2)
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(-.1,4))
        self.assertRaises(IndexError, sphere.u.__getitem__, 'foo')
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(0,'foo'))

    def test_melIndexing(self):
        pass
        

## There's a bug in Maya where if you select .sme[*], it crashes -
## so, temporarily, autofail all .sme's by wrapping the evalString functions
#
## Note - NEED to make autoFailSme a function, to avoid scope issues
#def autoFailSme(evalStringFunc):
#    def evalStringFunc_autoFailSme(*args, **kwargs):
#        results = evalStringFunc(*args, **kwargs)
#        for i, evalString in enumerate(results):
#            if re.search(r"""\.sme\[\*\]|\.sme(?:\[[*0-9]+\])*$|SubdEdge\(""", evalString):
#                results[i] = evalString + "   ***.sme AUTO-FAIL***"
#        return results
#    evalStringFunc_autoFailSme.__name__ = propName + "_autoFailSme"
#    return evalStringFunc_autoFailSme
#
#for propName, evalStringFunc in \
#        getEvalStringFunctions(testCase_components).iteritems():
#    setattr(testCase_components, propName, autoFailSme(evalStringFunc))
                        
for propName, evalStringFunc in \
        getEvalStringFunctions(testCase_components).iteritems():
    evalStringId = '_evalStrings'
    if propName.endswith(evalStringId):
        baseName = propName[:-len(evalStringId)].capitalize()
        newFuncName = 'test_' + baseName + '_ComponentCreation'
        setattr(testCase_components, newFuncName,
            makeComponentCreationTests(evalStringFunc))
        
class testCase_nurbsSurface(TestCaseExtended):
    def setUp(self):
        self.negUSurf = PyNode(surface(name='periodicSurf', du=3, dv=1,
                                       fu='periodic', fv='open',
                                       ku=range(-13, 0, 1), kv=(0, 1),
                                       pw=[(4, -4, 0, 1), (4, -4, -2.5, 1),
                                           (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                           (4, 4, 0, 1), (4, 4, -2.5, 1),
                                           (0, 5.5, 0, 1), (0, 5.5, -2.5, 1),
                                           (-4, 4, 0, 1), (-4, 4, -2.5, 1),
                                           (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1),
                                           (-4, -4, 0, 1), (-4, -4, -2.5, 1),
                                           (0, -5.5, 0, 1), (0, -5.5, -2.5, 1),
                                           (4, -4, 0, 1), (4, -4, -2.5, 1),
                                           (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                           (4, 4, 0, 1), (4, 4, -2.5, 1)] ))
        
    def tearDown(self):
        delete(self.negUSurf)
    
    def test_knotDomain(self):
        self.assertEqual(self.negUSurf.getKnotDomain(), (-11.0, -3.0, 0.0, 1.0))

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

class testCase_0_7_compatabilityMode(unittest.TestCase):
    # Just used to define a value that we know won't be stored in
    # 0_7_compatability mode...
    class NOT_SET(object): pass
    
    def setUp(self):
        self.stored_0_7_compatability_mode = mayahook.pymel_options.get( '0_7_compatibility_mode', False)
        mayahook.pymel_options['0_7_compatibility_mode'] = True
        
    def tearDown(self):
        if self.stored_0_7_compatability_mode == NOT_SET:
            del mayahook.pymel_options['0_7_compatibility_mode']
        else:
            mayahook.pymel_options['0_7_compatibility_mode'] = self.stored_0_7_compatability_mode
            
    def test_nonexistantPyNode(self):
        # Will raise an error if not in 0_7_compatability_mode
        PyNode('I_Dont_Exist_3142341324')
        

class testCase_apiArgConversion(unittest.TestCase):
    def test_unsignedIntRef_out_args(self):
        # the MFnLattice.getDivisions uses
        # multiple unsigned int & 'out' arguments ... make sure
        # that we can call them / they were translated correctly!
        res = (3,4,5)
        latticeObj = lattice(cmds.polyCube()[0], divisions=res)[1]
        self.assertEqual(latticeObj.getDivisions(), res)
        
    
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

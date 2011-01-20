import unittest
import itertools
import re
import platform

from pymel.all import *
import pymel.core as pm
from maintenance.pymelControlPanel import getClassHierarchy
from pymel.internal.factories import apiEnumsToPyComponents
import pymel.internal.factories as factories
import pymel.internal.apicache as apicache

from pymel.util.testing import TestCaseExtended, setCompare

VERBOSE = False

def getFundamentalTypes():
    classList = sorted( list( set( [ key[0] for key in factories.apiToMelData.keys()] ) ) )
    #leaves = [ util.capitalize(x.key) for x in factories.nodeHierarchy.leaves() ]
    leaves = [ util.capitalize(node) for node, parents, children in factories.nodeHierarchy if not children ]
    return sorted( set(classList).intersection(leaves) )

class CrashError(Exception):
    """
    Raised to signal that doing something would have caused maya to crash.
    """
    pass

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

    def test_add_delete(self):
        PyNode('persp').addAttr('foo')
        self.assert_( PyNode('persp').hasAttr('foo') )
        PyNode('persp').deleteAttr('foo')
        self.assert_(  not PyNode('persp').hasAttr('foo') )

def testInvertibles():
    classList = getFundamentalTypes()
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
            
            if apiClassName not in factories.apiClassInfo:
                continue
            
            #print className, apiClassName
            
            classInfo = factories.apiClassInfo[apiClassName]
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
                                
                            def checkUndo(*args): 
                                mel.undo()

                            checkSetter.description = descr
                            yield checkSetter, setter, args
                            checkUndo.description = descr + ' undo'
                            yield checkUndo
                            
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
    def __init__(self, pymelType, nodeName, compName, indices, ranges,
                 melCompName=None,
                 pythonIndices=None, melIndices=None, neverUnindexed=False):
        self.pymelType = pymelType
        self.nodeName = nodeName
        self.compName = compName
        if melCompName is None:
            melCompName = compName
        self.melCompName = melCompName
        self.indices = indices
        self.ranges = ranges
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

        
    def pyUnindexedComp(self):
        return self.nodeName + "." + self.compName
    
    def melUnindexedComp(self):
        return self.nodeName + "." + self.melCompName
    
    def _makeIndicesString(self, indexObj):
        return ''.join([('[%s]' % x) for x in indexObj.index])

    def pyIndexedComps(self):
        if not self.hasPyIndices():
            raise ValueError("no indices stored - %s" % self.pyUnindexedComp())
        else:
            # yield partial indices as well...
            for index in itertools.chain(self.indices, self.pythonIndices):
                if len(index.index):
                    for partialIndexLen in xrange(1, len(index.index)):
                        yield self.pyUnindexedComp() + self._makeIndicesString(IndexData(*index.index[:partialIndexLen]))
                yield self.pyUnindexedComp() + self._makeIndicesString(index)
    
    def melIndexedComps(self):
        if not self.hasMelIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in itertools.chain(self.indices, self.melIndices):
                yield self.melUnindexedComp() + self._makeIndicesString(index)
                
    def bothIndexedComps(self):
        """
        For indices which are same for mel/pymel, returns a pair (melComp, pyComp)
        if not self.hasMelIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in itertools.chain(self.indices, self.melIndices):
                yield self.melUnindexedComp() + self._makeIndicesString(index)
        """
        if not self.hasBothIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in self.indices:
                indiceString = self._makeIndicesString(index)
                yield (self.melUnindexedComp() + indiceString,
                       self.pyUnindexedComp() + indiceString)        
    
    def hasPyIndices(self):
        return self.indices or self.pythonIndices
    
    def hasMelIndices(self):
        return self.indices or self.melIndices

    def hasBothIndices(self):
        return bool(self.indices)    

    def typeEnum(self):
        return self._compObj.apiType()

    def typeName(self):
        return self._compObj.apiTypeStr()
    
class IndexData(object):
    def __init__(self, *index):
        self.index = index


def makeComponentCreationTests(evalStringCreator, funcName=None):
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
                try:
                    self._pyCompFromString(evalString)
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
    if funcName:
        test_makeComponents.__name__ = funcName
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
                        compDataStringFunc = compData.pyIndexedComps
                elif self.melOrPymel == 'both':
                    if compData.hasBothIndices():
                        compDataStringFunc = compData.bothIndexedComps
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, x)
                               for x in compDataStringFunc()]
            elif not compData.neverUnindexed:
                if self.melOrPymel == 'mel':
                    if self.alwaysMakeUnindexed or not compData.hasMelIndices():
                        compDataStringFunc = compData.melUnindexedComp
                elif self.melOrPymel == 'pymel':
                    if self.alwaysMakeUnindexed or not compData.hasPyIndices():
                        compDataStringFunc = compData.pyUnindexedComp
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, compDataStringFunc())]
            # get rid of any empty strings
            return [x for x in strings if x]
        return wrappedEvalStringCreator

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
                                            [(0,7)],
                                            pythonIndices = [IndexData(':-1')])
        self.compData['meshEdge'] = ComponentData(MeshEdge,
                                                  self.nodes['cube'], "e",
                                                  [IndexData(1)],
                                                  [(0,11)])
        #self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "edge", 1)   # This just gets the plug, not a kEdgeComponent
        self.compData['meshFace'] = ComponentData(MeshFace,
                                                  self.nodes['cube'], "f",
                                                  [IndexData(4)],
                                                  [(0,5)])
        self.compData['meshUV'] = ComponentData(MeshUV,
                                                self.nodes['cube'], "map",
                                                [IndexData(3)],
                                                [(0,13)])
        self.compData['meshVtxFace'] = ComponentData(MeshVertexFace,
                                                     self.nodes['cube'], "vtxFace",
                                                     [IndexData(3,0)],
                                                     [(0,7),(0,5)])
        self.compData['rotatePivot'] = ComponentData(Pivot,
                                                     self.nodes['cube'],
                                                     "rotatePivot", [], [])

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compData['subdCV'] = ComponentData(SubdVertex,
                                                self.nodes['subd'], "smp",
                                                [IndexData(0,2)], [])
        self.compData['subdEdge'] = ComponentData(SubdEdge,
                                                  self.nodes['subd'], "sme",
                                                  [IndexData(256,1)], [])
        self.compData['subdFace'] = ComponentData(SubdFace,
                                                  self.nodes['subd'], "smf",
                                                  [IndexData(256,0)], [])
        self.compData['subdUV'] = ComponentData(SubdUV,
                                                self.nodes['subd'], "smm",
                                                [IndexData(10)], [])
        self.compData['scalePivot'] = ComponentData(Pivot,
                                                    self.nodes['subd'],
                                                    "scalePivot", [], [])
        
        self.nodes['curve'] = cmds.circle()[0]
        self.compData['curveCV'] = ComponentData(NurbsCurveCV,
                                                 self.nodes['curve'], "cv",
                                                 [IndexData(6)],
                                                 [(0,7)])
        self.compData['curvePt'] = ComponentData(NurbsCurveParameter,
                                                 self.nodes['curve'], "u", 
                                                 [IndexData(7.26580365007639)],
                                                 [(0,8)])        
        self.compData['curveEP'] = ComponentData(NurbsCurveEP,
                                                 self.nodes['curve'], "ep",
                                                 [IndexData(7)],
                                                 [(0,7)])
        self.compData['curveKnot'] = ComponentData(NurbsCurveKnot,
                                                   self.nodes['curve'], "knot",
                                                   [IndexData(1)],
                                                   [(0,12)])

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compData['nurbsCV'] = ComponentData(NurbsSurfaceCV,
                                                 self.nodes['sphere'], "cv",
                                                 [IndexData(2,1)],
                                                 [(0,6),(0,7)],
                                                 pythonIndices = [IndexData('0:5:2', '1:4:3')])
        self.compData['nurbsIsoU'] = ComponentData(NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "u",
                                                   [IndexData(4),
                                                    IndexData(2.1,1.8)],
                                                   [(0,4),(0,8)],
                                                   neverUnindexed=True)
        self.compData['nurbsIsoV'] = ComponentData(NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "vIsoparm",
                                                   [IndexData(5.27974050577565),
                                                    IndexData(3,1.3)],
                                                   # Indice range given in u, v order,
                                                   # because comparison func will
                                                   # automatically flip indice
                                                   # order before using range
                                                   # info for 'v' isoparms
                                                   [(0,4),(0,8)],
                                                   melCompName="v",
                                                   neverUnindexed=True)
        self.compData['nurbsIsoUV'] = ComponentData(NurbsSurfaceIsoparm,
                                                    self.nodes['sphere'], "uv",
                                                    [IndexData(1, 4.8)],
                                                   [(0,4),(0,8)],
                                                    neverUnindexed=True)
        self.compData['nurbsPatch'] = ComponentData(NurbsSurfaceFace,
                                                    self.nodes['sphere'], "sf",
                                                    [IndexData(1,1)],
                                                    [(0,3),(0,7)])
        self.compData['nurbsEP'] = ComponentData(NurbsSurfaceEP,
                                                 self.nodes['sphere'], "ep",
                                                 [IndexData(1,5)],
                                                 [(0,4),(0,7)])
        self.compData['nurbsKnot'] = ComponentData(NurbsSurfaceKnot,
                                                   self.nodes['sphere'], "knot",
                                                   [IndexData(1,5)],
                                                   [(0,8),(0,12)])
        self.compData['nurbsRange'] = ComponentData(NurbsSurfaceRange,
                                                    self.nodes['sphere'], "u",
                                                    [IndexData('2:3')],
                                                    [(0,4),(0,8)])

        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'],
                                             divisions=(3,5,4))[1]
        self.compData['lattice'] = ComponentData(LatticePoint,
                                                 self.nodes['lattice'], "pt",
                                                 [IndexData(0,1,0)],
                                                 [(0,2),(0,4),(0,3)])
        self.nodes['polySphere'] = cmds.polySphere()[0]

        self.nodes['negUSurf'] = cmds.surface(name='periodicSurf', du=3, dv=1,
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
                                                  (4, 4, 0, 1), (4, 4, -2.5, 1)] )
        self.compData['negNurbsIso'] = ComponentData(NurbsSurfaceIsoparm,
                                                     self.nodes['negUSurf'], "uv",
                                                     [IndexData(-3.4, .5)],
                                                     [(-11,-3),(0,1)],
                                                     neverUnindexed=True)                                                     
        
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
                #pass
            
    def test_allCompsRepresented(self):
        unableToCreate = ('kEdgeComponent',
                          'kDecayRegionCapComponent',
                          'kSetGroupComponent',
                          'kDynParticleSetComponent',
                          )
        compTypesDict = factories.getComponentTypes()
        flatCompTypes = set()
        for typesList in compTypesDict.itervalues():
            flatCompTypes.update(typesList)
        flatCompTypes = flatCompTypes - set([factories.apiTypesToApiEnums[x] for x in unableToCreate])
        
        notFoundCompTypes = set(flatCompTypes)
        for compDatum in self.compData.itervalues():
            testedType = compDatum.typeEnum()
            self.assert_(testedType in flatCompTypes)
            notFoundCompTypes.discard(testedType)
        
        if notFoundCompTypes:
            failMsg = "component types not tested:\n"
            for x in notFoundCompTypes:
                failMsg += "    " + factories.apiEnumsToApiTypes[x] + "\n"
            self.fail(failMsg)

    _indicesRe = re.compile( r'\[([^]]*)\]')
    
    @classmethod
    def _compStrSplit(cls, compStr):
        """
        Returns a tuple (nodeName, compName, indices).
        
        Indices will itself be a list.
        
        Example:
        >> testCase_components._compStrSplit('mySurf.uv[4][*]') # doctest: +SKIP
        ('mySurf', 'uv', ['4', '*'])
        """
        if '.' not in compStr:
            raise ValueError("compStr must be in 'nodeName.comp' form")
        nodeName, rest = compStr.split('.', 1)
        if not rest:
            compName = ''
            indices = []
        else:
            indices = cls._indicesRe.findall(rest)
            if not indices:
                compName = rest
            else:
                compName = rest.split('[', 1)[0]
        return nodeName, compName, indices
    
    @classmethod
    def _compStrJoin(cls, nodeName, compName, indices):
        """
        Inverse of _compStrSplit
        
        Given three items, nodeName, compName, indices, will
        return a component string representing that comp.
        
        Example:
        >> testCase_components._joinCompStr('mySurf', 'uv', ['4', '*']) # doctest: +SKIP
        'mySurf.uv[4][*]'
        """
        indicesStr = ''
        for indice in indices:
            indicesStr += '[%s]' % indice
        return '%s.%s%s' % (nodeName, compName, indicesStr)
        
    def _compStringsEqual(self, comp1, comp2, compData):
        # We assume that these comps have a '.' in them,
        # and that they've already been fed through
        # filterExpand, so myCube.vtx / myCubeShape.vtx
        # have been standardized 
        if comp1==comp2:
            return True
        
        node1, comp1Name, indices1 = self._compStrSplit(comp1)
        node2, comp2Name, indices2 = self._compStrSplit(comp2)
        
        if node1 != node2:
            return False

        if not (comp1Name and comp2Name and
                indices1 and indices2):
            return False
        
        if comp1Name != comp2Name:
            # If the component names are not equal,
            # they're different components, unless
            # they're u/v/uv variants of each other...
            uvNames = ('u', 'v', 'uv')
            if (comp1Name not in uvNames or
                comp2Name not in uvNames):
                return False
        
        if comp1Name in ('vtxFace', 'smp', 'sme', 'smf'):
            # these types (really, any discrete component)
            # should be found
            # equal before we get here, by
            # filterExpand/setCompare -
            # so just fail these, as
            # the range information is hard to get
            return False
                
        # If one of them is v, we need to
        # flip the indices...
        if comp1Name == 'v':
            if len(indices1) == 0:
                pass
            elif len(indices1) == 1:
                indices1 = ['*', indices1[0]]
            elif len(indices1) == 2:
                indices1 = [indices1[1], indices1[0]]
            else:
                raise ValueError(comp1)
        if comp2Name == 'v':
            if len(indices2) == 0:
                pass
            elif len(indices2) == 1:
                indices2 = ['*', indices2[0]]
            elif len(indices2) == 2:
                indices2 = [indices2[1], indices2[0]]
            else:
                return ValueError(comp2)
            
        if len(indices1) < len(indices2):
            indices1 += (['*'] * (len(indices2) - len(indices1)))
        elif len(indices1) > len(indices2):
            indices2 += (['*'] * (len(indices1) - len(indices2)))
            
        if len(indices1) > len(compData.ranges):
            return False
        # it's ok if we have less indices than possible dimensions...
            
        for indice1, indice2, range in zip(indices1, indices2, compData.ranges):
            if indice1 == indice2:
                continue
            if (not self._isCompleteIndiceString(indice1, range) or
                not self._isCompleteIndiceString(indice2, range)):
                return False
        return True
    
    def _isCompleteIndiceString(self, indice, range):
        """
        Returns true if the given mel indice string would
        represent a 'complete' dimension for the given range.
        """
        if indice == '*':
            return True
        if indice.count(':') != 1:
            return False
        start, stop = indice.split(':')
        return float(start) == range[0] and float(stop) == range[1] 

    def compsEqual(self, comp1, comp2, compData, failOnEmpty=True):
        """
        Compares two components for equality.

        The two args should either be pymel components objects, strings
        which can be selected, or a tuple or list of such objects. 
        
        It will also return False if either component is empty, if failOnEmpty
        is True (default). 
        """
        # First, make sure comp1, comp2 are both lists
        bothComps = [comp1, comp2]
        for i, comp in enumerate(bothComps):
            if isinstance(comp, (Component, basestring)):
                bothComps[i] = [comp]
            else:
                # ensure it's a list, so we can modify it
                bothComps[i] = list(comp) 
        
        # there's a bug where a comp such as:
        #   myNurbSurf.u[2]
        # will get converted to
        #   myNurbSurf.u[2][0:1]
        # when it should be
        #   myNurbSurf.u[2][0:8]
        # ...to get around it, use
        #  myNurbSurf.u[2][*]
        # See test_mayaBugs.TestSurfaceRangeDomain
        # for complete info on what will go wrong...
        if compData.pymelType in (NurbsSurfaceRange, NurbsSurfaceIsoparm):
            for compIterable in bothComps:
                for i, comp in enumerate(compIterable):
                    # Just worry about strings - the PyNodes
                    # are supposed to handle this bug themselves!
                    if isinstance(comp, basestring):
                        nodePart, compName, indices = self._compStrSplit(comp)
                        if compName == 'uv':
                            compPart = 'u'
                        if compName in ('u', 'v'):
                            if len(indices) < 2:
                                indices.append('*')
                        comp = self._compStrJoin(nodePart, compName, indices)
                    compIterable[i] = comp
                    
        comp1, comp2 = bothComps
            


#        Comps are compared through first converting to strings
#        by selecting and using filterExpand, then by comparing the
#        the strings through string parsing.
#        This seems to be the only way to get comps such as
#        myNurbShape.v[3][0:4] and myNurb.v[3] (when the u range is 0-4,
#        and myNurbShape is the first shape of myNurb) to compare equal.

        
        # First, filter the results through filterExpand...
        if failOnEmpty:
            if not comp1: return False
            if not comp2: return False
        select(comp1)
        comp1 = cmds.filterExpand(sm=tuple(x for x in xrange(74)))
        select(comp2)
        comp2 = cmds.filterExpand(sm=tuple(x for x in xrange(74)))
        
        # first, filter out components whose strings are identical
        only1, both, only2 = setCompare(comp1, comp2)
        # Then, do pairwise comparison...
        # Make a copy of only1, as we'll be modifying it as we iterate
        # through...
        for comp1 in list(only1):
            for comp2 in only2:
                if self._compStringsEqual(comp1, comp2, compData):
                    only1.remove(comp1)
                    only2.remove(comp2)
                    break
            else:
                # we couldn't find a match for comp1 - fail!
                return False
        assert(not only1)
        # If only2 is now empty as well, success!
        return not only2

    def _pyCompFromString(self, compString):
        self._failIfWillMakeMayaCrash(compString)
        return eval(compString)
    
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
                    pymelObj = self._pyCompFromString(compString)
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
        
        If returnCompData is True, the returned list will be of tuples
            (evalString, compData)
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
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "selecting...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
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
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "getting repr...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
                    repr(pymelObj)
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
        
        for compString,compData in self.getComponentStrings(returnCompData=True):
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                # only test iteration for discrete components!
                if not isinstance(pymelObj, DiscreteComponent):
                    continue
                
                if VERBOSE:
                    print "iterating...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
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
                            if not self.compsEqual(iterSel, compSel, compData):
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
                pymelObj = self._pyCompFromString(compString)
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
            
    # There's a bug - if you add x.sme[*][*] to an
    # MSelectionList immediately
    # after creating the component, without any idle events
    # run in between, Maya crashes...
    # In gui mode, we process idle events after creation,
    # but we can't do that in batch... so if we're
    # in batch, just fail x.sme[*][*]...
    
    # Even more fun - on osx, any comp such as x.sm*[256][*] crashes as well...
    def _failIfWillMakeMayaCrash(self, comp):
        try:
            if isinstance(comp, basestring):
#                if versions.current() >= versions.v2011:
#                    # In 2011, MFnNurbsSurface.getKnotDomain will make maya crash,
#                    # meaning any surf.u/v/uv.__getindex__ will crash
#                    nodeName, compName, indices = self._compStrSplit(comp)
#                    if re.match(r'''(?:(u|v|uv)(Isoparm)?|comp\(u?['"](u|v|uv)(Isoparm)?['"]\))$''', compName):
#                        raise CrashError
                if (platform.system() == 'Darwin' or
                    api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                              api.MGlobal.kLibraryApp)):
                    if ((comp.startswith('SubdEdge') or
                         comp.endswith("comp(u'sme')") or
                         comp.endswith('.sme'))
                        and api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                        api.MGlobal.kLibraryApp)):
                        raise CrashError
                    elif platform.system() == 'Darwin':
                        crashRe = re.compile(r".sm[pef]('\))?\[[0-9]+\]$")
                        if crashRe.search(comp):
                            raise CrashError
            elif isinstance(comp, Component):
                # Check if we're in batch - in gui, we processed idle events after subd
                # creation, which for some reason, prevents the crash
                if api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                              api.MGlobal.kLibraryApp):
                    # In windows + linux, just selections of type .sme[*][*] - on OSX,
                    # it seems any .sm*[256][*] will crash it...
                    if platform.system() == 'Darwin':
                        if (isinstance(comp, (SubdEdge, SubdVertex, SubdFace)) and
                            comp.currentDimension() in (0, 1)):
                            raise CrashError
                    elif (isinstance(comp, SubdEdge) and
                          comp.currentDimension() == 0):
                        raise CrashError
        except CrashError, e:
            print "Auto-failing %r to avoid crash..." % comp
            raise
            
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
        self.assertTrue(self.compsEqual(desiredFaceStrings, connectedFaces, self.compData['meshFace']))

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
        self._failIfWillMakeMayaCrash('%s.u[2]' % sphere.name())
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
        melString = '%s.vtx[1:4]' % self.nodes['cube']
        self.assertTrue(self.compsEqual(melString, PyNode(melString), self.compData['meshVtx']))
        

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    node_dot_comptypeIndex_evalStrings = MakeEvalStringCreator('pymel', indexed=True)(node_dot_comptypeMaker)
        
    def test_melPyMelCompsEqual(self):
        def pairedStrings(self, compStringPair):
            # The mel compString we don't need to alter...
            # For the PyNode, use PyNode('cubeShape1').vtx[1] syntax
            return (compStringPair[0], self.node_dot_comptypeMaker(compStringPair[1]))
        
        unindexedPairedStrings = MakeEvalStringCreator('both', indexed=False)(pairedStrings)
        indexedPairedStrings = MakeEvalStringCreator('both', indexed=True)(pairedStrings)
        failedCreation  = []
        failedDuringCompare = []
        failedComparison = []
        for componentData in self.compData.itervalues():
            evalStringPairs = itertools.chain(unindexedPairedStrings(self, componentData),
                                              indexedPairedStrings(self, componentData))
            for melString, pyString in evalStringPairs:
                printedDone = False
                if VERBOSE:
                    print melString, "/", pyString, "-", "creating...",
                try:
                    pymelObj = self._pyCompFromString(pyString)
                except Exception:
                    failedCreation.append(pyString)
                else:
                    if VERBOSE:
                        print "comparing...",                        
                    try:
                        areEqual = self.compsEqual(melString, pymelObj, componentData)
                    except Exception:
                        #raise
                        failedDuringCompare.append(str( (melString, pyString) ))
                    else:
                        if not areEqual:
                            failedComparison.append(str( (melString, pyString) ))
                        else:
                            if VERBOSE:
                                print "done!"
                            printedDone = True
                if not printedDone and VERBOSE:
                    print "FAIL!!!"
                
        if any( (failedCreation, failedDuringCompare, failedComparison) ):
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedDuringCompare:
                failMsgs.append('Following components had error during compare:\n   ' + '\n   '.join(failedDuringCompare))
            if failedComparison:
                failMsgs.append('Following components unequal:\n   ' + '\n   '.join(failedComparison))
            self.fail('\n\n'.join(failMsgs))
            
    def test_extendedSlices(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        pyCube = PyNode('pCube1')
        check(pyCube.e[2:11:3],
              ('pCubeShape1.e[11]', 'pCubeShape1.e[8]',
               'pCubeShape1.e[5]', 'pCubeShape1.e[2]'),
              self.compData['meshEdge'])
        pySphere = PyNode('nurbsSphere1')
        check(pySphere.cv[1:5:2][1:4:3],
              ('nurbsSphereShape1.cv[1][4]', 'nurbsSphereShape1.cv[1][1]',
               'nurbsSphereShape1.cv[3][4]', 'nurbsSphereShape1.cv[3][1]',
               'nurbsSphereShape1.cv[5][4]', 'nurbsSphereShape1.cv[5][1]'),
              self.compData['nurbsCV'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))
            
    def test_continuousCompRanges(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        check(self._pyCompFromString("PyNode('nurbsSphere1').vIsoparm[5.54][1.1:3.4]"),
              'nurbsSphereShape1.u[1.1:3.4][5.54]',
              self.compData['nurbsIsoUV'])
        check(self._pyCompFromString("PyNode('nurbsCircle1').u[2.8:6]"),
              'nurbsCircleShape1.u[2.8:6]',
              self.compData['curvePt'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))
            
    def test_negativeDiscreteIndices(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        pyCurve = PyNode('nurbsCircle1')
        # Breaking into extra lines here just to make debugging easier
        pyCurveShape = pyCurve.getShape()
        knot = pyCurveShape.knot
        knotNeg3 = knot[-3]
        check(knotNeg3,
              'nurbsCircleShape1.knot[10]',
              self.compData['curveKnot'])
        pyLattice = PyNode('ffd1Lattice')
        check(pyLattice.pt[-1][-5:-2][-2],
              ('ffd1LatticeShape.pt[2][0][2]',
               'ffd1LatticeShape.pt[2][1][2]',
               'ffd1LatticeShape.pt[2][2][2]'),
              self.compData['lattice'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))        

    def test_negativeContinuousIndices(self):
        # For continous comps, these should behave just like positive ones...
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        surf = PyNode('surfaceShape1')
        check(surf.uv[-3.3][.5],
              'surfaceShape1.u[-3.3][.5]',
              self.compData['negNurbsIso'])
        check(surf.uv[-8:-5.1][0],
              'surfaceShape1.u[-8:-5.1][0]',
              self.compData['negNurbsIso'])
        
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))
            
    def test_multipleIterations(self):
        """
        Make sure that, on repeated iterations through a component, we get the same result. 
        """
        comp = PyNode(self.nodes['cube']).e[3:10]
        iter1 = [x for x in comp]
        iter2 = [x for x in comp]
        self.assertEqual(iter1, iter2)
        
    # Disabling this for now - such indicing wasn't possible in 0.9.x, either,
    # so while I'd like to get this working at some point, it's not necessary for now...
#    def test_multipleNoncontiguousIndices(self):
#        """
#        test things like .vtx[1,2,5:7] 
#        """
#        failedComps = []
#        def check(pynode, expectedStrings, compData):
#            if not self.compsEqual(pynode, expectedStrings, compData):
#                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))
#
#        cube = PyNode('pCube1')
#        vtx = cube.vtx
#        check(vtx[1,2,5:7],
#              ('pCubeShape1.vtx[1]',
#               'pCubeShape1.vtx[2]',
#               'pCubeShape1.vtx[5]',
#               'pCubeShape1.vtx[6]',
#               'pCubeShape1.vtx[7]'),
#              self.compData['meshVtx'])
#        
#        ffd = PyNode('ffd1LatticeShape')
#        pt = ffd.pt
#        check(pt[0,1][1,2,4,][0,2],
#              ('ffd1LatticeShape.pt[0][1][0]',
#               'ffd1LatticeShape.pt[0][1][2]',
#               'ffd1LatticeShape.pt[0][2][0]',
#               'ffd1LatticeShape.pt[0][2][2]',
#               'ffd1LatticeShape.pt[0][4][0]',
#               'ffd1LatticeShape.pt[0][4][2]',
#               'ffd1LatticeShape.pt[1][1][0]',
#               'ffd1LatticeShape.pt[1][1][2]',
#               'ffd1LatticeShape.pt[1][2][0]',
#               'ffd1LatticeShape.pt[1][2][2]',
#               'ffd1LatticeShape.pt[1][4][0]',
#               'ffd1LatticeShape.pt[1][4][2]',
#               ),
#               self.compData['lattice'])
#        
#        if failedComps:
#            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps)) 

        
for propName, evalStringFunc in \
        getEvalStringFunctions(testCase_components).iteritems():
    evalStringId = '_evalStrings'
    if propName.endswith(evalStringId):
        baseName = propName[:-len(evalStringId)].capitalize()
        newFuncName = 'test_' + baseName + '_ComponentCreation'
        setattr(testCase_components, newFuncName,
            makeComponentCreationTests(evalStringFunc, funcName=newFuncName))
        
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
        # Was a bug with this, due to automatic wrapping of api 'unsigned int &' args
        self.assertEqual(self.negUSurf.getKnotDomain(), (-11.0, -3.0, 0.0, 1.0))

class testCase_joint(TestCaseExtended):
    def setUp(self):
        self.j = Joint(radius=3.3, a=1, p=(4,5,6))
        
    def tearDown(self):
        delete(self.j)
    
#    def test_getAbsolute(self):
#        # Was a bug with this, due to handling of methods which needed casting AND unpacking
#        self.assertEqual(self.j.getAbsolute(), (4,5,6))
        
    def test_getRadius(self):
        # Was a bug with this, due to handling of methods which needed unpacking (but not casting)
        self.assertEqual(self.j.getRadius(), 3.3)



class testCase_sets(TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.cube = polyCube()[0]
        self.sphere = sphere()[0]
        self.set = sets()
    def assertSetSelect(self, setClass, *items): 
        """
        Generator function which tests the given set type. 
        It first selects the items, saves the list of the selected items, and makes a set
        from the selected items. Then it
            - selects the items in the set 
            - calls set.members()
        and compares each of the results to the initial selection.
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
        if issubclass(setClass, ObjectSet):
            myList = mySet.members()
        else:
            myList = list(mySet)
        select(myList)
        newSel = cmds.ls(sl=1)
        self.assertIteration(initialSel, newSel, orderMatters=False)
        
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

    def test_SelectionSet_nestedSets(self):
        self.assertSetSelect(SelectionSet, self.set)
        
#class testCase_0_7_compatabilityMode(unittest.TestCase):
#    # Just used to define a value that we know won't be stored in
#    # 0_7_compatability mode...
#    class NOT_SET(object): pass
#    
#    def setUp(self):
#        self.stored_0_7_compatability_mode = factories.pymel_options.get( '0_7_compatibility_mode', False)
#        factories.pymel_options['0_7_compatibility_mode'] = True
#        
#    def tearDown(self):
#        if self.stored_0_7_compatability_mode == NOT_SET:
#            del factories.pymel_options['0_7_compatibility_mode']
#        else:
#            factories.pymel_options['0_7_compatibility_mode'] = self.stored_0_7_compatability_mode
#            
#    def test_nonexistantPyNode(self):
#        # Will raise an error if not in 0_7_compatability_mode
#        PyNode('I_Dont_Exist_3142341324')
#        

class testCase_apiArgConversion(unittest.TestCase):
    def test_unsignedIntRef_out_args(self):
        # the MFnLattice.getDivisions uses
        # multiple unsigned int & 'out' arguments ... make sure
        # that we can call them / they were translated correctly!
        res = (3,4,5)
        latticeObj = lattice(cmds.polyCube()[0], divisions=res)[1]
        self.assertEqual(latticeObj.getDivisions(), res)
        
    def test_float2Ref_out_arg(self):
        """
        Test api functions that have an output arg of type float2 &
        MFnMesh.getUvAtPoint's uvPoint arg is one such arg.
        """
        mesh = polyCube()[0].getShape()
        self.assertEqual(mesh.getUVAtPoint([0,0,0], space='world'),
                         [0.49666666984558105, 0.125])
        
    def test_int2Ref_out_arg(self):
        """
        Test api functions that have an output arg of type int2 &
        MFnMesh.getEdgeVertices's vertexList arg is one such arg.
        """
        mesh = polyCube()[0].getShape()
        self.assertEqual(mesh.getEdgeVertices(2), [4,5])

class testCase_Mesh(unittest.TestCase):
    def test_emptyMeshOps(self):
        mesh = pm.createNode('mesh')
        for comp in (mesh.vtx, mesh.faces, mesh.edges):
            self.assertEqual(len(comp), 0)
            self.assertEqual(bool(comp), False)
        self.assertEqual(mesh.numColorSets(), 0)
        self.assertEqual(mesh.numFaceVertices(), 0)
        self.assertEqual(mesh.numNormals(), 0)
        self.assertEqual(mesh.numUVSets(), 0)
        self.assertEqual(mesh.numUVs(), 0)
        self.assertEqual(mesh.numFaces(), 0)
        self.assertEqual(mesh.numVertices(), 0)
        self.assertEqual(mesh.numEdges(), 0)

class TestConstraintAngleOffsetQuery(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)
        
    def runTest(self):
        for cmdName in ('aimConstraint', 'orientConstraint'):
            cube1 = pm.polyCube()[0]
            cube2 = pm.polyCube()[0]
            cube2.translate.set( (2,0,0) )
            cmd = getattr(pm, cmdName)            
            constraint = cmd(cube1, cube2)
            
            setVals = (12, 8, 7)
            cmd(constraint, e=1, offset=setVals)
            getVals = tuple(cmd(constraint, q=1, offset=1))
            self.assertVectorsEqual(setVals, getVals)
            
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

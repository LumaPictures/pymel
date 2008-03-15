import sys, inspect, warnings, timeit, time
import re
# based on pymel
from pymel import *
from pymel.util import Singleton
import maya.OpenMayaAnim as OpenMayaAnim
try: import maya.OpenMayaCloth as OpenMayaCloth
except: pass
try : import maya.OpenMayaFX as OpenMayaFX
except: pass
try : import maya.OpenMayaMPx as OpenMayaMPx
except: pass
if not cmds.about(batch=True) :
    try : import maya.OpenMayaUI as OpenMayaUI
    except: pass
try : import maya.OpenMayaRender as OpenMayaRender
except: pass


# Static singleton dictionnary metaclass to quickly build classes
# holding predefined immutable dicts
class metaStatic(type) :
    def __new__(mcl, classname, bases, classdict):
        # Class is a Singleton and some base class (dict or list for instance), Singleton must come first so that it's __new__
        # method takes precedence
        base = bases[0]
        if Singleton not in bases :
            bases = (Singleton,)+bases        
        # Some predefined methods
        def __init__(self, value=None):
            # Can only create once)       
            if value is not None :
                # Can only init once
                if not self:
                    # Use the ancestor class dict method to init self
                    # base.update(self, value)
                    # self = base(value)
                    base.__init__(self, value)
                else :
                    raise TypeError, "'"+classname+"' object does not support redefinition"
        # delete the setItem methods of dict we don't want (read only dictionary)
        def __getattribute__(self, name):         
            remove = ('clear', 'update', 'pop', 'popitem')
            if name in remove :
                raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'" 
#            elif self.__dict__.has_key(name) :
#                return self.__dict__[name]
            else :
                return base.__getattribute__(self, name)
        # Cnnot set an item of the read only dict or list
        def __setitem__(self,key,val) :
            raise TypeError, "'"+classname+"' object does not support item assignation"           
        # Now add methods of the defined class, as long as it doesn't try to redefine
        # __new__, __init__, __getattribute__ or __setitem__
        newdict = { '__slots__':[], '__dflts__':{}, '__init__':__init__, '__getattribute__':__getattribute__, '__setitem__':__setitem__ }
        # Note: could have defined the __new__ method like it is done in Singleton but it's as easy to derive from it
        for k in classdict :
            if k.startswith('__') and k.endswith('__') :
                # special methods, copy to newdict unless they conflict with pre-defined methods
                if k in newdict :
                    warnings.warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
                else :
                    newdict[k] = classdict[k]
            else :
                # class variables
                newdict['__slots__'].append(k)
                newdict['__dflts__'][k] = classdict[k]
        return super(metaStatic, mcl).__new__(mcl, classname, bases, newdict)

# fast convenience tests on API objects
def _isValidMObject (obj):
    if isinstance(obj, OpenMaya.MObject) :
        return not obj.isNull()
    else :
        return False
    
def _isValidMPlug (obj):
    if isinstance(obj, OpenMaya.MPlug) :
        return not obj.isNull()
    else :
        return False

def _isValidMDagPath (obj):
    if isinstance(obj, OpenMaya.MDagPath) :
        return obj.isValid()
    else :
        return False

def _isValidMNode (obj):
    if _isValidMObject(obj) :
        return obj.hasFn(OpenMaya.MFn.kDependencyNode)
    else :
        return False

def _isValidMDagNode (obj):
    if _isValidMObject(obj) :
        return obj.hasFn(OpenMaya.MFn.kDagNode)
    else :
        return False
    
def _isValidMNodeOrPlug (obj):
    return _isValidMPlug (obj) or _isValidMNode (obj)


# Maya static info :
# Initializes various static look-ups to speed up Maya types conversions


class MayaAPITypesInt(dict) :
    __metaclass__ =  metaStatic

# Dictionnary of Maya API types to their MFn::Types enum,
MayaAPITypesInt(dict(inspect.getmembers(OpenMaya.MFn, lambda x:type(x) is int)))

class MayaIntAPITypes(dict) :
    __metaclass__ =  metaStatic

# Inverse lookup of MFn::Types enum to Maya API types
MayaIntAPITypes(dict((MayaAPITypesInt()[k], k) for k in MayaAPITypesInt().keys()))

# Reserved Maya types and API types that need a special treatment (abstract types)
# TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
# stragely createNode ('cluster') works but dgMod.createNode('cluser') doesn't
class ReservedMayaTypes(dict) :
    __metaclass__ =  metaStatic

ReservedMayaTypes({ 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
                'constraint':'kConstraint', 'field':'kField', \
                'geometryShape':'kGeometric', 'shape':'kShape', 'deformFunc':'kDeformFunc', 'cluster':'kClusterFilter', \
                'dimensionShape':'kDimension', \
                'abstractBaseCreate':'kCreate', 'polyCreator':'kPolyCreator', \
                'polyModifier':'kMidModifier', 'subdModifier':'kSubdModifier', \
                'curveInfo':'kCurveInfo', 'curveFromSurface':'kCurveFromSurface', \
                'surfaceShape': 'kSurface', 'revolvedPrimitive':'kRevolvedPrimitive', 'plane':'kPlane', 'curveShape':'kCurve', \
                'animCurve': 'kAnimCurve', 'resultCurve':'kResultCurve', 'cacheBase':'kCacheBase', 'filter':'kFilter',
                'blend':'kBlend', 'ikSolver':'kIkSolver', \
                'light':'kLight', 'nonAmbientLightShapeNode':'kNonAmbientLight', 'nonExtendedLightShapeNode':'kNonExtendedLight', \
                'texture2d':'kTexture2d', 'texture3d':'kTexture3d', 'textureEnv':'kTextureEnv', \
                'plugin':'kPlugin', 'pluginNode':'kPluginDependNode', 'pluginLocator':'kPluginLocatorNode', 'pluginData':'kPluginData', \
                'pluginDeformer':'kPluginDeformerNode', 'pluginConstraint':'kPluginConstraintNode', \
                'unknown':'kUnknown', 'unknownDag':'kUnknownDag', 'unknownTransform':'kUnknownTransform',\
                'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip' })      # creating these 2 crash Maya      

# Inverse lookup
class ReservedAPITypes(dict) :
    __metaclass__ =  metaStatic

ReservedAPITypes(dict( (ReservedMayaTypes()[k], k) for k in ReservedMayaTypes().keys()))

# some handy aliases / shortcuts easier to remember and use than actual Maya type name
class ShortMayaTypes(dict) :
    __metaclass__ =  metaStatic
    
ShortMayaTypes({'all':'base', 'valid':'base', 'any':'base', 'node':'dependNode', 'dag':'dagNode', \
                'deformer':'geometryFilter', 'weightedDeformer':'weightGeometryFilter', 'geometry':'geometryShape', \
                'surface':'surfaceShape', 'revolved':'revolvedPrimitive', 'deformable':'deformableShape', \
                'curve':'curveShape' })                
                   
# Lookup of Maya types to their API counterpart, not a read only (static) dict as these can change (if you load a plugin)
class MayaTypesToAPI(Singleton, dict) :
    """ Dictionnary of currently existing Maya types as keys with their corresponding API type as values """

# Inverse lookup of Maya API types to Maya Types, in the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )
class MayaAPIToTypes(Singleton, dict) :
    """ Dictionnary of currently existing Maya types as keys with their corresponding API type as values """

# get the API type from a maya type
def _getAPIType (mayaType) :
    """ Get the Maya API type from the name of a Maya type """
    apiType = 'kInvalid'

    # Reserved types must be treated specially
    if ReservedMayaTypes().has_key(mayaType) :
        # It's an abstract type            
        apiType = ReservedMayaTypes()[mayaType]
    else :
        # we create a dummy object of this type in a dgModifier
        # as the dgModifier.doIt() method is never called, the object
        # is never actually created in the scene
        obj = OpenMaya.MObject() 
        dagMod = OpenMaya.MDagModifier()
        dgMod = OpenMaya.MDGModifier()          
        try :
            parent = dagMod.createNode ( 'transform', OpenMaya.MObject())
            obj = dagMod.createNode ( mayaType, parent )
        except :
            try :
                obj = dgMod.createNode ( mayaType )
            except :
                pass
        apiType = obj.apiTypeStr()
                          
    return apiType                      

# Add a type to the MayaTypes lists
def addToMayaTypesList(typeName) :
    """ Add a type to the MayaTypes lists """
    if not MayaTypesToAPI().has_key(typeName) :
        # this will happen for initial building and when a pluging is loaded that registers new types
        api = _getAPIType(typeName)
        if api is not 'kInvalid' :
            MayaTypesToAPI()[typeName] = api
            if not MayaAPIToTypes().has_key(api) :
                MayaAPIToTypes()[api] = dict( ((typeName, None),) )
            else :
                MayaAPIToTypes()[api][typeName] = None
            return True
    return False

# Initialises/updates MayaTypes for a faster later access
def updateMayaTypesList() :
    """ updates the cached MayaTypes lists """
    start = time.time()
    # use dict of empty keys just for faster random access
    typeList = dict( ReservedMayaTypes().items() + [(k, None) for k in cmds.ls(nodeTypes=True)] )
    # remove types that no longuer exist
    for k in MayaTypesToAPI().keys() :
        if not typeList.has_key(k) :
            # this could happen when a pluging is unloaded and some types become unregistered
            api = MayaTypesToAPI()[k]
            mtypes = MayaAPIToTypes()[api]
            mtypes.pop(k)
            MayaTypesToAPI().pop(k)
    # add new types
    for k in typeList.keys() :
         if not MayaTypesToAPI().has_key(k) :
            # this will happen for initial building and when a pluging is loaded that registers new types
            api = typeList[k]
            if not api :
                api = _getAPIType(k)
            MayaTypesToAPI()[k] = api
            # can have more than one Maya type associated with an API type (yeah..)
            # we mark one as "default" if it's a member of the reserved type by associating it with a True value in dict
            defType = ReservedMayaTypes().has_key(k)
            if not MayaAPIToTypes().has_key(api) :
                MayaAPIToTypes()[api] = dict( ((k, defType),) )
            else :
                MayaAPIToTypes()[api][k] = defType   
    elapsed = time.time() - start
    print "Updated Maya types list in %.2f sec" % elapsed

            
# initial update  
updateMayaTypesList()

# lookup tables for a direct conversion between Maya type and API types to their MFn::Types enum
class MayaTypesToAPITypeInt(Singleton, dict) :
    """ Direct lookup from Maya types to API MFn::Types enums """

# Dictionnary of Maya API types to their MFn::Types enum
MayaTypesToAPITypeInt((k, MayaAPITypesInt()[MayaTypesToAPI()[k]]) for k in MayaTypesToAPI().keys())
  
class APITypeIntToMayaTypes(Singleton, dict) :
    """ Direct lookup from API MFn::Types enums to Maya types """

# Dictionnary of Maya API types to their MFn::Types enum
APITypeIntToMayaTypes((MayaTypesToAPITypeInt()[k], k) for k in MayaTypesToAPITypeInt().keys())  
  
# Cache API types hierarchy, using MFn classes hierarchy and additionnal trials
# TODO : do the same for Maya types, but no clue how to inspect them apart from parsing docs

# Reserved API type hierarchy, for virtual types where we can not use the 'create trick'
# to query inheritage, as of 2008 types and API types seem a bit out of sync as API types
# didn't follow latest Maya types additions...
class ReservedAPIHierarchy(dict) :
    __metaclass__ =  metaStatic
    
ReservedAPIHierarchy({ 'kNamedObject':'kBase', 'kDependencyNode':'kNamedObject', 'kDagNode':'kDependencyNode', \
                    'kConstraint':'kTransform', 'kField':'kTransform', \
                    'kShape':'kDagNode', 'kGeometric':'kShape', 'kDeformFunc':'kShape', 'kClusterFilter':'kWeightGeometryFilt', \
                    'kDimension':'kShape', \
                    'kCreate':'kDependencyNode', 'kPolyCreator':'kDependencyNode', \
                    'kMidModifier':'kDependencyNode', 'kSubdModifier':'kDependencyNode', \
                    'kCurveInfo':'kCreate', 'kCurveFromSurface':'kCreate', \
                    'kSurface':'kGeometric', 'kRevolvedPrimitive':'kGeometric', 'kPlane':'kGeometric', 'kCurve':'kGeometric', \
                    'kAnimCurve':'kDependencyNode', 'kResultCurve':'kAnimCurve', 'kCacheBase':'kDependencyNode' ,'kFilter':'kDependencyNode', \
                    'kBlend':'kDependencyNode', 'kIkSolver':'kDependencyNode', \
                    'kLight':'kShape', 'kNonAmbientLight':'kLight', 'kNonExtendedLight':'kNonAmbientLight', \
                    'kTexture2d':'kDependencyNode', 'kTexture3d':'kDependencyNode', 'kTextureEnv':'kDependencyNode', \
                    'kPlugin':'kBase', 'kPluginDependNode':'kDependencyNode', 'kPluginLocatorNode':'kLocator', \
                    'kPluginDeformerNode':'kGeometryFilt', 'kPluginConstraintNode':'kConstraint', 'kPluginData':'kData', \
                    'kUnknown':'kDependencyNode', 'kUnknownDag':'kDagNode', 'kUnknownTransform':'kTransform',\
                    'kXformManip':'kTransform', 'kMoveVertexManip':'kXformManip' })         

def _getMObject(nodeType, dagMod, dgMod) :
    """ Returns a queryable MObject form a give apiType """
    
    if type(dagMod) is not OpenMaya.MDagModifier or type(dgMod) is not OpenMaya.MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"
    # cant create these nodes, some would crahs MAya also
    if ReservedAPITypes().has_key(nodeType) or ReservedMayaTypes().has_key(nodeType) :
        return None   
    obj = OpenMaya.MObject()
    if MayaAPIToTypes().has_key(nodeType) :
        mayaType = MayaAPIToTypes()[nodeType].keys()[0]
        apiType = nodeType
    elif MayaTypesToAPI().has_key(nodeType) :
        mayaType = nodeType
        apiType = MayaTypesToAPI()[nodeType]
    else :
        return None    
      
    try :
        parent = dagMod.createNode ( 'transform', OpenMaya.MObject())
        obj = dagMod.createNode ( mayaType, parent )
    except :
        try :
            obj = dgMod.createNode ( mayaType )
        except :
            pass
    if _isValidMObject(obj) :
        return obj
    else :
        return None


# check if a an API type herits from another
# it can't b e done for "virtual" types (in ReservedAPITypes)
def _hasFn (apiType, dagMod, dgMod, parentType=None) :
    """ Get the Maya API type from the name of a Maya type """
    if parentType is None :
        parentType = 'kBase'
    # Reserved we can't determine it as we can't create the node, all we can do is check if it's
    # in the ReservedAPIHierarchy
    if ReservedAPITypes().has_key(apiType) :
        return ReservedAPIHierarchy().get(apiType, None) == parentType
    # Need the MFn::Types enum for the parentType
    if MayaAPITypesInt().has_key(parentType) :
        typeInt = MayaAPITypesInt()[parentType]
    else :
        return False
    # print "need creation for %s" % apiType
    # we create a dummy object of this type in a dgModifier
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    obj = _getMObject(apiType, dagMod, dgMod, parentType) 
    if _isValidMObject(obj) :
        return obj.hasFn(typeInt)
    else :
        return False
 

# Filter the given API type list to retain those that are parent of apiType
# can pass a list of types to check for being possible parents of apiType
# or a dictionnary of types:node to speed up testing
def _parentFn (apiType, dagMod=None, dgMod=None, *args, **kwargs) :
    """ Checks the given API type list, or API type:MObject dictionnary to return the first parent of apiType """
    if not kwargs :
        if not args :
            args = ('kBase', )
        kwargs = dict( (args[k], None) for k in args )
    else :
        for k in args :
            if not kwargs.has_key(k) :
                kwargs[k] = None
    # Reserved we can't determine it as we can't create the node, all we can do is check if it's
    # in the ReservedAPIHierarchy
    if ReservedAPITypes().has_key(apiType) :
        p = ReservedAPIHierarchy().get(apiType, None)
        if p is not None :
            for t in kwargs.keys() :
                if p == t :
                    return t
        return None
    # we create a dummy object of this type in a dgModifier
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    result = None           
    obj = kwargs.get(apiType, None)        
    if not _isValidMObject(obj) :
        # print "need creation for %s" % apiType
        obj = _getMObject(apiType, dagMod, dgMod)
    if _isValidMObject(obj) :
        if not kwargs.get(apiType, None) :
            kwargs[apiType] = obj          # update it if we had to create
        parents = []
        for t in kwargs.keys() :
            # Need the MFn::Types enum for the parentType
            if t != apiType :
                if MayaAPITypesInt().has_key(t) :
                    ti = MayaAPITypesInt()[t]
                    if obj.hasFn(ti) :
                        parents.append(t)
        # problem is the MObject.hasFn method returns True for all ancestors, not only first one
        if len(parents) :
            if len(parents) > 1 :
                for p in parents :
                    if MayaAPITypesInt().has_key(p) :
                        ip = MayaAPITypesInt()[p]
                        isFirst = True
                        for q in parents :
                            if q != p :
                                stored = kwargs.get(q, None)
                                if not stored :
                                    if ReservedAPITypes().has_key(q) :
                                        isFirst = not ReservedAPIHierarchy().get(q, None) == p
                                    else :                                    
                                        stored = _getMObject(q, dagMod, dgMod)
                                        if not kwargs.get(q, None) :
                                            kwargs[q] = stored          # update it if we had to create                                        
                                if stored :
                                    isFirst = not stored.hasFn(ip)
                            if not isFirst :
                                break
                        if isFirst :
                            result = p
                            break
            else :
                result = parents[0]
                                 
    return result

# pre-build a type:MObject lookup for all provided types, be careful that these MObject
# can be used only as long as dagMod and dgMod are not deleted
def _createNodes(dagMod, dgMod, *args) :
    result = {}
    for k in args :
        mayaType = apiType = None
        if MayaAPIToTypes().has_key(k) :
            mayaType = MayaAPIToTypes()[k].keys()[0]
            apiType = k
        elif MayaTypesToAPI().has_key(k) :
            mayaType = k
            apiType = MayaTypesToAPI()[k]
        else :
            continue
        if ReservedAPITypes().has_key(apiType) or ReservedMayaTypes().has_key(mayaType) :
            result[apiType] = None
        else :
            obj = OpenMaya.MObject()          
            try :
                parent = dagMod.createNode ( 'transform', OpenMaya.MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
            if _isValidMObject(obj) :
                result[apiType] = obj
            else :
                result[apiType] = None
    return result

# child:parent lookup of the Maya API classes hierarchy (based on the existing MFn class hierarchy)
class MayaAPITypesHierarchy(dict) :
    __metaclass__ =  metaStatic

# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def buildAPITypesHierarchy () :
    def _MFnType(x) :
        if x == OpenMaya.MFnBase :
            return 1
        else :
            try :
                return x().type()
            except :
                return 0
    MFn = inspect.getmembers(OpenMaya, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    try : MFn += inspect.getmembers(OpenMayaAnim, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaCloth, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaFX, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaMPx, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    except : pass
    if not cmds.about(batch=True) :
        try : MFn += inspect.getmembers(OpenMayaUI, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
        except : pass
    try : MFn += inspect.getmembers(OpenMayaRender, lambda x: inspect.isclass(x) and issubclass(x, OpenMaya.MFnBase))
    except : pass
    MFn = dict(MFn)
    MFnTree = inspect.getclasstree([MFn[k] for k in MFn.keys()])
    MFnDict = {}
    for x in util.expandArgs(MFnTree, type='list') :
        try :
            ct = _MFnType(x[0])
            pt = _MFnType(x[1][0])
            if ct and pt :
                MFnDict[MayaIntAPITypes()[ct]] = MayaIntAPITypes()[pt]
        except :
            pass
        
    # print MFnDict.keys()
    # Fixes for types that don't have a MFn by faking a node creation and testing it
    # Make it faster by pre-creating the nodes used to test
    dagMod = OpenMaya.MDagModifier()
    dgMod = OpenMaya.MDGModifier()      
    nodeDict = _createNodes(dagMod, dgMod, *MayaAPITypesInt().keys())
    # for k in nodeDict.keys() :
        # print "Cached %s : %s" % (k, nodeDict[k])
    # Fix? some MFn results are not coherent with the hierarchy presented in the docs :
    MFnDict.pop('kWire', None)
    MFnDict.pop('kBlendShape', None)
    MFnDict.pop('kFFD', None)
    for k in MayaAPITypesInt().keys() :
        if k not in MFnDict.keys() :
            #print "%s not in MFnDict, looking for parents" % k
            #startParent = time.time()
            p = _parentFn(k, dagMod, dgMod, **nodeDict)
            #endParent = time.time()
            if p :
                #print "Found parent: %s in %.2f sec" % (p, endParent-startParent)
                MFnDict[k] = p
            else :
                #print "Found none in %.2f sec" % (endParent-startParent)     
                pass         
                                       
    # print MFnDict.keys()                
    return MFnDict 

# Initialize the API tree
# MayaAPITypesHierarchy(buildAPITypesHierarchy())
# initial update  
start = time.time()
MayaAPITypesHierarchy(buildAPITypesHierarchy())
elapsed = time.time() - start
print "Initialized Maya API types hierarchy tree in %.2f sec" % elapsed

# TODO : to represent pluging registered types we might want to create an updatable (dynamic, not static) MayaTypesHierarchy ?

# Need to build a similar dict of Pymel types to their corresponding API types
class PyNodeToMayaAPITypes(dict) :
    __metaclass__ =  metaStatic

# inverse lookup, some Maya API types won't have a PyNode equivalent
class MayaAPITypesToPyNode(dict) :
    __metaclass__ =  metaStatic

# build a PyNode to API type relation or PyNode to Maya node types relation ?
def buildPyNodeToAPI () :
    # Check if a pymel class is DependNode or a subclass of DependNode
    def _PyNodeClass (x) :
        try :
            return issubclass(x, node._BaseObj)
        except :
            return False    
    listPyNodes = dict(inspect.getmembers(node, _PyNodeClass))
    PyNodeDict = {}
    PyNodeInverseDict = {}
    for k in listPyNodes.keys() :
        # assume that PyNode type name is the API type without the leading 'k'
        PyNodeType = listPyNodes[k]
        PyNodeTypeName = PyNodeType.__name__
        APITypeName = 'k'+PyNodeTypeName
        if MayaAPIToTypes().has_key(APITypeName) :
            PyNodeDict[PyNodeType] = APITypeName
            PyNodeInverseDict[APITypeName] = PyNodeType
    # Would be good to limit special treatments
    PyNodeDict[node._BaseObj] = 'kBase'
    PyNodeInverseDict['kBase'] = node._BaseObj
    PyNodeDict[DependNode] = 'kDependencyNode'
    PyNodeInverseDict['kDependencyNode'] = DependNode
                          
    # Initialize the static classes to hold these
    PyNodeToMayaAPITypes (PyNodeDict)
    MayaAPITypesToPyNode (PyNodeInverseDict)

# Initialize Pymel classes to API types lookup
#buildPyNodeToAPI()
start = time.time()
buildPyNodeToAPI()
elapsed = time.time() - start
print "Initialized Pymel PyNodes types list in %.2f sec" % elapsed

# PyNode types names (as str)
class PyNodeTypeNames(dict) :
    """ Lookup from PyNode type name to PyNode type """
    __metaclass__ =  metaStatic

# Dictionnary of Maya API types to their MFn::Types enum
PyNodeTypeNames((k.__name__, k) for k in PyNodeToMayaAPITypes().keys())  

# child:parent lookup of the pymel classes that derive from DependNode
class PyNodeTypesHierarchy(dict) :
    __metaclass__ =  metaStatic

# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def buildPyNodeTypesHierarchy () :    
    PyNodeTree = inspect.getclasstree([k for k in PyNodeToMayaAPITypes().keys()])
    PyNodeDict = {}
    for x in util.expandArgs(PyNodeTree, type='list') :
        try :
            ct = x[0]
            pt = x[1][0]
            if issubclass(ct, node._BaseObj) and issubclass(pt, node._BaseObj) :
                PyNodeDict[ct] = pt
        except :
            pass

    return PyNodeDict 

# Initialize the Pymel class tree
# PyNodeTypesHierarchy(buildPyNodeTypesHierarchy())
start = time.time()
PyNodeTypesHierarchy(buildPyNodeTypesHierarchy())
elapsed = time.time() - start
print "Initialized Pymel PyNode classes hierarchy tree in %.2f sec" % elapsed


# conversion fonctions

# conversion maya type -> api type

# get the API type enum (The OpenMaya.MFn.Types int, ie OpenMaya.MFn.kDagNode) from a maya type,
# no check is done here, it's a fast private function to be used by the public functions in dagTools
def _nodeTypeToApiEnum (nodeType) :
    """ Given a Maya node type, return the corresponding API type enum int """
    return MayaTypesToAPITypeInt().get(nodeType, None)

# get the API type from a maya type, no check is done here, it's a fast private function
# to be used by the public functions in dagTools
def _nodeTypeToApiType (nodeType) :
    """ Given a Maya node type, return the corresponding API type name """
    return MayaTypesToAPI().get(nodeType, None)
        
# The public function that handles a variable number of node types and flags to return either api type enum int or name
# in the case where no correspondance is found, will return the API type of the first node type parent in the node types
# hierarchy that can be matched to an API type         
def nodeTypeToApi (*args, **kwargs) :
    """ Given a list of Maya node types, return the corresponding API type or API type int """
    if args :
        do_apiInt = kwargs.get('apiEnum', False)
        do_apiStr = kwargs.get('apiType', False)
        result = []
        for arg in args :
            if do_apiStr and do_apiInt :
                result.append(tuple(MayaTypesToAPI().get(arg,None), MayaTypesToAPITypeInt().get(arg,None)))
            elif do_apiInt :
                result.append(MayaTypesToAPITypeInt().get(arg,None))
            else : 
                result.append(MayaTypesToAPI().get(arg,None))    # default: API type name
        if len(result) == 1 :
            return result[0]
        else :
            return tuple(result)
        
# conversion node type -> api type

# get the maya type from an API type
def _apiEnumToNodeType (apiTypeEnum) :
    """ Given an API type enum int, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return APITypeIntToMayaTypes().get(apiTypeEnum, None)

def _apiTypeToNodeType (apiType) :
    """ Given an API type name, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return MayaAPIToTypes().get(apiType, None)

# conversion api type -> node type
# get the maya type from an API type
def apiToNodeType (*args) :
    """ Given a list of API type or API type int, return the corresponding Maya node types,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    result = []
    for a in args :
        if type(a) is int :         
            result.append(_apiEnumToNodeType(a))
        else :
            result.append(_apiTypeToNodeType(a))
    if len(result) == 1 :
        return result[0]
    else :
        return tuple(result)

def isValidMayaTypeName (arg):
    return MayaTypesToAPI().has_key(arg)

def isValidPyNodeType (arg):
    return PyNodeToMayaAPITypes().has_key(arg)

def isValidPyNodeTypeName (arg):
    return PyNodeTypeNames().has_key(arg)

# Converting API MObjects and more

# returns a MObject for an existing node
def _MObject (nodeName):
    """ Get the API MObject given the name of an existing node """ 
    sel = OpenMaya.MSelectionList()
    obj = OpenMaya.MObject()
    result = None
    try :
        sel.add( nodeName )
        sel.getDependNode( 0, obj )
        if _isValidMObject(obj) :
            result = obj        
    except :
        pass
    return result

def _MDagPath (nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """ 
    obj = _MObject (nodeName)
    if _isValidMDagNode (obj):
        dagFn = OpenMaya.MFnDagNode (obj)
        dagPath = OpenMaya.MDagPath()
        dagFn.getPath ( dagPath )
        return dagPath

# returns a MPlug for an existing plug
def _MPlug (plugName):
    """ Get the API MObject given the name of an existing plug (node.attribute) """
    nodeAndAttr = plugName.split('.', 1)
    obj = _MObject (nodeAndAttr[0])
    plug = None
    if _isValidMObject(obj) :
        depNodeFn = OpenMaya.MFnDependencyNode(obj)
        attr = depNodeFn.attribute(nodeAndAttr[1])
        plug = MPlug ( obj, attr )
        if plug.isNull() :
            plug = None
    return plug


# MDagPath, MPlug or MObject to name
# Note there is a kNamedObject API type but not corresponding MFn, thus
# I see no way of querying the name of something that isn't a kDependency node or a MPlug
# TODO : add components support, short/ long name support where applies
def _MObjectName( obj ):
    """ Get the name of an existing MPlug, MDagPath or MObject representing a dependency node""" 
    if _isValidMPlug (obj) :
        return obj.name()
    elif _isValidMNode (obj) :
        depNodeFn = OpenMaya.MFnDependencyNode(obj)
        return depNodeFn.name()
    elif _isValidMDagPath (obj):
        # return obj.fullPathName()
        return obj.partialPathName()
    else :
        return unicode(obj)

#  MObjects to PyNode
def _MObjectPyNode( obj, comp=None ):
    """ Get the names of existing nodes given their API MObject""" 
    if _isValidMPlug (obj):
        return Attribute (obj.name())
    elif _isValidMNode (obj):
        depNodeFn = OpenMaya.MFnDependencyNode(obj)
        oname = depNodeFn.name()
        otype = _apiEnumToNodeType(obj.apiType ())
        # return PyNode(oname, otype) 
        ptype = util.capitalize(otype)
        try:
            pyConst = getattr(node, ptype)
            pynode = pyConst(oname)
        except (AttributeError, TypeError):
            pynode = DependNode(oname)       
        return pynode
    elif _isValidMDagPath (obj):
        oname = obj.partialPathName()
        otype = _apiEnumToNodeType(obj.apiType ())
        if _isValidMObject (comp) :
            clist = None
            # TODO : component handling
            return PyNode(oname, otype)
        else :
            return PyNode(oname, otype)   
    else :
        raise ValueError, "'%s' is not a Plug, a Node or a Dag Path that can be expressed as a PyNode object" % unicode( obj )

# Selection list to PyNodes
def _MSelectionPyNode ( sel ):
    length = sel.length()
    dag = OpenMaya.MDagPath()
    comp = OpenMaya.MObject()
    obj = OpenMaya.MObject()
    result = []
    for i in xrange(length) :
        selStrs = []
        sel.getSelectionStrings ( i, selStrs )    
        print "Working on selection %i:'%s'" % (i, ', '.join(selStrs))
        try :
            sel.getDagPath(i, dag, comp)
            pynode = _MObjectPyNode( dag, comp )
            result.append(pynode)
        except :
            try :
                sel.getDependNode(i, obj)
                pynode = _MObjectPyNode( obj )
                result.append(pynode)                
            except :
                warnings.warn("Unable to recover selection %i:'%s'" % (i, ', '.join(selStrs)) )             
    return result      
        
        
def _activeSelectionPyNode () :
    sel = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList ( sel )   
    return _MSelectionPyNode ( sel )

# names to MObjects function (expected to be faster to share one selectionList)
def nameToMObject( *args ):
    """ Get the API MObjects given names of existing nodes """ 
    sel = OpenMaya.MSelectionList() 
    for name in args :
        sel.add( name )
    result = []            
    obj = OpenMaya.MObject()            
    for i in range(sel.length()) :
        try :
            sel.getDependNode( i, obj )
        except :
            result.append(None)
        if _isValidMObject(obj) :
            result.append(obj)
        else :
            result.append(None)
    if len(result) == 1:
        return result[0]
    else :
        return tuple(result)

# Maya scene nodes iterators

# An iterator on maya nodes using the API MItDependencyNodes (ie ls command)

def MItNodes( *args, **kwargs ):
    """ Iterator on MObjects of nodes of the specified types in the Maya scene,
        if a list of tyes is passed as args, then all nodes of a type included in the list will be iterated on,
        if no types are specified, all nodes of the scene will be iterated on
        the types are specified as Maya API types """
    typeFilter = OpenMaya.MIteratorType()
    if args : 
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = OpenMaya.MScriptUtil()
            typeIntM = OpenMaya.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.setObjectType ( OpenMaya.MIteratorType.kMObject )
    # create iterator with (possibly empty) typeFilter
    iterObj = OpenMaya.MItDependencyNodes ( typeFilter )     
    while not iterObj.isDone() :
        yield (iterObj.thisNode())
        iterObj.next()   


# Iterators on nodes connections using MItDependencyGraph (ie listConnections/ listHistory)
def MItGraph (nodeOrPlug, *args, **kwargs):
    """ Iterate over MObjects of Dependency Graph (DG) Nodes or Plugs starting at a specified root Node or Plug,
        If a list of types is provided, then only nodes of these types will be returned,
        if no type is provided all connected nodes will be iterated on.
        Types are specified as Maya API types.
        The following keywords will affect order and behavior of traversal:
        upstream: if True connections will be followed from destination to source,
                  if False from source to destination
                  default is False (downstream)
        breadth: if True nodes will be returned as a breadth first traversal of the connection graph,
                 if False as a preorder (depth first)
                 default is False (depth first)
        plug: if True traversal will be at plug level (no plug will be traversed more than once),
              if False at node level (no node will be traversed more than once),
              default is False (node level)
        prune : if True will stop the iteration on nodes than do not fit the types list,
                if False these nodes will be traversed but not returned
                default is False (do not prune) """
#    startObj = OpenMaya.MObject() 
#    startPlug = OpenMaya.MPlug()
    startObj = None
    startPlug = None   
    if _isValidMPlug(nodeOrPlug):
        startPlug = nodeOrPlug
    elif _isValidMNode(nodeOrPlug) :
        startObj = nodeOrPlug
    else :
        raise ValueError, "'%s' is not a valid Node or Plug" % _MObjectName(nodeOrPlug)
    upstream = kwargs.get('upstream', False)
    breadth = kwargs.get('breadth', False)
    plug = kwargs.get('plug', False)
    prune = kwargs.get('prune', False)
    if args : 
        typeFilter = OpenMaya.MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = OpenMaya.MScriptUtil()
            typeIntM = OpenMaya.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a node or a plug
        if startPlug is not None :
            typeFilter.setObjectType ( OpenMaya.MIteratorType.kMPlugObject )
        else :
            typeFilter.setObjectType ( OpenMaya.MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if upstream :
        direction = OpenMaya.MItDependencyGraph.kUpstream
    else :
        direction = OpenMaya.MItDependencyGraph.kDownstream
    if breadth :
        traversal = OpenMaya.MItDependencyGraph.kBreadthFirst 
    else :
        traversal =  OpenMaya.MItDependencyGraph.kDepthFirst
    if plug :
        level = OpenMaya.MItDependencyGraph.kPlugLevel
    else :
        level = OpenMaya.MItDependencyGraph.kNodeLevel
    iterObj = OpenMaya.MItDependencyGraph ( startObj, startPlug, typeFilter, direction, traversal, level )
    if prune :
        iterObj.enablePruningOnFilter()
    else :
        iterObj.disablePruningOnFilter() 
    # iterates and yields MObjects
    while not iterObj.isDone() :
        yield (iterObj.thisNode())
        iterObj.next()

# Iterators on dag nodes hierarchies using MItDag (ie listRelatives)
def MItDag (root = None, *args, **kwargs) :
    """ Iterate over the hierarchy under a root dag node, if root is None, will iterate on whole Maya scene
        If a list of types is provided, then only nodes of these types will be returned,
        if no type is provided all dag nodes under the root will be iterated on.
        Types are specified as Maya API types.
        The following keywords will affect order and behavior of traversal:
        breadth: if True nodes Mobjects will be returned as a breadth first traversal of the hierarchy tree,
                 if False as a preorder (depth first)
                 default is False (depth first)
        underworld: if True traversal will include a shape's underworld (dag object parented to the shape),
              if False underworld will not be traversed,
              default is False (do not traverse underworld )
        depth : if True will return depth of each node.
        prune : if True will stop the iteration on nodes than do not fit the types list,
                if False these nodes will be traversed but not returned
                default is False (do not prune) """
    # startObj = OpenMaya.MObject()
    # startPath = OpenMaya.MDagPath()
    startObj = startPath = None  
    if _isValidMDagPath (root) :
        startPath = root
    elif _isValidMDagNode (root) :
        startObj = root
    else :
        raise ValueError, "'%s' is not a valid Dag Node" % _MObjectName(root)
    breadth = kwargs.get('breadth', False)
    underworld = kwargs.get('underworld', False)
    prune = kwargs.get('prune', False)
    path = kwargs.get('path', False)
    allPaths = kwargs.get('allPaths', False)
    if args : 
        typeFilter = OpenMaya.MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = OpenMaya.MScriptUtil()
            typeIntM = OpenMaya.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a MDagPath or a Mobject
        if startPath is not None :
            typeFilter.setObjectType ( OpenMaya.MIteratorType.kMDagPathObject )
        else :
            typeFilter.setObjectType ( OpenMaya.MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if breadth :
        traversal = OpenMaya.MItDag.kBreadthFirst 
    else :
        traversal =  OpenMaya.MItDag.kDepthFirst
    iterObj = OpenMaya.MItDag ( typeFilter, traversal )
    if root is not None :
        iterObj.reset ( typeFilter, startObj, startPath, traversal )
 
    if underworld :
        iterObj.traverseUnderWorld (True)
    else :
        iterObj.traverseUnderWorld (False) 
    # iterates and yields MObject or MDagPath
    # handle prune ?

    # Must define dPath in loop or the iterator will yield
    # them as several references to the same object (thus with the same value each time)
    # instances must not be returned multiple times
    # could use a dict but it requires "obj1 is obj2" and not only "obj1 == obj2" to return true to
    # dic = {}
    # dic[obj1]=True
    # dic.has_key(obj2) 
    instance = []
    # code doesn't look nice but Im putting the tests out of the iter loops to loose as little speed as possible,
    # will certainly define functions for each case
    if allPaths :
        dPathArray = OpenMaya.MDagPathArray()
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    iterObj.getAllPaths(dPathArray)
                    nbDagPath = dPathArray.length()
                    for i in range(nbDagPath) :
                        dPath = OpenMaya.MDagPath(dPathArray[i])
                        yield dPath
                    instance.append(obj)
            else :
                iterObj.getAllPaths(dPathArray)
                nbDagPath = dPathArray.length()
                for i in range(nbDagPath) :
                    dPath = OpenMaya.MDagPath(dPathArray[i])
                    yield dPath
            iterObj.next()
    elif path :
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    dPath = OpenMaya.MDagPath()
                    iterObj.getPath(dPath)
                    yield dPath
                    instance.append(obj)
            else :
                dPath = OpenMaya.MDagPath()
                iterObj.getPath(dPath)
                yield dPath
            iterObj.next()                           
    else :
        while not iterObj.isDone() :
            obj = iterObj.currentItem()
            if iterObj.isInstanced ( True ) :
                if not obj in instance :
                    yield obj
                    instance.append(obj)
            else :
                yield obj
            iterObj.next()
         
#MItDag (  MIteratorType & dagInfoObject,  TraversalType  =  kDepthFirst ,  MStatus * ReturnStatus = NULL)
#
#kDepthFirst
#    kBreadthFirst 

def _optToDict(*args, **kwargs ):
    result = {}
    types = kwargs.get("valid", [])
    if not util.isSequence(types) :
        types = [types]
    if not basestr in types :
        types.append(basestr)
    for n in args :
        key = val = None
        if isinstance (n, basestr) :            
            if n.startswith("!") :
                key = n.lstrip('!')
                val = False          
            else :
                key = n
                val = True
            # strip all lead and end spaces
            key = key.strip()                       
        else :
            for t in types :
                if isinstance (n, t) :
                    key = n
                    val = True
        if key is not None and val is not None :
            # check for duplicates / contradictions
            if result.has_key(key) :
                if result[key] == val :
                    # already there, do nothing
                    pass
                else :
                    warnings.warn("%s=%s contradicts %s=%s, both ignored" % (key, val, key, result[key]))
                    del result[key]
            else :
                result[key] = val
        else :
            warnings.warn("'%r' has an invalid type for this keyword argument (valid types: %s)" % (n, types))
    return result                 
            
# calling the above iterators in iterators replicating the functionalities of the builtin Maya ls/listHistory/listRelatives
# TODO : add a condition keyword to pass a parsable logic expression of mixed conditions (my preferred way of calling it but
# might be too error prone for users ?)
def iterNodes ( *args, **kwargs ):
    """ Iterates on nodes of the argument list, or when args is empty on nodes of the Maya scene,
        that meet the given conditions.
        The following keywords change the way the iteration is done :
        selection=False
        above = 0
        below = 0
        parents=False
        childs=False        
        list = False
        tree = False
        breadth = False
        underworld = False
        allPaths = False
        prune = False
        The following flags specify conditions the iterated nodes are filtered against    
        name=None:
        position=None: 
        type=None: 
            The types are specified as Pymel or Maya types
        property=None:
        attribute=None:
        user=None:
        Conditions of the same type (same keyword) are combined as with a logical or for positive conditions :
        iterNodes(type = ['skinCluster', 'blendShape']) will iter on all nodes of type skinCluster OR blendShape
        Conditions of the type (same keyword) are combined as with a logical and for negative conditions :
        iterNodes(type = ['!transform', '!blendShape']) will iter on all nodes of type not transform AND not blendShape
        Different conditions types (different keyword) are combined as with a logical and :
        iterNodes(type = 'skinCluster', name = 'bodySkin*') will iter on all nodes that have type skinCluster AND whose name
        starts with 'bodySkin'. """

    # if a list of existing PyNodes (DependNodes) arguments is provided, only these will be iterated / tested on the conditions
    # TODO : pass the Pymel "Scene" object instead to list nodes of the Maya scene (instead of an empty arg list as for Maya's ls?
    # TODO : if a Tree or Dag of PyNodes is passed instead, make it work on it as wel    
    nodes = []
    for a in args :
        if isinstance(a, DependNode) :
            if a.exists() :
                if not a in nodes :
                    nodes.append(a)
            else :
                warnings.warn("'%r' does not exist, ignored" % a)
        else :
            warnings.warn("'%r' is not  valid PyNode (DependNode), ignored" % a)
    # check
    print nodes
    # parse kwargs for keywords
    # use current selection for *args
    select = int(kwargs.get('selection', 0))
    # also iterate on the hierarchy below or above (parents) that node for every iterated (dag) node
    below = int(kwargs.get('below', 0))
    above = int(kwargs.get('above', 0))
    # same as below(1) or above(1)
    childs = kwargs.get('childs', False)
    parents = kwargs.get('parents', False)
    if childs and below == 0 :
        below = 1
    if parents and above == 0 :
        above = 1  
    # return a tuple of all the hierarchy nodes instead of iterating on the nodes when node is a dag node
    # and above or below has been set
    asList = kwargs.get('list', False)
    # when below has been set, use breadth order instead of preorder for iterating the nodes below
    breadth = kwargs.get('breadth', False)
    # returns a Tree of all the hierarchy nodes instead of iterating on the nodes when node is a dag node
    # and above or below has been set
    asTree = kwargs.get('tree', False) 
    # include underworld in hierarchies
    underworld = kwargs.get('underword', False)                
    # include all instances paths for dag nodes (means parents can return more than one parent when allPaths is True)
    allPaths = kwargs.get('allPaths', False)
    # prune hierarchy (above or below) iteration when conditions are not met
    prune = kwargs.get('prune', False)
    # to use all namespaces when none is specified instead of current one
    # allNamespace = kwargs.get('allNamespace', False)
    # TODO : check for incompatible flags
    
    # selection
    if (select) :
        sel = _activeSelectionPyNode ()
        if not nodes :
            # use current selection
            nodes = sel
        else :
            # intersects, need to handle components
            for p in nodes :
                if p not in sel :
                    nodes.pop(p)
            
    # Add a conditions with a check for contradictory conditions
    def _addCondition(cDic, key, val):
        # check for duplicates
        if key is not None : 
            if cDic.has_key(key) and vDic[key] != val :
                # same condition with opposite value contradicts existing condition
                warnings.warn("Condition '%s' is present with mutually exclusive True and False expected result values, both ignored" % key)
                del cDic[key]
            else :
                cDic[key] = val
                return True
        return False     
                 
    # conditions on names (regular expressions, namespaces), can be passed as a dict of
    # condition:value (True or False) or a sequence of conditions, with an optional first
    # char of '!' to be tested for False instead of True. It can be an actual node name
    nameArgs = kwargs.get('name', None)
    # the resulting dictionnary of conditions on names (compiled regular expressions)
    cNames = {}
    # check
    print nameArgs   
    if nameArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(nameArgs):
            if not util.isSequence(nameArgs) :
                nameArgs = [nameArgs]    
            nameArgs = _optToDict(*nameArgs)
        # check
        print nameArgs
        # for names parsing
        invalidCharPattern = r"[^(a-z)^(A-Z)^(0-9)^_^*^?^:]"
        validCharPattern = r"[a-zA-Z0-9_]"
        namePattern = r"[a-zA-Z]+[a-zA-Z0-9_]*"
        nameSpacePattern = r"[a-zA-Z]+[a-zA-Z0-9_]*:"
        invalidChars = re.compile(r"("+invalidCharPattern+")+")
        validNameSpace = re.compile(r"^:?"+"("+nameSpacePattern+")*")
        validName = re.compile(namePattern+r"$")
        validFullName = re.compile(r"(^:?(?:"+nameSpacePattern+r")*)("+namePattern+r")$")
        curNameSpace = namespaceInfo( currentNamespace=True )    
        for i in nameArgs.items() :
            key = i[0]
            val = i[1]
            if key.startswith('(') and key.endswith(')') :
                # take it as a regular expression directly
                pass
            else :
                # either a valid node name or a glob pattern
                nameMatch = validFullName.match(key)
                if nameMatch is not None :
                    # if it's an actual node name
                    nameSpace = nameMatch.group[0]
                    name = nameMatch.group[1]
                    print nameSpace, name
                    if not nameSpace :
                        # if no namespace was specified use current ('*:' can still be used for 'all namespaces')
                        nameSpace = curNameSpace
                    if namespace(exists=nameSpace) :
                        # format to have distinct match groups for nameSpace and name
                        key = r"("+nameSpace+r")("+name+r")"
                    else :
                        warnings.warn("'%s' uses inexistent nameSpace '%s' and will be ignored" % (key, nameSpace))
                        continue
                else :
                    badChars = invalidChars.findall(key)
                    if badChars :
                        # invalid characters, ignore name
                        warnings.warn("'%s' contains invalid characters %s, ignored" % (key, badChars))
                        continue
                    elif '*' in key or '?' in key :
                        # it's a glob pattern, try build a re out of it and add it to names conditions
                        key = key.replace("*", r"("+validCharPattern+r")*")
                        key = key.replace("?", r"("+validCharPattern+r")")
                    else : 
                        # it's not anything we recognize
                        warnings.warn("'%s' is not a valid node name or glob/regular expression and will be ignored" % a)
            try :
                r = re.compile(key)
            except :
                warnings.warn("'%s' is not a valid regular expression, ignored" % key)
                continue
            # check for duplicates re and add
            _addCondition(cNames, r, val)
        # check
        for r in cNames.keys() :
            print "%s:%r" % (r.pattern, cNames[r])     
      
    # conditions on position in hierarchy (only apply to dag nodes)
    # can be passed as a dict of conditions and values
    # condition:value (True or False) or a sequence of conditions, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # valid flags are 'root', 'leaf', or 'level=x' for a relative depth to start node 
    posArgs = kwargs.get('position', None)
    # check
    print posArgs    
    cPos = {}    
    if posArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(posArgs):
            if not util.isSequence(posArgs) :
                posArgs = [posArgs]    
            posArgs = _optToDict(*posArgs)    
        # check
        print posArgs
        validLevelPattern = r"level\[(-?[0-9]*)(:?)(-?[0-9]*)\]"
        validLevel = re.compile(validLevelPattern)
        for i in posArgs.items() :
            key = i[0]
            val = i[1]
            if key == 'root' or key == 'leaf' :
                pass           
            elif key.startswith('level') :
                levelMatch = validLevel.match(key)
                level = None
                if levelMatch is not None :
                    if levelMatch.groups[1] :
                        # it's a range
                        lstart = lend = None
                        if levelMatch.groups[0] :
                            lstart = int(levelMatch.groups[0])
                        if levelMatch.groups[2] :
                            lend = int(levelMatch.groups[2])
                        if lstart is None and lend is None :
                            level = None
                        else :                      
                            level = int(lstart, lend)
                    else :
                        # it's a single value
                        if levelMatch.groups[1] :
                            level = None
                        elif levelMatch.groups[0] :
                            level = int(levelMatch.groups[0])
                        else :
                            level = None               
                if level is None :
                    warnings.warn("Invalid level condition %s, ignored" % key)
                    key = None
                else :
                    key = level     
            else :
                warnings.warn("Unknown position condition %s, ignored" % key)
                key = None
            # check for duplicates and add
            _addCondition(cPos, key, val)            
            # TODO : check for intersection with included levels
        # check
        for r in cPos.keys() :
            print "%s:%r" % (r, cPos[r])    
                           
    # conditions on types
    # can be passed as a dict of types (Maya or Pymel type names) and values
    # condition:value (True or False) or a sequence of type names, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # valid flags are 'root', 'leaf', or 'level=x' for a relative depth to start node                       
    # Note: API iterators can filter on API types, we need to postfilter for all the rest
    typeArgs = kwargs.get('type', None)
    # check
    print typeArgs
    # support for types that can be translated as API types and can be directly used by API iterators
    # and other types that must be post-filtered  
    cAPITypes = {}
    cExtTypes = {}
    cAPIFilter = []
    if typeArgs is not None :
        extendedFilter = False
        apiFilter = False
        # convert list to dict if necessary
        if not util.isMapping(typeArgs):
            if not util.isSequence(typeArgs) :
                typeArgs = [typeArgs]
            # can pass strings or PyNode types directly
            typeArgs = _optToDict(*typeArgs, **{'valid':DependNode})    
        # check
        print typeArgs
        for i in typeArgs.items() :
            key = i[0]
            val = i[1]
            apiType = extType = None
            if isValidMayaTypeName (key) :
                # is it a valid Maya type name
                extType = key
                # can we translate it to an API type enum (int)
                apiType = _nodeTypeToApiType(extType)
            else :
                # or a PyNode type or type name
                if isValidPyNodeTypeName(key) :
                    key = PyNodeTypeNames().get(key, None)
                if isValidPyNodeType(key) :
                    extType = key
                    apiType = PyNodeToMayaAPITypes().get(key, None)
            # if we have a valid API type, add it to cAPITypes, if type must be postfiltered, to cExtTypes
            if apiType is not None :
                if _addCondition(cAPITypes, apiType, val) :
                    if val :
                        apiFilter = True
            elif extType is not None :
                if _addCondition(cExtTypes, extType, val) :
                    if val :
                        extendedFilter = True
            else :
                warnings.warn("Invalid/unknown type condition %s, ignored" % key)  
        # check
        for r in cAPITypes.keys() :
            print "%s:%r" % (r, cAPITypes[r])   
        for r in cExtTypes.keys() :
            print "%s:%r" % (r, cExtTypes[r])
        # if we check for the presence (positive condition) of API types and API types only we can 
        # use the API MIteratorType for faster filtering, it's not applicable if we need to prune
        # iteration for unsatisfied conditions
        if apiFilter and not extendedFilter and not prune :
            for item in cAPITypes.items() :
                if item[1] and MayaAPITypesInt.has_key(item[0]) :
                     cAPIFilter.append(MayaAPITypesInt()[item[0]])
        # check
        print cAPIFilter  
                          
    # conditions on pre-defined properties (visible, ghost, etc) for compatibility with ls
    validProperties = {'visible':1, 'ghost':2, 'templated':3, 'intermediate':4}    
    propArgs = kwargs.get('properties', None)
    # check
    print propArgs    
    cProp = {}    
    if propArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(propArgs):
            if not util.isSequence(propArgs) :
                propArgs = [propArgs]    
            propArgs = _optToDict(*propArgs)    
        # check
        print propArgs
        for i in propArgs.items() :
            key = i[0]
            val = i[1]
            if validProperties.has_key(key) :
                # key = validProperties[key]
                _addCondition(cProp, key, val)
            else :
                warnings.warn("Unknown property condition %s, ignored" % key)
        # check
        for r in cProp.keys() :
            print "%s:%r" % (r, cProp[r])      
    # conditions on attributes existence / value
    # can be passed as a dict of conditions and booleans values
    # condition:value (True or False) or a sequence of conditions,, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # An attribute condition is in the forms :
    # attribute==value, attribute!=value, attribute>value, attribute<value, attribute>=value, attribute<=value, 
    # Note : can test for attribute existence with attr != None
    attrArgs = kwargs.get('attribute', None)
    # check
    print attrArgs    
    cAttr = {}    
    if attrArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(attrArgs):
            if not util.isSequence(attrArgs) :
                attrArgs = [attrArgs]    
            attrArgs = _optToDict(*attrArgs)    
        # check
        print attrArgs      
        attrNamePattern = r"([a-zA-Z]+[a-zA-Z0-9_]*)(\[[0-9]+\])?"
        attrValuePattern = r".+"
        validAttrName = re.compile(attrNamePattern)
        attrPattern = r"\.?("+attrNamePattern+r")(\."+attrNamePattern+r")*"
        validAttr = re.compile(attrPattern)
        attrCondPattern = r"(?P<attr>"+attrPattern+r")[ \t]*(?P<oper>==|!=|>|<|>=|<=)[ \t]*(?P<value>"+attrValuePattern+r")"
        validAttrCond = re.compile(attrCondPattern)        
        for i in attrArgs.items() :
            key = i[0]
            val = i[1]
            attCondMatch = validAttrCond.match(key.strip())
            if attCondMatch is not None :
                attCond = (attCondMatch.group('attr'), attCondMatch.group('oper'), attCondMatch.group('value'))
                # handle inversions
                if val is False :
                    if attCond[1] is '==' :
                        attCond[1] = '!='
                    elif attCond[1] is '!=' :
                        attCond[1] = '=='
                    elif attCond[1] is '>' :
                        attCond[1] = '<='
                    elif attCond[1] is '<=' :
                        attCond[1] = '>'
                    elif attCond[1] is '<' :
                        attCond[1] = '>='
                    elif attCond[1] is '>=' :
                        attCond[1] = '<'                        
                    val = True
                # Note : special case where value is None, means test for attribute existence
                # only valid with != or ==
                if attCond[2] is None :
                    if attCond[1] is '==' :
                        attCond[1] = None
                        val = False  
                    elif attCond[1] is '!=' :
                        attCond[1] = None
                        val = True
                    else :
                        warnings.warn("Value 'None' means testing for attribute existence and is only valid for operator '!=' or '==', '%s' ignored" % key)
                        attCond = None
                # check for duplicates and add
                _addCondition(cPos, attCond, val)                                               
            else :
                warnings.warn("Unknown attribute condition %s, ignored (must be in the form attr" % key)            
        # check
        for r in cAttr.keys() :
            print "%s:%r" % (r, cAttr[r])        
    # conditions on user defined boolean functions
    userArgs = kwargs.get('user', None)
    # check
    print userArgs    
    cUser = {}    
    if userArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(userArgs):
            if not util.isSequence(userArgs) :
                userArgss = [userArgs]    
            userArgs = _optToDict(*userArgs, **{'valid':function})    
        # check
        print userArgs            
        for i in userArgs.items() :
            key = i[0]
            val = i[1]
            if isinstance(key, basestr) :
                key = globals().get(key,None)
            if key is not None :
                if inspect.isfunction(key) and len(inspect.getargspec(key)[0]) is 1 :
                    _addCondition(cUser, key, val)
                else :
                    warnings.warn("user condition must be a function taking one argument (the node) that will be tested against True or False, %r ignored" % key)
            else :
                warnings.warn("name '%s' is not defined" % key)            
        # check
        for r in cUser.keys() :
            print "%r:%r" % (r, cUser[r])


    # post filtering function
    def _filter( pyobj, types=True, names=True, pos=True, prop=True, attr=True, user=True  ):
        result = True
        # check on types conditions
        if result and types :
            for ct in cAPITypes.items() :
                if pyobj.type() == ct[0] :
                    result &= cn[1]
                    break
            for ct in cExtTypes.items() :                      
                if isinstance(pyobj, ct[0]) :
                    result &= cn[1]
                    break        
        # check on names conditions
        if result and names :
            for cn in cNames.items() :
                if cn[0].match(pyobj) is not None :
                    result &= cn[1]
                    break             
        # check on position (for dags) conditions
        if result and pos and isinstance(pyobj, DagNode) :
            for cp in cPos.items() :
                if cp[0] == 'root' :
                    if pyobj.isRoot() :
                        result &= cn[1]
                        break
                elif cp[0] == 'leaf' :
                    if pyobj.isLeaf() :
                        result &= cn[1]
                        break                  
                # TODO : 'level' condition
        # check some pre-defined properties
        if result and prop :
            for cp in cProp.items() :
                if cp[0] == 'visible' :
                    # check if object is visible means also check parents for visibility
                    pass
                    # if pyobj.hasAttr('visibility') :                
                elif cp[0] == 'ghost' :
                    pass           
                elif cp[0] == 'templated' :
                    pass
                elif cp[0] == 'intermediate' :
                    pass
        # check for attribute existence and value
        if result and attr :
            pass
        # check for used condition functions
        if result and user :
            pass
        return result
            
    # Iteration :
    needLevelInfo = False
    
    if nodes :
        # if a list of existing nodes is provided we iterate on the ones that both exist and match the used flags        
        for pyobj in nodes :
            if _filter (pyobj) :
                yield pyobj
    else :
        # else we iterate on all scene nodes that satisfy the specified flags, 
        for obj in MItNodes( *cAPIFilter ) :
            pyobj = _MObjectPyNode( obj )
            if _filter (pyobj) :
                yield pyobj
        
# lst = list(iterNodes())

def iterConnections ( *args, **kwargs ):
    pass

def iterHierarchy ( *args, **kwargs ):
    pass




    # mayaType (nodeOrType, **kwargs) :
#    typeInt = []
#    for t in type :
#        typeInt.append(MayaAPITypesInt[MayaTypesToAPI[t]])
        
# Get the maya type, maya API type, maya API type name, plugin status
# of an existing maya object or maya object type or maya API type or PyNode node or type
# It uses cached values for faster access but will try to directly check an unknown
# Maya type and add it to the cache using addToMayaTypesList if necessary
def mayaType (nodeOrType, **kwargs) :
    """ Get the maya type, maya API type, maya API type name, plugin status, inherited types
        of an existing maya object or maya object type or maya API type or PyNode node or type
        >>> mayaType ('time1', type=True, apiType=True, apiEnum=True)
        >>> {'apiEnum': 507, 'type': u'time', 'apiType': u'kTime'}
        >>> polySphere()
        >>> [Transform('pSphere1'), PolySphere('polySphere1')]
        >>> mayaType ('pSphere1', type=True, apiType=True, pymel=True)
        >>> {'pymel': <class 'pymel.core.Transform'>, 'type': u'transform', 'apiType': u'kTransform'}
        >>> mayaType ('vortexField', apiType=True)
        >>> 'kVortex'
        >>> mayaType ('vortexField', apiType=True, inheritedAPI=True)
        >>> {'inheritedAPI': ['kField', 'kDagNode', 'kDependencyNode', 'kBase'], 'apiType': 'kVortex'}
        >>> mayaType ('polyAppend', inherited=True)
        >>> [u'polyAppend', 'polyModifier', 'dependNode', 'base']
        >>> mayaType ('kField')
        >>> 'field'
        >>> mayaType ('kConstraint', pymel=True)
        >>> mayaType ('kConstraint')
        >>> 'constraint'
        >>> mayaType ('kVortex', pymel=True)
        >>> <class 'pymel.Vortex'>
        >>> mayaType ('Vortex', inheritedPymel=True)
        >>> [<class 'pymel.Vortex'>, <class 'pymel.core.DagNode'>, <class 'pymel.core.DependNode'>, <class 'pymel.core.node._BaseObj'>]        
        >>> mayaType ('aimConstraint', apiType=True, inheritedAPI=True)
        >>> {'inheritedAPI': ['kConstraint'], 'apiType': 'kAimConstraint'}
        >>> mayaType (pymel.Transform)
        >>> u'transform'
        >>> mayaType (pymel.Transform, apiType=True)
        >>> 'kTransform'
        """
    apiTypeInt = None           # OpenMaya.MFn.kInvalid is 0, OpenMaya.MFn.kBase is 1
    apiTypeStr = None
    mayaType = None
    pyNodeType = None
    isPluginObject = None
    inherited = []
    apiInherited = []
    pymelInherited = []

    result = {}
    do_type, do_apiInt, do_apiStr, do_plugin, do_pymel, do_inherited, do_apiInherited = False, False, False, False, False, False, False
    if not kwargs :
        do_type = True
    else :
        do_type = kwargs.get('type', False)
        do_apiInt = kwargs.get('apiEnum', False)
        do_apiStr = kwargs.get('apiType', False)
        do_plugin = kwargs.get('plugin', False)
        do_pymel = kwargs.get('pymel', False)
        do_inherited = kwargs.get('inherited', False)
        do_apiInherited = kwargs.get('inheritedAPI', False)
        do_pymelInherited = kwargs.get('inheritedPymel', False)
                   
    # check what was passed as argument
    if (objExists(nodeOrType)) :      # @UndefinedVariable
        # Existing object, easy to find out
        mayaType = nodeType(nodeOrType)      # @UndefinedVariable
        apiTypeStr = nodeType(nodeOrType, apiType=True)     # @UndefinedVariable
        if do_inherited :
            inherited = nodeType(nodeOrType, inherited=True) 
    elif type(nodeOrType) == int :
        # MFn.Types enum int
        apiTypeStr = MayaIntAPITypes()[nodeOrType] 
    elif MayaAPITypesInt().has_key(nodeOrType) :
        # API type
        apiTypeStr = nodeOrType
    elif ShortMayaTypes().has_key(nodeOrType) :
        # shortcut for a maya type
        mayaType = ShortMayaTypes()[nodeOrType]
    elif MayaTypesToAPI().has_key(nodeOrType) :
        # Maya type
        mayaType = nodeOrType
    elif PyNodeToMayaAPITypes().has_key(nodeOrType) :
        # PyNode type
        pyNodeType = nodeOrType
        apiTypeStr = PyNodeToMayaAPITypes()[pyNodeType]
    elif isinstance(nodeOrType, DependNode) :
        # a PyNode object
        pyNodeType = type(nodeOrType)
        apiTypeStr = PyNodeToMayaAPITypes().get(pyNodeType, None)
    elif isinstance(nodeOrType, basestring) : 
        # check if it could be a PyMel type name
        if (hasattr(pymel, nodeOrType)) :
            pyAttr = getattr (pymel, nodeOrType)
            if inspect.isclass(pyAttr) :
                if issubclass(pyAttr, node._BaseObj) :
                    pyNodeType = pyAttr
                    apiTypeStr = PyNodeToMayaAPITypes().get(pyNodeType, None)
        # check if it could be a not yet cached Maya type
        if not apiTypeStr and not mayaType :
            if addToMayaTypesList(nodeOrType) :
                mayaType = nodeOrType
                apiTypeStr = MayaTypesToAPI()[mayaType]
            
    # minimum is to know Maya or API type
    if mayaType or apiTypeStr :
        if mayaType and not apiTypeStr :
            apiTypeStr = MayaTypesToAPI().get(mayaType, None)
        elif not mayaType and apiTypeStr :
            if do_type :
                mayatypes = MayaAPIToTypes()[apiTypeStr].keys()
                if len(mayatypes) == 1 :
                    mayaType = mayatypes[0]
                else :
                    mayaType = tuple(mayatypes)
    # no need to do more if we don't have a valid apiTypeStr               
    if apiTypeStr and apiTypeStr is not 'kInvalid' :                    
        if do_apiInt :
            apiTypeInt = MayaAPITypesInt().get(apiTypeStr, None)
        if do_plugin :
            isPluginObject = 'Plugin' in apiTypeStr
        if do_pymel and not pyNodeType :
            pyNodeType = MayaAPITypesToPyNode().get(apiTypeStr, None)                
        if do_inherited or do_apiInherited :
            k = apiTypeStr
            apiInherited.append(k)      # starting class
            while k is not 'kBase' and MayaAPITypesHierarchy().has_key(k) :
                k = MayaAPITypesHierarchy()[k]
                apiInherited.append(k)
            if do_inherited and not inherited :
                # problem, there can be more than one maya type for an API type, we take the "default" one is one is marked so
                # else we just take first (until we an get a separate maya type tree, it's not 100% satisfactory)
                for k in apiInherited :
                    mTypes = MayaAPIToTypes()[k].keys()
                    defType = None
                    if len(mTypes) > 1 :
                        for t in mTypes :
                            if MayaAPIToTypes()[k][t] :
                                defType = t
                                break
                    if defType is None and mTypes :
                        defType = mTypes[0]
                    inherited.append(defType)       
        if do_pymelInherited :
            k = pyNodeType
            pymelInherited.append(k)      # starting class
            while k is not 'node._BaseObj' and PyNodeTypesHierarchy().has_key(k) :
                k = PyNodeTypesHierarchy()[k]
                pymelInherited.append(k)            
            
    # format result
    if do_type :
        result['type'] = mayaType
    if do_apiStr :
        result['apiType'] = apiTypeStr
    if do_apiInt :
        result['apiEnum'] = apiTypeInt
    if do_plugin :
        result['plugin'] = isPluginObject
    if do_pymel :
        result['pymel'] = pyNodeType
    if do_inherited :
        result['inherited'] = inherited
    if do_apiInherited :
        result['inheritedAPI'] = apiInherited          
    if do_pymelInherited :
        result['inheritedPymel'] = pymelInherited    
                
    if len(result) == 1 :
        return result[result.keys()[0]] 
    else :        
        return result                              

## isAType
# Checks if provided arguments are subtypes of type,
# arguments an be maya actual objects, or maya type names, or pymel 'PyNode' objects or types.
# If no arguments are provided, the current selection is used.
def isAType (*args, **kwargs) :
    """ checks if given Maya objects or type names, or AMtypes objects or pymel class names are of the given type or derive from it,
    it will accept pymel types (classes) or pymel type names (class.__name__)
    >>> isAType(Transform, type='kDagNode')
    >>> True
    >>> isAType(Transform, type='dag')
    >>> True
    >>> isAType ('kVortex', type='dag')
    >>> True
    >>> isAType ('kVortex', type='kField')
    >>> True
    >>> isAType ('vortexField', type='field')
    >>> True
    >>> isAType (Vortex, type=Field)
    >>> Traceback (most recent call last):
    >>> File "<stdin>", line 1, in <module>
    >>> NameError: name 'Field' is not defined
    >>> isAType ('Vortex', type='Field')
    >>> False
    >>> isAType ('Vortex', type='DagNode')
    >>> True
    >>> isAType (Vortex, type=DagNode)
    >>> True
    Note that the most reliable source now is API types, there are sometimes more than one maya type corresponding to an API type, and in that
    case, heritage only considers the first in the list (though mayaType will return all of them), and pymel types are not 100% identical to
    Maya API types in name and structure (though close)
    """
    result = []
    checkType = kwargs.get('type', None)
    # None defaults to checking if the type exists / is valid
    if checkType is None :
        checkType = 'kBase'
    # if a shortcut is used, get the real maya type name instead
    if ShortMayaTypes().has_key(checkType) :
        checkType = ShortMayaTypes()[checkType]
    # consider pymel, maya or api type, or try to determine type of 'type' argument
    check_pymel, check_maya, check_api = False, False, False
    typeInfo = mayaType(checkType, type=True, apiType=True, pymel=True)
    maType = typeInfo['type']
    apiType = typeInfo['apiType']
    pyNodeType = typeInfo['pymel']
    # only check on explicit kind of type given (maya, API or pymel)
    if checkType == pyNodeType :
        check_pymel = True
    elif checkType == maType :
        check_maya = True          
    elif checkType == apiType :
        check_api = True
    else :
        check_pymel = pyNodeType is not None
        check_maya = maType is not None
        check_api = apiType is not None
    # no recognizable type to checks objects against   
    if not check_pymel and not check_maya and not check_api :
        return
    # print args
    if len(args) == 0 :
        args = ls( selection=True)
    for arg in util.iterateArgs(*args) :
        test = False
        # special case, for an existing object checked vs a maya type, there is the objectType cmd
        if (objExists(arg)) and check_maya :
            test = test or bool(objectType(arg, isAType=maType))
        if check_pymel :
            test = test or pyNodeType in mayaType(arg, inheritedPymel=True)
        if check_maya :
            test = test or maType in mayaType(arg, inherited=True)
        if check_api :
            test = test or apiType in mayaType(arg, inheritedAPI=True)
        result.append(test)
                    
    if len(result) == 0 :
        # return False
        pass
    elif len(result) == 1 :
        return result[0]
    else :
        return tuple(result)
    
## isDag
# Checks if provided maya objects arguments are maya <b>dag nodes</b>,
# or if provided type names are subtypes of the dag type.
# If no arguments are provided, the current selection is used.

def isDag (*args) :
    """checks if given Maya objects or type names, or AMtypes objects or class names are DAG objects or DAG sub-types
    >>> isDag('locator')
    >>> True
    >>> polySphere()
    >>> [Transform('pSphere1'), PolySphere('polySphere1')]  
    >>> isDag ('pSphereShape1')
    >>> True
    >>> isDag('time1')
    >>> False
    >>> isDag(Transform)
    >>> True
    >>> isDag(Wire)
    >>> False
    """
    kwargs = {'type':'dagNode'}
    return isAType (*args, **kwargs)


"""
    An exemple of use of the Tree library, returns the arguments, or the current selection
    if nothing is provided :
    Open maya file skel.ma then :
    >>> select('FBX_Hips', hierarchy=True)
    >>> lst = ls(selection=True)
    >>> print lst
    >>> tree = asHierarchy (*lst)
    >>> print tree
    >>> print repr(tree)
    >>> lst
    >>> [k for k in tree]
"""

def isExactChildFn(c, p) :
    """ a function to check if c is a direct child of p """    
    if (c is not None) and (p is not None) :
        #print "checking if "+c+" is child of "+p
        prt = c.getParent()
        if prt is not None and p is not None :
            return prt == p
        elif prt is None and p is None :
            return True
        else :
            return False
    else :
        return False

def asHierarchy (*args) :
    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
        as argument, or the current seleciton if no arguments are provided,
        in a way that mimics the Maya scene hierarchy existing on these nodes.
        Note that:
        >>> cmds.file ("~/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
        >>> File read in 0 seconds.
        >>> u'~/pymel/examples/skel.ma'
        >>> select ('FBX_Hips', replace=True, hierarchy=True)
        >>> sel=ls(selection=True)
        >>> skel=asHierarchy (sel)
        >>> skel.find('FBX_Head')
        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
        >>> skel.parent('FBX_Head')
        >>> Joint('FBX_Neck1')      
        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
        >>> True """
        
    if len(args) == 0 :
        nargs = ls( selection=True)
    else :
        args = util.expandArgs (*args)
        nargs = map(PyNode, args)
    # print "Arguments: %s"+str(nargs)
    result = treeFromChildLink (isExactChildFn, *nargs)
    # print "Result: %s"+str(result)
    return result

def asIndexedHierarchy (*args) :
    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
        as argument, or the current seleciton if no arguments are provided,
        in a way that mimics the Maya scene hierarchy existing on these nodes.
        Note that:
        >>> cmds.file ("~/Eclipse/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
        >>> File read in 0 seconds.
        >>> u'~/pymel/examples/skel.ma'
        >>> select ('FBX_Hips', replace=True, hierarchy=True)
        >>> sel=ls(selection=True)
        >>> skel=asHierarchy (sel)
        >>> skel.find('FBX_Head')
        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
        >>> skel.parent('FBX_Head')
        >>> Joint('FBX_Neck1')      
        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
        >>> True """
        
    if len(args) == 0 :
        nargs = ls( selection=True)
    else :
        args = util.expandArgs (*args)
        nargs = map(PyNode, args)
    # print "Arguments: %s"+str(nargs)
    result = indexedTreeFromChildLink (isExactChildFn, *nargs)
    # print "Result: %s"+str(result)
    return result

#cmds.file ("~/Eclipse/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
#select ('FBX_Hips', replace=True, hierarchy=True)
#sel=ls(selection=True)
#ihTree = asIndexedHierarchy (sel)
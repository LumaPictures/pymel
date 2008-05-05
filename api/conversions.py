""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here
from maya.cmds import about as _about
from maya.cmds import ls as _ls

# import all available Maya API methods in this module (api)
from maya.OpenMaya import *
from maya.OpenMayaAnim import *
try: from maya.OpenMayaCloth import *
except: pass
try : from maya.OpenMayaFX import *
except: pass
try : from maya.OpenMayaMPx import *
except: pass
if not _about(batch=True) :
    try : from maya.OpenMayaUI import *
    except: pass
try : from maya.OpenMayaRender import *
except: pass

import sys, inspect, warnings, timeit, time, re
from pymel.util import Singleton, metaStatic, expandArgs, Tree, FrozenTree, treeFromDict
import pymel.util as util
import pickle, os.path

# TODO : would need this shared as a Singleton class, but importing from factories anywhere 
# except form core seems to be a problem
#from factories import NodeHierarchy

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

# fast convenience tests on API objects
def isValidMObjectHandle (obj):
    if isinstance(obj, MObjectHandle) :
        return obj.isValid() and obj.isAlive()
    else :
        return False

def isValidMObject (obj):
    if isinstance(obj, MObject) :
        return not obj.isNull()
    else :
        return False
    
def isValidMPlug (obj):
    if isinstance(obj, MPlug) :
        return not obj.isNull()
    else :
        return False

def isValidMDagPath (obj):
    if isinstance(obj, MDagPath) :
        return obj.isValid()
    else :
        return False

def isValidMNode (obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDependencyNode)
    else :
        return False

def isValidMDagNode (obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDagNode)
    else :
        return False
    
def isValidMNodeOrPlug (obj):
    return isValidMPlug (obj) or isValidMNode (obj)

# Maya static info :
# Initializes various static look-ups to speed up Maya types conversions

# this dictionary is filled in core.general
class PyNodesToApiTypes(Singleton, dict) :
    """Lookup of Pymel Nodes to corresponding Maya API types"""


# this dictionary is filled in core.general. (some Maya API types won't have a PyNode equivalent)
class ApiTypesToPyNodes(Singleton, dict) :
    """Lookup of Maya API types to corresponding Pymel Nodes"""

     
class ApiTypesToApiEnums(Singleton, dict) :
    """Lookup of Maya API types to corresponding MFn::Types enum"""
    
ApiTypesToApiEnums(dict(inspect.getmembers(MFn, lambda x:type(x) is int)))


class ApiEnumsToApiTypes(Singleton, dict) :
    """Lookup of MFn::Types enum to corresponding Maya API types"""

ApiEnumsToApiTypes(dict((ApiTypesToApiEnums()[k], k) for k in ApiTypesToApiEnums().keys()))

# Reserved Maya types and API types that need a special treatment (abstract types)
# TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
# strangely createNode ('cluster') works but dgMod.createNode('cluster') doesn't

# added : filters them to weed out those not present in current version

class ReservedMayaTypes(dict) :
    __metaclass__ =  metaStatic
# Inverse lookup
class ReservedAPITypes(dict) :
    __metaclass__ =  metaStatic

def _buildMayaReservedTypes():
    """ Build a list of Maya reserved types.
        These cannot be created directly from the API, thus the dgMod trick to find the corresonding Maya type won't work """
        
    reservedTypes = { 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
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
                'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip' }      # creating these 2 crash Maya      

    # filter to make sure all these types exist in current version (some are Maya2008 only)
    ReservedMayaTypes ( dict( (item[0], item[1]) for item in filter(lambda i:i[1] in ApiTypesToApiEnums(), reservedTypes.iteritems()) ) )
    # build reverse dict
    ReservedAPITypes ( dict( (item[1], item[0]) for item in ReservedMayaTypes().iteritems() ) )
    
    return ReservedMayaTypes(), ReservedAPITypes()
    
# build them
_buildMayaReservedTypes()

# some handy aliases / shortcuts easier to remember and use than actual Maya type name
class ShortMayaTypes(dict) :
    __metaclass__ =  metaStatic
    
ShortMayaTypes({'all':'base', 'valid':'base', 'any':'base', 'node':'dependNode', 'dag':'dagNode', \
                'deformer':'geometryFilter', 'weightedDeformer':'weightGeometryFilter', 'geometry':'geometryShape', \
                'surface':'surfaceShape', 'revolved':'revolvedPrimitive', 'deformable':'deformableShape', \
                'curve':'curveShape' })                
                   
class MayaTypesToApiTypes(Singleton, dict) :
    """ Lookup of currently existing Maya types as keys with their corresponding API type as values.
    Not a read only (static) dict as these can change (if you load a plugin)"""


class ApiTypesToMayaTypes(Singleton, dict) :
    """ Lookup of currently existing Maya API types as keys with their corresponding Maya type as values.
    Not a read only (static) dict as these can change (if you load a plugin)
    In the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )"""

# get the API type from a maya type
def mayaTypeToApiType (mayaType) :
    """ Get the Maya API type from the name of a Maya type """
    try:
        return MayaTypesToApiTypes()[mayaType]
    except:
        apiType = 'kInvalid'
    
        # Reserved types must be treated specially
        if ReservedMayaTypes().has_key(mayaType) :
            # It's an abstract type            
            apiType = ReservedMayaTypes()[mayaType]
        else :
            # we create a dummy object of this type in a dgModifier
            # as the dgModifier.doIt() method is never called, the object
            # is never actually created in the scene
            obj = MObject() 
            dagMod = MDagModifier()
            dgMod = MDGModifier()          
            try :
                parent = dagMod.createNode ( 'transform', MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
            apiType = obj.apiTypeStr()
                              
        return apiType                      


def addToMayaTypes(mayaType, apiEnum, PyNodeType ) :
    """ Add a type to the MayaTypes lists """

    MayaTypesToApiEnums()[mayaType] = apiEnum
    ApiEnumsToMayaTypes()[apiEnum] = mayaType
    

    # this will happen for initial building and when a pluging is loaded that registers new types
    apiType = mayaTypeToApiType(mayaType)
    if apiType is not 'kInvalid' :
        MayaTypesToApiTypes()[mayaType] = apiType
        if not ApiTypesToMayaTypes().has_key(apiType) :
            ApiTypesToMayaTypes()[apiType] = { mayaType : None } # originally: dict( ((mayaType, None),) ) 
        else :
            ApiTypesToMayaTypes()[apiType][mayaType] = None

        if not ApiTypesToMayaTypes().has_key(apiType) :
            ApiTypesToMayaTypes()[apiType] = { PyNodeType : None } 
        else :
            ApiTypesToMayaTypes()[apiType][PyNodeType] = None
            
        ApiTypesToApiEnums()[apiType] = apiEnum
        ApiEnumsToApiTypes()[apiEnum] = apiType


# Initialises/updates MayaTypes for a faster later access
def updateMayaTypesList() :
    """Updates the cached MayaTypes lists """
    start = time.time()
    # use dict of empty keys just for faster random access
    typeList = dict( ReservedMayaTypes().items() + [(k, None) for k in _ls(nodeTypes=True)] )
    # remove types that no longuer exist
    for k in MayaTypesToApiTypes().keys() :
        if not typeList.has_key(k) :
            # this could happen when a plugin is unloaded and some types become unregistered
            api = MayaTypesToApiTypes()[k]
            mtypes = ApiTypesToMayaTypes()[api]
            mtypes.pop(k)
            MayaTypesToApiTypes().pop(k)
    # add new types
    for k in typeList.keys() :
         if not MayaTypesToApiTypes().has_key(k) :
            # this will happen for initial building and when a plugin is loaded that registers new types
            api = typeList[k]
            if not api :
                api = mayaTypeToApiType(k)
            MayaTypesToApiTypes()[k] = api
            # can have more than one Maya type associated with an API type (yeah..)
            # we mark one as "default" if it's a member of the reserved type by associating it with a True value in dict
            defType = ReservedMayaTypes().has_key(k)
            if not ApiTypesToMayaTypes().has_key(api) :
                ApiTypesToMayaTypes()[api] = dict( ((k, defType),) )
            else :
                ApiTypesToMayaTypes()[api][k] = defType   
    elapsed = time.time() - start
    print "Updated Maya types list in %.2f sec" % elapsed

            
# initial update  
updateMayaTypesList()

#: lookup tables for a direct conversion between Maya type to their MFn::Types enum
class MayaTypesToApiEnums(Singleton, dict) :
    """Lookup from Maya types to API MFn::Types enums """

MayaTypesToApiEnums((k, ApiTypesToApiEnums()[MayaTypesToApiTypes()[k]]) for k in MayaTypesToApiTypes().keys())


#: lookup tables for a direct conversion between API type to their MFn::Types enum 
class ApiEnumsToMayaTypes(Singleton, dict) :
    """Lookup from API MFn::Types enums to Maya types """

ApiEnumsToMayaTypes((MayaTypesToApiEnums()[k], k) for k in MayaTypesToApiEnums().keys())  
  
# Cache API types hierarchy, using MFn classes hierarchy and additionnal trials
# TODO : do the same for Maya types, but no clue how to inspect them apart from parsing docs

#: Reserved API type hierarchy, for virtual types where we can not use the 'create trick'
#: to query inheritance, as of 2008 types and API types seem a bit out of sync as API types
#: didn't follow latest Maya types additions...
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
    
    if type(dagMod) is not MDagModifier or type(dgMod) is not MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"
    # cant create these nodes, some would crahs MAya also
    if ReservedAPITypes().has_key(nodeType) or ReservedMayaTypes().has_key(nodeType) :
        return None   
    obj = MObject()
    if ApiTypesToMayaTypes().has_key(nodeType) :
        mayaType = ApiTypesToMayaTypes()[nodeType].keys()[0]
        apiType = nodeType
    elif MayaTypesToApiTypes().has_key(nodeType) :
        mayaType = nodeType
        apiType = MayaTypesToApiTypes()[nodeType]
    else :
        return None    
      
    try :
        parent = dagMod.createNode ( 'transform', MObject())
        obj = dagMod.createNode ( mayaType, parent )
    except :
        try :
            obj = dgMod.createNode ( mayaType )
        except :
            pass
    if isValidMObject(obj) :
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
    if ApiTypesToApiEnums().has_key(parentType) :
        typeInt = ApiTypesToApiEnums()[parentType]
    else :
        return False
    # print "need creation for %s" % apiType
    # we create a dummy object of this type in a dgModifier
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    obj = _getMObject(apiType, dagMod, dgMod, parentType) 
    if isValidMObject(obj) :
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
    if not isValidMObject(obj) :
        # print "need creation for %s" % apiType
        obj = _getMObject(apiType, dagMod, dgMod)
    if isValidMObject(obj) :
        if not kwargs.get(apiType, None) :
            kwargs[apiType] = obj          # update it if we had to create
        parents = []
        for t in kwargs.keys() :
            # Need the MFn::Types enum for the parentType
            if t != apiType :
                if ApiTypesToApiEnums().has_key(t) :
                    ti = ApiTypesToApiEnums()[t]
                    if obj.hasFn(ti) :
                        parents.append(t)
        # problem is the MObject.hasFn method returns True for all ancestors, not only first one
        if len(parents) :
            if len(parents) > 1 :
                for p in parents :
                    if ApiTypesToApiEnums().has_key(p) :
                        ip = ApiTypesToApiEnums()[p]
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


def _createNodes(dagMod, dgMod, *args) :
    """pre-build a type:MObject lookup for all provided types, be careful that these MObject
        can be used only as long as dagMod and dgMod are not deleted"""
        
    result = {}
    for k in args :
        mayaType = apiType = None
        if ApiTypesToMayaTypes().has_key(k) :
            mayaType = ApiTypesToMayaTypes()[k].keys()[0]
            apiType = k
        elif MayaTypesToApiTypes().has_key(k) :
            mayaType = k
            apiType = MayaTypesToApiTypes()[k]
        else :
            continue
        if ReservedAPITypes().has_key(apiType) or ReservedMayaTypes().has_key(mayaType) :
            result[apiType] = None
        else :
            obj = MObject()          
            try :
                parent = dagMod.createNode ( 'transform', MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
            if isValidMObject(obj) :
                result[apiType] = obj
            else :
                result[apiType] = None
    return result

# child:parent lookup of the Maya API classes hierarchy (based on the existing MFn class hierarchy)
# TODO : fix that, doesn't accept the Singleton base it seems
# class MayaAPITypesHierarchy(Singleton, FrozenTree) :
#    """ Hierarchy Tree of all API Types """

# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def _buildAPITypesHierarchy () :
    def _MFnType(x) :
        if x == MFnBase :
            return 1
        else :
            try :
                return x().type()
            except :
                return 0
            
    ver = util.getMayaVersion(extension=False)

    cacheFileName = os.path.join( util.moduleDir(),  'mayaApi'+ver+'.bin'  )
    try :
        file = open(cacheFileName, mode='rb')
        try :
            return pickle.load(file)
        except :
            print "Unable to load the Maya API Hierarchy from '"+file.name+"'"       
        file.close()
    except :
        print "Unable to open '"+cacheFileName+"' for reading the list of Maya commands"
    

    print "Rebuilding the Maya API Hierarchy..."
       
    # all of maya OpenMaya api is now imported in module api's namespace
    MFn = inspect.getmembers(_thisModule, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#    try : MFn += inspect.getmembers(OpenMayaAnim, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#    except : pass
#    try : MFn += inspect.getmembers(OpenMayaCloth, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#    except : pass
#    try : MFn += inspect.getmembers(OpenMayaFX, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#    except : pass
#    try : MFn += inspect.getmembers(OpenMayaMPx, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#    except : pass
#    if not cmds._about(batch=True) :
#        try : MFn += inspect.getmembers(OpenMayaUI, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
#        except : pass
#    try : MFn += inspect.getmembers(OpenMayaRender, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))    
#    except : pass
    MFn = dict(MFn)
    MFnTree = inspect.getclasstree([MFn[k] for k in MFn.keys()])
    MFnDict = {}
    for x in expandArgs(MFnTree, type='list') :
        try :
            ct = _MFnType(x[0])
            pt = _MFnType(x[1][0])
            if ct and pt :
                MFnDict[ApiEnumsToApiTypes()[ct]] = ApiEnumsToApiTypes()[pt]
        except :
            pass
        
    # print MFnDict.keys()
    # Fixes for types that don't have a MFn by faking a node creation and testing it
    # Make it faster by pre-creating the nodes used to test
    dagMod = MDagModifier()
    dgMod = MDGModifier()      
    nodeDict = _createNodes(dagMod, dgMod, *ApiTypesToApiEnums().keys())
    # for k in nodeDict.keys() :
        # print "Cached %s : %s" % (k, nodeDict[k])
    # Fix? some MFn results are not coherent with the hierarchy presented in the docs :
    MFnDict.pop('kWire', None)
    MFnDict.pop('kBlendShape', None)
    MFnDict.pop('kFFD', None)
    for k in ApiTypesToApiEnums().keys() :
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
    # make a Tree from that child:parent dictionnary
                    
    apiTypesTree = FrozenTree(treeFromDict(MFnDict))
    try :
        file = open(cacheFileName, mode='wb')
        try :
            pickle.dump( apiTypesTree,  file, 2)
            print "done"
        except:
            print "Unable to write the Maya API Hierarchy to '"+file.name+"'"
        file.close()
    except :
        print "Unable to open '"+newPath+"' for writing"
        
    return apiTypesTree
    

# Initialize the API tree
# MayaAPITypesHierarchy(_buildAPITypesHierarchy())
# initial update  
start = time.time()
# MayaAPITypesHierarchy(_buildAPITypesHierarchy())
mayaAPITypesHierarchy = _buildAPITypesHierarchy()
# quick fix until we can get a Singleton MayaAPITypesHierarchy() up
def MayaAPITypesHierarchy() :
    return mayaAPITypesHierarchy

elapsed = time.time() - start
print "Initialized Maya API types hierarchy tree in %.2f sec" % elapsed

# TODO : to represent plugin registered types we might want to create an updatable (dynamic, not static) MayaTypesHierarchy ?

# conversion node type -> api type

# conversion API enum int to API type string and back
def apiEnumToType (apiEnum) :
    """ Given an API type enum int, returns the corresponding Maya API type string,
        as in MObject.apiType() to MObject.apiTypeStr() """    
    return ApiEnumsToApiTypes().get(apiEnum, None)

def apiTypeToEnum (apiType) :
    """ Given an API type string, returns the corresponding Maya API type enum (int),
        as in MObject.apiTypeStr() to MObject.apiType()"""    
    return ApiTypesToApiEnums().get(apiType, None)

# get the maya type from an API type
def apiEnumToNodeType (apiTypeEnum) :
    """ Given an API type enum int, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return ApiEnumsToMayaTypes().get(apiTypeEnum, None)

def apiTypeToNodeType (apiType) :
    """ Given an API type name, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return ApiTypesToMayaTypes().get(apiType, None)

def nodeTypeToAPIType (nodeType) :
    """ Given an Maya node type name, returns the corresponding Maya API type name,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return MayaTypesToApiTypes().get(nodeType, None)

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

def apiTypeToPyNode( arg, default=None ):
    return ApiTypesToPyNodes().get(arg, default)

# Converting API MObjects and more

## type for a MObject with nodeType / objectType like options
#def objType (obj, api=True, inherited=True):
#    """ Returns the API or Node type name of MObject obj, and optionnally
#        the list of types it inherits from.
#            >>> obj = api.toMObject ('pCubeShape1')
#            >>> api.objType (obj, api=True, inherited=True)
#            >>> # Result: ['kBase', 'kDependencyNode', 'kDagNode', 'kMesh'] #
#            >>> api.objType (obj, api=False, inherited=True)
#            >>> # Result: ['dependNode', 'entity', 'dagNode', 'shape', 'geometryShape', 'deformableShape', 'controlPoint', 'surfaceShape', 'mesh'] # 
#        Note that unfortunatly API and Node types do not exactly match in their hierarchy in Maya
#    """
#    result = obj.apiType()
#    if api :
#        result = apiEnumToType (result)
#        if inherited :
#            result = [k.value for k in MayaAPITypesHierarchy().path(result)]    
#    else :
#        result = apiEnumToNodeType (result)
#        if inherited :
#            result =  [k.value for k in NodeHierarchy().path(result)]   
#    return result
            
# returns a MObject for an existing node
def toMObject (nodeName):
    """ Get the API MObject given the name of an existing node """ 
    sel = MSelectionList()
    obj = MObject()
    result = None
    try :
        sel.add( nodeName )
        sel.getDependNode( 0, obj )
        if isValidMObject(obj) :
            result = obj 
    except :
        pass
    return result

def toAPIObject (nodeName):
    """ Get the API MPlug, MObject or (MObject, MComponent) tuple given the name of an existing node, attribute, components selection """ 
    sel = MSelectionList()
    obj = MObject()
    result = None
    try :
        sel.add( nodeName )
        sel.getDependNode( 0, obj )
        if isValidMObject(obj) :
            result = obj
            # TODO : better parsing
            if "." in nodeName :
                # attribute or component
                nameSplt = nodeName.split(".", 1)
                try :
                    depFn = MFnDependencyNode(obj)
                    attr = depFn.attribute (nameSplt[-1])
                    result = MPlug(obj, attr)
                except :
                    pass   
    except :
        pass
    return result

def toMDagPath (nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """ 
    obj = toMObject (nodeName)
    if obj :
        dagFn = MFnDagNode (obj)
        dagPath = MDagPath()
        dagFn.getPath ( dagPath )
        return dagPath

# returns a MPlug for an existing plug
def toMPlug (plugName):
    """ Get the API MObject given the name of an existing plug (node.attribute) """
    nodeAndAttr = plugName.split('.', 1)
    obj = toMObject (nodeAndAttr[0])
    plug = None
    if obj :
        depNodeFn = MFnDependencyNode(obj)
        attr = depNodeFn.attribute(nodeAndAttr[1])
        plug = MPlug ( obj, attr )
        if plug.isNull() :
            plug = None
    return plug


# MDagPath, MPlug or MObject to name
# Note there is a kNamedObject API type but not corresponding MFn, thus
# I see no way of querying the name of something that isn't a kDependency node or a MPlug
# TODO : add components support, short/ long name support where applies
def MObjectName( obj ):
    """ Get the name of an existing MPlug, MDagPath or MObject representing a dependency node""" 
    if isValidMPlug (obj) :
        return obj.name()
    elif isValidMNode (obj) :
        depNodeFn = MFnDependencyNode(obj)
        return depNodeFn.name()
    elif isValidMDagPath (obj):
        # return obj.fullPathName()
        return obj.partialPathName()
    else :
        return unicode(obj)


# names to MObjects function (expected to be faster to share one selectionList)
def nameToMObject( *args ):
    """ Get the API MObjects given names of existing nodes """ 
    sel = MSelectionList() 
    for name in args :
        sel.add( name )
    result = []            
    obj = MObject()            
    for i in range(sel.length()) :
        try :
            sel.getDependNode( i, obj )
        except :
            result.append(None)
        if isValidMObject(obj) :
            result.append(obj)
        else :
            result.append(None)
    if len(result) == 1:
        return result[0]
    else :
        return tuple(result)
    
    
# wrap of api iterators

def MItNodes( *args, **kwargs ):
    """ Iterator on MObjects of nodes of the specified types in the Maya scene,
        if a list of tyes is passed as args, then all nodes of a type included in the list will be iterated on,
        if no types are specified, all nodes of the scene will be iterated on
        the types are specified as Maya API types """
    typeFilter = MIteratorType()
    if args : 
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) typeFilter
    iterObj = MItDependencyNodes ( typeFilter )     
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
#    startObj = MObject() 
#    startPlug = MPlug()
    startObj = None
    startPlug = None   
    if isValidMPlug(nodeOrPlug):
        startPlug = nodeOrPlug
    elif isValidMNode(nodeOrPlug) :
        startObj = nodeOrPlug
    else :
        raise ValueError, "'%s' is not a valid Node or Plug" % toMObjectName(nodeOrPlug)
    upstream = kwargs.get('upstream', False)
    breadth = kwargs.get('breadth', False)
    plug = kwargs.get('plug', False)
    prune = kwargs.get('prune', False)
    if args : 
        typeFilter = MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a node or a plug
        if startPlug is not None :
            typeFilter.setObjectType ( MIteratorType.kMPlugObject )
        else :
            typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if upstream :
        direction = MItDependencyGraph.kUpstream
    else :
        direction = MItDependencyGraph.kDownstream
    if breadth :
        traversal = MItDependencyGraph.kBreadthFirst 
    else :
        traversal =  MItDependencyGraph.kDepthFirst
    if plug :
        level = MItDependencyGraph.kPlugLevel
    else :
        level = MItDependencyGraph.kNodeLevel
    iterObj = MItDependencyGraph ( startObj, startPlug, typeFilter, direction, traversal, level )
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
    # startObj = MObject()
    # startPath = MDagPath()
    startObj = startPath = None  
    if isValidMDagPath (root) :
        startPath = root
    elif isValidMDagNode (root) :
        startObj = root
    else :
        raise ValueError, "'%s' is not a valid Dag Node" % toMObjectName(root)
    breadth = kwargs.get('breadth', False)
    underworld = kwargs.get('underworld', False)
    prune = kwargs.get('prune', False)
    path = kwargs.get('path', False)
    allPaths = kwargs.get('allPaths', False)
    if args : 
        typeFilter = MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a MDagPath or a Mobject
        if startPath is not None :
            typeFilter.setObjectType ( MIteratorType.kMDagPathObject )
        else :
            typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if breadth :
        traversal = MItDag.kBreadthFirst 
    else :
        traversal =  MItDag.kDepthFirst
    iterObj = MItDag ( typeFilter, traversal )
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
        dPathArray = MDagPathArray()
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    iterObj.getAllPaths(dPathArray)
                    nbDagPath = dPathArray.length()
                    for i in range(nbDagPath) :
                        dPath = MDagPath(dPathArray[i])
                        yield dPath
                    instance.append(obj)
            else :
                iterObj.getAllPaths(dPathArray)
                nbDagPath = dPathArray.length()
                for i in range(nbDagPath) :
                    dPath = MDagPath(dPathArray[i])
                    yield dPath
            iterObj.next()
    elif path :
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    dPath = MDagPath()
                    iterObj.getPath(dPath)
                    yield dPath
                    instance.append(obj)
            else :
                dPath = MDagPath()
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
    
    

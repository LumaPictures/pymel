""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

from maya.cmds import about
from maya.OpenMaya import *
from maya.OpenMayaAnim import *
try: from maya.OpenMayaCloth import *
except: pass
try : from maya.OpenMayaFX import *
except: pass
try : from maya.OpenMayaMPx import *
except: pass
if not about(batch=True) :
    try : from maya.OpenMayaUI import *
    except: pass
try : from maya.OpenMayaRender import *
except: pass


# Maya static info :
# Initializes various static look-ups to speed up Maya types conversions


class MayaAPITypesInt(dict) :
    __metaclass__ =  metaStatic

# Dictionnary of Maya API types to their MFn::Types enum,
MayaAPITypesInt(dict(inspect.getmembers(api.MFn, lambda x:type(x) is int)))

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
        obj = api.MObject() 
        dagMod = api.MDagModifier()
        dgMod = api.MDGModifier()          
        try :
            parent = dagMod.createNode ( 'transform', api.MObject())
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
    
    if type(dagMod) is not api.MDagModifier or type(dgMod) is not api.MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"
    # cant create these nodes, some would crahs MAya also
    if ReservedAPITypes().has_key(nodeType) or ReservedMayaTypes().has_key(nodeType) :
        return None   
    obj = api.MObject()
    if MayaAPIToTypes().has_key(nodeType) :
        mayaType = MayaAPIToTypes()[nodeType].keys()[0]
        apiType = nodeType
    elif MayaTypesToAPI().has_key(nodeType) :
        mayaType = nodeType
        apiType = MayaTypesToAPI()[nodeType]
    else :
        return None    
      
    try :
        parent = dagMod.createNode ( 'transform', api.MObject())
        obj = dagMod.createNode ( mayaType, parent )
    except :
        try :
            obj = dgMod.createNode ( mayaType )
        except :
            pass
    if api.isValidMObject(obj) :
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
    if api.isValidMObject(obj) :
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
    if not api.isValidMObject(obj) :
        # print "need creation for %s" % apiType
        obj = _getMObject(apiType, dagMod, dgMod)
    if api.isValidMObject(obj) :
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
            obj = api.MObject()          
            try :
                parent = dagMod.createNode ( 'transform', api.MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
            if api.isValidMObject(obj) :
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
        if x == api.MFnBase :
            return 1
        else :
            try :
                return x().type()
            except :
                return 0
    MFn = inspect.getmembers(OpenMaya, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
    try : MFn += inspect.getmembers(OpenMayaAnim, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaCloth, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaFX, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
    except : pass
    try : MFn += inspect.getmembers(OpenMayaMPx, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
    except : pass
    if not cmds.about(batch=True) :
        try : MFn += inspect.getmembers(OpenMayaUI, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
        except : pass
    try : MFn += inspect.getmembers(OpenMayaRender, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
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
    dagMod = api.MDagModifier()
    dgMod = api.MDGModifier()      
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
            return issubclass(x, _BaseObj)
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
    PyNodeDict[_BaseObj] = 'kBase'
    PyNodeInverseDict['kBase'] = _BaseObj
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
            if issubclass(ct, _BaseObj) and issubclass(pt, _BaseObj) :
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

# get the API type enum (The api.MFn.Types int, ie api.MFn.kDagNode) from a maya type,
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

# Converting API MObjects and more

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

def toMDagPath (nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """ 
    obj = toMObject (nodeName)
    if isValidMDagNode (obj):
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
    if isValidMObject(obj) :
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

# Selection list to PyNodes
def MSelectionPyNode ( sel ):
    length = sel.length()
    dag = MDagPath()
    comp = MObject()
    obj = MObject()
    result = []
    for i in xrange(length) :
        selStrs = []
        sel.getSelectionStrings ( i, selStrs )    
        print "Working on selection %i:'%s'" % (i, ', '.join(selStrs))
        try :
            sel.getDagPath(i, dag, comp)
            pynode = PyNode( dag, comp )
            result.append(pynode)
        except :
            try :
                sel.getDependNode(i, obj)
                pynode = PyNode( obj )
                result.append(pynode)                
            except :
                warnings.warn("Unable to recover selection %i:'%s'" % (i, ', '.join(selStrs)) )             
    return result      
        
        
def activeSelectionPyNode () :
    sel = MSelectionList()
    MGlobal.getActiveSelectionList ( sel )   
    return _MSelectionPyNode ( sel )

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

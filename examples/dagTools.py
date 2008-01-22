import sys, inspect, warnings, timeit, time
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
    try :
        import maya.OpenMayaUI as OpenMayaUI
    except:
        pass
try : import maya.OpenMayaRender as OpenMayaRender
except: pass


# Static singleton dictionnary metaclass to quickly build classes
# holding predefined immutable dicts
class metaStatic(type) :
    def __new__(mcl, classname, bases, classdict):
        # Class is a Singleton and some base class (dict or list for instance), Singleton must come first so that it's __new__
        # method takes precedence
        base = bases[0]
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
        # Note: could have defned the __new__ method like it is done in Singleton but it's as eas to derive from it
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

# some handy aliases / shortcuts easier to remember and use thatn actual Maya type name
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

# get a single MObject from a single node name
def _getMObject( name ): 
    """ Get an API MObject from the name of an existing node """
    sel = OpenMaya.MSelectionList() 
    sel.add( name )         
    node = OpenMaya.MObject()            
    try :
        sel.getDependNode( 0, node )
        if not node.isNull() :
            return node 
    except :
        pass

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
        node = OpenMaya.MObject() 
        dagMod = OpenMaya.MDagModifier()
        dgMod = OpenMaya.MDGModifier()          
        try :
            parent = dagMod.createNode ( 'transform', OpenMaya.MObject())
            node = dagMod.createNode ( mayaType, parent )
        except :
            try :
                node = dgMod.createNode ( mayaType )
            except :
                pass
        finally :
            apiType = node.apiTypeStr()
                          
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
    node = OpenMaya.MObject()
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
        node = dagMod.createNode ( mayaType, parent )
    except :
        try :
            node = dgMod.createNode ( mayaType )
        except :
            pass
    if not node.isNull() :
        return node
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
    node = _getMObject(apiType, dagMod, dgMod, parentType) 
    if node :
        return node.hasFn(typeInt)
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
    node = kwargs.get(apiType, None)        
    if not node or node.isNull() :
        # print "need creation for %s" % apiType
        node= _getMObject(apiType, dagMod, dgMod)

    if node :
        if not kwargs.get(apiType, None) :
            kwargs[apiType] = node          # update it if we had to create
        parents = []
        for t in kwargs.keys() :
            # Need the MFn::Types enum for the parentType
            if t != apiType :
                if MayaAPITypesInt().has_key(t) :
                    ti = MayaAPITypesInt()[t]
                    if node.hasFn(ti) :
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
            node = OpenMaya.MObject()          
            try :
                parent = dagMod.createNode ( 'transform', OpenMaya.MObject())
                node = dagMod.createNode ( mayaType, parent )
            except :
                try :
                    node = dgMod.createNode ( mayaType )
                except :
                    pass
            if not node.isNull() :
                result[apiType] = node
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
    # Fix? some MFn results are not coherent with the hierarchy presented int he docs :
    MFnDict.pop('kWire')
    MFnDict.pop('kBlendShape')
    MFnDict.pop('kFFD')
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
            return issubclass(x, pymel.core._BaseObj)
        except :
            return False    
    listPyNodes = dict(inspect.getmembers(pymel, _PyNodeClass))
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
    PyNodeDict[pymel.node._BaseObj] = 'kBase'
    PyNodeInverseDict['kBase'] = pymel.node._BaseObj
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
            if issubclass(ct, pymel.core._BaseObj) and issubclass(pt, pymel.core._BaseObj) :
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
        
# names to MObjects function
def nameToMObject( *args ):
    """ Get the API MObjects given names of existing nodes """ 
    sel = OpenMaya.MSelectionList() 
    for name in args :
        sel.add( name )
    result = []            
    node = OpenMaya.MObject()            
    for i in range(sel.length()) :
        try :
            sel.getDependNode( i, node )
        except :
            result.append(None)
        if not node.isNull() :
            result.append(node)
        else :
            result.append(None)
    if len(result) == 1:
        return result[0]
    else :
        return tuple(result)

#  MObjects to names
def MObjectToName( *args ):
    """ Get the names of existing nodes given their API MObject""" 
    depNodeFn = OpenMaya.MFnDependencyNode()
    result = []
    for a in args :
        depNodeFn.setObject(a)
        result.append(depNodeFn.name())
    if len(result) == 1:
        return result[0]
    else :
        return tuple(result)
  
# An iterator on maya nodes using the API MItDependencyNodes (ie ls command)

def MItNodes( *args ):
    """ Iterator on nodes of the specified types in the Maya scene,
        type is list, then all nodes of a type included in the list will be iterator on,
        if type is None, all nodes will be iterated on
        the types can be specified either as Maya types or API types """
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
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.objFilterType = OpenMaya.MIteratorType.kMObject
        iterObj = OpenMaya.MItDependencyNodes ( typeFilter )
    else :     
        iterObj = OpenMaya.MItDependencyNodes ( )     
    depNodeFn = OpenMaya.MFnDependencyNode()
    while not iterObj.isDone() :
        obj = iterObj.thisNode()
        depNodeFn.setObject(obj)
        yield (depNodeFn.name(), obj.apiType())
        iterObj.next()

        
        
#for a in MItNodes([]) :
#    print a     


# Iterators on nodes connections using MItDependencyNodes (ie listConnections/ listHistory)



# Iterators on dag nodes hierarchies using MItDag (ie listRelatives)


# conversion fonctions
# conversion maya type -> api type
# get the API type from a maya type
def mayaTypeToApiType (*args, **kwargs) :
    """ Given a list of maya types, return the equivalent API type or API type int """
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

# calling the above iterators in iterators replicating the functionalities of the builtin Maya ls/listHistory/listRelatives
# TODO : pass the Pymel "Scene" object instead to list nodes of the Maya scene (instead of an empty arg list as for Maya's ls)
# TODO : if a Tree or Dag of PyNodes is passed instead, make it work on it as wel
def iterNodes ( *args, **kwargs ):
    """ Iterator on nodes of the specified types in the Maya scene,
        type is list, then all nodes of a type included in the list will be iterator on,
        if type is None, all nodes will be iterated on
        the types can be specified either as Maya types or API types """           
    types = kwargs.get('type', None)
    if types :
#        kwords = {'apiEnum':True}
#        intTypes = typeToAPI(*types, **kwords)
        it_args = mayaTypeToApiType(*types, **{'apiEnum':True})
        if not util.isIterable(it_args) :
            it_args = [it_args]        
    else :
        it_args = [0]                # default : filter on kInvalid = return all nodes
    for tup in MItNodes( *it_args ) :
        # yield (tup[0], tup[1])
        yield (tup[0], MayaIntAPITypes()[tup[1]])
        

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
        >>> [<class 'pymel.Vortex'>, <class 'pymel.core.DagNode'>, <class 'pymel.core.DependNode'>, <class 'pymel.core._BaseObj'>]        
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
                if issubclass(pyAttr, pymel.core._BaseObj) :
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
            while k is not 'pymel.core._BaseObj' and PyNodeTypesHierarchy().has_key(k) :
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
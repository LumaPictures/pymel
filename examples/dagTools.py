import sys, inspect, warnings
# based on pymel
from pymel import *
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
                    base.update(self, value)
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

# Dictionnary of Maya API types to their MFn::Types enum
MayaAPITypesInt(dict(inspect.getmembers(OpenMaya.MFn, lambda x:type(x) is int)))

class MayaIntAPITypes(dict) :
    __metaclass__ =  metaStatic

# Inverse lookup of MFn::Types enum to Maya API types
MayaIntAPITypes(dict((MayaAPITypesInt()[k], k) for k in MayaAPITypesInt().keys()))

# Reserved Maya types and API types that need a special treatment (abstract types)
class ReservedMayaTypes(dict) :
    __metaclass__ =  metaStatic
    
ReservedMayaTypes({ 'base':'kBase', 'object':'kNamedObject', 'node':'kDependencyNode', 'dag':'kDagNode', 'deformer':'kGeometryFilt', \
                 'weightedDeformer':'kWeightGeometryFilt', 'constraint':'kConstraint', 'field':'kField', 'geometry':'kGeometric', 'shape':'kShape', \
                 'surface': 'kSurface', 'revolvedPrimitive':'kRevolvedPrimitive', 'curve':'kCurve', 'animCurve': 'kAnimCurve', 'resultCurve':'kResultCurve', \
                 'pluginNode':'kPluginDependNode', 'pluginDeformer':'kPluginDeformerNode', 'unknown':'kUnknown', 'unknownDag':'kUnknownDag', \
                 'unknownTransform':'kUnknownTransform', 'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip' })

# child:parent lookup of the Maya API classes hierarchy (based on the existing MFn classe hierarchy)
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
    # Fixes
    # types derived of kConstraint are not correctly addedas there is no MFn function on them
    for k in MayaAPITypesInt().keys() :
        if ('Constraint' in k and k is not 'kConstraint') or (k == 'kLookAt') :
            MFnDict[k] = 'kConstraint'
    return MFnDict 

# Initialize the API tree
MayaAPITypesHierarchy(buildAPITypesHierarchy())

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
            if not MayaAPIToTypes().has_key(api) :
                MayaAPIToTypes()[api] = dict( ((k, None),) )
            else :
                MayaAPIToTypes()[api][k] = None   

            
# initial update  
updateMayaTypesList()

# Need to build a similar dict of Pymel types to their corresponding API types
class PyNodeToMayaAPITypes(dict) :
    __metaclass__ =  metaStatic

# inverse lookup, some Maya API types won't have a PyNode equivalent
class MayaAPITypesToPyNode(dict) :
    __metaclass__ =  metaStatic

# build a PyNode to API type relation or PyNode to Maya node types relation ?
def buildPyNodeToAPI () :
    # Check if a pymel class is Node or a subclass of Node
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
    # Initialize the static classes to hold these
    PyNodeToMayaAPITypes (PyNodeDict)
    MayaAPITypesToPyNode (PyNodeInverseDict)

buildPyNodeToAPI()

# child:parent lookup of the pymel classes that derive from Node
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

# Initialize the API tree
PyNodeTypesHierarchy(buildPyNodeTypesHierarchy())
        
# Public names to MObjects function
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
        >>> mayaType ('kField')
        >>> 'field'
        >>> mayaType ('kConstraint', pymel=True)
        >>> mayaType ('kConstraint')
        >>> 'constraint'
        >>> mayaType ('kVortex', pymel=True)
        >>> <class 'pymel.Vortex'>
        >>> mayaType ('Vortex', inheritedPymel=True)
        >>> [<class 'pymel.Vortex'>, <class 'pymel.core.Dag'>, <class 'pymel.core.Node'>, <class 'pymel.core._BaseObj'>]        
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
#    elif ReservedMayaTypes().has_key(nodeOrType) :
#        # It's an abstract "reserved" type
#        mayaType = nodeOrType        
#        apiTypeStr = ReservedMayaTypes()[nodeOrType]    
    elif type(nodeOrType) == int :
        # MFn.Types enum int
        apiTypeStr = MayaIntAPITypes()[nodeOrType] 
    elif MayaAPITypesInt().has_key(nodeOrType) :
        # API type
        apiTypeStr = nodeOrType
    elif MayaTypesToAPI().has_key(nodeOrType) :
        # Maya type
        mayaType = nodeOrType
    elif PyNodeToMayaAPITypes().has_key(nodeOrType) :
        # PyNode type
        pyNodeType = nodeOrType
        apiTypeStr = PyNodeToMayaAPITypes()[pyNodeType]
    elif isinstance(nodeOrType, Node) :
        # a PyNode object
        pyNodeType = type(nodeOrType)
        apiTypeStr = PyNodeToMayaAPITypes().get(pyNodeType, None)
    elif isinstance(nodeOrType, basestring) : 
        # check if it could be a PyMel type name
        if (hasattr(pymel, nodeOrType)) :
            pyNodeType = getattr (pymel, nodeOrType)
            apiTypeStr = PyNodeToMayaAPITypes().get(pyNodeType, None)
        # check if it could be a not yet cached Maya type
        elif addToMayaTypesList(nodeOrType) :
            mayaType = nodeOrType
            
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
            if do_inherited :
                inherited = [MayaAPIToTypes()[k].keys() for k in apiInherited] 
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
    """checks if given Maya objects or type names, or AMtypes objects or class names are of the given type or derive from it"""
    result = []
    type = kwargs.get('type', None)
    if type is None :
        type = 'kBase'
    else :
        checkType = Node
        if objExists(type) :  # it's a Maya object name @UndefinedVariable
            checkType = nodeType(type) # it's a Maya object name @UndefinedVariable
        else :
            checkType = util.capitalize(type)            # a Maya type name, is it defined ?
    checkType = Dag
    # print args
    if len(args) == 0 :
        args = ls( selection=True)
    for nodeOrType in util.iterateListArgs(*args) :
        # print 'examining: '+nodeOrType
        # if hasattr(nodeOrType,'isDag')
        t = type(nodeOrType)
        if (t== unicode) or (t==str) :                        # it's a Maya object or Type name (string)
            if (objExists(nodeOrType)) :                      # a Maya object name @UndefinedVariable
                result.append(objectType(nodeOrType, isAType=checkType)) # @UndefinedVariable
            else :
                c = util.capitalize(nodeOrType)            # a Maya type name, is it defined ?
                if (hasattr(pymel, c)) :
                    t = getattr (pymel, c)
                    if (type(t)==type) :
                        result.append(issubclass(t,Dag))
                    else :
                        result.append(False)
                else :
                    result.append(False)
        elif t==type :                        # a Python type for a pymel class
            result.append(issubclass(nodeOrType,Dag))
        else :                                # a pymel object
            result.append(isinstance(nodeOrType, Dag)    )

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
    """checks if given Maya objects or type names, or AMtypes objects or class names are DAG objects or DAG sub-types"""
    kwargs = {'type':Dag}
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
        >>> sel=ls(selection=True)
        >>> skel=asHierarchy (sel)
        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
        >>> True """
        
    if len(args) == 0 :
        nargs = ls( selection=True)
    else :
        args = util.expandListArgs (*args)
        nargs = map(PyNode, args)
    # print "Arguments: %s"+str(nargs)
    result = treeFromChildLink (isExactChildFn, *nargs)
    # print "Result: %s"+str(result)
    return result


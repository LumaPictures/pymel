import sys, inspect, warnings, timeit, time
import re
# based on pymel
from pymel import node
from pymel import api





    # mayaType (nodeOrType, **kwargs) :
#    typeInt = []
#    for t in type :
#        typeInt.append(ApiTypesToApiEnums[MayaTypesToAPI[t]])
        
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
        >>> [<class 'pymel.Vortex'>, <class 'pymel.node.DagNode'>, <class 'pymel.node.DependNode'>, <class 'pymel.node._BaseObj'>]        
        >>> mayaType ('aimConstraint', apiType=True, inheritedAPI=True)
        >>> {'inheritedAPI': ['kConstraint'], 'apiType': 'kAimConstraint'}
        >>> mayaType (pymel.Transform)
        >>> u'transform'
        >>> mayaType (pymel.Transform, apiType=True)
        >>> 'kTransform'
        """
    apiTypeInt = None           # api.MFn.kInvalid is 0, api.MFn.kBase is 1
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
        apiTypeStr = ApiEnumsToApiTypes()[nodeOrType] 
    elif ApiTypesToApiEnums().has_key(nodeOrType) :
        # API type
        apiTypeStr = nodeOrType
    elif ShortMayaTypes().has_key(nodeOrType) :
        # shortcut for a maya type
        mayaType = ShortMayaTypes()[nodeOrType]
    elif MayaTypesToAPI().has_key(nodeOrType) :
        # Maya type
        mayaType = nodeOrType
    elif PyNodesToApiTypes().has_key(nodeOrType) :
        # PyNode type
        pyNodeType = nodeOrType
        apiTypeStr = PyNodesToApiTypes()[pyNodeType]
    elif isinstance(nodeOrType, DependNode) :
        # a PyNode object
        pyNodeType = type(nodeOrType)
        apiTypeStr = PyNodesToApiTypes().get(pyNodeType, None)
    elif isinstance(nodeOrType, basestring) : 
        # check if it could be a PyMel type name
        if (hasattr(pymel, nodeOrType)) :
            pyAttr = getattr (pymel, nodeOrType)
            if inspect.isclass(pyAttr) :
                if issubclass(pyAttr, _BaseObj) :
                    pyNodeType = pyAttr
                    apiTypeStr = PyNodesToApiTypes().get(pyNodeType, None)
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
                mayatypes = ApiTypesToMayaTypes()[apiTypeStr].keys()
                if len(mayatypes) == 1 :
                    mayaType = mayatypes[0]
                else :
                    mayaType = tuple(mayatypes)
    # no need to do more if we don't have a valid apiTypeStr               
    if apiTypeStr and apiTypeStr is not 'kInvalid' :                    
        if do_apiInt :
            apiTypeInt = ApiTypesToApiEnums().get(apiTypeStr, None)
        if do_plugin :
            isPluginObject = 'Plugin' in apiTypeStr
        if do_pymel and not pyNodeType :
            pyNodeType = ApiTypesToPyNodes().get(apiTypeStr, None)                
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
                    mTypes = ApiTypesToMayaTypes()[k].keys()
                    defType = None
                    if len(mTypes) > 1 :
                        for t in mTypes :
                            if ApiTypesToMayaTypes()[k][t] :
                                defType = t
                                break
                    if defType is None and mTypes :
                        defType = mTypes[0]
                    inherited.append(defType)       
        if do_pymelInherited :
            k = pyNodeType
            pymelInherited.append(k)      # starting class
            while k is not '_BaseObj' and PyNodeTypesHierarchy().has_key(k) :
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
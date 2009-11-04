# import all available Maya API methods in this module (api)
from maya.OpenMaya import *
from maya.OpenMayaAnim import *
try: from maya.OpenMayaCloth import *
except: pass
try : from maya.OpenMayaFX import *
except: pass
try : from maya.OpenMayaMPx import *
except: pass
if not MGlobal.mayaState() == MGlobal.kBatch:
    try : from maya.OpenMayaUI import *
    except: pass
try : from maya.OpenMayaRender import *
except: pass


# fast convenience tests on API objects
def isValidMObjectHandle(obj):
    if isinstance(obj, MObjectHandle) :
        return obj.isValid() and obj.isAlive()
    else :
        return False

def isValidMObject(obj):
    if isinstance(obj, MObject) :
        return not obj.isNull()
    else :
        return False
    
def isValidMPlug(obj):
    if isinstance(obj, MPlug) :
        return not obj.isNull()
    else :
        return False

def isValidMDagPath(obj):
    if isinstance(obj, MDagPath) : 
        # when the underlying MObject is no longer valid, dag.isValid() will still return true,
        # but obj.fullPathName() will be an empty string
        return obj.isValid() and obj.fullPathName() 
    else :
        return False

def isValidMNode(obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDependencyNode)
    else :
        return False

def isValidMDagNode(obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDagNode)
    else :
        return False
    
def isValidMNodeOrPlug(obj):
    return isValidMPlug(obj) or isValidMNode (obj)
            
# returns a MObject for an existing node
def toMObject(nodeName):
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

def toApiObject(nodeName, dagPlugs=True):
    """ Get the API MPlug, MObject or (MObject, MComponent) tuple given the name of an existing node, attribute, components selection
    
    if dagPlugs is True, plug result will be a tuple of type (MDagPath, MPlug)
    
    """ 
    sel = MSelectionList()
    try:
        sel.add( nodeName )
    except:
        if "." in nodeName :
            # Compound Attributes
            #  sometimes the index might be left off somewhere in a compound attribute 
            # (ex 'Nexus.auxiliary.input' instead of 'Nexus.auxiliary[0].input' )
            #  but we can still get a representative plug. this will return the equivalent of 'Nexus.auxiliary[-1].input'
            try:
                buf = nodeName.split('.')
                obj = toApiObject( buf[0] )
                if isinstance(obj,MDagPath):
                    mfn = MFnDagNode(obj)
                else:
                    mfn = MFnDependencyNode(obj)
                plug = mfn.findPlug( buf[-1], False )
                
                if dagPlugs: # and isValidMDagPath(obj) : 
                    return (obj, plug)
                return plug
            except (RuntimeError,ValueError):
                return
    else:
        if "." in nodeName :
            try:
                # Plugs
                plug = MPlug()
                sel.getPlug( 0, plug )
                if dagPlugs:
                    try:
                        # Plugs with DagPaths
                        sel.add( nodeName.split('.')[0] )
                        dag = MDagPath()
                        sel.getDagPath( 1, dag )
                        #if isValidMDagPath(dag) :
                        return (dag, plug)
                    except RuntimeError: pass
                return plug
            
            except RuntimeError:
                # Components
                dag = MDagPath()
                comp = MObject()
                sel.getDagPath( 0, dag, comp )
                #if not isValidMDagPath(dag) :   return
                return (dag, comp)
        else:
            try:
                # DagPaths
                dag = MDagPath()
                sel.getDagPath( 0, dag )
                #if not isValidMDagPath(dag) : return
                return dag
         
            except RuntimeError:
                # Objects
                obj = MObject()
                sel.getDependNode( 0, obj )          
                #if not isValidMObject(obj) : return     
                return obj
        
#    # TODO : components
#    if "." in nodeName :
#        # build up to the final MPlug
#        nameTokens = nameparse.getBasicPartList( nodeName )
#        if dag.isValid():
#            fn = MFnDagNode(dag)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, MPlug ):
#                        result = result.child( fn.attribute( unicode(token) ) )
#                    else:
#                        try:
#                            result = fn.findPlug( unicode(token) )
#                        except TypeError:
#                            for i in range(fn.childCount()):
#                                try:
#                                    result = MFnDagNode( fn.child(i) ).findPlug( unicode(token) )
#                                except TypeError:
#                                    pass
#                                else:
#                                    break
#                if isinstance( token, nameparse.NameIndex ):
#                    result = result.elementByLogicalIndex( token.value )
#            if dagMatters:
#                result = (dag, result)
#        else:
#            fn = MFnDependencyNode(obj)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, MPlug ):
#                        result = result.child( fn.attribute( unicode(token) ) )
#                    else:
#                        result = fn.findPlug( unicode(token) )
#                            
#                if isinstance( token, nameparse.NameIndex ):
#                    result = result.elementByLogicalIndex( token.value )
#        
#
#    return result

def toMDagPath(nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """ 
    obj = toMObject (nodeName)
    if obj :
        dagFn = MFnDagNode (obj)
        dagPath = MDagPath()
        dagFn.getPath ( dagPath )
        return dagPath

# returns a MPlug for an existing plug
def toMPlug(plugName):
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

def toComponentMObject( dagPath ):
    """
    get an MObject representing all components of the passed dagPath
    
    The component type that will be returned depends on the exact type of
    object passed in - for instance, a poly mesh will return a component
    representing all the kMeshVertComponents.
    
    The exact choice of component type is determined by MItGeometry.
    """
    
    component = MObject()
    sel = MSelectionList()
    mit = MItGeometry( dagPath )
    while not mit.isDone():
        # MItGeometry.component is deprecated
        comp = mit.currentItem()
        # merge is True
        sel.add( dagPath, comp, True )
        mit.next()
    sel.getDagPath( 0, dagPath, component )
    return component
      
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
    
           

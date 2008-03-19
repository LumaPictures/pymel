import sys, inspect, warnings, timeit, time
import re
# based on pymel
from pymel import node
from pymel import api

# need the base class
_BaseObj = node._BaseObj



# Maya scene nodes iterators

# An iterator on maya nodes using the API MItDependencyNodes (ie ls command)

def MItNodes( *args, **kwargs ):
    """ Iterator on MObjects of nodes of the specified types in the Maya scene,
        if a list of tyes is passed as args, then all nodes of a type included in the list will be iterated on,
        if no types are specified, all nodes of the scene will be iterated on
        the types are specified as Maya API types """
    typeFilter = api.MIteratorType()
    if args : 
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = api.MScriptUtil()
            typeIntM = api.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.setObjectType ( api.MIteratorType.kMObject )
    # create iterator with (possibly empty) typeFilter
    iterObj = api.MItDependencyNodes ( typeFilter )     
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
#    startObj = api.MObject() 
#    startPlug = api.MPlug()
    startObj = None
    startPlug = None   
    if api.isValidMPlug(nodeOrPlug):
        startPlug = nodeOrPlug
    elif api.isValidMNode(nodeOrPlug) :
        startObj = nodeOrPlug
    else :
        raise ValueError, "'%s' is not a valid Node or Plug" % api.toMObjectName(nodeOrPlug)
    upstream = kwargs.get('upstream', False)
    breadth = kwargs.get('breadth', False)
    plug = kwargs.get('plug', False)
    prune = kwargs.get('prune', False)
    if args : 
        typeFilter = api.MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = api.MScriptUtil()
            typeIntM = api.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a node or a plug
        if startPlug is not None :
            typeFilter.setObjectType ( api.MIteratorType.kMPlugObject )
        else :
            typeFilter.setObjectType ( api.MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if upstream :
        direction = api.MItDependencyGraph.kUpstream
    else :
        direction = api.MItDependencyGraph.kDownstream
    if breadth :
        traversal = api.MItDependencyGraph.kBreadthFirst 
    else :
        traversal =  api.MItDependencyGraph.kDepthFirst
    if plug :
        level = api.MItDependencyGraph.kPlugLevel
    else :
        level = api.MItDependencyGraph.kNodeLevel
    iterObj = api.MItDependencyGraph ( startObj, startPlug, typeFilter, direction, traversal, level )
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
    # startObj = api.MObject()
    # startPath = api.MDagPath()
    startObj = startPath = None  
    if api.isValidMDagPath (root) :
        startPath = root
    elif api.isValidMDagNode (root) :
        startObj = root
    else :
        raise ValueError, "'%s' is not a valid Dag Node" % api.toMObjectName(root)
    breadth = kwargs.get('breadth', False)
    underworld = kwargs.get('underworld', False)
    prune = kwargs.get('prune', False)
    path = kwargs.get('path', False)
    allPaths = kwargs.get('allPaths', False)
    if args : 
        typeFilter = api.MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = api.MScriptUtil()
            typeIntM = api.MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a MDagPath or a Mobject
        if startPath is not None :
            typeFilter.setObjectType ( api.MIteratorType.kMDagPathObject )
        else :
            typeFilter.setObjectType ( api.MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if breadth :
        traversal = api.MItDag.kBreadthFirst 
    else :
        traversal =  api.MItDag.kDepthFirst
    iterObj = api.MItDag ( typeFilter, traversal )
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
        dPathArray = api.MDagPathArray()
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    iterObj.getAllPaths(dPathArray)
                    nbDagPath = dPathArray.length()
                    for i in range(nbDagPath) :
                        dPath = api.MDagPath(dPathArray[i])
                        yield dPath
                    instance.append(obj)
            else :
                iterObj.getAllPaths(dPathArray)
                nbDagPath = dPathArray.length()
                for i in range(nbDagPath) :
                    dPath = api.MDagPath(dPathArray[i])
                    yield dPath
            iterObj.next()
    elif path :
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    dPath = api.MDagPath()
                    iterObj.getPath(dPath)
                    yield dPath
                    instance.append(obj)
            else :
                dPath = api.MDagPath()
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
    if not basestring in types :
        types.append(basestring)
    for n in args :
        key = val = None
        if isinstance (n, basestring) :            
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
# TODO : special return options: below, above, childs, parents, asList, breadth, asTree, underworld, allPaths and prune
# TODO : component support
def iterNodes ( *args, **kwargs ):
    """ Iterates on nodes of the argument list, or when args is empty on nodes of the Maya scene,
        that meet the given conditions.
        The following keywords change the way the iteration is done :
            selection = False : will use current selection if no nodes are passed in the arguments list,
                or will filter argument list to keep only selected nodes
            above = 0 : for each returned dag node will also iterate on its n first ancestors
            below = 0 : for each returned dag node will also iterate on levels of its descendents
            parents = False : if True is equivalent to above = 1
            childs = False : if True is equivalent to below = 1       
            asList = False : 
            asTree = False :
            breadth = False :
            underworld = False :
            allPaths = False :
            prune = False :
        The following keywords specify conditions the iterated nodes are filtered against, conditions can be passed either as a
        list of conditions, format depending on condition type, or a dictionnary of {condition:result} with result True or False
            name = None: will filter nodes that match these names. Names can be actual node names, use wildcards * and ?, or regular expression syntax
            position = None: will filter dag nodes that have a specific position in their hierarchy :
                'root' for root nodes
                'leaf' for leaves
                'level=<int>' or 'level=[<int>:<int>]' for a specific distance from their root
            type = None: will filter nodes that are of the specified type, or a derived type.
                The types can be specified as Pymel Node types (DependNode and derived) or Maya types names
            property = None: check for specific preset properties, for compatibility with the 'ls' command :
                'visible' : object is visible (it's visibility is True and none of it's ancestor has visibility to False)
                'ghost': ghosting is on for that object 
                'templated': object is templated or one of its ancestors is
                'intermediate' : object is marked as "intermediate object"
            attribute = None: each condition is a string made of at least an attribute name and possibly a comparison operator an a value
                checks a specific attribute of the node for existence: '.visibility',
                or against a value: 'translateX >= 2.0'
            user = None: each condition must be a previously defined function taking the iterated object as argument and returning True or False
        expression = None: allows to pass the string of a Python expression that will be evaluated on each iterated node,
            and will limit the result to nodes for which the expression evaluates to 'True'. Use the variable 'node' in the
            expression to represent the currently evaluated node

        Conditions of the same type (same keyword) are combined as with a logical 'or' for positive conditions :
        iterNodes(type = ['skinCluster', 'blendShape']) will iter on all nodes of type skinCluster OR blendShape
        Conditions of the type (same keyword) are combined as with a logical 'and' for negative conditions :
        iterNodes(type = ['!transform', '!blendShape']) will iter on all nodes of type not transform AND not blendShape
        Different conditions types (different keyword) are combined as with a logical 'and' :
        iterNodes(type = 'skinCluster', name = 'bodySkin*') will iter on all nodes that have type skinCluster AND whose name
        starts with 'bodySkin'. 
        
        Examples : (TODO)
        """

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
                raise ValueError, "'%r' does not exist" % a
        else :
            raise TypeError, "'%r' is not  valid PyNode (DependNode)" % a
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
    print "name args", nameArgs   
    if nameArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(nameArgs):
            if not util.isSequence(nameArgs) :
                nameArgs = [nameArgs]    
            nameArgs = _optToDict(*nameArgs)
        # check
        print nameArgs
        # for names parsing, see class definition in nodes
        curNameSpace = namespaceInfo( currentNamespace=True )    
        for i in nameArgs.items() :
            key = i[0]
            val = i[1]
            if key.startswith('(') and key.endswith(')') :
                # take it as a regular expression directly
                pass
            elif MayaName.invalid.findall(key) :
                # try it as a regular expression in case (is it a good idea)
                pass
            else :
                # either a valid node name or a glob pattern
                nameMatch = FullObjectName.valid.match(key)
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
                        raise ValueError, "'%s' uses inexistent nameSpace '%s'" % (key, nameSpace)
                elif '*' in key or '?' in key :
                    # it's a glob pattern, try build a re out of it and add it to names conditions
                    key = key.replace("*", r"("+MayaName.validCharPattern+r"*)")
                    key = key.replace("?", r"("+MayaName.validCharPattern+r")")
                else : 
                    #is not anything we recognize
                    raise ValueError, "'%s' is not a valid node name or glob/regular expression" % a
            try :
                r = re.compile(key)
            except :
                raise ValueError, "'%s' is not a valid regular expression" % key
            # check for duplicates re and add
            _addCondition(cNames, r, val)
        # check
        print "Name keys:"
        for r in cNames.keys() :
            print "%s:%r" % (r.pattern, cNames[r])     
      
    # conditions on position in hierarchy (only apply to dag nodes)
    # can be passed as a dict of conditions and values
    # condition:value (True or False) or a sequence of conditions, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # valid flags are 'root', 'leaf', or 'level=x' for a relative depth to start node 
    posArgs = kwargs.get('position', None)
    # check
    print "position args", posArgs    
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
                            level = IRange(lstart, lend)
                    else :
                        # it's a single value
                        if levelMatch.groups[1] :
                            level = None
                        elif levelMatch.groups[0] :
                            level = IRange(levelMatch.groups[0], levelMatch.groups[0]+1)
                        else :
                            level = None               
                if level is None :
                    raise ValueError, "Invalid level condition %s" % key
                    key = None
                else :
                    key = level     
            else :
                raise ValueError, "Unknown position condition %s" % key
            # check for duplicates and add
            _addCondition(cPos, key, val)            
            # TODO : check for intersection with included levels
        # check
        print "Pos keys:"
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
    print "type args", typeArgs
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
                raise ValueError, "Invalid/unknown type condition '%s'" % key 
        # check
        print " API type keys: "
        for r in cAPITypes.keys() :
            print "%s:%r" % (r, cAPITypes[r])
        print " Ext type keys: "   
        for r in cExtTypes.keys() :
            print "%s:%r" % (r, cExtTypes[r])
        # if we check for the presence (positive condition) of API types and API types only we can 
        # use the API MIteratorType for faster filtering, it's not applicable if we need to prune
        # iteration for unsatisfied conditions
        if apiFilter and not extendedFilter and not prune :
            for item in cAPITypes.items() :
                if item[1] and MayaAPITypesInt().has_key(item[0]) :
                     cAPIFilter.append(MayaAPITypesInt()[item[0]])
        # check
        print " API filter: "
        print cAPIFilter  
                          
    # conditions on pre-defined properties (visible, ghost, etc) for compatibility with ls
    validProperties = {'visible':1, 'ghost':2, 'templated':3, 'intermediate':4}    
    propArgs = kwargs.get('properties', None)
    # check
    print "Property args", propArgs    
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
                raise ValueError, "Unknown property condition '%s'" % key
        # check
        print "Properties keys:"
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
    print "Attr args", attrArgs    
    cAttr = {}    
    if attrArgs is not None :
        # convert list to dict if necessary
        if not util.isMapping(attrArgs):
            if not util.isSequence(attrArgs) :
                attrArgs = [attrArgs]    
            attrArgs = _optToDict(*attrArgs)    
        # check
        print attrArgs
        # for valid attribute name patterns check node.Attribute  
        # valid form for conditions
        attrValuePattern = r".+"
        attrCondPattern = r"(?P<attr>"+PlugName.pattern+r")[ \t]*(?P<oper>==|!=|>|<|>=|<=)?[ \t]*(?P<value>"+attrValuePattern+r")?"
        validAttrCond = re.compile(attrCondPattern)        
        for i in attrArgs.items() :
            key = i[0]
            val = i[1]
            attCondMatch = validAttrCond.match(key.strip())
            if attCondMatch is not None :
                # eval value here or wait resolution ?
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
                    if attCond[1] is None :
                        val = True
                    elif attCond[1] is '==' :
                        attCond[1] = None
                        val = False  
                    elif attCond[1] is '!=' :
                        attCond[1] = None
                        val = True
                    else :
                        raise ValueError, "Value 'None' means testing for attribute existence and is only valid for operator '!=' or '==', '%s' invalid" % key
                        attCond = None
                # check for duplicates and add
                _addCondition(cAttr, attCond, val)                                               
            else :
                raise ValueError, "Unknown attribute condition '%s', must be in the form attr <op> value with <op> : !=, ==, >=, >, <= or <" % key          
        # check
        print "Attr Keys:"
        for r in cAttr.keys() :
            print "%s:%r" % (r, cAttr[r])        
    # conditions on user defined boolean functions
    userArgs = kwargs.get('user', None)
    # check
    print "userArgs", userArgs    
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
            if isinstance(key, basestring) :
                key = globals().get(key,None)
            if key is not None :
                if inspect.isfunction(key) and len(inspect.getargspec(key)[0]) is 1 :
                    _addCondition(cUser, key, val)
                else :
                    raise ValueError, "user condition must be a function taking one argument (the node) that will be tested against True or False, %r invalid" % key
            else :
                raise ValueError, "name '%s' is not defined" % key        
        # check
        print "User Keys:"
        for r in cUser.keys() :
            print "%r:%r" % (r, cUser[r])
    # condition on a user defined expression that will be evaluated on each returned PyNode,
    # that must be represented by the variable 'node' in the expression    
    userExpr = kwargs.get('exp', None)
    if userExpr is not None and not isinstance(userExpr, basestring) :
        raise ValueError, "iterNodes expression keyword takes an evaluable string Python expression"

    # post filtering function
    def _filter( pyobj, apiTypes={}, extTypes={}, names={}, pos={}, prop={}, attr={}, user={}, expr=None  ):
        result = True
        # check on types conditions
        if result and (len(apiTypes)!=0 or len(extTypes)!=0) :
            result = False
            for cond in apiTypes.items() :
                ctyp = cond[0]
                cval = cond[1]
                if _nodeTypeToApiType(pyobj.type()) == ctyp :
                    result = cval
                    break
                elif not cval :
                    result = True                                      
            for cond in extTypes.items() :  
                ctyp = cond[0]
                cval = cond[1]                                    
                if isinstance(pyobj, ctyp) :
                    result = cval
                    break
                elif not cval :
                    result = True                   
        # check on names conditions
        if result and len(names)!=0 :
            result = False
            for cond in names.items() :
                creg = cond[0]
                cval = cond[1]
                if creg.match(pyobj) is not None :
                    result = cval
                    break
                elif not cval :
                    result = True                                             
        # check on position (for dags) conditions
        if result and len(pos)!=0 and isinstance(pyobj, DagNode) :
            result = False
            for cond in pos.items() :
                cpos = cond[0]
                cval = cond[1]                
                if cpos == 'root' :
                    if pyobj.isRoot() :
                        result = cval
                        break
                    elif not cval :
                        result = True
                elif cpos == 'leaf' :
                    if pyobj.isLeaf() :
                        result = cval
                        break
                    elif not cval :
                        result = True                    
                elif isinstance(cpos, IRange) :
                    if pyobj.depth() in cpos :
                        result = cval
                        break       
                    elif not cval :
                        result = True                                                                
        # TODO : 'level' condition, would be faster to get the depth from the API iterator
        # check some pre-defined properties, so far existing properties all concern dag nodes
        if result and len(prop)!=0 and isinstance(pyobj, DagNode) :
            result = False
            for cond in prop.items() :
                cprop = cond[0]
                cval = cond[1]                     
                if cprop == 'visible' :
                    if pyobj.isVisible() :
                        result = cval
                        break 
                    elif not cval :
                        result = True                                  
                elif cprop == 'ghost' :
                    if pyobj.hasAttr('ghosting') and pyobj.getAttr('ghosting') :
                        result = cval
                        break 
                    elif not cval :
                        result = True                                   
                elif cprop == 'templated' :
                    if pyobj.isTemplated() :
                        result = cval
                        break 
                    elif not cval :
                        result = True      
                elif cprop == 'intermediate' :
                    if pyobj.isIntermediate() :
                        result = cval
                        break 
                    elif not cval :
                        result = True                        
        # check for attribute existence and value
        if result and len(attr)!=0 :
            result = False
            for cond in attr.items() :
                cattr = cond[0] # a tuple of (attribute, operator, value)
                cval = cond[1]                  
                if cattr[1] is None :
                    if pyobj.hasAttr(cattr[0]) :
                        result = cval
                        break
                    elif not cval :
                        result = True                      
                else :
                    if eval(str(pyobj.getAttr(cattr[0]))+cattr[1]+cattr[2]) :
                        result = cval
                        break  
                    elif not cval :
                        result = True                                                                   
        # check for used condition functions
        if result and len(user)!=0 :
            result = False
            for cond in user.items() :
                cuser = cond[0]
                cval = cond[1]                    
                if cuser(pyobj) :
                    result = cval
                    break  
                elif not cval :
                    result = True  
        # check for a user eval expression
        if result and expr is not None :
            result = eval(expr, globals(), {'node':pyobj})     
                     
        return result
            
    # Iteration :
    needLevelInfo = False
    
    # TODO : special return options
    # below, above, childs, parents, asList, breadth, asTree, underworld, allPaths and prune
    if nodes :
        # if a list of existing nodes is provided we iterate on the ones that both exist and match the used flags        
        for pyobj in nodes :
            if _filter (pyobj, cAPITypes, cExtTypes, cNames, cPos, cProp, cAttr, cUser, userExpr ) :
                yield pyobj
    else :
        # else we iterate on all scene nodes that satisfy the specified flags, 
        for obj in MItNodes( *cAPIFilter ) :
            pyobj = api.MObjectPyNode( obj )
            if pyobj.exists() and _filter (pyobj, cAPITypes, cExtTypes, cNames, cPos, cProp, cAttr, cUser, userExpr ) :
                yield pyobj
        

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
                if issubclass(pyAttr, _BaseObj) :
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
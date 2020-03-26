from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import next
from builtins import range
from builtins import object
import weakref

import pymel.util as util

# import all available Maya API methods in this module (api)
from maya.OpenMaya import *
from maya.OpenMayaAnim import *
try:
    from maya.OpenMayaCloth import *
except:
    pass
try:
    from maya.OpenMayaFX import *
except:
    pass
try:
    from maya.OpenMayaMPx import *
except:
    pass
if not MGlobal.mayaState() == MGlobal.kBatch:
    try:
        from maya.OpenMayaUI import *
    except:
        pass
try:
    from maya.OpenMayaRender import *
except:
    pass

# So, it seems that MScriptUtil().as*Ptr has a serious
# problem... basically, it looks like the returned
# ptrs don't have a reference to the MScriptUtil()
# that provides the actual storage for them -
# thus, it's possible for the MScriptUtil to get
# garbage collected, but still have the pointer
# to it in use - so it points to garbage (and
# generally causes a crash).
# To get around this, we create a wrapper for
# ptrs which also contains a reference to the
# MScriptUtil which contains the storage. Pass
# it around in place of the pointer - then, when
# the 'actual' pointer is needed (ie, immediately
# before feeding it into an api function), 'call'
# the SafeApiValue/Ptr object to return the 'true'
# pointer.
# Also, even SafeApiPtr is not completely safe -
# for instance, you cannot create 'throwaway' instances,
# like:
#   theApiFunc(SafeApiPtr('double')())
# ...as there is a chance that the MScriptUtil will be
# garbage collected before the api function tries to
# write into it's pointer...

# Note - I would have liked to have implemented this
# by simply attaching the MScriptUtil to the ptr -
# but you can't add attributes to the pointer object.
# My next idea was to use weakrefs to create a dictionary
# which maps ptrs to MScriptUtils - and clean it
# periodically as the ptrs are garbage collected. Alas,
# the pointer objects are also not compatible with
# weakref.  So, we have to use a 'non-transparent' wrapper...
# ie, we have to 'call' the object before feeding to
# the api function...


class SafeApiPtr(object):

    """
    A wrapper for api pointers which also contains a reference
    to the MScriptUtil which contains the storage. This helps
    ensure that the 'storage' for the pointer doesn't get
    wiped out before the pointer does. Pass the SafeApiPtr
    around in place of the 'true' pointer - then, when
    the 'true' pointer is needed (ie, immediately
    before feeding it into an api function), 'call'
    the SafeApiPtr object to return the 'true'
    pointer.

    Examples
    --------
    >>> from pymel.api.allapi import *
    >>> sel = MSelectionList()
    >>> sel.add('perspShape')
    >>> dag = MDagPath()
    >>> sel.getDagPath(0, dag)
    >>> cam = MFnCamera(dag)

    >>> aperMin = SafeApiPtr('double')
    >>> aperMax = SafeApiPtr('double')
    >>> cam.getFilmApertureLimits(aperMin(), aperMax())
    >>> print('%.5f, %.5f' % (aperMin.get(), aperMax.get()))
    0.01378, 20.28991
    """

    def __init__(self, valueType, scriptUtil=None, size=1, asTypeNPtr=False):
        # type: (str, MScriptUtil, int, bool) -> None
        """
        Parameters
        ----------
        valueType : str
            The name of the maya pointer type you would like
            returned - ie, 'int', 'short', 'float'.
        scriptUtil : `MScriptUtil`
            If you wish to use an existing MScriptUtil as
            the 'storage' for the value returned, specify it
            here - otherwise, a new MScriptUtil object is
            created.
        size : `int`
            If we want a pointer to an array, size indicates
            the number of items the array holds.  If we are
            creating an MScriptUtil, it will be initialized
            to hold this many items - if we are fed an
            MScriptUtil, then it is your responsibility to
            make sure it can hold the necessary number of items,
            or else maya will crash!
        asTypeNPtr : `bool`
            If we want a call to this SafeApiPtr to return a pointer
            for an argument such as:
               int2 &myArg;
            then we need to set asTypeNPtr to True:
               SafeApiPtr('int', size=2, asTypeNPtr=True)
            Otherwise, it is assumed that calling the object returns array
            ptrs:
               int myArg[2];
        """
        if not scriptUtil:
            self.scriptUtil = MScriptUtil()
            if size < 1:
                raise ValueError('size must be >= 1')
            else:
                # Value stored here doesn't matter - just make sure
                # it's large enough!
                self.scriptUtil.createFromList([0.0] * size, size)
        else:
            self.scriptUtil = scriptUtil
        self.size = size
        capValue = util.capitalize(valueType)
        self._normPtr = getattr(self.scriptUtil, 'as' + capValue + 'Ptr')()
        # Unforunately, arguments such as:
        #    float2 &foo;
        # need to be handled differently - calling it, we need
        # to return asFloat2Ptr()... but when indexing, use the same old
        # asFloatPtr() result to feed into getFloatArrayValue.
        # Also, note that asFloatPtr() must be called BEFORE asFloat2Ptr() -
        # if it is called after, the float2 ptr seems to get reset!
        self._sizedIndexGetter = None
        self._sizedIndexSetter = None
        if asTypeNPtr:
            self._nPtr = getattr(self.scriptUtil, 'as' + capValue +
                                 str(size) + 'Ptr')()
            self._ptr = self._nPtr
            self._sizedIndexGetter = getattr(
                MScriptUtil, 'get' + capValue + str(size) + 'ArrayItem', None)
            self._sizedIndexSetter = getattr(
                MScriptUtil, 'set' + capValue + str(size) + 'ArrayItem', None)
        else:
            self._ptr = self._normPtr
        self._getter = getattr(MScriptUtil, 'get' + capValue, None)
        self._setter = getattr(MScriptUtil, 'set' + capValue, None)
        self._indexGetter = getattr(MScriptUtil,
                                    'get' + capValue + 'ArrayItem', None)
        self._indexSetter = getattr(MScriptUtil,
                                    'set' + capValue + 'Array', None)

    def __call__(self):
        return self._ptr

    def get(self):
        """
        Dereference the pointer - ie, get the actual value we're pointing to.
        """
        return self._getter(self._normPtr)

    def set(self, value):
        """
        Store the actual value we're pointing to.
        """
        return self._setter(self._normPtr, value)

    def __getitem__(self, index):
        if index < 0 or index > (self.size - 1):
            raise IndexError(index)
        if self._sizedIndexGetter is not None:
            # as of 2018, MSCriptUtil won't return the right result if we don't
            # use, ie, getFloat2ArrayItem(nPtr, 0, 1) - just doing, ie,
            # getFloatArrayItem(normPtr, 1) won't work
            return self._sizedIndexGetter(self._nPtr, index // self.size,
                                          index % self.size)
        else:
            return self._indexGetter(self._normPtr, index)

    def __setitem__(self, index, value):
        if index < 0 or index > (self.size - 1):
            raise IndexError(index)
        if self._sizedIndexSetter is not None:
            return self._sizedIndexSetter(self._nPtr, index // self.size,
                                          index % self.size, value)
        else:
            return self._indexSetter(self._normPtr, index, value)

    def __len__(self):
        return self.size


# fast convenience tests on API objects
def isValidMObjectHandle(obj):
    if isinstance(obj, MObjectHandle):
        return obj.isValid() and obj.isAlive()
    else:
        return False


def isValidMObject(obj):
    if isinstance(obj, MObject):
        return not obj.isNull()
    else:
        return False


def isValidMPlug(obj):
    if isinstance(obj, MPlug):
        return not obj.isNull()
    else:
        return False


def isValidMDagPath(obj):
    if isinstance(obj, MDagPath):
        # when the underlying MObject is no longer valid, dag.isValid() will still return true,
        # but obj.fullPathName() will be an empty string
        return obj.isValid() and obj.fullPathName()
    else:
        return False


def isValidMNode(obj):
    if isValidMObject(obj):
        return obj.hasFn(MFn.kDependencyNode)
    else:
        return False


def isValidMDagNode(obj):
    if isValidMObject(obj):
        return obj.hasFn(MFn.kDagNode)
    else:
        return False


def isValidMNodeOrPlug(obj):
    return isValidMPlug(obj) or isValidMNode(obj)

# returns a MObject for an existing node


def toMObject(nodeName):
    """ Get the API MObject given the name of an existing node """
    sel = MSelectionList()
    obj = MObject()
    result = None
    try:
        sel.add(nodeName)
        sel.getDependNode(0, obj)
        if isValidMObject(obj):
            result = obj
    except:
        pass
    return result


def toApiObject(nodeName, dagPlugs=True, plugs=True):
    # type: (Any, bool, bool) -> None
    """ Get the API MPlug, MObject or (MObject, MComponent) tuple given the name
    of an existing node, attribute, components selection

    Parameters
    ----------
    dagPlugs : bool
        if True, plug result will be a tuple of type (MDagPath, MPlug)
    plugs : bool
        if True, check if nodeName is an attribute/plug

    If we were unable to retrieve the node/attribute/etc, returns None
    """
    # special case check for empty string for speed...
    if not nodeName:
        return None

    sel = MSelectionList()
    try:
        sel.add(nodeName)
    except Exception:
        if "." in nodeName and plugs:
            # Compound Attributes
            #  sometimes the index might be left off somewhere in a compound attribute
            # (ex 'Nexus.auxiliary.input' instead of 'Nexus.auxiliary[0].input' )
            #  but we can still get a representative plug. this will return the equivalent of 'Nexus.auxiliary[-1].input'
            try:
                buf = nodeName.split('.')
                obj = toApiObject(buf[0])
                if isinstance(obj, MDagPath):
                    mfn = MFnDagNode(obj)
                else:
                    mfn = MFnDependencyNode(obj)
                plug = mfn.findPlug(buf[-1], False)

                if dagPlugs:  # and isValidMDagPath(obj) :
                    return (obj, plug)
                return plug
            except (RuntimeError, ValueError):
                pass
        return None
    else:
        if sel.length() != 1:
            return None
        splitName = nodeName.split('.')
        if len(splitName) > 1:
            if plugs:
                plug = MPlug()
                try:
                    sel.getPlug(0, plug)
                except RuntimeError:
                    pass
                else:
                    if dagPlugs:
                        try:
                            # Plugs with DagPaths
                            sel.add(splitName[0])
                            dag = MDagPath()
                            sel.getDagPath(1, dag)

                            # used to be a bug with some types that inherited from DagNode,
                            # but were not compatibile w/ MFnDagNode... these have been
                            # fixed, but we leave check in case another one crops up
                            if not dag.node().hasFn(MFn.kDagNode):
                                obj = MObject()
                                sel.getDependNode(1, obj)
                                return (obj, plug)

                            # if isValidMDagPath(dag) :
                            return (dag, plug)
                        except RuntimeError:
                            pass
                    return plug

            # Components
            dag = MDagPath()
            comp = MObject()
            try:
                sel.getDagPath(0, dag, comp)
            except RuntimeError:
                pass
            # if not isValidMDagPath(dag) :   return
            if not comp.isNull():
                return (dag, comp)

            # We may have gotten a published container attribute, which
            # auto- magically converts to the contained node it references
            # when added to an MSelectionList
            if plugs and len(splitName) == 2:
                # Thankfully, it seems you can't index / get children off an
                # aliased attribute - ie, myNode.myAlias[0] and
                # myNode.myAlias.childAttr don't work, even if myAlias point
                # to a multi / compound attr
                obj = MObject()
                try:
                    sel.add(splitName[0])
                    sel.getDependNode(1, obj)
                except RuntimeError:
                    pass
                else:
                    # Since it seems there's no api way to get at the plug for
                    # a published / aliased container attr, we just check for
                    # aliases...
                    mfn = MFnDependencyNode(obj)
                    aliases = []
                    if mfn.getAliasList(aliases):
                        for aliasName, trueName in util.pairIter(aliases):
                            if aliasName == splitName[1]:
                                return toApiObject('.'.join((splitName[0], trueName)),
                                                   dagPlugs=dagPlugs, plugs=plugs)
        else:
            try:
                # DagPaths
                dag = MDagPath()
                sel.getDagPath(0, dag)
                # if not isValidMDagPath(dag) : return

                # used to be a bug with some types that inherited from DagNode,
                # but were not compatibile w/ MFnDagNode... these have been
                # fixed, but we leave check in case another one crops up
                if not dag.node().hasFn(MFn.kDagNode):
                    raise RuntimeError
                return dag

            except RuntimeError:
                # Objects
                obj = MObject()
                sel.getDependNode(0, obj)
                # if not isValidMObject(obj) : return
                return obj


def toMDagPath(nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """
    obj = toMObject(nodeName)
    if obj:
        dagFn = MFnDagNode(obj)
        dagPath = MDagPath()
        dagFn.getPath(dagPath)
        return dagPath


# returns a MPlug for an existing plug
def toMPlug(plugName):
    """ Get the API MObject given the name of an existing plug (node.attribute) """
    nodeAndAttr = plugName.split('.', 1)
    obj = toMObject(nodeAndAttr[0])
    plug = None
    if obj:
        depNodeFn = MFnDependencyNode(obj)
        attr = depNodeFn.attribute(nodeAndAttr[1])
        plug = MPlug(obj, attr)
        if plug.isNull():
            plug = None
    return plug


def toComponentMObject(dagPath):
    """
    get an MObject representing all components of the passed dagPath

    The component type that will be returned depends on the exact type of
    object passed in - for instance, a poly mesh will return a component
    representing all the kMeshVertComponents.

    The exact choice of component type is determined by MItGeometry.
    """

    component = MObject()
    sel = MSelectionList()
    mit = MItGeometry(dagPath)
    while not mit.isDone():
        # MItGeometry.component is deprecated
        comp = mit.currentItem()
        # merge is True
        sel.add(dagPath, comp, True)
        next(mit)
    sel.getDagPath(0, dagPath, component)
    return component


# MDagPath, MPlug or MObject to name
# Note there is a kNamedObject API type but not corresponding MFn, thus
# I see no way of querying the name of something that isn't a kDependency node or a MPlug
# TODO : add components support, short/ long name support where applies
def MObjectName(obj):
    """ Get the name of an existing MPlug, MDagPath or MObject representing a dependency node"""
    from builtins import str

    if isValidMPlug(obj):
        return obj.name()
    elif isValidMNode(obj):
        depNodeFn = MFnDependencyNode(obj)
        return depNodeFn.name()
    elif isValidMDagPath(obj):
        # return obj.fullPathName()
        return obj.partialPathName()
    else:
        return str(obj)


# names to MObjects function (expected to be faster to share one selectionList)
def nameToMObject(*args):
    """ Get the API MObjects given names of existing nodes """
    sel = MSelectionList()
    for name in args:
        sel.add(name)
    result = []
    obj = MObject()
    for i in range(sel.length()):
        try:
            sel.getDependNode(i, obj)
        except:
            result.append(None)
        if isValidMObject(obj):
            result.append(obj)
        else:
            result.append(None)
    if len(result) == 1:
        return result[0]
    else:
        return tuple(result)


# wrap of api iterators
def MItNodes(*args, **kwargs):
    """ Iterator on MObjects of nodes of the specified types in the Maya scene,
        if a list of tyes is passed as args, then all nodes of a type included in the list will be iterated on,
        if no types are specified, all nodes of the scene will be iterated on
        the types are specified as Maya API types """
    typeFilter = MIteratorType()
    if args:
        if len(args) == 1:
            typeFilter.setFilterType(args[0])
        else:
            # annoying argument conversion for Maya API non standard C types
            typeIntM = MIntArray()
            MScriptUtil.createIntArrayFromList(args, typeIntM)
            typeFilter.setFilterList(typeIntM)
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.setObjectType(MIteratorType.kMObject)
    # create iterator with (possibly empty) typeFilter
    iterObj = MItDependencyNodes(typeFilter)
    while not iterObj.isDone():
        yield (iterObj.thisNode())
        next(iterObj)


# Iterators on nodes connections using MItDependencyGraph (ie listConnections/ listHistory)
def MItGraph(nodeOrPlug, *args, **kwargs):
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
    elif isValidMNode(nodeOrPlug):
        startObj = nodeOrPlug
    else:
        raise ValueError("'%s' is not a valid Node or Plug" % MObjectName(nodeOrPlug))
    upstream = kwargs.get('upstream', False)
    breadth = kwargs.get('breadth', False)
    plug = kwargs.get('plug', False)
    prune = kwargs.get('prune', False)
    if args:
        typeFilter = MIteratorType()
        if len(args) == 1:
            typeFilter.setFilterType(args[0])
        else:
            # annoying argument conversion for Maya API non standard C types
            typeIntM = MIntArray()
            MScriptUtil.createIntArrayFromList(args, typeIntM)
            typeFilter.setFilterList(typeIntM)
        # we start on a node or a plug
        if startPlug is not None:
            typeFilter.setObjectType(MIteratorType.kMPlugObject)
        else:
            typeFilter.setObjectType(MIteratorType.kMObject)
    # create iterator with (possibly empty) filter list and flags
    if upstream:
        direction = MItDependencyGraph.kUpstream
    else:
        direction = MItDependencyGraph.kDownstream
    if breadth:
        traversal = MItDependencyGraph.kBreadthFirst
    else:
        traversal = MItDependencyGraph.kDepthFirst
    if plug:
        level = MItDependencyGraph.kPlugLevel
    else:
        level = MItDependencyGraph.kNodeLevel
    iterObj = MItDependencyGraph(startObj, startPlug, typeFilter, direction, traversal, level)
    if prune:
        iterObj.enablePruningOnFilter()
    else:
        iterObj.disablePruningOnFilter()
    # iterates and yields MObjects
    while not iterObj.isDone():
        yield (iterObj.thisNode())
        next(iterObj)


# Iterators on dag nodes hierarchies using MItDag (ie listRelatives)
def MItDag(root=None, *args, **kwargs):
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
    if isValidMDagPath(root):
        startPath = root
    elif isValidMDagNode(root):
        startObj = root
    else:
        raise ValueError("'%s' is not a valid Dag Node" % MObjectName(root))
    breadth = kwargs.get('breadth', False)
    underworld = kwargs.get('underworld', False)
    prune = kwargs.get('prune', False)
    path = kwargs.get('path', False)
    allPaths = kwargs.get('allPaths', False)
    if args:
        typeFilter = MIteratorType()
        if len(args) == 1:
            typeFilter.setFilterType(args[0])
        else:
            # annoying argument conversion for Maya API non standard C types
            typeIntM = MIntArray()
            MScriptUtil.createIntArrayFromList(args, typeIntM)
            typeFilter.setFilterList(typeIntM)
        # we start on a MDagPath or a Mobject
        if startPath is not None:
            typeFilter.setObjectType(MIteratorType.kMDagPathObject)
        else:
            typeFilter.setObjectType(MIteratorType.kMObject)
    # create iterator with (possibly empty) filter list and flags
    if breadth:
        traversal = MItDag.kBreadthFirst
    else:
        traversal = MItDag.kDepthFirst
    iterObj = MItDag(typeFilter, traversal)
    if root is not None:
        iterObj.reset(typeFilter, startObj, startPath, traversal)

    if underworld:
        iterObj.traverseUnderWorld(True)
    else:
        iterObj.traverseUnderWorld(False)
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
    if allPaths:
        dPathArray = MDagPathArray()
        while not iterObj.isDone():
            if iterObj.isInstanced(True):
                obj = iterObj.currentItem()
                if not obj in instance:
                    iterObj.getAllPaths(dPathArray)
                    nbDagPath = dPathArray.length()
                    for i in range(nbDagPath):
                        dPath = MDagPath(dPathArray[i])
                        yield dPath
                    instance.append(obj)
            else:
                iterObj.getAllPaths(dPathArray)
                nbDagPath = dPathArray.length()
                for i in range(nbDagPath):
                    dPath = MDagPath(dPathArray[i])
                    yield dPath
            next(iterObj)
    elif path:
        while not iterObj.isDone():
            if iterObj.isInstanced(True):
                obj = iterObj.currentItem()
                if not obj in instance:
                    dPath = MDagPath()
                    iterObj.getPath(dPath)
                    yield dPath
                    instance.append(obj)
            else:
                dPath = MDagPath()
                iterObj.getPath(dPath)
                yield dPath
            next(iterObj)
    else:
        while not iterObj.isDone():
            obj = iterObj.currentItem()
            if iterObj.isInstanced(True):
                if not obj in instance:
                    yield obj
                    instance.append(obj)
            else:
                yield obj
            next(iterObj)


# Essentially duplicated in datatypes - only difference is
# whether return value is a PyMel or api object
# Repeated for speed
def getPlugValue(plug):
    """given an MPlug, get its value"""

    # if plug.isArray():
    #    raise TypeError, "array plugs of this type are not supported"

    obj = plug.attribute()
    apiType = obj.apiType()

    if apiType in [MFn.kAttribute2Double, MFn.kAttribute2Float, MFn.kAttribute2Short, MFn.kAttribute2Int,
                   MFn.kAttribute3Double, MFn.kAttribute3Float, MFn.kAttribute3Short, MFn.kAttribute3Int,
                   MFn.kAttribute4Double,
                   MFn.kCompoundAttribute]:
        res = []
        for i in range(plug.numChildren()):
            res.append(getPlugValue(plug.child(i)))
        return tuple(res)

    elif apiType in [MFn.kDoubleLinearAttribute, MFn.kFloatLinearAttribute]:
        return plug.asMDistance()

    elif apiType in [MFn.kDoubleAngleAttribute, MFn.kFloatAngleAttribute]:
        return plug.asMAngle()

    elif apiType == MFn.kTimeAttribute:
        return plug.asMTime()

    elif apiType == MFn.kNumericAttribute:
        # return getNumericPlugValue(plug)
        nAttr = MFnNumericAttribute(obj)
        dataType = nAttr.unitType()
        if dataType == MFnNumericData.kBoolean:
            return plug.asBool()

        elif dataType in [MFnNumericData.kShort, MFnNumericData.kInt, MFnNumericData.kLong, MFnNumericData.kByte]:
            return plug.asInt()

        elif dataType in [MFnNumericData.kFloat, MFnNumericData.kDouble, MFnNumericData.kAddr]:
            return plug.asDouble()
        raise "%s: unknown numeric attribute type: %s" % (plug.partialName(True, True, True, False, True, True), dataType)

    elif apiType == MFn.kEnumAttribute:
        return plug.asInt()

    elif apiType == MFn.kTypedAttribute:
        tAttr = MFnTypedAttribute(obj)
        dataType = tAttr.attrType()

        if dataType == MFnData.kInvalid:
            return None

        elif dataType == MFnData.kString:
            return plug.asString()

        elif dataType == MFnData.kNumeric:

            # all of the dynamic mental ray attributes fail here, but i have
            # no idea why they are numeric attrs and not message attrs.
            # cmds.getAttr returns None, so we will too.
            try:
                dataObj = plug.asMObject()
            except:
                return

            try:
                numFn = MFnNumericData(dataObj)
            except RuntimeError:
                if plug.isArray():
                    raise TypeError("%s: numeric arrays are not supported" %
                                    plug.partialName(True, True, True, False,
                                                     True, True))
                else:
                    raise TypeError("%s: attribute type is numeric, but its "
                                    "data cannot be interpreted numerically" %
                                    plug.partialName(True, True, True, False,
                                                     True, True))
            dataType = numFn.numericType()

            if dataType == MFnNumericData.kBoolean:
                return plug.asBool()

            elif dataType in [MFnNumericData.kShort, MFnNumericData.kInt, MFnNumericData.kLong, MFnNumericData.kByte]:
                return plug.asInt()

            elif dataType in [MFnNumericData.kFloat, MFnNumericData.kDouble, MFnNumericData.kAddr]:
                return plug.asDouble()

            elif dataType == MFnNumericData.k2Short:
                ptr1 = SafeApiPtr('short')
                ptr2 = SafeApiPtr('short')

                numFn.getData2Short(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType in [MFnNumericData.k2Int, MFnNumericData.k2Long]:
                ptr1 = SafeApiPtr('int')
                ptr2 = SafeApiPtr('int')

                numFn.getData2Int(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == MFnNumericData.k2Float:
                ptr1 = SafeApiPtr('float')
                ptr2 = SafeApiPtr('float')

                numFn.getData2Float(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == MFnNumericData.k2Double:
                ptr1 = SafeApiPtr('double')
                ptr2 = SafeApiPtr('double')

                numFn.getData2Double(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == MFnNumericData.k3Float:
                ptr1 = SafeApiPtr('float')
                ptr2 = SafeApiPtr('float')
                ptr3 = SafeApiPtr('float')

                numFn.getData3Float(ptr1(), ptr2(), ptr3())
                return (ptr1.get(), ptr2.get(), ptr3.get())

            elif dataType == MFnNumericData.k3Double:
                ptr1 = SafeApiPtr('double')
                ptr2 = SafeApiPtr('double')
                ptr3 = SafeApiPtr('double')

                numFn.getData3Double(ptr1(), ptr2(), ptr3())
                return (ptr1.get(), ptr2.get(), ptr3.get())

            elif dataType == MFnNumericData.kChar:
                return plug.asChar()

            raise TypeError(
                "%s: Unsupported numeric attribute: %s" %
                (plug.partialName(True, True, True, False, True, True),
                 dataType))

        elif dataType == MFnData.kMatrix:
            return MFnMatrixData(plug.asMObject()).matrix()

        elif dataType == MFnData.kDoubleArray:
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnDoubleArrayData(dataObj).array()

        elif dataType == MFnData.kIntArray:
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnIntArrayData(dataObj).array()

        elif dataType == MFnData.kPointArray:
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnPointArrayData(dataObj).array()

        elif dataType == MFnData.kVectorArray:
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnVectorArrayData(dataObj).array()

        elif dataType == MFnData.kStringArray:
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnStringArrayData(dataObj).array()
        raise TypeError("%s: Unsupported typed attribute: %s" %
                        (plug.partialName(True, True, True, False, True, True),
                         dataType))

    raise TypeError("%s: Unsupported Type: %s" %
                    (plug.partialName(True, True, True, False, True, True),
                     obj.apiTypeStr()))


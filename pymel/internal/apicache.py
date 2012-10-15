""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here
import inspect
import re
import itertools

import pymel.api as api
import pymel.versions as versions
import pymel.util as _util
import startup
import plogging as _plogging
from pymel.api.plugins import mpxNamesToApiEnumNames

_logger = _plogging.getLogger(__name__)

#===============================================================================
# Utility classes
#===============================================================================

class ApiEnum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )
    def __repr__(self):
        return '%s( %s )' % (self.__class__.__name__, super(ApiEnum, self).__repr__())
    def pymelName(self):
        import pymel.internal.factories as factories
        parts = list(self)
        pymelName = factories.apiClassNameToPymelClassName(self[0])
        if pymelName is not None:
            parts[0] = pymelName
        return '.'.join( [str(x) for x in parts] )

if versions.current() < versions.v2012:
    # Before 2012, api had Enum, and when we unpickle the caches, it will
    # need to be there... could rebuild the caches (like I had to do with
    # mayaApiMelBridge) but don't really want to...
    api.Enum = ApiEnum
    Enum = ApiEnum

def _defaultdictdict(cls, val=None):
    if val is None:
        return _util.defaultdict(dict)
    else:
        return _util.defaultdict(dict, val)

#===============================================================================
# ghost objects
#===============================================================================

def _makeDgModGhostObject(mayaType, dagMod, dgMod):
    print '#' * 60
    print "_makeDgModGhostObject(%s)" % mayaType
    import traceback
    print '\n'.join(traceback.format_stack())
    print '#' * 60
    
    # we create a dummy object of this type in a dgModifier (or dagModifier)
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene

    # Note: at one point, if we didn't call the dgMod/dagMod.deleteNode method,
    # and we call this function while loading a scene (for instance, if the scene requires
    # a plugin that isn't loaded, and defines custom node types), then the nodes were still
    # somehow created, despite never explicitly calling doIt()...
    # ... however, this seems to no longer be the case, and the deleteNode calls are apparently
    # harmful
    if type(dagMod) is not api.MDagModifier or type(dgMod) is not api.MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"

    # Regardless of whether we're making a DG or DAG node, make a parent first -
    # for some reason, this ensures good cleanup (don't ask me why...??)
    parent = dagMod.createNode ( 'transform', api.MObject())

    try :
        # DependNode
        obj = dgMod.createNode ( mayaType )
    except RuntimeError:
        # DagNode
        try:
            obj = dagMod.createNode ( mayaType, parent )
        except Exception, err:
            _logger.debug("Error trying to create ghost node for '%s': %s" %  (mayaType, err))
            return None

    if api.isValidMObject(obj) :
        return obj
    else :
        _logger.debug("Error trying to create ghost node for '%s'" %  mayaType)
        return None

class InvalidNodeTypeError(Exception): pass
class ManipNodeTypeError(InvalidNodeTypeError): pass

class _GhostObjMaker(object):
    '''Context used to get an mobject which we can query within this context.
    
    Automatically does any steps need to create and destroy the mobj within
    the context
    
    (Note - None may be returned in the place of any mobj)
    '''
    def __init__(self, mayaTypes, dagMod=None, dgMod=None, manipError=True,
                 multi=False):
        self.multi = multi
        if not multi:
            mayaTypes = [mayaTypes]
        self.mayaTypes = mayaTypes

        if dagMod is None:
            dagMod = api.MDagModifier()
        if dgMod is None:
            dgMod = api.MDGModifier()
        self.dagMod = dagMod
        self.dgMod = dgMod
        
        self.dagGhosts = False
        self.dgGhosts = False
        #self.theMod = None
        
        self.manipError = manipError
        self.byMayaType = {}
        self.ghosts = set()
        
    def __enter__(self):
        import maya.cmds as cmds
        
        for mayaType in self.mayaTypes:
            # check if an obj of the given type already exists in the scene, and
            # if so, use it
            madeGhost = False
            allObj = cmds.ls(exactType=mayaType)
            if allObj:
                obj = api.toMObject(allObj[0])
            else:
                obj = _makeDgModGhostObject(mayaType, self.dagMod, self.dgMod)
                if obj is not None:
                    self.ghosts.add(mayaType)
                    madeGhost = True
        
            if obj is not None:
                if (self.manipError 
                    and (obj.hasFn( api.MFn.kManipulator )      
                         or obj.hasFn( api.MFn.kManipContainer )
                         or obj.hasFn( api.MFn.kPluginManipContainer )
                         or obj.hasFn( api.MFn.kPluginManipulatorNode )
                         or obj.hasFn( api.MFn.kManipulator2D )
                         or obj.hasFn( api.MFn.kManipulator3D )
                         or obj.hasFn( api.MFn.kManip2DContainer)
                        )
                   ):
                    raise ManipNodeTypeError

                if madeGhost and not (self.dagGhosts and self.dgGhosts):
                    if obj.hasFn( api.MFn.kDagNode ):
                        self.dagGhosts = True
                    else:
                        self.dgGhosts = True
            self.byMayaType[mayaType] = obj
         
        # Note that we always create a "real" instance of the object by
        # calling doIt()... we used to not call doIt(), in which case
        # the mobject would actually still be queryable, but not in the
        # scene - thus the "ghost" obj - but this would create problems in
        # some cases - ie, if this was triggered during reference loading,
        # the objects would actually be entered into the scene... and
        # because we didn't call undoIt, they wouldn't get cleaned up
        if self.dagGhosts:
            self.dagMod.doIt()
        if self.dgGhosts:
            self.dgMod.doIt()
        if self.multi:
            return self.byMayaType
        else:
            return obj
                    
    def __exit__(self, type, value, traceback):
        try:
            if self.dagGhosts:
                self.dagMod.undoIt()
            if self.dgGhosts:
                self.dgMod.undoIt()
        except RuntimeError:
            stillExist = []
            for mayaType in self.ghosts:
                obj = self.byMayaType[mayaType]
                if obj is not None and api.isValidMObjectHandle(api.MObjectHandle(obj)):
                    stillExist.append(obj)
            if stillExist:
                mfnDag = api.MFnDagNode()
                mfnDep = api.MFnDependencyNode()
                names = []
                for obj in stillExist:
                    if obj.hasFn( api.MFn.kDagNode ):
                        # we need to delete the parent, since it will have
                        # created a parent transform too
                        mfnDag.setObject(obj)
                        mfnDag.setObject(mfnDag.parent(0))
                        names.append(mfnDag.partialPathName())
                    else:
                        mfnDep.setObject(obj)
                        names.append(mfnDep.name())
                print names
                #import maya.cmds as cmds
                #cmds.delete(names)

                mfnDag = api.MFnDagNode()
                dagMod = api.MDagModifier()
                dgMod = api.MDGModifier()
                
                delDag = False
                delDg = False
                
                for obj in stillExist:
                    if obj.hasFn( api.MFn.kDagNode ):
                        # we need to delete the parent, since it will have
                        # created a parent transform too
                        mfnDag.setObject(obj)
                        dagMod.deleteNode(mfnDag.parent(0))
                    else:
                        dgMod.deleteNode(obj)
                if delDag:
                    dagMod.doIt()
                if delDg:
                    dgMod.doIt()

#===============================================================================
# Utilities for query maya node info
#===============================================================================
_ABSTRACT_SUFFIX = ' (abstract)'
_ASSET_PREFIX = 'adskAssetInstanceNode_'
# You'd think getting a comprehensive list of node types would be easy, but
# due to strange behavior of various edge cases, it can be tricky...
def _getMayaTypes(real=True, abstract=True, basePluginTypes=True, addAncestors=True,
                  noManips=True, noPlugins=False):
    '''Returns a list of maya types
    
    Parameters
    ----------
    real : bool
        Include the set of real/createable nodes
    abstract : bool
        Include the set of abstract nodes (as defined by allNodeTypes(includeAbstract=True)
    basePluginTypes : bool
        Include the set of "base" plugin maya types (these are not returned by
        allNodeTypes(includeAbstract=True), and so, even though these types are
        abstract, this set shares no members with those added by the abstract
        flag
    addAncestors : bool
        If true, add to the list of nodes returned all of their ancestors as
        well
    noManips : bool
        If true, filter out any manipulator node types
    noPlugins : bool
        If true, filter out any nodes defined in plugins (note - if
        basePluginTypes is True, and noPlugins is False, the basePluginTypes
        will still be returned, as these types are not themselves defined in
        the plugin)
    '''
    import maya.cmds as cmds
    
    if abstract:
        # if we want abstract, need to do extra processing to strip the
        # trailing ' (abstract)'
        raw = cmds.allNodeTypes(includeAbstract=True)
        if real:
            nodes = [x[:-len(_ABSTRACT_SUFFIX)]
                     if x.endswith(_ABSTRACT_SUFFIX)
                     else x for x in raw]
        else:
            nodes = [x[:-len(_ABSTRACT_SUFFIX)] for x in raw
                     if x.endswith(_ABSTRACT_SUFFIX)]
        
        # For some reason, maya returns these names with cmds.allNodeTypes(includeAbstract=True):
        #   adskAssetInstanceNode_TlightShape
        #   adskAssetInstanceNode_TdnTx2D
        #   adskAssetInstanceNode_TdependNode
        # ...but they show up in parent hierarchies with a 'T' in front, ie:
        #   cmds.nodeType(adskMaterial, isTypeName=True, inherited=True)
        #           == [u'TadskAssetInstanceNode_TdependNode', u'adskMaterial']
        # the 'T' form is also what is needed to use it as an arg to nodeType...
        # ...so, stick the 'T' in front...
        nodes = ['T' + x if x.startswith(_ASSET_PREFIX) else x for x in nodes]
    elif real:
        nodes = cmds.allNodeTypes()
    else:
        nodes = []
    if basePluginTypes:
        import pymel.api.plugins
        nodes.extend(pymel.api.plugins.pluginMayaTypes)
    if addAncestors or noManips:
        # There are a few nodes which will not be returned even by
        # allNodeTypes(includeAbstract=True), but WILL show up in the
        # inheritance hierarchies...
        nodes = set(nodes)
        # iterate over a copy of nodes, because we'll be updating it as we go
        for mayaType in list(nodes):
            try:
                ancestors = getInheritance(mayaType, checkManip3D=noManips)
            except ManipNodeTypeError:
                nodes.remove(mayaType)
            except RuntimeError:
                # was an error querying - happens with some node types, like
                # adskAssetInstanceNode_TdnTx2D
                continue
            else:
                if addAncestors:
                    nodes.update(ancestors)
    if noPlugins:
        # if we have MNodeClass, this is easy...
        if hasattr(api, 'MNodeClass'):
            nonPluginNodes = set()
            for node in nodes:
                try:
                    api.MNodeClass(node).pluginName()
                except RuntimeError:
                    nonPluginNodes.add(node)
            nodes = nonPluginNodes
        else:
            # otherwise, we have to query all plugins...
            if not isinstance(nodes, set):
                nodes = set(nodes)
            for plugin in cmds.pluginInfo(q=1, listPlugins=True):
                nodes.difference_update(cmds.pluginInfo(plugin, q=1,
                                                        dependNode=True))
    if not isinstance(nodes, set):
        nodes = set(nodes)
    return nodes

def _getAbstractMayaTypes(**kwargs):
    kwargs.setdefault('real', False)
    kwargs['abstract'] = True
    return _getMayaTypes(**kwargs)

def _getRealMayaTypes(**kwargs):
    kwargs['real'] = True
    kwargs.setdefault('abstract', False)
    kwargs.setdefault('basePluginTypes', False)
    kwargs.setdefault('addAncestors', False)
    return _getMayaTypes(**kwargs)

def _getAllMayaTypes(**kwargs):
    kwargs['real'] = True
    kwargs['abstract'] = True
    return _getMayaTypes(**kwargs)

_fixedLineages = {}
        
def getInheritance( mayaType, checkManip3D=True ):
    """Get parents as a list, starting from the node after dependNode, and
    ending with the mayaType itself.
    
    Raises a ManipNodeTypeError if the node type fed in was a manipulator
    """

    # To get the inheritance post maya2012, we use nodeType(isTypeName=True),
    # which means we don't need a real node. However, in maya < 2012, nodeType
    # requires a real node.  To do get these without poluting the scene we use the
    # _GhostObjMaker, which on enter, uses a dag/dg modifier, and calls the doIt
    # method; we then get the lineage, and on exit, it calls undoIt.
    
    if versions.current() >= versions.v2012:
        import maya.cmds as cmds
        # We now have nodeType(isTypeName)! yay!
        try:
            lineage = cmds.nodeType(mayaType, isTypeName=True, inherited=True)
        except RuntimeError:
            lineage = None
    else:
        with _GhostObjMaker(mayaType) as obj:
            lineage = []
            if obj is not None:
                if obj.hasFn( api.MFn.kDagNode ):
                    name = api.MFnDagNode(obj).partialPathName()
                else:
                    name = api.MFnDependencyNode(obj).name()
                if not obj.isNull() and not obj.hasFn( api.MFn.kManipulator3D ) and not obj.hasFn( api.MFn.kManipulator2D ):
                    lineage = cmds.nodeType( name, inherited=1)
    if lineage is None:
        global _fixedLineages
        if not _fixedLineages:
            if versions.current() >= versions.v2012:
                controlPoint = cmds.nodeType('controlPoint', isTypeName=True,
                                             inherited=True)
            else:
                controlPoint = [u'containerBase',
                    u'entity',
                    u'dagNode',
                    u'shape',
                    u'geometryShape',
                    u'deformableShape',
                    u'controlPoint']
            # maya2013 introduced shadingDependNode...
            if versions.current() >= versions.v2013:
                texture2d = ['shadingDependNode', 'texture2d']
            else:
                texture2d = ['texture2d']
            # For whatever reason, nodeType(isTypeName) returns
            # None for the following mayaTypes:
            _fixedLineages = {
                'node':[],
                'file':texture2d + [u'file'],
                'lattice':controlPoint + [u'lattice'],
                'mesh':controlPoint + [u'surfaceShape', u'mesh'],
                'nurbsCurve':controlPoint + [u'curveShape', u'nurbsCurve'],
                'nurbsSurface':controlPoint + [u'surfaceShape', u'nurbsSurface'],
                'time':[u'time']
            }
        if mayaType in _fixedLineages:
            lineage = _fixedLineages[mayaType]
        else:
            raise RuntimeError("Could not query the inheritance of node type %s" % mayaType)
    elif checkManip3D and 'manip3D' in lineage:
        raise ManipNodeTypeError
    assert (mayaType == 'node' and lineage == []) or lineage[-1] == mayaType

    return lineage

#===============================================================================
# Name utilities
#===============================================================================

def nodeToApiName(nodeName):
    return 'k' + _util.capitalize(nodeName)

def getLowerCaseMapping(names):
    uniqueLowerNames = {}
    multiLowerNames = {}
    for name in names:
        lowerType = name.lower()
        if lowerType in multiLowerNames:
            multiLowerNames[lowerType].append(name)
        elif lowerType in uniqueLowerNames:
            multiLowerNames[lowerType] = [uniqueLowerNames.pop(lowerType), name]
        else:
            uniqueLowerNames[lowerType] = name
    return uniqueLowerNames, multiLowerNames

API_NAME_MODIFIERS = {
    'base':'',
    'abstract':'',
    'node':'',
    'shape':'',
    'mod(?!(ify|ifier))':'modify',
    'mod(?!(ify|ifier))':'modifier',
    'modifier':'mod',
    'modify':'mod',
    'poly(?!gon)':'polygon',
    'polygon':'poly',
    'vert(?!(ex|ice))':'vertex',
    'vert(?!(ex|ice))':'vertice',
    'vertice':'vert',
    'vertex':'vert',
    'subd(?!iv)':'subdiv',
    'subd(?!iv)':'subdivision',
    'subdiv(?!ision)':'subd',
    'subdiv(?!ision)':'subdivision',
    'subdivision':'subd',
    'subdivision':'subdiv',
    '^th(custom)?':'plugin',
    }
API_NAME_MODIFIERS = [(re.compile(find), replace)
                      for find, replace in API_NAME_MODIFIERS.iteritems()]

apiSuffixes = ['', 'node', 'shape', 'shapenode']

#===============================================================================
# Cache classes
#===============================================================================

class ApiMelBridgeCache(startup.SubItemCache):
    NAME = 'mayaApiMelBridge'
    DESC = 'the API-MEL bridge' 
    COMPRESSED = True
    USE_VERSION = False
    _CACHE_NAMES = '''apiToMelData apiClassOverrides'''.split()
    
    CACHE_TYPES = {'apiToMelData':_defaultdictdict}
    STORAGE_TYPES = {'apiToMelData':dict}


class ApiCache(startup.SubItemCache):
    NAME = 'mayaApi'
    DESC = 'the API cache'
    COMPRESSED = True
    USE_VERSION = True
    _CACHE_NAMES = '''apiTypesToApiEnums apiEnumsToApiTypes mayaTypesToApiTypes
                   apiTypesToApiClasses apiClassInfo'''.split()


    EXTRA_GLOBAL_NAMES = tuple(['mayaTypesToApiEnums'])
                            
    # Descriptions of various elements:
    
    # Maya static info :
    # Initializes various static look-ups to speed up Maya types conversions
    # self.apiClassInfo
    # self.apiTypesToApiEnums
    # self.apiEnumsToApiTypes
    # self.apiTypesToApiClasses

    # Lookup of currently existing Maya types as keys with their corresponding API type as values.
    # Not a read only (static) dict as these can change (if you load a plugin)
    # self.mayaTypesToApiTypes

    # lookup tables for a direct conversion between Maya type to their MFn::Types enum
    # self.mayaTypesToApiEnums

    # creating these will crash Maya!
    CRASH_TYPES = {
        'xformManip':'kXformManip',
        'moveVertexManip':'kMoveVertexManip',
    }

    # Not currently used, but hold any overrides for mayaTypesToApiTypes...
    # ie, for cases where the name guess is wrong, etc
    MAYA_TO_API_OVERRIDES = {
                             'node':'kDependencyNode',  # this what is returned by allNodeTypes(includeAbstract=True)
                             'dependNode':'kDependencyNode',  # this is the name pymel uses
                             'smear':'kSmear',          # a strange one - a plugin node that has an apitype... is in studioImport.so... also has a doc entry... 
                            }
    DEFAULT_API_TYPE = 'kDependencyNode'

    def __init__(self, docLocation=None):
        super(ApiCache, self).__init__()
        for name in self.EXTRA_GLOBAL_NAMES:
            setattr(self, name, {})
        self.docLocation = docLocation

    def _buildMayaToApiInfo(self):

        self._buildMayaNodeInfo()
        # Fixes for types that don't have a MFn by doing a node creation and testing it
        unknownTypes = set()
        toCreate = []

        self.mayaTypesToApiTypes = self._buildMayaReservedTypes()
        
        for mayaType in self.allMayaTypes:
            if mayaType not in self.mayaTypesToApiTypes:
                toCreate.append(mayaType)

        if toCreate:
            # Put in a debug, because ghost nodes can be problematic...
            _logger.debug("Starting to create ghost nodes...")
            with _GhostObjMaker(toCreate, manipError=False, multi=True) as typeToObj:
                for mayaType in toCreate:
                    obj = typeToObj[mayaType]
                    if obj :
                        apiType = obj.apiTypeStr()
                        self.mayaTypesToApiTypes[mayaType] = apiType
                    else:
                        unknownTypes.add(mayaType)
            # Put in a debug, because ghost nodes can be problematic...
            _logger.debug("...finished creating ghost nodes")
        
        if len(unknownTypes) > 0:
            _logger.warn("Unable to get maya-to-api type info for the following nodes: %s" % ", ".join(unknownTypes))
            for mayaType in unknownTypes:
                # For unknown types, use the parent type
                try:
                    inheritance = getInheritance(mayaType)
                except ManipNodeTypeError:
                    continue
                apiType = None
                
                # if we have a node A, and we get back it's inheritance as:
                #    [E, D, C, B, A]
                # ...and 'D' is the first parent that we can find info for, we
                # may as well set the types for 'B' and 'C' parents as well...
                # also, this means that we may already have set THIS mayaType
                # (if it was the parent of another unknown node we already set),
                # so we loop through all nodes in inheritance, including this
                # type 
                toSet = [mayaType]
                if inheritance:
                    for parent in reversed(inheritance):
                        apiType = self.mayaTypesToApiTypes.get(parent)
                        if apiType:
                            break
                        else:
                            toSet.append(parent)
                if not apiType:
                    apiType = self.DEFAULT_API_TYPE
                for node in toSet:
                    self.mayaTypesToApiTypes[node] = apiType

        for mayaType, apiType in self.mayaTypesToApiTypes.iteritems() :
            self.addMayaType( mayaType, apiType )

    def _buildApiTypesList(self):
        """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with
        an existing api type"""

        self.apiTypesToApiEnums = dict( inspect.getmembers(api.MFn, lambda x:type(x) is int))
        self.apiEnumsToApiTypes = dict( (self.apiTypesToApiEnums[k], k) for k in self.apiTypesToApiEnums.keys())


    def _buildMayaReservedTypes(self, force=False):
        """
        Build a list of Maya reserved types.
        
        These cannot be created directly from the API, thus the dgMod trick to
        find the corresponding Maya type won't work
        """
        reservedMayaTypes = {}
        
        # start with plugin types
        import pymel.api.plugins as plugins
        for mpxName, mayaNode in plugins.mpxNamesToMayaNodes.iteritems():
            reservedMayaTypes[mayaNode] = plugins.mpxNamesToApiEnumNames[mpxName]
        
        for mayaType in self.nonCreatableNodes:
            if mayaType in reservedMayaTypes:
                continue
            apiGuess = self._guessApiTypeByName(mayaType)
            if apiGuess:
                reservedMayaTypes[mayaType] = apiGuess
        
        reservedMayaTypes.update(self.MAYA_TO_API_OVERRIDES)
        # filter to make sure all these types exist in current version (some are Maya2008 only)
        reservedMayaTypes = dict((item[0], item[1])
                                      for item in reservedMayaTypes.iteritems()
                                      if item[1] in self.apiTypesToApiEnums)
        
        return reservedMayaTypes
    
    # TODO: eventually, would like to move the node-heirarchy-building stuff
    # from cmdcache into here... we could then cache the node inheritance info,
    # instead of constantly re-querying it in various places...
    def _buildMayaNodeInfo(self):
        '''Stores tempory information about maya nodes + names 
        '''
        if getattr(self, '_builtMayaNodeInfo', False):
            return
        
        if not self.apiTypesToApiEnums:
            self._buildApiTypesList()
        
        self.allMayaTypes = _getAllMayaTypes()
        
        # use noManips=False just so it's faster... we're just using this to
        # subtract out nodes from allNodes, so it won't matter if it has manip
        # node types
        realTypes = _getRealMayaTypes(noManips=False)
        # this will actually give slightly different results than just calling
        # _getAbstractNodes, due to addAncestors...
        self.nonCreatableNodes = self.allMayaTypes - realTypes 
        
        self.uniqueLowerMaya, self.multiLowerMaya = getLowerCaseMapping(self.allMayaTypes)
        self.allLowerMaya = set(self.uniqueLowerMaya) | set(self.multiLowerMaya)
        self.uniqueLowerApi, self.multiLowerApi = getLowerCaseMapping(self.apiTypesToApiEnums)
        self._builtMayaNodeInfo = True
        return
        
    # _buildMayaNodeInfo must already have been called...
    def _guessApiTypeByName(self, nodeName):
        # first, try the easy case...
        apiName = nodeToApiName(nodeName)
        if apiName in self.apiTypesToApiEnums:
            return apiName
        
        lowerNode = nodeName.lower()
        if lowerNode not in self.uniqueLowerMaya:
            return None
        
        # now, try with various modifications...
        possibleApiNames = set()
        
        possibleModifications = [(find, replace)
                                 for find, replace in API_NAME_MODIFIERS
                                 if find.search(lowerNode)]
        
        # find all possible combinations of all possible modifications
        for modifyNum in xrange(len(possibleModifications) + 1):
            for modifyCombo in itertools.combinations(possibleModifications, modifyNum):
                baseName = lowerNode
                for find, replace in modifyCombo:
                    baseName = find.sub(replace, baseName)
                if not baseName:
                    # if we've eliminated the name with our changes - ie,
                    # 'shape' would go to '' - then skip
                    continue
                if baseName != lowerNode and baseName in self.allLowerMaya:
                    # if after modification, our new name is the name of another
                    # maya node, skip
                    continue
                apiLower = 'k' + baseName
                if apiLower in self.uniqueLowerApi:
                    possibleApiNames.add(self.uniqueLowerApi[apiLower])
                else:
                    for suffix in apiSuffixes:
                        apiWithSuffix = apiLower + suffix
                        if apiWithSuffix in self.uniqueLowerApi:
                            possibleApiNames.add(self.uniqueLowerApi[apiWithSuffix])
        
        if len(possibleApiNames) == 1:
            return list(possibleApiNames)[0]
        return None
    
    # Note - it's possible there are multiple substrings of the same length
    # that are all "tied" for longest - this method will only return the first
    # it finds
    @staticmethod
    def _longestCommonSubstring(str1, str2):
        if str1 == str2:
            return [str1]
        
        if len(str1) > len(str2):
            longer = str1
            shorter = str2
        else:
            longer = str2
            shorter = str1
        maxSize = len(shorter)
        for strSize in xrange(maxSize, 0, -1):
            for startPos in xrange(0, maxSize - strSize + 1):
                subStr = shorter[startPos:startPos + strSize]
                if subStr in longer:
                    return subStr
        return ''
    
    @staticmethod
    def _bestMatches(theStr, otherStrings, minLength=2, caseSensitive=False):
        if not caseSensitive:
            theStr = theStr.lower()
        byLength = {}
        for otherString in otherStrings:
            if caseSensitive:
                compOther = otherString
            else:
                compOther = otherString.lower()
            size = len(_longestCommonSubstring(theStr, compOther))
            byLength.setdefault(size, []).append(otherString)
        longest = max(byLength)
        if longest >= minLength:
            return byLength[longest]
        else:
            return []

    def _buildApiClassInfo(self):
        _logger.debug("Starting ApiCache._buildApiClassInfo...") 
        from pymel.internal.parsers import ApiDocParser
        self.apiClassInfo = {}
        parser = ApiDocParser(api, enumClass=ApiEnum, docLocation=self.docLocation)

        for name, obj in inspect.getmembers( api, lambda x: type(x) == type and x.__name__.startswith('M') ):
            if not name.startswith( 'MPx' ):
                try:
                    info = parser.parse(name)
                    self.apiClassInfo[ name ] = info
                except (IOError, OSError, ValueError,IndexError), e:
                    import errno
                    _logger.warn( "failed to parse docs for %r:" % name)
                    if isinstance(e, (IOError, OSError)) and e.errno == errno.ENOENT:
                        _logger.warn("%s" % name, e)
                    else:
                        import traceback
                        _logger.warn(traceback.format_exc())
                        
        _logger.debug("...finished ApiCache._buildApiClassInfo")
        
    def _buildApiTypeToApiClasses(self):
        self.apiTypesToApiClasses = {}
        def _MFnType(x) :
            if x == api.MFnBase :
                return self.apiEnumsToApiTypes[ 1 ]  # 'kBase'
            else :
                try :
                    return self.apiEnumsToApiTypes[ x().type() ]
                except :
                    return self.apiEnumsToApiTypes[ 0 ] # 'kInvalid'

        # all of maya OpenMaya api is now imported in module api's namespace
        mfnClasses = inspect.getmembers(api, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
        for name, mfnClass in mfnClasses:
            current = _MFnType(mfnClass)
            if not current:
                _logger.warning("MFnClass gave MFnType %s" % current)
            elif current == 'kInvalid':
                _logger.warning("MFnClass gave MFnType %s" % current)
            else:
                self.apiTypesToApiClasses[ current ] = mfnClass
        # we got our map by going from Mfn to enum; however, multiple enums can
        # map to the same MFn, so need to fill in the gaps of missing enums for
        # enums to MFn...
        
        # we do this by querying the maya hierarchy, and marching up it until
        # we find an entry that IS in apiTypesToApiClasses
        for mayaType, apiType in self.mayaTypesToApiTypes.iteritems():
            if apiType not in self.apiTypesToApiClasses:
                mfnClass = None
                try:
                    inheritance = getInheritance(mayaType)
                except Exception:
                    continue
                # inheritance always ends with that node type... so skip that...
                for mayaParentType in reversed(inheritance[:-1]):
                    parentApiType = self.mayaTypesToApiTypes.get(mayaParentType)
                    if parentApiType:
                        parentMfn = self.apiTypesToApiClasses.get(parentApiType)
                        if parentMfn: 
                            mfnClass = parentMfn
                            break
                if not mfnClass:
                    mfnClass = api.MFnDependencyNode
                self.apiTypesToApiClasses[apiType] = mfnClass
                
    def _buildApiRelationships(self) :
        """
        Used to rebuild api info from scratch.
        
        WARNING: will load all maya-installed plugins, without making an
        attempt to return the loaded plugins to the state they were at before
        this command is run.  Also, the act of loading all the plugins may
        crash maya, especially if done from a non-GUI session
        """
        # Put in a debug, because this can be crashy
        _logger.debug("Starting ApiCache._buildApiTypeHierarchy...")        
        

        if not startup.mayaStartupHasRun():
            startup.mayaInit()
        import maya.cmds

        import pymel.api.plugins as plugins
        # load all maya plugins
        
        # There's some weirdness with plugin loading on windows XP x64... if
        # you have a fresh user profile, and do:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.mel as mel
        # mel.eval('''source "initialPlugins.mel"''')
        
        # ..then things work.  But if you import maya.OpenMaya:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.OpenMaya
        # import maya.mel as mel
        # mel.eval('''source "initialPlugins.mel"''')
        
        # ...it crashes when loading Mayatomr.  Also, oddly, if you load
        # Mayatomr directly, instead of using initialPlugins.mel, it also
        # crashes:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.cmds
        # maya.cmds.loadPlugin('C:\\3D\\Autodesk\\Maya2012\\bin\\plug-ins\\Mayatomr.mll')
        
        # Anyway, for now, adding in the line to do sourcing of initialPlugins.mel
        # until I can figure out if it's possible to avoid this crash...
#        import maya.mel
#        maya.mel.eval('source "initialPlugins.mel"')
#        plugins.loadAllMayaPlugins()

        # Now that we have static info for all plugin types, we shouldn't need
        # to have any plugins loaded before parsing api info...
        plugins.unloadAllPlugins()

        self._buildApiClassInfo()

        self._buildMayaToApiInfo()
        self._buildApiTypeToApiClasses()
        
        _logger.debug("...finished ApiCache._buildApiTypeHierarchy")

    def addMayaType(self, mayaType, apiType=None, updateObj=None):
        """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """

        if apiType is not 'kInvalid' :
            apiEnum = getattr( api.MFn, apiType )
            self.mayaTypesToApiTypes[mayaType] = apiType
            self.mayaTypesToApiEnums[mayaType] = apiEnum

    def removeMayaType(self, mayaType, updateObj=None):
        """ Remove a type from the MayaTypes lists.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """
        self.mayaTypesToApiEnums.pop( mayaType, None )
        self.mayaTypesToApiTypes.pop( mayaType, None )

    def read(self, raw=False):
        data = super(ApiCache, self).read()
        if not raw:
            # Before 2012, we cached reservedMayaTypes and reservedApiTypes,
            # even though they weren't used...
            if data is not None and len(data) != len(self._CACHE_NAMES):
                if len(data) == 8 and versions.current() < versions.v2012:
                    data = data[2:6] + data[7:]
                else:
                    # we need to rebuild, return None
                    data = None
        return data

    def rebuild(self):
        """Rebuild the api cache from scratch
        
        Unlike 'build', this does not attempt to load a cache file, but always
        rebuilds it by parsing the docs, etc.
        """
        _logger.info( "Rebuilding the API Caches..." )

        # fill out the data structures
        self._buildApiTypesList()
        #_buildMayaTypesList()
        
        self._buildApiRelationships()

        # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
        _logger.info( 'merging in dictionary of manual api overrides')
        self._mergeClassOverrides()

    def _mergeClassOverrides(self, bridgeCache=None):
        if bridgeCache is None:
            bridgeCache = ApiMelBridgeCache()
            bridgeCache.build()
        _util.mergeCascadingDicts( bridgeCache.apiClassOverrides, self.apiClassInfo, allowDictToListMerging=True )

    def melBridgeContents(self):
        return self._mayaApiMelBridge.contents()
    
    def extraDicts(self):
        return tuple( getattr(self, x) for x in self.EXTRA_GLOBAL_NAMES )

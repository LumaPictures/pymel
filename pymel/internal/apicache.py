""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

# They will be imported / redefined later in Pymel, but we temporarily need them here
from builtins import range
from past.builtins import basestring
from builtins import object
import inspect
import os
import re
import itertools

import pymel.api as api
import pymel.versions as versions
import pymel.util as _util
from . import startup
from . import plogging as _plogging
from pymel.api.plugins import mpxNamesToApiEnumNames

_logger = _plogging.getLogger(__name__)

#===============================================================================
# Utility classes
#===============================================================================


class ApiEnum(tuple):

    def __str__(self):
        return '.'.join([str(x) for x in self])

    def __repr__(self):
        return '%s( %s )' % (self.__class__.__name__, super(ApiEnum, self).__repr__())

    def pymelName(self):
        import pymel.internal.factories as factories
        parts = list(self)
        pymelName = factories.apiClassNameToPymelClassName(self[0])
        if pymelName is not None:
            parts[0] = pymelName
        return '.'.join([str(x) for x in parts])


def _defaultdictdict(cls, val=None):
    if val is None:
        return _util.defaultdict(dict)
    else:
        return _util.defaultdict(dict, val)

#===============================================================================
# ghost objects
#===============================================================================


class GhostObjsOkHere(object):
    _OK = False

    @classmethod
    def OK(cls):
        return cls._OK

    def __enter__(self):
        self.oldOK = self.OK()
        type(self)._OK = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        type(self)._OK = self.oldOK


def _makeDgModGhostObject(mayaType, dagMod, dgMod):
    # only time post-2012 when we should have to call this func is when
    # rebuilding caches - ie, running from inside ApiCache
    if not GhostObjsOkHere.OK():
        _logger.raiseLog(_logger.WARNING, '_makeDgModGhostObject should be '
                                          'unnecessary in maya versions '
                                          'past 2012 (except when '
                                          'rebuilding cache)  - was making '
                                          'a {!r} object'.format(mayaType))

    _logger.debug("Creating ghost node: %s" % mayaType)

    # we create a dummy object of this type in a dgModifier (or dagModifier)
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene

    # Note: at one point, if we didn't call the dgMod/dagMod.deleteNode method,
    # and we call this function while loading a scene (for instance, if the scene requires
    # a plugin that isn't loaded, and defines custom node types), then the nodes were still
    # somehow created, despite never explicitly calling doIt()...
    # ... however, this seems to no longer be the case, and the deleteNode calls are apparently
    # harmful
    if type(dagMod) is not api.MDagModifier or type(dgMod) is not api.MDGModifier:
        raise ValueError("Need a valid MDagModifier and MDGModifier or cannot return a valid MObject")

    # Regardless of whether we're making a DG or DAG node, make a parent first -
    # for some reason, this ensures good cleanup (don't ask me why...??)
    parent = dagMod.createNode('transform', api.MObject())

    try:
        # DependNode
        obj = dgMod.createNode(mayaType)
    except RuntimeError:
        # DagNode
        try:
            obj = dagMod.createNode(mayaType, parent)
        except Exception as err:
            _logger.debug("Error trying to create ghost node for '%s': %s" % (mayaType, err))
            return None

    if api.isValidMObject(obj):
        return obj
    else:
        _logger.debug("Error trying to create ghost node for '%s'" % mayaType)
        return None


class InvalidNodeTypeError(Exception):
    pass


class ManipNodeTypeError(InvalidNodeTypeError):
    pass


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
                if mayaType in ApiCache.CRASH_TYPES:
                    if self.manipError and "Manip" in mayaType:
                        raise ManipNodeTypeError
                    obj = None
                else:
                    obj = _makeDgModGhostObject(mayaType, self.dagMod, self.dgMod)
                if obj is not None:
                    self.ghosts.add(mayaType)
                    madeGhost = True

            if obj is not None:
                if (self.manipError
                        and (obj.hasFn(api.MFn.kManipulator)
                             or obj.hasFn(api.MFn.kManipContainer)
                             or obj.hasFn(api.MFn.kPluginManipContainer)
                             or obj.hasFn(api.MFn.kPluginManipulatorNode)
                             or obj.hasFn(api.MFn.kManipulator2D)
                             or obj.hasFn(api.MFn.kManipulator3D)
                             or obj.hasFn(api.MFn.kManip2DContainer)
                             )
                    ):
                    raise ManipNodeTypeError

                if madeGhost and not (self.dagGhosts and self.dgGhosts):
                    if obj.hasFn(api.MFn.kDagNode):
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

    def __exit__(self, exc_type, exc_value, traceback):
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
                    if obj.hasFn(api.MFn.kDagNode):
                        # we need to delete the parent, since it will have
                        # created a parent transform too
                        mfnDag.setObject(obj)
                        mfnDag.setObject(mfnDag.parent(0))
                        names.append(mfnDag.partialPathName())
                    else:
                        mfnDep.setObject(obj)
                        names.append(mfnDep.name())
                print(names)
                #import maya.cmds as cmds
                # cmds.delete(names)

                mfnDag = api.MFnDagNode()
                dagMod = api.MDagModifier()
                dgMod = api.MDGModifier()

                delDag = False
                delDg = False

                for obj in stillExist:
                    if obj.hasFn(api.MFn.kDagNode):
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

if hasattr(api, 'MNodeClass'):
    # if we have MNodeClass, this is easy...
    def isPluginNode(nodeName):
        try:
            api.MNodeClass(nodeName).pluginName()
            return True
        except RuntimeError:
            return False

else:
    # otherwise, we have to query all plugins...
    def isPluginNode(nodeName):
        import maya.cmds as cmds
        for plugin in cmds.pluginInfo(q=1, listPlugins=True):
            plugNodes = cmds.pluginInfo(plugin, q=1, dependNode=True)
            # plugNodes may be None...
            if plugNodes and nodeName in plugNodes:
                return True
        return False

# You'd think getting a comprehensive list of node types would be easy, but
# due to strange behavior of various edge cases, it can be tricky...


def _getMayaTypes(real=True, abstract=True, basePluginTypes=True, addAncestors=True,
                  noManips=True, noPlugins=False, returnRealAbstract=False):
    # type: (bool, bool, bool, bool, Union[bool, str], bool, bool) -> None
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
    noManips : Union[bool, str]
        If true, filter out any manipulator node types; if the special value
        'fast', then it will filter out manipulator node types, but will do so
        using a faster method that may potentially be less thorough
    noPlugins : bool
        If true, filter out any nodes defined in plugins (note - if
        basePluginTypes is True, and noPlugins is False, the basePluginTypes
        will still be returned, as these types are not themselves defined in
        the plugin)
    returnRealAbstract : bool
        if True, will return two sets, realNodes and abstractNodes; otherwise,
        returns a single set of all the desired nodes (more precisely, realNodes
        is defined as the set of directly createdable nodes matching the
        criteria, and abstract are all non-createable nodes matching the
        criteria)
    '''
    import maya.cmds as cmds

    # keep track of which nodes were abstract - this can be useful later,
    # especially pre-2012
    abstractNodes = set()
    realNodes = set()
    if abstract or addAncestors:
        # if we want abstract, need to do extra processing to strip the
        # trailing ' (abstract)'
        raw = cmds.allNodeTypes(includeAbstract=True)
        for node in raw:
            if node.endswith(_ABSTRACT_SUFFIX):
                node = node[:-len(_ABSTRACT_SUFFIX)]
                # For some reason, maya returns these names with cmds.allNodeTypes(includeAbstract=True):
                #   adskAssetInstanceNode_TlightShape
                #   adskAssetInstanceNode_TdnTx2D
                #   adskAssetInstanceNode_TdependNode
                # ...but they show up in parent hierarchies with a 'T' in front, ie:
                #   cmds.nodeType(adskMaterial, isTypeName=True, inherited=True)
                #           == [u'TadskAssetInstanceNode_TdependNode', u'adskMaterial']
                # the 'T' form is also what is needed to use it as an arg to nodeType...
                # ...so, stick the 'T' in front...
                if node.startswith(_ASSET_PREFIX):
                    node = 'T' + node
                abstractNodes.add(node)
            else:
                if not real:
                    continue
                realNodes.add(node)
    elif real:
        realNodes.update(cmds.allNodeTypes())

    if basePluginTypes:
        import pymel.api.plugins
        abstractNodes.update(pymel.api.plugins.pluginMayaTypes)

    # If we're doing addAncestors anyway, might was well get manips with the
    # more thorough method, using the inheritance chain, since we're doing that
    # anyway...
    if noManips == 'fast' and not addAncestors:
        manips = set(cmds.nodeType('manip3D', isTypeName=1, derived=1))
        realNodes.difference_update(manips)
        abstractNodes.difference_update(manips)
        noManips = False
    if addAncestors or noManips:
        # There are a few nodes which will not be returned even by
        # allNodeTypes(includeAbstract=True), but WILL show up in the
        # inheritance hierarchies...

        # iterate over first real nodes, then abstract nodes... this lets us
        # take advantage of inheritance caching - especially pre-2012, where
        # inheritance chain of abstract nodes is not directly queryable -
        # since getInheritance will cache the inheritance chain of the given
        # node, AND all its parents

        # make a copy of what we iterate over, as we will be modifying
        # realNodes and abstractNodes as we go...
        for mayaType in list(itertools.chain(realNodes, abstractNodes)):
            try:
                ancestors = getInheritance(mayaType, checkManip3D=noManips)
            except ManipNodeTypeError:
                realNodes.discard(mayaType)
                abstractNodes.discard(mayaType)
            except RuntimeError:
                # was an error querying - happens with some node types, like
                # adskAssetInstanceNode_TdnTx2D
                continue
            else:
                if addAncestors and ancestors:
                    abstractNodes.update(set(ancestors) - realNodes)
    if noPlugins:
        for nodeSet in (realNodes, abstractNodes):
            # need to modify in place, so make copy of nodeSet...
            for node in list(nodeSet):
                if isPluginNode(node):
                    nodeSet.remove(node)

    # we may have put nodes in realNodes or abstractNodes for info purposes...
    # make sure they are cleared before returning results, if needed...
    if not real:
        realNodes = set()
    if not abstract:
        abstractNodes = set()

    if returnRealAbstract:
        return realNodes, abstractNodes
    else:
        return realNodes | abstractNodes


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
_cachedInheritances = {}


def getInheritance(mayaType, checkManip3D=True, checkCache=True,
                   updateCache=True):
    """Get parents as a list, starting from the node after dependNode, and
    ending with the mayaType itself.

    Raises a ManipNodeTypeError if the node type fed in was a manipulator
    """

    # To get the inheritance post maya2012, we use nodeType(isTypeName=True),
    # which means we don't need a real node. However, in maya < 2012, nodeType
    # requires a real node.  To do get these without poluting the scene we use the
    # _GhostObjMaker, which on enter, uses a dag/dg modifier, and calls the doIt
    # method; we then get the lineage, and on exit, it calls undoIt.
    global _cachedInheritances
    if checkCache and mayaType in _cachedInheritances:
        return _cachedInheritances[mayaType]

    import maya.cmds as cmds
    lineage = None
    # We now have nodeType(isTypeName)! yay!
    try:
        lineage = cmds.nodeType(mayaType, isTypeName=True, inherited=True)
    except RuntimeError:
        pass
    if lineage is None:
        global _fixedLineages
        if not _fixedLineages:
            controlPoint = cmds.nodeType('controlPoint', isTypeName=True,
                                         inherited=True)
            # maya2013 introduced shadingDependNode...
            texture2d = ['shadingDependNode', 'texture2d']

            # For whatever reason, nodeType(isTypeName) returns
            # None for the following mayaTypes:
            _fixedLineages = {
                'node': [],
                'file': texture2d + [u'file'],
                'lattice': controlPoint + [u'lattice'],
                'mesh': controlPoint + [u'surfaceShape', u'mesh'],
                'nurbsCurve': controlPoint + [u'curveShape', u'nurbsCurve'],
                'nurbsSurface': controlPoint + [u'surfaceShape', u'nurbsSurface'],
                'time': [u'time']
            }
        if mayaType in _fixedLineages:
            lineage = _fixedLineages[mayaType]
        else:
            raise RuntimeError("Could not query the inheritance of node type %s" % mayaType)
    elif checkManip3D and 'manip3D' in lineage:
        raise ManipNodeTypeError

    try:
        assert (mayaType == 'node' and lineage == []) or lineage[-1] == mayaType
    except Exception:
        print(mayaType, lineage)
        raise

    if len(set(lineage)) != len(lineage):
        # cyclical lineage:  first discovered with xgen nodes.
        # might be a result of multiple inheritance being returned strangely by nodeType.
        #
        # an example lineage is:
        # [u'containerBase', u'entity', u'dagNode', u'shape', u'geometryShape', u'locator', u'THlocatorShape', u'SphereLocator',
        #  u'containerBase', u'entity', u'dagNode', u'shape', u'geometryShape', u'locator', u'THlocatorShape', u'aiSkyDomeLight']
        # note the repeat - we will try to fix lineages like this, resolving to:
        # [u'containerBase', u'entity', u'dagNode', u'shape', u'geometryShape', u'locator', u'THlocatorShape', u'SphereLocator', u'aiSkyDomeLight']

        # first pop the rightmost element, which is the mayaType...
        if lineage.pop() != mayaType:
            raise RuntimeError("lineage for %s did not end with it's own node type" % mayaType)

        # then try to find the first element somewhere else - this should indicate the start of the repeated chain...
        try:
            nextIndex = lineage.index(lineage[0], 1)
        except ValueError:
            # unknown case, don't know how to fix...
            pass
        else:
            firstLineage = lineage[:nextIndex]
            secondLineage = lineage[nextIndex:]
            if len(firstLineage) < len(secondLineage):
                shorter = firstLineage
                longer = secondLineage
            else:
                shorter = secondLineage
                longer = firstLineage
            if longer[:len(shorter)] == shorter:
                # yay! we know how to fix!
                lineage = longer
                lineage.append(mayaType)

    if updateCache and lineage:
        if len(set(lineage)) != len(lineage):
            # cyclical lineage:  first discovered with xgen nodes.
            # might be a result of multiple inheritance being returned strangely by nodeType.
            print(mayaType, lineage)
            _logger.raiseLog(_logger.WARNING, "lineage for node %s is cyclical: %s" % (mayaType, lineage))
            _cachedInheritances[mayaType] = lineage
            # don't cache any of the parents
            return lineage
        # add not just this lineage, but all parent's lineages as well...
        for i in range(len(lineage), 0, -1):
            thisLineage = lineage[:i]
            thisNode = thisLineage[-1]
            oldVal = _cachedInheritances.get(thisNode)
            if oldVal is None:
                _cachedInheritances[thisNode] = thisLineage
            elif oldVal != thisLineage:
                _logger.raiseLog(_logger.WARNING, "lineage for node %s changed:\n  from %s\n  to   %s)" % (thisNode, oldVal, thisLineage))
                _cachedInheritances[thisNode] = thisLineage
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
    'base': '',
    'abstract': '',
    'node': '',
    'shape': '',
    'mod(?!(ify|ifier))': 'modify',
    'mod(?!(ify|ifier))': 'modifier',
    'modifier': 'mod',
    'modify': 'mod',
    'poly(?!gon)': 'polygon',
    'polygon': 'poly',
    'vert(?!(ex|ice))': 'vertex',
    'vert(?!(ex|ice))': 'vertice',
    'vertice': 'vert',
    'vertex': 'vert',
    'subd(?!iv)': 'subdiv',
    'subd(?!iv)': 'subdivision',
    'subdiv(?!ision)': 'subd',
    'subdiv(?!ision)': 'subdivision',
    'subdivision': 'subd',
    'subdivision': 'subdiv',
    '^th(custom)?': 'plugin',
}
API_NAME_MODIFIERS = [(re.compile(find), replace)
                      for find, replace in API_NAME_MODIFIERS.items()]

apiSuffixes = ['', 'node', 'shape', 'shapenode']

#===============================================================================
# Cache classes
#===============================================================================


class BaseApiClassInfoCache(startup.SubItemCache):
    CLASSINFO_SUBCACHE_NAME = None

    def _modifyEnums(self, data, predicate, converter):
        '''Convert between Enum reprs and actual Enum objects'''
        apiClassInfo = data[self.itemIndex(self.CLASSINFO_SUBCACHE_NAME)]
        for classname, classInfo in apiClassInfo.items():
            enums = classInfo.get('enums')
            if enums:
                for enumdata in enums.values():
                    valdata = enumdata.get('values')
                    if predicate(valdata):
                        enumdata['values'] = converter(valdata)
            pymelEnums = classInfo.get('pymelEnums')
            if pymelEnums:
                for name, enumdata in pymelEnums.items():
                    if predicate(enumdata):
                        pymelEnums[name] = converter(enumdata)

    def _modifyApiEnums(self, data, predicate, converter):
        apiClassInfo = data[self.itemIndex(self.CLASSINFO_SUBCACHE_NAME)]
        for classname, classInfo in apiClassInfo.items():
            methods = classInfo.get('methods')
            if not methods:
                continue
            for overrides in methods.values():
                # if we have ApiCache.apiClassInfo, overrides will be a list,
                # but if we have ApiMelBridgeCache.apiClassOverrides, it will
                # be a dict (whose keys are indices into that list)
                if isinstance(overrides, dict):
                    methodInfos = overrides.values()
                else:
                    methodInfos = overrides
                for methodInfo in methodInfos:
                    returnInfo = methodInfo.get('returnInfo')
                    if returnInfo:
                        returnType = returnInfo.get('type')
                        if returnType and predicate(returnType):
                            returnInfo['type'] = converter(returnType)
                    returnType = methodInfo.get('returnType')
                    if returnType and predicate(returnType):
                        methodInfo['returnType'] = converter(returnType)
                    argInfo = methodInfo.get('argInfo')
                    if argInfo:
                        for singleArgInfo in argInfo.values():
                            argType = singleArgInfo.get('type')
                            if argType and predicate(argType):
                                singleArgInfo['type'] = converter(argType)
                    args = methodInfo.get('args')
                    if args:
                        # args may be list or dict, depending on which cache
                        if isinstance(args, dict):
                            iteritems = args.items()
                        else:
                            iteritems = enumerate(args)
                        for i, arg in iteritems:
                            if predicate(arg[1]):
                                arg = list(arg)
                                arg[1] = converter(arg[1])
                                args[i] = tuple(arg)
                    defaults = methodInfo.get('defaults')
                    if defaults:
                        for name, val in defaults.items():
                            if predicate(val):
                                defaults[name] = converter(val)
                    types = methodInfo.get('types')
                    if types:
                        for name, val in types.items():
                            if predicate(val):
                                types[name] = converter(val)

    def fromRawData(self, data):
        # Note that if we're doing "eval", we could just add Enum / ApiEnum to
        # the locals dict... however, seems good practice to serialize /
        # deserialize to basic types, and keeps the option open of going to a
        # more generic format (ie, json)

        # convert from string enum reprs to Enum objects
        def makeEnumFromRepr(enumRepr):
            return eval(enumRepr, {'Enum': _util.Enum})

        self._modifyEnums(data, lambda x: isinstance(x, basestring),
                          makeEnumFromRepr)

        # convert from tuples to ApiEnum tuples
        self._modifyApiEnums(data, lambda x: isinstance(x, tuple),
                             ApiEnum)
        return data

    def toRawData(self, data):
        # convert from Enum objects to string enum reprs
        self._modifyEnums(data, lambda x: isinstance(x, _util.Enum), repr)

        # convert from ApiEnum tuples to tuples
        self._modifyApiEnums(data, lambda x: isinstance(x, ApiEnum),
                             tuple)
        return super(BaseApiClassInfoCache, self).toRawData(data)


class ApiMelBridgeCache(BaseApiClassInfoCache):
    NAME = 'mayaApiMelBridge'
    DESC = 'the API-MEL bridge'
    USE_VERSION = False
    _CACHE_NAMES = '''apiToMelData apiClassOverrides'''.split()
    CLASSINFO_SUBCACHE_NAME = 'apiClassOverrides'

    def rebuild(self):
        raise RuntimeError("should never need to rebuild the {} cache"
                           .format(self.NAME))

    @classmethod
    def stripComments(cls, sourcelines):
        '''Returns the text of the input python source lines with no comments,
        or None if the source did not have any comments

        sourcelines should have trailing newlines, ie, as returned by readlines
        '''
        import tokenize

        if isinstance(sourcelines, basestring):
            if not sourcelines:
                sourcelines = []
            else:
                sourcelines = sourcelines.split('\n')
                sourcelines = [x + '\n' for x in sourcelines]
                sourcelines[-1] = sourcelines[-1][:-1]

        def isNewline(tok):
            return tok[0] in (tokenize.NL, tokenize.NEWLINE)

        nonComments = []
        linesRemoved = 0
        foundComments = False
        stripNewlines = False
        for tok in tokenize.generate_tokens(iter(sourcelines).__next__):
            if tok[0] == tokenize.COMMENT:
                foundComments = True
                # if the comment was the only thing on the line - ie, it wasn't
                # an inline comment - we also strip all empty lines before and after

                # first, check to see if the last token was a newline - this is
                # how we check if it was an inline comment...
                if not nonComments or isNewline(nonComments[-1]):
                    # ok, now strip the empty lines before...
                    # note that we still want to leave in ONE newline before, since
                    # we will strip newlines after!
                    while len(nonComments) > 1 and isNewline(nonComments[-2]):
                        linesRemoved += 1
                        nonComments.pop()
                    # then mark that we're stripping newlines, so we can filter
                    # the ones after...
                    stripNewlines = True
            elif stripNewlines and isNewline(tok):
                # skip the next newline(s) after a comment, if that was the only
                # thing on the line
                linesRemoved += 1
            else:
                stripNewlines = False
                # correct the token for the removed newlines, or else untokenize will
                # insert empty lines
                nonComments.append((
                    # token type
                    tok[0],
                    # token text
                    tok[1],
                    # token start row/col
                    (tok[2][0] - linesRemoved, tok[2][1]),
                    # token end row/col
                    (tok[3][0] - linesRemoved, tok[3][1]),
                    # line tok was in
                    tok[4],
                ))

        if foundComments:
            return tokenize.untokenize(nonComments)

    @classmethod
    def applyComments(cls, origText, origTextNoComments, newPath):
        import subprocess

        newPath = os.path.normpath(os.path.abspath(newPath))

        def readcache():
            with open(newPath, 'rb') as f:
                return f.read()

        def writecache(text):
            with open(newPath, 'wb') as f:
                f.write(text)

        # read the current state of newPath to get the updated text
        newText = readcache()
        if newText == origText:
            # nothing was changed, we can quit
            print("No changes made to {} - no need to apply comments".format(
                cls.NAME))
            return

        # we assume user has git installed, and this source file is part of a
        # git repo, as it simplifies things (ie, no diff tools on windows)
        # this should be fine, as ApiMelBridgeCache.write() / .save() should
        # only ever be invoked manually, since rebuild() is overridden to error

        thisFile = inspect.getsourcefile(cls)
        pymelRoot = os.path.dirname(os.path.dirname(os.path.dirname(thisFile)))

        # in case of error, and in case origText was NOT committed, write it
        # out to disk
        origTextPath = newPath + '.orig'
        with open(origTextPath, 'wb') as f:
            f.write(origText)

        def git(arg, output=False):
            if isinstance(arg, basestring):
                args = arg.split()
            else:
                args = arg
            if output:
                def func(*args, **kwargs):
                    kwargs['stderr'] = subprocess.STDOUT
                    return subprocess.check_output(*args, **kwargs)
            else:
                func = subprocess.check_call
            # on Windows, at least, when git is run from subprocess inside of
            # maya, it's unable to access the user's .gitconfig for some reason
            # Not too big of a deal, since these shouldn't be "permanent"
            # commits, so we just hard code some settings
            args = [
                'git',
                '-c', 'core.autocrlf=false',
                '-c', 'user.name=pymel',
                '-c', 'user.email=pymel@noexist',
            ] + list(args)
            # print '{}({!r}, cwd={!r})'.format(func.__name__, args, pymelRoot)
            return func(args, cwd=pymelRoot)

        def gitout(arg):
            return git(arg, output=True).rstrip()

        def commitcache(text, message):
            writecache(text)
            git(['add', newPath])
            git(['commit', '-m', message])

        # verify we have git accessible
        try:
            git('--version')
        except subprocess.CalledProcessError:
            raise RuntimeError("Cannot save {} cache and preserve comments - no"
                               "git installed / accessible on executable path"
                               .format(cls.NAME))

        # make sure the file is tracked by git
        output = gitout(['ls-files', '--', newPath])
        if not output:
            # file was not tracked - error
            raise RuntimeError("File did not seem to be tracked by git -"
                               " cannot revert comments: {}".format(newPath))

        # make sure that the user hasn't already added files to commit to the
        # git index with "git add" - outstanding untracked changes are fine,
        # just not things in the index.,
        try:
            git('diff-index --quiet --cached HEAD')
        except subprocess.CalledProcessError:
            raise RuntimeError("Outstanding changes were added to the git"
                               " index - commit or revert these before"
                               " continuing")

        # we'll be making commits, so we'll need our own temp branches
        COMMENT_APPLY_BRANCH = 'pymel_cache_temp_comment_apply'
        CACHE_CHANGES_BRANCH = 'pymel_cache_temp_new_changes'
        TEMP_BRANCHES = [COMMENT_APPLY_BRANCH, CACHE_CHANGES_BRANCH]
        for tempBranch in TEMP_BRANCHES:
            try:
                gitout(['rev-parse', '--verify', '--quiet', tempBranch])
            except subprocess.CalledProcessError:
                pass
            else:
                # The branch already exists, abort
                raise RuntimeError("The temp branch already exists - remove it "
                                   " before continuing: {}".format(tempBranch))

        oldBranch = gitout('rev-parse --abbrev-ref HEAD')
        git(['checkout', '-b', COMMENT_APPLY_BRANCH])

        # revert cache first, then commit origText if different... technically,
        # we could skip this step, and go straight for committing of
        # origNoComment, but this will make history slightly clearer if
        # something goes wrong
        git(['checkout', '-f', oldBranch, '--', newPath])
        revertedText = readcache()
        if revertedText != origText:
            commitcache(origText,
                 "writing uncomitted state before {} cache was re-written"
                        .format(cls.NAME))

        # ok, now commit the no-comment state, since this is the common
        # "merge-base"
        commitcache(origTextNoComments,
                    "commit no-comment cache to serve as common merge-base")

        git(['branch', CACHE_CHANGES_BRANCH])

        # now commit the with-comment state
        commitcache(origText, "re-add the comments")

        # ok, swap to different branch, and commit the new state
        git(['checkout', CACHE_CHANGES_BRANCH])
        commitcache(newText, "new changes, without comments")

        # finally, merge in the comments
        try:
            output = gitout(['merge', COMMENT_APPLY_BRANCH,
                             '-m', "merge in comments"])
        except subprocess.CalledProcessError as e:
            print('!' * 80)
            print(e)
            print(e.output)
            print("Error during merge - run the following to resolve the")
            print("merge conflict manually with mergetool, then commit the")
            print("result, and finally clean up your repo:")
            print()
            print("git mergetool")
            print('git commit -m "merge in comments"')
            print("git checkout {}".format(oldBranch))
            print('git checkout {} -- "{}"'.format(CACHE_CHANGES_BRANCH, newPath))
            print("git branch -D {}".format(' '.join(TEMP_BRANCHES)))
            return

        # since everything worked, do some cleanup!
        with open(newPath, 'rb') as f:
            newTextWithComments = f.read()
        # if we don't explicitly checkout the cache path from the oldBranch
        # first, we will get an error when we do "git checkout oldBranch"
        # We don't want to use "-f" in case there are outstanding changes to
        # other files!
        git(['checkout', oldBranch, '--', newPath])
        git(['checkout', oldBranch])
        # now write back our changes
        with open(newPath, 'wb') as f:
            f.write(newTextWithComments)
        os.remove(origTextPath)
        for tempBranch in TEMP_BRANCHES:
            git(['branch', '-D', tempBranch])

    # override write to preserve comments
    def write(self, data, ext=None):
        if ext is None:
            ext = self.DEFAULT_EXT

        def isPyPath(path):
            return os.path.splitext(self._lastReadPath)[1] == '.py'

        noComments = None
        if ext == '.py' and os.path.splitext(self._lastReadPath)[1] == '.py':
            # we last read .py, and we're writing .py... check for comments
            with open(self._lastReadPath, 'rb') as f:
                origLines = f.readlines()
            noComments = self.stripComments(origLines)

        super(ApiMelBridgeCache, self).write(data, ext=ext)

        if noComments is None:
            print("original {} had no comments, no need to strip".format(self.NAME))
        else:
            # if we had comments, try to apply them now
            self.applyComments(''.join(origLines), noComments,
                               self._lastWritePath)


class ApiCache(BaseApiClassInfoCache):
    NAME = 'mayaApi'
    DESC = 'the API cache'
    USE_VERSION = True
    _CACHE_NAMES = '''apiTypesToApiEnums apiEnumsToApiTypes mayaTypesToApiTypes
                   apiTypesToApiClasses apiClassInfo'''.split()
    CLASSINFO_SUBCACHE_NAME = 'apiClassInfo'

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
        'xformManip': 'kXformManip',
        'moveVertexManip': 'kMoveVertexManip',
    }

    # hold any overrides for mayaTypesToApiTypes...
    # ie, for cases where the name guess is wrong, or for weird plugin types
    # that don't inherit from an mpx type (ie, vectorRenderGlobals), etc
    MAYA_TO_API_OVERRIDES = {
        # this what is returned by
        # allNodeTypes(includeAbstract=True)
        'node': 'kDependencyNode',

        # this is the name pymel uses
        'dependNode': 'kDependencyNode',

        # a strange one - a plugin node that has an
        # apitype... is in studioImport.so... also has a
        # doc entry...
        'smear': 'kSmear',

        # plugin node that's not in all distributions
        # (ie, it's missing in Linux), so just include it
        # here
        'vectorRenderGlobals': 'kDependencyNode',
    }

    # Sometimes, the results of doing MFnType.type() are "wrong", or, at the
    # very least, inappropriate for determining which maya node types are
    # compatible with which MFn classes.
    # As an example, MFnContainerNode().type() will return MFn.kContainerBase;
    # however, kContainerBase clearly corresponds to the containerBase maya
    # type, which is the base type for entity, which in turn is the base for
    # dagNode and objectSet.  This would imply that ANY dag node or object set
    # should be compatible with MFnContainerNode, but that is not the case -
    # only container nodes are.  So we "fix" that here.
    MFN_TO_API_OVERRIDES = {
        api.MFnContainerNode: api.MFn.kContainer,
    }

    # TODO: if hikHandle bug ever fixed:
    #   - remove entry in apiCache.ApiCache.API_TO_MFN_OVERRIDES
    #   - remove hard-code setting of HikHandle's parent to Transform

    # TODO: if jointFfd bug ever fixed:
    #   - remove entry in apiCache.ApiCache.API_TO_MFN_OVERRIDES
    #   - remove hard-code setting of JointFfd's parent to DependNode

    API_TO_MFN_OVERRIDES = {
        'kHikHandle': api.MFnTransform,  # hikHandle inherits from ikHandle, but is not compatible with MFnIkHandle
        'kFfdDualBase': api.MFnDependencyNode,  # jointFfd inherits from ffd, but is not compatible with MFnGeometryFilter
    }

    DEFAULT_API_TYPE = 'kDependencyNode'

    @classmethod
    def allVersions(cls, allowEmpty=False):
        return [x for x in super(ApiCache, cls).allVersions(allowEmpty=allowEmpty)
                if x != 'MelBridge']

    def __init__(self, docLocation=None, strict=None):
        super(ApiCache, self).__init__()
        for name in self.EXTRA_GLOBAL_NAMES:
            setattr(self, name, {})
        self.docLocation = docLocation
        if strict is None:
            strict = _plogging.errorLevel() <= _plogging.WARNING
        self.strict = strict

    def _modifyApiTypes(self, data, predicate, converter):
        '''convert apiTypesToApiClasses between class names and class objects'''
        enumsToTypes = data[self.itemIndex('apiTypesToApiClasses')]
        for key, val in enumsToTypes.items():
            if predicate(val):
                enumsToTypes[key] = converter(val)


    def fromRawData(self, data):
        # convert from string class names to class objects
        self._modifyApiTypes(data, lambda x: isinstance(x, basestring),
                             startup.getImportableObject)

        # json automatically converts integer dict keys to strings...
        # we only need to undo this on read
        apiEnumsToApiTypes = data[self.itemIndex('apiEnumsToApiTypes')]
        if any(isinstance(k, basestring) for k in apiEnumsToApiTypes):
            # want to modify the dict in place, so make a copy
            newDict = {int(key): val
                       for key, val in apiEnumsToApiTypes.items()}
            apiEnumsToApiTypes.clear()
            apiEnumsToApiTypes.update(newDict)

        return super(ApiCache, self).fromRawData(data)

    def toRawData(self, data):
        # convert from class objects to string class names
        self._modifyApiTypes(data, inspect.isclass, startup.getImportableName)
        return super(ApiCache, self).toRawData(data)

    def _buildMayaToApiInfo(self, reservedOnly=False):

        self._buildMayaNodeInfo()
        # Fixes for types that don't have a MFn by doing a node creation and testing it
        unknownTypes = set()
        toCreate = []

        self.mayaTypesToApiTypes = self._buildMayaReservedTypes()

        # do real nodes first - on pre-2012, can't directly query inheritance of
        # abstract nodes, so relying on caching of parent hierarchies when
        # querying a real hierarchy is the only way to get inheritance info
        # for abstract types
        if not reservedOnly:
            for mayaType in itertools.chain(self.realMayaTypes,
                                            self.abstractMayaTypes):
                if mayaType not in self.mayaTypesToApiTypes:
                    toCreate.append(mayaType)

        if toCreate:
            # Put in a debug, because ghost nodes can be problematic...
            _logger.debug("Starting to create ghost nodes...")

            with GhostObjsOkHere():
                with _GhostObjMaker(toCreate, manipError=False, multi=True) as typeToObj:
                    for mayaType in toCreate:
                        obj = typeToObj[mayaType]
                        if obj:
                            apiType = obj.apiTypeStr()
                            self.mayaTypesToApiTypes[mayaType] = apiType
                        else:
                            unknownTypes.add(mayaType)
            # Put in a debug, because ghost nodes can be problematic...
            _logger.debug("...finished creating ghost nodes")

        if len(unknownTypes) > 0:
            for mayaType in unknownTypes:
                # For unknown types, use the parent type
                try:
                    inheritance = getInheritance(mayaType)
                except (ManipNodeTypeError, RuntimeError):
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

        self.filterPluginNodes()

        for mayaType, apiType in self.mayaTypesToApiTypes.items():
            self.addMayaType(mayaType, apiType)

    def _buildApiTypesList(self):
        """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with
        an existing api type"""

        self.apiTypesToApiEnums = dict(inspect.getmembers(api.MFn, lambda x: type(x) is int))
        self.apiEnumsToApiTypes = dict((self.apiTypesToApiEnums[k], k) for k in self.apiTypesToApiEnums.keys())

    def _fixApiEnumsToApiTypes(self):
        # For the MFn.Type mappings, we can have multiple string names mapping
        # to the same enum int value, and we need to determine which name is
        # the "default" when building the mapping from int to string.

        # We use the information parsed from the docs, for api.MFn.Type, to
        # pick a default - the first entry defined is the default
        numToNames = {}
        for name, num in self.apiTypesToApiEnums.items():
            numToNames.setdefault(num, []).append(name)
        mfnTypeEnum = self.apiClassInfo['MFn']['enums']['Type']['values']
        for num, names in numToNames.items():
            if len(names) <= 1:
                continue
            defaultName = mfnTypeEnum[num].key
            assert defaultName in names
            self.apiEnumsToApiTypes[num] = defaultName

    def _buildMayaReservedTypes(self):
        """
        Build a list of Maya reserved types.

        These cannot be created directly from the API, thus the dgMod trick to
        find the corresponding Maya type won't work
        """
        reservedMayaTypes = {}

        # start with plugin types
        import pymel.api.plugins as plugins
        for mayaNode, mpxName in plugins.mayaNodesToMpxNames.items():
            reservedMayaTypes[mayaNode] = plugins.mpxNamesToApiEnumNames[mpxName]

        for mayaType in self.abstractMayaTypes:
            if mayaType in reservedMayaTypes:
                continue
            apiGuess = self._guessApiTypeByName(mayaType)
            if apiGuess:
                reservedMayaTypes[mayaType] = apiGuess

        reservedMayaTypes.update(self.MAYA_TO_API_OVERRIDES)
        reservedMayaTypes.update(self.CRASH_TYPES)
        # filter to make sure all these types exist in current version (some are Maya2008 only)
        reservedMayaTypes = dict((item[0], item[1])
                                 for item in reservedMayaTypes.items()
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

        self.realMayaTypes, self.abstractMayaTypes = _getAllMayaTypes(returnRealAbstract=True)
        self.allMayaTypes = self.realMayaTypes | self.abstractMayaTypes

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
        for modifyNum in range(len(possibleModifications) + 1):
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
        for strSize in range(maxSize, 0, -1):
            for startPos in range(0, maxSize - strSize + 1):
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
        parser = ApiDocParser(api, enumClass=ApiEnum,
                              docLocation=self.docLocation, strict=self.strict)

        for name, obj in inspect.getmembers(api, lambda x: type(x) == type and x.__name__.startswith('M')):
            if parser.shouldSkip(name):
                continue
            try:
                info = parser.parse(name)
                if not isinstance(info, dict):
                    raise RuntimeError("ApiDocParser.parse must return a dict")
                self.apiClassInfo[name] = info
            except (IOError, OSError, ValueError, IndexError) as e:
                import errno
                baseMsg = "failed to parse docs for %r:" % name
                if isinstance(e, (IOError, OSError)) and e.errno == errno.ENOENT:
                    # If we couldn't parse because we couldn't find the
                    # file, only raise a warning... there are many classes
                    # (ie, MClothTriangle) that don't have a doc page...
                    _logger.warning(baseMsg)
                    _logger.warning("%s: %s" % (name, e))
                else:
                    if self.strict:
                        raise
                    import traceback
                    _logger.error(baseMsg)
                    _logger.error(traceback.format_exc())

        _logger.debug("...finished ApiCache._buildApiClassInfo")

    def getMfnClsToApiEnum(self, mfnCls):
        if mfnCls == api.MFnBase:
            return api.MFn.kBase  # 1
        else:
            enumInt = self.MFN_TO_API_OVERRIDES.get(mfnCls)
            if enumInt is None:
                enumInt = mfnCls().type()
            return enumInt

    def getApiEnumToApiType(self, enumInt):
        return self.apiEnumsToApiTypes.get(enumInt,
                                           # 'kInvalid'
                                           self.apiEnumsToApiTypes[0])

    def getMfnClsToApiType(self, mfnCls):
        return self.getApiEnumToApiType(self.getMfnClsToApiEnum(mfnCls))

    def _buildApiTypeToApiClasses(self):
        self.apiTypesToApiClasses = {}

        # all of maya OpenMaya api is now imported in module api's namespace
        mfnClasses = inspect.getmembers(api, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
        for name, mfnClass in mfnClasses:
            current = self.getMfnClsToApiType(mfnClass)
            if not current:
                _logger.warning("MFnClass gave MFnType %s" % current)
            elif current == 'kInvalid':
                _logger.warning("MFnClass gave MFnType %s" % current)
            else:
                self.apiTypesToApiClasses[current] = mfnClass
        # we got our map by going from Mfn to enum; however, multiple enums can
        # map to the same MFn, so need to fill in the gaps of missing enums for
        # enums to MFn...

        # we do this by querying the maya hierarchy, and marching up it until
        # we find an entry that IS in apiTypesToApiClasses
        for mayaType, apiType in self.mayaTypesToApiTypes.items():
            if apiType not in self.apiTypesToApiClasses:
                self._getOrSetApiClass(apiType, mayaType)

    def _getOrSetApiClass(self, apiType, mayaType):
        if apiType not in self.apiTypesToApiClasses:
            if apiType in self.API_TO_MFN_OVERRIDES:
                mfnClass = self.API_TO_MFN_OVERRIDES[apiType]
            else:
                mfnClass = self._getApiClassFromMayaInheritance(apiType, mayaType)
            self.apiTypesToApiClasses[apiType] = mfnClass
        return self.apiTypesToApiClasses[apiType]

    def _getApiClassFromMayaInheritance(self, apiType, mayaType):
        mfnClass = None
        try:
            inheritance = getInheritance(mayaType)
        except Exception:
            pass
        else:
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
        return mfnClass

    def _buildApiRelationships(self):
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
        import maya.mel
        maya.mel.eval('source "initialPlugins.mel"')

        # Note that even though we later call filterPluginNodes, which will
        # remove most of the info for plugin nodes, we still load all plugins
        # before building the cache.  This is because some "core" maya api types
        # (ie, node types that have a corresponding kSomeType entry on MFn,
        # and possibly even an MFnSomeType) are actually implemented in plugin
        # nodes, and we need to make sure we grab all of these.

        # However... bifrost takes a long time to load, and can significantly
        # slow cache building... and doesn't seem to have any affect on the
        # built caches. Add a way to skip it when testing.
        if os.environ.get('PYMEL_SKIP_BIFROST_AT_APICACHE_BUILD'):
            filters = ['bifmeshio', 'Boss', re.compile(r'bifrost.*')]
        else:
            filters = []
        plugins.loadAllMayaPlugins(filters=filters)

        self._buildApiClassInfo()
        self._fixApiEnumsToApiTypes()

        self._buildMayaToApiInfo(reservedOnly=False)
        self._buildApiTypeToApiClasses()

        _logger.debug("...finished ApiCache._buildApiTypeHierarchy")

    def addMayaType(self, mayaType, apiType, updateObj=None):
        """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums

        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """
        if apiType is None:
            # Check is here because formerly apiType was a kwarg with default
            # value of None
            raise ValueError("apiType must be given!")

        if apiType is not 'kInvalid':
            apiEnum = getattr(api.MFn, apiType)
            self.mayaTypesToApiTypes[mayaType] = apiType
            self.mayaTypesToApiEnums[mayaType] = apiEnum

    def removeMayaType(self, mayaType, updateObj=None):
        """ Remove a type from the MayaTypes lists.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums

        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """
        self.mayaTypesToApiEnums.pop(mayaType, None)
        self.mayaTypesToApiTypes.pop(mayaType, None)

    def mayaTypeToApiType(self, mayaType, useCache=True, ghostObjs=True):
        # type: (str, bool) -> str
        """
        Get the Maya API type from the name of a Maya type

        Parameters
        ----------
        mayaType : str
        useCache : bool

        Returns
        -------
        str
        """
        if useCache:
            apiType = self.mayaTypesToApiTypes.get(mayaType)
            if apiType:
                return apiType

        apiType = None
        import pymel.api.plugins as plugins
        try:
            inheritance = getInheritance(mayaType, checkManip3D=False)
        except Exception:
            inheritance = None
        if inheritance:
            for parentMayaType in reversed(inheritance[:-1]):
                apiType = self.mayaTypesToApiTypes.get(parentMayaType)
                if apiType:
                    break

        if not apiType:
            apiType = 'kInvalid'
            # we need to actually create the obj to query it...
            if ghostObjs:
                with _GhostObjMaker(mayaType) as obj:
                    if obj is not None and api.isValidMObject(obj):
                        apiType = obj.apiTypeStr()
        if useCache:
            self.mayaTypesToApiTypes[mayaType] = apiType
        return apiType

    def filterPluginNodes(self):
        '''Remove most plugin nodes from mayaTypesToApiTypes

        When building the cache, filter out most plugin nodes - these are
        easily queried dynamically when the plugin loads, and they just
        create bloat / noise in the caches.  However, we want to retain
        plugin nodes in two cases:
        - they map to an MFn enum other than one of the standard kPlugin*
          types - ie, some "core" maya types are actually implemented in
          plugins
        - their type can't be queried correctly without creating them
        '''
        toRemove = []
        for mayaType, apiType in self.mayaTypesToApiTypes.items():
            if not apiType.startswith('kPlugin') or apiType == 'kPlugin':
                continue
            # don't remove the maya types for the kPlugin* themselves - ie,
            # THdependNode == kPluginNode
            # Also, THmanip and THmanipContainer aren't actually even nodes -
            # ignore them too
            if mayaType in self.abstractMayaTypes \
                    or mayaType not in self.allMayaTypes:
                continue
            # ok, now query the type
            calcApiType = self.mayaTypeToApiType(mayaType, useCache=False,
                                                 ghostObjs=False)
            if calcApiType != apiType:
                _logger.raiseLog(_logger.WARNING,
                    "could not determine apiType for plugin node '{}' without"
                    " creating it (cached apiType: {} - determined type: {})"
                    .format(mayaType, apiType, calcApiType))
            else:
                toRemove.append(mayaType)
        for mayaType in toRemove:
            del self.mayaTypesToApiTypes[mayaType]

    def rebuild(self):
        """Rebuild the api cache from scratch

        Unlike 'build', this does not attempt to load a cache file, but always
        rebuilds it by parsing the docs, etc.
        """
        _logger.info("Rebuilding the API Caches...")

        # fill out the data structures
        self._buildApiTypesList()
        #_buildMayaTypesList()

        self._buildApiRelationships()

        # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
        _logger.info('merging in dictionary of manual api overrides')
        self._mergeClassOverrides()

    def _mergeClassOverrides(self, bridgeCache=None):
        if bridgeCache is None:
            bridgeCache = ApiMelBridgeCache()
            bridgeCache.build()
        _util.mergeCascadingDicts(bridgeCache.apiClassOverrides, self.apiClassInfo, allowDictToListMerging=True)

    def melBridgeContents(self):
        return self._mayaApiMelBridge.contents()

    def extraDicts(self):
        return tuple(getattr(self, x) for x in self.EXTRA_GLOBAL_NAMES)

"""
Functions which are not listed in the maya documentation, such as commands created by plugins,
as well as the name parsing classes `DependNodeName`, `DagNodeName`, and `AttributeName`.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future.utils import PY2

from builtins import str
import re
import inspect

import pymel.internal.factories as _factories
if False:
    from typing import *
    from maya import cmds

    NameParserT = TypeVar('NameParserT', bound=NameParser)
    DependNodeNameT = TypeVar('DependNodeNameT', bound=DependNodeName)
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]



# -------------------------
# Object Wrapper Classes
# -------------------------

class NameParser(str):
    PARENT_SEP = '|'

    def __new__(cls, strObj):
        """
        Casts a string to a pymel class.

        Use this function if you are unsure which class is the right one to use
        for your object.
        """
        strObj = str(strObj)
        # the if statement was failing for some types (ex: pymel.node.Vertex),
        # so forcing into unicode string:
        if cls is not NameParser:
            newcls = cls
        else:
            newcls = _getParserClass(strObj)
        self = super(NameParser, cls).__new__(newcls, strObj)
        return self

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           super(NameParser, self).__repr__())

    def __getattr__(self, attr):
        """
            >>> NameParser('foo:bar').spangle
            AttributeName('foo:bar.spangle')

        """
        if attr.startswith('__') and attr.endswith('__'):
            return super(NameParser, self).__getattr__(attr)

        return AttributeName('%s.%s' % (self, attr))

        #raise AttributeNameError, 'AttributeName does not exist %s' % attr

    def stripNamespace(self, levels=0):
        # type: (NameParserT, int) -> NameParserT
        """
        Returns a new instance of the object with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.

            >>> NameParser('foo:bar.spangle').stripNamespace()
            AttributeName('bar.spangle')
        """

        nodes = []
        for dagElem in self.split('|'):
            attrSplit = dagElem.split('.')
            spaceSplit = attrSplit[0].split(':')
            if levels:
                attrSplit[0] = ':'.join(spaceSplit[min(len(spaceSplit) - 1, levels):])
            else:
                attrSplit[0] = spaceSplit[-1]
            nodes.append('.'.join(attrSplit))
        return self.__class__('|'.join(nodes))

    def stripGivenNamespace(self, namespace, partial=True):
        # type: (NameParserT, str, bool) -> NameParserT
        """
        Returns a new instance of the object with any occurrences of the given namespace removed.  The calling instance is unaffected.
        The given namespace may end with a ':', or not.
        If partial is True (the default), and the given namespace has parent namespaces (ie, 'one:two:three'),
        then any occurrences of any parent namespaces are also stripped - ie, 'one' and 'one:two' would
        also be stripped.  If it is false, only namespaces

            >>> NameParser('foo:bar:top|foo:middle|foo:bar:extra:guy.spangle').stripGivenNamespace('foo:bar')
            AttributeName('top|middle|extra:guy.spangle')

            >>> NameParser('foo:bar:top|foo:middle|foo:bar:extra:guy.spangle').stripGivenNamespace('foo:bar', partial=False)
            AttributeName('top|foo:middle|extra:guy.spangle')
        """
        prefixSplit = namespace.rstrip(':').split(':')

        nodes = []
        for dagElem in self.split('|'):
            attrSplit = dagElem.split('.')
            spaceSplit = attrSplit[0].split(':')
            if partial:
                for toStrip in prefixSplit:
                    if spaceSplit[0] == toStrip:
                        spaceSplit.pop(0)
                    else:
                        break
            else:
                if spaceSplit[:len(prefixSplit)] == prefixSplit:
                    spaceSplit = spaceSplit[len(prefixSplit):]
                attrSplit[0] = spaceSplit[-1]
            attrSplit[0] = ':'.join(spaceSplit)
            nodes.append('.'.join(attrSplit))
        return self.__class__('|'.join(nodes))

    def swapNamespace(self, prefix):
        # type: (NameParserT, str) -> NameParserT
        """
        Returns a new instance of the object with its current namespace
        replaced with the provided one.

        The calling instance is unaffected.
        """
        if not prefix.endswith(':'):
            prefix += ':'
        return self.__class__.addPrefix(self.stripNamespace(), prefix)

    def namespaceList(self):
        # type: () -> List[str]
        """
        Useful for cascading references.

        Returns all of the namespaces of the calling object as a list
        """
        return self.lstrip('|').rstrip('|').split('|')[-1].split(':')[:-1]

    def namespace(self):
        # type: () -> str
        """
        Returns the namespace of the object with trailing colon included
        """
        nsList = self.namespaceList()
        if nsList:
            return ':'.join(nsList) + ':'
        return ''

    def addPrefix(self, prefix):
        # type: (NameParserT, str) -> NameParserT
        'addPrefixToName'
        name = self
        leadingSlash = False
        if name.startswith('|'):
            name = name[1:]
            leadingSlash = True
        name = self.__class__('|'.join([prefix + x for x in name.split('|')]))
        if leadingSlash:
            name = '|' + name
        return self.__class__(name)

    def attr(self, attr):
        # type: (str) -> AttributeName
        """access to AttributeName of a node. returns an instance of the
        AttributeName class for the given AttributeName.

            >>> NameParser('foo:bar').attr('spangle')
            AttributeName('foo:bar.spangle')

        """
        return AttributeName('%s.%s' % (self, attr))


class AttributeName(NameParser):

    """

    """
    attrItemReg = re.compile(r'\[(\d+:*\d*)\]$')

    # def __repr__(self):
    #    return "AttributeName('%s')" % self

    def __init__(self, attrName):
        attrName = str(attrName)
        if '.' not in attrName:
            raise TypeError("%s: AttributeNames must include the node and the "
                            "AttributeName. e.g. "
                            "'nodeName.AttributeNameName' " % self)
        self.__dict__['_multiattrIndex'] = 0

    def __getitem__(self, item):
        return AttributeName('%s[%s]' % (self, item))

    # Added the __call__ so to generate a more appropriate exception when a class method is not found
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" %
                        (repr(self.node()), self.plugAttr()))

    def array(self):
        # type: () -> AttributeName
        """
        Returns the array (multi) AttributeName of the current element
            >>> n = AttributeName('lambert1.groupNodes[0]')
            >>> n.array()
            AttributeName('lambert1.groupNodes')
        """
        try:
            return AttributeName(AttributeName.attrItemReg.split(self)[0])
        except:
            raise TypeError("%s is not a multi AttributeName" % self)

    def plugNode(self):
        # type: () -> NameParser
        """plugNode

        >>> NameParser('foo:bar.spangle.banner').plugNode()
        DependNodeName('foo:bar')

        """
        return NameParser(str(self).split('.')[0])

    node = plugNode

    def plugAttr(self):
        # type: () -> str
        """plugAttr

        >>> NameParser('foo:bar.spangle.banner').plugAttr()
        'spangle.banner'

        """
        if PY2:
            # just to get this method returning a builtins.str object, like
            # nearly everything else here does...
            return str('.').join(str(self).split('.')[1:])
        return '.'.join(str(self).split('.')[1:])

    def lastPlugAttr(self):
        # type: () -> str
        """
        >>> NameParser('foo:bar.spangle.banner').lastPlugAttr()
        'banner'

        """
        return self.split('.')[-1]

    def nodeName(self):
        # type: () -> str
        'basename'
        return self.split('|')[-1]

    def item(self, asSlice=False, asString=False):
        try:
            item = AttributeName.attrItemReg.search(self).group(1)
            if asString:
                return "[%s]" % str(item)
            val = item.split(":")
            val = [int(x) for x in val]
            if len(val) > 1:
                return asSlice and slice(*val) or val
            return val[0]
        except:
            return None

    def getParent(self, generations=1):
        # type: (int) -> AttributeName
        """
        Returns the parent attribute

        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> AttributeName("Cube1.multiComp[3].child.otherchild").getParent(2)
                  AttributeName('Cube1.multiComp[3]')

              Negative values will traverse from the top, not counting the initial node name:

                  >>> AttributeName("Cube1.multiComp[3].child.otherchild").getParent(-2)
                  AttributeName('Cube1.multiComp[3].child')

              A value of 0 will return the same node.
              The default value is 1.

              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown).
        """

        if generations == 0:
            return self

        split = self.split('.')
        if -len(split) < generations < len(split) - 1:
            if generations < 0:
                # Move it one over to account for the initial node name
                splitIndex = 1 - generations
            else:
                splitIndex = -generations
            try:
                return AttributeName('.'.join(split[:splitIndex]))
            except:
                pass

    def addAttr(self, **kwargs):
        kwargs['longName'] = self.plugAttr()
        kwargs.pop('ln', None)
        from pymel.core.general import addAttr
        return addAttr(self.node(), **kwargs)

    def setAttr(self, *args, **kwargs):
        from pymel.core.general import setAttr
        return setAttr(self, *args, **kwargs)

    set = setAttr
    add = addAttr

    def exists(self):
        node = self.plugNode()
        attr = self.plugAttr()
        if not node or not attr:
            return False

        if not cmds.objExists(node):
            return False

        # short name
        if attr in cmds.listAttr(node, shortNames=1) + cmds.listAttr(node):
            return True

        return False


class DependNodeName(NameParser):
    # ------------------------------
    #    Name Info and Manipulation
    # ------------------------------

    def node(self):
        # type: (DependNodeNameT) -> DependNodeNameT
        """
        for compatibility with AttributeName class
        """
        return self

    def nodeName(self):
        # type: (DependNodeNameT) -> DependNodeNameT
        """
        for compatibility with DagNodeName class
        """
        return self

    def exists(self, **kwargs):
        "objExists"
        return bool(cmds.objExists(self, **kwargs))

    _numPartReg = re.compile('([0-9]+)$')

    def stripNum(self):
        # type: () -> str
        """
        Return the name of the node with trailing numbers stripped off.

        If no trailing numbers are found the name will be returned unchanged."""
        try:
            return DependNodeName._numPartReg.split(self)[0]
        except IndexError:
            return str(self)

    def extractNum(self):
        # type: () -> str
        """
        Return the trailing numbers of the node name.

        If no trailing numbers are found an error will be raised.
        """

        try:
            return DependNodeName._numPartReg.split(self)[1]
        except IndexError:
            raise ValueError("No trailing numbers to extract on "
                             "object %s" % self)

    def nextUniqueName(self):
        # type: (DependNodeNameT) -> DependNodeNameT
        """
        Increment the trailing number of the object until a unique name is found

        If there is no trailing number, appends '1' to the name.
        Will always return a different name than the current name, even if the
            current name already does not exist.
        """
        try:
            name = self.nextName()
        except ValueError:
            name = self.__class__(self + '1')
        while name.exists():
            name = name.nextName()
        return name

    def nextName(self):
        # type: (DependNodeNameT) -> DependNodeNameT
        """Increment the trailing number of the object by 1"""

        groups = DependNodeName._numPartReg.split(self)
        if len(groups) > 1:
            num = groups[1]
            formatStr = '%s%0' + str(len(num)) + 'd'
            return self.__class__(formatStr % (groups[0], (int(num) + 1)))
        else:
            raise ValueError("could not find trailing numbers to increment on "
                             "object %s" % self)

    def prevName(self):
        # type: (DependNodeNameT) -> DependNodeNameT
        """Decrement the trailing number of the object by 1"""
        groups = DependNodeName._numPartReg.split(self)
        if len(groups) > 1:
            num = groups[1]
            formatStr = '%s%0' + str(len(num)) + 'd'
            return self.__class__(formatStr % (groups[0], (int(num) - 1)))
        else:
            raise ValueError("could not find trailing numbers to decrement on "
                             "object %s" % self)


class DagNodeName(DependNodeName):

    #    def __eq__(self, other):
    #        """ensures that we compare longnames when checking for dag node equality"""
    #        try:
    #            return unicode(self.longName()) == unicode(DagNodeName(other).longName())
    #        except (TypeError,IndexError):
    #            return unicode(self) == unicode(other)
    #
    #    def __ne__(self, other):
    #        """ensures that we compare longnames when checking for dag node equality"""
    #        try:
    #            return unicode(self.longName()) != unicode(DagNodeName(other).longName())
    #        except (TypeError,IndexError):
    #            return unicode(self) != unicode(other)

    # -------------------------
    #    DagNodeName Path Info
    # -------------------------
    def root(self):
        # type: () -> DagNodeName
        """rootOf"""
        return DagNodeName('|' + self.longName()[1:].split('|')[0])

    def getRoot(self):
        # type: () -> DagNodeName
        """unlike the root command which determines the parent via string formatting, this
        command uses the listRelatives command"""

        par = None
        cur = self
        while 1:
            par = cur.getParent()
            if not par:
                break
            cur = par
        return cur

    def firstParent(self):
        # type: () -> DagNodeName
        """firstParentOf"""

        return DagNodeName('|'.join(self.split('|')[:-1]))

    def getParent(self, generations=1):
        # type: (int) -> DagNodeName
        """
        Returns the parent node

        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> DagNodeName("NS1:TopLevel|Next|ns2:Third|Fourth").getParent(2)
                  DagNodeName('NS1:TopLevel|Next')

              Negative values will traverse from the top, not counting the initial node name:

                  >>> DagNodeName("NS1:TopLevel|Next|ns2:Third|Fourth").getParent(-3)
                  DagNodeName('NS1:TopLevel|Next|ns2:Third')

              A value of 0 will return the same node.
              The default value is 1.

              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown).
        """

        if generations == 0:
            return self

        split = self.split('|')
        if -len(split) <= generations < len(split):
            try:
                return DagNodeName('|'.join(split[:-generations]))
            except:
                pass


#    def shortName( self ):
#        'shortNameOf'
#        try:
#            return self.__class__( cmds.ls( self )[0] )
#        except:
#            return self

    def nodeName(self):
        # type: () -> str
        """basename"""
        return self.split('|')[-1]


def _getParserClass(strObj):
    # First, see if strObj is actually a PyNode - in that case, get the class
    # based off the node...
    mro = set([cls.__name__ for cls in inspect.getmro(type(strObj))])
    # doing string comparison so we don't have to import core.general/nodetypes
    if 'PyNode' in mro:
        if 'DagNode' in mro:
            newcls = DagNodeName
        elif 'Attribute' in mro:
            newcls = AttributeName
        else:
            newcls = DependNodeName
    else:
        strObj = str(strObj)

        if '.' in strObj:
            newcls = AttributeName
            # Return Component Arrays ==========================================
            #            attr = obj.array().plugAttr()
            #            if attr in ["f","vtx","e","map"]:
            #                comps = getattr(Mesh(obj.node()), attr)
            #                return comps.__getitem__(obj.item(asSlice=1))
            #            else:
            #                return obj
            #===================================================================

        elif '|' in strObj:
            newcls = DagNodeName
        else:
            newcls = DependNodeName
    return newcls

# ------ Do not edit below this line --------

TanimLayer = _factories.getCmdFunc('TanimLayer')

TrenderSetupStates = _factories.getCmdFunc('TrenderSetupStates')

adpAnalyticsDialog = _factories.getCmdFunc('adpAnalyticsDialog')

adskAsset = _factories.getCmdFunc('adskAsset')

adskAssetLibrary = _factories.getCmdFunc('adskAssetLibrary')

adskAssetList = _factories.getCmdFunc('adskAssetList')

@_factories.addCmdDocs
def adskAssetListUI(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ('cms', 'commandSuffix', 'uiC', 'uiCommand'):
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.adskAssetListUI(*args, **kwargs)
    return res

agFormatIn = _factories.getCmdFunc('agFormatIn')

agFormatOut = _factories.getCmdFunc('agFormatOut')

artAttr = _factories.getCmdFunc('artAttr')

artAttrSkinPaint = _factories.getCmdFunc('artAttrSkinPaint')

artAttrSkinPaintCmd = _factories.getCmdFunc('artAttrSkinPaintCmd')

artFluidAttr = _factories.getCmdFunc('artFluidAttr')

artSelect = _factories.getCmdFunc('artSelect')

artSetPaint = _factories.getCmdFunc('artSetPaint')

attrCompatibility = _factories.getCmdFunc('attrCompatibility')

blend = _factories.getCmdFunc('blend')

caddyManip = _factories.getCmdFunc('caddyManip')

clearShear = _factories.getCmdFunc('clearShear')

copyNode = _factories.getCmdFunc('copyNode')

crashInfoCmd = _factories.getCmdFunc('crashInfoCmd')

dagCommandWrapper = _factories.getCmdFunc('dagCommandWrapper')

dagObjectHit = _factories.getCmdFunc('dagObjectHit')

debug = _factories.getCmdFunc('debug')

debugNamespace = _factories.getCmdFunc('debugNamespace')

debugVar = _factories.getCmdFunc('debugVar')

dgControl = _factories.getCmdFunc('dgControl')

dgPerformance = _factories.getCmdFunc('dgPerformance')

dgcontrol = _factories.getCmdFunc('dgcontrol')

dgdebug = _factories.getCmdFunc('dgdebug')

dgstats = _factories.getCmdFunc('dgstats')

directConnectPath = _factories.getCmdFunc('directConnectPath')

dispatchGenericCommand = _factories.getCmdFunc('dispatchGenericCommand')

dynTestData = _factories.getCmdFunc('dynTestData')

evalContinue = _factories.getCmdFunc('evalContinue')

evaluationManagerInternal = _factories.getCmdFunc('evaluationManagerInternal')

evaluatorInternal = _factories.getCmdFunc('evaluatorInternal')

extendFluid = _factories.getCmdFunc('extendFluid')

@_factories.addCmdDocs
def flagTest(*args, **kwargs):
    for flag in ('timeRange', 'tr'):
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.flagTest(*args, **kwargs)
    return res

flushIdleQueue = _factories.getCmdFunc('flushIdleQueue')

flushThumbnailCache = _factories.getCmdFunc('flushThumbnailCache')

greasePencil = _factories.getCmdFunc('greasePencil')

greasePencilHelper = _factories.getCmdFunc('greasePencilHelper')

greaseRenderPlane = _factories.getCmdFunc('greaseRenderPlane')

groupParts = _factories.getCmdFunc('groupParts')

hotkeyEditor = _factories.getCmdFunc('hotkeyEditor')

hotkeyMapSet = _factories.getCmdFunc('hotkeyMapSet')

@_factories.addCmdDocs
def imageWindowEditor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ('cc', 'changeCommand'):
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.imageWindowEditor(*args, **kwargs)
    return res

interactionStyle = _factories.getCmdFunc('interactionStyle')

iterOnNurbs = _factories.getCmdFunc('iterOnNurbs')

journal = _factories.getCmdFunc('journal')

licenseCheck = _factories.getCmdFunc('licenseCheck')

manipComponentPivot = _factories.getCmdFunc('manipComponentPivot')

manipComponentUpdate = _factories.getCmdFunc('manipComponentUpdate')

matrix = _factories.getCmdFunc('matrix')

mayaDpiSettingAction = _factories.getCmdFunc('mayaDpiSettingAction')

meshIntersectTest = _factories.getCmdFunc('meshIntersectTest')

mimicMnipulation = _factories.getCmdFunc('mimicMnipulation')

mouldMesh = _factories.getCmdFunc('mouldMesh')

mouldSrf = _factories.getCmdFunc('mouldSrf')

mouldSubdiv = _factories.getCmdFunc('mouldSubdiv')

movieCompressor = _factories.getCmdFunc('movieCompressor')

myTestCmd = _factories.getCmdFunc('myTestCmd')

nodeGrapher = _factories.getCmdFunc('nodeGrapher')

nop = _factories.getCmdFunc('nop')

nurbsCurveRebuildPref = _factories.getCmdFunc('nurbsCurveRebuildPref')

ogsdebug = _factories.getCmdFunc('ogsdebug')

paint3d = _factories.getCmdFunc('paint3d')

polyColorSetCmdWrapper = _factories.getCmdFunc('polyColorSetCmdWrapper')

polyIterOnPoly = _factories.getCmdFunc('polyIterOnPoly')

polyPrimitiveMisc = _factories.getCmdFunc('polyPrimitiveMisc')

polySelectEditCtxDataCmd = _factories.getCmdFunc('polySelectEditCtxDataCmd')

polySelectSp = _factories.getCmdFunc('polySelectSp')

polySetVertices = _factories.getCmdFunc('polySetVertices')

polySpinEdge = _factories.getCmdFunc('polySpinEdge')

polyTestPop = _factories.getCmdFunc('polyTestPop')

polyToCurve = _factories.getCmdFunc('polyToCurve')

polyUVStackSimilarShellsCmd = _factories.getCmdFunc('polyUVStackSimilarShellsCmd')

polyWarpImage = _factories.getCmdFunc('polyWarpImage')

psdConvSolidTxOptions = _factories.getCmdFunc('psdConvSolidTxOptions')

rampWidget = _factories.getCmdFunc('rampWidget')

rampWidgetAttrless = _factories.getCmdFunc('rampWidgetAttrless')

readPDC = _factories.getCmdFunc('readPDC')

@_factories.addCmdDocs
def repeatLast(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ('ac', 'acl', 'addCommand', 'addCommandLabel', 'cl', 'cnl', 'commandList', 'commandNameList'):
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.repeatLast(*args, **kwargs)
    return res

retimeHelper = _factories.getCmdFunc('retimeHelper')

safemodecheckhash = _factories.getCmdFunc('safemodecheckhash')

@_factories.addCmdDocs
def selectKeyframe(*args, **kwargs):
    for flag in ('t', 'time'):
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.selectKeyframe(*args, **kwargs)
    return res

subdDisplayMode = _factories.getCmdFunc('subdDisplayMode')

subdToNurbs = _factories.getCmdFunc('subdToNurbs')

subgraph = _factories.getCmdFunc('subgraph')

syncSculptCache = _factories.getCmdFunc('syncSculptCache')

testPa = _factories.getCmdFunc('testPa')

testPassContribution = _factories.getCmdFunc('testPassContribution')

texSculptCacheSync = _factories.getCmdFunc('texSculptCacheSync')

@_factories.addCmdDocs
def timeRangeInfo(*args, **kwargs):
    for flag in ('t', 'time'):
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.timeRangeInfo(*args, **kwargs)
    return res

timeSliderCustomDraw = _factories.getCmdFunc('timeSliderCustomDraw')

warnUserDialog = _factories.getCmdFunc('warnUserDialog')

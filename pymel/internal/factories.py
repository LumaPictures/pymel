"""
Contains the wrapping mechanisms that allows pymel to integrate the api and maya.cmds into a unified interface
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# Built-in imports
from builtins import zip
from builtins import range
from past.builtins import basestring
from builtins import object
from future.utils import with_metaclass
import re
import types
import os
import inspect
import sys
import textwrap
import time
import traceback

# Maya imports
import maya.cmds as cmds
import maya.mel as mm

# PyMEL imports
import pymel.api as api
import pymel.util as util
from pymel.util.conditions import Always, Condition
import pymel.versions as versions
from pymel.internal.pwarnings import deprecated, maya_deprecated

# Module imports
from . import apicache
from . import cmdcache
from . import plogging
from . import pmcmds
from . import docstrings

if False:
    from typing import *
    import pymel.core.general
    import pymel.core.uitypes
    C = TypeVar('C', bound=Callable)

_logger = plogging.getLogger(__name__)

# Initialize the cache globals

# Doing an initialization here mainly just for auto-completion, and to
# see these variables are defined here when doing text searches; the values
# are set inside loadApi/CmdCache

# ApiCache
apiTypesToApiEnums = None  # type: Dict[str, int]
apiEnumsToApiTypes = None  # type: Dict[int, str]
mayaTypesToApiTypes = None  # type: Dict[str, str]
apiTypesToApiClasses = None  # type: Dict[str, Type]
apiClassInfo = None

mayaTypesToApiEnums = None  # type: Dict[str, int]

# ApiMelBridgeCache
apiToMelData = None
apiClassOverrides = None

# CmdCache
cmdlist = {}
nodeHierarchy = None
uiClassList = None
nodeCommandList = None
moduleCmds = None

# global variable that indicates if we're building templates
building = False


_apiCacheInst = None
_apiMelBridgeCacheInst = None
_cmdCacheInst = None


class MissingInCacheError(Exception):
    pass


class MelCommandMissingError(MissingInCacheError):
    def __init__(self, cmdName):
        self.cmdName = cmdName

    def str(self):
        return "mel command {} cannot be found - perhaps it is not available" \
               " in this version of maya?".format(self.cmdName)


class ApiMethodMissingError(MissingInCacheError):
    def __init__(self, apiClassName, methodName):
        self.apiClassName = apiClassName
        self.methodName = methodName

    def str(self):
        return "method {} of {} cannot be found - perhaps it is not available" \
               " in this version of maya?".format(self.methodName,
                                                  self.apiClassName)



# Though the global variables and the attributes on _apiCacheInst SHOULD
# always point to the same objects - ie,
#    _apiCacheInst.apiClassInfo is apiClassInfo
# should be true, I'm paranoid they will get out of sync, so I'm
# treating _apiCacheInst as though it ISN'T in sync, and needs to be updated
# whenever we interact with it...


def loadApiCache():
    _logger.debug("Loading api cache...")
    _start = time.time()

    global _apiCacheInst
    global _apiMelBridgeCacheInst

    _apiCacheInst = apicache.ApiCache()
    _apiCacheInst.build()
    _apiMelBridgeCacheInst = apicache.ApiMelBridgeCache()
    _apiMelBridgeCacheInst.build()
    _setApiCacheGlobals()

    _elapsed = time.time() - _start
    _logger.debug("Initialized API Cache in in %.2f sec" % _elapsed)


def _setApiCacheGlobals():
    global _apiCacheInst
    global _apiMelBridgeCacheInst

    for names, values in [(_apiCacheInst.cacheNames(),
                           _apiCacheInst.contents()),
                          (_apiMelBridgeCacheInst.cacheNames(),
                           _apiMelBridgeCacheInst.contents()),
                          (_apiCacheInst.EXTRA_GLOBAL_NAMES,
                           _apiCacheInst.extraDicts())]:
        for name, val in zip(names, values):
            globals()[name] = val


def loadCmdCache():
    global _cmdCacheInst

    global cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds

    # cmdlist can be populated when plugins are loaded, prior to this being called
    origCmdlist = cmdlist

    if nodeHierarchy is not None:
        return

    _logger.debug("Loading cmd cache...")
    _start = time.time()
    _cmdCacheInst = cmdcache.CmdCache()
    _cmdCacheInst.build()

    for name, val in zip(_cmdCacheInst.cacheNames(), _cmdCacheInst.contents()):
        globals()[name] = val

    assert not set(cmdlist.keys()).intersection(origCmdlist.keys())
    cmdlist.update(origCmdlist)

    _elapsed = time.time() - _start
    _logger.debug("Initialized Cmd Cache in in %.2f sec" % _elapsed)


def saveApiCache():
    global _apiCacheInst
    _apiCacheInst.save(globals())


def saveApiMelBridgeCache():
    global _apiMelBridgeCacheInst
    _apiMelBridgeCacheInst.save(globals())


def mergeApiClassOverrides():
    global _apiCacheInst
    global _apiMelBridgeCacheInst
    _apiCacheInst.update(globals())
    _apiMelBridgeCacheInst.update(globals())
    _apiCacheInst._mergeClassOverrides(_apiMelBridgeCacheInst)
    _setApiCacheGlobals()


loadApiCache()  # need mayaTypesToApiTypes

# ---------------------------------------------------------------
#        Mappings and Lists
# ---------------------------------------------------------------

EXCLUDE_METHODS = ['type', 'className', 'create', 'name', 'attribute',
                   'addAttribute', 'removeAttribute', 'typeId']

#: controls whether command docstrings will contain examples parsed from autodesk docs
# examples are usually only included when creating documentation, otherwise it's too much info
docstringMode = os.environ.get('PYMEL_DOCSTRINGS_MODE', 'pydoc')

# Lookup from PyNode type name as a string to PyNode type as a class
pyNodeNamesToPyNodes = {}  # type: Dict[str, Type]

# Lookup from MFn name to Pymel name
apiClassNamesToPyNodeNames = {}  # type: Dict[str, str]
# Lookup from MFn name to Pymel class
apiClassNamesToPymelTypes = {}  # type: Dict[str, Type]

# Dictionary mapping from maya node type names (ie, surfaceShape) to pymel
# class names, in this module - ie, SurfaceShape
mayaTypeNameToPymelTypeName = {}
pymelTypeNameToMayaTypeName = {}

# Lookup from Api Enums to Pymel Component Classes
#
# A list of possible component classes is always returned (even if it's only
# of length one).
apiEnumsToPyComponents = {}

# child:parent lookup of the pymel classes that derive from DependNode
pyNodeTypesHierarchy = {}


#: for certain nodes, the best command on which to base the node class cannot create nodes, but can only provide information.
#: these commands require special treatment during class generation because, for them the 'create' mode is the same as other node's 'edit' mode
nodeTypeToInfoCommand = {
    #'mesh' : 'polyEvaluate',
    'transform': 'xform'
}


def toPyNode(res):
    # type: (Optional[str]) -> Optional[pymel.core.general.PyNode]
    """
    returns a PyNode object

    Parameters
    ----------
    res : Optional[str]

    Returns
    -------
    Optional[pymel.core.general.PyNode]
    """
    if res is not None and res != '':
        import pymel.core.general
        return pymel.core.general.PyNode(res)


def unwrapToPyNode(res):
    # type: (List[str]) -> Optional[pymel.core.general.PyNode]
    """
    unwraps a 1-item list, and returns a PyNode object

    Parameters
    ----------
    res : List[str]

    Returns
    -------
    Optional[pymel.core.general.PyNode]
    """
    if res is not None and res[0]:
        import pymel.core.general
        return pymel.core.general.PyNode(res[0])


def toPyUI(res):
    # type: (Optional[str]) -> Optional[pymel.core.uitypes.PyUI]
    """
    returns a PyUI object

    Parameters
    ----------
    res : Optional[str]

    Returns
    -------
    Optional[pymel.core.uitypes.PyUI]
    """
    if res is not None:
        import pymel.core.uitypes
        return pymel.core.uitypes.PyUI(res)


def toPyType(moduleName, objectName):
    # type: (str, str) -> Callable[[Any], Any]
    """
    Returns a function which casts it's single argument to
    an object with the given name in the given module (name).

    The module / object are given as strings, so that the module
    may be imported when the function is called, to avoid
    making factories dependent on, say, pymel.core.general or
    pymel.core.uitypes

    Parameters
    ----------
    moduleName : str
    objectName : str

    Returns
    -------
    Callable[[Any], Any]
    """
    def toGivenClass(res):
        # Use the 'from moduleName import objectName' form of
        # __import__, because that guarantees it returns the
        # 'bottom' module (ie, myPackage.myModule, NOT myPackage),
        # note that __import__ doesn't actually insert objectName into
        # the locals... which we don't really want anyway
        module = __import__(moduleName, globals(), locals(), [objectName], -1)
        cls = getattr(module, objectName)
        if res is not None:
            return cls(res)
    toGivenClass.__name__ = 'to%s' % util.capitalize(objectName)
    toGivenClass.__doc__ = "returns a %s object" % objectName
    return toGivenClass


def toPyNodeList(res):
    # type: (Optional[List[str]]) -> List[pymel.core.general.PyNode]
    """
    returns a list of PyNode objects

    Parameters
    ----------
    res : Optional[List[str]]

    Returns
    -------
    List[pymel.core.general.PyNode]
    """
    if res is None:
        return []
    import pymel.core.general
    return [pymel.core.general.PyNode(x) for x in res]


def splitToPyNodeList(res):
    # type: (str) -> List[pymel.core.general.PyNode]
    """
    converts a whitespace-separated string of names to a list of PyNode objects

    Parameters
    ----------
    res : str

    Returns
    -------
    List[pymel.core.general.PyNode]
    """
    return toPyNodeList(res.split())


def toPyUIList(res):
    # type: (str) -> List[pymel.core.uitypes.PyUI]
    """
    returns a list of PyUI objects

    Parameters
    ----------
    res : str

    Returns
    -------
    List[pymel.core.uitypes.PyUI]
    """
    if res is None:
        return []
    import pymel.core.uitypes
    return [pymel.core.uitypes.PyUI(x) for x in res]


def toPyTypeList(moduleName, objectName):
    # type: (str, str) -> Callable[[Any], List[Any]]
    """
    Returns a function which casts the members of it's iterable
    argument to the given class.

    Parameters
    ----------
    moduleName : str
    objectName : str

    Returns
    -------
    Callable[[Any], List[Any]]
    """
    def toGivenClassList(res):
        module = __import__(moduleName, globals(), locals(), [objectName], 0)
        cls = getattr(module, objectName)
        if res is None:
            return []
        return [cls(x) for x in res]
    toGivenClassList.__name__ = 'to%sList' % util.capitalize(objectName)
    toGivenClassList.__doc__ = "returns a list of %s objects" % objectName
    return toGivenClassList


def raiseError(typ, *args):
    def f(res):
        raise typ(*args)
    return f


class Flag(Condition):

    def __init__(self, longName, shortName, truthValue=True):
        """
        Conditional for evaluating if a given flag is present.

        Will also check that the given flag has the required
        truthValue (True, by default). If you don't care
        about the truthValue (ie, you want to have the condition
        evaluate to true as long as the flag is present),
        set truthValue to None.
        """
        self.shortName = shortName
        self.longName = longName
        self.truthValue = truthValue

    def eval(self, kwargs):
        for arg in (self.shortName, self.longName):
            if arg in kwargs:
                if self.truthValue is None or \
                        bool(kwargs[arg]) == self.truthValue:
                    return True
        return False

    def __str__(self):
        return self.longName


# TODO: commands that don't return anything, but perhaps should?
# affectedNet (PyNodes created)

simpleCommandWraps = {
    'createRenderLayer': [(toPyNode, Always)],
    'createDisplayLayer': [(toPyNode, Always)],
    'distanceDimension': [(toPyNode, Always)],
    'listAttr': [(util.listForNone, Always)],
    'instance': [(toPyNodeList, Always)],

    'getPanel': [(toPyType('pymel.core.uitypes', 'Panel'),
                  Flag('containing', 'c', None) |
                  Flag('underPointer', 'up') |
                  Flag('withFocus', 'wf')),
                 (toPyTypeList('pymel.core.uitypes', 'Panel'),
                  ~Flag('typeOf', 'to', None))
                 ],

    'textScrollList': [(util.listForNone,
                        Flag('query', 'q') &
                        (Flag('selectIndexedItem', 'sii') |
                         Flag('allItems', 'ai') |
                         Flag('selectItem', 'si')))
                       ],

    'optionMenu': [(util.listForNone,
                    Flag('query', 'q') &
                    (Flag('itemListLong', 'ill') |
                     Flag('itemListShort', 'ils')))
                   ],

    'optionMenuGrp': [(util.listForNone,
                       Flag('query', 'q') &
                       (Flag('itemListLong', 'ill') |
                        Flag('itemListShort', 'ils')))
                      ],

    'modelEditor': [(toPyNode,
                     Flag('query', 'q') & Flag('camera', 'cam'))
                    ],

    'skinCluster': [(toPyNodeList,
                     Flag('query', 'q') &
                     (Flag('geometry', 'g') |
                      Flag('deformerTools', 'dt') |
                      Flag('influence', 'inf') |
                      Flag('weightedInfluence', 'wi'))),
                    ],
    'addDynamic': [(toPyNodeList, Always)],
    'addPP': [(toPyNodeList, Always)],
    'animLayer': [(toPyNode,
                   Flag('query', 'q') &
                   (Flag('root', 'r') |
                    Flag('bestLayer', 'bl') |
                    Flag('parent', 'p'))),
                  (toPyNodeList,
                   Flag('query', 'q') &
                   (Flag('children', 'c') |
                    Flag('attribute', 'at') |
                    Flag('bestAnimLayer', 'blr') |
                    Flag('animCurves', 'anc') |
                    Flag('baseAnimCurves', 'bac') |
                    Flag('blendNodes', 'bld') |
                    Flag('affectedLayers', 'afl') |
                    Flag('parent', 'p')))
                  ],
    'annotate': [(lambda res: toPyNode(res.strip()), Always)],
    'arclen': [(toPyNode, Flag(' constructionHistory', 'ch'))],
    'art3dPaintCtx': [(splitToPyNodeList,
                       Flag('query', 'q') &
                       (Flag('shapenames', 'shn') |
                        Flag('shadernames', 'hnm')))
                      ],
    'artAttrCtx': [(splitToPyNodeList,
                    Flag('query', 'q') &
                    Flag('paintNodeArray', 'pna'))
                   ],
    'container': [(toPyNodeList,
                   Flag('query', 'q') &
                   (Flag('nodeList', 'nl') |
                    Flag('connectionList', 'cl'))),
                  (toPyNode,
                   Flag('query', 'q') &
                   (Flag('findContainer', 'fc') |
                    Flag('asset', 'a'))),
                  (lambda res: [(toPyNode(res[i]), res[i + 1]) for i in range(0, len(res), 2)],
                   Flag('query', 'q') &
                   Flag('bindAttr', 'ba') & ~(Flag('publishName', 'pn') | Flag('publishAsParent', 'pap') | Flag('publishAsChild', 'pac'))),
                  (raiseError(ValueError, 'In query mode bindAttr can *only* be used with the publishName, publishAsParent and publishAsChild flags'),
                   Flag('query', 'q') &
                   Flag('unbindAttr', 'ua') & ~(Flag('publishName', 'pn') | Flag('publishAsParent', 'pap') | Flag('publishAsChild', 'pac'))),
                  ],
}
# ---------------------------------------------------------------

if docstringMode == 'html':
    # examples aren't crucial, don't error if can't be read
    examples = cmdcache.CmdProcessedExamplesCache().read(ignoreError=True)
    if examples:
        for cmd, example in examples.items():
            try:
                cmdlist[cmd]['example'] = example
            except KeyError:
                print("found an example for an unknown command:", cmd)
                pass


def _getApiOverrideData(classname, pymelName):
    data = apiToMelData.get((classname, pymelName))
    if data is not None:
        origName = data.get('origName')
        if origName:
            return _getApiOverrideData(classname, origName)
    if data is None:
        # return defaults
        data = {}
    return data


def _getApiOverrideNameAndData(classname, pymelName):
    origName = pymelName
    data = _getApiOverrideData(classname, pymelName)
    explicitRename = False
    nameType = data.get('useName', 'API')
    if nameType == 'API':
        pass
    elif nameType == 'MEL':
        pymelName = data.get('melName', pymelName)
    else:
        pymelName = nameType
        explicitRename = True
    # FIXME: think we don't need explicitRename - think we really only care
    # if name changed, not if it was an "explicit" rename, and so caller can
    # just compare returned name with passed in name... but I need to confirm
    # that won't change anything, don't have time to do that now
    if origName != pymelName:
        renamedData = apiToMelData.setdefault((classname, pymelName), {})
        if 'origName' not in renamedData:
            renamedData['origName'] = origName
    return pymelName, data, explicitRename


def getUncachedCmds():
    return list(set(name for (name, val) in inspect.getmembers(cmds, callable))
            .difference(cmdlist.keys()))


# -----------------------
# Function Factory
# -----------------------

docCacheLoaded = False


def loadCmdDocCache(ignoreError=True):
    global docCacheLoaded
    if docCacheLoaded:
        return
    # examples aren't crucial, don't error if can't be read
    data = cmdcache.CmdDocsCache().read(ignoreError=ignoreError)
    util.mergeCascadingDicts(data, cmdlist)
    docCacheLoaded = True


def getCmdFunc(cmdName):
    # type: (str) -> Callable
    """
    Parameters
    ----------
    cmdName : str

    Returns
    -------
    Callable
    """
    func = getattr(pmcmds, cmdName, None)
    if func is None:
        def nonExistantFunc(*args, **kwargs):
            '''Just gives the same attribute error you would get if you
            tried to access the module from the func, for consistency

            Also clearer than returning None, and getting an error about
            None not having a given attribute.

            This should generally only happen if using an "old" maya version
            that doesn't have a command found in newer maya versions
            '''
            getattr(pmcmds, cmdName)
        return nonExistantFunc
    return addCmdDocs(func)


def _guessCmdName(func):
    try:
        return func.__name__
    except AttributeError:
        return func.__class__.__name__


def addCmdDocs(func, cmdName=None):
    # type: (C, Optional[str]) -> C
    """
    Parameters
    ----------
    func : C
    cmdName : Optional[str]

    Returns
    -------
    C
    """

    if cmdName is None:
        cmdName = _guessCmdName(func)
    if func.__doc__:
        docstring = func.__doc__
    else:
        docstring = ''
    util.addLazyDocString(func, addCmdDocsCallback, cmdName, docstring)
    return func


def addCmdDocsCallback(cmdName, docstring=''):
    try:
        return docBuilderCls(cmdName).build(docstring)
    except MelCommandMissingError as e:
        # % formatter deals with unicode, but keeps strings str if not unicode
        return '%s' % e


if docstringMode == 'html':
    docBuilderCls = docstrings.RstDocstringBuilder
elif docstringMode == 'stubs':
    docBuilderCls = docstrings.NumpyDocstringBuilder
else:
    docBuilderCls = docstrings.PyDocstringBuilder


def _addFlagCmdDocs(func, cmdName, flag, docstring=''):
    util.addLazyDocString(func, addFlagCmdDocsCallback, cmdName, flag, docstring)
    return func


def addFlagCmdDocsCallback(cmdName, flag, docstring):
    """
    Add documentation to a method that corresponds to a single command flag
    """
    builder = docBuilderCls(cmdName)

    allFlagInfo = cmdlist[cmdName]['flags']
    try:
        flagInfo = allFlagInfo[flag]
    except KeyError:
        _logger.warning('could not find any info on flag %s' % flag)
    else:
        if docstring:
            docstring += '\n\n'

        newdocs = flagInfo.get('docstring', '')
        if newdocs:
            docstring += newdocs + '\n\n'

        if 'secondaryFlags' in flagInfo:
            builder.startFlagSection()
            for secondaryFlag in flagInfo['secondaryFlags']:
                docstring += builder._addFlag(flag, allFlagInfo[secondaryFlag])

        docstring += builder.addFooter()
    return docstring

#    func.__doc__ = docstring
#    return func


def _getTimeRangeFlags(cmdName):
    """
    used parsed data and naming convention to determine which flags are
    callbacks
    """

    commandFlags = set()
    try:
        flagDocs = cmdlist[cmdName]['flags']
    except KeyError:
        pass
    else:
        for flag, data in flagDocs.items():
            args = data['args']
            if isinstance(args, basestring) and args.lower() == 'timerange':
                commandFlags.update([flag, data['shortname']])
    return commandFlags


class Callback(object):

    """
    Enables deferred function evaluation with 'baked' arguments.
    Useful where lambdas won't work...

    It also ensures that the entire callback will be be represented by one
    undo entry.

    Example::

        import pymel as pm
        def addRigger(rigger, **kwargs):
            print "adding rigger", rigger

        for rigger in riggers:
            pm.menuItem(
                label = "Add " + str(rigger),
                c = Callback(addRigger,rigger,p=1))   # will run: addRigger(rigger,p=1)
    """

    MAX_RECENT_ERRORS = 10

    # keeps information for the most recent callback errors
    recentErrors = []

    CallbackErrorLog = util.namedtuple('CallbackErrorLog', 'callback exception trace creationTrace')

    @classmethod
    def logCallbackError(cls, callback, exception=None, trace=None,
                         creationTrace=None):
        if exception is None:
            exception = sys.exc_info()[1]
        if trace is None:
            trace = traceback.format_exc()
        if creationTrace is None:
            if isinstance(callback, Callback):
                creationTrace = ''.join(callback.traceback)
            else:
                creationTrace = ''
        cls.recentErrors.insert(0, cls.CallbackErrorLog(callback, exception,
                                                        trace, creationTrace))
        if len(cls.recentErrors) > cls.MAX_RECENT_ERRORS:
            del cls.recentErrors[cls.MAX_RECENT_ERRORS:]

    @classmethod
    def formatRecentError(cls, index=0):
        info = cls.recentErrors[index]
        msg = '''Error calling %s in a callback:
Callback Creation Trace:
%s

Error Trace:
%s
''' % (info.callback, info.creationTrace, info.trace)
        return msg

    @classmethod
    def printRecentError(cls, index=0):
        print(cls.formatRecentError(index=index))

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.traceback = traceback.format_stack()

    def __call__(self, *args):
        cmds.undoInfo(openChunk=1)
        try:
            try:
                return self.func(*self.args, **self.kwargs)
            except Exception as e:
                self.logCallbackError(self)
                raise
        finally:
            cmds.undoInfo(closeChunk=1)


class CallbackWithArgs(Callback):

    def __call__(self, *args, **kwargs):
        # not sure when kwargs would get passed to __call__,
        # but best not to remove support now
        kwargsFinal = self.kwargs.copy()
        kwargsFinal.update(kwargs)
        cmds.undoInfo(openChunk=1)
        try:
            try:
                return self.func(*self.args + args, **kwargsFinal)
            except Exception as e:
                self.logCallbackError(self)
                raise
        finally:
            cmds.undoInfo(closeChunk=1)


def makeUICallback(origCallback, args, doPassSelf):
    """
    this function is used to make the callback, so that we can ensure the origCallback gets
    "pinned" down
    """
    # print "fixing callback", key
    creationTraceback = ''.join(traceback.format_stack())

    def callback(*cb_args):
        newargs = list(cb_args)

        if doPassSelf:
            newargs = [args[0]] + newargs
        newargs = tuple(newargs)
        try:
            res = origCallback(*newargs)
        except Exception as e:
            # if origCallback was ITSELF a Callback obj, it will have
            # already logged the error..
            if not isinstance(origCallback, Callback):
                Callback.logCallbackError(origCallback,
                                          creationTrace=creationTraceback)
            raise
        if isinstance(res, util.ProxyUnicode):
            import builtins
            res = builtins.str(res)
        return res
    return callback


def fixCallbacks(inFunc, commandFlags, funcName=None):
    """
    Prior to maya 2011, when a user provides a custom callback functions for a
    UI elements, such as a checkBox, when the callback is triggered it is passed
    a string instead of a real python values.

    For example, a checkBox changeCommand returns the string 'true' instead of
    the python boolean True. This function wraps UI commands to correct the
    problem and also adds an extra flag to all commands with callbacks called
    'passSelf'.  When set to True, an instance of the calling UI class will be
    passed as the first argument.

    if inFunc has been renamed, pass a funcName to lookup command info in apicache.cmdlist
    """

    if not funcName:
        funcName = pmcmds.getCmdName(inFunc)

    if not commandFlags:
        #commandFlags = []
        return inFunc

    # need to define a seperate var here to hold
    # the old value of newFunc, b/c 'return newFunc'
    # would be recursive
    beforeUiFunc = inFunc

    def newUiFunc(*args, **kwargs):

        if len(args):
            doPassSelf = kwargs.pop('passSelf', False)
        else:
            doPassSelf = False

        for key in commandFlags:
            try:
                cb = kwargs[key]
                if callable(cb):
                    kwargs[key] = makeUICallback(cb, args, doPassSelf)
            except KeyError:
                pass

        return beforeUiFunc(*args, **kwargs)

    newUiFunc.__name__ = funcName
    newUiFunc.__module__ = inFunc.__module__
    newUiFunc.__doc__ = inFunc.__doc__

    return newUiFunc


def _getSourceFunction(funcNameOrObject, module=None):
    inFunc = None
    if isinstance(funcNameOrObject, basestring):
        funcName = funcNameOrObject

        # make sure that we import from pmcmds, not cmds
        if module and module != cmds:
            try:
                inFunc = getattr(module, funcName)
                customFunc = True
            except AttributeError:
                pass

        # inFunc may be a custom class object, like fileInfo, which may have
        # its own boolean testing... so be sure to check if it's None, not
        # "if not inFunc"!
        if inFunc is None:
            try:
                inFunc = getattr(pmcmds, funcName)
                customFunc = False
            except AttributeError:
                return None, None, None
    else:
        funcName = pmcmds.getCmdName(funcNameOrObject)
        inFunc = funcNameOrObject
        customFunc = True

    # Do some sanity checks...
    if not callable(inFunc):
        _logger.warning('%s not callable' % funcNameOrObject)
        return None, None, None
    # python doesn't like unicode function names
    funcName = str(funcName)
    return inFunc, funcName, customFunc


def convertTimeValues(rawVal):
    # in mel, you would do:
    #   keyframe -time "1:10"
    # in order to get the same behavior in python, you would
    # have to do:
    #   cmds.keyframe(time=("1:10",))
    # ...which is lame. So, standardize everything by throwing
    # it inside of a tuple...

    # we only DON'T put it in a tuple, if it already IS a tuple/
    # list, AND it doesn't look like a simple range - ie,
    #   cmds.keyframe(time=(1,10))
    # will get converted to
    #   cmds.keyframe(time=((1,10),))
    # but
    #   cmds.keyframe(time=('1:3', [1,5]))
    # will be left alone...
    if (isinstance(rawVal, (list, tuple))
            and 1 <= len(rawVal) <= 2
            and all(isinstance(x, (basestring, int, int, float))
                    for x in rawVal)):
        values = list(rawVal)
    else:
        values = [rawVal]

    for i, val in enumerate(values):
        if isinstance(val, slice):
            val = [val.start, val.stop]
        elif isinstance(val, tuple):
            val = list(val)

        if isinstance(val, list):
            if len(val) == 1:
                val.append(None)
            if len(val) == 2 and None in val:
                # easiest way to get accurate min/max bounds
                # is to convert to the string form...
                val = ':'.join('' if x is None else str(x)
                               for x in val)
            else:
                val = tuple(val)
        values[i] = val
    return values


def maybeConvert(val, castFunc):
    if isinstance(val, list):
        try:
            return [castFunc(x) for x in val]
        except:
            return val
    elif val:
        try:
            return castFunc(val)
        except Exception:
            return val


def functionFactory(funcNameOrObject, returnFunc=None, module=None,
                    rename=None, uiWidget=False):
    """
    create a new function, apply the given returnFunc to the results (if any)
    Use pre-parsed command documentation to add to __doc__ strings for the
    command.
    """

    # if module is None:
    #   module = _thisModule
    inFunc, funcName, customFunc = _getSourceFunction(funcNameOrObject, module)
    if inFunc is None:
        return

    cmdInfo = cmdlist[funcName]
    funcType = type(inFunc)

    if funcType == types.BuiltinFunctionType:
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                _logger.warning("Function found in module %s has different name "
                                "than desired: %s != %s. simple fix? %s" %
                                (inFunc.__module__, funcName, newFuncName,
                                funcType == types.FunctionType and
                                returnFunc is None))
        except AttributeError:
            _logger.warning("%s had no '__name__' attribute" % inFunc)

    timeRangeFlags = _getTimeRangeFlags(funcName)

    # some refactoring done here - to avoid code duplication (and make things
    # clearer),
    # we now ALWAYS do things in the following order:
    # 1. Perform operations which modify the execution of the function (ie,
    #    adding return funcs)
    # 2. Modify the function descriptors - ie, __doc__, __name__, etc

    newFunc = inFunc

    if timeRangeFlags:
        # need to define a seperate var here to hold
        # the old value of newFunc, b/c 'return newFunc'
        # would be recursive
        beforeTimeRangeFunc = newFunc

        def newFuncWithTimeRangeFlags(*args, **kwargs):
            for flag in timeRangeFlags:
                try:
                    # allow for open-ended time ranges:
                    # (1,None), (1,), slice(1,None), "1:"
                    # (None,100), slice(100), ":100"
                    # (None,None), ":"
                    rawVal = kwargs[flag]
                except KeyError:
                    continue
                else:
                    kwargs[flag] = convertTimeValues(rawVal)
            return beforeTimeRangeFunc(*args, **kwargs)
        newFunc = newFuncWithTimeRangeFlags

    if returnFunc:
        # need to define a separate var here to hold
        # the old value of newFunc, b/c 'return newFunc'
        # would be recursive
        beforeReturnFunc = newFunc

        def newFuncWithReturnFunc(*args, **kwargs):
            res = beforeReturnFunc(*args, **kwargs)
            # and 'edit' not in kwargs and 'e' not in kwargs:
            if not kwargs.get('query', kwargs.get('q', False)):
                if isinstance(res, list):
                    # some node commands unnecessarily return a list with a
                    # single object
                    if cmdInfo.get('resultNeedsUnpacking', False):
                        res = returnFunc(res[0])
                    else:
                        try:
                            res = [returnFunc(x) for x in res]
                        except:
                            pass

                elif res:
                    try:
                        res = returnFunc(res)
                    except Exception as e:
                        pass
            return res
        newFunc = newFuncWithReturnFunc

    createUnpack = cmdInfo.get('resultNeedsUnpacking', False)
    unpackFlags = set()
    for flag, flagInfo in cmdInfo.get('flags', {}).items():
        if flagInfo.get('resultNeedsUnpacking', False):
            unpackFlags.add(flagInfo.get('longname', flag))
            unpackFlags.add(flagInfo.get('shortname', flag))

    if (createUnpack or unpackFlags):
        beforeUnpackFunc = newFunc

        def newFuncWithUnpack(*args, **kwargs):
            res = beforeUnpackFunc(*args, **kwargs)
            if isinstance(res, list) and len(res) == 1:
                if kwargs.get('query', kwargs.get('q', False)):
                    # query mode...
                    if not unpackFlags.isdisjoint(kwargs):
                        res = res[0]
                else:
                    if createUnpack:
                        res = res[0]
            return res
        newFunc = newFuncWithUnpack

    if funcName in simpleCommandWraps:
        # simple wraps: we only do these for functions which have not been manually customized
        wraps = simpleCommandWraps[funcName]
        beforeSimpleWrap = newFunc

        def simpleWrapFunc(*args, **kwargs):
            res = beforeSimpleWrap(*args, **kwargs)
            for func, wrapCondition in wraps:
                if wrapCondition.eval(kwargs):
                    res = func(res)
                    break
            return res
        newFunc = simpleWrapFunc

        # create an initial docstring.  this will be filled out below
        # by addCmdDocs
        doc = docBuilderCls.section('Modifications')
        for func, wrapCondition in wraps:
            if wrapCondition != Always:
                # use only the long flag name
                flags = ' for flags: ' + str(wrapCondition)
            elif len(wraps) > 1:
                flags = ' for all other flags'
            else:
                flags = ''
            if func.__doc__:
                funcString = func.__doc__.strip()
            else:
                funcString = pmcmds.getCmdName(func) + '(result)'
            doc += '  - ' + funcString + flags + '\n'

        newFunc.__doc__ = doc

    #----------------------------
    # UI commands with callbacks
    #----------------------------

    callbackFlags = cmdInfo.get('callbackFlags', None)
    if callbackFlags:
        newFunc = fixCallbacks(newFunc, callbackFlags, funcName)

    # Check if we have not been wrapped yet. if we haven't and our input function is a builtin or we're renaming
    # then we need a wrap. otherwise we can just change the __doc__ and __name__ and move on
    if newFunc == inFunc and (type(newFunc) == types.BuiltinFunctionType or rename):
        # we'll need a new function: we don't want to touch built-ins, or
        # rename an existing function, as that can screw things up... just modifying docs
        # of non-builtin should be fine, though
        def newFunc(*args, **kwargs):
            return inFunc(*args, **kwargs)

    # 2. Modify the function descriptors - ie, __doc__, __name__, etc
    if customFunc:
        # copy over the exisitng docs
        if not newFunc.__doc__:
            newFunc.__doc__ = inFunc.__doc__
        elif inFunc.__doc__:
            newFunc.__doc__ = inFunc.__doc__

    if cmdlist[funcName]['type'] != 'runtime':
        # runtime functions have no docs
        addCmdDocs(newFunc, funcName)

    if rename:
        newFunc.__name__ = rename
    else:
        newFunc.__name__ = funcName

    return newFunc


def makeCreateFlagMethod(inFunc, flag, newMethodName=None, docstring='', cmdName=None, returnFunc=None):
    """
    Add documentation to a method that corresponds to a single command flag
    """
    #name = 'set' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = pmcmds.getCmdName(inFunc)

    if returnFunc:
        def wrappedMelFunc(*args, **kwargs):
            if len(args) <= 1:
                kwargs[flag] = True
            elif len(args) == 2:
                kwargs[flag] = args[1]
                args = (args[0],)
            else:
                kwargs[flag] = args[1:]
                args = (args[0],)
            return returnFunc(inFunc(*args, **kwargs))
    else:
        def wrappedMelFunc(*args, **kwargs):
            if len(args) <= 1:
                kwargs[flag] = True
            elif len(args) == 2:
                kwargs[flag] = args[1]
                args = (args[0],)
            else:
                kwargs[flag] = args[1:]
                args = (args[0],)
            return inFunc(*args, **kwargs)

    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag

    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring)


def createflag(cmdName, flag):
    """create flag decorator"""
    def create_decorator(method):
        wrappedMelFunc = makeCreateFlagMethod(method, flag, pmcmds.getCmdName(method), cmdName=cmdName)
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return create_decorator
'''
def secondaryflag( cmdName, flag ):
    """query flag decorator"""
    def secondary_decorator(method):
        return makeSecondaryFlagCmd( method, method.__name__, flag, cmdName=cmdName )
    return secondary_decorator
'''


def makeQueryFlagMethod(inFunc, flag, newMethodName=None, docstring='', cmdName=None, returnFunc=None):
    #name = 'get' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = pmcmds.getCmdName(inFunc)

    if returnFunc:
        def wrappedMelFunc(self, **kwargs):
            kwargs['query'] = True
            kwargs[flag] = True
            return returnFunc(inFunc(self, **kwargs))
    else:
        def wrappedMelFunc(self, **kwargs):
            kwargs['query'] = True
            kwargs[flag] = True
            return inFunc(self, **kwargs)

    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag

    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring)


def queryflag(cmdName, flag):
    """query flag decorator"""
    def query_decorator(method):
        wrappedMelFunc = makeQueryFlagMethod(method, flag, pmcmds.getCmdName(method), cmdName=cmdName)
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return query_decorator


def handleCallbacks(args, kwargs, callbackFlags):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in callbackFlags:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass


def asEdit(self, func, kwargs, flag, val):
    kwargs['edit'] = True
    kwargs[flag] = val
    try:
        return func(self, **kwargs)
    except TypeError:
        kwargs.pop('edit')
        return func(self, **kwargs)


def asQuery(self, func, kwargs, flag):
    kwargs['query'] = True
    kwargs[flag] = True
    return func(self, **kwargs)


def makeEditFlagMethod(inFunc, flag, newMethodName=None, docstring='', cmdName=None):
    #name = 'set' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = pmcmds.getCmdName(inFunc)

    def wrappedMelFunc(self, val=True, **kwargs):
        kwargs['edit'] = True
        kwargs[flag] = val
        try:
            return inFunc(self, **kwargs)
        except TypeError:
            kwargs.pop('edit')
            return inFunc(self, **kwargs)

    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag

    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring)


def editflag(cmdName, flag):
    """edit flag decorator"""
    def edit_decorator(method):
        wrappedMelFunc = makeEditFlagMethod(method, flag, pmcmds.getCmdName(method), cmdName=cmdName)
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return edit_decorator


def addMelDocs(cmdName, flag=None):
    """decorator for adding docs"""

    if flag:
        # A method generated from a flag
        def doc_decorator(method):
            wrappedMelFunc = _addFlagCmdDocs(method, cmdName, flag)
            wrappedMelFunc.__module__ = method.__module__
            return wrappedMelFunc
    else:
        # NOTE: runtime functions have no docs. Do not use this with runtime functions
        # A command
        def doc_decorator(func):
            try:
                wrappedMelFunc = addCmdDocs(func, cmdName)
                wrappedMelFunc.__module__ = func.__module__
            except KeyError:
                _logger.info(("No documentation available %s command" % (cmdName)))
                wrappedMelFunc = func
            return wrappedMelFunc

    return doc_decorator


def listForNoneQuery(res, kwargs, flags):
    "convert a None to an empty list on the given query flags"
    if res is None and kwargs.get('query', kwargs.get('q', False ) ) and \
            bool([True for long, short in flags if kwargs.get(long, kwargs.get(short, False))]):
        return []
    return res


class ApiTypeRegister(object):

    """"
    Use this class to register the classes and functions used to wrap api methods.

    there are 4 dictionaries of functions maintained by this class:
        - inCast : for casting input arguments to a type that the api method expects
        - outCast: for casting the result of the api method to a type that pymel expects (outCast expect two args (self, obj) )
        - refInit: for initializing types passed by reference or via pointer
        - refCast: for casting the pointers to pymel types after they have been passed to the method

    To register a new type call `ApiTypeRegister.register`.
    """
    types = {}  # type: Dict[str, str]
    inCast = {}  # type: Dict[str, Callable[[Any], Any]]
    # outcast functions have signature:
    #     func(pynodeInstance, value)
    # ...but as far as I can tell, only MPlug actually uses self
    outCast = {}  # type: Dict[str, Callable[[Any, Any], Any]]
    refInit = {}
    refCast = {}
    arrayItemTypes = {}
    doc = {}

    @staticmethod
    def _makeRefFunc(capitalizedApiType, size=1, **kwargs):
        # type: (Any, int, **Any) -> Callable[[], api.SafeApiPtr]
        """
        Returns a function which will return a SafeApiPtr object of the given
        type.

        This ensures that each created ref stems from a unique MScriptUtil,
        so no two refs point to the same storage!

        Parameters
        ----------
        size : `int`
            If other then 1, the returned function will initialize storage for
            an array of the given size.

        Returns
        -------
        Callable[[], api.SafeApiPtr]
        """
        def makeRef():
            return api.SafeApiPtr(capitalizedApiType, size=size, **kwargs)
        return makeRef

    @staticmethod
    def _makeApiArraySetter(type, inCast):
        iterable = hasattr(inCast, '__iter__')

        def setArray(array):
            arrayPtr = type()
            if iterable:
                [arrayPtr.append(inCast(*x)) for x in array]
            else:
                [arrayPtr.append(inCast(x)) for x in array]
            return arrayPtr
        setArray.__name__ = 'set_' + type.__name__
        return setArray

    @staticmethod
    def _makeArraySetter(apiTypeName, length, initFunc):
        def setArray(array):
            if len(array) != length:
                raise ValueError('Input list must contain exactly %s %ss' % (length, apiTypeName))
            safeArrayPtr = initFunc()
            for i, val in enumerate(array):
                safeArrayPtr[i] = val
            #_logger.debug("result %s" % safeArrayPtr)
            return safeArrayPtr
        setArray.__name__ = 'set_' + apiTypeName + str(length) + 'Array'
        return setArray

    @staticmethod
    def _makeArrayGetter(apiTypeName, length):
        def getArray(safeArrayPtr):
            return [x for x in safeArrayPtr]
        getArray.__name__ = 'get_' + apiTypeName + str(length) + 'Array'
        return getArray

    @classmethod
    def getPymelType(cls, apiType, allowGuess=True):
        # type: (Any, Any) -> Optional[str]
        """
        Map from api name to pymelName.

        we start by looking up types which are registered and then fall back
        to naming convention for types that haven't been registered yet.
        Perhaps pre-register the names?

        Returns
        -------
        Optional[str]
        """
        pymelType = cls.types.get(apiType)
        if pymelType is not None:
            if isinstance(pymelType, basestring):
                # strip the module
                return pymelType.rsplit('.', 1)[-1]
            return pymelType
        elif allowGuess:
            m = re.match('^((MIt)|(MFn)|(M))([A-Z]+.*)', apiType)
            if m:
                return m.groups()[-1]

    @classmethod
    def isRegistered(cls, apiTypeName):
        return apiTypeName in cls.types

    @classmethod
    def register(cls, apiTypeName, pymelType, inCast=None, outCast=None, apiArrayItemType=None):
        # type: (str, Type, Optional[Callable[[Any], Any]], Optional[Callable[[Any], Any]], Optional[Type]) -> None
        """
        pymelType is the type to be used internally by pymel.
        apiType will be hidden from the user and converted to the pymel type,
        possibly via inCast.

        Parameters
        ----------
        apiTypeName : str
            the name of an apiType
        pymelType : Type
        inCast : Optional[Callable[[Any], Any]]
        outCast : Optional[Callable[[Any], Any]]
        apiArrayItemType : Optional[Type]
            if set, it should be the api type that represents each item in the array
        """

        #apiTypeName = pymelType.__class__.__name__
        capType = util.capitalize(apiTypeName)

        # register type
        fullTypeName = pymelType.__name__
        moduleName = getattr(pymelType, '__module__', None)
        if moduleName:
            fullTypeName = moduleName + '.' + fullTypeName
        cls.types[apiTypeName] = fullTypeName

        if apiArrayItemType:
            cls.arrayItemTypes[apiTypeName] = apiArrayItemType
        # register result casting
        if outCast:
            cls.outCast[apiTypeName] = outCast
        elif apiArrayItemType is not None:
            pass
        else:
            # could be a lambda, but explicit function is better for debbuging
            def pymelTypeOutCast(self, x):
                return pymelType(x)
            cls.outCast[apiTypeName] = pymelTypeOutCast

        # register argument casting
        if inCast:
            cls.inCast[apiTypeName] = inCast
        elif apiArrayItemType is not None:
            pass  # filled out below
        else:
            cls.inCast[apiTypeName] = pymelType

        if apiTypeName in ['float', 'double', 'bool', 'int', 'short', 'long', 'uint']:
            initFunc = cls._makeRefFunc(capType)
            getFunc = api.SafeApiPtr.get
            cls.refInit[apiTypeName] = initFunc
            cls.refCast[apiTypeName] = getFunc
            for i in [2, 3, 4]:
                # Register arrays for this up to size for - ie,
                #   int myVar[2];
                iapiArrayTypename = apiTypeName + '__array' + str(i)
                arrayInitFunc = cls._makeRefFunc(capType, size=i)
                cls.refInit[iapiArrayTypename] = arrayInitFunc
                cls.inCast[iapiArrayTypename] = cls._makeArraySetter(apiTypeName, i, arrayInitFunc)
                cls.refCast[iapiArrayTypename] = cls._makeArrayGetter(apiTypeName, i)
                cls.types[iapiArrayTypename] = tuple([pymelType.__name__] * i)
                # Check if there is an explicit maya type for n of these - ie,
                #   int2 myVar;
                apiTypeNameN = apiTypeName + str(i)
                castNFuncName = 'as' + capType + str(i) + 'Ptr'
                if hasattr(api.MScriptUtil, castNFuncName):
                    nInitFunc = cls._makeRefFunc(apiTypeName, size=i, asTypeNPtr=True)
                    cls.refInit[apiTypeNameN] = nInitFunc
                    cls.inCast[apiTypeNameN] = cls._makeArraySetter(apiTypeName, i, nInitFunc)
                    cls.refCast[apiTypeNameN] = cls._makeArrayGetter(apiTypeName, i)
                    cls.types[apiTypeNameN] = tuple([pymelType.__name__] * i)
        else:
            try:
                apiType = getattr(api, apiTypeName)
            except AttributeError:
                if apiArrayItemType:
                    cls.refInit[apiTypeName] = list

                    # could be a lambda, but explicit function is better for debbuging
                    def apiArrayInCast(x):
                        return [apiArrayItemType(y) for y in x]

                    cls.inCast[apiTypeName] = apiArrayInCast
                    cls.refCast[apiTypeName] = None
                    cls.outCast[apiTypeName] = None

            else:
                # -- Api Array types
                if apiArrayItemType:

                    cls.refInit[apiTypeName] = apiType
                    cls.inCast[apiTypeName] = cls._makeApiArraySetter(apiType, apiArrayItemType)
                    # this is double wrapped because of the crashes occuring
                    # with MDagPathArray. not sure if it's applicable to all arrays
                    if apiType == api.MDagPathArray:
                        # could be a lambdas, but explicit functions are better for debbuging
                        def pymelDagArrayRefCast(x):
                            return [pymelType(apiArrayItemType(x[i])) for i in range(x.length())]

                        def pymelDagArrayOutCast(self, x):
                            return [pymelType(apiArrayItemType(x[i])) for i in range(x.length())]

                        cls.refCast[apiTypeName] = pymelDagArrayRefCast
                        cls.outCast[apiTypeName] = pymelDagArrayOutCast
                    else:
                        def pymelArrayRefCast(x):
                            return [pymelType(x[i]) for i in range(x.length())]

                        def pymelArrayOutCast(self, x):
                            return [pymelType(x[i]) for i in range(x.length())]

                        cls.refCast[apiTypeName] = pymelArrayRefCast
                        cls.outCast[apiTypeName] = pymelArrayOutCast

                # -- Api types
                else:
                    cls.refInit[apiTypeName] = apiType
                    cls.refCast[apiTypeName] = pymelType
                    try:
                        # automatically handle array types that correspond to
                        # this api type (e.g.  MColor and MColorArray )
                        arrayTypename = apiTypeName + 'Array'
                        apiArrayType = getattr(api, arrayTypename)
                        # e.g.  'MColorArray', Color, api.MColor
                        ApiTypeRegister.register(arrayTypename, pymelType, apiArrayItemType=apiType)
                    except AttributeError:
                        pass


ApiTypeRegister.register('float', float)
ApiTypeRegister.register('double', float)
ApiTypeRegister.register('bool', bool)
ApiTypeRegister.register('int', int)
ApiTypeRegister.register('short', int)
ApiTypeRegister.register('uint', int)
ApiTypeRegister.register('uchar', int)
#ApiTypeRegister.register('long', int)
ApiTypeRegister.register('char', str)
ApiTypeRegister.register('MString', str)
ApiTypeRegister.register('MStringArray', list, apiArrayItemType=str)
ApiTypeRegister.register('MIntArray', int, apiArrayItemType=int)
ApiTypeRegister.register('MFloatArray', float, apiArrayItemType=float)
ApiTypeRegister.register('MDoubleArray', float, apiArrayItemType=float)


class ApiArgUtil(object):

    def __init__(self, apiClassName, methodName, methodIndex=0):
        # type: (str, str, int) -> None
        """
        If methodInfo is None, then the methodIndex will be used to lookup
        the methodInfo from apiClassInfo

        Parameters
        ----------
        apiClassName : str
        methodName : str
        methodIndex : int
        """
        self.apiClassName = apiClassName
        self.methodName = methodName

        classInfo = apiClassInfo[apiClassName]
        self.basePymelName = classInfo.get('pymelMethods', {}).get(methodName,
                                                                 methodName)

        if methodIndex is None:
            try:
                methodInfoList = classInfo['methods'][methodName]
            except KeyError:
                raise ApiMethodMissingError(apiClassName, methodName)
            else:
                for i, methodInfo in enumerate(methodInfoList):

                    argHelper = ApiArgUtil(apiClassName, methodName, i)

                    if argHelper.canBeWrapped():
                        methodIndex = i
                        break

                # if it is still None then we didn't find anything
                if methodIndex is None:
                    raise TypeError("method %s of %s cannot be wrapped" % (methodName, apiClassName))

        self.methodInfo = apiClassInfo[apiClassName]['methods'][methodName][methodIndex]
        self.methodIndex = methodIndex

    def iterArgs(self, inputs=True, outputs=True, infoKeys=[]):
        res = []
        for argname, argtype, direction in self.methodInfo['args']:

            if direction == 'in':
                if not inputs:
                    continue
            else:
                if not outputs:
                    continue

            if infoKeys:
                arg_res = [argname]
                argInfo = self.methodInfo['argInfo'][argname]
                for key in infoKeys:
                    arg_res.append(argInfo[key])
            else:
                arg_res = argname
            res.append(arg_res)
        return res

    def inArgs(self):
        # type: () -> List[str]
        return self.methodInfo['inArgs']

    def outArgs(self):
        # type: () -> List[str]
        return self.methodInfo['outArgs']

    def argList(self):
        # type: () -> List[str]
        return self.methodInfo['args']

    def argInfo(self):
        return self.methodInfo['argInfo']

    def getGetterInfo(self):
        # type: () -> Optional[ApiArgUtil]
        """
        Return an ApiArgUtil for the getter method
        (assumes the current instance is the setter)

        Returns
        -------
        Optional[ApiArgUtil]
        """
        try:
            inverse, isgetter = self.methodInfo['inverse']
            if isgetter:
                if hasattr(getattr(api, self.apiClassName), inverse):
                    return ApiArgUtil(self.apiClassName, inverse, self.methodIndex)
        except:
            pass

    @staticmethod
    def isValidEnum(enumTuple):
        if enumTuple[0] in apiClassInfo and \
                enumTuple[1] in apiClassInfo[enumTuple[0]]['enums']:
            return True
        return False

    def hasOutput(self):
        if self.methodInfo['outArgs'] or self.methodInfo['returnType']:
            return True
        return False

    def canBeWrapped(self):
        defaults = self.methodInfo['defaults']
        #argList = methodInfo['args']
        returnType = self.methodInfo['returnType']
        # ensure that we can properly cast all the args and return values
        try:
            if returnType is not None:
                # Enum: ensure existence
                if isinstance(returnType, tuple):
                    assert self.isValidEnum(returnType), '%s.%s(): invalid return enum: %s' % (self.apiClassName, self.methodName, returnType)

                # Other: ensure we can cast result
                else:
                    assert returnType in ApiTypeRegister.outCast or \
                        returnType == self.apiClassName, \
                        '%s.%s(): invalid return type: %s' % (self.apiClassName, self.methodName, returnType)

            for argname, argtype, direction in self.methodInfo['args']:
                # Enum
                if isinstance(argtype, tuple):
                    assert self.isValidEnum(argtype), '%s.%s(): %s: invalid enum: %s' % (self.apiClassName, self.methodName, argname, argtype)

                # Input
                else:
                    if direction == 'in':
                        assert argtype in ApiTypeRegister.inCast or \
                            argname in defaults or \
                            argtype == self.apiClassName, \
                            '%s.%s(): %s: invalid input type %s' % (self.apiClassName, self.methodName, argname, argtype)

                        # if argname in ['instance', 'instanceNumber']: print '%s.%s(): %s: %r' % (self.apiClassName, self.methodName, argname, argtype)
                    # Output
                    elif direction == 'out':
                        assert argtype in ApiTypeRegister.refInit and argtype in ApiTypeRegister.refCast, '%s.%s(): %s: invalid output type %s' % (self.apiClassName, self.methodName, argname, argtype)
                        # try:
                        #    assert argtype.type() in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
                        # except AttributeError:
                        #    assert argtype in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
                    else:
                        # in+out, or something else weird...
                        return False
        except AssertionError as msg:
            #_logger.debug( str(msg) )
            return False

        #_logger.debug("%s: valid" % self.getPrototype())
        return True

#    def castEnum(self, argtype, input ):
#        if isinstance( input, int):
#            return input
#
#        elif input[0] != 'k' or not input[1].isupper():
#            input = 'k' + util.capitalize(input)
#            return apiClassInfo[argtype[0]]['enums'][argtype[1]].index(input)

    def getInputTypes(self):
        # type: () -> List[str]
        inArgs = self.methodInfo['inArgs']
        types = self.methodInfo['types']
        return [str(types[x]) for x in inArgs]

    def getOutputTypes(self):
        # type: () -> List[str]
        ret = self.methodInfo['returnType']
        if ret is None:
            ret = []
        else:
            ret = [str(ret)]

        outArgs = self.methodInfo['outArgs']
        types = self.methodInfo['types']
        return ret + [str(types[x]) for x in outArgs]

    def getReturnType(self):
        return self.methodInfo['returnType']

    def getPymelName(self):
        pymelName = self.basePymelName
        try:
            pymelClassName = apiClassNamesToPyNodeNames[self.apiClassName]
        except KeyError:
            pass
        else:
            pymelName = _getApiOverrideNameAndData(pymelClassName, pymelName)[0]
        return pymelName

    def getMethodDocs(self):
        return self.methodInfo['doc']

    def getPrototype(self, className=True, methodName=True, outputs=False,
                     defaults=False):
        inArgs = self.inArgs()
        outArgs = self.outArgs()
        returnType = self.getReturnType()
        types = self.methodInfo['types']
        args = []

        for x in inArgs:
            arg = str(types[x]) + ' ' + x
            if defaults:
                try:
                    arg += '=' + str(self.methodInfo['defaults'][x])
                except KeyError:
                    pass
            args.append(arg)

        proto = "(%s)" % (', '.join(args))
        if methodName:
            proto = self.methodName + proto
            if className:
                proto = self.apiClassName + '.' + proto

        if outputs:
            results = []
            if returnType:
                results.append(returnType)
            for x in outArgs:
                results.append(types[x])

            if len(results) == 1:
                proto += ' --> ' + str(results[0])
            elif len(results):
                proto += ' --> (%s)' % ', '.join([str(x) for x in results])
        return proto

    def getTypeComment(self):
        inArgs = self.inArgs()
        outArgs = self.outArgs()
        returnType = self.getReturnType()
        types = self.methodInfo['types']
        args = []

        pymelClass = apiClassNamesToPymelTypes.get(self.apiClassName)
        if pymelClass is None:
            currentModule = 'pymel.core.nodetypes'
        else:
            currentModule = pymelClass.__module__

        def toPymelType(apiName):
            moduleName = None

            pymelType = apiClassNamesToPymelTypes.get(apiName, None)
            if pymelType is not None:
                moduleName = pymelType.__module__
                pymelName = pymelType.__name__
            else:
                try:
                    pymelName = ApiTypeRegister.types[apiName]
                except KeyError:
                    match = re.match('^(?:(MIt)|(MFn)|(M))([A-Z]+.*)', apiName)
                    assert match is not None, apiName
                    isGeneral, isNode, isData, pymelName = match.groups()

                    if pymelName == 'Attribute':
                        moduleName = 'pymel.core.general'
                    elif isGeneral:
                        moduleName = 'pymel.core.general'
                    elif isNode:
                        moduleName = 'pymel.core.nodetypes'
                    elif isData:
                        moduleName = 'pymel.core.datatypes'
                else:
                    if isinstance(pymelName, tuple):
                        pymelName = 'Tuple[%s]' % ', '.join(pymelName)
                    else:
                        moduleName, pymelName = pymelName.rsplit('.', 1)

            if moduleName == 'pymel.core.nodetypes' and currentModule != 'pymel.core.nodetypes':
                return 'nt.' + pymelName
            if moduleName == 'pymel.core.datatypes' and currentModule != 'pymel.core.datatypes':
                return 'datatypes.' + pymelName
            if moduleName == 'pymel.core.general' and currentModule != 'pymel.core.general':
                return 'general.' + pymelName
            return pymelName

        def getType(apiName):

            arrayType = ApiTypeRegister.arrayItemTypes.get(apiName)
            if arrayType:
                try:
                    pymelName = toPymelType(arrayType.__name__)
                except AssertionError:
                    pymelName = arrayType.__name__
                return 'List[%s]' % pymelName
            else:
                pymelName = toPymelType(str(apiName))
            return pymelName

        for x in inArgs:
            if types[x] == 'MAnimCurveChange':
                continue
            args.append(getType(types[x]))

        comment = '# type: (%s)' % ', '.join(args)

        results = []
        if returnType:
            results.append(getType(returnType))
        for x in outArgs:
            results.append(getType(types[x]))

        if len(results) == 1:
            result = results[0]
        elif len(results):
            result = 'Tuple[%s]' % ', '.join(results)
        else:
            result = 'None'
        return comment + ' -> ' + result

    def castInput(self, argName, input):
        # type: (str, Any) -> Any
        """
        Parameters
        ----------
        argName : str
        input : Any

        Returns
        -------
        Any
        """
        # enums
        argtype = self.methodInfo['types'][argName]
        info = self.methodInfo['argInfo'][argName]
        unit = info.get('unitType', None)
        return self._castInput(input, argtype, unit)

    @classmethod
    def _castInput(cls, input, argtype, unit=None):
        if isinstance(argtype, tuple):
            # convert enum as a string or int to an int

            # if isinstance( input, int):
            #    return input

            apiClassName, enumName = argtype
            return cls.castInputEnum(apiClassName, enumName, input)

        elif input is not None:
            f = ApiTypeRegister.inCast[argtype]
            if f is None:
                return input

            input = cls.toInternalUnits(input, unit)
            return f(input)

    @classmethod
    def castInputEnum(cls, apiClassName, enumName, input):
        # pymelEnums should now have both api key names ("kPostTransform") and
        # pymel names ("postTransform") available as keys now, with the pymel
        # form the default... so only need to check pymelEnum, not
        #  apiClassInfo[apiClassName]['enums'][enumName]['values'].getIndex(input)
        try:
            return apiClassInfo[apiClassName]['pymelEnums'][enumName].getIndex(input)
        except ValueError:
            raise ValueError("expected an enum of type %s.%s: got %r" % (apiClassName, enumName, input))

    @staticmethod
    def fromInternalUnits(result, returnType, unit=None):
        #_logger.debug(unit)
        if unit == 'linear' or returnType in ('MPoint', 'MFloatPoint'):
            unitCast = ApiTypeRegister.outCast['MDistance']
            if util.isIterable(result):
                result = [unitCast(None, val) for val in result]
            else:
                result = unitCast(None, result)
        elif unit == 'angular':
            #_logger.debug("angular")
            unitCast = ApiTypeRegister.outCast['MAngle']
            if util.isIterable(result):
                result = [unitCast(None, val) for val in result]
            else:
                result = unitCast(None, result)
        return result

    @staticmethod
    def toInternalUnits(input, unit):
        # units
        if unit == 'linear':
            #_logger.debug("setting linear")
            unitCast = ApiTypeRegister.inCast['MDistance']
            if util.isIterable(input):
                input = [unitCast(val).asInternalUnit() for val in input]
            else:
                input = unitCast(input).asInternalUnit()

        elif unit == 'angular':
            #_logger.debug("setting angular")
            unitCast = ApiTypeRegister.inCast['MAngle']
            if util.isIterable(input):
                input = [unitCast(val).asInternalUnit() for val in input]
            else:
                input = unitCast(input).asInternalUnit()

        return input

    def castResult(self, pynodeInstance, result):
        returnType = self.methodInfo['returnType']
        if returnType:
            return self._castResult(pynodeInstance, result, returnType,
                                    self.methodInfo['returnInfo'].get('unitType', None))

    @classmethod
    def _castResult(cls, pynodeInstance, result, returnType, unitType):
        if returnType:
            # special case check - some functions return an MObject, but return
            # an empty/null MObject if no node was found - ie, MFnCharacter.getClipScheduler
            # In these cases, return None...
            if (returnType == 'MObject' and isinstance(result, api.MObject)
                    and result.isNull()):
                return None

            # enums
            if isinstance(returnType, tuple):
                #raise NotImplementedError
                apiClassName, enumName = returnType
                try:
                    # TODO: return EnumValue type
                    # convert int result into pymel string name.
                    return getattr(apiClassNamesToPymelTypes[apiClassName], enumName)[result]
                except KeyError:
                    raise ValueError("expected an enum of type %s.%s" %
                                     (apiClassName, enumName))

            else:
                # try:
                f = ApiTypeRegister.outCast[returnType]
                if f is None:
                    return result

                # FIXME: confirm this!!!
                # I believe methodInfo['returnInfo']['type'] is always the
                # same as returnType = self.methodInfo['returnType'], but the
                # old logic would use methodInfo['returnInfo']['type'], and I'm
                # paranoid...
                result = cls.fromInternalUnits(result,
                                               returnType=returnType,
                                               unit=unitType)

                return f(pynodeInstance, result)
#                except:
#                    cls = instance.__class__
#                    if returnType != cls.__name__:
#                        raise TypeError, "Cannot cast a %s to %s" % ( type(result).__name__, returnType )
#                    return cls(result)

    @staticmethod
    def initReference(argtype):
        return ApiTypeRegister.refInit[argtype]()

    @classmethod
    def castReferenceResult(cls, argtype, outArg):
        # special case check - some functions return an MObject, but return
        # an empty/null MObject if no node was found - ie, MFnContainer.getParentContainer
        # In these cases, return None...
        if (argtype == 'MObject' and isinstance(outArg, api.MObject)
                and outArg.isNull()):
            return None

        f = ApiTypeRegister.refCast[argtype]
        #_logger.debug("castReferenceResult")
        #_logger.debug( "%s %s %s" % (f, argtype, outArg) )
        if f is None:
            return outArg

        result = cls.fromInternalUnits(outArg, argtype)
        return f(result)

    def getDefaults(self):
        "get a list of defaults"
        defaults = []
        defaultInfo = self.methodInfo['defaults']
        inArgs = self.methodInfo['inArgs']
        argInfo = self.argInfo()
        nargs = len(inArgs)
        for arg in inArgs:
            if argInfo[arg]['type'] == 'MAnimCurveChange':
                continue

            if arg in defaultInfo:
                default = defaultInfo[arg]
            else:
                continue

            if isinstance(default, apicache.ApiEnum):
                # convert enums from apiName to pymelName. the default will be the readable string name
                apiClassName, enumName, enumValue = default
                try:
                    enumList = apiClassInfo[apiClassName]['enums'][enumName]['values']
                except KeyError:
                    _logger.warning("Could not find enumerator %s", default)
                else:
                    index = enumList.getIndex(enumValue)
                    default = apiClassInfo[apiClassName]['pymelEnums'][enumName][index]
            defaults.append(default)

        return defaults

    def isStatic(self):
        return self.methodInfo['static']

    def isDeprecated(self):
        return self.methodInfo.get('deprecated', False)


class ApiUndo(with_metaclass(util.Singleton, object)):

    """
    this is based on a clever prototype that Dean Edmonds posted on python_inside_maya
    awhile back.  it works like this:

        - using the API, create a garbage node with an integer attribute,
          lock it and set it not to save with the scene.
        - add an API callback to the node, so that when the special attribute
          is changed, we get a callback
        - the API queue is a list of simple python classes with undoIt and
          redoIt methods.  each time we add a new one to the queue, we increment
          the garbage node's integer attribute using maya.cmds.
        - when maya's undo or redo is called, it triggers the undoing or
          redoing of the garbage node's attribute change (bc we changed it using
          MEL/maya.cmds), which in turn triggers our API callback.  the callback
          runs the undoIt or redoIt method of the class at the index taken from
          the numeric attribute.

    """

    def __init__(self):
        self.node_name = '__pymelUndoNode'
        self.cb_enabled = True
        self.undo_queue = []
        self.redo_queue = []
        self.undoStateCallbackId = None

    def installUndoStateCallbacks(self):
        # Unfortunately, I couldn't find any callback that is triggered directly
        # when the undo state is changed or flushed; however, we can get a
        # callback to trigger whenever there is nothing to do or undo, which
        # is nearly as good...

        # First we set up a condition that should trip whenever there are no
        # undos or redos available...

        # alas, the condition command doesn't seem to work with python...
        # ...and it seems that in 2014, cmds.eval doesn't always work (??)...
        # so use api.MGlobal.executeCommand instead...
        api.MGlobal.executeCommand('''
        global proc int _pymel_undoOrRedoAvailable()
        {
            return (isTrue("UndoAvailable") || isTrue("RedoAvailable"));
        }
        ''', False, False)
        cmds.condition('UndoOrRedoAvailable', initialize=True,
                       d=['UndoAvailable', 'RedoAvailable',
                          # strictly speaking, we shouldn't need these three
                          # dependencies, but there's a bug with setting of
                          # UndoOrRedoAvailable + opening a new file... see
                          # test_mayaBugs::TestUndoRedoConditionNewFile
                          'newing', 'readingFile', 'opening'],
                       s='_pymel_undoOrRedoAvailable')

        # Now, we install our callback...
        id = api.MConditionMessage.addConditionCallback('UndoOrRedoAvailable',
                                                        self.flushCallback)
        self.undoStateCallbackId = id

    def flushCallback(self, undoOrRedoAvailable, *args):
        if undoOrRedoAvailable:
            return

        # we're trying to detect flush events, either from calling flush, or
        # from disabling undos... so, basically, we just check to see if there
        # is nothing in the undo / redo queue, and if so, we assume there was
        # a flush!
        if not (cmds.undoInfo(q=1, undoQueueEmpty=1)
                and cmds.undoInfo(q=1, redoQueueEmpty=1)):
            return

        # ok, looks like there was a flush...
        self.flushUndo()

    def _attrChanged(self, msg, plug, otherPlug, data):
        if self.cb_enabled\
           and (msg & api.MNodeMessage.kAttributeSet != 0) \
           and (plug == self.cmdCountAttr):

            #            #count = cmds.getAttr(self.node_name + '.cmdCount')
            #            #print count
            if api.MGlobal.isUndoing():
                # cmds.undoInfo(state=0)
                self.cb_enabled = False
                try:
                    cmdObj = self.undo_queue.pop()
                    cmdObj.undoIt()
                    self.redo_queue.append(cmdObj)
                finally:
                    # cmds.undoInfo(state=1)
                    self.cb_enabled = True

            elif api.MGlobal.isRedoing():
                # cmds.undoInfo(state=0)
                self.cb_enabled = False
                try:
                    cmdObj = self.redo_queue.pop()
                    cmdObj.redoIt()
                    self.undo_queue.append(cmdObj)
                finally:
                    # cmds.undoInfo(state=1)
                    self.cb_enabled = True

    def _createNode(self):
        """
        Create the undo node.

        Any type of node will do. I've chosen a 'facade' node since it
        doesn't have too much overhead and won't get deleted if the user
        optimizes the scene.

        Note that we don't want to use Maya commands here because they
        would pollute Maya's undo queue, so we use API calls instead.
        """

        ns = api.MNamespace.currentNamespace()
        api.MNamespace.setCurrentNamespace(':')
        self.flushUndo()

        dgmod = api.MDGModifier()
        self.undoNode = dgmod.createNode('facade')
        dgmod.renameNode(self.undoNode, self.node_name)
        dgmod.doIt()

        api.MNamespace.setCurrentNamespace(ns)

        # Add an attribute to keep a count of the commands in the stack.
        attrFn = api.MFnNumericAttribute()
        self.cmdCountAttr = attrFn.create('cmdCount', 'cc',
                                          api.MFnNumericData.kInt
                                          )

        nodeFn = api.MFnDependencyNode(self.undoNode)
        self.node_name = nodeFn.name()
        nodeFn.addAttribute(self.cmdCountAttr)

        nodeFn.setDoNotWrite(True)
        nodeFn.setLocked(True)

        try:
            api.MMessage.removeCallback(self.cbid)
            if hasattr(self.cbid, 'disown'):
                self.cbid.disown()
        except:
            pass
        self.cbid = api.MNodeMessage.addAttributeChangedCallback(self.undoNode, self._attrChanged)

    def append(self, cmdObj, undoName=None):
        if not self.undoStateCallbackId:
            self.installUndoStateCallbacks()

        assert undoName is None or isinstance(undoName, str)

        if not cmds.undoInfo(q=1, state=1):
            # if undo is off, don't add to the undo queue
            return

        self.cb_enabled = False
        try:
            # Increment the undo node's command count. We want this to go into
            # Maya's undo queue because changes to this attr will trigger our own
            # undo/redo code.
            try:
                count = cmds.getAttr(self.node_name + '.cmdCount')
            except Exception:
                if not cmds.objExists(self.node_name):
                    self._createNode()
                    count = cmds.getAttr(self.node_name + '.cmdCount')
                else:
                    raise

            if undoName is not None:
                cmds.undoInfo(openChunk=1, chunkName=undoName)
            try:
                cmds.setAttr(self.node_name + '.cmdCount', count + 1)
            finally:
                if undoName is not None:
                    cmds.undoInfo(closeChunk=1)

            # Append the command to the end of the undo queue.
            self.undo_queue.append(cmdObj)

            # Clear the redo queue.
            self.redo_queue = []
        finally:
            # Re-enable the callback.
            self.cb_enabled = True

    def execute(self, cmdObj, *args):
        # Execute the command object's 'doIt' method.
        res = cmdObj.doIt(*args)
        self.append(cmdObj)
        return res

    def flushUndo(self, *args):
        self.undo_queue = []
        self.redo_queue = []


apiUndo = ApiUndo()


class ApiUndoItem(object):

    """A simple class that reprsents an undo item to be undone or redone."""
    __slots__ = ['_setter', '_redo_args', '_undo_args', '_redo_kwargs',
                 '_undo_kwargs']

    def __init__(self, setter, redoArgs, undoArgs, redoKwargs=None,
                 undoKwargs=None):
        self._setter = setter
        self._redo_args = redoArgs
        self._undo_args = undoArgs
        if redoKwargs is None:
            redoKwargs = {}
        self._redo_kwargs = redoKwargs
        if undoKwargs is None:
            undoKwargs = {}
        self._undo_kwargs = undoKwargs

    def __repr__(self):
        args = [self._setter, self._redo_args, self._undo_args]
        args = [repr(x) for x in args]
        if self._redo_kwargs:
            args.append('redoKwargs={!r}'.format(self._redo_kwargs))
        if self._undo_kwargs:
            args.append('undoKwargs={!r}'.format(self._undo_kwargs))
        return '{}({})'.format(type(self).__name__, ', '.join(args))

    def redoIt(self):
        self._setter(*self._redo_args, **self._redo_kwargs)
    doIt = redoIt

    def undoIt(self):
        self._setter(*self._undo_args, **self._undo_kwargs)


class ApiRedoUndoItem(ApiUndoItem):

    """
    Similar to the base ApiUndoItem, but allows specifying a separate
    function for the redoer and the undoer
    """
    __slots__ = ['_undoer']

    def __init__(self, redoer, redoArgs, undoer, undoArgs, redoKwargs=None,
                 undoKwargs=None):
        super(ApiRedoUndoItem, self).__init__(redoer, redoArgs, undoArgs,
                                              redoKwargs=redoKwargs,
                                              undoKwargs=undoKwargs)
        self._undoer = undoer

    def __repr__(self):
        args = [self._setter, self._redo_args, self._undoer, self._undo_args]
        args = [repr(x) for x in args]
        if self._redo_kwargs:
            args.append('redoKwargs={!r}'.format(self._redo_kwargs))
        if self._undo_kwargs:
            args.append('undoKwargs={!r}'.format(self._undo_kwargs))
        return '{}({})'.format(type(self).__name__, ', '.join(args))


    def undoIt(self):
        self._undoer(*self._undo_args, **self._undo_kwargs)


class MAnimCurveChangeUndoItem(ApiRedoUndoItem):
    """
    Specialization of ApiRedoUndoItem for MAnimCurveChange objects.

    Basically just removes some boilerplate for construction of an
    ApiRedoUndoItem from an MAnimCurveChange object
    """
    __slots__ = ['_curveChange']

    def __init__(self, curveChangeObj):
        super(MAnimCurveChangeUndoItem, self).__init__(
            curveChangeObj.redoIt, (), curveChangeObj.undoIt, ())
        self._curveChange = curveChangeObj

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self._curveChange)


_DEBUG_API_WRAPS = False
if _DEBUG_API_WRAPS:
    _apiMethodWraps = {}


def getUndoArgs(args, argList, getter, getterInArgs):
    # type: (List[Any], List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]], Callable, List[str]) -> List[Any]
    """
    Parameters
    ----------
    args : List[Any]
        argument values
    argList : List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]
    getter : Callable
        get function
    getterInArgs : List[str]

    Returns
    -------
    List[Any]
    """
    getterArgs = []  # args required to get the current state before setting it
    undo_args = []  # args required to reset back to the original (starting) state  ( aka "undo" )
    missingUndoIndices = []  # indices for undo args that are not shared with the setter and which need to be filled by the result of the getter
    inCount = 0
    for name, argtype, direction, unit in argList:
        if direction == 'in':
            arg = args[inCount]
            undo_args.append(arg)
            if name in getterInArgs:
                # gather up args that are required to get the current value we are about to set.
                # these args are shared between getter and setter pairs
                getterArgs.append(arg)
                # undo_args.append(arg)
            else:
                # store the indices for
                missingUndoIndices.append(inCount)
                # undo_args.append(None)
            inCount += 1

    try:
        getterResult = getter(*getterArgs)
    except RuntimeError:
        _logger.error("the arguments at time of error were %r" % getterArgs)
        raise

    # when a command returns results normally and passes additional outputs by
    # reference, the result is returned as a tuple otherwise, always as a list
    if not isinstance(getterResult, tuple):
        getterResult = (getterResult,)

    for index, result in zip(missingUndoIndices, getterResult):
        undo_args[index] = result
    return undo_args


def getDoArgs(args, argList):
    # type: (List[Any], List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]) -> Tuple[List[Any], List[Any], List[Tuple[str, int]]]
    """
    Parameters
    ----------
    args : List[Any]
        argument values
    argList : List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]

    Returns
    -------
    do_args : List[Any]
    final_do_args : List[Any]
        Arguments prepped to be passed to the API method.
        Same as above but with SafeApiPtr converted
    out_type_list : List[Tuple[str, int]]
        list of (argument type, index)
    """
    do_args = []
    final_do_args = []
    outTypeList = []
    inCount = totalCount = 0
    for _, argtype, direction, unit in argList:
        if direction == 'in':
            if argtype == 'MAnimCurveChange':
                arg = api.MAnimCurveChange()
            else:
                arg = ApiArgUtil._castInput(args[inCount], argtype, unit)
                inCount += 1
        else:
            arg = ApiArgUtil.initReference(argtype)
            outTypeList.append((argtype, totalCount))
            # outTypeIndex.append( totalCount )
        do_args.append(arg)
        # Do final SafeApiPtr => 'true' ptr conversion
        if isinstance(arg, api.SafeApiPtr):
            final_do_args.append(arg())
        else:
            final_do_args.append(arg)
        totalCount += 1
    return do_args, final_do_args, outTypeList


# FIXME: if we reframe getterInArgs as a set of indices, then we can omit the argument names in generated functions, which are quite long
def getDoArgsGetterUndo(args, argList, getter, setter, getterInArgs):
    # type: (List[Any], List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]], Callable, Callable, List[str]) -> Tuple[List[Any], List[Any], List[Tuple[str, int]], ApiUndoItem]
    """
    Parameters
    ----------
    args : List[Any]
        argument values
    argList : List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]
    getter : Callable
        get function
    setter : Callable
        set function
    getterInArgs : List[str]
        list of argument names that are used to get the initial state when
        a method is undoable.

    Returns
    -------
    do_args : List[Any]
    final_do_args : List[Any]
        Same as above but with SafeApiPtr converted
    outTypeList : List[Tuple[str, int]]
        list of (argument type, index), used by processApiResult to retrieve
        output values from do_args
    undoItem : ApiUndoItem
    """
    undoEnabled = cmds.undoInfo(q=1, state=1) and apiUndo.cb_enabled

    # get the value we are about to set
    if undoEnabled:
        undo_args = getUndoArgs(args, argList, getter, getterInArgs)

    do_args, final_do_args, outTypeList = getDoArgs(args, argList)

    if undoEnabled:
        undoItem = ApiUndoItem(setter, do_args, undo_args)
    else:
        undoItem = None
    return do_args, final_do_args, outTypeList, undoItem


def getDoArgsAnimCurveUndo(args, argList):
    # type: (List[Any], List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]) -> Tuple[List[Any], List[Any], List[Tuple[str, int]], ApiUndoItem]
    """
    Parameters
    ----------
    args : List[Any]
        argument values
    argList : List[Tuple[str, Union[str, Tuple[str, str]], str, Optional[str]]]

    Returns
    -------
    do_args : List[Any]
    final_do_args : List[Any]
        Arguments prepped to be passed to the API method.
        Same as above but with SafeApiPtr converted
    out_type_list : List[Tuple[str, int]]
        list of (argument type, index)
    undoItem : ApiUndoItem
    """
    undoEnabled = cmds.undoInfo(q=1, state=1) and apiUndo.cb_enabled

    do_args, final_do_args, outTypeList = getDoArgs(args, argList)

    if undoEnabled:
        # find the position of the curve change arg...
        inArgIndex = 0
        curveChangeIndex = 0
        for argName, argType, direction, unit in argList:
            if direction == 'in':
                if argType == 'MAnimCurveChange':
                    curveChangeIndex = inArgIndex
                    break
                inArgIndex += 1
        else:
            raise RuntimeError("Could not find input MAnimCurveChange argument"
                               " in arglist: {}".format(argList))
        curveChange = do_args[curveChangeIndex]
        undoItem = MAnimCurveChangeUndoItem(curveChange)
    else:
        undoItem = None
    return do_args, final_do_args, outTypeList, undoItem


def processApiResult(result, outTypeList, do_args):
    # type: (Any, List[Tuple[str, int]], List[Any]) -> Any
    """
    Parameters
    ----------
    result : Any
        Result returned from the API method
    outTypeList : List[Tuple[str, int]]
        output argument types and their indices.  should be same len as outArgs
    do_args : List[Any]

    Returns
    -------
    Any
    """
    if len(outTypeList):
        if result is not None:
            result = [result]
        else:
            result = []

        for outType, index in outTypeList:
            outArgVal = do_args[index]
            res = ApiArgUtil.castReferenceResult(outType, outArgVal)
            result.append(res)

        if len(result) == 1:
            result = result[0]
        else:
            result = tuple(result)
    return result


def getProxyResult(self, apiClass, method, final_do=()):
    mfn = self.__apimfn__()
    if not isinstance(mfn, apiClass):
        mfn = apiClass(self.__apiobject__())
    return getattr(apiClass, method)(mfn, *final_do)


def wrapApiMethod(apiClass, methodName, newName=None, proxy=True, overloadIndex=None):
    # type: (Type, str, str, bool, Optional[int]) -> None
    """
    create a wrapped, user-friendly API method that works the way a python method should: no MScriptUtil and
    no special API classes required.  Inputs go in the front door, and outputs come out the back door.


    Regarding Undo
    --------------

    The API provides many methods which are pairs -- one sets a value
    while the other one gets the value.  the naming convention of these
    methods follows a fairly consistent pattern.  so what I did was
    determine all the get and set pairs, which I can use to automatically
    register api undo items:  prior to setting something, we first *get*
    it's existing value, which we can later use to reset when undo is
    triggered.

    This API undo is only for PyMEL methods which are derived from API
    methods.  it's not meant to be used with plugins.  and since it just
    piggybacks maya's MEL undo system, it won't get cross-mojonated.

    Take `MFnTransform.setTranslation`, for example. PyMEL provides a wrapped copy of this as
    `Transform.setTranslation`.   when pymel.Transform.setTranslation is
    called, here's what happens in relation to undo:

        #. process input args, if any
        #. call MFnTransform.getTranslation() to get the current translation.
        #. append to the api undo queue, with necessary info to undo/redo
           later (the current method, the current args, and the current
           translation)
        #. call MFnTransform.setTranslation() with the passed args
        #. process result and return it


    Parameters
    ----------
    apiClass : Type
        the api class
    methodName : str
        the name of the api method
    newName : str
        optionally provided if a name other than that of api method is desired
    proxy : bool
        If True, then __apimfn__ function used to retrieve the proxy class. If False,
        then we assume that the class being wrapped inherits from the underlying api class.
    overloadIndex : Optional[int]
        which of the overloaded C++ signatures to use as the basis of our wrapped function.
    """

    #getattr( api, apiClassName )

    apiClassName = apiClass.__name__
    try:
        method = getattr(apiClass, methodName)
    except AttributeError:
        return

    argHelper = ApiArgUtil(apiClassName, methodName, overloadIndex)
    undoable = True  # controls whether we print a warning in the docs

    if newName is None:
        pymelName = argHelper.getPymelName()
    else:
        pymelName = newName

    if not argHelper.canBeWrapped():
        return

    if argHelper.isDeprecated():
        _logger.debug("%s.%s is deprecated" % (apiClassName, methodName))

    argInfo = argHelper.methodInfo['argInfo']

    def getUnit(n):
        return argInfo[n].get('unitType', None)

    inArgs = argHelper.inArgs()
    outArgs = argHelper.outArgs()
    argList = [(name, typ, dir, getUnit(name))
               for name, typ, dir in argHelper.argList()]

    getterArgHelper = argHelper.getGetterInfo()

    if argHelper.hasOutput():
        getterInArgs = []
        # query method ( getter )
        # if argHelper.getGetterInfo() is not None:

        # temporarily supress this warning, until we get a deeper level
#            if getterArgHelper is not None:
#                _logger.warning( "%s.%s has an inverse %s, but it has outputs, which is not allowed for a 'setter'" % (
#                                                                            apiClassName, methodName, getterArgHelper.methodName ) )

    else:
        # edit method ( setter )
        if getterArgHelper is None:
            #_logger.debug( "%s.%s has no inverse: undo will not be supported" % ( apiClassName, methodName ) )
            getterInArgs = []
            undoable = False
        else:
            getterInArgs = getterArgHelper.inArgs()

    # create the function
    def wrappedApiFunc(self, *args):

        if len(args) != len(inArgs):
            raise TypeError("%s() takes exactly %s arguments (%s given)" %
                            (methodName, len(inArgs), len(args)))

        undoEnabled = getterArgHelper is not None and cmds.undoInfo(q=1, state=1) and apiUndo.cb_enabled

        # get the value we are about to set
        if undoEnabled:
            getter = getattr(self, getterArgHelper.getPymelName())
            undo_args = getUndoArgs(args, argList, getter, getterInArgs)

        do_args, final_do_args, outTypeList = getDoArgs(args, argList)

        if undoEnabled:
            setter = getattr(self, pymelName)
            undoItem = ApiUndoItem(setter, do_args, undo_args)
            apiUndo.append(undoItem)

        if argHelper.isStatic():
            result = method(*final_do_args)
        elif proxy:
            # due to the discrepancies between the API and Maya node
            # hierarchies, our __apimfn__ might not be a subclass of the api
            # class being wrapped, however, the api object can still be used
            # with this mfn explicitly.
            mfn = self.__apimfn__()
            if not isinstance(mfn, apiClass):
                mfn = apiClass(self.__apiobject__())
            result = method(mfn, *final_do_args)
        else:
            result = method(self, *final_do_args)

        result = argHelper.castResult(self, result)
        return processApiResult(result, outArgs, outTypeList, do_args)

    wrappedApiFunc.__name__ = pymelName

    _addApiDocs(wrappedApiFunc, apiClass, methodName, overloadIndex, undoable)

    # format EnumValue defaults
    defaults = []
    for default in argHelper.getDefaults():
        if isinstance(default, util.EnumValue):
            defaults.append(str(default))
        else:
            defaults.append(default)

    if defaults:
        pass
        #_logger.debug("defaults: %s" % defaults)

    wrappedApiFunc = util.interface_wrapper(
        wrappedApiFunc, ['self'] + inArgs, defaults=defaults)
    wrappedApiFunc._argHelper = argHelper

    global _DEBUG_API_WRAPS
    if _DEBUG_API_WRAPS:
        import weakref
        global _apiMethodWraps
        classWraps = _apiMethodWraps.setdefault(apiClassName, {})
        methodWraps = classWraps.setdefault(methodName, [])
        methodWraps.append({'index': argHelper.methodIndex,
                            'funcRef': weakref.ref(wrappedApiFunc),
                            })

    # do the debug stuff before turning into a classmethod, because you
    # can't create weakrefs of classmethods (don't ask me why...)
    if argHelper.isStatic():
        wrappedApiFunc = classmethod(wrappedApiFunc)

    if argHelper.isDeprecated():
        wrappedApiFunc = deprecated(wrappedApiFunc)
    return wrappedApiFunc


def addApiDocs(apiClass, methodName, overloadIndex=None, undoable=True):
    """decorator for adding API docs"""

    def doc_decorator(func):
        return _addApiDocs(func, apiClass, methodName, overloadIndex, undoable)

    return doc_decorator


def _addApiDocs(wrappedApiFunc, apiClass, methodName, overloadIndex=None,
                undoable=True):
    # apiClass may be None if we try to wrap a class that doesn't exist in this
    # version of maya
    if apiClass is not None:
        util.addLazyDocString(wrappedApiFunc, addApiDocsCallback, apiClass,
                              methodName, overloadIndex, undoable,
                              wrappedApiFunc.__doc__)
    return wrappedApiFunc


def addApiDocsCallback(apiClass, methodName, overloadIndex=None, undoable=True,
                       origDocstring=''):
    apiClassName = apiClass.__name__

    try:
        argHelper = ApiArgUtil(apiClassName, methodName, overloadIndex)
    except ApiMethodMissingError as e:
        # % formatter deals with unicode, but keeps strings str if not unicode
        return '%s' % e

    inArgs = argHelper.inArgs()
    outArgs = argHelper.outArgs()
    argList = argHelper.argList()
    argInfo = argHelper.argInfo()

    def formatDocstring(typ):
        """
        convert
        "['one', 'two', 'three', ['1', '2', '3']]"
        to
        "[`one`, `two`, `three`, [`1`, `2`, `3`]]"
        """
        if not isinstance(typ, (list, tuple)):
            pymelType = ApiTypeRegister.getPymelType(typ, allowGuess=False)
            if pymelType is None:
                pymelType = typ
        else:
            pymelType = typ

        if isinstance(pymelType, apicache.ApiEnum):
            pymelType = pymelType.pymelName()

        pymelType = repr(pymelType)  # .replace("'", "`")
        if typ in list(ApiTypeRegister.arrayItemTypes.keys()):
            pymelType = 'List[%s]' % pymelType
        return pymelType

    # Docstrings
    docstring = argHelper.getMethodDocs()
    # api is no longer in specific units, it respect UI units like MEL
    docstring = docstring.replace('centimeter', 'linear unit')
    docstring = docstring.replace('radian', 'angular unit')

    S = '    '
    if len(inArgs):
        docstring += '\n\n' + docBuilderCls.section('Parameters')
        for name in inArgs:
            info = argInfo[name]
            typ = info['type']
            typeStr = formatDocstring(typ)

            docstring += '%s : %s\n' % (name, typeStr)
            docstring += S + '%s\n' % (info['doc'])
            if isinstance(typ, apicache.ApiEnum):
                apiClassName, enumName = typ
                enumValues = apiClassInfo[apiClassName]['pymelEnums'][enumName].keys()
                docstring += '\n' + S + 'values: %s\n' % ', '.join(
                    ['%r' % x for x in enumValues
                     if x not in ['invalid', 'last']])

    # Results doc strings
    results = []
    returnType = argHelper.getReturnType()
    if returnType:
        rtype = formatDocstring(returnType)
        results.append(rtype)
    for argname in outArgs:
        rtype = argInfo[argname]['type']
        rtype = formatDocstring(rtype)
        results.append(rtype)

    if len(results) == 1:
        resultsStr = results[0]
    elif results:
        resultsStr = 'Tuple[%s]' % ', '.join(results)
    else:
        resultsStr = None
    if resultsStr:
        docstring += '\n\n' + docBuilderCls.section('Returns') + resultsStr + '\n'

    docstring += '\nDerived from api method `%s.%s.%s`\n' % (
        apiClass.__module__, apiClassName, methodName)
    if not undoable:
        docstring += '\n**Undo is not currently supported for this method**\n'

    pymelClassName = apiClassNameToPymelClassName(apiClassName)
    overrideData = _getApiOverrideData(pymelClassName, methodName)
    aliases = overrideData.get('aliases')
    if aliases:
        aliases = set(aliases)
        aliases.add(methodName)
        aliases = sorted(aliases)
        docstring += '\nAliases: {}\n'.format(', '.join(aliases))

    if origDocstring:
        docstring = origDocstring + '\n' + docstring

    return docstring


class ClassConstant(object):

    """Class constant descriptor"""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '%s.%s(%s)' % (self.__class__.__module__,
                              self.__class__.__name__, repr(self.value))

    def __str__(self):
        return self.__repr__()

    def __get__(self, instance, owner):
        # purposedly authorize notation MColor.blue but not MColor().blue,
        # the constants are a class property and are not defined on instances
        if instance is None:
            # note that conversion to the correct type is done here
            return owner(self.value)
        else:
            raise AttributeError("Class constants on %s are only "
                                 "defined on the class" % (owner.__name__))

    def __set__(self, instance, value):
        raise AttributeError("class constant cannot be set")

    def __delete__(self, instance):
        raise AttributeError("class constant cannot be deleted")


class MetaMayaTypeRegistry(util.metaReadOnlyAttr):

    """
    A metaclass for tracking pymel types.
    """
    def __new__(cls, classname, bases, classdict):
        try:
            apicls = classdict['apicls']
            proxy = False
        except KeyError:
            try:
                apicls = classdict['__apicls__']
                proxy = True
            except KeyError:
                apicls = None
                proxy = True

        # dataclasses multiply inherit their API class
        if not proxy and apicls is not None and apicls not in bases:
            bases = bases + (apicls,)

        newcls = super(MetaMayaTypeRegistry, cls).__new__(cls, classname, bases, classdict)

        nodeType = getattr(newcls, '__melnode__', None)
        if nodeType and classname not in pymelTypeNameToMayaTypeName:
            pymelTypeNameToMayaTypeName[nodeType] = classname
            mayaTypeNameToPymelTypeName.setdefault(nodeType, classname)

        if proxy:
            parentPyNode = [x for x in bases if issubclass(x, util.ProxyUnicode)]
            assert len(parentPyNode), \
                "%s did not have exactly one parent PyNode: %s (%s)" % \
                (classname, parentPyNode, bases)
            addPyNodeType(newcls, parentPyNode)

        if apicls is not None and apicls.__name__ not in apiClassNamesToPyNodeNames:
            #_logger.debug("ADDING %s to %s" % (apicls.__name__, classname))
            apiClassNamesToPyNodeNames[apicls.__name__] = classname
            apiClassNamesToPymelTypes[apicls.__name__] = newcls

        if hasattr(newcls, 'apicls') and not ApiTypeRegister.isRegistered(newcls.apicls.__name__):
            ApiTypeRegister.register(newcls.apicls.__name__, newcls)

        apienum = getattr(newcls, '_apienum__', None)

        if apienum is not None:
            if apienum not in apiEnumsToPyComponents:
                apiEnumsToPyComponents[apienum] = [newcls]
            else:
                oldEntries = apiEnumsToPyComponents[apienum]

                # if the apienum is already present, check if this class is a
                # subclass of an already present class
                newEntries = []
                for oldEntry in oldEntries:
                    for base in bases:
                        if issubclass(base, oldEntry):
                            break
                    else:
                        newEntries.append(oldEntry)
                newEntries.append(newcls)
                apiEnumsToPyComponents[apienum] = newEntries
        return newcls


class MetaMayaTypeWrapper(MetaMayaTypeRegistry):

    """ A metaclass to wrap Maya api types, with support for class constants """

    class ClassConstant(object):

        """Class constant"""

        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return '%s.%s(%s)' % (self.__class__.__module__, self.__class__.__name__, repr(self.value))

        def __str__(self):
            return self.__repr__()

        def __get__(self, instance, owner):
            # purposedly authorize notation MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None:
                # note that conversion to the correct type is done here
                return owner(self.value)
            else:
                raise AttributeError("Class constants on %s are only defined on the class" % (owner.__name__))

        def __set__(self, instance, value):
            raise AttributeError("class constant cannot be set")

        def __delete__(self, instance):
            raise AttributeError("class constant cannot be deleted")

    def __new__(cls, classname, bases, classdict):
        """ Create a new class of metaClassConstants type """

        #_logger.debug( 'MetaMayaTypeWrapper: %s' % classname )
        removeAttrs = []
        # define __slots__ if not defined
        if '__slots__' not in classdict:
            classdict['__slots__'] = ()
        try:
            apicls = classdict['apicls']
            proxy = False
        except KeyError:
            try:
                apicls = classdict['__apicls__']
                proxy = True
            except KeyError:
                apicls = None

        if apicls is not None:

            if not proxy and apicls not in bases:
                #_logger.debug("ADDING BASE %s" % classdict['apicls'])
                bases = bases + (classdict['apicls'],)

            try:
                classInfo = apiClassInfo[apicls.__name__]
            except KeyError:
                _logger.info("No api information for api class %s" % (apicls.__name__))
            else:
                parentApiClass = getattr(bases[0], '__apicls__', None)
                # we're not generating any methods, so this is just a sanity
                # check.  the issubclass exception was added for a case
                # demonstrated by aiStandIn, where the parent pynode class is
                # THsurfaceShape with an parentApiClass of MFnDagNode, while
                # apicls was MFnDependencyNode
                assert (apicls is parentApiClass or issubclass(parentApiClass, apicls)), (classname, apicls, parentApiClass)

            # used to add api-wrapped methods here - now done via template
            # building in maintenance.build

        # create the new class
        newcls = super(MetaMayaTypeWrapper, cls).__new__(cls, classname, bases, classdict)

        # shortcut for ensuring that our class constants are the same type as the class we are creating
        def makeClassConstant(attr):
            try:
                # return MetaMayaTypeWrapper.ClassConstant(newcls(attr))
                return MetaMayaTypeWrapper.ClassConstant(attr)
            except Exception as e:
                _logger.warning("Failed creating %s class constant (%s): %s" % (classname, attr, e))

        # used to add api-wrapped class constants here - now done via template
        # building in maintenance.build

        return newcls

    @classmethod
    def _hasApiSetAttrBug(cls, apiClass):
        """
        Maya has a bug on windows where some api objects have a __setattr__
        that bypasses properties (and other data descriptors).

        This tests if the given apiClass has such a bug.
        """
        class MyClass1(object):

            def __init__(self):
                self._bar = 'not set'

            def _setBar(self, val):
                self._bar = val

            def _getBar(self):
                return self._bar
            bar = property(_getBar, _setBar)

        class MyClass2(MyClass1, apiClass):
            pass

        foo2 = MyClass2()
        foo2.bar = 7
        # Here, on windows, MMatrix's __setattr__ takes over, and
        # (after presumabably determining it didn't need to do
        # whatever special case thing it was designed to do)
        # instead of calling the super's __setattr__, which would
        # use the property, inserts it into the object's __dict__
        # manually
        if foo2.bar != 7:
            return True

        # Starting in Maya2018 (at least on windows?), many wrapped datatypes
        # define a __setattr__ which will work in the "general" case tested
        # above, but will still take precedence if a "_swig_property" is
        # defined - ie, MEulerRotation.order.  Check to see if the apicls has
        # any properties, and ensure that our property still overrides theirs...
        for name, member in inspect.getmembers(apiClass,
                                               lambda x: isinstance(x, property)):
            setattr(MyClass1, name, MyClass1.__dict__['bar'])
            try:
                setattr(foo2, name, 1.23456)
            except Exception:
                return True
            if getattr(foo2, name) != 1.23456:
                return True
            # only check for one property - we assume that all apicls properties
            # will behave the same way...
            break
        return False

    @staticmethod
    def setattr_fixed_forDataDescriptorBug(self, name, value):
        """
        Fixes __setattr__ to work properly with properties

        Maya has a bug on windows where some api objects have a __setattr__
        that bypasses properties (and other data descriptors).
        """
        if hasattr(self.__class__, name):
            if hasattr(getattr(self.__class__, name), '__set__'):
                # we've got a data descriptor with a __set__...
                # don't use the apicls's __setattr__
                return super(self.apicls, self).__setattr__(name, value)
        return self.apicls.__setattr__(self, name, value)


class _MetaMayaCommandWrapper(MetaMayaTypeWrapper):

    """
    A metaclass for creating classes based on a maya command.

    Not intended to be used directly; instead, use the descendants: MetaMayaNodeWrapper, MetaMayaUIWrapper
    """

    _classDictKeyForMelCmd = None

    def __new__(cls, classname, bases, classdict):
        #_logger.debug( '_MetaMayaCommandWrapper: %s' % classname )

        newcls = super(_MetaMayaCommandWrapper, cls).__new__(cls, classname, bases, classdict)

        # -------------------------
        #   MEL Methods
        # -------------------------
        melCmdName, infoCmd = cls.getMelCmd(classdict)

        classdict = {}
        try:
            cmdInfo = cmdlist[melCmdName]
        except KeyError:
            pass
            #_logger.debug("No MEL command info available for %s" % melCmdName)
        else:
            pmSourceFunc = False
            try:
                cmdModule = __import__('pymel.core.' + cmdInfo['type'], globals(), locals(), [''])
                func = getattr(cmdModule, melCmdName)
                pmSourceFunc = True
            except (AttributeError, TypeError):
                func = getattr(pmcmds, melCmdName)

            # add documentation
            classdict['__doc__'] = util.LazyDocString((newcls, cls.docstring, (melCmdName,), {}))
            classdict['__melcmd__'] = staticmethod(func)
            classdict['__melcmdname__'] = melCmdName
            classdict['__melcmd_isinfo__'] = infoCmd

            # used to add mel-wrapped methods here - now done via template
            # building in maintenance.build

        for name, attr in classdict.items():
            type.__setattr__(newcls, name, attr)

        return newcls

    @classmethod
    def getMelCmd(cls, classdict):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.

        Intended to be overridden in derived metaclasses.
        """
        return util.uncapitalize(cls.__name__), False

    @classmethod
    def docstring(cls, melCmdName):
        try:
            cmdInfo = cmdlist[melCmdName]
        except KeyError:
            #_logger.debug("No MEL command info available for %s" % melCmdName)
            classdoc = ''
        else:
            loadCmdDocCache()
            classdoc = 'class counterpart of mel function `%s`\n\n%s\n\n' % (melCmdName, cmdInfo['description'])
        return classdoc


class MetaMayaNodeWrapper(_MetaMayaCommandWrapper):

    """
    A metaclass for creating classes based on node type.  Methods will be added to the new classes
    based on info parsed from the docs on their command counterparts.
    """
    def __new__(cls, classname, bases, classdict):
        # If the class explicitly gives it's mel node name, use that -
        # otherwise, assume it's the name of the PyNode, uncapitalized
        #_logger.debug( 'MetaMayaNodeWrapper: %s' % classname )
        nodeType = classdict.get('__melnode__')

        isVirtual = '_isVirtual' in classdict or any(hasattr(b, '_isVirtual')
                                                     for b in bases)
        if nodeType is None:
            # check for a virtual class...
            if isVirtual:
                for b in bases:
                    if hasattr(b, '__melnode__'):
                        nodeType = b.__melnode__
                        break
                else:
                    raise RuntimeError("Could not determine mel node type for virtual class %r" % classname)
            else:
                # not a virtual class, just use the classname
                nodeType = util.uncapitalize(classname)
            classdict['__melnode__'] = nodeType

        # mapping from pymel type to maya type should always be made...
        oldMayaType = pymelTypeNameToMayaTypeName.get(classname)
        if oldMayaType is None:
            pymelTypeNameToMayaTypeName[classname] = nodeType
        elif oldMayaType != nodeType:
            _logger.raiseLog(_logger.WARNING,
                             'creating new pymel node class %r for maya node '
                             'type %r, but a pymel class with the same name '
                             'already existed for maya node type %r' % (
                                 classname, nodeType, oldMayaType))

        # mapping from maya type to pymel type only happens if it's NOT a
        # virtual class...
        if not isVirtual:
            oldPymelType = mayaTypeNameToPymelTypeName.get(nodeType)
            if oldPymelType is None:
                mayaTypeNameToPymelTypeName[nodeType] = classname
            elif oldPymelType != classname:
                _logger.raiseLog(_logger.WARNING,
                                 'creating new pymel node class %r for maya node '
                                 'type %r, but there already existed a pymel'
                                 'class %r for the same maya node type' % (
                                     classname, nodeType, oldPymelType))

        addMayaType(nodeType)
        apicls = toApiFunctionSet(nodeType)
        if apicls is not None:
            classdict['__apicls__'] = apicls

        PyNodeType = super(MetaMayaNodeWrapper, cls).__new__(cls, classname, bases, classdict)
        return PyNodeType

    @classmethod
    def getMelCmd(cls, classdict):
        """
        Retrieves the name of the mel command for the node that the generated class wraps,
        and whether it is an info command.

        Derives the command name from the mel node name - so '__melnode__' must already be set
        in classdict.
        """
        nodeType = classdict['__melnode__']
        nodeCmd = classdict.get('__melcmd__')
        if nodeCmd:
            infoCmd = classdict.get('__melcmd_isinfo__', False)
        else:
            infoCmd = False
            try:
                nodeCmd = cmdcache.nodeTypeToNodeCommand[nodeType]
            except KeyError:
                try:
                    nodeCmd = nodeTypeToInfoCommand[nodeType]
                    infoCmd = True
                except KeyError:
                    nodeCmd = nodeType
        return nodeCmd, infoCmd


class MetaMayaUIWrapper(_MetaMayaCommandWrapper):

    """
    A metaclass for creating classes based on on a maya UI type/command.
    """

    def __new__(cls, classname, bases, classdict):
        # If the class explicitly gives it's mel ui command name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        uiType = classdict.setdefault('__melui__', util.uncapitalize(classname))

        # TODO: implement a option at the cmdlist level that triggers listForNone
        # TODO: create labelArray for *Grp ui elements, which passes to the correct arg ( labelArray3, labelArray4, etc ) based on length of passed array

        return super(MetaMayaUIWrapper, cls).__new__(cls, classname, bases, classdict)

    @classmethod
    def getMelCmd(cls, classdict):
        return classdict['__melui__'], False


def _createPyNode(module, mayaType, pyNodeTypeName, parentPyNodeTypeName, extraAttrs=None):
    # type: (Any, str, str, str, Any) -> Optional[type]
    """
    Parameters
    ----------
    module
    mayaType : str
    pyNodeTypeName : str
    parentPyNodeTypeName : str
    extraAttrs

    Returns
    -------
    Optional[type]
    """
    #_logger.debug( "%s(%s): creating" % (pyNodeTypeName,parentPyNodeTypeName) )
    try:
        ParentPyNode = getattr(module, parentPyNodeTypeName)
    except AttributeError:
        _logger.debug("error creating class %s: parent class %r not in "
                      "module %s" % (pyNodeTypeName, parentPyNodeTypeName,
                                     module.__name__))
        return

    classDict = {'__melnode__': mayaType}
    if extraAttrs:
        classDict.update(extraAttrs)
    if pyNodeTypeName in pyNodeNamesToPyNodes:
        PyNodeType = pyNodeNamesToPyNodes[pyNodeTypeName]
    else:
        try:
            PyNodeType = MetaMayaNodeWrapper(pyNodeTypeName, (ParentPyNode,), classDict)
        except TypeError as msg:
            # for the error: metaclass conflict: the metaclass of a derived
            # class must be a (non-strict) subclass of the metaclasses of all
            # its bases
            _logger.error("Could not create new PyNode: %s(%s): %s" %
                          (pyNodeTypeName, ParentPyNode.__name__, msg))
            import new
            PyNodeType = new.classobj(pyNodeTypeName, (ParentPyNode,), {})
            #_logger.debug(("Created new PyNode: %s(%s)" % (pyNodeTypeName, parentPyNodeTypeName)))

        PyNodeType.__module__ = module.__name__
    return PyNodeType


def addCustomPyNode(module, mayaType, extraAttrs=None):
    # type: (Any, Any, Any) -> Optional[str]
    """
    create a PyNode, also adding each member in the given maya node's inheritance if it does not exist.

    This function is used for creating PyNodes via plugins, where the nodes parent's might be abstract
    types not yet created by pymel.  also, this function ensures that the newly created node types are
    added to pymel.all, if that module has been imported.

    Returns
    -------
    Optional[str]
    """
    try:
        inheritance = apicache.getInheritance(mayaType)
    except apicache.ManipNodeTypeError:
        _logger.debug("could not create a PyNode for manipulator type %s" % mayaType)
        return
    except Exception:
        import traceback
        _logger.debug(traceback.format_exc())
        inheritance = None

    if not inheritance or not util.isIterable(inheritance):
        _logger.warning("could not get inheritance for mayaType %s" % mayaType)
    else:
        #__logger.debug(mayaType, inheritance)
        #__logger.debug("adding new node:", mayaType, apiEnum, inheritence)
        # some nodes in the hierarchy for this node might not exist, so we cycle through all
        parent = 'dependNode'

        pynodeName = None
        for node in inheritance:
            pynodeName, pynodeClass = _addPyNode(
                module, node, parent,
                extraAttrs=extraAttrs if node == mayaType else None)
            parent = node
            if 'pymel.all' in sys.modules:
                setattr(sys.modules['pymel.all'], pynodeName, pynodeClass)
        return pynodeName


def getPymelTypeName(mayaTypeName, create=True):
    # type: (str, bool) -> str
    pymelTypeName = mayaTypeNameToPymelTypeName.get(mayaTypeName)
    if pymelTypeName is None and create:
        pymelTypeName = str(util.capitalize(mayaTypeName))
        pymelTypeNameBase = pymelTypeName
        num = 1
        while pymelTypeName in pymelTypeNameToMayaTypeName:
            num += 1
            pymelTypeName = pymelTypeNameBase + str(num)
        mayaTypeNameToPymelTypeName[mayaTypeName] = pymelTypeName
        pymelTypeNameToMayaTypeName[pymelTypeName] = mayaTypeName
    return pymelTypeName


def _addPyNode(module, mayaType, parentMayaType, extraAttrs=None):
    # type: (Any, Any, Any, Any) -> Tuple[str, type]
    """
    create a PyNode type for a maya node.

    Returns
    -------
    name : str
    class : type
    """
    # unicode is not liked by metaNode
    parentPyNodeTypeName = mayaTypeNameToPymelTypeName.get(parentMayaType)
    if parentPyNodeTypeName is None:
        _logger.raiseLog(_logger.WARNING,
                         'trying to create PyNode for maya type %r, but could'
                         ' not find a registered PyNode for parent type %r' % (
                             mayaType, parentMayaType))
        parentPyNodeTypeName = str(util.capitalize(parentMayaType))
    pyNodeTypeName = getPymelTypeName(mayaType)

    if hasattr(module, pyNodeTypeName):
        return pyNodeTypeName, getattr(module, pyNodeTypeName)
    else:
        _logger.debug("addPyNode adding %s->%s on module %s" %
                      (mayaType, parentMayaType, module))
        newType = _createPyNode(module, mayaType, pyNodeTypeName,
                                parentPyNodeTypeName, extraAttrs)
        setattr(module, pyNodeTypeName, newType)
        return pyNodeTypeName, newType


def removePyNode(module, mayaType):
    pyNodeTypeName = mayaTypeNameToPymelTypeName.get(mayaType)
    if not pyNodeTypeName:
        _logger.raiseLog(_logger.WARNING,
                         'trying to remove PyNode for maya type %r, but could '
                         'not find an associated PyNode registered' % mayaType)
        pyNodeTypeName = str(util.capitalize(mayaType))
    removePyNodeType(pyNodeTypeName)

    _logger.debug('removing %s from %s' % (pyNodeTypeName, module.__name__))
    module.__dict__.pop(pyNodeTypeName, None)

    if 'pymel.all' in sys.modules:
        try:
            delattr(sys.modules['pymel.all'], pyNodeTypeName)
        except AttributeError:
            pass
    removeMayaType(mayaType)


def addPyNodeType(pyNodeType, parentPyNode):
    pyNodeNamesToPyNodes[pyNodeType.__name__] = pyNodeType
    pyNodeTypesHierarchy[pyNodeType] = parentPyNode


def removePyNodeType(pyNodeTypeName):
    pyNodeType = pyNodeNamesToPyNodes.pop(pyNodeTypeName, None)
    pyNodeTypesHierarchy.pop(pyNodeType, None)


def clearPyNodeTypes():
    pyNodeNamesToPyNodes.clear()
    pyNodeTypesHierarchy.clear()


def addMayaType(mayaType, apiType=None):
    """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for.

        - mayaTypesToApiTypes
        - mayaTypesToApiEnums
    """
    global _apiCacheInst
    if apiType is None:
        apiType = _apiCacheInst.mayaTypeToApiType(mayaType)

    _apiCacheInst.addMayaType(mayaType, apiType, globals())
    _setApiCacheGlobals()


def removeMayaType(mayaType):
    """ Remove a type from the MayaTypes lists.

        - mayaTypesToApiTypes
        - mayaTypesToApiEnums
    """
    global _apiCacheInst
    _apiCacheInst.removeMayaType(mayaType, globals())
    _setApiCacheGlobals()

VirtualClassInfo = util.namedtuple('VirtualClassInfo',
                                   'vclass parent nameRequired isVirtual preCreate create postCreate')


class VirtualClassError(Exception):
    pass


class VirtualClassManager(object):
    # these methods are particularly dangerous to override, so we prohibit it...

    # ...note that I don't know of any SPECIFIC problems with __init__ and
    # __new__... but we formerly disabled (nearly) all double-underscore
    # methods, and I THINK one of the main culprits was __init__ and __new__.
    # (At the very least, if they wanted to allow new args, the user would have
    # to modify both, because of the limitation in python that __new__ cannot
    # modify the args passed to __init__.)  If there is a great demand for
    # allowing __init__/__new__, we may remove these from the list...

    # __str__ is obviously dangerous, since in places the assumption is
    # essentially made that str(node) == node.name()...
    INVALID_ATTRS = set(['__init__', '__new__', '__str__'])

    def __init__(self):
        self._byVirtualClass = {}
        self._byParentClass = util.defaultdict(list)

    def register(self, vclass, nameRequired=False, isVirtual='_isVirtual',
                 preCreate='_preCreateVirtual',
                 create='_createVirtual',
                 postCreate='_postCreateVirtual', ):
        # type: (Any, bool, str or callable, str or callable, str or callable, str or callable) -> None
        """Register a new virtual class

        Allows a user to create their own subclasses of leaf PyMEL node classes,
        which are returned by `general.PyNode` and all other pymel commands.

        The process is fairly simple:
            1.  Subclass a PyNode class.  Be sure that it is a leaf class,
                meaning that it represents an actual Maya node type and not an
                abstract type higher up in the hierarchy.
            2.  Add an _isVirtual classmethod that accepts two arguments: an
                MObject/MDagPath instance for the current object, and its name.
                It should return True if the current object meets the
                requirements to become the virtual subclass, or else False.
            3.  Add optional _preCreate, _create, and _postCreate methods.  For
                more on these, see below
            4.  Register your subclass by calling
                factories.registerVirtualClass. If the _isVirtual callback
                requires the name of the object, set the keyword argument
                nameRequired to True. The object's name is not always
                immediately available and may take an extra calculation to
                retrieve, so if nameRequired is not set the name argument
                passed to your callback could be None.

        The creation of custom nodes may be customized with the use of
        isVirtual, preCreate, create, and postCreate functions; these are
        functions (or classmethods) which are called before / during / after
        creating the node.

        The isVirtual method is required - it is the callback used on instances
        of the base (ie, 'real') objects to determine whether they should be
        considered an instance of this virtual class. It's input is an MObject
        and an optional name (if nameRequired is set to True). It should return
        True to indicate that the given object is 'of this class', False
        otherwise. PyMEL code should not be used inside the callback, only API
        and maya.cmds. Keep in mind that once your new type is registered, its
        test will be run every time a node of its parent type is returned as a
        PyMEL node class, so be sure to keep your tests simple and fast.

        The preCreate function is called prior to node creation and gives you a
        chance to modify the kwargs dictionary; they are fed the kwargs fed to
        the creation command, and return either 1 or 2 dictionaries; the first
        dictionary is the one actually passed to the creation command; the
        second, if present, is passed to the postCreate command.

        The create method can be used to override the 'default' node creation
        command;  it is given the kwargs given on node creation (possibly
        altered by the preCreate), and must return the string name of the
        created node. (...or any another type of object (such as an MObject),
        as long as the postCreate and class.__init__ support it.)

        The postCreate function is called after creating the new node, and
        gives you a chance to modify it.  The method is passed the PyNode of
        the newly created node, as well as the second dictionary returned from
        the preCreate function as kwargs (if it was returned). You can use
        PyMEL code here, but you should avoid creating any new nodes.

        By default, any method named '_isVirtual', '_preCreateVirtual',
        '_createVirtual', or '_postCreateVirtual' on the class is used; if
        present, these must be classmethods or staticmethods.

        Other methods / functions may be used by passing a string or callable
        to the preCreate / postCreate kwargs.  If a string, then the method
        with that name on the class is used; it should be a classmethod or
        staticmethod present at the time it is registered.

        The value None may also be passed to any of these args (except isVirtual)
        to signal that no function is to be used for these purposes.

        If more than one subclass is registered for a node type, the registered
        callbacks will be run newest to oldest until one returns True. If no
        test returns True, then the standard node class is used. Also, for each
        base node type, if there is already a virtual class registered with the
        same name and module, then it is removed. (This helps alleviate
        registered callbacks from piling up if, for instance, a module is
        reloaded.)

        Overriding methods of PyMEL base classes should be performed with care,
        because certain methods are used internally and altering their results
        may cause PyMEL to error or behave unpredictably.  This is particularly
        true for special methods like __setattr__, __getattr__, __setstate__,
        __getstate__, etc.  Some methods are considered too dangerous to modify,
        and registration will fail if the user defines an override for them;
        this set includes __init__, __new__, and __str__.

        For a usage example, see examples/customClasses.py

        Parameters
        ----------
        nameRequired : `bool`
            True if the _isVirtual callback requires the string name to operate
            on. The object's name is not always immediately avaiable and may
            take an extra calculation to retrieve.
        isVirtual: `str` or callable
            the function to determine whether an MObject is an instance of this
            class; should take an MObject and name, returns True / or False
        preCreate: `str` or callable
            the function used to modify kwargs before being passed to the
            creation function
        create: `str` or callable
            function to use instead of the standard node creation method;
            takes whatever args are given to the cl
        postCreate: `str` or callable
            the function used to modify the PyNode after it is created.
        """
        if isinstance(isVirtual, basestring):
            isVirtual = getattr(vclass, isVirtual, None)
        if isinstance(preCreate, basestring):
            preCreate = getattr(vclass, preCreate, None)
        if isinstance(create, basestring):
            create = getattr(vclass, create, None)
        if isinstance(postCreate, basestring):
            postCreate = getattr(vclass, postCreate, None)

        # assert that we are a leaf class
        parentCls = None
        for each_cls in inspect.getmro(vclass):
            # we've reached a pymel node. we're done
            if each_cls.__module__.startswith('pymel.core'):
                parentCls = each_cls
                break
            else:
                # it's a custom class: test for disallowed attributes
                badAttrs = self.INVALID_ATTRS.intersection(each_cls.__dict__)
                if badAttrs:
                    raise ValueError('invalid attribute name(s) %s: these special attributes are not allowed on virtual nodes' % ', '.join(badAttrs))

        assert parentCls, "passed class must be a subclass of a PyNode type"
        #assert issubclass( vclass, parentCls ), "%s must be a subclass of %s" % ( vclass, parentCls )

        vclass.__melnode__ = parentCls.__melnode__

        # filter out any pre-existing classes with the same name / module as
        # this one, because leaving stale callbacks in the list will slow things
        # down
        for vClassInfo in self._byParentClass[parentCls]:
            otherVcls = vClassInfo.vclass
            if otherVcls.__name__ == vclass.__name__ and otherVcls.__module__ == vclass.__module__:
                self.unregister(otherVcls)

        # TODO:
        # inspect callbacks to ensure proper number of args and kwargs ( create callback must support **kwargs )
        # ensure that the name of our node does not conflict with a real node

        vClassInfo = VirtualClassInfo(vclass, parentCls, nameRequired,
                                      isVirtual, preCreate, create, postCreate)
        self._byParentClass[parentCls].append(vClassInfo)
        self._byVirtualClass[vclass] = vClassInfo

    def unregister(self, vcls):
        try:
            vClassInfo = self._byVirtualClass.pop(vcls)
        except KeyError:
            raise VirtualClassError('%r was not registered as a virtual class' % vcls)
        self._byParentClass[vClassInfo.parent].remove(vClassInfo)

    def getVirtualClass(self, baseClass, obj, name=None, fnDepend=None):
        '''
        Returns the virtual class to use for the given baseClass + obj, or
        the original baseClass if no virtual class matches.
        '''
        vClasses = self._byParentClass.get(baseClass)
        if not vClasses:
            return baseClass
        for vClassInfo in reversed(vClasses):
            if vClassInfo.nameRequired and name is None:
                if fnDepend is None:
                    fnDepend = api.MFnDependencyNode(obj)
                name = fnDepend.name()

            if vClassInfo.isVirtual(obj, name):
                return vClassInfo.vclass
        return baseClass

    def getVirtualClassInfo(self, vclass):
        '''
        Given a virtual class, returns it's registered VirtualClassInfo
        '''
        return self._byVirtualClass.get(vclass)

virtualClasses = VirtualClassManager()

# for backwards compatibility + ease of access
registerVirtualClass = virtualClasses.register

# -----------------------------------------------------------------------------


def isValidPyNode(arg):
    return arg in pyNodeTypesHierarchy


def isValidPyNodeName(arg):
    return arg in pyNodeNamesToPyNodes


def toApiTypeStr(obj, default=None):
    # type: (Union[int, str, util.ProxyUnicode], Optional[str]) -> Optional[str]
    """
    Parameters
    ----------
    obj : Union[int, str, util.ProxyUnicode]
    default : Optional[str]

    Returns
    -------
    Optional[str]
    """
    if isinstance(obj, int):
        return apiEnumsToApiTypes.get(obj, default)
    elif isinstance(obj, basestring):
        return mayaTypesToApiTypes.get(obj, default)
    elif isinstance(obj, util.ProxyUnicode):
        mayaType = getattr(obj, '__melnode__', None)
        return mayaTypesToApiTypes.get(mayaType, default)


def toApiTypeEnum(obj, default=None):
    # type: (Union[str, util.ProxyUnicode], Optional[int]) -> Optional[int]
    """
    Parameters
    ----------
    obj : Union[str, util.ProxyUnicode]
    default : Optional[int]

    Returns
    -------
    int
    """
    if isinstance(obj, util.ProxyUnicode):
        obj = getattr(obj, '__melnode__', default)
    try:
        return apiTypesToApiEnums[obj]
    except KeyError:
        return mayaTypesToApiEnums.get(obj, default)


def toApiFunctionSet(obj):
    # type: (Union[str, int]) -> Optional[Type]
    """
    Parameters
    ----------
    obj : Union[str, int]

    Returns
    -------
    Optional[Type]
    """
    if isinstance(obj, basestring):
        try:
            return apiTypesToApiClasses[obj]
        except KeyError:
            if obj in mayaTypesToApiTypes:
                mayaType = obj
                apiType = mayaTypesToApiTypes[obj]
                return _apiCacheInst._getOrSetApiClass(apiType, mayaType)
            else:
                return None
    elif isinstance(obj, int):
        try:
            return apiTypesToApiClasses[apiEnumsToApiTypes[obj]]
        except KeyError:
            return None


def apiClassNameToPymelClassName(apiName, allowGuess=True):
    # type: (str, bool) -> Optional[str]
    """
    Given the name of an api class, such as MFnTransform, MSpace, MAngle,
    returns the name of the corresponding pymel class.

    Parameters
    ----------
    apiName : str
    allowGuess : bool
        If enabled, and we cannot find a registered type that matches, will
        try to do string parsing to guess the pymel name.

    Returns
    -------
    Optional[str]
        Returns None if it was unable to determine the name.
    """
    pymelName = apiClassNamesToPyNodeNames.get(apiName, None)
    if pymelName is None:
        pymelName = ApiTypeRegister.getPymelType(apiName, allowGuess=allowGuess)
    return pymelName


def isMayaType(mayaType):
    # type: (str) -> bool
    """
    Whether the given type is a currently-defined maya node name

    Parameters
    ----------
    str

    Returns
    -------
    bool
    """
    # use nodeType(isTypeName) preferentially, because it returns results
    # for some objects that objectType(tagFromType) returns 0 for
    # (like TadskAssetInstanceNode_TdependNode, which is a parent of
    # adskMaterial
    try:
        cmds.nodeType(mayaType, isTypeName=True)
    except RuntimeError:
        return False
    else:
        return True

# Keep around for debugging/info gathering...


def getComponentTypes():
    # WTF is kMeshFaceVertComponent?? it doesn't inherit from MFnComponent,
    # and there's also a kMeshVtxFaceComponent (which does)??
    mfnCompBase = api.MFnComponent()
    mfnCompTypes = (api.MFnSingleIndexedComponent(),
                    api.MFnDoubleIndexedComponent(),
                    api.MFnTripleIndexedComponent())
    # Maya 2008 and before didn't haveMFnUint64SingleIndexedComponent
    if hasattr(api.MFn, 'kUint64SingleIndexedComponent'):
        mfnCompTypes += (api.MFnUint64SingleIndexedComponent(),)

    componentTypes = {}
    for compType in mfnCompTypes + (mfnCompBase,):
        componentTypes[compType.type()] = []

    for apiEnum in apiEnumsToApiTypes:
        if mfnCompBase.hasObj(apiEnum):
            for compType in mfnCompTypes:
                if compType.hasObj(apiEnum):
                    break
            else:
                compType = mfnCompBase
            componentTypes[compType.type()].append(apiEnum)

    return componentTypes

"""
Contains the wrapping mechanisms that allows pymel to integrate the api and maya.cmds into a unified interface
"""

# Built-in imports
import re
import types
import os
import inspect
import sys
import textwrap
import time
import traceback
from operator import itemgetter

# Maya imports
import maya.cmds as cmds
import maya.mel as mm

# PyMEL imports
import pymel.api as api
import pymel.util as util
from pymel.util.conditions import Always, Condition
import pymel.versions as versions

# Module imports
from . import apicache
from . import cmdcache
from . import plogging
from . import pmcmds

_logger = plogging.getLogger(__name__)

# Initialize the cache globals

# Doing an initialization here mainly just for auto-completion, and to
# see these variables are defined here when doing text searches; the values
# are set inside loadApi/CmdCache

# ApiCache
apiTypesToApiEnums = None
apiEnumsToApiTypes = None
mayaTypesToApiTypes = None
apiTypesToApiClasses = None
apiClassInfo = None

mayaTypesToApiEnums = None

# ApiMelBridgeCache
apiToMelData = None
apiClassOverrides = None

# CmdCache
cmdlist = None
nodeHierarchy = None
uiClassList = None
nodeCommandList = None
moduleCmds = None


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
    _logger.debug("Loading cmd cache...")
    _start = time.time()

    global _cmdCacheInst

    global cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds

    _cmdCacheInst = cmdcache.CmdCache()
    _cmdCacheInst.build()
    _setCmdCacheGlobals()

    _elapsed = time.time() - _start
    _logger.debug("Initialized Cmd Cache in in %.2f sec" % _elapsed)

def _setCmdCacheGlobals():
    global _cmdCacheInst

    for name, val in zip(_cmdCacheInst.cacheNames(), _cmdCacheInst.contents()):
        globals()[name] = val


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

loadApiCache()
loadCmdCache()


#---------------------------------------------------------------
#        Mappings and Lists
#---------------------------------------------------------------

DOC_WIDTH = 120

EXCLUDE_METHODS = ['type', 'className', 'create', 'name']

#: controls whether command docstrings will contain examples parsed from autodesk docs
# examples are usually only included when creating documentation, otherwise it's too much info
includeDocExamples = bool(os.environ.get('PYMEL_INCLUDE_EXAMPLES', False))

# Lookup from PyNode type name as a string to PyNode type as a class
pyNodeNamesToPyNodes = {}

# Lookup from MFn to PyNode name
apiClassNamesToPyNodeNames = {}

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
    "returns a PyNode object"
    if res is not None and res != '':
        import pymel.core.general
        return pymel.core.general.PyNode(res)

def unwrapToPyNode(res):
    "unwraps a 1-item list, and returns a PyNode object"
    if res is not None and res[0]:
        import pymel.core.general
        return pymel.core.general.PyNode(res[0])

def toPyUI(res):
    "returns a PyUI object"
    if res is not None:
        import pymel.core.uitypes
        return pymel.core.uitypes.PyUI(res)

def toPyType(moduleName, objectName):
    """
    Returns a function which casts it's single argument to
    an object with the given name in the given module (name).

    The module / object are given as strings, so that the module
    may be imported when the function is called, to avoid
    making factories dependent on, say, pymel.core.general or
    pymel.core.uitypes
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
    "returns a list of PyNode objects"
    if res is None:
        return []
    import pymel.core.general
    return [pymel.core.general.PyNode(x) for x in res]

def splitToPyNodeList(res):
    "converts a whitespace-separated string of names to a list of PyNode objects"
    return toPyNodeList(res.split())

def toPyUIList(res):
    "returns a list of PyUI objects"
    if res is None:
        return []
    import pymel.core.uitypes
    return [pymel.core.uitypes.PyUI(x) for x in res]

def toPyTypeList(moduleName, objectName):
    """
    Returns a function which casts the members of it's iterable
    argument to the given class.
    """
    def toGivenClassList(res):
        module = __import__(moduleName, globals(), locals(), [objectName], -1)
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

    'ikHandle': [(toPyNode,
                  Flag('query', 'q') & Flag('endEffector', 'ee')),
                 (toPyNodeList,
                  Flag('query', 'q') & Flag('jointList', 'jl')),
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
#---------------------------------------------------------------

if includeDocExamples:
    examples = cmdcache.CmdProcessedExamplesCache().read()
    for cmd, example in examples.iteritems():
        try:
            cmdlist[cmd]['example'] = example
        except KeyError:
            print "found an example for an unknown command:", cmd
            pass

#cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds = cmdcache.buildCachedData()

# FIXME
#: stores a dictionary of pymel classnames to mel method names
classToMelMap = util.defaultdict(list)

def _getApiOverrideNameAndData(classname, pymelName):
    if apiToMelData.has_key((classname, pymelName)):

        data = apiToMelData[(classname, pymelName)]
        try:
            nameType = data['useName']
        except KeyError:
            # Not sure why it was a big deal if useName wasn't set...?
            #_logger.warn( "no 'useName' key set for %s.%s" % (classname, pymelName) )
            nameType = 'API'

        if nameType == 'API':
            pass
        elif nameType == 'MEL':
            pymelName = data['melName']
        else:
            pymelName = nameType
    else:
        # set defaults
        #_logger.debug( "creating default api-to-MEL data for %s.%s" % ( classname, pymelName ) )
        data = {'enabled': pymelName not in EXCLUDE_METHODS}
        apiToMelData[(classname, pymelName)] = data

    #overloadIndex = data.get( 'overloadIndex', None )
    return pymelName, data


def getUncachedCmds():
    return list(set(map(itemgetter(0), inspect.getmembers(cmds, callable))).difference(cmdlist.keys()))


#-----------------------
# Function Factory
#-----------------------
docCacheLoaded = False
def loadCmdDocCache():
    global docCacheLoaded
    if docCacheLoaded:
        return
    data = cmdcache.CmdDocsCache().read()
    util.mergeCascadingDicts(data, cmdlist)
    docCacheLoaded = True

def _addCmdDocs(func, cmdName):
    # runtime functions have no docs
    if cmdlist[cmdName]['type'] == 'runtime':
        return func

    if func.__doc__:
        docstring = func.__doc__ + '\n\n'
    else:
        docstring = ''
    util.addLazyDocString(func, addCmdDocsCallback, cmdName, docstring)
    return func

def addCmdDocsCallback(cmdName, docstring=''):
    def section(title):
        if includeDocExamples:
            return '.. rubric:: %s' % title
        else:
            return title

    loadCmdDocCache()

    cmdInfo = cmdlist[cmdName]

    #docstring = cmdInfo['description'] + '\n\n' + '\n'.join(textwrap.wrap(docstring.strip(), DOC_WIDTH))

    docstring = '\n'.join(textwrap.wrap(cmdInfo['description'], DOC_WIDTH)) + '\n\n' + docstring.strip()

#    if func.__doc__:
#        docstring += func.__doc__ + '\n\n'

    docstring = docstring.rstrip() + '\n\n'

    flagDocs = cmdInfo['flags']

    if flagDocs and not set(flagDocs.keys()).issubset(['edit', 'query']):

        widths = [3, 100, 32, 32]
        altwidths = [widths[0] + widths[1]] + widths[2:]
        rowsep = '+' + '+'.join(['-' * (w - 1) for w in widths]) + '+\n'
        headersep = '+' + '+'.join(['=' * (w - 1) for w in widths]) + '+\n'

        def makerow(items, widths):
            return '|' + '|'.join(' ' + i.ljust(w - 2) for i, w in zip(items, widths)) + '|\n'

        docstring += section('Flags:') + '\n'

        if includeDocExamples:
            docstring += '\n' + rowsep
            docstring += makerow(['Long Name / Short Name', 'Argument Types', 'Properties'], altwidths)
            docstring += headersep

        for flag in sorted(flagDocs.keys()):
            if flag in ['edit', 'query']:
                continue
            docs = flagDocs[flag]

            # type
            try:
                typ = docs['args']
            except KeyError, e:
                raise KeyError("Error retrieving doc information for: %s, %s\n%s" % (cmdName, flag, e))
            if isinstance(typ, list):
                try:
                    typ = [x.__name__ for x in typ]
                except:
                    typ = [str(x) for x in typ]
                typ = ', '.join(typ)
            else:
                try:
                    typ = typ.__name__
                except:
                    pass

            # docstring
            descr = docs.get('docstring', '')

            # modes
            tmpmodes = docs.get('modes', [])
            modes = []
            if 'create' in tmpmodes:
                modes.append('create')
            if 'query' in tmpmodes:
                modes.append('query')
            if 'edit' in tmpmodes:
                modes.append('edit')

            if includeDocExamples:
                for data in util.izip_longest(['``%s`` / ``%s``' % (flag, docs['shortname'])],
                                              textwrap.wrap('*%s*' % typ, widths[2] - 2),
                                              ['.. image:: /images/%s.gif' % m for m in modes],
                                              fillvalue=''):
                    docstring += makerow(data, altwidths)

                #docstring += makerow( ['**%s (%s)**' % (flag, docs['shortname']), '*%s*' % typ, ''], altwidths )
                # for m in modes:
                #    docstring += makerow( ['', '', '.. image:: /images/%s.gif' % m], altwidths )

                docstring += rowsep

                descr_widths = [widths[0], sum(widths[1:])]
                if descr:
                    for line in textwrap.wrap(descr.strip('|'), sum(widths[1:]) - 2):
                        docstring += makerow(['', line], descr_widths)
                    # add some filler at the bottom
                    docstring += makerow(['', '  ..'], descr_widths)
                else:
                    docstring += makerow(['', ''], descr_widths)

                # empty row for spacing
                #docstring += rowsep
                #docstring += makerow( ['']*len(widths), widths )
                # closing separator
                docstring += rowsep

            else:
                descr = '\n'.join(['      ' + x for x in textwrap.wrap(descr, DOC_WIDTH)])
                # add trailing newline
                descr = descr + '\n' if descr else ''
                docstring += '  - %s %s [%s]\n%s\n' % (
                    (flag + ' : ' + docs['shortname']).ljust(30),
                    ('(' + typ + ')').ljust(15),
                    ','.join(modes),
                    descr)
#            #modified
#            try:
#                modified = docs['modified']
#                if modified:
#                    docstring += '        - modifies: *%s*\n' % ( ', '.join( modified ))
#            except KeyError: pass
#
#            #secondary flags
#            try:
#                docstring += '        - secondary flags: *%s*\n' % ( ', '.join(docs['secondaryFlags'] ))
#            except KeyError: pass
#
            # args

    docstring += '\nDerived from mel command `maya.cmds.%s`\n' % (cmdName)

    if includeDocExamples and cmdInfo.get('example', None):
        #docstring = ".. |create| image:: /images/create.gif\n.. |edit| image:: /images/edit.gif\n.. |query| image:: /images/query.gif\n\n" + docstring
        docstring += '\n\n' + section('Example:') + '\n\n::\n' + cmdInfo['example']

    return docstring

    #func.__doc__ = docstring
    # return func

def _addFlagCmdDocs(func, cmdName, flag, docstring=''):
    util.addLazyDocString(func, addFlagCmdDocsCallback, cmdName, flag, docstring)
    return func

def addFlagCmdDocsCallback(cmdName, flag, docstring):
    loadCmdDocCache()
    allFlagInfo = cmdlist[cmdName]['flags']
    try:
        flagInfo = allFlagInfo[flag]
    except KeyError:
        _logger.warn('could not find any info on flag %s' % flag)
    else:
        if docstring:
            docstring += '\n\n'

        newdocs = flagInfo.get('docstring', '')
        if newdocs:
            docstring += newdocs + '\n\n'

        if 'secondaryFlags' in flagInfo:
            docstring += 'Flags:\n'
            for secondaryFlag in flagInfo['secondaryFlags']:
                flagdoc = allFlagInfo[secondaryFlag]['docstring']
                docstring += '  - %s:\n%s\n' % (secondaryFlag,
                                                '\n'.join(['      ' + x for x in textwrap.wrap(flagdoc, DOC_WIDTH)]))

        docstring += '\nDerived from mel command `maya.cmds.%s`\n' % (cmdName)
    return docstring

#    func.__doc__ = docstring
#    return func


def _getTimeRangeFlags(cmdName):
    """used parsed data and naming convention to determine which flags are callbacks"""

    commandFlags = set()
    try:
        flagDocs = cmdlist[cmdName]['flags']
    except KeyError:
        pass
    else:
        for flag, data in flagDocs.iteritems():
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
            exception = sys.exc_value
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
        print cls.formatRecentError(index=index)

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
            except Exception, e:
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
            except Exception, e:
                self.logCallbackError(self)
                raise
        finally:
            cmds.undoInfo(closeChunk=1)

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

    argCorrector = None
    if versions.current() < versions.v2011:
        # wrap ui callback commands to ensure that the correct types are returned.
        # we don't have a list of which command-callback pairs return what type, but for many we can guess based on their name.
        if funcName.startswith('float'):
            argCorrector = float
        elif funcName.startswith('int'):
            argCorrector = int
        elif funcName.startswith('checkBox') or funcName.startswith('radioButton'):
            argCorrector = lambda x: x == 'true'

    # need to define a seperate var here to hold
    # the old value of newFunc, b/c 'return newFunc'
    # would be recursive
    beforeUiFunc = inFunc

    def _makeCallback(origCallback, args, doPassSelf):
        """this function is used to make the callback, so that we can ensure the origCallback gets
        "pinned" down"""
        # print "fixing callback", key
        creationTraceback = ''.join(traceback.format_stack())

        def callback(*cb_args):
            if argCorrector:
                newargs = [argCorrector(arg) for arg in cb_args]
            else:
                newargs = list(cb_args)

            if doPassSelf:
                newargs = [args[0]] + newargs
            newargs = tuple(newargs)
            try:
                res = origCallback(*newargs)
            except Exception, e:
                # if origCallback was ITSELF a Callback obj, it will have
                # already logged the error..
                if not isinstance(origCallback, Callback):
                    Callback.logCallbackError(origCallback,
                                              creationTrace=creationTraceback)
                raise
            if isinstance(res, util.ProxyUnicode):
                res = unicode(res)
            return res
        return callback

    def newUiFunc(*args, **kwargs):

        if len(args):
            doPassSelf = kwargs.pop('passSelf', False)
        else:
            doPassSelf = False

        for key in commandFlags:
            try:
                cb = kwargs[key]
                if callable(cb):
                    kwargs[key] = _makeCallback(cb, args, doPassSelf)
            except KeyError:
                pass

        return beforeUiFunc(*args, **kwargs)

    newUiFunc.__name__ = funcName
    newUiFunc.__module__ = inFunc.__module__
    newUiFunc.__doc__ = inFunc.__doc__

    return newUiFunc

def functionFactory(funcNameOrObject, returnFunc=None, module=None, rename=None, uiWidget=False):
    """
    create a new function, apply the given returnFunc to the results (if any)
    Use pre-parsed command documentation to add to __doc__ strings for the
    command.
    """

    # if module is None:
    #   module = _thisModule

    inFunc = None
    if isinstance(funcNameOrObject, basestring):
        funcName = funcNameOrObject

        # make sure that we import from pmcmds, not cmds
        if module and module != cmds:
            try:
                inFunc = getattr(module, funcName)
                customFunc = True
            except AttributeError:
                # if funcName == 'lsThroughFilter': #_logger.debug("function %s not found in module %s" % ( funcName, module.__name__))
                pass

        if not inFunc:
            try:
                inFunc = getattr(pmcmds, funcName)
                customFunc = False
                # if funcName == 'lsThroughFilter': #_logger.debug("function %s found in module %s: %s" % ( funcName, cmds.__name__, inFunc.__name__))
            except AttributeError:
                #_logger.debug('Cannot find function %s' % funcNameOrObject)
                return
    else:
        funcName = pmcmds.getCmdName(funcNameOrObject)
        inFunc = funcNameOrObject
        customFunc = True

    # Do some sanity checks...
    if not callable(inFunc):
        _logger.warn('%s not callable' % funcNameOrObject)
        return

    cmdInfo = cmdlist[funcName]
    funcType = type(inFunc)
    # python doesn't like unicode function names
    funcName = str(funcName)

    if funcType == types.BuiltinFunctionType:
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                _logger.warn("Function found in module %s has different name than desired: %s != %s. simple fix? %s" % (inFunc.__module__, funcName, newFuncName, funcType == types.FunctionType and returnFunc is None))
        except AttributeError:
            _logger.warn("%s had no '__name__' attribute" % inFunc)

    timeRangeFlags = _getTimeRangeFlags(funcName)

    # some refactoring done here - to avoid code duplication (and make things clearer),
    # we now ALWAYS do things in the following order:
    # 1. Perform operations which modify the execution of the function (ie, adding return funcs)
    # 2. Modify the function descriptors - ie, __doc__, __name__, etc

    # 1. Perform operations which modify the execution of the function (ie, adding return funcs)

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
                        and all(isinstance(x, (basestring, int, long, float))
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
                    kwargs[flag] = values
            return beforeTimeRangeFunc(*args, **kwargs)
        newFunc = newFuncWithTimeRangeFlags

    if returnFunc:
        # need to define a seperate var here to hold
        # the old value of newFunc, b/c 'return newFunc'
        # would be recursive
        beforeReturnFunc = newFunc

        def newFuncWithReturnFunc(*args, **kwargs):
            res = beforeReturnFunc(*args, **kwargs)
            if not kwargs.get('query', kwargs.get('q', False)):  # and 'edit' not in kwargs and 'e' not in kwargs:
                if isinstance(res, list):
                    # some node commands unnecessarily return a list with a single object
                    if cmdInfo.get('resultNeedsUnpacking', False):
                        res = returnFunc(res[0])
                    else:
                        try:
                            res = map(returnFunc, res)
                        except:
                            pass

                elif res:
                    try:
                        res = returnFunc(res)
                    except Exception, e:
                        pass
            return res
        newFunc = newFuncWithReturnFunc

    createUnpack = cmdInfo.get('resultNeedsUnpacking', False)
    unpackFlags = set()
    for flag, flagInfo in cmdInfo.get('flags', {}).iteritems():
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
        doc = 'Modifications:\n'
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
    _addCmdDocs(newFunc, funcName)

    if rename:
        newFunc.__name__ = rename
    else:
        newFunc.__name__ = funcName

    return newFunc

def makeCreateFlagMethod(inFunc, flag, newMethodName=None, docstring='', cmdName=None, returnFunc=None):
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
        # A command
        def doc_decorator(func):
            try:
                wrappedMelFunc = _addCmdDocs(func, cmdName)
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


def createFunctions(moduleName, returnFunc=None):
    module = sys.modules[moduleName]
    moduleShortName = moduleName.split('.')[-1]
    for funcName in moduleCmds[moduleShortName]:
        if funcName in nodeCommandList:
            func = functionFactory(funcName, returnFunc=returnFunc, module=module)
        else:
            func = functionFactory(funcName, returnFunc=None, module=module)
        if func:
            func.__module__ = moduleName
            setattr(module, funcName, func)


#: overrideMethods specifies methods of base classes which should not be overridden by sub-classes
overrideMethods = {}
overrideMethods['Constraint'] = ('getWeight', 'setWeight')


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
    types = {}
    inCast = {}
    outCast = {}
    refInit = {}
    refCast = {}
    arrayItemTypes = {}
    doc = {}

    @staticmethod
    def _makeRefFunc(capitalizedApiType, size=1, **kwargs):
        """
        Returns a function which will return a SafeApiPtr object of the given
        type.

        This ensures that each created ref stems from a unique MScriptUtil,
        so no two refs point to the same storage!

        :Parameters:
        size : `int`
            If other then 1, the returned function will initialize storage for
            an array of the given size.
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
                raise ValueError, 'Input list must contain exactly %s %ss' % (length, apiTypeName)
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
    def getPymelType(cls, apiType):
        """
        We need a way to map from api name to pymelName.  we start by looking up types which are registered
        and then fall back to naming convention for types that haven't been registered yet. Perhaps pre-register
        the names? """
        try:
            #_logger.debug("getting %s from dict" % apiType)
            return cls.types[apiType]
        except KeyError:
            try:
                # convert to pymel naming convetion  MTime -> Time,  MVector -> Vector
                #_logger.debug("getting pymelName %s" % apiType)
                buf = re.split('(?:MIt)|(?:MFn)|(?:M)', apiType)
                #_logger.debug(buf)
                assert buf[1]
                return buf[1]
            except IndexError:
                raise

    @classmethod
    def isRegistered(cls, apiTypeName):
        return apiTypeName in cls.types

    @classmethod
    def register(cls, apiTypeName, pymelType, inCast=None, outCast=None, apiArrayItemType=None):
        """
        pymelType is the type to be used internally by pymel.  apiType will be hidden from the user
        and converted to the pymel type.
        apiTypeName is the name of an apiType as a string
        if apiArrayItemType is set, it should be the api type that represents each item in the array"""

        #apiTypeName = pymelType.__class__.__name__
        capType = util.capitalize(apiTypeName)

        # register type
        cls.types[apiTypeName] = pymelType.__name__

        if apiArrayItemType:
            cls.arrayItemTypes[apiTypeName] = apiArrayItemType
        # register result casting
        if outCast:
            cls.outCast[apiTypeName] = outCast
        elif apiArrayItemType is not None:
            pass
        else:
            cls.outCast[apiTypeName] = lambda self, x: pymelType(x)

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
                    cls.inCast[apiTypeName] = lambda x: [apiArrayItemType(y) for y in x]
                    cls.refCast[apiTypeName] = None
                    cls.outCast[apiTypeName] = None

            else:
                #-- Api Array types
                if apiArrayItemType:

                    cls.refInit[apiTypeName] = apiType
                    cls.inCast[apiTypeName] = cls._makeApiArraySetter(apiType, apiArrayItemType)
                    # this is double wrapped because of the crashes occuring with MDagPathArray. not sure if it's applicable to all arrays
                    if apiType == api.MDagPathArray:
                        cls.refCast[apiTypeName] = lambda x: [pymelType(apiArrayItemType(x[i])) for i in range(x.length())]
                        cls.outCast[apiTypeName] = lambda self, x: [pymelType(apiArrayItemType(x[i])) for i in range(x.length())]
                    else:
                        cls.refCast[apiTypeName] = lambda x: [pymelType(x[i]) for i in range(x.length())]
                        cls.outCast[apiTypeName] = lambda self, x: [pymelType(x[i]) for i in range(x.length())]

                #-- Api types
                else:
                    cls.refInit[apiTypeName] = apiType
                    cls.refCast[apiTypeName] = pymelType
                    try:
                        # automatically handle array types that correspond to this api type (e.g.  MColor and MColorArray )
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
ApiTypeRegister.register('MString', unicode)
ApiTypeRegister.register('MStringArray', list, apiArrayItemType=unicode)
ApiTypeRegister.register('MIntArray', int, apiArrayItemType=int)
ApiTypeRegister.register('MFloatArray', float, apiArrayItemType=float)
ApiTypeRegister.register('MDoubleArray', float, apiArrayItemType=float)

class ApiArgUtil(object):

    def __init__(self, apiClassName, methodName, methodIndex=0):
        """If methodInfo is None, then the methodIndex will be used to lookup the methodInfo from apiClassInfo"""
        self.apiClassName = apiClassName
        self.methodName = methodName

        if methodIndex is None:
            try:
                methodInfoList = apiClassInfo[apiClassName]['methods'][methodName]
            except KeyError:
                raise TypeError, "method %s of %s cannot be found" % (methodName, apiClassName)
            else:
                for i, methodInfo in enumerate(methodInfoList):

                    #argInfo = methodInfo['argInfo']

                    #argList = methodInfo['args']
                    argHelper = ApiArgUtil(apiClassName, methodName, i)

                    if argHelper.canBeWrapped():
                        methodIndex = i
                        break

                # if it is still None then we didn't find anything
                if methodIndex is None:
                    raise TypeError, "method %s of %s cannot be wrapped" % (methodName, apiClassName)

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
        return self.methodInfo['inArgs']

    def outArgs(self):
        return self.methodInfo['outArgs']

    def argList(self):
        return self.methodInfo['args']

    def argInfo(self):
        return self.methodInfo['argInfo']

    def getGetterInfo(self):
        try:
            inverse, isgetter = self.methodInfo['inverse']
            if isgetter:
                if hasattr(getattr(api, self.apiClassName), inverse):
                    return ApiArgUtil(self.apiClassName, inverse, self.methodIndex)
        except:
            pass

    @staticmethod
    def isValidEnum(enumTuple):
        if apiClassInfo.has_key(enumTuple[0]) and \
                apiClassInfo[enumTuple[0]]['enums'].has_key(enumTuple[1]):
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
                    assert  returnType in ApiTypeRegister.outCast or \
                        returnType == self.apiClassName, \
                        '%s.%s(): invalid return type: %s' % (self.apiClassName, self.methodName, returnType)

            for argname, argtype, direction in self.methodInfo['args']:
                # Enum
                if isinstance(argtype, tuple):
                    assert self.isValidEnum(argtype), '%s.%s(): %s: invalid enum: %s' % (self.apiClassName, self.methodName, argname, argtype)

                # Input
                else:
                    if direction == 'in':
                        assert  argtype in ApiTypeRegister.inCast or \
                            defaults.has_key(argname) or \
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
        except AssertionError, msg:
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
        inArgs = self.methodInfo['inArgs']
        types = self.methodInfo['types']
        return [str(types[x]) for x in inArgs]

    def getOutputTypes(self):
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
        pymelName = self.methodInfo.get('pymelName', self.methodName)
        try:
            pymelClassName = apiClassNamesToPyNodeNames[self.apiClassName]
            pymelName, data = _getApiOverrideNameAndData(pymelClassName, pymelName)
        except KeyError:
            pass
        return pymelName

    def getMethodDocs(self):
        return self.methodInfo['doc']

    def getPrototype(self, className=True, methodName=True, outputs=False, defaults=False):
        inArgs = self.methodInfo['inArgs']
        outArgs = self.methodInfo['outArgs']
        returnType = self.methodInfo['returnType']
        types = self.methodInfo['types']
        args = []

        for x in inArgs:
            arg = str(types[x]) + ' ' + x
            if defaults:
                try:
                    #_logger.debug(self.methodInfo['defaults'][x])
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

    def castInput(self, argName, input, cls):
        # enums
        argtype = self.methodInfo['types'][argName]
        if isinstance(argtype, tuple):
            # convert enum as a string or int to an int

            # if isinstance( input, int):
            #    return input

            apiClassName, enumName = argtype
            return self.castInputEnum(apiClassName, enumName, input)

        elif input is not None:
            #            try:

            f = ApiTypeRegister.inCast[argtype]
            if f is None:
                return input

            input = self.toInternalUnits(argName, input)
            return f(input)
#            except:
#                if input is None:
#                    # we should do a check to ensure that the default is None, but for now, just return
#                    return input
#                if argtype != cls.__name__:
#                    raise TypeError, "Cannot cast a %s to %s" % ( type(input).__name__, argtype )
#                return cls(input)

    @classmethod
    def castInputEnum(cls, apiClassName, enumName, input):
        # pymelEnums should now have both api key names ("kPostTransform") and
        # pymel names ("postTransform") available as keys now, with the pymel
        # form the default... so only need to check pymelEnum, not
        #  apiClassInfo[apiClassName]['enums'][enumName]['values'].getIndex(input)
        try:
            return apiClassInfo[apiClassName]['pymelEnums'][enumName].getIndex(input)
        except ValueError:
            raise ValueError, "expected an enum of type %s.%s: got %r" % (apiClassName, enumName, input)

    def fromInternalUnits(self, result, instance=None):
        # units
        unit = self.methodInfo['returnInfo'].get('unitType', None)
        returnType = self.methodInfo['returnInfo']['type']
        #_logger.debug(unit)
        # returnType in ['MPoint'] or
        if unit == 'linear' or returnType == 'MPoint':
            unitCast = ApiTypeRegister.outCast['MDistance']
            if util.isIterable(result):
                result = [unitCast(instance, val) for val in result]
            else:
                result = unitCast(instance, result)

        # maybe this should not be hardwired here
        # the main reason it is hardwired is because we don't want to convert the w component, which we
        # would do if we iterated normally
        elif returnType == 'MPoint':
            #_logger.debug("linear")
            unitCast = ApiTypeRegister.outCast['MDistance']
            result = [unitCast(instance, result[0]), unitCast(instance, result[1]), unitCast(instance, result[2])]

        elif unit == 'angular':
            #_logger.debug("angular")
            unitCast = ApiTypeRegister.outCast['MAngle']
            if util.isIterable(result):
                result = [unitCast(instance, val) for val in result]
            else:
                result = unitCast(instance, result)
        return result

    def toInternalUnits(self, arg, input):
        # units
        info = self.methodInfo['argInfo'][arg]
        unit = info.get('unitType', None)
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

    def castResult(self, instance, result):
        returnType = self.methodInfo['returnType']
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
                    return apiClassInfo[apiClassName]['pymelEnums'][enumName][result]
                except KeyError:
                    raise ValueError, "expected an enum of type %s.%s" % (apiClassName, enumName)

            else:
                # try:
                f = ApiTypeRegister.outCast[returnType]
                if f is None:
                    return result

                result = self.fromInternalUnits(result, instance)

                return f(instance, result)
#                except:
#                    cls = instance.__class__
#                    if returnType != cls.__name__:
#                        raise TypeError, "Cannot cast a %s to %s" % ( type(result).__name__, returnType )
#                    return cls(result)

    def initReference(self, argtype):
        return ApiTypeRegister.refInit[argtype]()

    def castReferenceResult(self, argtype, outArg):
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

        result = self.fromInternalUnits(outArg)
        return f(result)

    def getDefaults(self):
        "get a list of defaults"
        defaults = []
        defaultInfo = self.methodInfo['defaults']
        inArgs = self.methodInfo['inArgs']
        nargs = len(inArgs)
        for i, arg in enumerate(inArgs):
            if arg in defaultInfo:
                default = defaultInfo[arg]

            # FIXME : these defaults should probably not be set here since this is supposed to be
            # a "dumb" registry of data.  perhaps move them to the controlPanel

            # set MSpace.Space enum to object space by default, but only if it is the last arg or
            # the next arg has a default ( i.e. kwargs must always come after args )
#            elif str(self.methodInfo['types'][arg]) == 'MSpace.Space' and \
#                (   i==(nargs-1) or ( i<(nargs-1) and inArgs[i+1] in defaultInfo )  ):
#                    default = apicache.ApiEnum(['MSpace', 'Space', 'kWorld'])  # should be kPostTransform?  this is what xform defaults to...

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


class ApiUndo(object):

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
    __metaclass__ = util.Singleton

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
                       d=['UndoAvailable', 'RedoAvailable'],
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

    def _attrChanged_85(self):
        print "attr changed", self.cb_enabled, api.MGlobal.isUndoing()
        if self.cb_enabled:

            if api.MGlobal.isUndoing():
                cmdObj = self.undo_queue.pop()
                print "calling undoIt"
                cmdObj.undoIt()
                self.redo_queue.append(cmdObj)

            elif api.MGlobal.isRedoing():
                cmdObj = self.redo_queue.pop()
                print "calling redoIt"
                cmdObj.redoIt()
                self.undo_queue.append(cmdObj)

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

    def append(self, cmdObj):
        if not self.undoStateCallbackId:
            self.installUndoStateCallbacks()

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

            cmds.setAttr(self.node_name + '.cmdCount', count + 1)

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

    def redoIt(self):
        self._setter(*self._redo_args, **self._redo_kwargs)
    doIt = redoIt

    def undoIt(self):
        self._setter(*self._undo_args, **self._undo_kwargs)


class ApiRedoUndoItem(ApiUndoItem):

    """Similar to the base ApiUndoItem, but allows specifying a separate
    function for the redoer and the undoer"""
    __slots__ = ['_undoer']

    def __init__(self, redoer, redoArgs, undoer, undoArgs, redoKwargs=None,
                 undoKwargs=None):
        super(ApiRedoUndoItem, self).__init__(redoer, redoArgs, undoArgs,
                                              redoKwargs=redoKwargs,
                                              undoKwargs=undoKwargs)
        self._undoer = undoer

    def undoIt(self):
        self._undoer(*self._undo_args, **self._undo_kwargs)

_DEBUG_API_WRAPS = False
if _DEBUG_API_WRAPS:
    _apiMethodWraps = {}

def wrapApiMethod(apiClass, methodName, newName=None, proxy=True, overloadIndex=None):
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


    :Parameters:

        apiClass : class
            the api class
        methodName : string
            the name of the api method
        newName : string
            optionally provided if a name other than that of api method is desired
        proxy : bool
            If True, then __apimfn__ function used to retrieve the proxy class. If False,
            then we assume that the class being wrapped inherits from the underlying api class.
        overloadIndex : None or int
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

    if argHelper.canBeWrapped():

        if argHelper.isDeprecated():
            _logger.debug("%s.%s is deprecated" % (apiClassName, methodName))
        inArgs = argHelper.inArgs()
        outArgs = argHelper.outArgs()
        argList = argHelper.argList()
        argInfo = argHelper.argInfo()

        getterArgHelper = argHelper.getGetterInfo()

        if argHelper.hasOutput():
            getterInArgs = []
            # query method ( getter )
            # if argHelper.getGetterInfo() is not None:

            # temporarily supress this warning, until we get a deeper level
#            if getterArgHelper is not None:
#                _logger.warn( "%s.%s has an inverse %s, but it has outputs, which is not allowed for a 'setter'" % (
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
            do_args = []
            outTypeList = []

            undoEnabled = getterArgHelper is not None and cmds.undoInfo(q=1, state=1) and apiUndo.cb_enabled
            #outTypeIndex = []

            if len(args) != len(inArgs):
                raise TypeError, "%s() takes exactly %s arguments (%s given)" % (methodName, len(inArgs), len(args))

            # get the value we are about to set
            if undoEnabled:
                getterArgs = []  # args required to get the current state before setting it
                undo_args = []  # args required to reset back to the original (starting) state  ( aka "undo" )
                missingUndoIndices = []  # indices for undo args that are not shared with the setter and which need to be filled by the result of the getter
                inCount = 0
                for name, argtype, direction in argList:
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

                getter = getattr(self, getterArgHelper.getPymelName())
                setter = getattr(self, pymelName)

                try:
                    getterResult = getter(*getterArgs)
                except RuntimeError:
                    _logger.error("the arguments at time of error were %r" % getterArgs)
                    raise

                # when a command returns results normally and passes additional outputs by reference, the result is returned as a tuple
                # otherwise, always as a list
                if not isinstance(getterResult, tuple):
                    getterResult = (getterResult,)

                for index, result in zip(missingUndoIndices, getterResult):
                    undo_args[index] = result

            inCount = totalCount = 0
            for name, argtype, direction in argList:
                if direction == 'in':
                    arg = args[inCount]
                    do_args.append(argHelper.castInput(name, arg, self.__class__))
                    inCount += 1
                else:
                    val = argHelper.initReference(argtype)
                    do_args.append(val)
                    outTypeList.append((argtype, totalCount))
                    #outTypeIndex.append( totalCount )
                totalCount += 1

            if undoEnabled:
                undoItem = ApiUndoItem(setter, do_args, undo_args)
                apiUndo.append(undoItem)

            # Do final SafeApiPtr => 'true' ptr conversion
            final_do_args = []
            for arg in do_args:
                if isinstance(arg, api.SafeApiPtr):
                    final_do_args.append(arg())
                else:
                    final_do_args.append(arg)
            if argHelper.isStatic():
                result = method(*final_do_args)
            else:
                if proxy:
                    # due to the discrepancies between the API and Maya node hierarchies, our __apimfn__ might not be a
                    # subclass of the api class being wrapped, however, the api object can still be used with this mfn explicitly.
                    mfn = self.__apimfn__()
                    if not isinstance(mfn, apiClass):
                        mfn = apiClass(self.__apiobject__())
                    result = method(mfn, *final_do_args)
                else:
                    result = method(self, *final_do_args)
            result = argHelper.castResult(self, result)

            if len(outArgs):
                if result is not None:
                    result = [result]
                else:
                    result = []

                for outType, index in outTypeList:
                    outArgVal = do_args[index]
                    res = argHelper.castReferenceResult(outType, outArgVal)
                    result.append(res)

                if len(result) == 1:
                    result = result[0]
                else:
                    result = tuple(result)
            return result

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

        wrappedApiFunc = util.interface_wrapper(wrappedApiFunc, ['self'] + inArgs, defaults=defaults)
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
            beforeDeprecationWrapper = wrappedApiFunc

            def wrappedApiFunc(*args, **kwargs):
                import warnings
                warnings.warn("%s.%s is deprecated" % (apiClassName,
                                                       methodName),
                              DeprecationWarning, stacklevel=2)
                beforeDeprecationWrapper(*args, **kwargs)
        return wrappedApiFunc

def addApiDocs(apiClass, methodName, overloadIndex=None, undoable=True):
    """decorator for adding API docs"""

    def doc_decorator(func):
        return _addApiDocs(func, apiClass, methodName, overloadIndex, undoable)

    return doc_decorator

def _addApiDocs(wrappedApiFunc, apiClass, methodName, overloadIndex=None, undoable=True):

    util.addLazyDocString(wrappedApiFunc, addApiDocsCallback, apiClass, methodName, overloadIndex, undoable, wrappedApiFunc.__doc__)
    return wrappedApiFunc

def addApiDocsCallback(apiClass, methodName, overloadIndex=None, undoable=True, origDocstring=''):
    apiClassName = apiClass.__name__

    argHelper = ApiArgUtil(apiClassName, methodName, overloadIndex)
    inArgs = argHelper.inArgs()
    outArgs = argHelper.outArgs()
    argList = argHelper.argList()
    argInfo = argHelper.argInfo()

    def formatDocstring(type):
        """
        convert
        "['one', 'two', 'three', ['1', '2', '3']]"
        to
        "[`one`, `two`, `three`, [`1`, `2`, `3`]]"
        """
        if not isinstance(type, list):
            pymelType = ApiTypeRegister.types.get(type, type)
        else:
            pymelType = type

        if isinstance(pymelType, apicache.ApiEnum):
            pymelType = pymelType.pymelName()

        doc = repr(pymelType).replace("'", "`")
        if type in ApiTypeRegister.arrayItemTypes.keys():
            doc += ' list'
        return doc

    # Docstrings
    docstring = argHelper.getMethodDocs()
    # api is no longer in specific units, it respect UI units like MEL
    docstring = docstring.replace('centimeter', 'linear unit')
    docstring = docstring.replace('radian', 'angular unit')

    S = '    '
    if len(inArgs):
        docstring += '\n\n:Parameters:\n'
        for name in inArgs:
            info = argInfo[name]
            type = info['type']
            typeStr = formatDocstring(type)

            docstring += S + '%s : %s\n' % (name, typeStr)
            docstring += S * 2 + '%s\n' % (info['doc'])
            if isinstance(type, apicache.ApiEnum):
                apiClassName, enumName = type
                enumValues = apiClassInfo[apiClassName]['pymelEnums'][enumName].keys()
                docstring += '\n' + S * 2 + 'values: %s\n' % ', '.join(['%r' % x for x in enumValues if x not in ['invalid', 'last']])

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
        results = results[0]
        docstring += '\n\n:rtype: %s\n' % results
    elif results:
        docstring += '\n\n:rtype: (%s)\n' % ', '.join(results)

    docstring += '\nDerived from api method `%s.%s.%s`\n' % (apiClass.__module__, apiClassName, methodName)
    if not undoable:
        docstring += '\n**Undo is not currently supported for this method**\n'

    if origDocstring:
        docstring = origDocstring + '\n' + docstring

    return docstring

class MetaMayaTypeWrapper(util.metaReadOnlyAttr):

    """ A metaclass to wrap Maya api types, with support for class constants """

    _originalApiSetAttrs = {}

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
                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)

        def __set__(self, instance, value):
            raise AttributeError, "class constant cannot be set"

        def __delete__(self, instance):
            raise AttributeError, "class constant cannot be deleted"

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
            if apicls.__name__ not in apiClassNamesToPyNodeNames:
                #_logger.debug("ADDING %s to %s" % (apicls.__name__, classname))
                apiClassNamesToPyNodeNames[apicls.__name__] = classname

            if not proxy and apicls not in bases:
                #_logger.debug("ADDING BASE %s" % classdict['apicls'])
                bases = bases + (classdict['apicls'],)
            try:
                classInfo = apiClassInfo[apicls.__name__]
            except KeyError:
                _logger.info("No api information for api class %s" % (apicls.__name__))
            else:
                #------------------------
                # API Wrap
                #------------------------

                # Find out methods herited from other bases than apicls to avoid
                # unwanted overloading
                herited = {}
                for base in bases:
                    if base is not apicls:
                        # basemro = inspect.getmro(base)
                        for attr in dir(base):
                            if attr not in herited:
                                herited[attr] = base

                ##_logger.debug("Methods info: %(methods)s" % classInfo)
                # Class Methods
                for methodName, info in classInfo['methods'].items():
                    # don't rewrap if already herited from a base class that is not the apicls
                    #_logger.debug("Checking method %s" % (methodName))

                    try:
                        pymelName = info[0]['pymelName']
                        removeAttrs.append(methodName)
                    except KeyError:
                        pymelName = methodName

#                    if classname == 'DependNode' and pymelName in ('setName','getName'):
#                        raise Exception('debug')

                    pymelName, data = _getApiOverrideNameAndData(classname, pymelName)

                    overloadIndex = data.get('overloadIndex', None)

                    assert isinstance(pymelName, str), "%s.%s: %r is not a valid name" % (classname, methodName, pymelName)

                    # TODO: some methods are being wrapped for the base class,
                    # and all their children - ie, MFnTransform.transformation()
                    # gets wrapped for Transform, Place3dTexture,
                    # HikGroundPlane, etc...
                    # Figure out why this happens, and stop it!
                    if pymelName not in herited:
                        if overloadIndex is not None:
                            if data.get('enabled', True):
                                if pymelName not in classdict:
                                    #_logger.debug("%s.%s autowrapping %s.%s usng proxy %r" % (classname, pymelName, apicls.__name__, methodName, proxy))
                                    method = wrapApiMethod(apicls, methodName, newName=pymelName, proxy=proxy, overloadIndex=overloadIndex)
                                    if method:
                                        #_logger.debug("%s.%s successfully created" % (classname, pymelName ))
                                        classdict[pymelName] = method
                                    # else: #_logger.debug("%s.%s: wrapApiMethod failed to create method" % (apicls.__name__, methodName ))
                                # else: #_logger.debug("%s.%s: skipping" % (apicls.__name__, methodName ))
                            # else: #_logger.debug("%s.%s has been manually disabled, skipping" % (apicls.__name__, methodName))
                        # else: #_logger.debug("%s.%s has no wrappable methods, skipping" % (apicls.__name__, methodName))
                    # else: #_logger.debug("%s.%s already herited from %s, skipping" % (apicls.__name__, methodName, herited[pymelName]))

                if 'pymelEnums' in classInfo:
                    # Enumerators

                    for enumName, enum in classInfo['pymelEnums'].items():
                        classdict[enumName] = enum

            if not proxy:
                # if removeAttrs:
                #    #_logger.debug( "%s: removing attributes %s" % (classname, removeAttrs) )
                def __getattribute__(self, name):
                    #_logger.debug(name )
                    if name in removeAttrs and name not in EXCLUDE_METHODS:  # tmp fix
                        #_logger.debug("raising error")
                        raise AttributeError, "'" + classname + "' object has no attribute '" + name + "'"
                    #_logger.debug("getting from %s" % bases[0])
                    # newcls will be defined by the time this is called...
                    return super(newcls, self).__getattribute__(name)

                classdict['__getattribute__'] = __getattribute__

                if cls._hasApiSetAttrBug(apicls):
                    # correct the setAttr bug by wrapping the api's
                    # __setattr__ to handle data descriptors...
                    origSetAttr = apicls.__setattr__
                    # in case we need to restore the original setattr later...
                    # ... as we do in a test for this bug!
                    cls._originalApiSetAttrs[apicls] = origSetAttr

                    def apiSetAttrWrap(self, name, value):
                        if hasattr(self.__class__, name):
                            if hasattr(getattr(self.__class__, name), '__set__'):
                                # we've got a data descriptor with a __set__...
                                # don't use the apicls's __setattr__
                                return super(apicls, self).__setattr__(name, value)
                        return origSetAttr(self, name, value)
                    apicls.__setattr__ = apiSetAttrWrap

        # create the new class
        newcls = super(MetaMayaTypeWrapper, cls).__new__(cls, classname, bases, classdict)

        # shortcut for ensuring that our class constants are the same type as the class we are creating
        def makeClassConstant(attr):
            try:
                # return MetaMayaTypeWrapper.ClassConstant(newcls(attr))
                return MetaMayaTypeWrapper.ClassConstant(attr)
            except Exception, e:
                _logger.warn("Failed creating %s class constant (%s): %s" % (classname, attr, e))
        #------------------------
        # Class Constants
        #------------------------
        if hasattr(newcls, 'apicls'):
            # type (api type) used for the storage of data
            apicls = newcls.apicls
            if apicls is not None:
                # build some constants on the class
                constant = {}
                # constants in class definition will be converted from api class to created class
                for name, attr in newcls.__dict__.iteritems():
                    # to add the wrapped api class constants as attributes on the wrapping class,
                    # convert them to own class
                    if isinstance(attr, apicls):
                        if name not in constant:
                            constant[name] = makeClassConstant(attr)
                # we'll need the api clas dict to automate some of the wrapping
                # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping
                apiDict = dict(inspect.getmembers(apicls))
                # defining class properties on the created class
                for name, attr in apiDict.iteritems():
                    # to add the wrapped api class constants as attributes on the wrapping class,
                    # convert them to own class
                    if isinstance(attr, apicls):
                        if name not in constant:
                            constant[name] = makeClassConstant(attr)
                # update the constant dict with herited constants
                mro = inspect.getmro(newcls)
                for parentCls in mro:
                    if isinstance(parentCls, MetaMayaTypeWrapper):
                        for name, attr in parentCls.__dict__.iteritems():
                            if isinstance(attr, MetaMayaTypeWrapper.ClassConstant):
                                if not name in constant:
                                    constant[name] = makeClassConstant(attr.value)

                # build the protected list to make some class ifo and the constants read only class attributes
                # new.__slots__ = ['_data', '_shape', '_ndim', '_size']
                # type.__setattr__(newcls, '__slots__', slots)

                # set class constants as readonly
#                readonly = newcls.__readonly__
#                if 'apicls' not in readonly :
#                    readonly['apicls'] = None
#                for c in constant.keys() :
#                    readonly[c] = None
#                type.__setattr__(newcls, '__readonly__', readonly)
                # store constants as class attributes
                for name, attr in constant.iteritems():
                    type.__setattr__(newcls, name, attr)

            # else :   raise TypeError, "must define 'apicls' in the class definition (which Maya API class to wrap)"

        if hasattr(newcls, 'apicls') and not ApiTypeRegister.isRegistered(newcls.apicls.__name__):
            ApiTypeRegister.register(newcls.apicls.__name__, newcls)

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
        return bool(foo2.bar != 7)

class _MetaMayaCommandWrapper(MetaMayaTypeWrapper):

    """
    A metaclass for creating classes based on a maya command.

    Not intended to be used directly; instead, use the descendants: MetaMayaNodeWrapper, MetaMayaUIWrapper
    """

    _classDictKeyForMelCmd = None

    def __new__(cls, classname, bases, classdict):
        #_logger.debug( '_MetaMayaCommandWrapper: %s' % classname )

        newcls = super(_MetaMayaCommandWrapper, cls).__new__(cls, classname, bases, classdict)

        #-------------------------
        #   MEL Methods
        #-------------------------
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

            filterAttrs = ['name', 'getName', 'setName'] + classdict.keys()
            filterAttrs += overrideMethods.get(bases[0].__name__, [])
            #filterAttrs += newcls.__dict__.keys()

            parentClasses = [x.__name__ for x in inspect.getmro(newcls)[1:]]
            for flag, flagInfo in cmdInfo['flags'].items():
                # don't create methods for query or edit, or for flags which only serve to modify other flags
                if flag in ['query', 'edit'] or 'modified' in flagInfo:
                    continue

                if flagInfo.has_key('modes'):
                    # flags which are not in maya docs will have not have a modes list unless they
                    # have passed through testNodeCmds
                    # continue
                    modes = flagInfo['modes']

                    # query command
                    if 'query' in modes:
                        methodName = 'get' + util.capitalize(flag)
                        classToMelMap[classname].append(methodName)

                        if methodName not in filterAttrs and \
                                (not hasattr(newcls, methodName) or cls.isMelMethod(methodName, parentClasses)):

                            # 'enabled' refers to whether the API version of this method will be used.
                            # if the method is enabled that means we skip it here.
                            if (not apiToMelData.has_key((classname, methodName))
                                    or apiToMelData[(classname, methodName)].get('melEnabled', False)
                                    or not apiToMelData[(classname, methodName)].get('enabled', True)):
                                returnFunc = None

                                if flagInfo.get('resultNeedsCasting', False):
                                    returnFunc = flagInfo['args']

                                # don't unpack if the source i
                                if (flagInfo.get('resultNeedsUnpacking', False)
                                        and not pmSourceFunc):
                                    if returnFunc:
                                        # can't do:
                                        #   returnFunc = lambda x: returnFunc(x[0])
                                        # ... as this would create a recursive function!
                                        origReturnFunc = returnFunc
                                        returnFunc = lambda x: origReturnFunc(x[0])
                                    else:
                                        returnFunc = lambda x: x[0]

                                wrappedMelFunc = makeQueryFlagMethod(func, flag, methodName,
                                                                     returnFunc=returnFunc)

                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                classdict[methodName] = wrappedMelFunc
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled or overridden by API" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))
                    # edit command:
                    if 'edit' in modes or (infoCmd and 'create' in modes):
                        # if there is a corresponding query we use the 'set' prefix.
                        if 'query' in modes:
                            methodName = 'set' + util.capitalize(flag)
                        # if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
                        else:
                            methodName = flag

                        classToMelMap[classname].append(methodName)

                        if methodName not in filterAttrs and \
                                (not hasattr(newcls, methodName) or cls.isMelMethod(methodName, parentClasses)):
                            if not apiToMelData.has_key((classname, methodName)) \
                                    or apiToMelData[(classname, methodName)].get('melEnabled', False) \
                                    or not apiToMelData[(classname, methodName)].get('enabled', True):
                                # FIXME: shouldn't we be able to use the wrapped pymel command, which is already fixed?
                                fixedFunc = fixCallbacks(func, melCmdName)

                                wrappedMelFunc = makeEditFlagMethod(fixedFunc, flag, methodName)
                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                classdict[methodName] = wrappedMelFunc
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))

        for name, attr in classdict.iteritems():
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
    def isMelMethod(cls, methodName, parentClassList):
        """
        Deteremine if the passed method name exists on a parent class as a mel method
        """
        for classname in parentClassList:
            if methodName in classToMelMap[classname]:
                return True
        return False

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
        # If the class explicitly gives it's mel node name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        #_logger.debug( 'MetaMayaNodeWrapper: %s' % classname )
        nodeType = classdict.get('__melnode__')

        if nodeType is None:
            # check for a virtual class...
            if '_isVirtual' in classdict or any(hasattr(b, '_isVirtual')
                                                for b in bases):
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

        addMayaType(nodeType)
        apicls = toApiFunctionSet(nodeType)
        if apicls is not None:
            classdict['__apicls__'] = apicls

        PyNodeType = super(MetaMayaNodeWrapper, cls).__new__(cls, classname, bases, classdict)
        ParentPyNode = [x for x in bases if issubclass(x, util.ProxyUnicode)]
        assert len(ParentPyNode), "%s did not have exactly one parent PyNode: %s (%s)" % (classname, ParentPyNode, bases)
        addPyNodeType(PyNodeType, ParentPyNode)
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

class MetaMayaComponentWrapper(MetaMayaTypeWrapper):

    """
    A metaclass for creating components.
    """
    def __new__(cls, classname, bases, classdict):
        newcls = super(MetaMayaComponentWrapper, cls).__new__(cls, classname, bases, classdict)
        apienum = getattr(newcls, '_apienum__', None)
#        print "addng new component %s - '%s' (%r):" % (newcls, classname, classdict),
        if apienum:
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


def addPyNodeCallback(dynModule, mayaType, pyNodeTypeName, parentPyNodeTypeName, extraAttrs=None):
    #_logger.debug( "%s(%s): creating" % (pyNodeTypeName,parentPyNodeTypeName) )
    try:
        ParentPyNode = getattr(dynModule, parentPyNodeTypeName)
    except AttributeError:
        _logger.debug("error creating class %s: parent class %r not in dynModule %s" % (pyNodeTypeName, parentPyNodeTypeName, dynModule.__name__))
        return

    classDict = {'__melnode__': mayaType}
    if extraAttrs:
        classDict.update(extraAttrs)
    if pyNodeTypeName in pyNodeNamesToPyNodes:
        PyNodeType = pyNodeNamesToPyNodes[pyNodeTypeName]
    else:
        try:
            PyNodeType = MetaMayaNodeWrapper(pyNodeTypeName, (ParentPyNode,), classDict)
        except TypeError, msg:
            # for the error: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
            _logger.error("Could not create new PyNode: %s(%s): %s" % (pyNodeTypeName, ParentPyNode.__name__, msg))
            import new
            PyNodeType = new.classobj(pyNodeTypeName, (ParentPyNode,), {})
            #_logger.debug(("Created new PyNode: %s(%s)" % (pyNodeTypeName, parentPyNodeTypeName)))

        PyNodeType.__module__ = dynModule.__name__
    setattr(dynModule, pyNodeTypeName, PyNodeType)
    return PyNodeType

def addCustomPyNode(dynModule, mayaType, extraAttrs=None):
    """
    create a PyNode, also adding each member in the given maya node's inheritance if it does not exist.

    This function is used for creating PyNodes via plugins, where the nodes parent's might be abstract
    types not yet created by pymel.  also, this function ensures that the newly created node types are
    added to pymel.all, if that module has been imported.

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
        _logger.warn("could not get inheritance for mayaType %s" % mayaType)
    else:
        #__logger.debug(mayaType, inheritance)
        #__logger.debug("adding new node:", mayaType, apiEnum, inheritence)
        # some nodes in the hierarchy for this node might not exist, so we cycle through all
        parent = 'dependNode'

        for node in inheritance:
            nodeName = addPyNode(dynModule, node, parent, extraAttrs=extraAttrs)
            parent = node
            if 'pymel.all' in sys.modules:
                # getattr forces loading of Lazy object
                setattr(sys.modules['pymel.all'], nodeName, getattr(dynModule, nodeName))

def addPyNode(dynModule, mayaType, parentMayaType, extraAttrs=None):
    """
    create a PyNode type for a maya node.
    """

    #_logger.debug("addPyNode adding %s->%s on dynModule %s" % (mayaType, parentMayaType, dynModule))
    # unicode is not liked by metaNode
    pyNodeTypeName = str(util.capitalize(mayaType))
    parentPyNodeTypeName = str(util.capitalize(parentMayaType))

    # If pymel.all is loaded, we will need to get the actual node in order to
    # store it on pymel.all, so in that case don't bother with the lazy-loading
    # behavior...
    if 'pymel.all' in sys.modules:
        newType = addPyNodeCallback(dynModule, mayaType, pyNodeTypeName, parentPyNodeTypeName, extraAttrs)
        setattr(sys.modules['pymel.all'], pyNodeTypeName, newType)
    # otherwise, do the lazy-loading thing
    else:
        try:
            dynModule[pyNodeTypeName]
        except KeyError:
            #_logger.info( "%s(%s): setting up lazy loading" % ( pyNodeTypeName, parentPyNodeTypeName ) )
            dynModule[pyNodeTypeName] = (addPyNodeCallback,
                                         (dynModule, mayaType, pyNodeTypeName, parentPyNodeTypeName, extraAttrs))
    return pyNodeTypeName

def removePyNode(dynModule, mayaType):
    pyNodeTypeName = str(util.capitalize(mayaType))
    removePyNodeType(pyNodeTypeName)

    _logger.debug('removing %s from %s' % (pyNodeTypeName, dynModule.__name__))
    dynModule.__dict__.pop(pyNodeTypeName, None)

    # delete the lazy loader too, so it does not regenerate the object
    # Note - even doing a 'hasattr' will trigger the lazy loader, so just
    # delete blind!
    try:
        delattr(dynModule.__class__, pyNodeTypeName)
    except Exception:
        pass
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
    if apiType is None:
        apiType = mayaTypeToApiType(mayaType)

    global _apiCacheInst
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

        :parameters:
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
                    raise ValueError, 'invalid attribute name(s) %s: these special attributes are not allowed on virtual nodes' % ', '.join(badAttrs)

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

        vClassInfo = VirtualClassInfo(vclass, parentCls, nameRequired, isVirtual, preCreate, create, postCreate)
        self._byParentClass[parentCls].append(vClassInfo)
        self._byVirtualClass[vclass] = vClassInfo

    def unregister(self, vcls):
        try:
            vClassInfo = self._byVirtualClass.pop(vcls)
        except KeyError:
            raise VirtualClassError('%r was not registered as a virtual class' % vcls)
        self._byParentClass[vClassInfo.parent].remove(vClassInfo)

    def getVirtualClass(self, baseClass, obj, name=None, fnDepend=None):
        '''Returns the virtual class to use for the given baseClass + obj, or
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
        '''Given a virtual class, returns it's registered VirtualClassInfo
        '''
        return self._byVirtualClass.get(vclass)

virtualClasses = VirtualClassManager()

# for backwards compatibility + ease of access
registerVirtualClass = virtualClasses.register

#-------------------------------------------------------------------------------

def isValidPyNode(arg):
    return pyNodeTypesHierarchy.has_key(arg)

def isValidPyNodeName(arg):
    return pyNodeNamesToPyNodes.has_key(arg)

def toApiTypeStr(obj, default=None):
    if isinstance(obj, int):
        return apiEnumsToApiTypes.get(obj, default)
    elif isinstance(obj, basestring):
        return mayaTypesToApiTypes.get(obj, default)
    elif isinstance(obj, util.ProxyUnicode):
        mayaType = getattr(obj, '__melnode__', None)
        return mayaTypesToApiTypes.get(mayaType, default)

def toApiTypeEnum(obj, default=None):
    if isinstance(obj, util.ProxyUnicode):
        obj = getattr(obj, '__melnode__', default)
    try:
        return apiTypesToApiEnums[obj]
    except KeyError:
        return mayaTypesToApiEnums.get(obj, default)

def toApiFunctionSet(obj):
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
    '''Given the name of an api class, such as MFnTransform, MSpace, MAngle,
    returns the name of the corresponding pymel class.

    If allowGuessing, and we cannot find a registered type that matches, will
    try to do string parsing to guess the pymel name.

    Returns None if it was unable to determine the name.
    '''
    pymelName = apiClassNamesToPyNodeNames.get(apiName, None)
    if pymelName is None:
        if allowGuess:
            try:
                pymelName = ApiTypeRegister.getPymelType(apiName)
            except Exception:
                pass
        else:
            pymelName = ApiTypeRegister.types.get(apiName, None)
    return pymelName

# get the API type from a maya type
def mayaTypeToApiType(mayaType):
    """ Get the Maya API type from the name of a Maya type """
    try:
        return mayaTypesToApiTypes[mayaType]
    except KeyError:
        apiType = None
        if versions.current() >= versions.v2012:
            import pymel.api.plugins as plugins
            try:
                inheritance = apicache.getInheritance(mayaType,
                                                      checkManip3D=False)
            except Exception:
                inheritance = None
            if inheritance:
                for mayaType in reversed(inheritance[:-1]):
                    apiType = mayaTypesToApiTypes.get(mayaType)
                    if apiType:
                        break

        if not apiType:
            apiType = 'kInvalid'
            # we need to actually create the obj to query it...
            with apicache._GhostObjMaker(mayaType) as obj:
                if obj is not None and api.isValidMObject(obj):
                    apiType = obj.apiTypeStr()
        mayaTypesToApiTypes[mayaType] = apiType
        return apiType

def isMayaType(mayaType):
    '''Whether the given type is a currently-defined maya node name
    '''
    # using objectType instead of MNodeClass or nodeType(isTypeName) because
    # it's available < 2012
    return bool(cmds.objectType(tagFromType=mayaType))

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

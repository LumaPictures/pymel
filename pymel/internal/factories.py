"""
Contains the wrapping mechanisms that allows pymel to integrate the api and maya.cmds into a unified interface
"""
import re, types, os, inspect, sys, textwrap
from operator import itemgetter
import pymel.util as util
import pymel.api as api
from startup import loadCache
import plogging as plogging
import cmdcache
from cmdcache import *
import apicache
from apicache import *
import pmcmds
import maya.cmds as cmds
import maya.mel as mm


_logger = plogging.getLogger(__name__)

#---------------------------------------------------------------
#        Mappings and Lists
#---------------------------------------------------------------

DOC_WIDTH = 120

EXCLUDE_METHODS = ['type', 'className', 'create', 'name' ]

#: examples are usually only included when creating documentation
includeDocExamples = bool( os.environ.get( 'PYMEL_INCLUDE_EXAMPLES', False ) )

#Lookup from PyNode type name as a string to PyNode type as a class
pyNodeNamesToPyNodes = {}

#Lookup from PyNode class to maya type
pyNodesToMayaTypes = {}

#Lookup from MFn to PyNode name
apiClassNamesToPyNodeNames = {}

#Lookup from Api Enums to Pymel Component Classes
#
#A list of possible component classes is always returned (even if it's only
#of length one).
apiEnumsToPyComponents = {}

#child:parent lookup of the pymel classes that derive from DependNode
pyNodeTypesHierarchy = {}


#: for certain nodes, the best command on which to base the node class cannot create nodes, but can only provide information.
#: these commands require special treatment during class generation because, for them the 'create' mode is the same as other node's 'edit' mode
nodeTypeToInfoCommand = {
    #'mesh' : 'polyEvaluate',
    'transform' : 'xform'
}

virtualClass = util.defaultdict(list)

def toPyNode(res):
    "returns a PyNode object"
    if res is not None:
        import pymel.core.general
        return pymel.core.general.PyNode(res)

def toPyUI(res):
    "returns a PyUI object"
    if res is not None:
        import pymel.core.uitypes
        return pymel.core.uitypes.PyUI(res)

def toPyNodeList(res):
    "returns a list of PyNode objects"
    if res is None:
        return []
    import pymel.core.general
    return [ pymel.core.general.PyNode(x) for x in res ]

def toPyUIList(res):
    "returns a list of PyUI objects"
    if res is None:
        return []
    import pymel.core.uitypes
    return [ pymel.core.uitypes.PyUI(x) for x in res ]

class Condition(object):
    """
    Used to chain together objects for conditional testing.
    """
    class NO_DATA(Exception): pass
    
    def __init__(self, value=None):
        self.value = value
        
    def eval(self, data=NO_DATA):
        return bool(self.value)
    
    def __or__(self, other):
        return Or(self, other)
    def __ror(self, other):
        return Or(other, self)
    
    def __and__(self, other):
        return And(self, other)
    def __rand__(self, other):
        return And(other, self)
    
    def __invert__(self):
        return Inverse(self)
    
    def __nonzero__(self):
        return self.eval()

Always = Condition(True)

Never = Condition(False)
    
class Inverse(Condition):
    def __init__(self, toInvert):
        self.toInvert = toInvert
        
    def eval(self, data=Condition.NO_DATA):
        return not self.toInvert.eval(data)

    def __str__(self):
        return "not %s" % self.toInvert

class AndOrAbstract(Condition):
    def __init__(self, *args):
        self.args = []
        for arg in args:
            if isinstance(arg, self.__class__):
                self.args.extend(arg.args)
            else:
                self.args.append(arg)

    def eval(self, data=Condition.NO_DATA):
        for arg in self.args:
            if isinstance(arg, Condition):
                val = arg.eval(data)
            else:
                val = bool(arg)
            if val == self._breakEarly:
                return self._breakEarly
        return not self._breakEarly

    def __str__(self):
        return "(%s)" % self._strJoiner.join([str(x) for x in self.args])
        
class And(AndOrAbstract):
    _breakEarly = False
    _strJoiner = ' and '

class Or(AndOrAbstract):
    _breakEarly = True
    _strJoiner = ' or '
    
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

simpleCommandWraps = {
    'createRenderLayer' : [ (toPyNode, Always) ],
    'createDisplayLayer': [ (toPyNode, Always) ],
    'distanceDimension' : [ (toPyNode, Always) ], 
    'listAttr'          : [ (util.listForNone, Always) ], 
    'instance'          : [ (toPyNodeList, Always) ], 
    
    'getPanel'          : [ ( toPyUI,
                              Flag('containing', 'c', None) |
                              Flag('underPointer', 'up') |
                              Flag('withFocus', 'wf')),
                            ( toPyUIList, ~Flag('typeOf', 'to', None) )
                          ],
                            
    'textScrollList'    : [ ( util.listForNone, 
                              Flag('query', 'q') &
                               (Flag('selectIndexedItem', 'sii') | 
                                Flag('allItems', 'ai') |
                                Flag('selectItem', 'si')) )
                          ],

    'optionMenu'        : [ ( util.listForNone,
                              Flag('query', 'q') &
                               (Flag('itemListLong', 'ill') | 
                                Flag('itemListShort', 'ils')) )
                          ], 

    'optionMenuGrp'     : [ ( util.listForNone,
                              Flag('query', 'q') &
                               (Flag('itemListLong', 'ill') | 
                                Flag('itemListShort', 'ils')) )
                          ], 

    'modelEditor'       : [ ( toPyNode,
                              Flag('query', 'q') & Flag('camera', 'cam') )
                          ],
    
    'ikHandle'          : [ ( toPyNode,
                              Flag('query', 'q') & Flag('endEffector', 'ee') ),
                            ( toPyNodeList,
                              Flag('query', 'q') & Flag('jointList', 'jl') ),
                          ]
}   
#---------------------------------------------------------------
   
if includeDocExamples:
    examples = loadCache('mayaCmdsExamples', 'maya Command examples',useVersion=False )
    for cmd, example in examples.iteritems():
        cmdlist[cmd]['example'] = example

#cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds = cmdcache.buildCachedData()

# FIXME
#: stores a dcitionary of pymel classnames and their methods.  i'm not sure if the 'api' portion is being used any longer
apiToMelMap = { 
               'mel' : util.defaultdict(list),
               'api' : util.defaultdict(list)
               }

def _getApiOverrideNameAndData(classname, pymelName):
    if apicache.apiToMelData.has_key( (classname,pymelName) ):

        data = apicache.apiToMelData[(classname,pymelName)]
        try:
            nameType = data['useName']
        except KeyError:
            _logger.warn( "no 'useName' key set for %s.%s" % (classname, pymelName) )
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
        data = { 'enabled' : pymelName not in EXCLUDE_METHODS }
        apicache.apiToMelData[(classname,pymelName)] = data

    
    #overloadIndex = data.get( 'overloadIndex', None )
    return pymelName, data


def getUncachedCmds():
    return list( set( map( itemgetter(0), inspect.getmembers( cmds, callable ) ) ).difference( cmdlist.keys() ) )
        


def getInheritance( mayaType ):
    """Get parents as a list, starting from the node after dependNode, and ending with the mayaType itself.
    To get the inheritance we use nodeType, which requires a real node.  To do get these without poluting the scene
    we use a dag/dg modifier, call the doIt method, get the lineage, then call undoIt."""

    dagMod = api.MDagModifier()
    dgMod = api.MDGModifier()
    
    # Regardless of whether we're making a DG or DAG node, make a parent first - 
    # for some reason, this ensures good cleanup (don't ask me why...??)
    parent = dagMod.createNode ( 'transform', api.MObject())

    try :
        # Try making it with dgMod FIRST - this way, we can avoid making an
        # unneccessary transform if it is a DG node
        obj = dgMod.createNode ( mayaType )
        dgMod.doIt()
        
        #_logger.debug( "Made ghost DG node of type '%s'" % mayaType )
        name = api.MFnDependencyNode(obj).name()
        mod = dgMod
        
    except RuntimeError:
        try:
            # DagNode
            obj = dagMod.createNode ( mayaType, parent )
            dagMod.doIt()
            
            #_logger.debug( "Made ghost DAG node of type '%s'" % mayaType )
            name = api.MFnDagNode(obj).name()
            mod = dagMod
        except RuntimeError:
            return None
        
    if not obj.isNull() and not obj.hasFn( api.MFn.kManipulator3D ) and not obj.hasFn( api.MFn.kManipulator2D ):
        lineage = cmds.nodeType( name, inherited=1)
    else:
        lineage = []
        
    mod.undoIt()
    return lineage
            


    
#-----------------------
# Function Factory
#-----------------------
docCacheLoaded = False
def loadCmdDocCache():
    global docCacheLoaded
    if docCacheLoaded:
        return
    data = loadCache( 'mayaCmdsDocs', 'the Maya command documentation' )
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
    util.addLazyDocString( func, addCmdDocsCallback, cmdName, docstring )
    return func

def addCmdDocsCallback(cmdName, docstring=''):
    loadCmdDocCache()
    
    cmdInfo = cmdlist[cmdName]
    
    #docstring = cmdInfo['description'] + '\n\n' + '\n'.join(textwrap.wrap(docstring.strip(), DOC_WIDTH))
    
    docstring = '\n'.join(textwrap.wrap(cmdInfo['description'], DOC_WIDTH)) + '\n\n' + docstring.strip()

#    if func.__doc__: 
#        docstring += func.__doc__ + '\n\n'
    
    docstring = docstring.rstrip() + '\n\n'
     
    flagDocs = cmdInfo['flags']
    
    if flagDocs and sorted(flagDocs.keys()) != ['edit', 'query']:

        widths = [3, 100, 32, 32]
        altwidths = [ widths[0] + widths[1] ] + widths[2:]
        rowsep = '    +' + '+'.join( [ '-'*(w-1) for w in widths ] ) + '+\n'
        headersep = '    +' + '+'.join( [ '='*(w-1) for w in widths ] ) + '+\n'

        def makerow( items, widths ):
            return '    |' + '|'.join( ' ' + i.ljust(w-2) for i, w in zip( items, widths ) ) + '|\n'

        
        docstring += 'Flags:\n'
    
        if includeDocExamples:
            docstring += rowsep
            docstring += makerow( ['Long name (short name)', 'Argument Types', 'Properties'], altwidths )
            docstring += headersep
              
        for flag in sorted(flagDocs.keys()):
            if flag in ['edit', 'query']: continue
            docs = flagDocs[flag]

            # type
            typ = docs['args']
            if isinstance(typ, list):
                try:
                    typ = [ x.__name__ for x in typ ]
                except:
                    typ = [ str(x) for x in typ ]
                typ = ', '.join(typ)
            else:
                try:
                    typ = typ.__name__
                except: pass
            
            # docstring
            descr = docs.get('docstring', '')
            
            # modes
            tmpmodes = docs.get('modes', [])
            modes = []
            if 'create' in tmpmodes: modes.append('create')
            if 'query' in tmpmodes: modes.append('query')
            if 'edit' in tmpmodes: modes.append('edit')
                        
            if includeDocExamples:
                for data in util.izip_longest( ['**%s (%s)**' % (flag, docs['shortname'])],
                                            textwrap.wrap( '*%s*' % typ, widths[2]-2 ),
                                            [ '.. image:: /images/%s.gif' % m for m in modes],
                                            fillvalue='' ):
                    docstring += makerow( data, altwidths )
                
                #docstring += makerow( ['**%s (%s)**' % (flag, docs['shortname']), '*%s*' % typ, ''], altwidths )
                #for m in modes:
                #    docstring += makerow( ['', '', '.. image:: /images/%s.gif' % m], altwidths )
                                
                docstring += rowsep
                
                descr_widths = [widths[0], sum(widths[1:])]
                if descr:
                    for line in textwrap.wrap( descr.strip('|'), sum(widths[1:])-2 ):
                        docstring += makerow( ['', line], descr_widths )
                    # add some filler at the bottom
                    docstring += makerow( ['', '  ..'], descr_widths )
                else:
                    docstring += makerow( ['', ''], descr_widths )
                
                # empty row for spacing
                #docstring += rowsep
                #docstring += makerow( ['']*len(widths), widths )
                # closing separator
                docstring += rowsep
                
            else:
                descr = '\n'.join([ '      '+x for x in textwrap.wrap(descr, DOC_WIDTH)])
                # add trailing newline
                descr = descr + '\n' if descr else ''
                docstring += '  - %s %s [%s]\n%s\n' % ( 
                                            (flag + ' : ' + docs['shortname']).ljust(30), 
                                            ('('+typ+')').ljust(15),
                                            ','.join( modes ),
                                             descr )
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
            #args

    
    docstring += '\nDerived from mel command `maya.cmds.%s`\n' % (cmdName) 
    
    if includeDocExamples and cmdInfo.get('example',None):
        #docstring = ".. |create| image:: /images/create.gif\n.. |edit| image:: /images/edit.gif\n.. |query| image:: /images/query.gif\n\n" + docstring
        docstring += '\n\nExample::\n\n' + cmdInfo['example']
    
    return docstring
    
    #func.__doc__ = docstring
    #return func        

def _addFlagCmdDocs(func, cmdName, flag, docstring=''):
    util.addLazyDocString( func, addFlagCmdDocsCallback, cmdName, flag, docstring )
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
                                            '\n'.join( ['      '+ x for x in textwrap.wrap( flagdoc, DOC_WIDTH)] ) )
    
        docstring += '\nDerived from mel command `maya.cmds.%s`\n' % (cmdName)
    return docstring

#    func.__doc__ = docstring
#    return func


def _getTimeRangeFlags(cmdName):
    """used parsed data and naming convention to determine which flags are callbacks"""
    
    commandFlags = []
    try:
        flagDocs = cmdlist[cmdName]['flags']
    except KeyError:
        pass
    else:
        for flag, data in flagDocs.items():
            if data['args'] == 'timeRange':
                commandFlags += [flag, data['shortname']]
    return commandFlags


def fixCallbacks(inFunc, commandFlags, funcName=None ):
    """
    When a user provides a custom callback functions for a UI elements, such as a checkBox, when the callback is trigger it is passed
    a string instead of a real python values. For example, a checkBox changeCommand returns the string 'true' instead of
    the python boolean True. This function wraps UI commands to correct the problem and also adds an extra flag
    to all commands with callbacks called 'passSelf'.  When set to True, an instance of the calling UI class will be passed
    as the first argument.
    
    if inFunc has been renamed, pass a funcName to lookup command info in apicache.cmdlist
    """
    
    if funcName is None:
        funcName = inFunc.__name__
        
    if not commandFlags:
        #commandFlags = []
        return inFunc
    
    # wrap ui callback commands to ensure that the correct types are returned.
    # we don't have a list of which command-callback pairs return what type, but for many we can guess based on their name.
    if funcName.startswith('float'):
        argCorrector = float
    elif funcName.startswith('int'):
        argCorrector = int
    elif funcName.startswith('checkBox') or funcName.startswith('radioButton'):
        argCorrector = lambda x: x == 'true'
    else:
        argCorrector = None
    

    # need to define a seperate var here to hold
    # the old value of newFunc, b/c 'return newFunc'
    # would be recursive
    beforeUiFunc = inFunc

    def _makeCallback( origCallback, args, doPassSelf ):
        """this function is used to make the callback, so that we can ensure the origCallback gets
        "pinned" down"""
        #print "fixing callback", key
        def callback(*cb_args):
            if argCorrector:
                newargs = [argCorrector(arg) for arg in cb_args]
            else:
                newargs = list(cb_args)
            
            if doPassSelf:
                newargs = [ args[0] ] + newargs
            newargs = tuple(newargs)
            res = origCallback( *newargs )
            if isinstance(res, util.ProxyUnicode):
                res = unicode(res)
            return res
        return callback

    def newUiFunc( *args, **kwargs):
            
        if len(args):
            doPassSelf = kwargs.pop('passSelf', False)
        else:
            doPassSelf = False
                  
        for key in commandFlags:
            try:
                cb = kwargs[ key ]
                if callable(cb):
                    kwargs[ key ] = _makeCallback( cb, args, doPassSelf )
            except KeyError: pass
            
        return beforeUiFunc(*args, **kwargs)   
    
    if funcName:
        newUiFunc.__name__ = funcName
    else:
        newUiFunc.__name__ = inFunc.__name__
    newUiFunc.__module__ = inFunc.__module__
    newUiFunc.__doc__ = inFunc.__doc__
     
    return  newUiFunc

def functionFactory( funcNameOrObject, returnFunc=None, module=None, rename=None, uiWidget=False ):
    """
    create a new function, apply the given returnFunc to the results (if any), 
    and add to the module given by 'moduleName'.  Use pre-parsed command documentation
    to add to __doc__ strings for the command.
    """

    #if module is None:
    #   module = _thisModule
    
    inFunc = None
    if isinstance( funcNameOrObject, basestring ):
        funcName = funcNameOrObject

        # make sure that we import from pmcmds, not cmds
        if module and module!=cmds:
            try:       
                inFunc = getattr(module, funcName)
                customFunc = True
            except AttributeError:
                #if funcName == 'lsThroughFilter': #_logger.debug("function %s not found in module %s" % ( funcName, module.__name__))
                pass
        
        if not inFunc:
            try:
                inFunc = getattr(pmcmds,funcName)
                customFunc = False
                #if funcName == 'lsThroughFilter': #_logger.debug("function %s found in module %s: %s" % ( funcName, cmds.__name__, inFunc.__name__))
            except AttributeError:
                #_logger.debug('Cannot find function %s' % funcNameOrObject)
                return
    else:
        funcName = funcNameOrObject.__name__
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
                _logger.warn("Function found in module %s has different name than desired: %s != %s. simple fix? %s" % ( inFunc.__module__, funcName, newFuncName, funcType == types.FunctionType and returnFunc is None))
        except AttributeError:
            _logger.warn("%s had no '__name__' attribute" % inFunc)

    timeRangeFlags = _getTimeRangeFlags(funcName)

    
    # some refactoring done here - to avoid code duplication (and make things clearer),
    # we now ALWAYS do things in the following order:
        # 1. Perform operations which modify the execution of the function (ie, adding return funcs)
        # 2. Modify the function descriptors - ie, __doc__, __name__, etc
        
        
    # 1. Perform operations which modify the execution of the function (ie, adding return funcs)

    newFunc = inFunc
    
    if returnFunc or timeRangeFlags:
        # need to define a seperate var here to hold
        # the old value of newFunc, b/c 'return newFunc'
        # would be recursive
        beforeReturnFunc = newFunc
        def newFuncWithReturnFunc( *args, **kwargs):
            for flag in timeRangeFlags:
                try:
                    # allow for open-ended time ranges: 
                    # (1,None), (1,), slice(1,None), "1:"
                    # (None,100), slice(100), ":100"
                    # (None,None), ":"
                    val = kwargs[flag]
                except KeyError: 
                    pass
                else:
                    if isinstance(val, slice):
                        val = [val.start, val.stop]
                    elif isinstance(val, basestring) and val.count(':') == 1:
                        val = val.split(':')
                        # keep this python 2.4 compatible
                        
                        for i, v in enumerate(val):
                            if not v.strip():
                                val[i] = None
                    elif isinstance(val, int):
                        val = (val,val)
                    
                    if isinstance(val, (tuple, list) ):
                        val = list(val)
                        if len(val)==2 :
                            if val[0] is None:
                                val[0] = cmds.findKeyframe(which='first')
                            if val[1] is None:
                                val[1] = cmds.findKeyframe(which='last')
                        elif len(val)==1:
                            val.append( cmds.findKeyframe(which='last') )
                        kwargs[flag] = tuple(val)

            res = beforeReturnFunc(*args, **kwargs)
            if not kwargs.get('query', kwargs.get('q',False)): # and 'edit' not in kwargs and 'e' not in kwargs:
                if isinstance(res, list):
                    # some node commands unnecessarily return a list with a single object
                    if cmdInfo.get('resultNeedsUnpacking',False):
                        res = returnFunc(res[0])
                    else:
                        try:
                            res = map( returnFunc, res )
                        except: pass
            
                elif res:
                    try:
                        res = returnFunc( res )
                    except Exception, e:
                        pass
            return res
        newFunc = newFuncWithReturnFunc
    
    if funcName in simpleCommandWraps:
        # simple wraps: we only do these for functions which have not been manually customized
        # data structure looks like:
        #'optionMenu'        : [ ([('query', 'q'), ('itemListLong', 'ill')],       [util.listForNone]),
        #                        ([('query', 'q'), ('itemListShort', 'ils')],      [util.listForNone])],
        
        #'getPanel'          : [ ( toPyUI,
        #                          ( [('containing', 'c')],
        #                            [('underPointer', 'up')]
        #                            [('withFocus', 'wf')] ) ),
        #                        ( util.listForNone,
        #                          ( [('typeOf', 'to')] ) ),
        #                        ( toPyUIList, None )
        #                      ],
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
            elif len(wraps)>1:
                flags = ' for all other flags'
            else:
                flags = ''
            if func.__doc__:
                funcString = func.__doc__.strip()
            else:
                funcString = func.__name__ + '(result)'
            doc += '  - ' + funcString + flags + '\n'
            
        newFunc.__doc__  = doc
        
    #----------------------------        
    # UI commands with callbacks
    #----------------------------
    
    callbackFlags = cmdInfo.get('callbackFlags', None)
    if callbackFlags:
        newFunc = fixCallbacks( newFunc, callbackFlags, funcName )

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

def makeCreateFlagMethod( inFunc, flag, newMethodName=None, docstring='', cmdName=None, returnFunc=None ):
    #name = 'set' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = inFunc.__name__

    if returnFunc:
        def wrappedMelFunc(*args, **kwargs): 
            if len(args)<=1:
                kwargs[flag]=True
            elif len(args)==2:
                kwargs[flag]=args[1]
                args = (args[0],)  
            else:
                kwargs[flag]=args[1:]
                args = (args[0],)  
            return returnFunc(inFunc( *args, **kwargs ))
    else:
        def wrappedMelFunc(*args, **kwargs): 
            if len(args)<=1:
                kwargs[flag]=True
            elif len(args)==2:
                kwargs[flag]=args[1]
                args = (args[0],)
            else:
                kwargs[flag]=args[1:]
                args = (args[0],)  
            return inFunc( *args, **kwargs )
        
    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag
    
    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring )

def createflag( cmdName, flag ):
    """create flag decorator"""
    def create_decorator(method):
        wrappedMelFunc = makeCreateFlagMethod( method, flag, method.__name__, cmdName=cmdName )
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

def makeQueryFlagMethod( inFunc, flag, newMethodName=None, docstring='', cmdName=None, returnFunc=None ):
    #name = 'get' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = inFunc.__name__

    if returnFunc:
        def wrappedMelFunc(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True
            return returnFunc( inFunc( self, **kwargs ) )
    else:
        def wrappedMelFunc(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True 
            return inFunc( self, **kwargs )
    
    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag
        
    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring )

def queryflag( cmdName, flag ):
    """query flag decorator"""
    def query_decorator(method):
        wrappedMelFunc = makeQueryFlagMethod( method, flag, method.__name__, cmdName=cmdName )
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return query_decorator

   
def makeEditFlagMethod( inFunc, flag, newMethodName=None, docstring='', cmdName=None):
    #name = 'set' + flag[0].upper() + flag[1:]    
    if cmdName is None:
        cmdName = inFunc.__name__

    def wrappedMelFunc(self, val=True, **kwargs): 
        kwargs['edit']=True
        kwargs[flag]=val 
        try:
            return inFunc( self, **kwargs )
        except TypeError:
            kwargs.pop('edit')
            return inFunc( self, **kwargs )
        
    if newMethodName:
        wrappedMelFunc.__name__ = newMethodName
    else:
        wrappedMelFunc.__name__ = flag
             
    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring )
            
            
def editflag( cmdName, flag ):
    """query flag decorator"""
    def edit_decorator(method):
        wrappedMelFunc = makeEditFlagMethod(  method, flag, method.__name__, cmdName=cmdName )
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return edit_decorator


def addMelDocs( cmdName, flag=None ):
    """decorator for adding docs"""
    
    if flag:
        # A method generated from a flag
        def doc_decorator(method):
            wrappedMelFunc = _addFlagCmdDocs(method, cmdName, flag )
            wrappedMelFunc.__module__ = method.__module__
            return wrappedMelFunc
    else:
        # A command  
        def doc_decorator(func):
            try:
                wrappedMelFunc = _addCmdDocs(func, cmdName )
                wrappedMelFunc.__module__ = func.__module__
            except KeyError:
                _logger.info(("No documentation available %s command" % ( cmdName ) ))
                wrappedMelFunc = func
            return wrappedMelFunc
    
    return doc_decorator

def listForNoneQuery(res, kwargs, flags):
    "convert a None to an empty list on the given query flags"
    if res is None and kwargs.get('query', kwargs.get('q', False ) ) and \
        bool( [ True for long, short in flags if kwargs.get(long, kwargs.get(short, False ))] ):
        return []
    return res


def createFunctions( moduleName, returnFunc=None ):
    module = sys.modules[moduleName]
    moduleShortName = moduleName.split('.')[-1]
    for funcName in moduleCmds[ moduleShortName ] :
        if funcName in nodeCommandList:
            func = functionFactory( funcName, returnFunc=returnFunc, module=module )
        else:
            func = functionFactory( funcName, returnFunc=None, module=module )
        if func:
            func.__module__ = moduleName
            setattr( module, funcName, func )


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
    def _makeApiArraySetter( type, inCast ):
        iterable = hasattr(inCast, '__iter__')
        def setArray( array ):
            arrayPtr = type()
            if iterable:
                [ arrayPtr.append( inCast(*x) ) for x in array ]
            else:
                [ arrayPtr.append( inCast(x) ) for x in array ]
            return arrayPtr
        setArray.__name__ = 'set_' + type.__name__
        return setArray
        
    @staticmethod
    def _makeArraySetter( apiTypeName, length, initFunc ):
        def setArray( array ):
            if len(array) != length:
                raise ValueError, 'Input list must contain exactly %s %ss' % ( length, apiTypeName )
            safeArrayPtr = initFunc()
            for i, val in enumerate( array ):
                safeArrayPtr[i] = val
            #_logger.debug("result %s" % safeArrayPtr)
            return safeArrayPtr
        setArray.__name__ = 'set_' + apiTypeName + str(length) + 'Array'
        return setArray

    @staticmethod
    def _makeArrayGetter( apiTypeName, length ):
        def getArray( safeArrayPtr ):
            return [ x for x in safeArrayPtr]
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
                buf = re.split( '(?:MIt)|(?:MFn)|(?:M)', apiType)
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
        capType = util.capitalize( apiTypeName ) 

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
            pass # filled out below
        else:
            cls.inCast[apiTypeName] = pymelType
        
        if apiTypeName in ['float', 'double', 'bool', 'int', 'short', 'long', 'uint']:
            initFunc = cls._makeRefFunc( capType )
            getFunc = api.SafeApiPtr.get
            cls.refInit[apiTypeName] = initFunc
            cls.refCast[apiTypeName] = getFunc
            for i in [2,3,4]:
                # Register arrays for this up to size for - ie,
                #   int myVar[2];
                iapiArrayTypename = apiTypeName + '__array' + str(i)
                arrayInitFunc = cls._makeRefFunc( capType, size=i)
                cls.refInit[iapiArrayTypename] = arrayInitFunc
                cls.inCast[iapiArrayTypename]  = cls._makeArraySetter( apiTypeName, i, arrayInitFunc )
                cls.refCast[iapiArrayTypename] = cls._makeArrayGetter( apiTypeName, i )
                cls.types[iapiArrayTypename] = tuple([pymelType.__name__]*i)
                # Check if there is an explicit maya type for n of these - ie,
                #   int2 myVar;
                apiTypeNameN = apiTypeName + str(i)
                castNFuncName = 'as' + capType + str(i) + 'Ptr'
                if hasattr(api.MScriptUtil, castNFuncName):
                    nInitFunc = cls._makeRefFunc(apiTypeName, size=i, asTypeNPtr=True)
                    cls.refInit[apiTypeNameN] = nInitFunc
                    cls.inCast[apiTypeNameN]  = cls._makeArraySetter( apiTypeName, i, nInitFunc )
                    cls.refCast[apiTypeNameN] = cls._makeArrayGetter( apiTypeName, i )
                    cls.types[apiTypeNameN] = tuple([pymelType.__name__]*i)
        else:
            try:      
                apiType = getattr( api, apiTypeName )
            except AttributeError:
                if apiArrayItemType:
                    cls.refInit[apiTypeName] = list
                    cls.inCast[apiTypeName] = lambda x: [ apiArrayItemType(y) for y in x ] 
                    cls.refCast[apiTypeName] = None
                    cls.outCast[apiTypeName] = None

            else:
                #-- Api Array types
                if apiArrayItemType:
                    
                    cls.refInit[apiTypeName] = apiType
                    cls.inCast[apiTypeName] = cls._makeApiArraySetter( apiType, apiArrayItemType )
                    # this is double wrapped because of the crashes occuring with MDagPathArray. not sure if it's applicable to all arrays
                    if apiType == api.MDagPathArray:
                        cls.refCast[apiTypeName] = lambda x:       [ pymelType( apiArrayItemType(x[i]) ) for i in range( x.length() ) ]
                        cls.outCast[apiTypeName] = lambda self, x: [ pymelType( apiArrayItemType(x[i]) ) for i in range( x.length() ) ]
                    else:
                        cls.refCast[apiTypeName] = lambda x:       [ pymelType( x[i] ) for i in range( x.length() ) ]
                        cls.outCast[apiTypeName] = lambda self, x: [ pymelType( x[i] ) for i in range( x.length() ) ]
                        
                #-- Api types
                else:
                    cls.refInit[apiTypeName] = apiType
                    cls.refCast[apiTypeName] = pymelType
                    try:
                        # automatically handle array types that correspond to this api type (e.g.  MColor and MColorArray )
                        arrayTypename = apiTypeName + 'Array'
                        apiArrayType = getattr( api, arrayTypename )
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
ApiTypeRegister.register('MString', unicode )
ApiTypeRegister.register('MStringArray', list, apiArrayItemType=unicode )
ApiTypeRegister.register('MIntArray', int, apiArrayItemType=int)
ApiTypeRegister.register('MFloatArray', float, apiArrayItemType=float)
ApiTypeRegister.register('MDoubleArray', float, apiArrayItemType=float)

class ApiArgUtil(object): 

    def __init__(self, apiClassName, methodName, methodIndex=0 ):
        """If methodInfo is None, then the methodIndex will be used to lookup the methodInfo from apiClassInfo"""
        self.apiClassName = apiClassName
        self.methodName = methodName
        
        
        if methodIndex is None:
            try:
                methodInfoList = apicache.apiClassInfo[apiClassName]['methods'][methodName]
            except KeyError:
                raise TypeError, "method %s of %s cannot be found" % (methodName, apiClassName)  
            else:
                for i, methodInfo in enumerate( methodInfoList ):
                  
                    #argInfo = methodInfo['argInfo']
            
                    #argList = methodInfo['args']
                    argHelper = ApiArgUtil(apiClassName, methodName, i)
                    
                    if argHelper.canBeWrapped() :
                        methodIndex = i  
                        break
                
                # if it is still None then we didn't find anything
                if methodIndex is None:
                    raise TypeError, "method %s of %s cannot be wrapped" % (methodName, apiClassName)  
        
        self.methodInfo = apicache.apiClassInfo[apiClassName]['methods'][methodName][methodIndex]
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
                    arg_res.append( argInfo[key] ) 
            else:
                arg_res = argname
            res.append( arg_res )
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
                if hasattr( getattr(api, self.apiClassName), inverse ):
                    return ApiArgUtil( self.apiClassName, inverse, self.methodIndex )
        except:
            pass
                  
    @staticmethod
    def isValidEnum( enumTuple ):
        if apicache.apiClassInfo.has_key(enumTuple[0]) and \
            apicache.apiClassInfo[enumTuple[0]]['enums'].has_key(enumTuple[1]):
            return True
        return False
    
    def hasOutput(self):
        if self.methodInfo['outArgs'] or self.methodInfo['returnType']:
            return True
        return False
    
    def canBeWrapped(self):
        inArgs = self.methodInfo['inArgs']
        outArgs =  self.methodInfo['outArgs']
        defaults = self.methodInfo['defaults']
        #argList = methodInfo['args']
        returnType =  self.methodInfo['returnType']
        # ensure that we can properly cast all the args and return values
        try:
            if returnType is not None:
                # Enum: ensure existence
                if isinstance( returnType, tuple ):
                    assert self.isValidEnum(returnType), '%s.%s(): invalid return enum: %s' % (self.apiClassName, self.methodName, returnType)
                    
                # Other: ensure we can cast result
                else:
                    assert  returnType in ApiTypeRegister.outCast or \
                            returnType == self.apiClassName, \
                    '%s.%s(): invalid return type: %s' % (self.apiClassName, self.methodName, returnType)
            
            for argname, argtype, direction in self.methodInfo['args'] :
                # Enum
                if isinstance( argtype, tuple ):
                    assert self.isValidEnum(argtype), '%s.%s(): %s: invalid enum: %s' % (self.apiClassName, self.methodName, argname, argtype) 
                
                # Input
                elif direction == 'in':
                    assert  argtype in ApiTypeRegister.inCast or \
                            defaults.has_key(argname) or \
                            argtype == self.apiClassName, \
                    '%s.%s(): %s: invalid input type %s' % (self.apiClassName, self.methodName, argname, argtype)
                    
                    #if argname in ['instance', 'instanceNumber']: print '%s.%s(): %s: %r' % (self.apiClassName, self.methodName, argname, argtype)
                # Output
                elif direction == 'out':
                    assert argtype in ApiTypeRegister.refInit and argtype in ApiTypeRegister.refCast, '%s.%s(): %s: invalid output type %s' % (self.apiClassName, self.methodName, argname, argtype)
                    #try:
                    #    assert argtype.type() in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
                    #except AttributeError:
                    #    assert argtype in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
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
#            return apicache.apiClassInfo[argtype[0]]['enums'][argtype[1]].index(input)
    
    def getInputTypes(self):
        inArgs = self.methodInfo['inArgs']
        types = self.methodInfo['types']
        return [str(types[x]) for x in inArgs ]

    def getOutputTypes(self):
        ret = self.methodInfo['returnType']
        if ret is None:
            ret = []
        else:
            ret = [str(ret)]
            
        outArgs =  self.methodInfo['outArgs']
        types = self.methodInfo['types']
        return ret + [str(types[x]) for x in outArgs ]
    
    def getReturnType(self):
        return self.methodInfo['returnType']
    
    def getPymelName(self ):
        pymelName = self.methodInfo.get('pymelName',self.methodName)
        try:
            pymelClassName = apiClassNamesToPyNodeNames[self.apiClassName]
            pymelName, data = _getApiOverrideNameAndData( pymelClassName, pymelName )
        except KeyError:
            pass
        return pymelName
    
    def getMethodDocs(self):
        return self.methodInfo['doc']
    
    def getPrototype(self, className=True, methodName=True, outputs=False, defaults=False):
        inArgs = self.methodInfo['inArgs']
        outArgs =  self.methodInfo['outArgs']
        returnType =  self.methodInfo['returnType']
        types = self.methodInfo['types']
        args = []
        
        for x in inArgs:
            arg = str(types[x]) + ' ' + x
            if defaults:
                try:
                    #_logger.debug(self.methodInfo['defaults'][x])
                    arg += '=' + str(self.methodInfo['defaults'][x])
                except KeyError: pass
            args.append( arg )
        
        proto = "(%s)" % (', '.join( args ) )
        if methodName:
            proto = self.methodName + proto
            if className:
                proto = self.apiClassName + '.' + proto
 
        
        if outputs:
            results = []
            if returnType:
                results.append(returnType)
            for x in outArgs:
                results.append( types[x] )

            if len(results)==1:
                proto += ' --> ' + str(results[0])
            elif len(results):
                proto += ' --> (%s)' % ', '.join( [str(x) for x in results] )
        return proto
    
    def castInput(self, argName, input, cls):
        # enums
        argtype = self.methodInfo['types'][argName]
        if isinstance( argtype, tuple ):
            # convert enum as a string or int to an int
            
            #if isinstance( input, int):
            #    return input
            
            apiClassName, enumName = argtype
            
            try:
                return apicache.apiClassInfo[apiClassName]['enums'][enumName]['values'].getIndex(input)
            except ValueError:
                try:
                    return apicache.apiClassInfo[apiClassName]['pymelEnums'][enumName].getIndex(input)
                except ValueError:
                    raise ValueError, "expected an enum of type %s.%s: got %r" % ( apiClassName, enumName, input )
                
        elif input is not None:
#            try:
            
            f = ApiTypeRegister.inCast[argtype]
            if f is None:
                return input

            input = self.toInternalUnits(argName, input)
            return f( input )   
#            except:
#                if input is None:
#                    # we should do a check to ensure that the default is None, but for now, just return
#                    return input
#                if argtype != cls.__name__:
#                    raise TypeError, "Cannot cast a %s to %s" % ( type(input).__name__, argtype ) 
#                return cls(input)

    def fromInternalUnits(self, result, instance=None):   
        # units
        unit = self.methodInfo['returnInfo'].get('unitType',None)
        returnType = self.methodInfo['returnInfo']['type']
        #_logger.debug(unit)
        #returnType in ['MPoint'] or 
        if unit == 'linear' or returnType == 'MPoint':
            unitCast = ApiTypeRegister.outCast['MDistance']
            if util.isIterable(result):
                result = [ unitCast(instance,val) for val in result ]
            else:
                result = unitCast(instance,result)
            
        # maybe this should not be hardwired here
        # the main reason it is hardwired is because we don't want to convert the w component, which we
        # would do if we iterated normally
        elif returnType == 'MPoint':
            #_logger.debug("linear")
            unitCast = ApiTypeRegister.outCast['MDistance']
            result = [ unitCast(instance,result[0]), unitCast(instance,result[1]), unitCast(instance,result[2]) ] 

        elif unit == 'angular':
            #_logger.debug("angular")
            unitCast = ApiTypeRegister.outCast['MAngle']
            if util.isIterable(result):
                result = [ unitCast(instance,val) for val in result ]
            else:
                result = unitCast(instance,result)
        return result

    def toInternalUnits(self, arg, input ):   
        # units
        info = self.methodInfo['argInfo'][arg]
        unit = info.get('unitType',None)
        if unit == 'linear':
            #_logger.debug("setting linear")
            unitCast = ApiTypeRegister.inCast['MDistance']
            if util.isIterable(input):
                input = [ unitCast(val).asInternalUnit() for val in input ]
            else:
                input = unitCast(input).asInternalUnit()
                
        elif unit == 'angular':
            #_logger.debug("setting angular")
            unitCast = ApiTypeRegister.inCast['MAngle']
            if util.isIterable(input):
                input = [ unitCast(val).asInternalUnit() for val in input ]
            else:
                input = unitCast(input).asInternalUnit()
                
        return input
            
    def castResult(self, instance, result ):
        returnType = self.methodInfo['returnType']
        if returnType:
            # enums
            if isinstance( returnType, tuple ):
                #raise NotImplementedError
                apiClassName, enumName = returnType
                try:
                    # TODO: return EnumValue type
                    
                    # convert int result into pymel string name.
                    return apicache.apiClassInfo[apiClassName]['pymelEnums'][enumName][result]
                except KeyError:
                    raise ValueError, "expected an enum of type %s.%s" % ( apiClassName, enumName )
    
            else:
                #try:
                f = ApiTypeRegister.outCast[returnType]
                if f is None:
                    return result
                
                result = self.fromInternalUnits(result, instance)
                
                return f( instance, result )  
#                except:
#                    cls = instance.__class__
#                    if returnType != cls.__name__:
#                        raise TypeError, "Cannot cast a %s to %s" % ( type(result).__name__, returnType ) 
#                    return cls(result)
    

         
    def initReference(self, argtype): 
        return ApiTypeRegister.refInit[argtype]()
     
    def castReferenceResult(self,argtype,outArg):
        f = ApiTypeRegister.refCast[ argtype ]
        #_logger.debug("castReferenceResult")
        #_logger.debug( "%s %s %s" % (f, argtype, outArg) )
        if f is None:
            return outArg
        
        result = self.fromInternalUnits(outArg)
        return f( result )

        
    
        
    def getDefaults(self):
        "get a list of defaults"
        defaults = []
        defaultInfo = self.methodInfo['defaults']
        inArgs = self.methodInfo['inArgs']
        nargs = len(inArgs)
        for i, arg in enumerate( inArgs ):
            if arg in defaultInfo:
                default = defaultInfo[arg]
            
            # FIXME : these defaults should probably not be set here since this is supposed to be 
            # a "dumb" registry of data.  perhaps move them to the controlPanel
            
            # set MSpace.Space enum to object space by default, but only if it is the last arg or 
            # the next arg has a default ( i.e. kwargs must always come after args )
#            elif str(self.methodInfo['types'][arg]) == 'MSpace.Space' and \
#                (   i==(nargs-1) or ( i<(nargs-1) and inArgs[i+1] in defaultInfo )  ):
#                    default = apicache.Enum(['MSpace', 'Space', 'kWorld'])  # should be kPostTransform?  this is what xform defaults to...

            else:
                continue    

            if isinstance(default, apicache.Enum ):
                # convert enums from apiName to pymelName. the default will be the readable string name
                apiClassName, enumName, enumValue = default
                try:
                    enumList = apicache.apiClassInfo[apiClassName]['enums'][enumName]['values']
                except KeyError:
                    _logger.warning("Could not find enumerator %s", default)
                else:
                    index = enumList.getIndex(enumValue)
                    default = apicache.apiClassInfo[apiClassName]['pymelEnums'][enumName][index]
            defaults.append( default )
            
        return defaults
    
    def isStatic(self):
        return self.methodInfo['static']
    
    def isDeprecated(self):
        return self.methodInfo.get('deprecated', False)

    
class ApiUndo:
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

    def __init__( self ):
        self.node_name = '__pymelUndoNode'
        self.cb_enabled = True
        self.undo_queue = []
        self.redo_queue = []


    def _attrChanged(self, msg, plug, otherPlug, data):
        if self.cb_enabled\
           and (msg & api.MNodeMessage.kAttributeSet != 0) \
           and (plug == self.cmdCountAttr):
            
            
#            #count = cmds.getAttr(self.node_name + '.cmdCount')
#            #print count
            if api.MGlobal.isUndoing():
                #cmds.undoInfo(state=0)
                self.cb_enabled = False
                cmdObj = self.undo_queue.pop()
                cmdObj.undoIt()
                self.redo_queue.append(cmdObj)
                #cmds.undoInfo(state=1)
                self.cb_enabled = True
                
            elif api.MGlobal.isRedoing():
                #cmds.undoInfo(state=0)
                self.cb_enabled = False
                cmdObj = self.redo_queue.pop()
                cmdObj.redoIt()
                self.undo_queue.append(cmdObj)
                #cmds.undoInfo(state=1)
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

    def _createNode( self ):
        """
        Create the undo node.

        Any type of node will do. I've chosen a 'facade' node since it
        doesn't have too much overhead and won't get deleted if the user
        optimizes the scene.

        Note that we don't want to use Maya commands here because they
        would pollute Maya's undo queue, so we use API calls instead.
        """
        
        self.flushUndo()

        dgmod = api.MDGModifier()
        self.undoNode = dgmod.createNode('facade')
        dgmod.renameNode(self.undoNode, self.node_name)
        dgmod.doIt()

        # Add an attribute to keep a count of the commands in the stack.
        attrFn = api.MFnNumericAttribute()
        self.cmdCountAttr = attrFn.create( 'cmdCount', 'cc',
                                           api.MFnNumericData.kInt
                                           )

        nodeFn = api.MFnDependencyNode(self.undoNode)
        self.node_name = nodeFn.name()
        nodeFn.addAttribute(self.cmdCountAttr)

        nodeFn.setDoNotWrite(True)
        nodeFn.setLocked(True)

        try:
            api.MMessage.removeCallback( self.cbid )
            self.cbid.disown()
        except:
            pass
        self.cbid = api.MNodeMessage.addAttributeChangedCallback( self.undoNode, self._attrChanged )

            
    def append(self, cmdObj ):
        
        self.cb_enabled = False

#        if not cmds.objExists( self.node_name ):
#            self._createNode()

        # Increment the undo node's command count. We want this to go into
        # Maya's undo queue because changes to this attr will trigger our own
        # undo/redo code.
        try:
            count = cmds.getAttr(self.node_name + '.cmdCount')
        except:
            self._createNode()
            count = cmds.getAttr(self.node_name + '.cmdCount')
        
        cmds.setAttr(self.node_name + '.cmdCount', count + 1)
      
        # Append the command to the end of the undo queue.
        self.undo_queue.append(cmdObj)

        # Clear the redo queue.
        self.redo_queue = []

        # Re-enable the callback.
        self.cb_enabled = True
    
    def execute( self, cmdObj, args ):
        self.cb_enabled = False

        if not cmds.objExists( self.node_name ):
            self._createNode()

        # Increment the undo node's command count. We want this to go into
        # Maya's undo queue because changes to this attr will trigger our own
        # undo/redo code.
        count = cmds.getAttr(self.node_name + '.cmdCount')
        cmds.setAttr(self.node_name + '.cmdCount', count + 1)

        # Execute the command object's 'doIt' method.
        res = cmdObj.doIt(args)

        # Append the command to the end of the undo queue.
        self.undo_queue.append(cmdObj)

        # Clear the redo queue.
        self.redo_queue = []

        # Re-enable the callback.
        self.cb_enabled = True
        return res

    def flushUndo( self, *args ):
        self.undo_queue = []
        self.redo_queue = []

apiUndo = ApiUndo()

class ApiUndoItem(object):
    """A simple class that reprsents an undo item to be undone or redone."""
    __slots__ = ['_setter', '_reo_args', '_undo_args' ]
    def __init__(self, setter, redoArgs, undoArgs):
        self._setter = setter
        self._reo_args = redoArgs
        self._undo_args = undoArgs
    def redoIt(self):
        self._setter(*self._reo_args)
        
    def undoIt(self):
        self._setter(*self._undo_args)
    
def wrapApiMethod( apiClass, methodName, newName=None, proxy=True, overloadIndex=None ):
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
        method = getattr( apiClass, methodName )
    except AttributeError:
        return
    
    argHelper = ApiArgUtil(apiClassName, methodName, overloadIndex)
    undoable = True # controls whether we print a warning in the docs
    
    if newName is None:
        pymelName = argHelper.getPymelName()
    else:
        pymelName = newName
          
    if argHelper.canBeWrapped() :
        
        if argHelper.isDeprecated():
            _logger.info(  "%s.%s is deprecated" % (apiClassName, methodName) )
        inArgs = argHelper.inArgs()
        outArgs = argHelper.outArgs()
        argList = argHelper.argList()
        argInfo = argHelper.argInfo()

        getterArgHelper = argHelper.getGetterInfo()
        
        if argHelper.hasOutput() :
            getterInArgs = []
            # query method ( getter )
            #if argHelper.getGetterInfo() is not None:
            if getterArgHelper is not None:
                _logger.warn( "%s.%s has an inverse %s, but it has outputs, which is not allowed for a 'setter'" % ( 
                                                                            apiClassName, methodName, getterArgHelper.methodName ) )
            
        else:
            # edit method ( setter )
            if getterArgHelper is None:
                #_logger.debug( "%s.%s has no inverse: undo will not be supported" % ( apiClassName, methodName ) )
                getterInArgs = []
                undoable = False
            else:
                getterInArgs = getterArgHelper.inArgs()
          
        
        # create the function 
        def wrappedApiFunc( self, *args ):

            do_args = []
            outTypeList = []

            undoEnabled = getterArgHelper is not None and cmds.undoInfo(q=1, state=1) and apiUndo.cb_enabled
            #outTypeIndex = []

            if len(args) != len(inArgs):
                raise TypeError, "%s() takes exactly %s arguments (%s given)" % ( methodName, len(inArgs), len(args) )
            
            # get the value we are about to set
            if undoEnabled:
                getterArgs = []  # args required to get the current state before setting it
                undo_args = []  # args required to reset back to the original (starting) state  ( aka "undo" )
                missingUndoIndices = [] # indices for undo args that are not shared with the setter and which need to be filled by the result of the getter
                inCount = 0
                for name, argtype, direction in argList :
                    if direction == 'in':
                        arg = args[inCount]
                        undo_args.append(arg)
                        if name in getterInArgs:
                            # gather up args that are required to get the current value we are about to set.
                            # these args are shared between getter and setter pairs
                            getterArgs.append(arg)
                            #undo_args.append(arg)
                        else:
                            # store the indices for 
                            missingUndoIndices.append(inCount)
                            #undo_args.append(None)
                        inCount +=1
                
                getter = getattr( self, getterArgHelper.getPymelName() )
                setter = getattr( self, pymelName )
                
                try:
                    getterResult = getter( *getterArgs )
                except RuntimeError:
                    _logger.error( "the arguments at time of error were %r" % getterArgs)
                    raise
                
                # when a command returns results normally and passes additional outputs by reference, the result is returned as a tuple
                # otherwise, always as a list
                if not isinstance( getterResult, tuple ):
                    getterResult = (getterResult,)
                
                for index, result in zip(missingUndoIndices, getterResult ):
                    undo_args[index] = result


            inCount = totalCount = 0
            for name, argtype, direction in argList :
                if direction == 'in':
                    arg = args[inCount]
                    do_args.append( argHelper.castInput( name, arg, self.__class__ ) )
                    inCount +=1
                else:
                    val = argHelper.initReference(argtype) 
                    do_args.append( val )
                    outTypeList.append( (argtype, totalCount) )
                    #outTypeIndex.append( totalCount )
                totalCount += 1


            if undoEnabled:
                undoItem = ApiUndoItem(setter, do_args, undo_args)
                apiUndo.append( undoItem )
                
            # Do final SafeApiPtr => 'true' ptr conversion
            final_do_args = []
            for arg in do_args:
                if isinstance(arg, api.SafeApiPtr):
                    final_do_args.append(arg())
                else:
                    final_do_args.append(arg)
            if argHelper.isStatic():
                result = method( *final_do_args )
            else:
                if proxy:
                    # due to the discrepancies between the API and Maya node hierarchies, our __apimfn__ might not be a 
                    # subclass of the api class being wrapped, however, the api object can still be used with this mfn explicitly.
                    mfn = self.__apimfn__()
                    if not isinstance(mfn, apiClass):
                        mfn = apiClass( self.__apiobject__() )
                    result = method( mfn, *final_do_args )
                else:
                    result = method( self, *final_do_args )
            result = argHelper.castResult( self, result ) 
        
            if len(outArgs):
                if result is not None:
                    result = [result]
                else:
                    result = []
                
                for outType, index in outTypeList:
                    outArgVal = do_args[index]
                    res = argHelper.castReferenceResult( outType, outArgVal )
                    result.append( res )
                    
                if len(result) == 1:
                    result = result[0]
                else:
                    result = tuple(result)
            return result
        
        wrappedApiFunc.__name__ = pymelName
        
        _addApiDocs( wrappedApiFunc, apiClass, methodName, overloadIndex, undoable )
   
        # format EnumValue defaults
        defaults = []
        for default in argHelper.getDefaults():
            if isinstance( default, util.EnumValue ):
                defaults.append( str(default) )
            else:
                defaults.append( default )
        
        if defaults:
            pass 
            #_logger.debug("defaults: %s" % defaults)
        
        wrappedApiFunc = util.interface_wrapper( wrappedApiFunc, ['self'] + inArgs, defaults=defaults )
        
        if argHelper.isStatic():
            wrappedApiFunc = classmethod(wrappedApiFunc)
            
        return wrappedApiFunc




def addApiDocs(apiClass, methodName, overloadIndex=None, undoable=True):
    """decorator for adding API docs"""
    
    def doc_decorator(func):
        return _addApiDocs( func, apiClass, methodName, overloadIndex, undoable)
        
    return doc_decorator

def _addApiDocs( wrappedApiFunc, apiClass, methodName, overloadIndex=None, undoable=True):

    util.addLazyDocString( wrappedApiFunc, addApiDocsCallback, apiClass, methodName, overloadIndex, undoable, wrappedApiFunc.__doc__ )
    return wrappedApiFunc

def addApiDocsCallback( apiClass, methodName, overloadIndex=None, undoable=True, origDocstring=''):
    
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
        
        Enums
        this is a little convoluted: we only want api.conversion.Enum classes here, but since we can't
        import api directly, we have to do a string name comparison
        """
        if not isinstance(type, list):
            pymelType = ApiTypeRegister.types.get(type,type)
        else:
            pymelType = type
        
        if pymelType.__class__.__name__ == 'Enum':
            try:
                pymelType = pymelType.pymelName()
            except:
                try:
                    pymelType = pymelType.pymelName( ApiTypeRegister.getPymelType( pymelType[0] ) )
                except:
                    pass
                    #_logger.debug("Could not determine pymel name for %r" % repr(pymelType))

        doc = repr(pymelType).replace("'", "`")
        if type in ApiTypeRegister.arrayItemTypes.keys():
            doc += ' list'
        return doc
    
    # Docstrings
    docstring = argHelper.getMethodDocs()
    # api is no longer in specific units, it respect UI units like MEL
    docstring = docstring.replace( 'centimeter', 'linear unit' )
    docstring = docstring.replace( 'radian', 'angular unit' )
    
    S = '    '
    if len(inArgs):
        docstring += '\n\n:Parameters:\n'
        for name in inArgs :
            info = argInfo[name]
            type = info['type']
            typeStr = formatDocstring(type)
            
            docstring += S + '%s : %s\n' % (name, typeStr )
            docstring += S*2 + '%s\n' % (info['doc'])
            if isinstance( type, apicache.Enum ):
                apiClassName, enumName = type
                enumValues = apicache.apiClassInfo[apiClassName]['pymelEnums'][enumName].keys()
                docstring += '\n' + S*2 + 'values: %s\n' % ', '.join( [ '%r' % x for x in enumValues if x not in ['invalid', 'last' ] ] )
            

            
    # Results doc strings
    results = []
    returnType = argHelper.getReturnType()
    if returnType: 
        rtype = formatDocstring(returnType)
        results.append( rtype )
    for argname in outArgs:
        rtype = argInfo[argname]['type']
        rtype = formatDocstring(rtype)
        results.append( rtype )
    
    if len(results) == 1:
        results = results[0]
        docstring += '\n\n:rtype: %s\n' % results
    elif results:
        docstring += '\n\n:rtype: (%s)\n' %  ', '.join(results)
    
    docstring += '\nDerived from api method `%s.%s.%s`\n' % (apiClass.__module__, apiClassName, methodName) 
    if not undoable:
        docstring += '\n**Undo is not currently supported for this method**\n'
    
    if origDocstring:
        docstring = origDocstring + '\n' + docstring

    return docstring
    
class MetaMayaTypeWrapper(util.metaReadOnlyAttr) :
    """ A metaclass to wrap Maya api types, with support for class constants """
    
    _originalApiSetAttrs = {}

    class ClassConstant(object):
        """Class constant"""
        def __init__(self, value):
            self.value = value
        def __repr__(self):
            return '%s.%s(%s)' % ( self.__class__.__module__,  self.__class__.__name__, repr(self.value) )
        def __str__(self):
            return self.__repr__()
        def __get__(self, instance, owner):
            # purposedly authorize notation MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None :
                # note that conversion to the correct type is done here
                return owner(self.value)
            else :
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
        if '__slots__' not in classdict :
            classdict['__slots__'] = ()
        try:
            apicls = classdict['apicls']
            proxy=False
        except KeyError:
            try:
                apicls = classdict['__apicls__']
                proxy=True
            except KeyError:
                apicls = None

        if apicls is not None:
            #_logger.debug("ADDING %s to %s" % (apicls.__name__, classname))
            apiClassNamesToPyNodeNames[apicls.__name__] = classname
            
            if not proxy and apicls not in bases:
                #_logger.debug("ADDING BASE %s" % classdict['apicls'])
                bases = bases + (classdict['apicls'],)
            try:
                classInfo = apicache.apiClassInfo[apicls.__name__]
            except KeyError:
                _logger.info("No api information for api class %s" % ( apicls.__name__ ))
            else:
                #------------------------
                # API Wrap
                #------------------------
                
                # Find out methods herited from other bases than apicls to avoid
                # unwanted overloading
                herited = {}
                for base in bases :
                    if base is not apicls :
                        # basemro = inspect.getmro(base)
                        for attr in dir(base) :
                            if attr not in herited :
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
                    
                    pymelName, data = _getApiOverrideNameAndData( classname, pymelName )
                        
                    overloadIndex = data.get( 'overloadIndex', None )
                    
                    assert isinstance( pymelName, str ), "%s.%s: %r is not a valid name" % ( classname, methodName, pymelName)
                       
                    if pymelName not in herited:
                        if overloadIndex is not None:
                            if data.get('enabled', True):                        
                                if pymelName not in classdict:
                                    #_logger.debug("%s.%s autowrapping %s.%s usng proxy %r" % (classname, pymelName, apicls.__name__, methodName, proxy))
                                    method = wrapApiMethod( apicls, methodName, newName=pymelName, proxy=proxy, overloadIndex=overloadIndex )
                                    if method:
                                        #_logger.debug("%s.%s successfully created" % (classname, pymelName ))
                                        classdict[pymelName] = method
                                    #else: #_logger.debug("%s.%s: wrapApiMethod failed to create method" % (apicls.__name__, methodName ))
                                #else: #_logger.debug("%s.%s: skipping" % (apicls.__name__, methodName ))
                            #else: #_logger.debug("%s.%s has been manually disabled, skipping" % (apicls.__name__, methodName))
                        #else: #_logger.debug("%s.%s has no wrappable methods, skipping" % (apicls.__name__, methodName))
                    #else: #_logger.debug("%s.%s already herited from %s, skipping" % (apicls.__name__, methodName, herited[pymelName]))
                
                if 'pymelEnums' in classInfo:
                    # Enumerators
                    
                    for enumName, enumList in classInfo['pymelEnums'].items():
                        #_logger.debug("adding enum %s to class %s" % ( enumName, classname ))
#                        #enum = util.namedtuple( enumName, enumList )
#                        #classdict[enumName] = enum( *range(len(enumList)) )
#                        # group into (key, doc) pairs
#                        enumKeyDocPairs = [ (k,classInfo['enums'][enumName]['valueDocs'][k] ) for k in enumList ]
#                        enum = util.Enum( *enumKeyDocPairs )
#                        classdict[enumName] = enum
                        classdict[enumName] = enumList
 
        
            if not proxy:
                #if removeAttrs:
                #    #_logger.debug( "%s: removing attributes %s" % (classname, removeAttrs) )
                def __getattribute__(self, name): 
                    #_logger.debug(name )
                    if name in removeAttrs and name not in EXCLUDE_METHODS: # tmp fix
                        #_logger.debug("raising error")
                        raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'" 
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
                _logger.warn( "Failed creating %s class constant (%s): %s" % (classname, attr, e) )
        #------------------------
        # Class Constants
        #------------------------
        if hasattr(newcls, 'apicls') :
            # type (api type) used for the storage of data
            apicls  = newcls.apicls
            if apicls is not None:                                             
                # build some constants on the class            
                constant = {}
                # constants in class definition will be converted from api class to created class
                for name, attr in newcls.__dict__.iteritems() :
                    # to add the wrapped api class constants as attributes on the wrapping class,
                    # convert them to own class         
                    if isinstance(attr, apicls) :
                        if name not in constant :
                            constant[name] = makeClassConstant(attr)                          
                # we'll need the api clas dict to automate some of the wrapping
                # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
                apiDict = dict(inspect.getmembers(apicls))            
                # defining class properties on the created class                 
                for name, attr in apiDict.iteritems() :
                    # to add the wrapped api class constants as attributes on the wrapping class,
                    # convert them to own class         
                    if isinstance(attr, apicls) :
                        if name not in constant :
                            constant[name] = makeClassConstant(attr)
                # update the constant dict with herited constants
                mro = inspect.getmro(newcls)            
                for parentCls in mro :
                    if isinstance(parentCls, MetaMayaTypeWrapper) :
                        for name, attr in parentCls.__dict__.iteritems() :
                            if isinstance(attr, MetaMayaTypeWrapper.ClassConstant) :
                                if not name in constant :
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
                for name, attr in constant.iteritems() :
                    type.__setattr__(newcls, name, attr)
                                               
            #else :   raise TypeError, "must define 'apicls' in the class definition (which Maya API class to wrap)"
        
        
        if hasattr(newcls, 'apicls') and not ApiTypeRegister.isRegistered(newcls.apicls.__name__):
            ApiTypeRegister.register( newcls.apicls.__name__, newcls )
  
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
        
        class MyClass2(MyClass1, apiClass): pass
        
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
            try:    
                cmdModule = __import__( 'pymel.core.' + cmdInfo['type'] , globals(), locals(), [''])
                func = getattr(cmdModule, melCmdName)
            except (AttributeError, TypeError):
                func = getattr(pmcmds,melCmdName)

            # add documentation
            classdict['__doc__'] = util.LazyDocString( (newcls, cls.docstring, (melCmdName,), {} ) )
            classdict['__melcmd__'] = staticmethod(func)
            classdict['__melcmd_isinfo__'] = infoCmd
            
            filterAttrs = ['name']+classdict.keys()
            filterAttrs += overrideMethods.get( bases[0].__name__ , [] )
            #filterAttrs += newcls.__dict__.keys()
            
            parentClasses = [ x.__name__ for x in inspect.getmro( newcls )[1:] ]
            for flag, flagInfo in cmdInfo['flags'].items():
                # don't create methods for query or edit, or for flags which only serve to modify other flags
                if flag in ['query', 'edit'] or 'modified' in flagInfo:
                    continue
                
                
                if flagInfo.has_key('modes'):
                    # flags which are not in maya docs will have not have a modes list unless they 
                    # have passed through testNodeCmds
                    #continue
                    modes = flagInfo['modes']
    
                    # query command
                    if 'query' in modes:
                        methodName = 'get' + util.capitalize(flag)
                        apiToMelMap['mel'][classname].append( methodName )
                        
                        if methodName not in filterAttrs and \
                                ( not hasattr(newcls, methodName) or cls.isMelMethod(methodName, parentClasses) ):
                            
                            # 'enabled' refers to whether the API version of this method will be used.
                            # if the method is enabled that means we skip it here. 
                            if not apicache.apiToMelData.has_key((classname,methodName)) \
                                or apicache.apiToMelData[(classname,methodName)].get('melEnabled',False) \
                                or not apicache.apiToMelData[(classname,methodName)].get('enabled',True):
                                returnFunc = None
                                
                                if flagInfo.get( 'resultNeedsCasting', False):
                                    returnFunc = flagInfo['args']
                                    
                                if flagInfo.get( 'resultNeedsUnpacking', False):
                                    if returnFunc:
                                        # can't do:
                                        #   returnFunc = lambda x: returnFunc(x[0])
                                        # ... as this would create a recursive function!
                                        origReturnFunc = returnFunc
                                        returnFunc = lambda x: origReturnFunc(x[0])
                                    else:
                                        returnFunc = lambda x: x[0]
                                
                                wrappedMelFunc = makeQueryFlagMethod( func, flag, methodName, 
                                     returnFunc=returnFunc )
                                
                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                classdict[methodName] = wrappedMelFunc
                            #else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled or overridden by API" % (classname, methodName)))
                        #else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))
                    # edit command: 
                    if 'edit' in modes or ( infoCmd and 'create' in modes ):
                        # if there is a corresponding query we use the 'set' prefix. 
                        if 'query' in modes:
                            methodName = 'set' + util.capitalize(flag)
                        #if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
                        else:
                            methodName = flag
                        
                        apiToMelMap['mel'][classname].append( methodName )
                           
                        if methodName not in filterAttrs and \
                                ( not hasattr(newcls, methodName) or cls.isMelMethod(methodName, parentClasses) ):
                            if not apicache.apiToMelData.has_key((classname,methodName)) \
                                or apicache.apiToMelData[(classname,methodName)].get('melEnabled',False) \
                                or not apicache.apiToMelData[(classname,methodName)].get('enabled', True):
                                #FIXME: shouldn't we be able to use the wrapped pymel command, which is already fixed?
                                fixedFunc = fixCallbacks( func, melCmdName )
                                
                                wrappedMelFunc = makeEditFlagMethod( fixedFunc, flag, methodName)
                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                classdict[methodName] = wrappedMelFunc
                            #else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)))
                        #else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))
        
        for name, attr in classdict.iteritems() :
            type.__setattr__(newcls, name, attr) 
                                
        return newcls
        
    @classmethod
    def getMelCmd(cls, classdict):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.
        
        Intended to be overridden in derived metaclasses.
        """
        return util.uncapitalize(classname), False
    
    @classmethod
    def isMelMethod(cls, methodName, parentClassList):
        """
        Deteremine if the passed method name exists on a parent class as a mel method
        """
        for classname in parentClassList:
            if methodName in apiToMelMap['mel'][classname]:
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
        
class MetaMayaNodeWrapper(_MetaMayaCommandWrapper) :
    """
    A metaclass for creating classes based on node type.  Methods will be added to the new classes 
    based on info parsed from the docs on their command counterparts.
    """
    completedClasses = {}
    def __new__(cls, classname, bases, classdict):
        # If the class explicitly gives it's mel node name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        #_logger.debug( 'MetaMayaNodeWrapper: %s' % classname )
        nodeType = classdict.setdefault('__melnode__', util.uncapitalize(classname))
        apicache.addMayaType( nodeType )
        apicls = apicache.toApiFunctionSet( nodeType )

        if apicls is not None:
            if apicls in MetaMayaNodeWrapper.completedClasses:
                pass
                #_logger.debug( "%s: %s already used by %s: not adding to __apicls__" % (classname, apicls, MetaMayaNodeWrapper.completedClasses[ apicls ]) )
            else:
                #_logger.debug( "%s: adding __apicls__ %s" % (classname, apicls) )
                MetaMayaNodeWrapper.completedClasses[ apicls ] = classname
                classdict['__apicls__'] = apicls
        
        return super(MetaMayaNodeWrapper, cls).__new__(cls, classname, bases, classdict)

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
            nodeCmd = cmdcache.nodeTypeToNodeCommand[ nodeType ]
        except KeyError:
            try:
                nodeCmd = nodeTypeToInfoCommand[ nodeType ]
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
        uiType= classdict.setdefault('__melui__', util.uncapitalize(classname))
        
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
                newEntries  = []
                for oldEntry in oldEntries:
                    for base in bases:
                        if issubclass(base, oldEntry):
                            break
                    else:
                        newEntries.append(oldEntry)
                newEntries.append(newcls)
                apiEnumsToPyComponents[apienum] = newEntries
        return newcls
#    
#def getValidApiMethods( apiClassName, api, verbose=False ):
#
#    validTypes = [ None, 'double', 'bool', 'int', 'MString', 'MObject' ]
#    
#    try:
#        methods = apicache.apiClassInfo[apiClassName]
#    except KeyError:
#        return []
#    
#    validMethods = []
#    for method, methodInfoList in methods.items():
#        for methodInfo in methodInfoList:
#            #_logger.debug(method, methodInfoList)
#            if not methodInfo['outArgs']:
#                returnType = methodInfo['returnType']
#                if returnType in validTypes:
#                    count = 0
#                    types = []
#                    for x in methodInfo['inArgs']:
#                        type = methodInfo['argInfo'][x]['type']
#                        #_logger.debug(x, type)
#                        types.append( type )
#                        if type in validTypes:
#                            count+=1
#                    if count == len( methodInfo['inArgs'] ):
#                        if verbose:
#                            _logger.info(('    %s %s(%s)' % ( returnType, method, ','.join( types ) )))
#                        validMethods.append(method)
#    return validMethods
#
#def readClassAnalysis( filename ):
#    f = open(filename)
#    info = {}
#    currentClass = None
#    currentSection = None
#    for line in f.readlines():
#        buf = line.split()
#        if buf[0] == 'CLASS':
#            currentClass = buf[1]
#            info[currentClass] = {}
#        elif buf[0].startswith('['):
#            if currentSection in ['shared_leaf', 'api', 'pymel']:
#                currentSection = buf.strip('[]')
#                info[currentClass][currentSection] = {}
#        else:
#            n = len(buf)
#            if n==2:
#                info[currentClass][currentSection][buf[0]] = buf[1]
#            elif n==1:
#                pass
#                #info[currentClass][currentSection][buf[0]] = None
#            else:
#                pass
#    f.close()
#    _logger.info(info)
#    return info
#
#def fixClassAnalysis( filename ):
#    f = open(filename)
#    info = {}
#    currentClass = None
#    currentSection = None
#    lines = f.readlines()
#    for i, line in enumerate(lines):
#        buf = line.split()
#        if buf[0] == 'CLASS':
#            currentClass = buf[1]
#            info[currentClass] = {}
#        elif buf[0].startswith('['):
#            if currentSection in ['shared_leaf', 'api', 'pymel']:
#                currentSection = buf.strip('[]')
#                info[currentClass][currentSection] = {}
#        else:
#            isAutoNamed, nativeName, pymelName, failedAutoName = re.match( '([+])?\s+([a-zA-Z0-9]+)(?:\s([a-zA-Z0-9]+))?(?:\s([a-zA-Z0-9]+))?', line ).groups()
#            if isAutoNamed and pymelName is None:
#                pymelName = nativeName
#            n = len(buf)
#            
#            if n==2:
#                info[currentClass][currentSection][buf[0]] = buf[1]
#            elif n==1:
#                pass
#                #info[currentClass][currentSection][buf[0]] = None
#            else:
#                pass
#    f.close()
#    _logger.info(info)
#    return info

#
#def analyzeApiClasses():
#    for elem in api.apiTypeHierarchy.preorder():
#        try:
#            parent = elem.parent.key
#        except:
#            parent = None
#        analyzeApiClass( elem.key, None )
#        
#def analyzeApiClass( apiTypeStr ):
#    try:
#        mayaType = apicache.apiTypesToMayaTypes[ apiTypeStr ].keys()
#        if util.isIterable(mayaType) and len(mayaType) == 1:
#            mayaType = mayaType[0]
#            pymelType = pyNodeNamesToPyNodes.get( util.capitalize(mayaType) , None )
#        else:
#            pymelType = None
#    except KeyError:
#        mayaType = None
#        pymelType = None
#        #_logger.debug("no Fn", elem.key, pymelType)
#
#    try:
#        apiClass = api.apiTypesToApiClasses[ apiTypeStr ]
#    except KeyError:
#        
#        _logger.info("no Fn %s", apiTypeStr)
#        return
#    
#    apiClassName = apiClass.__name__
#    parentApiClass = inspect.getmro( apiClass )[1]
#     
#    _logger.info("CLASS %s %s", apiClassName, mayaType)
#
#    # get all pymelName lookups for this class and its bases
#    pymelMethodNames = {}
#    for cls in inspect.getmro( apiClass ):
#        try:
#            pymelMethodNames.update( apicache.apiClassInfo[cls.__name__]['pymelMethods'] )
#        except KeyError: pass
#    reversePymelNames = dict( (v, k) for k,v in pymelMethodNames.items() ) 
#    
#    allApiMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( apiClass, callable )  ]) 
#    parentApiMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( parentApiClass, callable ) ])
#    apiMembers = allApiMembers.difference( parentApiMembers )
#    
#        
##    
##    else:
##        if apiTypeParentStr:
##            try:
##                parentApiClass = api.apiTypesToApiClasses[elem.parent.key ]
##                parentMembers = [ x[0] for x in inspect.getmembers( parentApiClass, callable ) ]
##            except KeyError:
##                parentMembers = []
##        else:
##            parentMembers = []
##        
##        if pymelType is None: pymelType = pyNodeNamesToPyNodes.get( apiClass.__name__[3:] , None )
##        
##        if pymelType:
##            parentPymelType = pyNodeTypesHierarchy[ pymelType ]
##            parentPyMembers = [ x[0] for x in inspect.getmembers( parentPymelType, callable ) ]
##            pyMembers = set([ x[0] for x in inspect.getmembers( pymelType, callable ) if x[0] not in parentPyMembers and not x[0].startswith('_') ])
##            
##            _logger.info("CLASS", apiClass.__name__, mayaType)
##            parentApiClass = inspect.getmro( apiClass )[1]
##            #_logger.debug(parentApiClass)
##            
##            pymelMethodNames = {}
##            # get all pymelName lookups for this class and its bases
##            for cls in inspect.getmro( apiClass ):
##                try:
##                    pymelMethodNames.update( apicache.apiClassInfo[cls.__name__]['pymelMethods'] )
##                except KeyError: pass
##                
##            allFnMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( apiClass, callable )  ])
##            
##            parentFnMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( parentApiClass, callable ) ])
##            fnMembers = allFnMembers.difference( parentFnMembers )
##
##            reversePymelNames = dict( (v, k) for k,v in pymelMethodNames.items() )
##            
##            sharedCurrent = fnMembers.intersection( pyMembers )
##            sharedOnAll = allFnMembers.intersection( pyMembers )
##            sharedOnOther = allFnMembers.intersection( pyMembers.difference( sharedCurrent) )
###            _logger.info("    [shared_leaf]")
###            for x in sorted( sharedCurrent ): 
###                if x in reversePymelNames: _logger.info('    ', reversePymelNames[x], x )
###                else: _logger.info('    ', x)
##                
###            _logger.info("    [shared_all]")
###            for x in sorted( sharedOnOther ): 
###                if x in reversePymelNames: _logger.info('    ', reversePymelNames[x], x )
###                else: _logger.info('    ', x)
##            
##            _logger.info("    [api]")
##            for x in sorted( fnMembers ): 
##                if x in sharedCurrent:
##                    prefix = '+   '
###                elif x in sharedOnOther:
###                    prefix = '-   '
##                else:
##                    prefix = '    '
##                if x in reversePymelNames: _logger.info(prefix, reversePymelNames[x], x )
##                else: _logger.info(prefix, x)
##            
##            _logger.info("    [pymel]")
##            for x in sorted( pyMembers.difference( allFnMembers ) ): _logger.info('    ', x)
#            
#    
def addPyNodeCallback( dynModule, mayaType, pyNodeTypeName, parentPyNodeTypeName):
    #_logger.info( "%s(%s): creating" % (pyNodeTypeName,parentPyNodeTypeName) )
    try:
        ParentPyNode = getattr( dynModule, parentPyNodeTypeName )
    except AttributeError:
        #_logger.info("error creating class %s: parent class %r not in dynModule %s" % (pyNodeTypeName, parentPyNodeTypeName, dynModule.__name__))
        return      
    try:
        PyNodeType = MetaMayaNodeWrapper(pyNodeTypeName, (ParentPyNode,), {'__melnode__':mayaType})
    except TypeError, msg:
        # for the error: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
        #_logger.debug("Could not create new PyNode: %s(%s): %s" % (pyNodeTypeName, ParentPyNode.__name__, msg ))
        import new
        PyNodeType = new.classobj(pyNodeTypeName, (ParentPyNode,), {})
        PyNodeType.__module__ = dynModule.__name__
        setattr( dynModule, pyNodeTypeName, PyNodeType )
    else:
        #_logger.debug(("Created new PyNode: %s(%s)" % (pyNodeTypeName, parentPyNodeTypeName)))
        PyNodeType.__module__ = dynModule.__name__
        setattr( dynModule, pyNodeTypeName, PyNodeType )
    pyNodeTypesHierarchy[PyNodeType] = ParentPyNode
    pyNodesToMayaTypes[PyNodeType] = mayaType
    pyNodeNamesToPyNodes[pyNodeTypeName] = PyNodeType
    return PyNodeType

def addPyNode( dynModule, mayaType, parentMayaType ):
    
    #_logger.debug("addPyNode adding %s->%s on dynModule %s" % (mayaType, parentMayaType, dynModule))
    # unicode is not liked by metaNode
    pyNodeTypeName = str( util.capitalize(mayaType) )
    parentPyNodeTypeName = str(util.capitalize(parentMayaType))
    
    try:
        dynModule[pyNodeTypeName]
    except KeyError:
        #_logger.info( "%s(%s): setting up lazy loading" % ( pyNodeTypeName, parentPyNodeTypeName ) )
        dynModule[pyNodeTypeName] = ( addPyNodeCallback, 
                                   ( dynModule, mayaType, pyNodeTypeName, parentPyNodeTypeName ) )
#    else:
#        if not pyNodeTypeName in dynModule.__dict__:
#            api.addMayaType( mayaType )
#            _logger.info( "%s(%s) exists" % ( pyNodeTypeName, parentPyNodeTypeName ) )
#            
#            
#            PyNodeType = getattr( dynModule, pyNodeTypeName )
#            try :
#                ParentPyNode = inspect.getmro(PyNodeType)[1]
#                #print "parent:", ParentPyNode, ParentPyNode.__name__
#                if ParentPyNode.__name__ != parentPyNodeTypeName :
#                    raise RuntimeError, "Unexpected PyNode %s for Maya type %s" % (ParentPyNode, )
#            except :
#                ParentPyNode = getattr( dynModule, parentPyNodeTypeName )
#            #_logger.debug("already exists:", pyNodeTypeName, )
#            pyNodeTypesHierarchy[PyNodeType] = ParentPyNode
#            pyNodesToMayaTypes[PyNodeType] = mayaType
#            pyNodeNamesToPyNodes[pyNodeTypeName] = PyNodeType

    return pyNodeTypeName

def removePyNode( dynModule, mayaType ):
    pyNodeTypeName = str( util.capitalize(mayaType) )
    PyNodeType = pyNodeNamesToPyNodes.pop( pyNodeTypeName, None )
    PyNodeParentType = pyNodeTypesHierarchy.pop( PyNodeType, None )
    pyNodesToMayaTypes.pop(PyNodeType,None)
    dynModule.__dict__.pop(pyNodeTypeName,None)
    dynModule.__class__.__dict__.pop(pyNodeTypeName,None)
    apicache.removeMayaType( mayaType )

def registerVirtualClass( cls, nameRequired=False ):
    """
    Allows a user to create their own subclasses of leaf PyMEL node classes,
    which are returned by `general.PyNode` and all other pymel commands.
    
    The process is fairly simple:
        1.  Subclass a pymel node class.  Be sure that it is a leaf class, meaning that it represents an actual Maya node type
            and not an abstract type higher up in the hierarchy. 
        2.  Register your subclass by calling this function
    
    :type  nameRequired: bool
    :param nameRequired: True if the _isVirtual callback requires the string name to operate on. The object's name is not always immediately
        avaiable and may take an extra calculation to retrieve.
        
    """
    validSpecialAttrs = set(['__module__','__readonly__','__slots__','__melnode__','__doc__'])

    # assert that we are a leaf class
    parentCls = None 
    for each_cls in inspect.getmro(cls):
        # we've reached a pymel node. we're done
        if each_cls.__module__.startswith('pymel.core'):
            parentCls = each_cls
            break
        else:
            # it's a custom class: test for disallowed attributes
            specialAttrs = [ x for x in each_cls.__dict__.keys() if x.startswith('__') and x.endswith('__') ]
            badAttrs = set(specialAttrs).difference(validSpecialAttrs)
            if badAttrs:
                raise ValueError, 'invalid attribute name(s) %s: special attributes are not allowed on virtual nodes' % ', '.join(badAttrs)
            
    assert parentCls, "passed class must be a subclass of a PyNode type"
    #assert issubclass( cls, parentCls ), "%s must be a subclass of %s" % ( cls, parentCls )

    cls.__melnode__ = parentCls.__melnode__
    
    # filter out any pre-existing classes with the same name as this one, because leaving stale callbacks in the list will slow things down
    virtualClass[parentCls] = [ x for x in virtualClass[parentCls] if x[0].__name__ != cls.__name__]
    
    #TODO:
    # inspect callbacks to ensure proper number of args and kwargs ( create callback must support **kwargs )
    # ensure that the name of our node does not conflict with a real node
    
    # put new classes at the front of list, so more recently added ones
    # will override old definitions
    virtualClass[parentCls].insert( 0, (cls, nameRequired) )

#-------------------------------------------------------------------------------

def isValidPyNode (arg):
    return pyNodeTypesHierarchy.has_key(arg)

def isValidPyNodeName (arg):
    return pyNodeNamesToPyNodes.has_key(arg)

def toPyNode( obj, default=None ):
    if isinstance( obj, int ):
        mayaType = apicache.apiEnumsToMayaTypes.get( obj, None )
        return pyNodeNamesToPyNodes.get( util.capitalize(mayaType), default )
    elif isinstance( obj, basestring ):
        try:
            return pyNodeNamesToPyNodes[ util.capitalize(obj) ]
        except KeyError:
            mayaType = apicache.apiTypesToMayaTypes.get( obj, None )
            return pyNodeNamesToPyNodes.get( util.capitalize(mayaType), default )
            
def toApiTypeStr( obj, default=None ):
    if isinstance( obj, int ):
        return apicache.apiEnumsToApiTypes.get( obj, default )
    elif isinstance( obj, basestring ):
        return apicache.mayaTypesToApiTypes.get( obj, default)
    elif isinstance( obj, util.ProxyUnicode ):
        mayaType = pyNodesToMayaTypes.get( obj, None )
        return apicache.mayaTypesToApiTypes.get( mayaType, default)
    
def toApiTypeEnum( obj, default=None ):
    if isinstance( obj, util.ProxyUnicode ):
        obj = pyNodesToMayaTypes.get( obj, None )
    return apicache.toApiTypeEnum(obj)

def toMayaType( obj, default=None ):
    if issubclass( obj, util.ProxyUnicode ):
        return pyNodesToMayaTypes.get( obj, default )
    return apicache.toMayaType(obj)

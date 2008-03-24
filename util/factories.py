import path, pymel.util, sys, os, inspect, pickle, re, types
from pymel.core.types.trees import *
#from networkx.tree import *
from HTMLParser import HTMLParser
from operator import itemgetter
try:
    import maya.cmds as cmds
    import maya.mel as mm
except ImportError: pass

#---------------------------------------------------------------
#        Mappings and Lists
#---------------------------------------------------------------

#: creation commands whose names do not match the type of node they return require this dict
#: to resolve which command the class should wrap 
nodeTypeToNodeCommand = {
    #'failed' : 'clip',
    #'failed' : 'clipSchedule',
    'airField' : 'air',
    'dragField' : 'drag',
    'emitter' : 'emitter',
    'turbulenceField' : 'turbulence',
    #'failed' : 'effector',
    'volumeAxisField' : 'volumeAxis',
    'uniformField' : 'uniform',
    'gravityField' : 'gravity',
    #'failed' : 'event',
    #'failed' : 'pointCurveConstraint',
    #'failed' : 'deformer',
    #'failed' : 'constrain',
    'locator' : 'spaceLocator',
    'vortexField' : 'vortex',
    'makeNurbTorus' : 'torus',
    'makeNurbCone' : 'cone',
    'makeNurbCylinder' : 'cylinder',
    #'failed' : 'curve',
    'makeNurbSphere' : 'sphere',
    'makeNurbCircle' : 'circle',
    'makeNurbPlane' : 'nurbsPlane',
    'makeNurbsSquare' : 'nurbsSquare',
    'makeNurbCube' : 'nurbsCube',
    'skinPercent' : 'skinCluster',
}

#: for certain nodes, the best command on which to base the node class cannot create nodes, but can only provide information.
#: these commands require special treatment during class generation because, for them the 'create' mode is the same as other node's 'edit' mode
nodeTypeToInfoCommand = {
    'mesh' : 'polyEvaluate',
    'transform' : 'xform'
}

moduleNameShortToLong = {
    'model' : 'Modeling',
    'render': 'Rendering',
    'fx'    : 'Effects',
    'anim'  : 'Animation',
    'ui'    : 'Windows',
    'io'    : 'System',
    'core' : 'General'
}

#: modifier flags can only be used in conjunction with other flags so we must exclude them when creating classes from commands.
#: because the maya docs do not specify in any parsable way which flags are modifiers, we must maintain this dictionary.
#: once this list is reliable enough and includes default values, we can use them as keyword arguments in the class methods that they modify.
secondaryFlags = {
    'xform' : ( ( 'absolute',         [] ),
                ( 'relative',         [] ),
                ( 'euler',            ['relative'] ),
                ( 'objectSpace',    ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotationTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots'] ),
                ( 'worldSpace',        ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotationTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots'] ),
                ( 'preserve',        ['scalePivot', 'rotatePivot', 'rotateOrder', 'rotateAxis', 'centerPivots'] ),
                ( 'worldSpaceDistance', ['scalePivot', 'rotatePivot', 'scaleTranslation', 'rotateTranslation', 'translation', 'pivots'] )
            ),
    'file' : ( ( 'loadAllDeferred', ['open'] ),
               ( 'loadNoReferences', ['open'] ),
               ( 'force', ['open', 'new', 'save', 'exportAll', 'exportSelected', 'exportAnim', 'exportSelectedAnim', 'exportAnimFromReference', 'exportSelectedAnimFromReference' ] ),
               ( 'returnNewNodes', ['open', 'reference', 'import' ] ),
               ( 'constructionHistory', ['exportSelected'] ),
               ( 'channels', ['exportSelected'] ),
               ( 'constraints', ['exportSelected'] )
             )
}

#: these are commands which should need to be manually added to the list parsed from the docs
moduleCommandAddtions = {
    'Windows' : ['deleteUI','uiTemplate','setUITemplate','renameUI','setParent','objectTypeUI','lsUI', 'disable', 'dimWhen']
}

#---------------------------------------------------------------
#        Doc Parser
#---------------------------------------------------------------
    
class CommandDocParser(HTMLParser):
    def __init__(self):
        self.flags = {}  # shortname, argtype, docstring, and a list of modes (i.e. edit, create, query)
        self.currFlag = ''
        # iData is used to track which type of data we are putting into flags, and corresponds with self.datatypes
        self.iData = 0
        self.pcount = 0
        self.active = False  # this is set once we reach the portion of the document that we want to parse
        self.description = ''
        self.example = ''
        HTMLParser.__init__(self)
    
    def startFlag(self, data):
        #print self, data
        #assert data == self.currFlag
        self.iData = 0
        self.flags[self.currFlag] = {'longname': self.currFlag, 'shortname': None, 'argtype': None, 'docstring': '', 'modes': [] }
    
    def addFlagData(self, data):
        # shortname, argtype
        if self.iData == 0:
            self.flags[self.currFlag]['shortname'] = data
        elif self.iData == 1:
            self.flags[self.currFlag]['argtype'] = data    
        else:
            #self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).strip() + " "
            
            
            data = data.replace( 'In query mode, this flag needs a value.', '' )
            data = data.replace( 'Flag can appear in Create mode of command', '' )
            data = data.replace( 'Flag can appear in Edit mode of command', '' )
            data = data.replace( 'Flag can appear in Query mode of command', '' )
            data = data.replace( '\r\n', ' ' ).lstrip()
            data = data.strip('{}\t')
            data = data.replace('*', '\*') # for reStructuredText
            self.flags[self.currFlag]['docstring'] += data
        self.iData += 1
        
    def endFlag(self):
        # cleanup last flag
        #data = self.flags[self.currFlag]['docstring']
        
        #print "ASSERT", data.pop(0), self.currFlag
        #self.flags[self.currFlag]['shortname'] = data.pop(0)
        self.iData = 0
        
    def handle_starttag(self, tag, attrs):
        #print "begin: %s tag: %s" % (tag, attrs)
        if not self.active:
            if tag == 'a':
                if attrs[0][1] == 'hFlags':
                    #print 'ACTIVE'
                    self.active = 'flag'
                elif attrs[0][1] == 'hExamples':
                    #print "start examples"
                    self.active = 'examples'
        elif tag == 'a' and attrs[0][0] == 'name':
            self.endFlag()
            #print "NEW FLAG", attrs
            self.currFlag = attrs[0][1][4:]
            
    
        elif tag == 'img' and len(attrs) > 4:
            #print "MODES", attrs[1][1]
            self.flags[self.currFlag]['modes'].append(attrs[1][1])
        elif tag == 'h2':
            self.active = False
                
    def handle_endtag(self, tag):
        #if tag == 'p' and self.active == 'command': self.active = False
        #print "end: %s" % tag
        if not self.active:
            if tag == 'p':
                if self.pcount == 3:
                    self.active = 'command'
                else:
                    self.pcount += 1
        elif self.active == 'examples' and tag == 'pre':
            self.active = False
    
    def handle_entityref(self,name):
        if self.active == 'examples':
            self.example += r'"'
            
    def handle_data(self, data):
        if not self.active:
            return
        elif self.active == 'flag':    
            if self.currFlag:
                stripped = data.strip()
                if stripped == 'Return value':
                    self.active=False
                    return
                    
                if data and stripped and stripped not in ['(',')', '=', '], [']:
                    #print "DATA", data
            
                    if self.currFlag in self.flags:                
                        self.addFlagData(data)
                    else:
                        self.startFlag(data)
        elif self.active == 'command':
            data = data.replace( '\r\n', ' ' ).lstrip()
            data = data.strip('{}')
            data = data.replace('*', '\*') # for reStructuredText
            if '{' not in data and '}' not in data:                
                self.description += data
            #print data
            #self.active = False
        elif self.active == 'examples' and data != 'Python examples':
            #print "Example\n"
            #print data
            self.example += data
            #self.active = False
            
def _mayaDocsLocation( version=None ):
    #docLocation = path.path( os.environ.get("MAYA_LOCATION", '/Applications/Autodesk/maya%s/Maya.app/Contents' % version) )
    if version == None :
        version = getMayaVersion(extension=False)
    docLocation = path.path( pymel.util.getMayaLocation() ) 
    # print docLocation
    
    import platform
    if platform.system() == 'Darwin':
        docLocation = docLocation.parent.parent
    docLocation = path.path( docLocation / 'docs/Maya%s/en_US' % version )
    return docLocation
    
# class MayaDocsLoc(pymel.util.Singleton) :
#    """ Path to the Maya docs, cached at pymel start """
    
# TODO : cache doc location or it's evaluated for each _getCmdInfo !    
# MayaDocsLoc(_mayaDocsLocation()) 

def _getCmdInfoBasic( command ):
    
    flags = {}
    try:
        lines = cmds.help( command ).split('\n')
        synopsis = lines.pop(0)
        #print synopsis
        lines.pop(0) # 'Flags'
        #print lines
        
        for line in lines:
            tokens = line.split()
            try:
                tokens.remove('(multi-use)')
            except:
                pass
            #print tokens
            if len(tokens) > 1:
                numArgs = len(tokens)-2
                flags['shortname'] = str(tokens[0])
                flags['longname'] = str(tokens[1])
    except:
        pass
        #print "could not retrieve command info for", command
    return flags
  
def _getCmdInfo( command, version='8.5' ):
    """Since many maya Python commands are builtins we can't get use getargspec on them.
    besides most use keyword args that we need the precise meaning of ( if they can be be used with 
    edit or query flags, the shortnames of flags, etc) so we have to parse the maya docs"""
    
    try:
        docloc = _mayaDocsLocation(version)
        f = open( docloc / 'CommandsPython/%s.html' % (command) )    
        parser = CommandDocParser()
        parser.feed( f.read() )
        f.close()    

        data = parser.example
        data.rstrip()
        reg = re.compile(r'\bcmds\.')
        lines = data.split('\n')
        for i, line in enumerate(lines):
            line = reg.sub( 'pm.', line )
            line = line.replace( 'import maya.cmds as cmds', 'import pymel as pm' )
            line = '    >>> ' + line
            lines[i] = line
            
        data = '\n'.join( lines )
        
        
        try:
            for secondaryFlag, modifiedList in secondaryFlags[command]:
                parser.flags[secondaryFlag]['modified'] = modifiedList
                for primaryFlag in modifiedList:
                    try:
                         parser.flags[primaryFlag]['secondaryFlags'].append(secondaryFlag)
                    except:
                         parser.flags[primaryFlag]['secondaryFlags'] = [secondaryFlag]

        except KeyError:pass
          
        return {  'flags': parser.flags, 'description' : parser.description, 'example': data }
    except IOError:
        #print "could not find docs for %s" % command
        
        return { 'flags': _getCmdInfoBasic(command), 'description' : '', 'example': '' }
        #raise IOError, "cannot find maya documentation directory"

class NodeHierarchyDocParser(HTMLParser):
                
    def __init__(self):
        self.currentTag = None
        self.depth = 0
        self.lastDepth = -1
        self.tree = None
        self.currentLeaves = []
        
        HTMLParser.__init__(self)
    def handle_starttag(self, tag, attrs):
        
        self.currentTag = tag
    
    def handle_data(self, data):
        if self.currentTag == 'tt':
            self.lastDepth = self.depth
            self.depth = data.count('>')
        if self.currentTag == 'a':
            data = data.lstrip()
            
            if self.depth == self.lastDepth:                
                #print "adding to level", self.depth, data
                self.tree[ self.depth ].append( data )
                
            elif self.depth > self.lastDepth:
                #print "starting new level", self.depth, data
                try:
                    self.tree.append( [data] )
                except AttributeError:
                    self.tree = [data]
                    
            elif self.depth < self.lastDepth:
                for i in range(0, self.lastDepth-self.depth):
                    branch = self.tree.pop()
                    #print "closing level", self.lastDepth
                    self.tree[-1].append( branch )
                
                #print "adding to level", self.depth, data
                self.tree[ self.depth ].append( data )
    '''        
    def handle_data(self, data):
        if self.currentTag == 'tt':
            self.lastDepth = self.depth
            self.depth = data.count('>')
            
        if self.currentTag == 'a':
            data = data.lstrip()
            
            if self.depth == self.lastDepth:                
                #print "adding to level", self.depth, data
                self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )
                self.currentLeaves[ self.depth ] = data
                
            elif self.depth > self.lastDepth:
                #print "starting new level", self.depth, data
                try:
                    self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )
                    
                except AttributeError:
                    self.tree = RootedTree(data)
                    #self.tree = DirectedTree()    
                    #self.tree.add_node( data )                
                self.currentLeaves.append( data )
                    
            elif self.depth < self.lastDepth:
                for i in range(0, self.lastDepth-self.depth):
                    self.currentLeaves.pop()
                    #print "closing level", self.lastDepth
                    #self.tree[-1].append( branch )
                
                #print "adding to level", self.depth, data
                self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )        
                self.currentLeaves[ self.depth ] = data
    '''
        
def printTree( tree, depth=0 ):
    for branch in tree:
        if pymel.util.isIterable(branch):
            printTree( branch, depth+1)
        else:
            print '> '*depth, branch
            
def _getNodeHierarchy( version='8.5' ):
    docloc = _mayaDocsLocation(version)
    f = open( docloc / 'Nodes/index_hierarchy.html' )    
    parser = NodeHierarchyDocParser()
    parser.feed( f.read() )
    f.close()
    return parser.tree

class CommandModuleDocParser(HTMLParser):
                
    def __init__(self):
        self.cmdList = []
        
        HTMLParser.__init__(self)
        
    def handle_starttag(self, tag, attrs):
        try:
            attrs = attrs[0]
            #print attrs
            if tag == 'a' and attrs[0]=='href': 
                cmd = attrs[1].split("'")[1].split('.')[0]
                self.cmdList.append( cmd )
                #print cmd
        except IndexError: return
        
    #def handle_data(self, data):
    #    #print self.currentTag, data
    #    if self.currentTag == 'a':
    #        print data

def _getUICommands():
    f = open(pymel.util.moduleDir() / 'misc/commandsUI', 'r')
    cmds = f.read().split('\n')
    f.close()
    return cmds

def getModuleCommandList( category, version='8.5' ):
    docloc = _mayaDocsLocation(version)
    f = open( docloc / 'Commands/cat_' + category + '.html' )
    parser = CommandModuleDocParser()
    parser.feed( f.read() )
    f.close()
    return parser.cmdList + moduleCommandAddtions.get(category, [] )
    
#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------
                
def buildCachedData() :
    """Build and save to disk the list of Maya Python commands and their arguments"""
    
    # need to skip version extension or you can get things such as
    # autodesk/maya2008-x64/docs/Maya2008 Service Pack 1 x64/en_US for docs path
    ver = pymel.util.getMayaVersion(extension=False)
        
    newPath = pymel.util.moduleDir() / 'mayaCmdsList'+ver+'.bin'
    cmdlist = {}
    try :
        file = newPath.open(mode='rb')
        try :
            cmdlist,nodeHierarchy,uiClassList,moduleCmds = pickle.load(file)
            nodeHierarchyTree = IndexedTree(nodeHierarchy)
        except :
            print "Unable to load the list of Maya commands from '"+file.name+"'"
        
        file.close()
    except :
        print "Unable to open '"+newPath+"' for reading the list of Maya commands"
    
    if not len(cmdlist): # or not isinstance(cmdlist,list):        
        
        print "Rebuilding the list of Maya commands..."
        
        nodeHierarchy = _getNodeHierarchy(ver)
        nodeHierarchyTree = IndexedTree(nodeHierarchy)
        uiClassList = _getUICommands()
        for moduleName, longname in moduleNameShortToLong.items():
            moduleNameShortToLong[moduleName] = getModuleCommandList( longname, ver )
                        
        tmpCmdlist = inspect.getmembers(cmds, callable)
        cmdlist = {}
        moduleCmds = pymel.util.defaultdict(list)
        for funcName, data in tmpCmdlist :    
            
            
            #modifiers = {}

                
            # determine to which module this function belongs
            module = None
            if funcName in ['eval', 'file', 'filter', 'help', 'quit']:
                module = None
            elif funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
                module = 'ctx'
            elif funcName in uiClassList:
                module = 'uiClass'
            elif funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
                module = 'node'
            else:
                for moduleName, commands in moduleNameShortToLong.items():
                    if funcName in commands:
                        module = moduleName
                
                if module is None:    
                    if mm.eval('whatIs "%s"' % funcName ) == 'Run Time Command':
                        module = 'runtime'
                    else:
                        module = 'other'
            
            cmdInfo = {}
            
            if module:
                moduleCmds[module].append(funcName)
            
            if module != 'runtime':
                cmdInfo = _getCmdInfo(funcName, ver)
            
            cmdInfo['type'] = module
            cmdlist[funcName] = cmdInfo
            
            '''
            # func, args, (usePyNode, baseClsName, nodeName)
            # args = dictionary of command flags and their data
            # usePyNode = determines whether the class returns its 'nodeName' or uses PyNode to dynamically return
            # baseClsName = for commands which should generate a class, this is the name of the superclass to inherit
            # nodeName = most creation commands return a node of the same name, this option is provided for the exceptions
            try:
                cmdlist[funcName] = args, pymelCmdsList[funcName] )        
            except KeyError:
                # context commands generate a class based on unicode (which is triggered by passing 'None' to baseClsName)
                if funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
                     cmdlist[funcName] = (funcName, args, (False, None, None) )
                else:
                    cmdlist[funcName] = (funcName, args, () )
            '''
        
        #uiClassList = map( pymel.util.capitalize, uiClassList )
                
        try :
            file = newPath.open(mode='wb')
            try :
                pickle.dump( (cmdlist,nodeHierarchy,uiClassList,moduleCmds),  file, 2)
                print "done"
            except:
                print "Unable to write the list of Maya commands to '"+file.name+"'"
            file.close()
        except :
            print "Unable to open '"+newPath+"' for writing"

    
    return (cmdlist,nodeHierarchyTree,uiClassList,moduleCmds)


                
#---------------------------------------------------------------
        
cmdlist, nodeHierarchy, uiClassList, moduleCmds = buildCachedData()
# quick fix until we make a Singleton of nodeHierarchy
def NodeHierarchy() :
    return nodeHierarchy

def getUncachedCmds():
    return list( set( map( itemgetter(0), inspect.getmembers( cmds, callable ) ) ).difference( cmdlist.keys() ) )
        
        
#-----------------------
# Function Factory
#-----------------------

def _addDocs(inObj, newObj, cmdInfo ):
    try:
        docstring = cmdInfo['description'] + '\n\n'
        flagDocs = cmdInfo['flags']
        if flagDocs:
            docstring += 'Flags:\n'
            for flag in sorted(flagDocs.keys()):
                docs = flagDocs[flag]

                label = '    - %s (%s)' % (flag, docs['shortname'])
                docstring += label + '\n'
                if docs['modes']:
                    docstring += '        - %s\n' % (', '.join(docs['modes']))
                try:
                    docstring += '        - modifies flags %s\n' % ( ', '.join(docs['modified'] ))
                except KeyError: pass
                
                docstring += '        - %s\n' %  docs['docstring']
        if cmdInfo['example']:
            docstring += '\nExample:\n' + cmdInfo['example']
        if inObj.__doc__:
            docstring = inObj.__doc__ + '\n' + docstring
        newObj.__doc__ = docstring
            
    except:
        pass
        #print "could not find help docs for %s" % inObj
    #except:
    #    print "failed on command %s %s" % ( inObj, docs )

def _getUICallbackFlags(flagDocs):
    commandFlags = []
    for flag, data in flagDocs.items():
        if 'command' in flag.lower():
            commandFlags += [flag, data['shortname']]
    return commandFlags

def getUICommandsWithCallbacks():
    cmds = []
    for funcName in moduleCmds['ui']:
        cbFlags = _getUICallbackFlags(cmdlist[funcName]['flags'])
        if cbFlags:
            cmds.append( [funcName, cbFlags] )
    return cmds


def functionFactory( funcName, returnFunc, module=None, rename=None ):
    """create a new function, apply the given returnFunc to the results (if any), 
    and add to the module given by 'moduleName'.  Use pre-parsed command documentation
    to add to __doc__ strings for the command."""

    #if module is None:
    #   module = _thisModule
    try:
        inFunc = getattr(module, funcName)          
    except AttributeError:
        try:
            inFunc = getattr(cmds,funcName)
        except AttributeError:
            return


    try:
        cmdInfo = cmdlist[funcName]
    except KeyError:
        return
        
    # if the function is not a builtin and there's no return command to map, just add docs
    if type(inFunc) == types.FunctionType and returnFunc is None:
        _addDocs( inFunc, inFunc, cmdInfo )
        if rename: inFunc.__name__ = rename
        return inFunc
    
    elif type(inFunc) == types.BuiltinFunctionType or ( type(inFunc) == types.FunctionType and returnFunc ):                    
            
        #----------------------------        
        # UI commands with callbacks
        #----------------------------
        
        if funcName in moduleCmds['ui']:
            # wrap ui callback commands to ensure that the correct types are returned.
            # we don't have a list of which command-callback pairs return what type, but for many we can guess based on their name.
            if funcName.startswith('float'):
                callbackReturnFunc = float
            elif funcName.startswith('int'):
                callbackReturnFunc = int
            elif funcName.startswith('checkBox') or funcName.startswith('radioButton'):
                callbackReturnFunc = lambda x: x == 'true'
            else:
                callbackReturnFunc = None
            
            if callbackReturnFunc:                
                commandFlags = _getUICallbackFlags(cmdInfo['flags'])
            else:
                commandFlags = []
                    
            #print inFunc.__name__, commandFlags        
            def newFunc( *args, **kwargs):
                for key in commandFlags:
                    try:
                        cb = kwargs[ key ]
                        if hasattr(cb, '__call__'):
                            def callback(*args):
                                newargs = []
                                for arg in args:
                                    arg = callbackReturnFunc(arg)
                                    newargs.append(arg)
                                newargs = tuple(newargs)
                                return cb( *newargs )
                            kwargs[ key ] = callback
                    except KeyError: pass
                
                res = apply( inFunc, args, kwargs )
                if not kwargs.get('query', kwargs.get('q',False)): # and 'edit' not in kwargs and 'e' not in kwargs:
                    if isinstance(res, list):                
                        try:
                            res = map( returnFunc, res )
                        except: pass
                
                    elif res:
                        try:
                            res = returnFunc( res )
                        except: pass
                return res
            
        #------------------------------------------------------------        
        # commands whose creation/edit results need post-processing
        #------------------------------------------------------------
        elif returnFunc:
            def newFunc( *args, **kwargs):
                res = apply( inFunc, args, kwargs )
                if not kwargs.get('query', kwargs.get('q',False)): # and 'edit' not in kwargs and 'e' not in kwargs:
                    if isinstance(res, list):                
                        try:
                            res = map( returnFunc, res )
                        except: pass
                
                    elif res:
                        try:
                            res = returnFunc( res )
                        except: pass
                return res
        #-----------
        # Others
        #-----------
        else:
            def newFunc(*args, **kwargs): return apply(inFunc, args, kwargs)
    
        _addDocs( inFunc, newFunc, cmdInfo )
        

        if rename: 
            newFunc.__name__ = rename
        else:
            newFunc.__name__ = inFunc.__name__
            
        return newFunc
    #else:
    #    print "function %s is of incorrect type: %s" % (funcName, type(inFunc) )

def _addFlagCmdDocs(f,name,inFunc,flag,docstring):
    f.__name__ = name
    if docstring:
        f.__doc__ = docstring
    else:
        try:
            f.__doc__ = cmdlist[inFunc.__name__]['flags'][flag]['docstring']
        except KeyError: pass    
    return f
            
def makeCreateFlagCmd( name, inFunc, flag, docstring='', returnFunc=None ):
    if returnFunc:
        def f(self, **kwargs):
            kwargs[flag]=True 
            return returnFunc( inFunc( self, **kwargs ) )
    else:
        def f(self, **kwargs):
            kwargs[flag]=True 
            return inFunc( self, **kwargs )
    return _addFlagCmdDocs(f, name, inFunc, flag, docstring )


def makeQueryFlagCmd( name, inFunc, flag, docstring='', returnFunc=None ):
    #name = 'get' + flag[0].upper() + flag[1:]
    if returnFunc:
        def f(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True 
            return returnFunc( inFunc( self, **kwargs ) )
    else:
        def f(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True 
            return inFunc( self, **kwargs )
    return _addFlagCmdDocs(f, name, inFunc, flag, docstring )

    
def makeEditFlagCmd( name, inFunc, flag, docstring='' ):
    #name = 'set' + flag[0].upper() + flag[1:]    
    def f(self, val, **kwargs): 
        kwargs['edit']=True
        kwargs[flag]=val 
        try:
            return inFunc( self, **kwargs )
        except TypeError:
            kwargs.pop('edit')
            return inFunc( self, **kwargs )
            
    return _addFlagCmdDocs(f, name, inFunc, flag, docstring )

def createFunctions( moduleName, returnFunc=None ):
    module = __import__(moduleName, globals(), locals(), [''])
    moduleName = moduleName.split('.')[-1]
    for funcName in moduleCmds[ moduleName ]:
        if not hasattr( module, funcName ):
            func = functionFactory( funcName, None )
            if func:
                func.__module__ = moduleName
                setattr( module, funcName, func )

#: overrideMethods specifies methods of base classes which should not be overridden by sub-classes 
overrideMethods = {}
overrideMethods['Constraint'] = ('getWeight', 'setWeight')

def makeMetaNode( moduleName ):
    module = __import__(moduleName, globals(), locals(), [''])
    class metaNode(type) :
        """
        A metaclass for creating classes based on node type.  Methods will be added to the new classes 
        based on info parsed from the docs on their command counterparts.
        """
    
        
        def __new__(cls, classname, bases, classdict):
            
            nodeType = pymel.util.uncapitalize(classname)
            
            try:
                infoCmd = False
                try:
                    nodeType = nodeTypeToNodeCommand[ nodeType ]
                except KeyError:
                    try:
                        nodeType = nodeTypeToInfoCommand[ nodeType ]
                        infoCmd = True
                    except KeyError: pass
                
                #if nodeHierarchy.children( nodeType ):
                #    print nodeType, nodeHierarchy.children( nodeType )
                cmdInfo = cmdlist[nodeType]
                
                try:    
                    func = getattr(module, nodeType)
    
                except AttributeError:
                    func = getattr(cmds,nodeType)
                
                # add documentation
                classdict['__doc__'] = 'class counterpart of function L{%s}\n\n%s\n\n' % (nodeType, cmdInfo['description'])
                
                for flag, flagInfo in cmdInfo['flags'].items():
                     
                     # don't create methods for query or edit, or for flags which only serve to modify other flags
                    if flag in ['query', 'edit'] or 'modified' in flagInfo:
                        continue
                    
                    modes = flagInfo['modes']
    
                    # query command
                    if 'query' in modes:
                        methodName = 'get' + pymel.util.capitalize(flag)
                        if methodName not in classdict:
                            if methodName not in overrideMethods.get( bases[0].__name__ , [] ):
                                classdict[methodName] = makeQueryFlagCmd( methodName, func, 
                                    flag, flagInfo['docstring'] )
                            #else: print "%s: skipping %s" % ( classname, methodName )
                    
                    # edit command: 
                    if 'edit' in modes or ( infoCmd and 'create' in modes ):
                        # if there is a corresponding query we use the 'set' prefix. 
                        if 'query' in modes:
                            methodName = 'set' + pymel.util.capitalize(flag)
                        #if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
                        else:
                            methodName = flag
                            
                        if methodName not in classdict:
                            if methodName not in overrideMethods.get( bases[0].__name__ , [] ):
                                classdict[methodName] = makeEditFlagCmd( methodName, func,
                                     flag, flagInfo['docstring'] )
                        
            except KeyError: # on cmdlist[nodeType]
                pass
                
            return super(metaNode, cls).__new__(cls, classname, bases, classdict)
    return metaNode

def makeDocs( mayaVersion='8.5' ):
    "internal use only"
    
    import re
    import epydoc.cli
    
    pymeldir = pymel.util.moduleDir()
    
    # generate epydocs
    os.chdir( pymeldir )
    sys.argv = [pymeldir, '--debug',  '--config=%s' % os.path.join( pymeldir, 'epydoc.cfg') ]
    epydoc.cli.cli(useLogger=False)
    
    return
    
    #---------------------------------------------------------------
    # skipping all this for now
    #---------------------------------------------------------------
    '''
    # copy over maya doc pages and link to them from the epydoc pages    
    docdir = pymeldir / 'docs'
    
    try:
        (docdir / 'CommandsPython').mkdir()
    except OSError:
        pass
    
    htmlFile = 'pymel-module.html'
    f = open( os.path.join( docdir, htmlFile), 'r'  )
    lines = f.readlines()
    f.close()
    
    reg = re.compile("(pymel-module.html#)([a-zA-Z0-9_]+)")
    for i, line in enumerate(lines):
        buf = reg.split( line )
        try:
            command = buf[2]
            localHelpFile = path( 'CommandsPython/' + command + '.html' )
            line = buf[0] + localHelpFile + buf[3]
            localHelpFile = docdir / localHelpFile
            if not localHelpFile.exists():                
                globalHelpFile = path( _mayaCommandHelpFile( command, mayaVersion ) )
                print "copying", globalHelpFile, localHelpFile
                globalHelpFile.copy( localHelpFile.parent )
                
        except: pass
        lines[i] = line 
    
    f = open( os.path.join(pymeldir, 'docs', htmlFile), 'w' ) 
    f.writelines(lines)
    f.close()
    '''

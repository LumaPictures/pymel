
from pymel.util.trees import *
import pymel.util as util
import pymel.mayahook as mayahook
assert mayahook.mayaInit() 
print "Maya up and running"
import pymel.tools.py2mel as py2mel
#from general import PyNode
import pymel.api as _api
import sys, os, inspect, pickle, re, types, os.path
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
    'modeling' : 'Modeling',
    'rendering': 'Rendering',
    'effects'    : 'Effects',
    'animation'  : 'Animation',
    'windows'    : 'Windows',
    'system'    : 'System',
    'general' : 'General'
}

#: secondary flags can only be used in conjunction with other flags so we must exclude them when creating classes from commands.
#: because the maya docs do not specify in any parsable way which flags are secondary modifiers, we must maintain this dictionary.
#: once this list is reliable enough and includes default values, we can use them as keyword arguments in the class methods that they modify.
secondaryFlags = {
    'xform' : ( ( 'absolute',         None,[] ),
                ( 'relative',         None,[] ),
                ( 'euler',            None,['relative'] ),
                ( 'objectSpace',      True, ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotateTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots'] ),
                ( 'worldSpace',       False, ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotateTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots'] ),
                ( 'preserve',         None,['scalePivot', 'rotatePivot', 'rotateOrder', 'rotateAxis', 'centerPivots'] ),
                ( 'worldSpaceDistance', None,['scalePivot', 'rotatePivot', 'scaleTranslation', 'rotateTranslation', 'translation', 'pivots'] )
            ),
    'file' : ( ( 'loadAllDeferred', False, ['open'] ),
               ( 'loadNoReferences', False, ['open', 'i', 'reference', 'loadReference'] ),
               ( 'loadReferenceDepth', None, ['open', 'i', 'reference', 'loadReference'] ),
               ( 'force',           False, ['open', 'newFile', 'save', 'exportAll', 'exportSelected', 'exportAnim', 
                                      'exportSelectedAnim', 'exportAnimFromReference', 'exportSelectedAnimFromReference' ] ),             
               ( 'constructionHistory', True, ['exportSelected'] ),
               ( 'channels',         True, ['exportSelected'] ),
               ( 'constraints',      True, ['exportSelected'] ),
               ( 'expressions',      True, ['exportSelected'] ),
               ( 'shader',           True, ['exportSelected'] ),
               ( 'defaultNamespace', False, ['reference', 'i'] ),
               ( 'deferReference',   False, ['reference', 'i'] ),
               ( 'editCommand',      None, ['cleanReference'] ),
               ( 'groupReference',   False, ['reference', 'i'] ),
               ( 'groupLocator',  None,['reference'] ),
               ( 'groupName',  None,['reference', 'i'] ),
               ( 'namespace',  None,['reference', 'exportAsReference'] ),
               ( 'referenceNode',  None,['reference', 'exportAnimFromReference', 'exportSelectedAnimFromReference'] ),
               ( 'renameAll', None,['i'] ),
               ( 'renamingPrefix',  None,['reference', 'i','exportAsReference'] ),
               #( 'saveTextures', "unlessRef", ['saveAs']),
               ( 'swapNamespace',  None, ['reference', 'i'] ),
               ( 'sharedReferenceFile',  None, ['reference'] ),
               ( 'sharedNodes',  None, ['reference'] ),
               ( 'returnNewNodes',  False, ['open', 'reference', 'i', 'loadReference' ] ),
               #( 'loadSettings', ),
               ( 'preserveReferences',  False, ['i', 'exportAll', 'exportSelected'] ),
               ( 'preSaveScript', None, ['save'] ),
               ( 'postSaveScript', None, ['save'] ),
               ( 'type', None, ['open', 'newFile', 'save', 'exportAll', 'exportSelected', 'exportAnim', 
                                      'exportSelectedAnim', 'exportAnimFromReference', 'exportSelectedAnimFromReference' ] ), 
             )
}



#---------------------------------------------------------------
#        Doc Parser
#---------------------------------------------------------------
class CommandDocParser(HTMLParser):

    def __init__(self, command):
        self.command = command
        self.flags = {}  # shortname, args, docstring, and a list of modes (i.e. edit, create, query)
        self.currFlag = ''
        # iData is used to track which type of data we are putting into flags, and corresponds with self.datatypes
        self.iData = 0
        self.pcount = 0
        self.active = False  # this is set once we reach the portion of the document that we want to parse
        self.description = ''
        self.example = ''
        self.emptyModeFlags = [] # when flags are in a sequence ( lable1, label2, label3 ), only the last flag has queryedit modes. we must gather them up and fill them when the last one ends
        HTMLParser.__init__(self)
    
    def startFlag(self, data):
        #print self, data
        #assert data == self.currFlag
        self.iData = 0
        self.flags[self.currFlag] = {'longname': self.currFlag, 'shortname': None, 'args': None, 'numArgs': None, 'docstring': '', 'modes': [] }
    
    def addFlagData(self, data):
        # Shortname
        if self.iData == 0:
            self.flags[self.currFlag]['shortname'] = data.lstrip('-')
            
        # Arguments
        elif self.iData == 1:
            typemap = {    
             'string'  : unicode,
             'float'   : float,
             'double'  : float,
             'linear'  : float,
             'angle'   : float,
             'int'     : int,
             'uint'    : int,
             'index'   : int,
             'integer'  : int,
             'boolean'  : bool,
             'script'   : callable,
             'name'     : 'PyNode',
             'select'   : 'PyNode'
            }
            args = [ typemap.get( x.strip(), x.strip() ) for x in data.strip('[]').split(',') ] 
            numArgs = len(args)
            if numArgs == 0:
                args = bool
                numArgs = 1
            elif numArgs == 1:
                args = args[0]
                    
            self.flags[self.currFlag]['args'] = args
            self.flags[self.currFlag]['numArgs'] = numArgs
            
        # Docstring  
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
        try:
            if not self.flags[self.currFlag]['modes']:
                self.emptyModeFlags.append(self.currFlag)
            elif self.emptyModeFlags:
                    #print "past empty flags:", self.command, self.emptyModeFlags, self.currFlag
                    basename = re.match( '([a-zA-Z]+)', self.currFlag ).groups()[0]
                    modes = self.flags[self.currFlag]['modes']
                    self.emptyModeFlags.reverse()
                    for flag in self.emptyModeFlags:
                        if re.match( '([a-zA-Z]+)', flag ).groups()[0] == basename:
                            self.flags[flag]['modes'] = modes
                        else:
                            break
                        
                    self.emptyModeFlags = []
        except KeyError, msg:
            pass
            #print self.currFlag, msg
        
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
            newFlag = attrs[0][1][4:]
            newFlag = newFlag.lstrip('-')
            self.currFlag = newFlag      
            self.iData = 0
            #print "NEW FLAG", attrs
            #self.currFlag = attrs[0][1][4:]
            
    
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
        
    
# class MayaDocsLoc(util.Singleton) :
#    """ Path to the Maya docs, cached at pymel start """
    
# TODO : cache doc location or it's evaluated for each getCmdInfo !    
# MayaDocsLoc(mayahook.mayaDocsLocation()) 

class CommandInfo(object):
    def __init__(self, flags={}, description='', example='', type='other'):
        self.flags = flags
        self.description = description
        self.example = example
        self.type = type

class FlagInfo(object):
    def __init__(self, longname, shortname=None, args=None, numArgs=None, docstring='', modes= [] ):
        self.longname = longname
        self.shortname = shortname
        self.args = args
        self.numArgs = numArgs
        self.docstring = docstring
        self.modes = modes

pythonReservedWords = ['and', 'del', 'from', 'not', 'while', 'as', 'elif', 'global', 'or', 
                       'with', 'assert', 'else', 'if', 'pass', 'yield', 'break', 'except', 
                       'import', 'print', 'class', 'exec', 'in', 'raise', 'continue', 
                       'finally', 'is', 'return', 'def', 'for', 'lambda', 'try']
  
def getCmdInfoBasic( command ):
    typemap = {    
             'string'  : unicode,
             'length'  : float,
             'float'   : float,
             'angle'   : float,
             'int'     : int,
             'unsignedint' : int,
             'on|off'  : bool,
             'script'  : callable,
             'name'    : 'PyNode'
    }
    flags = {}
    shortFlags = {}
    removedFlags = {}
    try:     
        lines = cmds.help( command ).split('\n')
    except RuntimeError:
        pass
    else:
        synopsis = lines.pop(0)
        # certain commands on certain platforms have an empty first line
        if not synopsis:
            synopsis = lines.pop(0)
        #print synopsis
        if lines:
            lines.pop(0) # 'Flags'
            #print lines
            
            for line in lines:
                line = line.replace( '(Query Arg Mandatory)', '' )
                line = line.replace( '(Query Arg Optional)', '' )
                tokens = line.split()
                try:
                    tokens.remove('(multi-use)')
                except:
                    pass
                #print tokens
                if len(tokens) > 1:
                    
                    args = [ typemap.get(x.lower(), util.uncapitalize(x) ) for x in tokens[2:] ]
                    numArgs = len(args)
                    
                    # lags with no args in mel require a boolean val in python
                    if numArgs == 0:
                        args = bool
                        # numArgs will stay at 0, which is the number of mel arguments.  
                        # this flag should be renamed to numMelArgs
                        #numArgs = 1
                    elif numArgs == 1:
                        args = args[0]
                          
                    longname = str(tokens[1][1:])
                    shortname = str(tokens[0][1:])

                    
                    if longname in pythonReservedWords:                       
                        removedFlags[ longname ] = shortname 
                        longname = shortname
                    elif shortname in pythonReservedWords:
                        removedFlags[ shortname ] = longname 
                        shortname = longname
                    #sometimes the longname is empty, so we'll use the shortname for both
                    elif longname == '':
                        longname = shortname
                        
                    flags[longname] = { 'longname' : longname, 'shortname' : shortname, 'args' : args, 'numArgs' : numArgs, 'docstring' : '' }
                    shortFlags[shortname] = flags[longname]
        
    #except:
    #    pass
        #print "could not retrieve command info for", command
    res = { 'flags': flags, 'shortFlags': shortFlags, 'description' : '', 'example': '', 'type' : 'other' }
    if removedFlags:
        res['removedFlags'] = removedFlags 
    return res

def getCmdInfo( command, version='8.5', python=True ):
    """Since many maya Python commands are builtins we can't get use getargspec on them.
    besides most use keyword args that we need the precise meaning of ( if they can be be used with 
    edit or query flags, the shortnames of flags, etc) so we have to parse the maya docs"""
    
    basicInfo = getCmdInfoBasic(command)
    
    try:
        docloc = mayahook.mayaDocsLocation(version)
        if python:
            docloc = os.path.join( docloc , 'CommandsPython/%s.html' % (command) )
        else:
            docloc = os.path.join( docloc , 'Commands/%s.html' % (command) )
            
        f = open( docloc )    
        parser = CommandDocParser(command)
        parser.feed( f.read() )
        f.close()    

        example = parser.example
        example = example.rstrip()
        if python:
            reg = re.compile(r'\bcmds\.')
            lines = example.split('\n')
            for i, line in enumerate(lines):
                line = reg.sub( 'pm.', line )
                line = line.replace( 'import maya.cmds as cmds', 'import pymel as pm' )
                line = '    >>> ' + line
                lines[i] = line
                
            example = '\n'.join( lines )
        
        # start with basic info, gathered using mel help command, then update with info parsed from docs
        # we copy because we need access to the original basic info below
        flags = basicInfo['flags'].copy()
        flags.update( parser.flags )
        
        if command in secondaryFlags:
            for secondaryFlag, defaultValue, modifiedList in secondaryFlags[command]:
                #print command, "2nd", secondaryFlag
                flags[secondaryFlag]['modified'] = modifiedList
                #print sorted(modifiedList)
                #print sorted(parser.flags.keys())
                for primaryFlag in modifiedList:
                    #print command, "1st", primaryFlag
                    if 'secondaryFlags' in parser.flags[primaryFlag]:
                         flags[primaryFlag]['secondaryFlags'].append(secondaryFlag)
                    else:
                         flags[primaryFlag]['secondaryFlags'] = [secondaryFlag]
        
                         
        # add shortname lookup
        #print command, sorted( basicInfo['flags'].keys() )
        #print command, sorted( flags.keys() )
        
        # args and numArgs is more reliable from mel help command than from parsed docs,
        # so, here we put that back in place and create shortflags. 
        shortFlags = basicInfo['shortFlags']
        for flag, flagData in flags.items():
            try:
                basicFlagData = basicInfo['flags'][flag]
#                if flagData['args'] != basicFlagData['args']:
#                    docArgs = flagData['args']
#                    helpArgs = basicFlagData['args']
#                    if ( isinstance(docArgs, str) and '|' in docArgs) or (docArgs == str and helpArgs == callable):
#                        flagData['args'] = helpArgs
#                    else:
#                        print command, flag, docArgs, helpArgs
#                else:
#                    flagData['args'] = basicFlagData['args']
                    
                flagData['args'] = basicFlagData['args']
                flagData['numArgs'] = basicFlagData['numArgs']
            except KeyError: pass
            
            shortFlags[ flagData['shortname'] ] = flagData
           
        #except KeyError:pass
          
        res = {  'flags': flags, 'shortFlags': shortFlags, 'description' : parser.description, 'example': example }
        try:
            res['removedFlags'] = basicInfo['removedFlags']
        except KeyError: pass
        return res
    
    
    except IOError:
        #print "could not find docs for %s" % command
        return basicInfo
        
        #raise IOError, "cannot find maya documentation directory"

class NodeHierarchyDocParser(HTMLParser):
 
    def parse(self):
        docloc = mayahook.mayaDocsLocation(self.version)
        f = open( os.path.join( docloc , 'Nodes/index_hierarchy.html' ) )    
        self.feed( f.read() )
        f.close()
        return self.tree
    
    def __init__(self, version=None):
        self.version = version
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
        if util.isIterable(branch):
            printTree( branch, depth+1)
        else:
            print '> '*depth, branch
            
def _getNodeHierarchy( version='8.5' ): 
    parser = NodeHierarchyDocParser(version)
    return parser.parse()

class CommandModuleDocParser(HTMLParser):
    #: these are commands which need to be manually added to the list parsed from the docs
    moduleCommandAdditions = {
        'Windows' : ['connectControl', 'deleteUI','uiTemplate','setUITemplate','renameUI','setParent','objectTypeUI','lsUI', 'disable', 'dimWhen'],
        'General' : ['encodeString', 'format', 'assignCommand', 'commandEcho', 'condition', 'evalDeferred', 'isTrue', 'itemFilter', 'itemFilterAttr', 
                     'itemFilterRender', 'itemFilterType', 'pause', 'refresh', 'stringArrayIntersector', 'selectionConnection']
    }
    
    def parse(self):
        docloc = mayahook.mayaDocsLocation(self.version)
        f = open( os.path.join( docloc , 'Commands/cat_' + self.category + '.html' ) )
        self.feed( f.read() )
        f.close()
        return self.cmdList + self.moduleCommandAdditions.get(self.category, [] )
              
    def __init__(self, category, version=None ):
        self.cmdList = []
        self.category = category
        self.version = version
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
    f = open( os.path.join( util.moduleDir() , 'misc/commandsUI') , 'r') 
    cmds = f.read().split('\n')
    f.close()
    return cmds

def getModuleCommandList( category, version='8.5' ):
    parser = CommandModuleDocParser(category, version)
    return parser.parse()

class ApiArrayTypeInfo(object):
    """Simple Struct-type class for holding type and length of api array types"""
    def __init__( self, type, length ):
        self._type = type
        self._length = length
    def type( self ):
        return self._type
    def length(self):
        return self._length
    def __str__(self):
        return self._type + str(self._length)
    def __repr__(self):
        return '%s(%s,%s)' % (self.__class__.__name__, self._type, self._length )
  
def buildCachedData() :
    """Build and save to disk the list of Maya Python commands and their arguments"""
    
    # With extension can't get docs on unix 64
    # path is
    # /usr/autodesk/maya2008-x64/docs/Maya2008/en_US/Nodes/index_hierarchy.html
    # and not
    # /usr/autodesk/maya2008-x64/docs/Maya2008-x64/en_US/Nodes/index_hierarchy.html
    ver = mayahook.getMayaVersion(extension=False)
        
    newPath = os.path.join( util.moduleDir(),  'mayaCmdsList'+ver+'.bin' )
    cmdlist = {}
    try :
        file = open(newPath, mode='rb')
        try :
            cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds = pickle.load(file)
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
        nodeCommandList = []
        for moduleName, longname in moduleNameShortToLong.items():
            moduleNameShortToLong[moduleName] = getModuleCommandList( longname, ver )
                        
        tmpCmdlist = inspect.getmembers(cmds, callable)
        cmdlist = {}
        #moduleCmds = defaultdict(list)
        moduleCmds = dict( (k,[]) for k in moduleNameShortToLong.keys() )
        moduleCmds.update( {'other':[], 'runtime': [], 'context': [], 'uiClass': [] } )
        
        for funcName, data in tmpCmdlist :    
            
            
            #modifiers = {}

                
            # determine to which module this function belongs
            module = None
            if funcName in ['eval', 'file', 'filter', 'help', 'quit']:
                module = None
            elif funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
                module = 'context'
            #elif funcName in uiClassList:
            #    module = 'uiClass'
            #elif funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
            #    module = 'node'
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
                cmdInfo = getCmdInfo(funcName, ver)
            
            cmdInfo['type'] = module
            
            
            if funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
                nodeCommandList.append(funcName)
                cmdInfo = testNodeCmd( funcName, cmdInfo, False )
                
                
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
        
            
        try :
            file = open(newPath, mode='wb')
            try :
                pickle.dump( (cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds),  file, 2)
                print "done"
            except:
                print "Unable to write the list of Maya commands to '"+file.name+"'"
            file.close()
        except :
            print "Unable to open '"+newPath+"' for writing"

    
    return (cmdlist,nodeHierarchyTree,uiClassList,nodeCommandList,moduleCmds)


                
#---------------------------------------------------------------
        
cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds = buildCachedData()
# quick fix until we make a util.Singleton of nodeHierarchy
def NodeHierarchy() :
    return nodeHierarchy

def getUncachedCmds():
    return list( set( map( itemgetter(0), inspect.getmembers( cmds, callable ) ) ).difference( cmdlist.keys() ) )
        
def getInheritance( mayaType ):
    """Get parents as a list, starting from the node after dependNode, and ending with the mayaType itself.
    This method relies on creating the node to use with cmds.nodeType -- i would prefer a cleaner solution."""
    parent = None
    try:
        state = cmds.undoInfo( q=1, state=1)
        cmds.undoInfo( state=0)
        res = cmds.createNode( mayaType )
        parent = cmds.nodeType( res, inherited=1)
        cmds.delete(res)
        cmds.undoInfo( state=state)
        return parent
    except:
        # there's a chance it failed on delete
        return parent
   
#-----------------------
# Function Factory
#-----------------------

def _addCmdDocs(inObj, newObj, cmdInfo ):
    
    #try:
    docstring = cmdInfo['description'] + '\n\n'
    
    flagDocs = cmdInfo['flags']
    if flagDocs:
        
        docstring += 'Flags:\n'
        for flag in sorted(flagDocs.keys()):
            docs = flagDocs[flag]

            label = '    - %s (%s)' % (flag, docs['shortname'])
            docstring += label + '\n'
            
            # docstring
            try:
                docstring += '        - %s\n' %  docs['docstring']
            except KeyError: pass
            
            # modes
            if docs.get('modes',False):
                docstring += '        - modes: *%s*\n' % (', '.join(docs['modes']))
            
            #modified
            try:
                modified = docs['modified']
                if modified:
                    docstring += '        - modifies: *%s*\n' % ( ', '.join( modified ))
            except KeyError: pass
            
            #secondary flags
            try:
                docstring += '        - secondary flags: *%s*\n' % ( ', '.join(docs['secondaryFlags'] ))
            except KeyError: pass
            
            #args
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
            docstring += '        - datatype: *%s*\n' % ( typ )
        
        """
        docstring += ':Keywords:\n'
        for flag in sorted(flagDocs.keys()):
            docs = flagDocs[flag]

            #label = '  %s (%s)' % (flag, docs['shortname'])
            label = '  %s' % (flag)
            docstring += label + '\n'
            
            try:
                docstring += '    %s\n' %  docs['docstring']
            except KeyError: pass
            
            
            if docs.get('modes',False):
                docstring += '        - modes: *%s*\n' % (', '.join(docs['modes']))
            
            try:
                modified = docs['modified']
                if modified:
                    docstring += '        - modifies: *%s*\n' % ( ', '.join( ))
            except KeyError: pass
            
            try:
                docstring += '        - secondary flags: *%s*\n' % ( ', '.join(docs['secondaryFlags'] ))
            except KeyError: pass
            
        docstring += '\n'
        """ 
    if cmdInfo['example']:
        docstring += '\nExample:\n' + cmdInfo['example']
        
    if inObj.__doc__:
        docstring = inObj.__doc__ + '\n' + docstring
    
    newObj.__doc__ = docstring
            

        #print "could not find help docs for %s" % inObj
    #except:
    #    print "failed to add docstring to %s using %s" % ( inObj.__name__, cmdInfo )

def _getUICallbackFlags(flagDocs):
    commandFlags = []
    for flag, data in flagDocs.items():
        if 'command' in flag.lower():
            commandFlags += [flag, data['shortname']]
    return commandFlags

def getUICommandsWithCallbacks():
    cmds = []
    for funcName in moduleCmds['windows']:
        cbFlags = _getUICallbackFlags(cmdlist[funcName]['flags'])
        if cbFlags:
            cmds.append( [funcName, cbFlags] )
    return cmds


def functionFactory( funcNameOrObject, returnFunc=None, module=None, rename=None, uiWidget=False ):
    """create a new function, apply the given returnFunc to the results (if any), 
    and add to the module given by 'moduleName'.  Use pre-parsed command documentation
    to add to __doc__ strings for the command."""

    #if module is None:
    #   module = _thisModule
    if isinstance( funcNameOrObject, basestring ):
        funcName = funcNameOrObject
        try:
            inFunc = getattr(module, funcName)
            #if funcName in moduleCmds['windows']: print "function %s found in module %s: %s" % ( funcName, module.__name__, inFunc.__name__)

        except AttributeError:
            try:
                inFunc = getattr(cmds,funcName)
                #if funcName in moduleCmds['windows']: print "function %s found in module %s: %s" % ( funcName, cmds.__name__, inFunc.__name__)
            except AttributeError:
                return
    else:
        funcName = funcNameOrObject.__name__
        inFunc = funcNameOrObject

                   
    cmdInfo = cmdlist[funcName]
    funcType = type(inFunc)
    

    
    # if the function is not a builtin and there's no return command to map, just add docs
    if funcType == types.FunctionType and returnFunc is None:
        # there are no docs to add for runtime commands
        if cmdInfo['type'] != 'runtime':
            _addCmdDocs( inFunc, inFunc, cmdInfo )
        if rename: inFunc.__name__ = rename
        #else: inFunc.__name__ = funcName
        return inFunc
    
    elif funcType == types.BuiltinFunctionType or ( funcType == types.FunctionType and returnFunc ):                    
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                print "Function found in module %s has different name than desired: %s != %s. simple fix? %s" % ( inFunc.__module__, funcName, newFuncName, funcType == types.FunctionType and returnFunc is None)
                return
        except AttributeError:
            pass
      
        #----------------------------        
        # UI commands with callbacks
        #----------------------------
        
        if uiWidget: #funcName in moduleCmds['windows']:
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
                    
            #print funcName, inFunc.__name__, commandFlags
                  
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
                        except: pass
                return res
        #-----------
        # Others
        #-----------
        else:
            def newFunc(*args, **kwargs):
                return apply(inFunc, args, kwargs)
            
        _addCmdDocs( inFunc, newFunc, cmdInfo )

        if rename: 
            newFunc.__name__ = rename
        else:
            newFunc.__name__ = inFunc.__name__
            
        return newFunc
    else:
        pass
        #raise "function %s is of incorrect type: %s" % (funcName, type(inFunc) )

def _addFlagCmdDocs(func,newFuncName,cmdName,flag,docstring=''):
    func.__name__ = newFuncName
    if docstring:
        func.__doc__ = docstring
    else:
        try:
            flagDocs = cmdlist[cmdName]['flags']
            docs = flagDocs[flag]
            docstring = ''
            docstring += '        - %s\n' %  docs['docstring']
            
            try:
                docstring += '        - secondary flags:\n'
                for secondaryFlag in docs['secondaryFlags']:
                     docstring += '            - %s: %s\n' % (secondaryFlag, flagDocs[secondaryFlag]['docstring'] )
            except KeyError: pass
            
            func.__doc__ = docstring
        except KeyError: print "No documentation available for %s flag of %s command" % (flag,cmdName )    
    return func

'''            
def makeCreateFlagCmd( inFunc, name, flag=None, docstring='', cmdName=None, returnFunc=None ):
    if cmdName is None:
        cmdName = inFunc.__name__
    if flag is None:
        flag = name
    
    if returnFunc:
        def f(self, **kwargs):
            kwargs[flag]=True 
            return returnFunc( inFunc( self, **kwargs ) )
    else:
        def f(self, **kwargs):
            kwargs[flag]=True 
            return inFunc( self, **kwargs )
    return _addFlagCmdDocs(f, name, cmdName, flag, docstring )
'''

def makeCreateFlagCmd( inFunc, newFuncName, flag=None, docstring='', cmdName=None, returnFunc=None ):
    #name = 'set' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = inFunc.__name__
    if flag is None:
        flag = newFuncName
    if returnFunc:
        def newfunc(*args, **kwargs): 
            if len(args)==1:
                kwargs[flag]=True
            elif len(args)==2:
                kwargs[flag]=args[1]
                args = (args[0],)  
            else:
                kwargs[flag]=args[1:]
                args = (args[0],)  
            return returnFunc(inFunc( *args, **kwargs ))
    else:
        def newfunc(*args, **kwargs): 
            if len(args)==1:
                kwargs[flag]=True
            elif len(args)==2:
                kwargs[flag]=args[1]
                args = (args[0],)
            else:
                kwargs[flag]=args[1:]
                args = (args[0],)  
            return inFunc( *args, **kwargs )
    #if moduleName:
    #    f.__module__ = moduleName             
    return _addFlagCmdDocs(newfunc, newFuncName, cmdName, flag, docstring )

def createflag( cmdName, flag ):
    """create flag decorator"""
    def create_decorator(method):
        newfunc = makeCreateFlagCmd( method, method.__name__, flag, cmdName=cmdName )
        newfunc.__module__ = method.__module__
        return newfunc
    return create_decorator
'''
def secondaryflag( cmdName, flag ):
    """query flag decorator"""
    def secondary_decorator(method):
        return makeSecondaryFlagCmd( method, method.__name__, flag, cmdName=cmdName )
    return secondary_decorator
'''

def makeQueryFlagCmd( inFunc, newFuncName, flag=None, docstring='', cmdName=None, returnFunc=None ):
    #name = 'get' + flag[0].upper() + flag[1:]
    if cmdName is None:
        cmdName = inFunc.__name__
    if flag is None:
        flag = newFuncName
    if returnFunc:
        def newfunc(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True
            return returnFunc( inFunc( self, **kwargs ) )
    else:
        def newfunc(self, **kwargs):
            kwargs['query']=True
            kwargs[flag]=True 
            return inFunc( self, **kwargs )
    return _addFlagCmdDocs(newfunc, newFuncName, cmdName, flag, docstring )

def queryflag( cmdName, flag ):
    """query flag decorator"""
    def query_decorator(method):
        newfunc = makeQueryFlagCmd( method, method.__name__, flag, cmdName=cmdName )
        newfunc.__module__ = method.__module__
        return newfunc
    return query_decorator

   
def makeEditFlagCmd( inFunc, newFuncName, flag=None, docstring='', cmdName=None):
    #name = 'set' + flag[0].upper() + flag[1:]    
    if cmdName is None:
        cmdName = inFunc.__name__
    if flag is None:
        flag = newFuncName
    def newfunc(self, val, **kwargs): 
        kwargs['edit']=True
        kwargs[flag]=val 
        try:
            return inFunc( self, **kwargs )
        except TypeError:
            kwargs.pop('edit')
            return inFunc( self, **kwargs )
            
    return _addFlagCmdDocs(newfunc, newFuncName, cmdName, flag, docstring )

def editflag( cmdName, flag ):
    """query flag decorator"""
    def edit_decorator(method):
        newfunc = makeEditFlagCmd(  method, method.__name__, flag, cmdName=cmdName )
        newfunc.__module__ = method.__module__
        return newfunc
    return edit_decorator


def add_docs( cmdName, flag ):
    """decorator"""
    def doc_decorator(method):
        newfunc = _addFlagCmdDocs(method, method.__name__, cmdName, flag )
        newfunc.__module__ = method.__module__
        return newfunc
    return doc_decorator

'''
def createFunctions( moduleName ):
    module = __import__(moduleName, globals(), locals(), [''])
    moduleShortName = moduleName.split('.')[-1]
    for funcName in moduleCmds[ moduleShortName ]:
        if not hasattr( module, funcName ):
            func = functionFactory( funcName, returnFunc=None )
            if func:
                func.__module__ = moduleName
                setattr( module, funcName, func )
'''
#generalModule = __import__(__name__, globals(), locals(), [''])

def createFunctions2( moduleName, returnFunc=None ):
    module = __import__(moduleName, globals(), locals(), [''])
    
    moduleShortName = moduleName.split('.')[-1]
    allCommands = set(moduleCmds[ moduleShortName ])

    if returnFunc is None:
         for funcName in allCommands:
             if not hasattr( module, funcName ):
                func = functionFactory( funcName, returnFunc=None )
                if func:
                    func.__module__ = moduleName
                    setattr( module, funcName, func )
    else:
        # node commands
        for funcName in allCommands.intersection(nodeCommandList):
            if not hasattr( module, funcName ):
                func = functionFactory( funcName, returnFunc=returnFunc )
                if func:
                    func.__module__ = moduleName
                    setattr( module, funcName, func )
        # regular commands
        for funcName in allCommands.difference(nodeCommandList):
            if not hasattr( module, funcName ):
                func = functionFactory( funcName, returnFunc=None )
                if func:
                    func.__module__ = moduleName
                    setattr( module, funcName, func )

def createFunctions( moduleName, returnFunc=None ):
    module = __import__(moduleName, globals(), locals(), [''])
    
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


#_api = __import__( 'pymel.api', globals(), locals(), [''])
#_gen = __import__( 'pymel.core.general', globals(), locals(), [''])
#PYNODE = None

class Holder(util.Singleton):
    def __init__(self):
        self.obj = None
    def store( self, obj ):
        print "storing", obj
        self.obj = obj
    def get(self):
        return self.obj

GenHolder = Holder()

class ApiArgUtil(object):

    def __init__(self, apiClassName, methodName, methodInfo ):
        PYNODE = GenHolder.get()
        su = _api.MScriptUtil()
        
        def setArrayFunction( type, length ):
            capType = util.capitalize( type ) 
            initFunc = getattr( su, 'as' + capType + 'Ptr')
            setFunc = getattr( su, 'set' + capType + 'Array')
            def setArray( array ):
                #print array
                if len(array) != length:
                    raise ValueError, 'Input list must contain exactly %s %ss' % ( length, type )
                arrayPtr = initFunc()
                for i, val in enumerate( array ):
                    setFunc( arrayPtr, i, val )
                #print arrayPtr
                return arrayPtr
            setArray.__name__ = 'set' + capType + 'Array'
            return setArray

        self.inCast = { 'double' : float,
                        'float'  : float,
                        'bool'   : bool,
                        'int'    : int,
                        'short'  : int,
                        'MString': unicode,
                        
                        'double3': setArrayFunction( 'double', 3),
                        'float2' : setArrayFunction( 'float', 2),
                        
                        'MVector': _api.wrappedtypes.MVector,
                        'MMatrix': _api.wrappedtypes.MMatrix,
                        'MPoint' : _api.wrappedtypes.MPoint,
                        'MColor' : _api.wrappedtypes.MColor,
                        
                        'MObject': lambda x: PYNODE(x).__apimobject__(),
                        'MDagPath': lambda x: PYNODE(x).__apimdagpath__(),
                        'MPlug'  : lambda x: PYNODE(x).__apimplug__()
                    }
    
        self.returnCast = {  'double' : float,
                        'float'  : float,
                        'bool'   : bool,
                        'int'    : int,
                        'short'  : int,
                        'MString': unicode,
                        
                        'MVector': _api.wrappedtypes.MVector,
                        'MMatrix': _api.wrappedtypes.MMatrix,
                        'MPoint' : _api.wrappedtypes.MPoint,
                        'MColor' : _api.wrappedtypes.MColor,
                        
                        'MObject': PYNODE,
                        'MDagPath': PYNODE,
                        'MPlug'  : PYNODE,
                    }
        
        self.refInit = {
                        'int'      : lambda: su.asIntPtr(),
                        'short'    : lambda: su.asShortPtr(),
                        'float'    : lambda: su.asFloatPtr(),
                        'double'   : lambda: su.asDoublePtr(),
                        'uint'     : lambda: su.asUintPtr(),
                        'bool'     : lambda: su.asBoolPtr(),
                        
                        'int2'      : lambda: su.asIntPtr(),
                        'short2'    : lambda: su.asShortPtr(),
                        'float2'    : lambda: su.asFloatPtr(),
                        'double2'   : lambda: su.asDoublePtr(),
                        'uint2'     : lambda: su.asUintPtr(),
                        'bool2'     : lambda: su.asBoolPtr(),
                        
                        'int3'      : lambda: su.asIntPtr(),
                        'short3'    : lambda: su.asShortPtr(),
                        'float3'    : lambda: su.asFloatPtr(),
                        'double3'   : lambda: su.asDoublePtr(),
                        'uint3'     : lambda: su.asUintPtr(),
                        'bool3'     : lambda: su.asBoolPtr(),
                        
                        'MVector'   : _api.MVector,
                        'MMatrix'   : _api.MMatrix,
                        'MPoint'   : _api.MPoint,
                        
                        'MObject'   : _api.MObject,
                        'MDagPathArray' : _api.MDagPathArray,
                        
                    }
        
        self.refCast = {     
                        'int'      : lambda x: su.getInt(x),
                        'short'    : lambda x: su.getShort(x),
                        'float'    : lambda x: su.getFloat(x),
                        'double'   : lambda x: su.getDouble(x),
                        'uint'     : lambda x: su.getUint(x),
                        'bool'     : lambda x: su.getBool(x),
                        
                        'int3'      : lambda x: tuple([ su.getIntArrayItem(x,0),   su.getIntArrayItem(x,1),   su.getIntArrayItem(x,2) ]),
                        'short3'    : lambda x: tuple([ su.getShortArrayItem(x,0), su.getShortArrayItem(x,1), su.getShortArrayItem(x,2) ]),
                        'float3'    : lambda x: tuple([ su.getFloatArrayItem(x,0), su.getFloatArrayItem(x,1), su.getFloatArrayItem(x,2) ]),
                        'double3'   : lambda x: tuple([ su.getDoubleArrayItem(x,0),su.getDoubleArrayItem(x,1),su.getDoubleArrayItem(x,2) ]),
                        'uint3'     : lambda x: tuple([ su.getUintArrayItem(x,0),  su.getUintArrayItem(x,1),  su.getUintArrayItem(x,2) ]),
                        'bool3'     : lambda x: tuple([ su.getBoolArrayItem(x,0),  su.getBoolArrayItem(x,1),  su.getBoolArrayItem(x,2) ]),
                        
                        'MVector'   : _api.wrappedtypes.MVector,
                        'MMatrix'   : _api.wrappedtypes.MMatrix,
                        'MPoint'    : _api.wrappedtypes.MPoint,
                        
                        'MObject'   : PYNODE,
                        'MDagPathArray' : lambda x: [ PYNODE( MDagPath(x[i]) ) for i in range( x.length() ) ],
                    }
        
        self.apiClassName = apiClassName
        self.methodName = methodName
        self.methodInfo = methodInfo


    def canBeWrapped(self):
        inArgs = self.methodInfo['inArgs']
        outArgs =  self.methodInfo['outArgs']
        #argList = methodInfo['args']
        returnType =  self.methodInfo['returnType']
        # ensure that we can properly cast all the args and return values
        try:
            if returnType is not None:
                if isinstance( returnType, tuple ):
                    assert _api.apiClassInfo.has_key(returnType[0]) and _api.apiClassInfo[returnType[0]]['enums'].has_key(returnType[1]),'%s.%s(): invalid return enum: %s' % (self.apiClassName, self.methodName, returnType)
                else:
                    assert returnType in self.returnCast, '%s.%s(): invalid return type: %s' % (self.apiClassName, self.methodName, returnType)
            
            for argname, argtype, default, direction in self.methodInfo['args'] :
                if isinstance( argtype, tuple ):
                    assert _api.apiClassInfo.has_key(argtype[0]) and _api.apiClassInfo[argtype[0]]['enums'].has_key(argtype[1]), '%s.%s(): %s: invalid enum: %s' % (self.apiClassName, self.methodName, argname, argtype)
                elif direction == 'in':
                    assert argtype in self.inCast, '%s.%s(): %s: invalid input type %s' % (self.apiClassName, self.methodName, argname, argtype)
                elif direction == 'out':
                    assert argtype in self.refInit and argtype in self.refCast, '%s.%s(): %s: invalid output type %s' % (self.apiClassName, self.methodName, argname, argtype)
                    #try:
                    #    assert argtype.type() in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
                    #except AttributeError:
                    #    assert argtype in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
        except AssertionError, msg:
            print msg
            return False
        
        print "succeeded: %s %s.%s(%s)" % ( returnType, self.apiClassName, self.methodName, ', '.join(inArgs) ) 
        return True
    
    def castEnum(self, argtype, input ):
        if isinstance( input, int):
            return input
        
        elif input[0] != 'k' or not input[1].isupper():
            input = 'k' + util.capitalize(input)
            return _api.apiClassInfo[argtype[0]]['enums'][argtype[1]].index(input)
            
    def castInput(self, argtype, input):
        # enums
        if isinstance( argtype, tuple ):
            return self.castEnum(argtype, input)

        else:
            return self.inCast[argtype]( input )        
            
    def castResult(self, result):
        returnType = self.methodInfo['returnType']
        if returnType:
            # enums
            if isinstance( returnType, tuple ):
                return self.castEnum(returnType, result)
    
            else:
                return self.returnCast[returnType]( result )  
    
    def initializeReference(self, argtype): 
        return self.refInit[argtype]()
     
    def castReferenceResult(self,argtype,outArg):
        return self.refCast[ argtype ]( outArg )
    
    def getDefaults(self):
        defaults = []
        for arg in self.methodInfo['inArgs']:
            try:
                defaults.append( self.methodInfo['defaults'][arg])
            except: pass
        return defaults
    
def interface_wrapper( doer, args=[], defaults=[] ):
    """
    A wrapper which allows factories to create functions with
    precise inputs arguments, instead of using the argument catchall:
        >>> f( *args, **kwargs ): 
        >>> ...

    :param doer: the function to be wrapped.
    :parm args: a list of strings to be used as argument names, in proper order
    :param defaults: a list of default values for the arguments. must be less than or equal
        to args in length. if less than, the last element of defaults will be paired with the last element of args,
        the second-to-last with the second-to-last and so on ( see inspect.getargspec ). Arguments
        which get a default become keyword arguments.
    """
    # TODO: ensure doer has only an *args parameter
    
    name = doer.__name__
    storageName = doer.__name__ + '_interfaced'
    g = { storageName : doer }
    kwargs=[]
    offset = len(args) - len(defaults)
    if offset < 0:
        raise TypeError, "The number of defaults cannot exceed the number of arguments"
    for i, arg in enumerate(args):
        if i >= offset:
            kwargs.append( '%s=%r' % (arg, defaults[i-offset]) )
        else:
            kwargs.append( str(arg) )

    defStr = """def %s( %s ): 
        return %s(%s)""" % (name, ','.join(kwargs), storageName, ','.join(args) )
        

    exec( defStr ) in g
    func = g[name]
    func.__doc__ = doer.__doc__
    func.__module__ = doer.__module__
    return func

    
def wrapApiMethod( apiClass, methodName, newName=None, apiObject=False ):
    #getattr( _api, apiClassName )
    
    #general = GenHolder.get()
    #_api = general.api
    #PYNODE = general.PyNode
    PYNODE = GenHolder.get()

    assert PYNODE is not None, 'Use registerPyNode prior to calling this function'
    
    apiClassName = apiClass.__name__
    try:
        # there may be more than one method signatures per method name
        methodInfoList = _api.apiClassInfo[apiClassName]['methods'][methodName]
    except KeyError:
        print "could not find method:", apiClassName, methodName
        return
    
    try:
        method = getattr( apiClass, methodName )
    except AttributeError:
        return
    
    if newName is None:
        newName = methodInfoList[0].get('pymelName',None)
            
    for methodInfo in methodInfoList:

        
        #argInfo = methodInfo['argInfo']
        inArgs = methodInfo['inArgs']
        outArgs = methodInfo['outArgs']
        #argList = methodInfo['args']
        argHelper = ApiArgUtil(apiClassName, methodName, methodInfo)
        
        if argHelper.canBeWrapped() :
            # create the function 
            def f( self, *args ):
                inCount = 0
                i = 0
                argList = []
                outTypeList = []
                outTypeIndex = []
                argInfo = methodInfo['args']
                if len(args) != len(inArgs):
                    raise TypeError, "%s() takes exactly %s arguments (%s given)" % ( methodName, len(inArgs), len(args) )
                
                for name, argtype, default, direction in argInfo :
                    if direction == 'in':
                        argList.append( argHelper.castInput( argtype, args[inCount] ) )
                        inCount +=1
                    else:
                        val = argHelper.initializeReference(argtype) 
                        argList.append( val )
                        outTypeList.append( argtype )
                        outTypeIndex.append( i )
                    i+=1
                                      
                #print argList
                if apiObject:
                    result = method( self.__apiobject__(), *argList )
                else:
                    result = method( self.__apimfn__(), *argList )
                #print "result", result
                result = argHelper.castResult(result) 
                    
                if len(outArgs):
                    if result is not None:
                        result = [result]
                    else:
                        result = []
                    
                    for outType, index in zip(outTypeList,outTypeIndex):
                        outArgVal = argList[index]
                        res = argHelper.castReferenceResult( outType, outArgVal )
                        result.append( res )
                        
                    if len(result) == 1:
                        result = result[0]
                return result
            
            if newName:
                f.__name__ = newName
            else:
                f.__name__ = methodName
            f.__doc__ = methodInfo['doc']
            
            
            defaults = argHelper.getDefaults()
                
            #print inArgs, defaults
            f = interface_wrapper( f, ['self'] + inArgs, defaults )
            
            
            return f
        
class metaNode(type) :
    """
    A metaclass for creating classes based on node type.  Methods will be added to the new classes 
    based on info parsed from the docs on their command counterparts.
    """

    def __new__(cls, classname, bases, classdict):

        #general = GenHolder.get()
        #_api = general.api
    
        nodeType = util.uncapitalize(classname)
        _api.addMayaType( nodeType )
  

        #-------------------------
        #   API Methods
        #-------------------------
        apiClass = _api.toApiFunctionSet( nodeType )
        #if nodeType == 'transform': print 'TRANSFORM', apiClass
        if apiClass:
            classdict['__apimfnclass__'] = apiClass
            print "="*60, nodeType, "="*60
            for methodName in _api.apiClassInfo[apiClass.__name__]['methods'].keys():
                method = wrapApiMethod( apiClass, methodName )
                if method:
                    #print "%s.%s() successfully created" % (apiClass.__name__, methodName )
                    classdict[methodName] = method
        #else: print "%s: NO API TYPE" % nodeType

        #-------------------------
        #   MEL Methods
        #-------------------------
#        try:
#            infoCmd = False
#            try:
#                nodeCmd = nodeTypeToNodeCommand[ nodeType ]
#            except KeyError:
#                try:
#                    nodeCmd = nodeTypeToInfoCommand[ nodeType ]
#                    infoCmd = True
#                except KeyError: 
#                    nodeCmd = nodeType
#            
#            #if nodeHierarchy.children( nodeType ):
#            #    print nodeType, nodeHierarchy.children( nodeType )
#            cmdInfo = cmdlist[nodeCmd]
#        except KeyError: # on cmdlist[nodeType]
#            pass
#        else:
#            try:    
#                cmdModule = __import__( 'pymel.core.' + cmdInfo['type'] , globals(), locals(), [''])
#                func = getattr(cmdModule, nodeCmd)
#
#            except (AttributeError, TypeError):
#                func = getattr(cmds,nodeCmd)
#            # add documentation
#            classdict['__doc__'] = 'class counterpart of function `%s`\n\n%s\n\n' % (nodeCmd, cmdInfo['description'])
#            for flag, flagInfo in cmdInfo['flags'].items():
#                #print nodeType, flag
#                 # don't create methods for query or edit, or for flags which only serve to modify other flags
#                if flag in ['query', 'edit'] or 'modified' in flagInfo:
#                    continue
#                
#                
#                if flagInfo.has_key('modes'):
#                    # flags which are not in maya docs will have not have a modes list unless they 
#                    # have passed through testNodeCmds
#                    #print classname, nodeType, flag
#                    #continue
#                    modes = flagInfo['modes']
#    
#                    # query command
#                    if 'query' in modes:
#                        methodName = 'get' + util.capitalize(flag)
#                        if methodName not in classdict:
#                            if methodName not in overrideMethods.get( bases[0].__name__ , [] ):
#                                returnFunc = None
#                                
#                                if flagInfo.get( 'resultNeedsCasting', False):
#                                    returnFunc = flagInfo['args']
#                                    if flagInfo.get( 'resultNeedsUnpacking', False):
#                                        returnFunc = lambda x: returnFunc(x[0])
#                                        
#                                elif flagInfo.get( 'resultNeedsUnpacking', False):
#                                    returnFunc = lambda x: returnFunc(x[0])
#                                
#                                classdict[methodName] = makeQueryFlagCmd( func, methodName, 
#                                    flag, docstring=flagInfo['docstring'], returnFunc=returnFunc )
#                            #else: print "%s: skipping %s" % ( classname, methodName )
#                    
#                    # edit command: 
#                    if 'edit' in modes or ( infoCmd and 'create' in modes ):
#                        # if there is a corresponding query we use the 'set' prefix. 
#                        if 'query' in modes:
#                            methodName = 'set' + util.capitalize(flag)
#                        #if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
#                        else:
#                            methodName = flag
#                            
#                        if methodName not in classdict:
#                            if methodName not in overrideMethods.get( bases[0].__name__ , [] ):
#                                classdict[methodName] = makeEditFlagCmd( func, methodName, 
#                                     flag, docstring=flagInfo['docstring'] )
                    

            
        return super(metaNode, cls).__new__(cls, classname, bases, classdict)

    
def getValidApiMethods( apiClassName, api, verbose=False ):

    validTypes = [ None, 'double', 'bool', 'int', 'MString', 'MObject' ]
    
    try:
        methods = api.apiClassInfo[apiClassName]
    except KeyError:
        return []
    
    validMethods = []
    for method, methodInfoList in methods.items():
        for methodInfo in methodInfoList:
            #print method, methodInfoList
            if not methodInfo['outArgs']:
                returnType = methodInfo['returnType']
                if returnType in validTypes:
                    count = 0
                    types = []
                    for x in methodInfo['inArgs']:
                        type = methodInfo['argInfo'][x]['type']
                        #print x, type
                        types.append( type )
                        if type in validTypes:
                            count+=1
                    if count == len( methodInfo['inArgs'] ):
                        if verbose:
                            print '    %s %s(%s)' % ( returnType, method, ','.join( types ) )
                        validMethods.append(method)
    return validMethods

def analyzeApiClass( apiTypeStr, apiTypeParentStr, api ):
    try:
        mayaType = api.ApiTypesToMayaTypes()[ apiTypeStr ].keys()
        if util.isIterable(mayaType) and len(mayaType) == 1:
            mayaType = mayaType[0]
            pymelType = PyNodeNamesToPyNodes().get( util.capitalize(mayaType) , None )
        else:
            pymelType = None
    except KeyError:
        mayaType = None
        pymelType = None
        #print "no Fn", elem.key, pymelType

    try:
        apiClass = api.ApiTypesToApiClasses()[ apiTypeStr ]
    except KeyError:
        pass
        #print "no Fn", elem.key
    else:
        if apiTypeParentStr:
            try:
                parentApiClass = api.ApiTypesToApiClasses()[elem.parent.key ]
                parentMembers = [ x[0] for x in inspect.getmembers( parentApiClass, callable ) ]
            except KeyError:
                parentMembers = []
        else:
            parentMembers = []
        
        if pymelType is None: pymelType = PyNodeNamesToPyNodes().get( apiClass.__name__[3:] , None )
        
        if pymelType:
            parentPymelType = PyNodeTypesHierarchy()[ pymelType ]
            parentPyMembers = [ x[0] for x in inspect.getmembers( parentPymelType, callable ) ]
            pyMembers = set([ x[0] for x in inspect.getmembers( pymelType, callable ) if x[0] not in parentPyMembers ])
            print apiClass.__name__, mayaType, pymelType
            allFnMembers = [ x[0] for x in inspect.getmembers( apiClass, callable ) if x[0] not in parentMembers ]
            validFnMembers = getValidApiMethods(apiClass.__name__)
            # convert from api convention to pymel convention
            origGetMethods = {}
            for i, member in enumerate(allFnMembers):
                if len(member) > 4 and member.startswith('set') and member[3].isupper():
                    # MFn api naming convention usually uses setValue(), value() convention for its set and get methods, respectively
                    # 'setSomething'  -->  'something'
                    origGetMethod = member[3].lower() + member[4:]
                    if origGetMethod in allFnMembers:
                        newGetMethod = 'get' + member[3:]
                        try:
                            idx = validFnMembers.index( origGetMethod ) 
                            validFnMembers[idx] = newGetMethod
                        except: pass
                        
                        idx = allFnMembers.index( origGetMethod ) 
                        allFnMembers[idx] = newGetMethod
                        
                        origGetMethods[ newGetMethod ] = origGetMethod
            
            validFnMembers = set(validFnMembers)
            invalidFnMembers = set(allFnMembers).difference(validFnMembers)
            
            print "    [shared]"
            for x in sorted( validFnMembers.intersection( pyMembers ) ): print '    ', x, origGetMethods.get( x, '' )
            print "    [potential shared]"
            for x in sorted( invalidFnMembers.intersection( pyMembers ) ): print '    ', x, origGetMethods.get( x, '' )          
            print "    [api]"
            for x in sorted( validFnMembers.difference( pyMembers ) ): print '    ', x, origGetMethods.get( x, '' )
            print "    [pymel]"
            for x in sorted( pyMembers.difference( allFnMembers ) ): print '    ', x
            
class PyNodeNamesToPyNodes(util.Singleton, dict):
    """ Lookup from PyNode type name as a string to PyNode type as a class"""

class PyNodesToMayaTypes(util.Singleton, dict):
    """Lookup from PyNode class to maya type"""
    
class PyNodeTypesHierarchy(util.Singleton, dict):
    """child:parent lookup of the pymel classes that derive from DependNode"""
 
def addPyNode( module, mayaType, parentMayaType ):
    
    #print "addPyNode adding %s->%s on module %s" % (mayaType, parentMayaType, module)
    # unicode is not liked by metaNode
    pyNodeTypeName = str( util.capitalize(mayaType) )
    parentPyNodeTypeName = str(util.capitalize(parentMayaType))
    
    
    if hasattr( module, pyNodeTypeName ):
        _api.addMayaType( mayaType )
        PyNodeType = getattr( module, pyNodeTypeName )
        try :
            ParentPyNode = inspect.getmro(PyNodeType)[1]
            if ParentPyNode.__name__ != parentPyNodeTypeName :
                raise RuntimeError, "Unexpected PyNode %s for Maya type %s" % (ParentPyNode, )
        except :
            ParentPyNode = getattr( module, parentPyNodeTypeName )
        #print "already exists:", pyNodeTypeName, 
    else:
        try:
            ParentPyNode = getattr( module, parentPyNodeTypeName )
        except AttributeError:
            print "error creating class %s: parent class %s not in module %s" % (pyNodeTypeName, parentMayaType, __name__)
            return      
        try:
            
            PyNodeType = metaNode(pyNodeTypeName, (ParentPyNode,), {})
        except TypeError, msg:
            # for the error: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
            print "could not create new PyNode: %s(%s): %s" % (pyNodeTypeName, ParentPyNode.__name__, msg )
            import new
            PyNodeType = new.classobj(pyNodeTypeName, (ParentPyNode,), {})
            PyNodeType.__module__ = module.__name__
            setattr( module, pyNodeTypeName, PyNodeType )
        else:
            #print "created new PyNode: %s(%s)" % (pyNodeTypeName, parentMayaType)
            PyNodeType.__module__ = module.__name__
            setattr( module, pyNodeTypeName, PyNodeType )
            
    PyNodeTypesHierarchy()[ PyNodeType ] = ParentPyNode
    PyNodesToMayaTypes()[PyNodeType] = mayaType
    PyNodeNamesToPyNodes()[pyNodeTypeName] = PyNodeType

    
    
    return PyNodeType

def removePyNode( module, mayaType ):
    pyNodeTypeName = str( util.capitalize(mayaType) )
    PyNodeType = PyNodeNamesToPyNodes().pop( pyNodeTypeName, None )
    PyNodeParentType = PyNodeTypesHierarchy().pop( PyNodeType, None )
    PyNodesToMayaTypes().pop(PyNodeType,None)
    module.__dict__.pop(pyNodeTypeName,None)
    module.api.removeMayaType( mayaType )

#: dictionary of plugins and the nodes and commands they register   
pluginData = {}
    
def pluginLoadedCallback( module ):
                
    def pluginLoadedCB(pluginName):
        print "Plugin loaded", pluginName
        commands = cmds.pluginInfo(pluginName, query=1, command=1)
        pluginData[pluginName] = {}
        
        # Commands
        if commands:
            pluginData[pluginName]['commands'] = commands
            print "adding new commands:", commands
            for funcName in commands:
                #print "adding new command:", funcName
                cmdlist[funcName] = getCmdInfoBasic( funcName )
                func = functionFactory( funcName )
                try:
                    if func:
                        setattr( module, funcName, func )
                    else:
                        print "failed to create function"
                except Exception, msg:
                    print "exception", msg
        
        # Nodes          
        mayaTypes = cmds.pluginInfo(pluginName, query=1, dependNode=1)
        #apiEnums = cmds.pluginInfo(pluginName, query=1, dependNodeId=1) 
        if mayaTypes :
            pluginData[pluginName]['dependNodes'] = mayaTypes
            print "adding new nodes:", ', '.join( mayaTypes )
            
            for mayaType in mayaTypes:
                inheritance = getInheritance( mayaType )
                
                #print "adding new node:", mayaType, apiEnum, inheritence
                # some nodes in the hierarchy for this node might not exist, so we cycle through all 
                parent = 'dependNode'
                for node in inheritance:
                    addPyNode( module, node, parent )
                    parent = node
                    
    return pluginLoadedCB

def pluginUnloadedCallback( module ):               
    def pluginUnloadedCB(pluginName):
        print "Plugin unloaded", pluginName
        try:
            data = pluginData.pop(pluginName)
        except KeyError: pass
        else:
            # Commands
            commands = data.pop('commands', [])
            print "removing commands:", ', '.join( commands )
            for command in commands:
                #print "removing command", command
                try:
                    module.__dict__.pop(command)
                except KeyError:
                    print "Failed to remove %s from module %s" % (command, module.__name__) 
                            
            # Nodes
            nodes = data.pop('dependNodes', [])
            print "removing nodes:", ', '.join( nodes )
            for node in nodes:
                removePyNode( module, node )
    return pluginUnloadedCB

global pluginLoadedCB
global pluginUnloadedCB
pluginLoadedCB = None
pluginUnloadedCB = None

def installCallbacks(module):
    
    global pluginLoadedCB
    if pluginLoadedCB is None:
        print "adding pluginLoaded callback"
        pluginLoadedCB = pluginLoadedCallback(module)
        cmds.loadPlugin( addCallback=pluginLoadedCB )
        
    else:
        print "pluginLoaded callback already exists"
    
    global pluginUnloadedCB
    if pluginUnloadedCB is None:
        print "adding pluginUnloaded callback"
        pluginUnloadedCB = pluginUnloadedCallback(module)
        #unloadPlugin has a bug which prevents it from using python objects, so we use our mel wrapper instead
        unloadCBStr = py2mel.py2melProc( pluginUnloadedCB, procName='pluginUnloadedProc' )
        cmds.unloadPlugin( addCallback=unloadCBStr )
    else:
        print "pluginUnloaded callback already exists"

    # add commands and nodes for plugins loaded prior to importing pymel
    preLoadedPlugins = cmds.pluginInfo( q=1, listPlugins=1 ) 
    if preLoadedPlugins:
        print "Updating pymel with pre-loaded plugins:", ', '.join( preLoadedPlugins )
        for plugin in preLoadedPlugins:
            pluginLoadedCB( plugin )

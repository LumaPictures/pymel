
from pymel.util.trees import *
import pymel.util as util
import pymel.mayahook as mayahook
#assert mayahook.mayaInit() 
#print "Maya up and running"
#from general import PyNode
import pymel.api as _api
import sys, os, inspect, pickle, re, types, os.path, warnings
#from networkx.tree import *
from HTMLParser import HTMLParser
from operator import itemgetter

import maya.cmds as cmds
import maya.mel as mm
import pmcmds



VERBOSE=0

#---------------------------------------------------------------
#        Mappings and Lists
#---------------------------------------------------------------

EXCLUDE_METHODS = ['type', 'className', 'create', 'name' ]

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
    'general' : 'General',
    'language' : 'Language'
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
             'script'   : 'script',
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
            data = data.replace( '\r\n', '\n' )
            self.example += data
            #self.active = False
        
    
# class MayaDocsLoc(str) :
#    """ Path to the Maya docs, cached at pymel start """
#    __metaclass__ = util.Singleton
    
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
            pass
        
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

def fixCodeExamples():
    """cycle through all examples from the maya docs, replacing maya.cmds with pymel and inserting pymel output.
    
    NOTE: this can only be run from gui mode
    WARNING: back up your preferences before running 
    
    TODO: auto backup and restore of maya prefs 
    """
    
    manipOptions = cmds.manipOptions( q=1, handleSize=1, scale=1 )
    animOptions = []
    animOptions.append( cmds.animDisplay( timeCode=True ) )
    animOptions.append( cmds.animDisplay( timeCodeOffset="02:01:25:12" ) )
    animOptions.append( cmds.animDisplay( modelUpdate="interactive" ) )
    
    openWindows = cmds.lsUI(windows=True)
    for command in sorted(cmdlist.keys()):
        info = cmdlist[command]
        try:
            example = info['example']
        except KeyError:
            pass
        else:
            if 'import pymel' in example:
                print "examples have already been fixed. to re-fix, first delete and recreate the commands cache"
                return
            
            print
            print "Starting command", command
            
            # change from cmds to pymel
            reg = re.compile(r'\bcmds\.')
            example = reg.sub( 'pm.', example )
            #example = example.replace( 'import maya.cmds as cmds', 'import pymel as pm\npm.newFile(f=1) #fresh scene' )
            
            lines = example.split('\n')
            if len(lines)==1:
                print "removing empty example for command", command
                info['example'] = None
                continue
            
            
            lines[0] = 'import pymel as pm' #     #doctest: +SKIP'
            #lines.insert(1, 'pm.newFile(f=1) #fresh scene')
            # create a fresh scene. this does not need to be in the docstring unless we plan on using it in doctests, which is probably unrealistic
            cmds.file(new=1,f=1)
            
            newlines = []
            statement = []
            
            # narrowed down the commands that cause maya to crash to these prefixes
            if re.match( '(dis)|(dyn)|(poly)', command) :
                evaluate = False
            elif command in []:
                evaluate = False
            else:
                evaluate = True
            
            # gives a little leniency for where spaces are placed in the result line
            resultReg = re.compile('# Result:\s*(.*) #$')
            try: # funky things can happen when executing maya code: some exceptions somehow occur outside the eval/exec
                for i, line in enumerate(lines):
                    res = None
                    # replace with pymel results  '# Result: 1 #'
                    m = resultReg.match(line)
                    if m:
                        if evaluate is False:
                            line = m.group(1)
                            newlines.append('    ' + line)
                    else:
                        if evaluate:
                            if line.strip().endswith(':') or line.startswith(' ') or line.startswith('\t'):
                                statement.append(line)
                            else:
                                # evaluate the compiled statement using exec, which can do multi-line if statements and so on
                                if statement:
                                    try:
                                        #print "executing", statement
                                        exec( '\n'.join(statement) )
                                        # reset statement
                                        statement = []
                                    except Exception, e:
                                        print "stopping evaluation", str(e) # of %s on line %r" % (command, line)
                                        evaluate = False
                                try:
                                    print "evaluating: %r" % line
                                    res = eval( line )
                                    #if res is not None: print "result", repr(repr(res))
                                    #else: print "no result"
                                except:
                                    #print "failed evaluating:", str(e)
                                    try:
                                        exec( line )
                                    except (Exception, TypeError), e:
                                        print "stopping evaluation", str(e) # of %s on line %r" % (command, line)
                                        evaluate = False
                                                
                        if line.startswith(' ') or line.startswith('\t'):       
                            newlines.append('    ... ' + line)
                        else:
                            newlines.append('    >>> ' + line)
                
                        if res is not None:
                            newlines.append( '    ' + repr(res) )
                        
                if evaluate:
                    print "successful evaluation!", command
                              
                example = '\n'.join( newlines )
                info['example'] = example
            except:
               print "COMPLETE AND UTTER FAILURE:", command
            
#            # cleanup opened windows
#            for ui in set(cmds.lsUI(windows=True)).difference(openWindows):
#                try: cmds.deleteUI(ui, window=True)
#                except:pass

    print "Done Fixing Examples. Writing out fixed commands cache..."
    
    # restore manipulators and anim options
    cmds.manipOptions( handleSize=manipOptions[0], scale=manipOptions[1] )
    cmds.animDisplay( e=1, timeCode=animOptions[0], timeCodeOffset=animOptions[1], modelUpdate=animOptions[2])



    short_version = mayahook.getMayaVersion(extension=False)
    newPath = os.path.join( util.moduleDir(),  'mayaCmdsList'+short_version+'.bin' )
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
        #print tag, attrs
        self.currentTag = tag
    
    def handle_data(self, data):
        print "data", data
        if self.currentTag == 'tt':
            self.depth = data.count('>')
            #print "lastDepth", self.lastDepth, "depth", self.depth
            
        elif self.currentTag == 'a':
            data = data.lstrip()

            if self.depth == 0:
                if self.tree is None:
                    #print "starting brand new tree", self.depth, data
                    self.tree = [data]
                else:
                    #print "skipping", data
                    return
                    
            elif self.depth == self.lastDepth and self.depth > 0:                
                #print "adding to current level", self.depth, data
                self.tree[ self.depth ].append( data )
                
            elif self.depth > self.lastDepth:
                #print "starting new level", self.depth, data
                self.tree.append( [data] )
                    
            elif self.depth < self.lastDepth:

                    for i in range(0, self.lastDepth-self.depth):
                        branch = self.tree.pop()
                        #print "closing level", self.lastDepth, self.depth, self.tree[-1]
                        currTree = self.tree[-1]
                        #if isinstance(currTree, list):
                        currTree.append( branch )
                        #else:
                        #    print "skipping", data
                        #    self.close()
                        #    return
                                
                    #print "adding to level", self.depth, data
                    self.tree[ self.depth ].append( data )
            else:
                return
            self.lastDepth = self.depth
            # with 2009 and the addition of the MPxNode, the hierarchy closes all the way out ( i.e. no  >'s )
            # this prevents the depth from getting set properly. as a workaround, we'll set it to 0 here,
            # then if we encounter '> >' we set the appropriate depth, otherwise it defaults to 0.
            self.depth = 0 
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

       
#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------
def testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=False ):

    dangerousCmds = ['doBlur']
    if funcName in dangerousCmds:
        return
    
    def _formatCmd( cmd, args, kwargs ):
        args = [ x.__repr__() for x in args ]
        kwargs = [ '%s=%s' % (key, val.__repr__()) for key, val in kwargs.items() ]                   
        return '%s( %s )' % ( cmd, ', '.join( args+kwargs ) )
    
    def _objectToType( result ):
        "convert a an instance or list of instances to a python type or list of types"
        if isinstance(result, list):
            return [ type(x) for x in result ]
        else:
            return type(result)
    
    _castList = [float, int, bool]
    
    def _listIsCastable(resultType):
        "ensure that all elements are the same type and that the types are castable"
        try:
            typ = resultType[0]
            trueCount = reduce( lambda x,y: x+y, [ int( x in _castList and x == typ ) for x in resultType ] )
            
            return len(resultType) == trueCount
        except IndexError:
            return False
    
    module = cmds
    
    if verbose:
        print funcName.center( 50, '=')
    
    if funcName in [ 'character', 'lattice', 'boneLattice', 'sculpt', 'wire' ]:
        if verbose:
            print "skipping"
        return cmdInfo
        
    try:
        func = getattr(module, funcName)
    except AttributeError:
        print "could not find function %s in modules %s" % (funcName, module.__name__)
        return cmdInfo
    
    # get the current list of objects in the scene so we can cleanup later, after we make nodes
    allObjsBegin = set( cmds.ls(l=1) )  
    try:
        
        # Attempt to create the node
        cmds.select(cl=1)
              
        # the arglist passed from creation to general testing
        args = []
        constrObj = None
        if nodeCmd:
            
            #------------------
            # CREATION
            #------------------
            
            # compile the args list for node creation
            if funcName.endswith( 'onstraint'):
                # special treatment for constraints because they need two objects passed to the function
                constrObj = module.polySphere()[0]
                c = module.polyCube()[0]
                # run the function
                createArgs = [constrObj,c]
            else:
                createArgs = []
                
            # run the function
            obj = func(*createArgs)
            
            if isinstance(obj, list):
                if verbose:
                    print "Return", obj
                if len(obj) == 1:
                    print "%s: args need unpacking" % funcName
                    cmdInfo['resultNeedsUnpacking'] = True
                obj = obj[-1]
                
                
            if obj is None:
                #emptyFunctions.append( funcName )
                raise ValueError, "Returned object is None"
            
            elif not cmds.objExists( obj ):
                raise ValueError, "Returned object %s is Invalid" % obj
         
            args = [obj]
                
    except (TypeError,RuntimeError, ValueError), msg:
        if verbose:
            print "failed creation:", msg
        
    else:
        
        #------------------
        # TESTING
        #------------------
            
        #(func, args, data) = cmdList[funcName]    
        #(usePyNode, baseClsName, nodeName)
        flags = cmdInfo['flags']

        hasQueryFlag = flags.has_key( 'query' )
        hasEditFlag = flags.has_key( 'edit' )
        
        for flag in sorted(flags.keys()):
            flagInfo = flags[flag]            
            if flag in ['query', 'edit']:
                continue
            
            # special case for constraints
            if constrObj and flag in ['weight']:
                flagargs = [constrObj] + args
            else:
                flagargs = args
                
            try:
                modes = flagInfo['modes']
                testModes = False
            except KeyError, msg:
                #raise KeyError, '%s: %s' % (flag, msg)
                #print flag, "Testing modes"
                flagInfo['modes'] = []
                modes = []
                testModes = True
            
            # QUERY
            val = None
            argtype = flagInfo['args']
            
            if 'query' in modes or testModes == True:
                if hasQueryFlag:
                    kwargs = {'query':True, flag:True}
                else:
                    kwargs = { flag:True }
                    
                cmd = _formatCmd(funcName, flagargs, kwargs)
                try:
                    val = func( *flagargs, **kwargs )
                    #print val
                    resultType = _objectToType(val)
                    
                    # ensure symmetry between edit and query commands:
                    # if this flag is queryable and editable, then its queried value should be symmetric to its edit arguments
                    if 'edit' in modes and argtype != resultType:
                        # there are certain patterns of asymmetry which we can safely correct:
                        # [bool] --> bool
                        if isinstance( resultType, list) and len(resultType) ==1 and resultType[0] == argtype:
                            flagInfo['resultNeedsUnpacking'] = True
                            val = val[0]
                            
                        # [int] --> bool
                        elif argtype in _castList and isinstance( resultType, list) and len(resultType) ==1 and resultType[0] in _castList:
                            flagInfo['resultNeedsUnpacking'] = True
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val[0])
                            
                        # [int, int] --> bool
                        elif argtype in _castList and isinstance( resultType, list) and _listIsCastable(resultType):
                            flagInfo['resultNeedsUnpacking'] = True
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val[0])
                            
                        # int --> bool
                        elif argtype in _castList and resultType in _castList:
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val)
                        else:
                            # no valid corrctions found
                            print cmd
                            print "\treturn mismatch"
                            print '\tresult:', val.__repr__()
                            print '\tpredicted type: ', argtype
                            print '\tactual type:    ', resultType
                            # value is no good. reset to None, so that a default will be generated for edit
                            val = None
                    
                    elif verbose:
                        print cmd
                        print "\tsucceeded"
                        print '\tresult:', val.__repr__()
                        print '\tresult type:    ', resultType
                        
                except TypeError, msg:
                    # flag is no longer supported                         
                    if str(msg).startswith( 'Invalid flag' ):
                        #if verbose:
                        print "removing flag", funcName, flag, msg
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag,None)
                        flagInfo.pop(shortname,None)
                        modes = [] # stop edit from running
                    else:
                        print cmd
                        print "\t", str(msg).rstrip('\n')
                    val = None
                    
                except RuntimeError, msg:
                    print cmd
                    print "\t", str(msg).rstrip('\n') 
                    val = None
                else:
                    # some flags are only in mel help and not in maya docs, so we don't know their
                    # supported per-flag modes.  we fill that in here
                    flagInfo['modes'].append('query')
            # EDIT
            if 'edit' in modes or testModes == True:
                
                #print "Args:", argtype
                try:
                    # we use the value returned from query above as defaults for putting back in as edit args
                    # but if the return was empty we need to produce something to test on.  
                    # NOTE: this is just a guess
                    if val is None:
                        
                        if isinstance(argtype, list):
                            val = []
                            for typ in argtype:
                                if type == unicode or isinstance(type,basestring):
                                    val.append('persp')
                                else:
                                    if 'query' in modes:
                                        val.append( typ(0) )
                                    # edit only, ensure that bool args are True
                                    else:
                                        val.append( typ(1) )
                        else:
                            if argtype == unicode or isinstance(argtype,basestring):
                                val = 'persp'
                            elif 'query' in modes:
                                val = argtype(0)
                            else:
                                # edit only, ensure that bool args are True
                                val = argtype(1)
                                  
                    kwargs = {'edit':True, flag:val}              
                    cmd = _formatCmd(funcName, args, kwargs)
                    val = func( *args, **kwargs )
                    if verbose:
                        print cmd
                        print "\tsucceeded"
                        #print '\t', val.__repr__()
                        #print '\t', argtype, type(val)
                    #print "SKIPPING %s: need arg of type %s" % (flag, flagInfo['argtype'])
                except TypeError, msg:                                                        
                    if str(msg).startswith( 'Invalid flag' ):
                        #if verbose:
                        # flag is no longer supported  
                        print "removing flag", funcName, flag, msg
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag,None)
                        flagInfo.pop(shortname,None)
                    else:
                        print cmd
                        print "\t", str(msg).rstrip('\n')
                        print "\tpredicted arg:", argtype
                        if not 'query' in modes:
                            print "\tedit only"
                except RuntimeError, msg:
                    print cmd
                    print "\t", str(msg).rstrip('\n')
                    print "\tpredicted arg:", argtype
                    if not 'query' in modes:
                        print "\tedit only"
                else:
                    flagInfo['modes'].append('edit')
    
    # cleanup
    allObjsEnd = set( cmds.ls(l=1) )
    newObjs = list(allObjsEnd.difference(  allObjsBegin ) )
    if newObjs:
        cmds.delete( newObjs ) 
    return cmdInfo

def loadCache( filePrefix, description=''):
    short_version = mayahook.getMayaVersion(extension=False)   
    newPath = os.path.join( util.moduleDir(),  filePrefix+short_version+'.bin' )
    
    if description:
        description = ' ' + description
    try :
        file = open(newPath, mode='rb')
        try :
            return pickle.load(file)
        except :
            print "Unable to load%s from '%s'" % (description,file.name)
        
        file.close()
    except :
        print "Unable to open '%s' for reading%s" % ( newPath, description )

 
def writeCache( data, filePrefix, description=''):
    print "writing cache"
    
    short_version = mayahook.getMayaVersion(extension=False)   
    newPath = os.path.join( util.moduleDir(),  filePrefix+short_version+'.bin' )

    if description:
        description = ' ' + description
    
    print "Saving%s to '%s'" % ( description, newPath )
    try :
        file = open(newPath, mode='wb')
        try :
            pickle.dump( data, file, 2)
            print "done"
        except:
            print "Unable to write%s to '%s'" % (description,file.name)
        file.close()
    except :
        print "Unable to open '%s' for writing%s" % ( newPath, description )
                   
       
def buildCachedData() :
    """Build and save to disk the list of Maya Python commands and their arguments"""
    
    # With extension can't get docs on unix 64
    # path is
    # /usr/autodesk/maya2008-x64/docs/Maya2008/en_US/Nodes/index_hierarchy.html
    # and not
    # /usr/autodesk/maya2008-x64/docs/Maya2008-x64/en_US/Nodes/index_hierarchy.html
    short_version = mayahook.getMayaVersion(extension=False)
    long_version = mayahook.getMayaVersion(extension=True)
    
    
    data = loadCache( 'mayaCmdsList', 'the list of Maya commands' )
    
    if data is not None:
        cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds = data
        nodeHierarchyTree = IndexedTree(nodeHierarchy)
    
    else: # or not isinstance(cmdlist,list):        
        cmdlist = {}
        print "Rebuilding the list of Maya commands..."
        
        nodeHierarchy = _getNodeHierarchy(long_version)
        nodeHierarchyTree = IndexedTree(nodeHierarchy)
        uiClassList = _getUICommands()
        nodeCommandList = []
        for moduleName, longname in moduleNameShortToLong.items():
            moduleNameShortToLong[moduleName] = getModuleCommandList( longname, long_version )
                        
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
                        break
                if module is None:    
                    if mm.eval('whatIs "%s"' % funcName ) == 'Run Time Command':
                        module = 'runtime'
                    else:
                        module = 'other'
 
            cmdInfo = {}
            
            if module:
                moduleCmds[module].append(funcName)
            
            if module != 'runtime':
                cmdInfo = getCmdInfo(funcName, long_version)

                if module != 'windows':
                    if funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
                        nodeCommandList.append(funcName)
                        cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=True, verbose=True  )
                    #elif module != 'context':
                    #    cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=True  )
                
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
        writeCache( (cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds), 'mayaCmdsList', 'the list of Maya commands' )
             
    return (cmdlist,nodeHierarchyTree,uiClassList,nodeCommandList,moduleCmds)


def loadApiToMelBridge():

    bridge = loadCache( 'mayaApiMelBridge', 'the api-mel bridge' )
    if bridge is not None:
        return bridge
    
    bridge = util.defaultdict(dict)
    return bridge

def saveApiToMelBridge():
    writeCache( apiToMelData, 'mayaApiMelBridge', 'the api-mel bridge' )

           
#---------------------------------------------------------------
        
cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds = buildCachedData()

apiToMelData = loadApiToMelBridge()

apiToMelMap = { 
               'mel' : util.defaultdict(list),
               'api' : util.defaultdict(list)
               }

# quick fix until we make a util.Singleton of nodeHierarchy
def NodeHierarchy() :
    return nodeHierarchy

def getUncachedCmds():
    return list( set( map( itemgetter(0), inspect.getmembers( cmds, callable ) ) ).difference( cmdlist.keys() ) )
        
def getInheritance( mayaType ):
    """Get parents as a list, starting from the node after dependNode, and ending with the mayaType itself.
    This method relies on creating the node to use with cmds.nodeType -- i would prefer a cleaner solution."""
    parent = []
    state = cmds.undoInfo( q=1, state=1)
    try:
        cmds.undoInfo( state=0)
        res = cmds.createNode( mayaType, parent=None )
        #print "created node: ", res
        parent = cmds.nodeType( res, inherited=1)
        #print "parents: ", parent
        
        # TODO: this will sometimes fail to get an inheritance when a file
        # is imported, and it requires an unloaded plugin... debug this
        if parent is None:
            util.warn("Could not find inheritance for node type '%s'" % mayaType)
            parent = []

        # createNode may also have created a transform above the returned node
        if 'dagNode' in parent:
            dagParent = cmds.listRelatives(res, parent=1)
            if dagParent is not None:
                cmds.delete(dagParent[0])
            else:
                cmds.delete(res)
        else:
            cmds.delete(res)
    finally:
        # there's a chance it failed on delete
        cmds.undoInfo( state=state)
        return parent
   
#-----------------------
# Function Factory
#-----------------------

def _addCmdDocs( func, cmdInfo=None ):
    if cmdInfo is None:
        cmdInfo = cmdlist[func.__name__]
        
    # runtime functions have no docs
    if cmdInfo['type'] == 'runtime':
        return func
        
    docstring = cmdInfo['description'] + '\n\n'

    if func.__doc__: 
        docstring += func.__doc__ + '\n\n'
        
    flagDocs = cmdInfo['flags']
    if flagDocs:
        
        docstring += 'Flags:\n'
        for flag in sorted(flagDocs.keys()):
            docs = flagDocs[flag]

            label = '    - %s (%s)' % (flag, docs['shortname'])
            docstring += label + '\n'
            
            # docstring
            try:
                doc = docs['docstring']
                if doc:
                    docstring += '        - %s\n' %  doc
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
        
    if cmdInfo.get('example',None):
        docstring += '\nExample:\n' + cmdInfo['example']
    

    
    func.__doc__ = docstring
    return func        

def _addFlagCmdDocs(func,cmdName,flag,docstring=''):
    if docstring:
        func.__doc__ = docstring
    else:
        try:
            flagDocs = cmdlist[cmdName]['flags']
            docs = flagDocs[flag]
            docstring = ''
            doc = docs['docstring']
            if doc:
                docstring += '        - %s\n' %  doc
            
            try:
                docstring += '        - secondary flags:\n'
                for secondaryFlag in docs['secondaryFlags']:
                    docstring += '            - %s: %s\n' % (secondaryFlag, flagDocs[secondaryFlag]['docstring'] )
            except KeyError: pass
            
            func.__doc__ = docstring
        except KeyError: print "No documentation available for %s flag of %s command" % (flag,cmdName )    
    return func




def _getCallbackFlags(flagDocs):
    """used parsed data and naming convention to determine which flags are callbacks"""
    commandFlags = []
    for flag, data in flagDocs.items():
        if data['args'] in ['script', callable] or 'command' in flag.lower():
            commandFlags += [flag, data['shortname']]
    return commandFlags

def getUICommandsWithCallbacks():
    cmds = []
    for funcName in moduleCmds['windows']:
        cbFlags = _getCallbackFlags(cmdlist[funcName]['flags'])
        if cbFlags:
            cmds.append( [funcName, cbFlags] )
    return cmds

def fixCallbacks(inFunc, funcName=None ):
    """ui callback functions are passed strings instead of python values. this fixes the problem and also adds an extra flag
    to all commands with callbacks called 'passSelf'.  when set to True, an instance of the ui element will be passed
    as the first argument."""
    
    if funcName is None:
        funcName = inFunc.__name__
    
    cmdInfo = cmdlist[funcName]
        
    commandFlags = _getCallbackFlags(cmdInfo['flags'])
    
    if not commandFlags:
        #commandFlags = []
        return inFunc
    
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
        
    #print funcName, inFunc.__name__, commandFlags

    # need to define a seperate var here to hold
    # the old value of newFunc, b/c 'return newFunc'
    # would be recursive
    beforeUiFunc = inFunc
    

    def newUiFunc( *args, **kwargs):
        if len(args):
            doPassSelf = kwargs.pop('passSelf', False)
        else:
            doPassSelf = False
                  
        for key in commandFlags:
            try:
                cb = kwargs[ key ]
                if callable(cb):
                    #print "fixing callback", key
                    def callback(*cb_args):
                        #print "callback args", args
                        newargs = []
                        for arg in cb_args:
                            if callbackReturnFunc:
                                arg = callbackReturnFunc(arg)
                            newargs.append(arg)
                        
                        if doPassSelf:
                            newargs = [ args[0] ] + newargs
                        newargs = tuple(newargs)
                        #print "callback newargs", newargs
                        return cb( *newargs )
                    kwargs[ key ] = callback
            except KeyError: pass
            
        return beforeUiFunc(*args, **kwargs)  
    
    if funcName:
        newUiFunc.__name__ = funcName
    else:
        newUiFunc.__name__ = inFunc.__name__
    newUiFunc.__module__ = inFunc.__module__   
    return  newUiFunc

def functionFactory( funcNameOrObject, returnFunc=None, module=None, rename=None, uiWidget=False ):
    """create a new function, apply the given returnFunc to the results (if any), 
    and add to the module given by 'moduleName'.  Use pre-parsed command documentation
    to add to __doc__ strings for the command."""

    #if module is None:
    #   module = _thisModule
    
    inFunc = None
    if isinstance( funcNameOrObject, basestring ):
        funcName = funcNameOrObject

        # make sure that we import from pmcmds, not cmds
        if module and module!=cmds:
            try:       
                inFunc = getattr(module, funcName)
            except AttributeError:
                #if funcName == 'lsThroughFilter': print "function %s not found in module %s" % ( funcName, module.__name__)
                pass
        
        if not inFunc:
            try:
                # import from pymel.mayahook.pmcmds
                inFunc = getattr(pmcmds,funcName)
                #inFunc = getattr(cmds,funcName)
                #if funcName == 'lsThroughFilter': print "function %s found in module %s: %s" % ( funcName, cmds.__name__, inFunc.__name__)
            except AttributeError:
                util.warn('Cannot find function %s' % funcNameOrObject)
                return
    else:
        funcName = funcNameOrObject.__name__
        inFunc = funcNameOrObject

    # Do some sanity checks...
    if not callable(inFunc):
        util.warn('%s not callable' % funcNameOrObject)
        return
    
    cmdInfo = cmdlist[funcName]
    funcType = type(inFunc)
    # python doesn't like unicode function names
    funcName = str(funcName)                   
    
    if funcType == types.BuiltinFunctionType:
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                util.warn("Function found in module %s has different name than desired: %s != %s. simple fix? %s" % ( inFunc.__module__, funcName, newFuncName, funcType == types.FunctionType and returnFunc is None))
        except AttributeError:
            util.warn("%s had no '__name__' attribute" % inFunc)

    # some refactoring done here - to avoid code duplication (and make things clearer),
    # we now ALWAYS do things in the following order:
        # 1. Check if we need a newFunction, or can modify existing one, and set our newFunc appropriately
        # 2. Perform operations which modify the execution of the function (ie, adding return funcs)
        # 3. Modify the function descriptors - ie, __doc__, __name__, etc
        
    # 1. Check if we need a newFunction, or can modify existing one, and set our newFunc appropriately
    if not (funcType == types.BuiltinFunctionType or rename):
        # if it's a non-builtin function and we're not renaming, we don't need to create a
        # new function - just tack docs onto existing one
        newFunc = inFunc
    else:
        # otherwise, we'll need a new function: we don't want to touch built-ins, or
        # rename an existing function, as that can screw things up... just modifying docs
        # of non-builtin should be fine, though
        def newFunc(*args, **kwargs):
            return inFunc(*args, **kwargs)
        
        # TODO: since adding returnFuncs is so common, move the code for that here, to avoid
        # an extra level of function wrapping
        
    # 2. Perform operations which modify the execution of the function (ie, adding return funcs)

    if returnFunc:
        # need to define a seperate var here to hold
        # the old value of newFunc, b/c 'return newFunc'
        # would be recursive
        
        beforeReturnFunc = newFunc
        def newFuncWithReturnFunc( *args, **kwargs):
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
                    except: pass
            return res
        newFunc = newFuncWithReturnFunc
        
    #----------------------------        
    # UI commands with callbacks
    #----------------------------
    
    if uiWidget: #funcName in moduleCmds['windows']:
 
#        # wrap ui callback commands to ensure that the correct types are returned.
#        # we don't have a list of which command-callback pairs return what type, but for many we can guess based on their name.
#        if funcName.startswith('float'):
#            callbackReturnFunc = float
#        elif funcName.startswith('int'):
#            callbackReturnFunc = int
#        elif funcName.startswith('checkBox') or funcName.startswith('radioButton'):
#            callbackReturnFunc = lambda x: x == 'true'
#        else:
#            callbackReturnFunc = None
#        
#        if callbackReturnFunc or passSelf:                
#            commandFlags = _getCallbackFlags(cmdInfo['flags'])
#        else:
#            commandFlags = []
#        
#
#         
#        #print funcName, inFunc.__name__, commandFlags
#
#        # need to define a seperate var here to hold
#        # the old value of newFunc, b/c 'return newFunc'
#        # would be recursive
#        beforeUiFunc = newFunc
#        
#        def newUiFunc( *args, **kwargs):
#            for key in commandFlags:
#                try:
#                    cb = kwargs[ key ]
#                    if callable(cb):
#                        def callback(*args):
#                            newargs = []
#                            for arg in args:
#                                arg = callbackReturnFunc(arg)
#                                newargs.append(arg)
#                            newargs = tuple(newargs)
#                            return cb( *newargs )
#                        kwargs[ key ] = callback
#                except KeyError: pass
#            
#            return beforeUiFunc(*args, **kwargs)
#        
#        newFunc = newUiFunc
        
        newFunc = fixCallbacks( newFunc, funcName )

        
    # 3. Modify the function descriptors - ie, __doc__, __name__, etc
    
    newFunc.__doc__ = inFunc.__doc__
    _addCmdDocs( newFunc, cmdInfo )

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


#def makeCallbackFlagMethod( inFunc, flag, newMethodName=None, docstring='', cmdName=None):
#
#    if cmdName is None:
#        cmdName = inFunc.__name__
#
#    inFunc = fixCallback( inFunc, cmdName, passSelf=True )
#    
#    def wrappedMelFunc(self, callback, passSelf=False): 
#        kwargs = {'edit' : True }
#        
#        if passSelf and callable(callback):
#            def newCallback(*args):
#                return callback( self, *args )
#        else:
#            newCallback = callback
#                        
#        kwargs[flag]=newCallback        
#        return inFunc( self, **kwargs )
#
#        
#    if newMethodName:
#        wrappedMelFunc.__name__ = newMethodName
#    else:
#        wrappedMelFunc.__name__ = flag
#        
#    return _addFlagCmdDocs(wrappedMelFunc, cmdName, flag, docstring )
            
            
def editflag( cmdName, flag ):
    """query flag decorator"""
    def edit_decorator(method):
        wrappedMelFunc = makeEditFlagMethod(  method, flag, method.__name__, cmdName=cmdName )
        wrappedMelFunc.__module__ = method.__module__
        return wrappedMelFunc
    return edit_decorator


def add_docs( cmdName, flag=None ):
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
                cmdInfo = cmdlist[cmdName]
                wrappedMelFunc = _addCmdDocs(func, cmdInfo )
                wrappedMelFunc.__module__ = func.__module__
            except KeyError:
                print "No documentation available %s command" % ( cmdName ) 
                wrappedMelFunc = func
            return wrappedMelFunc
    
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
    doc = {}
    su = _api.MScriptUtil()

    @staticmethod
    def _makeApiArraySetter( type, inCast ):
        def setArray( array ):
            arrayPtr = type()
            [ arrayPtr.append( inCast(x) ) for x in array ]
            return arrayPtr
        setArray.__name__ = 'set_' + type.__name__
        return setArray
        
    @staticmethod
    def _makeArraySetter( apiTypename, length, setFunc, initFunc ):
        def setArray( array ):
            if VERBOSE: print "set", array
            if len(array) != length:
                raise ValueError, 'Input list must contain exactly %s %ss' % ( length, apiTypename )
            arrayPtr = initFunc()
            for i, val in enumerate( array ):
                setFunc( arrayPtr, i, val )
            if VERBOSE: print "result", arrayPtr
            return arrayPtr
        setArray.__name__ = 'set_' + apiTypename + str(length) + 'Array'
        return setArray

    @staticmethod
    def _makeArrayGetter( apiTypename, length, getFunc ):
        def getArray( array ):
            if VERBOSE: print "get", array
            return tuple([ getFunc(array,i) for i in range(length) ] )
        getArray.__name__ = 'get_' + apiTypename + str(length) + 'Array'
        return getArray
    
    @classmethod
    def getPymelType(cls, apiType):
        """
        We need a way to map from api name to pymelName.  we start by looking up types which are registered
        and then fall back to naming convention for types that haven't been registered yet. Perhaps pre-register
        the names? """
        try:
            #print "getting %s from dict" % apiType
            return cls.types[apiType]
        except KeyError:
            try:
                # convert to pymel naming convetion  MTime -> Time,  MVector -> Vector
                #print "getting pymelName", apiType
                buf = re.split( '(?:MIt)|(?:MFn)|(?:M)', apiType)
                #print buf
                assert buf[1]
                return buf[1]
            except IndexError:
                raise

            
    @classmethod   
    def isRegistered(cls, apiTypename):
        return apiTypename in cls.types
        
    @classmethod         
    def register(cls, apiTypename, pymelType, inCast=None, outCast=None, apiArrayItemType=None):
        """
        pymelType is the type to be used internally by pymel.  apiType will be hidden from the user
        and converted to the pymel type.  
        apiTypename is the name of an apiType as a string
        if apiArrayItemType is set, it should be the api type that represents each item in the array"""

        #apiTypename = pymelType.__class__.__name__
        capType = util.capitalize( apiTypename ) 

        # register type
        cls.types[apiTypename] = pymelType.__name__
        
        # register result casting
        if outCast:
            cls.outCast[apiTypename] = outCast
        elif apiArrayItemType is not None:
            pass
        else:
            cls.outCast[apiTypename] = lambda self, x: pymelType(x)
            
        # register argument casting
        if inCast:
            cls.inCast[apiTypename] = inCast
        elif apiArrayItemType is not None:
            pass # filled out below
        else:
            cls.inCast[apiTypename] = pymelType
        
        if apiTypename in ['float', 'double', 'bool', 'int', 'short', 'long', 'uint']:
            initFunc = getattr( cls.su, 'as' + capType + 'Ptr')  # initialize: su.asFloatPtr()
            getFunc = getattr( cls.su, 'get' + capType )  # su.getFloat()
            setArrayFunc = getattr( cls.su, 'set' + capType + 'Array')  # su.setFloatArray()
            getArrayFunc = getattr( cls.su, 'get' + capType + 'ArrayItem') # su.getFloatArrayItem()
            cls.refInit[apiTypename] = initFunc
            cls.refCast[apiTypename] = getFunc
            for i in [2,3,4]:
                iapiTypename = apiTypename + str(i)
                cls.refInit[iapiTypename] = initFunc
                cls.inCast[iapiTypename]  = cls._makeArraySetter( apiTypename, i, setArrayFunc, initFunc )
                cls.refCast[iapiTypename] = cls._makeArrayGetter( apiTypename, i, getArrayFunc )
                cls.types[iapiTypename] = tuple([pymelType.__name__]*i)
        else:
            try:      
                apiType = getattr( _api, apiTypename )
            except AttributeError:
                if apiArrayItemType:
                    cls.refInit[apiTypename] = list
                    cls.inCast[apiTypename] = lambda x: [ apiArrayItemType(y) for y in x ] 
                    cls.refCast[apiTypename] = None
                    cls.outCast[apiTypename] = None

            else:
                #-- Api Array types
                if apiArrayItemType:
                    
                    cls.refInit[apiTypename] = apiType
                    cls.inCast[apiTypename] = cls._makeApiArraySetter( apiType, apiArrayItemType )
                    # this is double wrapped because of the crashes occuring with MDagPathArray. not sure if it's applicable to all arrays
                    if apiType == _api.MDagPathArray:
                        cls.refCast[apiTypename] = lambda x:       [ pymelType( apiType(x[i]) ) for i in range( x.length() ) ]
                        cls.outCast[apiTypename] = lambda self, x: [ pymelType( apiType(x[i]) ) for i in range( x.length() ) ]
                    else:
                        cls.refCast[apiTypename] = lambda x:       [ pymelType( x[i] ) for i in range( x.length() ) ]
                        cls.outCast[apiTypename] = lambda self, x: [ pymelType( x[i] ) for i in range( x.length() ) ]
                        
                #-- Api types
                else:
                    cls.refInit[apiTypename] = apiType
                    cls.refCast[apiTypename] = pymelType
                    try:
                        # automatically handle array types that correspond to this api type (e.g.  MColor and MColorArray )
                        arrayTypename = apiTypename + 'Array'
                        apiArrayType = getattr( _api, arrayTypename )
                        # e.g.  'MColorArray', MColor, api.MColor
                        ApiTypeRegister.register(arrayTypename, pymelType, apiArrayItemType=apiType)
                    except AttributeError:
                        pass



ApiTypeRegister.register('float', float)
ApiTypeRegister.register('double', float)
ApiTypeRegister.register('bool', bool)
ApiTypeRegister.register('int', int)
ApiTypeRegister.register('short', int)
ApiTypeRegister.register('uint', int)
#ApiTypeRegister.register('long', int)
ApiTypeRegister.register('MString', unicode )
ApiTypeRegister.register('MStringArray', list, apiArrayItemType=unicode )
ApiTypeRegister.register('MIntArray', int, apiArrayItemType=int)
ApiTypeRegister.register('MFloatArray', float, apiArrayItemType=float)
ApiTypeRegister.register('MDoubleArray', float, apiArrayItemType=float)

class ApiArgUtil(object):

    def __init__(self, apiClassName, methodName, methodInfo=None, methodIndex=0 ):
        """If methodInfo is None, then the methodIndex will be used to lookup the methodInfo from apiClassInfo"""
        self.apiClassName = apiClassName
        self.methodName = methodName
        if methodInfo is None:
            methodInfo = _api.apiClassInfo[apiClassName]['methods'][methodName][methodIndex]
        elif isinstance( methodInfo, int):
            methodIndex = methodInfo
            methodInfo = _api.apiClassInfo[apiClassName]['methods'][methodName][methodIndex]
        self.methodInfo = methodInfo

    @staticmethod
    def isValidEnum( enumTuple ):
        if _api.apiClassInfo.has_key(enumTuple[0]) and \
            _api.apiClassInfo[enumTuple[0]]['enums'].has_key(enumTuple[1]):
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
                
                # Output
                elif direction == 'out':
                    assert argtype in ApiTypeRegister.refInit and argtype in ApiTypeRegister.refCast, '%s.%s(): %s: invalid output type %s' % (self.apiClassName, self.methodName, argname, argtype)
                    #try:
                    #    assert argtype.type() in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
                    #except AttributeError:
                    #    assert argtype in refInit, '%s.%s(): cannot cast referece arg %s of type %s' % (apiClassName, methodName, argname, argtype)
        except AssertionError, msg:
            if VERBOSE: print msg
            return False
        
        if VERBOSE: print "%s: valid" % self.getPrototype()
        return True
    
#    def castEnum(self, argtype, input ):
#        if isinstance( input, int):
#            return input
#        
#        elif input[0] != 'k' or not input[1].isupper():
#            input = 'k' + util.capitalize(input)
#            return _api.apiClassInfo[argtype[0]]['enums'][argtype[1]].index(input)
    
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
                    print self.methodInfo['defaults'][x]
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
    
    def castInput(self, argtype, input, cls):
        # enums
        if isinstance( argtype, tuple ):
            if isinstance( input, int):
                return input
            
            apiClassName, enumName = argtype
            try:
                return _api.apiClassInfo[apiClassName]['enums'][enumName]['values'].index(input)
            except ValueError:
                try:
                    return _api.apiClassInfo[apiClassName]['pymelEnums'][enumName].index(input)
                except ValueError:
                    raise ValueError, "expected an enum of type %s.%s" % ( apiClassName, enumName )
                
        elif input is not None:
            try:
                f = ApiTypeRegister.inCast[argtype]
                if f is None:
                    return input
                return f( input )   
            except:
                if input is None:
                    # we should do a check to ensure that the default is None, but for now, just return
                    return input
                if argtype != cls.__name__:
                    raise TypeError, "Cannot cast a %s to %s" % ( type(input).__name__, argtype ) 
                return cls(input)
            
    def castResult(self, instance, result ):
        returnType = self.methodInfo['returnType']
        if returnType:
            # enums
            if isinstance( returnType, tuple ):
                #raise NotImplementedError
                apiClassName, enumName = returnType
                try:
                    # TODO : return EnumValue type
                    # convert int result into pymel string name.
                    return _api.apiClassInfo[apiClassName]['pymelEnums'][enumName][result]
                except KeyError:
                    raise ValueError, "expected an enum of type %s.%s" % ( apiClassName, enumName )
    
            else:
                try:
                    f = ApiTypeRegister.outCast[returnType]
                    if f is None:
                        return result
                    return f( instance, result )  
                except:
                    cls = instance.__class__
                    if returnType != cls.__name__:
                        raise TypeError, "Cannot cast a %s to %s" % ( type(result).__name__, returnType ) 
                    return cls(result)
                
    def initReference(self, argtype): 
        return ApiTypeRegister.refInit[argtype]()
     
    def castReferenceResult(self,argtype,outArg):
        f = ApiTypeRegister.refCast[ argtype ]
        if f is None:
            return outArg
        return f( outArg )
        
    def getDefaults(self):
        "get a list of defaults"
        defaults = []
        defaultInfo = self.methodInfo['defaults']
        inArgs = self.methodInfo['inArgs']
        nargs = len(inArgs)
        for i, arg in enumerate( inArgs ):
            if arg in defaultInfo:
                default = defaultInfo[arg]
            
            # set MSpace.Space enum to object space by default, but only if it is the last arg or the next arg has a default ( i.e. kwargs must always come after args )
            elif str(self.methodInfo['types'][arg]) == 'MSpace.Space' and \
                (   i==(nargs-1) or ( i<(nargs-1) and inArgs[i+1] in defaultInfo )  ):
                    default = _api.Enum(['MSpace', 'Space', 'kObject']) 

            else:
                continue    

            if isinstance(default, _api.Enum ):
                # convert enums from apiName to pymelName. the default will be the readable string name
                apiClassName, enumName, enumValue = default
                try:
                    enumList = _api.apiClassInfo[apiClassName]['enums'][enumName]['values']
                except KeyError:
                    print "COULD NOT FIND ENUM", default
                else:
                    index = enumList.index(enumValue)
                    default = _api.apiClassInfo[apiClassName]['pymelEnums'][enumName][index]
            defaults.append( default )
            
        return defaults
    
    def isStatic(self):
        return self.methodInfo['static']
    
def interface_wrapper( doer, args=[], defaults=[] ):
    """
    A wrapper which allows factories to create functions with
    precise inputs arguments, instead of using the argument catchall:
        >>> f( *args, **kwargs ): 
        >>> ...

    :param doer: the function to be wrapped.
    :param args: a list of strings to be used as argument names, in proper order
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

    
def wrapApiMethod( apiClass, methodName, newName=None, proxy=True, overloadIndex=None ):
    """If proxy is the True, then __apimfn__ function used to retrieve the proxy class. If None,
    then we assume that the class being wrapped inherits from the underlying api class."""
    
    #getattr( _api, apiClassName )

    apiClassName = apiClass.__name__
    try:
        # there may be more than one method signatures per method name
        methodInfoList = _api.apiClassInfo[apiClassName]['methods'][methodName]
        if overloadIndex is not None:
            methodInfoList = [ methodInfoList[overloadIndex] ] # a list with one element
        
            
            
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

        #argList = methodInfo['args']
        argHelper = ApiArgUtil(apiClassName, methodName, methodInfo)
        
        if argHelper.canBeWrapped() :
            inArgs = methodInfo['inArgs']
            outArgs = methodInfo['outArgs']
            argList = methodInfo['args']
            argInfo = methodInfo['argInfo']
                    
            # create the function 
            def wrappedApiFunc( self, *args ):

                newargs = []
                outTypeList = []
                #outTypeIndex = []

                if len(args) != len(inArgs):
                    raise TypeError, "%s() takes exactly %s arguments (%s given)" % ( methodName, len(inArgs), len(args) )
                #print args, argInfo
                inCount = 0
                totalCount = 0
                for name, argtype, direction in argList :
                    if direction == 'in':
                        newargs.append( argHelper.castInput( argtype, args[inCount], self.__class__ ) )
                        inCount +=1
                    else:
                        val = argHelper.initReference(argtype) 
                        newargs.append( val )
                        outTypeList.append( (argtype, totalCount) )
                        #outTypeIndex.append( totalCount )
                    totalCount+=1
      
                #print "%s.%s: arglist %s" % ( apiClassName, methodName, newargs)
                
                if argHelper.isStatic():
                    result = method( *newargs )
                else:
                    try:
                        if proxy:
                            result = method( self.__apimfn__(), *newargs )
                        else:
                            result = method( self, *newargs )
                    except RuntimeError:
                        print newargs
                        raise
                #print "%s.%s: result (pre) %s %s" % ( apiClassName, methodName, result, type(result) )
                
                result = argHelper.castResult( self, result ) 
                
                #print methodName, "result (post)", result
                 
                if len(outArgs):
                    if result is not None:
                        result = [result]
                    else:
                        result = []
                    
                    for outType, index in outTypeList:
                        outArgVal = newargs[index]
                        res = argHelper.castReferenceResult( outType, outArgVal )
                        result.append( res )
                        
                    if len(result) == 1:
                        result = result[0]
                return result
            
            if newName:
                wrappedApiFunc.__name__ = newName
            else:
                wrappedApiFunc.__name__ = methodName
            
            def formatDocstring(type):
                # convert
                # "['one', 'two', 'three', ['1', '2', '3']]"
                # to
                # "[`one`, `two`, `three`, [`1`, `2`, `3`]]"
                
                # Enums
                # this is a little convoluted: we only want api.conversion.Enum classes here, but since we can't
                # import api directly, we have to do a string name comparison
                if type.__class__.__name__ == 'Enum':
                    try:
                        type = type.pymelName()
                    except:
                        try:
                            type = type.pymelName( ApiTypeRegister.getPymelType( type[0] ) )
                        except:
                            print "Could not determine pymel name for", type
                            pass

                return repr(type).replace("'", "`")
            
            # Docstrings
            docstring = methodInfo['doc']
            S = '    '
            if len(inArgs):
                docstring += '\n\n:Parameters:\n'
                for name in inArgs :
                    info = argInfo[name]
                    type = info['type']
                    type = ApiTypeRegister.types.get(type,type)
                    type = formatDocstring(type)
                    
                    docstring += S + '%s : %s\n' % (name, type )
                    docstring += S*2 + '%s\n' % (info['doc'])  
                    

                    
            # Results doc strings
            results = []
            returnType = methodInfo['returnType']
            if returnType: 
                rtype = ApiTypeRegister.types.get(returnType, returnType)
                results.append( rtype )
            for argname in outArgs:
                rtype = argInfo[argname]['type']
                rtype = ApiTypeRegister.types.get(rtype,rtype)
                results.append( rtype )
            if len(results) == 1:
                results = results[0]
            if results:
                docstring += '\n\n:rtype: %s\n' %  formatDocstring(results)
            
            docstring += '\nDerived from api method `%s.%s.%s`\n' % (apiClass.__module__, apiClassName, methodName) 
            
            wrappedApiFunc.__doc__ = docstring
            

                
            defaults = argHelper.getDefaults()
                
            #print inArgs, defaults
            if defaults and VERBOSE: print "defaults", defaults
            wrappedApiFunc = interface_wrapper( wrappedApiFunc, ['self'] + inArgs, defaults )
            
            if argHelper.isStatic():
                wrappedApiFunc = classmethod(wrappedApiFunc)
                
            return wrappedApiFunc


class MetaMayaTypeWrapper(util.metaReadOnlyAttr) :
    """ A metaclass to wrap Maya api types, with support for class constants """ 

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
          
    def __new__(mcl, classname, bases, classdict):
        """ Create a new class of metaClassConstants type """
        
        if VERBOSE: print mcl, classname, bases, classdict
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
            
            if not proxy and apicls not in bases:
                #print "ADDING BASE",classdict['apicls']
                bases = bases + (classdict['apicls'],)
            try:
                if VERBOSE: print "="*40, classname, apicls, "="*40
                classInfo = _api.apiClassInfo[apicls.__name__]
            except KeyError:
                print "No api information for api class %s" % ( apicls.__name__ )
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
                
                #if VERBOSE : print "Methods info", classInfo['methods']        
                # Class Methods
                for methodName, info in classInfo['methods'].items(): 
                    # don't rewrap if already herited from a base class that is not the apicls
                    if VERBOSE : print "Checking method %s" % (methodName)
                    #TODO : check pymelName
                    try:
                        pymelName = info[0]['pymelName']
                        removeAttrs.append(methodName)
                    except KeyError:
                        pymelName = methodName
                    
                    # can't use try accept, because it's a defaultdict
                    if apiToMelData.has_key( (classname,pymelName) ):
                        #apiToMelMap['api'][classname].append( pymelName )
                        data = apiToMelData[(classname,pymelName)]
                        nameType = data['useName']
                        if nameType == 'API':
                            pass
                        elif nameType == 'MEL':
                            pymelName = data['melName']
                        else:
                            pymelName = nameType
                        
                        
                        overloadIndex = data.get( 'overloadIndex', None )
                    else:
                        # set defaults
                        data = { 'enabled' : pymelName not in EXCLUDE_METHODS }
                        apiToMelData[(classname,pymelName)] = data
                        overloadIndex = None
                    
                    assert isinstance( pymelName, str ), "%s.%s: %r is not a valid name" % ( classname, methodName, pymelName)
                       
                    if pymelName not in herited:
                        if data['enabled']:                        
                            if pymelName not in classdict:
                                if VERBOSE : print "Doing an auto wrap on %s for %s: proxy=%r" % (pymelName, methodName, proxy)
                                method = wrapApiMethod( apicls, methodName, newName=pymelName, proxy=proxy, overloadIndex=overloadIndex )
                                if method:
                                    if VERBOSE : print "%s.%s() successfully created" % (apicls.__name__, pymelName )
                                    classdict[pymelName] = method
                            elif VERBOSE: print "%s.%s() skipping" % (apicls.__name__, methodName )
                        elif VERBOSE : print "Method %s has been manually disabled, skipping" % (methodName) 
                    elif VERBOSE : print "Method %s already herited from %s, skipping" % (methodName, herited[methodName])    
                
                if 'pymelEnums' in classInfo:
                    # Enumerators   
                    for enumName, enumList in classInfo['pymelEnums'].items():
                        if VERBOSE: print "adding enum %s to class %s" % ( enumName, classname )
                        #enum = util.namedtuple( enumName, enumList )
                        #classdict[enumName] = enum( *range(len(enumList)) )
                        # group into (key, doc) pairs
                        enumKeyDocPairs = [ (k,classInfo['enums'][enumName]['valueDocs'][k] ) for k in enumList ]
                        enum = util.Enum( *enumKeyDocPairs )
                        classdict[enumName] = enum
 
        
            if not proxy:
                if removeAttrs:
                    if VERBOSE: print classname, "removing attributes", removeAttrs               
                def __getattribute__(self, name): 
                    #print name        
                    if name in removeAttrs and name not in EXCLUDE_METHODS: # tmp fix
                        #print "raising error"
                        raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'" 
                    #print "getting from", bases[0]
                    return bases[0].__getattribute__(self, name)
                    
                classdict['__getattribute__'] = __getattribute__
        
        # create the new class   
        newcls = super(MetaMayaTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)
        
        # shortcut for ensuring that our class constants are the same type as the class we are creating
        def makeClassConstant(attr):
            try:
                # return MetaMayaTypeWrapper.ClassConstant(newcls(attr))
                return MetaMayaTypeWrapper.ClassConstant(attr)
            except Exception, e:
                util.warn( "Failed creating %s class constant (%s): %s" % (classname, attr, e) )
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
                for cls in mro :
                    if isinstance(cls, MetaMayaTypeWrapper) :
                        for name, attr in cls.__dict__.iteritems() :
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

class _MetaMayaCommandWrapper(MetaMayaTypeWrapper):
    """
    A metaclass for creating classes based on a maya command.
    
    Not intended to be used directly; instead, use the descendants: MetaMayaNodeWrapper, MetaMayaUIWrapper
    """

    _classDictKeyForMelCmd = None
    
    def __new__(mcl, classname, bases, classdict):
        if VERBOSE: print mcl, classname, bases, classdict

        newcls = super(_MetaMayaCommandWrapper, mcl).__new__(mcl, classname, bases, classdict)
        
        #-------------------------
        #   MEL Methods
        #-------------------------
        melCmdName, infoCmd = mcl.getMelCmd(classdict)

        
        classdict = {}
        try:
            cmdInfo = cmdlist[melCmdName]
        except KeyError:
            if VERBOSE: print "No MEL command info available for %s" % melCmdName
        else:
            try:    
                cmdModule = __import__( 'pymel.core.' + cmdInfo['type'] , globals(), locals(), [''])
                func = getattr(cmdModule, melCmdName)
            except (AttributeError, TypeError):
                func = getattr(pmcmds,melCmdName)

            if VERBOSE: print "Generating methods for %s" % melCmdName
            # add documentation
            classdoc = 'class counterpart of mel function `%s`\n\n%s\n\n' % (melCmdName, cmdInfo['description'])
            classdict['__doc__'] = classdoc
            classdict['__melcmd__'] = staticmethod(func)
            
            
            
            filterAttrs = ['name']+classdict.keys()
            filterAttrs += overrideMethods.get( bases[0].__name__ , [] )
            #filterAttrs += newcls.__dict__.keys()
            
            for flag, flagInfo in cmdInfo['flags'].items():
                #print nodeType, flag
                 # don't create methods for query or edit, or for flags which only serve to modify other flags
                if flag in ['query', 'edit'] or 'modified' in flagInfo:
                    continue
                
                
                if flagInfo.has_key('modes'):
                    # flags which are not in maya docs will have not have a modes list unless they 
                    # have passed through testNodeCmds
                    #print classname, nodeType, flag
                    #continue
                    modes = flagInfo['modes']
    
                    # query command
                    if 'query' in modes:
                        methodName = 'get' + util.capitalize(flag)
                        apiToMelMap['mel'][classname].append( methodName )
                        
                        if methodName not in filterAttrs and not hasattr(newcls, methodName):
                            if not apiToMelData.has_key((classname,methodName)) or not apiToMelData[(classname,methodName)]['enabled']:
                                returnFunc = None
                                
                                if flagInfo.get( 'resultNeedsCasting', False):
                                    returnFunc = flagInfo['args']
                                    if flagInfo.get( 'resultNeedsUnpacking', False):
                                        returnFunc = lambda x: returnFunc(x[0])
                                        
                                elif flagInfo.get( 'resultNeedsUnpacking', False):
                                    returnFunc = lambda x: returnFunc(x[0])
                                
                                
                                wrappedMelFunc = makeQueryFlagMethod( func, flag, methodName, 
                                    docstring=flagInfo['docstring'], returnFunc=returnFunc )
                                
                                if VERBOSE: print "adding mel derived method %s.%s()" % (classname, methodName)
                                classdict[methodName] = wrappedMelFunc
                                #setattr( newcls, methodName, wrappedMelFunc )
                            elif VERBOSE:  print "skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)
                        elif VERBOSE:  print "skipping mel derived method %s.%s(): already exists" % (classname, methodName)
                    # edit command: 
                    if 'edit' in modes or ( infoCmd and 'create' in modes ):
                        # if there is a corresponding query we use the 'set' prefix. 
                        if 'query' in modes:
                            methodName = 'set' + util.capitalize(flag)
                        #if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
                        else:
                            methodName = flag
                        
                        apiToMelMap['mel'][classname].append( methodName )
                           
                        if methodName not in filterAttrs and not hasattr(newcls, methodName):
                        #if not hasattr( newcls, methodName ) :
                            if not apiToMelData.has_key((classname,methodName)) or not apiToMelData[(classname,methodName)]['enabled']:
                                fixedFunc = fixCallbacks( func, melCmdName )
                                
                                wrappedMelFunc = makeEditFlagMethod( fixedFunc, flag, methodName, 
                                                                     docstring=flagInfo['docstring'] )
                                if VERBOSE: print "adding mel derived method %s.%s()" % (classname, methodName)
                                classdict[methodName] = wrappedMelFunc
                                #setattr( newcls, methodName, wrappedMelFunc )
                            elif VERBOSE:  print "skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)
                        elif VERBOSE: print "skipping mel derived method %s.%s(): already exists" % (classname, methodName)
        
        for name, attr in classdict.iteritems() :
            type.__setattr__(newcls, name, attr) 
                                
        return newcls
        
    @classmethod
    def getMelCmd(mcl, classdict):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.
        
        Intended to be overridden in derived metaclasses.
        """
        return util.uncapitalize(classname), False
    
      
class MetaMayaNodeWrapper(_MetaMayaCommandWrapper) :
    """
    A metaclass for creating classes based on node type.  Methods will be added to the new classes 
    based on info parsed from the docs on their command counterparts.
    """

    def __new__(mcl, classname, bases, classdict):
        # If the class explicitly gives it's mel node name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        if VERBOSE: print mcl, classname, bases, classdict
        nodeType = classdict.setdefault('__melnode__', util.uncapitalize(classname))
        _api.addMayaType( nodeType )
        apicls = _api.toApiFunctionSet( nodeType )
        if apicls is not None:
            classdict['__apicls__'] = apicls
        #print "="*40, classname, apicls, "="*40
        
        return super(MetaMayaNodeWrapper, mcl).__new__(mcl, classname, bases, classdict)
        
    @classmethod
    def getMelCmd(mcl, classdict):
        """
        Retrieves the name of the mel command for the node that the generated class wraps,
        and whether it is an info command.
        
        Derives the command name from the mel node name - so '__melnode__' must already be set
        in classdict.
        """
        nodeType = classdict['__melnode__']
        infoCmd = False
        try:
            nodeCmd = nodeTypeToNodeCommand[ nodeType ]
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

    def __new__(mcl, classname, bases, classdict):
        # If the class explicitly gives it's mel ui command name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        uiType= classdict.setdefault('__melui__', util.uncapitalize(classname))
        
       # TODO: implement a option at the cmdlist level that triggers listForNone 
       # TODO: create labelArray for *Grp ui elements, which passes to the correct arg ( labelArray3, labelArray4, etc ) based on length of passed array
        
        
        if 'Layout' in classname:
            def clear(self):
                children = self.getChildArray()
                if children:
                    for child in self.getChildArray():
                        pmcmds.deleteUI(child)
            classdict['clear'] = clear
            
        return super(MetaMayaUIWrapper, mcl).__new__(mcl, classname, bases, classdict)
    
    @classmethod
    def getMelCmd(mcl, classdict):
        return classdict['__melui__'], False
        
    
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

def readClassAnalysis( filename ):
    f = open(filename)
    info = {}
    currentClass = None
    currentSection = None
    for line in f.readlines():
        buf = line.split()
        if buf[0] == 'CLASS':
            currentClass = buf[1]
            info[currentClass] = {}
        elif buf[0].startswith('['):
            if currentSection in ['shared_leaf', 'api', 'pymel']:
                currentSection = buf.strip('[]')
                info[currentClass][currentSection] = {}
        else:
            n = len(buf)
            if n==2:
                info[currentClass][currentSection][buf[0]] = buf[1]
            elif n==1:
                pass
                #info[currentClass][currentSection][buf[0]] = None
            else:
                pass
    f.close()
    print info
    return info

def fixClassAnalysis( filename ):
    f = open(filename)
    info = {}
    currentClass = None
    currentSection = None
    lines = f.readlines()
    for i, line in enumerate(lines):
        buf = line.split()
        if buf[0] == 'CLASS':
            currentClass = buf[1]
            info[currentClass] = {}
        elif buf[0].startswith('['):
            if currentSection in ['shared_leaf', 'api', 'pymel']:
                currentSection = buf.strip('[]')
                info[currentClass][currentSection] = {}
        else:
            isAutoNamed, nativeName, pymelName, failedAutoName = re.match( '([+])?\s+([a-zA-Z0-9]+)(?:\s([a-zA-Z0-9]+))?(?:\s([a-zA-Z0-9]+))?', line ).groups()
            if isAutoNamed and pymelName is None:
                pymelName = nativeName
            n = len(buf)
            
            if n==2:
                info[currentClass][currentSection][buf[0]] = buf[1]
            elif n==1:
                pass
                #info[currentClass][currentSection][buf[0]] = None
            else:
                pass
    f.close()
    print info
    return info

def analyzeApiClass( apiTypeStr ):
    try:
        mayaType = _api.ApiTypesToMayaTypes()[ apiTypeStr ].keys()
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
        apiClass = _api.ApiTypesToApiClasses()[ apiTypeStr ]
    except KeyError:
        
        print "no Fn", apiTypeStr
        return
    
    apiClassName = apiClass.__name__
    parentApiClass = inspect.getmro( apiClass )[1]
     
    print "CLASS", apiClassName, mayaType

    # get all pymelName lookups for this class and its bases
    pymelMethodNames = {}
    for cls in inspect.getmro( apiClass ):
        try:
            pymelMethodNames.update( _api.apiClassInfo[cls.__name__]['pymelMethods'] )
        except KeyError: pass
    reversePymelNames = dict( (v, k) for k,v in pymelMethodNames.items() ) 
    
    allApiMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( apiClass, callable )  ]) 
    parentApiMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( parentApiClass, callable ) ])
    apiMembers = allApiMembers.difference( parentApiMembers )
    
        
#    
#    else:
#        if apiTypeParentStr:
#            try:
#                parentApiClass = api.ApiTypesToApiClasses()[elem.parent.key ]
#                parentMembers = [ x[0] for x in inspect.getmembers( parentApiClass, callable ) ]
#            except KeyError:
#                parentMembers = []
#        else:
#            parentMembers = []
#        
#        if pymelType is None: pymelType = PyNodeNamesToPyNodes().get( apiClass.__name__[3:] , None )
#        
#        if pymelType:
#            parentPymelType = PyNodeTypesHierarchy()[ pymelType ]
#            parentPyMembers = [ x[0] for x in inspect.getmembers( parentPymelType, callable ) ]
#            pyMembers = set([ x[0] for x in inspect.getmembers( pymelType, callable ) if x[0] not in parentPyMembers and not x[0].startswith('_') ])
#            
#            print "CLASS", apiClass.__name__, mayaType
#            parentApiClass = inspect.getmro( apiClass )[1]
#            #print parentApiClass
#            
#            pymelMethodNames = {}
#            # get all pymelName lookups for this class and its bases
#            for cls in inspect.getmro( apiClass ):
#                try:
#                    pymelMethodNames.update( _api.apiClassInfo[cls.__name__]['pymelMethods'] )
#                except KeyError: pass
#                
#            allFnMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( apiClass, callable )  ])
#            
#            parentFnMembers = set([ pymelMethodNames.get(x[0],x[0]) for x in inspect.getmembers( parentApiClass, callable ) ])
#            fnMembers = allFnMembers.difference( parentFnMembers )
#
#            reversePymelNames = dict( (v, k) for k,v in pymelMethodNames.items() )
#            
#            sharedCurrent = fnMembers.intersection( pyMembers )
#            sharedOnAll = allFnMembers.intersection( pyMembers )
#            sharedOnOther = allFnMembers.intersection( pyMembers.difference( sharedCurrent) )
##            print "    [shared_leaf]"
##            for x in sorted( sharedCurrent ): 
##                if x in reversePymelNames: print '    ', reversePymelNames[x], x 
##                else: print '    ', x
#                
##            print "    [shared_all]"
##            for x in sorted( sharedOnOther ): 
##                if x in reversePymelNames: print '    ', reversePymelNames[x], x 
##                else: print '    ', x
#            
#            print "    [api]"
#            for x in sorted( fnMembers ): 
#                if x in sharedCurrent:
#                    prefix = '+   '
##                elif x in sharedOnOther:
##                    prefix = '-   '
#                else:
#                    prefix = '    '
#                if x in reversePymelNames: print prefix, reversePymelNames[x], x 
#                else: print prefix, x
#            
#            print "    [pymel]"
#            for x in sorted( pyMembers.difference( allFnMembers ) ): print '    ', x
            
class PyNodeNamesToPyNodes(dict):
    """ Lookup from PyNode type name as a string to PyNode type as a class"""
    __metaclass__ = util.Singleton

class PyNodesToMayaTypes(dict):
    """Lookup from PyNode class to maya type"""
    __metaclass__ = util.Singleton
    
class ApiEnumsToPyComponents(dict):
    """Lookup from Api Enums to Pymel Component Classes"""
    __metaclass__ = util.Singleton
    
class PyNodeTypesHierarchy(dict):
    """child:parent lookup of the pymel classes that derive from DependNode"""
    __metaclass__ = util.Singleton
    
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
            PyNodeType = MetaMayaNodeWrapper(pyNodeTypeName, (ParentPyNode,), {'__melnode__':mayaType})
        except TypeError, msg:
            # for the error: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
            if VERBOSE: print "could not create new PyNode: %s(%s): %s" % (pyNodeTypeName, ParentPyNode.__name__, msg )
            import new
            PyNodeType = new.classobj(pyNodeTypeName, (ParentPyNode,), {})
            PyNodeType.__module__ = module.__name__
            setattr( module, pyNodeTypeName, PyNodeType )
        else:
            if VERBOSE: print "created new PyNode: %s(%s)" % (pyNodeTypeName, parentMayaType)
            PyNodeType.__module__ = module.__name__
            setattr( module, pyNodeTypeName, PyNodeType )
           
    PyNodeTypesHierarchy()[ PyNodeType ] = ParentPyNode
    PyNodesToMayaTypes()[PyNodeType] = mayaType
    if VERBOSE:
        print "adding %s for %s" % ( PyNodeType, pyNodeTypeName )
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
            print "adding new commands:", ', '.join(commands)
            for funcName in commands:
                #print "adding new command:", funcName
                cmdlist[funcName] = getCmdInfoBasic( funcName )
                pmcmds.addWrappedCmd(funcName)
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
                #print mayaType, inheritance
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
                    pmcmds.removeWrappedCmd(command)
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
    import pymel.tools.py2mel as py2mel
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
#        unloadCBStr = py2mel.py2melProc( pluginUnloadedCB, procName='pluginUnloadedProc' )
#        cmds.unloadPlugin( addCallback=unloadCBStr )
    else:
        print "pluginUnloaded callback already exists"

    # add commands and nodes for plugins loaded prior to importing pymel
    preLoadedPlugins = cmds.pluginInfo( q=1, listPlugins=1 ) 
    if preLoadedPlugins:
        print "Updating pymel with pre-loaded plugins:", ', '.join( preLoadedPlugins )
        for plugin in preLoadedPlugins:
            pluginLoadedCB( plugin )

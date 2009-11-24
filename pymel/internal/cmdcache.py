import os, re, inspect, keyword
import maya.cmds as cmds
import maya.mel as mm
import pymel.util as util
import pymel.versions as versions
import plogging
import pymel.mayautils as mayautils
import startup
_logger = plogging.getLogger(__name__)

__all__ = [ 'cmdlist', 'nodeHierarchy', 'uiClassList', 'nodeCommandList', 'moduleCmds' ]

moduleNameShortToLong = {
    'modeling'   : 'Modeling',
    'rendering'  : 'Rendering',
    'effects'    : 'Effects',
    'animation'  : 'Animation',
    'windows'    : 'Windows',
    'system'     : 'System',
    'general'    : 'General',
    'language'   : 'Language'
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
               ( 'namespace',  None,['reference', 'exportAsReference', 'namespace'] ),
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
             ),
    'joint' : ( ( 'absolute',     True, ['position'] ),
                ( 'relative',     True, ['position'] ) )
}



UI_COMMANDS ="""attrColorSliderGrp        attrControlGrp           
                attrEnumOptionMenu        attrEnumOptionMenuGrp    
                attrFieldGrp              attrFieldSliderGrp       
                attrNavigationControlGrp  attributeMenu            
                colorIndexSliderGrp       colorSliderButtonGrp     
                colorSliderGrp            columnLayout             
                colorEditor               floatField               
                floatFieldGrp             floatScrollBar           
                floatSlider               floatSlider2             
                floatSliderButtonGrp      floatSliderGrp           
                frameLayout               iconTextButton           
                iconTextCheckBox          iconTextRadioButton      
                iconTextRadioCollection   iconTextScrollList       
                iconTextStaticLabel       intField                 
                intFieldGrp               intScrollBar             
                intSlider                 intSliderGrp             
                paneLayout                panel                    
                radioButton               radioButtonGrp           
                radioCollection           radioMenuItemCollection  
                symbolButton              symbolCheckBox           
                textCurves                textField                
                textFieldButtonGrp        textFieldGrp             
                text                      textScrollList           
                toolButton                toolCollection           
                window                    blendShapeEditor         
                blendShapePanel           button                   
                checkBox                  checkBoxGrp              
                confirmDialog             fontDialog               
                formLayout                menu                     
                menuBarLayout             menuEditor               
                menuItem                  menuSet                  
                promptDialog              scrollField              
                scrollLayout              scriptedPanel            
                scriptedPanelType         shelfButton              
                shelfLayout               shelfTabLayout           
                tabLayout                 outlinerEditor           
                optionMenu                outlinerPanel            
                optionMenuGrp             animCurveEditor          
                animDisplay               separator                
                visor                     layout                   
                layoutDialog              layerButton              
                hyperGraph                hyperPanel               
                hyperShade                rowColumnLayout          
                rowLayout                 renderLayerButton        
                renderWindowEditor        glRenderEditor           
                scriptTable               keyframeStats            
                keyframeOutliner          canvas                   
                channelBox                gradientControl          
                gradientControlNoAttr     gridLayout               
                messageLine               popupMenu                
                modelEditor               modelPanel               
                helpLine                  hardwareRenderPanel      
                image                     nodeIconButton           
                commandLine               progressBar              
                defaultLightListCheckBox  exclusiveLightCheckBox   
                shellField                clipSchedulerOutliner    
                clipEditor                deviceEditor             
                devicePanel               dynRelEdPanel            
                dynRelEditor              dynPaintEditor           
                nameField                 cmdScrollFieldExecuter   
                cmdScrollFieldReporter    cmdShell                 
                nameField                 palettePort """.split()
    
#: creation commands whose names do not match the type of node they return require this dict
#: to resolve which command the class should wrap 
nodeTypeToNodeCommand = {
    #'failed'            : 'clip',
    #'failed'            : 'clipSchedule',
    'airField'          : 'air',
    'dragField'         : 'drag',
    'emitter'           : 'emitter',
    'turbulenceField'   : 'turbulence',
    #'failed' : 'effector',
    'volumeAxisField'   : 'volumeAxis',
    'uniformField'      : 'uniform',
    'gravityField'      : 'gravity',
    #'failed'            : 'event',
    #'failed'            : 'pointCurveConstraint',
    #'failed'            : 'deformer',
    #'failed'            : 'constrain',
    'locator'           : 'spaceLocator',
    'vortexField'       : 'vortex',
    'makeNurbTorus'     : 'torus',
    'makeNurbCone'      : 'cone',
    'makeNurbCylinder'  : 'cylinder',
    'nurbsCurve'        : 'curve', # returns a single transform, but creates a nurbsCurve
    'makeNurbSphere'    : 'sphere',
    'makeNurbCircle'    : 'circle',
    'makeNurbPlane'     : 'nurbsPlane',
    'makeNurbsSquare'   : 'nurbsSquare',
    'makeNurbCube'      : 'nurbsCube',
    'skinPercent'       : 'skinCluster',
    'file'              : None # prevent File node from using cmds.file
}


cmdlistOverrides = {}
#util.setCascadingDictItem( cmdlistOverrides, ( 'optionMenu', 'shortFlags', 'sl', 'modes' ), ['create', 'query', 'edit'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'optionMenu', 'flags', 'select', 'modes' ),  ['create', 'query', 'edit'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'ikHandle', 'flags', 'jointList', 'modes' ), ['query'] )
#util.setCascadingDictItem( cmdlistOverrides, ( 'ikHandle', 'shortFlags', 'jl', 'modes' ),   ['query'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'keyframe', 'flags', 'index', 'args' ), 'timeRange' ) # make sure this is a time range so it gets proper slice syntax


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
        #_logger.debug(synopsis)
        if lines:
            lines.pop(0) # 'Flags'
            #_logger.debug(lines)
            
            for line in lines:
                line = line.replace( '(Query Arg Mandatory)', '' )
                line = line.replace( '(Query Arg Optional)', '' )
                tokens = line.split()
                
                try:
                    tokens.remove('(multi-use)')
                except:
                    pass
                #_logger.debug(tokens)
                if len(tokens) > 1 and tokens[0].startswith('-'):
                    
                    
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

                    
                    if longname in keyword.kwlist:                       
                        removedFlags[ longname ] = shortname 
                        longname = shortname
                    elif shortname in keyword.kwlist:
                        removedFlags[ shortname ] = longname 
                        shortname = longname
                    #sometimes the longname is empty, so we'll use the shortname for both
                    elif longname == '':
                        longname = shortname
                        
                    flags[longname] = { 'longname' : longname, 'shortname' : shortname, 'args' : args, 'numArgs' : numArgs, 'docstring' : '' }
                    shortFlags[shortname] = longname
        
    #except:
    #    pass
        #_logger.debug("could not retrieve command info for", command)
    res = { 'flags': flags, 'shortFlags': shortFlags, 'description' : '', 'example': '', 'type' : 'other' }
    if removedFlags:
        res['removedFlags'] = removedFlags 
    return res

def getCmdInfo( command, version='8.5', python=True ):
    """Since many maya Python commands are builtins we can't get use getargspec on them.
    besides most use keyword args that we need the precise meaning of ( if they can be be used with 
    edit or query flags, the shortnames of flags, etc) so we have to parse the maya docs"""
    from parsers import CommandDocParser, mayaDocsLocation
    
    basicInfo = getCmdInfoBasic(command)
    
    try:
        docloc = mayaDocsLocation(version)
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
                #_logger.debug(command, "2nd", secondaryFlag)
                flags[secondaryFlag]['modified'] = modifiedList
                #_logger.debug(sorted(modifiedList))
                #_logger.debug(sorted(parser.flags.keys()))
                for primaryFlag in modifiedList:
                    #_logger.debug(command, "1st", primaryFlag)
                    if 'secondaryFlags' in parser.flags[primaryFlag]:
                        flags[primaryFlag]['secondaryFlags'].append(secondaryFlag)
                    else:
                        flags[primaryFlag]['secondaryFlags'] = [secondaryFlag]
        
                         
        # add shortname lookup
        #_logger.debug((command, sorted( basicInfo['flags'].keys() )))
        #_logger.debug((command, sorted( flags.keys() )))
        
        # args and numArgs is more reliable from mel help command than from parsed docs,
        # so, here we put that back in place and create shortflags. 
        
        
        for flag, flagData in flags.items():
            try:
                basicFlagData = basicInfo['flags'][flag]
                flagData['args'] = basicFlagData['args']
                flagData['numArgs'] = basicFlagData['numArgs']
            except KeyError: pass

        shortFlags = basicInfo['shortFlags']
        res = { 'flags': flags, 
                'shortFlags': shortFlags, 
                'description' : parser.description, 
                'example': example }
        try:
            res['removedFlags'] = basicInfo['removedFlags']
        except KeyError: pass
        return res
    
    
    except IOError:
        #_logger.debug("could not find docs for %s" % command)
        return basicInfo
        
        #raise IOError, "cannot find maya documentation directory"

def fixCodeExamples(style='maya', force=False):
    """cycle through all examples from the maya docs, replacing maya.cmds with pymel and inserting pymel output.
    
    NOTE: this can only be run from gui mode
    WARNING: back up your preferences before running 
    
    TODO: auto backup and restore of maya prefs 
    """
    
    manipOptions = cmds.manipOptions( q=1, handleSize=1, scale=1 )
    animOptions = []
    animOptions.append( cmds.animDisplay( q=1, timeCode=True ) )
    animOptions.append( cmds.animDisplay( q=1, timeCodeOffset=True )  )
    animOptions.append( cmds.animDisplay( q=1, modelUpdate=True ) )
    
    openWindows = cmds.lsUI(windows=True)
    examples = startup.loadCache('mayaCmdsExamples')
    processedExamples = startup.loadCache('mayaCmdsExamples', version=False)
    sortedCmds = sorted(examples.keys())
    # put commands that require manual interaction first
    manualCmds = []
    sortedCmds = manualCmds + [ sortedCmds.pop(x) for x in manualCmds ]
    
    for command in sortedCmds:
        example = examples[command]

        if not force and command in processedExamples:
            _logger.info("%s: already completed. skipping." % command)
            continue
        
        _logger.info("Starting command %s", command)
        
        # change from cmds to pymel
        reg = re.compile(r'\bcmds\.')
        example = reg.sub( 'pm.', example )
        #example = example.replace( 'import maya.cmds as cmds', 'import pymel as pm\npm.newFile(f=1) #fresh scene' )
        
        lines = example.split('\n')
        if len(lines)==1:
            _logger.info("removing empty example for command %s", command)
            examples.pop(command)
            continue
        
        if style == 'doctest' :
            DOC_TEST_SKIP = ' #doctest: +SKIP'
        else:
            DOC_TEST_SKIP = ''
        
        lines[0] = 'import pymel.core as pm' + DOC_TEST_SKIP 
        #lines.insert(1, 'pm.newFile(f=1) #fresh scene')
        # create a fresh scene. this does not need to be in the docstring unless we plan on using it in doctests, which is probably unrealistic
        cmds.file(new=1,f=1)
        
        newlines = []
        statement = []
        
        # narrowed down the commands that cause maya to crash to these prefixes
        if re.match( '(dis)|(dyn)|(poly)', command) :
            evaluate = False
        elif command in ['emit', 'finder', 'doBlur', 'messageLine', 'renderWindowEditor']:
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
                                    #_logger.debug("executing %s", statement)
                                    exec( '\n'.join(statement) )
                                    # reset statement
                                    statement = []
                                except Exception, e:
                                    _logger.info("stopping evaluation %s", str(e))# of %s on line %r" % (command, line)
                                    evaluate = False
                            try:
                                _logger.debug("evaluating: %r" % line)
                                res = eval( line )
                                #if res is not None: _logger.info("result", repr(repr(res)))
                                #else: _logger.info("no result")
                            except:
                                #_logger.debug("failed evaluating:", str(e))
                                try:
                                    exec( line )
                                except (Exception, TypeError), e:
                                    _logger.info("stopping evaluation %s", str(e))# of %s on line %r" % (command, line)
                                    evaluate = False
                    if style == 'doctest':                     
                        if line.startswith(' ') or line.startswith('\t'):       
                            newlines.append('    ... ' + line  )
                        else:
                            newlines.append('    >>> ' + line + DOC_TEST_SKIP )
                
                        if res is not None:
                            newlines.append( '    ' + repr(res) )
                    else:
                        newlines.append('    ' + line )
                        if res is not None:
                            newlines.append( '    # Result: %r #' % (res,) )
                    
            if evaluate:
                _logger.info("successful evaluation! %s", command)
                          
            example = '\n'.join( newlines )
            processedExamples[command] = example
        except:
            _logger.info("COMPLETE AND UTTER FAILURE: %s", command)
        else:
            # write out after each success so that if we crash we don't have to start from scratch
            startup.writeCache(processedExamples, 'mayaCmdsExamples', 'the Maya commands examples', version=False)
        
        # cleanup opened windows
        for ui in set(cmds.lsUI(windows=True)).difference(openWindows):
            try: cmds.deleteUI(ui, window=True)
            except:pass

    _logger.info("Done Fixing Examples")
    
    # restore manipulators and anim options
    cmds.manipOptions( handleSize=manipOptions[0], scale=manipOptions[1] )
    cmds.animDisplay( e=1, timeCode=animOptions[0], timeCodeOffset=animOptions[1], modelUpdate=animOptions[2])
   
    #startup.writeCache('mayaCmdsExamples', examples, 'the Maya commands examples')


def getModuleCommandList( category, version=None ):
    from parsers import CommandModuleDocParser
    parser = CommandModuleDocParser(category, version)
    return parser.parse()

def getCallbackFlags(cmdInfo):
    """used parsed data and naming convention to determine which flags are callbacks"""
    commandFlags = []
    try:
        flagDocs = cmdInfo['flags']
    except KeyError:
        pass
    else:
        for flag, data in flagDocs.items():
            if data['args'] in ['script', callable] or 'command' in flag.lower():
                commandFlags += [flag, data['shortname']]
    return commandFlags

#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------
def testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=False ):

    dangerousCmds = ['doBlur', 'pointOnPolyConstraint']
    if funcName in dangerousCmds:
        return cmdInfo
    
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
    
#    def _listIsCastable(resultType):
#        "ensure that all elements are the same type and that the types are castable"
#        try:
#            typ = resultType[0]
#            return typ in _castList and all([ x == typ for x in resultType ])
#        except IndexError:
#            return False
    
    module = cmds
    

    _logger.info(funcName.center( 50, '='))
    
    if funcName in [ 'character', 'lattice', 'boneLattice', 'sculpt', 'wire' ]:
        _logger.debug("skipping")
        return cmdInfo
        
    try:
        func = getattr(module, funcName)
    except AttributeError:
        _logger.warning("could not find function %s in modules %s" % (funcName, module.__name__))
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
                _logger.debug("Return %s", obj)
                if len(obj) == 1:
                    _logger.info("%s: creation return values need unpacking" % funcName)
                    cmdInfo['resultNeedsUnpacking'] = True
                elif not obj:
                    raise ValueError, "returned object is an empty list"
                obj = obj[-1]
                
                
            if obj is None:
                #emptyFunctions.append( funcName )
                raise ValueError, "Returned object is None"
            
            elif not cmds.objExists( obj ):
                raise ValueError, "Returned object %s is Invalid" % obj
         
            args = [obj]
                
    except (TypeError,RuntimeError, ValueError), msg:
        _logger.debug("failed creation: %s", msg)
        
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
            
            assert flag != 'ype', "%s has bad flag" % funcName

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
                #_logger.debug(flag, "Testing modes")
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
                    #_logger.debug(val)
                    resultType = _objectToType(val)
                    
                    # ensure symmetry between edit and query commands:
                    # if this flag is queryable and editable, then its queried value should be symmetric to its edit arguments
                    if 'edit' in modes and argtype != resultType:
                        # there are certain patterns of asymmetry which we can safely correct:
                        # [bool] --> bool
                        if isinstance( resultType, list) and len(resultType) ==1 and resultType[0] == argtype:
                            _logger.info("%s, %s: query flag return values need unpacking" % (funcName, flag))
                            flagInfo['resultNeedsUnpacking'] = True
                            val = val[0]
                            
                        # [int] --> bool
                        elif argtype in _castList and isinstance( resultType, list) and len(resultType) ==1 and resultType[0] in _castList:
                            _logger.info("%s, %s: query flag return values need unpacking and casting" % (funcName, flag))
                            flagInfo['resultNeedsUnpacking'] = True
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val[0])
                            
                        # int --> bool
                        elif argtype in _castList and resultType in _castList:
                            _logger.info("%s, %s: query flag return values need casting" % (funcName, flag))
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val)
                        else:
                            # no valid corrctions found
                            _logger.info(cmd)
                            _logger.info("\treturn mismatch")
                            _logger.info('\tresult: %s', val.__repr__())
                            _logger.info('\tpredicted type: %s', argtype)
                            _logger.info('\tactual type:    %s', resultType)
                            # value is no good. reset to None, so that a default will be generated for edit
                            val = None
                    
                    else:
                        _logger.debug(cmd)
                        _logger.debug("\tsucceeded")
                        _logger.debug('\tresult: %s', val.__repr__())
                        _logger.debug('\tresult type:    %s', resultType)
                        
                except TypeError, msg:
                    # flag is no longer supported                         
                    if str(msg).startswith( 'Invalid flag' ):
                        #if verbose:
                        _logger.info("removing flag %s %s %s", funcName, flag, msg)
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag,None)
                        flagInfo.pop(shortname,None)
                        modes = [] # stop edit from running
                    else:
                        _logger.info(cmd)
                        _logger.info("\t" + str(msg).rstrip('\n'))
                    val = None
                    
                except RuntimeError, msg:
                    _logger.info(cmd)
                    _logger.info("\t" + str(msg).rstrip('\n') )
                    val = None
                else:
                    # some flags are only in mel help and not in maya docs, so we don't know their
                    # supported per-flag modes.  we fill that in here
                    if 'query' not in flagInfo['modes']:
                        flagInfo['modes'].append('query')
            # EDIT
            if 'edit' in modes or testModes == True:
                
                #_logger.debug("Args:", argtype)
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
                    _logger.debug(cmd)
                    _logger.debug("\tsucceeded")
                    #_logger.debug('\t%s', val.__repr__())
                    #_logger.debug('\t%s %s', argtype, type(val))
                    #_logger.debug("SKIPPING %s: need arg of type %s" % (flag, flagInfo['argtype']))
                except TypeError, msg:                                                        
                    if str(msg).startswith( 'Invalid flag' ):
                        #if verbose:
                        # flag is no longer supported  
                        _logger.info("removing flag %s %s %s", funcName, flag, msg)
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag,None)
                        flagInfo.pop(shortname,None)
                    else:
                        _logger.info(cmd)
                        _logger.info("\t" + str(msg).rstrip('\n'))
                        _logger.info("\tpredicted arg: %s", argtype)
                        if not 'query' in modes:
                            _logger.info("\tedit only")
                except RuntimeError, msg:
                    _logger.info(cmd)
                    _logger.info("\t" + str(msg).rstrip('\n'))
                    _logger.info("\tpredicted arg: %s", argtype)
                    if not 'query' in modes:
                        _logger.info("\tedit only")
                else:
                    if 'edit' not in flagInfo['modes']:
                        flagInfo['modes'].append('edit')
    
    # cleanup
    allObjsEnd = set( cmds.ls(l=1) )
    newObjs = list(allObjsEnd.difference(  allObjsBegin ) )
    if newObjs:
        cmds.delete( newObjs ) 
    return cmdInfo
  
def _getNodeHierarchy( version=None ):
    """
    parse node hierarchy from docs and return as a list of 3-value tuples:
        ( nodeType, parents, children )
    """
    from parsers import NodeHierarchyDocParser
    parser = NodeHierarchyDocParser(version)
    import pymel.util.trees as trees
    nodeHierarchyTree = trees.IndexedTree(parser.parse())
    return [ (x.key, tuple( [y.key for y in x.parents()]), tuple( [y.key for y in x.childs()] ) ) \
             for x in nodeHierarchyTree.preorder() ]
   
def buildCachedData() :
    """Build and save to disk the list of Maya Python commands and their arguments"""
    
    # With extension can't get docs on unix 64
    # path is
    # /usr/autodesk/maya2008-x64/docs/Maya2008/en_US/Nodes/index_hierarchy.html
    # and not
    # /usr/autodesk/maya2008-x64/docs/Maya2008-x64/en_US/Nodes/index_hierarchy.html
    long_version = versions.installName()
    
    data = startup.loadCache( 'mayaCmdsList', 'the list of Maya commands' )
    
    if data is not None:
        cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds = data
    
    else: # or not isinstance(cmdlist,list):        
        cmdlist = {}
        _logger.info("Rebuilding the list of Maya commands...")
        
        nodeHierarchy = _getNodeHierarchy(long_version)
        nodeFunctions = [ x[0] for x in nodeHierarchy ]
        nodeFunctions += nodeTypeToNodeCommand.values()
        
        #nodeHierarchyTree = trees.IndexedTree(nodeHierarchy)
        uiClassList = UI_COMMANDS
        nodeCommandList = []
        for moduleName, longname in moduleNameShortToLong.items():
            moduleNameShortToLong[moduleName] = getModuleCommandList( longname, long_version )
                        
        tmpCmdlist = inspect.getmembers(cmds, callable)
        cmdlist = {}
        #moduleCmds = defaultdict(list)
        moduleCmds = dict( (k,[]) for k in moduleNameShortToLong.keys() )
        moduleCmds.update( {'other':[], 'runtime': [], 'context': [], 'uiClass': [] } )
    
        for funcName, data in tmpCmdlist :     
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
                    if funcName in nodeFunctions:
                        nodeCommandList.append(funcName)
                        cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=True, verbose=True  )
                    #elif module != 'context':
                    #    cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=True  )
                
            cmdInfo['type'] = module
            flags = getCallbackFlags(cmdInfo)
            if flags:
                cmdInfo['callbackFlags'] = flags
            
            cmdlist[funcName] = cmdInfo
            
            
#            # func, args, (usePyNode, baseClsName, nodeName)
#            # args = dictionary of command flags and their data
#            # usePyNode = determines whether the class returns its 'nodeName' or uses PyNode to dynamically return
#            # baseClsName = for commands which should generate a class, this is the name of the superclass to inherit
#            # nodeName = most creation commands return a node of the same name, this option is provided for the exceptions
#            try:
#                cmdlist[funcName] = args, pymelCmdsList[funcName] )        
#            except KeyError:
#                # context commands generate a class based on unicode (which is triggered by passing 'None' to baseClsName)
#                if funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
#                     cmdlist[funcName] = (funcName, args, (False, None, None) )
#                else:
#                    cmdlist[funcName] = (funcName, args, () )

        # split the cached data for lazy loading
        cmdDocList = {}
        examples = {} 
        for cmdName, cmdInfo in cmdlist.iteritems():
            try:
                examples[cmdName] = cmdInfo.pop('example')
            except KeyError:
                pass
            
            newCmdInfo = {}
            if 'description' in cmdInfo:
                newCmdInfo['description'] = cmdInfo.pop('description')
            newFlagInfo = {}
            if 'flags' in cmdInfo:
                for flag, flagInfo in cmdInfo['flags'].iteritems():
                    newFlagInfo[flag] = { 'docstring' : flagInfo.pop('docstring') }
                newCmdInfo['flags'] = newFlagInfo
            
            if newCmdInfo:
                cmdDocList[cmdName] = newCmdInfo
         
        startup.writeCache( (cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds), 
                              'mayaCmdsList', 'the list of Maya commands',compressed=True )
        
        startup.writeCache( cmdDocList, 
                              'mayaCmdsDocs', 'the Maya command documentation',compressed=True )
    
        startup.writeCache( examples, 
                              'mayaCmdsExamples', 'the list of Maya command examples',compressed=True )
    
    util.mergeCascadingDicts( cmdlistOverrides, cmdlist )
            
    return (cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds)

cmdlist, nodeHierarchy, uiClassList, nodeCommandList, moduleCmds = buildCachedData()

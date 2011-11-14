# Built-in imports
import os, re, inspect, keyword

# Maya imports
import maya.cmds as cmds
import maya.mel as mm

# PyMEL imports
import pymel.util as util
import pymel.versions as versions

# Module imports
from . import plogging
from . import startup

_logger = plogging.getLogger(__name__)

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

#: these are commands which need to be manually added to the list parsed from the docs
moduleCommandAdditions = {
    'windows' : ['connectControl', 'deleteUI','uiTemplate','setUITemplate','renameUI','setParent','objectTypeUI','lsUI', 'disable', 'dimWhen'],
    'general' : ['encodeString', 'format', 'assignCommand', 'commandEcho', 'condition', 'evalDeferred', 'isTrue', 'itemFilter', 'itemFilterAttr',
                 'itemFilterRender', 'itemFilterType', 'pause', 'refresh', 'stringArrayIntersector', 'selectionConnection']
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
    'file'              : None, # prevent File node from using cmds.file
    'nurbsSurface'      : 'surface',
    'annotationShape'   : 'annotate',
    'condition'         : None, # prevent Condition node from using cmds.condition (which is for script conditions)
}


cmdlistOverrides = {}
#util.setCascadingDictItem( cmdlistOverrides, ( 'optionMenu', 'shortFlags', 'sl', 'modes' ), ['create', 'query', 'edit'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'optionMenu', 'flags', 'select', 'modes' ),  ['create', 'query', 'edit'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'ikHandle', 'flags', 'jointList', 'modes' ), ['query'] )
#util.setCascadingDictItem( cmdlistOverrides, ( 'ikHandle', 'shortFlags', 'jl', 'modes' ),   ['query'] )
util.setCascadingDictItem( cmdlistOverrides, ( 'keyframe', 'flags', 'index', 'args' ), 'timeRange' ) # make sure this is a time range so it gets proper slice syntax

# Need to override this, rather than having it deteced from testNodeCmd, because
# it crashes testNodeCmd
util.setCascadingDictItem( cmdlistOverrides, ( 'pointOnPolyConstraint', 'resultNeedsUnpacking', ), True )

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
                    multiuse = True
                except ValueError:
                    multiuse = False
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
                    if multiuse:
                        flags[longname].setdefault('modes', []).append('multiuse')
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

        # also use original 'multiuse' info...

        for flag, flagData in flags.items():
            basicFlagData = basicInfo.get('flags', {}).get(flag)
            if basicFlagData:
                if 'args' in basicFlagData and 'numargs' in basicFlagData:
                    flagData['args'] = basicFlagData['args']
                    flagData['numArgs'] = basicFlagData['numArgs']
                    if (        'multiuse' in basicFlagData.get('modes', [])
                            and 'multiuse' not in  flagData.get('modes', [])):
                        flagData.setdefault('modes', []).append('multiuse')

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
    examples = CmdExamplesCache().read()
    processedExamples = CmdProcessedExamplesCache().read()
    processedExamples = {} if processedExamples is None else processedExamples
    allCmds = set(examples.keys())
    # put commands that require manual interaction first
    manualCmds = ['fileBrowserDialog', 'fileDialog', 'fileDialog2', 'fontDialog']
    skipCmds = ['colorEditor', 'emit', 'finder', 'doBlur', 'messageLine', 'renderWindowEditor', 'ogsRender', 'webBrowser', 'deleteAttrPattern']
    allCmds.difference_update(manualCmds)
    sortedCmds = manualCmds + sorted(allCmds)
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
            processedExamples[command] = ''
            # write out after each success so that if we crash we don't have to start from scratch
            CmdProcessedExamplesCache().write(processedExamples)
            continue

        if style == 'doctest' :
            DOC_TEST_SKIP = ' #doctest: +SKIP'
        else:
            DOC_TEST_SKIP = ''

        lines[0] = 'import pymel.core as pm' + DOC_TEST_SKIP
        
        if command in skipCmds:
            example = '\n'.join( lines )
            processedExamples[command] = example
            # write out after each success so that if we crash we don't have to start from scratch
            CmdProcessedExamplesCache().write(processedExamples)

        #lines.insert(1, 'pm.newFile(f=1) #fresh scene')
        # create a fresh scene. this does not need to be in the docstring unless we plan on using it in doctests, which is probably unrealistic
        cmds.file(new=1,f=1)

        newlines = []
        statement = []

        # narrowed down the commands that cause maya to crash to these prefixes
        if re.match( '(dis)|(dyn)|(poly)', command) :
            evaluate = False
        elif command in skipCmds:
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
        except Exception, e:
            raise
            #_logger.info("FAILED: %s: %s" % (command, e) )
        else:
            # write out after each success so that if we crash we don't have to start from scratch
            CmdProcessedExamplesCache().write(processedExamples)

        # cleanup opened windows
        for ui in set(cmds.lsUI(windows=True)).difference(openWindows):
            try: cmds.deleteUI(ui, window=True)
            except:pass

    _logger.info("Done Fixing Examples")

    # restore manipulators and anim options
    print manipOptions
    cmds.manipOptions( handleSize=manipOptions[0], scale=manipOptions[1] )
    cmds.animDisplay( e=1, timeCode=animOptions[0], timeCodeOffset=animOptions[1], modelUpdate=animOptions[2])

    #CmdExamplesCache(examples)


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

def getModule(funcName, knownModuleCmds):
    # determine to which module this function belongs
    module = None
    if funcName in ['eval', 'file', 'filter', 'help', 'quit']:
        module = None
    elif funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
        module = 'context'
    #elif funcName in self.uiClassList:
    #    module = 'uiClass'
    #elif funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
    #    module = 'node'
    else:
        for moduleName, commands in knownModuleCmds.iteritems():
            if funcName in commands:
                module = moduleName
                break
        if module is None:
            if mm.eval('whatIs "%s"' % funcName ) == 'Run Time Command':
                module = 'runtime'
            else:
                module = 'other'
    return module

#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------
_cmdArgMakers = {}
def cmdArgMakers(force=False):
    global _cmdArgMakers
    
    if _cmdArgMakers and not force:
        return _cmdArgMakers
    
    def makeCircle():
        return cmds.circle()[0]
    def makeEp():
        return makeCircle() + '.ep[1]'
    def makeSphere():
        return cmds.polySphere()[0]
    def makeCube():
        return cmds.polyCube()[0]
    def makeIk():
        j1 = cmds.joint()
        j2 = cmds.joint()
        return cmds.ikHandle(j1, j2, solver='ikRPsolver')[0]
    def makeJoint():
        return cmds.joint()
    def makeSkin():
        j1 = cmds.joint()
        j2 = cmds.joint()
        sphere = makeSphere()
        return cmds.skinCluster(j1, j2, sphere)[0]
    
    _cmdArgMakers = \
        { 'tangentConstraint'   : ( makeCircle, makeCube ),
          'poleVectorConstraint': ( makeSphere, makeIk ),
          'pointCurveConstraint': ( makeEp, ),
          'skinCluster'         : ( makeJoint, makeJoint, makeSphere ),
        }
    
    constraintCmds = [x for x in dir(cmds)
                      if x.endswith('onstraint')
                         and not cmds.runTimeCommand(x, q=1, exists=1)
                         and x != 'polySelectConstraint']
    
    for constrCmd in constraintCmds:
        if constrCmd not in _cmdArgMakers: 
            _cmdArgMakers[constrCmd] = ( makeSphere, makeCube )
    
    return _cmdArgMakers

def nodeCreationCmd(func, nodeType):
    argMakers = cmdArgMakers()
    
    # compile the args list for node creation
    createArgs = argMakers.get(nodeType, [])
    if createArgs:
        createArgs = [argMaker() for argMaker in createArgs] 

    # run the function
    return func(*createArgs)

def testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=False ):

    _logger.info(funcName.center( 50, '='))

    if funcName in [ 'character', 'lattice', 'boneLattice', 'sculpt', 'wire' ]:
        _logger.debug("skipping")
        return cmdInfo
    
    # These cause crashes... confirmed that pointOnPolyConstraint still
    # crashes in 2012
    dangerousCmds = ['doBlur', 'pointOnPolyConstraint']
    if funcName in dangerousCmds:
        _logger.debug("skipping 'dangerous command'")
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
            obj = nodeCreationCmd(func, funcName)

            if isinstance(obj, list):
                _logger.debug("Return %s", obj)
                if len(obj) == 1:
                    _logger.info("%s: creation return values need unpacking" % funcName)
                    cmdInfo['resultNeedsUnpacking'] = True
                elif not obj:
                    raise ValueError, "returned object is an empty list"
                objTransform = obj[0]
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
        objType = cmds.objectType(obj)
        #------------------
        # TESTING
        #------------------

        #(func, args, data) = cmdList[funcName]
        #(usePyNode, baseClsName, nodeName)
        flags = cmdInfo['flags']

        hasQueryFlag = flags.has_key( 'query' )
        hasEditFlag = flags.has_key( 'edit' )

        anyNumRe = re.compile('\d+')

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
                    _logger.debug(cmd)
                    val = func( *flagargs, **kwargs )
                    #_logger.debug(val)
                    resultType = _objectToType(val)

                    # ensure symmetry between edit and query commands:
                    # if this flag is queryable and editable, then its queried value should be symmetric to its edit arguments
                    if 'edit' in modes and argtype != resultType:
                        # there are certain patterns of asymmetry which we can safely correct:
                        singleItemList = (isinstance( resultType, list)
                                          and len(resultType) ==1
                                          and 'multiuse' not in flagInfo.get('modes', []))
                        
                        # [bool] --> bool
                        if singleItemList and resultType[0] == argtype:
                            _logger.info("%s, %s: query flag return values need unpacking" % (funcName, flag))
                            flagInfo['resultNeedsUnpacking'] = True
                            val = val[0]

                        # [int] --> bool
                        elif singleItemList and argtype in _castList and resultType[0] in _castList:
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
                    _logger.debug(cmd)

                    # some commands will either delete or rename a node, ie:
                    #     spaceLocator(e=1, name=...)
                    #     container(e=1, removeContainer=True )
                    # ...which will then make subsequent cmds fail.
                    # To get around this, we need to undo the cmd.
                    try:
                        cmds.undoInfo(openChunk=True)
                        editResult = func( *args, **kwargs )
                    finally:
                        cmds.undoInfo(closeChunk=True)

                    if not cmds.objExists(obj):
                        # cmds.camera(e=1, name=...) does weird stuff - it
                        # actually renames the parent transform, even if you give
                        # the name of the shape... which means the shape
                        # then gets a second 'Shape1' tacked at the end...
                        # ...and in addition, undo is broken as well.
                        # So we need a special case for this, where we rename...
                        if objType == 'camera' and flag == 'name':
                            _logger.info('\t(Undoing camera rename)')
                            renamePattern = anyNumRe.sub('*', obj)
                            possibleRenames = cmds.ls(renamePattern, type=objType)
                            possibleRenames = [x for x in possibleRenames
                                               if x not in allObjsBegin]
                            # newName might not be the exact same as our original,
                            # but as long as it's the same maya type, and isn't
                            # one of the originals, it shouldn't matter...
                            newName = possibleRenames[-1]
                            cmds.rename(newName, obj)
                        else:
                            _logger.info('\t(Undoing cmd)')
                            cmds.undo()
                    _logger.debug("\tsucceeded")
                    #_logger.debug('\t%s', editResult.__repr__())
                    #_logger.debug('\t%s %s', argtype, type(editResult))
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
                        _logger.info(funcName)
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

class InvalidNodeTypeError(Exception): pass
class ManipNodeTypeError(InvalidNodeTypeError): pass

def getInheritance( mayaType, checkManip3D=True ):
    """Get parents as a list, starting from the node after dependNode, and
    ending with the mayaType itself. To get the inheritance we use nodeType,
    which requires a real node.  To do get these without poluting the scene we
    use a dag/dg modifier, call the doIt method, get the lineage, then call
    undoIt.
    
    A ManipNodeTypeError is the node type fed in was a manipulator
    """
    from . import apicache
    import pymel.api as api
    
    if versions.current() >= versions.v2012:
        # We now have nodeType(isTypeName)! yay!
        kwargs = dict(isTypeName=True, inherited=True)
        lineage = cmds.nodeType(mayaType, **kwargs)
        if lineage is None:
            controlPoint = cmds.nodeType('controlPoint', **kwargs)
            # For whatever reason, nodeType(isTypeName) returns
            # None for the following mayaTypes:
            fixedLineages = {
                'file':[u'texture2d', u'file'],
                'lattice':controlPoint + [u'lattice'],
                'mesh':controlPoint + [u'surfaceShape', u'mesh'],
                'nurbsCurve':controlPoint + [u'curveShape', u'nurbsCurve'],
                'nurbsSurface':controlPoint + [u'surfaceShape', u'nurbsSurface'],
                'time':[u'time']
            }
            if mayaType in fixedLineages:
                lineage = fixedLineages[mayaType]
            else:
                raise RuntimeError("Could not query the inheritance of node type %s" % mayaType)
        elif checkManip3D and 'manip3D' in lineage:
            raise ManipNodeTypeError
        assert lineage[-1] == mayaType
    else:
        dagMod = api.MDagModifier()
        dgMod = api.MDGModifier()
    
        obj = apicache._makeDgModGhostObject(mayaType, dagMod, dgMod)
    
        lineage = []
        if obj is not None:
            if (      obj.hasFn( api.MFn.kManipulator )      
                   or obj.hasFn( api.MFn.kManipContainer )
                   or obj.hasFn( api.MFn.kPluginManipContainer )
                   or obj.hasFn( api.MFn.kPluginManipulatorNode )
                   
                   or obj.hasFn( api.MFn.kManipulator2D )
                   or obj.hasFn( api.MFn.kManipulator3D )
                   or obj.hasFn( api.MFn.kManip2DContainer) ):
                raise ManipNodeTypeError
     
            if obj.hasFn( api.MFn.kDagNode ):
                mod = dagMod
                mod.doIt()
                name = api.MFnDagNode(obj).partialPathName()
            else:
                mod = dgMod
                mod.doIt()
                name = api.MFnDependencyNode(obj).name()
        
            if not obj.isNull() and not obj.hasFn( api.MFn.kManipulator3D ) and not obj.hasFn( api.MFn.kManipulator2D ):
                lineage = cmds.nodeType( name, inherited=1)
            mod.undoIt()
    return lineage

def _getNodeHierarchy( version=None ):
    """
    get node hierarchy as a list of 3-value tuples:
        ( nodeType, parents, children )
    """
    import pymel.util.trees as trees
    
    if versions.current() >= versions.v2012:
        # We now have nodeType(isTypeName)! yay!
        inheritances = {}
        for nodeType in cmds.allNodeTypes():
            try:
                inheritances[nodeType] = getInheritance(nodeType)
            except ManipNodeTypeError:
                continue
        
        parentTree = {}
        # Convert inheritance lists node=>parent dict
        for nodeType, inheritance in inheritances.iteritems():
            for i in xrange(len(inheritance)):
                child = inheritance[i]
                if i == 0:
                    if child == 'dependNode':
                        continue
                    # FIXME: this is a hack because something may be wrong with the file node.  
                    # all other nodes that inherit from 'texture2d' identify its parent as 'shadingDependNode'
                    elif nodeType == 'file':
                        parent = 'shadingDependNode'
                    else:
                        parent = 'dependNode'
                else:
                    parent = inheritance[i - 1]
                
                if child in parentTree:
                    assert parentTree[child] == parent, "conflicting parents: node type '%s' previously determined parent was '%s'. now '%s'" % (child, parentTree[child], parent)
                else:
                    parentTree[child] = parent
        nodeHierarchyTree = trees.treeFromDict(parentTree)
    else:
        from .parsers import NodeHierarchyDocParser
        parser = NodeHierarchyDocParser(version)
        nodeHierarchyTree = trees.IndexedTree(parser.parse())
    return [ (x.value, tuple( [y.value for y in x.parents()]), tuple( [y.value for y in x.childs()] ) ) \
             for x in nodeHierarchyTree.preorder() ]


class CmdExamplesCache(startup.PymelCache):
    NAME = 'mayaCmdsExamples'
    DESC = 'the list of Maya command examples'
    USE_VERSION = True

class CmdProcessedExamplesCache(CmdExamplesCache):
    USE_VERSION = False

class CmdDocsCache(startup.PymelCache):
    NAME = 'mayaCmdsDocs'
    DESC = 'the Maya command documentation'

class CmdCache(startup.SubItemCache):
    NAME = 'mayaCmdsList'
    DESC = 'the list of Maya commands'
    _CACHE_NAMES = '''cmdlist nodeHierarchy uiClassList
                        nodeCommandList moduleCmds'''.split()
    CACHE_TYPES = {'nodeHierarchy':list,
                   'uiClassList':list,
                   'nodeCommandList':list,
                   }
        
    def rebuild(self) :
        """Build and save to disk the list of Maya Python commands and their arguments
        
        WARNING: will unload existing plugins, then (re)load all maya-installed
        plugins, without making an attempt to return the loaded plugins to the
        state they were at before this command is run.  Also, the act of
        loading all the plugins may crash maya, especially if done from a
        non-GUI session        
        """
        # Put in a debug, because this can be crashy
        _logger.debug("Starting CmdCache.rebuild...")
        
        # With extension can't get docs on unix 64
        # path is
        # /usr/autodesk/maya2008-x64/docs/Maya2008/en_US/Nodes/index_hierarchy.html
        # and not
        # /usr/autodesk/maya2008-x64/docs/Maya2008-x64/en_US/Nodes/index_hierarchy.html

        long_version = versions.installName()
        
        _logger.info("Rebuilding the maya node hierarchy...")
        
        # Load all plugins to get the nodeHierarchy / nodeFunctions
        import pymel.api.plugins as plugins
        
        # We don't want to add in plugin nodes / commands - let that be done
        # by the plugin callbacks.  However, unloading mechanism is not 100%
        # ... sometimes functions get left in maya.cmds... and then trying
        # to use those left-behind functions can cause crashes (ie,
        # FBXExportQuaternion). So check which methods SHOULD be unloaded
        # first, so we know to skip those if we come across them even after
        # unloading the plugin
        pluginCommands = set()
        loadedPlugins = cmds.pluginInfo(q=True, listPlugins=True)
        if loadedPlugins:
            for plug in loadedPlugins:
                plugCmds = plugins.pluginCommands(plug)
                if plugCmds:
                    pluginCommands.update(plugCmds)
        
        plugins.unloadAllPlugins()

        self.nodeHierarchy = _getNodeHierarchy(long_version)
        nodeFunctions = [ x[0] for x in self.nodeHierarchy ]
        nodeFunctions += nodeTypeToNodeCommand.values()


        _logger.info("Rebuilding the list of Maya commands...")

        #nodeHierarchyTree = trees.IndexedTree(self.nodeHierarchy)
        self.uiClassList = UI_COMMANDS
        self.nodeCommandList = []
        tmpModuleCmds = {}
        for moduleName, longname in moduleNameShortToLong.items():
            tmpModuleCmds[moduleName] = getModuleCommandList( longname, long_version )

        tmpCmdlist = inspect.getmembers(cmds, callable)

        #self.moduleCmds = defaultdict(list)
        self.moduleCmds = dict( (k,[]) for k in moduleNameShortToLong.keys() )
        self.moduleCmds.update( {'other':[], 'runtime': [], 'context': [], 'uiClass': [] } )

        def addCommand(funcName):
            _logger.debug('adding command: %s' % funcName)
            module = getModule(funcName, tmpModuleCmds)

            cmdInfo = {}

            if module:
                self.moduleCmds[module].append(funcName)

            if module != 'runtime':
                cmdInfo = getCmdInfo(funcName, long_version)

                if module != 'windows':
                    if funcName in nodeFunctions:
                        self.nodeCommandList.append(funcName)
                        cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=True, verbose=True  )
                    #elif module != 'context':
                    #    cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=True  )

            cmdInfo['type'] = module
            flags = getCallbackFlags(cmdInfo)
            if flags:
                cmdInfo['callbackFlags'] = flags

            self.cmdlist[funcName] = cmdInfo

#            # func, args, (usePyNode, baseClsName, nodeName)
#            # args = dictionary of command flags and their data
#            # usePyNode = determines whether the class returns its 'nodeName' or uses PyNode to dynamically return
#            # baseClsName = for commands which should generate a class, this is the name of the superclass to inherit
#            # nodeName = most creation commands return a node of the same name, this option is provided for the exceptions
#            try:
#                self.cmdlist[funcName] = args, pymelCmdsList[funcName] )
#            except KeyError:
#                # context commands generate a class based on unicode (which is triggered by passing 'None' to baseClsName)
#                if funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
#                     self.cmdlist[funcName] = (funcName, args, (False, None, None) )
#                else:
#                    self.cmdlist[funcName] = (funcName, args, () )

        for funcName, _ in tmpCmdlist :
            if funcName in pluginCommands:
                _logger.debug("command %s was a plugin command that should have been unloaded - skipping" % funcName)
                continue 
            addCommand(funcName)

        # split the cached data for lazy loading
        cmdDocList = {}
        examples = {}
        for cmdName, cmdInfo in self.cmdlist.iteritems():
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
    
        CmdDocsCache().write(cmdDocList)
        CmdExamplesCache().write(examples)
        
    def build(self):
        super(CmdCache, self).build()

        # corrections that are always made, to both loaded and freshly built caches
        util.mergeCascadingDicts( cmdlistOverrides, self.cmdlist )
        # add in any nodeCommands added after cache rebuild
        self.nodeCommandList = set(self.nodeCommandList).union(nodeTypeToNodeCommand.values())
        self.nodeCommandList = sorted( self.nodeCommandList )
    
    
        for module, funcNames in moduleCommandAdditions.iteritems():
            for funcName in funcNames:
                currModule = self.cmdlist[funcName]['type']
                if currModule != module:
                    self.cmdlist[funcName]['type'] = module
                    id = self.moduleCmds[currModule].index(funcName)
                    self.moduleCmds[currModule].pop(id)
                    self.moduleCmds[module].append(funcName)
        return (self.cmdlist,self.nodeHierarchy,self.uiClassList,self.nodeCommandList,self.moduleCmds)

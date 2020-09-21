from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
# Built-in imports
from future.utils import PY2
from builtins import range
from past.builtins import basestring
import os
import re
import inspect
import keyword

# Maya imports
import maya.cmds as cmds
import maya.mel as mm

# PyMEL imports
import pymel.util as util
import pymel.versions as versions

# Module imports
from . import plogging
from . import startup

if False:
    from typing import *

_logger = plogging.getLogger(__name__)

moduleNameShortToLong = {
    'modeling': 'Modeling',
    'rendering': 'Rendering',
    'effects': 'Effects',
    'animation': 'Animation',
    'windows': 'Windows',
    'system': 'System',
    'general': 'General',
    'language': 'Language'
}

#: these are commands which need to be manually added to the list parsed from the docs
moduleCommandAdditions = {
    'windows': ['connectControl', 'deleteUI', 'uiTemplate', 'setUITemplate', 'renameUI', 'setParent', 'objectTypeUI', 'lsUI', 'disable', 'dimWhen'],
    'general': ['encodeString', 'format', 'assignCommand', 'commandEcho', 'condition', 'evalDeferred', 'isTrue', 'itemFilter', 'itemFilterAttr',
                'itemFilterRender', 'itemFilterType', 'pause', 'refresh', 'stringArrayIntersector', 'selectionConnection']
}

# secondary flags can only be used in conjunction with other flags so we must
# exclude them when creating classes from commands. because the maya docs do
# not specify in any parsable way which flags are secondary modifiers, we must
# maintain this dictionary. once this list is reliable enough and includes
# default values, we can use them as keyword arguments in the class methods
# that they modify.
secondaryFlags = {
    'xform': (('absolute', None, []),
              ('relative', None, []),
              ('euler', None, ['relative']),
              ('objectSpace', True, ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotateTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots']),
              ('worldSpace', False, ['scalePivot', 'rotatePivot', 'rotateAxis', 'rotation', 'rotateTranslation', 'translation', 'matrix', 'boundingBox', 'boundingBoxInvisible', 'pivots']),
              ('preserve', None, ['scalePivot', 'rotatePivot', 'rotateOrder', 'rotateAxis', 'centerPivots']),
              ('worldSpaceDistance', None, ['scalePivot', 'rotatePivot', 'scaleTranslation', 'rotateTranslation', 'translation', 'pivots'])
              ),
    'file': (('loadAllDeferred', False, ['open']),
             ('loadNoReferences', False, ['open', 'i', 'reference', 'loadReference']),
             ('loadReferenceDepth', None, ['open', 'i', 'reference', 'loadReference']),
             ('force', False, ['open', 'newFile', 'save', 'exportAll', 'exportSelected', 'exportAnim',
                               'exportSelectedAnim', 'exportAnimFromReference', 'exportSelectedAnimFromReference']),
             ('constructionHistory', True, ['exportSelected']),
             ('channels', True, ['exportSelected']),
             ('constraints', True, ['exportSelected']),
             ('expressions', True, ['exportSelected']),
             ('shader', True, ['exportSelected']),
             ('defaultNamespace', False, ['reference', 'i']),
             ('deferReference', False, ['reference', 'i']),
             ('editCommand', None, ['cleanReference']),
             ('groupReference', False, ['reference', 'i']),
             ('groupLocator', None, ['reference']),
             ('groupName', None, ['reference', 'i']),
             ('namespace', None, ['reference', 'exportAsReference', 'namespace']),
             ('referenceNode', None, ['reference', 'exportAnimFromReference', 'exportSelectedAnimFromReference']),
             ('renameAll', None, ['i']),
             ('renamingPrefix', None, ['reference', 'i', 'exportAsReference']),
             #( 'saveTextures', "unlessRef", ['saveAs']),
             ('swapNamespace', None, ['reference', 'i']),
             ('sharedReferenceFile', None, ['reference']),
             ('sharedNodes', None, ['reference']),
             ('returnNewNodes', False, ['open', 'reference', 'i', 'loadReference']),
             #( 'loadSettings', ),
             ('preserveReferences', False, ['i', 'exportAll', 'exportSelected']),
             ('preSaveScript', None, ['save']),
             ('postSaveScript', None, ['save']),
             ('type', None, ['open', 'newFile', 'save', 'exportAll', 'exportSelected', 'exportAnim',
                             'exportSelectedAnim', 'exportAnimFromReference', 'exportSelectedAnimFromReference']),
             ),
    'joint': (('absolute', True, ['position']),
              ('relative', True, ['position']))
}


UI_COMMANDS = """attrColorSliderGrp        attrControlGrp
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

#: creation commands whose names do not match the type of node they return
# require this dict to resolve which command the class should wrap
nodeTypeToNodeCommand = {
    #'failed'            : 'clip',
    #'failed'            : 'clipSchedule',
    'airField': 'air',
    'dragField': 'drag',
    'emitter': 'emitter',
    'turbulenceField': 'turbulence',
    #'failed' : 'effector',
    'volumeAxisField': 'volumeAxis',
    'uniformField': 'uniform',
    'gravityField': 'gravity',
    #'failed'            : 'event',
    #'failed'            : 'pointCurveConstraint',
    #'failed'            : 'deformer',
    #'failed'            : 'constrain',
    'locator': 'spaceLocator',
    'vortexField': 'vortex',
    'makeNurbTorus': 'torus',
    'makeNurbCone': 'cone',
    'makeNurbCylinder': 'cylinder',
    'nurbsCurve': 'curve',  # returns a single transform, but creates a nurbsCurve
    'makeNurbSphere': 'sphere',
    'makeNurbCircle': 'circle',
    'makeNurbPlane': 'nurbsPlane',
    'makeNurbsSquare': 'nurbsSquare',
    'makeNurbCube': 'nurbsCube',
    'skinPercent': 'skinCluster',
    'file': None,  # prevent File node from using cmds.file
    'nurbsSurface': 'surface',
    'annotationShape': 'annotate',
    'condition': None,  # prevent Condition node from using cmds.condition (which is for script conditions)
}


cmdlistOverrides = {}
#util.setCascadingDictItem( cmdlistOverrides, ( 'optionMenu', 'shortFlags', 'sl', 'modes' ), ['create', 'query', 'edit'] )
util.setCascadingDictItem(cmdlistOverrides, ('optionMenu', 'flags', 'select', 'modes'), ['create', 'query', 'edit'])
util.setCascadingDictItem(cmdlistOverrides, ('ikHandle', 'flags', 'jointList', 'modes'), ['query'])
#util.setCascadingDictItem( cmdlistOverrides, ( 'ikHandle', 'shortFlags', 'jl', 'modes' ),   ['query'] )
util.setCascadingDictItem(cmdlistOverrides, ('keyframe', 'flags', 'index', 'args'), 'timeRange')  # make sure this is a time range so it gets proper slice syntax

# Need to override this, rather than having it deteced from testNodeCmd, because
# it crashes testNodeCmd
util.setCascadingDictItem(cmdlistOverrides, ('pointOnPolyConstraint', 'resultNeedsUnpacking', ), True)

_internalCmds = None

def getInternalCmds(errorIfMissing=True):
    global _internalCmds

    if _internalCmds is not None:
        return _internalCmds

    from .parsers import mayaDocsLocation
    docsdir = mayaDocsLocation()
    cmds = []
    # they first provided them as 'internalCmds.txt', then as
    # internalCommandList.txt
    notfound = []
    for filename in ('internalCmds.txt', 'internalCommandList.txt'):
        cmdlistPath = os.path.join(docsdir, filename)
        if os.path.isfile(cmdlistPath):
            break
        else:
            notfound.append(cmdlistPath)
    else:
        filepaths = ', '.join(notfound)
        raise RuntimeError("could not find list of internal commands - tried: {}"
                           .format(filepaths))
    with open(cmdlistPath) as f:
        for line in f:
            line = line.strip()
            if line:
                cmds.append(line)
    _internalCmds = set(cmds)
    return _internalCmds


def getCmdInfoBasic(command):
    typemap = {
        'string': str,
        'length': float,
        'float': float,
        'angle': float,
        'int': int,
        'unsignedint': int,
        'on|off': bool,
        'script': callable,
        'name': 'PyNode'
    }
    flags = {}
    shortFlags = {}
    removedFlags = {}
    try:
        lines = cmds.help(command).split('\n')
    except RuntimeError:
        pass
    else:
        synopsis = lines.pop(0)
        # certain commands on certain platforms have an empty first line
        if not synopsis:
            synopsis = lines.pop(0)
        #_logger.debug(synopsis)
        if lines:
            lines.pop(0)  # 'Flags'
            #_logger.debug(lines)

            for line in lines:
                line = line.replace('(Query Arg Mandatory)', '')
                line = line.replace('(Query Arg Optional)', '')
                tokens = line.split()

                try:
                    tokens.remove('(multi-use)')
                    multiuse = True
                except ValueError:
                    multiuse = False
                #_logger.debug(tokens)
                if len(tokens) > 1 and tokens[0].startswith('-'):

                    args = [typemap.get(x.lower(), util.uncapitalize(x)) for x in tokens[2:]]
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
                        removedFlags[longname] = shortname
                        longname = shortname
                    elif shortname in keyword.kwlist:
                        removedFlags[shortname] = longname
                        shortname = longname
                    # sometimes the longname is empty, so we'll use the shortname for both
                    elif longname == '':
                        longname = shortname

                    flags[longname] = {'longname': longname, 'shortname': shortname, 'args': args, 'numArgs': numArgs, 'docstring': ''}
                    if multiuse:
                        flags[longname].setdefault('modes', []).append('multiuse')
                    shortFlags[shortname] = longname

    # except:
    #    pass
        #_logger.debug("could not retrieve command info for", command)
    res = {'flags': flags, 'shortFlags': shortFlags, 'description': '', 'example': '', 'type': 'other'}
    if removedFlags:
        res['removedFlags'] = removedFlags
    return res


def getCmdInfo(command, version, python=True):
    """Since many maya Python commands are builtins we can't get use getargspec on them.
    besides most use keyword args that we need the precise meaning of ( if they can be be used with
    edit or query flags, the shortnames of flags, etc) so we have to parse the maya docs"""
    from .parsers import CommandDocParser, mayaDocsLocation

    basicInfo = getCmdInfoBasic(command)

    # for consistency, always just use basicInfo for internal commands -
    # sometimes we get docs for them, sometimes we don't
    if command in getInternalCmds():
        return basicInfo

    docloc = mayaDocsLocation(version)
    if python:
        docloc = os.path.join(docloc, 'CommandsPython/%s.html' % (command))
    else:
        docloc = os.path.join(docloc, 'Commands/%s.html' % (command))

    try:
        with open(docloc) as f:
            parser = CommandDocParser(command)
            parser.feed(f.read())
    except IOError:
        _logger.debug("could not find docs for %s" % command)
        return basicInfo

    if parser.internal:
        return basicInfo

    example = parser.example
    example = example.rstrip()

    # start with basic info, gathered using mel help command, then update with info parsed from docs
    # we copy because we need access to the original basic info below
    basicFlags = basicInfo.get('flags', {})
    flags = basicInfo['flags'].copy()

    # if we have a "true" mel boolean flag, then getCmdInfoBasic will return
    # numArgs == 0, but parsing the PYTHON docs will return a numArgs of 1;
    # keep the numArgs of 0
    for flag, flagInfo in parser.flags.items():
        if flagInfo.get('args') == bool and flagInfo.get('numArgs') == 1:
            basicFlagInfo = basicFlags.get(flag, {})
            if (basicFlagInfo.get('args') == bool
                    and basicFlagInfo.get('numArgs') == 0):
                flagInfo['numArgs'] = 0
        docstring = flagInfo.get('docstring')
        if docstring:
            flagInfo['docstring'] = docstring.strip()

    flags.update(parser.flags)
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
        basicFlagData = basicFlags.get(flag)
        if basicFlagData:
            if 'args' in basicFlagData and 'numargs' in basicFlagData:
                flagData['args'] = basicFlagData['args']
                flagData['numArgs'] = basicFlagData['numArgs']
                if ('multiuse' in basicFlagData.get('modes', [])
                        and 'multiuse' not in flagData.get('modes', [])):
                    flagData.setdefault('modes', []).append('multiuse')

    shortFlags = basicInfo['shortFlags']
    res = {'flags': flags,
           'shortFlags': shortFlags,
           'description': parser.description,
           'example': example}
    try:
        res['removedFlags'] = basicInfo['removedFlags']
    except KeyError:
        pass
    return res


def fixCodeExamples(style='maya', force=False):
    """cycle through all examples from the maya docs, replacing maya.cmds with pymel and inserting pymel output.

    NOTE: this can only be run from gui mode
    WARNING: back up your preferences before running

    TODO: auto backup and restore of maya prefs
    """
    import shutil

    # some imports to get things into global / local namespaces
    import pymel
    import pymel.core as pm
    import pymel.core.windows as windows
    import maya.mel

    frozen_globals = dict(globals())
    # get a few more things into globals, as opposed to just locals. This is
    # in case there are functions defined, in the source - these will only have
    # access to globals, not locals
    frozen_globals['windows'] = windows
    frozen_globals['pm'] = pm
    frozen_globals['pymel'] = pymel
    frozen_globals['maya'] = maya

    frozen_locals = dict(locals())

    manipSize = cmds.manipOptions(q=1, handleSize=1)[0]
    manipScale = cmds.manipOptions(q=1, scale=1)[0]
    animOptions = []
    animOptions.append(cmds.animDisplay(q=1, timeCode=True))
    animOptions.append(cmds.animDisplay(q=1, timeCodeOffset=True))
    animOptions.append(cmds.animDisplay(q=1, modelUpdate=True))

    openWindows = cmds.lsUI(windows=True)
    examples = CmdExamplesCache().read()
    processedExamples = CmdProcessedExamplesCache().read()
    processedExamples = {} if processedExamples is None else processedExamples
    allCmds = set(examples.keys())
    # put commands that require manual interaction first
    manualCmds = ['fileBrowserDialog', 'fileDialog', 'fileDialog2', 'fontDialog']
    skipCmds = ['colorEditor', 'emit', 'finder', 'doBlur', 'messageLine', 'renderWindowEditor',
                'ogsRender', 'webBrowser', 'deleteAttrPattern', 'grabColor']
    allCmds.difference_update(manualCmds)
    sortedCmds = manualCmds + sorted(allCmds)

    succeeded = []
    failed = []
    skipped = []

    crashTempDir = startup._moduleJoin('cache', 'processedExamplesTemp')
    if os.path.isdir(crashTempDir):
        # If there are results in this dir, it's because we crashed last time
        # we ran. Read in the results here, and add them to the
        # processedExamples
        for command in os.listdir(crashTempDir):
            commandPath = os.path.join(crashTempDir, command)
            with open(commandPath, "rb") as f:
                example = f.read()
            processedExamples[command] = example
            os.remove(commandPath)
        # Now write out the results in the temp dir, into the processed cache
        CmdProcessedExamplesCache().write(processedExamples)
    else:
        os.mkdir(crashTempDir)

    def addProcessedExample(command, example):
        # first, write the temp result, in case we crash
        # Note that we COULD simply write to the CmdProcessedExamplesCache()
        # every time through, but this slows down the process considerably,
        # especially near the end, as we are having to re-write out ALL
        # the data, every time. It's much faster to just write out each temp
        # result to it's own file, then batch gather and add if we do crash.
        tempPath = os.path.join(crashTempDir, command)
        with open(tempPath, "wb") as f:
            f.write(example)
        # then add to the in-memory processedExamples
        processedExamples[command] = example

    command = None
    example = None
    commandsEvaluated = set()
    crashJournalPath = CmdProcessedExamplesCache.path() + '.crashjournal.txt'
    crashedCommand = None
    if os.path.isfile(crashJournalPath):
        with open(crashJournalPath, "r") as f:
            crashedCommand = f.read()
        os.remove(crashJournalPath)

    def tryEval(source, execOnly=False):
        if command == crashedCommand:
            # if last time we tried to run this command, but it crashed, AND
            # it was the FIRST command we tried to run, then we assume it will
            # crash again and skip it.
            _logger.info("skipping evaluation of command {} because it crashed"
                         " as the first command run".format(command))
            return False, None

        commandsEvaluated.add(command)
        # if this is the first command we've tried to evaluate, then
        # write the the crash journal.  Note that we don't write to the crash
        # journal for any commands OTHER than the first command, because:
        #     1) it's possible that a command ONLY crashes due to interaction
        #        with other commands previously run, and it might run
        #        successfully if it's the first command run
        #     2) If we crash on any command other than the first, we should at
        #        least have added some more entries to the processedExamples,
        #        which gets written out to disk on every command. This means
        #        that non-first-run commands that crash will either eventually
        #        start working (because some other command it interacts with is
        #        no longer run), or become the the first command run, at which
        #        point they will be skipped the next run
        if len(commandsEvaluated) == 1:
            with open(crashJournalPath, "w") as f:
                f.write(command)
        try:
            # _logger.debug("executing %s", source)
            try:
                if not execOnly:
                    try:
                        res = eval(source, globs, locs)
                        return True, res
                    except Exception:
                        pass
                exec(source, globs, locs)
                return True, None
            except Exception as e:
                _logger.info("stopping evaluation of command {}: {}".format(
                    command, e))
                _logger.info("full example:\n{}".format(example))
                if source != example:
                    _logger.info("failed line(s):\n{}".format(source))
                return False, None
        finally:
            # because we remove the journal in a finally block, it should ONLY
            # get left around if we hard crash inside the try (or there's some
            # sort of ioerror / perms error when we try to remove)
            if len(commandsEvaluated) == 1:
                os.remove(crashJournalPath)

    def tryExec(source):
        return tryEval(source, execOnly=True)[0]

    try:
        for command in sortedCmds:
            if not force and command in processedExamples:
                _logger.info("%s: already completed. skipping." % command)
                continue

            # within a command, we want to re-use globals and locals, so
            # each line can add to it, but
            globs = dict(frozen_globals)
            locs = dict(frozen_locals)

            example = examples[command]

            _logger.info("Starting command %s", command)

            if style == 'doctest':
                DOC_TEST_SKIP = ' #doctest: +SKIP'
            else:
                DOC_TEST_SKIP = ''

            # change from cmds to pymel
            reg = re.compile(r'\bcmds\.')
            example = example.replace('import maya.cmds as cmds', 'import pymel.core as pm' + DOC_TEST_SKIP, 1)
            example = reg.sub('pm.', example)

            # example = example.replace( 'import maya.cmds as cmds', 'import pymel as pm\npm.newFile(f=1) #fresh scene' )

            lines = example.split('\n')
            nonEmptyLines = any(x for x in lines if x.strip()
                                and not x.strip().startswith('#'))
            if not nonEmptyLines:
                _logger.info("removing empty example for command %s", command)
                examples.pop(command)
                addProcessedExample(command, '')
                continue

            skip = False
            if command in skipCmds:
                example = '\n'.join(lines)
                addProcessedExample(command, example)
                skip = True

            # lines.insert(1, 'pm.newFile(f=1) #fresh scene')
            # create a fresh scene. this does not need to be in the docstring
            # unless we plan on using it in doctests, which is probably
            # unrealistic
            cmds.file(new=1, f=1)

            newlines = []
            statement = []

            # narrowed down the commands that cause maya to crash to these prefixes
            if re.match('(dis)|(dyn)|(poly)', command):
                skip = True

            evaluate = not skip

            # gives a little leniency for where spaces are placed in the result line
            resultReg = re.compile(r'# Result:\s*(.*) #$')
            try:  # funky things can happen when executing maya code: some
                # exceptions somehow occur outside the eval/exec
                for i, line in enumerate(lines):
                    res = None
                    # replace with pymel results  '# Result: 1 #'
                    m = resultReg.match(line)
                    if m:
                        if evaluate is False:
                            newlines.append('    ' + line)
                    else:
                        if evaluate:
                            if line.strip().endswith(':') or line.startswith(' ') or line.startswith('\t'):
                                statement.append(line)
                            else:
                                # evaluate the compiled statement using exec,
                                # which can do multi-line if statements and so on
                                if statement:
                                    evaluate = tryExec('\n'.join(statement))
                                    if evaluate:
                                        # reset statement
                                        statement = []
                                if evaluate:
                                    evaluate, res = tryEval(line)
                        if style == 'doctest':
                            if line.startswith(' ') or line.startswith('\t'):
                                newlines.append('    ... ' + line)
                            else:
                                newlines.append('    >>> ' + line + DOC_TEST_SKIP)

                            if res is not None:
                                newlines.append('    ' + repr(res))
                        else:
                            newlines.append('    ' + line)
                            if res is not None:
                                newlines.append('    # Result: %r #' % (res,))

                if skip:
                    skipped.append(command)
                elif evaluate:
                    _logger.info("successful evaluation! %s", command)
                    succeeded.append(command)
                else:
                    failed.append((command, example))

                example = '\n'.join(newlines)
                addProcessedExample(command, example)
            except Exception as e:
                raise
                #_logger.info("FAILED: %s: %s" % (command, e) )

            # cleanup opened windows
            for ui in set(cmds.lsUI(windows=True)).difference(openWindows):
                try:
                    cmds.deleteUI(ui, window=True)
                except:
                    pass
    finally:
        # clean up the temp dir
        shutil.rmtree(crashTempDir)
        # then write out the final version of the cache, since we didn't crash!
        CmdProcessedExamplesCache().write(processedExamples)

    _logger.info("Done Fixing Examples")

    # restore manipulators and anim options
    print([manipSize, manipScale])
    cmds.manipOptions(handleSize=manipSize, scale=manipScale)
    print(animOptions)
    cmds.animDisplay(e=1, timeCode=animOptions[0], timeCodeOffset=animOptions[1], modelUpdate=animOptions[2])

    # CmdExamplesCache(examples)
    return {
        'succeeded': succeeded,
        'failed': failed,
        'skipped': skipped,
    }


def getModuleCommandList(category, version=None):
    from .parsers import CommandModuleDocParser
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
    commandFlags.sort()
    return commandFlags


def getModule(funcName, knownModuleCmds):
    # determine to which module this function belongs
    module = None
    if funcName in ['eval', 'file', 'filter', 'help', 'quit']:
        module = None
    elif funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
        module = 'context'
    # elif funcName in self.uiClassList:
    #    module = 'uiClass'
    # elif funcName in nodeHierarchyTree or funcName in nodeTypeToNodeCommand.values():
    #    module = 'node'
    else:
        for moduleName, commands in knownModuleCmds.items():
            if funcName in commands:
                module = moduleName
                break
        if module is None:
            if mm.eval('whatIs "%s"' % funcName) == 'Run Time Command':
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
        {'tangentConstraint': (makeCircle, makeCube),
         'poleVectorConstraint': (makeSphere, makeIk),
         'pointCurveConstraint': (makeEp, ),
         'skinCluster': (makeJoint, makeJoint, makeSphere),
         }

    constraintCmds = [x for x in dir(cmds)
                      if x.endswith('onstraint')
                      and not cmds.runTimeCommand(x, q=1, exists=1)
                      and x != 'polySelectConstraint']

    for constrCmd in constraintCmds:
        if constrCmd not in _cmdArgMakers:
            _cmdArgMakers[constrCmd] = (makeSphere, makeCube)

    return _cmdArgMakers


def nodeCreationCmd(func, nodeType):
    argMakers = cmdArgMakers()

    # compile the args list for node creation
    createArgs = argMakers.get(nodeType, [])
    if createArgs:
        createArgs = [argMaker() for argMaker in createArgs]

    # run the function
    _logger.debug('{}(*{!r})'.format(func.__name__, createArgs))

    return func(*createArgs)


def testNodeCmd(funcName, cmdInfo, nodeCmd=False, verbose=False):

    _logger.info(funcName.center(50, '='))

    if funcName in ['character', 'lattice', 'boneLattice', 'sculpt', 'wire']:
        _logger.debug("skipping")
        return cmdInfo

    # These cause crashes... confirmed that pointOnPolyConstraint still
    # crashes in 2012
    dangerousCmds = ['doBlur', 'pointOnPolyConstraint']
    if funcName in dangerousCmds:
        _logger.debug("skipping 'dangerous command'")
        return cmdInfo

    def _formatCmd(cmd, args, kwargs):
        args = [x.__repr__() for x in args]
        kwargs = ['%s=%s' % (key, val.__repr__()) for key, val in kwargs.items()]
        return '%s( %s )' % (cmd, ', '.join(args + kwargs))

    def _objectToType(result):
        "convert a an instance or list of instances to a python type or list of types"
        if isinstance(result, list):
            return [type(x) for x in result]
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
    allObjsBegin = set(cmds.ls(l=1))
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
                    _logger.info("%s: creation return values need unpacking" %
                                 funcName)
                    cmdInfo['resultNeedsUnpacking'] = True
                elif not obj:
                    raise ValueError("returned object is an empty list")
                objTransform = obj[0]
                obj = obj[-1]

            if obj is None:
                #emptyFunctions.append( funcName )
                raise ValueError("Returned object is None")

            elif not cmds.objExists(obj):
                raise ValueError("Returned object %s is Invalid" % obj)

            args = [obj]

    except (TypeError, RuntimeError, ValueError) as msg:
        _logger.debug("failed creation: %s", msg)

    else:
        objType = cmds.objectType(obj)
        #------------------
        # TESTING
        #------------------

        #(func, args, data) = cmdList[funcName]
        #(usePyNode, baseClsName, nodeName)
        flags = cmdInfo['flags']

        hasQueryFlag = 'query' in flags
        hasEditFlag = 'edit' in flags

        anyNumRe = re.compile(r'\d+')

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
            except KeyError as msg:
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
                    kwargs = {'query': True, flag: True}
                else:
                    kwargs = {flag: True}

                cmd = _formatCmd(funcName, flagargs, kwargs)
                try:
                    _logger.debug(cmd)
                    val = func(*flagargs, **kwargs)
                    #_logger.debug('val: %r' % (val,))
                    resultType = _objectToType(val)

                    # deal with unicode vs str
                    if PY2:
                        strUni = (str, unicode)
                        lStrUni = ([str], [unicode])
                        if (argtype in strUni and resultType in strUni)\
                                or (argtype in lStrUni and resultType in lStrUni):
                            # just ignore str/unicode diff, set resultType to match
                            resultType = argtype
                        elif argtype in strUni and resultType in lStrUni:
                            resultType[0] = argtype

                    # ensure symmetry between edit and query commands:
                    # if this flag is queryable and editable, then its queried value should be symmetric to its edit arguments
                    if 'edit' in modes and argtype != resultType:
                        # there are certain patterns of asymmetry which we can safely correct:
                        singleItemList = (isinstance(resultType, list)
                                          and len(resultType) == 1
                                          and 'multiuse' not in flagInfo.get('modes', []))

                        # [bool] --> bool
                        if singleItemList and resultType[0] == argtype:
                            _logger.info("%s, %s: query flag return values "
                                         "need unpacking" % (funcName, flag))
                            flagInfo['resultNeedsUnpacking'] = True
                            val = val[0]

                        # [int] --> bool
                        elif singleItemList and argtype in _castList and resultType[0] in _castList:
                            _logger.info("%s, %s: query flag return values "
                                         "need unpacking and casting" % (funcName, flag))
                            flagInfo['resultNeedsUnpacking'] = True
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val[0])

                        # int --> bool
                        elif argtype in _castList and resultType in _castList:
                            _logger.info("%s, %s: query flag return values "
                                         "need casting" % (funcName, flag))
                            flagInfo['resultNeedsCasting'] = True
                            val = argtype(val)
                        else:
                            # no valid corrections found
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

                except TypeError as msg:
                    # flag is no longer supported
                    if str(msg).startswith('Invalid flag'):
                        # if verbose:
                        _logger.info("removing flag %s %s %s", funcName, flag, msg)
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag, None)
                        flagInfo.pop(shortname, None)
                        modes = []  # stop edit from running
                    else:
                        _logger.info("Error running: {}".format(cmd))
                        _logger.info("\t" + str(msg).rstrip('\n'))
                        import traceback
                        _logger.debug(traceback.format_exc())
                    val = None

                except RuntimeError as msg:
                    _logger.info(cmd)
                    _logger.info("\tRuntimeError: " + str(msg).rstrip('\n'))
                    val = None
                except ValueError as msg:
                    _logger.info(cmd)
                    _logger.info("\tValueError: " + str(msg).rstrip('\n'))
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
                    # we use the value returned from query above as defaults
                    # for putting back in as edit args
                    # but if the return was empty we need to produce something to test on.
                    # NOTE: this is just a guess
                    if val is None:

                        if isinstance(argtype, list):
                            val = []
                            for typ in argtype:
                                if type == str or isinstance(type, basestring):
                                    val.append('persp')
                                else:
                                    if 'query' in modes:
                                        val.append(typ(0))
                                    # edit only, ensure that bool args are True
                                    else:
                                        val.append(typ(1))
                        else:
                            if argtype == str or isinstance(argtype, basestring):
                                val = 'persp'
                            elif 'query' in modes:
                                val = argtype(0)
                            else:
                                # edit only, ensure that bool args are True
                                val = argtype(1)

                    kwargs = {'edit': True, flag: val}
                    cmd = _formatCmd(funcName, args, kwargs)
                    _logger.debug(cmd)

                    # some commands will either delete or rename a node, ie:
                    #     spaceLocator(e=1, name=...)
                    #     container(e=1, removeContainer=True )
                    # ...which will then make subsequent cmds fail.
                    # To get around this, we need to undo the cmd.
                    try:
                        cmds.undoInfo(openChunk=True)
                        editResult = func(*args, **kwargs)
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
                except TypeError as msg:
                    if str(msg).startswith('Invalid flag'):
                        # if verbose:
                        # flag is no longer supported
                        _logger.info("removing flag %s %s %s", funcName, flag, msg)
                        shortname = flagInfo['shortname']
                        flagInfo.pop(flag, None)
                        flagInfo.pop(shortname, None)
                    else:
                        _logger.info(funcName)
                        _logger.info("\t" + str(msg).rstrip('\n'))
                        _logger.info("\tpredicted arg: %s", argtype)
                        if not 'query' in modes:
                            _logger.info("\tedit only")
                except RuntimeError as msg:
                    _logger.info(cmd)
                    _logger.info("\t" + str(msg).rstrip('\n'))
                    _logger.info("\tpredicted arg: %s", argtype)
                    if not 'query' in modes:
                        _logger.info("\tedit only")
                except ValueError as msg:
                    _logger.info(cmd)
                    _logger.info("\tValueError: " + str(msg).rstrip('\n'))
                    val = None
                else:
                    if 'edit' not in flagInfo['modes']:
                        flagInfo['modes'].append('edit')

    # cleanup
    allObjsEnd = set(cmds.ls(l=1))
    newObjs = list(allObjsEnd.difference(allObjsBegin))
    if newObjs:
        cmds.delete(newObjs)
    return cmdInfo


def _getNodeHierarchy(version=None):
    # type: (...) -> List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]]
    """
    get node hierarchy as a list of 3-value tuples:
        ( nodeType, parents, children )
    """
    import pymel.util.trees as trees
    import pymel.internal.apicache as apicache

    # We now have nodeType(isTypeName)! yay!
    inheritances = {}
    for nodeType in apicache._getAllMayaTypes():
        try:
            inheritances[nodeType] = apicache.getInheritance(nodeType)
        except apicache.ManipNodeTypeError:
            continue
        except Exception:
            print("Error getting inheritance: %s" % nodeType)
            raise

    parentTree = {}
    # Convert inheritance lists node=>parent dict
    for nodeType, inheritance in inheritances.items():
        for i in range(len(inheritance)):
            child = inheritance[i]
            if i == 0:
                if child == 'dependNode':
                    continue
                else:
                    parent = 'dependNode'
            else:
                parent = inheritance[i - 1]

            if child in parentTree:
                assert parentTree[child] == parent, (
                        "conflicting parents: node type '%s' previously "
                        "determined parent was '%s'. now '%s'" %
                        (child, parentTree[child], parent))
            else:
                parentTree[child] = parent
    nodeHierarchyTree = trees.treeFromDict(parentTree)
    # sort the tree, so we have consistent / comparable results
    nodeHierarchyTree.sort()
    return [
        (x.value,
         tuple(y.value for y in x.parents()),
         tuple(y.value for y in x.childs()))
        for x in nodeHierarchyTree.preorder()]


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
    ITEM_TYPES = {
        'nodeHierarchy': list,
        'uiClassList': list,
        'nodeCommandList': list,
    }

    def rebuild(self):
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

        from .parsers import mayaDocsLocation
        cmddocs = os.path.join(mayaDocsLocation(long_version), 'CommandsPython')
        assert os.path.exists(cmddocs), "Command documentation does not exist: %s" % cmddocs

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
        nodeFunctions = {x[0] for x in self.nodeHierarchy}
        nodeFunctions.update(x for x in nodeTypeToNodeCommand.values() if x)

        _logger.info("Rebuilding the list of Maya commands...")

        #nodeHierarchyTree = trees.IndexedTree(self.nodeHierarchy)
        self.uiClassList = UI_COMMANDS
        self.nodeCommandList = []
        tmpModuleCmds = {}
        for moduleName, longname in moduleNameShortToLong.items():
            tmpModuleCmds[moduleName] = getModuleCommandList(longname, long_version)

        tmpCmdlist = inspect.getmembers(cmds, callable)

        #self.moduleCmds = defaultdict(list)
        self.moduleCmds = dict((k, []) for k in moduleNameShortToLong.keys())
        self.moduleCmds.update({'other': [], 'runtime': [], 'context': [], 'uiClass': []})

        def addCommand(funcName):
            # type: (str) -> None
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
                        cmdInfo = testNodeCmd(funcName, cmdInfo, nodeCmd=True, verbose=True)
                    # elif module != 'context':
                    #    cmdInfo = testNodeCmd( funcName, cmdInfo, nodeCmd=False, verbose=True  )

            cmdInfo['type'] = module
            flags = getCallbackFlags(cmdInfo)
            if flags:
                cmdInfo['callbackFlags'] = flags

            self.cmdlist[funcName] = cmdInfo

            # # func, args, (usePyNode, baseClsName, nodeName)
            # # args = dictionary of command flags and their data
            # # usePyNode = determines whether the class returns its 'nodeName'
            # # or uses PyNode to dynamically return
            # # baseClsName = for commands which should generate a class, this is
            # # the name of the superclass to inherit nodeName = most creation
            # # commands return a node of the same name, this option is provided for the exceptions
            # try:
            #    self.cmdlist[funcName] = args, pymelCmdsList[funcName] )
            # except KeyError:
            #    # context commands generate a class based on unicode (which is triggered by passing 'None' to baseClsName)
            #    if funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
            #         self.cmdlist[funcName] = (funcName, args, (False, None, None) )
            #    else:
            #        self.cmdlist[funcName] = (funcName, args, () )

        for funcName, _ in tmpCmdlist:
            if funcName in pluginCommands:
                _logger.debug("command %s was a plugin command that should "
                              "have been unloaded - skipping" % funcName)
                continue
            addCommand(funcName)

        # split the cached data for lazy loading
        cmdDocList = {}
        examples = {}
        for cmdName, cmdInfo in self.cmdlist.items():
            try:
                examples[cmdName] = cmdInfo.pop('example')
            except KeyError:
                pass

            newCmdInfo = {}
            if 'description' in cmdInfo:
                newCmdInfo['description'] = cmdInfo.pop('description')
            newFlagInfo = {}
            if 'flags' in cmdInfo:
                for flag, flagInfo in cmdInfo['flags'].items():
                    newFlagInfo[flag] = {'docstring': flagInfo.pop('docstring')}
                newCmdInfo['flags'] = newFlagInfo

            if newCmdInfo:
                cmdDocList[cmdName] = newCmdInfo

        CmdDocsCache().write(cmdDocList)
        CmdExamplesCache().write(examples)

    def build(self):
        super(CmdCache, self).build()

        # corrections that are always made, to both loaded and freshly built caches
        util.mergeCascadingDicts(cmdlistOverrides, self.cmdlist)
        # add in any nodeCommands added after cache rebuild
        nodeCommandList = set(self.nodeCommandList)
        nodeCommandList.update(x for x in nodeTypeToNodeCommand.values() if x)
        self.nodeCommandList = sorted(nodeCommandList)

        for module, funcNames in moduleCommandAdditions.items():
            for funcName in funcNames:
                currModule = self.cmdlist[funcName]['type']
                if currModule != module:
                    self.cmdlist[funcName]['type'] = module
                    id = self.moduleCmds[currModule].index(funcName)
                    self.moduleCmds[currModule].pop(id)
                    self.moduleCmds[module].append(funcName)
        return (self.cmdlist, self.nodeHierarchy, self.uiClassList, self.nodeCommandList, self.moduleCmds)

    def _modifyTypes(self, data, predicate, converter):
        '''convert between class names and class objects'''
        cmdlist = data[self.itemIndex('cmdlist')]
        for cmdinfo in cmdlist.values():
            flags = cmdinfo.get('flags')
            if not flags:
                continue
            for flaginfo in flags.values():
                args = flaginfo.get('args')
                if not args:
                    continue
                if predicate(args):
                    flaginfo['args'] = converter(args)
                elif isinstance(args, list):
                    for i, arg in enumerate(args):
                        if predicate(arg):
                            args[i] = converter(arg)

    def fromRawData(self, data):
        # convert from string class names to class objects
        def isTypeStr(obj):
            return isinstance(obj, basestring) and obj.startswith('<type ') \
                   and obj.endswith('>')

        def fromTypeStr(typeStr):
            return startup.getImportableObject(typeStr[len('<type '):-1])

        self._modifyTypes(data, isTypeStr, fromTypeStr)
        return data

    def toRawData(self, data):
        # convert from class objects to string class names
        def toTypeStr(typeObj):
            return '<type {}>'.format(startup.getImportableName(typeObj))

        self._modifyTypes(data, callable, toTypeStr)
        return super(CmdCache, self).toRawData(data)

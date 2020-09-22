"""functions related to animation"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from past.builtins import basestring
import pymel.util as _util
import pymel.internal.factories as _factories
import pymel.core.general as _general

if False:
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]


def currentTime(*args, **kwargs):
    """
    Modifications:
        - if no args are provided, the command returns the current time
    """
    if not args and not kwargs:
        return cmds.currentTime(q=1)
    else:
        return cmds.currentTime(*args, **kwargs)


def getCurrentTime():
    """get the current time as a float"""
    return cmds.currentTime(q=1)


def setCurrentTime(time):
    """set the current time """
    return cmds.currentTime(time)


def listAnimatable(*args, **kwargs):
    """
    Modifications:
        - returns an empty list when the result is None
        - returns wrapped classes
    """
    return [_general.PyNode(x) for x in
            _util.listForNone(cmds.listAnimatable(*args, **kwargs))]


def keyframe(*args, **kwargs):
    """
    Modifications:
        - returns an empty list when the result is None
        - if both valueChange and timeChange are queried, the result will be a list of (time,value) pairs
    """
    res = _util.listForNone(cmds.keyframe(*args, **kwargs))
    if kwargs.get('query', kwargs.get('q', False) ) and \
            kwargs.get('valueChange', kwargs.get('vc', False)) and kwargs.get('timeChange', kwargs.get('tc', False)):
        return list(_util.pairIter(res))
    return res


def deformer(*args, **kwargs):
    return [_general.PyNode(x) for x in cmds.deformer(*args, **kwargs)]


def _constraint(func):
    def constraintWithWeightSyntax(*args, **kwargs):
        """
        Maya Bug Fix:
          - when queried, angle offsets would be returned in radians, not current angle unit

        Modifications:
          - added new syntax for querying the weight of a target object, by passing the constraint first::

                aimConstraint('pCube1_aimConstraint1', q=1, weight='pSphere1')
                aimConstraint('pCube1_aimConstraint1', q=1, weight=['pSphere1', 'pCylinder1'])
                aimConstraint('pCube1_aimConstraint1', q=1, weight=True)
        """
        if kwargs.get('query', kwargs.get('q', False) and len(args) == 1):
            # Fix the big with angle offset query always being in radians
            if kwargs.get('offset', kwargs.get('o', None)):
                return _general.getAttr(str(args[0]) + ".offset")

            # try seeing if we can apply the new weight query syntax
            targetObjects = kwargs.get('weight', kwargs.get('w', None))
            if targetObjects is not None:
                # old way caused KeyError if 'w' not in kwargs, even if 'weight' was!
                # targetObjects = kwargs.get( 'weight', kwargs['w'] )
                constraint = args[0]
                if 'constraint' in cmds.nodeType(constraint, inherited=1):
                    if targetObjects is True or (
                            # formerly, we allowed 'weight=[]' instead of
                            # 'weight=True' - while this is somewhat more
                            # confusing, continue to support it for backwards
                            # compatibility
                            _util.isIterable(targetObjects)
                            and not targetObjects):
                        targetObjects = func(constraint, q=1, targetList=1)
                    elif _util.isIterable(targetObjects):
                        # convert to list, in case it isn't one
                        targetObjects = list(targetObjects)
                    else:
                        targetObjects = [targetObjects]

                    constraintObj = cmds.listConnections(constraint + '.constraintParentInverseMatrix', s=1, d=0)[0]
                    args = targetObjects + [constraintObj]
                    kwargs.pop('w', None)
                    kwargs['weight'] = True
        res = func(*args, **kwargs)
        if kwargs.get('query', kwargs.get('q', False) and len(args) == 1):
            if kwargs.get('weightAliasList', kwargs.get('wal', None)):
                res = [_general.Attribute(args[0] + '.' + attr) for attr in res]
            elif kwargs.get('worldUpObject', kwargs.get('wuo', None)):
                res = _factories.unwrapToPyNode(res)
            elif kwargs.get('targetList', kwargs.get('tl', None)):
                res = _factories.toPyNodeList(res)
        return res

    constraintWithWeightSyntax.__name__ = func.__name__
    return constraintWithWeightSyntax


for contstraintCmdName in ('''aimConstraint geometryConstraint normalConstraint
                              orientConstraint parentConstraint pointConstraint
                              pointOnPolyConstraint poleVectorConstraint
                              scaleConstraint tangentConstraint''').split():
    cmd = getattr(cmds, contstraintCmdName, None)
    if cmd:
        globals()[contstraintCmdName] = _constraint(cmd)


def ikHandle(*args, **kwargs):
    """
    Modifications:
        - always converts to PyNodes in create mode, even though results are
          non-unique short names
    """
    from . import nodetypes
    from maya.OpenMaya import MGlobal

    res = cmds.ikHandle(*args, **kwargs)

    # unfortunately, ikHandle returns non-unique names... however, it
    # doesn't support a parent option - so we can just throw a '|' in front
    # of the first return result (the ikHandle itself) to get a unique name
    # We then need to track through it's connections to find the endEffector...

    if kwargs.get('query', kwargs.get('q', False)):
        if kwargs.get('endEffector', kwargs.get('ee', False)):
            res = _factories.toPyNode(res)
        elif kwargs.get('jointList', kwargs.get('jl', False)):
            res = _factories.toPyNodeList(res)
    elif (not kwargs.get('edit', kwargs.get('e', False))
            and isinstance(res, list) and len(res) == 2
            and all(isinstance(x, basestring) for x in res)):
        handleName, effectorName = res
        # ikHandle doesn't support a parent kwarg, so result should always be
        # grouped under the world...
        handleNode = _factories.toPyNode('|' + handleName)
        # unfortunately, effector location is a little harder to predict. but
        # can find it by following connections...
        effectorNode = handleNode.attr('endEffector').inputs()[0]
        if effectorNode.nodeName() == effectorName:
            res = [handleNode, effectorNode]
        else:
            MGlobal.displayWarning(
                "Warning: returned ikHandle %r was connected to effector %r, "
                "which did not match returned effector name %r"
                % (handleName, effectorNode.shortName(), effectorName))
    return res

# ------ Do not edit below this line --------

_aimConstraint = aimConstraint

@_factories.addCmdDocs
def aimConstraint(*args, **kwargs):
    res = _aimConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def animCurveEditor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dcc', 'denormalizeCurvesCommand', 'm', 'menu', 'ncc', 'normalizeCurvesCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.animCurveEditor(*args, **kwargs)
    return res

animDisplay = _factories.getCmdFunc('animDisplay')

@_factories.addCmdDocs
def animLayer(*args, **kwargs):
    res = cmds.animLayer(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    wraps = _factories.simpleCommandWraps['animLayer']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

animView = _factories.getCmdFunc('animView')

applyTake = _factories.getCmdFunc('applyTake')

autoKeyframe = _factories.getCmdFunc('autoKeyframe')

backgroundEvaluationManager = _factories.getCmdFunc('backgroundEvaluationManager')

bakeClip = _factories.getCmdFunc('bakeClip')

@_factories.addCmdDocs
def bakeDeformer(*args, **kwargs):
    for flag in ['customRangeOfMotion', 'rom']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.bakeDeformer(*args, **kwargs)
    return res

@_factories.addCmdDocs
def bakeResults(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.bakeResults(*args, **kwargs)
    return res

@_factories.addCmdDocs
def bakeSimulation(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.bakeSimulation(*args, **kwargs)
    return res

bindSkin = _factories.getCmdFunc('bindSkin')

@_factories.addCmdDocs
def blendShape(*args, **kwargs):
    res = cmds.blendShape(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

blendShapeEditor = _factories.getCmdFunc('blendShapeEditor')

@_factories.addCmdDocs
def blendShapePanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.blendShapePanel(*args, **kwargs)
    return res

@_factories.addCmdDocs
def blendTwoAttr(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.blendTwoAttr(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def boneLattice(*args, **kwargs):
    res = cmds.boneLattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def bufferCurve(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.bufferCurve(*args, **kwargs)
    return res

buildBookmarkMenu = _factories.getCmdFunc('buildBookmarkMenu')

buildKeyframeMenu = _factories.getCmdFunc('buildKeyframeMenu')

@_factories.addCmdDocs
def character(*args, **kwargs):
    res = cmds.character(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def characterMap(*args, **kwargs):
    res = cmds.characterMap(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

characterize = _factories.getCmdFunc('characterize')

@_factories.addCmdDocs
def choice(*args, **kwargs):
    res = cmds.choice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

clip = _factories.getCmdFunc('clip')

clipEditor = _factories.getCmdFunc('clipEditor')

clipMatching = _factories.getCmdFunc('clipMatching')

clipSchedule = _factories.getCmdFunc('clipSchedule')

@_factories.addCmdDocs
def clipSchedulerOutliner(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.clipSchedulerOutliner(*args, **kwargs)
    return res

@_factories.addCmdDocs
def cluster(*args, **kwargs):
    res = cmds.cluster(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def combinationShape(*args, **kwargs):
    res = cmds.combinationShape(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

connectJoint = _factories.getCmdFunc('connectJoint')

@_factories.addCmdDocs
def controller(*args, **kwargs):
    res = cmds.controller(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

copyDeformerWeights = _factories.getCmdFunc('copyDeformerWeights')

copyFlexor = _factories.getCmdFunc('copyFlexor')

@_factories.addCmdDocs
def copyKey(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.copyKey(*args, **kwargs)
    return res

copySkinWeights = _factories.getCmdFunc('copySkinWeights')

currentTime = _factories.addCmdDocs(currentTime)

@_factories.addCmdDocs
def cutKey(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.cutKey(*args, **kwargs)
    return res

@_factories.addCmdDocs
def dagPose(*args, **kwargs):
    res = cmds.dagPose(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

defineDataServer = _factories.getCmdFunc('defineDataServer')

defineVirtualDevice = _factories.getCmdFunc('defineVirtualDevice')

@_factories.addCmdDocs
def deformableShape(*args, **kwargs):
    res = cmds.deformableShape(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

deformer = _factories.addCmdDocs(deformer)

deformerWeights = _factories.getCmdFunc('deformerWeights')

@_factories.addCmdDocs
def deltaMush(*args, **kwargs):
    res = cmds.deltaMush(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    if isinstance(res, list) and len(res) == 1:
        if kwargs.get('query', kwargs.get('q', False)):
            # unpack for specific query flags
            unpackFlags = {'en', 'envelope', 'inwardConstraint', 'iwc', 'outwardConstraint', 'owc', 'pbv', 'pinBorderVertices', 'smoothingStep', 'ss'}
            if not unpackFlags.isdisjoint(kwargs):
                res = res[0]
        else:
            # unpack create/edit result
            res = res[0]
    return res

deviceManager = _factories.getCmdFunc('deviceManager')

disconnectJoint = _factories.getCmdFunc('disconnectJoint')

dopeSheetEditor = _factories.getCmdFunc('dopeSheetEditor')

@_factories.addCmdDocs
def dropoffLocator(*args, **kwargs):
    res = cmds.dropoffLocator(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

effector = _factories.getCmdFunc('effector')

enableDevice = _factories.getCmdFunc('enableDevice')

evaluationManager = _factories.getCmdFunc('evaluationManager')

evaluator = _factories.getCmdFunc('evaluator')

filterCurve = _factories.getCmdFunc('filterCurve')

findDeformers = _factories.getCmdFunc('findDeformers')

@_factories.addCmdDocs
def findKeyframe(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.findKeyframe(*args, **kwargs)
    return res

@_factories.addCmdDocs
def flexor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dc', 'deformerCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.flexor(*args, **kwargs)
    return res

@_factories.addCmdDocs
def flow(*args, **kwargs):
    res = cmds.flow(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

freezeOptions = _factories.getCmdFunc('freezeOptions')

@_factories.addCmdDocs
def geomBind(*args, **kwargs):
    res = cmds.geomBind(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_geometryConstraint = geometryConstraint

@_factories.addCmdDocs
def geometryConstraint(*args, **kwargs):
    res = _geometryConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

ghosting = _factories.getCmdFunc('ghosting')

hikGlobals = _factories.getCmdFunc('hikGlobals')

_ikHandle = ikHandle

@_factories.addCmdDocs
def ikHandle(*args, **kwargs):
    res = _ikHandle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ikHandleDisplayScale = _factories.getCmdFunc('ikHandleDisplayScale')

@_factories.addCmdDocs
def ikSolver(*args, **kwargs):
    res = cmds.ikSolver(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def ikSystem(*args, **kwargs):
    res = cmds.ikSystem(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ikSystemInfo = _factories.getCmdFunc('ikSystemInfo')

ikfkDisplayMethod = _factories.getCmdFunc('ikfkDisplayMethod')

insertJoint = _factories.getCmdFunc('insertJoint')

@_factories.addCmdDocs
def joint(*args, **kwargs):
    res = cmds.joint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    if isinstance(res, list) and len(res) == 1:
        # unpack for specific query flags
        unpackFlags = {'angleX', 'angleY', 'angleZ', 'ax', 'ay', 'az', 'rad', 'radius', 'stiffnessX', 'stiffnessY', 'stiffnessZ', 'stx', 'sty', 'stz'}
        if kwargs.get('query', kwargs.get('q', False)) and not unpackFlags.isdisjoint(kwargs):
            res = res[0]
    return res

@_factories.addCmdDocs
def jointCluster(*args, **kwargs):
    res = cmds.jointCluster(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

jointDisplayScale = _factories.getCmdFunc('jointDisplayScale')

@_factories.addCmdDocs
def jointLattice(*args, **kwargs):
    res = cmds.jointLattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def keyTangent(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.keyTangent(*args, **kwargs)
    return res

_keyframe = keyframe

@_factories.addCmdDocs
def keyframe(*args, **kwargs):
    for flag in ['index', 't', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = _keyframe(*args, **kwargs)
    return res

@_factories.addCmdDocs
def keyframeOutliner(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.keyframeOutliner(*args, **kwargs)
    return res

@_factories.addCmdDocs
def keyframeStats(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.keyframeStats(*args, **kwargs)
    return res

@_factories.addCmdDocs
def keyingGroup(*args, **kwargs):
    res = cmds.keyingGroup(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def lattice(*args, **kwargs):
    res = cmds.lattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

listAnimatable = _factories.addCmdDocs(listAnimatable)

marker = _factories.getCmdFunc('marker')

mimicManipulation = _factories.getCmdFunc('mimicManipulation')

mirrorJoint = _factories.getCmdFunc('mirrorJoint')

movIn = _factories.getCmdFunc('movIn')

@_factories.addCmdDocs
def movOut(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.movOut(*args, **kwargs)
    return res

movieInfo = _factories.getCmdFunc('movieInfo')

@_factories.addCmdDocs
def mute(*args, **kwargs):
    res = cmds.mute(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def nonLinear(*args, **kwargs):
    res = cmds.nonLinear(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_normalConstraint = normalConstraint

@_factories.addCmdDocs
def normalConstraint(*args, **kwargs):
    res = _normalConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_orientConstraint = orientConstraint

@_factories.addCmdDocs
def orientConstraint(*args, **kwargs):
    res = _orientConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def pairBlend(*args, **kwargs):
    res = cmds.pairBlend(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_parentConstraint = parentConstraint

@_factories.addCmdDocs
def parentConstraint(*args, **kwargs):
    res = _parentConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def pasteKey(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.pasteKey(*args, **kwargs)
    return res

pathAnimation = _factories.getCmdFunc('pathAnimation')

percent = _factories.getCmdFunc('percent')

play = _factories.getCmdFunc('play')

playbackOptions = _factories.getCmdFunc('playbackOptions')

playblast = _factories.getCmdFunc('playblast')

_pointConstraint = pointConstraint

@_factories.addCmdDocs
def pointConstraint(*args, **kwargs):
    res = _pointConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_pointOnPolyConstraint = pointOnPolyConstraint

@_factories.addCmdDocs
def pointOnPolyConstraint(*args, **kwargs):
    res = _pointOnPolyConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_poleVectorConstraint = poleVectorConstraint

@_factories.addCmdDocs
def poleVectorConstraint(*args, **kwargs):
    res = _poleVectorConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

polyUniteSkinned = _factories.getCmdFunc('polyUniteSkinned')

pose = _factories.getCmdFunc('pose')

poseEditor = _factories.getCmdFunc('poseEditor')

@_factories.addCmdDocs
def posePanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.posePanel(*args, **kwargs)
    return res

readTake = _factories.getCmdFunc('readTake')

recordDevice = _factories.getCmdFunc('recordDevice')

removeJoint = _factories.getCmdFunc('removeJoint')

reorderDeformers = _factories.getCmdFunc('reorderDeformers')

reroot = _factories.getCmdFunc('reroot')

rotationInterpolation = _factories.getCmdFunc('rotationInterpolation')

_scaleConstraint = scaleConstraint

@_factories.addCmdDocs
def scaleConstraint(*args, **kwargs):
    res = _scaleConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def scaleKey(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.scaleKey(*args, **kwargs)
    return res

@_factories.addCmdDocs
def sculpt(*args, **kwargs):
    res = cmds.sculpt(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

sculptTarget = _factories.getCmdFunc('sculptTarget')

@_factories.addCmdDocs
def sequenceManager(*args, **kwargs):
    res = cmds.sequenceManager(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

setDrivenKeyframe = _factories.getCmdFunc('setDrivenKeyframe')

setInfinity = _factories.getCmdFunc('setInfinity')

setKeyPath = _factories.getCmdFunc('setKeyPath')

setKeyframe = _factories.getCmdFunc('setKeyframe')

setKeyframeBlendshapeTargetWts = _factories.getCmdFunc('setKeyframeBlendshapeTargetWts')

shapeEditor = _factories.getCmdFunc('shapeEditor')

@_factories.addCmdDocs
def shapePanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shapePanel(*args, **kwargs)
    return res

@_factories.addCmdDocs
def shot(*args, **kwargs):
    res = cmds.shot(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

shotRipple = _factories.getCmdFunc('shotRipple')

@_factories.addCmdDocs
def simplify(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.simplify(*args, **kwargs)
    return res

skeletonEmbed = _factories.getCmdFunc('skeletonEmbed')

@_factories.addCmdDocs
def skinCluster(*args, **kwargs):
    res = cmds.skinCluster(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    wraps = _factories.simpleCommandWraps['skinCluster']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

skinPercent = _factories.getCmdFunc('skinPercent')

@_factories.addCmdDocs
def snapKey(*args, **kwargs):
    for flag in ['t', 'time']:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    res = cmds.snapKey(*args, **kwargs)
    return res

@_factories.addCmdDocs
def snapshot(*args, **kwargs):
    res = cmds.snapshot(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def softMod(*args, **kwargs):
    res = cmds.softMod(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

sound = _factories.getCmdFunc('sound')

substituteGeometry = _factories.getCmdFunc('substituteGeometry')

_tangentConstraint = tangentConstraint

@_factories.addCmdDocs
def tangentConstraint(*args, **kwargs):
    res = _tangentConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def tension(*args, **kwargs):
    res = cmds.tension(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    if isinstance(res, list) and len(res) == 1:
        if kwargs.get('query', kwargs.get('q', False)):
            # unpack for specific query flags
            unpackFlags = {'en', 'envelope', 'inwardConstraint', 'iwc', 'outwardConstraint', 'owc', 'pbv', 'pinBorderVertices', 'smoothingStep', 'ss'}
            if not unpackFlags.isdisjoint(kwargs):
                res = res[0]
        else:
            # unpack create/edit result
            res = res[0]
    return res

@_factories.addCmdDocs
def textureDeformer(*args, **kwargs):
    res = cmds.textureDeformer(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def timeEditor(*args, **kwargs):
    res = cmds.timeEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def timeEditorAnimSource(*args, **kwargs):
    res = cmds.timeEditorAnimSource(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

timeEditorBakeClips = _factories.getCmdFunc('timeEditorBakeClips')

@_factories.addCmdDocs
def timeEditorClip(*args, **kwargs):
    res = cmds.timeEditorClip(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

timeEditorClipLayer = _factories.getCmdFunc('timeEditorClipLayer')

timeEditorClipOffset = _factories.getCmdFunc('timeEditorClipOffset')

timeEditorComposition = _factories.getCmdFunc('timeEditorComposition')

@_factories.addCmdDocs
def timeEditorPanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['m', 'menu']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.timeEditorPanel(*args, **kwargs)
    return res

@_factories.addCmdDocs
def timeEditorTracks(*args, **kwargs):
    res = cmds.timeEditorTracks(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def timeWarp(*args, **kwargs):
    res = cmds.timeWarp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ubercam = _factories.getCmdFunc('ubercam')

volumeBind = _factories.getCmdFunc('volumeBind')

@_factories.addCmdDocs
def wire(*args, **kwargs):
    res = cmds.wire(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

wrinkle = _factories.getCmdFunc('wrinkle')

writeTake = _factories.getCmdFunc('writeTake')

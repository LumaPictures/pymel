"""functions related to animation"""

import pymel.util as _util
import pymel.internal.factories as _factories
import general as _general
import pymel.versions as versions

import pymel.internal.pmcmds as cmds


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
    return map(_general.PyNode,
               _util.listForNone(cmds.listAnimatable(*args, **kwargs)))


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
    return map(_general.PyNode, cmds.deformer(*args, **kwargs))


def _constraint(func):
    def constraintWithWeightSyntax(*args, **kwargs):
        """
        Maya Bug Fix:
          - when queried, angle offsets would be returned in radians, not current angle unit

        Modifications:
          - added new syntax for querying the weight of a target object, by passing the constraint first::

                aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
                aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
                aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
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
                    if not _util.isIterable(targetObjects):
                        targetObjects = [targetObjects]
                    elif not targetObjects:
                        targetObjects = func(constraint, q=1, targetList=1)

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

    constraint = constraintWithWeightSyntax
    constraint.__name__ = func.__name__
    return constraint


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
    import nodetypes
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

@_factories._addCmdDocs
def aimConstraint(*args, **kwargs):
    res = _aimConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
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

animDisplay = _factories._addCmdDocs('animDisplay')

@_factories._addCmdDocs
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

animView = _factories._addCmdDocs('animView')

applyTake = _factories._addCmdDocs('applyTake')

autoKeyframe = _factories._addCmdDocs('autoKeyframe')

bakeClip = _factories._addCmdDocs('bakeClip')

bakeDeformer = _factories._addCmdDocs('bakeDeformer')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

bindSkin = _factories._addCmdDocs('bindSkin')

@_factories._addCmdDocs
def blendShape(*args, **kwargs):
    res = cmds.blendShape(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

blendShapeEditor = _factories._addCmdDocs('blendShapeEditor')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def boneLattice(*args, **kwargs):
    res = cmds.boneLattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
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

buildBookmarkMenu = _factories._addCmdDocs('buildBookmarkMenu')

buildKeyframeMenu = _factories._addCmdDocs('buildKeyframeMenu')

@_factories._addCmdDocs
def character(*args, **kwargs):
    res = cmds.character(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def characterMap(*args, **kwargs):
    res = cmds.characterMap(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

characterize = _factories._addCmdDocs('characterize')

@_factories._addCmdDocs
def choice(*args, **kwargs):
    res = cmds.choice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

clip = _factories._addCmdDocs('clip')

clipEditor = _factories._addCmdDocs('clipEditor')

clipMatching = _factories._addCmdDocs('clipMatching')

clipSchedule = _factories._addCmdDocs('clipSchedule')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def cluster(*args, **kwargs):
    res = cmds.cluster(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def combinationShape(*args, **kwargs):
    res = cmds.combinationShape(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

connectJoint = _factories._addCmdDocs('connectJoint')

@_factories._addCmdDocs
def controller(*args, **kwargs):
    res = cmds.controller(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

copyDeformerWeights = _factories._addCmdDocs('copyDeformerWeights')

copyFlexor = _factories._addCmdDocs('copyFlexor')

@_factories._addCmdDocs
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

copySkinWeights = _factories._addCmdDocs('copySkinWeights')

currentTime = _factories._addCmdDocs(currentTime)

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def dagPose(*args, **kwargs):
    res = cmds.dagPose(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

defineDataServer = _factories._addCmdDocs('defineDataServer')

defineVirtualDevice = _factories._addCmdDocs('defineVirtualDevice')

deformer = _factories._addCmdDocs(deformer)

deformerWeights = _factories._addCmdDocs('deformerWeights')

@_factories._addCmdDocs
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

deviceManager = _factories._addCmdDocs('deviceManager')

disconnectJoint = _factories._addCmdDocs('disconnectJoint')

dopeSheetEditor = _factories._addCmdDocs('dopeSheetEditor')

@_factories._addCmdDocs
def dropoffLocator(*args, **kwargs):
    res = cmds.dropoffLocator(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

effector = _factories._addCmdDocs('effector')

enableDevice = _factories._addCmdDocs('enableDevice')

evaluationManager = _factories._addCmdDocs('evaluationManager')

evaluator = _factories._addCmdDocs('evaluator')

filterCurve = _factories._addCmdDocs('filterCurve')

findDeformers = _factories._addCmdDocs('findDeformers')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def flow(*args, **kwargs):
    res = cmds.flow(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

freezeOptions = _factories._addCmdDocs('freezeOptions')

@_factories._addCmdDocs
def geomBind(*args, **kwargs):
    res = cmds.geomBind(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_geometryConstraint = geometryConstraint

@_factories._addCmdDocs
def geometryConstraint(*args, **kwargs):
    res = _geometryConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

hikGlobals = _factories._addCmdDocs('hikGlobals')

_ikHandle = ikHandle

@_factories._addCmdDocs
def ikHandle(*args, **kwargs):
    res = _ikHandle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ikHandleDisplayScale = _factories._addCmdDocs('ikHandleDisplayScale')

@_factories._addCmdDocs
def ikSolver(*args, **kwargs):
    res = cmds.ikSolver(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def ikSystem(*args, **kwargs):
    res = cmds.ikSystem(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ikSystemInfo = _factories._addCmdDocs('ikSystemInfo')

ikfkDisplayMethod = _factories._addCmdDocs('ikfkDisplayMethod')

insertJoint = _factories._addCmdDocs('insertJoint')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def jointCluster(*args, **kwargs):
    res = cmds.jointCluster(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

jointDisplayScale = _factories._addCmdDocs('jointDisplayScale')

@_factories._addCmdDocs
def jointLattice(*args, **kwargs):
    res = cmds.jointLattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def keyingGroup(*args, **kwargs):
    res = cmds.keyingGroup(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def lattice(*args, **kwargs):
    res = cmds.lattice(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

listAnimatable = _factories._addCmdDocs(listAnimatable)

marker = _factories._addCmdDocs('marker')

mirrorJoint = _factories._addCmdDocs('mirrorJoint')

movIn = _factories._addCmdDocs('movIn')

@_factories._addCmdDocs
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

movieInfo = _factories._addCmdDocs('movieInfo')

@_factories._addCmdDocs
def mute(*args, **kwargs):
    res = cmds.mute(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def nonLinear(*args, **kwargs):
    res = cmds.nonLinear(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_normalConstraint = normalConstraint

@_factories._addCmdDocs
def normalConstraint(*args, **kwargs):
    res = _normalConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_orientConstraint = orientConstraint

@_factories._addCmdDocs
def orientConstraint(*args, **kwargs):
    res = _orientConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def pairBlend(*args, **kwargs):
    res = cmds.pairBlend(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

_parentConstraint = parentConstraint

@_factories._addCmdDocs
def parentConstraint(*args, **kwargs):
    res = _parentConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
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

pathAnimation = _factories._addCmdDocs('pathAnimation')

percent = _factories._addCmdDocs('percent')

play = _factories._addCmdDocs('play')

playbackOptions = _factories._addCmdDocs('playbackOptions')

playblast = _factories._addCmdDocs('playblast')

_pointConstraint = pointConstraint

@_factories._addCmdDocs
def pointConstraint(*args, **kwargs):
    res = _pointConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_pointOnPolyConstraint = pointOnPolyConstraint

@_factories._addCmdDocs
def pointOnPolyConstraint(*args, **kwargs):
    res = _pointOnPolyConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

_poleVectorConstraint = poleVectorConstraint

@_factories._addCmdDocs
def poleVectorConstraint(*args, **kwargs):
    res = _poleVectorConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

polyUniteSkinned = _factories._addCmdDocs('polyUniteSkinned')

pose = _factories._addCmdDocs('pose')

poseEditor = _factories._addCmdDocs('poseEditor')

@_factories._addCmdDocs
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

readTake = _factories._addCmdDocs('readTake')

recordDevice = _factories._addCmdDocs('recordDevice')

removeJoint = _factories._addCmdDocs('removeJoint')

reorderDeformers = _factories._addCmdDocs('reorderDeformers')

reroot = _factories._addCmdDocs('reroot')

rotationInterpolation = _factories._addCmdDocs('rotationInterpolation')

_scaleConstraint = scaleConstraint

@_factories._addCmdDocs
def scaleConstraint(*args, **kwargs):
    res = _scaleConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def sculpt(*args, **kwargs):
    res = cmds.sculpt(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

sculptTarget = _factories._addCmdDocs('sculptTarget')

@_factories._addCmdDocs
def sequenceManager(*args, **kwargs):
    res = cmds.sequenceManager(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

setDrivenKeyframe = _factories._addCmdDocs('setDrivenKeyframe')

setInfinity = _factories._addCmdDocs('setInfinity')

setKeyPath = _factories._addCmdDocs('setKeyPath')

setKeyframe = _factories._addCmdDocs('setKeyframe')

setKeyframeBlendshapeTargetWts = _factories._addCmdDocs('setKeyframeBlendshapeTargetWts')

shapeEditor = _factories._addCmdDocs('shapeEditor')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def shot(*args, **kwargs):
    res = cmds.shot(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

shotRipple = _factories._addCmdDocs('shotRipple')

@_factories._addCmdDocs
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

skeletonEmbed = _factories._addCmdDocs('skeletonEmbed')

@_factories._addCmdDocs
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

skinPercent = _factories._addCmdDocs('skinPercent')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def snapshot(*args, **kwargs):
    res = cmds.snapshot(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def softMod(*args, **kwargs):
    res = cmds.softMod(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

sound = _factories._addCmdDocs('sound')

substituteGeometry = _factories._addCmdDocs('substituteGeometry')

_tangentConstraint = tangentConstraint

@_factories._addCmdDocs
def tangentConstraint(*args, **kwargs):
    res = _tangentConstraint(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def textureDeformer(*args, **kwargs):
    res = cmds.textureDeformer(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def timeEditor(*args, **kwargs):
    res = cmds.timeEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def timeEditorAnimSource(*args, **kwargs):
    res = cmds.timeEditorAnimSource(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

timeEditorBakeClips = _factories._addCmdDocs('timeEditorBakeClips')

@_factories._addCmdDocs
def timeEditorClip(*args, **kwargs):
    res = cmds.timeEditorClip(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

timeEditorClipLayer = _factories._addCmdDocs('timeEditorClipLayer')

timeEditorClipOffset = _factories._addCmdDocs('timeEditorClipOffset')

timeEditorComposition = _factories._addCmdDocs('timeEditorComposition')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def timeEditorTracks(*args, **kwargs):
    res = cmds.timeEditorTracks(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def timeWarp(*args, **kwargs):
    res = cmds.timeWarp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

ubercam = _factories._addCmdDocs('ubercam')

volumeBind = _factories._addCmdDocs('volumeBind')

@_factories._addCmdDocs
def wire(*args, **kwargs):
    res = cmds.wire(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

wrinkle = _factories._addCmdDocs('wrinkle')

writeTake = _factories._addCmdDocs('writeTake')

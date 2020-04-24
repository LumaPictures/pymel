"""
Contains all context command functions (previously 'ctx').
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pymel.internal.factories as _factories
if False:
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]


# ------ Do not edit below this line --------

alignCtx = _factories.getCmdFunc('alignCtx')

arcLenDimContext = _factories.getCmdFunc('arcLenDimContext')

@_factories.addCmdDocs
def art3dPaintCtx(*args, **kwargs):
    res = cmds.art3dPaintCtx(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['art3dPaintCtx']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def artAttrCtx(*args, **kwargs):
    res = cmds.artAttrCtx(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['artAttrCtx']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

artAttrPaintVertexCtx = _factories.getCmdFunc('artAttrPaintVertexCtx')

artAttrSkinPaintCtx = _factories.getCmdFunc('artAttrSkinPaintCtx')

artBaseCtx = _factories.getCmdFunc('artBaseCtx')

artFluidAttrCtx = _factories.getCmdFunc('artFluidAttrCtx')

artPuttyCtx = _factories.getCmdFunc('artPuttyCtx')

artSelectCtx = _factories.getCmdFunc('artSelectCtx')

artSetPaintCtx = _factories.getCmdFunc('artSetPaintCtx')

@_factories.addCmdDocs
def artUserPaintCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'chunkCommand', 'gac', 'getArrayAttrCommand', 'getSurfaceCommand', 'getValueCommand', 'gsc', 'gvc', 'sac', 'setArrayValueCommand', 'setValueCommand', 'svc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.artUserPaintCtx(*args, **kwargs)
    return res

blendCtx = _factories.getCmdFunc('blendCtx')

boxDollyCtx = _factories.getCmdFunc('boxDollyCtx')

boxZoomCtx = _factories.getCmdFunc('boxZoomCtx')

clipEditorCurrentTimeCtx = _factories.getCmdFunc('clipEditorCurrentTimeCtx')

createNurbsCircleCtx = _factories.getCmdFunc('createNurbsCircleCtx')

createNurbsConeCtx = _factories.getCmdFunc('createNurbsConeCtx')

createNurbsCubeCtx = _factories.getCmdFunc('createNurbsCubeCtx')

createNurbsCylinderCtx = _factories.getCmdFunc('createNurbsCylinderCtx')

createNurbsPlaneCtx = _factories.getCmdFunc('createNurbsPlaneCtx')

createNurbsSphereCtx = _factories.getCmdFunc('createNurbsSphereCtx')

createNurbsSquareCtx = _factories.getCmdFunc('createNurbsSquareCtx')

createNurbsTorusCtx = _factories.getCmdFunc('createNurbsTorusCtx')

createPolyConeCtx = _factories.getCmdFunc('createPolyConeCtx')

createPolyCubeCtx = _factories.getCmdFunc('createPolyCubeCtx')

createPolyCylinderCtx = _factories.getCmdFunc('createPolyCylinderCtx')

createPolyHelixCtx = _factories.getCmdFunc('createPolyHelixCtx')

createPolyPipeCtx = _factories.getCmdFunc('createPolyPipeCtx')

createPolyPlaneCtx = _factories.getCmdFunc('createPolyPlaneCtx')

createPolyPlatonicSolidCtx = _factories.getCmdFunc('createPolyPlatonicSolidCtx')

createPolyPrismCtx = _factories.getCmdFunc('createPolyPrismCtx')

createPolyPyramidCtx = _factories.getCmdFunc('createPolyPyramidCtx')

createPolySoccerBallCtx = _factories.getCmdFunc('createPolySoccerBallCtx')

createPolySphereCtx = _factories.getCmdFunc('createPolySphereCtx')

createPolyTorusCtx = _factories.getCmdFunc('createPolyTorusCtx')

ctxAbort = _factories.getCmdFunc('ctxAbort')

ctxCompletion = _factories.getCmdFunc('ctxCompletion')

ctxData = _factories.getCmdFunc('ctxData')

ctxEditMode = _factories.getCmdFunc('ctxEditMode')

ctxTraverse = _factories.getCmdFunc('ctxTraverse')

currentCtx = _factories.getCmdFunc('currentCtx')

currentTimeCtx = _factories.getCmdFunc('currentTimeCtx')

curveAddPtCtx = _factories.getCmdFunc('curveAddPtCtx')

curveBezierCtx = _factories.getCmdFunc('curveBezierCtx')

curveCVCtx = _factories.getCmdFunc('curveCVCtx')

curveEPCtx = _factories.getCmdFunc('curveEPCtx')

curveEditorCtx = _factories.getCmdFunc('curveEditorCtx')

curveMoveEPCtx = _factories.getCmdFunc('curveMoveEPCtx')

curveSketchCtx = _factories.getCmdFunc('curveSketchCtx')

directKeyCtx = _factories.getCmdFunc('directKeyCtx')

distanceDimContext = _factories.getCmdFunc('distanceDimContext')

dollyCtx = _factories.getCmdFunc('dollyCtx')

dpBirailCtx = _factories.getCmdFunc('dpBirailCtx')

dragAttrContext = _factories.getCmdFunc('dragAttrContext')

@_factories.addCmdDocs
def draggerContext(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dc', 'dragCommand', 'finalize', 'fnz', 'hc', 'holdCommand', 'initialize', 'inz', 'pc', 'ppc', 'prePressCommand', 'pressCommand', 'rc', 'releaseCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.draggerContext(*args, **kwargs)
    return res

drawExtrudeFacetCtx = _factories.getCmdFunc('drawExtrudeFacetCtx')

dynPaintCtx = _factories.getCmdFunc('dynPaintCtx')

dynParticleCtx = _factories.getCmdFunc('dynParticleCtx')

dynSelectCtx = _factories.getCmdFunc('dynSelectCtx')

dynWireCtx = _factories.getCmdFunc('dynWireCtx')

filterButterworthCtx = _factories.getCmdFunc('filterButterworthCtx')

filterKeyReducerCtx = _factories.getCmdFunc('filterKeyReducerCtx')

filterPeakRemoverCtx = _factories.getCmdFunc('filterPeakRemoverCtx')

graphDollyCtx = _factories.getCmdFunc('graphDollyCtx')

graphSelectContext = _factories.getCmdFunc('graphSelectContext')

graphTrackCtx = _factories.getCmdFunc('graphTrackCtx')

greasePencilCtx = _factories.getCmdFunc('greasePencilCtx')

hotkeyCtx = _factories.getCmdFunc('hotkeyCtx')

ikHandleCtx = _factories.getCmdFunc('ikHandleCtx')

ikSplineHandleCtx = _factories.getCmdFunc('ikSplineHandleCtx')

insertJointCtx = _factories.getCmdFunc('insertJointCtx')

insertKeyCtx = _factories.getCmdFunc('insertKeyCtx')

jointCtx = _factories.getCmdFunc('jointCtx')

keyframeRegionCurrentTimeCtx = _factories.getCmdFunc('keyframeRegionCurrentTimeCtx')

keyframeRegionDirectKeyCtx = _factories.getCmdFunc('keyframeRegionDirectKeyCtx')

keyframeRegionDollyCtx = _factories.getCmdFunc('keyframeRegionDollyCtx')

keyframeRegionInsertKeyCtx = _factories.getCmdFunc('keyframeRegionInsertKeyCtx')

keyframeRegionMoveKeyCtx = _factories.getCmdFunc('keyframeRegionMoveKeyCtx')

keyframeRegionScaleKeyCtx = _factories.getCmdFunc('keyframeRegionScaleKeyCtx')

keyframeRegionSelectKeyCtx = _factories.getCmdFunc('keyframeRegionSelectKeyCtx')

keyframeRegionSetKeyCtx = _factories.getCmdFunc('keyframeRegionSetKeyCtx')

keyframeRegionTrackCtx = _factories.getCmdFunc('keyframeRegionTrackCtx')

lassoContext = _factories.getCmdFunc('lassoContext')

latticeDeformKeyCtx = _factories.getCmdFunc('latticeDeformKeyCtx')

@_factories.addCmdDocs
def manipMoveContext(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pod', 'postCommand', 'postDragCommand', 'prc', 'prd', 'preCommand', 'preDragCommand', 'psc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.manipMoveContext(*args, **kwargs)
    return res

manipMoveLimitsCtx = _factories.getCmdFunc('manipMoveLimitsCtx')

@_factories.addCmdDocs
def manipRotateContext(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pod', 'postCommand', 'postDragCommand', 'prc', 'prd', 'preCommand', 'preDragCommand', 'psc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.manipRotateContext(*args, **kwargs)
    return res

manipRotateLimitsCtx = _factories.getCmdFunc('manipRotateLimitsCtx')

@_factories.addCmdDocs
def manipScaleContext(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pod', 'postCommand', 'postDragCommand', 'prc', 'prd', 'preCommand', 'preDragCommand', 'psc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.manipScaleContext(*args, **kwargs)
    return res

manipScaleLimitsCtx = _factories.getCmdFunc('manipScaleLimitsCtx')

mateCtx = _factories.getCmdFunc('mateCtx')

modelCurrentTimeCtx = _factories.getCmdFunc('modelCurrentTimeCtx')

modelingToolkitSuperCtx = _factories.getCmdFunc('modelingToolkitSuperCtx')

moveKeyCtx = _factories.getCmdFunc('moveKeyCtx')

mpBirailCtx = _factories.getCmdFunc('mpBirailCtx')

orbitCtx = _factories.getCmdFunc('orbitCtx')

panZoomCtx = _factories.getCmdFunc('panZoomCtx')

paramDimContext = _factories.getCmdFunc('paramDimContext')

polyAppendFacetCtx = _factories.getCmdFunc('polyAppendFacetCtx')

polyCreaseCtx = _factories.getCmdFunc('polyCreaseCtx')

polyCreateFacetCtx = _factories.getCmdFunc('polyCreateFacetCtx')

polyCutCtx = _factories.getCmdFunc('polyCutCtx')

polyCutUVCtx = _factories.getCmdFunc('polyCutUVCtx')

polyMergeEdgeCtx = _factories.getCmdFunc('polyMergeEdgeCtx')

polyMergeFacetCtx = _factories.getCmdFunc('polyMergeFacetCtx')

polyRetopoCtx = _factories.getCmdFunc('polyRetopoCtx')

polySelectCtx = _factories.getCmdFunc('polySelectCtx')

polySelectEditCtx = _factories.getCmdFunc('polySelectEditCtx')

polyShortestPathCtx = _factories.getCmdFunc('polyShortestPathCtx')

polySlideEdgeCtx = _factories.getCmdFunc('polySlideEdgeCtx')

polySplitCtx = _factories.getCmdFunc('polySplitCtx')

polySuperCtx = _factories.getCmdFunc('polySuperCtx')

polyVertexNormalCtx = _factories.getCmdFunc('polyVertexNormalCtx')

projectionContext = _factories.getCmdFunc('projectionContext')

propModCtx = _factories.getCmdFunc('propModCtx')

regionSelectKeyCtx = _factories.getCmdFunc('regionSelectKeyCtx')

renderWindowSelectContext = _factories.getCmdFunc('renderWindowSelectContext')

retimeKeyCtx = _factories.getCmdFunc('retimeKeyCtx')

rollCtx = _factories.getCmdFunc('rollCtx')

roundCRCtx = _factories.getCmdFunc('roundCRCtx')

scaleKeyCtx = _factories.getCmdFunc('scaleKeyCtx')

@_factories.addCmdDocs
def scriptCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['fcs', 'finalCommandScript', 'tf', 'toolFinish', 'toolStart', 'ts']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.scriptCtx(*args, **kwargs)
    return res

sculptMeshCacheCtx = _factories.getCmdFunc('sculptMeshCacheCtx')

selectContext = _factories.getCmdFunc('selectContext')

selectKeyCtx = _factories.getCmdFunc('selectKeyCtx')

selectKeyframeRegionCtx = _factories.getCmdFunc('selectKeyframeRegionCtx')

setEditCtx = _factories.getCmdFunc('setEditCtx')

setKeyCtx = _factories.getCmdFunc('setKeyCtx')

@_factories.addCmdDocs
def shadingGeometryRelCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ofc', 'offCommand', 'onCommand', 'onc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shadingGeometryRelCtx(*args, **kwargs)
    return res

@_factories.addCmdDocs
def shadingLightRelCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ofc', 'offCommand', 'onCommand', 'onc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shadingLightRelCtx(*args, **kwargs)
    return res

@_factories.addCmdDocs
def showManipCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['tf', 'toolFinish', 'toolStart', 'ts']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.showManipCtx(*args, **kwargs)
    return res

skinBindCtx = _factories.getCmdFunc('skinBindCtx')

snapTogetherCtx = _factories.getCmdFunc('snapTogetherCtx')

snapshotBeadContext = _factories.getCmdFunc('snapshotBeadContext')

snapshotBeadCtx = _factories.getCmdFunc('snapshotBeadCtx')

snapshotModifyKeyCtx = _factories.getCmdFunc('snapshotModifyKeyCtx')

softModContext = _factories.getCmdFunc('softModContext')

softModCtx = _factories.getCmdFunc('softModCtx')

softSelectOptionsCtx = _factories.getCmdFunc('softSelectOptionsCtx')

spBirailCtx = _factories.getCmdFunc('spBirailCtx')

srtContext = _factories.getCmdFunc('srtContext')

stitchSurfaceCtx = _factories.getCmdFunc('stitchSurfaceCtx')

superCtx = _factories.getCmdFunc('superCtx')

targetWeldCtx = _factories.getCmdFunc('targetWeldCtx')

texCutContext = _factories.getCmdFunc('texCutContext')

texLatticeDeformContext = _factories.getCmdFunc('texLatticeDeformContext')

texManipContext = _factories.getCmdFunc('texManipContext')

texMoveContext = _factories.getCmdFunc('texMoveContext')

texMoveUVShellContext = _factories.getCmdFunc('texMoveUVShellContext')

texRotateContext = _factories.getCmdFunc('texRotateContext')

texScaleContext = _factories.getCmdFunc('texScaleContext')

texSculptCacheContext = _factories.getCmdFunc('texSculptCacheContext')

texSelectContext = _factories.getCmdFunc('texSelectContext')

texSelectShortestPathCtx = _factories.getCmdFunc('texSelectShortestPathCtx')

texSmoothContext = _factories.getCmdFunc('texSmoothContext')

texSmudgeUVContext = _factories.getCmdFunc('texSmudgeUVContext')

texTweakUVContext = _factories.getCmdFunc('texTweakUVContext')

texWinToolCtx = _factories.getCmdFunc('texWinToolCtx')

textureLassoContext = _factories.getCmdFunc('textureLassoContext')

texturePlacementContext = _factories.getCmdFunc('texturePlacementContext')

threePointArcCtx = _factories.getCmdFunc('threePointArcCtx')

trackCtx = _factories.getCmdFunc('trackCtx')

trimCtx = _factories.getCmdFunc('trimCtx')

tumbleCtx = _factories.getCmdFunc('tumbleCtx')

twoPointArcCtx = _factories.getCmdFunc('twoPointArcCtx')

@_factories.addCmdDocs
def userCtx(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editCommand', 'fc', 'finalCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.userCtx(*args, **kwargs)
    return res

view2dToolCtx = _factories.getCmdFunc('view2dToolCtx')

walkCtx = _factories.getCmdFunc('walkCtx')

wireContext = _factories.getCmdFunc('wireContext')

wrinkleContext = _factories.getCmdFunc('wrinkleContext')

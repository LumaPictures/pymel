"""
Contains all context command functions (previously 'ctx').
"""

import pymel.internal.factories as _factories
import pymel.internal.pmcmds as cmds

# ------ Do not edit below this line --------
alignCtx = _factories._addCmdDocs('alignCtx')

arcLenDimContext = _factories._addCmdDocs('arcLenDimContext')

@_factories._addCmdDocs
def art3dPaintCtx(*args, **kwargs):
    res = cmds.art3dPaintCtx(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['art3dPaintCtx']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories._addCmdDocs
def artAttrCtx(*args, **kwargs):
    res = cmds.artAttrCtx(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['artAttrCtx']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

artAttrPaintVertexCtx = _factories._addCmdDocs('artAttrPaintVertexCtx')

artAttrSkinPaintCtx = _factories._addCmdDocs('artAttrSkinPaintCtx')

artBaseCtx = _factories._addCmdDocs('artBaseCtx')

artFluidAttrCtx = _factories._addCmdDocs('artFluidAttrCtx')

artPuttyCtx = _factories._addCmdDocs('artPuttyCtx')

artSelectCtx = _factories._addCmdDocs('artSelectCtx')

artSetPaintCtx = _factories._addCmdDocs('artSetPaintCtx')

@_factories._addCmdDocs
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

blendCtx = _factories._addCmdDocs('blendCtx')

boxDollyCtx = _factories._addCmdDocs('boxDollyCtx')

boxZoomCtx = _factories._addCmdDocs('boxZoomCtx')

clipEditorCurrentTimeCtx = _factories._addCmdDocs('clipEditorCurrentTimeCtx')

createNurbsCircleCtx = _factories._addCmdDocs('createNurbsCircleCtx')

createNurbsConeCtx = _factories._addCmdDocs('createNurbsConeCtx')

createNurbsCubeCtx = _factories._addCmdDocs('createNurbsCubeCtx')

createNurbsCylinderCtx = _factories._addCmdDocs('createNurbsCylinderCtx')

createNurbsPlaneCtx = _factories._addCmdDocs('createNurbsPlaneCtx')

createNurbsSphereCtx = _factories._addCmdDocs('createNurbsSphereCtx')

createNurbsSquareCtx = _factories._addCmdDocs('createNurbsSquareCtx')

createNurbsTorusCtx = _factories._addCmdDocs('createNurbsTorusCtx')

createPolyConeCtx = _factories._addCmdDocs('createPolyConeCtx')

createPolyCubeCtx = _factories._addCmdDocs('createPolyCubeCtx')

createPolyCylinderCtx = _factories._addCmdDocs('createPolyCylinderCtx')

createPolyHelixCtx = _factories._addCmdDocs('createPolyHelixCtx')

createPolyPipeCtx = _factories._addCmdDocs('createPolyPipeCtx')

createPolyPlaneCtx = _factories._addCmdDocs('createPolyPlaneCtx')

createPolyPlatonicSolidCtx = _factories._addCmdDocs('createPolyPlatonicSolidCtx')

createPolyPrismCtx = _factories._addCmdDocs('createPolyPrismCtx')

createPolyPyramidCtx = _factories._addCmdDocs('createPolyPyramidCtx')

createPolySoccerBallCtx = _factories._addCmdDocs('createPolySoccerBallCtx')

createPolySphereCtx = _factories._addCmdDocs('createPolySphereCtx')

createPolyTorusCtx = _factories._addCmdDocs('createPolyTorusCtx')

ctxAbort = _factories._addCmdDocs('ctxAbort')

ctxCompletion = _factories._addCmdDocs('ctxCompletion')

ctxData = _factories._addCmdDocs('ctxData')

ctxEditMode = _factories._addCmdDocs('ctxEditMode')

ctxTraverse = _factories._addCmdDocs('ctxTraverse')

currentCtx = _factories._addCmdDocs('currentCtx')

currentTimeCtx = _factories._addCmdDocs('currentTimeCtx')

curveAddPtCtx = _factories._addCmdDocs('curveAddPtCtx')

curveBezierCtx = _factories._addCmdDocs('curveBezierCtx')

curveCVCtx = _factories._addCmdDocs('curveCVCtx')

curveEPCtx = _factories._addCmdDocs('curveEPCtx')

curveEditorCtx = _factories._addCmdDocs('curveEditorCtx')

curveMoveEPCtx = _factories._addCmdDocs('curveMoveEPCtx')

curveSketchCtx = _factories._addCmdDocs('curveSketchCtx')

directKeyCtx = _factories._addCmdDocs('directKeyCtx')

distanceDimContext = _factories._addCmdDocs('distanceDimContext')

dollyCtx = _factories._addCmdDocs('dollyCtx')

dpBirailCtx = _factories._addCmdDocs('dpBirailCtx')

dragAttrContext = _factories._addCmdDocs('dragAttrContext')

@_factories._addCmdDocs
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

drawExtrudeFacetCtx = _factories._addCmdDocs('drawExtrudeFacetCtx')

dynPaintCtx = _factories._addCmdDocs('dynPaintCtx')

dynParticleCtx = _factories._addCmdDocs('dynParticleCtx')

dynSelectCtx = _factories._addCmdDocs('dynSelectCtx')

dynWireCtx = _factories._addCmdDocs('dynWireCtx')

graphDollyCtx = _factories._addCmdDocs('graphDollyCtx')

graphSelectContext = _factories._addCmdDocs('graphSelectContext')

graphTrackCtx = _factories._addCmdDocs('graphTrackCtx')

greasePencilCtx = _factories._addCmdDocs('greasePencilCtx')

hotkeyCtx = _factories._addCmdDocs('hotkeyCtx')

ikHandleCtx = _factories._addCmdDocs('ikHandleCtx')

ikSplineHandleCtx = _factories._addCmdDocs('ikSplineHandleCtx')

insertJointCtx = _factories._addCmdDocs('insertJointCtx')

insertKeyCtx = _factories._addCmdDocs('insertKeyCtx')

jointCtx = _factories._addCmdDocs('jointCtx')

keyframeRegionCurrentTimeCtx = _factories._addCmdDocs('keyframeRegionCurrentTimeCtx')

keyframeRegionDirectKeyCtx = _factories._addCmdDocs('keyframeRegionDirectKeyCtx')

keyframeRegionDollyCtx = _factories._addCmdDocs('keyframeRegionDollyCtx')

keyframeRegionInsertKeyCtx = _factories._addCmdDocs('keyframeRegionInsertKeyCtx')

keyframeRegionMoveKeyCtx = _factories._addCmdDocs('keyframeRegionMoveKeyCtx')

keyframeRegionScaleKeyCtx = _factories._addCmdDocs('keyframeRegionScaleKeyCtx')

keyframeRegionSelectKeyCtx = _factories._addCmdDocs('keyframeRegionSelectKeyCtx')

keyframeRegionSetKeyCtx = _factories._addCmdDocs('keyframeRegionSetKeyCtx')

keyframeRegionTrackCtx = _factories._addCmdDocs('keyframeRegionTrackCtx')

lassoContext = _factories._addCmdDocs('lassoContext')

latticeDeformKeyCtx = _factories._addCmdDocs('latticeDeformKeyCtx')

@_factories._addCmdDocs
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

manipMoveLimitsCtx = _factories._addCmdDocs('manipMoveLimitsCtx')

@_factories._addCmdDocs
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

manipRotateLimitsCtx = _factories._addCmdDocs('manipRotateLimitsCtx')

@_factories._addCmdDocs
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

manipScaleLimitsCtx = _factories._addCmdDocs('manipScaleLimitsCtx')

mateCtx = _factories._addCmdDocs('mateCtx')

modelCurrentTimeCtx = _factories._addCmdDocs('modelCurrentTimeCtx')

modelingToolkitSuperCtx = _factories._addCmdDocs('modelingToolkitSuperCtx')

moveKeyCtx = _factories._addCmdDocs('moveKeyCtx')

mpBirailCtx = _factories._addCmdDocs('mpBirailCtx')

orbitCtx = _factories._addCmdDocs('orbitCtx')

panZoomCtx = _factories._addCmdDocs('panZoomCtx')

paramDimContext = _factories._addCmdDocs('paramDimContext')

polyAppendFacetCtx = _factories._addCmdDocs('polyAppendFacetCtx')

polyCreaseCtx = _factories._addCmdDocs('polyCreaseCtx')

polyCreateFacetCtx = _factories._addCmdDocs('polyCreateFacetCtx')

polyCutCtx = _factories._addCmdDocs('polyCutCtx')

polyCutUVCtx = _factories._addCmdDocs('polyCutUVCtx')

polyMergeEdgeCtx = _factories._addCmdDocs('polyMergeEdgeCtx')

polyMergeFacetCtx = _factories._addCmdDocs('polyMergeFacetCtx')

polySelectCtx = _factories._addCmdDocs('polySelectCtx')

polySelectEditCtx = _factories._addCmdDocs('polySelectEditCtx')

polyShortestPathCtx = _factories._addCmdDocs('polyShortestPathCtx')

polySlideEdgeCtx = _factories._addCmdDocs('polySlideEdgeCtx')

polySplitCtx = _factories._addCmdDocs('polySplitCtx')

polySuperCtx = _factories._addCmdDocs('polySuperCtx')

polyVertexNormalCtx = _factories._addCmdDocs('polyVertexNormalCtx')

projectionContext = _factories._addCmdDocs('projectionContext')

propModCtx = _factories._addCmdDocs('propModCtx')

regionSelectKeyCtx = _factories._addCmdDocs('regionSelectKeyCtx')

renderWindowSelectContext = _factories._addCmdDocs('renderWindowSelectContext')

retimeKeyCtx = _factories._addCmdDocs('retimeKeyCtx')

rollCtx = _factories._addCmdDocs('rollCtx')

roundCRCtx = _factories._addCmdDocs('roundCRCtx')

scaleKeyCtx = _factories._addCmdDocs('scaleKeyCtx')

@_factories._addCmdDocs
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

sculptMeshCacheCtx = _factories._addCmdDocs('sculptMeshCacheCtx')

selectContext = _factories._addCmdDocs('selectContext')

selectKeyCtx = _factories._addCmdDocs('selectKeyCtx')

selectKeyframeRegionCtx = _factories._addCmdDocs('selectKeyframeRegionCtx')

setEditCtx = _factories._addCmdDocs('setEditCtx')

setKeyCtx = _factories._addCmdDocs('setKeyCtx')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

skinBindCtx = _factories._addCmdDocs('skinBindCtx')

snapTogetherCtx = _factories._addCmdDocs('snapTogetherCtx')

snapshotBeadContext = _factories._addCmdDocs('snapshotBeadContext')

snapshotBeadCtx = _factories._addCmdDocs('snapshotBeadCtx')

snapshotModifyKeyCtx = _factories._addCmdDocs('snapshotModifyKeyCtx')

softModContext = _factories._addCmdDocs('softModContext')

softModCtx = _factories._addCmdDocs('softModCtx')

softSelectOptionsCtx = _factories._addCmdDocs('softSelectOptionsCtx')

spBirailCtx = _factories._addCmdDocs('spBirailCtx')

srtContext = _factories._addCmdDocs('srtContext')

stitchSurfaceCtx = _factories._addCmdDocs('stitchSurfaceCtx')

superCtx = _factories._addCmdDocs('superCtx')

targetWeldCtx = _factories._addCmdDocs('targetWeldCtx')

texCutContext = _factories._addCmdDocs('texCutContext')

texLatticeDeformContext = _factories._addCmdDocs('texLatticeDeformContext')

texManipContext = _factories._addCmdDocs('texManipContext')

texMoveContext = _factories._addCmdDocs('texMoveContext')

texMoveUVShellContext = _factories._addCmdDocs('texMoveUVShellContext')

texRotateContext = _factories._addCmdDocs('texRotateContext')

texScaleContext = _factories._addCmdDocs('texScaleContext')

texSculptCacheContext = _factories._addCmdDocs('texSculptCacheContext')

texSelectContext = _factories._addCmdDocs('texSelectContext')

texSelectShortestPathCtx = _factories._addCmdDocs('texSelectShortestPathCtx')

texSmoothContext = _factories._addCmdDocs('texSmoothContext')

texSmudgeUVContext = _factories._addCmdDocs('texSmudgeUVContext')

texTweakUVContext = _factories._addCmdDocs('texTweakUVContext')

texWinToolCtx = _factories._addCmdDocs('texWinToolCtx')

textureLassoContext = _factories._addCmdDocs('textureLassoContext')

texturePlacementContext = _factories._addCmdDocs('texturePlacementContext')

threePointArcCtx = _factories._addCmdDocs('threePointArcCtx')

trackCtx = _factories._addCmdDocs('trackCtx')

trimCtx = _factories._addCmdDocs('trimCtx')

tumbleCtx = _factories._addCmdDocs('tumbleCtx')

twoPointArcCtx = _factories._addCmdDocs('twoPointArcCtx')

@_factories._addCmdDocs
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

view2dToolCtx = _factories._addCmdDocs('view2dToolCtx')

walkCtx = _factories._addCmdDocs('walkCtx')

wireContext = _factories._addCmdDocs('wireContext')

wrinkleContext = _factories._addCmdDocs('wrinkleContext')

"""functions related to modeling"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pymel.internal.factories as _factories
import pymel.core.general as _general
if False:
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]


def pointPosition(*args, **kwargs):
    return _general.datatypes.Point(cmds.pointPosition(*args, **kwargs))


def curve(*args, **kwargs):
    """
    Maya Bug Fix:
      - name parameter only applied to transform. now applies to shape as well
    """
    # curve returns a transform
    name = kwargs.pop('name', kwargs.pop('n', None))
    res = _general.PyNode(cmds.curve(*args, **kwargs))
    if name:
        res.rename(name)
    return res


def surface(*args, **kwargs):
    """
    Maya Bug Fix:
      - name parameter only applied to transform. now applies to shape as well
    """
    # surface returns a shape
    name = kwargs.pop('name', kwargs.pop('n', None))
    res = _general.PyNode(cmds.surface(*args, **kwargs))
    if name:
        res.getParent().rename(name)
    return res

# ------ Do not edit below this line --------

addMetadata = _factories.getCmdFunc('addMetadata')

@_factories.addCmdDocs
def alignCurve(*args, **kwargs):
    res = cmds.alignCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def alignSurface(*args, **kwargs):
    res = cmds.alignSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def angleBetween(*args, **kwargs):
    res = cmds.angleBetween(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

applyMetadata = _factories.getCmdFunc('applyMetadata')

@_factories.addCmdDocs
def arcLengthDimension(*args, **kwargs):
    res = cmds.arcLengthDimension(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def arclen(*args, **kwargs):
    res = cmds.arclen(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['arclen']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

arubaNurbsToPoly = _factories.getCmdFunc('arubaNurbsToPoly')

@_factories.addCmdDocs
def attachCurve(*args, **kwargs):
    res = cmds.attachCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def attachSurface(*args, **kwargs):
    res = cmds.attachSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def bevel(*args, **kwargs):
    res = cmds.bevel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def bevelPlus(*args, **kwargs):
    res = cmds.bevelPlus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

bezierAnchorPreset = _factories.getCmdFunc('bezierAnchorPreset')

bezierAnchorState = _factories.getCmdFunc('bezierAnchorState')

@_factories.addCmdDocs
def bezierCurveToNurbs(*args, **kwargs):
    res = cmds.bezierCurveToNurbs(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

bezierInfo = _factories.getCmdFunc('bezierInfo')

blend2 = _factories.getCmdFunc('blend2')

blindDataType = _factories.getCmdFunc('blindDataType')

@_factories.addCmdDocs
def boundary(*args, **kwargs):
    res = cmds.boundary(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

canCreateManip = _factories.getCmdFunc('canCreateManip')

changeSubdivComponentDisplayLevel = _factories.getCmdFunc('changeSubdivComponentDisplayLevel')

changeSubdivRegion = _factories.getCmdFunc('changeSubdivRegion')

@_factories.addCmdDocs
def circle(*args, **kwargs):
    res = cmds.circle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

circularFillet = _factories.getCmdFunc('circularFillet')

@_factories.addCmdDocs
def closeCurve(*args, **kwargs):
    res = cmds.closeCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def closeSurface(*args, **kwargs):
    res = cmds.closeSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

coarsenSubdivSelectionList = _factories.getCmdFunc('coarsenSubdivSelectionList')

@_factories.addCmdDocs
def cone(*args, **kwargs):
    res = cmds.cone(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

constructionHistory = _factories.getCmdFunc('constructionHistory')

createSubdivRegion = _factories.getCmdFunc('createSubdivRegion')

_curve = curve

@_factories.addCmdDocs
def curve(*args, **kwargs):
    res = _curve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def curveIntersect(*args, **kwargs):
    res = cmds.curveIntersect(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

curveOnSurface = _factories.getCmdFunc('curveOnSurface')

@_factories.addCmdDocs
def cylinder(*args, **kwargs):
    res = cmds.cylinder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

dataStructure = _factories.getCmdFunc('dataStructure')

@_factories.addCmdDocs
def detachCurve(*args, **kwargs):
    res = cmds.detachCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def detachSurface(*args, **kwargs):
    res = cmds.detachSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

doubleProfileBirailSurface = _factories.getCmdFunc('doubleProfileBirailSurface')

duplicateCurve = _factories.getCmdFunc('duplicateCurve')

duplicateSurface = _factories.getCmdFunc('duplicateSurface')

@_factories.addCmdDocs
def editMetadata(*args, **kwargs):
    res = cmds.editMetadata(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def extendCurve(*args, **kwargs):
    res = cmds.extendCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def extendSurface(*args, **kwargs):
    res = cmds.extendSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def extrude(*args, **kwargs):
    res = cmds.extrude(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def filletCurve(*args, **kwargs):
    res = cmds.filletCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

filterExpand = _factories.getCmdFunc('filterExpand')

@_factories.addCmdDocs
def fitBspline(*args, **kwargs):
    res = cmds.fitBspline(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

freeFormFillet = _factories.getCmdFunc('freeFormFillet')

geomToBBox = _factories.getCmdFunc('geomToBBox')

getMetadata = _factories.getCmdFunc('getMetadata')

@_factories.addCmdDocs
def globalStitch(*args, **kwargs):
    res = cmds.globalStitch(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def grid(*args, **kwargs):
    res = cmds.grid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

hardenPointCurve = _factories.getCmdFunc('hardenPointCurve')

hasMetadata = _factories.getCmdFunc('hasMetadata')

illustratorCurves = _factories.getCmdFunc('illustratorCurves')

@_factories.addCmdDocs
def insertKnotCurve(*args, **kwargs):
    res = cmds.insertKnotCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def insertKnotSurface(*args, **kwargs):
    res = cmds.insertKnotSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

intersect = _factories.getCmdFunc('intersect')

@_factories.addCmdDocs
def loft(*args, **kwargs):
    res = cmds.loft(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

makeSingleSurface = _factories.getCmdFunc('makeSingleSurface')

manipOptions = _factories.getCmdFunc('manipOptions')

manipPivot = _factories.getCmdFunc('manipPivot')

moveVertexAlongDirection = _factories.getCmdFunc('moveVertexAlongDirection')

multiProfileBirailSurface = _factories.getCmdFunc('multiProfileBirailSurface')

nurbsBoolean = _factories.getCmdFunc('nurbsBoolean')

nurbsCopyUVSet = _factories.getCmdFunc('nurbsCopyUVSet')

@_factories.addCmdDocs
def nurbsCube(*args, **kwargs):
    res = cmds.nurbsCube(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def nurbsCurveToBezier(*args, **kwargs):
    res = cmds.nurbsCurveToBezier(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsEditUV = _factories.getCmdFunc('nurbsEditUV')

@_factories.addCmdDocs
def nurbsPlane(*args, **kwargs):
    res = cmds.nurbsPlane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsSelect = _factories.getCmdFunc('nurbsSelect')

@_factories.addCmdDocs
def nurbsSquare(*args, **kwargs):
    res = cmds.nurbsSquare(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsToPoly = _factories.getCmdFunc('nurbsToPoly')

nurbsToPolygonsPref = _factories.getCmdFunc('nurbsToPolygonsPref')

@_factories.addCmdDocs
def nurbsToSubdiv(*args, **kwargs):
    res = cmds.nurbsToSubdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsToSubdivPref = _factories.getCmdFunc('nurbsToSubdivPref')

nurbsUVSet = _factories.getCmdFunc('nurbsUVSet')

@_factories.addCmdDocs
def offsetCurve(*args, **kwargs):
    res = cmds.offsetCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

offsetCurveOnSurface = _factories.getCmdFunc('offsetCurveOnSurface')

@_factories.addCmdDocs
def offsetSurface(*args, **kwargs):
    res = cmds.offsetSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

planarSrf = _factories.getCmdFunc('planarSrf')

@_factories.addCmdDocs
def plane(*args, **kwargs):
    res = cmds.plane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

pointCurveConstraint = _factories.getCmdFunc('pointCurveConstraint')

pointOnCurve = _factories.getCmdFunc('pointOnCurve')

pointOnSurface = _factories.getCmdFunc('pointOnSurface')

pointPosition = _factories.addCmdDocs(pointPosition)

@_factories.addCmdDocs
def polyAppend(*args, **kwargs):
    res = cmds.polyAppend(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyAppendVertex(*args, **kwargs):
    res = cmds.polyAppendVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyAutoProjection = _factories.getCmdFunc('polyAutoProjection')

polyAverageNormal = _factories.getCmdFunc('polyAverageNormal')

@_factories.addCmdDocs
def polyAverageVertex(*args, **kwargs):
    res = cmds.polyAverageVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyBevel(*args, **kwargs):
    res = cmds.polyBevel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyBevel3(*args, **kwargs):
    res = cmds.polyBevel3(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyBlendColor = _factories.getCmdFunc('polyBlendColor')

@_factories.addCmdDocs
def polyBlindData(*args, **kwargs):
    res = cmds.polyBlindData(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyBoolOp(*args, **kwargs):
    res = cmds.polyBoolOp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyBridgeEdge(*args, **kwargs):
    res = cmds.polyBridgeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCBoolOp(*args, **kwargs):
    res = cmds.polyCBoolOp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCacheMonitor = _factories.getCmdFunc('polyCacheMonitor')

polyCanBridgeEdge = _factories.getCmdFunc('polyCanBridgeEdge')

polyCheck = _factories.getCmdFunc('polyCheck')

@_factories.addCmdDocs
def polyChipOff(*args, **kwargs):
    res = cmds.polyChipOff(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCircularize(*args, **kwargs):
    res = cmds.polyCircularize(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCircularizeEdge = _factories.getCmdFunc('polyCircularizeEdge')

polyCircularizeFace = _factories.getCmdFunc('polyCircularizeFace')

@_factories.addCmdDocs
def polyClean(*args, **kwargs):
    res = cmds.polyClean(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyClipboard = _factories.getCmdFunc('polyClipboard')

@_factories.addCmdDocs
def polyCloseBorder(*args, **kwargs):
    res = cmds.polyCloseBorder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCollapseEdge(*args, **kwargs):
    res = cmds.polyCollapseEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCollapseFacet = _factories.getCmdFunc('polyCollapseFacet')

polyCollapseTweaks = _factories.getCmdFunc('polyCollapseTweaks')

polyColorBlindData = _factories.getCmdFunc('polyColorBlindData')

@_factories.addCmdDocs
def polyColorDel(*args, **kwargs):
    res = cmds.polyColorDel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyColorMod(*args, **kwargs):
    res = cmds.polyColorMod(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyColorPerVertex(*args, **kwargs):
    res = cmds.polyColorPerVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyColorSet = _factories.getCmdFunc('polyColorSet')

polyCompare = _factories.getCmdFunc('polyCompare')

@_factories.addCmdDocs
def polyCone(*args, **kwargs):
    res = cmds.polyCone(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyConnectComponents(*args, **kwargs):
    res = cmds.polyConnectComponents(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyContourProjection = _factories.getCmdFunc('polyContourProjection')

@_factories.addCmdDocs
def polyCopyUV(*args, **kwargs):
    res = cmds.polyCopyUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCrease(*args, **kwargs):
    res = cmds.polyCrease(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCreateFacet = _factories.getCmdFunc('polyCreateFacet')

@_factories.addCmdDocs
def polyCube(*args, **kwargs):
    res = cmds.polyCube(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCut(*args, **kwargs):
    res = cmds.polyCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyCylinder(*args, **kwargs):
    res = cmds.polyCylinder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCylindricalProjection = _factories.getCmdFunc('polyCylindricalProjection')

@_factories.addCmdDocs
def polyDelEdge(*args, **kwargs):
    res = cmds.polyDelEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyDelFacet(*args, **kwargs):
    res = cmds.polyDelFacet(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyDelVertex(*args, **kwargs):
    res = cmds.polyDelVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyDuplicateAndConnect = _factories.getCmdFunc('polyDuplicateAndConnect')

@_factories.addCmdDocs
def polyDuplicateEdge(*args, **kwargs):
    res = cmds.polyDuplicateEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyEditEdgeFlow(*args, **kwargs):
    res = cmds.polyEditEdgeFlow(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyEditUV = _factories.getCmdFunc('polyEditUV')

polyEditUVShell = _factories.getCmdFunc('polyEditUVShell')

polyEvaluate = _factories.getCmdFunc('polyEvaluate')

@_factories.addCmdDocs
def polyExtrudeEdge(*args, **kwargs):
    res = cmds.polyExtrudeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyExtrudeFacet = _factories.getCmdFunc('polyExtrudeFacet')

@_factories.addCmdDocs
def polyExtrudeVertex(*args, **kwargs):
    res = cmds.polyExtrudeVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyFlipEdge(*args, **kwargs):
    res = cmds.polyFlipEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyFlipUV(*args, **kwargs):
    res = cmds.polyFlipUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyForceUV = _factories.getCmdFunc('polyForceUV')

polyGeoSampler = _factories.getCmdFunc('polyGeoSampler')

@_factories.addCmdDocs
def polyHelix(*args, **kwargs):
    res = cmds.polyHelix(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyHole = _factories.getCmdFunc('polyHole')

polyInfo = _factories.getCmdFunc('polyInfo')

@_factories.addCmdDocs
def polyInstallAction(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cn', 'commandName']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.polyInstallAction(*args, **kwargs)
    return res

@_factories.addCmdDocs
def polyLayoutUV(*args, **kwargs):
    res = cmds.polyLayoutUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyListComponentConversion = _factories.getCmdFunc('polyListComponentConversion')

@_factories.addCmdDocs
def polyMapCut(*args, **kwargs):
    res = cmds.polyMapCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMapDel(*args, **kwargs):
    res = cmds.polyMapDel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMapSew(*args, **kwargs):
    res = cmds.polyMapSew(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMapSewMove(*args, **kwargs):
    res = cmds.polyMapSewMove(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMergeEdge(*args, **kwargs):
    res = cmds.polyMergeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMergeFacet = _factories.getCmdFunc('polyMergeFacet')

@_factories.addCmdDocs
def polyMergeUV(*args, **kwargs):
    res = cmds.polyMergeUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMergeVertex = _factories.getCmdFunc('polyMergeVertex')

polyMirrorFace = _factories.getCmdFunc('polyMirrorFace')

@_factories.addCmdDocs
def polyMoveEdge(*args, **kwargs):
    res = cmds.polyMoveEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMoveFacet = _factories.getCmdFunc('polyMoveFacet')

@_factories.addCmdDocs
def polyMoveFacetUV(*args, **kwargs):
    res = cmds.polyMoveFacetUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMoveUV(*args, **kwargs):
    res = cmds.polyMoveUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyMoveVertex(*args, **kwargs):
    res = cmds.polyMoveVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMultiLayoutUV = _factories.getCmdFunc('polyMultiLayoutUV')

@_factories.addCmdDocs
def polyNormal(*args, **kwargs):
    res = cmds.polyNormal(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyNormalPerVertex(*args, **kwargs):
    res = cmds.polyNormalPerVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyNormalizeUV(*args, **kwargs):
    res = cmds.polyNormalizeUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyOptUvs(*args, **kwargs):
    res = cmds.polyOptUvs(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyOptions = _factories.getCmdFunc('polyOptions')

polyOutput = _factories.getCmdFunc('polyOutput')

@_factories.addCmdDocs
def polyPinUV(*args, **kwargs):
    res = cmds.polyPinUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyPipe(*args, **kwargs):
    res = cmds.polyPipe(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyPlanarProjection = _factories.getCmdFunc('polyPlanarProjection')

@_factories.addCmdDocs
def polyPlane(*args, **kwargs):
    res = cmds.polyPlane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyPlatonicSolid(*args, **kwargs):
    res = cmds.polyPlatonicSolid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyPoke(*args, **kwargs):
    res = cmds.polyPoke(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyPrimitive(*args, **kwargs):
    res = cmds.polyPrimitive(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyPrism(*args, **kwargs):
    res = cmds.polyPrism(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyProjectCurve(*args, **kwargs):
    res = cmds.polyProjectCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyProjection = _factories.getCmdFunc('polyProjection')

@_factories.addCmdDocs
def polyPyramid(*args, **kwargs):
    res = cmds.polyPyramid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyQuad(*args, **kwargs):
    res = cmds.polyQuad(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyQueryBlindData = _factories.getCmdFunc('polyQueryBlindData')

@_factories.addCmdDocs
def polyReduce(*args, **kwargs):
    res = cmds.polyReduce(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyRemesh(*args, **kwargs):
    res = cmds.polyRemesh(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyRetopo(*args, **kwargs):
    res = cmds.polyRetopo(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySelect = _factories.getCmdFunc('polySelect')

polySelectConstraint = _factories.getCmdFunc('polySelectConstraint')

@_factories.addCmdDocs
def polySelectConstraintMonitor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.polySelectConstraintMonitor(*args, **kwargs)
    return res

@_factories.addCmdDocs
def polySeparate(*args, **kwargs):
    res = cmds.polySeparate(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySetToFaceNormal = _factories.getCmdFunc('polySetToFaceNormal')

@_factories.addCmdDocs
def polySewEdge(*args, **kwargs):
    res = cmds.polySewEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySlideEdge = _factories.getCmdFunc('polySlideEdge')

@_factories.addCmdDocs
def polySmooth(*args, **kwargs):
    res = cmds.polySmooth(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polySoftEdge(*args, **kwargs):
    res = cmds.polySoftEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polySphere(*args, **kwargs):
    res = cmds.polySphere(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySphericalProjection = _factories.getCmdFunc('polySphericalProjection')

@_factories.addCmdDocs
def polySplit(*args, **kwargs):
    res = cmds.polySplit(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polySplitEdge(*args, **kwargs):
    res = cmds.polySplitEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polySplitRing(*args, **kwargs):
    res = cmds.polySplitRing(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySplitVertex = _factories.getCmdFunc('polySplitVertex')

@_factories.addCmdDocs
def polyStraightenUVBorder(*args, **kwargs):
    res = cmds.polyStraightenUVBorder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySubdivideEdge = _factories.getCmdFunc('polySubdivideEdge')

polySubdivideFacet = _factories.getCmdFunc('polySubdivideFacet')

@_factories.addCmdDocs
def polyToSubdiv(*args, **kwargs):
    res = cmds.polyToSubdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyTorus(*args, **kwargs):
    res = cmds.polyTorus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyTransfer(*args, **kwargs):
    res = cmds.polyTransfer(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyTriangulate(*args, **kwargs):
    res = cmds.polyTriangulate(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyUVCoverage = _factories.getCmdFunc('polyUVCoverage')

polyUVOverlap = _factories.getCmdFunc('polyUVOverlap')

@_factories.addCmdDocs
def polyUVRectangle(*args, **kwargs):
    res = cmds.polyUVRectangle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyUVSet = _factories.getCmdFunc('polyUVSet')

polyUVStackSimilarShells = _factories.getCmdFunc('polyUVStackSimilarShells')

@_factories.addCmdDocs
def polyUnite(*args, **kwargs):
    res = cmds.polyUnite(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def polyWedgeFace(*args, **kwargs):
    res = cmds.polyWedgeFace(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def projectCurve(*args, **kwargs):
    res = cmds.projectCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def projectTangent(*args, **kwargs):
    res = cmds.projectTangent(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

propMove = _factories.getCmdFunc('propMove')

querySubdiv = _factories.getCmdFunc('querySubdiv')

@_factories.addCmdDocs
def rebuildCurve(*args, **kwargs):
    res = cmds.rebuildCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def rebuildSurface(*args, **kwargs):
    res = cmds.rebuildSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

refineSubdivSelectionList = _factories.getCmdFunc('refineSubdivSelectionList')

@_factories.addCmdDocs
def reverseCurve(*args, **kwargs):
    res = cmds.reverseCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def reverseSurface(*args, **kwargs):
    res = cmds.reverseSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def revolve(*args, **kwargs):
    res = cmds.revolve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def roundConstantRadius(*args, **kwargs):
    res = cmds.roundConstantRadius(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

setXformManip = _factories.getCmdFunc('setXformManip')

showMetadata = _factories.getCmdFunc('showMetadata')

singleProfileBirailSurface = _factories.getCmdFunc('singleProfileBirailSurface')

@_factories.addCmdDocs
def smoothCurve(*args, **kwargs):
    res = cmds.smoothCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

smoothTangentSurface = _factories.getCmdFunc('smoothTangentSurface')

@_factories.addCmdDocs
def sphere(*args, **kwargs):
    res = cmds.sphere(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

squareSurface = _factories.getCmdFunc('squareSurface')

stitchSurface = _factories.getCmdFunc('stitchSurface')

stitchSurfacePoints = _factories.getCmdFunc('stitchSurfacePoints')

subdAutoProjection = _factories.getCmdFunc('subdAutoProjection')

@_factories.addCmdDocs
def subdCleanTopology(*args, **kwargs):
    res = cmds.subdCleanTopology(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdCollapse = _factories.getCmdFunc('subdCollapse')

subdDuplicateAndConnect = _factories.getCmdFunc('subdDuplicateAndConnect')

subdEditUV = _factories.getCmdFunc('subdEditUV')

@_factories.addCmdDocs
def subdLayoutUV(*args, **kwargs):
    res = cmds.subdLayoutUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdListComponentConversion = _factories.getCmdFunc('subdListComponentConversion')

@_factories.addCmdDocs
def subdMapCut(*args, **kwargs):
    res = cmds.subdMapCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def subdMapSewMove(*args, **kwargs):
    res = cmds.subdMapSewMove(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdMatchTopology = _factories.getCmdFunc('subdMatchTopology')

subdMirror = _factories.getCmdFunc('subdMirror')

subdPlanarProjection = _factories.getCmdFunc('subdPlanarProjection')

subdToBlind = _factories.getCmdFunc('subdToBlind')

subdToPoly = _factories.getCmdFunc('subdToPoly')

subdTransferUVsToCache = _factories.getCmdFunc('subdTransferUVsToCache')

@_factories.addCmdDocs
def subdiv(*args, **kwargs):
    res = cmds.subdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdivCrease = _factories.getCmdFunc('subdivCrease')

subdivDisplaySmoothness = _factories.getCmdFunc('subdivDisplaySmoothness')

_surface = surface

@_factories.addCmdDocs
def surface(*args, **kwargs):
    res = _surface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

textCurves = _factories.getCmdFunc('textCurves')

tolerance = _factories.getCmdFunc('tolerance')

@_factories.addCmdDocs
def torus(*args, **kwargs):
    res = cmds.torus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def transferAttributes(*args, **kwargs):
    res = cmds.transferAttributes(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

transferShadingSets = _factories.getCmdFunc('transferShadingSets')

@_factories.addCmdDocs
def trim(*args, **kwargs):
    res = cmds.trim(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

unfold = _factories.getCmdFunc('unfold')

untangleUV = _factories.getCmdFunc('untangleUV')

@_factories.addCmdDocs
def untrim(*args, **kwargs):
    res = cmds.untrim(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

uvSnapshot = _factories.getCmdFunc('uvSnapshot')

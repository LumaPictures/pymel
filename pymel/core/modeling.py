"""functions related to modeling"""

import pymel.internal.factories as _factories
import pymel.internal.pmcmds as cmds
import general as _general

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
addMetadata = _factories._addCmdDocs('addMetadata')

@_factories._addCmdDocs
def alignCurve(*args, **kwargs):
    res = cmds.alignCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def alignSurface(*args, **kwargs):
    res = cmds.alignSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def angleBetween(*args, **kwargs):
    res = cmds.angleBetween(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

applyMetadata = _factories._addCmdDocs('applyMetadata')

@_factories._addCmdDocs
def arcLengthDimension(*args, **kwargs):
    res = cmds.arcLengthDimension(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def arclen(*args, **kwargs):
    res = cmds.arclen(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['arclen']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

arubaNurbsToPoly = _factories._addCmdDocs('arubaNurbsToPoly')

@_factories._addCmdDocs
def attachCurve(*args, **kwargs):
    res = cmds.attachCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def attachSurface(*args, **kwargs):
    res = cmds.attachSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def bevel(*args, **kwargs):
    res = cmds.bevel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def bevelPlus(*args, **kwargs):
    res = cmds.bevelPlus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

bezierAnchorPreset = _factories._addCmdDocs('bezierAnchorPreset')

bezierAnchorState = _factories._addCmdDocs('bezierAnchorState')

@_factories._addCmdDocs
def bezierCurveToNurbs(*args, **kwargs):
    res = cmds.bezierCurveToNurbs(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

bezierInfo = _factories._addCmdDocs('bezierInfo')

blend2 = _factories._addCmdDocs('blend2')

blindDataType = _factories._addCmdDocs('blindDataType')

@_factories._addCmdDocs
def boundary(*args, **kwargs):
    res = cmds.boundary(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

canCreateManip = _factories._addCmdDocs('canCreateManip')

changeSubdivComponentDisplayLevel = _factories._addCmdDocs('changeSubdivComponentDisplayLevel')

changeSubdivRegion = _factories._addCmdDocs('changeSubdivRegion')

@_factories._addCmdDocs
def circle(*args, **kwargs):
    res = cmds.circle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

circularFillet = _factories._addCmdDocs('circularFillet')

@_factories._addCmdDocs
def closeCurve(*args, **kwargs):
    res = cmds.closeCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def closeSurface(*args, **kwargs):
    res = cmds.closeSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

coarsenSubdivSelectionList = _factories._addCmdDocs('coarsenSubdivSelectionList')

@_factories._addCmdDocs
def cone(*args, **kwargs):
    res = cmds.cone(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

constructionHistory = _factories._addCmdDocs('constructionHistory')

createSubdivRegion = _factories._addCmdDocs('createSubdivRegion')

_curve = curve

@_factories._addCmdDocs
def curve(*args, **kwargs):
    res = _curve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def curveIntersect(*args, **kwargs):
    res = cmds.curveIntersect(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

curveOnSurface = _factories._addCmdDocs('curveOnSurface')

@_factories._addCmdDocs
def cylinder(*args, **kwargs):
    res = cmds.cylinder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

dataStructure = _factories._addCmdDocs('dataStructure')

@_factories._addCmdDocs
def detachCurve(*args, **kwargs):
    res = cmds.detachCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def detachSurface(*args, **kwargs):
    res = cmds.detachSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

doubleProfileBirailSurface = _factories._addCmdDocs('doubleProfileBirailSurface')

duplicateCurve = _factories._addCmdDocs('duplicateCurve')

duplicateSurface = _factories._addCmdDocs('duplicateSurface')

@_factories._addCmdDocs
def editMetadata(*args, **kwargs):
    res = cmds.editMetadata(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def extendCurve(*args, **kwargs):
    res = cmds.extendCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def extendSurface(*args, **kwargs):
    res = cmds.extendSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def extrude(*args, **kwargs):
    res = cmds.extrude(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def filletCurve(*args, **kwargs):
    res = cmds.filletCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

filterExpand = _factories._addCmdDocs('filterExpand')

@_factories._addCmdDocs
def fitBspline(*args, **kwargs):
    res = cmds.fitBspline(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

freeFormFillet = _factories._addCmdDocs('freeFormFillet')

geomToBBox = _factories._addCmdDocs('geomToBBox')

getMetadata = _factories._addCmdDocs('getMetadata')

@_factories._addCmdDocs
def globalStitch(*args, **kwargs):
    res = cmds.globalStitch(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def grid(*args, **kwargs):
    res = cmds.grid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

hardenPointCurve = _factories._addCmdDocs('hardenPointCurve')

hasMetadata = _factories._addCmdDocs('hasMetadata')

illustratorCurves = _factories._addCmdDocs('illustratorCurves')

@_factories._addCmdDocs
def insertKnotCurve(*args, **kwargs):
    res = cmds.insertKnotCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def insertKnotSurface(*args, **kwargs):
    res = cmds.insertKnotSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

intersect = _factories._addCmdDocs('intersect')

@_factories._addCmdDocs
def loft(*args, **kwargs):
    res = cmds.loft(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

makeSingleSurface = _factories._addCmdDocs('makeSingleSurface')

manipOptions = _factories._addCmdDocs('manipOptions')

manipPivot = _factories._addCmdDocs('manipPivot')

moveVertexAlongDirection = _factories._addCmdDocs('moveVertexAlongDirection')

multiProfileBirailSurface = _factories._addCmdDocs('multiProfileBirailSurface')

nurbsBoolean = _factories._addCmdDocs('nurbsBoolean')

nurbsCopyUVSet = _factories._addCmdDocs('nurbsCopyUVSet')

@_factories._addCmdDocs
def nurbsCube(*args, **kwargs):
    res = cmds.nurbsCube(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def nurbsCurveToBezier(*args, **kwargs):
    res = cmds.nurbsCurveToBezier(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsEditUV = _factories._addCmdDocs('nurbsEditUV')

@_factories._addCmdDocs
def nurbsPlane(*args, **kwargs):
    res = cmds.nurbsPlane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsSelect = _factories._addCmdDocs('nurbsSelect')

@_factories._addCmdDocs
def nurbsSquare(*args, **kwargs):
    res = cmds.nurbsSquare(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsToPoly = _factories._addCmdDocs('nurbsToPoly')

nurbsToPolygonsPref = _factories._addCmdDocs('nurbsToPolygonsPref')

@_factories._addCmdDocs
def nurbsToSubdiv(*args, **kwargs):
    res = cmds.nurbsToSubdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nurbsToSubdivPref = _factories._addCmdDocs('nurbsToSubdivPref')

nurbsUVSet = _factories._addCmdDocs('nurbsUVSet')

@_factories._addCmdDocs
def offsetCurve(*args, **kwargs):
    res = cmds.offsetCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

offsetCurveOnSurface = _factories._addCmdDocs('offsetCurveOnSurface')

@_factories._addCmdDocs
def offsetSurface(*args, **kwargs):
    res = cmds.offsetSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

planarSrf = _factories._addCmdDocs('planarSrf')

@_factories._addCmdDocs
def plane(*args, **kwargs):
    res = cmds.plane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

pointCurveConstraint = _factories._addCmdDocs('pointCurveConstraint')

pointOnCurve = _factories._addCmdDocs('pointOnCurve')

pointOnSurface = _factories._addCmdDocs('pointOnSurface')

pointPosition = _factories._addCmdDocs(pointPosition)

@_factories._addCmdDocs
def polyAppend(*args, **kwargs):
    res = cmds.polyAppend(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyAppendVertex(*args, **kwargs):
    res = cmds.polyAppendVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyAutoProjection = _factories._addCmdDocs('polyAutoProjection')

polyAverageNormal = _factories._addCmdDocs('polyAverageNormal')

@_factories._addCmdDocs
def polyAverageVertex(*args, **kwargs):
    res = cmds.polyAverageVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyBevel(*args, **kwargs):
    res = cmds.polyBevel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyBevel3(*args, **kwargs):
    res = cmds.polyBevel3(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyBlendColor = _factories._addCmdDocs('polyBlendColor')

@_factories._addCmdDocs
def polyBlindData(*args, **kwargs):
    res = cmds.polyBlindData(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyBoolOp(*args, **kwargs):
    res = cmds.polyBoolOp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyBridgeEdge(*args, **kwargs):
    res = cmds.polyBridgeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCBoolOp(*args, **kwargs):
    res = cmds.polyCBoolOp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCacheMonitor = _factories._addCmdDocs('polyCacheMonitor')

polyCanBridgeEdge = _factories._addCmdDocs('polyCanBridgeEdge')

polyCheck = _factories._addCmdDocs('polyCheck')

@_factories._addCmdDocs
def polyChipOff(*args, **kwargs):
    res = cmds.polyChipOff(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCircularize(*args, **kwargs):
    res = cmds.polyCircularize(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCircularizeEdge = _factories._addCmdDocs('polyCircularizeEdge')

polyCircularizeFace = _factories._addCmdDocs('polyCircularizeFace')

@_factories._addCmdDocs
def polyClean(*args, **kwargs):
    res = cmds.polyClean(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyClipboard = _factories._addCmdDocs('polyClipboard')

@_factories._addCmdDocs
def polyCloseBorder(*args, **kwargs):
    res = cmds.polyCloseBorder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCollapseEdge(*args, **kwargs):
    res = cmds.polyCollapseEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCollapseFacet = _factories._addCmdDocs('polyCollapseFacet')

polyCollapseTweaks = _factories._addCmdDocs('polyCollapseTweaks')

polyColorBlindData = _factories._addCmdDocs('polyColorBlindData')

@_factories._addCmdDocs
def polyColorDel(*args, **kwargs):
    res = cmds.polyColorDel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyColorMod(*args, **kwargs):
    res = cmds.polyColorMod(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyColorPerVertex(*args, **kwargs):
    res = cmds.polyColorPerVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyColorSet = _factories._addCmdDocs('polyColorSet')

polyCompare = _factories._addCmdDocs('polyCompare')

@_factories._addCmdDocs
def polyCone(*args, **kwargs):
    res = cmds.polyCone(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyConnectComponents(*args, **kwargs):
    res = cmds.polyConnectComponents(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyContourProjection = _factories._addCmdDocs('polyContourProjection')

@_factories._addCmdDocs
def polyCopyUV(*args, **kwargs):
    res = cmds.polyCopyUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCrease(*args, **kwargs):
    res = cmds.polyCrease(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCreateFacet = _factories._addCmdDocs('polyCreateFacet')

@_factories._addCmdDocs
def polyCube(*args, **kwargs):
    res = cmds.polyCube(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCut(*args, **kwargs):
    res = cmds.polyCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyCylinder(*args, **kwargs):
    res = cmds.polyCylinder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyCylindricalProjection = _factories._addCmdDocs('polyCylindricalProjection')

@_factories._addCmdDocs
def polyDelEdge(*args, **kwargs):
    res = cmds.polyDelEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyDelFacet(*args, **kwargs):
    res = cmds.polyDelFacet(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyDelVertex(*args, **kwargs):
    res = cmds.polyDelVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyDuplicateAndConnect = _factories._addCmdDocs('polyDuplicateAndConnect')

@_factories._addCmdDocs
def polyDuplicateEdge(*args, **kwargs):
    res = cmds.polyDuplicateEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyEditEdgeFlow(*args, **kwargs):
    res = cmds.polyEditEdgeFlow(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyEditUV = _factories._addCmdDocs('polyEditUV')

polyEditUVShell = _factories._addCmdDocs('polyEditUVShell')

polyEvaluate = _factories._addCmdDocs('polyEvaluate')

@_factories._addCmdDocs
def polyExtrudeEdge(*args, **kwargs):
    res = cmds.polyExtrudeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyExtrudeFacet = _factories._addCmdDocs('polyExtrudeFacet')

@_factories._addCmdDocs
def polyExtrudeVertex(*args, **kwargs):
    res = cmds.polyExtrudeVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyFlipEdge(*args, **kwargs):
    res = cmds.polyFlipEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyFlipUV(*args, **kwargs):
    res = cmds.polyFlipUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyForceUV = _factories._addCmdDocs('polyForceUV')

polyGeoSampler = _factories._addCmdDocs('polyGeoSampler')

@_factories._addCmdDocs
def polyHelix(*args, **kwargs):
    res = cmds.polyHelix(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyHole = _factories._addCmdDocs('polyHole')

polyInfo = _factories._addCmdDocs('polyInfo')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def polyLayoutUV(*args, **kwargs):
    res = cmds.polyLayoutUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyListComponentConversion = _factories._addCmdDocs('polyListComponentConversion')

@_factories._addCmdDocs
def polyMapCut(*args, **kwargs):
    res = cmds.polyMapCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMapDel(*args, **kwargs):
    res = cmds.polyMapDel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMapSew(*args, **kwargs):
    res = cmds.polyMapSew(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMapSewMove(*args, **kwargs):
    res = cmds.polyMapSewMove(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMergeEdge(*args, **kwargs):
    res = cmds.polyMergeEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMergeFacet = _factories._addCmdDocs('polyMergeFacet')

@_factories._addCmdDocs
def polyMergeUV(*args, **kwargs):
    res = cmds.polyMergeUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMergeVertex = _factories._addCmdDocs('polyMergeVertex')

polyMirrorFace = _factories._addCmdDocs('polyMirrorFace')

@_factories._addCmdDocs
def polyMoveEdge(*args, **kwargs):
    res = cmds.polyMoveEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMoveFacet = _factories._addCmdDocs('polyMoveFacet')

@_factories._addCmdDocs
def polyMoveFacetUV(*args, **kwargs):
    res = cmds.polyMoveFacetUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMoveUV(*args, **kwargs):
    res = cmds.polyMoveUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyMoveVertex(*args, **kwargs):
    res = cmds.polyMoveVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyMultiLayoutUV = _factories._addCmdDocs('polyMultiLayoutUV')

@_factories._addCmdDocs
def polyNormal(*args, **kwargs):
    res = cmds.polyNormal(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyNormalPerVertex(*args, **kwargs):
    res = cmds.polyNormalPerVertex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyNormalizeUV(*args, **kwargs):
    res = cmds.polyNormalizeUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyOptUvs(*args, **kwargs):
    res = cmds.polyOptUvs(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyOptions = _factories._addCmdDocs('polyOptions')

polyOutput = _factories._addCmdDocs('polyOutput')

@_factories._addCmdDocs
def polyPinUV(*args, **kwargs):
    res = cmds.polyPinUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyPipe(*args, **kwargs):
    res = cmds.polyPipe(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyPlanarProjection = _factories._addCmdDocs('polyPlanarProjection')

@_factories._addCmdDocs
def polyPlane(*args, **kwargs):
    res = cmds.polyPlane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyPlatonicSolid(*args, **kwargs):
    res = cmds.polyPlatonicSolid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyPoke(*args, **kwargs):
    res = cmds.polyPoke(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyPrimitive(*args, **kwargs):
    res = cmds.polyPrimitive(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyPrism(*args, **kwargs):
    res = cmds.polyPrism(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyProjectCurve(*args, **kwargs):
    res = cmds.polyProjectCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyProjection = _factories._addCmdDocs('polyProjection')

@_factories._addCmdDocs
def polyPyramid(*args, **kwargs):
    res = cmds.polyPyramid(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyQuad(*args, **kwargs):
    res = cmds.polyQuad(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyQueryBlindData = _factories._addCmdDocs('polyQueryBlindData')

@_factories._addCmdDocs
def polyReduce(*args, **kwargs):
    res = cmds.polyReduce(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyRemesh(*args, **kwargs):
    res = cmds.polyRemesh(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySelect = _factories._addCmdDocs('polySelect')

polySelectConstraint = _factories._addCmdDocs('polySelectConstraint')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def polySeparate(*args, **kwargs):
    res = cmds.polySeparate(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySetToFaceNormal = _factories._addCmdDocs('polySetToFaceNormal')

@_factories._addCmdDocs
def polySewEdge(*args, **kwargs):
    res = cmds.polySewEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySlideEdge = _factories._addCmdDocs('polySlideEdge')

@_factories._addCmdDocs
def polySmooth(*args, **kwargs):
    res = cmds.polySmooth(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polySoftEdge(*args, **kwargs):
    res = cmds.polySoftEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polySphere(*args, **kwargs):
    res = cmds.polySphere(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySphericalProjection = _factories._addCmdDocs('polySphericalProjection')

@_factories._addCmdDocs
def polySplit(*args, **kwargs):
    res = cmds.polySplit(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polySplitEdge(*args, **kwargs):
    res = cmds.polySplitEdge(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polySplitRing(*args, **kwargs):
    res = cmds.polySplitRing(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySplitVertex = _factories._addCmdDocs('polySplitVertex')

@_factories._addCmdDocs
def polyStraightenUVBorder(*args, **kwargs):
    res = cmds.polyStraightenUVBorder(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polySubdivideEdge = _factories._addCmdDocs('polySubdivideEdge')

polySubdivideFacet = _factories._addCmdDocs('polySubdivideFacet')

@_factories._addCmdDocs
def polyToSubdiv(*args, **kwargs):
    res = cmds.polyToSubdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyTorus(*args, **kwargs):
    res = cmds.polyTorus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyTransfer(*args, **kwargs):
    res = cmds.polyTransfer(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyTriangulate(*args, **kwargs):
    res = cmds.polyTriangulate(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyUVCoverage = _factories._addCmdDocs('polyUVCoverage')

polyUVOverlap = _factories._addCmdDocs('polyUVOverlap')

@_factories._addCmdDocs
def polyUVRectangle(*args, **kwargs):
    res = cmds.polyUVRectangle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

polyUVSet = _factories._addCmdDocs('polyUVSet')

polyUVStackSimilarShells = _factories._addCmdDocs('polyUVStackSimilarShells')

@_factories._addCmdDocs
def polyUnite(*args, **kwargs):
    res = cmds.polyUnite(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def polyWedgeFace(*args, **kwargs):
    res = cmds.polyWedgeFace(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def projectCurve(*args, **kwargs):
    res = cmds.projectCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def projectTangent(*args, **kwargs):
    res = cmds.projectTangent(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

propMove = _factories._addCmdDocs('propMove')

querySubdiv = _factories._addCmdDocs('querySubdiv')

@_factories._addCmdDocs
def rebuildCurve(*args, **kwargs):
    res = cmds.rebuildCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def rebuildSurface(*args, **kwargs):
    res = cmds.rebuildSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

refineSubdivSelectionList = _factories._addCmdDocs('refineSubdivSelectionList')

@_factories._addCmdDocs
def reverseCurve(*args, **kwargs):
    res = cmds.reverseCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def reverseSurface(*args, **kwargs):
    res = cmds.reverseSurface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def revolve(*args, **kwargs):
    res = cmds.revolve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def roundConstantRadius(*args, **kwargs):
    res = cmds.roundConstantRadius(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

setXformManip = _factories._addCmdDocs('setXformManip')

showMetadata = _factories._addCmdDocs('showMetadata')

singleProfileBirailSurface = _factories._addCmdDocs('singleProfileBirailSurface')

@_factories._addCmdDocs
def smoothCurve(*args, **kwargs):
    res = cmds.smoothCurve(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

smoothTangentSurface = _factories._addCmdDocs('smoothTangentSurface')

@_factories._addCmdDocs
def sphere(*args, **kwargs):
    res = cmds.sphere(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

squareSurface = _factories._addCmdDocs('squareSurface')

stitchSurface = _factories._addCmdDocs('stitchSurface')

stitchSurfacePoints = _factories._addCmdDocs('stitchSurfacePoints')

subdAutoProjection = _factories._addCmdDocs('subdAutoProjection')

@_factories._addCmdDocs
def subdCleanTopology(*args, **kwargs):
    res = cmds.subdCleanTopology(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdCollapse = _factories._addCmdDocs('subdCollapse')

subdDuplicateAndConnect = _factories._addCmdDocs('subdDuplicateAndConnect')

subdEditUV = _factories._addCmdDocs('subdEditUV')

@_factories._addCmdDocs
def subdLayoutUV(*args, **kwargs):
    res = cmds.subdLayoutUV(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdListComponentConversion = _factories._addCmdDocs('subdListComponentConversion')

@_factories._addCmdDocs
def subdMapCut(*args, **kwargs):
    res = cmds.subdMapCut(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def subdMapSewMove(*args, **kwargs):
    res = cmds.subdMapSewMove(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdMatchTopology = _factories._addCmdDocs('subdMatchTopology')

subdMirror = _factories._addCmdDocs('subdMirror')

subdPlanarProjection = _factories._addCmdDocs('subdPlanarProjection')

subdToBlind = _factories._addCmdDocs('subdToBlind')

subdToPoly = _factories._addCmdDocs('subdToPoly')

subdTransferUVsToCache = _factories._addCmdDocs('subdTransferUVsToCache')

@_factories._addCmdDocs
def subdiv(*args, **kwargs):
    res = cmds.subdiv(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

subdivCrease = _factories._addCmdDocs('subdivCrease')

subdivDisplaySmoothness = _factories._addCmdDocs('subdivDisplaySmoothness')

_surface = surface

@_factories._addCmdDocs
def surface(*args, **kwargs):
    res = _surface(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

textCurves = _factories._addCmdDocs('textCurves')

tolerance = _factories._addCmdDocs('tolerance')

@_factories._addCmdDocs
def torus(*args, **kwargs):
    res = cmds.torus(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def transferAttributes(*args, **kwargs):
    res = cmds.transferAttributes(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

transferShadingSets = _factories._addCmdDocs('transferShadingSets')

@_factories._addCmdDocs
def trim(*args, **kwargs):
    res = cmds.trim(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

unfold = _factories._addCmdDocs('unfold')

untangleUV = _factories._addCmdDocs('untangleUV')

@_factories._addCmdDocs
def untrim(*args, **kwargs):
    res = cmds.untrim(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

uvSnapshot = _factories._addCmdDocs('uvSnapshot')

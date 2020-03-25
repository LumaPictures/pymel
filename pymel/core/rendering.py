"""Functions related to rendering"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import pymel.util as _util
import pymel.internal.factories as _factories
import pymel.core.general as _general
import pymel.core.language as _language
if False:
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]


def shadingNode(*args, **kwargs):
    res = cmds.shadingNode(*args, **kwargs)
    if res is not None:
        return _general.PyNode(res)


def createSurfaceShader(shadertype, name=None):
    """
    create a shader and shading group
    """
    classification = _general.getClassification(shadertype)
    # print classification

    newShader = None
    from . import nodetypes
    # if 'shader/surface' in classification:
    if 'rendernode/mentalray/material' in classification:
        newShader = nodetypes.DependNode(_language.mel.mrCreateCustomNode("-asShader", "", shadertype))
    else:
        newShader = nodetypes.DependNode(_language.mel.renderCreateNode("-asShader", "surfaceShader", shadertype, "", 0, 0, 0, 1, 0, ""))
    # else:
    #    raise TypeError, "%s is not a valid surface shader type. shader must be classified as 'shader/surface'" % shadertype
    sg = newShader.shadingGroups()[0]
    if name:
        newShader = newShader.rename(name)
        sg = sg.rename(name + 'SG')
    return newShader, sg


def lsThroughFilter(*args, **kwargs):
    """
    Modifications:
      - returns an empty list when the result is None
      - returns wrapped classes
    """
    return [_general.PyNode(x) for x in
            _util.listForNone(cmds.lsThroughFilter(*args, **kwargs))]


def pointLight(*args, **kwargs):
    """
    Maya Bug Fix:
      - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.pointLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False))
        if name:
            tmp = cmds.pointLight(*args, **kwargs)
            tmp = cmds.rename(cmds.listRelatives(tmp, parent=1)[0], name)
            return _general.PyNode(cmds.listRelatives(tmp, shapes=1)[0])

    return _general.PyNode(cmds.pointLight(*args, **kwargs))


def spotLight(*args, **kwargs):
    """
    Maya Bug Fix:
      - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.spotLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False))
        if name:
            tmp = cmds.spotLight(*args, **kwargs)
            tmp = cmds.rename(cmds.listRelatives(tmp, parent=1)[0], name)
            return _general.PyNode(cmds.listRelatives(tmp, shapes=1)[0])

    return _general.PyNode(cmds.spotLight(*args, **kwargs))


def directionalLight(*args, **kwargs):
    """
    Maya Bug Fix:
      - name flag was ignored
    """

    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.directionalLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False))
        if name:
            tmp = cmds.directionalLight(*args, **kwargs)
            tmp = cmds.rename(cmds.listRelatives(tmp, parent=1)[0], name)
            return _general.PyNode(cmds.listRelatives(tmp, shapes=1)[0])

    return _general.PyNode(cmds.directionalLight(*args, **kwargs))


def ambientLight(*args, **kwargs):
    """
    Maya Bug Fix:
      - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.ambientLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False))
        if name:
            tmp = cmds.ambientLight(*args, **kwargs)
            tmp = cmds.rename(cmds.listRelatives(tmp, parent=1)[0], name)
            return _general.PyNode(cmds.listRelatives(tmp, shapes=1)[0])

    return _general.PyNode(cmds.ambientLight(*args, **kwargs))

# def createRenderLayer(*args, **kwargs):
#    return _general.PyNode( cmds.createRenderLayer(*args, **kwargs) )
#
# def createDisplayLayer(*args, **kwargs):
#    return _general.PyNode( cmds.createDisplayLayer(*args, **kwargs) )

# ------ Do not edit below this line --------

_ambientLight = ambientLight

@_factories.addCmdDocs
def ambientLight(*args, **kwargs):
    res = _ambientLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

assignViewportFactories = _factories.getCmdFunc('assignViewportFactories')

@_factories.addCmdDocs
def batchRender(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['mc', 'melCommand', 'prc', 'preRenderCommand', 'rco', 'renderCommandOptions']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.batchRender(*args, **kwargs)
    return res

binMembership = _factories.getCmdFunc('binMembership')

@_factories.addCmdDocs
def camera(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['hc', 'homeCommand', 'jc', 'journalCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.camera(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def cameraSet(*args, **kwargs):
    res = cmds.cameraSet(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def cameraView(*args, **kwargs):
    res = cmds.cameraView(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

checkDefaultRenderGlobals = _factories.getCmdFunc('checkDefaultRenderGlobals')

convertIffToPsd = _factories.getCmdFunc('convertIffToPsd')

convertSolidTx = _factories.getCmdFunc('convertSolidTx')

convertTessellation = _factories.getCmdFunc('convertTessellation')

createLayeredPsdFile = _factories.getCmdFunc('createLayeredPsdFile')

@_factories.addCmdDocs
def createRenderLayer(*args, **kwargs):
    res = cmds.createRenderLayer(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['createRenderLayer']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def defaultLightListCheckBox(*args, **kwargs):
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
    res = cmds.defaultLightListCheckBox(*args, **kwargs)
    return res

_directionalLight = directionalLight

@_factories.addCmdDocs
def directionalLight(*args, **kwargs):
    res = _directionalLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

displacementToPoly = _factories.getCmdFunc('displacementToPoly')

doBlur = _factories.getCmdFunc('doBlur')

dolly = _factories.getCmdFunc('dolly')

editRenderLayerAdjustment = _factories.getCmdFunc('editRenderLayerAdjustment')

editRenderLayerGlobals = _factories.getCmdFunc('editRenderLayerGlobals')

editRenderLayerMembers = _factories.getCmdFunc('editRenderLayerMembers')

@_factories.addCmdDocs
def exclusiveLightCheckBox(*args, **kwargs):
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
    res = cmds.exclusiveLightCheckBox(*args, **kwargs)
    return res

frameBufferName = _factories.getCmdFunc('frameBufferName')

getRenderDependencies = _factories.getCmdFunc('getRenderDependencies')

getRenderTasks = _factories.getCmdFunc('getRenderTasks')

glRender = _factories.getCmdFunc('glRender')

glRenderEditor = _factories.getCmdFunc('glRenderEditor')

@_factories.addCmdDocs
def hwReflectionMap(*args, **kwargs):
    res = cmds.hwReflectionMap(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

hwRender = _factories.getCmdFunc('hwRender')

hwRenderLoad = _factories.getCmdFunc('hwRenderLoad')

@_factories.addCmdDocs
def imagePlane(*args, **kwargs):
    res = cmds.imagePlane(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    if isinstance(res, list) and len(res) == 1:
        # unpack for specific query flags
        unpackFlags = {'c', 'camera', 'h', 'height', 'lookThrough', 'lt', 'maintainRatio', 'mr', 'showInAllViews', 'sia', 'w', 'width'}
        if kwargs.get('query', kwargs.get('q', False)) and not unpackFlags.isdisjoint(kwargs):
            res = res[0]
    return res

iprEngine = _factories.getCmdFunc('iprEngine')

@_factories.addCmdDocs
def layeredShaderPort(*args, **kwargs):
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
    res = cmds.layeredShaderPort(*args, **kwargs)
    return res

@_factories.addCmdDocs
def layeredTexturePort(*args, **kwargs):
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
    res = cmds.layeredTexturePort(*args, **kwargs)
    return res

@_factories.addCmdDocs
def lightList(*args, **kwargs):
    res = cmds.lightList(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

lightlink = _factories.getCmdFunc('lightlink')

listCameras = _factories.getCmdFunc('listCameras')

lookThru = _factories.getCmdFunc('lookThru')

lsThroughFilter = _factories.addCmdDocs(lsThroughFilter)

makebot = _factories.getCmdFunc('makebot')

mayaHasRenderSetup = _factories.getCmdFunc('mayaHasRenderSetup')

@_factories.addCmdDocs
def nodeIconButton(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nodeIconButton(*args, **kwargs)
    return res

nodePreset = _factories.getCmdFunc('nodePreset')

ogsRender = _factories.getCmdFunc('ogsRender')

orbit = _factories.getCmdFunc('orbit')

panZoom = _factories.getCmdFunc('panZoom')

perCameraVisibility = _factories.getCmdFunc('perCameraVisibility')

_pointLight = pointLight

@_factories.addCmdDocs
def pointLight(*args, **kwargs):
    res = _pointLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

preferredRenderer = _factories.getCmdFunc('preferredRenderer')

@_factories.addCmdDocs
def prepareRender(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pof', 'pol', 'por', 'postRender', 'postRenderFrame', 'postRenderLayer', 'preRender', 'preRenderFrame', 'preRenderLayer', 'prf', 'prl', 'prr', 'settingsUI', 'sui', 'traversalSetInit', 'tsi']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.prepareRender(*args, **kwargs)
    return res

projectionManip = _factories.getCmdFunc('projectionManip')

@_factories.addCmdDocs
def psdChannelOutliner(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.psdChannelOutliner(*args, **kwargs)
    return res

psdEditTextureFile = _factories.getCmdFunc('psdEditTextureFile')

psdExport = _factories.getCmdFunc('psdExport')

psdTextureFile = _factories.getCmdFunc('psdTextureFile')

@_factories.addCmdDocs
def rampColorPort(*args, **kwargs):
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
    res = cmds.rampColorPort(*args, **kwargs)
    return res

render = _factories.getCmdFunc('render')

renderGlobalsNode = _factories.getCmdFunc('renderGlobalsNode')

renderInfo = _factories.getCmdFunc('renderInfo')

renderLayerPostProcess = _factories.getCmdFunc('renderLayerPostProcess')

renderManip = _factories.getCmdFunc('renderManip')

renderPartition = _factories.getCmdFunc('renderPartition')

renderPassRegistry = _factories.getCmdFunc('renderPassRegistry')

renderQualityNode = _factories.getCmdFunc('renderQualityNode')

renderSettings = _factories.getCmdFunc('renderSettings')

renderThumbnailUpdate = _factories.getCmdFunc('renderThumbnailUpdate')

@_factories.addCmdDocs
def renderWindowEditor(*args, **kwargs):
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
    res = cmds.renderWindowEditor(*args, **kwargs)
    return res

@_factories.addCmdDocs
def renderer(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['commandRenderProcedure', 'cr']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.renderer(*args, **kwargs)
    return res

resolutionNode = _factories.getCmdFunc('resolutionNode')

roll = _factories.getCmdFunc('roll')

sampleImage = _factories.getCmdFunc('sampleImage')

setDefaultShadingGroup = _factories.getCmdFunc('setDefaultShadingGroup')

setRenderPassType = _factories.getCmdFunc('setRenderPassType')

shadingConnection = _factories.getCmdFunc('shadingConnection')

shadingNetworkCompare = _factories.getCmdFunc('shadingNetworkCompare')

shadingNode = _factories.addCmdDocs(shadingNode)

showShadingGroupAttrEditor = _factories.getCmdFunc('showShadingGroupAttrEditor')

soloMaterial = _factories.getCmdFunc('soloMaterial')

_spotLight = spotLight

@_factories.addCmdDocs
def spotLight(*args, **kwargs):
    res = _spotLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def spotLightPreviewPort(*args, **kwargs):
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
    res = cmds.spotLightPreviewPort(*args, **kwargs)
    return res

surfaceSampler = _factories.getCmdFunc('surfaceSampler')

surfaceShaderList = _factories.getCmdFunc('surfaceShaderList')

swatchRefresh = _factories.getCmdFunc('swatchRefresh')

@_factories.addCmdDocs
def textureWindow(*args, **kwargs):
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
    res = cmds.textureWindow(*args, **kwargs)
    return res

track = _factories.getCmdFunc('track')

tumble = _factories.getCmdFunc('tumble')

uvLink = _factories.getCmdFunc('uvLink')

viewCamera = _factories.getCmdFunc('viewCamera')

viewClipPlane = _factories.getCmdFunc('viewClipPlane')

viewFit = _factories.getCmdFunc('viewFit')

viewHeadOn = _factories.getCmdFunc('viewHeadOn')

viewLookAt = _factories.getCmdFunc('viewLookAt')

viewPlace = _factories.getCmdFunc('viewPlace')

viewSet = _factories.getCmdFunc('viewSet')

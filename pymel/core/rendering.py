"""Functions related to rendering"""

import pymel.util as _util
import pymel.internal.factories as _factories
import general as _general
import language as _language
import pymel.internal.pmcmds as cmds


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
    import nodetypes
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
    return map(_general.PyNode, _util.listForNone(cmds.lsThroughFilter(*args, **kwargs)))

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

@_factories._addCmdDocs
def ambientLight(*args, **kwargs):
    res = _ambientLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

assignViewportFactories = _factories._addCmdDocs('assignViewportFactories')

@_factories._addCmdDocs
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

binMembership = _factories._addCmdDocs('binMembership')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def cameraSet(*args, **kwargs):
    res = cmds.cameraSet(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def cameraView(*args, **kwargs):
    res = cmds.cameraView(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

checkDefaultRenderGlobals = _factories._addCmdDocs('checkDefaultRenderGlobals')

convertIffToPsd = _factories._addCmdDocs('convertIffToPsd')

convertSolidTx = _factories._addCmdDocs('convertSolidTx')

convertTessellation = _factories._addCmdDocs('convertTessellation')

createLayeredPsdFile = _factories._addCmdDocs('createLayeredPsdFile')

@_factories._addCmdDocs
def createRenderLayer(*args, **kwargs):
    res = cmds.createRenderLayer(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['createRenderLayer']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def directionalLight(*args, **kwargs):
    res = _directionalLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

displacementToPoly = _factories._addCmdDocs('displacementToPoly')

doBlur = _factories._addCmdDocs('doBlur')

dolly = _factories._addCmdDocs('dolly')

editRenderLayerAdjustment = _factories._addCmdDocs('editRenderLayerAdjustment')

editRenderLayerGlobals = _factories._addCmdDocs('editRenderLayerGlobals')

editRenderLayerMembers = _factories._addCmdDocs('editRenderLayerMembers')

@_factories._addCmdDocs
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

frameBufferName = _factories._addCmdDocs('frameBufferName')

getRenderDependencies = _factories._addCmdDocs('getRenderDependencies')

getRenderTasks = _factories._addCmdDocs('getRenderTasks')

glRender = _factories._addCmdDocs('glRender')

glRenderEditor = _factories._addCmdDocs('glRenderEditor')

@_factories._addCmdDocs
def hwReflectionMap(*args, **kwargs):
    res = cmds.hwReflectionMap(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

hwRender = _factories._addCmdDocs('hwRender')

hwRenderLoad = _factories._addCmdDocs('hwRenderLoad')

@_factories._addCmdDocs
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

iprEngine = _factories._addCmdDocs('iprEngine')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

@_factories._addCmdDocs
def lightList(*args, **kwargs):
    res = cmds.lightList(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

lightlink = _factories._addCmdDocs('lightlink')

listCameras = _factories._addCmdDocs('listCameras')

lookThru = _factories._addCmdDocs('lookThru')

lsThroughFilter = _factories._addCmdDocs(lsThroughFilter)

makebot = _factories._addCmdDocs('makebot')

@_factories._addCmdDocs
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

nodePreset = _factories._addCmdDocs('nodePreset')

ogsRender = _factories._addCmdDocs('ogsRender')

orbit = _factories._addCmdDocs('orbit')

panZoom = _factories._addCmdDocs('panZoom')

perCameraVisibility = _factories._addCmdDocs('perCameraVisibility')

_pointLight = pointLight

@_factories._addCmdDocs
def pointLight(*args, **kwargs):
    res = _pointLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

preferredRenderer = _factories._addCmdDocs('preferredRenderer')

@_factories._addCmdDocs
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

projectionManip = _factories._addCmdDocs('projectionManip')

@_factories._addCmdDocs
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

psdEditTextureFile = _factories._addCmdDocs('psdEditTextureFile')

psdExport = _factories._addCmdDocs('psdExport')

psdTextureFile = _factories._addCmdDocs('psdTextureFile')

@_factories._addCmdDocs
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

render = _factories._addCmdDocs('render')

renderGlobalsNode = _factories._addCmdDocs('renderGlobalsNode')

renderInfo = _factories._addCmdDocs('renderInfo')

renderLayerPostProcess = _factories._addCmdDocs('renderLayerPostProcess')

renderManip = _factories._addCmdDocs('renderManip')

renderPartition = _factories._addCmdDocs('renderPartition')

renderPassRegistry = _factories._addCmdDocs('renderPassRegistry')

renderQualityNode = _factories._addCmdDocs('renderQualityNode')

renderSettings = _factories._addCmdDocs('renderSettings')

renderThumbnailUpdate = _factories._addCmdDocs('renderThumbnailUpdate')

@_factories._addCmdDocs
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

@_factories._addCmdDocs
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

resolutionNode = _factories._addCmdDocs('resolutionNode')

roll = _factories._addCmdDocs('roll')

sampleImage = _factories._addCmdDocs('sampleImage')

setDefaultShadingGroup = _factories._addCmdDocs('setDefaultShadingGroup')

setRenderPassType = _factories._addCmdDocs('setRenderPassType')

shadingConnection = _factories._addCmdDocs('shadingConnection')

shadingNetworkCompare = _factories._addCmdDocs('shadingNetworkCompare')

shadingNode = _factories._addCmdDocs(shadingNode)

showShadingGroupAttrEditor = _factories._addCmdDocs('showShadingGroupAttrEditor')

soloMaterial = _factories._addCmdDocs('soloMaterial')

_spotLight = spotLight

@_factories._addCmdDocs
def spotLight(*args, **kwargs):
    res = _spotLight(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
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

surfaceSampler = _factories._addCmdDocs('surfaceSampler')

surfaceShaderList = _factories._addCmdDocs('surfaceShaderList')

swatchRefresh = _factories._addCmdDocs('swatchRefresh')

@_factories._addCmdDocs
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

track = _factories._addCmdDocs('track')

tumble = _factories._addCmdDocs('tumble')

uvLink = _factories._addCmdDocs('uvLink')

viewCamera = _factories._addCmdDocs('viewCamera')

viewClipPlane = _factories._addCmdDocs('viewClipPlane')

viewFit = _factories._addCmdDocs('viewFit')

viewHeadOn = _factories._addCmdDocs('viewHeadOn')

viewLookAt = _factories._addCmdDocs('viewLookAt')

viewPlace = _factories._addCmdDocs('viewPlace')

viewSet = _factories._addCmdDocs('viewSet')

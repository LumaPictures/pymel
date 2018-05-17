"""Functions related to fx"""

import pymel.internal.factories as _factories
import general as _general
import pymel.internal.pmcmds as cmds

# ------ Do not edit below this line --------
@_factories._addCmdDocs
def addDynamic(*args, **kwargs):
    res = cmds.addDynamic(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['addDynamic']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories._addCmdDocs
def addPP(*args, **kwargs):
    res = cmds.addPP(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['addPP']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories._addCmdDocs
def air(*args, **kwargs):
    res = cmds.air(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def arrayMapper(*args, **kwargs):
    res = cmds.arrayMapper(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

collision = _factories._addCmdDocs('collision')

colorAtPoint = _factories._addCmdDocs('colorAtPoint')

@_factories._addCmdDocs
def connectDynamic(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['addScriptHandler', 'ash']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.connectDynamic(*args, **kwargs)
    return res

constrain = _factories._addCmdDocs('constrain')

@_factories._addCmdDocs
def drag(*args, **kwargs):
    res = cmds.drag(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

dynCache = _factories._addCmdDocs('dynCache')

dynControl = _factories._addCmdDocs('dynControl')

dynExport = _factories._addCmdDocs('dynExport')

dynExpression = _factories._addCmdDocs('dynExpression')

@_factories._addCmdDocs
def dynGlobals(*args, **kwargs):
    res = cmds.dynGlobals(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def dynPaintEditor(*args, **kwargs):
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
    res = cmds.dynPaintEditor(*args, **kwargs)
    return res

dynPref = _factories._addCmdDocs('dynPref')

emit = _factories._addCmdDocs('emit')

@_factories._addCmdDocs
def emitter(*args, **kwargs):
    res = cmds.emitter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def event(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pr', 'proc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.event(*args, **kwargs)
    return res

@_factories._addCmdDocs
def expression(*args, **kwargs):
    res = cmds.expression(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

expressionEditorListen = _factories._addCmdDocs('expressionEditorListen')

fluidCacheInfo = _factories._addCmdDocs('fluidCacheInfo')

@_factories._addCmdDocs
def fluidEmitter(*args, **kwargs):
    res = cmds.fluidEmitter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

fluidVoxelInfo = _factories._addCmdDocs('fluidVoxelInfo')

getDefaultBrush = _factories._addCmdDocs('getDefaultBrush')

getFluidAttr = _factories._addCmdDocs('getFluidAttr')

getParticleAttr = _factories._addCmdDocs('getParticleAttr')

goal = _factories._addCmdDocs('goal')

@_factories._addCmdDocs
def gravity(*args, **kwargs):
    res = cmds.gravity(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

loadFluid = _factories._addCmdDocs('loadFluid')

@_factories._addCmdDocs
def nBase(*args, **kwargs):
    res = cmds.nBase(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def nParticle(*args, **kwargs):
    res = cmds.nParticle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nSoft = _factories._addCmdDocs('nSoft')

newton = _factories._addCmdDocs('newton')

paintEffectsDisplay = _factories._addCmdDocs('paintEffectsDisplay')

@_factories._addCmdDocs
def particle(*args, **kwargs):
    res = cmds.particle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

particleExists = _factories._addCmdDocs('particleExists')

particleFill = _factories._addCmdDocs('particleFill')

particleInstancer = _factories._addCmdDocs('particleInstancer')

particleRenderInfo = _factories._addCmdDocs('particleRenderInfo')

pfxstrokes = _factories._addCmdDocs('pfxstrokes')

radial = _factories._addCmdDocs('radial')

resampleFluid = _factories._addCmdDocs('resampleFluid')

@_factories._addCmdDocs
def rigidBody(*args, **kwargs):
    res = cmds.rigidBody(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def rigidSolver(*args, **kwargs):
    res = cmds.rigidSolver(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

runup = _factories._addCmdDocs('runup')

saveFluid = _factories._addCmdDocs('saveFluid')

saveInitialState = _factories._addCmdDocs('saveInitialState')

setDynamic = _factories._addCmdDocs('setDynamic')

setFluidAttr = _factories._addCmdDocs('setFluidAttr')

setParticleAttr = _factories._addCmdDocs('setParticleAttr')

soft = _factories._addCmdDocs('soft')

@_factories._addCmdDocs
def spring(*args, **kwargs):
    res = cmds.spring(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories._addCmdDocs
def stroke(*args, **kwargs):
    res = cmds.stroke(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

truncateFluidCache = _factories._addCmdDocs('truncateFluidCache')

truncateHairCache = _factories._addCmdDocs('truncateHairCache')

@_factories._addCmdDocs
def turbulence(*args, **kwargs):
    res = cmds.turbulence(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def uniform(*args, **kwargs):
    res = cmds.uniform(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def volumeAxis(*args, **kwargs):
    res = cmds.volumeAxis(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories._addCmdDocs
def vortex(*args, **kwargs):
    res = cmds.vortex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

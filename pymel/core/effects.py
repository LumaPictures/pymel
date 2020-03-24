"""Functions related to fx"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pymel.internal.factories as _factories
import pymel.core.general as _general
if False:
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]

# ------ Do not edit below this line --------

@_factories.addCmdDocs
def addDynamic(*args, **kwargs):
    res = cmds.addDynamic(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['addDynamic']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def addPP(*args, **kwargs):
    res = cmds.addPP(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['addPP']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def air(*args, **kwargs):
    res = cmds.air(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def arrayMapper(*args, **kwargs):
    res = cmds.arrayMapper(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

collision = _factories.getCmdFunc('collision')

colorAtPoint = _factories.getCmdFunc('colorAtPoint')

@_factories.addCmdDocs
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

constrain = _factories.getCmdFunc('constrain')

@_factories.addCmdDocs
def drag(*args, **kwargs):
    res = cmds.drag(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

dynCache = _factories.getCmdFunc('dynCache')

dynControl = _factories.getCmdFunc('dynControl')

dynExport = _factories.getCmdFunc('dynExport')

dynExpression = _factories.getCmdFunc('dynExpression')

@_factories.addCmdDocs
def dynGlobals(*args, **kwargs):
    res = cmds.dynGlobals(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
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

dynPref = _factories.getCmdFunc('dynPref')

emit = _factories.getCmdFunc('emit')

@_factories.addCmdDocs
def emitter(*args, **kwargs):
    res = cmds.emitter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
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

@_factories.addCmdDocs
def expression(*args, **kwargs):
    res = cmds.expression(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

expressionEditorListen = _factories.getCmdFunc('expressionEditorListen')

fluidCacheInfo = _factories.getCmdFunc('fluidCacheInfo')

@_factories.addCmdDocs
def fluidEmitter(*args, **kwargs):
    res = cmds.fluidEmitter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

fluidVoxelInfo = _factories.getCmdFunc('fluidVoxelInfo')

getDefaultBrush = _factories.getCmdFunc('getDefaultBrush')

getFluidAttr = _factories.getCmdFunc('getFluidAttr')

getParticleAttr = _factories.getCmdFunc('getParticleAttr')

goal = _factories.getCmdFunc('goal')

@_factories.addCmdDocs
def gravity(*args, **kwargs):
    res = cmds.gravity(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

loadFluid = _factories.getCmdFunc('loadFluid')

@_factories.addCmdDocs
def nBase(*args, **kwargs):
    res = cmds.nBase(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def nParticle(*args, **kwargs):
    res = cmds.nParticle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

nSoft = _factories.getCmdFunc('nSoft')

newton = _factories.getCmdFunc('newton')

paintEffectsDisplay = _factories.getCmdFunc('paintEffectsDisplay')

@_factories.addCmdDocs
def particle(*args, **kwargs):
    res = cmds.particle(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

particleExists = _factories.getCmdFunc('particleExists')

particleFill = _factories.getCmdFunc('particleFill')

particleInstancer = _factories.getCmdFunc('particleInstancer')

particleRenderInfo = _factories.getCmdFunc('particleRenderInfo')

pfxstrokes = _factories.getCmdFunc('pfxstrokes')

radial = _factories.getCmdFunc('radial')

resampleFluid = _factories.getCmdFunc('resampleFluid')

@_factories.addCmdDocs
def rigidBody(*args, **kwargs):
    res = cmds.rigidBody(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def rigidSolver(*args, **kwargs):
    res = cmds.rigidSolver(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

runup = _factories.getCmdFunc('runup')

saveFluid = _factories.getCmdFunc('saveFluid')

saveInitialState = _factories.getCmdFunc('saveInitialState')

setDynamic = _factories.getCmdFunc('setDynamic')

setFluidAttr = _factories.getCmdFunc('setFluidAttr')

setParticleAttr = _factories.getCmdFunc('setParticleAttr')

soft = _factories.getCmdFunc('soft')

@_factories.addCmdDocs
def spring(*args, **kwargs):
    res = cmds.spring(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

@_factories.addCmdDocs
def stroke(*args, **kwargs):
    res = cmds.stroke(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    return res

truncateFluidCache = _factories.getCmdFunc('truncateFluidCache')

truncateHairCache = _factories.getCmdFunc('truncateHairCache')

@_factories.addCmdDocs
def turbulence(*args, **kwargs):
    res = cmds.turbulence(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def uniform(*args, **kwargs):
    res = cmds.uniform(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def volumeAxis(*args, **kwargs):
    res = cmds.volumeAxis(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

@_factories.addCmdDocs
def vortex(*args, **kwargs):
    res = cmds.vortex(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, _general.PyNode)
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    return res

"The primary module for maya commands and node classes"
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
import pymel as _pymel
_pymel.core = sys.modules[__name__]
import pymel.internal.startup as _startup
import pymel.internal as _internal

# will check for the presence of an initilized Maya / launch it
_startup.mayaInit()

import pymel.internal.factories as _factories
import pymel.internal.cmdcache as _cmdcache
import pymel.internal.pmcmds as _pmcmds
_pmcmds.addAllWrappedCmds()

import pymel.api.plugins as _plugins
from pymel.core.general import *
from pymel.core.context import *
from pymel.core.system import *
from pymel.core.windows import *
from pymel.core.animation import *
from pymel.core.effects import *
from pymel.core.modeling import *
from pymel.core.rendering import *
from pymel.core.language import *
from pymel.core.other import *

from pymel import api
from pymel.core import nodetypes
from pymel.core import datatypes
from pymel.core import uitypes
from pymel import versions

nt = nodetypes
dt = datatypes
ui = uitypes

from future.utils import PY2
if PY2:
    from __builtin__ import str

# This is for backwards incompatibility due to a bug in the way LazyLoadModule
# was used, which made all the uitypes available in this namespace
# We may consider deprecating or removing these at some point, so don't rely on
# these always being there!
_uitypes_names = ['AnimCurveEditor', 'AnimDisplay', 'AttrColorSliderGrp',
    'AttrControlGrp', 'AttrEnumOptionMenu', 'AttrEnumOptionMenuGrp',
    'AttrFieldGrp', 'AttrFieldSliderGrp', 'AttrNavigationControlGrp',
    'AttributeMenu', 'BlendShapeEditor', 'BlendShapePanel', 'Button', 'Canvas',
    'ChannelBox', 'CheckBox', 'CheckBoxGrp', 'ClipEditor',
    'ClipSchedulerOutliner', 'CmdScrollFieldExecuter', 'CmdScrollFieldReporter',
    'CmdShell', 'ColorEditor', 'ColorIndexSliderGrp', 'ColorSliderButtonGrp',
    'ColorSliderGrp', 'ColumnLayout', 'CommandLine', 'ConfirmDialog',
    'DefaultLightListCheckBox', 'DeviceEditor', 'DevicePanel', 'DynPaintEditor',
    'DynRelEdPanel', 'DynRelEditor', 'ExclusiveLightCheckBox', 'FloatField',
    'FloatFieldGrp', 'FloatScrollBar', 'FloatSlider', 'FloatSlider2',
    'FloatSliderButtonGrp', 'FloatSliderGrp', 'FontDialog', 'FrameLayout',
    'GlRenderEditor', 'GradientControl', 'GradientControlNoAttr', 'GridLayout',
    'HardwareRenderPanel', 'HelpLine', 'HyperGraph', 'HyperPanel', 'HyperShade',
    'IconTextButton', 'IconTextCheckBox', 'IconTextRadioButton',
    'IconTextRadioCollection', 'IconTextScrollList', 'IconTextStaticLabel',
    'Image', 'IntField', 'IntFieldGrp', 'IntScrollBar', 'IntSlider',
    'IntSliderGrp', 'KeyframeOutliner', 'KeyframeStats', 'LayerButton',
    'LayoutDialog', 'MenuBarLayout', 'MenuEditor', 'MenuSet', 'MessageLine',
    'ModelEditor', 'ModelPanel', 'NameField', 'NodeIconButton',
    'OutlinerEditor', 'OutlinerPanel', 'PalettePort', 'PaneLayout',
    'ProgressBar', 'PromptDialog', 'RadioButton', 'RadioButtonGrp',
    'RadioCollection', 'RadioMenuItemCollection', 'RenderLayerButton',
    'RenderWindowEditor', 'RowColumnLayout', 'ScriptTable', 'ScriptedPanel',
    'ScriptedPanelType', 'ScrollField', 'ScrollLayout', 'Separator',
    'ShelfButton', 'ShelfLayout', 'ShelfTabLayout', 'ShellField',
    'SymbolButton', 'SymbolCheckBox', 'TabLayout', 'Text', 'TextCurves',
    'TextField', 'TextFieldButtonGrp', 'TextFieldGrp', 'ToolButton',
    'ToolCollection', 'Visor']
if not _factories.building:
    for _uiname in _uitypes_names:
        setattr(nodetypes, _uiname, getattr(uitypes, _uiname))
    del _uiname

# create some aliases for legacy reasons
objectTypeUI = windows.objectTypeUI = ui.objectTypeUI
toQtObject = windows.toQtObject = ui.toQtObject
toQtLayout = windows.toQtLayout = ui.toQtLayout
toQtControl = windows.toQtControl = ui.toQtControl
toQtMenuItem = windows.toQtMenuItem = ui.toQtMenuItem
toQtWindow = windows.toQtWindow = ui.toQtWindow

from . import runtime

import maya.cmds as cmds

# these modules are imported anyway so they should not be a performance hit
import pymel.util as util
import pymel.api as api

_logger = _internal.getLogger(__name__)

#: dictionary of plugins and the nodes and commands they register
_pluginData = {}

_module = sys.modules[__name__]


def _addPluginCommand(pluginName, funcName):
    global _pluginData

    if funcName not in _pluginData[pluginName].setdefault('commands', []):
        _pluginData[pluginName]['commands'].append(funcName)
    _logger.debug("Adding plugin command: {} (plugin: {})".format(funcName,
                                                                  pluginName))
    #_logger.debug("adding new command:", funcName)
    _factories.cmdlist[funcName] = _cmdcache.getCmdInfoBasic(funcName)
    _factories.cmdlist[funcName]['plugin'] = pluginName
    _pmcmds.addWrappedCmd(funcName)
    # FIXME: I think we can call a much simpler factory function, because
    # plugins cannnot opt into the complex mutations that functionFactory can apply
    func = _factories.functionFactory(funcName)
    try:
        if func:
            # FIXME: figure out what to do about moduleCmds. could a plugin function be in moduleCmds???
            coreModule = 'pymel.core.%s' % _cmdcache.getModule(funcName, {})  # _factories.moduleCmds)
            if coreModule in sys.modules:
                setattr(sys.modules[coreModule], funcName, func)
            # Note that we add the function to both a core module (ie,
            # pymel.core.other), the pymel.core itself, and pymel.all; this
            # way, we mirror the behavior of 'normal' functions
            setattr(_module, funcName, func)
            if 'pymel.all' in sys.modules:
                setattr(sys.modules['pymel.all'], funcName, func)
        else:
            _logger.warning("failed to create function")
    except Exception as msg:
        from builtins import str
        _logger.warning("exception: %s" % str(msg))


def _addPluginNode(pluginName, mayaType):
    global _pluginData

    if mayaType not in _pluginData[pluginName].setdefault('dependNodes', []):
        _pluginData[pluginName]['dependNodes'].append(mayaType)
    _logger.debug("Adding plugin node: {} (plugin: {})".format(mayaType,
                                                               pluginName))
    extraAttrs = _plugins.pyNodeMethods.get(pluginName, {}).get(mayaType, {})
    return _factories.addCustomPyNode(nodetypes, mayaType, extraAttrs=extraAttrs)


def _removePluginCommand(pluginName, command):
    global _pluginData

    commands = _pluginData.get(pluginName, {}).get('commands', [])
    if command in commands:
        commands.remove(command)
    try:
        _pmcmds.removeWrappedCmd(command)
        _module.__dict__.pop(command, None)
    except KeyError:
        _logger.warning("Failed to remove %s from module %s" %
                        (command, _module.__name__))


def _removePluginNode(pluginName, node):
    global _pluginData

    nodes = _pluginData.get(pluginName, {}).get('dependNodes', [])
    if node in nodes:
        nodes.remove(node)
    _factories.removePyNode(nodetypes, node)


def _stripPluginExt(pluginName):
    if not pluginName:
        return pluginName
    def stripExt(name, ext):
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
        return name
    for ext in ('.mll', '.so', '.dylib', '.py', '.pyc'):
        pluginName = stripExt(pluginName, ext)
    return pluginName


def _pluginLoaded(*args):
    global _pluginData

    if len(args) > 1:
        # 2009 API callback, the args are ( [ pathToPlugin, pluginName ], clientData )
        pluginName = args[0][1]
    else:
        pluginName = args[0]
    pluginName = _stripPluginExt(pluginName)

    if not pluginName:
        return

    # Check to see if plugin is really loaded
    if not (cmds.pluginInfo(pluginName, query=1, loaded=1)):
        return

    # Make sure there are no registered callbacks for this plug-in. It has been
    # reported that some 3rd party plug-ins will enter here twice, causing a
    # "callback id leak" which potentially leads to a crash. The reported
    # scenario was:
    # - Launching mayapy.exe
    # - Opening a Maya scene having a requires statement (to the plug-in)
    # - The plug-in imports pymel, causing initialization and entering here.
    if (pluginName in _pluginData) and 'callbackId' in _pluginData[pluginName] \
            and _pluginData[pluginName]['callbackId'] != None:
        api.MEventMessage.removeCallback(_pluginData[pluginName]['callbackId'])

    _logger.debug("Plugin loaded: %s", pluginName)
    _pluginData[pluginName] = {}

    # Commands
    commands = _plugins.pluginCommands(pluginName)

    if commands:
        # clear out the command list first
        _pluginData[pluginName]['commands'] = []
        for funcName in commands:
            try:
                _addPluginCommand(pluginName, funcName)
            except Exception as e:
                _logger.error("Error adding command %s from plugin %s - %s" %
                              (funcName, pluginName, e))
                _logger.debug(traceback.format_exc())

    # Nodes
    try:
        mayaTypes = cmds.pluginInfo(pluginName, query=1, dependNode=1)
    except Exception:
        _logger.error("Failed to get depend nodes list from %s", pluginName)
        mayaTypes = None
    #apiEnums = cmds.pluginInfo(pluginName, query=1, dependNodeId=1)
    if mayaTypes:
        def addPluginPyNodes(*args):
            try:
                id = _pluginData[pluginName].get('callbackId')
            except KeyError:
                _logger.warning("could not find callback id!")
            else:
                if id is not None:
                    api.MEventMessage.removeCallback(id)
                    if hasattr(id, 'disown'):
                        id.disown()

            _pluginData[pluginName]['dependNodes'] = []
            allTypes = set(cmds.ls(nodeTypes=1))
            for mayaType in mayaTypes:
                # make sure it's a 'valid' type - some plugins list node types
                # that don't show up in ls(nodeTypes=1), and aren't creatable
                # ...perhaps they're abstract types?
                # Unfortunately, can't check this, as only plugin I know of
                # that has such a node - mayalive, mlConstraint - is only
                # available up to 2009, which has a bug with allNodeTypes...
                # Oddly enough, mlConstraint WILL show up in allTypes here,
                # but not after the plugin is loaded / callback finishes...?
                if mayaType not in allTypes:
                    continue
                _addPluginNode(pluginName, mayaType)

        # Note - in my testing, a single api.MFileIO.isReadingFile() call would
        # also catch opening + referencing operations... but in commit
        # 6e53d7818e9363d55d417c3a80ea7df94c4998ec, a check only against
        # isReadingFile is commented out... so I'm playing it safe, and assuming
        # there are edge cases where isOpeningFile is True but isReadingFile is
        # not

        # Detect if we are currently opening/importing a file and load as a callback versus execute now
        if (api.MFileIO.isReadingFile() or api.MFileIO.isOpeningFile() or
                api.MFileIO.isReferencingFile()):
            if api.MFileIO.isReferencingFile():
                _logger.debug("Installing temporary plugin-loaded nodes callback - PostSceneRead")
                id = api.MEventMessage.addEventCallback('PostSceneRead', addPluginPyNodes)
            elif api.MFileIO.isImportingFile():
                _logger.debug("Installing temporary plugin-loaded nodes callback - SceneImported")
                id = api.MEventMessage.addEventCallback('SceneImported', addPluginPyNodes)
            else:
                # pre-2012 referencing operations will fall into this branch,
                # which will not work (ie, pre-2012, plugins loaded due to
                # reference loads will not trigger adding of that plugin's
                # PyNodes).
                # While this is obviously less than ideal, no 2011 versions were
                # available for testing when I made the fix for 2012+, and we
                # decided that making nothing worse would be better than
                # potentially introducing problems/instabilities (ie, see
                # messages in commits 6e53d7818e9363d55d417c3a80ea7df94c4998ec
                # and 81bc5ee28f1775a680449fec8724e21e703a52b8).
                _logger.debug("Installing temporary plugin-loaded nodes callback - SceneOpened")
                id = api.MEventMessage.addEventCallback('SceneOpened', addPluginPyNodes)
            _pluginData[pluginName]['callbackId'] = id
            # scriptJob not respected in batch mode, had to use api
            #cmds.scriptJob( event=('SceneOpened',doSomethingElse), runOnce=1 )
        else:
            _logger.debug("Running plugin-loaded nodes callback")
            # add the callback id as None, so addPluginPyNodes SHOULD know that
            # SOMETHING is always in _pluginData[pluginName]['callbackId'], and
            # if there isn't, then something is wrong...
            _pluginData[pluginName]['callbackId'] = None
            addPluginPyNodes()


def _pluginUnloaded(*args):
    global _pluginData

    if len(args) > 1:
        # 2009 API callback, the args are
        # ( [ pluginName, pathToPlugin ], clientData )  OR
        # ( [ pathToPlugin ], clientData )
        pluginName = args[0][0]
    else:
        pluginName = args[0]
    pluginName = _stripPluginExt(pluginName)

    _logger.debug("Plugin unloaded: %s" % pluginName)

    try:
        data = _pluginData.pop(pluginName)
    except KeyError:
        pass
    else:
        # Commands
        commands = data.pop('commands', [])
        if commands:
            _logger.debug("Removing plugin commands: {}".format(
                ', '.join(commands)))
            for command in commands:
                _removePluginCommand(pluginName, command)

        # Nodes
        nodes = data.pop('dependNodes', [])
        if nodes:
            _logger.debug("Removing plugin nodes: {}".format(', '.join(nodes)))
            for node in nodes:
                _removePluginNode(pluginName, node)


global _pluginLoadedCB
global _pluginUnloadedCB
_pluginLoadedCB = None
_pluginUnloadedCB = None


def _installCallbacks():
    """install the callbacks that trigger new nodes and commands to be added to pymel when a
    plugin loads.  This is called from pymel.__init__
    """

    global _pluginLoadedCB
    if _pluginLoadedCB is None:
        _pluginLoadedCB = True
        _logger.debug("Adding pluginLoaded callback")
        #_pluginLoadedCB = pluginLoadedCallback(module)

        id = api.MSceneMessage.addStringArrayCallback(api.MSceneMessage.kAfterPluginLoad, _pluginLoaded)
        if hasattr(id, 'disown'):
            id.disown()
    else:
        _logger.debug("PluginLoaded callback already exists")

    global _pluginUnloadedCB
    if _pluginUnloadedCB is None:
        _pluginUnloadedCB = True

        # BUG: autodesk still has not add python callback support, and calling this as MEL is not getting the plugin name passed to it
        # mel.unloadPlugin( addCallback='''python("import pymel; pymel._pluginUnloaded('#1')")''' )

        _logger.debug("Adding pluginUnloaded callback")
        id = api.MSceneMessage.addStringArrayCallback(api.MSceneMessage.kAfterPluginUnload, _pluginUnloaded)
        if hasattr(id, 'disown'):
            id.disown()

    else:
        _logger.debug("PluginUnloaded callback already exists")

    # add commands and nodes for plugins loaded prior to importing pymel
    preLoadedPlugins = cmds.pluginInfo(q=1, listPlugins=1)
    if preLoadedPlugins:
        _logger.info("Updating pymel with pre-loaded plugins: %s" % ', '.join(preLoadedPlugins))
        for plugin in preLoadedPlugins:
            _pluginLoaded(plugin)


if not _factories.building:
    _installCallbacks()

# run userSetup.py / initialize MEL...
# ...userStartup.py / .mel may try to add plugins and then use their commands /
# nodes with pymel... so do the plugin stuff first
_startup.finalize()

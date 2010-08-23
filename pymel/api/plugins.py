"""
from pymel.api.plugins import Command
class testCmd(Command):
    def doIt(self, args):
        print "doIt..."

testCmd.register()
cmds.testCmd()
testCmd.deregister()
"""


import sys
import inspect
import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx
import maya.cmds
from collections import defaultdict


global registered
registered = {}

def _pluginModule():
    return inspect.getmodule( lambda: None )

def _pluginName():
    return _pluginModule().__name__.split('.')[-1]

def _pluginFile():
    return inspect.getsourcefile( lambda:None )
#    module = sys.modules[__name__]
#    print module, __name__
#    return module.__file__

def _loadPlugin():
    thisFile = _pluginFile()
    if not maya.cmds.pluginInfo( thisFile, query=1, loaded=1 ):
        maya.cmds.loadPlugin( thisFile )

def _unloadPlugin():
    thisFile = _pluginFile()
    if maya.cmds.pluginInfo( thisFile, query=1, loaded=1 ):
        maya.cmds.unloadPlugin( thisFile )


def _getPlugin(object=None):
    if object is None:
        _loadPlugin()
        mobject = mpx.MFnPlugin.findPlugin( _pluginName() )
        plugin = mpx.MFnPlugin(mobject)
    elif isinstance(object, om.MObject):
        plugin = mpx.MFnPlugin(object)
    elif isinstance(object, mpx.MFnPlugin):
        plugin = object
    else:
        raise TypeError('expected an MFnPlugin instance or an MObject that can be cast to an MFnPlugin')
    return plugin

class Command(mpx.MPxCommand):
    _name = None
    def __init__(self):
        mpx.MPxCommand.__init__(self)

    @classmethod
    def create(cls):
        return mpx.asMPxPtr( cls() )

    @classmethod
    def createSyntax(cls):
        return om.MSyntax()

    @classmethod
    def register(cls, plugin=None):
        """
        By default the command will be registered to a dummy plugin provided by pymel.

        If using from within a plugin module's ``initializePlugin`` or ``uninitializePlugin`` callback, pass along the
        MObject given to these functions.
        """
        global registered
        name = cls._name if cls._name else cls.__name__
        mplugin = _getPlugin(plugin)
        mplugin.registerCommand( name, cls.create, cls.createSyntax )
        if plugin is None:
            registered[cls] = None

    @classmethod
    def deregister(cls, plugin=None):
        """
        If using from within a plugin module's ``initializePlugin`` or ``uninitializePlugin`` callback, pass along the
        MObject given to these functions.
        """
        global registered
        name = cls._name if cls._name else cls.__name__
        mplugin = _getPlugin(plugin)
        mplugin.deregisterCommand( name )
        if plugin is None:
            registered.pop(cls)

class LocatorNode(mpx.MPxLocatorNode):
    _typeName = None
    _typeId = None
    _type = mpx.MPxNode.kLocatorNode
    _callbacks = defaultdict(list)
    def __init__(self):
        mpx.MPxLocatorNode.__init__(self)

    @classmethod
    def name(cls):
        if cls._name:
            return cls._name
        else:
            return cls.__name__

    @classmethod
    def create(cls):
        return mpx.asMPxPtr( cls() )

    @classmethod
    def initialize(cls):
        return

    @classmethod
    def register(cls, plugin=None):
        """
        By default the command will be registered to a dummy plugin provided by pymel.

        If using from within a plugin module's ``initializePlugin`` or ``uninitializePlugin`` callback, pass along the
        MObject given to these functions.
        """
        global registered
        name = cls._typeName if cls._typeName else cls.__name__
        mplugin = _getPlugin(plugin)
        mplugin.registerNode( name, cls._typeId, cls.create, cls.initialize, cls._type )
        if plugin is None:
            registered[cls] = None
            import pymel.core.nodetypes as nodetypes
            import pymel.internal.factories as factories
            factories.addCustomPyNode(nodetypes, name)
        # callbacks
        for cbname, reg in [
                    ('timeChanged', om.MDGMessage.addTimeChangeCallback),
                    ('forcedUpdate', om.MDGMessage.addForceUpdateCallback),
                    ('nodeAdded', om.MDGMessage.addNodeAddedCallback),
                    ('nodeRemoved', om.MDGMessage.addNodeRemovedCallback),
                    #('connectionMade', om.MDGMessage.addConnectionCallback), # conflicts with MPxNode.connectionMade
                    ('preConnectionMade', om.MDGMessage.addPreConnectionCallback)]:
            if hasattr(cls, cbname):
                cb = getattr(cls, cbname)
                # TODO: assert cb is a classmethod, maybe check number of inputs too
                cls._callbacks[name].append(reg(cb, cls._typeName))

    @classmethod
    def deregister(cls, plugin=None):
        """
        If using from within a plugin module's ``initializePlugin`` or ``uninitializePlugin`` callback, pass along the
        MObject given to these functions.
        """
        global registered
        _getPlugin(plugin).deregisterNode( cls._typeId )
        name = cls._typeName if cls._typeName else cls.__name__
        if plugin is None:
            registered.pop(cls)
            import pymel.core.nodetypes as nodetypes
            import pymel.internal.factories as factories
            factories.removePyNode(nodetypes, name)
        for id in cls._callbacks.pop(name):
            om.MMessage.removeCallback(id)

# allow this file to be loaded as its own dummy plugin
# Initialize the script plug-in
def initializePlugin(mobject):
    pass


# Uninitialize the script plug-in
def uninitializePlugin(mobject):

    #print "getmodule", inspect.getmodule( None )
    #mod = _pluginModule()

    #when uninitializePlugin is called it is execfile'd which changes the module in which this code runs.
    #we need to get the correct module first

    # FIXME: determine a reliable way to get this module's name when it is being execfile'd
    global registered
    mod = sys.modules['pymel.api.plugins']

    plugin = mpx.MFnPlugin(mobject)
    for obj in registered:
        print "deregistering", obj.name()
        obj.deregisterCommand(plugin)
    registered = {}

#def _repoplulate():
#    print "repopulate"
#    try:
#        global registered
#        commands = maya.cmds.pluginInfo(_pluginName(), query=1, command=1)
#        registered = registered
#    except:
#        pass
#
#_repoplulate()


# when we reload, should we deregister all plugins??? or maybe we can just repopulate registered
#_unloadPlugin()

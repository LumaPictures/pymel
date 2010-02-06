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

import maya.OpenMayaMPx as mpx
import maya.cmds



global registeredCommands
registeredCommands = []

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


def _getPlugin():
    _loadPlugin()
    mobject = mpx.MFnPlugin.findPlugin( _pluginName() )
    return mpx.MFnPlugin(mobject)

class Command(mpx.MPxCommand):
    registeredCommands = []
    def __init__(self):
        mpx.MPxCommand.__init__(self)

    @classmethod
    def creator(cls):
        return mpx.asMPxPtr( cls() )

    @classmethod
    def register(cls, object=None):
        """
        by default the command will be registered to a dummy plugin provided by pymel.

        If you
        if using from within a plugin's initializePlugin or uninitializePlugin callback, pass along the
        MObject given to these functions
        """
        if object is None:
            plugin = _getPlugin()
            cls.registeredCommands.append( cls.__name__ )
        else:
            plugin = mpx.MFnPlugin(object)
        if hasattr(cls, 'createSyntax'):
            plugin.registerCommand( cls.__name__, cls.creator, cls.createSyntax )
        else:
            plugin.registerCommand( cls.__name__, cls.creator )

    @classmethod
    def deregister(cls, object=None):
        """
        if using from within a plugin's initializePlugin or uninitializePlugin callback, pass along the
        MObject given to these functions
        """
        if object is None:
            plugin = _getPlugin()
            cls.registeredCommands.pop(cls.__name__)
        else:
            plugin = mpx.MFnPlugin(object)
        plugin.deregisterCommand( cls.__name__ )

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
    mod = sys.modules['pymel.api.plugins']

    plugin = mpx.MFnPlugin(mobject)
    for cmd in mod.Command.registeredCommands:
        print "deregistering", cmd
        plugin.deregisterCommand(cmd)
    registeredCommands = []

#def _repoplulate():
#    print "repopulate"
#    try:
#        global registeredCommands
#        commands = maya.cmds.pluginInfo(_pluginName(), query=1, command=1)
#        registeredCommands = registeredCommands
#    except:
#        pass
#
#_repoplulate()


# when we reload, should we deregister all plugins??? or maybe we can just repopulate registeredCommands
#_unloadPlugin()

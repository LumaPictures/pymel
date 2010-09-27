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
import hashlib
from collections import defaultdict

import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx
import maya.cmds

registered = {}

pyNodeMethods = {}

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

class BasePluginMixin(object):
    # The name of the command or the node type
    _name = None
    _mpxType = None
    
    @classmethod
    def create(cls):
        return mpx.asMPxPtr( cls() )    

    @classmethod
    def mayaName(cls):
        return cls._name if cls._name else cls.__name__
    
    @classmethod
    def register(cls, plugin=None):
        """Used to register this MPx object wrapper with the maya plugin.
        
        By default the command will be registered to a dummy plugin provided by pymel.

        If using from within a plugin module's ``initializePlugin`` or
        ``uninitializePlugin`` callback, pass along the MObject given to these
        functions.
        
        When implementing the derived MPx wrappers, do not override this -
        instead, override _registerOverride
        """
        global registered
        useThisPlugin = (plugin is None)
        mplugin = _getPlugin(plugin)
        cls._registerOverride(mplugin, useThisPlugin)
        if useThisPlugin:
            registered[cls] = None
            
    @classmethod
    def _registerOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual registration behavior for
        the MPx class. 
        '''
        return
    
    @classmethod
    def deregister(cls, plugin=None):
        """
        If using from within a plugin module's ``initializePlugin`` or
        ``uninitializePlugin`` callback, pass along the MObject given to these
        functions.
        """
        global registered
        useThisPlugin = (plugin is None)
        mplugin = _getPlugin(plugin)
        cls._deregisterOverride(mplugin, useThisPlugin)
        if plugin is None:
            registered.pop(cls)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class. 
        '''
        return

class BaseCommandMixin(BasePluginMixin):
    @classmethod
    def createSyntax(cls):
        return om.MSyntax()

    @classmethod
    def _registerOverride(cls, mplugin, useThisPlugin):
        name = cls.mayaName()
        mplugin.registerCommand( name, cls.create, cls.createSyntax )
        if useThisPlugin:
            import pymel.core
            pymel.core._addPluginCommand(mplugin.name(), name)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class. 
        '''
        name = cls.mayaName()
        mplugin.deregisterCommand( name )
        if useThisPlugin:
            import pymel.core
            pymel.core._removePluginCommand(mplugin.name(), name)
            
class Command(BaseCommandMixin, mpx.MPxCommand):
    _mpxType = mpx.MPxCommand


# Todo: implement the underlying stuff to make PyNodeMethod work... probably
# need to unify the code in pymel.core._pluginLoaded/_pluginUnloaded and
# factories.addCustomPyNode; then, just have anytime we're adding new plugin
# nodes, check for PyNodeMethod objects on the class, and modify the resulting
# PyNode accordingly

# The support for this isn't implemented yet... just here to give an idea of
# how it would work...
class PyNodeMethod(object):
    '''Used as a decorator, placed on methods on a plugin node class, to signal
    that these methods should be placed on to PyNode objects constructed for
    the resulting depend nodes.
    
    >>> class FriendlyNode(DependNode):
    ...     _typeId = om.MTypeId(654748)
    ...     @PyNodeMethod
    ...     def introduce(self):
    ...         print "Hi, I'm an instance of a MyNode PyNode - my name is %s!" % self.name()
    >>> FriendlyNode.register()
    >>> import pymel.core as pm
    >>> frank = pm.createNode('FriendlyNode', name='Frank')
    >>> frank.introduce()
    Hi, I'm an instance of a MyNode PyNode - my name is Frank!
    '''
    def __init__(self, func, name=None):
        if name is None:
            name = func.__name__
        self.func = func
        self.name = name

class BaseNodeMixin(BasePluginMixin):
    _typeId = None
    _callbacks = defaultdict(list)
    
    @classmethod
    def initialize(cls):
        return

    @classmethod
    def _registerOverride(cls, mplugin, useThisPlugin):
        nodeName = cls.mayaName()

        # PyNodeMethods
        global pyNodeMethods
        pluginPynodeMethods = pyNodeMethods.setdefault(mplugin.name(), {})
        pluginPynodeMethods[nodeName] = {}
        for clsAttrName, clsObj in inspect.getmembers(cls):
            if isinstance(clsObj, PyNodeMethod):
                pluginPynodeMethods[nodeName][clsObj.name] = clsObj.func
                        
        
        mplugin.registerNode( nodeName, cls._typeId, cls.create, cls.initialize, cls._type )
        
        if useThisPlugin:
            import pymel.core
            pymel.core._addPluginNode(mplugin.name(), nodeName)
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
                cls._callbacks[nodeName].append(reg(cb, nodeName))
                
        
                
    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class. 
        '''
        nodeName = cls.mayaName()

        # PyNodeMethods
        global pyNodeMethods
        pyNodeMethods.get(mplugin.name(), {}).pop(nodeName, None)
        
        mplugin.deregisterNode( cls._typeId )
        if useThisPlugin:
            import pymel.core
            pymel.core._removePluginNode(mplugin.name(), nodeName)
        for id in cls._callbacks.pop(nodeName):
            om.MMessage.removeCallback(id)
            
    @classmethod
    def _devTypeIdHash(cls, name):
        '''hashes the given string to a MTypeId, somewhere in the dev range
        (0x80000 - 0xfffff)
        '''
        start = 0x80000
        end = 0xfffff
        size = (end - start) + 1
        md5 = hashlib.md5()
        md5.update(name)
        id = start + long(md5.hexdigest(), 16) % size
        return om.MTypeId(id)
            
class DependNode(BaseNodeMixin, mpx.MPxNode):
    _mpxType = mpx.MPxNode
    _type = mpx.MPxNode.kDependNode
                
class LocatorNode(BaseNodeMixin, mpx.MPxLocatorNode):
    _mpxType = mpx.MPxLocatorNode
    _type = mpx.MPxNode.kLocatorNode


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

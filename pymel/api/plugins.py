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

#===============================================================================
# General Info
#===============================================================================

mpxToEnum = {
    mpx.MPxNode:mpx.MPxNode.kDependNode,
    mpx.MPxPolyTrg:mpx.MPxNode.kDependNode,             # has no unique enum
    mpx.MPxLocatorNode:mpx.MPxNode.kLocatorNode,
    mpx.MPxDeformerNode:mpx.MPxNode.kDeformerNode,
    mpx.MPxManipContainer:mpx.MPxNode.kManipContainer,
    mpx.MPxSurfaceShape:mpx.MPxNode.kSurfaceShape,
    mpx.MPxComponentShape:mpx.MPxNode.kSurfaceShape,    # has no unique enum
    mpx.MPxFieldNode:mpx.MPxNode.kFieldNode,
    mpx.MPxEmitterNode:mpx.MPxNode.kEmitterNode,
    mpx.MPxSpringNode:mpx.MPxNode.kSpringNode,
    mpx.MPxIkSolverNode:mpx.MPxNode.kIkSolverNode,
    mpx.MPxHardwareShader:mpx.MPxNode.kHardwareShader,
    mpx.MPxHwShaderNode:mpx.MPxNode.kHwShaderNode,
    mpx.MPxTransform:mpx.MPxNode.kTransformNode,
    mpx.MPxObjectSet:mpx.MPxNode.kObjectSet,
    mpx.MPxFluidEmitterNode:mpx.MPxNode.kFluidEmitterNode,
    mpx.MPxImagePlane:mpx.MPxNode.kImagePlaneNode,
    mpx.MPxParticleAttributeMapperNode:mpx.MPxNode.kParticleAttributeMapperNode,
    mpx.MPxCameraSet:mpx.MPxNode.kCameraSetNode,
    mpx.MPxConstraint:mpx.MPxNode.kConstraintNode,
    mpx.MPxManipulatorNode:mpx.MPxNode.kManipulatorNode,
    }

_enumToStr = None
def enumToStr():
    '''Returns a dictionary mapping from an MPxNode node type enum to it's
    string name.
    Useful for debugging purposes.
    '''
    global _enumToStr
    if _enumToStr is None:
        _enumToStr = {}
        for name, val in inspect.getmembers(mpx.MPxNode, lambda x: isinstance(x, int)):
            if name.startswith('k'):
                _enumToStr[val] = name
    return _enumToStr
    
_allMPx = None
def allMPx():
    '''
    Returns a list of all MPx classes
    '''
    global _allMPx
    if _allMPx is None:
        _allMPx = []
        for _, cls in inspect.getmembers(mpx, lambda x: inspect.isclass(x) and issubclass(x, mpx.MPxNode)):
            _allMPx.append(cls)
    return _allMPx

# We want to make sure we know if maya adds a new MPx class!
for _mpx in allMPx():
    assert _mpx in mpxToEnum, 'new MPx class found: %s' % _mpx.__name__

#===============================================================================
# Plugin Registration / loading
#===============================================================================

registered = set()

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
    registered = set()

#===============================================================================
# Plugin Mixin Classes
#===============================================================================

class BasePluginMixin(object):
    # The name of the command or the node type
    _name = None
    
    # You can manually set this, or just leave it at None to let pymel
    # automatically determine it from the base classes
    _mpxType = None
    
    @classmethod
    def getMpxType(cls):
        if cls._mpxType is None:
            for pClass in inspect.getmro(cls):
                if pClass in mpxToEnum:
                    cls._mpxType = pClass
                    break
        return cls._mpxType
    
    @classmethod
    def mayaName(cls):
        if cls._name is None:
            cls._name = cls.__name__
        return cls._name

    _typeId = None
    
    # Defined here just so it can be shared between MPxTransformationMatrix
    # and DependNode
    @classmethod
    def getTypeId(cls, nodeName=None):
        if cls._typeId is None:
            if nodeName is None:
                nodeName = cls.mayaName()
            cls._typeId = cls._devTypeIdHash(nodeName)
        return cls._typeId

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
    
    @classmethod
    def create(cls):
        return mpx.asMPxPtr( cls() )    

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
            registered.add(cls)
            
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
            registered.remove(cls)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class. 
        '''
        return

#===============================================================================
# Plugin Classes - inherit from these!
#===============================================================================

            
class Command(BasePluginMixin, mpx.MPxCommand):
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
            
class TransformationMatrix(BasePluginMixin, mpx.MPxTransformationMatrix):
    _typeId = None
    # Override to do nothing - should be (de)registered by the transform!
    @classmethod
    def register(cls, plugin=None): pass
    @classmethod
    def deregister(cls, plugin=None): pass
                
class DependNode(BasePluginMixin, mpx.MPxNode):
    # You can manually set this, or just leave it at None to let pymel
    # automatically determine it from the MPxType
    _typeEnum = None

    # If this is left as None, a 'reasonable' default will be made based on a
    # hash of the node name in the user range... to ensure no name clashes,
    # though, you should get a node id from Autodesk!
    _typeId = None
    
    @classmethod
    def getTypeEnum(cls):
        if cls._typeEnum is None:
            cls._typeEnum = mpxToEnum[cls.getMpxType()]
        return cls._typeEnum
    
    _classification = None
    
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
            
        cls._nodeRegisterOverride( nodeName, mplugin )
        
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
    def _nodeRegisterOverride( cls, nodeName, mplugin ):
        registerArgs = [ nodeName, cls.getTypeId(), cls.create, cls.initialize,
                         cls.getTypeEnum() ]
        if cls._classification:
            registerArgs.append(cls._classification)
        mplugin.registerNode( *registerArgs )
        
                
    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class. 
        '''
        nodeName = cls.mayaName()

        # PyNodeMethods
        global pyNodeMethods
        pyNodeMethods.get(mplugin.name(), {}).pop(nodeName, None)
        
        mplugin.deregisterNode( cls.getTypeId() )
        if useThisPlugin:
            import pymel.core
            pymel.core._removePluginNode(mplugin.name(), nodeName)
        for id in cls._callbacks.pop(nodeName, []):
            om.MMessage.removeCallback(id)

    @classmethod
    def isAbstractClass(cls):
        # MPxPolyTrg returns True
        return False
            
# I have some unnecessary if statements, just to visually show the hierarchy
                
class CameraSet(DependNode, mpx.MPxCameraSet): pass
        
class Constraint(DependNode, mpx.MPxConstraint): pass

class DeformerNode(DependNode, mpx.MPxDeformerNode): pass

class EmitterNode(DependNode, mpx.MPxEmitterNode): pass

if 1:
    class FluidEmitterNode(EmitterNode, mpx.MPxFluidEmitterNode): pass

class FieldNode(DependNode, mpx.MPxFieldNode): pass
    
class HardwareShader(DependNode, mpx.MPxHardwareShader): pass

class HwShaderNode(DependNode, mpx.MPxHwShaderNode): pass

class IkSolverNode(DependNode, mpx.MPxIkSolverNode): pass

class ImagePlane(DependNode, mpx.MPxImagePlane): pass

class LocatorNode(DependNode, mpx.MPxLocatorNode): pass

class ManipContainer(DependNode, mpx.MPxManipContainer): pass

class ManipulatorNode(DependNode, mpx.MPxManipulatorNode): pass

class ObjectSet(DependNode, mpx.MPxObjectSet): pass

class ParticleAttributeMapperNode(DependNode, mpx.MPxParticleAttributeMapperNode): pass

class PolyTrg(DependNode, mpx.MPxPolyTrg): pass

class SpringNode(DependNode, mpx.MPxSpringNode): pass

class SurfaceShape(DependNode, mpx.MPxSurfaceShape): pass

if 1:
    class ComponentShape(SurfaceShape, mpx.MPxComponentShape): pass
    
class Transform(DependNode, mpx.MPxTransform):
    # Bug in python - can't just use MPxTransformationMatrix, as there's a
    # problem with MPxTransformationMatrix.baseTransformationMatrixId
    _transformMatrix = TransformationMatrix
    
    @classmethod                
    def _nodeRegisterOverride( cls, nodeName, mplugin ):
        registerArgs = [ nodeName, cls.getTypeId(), cls.create, cls.initialize,
                         cls._transformMatrix.create,
                         cls._transformMatrix.getTypeId() ]
        if cls._classification:
            registerArgs.append(cls._classification)
        mplugin.registerTransform( *registerArgs )

#===============================================================================
# Plugin Class Helpers
#===============================================================================

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


#===============================================================================
# Querying Plugin Hierarchy
#===============================================================================

def getPluginHierarchy():
    '''Dynamically query the mel node hierarchy for all plugin node types
    
    This command must be run from within a running maya session - ie, where
    maya.cmds, etc are accessible.
    '''
    import pymel.internal.factories as factories
    
    dummyClasses = createDummyNodePlugins()
    inheritances = {}
    for pluginType, dummyClass in dummyClasses.iteritems():
        nodeType = dummyClass.mayaName()
        dummyClass.register()
        try:
            try:
                inheritance = factories.getInheritance(nodeType)
            except factories.ManipNodeTypeError:
                continue
        finally:
            dummyClass.deregister()
        assert inheritance[-1] == nodeType
        inheritances[pluginType] = inheritance[1:]
    return inheritances

def createDummyNodePlugins():
    '''Registers with the dummy pymel plugin a dummy node type for each MPxNode
    subclass
    
    returns a dictionary mapping from MPx class to a maya node type string
    '''
    pymelPlugClasses = []
    
    for obj in globals().itervalues():
        if inspect.isclass(obj) and issubclass(obj, DependNode):
            pymelPlugClasses.append(obj)
            
    dummyClasses = {}
    for cls in pymelPlugClasses:
        class DummyClass(cls):
            _name = 'dummy' + cls.__name__
        DummyClass.__name__ = 'Dummy' + cls.__name__
        dummyClasses[DummyClass.getMpxType()] = DummyClass
        
    return dummyClasses
    


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

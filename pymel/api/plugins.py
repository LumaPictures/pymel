"""
Maya API plugin utilities

A quick example::

    from pymel.api.plugins import Command
    class testCmd(Command):
        @classmethod
        def createSyntax(cls):
            syntax = om.MSyntax()
            # the node type name
            syntax.addArg(om.MSyntax.kString)
            return syntax

        def doIt(self, args):
            argParser =  om.MArgParser(self.syntax(), args)
            arg = argParser.commandArgumentString(0)
            print "doing it: {}".format(arg)

    testCmd.register()
    cmds.testCmd()
    testCmd.deregister()

An example of a plugin which creates a node::

    import math

    import pymel.api.plugins as plugins
    import maya.OpenMaya as om

    class PymelSineNode(plugins.DependNode):
        '''Example node adapted from maya's example sine node plugin

        Shows how much easier it is to create a plugin node using pymel.api.plugins
        '''
        # For quick testing, if _typeId is not defined, pymel will create one by
        # hashing the node name. For longer-term uses, you should explicitly set
        # own typeId like this
        #
        # (NOTE - if using the automatic typeId generation, the hashlib python
        # builtin library must be functional / working from within maya... due
        # to dynamic library linking issues (ie, libssl, libcrypto), this
        # may not always be the case out-of-the-box on some linux distros
        _typeId = om.MTypeId(0x900FF)

        # by default, the name of the node will be the name of the class - to
        # override and set your own maya node name, do this:
        #_name = 'PymelSineNode'

        @classmethod
        def initialize(cls):
            # input
            nAttr = om.MFnNumericAttribute()
            cls.input = nAttr.create( "input", "in", om.MFnNumericData.kFloat, 0.0 )
            nAttr.setStorable(1)
            cls.addAttribute( cls.input )

            # output
            cls.output = nAttr.create( "output", "out", om.MFnNumericData.kFloat, 0.0 )
            nAttr.setStorable(1)
            nAttr.setWritable(1)
            cls.addAttribute( cls.output )

            # set attributeAffects relationships
            cls.attributeAffects( cls.input, cls.output )

        def compute(self, plug, dataBlock):
            if ( plug == self.output ):
                dataHandle = dataBlock.inputValue( self.input )
                inputFloat = dataHandle.asFloat()
                result = math.sin( inputFloat )
                outputHandle = dataBlock.outputValue( self.output )
                outputHandle.setFloat( result )
                dataBlock.setClean( plug )
                return om.MStatus.kSuccess
            return om.MStatus.kUnknownParameter

    ## initialize the script plug-in
    def initializePlugin(mobject):
        PymelSineNode.register(mobject)

    # uninitialize the script plug-in
    def uninitializePlugin(mobject):
        PymelSineNode.deregister(mobject)
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future.utils import PY2

from pymel.util.py2to3 import RePattern

from builtins import object
import re
import sys
import os
import inspect
import collections

import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx
import maya.cmds

#===============================================================================
# Errors
#===============================================================================


class PluginError(Exception):
    pass


class PluginRegistryError(PluginError):
    pass


class AlreadyRegisteredError(PluginRegistryError):
    pass


class NotRegisteredError(PluginRegistryError):
    pass

#===============================================================================
# General Info
#===============================================================================

# Gives a map from an MPx class name to it's enum name in MPxNode.Type
# Because different versions of maya may not have all these MPxNodes, we need
# to store as strings, and retrieve from mpx
# Constructed by manual inspection of names in MPxNode.Type
mpxNamesToEnumNames = {
    'MPxNode': 'kDependNode',
    'MPxPolyTrg': 'kDependNode',             # has no unique enum
    'MPxLocatorNode': 'kLocatorNode',
    'MPxDeformerNode': 'kDeformerNode',
    'MPxManipContainer': 'kManipContainer',
    'MPxSurfaceShape': 'kSurfaceShape',
    'MPxComponentShape': 'kSurfaceShape',    # has no unique enum
    'MPxFieldNode': 'kFieldNode',
    'MPxEmitterNode': 'kEmitterNode',
    'MPxSpringNode': 'kSpringNode',
    'MPxIkSolverNode': 'kIkSolverNode',
    'MPxHardwareShader': 'kHardwareShader',
    'MPxHwShaderNode': 'kHwShaderNode',
    'MPxTransform': 'kTransformNode',
    # this is a temp entity - same as MPxTransform, but with fixed / added API
    # for bounding boxes; since not 100% binary / ABI compatible, added as
    # a new class in 2019.2.  Will replace the "standard" MPxTransform in 2020
    'MPxTransform_BoundingBox': 'kTransformNode',
    'MPxObjectSet': 'kObjectSet',
    'MPxFluidEmitterNode': 'kFluidEmitterNode',
    'MPxImagePlane': 'kImagePlaneNode',
    'MPxParticleAttributeMapperNode': 'kParticleAttributeMapperNode',
    'MPxCameraSet': 'kCameraSetNode',
    'MPxConstraint': 'kConstraintNode',
    'MPxManipulatorNode': 'kManipulatorNode',
    #    'MPxRepMgr':'kRepMgr',
    #    'MPxRepresentation':'kRepresentation',
    'MPxAssembly': 'kAssembly',
    'MPxBlendShape': 'kBlendShape',  # auto
    'MPxGeometryFilter': 'kGeometryFilter',  # auto
    'MPxMotionPathNode': 'kMotionPathNode',  # auto
    'MPxSkinCluster': 'kSkinCluster',  # auto
}

# Gives a map from an MPx class name to it's enum name in MFn.Type
# Constructed by a combination of _buildMpxNamesToApiEnumNames and manual
# inspection of names in MFn.Type
mpxNamesToApiEnumNames = {
    'MPxNode': 'kPluginDependNode',
    'MPxPolyTrg': 'kPluginDependNode',   # has no unique enum
    'MPxLocatorNode': 'kPluginLocatorNode',
    'MPxDeformerNode': 'kPluginDeformerNode',
    'MPxManipContainer': 'kPluginManipContainer',  # added manually
    'MPxSurfaceShape': 'kPluginShape',
    'MPxComponentShape': 'kPluginShape',  # has no unique enum
    'MPxFieldNode': 'kPluginFieldNode',
    'MPxEmitterNode': 'kPluginEmitterNode',
    'MPxSpringNode': 'kPluginSpringNode',
    'MPxIkSolverNode': 'kPluginIkSolver',
    'MPxHardwareShader': 'kPluginHardwareShader',
    'MPxHwShaderNode': 'kPluginHwShaderNode',
    'MPxTransform': 'kPluginTransformNode',
    'MPxTransform_BoundingBox': 'kPluginTransformNode',
    'MPxObjectSet': 'kPluginObjectSet',
    'MPxFluidEmitterNode': 'kPluginEmitterNode',
    'MPxImagePlane': 'kPluginImagePlaneNode',
    'MPxParticleAttributeMapperNode': 'kPluginParticleAttributeMapperNode',  # added manually
    'MPxCameraSet': 'kPluginCameraSet',
    'MPxConstraint': 'kPluginConstraintNode',
    'MPxManipulatorNode': 'kPluginManipulatorNode',  # added manually
    'MPxRepMgr': 'kPluginRepMgr',  # guessed?
    'MPxRepresentation': 'kPluginRepresentation',  # guessed?
    'MPxAssembly': 'kAssembly',
    'MPxBlendShape': 'kPluginBlendShape',  # auto
    'MPxGeometryFilter': 'kPluginGeometryFilter',  # auto
    'MPxMotionPathNode': 'kPluginMotionPathNode',  # auto
    'MPxSkinCluster': 'kPluginSkinCluster',  # auto
}

# Gives a map from an MPx class name to it's maya node type name
# Constructed from a combination of _buildMpxNamesToMayaNodes and manual
# guess + check with nodeType(isTypeName=True)
mpxNamesToMayaNodes = {
    'MPxNode': u'THdependNode',
    'MPxPolyTrg': u'THdependNode',
    'MPxLocatorNode': u'THlocatorShape',
    'MPxDeformerNode': u'THdeformer',
    'MPxManipContainer': u'THmanipContainer',  # guessed + confirmed
    'MPxSurfaceShape': u'THsurfaceShape',
    'MPxComponentShape': u'THsurfaceShape',
    'MPxFieldNode': u'THdynField',
    'MPxEmitterNode': u'THdynEmitter',
    'MPxSpringNode': u'THdynSpring',
    'MPxIkSolverNode': u'THikSolverNode',
    'MPxHardwareShader': u'THhardwareShader',
    'MPxHwShaderNode': u'THhwShader',
    'MPxTransform': u'THcustomTransform',
    'MPxTransform_BoundingBox': u'THcustomTransform',
    'MPxObjectSet': u'THobjectSet',
    'MPxFluidEmitterNode': u'THfluidEmitter',
    'MPxImagePlane': u'THimagePlane',
    'MPxParticleAttributeMapperNode': u'THarrayMapper',
    'MPxCameraSet': u'THcameraSet',
    'MPxConstraint': u'THconstraint',
    'MPxManipulatorNode': 'THmanip',  # guessed + confirmed
    'MPxRepMgr': 'THdependNode',  # no clue...?
    'MPxRepresentation': 'THdependNode',  # no clue...?
    'MPxAssembly': 'THassembly',
    'MPxBlendShape': u'THblendShape',  # auto
    'MPxGeometryFilter': u'THgeometryFilter',  # auto
    'MPxMotionPathNode': u'THmotionPath',  # auto
    'MPxSkinCluster': u'THskinCluster',  # auto
}

# make reverse mapping...

# it's possible that multiple mpxNames map to the same maya name  -
# ie, we know multiple types map to 'THdependNode' ('MPxNode',
# 'MPxRepresentation', 'MPxRepMgr', 'MPxPolyTrg'), and
# 'THsurfaceShape' ('MPxSurfaceShape', 'MPxComponentShape').
# Harcode these, and error if any other maya type has multiple
# mpx names

_knownRepeatedMayaNames = {
    'THdependNode': 'MPxNode',
    'THsurfaceShape': 'MPxSurfaceShape',
    'THcustomTransform': 'MPxTransform',
}

mayaNodesToMpxNames = dict(_knownRepeatedMayaNames)

for mpxName, mayaName in mpxNamesToMayaNodes.items():
    if mayaName in _knownRepeatedMayaNames:
        continue
    existingMpxName = mayaNodesToMpxNames.get(mayaName)
    if existingMpxName is not None:
        msg = "Encountered unexpected mapping of multiple MPx nodes ({}, {})" \
              " to the same maya node ({})".format(mpxName, existingMpxName,
                                                   mayaName)
        raise RuntimeError(msg)
    mayaNodesToMpxNames[mayaName] = mpxName


# remove entries from mpxNamesToEnumNames which are not in OpenMayaMPx, and add
# those that are to mpxClassesToMpxEnums
mpxClassesToMpxEnums = {}
missingMPx = []
for _mpxName, _enumName in mpxNamesToEnumNames.items():
    _mpxCls = getattr(mpx, _mpxName, None)

    if _mpxCls:
        _enum = getattr(mpx.MPxNode, _enumName, None)
        if _enum is not None:
            mpxClassesToMpxEnums[_mpxCls] = _enum
        else:
            print("warning: could not find enum MPxNode.%s for class %s" % (_enumName, _mpxName))
    else:
        missingMPx.append(_mpxName)

for _mpxName in missingMPx:
    mpxNamesToEnumNames.pop(_mpxName, None)
    mpxNamesToApiEnumNames.pop(_mpxName, None)
    mpxNamesToMayaNodes.pop(_mpxName, None)

del _mpxName, _enumName, _enum

pluginMayaTypes = set(mpxNamesToMayaNodes.values())

NON_CREATABLE = set(['MPxManipContainer',
                     'MPxManipulatorNode',
                     'MPxParticleAttributeMapperNode',
                     ])

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


def _guessEnumStrFromMpxClass(className):
    assert className.startswith('MPx')
    name = className[3:]
    enums = list(enumToStr().values())
    enumStr = 'k' + name
    if enumStr in enums:
        return enumStr


def _suggestNewMPxValues(classes=None):
    if classes is None:
        classes = [x for x in allMPx() if x not in mpxClassesToMpxEnums]

    if not classes:
        print("All classes exist in mpxClassesToMpxEnums")
        return

    import pymel.core  # need maya.cmds
    import pprint

    mpxToEnum = {}
    for cls in classes:
        className = cls.__name__
        enumStr = _guessEnumStrFromMpxClass(className)
        if enumStr:
            # add it to the master dictionary, because it is used by _buildAll.
            # this is not a complete fix, as mpxNamesToApiEnumNames, and mpxNamesToMayaNodes
            # also need to be filled out
            enumValue = getattr(mpx.MPxNode, enumStr)
            mpxClassesToMpxEnums[cls] = enumValue
            mpxNamesToEnumNames[className] = enumStr
            mpxToEnum[className] = enumStr
        else:
            print("could not find enum for %s" % className)

    if mpxToEnum:
        _, mpxToMaya, mpxToApiEnums = _buildAll()

        def prints(d):
            for key in sorted(d.keys()):
                print("    %r: %r,  # auto" % (key, d[key]))

        print('Verify and add these entries to the following dictionaries in pymel.api.plugins')
        print('mpxNamesToEnumNames')
        prints(mpxToEnum)
        print('mpxNamesToApiEnumNames')
        prints(dict((k, v) for k, v in mpxToApiEnums.items() if k in mpxToEnum))
        # pprint.pprint(mpxToApiEnums)
        print('mpxNamesToMayaNodes')
        prints(dict((k, v) for k, v in mpxToMaya.items() if k in mpxToEnum))
        # pprint.pprint(mpxToMaya)

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
_new = [_mpx.__name__ for _mpx in allMPx() if _mpx not in mpxClassesToMpxEnums]
if _new:
    import pymel.internal.plogging as plog
    _logger = plog.getLogger('pymel')
    _logger.raiseLog(_logger.WARNING, 'found new MPx classes: %s. Run pymel.api.plugins._suggestNewMPxValues()'
                     % ', '.join(_new))

#===============================================================================
# Plugin Registration / loading
#===============================================================================

registered = set()

pyNodeMethods = {}


def _pluginModule():
    return inspect.getmodule(lambda: None)


def _pluginName():
    return _pluginModule().__name__.split('.')[-1]


def _pluginFile():
    return inspect.getsourcefile(lambda: None)
#    module = sys.modules[__name__]
#    print module, __name__
#    return module.__file__


def _loadPlugin():
    thisFile = _pluginFile()
    if not maya.cmds.pluginInfo(thisFile, query=1, loaded=1):
        maya.cmds.loadPlugin(thisFile)


def _unloadPlugin():
    thisFile = _pluginFile()
    if maya.cmds.pluginInfo(thisFile, query=1, loaded=1):
        maya.cmds.unloadPlugin(thisFile)


def _getPlugin(object=None):
    if object is None:
        _loadPlugin()
        mobject = mpx.MFnPlugin.findPlugin(_pluginName())
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
    "do not call directly"
    pass

# Uninitialize the script plug-in


def uninitializePlugin(mobject):
    "do not call directly"

    # print "getmodule", inspect.getmodule( None )
    #mod = _pluginModule()

    # when uninitializePlugin is called it is execfile'd which changes the module in which this code runs.
    # we need to get the correct module first

    # FIXME: determine a reliable way to get this module's name when it is being execfile'd
    global registered
    mod = sys.modules['pymel.api.plugins']

    plugin = mpx.MFnPlugin(mobject)
    for obj in registered:
        print("deregistering", obj.name())
        obj.deregisterCommand(plugin)
    registered = set()

#===============================================================================
# Plugin Mixin Classes
#===============================================================================


class BasePluginMixin(object):
    # The name of the command or the node type
    _name = None

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
        import hashlib

        start = 0x80000
        end = 0xfffff
        size = (end - start) + 1
        md5 = hashlib.md5()
        if PY2:
            md5.update(name)
        else:
            md5.update(name.encode('utf8'))
        id = start + int(md5.hexdigest(), 16) % size
        return om.MTypeId(id)

    @classmethod
    def create(cls):
        inst = cls()
        return mpx.asMPxPtr(inst)

    @classmethod
    def _getRegisteredPluginObj(cls):
        # plugin registry should NOT be inherited from parents!
        if '_registeredPlugin_data' not in cls.__dict__:
            cls._registeredPlugin_data = None
        return cls._registeredPlugin_data

    @classmethod
    def _setRegisteredPluginObj(cls, val):
        if val and cls.isRegistered():
            raise AlreadyRegisteredError("Class %s is already registered to a plugin" % cls.__name__)
        cls._registeredPlugin_data = val

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

        cls._setRegisteredPluginObj(mplugin.object())

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
        if not cls.isRegistered():
            raise NotRegisteredError("Class %s is not registered to a plugin" % cls.__name__)

        useThisPlugin = (plugin is None)
        mplugin = _getPlugin(plugin)
        cls._deregisterOverride(mplugin, useThisPlugin)
        if plugin is None:
            registered.remove(cls)

        cls._setRegisteredPluginObj(None)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class.
        '''
        return

    @classmethod
    def isRegistered(cls):
        return bool(cls._getRegisteredPluginObj())

#===============================================================================
# Plugin Classes - inherit from these!
#===============================================================================


class Command(BasePluginMixin, mpx.MPxCommand):

    """create a subclass of this with a doIt method"""
    @classmethod
    def createSyntax(cls):
        return om.MSyntax()

    @classmethod
    def _registerOverride(cls, mplugin, useThisPlugin):
        name = cls.mayaName()
        mplugin.registerCommand(name, cls.create, cls.createSyntax)
        if useThisPlugin:
            import pymel.core
            pymel.core._addPluginCommand(mplugin.name(), name)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class.
        '''
        name = cls.mayaName()
        mplugin.deregisterCommand(name)
        if useThisPlugin:
            import pymel.core
            pymel.core._removePluginCommand(mplugin.name(), name)


class TransformationMatrix(BasePluginMixin, mpx.MPxTransformationMatrix):
    _typeId = None
    # Override to do nothing - should be (de)registered by the transform!

    @classmethod
    def register(cls, plugin=None):
        pass

    @classmethod
    def deregister(cls, plugin=None):
        pass


class FileTranslator(BasePluginMixin, mpx.MPxFileTranslator):
    # the pathname of the icon used in file selection dialogs
    _pixmapName = None

    # the name of a MEL script that will be used to display the contents of
    # the options dialog during file open/save/import/etc
    _optionsScriptName = None

    # the default value of the options string that will be passed to the
    # options script.
    _defaultOptionsString = None

    # this should be set to true if the reader method in the derived class
    # intends to issue MEL commands via the MGlobal::executeCommand method.
    # Setting this to true will slow down the creation of new objects,
    # but allows MEL commands other than those that are part of the Maya
    # Ascii file format to function correctly. This parameter defaults to
    # false.
    _requiresFullMel = False

    # the default location where this translator will store its data relative
    #  to the current project. This defaults to
    # MFnPlugin::kDefaultDataLocation The translator command parameter
    # -defaultFileRule will return this value.
    _dataStorageLocation = mpx.MFnPlugin.kDefaultDataLocation

    # The default extension for this translator
    _extension = None

    @classmethod
    def _registerOverride(cls, mplugin, useThisPlugin):
        try:
            mplugin.registerFileTranslator(cls.mayaName(),
                                           cls._pixmapName,
                                           cls.create,
                                           cls._optionsScriptName,
                                           cls._defaultOptionsString,
                                           cls._requiresFullMel,
                                           cls._dataStorageLocation)
        except Exception:
            sys.stderr.write(
                "Failed to register translator: %s" % cls.mayaName())
            raise

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        try:
            mplugin.deregisterFileTranslator(cls.mayaName())
        except Exception:
            sys.stderr.write(
                "Failed to deregister translator: %s" % cls.mayaName())
            raise

    def filter(self):
        return "*.%s" % (self._extension,)

    def defaultExtension(self):
        return self._extension

    def identifyFile(self, mfile, buffer, size):
        fileName = mfile.fullName()
        if fileName.endswith("." + self.defaultExtension()):
            return mpx.MPxFileTranslator.kIsMyFileType
        return mpx.MPxFileTranslator.kNotMyFileType


class DependNode(BasePluginMixin, mpx.MPxNode):
    # You can manually set this, or just leave it at None to let pymel
    # automatically determine it from the MPxType
    _typeEnum = None

    # If this is left as None, a 'reasonable' default will be made based on a
    # hash of the node name in the user range... to ensure no name clashes,
    # though, you should get a node id from Autodesk!
    _typeId = None

    # You can manually set this, or just leave it at None to let pymel
    # automatically determine it from the base classes
    _mpxType = None

    @classmethod
    def getMpxType(cls):
        if cls._mpxType is None:
            for pClass in inspect.getmro(cls):
                if pClass in mpxClassesToMpxEnums:
                    cls._mpxType = pClass
                    break
        return cls._mpxType

    @classmethod
    def getTypeEnum(cls):
        if cls._typeEnum is None:
            cls._typeEnum = mpxClassesToMpxEnums[cls.getMpxType()]
        return cls._typeEnum

    _classification = None

    _callbacks = collections.defaultdict(list)

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
        for _, clsObj in inspect.getmembers(cls):
            if isinstance(clsObj, PyNodeMethod):
                pluginPynodeMethods[nodeName][clsObj.name] = clsObj.func

        cls._nodeRegisterOverride(nodeName, mplugin)

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
    def _nodeRegisterOverride(cls, nodeName, mplugin):
        registerArgs = [nodeName, cls.getTypeId(), cls.create, cls.initialize,
                        cls.getTypeEnum()]
        if cls._classification:
            registerArgs.append(cls._classification)
        mplugin.registerNode(*registerArgs)

    @classmethod
    def _deregisterOverride(cls, mplugin, useThisPlugin):
        '''Override this to implement the actual deregistration behavior for
        the MPx class.
        '''
        nodeName = cls.mayaName()

        # PyNodeMethods
        global pyNodeMethods
        pyNodeMethods.get(mplugin.name(), {}).pop(nodeName, None)

        mplugin.deregisterNode(cls.getTypeId())
        if useThisPlugin:
            import pymel.core
            pymel.core._removePluginNode(mplugin.name(), nodeName)
        for id in cls._callbacks.pop(nodeName, []):
            om.MMessage.removeCallback(id)

    @classmethod
    def isAbstractClass(cls):
        # MPxPolyTrg returns True
        return False

# new in 2014
if hasattr(mpx, 'MPxAssembly'):
    class Assembly(DependNode, mpx.MPxAssembly):
        pass

# new in 2016
if hasattr(mpx, 'MPxBlendShape'):
    class BlendShape(DependNode, mpx.MPxBlendShape):
        pass


class CameraSet(DependNode, mpx.MPxCameraSet):
    pass


class Constraint(DependNode, mpx.MPxConstraint):
    pass


class DeformerNode(DependNode, mpx.MPxDeformerNode):
    pass


class EmitterNode(DependNode, mpx.MPxEmitterNode):
    pass


class FluidEmitterNode(EmitterNode, mpx.MPxFluidEmitterNode):
    pass


class FieldNode(DependNode, mpx.MPxFieldNode):
    pass

# new in 2016
if hasattr(mpx, 'MPxGeometryFilter'):
    class GeometryFilter(DependNode, mpx.MPxGeometryFilter):
        pass


class HardwareShader(DependNode, mpx.MPxHardwareShader):
    pass


class HwShaderNode(DependNode, mpx.MPxHwShaderNode):
    pass


class IkSolverNode(DependNode, mpx.MPxIkSolverNode):
    pass


class ImagePlane(DependNode, mpx.MPxImagePlane):
    pass


class LocatorNode(DependNode, mpx.MPxLocatorNode):
    pass


class ManipContainer(DependNode, mpx.MPxManipContainer):
    pass


class ManipulatorNode(DependNode, mpx.MPxManipulatorNode):
    pass

# new in 2016
if hasattr(mpx, 'MPxMotionPathNode'):
    class MotionPathNode(DependNode, mpx.MPxMotionPathNode):
        pass


class ObjectSet(DependNode, mpx.MPxObjectSet):
    pass


class ParticleAttributeMapperNode(DependNode, mpx.MPxParticleAttributeMapperNode):
    pass


class PolyTrg(DependNode, mpx.MPxPolyTrg):
    pass


class SpringNode(DependNode, mpx.MPxSpringNode):
    pass

# new in 2016
if hasattr(mpx, 'MPxSkinCluster'):
    class SkinCluster(DependNode, mpx.MPxSkinCluster):
        pass


class SurfaceShape(DependNode, mpx.MPxSurfaceShape):
    pass


class ComponentShape(SurfaceShape, mpx.MPxComponentShape):
    pass


class Transform(DependNode, mpx.MPxTransform):
    # Bug in python - can't just use MPxTransformationMatrix, as there's a
    # problem with MPxTransformationMatrix.baseTransformationMatrixId
    _transformMatrix = TransformationMatrix

    @classmethod
    def _nodeRegisterOverride(cls, nodeName, mplugin):
        registerArgs = [nodeName, cls.getTypeId(), cls.create, cls.initialize,
                        cls._transformMatrix.create,
                        cls._transformMatrix.getTypeId()]
        if cls._classification:
            registerArgs.append(cls._classification)
        mplugin.registerTransform(*registerArgs)

# these 2 appear to temporary or debugging types? they existed at some point in
# the beta for 2013, then went away?
# if hasattr(mpx, 'MPxRepMgr'):
#    class RepMgr(DependNode, mpx.MPxRepMgr): pass

# if hasattr(mpx, 'MPxRepresentation'):
#    class Representation(DependNode, mpx.MPxRepresentation): pass


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
    ...         print("Hi, I'm an instance of a MyNode PyNode - my name is %s!" % self.name())
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

def _buildPluginHierarchy(dummyClasses=None):
    '''Dynamically query the mel node hierarchy for all plugin node types

    This command must be run from within a running maya session - ie, where
    maya.cmds, etc are accessible.
    '''
    import pymel.internal.apicache as apicache

    if dummyClasses is None:
        dummyClasses = _createDummyPluginNodeClasses()

    # note that we always try to query inheritance, even for node types in
    # NON_CREATABLE, because post 2012, we should be able to query inheritance
    # without needing to create a node...
    inheritances = {}
    for pluginType, dummyClass in dummyClasses.items():
        nodeType = dummyClass.mayaName()
        wasRegistered = dummyClass.isRegistered()
        if not wasRegistered:
            dummyClass.register()
        try:
            try:
                inheritance = apicache.getInheritance(nodeType)
            except apicache.ManipNodeTypeError:
                continue
        finally:
            if not wasRegistered:
                dummyClass.deregister()
        if not inheritance:
            # If there was a problem creating a node - for instance, in the
            # case of MPxParticleAttributeMapperNode...
            continue
        assert inheritance[-1] == nodeType
        inheritances[pluginType] = inheritance[:-1]
    return inheritances


def _buildMpxNamesToApiEnumNames(dummyClasses=None, dummyNodes=None):
    import pymel.api as api
    mpxToEnumNames = {}
    with _DummyPluginNodesMaker(dummyClasses=dummyClasses,
                                alreadyCreated=dummyNodes) as nodeMaker:
        for mpxCls, mayaNode in nodeMaker.nodes.items():
            mobj = api.toMObject(mayaNode)
            mpxToEnumNames[mpxCls.__name__] = mobj.apiTypeStr()
    return mpxToEnumNames


def _buildAll():
    with _DummyPluginNodesMaker() as nodeMaker:
        hierarchy = _buildPluginHierarchy(dummyClasses=nodeMaker.dummyClasses)
        mpxToMpxEnums = _buildMpxNamesToApiEnumNames(dummyClasses=nodeMaker.dummyClasses,
                                                     dummyNodes=nodeMaker.nodes)
        mpxToMaya = _buildMpxNamesToMayaNodes(hierarchy=hierarchy)
    return hierarchy, mpxToMaya, mpxToMpxEnums


def _buildMpxNamesToMayaNodes(hierarchy=None):
    if hierarchy is None:
        hierarchy = _buildPluginHierarchy()
    mpxNamesToMayaNodes = {}
    for mpxCls, parents in hierarchy.items():
        if not parents:
            mayaType = hierarchy[mpx.MPxNode][-1]
        else:
            mayaType = parents[-1]
        mpxNamesToMayaNodes[mpxCls.__name__] = mayaType
    return mpxNamesToMayaNodes


def _createDummyPluginNodeClasses():
    '''Registers with the dummy pymel plugin a dummy node type for each MPxNode
    subclass

    returns a dictionary mapping from MPx class to a pymel dummy class of that
    type
    '''
    import logging
    pymelPlugClasses = []

    for obj in globals().values():
        if inspect.isclass(obj) and issubclass(obj, DependNode):
            pymelPlugClasses.append(obj)

    dummyClasses = {}
    for cls in pymelPlugClasses:
        class DummyClass(cls):
            _name = 'dummy' + cls.__name__
        DummyClass.__name__ = 'Dummy' + cls.__name__
        mpxType = DummyClass.getMpxType()
        if mpxType in dummyClasses:
            logger = logging.getLogger('pymel')
            logger.warning("Skipping %s: MPx type %s is already associated with %s" %
                           (DummyClass, mpxType, dummyClasses[mpxType]))
        else:
            dummyClasses[mpxType] = DummyClass

    return dummyClasses


class _DummyPluginNodesMaker(object):

    def __init__(self, dummyClasses=None, alreadyCreated=None):
        if dummyClasses is None:
            dummyClasses = _createDummyPluginNodeClasses()
        self.dummyClasses = dummyClasses
        self.toUnregister = []
        self.nodes = {}
        if alreadyCreated is None:
            alreadyCreated = {}
        self.alreadyCreated = alreadyCreated
        if self.alreadyCreated:
            self.nodes.update(self.alreadyCreated)
        self.toDelete = []

    def __enter__(self):
        for mpxCls, pyCls in self.dummyClasses.items():
            if not pyCls.isRegistered():
                self.toUnregister.append(pyCls)
                pyCls.register()
            if mpxCls not in self.alreadyCreated:
                if mpxCls.__name__ in NON_CREATABLE:
                    continue
                newNode = maya.cmds.createNode(pyCls.mayaName())
                parent = maya.cmds.listRelatives(newNode, parent=1)
                self.nodes[mpxCls] = newNode
                if parent:
                    self.toDelete.append(parent)
                else:
                    self.toDelete.append(newNode)
        return self

    def __exit__(self, type, value, traceback):
        if self.toDelete:
            maya.cmds.delete(*self.toDelete)
        for pyCls in self.toUnregister:
            pyCls.deregister()

# def _repoplulate():
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

#==============================================================================
# Utility functions
#==============================================================================

def filterPlugins(plugins, filters):
    # type: (Iterable[str], Iterable[Union[str, RePattern, Callable[[str], bool]]]) -> [str]
    '''Filters the given plugins against the given filter tests.

    Parameters
    ----------
    plugins : Iterable[str]
        List of plugin names to test
    filters : Iterable[Union[str, RePattern, Callable[[str], bool]]]
        If given, specifies plugins which should not be returned.  Can be
        specified as a simple string (in which case a plugin name, stripped of
        it's trailing extension, must match it in order to be skipped), a
        compiled regular expression (whose 'match()' method must return a result
        against a plugin in order for it to be skipped), or a callable (which
        takes a plugin name as input, and returns True if it should be skipped)
    '''
    import logging
    logger = logging.getLogger('pymel')

    # turn into a list of tester methods
    filterTests = []

    def makeNameSkipper(skipName):
        def matchesName(plugName):
            return plugName.rsplit('.', 1)[0] == skipName

        return matchesName

    for filterItem in filters:
        if isinstance(filterItem, str):
            filterTests.append(makeNameSkipper(filterItem))
        elif isinstance(filterItem, RePattern):
            filterTests.append(filterItem.match)
        elif callable(filterItem):
            filterTests.append(filterItem)
        else:
            raise TypeError(filterItem)
    filteredPlugs = []
    for plug in plugins:
        if not any(test(plug) for test in filterTests):
            filteredPlugs.append(plug)
        else:
            logger.debug("Filtering maya plugin: {}".format(plug))
    return filteredPlugs


def mayaPlugins(filters=(), loaded=None):
    # type: (Iterable[Union[str, RePattern, Callable[[str], bool]]], Optional[bool]) -> [str]
    '''All maya plugins in the maya install directory

    Parameters
    ----------
    filters : Iterable[Union[str, RePattern, Callable[[str], bool]]]
        If given, specifies plugins which should not be returned.  Passed to
        filterPlugins - see that function for a full description of this arg.
    loaded : If None (the default), then all plugins are returned regardless of
        current loaded status; if True, only currently loaded plugins are
        returned; if False, only currenlty unloaded plugins.
    '''
    import pymel.mayautils

    mayaLoc = pymel.mayautils.getMayaLocation()
    # always include some plugins in the list of maya plugins, even though
    # they're installed in a different dir
    plugins = ['mtoa']
    pluginPath = os.environ.get('MAYA_PLUG_IN_PATH')
    if pluginPath is None:
        raise RuntimeError("maya.standalone.initialize() must be called before"
                           " this function")
    # need to set to os.path.realpath to get a 'canonical' path for string comparison...
    pluginPaths = [os.path.realpath(x) for x in pluginPath.split(os.path.pathsep)]

    def isMayaPluginDir(path):
        if not os.path.isdir(path):
            return False
        if path.startswith(mayaLoc):
            return True
        if os.path.altsep:
            path = path.replace(os.path.altsep, os.path.sep)
        # if it's a bifrost plugin dir, return true
        return 'bifrost' in [x.lower() for x in path.split(os.path.sep)]

    for pluginPath in pluginPaths:
        if not isMayaPluginDir(pluginPath):
            continue
        for x in os.listdir(pluginPath):
            if os.path.isfile(os.path.join(pluginPath, x)):
                plugins.append(x)

    if loaded is not None:
        plugins = [x for x in plugins
                   if maya.cmds.pluginInfo(x, q=1, loaded=1) == loaded]

    if filters:
        plugins = filterPlugins(plugins, filters)
    return plugins


def loadAllMayaPlugins(filters=()):
    # type: (Iterable[Union[str, RePattern, Callable[[str], bool]]]) -> None
    '''will load all maya-installed plugins

    Parameters
    ----------
    filters : Iterable[Union[str, RePattern, Callable[[str], bool]]]
        If given, specifies plugins which should not be loaded.  Passed to
        filterPlugins - see that function for a full description of this arg.

    WARNING: tthe act of loading all the plugins may crash maya, especially if
    done from a non-GUI session
    '''
    import logging
    logger = logging.getLogger('pymel')
    # we iterate through the list multiple times, because some plugins won't
    # load until other plugins are loaded first... we stop if we've loaded all
    # plugins, or we went through a pass where no plugins were successfully
    # loaded
    unloadedPlugins = set(mayaPlugins(filters=filters, loaded=False))
    loadedAPlugin = True
    passNum = 0
    while unloadedPlugins and loadedAPlugin:
        passNum += 1
        logger.debug("loading all maya plugins (pass {})...".format(passNum))
        loadedAPlugin = False
        thisPass = unloadedPlugins
        unloadedPlugins = []
        for plugin in thisPass:
            try:
                logger.debug("attempting to load: {}".format(plugin))
                maya.cmds.loadPlugin(plugin, quiet=1)
            except RuntimeError:
                logger.debug("...failed")
                unloadedPlugins.append(plugin)
            else:
                logger.debug("...success!")
                loadedAPlugin = True
    logger.debug("...done loading all maya plugins")


def unloadAllPlugins(skipErrors=False, exclude=('DirectConnect',)):
    import logging
    logger = logging.getLogger('pymel')

    logger.debug("unloading all plugins...")
    loadedPlugins = maya.cmds.pluginInfo(q=True, listPlugins=True)
    loadedPlugins = filterPlugins(loadedPlugins, exclude)
    # loadedPlugins may be None
    if loadedPlugins:
        # could just unload all plugins at once with:
        # maya.cmds.unloadPlugin(force=True, *loadedPlugins)
        # ...but if we do one at a time, we can at least get debugging info
        # on which one crashed...
        for plug in loadedPlugins:
            logger.debug("...unloading: %s" % plug)
            try:
                maya.cmds.unloadPlugin(plug, force=True)
            except Exception:
                if skipErrors:
                    import traceback
                    logger.warning("Error unloading plugin %s:" % plug)
                    logger.warning(traceback.format_exc())
                else:
                    logger.error("Error unloading plugin %s:" % plug)
                    raise
    logger.debug("...done unloading all plugins")

# It's not possible to query all plugin commands that a plugin registers with
# pluginInfo, so this holds a list of plugin commands that we still want to
# wrap.
# With 2012, we can now query modelEditor, constraint, and control commands.
# Unfortunately, we still can't get context commands... so UNREPORTED_COMMANDS
# is still necessary
# We sort by type of command, so that if pluginInfo does have the necessary
# flag for reporting, we can just use that.
UNREPORTED_COMMANDS = {
    'command': {},       # all versions of maya should support this flag!
    'modelEditorCommand': {'stereoCamera': ['stereoCameraView']},
    'controlCommand': {},
    'constraintCommand': {},
    'tool': {},  # Tool replacing contextCommand to match Maya implementation
    #'other':{}, # just to hold any commands we may want that don't fall in other categories
}


def pluginCommands(pluginName, reportedOnly=False):
    '''Returns the list of all commands that the plugin provides, to the best
    of our knowledge.

    Note that depending on your version of maya, this may not actually be the
    list of all commands provided.
    '''
    import logging
    logger = logging.getLogger('pymel')

    commands = []
    for cmdType, pluginToCmds in UNREPORTED_COMMANDS.items():
        try:
            moreCmds = maya.cmds.pluginInfo(pluginName, query=1, **{cmdType: 1})
        except TypeError:  # will get this if it's a flag pluginInfo doesn't know
            if reportedOnly:
                moreCmds = []
            else:
                moreCmds = pluginToCmds.get(pluginName, [])
        except Exception:
            logger.error("Failed to get %s list from %s" % (cmdType, pluginName))
            moreCmds = []

        # moreCmds may be None, as pluginInfo will return None
        if moreCmds:
            commands.extend(moreCmds)
    return commands


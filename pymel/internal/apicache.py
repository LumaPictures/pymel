""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here
import sys, inspect, time, os.path

import pymel.api as api
import pymel.versions as versions
from pymel.util import expandArgs
import pymel.util as _util
import startup
import plogging as _plogging

_logger = _plogging.getLogger(__name__)

class ApiEnum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )
    def __repr__(self):
        return '%s( %s )' % (self.__class__.__name__, super(ApiEnum, self).__repr__())
    def pymelName(self):
        import pymel.internal.factories as factories
        parts = list(self)
        pymelName = factories.apiClassNameToPymelClassName(self[0])
        if pymelName is not None:
            parts[0] = pymelName
        return '.'.join( [str(x) for x in parts] )

if versions.current() < versions.v2012:
    # Before 2012, api had Enum, and when we unpickle the caches, it will
    # need to be there... could rebuild the caches (like I had to do with
    # mayaApiMelBridge) but don't really want to...
    api.Enum = ApiEnum
    Enum = ApiEnum

def _makeDgModGhostObject(mayaType, dagMod, dgMod):
    # we create a dummy object of this type in a dgModifier (or dagModifier)
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene

    # Note: at one point, if we didn't call the dgMod/dagMod.deleteNode method,
    # and we call this function while loading a scene (for instance, if the scene requires
    # a plugin that isn't loaded, and defines custom node types), then the nodes were still
    # somehow created, despite never explicitly calling doIt()...
    # ... however, this seems to no longer be the case, and the deleteNode calls are apparently
    # harmful
    if type(dagMod) is not api.MDagModifier or type(dgMod) is not api.MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"

    # Regardless of whether we're making a DG or DAG node, make a parent first -
    # for some reason, this ensures good cleanup (don't ask me why...??)
    parent = dagMod.createNode ( 'transform', api.MObject())

    try :
        # DependNode
        obj = dgMod.createNode ( mayaType )
    except RuntimeError:
        # DagNode
        try:
            obj = dagMod.createNode ( mayaType, parent )
        except Exception, err:
            _logger.debug("Error trying to create ghost node for '%s': %s" %  (mayaType, err))
            return None

    if api.isValidMObject(obj) :
        return obj
    else :
        _logger.debug("Error trying to create ghost node for '%s'" %  mayaType)
        return None


def _defaultdictdict(cls, val=None):
    if val is None:
        return _util.defaultdict(dict)
    else:
        return _util.defaultdict(dict, val)
                   
class ApiMelBridgeCache(startup.SubItemCache):
    NAME = 'mayaApiMelBridge'
    DESC = 'the API-MEL bridge' 
    COMPRESSED = True
    USE_VERSION = False
    _CACHE_NAMES = '''apiToMelData apiClassOverrides'''.split()
    
    CACHE_TYPES = {'apiToMelData':_defaultdictdict}
    STORAGE_TYPES = {'apiToMelData':dict}


class ApiCache(startup.SubItemCache):
    NAME = 'mayaApi'
    DESC = 'the API cache'
    COMPRESSED = True
    USE_VERSION = True
    _CACHE_NAMES = '''apiTypesToApiEnums apiEnumsToApiTypes mayaTypesToApiTypes
                   apiTypesToApiClasses apiClassInfo'''.split()


    EXTRA_GLOBAL_NAMES = tuple('''reservedMayaTypes reservedApiTypes
                            mayaTypesToApiEnums'''.split())
                            
    # Descriptions of various elements:
    
    # Maya static info :
    # Initializes various static look-ups to speed up Maya types conversions
    # self.apiClassInfo
    # self.apiTypesToApiEnums
    # self.apiEnumsToApiTypes
    # self.apiTypesToApiClasses

    # Reserved Maya types and API types that need a special treatment (abstract types)
    # TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
    # strangely createNode ('cluster') works but dgMod.createNode('cluster') doesn't
    # self.reservedMayaTypes
    # self.reservedApiTypes

    # Lookup of currently existing Maya types as keys with their corresponding API type as values.
    # Not a read only (static) dict as these can change (if you load a plugin)
    # self.mayaTypesToApiTypes

    # lookup tables for a direct conversion between Maya type to their MFn::Types enum
    # self.mayaTypesToApiEnums


    # TODO: may always need a manual map from reserved types to apiType,
    # but may want to dynamically generate the list of abstract types
    # (and possibly manipulators)?
    # see maintenance/inheritance.py for sample of how to create list
    # of abstract types
    RESERVED_TYPES = { 'invalid':'kInvalid', 'base':'kBase',
                'object':'kNamedObject',
                'dependNode':'kDependencyNode', 'dagNode':'kDagNode',
                'entity':'kDependencyNode',
                'constraint':'kConstraint', 'field':'kField',
                'geometryShape':'kGeometric', 'shape':'kShape',
                'deformFunc':'kDeformFunc', 'cluster':'kClusterFilter',
                'dimensionShape':'kDimension',
                'abstractBaseCreate':'kCreate', 'polyCreator':'kPolyCreator',
                'polyModifier':'kMidModifier', 'subdModifier':'kSubdModifier',
                'curveInfo':'kCurveInfo',
                'curveFromSurface':'kCurveFromSurface',
                'surfaceShape': 'kSurface',
                'revolvedPrimitive':'kRevolvedPrimitive',
                'plane':'kPlane', 'curveShape':'kCurve',
                'animCurve': 'kAnimCurve',
                'resultCurve':'kResultCurve', 'cacheBase':'kCacheBase',
                'filter':'kFilter',
                'blend':'kBlend', 'ikSolver':'kIkSolver',
                'light':'kLight', 'renderLight':'kLight',
                'nonAmbientLightShapeNode':'kNonAmbientLight',
                'nonExtendedLightShapeNode':'kNonExtendedLight',
                'texture2d':'kTexture2d', 'texture3d':'kTexture3d', 
                'textureEnv':'kTextureEnv',
                'primitive':'kPrimitive', 'reflect':'kReflect',
                'smear':'kSmear',
                'plugin':'kPlugin',
                'THdependNode':'kPluginDependNode',
                'THlocatorShape':'kPluginLocatorNode',
                'pluginData':'kPluginData',
                'THdeformer':'kPluginDeformerNode',
                'pluginConstraint':'kPluginConstraintNode',
                'unknown':'kUnknown', 'unknownDag':'kUnknownDag',
                'unknownTransform':'kUnknownTransform',
                'dynBase': 'kDynBase',
                'polyPrimitive': 'kPolyPrimitive',
                'nParticle': 'kNParticle',
                'birailSrf': 'kBirailSrf', 'pfxGeometry': 'kPfxGeometry',

                # creating these 2 crash Maya
                'xformManip':'kXformManip',
                'moveVertexManip':'kMoveVertexManip',
    }


    def __init__(self):
        super(ApiCache, self).__init__()
        for name in self.EXTRA_GLOBAL_NAMES:
            setattr(self, name, {})

    def _buildMayaToApiInfo(self, mayaTypes):
        # Fixes for types that don't have a MFn by faking a node creation and testing it
        # Make it faster by pre-creating the nodes used to test
        dagMod = api.MDagModifier()
        dgMod = api.MDGModifier()

        # Put in a debug, because this can be crashy
        _logger.debug("Starting to create ghost nodes...")

        unknownTypes = set()

        for mayaType in mayaTypes :
            apiType = None
            if self.reservedMayaTypes.has_key(mayaType) :
                apiType = self.reservedMayaTypes[mayaType]
            else:
                obj = _makeDgModGhostObject(mayaType, dagMod, dgMod)
                if obj :
                    apiType = obj.apiTypeStr()
                else:
                    unknownTypes.add(mayaType)
            if apiType is not None:
                self.mayaTypesToApiTypes[mayaType] = apiType

        # Put in a debug, because this can be crashy
        _logger.debug("...finished creating ghost nodes")
        
        if len(unknownTypes) > 0:
            _logger.warn("Unable to get maya-to-api type info for the following nodes: %s" % ", ".join(unknownTypes))

        for mayaType, apiType in self.mayaTypesToApiTypes.iteritems() :
            self.addMayaType( mayaType, apiType )

    def _buildApiTypesList(self):
        """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with
        an existing api type"""

        self.apiTypesToApiEnums = dict( inspect.getmembers(api.MFn, lambda x:type(x) is int))
        self.apiEnumsToApiTypes = dict( (self.apiTypesToApiEnums[k], k) for k in self.apiTypesToApiEnums.keys())


    def _buildMayaReservedTypes(self, force=False):
        """
        Build a list of Maya reserved types.
        These cannot be created directly from the API, thus the dgMod trick to find the corresponding Maya type won't work
        """
        # Must have already built apiTypesToApiEnums
        
        if not force and (getattr(self, 'reservedMayaTypes', None)  
                          and getattr(self, 'reservedApiTypes', None) ):
            return        

        # no known api types: these do not have valid api types, so we add them in to avoid querying them on each load
        invalidReservedTypes = {'deformableShape' : 'kInvalid', 'controlPoint' : 'kInvalid'}

        # filter to make sure all these types exist in current version (some are Maya2008 only)
        self.reservedMayaTypes = dict( (item[0], item[1]) for item in filter(lambda i:i[1] in self.apiTypesToApiEnums, self.RESERVED_TYPES.iteritems()) )
        self.reservedMayaTypes.update(invalidReservedTypes)
        # build reverse dict
        self.reservedApiTypes = dict( (item[1], item[0]) for item in self.reservedMayaTypes.iteritems() )


    ## Initialises MayaTypes for a faster later access
    #def _buildMayaTypesList() :
    #    """Updates the cached MayaTypes lists """
    #    start = time.time()
    #    from maya.cmds import ls as _ls
    #    # api types/enums dicts must be created before reserved type bc they are used for filtering
    #    self._buildMayaReservedTypes()
    #
    #    # use dict of empty keys just for faster random access
    #    # the nodes returned by ls will be added by createPyNodes and pluginLoadedCB
    #    # add new types
    #    print "reserved types", self.reservedMayaTypes
    #    for mayaType, apiType in self.reservedMayaTypes.items() + [(k, None) for k in _ls(nodeTypes=True)]:
    #         #if not self.mayaTypesToApiTypes.has_key(mayaType) :
    #         self.addMayaType( mayaType, apiType )
    #    elapsed = time.time() - start
    #    print "Updated Maya types list in %.2f sec" % elapsed

    def _buildApiClassInfo(self):
        _logger.debug("Starting ApiCache._buildApiClassInfo...") 
        from pymel.internal.parsers import ApiDocParser
        self.apiClassInfo = {}
        parser = ApiDocParser(api, enumClass=ApiEnum)

        for name, obj in inspect.getmembers( api, lambda x: type(x) == type and x.__name__.startswith('M') ):
            if not name.startswith( 'MPx' ):
                try:
                    info = parser.parse(name)
                    self.apiClassInfo[ name ] = info
                except (IOError, ValueError,IndexError), e:
                    _logger.warn( "failed to parse docs for %r:\n%s" % (name, e) )
        _logger.debug("...finished ApiCache._buildApiClassInfo")

    def _buildApiRelationships(self) :
        """
        Used to rebuild api info from scratch.
        
        WARNING: will load all maya-installed plugins, without making an
        attempt to return the loaded plugins to the state they were at before
        this command is run.  Also, the act of loading all the plugins may
        crash maya, especially if done from a non-GUI session
        """
        # Put in a debug, because this can be crashy
        _logger.debug("Starting ApiCache._buildApiTypeHierarchy...")        
        
        def _MFnType(x) :
            if x == api.MFnBase :
                return self.apiEnumsToApiTypes[ 1 ]  # 'kBase'
            else :
                try :
                    return self.apiEnumsToApiTypes[ x().type() ]
                except :
                    return self.apiEnumsToApiTypes[ 0 ] # 'kInvalid'

        if not startup.mayaStartupHasRun():
            startup.mayaInit()
        import maya.cmds

        import pymel.api.plugins as plugins
        # load all maya plugins
        
        # There's some weirdness with plugin loading on windows XP x64... if
        # you have a fresh user profile, and do:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.mel as mel
        # mel.eval('''source "initialPlugins.mel"''')
        
        # ..then things work.  But if you import maya.OpenMaya:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.OpenMaya
        # import maya.mel as mel
        # mel.eval('''source "initialPlugins.mel"''')
        
        # ...it crashes when loading Mayatomr.  Also, oddly, if you load
        # Mayatomr directly, instead of using initialPlugins.mel, it also
        # crashes:
        
        # import maya.standalone
        # maya.standalone.initialize()
        # import maya.cmds
        # maya.cmds.loadPlugin('C:\\3D\\Autodesk\\Maya2012\\bin\\plug-ins\\Mayatomr.mll')
        
        # Anyway, for now, adding in the line to do sourcing of initialPlugins.mel
        # until I can figure out if it's possible to avoid this crash...
        import maya.mel
        maya.mel.eval('source "initialPlugins.mel"')
        plugins.loadAllMayaPlugins()

        # all of maya OpenMaya api is now imported in module api's namespace
        mfnClasses = inspect.getmembers(api, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
        for name, mfnClass in mfnClasses:
            current = _MFnType(mfnClass)
            if not current:
                _logger.warning("MFnClass gave MFnType %s" % current)
            elif current == 'kInvalid':
                _logger.warning("MFnClass gave MFnType %s" % current)
            else:
                self.apiTypesToApiClasses[ current ] = mfnClass

        self._buildApiClassInfo()

        allMayaTypes = self.reservedMayaTypes.keys() + maya.cmds.ls(nodeTypes=True)
        self._buildMayaToApiInfo(allMayaTypes)
        
        _logger.debug("...finished ApiCache._buildApiTypeHierarchy")

    def addMayaType(self, mayaType, apiType=None, updateObj=None):
        """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """

        if apiType is not 'kInvalid' :
            apiEnum = getattr( api.MFn, apiType )
            self.mayaTypesToApiTypes[mayaType] = apiType
            self.mayaTypesToApiEnums[mayaType] = apiEnum

    def removeMayaType(self, mayaType, updateObj=None):
        """ Remove a type from the MayaTypes lists.

            - mayaTypesToApiTypes
            - mayaTypesToApiEnums
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """
        self.mayaTypesToApiEnums.pop( mayaType, None )
        self.mayaTypesToApiTypes.pop( mayaType, None )

    def build(self):
        """
        Used to rebuild api cache, either by loading from a cache file, or rebuilding from scratch.
        """
        super(ApiCache, self).build()
        # If we loaded from cache, we still need to rebuild the reserved types
        self._buildMayaReservedTypes(force=False)

    def read(self, raw=False):
        data = super(ApiCache, self).read()
        if not raw:
            # Before 2012, we cached reservedMayaTypes and reservedApiTypes,
            # even though they weren't used...
            if data is not None and len(data) != len(self._CACHE_NAMES):
                if len(data) == 8 and versions.current() < versions.v2012:
                    data = data[2:6] + data[7:]
                else:
                    # we need to rebuild, return None
                    data = None
        return data

    def rebuild(self):
        """Rebuild the api cache from scratch
        
        Unlike 'build', this does not attempt to load a cache file, but always
        rebuilds it by parsing the docs, etc.
        """
        _logger.info( "Rebuilding the API Caches..." )

        # fill out the data structures
        self._buildApiTypesList()
        #_buildMayaTypesList()
        
        self._buildMayaReservedTypes(force=True)

        self._buildApiRelationships()

        # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
        _logger.info( 'merging in dictionary of manual api overrides')
        self._mergeClassOverrides()

    def _mergeClassOverrides(self, bridgeCache=None):
        if bridgeCache is None:
            bridgeCache = ApiMelBridgeCache()
            bridgeCache.build()
        _util.mergeCascadingDicts( bridgeCache.apiClassOverrides, self.apiClassInfo, allowDictToListMerging=True )

    def melBridgeContents(self):
        return self._mayaApiMelBridge.contents()
    
    def extraDicts(self):
        return tuple( getattr(self, x) for x in self.EXTRA_GLOBAL_NAMES )

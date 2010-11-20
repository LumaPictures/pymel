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

class Enum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )
    def __repr__(self): return repr(str(self))
    def pymelName(self, forceType=None):
        import pymel.internal.factories as factories
        parts = list(self)
        if forceType:
            parts[0] = forceType
        else:
            mfn = getattr( api, self[0] )
            mayaTypeDict = factories.apiEnumsToMayaTypes[ mfn().type() ]
            parts[0] = _util.capitalize( mayaTypeDict.keys()[0] )

        return '.'.join( [str(x) for x in parts] )
    
if versions.current() < versions.v2012:
    # Before 2012, api had Enum, and when we unpickle the caches, it will
    # need to be there... could rebuild the caches (like I had to do with
    # mayaApiMelBridge) but don't really want to...
    api.Enum = Enum

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

    try:
        try :
            # Try making it with dgMod FIRST - this way, we can avoid making an
            # unneccessary transform if it is a DG node
            obj = dgMod.createNode ( mayaType )
        except RuntimeError:
            # DagNode
            obj = dagMod.createNode ( mayaType, parent )
            _logger.debug( "Made ghost DAG node of type '%s'" % mayaType )
        else:
            # DependNode
            _logger.debug( "Made ghost DG node of type '%s'" % mayaType )
#            dgMod.deleteNode(obj)
    except:
        obj = api.MObject()

#    dagMod.deleteNode(parent)

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
                   
class ApiMelBridgeCache(startup.MayaCache):
    NAME = 'mayaApiMelBridge'
    DESC = 'the API-MEL bridge' 
    COMPRESSED = True
    USE_VERSION = False
    CACHE_NAMES = '''apiToMelData apiClassOverrides'''.split()
    
    CACHE_TYPES = {'apiToMelData':_defaultdictdict}
    STORAGE_TYPES = {'apiToMelData':dict}


class ApiCache(startup.MayaCache):
    NAME = 'mayaApi'
    DESC = 'the API cache'
    COMPRESSED = True
    USE_VERSION = True
    CACHE_NAMES = '''apiTypesToApiEnums apiEnumsToApiTypes mayaTypesToApiTypes
                   apiTypesToApiClasses apiClassInfo'''.split()


    EXTRA_GLOBAL_NAMES = '''reservedMayaTypes reservedApiTypes
                            apiTypesToMayaTypes mayaTypesToApiEnums
                            apiEnumsToMayaTypes'''.split()
                            
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

    # Lookup of currently existing Maya API types as keys with their corresponding Maya type as values.
    # Not a read only (static) dict as these can change (if you load a plugin)
    # In the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )
    # self.apiTypesToMayaTypes

    # lookup tables for a direct conversion between Maya type to their MFn::Types enum
    # self.mayaTypesToApiEnums

    # lookup tables for a direct conversion between API type to their MFn::Types enum
    # self.apiEnumsToMayaTypes

    RESERVED_TYPES = { 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
                'entity':'kDependencyNode', \
                'constraint':'kConstraint', 'field':'kField', \
                'geometryShape':'kGeometric', 'shape':'kShape', 'deformFunc':'kDeformFunc', 'cluster':'kClusterFilter', \
                'dimensionShape':'kDimension', \
                'abstractBaseCreate':'kCreate', 'polyCreator':'kPolyCreator', \
                'polyModifier':'kMidModifier', 'subdModifier':'kSubdModifier', \
                'curveInfo':'kCurveInfo', 'curveFromSurface':'kCurveFromSurface', \
                'surfaceShape': 'kSurface', 'revolvedPrimitive':'kRevolvedPrimitive', 'plane':'kPlane', 'curveShape':'kCurve', \
                'animCurve': 'kAnimCurve', 'resultCurve':'kResultCurve', 'cacheBase':'kCacheBase', 'filter':'kFilter',
                'blend':'kBlend', 'ikSolver':'kIkSolver', \
                'light':'kLight', 'renderLight':'kLight', 'nonAmbientLightShapeNode':'kNonAmbientLight', 'nonExtendedLightShapeNode':'kNonExtendedLight', \
                'texture2d':'kTexture2d', 'texture3d':'kTexture3d', 'textureEnv':'kTextureEnv', \
                'primitive':'kPrimitive', 'reflect':'kReflect', 'smear':'kSmear', \
                'plugin':'kPlugin', 'THdependNode':'kPluginDependNode', 'THlocatorShape':'kPluginLocatorNode', 'pluginData':'kPluginData', \
                'THdeformer':'kPluginDeformerNode', 'pluginConstraint':'kPluginConstraintNode', \
                'unknown':'kUnknown', 'unknownDag':'kUnknownDag', 'unknownTransform':'kUnknownTransform',\
                # creating these 2 crash Maya
                'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip',

                'dynBase': 'kDynBase', 'polyPrimitive': 'kPolyPrimitive','nParticle': 'kNParticle', 'birailSrf': 'kBirailSrf', 'pfxGeometry': 'kPfxGeometry',
    }


    
    SUB_CACHE_TYPES = [ApiMelBridgeCache]
    SUB_CACHE_ATTRS = ['_' + cacheType.NAME for cacheType in SUB_CACHE_TYPES]
    
    def _make_item_property(name, cacheAttr):
        def _get_item(self):
            cache = getattr(self, cacheAttr)
            return getattr(cache, name)
            
        _get_item.__name__ = '_get_%s' % name

        def _set_item(self, val):
            cache = getattr(self, cacheAttr)
            setattr(cache, name, val)
        _set_item.__name__ = '_set_%s' % name

        return _get_item, _set_item, property(_get_item, _set_item)

    for cacheType, cacheName in zip(SUB_CACHE_TYPES, SUB_CACHE_ATTRS):
        # make properties for each of the sub-cache's sub-items
        for itemName in cacheType.CACHE_NAMES:
            getter, setter, prop = _make_item_property(itemName, cacheName)
            # can't do setattr, because we don't have a class object yet...
            # and can't modify locals()...
            # and properties MUST be defined inside class, so when the class
            # is created, the magic is set up...
            # so only way to do this seems to be to use exec
            exec "%s = getter" % getter.__name__
            exec "%s = setter" % setter.__name__
            exec "%s = prop" % itemName

    # done with _make_item_property now - don't want it to become a method...
    del _make_item_property
        
    def __init__(self):
        super(ApiCache, self).__init__()
        for cacheType, cacheAttr in zip(self.SUB_CACHE_TYPES, self.SUB_CACHE_ATTRS):
            # Initialize the sub-caches
            subCache = cacheType()
            setattr(self, cacheAttr, subCache)
        
        for name in self.EXTRA_GLOBAL_NAMES:
            self.initVal(name)

    def _getMObject(self, nodeType, dagMod, dgMod) :
        """ Returns a queryable MObject from a given apiType or mayaType"""

        # cant create these nodes, some would crahs MAya also
        if self.reservedApiTypes.has_key(nodeType) or self.reservedMayaTypes.has_key(nodeType) :
            return None

        if self.apiTypesToMayaTypes.has_key(nodeType) :
            mayaType = self.apiTypesToMayaTypes[nodeType].keys()[0]
            #apiType = nodeType
        elif self.mayaTypesToApiTypes.has_key(nodeType) :
            mayaType = nodeType
            #apiType = self.mayaTypesToApiTypes[nodeType]
        else :
            return None

        return _makeDgModGhostObject(mayaType, dagMod, dgMod)

    def _createNodes(self, dagMod, dgMod, *args) :
        """pre-build a apiType:MObject, and mayaType:apiType lookup for all provided types, be careful that these MObject
            can be used only as long as dagMod and dgMod are not deleted
            
            returns result, mayaResult, unableToCreate
            
            where:
                result is a dict mapping from an apiType to an MObject of that type
                mayaResult is a dict mapping from mayaType to apiType
                unableToCreate is a set of mayaTypes that we were unable to make"""
            
        # Put in a debug, because this can be crashy
        _logger.debug("Starting ApiCache._createNodes...")

        result = {}
        mayaResult = {}
        unableToCreate = set()


        for mayaType in args :
            if self.reservedMayaTypes.has_key(mayaType) :
                apiType = self.reservedMayaTypes[mayaType]
                #print "reserved", mayaType, apiType
                mayaResult[mayaType] = apiType
                result[apiType] = None

            else :
                obj = _makeDgModGhostObject(mayaType, dagMod, dgMod)
                if obj :
                    apiType = obj.apiTypeStr()
                    mayaResult[mayaType] = apiType
                    result[apiType] = obj
                else:
                    unableToCreate.add(mayaType)

        # Put in a debug, because this can be crashy
        _logger.debug("...finished ApiCache._createNodes")
        
        return result, mayaResult, unableToCreate

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
        parser = ApiDocParser(api, enumClass=Enum)

        for name, obj in inspect.getmembers( api, lambda x: type(x) == type and x.__name__.startswith('M') ):
            if not name.startswith( 'MPx' ):
                try:
                    info = parser.parse(name)
                    self.apiClassInfo[ name ] = info
                except (IOError, ValueError,IndexError), e:
                    _logger.warn( "failed to parse docs for %r:\n%s" % (name, e) )
        _logger.debug("...finished ApiCache._buildApiClassInfo")

    # Build a dictionnary of api types and parents to represent the MFn class hierarchy
    def _buildApiTypeHierarchy(self) :
        """
        Used to rebuild api info from scratch.
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

        import pymel.mayautils as mayautils
        # load all maya plugins
        mayaLoc = mayautils.getMayaLocation()
        # need to set to os.path.realpath to get a 'canonical' path for string comparison...
        pluginPaths = [os.path.realpath(x) for x in os.environ['MAYA_PLUG_IN_PATH'].split(os.path.pathsep)]
        for pluginPath in [x for x in pluginPaths if x.startswith( mayaLoc ) and os.path.isdir(x) ]:
            for x in os.listdir( pluginPath ):
                if os.path.isfile( os.path.join(pluginPath,x)):
                    try:
                        maya.cmds.loadPlugin( x )
                    except RuntimeError: pass

        allMayaTypes = self.reservedMayaTypes.keys() + maya.cmds.ls(nodeTypes=True)

        # all of maya OpenMaya api is now imported in module api's namespace
        MFnClasses = inspect.getmembers(api, lambda x: inspect.isclass(x) and issubclass(x, api.MFnBase))
        MFnTree = inspect.getclasstree( [x[1] for x in MFnClasses] )

        for MFnClass, bases in expandArgs(MFnTree, type='list') :
            current = _MFnType(MFnClass)
            if current and current != 'kInvalid' and len(bases) > 0:
                #Check that len(x[1]) > 0 because base python 'object' will have no parents...
                assert len(bases) == 1
                parent = _MFnType(bases[0])
                if parent:
                    self.apiTypesToApiClasses[ current ] = MFnClass
                else:
                    print "debug info - MFnClass %s gave MFnType %s, but could not determine type of parent class %s" % (MFnClass, MFnType, parent)

        self._buildApiClassInfo()

        # Fixes for types that don't have a MFn by faking a node creation and testing it
        # Make it faster by pre-creating the nodes used to test
        dagMod = api.MDagModifier()
        dgMod = api.MDGModifier()

        nodeDict, mayaDict, unableToCreate = self._createNodes( dagMod, dgMod, *allMayaTypes )
        if len(unableToCreate) > 0:
            _logger.warn("Unable to create the following nodes: %s" % ", ".join(unableToCreate))

        for mayaType, apiType in mayaDict.items() :
            self.mayaTypesToApiTypes[mayaType] = apiType
            self.addMayaType( mayaType, apiType )

        _logger.debug("...finished ApiCache._buildApiTypeHierarchy")

    def addMayaType(self, mayaType, apiType=None, updateObj=None):
        """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for.

            - mayaTypesToApiTypes
            - apiTypesToMayaTypes
            - apiTypesToApiEnums
            - apiEnumsToApiTypes
            - mayaTypesToApiEnums
            - apiEnumsToMayaTypes
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """

        if apiType is not 'kInvalid' :

            apiEnum = getattr( api.MFn, apiType )

            defType = self.reservedMayaTypes.has_key(mayaType)

            self.mayaTypesToApiTypes[mayaType] = apiType
            if not self.apiTypesToMayaTypes.has_key(apiType) :
                self.apiTypesToMayaTypes[apiType] = { mayaType : defType }
            else :
                self.apiTypesToMayaTypes[apiType][mayaType] = defType

            # these are static and are build elsewhere
            #self.apiTypesToApiEnums[apiType] = apiEnum
            #self.apiTypesToApiClasses[apiEnum] = apiType

            self.mayaTypesToApiEnums[mayaType] = apiEnum
            if not self.apiEnumsToMayaTypes.has_key(apiEnum) :
                self.apiEnumsToMayaTypes[apiEnum] = { mayaType : None }
            else:
                self.apiEnumsToMayaTypes[apiEnum][mayaType] = None

    def removeMayaType(self, mayaType, updateObj=None):
        """ Remove a type from the MayaTypes lists.

            - mayaTypesToApiTypes
            - apiTypesToMayaTypes
            - apiTypesToApiEnums
            - apiEnumsToApiTypes
            - mayaTypesToApiEnums
            - apiEnumsToMayaTypes
            
        if updateObj is given, this instance will first be updated from it,
        before the mayaType is added.
        """
        try:
            apiEnum = self.mayaTypesToApiEnums.pop( mayaType )
        except KeyError: pass
        else:
            enums = self.apiEnumsToMayaTypes[apiEnum]
            enums.pop( mayaType, None )
            if not enums:
                self.apiEnumsToMayaTypes.pop(apiEnum)
                self.apiEnumsToApiTypes.pop(apiEnum)
        try:
            apiType = self.mayaTypesToApiTypes.pop( mayaType, None )
        except KeyError: pass
        else:
            # due to lazy loading we are not guaranteed to have an entry
            if apiType in self.apiTypesToMayaTypes:
                types = self.apiTypesToMayaTypes[apiType]
                _logger.debug('removeMayaType %s: %s' % (mayaType, types))
                types.pop( mayaType, None )
                if not types:
                    self.apiTypesToMayaTypes.pop(apiType)
                    self.apiTypesToApiEnums.pop(apiType)

    def build(self):
        """
        Used to rebuild api cache, either by loading from a cache file, or rebuilding from scratch.
        """
        super(ApiCache, self).build()
        # If we loaded from cache, we still need to rebuild the reserved types
        self._buildMayaReservedTypes(force=False)
        self._mayaApiMelBridge.build()

    def _load(self):
        data = super(ApiCache, self)._load()
        # Before 2012, we cached reservedMayaTypes and reservedApiTypes,
        # even though they weren't used...
        if data is not None and len(data) != len(self.CACHE_NAMES):
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

        self._buildApiTypeHierarchy()

        # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
        _logger.info( 'merging in dictionary of manual api overrides')
        self._mergeClassOverrides()
        
        self.save()

    def _mergeClassOverrides(self):
        _util.mergeCascadingDicts( self.apiClassOverrides, self.apiClassInfo, allowDictToListMerging=True )
        
    def melBridgeContents(self):
        return self._mayaApiMelBridge.contents()
    
    def extraDicts(self):
        return tuple( getattr(self, x) for x in self.EXTRA_GLOBAL_NAMES )

""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here
import sys, inspect, time, os.path

import pymel.api as api
from pymel.util import expandArgs
import pymel.util as _util
import startup
import plogging as _plogging

_logger = _plogging.getLogger(__name__)

__all__ = ['reservedMayaTypes', 'reservedApiTypes', 'apiTypesToApiEnums', 'apiEnumsToApiTypes',  
'mayaTypesToApiTypes', 'apiTypesToApiClasses', 'apiTypeHierarchy', 'apiClassInfo',
'apiToMelData', 'apiClassOverrides']

class Enum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )
    def __repr__(self): return repr(str(self))
    def pymelName(self, forceType=None):
        parts = list(self)
        if forceType:
            parts[0] = forceType
        else:
            mfn = getattr( api, self[0] )
            mayaTypeDict = apiCache.apiEnumsToMayaTypes[ mfn().type() ]
            parts[0] = _util.capitalize( mayaTypeDict.keys()[0] )

        return '.'.join( [str(x) for x in parts] )

api.Enum = Enum
# prevent auto-completion generator from getting confused
api.Enum.__module__ = 'pymel.api'

def _makeDgModGhostObject(mayaType, dagMod, dgMod):
    # we create a dummy object of this type in a dgModifier (or dagModifier)
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    
    # Note that you need to call the dgMod/dagMod.deleteNode method as well - if we don't,
    # and we call this function while loading a scene (for instance, if the scene requires
    # a plugin that isn't loaded, and defines custom node types), then the nodes are still
    # somehow created, despite never explicitly calling doIt()
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
            dgMod.deleteNode(obj)
    except:
        obj = api.MObject()

    dagMod.deleteNode(parent)

    if api.isValidMObject(obj) :
        return obj
    else :
        _logger.debug("Error trying to create ghost node for '%s'" %  mayaType)
        return None


def saveApiCache():
    startup.writeCache( ( apiCache.reservedMayaTypes, apiCache.reservedApiTypes, 
                           apiCache.apiTypesToApiEnums, apiCache.apiEnumsToApiTypes, 
                           apiCache.mayaTypesToApiTypes, 
                           apiCache.apiTypesToApiClasses, apiCache.apiTypeHierarchy, apiCache.apiClassInfo ),
                        'mayaApi', 'the API cache' )

def loadApiToMelBridge():

    data = startup.loadCache( 'mayaApiMelBridge', 'the API-MEL bridge', useVersion=False, compressed=True )
    if data is not None:
        # maya 8.5 fix: convert dict to defaultdict
        bridge, overrides = data
        bridge = _util.defaultdict(dict, bridge)
        return bridge, overrides
    
    # no bridge cache exists. create default
    bridge = _util.defaultdict(dict)
    
    # no api overrides exist. create default
    overrides = {}
    
    return bridge, overrides

def saveApiToMelBridge():
    # maya 8.5 fix: convert defaultdict to dict
    bridge = dict(apiToMelData)
    startup.writeCache( (bridge,apiClassOverrides), 'mayaApiMelBridge', 'the api-mel bridge', useVersion=False )


apiToMelData, apiClassOverrides = loadApiToMelBridge()
                             
class ApiCache(object):
    
    # Maya static info :
    # Initializes various static look-ups to speed up Maya types conversions
    apiClassInfo = {}
    apiTypesToApiEnums = {}
    apiEnumsToApiTypes = {}
    
    apiTypesToApiClasses = {}
    
    # Reserved Maya types and API types that need a special treatment (abstract types)
    # TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
    # strangely createNode ('cluster') works but dgMod.createNode('cluster') doesn't
    reservedMayaTypes = {}
    reservedApiTypes = {}
    
    # some handy aliases / shortcuts easier to remember and use than actual Maya type name  
    shortMayaTypes = {'all':'base', 'valid':'base', 'any':'base', 'node':'dependNode', 'dag':'dagNode', \
                    'deformer':'geometryFilter', 'weightedDeformer':'weightGeometryFilter', 'geometry':'geometryShape', \
                    'surface':'surfaceShape', 'revolved':'revolvedPrimitive', 'deformable':'deformableShape', \
                    'curve':'curveShape' }              
                    
    
    #: Lookup of currently existing Maya types as keys with their corresponding API type as values.
    #: Not a read only (static) dict as these can change (if you load a plugin)
    mayaTypesToApiTypes = {}
    
    #: Lookup of currently existing Maya API types as keys with their corresponding Maya type as values.
    #: Not a read only (static) dict as these can change (if you load a plugin)
    #: In the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )
    apiTypesToMayaTypes = {}
        
    #: lookup tables for a direct conversion between Maya type to their MFn::Types enum
    mayaTypesToApiEnums = {}
        
    #: lookup tables for a direct conversion between API type to their MFn::Types enum 
    apiEnumsToMayaTypes = {}
    
     
    # Cache API types hierarchy, using MFn classes hierarchy and additionnal trials
    # TODO : do the same for Maya types, but no clue how to inspect them apart from parsing docs
    
    
    #: Reserved API type hierarchy, for virtual types where we can not use the 'create trick'
    #: to query inheritance, as of 2008 types and API types seem a bit out of sync as API types
    #: didn't follow latest Maya types additions...
    reservedApiHierarchy = { 'kNamedObject':'kBase', 'kDependencyNode':'kNamedObject', 'kDagNode':'kDependencyNode', \
                        'kConstraint':'kTransform', 'kField':'kTransform', \
                        'kShape':'kDagNode', 'kGeometric':'kShape', 'kDeformFunc':'kShape', 'kClusterFilter':'kWeightGeometryFilt', \
                        'kDimension':'kShape', \
                        'kCreate':'kDependencyNode', 'kPolyCreator':'kDependencyNode', \
                        'kMidModifier':'kDependencyNode', 'kSubdModifier':'kDependencyNode', \
                        'kCurveInfo':'kCreate', 'kCurveFromSurface':'kCreate', \
                        'kSurface':'kGeometric', 'kRevolvedPrimitive':'kGeometric', 'kPlane':'kGeometric', 'kCurve':'kGeometric', \
                        'kAnimCurve':'kDependencyNode', 'kResultCurve':'kAnimCurve', 'kCacheBase':'kDependencyNode' ,'kFilter':'kDependencyNode', \
                        'kBlend':'kDependencyNode', 'kIkSolver':'kDependencyNode', \
                        'kLight':'kShape', 'kNonAmbientLight':'kLight', 'kNonExtendedLight':'kNonAmbientLight', \
                        'kTexture2d':'kDependencyNode', 'kTexture3d':'kDependencyNode', 'kTextureEnv':'kDependencyNode', \
                        'kPlugin':'kBase', 'kPluginDependNode':'kDependencyNode', 'kPluginLocatorNode':'kLocator', \
                        'kPluginDeformerNode':'kGeometryFilt', 'kPluginConstraintNode':'kConstraint', 'kPluginData':'kData', \
                        'kUnknown':'kDependencyNode', 'kUnknownDag':'kDagNode', 'kUnknownTransform':'kTransform',\
                        'kXformManip':'kTransform', 'kMoveVertexManip':'kXformManip' }
    
    apiTypeHierarchy = {}
    
    def _buildMayaReservedTypes(self):
        """ 
        Build a list of Maya reserved types.
        These cannot be created directly from the API, thus the dgMod trick to find the corresponding Maya type won't work
        """
            
        reservedTypes = { 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
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
        # no known api types: these do not have valid api types, so we add them in to avoid querying them on each load
        invalidReservedTypes = {'deformableShape' : 'kInvalid', 'controlPoint' : 'kInvalid'}
        
        # filter to make sure all these types exist in current version (some are Maya2008 only)
        self.reservedMayaTypes = dict( (item[0], item[1]) for item in filter(lambda i:i[1] in self.apiTypesToApiEnums, reservedTypes.iteritems()) )
        self.reservedMayaTypes.update(invalidReservedTypes)
        # build reverse dict
        self.reservedApiTypes = dict( (item[1], item[0]) for item in self.reservedMayaTypes.iteritems() )
 
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
    
    # check if a an API type herits from another
    # it can't b e done for "virtual" types (in self.reservedApiTypes)
    def _hasFn(self, apiType, dagMod, dgMod, parentType=None) :
        """ Get the Maya API type from the name of a Maya type """
        if parentType is None :
            parentType = 'kBase'
        # Reserved we can't determine it as we can't create the node, all we can do is check if it's
        # in the self.reservedApiHierarchy
        if self.reservedApiTypes.has_key(apiType) :
            return self.reservedApiHierarchy.get(apiType, None) == parentType
        # Need the MFn::Types enum for the parentType
        if self.apiTypesToApiEnums.has_key(parentType) :
            typeInt = self.apiTypesToApiEnums[parentType]
        else :
            return False
        # print "need creation for %s" % apiType
        obj = self._getMObject(apiType, dagMod, dgMod, parentType) 
        if api.isValidMObject(obj) :
            return obj.hasFn(typeInt)
        else :
            return False
     
    
    # Filter the given API type list to retain those that are parent of apiType
    # can pass a list of types to check for being possible parents of apiType
    # or a dictionnary of types:node to speed up testing
    def _parentFn(self, apiType, dagMod, dgMod, *args, **kwargs) :
        """ Checks the given API type list, or API type:MObject dictionnary to return the first parent of apiType """
        if not kwargs :
            if not args :
                args = ('kBase', )
            kwargs = dict( (args[k], None) for k in args )
        else :
            for k in args :
                if not kwargs.has_key(k) :
                    kwargs[k] = None
        # Reserved we can't determine it as we can't create the node, all we can do is check if it's
        # in the self.reservedApiHierarchy
        if self.reservedApiTypes.has_key(apiType) :
            p = self.reservedApiHierarchy.get(apiType, None)
            if p is not None :
                for t in kwargs.keys() :
                    if p == t :
                        return t
            return None
    
        result = None           
        obj = kwargs.get(apiType, None)        
        if not api.isValidMObject(obj) :
            # print "need creation for %s" % apiType
            obj = self._getMObject(apiType, dagMod, dgMod)
        if api.isValidMObject(obj) :
            if not kwargs.get(apiType, None) :
                kwargs[apiType] = obj          # update it if we had to create
            parents = []
            for t in kwargs.keys() :
                # Need the MFn::Types enum for the parentType
                if t != apiType :
                    if self.apiTypesToApiEnums.has_key(t) :
                        ti = self.apiTypesToApiEnums[t]
                        if obj.hasFn(ti) :
                            parents.append(t)
            # problem is the MObject.hasFn method returns True for all ancestors, not only first one
            if len(parents) :
                if len(parents) > 1 :
                    for p in parents :
                        if self.apiTypesToApiEnums.has_key(p) :
                            ip = self.apiTypesToApiEnums[p]
                            isFirst = True
                            for q in parents :
                                if q != p :
                                    stored = kwargs.get(q, None)
                                    if not stored :
                                        if self.reservedApiTypes.has_key(q) :
                                            isFirst = not self.reservedApiHierarchy.get(q, None) == p
                                        else :                                    
                                            stored = self._getMObject(q, dagMod, dgMod)
                                            if not kwargs.get(q, None) :
                                                kwargs[q] = stored          # update it if we had to create                                        
                                    if stored :
                                        isFirst = not stored.hasFn(ip)
                                if not isFirst :
                                    break
                            if isFirst :
                                result = p
                                break
                else :
                    result = parents[0]
                                     
        return result
    
    def _createNodes(self, dagMod, dgMod, *args) :
        """pre-build a apiType:MObject, and mayaType:apiType lookup for all provided types, be careful that these MObject
            can be used only as long as dagMod and dgMod are not deleted"""
    
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
        return result, mayaResult, unableToCreate
    
    # child:parent lookup of the Maya API classes hierarchy (based on the existing MFn class hierarchy)
    # TODO : fix that, doesn't accept the Singleton base it seems
    # class self.apiTypeHierarchy(FrozenTree) :
    #    """ Hierarchy Tree of all API Types """
    #    __metaclass__ = Singleton
    
    def _buildApiTypesList(self):
        """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with 
        an existing api type"""
        
    
        self.apiTypesToApiEnums = dict( inspect.getmembers(api.MFn, lambda x:type(x) is int)) 
        self.apiEnumsToApiTypes = dict( (self.apiTypesToApiEnums[k], k) for k in self.apiTypesToApiEnums.keys()) 

        
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
        from pymel.internal.parsers import ApiDocParser
        self.apiClassInfo = {}
#        try:
        parser = ApiDocParser(api)
#        except IOError, msg: 
#            _logger.warn( "failed to find docs for current version: %s", name )
            
        for name, obj in inspect.getmembers( api, lambda x: type(x) == type and x.__name__.startswith('M') ):
            if not name.startswith( 'MPx' ):
                
                try:
                    try:
                        info = parser.parse(name)
                        self.apiClassInfo[ name ] = info
                    except IOError:
                        _logger.warn( "failed to parse docs: %s", name )

                except (ValueError,IndexError), msg: 
                    _logger.warn( "failed %s %s" % ( name, msg ) )
 
    # Build a dictionnary of api types and parents to represent the MFn class hierarchy
    def _buildApiTypeHierarchy(self) :
        """
        Used to rebuild api info from scratch.
        
        Set 'apiClassInfo' to a valid apiClassInfo structure to disable rebuilding of apiClassInfo
        - this is useful for versions < 2009, as these versions cannot parse the api docs; by passing
        in an apiClassInfo, you can rebuild all other api information.  If left at the default value
        of 'None', then it will be rebuilt using the apiDocParser.
        """
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
        self.apiTypeHierarchy = {}
        
        for x in expandArgs(MFnTree, type='list') :
            MFnClass = x[0]
            current = _MFnType(MFnClass)
            if current and current != 'kInvalid' and len(x[1]) > 0:
                #Check that len(x[1]) > 0 because base python 'object' will have no parents...
                parent = _MFnType(x[1][0])
                if parent:
                    self.apiTypesToApiClasses[ current ] = MFnClass
                    self.apiTypeHierarchy[ current ] = parent
        
        if not self.apiClassInfo:
            self._buildApiClassInfo()
                        
        # print self.apiTypeHierarchy.keys()
        # Fixes for types that don't have a MFn by faking a node creation and testing it
        # Make it faster by pre-creating the nodes used to test
        dagMod = api.MDagModifier()
        dgMod = api.MDGModifier()      
        #nodeDict = self._createNodes(dagMod, dgMod, *self.apiTypesToApiEnums.keys())
        nodeDict, mayaDict, unableToCreate = self._createNodes( dagMod, dgMod, *allMayaTypes )
        if len(unableToCreate) > 0:
            _logger.warn("Unable to create the following nodes: %s" % ", ".join(unableToCreate))
        
        for mayaType, apiType in mayaDict.items() :
            self.mayaTypesToApiTypes[mayaType] = apiType
            self.addMayaType( mayaType, apiType )
        
        # Fix? some MFn results are not coherent with the hierarchy presented in the docs :
        self.apiTypeHierarchy.pop('kWire', None)
        self.apiTypeHierarchy.pop('kBlendShape', None)
        self.apiTypeHierarchy.pop('kFFD', None)
        for k in self.apiTypesToApiEnums.keys() :
            if k not in self.apiTypeHierarchy.keys() :
                #print "%s not in self.apiTypeHierarchy, looking for parents" % k
                #startParent = time.time()
                p = self._parentFn(k, dagMod, dgMod, **nodeDict)
                #endParent = time.time()
                if p :
                    #print "Found parent: %s in %.2f sec" % (p, endParent-startParent)
                    self.apiTypeHierarchy[k] = p
                else :
                    #print "Found none in %.2f sec" % (endParent-startParent)     
                    pass         
                                           
        # print self.apiTypeHierarchy.keys()
        # make a Tree from that child:parent dictionnary
    
    def addMayaType(self, mayaType, apiType=None):
        """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for. 
        
            - apiCache.mayaTypesToApiTypes
            - apiCache.apiTypesToMayaTypes
            - apiCache.apiTypesToApiEnums
            - apiCache.apiEnumsToApiTypes
            - apiCache.mayaTypesToApiEnums
            - apiCache.apiEnumsToMayaTypes
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
            #apiCache.apiTypesToApiEnums[apiType] = apiEnum
            #apiCache.apiTypesToApiClasses[apiEnum] = apiType
            
            self.mayaTypesToApiEnums[mayaType] = apiEnum
            if not self.apiEnumsToMayaTypes.has_key(apiEnum) :
                self.apiEnumsToMayaTypes[apiEnum] = { mayaType : None }
            else:
                self.apiEnumsToMayaTypes[apiEnum][mayaType] = None 

    def removeMayaType(self, mayaType):
        """ Remove a type from the MayaTypes lists. 
        
            - apiCache.mayaTypesToApiTypes
            - apiCache.apiTypesToMayaTypes
            - apiCache.apiTypesToApiEnums
            - apiCache.apiEnumsToApiTypes
            - apiCache.mayaTypesToApiEnums
            - apiCache.apiEnumsToMayaTypes
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
            types = self.apiTypesToMayaTypes[apiType]
            types.pop( mayaType, None )
            if not types:
                self.apiTypesToMayaTypes.pop(apiType)
                self.apiTypesToApiEnums.pop(apiType)
              
    def build(self, rebuildAllButClassInfo=False):
        """
        Used to rebuild api cache, either by loading from a cache file, or rebuilding from scratch.
        
        Set 'rebuildAllButClassInfo' to True to force rebuilding of all info BUT self.apiClassInfo -
        this is useful for versions < 2009, as these versions cannot parse the api docs; by setting
        this to False, you can rebuild all other api information.
        """
        
        # Need to initialize this to possibly pass into _buildself.apiTypeHierarchy, if rebuildAllButClassInfo
        self.apiClassInfo = None
        
        data = startup.loadCache( 'mayaApi', 'the API cache', compressed=True )
        
        self._buildMayaReservedTypes()
        
        if data is not None:
            
            #self.reservedMayaTypes = data[0]
            #self.reservedApiTypes = data[1]
            self.apiTypesToApiEnums = data[2]
            self.apiEnumsToApiTypes = data[3]
            self.mayaTypesToApiTypes = data[4]
            self.apiTypesToApiClasses = data[5]
            self.apiTypeHierarchy = data[6]
            self.apiClassInfo = data[7]
            
            
            if not rebuildAllButClassInfo:
                # Note that even if rebuildAllButClassInfo, we still want to load
                # the cache file, in order to grab self.apiClassInfo
                return
                
        
        _logger.info( "Rebuilding the API Caches..." )
        
        # fill out the data structures
        self._buildApiTypesList()
        #self.apiTypesToApiEnums, self.apiTypesToApiClasses = self._buildApiTypesList()
        #_buildMayaTypesList()
        
        if not rebuildAllButClassInfo:
            self.apiClassInfo = None
        
        self._buildApiTypeHierarchy()
    
        # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
        _logger.info( 'merging in dictionary of manual api overrides')
        _util.mergeCascadingDicts( apiClassOverrides, self.apiClassInfo, allowDictToListMerging=True )
        
        startup.writeCache( ( self.reservedMayaTypes, self.reservedApiTypes, 
                               self.apiTypesToApiEnums, self.apiEnumsToApiTypes, 
                               self.mayaTypesToApiTypes, 
                               self.apiTypesToApiClasses, self.apiTypeHierarchy, self.apiClassInfo ), 
                               'mayaApi', 'the API cache' )
        
        return

    def caches(self):
        return (self.reservedMayaTypes, self.reservedApiTypes, 
                               self.apiTypesToApiEnums, self.apiEnumsToApiTypes, 
                               self.mayaTypesToApiTypes, 
                               self.apiTypesToApiClasses, self.apiTypeHierarchy, self.apiClassInfo )


def toApiTypeStr( obj ):
    if isinstance( obj, int ):
        return apiCache.apiEnumsToApiTypes.get( obj, None )
    elif isinstance( obj, basestring ):
        return apiCache.mayaTypesToApiTypes.get( obj, None)
    
def toApiTypeEnum( obj ):
    try:
        return apiCache.apiTypesToApiEnums[obj]
    except KeyError:
        return apiCache.mayaTypesToApiEnums.get(obj,None)

def toMayaType( obj ):
    if isinstance( obj, int ):
        return apiCache.apiEnumsToMayaTypes.get( obj, None )
    elif isinstance( obj, basestring ):
        return apiCache.apiTypesToMayaTypes.get( obj, None)
    
def toApiFunctionSet( obj ):
    if isinstance( obj, basestring ):
        try:
            return apiCache.apiTypesToApiClasses[ obj ]
        except KeyError:
            return apiCache.apiTypesToApiClasses.get( apiCache.mayaTypesToApiTypes.get( obj, None ) )
         
    elif isinstance( obj, int ):
        try:
            return apiCache.apiTypesToApiClasses[ apiCache.apiEnumsToApiTypes[ obj ] ]
        except KeyError:
            return

def isValidMayaType (arg):
    return mayaTypesToApiTypes.has_key(arg)

# get the API type from a maya type
def mayaTypeToApiType(mayaType) :
    """ Get the Maya API type from the name of a Maya type """
    try:
        return apiCache.mayaTypesToApiTypes[mayaType]
    except KeyError:
        apiType = 'kInvalid'
        # Reserved types must be treated specially
        if apiCache.reservedMayaTypes.has_key(mayaType) :
            # It's an abstract type            
            apiType = apiCache.reservedMayaTypes[mayaType]
        else :
            # we create a dummy object of this type in a dgModifier
            # as the dgModifier.doIt() method is never called, the object
            # is never actually created in the scene
            obj = api.MObject() 
            dagMod = api.MDagModifier()
            dgMod = api.MDGModifier()
            obj = _makeDgModGhostObject(mayaType, dagMod, dgMod)
            if api.isValidMObject(obj):
                apiType = obj.apiTypeStr()
        return apiType
        
def getComponentTypes():
    # WTF is kMeshFaceVertComponent?? it doesn't inherit from MFnComponent,
    # and there's also a kMeshVtxFaceComponent (which does)??
    mfnCompBase = api.MFnComponent()
    mfnCompTypes = (api.MFnSingleIndexedComponent(),
                    api.MFnDoubleIndexedComponent(),
                    api.MFnTripleIndexedComponent())
    # Maya 2008 and before didn't haveMFnUint64SingleIndexedComponent
    if hasattr(api.MFn, 'kUint64SingleIndexedComponent'):
        mfnCompTypes += (api.MFnUint64SingleIndexedComponent(),)
    
    componentTypes = {}
    for compType in mfnCompTypes + (mfnCompBase,):
        componentTypes[compType.type()] = []

    for apiEnum in apiCache.apiEnumsToApiTypes:
        if mfnCompBase.hasObj(apiEnum):
            for compType in mfnCompTypes:
                if compType.hasObj(apiEnum):
                    break
            else:
                compType = mfnCompBase
            componentTypes[compType.type()].append(apiEnum)
                
    return componentTypes

   
def addMayaType(mayaType, apiType=None):
    """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for. 
    
        - apiCache.mayaTypesToApiTypes
        - apiCache.apiTypesToMayaTypes
        - apiCache.apiTypesToApiEnums
        - apiCache.apiEnumsToApiTypes
        - apiCache.mayaTypesToApiEnums
        - apiCache.apiEnumsToMayaTypes
    """


    if apiType is None:
        apiType = mayaTypeToApiType(mayaType)    
    apiCache.addMayaType(mayaType, apiType)

def removeMayaType(mayaType):
    """ Remove a type from the MayaTypes lists. 
    
        - apiCache.mayaTypesToApiTypes
        - apiCache.apiTypesToMayaTypes
        - apiCache.apiTypesToApiEnums
        - apiCache.apiEnumsToApiTypes
        - apiCache.mayaTypesToApiEnums
        - apiCache.apiEnumsToMayaTypes
    """
    apiCache.removeMayaType(mayaType)

#-------------------------------------------------------------------------------------

_start = time.time()

apiCache = ApiCache()
apiCache.build(rebuildAllButClassInfo=False)

(reservedMayaTypes, reservedApiTypes, apiTypesToApiEnums, apiEnumsToApiTypes, 
mayaTypesToApiTypes, apiTypesToApiClasses, apiTypeHierarchy, apiClassInfo) = apiCache.caches()
                                  
_elapsed = time.time() - _start
_logger.debug( "Initialized API Cache in in %.2f sec" % _elapsed )

#-------------------------------------------------------------------------------------
 
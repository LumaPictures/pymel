"""
Contains classes corresponding to the Maya type hierarchy, including `DependNode`, `Transform`, `Mesh`, and `Camera`.
"""
import sys, os, re

import pmcmds as cmds #@UnresolvedImport
import inspect, itertools, math
import pymel.util as util
import factories as _factories
import pymel.api as api #@UnresolvedImport
import datatypes
import logging
_logger = logging.getLogger(__name__)

# to make sure Maya is up
import pymel.mayahook as mayahook
from pymel import version

from maya.cmds import about as _about
import maya.mel as mm

#from general import *
import general
import other
from animation import listAnimatable as _listAnimatable
from system import namespaceInfo as _namespaceInfo, FileReference as _FileReference

_thisModule = sys.modules[__name__]

#__all__ = ['Component', 'MeshEdge', 'MeshVertex', 'MeshFace', 'Attribute', 'DependNode' ]

def _makeAllParentFunc_and_ParentFuncWithGenerationArgument(baseParentFunc):
    """
    Generator function which makes 2 new 'parent' functions, given a baseParentFunc.
    
    The first function returns an array of all parents, starting from the parent immediately above, going up.
    The second returns baseParentFunc, but adds an optional keyword arg, generations, used to control
    the number of levels up to find the parent.

    It is assumed that the first arg to baseParentFunc is the object whose parent we wish to find.
    
    The optional 'generations' keyword arg will be added as though it were the very FIRST
    optional keyword arg given - ie, if we have:
    
    def baseParentFunc(mandatory1, mandatory2, optional1=None, optional2="foo", *args, **kwargs)
    
    then the function returned will be like a function declared like:
    
    parentFuncWithGenerations(mandatory1, mandatory2, generations=1, optional1=None, optional2="foo", *args, **kwargs)
    """
    namedArgs, varargs, varkwargs, defaults = inspect.getargspec(baseParentFunc)
    if defaults is None:
        mandatoryArgs = namedArgs
        defaultArgs = {}
    else:
        mandatoryArgs = namedArgs[:-len(defaults)]
        defaultArgs = dict(zip(namedArgs[-len(defaults):], defaults)) 
    
    def getAllParents(*args, **kwargs):
        """Return a list of all parents above this.
        
        Starts from the parent immediately above, going up."""
        
        x = baseParentFunc(*args, **kwargs)
        res = []
        while x:
            res.append(x)
            x = baseParentFunc(x, *args[1:], **kwargs)
        return res
    
    def parentFuncWithGenerations(*args, **kwargs):
        if 'generations' in kwargs:
            generations = kwargs.pop('generations')
        elif len(args) > len(mandatoryArgs):
            args = list(args)
            generations = args.pop(len(mandatoryArgs))
        else:
            generations = 1

        if generations == 0:
            return args[0]
        elif generations >= 1:
            firstParent = baseParentFunc(*args, **kwargs)
            
            if generations == 1 or firstParent is None:
                return firstParent
            else:
                kwargs['generations'] = generations - 1
                return parentFuncWithGenerations(firstParent, *args[1:], **kwargs)
        elif generations < 0:
            allParents = getAllParents(*args, **kwargs)
            
            if -generations > (len(allParents) + 1):
                return None
            # Assures we can return self
            elif -generations == (len(allParents) + 1):
                return args[0]
            else:
                return allParents[generations]
                        
    parentFuncWithGenerations.__doc__ = baseParentFunc.__doc__
    
    return getAllParents, parentFuncWithGenerations

# TODO:
# -----
# Seperate out _makeComponentHandle and _setComponentHandle - ie, order should be:
#    1. _makeComponentHandle
#    2. _makeMFnComponent
#    3. _setComponentHandle
# Implement makeComponentFromIndex - have it return an MObject handle
# Implement multiple component labels! (ie, surface iso can be 'u' or 'v')
# Add 'setCompleteData' when we can find how many components (instead of just 'setComplete')
# Handle multiple _ComponentLabel__'s that refer to different flavors of same component type -
#    ie, NurbsSurface.u/.v/.uv, transform.rotatePivot/scalePivot
# NurbsSurfaceRange
# Make it work with multiple component types in single component(?) 

def _sequenceToComponentSlice( array ):
    """given an array, convert to a maya-formatted slice"""
    
    return [ HashableSlice( x.start, x.stop-1, x.step) for x in util.sequenceToSlices( array ) ]

def _formatSlice(sliceObj):
    startIndex, stopIndex, step = sliceObj.start, sliceObj.stop, sliceObj.step
    if startIndex == stopIndex:
        sliceStr = '%s' % startIndex
    elif step is not None and step != 1:
        sliceStr = '%s:%s:%s' % (startIndex, stopIndex, step)
    else:
        sliceStr = '%s:%s' % (startIndex, stopIndex)
    return sliceStr 

# even though slice objects are essentially immutable, due to implementation
# of proxyClass, need to set sourceIsImmutable to False
# (not sure why proxyClass is implemented like this...?)
ProxySlice = util.proxyClass( slice, 'ProxySlice', dataAttrName='_slice', sourceIsImmutable=False)
# Really, don't need to have another class inheriting from
# the proxy class, but do this so I can define a method using
# normal class syntax...
class HashableSlice( ProxySlice):
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], (slice, HashableSlice)):
            if isinstance(args[0], HashableSlice):
                self._slice = args[0]._slice
            else:
                self._slice = args[0]
        else:
            self._slice = slice(*args, **kwargs)
            
    def __hash__(self):
        if not hasattr(self, '_hash'):
            self._hash = (self.start, self.stop, self.step).__hash__()
        return self._hash
    
    @property
    def start(self):
        return self._slice.start
      
    @property
    def stop(self):
        return self._slice.stop

    @property
    def step(self):
        return self._slice.step

class Component( general.PyNode ):
    """
    Abstract base class for pymel components.
    """
    
    __metaclass__ = _factories.MetaMayaComponentWrapper
    _mfncompclass = api.MFnComponent
    _apienum__ = api.MFn.kComponent
    _ComponentLabel__ = None

    # Maya 2008 and earlier have no kUint64SingleIndexedComponent /
    # MFnUint64SingleIndexedComponent...
    _componentEnums = [api.MFn.kComponent,
                       api.MFn.kSingleIndexedComponent,
                       api.MFn.kDoubleIndexedComponent,
                       api.MFn.kTripleIndexedComponent]

    if hasattr(api.MFn, 'kUint64SingleIndexedComponent'):
        _hasUint64 = True
        _componentEnums.append(api.MFn.kUint64SingleIndexedComponent)
    else:
        _hasUint64 = False
        
    @classmethod
    def printComponentTypes(cls):
        # Output
    #        kComponent :
    #             kCurveParamComponent
    #             kIsoparmComponent
    #             kPivotComponent
    #             kEdgeComponent
    #             kSurfaceRangeComponent
    #             kDecayRegionCapComponent
    #             kSetGroupComponent
    #        kSingleIndexedComponent :
    #             kCurveCVComponent
    #             kCurveEPComponent
    #             kCurveKnotComponent
    #             kMeshEdgeComponent
    #             kMeshPolygonComponent
    #             kMeshVertComponent
    #             kDynParticleSetComponent
    #             kMeshMapComponent
    #             kSubdivMapComponent
    #        kDoubleIndexedComponent :
    #             kSurfaceCVComponent
    #             kSurfaceEPComponent
    #             kSurfaceKnotComponent
    #             kMeshVtxFaceComponent
    #             kSurfaceFaceComponent
    #        kTripleIndexedComponent :
    #             kLatticeComponent
    #        kUint64SingleIndexedComponent :
    #             kSubdivCVComponent
    #             kSubdivEdgeComponent
    #             kSubdivFaceComponent
    
    # WTF is kMeshFaceVertComponent?? it doesn't inherit from MFnComponent,
    # and there's also a kMeshVtxFaceComponent (which does)??
        compTypes = api.getComponentTypes()
        for compType, compList in compTypes.iteritems():
            print api.ApiEnumsToApiTypes()[compType], ":"
            for exactComp in compList:
                print "    ", api.ApiEnumsToApiTypes()[exactComp]

    @classmethod
    def _componentMObjEmpty(cls, mobj):
        """
        Returns true if the given component mobj is empty (has no elements).
        """
        
#        Note that a component marked as complete will return elementCount == 0,
#        even if it is not truly empty.
#        
#        Even MFnComponent.isEmpty will sometimes "lie" if component is complete.
#        
#        Try this:
#        
#        import maya.OpenMaya as api
#        import maya.cmds as cmds
#        
#        melSphere = cmds.sphere()[0]
#        selList = api.MSelectionList()
#        selList.add(melSphere + '.cv[*][*]')
#        compObj = api.MObject()
#        dagPath = api.MDagPath()
#        selList.getDagPath(0, dagPath, compObj)
#        mfnComp = api.MFnDoubleIndexedComponent(compObj)
#        print "is empty:", mfnComp.isEmpty()
#        print "is complete:", mfnComp.isComplete()
#        print "elementCount:", mfnComp.elementCount()
#        print
#        mfnComp.setComplete(True)
#        print "is empty:", mfnComp.isEmpty()
#        print "is complete:", mfnComp.isComplete()
#        print "elementCount:", mfnComp.elementCount()
#        print
#        mfnComp.setComplete(False)
#        print "is empty:", mfnComp.isEmpty()
#        print "is complete:", mfnComp.isComplete()
#        print "elementCount:", mfnComp.elementCount()
#        print
        
        mfnComp = api.MFnComponent(mobj)
        completeStatus = mfnComp.isComplete()
        if completeStatus:
            mfnComp.setComplete(False)
        isEmpty = mfnComp.isEmpty()
        if completeStatus:
            mfnComp.setComplete(True)
        return isEmpty
        
    def __init__(self, *args, **kwargs ):
        # the Component class can be instantiated several ways:
        # Component(dagPath, component):
        #    args get stored on self._node and
        #    self.__apiobjects__['MObjectHandle'] respectively
        # Component(dagPath):
        #    in this case, stored on self.__apiobjects__['MDagPath']
        #    (self._node will be None)
        
        # First, ensure that we have a self._node...
        if not self._node :
            dag = self.__apiobjects__['MDagPath']
            self._node = general.PyNode(dag)
        assert(self._node)

        # Need to do indices checking even for non-dimensional
        # components, because the ComponentIndex might be used to
        # specify the 'flavor' of the component - ie, 'scalePivot' or
        # 'rotatePivot' for Pivot components
        self._indices = self.__apiobjects__.get('ComponentIndex', None)
        
        if self._indices:
            if util.isIterable(self._ComponentLabel__):
                oldCompLabel = set(self._ComponentLabel__)
            else:
                oldCompLabel = set( (self._ComponentLabel__,) )
            if isinstance(self._indices, dict):
                if len(self._indices) > 1:
                    isComplete = False
                    assert set(self._indices.iterkeys()).issubset(oldCompLabel)
                    self._ComponentLabel__ = self._indices.keys()
                else:
                    # dict only has length 1..
                    self._ComponentLabel__ = self._indices.keys()[0]
                    self._indices = self._indices.values()[0]
            if isinstance(self._indices, ComponentIndex) and self._indices.label:
                assert self._indices.label in oldCompLabel
                self._ComponentLabel__ = self._indices.label
        elif 'MObjectHandle' not in self.__apiobjects__:
            # We're making a component by ComponentClass(shapeNode)...
            # set a default label if one is specified
            if self._defaultLabel():
                self._ComponentLabel__ = self._defaultLabel()
        
    def __apimdagpath__(self) :
        "Return the MDagPath for the node of this component, if it is valid"
        try:
            #print "NODE", self.node()
            return self.node().__apimdagpath__()
        except AttributeError: pass
        
    def __apimobject__(self) :
        "get the MObject for this component if it is valid"
        handle = self.__apihandle__()
        if api.isValidMObjectHandle( handle ) :
            return handle.object()
        # Can't use self.name(), as that references this!
        raise MayaObjectError( self._completeNameString() )        

    def __apiobject__(self) :
        return self.__apimobject__()

    def __apihandle__(self) :
        if 'MObjectHandle' not in self.__apiobjects__:
            handle = self._makeComponentHandle()
            if not handle or not api.isValidMObjectHandle(handle):
                raise MayaObjectError( self._completeNameString() )
            self.__apiobjects__['MObjectHandle'] = handle            
        return self.__apiobjects__['MObjectHandle']

    def __apicomponent__(self):
        mfnComp = self.__apiobjects__.get('MFnComponent', None)
        if mfnComp is None:
            mfnComp = self._mfncompclass(self.__apimobject__())
            self.__apiobjects__['MFnComponent'] = mfnComp
        return mfnComp
    
    def __apimfn__(self):
        return self.__apicomponent__()

    def __eq__(self, other):
        if not hasattr(other, '__apicomponent__'):
            return False
        return self.__apicomponent__().isEqual( other.__apicomponent__().object() )
               
    def __str__(self): 
        return str(self.name())
    
    def __unicode__(self): 
        return self.name()
                
    def _completeNameString(self):
        return u'%s.%s' % ( self.node(), self.plugAttr())

    def _makeComponentHandle(self):
        component = None
        # try making from MFnComponent.create, if _mfncompclass has it defined
        if ('create' in dir(self._mfncompclass) and
            self._apienum__ not in self._componentEnums + [None]):
            try:
                component = self._mfncompclass().create(self._apienum__)
            # Note - there's a bug with kSurfaceFaceComponent - can't use create
            except RuntimeError:
                pass
            else:
                if not api.isValidMObject(component):
                    component = None        
        
        # that didn't work - try checking if we have a valid plugAttr  
        if not component and self.plugAttr():
            try:
                component = api.toApiObject(self._completeNameString())[1]
            except:
                pass
            else:
                if not api.isValidMObject(component):
                    component = None

        # component objects we create always start out 'complete'
        mfnComp = self._mfncompclass(component)
        mfnComp.setComplete(True)

        return api.MObjectHandle(component)

    def __melobject__(self):
        selList = api.MSelectionList()
        selList.add(self.__apimdagpath__(), self.__apimobject__(), False)
        strings = []
        selList.getSelectionStrings(0, strings)
        nodeName = self.node().name() + '.'
        strings = [ nodeName + x.split('.',1)[-1] for x in strings ]
        if not strings:
            return self._completeNameString()
        elif len(strings) == 1:
            return strings[0]
        else:
            return strings
            
    def name(self):
        melObj = self.__melobject__()
        if isinstance(melObj, basestring):
            return melObj
        return repr(melObj)
                
    def node(self):
        return self._node
    
    def plugAttr(self):
        return self._ComponentLabel__
    
    def isComplete(self, *args, **kwargs):
        return self.__apicomponent__().isComplete()
    
    @staticmethod
    def numComponentsFromStrings(*componentStrings):
        """
        Does basic string processing to count the number of components
        given a number of strings, which are assumed to be the valid mel names
        of components. 
        """
        numComps = 0
        for compString in componentStrings:
            indices = re.findall(r'\[[^\]]*\]', compString)
            newComps = 1
            if indices:
                for index in indices:
                    if ':' in index:
                        indexSplit = index.split(':')
                        # + 1 is b/c mel indices are inclusive
                        newComps *= int(indexSplit[1]) - int(indexSplit[0]) + 1
            numComps += newComps
        return numComps
                    
class DimensionedComponent( Component ):
    """
    Components for which having a __getitem__ of some sort makes sense
    
    ie, myComponent[X] would be reasonable.
    """
    # All components except for the pivot component and the unknown ones are
    # indexable in some manner
    
    dimensions = 0

    def __init__(self, *args, **kwargs ):
        # the Component class can be instantiated several ways:
        # Component(dagPath, component):
        #    args get stored on self._node and
        #    self.__apiobjects__['MObjectHandle'] respectively
        # Component(dagPath):
        #    in this case, stored on self.__apiobjects__['MDagPath']
        #    (self._node will be None)
        super(DimensionedComponent, self).__init__(*args, **kwargs)
                        
        isComplete = True

        # If we're fed an MObjectHandle already, we don't allow
        # __getitem__ indexing... unless it's complete
        handle = self.__apiobjects__.get('MObjectHandle', None)
        if handle is not None:
            mfncomp = self._mfncompclass(handle.object())
            if not mfncomp.isComplete():
                isComplete = False

        if isinstance(self._indices, dict) and len(self._indices) > 1:
            isComplete = False
                        
        # If the component is complete, we allow further indexing of it using
        # __getitem__
        # Whether or not __getitem__ indexing is allowed, and what dimension
        # we are currently indexing, is stored in _partialIndex
        # If _partialIndex is None, __getitem__ indexing is NOT allowed
        # Otherwise, _partialIndex should be a ComponentIndex object,
        # and it's length indicates how many dimensions have already been
        # specified. 
        if isComplete:
            # Do this test before doing 'if self._indices',
            # because an empty ComponentIndex will be 'False',
            # but could still have useful info (like 'label')!
            if isinstance(self._indices, ComponentIndex):
                if len(self._indices) < self.dimensions:
                    self._partialIndex = self._indices
                else:
                    self._partialIndex = None
            elif self._indices:
                self._partialIndex = None
            else:
                self._partialIndex = ComponentIndex(label=self._ComponentLabel__)
        else:
            self._partialIndex = None
            
    def _defaultLabel(self):
        """
        Intended for classes such as NurbsSurfaceRange which have multiple possible
        component labels (ie, u, v, uv), and we want to specify a 'default' one
        so that we can do NurbsSurfaceRange(myNurbsSurface).

        This should be None if either the component only has one label, or picking
        a default doesn't make sense (ie, in the case of Pivot, we have no
        idea whether the user would want the scale or rotate pivot, so
        doing Pivot(myObject) makes no sense...
        """
        return None

    def _completeNameString(self):
        # Note - most multi-dimensional components allow selection of all
        # components with only a single index - ie,
        #    myNurbsSurface.cv[*]
        # will work, even though nurbs cvs are double-indexed
        # However, some multi-indexed components WON'T work like this, ie
        #    myNurbsSurface.sf[*]
        # FAILS, and you MUST do:
        #    myNurbsSurface.sf[*][*]
        return (super(DimensionedComponent, self)._completeNameString() +
                 ('[*]' * self.dimensions))

    def _makeComponentHandle(self):
        indices = self.__apiobjects__.get('ComponentIndex', None)
        indices = self._standardizeIndices(indices)
        handle = self._makeIndexedComponentHandle(indices)
        return handle 

    def _makeIndexedComponentHandle(self, indices):
        """
        Returns an MObjectHandle that points to a maya component object with
        the given indices.
        """
        selList = api.MSelectionList()
        for index in indices:
            compName = Component._completeNameString(self)
            for dimNum, dimIndex in enumerate(index):
                if isinstance(dimIndex, (slice, HashableSlice)):
                    # by the time we're gotten here, standardizedIndices
                    # should have either flattened out slice-indices
                    # (DiscreteComponents) or disallowed slices with
                    # step values (ContinuousComponents)
                    if dimIndex.start == dimIndex.stop == None:
                        dimIndex = '*'
                    else:
                        if dimIndex.start is None:
                            if isinstance(self, DiscreteComponent):
                                start = 0
                            else:
                                partialIndex = ComponentIndex(('*',)*dimNum,
                                                              index.label) 
                                start = self._dimRange(partialIndex)[0]
                        else:
                            start = dimIndex.start
                        if dimIndex.stop is None:
                            partialIndex = ComponentIndex(('*',)*dimNum,
                                                          index.label) 
                            stop= self._dimRange(partialIndex)[1]
                        else:
                            stop = dimIndex.stop
                        dimIndex = "%s:%s" % (start, stop)
                compName += '[%s]' % dimIndex
            try:
                selList.add(compName)
            except RuntimeError:
                raise general.MayaComponentError(compName)
        compMobj = api.MObject()
        dagPath = api.MDagPath()
        selList.getDagPath(0, dagPath, compMobj)
        return api.MObjectHandle(compMobj)

    VALID_SINGLE_INDEX_TYPES = []  # re-define in derived!

    def _standardizeIndices(self, indexObjs, allowIterable=True, label=None):
        """
        Convert indexObjs to an iterable of ComponentIndex objects.
        
        indexObjs may be a member of VALID_SINGLE_INDEX_TYPES, a
        ComponentIndex object, or an iterable of such items (if allowIterable),
        or 'None'
        """
        if indexObjs is None:
            indexObjs = ComponentIndex(label=label)

        indices = set()
        # Convert single objects to a list
        if isinstance(indexObjs, self.VALID_SINGLE_INDEX_TYPES):
            if self.dimensions == 1:
                if isinstance(indexObjs, (slice, HashableSlice)):
                    return self._standardizeIndices(self._sliceToIndices(indexObjs), label=label)
                else:
                    indices.add(ComponentIndex((indexObjs,), label=label))
            else:
                raise IndexError("Single Index given for a multi-dimensional component")
        elif (isinstance(indexObjs, ComponentIndex) and
              all([isinstance(dimIndex, self.VALID_SINGLE_INDEX_TYPES) for dimIndex in indexObjs])):
            if label and indexObjs.label and label != indexObjs.label:
                raise IndexError('ComponentIndex object had a different label than desired (wanted %s, found %s)'
                                 % (label, indexObjs.label))
            indices.update(self._flattenIndex(indexObjs))
        elif isinstance(indexObjs, dict):
            # Dicts are used to specify component labels for a group of indices at once...
            for dictLabel, dictIndices in indexObjs.iteritems():
                if label and label != dictLabel:
                    raise IndexError('ComponentIndex object had a different label than desired (wanted %s, found %s)'
                                     % (label, dictLabel))
                indices.update(self._standardizeIndices(dictIndices, label=dictLabel))
        elif allowIterable and util.isIterable(indexObjs):
            for index in indexObjs:
                indices.update(self._standardizeIndices(index,
                                                        allowIterable=False,
                                                        label=label))
        else:
            raise IndexError("Invalid indices for component: %r" % (indexObjs,) )
        return tuple(indices)

    def _sliceToIndices(self, sliceObj):
        raise NotImplementedError
    
    def _flattenIndex(self, index, allowIterable=True):
        """
        Given a ComponentIndex object, which may be either a partial index (ie,
        len(index) < self.dimensions), or whose individual-dimension indices
        might be slices or iterables, return an flat list of ComponentIndex
        objects. 
        """
        # Some components - such as face-vertices - need to know the previous
        # indices to be able to fully expand the remaining indices... ie,
        # faceVertex[1][2][:] may result in a different expansion than for
        # faceVertex[3][8][:]...
        # for this reason, we need to supply the previous indices to 
        # _sliceToIndices, and expand on a per-partial-index basis
        while len(index) < self.dimensions:
            index = ComponentIndex(index + (HashableSlice(None),))
        
        indices = [ComponentIndex(label=index.label)]
        for dimIndex in index:
            if isinstance(dimIndex, (slice, HashableSlice)):
                newIndices = []
                for oldPartial in indices:
                    newIndices.extend(self._sliceToIndices(dimIndex,
                                                           partialIndex=oldPartial))
                indices = newIndices
            elif allowIterable and util.isIterable(dimIndex):
                newIndices = []
                for oldPartial in indices:
                    for indice in dimIndex:
                        newIndices.extend(self._flattenIndex(oldPartial + (indice,),
                                                             allowIterable=False))
                return newIndices
            else:
                indices = [x + (dimIndex,) for x in indices]
        return indices    

    def __getitem__(self, item):
        if self.currentDimension() is None:
            raise IndexError("Indexing only allowed on an incompletely "
                             "specified component (ie, 'cube.vtx')")         
        self._validateGetItemIndice(item)
        return self.__class__(self._node,
            ComponentIndex(self._partialIndex + (item,)))        

    def _validateGetItemIndice(self, item, allowIterables=True):
        """
        Will raise an appropriate IndexError if the given item
        is not suitable as a __getitem__ indice.
        """
        if allowIterables and util.isIterable(item):
            for x in item:
                self._validateGetItemIndice(item, allowIterables=False)
            return
        if not isinstance(item, self.VALID_SINGLE_INDEX_TYPES):
            raise IndexError("Invalid indice type for %s: %r" %
                             (self.__class__.__name__,
                              item.__class__.__name__) )
        if isinstance(item, (slice, HashableSlice)):
            # 'None' compares as less than all numbers, so need
            # to check for it explicitly
            if item.start is None and item.stop is None:
                # If it's an open range, [:], and slices are allowed,
                # it's valid
                return
            elif item.start is None:
                minIndex = maxIndex = item.stop
            elif item.stop is None:
                minIndex = maxIndex = item.start
            else:
                maxIndex = max(item.start, item.stop)
                minIndex = min(item.start, item.stop)
            if (not isinstance(maxIndex, self.VALID_SINGLE_INDEX_TYPES) or
                not isinstance(minIndex, self.VALID_SINGLE_INDEX_TYPES)):
                raise IndexError("Invalid slice start or stop value")
        else:
            maxIndex = minIndex = item
        allowedRange = self._dimRange(self._partialIndex)
        if minIndex < allowedRange[0] or maxIndex > allowedRange[1]:
            raise IndexError("Indice %s out of range %s" % (item, allowedRange))        

    def _dimRange(self, partialIndex):
        """
        Returns (minIndex, maxIndex) for the next dimension index after
        the given partialIndex.
        The range is inclusive.
        """
        raise NotImplemented

    def _dimLength(self, partialIndex):
        """
        Given a partialIndex, returns the maximum value for the first
         unspecified dimension.
        """
        # Implement in derived classes - no general way to determine the length
        # of components!
        raise NotImplementedError

    def currentDimension(self):
        """
        Returns the dimension index that an index operation - ie, self[...] /
        self.__getitem__(...) - will operate on.
        
        If the component is completely specified (ie, all dimensions are
        already indexed), then None is returned.
        """
        if not hasattr(self, '_currentDimension'):
            indices = self._partialIndex
            if (indices is not None and
                len(indices) < self.dimensions):
                self._currentDimension = len(indices)
            else:
                self._currentDimension = None
        return self._currentDimension

class ComponentIndex( tuple ):
    """
    Class used to specify a multi-dimensional component index.
    
    If the length of a ComponentIndex object < the number of dimensions,
    then the remaining dimensions are taken to be 'complete' (ie, have not yet
    had indices specified).
    """
    def __new__(cls, *args, **kwargs):
        """
        :Parameters:
        label : `string`
            Component label for this index.
            Useful for components whose 'mel name' may vary - ie, an isoparm
            may be specified as u, v, or uv.
        """
        label = kwargs.pop('label', None)
        self = tuple.__new__(cls, *args, **kwargs)
        if not label and args and isinstance(args[0], ComponentIndex) and args[0].label:
            self.label = args[0].label
        else:
            self.label = label
        return self
    
    def __add__(self, other):
        if isinstance(other, ComponentIndex) and other.label:
            if not self.label:
                label = other.label
            else:
                if other.label != self.label:
                    raise ValueError('cannot add two ComponentIndex objects with different labels')
                label = self.label
        else:
            label = self.label
        return ComponentIndex(itertools.chain(self, other), label=label)

def validComponentIndexType( argObj, allowDicts=True, componentIndexTypes=None):
    """
    True if argObj is of a suitable type for specifying a component's index.
    False otherwise.
    
    Dicts allow for components whose 'mel name' may vary - ie, a single
    isoparm component may have, u, v, or uv elements; or, a single pivot
    component may have scalePivot and rotatePivot elements.  The key of the
    dict would indicate the 'mel component name', and the value the actual
    indices.
    
    Thus:
       {'u':3, 'v':(4,5), 'uv':ComponentIndex((1,4)) }
    would represent single component that contained:
       .u[3]
       .v[4]
       .v[5]
       .uv[1][4]
       
    Derived classes should implement:
    _dimLength           
    """
    if not componentIndexTypes:
        componentIndexTypes = (int, long, float, slice, HashableSlice, ComponentIndex)
    
    if allowDicts and isinstance(argObj, dict):
        for key, value in argObj.iteritems():
            if not validComponentIndexType(value, allowDicts=False):
                return False
        return True
    else:
        if isinstance(argObj, componentIndexTypes):
            return True
        elif isinstance( argObj, (list,tuple) ) and len(argObj):
            for indice in argObj:
                if not isinstance(indice, componentIndexTypes):
                    return False
            else:
                return True
    return False

class DiscreteComponent( DimensionedComponent ):
    """
    Components whose dimensions are discretely indexed.
    
    Ie, there are a finite number of possible components, referenced by integer
    indices.
    
    Example: polyCube.vtx[38], f.cv[3][2]
    
    Derived classes should implement:
    _dimLength    
    """

    VALID_SINGLE_INDEX_TYPES = (int, long, slice, HashableSlice)
    
    def __init__(self, *args, **kwargs):
        self.reset()
        super(DiscreteComponent, self).__init__(*args, **kwargs)

    def _sliceToIndices(self, sliceObj, partialIndex=None):
        """
        Converts a slice object to an iterable of the indices it represents.
        
        If a partialIndex is supplied, then sliceObj is taken to be a slice
        at the next dimension not specified by partialIndex - ie,
        
        myFaceVertex._sliceToIndices(slice(1,-1), partialIndex=ComponentIndex((3,)))
        
        might be used to get a component such as
        
        faceVertices[3][1:-1]
        """
        
        if partialIndex is None:
            partialIndex = ComponentIndex()

        # store these in local variables, to avoid constantly making
        # new slice objects, since slice objects are immutable
        start = sliceObj.start
        stop = sliceObj.stop
        step = sliceObj.step
        
        if start is None:
            start = 0
            
        if step is None:
            step = 1

        # convert 'maya slices' to 'python slices'...
        # ie, in maya, someObj.vtx[2:3] would mean:
        #  (vertices[2], vertices[3])
        # in python, it would mean:
        #  (vertices[2],)        
        if stop is not None and stop >= 0:
            stop += 1
        
        if stop is None or start < 0 or stop < 0 or step < 0:
            start, stop, step = slice(start, stop, step).indices(self._dimLength(partialIndex))

        # Made this return a normal list for easier debugging...
        # ... can always make it back to a generator if need it for speed
        for rawIndex in xrange(start, stop, step):
            yield ComponentIndex(partialIndex + (rawIndex,))
#        return [ComponentIndex(partialIndex + (rawIndex,))
#                for rawIndex in xrange(start, stop, step)]
    
    def _makeIndexedComponentHandle(self, indices):
        # We could always create our component using the selection list
        # method; but since this has to do string processing, it is slower...
        # so use MFnComponent.addElements method if possible.
        handle = Component._makeComponentHandle(self)
        if self._componentMObjEmpty(handle.object()):
            mayaArrays = [] 
            for dimIndices in zip(*indices):
                mayaArrays.append(self._pyArrayToMayaArray(dimIndices))
            mfnComp = self._mfncompclass(handle.object())
            mfnComp.setComplete(False)
            mfnComp.addElements(*mayaArrays)
            return handle
        else:
            return super(DiscreteComponent, self)._makeIndexedComponentHandle(indices)

    @classmethod
    def _pyArrayToMayaArray(cls, pythonArray):
        mayaArray = api.MIntArray()
        api.MScriptUtil.createIntArrayFromList( list(pythonArray), mayaArray)
        return mayaArray
    
    def _dimRange(self, partialIndex):
        dimLen = self._dimLength(partialIndex)
        return (-dimLen, dimLen - 1)
    
    def __iter__(self):
        # We proceed in two ways, depending on whether we're a
        # completely-specified component (ie, no longer indexable),
        # or partially-specified (ie, still indexable).
        for compIndex in self._compIndexObjIter():
            yield self.__class__(self._node, compIndex)
            
    def _compIndexObjIter(self):
        """
        An iterator over all the indices contained by this component,
        as ComponentIndex objects (which are a subclass of tuple).
        """
        if self.currentDimension() is None:
            # we're completely specified, do flat iteration
            return self._flatIter()
        else:
            # we're incompletely specified, iterate across the dimensions!
            return self._dimensionIter()

    # Essentially identical to _compIndexObjIter, except that while
    # _compIndexObjIter, this is intended for use by end-user,
    # and so if it's more 'intuitive' to return some other object,
    # it will be overriden in derived classes to do so.
    # ie, for Component1D, this will return ints
    indicesIter = _compIndexObjIter

    def indices(self):
        """
        A list of all the indices contained by this component.
        """
        return list(self.indicesIter())

    def _dimensionIter(self):
        # If we're incompletely specified, then if, for instance, we're
        # iterating through all the vertices of a poly with 500,000 verts,
        # then it's a huge waste of time / space to create a list of
        # 500,000 indices in memory, then iterate through it, when we could
        # just as easily generate the indices as we go with an xrange
        # Since an MFnComponent is essentially a flat list of such indices
        # - only it's stored in maya's private memory space - we AVOID
        # calling __apicomponent__ in this case!
        
        # self._partialIndex may have slices...
        for index in self._flattenIndex(self._partialIndex):
            yield index
        
    def _flatIter(self):
        #If we're completely specified, we assume that we NEED
        # to have some sort of list of indicies just in order to know
        # what this component obejct holds (ie, we might have
        # [1][4], [3][80], [3][100], [4][10], etc)
        # ...so we assume that we're not losing any speed / memory
        # by iterating through a 'list of indices' stored in memory
        # in our case, this list of indices is the MFnComponent object
        # itself, and is stored in maya's memory, but the idea is the same... 

        # This code duplicates much of currentItem - keeping both
        # for speed, as _flatIter may potentially have to plow through a lot of
        # components, so we don't want to make an extra function call...

        dimensionIndicePtrs = []
        mfncomp = self.__apicomponent__()
        for i in xrange(self.dimensions):
            dimensionIndicePtrs.append(api.MScriptUtil().asIntPtr())
            
        for flatIndex in xrange(len(self)):
            mfncomp.getElement(flatIndex, *dimensionIndicePtrs)
            yield ComponentIndex(api.MScriptUtil.getInt(x) for x in dimensionIndicePtrs)

    def __len__(self):
        return self.__apicomponent__().elementCount()

    def count(self):
        return len(self)

    def setIndex(self, index):
        if not 0 <= index < len(self):
            raise IndexError
        self._currentFlatIndex = index
        return self
    
    def getIndex(self):
        return self._currentFlatIndex            
            
    def currentItem(self):
        # This code duplicates much of _flatIter - keeping both
        # for speed, as _flatIter may potentially have to plow through a lot of
        # components, so we don't want to make an extra function call...
        dimensionIndicePtrs = []
        mfncomp = self.__apicomponent__()
        for i in xrange(self.dimensions):
            dimensionIndicePtrs.append(api.MScriptUtil().asIntPtr())

        mfncomp.getElement(self._currentFlatIndex, *dimensionIndicePtrs)
        curIndex = ComponentIndex(api.MScriptUtil.getInt(x) for x in dimensionIndicePtrs)
        return self.__class__(self._node, curIndex)
            
    def next(self):
        if self._stopIteration:
            raise StopIteration
        elif not self:
            self._stopIteration = True
            raise StopIteration
        else:
            toReturn = self.currentItem()
            try:
                self.setIndex(self.getIndex() + 1)
            except IndexError:
                self._stopIteration = True
            return toReturn
    
    def reset(self):
        self._stopIteration = False
        self._currentFlatIndex = 0
        

class ContinuousComponent( DimensionedComponent ):
    """
    Components whose dimensions are continuous.
    
    Ie, there are an infinite number of possible components, referenced by
    floating point parameters.
    
    Example: nurbsCurve.u[7.48], nurbsSurface.uv[3.85][2.1]
    
    Derived classes should implement:
    _dimRange      
    """
    VALID_SINGLE_INDEX_TYPES = (int, long, float, slice, HashableSlice)
    
    def _standardizeIndices(self, indexObjs, **kwargs):
        return super(ContinuousComponent, self)._standardizeIndices(indexObjs,
                                                           allowIterable=False,
                                                           **kwargs)

    def _sliceToIndices(self, sliceObj, partialIndex=None):
        # Note that as opposed to a DiscreteComponent, where we
        # always want to flatten a slice into it's discrete elements,
        # with a ContinuousComponent a slice is a perfectly valid
        # indices... the only caveat is we need to convert it to a
        # HashableSlice, as we will be sticking it into a set...        
        if sliceObj.step != None:
            raise ComponentError("%ss may not use slice-indices with a 'step' -  bad slice: %s" %
                                 (self.__class__.__name__, sliceObj))
        if partialIndex is None:
            partialIndex = ComponentIndex()
        if sliceObj.start == sliceObj.stop == None:
            return (partialIndex + (HashableSlice(None), ), )
        else:
            return (partialIndex +
                    (HashableSlice(sliceObj.start, sliceObj.stop),), )

    def __iter__(self):
        raise TypeError("%r object is not iterable" % self.__class__.__name__)

    def _dimLength(self, partialIndex):
        # Note that in the default implementation, used
        # by DiscreteComponent, _dimRange depends on _dimLength.
        # In ContinuousComponent, the opposite is True - _dimLength
        # depends on _dimRange
        range = self._dimRange(partialIndex)
        return range[1] - range[0]
    
    def _dimRange(self, partialIndex):
        # Note that in the default implementation, used
        # by DiscreteComponent, _dimRange depends on _dimLength.
        # In ContinuousComponent, the opposite is True - _dimLength
        # depends on _dimRange
        raise NotImplementedError
            
class Component1DFloat( ContinuousComponent ):
    dimensions = 1

class Component2DFloat( ContinuousComponent ):
    dimensions = 2

class Component1D( DiscreteComponent ):
    _mfncompclass = api.MFnSingleIndexedComponent
    _apienum__ = api.MFn.kSingleIndexedComponent
    dimensions = 1
    
    def name(self):
        # this function produces a name that uses extended slice notation, such as vtx[10:40:2]
        melobj = self.__melobject__()
        if isinstance(melobj, basestring):
            return melobj
        else:
            compSlice = _sequenceToComponentSlice( self.indicesIter() )
            sliceStr = ','.join( [ _formatSlice(x) for x in compSlice ] )
            return self._completeNameString().replace( '*', sliceStr )

    def _flatIter(self):
        # for some reason, the command to get an element is 'element' for
        # 1D components, and 'getElement' for 2D/3D... so parent class's
        # _flatIter won't work!
        # Just as well, we get a more efficient iterator for 1D comps...
        mfncomp = self.__apicomponent__()
        for flatIndex in xrange(len(self)):
            yield ComponentIndex( (mfncomp.element(flatIndex),) )
            
    def currentItem(self):
        mfncomp = self.__apicomponent__()
        return self.__class__(self._node, mfncomp.element(self._currentFlatIndex))
    
    def indicesIter(self):
        """
        An iterator over all the indices contained by this component,
        as integers.
        """
        for compIndex in self._compIndexObjIter():
            yield compIndex[0]
            
class Component2D( DiscreteComponent ):
    _mfncompclass = api.MFnDoubleIndexedComponent
    _apienum__ = api.MFn.kDoubleIndexedComponent
    dimensions = 2
    
class Component3D( DiscreteComponent ):
    _mfncompclass = api.MFnTripleIndexedComponent
    _apienum__ = api.MFn.kTripleIndexedComponent
    dimensions = 3

# Mixin class for components which use MIt* objects for some functionality
class MItComponent( Component ):
    """
    Abstract base class for pymel components that can be accessed via iterators.
    
    (ie, `MeshEdge`, `MeshVertex`, and `MeshFace` can be wrapped around
    MItMeshEdge, etc)
    
    If deriving from this class, you should set __apicls__ to an appropriate
    MIt* type - ie, for MeshEdge, you would set __apicls__ = api.MItMeshEdge
    """
#
    def __init__(self, *args, **kwargs ):
        super(MItComponent, self).__init__(*args, **kwargs)
    
    def __apimit__(self, alwaysUnindexed=False):
        # Note - the iterator should NOT be stored, as if it gets out of date,
        # it can cause crashes - see, for instance, MItMeshEdge.geomChanged
        # Since we don't know how the user might end up using the components
        # we feed out, and it seems like asking for trouble to have them
        # keep track of when things such as geomChanged need to be called,
        # we simply never retain the MIt for long..
        if self._currentFlatIndex == 0 or alwaysUnindexed:
            return self.__apicls__( self.__apimdagpath__(), self.__apimobject__() )
        else:
            return self.__apicls__( self.__apimdagpath__(), self.currentItem().__apimobject__() )
    
    def __apimfn__(self):
        return self.__apimit__()
    
class MItComponent1D( MItComponent, Component1D ): pass

class Component1D64( DiscreteComponent ):
    if Component._hasUint64:
        _mfncompclass = api.MFnUint64SingleIndexedComponent
        _apienum__ = api.MFn.kUint64SingleIndexedComponent
        
    else:
        _mfncompclass = api.MFnComponent
        _apienum__ = api.MFn.kComponent

    if Component._hasUint64 and hasattr(api, 'MUint64'):
        # Note that currently the python api has zero support for MUint64's
        # This code is just here because I'm an optimist...
        @classmethod
        def _pyArrayToMayaArray(cls, pythonArray):
            mayaArray = api.MUint64Array(len(pythonArray))
            for i, value in enumerate(pythonArray):
                mayaArray.set(value, i)
            return mayaArray
    else:
        # Component indices aren't sequential, and without MUint64, the only
        # way to check if a given indice is valid is by trying to insert it
        # into an MSelectionList... since this is both potentially fairly
        # slow, for now just going to 'open up the gates' as far as
        # validation is concerned...
        _max32 = 2**32
        def _dimLength(self, partialIndex):
            return self._max32

        # The ContinuousComponent version works fine for us - just
        # make sure we grab the original function object, not the method
        # object, since we don't inherit from ContinuousComponent
        _sliceToIndices = ContinuousComponent._sliceToIndices.im_func

        # We're basically having to fall back on strings here, so revert 'back'
        # to the string implementation of various methods...
        _makeIndexedComponentHandle = DimensionedComponent._makeIndexedComponentHandle

        def __len__(self):
            if hasattr(self, '_storedLen'):
                return self._storedLen
            else:
                # subd MIt*'s have no .count(), and there is no appropriate
                # MFn, so count it using strings...
                melStrings = self.__melobject__()
                if util.isIterable(melStrings):
                    count = Component.numComponentsFromStrings(*melStrings)
                else:
                    count = Component.numComponentsFromStrings(melStrings)
                self._storedLen = count
                return count
            
        # The standard _flatIter relies on being able to use element/getElement
        # Since we can't use these, due to lack of MUint64, fall back on
        # string processing...
        _indicesRe = re.compile( r'\[((?:\d+(?::\d+)?)|\*)\]'*2 + '$' )
        def _flatIter(self):
            if not hasattr(self, '_fullIndices'):
                melobj = self.__melobject__()
                if isinstance(melobj, basestring):
                    melobj = [melobj]
                indices = [ self._indicesRe.search(x).groups() for x in melobj ]
                for i, indicePair in enumerate(indices):
                    processedPair = []
                    for dimIndice in indicePair:
                        if dimIndice == '*':
                            processedPair.append(HashableSlice(None))
                        elif ':' in dimIndice:
                            start, stop = dimIndice.split(':')
                            processedPair.append(HashableSlice(int(start),
                                                               int(stop)))
                        else:
                            processedPair.append(int(dimIndice))
                    indices[i] = ComponentIndex(processedPair)
                self._fullIndices = indices
            for fullIndex in self._fullIndices:
                for index in self._flattenIndex(fullIndex):
                    yield index
        
    # kUint64SingleIndexedComponent components have a bit of a dual-personality
    # - though internally represented as a single-indexed long-int, in almost
    # all of the "interface", they are displayed as double-indexed-ints:
    # ie, if you select a subd vertex, it might be displayed as
    #    mySubd.smp[256][4388]
    # Since the end user will mostly "see" the component as double-indexed,
    # the default pymel indexing will be double-indexed, so we set dimensions
    # to 2, and then hand correct cases where self.dimensions affects how
    # we're interacting with the kUint64SingleIndexedComponent
    dimensions = 2

## Specific Components...

## Pivot Components

class Pivot( Component ):
    _apienum__ = api.MFn.kPivotComponent
    _ComponentLabel__ = ("rotatePivot", "scalePivot") 
    
## Mesh Components

class MeshVertex( MItComponent1D ):
    __apicls__ = api.MItMeshVertex
    _ComponentLabel__ = "vtx"
    _apienum__ = api.MFn.kMeshVertComponent

    def _dimLength(self, partialIndex):
        return self.node().numVertices()
   
    def setColor(self,color):
        self.node().setVertexColor( color, self.getIndex() )

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @mayahook.deprecated("Use 'connectedEdges' instead.") 
    def toEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        return self.connectedEdges()

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @mayahook.deprecated("Use 'connectedFaces' instead.")
    def toFaces(self):
        """
        :rtype: `MeshFace` list
        """
        return self.connectedFaces()
    
    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) ) 
 
    def isConnectedTo(self, component):
        """
        pass a component of type `MeshVertex`, `MeshEdge`, `MeshFace`, with a single element
        
        :rtype: bool
        """
        if isinstance(component,MeshFace):
            return self.isConnectedToFace( component.getIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.getIndex() )
        if isinstance(component,MeshVertex):
            array = api.MIntArray()
            self.__apimfn__().getConnectedVertices(array)
            return component.getIndex() in [ array[i] for i in range( array.length() ) ]

        raise TypeError, 'type %s is not supported' % type(component)

class MeshEdge( MItComponent1D ):
    __apicls__ = api.MItMeshEdge
    _ComponentLabel__ = "e"
    _apienum__ = api.MFn.kMeshEdgeComponent
    
    def _dimLength(self, partialIndex):
        return self.node().numEdges()


    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @mayahook.deprecated("Use 'connectedFaces' instead.")
    def toFaces(self):
        """
        :rtype: `MeshFace` list
        """
        return self.connectedFaces()

    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        
        index0 = self.__apimfn__().index(0)
        index1 = self.__apimfn__().index(1)
        return ( MeshVertex(self,index0), MeshVertex(self,index1) )

    def isConnectedTo(self, component):
        """
        :rtype: bool
        """
        if isinstance(component,MeshFace):
            return self.isConnectedToFace( component.getIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.getIndex() )
        if isinstance(component,MeshVertex):
            index0 = self.__apimfn__().index(0)
            index1 = self.__apimfn__().index(1)
            return component.getIndex() in [index0, index1]

        raise TypeError, 'type %s is not supported' % type(component)
  
class MeshFace( MItComponent1D ):
    __apicls__ = api.MItMeshPolygon
    _ComponentLabel__ = "f"
    _apienum__ = api.MFn.kMeshPolygonComponent

    def _dimLength(self, partialIndex):
        return self.node().numFaces()

       

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @mayahook.deprecated("Use 'connectedEdges' instead.") 
    def toEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @mayahook.deprecated("Use 'connectedVertices' instead.")
    def toVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) ) 
    
    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, _sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) ) 

    def isConnectedTo(self, component):
        """
        :rtype: bool
        """
        if isinstance(component,MeshFace):
            return self.isConnectedToFace( component.getIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.getIndex() )
        if isinstance(component,MeshVertex):
            return self.isConnectedToVertex( component.getIndex() )

        raise TypeError, 'type %s is not supported' % type(component)

class MeshUV( Component1D ):
    _ComponentLabel__ = "map"
    _apienum__ = api.MFn.kMeshMapComponent

    def _dimLength(self, partialIndex):
        return self._node.numUVs()
    
class MeshVertexFace( Component2D ):
    _ComponentLabel__ = "vtxFace"
    _apienum__ = api.MFn.kMeshVtxFaceComponent
    
    def _dimLength(self, partialIndex):
        if len(partialIndex) == 0:
            return self._node.numVertices()
        elif len(partialIndex) == 1:
            return self._node.vtx[partialIndex[0]].numConnectedFaces()
        
    def _sliceToIndices(self, sliceObj, partialIndex=None):
        if not partialIndex:
            # If we're just grabbing a slice of the first index,
            # the verts, we can proceed as normal...
            for x in super(MeshVertexFace, self)._sliceToIndices(sliceObj, partialIndex):
                yield x
                
        # If we're iterating over the FACES attached to a given vertex,
        # which may be a random set - say, (3,6,187) - not clear how to
        # interpret an index 'range'
        else:
            if (sliceObj.start not in (0, None) or
                sliceObj.stop is not None or
                sliceObj.step is not None):
                raise ValueError('%s objects may not be indexed with slices, execpt for [:]' %
                                 self.__class__.__name__)
    
            # get a MitMeshVertex ...
            mIt = api.MItMeshVertex(self._node.__apimdagpath__())
            mIt.setIndex(partialIndex[0], api.MScriptUtil().asIntPtr())
            intArray = api.MIntArray()
            mIt.getConnectedFaces(intArray)
            for i in xrange(intArray.length()):
                yield partialIndex + (intArray[i],)
                
    def _validateGetItemIndice(self, item, allowIterables=True):
        """
        Will raise an appropriate IndexError if the given item
        is not suitable as a __getitem__ indice.
        """
        if len(self._partialIndex) == 0:
            return super(MeshVertexFace, self)._validateGetItemIndice(item)
        if allowIterables and util.isIterable(item):
            for x in item:
                self._validateGetItemIndice(item, allowIterables=False)
            return
        if isinstance(item, (slice, HashableSlice)):
            if slice.start == slice.stop == slice.step == None:
                return
            raise IndexError("only completely open-ended slices are allowable"\
                             " for the second indice of %s objects" %
                             self.__class__.__name__)
        if not isinstance(item, self.VALID_SINGLE_INDEX_TYPES):
            raise IndexError("Invalid indice type for %s: %r" %
                             (self.__class__.__name__,
                              item.__class__.__name__) )
        
        for fullIndice in self._sliceToIndices(slice(None),
                                               partialIndex=self._partialIndex):
            if item == fullIndice[1]:
                return
        raise IndexError("vertex-face %s-%s does not exist" %
                         (self._partialIndex[0], item))
    
## Subd Components    

class SubdVertex( Component1D64 ):
    _ComponentLabel__ = "smp"
    _apienum__ = api.MFn.kSubdivCVComponent

class SubdEdge( Component1D64 ):
    _ComponentLabel__ = "sme"
    _apienum__ = api.MFn.kSubdivEdgeComponent
    
class SubdFace( Component1D64 ):
    _ComponentLabel__ = "smf"
    _apienum__ = api.MFn.kSubdivFaceComponent

class SubdUV( Component1D ):
    _ComponentLabel__ = "smm"
    _apienum__ = api.MFn.kSubdivMapComponent
    
    # This implementation failed because
    # it appears that you can have a subd shape
    # with no uvSet elements
    # (shape.uvSet.evaluateNumElements() == 0)
    # but with valid .smm's
#    def _dimLength(self, partialIndex):
#        # My limited tests reveal that
#        # subds with multiple uv sets
#        # mostly just crash a lot
#        # However, when not crashing, it
#        # SEEMS that you can select
#        # a .smm[x] up to the size
#        # of the largest possible uv
#        # set, regardless of which uv
#        # set is current...
#        max = 0
#        for elemPlug in self._node.attr('uvSet'):
#            numElements = elemPlug.evaluateNumElements()
#            if numElements > max:
#                max = numElements
#        # For some reason, if there are 206 elements
#        # in the uvSet, the max indexable smm's go from
#        # .smm[0] to .smm[206] - ie, num elements + 1...?
#        return max + 1

    _MAX_INDEX = 2 ** util.interpreterBits() - 1
    _tempSel = api.MSelectionList()
    _maxIndexRe = re.compile(r'\[0:([0-9]+)\]$')
    def _dimLength(self, partialIndex):
        # Fall back on good ol' string processing...
        self._tempSel.clear()
        self._tempSel.add(Component._completeNameString(self) +
                          '[0:%d]' % self._MAX_INDEX)
        selStrings = []
        self._tempSel.getSelectionStrings(0, selStrings)
        try:
            # remember the + 1 for the 0'th index
            return int(self._maxIndexRe.search(selStrings[0]).group(1)) + 1
        except AttributeError:
            raise RuntimeError("Couldn't determine max index for %s" %
                               Component._completeNameString(self))

    # SubdUV's don't work with .smm[*] - so need to use
    # explicit range instead - ie, .smm[0:206]
    def _completeNameString(self):
        # Note - most multi-dimensional components allow selection of all
        # components with only a single index - ie,
        #    myNurbsSurface.cv[*]
        # will work, even though nurbs cvs are double-indexed
        # However, some multi-indexed components WON'T work like this, ie
        #    myNurbsSurface.sf[*]
        # FAILS, and you MUST do:
        #    myNurbsSurface.sf[*][*]
        return (super(DimensionedComponent, self)._completeNameString() +
                 ('[:%d]' % self._dimLength(None) ))

## Nurbs Curve Components

class NurbsCurveParameter( Component1DFloat ):
    _ComponentLabel__ = "u"
    _apienum__ = api.MFn.kCurveParamComponent
    
    def _dimRange(self, partialIndex):
        return self._node.getKnotDomain()

class NurbsCurveCV( MItComponent1D ):
    __apicls__ = api.MItCurveCV
    _ComponentLabel__ = "cv"
    _apienum__ = api.MFn.kCurveCVComponent
    
    def _dimLength(self, partialIndex):
        return self.node().numCVs()
    
class NurbsCurveEP( Component1D ):
    _ComponentLabel__ = "ep"
    _apienum__ = api.MFn.kCurveEPComponent

    def _dimLength(self, partialIndex):
        return self.node().numEPs()
        
class NurbsCurveKnot( Component1D ):
    _ComponentLabel__ = "knot"
    _apienum__ = api.MFn.kCurveKnotComponent

    def _dimLength(self, partialIndex):
        return self.node().numKnots()
    
## NurbsSurface Components

class NurbsSurfaceIsoparm( Component2DFloat ):
    _apienum__ = api.MFn.kIsoparmComponent
    _ComponentLabel__ = ("u", "v", "uv")
    
    def __init__(self, *args, **kwargs):
        super(NurbsSurfaceIsoparm, self).__init__(*args, **kwargs)
        # Fix the bug where running:
        # 
        # import maya.cmds as cmds
        # cmds.sphere()
        # cmds.select('nurbsSphere1.uv[*][*]')
        # print cmds.ls(sl=1)
        # cmds.select('nurbsSphere1.u[*][*]')
        # print cmds.ls(sl=1)
        # 
        # Gives two different results:
        # [u'nurbsSphere1.u[0:4][0:1]']
        # [u'nurbsSphere1.u[0:4][0:8]']
        
        # to fix this, change 'uv' comps to 'u' comps
        if hasattr(self, '_partialIndex'):
            self._partialIndex = self._convertUVtoU(self._partialIndex)
        if 'ComponentIndex' in self.__apiobjects__:
            self.__apiobjects__['ComponentIndex'] = self._convertUVtoU(self.__apiobjects__['ComponentIndex'])
        if hasattr(self, '_indices'):
            self._indices = self._convertUVtoU(self._indices)
        self._ComponentLabel__ = self._convertUVtoU(self._ComponentLabel__)

    @classmethod
    def _convertUVtoU(cls, index):
        if isinstance(index, dict):
            if 'uv' in index:
                # convert over index['uv']
                oldUvIndex = cls._convertUVtoU(index['uv'])
                if 'u' in index:
                    # First, make sure index['u'] is a list
                    if (isinstance(index['u'], ComponentIndex) or
                        not isinstance(index['u'], (list, tuple))):
                        index['u'] = [index['u']]
                    elif isinstance(index['u'], tuple):
                        index['u'] = list(index['u'])
                    
                    # then add on 'uv' contents
                    if (isinstance(oldUvIndex, ComponentIndex) or
                        not isinstance(oldUvIndex, (list, tuple))):
                        index['u'].append(oldUvIndex)
                    else:
                        index['u'].extend(oldUvIndex)
                else:
                    index['u'] = oldUvIndex
                del index['uv']
        elif isinstance(index, ComponentIndex):
            # do this check INSIDE here, because, since a ComponentIndex is a tuple,
            # we don't want to change a ComponentIndex object with a 'v' index
            # into a list in the next elif clause!
            if index.label == 'uv':
                index.label = 'u'
        elif isinstance(index, (list, tuple)) and not isinstance(index, ComponentIndex):
            index = [cls._convertUVtoU(x) for x in index]
        elif isinstance(index, basestring):
            if index == 'uv':
                index = 'u'
        return index
    
    def _defaultLabel(self):
        return 'u'

    def _dimRange(self, partialIndex):
        minU, maxU, minV, maxV = self._node.getKnotDomain()
        if len(partialIndex) == 0:
            if partialIndex.label == 'v':
                param = 'v'
            else:
                param = 'u'
        else:
            if partialIndex.label == 'v':
                param = 'u'
            else:
                param = 'v'
        if param == 'u':
            return minU, maxU
        else:
            return minV, maxV
    
class NurbsSurfaceRange( NurbsSurfaceIsoparm ):
    _ComponentLabel__ = ("u", "v", "uv")
    _apienum__ = api.MFn.kSurfaceRangeComponent
    
    def __getitem__(self, item):
        if self.currentDimension() is None:
            raise IndexError("Indexing only allowed on an incompletely "
                             "specified component")
        self._validateGetItemIndice(item)            
        # You only get a NurbsSurfaceRange if BOTH indices are slices - if
        # either is a single value, you get an isoparm
        if (not isinstance(item, (slice, HashableSlice)) or
              (self.currentDimension() == 1 and
               not isinstance(self._partialIndex[0], (slice, HashableSlice)))):
            return NurbsSurfaceIsoparm(self._node, self._partialIndex + (item,))
        else:
            return super(NurbsSurfaceRange, self).__getitem__(item)    

class NurbsSurfaceCV( Component2D ):
    _ComponentLabel__ = "cv"
    _apienum__ = api.MFn.kSurfaceCVComponent

    def _dimLength(self, partialIndex):
        if len(partialIndex) == 0:
            return self.node().numCVsInU()
        elif len(partialIndex) == 1:
            return self.node().numCVsInV()
        else:
            raise ValueError('partialIndex %r too long for %s._dimLength' %
                             (partialIndex, self.__class__.__name__))
        
class NurbsSurfaceEP( Component2D ):
    _ComponentLabel__ = "ep"
    _apienum__ = api.MFn.kSurfaceEPComponent

    def _dimLength(self, partialIndex):
        if len(partialIndex) == 0:
            return self.node().numEPsInU()
        elif len(partialIndex) == 1:
            return self.node().numEPsInV()
        else:
            raise ValueError('partialIndex %r too long for %s._dimLength' %
                             (partialIndex, self.__class__.__name__))
            
class NurbsSurfaceKnot( Component2D ):
    _ComponentLabel__ = "knot"
    _apienum__ = api.MFn.kSurfaceKnotComponent

    def _dimLength(self, partialIndex):
        if len(partialIndex) == 0:
            return self.node().numKnotsInU()
        elif len(partialIndex) == 1:
            return self.node().numKnotsInV()
        else:
            raise ValueError('partialIndex %r too long for %s._dimLength' %
                             (partialIndex, self.__class__.__name__))
            
class NurbsSurfaceFace( Component2D ):
    _ComponentLabel__ = "sf"
    _apienum__ = api.MFn.kSurfaceFaceComponent

    def _dimLength(self, partialIndex):
        if len(partialIndex) == 0:
            return self.node().numSpansInU()
        elif len(partialIndex) == 1:
            return self.node().numSpansInV()
        else:
            raise IndexError("partialIndex %r for %s must have length <= 1" %
                             (partialIndex, self.__class__.__name__))
        
## Lattice Components

class LatticePoint( Component3D ):
    _ComponentLabel__ = "pt"
    _apienum__ = api.MFn.kLatticeComponent
    
    def _dimLength(self, partialIndex):
        if len(partialIndex) > 2:
            raise ValueError('partialIndex %r too long for %s._dimLength' %
                             (partialIndex, self.__class__.__name__))    
        return self.node().getDivisions()[len(partialIndex)]

class ComponentArray(object):
    def __init__(self, name):
        self._name = name
        self._iterIndex = 0
        self._node = self.node()
        
    def __str__(self):
        return self._name
        
    def __repr__(self):
        return "ComponentArray(u'%s')" % self
    
    #def __len__(self):
    #    return 0
        
    def __iter__(self):
#        """iterator for multi-attributes
#        
#            >>> for attr in SCENE.persp.attrInfo(multi=1)[0]: 
#            ...     print attr
#            
#        """
        return self
                
    def next(self):
#        """iterator for multi-attributes
#        
#            >>> for attr in SCENE.persp.attrInfo(multi=1)[0]: 
#            ...    print attr
#            
#        """
        if self._iterIndex >= len(self):
            raise StopIteration
        else:                        
            new = self[ self._iterIndex ]
            self._iterIndex += 1
            return new
            
    def __getitem__(self, item):
        
        def formatSlice(item):
            step = item.step
            if step is not None:
                return '%s:%s:%s' % ( item.start, item.stop, step) 
            else:
                return '%s:%s' % ( item.start, item.stop ) 
        
 
#        if isinstance( item, tuple ):            
#            return [ Component(u'%s[%s]' % (self, formatSlice(x)) ) for x in  item ]
#            
#        elif isinstance( item, slice ):
#            return Component(u'%s[%s]' % (self, formatSlice(item) ) )
#
#        else:
#            return Component(u'%s[%s]' % (self, item) )

        if isinstance( item, tuple ):            
            return [ self.returnClass( self._node, formatSlice(x) ) for x in  item ]
            
        elif isinstance( item, (slice, HashableSlice) ):
            return self.returnClass( self._node, formatSlice(item) )

        else:
            return self.returnClass( self._node, item )


    def plugNode(self):
        'plugNode'
        return general.PyNode( str(self).split('.')[0])
                
    def plugAttr(self):
        """plugAttr"""
        return '.'.join(str(self).split('.')[1:])

    node = plugNode
                
class _Component(object):
    """
    Abstract base class for component types like vertices, edges, and faces.
    
    This class is deprecated.
    """
    def __init__(self, node, item):
        self._item = item
        self._node = node
                
    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self)
        
    def node(self):
        'plugNode'
        return self._node
    
    def item(self):
        return self._item    
        
    def move( self, *args, **kwargs ):
        return general.move( self, *args, **kwargs )
    def scale( self, *args, **kwargs ):
        return general.scale( self, *args, **kwargs )    
    def rotate( self, *args, **kwargs ):
        return general.rotate( self, *args, **kwargs )

class AttributeDefaults(general.PyNode):
    __metaclass__ = _factories.MetaMayaTypeWrapper
    __apicls__ = api.MFnAttribute
    
    def __apiobject__(self) :
        "Return the default API object for this attribute, if it is valid"
        return self.__apimobject__()
    
    def __apimobject__(self):
        "Return the MObject for this attribute, if it is valid"
        try:
            handle = self.__apiobjects__['MObjectHandle']
        except:
            handle = self.__apiobjects__['MPlug'].attribute()
            self.__apiobjects__['MObjectHandle'] = handle
        if api.isValidMObjectHandle( handle ):
            return handle.object()

        raise general.MayaAttributeError
    
    def __apimplug__(self) :
        "Return the MPlug for this attribute, if it is valid"
        # check validity
        #self.__apimobject__()
        return self.__apiobjects__['MPlug']

    def __apimdagpath__(self) :
        "Return the MDagPath for the node of this attribute, if it is valid"
        try:
            return self.node().__apimdagpath__()
        except AttributeError: pass
                 
class Attribute(general.PyNode):
    """
    
    """
    
    #
    
    
    """
    Attributes
    ==========
    
    The Attribute class is your one-stop shop for all attribute related functions. Those of us who have spent time using MEL
    have become familiar with all the many commands for operating on attributes.  This class gathers them all into one
    place. If you forget or are unsure of the right method name, just ask for help by typing `help(Attribute)`.  
    
    For the most part, the names of the class equivalents to the maya.cmds functions follow a fairly simple pattern:
    `setAttr` becomes `Attribute.set`, `getAttr` becomes `Attribute.get`, `connectAttr` becomes `Attribute.connect` and so on.  
    Here's a simple example showing how the Attribute class is used in context.
    
        >>> from pymel.all import *
        >>> cam = general.PyNode('persp')
        >>> if cam.visibility.isKeyable() and not cam.visibility.isLocked():
        ...     cam.visibility.set( True )
        ...     cam.visibility.lock()
        ... 
        >>> print cam.v.type()      # shortnames also work    
        bool
    
    Accessing Attributes
    --------------------
    
    You can access an attribute class in three ways.  The first two require that you already have a `general.PyNode` object.
    
    Shorthand
    ~~~~~~~~~
    
    The shorthand method is the most visually appealing and readable -- you simply access the maya attribute as a normal python attribute --
    but it has one major drawback: **if the attribute that you wish to acess has the same name as one of the attributes or methods of the 
    python class then it will fail**. 

        >>> cam  # continue from where we left off above
        Transform(u'persp')
        >>> cam.visibility # long name access
        Attribute(u'persp.visibility')
        >>> cam.v # short name access
        Attribute(u'persp.visibility')
        
    Keep in mind, that regardless of whether you use the long or short name of the attribute, you are accessing the same underlying API object.
    If you need the attribute formatted as a string in a particular way, use `Attribute.name`, `Attribute.longName`, `Attribute.shortName`,
    `Attribute.plugAttr`, or `Attribute.lastPlugAttr`.

    
    attr Method
    ~~~~~~~~~~~
    The attr method is the safest way to access an attribute, and can even be used to access attributes that conflict with 
    python methods, which would fail using shorthand syntax. This method is passed a string which
    is the name of the attribute to be accessed. 
        
        >>> cam.attr('visibility')
        Attribute(u'persp.visibility')
    
    Unlike the shorthand syntax, this method is capable of being passed attributes which are passed in as variables:        
        
        >>> for axis in ['scaleX', 'scaleY', 'scaleZ']: 
        ...     cam.attr( axis ).lock()          
    
    Direct Instantiation
    ~~~~~~~~~~~~~~~~~~~~
    The last way of getting an attribute is by directly instantiating the class. You can pass the attribute name as a string, or if you have one handy,
    pass in an api MPlug object.  If you don't know whether the string name represents a node or an attribute, you can always instantiate via the `general.PyNode`
    class, which will determine the appropriate class automaticallly.
    
    explicitly request an Attribute:
    
        >>> Attribute( 'persp.visibility' ) 
        Attribute(u'persp.visibility')
        
    let general.PyNode figure it out for you:
    
        >>> general.PyNode( 'persp.translate' ) 
        Attribute(u'persp.translate')
    

    Setting Attributes Values
    -------------------------
    
    To set the value of an attribute, you use the `Attribute.set` method.
    
        >>> cam.translateX.set(0)
        
    to set an attribute that expects a double3, you can use any iterable with 3 elements:
    
        >>> cam.translate.set([4,5,6])
        >>> cam.translate.set(datatypes.Vector([4,5,6]))

    Getting Attribute Values
    ------------------------
    To get the value of an attribute, you use the `Attribute.get` method. Keep in mind that, where applicable, the values returned will 
    be cast to pymel classes. This example shows that rotation (along with translation and scale) will be returned as a `Vector`.
    
        >>> t = cam.translate.get()
        >>> print t
        [4.0, 5.0, 6.0]
        >>> # translation is returned as a vector class
        >>> print type(t) 
        <class 'pymel.core.datatypes.Vector'>
        
    `set` is flexible in the types that it will accept, but `get` will always return the same type 
    for a given attribute. This can be a potential source of confusion:
        
        >>> value = [4,5,6]
        >>> cam.translate.set(value)
        >>> result = cam.translate.get()
        >>> value == result
        False
        >>> # why is this? because result is a Vector and value is a list
        >>> # use `Vector.isEquivalent` or cast the list to a `Vector`
        >>> result == datatypes.Vector(value)
        True
        >>> result.isEquivalent(value)
        True
    
    Connecting Attributes
    ---------------------
    As you might expect, connecting and disconnecting attributes is pretty straightforward.
                
        >>> cam.rotateX.connect( cam.rotateY )
        >>> cam.rotateX.disconnect( cam.rotateY )
    
    there are also handy operators for connection (`Attribute.__rshift__`) and disconnection (`Attribute.__floordiv__`)

        >>> c = polyCube(name='testCube')[0]        
        >>> cam.tx >> c.tx    # connect
        >>> cam.tx.outputs()
        [Transform(u'testCube')]
        >>> cam.tx // c.tx    # disconnect
        >>> cam.tx.outputs()
        []
            

    """
    __metaclass__ = _factories.MetaMayaTypeWrapper
    __apicls__ = api.MPlug
    attrItemReg = re.compile( '\[(\d+)\]$')
    
#    def __init__(self, *args, **kwargs ):
#        self.apicls.__init__(self, self._apiobject )
    
    def __apiobject__(self) :
        "Return the default API object (MPlug) for this attribute, if it is valid"
        return self.__apimplug__()
    
    def __apimobject__(self):
        "Return the MObject for this attribute, if it is valid"
        try:
            handle = self.__apiobjects__['MObjectHandle']
        except:
            handle = api.MObjectHandle( self.__apiobjects__['MPlug'].attribute() )
            self.__apiobjects__['MObjectHandle'] = handle
        if api.isValidMObjectHandle( handle ):
            return handle.object()

        raise general.MayaAttributeError
    
    def __apimplug__(self) :
        "Return the MPlug for this attribute, if it is valid"
        # check validity
        #self.__apimobject__()
        return self.__apiobjects__['MPlug']

    def __apimdagpath__(self) :
        "Return the MDagPath for the node of this attribute, if it is valid"
        try:
            return self.node().__apimdagpath__()
        except AttributeError: pass
    
                               
#    def __init__(self, attrName):
#        assert isinstance( api.__apiobject__(), api.MPlug )
        
#        if '.' not in attrName:
#            raise TypeError, "%s: Attributes must include the node and the attribute. e.g. 'nodeName.attributeName' " % self
#        self._name = attrName
#        # TODO : MObject support
#        self.__dict__['_multiattrIndex'] = 0
#        

    __getitem__ = _factories.wrapApiMethod( api.MPlug, 'elementByLogicalIndex', '__getitem__' )
    #elementByPhysicalIndex = _factories.wrapApiMethod( api.MPlug, 'elementByPhysicalIndex' )
    
    def attr(self, attr):
        """
        :rtype: `Attribute`
        """
        node = self.node()
        try:
            plug = self.__apimplug__()
            # if this plug is an array we can't properly get the child plug
            if plug.isArray():
                return node.attr(attr)
            else:
                attrObj = node.__apimfn__().attribute(attr)
                return Attribute( node, plug.child( attrObj ) )
        except RuntimeError:
            # raise our own MayaAttributeError, which subclasses AttributeError and MayaObjectError
            raise general.MayaAttributeError( '%s.%s' % (self, attr) )
    
    
    def __getattr__(self, attr):
        try:
            return self.attr(attr)
        except general.MayaAttributeError, e:
            raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
    # Added the __call__ so to generate a more appropriate exception when a class method is not found 
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" % (repr(self.node()), self.plugAttr()))
    
    
    def __iter__(self):
        """
        iterator for multi-attributes
        
            >>> from pymel.all import *
            >>> f=newFile(f=1) #start clean
            >>> 
            >>> at = general.PyNode( 'defaultLightSet.dagSetMembers' )
            >>> SpotLight()
            SpotLight(u'spotLightShape1')
            >>> SpotLight()
            SpotLight(u'spotLightShape2')
            >>> SpotLight()
            SpotLight(u'spotLightShape3')
            >>> for x in at: print x
            ... 
            defaultLightSet.dagSetMembers[0]
            defaultLightSet.dagSetMembers[1]
            defaultLightSet.dagSetMembers[2]
        """
        if self.isMulti():
            return self
            #return self[0]
        else:
            raise TypeError, "%s is not a multi-attribute and cannot be iterated over" % self
            
    def next(self):
        """
        iterator for multi-attributes.  Iterates over the sparse array, so if an idex has not been set
        or connected, it will be skipped.
        """
#        index = self.index()
#        size = self.size()
        try:
            index = self.__dict__['_iterIndex']
            size, indices = self.__dict__['_iterIndices']
            
        except KeyError:
            #size = self.size()
            try:
                size, indices = self._getArrayIndices()
            except RuntimeError:
                raise TypeError, "%s is not a multi-attribute and cannot be iterated over" % self
            index = 0
            self.__dict__['_iterIndices'] = size, indices

        if index >= size:
            self.__dict__.pop('_iterIndex', None)
            self.__dict__.pop('_iterIndices', None)
            raise StopIteration

        else:
            self.__dict__['_iterIndex'] = index+1
            return self[indices[index]]
        
    def __str__(self):
        """
        :rtype: `str`
        """
        return str(self.name())

    def __unicode__(self):
        """
        :rtype: `unicode`
        """
        return self.name()

    def __eq__(self, other):
        """
        :rtype: `bool`
        """
        thisPlug = self.__apimplug__()
        try:
            thisIndex = thisPlug.logicalIndex()
        except RuntimeError:
            thisIndex = None
            
        if not isinstance(other,Attribute):
            try:
                other = general.PyNode(other)
                if not hasattr(other, '__apimplug__'):
                    return False
            except (ValueError,TypeError): # could not cast to general.PyNode
                return False
            
        otherPlug = other.__apimplug__()
        # foo.bar[10] and foo.bar[20] and foo.bar eval to the same object in api.  i don't think this is very intuitive.
        try:
            otherIndex = otherPlug.logicalIndex()
        except RuntimeError:
            otherIndex = None  
        return thisPlug == otherPlug and thisIndex == otherIndex

    def __hash__(self):
        """
        :rtype: `int`
        """
        return (self.plugNode(), self.name(includeNode=False) ).__hash__()
        
    def __ne__(self, other):
        """
        :rtype: `bool`
        """
        return not self.__eq__(other)
           
    def name(self, includeNode=True, longName=True, fullAttrPath=False, fullDagPath=False):
        """ Returns the name of the attribute (plug)
        
        :rtype: `unicode`
        """
        obj = self.__apimplug__()
        if obj:
            name = ''
            node = self.plugNode()
            if includeNode:
                if isinstance(node, DagNode):
                    name = node.name(fullDagPath)
                else:
                    name = node.name()
                name += '.'
         
            
            return name + obj.partialName(    False, #includeNodeName
                                              True, #includeNonMandatoryIndices
                                              True, #includeInstancedIndices
                                              False, #useAlias
                                              fullAttrPath, #useFullAttributePath
                                              longName #useLongNames 
                                            )
        raise general.MayaObjectError(self._name)
    
    
#    def attributeName(self):
#        pass
#    
#    def attributeNames(self):
#        pass
      
    
    def plugNode(self):
        """plugNode
        
        :rtype: `DependNode`
        """
        return self._node
    
    node = plugNode
                
    def plugAttr(self, longName=False, fullPath=False):
        """
            >>> from pymel.all import *
            >>> at = SCENE.persp.t.tx
            >>> at.plugAttr(longName=False, fullPath=False)
            u'tx'
            >>> at.plugAttr(longName=False, fullPath=True)
            u't.tx'
            >>> at.plugAttr(longName=True, fullPath=True)
            u'translate.translateX'
        
        :rtype: `unicode`
        """
        return self.name(includeNode=False,
                         longName=longName,
                         fullAttrPath=fullPath)
        
    
    def lastPlugAttr(self, longName=False):
        """
            >>> from pymel.all import *
            >>> at = SCENE.persp.t.tx
            >>> at.lastPlugAttr(longName=False)
            u'tx'
            >>> at.lastPlugAttr(longName=True)
            u'translateX'
        
        :rtype: `unicode`
        """
        return self.name(includeNode=False,
                         longName=longName,
                         fullAttrPath=False)

    
    def longName(self, fullPath=False ):
        """
            >>> from pymel.all import *
            >>> at = SCENE.persp.t.tx
            >>> at.longName(fullPath=False)
            u'translateX'
            >>> at.longName(fullPath=True)
            u'translate.translateX'
        
        :rtype: `unicode`
        """
        return self.name(includeNode=False,
                         longName=True,
                         fullAttrPath=fullPath)
        
    def shortName(self, fullPath=False):
        """
            >>> from pymel.all import *
            >>> at = SCENE.persp.t.tx
            >>> at.shortName(fullPath=False)
            u'tx'
            >>> at.shortName(fullPath=True)
            u't.tx'
        
        :rtype: `unicode`
        """
        return self.name(includeNode=False,
                         longName=False,
                         fullAttrPath=fullPath)
        
    def nodeName( self ):
        """The node part of this plug as a string
        
        :rtype: `unicode`
        """
        return self.plugNode().name()

       
    def array(self):
        """
        Returns the array (multi) attribute of the current element:
        
            >>> n = Attribute(u'initialShadingGroup.groupNodes[0]')
            >>> n.isElement()
            True
            >>> n.array()
            Attribute(u'initialShadingGroup.groupNodes')

        This method will raise an error for attributes which are not elements of
        an array:
            
            >>> m = Attribute(u'initialShadingGroup.groupNodes')
            >>> m.isElement()
            False
            >>> m.array()
            Traceback (most recent call last):
            ...
            TypeError: initialShadingGroup.groupNodes is not an array (multi) attribute
            
        :rtype: `Attribute`
        """
        try:
            return Attribute( self._node, self.__apimplug__().array() )
            #att = Attribute(Attribute.attrItemReg.split( self )[0])
            #if att.isMulti() :
            #    return att
            #else :
            #    raise TypeError, "%s is not a multi attribute" % self
        except:
            raise TypeError, "%s is not an array (multi) attribute" % self


    # TODO : do not list all children elements by default, allow to do 
    #        skinCluster1.weightList.elements() for first level elements weightList[x]
    #        or skinCluster1.weightList.weights.elements() for all weightList[x].weights[y]

    def elements(self):
        """
        ``listAttr -multi``
        
        Return a list of strings representing all the attributes in the array.
        
        If you don't need actual strings, it is recommended that you simply iterate through the elements in the array.
        See `Attribute.__iter__`.
        """
        
        return cmds.listAttr(self.array(), multi=True)
    
#    def item(self):
#        try: 
#            return int(Attribute.attrItemReg.search(self).group(1))
#        except: return None

    def getArrayIndices(self):
        """
        Get all set or connected array indices. Raises an error if this is not an array Attribute
        
        :rtype: `int` list
        """
        try:
            return self._getArrayIndices()[1]
        except RuntimeError:
            raise TypeError, "%s is not an array (multi) attribute" % self
    
    def numElements(self):
        """
        The number of elements in an array attribute. Raises an error if this is not an array Attribute
        
        Be aware that `Attribute.size`, which derives from ``getAttr -size``, does not always produce the expected
        value. It is recommend that you use `Attribute.numElements` instead.  This is a maya bug, *not* a pymel bug.
        
            >>> from pymel.all import *
            >>> f=newFile(f=1) #start clean
            >>> 
            >>> dls = SCENE.defaultLightSet
            >>> dls.dagSetMembers.numElements()
            0
            >>> dls.dagSetMembers.size()
            0
            >>> SpotLight() # create a light, which adds to the lightSet
            SpotLight(u'spotLightShape1')
            >>> dls.dagSetMembers.numElements()
            1
            >>> dls.dagSetMembers.size()  # should be 1
            0
            >>> SpotLight() # create another light, which adds to the lightSet
            SpotLight(u'spotLightShape2')
            >>> dls.dagSetMembers.numElements()
            2
            >>> dls.dagSetMembers.size() # should be 2
            1
        
        :rtype: `int`
        """
        
        try:
            return self._getArrayIndices()[0]
        except RuntimeError:
            raise TypeError, "%s is not an array (multi) attribute" % self

    @mayahook.deprecated('This method does not always produce the expected result. Use Attribute.numElements instead.', 'Attribute')
    def size(self):
        """
        The number of elements in an array attribute. Returns None if not an array element.
        
        Be aware that `Attribute.size`, which derives from ``getAttr -size``, does not always produce the expected
        value. It is recommend that you use `Attribute.numElements` instead.  This is a maya bug, *not* a pymel bug.
        
            >>> from pymel.all import *
            >>> f=newFile(f=1) #start clean
            >>>
            >>> dls = SCENE.defaultLightSet
            >>> dls.dagSetMembers.numElements()
            0
            >>> dls.dagSetMembers.size()
            0
            >>> SpotLight() # create a light, which adds to the lightSet
            SpotLight(u'spotLightShape1')
            >>> dls.dagSetMembers.numElements()
            1
            >>> dls.dagSetMembers.size()  # should be 1
            0
            >>> SpotLight() # create another light, which adds to the lightSet
            SpotLight(u'spotLightShape2')
            >>> dls.dagSetMembers.numElements()
            2
            >>> dls.dagSetMembers.size() # should be 2
            1
            
        :rtype: `int`
        """
        #return cmds.getAttr(self, size=True)    
        try:
            return self.__apiobject__().numElements()
        except RuntimeError:
            pass
                
    item = _factories.wrapApiMethod( api.MPlug, 'logicalIndex', 'item' )
    index = _factories.wrapApiMethod( api.MPlug, 'logicalIndex', 'index' )
    
    def setEnums(self, enumList):
        cmds.addAttr( self, e=1, en=":".join(enumList) )
    
    def getEnums(self):
        """
        :rtype: `unicode` list
        """
        return cmds.addAttr( self, q=1, en=1 ).split(':')    
            
    # getting and setting                    
    set = general.setAttr            
    get = general.getAttr
    setKey = _factories.functionFactory( cmds.setKeyframe, rename='setKey' )       
    
    
#----------------------
#xxx{ Connections
#----------------------    
          
    def isConnectedTo(self, other, ignoreUnitConversion=False, checkLocalArray=False, checkOtherArray=False ):
        """
        Determine if the attribute is connected to the passed attribute.
        
        If checkLocalArray is True and the current attribute is a multi/array, the current attribute's elements will also be tested.
        
        If checkOtherArray is True and the passed attribute is a multi/array, the passed attribute's elements will also be tested.
        
        If checkLocalArray and checkOtherArray are used together then all element combinations will be tested.
         
        """

        if cmds.isConnected( self, other, ignoreUnitConversion=ignoreUnitConversion):
            return True
        
        if checkLocalArray and self.isMulti():
            for elem in self:
                if elem.isConnectedTo(other, ignoreUnitConversion=ignoreUnitConversion, checkLocalArray=False, checkOtherArray=checkOtherArray):
                    return True
                
        if checkOtherArray:
            other = Attribute(other)
            if other.isMulti():
                for elem in other:
                    if self.isConnectedTo(elem, ignoreUnitConversion=ignoreUnitConversion, checkLocalArray=False, checkOtherArray=False):
                        return True

        
        return False
    
    ## does not work because this method cannot return a value, it is akin to +=       
    #def __irshift__(self, other):
    #    """operator for 'isConnected'
    #        sphere.tx >>= box.tx
    #    """ 
    #    return cmds.isConnected(self, other)
    

    connect = general.connectAttr
        
    def __rshift__(self, other):
        """
        operator for 'connectAttr'
        
            >>> from pymel.all import *
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """ 
        return general.connectAttr( self, other, force=True )
                
    disconnect = general.disconnectAttr
    
    def __floordiv__(self, other):
        """
        operator for 'disconnectAttr'
        
            >>> from pymel.all import *
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """ 
        # no return
        cmds.disconnectAttr( self, other )
                
    def inputs(self, **kwargs):
        """
        ``listConnections -source 1 -destination 0``
        
        see `Attribute.connections` for the full ist of flags.
        
        :rtype: `general.PyNode` list
        """
        
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        
        return general.listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        """
        ``listConnections -source 0 -destination 1``
        
        see `Attribute.connections` for the full ist of flags.
        
        :rtype: `general.PyNode` list
        """
        
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return general.listConnections(self, **kwargs)
    
    def insertInput(self, node, nodeOutAttr, nodeInAttr ):
        """connect the passed node.outAttr to this attribute and reconnect
        any pre-existing connection into node.inAttr.  if there is no
        pre-existing connection, this method works just like connectAttr. 
        
        for example, for two nodes with the connection::
                
            a.out-->b.in
            
        running this command::
        
            b.insertInput( 'c', 'out', 'in' )
            
        causes the new connection order (assuming 'c' is a node with 'in' and 'out' attributes)::
                
            a.out-->c.in
            c.out-->b.in
        """
        inputs = self.inputs(plugs=1)
        self.connect( node + '.' + nodeOutAttr, force=1 )
        if inputs:
            inputs[0].connect( node + '.' + nodeInAttr )
    
    @_factories.addMelDocs( 'setKeyframe' )    
    def setKey(self, **kwargs):
        kwargs.pop( 'attribute', None )
        kwargs.pop( 'at', None )
        return cmds.setKeyframe( self, **kwargs )
#}
#----------------------
#xxx{ Info and Modification
#----------------------
    
#    def alias(self, **kwargs):
#        """aliasAttr"""
#        return cmds.aliasAttr( self, **kwargs )    
                            
#    def add( self, **kwargs):    
#        kwargs['longName'] = self.plugAttr()
#        kwargs.pop('ln', None )
#        return addAttr( self.node(), **kwargs )    
                    
    def delete(self):
        """deleteAttr"""
        return cmds.deleteAttr( self )
    
    def remove( self, **kwargs):
        'removeMultiInstance'
        #kwargs['break'] = True
        return cmds.removeMultiInstance( self, **kwargs )
        
    # Edge, Vertex, CV Methods
#    def getTranslation( self, **kwargs ):
#        """xform -translation"""
#        kwargs['translation'] = True
#        kwargs['query'] = True
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )
        
    #----------------------
    # Info Methods
    #----------------------
    
    def isDirty(self, **kwargs):
        """
        :rtype: `bool`
        """
        return cmds.isDirty(self, **kwargs)
        
    def affects( self, **kwargs ):
        return map( lambda x: Attribute( '%s.%s' % ( self.node(), x )),
            cmds.affects( self.plugAttr(), self.node()  ) )

    def affected( self, **kwargs ):
        return map( lambda x: Attribute( '%s.%s' % ( self.node(), x )),
            cmds.affects( self.plugAttr(), self.node(), by=True  ))
                
    # getAttr info methods
    def type(self):
        """
        getAttr -type
        
        :rtype: `unicode`
        """
        return cmds.getAttr(self, type=True)
    
   
    def lock(self):
        "setAttr -locked 1"
        return self.setLocked(True)
        
    def unlock(self):
        "setAttr -locked 0"
        return self.setLocked(False)
    
              
    def isSettable(self):
        """getAttr -settable
        
        :rtype: `bool`
        """
        return cmds.getAttr(self, settable=True)
    
    # attributeQuery info methods
    def isHidden(self):
        """
        attributeQuery -hidden
        
        :rtype: `bool`
        """
        return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), hidden=True)
        
    def isConnectable(self):
        """
        attributeQuery -connectable
        
        :rtype: `bool`
        """
        return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), connectable=True)    

    
    isMulti = _factories.wrapApiMethod( api.MPlug, 'isArray', 'isMulti' )

    
    def exists(self):
        """
        Whether the attribute actually exists.
        
        In spirit, similar to 'attributeQuery -exists'...
        ...however, also handles multi (array) attribute elements, such as plusMinusAverage.input1D[2] 
        
        :rtype: `bool`
        """
        
        if self.isElement():
            arrayExists = self.array().exists()
            if not arrayExists:
                return False
            
            # If the array exists, now check the array indices...
            indices = self.array().getArrayIndices()
            return (indices and self.index() in indices)
        else:
            try:
                return bool( cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), exists=True) ) 
            except TypeError:
                return False
        
#}
#-------------------------- 
#xxx{ Ranges
#-------------------------- 
        
    def getSoftMin(self):
        """attributeQuery -softMin
            Returns None if softMin does not exist.
        
        :rtype: `float`  
        """
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMinExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMin=True)[0]    
            
    def getSoftMax(self):
        """attributeQuery -softMax
            Returns None if softMax does not exist.
            
        :rtype: `float`      
        """
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMaxExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMax=True)[0]
    
    def getMin(self):
        """attributeQuery -min
            Returns None if min does not exist.
        
        :rtype: `float`  
        """
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), minExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), min=True)[0]
            
    def getMax(self):
        """attributeQuery -max
            Returns None if max does not exist.
            
        :rtype: `float`  
        """
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), maxExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), max=True)[0]
    
    def getSoftRange(self):
        """attributeQuery -softRange
            returns a two-element list containing softMin and softMax. if the attribute does not have
            a softMin or softMax the corresponding element in the list will be set to None.
         
        :rtype: [`float`, `float`]     
        """
        softRange = []
        softRange.append( self.getSoftMin() )
        softRange.append( self.getSoftMax() )
        return softRange
    
            
    def getRange(self):
        """attributeQuery -range
            returns a two-element list containing min and max. if the attribute does not have
            a softMin or softMax the corresponding element will be set to None.
        
        :rtype: `float`      
        """
        range = []
        range.append( self.getMin() )
        range.append( self.getMax() )
        return range
    
    def setMin(self, newMin):
        self.setRange(newMin, 'default')
        
    def setMax(self, newMax):
        self.setRange('default', newMax)

    def setSoftMin(self, newMin):
        self.setSoftRange(newMin, 'default')
        
    def setSoftMax(self, newMax):
        self.setSoftRange('default', newMax)
                
    def setRange(self, *args):
        """provide a min and max value as a two-element tuple or list, or as two arguments to the
        method. To remove a limit, provide a None value.  for example:
        
            >>> from pymel.all import *
            >>> s = polyCube()[0]
            >>> s.addAttr( 'new' )
            >>> s.new.setRange( -2, None ) #sets just the min to -2 and removes the max limit
            >>> s.new.setMax( 3 ) # sets just the max value and leaves the min at its previous default 
            >>> s.new.getRange()
            [-2.0, 3.0]
            
        """
        
        self._setRange('hard', *args)
        
    def setSoftRange(self, *args):
        self._setRange('soft', *args)    
        
    def _setRange(self, limitType, *args):
        
        if len(args)==2:
            newMin = args[0]
            newMax = args[1]
        
        if len(args)==1:
            try:
                newMin = args[0][0]
                newMax = args[0][1]
            except:    
                raise TypeError, "Please provide a min and max value as a two-element tuple or list, or as two arguments to the method. To ignore a limit, provide a None value."

                
        # first find out what connections are going into and out of the object
        ins = self.inputs(p=1)
        outs = self.outputs(p=1)

        # get the current value of the attr
        val = self.get()

        # break the connections if they exist
        self.disconnect()

        #now tokenize $objectAttr in order to get it's individual parts
        obj = self.node()
        attr = self.plugAttr()

        # re-create the attribute with the new min/max
        kwargs = {}
        kwargs['at'] = self.type()
        kwargs['ln'] = attr
        
        # MIN
        # if 'default' is passed a value, we retain the current value
        if newMin == 'default':
            currMin = self.getMin()
            currSoftMin = self.getSoftMin()
            if currMin is not None:
                kwargs['min'] = currMin
            elif currSoftMin is not None:
                kwargs['smn'] = currSoftMin    
                
        elif newMin is not None:
            if limitType == 'hard':
                kwargs['min'] = newMin
            else:
                kwargs['smn'] = newMin
                
        # MAX    
        # if 'default' is passed a value, we retain the current value
        if newMax == 'default':
            currMax = self.getMax()
            currSoftMax = self.getSoftMin()
            if currMax is not None:
                kwargs['max'] = currMax
            elif currSoftMax is not None:
                kwargs['smx'] = currSoftMax    
                
        elif newMax is not None:
            if limitType == 'hard':
                kwargs['max'] = newMax
            else:
                kwargs['smx'] = newMax
        
        # delete the attribute
        self.delete()                
        cmds.addAttr( obj, **kwargs )

        # set the value to be what it used to be
        self.set(val);

        # remake the connections
        for conn in ins:
            conn >> self
            
        for conn in outs:
            self >> outs


#    def getChildren(self):
#        """attributeQuery -listChildren"""
#        return map( 
#            lambda x: Attribute( self.node() + '.' + x ), 
#            util.listForNone( cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), listChildren=True) )
#                )
#}
#-------------------------- 
#xxx{ Relatives
#-------------------------- 

    def getChildren(self):
        """attributeQuery -listChildren
        
        :rtype: `Attribute` list  
        """
        res = []
        for i in range(self.numChildren() ):
            res.append( Attribute( self.node(), self.__apimfn__().child(i) ) )
        return res
    children = getChildren
    
    def getSiblings(self):
        """attributeQuery -listSiblings
        
        :rtype: `Attribute` list  
        """
        try:
            return self.getParent().getChildren()
        except:
            pass
    siblings = getSiblings
    
    def firstParent(self):
        """
        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;

              
              Negative values will traverse from the top.

              A value of 0 will return the same node.
              The default value is 1.
              
              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown). 
        
        :rtype: `Attribute`  
        """
        try:
            return Attribute( self.node(), self.__apimfn__().parent() )
        except:
            pass

    getAllParents, getParent = _makeAllParentFunc_and_ParentFuncWithGenerationArgument(firstParent)
    parent = getParent
        
#}      


class DependNode( general.PyNode ):
    __apicls__ = api.MFnDependencyNode
    __metaclass__ = _factories.MetaMayaNodeWrapper
    #-------------------------------
    #    Name Info and Manipulation
    #-------------------------------
#    def __new__(cls,name,create=False):
#        """
#        Provides the ability to create the object when creating a class
#        
#            >>> n = pm.Transform("persp",create=True)
#            >>> n.__repr__()
#            # Result: Transform(u'persp1')
#        """
#        if create:
#            ntype = cls.__melnode__
#            name = createNode(ntype,n=name,ss=1)
#        return general.PyNode.__new__(cls,name)

#    def __init__(self, *args, **kwargs ):
#        self.apicls.__init__(self, self._apiobject.object() )
        
    def _updateName(self) :
        # test validity
        self.__apimobject__()
        self._name = self.__apimfn__().name()
        return self._name 

    def name(self, update=True) :
        """
        :rtype: `unicode`
        """
        
        if update or self._name is None:
            try:
                return self._updateName()
            except general.MayaObjectError:
                _logger.warn( "object %s no longer exists" % self._name ) 
        return self._name  
#
#    def shortName(self):
#        """
#        This produces the same results as `DependNode.name` and is included to simplify looping over lists
#        of nodes that include both Dag and Depend nodes.
#        
#        :rtype: `unicode`
#        """ 
#        return self.name()
#
#    def longName(self):
#        """
#        This produces the same results as `DependNode.name` and is included to simplify looping over lists
#        of nodes that include both Dag and Depend nodes.
#        
#        :rtype: `unicode`
#        """ 
#        return self.name()
#
#    def nodeName(self):
#        """
#        This produces the same results as `DependNode.name` and is included to simplify looping over lists
#        of nodes that include both Dag and Depend nodes.
#        
#        :rtype: `unicode`
#        """ 
#        return self.name()
#    
    #rename = rename
    def rename( self, name ):
        """
        :rtype: `DependNode`
        """
        # TODO : ensure that name is the shortname of a node. implement ignoreShape flag
        #self.setName( name ) # no undo support
        return general.rename(self, name)
    
    def __apiobject__(self) :
        "get the default API object (MObject) for this node if it is valid"
        return self.__apimobject__()
    
    def __apimobject__(self) :
        "get the MObject for this node if it is valid"
        handle = self.__apihandle__()
        if api.isValidMObjectHandle( handle ) :
            return handle.object()
        raise general.MayaNodeError( self._name )
        
    def __apihandle__(self) :
        return self.__apiobjects__['MObjectHandle']
    

    def __str__(self):
        return "%s" % self.name()

    def __unicode__(self):
        return u"%s" % self.name()

    if version.CURRENT >= version.v2009:
        def __hash__(self):
            return self.__apihandle__().hashCode()

    def node(self):
        """for compatibility with Attribute class
        
        :rtype: `DependNode`
        
        """
        return self
    

        
        
    #--------------------------
    #    Modification
    #--------------------------
      
    def lock( self, **kwargs ):
        'lockNode -lock 1'
        #kwargs['lock'] = True
        #kwargs.pop('l',None)
        #return cmds.lockNode( self, **kwargs)
        return self.setLocked( True )
        
    def unlock( self, **kwargs ):
        'lockNode -lock 0'
        #kwargs['lock'] = False
        #kwargs.pop('l',None)
        #return cmds.lockNode( self, **kwargs)
        return self.setLocked( False )

    def cast( self, swapNode, **kwargs):
        """nodeCast"""
        return cmds.nodeCast( self, swapNode, *kwargs )

    
    duplicate = general.duplicate
    
#--------------------------
#xxx{    Presets
#-------------------------- 
   
    def savePreset(self, presetName, custom=None, attributes=[]):
        
        kwargs = {'save':True}
        if attributes:
            kwargs['attributes'] = ' '.join(attributes)
        if custom:
            kwargs['custom'] = custom
            
        return cmds.nodePreset( presetName, **kwargs)
        
    def loadPreset(self, presetName):
        kwargs = {'load':True}
        return cmds.nodePreset( presetName, **kwargs)
        
    def deletePreset(self, presetName):
        kwargs = {'delete':True}
        return cmds.nodePreset( presetName, **kwargs)
        
    def listPresets(self):
        kwargs = {'list':True}
        return cmds.nodePreset( **kwargs)
#} 
          
#--------------------------
#xxx{    Info
#-------------------------- 
    type = general.nodeType
            
         
    def referenceFile(self):
        """referenceQuery -file
        Return the reference file to which this object belongs.  None if object is not referenced
        
        :rtype: `FileReference`
        
        """
        try:
            return _FileReference( cmds.referenceQuery( self, f=1) )
        except RuntimeError:
            None

    isReadOnly = _factories.wrapApiMethod( api.MFnDependencyNode, 'isFromReferencedFile', 'isReadOnly' )
            
    def classification(self):
        'getClassification'
        return general.getClassification( self.type() )    
        #return self.__apimfn__().classification( self.type() )
    
#}
#--------------------------
#xxx{   Connections
#-------------------------- 
    
    def inputs(self, **kwargs):
        """listConnections -source 1 -destination 0
        
        :rtype: `general.PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return general.listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        """listConnections -source 0 -destination 1
        
        :rtype: `general.PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return general.listConnections(self, **kwargs)                            

    def sources(self, **kwargs):
        """listConnections -source 1 -destination 0
        
        :rtype: `general.PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return general.listConnections(self, **kwargs)
    
    def destinations(self, **kwargs):
        """listConnections -source 0 -destination 1
        
        :rtype: `general.PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return general.listConnections(self, **kwargs)    
        
    def shadingGroups(self):
        """list any shading groups in the future of this object - works for shading nodes, transforms, and shapes 
        
        :rtype: `DependNode` list
        """
        return self.future(type='shadingEngine')
        
#}     
#--------------------------
#xxx{    Attributes
#--------------------------
    def __getattr__(self, attr):
        try :
            return getattr(super(general.PyNode, self), attr)
        except AttributeError :
            try:
                return DependNode.attr(self,attr)
            except general.MayaAttributeError, e:
                # since we're being called via __getattr__ we don't know whether the user was intending 
                # to get a class method or a maya attribute, so we raise a more generic AttributeError
                raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
            
    @util.universalmethod
    def attrDefaults(obj,attr):
        """
        Access to an attribute of a node.  This does not require an instance:
            
            >>> Transform.attrDefaults('tx').isKeyable()
            True
            
        but it can use one if needed ( for example, for dynamically created attributes )
            
            >>> Transform(u'persp').attrDefaults('tx').isKeyable()
            
        Note: this is still experimental.   
        """
        if inspect.isclass(obj):
            cls = obj # keep things familiar
            try:
                nodeMfn = cls.__apiobjects__['MFn']
            except KeyError:          
                cls.__apiobjects__['dagMod'] = api.MDagModifier()
                cls.__apiobjects__['dgMod'] = api.MDGModifier()
                # TODO: make something more reliable than uncapitalize
                obj = api.conversions._makeDgModGhostObject( util.uncapitalize(cls.__name__), 
                                                                cls.__apiobjects__['dagMod'], 
                                                                cls.__apiobjects__['dgMod'] )
                nodeMfn = cls.__apicls__(obj)
                cls.__apiobjects__['MFn'] = nodeMfn
            
        else:
            self = obj # keep things familiar
            nodeMfn = self.__apimfn__()
        
        # TODO: create a wrapped class for MFnAttribute
        return api.MFnAttribute( nodeMfn.attribute(attr) )
        
    def attr(self, attr):
        """
        access to attribute plug of a node. returns an instance of the Attribute class for the 
        given attribute name.
        
        :rtype: `Attribute`
        """
        #return Attribute( '%s.%s' % (self, attr) )
        try :
            if '.' in attr or '[' in attr:
                # Compound or Multi Attribute
                # there are a couple of different ways we can proceed: 
                # Option 1: back out to api.toApiObject (via general.PyNode)
                # return Attribute( self.__apiobject__(), self.name() + '.' + attr )
            
                # Option 2: nameparse.
                # this avoids calling self.name(), which can be slow
                import pymel.util.nameparse as nameparse
                nameTokens = nameparse.getBasicPartList( 'dummy.' + attr )
                result = self.__apiobject__()
                for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
                    if isinstance( token, nameparse.MayaName ):
                        if isinstance( result, api.MPlug ):
                            # you can't get a child plug from a multi/array plug.
                            # if result is currently 'defaultLightList1.lightDataArray' (an array)
                            # and we're trying to get the next plug, 'lightDirection', then we need a dummy index.
                            # the following line will reuslt in 'defaultLightList1.lightDataArray[-1].lightDirection'
                            if result.isArray():
                                result = self.__apimfn__().findPlug( unicode(token) )  
                            else:
                                result = result.child( self.__apimfn__().attribute( unicode(token) ) )
                        else: # Node
                            result = self.__apimfn__().findPlug( unicode(token) )                              
#                                # search children for the attribute to simulate  cam.focalLength --> perspShape.focalLength
#                                except TypeError:
#                                    for i in range(fn.childCount()):
#                                        try: result = api.MFnDagNode( fn.child(i) ).findPlug( unicode(token) )
#                                        except TypeError: pass
#                                        else:break
                    if isinstance( token, nameparse.NameIndex ):
                        result = result.elementByLogicalIndex( token.value )
                return Attribute( self.__apiobject__(), result )
            else:
                # NOTE: not sure if this should be True or False
                return Attribute( self.__apiobject__(), self.__apimfn__().findPlug( attr, False ) ) 
            
        except RuntimeError:
            if mayahook.pymel_options.get( '0_7_compatibility_mode', True):
                import other
                return other.AttributeName( '%s.%s' % (self, attr) )
                
            # raise our own MayaAttributeError, which subclasses AttributeError and MayaObjectError
            raise general.MayaAttributeError( '%s.%s' % (self, attr) )
               
    def hasAttr( self, attr):
        """
        check if the node has the given maya attribute.
        :rtype: `bool`
        """
        try : 
            self.attr(attr)
            return True
        except AttributeError:
            return False

    @_factories.addMelDocs('setAttr')  
    def setAttr( self, attr, *args, **kwargs):
        # for now, using strings is better, because there is no MPlug support
        return general.setAttr( "%s.%s" % (self, attr), *args, **kwargs )
    
    @_factories.addMelDocs('setAttr')  
    def setDynamicAttr( self, attr, *args, **kwargs):
        """
        same as `DependNode.setAttr` with the force flag set to True.  This causes
        the attribute to be created based on the passed input value.
        """
        
        # for now, using strings is better, because there is no MPlug support
        kwargs['force'] = True
        return general.setAttr( "%s.%s" % (self, attr), *args, **kwargs )
    
    @_factories.addMelDocs('getAttr')  
    def getAttr( self, attr, *args, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return general.getAttr( "%s.%s" % (self, attr), *args,  **kwargs )

    @_factories.addMelDocs('addAttr')  
    def addAttr( self, attr, **kwargs):
        # for now, using strings is better, because there is no MPlug support  
        assert 'longName' not in kwargs and 'ln' not in kwargs
        kwargs['longName'] = attr
        return general.addAttr( unicode(self), **kwargs )
    
    @_factories.addMelDocs('connectAttr')  
    def connectAttr( self, attr, destination, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return general.connectAttr( "%s.%s" % (self, attr), destination, **kwargs )
    
    @_factories.addMelDocs('disconnectAttr')  
    def disconnectAttr( self, attr, destination=None, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return general.disconnectAttr( "%s.%s" % (self, attr), destination, **kwargs )

                    
    listAnimatable = _listAnimatable

    def listAttr( self, **kwargs):
        """listAttr
        
        :rtype: `Attribute` list
        
        """
        # stringify fix
        return map( lambda x: self.attr(x), util.listForNone(cmds.listAttr(self.name(), **kwargs)))

    def attrInfo( self, **kwargs):
        """attributeInfo
        
        :rtype: `Attribute` list
        """
        # stringify fix
        return map( lambda x: self.attr(x) , util.listForNone(cmds.attributeInfo(self.name(), **kwargs)))
 
 
#}
#-----------------------------------------
#xxx{ Name Info and Manipulation
#-----------------------------------------

# Now just wraps NameParser functions
    
    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged.
        
        >>> from pymel.all import *
        >>> SCENE.lambert1.stripNum()
        u'lambert'
        
        :rtype: `unicode`
        """
        return other.NameParser(self.name()).stripNum()
            
    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised.

        >>> from pymel.all import *
        >>> SCENE.lambert1.extractNum()
        u'1'
        
        :rtype: `unicode`
        """
        return other.NameParser(self.name()).extractNum()

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found

        If there is no trailing number, appends '1' to the name.
        
        :rtype: `unicode`
        """
        return other.NameParser(self.name()).nextUniqueName()
                
    def nextName(self):
        """Increment the trailing number of the object by 1

        Raises an error if the name has no trailing number.
        
        >>> from pymel.all import *
        >>> SCENE.lambert1.nextName()
        DependNodeName('lambert2')
        
        :rtype: `unicode`
        """
        return other.NameParser(self.name()).nextName()
            
    def prevName(self):
        """Decrement the trailing number of the object by 1
        
        Raises an error if the name has no trailing number.
        
        :rtype: `unicode`
        """
        return other.NameParser(self.name()).prevName()
    
    @classmethod
    def registerVirtualSubClass( cls, nameRequired=False ):
        """
        Deprecated
        """
        _factories.registerVirtualClass(cls, nameRequired)

#}

if version.CURRENT >= version.v2011:
    class ContainerBase(DependNode):
        __metaclass__ = _factories.MetaMayaNodeWrapper
        pass

    class Entity(ContainerBase):
        __metaclass__ = _factories.MetaMayaNodeWrapper
        pass

else:
    class Entity(DependNode):
        __metaclass__ = _factories.MetaMayaNodeWrapper
        pass

class DagNode(Entity):
 
    #:group Path Info and Modification: ``*parent*``, ``*Parent*``, ``*child*``, ``*Child*``
    """
    """
    
    __apicls__ = api.MFnDagNode
    __metaclass__ = _factories.MetaMayaNodeWrapper
    
#    def __init__(self, *args, **kwargs ):
#        self.apicls.__init__(self, self.__apimdagpath__() )
    _componentAttributes = {}

    def comp(self, compName):
        """
        Will retrieve a Component object for this node; similar to
        DependNode.attr(), but for components.
        
        :rtype: `Component`
        """        
        if compName in self._componentAttributes:
            compClass = self._componentAttributes[compName]
            if isinstance(compClass, tuple):
                # We have something like:
                # 'uIsoparm'    : (NurbsSurfaceIsoparm, 'u')
                # need to specify what 'flavor' of the basic
                # component we need...
                return compClass[0](self, {compClass[1]:ComponentIndex(label=compClass[1])})
            else:
                return compClass(self)
        # if we do self.getShape(), and this is a shape node, we will
        # enter a recursive loop if compName isn't actually a comp:
        # since shape doesn't have 'getShape', it will call __getattr__
        # for 'getShape', which in turn call comp to check if it's a comp,
        # which will call __getattr__, etc
        # ..soo... check if we have a 'getShape'!
        elif hasattr(self, 'getShape'):
            shape = self.getShape()
            if shape:
                return shape.comp(compName)
        raise general.MayaComponentError( '%s.%s' % (self, compName) )
                
    def _updateName(self, long=False) :
        #if api.isValidMObjectHandle(self._apiobject) :
            #obj = self._apiobject.object()
            #dagFn = api.MFnDagNode(obj)
            #dagPath = api.MDagPath()
            #dagFn.getPath(dagPath)
        dag = self.__apimdagpath__()
        if dag:
            name = dag.partialPathName()
            if not name:
                raise general.MayaNodeError
            
            self._name = name
            if long :
                return dag.fullPathName()

        return self._name                       
            
    def name(self, update=True, long=False) :
        
        if update or long or self._name is None:
            try:
                return self._updateName(long)
            except general.MayaObjectError:
                _logger.warn( "object %s no longer exists" % self._name ) 
        return self._name  
    
    def longName(self):
        """
        The full dag path to the object, including leading pipe ( | )
        
        :rtype: `unicode`
        """
        return self.name(long=True)
    fullPath = longName
            
    def shortName( self ):
        """
        The shortest unique name.
        
        :rtype: `unicode`
        """
        return self.name(long=False)

    def nodeName( self ):
        """
        Just the name of the node, without any dag path
        
        :rtype: `unicode`
        """
        return self.name().split('|')[-1]
    
      
    def __apiobject__(self) :
        "get the MDagPath for this object if it is valid"
        return self.__apimdagpath__()
 
    def __apimdagpath__(self) :
        "get the MDagPath for this object if it is valid"

        try:
            dag = self.__apiobjects__['MDagPath']
            # test for validity: if the object is not valid an error will be raised
            self.__apimobject__()
            return dag
        except KeyError:
            # class was instantiated from an MObject, but we can still retrieve the first MDagPath
            
            #assert argObj.hasFn( api.MFn.kDagNode ) 
            dag = api.MDagPath()
            # we can't use self.__apimfn__() becaue the mfn is instantiated from an MDagPath 
            # which we are in the process of finding out
            mfn = api.MFnDagNode( self.__apimobject__() )
            mfn.getPath(dag)
            self.__apiobjects__['MDagPath'] = dag
            return dag
#            if dag.isValid():
#                #argObj = dag
#                if dag.fullPathName():
#                    argObj = dag
#                else:
#                    print 'produced valid MDagPath with no name: %s(%s)' % ( argObj.apiTypeStr(), api.MFnDependencyNode(argObj).name() )

    def __apihandle__(self) :
        try:
            handle = self.__apiobjects__['MObjectHandle']
        except:
            try:
                handle = api.MObjectHandle( self.__apiobjects__['MDagPath'].node() )
            except RuntimeError:
                raise general.MayaNodeError( self._name )
            self.__apiobjects__['MObjectHandle'] = handle
        return handle
    
#    def __apimfn__(self):
#        if self._apimfn:
#            return self._apimfn
#        elif self.__apicls__:
#            obj = self._apiobject
#            if api.isValidMDagPath(obj):
#                try:
#                    self._apimfn = self.__apicls__(obj)
#                    return self._apimfn
#                except KeyError:
#                    pass
                        
#    def __init__(self, *args, **kwargs):
#        if self._apiobject:
#            if isinstance(self._apiobject, api.MObjectHandle):
#                dagPath = api.MDagPath()
#                api.MDagPath.getAPathTo( self._apiobject.object(), dagPath )
#                self._apiobject = dagPath
#        
#            assert api.isValidMDagPath( self._apiobject )
            
    """
    def __init__(self, *args, **kwargs) :
        if args :
            arg = args[0]
            if len(args) > 1 :
                comp = args[1]
            if isinstance(arg, DagNode) :
                self._name = unicode(arg.name())
                self._apiobject = api.MObjectHandle(arg.object())
            elif api.isValidMObject(arg) or api.isValidMObjectHandle(arg) :
                objHandle = api.MObjectHandle(arg)
                obj = objHandle.object() 
                if api.isValidMDagNode(obj) :
                    self._apiobject = objHandle
                    self._updateName()
                else :
                    raise TypeError, "%r might be a dependencyNode, but not a dagNode" % arg              
            elif isinstance(arg, basestring) :
                obj = api.toMObject (arg)
                if obj :
                    # creation for existing object
                    if api.isValidMDagNode (obj):
                        self._apiobject = api.MObjectHandle(obj)
                        self._updateName()
                    else :
                        raise TypeError, "%r might be a dependencyNode, but not a dagNode" % arg 
                else :
                    # creation for inexistent object 
                    self._name = arg
            else :
                raise TypeError, "don't know how to make a DagNode out of a %s : %r" % (type(arg), arg)  
       """   

            
#--------------------------------
#xxx{  Path Info and Modification
#--------------------------------
    def root(self):
        """rootOf
        
        :rtype: `unicode`
        """
        return DagNode( '|' + self.longName()[1:].split('|')[0] )

#    def hasParent(self, parent ):
#        try:
#            return self.__apimfn__().hasParent( parent.__apiobject__() )
#        except AttributeError:
#            obj = api.toMObject(parent)
#            if obj:
#               return self.__apimfn__().hasParent( obj )
#          
#    def hasChild(self, child ):
#        try:
#            return self.__apimfn__().hasChild( child.__apiobject__() )
#        except AttributeError:
#            obj = api.toMObject(child)
#            if obj:
#               return self.__apimfn__().hasChild( obj )
#    
#    def isParentOf( self, parent ):
#        try:
#            return self.__apimfn__().isParentOf( parent.__apiobject__() )
#        except AttributeError:
#            obj = api.toMObject(parent)
#            if obj:
#               return self.__apimfn__().isParentOf( obj )
#    
#    def isChildOf( self, child ):
#        try:
#            return self.__apimfn__().isChildOf( child.__apiobject__() )
#        except AttributeError:
#            obj = api.toMObject(child)
#            if obj:
#               return self.__apimfn__().isChildOf( obj )

    def isInstanceOf(self, other):
        """
        :rtype: `bool`
        """
        if isinstance( other, general.PyNode ):
            return self.__apimobject__() == other.__apimobject__()
        else:
            try:
                return self.__apimobject__() == general.PyNode(other).__apimobject__()
            except:
                return False
    
    def instanceNumber(self):
        """
        returns the instance number that this path represents in the DAG. The instance number can be used to determine which
        element of the world space array attributes of a DAG node to connect to get information regarding this instance.
        
        :rtype: `int`
        """
        return self.__apimdagpath__().instanceNumber()
    
        
    def getInstances(self, includeSelf=True):
        """
        :rtype: `DagNode` list
        
        >>> from pymel.all import *
        >>> f=newFile(f=1) #start clean
        >>>
        >>> s = polyPlane()[0]
        >>> instance(s)
        [Transform(u'pPlane2')]
        >>> instance(s)
        [Transform(u'pPlane3')]
        >>> s.getShape().getInstances()
        [Mesh(u'pPlane1|pPlaneShape1'), Mesh(u'pPlane2|pPlaneShape1'), Mesh(u'pPlane3|pPlaneShape1')]
        >>> s.getShape().getInstances(includeSelf=False)
        [Mesh(u'pPlane2|pPlaneShape1'), Mesh(u'pPlane3|pPlaneShape1')]
        
        """
        d = api.MDagPathArray()
        self.__apimfn__().getAllPaths(d)
        thisDagPath = self.__apimdagpath__()
        result = [ general.PyNode( api.MDagPath(d[i])) for i in range(d.length()) if includeSelf or not d[i] == thisDagPath ]
        
        return result

    def getOtherInstances(self):
        """
        same as `DagNode.getInstances` with includeSelf=False.
        
        :rtype: `DagNode` list
        """
        return self.getInstances(includeSelf=False)
    
    def firstParent(self):
        """firstParentOf
        
        :rtype: `DagNode`
        """
        try:
            return DagNode( '|'.join( self.longName().split('|')[:-1] ) )
        except TypeError:
            return DagNode( '|'.join( self.split('|')[:-1] ) )

#    def numChildren(self):
#        """
#        see also `childCount`
#        
#        :rtype: `int`
#        """
#        return self.__apimdagpath__().childCount()
    
#    def getParent(self, **kwargs):
#        # TODO : print warning regarding removal of kwargs, test speed difference
#        parent = api.MDagPath( self.__apiobject__() )
#        try:
#            parent.pop()
#            return general.PyNode(parent)
#        except RuntimeError:
#            pass
#
#    def getChildren(self, **kwargs):
#        # TODO : print warning regarding removal of kwargs
#        children = []
#        thisDag = self.__apiobject__()
#        for i in range( thisDag.childCount() ):
#            child = api.MDagPath( thisDag )
#            child.push( thisDag.child(i) )
#            children.append( general.PyNode(child) )
#        return children

    def firstParent2(self, **kwargs):
        """unlike the firstParent command which determines the parent via string formatting, this 
        command uses the listRelatives command
        
        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> from pymel.all import *
                  >>> select(cl=1)
                  >>> bottom = group(n='bottom')
                  >>> group(n='almostThere')
                  Transform(u'almostThere')
                  >>> group(n='nextLevel')
                  Transform(u'nextLevel')
                  >>> group(n='topLevel')
                  Transform(u'topLevel')
                  >>> bottom.longName()
                  u'|topLevel|nextLevel|almostThere|bottom'
                  >>> bottom.getParent(2)
                  Transform(u'nextLevel')
              
              Negative values will traverse from the top:
              
                  >>> bottom.getParent(generations=-3)
                  Transform(u'almostThere')
              
              A value of 0 will return the same node.
              The default value is 1.
              
              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown). 
        
        :rtype: `DagNode`
        
        """
        
        kwargs['parent'] = True
        kwargs.pop('p',None)
        #if longNames:
        kwargs['fullPath'] = True
        kwargs.pop('f',None)
        
        try:
            res = cmds.listRelatives( self, **kwargs)[0]
        except TypeError:
            return None
             
        res = general.PyNode( res )
        return res
        
    getAllParents, getParent = _makeAllParentFunc_and_ParentFuncWithGenerationArgument(firstParent2)
                     
    def getChildren(self, **kwargs ):
        """
        see also `childAtIndex`
        
        :rtype: `DagNode` list
        """
        kwargs['children'] = True
        kwargs.pop('c',None)

        return general.listRelatives( self, **kwargs)
        
    def getSiblings(self, **kwargs ):
        """
        :rtype: `DagNode` list
        """
        #pass
        try:
            return [ x for x in self.getParent().getChildren() if x != self]
        except:
            return []
                
    def listRelatives(self, **kwargs ):
        """
        :rtype: `general.PyNode` list
        """
        return general.listRelatives( self, **kwargs)
        
    
    def setParent( self, *args, **kwargs ):
        """
        parent

        Modifications:
            if parent is 'None', world=True is automatically set
        """
        if args and args[-1] is None:
            kwargs['world']=True
        return self.__class__( cmds.parent( self, *args, **kwargs )[0] )

    def addChild( self, child, **kwargs ):
        """parent (reversed)
        
        :rtype: `DagNode`
        """
        cmds.parent( child, self, **kwargs )
        if not isinstance( child, general.PyNode ):
            child = general.PyNode(child)
        return child
    
    def __or__(self, child, **kwargs):
        """
        operator for `addChild`. Use to easily daisy-chain together parenting operations.
        The operation order visually mimics the resulting dag path:
        
            >>> from pymel.all import *
            >>> s = polySphere(name='sphere')[0]
            >>> c = polyCube(name='cube')[0]
            >>> t = polyTorus(name='torus')[0]
            >>> s | c | t
            Transform(u'torus')
            >>> print t.fullPath()
            |sphere|cube|torus
            
        :rtype: `DagNode`
        """
        return self.addChild(child,**kwargs)

#}   
    #instance = instance

    #--------------------------
    #    Shading
    #--------------------------    

    def isDisplaced(self):
        """Returns whether any of this object's shading groups have a displacement shader input
        
        :rtype: `bool`
        """
        for sg in self.shadingGroups():
            if len( sg.attr('displacementShader').inputs() ):
                return True
        return False

    def setObjectColor( self, color=None ):
        """This command sets the dormant wireframe color of the specified objects to an integer
        representing one of the user defined colors, or, if set to None, to the default class color"""

        kwargs = {}
        if color:
            kwargs['userDefined'] = color
        cmds.color(self, **kwargs)
        
    def makeLive( self, state=True ):
        if not state:
            cmds.makeLive(none=True)
        else:
            cmds.makeLive(self)





class Shape(DagNode):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    def getTransform(self): pass    
#class Joint(Transform):
#    pass

        
class Camera(Shape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    @mayahook.deprecated('Use getHorizontalFieldOfView instead', 'Camera' )
    def getFov(self):
        aperture = self.horizontalFilmAperture.get()
        fov = (0.5 * aperture) / (self.focalLength.get() * 0.03937)
        fov = 2.0 * math.atan (fov)
        fov = 57.29578 * fov
        return fov
    
    @mayahook.deprecated('Use setHorizontalFieldOfView instead', 'Camera' )   
    def setFov(self, fov):
        aperture = self.horizontalFilmAperture.get()
        focal = math.tan (0.00872665 * fov);
        focal = (0.5 * aperture) / (focal * 0.03937);
        self.focalLength.set(focal)
    
    @mayahook.deprecated('Use getAspectRatio instead', 'Camera' )  
    def getFilmAspect(self):
        return self.horizontalFilmAperture.get()/ self.verticalFilmAperture.get()

    def applyBookmark(self, bookmark):
        kwargs = {}
        kwargs['camera'] = self
        kwargs['edit'] = True
        kwargs['setCamera'] = True
            
        cmds.cameraView( bookmark, **kwargs )
            
    def addBookmark(self, bookmark=None):
        kwargs = {}
        kwargs['camera'] = self
        kwargs['addBookmark'] = True
        if bookmark:
            kwargs['name'] = bookmark
            
        cmds.cameraView( **kwargs )
        
    def removeBookmark(self, bookmark):
        kwargs = {}
        kwargs['camera'] = self
        kwargs['removeBookmark'] = True
        kwargs['name'] = bookmark
            
        cmds.cameraView( **kwargs )
        
    def updateBookmark(self, bookmark):    
        kwargs = {}
        kwargs['camera'] = self
        kwargs['edit'] = True
        kwargs['setView'] = True
            
        cmds.cameraView( bookmark, **kwargs )
        
    def listBookmarks(self):
        return self.bookmarks.inputs()
    
    @_factories.addMelDocs('dolly')
    def dolly(self, distance, relative=True):
        kwargs = {}
        kwargs['distance'] = distance
        if relative:
            kwargs['relative'] = True
        else:
            kwargs['absolute'] = True
        cmds.dolly(self, **kwargs)

    @_factories.addMelDocs('roll')
    def roll(self, degree, relative=True):
        Camera(u'frontShape')
        kwargs = {}
        kwargs['degree'] = degree
        if relative:
            kwargs['relative'] = True
        else:
            kwargs['absolute'] = True
        cmds.roll(self, **kwargs)

    #TODO: the functionFactory is causing these methods to have their docs doubled-up,  in both pymel.track, and pymel.Camera.track     
    #dolly = _factories.functionFactory( cmds.dolly  )
    #roll = _factories.functionFactory( cmds.roll  )
    orbit = _factories.functionFactory( cmds.orbit  )
    track = _factories.functionFactory( cmds.track )
    tumble = _factories.functionFactory( cmds.tumble ) 
    

class Transform(DagNode):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    _componentAttributes = {'rotatePivot' : (Pivot, 'rotatePivot'), 
                            'scalePivot'  : (Pivot, 'scalePivot')}
#    def __getattr__(self, attr):
#        try :
#            return super(general.PyNode, self).__getattr__(attr)
#        except AttributeError, msg:
#            try: 
#                return self.getShape().attr(attr)
#            except AttributeError: 
#                pass
#            
#            # it doesn't exist on the class
#            try:
#                return self.attr(attr)
#            except MayaAttributeError, msg:
#                # try the shape
#                try: return self.getShape().attr(attr)
#                except AttributeError: pass
#                # since we're being called via __getattr__ we don't know whether the user was trying 
#                # to get a class method or a maya attribute, so we raise a more generic AttributeError
#                raise AttributeError, msg
 
    def __getattr__(self, attr):
        """
        Checks in the following order:
            1. Functions on this node class
            2. Attributes on this node class
            3. Functions on this node class's shape
            4. Attributes on this node class's shape
        """
        try :
            #print "Transform.__getattr__(%r)" % attr
            # Functions through normal inheritance
            res = DependNode.__getattr__(self,attr)
        except AttributeError, e:
            # Functions via shape inheritance , and then, implicitly, Attributes
            shape = self.getShape()
            if shape:
                try:
                    return getattr(shape,attr)
                except AttributeError: pass
            raise e
        
        # if compatibility mode is on then we would get an AttributeName if the attribute did not exist
        if mayahook.pymel_options.get( '0_7_compatibility_mode', True):
            import other
            if isinstance(res, other.AttributeName):
                # we didn't get a real attribute, so lets' try to get a real one on the shape
                shape = self.getShape()
                if shape:
                    shapeRes = shape.attr(attr)
                    if isinstance(shapeRes, Attribute):
                        return shapeRes
                
        return res
    
    def __setattr__(self, attr, val):
        """
        Checks in the following order:
            1. Functions on this node class
            2. Attributes on this node class
            3. Functions on this node class's shape
            4. Attributes on this node class's shape
        """
        try :
            #print "Transform.__setattr__", attr, val
            # Functions through normal inheritance
            return DependNode.__setattr__(self,attr,val)
        except AttributeError, e:
            # Functions via shape inheritance , and then, implicitly, Attributes
            #print "Trying shape"
            shape = self.getShape()
            if shape:
                try:
                    return setattr(shape,attr, val)
                except AttributeError: pass
            raise e
                         
    def attr(self, attr, checkShape=True):
        """
        when checkShape is enabled, if the attribute does not exist the transform but does on the shape, then the shape's attribute will
        be returned.
        
        :rtype: `Attribute`
        """
        #print "ATTR: Transform"
        try :
            res = DependNode.attr(self,attr)
        except general.MayaAttributeError, e:
            if checkShape:
                try: 
                    return self.getShape().attr(attr)
                except AttributeError:
                    raise e
            raise e
        
        # if compatibility mode is on then we would get an AttributeName if the attribute did not exist
        if checkShape and mayahook.pymel_options.get( '0_7_compatibility_mode', True):
            import other
            if isinstance(res, other.AttributeName):
                # we didn't get a real attribute, so lets' try to get a real one on the shape
                shape = self.getShape()
                if shape:
                    shapeRes = shape.attr(attr)
                    if isinstance(shapeRes, Attribute):
                        return shapeRes                
        return res
    
#    def __getattr__(self, attr):
#        if attr.startswith('__') and attr.endswith('__'):
#            return super(general.PyNode, self).__getattr__(attr)
#                        
#        at = Attribute( '%s.%s' % (self, attr) )
#        
#        # if the attribute does not exist on this node try the shape node
#        if not at.exists():
#            try:
#                childAttr = getattr( self.getShape(), attr)
#                try:
#                    if childAttr.exists():
#                        return childAttr
#                except AttributeError:
#                    return childAttr
#            except (AttributeError,TypeError):
#                pass
#                    
#        return at
#    
#    def __setattr__(self, attr,val):
#        if attr.startswith('_'):
#            attr = attr[1:]
#                        
#        at = Attribute( '%s.%s' % (self, attr) )
#        
#        # if the attribute does not exist on this node try the shape node
#        if not at.exists():
#            try:
#                childAttr = getattr( self.getShape(), attr )
#                try:
#                    if childAttr.exists():
#                        return childAttr.set(val)
#                except AttributeError:
#                    return childAttr.set(val)
#            except (AttributeError,TypeError):
#                pass
#                    
#        return at.set(val)
            
    """    
    def move( self, *args, **kwargs ):
        return move( self, *args, **kwargs )
    def scale( self, *args, **kwargs ):
        return scale( self, *args, **kwargs )
    def rotate( self, *args, **kwargs ):
        return rotate( self, *args, **kwargs )
    def align( self, *args, **kwargs):
        args = (self,) + args
        cmds.align(self, *args, **kwargs)
    """
    # NOTE : removed this via proxyClass
#    # workaround for conflict with translate method on basestring
#    def _getTranslate(self):
#        return self.__getattr__("translate")
#    def _setTranslate(self, val):
#        return self.__setattr__("translate", val)        
#    translate = property( _getTranslate , _setTranslate )
    
    def hide(self):
        self.visibility.set(0)
        
    def show(self):
        self.visibility.set(1)
                
    def getShape( self, **kwargs ):
        """
        :rtype: `DagNode`
        """
        kwargs['shapes'] = True
        try:
            return self.getChildren( **kwargs )[0]            
        except IndexError:
            pass
                
    def ungroup( self, **kwargs ):
        return cmds.ungroup( self, **kwargs )
    

#    @_factories.editflag('xform','scale')      
#    def setScale( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )

#    @_factories.editflag('xform','rotation')             
#    def setRotationOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
#        
#    @_factories.editflag('xform','translation')  
#    def setTranslationOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
#
#    @_factories.editflag('xform','scalePivot')  
#    def setScalePivotOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
#        
#    @_factories.editflag('xform','rotatePivot')         
#    def setRotatePivotOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
 
#    @_factories.editflag('xform','pivots')         
#    def setPivots( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
        
#    @_factories.editflag('xform','rotateAxis')  
#    def setRotateAxisOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
#        
#    @_factories.editflag('xform','shear')                                 
#    def setShearingOld( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )

    
    @_factories.editflag('xform','rotateAxis')                                
    def setMatrix( self, val, **kwargs ):
        """xform -scale"""
        if isinstance(val, datatypes.Matrix):
            val = val.toList()
    
        kwargs['matrix'] = val
        cmds.xform( self, **kwargs )

#    @_factories.queryflag('xform','scale') 
#    def getScaleOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    def _getSpaceArg(self, space, kwargs):
        "for internal use only"
        if kwargs.pop( 'worldSpace', kwargs.pop('ws', False) ):
            space = 'world'
        elif kwargs.pop( 'objectSpace', kwargs.pop('os', False) ):
            space = 'object'
        return space
    
    def _isRelativeArg(self, kwargs ):
        
        isRelative = kwargs.pop( 'relative', kwargs.pop('r', None) )
        if isRelative is None:
            isRelative = not kwargs.pop( 'absolute', kwargs.pop('a', True) )
        return isRelative
            
#    @_factories.queryflag('xform','translation') 
#    def getTranslationOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( api.MFnTransform, 'setTranslation' )
    def setTranslation(self, vector, space='object', **kwargs):
        if self._isRelativeArg(kwargs):
            return self.translateBy(vector, space, **kwargs)
        space = self._getSpaceArg(space, kwargs )
        return self._setTranslation(vector, space=space)
    
    @_factories.addApiDocs( api.MFnTransform, 'getTranslation' )
    def getTranslation(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getTranslation(space=space)

    @_factories.addApiDocs( api.MFnTransform, 'translateBy' )
    def translateBy(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        curr = self._getTranslation(space)
        self._translateBy(vector, space)
        new = self._getTranslation(space)
        undoItem = _factories.ApiUndoItem(Transform.setTranslation, (self, new, space), (self, curr, space) )
        _factories.apiUndo.append( undoItem )

    @_factories.addApiDocs( api.MFnTransform, 'setScale' )
    def setScale(self, scale, **kwargs):
        if self._isRelativeArg(kwargs):
            return self.scaleBy(scale, **kwargs)
        return self._setScale(scale)
    
    @_factories.addApiDocs( api.MFnTransform, 'scaleBy' )
    def scaleBy(self, scale, **kwargs):
        curr = self.getScale()
        self._scaleBy(scale)
        new = self.getScale()
        undoItem = _factories.ApiUndoItem(Transform.setScale, (self, new), (self, curr) )
        _factories.apiUndo.append( undoItem )

    @_factories.addApiDocs( api.MFnTransform, 'setShear' )
    def setShear(self, shear, **kwargs):
        if self._isRelativeArg(kwargs):
            return self.shearBy(shear, **kwargs)
        return self._setShear(shear)
    
    @_factories.addApiDocs( api.MFnTransform, 'shearBy' )
    def shearBy(self, shear, **kwargs):
        curr = self.getShear()
        self._shearBy(shear)
        new = self.getShear()
        undoItem = _factories.ApiUndoItem(Transform.setShear, (self, new), (self, curr) )
        _factories.apiUndo.append( undoItem )
         
        
#    @_factories.queryflag('xform','rotatePivot')        
#    def getRotatePivotOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( api.MFnTransform, 'setRotatePivot' )
    def setRotatePivot(self, point, space='object', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivot(point, space=space, balance=balance) 
    
    @_factories.addApiDocs( api.MFnTransform, 'rotatePivot' )
    def getRotatePivot(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivot(space=space)

    @_factories.addApiDocs( api.MFnTransform, 'setRotatePivotTranslation' )
    def setRotatePivotTranslation(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivotTranslation(vector, space=space)
    
    @_factories.addApiDocs( api.MFnTransform, 'rotatePivotTranslation' )
    def getRotatePivotTranslation(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivotTranslation(space=space)

 
#    @_factories.queryflag('xform','rotation')        
#    def getRotationOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( api.MFnTransform, 'setRotation' )
    def setRotation(self, rotation, space='object', **kwargs):
        # quaternions are the only method that support a space parameter
        if self._isRelativeArg(kwargs):
            return self.rotateBy(rotation, space, **kwargs)
        space = self._getSpaceArg(space, kwargs )
        rotation = list(rotation)

        rotation = [ datatypes.Angle( x ).asRadians() for x in rotation ]

        quat = api.MEulerRotation( *rotation ).asQuaternion()
        api.MFnTransform(self.__apiobject__()).setRotation(quat, datatypes.Spaces.getIndex(space) )
      
#    @_factories.addApiDocs( api.MFnTransform, 'getRotation' )
#    def getRotation(self, space='object', **kwargs):
#        # quaternions are the only method that support a space parameter
#        space = self._getSpaceArg(space, kwargs )
#        quat = api.MQuaternion()
#        api.MFnTransform(self.__apimfn__()).getRotation(quat, datatypes.Spaces.getIndex(space) )
#        return datatypes.EulerRotation( quat.asEulerRotation() )

    @_factories.addApiDocs( api.MFnTransform, 'getRotation' )
    def getRotation(self, space='object', **kwargs):
        # quaternions are the only method that support a space parameter
        space = self._getSpaceArg(space, kwargs )
        #return self._getRotation(space=space).asEulerRotation()
        e = self._getRotation(space=space).asEulerRotation()
        e.setDisplayUnit( datatypes.Angle.getUIUnit() )
        return e

    
    @_factories.addApiDocs( api.MFnTransform, 'rotateBy' )
    def rotateBy(self, rotation, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        curr = self.getRotation(space)
        self._rotateBy(rotation, space)
        new = self.getRotation(space)
        undoItem = _factories.ApiUndoItem(Transform.setRotation, (self, new, space), (self, curr, space) )
        _factories.apiUndo.append( undoItem )


#    @_factories.queryflag('xform','scalePivot') 
#    def getScalePivotOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( api.MFnTransform, 'setScalePivotTranslation' )
    def setScalePivot(self, point, space='object', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivotTranslation(point, space=space, balance=balance)
    
    @_factories.addApiDocs( api.MFnTransform, 'scalePivot' )
    def getScalePivot(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getScalePivot(space=space)

    @_factories.addApiDocs( api.MFnTransform, 'setScalePivotTranslation' )
    def setScalePivotTranslation(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivotTranslation(vector, space=space)
          
    @_factories.addApiDocs( api.MFnTransform, 'scalePivotTranslation' )
    def getScalePivotTranslation(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getScalePivotTranslation(space=space)
    
    @_factories.queryflag('xform','pivots') 
    def getPivots( self, **kwargs ):
        res = cmds.xform( self, **kwargs )
        return ( datatypes.Vector( res[:3] ), datatypes.Vector( res[3:] )  )
    
    @_factories.queryflag('xform','rotateAxis') 
    def getRotateAxis( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )
        
#    @_factories.queryflag('xform','shear')                          
#    def getShearOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.queryflag('xform','matrix')                
    def getMatrix( self, **kwargs ): 
        return datatypes.Matrix( cmds.xform( self, **kwargs ) )
      
    #TODO: create API equivalent of `xform -boundingBoxInvisible` so we can replace this with api.
    def getBoundingBox(self, invisible=False, space='object'):
        """xform -boundingBox and xform -boundingBoxInvisible
        
        :rtype: `BoundingBox`
        
        
        """
        kwargs = {'query' : True }    
        if invisible:
            kwargs['boundingBoxInvisible'] = True
        else:
            kwargs['boundingBox'] = True
        if space=='object':
            kwargs['objectSpace'] = True
        elif space=='world':
            kwargs['worldSpace'] = True
        else:
            raise ValueError('unknown space %r' % space)
                    
        res = cmds.xform( self, **kwargs )
        #return ( datatypes.Vector(res[:3]), datatypes.Vector(res[3:]) )
        return datatypes.BoundingBox( res[:3], res[3:] )
    
    def getBoundingBoxMin(self, invisible=False, space='object'):
        """
        :rtype: `Vector`
        """
        return self.getBoundingBox(invisible, space)[0]
        #return self.getBoundingBox(invisible).min()
    
    def getBoundingBoxMax(self, invisible=False, space='object'):
        """
        :rtype: `Vector`
        """
        return self.getBoundingBox(invisible, space)[1]   
        #return self.getBoundingBox(invisible).max()
    '''        
    def centerPivots(self, **kwargs):
        """xform -centerPivots"""
        kwargs['centerPivots'] = True
        cmds.xform( self, **kwargs )
        
    def zeroTransformPivots(self, **kwargs):
        """xform -zeroTransformPivots"""
        kwargs['zeroTransformPivots'] = True
        cmds.xform( self, **kwargs )        
    '''

class Joint(Transform):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    connect = _factories.functionFactory( cmds.connectJoint, rename='connect')
    disconnect = _factories.functionFactory( cmds.disconnectJoint, rename='disconnect')
    insert = _factories.functionFactory( cmds.insertJoint, rename='insert')

if version.isUnlimited():
    class FluidEmitter(Transform):
        __metaclass__ = _factories.MetaMayaNodeWrapper
        fluidVoxelInfo = _factories.functionFactory( cmds.fluidVoxelInfo, rename='fluidVoxelInfo')
        loadFluid = _factories.functionFactory( cmds.loadFluid, rename='loadFluid')
        resampleFluid = _factories.functionFactory( cmds.resampleFluid, rename='resampleFluid')
        saveFluid = _factories.functionFactory( cmds.saveFluid, rename='saveFluid')
        setFluidAttr = _factories.functionFactory( cmds.setFluidAttr, rename='setFluidAttr')
        getFluidAttr = _factories.functionFactory( cmds.getFluidAttr, rename='getFluidAttr')
    
class RenderLayer(DependNode):
    def listMembers(self, fullNames=True):
        if fullNames:
            return map( general.PyNode, util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=True) ) )
        else:
            return util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=False) )
        
    def addMembers(self, members, noRecurse=True):
        cmds.editRenderLayerMembers( self, members, noRecurse=noRecurse )

    def removeMembers(self, members ):
        cmds.editRenderLayerMembers( self, members, remove=True )
 
    def listAdjustments(self):
        return map( general.PyNode, util.listForNone( cmds.editRenderLayerAdjustment( layer=self, q=1) ) )
      
    def addAdjustments(self, members, noRecurse):
        return cmds.editRenderLayerMembers( self, members, noRecurse=noRecurse )

    def removeAdjustments(self, members ):
        return cmds.editRenderLayerMembers( self, members, remove=True )      
    
    def setCurrent(self):
        cmds.editRenderLayerGlobals( currentRenderLayer=self)    

class DisplayLayer(DependNode):
    def listMembers(self, fullNames=True):
        if fullNames:
            return map( general.PyNode, util.listForNone( cmds.editDisplayLayerMembers( self, q=1, fullNames=True) ) )
        else:
            return util.listForNone( cmds.editDisplayLayerMembers( self, q=1, fullNames=False) )
        
    def addMembers(self, members, noRecurse=True):
        cmds.editDisplayLayerMembers( self, members, noRecurse=noRecurse )

    def removeMembers(self, members ):
        cmds.editDisplayLayerMembers( self, members, remove=True )
        
    def setCurrent(self):
        cmds.editDisplayLayerMembers( currentDisplayLayer=self)  
    
class Constraint(Transform):
    def setWeight( self, weight, *targetObjects ):
        inFunc = getattr( cmds, self.type() )
        if not targetObjects:
            targetObjects = self.getTargetList() 
        
        constraintObj = self.constraintParentInverseMatrix.inputs()[0]    
        args = list(targetObjects) + [constraintObj]
        return inFunc(  *args, **{'edit':True, 'weight':weight} )
        
    def getWeight( self, *targetObjects ):
        inFunc = getattr( cmds, self.type() )
        if not targetObjects:
            targetObjects = self.getTargetList() 
        
        constraintObj = self.constraintParentInverseMatrix.inputs()[0]    
        args = list(targetObjects) + [constraintObj]
        return inFunc(  *args, **{'query':True, 'weight':True} )

class GeometryShape(DagNode):
    def __getattr__(self, attr):
        #print "Mesh.__getattr__", attr
        try:
            return self.comp(attr)
        except general.MayaComponentError:
            #print "getting super", attr
            return super(GeometryShape,self).__getattr__(attr)
            
class DeformableShape(GeometryShape):
    @classmethod
    def _numCVsFunc_generator(cls, formFunc, spansPlusDegreeFunc, spansFunc,
                              name=None, doc=None):
        """
        Intended to be used by NurbsCurve / NurbsSurface to generate
        functions which give the 'true' number of editable CVs,
        as opposed to just numSpans + degree.
        (The two values will differ if we have a periodic curve).
        
        Note that this will usually need to be called outside/after the
        class definition, as formFunc/spansFunc/etc will not be defined
        until then, as they are added by the metaclass.
        """
        def _numCvs_generatedFunc(self, editableOnly=True):
            if editableOnly and formFunc(self) == self.Form.periodic:
                return spansFunc(self)
            else:
                return spansPlusDegreeFunc(self)
        if name:
            _numCvs_generatedFunc.__name__ = name
        if doc:
            _numCvs_generatedFunc.__doc__ = doc
        return _numCvs_generatedFunc
    
    @classmethod
    def _numEPsFunc_generator(cls, formFunc, spansFunc,
                              name=None, doc=None):
        """
        Intended to be used by NurbsCurve / NurbsSurface to generate
        functions which give the 'true' number of editable EPs,
        as opposed to just numSpans.
        (The two values will differ if we have a periodic curve).
        
        Note that this will usually need to be called outside/after the
        class definition, as formFunc/spansFunc will not be defined
        until then, as they are added by the metaclass.
        """
        def _numEPs_generatedFunc(self, editableOnly=True):
            if editableOnly and formFunc(self) == self.Form.periodic:
                return spansFunc(self)
            else:
                return spansFunc(self) + 1
        if name:
            _numEPs_generatedFunc.__name__ = name
        if doc:
            _numEPs_generatedFunc.__doc__ = doc
        return _numEPs_generatedFunc    
        
class ControlPoint(DeformableShape): pass
class CurveShape(DeformableShape): pass
class NurbsCurve(CurveShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    _componentAttributes = {'u'           : NurbsCurveParameter,
                            'cv'          : NurbsCurveCV,
                            'conrolVerts' : NurbsCurveCV,
                            'ep'          : NurbsCurveEP,
                            'editPoints'  : NurbsCurveEP,
                            'knot'        : NurbsCurveKnot,    
                            'knots'       : NurbsCurveKnot}
# hard coding the mapping of numCVs => _numCVs for now,
# instead of using apiToMelBridge, as caches are in a state of flux
# for now
# can leave this in, or always move it to apiToMelBridge later...
NurbsCurve._numCVs = NurbsCurve.numCVs
NurbsCurve.numCVs = \
    NurbsCurve._numCVsFunc_generator(NurbsCurve.form,
                                     NurbsCurve._numCVs,
                                     NurbsCurve.numSpans,
                                     name='numCVs',
                                     doc =
        """
        Returns the number of CVs.
        
        :Parameters:
        editableOnly : `bool`
            If editableOnly evaluates to True (default), then this will return
            the number of cvs that can be actually edited (and also the highest
            index that may be used for cv's - ie, if
                myCurve.numCVs(editableOnly=True) == 4
            then allowable cv indices go from
                myCurve.cv[0] to mySurf.cv[3]
            
            If editablyOnly is False, then this will return the underlying
            number of cvs used to define the mathematical curve -
            degree + numSpans.
            
            These will only differ if the form is 'periodic', in which
            case the editable number will be numSpans (as the last 'degree'
            cv's are 'locked' to be the same as the first 'degree' cvs).
            In all other cases, the number of cvs will be degree + numSpans.
        
        :Examples:
            >>> # a periodic curve
            >>> myCurve = PyNode(curve(name='periodicCurve', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] ))
            >>> myCurve.cv
            NurbsCurveCV(u'periodicCurveShape.cv[0:7]')
            >>> myCurve.numCVs()
            8
            >>> myCurve.numCVs(editableOnly=False)
            11

            >>> # an open curve
            >>> myCurve = PyNode(curve(name='openCurve', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] ))
            >>> myCurve.cv
            NurbsCurveCV(u'openCurveShape.cv[0:10]')
            >>> myCurve.numCVs()
            11
            >>> myCurve.numCVs(editableOnly=False)
            11

        :rtype: `int`
        """)

NurbsCurve.numEPs = \
    NurbsCurve._numEPsFunc_generator(NurbsCurve.form,
                                       NurbsCurve.numSpans,
                                       name='numEPs',
                                       doc =
        """
        Returns the number of EPs.
        
        :Examples:
            >>> # a periodic curve
            >>> myCurve = PyNode(curve(name='periodicCurve', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] ))
            >>> myCurve.ep
            NurbsCurveEP(u'periodicCurveShape.ep[0:7]')
            >>> myCurve.numEPs()
            8

            >>> # an open curve
            >>> myCurve = PyNode(curve(name='openCurve', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] ))
            >>> myCurve.ep
            NurbsCurveEP(u'openCurveShape.ep[0:8]')
            >>> myCurve.numEPs()
            9

        :rtype: `int`
        """)



class SurfaceShape(ControlPoint): pass

class NurbsSurface(SurfaceShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    _componentAttributes = {'u'           : (NurbsSurfaceRange, 'u'),
                            'uIsoparm'    : (NurbsSurfaceRange, 'u'),
                            'v'           : (NurbsSurfaceRange, 'v'),
                            'vIsoparm'    : (NurbsSurfaceRange, 'v'),
                            'uv'          : (NurbsSurfaceRange, 'uv'),
                            'cv'          : NurbsSurfaceCV,
                            'conrolVerts' : NurbsSurfaceCV,
                            'ep'          : NurbsSurfaceEP,
                            'editPoints'  : NurbsSurfaceEP,
                            'knot'        : NurbsSurfaceKnot,
                            'knots'       : NurbsSurfaceKnot,
                            'sf'          : NurbsSurfaceFace,
                            'faces'       : NurbsSurfaceFace}
# hard coding the mapping of numCVs => _numCVs for now,
# instead of using apiToMelBridge, as caches are in a state of flux
# for now
# can leave this in, or always move it to apiToMelBridge later...
NurbsSurface._numCVsInU = NurbsSurface.numCVsInU
NurbsSurface.numCVsInU = \
    NurbsSurface._numCVsFunc_generator(NurbsSurface.formInU,
                                       NurbsSurface._numCVsInU,
                                       NurbsSurface.numSpansInU,
                                       name='numCVsInU',
                                       doc =
        """
        Returns the number of CVs in the U direction.
        
        :Parameters:
        editableOnly : `bool`
            If editableOnly evaluates to True (default), then this will return
            the number of cvs that can be actually edited (and also the highest
            index that may be used for u - ie, if
                mySurf.numCVsInU(editableOnly=True) == 4
            then allowable u indices go from
                mySurf.cv[0][*] to mySurf.cv[3][*]
            
            If editablyOnly is False, then this will return the underlying
            number of cvs used to define the mathematical curve in u -
            degreeU + numSpansInU.
            
            These will only differ if the form in u is 'periodic', in which
            case the editable number will be numSpansInU (as the last 'degree'
            cv's are 'locked' to be the same as the first 'degree' cvs).
            In all other cases, the number of cvs will be degreeU + numSpansInU.
                    
        :Examples:
            >>> # a periodic surface
            >>> mySurf = PyNode(surface(name='periodicSurf', du=3, dv=1, fu='periodic', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.cv[*][0]
            NurbsCurveCV(u'periodicSurfShape.cv[0:7][0]')
            >>> mySurf.numCVsInU()
            8
            >>> mySurf.numCVsInU(editableOnly=False)
            11

            >>> # an open surface
            >>> mySurf = PyNode(surface(name='openSurf', du=3, dv=1, fu='open', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=((4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)) ))
            >>> mySurf.cv[*][0]
            NurbsCurveCV(u'openSurfShape.cv[0:10][0]')
            >>> mySurf.numCVsInU()
            11
            >>> mySurf.numCVsInU(editableOnly=False)
            11        

        :rtype: `int`
        """)
# hard coding the mapping of numCVs => _numCVs for now,
# instead of using apiToMelBridge, as caches are in a state of flux
# for now
# can leave this in, or always move it to apiToMelBridge later...
NurbsSurface._numCVsInV = NurbsSurface.numCVsInV
NurbsSurface.numCVsInV = \
    NurbsSurface._numCVsFunc_generator(NurbsSurface.formInV,
                                       NurbsSurface._numCVsInV,
                                       NurbsSurface.numSpansInV,
                                       name='numCVsInV',
                                       doc =
        """
        Returns the number of CVs in the V direction.
        
        :Parameters:
        editableOnly : `bool`
            If editableOnly evaluates to True (default), then this will return
            the number of cvs that can be actually edited (and also the highest
            index that may be used for v - ie, if
                mySurf.numCVsInV(editableOnly=True) == 4
            then allowable v indices go from
                mySurf.cv[*][0] to mySurf.cv[*][3]
            
            If editablyOnly is False, then this will return the underlying
            number of cvs used to define the mathematical curve in v -
            degreeV + numSpansInV.
            
            These will only differ if the form in v is 'periodic', in which
            case the editable number will be numSpansInV (as the last 'degree'
            cv's are 'locked' to be the same as the first 'degree' cvs).
            In all other cases, the number of cvs will be degreeV + numSpansInV.

        :Examples:
            >>> # a periodic surface
            >>> mySurf = PyNode(surface(name='periodicSurf', du=1, dv=3, fu='open', fv='periodic', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.cv[0][*]
            NurbsCurveCV(u'periodicSurfShape.cv[0][0:7]')
            >>> mySurf.numCVsInV()
            8
            >>> mySurf.numCVsInV(editableOnly=False)
            11

            >>> # an open surface
            >>> mySurf = PyNode(surface(name='openSurf', du=1, dv=3, fu='open', fv='open', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.cv[0][*]
            NurbsCurveCV(u'openSurfShape.cv[0][0:10]')
            >>> mySurf.numCVsInV()
            11
            >>> mySurf.numCVsInV(editableOnly=False)
            11        
            
        :rtype: `int`
        """)

NurbsSurface.numEPsInU = \
    NurbsSurface._numEPsFunc_generator(NurbsSurface.formInU,
                                       NurbsSurface.numSpansInU,
                                       name='numEPsInU',
                                       doc =
        """
        Returns the number of EPs in the U direction.

        :Examples:
            >>> # a periodic surface
            >>> mySurf = PyNode(surface(name='periodicSurf', du=3, dv=1, fu='periodic', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.ep[*][0]
            NurbsCurveEP(u'periodicSurfShape.ep[0:7][0]')
            >>> mySurf.numEPsInV()
            8

            >>> # an open surface
            >>> mySurf = PyNode(surface(name='openSurf', du=3, dv=1, fu='open', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.ep[*][0]
            NurbsCurveEP(u'openSurfShape.ep[0:8][0]')
            >>> mySurf.numEPsInV()
            9
                    
        :rtype: `int`
        """)

NurbsSurface.numEPsInV = \
    NurbsSurface._numEPsFunc_generator(NurbsSurface.formInV,
                                       NurbsSurface.numSpansInV,
                                       name='numEPsInV',
                                       doc =
        """
        Returns the number of EPs in the V direction.
        
        :Examples:
            >>> # a periodic surface
            >>> mySurf = PyNode(surface(name='periodicSurf', du=1, dv=3, fu='open', fv='periodic', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.ep[0][*]
            NurbsCurveEP(u'periodicSurfShape.ep[0][0:7]')
            >>> mySurf.numEPsInV()
            8

            >>> # an open surface
            >>> mySurf = PyNode(surface(name='openSurf', du=1, dv=3, fu='open', fv='open', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] ))
            >>> mySurf.ep[0][*]
            NurbsCurveEP(u'openSurfShape.ep[0][0:8]')
            >>> mySurf.numEPsInV()
            9
                    
        :rtype: `int`
        """)


class Mesh(SurfaceShape):
    """
    The Mesh class provides wrapped access to many API methods for querying and modifying meshes.  Be aware that 
    modifying meshes using API commands outside of the context of a plugin is still somewhat uncharted territory,
    so proceed at our own risk. 
    
   
    The component types can be accessed from the `Mesh` type (or it's transform) using the names you are
    familiar with from MEL:

        >>> from pymel.all import *
        >>> p = polySphere( name='theMoon', sa=7, sh=7 )[0]
        >>> p.vtx
        MeshVertex(u'theMoonShape.vtx[0:43]')
        >>> p.e
        MeshEdge(u'theMoonShape.e[0:90]')
        >>> p.f
        MeshFace(u'theMoonShape.f[0:48]')
        
    They are also accessible from their more descriptive alternatives:
    
        >>> p.verts
        MeshVertex(u'theMoonShape.vtx[0:43]')
        >>> p.edges
        MeshEdge(u'theMoonShape.e[0:90]')
        >>> p.faces
        MeshFace(u'theMoonShape.f[0:48]')
     
    As you'd expect, these components are all indexible:
     
        >>> p.vtx[0]
        MeshVertex(u'theMoonShape.vtx[0]')
        
    The classes themselves contain methods for getting information about the component.
     
        >>> p.vtx[0].connectedEdges()
        MeshEdge(u'theMoonShape.e[0,6,42,77]')
      
    This class provides support for python's extended slice notation. Typical maya ranges express a start and stop value separated
    by a colon.  Extended slices add a step parameter and can also represent multiple ranges separated by commas. 
    Thus, a single component object can represent any collection of indices.
    
    This includes start, stop, and step values.
    
        >>> # do every other edge between 0 and 10
        >>> for edge in p.e[0:10:2]: 
        ...     print edge
        ... 
        theMoonShape.e[0]
        theMoonShape.e[2]
        theMoonShape.e[4]
        theMoonShape.e[6]
        theMoonShape.e[8]
        theMoonShape.e[10]

    Negative indices can be used for getting indices relative to the end:
    
        >>> p.edges  # the full range
        MeshEdge(u'theMoonShape.e[0:90]')
        >>> p.edges[5:-10]  # index 5 through to 10 from the last
        MeshEdge(u'theMoonShape.e[5:80]')
    
    Just like with python ranges, you can leave an index out, and the logical result will follow:
    
        >>> p.edges[:-10]  # from the beginning 
        MeshEdge(u'theMoonShape.e[0:80]')
        >>> p.edges[20:]
        MeshEdge(u'theMoonShape.e[20:90]')
        
    Or maybe you want the position of every tenth vert:
    
        >>> for x in p.vtx[::10]: 
        ...     print x, x.getPosition()
        ... 
        theMoonShape.vtx[0] [0.270522117615, -0.900968849659, -0.339223951101]
        theMoonShape.vtx[10] [-0.704405844212, -0.623489797115, 0.339223951101]
        theMoonShape.vtx[20] [0.974927902222, -0.222520858049, 0.0]
        theMoonShape.vtx[30] [-0.704405784607, 0.623489797115, -0.339224010706]
        theMoonShape.vtx[40] [0.270522087812, 0.900968849659, 0.339223980904]

    
    To be compatible with Maya's range notation, these slices are inclusive of the stop index.
    
        >>> # face at index 8 will be included in the sequence
        >>> for f in p.f[4:8]: print f  
        ... 
        theMoonShape.f[4]
        theMoonShape.f[5]
        theMoonShape.f[6]
        theMoonShape.f[7]
        theMoonShape.f[8]

    >>> from pymel.all import *
    >>> obj = polyTorus()[0]
    >>> colors = []
    >>> for i, vtx in enumerate(obj.vtx):
    ...     edgs=vtx.toEdges()
    ...     totalLen=0
    ...     edgCnt=0
    ...     for edg in edgs:
    ...         edgCnt += 1
    ...         l = edg.getLength()
    ...         totalLen += l
    ...     avgLen=totalLen / edgCnt
    ...     #print avgLen
    ...     currColor = vtx.getColor(0)
    ...     color = datatypes.Color.black
    ...     # only set blue if it has not been set before
    ...     if currColor.b<=0.0:
    ...         color.b = avgLen
    ...     color.r = avgLen
    ...     colors.append(color)
    
    
    """
    __metaclass__ = _factories.MetaMayaNodeWrapper
#    def __init__(self, *args, **kwargs ):      
#        SurfaceShape.__init__(self, self._apiobject )
#        self.vtx = MeshEdge(self.__apimobject__() )
    _componentAttributes = {'vtx'   : MeshVertex,
                            'verts' : MeshVertex,
                            'e'     : MeshEdge,
                            'edges' : MeshEdge,
                            'f'     : MeshFace,
                            'faces' : MeshFace,
                            'map'   : MeshUV,
                            'uvs'   : MeshUV,
                            'vtxFace'   : MeshVertexFace,
                            'faceVerts' : MeshVertexFace}
                        
    vertexCount =  mayahook.deprecated( "Use 'numVertices' instead.")( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertex', 'vertexCount' ))
    edgeCount =    mayahook.deprecated( "Use 'numEdges' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edge', 'edgeCount' ))
    faceCount =    mayahook.deprecated( "Use 'numFaces' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate,  'face', 'faceCount' ))
    uvcoordCount = mayahook.deprecated( "Use 'numUVs' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'uvcoord', 'uvcoordCount' ))
    triangleCount = mayahook.deprecated( "Use 'numTriangles' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangle', 'triangleCount' ))
    
    numTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangles', 'numTriangles' )
    numSelectedTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangleComponent', 'numSelectedTriangles' )
    numSelectedFaces = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'faceComponent', 'numSelectedFaces' )
    numSelectedEdges = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edgeComponent', 'numSelectedEdges' )
    numSelectedVertices = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertexComponent', 'numSelectedVertices' )
     
    area = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'area'  )
    worldArea = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'worldArea' )
    
    if version.CURRENT >= version.v2009:
        @_factories.addApiDocs( api.MFnMesh, 'currentUVSetName' )  
        def getCurrentUVSetName(self):
            return self.__apimfn__().currentUVSetName( self.instanceNumber() )
        
        @_factories.addApiDocs( api.MFnMesh, 'currentColorSetName' )
        def getCurrentColorSetName(self):
            return self.__apimfn__().currentColorSetName( self.instanceNumber() )
        
    else:
        @_factories.addApiDocs( api.MFnMesh, 'currentUVSetName' )  
        def getCurrentUVSetName(self):
            return self.__apimfn__().currentUVSetName()
    
        @_factories.addApiDocs( api.MFnMesh, 'currentColorSetName' )
        def getCurrentColorSetName(self):
            return self.__apimfn__().currentColorSetName()
        
    @_factories.addApiDocs( api.MFnMesh, 'numColors' )
    def numColors(self, colorSet=None):
        args = []
        if colorSet:
            args.append(colorSet)
        return self.__apimfn__().numColors(*args)
     
class Subdiv(SurfaceShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    
    _componentAttributes = {'smp'   : SubdVertex,
                            'verts' : SubdVertex,
                            'sme'   : SubdEdge,
                            'edges' : SubdEdge,
                            'smf'   : SubdFace,
                            'faces' : SubdFace,
                            'smm'   : SubdUV,
                            'uvs'   : SubdUV}
        
    def getTweakedVerts(self, **kwargs):
        return cmds.querySubdiv( action=1, **kwargs )
        
    def getSharpenedVerts(self, **kwargs):
        return cmds.querySubdiv( action=2, **kwargs )
        
    def getSharpenedEdges(self, **kwargs):
        return cmds.querySubdiv( action=3, **kwargs )
        
    def getEdges(self, **kwargs):
        return cmds.querySubdiv( action=4, **kwargs )
                
    def cleanTopology(self):
        cmds.subdCleanTopology(self)

class Lattice(ControlPoint):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    _componentAttributes = {'pt'    : LatticePoint,
                            'points': LatticePoint}
        
class Particle(DeformableShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    
    class PointArray(ComponentArray):
        def __init__(self, name):
            ComponentArray.__init__(self, name)
            self.returnClass = Particle.Point

        def __len__(self):
            return cmds.particle(self.node(), q=1,count=1)        
        
    class Point(_Component):
        def __str__(self):
            return '%s.pt[%s]' % (self._node, self._item)
        def __getattr__(self, attr):
            return cmds.particle( self._node, q=1, attribute=attr, order=self._item)
            
    
    def _getPointArray(self):
        return Particle.PointArray( self + '.pt' )    
    pt = property(_getPointArray)
    points = property(_getPointArray)
    
    def pointCount(self):
        return cmds.particle( self, q=1,count=1)
    num = pointCount

class SelectionSet( api.MSelectionList):
    apicls = api.MSelectionList
    __metaclass__ = _factories.MetaMayaTypeWrapper

    def __init__(self, objs):
        """ can be initialized from a list of objects, another SelectionSet, an MSelectionList, or an ObjectSet"""
        if isinstance(objs, api.MSelectionList ):
            api.MSelectionList.__init__(self, objs)
            
        elif isinstance(objs, ObjectSet ):
            api.MSelectionList.__init__(self, objs.asSelectionSet() )
            
        else:
            api.MSelectionList.__init__(self)
            for obj in objs:
                if isinstance(obj, (DependNode, DagNode) ):
                    self.apicls.add( self, obj.__apiobject__() )
                elif isinstance(obj, Attribute):
                    self.apicls.add( self, obj.__apiobject__(), True )
    #            elif isinstance(obj, Component):
    #                sel.add( obj.__apiobject__(), True )
                elif isinstance( obj, basestring ):
                    self.apicls.add( self, obj )
                else:
                    raise TypeError
                
    def __melobject__(self):
        # If the list contains components, THEIR __melobject__ is a list -
        # so need to iterate through, and flatten if needed
        melList = []
        for selItem in self:
            selItem = selItem.__melobject__()
            if util.isIterable(selItem):
                melList.extend(selItem)
            else:
                melList.append(selItem)
        return melList
    
    def __len__(self):
        """:rtype: `int` """
        return self.apicls.length(self)
    
    def __contains__(self, item):
        """:rtype: `bool` """
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.apicls.hasItem(self, item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.hasItem(self, general.PyNode(item).__apiobject__())

    def __repr__(self):
        """:rtype: `str` """
        names = []
        self.apicls.getSelectionStrings( self, names )
        return '%s(%s)' % ( self.__class__.__name__, names )

        
    def __getitem__(self, index):
        """:rtype: `general.PyNode` """
        if index >= len(self):
            raise IndexError, "index out of range"
        
        plug = api.MPlug()
        obj = api.MObject()
        dag = api.MDagPath()
        comp = api.MObject()
        
        # Go from most specific to least - plug, dagPath, dependNode
        try:
            self.apicls.getPlug( self, index, plug )
        except RuntimeError:
            try:
                self.apicls.getDagPath( self, index, dag, comp )
            except RuntimeError:
                try:
                    self.apicls.getDependNode( self, index, obj )
                    return general.PyNode( obj )
                except:
                    pass
            else:
                if comp.isNull():
                    return general.PyNode( dag )
                else:
                    return general.PyNode( dag, comp )
        else:
            return general.PyNode( plug )

                
    def __setitem__(self, index, item):
        
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.apicls.replace(self, index, item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.replace(self, general.PyNode(item).__apiobject__())
        
    def __and__(self, s):
        "operator for `SelectionSet.getIntersection`"
        return self.getIntersection(s)

    def __iand__(self, s):
        "operator for `SelectionSet.intersection`"
        return self.intersection(s)
       
    def __or__(self, s):
        "operator for `SelectionSet.getUnion`"
        return self.getUnion(s)

    def __ior__(self, s):
        "operator for `SelectionSet.union`"
        return self.union(s)

    def __lt__(self, s):
        "operator for `SelectionSet.isSubSet`"
        return self.isSubSet(s)

    def __gt__(self, s):
        "operator for `SelectionSet.isSuperSet`"
        return self.isSuperSet(s)
                    
    def __sub__(self, s):
        "operator for `SelectionSet.getDifference`"
        return self.getDifference(s)

    def __isub__(self, s):
        "operator for `SelectionSet.difference`"
        return self.difference(s)       
    
    def __xor__(self, s):
        "operator for `SelectionSet.symmetricDifference`"
        return self.getSymmetricDifference(s)

    def __ixor__(self, s):
        "operator for `SelectionSet.symmetricDifference`"
        return self.symmetricDifference(s)     
     
    def add(self, item):
        
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.apicls.add(self, item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.add(self, general.PyNode(item).__apiobject__())
        
     
    def pop(self, index):
        """:rtype: `general.PyNode` """
        if index >= len(self):
            raise IndexError, "index out of range"
        return self.apicls.remove(self, index )
    

    def isSubSet(self, other):
        """:rtype: `bool`"""
        if isinstance(other, ObjectSet):
            other = other.asSelectionSet()
        return set(self).issubset(other)
    
    def isSuperSet(self, other, flatten=True ):
        """:rtype: `bool`"""
        if isinstance(other, ObjectSet):
            other = other.asSelectionSet()
        return set(self).issuperset(other)
    
    def getIntersection(self, other):
        """:rtype: `SelectionSet`"""
        # diff = self-other
        # intersect = self-diff
        diff = self.getDifference(other)
        return self.getDifference(diff)
    
    def intersection(self, other):
        diff = self.getDifference(other)
        self.difference(diff)
        
    def getDifference(self, other):
        """:rtype: `SelectionSet`"""
        # create a new SelectionSet so that we don't modify our current one
        newSet = SelectionSet( self )
        newSet.difference(other)
        return newSet
    
    def difference(self, other):
        if not isinstance( other, api.MSelectionList ):
            other = SelectionSet( other )
        self.apicls.merge( self, other, api.MSelectionList.kRemoveFromList )
    
    def getUnion(self, other):
        """:rtype: `SelectionSet`"""
        newSet = SelectionSet( self )
        newSet.union(other)
        return newSet
    
    def union(self, other):
        if not isinstance( other, api.MSelectionList ):
            other = SelectionSet( other )
        self.apicls.merge( self, other, api.MSelectionList.kMergeNormal )
        
        
    def getSymmetricDifference(self, other):
        """
        Also known as XOR
        
        :rtype: `SelectionSet`
        """
        # create a new SelectionSet so that we don't modify our current one
        newSet = SelectionSet( self )
        newSet.symmetricDifference(other)
        return newSet
    
    def symmetricDifference(self, other):
        if not isinstance( other, api.MSelectionList ):
            other = SelectionSet( other )
        self.apicls.merge( self, other, api.MSelectionList.kXOR )

    def asObjectSet(self):
        return general.sets( self )
#    def intersect(self, other):
#        self.apicls.merge( other, api.MSelectionList.kXORWithList )
    

       
class ObjectSet(Entity):
    """
    The ObjectSet class and `SelectionSet` class work together.  Both classes have a very similar interface,
    the primary difference is that the ObjectSet class represents connections to an objectSet node, while the
    `SelectionSet` class is a generic set, akin to pythons built-in `set`. 
 
    
    create some sets:
    
        >>> from pymel.all import *
        >>> f=newFile(f=1) #start clean
        >>> 
        >>> s = sets()  # create an empty set
        >>> s.union( ls( type='camera') )  # add some cameras to it
        >>> s.members()  # doctest: +SKIP
        [Camera(u'sideShape'), Camera(u'frontShape'), Camera(u'topShape'), Camera(u'perspShape')]
        >>> sel = s.asSelectionSet() # or as a SelectionSet
        >>> sel # doctest: +SKIP
        SelectionSet([u'sideShape', u'frontShape', u'topShape', u'perspShape'])
        >>> sorted(sel) # as a sorted list
        [Camera(u'frontShape'), Camera(u'perspShape'), Camera(u'sideShape'), Camera(u'topShape')]
        
    Operations between sets result in `SelectionSet` objects:
    
        >>> t = sets()  # create another set
        >>> t.add( 'perspShape' )  # add the persp camera shape to it
        >>> s.getIntersection(t)
        SelectionSet([u'perspShape'])
        >>> diff = s.getDifference(t)
        >>> diff #doctest: +SKIP
        SelectionSet([u'sideShape', u'frontShape', u'topShape'])
        >>> sorted(diff)
        [Camera(u'frontShape'), Camera(u'sideShape'), Camera(u'topShape')]
        >>> s.isSuperSet(t)
        True
        
             
        
    """

  
#        >>> u = sets( s&t ) # intersection
#        >>> print u.elements(), s.elements()
#        >>> if u < s: print "%s is a sub-set of %s" % (u, s)
#        
#    place a set inside another, take1
#    
#        >>> # like python's built-in set, the add command expects a single element
#        >>> s.add( t )
#
#    place a set inside another, take2
#    
#        >>> # like python's built-in set, the update command expects a set or a list
#        >>> t.update([u])
#
#        >>> # put the sets back where they were
#        >>> s.remove(t)
#        >>> t.remove(u)
#
#    now put the **contents** of a set into another set
#    
#        >>> t.update(u)
#
#    mixed operation between pymel.core.ObjectSet and built-in set
#        
#        >>> v = set(['polyCube3', 'pSphere3'])
#        >>> print s.intersection(v)
#        >>> print v.intersection(s)  # not supported yet
#        >>> u.clear()
#
#        >>> delete( s )
#        >>> delete( t )
#        >>> delete( u )
#        
#        
#    these will return the results of the operation as python sets containing lists of pymel node classes::
#    
#        s&t     # s.intersection(t)
#        s|t     # s.union(t)
#        s^t     # s.symmetric_difference(t)
#        s-t     # s.difference(t)
#    
#    the following will alter the contents of the maya set::
#        
#        s&=t    # s.intersection_update(t)
#        s|=t    # s.update(t)
#        s^=t    # s.symmetric_difference_update(t)
#        s-=t    # s.difference_update(t) 
#            
#    def _elements(self):
#        """ used internally to get a list of elements without casting to node classes"""
#        return sets( self, q=True)
#    #-----------------------
#    # Maya Methods
#    #-----------------------

    __metaclass__ = _factories.MetaMayaNodeWrapper
    #-----------------------
    # Python ObjectSet Methods
    #-----------------------
                    
    def __contains__(self, item):
        """:rtype: `bool` """
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.__apimfn__().isMember(item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.__apimfn__().isMember(general.PyNode(item).__apiobject__())

    def __getitem__(self, index):
        return self.asSelectionSet()[index]
                                       
    def __len__(self, s):
        """:rtype: `int`"""
        return len(self.asSelectionSet())


    #def __eq__(self, s):
    #    return s == self._elements()

    #def __ne__(self, s):
    #    return s != self._elements()
         
    def __and__(self, s):
        "operator for `ObjectSet.getIntersection`"
        return self.getIntersection(s)

    def __iand__(self, s):
        "operator for `ObjectSet.intersection`"
        return self.intersection(s)
       
    def __or__(self, s):
        "operator for `ObjectSet.getUnion`"
        return self.getUnion(s)

    def __ior__(self, s):
        "operator for `ObjectSet.union`"
        return self.union(s)

#    def __lt__(self, s):
#        "operator for `ObjectSet.isSubSet`"
#        return self.isSubSet(s)
#
#    def __gt__(self, s):
#        "operator for `ObjectSet.isSuperSet`"
#        return self.isSuperSet(s)
                    
    def __sub__(self, s):
        "operator for `ObjectSet.getDifference`"
        return self.getDifference(s)

    def __isub__(self, s):
        "operator for `ObjectSet.difference`"
        return self.difference(s)                  
    
    def __xor__(self, s):
        "operator for `ObjectSet.symmetricDifference`"
        return self.getSymmetricDifference(s)

    def __ixor__(self, s):
        "operator for `ObjectSet.symmetricDifference`"
        return self.symmetricDifference(s)     

#
#    def subtract(self, set2):
#        return sets( self, subtract=set2 )
#       
#    def add(self, element):
#        return sets( self, add=[element] )
#    
#    def clear(self):
#        return sets( self, clear=True )
#    
#    def copy(self ):
#        return sets( self, copy=True )
#    
#    def difference(self, elements):
#        if isinstance(elements,basestring):
#            elements = cmds.sets( elements, q=True)
#        return list(set(self.elements()).difference(elements))
#        
#        '''
#        if isinstance(s, ObjectSet) or isinstance(s, str):
#            return sets( s, subtract=self )
#        
#        s = sets( s )
#        res = sets( s, subtract=self )
#        cmds.delete(s)
#        return res'''
#    
#    def difference_update(self, elements ):
#        return sets( self, remove=elements)
#    
#    def discard( self, element ):
#        try:
#            return self.remove(element)
#        except TypeError:
#            pass
#
#    def intersection(self, elements):
#        if isinstance(elements,basestring):
#            elements = cmds.sets( elements, q=True)
#        return set(self.elements()).intersection(elements)
#    
#    def intersection_update(self, elements):
#        self.clear()
#        sets( self, add=self.intersections(elements) )
#            
#            
#    def remove( self, element ):
#        return sets( self, remove=[element])
#
#    def symmetric_difference(self, elements):
#        if isinstance(elements,basestring):
#            elements = cmds.sets( elements, q=True)
#        return set(self.elements()).symmetric_difference(elements)
#            
#    def union( self, elements ):
#        if isinstance(elements,basestring):
#            elements = cmds.sets( elements, q=True)
#        return set(self.elements()).union(elements)
#    
#    def update( self, set2 ):        
#        sets( self, forceElement=set2 )
    
    def members(self, flatten=False):
        """return members as a list
        :rtype: `list`
        """
        return list( self.asSelectionSet(flatten) )

    @mayahook.deprecated( 'Use ObjectSet.members instead', 'ObjectSet' )
    def elements(self, flatten=False):
        """return members as a list
        :rtype: `list`
        """
        return list( self.asSelectionSet(flatten) )
    
    def flattened(self):
        """return a flattened list of members.  equivalent to `ObjectSet.members(flatten=True)`
        :rtype: `list`
        """
        return self.members(flatten=True)
    
    def resetTo(self, newContents ):
        """clear and set the members to the passed list/set"""
        self.clear()
        self.addMembers( newContents )
    

    def add(self, item):
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.__apimfn__().addMember(item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError
        else:
            return self.__apimfn__().addMember(general.PyNode(item).__apiobject__())

    def remove(self, item):
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.__apimfn__().removeMember(item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError
        else:
            return self.__apimfn__().removeMember(general.PyNode(item).__apiobject__())
          
    def isSubSet(self, other):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSubSet(other)
    
    issubset = mayahook.deprecated( 'Use ObjectSet.isSubSet instead', 'ObjectSet' )( members ) 
    
    
    def isSuperSet(self, other ):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSuperSet(other)
    
    issuperset = mayahook.deprecated( 'Use ObjectSet.isSuperSet instead', 'ObjectSet' )( members ) 
    
    def isEqual(self, other ):
        """
        do not use __eq__ to test equality of set contents. __eq__ will only tell you if 
        the passed object is the same node, not if this set and the passed set
        have the same contents.
        :rtype: `bool` 
        """
        return self.asSelectionSet() == SelectionSet(other)
    
    
    def getDifference(self, other):
        """:rtype: `SelectionSet`"""
        sel = self.asSelectionSet()
        sel.difference(other)
        return sel
    
    def difference(self, other):
        sel = self.getDifference(other)
        self.resetTo(sel)

    def getSymmetricDifference(self, other):
        """also known as XOR
        :rtype: `SelectionSet`
        """
        sel = self.getSymmetricDifference()
        sel.difference(other)
        return sel
    
    def symmetricDifference(self, other):
        sel = self.symmetricDifference(other)
        self.resetTo(sel)
        
    def getIntersection(self, other):
        """:rtype: `SelectionSet`"""
        if isinstance(other, ObjectSet):
            return self._getIntersection(other)
        
        #elif isinstance(other, SelectionSet) or hasattr(other, '__iter__'):
        selSet = self.asSelectionSet()
        selSet.intersection(other)
        return selSet
        
        #raise TypeError, 'Cannot perform intersection with non-iterable type %s' % type(other)

    def intersection(self, other):
        sel = self.getIntersection(other)
        self.resetTo(sel)
        
        
    def getUnion(self, other):
        """:rtype: `SelectionSet`"""
        if isinstance(other, ObjectSet):
            return self._getUnion(other)
        
        selSet = self.asSelectionSet()
        selSet.union(other)
        return selSet

    def union(self, other):
        self.addMembers(other)
     
    update = mayahook.deprecated( 'Use ObjectSet.union instead', 'ObjectSet' )( members ) 


class GeometryFilter(DependNode): pass
class SkinCluster(GeometryFilter):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    
    def getWeights(self, geometry, influenceIndex=None):
        if not isinstance(geometry, general.PyNode):
            geometry = general.PyNode(geometry)
            
        if isinstance( geometry, Transform ):
            try:
                geometry = geometry.getShape()
            except:
                raise TypeError, "%s is a transform with no shape" % geometry
              
        if isinstance(geometry, GeometryShape):
            components = api.toComponentMObject( geometry.__apimdagpath__() )
        elif isinstance(geometry, Component):
            components = geometry.__apiobject__()
            
        else:
            raise TypeError
        
        if influenceIndex is not None:
            weights = api.MDoubleArray()
            self.__apimfn__().getWeights( geometry.__apimdagpath__(), components, influenceIndex, weights )
            return iter(weights)
        else:
            weights = api.MDoubleArray()
            index = api.MScriptUtil().asUintPtr()
            self.__apimfn__().getWeights( geometry.__apimdagpath__(), components, weights, index )
            index = api.MScriptUtil.getInt(index)
            args = [iter(weights)] * index
            return itertools.izip(*args)
        
    @_factories.addApiDocs( api.MFnSkinCluster, 'influenceObjects' )        
    def influenceObjects(self):
        return self._influenceObjects()[1]
    
    def numInfluenceObjects(self):
        return self._influenceObjects()[0]
             
_factories.ApiTypeRegister.register( 'MSelectionList', SelectionSet )  


def _createPyNodes():

    dynModule = util.LazyLoadModule(__name__, globals())
    
    # reset cache
    _factories.PyNodeTypesHierarchy().clear()
    _factories.PyNodeNamesToPyNodes().clear()
    
    for mayaType, parents, children in _factories.nodeHierarchy:

        if mayaType == 'dependNode': continue
        
        parentMayaType = parents[0]
        #print "superNodeType: ", superNodeType, type(superNodeType)
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue
        
        #className = util.capitalize(mayaType)
        #if className not in __all__: __all__.append( className )
        
        _factories.addPyNode( dynModule, mayaType, parentMayaType )
    
    sys.modules[__name__] = dynModule


# Initialize Pymel classes to API types lookup
#_startTime = time.time()
_createPyNodes()
#_logger.debug( "Initialized Pymel PyNodes types list in %.2f sec" % time.time() - _startTime )

dynModule = sys.modules[__name__]
#def listToMSelection( objs ):
#    sel = api.MSelectionList()
#    for obj in objs:
#        if isinstance(obj, DependNode):
#            sel.add( obj.__apiobject__() )
#        elif isinstance(obj, Attribute):
#            sel.add( obj.__apiobject__(), True )
#        elif isinstance(obj, Component):
#            pass
#            #sel.add( obj.__apiobject__(), True )
#        else:
#            raise TypeError

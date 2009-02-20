"""
Contains classes corresponding to the Maya type hierarchy, including `DependNode`, `Transform`, `Mesh`, and `Camera`.
"""
import sys, os, re

import pmcmds as cmds
import maya.mel as mm

import inspect

import pymel.util as util
import factories as _factories
from factories import queryflag, editflag, createflag, addMelDocs, addApiDocs, MetaMayaTypeWrapper, MetaMayaNodeWrapper
import pymel.api as api
import datatypes
import pymel.util.nameparse as nameparse
import pymel.util.pwarnings as pwarnings
import logging
_logger = logging.getLogger(__name__)

# to make sure Maya is up
import pymel.mayahook as mayahook
from pymel.mayahook import Version
assert mayahook.mayaInit()


from maya.cmds import about as _about
import maya.mel as mm

from general import *

from animation import listAnimatable as _listAnimatable
from system import namespaceInfo as _namespaceInfo, FileReference as _FileReference

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

#__all__ = ['Component', 'MeshEdge', 'MeshVertex', 'MeshFace', 'Attribute', 'DependNode' ]


class Component( PyNode ):
    """
    Abstract base class for pymel components, such as `MeshEdge`, `MeshVertex`, and `MeshFace`.
 
    
    
    """
    @staticmethod
    def _formatSlice(startIndex, stopIndex, step):
        if startIndex == stopIndex:
            sliceStr = '%s' % startIndex
        elif step is not None and step != 1:
            sliceStr = '%s:%s:%s' % (startIndex, stopIndex, step)
        else:
            sliceStr = '%s:%s' % (startIndex, stopIndex)
        return sliceStr 
    
    @staticmethod
    def _getRange(start, stop, step):
        if step is None or step == 1:   
            indices = range( start, stop+1 )
        else:
            indices = range( start, stop+1, step )
              
        return indices
    
    @staticmethod
    def _getMayaSlice( array ):
        """given an MIntArray, convert to a maya-formatted slice"""
        
        return [ slice( x.start, x.stop-1, x.step) for x in util.sequenceToSlice( array ) ]

    
    def isComplete(self):
        return self._range is None
          
    def __init__(self, *args, **kwargs ):
        

        
        isApiComponent = False 
        component = None
        newargs = []
        # the Component class can be instantiated several ways:
        # Component(dagPath, component): args get stored on self._node and self.__apiobjects__['MObjectHandle'] respectively
        if self._node :
            newargs.append( self._node.__apimdagpath__() )
            try:
                component = self.__apiobjects__['MObjectHandle']
                if api.isValidMObjectHandle( component ): 
                    newargs.append( component.object() )  
                    isApiComponent = True
            except KeyError:
                component = self.__apiobjects__['ComponentIndex']
            
        # Component(dagPath): in this case, stored on self.__apiobjects__['MDagPath'] (self._node will be None)
        else:
            dag = self.__apiobjects__['MDagPath']
            newargs = [dag]
            self._node = PyNode(dag)
            
        #print "ARGS", newargs   

        # DEFAULTS
        self._range = None # a list of component indices
        self._rangeIndex = 0 # an index into the range
        self._sliceStr = ''
        self._slices = None
        
        stopIndex = 0
        self.isReset = True # if the iterator is at its first item
   
        # instantiate the api component iterator    
        self.__apiobjects__['MFn'] = self.__apicls__(*newargs )
        
        
        if isApiComponent:
            startIndex = self.getIndex()
            stopIndex = startIndex + self.__apimfn__().count()-1
            if startIndex == stopIndex:
                self._sliceStr = '%s' % startIndex
            else:
                self._sliceStr = '%s:%s' % (startIndex, stopIndex)
            self._slices = [ slice(startIndex, stopIndex) ]   
            self._range = xrange( startIndex, stopIndex+1)
            
        elif isinstance(component, int):
            self._sliceStr = '%s' % component
            self._range = [component]
            su = api.MScriptUtil()
            self.__apimfn__().setIndex( component, su.asIntPtr() )  # bug workaround
            self._slices = [ slice(component,component) ]  
            
        elif isinstance(component, slice):
            
            start, stop, step = component.indices( self.__apimfn__().count()-1 )
            
            self._slices = [ component ]  
            self._sliceStr = self._formatSlice( start, stop, step )
            
            #if component.stop is not None and component.stop >= 0:
            stop += 1
                
            self._range = xrange( start, stop, step )
            
            su = api.MScriptUtil()
            self.__apimfn__().setIndex( start, su.asIntPtr() )  # bug workaround
            
        elif isinstance(component, (list,tuple) ) and len(component) and isinstance( component[0], slice ):
    
            indices = []
            sliceStrs = []
            self._range = []
            self._slices = component
            count = self.__apimfn__().count()
            for x in component:
                if isinstance(x, int):
                    x = slice(x, x)
                
                #print x, self.__apimfn__().count() 
                start, stop, step = x.indices( count-1 )
                    
                sliceStr = self._formatSlice( start, stop, step)
                #if component.stop is not None and component.stop >= 0:
                stop += 1
                
                #indices = self._getRange( startIndex, stopIndex, step)
                indices = range( start, stop, step )
                
                sliceStrs.append( sliceStr )
                self._range += indices
            
            self._sliceStr = ','.join(sliceStrs)
            su = api.MScriptUtil()
            self.__apimfn__().setIndex( self._range[0], su.asIntPtr() )  # bug workaround
              
        elif component is None:
            start = 0
            stop = self.count()-1
            self._sliceStr = '%s:%s' % (start, stop)
            self._slices = [ slice(start, stop) ]
        else:
            raise TypeError, "component must be an MObject, an integer, a slice, or a tuple of slices"
        
        #print "START-STOP", self._startIndex, self._stopIndex
        #self._node = node
        #self._comp = component
        self._comp = component

    
    def name(self):
#        if isinstance( self._comp, int ):
#            return u'%s.%s[%s]' % ( self._node, self._ComponentLabel__, self._comp )
#        elif isinstance( self._comp, slice ):
#            return u'%s.%s[%s:%s]' % ( self._node, self._ComponentLabel__, self._comp.start, self._comp.stop )
#        
#        return u'%s.%s[0:%s]' % (self._node, self._ComponentLabel__, self.count()-1)
        
        return u'%s.%s[%s]' % ( self._node, self._ComponentLabel__, self._sliceStr )

    def __melobject__(self):
        """convert components with pymel extended slices into a list of maya.cmds compatible names"""
        ranges = []
        count = self.__apimfn__().count()
        for slice in self._slices:
            start, stop, step = slice.indices(count)
            if step == 1:
                ranges.append( self._formatSlice( start, stop, step ) )
            else:
                # maya cannot do steps
                ranges +=  [ str(x) for x in self._getRange( start, stop, step ) ]
                
        return [ u'%s.%s[%s]' % ( self._node, self._ComponentLabel__, range ) for range in ranges ]
                
    def __apiobject__(self):
        try:
            return self.__apiobjects__['MObjectHandle'].object()
        except KeyError:
            if len(self._range) == 1:
                return self.__apiobjects__['MFn'].currentItem()
            else:
                raise ValueError, "Cannot determine mobject"
        
    def __apimdagpath__(self) :
        "Return the MDagPath for the node of this attribute, if it is valid"
        try:
            #print "NODE", self.node()
            return self.node().__apimdagpath__()
        except AttributeError: pass
        
    def __apimfn__(self):
        try:
            return self.__apiobjects__['MFn']
        except KeyError:
            if self.__apicls__:
                obj = self.__apiobject__()
                if obj:
                    mfn = self.__apicls__( self.__apimdagpath__(), self.__apiobject__() )
                    self.__apiobjects__['MFn'] = mfn
                    return mfn
    
    def __eq__(self, other):
        return api.MFnComponent( self.__apiobject__() ).isEqual( other.__apiobject__() )
               
    def __str__(self): 
        return str(self.name())
    
    def __unicode__(self): 
        return self.name()                                
     
    def __iter__(self): 
        return self
    
    def node(self):
        return self._node

    def setIndex(self, index):
        #self._range = [component]
        su = api.MScriptUtil()
        self.__apimfn__().setIndex( index, su.asIntPtr() )  # bug workaround
        #self._index = index
        return self
    
    def getIndex(self):
        return self.__apimfn__().index()
    
    def next(self):
        if self.__apimfn__().isDone(): raise StopIteration
        if self._range is not None:
            try:
                nextIndex = self._range[self._rangeIndex]
                su = api.MScriptUtil()
                self.__apimfn__().setIndex( nextIndex, su.asIntPtr() )  # bug workaround
                self._rangeIndex += 1
                return self.__class__(self._node, nextIndex)
            except IndexError:
                raise StopIteration

        else:
            if self.isReset:
                self.isReset = False
            else:
                #print "INCREMENTING"
                self.__apimfn__().next()
                if self.__apimfn__().isDone(): raise StopIteration
        #print "NEXT", self.getIndex()
        #return self.__class__(self._node, self.__apimfn__().index() )
        
        #print "RETURNING"
        return self.__class__( self, self.getIndex() )
#        if isinstance( self._comp, int ):
#            _api.apicls.setIndex( self, self._comp, su.asIntPtr() )  # bug workaround
#        elif isinstance( self._comp, slice):
#            _api.apicls.setIndex( self, i, su.asIntPtr() )  # bug workaround
    
    def __len__(self): 
        return self.count()
            
    def __getitem__(self, item):
        if self.isComplete():
            #return self.__class__(self._node, item)
            return self.__class__(self._node, item)
        else:
            assert isinstance(item, (int,slice) ), "Extended slice syntax only allowed on a complete range, such as when using Mesh(u'obj').vtx"
            return self.__class__( self._node, self._getMayaSlice(self._range[item]) )

        
class MeshEdge( Component ):
    __apicls__ = api.MItMeshEdge
    __metaclass__ = _factories.MetaMayaTypeWrapper
    _ComponentLabel__ = 'e'
    
    
    def count(self):
        """
        :rtype: int
        """
        if self._range is not None:
            return len(self._range)
        else:
            return self.__apimfn__().count()

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @util.deprecated("Use 'connectedFaces' instead.")
    def toFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )

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
    
_factories.ApiEnumsToPyComponents()[api.MFn.kMeshEdgeComponent  ] = MeshEdge
       
class MeshVertex( Component ):
    __apicls__ = api.MItMeshVertex
    __metaclass__ = _factories.MetaMayaTypeWrapper
    _ComponentLabel__ = 'vtx'
    def count(self):
        if self._range is not None:
            return len(self._range)
        else:
            return self.__apimfn__().count()
    
    def setColor(self,color):
        self.node().setVertexColor( color, self.getIndex() )

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @util.deprecated("Use 'connectedEdges' instead.") 
    def toEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @util.deprecated("Use 'connectedFaces' instead.")
    def toFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) ) 
 
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
            
_factories.ApiEnumsToPyComponents()[api.MFn.kMeshVertComponent ] = MeshVertex  
  
class MeshFace( Component ):
    __apicls__ = api.MItMeshPolygon
    __metaclass__ = _factories.MetaMayaTypeWrapper
    _ComponentLabel__ = 'f'
    def count(self):
        """
        :rtype: int
        """
        if self._range is not None:
            return len(self._range)
        else:
            return self.__apimfn__().count()
        

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @util.deprecated("Use 'connectedEdges' instead.") 
    def toEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) )
    
    @util.deprecated("Use 'connectedVertices' instead.")
    def toVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) ) 
    
    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, self._getMayaSlice( [ array[i] for i in range( array.length() ) ] ) ) 

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
    
_factories.ApiEnumsToPyComponents()[api.MFn.kMeshPolygonComponent ] = MeshFace

class NurbsCurveCV( Component ):
    apicls = api.MItCurveCV
    __metaclass__ = _factories.MetaMayaTypeWrapper
    _ComponentLabel__ = 'cv'
    def count(self):
        if self._range is not None:
            return len(self._range)
        else:
            return self.node().numCVs()
_factories.ApiEnumsToPyComponents()[api.MFn.kCurveCVComponent] = NurbsCurveCV
           
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
            
        elif isinstance( item, slice ):
            return self.returnClass( self._node, formatSlice(item) )

        else:
            return self.returnClass( self._node, item )


    def plugNode(self):
        'plugNode'
        return PyNode( str(self).split('.')[0])
                
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
        return move( self, *args, **kwargs )
    def scale( self, *args, **kwargs ):
        return scale( self, *args, **kwargs )    
    def rotate( self, *args, **kwargs ):
        return rotate( self, *args, **kwargs )

class AttributeDefaults(PyNode):
    __metaclass__ = MetaMayaTypeWrapper
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

        raise MayaAttributeError
    
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
                 
class Attribute(PyNode):
    """
    Attributes
    ==========
    
    The Attribute class is your one-stop shop for all attribute related functions. Those of us who have spent time using MEL
    have become familiar with all the many commands for operating on attributes.  This class gathers them all into one
    place. If you forget or are unsure of the right method name, just ask for help by typing `help(Attribute)`.  
    
    For the most part, the names of the class equivalents to the maya.cmds functions follow a fairly simple pattern:
    `setAttr` becomes `Attribute.set`, `getAttr` becomes `Attribute.get`, `connectAttr` becomes `Attribute.connect` and so on.  
    Here's a simple example showing how the Attribute class is used in context.
    
        >>> from pymel import *
        >>> cam = PyNode('persp')
        >>> if cam.visibility.isKeyable() and not cam.visibility.isLocked():
        ...     cam.visibility.set( True )
        ...     cam.visibility.lock()
        ... 
        >>> print cam.v.type()      # shortnames also work    
        bool
    
    Accessing Attributes
    --------------------
    
    You can access an attribute class in three ways.  The first two require that you already have a `PyNode` object.
    
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
    pass in an api MPlug object.  If you don't know whether the string name represents a node or an attribute, you can always instantiate via the `PyNode`
    class, which will determine the appropriate class automaticallly.
    
    explicitly request an Attribute:
    
        >>> Attribute( 'persp.visibility' ) 
        Attribute(u'persp.visibility')
        
    let PyNode figure it out for you:
    
        >>> PyNode( 'persp.translate' ) 
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
    __metaclass__ = MetaMayaTypeWrapper
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

        raise MayaAttributeError
    
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
            raise MayaAttributeError( '%s.%s' % (self, attr) )
    
    
    def __getattr__(self, attr):
        try:
            return self.attr(attr)
        except MayaAttributeError, e:
            raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
    # Added the __call__ so to generate a more appropriate exception when a class method is not found 
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" % (repr(self.node()), self.plugAttr()))
    
    
    def __iter__(self):
        """
        iterator for multi-attributes
        
            >>> from pymel import *
            >>> f=newFile(f=1) #start clean
            >>> 
            >>> at = PyNode( 'defaultLightSet.dagSetMembers' )
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
            self.__dict__.pop('_iterIndex')
            self.__dict__.pop('_iterIndices')
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
                other = PyNode(other)
            except (ValueError,TypeError): # could not cast to PyNode
                return False
            
        otherPlug = other.__apimplug__()
        # foo.bar[10] and foo.bar[20] and foo.bar eval to the same object in api.  i don't think this is very intuitive.
        try:
            otherIndex = otherPlug.logicalIndex()
        except RuntimeError:
            otherIndex = None  
        return thisPlug == otherPlug and thisIndex == otherIndex

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
        raise MayaObjectError(self._name)
    
    
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
        
            >>> from pymel import *
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

    @util.deprecated('This method does not always produce the expected result. Use Attribute.numElements instead.', 'Attribute')
    def size(self):
        """
        The number of elements in an array attribute. Returns None if not an array element.
        
        Be aware that `Attribute.size`, which derives from ``getAttr -size``, does not always produce the expected
        value. It is recommend that you use `Attribute.numElements` instead.  This is a maya bug, *not* a pymel bug.
        
            >>> from pymel import *
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
    set = setAttr            
    get = getAttr
    setKey = _factories.functionFactory( cmds.setKeyframe, rename='setKey' )       
    
    
#----------------------
#xxx{ Connections
#----------------------    
          
    def isConnectedTo(self, other, ignoreUnitConversion=False):          
        return cmds.isConnected( self, other, ignoreUnitConversion=ignoreUnitConversion)
    
    ## does not work because this method cannot return a value, it is akin to +=       
    #def __irshift__(self, other):
    #    """operator for 'isConnected'
    #        sphere.tx >>= box.tx
    #    """ 
    #    return cmds.isConnected(self, other)
    

    connect = connectAttr
        
    def __rshift__(self, other):
        """
        operator for 'connectAttr'
        
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """ 
        return connectAttr( self, other, force=True )
                
    disconnect = disconnectAttr
    
    def __floordiv__(self, other):
        """
        operator for 'disconnectAttr'
        
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """ 
        # no return
        cmds.disconnectAttr( self, other )
                
    def inputs(self, **kwargs):
        """
        ``listConnections -source 1 -destination 0``
        
        see `Attribute.connections` for the full ist of flags.
        
        :rtype: `PyNode` list
        """
        
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        
        return listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        """
        ``listConnections -source 0 -destination 1``
        
        see `Attribute.connections` for the full ist of flags.
        
        :rtype: `PyNode` list
        """
        
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return listConnections(self, **kwargs)
    
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
    
    @addMelDocs( 'setKeyframe' )    
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
        """attributeQuery -exists
        
        :rtype: `bool`
        """
        try:
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), exists=True)    
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

    def setMin(self, newMin):
        self.setSoftRange(newMin, 'default')
        
    def setSoftMax(self, newMax):
        self.setSoftRange('default', newMax)
                
    def setRange(self, *args):
        """provide a min and max value as a two-element tuple or list, or as two arguments to the
        method. To remove a limit, provide a None value.  for example:
        
            >>> from pymel import *
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
    
    def getParent(self):
        """
        :rtype: `Attribute`  
        """
        try:
            return Attribute( self.node(), self.__apimfn__().parent() )
        except:
            pass
    
    parent = getParent
#}      


class DependNode( PyNode ):
    __apicls__ = api.MFnDependencyNode
    __metaclass__ = MetaMayaNodeWrapper
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
#        return PyNode.__new__(cls,name)

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
            except MayaObjectError:
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
        return rename(self, name)
    
    def __apiobject__(self) :
        "get the default API object (MObject) for this node if it is valid"
        return self.__apimobject__()
    
    def __apimobject__(self) :
        "get the MObject for this node if it is valid"
        handle = self.__apihandle__()
        if api.isValidMObjectHandle( handle ) :
            return handle.object()
        raise MayaNodeError( self._name )
        
    def __apihandle__(self) :
        return self.__apiobjects__['MObjectHandle']
    

    def __str__(self):
        return "%s" % self.name()

    def __unicode__(self):
        return u"%s" % self.name()

    if Version.current >= Version.v2009:
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

    
    duplicate = duplicate
    
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
    type = nodeType
            
         
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
        return getClassification( self.type() )    
        #return self.__apimfn__().classification( self.type() )
    
#}
#--------------------------
#xxx{   Connections
#-------------------------- 
    
    def inputs(self, **kwargs):
        """listConnections -source 1 -destination 0
        
        :rtype: `PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        """listConnections -source 0 -destination 1
        
        :rtype: `PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return listConnections(self, **kwargs)                            

    def sources(self, **kwargs):
        """listConnections -source 1 -destination 0
        
        :rtype: `PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return listConnections(self, **kwargs)
    
    def destinations(self, **kwargs):
        """listConnections -source 0 -destination 1
        
        :rtype: `PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return listConnections(self, **kwargs)    
        
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
            #print "DependNode.__getattr__(%r)" % attr
            #return super(PyNode, self).__getattr__(attr) 
            return getattr(super(PyNode, self), attr)
        except AttributeError :
            try:
                #print "DependNode.attr(%r)" % attr
                return DependNode.attr(self,attr)
            except MayaAttributeError, e:
                # since we're being called via __getattr__ we don't know whether the user was trying 
                # to get a class method or a maya attribute, so we raise a more generic AttributeError
                raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
            

    def __setattr__(self, attr, val):
        #print "DependNode.__setattr__", attr, val

        # TODO: check all nodes in hierarchy
        if hasattr(PyNode, attr):
            super(PyNode, self).__setattr__( attr, val )
        else:
            DependNode.attr(self,attr).set(val)
             
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
                # Option 1: back out to api.toApiObject (via PyNode)
                # return Attribute( self.__apiobject__(), self.name() + '.' + attr )
            
                # Option 2: nameparse.
                # this avoids calling self.name(), which can be slow
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
                                result = self.__apimfn__().findPlug( token )  
                            else:
                                result = result.child( self.__apimfn__().attribute( token ) )
                        else: # Node
                            result = self.__apimfn__().findPlug( token )                              
#                                # search children for the attribute to simulate  cam.focalLength --> perspShape.focalLength
#                                except TypeError:
#                                    for i in range(fn.childCount()):
#                                        try: result = api.MFnDagNode( fn.child(i) ).findPlug( token )
#                                        except TypeError: pass
#                                        else:break
                    if isinstance( token, nameparse.NameIndex ):
                        result = result.elementByLogicalIndex( token.value )
                return Attribute( self.__apiobject__(), result )
            else:
                # NOTE: not sure if this should be True or False
                return Attribute( self.__apiobject__(), self.__apimfn__().findPlug( attr, False ) ) 
            
        except RuntimeError:
            # raise our own MayaAttributeError, which subclasses AttributeError and MayaObjectError
            raise MayaAttributeError( '%s.%s' % (self, attr) )
               
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

    @addMelDocs('setAttr')  
    def setAttr( self, attr, *args, **kwargs):
        # for now, using strings is better, because there is no MPlug support
        return setAttr( "%s.%s" % (self, attr), *args, **kwargs )
    
    @addMelDocs('setAttr')  
    def setDynamicAttr( self, attr, *args, **kwargs):
        """
        same as `DependNode.setAttr` with the force flag set to True.  This causes
        the attribute to be created based on the passed input value.
        """
        
        # for now, using strings is better, because there is no MPlug support
        kwargs['force'] = True
        return setAttr( "%s.%s" % (self, attr), *args, **kwargs )
    
    @addMelDocs('getAttr')  
    def getAttr( self, attr, *args, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return getAttr( "%s.%s" % (self, attr), *args,  **kwargs )

    @addMelDocs('addAttr')  
    def addAttr( self, attr, **kwargs):
        # for now, using strings is better, because there is no MPlug support  
        assert 'longName' not in kwargs and 'ln' not in kwargs
        kwargs['longName'] = attr
        return addAttr( unicode(self), **kwargs )
    
    @addMelDocs('connectAttr')  
    def connectAttr( self, attr, destination, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return connectAttr( "%s.%s" % (self, attr), destination, **kwargs )
    
    @addMelDocs('disconnectAttr')  
    def disconnectAttr( self, attr, destination=None, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return disconnectAttr( "%s.%s" % (self, attr), destination, **kwargs )

                    
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
    _numPartReg = re.compile('([0-9]+)$')
    
    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged.
        
        >>> SCENE.lambert1.stripNum()
        u'lambert'
        
        :rtype: `unicode`
        """
        try:
            return DependNode._numPartReg.split( self.name() )[0]
        except IndexError:
            return unicode(self)
            
    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised.

        >>> SCENE.lambert1.extractNum()
        u'1'
        
        :rtype: `unicode`
        """
        
        try:
            return DependNode._numPartReg.split( self.name() )[1]
        except IndexError:
            raise ValueError, "No trailing numbers to extract on object %s" % self

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found

        
        :rtype: `unicode`
        """
        name = self.nextName()
        while name.exists():
            name = name.nextName()
        return name
                
    def nextName(self):
        """Increment the trailing number of the object by 1

        >>> SCENE.lambert1.nextName()
        DependNodeName('lambert2')
        
        :rtype: `unicode`
        """
        import other
        groups = DependNode._numPartReg.split( self.name() )
        if groups:
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return other.NameParser( formatStr % ( groups[0], (int(num) + 1) ) )
        else:
            raise ValueError, "could not find trailing numbers to increment on object %s" % self
            
    def prevName(self):
        """Decrement the trailing number of the object by 1
        
        :rtype: `unicode`
        """
        import other
        try:
            groups = DependNode._numPartReg.split(self)
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return other.NameParser( formatStr % ( groups[0], (int(num) - 1) ) )
        except:
            raise ValueError, "could not find trailing numbers to decrement on object %s" % self
#}

class Entity(DependNode):
    __metaclass__ = MetaMayaNodeWrapper
    pass

class DagNode(Entity):
 
    #:group Path Info and Modification: ``*parent*``, ``*Parent*``, ``*child*``, ``*Child*``
    """
    """
    
    __apicls__ = api.MFnDagNode
    __metaclass__ = MetaMayaNodeWrapper
    
#    def __init__(self, *args, **kwargs ):
#        self.apicls.__init__(self, self.__apimdagpath__() )
        
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
                raise MayaNodeError
            
            self._name = name
            if long :
                return dag.fullPathName()

        return self._name                       
            
    def name(self, update=True, long=False) :
        
        if update or long or self._name is None:
            try:
                return self._updateName()
            except MayaObjectError:
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
                raise MayaNodeError( self._name )
            self.__apiobjects__['MObjectHandle'] = handle
        return handle
    
    def __apimobject__(self) :
        "get the MObject for this object if it is valid"
        handle = self.__apihandle__()
        if api.isValidMObjectHandle( handle ):
            return handle.object()
        raise MayaNodeError( self._name )
            

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
        if isinstance( other, PyNode ):
            return self.__apimobject__() == other.__apimobject__()
        else:
            try:
                return self.__apimobject__() == PyNode(other).__apimobject__()
            except:
                return False
    
    def getInstances(self, includeSelf=True):
        """
        :rtype: `DagNode` list
        
        >>> from pymel import *
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
        result = [ PyNode( api.MDagPath(d[i])) for i in range(d.length()) if includeSelf or not d[i] == thisDagPath ]
        
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
#            return PyNode(parent)
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
#            children.append( PyNode(child) )
#        return children
             
    def getParent(self, **kwargs):
        """unlike the firstParent command which determines the parent via string formatting, this 
        command uses the listRelatives command
        
        see also `parentAtIndex`
        
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
             
        res = PyNode( res )
        return res
    
    def getAllParents(self):
        """return a list of all transforms above this node"""
        x = self.getParent()
        res = []
        while x:
            res.append(x)
            x = x.getParent()
        return res      
                
                     
    def getChildren(self, **kwargs ):
        """
        see also `childAtIndex`
        
        :rtype: `DagNode` list
        """
        kwargs['children'] = True
        kwargs.pop('c',None)

        return listRelatives( self, **kwargs)
        
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
        :rtype: `PyNode` list
        """
        return listRelatives( self, **kwargs)
        
    
    def setParent( self, *args, **kwargs ):
        'parent'
        return self.__class__( cmds.parent( self, *args, **kwargs )[0] )

    def addChild( self, child, **kwargs ):
        """parent (reversed)
        
        :rtype: `DagNode`
        """
        cmds.parent( child, self, **kwargs )
        if not isinstance( child, PyNode ):
            child = PyNode(child)
        return child
    
    def __or__(self, child, **kwargs):
        """
        operator for `addChild`. Use to easily daisy-chain together parenting operations.
        The operation order visually mimics the resulting dag path:
        
            >>> from pymel import *
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
    __metaclass__ = MetaMayaNodeWrapper
    def getTransform(self): pass    
#class Joint(Transform):
#    pass

        
class Camera(Shape):
    __metaclass__ = MetaMayaNodeWrapper
    @util.deprecated('Use getHorizontalFieldOfView instead', 'Camera' )
    def getFov(self):
        aperture = self.horizontalFilmAperture.get()
        fov = (0.5 * aperture) / (self.focalLength.get() * 0.03937)
        fov = 2.0 * atan (fov)
        fov = 57.29578 * fov
        return fov
    
    @util.deprecated('Use setHorizontalFieldOfView instead', 'Camera' )   
    def setFov(self, fov):
        aperture = self.horizontalFilmAperture.get()
        focal = tan (0.00872665 * fov);
        focal = (0.5 * aperture) / (focal * 0.03937);
        self.focalLength.set(focal)
    
    @util.deprecated('Use getAspectRatio instead', 'Camera' )  
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
    
    @addMelDocs('dolly')
    def dolly(self, distance, relative=True):
        kwargs = {}
        kwargs['distance'] = distance
        if relative:
            kwargs['relative'] = True
        else:
            kwargs['absolute'] = True
        cmds.dolly(self, **kwargs)

    @addMelDocs('roll')
    def roll(self, degree, relative=True):
        Camera(u'frontShape')
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
    __metaclass__ = MetaMayaNodeWrapper
#    def __getattr__(self, attr):
#        try :
#            return super(PyNode, self).__getattr__(attr)
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
            return DependNode.__getattr__(self,attr)
        except AttributeError, e:
            # Functions via shape inheritance , and then, implicitly, Attributes
            shape = self.getShape()
            if shape:
                try:
                    #print "Transform: trying shape: getattr(%s,%s)" % (shape,attr)
                    return getattr(shape,attr)
                except AttributeError: pass
            raise e
        
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
            return DependNode.attr(self,attr)
        except MayaAttributeError, e:
            if checkShape:
                #print "\tCHECKING SHAPE"
                try: 
                    return self.getShape().attr(attr)
                except AttributeError:
                    raise e
            raise e
        
#    def __getattr__(self, attr):
#        if attr.startswith('__') and attr.endswith('__'):
#            return super(PyNode, self).__getattr__(attr)
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
    

#    @editflag('xform','scale')      
#    def setScale( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )

    @editflag('xform','rotation')             
    def setRotationOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )
        
    @editflag('xform','translation')  
    def setTranslationOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )

    @editflag('xform','scalePivot')  
    def setScalePivotOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )
        
    @editflag('xform','rotatePivot')         
    def setRotatePivotOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )
 
#    @editflag('xform','pivots')         
#    def setPivots( self, val, **kwargs ):
#        cmds.xform( self, **kwargs )
        
    @editflag('xform','rotateAxis')  
    def setRotateAxisOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )
        
    @editflag('xform','shear')                                 
    def setShearingOld( self, val, **kwargs ):
        cmds.xform( self, **kwargs )

    
    @editflag('xform','rotateAxis')                                
    def setMatrix( self, val, **kwargs ):
        """xform -scale"""
        if isinstance(val, datatypes.Matrix):
            val = val.toList()
    
        kwargs['matrix'] = val
        cmds.xform( self, **kwargs )

#    @queryflag('xform','scale') 
#    def getScaleOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    def _getSpaceArg(self, space, kwargs):
        if kwargs.pop( 'worldSpace', kwargs.pop('ws', False) ):
            space = 'world'
        elif kwargs.pop( 'objectSpace', kwargs.pop('os', False) ):
            space = 'object'
        if kwargs:
            raise ValueError, "unknown keyword argument(s) %s" % ','.join( kwargs.keys() )
        return space
    
    @queryflag('xform','translation') 
    def getTranslationOld( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @addApiDocs( api.MFnTransform, 'setTranslation' )
    def setTranslation(self, vector, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setTranslation(vector, space=space)
    
    @addApiDocs( api.MFnTransform, 'getTranslation' )
    def getTranslation(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getTranslation(space=space)

    
    @queryflag('xform','rotatePivot')        
    def getRotatePivotOld( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @addApiDocs( api.MFnTransform, 'setRotatePivot' )
    def setRotatePivot(self, point, space='world', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivot(point, space=space, balance=balance) 
    
    @addApiDocs( api.MFnTransform, 'rotatePivot' )
    def getRotatePivot(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivot(space=space)

    @addApiDocs( api.MFnTransform, 'setRotatePivotTranslation' )
    def setRotatePivotTranslation(self, vector, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivotTranslation(vector, space=space)
    
    @addApiDocs( api.MFnTransform, 'rotatePivotTranslation' )
    def getRotatePivotTranslation(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivotTranslation(space=space)

 
    @queryflag('xform','rotation')        
    def getRotationOld( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @addApiDocs( api.MFnTransform, 'setRotation' )
    def setRotation(self, rotation, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        quat = api.MQuaternion(rotation)
        self.__apimfn__().setRotation(quat, datatypes.Spaces.getIndex(space) )
      
    @addApiDocs( api.MFnTransform, 'getRotation' )
    def getRotation(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        quat = api.MQuaternion()
        self.__apimfn__().getRotation(quat, datatypes.Spaces.getIndex(space) )
        return datatypes.EulerRotation( quat.asEulerRotation() )

    
    @queryflag('xform','scalePivot') 
    def getScalePivotOld( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @addApiDocs( api.MFnTransform, 'setScalePivotTranslation' )
    def setScalePivot(self, point, space='world', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivotTranslation(point, space=space, balance=balance)
    
    @addApiDocs( api.MFnTransform, 'scalePivot' )
    def getScalePivot(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getScalePivot(space=space)

    @addApiDocs( api.MFnTransform, 'setScalePivotTranslation' )
    def setScalePivotTranslation(self, vector, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivotTranslation(vector, space=space)
          
    @addApiDocs( api.MFnTransform, 'scalePivotTranslation' )
    def getScalePivotTranslation(self, space='world', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getScalePivotTranslation(space=space)
    
    @queryflag('xform','pivots') 
    def getPivots( self, **kwargs ):
        res = cmds.xform( self, **kwargs )
        return ( datatypes.Vector( res[:3] ), datatypes.Vector( res[3:] )  )
    
    @queryflag('xform','rotateAxis') 
    def getRotateAxis( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )
        
    @queryflag('xform','shear')                          
    def getShearOld( self, **kwargs ):
        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @queryflag('xform','matrix')                
    def getMatrix( self, **kwargs ): 
        return datatypes.Matrix( cmds.xform( self, **kwargs ) )
      
    #TODO: create API equivalent of `xform -boundingBoxInvisible` so we can replace this with api.
    def getBoundingBox(self, invisible=False):
        """xform -boundingBox and xform -boundingBoxInvisible
        
        :rtype: `BoundingBox`
        
        
        """
        kwargs = {'query' : True }    
        if invisible:
            kwargs['boundingBoxInvisible'] = True
        else:
            kwargs['boundingBox'] = True
                    
        res = cmds.xform( self, **kwargs )
        #return ( datatypes.Vector(res[:3]), datatypes.Vector(res[3:]) )
        return datatypes.BoundingBox( res[:3], res[3:] )
    
    def getBoundingBoxMin(self, invisible=False):
        """
        :rtype: `Vector`
        """
        return self.getBoundingBox(invisible)[0]
        #return self.getBoundingBox(invisible).min()
    
    def getBoundingBoxMax(self, invisible=False):
        """
        :rtype: `Vector`
        """
        return self.getBoundingBox(invisible)[1]   
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
    __metaclass__ = MetaMayaNodeWrapper
    connect = _factories.functionFactory( cmds.connectJoint, rename='connect')
    disconnect = _factories.functionFactory( cmds.disconnectJoint, rename='disconnect')
    insert = _factories.functionFactory( cmds.insertJoint, rename='insert')

if Version.isUnlimited():
    class FluidEmitter(Transform):
        __metaclass__ = MetaMayaNodeWrapper
        fluidVoxelInfo = _factories.functionFactory( cmds.fluidVoxelInfo, rename='fluidVoxelInfo')
        loadFluid = _factories.functionFactory( cmds.loadFluid, rename='loadFluid')
        resampleFluid = _factories.functionFactory( cmds.resampleFluid, rename='resampleFluid')
        saveFluid = _factories.functionFactory( cmds.saveFluid, rename='saveFluid')
        setFluidAttr = _factories.functionFactory( cmds.setFluidAttr, rename='setFluidAttr')
        getFluidAttr = _factories.functionFactory( cmds.getFluidAttr, rename='getFluidAttr')
    
class RenderLayer(DependNode):
    def listMembers(self, fullNames=True):
        if fullNames:
            return map( PyNode, util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=True) ) )
        else:
            return util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=False) )
        
    def addMembers(self, members, noRecurse=True):
        cmds.editRenderLayerMembers( self, members, noRecurse=noRecurse )

    def removeMembers(self, members ):
        cmds.editRenderLayerMembers( self, members, remove=True )
 
    def listAdjustments(self):
        return map( PyNode, util.listForNone( cmds.editRenderLayerAdjustment( layer=self, q=1) ) )
      
    def addAdjustments(self, members, noRecurse):
        return cmds.editRenderLayerMembers( self, members, noRecurse=noRecurse )

    def removeAdjustments(self, members ):
        return cmds.editRenderLayerMembers( self, members, remove=True )      
    
    def setCurrent(self):
        cmds.editRenderLayerGlobals( currentRenderLayer=self)    

class DisplayLayer(DependNode):
    def listMembers(self, fullNames=True):
        if fullNames:
            return map( PyNode, util.listForNone( cmds.editDisplayLayerMembers( self, q=1, fullNames=True) ) )
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

class GeometryShape(DagNode): pass
class DeformableShape(GeometryShape): pass
class ControlPoint(DeformableShape): pass
class CurveShape(DeformableShape): pass
class NurbsCurve(CurveShape):
    __metaclass__ = MetaMayaNodeWrapper
    @property
    def cv(self): return NurbsCurveCV(self)
    
class SurfaceShape(ControlPoint): pass
class Mesh(SurfaceShape):
    """
    The Mesh class provides wrapped access to many API methods for querying and modifying meshes.  Be aware that 
    modifying meshes using API commands outside of the context of a plugin is still somewhat uncharted territory,
    so proceed at our own risk. 
    
   
    The component types can be accessed from the `Mesh` type (or it's transform) using the names you are
    familiar with from MEL:

        >>> from pymel import *
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

    >>> from pymel import *
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
    __metaclass__ = MetaMayaNodeWrapper
#    def __init__(self, *args, **kwargs ):      
#        SurfaceShape.__init__(self, self._apiobject )
#        self.vtx = MeshEdge(self.__apimobject__() )
    def __getattr__(self, attr):
        #print "Mesh.__getattr__", attr
        try:
            {   'vtx'   : MeshVertex,
                'verts' : MeshVertex,
                'e'     : MeshEdge,
                'edges' : MeshEdge,
                'f'     : MeshEdge,
                'faces' : MeshEdge
            }[attr](self)
        except KeyError:
            #print "getting super", attr
            return DependNode.__getattr__(self,attr)
         
    @property
    def f(self): return MeshFace(self)
    @property
    def faces(self): return MeshFace(self)
    
    @property
    def e(self): return MeshEdge(self)
    @property
    def edges(self): return MeshEdge(self)
     
    @property
    def vtx(self): return MeshVertex(self)
    @property
    def verts(self): return MeshVertex(self)
                    
    vertexCount =  util.deprecated( "Use 'numVertices' instead.")( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertex', 'vertexCount' ))
    edgeCount =    util.deprecated( "Use 'numEdges' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edge', 'edgeCount' ))
    faceCount =    util.deprecated( "Use 'numFaces' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate,  'face', 'faceCount' ))
    uvcoordCount = util.deprecated( "Use 'numUVs' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'uvcoord', 'uvcoordCount' ))
    triangleCount = util.deprecated( "Use 'numTriangles' instead." )( _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangle', 'triangleCount' ))
    
    numTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangles', 'numTriangles' )
    numSelectedTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangleComponent', 'numSelectedTriangles' )
    numSelectedFaces = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'faceComponent', 'numSelectedFaces' )
    numSelectedEdges = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edgeComponent', 'numSelectedEdges' )
    numSelectedVertices = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertexComponent', 'numSelectedVertices' )
     
    area = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'area'  )
    worldArea = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'worldArea' )
           

class Subdiv(SurfaceShape):
    __metaclass__ = MetaMayaNodeWrapper
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
    
class Particle(DeformableShape):
    __metaclass__ = MetaMayaNodeWrapper
    
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
        return list(self)
    
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
            return self.apicls.hasItem(self, PyNode(item).__apiobject__())

    def __repr__(self):
        """:rtype: `str` """
        names = []
        self.apicls.getSelectionStrings( self, names )
        return '%s(%s)' % ( self.__class__.__name__, names )

        
    def __getitem__(self, index):
        """:rtype: `PyNode` """
        if index >= len(self):
            raise IndexError, "index out of range"
        
        plug = api.MPlug()
        obj = api.MObject()
        dag = api.MDagPath()
        try:
            self.apicls.getPlug( self, index, plug )
            return PyNode( plug )
        except RuntimeError:
            try:
                self.apicls.getDependNode( self, index, obj )
                return PyNode( obj )
            except RuntimeError:
                try:
                    self.apicls.getDagPath( self, index, dag )
                    return PyNode( dag )
                except:
                    pass
                
    def __setitem__(self, index, item):
        
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.apicls.replace(self, index, item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.replace(self, PyNode(item).__apiobject__())
        
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
            return self.apicls.add(self, PyNode(item).__apiobject__())
        
     
    def pop(self, index):
        """:rtype: `PyNode` """
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
        return sets( self )
#    def intersect(self, other):
#        self.apicls.merge( other, api.MSelectionList.kXORWithList )
    

       
class ObjectSet(Entity):
    """
    The ObjectSet class and `SelectionSet` class work together.  Both classes have a very similar interface,
    the primary difference is that the ObjectSet class represents connections to an objectSet node, while the
    `SelectionSet` class is a generic set, akin to pythons built-in `set`. 
 
    
    create some sets:
    
        >>> from pymel import *
        >>> f=newFile(f=1) #start clean
        >>> 
        >>> s = sets()  # create an empty set
        >>> s.union( ls( type='camera') )  # add some cameras to it
        >>> s.members()  # get members as a list
        [Camera(u'sideShape'), Camera(u'frontShape'), Camera(u'topShape'), Camera(u'perspShape')]
        >>> sel = s.asSelectionSet() # or as a SelectionSet
        >>> sel # doctest: +SKIP
        SelectionSet([u'sideShape', u'frontShape', u'topShape', u'perspShape'])
        >>> sorted(sel)
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

    __metaclass__ = MetaMayaNodeWrapper
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
            return self.__apimfn__().isMember(PyNode(item).__apiobject__())

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

    @util.deprecated( 'Use ObjectSet.members instead', 'ObjectSet' )
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
            return self.__apimfn__().addMember(PyNode(item).__apiobject__())

    def remove(self, item):
        if isinstance(item, (DependNode, DagNode, Attribute) ):
            return self.__apimfn__().removeMember(item.__apiobject__())
        elif isinstance(item, Component):
            raise NotImplementedError
        else:
            return self.__apimfn__().removeMember(PyNode(item).__apiobject__())
          
    def isSubSet(self, other):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSubSet(other)
    
    issubset = util.deprecated( 'Use ObjectSet.isSubSet instead', 'ObjectSet' )( members ) 
    
    
    def isSuperSet(self, other ):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSuperSet(other)
    
    issuperset = util.deprecated( 'Use ObjectSet.isSuperSet instead', 'ObjectSet' )( members ) 
    
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
     
    update = util.deprecated( 'Use ObjectSet.union instead', 'ObjectSet' )( members ) 

_factories.ApiTypeRegister.register( 'MSelectionList', SelectionSet )  


def _createPyNodes():
    #for cmds.nodeType in networkx.search.dfs_preorder( _factories.nodeHierarchy , 'dependNode' )[1:]:
    #print _factories.nodeHierarchy
    # see if breadth first isn't more practical ?
    
    # reset cache
    _factories.PyNodeTypesHierarchy().clear()
    _factories.PyNodeNamesToPyNodes().clear()
    
    for treeElem in _factories.nodeHierarchy.preorder():
        #print "treeElem: ", treeElem
        mayaType = treeElem.key
            
        #print "cmds.nodeType: ", cmds.nodeType
        if mayaType == 'dependNode': continue
        
        parentMayaType = treeElem.parent.key
        #print "superNodeType: ", superNodeType, type(superNodeType)
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue
        
        className = util.capitalize(mayaType)
        #if className not in __all__: __all__.append( className )
        
        _factories.addPyNode( _thisModule, mayaType, parentMayaType )



# Initialize Pymel classes to API types lookup
#_startTime = time.time()
_createPyNodes()
#_logger.debug( "Initialized Pymel PyNodes types list in %.2f sec" % time.time() - _startTime )



def _getPymelType(arg) :
    """ Get the correct Pymel Type for an object that can be a MObject, PyNode or name of an existing Maya object,
        if no correct type is found returns DependNode by default.
        
        If the name of an existing object is passed, the name and MObject will be returned
        If a valid MObject is passed, the name will be returned as None
        If a PyNode instance is passed, its name and MObject will be returned
        """
        
    def getPymelTypeFromObject(obj):
        try:
            return _factories.ApiEnumsToPyComponents()[obj.apiType()]
        except KeyError:
            try:  
                fnDepend = api.MFnDependencyNode( obj )
                mayaType = fnDepend.typeName()
                pymelType = mayaTypeToPyNode( mayaType, DependNode )
                return pymelType
            except RuntimeError:
                raise MayaNodeError
    obj = None
    results = {}
    
    passedType = ''
    isAttribute = False
  
    #--------------------------   
    # API object testing
    #--------------------------   
    if isinstance(arg, api.MObject) :     
        results['MObjectHandle'] = api.MObjectHandle( arg )
        obj = arg
#        if api.isValidMObjectHandle( obj ) :
#            pymelType = getPymelTypeFromObject( obj.object() )        
#        else:
#            raise ValueError, "Unable to determine Pymel type: the passed MObject is not valid" 
                      
    elif isinstance(arg, api.MObjectHandle) :      
        results['MObjectHandle'] = arg
        obj = arg.object()
        
#        if api.isValidMObjectHandle( obj ) :          
#            pymelType = getPymelTypeFromObject( obj.object() )    
#        else:
#            raise ValueError, "Unable to determine Pymel type: the passed MObjectHandle is not valid" 
        
    elif isinstance(arg, api.MDagPath) :
        results['MDagPath'] = arg
        obj = arg.node()
#        if api.isValidMDagPath( obj ):
#            pymelType = getPymelTypeFromObject( obj.node() )    
#        else:
#            raise ValueError, "Unable to determine Pymel type: the passed MDagPath is not valid"
                               
    elif isinstance(arg, api.MPlug) : 
        isAttribute = True
        obj = arg
        results['MPlug'] = obj
        if api.isValidMPlug(arg):
            pymelType = Attribute
        else :
            raise MayaAttributeError, "Unable to determine Pymel type: the passed MPlug is not valid" 

#    #---------------------------------
#    # No Api Object : Virtual PyNode 
#    #---------------------------------   
#    elif objName :
#        # non existing node
#        pymelType = DependNode
#        if '.' in objName :
#            # TODO : some better checking / parsing
#            pymelType = Attribute 
    else :
        raise ValueError, "Unable to determine Pymel type for %r" % arg         
    
    if not isAttribute:
        pymelType = getPymelTypeFromObject( obj ) 
    
    return pymelType, results


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
        

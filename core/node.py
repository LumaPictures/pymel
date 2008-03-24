"""
The node module contains functions which are used to create nodes, as well as their class counterparts.
See the sections `Node Class Hierarchy`_ and `Node Commands and their Class Counterparts`_.
"""


import pymel.util.api
import pymel.core.core, pymel.util.factories, pymel.util, pymel.core.anim
import sys, os, re, inspect, warnings, timeit, time
try:
    import maya.cmds as cmds
    import maya.mel as mm
except ImportError:
    pass

#from vector import pymel.core.core.Vector, pymel.core.core.Matrix  # in core
#from core import *
#from anim import *
#import pymel.util, pymel.util.factories  # in core


#-----------------------------------------------
#  Enhanced Node Commands
#-----------------------------------------------

metaNode = pymel.util.factories.makeMetaNode( __name__ )

def joint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, limitSwitch*, stiffness*, and angle* flags returned lists of values instead 
        of single values. Values are now properly unpacked
    """
    
    res = cmds.joint(*args, **kwargs)
    
    #if kwargs.pop('query',False) or kwargs.pop('q',False):

    if kwargs.get('query', kwargs.get( 'q', False)):
        args = [
        'limitSwitchX', 'lsx',
        'limitSwitchY', 'lsy',
        'limitSwitchZ', 'lsz',
        'stiffnessX', 'stx',
        'stiffnessY', 'sty',
        'stiffnessZ', 'stz',
        'angleX', 'ax',
        'angleY', 'ay',
        'angleZ', 'az'
        ]
        if filter( lambda x: x in args, kwargs.keys()):
            res = res[0]
    elif res is not None:    
        res = PyNode(res)
    return res

def _constraint( func ):

    def constraint(*args, **kwargs):
        """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
Modifications:
    - added new syntax for querying the weight of a target object, by passing the constraint first::
    
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
        """
        if kwargs.get( 'query', kwargs.get('q', False) ) :
            attrs = [
            'upVector', 'u',
            'worldUpVector', 'wu',
            'aimVector', 'a' ]
            
            for attr in attrs:
                if attr in kwargs:
                    return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                    
            
        if len(args)==1:
            
            try:        
                # this will cause a KeyError if neither flag has been set. this quickly gets us out of if section if
                # we're not concerned with weights
                targetObjects = kwargs.get( 'weight', kwargs['w'] ) 
                constraint = args[0]
                if 'constraint' in cmds.cmds.nodeType( constraint, inherited=1 ):
                    print constraint
                    if not pymel.util.isIterable( targetObjects ):
                        targetObjects = [targetObjects]
                    elif not targetObjects:
                        targetObjects = func( constraint, q=1, targetList=1 )
    
                    constraintObj = cmds.listConnections( constraint + '.constraintParentInverseMatrix', s=1, d=0 )[0]    
                    args = targetObjects + [constraintObj]
                    kwargs.pop('w',None)
                    kwargs['weight'] = True
            except: pass
                
        res = func(*args, **kwargs)
        return res
    
    constraint.__name__ = func.__name__
    return constraint

#aimConstraint = _constraint( cmds.aimConstraint )
#geometryConstraint = _constraint( cmds.geometryConstraint )
#normalConstraint = _constraint( cmds.normalConstraint )
#orientConstraint = _constraint( cmds.orientConstraint )
#pointConstraint = _constraint( cmds.pointConstraint )
#scaleConstraint = _constraint( cmds.scaleConstraint )


def aimConstraint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
Modifications:
    - added new syntax for querying the weight of a target object, by passing the constraint first::
    
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
    """
    
    if kwargs.get( 'query', kwargs.get('q', False) ) :
        attrs = [
        'upVector', 'u',
        'worldUpVector', 'wu',
        'aimVector', 'a' ]
        
        for attr in attrs:
            if attr in kwargs:
                return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                
        
    if len(args)==1:
        
        try:        
            # this will cause a KeyError if neither flag has been set. this quickly gets us out of if section if
            # we're not concerned with weights
            targetObjects = kwargs.get( 'weight', kwargs['w'] ) 
            constraint = args[0]
            if 'constraint' in cmds.cmds.nodeType( constraint, inherited=1 ):
                print constraint
                if not pymel.util.isIterable( targetObjects ):
                    targetObjects = [targetObjects]
                elif not targetObjects:
                    targetObjects = cmds.aimConstraint( constraint, q=1, targetList=1 )

                constraintObj = cmds.listConnections( constraint + '.constraintParentInverseMatrix', s=1, d=0 )[0]    
                args = targetObjects + [constraintObj]
                kwargs.pop('w',None)
                kwargs['weight'] = True
        except: pass
            
    res = cmds.aimConstraint(*args, **kwargs)
    return res


def normalConstraint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
    """
    if 'query' in kwargs or 'q' in kwargs:
        
        attrs = [
        'upVector', 'u',
        'worldUpVector', 'wu',
        'aimVector', 'a' ]
        
        for attr in attrs:
            if attr in kwargs:
                return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                
            
    res = cmds.normalConstraint(*args, **kwargs)
    return res


def pointLight(*args,**kwargs):
    """
Maya Bug Fix:
    - name flag was ignored
    """    
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.pointLight(*args, **kwargs)
    
    else:    
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.pointLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'pointLight' )
    
    return PyNode( cmds.pointLight(*args, **kwargs), 'pointLight'  )

def spotLight(*args,**kwargs):
    """
Maya Bug Fix:
    - name flag was ignored
    """    
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.spotLight(*args, **kwargs)
    
    else:    
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.spotLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'spotLight' )
    
    return PyNode( cmds.spotLight(*args, **kwargs), 'spotLight'  )

def directionalLight(*args,**kwargs):
    """
Maya Bug Fix:
    - name flag was ignored
    """    
    
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.directionalLight(*args, **kwargs)
    
    else:    
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.directionalLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'directionalLight' )
    
    return PyNode( cmds.directionalLight(*args, **kwargs), 'directionalLight'  )

def ambientLight(*args,**kwargs):
    """
Maya Bug Fix:
    - name flag was ignored
    """    
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.ambientLight(*args, **kwargs)
    
    else:    
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.ambientLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'ambientLight' )
    
    return PyNode( cmds.ambientLight(*args, **kwargs), 'ambientLight'  )
                                
def spaceLocator(*args, **kwargs):
    """
Modifications:
    - returns a locator instead of a list with a single locator
    """
    res = cmds.spaceLocator(**kwargs)
    try:
        return Transform(res[0])
    except:
        return res
    
def instancer(*args, **kwargs):
    """
Maya Bug Fix:
    - name of newly created instancer was not returned
    """    
    if kwargs.get('query', kwargs.get('q',False)):
        return cmds.instancer(*args, **kwargs)
    if kwargs.get('edit', kwargs.get('e',False)):
        cmds.instancer(*args, **kwargs)
        return PyNode( args[0], 'instancer' )
    else:
        instancers = cmds.ls(type='instancer')
        cmds.instancer(*args, **kwargs)
        return PyNode( list( set(cmds.ls(type='instancer')).difference( instancers ) )[0], 'instancer' )


def getPymelType(obj, comp=None) :
    """ Get the correct Pymel Type for an object that can be a MObject, PyNode or name of an existing Maya object,
        if no correct type is found returns DependNode by default """
        
    objHandle = None
    objName = None
    # TODO : handle comp as a MComponent or list of components
    if isinstance(obj, PyNode) :
        objHandle = obj._object
    elif isinstance(obj, pymel.util.api.MObject) :
        objHandle = pymel.util.api.MObjectHandle(obj)
    elif isinstance(obj,basestring) :
        objName = obj
        obj = pymel.util.api.toMObject (obj)
        if obj is not None :
            objHandle = pymel.util.api.MObjectHandle(obj)   

    pymelType = DependNode
    if '.' in objName :
        # TODO : some better checking / parsing
        pymelType = Attribute                                           
    elif pymel.util.api.isValidMObjectHandle(objHandle) :
        obj = objHandle.object()
        objType = pymel.util.api.apiEnumToNodeType(obj.apiType ())
        try :
            pymelType = getattr(_thisModule, pymel.util.capitalize(objType))
        except :
            pymelType = DependNode
    else :
        # non existing node
        pymelType = basestring
    
    return pymelType  

#--------------------------
# Object Wrapper Classes
#--------------------------

class PyNode(object):
    """ Abstract class that is base for all pymel nodes classes, will try to detect argument type if called directly
        and defer to the correct derived class """
    #__metaclass__ = metaNode
    
    _name = None              # unicode
    _object = None            # pymel.util.api.MObjectHandle()
    
    def __new__(cls, *args, **kwargs):
        """ Catch all creation for PyNode classes, creates correct class depending on type passed """
        
        if args :
            obj = args[0]
            comp = None
            if len(args)>1 :
                comp = args[1]
            pymelType = getPymelType(obj, comp)
        else :
            pymelType = DependNode
        
        # print "PyNode __new__ : called with obj=%r, cls=%r, on object of type %s" % (obj, cls, pymelType)
        # if an explicit class was given (ie: pyObj=DagNode('pCube1')) just check if actual type is compatible
        # if none was given (ie generic pyObj=PyNode('pCube1')) then use the class corresponding to the type we found
        if cls is not PyNode :
            # a PyNode class was explicitely required, if an existing object was passed to init check that the object type
            # is compatible with the required class, if no existing object was passed, create an empty PyNode of the required class
            # TODO : can add object creation option in the __init__ if desired
            if issubclass(pymelType, basestring) :
                pymelType = cls            
            if issubclass(pymelType, cls) :
                return super(PyNode, cls).__new__(cls)
            else :
                raise TypeError, "Cannot make a %s PyNode out of a %s object" % (cls.__name__, pymelType.__name__)
        else :
            # no class name specified, use pymelType, default to DependNode if just a string that isn't an existing object was passed
            if issubclass(pymelType, basestring) :
                pymelType = DependNode
            return super(PyNode, cls).__new__(pymelType)
   

    
    def stripNamespace(self, levels=0):
        """
        Returns a new instance of the object with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.
        """
        
        nodes = []
        for x in self.split('|'):
            y = x.split('.')
            z = y[0].split(':')
            if levels:
                y[0] = ':'.join( z[min(len(z)-1,levels):] )
    
            else:
                y[0] = z[-1]
            nodes.append( '.'.join( y ) )
        return self.__class__( '|'.join( nodes) )

    def swapNamespace(self, prefix):
        """Returns a new instance of the object with its current namespace replaced with the provided one.  
        The calling instance is unaffected."""    
        return DependNode.addPrefix( self.stripNamespace(), prefix+':' )
            
    def namespaceList(self):
        """Useful for cascading references.  Returns all of the namespaces of the calling object as a list"""
        return self.lstrip('|').rstrip('|').split('|')[-1].split(':')[:-1]
            
    def namespace(self):
        """Returns the namespace of the object with trailing colon included"""
        return ':'.join(self.namespaceList()) + ':'
        
    def addPrefix(self, prefix):
        'addPrefixToName'
        name = self
        leadingSlash = False
        if name.startswith('|'):
            name = name[1:]
            leadingSlash = True
        name = self.__class__( '|'.join( map( lambda x: prefix+x, name.split('|') ) ) )
        if leadingSlash:
            name = '|' + name
        return self.__class__( name )
                
                        
    def attr(self, attr):
        """access to attribute of a node. returns an instance of the Attribute class for the 
        given attribute."""
        return Attribute( '%s.%s' % (self, attr) )
                
    objExists = cmds.objExists
        
    cmds.nodeType = cmds.nodeType

    def select(self, **kwargs):
        forbiddenKeys = ['all', 'allDependencyNodes', 'adn', '-allDagObjects' 'ado', 'clear', 'cl']
        for key in forbiddenKeys:
            if key in kwargs:
                raise TypeError, "'%s' is an inappropriate keyword argument for object-oriented implementation of this command" % key
        
        return cmds.select( self, **kwargs )    

    def deselect( self ):
        self.select( deselect=1 )
    
    listConnections = pymel.core.core.listConnections
        
    connections = pymel.core.core.listConnections

    listHistory = pymel.core.core.listHistory
        
    history = pymel.core.core.listHistory

    listFuture = pymel.core.core.listFuture
                
    future = pymel.core.core.listFuture


                    
class ComponentArray(object):
    def __init__(self, name):
        self._name = name
        self._iterIndex = 0
        self._node = self.node()
        
    def __str__(self):
        return self._name
        
    def __repr__(self):
        return "ComponentArray('%s')" % self
    
    #def __len__(self):
    #    return 0
        
    def __iter__(self):
        """iterator for multi-attributes
        
            >>> for attr in SCENE.Nexus1.attrInfo(multi=1)[0]: print attr
            
        """
        return self
                
    def next(self):
        """iterator for multi-attributes
        
            >>> for attr in SCENE.Nexus1.attrInfo(multi=1)[0]: print attr
            
        """
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
        
        '''    
        if isinstance( item, tuple ):            
            return [ Component('%s[%s]' % (self, formatSlice(x)) ) for x in  item ]
            
        elif isinstance( item, slice ):
            return Component('%s[%s]' % (self, formatSlice(item) ) )

        else:
            return Component('%s[%s]' % (self, item) )
        '''
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
                
class Component(object):
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
    
                
class Attribute(PyNode):
    """
    Attributes
    ==========
    
    The Attribute class is your one-stop shop for all attribute related functions. Modifying attributes follows a fairly
    simple pattern:  `setAttr` becomes L{set<Attribute.set>}, `getAttr` becomes L{get<Attribute.get>}, `connectAttr`
    becomes L{connect<Attribute.connect>} and so on.  
    
    Accessing Attributes
    --------------------
    Most of the time, you will access instances of the Attribute class via `DependNode` or one of its subclasses. This example demonstrates
    that the Attribute class like the `DependNode` classes are based on a unicode string, and so when printed will 
    
        >>> s = polySphere()[0]
        >>> if s.visibility.isKeyable() and not s.visibility.isLocked():
        >>>     s.visibility = True
        >>>     s.visibility.lock()
        
        >>> print s.v.type()      # shortnames also work    
        bool
    
    Note that when the attribute is created there is currently no check for whether or not the attribute exists, just as there is 
    no check when creating instances of DependNode classes. This is both for speed and also because it can be useful to get a virtual
    representation of an object or attribute before it exists. 

    Getting Attribute Values
    ------------------------
    To get an attribute, you use the L{'get'<Attribute.get>} method. Keep in mind that, where applicable, the values returned will 
    be cast to pymel classes. This example shows that rotation (along with translation and scale) will be returned as `pymel.core.core.Vector`.
    
        >>> rot = s.rotate.get()
        >>> print rot
        [0.0, 0.0, 0.0]
        >>> print type(rot) # rotation is returned as a vector class
        <class 'pymel.core.vector.pymel.core.core.Vector'>

    Setting Attributes Values
    -------------------------
    there are several ways to set attributes in pymel.core.  maybe there's too many....
    
        >>> s.rotate.set([4,5,6])   # you can pass triples as a list
        >>> s.rotate.set(4,5,6)     # or not    
        >>> s.rotate = [4,5,6]      # my personal favorite

    Connecting Attributes
    ---------------------
    Since the Attribute class inherits the builtin string, you can just pass the Attribute to the `connect` method. The string formatting
    is handled for you.
                
        >>> s.rotateX.connect( s.rotateY )
    
    there are also handy operators for L{connect<Attribute.__rshift__>} and L{disconnect<Attribute.__ne__>}

        >>> c = polyCube()[0]        
        >>> s.tx >> c.tx    # connect
        >>> s.tx <> c.tx    # disconnect
            
    Avoiding Clashes between Attributes and Class Methods
    -----------------------------------------------------
    All of the examples so far have shown the shorthand syntax for accessing an attribute. The shorthand syntax has the most readability, 
    but it has the drawaback that if the attribute that you wish to acess has the same name as one of the class methods of the node
    then an error will be raised. There is an alternatives which will avoid this pitfall.
            
    attr Method
    ~~~~~~~~~~~
    The attr method is the safest way the access an attribute, and can even be used to access attributes that conflict with 
    python's own special methods, and which would fail using shorthand syntax. This method is passed a string which
    is the name of the attribute to be accessed. This gives it the added advantage of being capable of recieving attributes which 
    are determine at runtime: 
    
        >>> s.addAttr('__init__')
        >>> s.attr('__init__').set( .5 )
        >>> for axis in ['X', 'Y', 'Z']: s.attr( 'translate' + axis ).lock()    
    """
    attrItemReg = re.compile( '\[(\d+)\]$')
    
    #def __repr__(self):
    #    return "Attribute('%s')" % self
            
    def __init__(self, attrName):
        if '.' not in attrName:
            raise TypeError, "%s: Attributes must include the node and the attribute. e.g. 'nodeName.attributeName' " % self
        self._name = attrName
        # TODO : MObject support
        self.__dict__['_multiattrIndex'] = 0
        
    def __getitem__(self, item):
       return Attribute('%s[%s]' % (self, item) )

    # Added the __call__ so to generate a more appropriate exception when a class method is not found 
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" % (repr(self.node()), self.plugAttr()))
    
    '''
    def __iter__(self):
        """iterator for multi-attributes
        
            >>> for attr in SCENE.Nexus1.attrInfo(multi=1)[0]: print attr
            
        """
        if self.isMulti():
            return self
        else:
            raise TypeError, "%s is not a multi-attribute and cannot be iterated over" % self
            
    def next(self):
        """iterator for multi-attributes
        
            >>> for attr in SCENE.Nexus1.attrInfo(multi=1)[0]: print attr
            
        """
        if self.__dict__['_multiattrIndex'] >= self.size():
            raise StopIteration
        else:            
            attr = Attribute('%s[%s]' % (self, self.__dict__['_multiattrIndex']) )
            self.__dict__['_multiattrIndex'] += 1
            return attr
    '''        
 
 
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self.name())

    def __str__(self):
        return "%s" % self.name()

    def __unicode__(self):
        return u"%s" % self.name()

    def name(self):
        """ Returns the full name of that attribute(plug) """
        return self._name
    
    def nodeName(self):
        """ Returns the node name of that attribute(plug) """
        pass
    
    def attributeName(self):
        pass
    
    def attributeNames(self):
        pass
       
    def array(self):
        """
        Returns the array (multi) attribute of the current element
            >>> n = Attribute('lambert1.groupNodes[0]')
            >>> n.array()
            'lambert1.groupNode'
        """
        try:
            att = Attribute(Attribute.attrItemReg.split( self )[0])
            if att.isMulti() :
                return att
            else :
                raise TypeError, "%s is not a multi attribute" % self
        except:
            raise TypeError, "%s is not a multi attribute" % self


    # TODO : do not list all children elements by default, allow to do 
    #        skinCluster1.weightList.elements() for first level elements weightList[x]
    #        or skinCluster1.weightList.weights.elements() for all weightList[x].weights[y]

    def elements(self):
        return cmds.listAttr(self.array(), multi=True)
        
    def isElement(self):
        """ Is the attribute an element of a multi attribute """
        return (Attribute.attrItemReg.search(str(self).split('.')[-1]) is not None)

    def plugNode(self):
        'plugNode'
        return PyNode( str(self).split('.')[0])
                
    def plugAttr(self):
        """plugAttr
        
            >>> SCENE.persp.t.tx.plugAttr()
            't.tx'
        """
        return '.'.join(str(self).split('.')[1:])
    
    def lastPlugAttr(self):
        """
        
            >>> SCENE.persp.t.tx.lastPlugAttr()
            'tx'
        """
        return Attribute.attrItemReg.split( self.split('.')[-1] )[0]
        
    node = plugNode
    
    def nodeName( self ):
        'basename'
        return self.split('|')[-1]
    
    def item(self):
        try: 
            return int(Attribute.attrItemReg.search(self).group(1))
        except: return None
    
    def setEnums(self, enumList):
        cmds.addAttr( self, e=1, en=":".join(enumList) )
    
    def getEnums(self):
        return cmds.addAttr( self, q=1, en=1 ).split(':')    
            
    # getting and setting                    
    set = pymel.core.core.setAttr            
    get = pymel.core.core.getAttr
    setKey = pymel.core.anim.setKeyframe    
    
    
    #----------------------
    # Connections
    #----------------------    
                    
    isConnected = cmds.isConnected
    
            
    #def __irshift__(self, other):
    #    """operator for 'isConnected'
    #        sphere.tx >>= box.tx
    #    """ 
    #    print self, other, cmds.isConnected(self, other)
    #    return cmds.isConnected(self, other)
    

    connect = pymel.core.core.connectAttr
        
    def __rshift__(self, other):
        """operator for 'connectAttr'
            sphere.tx >> box.tx
        """ 
        return pymel.core.core.connectAttr( self, other, force=True )
                
    disconnect = pymel.core.core.disconnectAttr

    def __ne__(self, other):
        """operator for 'disconnectAttr'
            sphere.tx <> box.tx
        """ 
        return cmds.disconnectAttr( self, other )
                
    def inputs(self, **kwargs):
        'pymel.core.core.listConnections -source 1 -destination 0'
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        
        return pymel.core.core.listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        'pymel.core.core.listConnections -source 0 -destination 1'
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return pymel.core.core.listConnections(self, **kwargs)
    
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

    #----------------------
    # Modification
    #----------------------
    
    def alias(self, **kwargs):
        """aliasAttr"""
        return cmds.aliasAttr( self, **kwargs )    
                            
    def add( self, **kwargs):    
        kwargs['longName'] = self.plugAttr()
        kwargs.pop('ln', None )
        return addAttr( self.node(), **kwargs )    
                    
    def delete(self):
        """deleteAttr"""
        return cmds.deleteAttr( self )
    
    def remove( self, **kwargs):
        'removeMultiInstance'
        #kwargs['break'] = True
        return cmds.removeMultiInstance( self, **kwargs )
        
    # Edge, Vertex, CV Methods
    def getTranslation( self, **kwargs ):
        """xform -translation"""
        kwargs['translation'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
        
    #----------------------
    # Info Methods
    #----------------------
    
    def isDirty(self, **kwargs):
        return cmds.isDirty(self, **kwargs)
        
    def affects( self, **kwargs ):
        return map( lambda x: Attribute( '%s.%s' % ( self.node(), x )),
            cmds.affects( self.plugAttr(), self.node()  ) )

    def affected( self, **kwargs ):
        return map( lambda x: Attribute( '%s.%s' % ( self.node(), x )),
            cmds.affects( self.plugAttr(), self.node(), by=True  ))
                
    # getAttr info methods
    def type(self):
        "getAttr -type"
        return cmds.getAttr(self, type=True)
        
    def isKeyable(self):
        "getAttr -keyable"
        return cmds.getAttr(self, keyable=True)
            
    def size(self):
        "getAttr -size"
        return cmds.getAttr(self, size=True)    
    
    def isLocked(self):
        "getAttr -lock"
        return cmds.getAttr(self, lock=True)    

    def isSettable(self):
        "getAttr -settable"
        return cmds.getAttr(self, settable=True)

    def isCaching(self):
        "getAttr -caching"
        return cmds.getAttr(self, caching=True)
        
    def isInChannelBox(self):
        "getAttr -channelBox"
        return cmds.getAttr(self, channelBox=True)    
        
    # setAttr property methods
    def setKeyable(self, state):
        "setAttr -keyable"
        return cmds.setAttr(self, keyable=state)
            
    def setLocked(self, state):
        "setAttr -locked"
        return cmds.setAttr(self, lock=state)
        
    def lock(self):
        "setAttr -locked 1"
        return cmds.setAttr(self, lock=True)
        
    def unlock(self):
        "setAttr -locked 0"
        return cmds.setAttr(self, lock=False)
                
    def setCaching(self, state):
        "setAttr -caching"
        return cmds.setAttr(self, caching=state)
                
    def showInChannelBox(self, state):
        "setAttr -channelBox"
        return cmds.setAttr(self, channelBox=state)    
    
    # attributeQuery info methods
    def isHidden(self):
        "attributeQuery -hidden"
        return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), hidden=True)
        
    def isConnectable(self):
        "attributeQuery -connectable"
        return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), connectable=True)    

    def isMulti(self):
        "attributeQuery -multi"
        return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), multi=True)    
    
    def exists(self):
        "attributeQuery -exists"
        try:
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), exists=True)    
        except TypeError:
            return False
            
    def longName(self):
        "attributeQuery -longName"
        return cmds.attributeQuery( self.lastPlugAttr(), node=self.node(), longName=True)
        
    def shortName(self):
        "attributeQuery -shortName"
        return cmds.attributeQuery( self.lastPlugAttr(), node=self.node(), shortName=True)
            
    def getSoftMin(self):
        """attributeQuery -softMin
            Returns None if softMin does not exist."""
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMinExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMin=True)[0]    
            
    def getSoftMax(self):
        """attributeQuery -softMax
            Returns None if softMax does not exist."""
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMaxExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), softMax=True)[0]
    
    def getMin(self):
        """attributeQuery -min
            Returns None if min does not exist."""
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), minExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), min=True)[0]
            
    def getMax(self):
        """attributeQuery -max
            Returns None if max does not exist."""
        if cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), maxExists=True):
            return cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), max=True)[0]
    
    def getSoftRange(self):
        """attributeQuery -softRange
            returns a two-element list containing softMin and softMax. if the attribute does not have
            a softMin or softMax the corresponding element in the list will be set to None."""
        softRange = []
        softRange.append( self.getSoftMin() )
        softRange.append( self.getSoftMax() )
        return softRange
    
            
    def getRange(self):
        """attributeQuery -range
            returns a two-element list containing min and max. if the attribute does not have
            a softMin or softMax the corresponding element will be set to None."""
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
        
            >>> s = polyCube()[0]
            >>> s.addAttr( 'new' )
            >>> s.new.setRange( -2, None ) #sets just the min to -2 and removes the max limit
            >>> s.new.setMax( 3 ) # sets just the max value and leaves the min at its previous default 
            >>> s.new.getRange()
            [-2.0, 3.0 ]
            
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


    def getChildren(self):
        """attributeQuery -listChildren"""
        return map( 
            lambda x: Attribute( self.node() + '.' + x ), 
            pymel.util.listForNone( cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), listChildren=True) )
                )


    def getSiblings(self):
        """attributeQuery -listSiblings"""
        return map( 
            lambda x: Attribute( self.node() + '.' + x ), 
            pymel.util.listForNone( cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), listSiblings=True) )
                )

        
    def getParent(self):
        """attributeQuery -listParent"""    
        
        if self.count('.') > 1:
            return Attribute('.'.join(self.split('.')[:-1]))
        try:
            return Attribute( self.node() + '.' + cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), listParent=True)[0] )
        except TypeError:
            return None
    
        
'''
class NodeAttrRelay(unicode):
    
    def __getattr__(self, attr):
        if attr.startswith('_'):
            return getAttr( '%s.%s' % (self, attr[1:]) )        
        return getAttr( '%s.%s' % (self, attr) )
    
    def __setattr__(self, attr, val):
        if attr.startswith('_'):
            return setAttr( '%s.%s' % (self, attr[1:]), val )            
        return setAttr( '%s.%s' % (self, attr), val )    
'''

class DependNode( PyNode ):
    #-------------------------------
    #    Name Info and Manipulation
    #-------------------------------
#    def __new__(cls,name,create=False):
#        """
#        Provides the ability to create the object when creating a class
#        
#            >>> n = pm.Transform("persp",create=True)
#            >>> n.__repr__()
#            # Result: Transform('persp1')
#        """
#        if create:
#            ntype = pymel.util.uncapitalize(cls.__name__)
#            name = createNode(ntype,n=name,ss=1)
#        return PyNode.__new__(cls,name)

    def _updateName(self) :
        if pymel.util.api.isValidMObjectHandle(self._object) :
            obj = self._object.object()
            depFn = pymel.util.api.MFnDependencyNode(obj)
            self._name = depFn.name()
        return self._name 

    def object(self) :
        if pymel.util.api.isValidMObjectHandle(self._object) :
            return self._object.object()
        
    def name(self, update=True) :
        if update :
            return self._updateName()
        else :
            return self._name  

    def __init__(self, handleOrName) :
        if isinstance(handleOrName, DependNode) :
            self._name = unicode(handleOrName.name())
            self._object = pymel.util.api.MObjectHandle(handleOrName.object())
        elif pymel.util.api.isValidMObject(handleOrName) or pymel.util.api.isValidMObjectHandle(handleOrName) :
            self._object = pymel.util.api.MObjectHandle(handleOrName)
            self._updateName()
        elif isinstance(handleOrName, basestring) :
            obj = pymel.util.api.toMObject (handleOrName)
            if pymel.util.api.isValidMObject(obj) :
                # actual Maya object creation
                self._object = pymel.util.api.MObjectHandle(obj)
                self._updateName()
            else :
                # non existent object
                self._name = handleOrName 
        else :
            raise TypeError, "don't know how to make a Pymel DependencyNode out of a %s : %r" % (type(handleOrName), handleOrName)  

    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self.name())

    def __str__(self):
        return "%s" % self.name()

    def __unicode__(self):
        return u"%s" % self.name()
    
    def node(self):
        """for compatibility with Attribute class"""
        return self
        
    def __getattr__(self, attr):
        try :
            return super(PyNode, self).__getattr__(attr)
        except AttributeError :
            return Attribute( '%s.%s' % (self, attr) )
        
        #if attr.startswith('__') and attr.endswith('__'):
        #    return super(PyNode, self).__getattr__(attr)
            
        #return Attribute( '%s.%s' % (self, attr) )
        
        #raise AttributeError, 'attribute does not exist %s' % attr

    def __setattr__(self, attr, val):
        try :
            return super(PyNode, self).__setattr__(attr, val)
        except AttributeError :
            return pymel.core.core.setAttr( '%s.%s' % (self, attr), val ) 


        # if attr.startswith('__') and attr.endswith('__'):
        #     return super(PyNode, self).__setattr__(attr, val)        
        # return setAttr( '%s.%s' % (self, attr), val )

    #--------------------------
    #    Modification
    #--------------------------
        
    def lock( self, **kwargs ):
        'lockNode -lock 1'
        kwargs['lock'] = True
        kwargs.pop('l',None)
        return cmds.lockNode( self, **kwargs)
        
    def unlock( self, **kwargs ):
        'lockNode -lock 0'
        kwargs['lock'] = False
        kwargs.pop('l',None)
        return cmds.lockNode( self, **kwargs)
            
    def cast( self, swapNode, **kwargs):
        """nodeCast"""
        return cmds.nodeCast( self, swapNode, *kwargs )
    
    rename = pymel.core.core.rename
    
    duplicate = pymel.core.core.duplicate
    
    #--------------------------
    #    Presets
    #--------------------------
    
    def savePreset(self, presetName, custom=None, attributes=[]):
        
        kwargs = {'save':True}
        if attributes:
            kwargs['attributes'] = ' '.join(attributes)
        if custom:
            kwargs['custom'] = custom
            
        return cmds.nodePrest( presetName, **kwargs)
        
    def loadPreset(self, presetName):
        kwargs = {'load':True}
        return cmds.nodePrest( presetName, **kwargs)
        
    def deletePreset(self, presetName):
        kwargs = {'delete':True}
        return cmds.nodePrest( presetName, **kwargs)
        
    def listPresets(self):
        kwargs = {'list':True}
        return cmds.nodePrest( presetName, **kwargs)
            
    #--------------------------
    #    Info
    #--------------------------

    def type(self, **kwargs):
        "nodetype"        
        return self.cmds.nodeType(**kwargs)
            
    def exists(self, **kwargs):
        "cmds.objExists"
        return self.cmds.objExists(**kwargs)
        
    def isReadOnly(self):
        return (cmds.ls( self, ro=1) and True) or False
        
    def referenceFile(self):
        """referenceQuery -file
        Return the reference file to which this object belongs.  None if object is not referenced"""
        try:
            return FileReference( cmds.referenceQuery( self, f=1) )
        except:
            None
            
    def isReferenced(self):
        """referenceQuery -isNodeReferenced
        Return True or False if the node is referenced"""    
        return cmds.referenceQuery( self, isNodeReferenced=1)

            
    def classification(self):
        'getClassification'
        return getClassification( self.type() )    
    
    #--------------------------
    #    Connections
    #--------------------------    
    
    def inputs(self, **kwargs):
        'pymel.core.core.listConnections -source 1 -destination 0'
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return pymel.core.core.listConnections(self, **kwargs)
    
    def outputs(self, **kwargs):
        'pymel.core.core.listConnections -source 0 -destination 1'
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return pymel.core.core.listConnections(self, **kwargs)                            

    def sources(self, **kwargs):
        'pymel.core.core.listConnections -source 1 -destination 0'
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return pymel.core.core.listConnections(self, **kwargs)
    
    def destinations(self, **kwargs):
        'pymel.core.core.listConnections -source 0 -destination 1'
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )
        
        return pymel.core.core.listConnections(self, **kwargs)    
        
    def shadingGroups(self):
        """list any shading groups in the future of this object - works for shading nodes, transforms, and shapes """
        return self.future(type='shadingEngine')
        
        
    #--------------------------
    #    Attributes
    #--------------------------        
        
    def setAttr( self, attr, *args, **kwargs):
        return self.attr(attr).set( *args, **kwargs )
            
    def getAttr( self, attr, **kwargs ):
        return self.attr(attr).get( **kwargs )

    def addAttr( self, attr, **kwargs):        
        return self.attr(attr).add( **kwargs )
            
    def connectAttr( self, attr, *args, **kwargs ):
        return cmds.attr(attr).connect( *args, **kwargs )

    def disconnectAttr( self, source, destination=None, **kwargs ):
        if destination:
            return cmds.disconnectAttr( "%s.%s" % (self, source), destination, **kwargs )
        else:
            for destination in self.outputs( plugs=True ):
                cmds.disconnectAttr( "%s.%s" % (self, source), destination, **kwargs )
                    
    listAnimatable = pymel.core.core.listAnimatable

    def listAttr( self, **kwargs):
        "listAttr"
        return map( lambda x: PyNode( '%s.%s' % (self, x) ), pymel.util.listForNone(cmds.listAttr(self, **kwargs)))

    def attrInfo( self, **kwargs):
        "attributeInfo"
        return map( lambda x: PyNode( '%s.%s' % (self, x) ), pymel.util.listForNone(cmds.attributeInfo(self, **kwargs)))
            
    _numPartReg = re.compile('([0-9]+)$')
    
    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged."""
        try:
            return DependNode._numPartReg.split(self)[0]
        except:
            return unicode(self)
            
    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised."""
        
        try:
            return DependNode._numPartReg.split(self)[1]
        except:
            raise "No trailing numbers to extract on object ", self

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found"""
        name = self.shortName().nextName()
        while name.exists():
            name = name.nextName()
        return name
                
    def nextName(self):
        """Increment the trailing number of the object by 1"""
        try:
            groups = DependNode._numPartReg.split(self)
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return self.__class__(formatStr % ( groups[0], (int(num) + 1) ))
        except:
            raise "could not find trailing numbers to increment"
            
    def prevName(self):
        """Decrement the trailing number of the object by 1"""
        try:
            groups = DependNode._numPartReg.split(self)
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return self.__class__(formatStr % ( groups[0], (int(num) - 1) ))
        except:
            raise "could not find trailing numbers to decrement"

class Entity(DependNode): pass
class DagNode(Entity):
    
    def _updateName(self, long=False) :
        if pymel.util.api.isValidMObjectHandle(self._object) :
            obj = self._object.object()
            dagFn = pymel.util.api.MFnDagNode(obj)
            dagPath = pymel.util.api.MDagPath()
            dagFn.getPath(dagPath)
            self._name = dagPath.partialPathName()
            if long :
                return dagPath.fullPathName()
        return self._name                       

    def object(self) :
        if pymel.util.api.isValidMObjectHandle(self._object) :
            return self._object.object()
        
    def name(self, update=True, long=False) :
        if update or long :
            return self._updateName(long)
        else :
            return self._name  
    
    def __init__(self, handleOrName) :
        if isinstance(handleOrName, DagNode) :
            self._name = unicode(handleOrName.name())
            self._object = pymel.util.api.MObjectHandle(handleOrName.object())
        elif pymel.util.api.isValidMObject(handleOrName) or pymel.util.api.isValidMObjectHandle(handleOrName) :
            objHandle = pymel.util.api.MObjectHandle(handleOrName)
            obj = objHandle.object() 
            if pymel.util.api.isValidMDagNode(obj) :
                self._object = objHandle
                self._updateName()
            else :
                raise TypeError, "%r might be a dependencyNode, but not a dagNode" % handleOrName              
        elif isinstance(handleOrName, basestring) :
            obj = pymel.util.api.toMObject (handleOrName)
            if pymel.util.api.isValidMObject(obj) :
                # creation for existing object
                if pymel.util.api.isValidMDagNode (obj):
                    self._object = pymel.util.api.MObjectHandle(pymel.util.api.toMObject (handleOrName))
                    self._updateName()
                else :
                    raise TypeError, "%r might be a dependencyNode, but not a dagNode" % handleOrName 
            else :
                # creation for inexistent object 
                self._name = handleOrName
        else :
            raise TypeError, "don't know how to make a DagNode out of a %s : %r" % (type(handleOrName), handleOrName)  
          
    
    def __eq__(self, other):
        """ensures that we compare longnames when checking for dag node equality"""
        try:
            return unicode(self.longName()) == unicode(DagNode(other).longName())
        except (TypeError,IndexError):
            return unicode(self) == unicode(other)
            
    def __ne__(self, other):
        """ensures that we compare longnames when checking for dag node equality"""
        try:
            return unicode(self.longName()) != unicode(DagNode(other).longName())
        except (TypeError,IndexError):
            return unicode(self) != unicode(other)    
            
    #--------------------------
    #    DagNode Path Info
    #--------------------------    
    def root(self):
        'rootOf'
        return DagNode( '|' + self.longName()[1:].split('|')[0] )
    
    def firstParent(self):
        'firstParentOf'
        try:
            return DagNode( '|'.join( self.longName().split('|')[:-1] ) )
        except TypeError:
            return DagNode( '|'.join( self.split('|')[:-1] ) )
    
    def getParent(self, **kwargs):
        """unlike the firstParent command which determines the parent via string formatting, this 
        command uses the pymel.core.core.listRelatives command"""
        
        kwargs['parent'] = True
        kwargs.pop('p',None)
        #if longNames:
        kwargs['fullPath'] = True
        kwargs.pop('p',None)
        
        try:
            res = cmds.listRelatives( self, **kwargs)[0]
        except TypeError:
            return None
             
        res = Transform( res )
        if not longNames:
            return res.shortName()
        return res
                    
    def getChildren(self, **kwargs ):
        kwargs['children'] = True
        kwargs.pop('c',None)

        return pymel.core.core.listRelatives( self, **kwargs)
        
    def getSiblings(self, **kwargs ):
        #pass
        try:
            return [ x for x in self.getParent().getChildren() if x != self]
        except:
            return []
                
    def listRelatives(self, **kwargs ):
        return pymel.core.core.listRelatives( self, **kwargs)
        
    def longName(self):
        'longNameOf'
        return self.name(long=True)
            
    def shortName( self ):
        'shortNameOf'
        return self.name(long=False)

    def nodeName( self ):
        'basename'
        return self.name().split('|')[-1]

        
    #--------------------------
    #    DagNode Path Modification
    #--------------------------    
    
    def setParent( self, *args, **kwargs ):
        'parent'
        return self.__class__( cmds.parent( self, *args, **kwargs )[0] )
                
    #instance = pymel.core.core.instance

    #--------------------------
    #    Shading
    #--------------------------    

    def isDisplaced(self):
        """Returns whether any of this object's shading groups have a displacement shader input"""
        for sg in self.shadingGroups():
            if len( sg.attr('displacementShader').inputs() ):
                return True
        return False

    def setColor( self, color=None ):
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
    def getTransform(self): pass    
#class Joint(Transform):
#    pass

        
class Camera(Shape):
    __metaclass__ = metaNode
    def getFov(self):
        aperture = self.horizontalFilmAperture.get()
        fov = (0.5 * aperture) / (self.focalLength.get() * 0.03937)
        fov = 2.0 * atan (fov)
        fov = 57.29578 * fov
        return fov
        
    def setFov(self, fov):
        aperture = self.horizontalFilmAperture.get()
        focal = tan (0.00872665 * fov);
        focal = (0.5 * aperture) / (focal * 0.03937);
        self.focalLength.set(focal)
    
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
    
    dolly = pymel.util.factories.functionFactory('dolly', None, cmds )
    roll = pymel.util.factories.functionFactory('roll', None, cmds )
    orbit = pymel.util.factories.functionFactory('orbit', None, cmds )
    track = pymel.util.factories.functionFactory('track', None, cmds )
    tumble = pymel.util.factories.functionFactory('tumble', None, cmds )
    
            
class Transform(DagNode):
    __metaclass__ = metaNode
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
    # workaround for conflict with translate method on basestring
    def _getTranslate(self):
        return self.__getattr__("translate")
    def _setTranslate(self, val):
        return self.__setattr__("translate", val)        
    translate = property( _getTranslate , _setTranslate )
    
    def hide(self):
        self.visibility.set(0)
        
    def show(self):
        self.visibility.set(1)
                
    def getShape( self, **kwargs ):
        kwargs['shapes'] = True
        try:
            return self.getChildren( **kwargs )[0]            
        except:
            pass
                
    def ungroup( self, **kwargs ):
        return cmds.ungroup( self, **kwargs )

    '''
    def setScale( self, val, **kwargs ):
        """xform -scale"""
        kwargs['scale'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )
            
    def setRotation( self, val, **kwargs ):
        """xform -rotation"""
        kwargs['rotation'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )

    def setTranslation( self, val, **kwargs ):
        """xform -translation"""
        kwargs['translation'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )


    def setScalePivot( self, val, **kwargs ):
        """xform -scalePivot"""
        kwargs['scalePivot'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )
        
    def setRotatePivot( self, val, **kwargs ):
        """xform -rotatePivot"""
        kwargs['rotatePivot'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )
        
    def setPivots( self, val, **kwargs ):
        """xform -pivots"""
        kwargs['pivots'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )

    def setRotateAxis( self, val, **kwargs ):
        """xform -rotateAxis"""
        kwargs['rotateAxis'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )
        
                                
    def setShearing( self, val, **kwargs ):
        """xform -shear"""
        kwargs['shear'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )
                                
    def setMatrix( self, val, **kwargs ):
        """xform -scale"""
        if isinstance(val, pymel.core.core.Matrix):
            val = val.toList()
    
        kwargs['matrix'] = val
        kwargs.pop('q',None)
        kwargs.pop('query',None)
        cmds.xform( self, **kwargs )

    '''
    #getScale = pymel.util.factories.makeQueryFlagCmd( 'getScale', cmds.xform, 'scale', returnFunc=pymel.core.core.Vector )
    #getRotation = pymel.util.factories.makeQueryFlagCmd( 'getRotation', cmds.xform, 'rotation', returnFunc=pymel.core.core.Vector )    
    #getTranslation = pymel.util.factories.makeQueryFlagCmd( 'getTranslation', cmds.xform, 'translation', returnFunc=pymel.core.core.Vector )    
    #getScalePivot = pymel.util.factories.makeQueryFlagCmd( 'getScalePivot', cmds.xform, 'scalePivot', returnFunc=pymel.core.core.Vector )    
    #getRotatePivot = pymel.util.factories.makeQueryFlagCmd( 'getRotatePivot', cmds.xform, 'rotatePivot', returnFunc=pymel.core.core.Vector )    
    ##getPivots = pymel.util.factories.makeQueryFlagCmd( 'getPivots', cmds.xform, 'pivots', returnFunc=pymel.core.core.Vector )    
    #getRotateAxis = pymel.util.factories.makeQueryFlagCmd( 'getRotateAxis', cmds.xform, 'rotateAxis', returnFunc=pymel.core.core.Vector )    
    getShear = pymel.util.factories.makeQueryFlagCmd( 'getShear', cmds.xform, 'shear', returnFunc=pymel.core.core.Vector )    
    getMatrix = pymel.util.factories.makeQueryFlagCmd( 'getMatrix', cmds.xform, 'matrix', returnFunc=pymel.core.core.Matrix )    
    '''
    def getScale( self, **kwargs ):
        """xform -scale"""
        kwargs['scale'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
        
    def getRotation( self, **kwargs ):
        """xform -rotation"""
        kwargs['rotation'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )

    def getTranslation( self, **kwargs ):
        """xform -translation"""
        kwargs['translation'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )

    def getScalePivot( self, **kwargs ):
        """xform -scalePivot"""
        kwargs['scalePivot'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
        
    def getRotatePivot( self, **kwargs ):
        """xform -rotatePivot"""
        kwargs['rotatePivot'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
    '''    
    def getPivots( self, **kwargs ):
        """xform -pivots"""
        kwargs['pivots'] = True
        kwargs['query'] = True
        res = cmds.xform( self, **kwargs )
        return ( pymel.core.core.Vector( res[:3] ), pymel.core.core.Vector( res[3:] )  )
    '''
    def getRotateAxis( self, **kwargs ):
        """xform -rotateAxis"""
        kwargs['rotateAxis'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
        
                                
    def getShear( self, **kwargs ):
        """xform -shear"""
        kwargs['shear'] = True
        kwargs['query'] = True
        return pymel.core.core.Vector( cmds.xform( self, **kwargs ) )
                                
    def getMatrix( self, **kwargs ):
        """xform -matrix"""
    
        kwargs['matrix'] = True
        kwargs['query'] = True
        return pymel.core.core.Matrix( cmds.xform( self, **kwargs ) )
    '''        
    def getBoundingBox(self, invisible=False):
        """xform -boundingBox and xform-boundingBoxInvisible
        
        returns a tuple with two MVecs: ( bbmin, bbmax )
        """
        kwargs = {'query' : True }    
        if invisible:
            kwargs['boundingBoxInvisible'] = True
        else:
            kwargs['boundingBox'] = True
                    
        res = cmds.xform( self, **kwargs )
        return ( pymel.core.core.Vector(res[:3]), pymel.core.core.Vector(res[3:]) )
    
    def getBoundingBoxMin(self, invisible=False):
        return self.getBoundingBox(invisible)[0]
        
    def getBoundingBoxMax(self, invisible=False):
        return self.getBoundingBox(invisible)[1]    
    
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
    __metaclass__ = metaNode
    connect = pymel.util.factories.functionFactory('connectJoint', None, cmds)
    disconnect = pymel.util.factories.functionFactory('disconnectJoint', None, cmds)
    insert = pymel.util.factories.functionFactory('insertJoint', None, cmds)

class FluidEmitter(Transform):
    __metaclass__ = metaNode
    fluidVoxelInfo = pymel.util.factories.functionFactory('fluidVoxelInfo', None, cmds)
    loadFluid = pymel.util.factories.functionFactory('loadFluid', None, cmds)
    resampleFluid = pymel.util.factories.functionFactory('resampleFluid', None, cmds)
    saveFluid = pymel.util.factories.functionFactory('saveFluid', None, cmds)
    setFluidAttr = pymel.util.factories.functionFactory('setFluidAttr', None, cmds)
    getFluidAttr = pymel.util.factories.functionFactory('getFluidAttr', None, cmds)
    
class RenderLayer(DependNode):
    __metaclass__ = metaNode
    editAdjustment = pymel.util.factories.functionFactory('editRenderLayerAdjustment', None, cmds)
    editGlobals = pymel.util.factories.functionFactory('editRenderLayerGlobals', None, cmds)
    editMembers = pymel.util.factories.functionFactory('editRenderLayerMembers',None, cmds)
    postProcess = pymel.util.factories.functionFactory('renderLayerPostProcess',None,cmds)

class DisplayLayer(DependNode):
    __metaclass__ = metaNode
    editGlobals = pymel.util.factories.functionFactory('editDisplayLayerGlobals', None, cmds)
    editMembers = pymel.util.factories.functionFactory('editDisplayLeyerMembers', None, cmds)
    
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
class SurfaceShape(ControlPoint): pass
class Mesh(SurfaceShape):
    __metaclass__ = metaNode
    """
    Cycle through faces and select those that point up in world space
    
    >>> s = PyNode('pSphere1')
    >>> for face in s.faces:
    >>>     if face.normal.objectToWorld(s).y > 0:
    >>>         print face
    >>>         select( face , add=1)
    
    """
    class FaceArray(ComponentArray):
        def __init__(self, name):
            ComponentArray.__init__(self, name)
            self.returnClass = Mesh.Face
            
        def __len__(self):
            return cmds.polyEvaluate(self.node(), face=True)
    
    class EdgeArray(ComponentArray):
        def __init__(self, name):
            ComponentArray.__init__(self, name)
            self.returnClass = Mesh.Edge
        def __len__(self):
            return cmds.polyEvaluate(self.node(), edge=True)
    
    class VertexArray(ComponentArray):
        def __init__(self, name):
            ComponentArray.__init__(self, name)
            self.returnClass = Mesh.Vertex
            
        def __len__(self):
            return cmds.polyEvaluate(self.node(), vertex=True)
        
    class Face(Component):
        def __str__(self):
            return '%s.f[%s]' % (self._node, self._item)
    
        def getNormal(self):
            return pymel.core.core.Vector( map( float, cmds.polyInfo( self._node, fn=1 )[self._item].split()[2:] ))        
        normal = property(getNormal)
        
        def toEdges(self):
            return map( self._node.e.__getitem__, cmds.polyInfo( str(self), faceToEdge=1)[0].split()[2:] )        
        edges = property(toEdges)
        
        def toVertices(self):
            return map( self._node.vtx.__getitem__, cmds.polyInfo( str(self), faceToVertex=1)[0].split()[2:] )        
        vertices = property(toVertices)
        
    class Edge(Component):
        def __str__(self):
            return '%s.e[%s]' % (self._node, self._item)
            
        def toFaces(self):
            return map( self._node.e.__getitem__, cmds.polyInfo( str(self), edgeToFace=1)[0].split()[2:] )        
        faces = property(toFaces)
        
    class Vertex(Component):
        def __str__(self):
            return '%s.vtx[%s]' % (self._node, self._item)
            
        def toEdges(self):
            return map( self._node.e.__getitem__, cmds.polyInfo( str(self), vertexToEdge=1)[0].split()[2:] )        
        edges = property(toEdges)
        
        def toFaces(self):
            return map( self._node.e.__getitem__, cmds.polyInfo( str(self), vertexToFace=1)[0].split()[2:] )        
        faces = property(toFaces)
    
    def _getFaceArray(self):
        return Mesh.FaceArray( self + '.f' )    
    f = property(_getFaceArray)
    faces = property(_getFaceArray)
    
    def _getEdgeArray(self):
        return Mesh.EdgeArray( self + '.e' )    
    e = property(_getEdgeArray)
    edges = property(_getEdgeArray)
    
    def _getVertexArray(self):
        return Mesh.VertexArray( self + '.vtx' )    
    vtx = property(_getVertexArray)
    verts = property(_getVertexArray)
            
    def __getattr__(self, attr):
        try :
            return super(PyNode, self).__getattr__(attr)
        except AttributeError :
            at = Attribute( '%s.%s' % (self, attr) )   
            # if the attribute does not exist on this node try the history
            if not at.exists():
                try:
                    childAttr = getattr( self.inMesh.inputs()[0], attr )
                
                    try:
                        if childAttr.exists():
                            return childAttr
                    except AttributeError:
                        return childAttr
                
                except IndexError:
                    pass
                """
                try:    
                    return getattr( self.inMesh.inputs()[0], attr)
                except IndexError:
                    raise AttributeError, "Attribute does not exist: %s" % at
                """
            return at

    def __setattr__(self, attr, val):
        try :
            return super(PyNode, self).__setattr__(attr, val)
        except AttributeError :
            at = Attribute( '%s.%s' % (self, attr) )   
            # if the attribute does not exist on this node try the history
            if not at.exists():
                try:
                    childAttr = getattr( self.inMesh.inputs()[0], attr )
                
                    try:
                        if childAttr.exists():
                            return childAttr.set(val)
                    except AttributeError:
                        return childAttr.set(val)
                
                except IndexError:
                    pass
                """
                try:    
                    return getattr( self.inMesh.inputs()[0], attr)
                except IndexError:
                    raise AttributeError, "Attribute does not exist: %s" % at
                """
            return at.set(val)
                        
    vertexCount = pymel.util.factories.makeCreateFlagCmd( 'vertexCount', cmds.polyEvaluate, 'vertex' )
    edgeCount = pymel.util.factories.makeCreateFlagCmd( 'edgeCount', cmds.polyEvaluate, 'edge' )
    faceCount = pymel.util.factories.makeCreateFlagCmd( 'faceCount', cmds.polyEvaluate, 'face' )
    uvcoordCount = pymel.util.factories.makeCreateFlagCmd( 'uvcoordCount', cmds.polyEvaluate, 'uvcoord' )
    triangleCount = pymel.util.factories.makeCreateFlagCmd( 'triangleCount', cmds.polyEvaluate, 'triangle' )
    #area = pymel.util.factories.makeCreateFlagCmd( 'area', cmds.polyEvaluate, 'area' )
    
    #def area(self):
    #    return cmds.polyEvaluate(self, area=True)
        
    #def worldArea(self):
    #    return cmds.polyEvaluate(self, worldArea=True)
    
    '''
    def _listComponent( self, compType, num ):
        for i in range(0, num):
             yield Attribute( '%s.vtx[%s]' % (self, i) )
    
    def verts(self):
        return self._listComponent( 'vtx', self.numVerts() )
    '''
                    

class Subdiv(SurfaceShape):
    __metaclass__ = metaNode
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
    __metaclass__ = metaNode
    
    class PointArray(ComponentArray):
        def __init__(self, name):
            ComponentArray.__init__(self, name)
            self.returnClass = Particle.Point

        def __len__(self):
            return cmds.particle(self.node(), q=1,count=1)        
        
    class Point(Component):
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
    
class ObjectSet(Entity):
    """
    this is currently a work in progress.  my goal is to create a class for doing set operations in maya that is
    compatiable with python's powerful built-in set class.  
    
    each operand has its own method equivalent. 
    
    these will return the results of the operation as python sets containing lists of pymel node classes::
    
        s&t     s.intersection(t)
        s|t        s.union(t)
        s^t        s.symmetric_difference(t)
        s-t        s.difference(t)
    
    the following will alter the contents of the maya set::
        
        s&=t     s.intersection_update(t)
        s|=t    s.update(t)
        s^=t    s.symmetric_difference_update(t)
        s-=t    s.difference_update(t)        
    
    create some sets
    
        >>> sphere = polySphere()
        >>> cube = polyCube()
        >>> s = sets( cube )
        >>> s.update( ls( type='camera') )
        >>> t = sets( sphere )
        >>> t.add( 'perspShape' )

        >>> print s|t  # union

        >>> u = sets( s&t ) # intersection
        >>> print u.elements(), s.elements()
        >>> if u < s: print "%s is a sub-set of %s" % (u, s)
        
    place a set inside another, take1
    
        >>> # like python's built-in set, the add command expects a single element
        >>> s.add( t )

    place a set inside another, take2
    
        >>> # like python's built-in set, the update command expects a set or a list
        >>> t.update([u])

        >>> # put the sets back where they were
        >>> s.remove(t)
        >>> t.remove(u)

    now put the **contents** of a set into another set
    
        >>> t.update(u)

    mixed operation between pymel.core.ObjectSet and built-in set
        
        >>> v = set(['polyCube3', 'pSphere3'])
        >>> print s.intersection(v)
        >>> print v.intersection(s)  # not supported yet
        >>> u.clear()

        >>> delete( s )
        >>> delete( t )
        >>> delete( u )
    """
            
    def _elements(self):
        """ used internally to get a list of elements without casting to node classes"""
        return sets( self, q=True)
    #-----------------------
    # Maya Methods
    #-----------------------
    def elements(self):
        return set( map( PyNode, self._elements() ) )

    def subtract(self, set2):
        return sets( self, subtract=set2 )
    
    def flatten(self):
        return sets( flatten=self )
    
    #-----------------------
    # Python ObjectSet Methods
    #-----------------------
    def __and__(self, s):
        return self.intersection(s)

    def __iand__(self, s):
        return self.intersection_update(s)
                    
    def __contains__(self, element):
        return element in self._elements()

    #def __eq__(self, s):
    #    return s == self._elements()

    #def __ne__(self, s):
    #    return s != self._elements()
            
    def __or__(self, s):
        return self.union(s)

    def __ior__(self, s):
        return self.update(s)
                                    
    def __len__(self, s):
        return len(self._elements())

    def __lt__(self, s):
        return self.issubset(s)

    def __gt__(self, s):
        return self.issuperset(s)
                    
    def __sub__(self, s):
        return self.difference(s)

    def __isub__(self, s):
        return self.difference_update(s)                        

    def __xor__(self, s):
        return self.symmetric_difference(s)
        
    def add(self, element):
        return sets( self, add=[element] )
    
    def clear(self):
        return sets( self, clear=True )
    
    def copy(self ):
        return sets( self, copy=True )
    
    def difference(self, elements):
        if isinstance(elements,basestring):
            elements = cmds.sets( elements, q=True)
        return list(set(self.elements()).difference(elements))
        
        '''
        if isinstance(s, ObjectSet) or isinstance(s, str):
            return sets( s, subtract=self )
        
        s = sets( s )
        res = sets( s, subtract=self )
        cmds.delete(s)
        return res'''
    
    def difference_update(self, elements ):
        return sets( self, remove=elements)
    
    def discard( self, element ):
        try:
            return self.remove(element)
        except TypeError:
            pass

    def intersection(self, elements):
        if isinstance(elements,basestring):
            elements = cmds.sets( elements, q=True)
        return set(self.elements()).intersection(elements)
    
    def intersection_update(self, elements):
        self.clear()
        sets( self, add=self.intersections(elements) )
            
    def issubset(self, set2):
        return sets( self, isMember=set2)

    def issuperset(self, set2):
        return sets( self, isMember=set2)
            
    def remove( self, element ):
        return sets( self, remove=[element])

    def symmetric_difference(self, elements):
        if isinstance(elements,basestring):
            elements = cmds.sets( elements, q=True)
        return set(self.elements()).symmetric_difference(elements)
            
    def union( self, elements ):
        if isinstance(elements,basestring):
            elements = cmds.sets( elements, q=True)
        return set(self.elements()).union(elements)
    
    def update( self, set2 ):        
        sets( self, forceElement=set2 )
        
        #if isinstance(s, str):
        #    items = ObjectSet(  )
            
        #items = self.union(items)

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createClasses():
    #for cmds.nodeType in networkx.search.dfs_preorder( pymel.util.factories.nodeHierarchy , 'dependNode' )[1:]:
    #print pymel.util.factories.nodeHierarchy
    # see if breadth first isn't more practical ?
    for treeElem in pymel.util.factories.nodeHierarchy.preorder():
        #print "treeElem: ", treeElem
        cmds.nodeType = treeElem.key
        #print "cmds.nodeType: ", cmds.nodeType
        if cmds.nodeType == 'dependNode': continue
        classname = pymel.util.capitalize(cmds.nodeType)
        if not hasattr( _thisModule, classname ):
            #superNodeType = pymel.util.factories.nodeHierarchy.parent( cmds.nodeType )
            superNodeType = treeElem.parent.key
            #print "superNodeType: ", superNodeType, type(superNodeType)
            if superNodeType is None:
                print "could not find parent node", cmds.nodeType
                continue
            try:
                base = getattr( _thisModule, pymel.util.capitalize(superNodeType) )
            except AttributeError:
                print "could not find parent class", cmds.nodeType
                continue
        
            try:
                cls = metaNode(classname, (base,), {})
            except TypeError, msg:
                #print "%s(%s): %s" % (classname, superNodeType, msg )
                pass
            else:    
                cls.__module__ = __name__
                setattr( _thisModule, classname, cls )
        #else:
        #    print "already created", classname
_createClasses()


def testNodeCmds(verbose=False):

    emptyFunctions = []
    
    for funcName in pymel.util.factories.moduleCmds['node']:
        print funcName.center( 50, '=')
        
        if funcName in [ 'character', 'lattice', 'boneLattice', 'sculpt', 'wire' ]:
            print "skipping"
            continue
        
        
        
        try:
            func = getattr(_thisModule, funcName)
        except AttributeError:
            continue
            
        try:
            cmds.select(cl=1)
            
            if funcName.endswith( 'onstraint'):
                s = cmds.polySphere()[0]
                c = cmds.polyCube()[0]
                obj = func(s,c)
            else:
                obj = func()
                if obj is None:
                    emptyFunctions.append( funcName )
                    raise ValueError, "Returned object is None"
            
        except (TypeError,RuntimeError, ValueError), msg:
            print "ERROR: failed creation:", msg

        else:
            #(func, args, data) = cmdList[funcName]    
            #(usePyNode, baseClsName, nodeName)
            args = pymel.util.factories.cmdlist[funcName]['flags']

            if isinstance(obj, list):
                print "returns list"
                obj = obj[-1]

            for flag, flagInfo in args.items():            
                if flag in ['query', 'edit']:
                    continue
                modes = flagInfo['modes']
            
                # QUERY
                val = None
                if 'query' in modes:
                    cmd = "%s('%s', query=True, %s=True)" % (func.__name__, obj,  flag)
                    try:
                        val = func( obj, **{'query':True, flag:True} )
                        #print val
                        if verbose:
                            print cmd
                            print "\tsucceeded: %s" % val
                    except TypeError, msg:                            
                        if str(msg).startswith( 'Invalid flag' ):
                            pymel.util.factories.cmdlist[funcName]['flags'].pop(flag,None)
                        #else:
                        print cmd
                        print "\t", msg
                        val = None
                    except RuntimeError, msg:
                        print cmd
                        print "\t", msg    
                        val = None
                        
                # EDIT
                if 'edit' in modes:
                    try:    
                        if val is None:
                            argMap = { 
                                'boolean'         : True,
                                'int'            : 0,
                                'float'            : 0.0,
                                'linear'        : 0.0,
                                'double'        : 0.0,
                                'angle'            : 0,
                                'string' :        'persp'
                            }
                            
                            argtype = flagInfo['argtype']
                            if '[' in argtype:
                                val = []
                                for typ in argtype.strip('[]').split(','):
                                    val.append( argMap[typ.strip()] )
                            else:
                                val = argMap[argtype]    
                                                
                        cmd =  "%s('%s', edit=True, %s=%s)" % (func.__name__, obj,  flag, val)
                        val = func( obj, **{'edit':True, flag:val} )
                        if verbose:
                            print cmd
                            print "\tsucceeded: %s" % val
                        #print "SKIPPING %s: need arg of type %s" % (flag, flagInfo['argtype'])
                    except TypeError, msg:                                                        
                        if str(msg).startswith( 'Invalid flag' ):
                            pymel.util.factories.cmdlist[funcName]['flags'].pop(flag,None)
                        #else:
                        print cmd
                        print "\t", msg 
                    except RuntimeError, msg:
                        print cmd
                        print "\t", msg    
                    except KeyError:
                        print "UNKNOWN ARG:", flagInfo['argtype']    
    
    print "done"
    print emptyFunctions

def _createFunctions():
    for funcName in pymel.util.factories.moduleCmds['node']:
        func = pymel.util.factories.functionFactory( funcName, PyNode, _thisModule )
        
        if func:
            try:
                func.__doc__ = 'function counterpart of class `%s`\n\n' % pymel.util.capitalize( funcName ) + func.__doc__
                func.__module__ = __name__
                setattr( _thisModule, funcName, func )
            except:
                print "could not add %s to module %s" % (func, _thisModule)

_createFunctions()
#pymel.util.factories.createFunctions( _thisModule, PyNode )

# create PyNode conversion tables

# Need to build a similar dict of Pymel types to their corresponding API types
class PyNodeToMayaAPITypes(dict) :
    __metaclass__ =  pymel.util.metaStatic

# inverse lookup, some Maya API types won't have a PyNode equivalent
class MayaAPITypesToPyNode(dict) :
    __metaclass__ =  pymel.util.metaStatic

# build a PyNode to API type relation or PyNode to Maya node types relation ?
def buildPyNodeToAPI () :
    # Check if a pymel class is DependNode or a subclass of DependNode
    def _PyNodeClass (x) :
        try :
            return issubclass(x, PyNode)
        except :
            return False    
    listPyNodes = dict(inspect.getmembers(_thisModule, _PyNodeClass))
    print listPyNodes
    PyNodeDict = {}
    PyNodeInverseDict = {}
    for k in listPyNodes.keys() :
        # assume that PyNode type name is the API type without the leading 'k'
        PyNodeType = listPyNodes[k]
        PyNodeTypeName = PyNodeType.__name__
        APITypeName = 'k'+PyNodeTypeName
        if pymel.util.api.MayaAPIToTypes().has_key(APITypeName) :
            PyNodeDict[PyNodeType] = APITypeName
            PyNodeInverseDict[APITypeName] = PyNodeType
    # Would be good to limit special treatments
    PyNodeDict[PyNode] = 'kBase'
    PyNodeInverseDict['kBase'] = PyNode
    PyNodeDict[DependNode] = 'kDependencyNode'
    PyNodeInverseDict['kDependencyNode'] = DependNode
                          
    # Initialize the static classes to hold these
    PyNodeToMayaAPITypes (PyNodeDict)
    MayaAPITypesToPyNode (PyNodeInverseDict)

# Initialize Pymel classes to API types lookup
#buildPyNodeToAPI()
start = time.time()
buildPyNodeToAPI()
elapsed = time.time() - start
print "Initialized Pymel PyNodes types list in %.2f sec" % elapsed

# PyNode types names (as str)
class PyNodeTypeNames(dict) :
    """ Lookup from PyNode type name to PyNode type """
    __metaclass__ =  pymel.util.metaStatic

# Dictionnary of Maya API types to their MFn::Types enum
PyNodeTypeNames((k.__name__, k) for k in PyNodeToMayaAPITypes().keys())  

# child:parent lookup of the pymel classes that derive from DependNode
class PyNodeTypesHierarchy(dict) :
    __metaclass__ =  pymel.util.metaStatic

# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def buildPyNodeTypesHierarchy () :    
    PyNodeTree = inspect.getclasstree([k for k in PyNodeToMayaAPITypes().keys()])
    PyNodeDict = {}
    for x in pymel.util.expandArgs(PyNodeTree, type='list') :
        try :
            ct = x[0]
            pt = x[1][0]
            if issubclass(ct, PyNode) and issubclass(pt, PyNode) :
                PyNodeDict[ct] = pt
        except :
            pass

    return PyNodeDict 

# Initialize the Pymel class tree
# PyNodeTypesHierarchy(buildPyNodeTypesHierarchy())
start = time.time()
#PyNodeTypesHierarchy(buildPyNodeTypesHierarchy())
elapsed = time.time() - start
print "Initialized Pymel PyNode classes hierarchy tree in %.2f sec" % elapsed



def isValidPyNodeType (arg):
    return PyNodeToMayaAPITypes().has_key(arg)

def isValidPyNodeTypeName (arg):
    return PyNodeTypeNames().has_key(arg)

# Selection list to PyNodes
def MSelectionPyNode ( sel ):
    length = sel.length()
    dag = pymel.util.api.MDagPath()
    comp = pymel.util.api.MObject()
    obj = pymel.util.api.MObject()
    result = []
    for i in xrange(length) :
        selStrs = []
        sel.getSelectionStrings ( i, selStrs )    
        print "Working on selection %i:'%s'" % (i, ', '.join(selStrs))
        try :
            sel.getDagPath(i, dag, comp)
            pynode = PyNode( dag, comp )
            result.append(pynode)
        except :
            try :
                sel.getDependNode(i, obj)
                pynode = PyNode( obj )
                result.append(pynode)                
            except :
                warnings.warn("Unable to recover selection %i:'%s'" % (i, ', '.join(selStrs)) )             
    return result      
        
        
def activeSelectionPyNode () :
    sel = pymel.util.api.MSelectionList()
    pymel.util.api.MGlobal.getActiveSelectionList ( sel )   
    return MSelectionPyNode ( sel )
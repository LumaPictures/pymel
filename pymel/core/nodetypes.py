"""
Contains classes corresponding to the Maya type hierarchy, including `DependNode`, `Transform`, `Mesh`, and `Camera`.
"""
import sys, os, re
import inspect, itertools, math

import pymel.util as _util
import pymel.internal.pmcmds as cmds #@UnresolvedImport
import pymel.internal.factories as _factories
import pymel.api as _api #@UnresolvedImport
import pymel.internal.apicache as _apicache
import pymel.internal.pwarnings as _warnings
from pymel.internal import getLogger as _getLogger
import datatypes
_logger = _getLogger(__name__)

# to make sure Maya is up
import pymel.internal as internal
import pymel.versions as versions

from maya.cmds import about as _about
import maya.mel as mm

#from general import *
import general
import other
from animation import listAnimatable as _listAnimatable
from system import namespaceInfo as _namespaceInfo, FileReference as _FileReference

_thisModule = sys.modules[__name__]

#__all__ = ['Component', 'MeshEdge', 'MeshVertex', 'MeshFace', 'Attribute', 'DependNode' ]

## Mesh Components

# If we're reloading, clear the pynode types out
_factories.clearPyNodeTypes()

class DependNode( general.PyNode ):
    __apicls__ = _api.MFnDependencyNode
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
#            # Result: nt.Transform(u'persp1')
#        """
#        if create:
#            ntype = cls.__melnode__
#            name = createNode(ntype,n=name,ss=1)
#        return general.PyNode.__new__(cls,name)

#    def __init__(self, *args, **kwargs ):
#        self.apicls.__init__(self, self._apiobject.object() )

    @_util.universalmethod
    def __melobject__(self):
        """Special method for returning a mel-friendly representation."""
        if isinstance(self, DependNode):
            # For instance, return the node's name...
            return self.name()
        else:
            # For the class itself, return the mel node name
            return self.__melnode__

    def __repr__(self):
        """
        :rtype: `unicode`
        """
        return u"nt.%s(%r)" % (self.__class__.__name__, self.name())

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

    def shortName(self):
        """
        This produces the same results as `DependNode.name` and is included to simplify looping over lists
        of nodes that include both Dag and Depend nodes.

        :rtype: `unicode`
        """
        return self.name()

    def longName(self):
        """
        This produces the same results as `DependNode.name` and is included to simplify looping over lists
        of nodes that include both Dag and Depend nodes.

        :rtype: `unicode`
        """
        return self.name()

    def nodeName(self):
        """
        This produces the same results as `DependNode.name` and is included to simplify looping over lists
        of nodes that include both Dag and Depend nodes.

        :rtype: `unicode`
        """
        return self.name()

    #rename = rename
    def rename( self, name, **kwargs ):
        """
        :rtype: `DependNode`
        """
        #self.setName( name ) # no undo support
        
        #check for preserveNamespace a pymel unique flag
        if kwargs.pop('preserveNamespace', False):
            name = self.namespace(root=True) + name
        
        #ensure shortname
        if '|' in name:
            name = name.split('|')[-1]
        
        return general.rename(self, name, **kwargs)

    def __apiobject__(self) :
        "get the default API object (MObject) for this node if it is valid"
        return self.__apimobject__()

    def __apimobject__(self) :
        "get the MObject for this node if it is valid"
        handle = self.__apihandle__()
        if _api.isValidMObjectHandle( handle ) :
            return handle.object()
        raise general.MayaNodeError( self._name )

    def __apihandle__(self) :
        return self.__apiobjects__['MObjectHandle']


    def __str__(self):
        return "%s" % self.name()

    def __unicode__(self):
        return u"%s" % self.name()

    if versions.current() >= versions.v2009:
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

    isReadOnly = _factories.wrapApiMethod( _api.MFnDependencyNode, 'isFromReferencedFile', 'isReadOnly' )

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

        :rtype: `PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return general.listConnections(self, **kwargs)

    def outputs(self, **kwargs):
        """listConnections -source 0 -destination 1

        :rtype: `PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )

        return general.listConnections(self, **kwargs)

    def sources(self, **kwargs):
        """listConnections -source 1 -destination 0

        :rtype: `PyNode` list
        """
        kwargs['source'] = True
        kwargs.pop('s', None )
        kwargs['destination'] = False
        kwargs.pop('d', None )
        return general.listConnections(self, **kwargs)

    def destinations(self, **kwargs):
        """listConnections -source 0 -destination 1

        :rtype: `PyNode` list
        """
        kwargs['source'] = False
        kwargs.pop('s', None )
        kwargs['destination'] = True
        kwargs.pop('d', None )

        return general.listConnections(self, **kwargs)

    def shadingGroups(self):
        """list any shading groups in the future of this object - works for
        shading nodes, transforms, and shapes
        
        Also see listSets(type=1) - which returns which 'rendering sets' the
        object is a member of (and 'rendering sets' seem to consist only of
        shading groups), whereas this method searches the object's future for
        any nodes of type 'shadingEngine'.   
        
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

    @_util.universalmethod
    def attrDefaults(obj,attr):
        """
        Access to an attribute of a node.  This does not require an instance:

            >>> nt.Transform.attrDefaults('tx').isKeyable()
            True

        but it can use one if needed ( for example, for dynamically created attributes )

            >>> nt.Transform(u'persp').attrDefaults('tx').isKeyable()

        Note: this is still experimental.
        """
        if inspect.isclass(obj):
            self = None
            cls = obj # keep things familiar
        else:
            self = obj # keep things familiar
            cls = type(obj)
        
        attributes = cls.__apiobjects__.setdefault('MFnAttributes', {})
        attrObj = attributes.get(attr, None)
        if not _api.isValidMObject(attrObj):
            if self is None:
                # We don't have an instance of the node, we need
                # to make a ghost one...
                dagMod = _api.MDagModifier()
                dgMod = _api.MDGModifier()
                nodeObj = _apicache._makeDgModGhostObject( cls.__melnode__,
                                                           dagMod,
                                                           dgMod )
                nodeMfn = cls.__apicls__(obj)
            else:
                nodeMfn = self.__apimfn__()
            attrObj = nodeMfn.attribute(attr)
            attributes[attr] = attrObj
        return general.AttributeDefaults( attrObj )

    def attr(self, attr):
        """
        access to attribute plug of a node. returns an instance of the Attribute class for the
        given attribute name.

        :rtype: `Attribute`
        """
        return self._attr(attr, False)
        
    # Just have this alias because it will sometimes return attributes for an
    # underlying shape, which we may want for DagNode.attr, but don't want for
    # DependNode.attr (and using the on-shape result, instead of throwing it
    # away and then finding it again on the shape, saves time for the DagNode
    # case)
    def _attr(self, attr, allowOtherNode):
        #return Attribute( '%s.%s' % (self, attr) )
        try :
            if '.' in attr or '[' in attr:
                # Compound or Multi Attribute
                # there are a couple of different ways we can proceed:
                # Option 1: back out to _api.toApiObject (via general.PyNode)
                # return Attribute( self.__apiobject__(), self.name() + '.' + attr )

                # Option 2: nameparse.
                # this avoids calling self.name(), which can be slow
                import pymel.util.nameparse as nameparse
                nameTokens = nameparse.getBasicPartList( 'dummy.' + attr )
                result = self.__apiobject__()
                for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
                    if isinstance( token, nameparse.MayaName ):
                        if isinstance( result, _api.MPlug ):
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
#                                        try: result = _api.MFnDagNode( fn.child(i) ).findPlug( unicode(token) )
#                                        except TypeError: pass
#                                        else:break
                    if isinstance( token, nameparse.NameIndex ):
                        if token.value != -1:
                            result = result.elementByLogicalIndex( token.value )
                plug = result
            else:
                try:
                    plug = self.__apimfn__().findPlug( attr, False )
                except RuntimeError:
                    # Don't use .findAlias, as it always returns the 'base'
                    # attribute - ie, if the alias is to foo[0].bar, it will
                    # just point to foo
                    # aliases
                    #obj = _api.MObject()
                    #self.__apimfn__().findAlias( attr, obj )
                    #plug = self.__apimfn__().findPlug( obj, False )
                    
                    # the following technique gets aliased attributes as well. turning dagPlugs to off saves time because we already
                    # know the dagNode. however, certain attributes, such as rotatePivot, are detected as components,
                    # despite the fact that findPlug finds them as MPlugs. need to look into this
                    # TODO: test speed versus above method
                    try:
                        plug = _api.toApiObject(self.name() + '.' + attr, dagPlugs=False)
                    except RuntimeError:
                        raise
                    if not isinstance(plug, _api.MPlug):
                        raise RuntimeError
                    
                if not (allowOtherNode or plug.node() == self.__apimobject__()):
                    # we could have gotten an attribute on a shape object,
                    # which we don't want
                    raise RuntimeError
            return general.Attribute( self.__apiobject__(), plug )

        except RuntimeError:
            # raise our own MayaAttributeError, which subclasses AttributeError and MayaObjectError
            raise general.MayaAttributeError( '%s.%s' % (self, attr) )

    hasAttr = general.hasAttr

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

    @_factories.addMelDocs('deleteAttr')
    def deleteAttr( self, attr, *args, **kwargs ):
        # for now, using strings is better, because there is no MPlug support
        return general.deleteAttr( "%s.%s" % (self, attr), *args,  **kwargs )

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
        """
        listAttr

        Modifications:
          - returns an empty list when the result is None
          - added 'alias' keyword to list attributes that have aliases
        :rtype: `Attribute` list

        """
        alias = kwargs.pop('alias', False)
        # stringify fix
        res = map( lambda x: self.attr(x), _util.listForNone(cmds.listAttr(self.name(), **kwargs)))
        if alias:
            res = [ x[1] for x in self.listAliases() if x[1] in res]

#            aliases = dict( (x[1], x[0]) for x in general.aliasAttr(self.name()) )
#            tmp = res
#            res = []
#            for at in tmp:
#                try:
#                    res.append( aliases[at], at )
#                except KeyError:
#                    pass
        return res

    def listAliases( self ):
        """
        aliasAttr

        Modifications:
          - returns an empty list when the result is None
          - when queried, returns a list of (alias, `Attribute`) pairs.

        :rtype: (`str`, `Attribute`) list

        """

        #tmp = _util.listForNone(cmds.aliasAttr(self.name(),query=True))
        tmp = []
        self.__apimfn__().getAliasList(tmp)
        res = []
        for i in range(0,len(tmp),2):
            res.append((tmp[i], general.Attribute(self.node() + '.' + tmp[i+1])))
        return res


    def attrInfo( self, **kwargs):
        """attributeInfo

        :rtype: `Attribute` list
        """
        # stringify fix
        return map( lambda x: self.attr(x) , _util.listForNone(cmds.attributeInfo(self.name(), **kwargs)))


#}
#-----------------------------------------
#xxx{ Name Info and Manipulation
#-----------------------------------------

# Now just wraps NameParser functions

    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged.

        >>> from pymel.core import *
        >>> SCENE.lambert1.stripNum()
        u'lambert'

        :rtype: `unicode`
        """
        return other.NameParser(self).stripNum()

    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised.

        >>> from pymel.core import *
        >>> SCENE.lambert1.extractNum()
        u'1'

        :rtype: `unicode`
        """
        return other.NameParser(self).extractNum()

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found

        If there is no trailing number, appends '1' to the name.

        :rtype: `unicode`
        """
        return other.NameParser(self).nextUniqueName()

    def nextName(self):
        """Increment the trailing number of the object by 1

        Raises an error if the name has no trailing number.

        >>> from pymel.core import *
        >>> SCENE.lambert1.nextName()
        DependNodeName(u'lambert2')

        :rtype: `unicode`
        """
        return other.NameParser(self).nextName()

    def prevName(self):
        """Decrement the trailing number of the object by 1

        Raises an error if the name has no trailing number.

        :rtype: `unicode`
        """
        return other.NameParser(self).prevName()

    @classmethod
    def registerVirtualSubClass( cls, nameRequired=False ):
        """
        Deprecated
        """
        _factories.registerVirtualClass(cls, nameRequired)

#}

if versions.current() >= versions.v2011:
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

    __apicls__ = _api.MFnDagNode
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
                return compClass[0](self, {compClass[1]:general.ComponentIndex(label=compClass[1])})
            else:
                return compClass(self)
        # if we do self.getShape(), and this is a shape node, we will
        # enter a recursive loop if compName isn't actually a comp:
        # since shape doesn't have 'getShape', it will call __getattr__
        # for 'getShape', which in turn call comp to check if it's a comp,
        # which will call __getattr__, etc
        # ..soo... check if we have a 'getShape'!
        # ...also, don't use 'hasattr', as this will also call __getattr__!
        try:
            object.__getattribute__(self, 'getShape')
        except AttributeError:
            raise general.MayaComponentError( '%s.%s' % (self, compName) )
        else:
            shape = self.getShape()
            if shape:
                return shape.comp(compName)


    def _updateName(self, long=False) :
        #if _api.isValidMObjectHandle(self._apiobject) :
            #obj = self._apiobject.object()
            #dagFn = _api.MFnDagNode(obj)
            #dagPath = _api.MDagPath()
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

    def longName(self,stripNamespace=False,levels=0):
        """
        The full dag path to the object, including leading pipe ( | )

        :rtype: `unicode`
        """
        if stripNamespace:
            name = self.name(long=True)
            nodes = []
            for x in name.split('|'):
                y = x.split('.')
                z = y[0].split(':')
                if levels:
                    y[0] = ':'.join( z[min(len(z)-1,levels):] )

                else:
                    y[0] = z[-1]
                nodes.append( '.'.join( y ) )
            stripped_name = '|'.join( nodes)
            return stripped_name

        return self.name(long=True)
    fullPath = longName

    def shortName( self ):
        """
        The shortest unique name.

        :rtype: `unicode`
        """
        return self.name(long=False)

    def nodeName( self, stripNamespace=False ):
        """
        Just the name of the node, without any dag path

        :rtype: `unicode`
        """
        name = self.name().rsplit('|', 1)[-1]
        if stripNamespace:
            name = name.rsplit(':', 1)[-1]
        return name


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

            #assert argObj.hasFn( _api.MFn.kDagNode )
            dag = _api.MDagPath()
            # we can't use self.__apimfn__() becaue the mfn is instantiated from an MDagPath
            # which we are in the process of finding out
            mfn = _api.MFnDagNode( self.__apimobject__() )
            mfn.getPath(dag)
            self.__apiobjects__['MDagPath'] = dag
            return dag
#            if dag.isValid():
#                #argObj = dag
#                if dag.fullPathName():
#                    argObj = dag
#                else:
#                    print 'produced valid MDagPath with no name: %s(%s)' % ( argObj.apiTypeStr(), _api.MFnDependencyNode(argObj).name() )

    def __apihandle__(self) :
        try:
            handle = self.__apiobjects__['MObjectHandle']
        except:
            try:
                handle = _api.MObjectHandle( self.__apiobjects__['MDagPath'].node() )
            except RuntimeError:
                raise general.MayaNodeError( self._name )
            self.__apiobjects__['MObjectHandle'] = handle
        return handle

#    def __apimfn__(self):
#        if self._apimfn:
#            return self._apimfn
#        elif self.__apicls__:
#            obj = self._apiobject
#            if _api.isValidMDagPath(obj):
#                try:
#                    self._apimfn = self.__apicls__(obj)
#                    return self._apimfn
#                except KeyError:
#                    pass

#    def __init__(self, *args, **kwargs):
#        if self._apiobject:
#            if isinstance(self._apiobject, _api.MObjectHandle):
#                dagPath = _api.MDagPath()
#                _api.MDagPath.getAPathTo( self._apiobject.object(), dagPath )
#                self._apiobject = dagPath
#
#            assert _api.isValidMDagPath( self._apiobject )


#    def __init__(self, *args, **kwargs) :
#        if args :
#            arg = args[0]
#            if len(args) > 1 :
#                comp = args[1]
#            if isinstance(arg, DagNode) :
#                self._name = unicode(arg.name())
#                self._apiobject = _api.MObjectHandle(arg.object())
#            elif _api.isValidMObject(arg) or _api.isValidMObjectHandle(arg) :
#                objHandle = _api.MObjectHandle(arg)
#                obj = objHandle.object()
#                if _api.isValidMDagNode(obj) :
#                    self._apiobject = objHandle
#                    self._updateName()
#                else :
#                    raise TypeError, "%r might be a dependencyNode, but not a dagNode" % arg
#            elif isinstance(arg, basestring) :
#                obj = _api.toMObject (arg)
#                if obj :
#                    # creation for existing object
#                    if _api.isValidMDagNode (obj):
#                        self._apiobject = _api.MObjectHandle(obj)
#                        self._updateName()
#                    else :
#                        raise TypeError, "%r might be a dependencyNode, but not a dagNode" % arg
#                else :
#                    # creation for inexistent object
#                    self._name = arg
#            else :
#                raise TypeError, "don't know how to make a DagNode out of a %s : %r" % (type(arg), arg)



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
#            obj = _api.toMObject(parent)
#            if obj:
#               return self.__apimfn__().hasParent( obj )
#
#    def hasChild(self, child ):
#        try:
#            return self.__apimfn__().hasChild( child.__apiobject__() )
#        except AttributeError:
#            obj = _api.toMObject(child)
#            if obj:
#               return self.__apimfn__().hasChild( obj )
#
#    def isParentOf( self, parent ):
#        try:
#            return self.__apimfn__().isParentOf( parent.__apiobject__() )
#        except AttributeError:
#            obj = _api.toMObject(parent)
#            if obj:
#               return self.__apimfn__().isParentOf( obj )
#
#    def isChildOf( self, child ):
#        try:
#            return self.__apimfn__().isChildOf( child.__apiobject__() )
#        except AttributeError:
#            obj = _api.toMObject(child)
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

        >>> from pymel.core import *
        >>> f=newFile(f=1) #start clean
        >>>
        >>> s = polyPlane()[0]
        >>> instance(s)
        [nt.Transform(u'pPlane2')]
        >>> instance(s)
        [nt.Transform(u'pPlane3')]
        >>> s.getShape().getInstances()
        [nt.Mesh(u'pPlane1|pPlaneShape1'), nt.Mesh(u'pPlane2|pPlaneShape1'), nt.Mesh(u'pPlane3|pPlaneShape1')]
        >>> s.getShape().getInstances(includeSelf=False)
        [nt.Mesh(u'pPlane2|pPlaneShape1'), nt.Mesh(u'pPlane3|pPlaneShape1')]

        """
        d = _api.MDagPathArray()
        self.__apimfn__().getAllPaths(d)
        thisDagPath = self.__apimdagpath__()
        result = [ general.PyNode( _api.MDagPath(d[i])) for i in range(d.length()) if includeSelf or not d[i] == thisDagPath ]

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
#        parent = _api.MDagPath( self.__apiobject__() )
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
#            child = _api.MDagPath( thisDag )
#            child.push( thisDag.child(i) )
#            children.append( general.PyNode(child) )
#        return children

    def firstParent2(self, **kwargs):
        """unlike the firstParent command which determines the parent via string formatting, this
        command uses the listRelatives command
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

    @staticmethod
    def _getDagParent(dag):
        if dag.length() <= 1:
            return None
        # Need a copy as we'll be modifying it...
        dag = _api.MDagPath(dag)
        dag.pop()
        return dag

    def getParent(self, generations=1):
        """
        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> from pymel.core import *
                  >>> select(cl=1)
                  >>> bottom = group(n='bottom')
                  >>> group(n='almostThere')
                  nt.Transform(u'almostThere')
                  >>> group(n='nextLevel')
                  nt.Transform(u'nextLevel')
                  >>> group(n='topLevel')
                  nt.Transform(u'topLevel')
                  >>> bottom.longName()
                  u'|topLevel|nextLevel|almostThere|bottom'
                  >>> bottom.getParent(2)
                  nt.Transform(u'nextLevel')

              Negative values will traverse from the top:

                  >>> bottom.getParent(generations=-3)
                  nt.Transform(u'almostThere')

              A value of 0 will return the same node.
              The default value is 1.

              If generations is None, it will be interpreted as 'return all
              parents', and a list will be returned.
              
              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown).

        :rtype: `DagNode`
        """

        # Get the parent through the api - listRelatives doesn't handle instances correctly,
        # and string processing seems unreliable...

        res = general._getParent(self._getDagParent, self.__apimdagpath__(), generations)
        
        if generations is None:
            if res is None:
                return []
            return [general.PyNode(x) for x in res]
        elif res is not None:
            return general.PyNode( res )
        
    def getAllParents(self):
        """
        Return a list of all parents above this.

        Starts from the parent immediately above, going up.

        :rtype: `DagNode` list
        """
        return self.getParent(generations=None)

    def getChildren(self, **kwargs ):
        """
        see also `childAtIndex`

        for flags, see pymel.core.general.listRelatives

        :rtype: `DagNode` list
        """
        kwargs['children'] = True
        kwargs.pop('c',None)

        return general.listRelatives( self, **kwargs)

    def getSiblings(self, **kwargs ):
        """
        for flags, see pymel.core.general.listRelatives

        :rtype: `DagNode` list
        """
        #pass
        try:
            return [ x for x in self.getParent().getChildren(**kwargs) if x != self]
        except:
            return []

    def listRelatives(self, **kwargs ):
        """
        for flags, see pymel.core.general.listRelatives

        :rtype: `PyNode` list
        """
        return general.listRelatives( self, **kwargs)


    def setParent( self, *args, **kwargs ):
        """
        parent

        Modifications:
            if parent is 'None', world=True is automatically set
        """
        if args and args[-1] is None:
            if not kwargs.get('w', kwargs.get('world', True)):
                raise ValueError('No parent given, but parent to world explicitly set to False')
            if 'world' in kwargs:
                del kwargs['world']
            kwargs['w']=True
        elif 'world' in kwargs:
            # Standardize on 'w', for easier checking later
            kwargs['w'] = kwargs['world']
            del kwargs['world']

        # if you try to parent to the current parent, maya errors...
        # check for this and return if that's the case
        currentParent = self.getParent()
        if ( (currentParent is None and kwargs.get('w', False))
            or (args and currentParent == args[-1]) ):
            return self 
        
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

            >>> from pymel.core import *
            >>> s = polySphere(name='sphere')[0]
            >>> c = polyCube(name='cube')[0]
            >>> t = polyTorus(name='torus')[0]
            >>> s | c | t
            nt.Transform(u'torus')
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
    
    def hide(self):
        self.visibility.set(0)

    def show(self):
        self.visibility.set(1)
        
    def isVisible(self):
        if not self.attr('visibility').get():
            return False
        parent = self.getParent()
        if not parent:
            return True
        else:
            return parent.isVisible()

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
    
    def setParent(self, *args, **kwargs):
        if 'shape' not in kwargs and 's' not in kwargs:
            kwargs['s'] = True
        super(Shape, self).setParent(*args, **kwargs)
#class Joint(Transform):
#    pass


class Camera(Shape):
    __metaclass__ = _factories.MetaMayaNodeWrapper

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
    _componentAttributes = {'rotatePivot' : (general.Pivot, 'rotatePivot'),
                            'scalePivot'  : (general.Pivot, 'scalePivot')}
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
            for shape in self.getShapes():
                try:
                    return getattr(shape,attr)
                except AttributeError: pass
            raise e
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
            res = self._attr(attr, checkShape)
        except general.MayaAttributeError, e:
            if checkShape:
                try:
                    res = self.getShape().attr(attr)
                except AttributeError:
                    raise e
            raise e
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

    def getShape( self, **kwargs ):
        """
        :rtype: `DagNode`
        """
        kwargs['shapes'] = True
        try:
            return self.getChildren( **kwargs )[0]
        except IndexError:
            pass

    def getShapes( self, **kwargs ):
        """
        :rtype: `DagNode`
        """
        kwargs['shapes'] = True
        return self.getChildren( **kwargs )


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


    @_factories.addMelDocs('xform','rotateAxis')
    def setMatrix( self, val, **kwargs ):
        """xform -scale"""
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

    @_factories.addApiDocs( _api.MFnTransform, 'setTranslation' )
    def setTranslation(self, vector, space='object', **kwargs):
        if self._isRelativeArg(kwargs):
            return self.translateBy(vector, space, **kwargs)
        space = self._getSpaceArg(space, kwargs )
        return self._setTranslation(vector, space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'getTranslation' )
    def getTranslation(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getTranslation(space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'translateBy' )
    def translateBy(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        curr = self._getTranslation(space)
        self._translateBy(vector, space)
        new = self._getTranslation(space)
        undoItem = _factories.ApiUndoItem(Transform.setTranslation, (self, new, space), (self, curr, space) )
        _factories.apiUndo.append( undoItem )

    @_factories.addApiDocs( _api.MFnTransform, 'setScale' )
    def setScale(self, scale, **kwargs):
        if self._isRelativeArg(kwargs):
            return self.scaleBy(scale, **kwargs)
        return self._setScale(scale)

    @_factories.addApiDocs( _api.MFnTransform, 'scaleBy' )
    def scaleBy(self, scale, **kwargs):
        curr = self.getScale()
        self._scaleBy(scale)
        new = self.getScale()
        undoItem = _factories.ApiUndoItem(Transform.setScale, (self, new), (self, curr) )
        _factories.apiUndo.append( undoItem )

    @_factories.addApiDocs( _api.MFnTransform, 'setShear' )
    def setShear(self, shear, **kwargs):
        if self._isRelativeArg(kwargs):
            return self.shearBy(shear, **kwargs)
        return self._setShear(shear)

    @_factories.addApiDocs( _api.MFnTransform, 'shearBy' )
    def shearBy(self, shear, **kwargs):
        curr = self.getShear()
        self._shearBy(shear)
        new = self.getShear()
        undoItem = _factories.ApiUndoItem(Transform.setShear, (self, new), (self, curr) )
        _factories.apiUndo.append( undoItem )


#    @_factories.queryflag('xform','rotatePivot')
#    def getRotatePivotOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( _api.MFnTransform, 'setRotatePivot' )
    def setRotatePivot(self, point, space='object', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivot(point, space=space, balance=balance)

    @_factories.addApiDocs( _api.MFnTransform, 'rotatePivot' )
    def getRotatePivot(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivot(space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'setRotatePivotTranslation' )
    def setRotatePivotTranslation(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setRotatePivotTranslation(vector, space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'rotatePivotTranslation' )
    def getRotatePivotTranslation(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getRotatePivotTranslation(space=space)


#    @_factories.queryflag('xform','rotation')
#    def getRotationOld( self, **kwargs ):
#        return datatypes.Vector( cmds.xform( self, **kwargs ) )

    @_factories.addApiDocs( _api.MFnTransform, 'setRotation' )
    def setRotation(self, rotation, space='object', **kwargs):
        # quaternions are the only method that support a space parameter
        if self._isRelativeArg(kwargs):
            return self.rotateBy(rotation, space, **kwargs)
        space = self._getSpaceArg(space, kwargs )
        rotation = list(rotation)

        rotation = [ datatypes.Angle( x ).asRadians() for x in rotation ]

        quat = _api.MEulerRotation( *rotation ).asQuaternion()
        _api.MFnTransform(self.__apiobject__()).setRotation(quat, datatypes.Spaces.getIndex(space) )

#    @_factories.addApiDocs( _api.MFnTransform, 'getRotation' )
#    def getRotation(self, space='object', **kwargs):
#        # quaternions are the only method that support a space parameter
#        space = self._getSpaceArg(space, kwargs )
#        quat = _api.MQuaternion()
#        _api.MFnTransform(self.__apimfn__()).getRotation(quat, datatypes.Spaces.getIndex(space) )
#        return datatypes.EulerRotation( quat.asEulerRotation() )

    @_factories.addApiDocs( _api.MFnTransform, 'getRotation', overloadIndex=1 )
    def getRotation(self, space='object', quaternion=False, **kwargs):
        '''
    Modifications:
      - added 'quaternion' keyword arg, to specify whether the result
        be returned as a Quaternion object, as opposed to the default
        EulerRotation object
      - added 'space' keyword arg, which defaults to 'object'
        '''
        # quaternions are the only method that support a space parameter
        space = self._getSpaceArg(space, kwargs )
        if space.lower() in ('object', 'pretransform', 'transform') and not quaternion:
            # In this case, we can just go straight to the EulerRotation,
            # without having to go through Quaternion - this means we will
            # get information like angles > 360 degrees
            euler = _api.MEulerRotation()
            self.__apimfn__().getRotation(euler)
            rot = datatypes.EulerRotation(euler)
        else:
            rot = self._getRotation(space=space)
            if not quaternion:
                rot =  rot.asEulerRotation()
        if isinstance(rot, datatypes.EulerRotation):
            rot.setDisplayUnit( datatypes.Angle.getUIUnit() )
        return rot


    @_factories.addApiDocs( _api.MFnTransform, 'rotateBy' )
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

    @_factories.addApiDocs( _api.MFnTransform, 'setScalePivot' )
    def setScalePivot(self, point, space='object', balance=True, **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivot(point, space=space, balance=balance)

    @_factories.addApiDocs( _api.MFnTransform, 'scalePivot' )
    def getScalePivot(self, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._getScalePivot(space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'setScalePivotTranslation' )
    def setScalePivotTranslation(self, vector, space='object', **kwargs):
        space = self._getSpaceArg(space, kwargs )
        return self._setScalePivotTranslation(vector, space=space)

    @_factories.addApiDocs( _api.MFnTransform, 'scalePivotTranslation' )
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

    #TODO: create API equivalent of `xform -boundingBoxInvisible` so we can replace this with _api.
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

#    def centerPivots(self, **kwargs):
#        """xform -centerPivots"""
#        kwargs['centerPivots'] = True
#        cmds.xform( self, **kwargs )
#
#    def zeroTransformPivots(self, **kwargs):
#        """xform -zeroTransformPivots"""
#        kwargs['zeroTransformPivots'] = True
#        cmds.xform( self, **kwargs )


class Joint(Transform):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    connect = _factories.functionFactory( cmds.connectJoint, rename='connect')
    disconnect = _factories.functionFactory( cmds.disconnectJoint, rename='disconnect')
    insert = _factories.functionFactory( cmds.insertJoint, rename='insert')

if versions.isUnlimited():
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
            return map( general.PyNode, _util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=True) ) )
        else:
            return _util.listForNone( cmds.editRenderLayerMembers( self, q=1, fullNames=False) )

    def addMembers(self, members, noRecurse=True):
        cmds.editRenderLayerMembers( self, members, noRecurse=noRecurse )

    def removeMembers(self, members ):
        cmds.editRenderLayerMembers( self, members, remove=True )

    def listAdjustments(self):
        return map( general.PyNode, _util.listForNone( cmds.editRenderLayerAdjustment( self, layer=1, q=1) ) )

    def addAdjustments(self, members):
        return cmds.editRenderLayerAdjustment( members, layer=self )

    def removeAdjustments(self, members ):
        return cmds.editRenderLayerAdjustment( members, layer=self, remove=True )

    def setCurrent(self):
        cmds.editRenderLayerGlobals( currentRenderLayer=self)

class DisplayLayer(DependNode):
    def listMembers(self, fullNames=True):
        if fullNames:
            return map( general.PyNode, _util.listForNone( cmds.editDisplayLayerMembers( self, q=1, fullNames=True) ) )
        else:
            return _util.listForNone( cmds.editDisplayLayerMembers( self, q=1, fullNames=False) )

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
    _componentAttributes = {'u'           : general.NurbsCurveParameter,
                            'cv'          : general.NurbsCurveCV,
                            'conrolVerts' : general.NurbsCurveCV,
                            'ep'          : general.NurbsCurveEP,
                            'editPoints'  : general.NurbsCurveEP,
                            'knot'        : general.NurbsCurveKnot,
                            'knots'       : general.NurbsCurveKnot}

# apiToMelBridge maps MFnNurbsCurve.numCVs => NurbsCurve._numCVsApi
NurbsCurve.numCVs = \
    NurbsCurve._numCVsFunc_generator(NurbsCurve.form,
                                     NurbsCurve._numCVsApi,
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
            >>> from pymel.core import *
            >>> # a periodic curve
            >>> myCurve = curve(name='periodicCurve1', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] )
            >>> myCurve.cv
            NurbsCurveCV(u'periodicCurveShape1.cv[0:7]')
            >>> myCurve.numCVs()
            8
            >>> myCurve.numCVs(editableOnly=False)
            11
            >>>
            >>> # an open curve
            >>> myCurve = curve(name='openCurve1', d=3, periodic=False, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] )
            >>> myCurve.cv
            NurbsCurveCV(u'openCurveShape1.cv[0:10]')
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
            >>> from pymel.core import *
            >>> # a periodic curve
            >>> myCurve = curve(name='periodicCurve2', d=3, periodic=True, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] )
            >>> myCurve.ep
            NurbsCurveEP(u'periodicCurveShape2.ep[0:7]')
            >>> myCurve.numEPs()
            8
            >>>
            >>> # an open curve
            >>> myCurve = curve(name='openCurve2', d=3, periodic=False, k=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1)] )
            >>> myCurve.ep
            NurbsCurveEP(u'openCurveShape2.ep[0:8]')
            >>> myCurve.numEPs()
            9

        :rtype: `int`
        """)



class SurfaceShape(ControlPoint): pass

class NurbsSurface(SurfaceShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper
    _componentAttributes = {'u'           : (general.NurbsSurfaceRange, 'u'),
                            'uIsoparm'    : (general.NurbsSurfaceRange, 'u'),
                            'v'           : (general.NurbsSurfaceRange, 'v'),
                            'vIsoparm'    : (general.NurbsSurfaceRange, 'v'),
                            'uv'          : (general.NurbsSurfaceRange, 'uv'),
                            'cv'          : general.NurbsSurfaceCV,
                            'conrolVerts' : general.NurbsSurfaceCV,
                            'ep'          : general.NurbsSurfaceEP,
                            'editPoints'  : general.NurbsSurfaceEP,
                            'knot'        : general.NurbsSurfaceKnot,
                            'knots'       : general.NurbsSurfaceKnot,
                            'sf'          : general.NurbsSurfaceFace,
                            'faces'       : general.NurbsSurfaceFace}

# apiToMelBridge maps MFnNurbsCurve._numCVsInU => NurbsCurve._numCVsInUApi
NurbsSurface.numCVsInU = \
    NurbsSurface._numCVsFunc_generator(NurbsSurface.formInU,
                                       NurbsSurface._numCVsInUApi,
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
            >>> from pymel.core import *
            >>> # a periodic surface
            >>> mySurf = surface(name='periodicSurf1', du=3, dv=1, fu='periodic', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.cv[:][0].indices())        # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((7, 0), label=None)]
            >>> mySurf.numCVsInU()
            8
            >>> mySurf.numCVsInU(editableOnly=False)
            11
            >>>
            >>> # an open surface
            >>> mySurf = surface(name='openSurf1', du=3, dv=1, fu='open', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=((4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)) )
            >>> sorted(mySurf.cv[:][0].indices())        # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((10, 0), label=None)]
            >>> mySurf.numCVsInU()
            11
            >>> mySurf.numCVsInU(editableOnly=False)
            11

        :rtype: `int`
        """)

# apiToMelBridge maps MFnNurbsCurve._numCVsInV => NurbsCurve._numCVsInVApi
NurbsSurface.numCVsInV = \
    NurbsSurface._numCVsFunc_generator(NurbsSurface.formInV,
                                       NurbsSurface._numCVsInVApi,
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
            >>> from pymel.core import *
            >>> # a periodic surface
            >>> mySurf = surface(name='periodicSurf2', du=1, dv=3, fu='open', fv='periodic', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.cv[0].indices())         # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((0, 7), label='cv')]
            >>> mySurf.numCVsInV()
            8
            >>> mySurf.numCVsInV(editableOnly=False)
            11
            >>>
            >>> # an open surface
            >>> mySurf = surface(name='openSurf2', du=1, dv=3, fu='open', fv='open', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.cv[0].indices())          # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((0, 10), label='cv')]
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
            >>> from pymel.core import *
            >>> # a periodic surface
            >>> mySurf = surface(name='periodicSurf3', du=3, dv=1, fu='periodic', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.ep[:][0].indices())      # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((7, 0), label=None)]
            >>> mySurf.numEPsInU()
            8
            >>>
            >>> # an open surface
            >>> mySurf = surface(name='openSurf3', du=3, dv=1, fu='open', fv='open', ku=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), kv=(0, 1), pw=[(4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1), (0, 5.5, 0, 1), (0, 5.5, -2.5, 1), (-4, 4, 0, 1), (-4, 4, -2.5, 1), (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1), (-4, -4, 0, 1), (-4, -4, -2.5, 1), (0, -5.5, 0, 1), (0, -5.5, -2.5, 1), (4, -4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, 0, 1), (5.5, 0, -2.5, 1), (4, 4, 0, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.ep[:][0].indices())      # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((8, 0), label=None)]
            >>> mySurf.numEPsInU()
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
            >>> from pymel.core import *
            >>> # a periodic surface
            >>> mySurf = surface(name='periodicSurf4', du=1, dv=3, fu='open', fv='periodic', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.ep[0][:].indices())      # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((0, 7), label=None)]
            >>> mySurf.numEPsInV()
            8
            >>>
            >>> # an open surface
            >>> mySurf = surface(name='openSurf4', du=1, dv=3, fu='open', fv='open', ku=(0, 1), kv=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), pw=[(4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (0, 5.5, 0, 1), (-4, 4, 0, 1), (-5.5, 0, 0, 1), (-4, -4, 0, 1), (0, -5.5, 0, 1), (4, -4, 0, 1), (5.5, 0, 0, 1), (4, 4, 0, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1), (0, 5.5, -2.5, 1), (-4, 4, -2.5, 1), (-5.5, 0, -2.5, 1), (-4, -4, -2.5, 1), (0, -5.5, -2.5, 1), (4, -4, -2.5, 1), (5.5, 0, -2.5, 1), (4, 4, -2.5, 1)] )
            >>> sorted(mySurf.ep[0][:].indices())      # doctest: +ELLIPSIS
            [ComponentIndex((0, 0), ... ComponentIndex((0, 8), label=None)]
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

        >>> from pymel.core import *
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

    >>> from pymel.core import *
    >>> obj = polyTorus()[0]
    >>> colors = []
    >>> for i, vtx in enumerate(obj.vtx):   # doctest: +SKIP
    ...     edgs=vtx.toEdges()              # doctest: +SKIP
    ...     totalLen=0                      # doctest: +SKIP
    ...     edgCnt=0                        # doctest: +SKIP
    ...     for edg in edgs:                # doctest: +SKIP
    ...         edgCnt += 1                 # doctest: +SKIP
    ...         l = edg.getLength()         # doctest: +SKIP
    ...         totalLen += l               # doctest: +SKIP
    ...     avgLen=totalLen / edgCnt        # doctest: +SKIP
    ...     #print avgLen                   # doctest: +SKIP
    ...     currColor = vtx.getColor(0)     # doctest: +SKIP
    ...     color = datatypes.Color.black   # doctest: +SKIP
    ...     # only set blue if it has not been set before
    ...     if currColor.b<=0.0:            # doctest: +SKIP
    ...         color.b = avgLen            # doctest: +SKIP
    ...     color.r = avgLen                # doctest: +SKIP
    ...     colors.append(color)            # doctest: +SKIP


    """
    __metaclass__ = _factories.MetaMayaNodeWrapper
#    def __init__(self, *args, **kwargs ):
#        SurfaceShape.__init__(self, self._apiobject )
#        self.vtx = MeshEdge(self.__apimobject__() )
    _componentAttributes = {'vtx'   : general.MeshVertex,
                            'verts' : general.MeshVertex,
                            'e'     : general.MeshEdge,
                            'edges' : general.MeshEdge,
                            'f'     : general.MeshFace,
                            'faces' : general.MeshFace,
                            'map'   : general.MeshUV,
                            'uvs'   : general.MeshUV,
                            'vtxFace'   : general.MeshVertexFace,
                            'faceVerts' : general.MeshVertexFace}

    # Unfortunately, objects that don't yet have any mesh data - ie, if you do
    # createNode('mesh') - can't be fed into MFnMesh (even though it is a mesh
    # node).  This means that all the methods wrapped from MFnMesh won't be
    # usable in this case.  While it might make sense for some methods - ie,
    # editing methods like collapseEdges - to fail in this situation, some
    # basic methods like numVertices should still be usable.  Therefore,
    # we override some of these with the mel versions (which still work...)
    numVertices = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertex', 'numVertices' )
    numEdges = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edge', 'numEdges' )
    numFaces = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'face', 'numFaces' )

    numTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangles', 'numTriangles' )
    numSelectedTriangles = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'triangleComponent', 'numSelectedTriangles' )
    numSelectedFaces = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'faceComponent', 'numSelectedFaces' )
    numSelectedEdges = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'edgeComponent', 'numSelectedEdges' )
    numSelectedVertices = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'vertexComponent', 'numSelectedVertices' )

    area = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'area'  )
    worldArea = _factories.makeCreateFlagMethod( cmds.polyEvaluate, 'worldArea' )

    if versions.current() >= versions.v2009:
        @_factories.addApiDocs( _api.MFnMesh, 'currentUVSetName' )
        def getCurrentUVSetName(self):
            return self.__apimfn__().currentUVSetName( self.instanceNumber() )

        @_factories.addApiDocs( _api.MFnMesh, 'currentColorSetName' )
        def getCurrentColorSetName(self):
            return self.__apimfn__().currentColorSetName( self.instanceNumber() )

    else:
        @_factories.addApiDocs( _api.MFnMesh, 'currentUVSetName' )
        def getCurrentUVSetName(self):
            return self.__apimfn__().currentUVSetName()

        @_factories.addApiDocs( _api.MFnMesh, 'currentColorSetName' )
        def getCurrentColorSetName(self):
            return self.__apimfn__().currentColorSetName()

    @_factories.addApiDocs( _api.MFnMesh, 'numColors' )
    def numColors(self, colorSet=None):
        mfn = self.__apimfn__()
        # If we have an empty mesh, we will get an MFnDagNode...
        if not isinstance(mfn, _api.MFnMesh):
            return 0
        args = []
        if colorSet:
            args.append(colorSet)
        return mfn.numColors(*args)

# Unfortunately, objects that don't yet have any mesh data - ie, if you do
# createNode('mesh') - can't be fed into MFnMesh (even though it is a mesh
# node).  This means that all the methods wrapped from MFnMesh won't be
# usable in this case.  While it might make sense for some methods - ie,
# editing methods like collapseEdges - to fail in this situation, some
# basic methods like numVertices should still be usable.  Therefore,
# we override some of these with the mel versions (which still work...)

def _makeApiMethodWrapForEmptyMesh(apiMethodName, baseMethodName=None,
                                   resultName=None, defaultVal=0):
    if baseMethodName is None:
        baseMethodName = '_' + apiMethodName
    if resultName is None:
        resultName = apiMethodName

    baseMethod = getattr(Mesh, baseMethodName)

    @_factories.addApiDocs( _api.MFnMesh, apiMethodName )        
    def methodWrapForEmptyMesh(self, *args, **kwargs):
        # If we have an empty mesh, we will get an MFnDagNode...
        mfn = self.__apimfn__()
        if not isinstance(mfn, _api.MFnMesh):
            return defaultVal
        return baseMethod(self, *args, **kwargs)
    methodWrapForEmptyMesh.__name__ = resultName
    return methodWrapForEmptyMesh

for _apiMethodName in '''numColorSets
                    numFaceVertices
                    numNormals
                    numUVSets
                    numUVs'''.split():
    _wrappedFunc = _makeApiMethodWrapForEmptyMesh(_apiMethodName)
    setattr(Mesh, _wrappedFunc.__name__, _wrappedFunc)

class Subdiv(SurfaceShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper

    _componentAttributes = {'smp'   : general.SubdVertex,
                            'verts' : general.SubdVertex,
                            'sme'   : general.SubdEdge,
                            'edges' : general.SubdEdge,
                            'smf'   : general.SubdFace,
                            'faces' : general.SubdFace,
                            'smm'   : general.SubdUV,
                            'uvs'   : general.SubdUV}

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
    _componentAttributes = {'pt'    : general.LatticePoint,
                            'points': general.LatticePoint}

class Particle(DeformableShape):
    __metaclass__ = _factories.MetaMayaNodeWrapper

    class PointArray(general.ComponentArray):
        def __init__(self, name):
            general.ComponentArray.__init__(self, name)
            self.returnClass = Particle.Point

        def __len__(self):
            return cmds.particle(self.node(), q=1,count=1)

    class Point(general._Component):
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

class SelectionSet( _api.MSelectionList):
    apicls = _api.MSelectionList
    __metaclass__ = _factories.MetaMayaTypeWrapper

    def __init__(self, objs):
        """ can be initialized from a list of objects, another SelectionSet, an MSelectionList, or an ObjectSet"""
        if isinstance(objs, _api.MSelectionList ):
            _api.MSelectionList.__init__(self, objs)

        elif isinstance(objs, ObjectSet ):
            _api.MSelectionList.__init__(self, objs.asSelectionSet() )

        else:
            _api.MSelectionList.__init__(self)
            for obj in objs:
                if isinstance(obj, (DependNode, DagNode) ):
                    self.apicls.add( self, obj.__apiobject__() )
                elif isinstance(obj, general.Attribute):
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
            if _util.isIterable(selItem):
                melList.extend(selItem)
            else:
                melList.append(selItem)
        return melList

    def __len__(self):
        """:rtype: `int` """
        return self.apicls.length(self)

    def __contains__(self, item):
        """:rtype: `bool` """
        if isinstance(item, (DependNode, DagNode, general.Attribute) ):
            return self.apicls.hasItem(self, item.__apiobject__())
        elif isinstance(item, general.Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.hasItem(self, general.PyNode(item).__apiobject__())

    def __repr__(self):
        """:rtype: `str` """
        names = []
        self.apicls.getSelectionStrings( self, names )
        return 'nt.%s(%s)' % ( self.__class__.__name__, names )


    def __getitem__(self, index):
        """:rtype: `PyNode` """
        if index >= len(self):
            raise IndexError, "index out of range"

        plug = _api.MPlug()
        obj = _api.MObject()
        dag = _api.MDagPath()
        comp = _api.MObject()

        # Go from most specific to least - plug, dagPath, dependNode
        try:
            self.apicls.getPlug( self, index, plug )
            assert not plug.isNull()
        except (RuntimeError, AssertionError):
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

        if isinstance(item, (DependNode, DagNode, general.Attribute) ):
            return self.apicls.replace(self, index, item.__apiobject__())
        elif isinstance(item, general.Component):
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

        if isinstance(item, (DependNode, DagNode, general.Attribute) ):
            return self.apicls.add(self, item.__apiobject__())
        elif isinstance(item, general.Component):
            raise NotImplementedError, 'Components not yet supported'
        else:
            return self.apicls.add(self, general.PyNode(item).__apiobject__())


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
        if not isinstance( other, _api.MSelectionList ):
            other = SelectionSet( other )
        self.apicls.merge( self, other, _api.MSelectionList.kRemoveFromList )

    def getUnion(self, other):
        """:rtype: `SelectionSet`"""
        newSet = SelectionSet( self )
        newSet.union(other)
        return newSet

    def union(self, other):
        if not isinstance( other, _api.MSelectionList ):
            other = SelectionSet( other )
        self.apicls.merge( self, other, _api.MSelectionList.kMergeNormal )


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
        if not isinstance( other, _api.MSelectionList ):
            other = SelectionSet( other )
        # FIXME: does kXOR exist?  completion says only kXORWithList exists
        self.apicls.merge( self, other, _api.MSelectionList.kXOR )

    def asObjectSet(self):
        return general.sets( self )
#    def intersect(self, other):
#        self.apicls.merge( other, _api.MSelectionList.kXORWithList )



class ObjectSet(Entity):
    """
    The ObjectSet class and `SelectionSet` class work together.  Both classes have a very similar interface,
    the primary difference is that the ObjectSet class represents connections to an objectSet node, while the
    `SelectionSet` class is a generic set, akin to pythons built-in `set`.


    create some sets:

        >>> from pymel.core import *
        >>> f=newFile(f=1) #start clean
        >>>
        >>> s = sets()  # create an empty set
        >>> s.union( ls( type='camera') )  # add some cameras to it
        >>> s.members()  # doctest: +SKIP
        [nt.Camera(u'sideShape'), nt.Camera(u'frontShape'), nt.Camera(u'topShape'), nt.Camera(u'perspShape')]
        >>> sel = s.asSelectionSet() # or as a SelectionSet
        >>> sel # doctest: +SKIP
        nt.SelectionSet([u'sideShape', u'frontShape', u'topShape', u'perspShape'])
        >>> sorted(sel) # as a sorted list
        [nt.Camera(u'frontShape'), nt.Camera(u'perspShape'), nt.Camera(u'sideShape'), nt.Camera(u'topShape')]

    Operations between sets result in `SelectionSet` objects:

        >>> t = sets()  # create another set
        >>> t.add( 'perspShape' )  # add the persp camera shape to it
        >>> s.getIntersection(t)
        nt.SelectionSet([u'perspShape'])
        >>> diff = s.getDifference(t)
        >>> diff #doctest: +SKIP
        nt.SelectionSet([u'sideShape', u'frontShape', u'topShape'])
        >>> sorted(diff)
        [nt.Camera(u'frontShape'), nt.Camera(u'sideShape'), nt.Camera(u'topShape')]
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

    @classmethod
    def _getApiObjs(cls, item, tryCast=True):
        """
        Returns a tuple of api objects suitable (after unpacking) for
        feeding to most of the MFnSet methods (ie, remove, isMember, etc)
        """
        if isinstance(item, DagNode):
            return ( item.__apimdagpath__(), _api.MObject() )
        elif isinstance(item, (DependNode, general.Attribute) ):
            return ( item.__apiobject__(), )
        elif isinstance(item, general.Component):
            return ( item.__apimdagpath__(), item.__apimobject__() )
        elif tryCast:
            return cls._getApiObjs(general.PyNode(item), tryCast=False)
        else:
            raise TypeError(item)

    def __contains__(self, item):
        """:rtype: `bool` """
        return self.__apimfn__().isMember(*self._getApiObjs(item))

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

    @_warnings.deprecated( 'Use ObjectSet.members instead', 'ObjectSet' )
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
        return self.__apimfn__().addMember(*self._getApiObjs(item))

    def remove(self, item):
        try:
            return self.__apimfn__().removeMember(*self._getApiObjs(item))
        except RuntimeError:
            # Provide a more informative error if object is not in set
            if item not in self:
                try:
                    itemStr = repr(item)
                except Exception:
                    itemStr = 'item'
                raise ValueError("%s not in set %r" % (itemStr, self))
            else:
                raise

    def isSubSet(self, other):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSubSet(other)

    def isSuperSet(self, other ):
        """:rtype: `bool`"""
        return self.asSelectionSet().isSuperSet(other)

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

    def isRenderable(self):
        '''Mimics cmds.sets(self, q=True, renderable=True).

        Alternatively you can use isinstance(someset, pm.nt.ShadingEngine)
        since shadingEngine is the only renderable set in maya now
        '''
        return bool(cmds.sets(self, q=True, r=True))

class ShadingEngine(ObjectSet):
    @classmethod
    def _getApiObjs(cls, item, tryCast=True):
        # Since shading groups can't contain transforms, as a convenience,
        # use getShape on any transforms
        if isinstance(item, Transform):
            shape = item.getShape()
            if shape:
                return cls._getApiObjs(shape)
            else:
                try:
                    itemStr = repr(item)
                except Exception:
                    itemStr = 'item'
                raise TypeError("%s has no shape, and %s objects cannot contain Transforms" % (itemStr, cls.__name__))
        else:
            return super(ShadingEngine, cls)._getApiObjs(item, tryCast=tryCast)

class AnimCurve(DependNode):
    __metaclass__ = _factories.MetaMayaNodeWrapper

    def addKeys(self,time,values,tangentInType='linear',tangentOutType='linear',unit=None):
        if not unit:
            unit = _api.MTime.uiUnit()
        times = _api.MTimeArray()
        for frame in time: times.append(_api.MTime(frame,unit))
        keys = _api.MDoubleArray()
        for value in values: keys.append(value)
        return self.__apimfn__().addKeys( times, keys,
                                          _factories.apiClassInfo['MFnAnimCurve']['enums']['TangentType']['values'].getIndex('kTangent'+tangentInType.capitalize()),
                                          _factories.apiClassInfo['MFnAnimCurve']['enums']['TangentType']['values'].getIndex('kTangent'+tangentOutType.capitalize()))

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
            components = _api.toComponentMObject( geometry.__apimdagpath__() )
        elif isinstance(geometry, general.Component):
            components = geometry.__apiobject__()

        else:
            raise TypeError

        if influenceIndex is not None:
            weights = _api.MDoubleArray()
            self.__apimfn__().getWeights( geometry.__apimdagpath__(), components, influenceIndex, weights )
            return iter(weights)
        else:
            weights = _api.MDoubleArray()
            index = _api.SafeApiPtr('uint')
            self.__apimfn__().getWeights( geometry.__apimdagpath__(), components, weights, index() )
            index = index.get()
            args = [iter(weights)] * index
            return itertools.izip(*args)

    def setWeights(self, geometry, influnces, weights, normalize=True):
        if not isinstance(geometry, general.PyNode):
            geometry = general.PyNode(geometry)

        if isinstance( geometry, Transform ):
            try:
                geometry = geometry.getShape()
            except:
                raise TypeError, "%s is a transform with no shape" % geometry

        if isinstance(geometry, GeometryShape):
            components = _api.toComponentMObject( geometry.__apimdagpath__() )
        elif isinstance(geometry, general.Component):
            components = geometry.__apiobject__()

        else:
            raise TypeError

        if not isinstance(influnces,_api.MIntArray):
            api_influnces = _api.MIntArray()
            for influnce in influnces:
                api_influnces.append(influnce)
            influnces = api_influnces

        if not isinstance(weights,_api.MDoubleArray):
            api_weights = _api.MDoubleArray()
            for weight in weights:
                api_weights.append(weight)
            weights = api_weights

        old_weights = _api.MDoubleArray()
        su = _api.MScriptUtil()
        su.createFromInt(0)
        index = su.asUintPtr()
        self.__apimfn__().getWeights( geometry.__apimdagpath__(), components, old_weights, index )
        return self.__apimfn__().setWeights( geometry.__apimdagpath__(), components, influnces, weights, normalize, old_weights )

    @_factories.addApiDocs( _api.MFnSkinCluster, 'influenceObjects' )
    def influenceObjects(self):
        return self._influenceObjects()[1]

    def numInfluenceObjects(self):
        return self._influenceObjects()[0]

_factories.ApiTypeRegister.register( 'MSelectionList', SelectionSet )


def _createPyNodes():

    dynModule = _util.LazyLoadModule(__name__, globals())

    for mayaType, parents, children in _factories.nodeHierarchy:

        if mayaType == 'dependNode':
        # This seems like the more 'correct' way of doing it - only node types
        # that are currently available have PyNodes created for them - but
        # changing it so some PyNodes are no longer available until their
        # plugin is loaded may create backwards incompatibility issues... 
#        if (mayaType == 'dependNode'
#                or mayaType not in _factories.mayaTypesToApiTypes):
            continue

        parentMayaType = parents[0]
        #print "superNodeType: ", superNodeType, type(superNodeType)
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue

        #className = _util.capitalize(mayaType)
        #if className not in __all__: __all__.append( className )

        _factories.addPyNode( dynModule, mayaType, parentMayaType )

    sys.modules[__name__] = dynModule


# Initialize Pymel classes to API types lookup
#_startTime = time.time()
_createPyNodes()
#_logger.debug( "Initialized Pymel PyNodes types list in %.2f sec" % time.time() - _startTime )

dynModule = sys.modules[__name__]
#def listToMSelection( objs ):
#    sel = _api.MSelectionList()
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

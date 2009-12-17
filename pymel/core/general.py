"""
Contains general node and attribute functions, as well as the main `PyNode` base class. 

For the rest of the class hierarchy, including `DependNode <pymel.core.nodetypes.DependNode>`, `Transform <pymel.core.nodetypes.Transform>`, 
and `Attribute <pymel.core.nodetypes.Attribute>`, see :mod:`pymel.core.nodetypes`.


"""


import sys, os, re
from getpass import getuser
from socket import gethostname
import inspect, timeit, time

import pymel.internal.pmcmds as cmds
import pymel.util as util
import pymel.internal.factories as _factories
import pymel.api as _api

import datatypes
import logging
from maya.cmds import about as _about

_logger = logging.getLogger(__name__)


# TODO: factories.functionFactory should automatically handle conversion of output to PyNodes...
#       ...so we shouldn't always have to do it here as well?

def _getPymelTypeFromObject(obj, name):
        compTypes = _factories.apiEnumsToPyComponents.get(obj.apiType(), None)
        if compTypes is not None:
            if len(compTypes) == 1:
                return compTypes[0]
            else:
                raise RuntimeError('Got an instance of a component with more than one possible PyNode type: %s' % obj.apiTypeStr())
        else:
            try:  
                fnDepend = _api.MFnDependencyNode( obj )
                mayaType = fnDepend.typeName()
                import nodetypes
                pymelType = getattr( nodetypes, util.capitalize(mayaType), nodetypes.DependNode )

            except RuntimeError:
                raise MayaNodeError
            
            if pymelType in _factories.virtualClass:
                data = _factories.virtualClass[pymelType]
                nodeName = name
                for virtualCls, nameRequired in data:
                    if nameRequired and nodeName is None:
                        nodeName = fnDepend.name()
                    
                    if virtualCls._isVirtual(obj, nodeName):
                        pymelType = virtualCls
                        break
            return pymelType

def _getPymelType(arg, name) :
    """ Get the correct Pymel Type for an object that can be a MObject, PyNode or name of an existing Maya object,
        if no correct type is found returns DependNode by default.
        
        If the name of an existing object is passed, the name and MObject will be returned
        If a valid MObject is passed, the name will be returned as None
        If a PyNode instance is passed, its name and MObject will be returned
        """

    obj = None
    results = {}
    
    isAttribute = False
  
    #--------------------------   
    # API object testing
    #--------------------------   
    if isinstance(arg, _api.MObject) :     
        results['MObjectHandle'] = _api.MObjectHandle( arg )
        obj = arg
                    
    elif isinstance(arg, _api.MObjectHandle) :      
        results['MObjectHandle'] = arg
        obj = arg.object()
           
    elif isinstance(arg, _api.MDagPath) :
        results['MDagPath'] = arg
        obj = arg.node()
                              
    elif isinstance(arg, _api.MPlug) : 
        isAttribute = True
        obj = arg
        results['MPlug'] = obj
        if _api.isValidMPlug(arg):
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
        pymelType = _getPymelTypeFromObject( obj, name ) 
    
    return pymelType, results
#-----------------------------------------------
#  Enhanced Commands
#-----------------------------------------------

# TODO: possible bugfix for 'parent'?
# Docs state 'If there is only a single object specified then the selected objects are parented to that object. '
# ...but actual behavior is to parent the named object (and any other selected objects) to the last selected object

def about(**kwargs):
    """
Modifications:
  - added apiVersion/_api flag to about command for version 8.5 and 8.5sp1
    """
    if kwargs.get('apiVersion', kwargs.get('_api',False)):
        try:
            return _about(_api=1)
        except TypeError:
            return { 
             '8.5 Service Pack 1': 200701,
             '8.5': 200700,
             }[ _about(version=1)]
             
    return _about(**kwargs)


          
#-----------------------
#  Object Manipulation
#-----------------------

def select(*args, **kwargs):
    """
Modifications:
  - passing an empty list no longer causes an error. instead, the selection is cleared
    
    """
    
    try:
        cmds.select(*args, **kwargs)
    except TypeError, msg:
        if args == ([],):
            cmds.select(cl=True)
        else:
            raise TypeError, msg
#select.__doc__ = mel.help('select') + select.__doc__


# TODO: make it handle multiple objects, like original command
def move(obj, *args, **kwargs):
    """
Modifications:
  - allows any iterable object to be passed as first argument::
    
        move("pSphere1", [0,1,2])
        
NOTE: this command also reorders the argument order to be more intuitive, with the object first
    """
    if len(args) == 1 and util.isIterable(args[0]):
        args = tuple(args[0])
    args = args + (obj,)
    return cmds.move(*args, **kwargs)

def scale(obj, *args, **kwargs):
    """
Modifications:
  - allows any iterable object to be passed as first argument::
    
        scale("pSphere1", [0,1,2])
        
NOTE: this command also reorders the argument order to be more intuitive, with the object first
    """
    if len(args) == 1 and util.isIterable(args[0]):
        args = tuple(args[0])
    args = args + (obj,)
    return cmds.scale(*args, **kwargs)
    
def rotate(obj, *args, **kwargs):
    """
Modifications:
  - allows any iterable object to be passed as first argument::
    
        rotate("pSphere1", [0,1,2])
        
NOTE: this command also reorders the argument order to be more intuitive, with the object first
    """
    if len(args) == 1 and util.isIterable(args[0]):
        args = tuple(args[0])
    args = args + (obj,)
    return cmds.rotate(*args, **kwargs)



#-----------------------
#  Attributes
#-----------------------
        
def connectAttr( source, destination, **kwargs ):
    """
Maya Bug Fix: 
  - even with the 'force' flag enabled, the command would raise an error if the connection already existed. 
    
    """
    if kwargs.get('force', False) or kwargs.get('f', False):    
        try:
            cmds.connectAttr( source, destination, **kwargs )
        except RuntimeError, e:
            if str(e) != 'Maya command error':
                # we only want to pass on a certain connection error.  all others we re-raise
                raise e
    else:
        cmds.connectAttr( source, destination, **kwargs )

def disconnectAttr( source, destination=None, **kwargs ):
    """
Modifications:
  - If no destination is passed, all inputs and outputs will be disconnected from the attribute
    """
    
    if destination:
        cmds.disconnectAttr( source, destination, **kwargs )
    else:
        # if disconnectingInputs, we're disconnecting inputs; otherwise, we're disconnecting outputs
        for disconnectingInputs in (True, False):
            connections = cmds.listConnections(source,
                                               source=disconnectingInputs,
                                               destination=(not disconnectingInputs),
                                               connections=True,
                                               plugs=True)
            # stupid maya.cmds returns None instead of []...
            if connections is None: continue
            
            # if disconnectingInputs, results from listConnections will be returned in dest, src order -
            # reverse the list to flip this to src, dest
            if disconnectingInputs:
                connections.reverse()
            
            for src, dest in util.pairIter(connections):
                cmds.disconnectAttr( src, dest, **kwargs )  
        
def getAttr( attr, default=None, **kwargs ):
    """
Maya Bug Fix:
  - maya pointlessly returned vector results as a tuple wrapped in a list ( ex.  '[(1,2,3)]' ). This command unpacks the vector for you.

Modifications:
  - casts double3 datatypes to `Vector`
  - casts matrix datatypes to `Matrix`
  - casts vectorArrays from a flat array of floats to an array of Vectors
  - when getting a multi-attr, maya would raise an error, but pymel will return a list of values for the multi-attr
  - added a default argument. if the attribute does not exist and this argument is not None, this default value will be returned
    """
    def listToMat( l ):
        return datatypes.Matrix(
            [     [    l[0], l[1], l[2], l[3]    ],
            [    l[4], l[5], l[6], l[7]    ],
            [    l[8], l[9], l[10], l[11]    ],
            [    l[12], l[13], l[14], l[15] ]    ])
    
    def listToVec( l ):
        vecRes = []
        for i in range( 0, len(res), 3):
            vecRes.append( datatypes.Vector( res[i:i+3] ) )
        return vecRes

    # stringify fix
    attr = unicode(attr)

    try:
        res = cmds.getAttr( attr, **kwargs)
        
        if isinstance(res, list) and len(res):
            if isinstance(res[0], tuple):
                typ = cmds.getAttr( attr, type=1)
                if typ == 'pointArray':
                    return [ datatypes.Point(x) for x in res ]
                
                res = res[0]
                if typ == 'double3':
                    
                    return datatypes.Vector(list(res))

            #elif cmds.getAttr( attr, type=1) == 'matrix':
            #    return listToMat(res)
            else:
                try:
                    return { 
                        'matrix': listToMat,
                        'vectorArray' : listToVec
                        }[cmds.getAttr( attr, type=1)](res)
                except KeyError: pass
        return res
    
    # perhaps it error'd because it's a mixed compound, or a multi attribute
    except RuntimeError, e:
        try:
            pyattr = Attribute(attr)
            # mixed compound takes precedence, because by default, compound attributes are returned by getAttr, but
            # mixed compounds cannot be expressed in a mel array.
            if pyattr.isCompound():
                return [child.get() for child in pyattr.getChildren() ]
            elif pyattr.isMulti():
                return [attr[i].get() for i in range(pyattr.size())]
            # re-raise error
            raise
        except AttributeError:
            if default is not None:
                return default
            # raise original RuntimeError
            raise e


class AmbiguityWarning(Warning):
    pass

# getting and setting                    
def setAttr( attr, *args, **kwargs):
    """
Maya Bug Fix:
  - setAttr did not work with type matrix. 

Modifications:
  - No need to set type, this will automatically be determined
  - Adds support for passing a list or tuple as the second argument for datatypes such as double3.
  - When setting stringArray datatype, you no longer need to prefix the list with the number of elements - just pass a list or tuple as with other arrays
  - Added 'force' kwarg, which causes the attribute to be added if it does not exist. 
        - if no type flag is passed, the attribute type is based on type of value being set (if you want a float, be sure to format it as a float, e.g.  3.0 not 3)
        - currently does not support compound attributes
        - currently supported python-to-maya mappings:   
        
            python type  maya type
            ============ ===========
            float        double
            ------------ -----------
            int          long
            ------------ -----------
            str          string
            ------------ -----------
            bool         bool
            ------------ -----------
            Vector       double3
            ------------ -----------
            Matrix       matrix
            ------------ -----------
            [str]        stringArray
            ============ ===========
     
           
    >>> addAttr( 'persp', longName= 'testDoubleArray', dataType='doubleArray') 
    >>> setAttr( 'persp.testDoubleArray', [0,1,2])
    >>> setAttr( 'defaultRenderGlobals.preMel', 'sfff')
    
    """
    datatype = kwargs.get( 'type', kwargs.get( 'typ', None) )
    
    # if there is only one argument we do our special pymel tricks
    if len(args) == 1:
        
        arg = args[0]
        
        # force flag
        force = kwargs.pop('force', kwargs.pop('f', False) )
        
        
        # vector, matrix, and arrays
        if util.isIterable(arg):
            if datatype is None:
                # if we're using force flag and the attribute does not exist
                # we can infer the type from the passed value
                #attr = Attribute(attr)
                if force and not cmds.objExists(attr): #attr.exists():
                    import pymel.util.nameparse as nameparse
                    attrName = nameparse.parse( attr )
                    assert attrName.isAttributeName(), "passed object is not an attribute"
                    try:
                        if isinstance( arg[0], (basestring, util.ProxyUnicode ) ):
                            datatype = 'stringArray'
                        elif isinstance( arg[0], (list,datatypes.Vector) ):
                            datatype = 'vectorArray'
                        elif isinstance( arg[0], (list,datatypes.Point) ):
                            datatype = 'pointArray'
                        elif isinstance( arg, datatypes.Vector):
                            datatype = 'double3'
                        elif isinstance( arg,  datatypes.Matrix ):
                            datatype = 'matrix'
                        elif isinstance( arg[0], int ):
                            datatype = 'Int32Array'
                        elif isinstance( arg[0], float ):
                            datatype = 'doubleArray'
                            if len(arg)==3:
                                _logger.warn(
                                    "The supplied value will be interperted as a 'doubleArray' and not as a 'double3' (vector). "
                                    "Supply an explicit 'datatype' argument to avoid this warning." )
                        else:
                            raise ValueError, "pymel.core.setAttr: %s is not a supported type for use with the force flag" % type(arg[0])

                        _logger.debug("adding %r as %r", attr, datatype)
                        addAttr( attrName.nodePath, ln=attrName.attribute, dt=datatype ) 
                        kwargs['type'] = datatype
                        
                    # empty array is being passed
                    # if the attribute exists, this is ok
                    except IndexError:
                        raise ValueError, "pymel.core.setAttr: when setting 'force' keyword to create a new array attribute, you must provide an array with at least one element"                      
                    
                    except TypeError:
                        raise ValueError, "pymel.core.setAttr: %s is not a supported type" % type(args)
                    
                    kwargs['type'] = datatype
                
                else:
                    if isinstance( arg, datatypes.Vector):
                        datatype = 'double3'
                    elif isinstance( arg, datatypes.Matrix ):
                        datatype = 'matrix'
                    else:        
                        datatype = getAttr( attr, type=1)
                        if not datatype:
                            datatype = addAttr( attr, q=1, dataType=1) #[0] # this is returned as a single element list
                    
                        # set datatype for arrays
                        # we could do this for all, but i'm uncertain that it needs to be 
                        # done and it might cause more problems
                        if datatype.endswith('Array'):
                            kwargs['type'] = datatype
            
            if datatype == 'stringArray':
                # string arrays:
                #    first arg must be the length of the array being set
                # ex:
                #     setAttr('loc.strArray',["first", "second", "third"] )    
                # becomes:
                #     cmds.setAttr('loc.strArray',3,"first", "second", "third",type='stringArray')
                args = tuple( [len(arg)] + arg )
            
            elif datatype in ['vectorArray', 'pointArray']:
                # vector arrays:
                #    first arg must be the length of the array being set
                #    empty values are placed between vectors
                # ex:
                #     setAttr('loc.vecArray',[1,2,3],[4,5,6],[7,8,9] )    
                # becomes:
                #     cmds.setAttr('loc.vecArray',3,[1,2,3],"",[4,5,6],"",[7,8,9],type='vectorArray')
                arg = list(arg)
                size = len(arg)
                try:
                    tmpArgs = [arg.pop(0)]
                    for filler, real in zip( [""]*(size-1), arg ):
                        tmpArgs.append( filler )
                        tmpArgs.append( real )
                except IndexError:
                    tmpArgs = []
                            
                args = tuple( [size] + tmpArgs )
                #print args
            
            elif datatype in ['Int32Array', 'doubleArray']:
                # int32 and double arrays: 
                #   actually fairly sane
                # ex:
                #     setAttr('loc.doubleArray',[1,2,3] )    
                # becomes:
                #     cmds.setAttr('loc.doubleArray',[1,2,3],type='doubleArray')
                args = (tuple(arg),)
 
            else: 
                # others: short2, short3, long2, long3, float2, etc...
                #    args must be expanded
                # ex:
                #     setAttr('loc.foo',[1,2,3] )    
                # becomes:
                #     cmds.setAttr('loc.foo',1,2,3 )   
                args = tuple(arg)
                
        # non-iterable types
        else:
            if datatype is None:
                #attr = Attribute(attr)    
                if force and not cmds.objExists(attr): #attr.exists(): 
                    import pymel.util.nameparse as nameparse
                    attrName = nameparse.parse( attr )
                    assert attrName.isAttributeName(), "passed object is not an attribute"
                    if isinstance( arg, basestring ):
                        addAttr( attrName.nodePath, ln=attrName.attribute, dt='string' )
                        kwargs['type'] = 'string'
                    elif isinstance( arg, int ):
                        addAttr( attrName.nodePath, ln=attrName.attribute, at='long' ) 
                    elif isinstance( arg, float ):
                        addAttr( attrName.nodePath, ln=attrName.attribute, at='double' ) 
                    elif isinstance( arg, bool ):
                        addAttr( attrName.nodePath, ln=attrName.attribute, at='bool' ) 
                    else:
                        raise TypeError, "%s.setAttr: %s is not a supported type for use with the force flag" % ( __name__, type(arg) )
                                        
                elif isinstance(arg,basestring) or isinstance(arg, util.ProxyUnicode):
                    kwargs['type'] = 'string'

    if datatype == 'matrix':
        cmd = 'setAttr -type "matrix" "%s" %s' % (attr, ' '.join( map( str, args ) ) )
        import maya.mel as _mm
        _mm.eval(cmd)
        return 
    
    # stringify fix
    attr = unicode(attr)   

    try:
        #print args, kwargs
        # NOTE: changed *args to args to get array types to work. this may be a change between 8.5 and 2008, because i swear i've tested this before
        cmds.setAttr( attr, *args, **kwargs)
    except TypeError, msg:
        val = kwargs.pop( 'type', kwargs.pop('typ', False) )
        typ = addAttr( attr, q=1, at=1)
        if val == 'string' and typ == 'enum':
            enums = addAttr(attr, q=1, en=1).split(":")
            index = enums.index( args[0] )
            args = ( index, )
            cmds.setAttr( attr, *args, **kwargs)
        else:
            raise TypeError, msg
    except RuntimeError, msg:
        # normally this is handled in pmcmds, but setAttr error is different for some reason
        if str(msg).startswith('No object matches name: '):
            raise _objectError(attr)
        else:
            # re-raise
            raise
            
def addAttr( *args, **kwargs ):
    """
Modifications:
  - allow python types to be passed to set -at type
            str        S{->} string
            float     S{->} double
            int        S{->} long
            bool    S{->} bool
            Vector    S{->} double3
  - when querying dataType, the dataType is no longer returned as a list
    """
    at = kwargs.pop('attributeType', kwargs.pop('at', None ))
    if at is not None:
        try: 
            kwargs['at'] = {
                float: 'double',
                int: 'long',
                bool: 'bool',
                datatypes.Vector: 'double3',
                str: 'string',
                unicode: 'string'
            }[at]
        except KeyError:
            kwargs['at'] = at
    
    # MObject stringify Fix
    #args = map(unicode, args) 
    res = cmds.addAttr( *args, **kwargs )
    if kwargs.get( 'q', kwargs.get('query',False) ) and kwargs.get( 'dt', kwargs.get('dataType',False) ):
        res = res[0]
    
    return res

def hasAttr( pyObj, attr, checkShape=True ):
    """convenience function for determining if an object has an attribute.
    If checkShape is enabled, the shape node of a transform will also be checked for the attribute.
    
    :rtype: `bool`
    """
    if not isinstance( pyObj, PyNode ):
        raise TypeError, "hasAttr requires a PyNode instance and a string"
    
    import nodetypes
    if isinstance( pyObj, nodetypes.Transform ):
        try:
            pyObj.attr(attr,checkShape=checkShape)
            return True
        except AttributeError: 
            return False
        
    try:  
        pyObj.attr(attr)
        return True
    except AttributeError:
        return False

#-----------------------
#  List Functions
#-----------------------

def listAttr(*args, **kwargs):
    """
Modifications:
  - returns an empty list when the result is None
    """
    return util.listForNone(cmds.listAttr(*args, **kwargs))
      
def listConnections(*args, **kwargs):
    """
Modifications:
  - returns an empty list when the result is None
  - When 'connections' flag is True, the attribute pairs are returned in a 2D-array::
    
        [['checker1.outColor', 'lambert1.color'], ['checker1.color1', 'fractal1.outColor']]
        
  - added sourceFirst keyword arg. when sourceFirst is true and connections is also true, 
        the paired list of plugs is returned in (source,destination) order instead of (thisnode,othernode) order.
        this puts the pairs in the order that disconnectAttr and connectAttr expect.
  - added ability to pass a list of types
    
    :rtype: `PyNode` list
    """
    def makePairs(l):
        if l is None:
            return []
        return [(PyNode(a), PyNode(b)) for (a, b) in util.pairIter(l)]
            
    # group the core functionality into a funcion, so we can call in a loop when passed a list of types    
    def doIt(**kwargs):
        if kwargs.get('connections', kwargs.get('c', False) ) :    
                  
            if kwargs.pop('sourceFirst',False):
                source = kwargs.get('source', kwargs.get('s', True ) )
                dest = kwargs.get('destination', kwargs.get('d', True ) )
    
                if source:                
                    if not dest:
                        return [ (s, d) for d, s in makePairs( cmds.listConnections( *args,  **kwargs ) ) ]
                    else:
                        res = []
                        kwargs.pop('destination', None)
                        kwargs['d'] = False                    
                        res = [ (s, d) for d, s in makePairs( cmds.listConnections( *args,  **kwargs )) ]                    
    
                        kwargs.pop('source', None)
                        kwargs['s'] = False
                        kwargs['d'] = True
                        return makePairs(cmds.listConnections( *args,  **kwargs )) + res
                        
                # if dest passes through to normal method 
                
            return makePairs( cmds.listConnections( *args,  **kwargs ) )
    
        else:
            return map(PyNode, util.listForNone(cmds.listConnections( *args,  **kwargs )) )
    
    # if passed a list of types, concatenate the resutls
    # NOTE: there may be duplicate results if a leaf type and it's parent are both passed: ex.  animCurve and animCurveTL
    types = kwargs.get('type', kwargs.get('t',None))
    if util.isIterable(types):
        types = list(set(types)) # remove dupes from types list
        kwargs.pop('type',None)
        kwargs.pop('t',None)
        res = []
        for type in types:
            ikwargs = kwargs.copy()
            ikwargs['type'] = type
            res += doIt(**ikwargs)
        return res
    else:
        return doIt(**kwargs)

def listHistory( *args, **kwargs ):
    """
Modifications:
  - returns an empty list when the result is None
  - added a much needed 'type' filter
  - added an 'exactType' filter (if both 'exactType' and 'type' are present, 'type' is ignored)
    
    :rtype: `DependNode` list
    
    """

    type = exactType = None
    if 'type' in kwargs:
        type = kwargs.pop('type')
    if 'exactType' in kwargs:
        exactType = kwargs.pop('exactType')

    results = [PyNode(x) for x in util.listForNone(cmds.listHistory( *args,  **kwargs ))]

    if exactType:
        results = [x for x in results if x.nodeType() == exactType]
    elif type:
        results = [x for x in results if type in x.nodeType(inherited=True)]

    return results

        
def listFuture( *args, **kwargs ):
    """
Modifications:
  - returns an empty list when the result is None
  - added a much needed 'type' filter
  - added an 'exactType' filter (if both 'exactType' and 'type' are present, 'type' is ignored)
    
    :rtype: `DependNode` list
    
    """
    kwargs['future'] = True
    
    return listHistory(*args, **kwargs)

        
def listRelatives( *args, **kwargs ):
    """
Maya Bug Fix:
  - allDescendents and shapes flags did not work in combination
    
Modifications:
  - returns an empty list when the result is None
  - returns wrapped classes
  - fullPath is forced on to ensure that all returned node paths are unique
    
    :rtype: `DependNode` list
    """
    kwargs['fullPath'] = True
    kwargs.pop('f', None)
    # Stringify Fix
    #args = [ unicode(x) for x in args ]
    if kwargs.get( 'allDescendents', kwargs.get('ad', False) ) and kwargs.pop( 'shapes', kwargs.pop('s', False) ):        
        kwargs['fullPath'] = True
        kwargs.pop('f', None)

        res = cmds.listRelatives( *args, **kwargs)
        if res is None:
            return []
        return ls( res, shapes=1)
                
    return map(PyNode, util.listForNone(cmds.listRelatives(*args, **kwargs)))


def ls( *args, **kwargs ):
    """
Modifications:
  - Added new keyword: 'editable' - this will return the inverse set of the readOnly flag. i.e. non-read-only nodes
  - Added new keyword: 'regex' - pass a valid regular expression string, compiled regex pattern, or list thereof. 
   
        >>> group('top')
        nt.Transform(u'group1')
        >>> duplicate('group1')
        [nt.Transform(u'group2')]
        >>> ls(regex='group\d+\|top') # don't forget to escape pipes `|` 
        [nt.Transform(u'group1|top'), nt.Transform(u'group2|top')]
        >>> ls(regex='group\d+\|top.*')
        [nt.Transform(u'group1|top'), nt.Camera(u'group1|top|topShape'), nt.Transform(u'group2|top'), nt.Camera(u'group2|top|topShape')]
        >>> ls(regex='group\d+\|top.*', cameras=1)
        [nt.Camera(u'group2|top|topShape'), nt.Camera(u'group1|top|topShape')]
        >>> ls(regex='\|group\d+\|top.*', cameras=1) # add a leading pipe
        [nt.Camera(u'group1|top|topShape')]
        
    The regular expression will be used to search the full DAG path, starting from the right, in a similar fashion to how globs currently work.
    Technically speaking, your regular expression string is used like this::
        
        re.search( '(\||^)' + yourRegexStr + '$', fullNodePath )
        
    :rtype: `PyNode` list
    """
    kwargs['long'] = True
    kwargs.pop('l', None)

#    # TODO: make this safe for international unicode characters
#    validGlobChars = re.compile('[a-zA-Z0-9_|.*?\[\]]+$')
#    newArgs = []
#    regexArgs = []
#    for arg in args:
#        if isinstance(arg, (list, tuple)):
#            # maya only goes one deep, and only checks for lists or tuples
#            for subarg in arg:
#                if isinstance(subarg, basestring) and not validGlobChars.match(subarg):
#                    regexArgs.append(subarg)
#                else:
#                    newArgs.append(subarg)
#        elif isinstance(arg, basestring) and not validGlobChars.match(arg):
#            regexArgs.append(arg)
#        else:
#            newArgs.append(arg)
    
    regexArgs = kwargs.pop('regex', [])
    if not isinstance(regexArgs, (tuple,list)):
        regexArgs = [regexArgs]
    
    for i,val in enumerate(regexArgs):
        # add a prefix which allows the regex to match against a dag path, mounted at the right
        if isinstance(val,basestring):
            if not val.endswith('$'):
                val = val + '$'
            val = re.compile('(\||^)' + val)
        elif not isinstance(val,re._pattern_type):
            raise TypeError( 'regex flag must be passed a valid regex string, a compiled regex object, or a list of these types. got %s' % type(val).__name__ )
        regexArgs[i] = val
    
    res = util.listForNone(cmds.ls(*args, **kwargs))
    if regexArgs:
        tmp = res
        res = []
        for x in tmp:
            for reg in regexArgs:
                if reg.search(x):
                    res.append(x)
                    break
    
    if kwargs.pop('editable', False):
        kwargs['readOnly'] = True
        kwargs.pop('ro',True)
        roNodes = util.listForNone(cmds.ls(*args, **kwargs))
        # faster way?
        return map( PyNode, filter( lambda x: x not in roNodes, res ) )

    
    if kwargs.get( 'readOnly', kwargs.get('ro', False) ):
        # when readOnly is provided showType is ignored
        return map(PyNode, res)
        
    if kwargs.get( 'showType', kwargs.get('st', False) ):
        tmp = res
        res = []
        for i in range(0,len(tmp),2):
            res.append( PyNode( tmp[i] ) )
            res.append( tmp[i+1] )
        return res    
    
    if kwargs.get( 'nodeTypes', kwargs.get('nt', False) ):
        return res
    
#    kwargs['showType'] = True
#    tmp = util.listForNone(cmds.ls(*args, **kwargs))
#    res = []
#    for i in range(0,len(tmp),2):
#        res.append( PyNode( tmp[i], tmp[i+1] ) )
#    
#    return res
    return map(PyNode, res)
    
 
#    showType = kwargs.get( 'showType', kwargs.get('st', False) )
#    kwargs['showType'] = True
#    kwargs.pop('st',None)    
#    res = []
#    if kwargs.get( 'readOnly', kwargs.get('ro', False) ):
#        
#        ro = cmds.ls(*args, **kwargs) # showType flag will be ignored
#        
#        # this was unbelievably slow
#        
#        kwargs.pop('readOnly',None)
#        kwargs.pop('ro',None)
#        all = cmds.ls(*args, **kwargs)
#        for pymel.core.node in ro:
#            try:    
#                idx = all.index(pymel.core.node)
#                all.pop(idx)
#                typ = all.pop(idx+1)
#                res.append( PyNode( pymel.core.node, typ ) ) 
#                if showType:
#                    res.append( typ )
#            except ValueError: pass
#        return res
#    else:
#        tmp = util.listForNone(cmds.ls(*args, **kwargs))
#        for i in range(0,len(tmp),2):
#            typ = tmp[i+1]
#            res.append( PyNode( tmp[i],  ) )    
#            if showType:
#                res.append( typ )
#        
#        return res


def listTransforms( *args, **kwargs ):
    """
Modifications:
  - returns wrapped classes
    
    :rtype: `Transform` list
    """
    kwargs['ni']=True
    res = cmds.ls(*args, **kwargs)
    if not res:
        return res
    res = cmds.listRelatives(  res, p=1, path=1 )
    if res is None:
        return []
    #res = list(set(res)) # ruins the order, but prevents dupes, which can happend when a transform has more than one shape
    return [PyNode(x) for x in res] #, ['transform']*len(res) )


    
#-----------------------
#  Objects
#-----------------------

def nodeType( node, **kwargs ):
    """
    Note: this will return the dg node type for an object, like maya.cmds.nodeType,
    NOT the pymel PyNode class.  For objects like components or attributes,
    nodeType will return the dg type of the node to which the PyNode is attached.
    
    :rtype: `unicode`
    """
    # still don't know how to do inherited via _api
    if kwargs.get( 'inherited', kwargs.get( 'i', False) ):
        return cmds.nodeType( unicode(node), **kwargs )

     
    obj = None
    objName = None

    import nodetypes
    
    if isinstance(node, nodetypes.DependNode) :
        pass
        #obj = node.__apimobject__()
    elif isinstance(node, Attribute) :
        node = node.plugNode()
#    elif isinstance(node, _api.MObject) :
#        # TODO : convert MObject attributes to DependNode
#        if _api.isValidMObjectHandle(_api.MObjectHandle(node)) :
#            obj = node
#        else :
#            obj = None
    else:
    #if isinstance(node,basestring) :
        #obj = _api.toMObject( node.split('.')[0] )
        # don't spend the extra time converting to MObject
        return cmds.nodeType( unicode(node), **kwargs )
        #raise TypeError, "Invalid input %r." % node
        
    if kwargs.get( 'apiType', kwargs.get( '_api', False) ):
        return node.__apimobject__().apiTypeStr()     
    # default
    try:
        return node.__apimfn__().typeName()
    except RuntimeError: pass
        
def group( *args, **kwargs ):
    """
Modifications
  - if no objects are provided for grouping, the empty flag is automatically set
    """
    if not args and not cmds.ls(sl=1):
        kwargs['empty'] = True
        
    # found an interesting bug. group does not return a unique path, so the following line
    # will error if the passed name is in another group somewhere:
    # Transform( cmds.group( name='foo') )
    # luckily the group command always selects the last created node, so we can just use selected()[0]
    cmds.group( *args, **kwargs)
    return selected()[0]

    #except RuntimeError, msg:
    #    print msg
    #    if msg == 'Not enough objects or values.':
    #        kwargs['empty'] = True
    #        return Transform( cmds.group(**kwargs) )

def duplicate( *args, **kwargs ):
    """
Modifications:
  - new option: addShape
        If addShape evaluates to True, then all arguments fed in must be shapes, and each will be duplicated and added under
        the existing parent transform, instead of duplicating the parent transform.
        The following arguments are incompatible with addShape, and will raise a ValueError if enabled along with addShape:
            renameChildren (rc), instanceLeaf (ilf), parentOnly (po), smartTransform (st)
  - returns wrapped classes
  - returnRootsOnly is forced on. This is because the duplicate command does not use full paths when returning
    the names of duplicated objects and will fail if the name is not unique. Rather than return a mixed list of PyNodes and
    strings, I thought it best to give more predictable results.
    """
    addShape = kwargs.pop('addShape', False)
    kwargs['returnRootsOnly'] = True
    kwargs.pop('rr', None)
    
    if not addShape:
        return map(PyNode, cmds.duplicate( *args, **kwargs ) )
    else:
        for invalidArg in ('renameChildren', 'rc', 'instanceLeaf', 'ilf',
                           'parentOnly', 'po', 'smartTransform', 'st'):
            if kwargs.get(invalidArg, False) :
                raise ValueError("duplicate: argument %r may not be used with 'addShape' argument" % invalidArg)
        name=kwargs.pop('name', kwargs.pop('n', None))
                    
        import nodetypes
        
        newShapes = []
        for origShape in [PyNode(x) for x in args]:
            if 'shape' not in cmds.nodeType(origShape.name(), inherited=True):
                raise TypeError('addShape arg of duplicate requires all arguments to be shapes (non-shape arg: %r)'
                                % origShape)

            # This is somewhat complex, because if we have a transform with
            # multiple shapes underneath it,
            #   a) The transform and all shapes are always duplicated
            #   b) After duplication, there is no reliable way to distinguish
            #         which shape is the duplicate of the one we WANTED to
            #         duplicate (cmds.shapeCompare does not work on all types
            #         of shapes - ie, subdivs)
            
            # To get around this, we:
            # 1) duplicate the transform ONLY (result: dupeTransform1)
            # 2) instance the shape we want under the new transform
            #    (result: dupeTransform1|instancedShape)
            # 3) duplicate the new transform
            #    (result: dupeTransform2, dupeTransform2|duplicatedShape)
            # 4) delete the transform with the instance (delete dupeTransform1)
            # 5) place an instance of the duplicated shape under the original
            #    transform (result: originalTransform|duplicatedShape)
            # 6) delete the extra transform (delete dupeTransform2)
            # 7) rename the final shape (if requested)
            
            # 1) duplicate the transform ONLY (result: dupeTransform1)
            dupeTransform1 = duplicate(origShape, parentOnly=1)[0]

            # 2) instance the shape we want under the new transform
            #    (result: dupeTransform1|instancedShape)
            cmds.parent(origShape, dupeTransform1, shape=True, addObject=True,
                        relative=True)
            
            # 3) duplicate the new transform
            #    (result: dupeTransform2, dupeTransform2|duplicatedShape)
            dupeTransform2 = duplicate(dupeTransform1, **kwargs)[0]

            # 4) delete the transform with the instance (delete dupeTransform1)
            delete(dupeTransform1)

            # 5) place an instance of the duplicated shape under the original
            #    transform (result: originalTransform|duplicatedShape)
            newShape = PyNode(cmds.parent(dupeTransform2.getShape(),
                                     origShape.getParent(),
                                     shape=True, addObject=True,
                                     relative=True)[0])

            # 6) delete the extra transform (delete dupeTransform2)
            delete(dupeTransform2)
            
            # 7) rename the final shape (if requested)
            if name is not None:
                newShape.rename(name)
            
            newShapes.append(newShape)
        select(newShapes, r=1)
        return newShapes
    
def instance( *args, **kwargs ):
    """
Modifications:
  - returns wrapped classes
    """
    return map(PyNode, cmds.instance( *args, **kwargs ) )    

'''        
def attributeInfo( *args, **kwargs ):
    """
Modifications:
  - returns an empty list when the result is None
  - returns wrapped classes
    """
    
    return map(PyNode, util.listForNone(cmds.attributeInfo(*args, **kwargs)))
'''

def rename( obj, newname, **kwargs):
    """
Modifications:
    - if the full path to an object is passed as the new name, the shortname of the object will automatically be used
    """
    import nodetypes, other
    # added catch to use object name explicitly when object is a Pymel Node
    if isinstance( newname, nodetypes.DagNode ):
        newname = newname.nodeName()
    else:
        newname = other.DagNodeName(newname).nodeName()
           
    return PyNode( cmds.rename( obj, newname, **kwargs ) )
    
def createNode( *args, **kwargs):
    res = cmds.createNode( *args, **kwargs )
    # createNode can sometimes return None, if the shared=True and name= an object that already exists
    if res:
        return PyNode(res)
            
                
def sets( *args, **kwargs):
    """
Modifications
  - resolved confusing syntax: operating set is always the first and only arg:
    
        >>> from pymel.all import *
        >>> f=newFile(f=1) #start clean
        >>> 
        >>> shdr, sg = createSurfaceShader( 'blinn' )
        >>> shdr
        Blinn(u'blinn1')
        >>> sg
        ShadingEngine(u'blinn1SG')
        >>> s,h = polySphere()
        >>> s
        Transform(u'pSphere1')
        >>> sets( sg, forceElement=s ) # add the sphere
        ShadingEngine(u'blinn1SG')
        >>> sets( sg, q=1)  # check members
        [Mesh(u'pSphereShape1')]
        >>> sets( sg, remove=s )
        ShadingEngine(u'blinn1SG')
        >>> sets( sg, q=1)
        []
    
  - returns wrapped classes
        
    """
    setSetFlags = [
    'subtract', 'sub',
    'union', 'un',
    'intersection', 'int',    
    'isIntersecting', 'ii',
    'isMember', 'im',    
    'split', 'sp',    
    'noWarnings', 'nw',    
    'addElement', 'add',
    'include', 'in',
    'remove', 'rm',    
    'forceElement', 'fe'
    ]
    setFlags = [
    'copy', 'cp',        
    'clear', 'cl',
    'flatten', 'fl'
    ]
    
    #args = (objectSet,)
    
    #     this:
    #        sets('myShadingGroup', forceElement=1)
    #    must be converted to:
    #        sets(forceElement='myShadingGroup')
    
    
    for flag, value in kwargs.items():    
        if flag in setSetFlags:
            kwargs[flag] = args[0]
            
            # move arg over to kwarg
            if util.isIterable(value):
                args = tuple(value)
            elif isinstance( value, (basestring,PyNode) ):
                args = (value,)
            else:
                args = ()
            break
        elif flag in setFlags:
            kwargs[flag] = args[0]
            args = ()
            break
    
    
#    # the case where we need to return a list of objects       
#    if kwargs.get( 'query', kwargs.get('q',False) ):
#        size = len(kwargs)
#        if size == 1 or (size==2 and kwargs.get( 'nodesOnly', kwargs.get('no',False) )  ) :
#            return map( PyNode, util.listForNone(cmds.sets( *args, **kwargs )) )

    # Just get the result, then check if it's a list, rather than trying to
    # parse the kwargs...
    result = cmds.sets( *args, **kwargs )
    if isinstance(result, (bool, int, long, float)):
        return result
    if util.isIterable(result):
        return map( PyNode, util.listForNone(result) )
    elif result is None:
        return []
    else:
        return PyNode(result)
    
    '''
    #try:
    #    elements = elements[0]
    #except:
    #    pass
    
    #print elements
    if kwargs.get('query', kwargs.get( 'q', False)):
        #print "query", kwargs, len(kwargs)
        if len(kwargs) == 1:
            # list of elements
            
            return set( cmds.sets( elements, **kwargs ) or [] )
        # other query
        return cmds.sets( elements, **kwargs )
        
    elif kwargs.get('clear', kwargs.get( 'cl', False)):        
        return cmds.sets( **kwargs )
    
    
    #if isinstance(elements,basestring) and cmds.ls( elements, sets=True):
    #    elements = cmds.sets( elements, q=True )
    
    #print elements, kwargs    
    nonCreationArgs = set([
                'edit', 'e',
                'isIntersecting', 'ii',
                'isMember', 'im',
                'subtract', 'sub',
                'union', 'un',
                'intersection', 'int'])
    if len( nonCreationArgs.intersection( kwargs.keys()) ):
        #print "creation"
        return cmds.sets( *elements, **kwargs )

    # Creation
    #args = _convertListArgs(args)
    #print "creation"
    return ObjectSet(cmds.sets( *elements, **kwargs ))
    '''

def delete(*args, **kwargs):
    """
Modifications:
  - the command will not fail on an empty list
    """
    #if kwargs.pop('safe',False):
        # empty list
    if len(args) ==1 and util.isIterable(args[0]) and not args[0]:
        return
    
    cmds.delete(*args, **kwargs)

  
        
def getClassification( *args ):
    """
Modifications:
  - previously returned a list with a single colon-separated string of classifications. now returns a list of classifications
    
    :rtype: `unicode` list
    """
    return cmds.getClassification(*args)[0].split(':')
    

#--------------------------
# New Commands
#--------------------------



def selected( **kwargs ):
    """ls -sl"""
    kwargs['sl'] = 1
    return ls( **kwargs )


_thisModule = sys.modules[__name__]
                                
#def spaceLocator(*args, **kwargs):
#    """
#Modifications:
#    - returns a locator instead of a list with a single locator
#    """
#    res = cmds.spaceLocator(**kwargs)
#    try:
#        return Transform(res[0])
#    except:
#        return res
    
def instancer(*args, **kwargs):
    """
Maya Bug Fix:
    - name of newly created instancer was not returned
    """ 
    # instancer does not like PyNode objects
    args = map( unicode, args )   
    if kwargs.get('query', kwargs.get('q',False)):
        return cmds.instancer(*args, **kwargs)
    if kwargs.get('edit', kwargs.get('e',False)):
        cmds.instancer(*args, **kwargs)
        return PyNode( args[0], 'instancer' )
    else:
        instancers = cmds.ls(type='instancer')
        cmds.instancer(*args, **kwargs)
        return PyNode( list( set(cmds.ls(type='instancer')).difference( instancers ) )[0], 'instancer' )

#--------------------------
# PyNode Exceptions
#--------------------------
class MayaObjectError(TypeError):
    _objectDescription = 'Object'
    def __init__(self, node=None):
        self.node = unicode(node)
    def __str__(self):
        msg = "Maya %s does not exist" % (self._objectDescription)
        if self.node:
            msg += ": %r" % (self.node)
        return msg

class MayaNodeError(MayaObjectError):
    _objectDescription = 'Node'

class MayaSubObjectError(MayaObjectError, AttributeError):
    _objectDescription = 'Attribute or Component'
    
class MayaAttributeError(MayaSubObjectError):
    _objectDescription = 'Attribute'
    
class MayaComponentError(MayaSubObjectError):
    _objectDescription = 'Component'

def _objectError(objectName):
    # TODO: better name parsing
    if '.' in objectName:
        return MayaSubObjectError(objectName)
    return MayaNodeError(objectName)

#--------------------------
# Object Wrapper Classes
#--------------------------

class PyNode(util.ProxyUnicode):
    """
    Abstract class that is base for all pymel nodes classes.
 
    The names of nodes and attributes can be passed to this class, and the appropriate subclass will be determined.
    
        >>> PyNode('persp')
        Transform(u'persp')
        >>> PyNode('persp.tx')
        Attribute(u'persp.translateX')
        
    If the passed node or attribute does not exist an error will be raised.
    
    """
        
    _name = None              # unicode
    
    # for DependNode : _api.MObjectHandle
    # for DagNode    : _api.MDagPath
    # for Attribute  : _api.MPlug
                              
    _node = None              # Attribute Only: stores the PyNode for the plug's node
    __apiobjects__ = {}
    def __new__(cls, *args, **kwargs):
        """ Catch all creation for PyNode classes, creates correct class depending on type passed.
        
        
        For nodes:
            MObject
            MObjectHandle
            MDagPath
            string/unicode
            
        For attributes:
            MPlug
            MDagPath, MPlug
            string/unicode
        """
        import nodetypes
        #print cls.__name__, cls
        
        pymelType = None
        obj = None
        name = None
        attrNode = None
        argObj = None
        if args :
            

            if len(args)>1 :
                # Attribute passed as two args: ( node, attr )
                # valid types:
                #    node : MObject, MObjectHandle, MDagPath
                #    attr : MPlug  (TODO: MObject and MObjectHandle )
                # One very important reason for allowing an attribute to be specified as two args instead of as an MPlug
                # is that the node can be represented as an MDagPath which will differentiate between instances, whereas
                # an MPlug loses this distinction.
                
                attrNode = args[0]
                argObj = args[1]
                
                #-- First Argument: Node
                # ensure that the node object is a PyNode object
                if not isinstance( attrNode, nodetypes.DependNode ):
                    attrNode = PyNode( attrNode )
                
#                #-- Second Argument: Plug or Component
#                # convert from string to _api objects.
#                if isinstance(argObj,basestring) :
#                    argObj = _api.toApiObject( argObj, dagPlugs=False )
#                    
#                # components
#                elif isinstance( argObj, int ) or isinstance( argObj, slice ):
#                    argObj = attrNode._apiobject

                
            else:
                argObj = args[0]
                
                # the order of the following 3 checks is important, as it is in increasing generality
                
                if isinstance( argObj, Attribute ):
                    attrNode = argObj._node
                    argObj = argObj.__apiobjects__['MPlug']
                elif isinstance( argObj, nodetypes.Component ):
                    try:
                        argObj = argObj._node.__apiobjects__[ 'MDagPath']
                    except KeyError:
                        argObj = argObj._node.__apiobjects__['MObjectHandle'] 
                        
                elif isinstance( argObj, PyNode ):
                    try:
                        argObj = argObj.__apiobjects__[ 'MDagPath']
                    except KeyError:
                        argObj = argObj.__apiobjects__['MObjectHandle'] 
                        
                elif hasattr( argObj, '__module__') and argObj.__module__.startswith( 'maya.OpenMaya' ) :
                    pass
                
                #elif isinstance(argObj,basestring) : # got rid of this check because of nameparse objects
                else:
                    # didn't match any known types. treat as a string
                    # convert to string then to _api objects.
                    try:
                        name = unicode(argObj)
                    except:
                        raise MayaNodeError
                    else:
                        res = _api.toApiObject( name, dagPlugs=True )
                        # DagNode Plug
                        if isinstance(res, tuple):
                            # Plug or Component
                            #print "PLUG or COMPONENT", res
                            attrNode = PyNode(res[0])
                            argObj = res[1]
                        # DependNode Plug
                        elif isinstance(res,_api.MPlug):
                            attrNode = PyNode(res.node())
                            argObj = res
                        # Other Object
                        elif res:
                            argObj = res
                        else:
                            # Removed ability to create components such as
                            #   PyNode('myCube.vtx')
                            # because of inconsistency - in general, for
                            #   PyNode(stringName)
                            # stringName should be a valid mel name, ie
                            #   cmds.select(stringName)
                            # should work
                            
#                            # Check if it's a component that's normally indexed,
#                            # but has no index specified - ie, myPoly.vtx,
#                            # instead of the (mel-valid) myPoly.vtx[*]
#                            dotSplit = name.split('.')
#                            if len(dotSplit) == 2:
#                                try:
#                                    res = PyNode(dotSplit[0])
#                                except MayaObjectError:
#                                    pass
#                                else:
#                                    try:
#                                        argObj = getattr(res, dotSplit[1])
#                                    except AttributeError:
#                                        pass
#                                    else:
#                                        if isinstance(argObj, cls):
#                                            return argObj
                            
                            # non-existent objects
                            # the object doesn't exist: raise an error
                            raise _objectError( name )


            #-- Components
            if nodetypes.validComponentIndexType(argObj):
                #pymelType, obj, name = _getPymelType( attrNode._apiobject )
                obj = {'ComponentIndex' : argObj }
                # if we are creating a component class using an int or slice, then we must specify a class type:
                #    valid:    MeshEdge( myNode, 2 )
                #    invalid:  PyNode( myNode, 2 )
                assert issubclass(cls,nodetypes.Component), "%s is not a Component class" % cls.__name__
                
            #-- All Others
            else:
                pymelType, obj = _getPymelType( argObj, name )
            #print pymelType, obj, name, attrNode
            
            # Virtual (non-existent) objects will be cast to their own virtual type.
            # so, until we make that, we're rejecting them
            assert obj is not None# real objects only
            #assert obj or name
            
        else :
            # create node if possible
            if issubclass(cls,nodetypes.DependNode):
                newNode = None
                #----------------------------------
                # Pre Creation
                #----------------------------------
                if hasattr( cls, '_preCreateVirtual' ):
                    newkwargs = cls._preCreateVirtual(**kwargs)
                    assert isinstance(newkwargs, dict), "_preCreateVirtual must return a dictionary of keyword arguments"
                    kwargs = newkwargs
                    
                #----------------------------------
                # Creation
                #----------------------------------
                if hasattr( cls, '_createVirtual' ):
                    newNode = cls.createVirtual(**kwargs)
                    assert isinstance(newNode, basestring), "_createVirtual must return the name created node"
#                elif cls in _factories.virtualClassCreation:
#                    res = _factories.virtualClassCreation[cls](**kwargs)
#                    if res is None:
#                        raise TypeError, "the creation callback of a virtual node must return the created node"
#                    return cls(res)
                
                elif hasattr(cls, '__melcmd__') and not cls.__melcmd_isinfo__:
                    try:
                        _logger.debug( 'creating node of type %s using %s' % (cls.__melnode__, cls.__melcmd__.__name__ ) ) 
                        res = cls.__melcmd__(**kwargs)
                    except Exception, e:
                        _logger.debug( 'failed to create %s' % e )
                        pass
                    else:
                        if isinstance(res,list):
                            # we only want to return a single object
                            for x in res:
                                typ = cmds.nodeType(x)
                                if typ == cls.__melnode__:
                                    newNode = x
                                    break
                                elif typ == 'transform':
                                    shape = cmds.listRelatives( x, s=1)
                                    if shape and cmds.nodeType(shape[0]) == cls.__melnode__:
                                        newNode = shape[0]
                                        break
                            if newNode is None:       
                                raise ValueError, "could not find type %s in result %s returned by %s" % ( cls.__name__, res, cls.__melcmd__.__name__ )
                        elif cls.__melnode__ == nodeType(res): #isinstance(res,cls):
                            newNode = res
                        else:
                            raise ValueError, "unexpect result %s returned by %s" % ( res, cls.__melcmd__.__name__ )
                else:
                    _logger.debug( 'creating node of type %s using createNode' % cls.__melnode__ )
                    try:
                        newNode = createNode( cls.__melnode__, **kwargs )
                    except RuntimeError:
                        # FIXME: should we really be passing on this?
                        pass
                
                #----------------------------------
                # Post Creation
                #----------------------------------
                if newNode:
                    if hasattr( cls, '_postCreateVirtual' ):
                        cls._postCreateVirtual( newNode )
                    return cls(newNode)
                    
            raise ValueError, 'PyNode expects at least one argument: an object name, MObject, MObjectHandle, MDagPath, or MPlug'
        
        # print "type:", pymelType
        # print "PyNode __new__ : called with obj=%r, cls=%r, on object of type %s" % (obj, cls, pymelType)
        # if an explicit class was given (ie: pyObj=DagNode(u'pCube1')) just check if actual type is compatible
        # if none was given (ie generic pyObj=PyNode('pCube1')) then use the class corresponding to the type we found
        newcls = None
            
        if cls is not PyNode :
            # a PyNode class was explicitly required, if an existing object was passed to init check that the object type
            # is compatible with the required class, if no existing object was passed, create an empty PyNode of the required class
            # There is one exception type:  MeshVertex( Mesh( 'pSphere1') )
            # TODO : can add object creation option in the __init__ if desired
            
            if not pymelType or not issubclass( pymelType, cls ):
                if issubclass( cls, nodetypes.Component ):
                    newcls = cls
                else:
                    raise TypeError, "Determined type is %s, which is not a subclass of desired type %s" % ( pymelType.__name__, cls.__name__ )
            else:
                newcls = pymelType
        else :
            newcls = pymelType
   
        if newcls :  
            self = super(PyNode, cls).__new__(newcls)
            self._name = name
            if attrNode:
                #print 'ATTR', attr, obj, pymelType
                self._node = attrNode
            
            self.__apiobjects__ = obj
            return self
        else :
            raise TypeError, "Cannot make a %s out of a %r object" % (cls.__name__, pymelType)   

    def __init__(self, *args, **kwargs):
        # this  prevents the _api class which is the second base, from being automatically instantiated. This __init__ should
        # be overridden on subclasses of PyNode
        pass
 
                         
                          
    def __melobject__(self):
        """Special method for returning a mel-friendly representation. """
        return self.name()
    
    def __apimfn__(self):
        try:
            # if we have it, use it
            return self.__apiobjects__['MFn']
        except KeyError:          
            if self.__apicls__:
                # use whatever type is appropriate
                obj = self.__apiobject__()
                if obj:
                    try:
                        mfn = self.__apicls__(obj)
                        self.__apiobjects__['MFn'] = mfn
                        
                    except RuntimeError:
                        # when using PyNodes in strange places, like node creation callbacks, the proper MFn does not work yet, so we default to
                        # a super class and we don't save it, so that we can get the right one later
                        if isinstance(obj, _api.MDagPath):
                            mfn = _api.MFnDagNode( obj )
                            _logger.warning( "Could not create desired MFn. Defaulting to MFnDagNode." )
                            
                        elif isinstance(obj, _api.MObject):
                            mfn = _api.MFnDependencyNode( obj ) 
                            _logger.warning( "Could not create desired MFn. Defaulting to MFnDependencyNode." )
                        else:
                            raise
                    return mfn  
    def __repr__(self):
        """
        :rtype: `unicode`
        """
        return u"%s(%r)" % (self.__class__.__name__, self.name())

    def __radd__(self, other):
        if isinstance(other, basestring):
            return other.__add__( self.name() )
        else:
            raise TypeError, "cannot concatenate '%s' and '%s' objects" % ( other.__class__.__name__, self.__class__.__name__)

    def __reduce__(self):
        """allows PyNodes to be pickled"""
        return (PyNode, (self.name(),) )
    
    def __eq__(self, other):
        """
        :rtype: `bool`
        """
        if isinstance(other,PyNode):
            try:
                apiobj = other.__apiobject__()
            except TypeError: # intermixing MDagPath with MObject
                return False
        else:
            try:
                apiobj = PyNode(other).__apiobject__()
            except:
                return False
        
        try:
            return self.__apiobject__() == apiobj
        except: 
            return False
       
    def __ne__(self, other):
        """
        :rtype: `bool`
        """
        # != does not work for MDagPath (maybe others) iff MDagPaths are equal (returns True)
        return not self == other


    def __nonzero__(self):
        """
        :rtype: `bool`
        """
        return self.exists()

    def __lt__(self, other):
        if isinstance(other, (basestring,PyNode) ):
            return self.name().__lt__( unicode(other) )
        else:
            return NotImplemented
        
    def __gt__(self, other):
        if isinstance(other, (basestring,PyNode) ):
            return self.name().__gt__( unicode(other) )
        else:
            return NotImplemented
        
    def __le__(self, other):
        if isinstance(other, (basestring,PyNode) ):
            return self.name().__le__( unicode(other) )
        else:
            return NotImplemented
        
    def __ge__(self, other):
        if isinstance(other, (basestring,PyNode) ):
            return self.name().__ge__( unicode(other) )
        else:
            return NotImplemented
    #-----------------------------------------
    # Name Info and Manipulation
    #-----------------------------------------
    
    def stripNamespace(self, levels=0):
        """
        Returns the object's name with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.
        
        :rtype: `other.NameParser`
        
        """
        import other
        nodes = []
        for x in self.split('|'):
            y = x.split('.')
            z = y[0].split(':')
            if levels:
                y[0] = ':'.join( z[min(len(z)-1,levels):] )
    
            else:
                y[0] = z[-1]
            nodes.append( '.'.join( y ) )
        return other.NameParser( '|'.join( nodes) )

    def swapNamespace(self, prefix):
        """Returns the object's name with its current namespace replaced with the provided one.  
        The calling instance is unaffected.
        
        :rtype: `other.NameParser`
        """    
        return self.stripNamespace().addPrefix( prefix+':' )
            
    def namespaceList(self):
        """Useful for cascading references.  Returns all of the namespaces of the calling object as a list
        
        :rtype: `unicode` list
        """
        return self.lstrip('|').rstrip('|').split('|')[-1].split(':')[:-1]
            
    def namespace(self):
        """Returns the namespace of the object with trailing colon included.  See `DependNode.parentNamespace` for 
        a variant which does not include the trailing colon.
        
        :rtype: `unicode`
        
        """
        ns = self.parentNamespace()
        if ns:
            ns += ':'
        return ns
        
    def addPrefix(self, prefix):
        """Returns the object's name with a prefix added to the beginning of the name
        
        :rtype: `other.NameParser`
        """
        import other
        name = self
        leadingSlash = False
        if name.startswith('|'):
            name = name[1:]
            leadingSlash = True
        name =  '|'.join( map( lambda x: prefix+x, name.split('|') ) ) 
        if leadingSlash:
            name = '|' + name
        return other.NameParser(name) 
                


                        
#    def attr(self, attr):
#        """access to attribute of a node. returns an instance of the Attribute class for the 
#        given attribute."""
#        return Attribute( '%s.%s' % (self, attr) )

    def exists(self, **kwargs):
        "objExists"
        try:
            if self.__apiobject__() :
                return True
        except MayaObjectError:
            pass
        return False
                 
    objExists = exists
        
    nodeType = cmds.nodeType

    def select(self, **kwargs):
        forbiddenKeys = ['all', 'allDependencyNodes', 'adn', 'allDagObjects' 'ado', 'clear', 'cl']
        for key in forbiddenKeys:
            if key in kwargs:
                raise TypeError, "'%s' is an inappropriate keyword argument for object-oriented implementation of this command" % key
        # stringify
        return cmds.select( self.name(), **kwargs )    

    def deselect( self ):
        self.select( deselect=1 )
    
    listConnections = listConnections
        
    connections = listConnections

    listHistory = listHistory
        
    history = listHistory

    listFuture = listFuture
                
    future = listFuture

                         
_factories.pyNodeNamesToPyNodes['PyNode'] = PyNode

#def _MObjectIn(x):
#    if isinstance(x,PyNode): return x.__apimobject__()
#    return PyNode(x).__apimobject__()
#def _MDagPathIn(x):
#    if isinstance(x,DagNode): return x.__apimdagpath__()
#    return PyNode(x).__apimdagpath__()
#def _MPlugIn(x):
#    if isinstance(x,Attribute): return x.__apimplug__()
#    return PyNode(x).__apimplug__()
#def _MPlugOut(self,x):
#    try: return Attribute(self.node(), x)
#    except: pass
#    return Attribute(x)
#_factories.ApiTypeRegister.register('MObject', PyNode, inCast=_MObjectIn )
#_factories.ApiTypeRegister.register('MDagPath', DagNode, inCast=_MDagPathIn )
#_factories.ApiTypeRegister.register('MPlug', Attribute, inCast=_MPlugIn, outCast=_MPlugOut )


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
              
class Attribute(PyNode):
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
    __metaclass__ = _factories.MetaMayaTypeWrapper
    __apicls__ = _api.MPlug
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
            handle = _api.MObjectHandle( self.__apiobjects__['MPlug'].attribute() )
            self.__apiobjects__['MObjectHandle'] = handle
        if _api.isValidMObjectHandle( handle ):
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
#        assert isinstance( _api.__apiobject__(), _api.MPlug )
        
#        if '.' not in attrName:
#            raise TypeError, "%s: Attributes must include the node and the attribute. e.g. 'nodeName.attributeName' " % self
#        self._name = attrName
#        # TODO : MObject support
#        self.__dict__['_multiattrIndex'] = 0
#        

    __getitem__ = _factories.wrapApiMethod( _api.MPlug, 'elementByLogicalIndex', '__getitem__' )
    #elementByPhysicalIndex = _factories.wrapApiMethod( _api.MPlug, 'elementByPhysicalIndex' )
    
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
        
            >>> from pymel.all import *
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
                other = PyNode(other)
                if not hasattr(other, '__apimplug__'):
                    return False
            except (ValueError,TypeError): # could not cast to PyNode
                return False
            
        otherPlug = other.__apimplug__()
        # foo.bar[10] and foo.bar[20] and foo.bar eval to the same object in _api.  i don't think this is very intuitive.
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
                import nodetypes
                if isinstance(node, nodetypes.DagNode):
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
                
    item = _factories.wrapApiMethod( _api.MPlug, 'logicalIndex', 'item' )
    index = _factories.wrapApiMethod( _api.MPlug, 'logicalIndex', 'index' )
    
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
    

    connect = connectAttr
        
    def __rshift__(self, other):
        """
        operator for 'connectAttr'
        
            >>> from pymel.all import *
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """ 
        return connectAttr( self, other, force=True )
                
    disconnect = disconnectAttr
    
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
    
    @_factories.addMelDocs( 'setKeyframe' )    
    def setKey(self, **kwargs):
        kwargs.pop( 'attribute', None )
        kwargs.pop( 'at', None )
        return cmds.setKeyframe( self, **kwargs )
#}
#----------------------
#xxx{ Info and Modification
#----------------------
    
    def getAlias(self, **kwargs):
        """
        Returns the alias for this attribute, or None.
        
        The alias of the attribute is set through
        Attribute.setAlias, or the aliasAttr command. 
        """
        alias = self.node().__apimfn__().plugsAlias(self.__apimplug__())
        if alias:
            return alias
        else:
            return None
        
    def setAlias(self, alias):
        """
        Sets the alias for this attribute (similar to aliasAttr).
        """
        cmds.aliasAttr(alias, self.name())
                            
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

    
    isMulti = _factories.wrapApiMethod( _api.MPlug, 'isArray', 'isMulti' )

    
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
            return bool(indices and self.index() in indices)
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
#            _util.listForNone( cmds.attributeQuery(self.lastPlugAttr(), node=self.node(), listChildren=True) )
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

def _MObjectIn(x):
    if isinstance(x,PyNode): return x.__apimobject__()
    return PyNode(x).__apimobject__()
def _MDagPathIn(x):
    if isinstance(x,PyNode): return x.__apimdagpath__()
    return PyNode(x).__apimdagpath__()
def _MPlugIn(x):
    if isinstance(x,PyNode): return x.__apimplug__()
    return PyNode(x).__apimplug__()
def _MPlugOut(self,x):
    return PyNode(self.node(), x)
    #try: return PyNode(self.node(), x)
    #except: pass
    #return PyNode(x)
_factories.ApiTypeRegister.register('MObject', PyNode, inCast=_MObjectIn )
_factories.ApiTypeRegister.register('MDagPath', PyNode, inCast=_MDagPathIn )
_factories.ApiTypeRegister.register('MPlug', PyNode, inCast=_MPlugIn, outCast=_MPlugOut )
                   
#from animation import listAnimatable as _listAnimatable

#-----------------------------------------------
#  Global Settings
#-----------------------------------------------


#-----------------------------------------------
#  Scene Class
#-----------------------------------------------

class Scene(object):
    """
    The Scene class provides an attribute-based method for retrieving `PyNode` instances of
    nodes in the current scene.
    
        >>> SCENE = Scene()
        >>> SCENE.persp
        Transform(u'persp')
        >>> SCENE.persp.t
        Attribute(u'persp.translate')
    
    An instance of this class is provided for you with the name `SCENE`. 
    """
    __metaclass__ = util.Singleton
    def __getattr__(self, obj):
        if obj.startswith('__') and obj.endswith('__'):
            try:
                return self.__dict__[obj]
            except KeyError, err:
                raise AttributeError, "type object %r has no attribute %r" % (self.__class__.__name__, obj)
                
        return PyNode( obj )

SCENE = Scene()






_factories.createFunctions( __name__, PyNode )

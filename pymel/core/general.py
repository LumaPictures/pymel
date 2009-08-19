"""
Contains general node and attribute functions, as well as the main `PyNode` base class. 

For the rest of the class hierarchy, including `DependNode <pymel.core.nodetypes.DependNode>`, `Transform <pymel.core.nodetypes.Transform>`, 
and `Attribute <pymel.core.nodetypes.Attribute>`, see :mod:`pymel.core.nodetypes`.


"""


import sys, os, re
from getpass import getuser
from socket import gethostname

import pmcmds as cmds
#import maya.cmds as cmds
import maya.mel as mm

import inspect, timeit, time

import pymel.util as util
import factories as _factories

import pymel.api as api
import datatypes
import pymel.util.nameparse as nameparse
import pymel.mayahook.pwarnings as pwarnings
import logging
_logger = logging.getLogger(__name__)

# to make sure Maya is up
import pymel.mayahook as mayahook

from maya.cmds import about as _about

# TODO: factories.functionFactory should automatically handle conversion of output to PyNodes...
#       ...so we shouldn't always have to do it here as well?

#-----------------------------------------------
#  Enhanced Commands
#-----------------------------------------------

# TODO: possible bugfix for 'parent'?
# Docs state 'If there is only a single object specified then the selected objects are parented to that object. '
# ...but actual behavior is to parent the named object (and any other selected objects) to the last selected object

def about(**kwargs):
    """
Modifications:
    - added apiVersion/api flag to about command for version 8.5 and 8.5sp1
    """
    if kwargs.get('apiVersion', kwargs.get('api',False)):
        try:
            return _about(api=1)
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
    - maya pointlessly returned vector results as a tuple wrapped in 
        a list ( ex.  '[(1,2,3)]' ). This command unpacks the vector for you.
Modifications:
    - casts double3 datatypes to `Vector`
    - casts matrix datatypes to `Matrix`
    - casts vectorArrays from a flat array of floats to an array of Vectors
    - when getting a multi-attr, maya would raise an error, but pymel will return a list of
         values for the multi-attr
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
                res = res[0]
                if cmds.getAttr( attr, type=1) == 'double3':
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
    
    # perhaps it errored because it's a mixed compound, or a multi attribute
    except RuntimeError, e:
        try:
            import nodetypes
            attr = nodetypes.Attribute(attr)
            # mixed compound takes precedence, because by default, compound attributes are returned by getAttr, but
            # mixed compounds cannot be expressed in a mel array.
            if attr.isCompound():
                return [child.get() for child in attr.getChildren() ]
            elif attr.isMulti():
                return [attr[i].get() for i in range(attr.size())]
            raise e
        except AttributeError, e:
            if default is not None:
                return default
            else:
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
            - float     S{->} double
            - int        S{->} long
            - str        S{->} string
            - bool        S{->} bool
            - Vector    S{->} double3
            - Matrix    S{->} matrix
            - [str]        S{->} stringArray
     
           
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
                    attrName = nameparse.parse( attr )
                    assert attrName.isAttributeName(), "passed object is not an attribute"
                    try:
                        if isinstance( arg[0], (basestring, util.ProxyUnicode ) ):
                            datatype = 'stringArray'
                        elif isinstance( arg[0], (list,datatypes.Vector) ):
                            datatype = 'vectorArray'
                        elif isinstance( arg, datatypes.Vector):
                            datatype = 'double3'
                        elif isinstance( arg,  datatypes.Matrix ):
                            datatype = 'matrix'
                        elif isinstance( arg[0], int ):
                            datatype = 'Int32Array'
                        elif isinstance( arg[0], float ):
                            datatype = 'doubleArray'
                            if len(arg)==3:
                                pwarnings.warn(AmbiguityWarning(
                                    "The supplied value will be interperted as a 'doubleArray' and not as a 'double3' (vector). "
                                    "Supply an explicit 'datatype' argument to avoid this warning."
                                    ))
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
                            #print "Getting datatype", attr
                            datatype = addAttr( attr, q=1, dataType=1) #[0] # this is returned as a single element list
                    
                        # set datatype for arrays
                        # we could do this for all, but i'm uncertain that it needs to be 
                        # done and it might cause more problems
                        if datatype.endswith('Array'):
                            kwargs['type'] = datatype
            
            # string arrays:
            #    first arg must be the length of the array being set
            # ex:
            #     setAttr('loc.strArray',["first", "second", "third"] )    
            # becomes:
            #     cmds.setAttr('loc.strArray',3,"first", "second", "third",type='stringArray')
            if datatype == 'stringArray':
                args = tuple( [len(arg)] + arg )
            
            # vector arrays:
            #    first arg must be the length of the array being set
            #    empty values are placed between vectors
            # ex:
            #     setAttr('loc.vecArray',[1,2,3],[4,5,6],[7,8,9] )    
            # becomes:
            #     cmds.setAttr('loc.vecArray',3,[1,2,3],"",[4,5,6],"",[7,8,9],type='vectorArray')
            elif datatype == 'vectorArray':            
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

            # others: 
            #    args must be expanded
            # ex:
            #     setAttr('loc.foo',[1,2,3] )    
            # becomes:
            #     cmds.setAttr('loc.foo',1,2,3 )    
            else:
                args = tuple(arg)
                
        # non-iterable types
        else:
            if datatype is None:
                #attr = Attribute(attr)    
                if force and not cmds.objExists(attr): #attr.exists(): 
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
        mm.eval(cmd)
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
    - ...and an 'exactType' filter (if both are present, 'type' is ignored)
    
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
    - ...and an 'exactType' filter (if both are present, 'type' is ignored)
    
    :rtype: `DependNode` list
    
    """
    kwargs['future'] = True
    
    return listHistory(*args, **kwargs)

        
def listRelatives( *args, **kwargs ):
    """
Maya Bug Fix
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
    
    :rtype: `PyNode` list
    """

    kwargs['long'] = True
    kwargs.pop('l', None)
    
    if kwargs.pop('editable', False):
        allNodes = util.listForNone(cmds.ls(*args, **kwargs))
        kwargs['readOnly'] = True
        kwargs.pop('ro',True)
        roNodes = util.listForNone(cmds.ls(*args, **kwargs))
        
        # faster way?
        return map( PyNode, filter( lambda x: x not in roNodes, allNodes ) )
    
    # this has been removed because the method below
    # is 3x faster because it gets the pymel.core.node type along with the pymel.core.node list
    # unfortunately, it's still about 2x slower than cmds.ls
    #return map(PyNode, util.listForNone(cmds.ls(*args, **kwargs)))
    
    if kwargs.get( 'readOnly', kwargs.get('ro', False) ):
        # when readOnly is provided showType is ignored
        return map(PyNode, util.listForNone(cmds.ls(*args, **kwargs)))
        
    if kwargs.get( 'showType', kwargs.get('st', False) ):
        tmp = util.listForNone(cmds.ls(*args, **kwargs))
        res = []
        for i in range(0,len(tmp),2):
            # res.append( PyNode( tmp[i], tmp[i+1] ) )
            res.append( PyNode( tmp[i] ) )
            res.append( tmp[i+1] )
        return res    
    
    if kwargs.get( 'nodeTypes', kwargs.get('nt', False) ):
        # when readOnly is provided showType is ignored
        return cmds.ls(*args, **kwargs)   
    
#    kwargs['showType'] = True
#    tmp = util.listForNone(cmds.ls(*args, **kwargs))
#    res = []
#    for i in range(0,len(tmp),2):
#        res.append( PyNode( tmp[i], tmp[i+1] ) )
#    
#    return res
    return map(PyNode, util.listForNone(cmds.ls(*args, **kwargs)))
    
 
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
    #res = list(set(res)) # ruins the order, but prevents dupes, which can happend when a transform has more than one shape
    return map( PyNode, res ) #, ['transform']*len(res) )


    
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
    # still don't know how to do inherited via api
    if kwargs.get( 'inherited', kwargs.get( 'i', False) ):
        return cmds.nodeType( unicode(node), **kwargs )

     
    obj = None
    objName = None

    import nodetypes
    
    if isinstance(node, nodetypes.DependNode) :
        pass
        #obj = node.__apimobject__()
    elif isinstance(node, nodetypes.Attribute) :
        node = node.plugNode()
#    elif isinstance(node, api.MObject) :
#        # TODO : convert MObject attributes to DependNode
#        if api.isValidMObjectHandle(api.MObjectHandle(node)) :
#            obj = node
#        else :
#            obj = None
    else:
    #if isinstance(node,basestring) :
        #obj = api.toMObject( node.split('.')[0] )
        # don't spend the extra time converting to MObject
        return cmds.nodeType( unicode(node), **kwargs )
        #raise TypeError, "Invalid input %r." % node
        
    if kwargs.get( 'apiType', kwargs.get( 'api', False) ):
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
            parent(origShape, dupeTransform1, shape=True, addObject=True,
                        relative=True)
            
            # 3) duplicate the new transform
            #    (result: dupeTransform2, dupeTransform2|duplicatedShape)
            dupeTransform2 = duplicate(dupeTransform1, **kwargs)[0]

            # 4) delete the transform with the instance (delete dupeTransform1)
            delete(dupeTransform1)

            # 5) place an instance of the duplicated shape under the original
            #    transform (result: originalTransform|duplicatedShape)
            newShape = PyNode(parent(dupeTransform2.getShape(),
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
    
        >>> from pymel import *
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


_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

                                
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
class MayaObjectError(ValueError):
    def __init__(self, node=None):
        self.node = unicode(node)
    def __str__(self):
        if self.node:
            return "Maya Object does not exist: %r" % self.node
        return "Maya Object does not exist"
class MayaNodeError(MayaObjectError):
    def __str__(self):
        if self.node is not None:
            return "Maya Node does not exist: %r" % self.node
        return "Maya Node does not exist"
class MayaAttributeError(MayaObjectError, AttributeError):
    def __str__(self):
        if self.node is not None:
            return "Maya Attribute does not exist: %r" % self.node
        return "Maya Attribute does not exist"

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
    
    # for DependNode : api.MObjectHandle
    # for DagNode    : api.MDagPath
    # for Attribute  : api.MPlug
                              
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
#                # convert from string to api objects.
#                if isinstance(argObj,basestring) :
#                    argObj = api.toApiObject( argObj, dagPlugs=False )
#                    
#                # components
#                elif isinstance( argObj, int ) or isinstance( argObj, slice ):
#                    argObj = attrNode._apiobject

                
            else:
                argObj = args[0]
                
                # the order of the following 3 checks is important, as it is in increasing generality
                
                if isinstance( argObj, nodetypes.Attribute ):
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
                    # convert to string then to api objects.
                    try:
                        name = unicode(argObj)
                    except:
                        raise MayaNodeError
                    else:
                        res = api.toApiObject( name, dagPlugs=True )
                        # DagNode Plug
                        if isinstance(res, tuple):
                            # Plug or Component
                            #print "PLUG or COMPONENT", res
                            attrNode = PyNode(res[0])
                            argObj = res[1]
                        # DependNode Plug
                        elif isinstance(res,api.MPlug):
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
                            if mayahook.pymel_options.get( '0_7_compatibility_mode', False):
                                import other
                                
                                if '.' in name:
                                    newcls = other.AttributeName
                                elif '|' in name:
                                    newcls = other.DagNodeName
                                else:
                                    newcls = other.DependNodeName
                                    
                                self = unicode.__new__(newcls, name)
                                
                                return self  
                            else:
                                # the object doesn't exist: raise an error
                                if '.' in name:
                                    raise MayaAttributeError( name )
                                else:
                                    raise MayaNodeError( name )

            #-- Components
            if nodetypes.validComponentIndex(argObj):
                #pymelType, obj, name = _getPymelType( attrNode._apiobject )
                obj = {'ComponentIndex' : argObj }
                # if we are creating a component class using an int or slice, then we must specify a class type:
                #    valid:    MeshEdge( myNode, 2 )
                #    invalid:  PyNode( myNode, 2 )
                assert issubclass(cls,nodetypes.Component), "%s is not a Component class" % cls.__name__
                
            #-- All Others
            else:
                pymelType, obj = nodetypes._getPymelType( argObj, name )
            #print pymelType, obj, name, attrNode
            
            # Virtual (non-existent) objects will be cast to their own virtual type.
            # so, until we make that, we're rejecting them
            assert obj is not None# real objects only
            #assert obj or name
            
        else :
            # create node if possible
            if issubclass(cls,nodetypes.DependNode):
                if hasattr( cls, 'createVirtual' ):
                    res = cls.createVirtual(**kwargs)
                    if res is None:
                        raise TypeError, "createVirtual must return the created node"
                    return cls(res)
                elif cls in _factories.virtualClassCreation:
                    res = _factories.virtualClassCreation[cls](**kwargs)
                    if res is None:
                        raise TypeError, "createVirtual must return the created node"
                    return cls(res)
                
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
                                    return cls(x)
                                elif typ == 'transform':
                                    shape = cmds.listRelatives( x, s=1)
                                    if shape and cmds.nodeType(shape[0]) == cls.__melnode__:
                                        return cls(shape[0])
                                    
                            raise ValueError, "could not find type %s in result %s returned by %s" % ( cls.__name__, res, cls.__melcmd__.__name__ )
                        elif cls.__melnode__ == nodeType(res): #isinstance(res,cls):
                            return cls(res)
                        else:
                            raise ValueError, "unexpect result %s returned by %s" % ( res, cls.__melcmd__.__name__ )
                else:
                    _logger.debug( 'creating node of type %s using createNode' % cls.__melnode__ )
                    try:
                        return createNode( cls.__melnode__, **kwargs )
                    except RuntimeError:
                        pass
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
        # this  prevents the api class which is the second base, from being automatically instantiated. This __init__ should
        # be overridden on subclasses of PyNode
        pass
 
                         
                          
    def __melobject__(self):
        """Special method for returning a mel-friendly representation. """
        #if mayahook.Version.current >= mayahook.Version.v2009:
        #    raise AttributeError
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
                        if isinstance(obj, api.MDagPath):
                            mfn = api.MFnDagNode( obj )
                            _logger.warning( "Could not create desired MFn. Defaulting to MFnDagNode." )
                            
                        elif isinstance(obj, api.MObject):
                            mfn = api.MFnDependencyNode( obj ) 
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

def _deprecatePyNode():
    strDeprecateDecorator = mayahook.deprecated( 'Convert to string first using str() or PyNode.name().', 'PyNode' )
    
    def makeDeprecatedMethod(method):
        def f(self, *args):
            proxyMethod = getattr( util.ProxyUnicode, method )
            return proxyMethod(self,*args)
        
        f.__doc__ = "deprecated\n"
        f.__name__ = method
        g = strDeprecateDecorator(f)
        setattr( PyNode, method, g)
        

    for method in ['__contains__',  '__len__', 
                            #'__ge__', '__gt__', '__le__', '__lt__',  # still very useful for sorting a list by name
                             '__mod__', '__mul__', '__add__', '__rmod__', '__rmul__',  ]: #'__reduce__' '__radd__', 
        makeDeprecatedMethod( method )                   


_deprecatePyNode()            
                         
_factories.PyNodeNamesToPyNodes()['PyNode'] = PyNode

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
        return PyNode( obj )

SCENE = Scene()
           
        


def isValidMayaType (arg):
    return api.MayaTypesToApiTypes().has_key(arg)

def isValidPyNode (arg):
    return _factories.PyNodeTypesHierarchy().has_key(arg)

def isValidPyNodeName (arg):
    return _factories.PyNodeNamesToPyNodes().has_key(arg)

def mayaTypeToPyNode( arg, default=None ):
    return _factories.PyNodeNamesToPyNodes().get( util.capitalize(arg), default )

def toPyNode( obj, default=None ):
    if isinstance( obj, int ):
        mayaType = api.ApiEnumsToMayaTypes().get( obj, None )
        return _factories.PyNodeNamesToPyNodes().get( util.capitalize(mayaType), default )
    elif isinstance( obj, basestring ):
        try:
            return _factories.PyNodeNamesToPyNodes()[ util.capitalize(obj) ]
        except KeyError:
            mayaType = api.ApiTypesToMayaTypes().get( obj, None )
            return _factories.PyNodeNamesToPyNodes().get( util.capitalize(mayaType), default )
            
def toApiTypeStr( obj, default=None ):
    if isinstance( obj, int ):
        return api.ApiEnumsToApiTypes().get( obj, default )
    elif isinstance( obj, basestring ):
        return api.MayaTypesToApiTypes().get( obj, default)
    elif isinstance( obj, PyNode ):
        mayaType = _factories.PyNodesToMayaTypes().get( obj, None )
        return api.MayaTypesToApiTypes().get( mayaType, default)
    
def toApiTypeEnum( obj, default=None ):
    if isinstance( obj, PyNode ):
        obj = _factories.PyNodesToMayaTypes().get( obj, None )
    return api.toApiTypeEnum(obj)

def toMayaType( obj, default=None ):
    if issubclass( obj, PyNode ):
        return _factories.PyNodesToMayaTypes().get( obj, default )
    return api.toMayaType(obj)


import nodetypes



# Selection list to PyNodes
def _apiSelectionToList ( sel ):
    length = sel.length()
    dag = api.MDagPath()
    comp = api.MObject()
    obj = api.MObject()
    result = []
    for i in xrange(length) :
        selStrs = []
        sel.getSelectionStrings ( i, selStrs )    
        # print "Working on selection %i:'%s'" % (i, ', '.join(selStrs))
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
                pwarnings.warn("Unable to recover selection %i:'%s'" % (i, ', '.join(selStrs)) )             
    return result      
    
    
def _activeSelection () :
    sel = api.MSelectionList()
    api.MGlobal.getActiveSelectionList ( sel )   
    return _apiSelectionToList ( sel )



def _optToDict(*args, **kwargs ):
    result = {}
    types = kwargs.get("valid", [])
    if not util.isSequence(types) :
        types = [types]
    if not basestring in types :
        types.append(basestring)
    for n in args :
        key = val = None
        if isinstance (n, basestring) :            
            if n.startswith("!") :
                key = n.lstrip('!')
                val = False          
            else :
                key = n
                val = True
            # strip all lead and end spaces
            key = key.strip()                       
        else :
            for t in types :
                if isinstance (n, t) :
                    key = n
                    val = True
        if key is not None and val is not None :
            # check for duplicates / contradictions
            if result.has_key(key) :
                if result[key] == val :
                    # already there, do nothing
                    pass
                else :
                    pwarnings.warn("%s=%s contradicts %s=%s, both ignored" % (key, val, key, result[key]))
                    del result[key]
            else :
                result[key] = val
        else :
            pwarnings.warn("'%r' has an invalid type for this keyword argument (valid types: %s)" % (n, types))
    return result                 
            


# calling the above iterators in iterators replicating the functionalities of the builtin Maya ls/listHistory/listRelatives
# TODO : special return options: below, above, childs, parents, asList, breadth, asTree, underworld, allPaths and prune
# TODO : component support
def iterNodes (  *args, **kwargs ):
    """
    Iterates on nodes of the argument list, or when args is empty on nodes of the Maya scene,
    that meet the given conditions.
    
    WARNING: This function is still a work in progress.
    
    The following keywords change the way the iteration is done :
    
    :Keywords:
        selection : bool : False
            will use current selection if no nodes are passed in the arguments list,
            or will filter argument list to keep only selected nodes
        above : int : 0
            for each returned dag node will also iterate on its n first ancestors
        below : int : 0
            for each returned dag node will also iterate on levels of its descendents
        parents : bool : False
            if True is equivalent to above = 1
        childs : bool : False
            if True is equivalent to below = 1       
        asList : bool : False 
        asTree : bool : False
        breadth : bool : False
        underworld : bool : False
        allPaths : bool : False
        prune : bool : False
            
    
    The following keywords specify conditions the iterated nodes are filtered against, conditions can be passed either as a
    list of conditions, format depending on condition type, or a dictionnary of {condition:result} with result True or False
    
    :Keywords:
        name : string or regular expression : None
            will filter nodes that match these names. Names can be full node names, use wildcards * and ?, or regular expression syntax.      
        position = None: will filter dag nodes that have a specific position in their hierarchy :
            'root' for root nodes
            'leaf' for leaves
            'level=<int>' or 'level=[<int>:<int>]' for a specific distance from their root
        type = None: will filter nodes that are of the specified type, or a derived type.
            The types can be specified as Pymel Node types (DependNode and derived) or Maya types names
        property = None: check for specific preset properties, for compatibility with the 'ls' command :
            'visible' : object is visible (it's visibility is True and none of it's ancestor has visibility to False)
            'ghost': ghosting is on for that object 
            'templated': object is templated or one of its ancestors is
            'intermediate' : object is marked as "intermediate object"
        attribute = None: each condition is a string made of at least an attribute name and possibly a comparison operator an a value
            checks a specific attribute of the node for existence: '.visibility',
            or against a value: 'translateX >= 2.0'
        user = None: each condition must be a previously defined function taking the iterated object as argument and returning True or False
    
    expression = None: allows to pass the string of a Python expression that will be evaluated on each iterated node,
        and will limit the result to nodes for which the expression evaluates to 'True'. Use the variable 'node' in the
        expression to represent the currently evaluated node

    Conditions of the same type (same keyword) are combined as with a logical 'or' for positive conditions :
    iterNodes(type = ['skinCluster', 'blendShape']) will iter on all nodes of type skinCluster OR blendShape
    Conditions of the type (same keyword) are combined as with a logical 'and' for negative conditions :
    iterNodes(type = ['!transform', '!blendShape']) will iter on all nodes of type not transform AND not blendShape
    Different conditions types (different keyword) are combined as with a logical 'and' :
    iterNodes(type = 'skinCluster', name = 'bodySkin*') will iter on all nodes that have type skinCluster AND whose name
    starts with 'bodySkin'. 
    
    Examples : (TODO)
    
    
    """
    from system import namespaceInfo as _namespaceInfo, FileReference as _FileReference
    # if a list of existing PyNodes (DependNodes) arguments is provided, only these will be iterated / tested on the conditions
    # TODO : pass the Pymel "Scene" object instead to list nodes of the Maya scene (instead of an empty arg list as for Maya's ls?
    # TODO : if a Tree or Dag of PyNodes is passed instead, make it work on it as wel    
    nodes = []
    for a in args :
        if isinstance(a, nodetypes.DependNode) :
            if a.exists() :
                if not a in nodes :
                    nodes.append(a)
            else :
                raise ValueError, "'%r' does not exist" % a
        else :
            raise TypeError, "%r is not  valid PyNode (DependNode)" % a
    # check
    #print nodes
    # parse kwargs for keywords
    # use current selection for *args
    select = int(kwargs.get('selection', 0))
    # also iterate on the hierarchy below or above (parents) that node for every iterated (dag) node
    below = int(kwargs.get('below', 0))
    above = int(kwargs.get('above', 0))
    # same as below(1) or above(1)
    childs = kwargs.get('childs', False)
    parents = kwargs.get('parents', False)
    if childs and below == 0 :
        below = 1
    if parents and above == 0 :
        above = 1  
    # return a tuple of all the hierarchy nodes instead of iterating on the nodes when node is a dag node
    # and above or below has been set
    asList = kwargs.get('list', False)
    # when below has been set, use breadth order instead of preorder for iterating the nodes below
    breadth = kwargs.get('breadth', False)
    # returns a Tree of all the hierarchy nodes instead of iterating on the nodes when node is a dag node
    # and above or below has been set
    asTree = kwargs.get('tree', False) 
    # include underworld in hierarchies
    underworld = kwargs.get('underword', False)                
    # include all instances paths for dag nodes (means parents can return more than one parent when allPaths is True)
    allPaths = kwargs.get('allPaths', False)
    # prune hierarchy (above or below) iteration when conditions are not met
    prune = kwargs.get('prune', False)
    # to use all namespaces when none is specified instead of current one
    # allNamespace = kwargs.get('allNamespace', False)
    # TODO : check for incompatible flags
    
    # selection
    if (select) :
        sel = _activeSelection()
        if not nodes :
            # use current selection
            nodes = sel
        else :
            # intersects, need to handle components
            for p in nodes :
                if p not in sel :
                    nodes.pop(p)
                    
    _logger.debug("selected nodes: %s", nodes)        
    # Add a conditions with a check for contradictory conditions
    def _addCondition(cDic, key, val):
        # check for duplicates
        if key is not None : 
            if cDic.has_key(key) and vDic[key] != val :
                # same condition with opposite value contradicts existing condition
                pwarnings.warn("Condition '%s' is present with mutually exclusive True and False expected result values, both ignored" % key)
                del cDic[key]
            else :
                cDic[key] = val
                return True
        return False     
                 
    # conditions on names (regular expressions, namespaces), can be passed as a dict of
    # condition:value (True or False) or a sequence of conditions, with an optional first
    # char of '!' to be tested for False instead of True. It can be an actual node name
    nameArgs = kwargs.get('name', None)
    # the resulting dictionnary of conditions on names (compiled regular expressions)
    cNames = {}
    # check
    #print "name args", nameArgs   
    if nameArgs is not None :
        # convert list to dict if necessary
        if not isinstance(nameArgs, dict):
            if not util.isSequence(nameArgs) :
                nameArgs = [nameArgs]    
            nameArgs = _optToDict(*nameArgs)
        # check
        logging.debug("nameArgs: %s", nameArgs)
        # for names parsing, see class definition in nodes
        curNameSpace = _namespaceInfo( currentNamespace=True )    
        for i in nameArgs.items() :
            key = i[0]
            val = i[1]
            if key.startswith('(') and key.endswith(')') :
                # take it as a regular expression directly
                pass
            elif '*' in key or '?' in key :
                # it's a glob pattern, try build a re out of it and add it to names conditions
                validCharPattern = r"[a-zA-z0-9_]"
                key = key.replace("*", r"("+validCharPattern+r"*)")
                key = key.replace("?", r"("+validCharPattern+r")")
            else :
                # either a valid dag node / node name or a glob pattern
                try :
                    name = nameparse.MayaObjectName(key)
                    # if it's an actual node, plug or component name
                    # TODO : if it's a long name need to substitude namespaces on all dags
                    name = name.node
                    # only returns last node namespace in the case of a long name / dag path
                    # TODO : check how ls handles that
                    nameSpace = name.node.namespace
                    #print nameSpace, name
                    if not nameSpace :
                        # if no namespace was specified use current ('*:' can still be used for 'all namespaces')
                        nameSpace = curNameSpace
                    if cmds.namespace(exists=nameSpace) :
                        # format to have distinct match groups for nameSpace and name
                        key = r"("+nameSpace+r")("+name+r")"
                    else :
                        raise ValueError, "'%s' uses inexistent nameSpace '%s'" % (key, nameSpace)
                    # namespace thing needs a fix
                    key = r"("+name+r")"                    
                except nameparse.NameParseError, e :
                    # TODO : bad formed name, ignore it
                    pass
            try :
                r = re.compile(key)
            except :
                raise ValueError, "'%s' is not a valid regular expression" % key
            # check for duplicates re and add
            _addCondition(cNames, r, val)
        # check
        #print "Name keys:"
        #for r in cNames.keys() :
            #print "%s:%r" % (r.pattern, cNames[r])     
      
    # conditions on position in hierarchy (only apply to dag nodes)
    # can be passed as a dict of conditions and values
    # condition:value (True or False) or a sequence of conditions, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # valid flags are 'root', 'leaf', or 'level=x' for a relative depth to start node 
    posArgs = kwargs.get('position', None)
    # check
    #print "position args", posArgs    
    cPos = {}    
    if posArgs is not None :
        # convert list to dict if necessary
        if not isinstance(posArgs, dict):
            if not util.isSequence(posArgs) :
                posArgs = [posArgs]    
            posArgs = _optToDict(*posArgs)    
        # check
        #print posArgs
        validLevelPattern = r"level\[(-?[0-9]*)(:?)(-?[0-9]*)\]"
        validLevel = re.compile(validLevelPattern)
        for i in posArgs.items() :
            key = i[0]
            val = i[1]
            if key == 'root' or key == 'leaf' :
                pass           
            elif key.startswith('level') :
                levelMatch = validLevel.match(key)
                level = None
                if levelMatch is not None :
                    if levelMatch.groups[1] :
                        # it's a range
                        lstart = lend = None
                        if levelMatch.groups[0] :
                            lstart = int(levelMatch.groups[0])
                        if levelMatch.groups[2] :
                            lend = int(levelMatch.groups[2])
                        if lstart is None and lend is None :
                            level = None
                        else :                      
                            level = IRange(lstart, lend)
                    else :
                        # it's a single value
                        if levelMatch.groups[1] :
                            level = None
                        elif levelMatch.groups[0] :
                            level = IRange(levelMatch.groups[0], levelMatch.groups[0]+1)
                        else :
                            level = None               
                if level is None :
                    raise ValueError, "Invalid level condition %s" % key
                    key = None
                else :
                    key = level     
            else :
                raise ValueError, "Unknown position condition %s" % key
            # check for duplicates and add
            _addCondition(cPos, key, val)            
            # TODO : check for intersection with included levels
        # check
        #print "Pos keys:"
        #for r in cPos.keys() :
            #print "%s:%r" % (r, cPos[r])    
                           
    # conditions on types
    # can be passed as a dict of types (Maya or Pymel type names) and values
    # condition:value (True or False) or a sequence of type names, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # valid flags are 'root', 'leaf', or 'level=x' for a relative depth to start node                       
    # Note: API iterators can filter on API types, we need to postfilter for all the rest
    typeArgs = kwargs.get('type', None)
    # check
    # #print "type args", typeArgs
    # support for types that can be translated as API types and can be directly used by API iterators
    # and other types that must be post-filtered  
    cAPITypes = {}
    cAPIPostTypes = {}
    cExtTypes = {}
    cAPIFilter = []
    
    # filter out kWorld.  what the hell is this anyway?  is it useful?  (CHAD)

    if typeArgs is not None :
        #extendedFilter = False
        apiFilter = False
        # convert list to dict if necessary
        if not isinstance(typeArgs, dict):
            if not util.isSequence(typeArgs) :
                typeArgs = [typeArgs]
            # can pass strings or PyNode types directly
            typeArgs = _optToDict(*typeArgs, **{'valid':nodetypes.DependNode})    
        # check
        #print typeArgs
        for key, isInclusive in typeArgs.items() :
            apiType = extType = None
            if isValidMayaType(key) :
                # is it a valid Maya type name
                extType = key
                # can we translate it to an API type string
                apiType = api.mayaTypeToApiType(extType)
            else :
                # or a PyNode type or type name
                if isValidPyNodeTypeName(key) :
                    key = PyNodeNamesToPyNodes().get(key, None)
                if isValidPyNodeType(key) :
                    extType = key
                    apiType = api.PyNodesToApiTypes().get(key, None)
                    
            print "%s ---> %s: %s" % ( extType, apiType, isInclusive )
            # if we have a valid API type, add it to cAPITypes, if type must be postfiltered, to cExtTypes
            if apiType is not None :
                if _addCondition(cAPITypes, apiType, isInclusive) :
                    if isInclusive :
                        apiFilter = True
            elif extType is not None :
                if _addCondition(cExtTypes, extType, isInclusive) :
                    if isInclusive :
                        extendedFilter = True
            else :
                raise ValueError, "Invalid/unknown type condition '%s'" % key 
        # check
        _logger.debug(" API type keys: ")
        map(_logger.debug, map(str, cAPITypes.items()))   
        _logger.debug(" Ext type keys: ")
        map(_logger.debug, map(str, cExtTypes.items()))   
        
        # if we check for the presence (positive condition) of API types and API types only we can 
        # use the API MIteratorType for faster filtering, it's not applicable if we need to prune
        # iteration for unsatisfied conditions
        if apiFilter and not extendedFilter and not prune :
            for key, isInclusive in cAPITypes.items() :
                #NOTE: is apiTypeToEnum ever a 1-to-many relationship?
                apiInt = api.apiTypeToEnum(key)
                if isInclusive and apiInt :
                    # can only use API filter for API types enums that are tested for positive
                    cAPIFilter.append(apiInt)
                else :
                    # otherwise must postfilter
                    cAPIPostTypes[key] = isInclusive
        else :
            cAPIPostTypes = cAPITypes
        # check
        _logger.debug(" API filter: ")
        _logger.debug(cAPIFilter)  
        _logger.debug(" API post types ")
        _logger.debug(cAPIPostTypes)
                          
    # conditions on pre-defined properties (visible, ghost, etc) for compatibility with ls
    validProperties = {'visible':1, 'ghost':2, 'templated':3, 'intermediate':4}    
    propArgs = kwargs.get('properties', None)
    # check
    #print "Property args", propArgs    
    cProp = {}    
    if propArgs is not None :
        # convert list to dict if necessary
        if not isinstance(propArgs, dict):
            if not util.isSequence(propArgs) :
                propArgs = [propArgs]    
            propArgs = _optToDict(*propArgs)    
        # check
        #print propArgs
        for i in propArgs.items() :
            key = i[0]
            val = i[1]
            if validProperties.has_key(key) :
                # key = validProperties[key]
                _addCondition(cProp, key, val)
            else :
                raise ValueError, "Unknown property condition '%s'" % key
        # check
        #print "Properties keys:"
        #for r in cProp.keys() :
            #print "%s:%r" % (r, cProp[r])      
    # conditions on attributes existence / value
    # can be passed as a dict of conditions and booleans values
    # condition:value (True or False) or a sequence of conditions,, with an optionnal first
    # char of '!' to be tested for False instead of True.
    # An attribute condition is in the forms :
    # attribute==value, attribute!=value, attribute>value, attribute<value, attribute>=value, attribute<=value, 
    # Note : can test for attribute existence with attr != None
    attrArgs = kwargs.get('attribute', None)
    # check
    #print "Attr args", attrArgs    
    cAttr = {}    
    if attrArgs is not None :
        # convert list to dict if necessary
        if not isinstance(attrArgs, dict):
            if not util.isSequence(attrArgs) :
                attrArgs = [attrArgs]    
            attrArgs = _optToDict(*attrArgs)    
        # check
        #print attrArgs
        # for valid attribute name patterns check node.Attribute  
        # valid form for conditions
        attrValuePattern = r".+"
        attrCondPattern = r"(?P<attr>"+nameparse.PlugName.pattern+r")[ \t]*(?P<oper>==|!=|>|<|>=|<=)?[ \t]*(?P<value>"+attrValuePattern+r")?"
        validAttrCond = re.compile(attrCondPattern)        
        for i in attrArgs.items() :
            key = i[0]
            val = i[1]
            attCondMatch = validAttrCond.match(key.strip())
            if attCondMatch is not None :
                # eval value here or wait resolution ?
                attCond = (attCondMatch.group('attr'), attCondMatch.group('oper'), attCondMatch.group('value'))
                # handle inversions
                if val is False :
                    if attCond[1] is '==' :
                        attCond[1] = '!='
                    elif attCond[1] is '!=' :
                        attCond[1] = '=='
                    elif attCond[1] is '>' :
                        attCond[1] = '<='
                    elif attCond[1] is '<=' :
                        attCond[1] = '>'
                    elif attCond[1] is '<' :
                        attCond[1] = '>='
                    elif attCond[1] is '>=' :
                        attCond[1] = '<'                        
                    val = True
                # Note : special case where value is None, means test for attribute existence
                # only valid with != or ==
                if attCond[2] is None :
                    if attCond[1] is None :
                        val = True
                    elif attCond[1] is '==' :
                        attCond[1] = None
                        val = False  
                    elif attCond[1] is '!=' :
                        attCond[1] = None
                        val = True
                    else :
                        raise ValueError, "Value 'None' means testing for attribute existence and is only valid for operator '!=' or '==' '%s' invalid" % key
                        attCond = None
                # check for duplicates and add
                _addCondition(cAttr, attCond, val)                                               
            else :
                raise ValueError, "Unknown attribute condition '%s', must be in the form 'attr <op> value' where <op> is !=, ==, >=, >, <= or <" % key          
        # check
        #print "Attr Keys:"
        #for r in cAttr.keys() :
            #print "%s:%r" % (r, cAttr[r])        
    # conditions on user defined boolean functions
    userArgs = kwargs.get('user', None)
    # check
    #print "userArgs", userArgs    
    cUser = {}    
    if userArgs is not None :
        # convert list to dict if necessary
        if not isinstance(userArgs, dict):
            if not util.isSequence(userArgs) :
                userArgss = [userArgs]    
            userArgs = _optToDict(*userArgs, **{'valid':function})    
        # check
        #print userArgs            
        for i in userArgs.items() :
            key = i[0]
            val = i[1]
            if isinstance(key, basestring) :
                key = globals().get(key,None)
            if key is not None :
                if inspect.isfunction(key) and len(inspect.getargspec(key)[0]) is 1 :
                    _addCondition(cUser, key, val)
                else :
                    raise ValueError, "user condition must be a function taking one argument (the node) that will be tested against True or False, %r invalid" % key
            else :
                raise ValueError, "name '%s' is not defined" % key        
        # check
        #print "User Keys:"
        #for r in cUser.keys() :
            #print "%r:%r" % (r, cUser[r])
    # condition on a user defined expression that will be evaluated on each returned PyNode,
    # that must be represented by the variable 'node' in the expression    
    userExpr = kwargs.get('exp', None)
    if userExpr is not None and not isinstance(userExpr, basestring) :
        raise ValueError, "iterNodes expression keyword takes an evaluable string Python expression"

    # post filtering function
    def _filter( pyobj, apiTypes={}, extTypes={}, names={}, pos={}, prop={}, attr={}, user={}, expr=None  ):
        result = True
        
        # always filter kWorld
        apiType = pyobj.type(api=True)
        if apiType == 'kWorld':
            result = False
            
        # check on types conditions
        if result and (len(apiTypes)!=0 or len(extTypes)!=0) :
            result = False
            for ctyp, cval in apiTypes.items() :
                #if pyobj.type(api=True) == ctyp :
                if apiType == ctyp :
                    result = cval
                    break
                elif not cval :
                    result = True                                      
            for ctyp, cval in extTypes.items() :                                     
                if isinstance(pyobj, ctyp) :
                    result = cval
                    break
                elif not cval :
                    result = True                   
        # check on names conditions
        if result and len(names)!=0 :
            result = False
            for creg, cval in names.items() :
                _logger.debug("match %s on %s" % (creg.pattern, pyobj.name(update=False)))
                if creg.match(pyobj.name(update=False)) is not None :
                    result = cval
                    break
                elif not cval :
                    result = True                                             
        # check on position (for dags) conditions
        if result and len(pos)!=0 and isinstance(pyobj, nodetypes.DagNode) :
            result = False
            for cpos, cval in pos.items() :              
                if cpos == 'root' :
                    if pyobj.isRoot() :
                        result = cval
                        break
                    elif not cval :
                        result = True
                elif cpos == 'leaf' :
                    if pyobj.isLeaf() :
                        result = cval
                        break
                    elif not cval :
                        result = True                    
                elif isinstance(cpos, IRange) :
                    if pyobj.depth() in cpos :
                        result = cval
                        break       
                    elif not cval :
                        result = True                                                                
        # TODO : 'level' condition, would be faster to get the depth from the API iterator
        # check some pre-defined properties, so far existing properties all concern dag nodes
        if result and len(prop)!=0 and isinstance(pyobj, nodetypes.DagNode) :
            result = False
            for cprop, cval in prop.items() :                   
                if cprop == 'visible' :
                    if pyobj.isVisible() :
                        result = cval
                        break 
                    elif not cval :
                        result = True                                  
                elif cprop == 'ghost' :
                    if pyobj.hasAttr('ghosting') and pyobj.getAttr('ghosting') :
                        result = cval
                        break 
                    elif not cval :
                        result = True                                   
                elif cprop == 'templated' :
                    if pyobj.isTemplated() :
                        result = cval
                        break 
                    elif not cval :
                        result = True      
                elif cprop == 'intermediate' :
                    if pyobj.isIntermediate() :
                        result = cval
                        break 
                    elif not cval :
                        result = True                        
        # check for attribute existence and value
        if result and len(attr)!=0 :
            result = False
            for cattr, cval in attr.items() :
                # cattr is a tuple of (attribute, operator, value)
                if pyobj.hasAttr(cattr[0]) :                
                    if cattr[1] is None :
                        result = cval
                        break                    
                    else :
                        if eval(str(pyobj.getAttr(cattr[0]))+cattr[1]+cattr[2]) :
                            result = cval
                            break  
                        elif not cval :
                            result = True
                elif not cval :
                    result = True                                                                  
        # check for used condition functions
        if result and len(user)!=0 :
            result = False
            for cuser, cval in user.items() :                  
                if cuser(pyobj) :
                    result = cval
                    break  
                elif not cval :
                    result = True  
        # check for a user eval expression
        if result and expr is not None :
            result = eval(expr, globals(), {'node':pyobj})     
                     
        return result
        # END _filter
    
       
    # Iteration :
    needLevelInfo = False
    
    # TODO : special return options
    # below, above, childs, parents, asList, breadth, asTree, underworld, allPaths and prune
    if nodes :
        # if a list of existing nodes is provided we iterate on the ones that both exist and match the used flags        
        for pyobj in nodes :
            if _filter (pyobj, cAPIPostTypes, cExtTypes, cNames, cPos, cProp, cAttr, cUser, userExpr ) :
                yield pyobj
    else :
        # else we iterate on all scene nodes that satisfy the specified flags, 
        for obj in api.MItNodes( *cAPIFilter ) :
            pyobj = PyNode( obj )
            # can MItDependencyNodes return a non-existent object? (CHAD)
            if pyobj.exists() :
                if _filter (pyobj, cAPIPostTypes, cExtTypes, cNames, cPos, cProp, cAttr, cUser, userExpr ) :
                    yield pyobj
        

def iterConnections ( *args, **kwargs ):
    pass

def iterHierarchy ( *args, **kwargs ):
    pass




def _analyzeApiClasses():
    for elem in api.apiTypeHierarchy.preorder():
        try:
            parent = elem.parent.key
        except:
            parent = None
        _factories.analyzeApiClass( elem.key, None )
        



_factories.createFunctions( __name__, PyNode )

"""
Contains general node and attribute functions, as well as the main `PyNode` base class.

For the rest of the class hierarchy, including `DependNode <pymel.core.nodetypes.DependNode>`, `Transform <pymel.core.nodetypes.Transform>`,
and `Attribute <pymel.core.nodetypes.Attribute>`, see :mod:`pymel.core.nodetypes`.


"""
from __future__ import with_statement

import sys, os, re, itertools, inspect

import pymel.internal.pmcmds as cmds
import pymel.util as _util
import pymel.internal.factories as _factories
import pymel.internal.pwarnings as _warnings
import pymel.api as _api
import pymel.versions as _versions
import datatypes
import logging
from maya.cmds import about as _about
_logger = logging.getLogger(__name__)


# TODO: factories.functionFactory should automatically handle conversion of output to PyNodes...
#       ...so we shouldn't always have to do it here as well?

def _getPymelTypeFromObject(obj, name):
    if obj.hasFn(_api.MFn.kDependencyNode):
        fnDepend = _api.MFnDependencyNode( obj )
        mayaType = fnDepend.typeName()
        import nodetypes
        pymelType = getattr( nodetypes, _util.capitalize(mayaType), nodetypes.DependNode )
        pymelType = _factories.virtualClasses.getVirtualClass(pymelType, obj, name, fnDepend)
    elif obj.hasFn(_api.MFn.kComponent):
        compTypes = _factories.apiEnumsToPyComponents.get(obj.apiType(), None)
        if compTypes is None:
            raise RuntimeError('Got an instance of a component which could not be mapped to a pymel class: %s' % obj.apiTypeStr())
        if len(compTypes) != 1:
            raise RuntimeError('Got an instance of a component with more than one possible PyNode type: %s' % obj.apiTypeStr())
        pymelType = compTypes[0]
    elif obj.hasFn(_api.MFn.kAttribute):
        pymelType = AttributeDefaults
    else:
        raise RuntimeError('Could not determine pymel type for object of type %s' % obj.apiTypeStr())

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
        raise ValueError( "Unable to determine Pymel type for %r" % (arg,) )

    if not isAttribute:
        pymelType = _getPymelTypeFromObject( obj, name )

    return pymelType, results
#-----------------------------------------------
#  Enhanced Commands
#-----------------------------------------------

# TODO: possible bugfix for 'parent'?
# Docs state 'If there is only a single object specified then the selected objects are parented to that object. '
# ...but actual behavior is to parent the named object (and any other selected objects) to the last selected object

#-----------------------
#  Object Manipulation
#-----------------------

def select(*args, **kwargs):
    """
Modifications:
  - passing an empty list no longer causes an error.
      instead, the selection is cleared if the selection mod is replace (the default);
      otherwise, it does nothing

    """
    try:
        cmds.select(*args, **kwargs)
    except TypeError, msg:
        if args == ([],):
            for modeFlag in ('add', 'af', 'addFirst',
                             'd', 'deselect',
                             'tgl', 'toggle'):
                if kwargs.get(modeFlag, False):
                    return
            # The mode is replace, clear the selection
            cmds.select(cl=True)
        else:
            raise TypeError, msg
#select.__doc__ = mel.help('select') + select.__doc__


# TODO: make it handle multiple objects, like original command
def move(*args, **kwargs):
    """
Modifications:
  - allows any iterable object to be passed as first argument::

        move("pSphere1", [0,1,2])

NOTE: this command also reorders the argument order to be more intuitive, with the object first
    """
    obj = None
    if args and isinstance(args[0], (basestring, PyNode)):
        obj = args[0]
        args = args[1:]

    if len(args) == 1 and _util.isIterable(args[0]):
        args = tuple(args[0])
    if obj is not None:
        args = args + (obj,)
    return cmds.move(*args, **kwargs)

def scale(obj, *args, **kwargs):
    """
Modifications:
  - allows any iterable object to be passed as first argument::

        scale("pSphere1", [0,1,2])

NOTE: this command also reorders the argument order to be more intuitive, with the object first
    """
    if len(args) == 1 and _util.isIterable(args[0]):
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
    if len(args) == 1 and _util.isIterable(args[0]):
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

            for src, dest in _util.pairIter(connections):
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
  - added support for getting message attributes
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
    if isinstance(attr, Attribute):
        attr = attr.name(placeHolderIndices=False)
    else:
        attr = unicode(attr)

    try:
        res = cmds.getAttr( attr, **kwargs)

        if isinstance(res, list) and len(res):
            if isinstance(res[0], tuple):
                typ = cmds.getAttr( attr, type=1)
                if typ == 'pointArray':
                    return [ datatypes.Point(x) for x in res ]
                elif typ == 'vectorArray':
                    return [ datatypes.Vector(x) for x in res ]
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
                if pyattr.type() == 'message':
                    return pyattr.listConnections()
                return [pyattr[i].get() for i in range(pyattr.numElements())]
            # re-raise error
            elif pyattr.type() == 'message':
                connects = pyattr.listConnections()
                if connects:
                    return connects[0]
                else:
                    return None
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

  - Added ability to set enum attributes using the string values; this may be
    done either by setting the 'asString' kwarg to True, or simply supplying
    a string value for an enum attribute.

    """
    datatype = kwargs.get( 'type', kwargs.get( 'typ', None) )

    # if there is only one argument we do our special pymel tricks
    if len(args) == 1:

        arg = args[0]

        # force flag
        force = kwargs.pop('force', kwargs.pop('f', False) )

        # asString flag
        asString = kwargs.pop('asString', None)

        # vector, matrix, and arrays
        if _util.isIterable(arg):
            if datatype is None:
                # if using force flag and the attribute does not exist
                # we can infer the type from the passed value
                #attr = Attribute(attr)
                if force and not cmds.objExists(attr): #attr.exists():
                    import pymel.util.nameparse as nameparse
                    attrName = nameparse.parse( attr )
                    assert attrName.isAttributeName(), "passed object is not an attribute"
                    try:
                        if isinstance( arg[0], (basestring, _util.ProxyUnicode ) ):
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

                        #_logger.debug("adding %r as %r", attr, datatype)
                        addAttr( attrName.nodePath, ln=attrName.attribute, dt=datatype )

                    # empty array is being passed
                    # if the attribute exists, this is ok
                    except IndexError:
                        raise ValueError, "pymel.core.setAttr: when setting 'force' keyword to create a new array attribute, you must provide an array with at least one element"

                    except TypeError:
                        raise ValueError, "pymel.core.setAttr: %s is not a supported type" % type(args)

                else:
                    if isinstance( arg, datatypes.Vector):
                        datatype = 'double3'
                    elif isinstance( arg, datatypes.Matrix ):
                        datatype = 'matrix'
                    else:
                        datatype = getAttr( attr, type=1)
                        if not datatype:
                            datatype = addAttr( attr, q=1, dataType=1) #[0] # this is returned as a single element list
                if datatype:
                    kwargs['type'] = datatype

            try:
                arg = arg.__melobject__()
            except AttributeError:
                pass
            if datatype == 'stringArray':
                # string arrays:
                #    first arg must be the length of the array being set
                # ex:
                #     setAttr('loc.strArray',["first", "second", "third"] )
                # becomes:
                #     cmds.setAttr('loc.strArray',3,"first", "second", "third",type='stringArray')
                args = tuple( [len(arg)] + arg )

            elif datatype in ['vectorArray', 'pointArray']:
                if _versions.current() < _versions.v2011:
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
                else:
                    # vector arrays:
                    #    first arg must be the length of the array being set
                    #    empty values are placed between vectors
                    # ex:
                    #     setAttr('loc.vecArray',[1,2,3],[4,5,6],[7,8,9] )
                    # becomes:
                    #     cmds.setAttr('loc.vecArray',3,[1,2,3],[4,5,6],[7,8,9],type='vectorArray')
                    arg = list(arg)
                    size = len(arg)
                    args = tuple( [size] + arg )

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

                elif isinstance(arg, (basestring, _util.ProxyUnicode)):
                    if asString is None:
                        if isinstance(attr, Attribute):
                            attrType = attr.type()
                        else:
                            attrType = cmds.getAttr(attr, type=1)
                        asString = (attrType == 'enum')
                    if asString:
                        val = getEnums(attr).get(arg)
                        if val is None:
                            raise MayaAttributeEnumError(attr, arg)
                        arg = val
                        args = (val,)
                    else:
                        kwargs['type'] = 'string'

    if datatype == 'matrix' and _versions.current() < _versions.v2011:
        import language
        #language.mel.setAttr( attr, *args, **kwargs )
        strFlags = [ '-%s %s' % ( key, language.pythonToMel(val) ) for key, val in kwargs.items() ]
        cmd = 'setAttr %s %s %s' % ( attr, ' '.join( strFlags ), ' '.join( [str(x) for x in args] ) )
        import maya.mel as _mm
        #print cmd
        _mm.eval(cmd)
        return

    # stringify fix
    attr = unicode(attr)

    try:
        #print args, kwargs
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
        # can't use 'startswith' because of Autodesk test strings wrapped in commas
        if 'No object matches name: ' in str(msg):
            raise _objectError(attr)
        else:
            # re-raise
            raise

def addAttr( *args, **kwargs ):
    """
Modifications:
  - allow python types to be passed to set -at type
            str         string
            float       double
            int         long
            bool        bool
            Vector      double3
  - when querying dataType, the dataType is no longer returned as a list
  - when editing hasMinValue, hasMaxValue, hasSoftMinValue, or hasSoftMaxValue the passed boolean value was ignored
    and the command instead behaved as a toggle.  The behavior is now more intuitive::
        >>> addAttr('persp', ln='test', at='double', k=1)
        >>> addAttr('persp.test', query=1, hasMaxValue=True)
        False
        >>> addAttr('persp.test', edit=1, hasMaxValue=False)
        >>> addAttr('persp.test', query=1, hasMaxValue=True)
        False
        >>> addAttr('persp.test', edit=1, hasMaxValue=True)
        >>> addAttr('persp.test', query=1, hasMaxValue=True)
        True

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

    if kwargs.get( 'e', kwargs.get('edit',False) ):
            for editArg, value in kwargs.iteritems():
                if editArg not in ('e', 'edit') and value:
                    break
            if editArg in ('hasMinValue', 'hnv', 'hasMaxValue', 'hxv', 'hasSoftMinValue', 'hsn', 'hasSoftMaxValue', 'hsx'):
                # bugfix: hasM*Value works as a toggle, regardless of whether you specify True or False
                if bool(value) != bool(cmds.addAttr(*args, **{'query':True, editArg:True})):
                    return cmds.addAttr(*args, **kwargs)
                else:
                    # otherwise, don't do anything, bc the value is already correct
                    return
    # MObject stringify Fix
    #args = map(unicode, args)
    res = cmds.addAttr( *args, **kwargs )
    if kwargs.get( 'q', kwargs.get('query',False) ):
        # When addAttr is queried, and has multiple other query flags - ie,
        #   addAttr('joint1.sweetpea', q=1, parent=1, dataType=1)
        # ... it seems to ignore every kwarg but the 'first'
        for queriedArg, value in kwargs.iteritems():
            if queriedArg not in ('q', 'query') and value:
                break
        if queriedArg in ('dt', 'dataType'):
            # If the attr is not a dynamic attribute, maya.cmds prints:
            #    Error: '...' is not a dynamic attribute of node '...'.
            # ...but does NOT raise an exception
            # Because it will be more consistent with maya.cmds, and because
            # attributeType already behaves like this, we will do the same -
            # allow maya.cmds to print it's error message, and return None, but
            # not raise an exception  
            if res is not None: 
                res = res[0]
        elif queriedArg in ('p', 'parent'):
            node = None
            if args:
                node = PyNode(args[0])
            else:
                node = ls(sl=1)[0]
            if isinstance(node, Attribute):
                node = node.node()
            res = node.attr(res)

#    else:
#        # attempt to gather Attributes we just made
#        # this is slightly problematic because compound attributes are invalid
#        # until all of their children are created, as in these example from the docs
#
#        #addAttr( longName='sampson', numberOfChildren=5, attributeType='compound' )
#        #addAttr( longName='homeboy', attributeType='matrix', parent='sampson' )
#        #addAttr( longName='midge', attributeType='message', parent='sampson' )
#        #addAttr( longName='damien', attributeType='double', parent='sampson' )
#        #addAttr( longName='elizabeth', attributeType='double', parent='sampson' )
#        #addAttr( longName='sweetpea', attributeType='double', parent='sampson' )
#
#
#        if not args:
#            args=cmds.ls(sl=1,l=1)
#        longName = kwargs.pop( 'longName', kwargs.get('ln',None) )
#        shortName = kwargs.pop( 'shortName', kwargs.get('sn',None) )
#        name = longName if longName else shortName
#        assert name, "could not determine name of attribute"
#        res = [ Attribute(x + '.' + name) for x in args]

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
#  Attr Enums
#-----------------------

def setEnums(attr, enumList):
    cmds.addAttr( attr, e=1, en=":".join(enumList) )


def getEnums(attr):
    """
    :rtype: `util.enum.EnumDict`

    >>> addAttr( "persp", ln='numbers', at='enum', enumName="zero:one:two:thousand=1000:three")
    >>> numbers = Attribute('persp.numbers').getEnums()
    >>> sorted(numbers.items())
    [(u'one', 1), (u'thousand', 1000), (u'three', 1001), (u'two', 2), (u'zero', 0)]
    >>> numbers[1]
    u'one'
    >>> numbers['thousand']
    1000

    """
    if isinstance(attr, Attribute):
        attrName = attr.attrName()
        node = attr.node().name()
    else:
        node, attrName = unicode(attr).rsplit('.', 1)
    enum_list = cmds.attributeQuery(attrName, node=node,
                                    listEnum=True)[0].split(':')

    enum_dict = {}
    index = 0
    for enum in enum_list:
        try:
            name, value = enum.split(u'=')
            index = int(value)
            enum = name
        except:
            pass
        enum_dict[enum] = index
        index += 1

    return _util.enum.EnumDict(enum_dict)

#-----------------------
#  List Functions
#-----------------------

#def listAttr(*args, **kwargs):
#    """
#Modifications:
#  - returns an empty list when the result is None
#    """
#    return _util.listForNone(cmds.listAttr(*args, **kwargs))

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
    # We need to force casting to Attribute, as opposed to just Pynode,
    # if we are returning plugs, because PyNode will prefer component
    # objects over attributes when there is amibiguity - ie,
    # PyNode('myNode.rotatePivot') will give a component
    plugs = kwargs.get('plugs', kwargs.get('p', False))
    if plugs:
        CastObj = Attribute
    else:
        CastObj = PyNode

    def makePairs(l):
        if l is None:
            return []
        return [(CastObj(a), CastObj(b)) for (a, b) in _util.pairIter(l)]

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
            return map(CastObj, _util.listForNone(cmds.listConnections( *args,  **kwargs )) )

    # if passed a list of types, concatenate the resutls
    # NOTE: there may be duplicate results if a leaf type and it's parent are both passed: ex.  animCurve and animCurveTL
    types = kwargs.get('type', kwargs.get('t',None))
    if _util.isIterable(types):
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

    results = [PyNode(x) for x in _util.listForNone(cmds.listHistory( *args,  **kwargs ))]

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
  - noIntermediate doesn't appear to work

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

    results = map(PyNode, _util.listForNone(cmds.listRelatives(*args, **kwargs)))
    #Fix that noIntermediate doesn't seem to work in list relatives
    if kwargs.get('noIntermediate',kwargs.get('ni',False)):
        return [ result for result in results if not result.intermediateObject.get()]
    return results


def ls( *args, **kwargs ):
    """
Modifications:
  - Added new keyword: 'editable' - this will return the inverse set of the readOnly flag. i.e. non-read-only nodes
  - Added new keyword: 'regex' - pass a valid regular expression string, compiled regex pattern, or list thereof.

        >>> group('top')
        nt.Transform(u'group1')
        >>> duplicate('group1')
        [nt.Transform(u'group2')]
        >>> group('group2')
        nt.Transform(u'group3')
        >>> ls(regex='group\d+\|top') # don't forget to escape pipes `|`
        [nt.Transform(u'group1|top'), nt.Transform(u'group2|top')]
        >>> ls(regex='group\d+\|top.*')
        [nt.Transform(u'group1|top'), nt.Camera(u'group1|top|topShape'), nt.Transform(u'group2|top'), nt.Camera(u'group2|top|topShape')]
        >>> ls(regex='group\d+\|top.*', cameras=1)
        [nt.Camera(u'group2|top|topShape'), nt.Camera(u'group1|top|topShape')]
        >>> ls(regex='\|group\d+\|top.*', cameras=1) # add a leading pipe to search for full path
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

    editable = kwargs.pop('editable', False)

    res = _util.listForNone(cmds.ls(*args, **kwargs))
    if regexArgs:
        tmp = res
        res = []
        for x in tmp:
            for reg in regexArgs:
                if reg.search(x):
                    res.append(x)
                    break

    if editable:
        kwargs['readOnly'] = True
        kwargs.pop('ro',True)
        roNodes = _util.listForNone(cmds.ls(*args, **kwargs))
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
#    tmp = _util.listForNone(cmds.ls(*args, **kwargs))
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
#        tmp = _util.listForNone(cmds.ls(*args, **kwargs))
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


def listSets(*args, **kwargs):
    '''
Modifications:
  - returns wrapped classes
  - if called without arguments and keys works as with allSets=True
  :rtype: `PyNode` list
    '''
    #cmds.listSets() reports existance of defaultCreaseDataSet which does not
    #exist if checked with cmds.objExists at least linux-2010
    if not args and not kwargs:
        kwargs['allSets'] = True
    return [PyNode(x) for x in _util.listForNone(cmds.listSets( *args,  **kwargs))
            if not x == 'defaultCreaseDataSet' ]

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

#    obj = None
#    objName = None

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
        # don't do unicode(node) - let pmcmds wrap handle it - 'node' may
        #     actually be a single item list, which cmds.nodeType accepts as a
        #    valid arg 
        return cmds.nodeType( node, **kwargs )
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
  - if no objects are passed or selected, the empty flag is automatically set
Maya Bug Fix:
  - corrected to return a unique name
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
  - returnRootsOnly is forced on for dag objects. This is because the duplicate command does not use full paths when returning
    the names of duplicated objects and will fail if the name is not unique.
    """
    addShape = kwargs.pop('addShape', False)
    kwargs.pop('rr', None)
    kwargs['returnRootsOnly'] = bool(cmds.ls(dag=1,*args))

    if not addShape:
        return map(PyNode, cmds.duplicate( *args, **kwargs ) )
    else:
        for invalidArg in ('renameChildren', 'rc', 'instanceLeaf', 'ilf',
                           'parentOnly', 'po', 'smartTransform', 'st'):
            if kwargs.get(invalidArg, False) :
                raise ValueError("duplicate: argument %r may not be used with 'addShape' argument" % invalidArg)
        name=kwargs.pop('name', kwargs.pop('n', None))

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

#def instance( *args, **kwargs ):
#    """
#Modifications:
#  - returns wrapped classes
#    """
#    return map(PyNode, cmds.instance( *args, **kwargs ) )

'''
def attributeInfo( *args, **kwargs ):
    """
Modifications:
  - returns an empty list when the result is None
  - returns wrapped classes
    """

    return map(PyNode, _util.listForNone(cmds.attributeInfo(*args, **kwargs)))
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

        >>> from pymel.core import *
        >>> f=newFile(f=1) #start clean
        >>>
        >>> shdr, sg = createSurfaceShader( 'blinn' )
        >>> shdr
        nt.Blinn(u'blinn1')
        >>> sg
        nt.ShadingEngine(u'blinn1SG')
        >>> s,h = polySphere()
        >>> s
        nt.Transform(u'pSphere1')
        >>> sets( sg, forceElement=s ) # add the sphere
        nt.ShadingEngine(u'blinn1SG')
        >>> sets( sg, q=1)  # check members
        [nt.Mesh(u'pSphereShape1')]
        >>> sets( sg, remove=s )
        nt.ShadingEngine(u'blinn1SG')
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
            if _util.isIterable(value):
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
#            return map( PyNode, _util.listForNone(cmds.sets( *args, **kwargs )) )

    # Just get the result, then check if it's a list, rather than trying to
    # parse the kwargs...
    result = cmds.sets( *args, **kwargs )
    if isinstance(result, (bool, int, long, float)):
        return result
    if _util.isIterable(result):
        return map( PyNode, _util.listForNone(result) )
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
    if len(args) ==1 and _util.isIterable(args[0]) and not args[0]:
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

class MayaAttributeError(MayaObjectError, AttributeError):
    _objectDescription = 'Attribute'

class MayaAttributeEnumError(MayaAttributeError):
    _objectDescription = 'Attribute Enum'
    def __init__(self, node=None, enum=None):
        super(MayaAttributeEnumError, self).__init__(node)
        self.enum = enum
    def __str__(self):
        msg = super(MayaAttributeEnumError, self).__str__()
        if self.enum:
            msg += " - %r" % (self.enum)
        return msg

class MayaComponentError(MayaAttributeError):
    _objectDescription = 'Component'

def _objectError(objectName):
    # TODO: better name parsing
    if '.' in objectName:
        return MayaAttributeError(objectName)
    return MayaNodeError(objectName)

#--------------------------
# Object Wrapper Classes
#--------------------------

class PyNode(_util.ProxyUnicode):
    """
    Abstract class that is base for all pymel nodes classes.

    The names of nodes and attributes can be passed to this class, and the appropriate subclass will be determined.

        >>> PyNode('persp')
        nt.Transform(u'persp')
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
                elif isinstance( argObj, Component ):
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

                            # There are some names which are both components and
                            #    attributes: ie, scalePivot / rotatePivot
                            # toApiObject (and MSelectionList) will return the
                            #    component in these ambigious cases; therefore,
                            #    if we're explicitly trying to make an Attribute - ie,
                            #        Attribute('myCube.scalePivot')
                            #    ... make sure to cast it to one in these cases
                            if issubclass(cls, Attribute) and \
                                    isinstance(argObj, _api.MObject) and \
                                    _api.MFnComponent().hasObj(argObj) and \
                                    '.' in name:
                                attrName = name.split('.', 1)[1]
                                if attrNode.hasAttr(attrName):
                                    return attrNode.attr(attrName)
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
            if validComponentIndexType(argObj):
                #pymelType, obj, name = _getPymelType( attrNode._apiobject )
                obj = {'ComponentIndex' : argObj }
                # if we are creating a component class using an int or slice, then we must specify a class type:
                #    valid:    MeshEdge( myNode, 2 )
                #    invalid:  PyNode( myNode, 2 )
                assert issubclass(cls,Component), "%s is not a Component class" % cls.__name__

            #-- All Others
            else:
                pymelType, obj = _getPymelType( argObj, name )
                if attrNode is None and issubclass(pymelType, Attribute):
                    attrNode = PyNode(obj['MPlug'].name().split('.')[0])

            #print pymelType, obj, name, attrNode

            # Virtual (non-existent) objects will be cast to their own virtual type.
            # so, until we make that, we're rejecting them
            assert obj is not None# real objects only
            #assert obj or name

        else :
            # create node if possible
            if issubclass(cls,nodetypes.DependNode):
                newNode = None
                vClassInfo = _factories.virtualClasses.getVirtualClassInfo(cls)
                #----------------------------------
                # Pre Creation
                #----------------------------------
                postArgs = {}
                if vClassInfo and vClassInfo.preCreate:
                    kwargs = vClassInfo.preCreate(**kwargs)
                    if isinstance(kwargs, tuple):
                        assert len(kwargs) == 2, "preCreate must either 1 or 2 dictionaries of keyword arguments"
                        kwargs, postArgs = kwargs
                        assert isinstance(postArgs, dict), "preCreate second return value must be a dictionary of keyword arguments"
                    assert isinstance(kwargs, dict), "_preCreateVirtual must return a dictionary of keyword arguments"

                #----------------------------------
                # Creation
                #----------------------------------
                if vClassInfo and vClassInfo.create:
                    newNode = vClassInfo.create(**kwargs)
                    assert isinstance(newNode, basestring), "_createVirtual must return the name created node"

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
                    if vClassInfo and vClassInfo.postCreate:
                        vClassInfo.postCreate(newNode, **postArgs)
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
                if issubclass( cls, Component ):
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
        """Special method for returning a mel-friendly representation."""
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

    def stripNamespace(self, *args, **kwargs):
        """
        Returns the object's name with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.

        :rtype: `other.NameParser`

        """
        import other
        return other.NameParser(self).stripNamespace(*args, **kwargs)

    def swapNamespace(self, prefix):
        """Returns the object's name with its current namespace replaced with the provided one.
        The calling instance is unaffected.

        :rtype: `other.NameParser`
        """
        import other
        return other.NameParser(self).swapNamespace(prefix)

    def namespaceList(self):
        """Useful for cascading references.  Returns all of the namespaces of the calling object as a list

        :rtype: `unicode` list
        """
        return self.lstrip('|').rstrip('|').split('|')[-1].split(':')[:-1]

    def namespace(self, root=False):
        """Returns the namespace of the object with trailing colon included.
        
        See `DependNode.parentNamespace` for a variant which does not include
        the trailing colon.

        By default, if the object is in the root namespace, an empty string is
        returned; if root is True, ':' is returned in this case.

        :rtype: `unicode`

        """
        ns = self.parentNamespace()
        if ns or root:
            ns += ':'
        return ns

    def addPrefix(self, prefix):
        """Returns the object's name with a prefix added to the beginning of the name

        :rtype: `other.NameParser`
        """
        import other
        return other.NameParser(self).addPrefix(prefix)


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

    def listSets(self, *args, **kwargs):
        '''
        Returns list of sets this object belongs

        listSets -o $this

        :rtype: 'PyNode' list
        '''
        return listSets(o=self, *args, **kwargs)


    listConnections = listConnections

    connections = listConnections

    listHistory = listHistory

    history = listHistory

    listFuture = listFuture

    future = listFuture

# This was supposed to be removed in the 1.0 update, but somehow got left out...
deprecated_str_methods = ['__getitem__']
strDeprecateDecorator = _warnings.deprecated( 'Convert to string first using str() or PyNode.name()', 'PyNode' )

def _deprecatePyNode():
    def makeDeprecatedMethod(method):
        def f(self, *args):
            proxyMethod = getattr( _util.ProxyUnicode, method )
            return proxyMethod(self,*args)

        f.__doc__ = "deprecated\n"
        f.__name__ = method
        g = strDeprecateDecorator(f)
        setattr( PyNode, method, g)


    for method in deprecated_str_methods:
        makeDeprecatedMethod( method )

_deprecatePyNode()


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

def _getParent( getter, obj, generations):
    '''If generations is None, then a list of all the parents is returned.
    '''
    if generations == 0:
        return obj

    x = obj
    allParents = [obj]
    if generations is None:
        i = -1
    else:
        i = generations

    # If generations is positive, we will stop as soon as we get to the parent
    # we need; otherwise, we will get all the parents
    while i != 0:
        try:
            x = getter( x )
        except Exception:
            break
        if x is None:
            break
        allParents.append(x)
        i -= 1

    if generations is None:
        return allParents[1:]

    if generations >= 1:
        if generations < len(allParents):
            return allParents[generations]
        else:
            return None
    elif generations < 0:
        if -generations > len(allParents):
            return None
        else:
            return allParents[generations]

class Attribute(PyNode):
    """Attribute class

    see pymel docs for details on usage
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

        >>> from pymel.core import *
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
        >>> # use `Vector.isEquivalent` or cast the list to a `list`
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
        [nt.Transform(u'testCube')]
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

    def __apimattr__(self) :
        "Return the MFnAttribute for this attribute, if it is valid"
        try:
            if 'MFnAttribute' not in self.__apiobjects__:
                self.__apiobjects__['MFnAttribute'] = _api.MFnAttribute(self.__apimobject__())
            return self.__apiobjects__['MFnAttribute']
        except Exception:
            raise MayaAttributeError


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
        except MayaAttributeError:
            raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
    # Added the __call__ so to generate a more appropriate exception when a class method is not found
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" % (repr(self.node()), self.plugAttr()))

    # Need an iterator which is NOT self, so that we can have independent
    # iterators - ie, so if we do:
    #     zip(self, self)
    # we get
    #     ( (self[0], self[0]), (self[1], self[1]), (self[2], self[2]) ... )
    # and not
    #     ( (self[0], self[1]), (self[2], self[3]), (self[4], self[5]) ... )
    def __iter__(self):
        """
        iterator for multi-attributes

            >>> from pymel.core import *
            >>> f=newFile(f=1) #start clean
            >>>
            >>> at = PyNode( 'defaultLightSet.dagSetMembers' )
            >>> nt.SpotLight()
            nt.SpotLight(u'spotLightShape1')
            >>> nt.SpotLight()
            nt.SpotLight(u'spotLightShape2')
            >>> nt.SpotLight()
            nt.SpotLight(u'spotLightShape3')
            >>> for x in at: print x
            ...
            defaultLightSet.dagSetMembers[0]
            defaultLightSet.dagSetMembers[1]
            defaultLightSet.dagSetMembers[2]
        """
        if self.isMulti():
            for i in self._getArrayIndices()[1]:
                yield self[i]
            #return self[0]
        else:
            raise TypeError, "%s is not a multi-attribute and cannot be iterated over" % self

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

    def name(self, includeNode=True, longName=True, fullAttrPath=False,
             fullDagPath=False, placeHolderIndices=True):
        """ Returns the name of the attribute (plug)

            >>> tx = SCENE.persp.t.tx
            >>> tx.name()
            u'persp.translateX'
            >>> tx.name(includeNode=False)
            u'translateX'
            >>> tx.name(longName=False)
            u'persp.tx'
            >>> tx.name(fullAttrPath=True, includeNode=False)
            u'translate.translateX'

            >>> vis = SCENE.perspShape.visibility
            >>> vis.name()
            u'perspShape.visibility'
            >>> vis.name(fullDagPath=True)
            u'perspShape.visibility'

            >>> og = SCENE.persp.instObjGroups.objectGroups
            >>> og.name()
            u'persp.instObjGroups[-1].objectGroups'
            >>> og.name(placeHolderIndices=False)
            u'persp.instObjGroups.objectGroups'

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


            name += obj.partialName(    False, #includeNodeName
                                        True, #includeNonMandatoryIndices
                                        True, #includeInstancedIndices
                                        False, #useAlias
                                        fullAttrPath, #useFullAttributePath
                                        longName #useLongNames
                                    )
            if not placeHolderIndices:
                name  = name.replace('[-1]', '')
            return name
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
        # we shouldn't have to use this
        #if self._node is None:
        #    self._node = PyNode(self.__apimplug__().node())

        return self._node

    node = plugNode

    def plugAttr(self, longName=False, fullPath=False):
        """
            >>> from pymel.core import *
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
            >>> from pymel.core import *
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
            >>> from pymel.core import *
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
            >>> from pymel.core import *
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

    def attrName( self, longName=False, includeNode=False ):
        """Just the name of the attribute for this plug

        This will have no indices, no parent attributes, etc...
        This is suitable for use with cmds.attributeQuery

            >>> at = SCENE.persp.instObjGroups.objectGroups
            >>> at.name()
            u'persp.instObjGroups[-1].objectGroups'
            >>> at.attrName()
            u'og'
            >>> at.attrName(longName=True)
            u'objectGroups'
        """
        # Need to implement this with MFnAttribute - anything
        # with MPlug will have the [-1]...
        attr = self.__apimattr__()
        if longName:
            name = attr.name()
        else:
            name = attr.shortName()
        if includeNode:
            name = self.nodeName() + '.' + name
        return name

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

        Modifications:
          - returns an empty list when the result is None
        """
        if self.isElement():
            arrayAttr = self.array()
        else:
            arrayAttr = self
        return _util.listForNone(cmds.listAttr(arrayAttr, multi=True))

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

        Be aware that ``getAttr(..., size=1)`` does not always produce the expected value. It is recommend
        that you use `Attribute.numElements` instead.  This is a maya bug, *not* a pymel bug.

            >>> from pymel.core import *
            >>> f=newFile(f=1) #start clean
            >>>
            >>> dls = SCENE.defaultLightSet
            >>> dls.dagSetMembers.numElements()
            0
            >>> nt.SpotLight() # create a light, which adds to the lightSet
            nt.SpotLight(u'spotLightShape1')
            >>> dls.dagSetMembers.numElements()
            1
            >>> nt.SpotLight() # create another light, which adds to the lightSet
            nt.SpotLight(u'spotLightShape2')
            >>> dls.dagSetMembers.numElements()
            2

        :rtype: `int`
        """

        try:
            return self._getArrayIndices()[0]
        except RuntimeError:
            raise TypeError, "%s is not an array (multi) attribute" % self

    item = _factories.wrapApiMethod( _api.MPlug, 'logicalIndex', 'item' )
    index = _factories.wrapApiMethod( _api.MPlug, 'logicalIndex', 'index' )

    # enums
    getEnums = getEnums
    setEnums = setEnums

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

            >>> from pymel.core import *
            >>> SCENE.persp.tx >> SCENE.top.tx  # connect
            >>> SCENE.persp.tx // SCENE.top.tx  # disconnect
        """
        return connectAttr( self, other, force=True )

    disconnect = disconnectAttr

    def __floordiv__(self, other):
        """
        operator for 'disconnectAttr'

            >>> from pymel.core import *
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
    
    def setDirty(self, **kwargs):
        cmds.dgdirty(self, **kwargs)
        
    def evaluate(self, **kwargs):
        cmds.dgeval(self, **kwargs)

    def affects( self, **kwargs ):
        rawResult = cmds.affects( self.plugAttr(), self.node() )
        if not rawResult:
            return []
        return [Attribute( '%s.%s' % ( self.node(), x )) for x in rawResult]

    def affected( self, **kwargs ):
        rawResult = cmds.affects( self.plugAttr(), self.node(), by=True  )
        if not rawResult:
            return []
        return [Attribute( '%s.%s' % ( self.node(), x )) for x in rawResult]

    class  _TempRealIndexedAttr(object):
        '''When used with the 'with statement', will return a 'sibling' of the
        whose indices all exist - creating indices if needed.

        If any indices are created, they will be destroyed in exit.
        '''
        def __init__(self, attr):
            self.origAttr = attr

            # indexed attrs whose indice we have created, and will need to
            # delete when done
            self.toDelete = None

        def _getRealIndexedElem(self, plug, i):
            parent = self.chain[i - 1]
            indices = parent.getArrayIndices()
            if plug.index() in indices:
                return plug
            if indices:
                #print "plug didn't exist, but parent had existing indices..."
                return parent[indices[0]]
            # Because it was the Great One's number...
            newPlug = parent[99]
            #print "plug didn't exist, parent had no existing indices..."
            try:
                # this should create a 'real' instance at that index
                newPlug.get()
            except Exception:
                pass

            self.chain[i] = newPlug
            # Only need to delete the 'topmost' plug
            if self.toDelete is None:
                self.toDelete = newPlug

        def __enter__(self):
            self.chain = self.origAttr.getAllParents(arrays=True)
            self.chain.reverse()
            self.chain.append(self.origAttr)

            # traverse, starting from upper-most parent, as we may need to
            # replace children with 'real' ones as we go down
            for i in xrange(len(self.chain)):
                #print 'processing:', i
                elem = self.chain[i]
                if self.toDelete:
                    #print 'need new plug due to upstream change'
                    # We've already had to make a new attribute upstream,
                    # which means we need to grab a 'new' object for every
                    # element downstream.
                    if elem.isChild():
                        newPlug = self.chain[i-1].attr(elem.attrName())
                        self.chain[i] = newPlug
                    elif elem.isElement():
                        self._getRealIndexedElem(elem, i)
                elif elem.isElement():
                    self._getRealIndexedElem(elem, i)
            return self.chain[-1]

        def __exit__(self, type, value, traceback):
            if self.toDelete is not None:
                cmds.removeMultiInstance(self.toDelete.name())

    # getAttr info methods
    def type(self):
        """
        getAttr -type

        :rtype: `unicode`
        """
        # Note - currently, this returns 'TdataCompound' even for multi,
        # NON-compound attributes, if you feed it the array plug (ie, not
        # an indexed element plug)
        # Not sure this is really desirable, but changing would be backward
        # incompatible... revisit this later?
        with self._TempRealIndexedAttr(self) as realAttr:
            res = cmds.getAttr(realAttr.name(), type=True)
            if res:
                return res
            # Sometimes getAttr seems to fail with dynamic attributes...
            if realAttr.isDynamic():
                at = cmds.addAttr(realAttr.name(), q=1, attributeType=1)
                if isinstance(at, (list, tuple)):
                    at = at[0]
                if at != 'typed':
                    return at
                dt = cmds.addAttr(realAttr.name(), q=1, dataType=1)
                if isinstance(dt, (list, tuple)):
                    dt = dt[0]
                return dt

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
        # use MPlug.isFreeToChange, as it doesn't have the issues that getAttr
        # does with multi-compound attributes with no indices existing
        #return cmds.getAttr(self.name(placeHolderIndices=False), settable=True)
        return self.__apimplug__().isFreeToChange() == _api.MPlug.kFreeToChange

    # attributeQuery info methods
    def isHidden(self):
        """
        attributeQuery -hidden

        :rtype: `bool`
        """
        return cmds.attributeQuery(self.attrName(), node=self.node(), hidden=True)

    def isConnectable(self):
        """
        attributeQuery -connectable

        :rtype: `bool`
        """
        return cmds.attributeQuery(self.attrName(), node=self.node(), connectable=True)
    def isUsedAsColor(self):
        """
        attributeQuery -usedAsColor
        """
        return cmds.attributeQuery(self.attrName(), node=self.node(),uac=True)


    def indexMatters(self):
        return self.__apimattr__().indexMatters()

    isMulti = _factories.wrapApiMethod( _api.MPlug, 'isArray', 'isMulti' )


    def exists(self):
        """
        Whether the attribute actually exists.

        In spirit, similar to 'attributeQuery -exists'...
        ...however, also handles multi (array) attribute elements, such as plusMinusAverage.input1D[2]

        :rtype: `bool`
        """
        if not self.node().exists():
            return False

        if self.isElement():
            arrayExists = self.array().exists()
            if not arrayExists:
                return False

            # If the array exists, now check the array indices...
            indices = self.array().getArrayIndices()
            return bool(indices and self.index() in indices)
        elif self.isChild():
            # attributeQuery doesn't handle multi-compound attributes well...
            # so need to traverse all the way up the parent chain
            return self.parent().exists()
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

            >>> from pymel.core import *
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


#        # first find out what connections are going into and out of the object
#        ins = self.inputs(p=1)
#        outs = self.outputs(p=1)
#
#        # get the current value of the attr
#        val = self.get()
#
#        # break the connections if they exist
#        self.disconnect()

        # MIN
        # if 'default' is passed, we retain the current value
        if newMin == 'default':
            pass
        elif newMin is None:
            if limitType == 'hard':
                addAttr(self, edit=1, hasMinValue=False)
            else:
                addAttr(self, edit=1, hasSoftMinValue=False)
        else:
            if limitType == 'hard':
                addAttr(self, edit=1, minValue=newMin)
            else:
                addAttr(self, edit=1, softMinValue=newMin)


        # MAX
        # if 'default' is passed, we retain the current value
        if newMax == 'default':
            pass
        elif newMax is None:
            if limitType == 'hard':
                addAttr(self, edit=1, hasMaxValue=False)
            else:
                addAttr(self, edit=1, hasSoftMaxValue=False)
        else:
            if limitType == 'hard':
                addAttr(self, edit=1, maxValue=newMax)
            else:
                addAttr(self, edit=1, softMaxValue=newMax)


#        # set the value to be what it used to be
#        self.set(val)
#
#        # remake the connections
#        for conn in ins:
#            conn >> self
#
#        for conn in outs:
#            self >> outs


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
        """
        attributeQuery -listSiblings

        :rtype: `Attribute` list
        """
        try:
            return self.getParent().getChildren()
        except:
            pass
    siblings = getSiblings

    @_warnings.deprecated('use Attribute.getParent instead', 'Attribute')
    def firstParent(self):
        "deprecated: use getParent instead"

        try:
            return Attribute( self.node(), self.__apimfn__().parent() )
        except:
            pass

    @staticmethod
    def _getAttrParent(plug):
        if plug.isChild():
            return plug.parent()
        else:
            return None

    @staticmethod
    def _getAttrOrMultiParent(plug):
        if plug.isChild():
            return plug.parent()
        elif plug.isElement():
            return plug.array()
        else:
            return None


    def getParent(self, generations=1, arrays=False):
        """
        Modifications:
            - added optional generations keyword arg, which gives the number of
              levels up that you wish to go for the parent

              Negative values will traverse from the top.

              A value of 0 will return the same node.
              The default value is 1.

              If generations is None, it will be interpreted as 'return all
              parents', and a list will be returned.

              Since the original command returned None if there is no parent,
              to sync with this behavior, None will be returned if generations
              is out of bounds (no IndexError will be thrown).

            - added optional arrays keyword arg, which if True, will also
              traverse from an array element to an array plug

        :rtype: `Attribute`
        """
        if arrays:
            getter = self._getAttrOrMultiParent
        else:
            getter = self._getAttrParent

        res = _getParent(getter, self.__apimfn__(), generations)
        if generations is None:
            if res is None:
                return []
            return [Attribute(self.node(), x) for x in res]
        elif res is not None:
            return Attribute( self.node(), res )

    def getAllParents(self, arrays=False):
        """
        Return a list of all parents above this.

        Starts from the parent immediately above, going up.

        :rtype: `Attribute` list
        """
        return self.getParent(generations=None, arrays=arrays)

    parent = getParent

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

def _formatSlice(sliceObj):
    startIndex, stopIndex, step = sliceObj.start, sliceObj.stop, sliceObj.step
    if startIndex == stopIndex:
        sliceStr = '%s' % startIndex
    elif step is not None and step != 1:
        sliceStr = '%s:%s:%s' % (startIndex, stopIndex, step)
    else:
        sliceStr = '%s:%s' % (startIndex, stopIndex)
    return sliceStr


ProxySlice = _util.proxyClass( slice, 'ProxySlice', dataAttrName='_slice', makeDefaultInit=True)
# prevent auto-completion generator from getting confused
ProxySlice.__module__ = __name__

# Really, don't need to have another class inheriting from
# the proxy class, but do this so I can define a method using
# normal class syntax...
class HashableSlice(ProxySlice):
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

class Component( PyNode ):
    """
    Abstract base class for pymel components.
    """

    __metaclass__ = _factories.MetaMayaComponentWrapper
    _mfncompclass = _api.MFnComponent
    _apienum__ = _api.MFn.kComponent
    _ComponentLabel__ = None

    # Maya 2008 and earlier have no kUint64SingleIndexedComponent /
    # MFnUint64SingleIndexedComponent...
    _componentEnums = [_api.MFn.kComponent,
                       _api.MFn.kSingleIndexedComponent,
                       _api.MFn.kDoubleIndexedComponent,
                       _api.MFn.kTripleIndexedComponent]

    if hasattr(_api.MFn, 'kUint64SingleIndexedComponent'):
        _hasUint64 = True
        _componentEnums.append(_api.MFn.kUint64SingleIndexedComponent)
    else:
        _hasUint64 = False


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
#        selList = _api.MSelectionList()
#        selList.add(melSphere + '.cv[*][*]')
#        compObj = _api.MObject()
#        dagPath = _api.MDagPath()
#        selList.getDagPath(0, dagPath, compObj)
#        mfnComp = _api.MFnDoubleIndexedComponent(compObj)
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

        mfnComp = _api.MFnComponent(mobj)
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
            self._node = PyNode(dag)
        assert(self._node)

        # Need to do indices checking even for non-dimensional
        # components, because the ComponentIndex might be used to
        # specify the 'flavor' of the component - ie, 'scalePivot' or
        # 'rotatePivot' for Pivot components
        self._indices = self.__apiobjects__.get('ComponentIndex', None)

        if self._indices:
            if _util.isIterable(self._ComponentLabel__):
                oldCompLabel = set(self._ComponentLabel__)
            else:
                oldCompLabel = set( (self._ComponentLabel__,) )
            if isinstance(self._indices, dict):
                if len(self._indices) > 1:
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
        if _api.isValidMObjectHandle( handle ) :
            return handle.object()
        # Can't use self.name(), as that references this!
        raise MayaObjectError( self._completeNameString() )

    def __apiobject__(self) :
        return self.__apimobject__()

    def __apihandle__(self) :
        if 'MObjectHandle' not in self.__apiobjects__:
            handle = self._makeComponentHandle()
            if not handle or not _api.isValidMObjectHandle(handle):
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

    def __nonzero__(self):
        """
        :rtype: `bool`
        """
        return bool(len(self))

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
                if not _api.isValidMObject(component):
                    component = None

        # that didn't work - try checking if we have a valid plugAttr
        if not component and self.plugAttr():
            try:
                component = _api.toApiObject(self._completeNameString())[1]
            except:
                pass
            else:
                if not _api.isValidMObject(component):
                    component = None

        # component objects we create always start out 'complete'
        mfnComp = self._mfncompclass(component)
        mfnComp.setComplete(True)

        return _api.MObjectHandle(component)

    def __melobject__(self):
        selList = _api.MSelectionList()
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
        indices = self._standardizeIndices(self._indices)
        handle = self._makeIndexedComponentHandle(indices)
        return handle

    def _makeIndexedComponentHandle(self, indices):
        """
        Returns an MObjectHandle that points to a maya component object with
        the given indices.
        """
        selList = _api.MSelectionList()
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
                raise MayaComponentError(compName)
        compMobj = _api.MObject()
        dagPath = _api.MDagPath()
        selList.getDagPath(0, dagPath, compMobj)
        return _api.MObjectHandle(compMobj)

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
        elif isinstance(indexObjs, ComponentIndex):
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
        elif allowIterable and _util.isIterable(indexObjs):
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
            elif _util.isIterable(dimIndex):
                if allowIterable:
                    newIndices = []
                    for oldPartial in indices:
                        for indice in dimIndex:
                            newIndices.append(oldPartial + (indice,))
                    indices = newIndices
                else:
                    raise IndexError(index)
            elif isinstance(dimIndex, (float, int, long)) and dimIndex < 0:
                indices = [x + (self._translateNegativeIndice(dimIndex,x),)
                           for x in indices]
            else:
                indices = [x + (dimIndex,) for x in indices]
        return indices

    def _translateNegativeIndice(self, negIndex, partialIndex):
        raise NotImplementedError
        assert negIndex < 0
        self._dimLength

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
        if allowIterables and _util.isIterable(item):
            for x in item:
                self._validateGetItemIndice(x, allowIterables=False)
            return
        if not isinstance(item, self.VALID_SINGLE_INDEX_TYPES):
            raise IndexError("Invalid indice type for %s: %r" %
                             (self.__class__.__name__,
                              item.__class__.__name__) )
        if isinstance(item, (slice, HashableSlice)):
            if item.step and item.step < 0:
                raise IndexError("Components do not support slices with negative steps")
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

    def __repr__(self):
        return "%s(%s, label=%r)" % (self.__class__.__name__,
                                     super(ComponentIndex, self).__repr__(),
                                     self.label)

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
        for value in argObj.itervalues():
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
            if mayaArrays:
                mfnComp.addElements(*mayaArrays)
            return handle
        else:
            return super(DiscreteComponent, self)._makeIndexedComponentHandle(indices)

    @classmethod
    def _pyArrayToMayaArray(cls, pythonArray):
        mayaArray = _api.MIntArray()
        _api.MScriptUtil.createIntArrayFromList( list(pythonArray), mayaArray)
        return mayaArray

    def _dimRange(self, partialIndex):
        dimLen = self._dimLength(partialIndex)
        return (-dimLen, dimLen - 1)

    def _translateNegativeIndice(self, negIndex, partialIndex):
        assert negIndex < 0
        return self._dimLength(partialIndex) + negIndex

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
        for _ in xrange(self.dimensions):
            dimensionIndicePtrs.append(_api.SafeApiPtr('int'))

        for flatIndex in xrange(len(self)):
            mfncomp.getElement(flatIndex, *[x() for x in dimensionIndicePtrs])
            yield ComponentIndex( [x.get() for x in dimensionIndicePtrs] )

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
        '''Returns the current 'flat list' index for this group of components -
        ie, if this component holds the vertices:
            [5, 7, 12, 13, 14, 25]
        then if the 'flat list' index is 2, then we are pointing to vertex 12.
        '''
        return self._currentFlatIndex

    def currentItem(self):
        # This code duplicates much of _flatIter - keeping both
        # for speed, as _flatIter may potentially have to plow through a lot of
        # components, so we don't want to make an extra function call...

        dimensionIndicePtrs = []
        mfncomp = self.__apicomponent__()
        for _ in xrange(self.dimensions):
            dimensionIndicePtrs.append(_api.SafeApiPtr('int'))

        mfncomp.getElement(self._currentFlatIndex, *[x() for x in dimensionIndicePtrs])
        curIndex = ComponentIndex( [x.get() for x in dimensionIndicePtrs] )
        return self.__class__(self._node, curIndex)

    def currentItemIndex(self):
        '''Returns the component indices for the current item in this component
        group

        If the component type has more then one dimension, the return result
        will be a ComponentIndex object which is a sub-class of tuple; otherwise,
        it will be a single int.

        These values correspond to the indices that you would use when selecting
        components in mel - ie, vtx[5], cv[3][2]
        '''
        # Again, duplicates some code in currentItem/_flatIter for speed
        dimensionIndicePtrs = []
        mfncomp = self.__apicomponent__()
        for _ in xrange(self.dimensions):
            dimensionIndicePtrs.append(_api.SafeApiPtr('int'))

        mfncomp.getElement(self._currentFlatIndex, *[x() for x in dimensionIndicePtrs])
        if self.dimensions == 1:
            return dimensionIndicePtrs[0].get()
        else:
            return ComponentIndex( [x.get() for x in dimensionIndicePtrs] )

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
            raise MayaComponentError("%ss may not use slice-indices with a 'step' -  bad slice: %s" %
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

    def _translateNegativeIndice(self, negIndex, partialIndex):
        return negIndex

class Component1DFloat( ContinuousComponent ):
    dimensions = 1

class Component2DFloat( ContinuousComponent ):
    dimensions = 2

class Component1D( DiscreteComponent ):
    _mfncompclass = _api.MFnSingleIndexedComponent
    _apienum__ = _api.MFn.kSingleIndexedComponent
    dimensions = 1

    @staticmethod
    def _sequenceToComponentSlice( array ):
        """given an array, convert to a maya-formatted slice"""

        return [ HashableSlice( x.start, x.stop-1, x.step) for x in _util.sequenceToSlices( array ) ]


    def name(self):
        # this function produces a name that uses extended slice notation, such as vtx[10:40:2]
        melobj = self.__melobject__()
        if isinstance(melobj, basestring):
            return melobj
        else:
            compSlice = self._sequenceToComponentSlice( self.indicesIter() )
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

    def currentItemIndex(self):
        '''Returns the component indices for the current item in this component
        group

        If the component type has more then one dimension, the return result
        will be a ComponentIndex object which is a sub-class of tuple; otherwise,
        it will be a single int.

        These values correspond to the indices that you would use when selecting
        components in mel - ie, vtx[5], cv[3][2]
        '''
        # Again, duplicates some code in currentItem/_flatIter for speed
        mfncomp = self.__apicomponent__()
        return mfncomp.element(self._currentFlatIndex)

    def indicesIter(self):
        """
        An iterator over all the indices contained by this component,
        as integers.
        """
        for compIndex in self._compIndexObjIter():
            yield compIndex[0]

class Component2D( DiscreteComponent ):
    _mfncompclass = _api.MFnDoubleIndexedComponent
    _apienum__ = _api.MFn.kDoubleIndexedComponent
    dimensions = 2

class Component3D( DiscreteComponent ):
    _mfncompclass = _api.MFnTripleIndexedComponent
    _apienum__ = _api.MFn.kTripleIndexedComponent
    dimensions = 3

# Mixin class for components which use MIt* objects for some functionality
class MItComponent( Component ):
    """
    Abstract base class for pymel components that can be accessed via iterators.

    (ie, `MeshEdge`, `MeshVertex`, and `MeshFace` can be wrapped around
    MItMeshEdge, etc)

    If deriving from this class, you should set __apicls__ to an appropriate
    MIt* type - ie, for MeshEdge, you would set __apicls__ = _api.MItMeshEdge
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
        _mfncompclass = _api.MFnUint64SingleIndexedComponent
        _apienum__ = _api.MFn.kUint64SingleIndexedComponent

    else:
        _mfncompclass = _api.MFnComponent
        _apienum__ = _api.MFn.kComponent

    if Component._hasUint64 and hasattr(_api, 'MUint64'):
        # Note that currently the python api has zero support for MUint64's
        # This code is just here because I'm an optimist...
        @classmethod
        def _pyArrayToMayaArray(cls, pythonArray):
            mayaArray = _api.MUint64Array(len(pythonArray))
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
                if _util.isIterable(melStrings):
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

#-----------------------------------------
# Specific Components...
#-----------------------------------------


class MeshVertex( MItComponent1D ):
    __apicls__ = _api.MItMeshVertex
    _ComponentLabel__ = "vtx"
    _apienum__ = _api.MFn.kMeshVertComponent

    def _dimLength(self, partialIndex):
        return self.node().numVertices()

    def setColor(self,color):
        for i in self.indices():
            self.node().setVertexColor( color, i )

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def isConnectedTo(self, component):
        """
        pass a component of type `MeshVertex`, `MeshEdge`, `MeshFace`, with a single element

        :rtype: bool
        """
        if isinstance(component,MeshFace):
            return self.isConnectedToFace( component.currentItemIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.currentItemIndex() )
        if isinstance(component,MeshVertex):
            array = _api.MIntArray()
            self.__apimfn__().getConnectedVertices(array)
            return component.currentItemIndex() in [ array[i] for i in range( array.length() ) ]
        raise TypeError, 'type %s is not supported' % type(component)

    def getColor(self, *args, **kwargs):
        # Want all possible versions of this command, so easiest to just manually
        # wrap (particularly want to be able to invoke with no args!
        color = _api.MColor()
        self.__apimfn__().getColor(color, *args, **kwargs)
        return datatypes.Color(color)

class MeshEdge( MItComponent1D ):
    __apicls__ = _api.MItMeshEdge
    _ComponentLabel__ = "e"
    _apienum__ = _api.MFn.kMeshEdgeComponent

    def _dimLength(self, partialIndex):
        return self.node().numEdges()


    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

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
            return self.isConnectedToFace( component.currentItemIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.currentItemIndex() )
        if isinstance(component,MeshVertex):
            index0 = self.__apimfn__().index(0)
            index1 = self.__apimfn__().index(1)
            return component.currentItemIndex() in [index0, index1]

        raise TypeError, 'type %s is not supported' % type(component)

class MeshFace( MItComponent1D ):
    __apicls__ = _api.MItMeshPolygon
    _ComponentLabel__ = "f"
    _apienum__ = _api.MFn.kMeshPolygonComponent

    def _dimLength(self, partialIndex):
        return self.node().numFaces()

    def connectedEdges(self):
        """
        :rtype: `MeshEdge` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedEdges(array)
        return MeshEdge( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedFaces(self):
        """
        :rtype: `MeshFace` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedFaces(array)
        return MeshFace( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def connectedVertices(self):
        """
        :rtype: `MeshVertex` list
        """
        array = _api.MIntArray()
        self.__apimfn__().getConnectedVertices(array)
        return MeshVertex( self, self._sequenceToComponentSlice( [ array[i] for i in range( array.length() ) ] ) )

    def isConnectedTo(self, component):
        """
        :rtype: bool
        """
        if isinstance(component,MeshFace):
            return self.isConnectedToFace( component.currentItemIndex() )
        if isinstance(component,MeshEdge):
            return self.isConnectedToEdge( component.currentItemIndex() )
        if isinstance(component,MeshVertex):
            return self.isConnectedToVertex( component.currentItemIndex() )

        raise TypeError, 'type %s is not supported' % type(component)

class MeshUV( Component1D ):
    _ComponentLabel__ = "map"
    _apienum__ = _api.MFn.kMeshMapComponent

    def _dimLength(self, partialIndex):
        return self._node.numUVs()

class MeshVertexFace( Component2D ):
    _ComponentLabel__ = "vtxFace"
    _apienum__ = _api.MFn.kMeshVtxFaceComponent

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
            mIt = _api.MItMeshVertex(self._node.__apimdagpath__())

            # Even though we're not using the result stored in the int,
            # STILL need to store a ref to the MScriptUtil - otherwise,
            # there's a chance it gets garbage collected before the
            # api function call is made, and it writes the value into
            # the pointer...
            intPtr = _api.SafeApiPtr('int')
            mIt.setIndex(partialIndex[0], intPtr())
            intArray = _api.MIntArray()
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
        if allowIterables and _util.isIterable(item):
            for _ in item:
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
    _apienum__ = _api.MFn.kSubdivCVComponent

class SubdEdge( Component1D64 ):
    _ComponentLabel__ = "sme"
    _apienum__ = _api.MFn.kSubdivEdgeComponent

class SubdFace( Component1D64 ):
    _ComponentLabel__ = "smf"
    _apienum__ = _api.MFn.kSubdivFaceComponent

class SubdUV( Component1D ):
    _ComponentLabel__ = "smm"
    _apienum__ = _api.MFn.kSubdivMapComponent

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


    # ok - some weirdness in trying to find what the maximum
    # allowable smm index is...
    # To see what I mean, uncomment this and try it in maya:
#from pymel.core import *
#import sys
#import platform
#
#def testMaxIndex():
#
#
#    def interpreterBits():
#        """
#        Returns the number of bits of the architecture the interpreter was compiled on
#        (ie, 32 or 64).
#
#        :rtype: `int`
#        """
#        return int(re.match(r"([0-9]+)(bit)?", platform.architecture()[0]).group(1))
#
#    subdBase = polyCube()[0]
#    subdTrans = polyToSubdiv(subdBase)[0]
#    subd = subdTrans.getShape()
#    selList = _api.MSelectionList()
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), sys.maxint))
#    except:
#        print "sys.maxint (%d) failed..." % sys.maxint
#    else:
#        print "sys.maxint (%d) SUCCESS" % sys.maxint
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** interpreterBits() - 1))
#    except:
#        print "2 ** %d - 1 (%d) failed..." % (interpreterBits(), 2 ** interpreterBits() - 1)
#    else:
#        print "2 ** %d - 1 (%d) SUCCESS" % (interpreterBits(), 2 ** interpreterBits() - 1)
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** interpreterBits()))
#    except:
#        print "2 ** %d (%d) failed..." % (interpreterBits(), 2 ** interpreterBits())
#    else:
#        print "2 ** %d (%d) SUCCESS" % (interpreterBits(), 2 ** interpreterBits())
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** 31 - 1))
#    except:
#        print "2 ** 31 - 1 (%d) failed..." % (2 ** 31 - 1)
#    else:
#        print "2 ** 31 - 1 (%d) SUCCESS" % (2 ** 31 - 1)
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** 31))
#    except:
#        print "2 ** 31 (%d) failed..." % (2 ** 31)
#    else:
#        print "2 ** 31 (%d) SUCCESS" % (2 ** 31)
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** 32 - 1))
#    except:
#        print "2 ** 32 - 1 (%d) failed..." % (2 ** 32 - 1)
#    else:
#        print "2 ** 32 - 1 (%d) SUCCESS" % (2 ** 32 - 1)
#    try:
#        selList.add("%s.smm[0:%d]" % (subd.name(), 2 ** 32))
#    except:
#        print "2 ** 32 (%d) failed..." % (2 ** 32)
#    else:
#        print "2 ** 32 (%d) SUCCESS" % (2 ** 32)
#

    # On Windows XP x64, Maya2009x64, 2**64 -1 works (didn't try others at the time)
    # ...but on Linux Maya2009x64, and OSX Maya2011x64, I get this weirdness:
#sys.maxint (9223372036854775807) failed...
#2 ** 64 - 1 (18446744073709551615) failed...
#2 ** 64 (18446744073709551616) failed...
#2 ** 31 - 1 (2147483647) SUCCESS
#2 ** 31 (2147483648) failed...
#2 ** 32 - 1 (4294967295) failed...
#2 ** 32 (4294967296) SUCCESS

    # So, given the inconsistencies here, just going to use
    # 2**31 -1... hopefully nobody needs more uv's than that
    _MAX_INDEX = 2 ** 31 - 1
    _tempSel = _api.MSelectionList()
    _maxIndexRe = re.compile(r'\[0:([0-9]+)\]$')
    def _dimLength(self, partialIndex):
        # Fall back on good ol' string processing...
        # unfortunately, .smm[*] is not allowed -
        # so we have to provide a 'maximum' value...
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
    _apienum__ = _api.MFn.kCurveParamComponent

    def _dimRange(self, partialIndex):
        return self._node.getKnotDomain()

class NurbsCurveCV( MItComponent1D ):
    __apicls__ = _api.MItCurveCV
    _ComponentLabel__ = "cv"
    _apienum__ = _api.MFn.kCurveCVComponent

    def _dimLength(self, partialIndex):
        return self.node().numCVs()

class NurbsCurveEP( Component1D ):
    _ComponentLabel__ = "ep"
    _apienum__ = _api.MFn.kCurveEPComponent

    def _dimLength(self, partialIndex):
        return self.node().numEPs()

class NurbsCurveKnot( Component1D ):
    _ComponentLabel__ = "knot"
    _apienum__ = _api.MFn.kCurveKnotComponent

    def _dimLength(self, partialIndex):
        return self.node().numKnots()

## NurbsSurface Components

class NurbsSurfaceIsoparm( Component2DFloat ):
    _apienum__ = _api.MFn.kIsoparmComponent
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
    _apienum__ = _api.MFn.kSurfaceRangeComponent

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
    _apienum__ = _api.MFn.kSurfaceCVComponent

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
    _apienum__ = _api.MFn.kSurfaceEPComponent

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
    _apienum__ = _api.MFn.kSurfaceKnotComponent

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
    _apienum__ = _api.MFn.kSurfaceFaceComponent

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
    _apienum__ = _api.MFn.kLatticeComponent

    def _dimLength(self, partialIndex):
        if len(partialIndex) > 2:
            raise ValueError('partialIndex %r too long for %s._dimLength' %
                             (partialIndex, self.__class__.__name__))
        return self.node().getDivisions()[len(partialIndex)]


#-----------------------------------------
# Pivot Components
#-----------------------------------------

class Pivot( Component ):
    _apienum__ = _api.MFn.kPivotComponent
    _ComponentLabel__ = ("rotatePivot", "scalePivot")

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
    __metaclass__ = _factories.MetaMayaTypeWrapper
    __apicls__ = _api.MFnAttribute

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

    def name(self):
        return self.__apimfn__().name()


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
        nt.Transform(u'persp')
        >>> SCENE.persp.t
        Attribute(u'persp.translate')

    An instance of this class is provided for you with the name `SCENE`.
    """
    __metaclass__ = _util.Singleton
    def __getattr__(self, obj):
        if obj.startswith('__') and obj.endswith('__'):
            try:
                return self.__dict__[obj]
            except KeyError:
                raise AttributeError, "type object %r has no attribute %r" % (self.__class__.__name__, obj)

        return PyNode( obj )

SCENE = Scene()






_factories.createFunctions( __name__, PyNode )

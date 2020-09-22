"""
Functions and classes related to scripting, including `MelGlobals` and `Mel`
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import map
from builtins import range
from past.builtins import basestring
from builtins import object
from future.utils import PY2

import collections

# 2to3: remove switch when python-3 only
try:
    from collections.abc import Mapping, MutableMapping
except ImportError:
    from collections import Mapping, MutableMapping
import sys
import os
import inspect
from getpass import getuser as _getuser
from pymel.core import system

import maya.mel as _mm
import maya.cmds as _mc

import pymel.util as util
import pymel.internal.factories as _factories
import pymel.internal.cmdcache as _cmdcache
import pymel.core.datatypes as datatypes

if False:
    from typing import *
    from maya import cmds
    import maya.OpenMaya as _api
else:
    import pymel.api as _api
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]

# -------------------------
# Mel <---> Python Glue
# -------------------------

MELTYPES = ['string', 'string[]', 'int', 'int[]', 'float', 'float[]', 'vector',
            'vector[]']


def isValidMelType(typStr):
    # type: (Any) -> bool
    """Returns whether ``typeStr`` is a valid MEL type identifier

    Returns
    -------
    bool
    """
    return typStr in MELTYPES


def _flatten(iterables):
    for it in iterables:
        if util.isIterable(it):
            for element in it:
                yield element
        else:
            yield it


def pythonToMel(arg):
    # type: (str) -> str
    """
    convert a python object to a string representing an equivalent value in mel

    iterables are flattened.

    mapping types like dictionaries have their key value pairs flattened:
        { key1 : val1, key2 : val2 }  -- >  ( key1, val1, key2, val2 )

    """
    if arg is None:
        return ''
    if arg is True or arg is False:
        return str(arg).lower()
    if util.isNumeric(arg):
        return str(arg)
    if isinstance(arg, datatypes.Vector):
        return '<<%f,%f,%f>>' % (arg[0], arg[1], arg[2])
    if util.isIterable(arg):
        if isinstance(arg, Mapping):
            arg = list(_flatten(arg.items()))
        else:
            arg = list(_flatten(arg))
        forceString = False
        for each in arg:
            if not util.isNumeric(each):
                forceString = True
                break

        if forceString:
            newargs = ['"%s"' % x for x in arg]
        else:
            newargs = [str(x) for x in arg]

        return '{%s}' % ','.join(newargs)

    # in order for PyNodes to get wrapped in quotes we have to treat special
    # cases first, we cannot simply test if arg is an instance of basestring
    # because PyNodes are not
    return '"%s"' % cmds.encodeString(str(arg))


def pythonToMelCmd(command, *args, **kwargs):
    '''Given a mel command name, and a set of python args / kwargs, return
    a mel string used to call the given command.

    Note that the first member of commandAndArgs is the command name, and is
    required; the remainder are the args to it.  We use this odd signature to
    avoid any name conflicts with mel flag names - ie, the signature used to be:
        pythonToMelCmd(command, *args, **kwargs)
    but this caused problems with the mel "button" function, which has a
    "command" flag.
    '''
    _factories.loadCmdCache()
    strArgs = [pythonToMel(arg) for arg in args]

    if kwargs:
        # keyword args trigger us to format as a command rather than a procedure
        strFlags = []  # type: List[str]
        if command in _factories.cmdlist:
            flags = _factories.cmdlist[command]['flags']
            shortFlags = _factories.cmdlist[command]['shortFlags']
        else:
            #            # Make a dummy flags dict - basically, just assume that q / e
            #            # are bool flags with no args...
            #            flags = {'query':{'args': bool,
            #                              'longname': 'query',
            #                              'numArgs': 0,
            #                              'shortname': 'q'},
            #                     'edit': {'args': bool,
            #                              'longname': 'edit',
            #                              'numArgs': 0,
            #                              'shortname': 'e'}}
            #            shortFlags = {'q':'query', 'e':'edit'}
            # Changed my mind - decided it's safest for unknown commands to
            # make no assumptions.  If they want a flag that takes no args,
            # they can use arg=None...
            flags = {}
            shortFlags = {}
        for key, val in kwargs.items():
            flagInfo = None
            if key in flags:
                flagInfo = flags[key]
            elif key in shortFlags:
                flagInfo = flags[shortFlags[key]]
            if (flagInfo and flagInfo.get('args') == bool
                    and flagInfo.get('numArgs') == 0):
                # we have a boolean argument that takes no args!
                # doing something like '-q 1' will raise an error, just
                # do '-q'
                strFlags.append('-%s' % key)
            elif (isinstance(val, (tuple, list))
                    and len(val) == flagInfo.get('numArgs')):
                strFlags.append('-%s %s' %
                                (key, ' '.join(pythonToMel(x) for x in val)))
            else:
                strFlags.append('-%s %s' % (key, pythonToMel(val)))
        cmdStr = '%s %s %s' % (command, ' '.join(strFlags), ' '.join(strArgs))
    else:
        # procedure
        cmdStr = '%s(%s)' % (command, ','.join(strArgs))
    return cmdStr


def getMelType(pyObj, exactOnly=True, allowBool=False, allowMatrix=False):
    # type: (Any, bool, bool, bool) -> str
    """
    return the name of the closest MEL type equivalent for the given python
    object.

    MEL has no true boolean or matrix types, but it often reserves special
    treatment for them in other ways.

    To control the handling of these types, use `allowBool` and `allowMatrix`.
    For python iterables, the first element in the array is used to determine
    the type. for empty lists, 'string[]' is returned.

        >>> from pymel.all import *
        >>> getMelType( 1 )
        'int'
        >>> p = SCENE.persp
        >>> getMelType( p.translate.get() )
        'vector'
        >>> getMelType( datatypes.Matrix )
        'int[]'
        >>> getMelType( datatypes.Matrix, allowMatrix=True )
        'matrix'
        >>> getMelType( True )
        'int'
        >>> getMelType( True, allowBool=True)
        'bool'
        >>> # make a dummy class
        >>> class MyClass(object): pass
        >>> getMelType( MyClass ) # returns None
        >>> getMelType( MyClass, exactOnly=False )
        'MyClass'

    Parameters
    ----------
    pyObj
        can be either a class or an instance.
    exactOnly : bool
        If True and no suitable MEL analog can be found, the function will
        return None.
        If False, types which do not have an exact mel analog will return
        the python type name as a string
    allowBool : bool
        if True and a bool type is passed, 'bool' will be returned.
        otherwise 'int'.
    allowMatrix : bool
        if True and a `Matrix` type is passed, 'matrix' will be returned.
        otherwise 'int[]'.

    Returns
    -------
    str
    """

    if inspect.isclass(pyObj):

        if issubclass(pyObj, basestring):
            return 'string'
        elif allowBool and issubclass(pyObj, bool):
            return 'bool'
        elif issubclass(pyObj, int):
            return 'int'
        elif issubclass(pyObj, float):
            return 'float'
        elif issubclass(pyObj, datatypes.VectorN):
            return 'vector'
        elif issubclass(pyObj, datatypes.MatrixN):
            if allowMatrix:
                return 'matrix'
            else:
                return 'int[]'

        elif not exactOnly:
            return pyObj.__name__

    else:
        if isinstance(pyObj, datatypes.VectorN):
            return 'vector'
        elif isinstance(pyObj, datatypes.MatrixN):
            if allowMatrix:
                return 'matrix'
            else:
                return 'int[]'
        elif util.isIterable(pyObj):
            try:
                return getMelType(pyObj[0], exactOnly=True) + '[]'
            except IndexError:
                # TODO : raise warning
                return 'string[]'
            except:
                return
        if isinstance(pyObj, basestring):
            return 'string'
        elif allowBool and isinstance(pyObj, bool):
            return 'bool'
        elif isinstance(pyObj, int):
            return 'int'
        elif isinstance(pyObj, float):
            return 'float'

        elif not exactOnly:
            return type(pyObj).__name__


# TODO : convert array variables to a semi-read-only list ( no append or extend, += is ok ):
# using append or extend will not update the mel variable

# we only inherit from dict for backward-compatability...
if False:
    _Parent = object
else:
    # 2to3: need to use "true" dict object in python-2 to avoid metaclass issue
    _Parent = __builtins__['dict']


class MelGlobals(MutableMapping, _Parent):

    """ A dictionary-like class for getting and setting global variables between mel and python.

    An instance of the class is created by default in the pymel namespace as ``melGlobals``.

    To retrieve existing global variables, just use the name as a key:

    >>> melGlobals['gPanelLabels'] #doctest: +ELLIPSIS
    [...'Side View', ...]
    >>> # works with or without $
    >>> melGlobals['$gFilterUIDefaultAttributeFilterList']  #doctest: +ELLIPSIS
    ['DefaultHiddenAttributesFilter', 'animCurveFilter', ..., 'publishedFilter']

    Creating new variables requires the use of the `initVar` function to specify the type:

    >>> melGlobals.initVar('string', 'gMyStrVar')
    '$gMyStrVar'
    >>> melGlobals['gMyStrVar'] = 'fooey'

    The variable will now be accessible within MEL as a global string.
    """
    melTypeToPythonType = {
        'string': str,
        'int': int,
        'float': float,
        'vector': datatypes.Vector
    }

#    class MelGlobalArray1( tuple ):
#        def __new__(cls, type, variable, *args, **kwargs ):
#
#            self = tuple.__new__( cls, *args, **kwargs )
#
#            decl_name = variable
#            if type.endswith('[]'):
#                type = type[:-2]
#                decl_name += '[]'
#
#            self._setItemCmd = "global %s %s; %s" % ( type, decl_name, variable )
#            self._setItemCmd += '[%s]=%s;'
#            return self
#
#        def setItem(self, index, value ):
#            _mm.eval(self._setItemCmd % (index, value) )

    class MelGlobalArray(util.defaultlist):

        def __init__(self, type, variable, *args, **kwargs):

            if type.endswith('[]'):
                type = type[:-2]

            pyType = MelGlobals.melTypeToPythonType[type]
            util.defaultlist.__init__(self, pyType, *args, **kwargs)

            declaration = MelGlobals._get_decl_statement(type, variable)
            self._setItemCmd = "%s; %s" % (declaration, variable)
            self._setItemCmd += '[%s]=%s;'

        def __setitem__(self, index, value):
            _mm.eval(self._setItemCmd % (index, pythonToMel(value)))
            super(MelGlobals.MelGlobalArray, self).__setitem__(index, value)
        setItem = __setitem__

        def append(self, val):
            raise AttributeError

        def extend(self, val):
            raise AttributeError

    typeMap = {}  # type: Dict[str, str]
    VALID_TYPES = MELTYPES

    def __iter__(self):
        for varName in mel.env():
            yield varName

    def __len__(self):
        return len(mel.env())

    def __getitem__(self, variable):
        # type: (str) -> str
        """
        Parameters
        ----------
        variable : str

        Returns
        -------
        str
        """
        return self.__class__.get(variable)

    def __setitem__(self, variable, value):
        # type: (str, Any) -> Any
        """
        Parameters
        ----------
        variable : str
        value : Any

        Returns
        -------
        Any
        """
        return self.__class__.set(variable, value)

    @classmethod
    def _formatVariable(cls, variable):
        # type: (str) -> str
        """
        Parameters
        ----------
        variable : str

        Returns
        -------
        str
        """
        # TODO : add validity check
        if not variable.startswith('$'):
            variable = '$' + variable
        if variable.endswith('[]'):
            variable = variable[:-2]
        return variable

    @classmethod
    def getType(cls, variable):
        # type: (str) -> str
        """
        Get the type of a global MEL variable

        Parameters
        ----------
        variable : str

        Returns
        -------
        str
        """
        variable = cls._formatVariable(variable)
        info = mel.whatIs(variable).split()
        if len(info) == 2 and info[1] == 'variable':
            MelGlobals.typeMap[variable] = info[0]
            return info[0]
        raise TypeError("Cannot determine type for this variable. "
                        "Use melGlobals.initVar first.")

    @classmethod
    def _get_decl_statement(cls, type, variable):
        decl_name = cls._formatVariable(variable)
        if type.endswith('[]'):
            type = type[:-2]
            decl_name += '[]'
        return "global %s %s" % (type, decl_name)

    @classmethod
    def initVar(cls, type, variable):
        # type: (str, str) -> str
        """
        Initialize a new global MEL variable

        Parameters
        ----------
        type : str
            one of ``MELTYPES``
        variable : str

        Returns
        -------
        str
        """
        if type not in MELTYPES:
            raise TypeError("type must be a valid mel type: %s" %
                            ', '.join(["'%s'" % x for x in MELTYPES]))
        variable = cls._formatVariable(variable)
        _mm.eval(cls._get_decl_statement(type, variable))
        MelGlobals.typeMap[variable] = type
        return variable

    def get_dict(self, variable, default=None):
        return super(MelGlobals, self).get(variable, default)

    # this clashes with a standard dict's "get", which will not error if a dict
    # does not contain a key...
    # ...but because of backwards compatibility, not sure what to do...?
    # for now, making a separate "get_default" method that acts like dict.get...
    # ...but may want to switch this in the future...
    @classmethod
    def get(cls, variable, type=None):
        # type: (str, Optional[str]) -> Any
        """
        get a MEL global variable.

        If the type is not specified, the mel ``whatIs`` command will be used
        to determine it.

        Parameters
        ----------
        variable : str
        type : Optional[str]
            one of ``MELTYPES``

        Returns
        -------
        Any
        """

        variable = cls._formatVariable(variable)
        if type is None:
            try:
                type = MelGlobals.typeMap[variable]
            except KeyError:
                try:
                    type = cls.getType(variable)
                except TypeError:
                    raise KeyError(variable)

        variable = cls.initVar(type, variable)

        if type.endswith('[]'):
            array = True
            proc_name = 'pymel_get_global_' + type.replace('[]', 'Array')
        else:
            array = False
            proc_name = 'pymel_get_global_' + type
        declaration = cls._get_decl_statement(type, variable)
        cmd = "global proc %s %s() { %s; return %s; } %s();" % (type, proc_name, declaration, variable, proc_name)
        # print cmd
        res = _mm.eval(cmd)
        if array:
            return MelGlobals.MelGlobalArray(type, variable, res)
        else:
            return MelGlobals.melTypeToPythonType[type](res)

    @classmethod
    def set(cls, variable, value, type=None):
        # type: (str, Any, Optional[str]) -> None
        """
        set a mel global variable

        Parameters
        ----------
        variable : str
        value : Any
        type : Optional[str]
            one of ``MELTYPES``
        """
        variable = cls._formatVariable(variable)
        if type is None:
            try:
                type = MelGlobals.typeMap[variable]
            except KeyError:
                type = cls.getType(variable)

        variable = cls.initVar(type, variable)
        declaration = cls._get_decl_statement(type, variable)
        cmd = "%s; %s=%s;" % (declaration, variable, pythonToMel(value))

        # print cmd
        _mm.eval(cmd)

    @classmethod
    def keys(cls):
        # type: () -> List[str]
        """
        list all global variables

        Returns
        -------
        List[str]
        """
        return mel.env()


melGlobals = MelGlobals()


# for backward compatibility
def getMelGlobal(type, variable):
    return melGlobals.get(variable, type)


def setMelGlobal(type, variable, value):
    return melGlobals.set(variable, value, type)


class Catch(object):

    """Reproduces the behavior of the mel command of the same name. if writing
    pymel scripts from scratch, you should use the try/except structure. This
    command is provided for python scripts generated by py2mel.  stores the
    result of the function in catch.result.

    >>> if not catch( lambda: myFunc( "somearg" ) ):
    ...    result = catch.result
    ...    print("succeeded:", result)

    """
    result = None
    success = None

    def __call__(self, func, *args, **kwargs):
        try:
            Catch.result = func(*args, **kwargs)
            Catch.success = True
            return 0
        except:
            Catch.success = False
            return 1

    def reset(self):
        Catch.result = None
        Catch.success = None


catch = Catch()


class OptionVarList(tuple):

    def __new__(cls, val, key):
        self = tuple.__new__(cls, val)
        return self

    def __init__(self, val, key):
        # tuple's init is object.__init__, which takes no args...
        #tuple.__init__(self, val)
        self.key = key

    def __setitem__(self, key, val):
        raise TypeError('%s object does not support item assignment - try '
                        'casting to a list, and assigning the whole list to '
                        'the optionVar' % self.__class__.__name__)

    def appendVar(self, val):
        """values appended to the OptionVarList with this method will be added
        to the Maya optionVar at the key denoted by self.key.
        """

        if isinstance(val, basestring):
            return cmds.optionVar(stringValueAppend=[self.key, val])
        if isinstance(val, (int, int)):
            return cmds.optionVar(intValueAppend=[self.key, val])
        if isinstance(val, float):
            return cmds.optionVar(floatValueAppend=[self.key, val])
        raise TypeError('unsupported datatype: strings, ints, floats and '
                        'their subclasses are supported')

    append = appendVar

# PY2: when we switch to python3-only, change
#    print(numArray)
# to
#    print(numArray)
# The int conversion is needed because in python-2, the values would be longs,
# ie, [1L, 24L, 7L, 9L]
class OptionVarDict(MutableMapping):

    """
    A dictionary-like class for accessing and modifying optionVars.

        >>> from pymel.all import *
        >>> optionVar['test'] = 'dooder'
        >>> optionVar['test']
        'dooder'

        >>> if 'numbers' not in env.optionVars:
        ...     optionVar['numbers'] = [1,24,7]
        >>> optionVar['numbers'].appendVar( 9 )
        >>> numArray = optionVar.pop('numbers')
        >>> print([int(x) for x in numArray])
        [1, 24, 7, 9]
        >>> optionVar.has_key('numbers') # previous pop removed the key
        False
    """

    def __call__(self, *args, **kwargs):
        return cmds.optionVar(*args, **kwargs)

    # use more efficient method provided by cmds.optionVar
    # (or at least, I hope it's more efficient...)
    def __contains__(self, key):
        return bool(cmds.optionVar(exists=key))

    # not provided by MutableMapping
    def has_key(self, key):
        return self.__contains__(key)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        val = cmds.optionVar(q=key)
        if isinstance(val, list):
            val = OptionVarList(val, key)
        return val

    def __setitem__(self, key, val):
        if isinstance(val, basestring):
            return cmds.optionVar(stringValue=[key, val])
        if isinstance(val, (int, bool, int)):
            return cmds.optionVar(intValue=[key, int(val)])
        if isinstance(val, float):
            return cmds.optionVar(floatValue=[key, val])
        if isinstance(val, (list, tuple)):
            if len(val) == 0:
                return cmds.optionVar(clearArray=key)
            listType = type(val[0])
            if issubclass(listType, basestring):
                flag = 'stringValue'
            elif issubclass(listType, (int, int)):
                flag = 'intValue'
            elif issubclass(listType, float):
                flag = 'floatValue'
            else:
                raise TypeError('%r is unsupported; Only strings, ints, float, lists, and their subclasses are supported' % listType)

            cmds.optionVar(**{flag: [key, val[0]]})  # force to this datatype
            flag += "Append"
            for elem in val[1:]:
                if not isinstance(elem, listType):
                    raise TypeError('all elements in list must be of the same datatype')
                cmds.optionVar(**{flag: [key, elem]})

    def keys(self):
        return cmds.optionVar(list=True)

    def pop(self, key):
        val = cmds.optionVar(q=key)
        cmds.optionVar(remove=key)
        return val

    def __delitem__(self, key):
        self.pop(key)

    def iterkeys(self):
        for key in self.keys():
            yield key
    __iter__ = iterkeys

    def __len__(self):
        return len(self.keys())


optionVar = OptionVarDict()


class Env(object):

    """ A Singleton class to represent Maya current optionVars and settings """

    optionVars = OptionVarDict()
    # grid = Grid()
    # playbackOptions = PlaybackOptions()

    # TODO : create a wrapper for os.environ which allows direct appending
    # and popping of individual env entries (i.e. make ':' transparent)
    envVars = os.environ

    def setConstructionHistory(self, state):
        cmds.constructionHistory(tgl=state)

    def getConstructionHistory(self):
        return cmds.constructionHistory(q=True, tgl=True)

    def sceneName(self):
        return system.Path(cmds.file(q=1, sn=1))

    def setUpAxis(self, axis, rotateView=False):
        """This flag specifies the axis as the world up direction. The valid
        axis are either 'y' or 'z'."""
        cmds.upAxis(axis=axis, rotateView=rotateView)

    def getUpAxis(self):
        """This flag gets the axis set as the world up direction. The valid
        axis are either 'y' or 'z'."""
        return cmds.upAxis(q=True, axis=True)

    def user(self):
        return _getuser()

    def host(self):
        return _gethostname()

    def getTime(self):
        return cmds.currentTime(q=1)

    def setTime(self, val):
        cmds.currentTime(val)
    time = property(getTime, setTime)

    def getMinTime(self):
        return cmds.playbackOptions(q=1, minTime=1)

    def setMinTime(self, val):
        cmds.playbackOptions(minTime=val)
    minTime = property(getMinTime, setMinTime)

    def getMaxTime(self):
        return cmds.playbackOptions(q=1, maxTime=1)

    def setMaxTime(self, val):
        cmds.playbackOptions(maxTime=val)
    maxTime = property(getMaxTime, setMaxTime)

    def getAnimStartTime(self):
        return cmds.playbackOptions(q=1, animationStartTime=1)

    def setAnimStartTime(self, val):
        cmds.playbackOptions(animationStartTime=val)
    animStartTime = property(getAnimStartTime, setAnimStartTime)

    def getAnimEndTime(self):
        return cmds.playbackOptions(q=1, animationEndTime=1)

    def setAnimEndTime(self, val):
        cmds.playbackOptions(animationEndTime=val)
    animEndTime = property(getAnimEndTime, setAnimEndTime)

    def getPlaybackTimes(self):
        return (self.animStartTime, self.minTime, self.maxTime,
                self.animEndTime)

    def setPlaybackTimes(self, playbackTimes):
        if len(playbackTimes) != 4:
            raise ValueError("must have 4 playback times")
        self.animStartTime = playbackTimes[0]
        self.minTime = playbackTimes[1]
        self.maxTime = playbackTimes[2]
        self.animEndTime = playbackTimes[3]
    playbackTimes = property(getPlaybackTimes, setPlaybackTimes)

env = Env()


# -------------------------
# Maya.mel Wrapper
# -------------------------

class MelError(RuntimeError):

    """Generic MEL error"""
    pass


class MelConversionError(MelError, TypeError):

    """MEL cannot process a conversion or cast between data types"""
    pass


class MelUnknownProcedureError(MelError, NameError):

    """The called MEL procedure does not exist or has not been sourced"""
    pass


class MelArgumentError(MelError, TypeError):

    """The arguments passed to the MEL script are incorrect"""
    pass


class MelSyntaxError(MelError, SyntaxError):

    """The MEL script has a syntactical error"""
    pass


class MelCallable(object):

    """
    Class for wrapping up callables created by Mel class' procedure calls.

    The class is designed to support chained, "namespace-protected" MEL
    procedure calls, like: ``Foo.bar.spam()``. In this case, Foo, bar and spam
    would each be `MelCallable` objects.
    """

    def __init__(self, head, name):
        if head:
            self.full_name = '%s.%s' % (head, name)
        else:
            self.full_name = name

    def __getattr__(self, command):
        if command.startswith('__') and command.endswith('__'):
            try:
                return self.__dict__[command]
            except KeyError:
                raise AttributeError("object has no attribute '%s'" % command)

        return MelCallable(head=self.full_name, name=command)

    def __call__(self, *args, **kwargs):
        cmd = pythonToMelCmd(self.full_name, *args, **kwargs)
        return Mel._eval(cmd, self.full_name)

# PY2: when we convert, remove the "#doctest: +IGNORE_EXCEPTION_DETAIL" bits
# They're needed, because in python 2, we get exceptions with no module:
#   MelConversionError: ...
# While in python 3, it includes the module:
#   pymel.core.language.MelConversionError: ...
# However, there's a known bug with ellipsis + doctest, so that this won't work:
#   ...MelConversionError: ...
# IGNORE_EXCEPTION_DETAIL is the ONLY thing that will make it ignore the leading
# module - however, that flag ALSO makes it completely ignore the exception
# value as well - all that is checked is the type (minus the module). So, once
# we can, get rid of IGNORE_EXCEPTION_DETAIL

class Mel(object):

    """Acts as a namespace from which MEL procedures can be called as if they
    were python functions.

    Automatically formats python arguments into a command string which is
    executed via ``maya.mel.eval``.  An instance of this class is created for
    you as `pymel.core.mel`.

    default:
        >>> import maya.mel as mel
        >>> # create the proc
        >>> mel.eval( 'global proc myScript( string $stringArg, float $floatArray[] ){}')
        >>> # run the script
        >>> mel.eval( 'myScript("firstArg", {1.0, 2.0, 3.0})')

    pymel:
        >>> from pymel.all import *
        >>> # create the proc
        >>> mel.eval( 'global proc myScript( string $stringArg, float $floatArray[] ){}')
        >>> # run the script
        >>> mel.myScript("firstArg", [1.0, 2.0, 3.0])

    The above is a very simplistic example. The advantages of pymel.mel over
    ``maya.mel.eval`` are more readily apparent when we want to pass a python
    object to our mel procedure:

    default:
        >>> import maya.cmds as cmds
        >>> node = "lambert1"
        >>> color = cmds.getAttr( node + ".color" )[0]
        >>> mel.eval('myScript("%s",{%f,%f,%f})' % (cmds.nodeType(node), color[0], color[1], color[2])   )

    pymel:
        >>> from pymel.all import *
        >>> node = PyNode("lambert1")
        >>> mel.myScript( node.type(), node.color.get() )

    In this you can see how `pymel.core.mel` allows you to pass any python
    object directly to your mel script as if it were a python function, with
    no need for formatting arguments.  The resulting code is much more readable.

    Another advantage of this class over maya.mel.eval is its handling of mel
    errors.  If a mel procedure fails to execute, you will get the specific mel
    error message in the python traceback, and, if they are enabled,
    line numbers!

    For example, in the example below we redeclare the myScript procedure with
    a line that will result in an error:

        >>> commandEcho(lineNumbers=1)  # turn line numbers on
        >>> mel.eval( '''
        ... global proc myScript( string $stringArg, float $floatArray[] ){
        ...     float $donuts = `ls -type camera`;}
        ... ''')
        >>> mel.myScript( 'foo', [] ) #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        pymel.core.language.MelConversionError: Error during execution of MEL script: line 2: ,Cannot convert data of type string[] to type float.,
        Calling Procedure: myScript, in Mel procedure entered interactively.
          myScript("foo",{})

    Notice that the error raised is a `MelConversionError`.  There are several
    MEL exceptions that may be raised, depending on the type of error
    encountered: `MelError`, `MelConversionError`, `MelArgumentError`,
    `MelSyntaxError`, and `MelUnknownProcedureError`.

    Here's an example showing a `MelArgumentError`, which also demonstrates
    the additional traceback information that is provided for you, including
    the file of the calling script.

        >>> mel.startsWith('bar') #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        pymel.core.language.MelArgumentError: Error during execution of MEL script: Line 1.18: ,Wrong number of arguments on call to startsWith.,
        Calling Procedure: startsWith, in file "..."
          startsWith("bar")

    Lastly, an example of `MelUnknownProcedureError`

        >>> mel.poop() #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        pymel.core.language.MelUnknownProcedureError: Error during execution of MEL script: line 1: ,Cannot find procedure "poop".,

    Finally, some limitations: this Mel wrapper class cannot be used in
    situations in which the mel procedure modifies arguments (such as lists)
    in place, and you wish to then see the modified result in the calling code.
    Ie:

        >>> origList = []
        >>> newList = ["yet", "more", "things"]
        >>> mel.appendStringArray(origList, newList, 2)
        >>> origList
        []

    You will have to fall back to using mel.eval in such situations:

        >>> mel.eval('''
        ... string $origList[] = {};
        ... string $newList[] = {"yet", "more", "things"};
        ... appendStringArray($origList, $newList, 2);
        ... /* force a return value */
        ... $origList=$origList;
        ... ''')
        [u'yet', u'more']

    .. note::

        To remain backward compatible with maya.cmds, `MelError`, the base
        exception class that all these exceptions inherit from, in turn inherits
        from `RuntimeError`.
    """
    # proc is not an allowed name for a global procedure, so it's safe to use as an attribute
    proc = None

    def __getattr__(self, command):
        if command.startswith('__') and command.endswith('__'):
            try:
                return self.__dict__[command]
            except KeyError:
                raise AttributeError("object has no attribute '%s'" % command)

        return MelCallable(head='', name=command)

    @classmethod
    def mprint(cls, *args):
        """mel print command in case the python print command doesn't cut it"""
        # print r"""print (%s\\n);""" % pythonToMel( ' '.join( map( str, args)))
        _mm.eval( r"""print (%s);""" % pythonToMel( ' '.join( map( str, args))) + '\n' )

    @classmethod
    def source(cls, script, language='mel'):
        # type: (str, str) -> None
        """use this to source mel or python scripts.

        Parameters
        ----------
        script : str
        language : str
            {'mel', 'python'}
            When set to 'python', the source command will look for the
            python equivalent of this mel file, if it exists, and attempt
            to import it. This is particularly useful when transitioning
            from mel to python via `pymel.tools.mel2py`, with this simple
            switch you can change back and forth from sourcing mel to
            importing python.
        """

        if language == 'mel':
            cls.eval( """source "%s";""" % script )

        elif language == 'python':
            script = util.path(script)
            modulePath = script.namebase
            folder = script.parent
            print(modulePath)
            if modulePath not in sys.modules:
                print("importing")
                module = __import__(modulePath, globals(), locals(), [''])
                sys.modules[modulePath] = module

        else:
            raise TypeError("language keyword expects 'mel' or 'python'. "
                            "got '%s'" % language)

    @classmethod
    def eval(cls, cmd):
        """
        evaluate a string as a mel command and return the result.

        Behaves like `maya.mel.eval`, with several improvements:
            - returns `pymel.datatype.Vector` and `pymel.datatype.Matrix`
              classes
            - when an error is encountered a `MelError` exception is raised,
              along with the line number (if enabled) and exact mel error.

        >>> mel.eval( 'attributeExists("persp", "translate")' )
        0
        >>> mel.eval( 'interToUI( "fooBarSpangle" )' )
        'Foo Bar Spangle'

        """
        return cls._eval(cmd, None)

    @classmethod
    def _eval(cls, cmd, commandName):
        # commandName is just used for nicer formatting of error messages,
        # and is used by MelCallable

        # should return a value, like _mm.eval
        # return _mm.eval( cmd )
        # get this before installing the callback
        undoState = _mc.undoInfo(q=1, state=1)
        lineNumbers = _mc.commandEcho(q=1, lineNumbers=1)
        _mc.commandEcho(lineNumbers=1)
        global errors
        errors = []  # a list to store each error line

        def errorCallback(nativeMsg, messageType, data):
            global errors
            if messageType == _api.MCommandMessage.kError:
                if nativeMsg:
                    errors += [nativeMsg]

        # setup the callback:
        # assigning ids to a list avoids the swig memory leak warning, which would scare a lot of people even though
        # it is harmless.  hoping we get a real solution to this so that we don't have to needlessly accumulate this data
        id = _api.MCommandMessage.addCommandOutputCallback(errorCallback, None)

        try:
            res = _api.MCommandResult()
            _api.MGlobal.executeCommand(cmd, res, False, undoState)
        except Exception:
            msg = '\n'.join(errors)

            if 'Cannot find procedure' in msg:
                e = MelUnknownProcedureError
            elif 'Wrong number of arguments' in msg:
                e = MelArgumentError
                if commandName:
                    # remove the calling proc, it will be added below
                    msg = msg.split('\n', 1)[1].lstrip()
            elif 'Cannot convert data' in msg or 'Cannot cast data' in msg:
                e = MelConversionError
            elif 'Syntax error' in msg:
                e = MelSyntaxError
            else:
                e = MelError
            message = "Error during execution of MEL script: %s" % (msg)
            fmtCmd = '\n'.join(['  ' + x for x in cmd.split('\n')])

            if commandName:
                if e is not MelUnknownProcedureError:
                    file = _mm.eval('whatIs "%s"' % commandName)
                    if file.startswith('Mel procedure found in: '):
                        file = 'file "%s"' % os.path.realpath(file.split(':')[1].lstrip())
                    message += '\nCalling Procedure: %s, in %s' % (commandName, file)
                    message += '\n' + fmtCmd
            else:
                message += '\nScript:\n%s' % fmtCmd
            # PY2: once we switch to python-3 only, suppress the original
            # exception context, it's not useful
            #raise e(message) from None
            raise e(message)
        else:
            resType = res.resultType()

            if resType == _api.MCommandResult.kInvalid:
                return
            elif resType == _api.MCommandResult.kInt:
                result = _api.SafeApiPtr('int')
                res.getResult(result())
                return result.get()
            elif resType == _api.MCommandResult.kIntArray:
                result = _api.MIntArray()
                res.getResult(result)
                return [result[i] for i in range(result.length())]
            elif resType == _api.MCommandResult.kDouble:
                result = _api.SafeApiPtr('double')
                res.getResult(result())
                return result.get()
            elif resType == _api.MCommandResult.kDoubleArray:
                result = _api.MDoubleArray()
                res.getResult(result)
                return [result[i] for i in range(result.length())]
            elif resType == _api.MCommandResult.kString:
                return res.stringResult()
            elif resType == _api.MCommandResult.kStringArray:
                result = []
                res.getResult(result)
                return result
            elif resType == _api.MCommandResult.kVector:
                result = _api.MVector()
                res.getResult(result)
                return datatypes.Vector(result)
            elif resType == _api.MCommandResult.kVectorArray:
                result = _api.MVectorArray()
                res.getResult(result)
                return [datatypes.Vector(result[i]) for i in range(result.length())]
            elif resType == _api.MCommandResult.kMatrix:
                result = _api.MMatrix()
                res.getResult(result)
                return datatypes.Matrix(result)
            elif resType == _api.MCommandResult.kMatrixArray:
                result = _api.MMatrixArray()
                res.getResult(result)
                return [datatypes.Matrix(result[i]) for i in range(result.length())]
        finally:
            _api.MMessage.removeCallback(id)
            _mc.commandEcho(lineNumbers=lineNumbers)
            # 8.5 fix
            if hasattr(id, 'disown'):
                id.disown()

    @staticmethod
    def error(msg, showLineNumber=False):
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        _mm.eval( """error %s %s""" % ( flags, pythonToMel( msg) ) )

    @staticmethod
    def warning(msg, showLineNumber=False):
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        _mm.eval( """warning %s %s""" % ( flags, pythonToMel( msg) ) )

    @staticmethod
    def trace(msg, showLineNumber=False):
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        _mm.eval( """trace %s %s""" % ( flags, pythonToMel( msg) ) )

    @staticmethod
    def tokenize(*args):
        raise NotImplementedError("Calling the mel command 'tokenize' from "
                                  "python will crash Maya. Use the string "
                                  "split method instead.")

    # just a convenient alias
    globals = melGlobals


mel = Mel()


def conditionExists(conditionName):
    # type: (str) -> None
    """
    Returns True if the named condition exists, False otherwise.

    Parameters
    ----------
    conditionName : str
        A type used by `isTrue` and `scriptJob` (*Not* a type used by the
        condition *node*).
    """
    return conditionName in cmds.scriptJob(listConditions=True)


# ------ Do not edit below this line --------

@_factories.addCmdDocs
def callbacks(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ac', 'addCallback', 'rc', 'removeCallback']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.callbacks(*args, **kwargs)
    return res

evalEcho = _factories.getCmdFunc('evalEcho')

evalNoSelectNotify = _factories.getCmdFunc('evalNoSelectNotify')

getLastError = _factories.getCmdFunc('getLastError')

getProcArguments = _factories.getCmdFunc('getProcArguments')

matrixUtil = _factories.getCmdFunc('matrixUtil')

melOptions = _factories.getCmdFunc('melOptions')

optionVar = _factories.addCmdDocs(optionVar, cmdName='optionVar')

python = _factories.getCmdFunc('python')

resourceManager = _factories.getCmdFunc('resourceManager')

@_factories.addCmdDocs
def scriptJob(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['idleEvent', 'ie', 'tc', 'timeChange']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.scriptJob(*args, **kwargs)
    return res

sortCaseInsensitive = _factories.getCmdFunc('sortCaseInsensitive')

stackTrace = _factories.getCmdFunc('stackTrace')

waitCursor = _factories.getCmdFunc('waitCursor')

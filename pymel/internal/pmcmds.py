'''
This module wraps maya.cmds to accept special pymel arguments.

There are a number of pymel objects which must be converted to a "mel-friendly"
representation. For example, in versions prior to 2009, some mel commands (ie, getAttr) which expect
string arguments will simply reject custom classes, even if they have a valid string representation.
Another Example is mel's matrix inputs, which expects a flat list of 16 flaots, while pymel's Matrix has a more typical
4x4 representation.

If you're having compatibility issues with your custom classes when passing them to maya.cmds,
simply add a __melobject__ function that returns a mel-friendly result and pass them to pymel's wrapped commands.

The wrapped commands in this module are the starting point for any other pymel customizations.

'''

import inspect
import sys
import re
import os

import pymel.util as util
import pymel.versions as versions
#import mayautils
import maya.cmds
import warnings

__all__ = ['getMelRepresentation']
_thisModule = sys.modules[__name__]

# In Maya <= 2011, the error would be:
#   TypeError: Object foo.bar is invalid
# In Maya 2012, it is:
#   ValueError: No object matches name: foo.bar
if versions.current() < versions.v2012:
    objectErrorType = TypeError
    objectErrorReg = re.compile(',?Object (.*) is invalid,?$')
else:
    objectErrorType = ValueError
    objectErrorReg = re.compile(',?No object matches name: ,?(.*)$')

def _testDecorator(function):
    def newFunc(*args, **kwargs):
        print "wrapped function for %s" % function.__name__
        return function(*args, **kwargs)
    newFunc.__name__ =  function.__name__
    newFunc.__doc__ =  function.__doc__
    return newFunc


def getCmdName(inFunc):
    '''Use in place of inFunc.__name__ when inFunc could be a maya.cmds cmd

    handles stubFuncs
    '''
    cmdName = inFunc.__name__
    if cmdName == 'stubFunc':
        sourceFile = inspect.getsourcefile(inFunc)
        if (isinstance(sourceFile, basestring) and
                os.path.join('maya','app','commands') in sourceFile):
            # Here's where it gets tricky... this is a fairly big hack, highly
            # dependent on the exact implementation of maya.app.commands.stubFunc...
            freevars = inFunc.func_code.co_freevars
            # in python 2.5, tuples don't have index / find methods
            if not hasattr(freevars, 'index'):
                freevars = list(freevars)
            freeVarIndex = freevars.index('command')
            if freeVarIndex:
                raise ValueError('could not find a command var in %s' % cmdName)
            cmdName = inFunc.func_closure[freeVarIndex].cell_contents
    return cmdName

def getMelRepresentation( args, recursionLimit=None, maintainDicts=True):
    """Will return a list which contains each element of the iterable 'args' converted to a mel-friendly representation.

    :Parameters:
        recursionLimit : int or None
            If an element of args is itself iterable, recursionLimit specifies the depth to which iterable elements
            will recursively search for objects to convert; if ``recursionLimit==0``, only the elements
            of args itself will be searched for PyNodes -  if it is 1, iterables within args will have getMelRepresentation called
            on them, etc.  If recursionLimit==None, then there is no limit to recursion depth.

        maintainDicts : bool
            In general, all iterables will be converted to tuples in the returned copy - however, if maintainDicts==True,
            then iterables for which ``util.isMapping()`` returns True will be returned as dicts.

    """
    if recursionLimit:
        recursionLimit -= 1


    if maintainDicts and util.isMapping(args):
        newargs = dict(args)
        argIterable = args.iteritems()
        isList = False
    else:
        newargs = list(args)
        argIterable = enumerate(args)
        isList = True

    for index, value in argIterable:
        try:
            newargs[index] = value.__melobject__()
        except AttributeError:
            if ( (not recursionLimit) or recursionLimit >= 0) and util.isIterable(value):
                # ...otherwise, recurse if not at recursion limit and  it's iterable
                newargs[index] = getMelRepresentation(value, recursionLimit, maintainDicts)
    if isList:
        newargs = tuple(newargs)
    return newargs


def addWrappedCmd(cmdname, cmd=None):
    if cmd is None:
        cmd = getattr(maya.cmds, cmdname)

    #if cmd.__name__ == 'dummyFunc': print cmdname

    def wrappedCmd(*args, **kwargs):
        # we must get the cmd each time, because maya delays loading of functions until they are needed.
        # if we don't reload we'll keep the dummyFunc around
        new_cmd = getattr(maya.cmds, cmdname)
        #print args, kwargs
        # convert args to mel-friendly representation
        new_args = getMelRepresentation(args)

        # flatten list. this is necessary for list of components.  see Issue 71.  however, be sure that it's not an empty list/tuple
        if len(new_args) == 1 and util.isIterable(new_args[0]) and len(new_args[0]): #isinstance( new_args[0], (tuple, list) ):
            new_args = new_args[0]

        new_kwargs = getMelRepresentation(kwargs)
        #print new_args, new_kwargs
        try:
            res = new_cmd(*new_args, **new_kwargs)
        except objectErrorType, e:
            m = objectErrorReg.match(str(e))
            if m:
                import pymel.core.general
                obj = m.group(1)
                raise pymel.core.general._objectError(obj)

            else:
                # re-raise error
                raise

        # when editing, some of maya.cmds functions return empty strings and some return idiotic statements like 'Values Edited'.
        # however, for UI's in particular, people use the edit command to get a pymel class for existing objects.
        # return None when we get an empty string
        try:
            if res=='' and kwargs.get('edit', kwargs.get('e', False) ):
                return None
        except AttributeError:
            pass
        return res

    wrappedCmd.__doc__ = cmd.__doc__

    oldname = getattr(cmd, '__name__', None)
    if isinstance(oldname, str):
        # Don't use cmd.__name__, as this could be 'stubFunc'
        wrappedCmd.__name__ = getCmdName(cmd)
    else:
        wrappedCmd.__name__ = str(cmdname)

    # for debugging, to make sure commands got wrapped...
    #wrappedCmd = _testDecorator(wrappedCmd)

    # so that we can identify that this is a wrapped maya command
    setattr( _thisModule, cmdname, wrappedCmd )
    #globals()[cmdname] = wrappedCmd

def removeWrappedCmd(cmdname):
    try:
        del cmdname
    except NameError:
        warnings.warn("%s not found in %s" % (cmdname, __name__))

def addAllWrappedCmds():
    for cmdname, cmd in inspect.getmembers(maya.cmds, callable):
        addWrappedCmd(cmdname, cmd)




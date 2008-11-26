'''
Module which wraps the commands in maya.cmds to accept special pymel arguments.

There are a number of pymel objects which must be converted to a "mel-friendly"
representation. For example, in versions prior to 2009, some mel commands (ie, getAttr) that expect 
string arguments will only accept string instances, and simply reject
custom objects that have a valid string representation.  Another Example is mel's matrix inputs,
which expects a flat list of 16 flaots, while pymel's Matrix has a more typical and appropriate
4x4 representation.

This module provides a mechanism to allow pymel objects to provide an alternative mel-representation
if the default is not mel-compatible.  It wraps the commands in maya.cmds, and if it exists, it calls
a __melobject__ function to get the alternate object.

The wrapped commands in this module become the starting point for all commands in pymel.animation, pymel.general,
pymel.rendering, etc.

If you're having compatibility issues with your custom classes when passing them to mel commands, 
simply add a __melobject__ function that returns a mel-friendly result and pass them to pymel's wrapped commands.


'''

import inspect

import pymel.util as util
#import mayautils
import maya.cmds
import warnings

_thisModule = __import__(__name__, globals(), locals(), [''])

def _testDecorator(function):
    def newFunc(*args, **kwargs):
        print "wrapped function for %s" % function.__name__
        return function(*args, **kwargs)
    newFunc.__name__ =  function.__name__
    newFunc.__doc__ =  function.__doc__
    return newFunc
        

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
        new_args = util.getMelRepresentation(args)
        new_kwargs = util.getMelRepresentation(kwargs)
        #print new_args, new_kwargs
        res = new_cmd(*new_args, **new_kwargs)
        
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
    
    try:
        wrappedCmd.__name__ = cmd.__name__
    except TypeError:
        wrappedCmd.__name__ = cmdname

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

addAllWrappedCmds()

    

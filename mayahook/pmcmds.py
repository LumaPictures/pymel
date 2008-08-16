'''
Module which wraps the commands in maya.cmds to accept PyNode arguments.

In versions prior to 2009, some mel commands (ie, getAttr) that expect 
string arguments will only accept string instances, and simply reject
custom objects that have a valid string representation. This module wraps
the commands in maya.cmds, and properly stringifies any PyNode arguments
(more exactly, and ProxyUnicode args) before passing to maya.cmds.
 
This is not intended to be used by the end user, but to be in implementations
of pymel cmds, so that we don't need to remember to always stringify PyNode
arguments before calling the underlying maya.cmds
(or remember which cmds need stringifying).

The wrapping will be switched off for 2009 and later...
'''

import inspect

import pymel.util as util
import mayautils
import maya.cmds
import warnings

_thisModule = __import__(__name__, globals(), locals(), [''])



def _needStringifiedCmds():
    # for debugging purposes, this is set to always return True
    # ...eventually, will switch off for versions >=2009
    return True
    # TODO: uncomment before release!
    #return mayautils.getMayaVersion(extension=False) < 2009

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
    wrappedCmd = util.stringifyPyNodeArgs(cmd)

    # for debugging, to make sure commands got wrapped...
    #wrappedCmd = _testDecorator(wrappedCmd)

    # so that we can identify that this is a wrapped maya command
    setattr( _thisModule, cmdname, wrappedCmd )
    
def removeWrappedCmd(cmdname):
    try:
        del cmdname
    except NameError:
        warnings.warn("%s not found in %s" % (cmdname, __name__))
    
def addAllWrappedCmds():
    for cmdname, cmd in inspect.getmembers(maya.cmds, callable):
        addWrappedCmd(cmdname, cmd)

if _needStringifiedCmds():
    addAllWrappedCmds()
else:
    from maya.cmds import *
    

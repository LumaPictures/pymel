"""
This is an experimental feature!!!

Allows a user to create their own subclasses of leaf PyMEL node classes,
which are returned by `PyNode` and all other pymel commands.

The process is fairly simple:
    1.  Subclass a pymel node class.  Be sure that it is a leaf class, meaning that it represents an actual Maya node type
        and not an abstract type higher up in the hierarchy. 
    2.  Register your subclass by calling the registerVirtualSubClass method of your new class.  This is a class method, 
        meaning that it **must** be called from an uninstantiated class.  You do not need to create a node to register it.

When registering a new virtual subclass,  you must provide a callback function that accepts two arguments: an MFnDepencencyNode 
instance for the current object, and its name. The callback function should return True if the current object meets the requirements to become the
virtual subclass, or else False. If the callback requires the name of the object, set the keyword argument nameRequired to True when registering the
new class. The object's name is not always immediately available and may take an extra calculation to retrieve, so if nameRequired is not set
the name argument passed to your callback could be None.
            
If more than one subclass is registered for a node type, the tests will be run in the order they were registered until one returns True.  
If no test returns True, then the standard node class is used.  Keep in mind that once your new type is registered, its test will be run
every time a node of that type is returned as a PyMEL node class, so be sure to keep your tests simple and fast.  

If your callback needs access to Maya functionality, it should only use the API. This ensure that it is fast and that it does not cause an
infinite recursion.


"""

from pymel import *

import re

class LegJoint(Joint):
    """ this is an example of how to create your own subdivisions of existing nodes"""
    
    def kick(self):
        print "kicking"
        
class JawJoint(Joint):
    """ this is an example of how to create your own subdivisions of existing nodes"""
    
    def munch(self):
        print "munching"
        
def legJointCallback( fn, name ):
    """if the desired attribute exists, then we're a LegJoint!"""
    try:
        # this function fails if the attribute does not exist, so we have to try/except it.
        return fn.hasAttribute( 'jointType_leg' )
    except: pass
    return False

def jawJointCallback( fn, name ):
    """if the desired attribute exists, then we're a LegJoint!"""
    try:
        # this function fails if the attribute does not exist, so we have to try/except it.
        print "testing if this is a leg joint"
        return fn.hasAttribute( 'jointType_jaw' )
    except: pass
    return False

LegJoint.registerVirtualSubClass( legJointCallback, nameRequired=False )
JawJoint.registerVirtualSubClass( jawJointCallback, nameRequired=False )

    
def testJoint():
    joint()
    joint()
    j1 = joint()
    j2 = joint()
    j1.addAttr( 'jointType_leg' )
    j2.addAttr( 'jointType_jaw' )
    
    # now list the joints and see which ones are our special joints
    res = ls(type='joint')
    for x in res:
        if isinstance(x, LegJoint ):
            x.kick()
        elif isinstance(x, JawJoint ):
            x.munch()
    
    

# make sure Mayatomr plugin is loaded ore the Mib_amb_occlusion might not exist
loadPlugin('Mayatomr')
class Mib_amb_occlusion(Mib_amb_occlusion):
    """This is an example of how to replace a node.  Use this technique with care"""
    def occlude(self):
        print "occluding!"

# the callback always returns True, so we always replace it with our own.
Mib_amb_occlusion.registerVirtualSubClass( lambda *args: True, nameRequired=False )
    

def testMib():
    n = createNode('mib_amb_occlusion')
    n.occlude()
    

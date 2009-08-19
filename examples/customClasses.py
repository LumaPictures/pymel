"""
This is an experimental feature!!!  

Allows a user to create their own subclasses of leaf PyMEL node classes,
which are returned by `PyNode` and all other pymel commands.

The process is fairly simple:
    1.  Subclass a pymel node class.  Be sure that it is a leaf class, meaning that it represents an actual Maya node type
        and not an abstract type higher up in the hierarchy. 
    2.  Register your subclass by calling the registerVirtualSubClass method of your new class.  This is a class method, 
        meaning that it **must** be called from an uninstantiated class.  You do not need to create a node to register it.

When registering a new virtual subclass,  you must provide a callback function that accepts two arguments: an MObject/MDagPath 
instance for the current object, and its name. The callback function should return True if the current object meets the requirements to become the
virtual subclass, or else False. If the callback requires the name of the object, set the keyword argument nameRequired to True when registering the
new class. The object's name is not always immediately available and may take an extra calculation to retrieve, so if nameRequired is not set
the name argument passed to your callback could be None.
            
If more than one subclass is registered for a node type, the registered callbacks will be run newest to oldest until one returns True.  
If no test returns True, then the standard node class is used.  Keep in mind that once your new type is registered, its test will be run
every time a node of its parent type is returned as a PyMEL node class, so be sure to keep your tests simple and fast.  

If your callback needs access to Maya functionality, it should only use the API or plain ole' maya.cmds. This ensure that it does not cause an
infinite recursion.


"""

from pymel import *
    
#-------------------------------------------------------------------------------


def _create(cls, **kwargs):
    """
    This method is called when no argument is passed to the class ( not including keyword arguments), such as:
    
    >>> LegJoint(name='right')
    LegJoint(u'right')
    
    this method must be a classmethod or staticmethod. If you don't know what that means, just make sure you have
    @classmethod above your createVirtual method, as in this example.
    """
    print "create callback"
    # create a joint
    j = cmds.joint(**kwargs)
    # add the identifying attribute. the attribute name will be set on subclasses of this class
    cmds.addAttr( j, ln=cls._jointClassID )
    return j
    
class CustomJointBase(Joint):
    """ this is an example of how to create your own subdivisions of existing nodes. """
    @classmethod
    def _create(cls, **kwargs):
        """
        This method is called when no argument is passed to the class ( not including keyword arguments), such as:
        
        >>> LegJoint(name='right')
        LegJoint(u'right')
        
        this method must be a classmethod or staticmethod. If you don't know what that means, just make sure you have
        @classmethod above your createVirtual method, as in this example.
        """
        # create a joint
        j = cmds.joint(**kwargs)
        # add the identifying attribute. the attribute name will be set on subclasses of this class
        cmds.addAttr( j, ln=cls._jointClassID )
        return j
        
    
    @classmethod
    def _callback( cls, obj, name ):
        """This is the callback for determining if a Joint should become a "virtual" LegJoint or JawJoint, etc.  
        Notice that this method is a classmethod, which means it gets passed the class as "cls" instead of an instance as "self".
        The name of the method is unimportant, and it could have actually been a regular function instead of a class method.
        
        PyMEL code should not be used inside the callback, only API and maya.cmds. 
        """
        # obj is either an MObject or an MDagPath, depending on whether this class is a subclass of DependNode or DagNode, respectively.
        # we use MFnDependencyNode below because it works with either and we onl need to test attribute existence.
        fn = api.MFnDependencyNode(obj)
        try:
            # NOTE: MFnDependencyNode.hasAttribute fails if the attribute does not exist, so we have to try/except it.
            # the _jointClassID is stored on subclass of CustomJointBase
            return fn.hasAttribute( cls._jointClassID )
        except: pass
        return False
 
 
class LegJoint(CustomJointBase):
    _jointClassID = 'jointType_leg'
    
    def kick(self):
        print "kicking"
        
        
class JawJoint(CustomJointBase):
    _jointClassID = 'jointType_jaw'
    
    def munch(self):
        print "munching"

# we don't need to register CustomJointBase because it's just an abstract class to help us easily make our other virtual nodes
#LegJoint.registerVirtualSubClass( LegJoint._callback, createCallback=LegJoint._create, nameRequired=False )
#JawJoint.registerVirtualSubClass( JawJoint._callback, createCallback=JawJoint._create, nameRequired=False )

factories.registerVirtualSubClass( LegJoint, LegJoint._callback, createCallback=LegJoint._create, nameRequired=False )
factories.registerVirtualSubClass( JawJoint, JawJoint._callback, createCallback=JawJoint._create, nameRequired=False )
   
def testJoint():
    Joint()
    Joint()
    LegJoint(name='leftLeg')
    JawJoint()

    # now list the joints and see which ones are our special joints
    res = ls(type='joint')
    for x in res:
        if isinstance(x, LegJoint ):
            x.kick()
        elif isinstance(x, JawJoint ):
            x.munch()
    

#-------------------------------------------------------------------------------

# make sure Mayatomr plugin is loaded or the Mib_amb_occlusion node type might not exist
loadPlugin('Mayatomr')
class Mib_amb_occlusion(Mib_amb_occlusion):
    """This is an example of how to replace a node.  Use this technique with care"""
    def occlude(self):
        print "occluding!"

# the callback always returns True, so we always replace the default with our own.
Mib_amb_occlusion.registerVirtualSubClass( lambda *args: True, nameRequired=False )
    

def testMib():
    n = createNode('mib_amb_occlusion')
    n.occlude()
    

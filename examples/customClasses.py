"""
This is an experimental feature!!!  for advanced users only.

Allows a user to create their own subclasses of leaf PyMEL node classes,
which are returned by `PyNode` and all other pymel commands.

.. warning:: If you are not familiar with the classmethod and staticmethod decorators you should read up on them before using this feature.

The process is fairly simple:
    1.  Subclass a PyNode class.  Be sure that it is a leaf class, meaning that it represents an actual Maya node type
        and not an abstract type higher up in the hierarchy. 
    2.  Add an _isVirtual classmethod that accepts two arguments: an MObject/MDagPath instance for the current object, and its name. 
        It should return True if the current object meets the requirements to become the virtual subclass, or else False. 
    3.  Add an optional _preCreate and _postCreate method.  for more on these, see the examples below.
    4.  Register your subclass by calling factories.registerVirtualClass. If the _isVirtual callback requires the name of the object, 
        set the keyword argument nameRequired to True. The object's name is not always immediately available and may take an extra 
        calculation to retrieve, so if nameRequired is not set the name argument passed to your callback could be None.
            
If more than one subclass is registered for a node type, the registered callbacks will be run newest to oldest until one returns True.  
If no test returns True, then the standard node class is used.  Keep in mind that once your new type is registered, its test will be run
every time a node of its parent type is returned as a PyMEL node class, so be sure to keep your tests simple and fast.  

"""

from pymel.all import *
    
#-------------------------------------------------------------------------------


    
class CustomJointBase(Joint):
    """ this is an example of how to create your own subdivisions of existing nodes. """
       
    @classmethod
    def _isVirtual( cls, obj, name ):
        """This is the callback for determining if a Joint should become a "virtual" LegJoint or JawJoint, etc.  
        Notice that this method is a classmethod, which means it gets passed the class as "cls" instead of an instance as "self".
        
        PyMEL code should not be used inside the callback, only API and maya.cmds. 
        """
        # obj is either an MObject or an MDagPath, depending on whether this class is a subclass of DependNode or DagNode, respectively.
        # we use MFnDependencyNode below because it works with either and we only need to test attribute existence.
        fn = api.MFnDependencyNode(obj)
        try:
            # NOTE: MFnDependencyNode.hasAttribute fails if the attribute does not exist, so we have to try/except it.
            # the _jointClassID is stored on subclass of CustomJointBase
            return fn.hasAttribute( cls._jointClassID )
        except: pass
        return False
 
    @classmethod
    def _preCreateVirtual(cls, **kwargs ):
        """
        This class method is called prior to node creation and gives you a chance to modify the kwargs dictionary
        that is passed to the creation command.
        
        this method must be a classmethod or staticmethod
        """
        if 'name' not in kwargs and 'n' not in kwargs:
            # if no name is passed, then use the joint Id as the name.
            kwargs['name'] = cls._jointClassID
        # be sure to return the modified kwarg dictionary
        return kwargs
          
    @classmethod
    def _postCreateVirtual(cls, newNode ):
        """
        This method is called after creating the new node, and gives you a chance to modify it.  The method is
        passed the PyNode of the newly created node. You can use PyMEL code here, but you should avoid creating
        any new nodes.
        
        this method must be a classmethod or staticmethod
        """
        # add the identifying attribute. the attribute name will be set on subclasses of this class
        newNode.addAttr( cls._jointClassID )
 
class LegJoint(CustomJointBase):
    _jointClassID = 'joint_leg'
    def kick(self):
        print "kicking"
        
        
class JawJoint(CustomJointBase):
    _jointClassID = 'joint_jaw'
    def munch(self):
        print "munching"

# we don't need to register CustomJointBase because it's just an abstract class to help us easily make our other virtual nodes
factories.registerVirtualClass( LegJoint, nameRequired=False )
factories.registerVirtualClass( JawJoint, nameRequired=False )
   
def testJoint():
    # make some regular joints
    Joint()
    Joint()
    # now make some of our custom joints
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

    @staticmethod
    def _isVirtual(obj, name):
        """
        the callback always returns True, so we always replace the default with our own.
        """
        return True
     
factories.registerVirtualClass( Mib_amb_occlusion, nameRequired=False )
    

def testMib():
    n = createNode('mib_amb_occlusion')
    n.occlude()
    

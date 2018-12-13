"""
This is an experimental feature!!!  for advanced users only.

Allows a user to create their own subclasses of leaf PyMEL node classes, which
are returned by `PyNode` and all other pymel commands.

.. warning:: If you are not familiar with the classmethod and staticmethod
decorators you should read up on them before using this feature.

        The process is fairly simple:
            1.  Subclass a PyNode class.  Be sure that it is a leaf class,
                meaning that it represents an actual Maya node type and not an
                abstract type higher up in the hierarchy.
            2.  Add an _isVirtual classmethod that accepts two arguments: an
                MObject/MDagPath instance for the current object, and its name.
                It should return True if the current object meets the
                requirements to become the virtual subclass, or else False.
            3.  Add optional _preCreate, _create, and _postCreate methods.  For
                more on these, see below
            4.  Register your subclass by calling
                factories.virtualClasses.register. If the _isVirtual callback
                requires the name of the object, set the keyword argument
                nameRequired to True. The object's name is not always
                immediately available and may take an extra calculation to
                retrieve, so if nameRequired is not set the name argument
                passed to your callback could be None.

        The creation of custom nodes may be customized with the use of
        isVirtual, preCreate, create, and postCreate functions; these are
        functions (or classmethods) which are called before / during / after
        creating the node.

        The isVirtual method is required - it is the callback used on instances
        of the base (ie, 'real') objects to determine whether they should be
        considered an instance of this virtual class. It's input is an MObject
        and an optional name (if nameRequired is set to True). It should return
        True to indicate that the given object is 'of this class', False
        otherwise. PyMEL code should not be used inside the callback, only API
        and maya.cmds. Keep in mind that once your new type is registered, its
        test will be run every time a node of its parent type is returned as a
        PyMEL node class, so be sure to keep your tests simple and fast.

        The preCreate function is called prior to node creation and gives you a
        chance to modify the kwargs dictionary; they are fed the kwargs fed to
        the creation command, and return either 1 or 2 dictionaries; the first
        dictionary is the one actually passed to the creation command; the
        second, if present, is passed to the postCreate command.

        The create method can be used to override the 'default' node creation
        command;  it is given the kwargs given on node creation (possibly
        altered by the preCreate), and must return the string name of the
        created node. (...or any another type of object (such as an MObject),
        as long as the postCreate and class.__init__ support it.)

        The postCreate function is called after creating the new node, and
        gives you a chance to modify it.  The method is passed the PyNode of
        the newly created node, as well as the second dictionary returned from
        the preCreate function as kwargs (if it was returned). You can use
        PyMEL code here, but you should avoid creating any new nodes.

        By default, any method named '_isVirtual', '_preCreateVirtual',
        '_createVirtual', or '_postCreateVirtual' on the class is used; if
        present, these must be classmethods or staticmethods.

        Other methods / functions may be used by passing a string or callable
        to the preCreate / postCreate kwargs.  If a string, then the method
        with that name on the class is used; it should be a classmethod or
        staticmethod present at the time it is registered.

        The value None may also be passed to any of these args (except isVirtual)
        to signal that no function is to be used for these purposes.

        If more than one subclass is registered for a node type, the registered
        callbacks will be run newest to oldest until one returns True. If no
        test returns True, then the standard node class is used. Also, for each
        base node type, if there is already a virtual class registered with the
        same name and module, then it is removed. (This helps alleviate
        registered callbacks from piling up if, for instance, a module is
        reloaded.)

        Overriding methods of PyMEL base classes should be performed with care,
        because certain methods are used internally and altering their results
        may cause PyMEL to error or behave unpredictably.  This is particularly
        true for special methods like __setattr__, __getattr__, __setstate__,
        __getstate__, etc.  Some methods are considered too dangerous to modify,
        and registration will fail if the user defines an override for them;
        this set includes __init__, __new__, and __str__.
"""
# Note - all of this, below the 'warning', is copied from the docstring for
# VirtualClassManger.register - keep it in sync!


import pymel.core as pm
from pymel.internal.factories import virtualClasses

#-------------------------------------------------------------------------------



class CustomJointBase(pm.nt.Joint):
    """ this is an example of how to create your own subdivisions of existing nodes. """

    @classmethod
    def _isVirtual( cls, obj, name ):
        """This is the callback for determining if a Joint should become a "virtual" LegJoint or JawJoint, etc.
        Notice that this method is a classmethod, which means it gets passed the class as "cls" instead of an instance as "self".

        PyMEL code should not be used inside the callback, only API and maya.cmds.
        """
        # obj is either an MObject or an MDagPath, depending on whether this class is a subclass of DependNode or DagNode, respectively.
        # we use MFnDependencyNode below because it works with either and we only need to test attribute existence.
        fn = pm.api.MFnDependencyNode(obj)
        try:
            # NOTE: MFnDependencyNode.hasAttribute fails if the attribute does not exist, so we have to try/except it.
            # the _jointClassID is stored on subclass of CustomJointBase
            return fn.hasAttribute( cls._jointClassID )
        except: pass
        return False

    @classmethod
    def _preCreateVirtual(cls, **kwargs ):
        """
        This class method is called prior to node creation and gives you a
        chance to modify the kwargs dictionary that is passed to the creation
        command.  If it returns two dictionaries, the second is used passed
        as the kwargs to the postCreate method

        this method must be a classmethod or staticmethod
        """
        if 'name' not in kwargs and 'n' not in kwargs:
            # if no name is passed, then use the joint Id as the name.
            kwargs['name'] = cls._jointClassID
        # be sure to return the modified kwarg dictionary

        postKwargs = {}

        if 'rotate' in kwargs:
            postKwargs['rotate'] = kwargs.pop('rotate')
        return kwargs, postKwargs

    @classmethod
    def _postCreateVirtual(cls, newNode, **kwargs ):
        """
        This method is called after creating the new node, and gives you a
        chance to modify it.  The method is passed the PyNode of the newly
        created node, and the second dictionary returned by the preCreate, if
        it returned two items. You can use PyMEL code here, but you should
        avoid creating any new nodes.

        this method must be a classmethod or staticmethod
        """
        # add the identifying attribute. the attribute name will be set on subclasses of this class
        newNode.addAttr( cls._jointClassID )
        rotate = kwargs.get('rotate')
        if rotate is not None:
            newNode.attr('rotate').set(rotate)

class LegJoint(CustomJointBase):
    _jointClassID = 'joint_leg'
    def kick(self):
        print "%s is kicking" % self.name()
        return "kiyaah!"


class JawJoint(CustomJointBase):
    _jointClassID = 'joint_jaw'
    def munch(self):
        print "%s is munching" % self.name()
        return "nom nom nom..."

# we don't need to register CustomJointBase because it's just an abstract class to help us easily make our other virtual nodes
virtualClasses.register( LegJoint, nameRequired=False )
virtualClasses.register( JawJoint, nameRequired=False )

def test_Joint():
    # make some regular joints
    pm.nt.Joint()
    pm.nt.Joint()
    # now make some of our custom joints
    LegJoint(name='leftLeg')
    JawJoint(rotate=(90,45,0))

    # now list the joints and see which ones are our special joints
    res = pm.ls(type='joint')
    results = []
    for x in res:
        if isinstance(x, LegJoint ):
            results.append(x.kick())
        elif isinstance(x, JawJoint ):
            results.append(x.munch())
    assert results.count("kiyaah!") == 1
    assert results.count("nom nom nom...") == 1


#-------------------------------------------------------------------------------

class MyRamp(pm.nt.Ramp):
    """This is an example of how to replace a node.  Use this technique with care"""
    def ramp(self):
        msg = "ramp!"
        print msg
        return msg

    @staticmethod
    def _isVirtual(obj, name):
        """
        the callback always returns True, so we always replace the default with our own.
        """
        return True

virtualClasses.register( MyRamp, nameRequired=False )


def test_Mib():
    n = pm.createNode('ramp')
    assert isinstance(n, MyRamp)
    assert n.ramp() == "ramp!"

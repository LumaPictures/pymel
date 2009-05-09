
=======================================
PyNodes
=======================================

The pymel module reorganizes many of the most commonly used mel commands and API methods into a 
hierarchy of classes. This design allows you to write much more concise and readable python code. It also helps
keep all of the commands organized, so that
functions are paired only with the types of objects that can use them.

The `PyNode` class is the base object for all node-, component-, and attribute-related classes. We collectively refer
to all these classes as "PyNodes".

In order to use the object-oriented design of pymel, you must ensure that the objects that you are working 
with are instances of PyMEL classes. To make this easier, PyMEL contains wrapped version 
of the more common commands for creating and getting lists of objects. These modified commands cast their results to the appropriate 
`PyNode` class type. See `ls`, `listRelatives`, `listTransforms`, `selected`, and `listHistory`, for a few examples.  

Commands that list objects return PyMEL classes:
    >>> s = ls(type='transform')[0]
    >>> print type(s)
    <class 'pymel.core.nodetypes.Transform'>
    
Commands that create objects are wrapped as well:
    >>> t = polySphere()[0]
    >>> print t, type(t)
    pSphere1 <class 'pymel.core.nodetypes.Transform'>
    
---------------------------------------
API Underpinnings
---------------------------------------
In MEL, the best representation we have have of a maya node or attribute is its name.  But with the API we can do better!  
When creating an instance of a `PyNode` class, PyMEL determines the underlying API object behind the scenes.
With this in hand, it can operate on the object itself, not just the string representing the object.

So, what does this mean to you?  Well, let's take a common example: testing if two nodes or attributes are the
same. In MEL, to accomplish this the typical solution is to perform a string comparison 
of two object names, but there are many ways that this seemingly simple operation can go wrong. For instance, forgetting to compare the
full paths of dag node objects, or comparing the long name of an attribute to the short name of an attribute.  
And what if you want to test if the nodes are instances of each other?  You'll have some pretty 
nasty string processing ahead of you.  And what if someone renames the node or its name becomes non-unique?  With PyMEL, the nightmares
of string comparisons are over.

But since PyMEL uses the underlying API objects, these operations are simple
and API-fast.

        >>> from pymel import *
        >>> # Make two instanced spheres in different groups
        >>> sphere1, hist = polySphere(name='mySphere')
        >>> grp = group(sphere1)
        >>> grp2 = instance(grp)[0]
        >>> sphere2 = grp2.getChildren()[0]
        >>> # check out our objects
        >>> sphere1                            # the original
        Transform(u'group1|mySphere')
        >>> sphere2                            # the instance
        Transform(u'group2|mySphere')
        >>> # do some tests
        >>> # they aren't the same dag objects
        >>> sphere1 == sphere2              
        False
        >>> # they are instances of each other
        >>> sphere1.isInstanceOf( sphere2 )    
        True
        >>> sphere1.getInstances()
        [Transform(u'group1|mySphere'), Transform(u'group2|mySphere')]
        >>> 
        >>> # long and short names retrieve the same attribute
        >>> sphere1.t == sphere1.translate    
        True
        >>> sphere1.tx == sphere1.translate.translateX
        True
        >>> # the same attrs on different nodes/instances are still the same 
        >>> sphere1.t == sphere2.t    
        True

For more on the relationship between PyMEL and Maya's API, see `API Classes and their PyNode Counterparts`_
   
---------------------------------------
PyNodes Are Not Strings
---------------------------------------

In previous versions of pymel, the node classes inherited from the builtin unicode string class.  With the introduction of the new API
underpinnings, the node classes inherit from a special `ProxyUnicode` class, which has the functionality of a string object, but
removes the immutability restriction ( see the next section `Mutability And You`_ ).  It is important to keep in mind that although
PyNodes *behave* like strings in most situations, they are no longer actual strings. Functions which explicity require a string, and which worked 
with PyNodes in previous versions of pymel, might raise an error with version 0.9 and later. For example:

    >>> objs = ls( type='camera')
    >>> print ', '.join( objs )
    Traceback (most recent call last):
        ...
    TypeError: sequence item 0: expected string, Camera found

The solution is simple: convert the PyNodes to strings.  The following example uses a shorthand python expression called "list comprehension" to 
convert the list of PyNodes to a list of strings:

    >>> objs = ls( type='camera')
    >>> ', '.join( [ str(x) for x in objs ] )
    'frontShape, perspShape, sideShape, topShape'

Similarly, if you are trying to concatenate your PyNode with another string, you will need to cast it to a string (same as you would have
to do with an int):
    
    >>> cam = PyNode('frontShape')
    >>> print "The node " + str(cam) + " is a camera"
    The node frontShape is a camera
   
Alternately, you can use % string formatting syntax:

    >>> print "The node %s is a camera" % cam
    The node frontShape is a camera
    
By default the shortest unique name of the node is used. If you want more control over how the name is printed, use the various methods for retrieving the
name as a string:

    >>> cam.shortName() # shortest unique
    u'frontShape'
    >>> cam.nodeName() # just the node, same as unique in this case
    u'frontShape'
    >>> cam.longName() # full dag path
    u'|front|frontShape'

Finally, be aware that string operations with PyNodes return strings not new PyNodes:

    >>> new = cam.replace( 'front', 'monkey' )
    >>> print new, type(new), type(cam)
    monkeyShape <type 'unicode'> <class 'pymel.core.nodetypes.Camera'>
    
---------------------------------------
Mutability and You
---------------------------------------

One change that has come about due to the new API-based approach is node name mutability. You might have noticed
when working with strings in python that they cannot be changed "in place". In other words, all string operations return a new string. This is
is known as immutability.

By inheriting from a mutable `ProxyUnicode` class instead of an immutable string, we are now able to provide a design which more accurately reflects 
how nodes work in maya --  when a node's name is changed it is still the same object with the same properties --  the name
is simply a label or handle. In practice, this
means that each time the name of the node is required -- such as printing, slicing, splitting, etc -- the object's current name
is queried from the underlying API object. This ensures renames performed via mel or the UI will always be reflected 
in the name returned by your PyNode class.

Renaming
========

In versions of PyMEL previous to 0.9, the node classes inherited from python's built-in unicode
string type, which, due to its immutability, could cause unintuitive results with commands like rename.
The new behavior creates a more intuitve result.

New Behavior:
    >>> orig = polyCube(name='myCube')[0]
    >>> print orig                    # print out the starting name
    myCube
    >>> orig.rename('crazyCube')    # rename it (the new name is returned)
    Transform(u'crazyCube')
    >>> print orig                    # the variable 'orig' reflects the name change
    crazyCube
    
As you can see, you no longer need to assign the result of a rename to a variable, although, for backward
compatibility's sake, we've ensured that you still can.

Using PyNodes as Keys in Dictionaries
=====================================

Maya 2008 and Earlier
---------------------

There is one caveat to the mutability of node names: it can cause problems when using a PyMEL node as a key in a dictionary prior to 2009.
The reason is that the hash ( a hash is an integer value which is used to speed up dictionary access ) generated by a PyMEL node
is based on the node's name, which is subject to change.  

    >>> orig = polySphere()[0]         #doctest: +SKIP
    >>> d = { orig :  True }           #doctest: +SKIP
    >>> orig.rename('crazySphere')     #doctest: +SKIP
    Transform(u'crazySphere')
    >>> print d[orig]                  #doctest: +SKIP
    Traceback (most recent call last):
        ...
    KeyError: Transform(u'crazySphere')
    

Maya 2009 and Later
-------------------

A powerful new feature was added in Maya 2009 that gives us access to a unique id per node. You can access this by 
using the special method `DependNode.__hash__`.  The most important benefit of this is that PyNodes can be used as a key in
a dictionary in a name-independent way: if the name of the node changes, the PyNode object can still be used to retrieve data placed in the dictionary
prior to the name change.  It is important to note, however, that this id is only valid while the scene is open. Once it is closed and
reopened, the id for each node will change.

Below is an example demonstrating how this feature allows us to create a dictionary of node-to-name mappings, which could be used
to track changes to a file.

    >>> AllObjects = {}  # node-to-name dictionary
    >>> def store():
    ...     for obj in ls():
    ...         AllObjects[obj] = obj.name()
    >>> 
    >>> def diff():
    ...     AllObjsCopy = AllObjects.copy()
    ...     for obj in ls():
    ...         try:
    ...             oldName = AllObjsCopy.pop(obj)
    ...             newName = obj.name()
    ...             if  newName != oldName:
    ...                 print "renamed: %s ---> %s" % ( oldName, newName )
    ...         except KeyError:
    ...             print "new: %s" % ( obj.name() )
    ...     for obj, name in AllObjsCopy.iteritems():
    ...         print "deleted:", name
    >>>     
    >>> s = sphere()[0]
    >>> c = polyCube(ch=0)[0]
    >>> store()  # save the state of the current scene
    >>>
    >>> # make some changes
    >>> s.rename('monkey')
    Transform(u'monkey')
    >>> delete(c.getShape())
    >>> polyTorus()
    [Transform(u'pTorus1'), PolyTorus(u'polyTorus1')]
    >>>
    >>> diff() # print out what's changed since we ran 'store()'
    renamed: nurbsSphere1 ---> monkey
    renamed: nurbsSphereShape1 ---> monkeyShape
    new: polyTorus1
    new: pTorus1
    new: pTorusShape1
    deleted: pCubeShape1


---------------------------------------
Node Class Hierarchy
---------------------------------------


PyMEL provides a class for every node type in Maya's type hierarchy.  The name of the class is the node type captitalized.  Wherever possible,
PyMEL functions will return objects as instances of these classes. This allows you to use builtin python functions to inspect
and compare your objects.  For example:

    >>> dl = directionalLight()
    >>> type(dl)
    <class 'pymel.core.nodetypes.DirectionalLight'>
    >>> isinstance( dl, nodetypes.DirectionalLight)
    True
    >>> isinstance( dl, nodetypes.Light)
    True
    >>> isinstance( dl, nodetypes.Shape)
    True
    >>> isinstance( dl, nodetypes.DagNode)
    True
    >>> isinstance( dl, nodetypes.Mesh)
    False
     
Many of these classes contain no methods of their own and exist only as place-holders in the hierarchy.
However, there are certain key classes which provide important methods to all their sub-classes. A few of the more important
include `DependNode`, `DagNode`, `Transform`, and `Constraint`.

The methods on each node class are derived from three sources:
    1. automatically, from maya.cmds
    2. automatically, from maya.OpenMaya*
    3. manually, written by PyMEL team

MEL Node Commands and their PyNode Counterparts
===============================================

As you are probably aware, MEL contains a number of commands
which are used to create, edit, and query object types in maya.  Typically, the names of these commands correspond
with the node type on which they operate. However, it should be noted
that there are a handful of exceptions to this rule.

Some examples of command-class pairs.  Notice that the last two nodes do not match their corresponding command:

================    ================    =================
Mel Command         Maya Node Type      PyMEL Node  Class
================    ================    =================
aimConstraint       aimConstraint       AimConstraint
camera              camera              Camera
directionalLight    directionalLight    DirectionalLight 
spaceLocator        locator             Locator
vortex              vortexField         VortexField
================    ================    =================

    

This example demonstrates some basic principles. Note the relationship between the name of the object
created, its node type, and its class type. Also notice that instead of creating new objects using
maya.cmds functions ( ex. spotlight ), the class ( ex. Spotlight ) can also be used :

    >>> l = nodetypes.SpotLight()
    >>> print "The name is", l
    The name is spotLightShape1
    >>> print "The maya type is", l.type()
    The maya type is spotLight
    >>> print "The python type is", type(l)    
    The python type is <class 'pymel.core.nodetypes.SpotLight'>

Once you have an instance of a PyMEL class (usually handled automatically), you can use it to query and edit the
maya node it represents in an object-oriented way.

make the light red and get shadow samples, the old, procedural way
    >>> spotLight( l, edit=1, rgb=[1,0,0] ) 
    >>> print spotLight( l, query=1, shadowSamples=1 ) 
    1
    
now, the object-oriented, PyMEL way
    >>> l.setRgb( [1,0,0] )
    >>> print l.getShadowSamples()   
    1

For those familiar with MEL, you can probably already tell that the DirectionalLight class can be understood as an 
object-oriented reorganization of the directionalLight command, where you 'get' queries and you 'set' edits.  

Some classes have functionality that goes beyond their command counterpart. The `Camera` class,
for instance, also contains the abilities of the `track`, `orbit`, `dolly`, and `cameraView` commands:

    >>> cam = nodetypes.Camera(name='newCam')
    >>> cam.setFocalLength(100)
    >>> cam.getHorizontalFieldOfView()
    20.407947443463367
    >>> cam.dolly( distance = -3 )
    >>> cam.track(left=10)
    >>> cam.addBookmark('new')


API Classes and their PyNode Counterparts
=========================================

PyNode classes now derive their methods from both MEL and the API ( aka. maya.cmds and maya.OpenMaya, respectivelly ).  If you're 
familiar with Maya's API, you know that there is a distinct separation between objects and their abilities.  There are fundamental
object types such as MObject and MDagPath that represent the object itself, and there are "function sets", which are classes that,
once instantiated with a given fundamental object, provide it with special abilities.  ( Because I am a huge nerd, I like to the think of the 
function sets as robotic "mechs" and the fundamental objects as "spirits" or "ghosts" that inhabit them, like in *Ghost in the Shell* ). 

For simplicity, PyMEL does away with this distinction: a PyNode instance is the equivalent of an activated API function set;  the 
necessary fundamental API objects are determined behind the scenes at instantiation.  You can access these by using the special methods
__apimobject__, __apihandle__, __apimdagpath__, __apimplug__, and __apimfn__.  ( Be aware that this is still considered internal magic, 
and the names of these methods are subject to change ):

    >>> p = PyNode('perspShape')
    >>> p.__apimfn__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MFnCamera; proxy of <Swig Object of type 'MFnCamera *' at ...> >
    >>> p.__apimdagpath__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MDagPath; proxy of <Swig Object of type 'MDagPath *' at ...> >
    >>> a = p.focalLength
    >>> a
    Attribute(u'perspShape.focalLength')
    >>> a.__apimplug__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MPlug; proxy of <Swig Object of type 'MPlug *' at ...> >

As you can probably see, these methods are enormously useful when prototyping API plugins.  Also of great use is the `PyNode` class,
which can be instantiated using API objects.


 
---------------------------------------
Chained Function and Attribute Lookups
---------------------------------------

Mel provides the versatility of operating on a shape node via its transform node.  For example, these two commands work
interchangably::

    camera -q -centerOfInterest persp
    camera -q -centerOfInterest perspShape


PyMEL achieves this effect by chaining function lookups.  If a called method does not exist on the Transform class, the 
request will be passed to appropriate class of the transform's shape node, if it exists.

    >>> # get the persp camera as a PyNode
    >>> trans = PyNode('persp')
    >>> print type(trans)
    <class 'pymel.core.nodetypes.Transform'>
    >>> # get the transform's shape, aka the camera node
    >>> cam = trans.getShape()
    >>> print cam
    perspShape
    >>> print type( cam )
    <class 'pymel.core.nodetypes.Camera'>
    >>> trans.getCenterOfInterest()
    44.82186966202994
    >>> cam.getCenterOfInterest()
    44.82186966202994

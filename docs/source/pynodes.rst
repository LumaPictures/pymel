.. currentmodule:: pymel.core.general

=======================================
PyNodes
=======================================

The pymel module reorganizes many of the most commonly used mel commands and API methods into a 
hierarchy of classes. This design allows you to write much more concise and readable python code. It also helps
keep all of the commands organized, so that functions are paired only with the types of objects that can use them.

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

In MEL, the best representation we have have of a maya node or attribute is its name.  But with the API we can do better!  When creating an instance of a `PyNode` class, PyMEL determines the underlying API object behind the scenes. With this in hand, it can operate on the object itself, not just the string representing the object.

So, what does this mean to you?  Well, let's take a common example: testing if two nodes or attributes are the
same. In MEL, to accomplish this the typical solution is to perform a string comparison of two object names, but there are many ways that this seemingly simple operation can go wrong. For instance, forgetting to compare the full paths of dag node objects, or comparing the long name of an attribute to the short name of an attribute.  And what if you want to test if the nodes are instances of each other?  You'll have some pretty nasty string processing ahead of you.  And if someone renames the node or its name becomes non-unique after you've already gotten its name as a string then your script will fail.  With PyMEL, the nightmares of string comparisons are over.

Since PyMEL uses the underlying API objects, these operations are simple and API-fast.

In this example, we'll make a sphere, group it, then instance the group, so that we have a tricky situation with instances and non-unique names. 

        >>> from pymel.core import *
        >>> # Make two instanced spheres in different groups
        >>> sphere1, hist = polySphere(name='mySphere')
        >>> grp = group(sphere1)
        >>> grp2 = instance(grp)[0]
        >>> sphere2 = grp2.getChildren()[0]

Now lets take a look at our objects and see how our various comparisons turn out.

        >>> # check out our objects
        >>> sphere1                            # the original
        Transform('group1|mySphere')
        >>> sphere2                            # the instance
        Transform('group2|mySphere')
        >>> # do some tests
        >>> # they aren't the same dag objects
        >>> sphere1 == sphere2
        False
        >>> # but they are instances of each other
        >>> sphere1.isInstanceOf( sphere2 )    
        True

Attribute comparison is simple, too. Keep in mind, we are not comparing the values of the attributes -- for that we would need to use the `get <nodetypes.Attribute.get>` method -- we are comparing the attributes themselves.  This is more flexible and reliable than comparing names:

        >>> # long and short names retrieve the same attribute
        >>> sphere1.t == sphere1.translate    
        True
        >>> sphere1.tx == sphere1.translate.translateX
        True
        >>> # the same attrs on different nodes/instances are still the same 
        >>> sphere1.t == sphere2.t
        True

And here's an incredibly useful feature that I get asked for all the time.  Get all the instances of an object in a scene::

	    >>> sphere1.getInstances()
        [Transform(u'group1|mySphere'), Transform(u'group2|mySphere')]
	    >>> sphere1.getOtherInstances()
        [Transform(u'group2|mySphere')]

For more on the relationship between PyMEL and Maya's API, see :ref:`api_pynodes`.

.. _pynodes_not_strings:
  
---------------------------------------
PyNodes Are Not Strings
---------------------------------------

The `PyNode` base class inherits from `ProxyUnicode <pymel.util.utilitytypes.ProxyUnicode>` class, which has the functionality of a string object, but removes the immutability restriction.  It is important to keep in mind that although PyNodes *behave* like strings in most situations, they are not actual strings. Functions which explicitly require a string, might raise an error. For example:

    >>> objs = ls( type='camera')
    >>> print ', '.join( objs )
    Traceback (most recent call last):
        ...
    TypeError: sequence item 0: expected string, Camera found

The solution is simple: convert the PyNodes to strings.  The following example uses a shorthand python expression called "list comprehension" to convert the list of PyNodes to a list of strings:

    >>> objs = ls(type='camera')
    >>> ', '.join([ str(x) for x in objs ])
    'frontShape, perspShape, sideShape, topShape'

Similarly, if you are trying to concatenate your PyNode with another string, you will need to cast it to a string (same as you would have
to do with an int):
    
    >>> print "Camera 1 of " + str(len(objs)) + " is named " + str(objs[0])
    Camera 1 of 4 is named frontShape
       
Alternately, you can use string formatting syntax:

    >>> print "Camera 1 of %s is named %s" % ( len(objs), objs[0] )
    Camera 1 of 4 is named frontShape

The ``%s`` means to format as a string.  

.. note:: 
    You can get more control over how numbers are formatted by using ``%f`` for floats and ``%d`` for integers::

        >>> "You can control precision %.02f and padding %04d" % ( 1.2345, 2 ) 
        'You can control precision 1.23 and padding 0002'

    
By default, the shortest unique name of the node is used when converting to a string. If you want more control over how the name is printed, use the various methods for retrieving the name as a string:

    >>> cam.shortName() # shortest unique
    'frontShape'
    >>> cam.nodeName() # just the node, same as unique in this case
    'frontShape'
    >>> cam.longName() # full dag path
    '|front|frontShape'

Finally, be aware that string operations with PyNodes return strings not new PyNodes:

    >>> new = cam.replace('front', 'monkey')
    >>> print new, type(new), type(cam)
    monkeyShape <type 'unicode'> <class 'pymel.core.nodetypes.Camera'>
    
Node Renaming
===============

Maya nodes can be renamed, which means that each time the name of the node is required -- such as printing, slicing, splitting, or passing to any command derived from ``maya.cmds`` -- the object's current name is queried from the underlying API object. This ensures renames performed via mel or the UI will always be reflected in the name returned by your PyNode class and your variables will remain valid despite these changes.::

    >>> orig = polyCube(name='myCube')[0]
    >>> print orig                    # print out the starting name
    myCube
    >>> orig.rename('crazyCube')      # rename it (the new name is returned)
    Transform('crazyCube')
    >>> print orig                    # the variable 'orig' reflects the name change
    crazyCube
    
As you can see, you do not need to assign the result of a rename to a variable, although, for backward compatibility's sake, we've ensured that you still can.

Querying the name of the object is not infinitely fast, so try to avoid doing it repetitively, if possible.

See :ref:`pynodes_in_dicts` for more information on PyNode mutability.


---------------------------------------
Node Class Hierarchy
---------------------------------------


PyMEL provides a class for every node type in Maya's type hierarchy.  The name of the class is the node type capitalized.  Wherever possible,
PyMEL functions will return objects as instances of these classes. This allows you to use built-in python functions to inspect
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
include `nt.DependNode <pymel.core.nodetypes.DependNode>`, `nt.DagNode <pymel.core.nodetypes.DagNode>`, `nt.Transform <pymel.core.nodetypes.Transform>`, and `nt.Constraint <pymel.core.nodetypes.Constraint>`.

---------------------------------------
Chained Function and Attribute Lookups
---------------------------------------

Mel provides the versatility of operating on a shape node via its transform node.  For example::

    camera -q -centerOfInterest persp
    camera -q -centerOfInterest perspShape


PyMEL achieves this effect by chaining function lookups.  If a called method does not exist on the `Transform` class, the 
request will be passed to appropriate class of the transform's shape node, if it exists.

    >>> # get the persp camera as a PyNode
    >>> trans = PyNode('persp')
    >>> # get the transform's shape, aka the camera node
    >>> cam = trans.getShape()
    >>> print cam
    perspShape
    >>> trans.getCenterOfInterest()
    44.82186966202994
    >>> cam.getCenterOfInterest()
    44.82186966202994

Technically speaking, the Transform does not have a `getCenterOfInterest` method:: 

 	>>> trans.getCenterOfInterest
	<bound method Camera.getCenterOfInterest of Camera(u'perspShape')>

Notice the bound method belongs to the `nt.Camera <pymel.core.nodetypes.Camera>` class.

.. _pynodes_in_dicts:

-------------------------------------
Using PyNodes as Keys in Dictionaries
-------------------------------------

A powerful feature was added in Maya 2009 that gives us access to a unique id per node. You can access this by 
using the special method `nt.DependNode.__hash__ <pymel.core.nodetypes.DependNode.__hash__>`, though typically you won't need to use this directly.  Its existence means that PyNodes can be used as a key in a dictionary in a name-independent way: if the name of the node changes, the PyNode object can still be used to retrieve data placed in the dictionary prior to the name change.  It is important to note, however, that this id is only valid while the scene is open. Once it is closed and reopened, the id for each node will change.

Below is an example demonstrating how this feature allows us to create a dictionary of node-to-name mappings, which could be used to track changes to a file. ::

    AllObjects = {}  # node-to-name dictionary
    def store():
        for obj in ls():
            AllObjects[obj] = obj.name()
    
    def diff():
        AllObjsCopy = AllObjects.copy()
        for obj in ls():
            try:
                oldName = AllObjsCopy.pop(obj)
                newName = obj.name()
                if newName != oldName:
                    print "renamed: %s ---> %s" % (oldName, newName)
            except KeyError:
               print "new: %s" % obj.name()
        for obj, name in AllObjsCopy.iteritems():
            print "deleted:", name
    
create some objects and store them to start::
    
    s = sphere()[0]
    c = polyCube(ch=0)[0]
    store()  # save the state of the current scene

now make some changes::

    s.rename('monkey')
    delete(c.getShape())
    polyTorus()

print out what's changed since we ran ``store()``::
   
    diff()
    
this prints out::

    renamed: nurbsSphere1 ---> monkey
    renamed: nurbsSphereShape1 ---> monkeyShape
    new: polyTorus1
    new: pTorus1
    new: pTorusShape1
    deleted: pCubeShape1


---------------------------------------------
Mommy, Where Do PyNodes Come From?
---------------------------------------------

In order to understand PyNode classes, it's best to understand their relationship to the underlying objects that they wrap. The methods on each node class are derived from three sources:

1. automatically, from maya.cmds
2. automatically, from maya.OpenMaya*
3. manually, written by PyMEL team

.. _mel_pynodes:

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
maya.cmds functions ( ex. `spotlight <pymel.core.rendering.spotLight>` ), the class ( ex. `nt.SpotLight <pymel.core.nodetypes.SpotLight>` ) can also be used :

    >>> from pymel.core import *
    >>> l = nodetypes.SpotLight()
    >>> print "The name is", l
    The name is spotLightShape1
    >>> print "The maya type is", l.type()
    The maya type is spotLight
    >>> print "The python type is", type(l)    
    The python type is <class 'pymel.core.nodetypes.SpotLight'>

Once you have an instance of a PyMEL class, you can use it to query and edit the
maya node it represents in an object-oriented way.

Make the light red and get shadow samples, the old, procedural way::

    >>> spotLight(l, edit=1, rgb=[1, 0, 0]) 
    >>> print spotLight(l, query=1, shadowSamples=1) 
    1
    
Now, the object-oriented, PyMEL way::

    >>> l.setRgb([1, 0, 0])
    >>> print l.getShadowSamples()   
    1

For those familiar with MEL, you can probably already tell that the DirectionalLight class can be understood as an 
object-oriented reorganization of the directionalLight command, where you 'get' queries and you 'set' edits.  

Some classes have functionality that goes beyond their command counterpart. The `nt.Camera <pymel.core.nodetypes.Camera>` class,
for instance, also contains the abilities of the `track <pymel.core.rendering.track>`, `orbit <pymel.core.rendering.orbit>`, `dolly <pymel.core.rendering.dolly>`, and `cameraView <pymel.core.rendering.cameraView>` commands:

    >>> cam = nodetypes.Camera(name='newCam')
    >>> cam.setFocalLength(100)
    >>> cam.getHorizontalFieldOfView()
    20.407947443463367
    >>> cam.dolly(distance=-3)
    >>> cam.track(left=10)
    >>> cam.addBookmark('new')

.. _api_pynodes:

API Classes and their PyNode Counterparts
=========================================

PyNode classes derive their methods from both MEL and the API ( aka. maya.cmds and maya.OpenMaya, respectively ).  If you're familiar with Maya's API, you know that there is a distinct separation between objects and their abilities.  There are fundamental object types such as ``maya.OpenMaya.MObject`` and ``maya.OpenMaya.MDagPath`` that represent the object itself, and there are "function sets", which are classes that,
once instantiated with a given fundamental object, provide it with special abilities.  ( Because I am a huge nerd, I like to the think of the function sets as robotic "mechs" and the fundamental objects as "spirits" or "ghosts" that inhabit them, like in *Ghost in the Shell* ). 

For simplicity, PyMEL does away with this distinction: a PyNode instance is the equivalent of an activated API function set;  the necessary fundamental API objects are determined behind the scenes at instantiation.  You can access these by using the special methods `nt.DependNode.__apimobject__ <pymel.core.nodetypes.DependNode.__apimobject__>`, `Attribute.__apimobject__`, `nt.DependNode.__apihandle__ <pymel.core.nodetypes.DependNode.__apihandle__>`, `nt.DagNode.__apimdagpath__ <pymel.core.nodetypes.DagNode.__apimdagpath__>`, `Attribute.__apimdagpath__`, `Attribute.__apimplug__`, and `PyNode.__apimfn__`.  (Be aware that this is still considered internal magic, and the names of these methods are subject to change ):

    >>> p = PyNode('perspShape')
    >>> p.__apimfn__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MFnCamera; proxy of <Swig Object of type 'MFnCamera *' at ...> >
    >>> p.__apimdagpath__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MDagPath; proxy of <Swig Object of type 'MDagPath *' at ...> >
    >>> a = p.focalLength
    >>> a
    Attribute('perspShape.focalLength')
    >>> a.__apimplug__() # doctest: +ELLIPSIS
    <maya.OpenMaya.MPlug; proxy of <Swig Object of type 'MPlug *' at ...> >

As you can probably see, these methods are enormously useful when prototyping API plugins.  Also of great use is the `PyNode` class, which can be instantiated using API objects.



..
    ---------------------------------------------
    ipymel
    ---------------------------------------------


---------------------------------------
Glossary
---------------------------------------

.. glossary::

	mutable

        Mutability describes a data type whos value can be changed without reassigning.  An example of a mutable data type is the builtin list.
    
            >>> numbers = [1,2,3]
            >>> numbers.append(4)
            >>> numbers
            [1, 2, 3, 4]
    
        As you can see we have changed the value of ``numbers`` without reassigning a new value ``numbers`` (in plain english, we didn't use an equal sign). 

        You might have noticed when working with strings in python that they cannot be changed "in place". All string operations that modify the string, return a brand new string as a result, leaving the original intact. This is is known as immutability::

            >>> s1 = 'hampster dance'
            >>> s2 = s1.replace('hampster', 'chicken')
            >>> s1
            'hampster dance'
            >>> s2
            'chicken dance'
    
        The value of ``s1`` remained the same, but the result of the ``replace`` operation was stored into ``s2``. Because strings are immutable and the value of ``s1`` cannot change without assigning a brand new value to ``s1``::

            >>> s1 = 'brand new dance!'

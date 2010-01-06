=============================================
Advanced Topics
=============================================

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
maya.cmds functions ( ex. spotlight ), the class ( ex. Spotlight ) can also be used :

    >>> from pymel.core import *
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

.. _api_pynodes:

API Classes and their PyNode Counterparts
=========================================

PyNode classes derive their methods from both MEL and the API ( aka. maya.cmds and maya.OpenMaya, respectively ).  If you're familiar with Maya's API, you know that there is a distinct separation between objects and their abilities.  There are fundamental object types such as ``maya.OpenMaya.MObject`` and ``maya.OpenMaya.MDagPath`` that represent the object itself, and there are "function sets", which are classes that,
once instantiated with a given fundamental object, provide it with special abilities.  ( Because I am a huge nerd, I like to the think of the function sets as robotic "mechs" and the fundamental objects as "spirits" or "ghosts" that inhabit them, like in *Ghost in the Shell* ). 

For simplicity, PyMEL does away with this distinction: a PyNode instance is the equivalent of an activated API function set;  the necessary fundamental API objects are determined behind the scenes at instantiation.  You can access these by using the special methods ``__apimobject__``, ``__apihandle__``, ``__apimdagpath__``, ``__apimplug__``, and ``__apimfn__``.  ( Be aware that this is still considered internal magic, 
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

As you can probably see, these methods are enormously useful when prototyping API plugins.  Also of great use is the `PyNode` class, which can be instantiated using API objects.

..
    __apiobject__ and __melobject__
    ===============================


    ---------------------------------------------
    Custom Classes
    ---------------------------------------------

---------------------------------------
Mutability and You
---------------------------------------

One change that has come about due to the new API-based approach is node name mutability. By inheriting from a :term:`mutable` `ProxyUnicode` class instead of an immutable string, we are able to provide a design which more accurately reflects how nodes work in maya --  when a node's name is changed it is still the same object with the same properties --  the name is simply a label or handle.  This means that each time the name of the node is required -- such as printing, slicing, splitting, etc -- the object's current name is queried from the underlying API object. This ensures any renaming of the nodes, regardless of how it is performed, will always be reflected by your PyNode object, and therefore, you can rest assured that PyNodes stored away in lists and dictionaries will remain valid, unlike a string name.

Renaming
========

In versions of PyMEL previous to 0.9, the node classes inherited from python's built-in unicode
string type, which, due to its immutability, could cause unintuitive results with commands like `rename`.
The new behavior creates a more intuitive result.

New Behavior:
    >>> orig = polyCube(name='myCube')[0]
    >>> print orig                    # print out the starting name
    myCube
    >>> orig.rename('crazyCube')      # rename it (the new name is returned, but not stored)
    Transform(u'crazyCube')
    >>> print orig                    # the variable 'orig' reflects the name change
    crazyCube
    
Unlike with strings, when you alter the name of a Node you do not need to assign the result to a variable, although, for backward
compatibility's sake, we've ensured that you still can.

.. _pynodes_in_dicts:

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
using the special method `DependNode.__hash__`.  The most important benefit of this is that PyNodes can be used as a key in a dictionary in a name-independent way: if the name of the node changes, the PyNode object can still be used to retrieve data placed in the dictionary prior to the name change.  It is important to note, however, that this id is only valid while the scene is open. Once it is closed and reopened, the id for each node will change.

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
                if  newName != oldName:
                    print "renamed: %s ---> %s" % ( oldName, newName )
            except KeyError:
               print "new: %s" % ( obj.name() )
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

..
    ---------------------------------------------
    ipymel
    ---------------------------------------------









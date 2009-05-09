=======================================
Tutorial
=======================================

This tutorial assumes that you have some familiarity with python, but even if you only have MEL experience, you'll probably be able to follow along.
If you are a MEL scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly
the section `Using Python <http://download.autodesk.com/us/maya/2008help/General/Using_Python.html>`__. This will help you to understand 
the differences in syntax between the two languages and how to translate between them. Another great way to learn how to translate 
mel into python is to install the new `Script Editor`_. With it you can execute some mel code and watch the 
python output in the top pane. You can toggle back and forth by checking and unchecking the "Convert Mel to Python" checkbox.


---------------------------------------
Importing PyMEL
---------------------------------------

To get started we need to import pymel.

    >>> from pymel import *
   	
This brings everything in pymel into the main namespace, meaning that you won't have to prefix the maya commands with the
module name. 

.. warning::

	One problem with maya.cmds is that importing it into the root namespace (e.g. ``from maya.cmds import *``)
	is dangerous because it will override several of python's more important built-in methods. PyMEL is designed
	to be safe to import into the root namespace so that scripts can be written much more concisely. However, if you are
	a python novice, you might want to keep pymel in its own namespace, because, unlike in mel, in python you can "overwrite" functions
	if you are not careful:
	
		>>> from pymel import *
		>>> s = sphere() # create a nurbsSphere
		>>> sphere = 'mySphere'  # oops, we've overwritten the sphere command with a string
		>>> sphere()
		Traceback (most recent call last):
			...
		TypeError: 'str' object is not callable

.. note::

	All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( ``file``, ``filter``, ``eval``,
	``help``, and ``quit``). The conflicting commands can be found in the `pymel.cmds` namespace, along with all of the unaltered
	maya commands.  

Before we proceed let's make sure we have a clean scene so that you'll get the same results as me:

    >>> f=newFile(f=1) #start clean
    
---------------------------------------
The Basics
---------------------------------------

Next, we need some nodes to work with.  In general, we can get nodes in 3 ways: list them
based on some critera, create them, or just get them by name.  Let's start by listing the cameras in the scene.  We do this in the 
same way that we would with maya.cmds.

    >>> ls(type='camera')
    [Camera(u'frontShape'), Camera(u'perspShape'), Camera(u'sideShape'), Camera(u'topShape')]

Notice that the names of the returned nodes are preceded by the node type, `Camera`.  When using pymel, commands don't return strings
as they do in MEL and maya.cmds.  Instead they return instances of `PyNode` classes which correspond to the type of object or UI.
These python objects are like strings on steroids: in addition to methods found on the builtin string ( a method is a function bound to an object. ex. 'bar' is the
method in 'foo.bar' ), 
PyMEL adds methods for operating on the specific type of maya object that the string represents. 

Let's use one of these camera objects to get some information:
        
    >>> # assign the first camera to a variable
    >>> cam = ls(type='camera')[0]
    >>> cam
    Camera(u'frontShape')
    >>> # get some information
    >>> cam.getAspectRatio()
    1.5
    >>> cam.getFocalLength()
    35.0


Now let's create a node:

    >>> objs = polyPlane()
    >>> objs
    [Transform(u'pPlane1'), PolyPlane(u'polyPlane1')]

You can see that, like the `ls` command, the `polyPlane` command also returns `PyNode` classes.  As in MEL, it returns a list: the
first object is the tranform of the plane, and the second is the construction history. Now
let's get the shape of the transform:

    >>> #assign the transform from above to a variable
    >>> plane = objs[0]
    >>> shape = plane.getShape()
    >>> shape
    Mesh(u'pPlaneShape1')
    
So, we can clearly see that the shape is a Mesh. Let's explore the `Mesh` object a little. We can get the name as a string, 
formatted in different ways (the u in front of the string denotes that it is a unicode string, meaning it can represent international
characters).

    >>> shape.longName()
    u'|pPlane1|pPlaneShape1'
    >>> shape.name()
    u'pPlaneShape1'
    
We can also get information specific to this mesh:
    
    >>> shape.numEdges()
    220
    >>> shape.numVertices()
    121
    >>> shape.vtx[0]
    MeshVertex(u'pPlaneShape1.vtx[0]')

On the last line you see that vertices have their own class as well, `MeshVertex`.

---------------------------------------
Getting Help
---------------------------------------

If you are ever unsure of what method to use, just use the builtin python help command on the node class (the capitalized node type):

    >>> help(Camera)   #doctest: +SKIP

You can do the same thing for any function as well.

    >>> help(ls)   #doctest: +SKIP


---------------------------------------
Attributes
---------------------------------------

I think it's time we learned how to set some attributes.  Let's go back and take a look at our plane's transform and access an `Attribute`
object.  Just like nodes, attributes have their own class with methods that encompass the dozens of MEL commands for
operating on them.

    >>> plane.translateX
    Attribute(u'pPlane1.translateX')

To get and set attributes:

    >>> plane.translateX.get()
    0.0
    >>> plane.translateX.set(10.0)
    
Here's a few examples of how to query and edit properties of attributes:

    >>> plane.translateX.isLocked()
    False
    >>> plane.translateX.setLocked(True)
    >>> 
    >>> plane.translateX.isKeyable()
    True
    >>> plane.translateX.setKeyable(False)  

---------------------------------------
Connections
---------------------------------------

Now let's look into getting other objects connected to our plane shape.  The `Attribute.connections` method accepts the 
same flags as the procedural command `listConnections`.  

    >>> # below we get incoming and outgoing connections
    >>> shape.connections()
    [ShadingEngine(u'initialShadingGroup'), PolyPlane(u'polyPlane1')]
    >>> # 'inputs' is a shorcut to connections(source=True)
    >>> shape.inputs()
    [PolyPlane(u'polyPlane1')]
    >>> # 'outputs' is a shorcut to connections(source=False)
    >>> shape.outputs()
    [ShadingEngine(u'initialShadingGroup')]

Notice that when we enable the ``plugs`` flag that the result becomes an `Attribute`

    >>> shape.inputs(plugs=1)
    [Attribute(u'polyPlane1.output')]

Here's another handy feature of python: it supports 2D arrays, meaning you can put lists inside lists.  PyMEL takes advantage of
that in many situations, including when we use the ``connections`` flag, which causes `listConnections` to list source-destination
pairs.

    >>> shape.connections(c=1, p=1)
    [(Attribute(u'pPlaneShape1.instObjGroups[0]'), Attribute(u'initialShadingGroup.dagSetMembers[0]')), (Attribute(u'pPlaneShape1.inMesh'), Attribute(u'polyPlane1.output'))]

This is particularly useful for looping:

    >>> for source, destination in shape.connections(c=1, p=1):
    ...     print source, destination
    ... 
    pPlaneShape1.instObjGroups[0] initialShadingGroup.dagSetMembers[0]
    pPlaneShape1.inMesh polyPlane1.output

---------------------------------------
Using Existing Objects by Name
---------------------------------------

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing object by name. PyMEL
provides two ways of doing this. Both of them will automatically choose the correct PyMEL class for your object.

The `PyNode` class:
    >>> PyNode( 'defaultRenderGlobals').startFrame.get()
    1.0

The SCENE object ( an instance of the `Scene` class ) :
    >>> SCENE.defaultRenderGlobals.startFrame.get()
    1.0

---------------------------------------
Mel Scripts
---------------------------------------

Calling mel scripts through maya.mel.eval is a nuisances because it requires so much string formatting on 
the programmer's part.  `pymel.mel` handles all of that for you so you can use your mel scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. 

    
Check out `pymel.core.Mel` for more information.


---------------------------------------
Transitioning Tips
---------------------------------------


All of the MEL functions in maya.cmds exist in pymel, with a few exceptions ( see `Module Namespaces`_ ).  MEL functions that operate on nodes and/or attributes
almost always fall into one or more of these categories:  creating, listing, querying/editing. 
As you begin shifting toward a more object-oriented approach, you will still retain the need for procedural programming.
Use these guidelines for what aspects of PyMEL are best suited to object-oriented programming:


    1. creating nodes and UI elements : remains mostly procedural
    2. listing objects and UI elements:  object-oriented, except for general listing commands like `ls`
    3. querying and editing objects and UI elements:  object-oriented, except for commands that operate on many nodes at once, like `select` and `delete`


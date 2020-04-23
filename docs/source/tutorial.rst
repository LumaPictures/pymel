.. currentmodule:: pymel.core

=======================================
Getting Started
=======================================

This tutorial assumes that you have some familiarity with python, but even if you only have MEL experience, you'll probably be able to follow along. If you are a MEL scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly the section `Using Python <http://download.autodesk.com/us/maya/2008help/General/Using_Python.html>`__. This will help you to understand 
the differences in syntax between the two languages and how to translate between them. 

---------------------------------------------------------
Formatting: Read Me First to Avoid Confusion
---------------------------------------------------------


The code in these tutorials is formatted as you would see it in Maya's Script Editor; however, the majority of the documentation outside of these tutorials is formatted as you would see it in a :doc:`python interpreter <standalone>`, which is standard for python documentation.

In an external interpreter::
    
        >>> ls(type='camera')[0]
        nt.Camera('frontShape')
        
Maya's script editor:: 
    
        ls(type='camera')[0]
        # Result: frontShape

You might notice that the differences go beyond formatting. Although it is not the case, it appears as though the same commands return two different results: ``nt.Camera(u'frontShape')`` and ``frontShape``. Prior to version 2011, Autodesk chose to deviate from the standard python practice of using an object's reproduction strings -- as returned by ``repr()`` -- to display results, instead they use the object's string representation -- as returned by ``str()``.  This inevitably leads to confusion. 

Here's how you can get more informative results in the Script Editor::

    repr(ls(type='camera')[0]) 
    # Result: nt.Camera(u'frontShape')

here's a shorthand for the same thing::

    `ls(type='camera')[0]`
    # Result: nt.Camera(u'frontShape')

.. 
    Another great way to learn how to translate 
    mel into python is to install the new `Script Editor`_. With it you can execute some mel code and watch the 
    python output in the top pane. You can toggle back and forth by checking and unchecking the "Convert Mel to Python" checkbox.




    
---------------------------------------------------------
Example 1: The Basics
---------------------------------------------------------

Importing PyMEL
===============

To get started we need to import the pymel module::

    from pymel.core import *
    
This brings everything in pymel into the main namespace, meaning that you won't have to prefix the maya commands with the module name. 

.. warning::

    One problem with ``maya.cmds`` is that importing it into the root namespace (e.g. ``from maya.cmds import *``) is dangerous because it will override several of python's more important built-in methods. PyMEL is designed to be safe to import into the root namespace so that scripts can be written much more concisely. However, if you are a python novice, you might want to keep pymel in its own namespace, because, **unlike in MEL, in python you can "overwrite" functions if you are not careful**::
    
        from pymel.core import *
        s = sphere() # create a nurbsSphere
        sphere = 'mySphere'  # oops, we've overwritten the sphere command with a string
        sphere()
        # Error: name 'sphere' is not defined
        # Traceback (most recent call last):
        #   File "<maya console>", line 1, in <module>
        # NameError: name 'sphere' is not defined # 

.. note::

    All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( ``file``, ``filter``, ``eval``, ``help``, and ``quit``). The conflicting commands can be found in the `pymel.cmds` namespace, along with all of the unaltered maya commands.   
    
An Intro to PyMEL Objects in Maya
=================================

Before we proceed let's make sure we have a clean scene so that you'll get the same results as me::

    f=newFile(f=1) #start clean

Let's start by listing the cameras in the scene.  We do this in the same way that we would with ``maya.cmds``::

    ls(type='camera')
    # Result: [nt.Camera(u'frontShape'), nt.Camera(u'perspShape'), nt.Camera(u'sideShape'), nt.Camera(u'topShape')]

Just for comparison, let's do the same thing using ``maya.cmds``::

    import maya.cmds as cmds
    cmds.ls(type='camera')
    # Result: [u'frontShape', u'perspShape', u'sideShape', u'topShape']

Notice the difference in the returned results.  In the second example using ``maya.cmds``, the `ls <general.ls>` function returns a list of strings. For those of us coming from a MEL background, a list of names as strings is what we would expect out of ``ls``. PyMEL returns something much better -- instances of `PyNode <general.PyNode>` classes -- which are like strings on steroids. In addition to :term:`methods` for operating on node *names* as strings, these classes have methods for operating on the type of node or UI element that the string represents. 

.. note:: 
    object oriented programming introduces the concept of classes or "types", and each occurrence of a type is called an instance. For example, a string is a *type* of object that represents a series of characters. An *instance* of a string could be the word 'hello'.  You'll probably find that the concepts behind object oriented programming are fairly familiar, because Maya itself is designed in a very object-oriented way. Maya has many types of nodes, each with its own attributes, properties, and capabilities. Each unique occurrence of one of these node types in your scene is like an instance of a class in python. 

    The great thing about python is, unlike MEL, we're not stuck with the default data types. We can make new types!  That's a big part of what PyMEL adds: new Maya-specific data types to represent nodes, attributes, UI elements, vectors, matrices, etc.

Let's use one of these camera objects to get some information.  To do this using ``maya.cmds`` we might write something like this::

    cam = ls(type='camera')[0]
    camera( cam, query=True, aspectRatio=True)
    # Result: 1.5
    camera( cam, query=True, focalLength=True)
    # Result: 35.0
    camera( cam, edit=True, focalLength=20)
    
Rewriting this in an object-oriented way is fairly straight-forward::
        
    cam = ls(type='camera')[0]
    cam.getAspectRatio()
    # Result: 1.5
    cam.getFocalLength()
    # Result: 35.0
    cam.setFocalLength(20)
    
The two examples start out the same way: with the `ls <general.ls>` function. This is how we get our raw material to work with, in this case our node objects. In general, we can get nodes in 3 ways: 
  - list them based on some criteria
  - create them
  - get them by their name if we know it
 
Once we have our list of nodes, we can begin to work in an object-oriented fashion. There is not a hard-fast rule for converting from a procedural style to an object-oriented one, but here are some general guidelines:
  - the argument to the command -- in this case ``cam`` -- becomes the operating object on the left
  - instead of flags -- ``focalLength`` and ``aspectRatio`` we use methods, which are attached to right of the object with a period ``.``
  - query methods are typically prefixed with 'get' and edit methods are prefixed with 'set'.  If a query does not have a corresponding edit, it may not have a 'get' prefix.

So, in our case ``query=True, aspectRatio=True`` becomes ``.getAspectRatio``.  And ``query=True, focalLength=True`` becomes ``.getFocalLength``.


Getting Help
============

If you are ever unsure of what method to use, just use the builtin python ``help`` command on the node class (the capitalized node type).  First find out what type of node you're working with.  we'll continue from the example above, with our ``cam`` variable::

    print repr(cam)
    
This prints ``nt.Camera(u'frontShape')``. The ``nt.Camera`` part tells you what type of object it is. Now we can get help on that object type::

    help(nt.Camera)

This prints all the documentation on the `Camera <nodetypes.Camera>` node type. If you want help on a particular method, you can do this::

    help(nt.Camera.getFocalLength)

You can do the same thing for any function as well::

    help(ls)
    
---------------------------------------------------------
Example 2: Transitioning from Procedural Programming
---------------------------------------------------------

Let's look at another simple procedural example in which we find a camera, get it's transform node, then get the z component of its translation:: 

    cam = ls(type='camera')[0]
    parent = listRelatives(cam, p=1)[0]
    trans = xform(parent,q=1,t=1)
    `trans`
    # Result: [28.0, 21.0, 28.0]
    trans[2]
    # Result: 28.0

Now let's convert this to an object-oriented style.

Instead of `listRelatives`, we can use use methods available on ``cam``, which is a `nodetypes.Camera` class ( which can also be referred to by the shorthand ``nt.Camera``). ``nodetypes.Camera`` inherits from `nodetypes.DagNode`, so it has methods such as :meth:`getParent <nodetypes.DagNode.getParent>`, and :meth:`getChildren <nodetypes.DagNode.getChildren>`.  In this case, we'll use ``getParent``::

    cam = ls(type='camera')[0]
    parent = cam.getParent() # <---
    trans = xform(parent,q=1,t=1)
    `trans`
    # Result: [28.0, 21.0, 28.0]
    trans[2]
    # Result: 28.0
        
Next, instead of `xform <general.xform>`, we can use the :meth:`getTranslation <nodetypes.Transform.getTranslation>` method of the `nodetypes.Transform` node::

    cam = ls(type='camera')[0]
    parent = cam.getParent()
    trans = parent.getTranslation() # <---
    `trans`
    # Result: dt.Vector([28.0, 21.0, 28.0])
    trans.z
    # Result: 28.0

Now, let's chain these commands together to compare procedural versus object-oriented.

procedural::

    xform( listRelatives( ls(type='camera')[0], p=1)[0],q=1,t=1)[2]
    # Result: 28.0

object-oriented::

    ls(type='camera')[0].getParent().getTranslation().z
    # Result: 28.0

In procedural programming, you take the result of one function and feed it into the arguments of another function, but in object oriented programming, functions are associated with -- you might even say "attached to" -- the returned objects themselves, so the chaining of functions is much easier to read.  The object-oriented approach is shorter even though the procedural approach uses short flag names that obscure their purpose.

One thing that should be clear by now is that you can continue to code in a procedural way using PyMEL, because the `pymel.core` module provides the same set of :ref:`MEL-derived <why_wrappers>` commands as ``maya.cmds``, but  PyMEL wraps all of these commands to return powerful PyMEL node classes, so you can begin mixing in object-oriented code as you become more comfortable with it.

---------------------------------------
Example 3: Some More OO Basics
---------------------------------------

Now let's create a node::

    objs = polyPlane()
    objs
    # Result: [nt.Transform(u'pPlane1'), nt.PolyPlane(u'polyPlane1')]

You can see that, like the `ls <general.ls>` command, the `polyPlane <modeling.polyPlane>` command also returns `PyNode <general.PyNode>` classes.  As in MEL, it returns a list: the first object is the tranform of the plane, and the second is the construction history. Now let's get the shape of the transform::

    # assign the transform from above to a variable
    plane = objs[0]
    shape = plane.getShape()
    `shape`
    # Result: nt.Mesh(u'pPlaneShape1')
    
So, we can clearly see that the shape is a Mesh. Let's explore the `nodetypes.Mesh` object a little. We can get the name as a string, formatted in different ways (the ``u`` in front of the string denotes that it is a unicode string, meaning it can represent international characters).::

    shape.longName()
    # Result: |pPlane1|pPlaneShape1
    shape.name()
    # Result: pPlaneShape1
    
We can also get information specific to this mesh::
    
    shape.numEdges()
    # Result: 220
    shape.numVertices()
    121
    `shape.vtx[0]`
    # Result: MeshVertex(u'pPlaneShape1.vtx[0]')

On the last line you see that vertices have their own class as well, `MeshVertex <general.MeshVertex>`.  More on that later.



Attributes
==========

I think it's time we learned how to set some attributes.  Let's go back and take a look at our plane's transform and access an `Attribute <general.Attribute>` object. Just like nodes, attributes have their own class with methods that encompass the dozens of MEL commands for operating on them.::

    print `plane.translateX`
    # Result: Attribute(u'pPlane1.translateX')

To get and set attributes::

    plane.translateX.get()
    # Result: 0.0
    plane.translateX.set(10.0)
    
Here's a few examples of how to query and edit properties of attributes::

    plane.translateX.isLocked()
    # Result: False
    plane.translateX.setLocked(True)
    plane.translateX.isKeyable()
    # Result: True
    plane.translateX.setKeyable(False)  


Connections
===========

Now let's look into getting other objects connected to our plane shape.  The :meth:`Attribute.connections <general.Attribute.connections>` method accepts the 
same flags as the procedural command `listConnections`. 

Below we get incoming and outgoing connections::

    shape.connections()
    # Result: [ShadingEngine(u'initialShadingGroup'), PolyPlane(u'polyPlane1')]
    
`inputs <general.Attribute.inputs>` is a shorcut to ``connections(source=True)``::

    shape.inputs()
    # Result: [PolyPlane(u'polyPlane1')]
    
`outputs <general.Attribute.outputs>` is a shorcut to ``connections(source=False)``::

    shape.outputs()
    # Result: [ShadingEngine(u'initialShadingGroup')]

Notice that when we enable the ``plugs`` flag that the result becomes an `Attribute <general.Attribute>` instead of a node type.::

    shape.inputs(plugs=1)
    # Result: [Attribute(u'polyPlane1.output')]

Here's another handy feature of python: it supports 2D arrays, meaning you can put lists inside lists.  PyMEL takes advantage of that in many situations, including when we enable the ``connections`` flag, which causes `listConnections` to list source-destination pairs.::

    shape.connections(c=1, p=1)
    # Result: [(Attribute(u'pPlaneShape1.instObjGroups[0]'), Attribute(u'initialShadingGroup.dagSetMembers[0]')), (Attribute(u'pPlaneShape1.inMesh'), Attribute(u'polyPlane1.output'))]

This is particularly useful for looping

.. testcode::

    for source, destination in shape.connections(c=1, p=1):
    ...     print source, destination

.. testoutput::

    pPlaneShape1.instObjGroups[0] initialShadingGroup.dagSetMembers[0]
    pPlaneShape1.inMesh polyPlane1.output


Using Existing Objects by Name
==============================

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing object by name. PyMEL provides two ways of doing this. Both of them will automatically choose the correct PyMEL class for your object.

The `PyNode <general.PyNode>` class::

    PyNode( 'defaultRenderGlobals').startFrame.get()
    # Result: 1.0

The SCENE object ( an instance of the `Scene` class ) ::

    SCENE.defaultRenderGlobals.startFrame.get()
    # Result: 1.0


Mel Scripts
===========

Calling MEL scripts through ``maya.mel.eval`` is a nuisance because it requires so much string formatting on 
the programmer's part.  ``pymel.mel`` handles all of that for you so you can use your MEL scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. 

See out `pymel.core.language.Mel` for more information.


---------------------------------------
Transitioning Tips
---------------------------------------

What to Change
==============

All of the MEL functions in ``maya.cmds`` exist in ``pymel``, with a few exceptions ( see :doc:`modules` ).  MEL functions that operate on nodes and/or attributes almost always fall into one or more of these categories:  creating, listing, querying/editing.  As you begin shifting toward a more object-oriented approach, you will still retain the need for procedural programming.
Use these guidelines for what aspects of PyMEL are best suited to object-oriented programming:

    1. creating nodes and UI elements : remains mostly procedural
    2. listing objects and UI elements:  object-oriented, except for general listing commands like `ls`
    3. querying and editing objects and UI elements:  object-oriented, except for commands that operate on many nodes at once, like `select` and `delete`

Partial Conversion is Bad, mmkay
================================

Mixing ``maya.cmds`` module with ``pymel.core`` will result in problems, because ``maya.cmds`` doesn't know what to do with anything other than very basic data types. Passing a `PyNode <general.PyNode>`, `Matrix <datatypes.Matrix>`, `Vector <datatypes.Vector>`, or other custom type to a ``maya.cmds`` function will result in errors.  Your best bet is to completely replace ``maya.cmds`` with ``pymel`` throughout your code in one go.  This might sound frightening, but it will ultimately lead to fewer errors than partial PyMEL integration.  The  purely procedural part of ``pymel.core`` will behave exactly the same as ``maya.cmds`` as long as it is replaced wholesale, but if it is not, results returned from PyMEL functions will cause errors when passed to ``maya.cmds`` functions, and results from ``maya.cmds`` will need to be cast to PyNodes.   

There are only a handful of ``maya.cmds`` wraps in PyMEL that are not backward compatible. They all fall into the category of functions which now return a list of tuple pairs instead of a flat list::

    listConnections( connections=True )
    keyframe( q=True, valueChange=True )
    keyframe( q=True, timeChange=True )
    ls( showType=True )

These changes are all noted in the docstrings of each function.

---------------------------------------
Glossary
---------------------------------------

.. glossary::

    methods
        a method is a function bound to an object. ex. 'bar' is the method in ``foo.bar()``

.. currentmodule:: pymel

=======================================
Getting Started
=======================================

This tutorial assumes that you have some familiarity with python, but even if you only have MEL experience, you'll probably be able to follow along. If you are a MEL scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly the section `Using Python <http://download.autodesk.com/us/maya/2008help/General/Using_Python.html>`__. This will help you to understand 
the differences in syntax between the two languages and how to translate between them. 

.. note:: The code in these tutorials is formatted as you would see it in Maya's script editor; however, the majority of the documentation outside of these tutorials is formatted as you would see it in a :doc:`python interpreter <standalone>`, which is standard for python documentation.

	Maya's script editor::
	
		ls(type='camera')
		# Result: [Camera(u'frontShape'), Camera(u'perspShape'), Camera(u'sideShape'), Camera(u'topShape')] # 

	In an external interpreter::
	
		>>> ls(type='camera')
		[Camera(u'frontShape'), Camera(u'perspShape'), Camera(u'sideShape'), Camera(u'topShape')]
.. 
	Another great way to learn how to translate 
	mel into python is to install the new `Script Editor`_. With it you can execute some mel code and watch the 
	python output in the top pane. You can toggle back and forth by checking and unchecking the "Convert Mel to Python" checkbox.

	
---------------------------------------------------------
Example 1: The Basics
---------------------------------------------------------

Importing PyMEL
===============

To get started we need to import the pymel module.::

	from pymel import *
	
This brings everything in pymel into the main namespace, meaning that you won't have to prefix the maya commands with the module name. 

.. warning::

	One problem with ``maya.cmds`` is that importing it into the root namespace (e.g. ``from maya.cmds import *``)
	is dangerous because it will override several of python's more important built-in methods. PyMEL is designed
	to be safe to import into the root namespace so that scripts can be written much more concisely. However, if you are
	a python novice, you might want to keep pymel in its own namespace, because, unlike in MEL, in python you can "overwrite" functions
	if you are not careful::
	
		from pymel import *
		s = sphere() # create a nurbsSphere
		sphere = 'mySphere'	 # oops, we've overwritten the sphere command with a string
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

Next, we need some nodes to work with.	In general, we can get nodes in 3 ways: 
  - list them based on some criteria
  - create them
  - get them by their name if we know it

Let's start by listing the cameras in the scene.  We do this in the same way that we would with ``maya.cmds``::

	ls(type='camera')
	# Result: [Camera(u'frontShape'), Camera(u'perspShape'), Camera(u'sideShape'), Camera(u'topShape')]

Just for comparison, let's do the same thing using ``maya.cmds``::

	import maya.cmds as cmds
	cmds.ls(type='camera')
	# Result: [u'frontShape', u'perspShape', u'sideShape', u'topShape']

Notice the difference in the returned results.	In the second example using ``maya.cmds`` the ``ls`` function returns a list of strings. For those of us coming from a MEL background, a list of names as strings is what we would expect out of `ls`. PyMEL returns something much better -- instances of `PyNode` classes -- which are like strings on steroids. In addition to :term:`methods` for operating on node *names* as strings, these classes have methods for operating on the type of node or UI element that the string represents. 

.. note:: object oriented programming introduces the concept of classes or "types", and each occurrence of a type is called an instance. For example, a string is a *type* of object that represents a series of characters. An *instance* of a string could be the word 'hello'.  You'll probably find that the concepts behind object oriented programming are fairly familiar, because Maya itself is designed in a very object-oriented way. Maya has many types of nodes, each with its own attributes, properties, and capabilities. Each unique occurrence of one of these node types in your scene is like an instance of a class in python. 

The great thing about python is, unlike MEL, we're not stuck with the default data types. We can make new types!  That's a big part of what PyMEL adds: new Maya-specific data types to represent nodes, attributes, UI elements, vectors, matrices, etc.

Let's use one of these camera objects to get some information::
		
	cam = ls(type='camera')[0]
	cam.getAspectRatio()
	# Result: 1.5
	cam.getFocalLength()
	# Result: 35.0

So, there you can see some examples of object-oriented programming using PyMEL.  Not so hard, is it?  For reference, here's the same thing done in  a procedural way::

	cam = ls(type='camera')[0]
	camera( cam, q=True, aspectRatio=True)
	# Result: 1.5
	camera( cam, q=True, focalLength=True)
	# Result: 35.0
	
The code above is using PyMEL. This illustrates an important point: you can continue to code in a procedural way using PyMEL, because PyMEL provides the same set of :ref:`MEL-derived <why_wrappers>` commands as ``maya.cmds``, but because PyMEL wraps all of these commands to return powerful PyMEL node classes, you can begin mixing in object-oriented code as you become more comfortable with it.

---------------------------------------------------------
Example 2: Transitioning from Procedural Programming
---------------------------------------------------------

Let's look at another simple example in which we find a camera, get it's transform node, then get the z component of its translation:: 

	cam = ls(type='camera')[0]
	parent = listRelatives(cam, p=1)[0]
	trans = xform(parent,q=1,t=1)
	trans
	# Result: [28.0, 21.0, 28.0]
	trans[2]
	# Result: 28.0


Instead of `listRelatives`, we can use use methods available on `DagNode`, such as :meth:`getParent <DagNode.getParent>`, :meth:`getShape <DagNode.getShape>`, :meth:`getChildren <DagNode.getChildren>`.  In this case, we'll use ``getParent``::

	cam = ls(type='camera')[0]
	parent = cam.getParent() # <---
	trans = xform(parent,q=1,t=1)
	trans
	# Result: [28.0, 21.0, 28.0]
	trans[2]
	# Result: 28.0
		
Or, instead of `xform`, we can use the :meth:`getTranslation <Transform.getTranslation>` method of the `Transform` node::

	cam = ls(type='camera')[0]
	parent = cam.getParent()
	trans = parent.getTranslation() # <---
	trans
	# Result: datatypes.Vector([28.0, 21.0, 28.0])
	trans.z
	# Result: 28.0

Now, let's chain these commands together to compare procedural versus object-oriented::

	xform( listRelatives( ls(type='camera')[0], p=1)[0],q=1,t=1)[2]
	# Result: 28.0

::

	ls(type='camera')[0].getParent().getTranslation().z
	# Result: 28.0

In procedural programming, you take the result of one function and feed it into the arguments of another function, but in object oriented programming, functions are associated with -- you might even say "attached to" -- the returned objects themselves, so the chaining of functions is much easier to read.  The object-oriented approach is shorter even though the procedural approach uses short flag names that obscure their purpose.


Getting Help
============

If you are ever unsure of what method to use, just use the builtin python help command on the node class (the capitalized node type)::

	help(Camera)

You can do the same thing for any function as well.::

	help(ls)


---------------------------------------
Example 3: Some More OO Basics
---------------------------------------

Now let's create a node::

	objs = polyPlane()
	objs
	# Result: [Transform(u'pPlane1'), PolyPlane(u'polyPlane1')]

You can see that, like the `ls` command, the `polyPlane` command also returns `PyNode` classes.	 As in MEL, it returns a list: the
first object is the tranform of the plane, and the second is the construction history. Now let's get the shape of the transform::

	# assign the transform from above to a variable
	plane = objs[0]
	shape = plane.getShape()
	shape
	# Result: Mesh(u'pPlaneShape1')
	
So, we can clearly see that the shape is a Mesh. Let's explore the `Mesh` object a little. We can get the name as a string, 
formatted in different ways (the ``u`` in front of the string denotes that it is a unicode string, meaning it can represent international characters).::

	shape.longName()
	# Result: |pPlane1|pPlaneShape1
	shape.name()
	# Result: pPlaneShape1
	
We can also get information specific to this mesh::
	
	shape.numEdges()
	# Result: 220
	shape.numVertices()
	121
	print `shape.vtx[0]`
	# Result: MeshVertex(u'pPlaneShape1.vtx[0]')

On the last line you see that vertices have their own class as well, `MeshVertex`.	More on that later.



Attributes
==========

I think it's time we learned how to set some attributes.  Let's go back and take a look at our plane's transform and access an `Attribute` object. Just like nodes, attributes have their own class with methods that encompass the dozens of MEL commands for operating on them.::

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

Now let's look into getting other objects connected to our plane shape.	 The :meth:`Attribute.connections` method accepts the 
same flags as the procedural command `listConnections`.	

Below we get incoming and outgoing connections::

	shape.connections()
	# Result: [ShadingEngine(u'initialShadingGroup'), PolyPlane(u'polyPlane1')]
	
`inputs <Attribute.inputs>` is a shorcut to ``connections(source=True)``::

	shape.inputs()
	# Result: [PolyPlane(u'polyPlane1')]
	
`outputs <Attribute.outputs>` is a shorcut to ``connections(source=False)``::

	shape.outputs()
	# Result: [ShadingEngine(u'initialShadingGroup')]

Notice that when we enable the ``plugs`` flag that the result becomes an `Attribute` instead of a node type.::

	shape.inputs(plugs=1)
	# Result: [Attribute(u'polyPlane1.output')]

Here's another handy feature of python: it supports 2D arrays, meaning you can put lists inside lists.	PyMEL takes advantage of
that in many situations, including when we enable the ``connections`` flag, which causes `listConnections` to list source-destination
pairs.::

	shape.connections(c=1, p=1)
	# Result: [(Attribute(u'pPlaneShape1.instObjGroups[0]'), Attribute(u'initialShadingGroup.dagSetMembers[0]')), (Attribute(u'pPlaneShape1.inMesh'), Attribute(u'polyPlane1.output'))]

This is particularly useful for looping

.. testcode::

	for source, destination in shape.connections(c=1, p=1):
	...		print source, destination

.. testoutput::

	pPlaneShape1.instObjGroups[0] initialShadingGroup.dagSetMembers[0]
	pPlaneShape1.inMesh polyPlane1.output


Using Existing Objects by Name
==============================

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing object by name. PyMEL
provides two ways of doing this. Both of them will automatically choose the correct PyMEL class for your object.

The `PyNode` class::

	PyNode( 'defaultRenderGlobals').startFrame.get()
	# Result: 1.0

The SCENE object ( an instance of the `Scene` class ) ::

	SCENE.defaultRenderGlobals.startFrame.get()
	# Result: 1.0


Mel Scripts
===========

Calling mel scripts through maya.mel.eval is a nuisance because it requires so much string formatting on 
the programmer's part.	`pymel.mel` handles all of that for you so you can use your mel scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. 

	
Check out `pymel.Mel` for more information.


---------------------------------------
Transitioning Tips
---------------------------------------


All of the MEL functions in maya.cmds exist in pymel, with a few exceptions ( see :doc:`modules` ).	 MEL functions that operate on nodes and/or attributes
almost always fall into one or more of these categories:  creating, listing, querying/editing. 
As you begin shifting toward a more object-oriented approach, you will still retain the need for procedural programming.
Use these guidelines for what aspects of PyMEL are best suited to object-oriented programming:


	1. creating nodes and UI elements : remains mostly procedural
	2. listing objects and UI elements:	 object-oriented, except for general listing commands like `ls`
	3. querying and editing objects and UI elements:  object-oriented, except for commands that operate on many nodes at once, like `select` and `delete`


---------------------------------------
Glossary
---------------------------------------

.. glossary::

	methods
		a method is a function bound to an object. ex. 'bar' is the method in ``foo.bar()``

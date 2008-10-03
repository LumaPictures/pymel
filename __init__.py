
# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com
 
"""
=====
Pymel
=====

Pymel makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of mel commands into python commands. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. Pymel
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.

.. contents:: :backlinks: none

=========================
What's New in Version 0.8
=========================

-------------------------------
Non-Backward Compatible Changes
-------------------------------
	- Renamed Classes:
		- Vector --> `MVector`
		- Matrix --> `MMatrix`
	- Changed and Renamed Functions:
		- Attribute disconnection operator has changed from <> to //
	- Node classes no longer inherit from unicode: see section `API Underpinnings`

	
---------------------------		
Other Additions and Changes
---------------------------
	- Module reorganization: 
		- `core` is the primary module for maya commands and node classes
			- Its sub-modules correspond to the groupings in the maya command documentation
				- `animation`
				- `effects`
				- `general`: encompasses old 'core' and 'node' modules
				- `language`
				- `modeling`
				- `rendering`
				- `system`: previously 'io'
				- `windows`: previously 'ui'
			- It also contains special-purpose sub-modules
				- `context`: previously 'ctx', contains context tools
				- `runtime`: runtime commands
				- `other`: for commands which are not included in the maya documentation (such as commands created by plugins)
		
	
	- New Classes:
		- `MelGlobals` class, for more streamlined access to mel global variables

				
	- Maya Bug Fixes


	- Pymel Bug Fixes

				
	- Other Improvements
		- commands and classes created by plugins are now properly created on load and removed on unload
		
========================
Installation
========================

-------------
Pymel Package
-------------

If on linux or osx, the simplest way to install pymel is to place the unzipped pymel folder in your scripts directory 

=========   =======================
Platform    Location
=========   =======================
mac         ~/Library/Preferences/Autodesk/maya/8.5/scripts
linux       ~/maya/maya/8.5/scripts
=========   =======================
	
However, it is usually a good idea to create a separate directory for your python scripts so that you can organize them independently
of your mel scripts.  You can do this by setting the PYTHONPATH environment variable in your Maya.env file. Set the PYTHONPATH environment
variable to the directory *above* the pymel folder.  For example, if the pymel folder on your machine is C:\My Documents\python\pymel 
then you would add this line to your Maya.env::  

	PYTHONPATH = C:\My Documents\python

Next, to avoid having to import pymel every time you startup, you can create a userSetup.mel
file, place it in your scipts directory and add this line::

	python("from pymel import *");

Alternately, you can create a userSetup.py file and add the line::

	from pymel import *

Note that if you have your PYTHONPATH set in a shell resource file, this value will override your Maya.env value.

-------------
Script Editor
-------------
Pymel includes a replacement for the script editor window that provides the option to translate all mel history into python. 
Currently this feature is beta and works only in versions beginning with Maya 8.5 SP1.

The script editor is comprised of two files located in the pymel/tools/scriptEditor directory: scriptEditorPanel.mel and pymelScrollFieldReporter.py.  
Place the mel file into your scripts directory, and the python file into your Maya plugins directory. Open Maya, go-to 
**Window --> Settings/Preferences --> Plug-in Manager** and load pymelScrollFieldReporter.  Be sure to also check 
"Auto Load" for this plugin. Next, open the Script Editor and go to **History --> History Output --> Convert 
Mel to Python**. Now all output will be reported in python, regardless of whether the input is mel or python.

Problems with Maya 2008-x64 on Linux
====================================

If you encounter an error loading the plugin in maya 2008 on 64-bit linux, you may have to fix a few symlinks. 
As root, or with sudo privileges do the following::

	cd /lib64
	ls -la libssl*

You might see something like the following returned::
	
	-rwxr-xr-x 1 root root 302552 Nov 30  2006 libssl.so.0.9.8b
	lrwxrwxrwx 1 root root     16 Jul 16  2007 libssl.so.6 -> libssl.so.0.9.8b

The distribution of python2.5 that comes with maya2008 expects libssl.so.4, but i have libssl.so.6.  So, I have to 
create a symbolic link to the real library (in my case libssl.so.0.9.8b, but it may differ depending on your distribution)::
	
	sudo ln -s libssl.so.0.9.8b libssl.so.4

The same thing must be done for libcrypto.so.4

===============
Getting Started
===============

If you are a mel scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly
the section `Using Python <http://download.autodesk.com/us/maya/2008help/General/Using_Python.html>`__. This will help you to understand 
the differences in syntax between the two languages and how to translate between them. Another great way to learn how to translate 
mel into python is to install the new Script Editor (instructions above). With it you can execute some mel code and watch the 
python output in the top pane. You can toggle back and forth by checking and unchecking the "Convert Mel to Python" checkbox.

----------
The Basics
----------

In its current incarnation, pymel is designed with a great deal of backward compatibility in mind, so that the maya.cmds
module and the pymel module can usually be used interchangably with the same code.  However, a closer look reveals pymel is actually
hiding a great deal of its power right under your nose.  Take the `ls` command for example.  `maya.cmds.ls` 
will return a list of strings.  These strings have a lot of built-in functionality that make them a much more 
powerful than strings in mel:

	>>> import maya.cmds
	>>> cam = maya.cmds.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> print cam[0] # indexable: get a single element of the string
	f
	>>> print cam[5:] # slicable: get a sub string
	Shape
	>>> new = cam.replace( 'front', 'monkey' )  # an example string operation
	>>> print new
	monkeyShape
		
So, already you have object-oriented power at your fingertips. When using pymel, the `ls` command still returns special `PyNode` classes,
which are like strings are on steroids: in addition to the built-in string methods ( a method is a function that belongs to a class ), 
pymel adds methods for operating on the type of object that the string represents:

	>>> import pymel
	>>> cam = pymel.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> print cam[0] # indexable
	f
	>>> print cam[5:]  # still has the string functionality as well
	Shape
	>>> cam.getFocalLength()  # but it has maya node methods too
	35.0
	>>> new = cam.replace( 'front', 'monkey' ) # be aware that string operations return strings not pymel nodes
	>>> print new, type(new), type(cam)
	monkeyShape <type 'unicode'> <class 'pymel.core.general.Camera'>
	
The same goes for other objects when using pymel.  When getting a triple attribute like translate or rotate, maya.cmds.getAttr
will return a list with three floats.  Pymel nodes, on the other hand, return a 3-element `MVector`. 

======================
Object-Oriented Design
======================

The pymel module reorganizes many of the most commonly used mel commands into a hierarchy of classes. This design allows 
you to write much more concise and readable python code. It also helps keep all of the commands organized, so that
functions are paired only with the types of objects that can use them.

All node classes inherit from the `DependNode` class. 
	
Understanding the `Attribute` class is essential to using pymel to its fullest extent.
	
In order to use the object-oriented design of pymel, you must ensure that the objects that you are working 
with are instances of pymel classes. To make this easier, pymel contains wrapped version 
of the more common commands for creating and getting lists of objects. These modified commands cast their results to the appropriate 
class type. See `ls`, `listRelatives`, `listTransforms`, `selected`, and `listHistory`, for a few examples.  

Commands that list objects return pymel classes:
	>>> s = ls(type='transform')[0]
	>>> print type(s)
	<class 'pymel.core.general.Transform'>
	
Commands that create objects are wrapped as well:
	>>> t = polySphere()[0]
	>>> print t, type(t)
	pSphere1 <class 'pymel.core.general.Transform'>
	

--------------------
Node Class Hierarchy
--------------------

Pymel uses data parsed from the maya documentation to reconstruct the maya node type hierarchy by creating
a class for every node type in the tree.  The name of the class is the node type captitalized.  Wherever possible,
pymel will return objects as instances of these classes. This allows you to use builtin python functions to inspect
and compare your objects.  For example:

	>>> dl = directionalLight()
	>>> type(dl)
	<class 'pymel.core.general.DirectionalLight'>
	>>> isinstance( dl, DirectionalLight)
	True
	>>> isinstance( dl, Light)
	True
	>>> isinstance( dl, Shape)
	True
	>>> isinstance( dl, DagNode)
 	True
	>>> isinstance( dl, Mesh)
 	False
 	
Many of these classes contain no methods of their own and exist only as place-holders in the hierarchy.
However, there are certain key classes which provide important methods to all their sub-classes. A few of the more important
include `DependNode`, `DagNode`, `Transform`, and `Constraint`.


------------------------------------------
Node Commands and their Class Counterparts
------------------------------------------

As you are probably aware, Mel contains a number of commands
which are used to create, edit, and query object types in maya.  Typically, the names of these commands correspond
with the node type on which they operate. However, it should be noted
that there are a handful of exceptions to this rule.

Some examples of command-class pairs.  Notice that the last two nodes do not match their corresponding command:

================    ================    =================
Mel Command         Maya Node Type      Pymel Node  Class
================    ================    =================
aimConstraint       aimConstraint       AimConstraint
camera              camera              Camera
directionalLight    directionalLight    DirectionalLight 
spaceLocator        locator             Locator
vortex              vortexField         VortexField
================    ================    =================

	

This example demonstrates some basic principles. Note the relationship between the name of the object
created, its node type, and its class type:

	>>> l = spotLight()
	>>> print "The name is", l
	The name is spotLightShape1
	>>> print "The maya type is", l.type()
	The maya type is spotLight
	>>> print "The python type is", type(l)	
	The python type is <class 'pymel.core.general.SpotLight'>

Once you have an instance of a pymel class (usually handled automatically), you can use it to query and edit the
maya node it represents in an object-oriented way.

make the light red and get shadow samples, the old, procedural way
	>>> spotLight( l, edit=1, rgb=[1,0,0] ) 
	>>> print spotLight( l, query=1, shadowSamples=1 ) 
	1
	
now, the object-oriented, pymel way
	>>> l.setRgb( [1,0,0] )
	>>> print l.getShadowSamples()   
	1

For those familiar with Mel, you can probably already tell that the DirectionalLight class can be understood as an 
object-oriented reorganization of the directionalLight command, where you 'get' queries and you 'set' edits.  

Some classes have functionality that goes beyond their command counterpart. The `Camera` class,
for instance, also contains the abilities of the `track`, `orbit`, `dolly`, and `cameraView` commands:

	>>> camTrans, cam = camera()
	>>> cam.setFocalLength(100)
	>>> cam.getFov()
	20.407947616896568
	>>> cam.dolly( distance = -3 )
	>>> cam.track(left=10)
	>>> cam.addBookmark('new')

------------------------------
Using Existing Objects by Name
------------------------------

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing the object by name. Pymel
provides two ways of doing this. Both of them will automatically choose	the correct pymel class for your object.

The `PyNode` command:
	>>> PyNode( 'defaultRenderGlobals').startFrame.get()
	1.0

The SCENE object:
	>>> SCENE.defaultRenderGlobals.startFrame.get()
	1.0

------------------
API Underpinnings
------------------

In mel, the best representation we have have of a maya node or attribute is its name.  But with the API we can do better!  
When creating an instance of a `PyNode` class, pymel determines the underlying API object behind the scenes.
With this in hand, it can operate on the object itself, not just the string representing the object.

So, what does this mean to you?  Well, let's take a common example: testing if two nodes or attributes are the
same. In mel, to accomplish this the typical solution is to perform a string comparison 
of the object names, but there are many ways that this seemingly simple operation can go wrong. For instance, forgetting to compare the
full paths of dag node objects, or comparing the long name of an attribute to the short name of an attribute.  
And what if you want to test if the nodes are instances of each other?  You'll have some pretty 
nasty string processing ahead of you.  But since pymel uses the underlying API objects, these operations are simple
and API-fast.

		>>> from pymel import *
		>>> # Make two instanced spheres in different groups
		>>> sphere1, hist = polySphere(name='mySphere')
		>>> grp = group(sphere1)
		>>> grp2 = instance(grp)[0]
		>>> sphere2 = grp2.getChildren()[0]
		>>> sphere1  # the original
		Transform('group1|mySphere')
		>>> sphere2  # the instance
		Transform('group2|mySphere')
		>>> sphere1 == sphere2  # they aren't the same dag objects
		False
		>>> sphere1.isInstance( sphere2 )  # but they are instances of each other
		True
		>>> sphere1.t == sphere1.translate
		True
		>>> sphere1.tx == sphere1.translate.translateX
		True

New PyNode Behavior
===================

PyNodes Are Not Strings
-----------------------

In previous versions of pymel, the node classes inherited from the builtin unicode string class.  With the introduction of the new API
underpinnings, the node classes inherit from a special `ProxyUnicode` class, which has the functionality of a string object, but
removes the immutability restriction ( see the next section `Mutability And You`_ ).  It is important to keep in mind, that although
PyNodes *behave* like strings, they are no longer actual strings. Functions which explicity require a string, and which worked 
with PyNodes in previous versions of pymel, might raise an error with version 0.8. For example:

	>>> objs = ls( type='camera')
	>>> print ', '.join( objs )
	Traceback (most recent call last):
		...
	TypeError: sequence item 0: expected string, Camera found

The solution is simple: convert the PyNodes to strings.  The following example uses a shorthand syntax called "list comprehension" to 
convert the list of PyNodes to a list of strings:

	>>> objs = ls( type='camera')
	>>> ', '.join( [ str(x) for x in objs ] )
	'cameraShape1, frontShape, perspShape, sideShape, topShape'

	
Mutability and You
------------------

One change that has come about due to the new API-based approach is node name mutability. You might have noticed
when working with strings in python that they cannot be changed "in place" -- all string operations return a new string. This is
because strings are immutable, and cannot be changed.

By inheriting from a mutable `ProxyUnicode` class instead of an immutable string, we are now able to provide a design which more accurately reflects 
how nodes work in maya --  when a node's name is changed it is still the same object with the same properties --  the name
is simply a label or handle. In practice, this
means that each time the name of the node is required -- such as printing, slicing, splitting, etc -- the object's current name
is queried from the underlying API object. This ensures that if the node is renamed by the user via the UI or mel the 
changes will always be reflected in the name returned by your PyNode class.

Renaming
~~~~~~~~

In versions of pymel previous to 0.8, the node classes inherited from python's built-in unicode
string type, which, due to its immutability, could cause unintuitive results with commands like rename.
The new behavior creates a more intuitve result.

New Behavior:
	>>> orig = polyCube()[0]
	>>> print orig, orig.exists()
	pCube1 True
	>>> orig.rename('crazyCube')
	Transform('crazyCube')
	>>> print "object %s still exists? %s" % (orig, orig.exists() )
	object crazyCube still exists? True
	
As you can see, you no longer need to assign the result of a rename to a variable, although, for backward
compatibility's sake, we've ensured that you still can.

Using as Keys in Dictionaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is one caveat to the mutability of node names: it can cause problems when using a pymel node as a key in a dictionary.
The reason is that the hash ( a hash is an integer value which is used to speed up dictionary access ) generated by a pymel node
is based on the node's name, which is subject to change.  

	>>> orig = polySphere()[0]
	>>> d = { orig :  True }
	>>> orig.rename('crazySphere')
	Transform('crazySphere')
	>>> print d[orig]
	Traceback (most recent call last):
		...
	KeyError: Transform('crazySphere')
	
This might seem like an obvious and necessary limitation, but we are working with Autodesk to provide a node hash which persists
even after the node is renamed, thereby providing an object-based immutability independent of name.


Non-Existent Objects
--------------------

Previous versions of pymel allowed you to instantiate classes for nonexistent objects.  This could be useful in circumstances where
you wished to use name formatting methods.
Starting with this version, an exception will be raised if the passed name does not represent an object in the scene.  As a result,
certain conventions for existence testing are no longer supported, while new ones have also been added.

We've added three new exceptions which can be used to test for existence errors when creating new PyNodes: `MayaObjectError`, 
`MayaNodeError`, and `MayaAttributeError`. 
	
	>>> for x in [ 'fooBar.spangle', 'superMonk' ] :
	...     try:
	...         PyNode( x )
	...         print "It Exists"
	...     except MayaNodeError:
	...         print "The Node Doesn't Exist:", x
	...     except MayaAttributeError:
	...         print "The Attribute Doesn't Exist:", x
	...
	The Attribute Doesn't Exist: fooBar.spangle
	The Node Doesn't Exist: superMonk

Both exceptions can be caught by using the parent exception `MayaObjectError`. In addition `MayaAttributeError` can also be caught
with the builtin exception `AttributeError`.

Note that you will get different exceptions depending on how you access the attribute. This is because the shorthand notation can also
be used to access functions, in which case the `MayaAttributeError` does not make sense to raise.  As mentioned above, you can always
use AttributeError to catch both.


Explicit notation:
	>>> x = polySphere()[0]
	>>> x.attr('myAttr')
	Traceback (most recent call last):
		...
	MayaAttributeError: Maya Attribute does not exist: 'pSphere2.myAttr'
	
Shorthand notation:
	>>> x = polySphere()[0]
	>>> x.myAttr
	Traceback (most recent call last):
		...
	AttributeError: Transform('pSphere3') has no attribute or method named 'myAttr'
	

Conventions for Testing Node Existence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No longer supported:
	>>> if PyNode( 'fooBar' ).exists(): #doctest: +SKIP
	...     print "It Exists"
	... else:
	...     print "It Doesn't Exist"
	It Doesn't Exist
		
Still supported:
	>>> if objExists( 'fooBar' ): 
	...     print "It Exists"
	... else:
	...     print "It Doesn't Exist"
	It Doesn't Exist
	
New construct:
	>>> try:
	...     PyNode( 'fooBar' )
	...     print "It Exists"
	... except MayaObjectError:
	...     print "It Doesn't Exist"
	It Doesn't Exist

Conventions for Testing Attribute Existence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No longer supported:
	>>> if PyNode( 'fooBar.spangle' ).exists(): #doctest: +SKIP
	...     print "Attribute Exists"
	... else:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist
	
No longer supported:
	>>> x = polySphere()[0] 
	>>> if x.myAttr.exists(): #doctest: +SKIP
	...     print "Attribute Exists"
	... else:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist

Still supported:
	>>> if objExists( 'fooBar.spangle' ):
	...     print "Attribute Exists"
	... else:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist

Still supported:
	>>> if mel.attributeExists( 'spangle','fooBar' ):
	...     print "Attribute Exists"
	... else:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist
			
New construct:	
	>>> x = polySphere()[0]
	>>> if x.hasAttr('myAttr'):
	...     print "Attribute Exists"
	... else:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist

New construct:
	>>> try:
	...     PyNode( 'fooBar.spangle' )
	...     print "Attribute Exists"
	... except MayaAttributeError:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist

New construct:
	>>> x = polySphere()[0]
	>>> try:
	...     x.myAttr
	...     print "Attribute Exists"
	... except AttributeError:
	...     print "Attribute Doesn't Exist"
	Attribute Doesn't Exist


------------------------------------------------------
Delving Deeper: Chained Function and Attribute Lookups
------------------------------------------------------

Mel provides the versatility of operating on a shape node via its transform node.  For example, these two commands work
interchangably::

	camera -q -centerOfInterest persp
	camera -q -centerOfInterest perspShape


pymel achieves this effect by chaining function lookups.  If a called method does not exist on the Transform class, the 
request will be passed to appropriate class of the transform's shape node, if it exists.
The chaining goes one further for object primitives, such as spheres, cones, etc.  For example:
	
create a sphere and return its transform
	>>> trans = polySphere()[0]
	>>> print type(trans)
	<class 'pymel.core.general.Transform'>
	
get the transform's shape
	>>> shape = trans.getShape()
	>>> print type( shape )
	<class 'pymel.core.general.Mesh'>
	
get the shape's history
	>>> hist = shape.history()[1]
	>>> type( hist )
	<class 'pymel.core.general.PolySphere'>
	
get the radius of the sphere 
	>>> hist.getRadius()
	1.0
	>>> # chained lookup allows the PolySphere.getRadus method to work on the Transform class  
	>>> trans.getRadius()
	1.0

the method getRadius belongs to the PolySphere class.  In this example, getRadius does not exist on the Transform class, so it passes
the request to its shape, which is a Poly class. The method does not exist here either, so the Poly class searches for its primary
construction history node, which is the polySphere node.  This node is cast to a PolySphere class which has the desired getRadius method,
which is then called.   

===========
Mel Scripts
===========

Calling mel scripts through maya.mel.eval is a nuisances because it requires so much string formatting on 
the programmer's part.  `pymel.mel` handles all of that for you so you can use your mel scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. see
`pymel.core.Mel` for more information.

=================
Module Namespaces
=================

Another problem with maya.cmds is that importing it into the root namespace (e.g. ``from maya.cmds import *``)
is dangerous because it will override several of python's more important built-in methods. pymel is designed
to be safe to import into the root namespace so that scripts can be written much more concisely. However, if you are
a python novice, you might want to keep pymel in its own namespace, because, unlike in mel, in python you can "overwrite" functions
if you are not careful:

	>>> from pymel import *
	>>> sphere() # create a nurbsSphere
	[Transform('nurbsSphere1'), MakeNurbSphere('makeNurbSphere1')]
	>>> sphere = 'mySphere'  # whoops, we've overwritten the sphere command with a string
	>>> sphere()
	Traceback (most recent call last):
		...
	TypeError: 'str' object is not callable
	
All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( file, filter, eval,
help, and quit). The conflicting commands can be found in the pymel.cmds namespace, along with all of the unaltered
maya commands.  

See `pymel.core.system` for more information on how the file command is implemented in pymel.

Even though pymel has a handful of modules, all but `pymel.runtime` are imported directly into the main namespace. The sub-modules are provided
primarily to improve the clarity of the documentation.

=================
Design Philosophy
=================

When approaching the reorganization of the existing commands provided by maya.cmds, pymel follows these practical guidelines:

	- a value returned by a get* function or query flag should be accepted as a valid argument by the corresponding set* function or edit flag
	- a function which returns a list should return an empty list (not None) if it finds no matches ( ex. ls, listRelatives )
	- a function which always returns a single item should not return that item in a list or tuple ( ex. spaceLocator )
	- wherever possible, pymel/python objects should be returned
	- a function which provides a mapping mechanism should have a dictionary-like pymel counterpart ( ex. fileInfo, optionVar )
	- a function which returns a list of pairs should be a 2D array, or possibly a dictionary ( ex. ls( showType=1 ), listConnections(connections=1) )
	- the arguments provided by a ui callback should be of the appropriate type ( as a test, it should be capable of being used to set the value of the control )

Pymel design rules:

	- node classes should never use properties -- all behavior should be placed in methods to differentiate them from shorthand attribute syntax ( ex. foo.bar retrieves an attribute, foo.bar() executes a function )
	- node classes are named after the nodes they control, not the mel commands that they proxy  ( ex. Locator vs. spaceLactor )
"""



"""
Version History
-0.1-	
first public release
-0.2-	
added Matrix class and revamped vector module
added Transform class with xform methods, and which delegates to child attributes when necessary
added MScene class for quick wrapping of pre-existing objects
added Attribute.remove() method for multi instance attributes
added menu commands to the pymel ui classes
added rwaExport example
-0.3-	
added duplicate command
added instance command
added listTransforms command
added Particle class
added Transform.hide() and Transform.show()
enhanced setAttr to handle stringArray datatypes more intelligently, and auto-set datatype for arrays
added force arg to setAttr which causes non-existent attrs to be added before they are set
-0.4-		
added a handful of classes which are automatically generated from pre-processed maya docs
better documentaion, added docstring to many functions derived from the mel help command
reorganized attribute limits: getMin, getMax, getSoftMin, getSoftMax, getRange, getSoftRange, and all their set* counterparts
-0.5.0-
added __eq__ and __ne__ methods for Dag class, which ensure that we compare the longnames of the node. (aka 'isSameObject' macro )
all node classes now inherit from unicode instead of str. this benefits our friends overseas and is generally more maya-compatible.
fixed bug which caused an infinite loop in Maya2008 when accessing attributes - related to str vs. unicode  (thanks John)
began merging pymel and maya docs to create a more thorough, hybrid solution.
added assignment operator for attributes: they can now be set with the equal sign (=) in addition to using the set() method
listReferences now returns a dictionary of { namespace : reference }
-0.5.1-
changed ui commands to work more like the creation commands, with command-class pairs
more documentation
improved example code
-0.6.0-
fixed setAttr force flag so that when using the force flag with pymel Node classes, the type is detected properly
fixed a bug in mel2py introduced in 0.5.0 when i changed from str to unicode
mel2py now supports block quotes which are terminated by the end of file instead of with '*/'
mel2py now supports on and off keywords
fixed a bug in mel2py when casting expressions to a different datatype  ex.  $var = string(5-2)
fixed mel2py's translation of commands like optionVar where the query flag expects a value other than a boolean
fixed mel2py's translation of reversed for loops
fixed a bug in isIterable/convertListArgs which was incorrectly detecting Node classes as arrays (thanks Olivier)
fixed a bug in Env class where maxTime property was incorrectly created as minTime
converted Env class and OptionVarDict class to singleton classes
fixed a bug with cascading nodes (transform->shape->history) when getting attributes that don't exist
fixed a bug in setAttr pertaining to stringArrays
fixed a bug in disconnectAttr
added and removed an iterator for multi-attributes to the Attribute class (this could confuse isIterable. need to think this over)
added Attribute.item() for getting the item number of a multi attribute
added Attribute.attrInfo()
modified listAttr() method to return Attribute classes
-0.7-
added wrapped commands: lsThruFilter, shadingNode, createNode
changed Dag.getParent to Dag.firstParent, and changed Dag.getParent2 to Dag.getParent
added Component class for verts, edges, faces, etc
added documentation for all commands
added Workspace class
added Subdiv class
added sourceFirst keyword arg for listConnections. when sourceFirst is true and connections is also true,
	the paired list of plugs is returned in (source,destination) order instead of (thisnode,othernode) order.
	this puts the pairs in the order that disconnectAttr and connectAttr expect.
fixed setAttr force flag to work for instances of builtin types as well, such as Path
added getSiblings to Dag class
fixed Attribute.exists() to not raise an error when the node does not exist, instead it returns False like the mel command 'attributeExists'
fixed a bug in Dag.namespaceList
added a levels keyword to Dag.stripNamespace
Maya Bug Fix: severe design oversight in all ui callback commands. 
	the callbacks were being passed u'true' and u'false' instead of python booleans. (why, autodesk? why?!)
added Transform.getBoundingBox()
fixed a bug in Transform: getShape() getChildren() and listRelatives() were erroring on maya 2008 
added chained-lookup to setattr
added Attribute.plugNode, same as Attribute.node
changed Attribute.plug to Attribute.plugAttr
changed behavior of shortName to behave like the mel script shortNameOf
changed Node.node to Node.nodeName
Maya Bug Fix: listRelatives: allDescendents and shapes flags did not work in combination
Fixed __unicode__ issue, removed underscore syntax
Added mayaInit for using pymel via an external interpreter
Maya Bug Fix: pointLight, directionalLight, ambientLight, spotLight did not return the correct name of created light 
Maya Bug Fix: instancer node was not returning name of created shape
added Camera.dolly, Camera.track, Camera.tumble, Camera.orbit
enhanced addAttr to allow python types to be passed to set -at type
			str 	--> string
			float 	--> double
			int		--> long
			bool	--> bool
			Vector	--> double3
added FileInfo class for accessing per-file data as a dictionary
Maya Bug Fix: fixed getCellCmd flag of scriptTable to work with python functions, previously only worked with mel callbacks
removed 'M' from Vector, Matrix, FileReference, and Path
changed sets command so that the operating set is always the first arg
added PyUI
fixed bug in createSurfaceShader
changed lsUI to return wrapped UI classes
added a class for every node type in the node hierarchy.
greatly improved documentation
added translate property to Transform class to overcome conflict with basestring.translate method
-0.7.5-
fixed bug in PyNode that was failing to cast Attributes to Nodes
fixed a bug in createSurfaceShader which was failing to return the correctly renamed shadingGroup
fixed a bug in mel2py when attempting to resolve path of a mel script that uses whitespace
fixed several minor bugs in mel2py and added many formatting improvements
renamed Reference to FileReference to avoid conflict with node.Reference
added listAnimatable
added mel2pyStr for converting a string representing mel code into python
improved mel2py formatting - now attempts to match lists and commands that span multiple lines
fixed a bug in Transform.zeroTransformPivots (thx koreno)
fixed a bug in Transform.centerPivots (thx koreno)
all commands, including custom commands, are now brought into the main namespace (excepting those we *wish* to filter)
fixed bugs in Attribute.getParent, Attribute.getChildren, Attribute.getSiblings, where results were not being returned as Attribute classes
fixed bug in Constraint.getWeight, Constraint.setWeight, and all constraint nodes that inherit from it.
added Attribute.lastPlugAttr, which will only return the last plug attribute of a compound attribute
Attribute commands which wrap attributeQuery now use lastPlugAttr for compatibility with compound attributes
added Attribute.array for retreiving the array (multi) attribute of the current element
-0.7.6-
fixed a bug introduced in 0.7.5 with set* class methods not being generated
added Attribute.getEnums and Attribute.setEnums
added DependNode.__new__ with 'create' flag to provide the option to create an object when creating an instance of the class
patched up pymelScrollFieldReporter for its first beta run (Fingers crosssed)
-0.7.7-
improved pymelScrollFieldReporter stability, particularly for windows and linux
added support for vectorArrays to addAttr, setAttr, getAttr
-0.7.8-
various bug fixes
-0.7.9-
fixed several bugs in Particle class
fixed bug in DagNode.isDisplaced()
Maya Bug Fix: setAttr did not work with type matrix. 
setAttr: to prevent mixup with double3, int3, ..., removed doubleArray and Int32Array from attribute types which are auto-detected when using force flag

 TODO: 
	Factory:
	- provide on option for creation command factory so that commands that always return a single object do not return a list

	mel2py and pymelScrollFieldReporter:
	- formatting: different spacing for negative numbers and subtraction: ( '-1', '2 - 5') 
	- flag info : 
		- share cache with pymel? must deal with commands whose synatx is altered (sets, move).
		- alternative to above: cache flag info of previously used commands
	- runtime commands
	
	To Debate:
	- filter out self from listHistory command?
	- remove deprecated commands from main namespace?: reference, equivalentTol, etc
	- remove commands that have been subsumed under a class? ex. dolly, track, orbit have all been added to Camera	
	- new feature for setAttr? : when sending a single value to a double3, et al, convert that to the appropriate list
		- ex.   setAttr( 'lambert1.color', 1 )  ---> setAttr( 'lambert1.color', [1,1,1] )
		- this is particularly useful for colors
	
	Todo:
	- create a feature-rich listReferences command, with flags for recursionDepth, regular expression match, return type ( list, dict, tree )  (API?)
	- create links between Reference (from node-hierarchy) and FileReference 
	- re-write primary list commands using API
	- add component classes for nurbs and subdiv
	- make Transforms delegate to component classes correctly (instead of returning Attribute class)
	- pymel preferences for breaking or maintaining backward compatibility:
		- longNames
		- twoDimensionalArrays (ex. ls(showType=1), fileInfo(q=1) )
		- namespaces
	- more module organization
	- Path
		- add sequence handling methods
		- rename methods using hungarian notation/camelCase?
	- Vector
		- add constants.  Red, White, Up, Down, etc
		- wrap MVector for speed
	- develop a way to add docs to selective objects based on cached info
	- explore the possibility of a mutable node class tied to the MObject
"""

__version__ = '0.8.0'

# not maya dependant
#import util
#print "imported utils"

# will check for the presence of an initilized Maya / launch it
from mayahook import mayaInit as _mayaInit
print "imported mayahook"
assert _mayaInit() 

#import tools
#print "imported tools"
#
import core.pmtypes.factories as factories
#print "imported factories"

import api
print "imported api"

from core import *
print "imported core"

#_module = __import__('core.other', globals(), locals(), [''])

#import factories
_module = __import__(__name__)    
#_factories.installCallbacks(_module)
#cmds.loadPlugin( addCallback=pluginLoadedCallback(_module) )
factories.installCallbacks(_module)

# some submodules do 'import pymel.core.pymel.mayahook.pmcmds as cmds' -
# this ensures that when the user does 'from pymel import *',
# cmds is always maya.cmds
import maya.cmds as cmds

def _test():
    import doctest
    doctest.testmod(verbose=True)

if __name__ == "__main__":
    _test()


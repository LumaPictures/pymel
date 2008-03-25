
# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com
 
"""

Pymel
=====

Pymel makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of mel commands into python commands. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. Pymel
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.

.. contents:: :backlinks: none

What's New in Version 0.7
=========================
If you are upgrading from a previous version of pymel, there are some big changes that you need to be aware of. 
This version introduces new modules and name-changes that add further organization and refinement, but at the cost
of backward compatibility with older code. Following the release of this version these sorts of changes should occur
much less frequently. 

Most of the changes are self-explanatory, except perhaps the removal of the underscore syntax for accessing attributes.
For more information on ways to access attributes from node classes, see the `Attribute` class.

Non-Backward Compatible Changes
-------------------------------
	- Removed underscore shorthand syntax for accessing attributes	
	- Renamed Classes:
		- MVec --> `Vector`
		- MMat --> `Matrix`
		- MPath --> `Path`
		- MReference --> `FileReference`
		- Node --> `DependNode`
		- Dag --> `DagNode`
		- Set --> `ObjectSet`
	- Changed and Renamed Functions:
		- renamed Attribute.plug to `Attribute.plugAttr`
		- renamed DagNode.node to `DagNode.nodeName`
		- changed `sets` command so that the operating set is always the first arg		
		- changed `DagNode.shortName` to behave like the mel script shortNameOf
		- changed `Attribute.exists` to not raise an error when the node does not exist, instead it returns False like the mel command 'attributeExists'
		
	- Module reorganization:
		- moved all function and classes which create or represent a node type to the `node` module
		- moved all functions and classes which create or represent a ui element to the `ui` module

Other Additions and Changes
---------------------------

	- Added wrapped commands: `lsThroughFilter`, `shadingNode`, `createNode`, `lsUI`	
	- Added documentation for all commands and classes
	
	- New Classes
		- Added an auto-generated class for every node type in the node hierarchy
		- Other New Classes:
			- `Workspace`
			- `Subdiv`
			- `FileInfo`
			- `Mesh.FaceArray`, `Mesh.EdgeArray`, `Mesh.VertexArray`, `Mesh.Face`, `Mesh.Edge`, `Mesh.Vertex`
				
	- Maya Bug Fixes
		- severe design oversight in many ui commands.  callbacks were being passed strings instead of the appropriate python types (int, float, bool).
		- listRelatives: allDescendents and shapes flags did not work in combination
		- pointLight, directionalLight, ambientLight, spotLight did not return the correct name of created light 
		- instancer node was not returning name of created shape
		- fixed scriptTable getCellCmd flag to work with python functions, previously only worked with mel callbacks

	- Pymel Bug Fixes
		- _BaseObj.__unicode__ was causing errors in maya 2008
		- Transform: getShape() getChildren() and listRelatives() were erroring on maya 2008 
		- `DagNode.__eq__` was not comparing DAG nodes properly
		- createSurfaceShader was not working properly
		- fixed a bug in DagNode.namespaceList
		- fixed setAttr force flag to work for subclasses of basestring, such as Path, _BaseObj, etc
				
	- Other Improvments
		- changed DagNode.getParent to `DagNode.firstParent`, and changed DagNode.getParent2 to `DagNode.getParent`			
		- added sourceFirst keyword arg for `listConnections`, `_BaseObj.connections`, `_BaseObj.inputs`, `_BaseObj.outputs`.
		- added `DagNode.getSiblings` 		
		- added a levels keyword to `DagNode.stripNamespace`		
		- added `Transform.getBoundingBox`	
		- added chained-lookup to `_BaseObj.__setattr__`
		- added `Attribute.plugNode`, same as Attribute.node
		- added mayaInit for using pymel via an external interpreter
		- added `Camera.dolly`, `Camera.track`, `Camera.tumble`, `Camera.orbit`
		- enhanced `addAttr`, `Attribute.add`, and `DependNode.addAttr` to allow python types to be passed to set -at type
		- added `Transform.translate` property to overcome conflict with basestring.translate method
		- added `Attribute.getEnums` and `Attribute.setEnums` and `Attribute.lastPlugAttr`
		- added `DependNode.__new__` with 'create' flag to provide the option to create an object when creating an instance of the class

Installation
============

Pymel Package
-------------

If on linux or osx, the simplest way to install pymel is to place the unzipped pymel folder in your scripts directory 

=========   =======================
Platform    Location
=========   =======================
mac         ~/Library/Preferences/Autodesk/maya/8.5/scripts
linux       ~/maya/maya/8.5/scripts
=========   =======================
	
Otherwise, it is a good idea to create a separate directory for your python scripts so that
they will be accessible from within Maya.  You can do this by setting the PYTHONPATH environment variable in Maya.env::  

	PYTHONPATH = /path/to/folder

Then place the pymel directory in your PYTHONPATH directory.

Next, to avoid having to import pymel every time you startup, you can create a userSetup.mel
file, place it in your scipts directory and add this line::

	python("from pymel import *");

Note, that if you have your PYTHONPATH set in a shell resource file, this value will override your Maya.env value.

Script Editor
-------------
Pymel includes a replacement for the script editor window that provides the option to translate all mel history into python. 
Currently this feature is beta and works only in Maya 8.5 SP1 and Maya 2008.

The script editor is comprised of two files located in the pymel/misc directory: scriptEditorPanel.mel and pymelScrollFieldReporter.py.  
Place the mel file into your scripts directory, and the python file into your Maya plugins directory. Open Maya, go-to 
B{Window --> Settings/Preferences --> Plug-in Manager} and load pymelScrollFieldReporter.  Be sure to also check 
"Auto Load" for this plugin. Next, open the Script Editor and go to B{History --> History Output --> Convert 
Mel to Python}. Now all output will be reported in python, regardless of whether the input is mel or python.

Problems with Maya 2008-x64 on Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Getting Started
===============

If you are a mel scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly
the section U{Using Python<http://download.autodesk.com/us/maya/2008help/General/Using_Python.html>}. This will help you to understand the differences in syntax between the two languages and how 
to translate between them. Another great way to learn how to translate mel into python is to install the new Script Editor (instructions
above). With it you can execute some mel code and watch the python output in the top pane. You can toggle back and forth by checking and
unchecking the "Convert Mel to Python" checkbox.

The Basics
----------

In its current incarnation, pymel is designed with a great deal of backward compatibility in mind, so that the maya.cmds
module and the pymel module can be used interchangably with the same code.  However, a closer look reveals pymel is actually
hiding a great deal of its power right under your nose.  Take the `ls` command for example.  `maya.cmds.ls` 
will return a list of strings.  These strings have a lot of built-in functionality that make them a million times more 
powerful than strings in mel:

	>>> import maya.cmds
	>>> cam = maya.cmds.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> cam = cam.replace( 'front', 'crazy' )  # an example string operation
	>>> print cam
	crazyShape
	>>> print cam[0] # indexable
	c
	>>> print cam[-5:] # slicable
	Shape
		
So, already you have object-oriented power at your fingertips. When using pymel, the `ls` command still returns a list of strings,
but these strings are on steroids: in addition to the built-in string methods ( a method is a function that belongs to a class ), 
pymel adds methods for operating on the type of object that the string represents:

	>>> import pymel
	>>> cam = pymel.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> cam.getFocalLength()
	# Result: 35.0 # 
	>>> print cam[-5:]  # still has the string functionality as well
	Shape

The same goes for other objects when using pymel.  When getting a triple attribute like translate or rotate, maya.cmds.getAttr
will return a list with three floats.  Pymel nodes, on the other hand, return a 3-element L{vector<Vector>} which inherits from the list class,
so that it has all the power of a list, and is backward compatible with any functions that expect to receive lists, but which
also has the ability to do vector and matrix math functions. 


Object-Oriented Design
======================

The pymel module reorganizes many of the most commonly used mel commands into a hierarchy of classes. This design allows 
you to write much more concise and readable python code. It also helps keep all of the commands organized, so that
functions are paired only with the types of objects that can use them.

All node classes inherit from the `DependNode` class. 
	
Understanding the `Attribute` class is essential to using pymel to its fullest extent.
	
In order to use the object-oriented design of pymel, you must ensure that the objects that you are working 
with are instances of pymel classes. To make this easier, this module contains wrapped version 
of the more common commands for creating and getting lists of objects. These modified commands cast their results to the appropriate 
class type. See `ls`, `listRelatives`, `listTransforms`, `selected`, and `listHistory`, for a few examples.  

Commands that list objects return pymel classes:

	>>> s = ls(type='transform')[0]
	>>> print type(s)
	<class 'pymel.node.Transform'> #
	
Most commands that create objects are wrapped as well (see below):

	>>> t = polySphere()[0]
	>>> print t, type(t)
	pSphere2, <class 'pymel.node.Transform'> #
	


Node Class Hierarchy
--------------------

Pymel uses data parsed from the maya documentation to reconstruct the maya node type hierarchy by creating
a class is for every node type in the tree.  The name of the class is the node type captitalized.  Wherever possible,
pymel will return objects as instances of these classes. This allows you to use builtin python functions to inspect
and compare your objects.  For example:

	>>> dl = directionalLight()
	>>> type(dl)
	<class 'pymel.node.DirectionalLight'>
	>>> isinstance( dl, DirectionalLight)
	True
	>>> isinstance( dl, Light)
	True
	>>> isinstance( dl, Shape)
	True
	>>> isinstance( dl, DagNode)
 	True

Most of these classes contain no methods of their own and exist only as place-holders in the hierarchy.
However, there are certain key classes which provide important methods to all their sub-classes. Currently, These are
`DependNode`, `DagNode`, `Transform`, `Constraint`, and `ObjectSet`.



Node Commands and their Class Counterparts
------------------------------------------

At the leaf level of the node hierarchy you will find the Node Command Classes, which are
node classes that have methods specific to their node type. As you are probably aware, Mel contains a number of commands
which are used to create, edit, and query object types in maya.  Typically, the names of these commands correspond
with the node type on which they operate, and hence, the pymel classes which they return. However, it should be noted
that there are a handful of exceptions to this rule.

Some examples of command-class pairs:

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

	>>> l = directionalLight()
	>>> print "The name is", l
	The name is directionalLightShape1
	>>> print "The maya type is", l.type()
	The maya type is directionalLight
	>>> print "The python type is", type(l)	
	The python type is <class 'pymel.node.DirectionalLight'>

Once you have an instance of a pymel class (usually handled automatically), you can use it to query and edit the
maya node it represents in an object-oriented way.

make the light red and get shadow samples, the old, procedural way
	>>> directionalLight( l, edit=1, rgb=[1,0,0] ) 
	>>> print directionalLight( l, query=1, shadowSamples=1 ) 
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
	# Result: 20.4079476169
	>>> cam.dolly( distance = -3 )
	>>> cam.track(left=10)
	>>> cam.addBookmark('new')


Using Existing Objects by Name
------------------------------

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing the object by name. Pymel
provides two ways of doing this. Both of them will automatically choose	the correct pymel class for your object.

The `PyNode` command:

	>>> PyNode( 'defaultRenderGlobals').startFrame.get()
	# Result: 1.0 #

The SCENE object:

	>>> SCENE.defaultRenderGlobals.startFrame.get()
	# Result: 1.0 #


Immutability
------------

All node classes are subclasses of python's built-in unicode string type, which allow them to be easily printed, passed to 
commands and used as keys in dictionaries. However, since strings are immutable, when calling 
commands like `rename`, the calling instance will point to an invalid object after the rename, so if you plan
to operate on this new instance, be sure to assign the result to a variable. For example:

	>>> orig = polySphere()[0]
	>>> print orig.exists()
	1
	>>> new = orig.rename('crazySphere')
	>>> print orig.exists(), new.exists()
	0 1
	
Delving Deeper: Chained Node Lookups
------------------------------------

Mel provides the versatility of operating on a shape node via its transform node.  for example, these two commands work
interchangably::

	camera -q -centerOfInterest persp
	camera -q -centerOfInterest perspShape

pymel achieves this effect by chaining function lookups.  If a called method does not exist on the Transform class, the 
request will be passed to appropriate class of the transform's shape node, if it exists.
The chaining goes one further for object primitives, such as spheres, cones, etc.  For example:
	
create a sphere and return its transform
	>>> trans = polySphere()[0]
	>>> print type(trans)
	<class 'pymel.node.Transform'>
	
get the transform's shape
	>>> shape = trans.getShape()
	>>> print type( shape )
	<class 'pymel.node.Mesh'>
	
get the shape's history
	>>> hist = shape.history()[1]
	>>> type( hist )
	<class 'pymel.node.PolySphere'>
	
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

Mel Scripts
===========
Calling mel scripts through maya.mel.eval is a nuisances because it requires so much string formatting on 
the programmer's part.  `pymel.mel` handles all of that for you so you can use your mel scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. see
`pymel.core.Mel` for more information.


Module Namespaces
=================

Another problem with maya.cmds is that importing it into the root namespace (e.g. ``from maya.cmds import *``)
is dangerous because it will override several of python's more important built-in methods. pymel is designed
to be safe to import into the root namespace so that scripts can be written much more concisely. 

All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( file, filter, eval,
help, and quit). The conflicting commands can be found in the pymel.cmds namespace, along with all of the unaltered
maya commands.  

See `pymel.io` for more information on how the file command is implemented in pymel.

Even though pymel has a handful of modules, all but `pymel.runtime` are imported directly into the main namespace. The sub-modules are provided
for two reasons: 1) to improve the clarity of the documentation, and 2) so that, if desired, the user can edit the import commands
in __init__.py to customize which modules are directly imported and which should remain in their own namespace 
for organizational reasons.

Design Philosophy
=================

When approaching the reorganization of the existing commands provided by maya.cmds, pymel follows these practical guidelines:

	- a value returned by a get* function or query flag should be accepted as a valid argument by the corresponding set* function or edit flag
	- a function which returns a list should return an empty list (not None) if it finds no matches ( ex. ls, listRelatives )
	- a function which always returns a single item should not return that item in a list or tuple ( ex. spaceLocator )
	- wherever possible, pymel/python objects should be returned
	- a function which provides a mapping mechanism should have a dictionary-like pymel counterpart ( ex. fileInfo, optionVar )
	- a function which returns a list of pairs should be a 2D array, or possibly a dictionary ( ex. ls( showType=1 )  )
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

__version__ = '0.7.9'

#check for the presence of an initilized Maya
import util
assert util.mayaInit() 

#import api
#from core.node import *
#from core.core import *
from core.general import *
from core.ctx import *
from core.system import *
from core.windows import *
from core.animation import *
from core.effects import *
from core.modeling import *
from core.rendering import *
import core.runtime

	
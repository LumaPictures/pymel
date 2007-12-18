

# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com
 
"""

Pymel
=====

Pymel makes python scripting with Maya work the way it should. Maya's command module is a direct
translation of mel commands into python commands. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particulary, a flexible, object-oriented design. Pymel
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.


Getting Started
===============

If you are a mel scripter but have not used python in maya yet, you should start with the Maya docs on the subject, particularly
the section 'Using Python'. This will help you to understand the differences in syntax between the two languages and how 
to translate between them.

The Basics
----------

In its current incarnation, pymel is designed with a great deal of backward compatibility in mind, so that the maya.cmds
module and the pymel module can be used interchangably with the same code.  However, a closer look reveals pymel is actually
hiding a great deal of its power right under your nose.  Take the L{ls} command for example.  L{maya.cmds.ls} 
will return a list of strings.  These strings have a lot of built-in functionality that make them a million times more 
powerful than strings in mel:

	>>> import maya.cmds
	>>> cam = maya.cmds.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> cam.replace( 'front', 'crazy' )  # an example string operation
	# Result: crazyShape # 
		
So, already you have object-oriented power at your fingertips. When using pymel, the L{ls} command still returns a list of strings,
but these strings are on steroids: in addition to the built-in string methods ( a method is a function that belongs to a class ), 
pymel adds methods for operating on the type of object that the string represents:

	>>> import pymel
	>>> cam = pymel.ls( type='camera')[0]
	>>> print cam
	frontShape
	>>> cam.getFocalLength()
	# Result: 35.0 # 
	>>> cam.replace( 'front', 'crazy' )  # still has the string functionality as well
	# Result: monkeyShape #

The same goes for other objects when using pymel.  When getting a triple attribute like translate or rotate, maya.cmds.getAttr
will return a list with three floats.  Pymel nodes, on the other hand, return a 3-element L{vector<Vector>} which inherits from the list class,
so that it has all the power of a list, and is backward compatible with any functions that expect to receive lists, but which
also has the ability to do vector and matrix math functions. 


Object-Oriented Design
======================

The pymel module reorganizes many of the most commonly used mel commands into a hierarchy of classes. This design allows 
you to write much more concise and readable python code. It also helps keep all of the commands organized, so that
functions are paired only with the types of objects that can use them.

All node classes inherit from the L{Node} class. 
	
Understanding the L{Attribute} class is essential to using pymel to its fullest extent.
	
Using Node Classes
------------------

	In order to use the object-oriented design of pymel, you must ensure that the objects that you are working 
	with are instances of pymel classes. To make this easier, this module contains wrapped version 
	of the more common commands for creating and getting lists of objects. These modified commands cast their results to the appropriate 
	class type. See L{ls}, L{listRelatives}, L{listTransforms}, L{selected}, and L{listHistory}.  
	
	Commands that list objects return pymel classes:
	
		>>> s = ls(type='transform')[0]
		>>> print type(t)
		<class 'pymel.core.Transform'> #
		
	Most commands that create objects are wrapped as well (see below):
	
		>>> t = polySphere()[0]
		>>> print t, type(t)
		pSphere2, <class 'pymel.core.Transform'> #
		
	In many cases, you won't be creating the object directly in your code, but will want to gain access to the object by name. Pymel
	provides two new ways of doing this.
		
	Using Objects by Name: The PyNode Command
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
	The L{PyNode} command will automatically choose	the correct pymel class for your object.
	
		>>> s = PyNode('perspShape') # convert to a pymel class
		>>> print s, type(s)
		perspShape, <class 'pymel.Camera'> # 



	Using Objects by Name: The SCENE object
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		
	The 'SCENE' object provides the same functionality as the PyNode command, but with a slightly different syntax.

	with PyNode:
		>>> PyNode( 'defaultRenderGlobals').startFrame.get()
		# Result: 1.0 #

	with SCENE:
		>>> SCENE.defaultRenderGlobals.startFrame.get()
		# Result: 1.0 #



Object Commands and their Classes
---------------------------------

Mel contains a number of commands which are used to create, edit, and query specific object types in maya.  
Typically, the names of these commands correspond with the node type on which they operate.  some examples of these
commands are aimConstraint, camera, directionalLight, and polySphere ( see commandsCreation in the pymel directory
for a complete list). Pymel creates a class for each of these commands -- the class name is simply the command capitalized.
Once nodes have been cast to their appropriate type (usually handled automatically) the commands operations can
be performed in an object oriented way.

this example demonstrates some basic principles. note the relationship between the name of the object
created, its node type, and its class type

	>>> l = directionalLight()
	>>> # print the name of the object, its maya object type, and the class type
	>>> print l, l.type(), type(l)	
	directionalLightShape1 directionalLight <class 'pymel.DirectionalLight'>

make the light red and get shadow samples, the old school way
	>>> directionalLight( l, edit=1, rgb=[1,0,0] ) 
	>>> directionalLight( l, query=1, shadowSamples=1 ) 
	1	
	
now, the pymel way
	>>> l.setRgb( [1,0,0] )
	>>> print l.getShadowSamples()   
	1


Some fun with cameras

	>>> camTrans, cam = camera()
	>>> cam.setFocalLength(100)
	>>> cam.getFov()
	# Result: 20.4079476169
	>>> cam.dolly( distance = -3 )
	>>> cam.track(left=10)
	>>> cam.addBookmark('new')


Immutability
------------

All node classes are subclasses of python's built-in unicode string type, which allow them to be easily printed, passed to 
commands and used as keys in dictionaries. However, since strings are immutable, when calling 
commands like L{rename}, the calling instance will point to an invalid object after the rename, so if you plan
to operate on this new instance, be sure to assign the result to a variable. For example:

	>>> orig = polySphere()[0]
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
	<class 'pymel.core.Transform'>
	
get the transform's shape
	>>> shape = trans.getShape()
	>>> print type( shape )
	<class 'pymel.core.Poly'>
	
get the shape's history
	>>> hist = shape.history()[1]
	>>> type( hist )
	<class 'pymel.PolySphere'>
	
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
the programmer's part.  L{pymel.mel} handles all of that for you so you can use your mel scripts as if they 
were python functions. This includes automatically formatting all iterable types into maya arrays. see
L{pymel.core.Mel} for more information.


Module Namespaces
=================

Another problem with maya.cmds is that importing it into the root namespace (e.g. 'from maya.cmds import *')
is dangerous because it will override several of python's more important built-in methods. pymel is designed
to be safe to import into the root namespace so that scripts can be written much more concisely. 

All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( file, filter, eval,
help, and quit). The conflicting commands can be found in the pymel.cmds namespace, along with all of the unaltered
maya commands.  

Also, see L{pymel.io} for more information on how the file command is implemented in pymel.

Even though pymel has a handful of modules, they are all imported directly into the main namespace, except for the ctx module.
In the future, I will try to establish a way for the user to easily customize which modules are directly imported and
which should remain in their own namespace for organizational reasons.


Setup
=====

if you have not done so already, it is a good idea to setup a directory for your published python scripts so that
they will be accessible from within maya.  you do this by setting the PYTHONPATH environment variable in Maya.env.  
if you want to use your current maya scripts directory simply add this to your Maya.env::

	PYTHONPATH = $MAYA_SCRIPT_PATH

then place the pymel directory in your PYTHONPATH directory.

next, to avoid having to import pymel every time you startup, if you have not done so already, you can create a userSetup.mel
file, place it in your scipts directory and add this line::

	python("from pymel import *");

Note, that if you have your PYTHONPATH set in a shell resource file, this value will override your Maya.env value.
 
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
added commands lsThruFilter, shadingNode
fixed createNode so that it does not generate a class since it has no edit flags
changed Dag.getParent to Dag.firstParent, and changed Dag.getParent2 to Dag.getParent
added Component class for verts, edges, faces, etc
reorganized the help/documentation functions into their own module
renamed helpers module to util to avoid confusion with the new helpDoc module
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
added cascading to setattr
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
Maya Bug Fix: fixed getCellCmd to work with python functions, previously only worked with mel callbacks
removed 'M' from Vector, Matrix, Reference, and Path

 TODO: 
	Factory:
	- provide on option for creation command factory so that commands that always return a single object do not return a list
	- __init__ func for factory classes.  
		- provide an alternate method of creation, which creates the named object if it does not exist.
		- always returns a single object, not a list

	To Debate:
	- filter out self from listHistory command?
	- remove deprecated commands from main namespace?: reference, equivalentTol, etc
	- new feature for setAttr? : when sending a single value to a double3, et al, convert that to the appropriate list
		- ex.   setAttr( 'lambert1.color', 1 )  ---> setAttr( 'lambert1.color', [1,1,1] )
		- this is particularly useful for colors
	
	
	For Next Release:
	- sort out listReferences, getReferences
	- add component classes for nurbs and subdiv
	- make Transforms delegate to component classes correctly (instead of returning Attribute class)
	- correctly separate examples flag info when parsing docs
	- format docstrings to be epydoc friendly
	
	For Future Release:
	- pymel preferences for breaking or maintaining backward compatibility:
		- longNames
		- twoDimensionalArrays (ex. ls(showType=1), fileInfo(q=1) )
	- add sequence handling methods to Path
	- create Vector constants.  Red, White, Up, Down, etc
	- develop a way to add docs to selective objects based on cached info
"""

__version__ = 0.7

#check for the presence of an initilized Maya
import util
assert util.mayaInit() 

from core import *

#import io
from io import *

#import scene
#from scene import *

#import env
from env import *

#import ui
# if importing into main namespace, be sure to change the __module__ property in ui.py

from ui import *
#import ui

#from trees import *

# Olivier : Can have trouble loading a module by its absolute path since we are in pymel ?
try :
	import factories
	factories.createPymelObjects()
except :
	import pymel.factories
#pymel.factories.createClasses('commandsCreation', 'pymel', usePyNode=True)
#pymel.factories.createClasses('commandsUI', 'pymel', usePyNode=False)
#pymel.factories.createClasses('commandsCtx', 'pymel.ctx', usePyNode=False)
	pymel.factories.createPymelObjects()



	
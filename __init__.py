
# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com
 
"""
*******************************
          Pymel
*******************************

Pymel makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of mel commands into python commands. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. Pymel
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.


.. contents:: :backlinks: none

=======================================
What's New in Version 0.8
=======================================
---------------------------------------    
Licensing Change
---------------------------------------
pymel is now offered under the New BSD license.

---------------------------------------
Non-Backward Compatible Changes
---------------------------------------
    - Attribute disconnection operator has changed from ``<>`` to ``//``
        ``<>`` operator corresponds to __ne__ method, whose other operator is '!=' and we need that to mean 'not equal'.
    - Node classes no longer inherit from unicode: see `PyNodes Are Not Strings`_
        This allows node classes to reflect name changes such as parenting or renaming, a key aspect of the API integration
    - Instantiation of non-existent PyNode objects now results in an exception: see `Non-Existent Objects`_
        Also a side-effect of the API integration.  Prevents mistakes and produces cleaner code with use of new exception classes
    - _BaseObj has been replaced with `PyNode` class, which operates like the old PyNode function
        Provides more intuitive relationship between PyNode() and node classes
    - removed method-chaining between shapes and their history
        chaining transforms to shapes 
     
---------------------------------------    
Other Additions and Changes
---------------------------------------
    - Module reorganization
        .. packagetree:: pymel

    - API Hybridization: the Node hierarchy now automatically derives many of its methods from API MFn classes
 
    - New Classes
        - The `MelGlobals` class adds dictionary-like access to mel global variables
        - The `Version` class simplifies comparison of Maya versions
        
    - General Improvements
        - Commands and classes created by plugins are now added to pymel namespace on load and removed on unload
        - Name-independent dictionary hashing for nodes in maya 2009: see section `Using PyNodes as Keys in Dictionaries`_
        - Added `DagNode.addChild` as well an addChild operator ( | ) for DAG objects: `DagNode.__or__`
        - The `Mel` class now prints mel errors and line numbers when an exception is raised
        - The `Mel` class returns pymel Vectors and Matrices
        - `DependNode` subclasses can be used to create new nodes

=======================================
Installation
=======================================

---------------------------------------
Pymel Package
---------------------------------------

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

---------------------------------------
Script Editor
---------------------------------------
Pymel includes a replacement for the script editor window that provides the option to translate all mel history into python. 
Currently this feature is beta and works only in versions beginning with Maya 8.5 SP1.

The script editor is comprised of two files located in the pymel/tools/scriptEditor directory: scriptEditorPanel.mel and pymelScrollFieldReporter.py.  
Place the mel file into your scripts directory, and the python file into your Maya plugins directory. Open Maya, go-to 
**Window --> Settings/Preferences --> Plug-in Manager** and load pymelScrollFieldReporter.  Be sure to also check 
"Auto Load" for this plugin. Next, open the Script Editor and go to **History --> History Output --> Convert 
Mel to Python**. Now all output will be reported in python, regardless of whether the input is mel or python.

---------------------------------------
ipymel
---------------------------------------
ipymel is an extension of the ultra-customizable IPython interpreter, which enables it to easily work with mayapy and pymel.  It adds tab completion of maya depend nodes,
dag nodes, and attributes, as well as automatic import of pymel at startup.  Many more features to come. 

OSX and Linux
=============

    1. Install IPython.  I recommend downloading the tarball, not the egg file. uzip the tar.gz and put the subdirectory named IPython somewhere on your PYTHONPATH
    2. Ensure that the maya bin directory is on your system PATH
    3. Open a terminal, cd into pymel/tools and run::
        chmod 777 ipymel
    4. now run::
        ./ipymel
    
It's easiest if you either add the pymel/tools directory to your system PATH variable or if you copy ipymel to somewhere on your PATH like /usr/local/bin. Once
it is on your you can simply open a shell and type ``ipymel`` to launch.

Windows
=======

coming soon...


---------------------------------------
Problems on Linux
---------------------------------------

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

=======================================
    Design Philosophy
=======================================

---------------------------------------
Procedural (maya.cmds)
---------------------------------------

When approaching the reorganization of the existing commands provided by maya.cmds, pymel follows these practical guidelines:

    - a value returned by a query flag should be accepted as a valid argument by the corresponding edit flag
    - a function which returns a list should return an empty list (not None) if it finds no matches 
        ( ex. `ls`, `listRelatives` )
    - a function which always returns a single item should not return that item in a list or tuple 
        ( ex. `spaceLocator` )
    - wherever possible, pymel/python objects should be returned
    - a function which provides a mapping mechanism should have a dictionary-like pymel counterpart 
        ( ex. `fileInfo`, `optionVar` )
    - a function which returns a list of pairs should be a 2D array, or possibly a dictionary 
        ( ex. ls( showType=1 ), listConnections(connections=1) )
    - the arguments provided by a ui callback should be of the appropriate type 
        ( as a test, it should be capable of being used to set the value of the control )
    - if a function's purpose is to query and edit maya nodes, that node should be passed as an argument, not a keyword
        ( ex. `sets` )

---------------------------------------
Object-Oriented
---------------------------------------

In constructing the PyNode classes, pymel follows these design rules:

    - node classes should never use properties -- all behavior should be placed in methods to differentiate them from shorthand attribute syntax
        ( ex. foo.bar retrieves an Attribute class, foo.bar() executes a function )
    - node classes are named after the nodes they control, not the mel commands that they proxy  
        ( ex. Locator vs. spaceLactor )
    - a value returned by a get* function should be accepted as a valid argument by the corresponding set* function


=======================================
    Background
=======================================

.. packagetree:: pymel
    :dir: down
    :style: tree
    
.. digraph:: title
     a -> b -> c
     b -> d
        
MEL is a procedural language, meaning it provides the ability to encapsulate code
into reusable "procedures" ( aka "functions" ).  (This is probably old news to you, but
bear with me, there's a midly entertaining analogy coming up ). The term "procedural programming" is 
mentioned primarily in the context of disguishing something from the newer, object-oriented paradigm. If you have used MEL
extensively you know you can get pretty far with procedural programming alone,
but once you've gotten comfortable with python's object-oriented design, you will never go back. 

Object-oriented programming adds another level of organization by creating logical groupings of functions
which are accessed from a common "object".  A quick perusal of the hundreds of MEL commands in the MAYA documentation
will give you an idea why these groupings are a good idea.  MEL is like a toolchest, a wardrobe, and
a kitchen set all dumped into a bathtub -- everything in there is useful, but you've really got to know what
you're looking for to get anything done.  Through the use of classes and modules, python makes sure that
everything is in its right place.

So now that python is availabe in Maya all of our problems are solved, right?  Not quite.  The root of the problem
is that maya.cmds is just a python wrap of the same underlying MEL codebase we've had all along.
And since it was never intended to be python in the first place, the syntax that results from this layering of Python over MEL
tends to be awkward, especially to those used to python idioms. 

The C++ API also has a python wrap but it too suffers from awkward and unpythonic idioms, stemming from its C++ heritage.  Unlike MEL, Maya's C++ API 
benefits from the fact that it was object-oriented to begin with, but from a scripters' standpoint, it's tortuously verbose and cryptic.
Certainly nothing you would want to write an entire pipeline with.

Enter Pymel.  The reasons for pymel's existence are threefold:

    1. to fix bugs in maya.cmds
    2. to modify the behavior of maya.cmds to improve workflow and make it more pythonic ( like returning an empty list instead of None )
    3. to provide a complete object-oriented design for working with nodes, attributes, and other maya structures

If you're still not sure you're ready to make the jump to object-oriented programming, the first two points alone
are reason enough to use pymel, but the object-oriented design is where pymel really shines.  Pymel 
strikes a balance between the complicated yet powerful API, and straightforward but unruly MEL. 


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
Getting Started
---------------------------------------

To get started we need to import pymel.

    >>> from pymel import *
    
This brings everything in pymel into the main namespace, meaning that you won't have to prefix the maya commands with the
module name.  For more information on the pros and cons of this see `Module Namespaces`_.

---------------------------------------
The Basics
---------------------------------------

Next, we need some nodes to work with.  In general, we can get nodes in 3 ways: list them
based on some critera, create them, or just get them by name.  Let's start by listing the cameras in the scene.  We do this in the 
same way that we would with maya.cmds.

    >>> ls(type='camera')
    [Camera('frontShape'), Camera('perspShape'), Camera('sideShape'), Camera('topShape')]

Notice that the names of the returned nodes are preceded by the node type, `Camera`.  When using pymel, commands don't return strings
as they do in MEL and maya.cmds.  Instead they return `PyNode` classes which correspond to the type of object or UI.
These python objects are like strings on steroids: in addition to methods found on the builtin string ( a method is a function bound to an object. ex. 'bar' is the
method in 'foo.bar' ), 
pymel adds methods for operating on the specific type of maya object that the string represents. 

Let's use one of these camera objects to get some information:

    >>> # assign the first camera to a variable
    >>> cam = ls(type='camera')[0]
    >>> cam
    Camera('frontShape')
    >>> # get some information
    >>> cam.getAspectRatio()
    1.5
    >>> cam.getFocalLength()
    35.0


Now let's create a node:

    >>> objs = polyPlane()
    >>> objs
    [Transform('pPlane1'), PolyPlane('polyPlane1')]

You can see that, like the `ls` command, the `polyPlane` command also returns `PyNode` classes.  As in MEL, it returns a list: the
first object is the tranform of the plane, and the second is the construction history (if construction history is turned on). Now
let's get the shape of the transform:

    >>> #assign the transform to a variable
    >>> plane = objs[0]
    >>> shape = plane.getShape()
    >>> shape
    Mesh('pPlaneShape1')
    
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
    MeshVertex('pPlaneShape1.vtx[0]')

On the last line you see that vertices have their own class as well, `MeshVertex`.

---------------------------------------
Getting Help
---------------------------------------

If you are ever unsure of what method to use, just use the builtin python help command on the node class (the capitalized node type):

    >>> help(Camera)   #doctest: SKIP

You can do the same thing for any command in pymel as well.

    >>> help(ls)   #doctest: SKIP


---------------------------------------
Attributes
---------------------------------------

I think it's time we learned how to set some attributes.  Let's go back and take a look at our plane's transform and access an `Attribute`
object.  Just like nodes, attributes have their own class with methods that encompass the dozens of MEL commands for
operating on them.

    >>> plane.translateX
    Attribute('pPlane1.translateX')

To get and set attributes:

    >>> plane.translateX.get()
    0.0
    >>> plane.translateX.set(10.0)
    
To query and edit properties of attributes:

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
    [ShadingEngine('initialShadingGroup'), PolyPlane('polyPlane1')]
    >>> # 'inputs' is a shorcut to connections(source=True)
    >>> shape.inputs()
    [PolyPlane('polyPlane1')]
    >>> # 'outputs' is a shorcut to connections(source=False)
    >>> shape.outputs()
    [ShadingEngine('initialShadingGroup')]

Notice that when we enable the ``plugs`` flag that the result becomes an `Attribute`

    >>> shape.inputs(plugs=1)
    [Attribute('polyPlane1.output')]

Here's another handy feature of python: it supports 2D arrays, meaning you can put lists inside lists.  Pymel takes advantage of
that in many situations, including when we use the ``connections`` flag, which causes `listConnections` to list source-destination
pairs.

    >>> for source, destination in shape.connections(c=1, p=1):
    ...     print source, destination
    ... 
    pPlaneShape1.instObjGroups[0] initialShadingGroup.dagSetMembers[0]
    pPlaneShape1.inMesh polyPlane1.output

---------------------------------------
Using Existing Objects by Name
---------------------------------------

In many cases, you won't be creating objects directly in your code, but will want to gain access to an existing object by name. Pymel
provides two ways of doing this. Both of them will automatically choose the correct pymel class for your object.

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


All of the MEL functions in maya.cmds exist in pymel, with a few exceptions ( see `Module Namespaces`_ ).  The purpose
of these functions tend to fall into one or two of the following categories:

    1. create objects and UI's : remains mostly procedural
    2. list objects and UI's :  object-oriented, except for general listing commands like `ls`
    3. query and edit objects and UI's :  object-oriented, excepot for commands that operate on many nodes, like `select` and `delete`

Use these guidelines as you retrain yourself to use object methods instead of the usual procedural commands.




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
with are instances of pymel classes. To make this easier, pymel contains wrapped version 
of the more common commands for creating and getting lists of objects. These modified commands cast their results to the appropriate 
`PyNode` class type. See `ls`, `listRelatives`, `listTransforms`, `selected`, and `listHistory`, for a few examples.  

Commands that list objects return pymel classes:
    >>> s = ls(type='transform')[0]
    >>> print type(s)
    <class 'pymel.core.general.Transform'>
    
Commands that create objects are wrapped as well:
    >>> t = polySphere()[0]
    >>> print t, type(t)
    pSphere1 <class 'pymel.core.general.Transform'>
    
---------------------------------------
API Underpinnings
---------------------------------------
In MEL, the best representation we have have of a maya node or attribute is its name.  But with the API we can do better!  
When creating an instance of a `PyNode` class, pymel determines the underlying API object behind the scenes.
With this in hand, it can operate on the object itself, not just the string representing the object.

So, what does this mean to you?  Well, let's take a common example: testing if two nodes or attributes are the
same. In MEL, to accomplish this the typical solution is to perform a string comparison 
of two object names, but there are many ways that this seemingly simple operation can go wrong. For instance, forgetting to compare the
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
        >>> # check out our objects
        >>> sphere1                            # the original
        Transform('group1|mySphere')
        >>> sphere2                            # the instance
        Transform('group2|mySphere')
        >>> # do some tests
        >>> # they aren't the same dag objects
        >>> sphere1 == sphere2              
        False
        >>> # they are instances of each other
        >>> sphere1.isInstanceOf( sphere2 )    
        True
        >>> sphere1.getAllInstances()
        [Transform('group1|mySphere'), Transform('group2|mySphere')]
        >>> 
        >>> # long and short names retrieve the same attribute
        >>> sphere1.t == sphere1.translate    
        True
        >>> sphere1.tx == sphere1.translate.translateX
        True
        >>> # the same attrs on different nodes/instances are still the same 
        >>> sphere1.t == sphere2.t    
        True
        
---------------------------------------
PyNodes Are Not Strings
---------------------------------------

In previous versions of pymel, the node classes inherited from the builtin unicode string class.  With the introduction of the new API
underpinnings, the node classes inherit from a special `ProxyUnicode` class, which has the functionality of a string object, but
removes the immutability restriction ( see the next section `Mutability And You`_ ).  It is important to keep in mind that although
PyNodes *behave* like strings, they are no longer actual strings. Functions which explicity require a string, and which worked 
with PyNodes in previous versions of pymel, might raise an error with version 0.8 and later. For example:

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

Also be aware that string operations with PyNodes return strings not new PyNodes:

    >>> cam = PyNode('frontShape')
    >>> new = cam.replace( 'front', 'monkey' )
    >>> print new, type(new), type(cam)
    monkeyShape <type 'unicode'> <class 'pymel.core.general.Camera'>
    
---------------------------------------
Mutability and You
---------------------------------------

One change that has come about due to the new API-based approach is node name mutability. You might have noticed
when working with strings in python that they cannot be changed "in place". In other words, all string operations return a new string. This is
because strings are immutable, and cannot be changed.

By inheriting from a mutable `ProxyUnicode` class instead of an immutable string, we are now able to provide a design which more accurately reflects 
how nodes work in maya --  when a node's name is changed it is still the same object with the same properties --  the name
is simply a label or handle. In practice, this
means that each time the name of the node is required -- such as printing, slicing, splitting, etc -- the object's current name
is queried from the underlying API object. This ensures renames performed via mel or the UI will always be reflected 
in the name returned by your PyNode class.

Renaming
========

In versions of pymel previous to 0.8, the node classes inherited from python's built-in unicode
string type, which, due to its immutability, could cause unintuitive results with commands like rename.
The new behavior creates a more intuitve result.

New Behavior:
    >>> orig = polyCube(name='myCube')[0]
    >>> print orig                    # print out the starting name
    myCube
    >>> orig.rename('crazyCube')    # rename it (the new name is returned)
    Transform('crazyCube')
    >>> print orig                    # the variable 'orig' reflects the name change
    crazyCube
    
As you can see, you no longer need to assign the result of a rename to a variable, although, for backward
compatibility's sake, we've ensured that you still can.

Using PyNodes as Keys in Dictionaries
=====================================

Maya 2008 and Earlier
---------------------

There is one caveat to the mutability of node names: it can cause problems when using a pymel node as a key in a dictionary prior to 2009.
The reason is that the hash ( a hash is an integer value which is used to speed up dictionary access ) generated by a pymel node
is based on the node's name, which is subject to change.  

    >>> orig = polySphere()[0]         #doctest: +SKIP
    >>> d = { orig :  True }           #doctest: +SKIP
    >>> orig.rename('crazySphere')     #doctest: +SKIP
    Transform('crazySphere')
    >>> print d[orig]                  #doctest: +SKIP
    Traceback (most recent call last):
        ...
    KeyError: Transform('crazySphere')
    

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
    >>> c = polyCube()[0]
    >>> store()  # save the state of the current scene
    >>>
    >>> # make some changes
    >>> s.rename('monkey')
    Transform('monkey')
    >>> delete(c)
    >>> polyTorus()
    [Transform('pTorus1'), PolyTorus('polyTorus1')]
    >>>
    >>> diff() # print out what's changed since we ran 'store()'
    renamed: nurbsSphere1 ---> monkey
    renamed: nurbsSphereShape1 ---> monkeyShape
    new: polyTorus1
    new: pTorus1
    new: pTorusShape1
    deleted: pCube1
    deleted: polyCube1
    deleted: pCubeShape1



---------------------------------------
Enumerators
---------------------------------------

---------------------------------------
Node Class Hierarchy
---------------------------------------


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


MEL Node Commands and their PyNode Counterparts
===============================================

As you are probably aware, MEL contains a number of commands
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
created, its node type, and its class type. Also notice that instead of creating new objects using
maya.cmds functions ( ex. spotlight ), the class ( ex. Spotlight ) can also be used :

    >>> l = SpotLight()
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

For those familiar with MEL, you can probably already tell that the DirectionalLight class can be understood as an 
object-oriented reorganization of the directionalLight command, where you 'get' queries and you 'set' edits.  

Some classes have functionality that goes beyond their command counterpart. The `Camera` class,
for instance, also contains the abilities of the `track`, `orbit`, `dolly`, and `cameraView` commands:

    >>> cam = Camera(name='newCam')
    >>> cam.setFocalLength(100)
    >>> cam.getHorizontalFieldOfView()
    20.407947443463367
    >>> cam.dolly( distance = -3 )
    >>> cam.track(left=10)
    >>> cam.addBookmark('new')


API Classes and their PyNode Counterparts
=========================================

---------------------------------------
Chained Function and Attribute Lookups
---------------------------------------

Mel provides the versatility of operating on a shape node via its transform node.  For example, these two commands work
interchangably::

    camera -q -centerOfInterest persp
    camera -q -centerOfInterest perspShape


pymel achieves this effect by chaining function lookups.  If a called method does not exist on the Transform class, the 
request will be passed to appropriate class of the transform's shape node, if it exists.

    >>> # get the persp camera as a PyNode
    >>> trans = PyNode('persp')
    >>> print type(trans)
    <class 'pymel.core.general.Transform'>
    >>> # get the transform's shape, aka the camera node
    >>> cam = trans.getShape()
    >>> print cam
    perspShape
    >>> print type( cam )
    <class 'pymel.core.general.Camera'>
    >>> trans.getCenterOfInterest()
    44.82186966202994
    >>> cam.getCenterOfInterest()
    44.82186966202994

=======================================
Non-Existent Objects
=======================================

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
    >>> x = polySphere(name='earth')[0]
    >>> x.attr('myAttr')
    Traceback (most recent call last):
        ...
    MayaAttributeError: Maya Attribute does not exist: 'earth.myAttr'
    
Shorthand notation:
    >>> x = polySphere(name='moon')[0]
    >>> x.myAttr
    Traceback (most recent call last):
        ...
    AttributeError: Transform('moon') has no attribute or method named 'myAttr'
    
---------------------------------------
Testing Node Existence
---------------------------------------

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
    
---------------------------------------
Testing Attribute Existence
---------------------------------------

No longer supported:
    >>> if PyNode( 'persp.spangle' ).exists(): #doctest: +SKIP
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
    
No longer supported:
    >>> x = PyNode('persp') 
    >>> if x.spangle.exists(): #doctest: +SKIP
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

Still supported:
    >>> if objExists( 'persp.spangle' ):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
            
New construct:    
    >>> x = PyNode('persp') 
    >>> if x.hasAttr('spangle'):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

New construct:
    >>> try:
    ...     PyNode( 'persp.spangle' )
    ...     print "Attribute Exists"
    ... except MayaAttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

New construct:
    >>> x = PyNode('persp') 
    >>> try:
    ...     x.spangle
    ...     print "Attribute Exists"
    ... except AttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

--------------------------------------------
Manipulating Names of Non-Existent Objects
--------------------------------------------

One advantage of the old way of dealing with non-existent objects was that you could use the name parsing methods of the PyNode
classes to manipulate the object's name until you found what you were looking for.  To allow for this, we've added
several classes which operate on non-existent nodes, except they contain only methods for string parsing and existence testing.
These nodes can be found in the `other` module and are named `NameParser`, `AttributeName`, `DependNodeName`, and `DagNodeName`.

Also, there is a new fully-featured maya name parsing module, `util.nameparser`, which is based on Python Lex Yacc.  It parses maya
object names into hierarchical name tokens, accessible via cascading class attributes.


=======================================
    Module Namespaces
=======================================

Another problem with maya.cmds is that importing it into the root namespace (e.g. ``from maya.cmds import *``)
is dangerous because it will override several of python's more important built-in methods. pymel is designed
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
    
All the functions in maya.cmds are in the pymel namespace, except the conflicting ones ( file, filter, eval,
help, and quit). The conflicting commands can be found in the pymel.cmds namespace, along with all of the unaltered
maya commands.  

See `pymel.core.system` for more information on how the file command is implemented in pymel.

Even though pymel has a handful of modules, all but `pymel.runtime` are imported directly into the main namespace. The sub-modules are provided
primarily to improve the clarity of the documentation.

=======================================
    Standalone Maya Python
=======================================

To use maya functions in an external python interpreter, maya provides a handy executable called mayapy.  You can find it in the maya bin 
directory.  Pymel has some more tricks up its sleeves in this arena as well.  When pymel detects that it is being imported in an external
interpreter it automatically initializes maya.standalone and adds variables to your environment from your Maya.env file, steps which you 
would normally have to manage yourself.


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
            str     --> string
            float     --> double
            int        --> long
            bool    --> bool
            Vector    --> double3
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

#class A(object):
#    pass
#
#class B(A): pass
#
#class C(A): pass

# will check for the presence of an initilized Maya / launch it
from mayahook import mayaInit as _mayaInit
#print "imported mayahook"
assert _mayaInit() 

#import tools
#print "imported tools"
#
import core.pmtypes.factories as factories
#print "imported factories"

import api
#print "imported api"

from core import *
#print "imported core"

import mayahook.plogging as plogging
from mayahook.plogging import getLogger
from util.test import pymel_test

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

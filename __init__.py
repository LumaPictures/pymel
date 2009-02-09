
# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com
 
"""
*******************************
          Pymel
*******************************

Pymel makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of MEL commands into python functions. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. Pymel
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.


.. contents:: 
    :backlinks: none
    :depth: 3

=======================================
What's New in Version 0.8
=======================================
---------------------------------------    
Licensing Change
---------------------------------------

Pymel is now released under the BSD license, which is as open as open source gets.  Your studio can freely use, contribute to, and 
modify this module with no strings attached.

---------------------------------------    
Additions and Changes
---------------------------------------

Module reorganization:

.. packagetree:: pymel
    :style: uml

    
API Hybridization: 
        - the Node hierarchy now automatically derives many of its methods from API MFn classes
 
New Classes:
        - The `MelGlobals` class adds dictionary-like access to mel global variables
        - The `Version` class simplifies comparison of Maya versions
        - New mesh component classes `MeshVertex`, `MeshEdge`, and `MeshFace` add many new methods, as well as extended slice syntax
        
General Improvements:
        - Commands and classes created by plugins are now added to pymel namespace on load and removed on unload
        - Name-independent dictionary hashing for nodes in maya 2009: see section `Using PyNodes as Keys in Dictionaries`_
        - Added `DagNode.addChild` as well an addChild operator ( | ) for DAG objects: `DagNode.__or__`
        - The `Mel` class now prints mel errors and line numbers when an exception is raised
        - The `Mel` class returns pymel Vectors and Matrices
        - Name changes are automatically reflected in PyNode objects

---------------------------------------
Non-Backward Compatible Changes
---------------------------------------
    - Attribute disconnection operator has changed from ``<>`` to ``//``
        ``<>`` operator corresponds to __ne__ method, whose other operator is '!=' and we need that to mean 'not equal'.
    - Node classes no longer inherit from unicode: see `PyNodes Are Not Strings`_
        This allows node classes to reflect name changes such as parenting or renaming, a key aspect of the API integration
    - Instantiation of non-existent PyNode objects (nodes and attributes) now results in an exception: see `Non-Existent Objects`_
        Also a side-effect of the API integration.  Prevents mistakes and produces more pythonic code with use of new exception classes
    - _BaseObj has been replaced with `PyNode` class, which operates like the old PyNode function
        Provides more intuitive relationship between PyNode() and node classes
    - removed method-chaining between shapes and their history
        Chaining transforms to shapes is used throughout Maya, but the additional chaining of shapes to their history can produce
        unexpected results that are difficult to troubleshoot
    - redesigned `ObjectSet` class
    - completely rewrote `Vector` and `Matrix` classes


=======================================
Installation
=======================================

---------------------------------------
Pymel Package
---------------------------------------


Pymel is installed like any other python module or package.  In general, installing python pacakges can be a bit tricky, and Maya
adds an extra level of complexity.   To find available modules, python searches directories set in an environment variable called PYTHONPATH.
This environment variable can be set for each Maya install using the Maya.env file, or it can be set at the system-level, and
all instances of python, including those built into Maya will read it.  I recommend setting your PYTHONPATH at both the system level
level and the Maya.env level because it is more reliable and because it will allow you to use pymel from a standalone python interpreter.
 
Install Using Maya.env
======================

OSX and Linux
-------------

If on linux or osx, the simplest way to install pymel is to place the unzipped pymel folder in your Maya scripts directory. This 
will allow you to immediately use pymel from within Maya.  However, it is usually a good idea to create a separate directory for your python 
scripts so that you can organize them independently of your mel scripts.  

Let's say that you decide to create your own python development directory ``~/dev/python/``.  The pymel *folder* would go within this 
directory at ``~/dev/python/pymel``. Then you would add this line to your Maya.env:

.. python::
 
    PYTHONPATH = ~/dev/python

Windows
-------

On, Windows you might create a directory for python development at ``C:\My Documents\python\``. 
Then you would add this line to your Maya.env:

.. python::

    PYTHONPATH = C:\My Documents\python


System Install
==============

OSX and Linux
-------------

Setting up your python paths for the system on OSX and Linux is a little bit involved.  I will focus on OSX here, because Linux users
tend to be more technical. When you open a terminal on osx ( /Applications/Utilites/Terminal.app ), your shell may be using
several different scripting languages.  You can easily tell which is being used by looking at the label on the top bar of the terminal 
window, or the name of the tab, if you have more than one open.  It will
most likely say "bash", which is the default.  To set up python at the system level using bash, first create a new file called ``.profile``
in your home directory ( ~/ ).  Inside this file paste the following, being sure to set the desired Maya version:
 
.. python::

    export PYTHONDEV=~/dev/python
    export MAYA_LOCATION=/Applications/Autodesk/maya2009/Maya.app/Contents
    export PATH=$MAYA_LOCATION/bin:$PYTHONDEV/pymel/tools/bin:$PATH
    export PYTHONPATH=$PYTHONPATH:$PYTHONDEV


The first line sets your custom python directory, under which should be your pymel directory.
You can change this to whatever you want, but make sure your pymel directory is directly below this path. 
The second line sets a special Maya environment variable that helps Maya determine which version to use when working via the command
line ( be sure to point it to the correct Maya version).  The third line allows you to access all the executables in the Maya bin
directory from a shell without using the full path, and also allows you to use the special `ipymel` interpreter ( but only after you install
IPython!).  For example, you can launch Maya by typing ``maya``, or open a special Maya python interpreter by typing ``mayapy``. 
The last line ensures that python will see your python dev directory, where pymel resides.


Windows
-------

Click the Start Menu, right-click on "My Computer" and then click on "Properties".  This will open the "System Properties" window.  Click on
the "Advanced" tab, then on the "Environment Variables" button at the bottom.  In the new window that pops up, look
through your "User Varaibles" on top and your "System Variables" on the bottom, looking to see if the ``PYTHONPATH`` variable is set anywhere.

If it is not set, make a new variable for either your user or the system (if you have permission).  Use ``PYTHONPATH`` for the name and
for the the value use the directory *above* the pymel directory.  So, for example, if the pymel directory is ``C:\My Documents\python\pymel`` copy and 
paste in the value``C:\My Documents\python`` from an explorer window.

If ``PYTHONPATH`` is already set, select it and click "Edit".  This value is a list of paths separated by semi-colons.  Scroll to 
the end of the value and add a semi-colon ( ; ) and after this add the 
directory *above* the pymel directory to the end of the existing path. If the pymel directory is ``C:\My Documents\python\pymel`` copy and 
paste in the value ``C:\My Documents\python`` *after* the semi colon that you just added.

Find and edit your PATH variable, appending to the end of the existing value a semi-colon ( ; ) and the value 
``C:\Program Files\Autodesk\Maya2008\bin;C:\My Documents\python\pymel\tools\bin``.  These are just example paths: be sure to use 
the path to the Maya bin directory for your desired version of Maya as well as the path to your pymel bin directory.


userSetup files
===============


Next, to avoid having to import pymel every time you startup, you can create a userSetup.mel
file, place it in your Maya scipts directory and add this line:

.. python::

    python("from pymel import *");

Alternately, you can create a userSetup.py file and add the line:

.. python::

    from pymel import *

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

    #. Follow the installation instructions above for `System Install`
    #. Install IPython.  I recommend downloading the tarball, not the egg file. Unzip the tar.gz and put the sub-directory named IPython somewhere on your PYTHONPATH,
       or just put it directly into your python site-packages directory
    #. Open a terminal and run::
    
        chmod 777 `which ipymel`
        
    #. then run::
    
        ipymel


Windows
=======

    #. Follow the installation instructions above for `System Install`
    #. Install python for windows, if you have not already.
    #. Install IPython using their windows installer.  The installer will most likely not find the maya python install, 
       so install IPython to your system Python instead (from step 1).
    #. Install pyreadline for windows, also from the IPython website
    #. Copy the IPython directory, pyreadline directory, and all the pyreadline.* files from your system site-packages directory 
       ( ex.``C:\Python25\Lib\site-packages ) to your Maya site-packages directory ( ex. ``C:\Program Files\Autodesk\Maya2008\Python\lib\site-packages`` ). 
    #. open a command prompt ( go to Start menu, then click 'Run...', then enter ``cmd`` ).  Once it is open execute the following line to start ipymel::
    
        ipymel.bat


---------------------------------------
Problems on Linux
---------------------------------------

If you encounter an error loading the plugin in on linux, you may have to fix a few symlinks. 
As root, or with sudo privileges do the following::

    cd /lib64
    ls -la libssl*

You might see something like the following returned::
    
    -rwxr-xr-x 1 root root 302552 Nov 30  2006 libssl.so.0.9.8b
    lrwxrwxrwx 1 root root     16 Jul 16  2007 libssl.so.6 -> libssl.so.0.9.8b

The distribution of python that comes with maya is compiled to work with a particular flavor and version of linux, but yours most likely
differs. In my case, it expects libssl.so.4, but i have libssl.so.6 and libssl.so.0.9.8b.  So, I have to 
create a symbolic link to the real library::
    
    sudo ln -s libssl.so.0.9.8b libssl.so.4

I've found that the same thing must sometimes be done for libcrypto.so.4, as well.

=======================================
    Design Philosophy
=======================================

---------------------------------------
Procedural (maya.cmds)
---------------------------------------

When approaching the reorganization of the existing commands provided by maya.cmds, pymel follows these practical guidelines:

    - a value returned by a query flag should be accepted as a valid argument by the corresponding edit flag
        - example: ``camera( 'persp', e=1, focalLength = camera( 'persp', q=1, focalLength=1)   )``
    - a function which returns a list should return an empty list (not None) if it finds no matches 
        - example: `ls`, `listRelatives` 
    - a function which always returns a single item should not return that item in a list or tuple 
        - example: `spaceLocator`
    - wherever possible, pymel/python objects should be returned
        - example: pretty much every command
    - a function which provides a mapping mechanism should have a dictionary-like pymel counterpart 
        - example: `fileInfo` and `FileInfo`, `optionVar` and `OptionVar`
    - a function which returns a list of pairs should be a 2D array, or possibly a dictionary 
        - example: ``ls( showType=1 )``, ``listConnections(connections=1)``
    - the arguments provided by a ui callback should be of the appropriate type 
        - as a test, it should be capable of being used to set the value of the control 
    - if a function's purpose is to query and edit maya nodes, that node should be passed as an argument, not a keyword
        - example: `sets`

---------------------------------------
Object-Oriented
---------------------------------------

In constructing the PyNode classes, pymel follows these design rules:

    - node classes should never use properties -- all behavior should be placed in methods to differentiate them from shorthand attribute syntax
        - ( ex. foo.bar retrieves an Attribute class, foo.bar() executes a function )
    - node classes are named after the nodes they control, not the mel commands that they proxy  
        - ( ex. Locator vs. spaceLactor )
    - a value returned by a get* function should be accepted as a valid argument by the corresponding set* function


=======================================
    Background
=======================================
    
        
MEL is a procedural language, meaning it provides the ability to encapsulate code
into reusable "procedures" ( aka "functions" ).  (This is probably old news to you, but
bear with me, there's a midly entertaining analogy coming up ). The term "procedural programming" is 
mentioned primarily in the context of disguishing something from the newer, object-oriented paradigm. If you have used MEL
extensively you know you can get pretty far with procedural programming alone,
but once you've gotten comfortable with python's object-oriented design, you will never go back. 

Object-oriented programming adds another level of organization by creating logical groupings of functions
which are accessed from a common "object".  A quick perusal of the hundreds of MEL commands in the Maya documentation
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

Enter Pymel.  The primary reasons for pymel's existence are threefold:

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

Before we proceed let's make sure we have a clean scene so that you'll get the same results as me::

    >>> newFile( f=1 )
    Path('untitled')
    
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
pymel adds methods for operating on the specific type of maya object that the string represents. 

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

You can do the same thing for any command in pymel as well.

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

Here's another handy feature of python: it supports 2D arrays, meaning you can put lists inside lists.  Pymel takes advantage of
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
of these functions tend to fall into one or two of the following categories:  creating, listing, querying/editing. 
As you begin to retrain yourself to use a more object-oriented approach, you should know where to focus your efforts. 
Use these guidelines for what aspects of pymel are best suited to object-oriented programming:


    1. creating nodes and UI elements : remains mostly procedural
    2. listing objects and UI elements:  object-oriented, except for general listing commands like `ls`
    3. querying and editing objects and UI elements:  object-oriented, except for commands that operate on many nodes, like `select` and `delete`



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
    <class 'pymel.core.nodetypes.Transform'>
    
Commands that create objects are wrapped as well:
    >>> t = polySphere()[0]
    >>> print t, type(t)
    pSphere1 <class 'pymel.core.nodetypes.Transform'>
    
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
nasty string processing ahead of you.  And what if someone renames the node or its name becomes non-unique?  With PyMEL, the nightmares
of string comparisons are over.

But since pymel uses the underlying API objects, these operations are simple
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
        
---------------------------------------
PyNodes Are Not Strings
---------------------------------------

In previous versions of pymel, the node classes inherited from the builtin unicode string class.  With the introduction of the new API
underpinnings, the node classes inherit from a special `ProxyUnicode` class, which has the functionality of a string object, but
removes the immutability restriction ( see the next section `Mutability And You`_ ).  It is important to keep in mind that although
PyNodes *behave* like strings in most situations, they are no longer actual strings. Functions which explicity require a string, and which worked 
with PyNodes in previous versions of pymel, might raise an error with version 0.8 and later. For example:

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

In versions of pymel previous to 0.8, the node classes inherited from python's built-in unicode
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

There is one caveat to the mutability of node names: it can cause problems when using a pymel node as a key in a dictionary prior to 2009.
The reason is that the hash ( a hash is an integer value which is used to speed up dictionary access ) generated by a pymel node
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
    >>> c = polyCube()[0]
    >>> store()  # save the state of the current scene
    >>>
    >>> # make some changes
    >>> s.rename('monkey')
    Transform(u'monkey')
    >>> delete(c)
    >>> polyTorus()
    [Transform(u'pTorus1'), PolyTorus(u'polyTorus1')]
    >>>
    >>> diff() # print out what's changed since we ran 'store()'
    renamed: nurbsSphere1 ---> monkey
    renamed: nurbsSphereShape1 ---> monkeyShape
    new: polyTorus1
    new: pTorus1
    new: pTorusShape1
    deleted: pCube1
    deleted: pCubeShape1
    deleted: polyCube2


---------------------------------------
Enumerators
---------------------------------------

---------------------------------------
Node Class Hierarchy
---------------------------------------


Pymel provides a class for every node type in Maya's type hierarchy.  The name of the class is the node type captitalized.  Wherever possible,
pymel will return objects as instances of these classes. This allows you to use builtin python functions to inspect
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
    3. manually, written by pymel team

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

    >>> l = nodetypes.SpotLight()
    >>> print "The name is", l
    The name is spotLightShape1
    >>> print "The maya type is", l.type()
    The maya type is spotLight
    >>> print "The python type is", type(l)    
    The python type is <class 'pymel.core.nodetypes.SpotLight'>

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

    >>> cam = nodetypes.Camera(name='newCam')
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

=======================================
Non-Existent Objects
=======================================

Previous versions of pymel allowed you to instantiate classes for nonexistent objects.  This could be useful in circumstances where
you wished to use name formatting methods, and was also part of several PyMEL idioms, including PyNode.exists(). 

Starting with this version, an exception will be raised if the passed name does not represent an object in the scene. This has several advantages:

    1. you will never accidentally attempt to work with a node or attribute that does not exist
    2. it brings PyMEL's attribute handling more in line with pythonic rules, where attributes must exist before accessing them
    3. it prevents the awkward situation of having an object for which only a handful of methods will actually work
    
The side-effect, however, is that certain conventions for existence testing are no longer supported, while new ones have also been added.

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
    MayaAttributeError: Maya Attribute does not exist: u'earth.myAttr'
    
Shorthand notation:
    >>> x = polySphere(name='moon')[0]
    >>> x.myAttr
    Traceback (most recent call last):
        ...
    AttributeError: Transform(u'moon') has no attribute or method named 'myAttr'
    
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
    
---------------------------------------
Other Pymel Idioms
---------------------------------------
Two other pymel idioms have been removed as a result of this change. `Attribute.add` has been removed because, the attribute has to exist
in order to successfully get an Attribute instance.  So instead you have to use the addAttr method on the node:


No longer supported:
    
    >>> PyNode('persp').myNewFloatAttr.add( at=float ) #doctest: +SKIP
    
Still supported:

    >>> PyNode('persp').addAttr( 'myNewFloatAttr', at=float )

Similarly, the ``force`` flag for setAttr functions, which creates the attribute before setting if it does not exist, can only be safely used from the node class
and not the attribute class:

No longer supported:
  
    >>> PyNode('persp').myNewIntAttr.set( 2, force=1 ) #doctest: +SKIP

Still supported:

    >>> PyNode('persp').setAttr( 'myNewIntAttr', 2, force=1 )

New construct:
 
    >>> PyNode('persp').setDynamicAttr( 'myNewIntAttr', 2 )
      
--------------------------------------------
Manipulating Names of Non-Existent Objects
--------------------------------------------

One advantage of the old way of dealing with non-existent objects was that you could use the name parsing methods of the PyNode
classes to manipulate the object's name until you found what you were looking for.  To allow for this, we've added
several classes which operate on non-existent nodes and contain only methods for string parsing and existence testing.
These nodes can be found in the `other` module and are named `other.NameParser`, `other.AttributeName`, `other.DependNodeName`, and `other.DagNodeName`.


--------------------------------------------
Asserting Proper Type
--------------------------------------------

While `PyNode` serves to easily cast any string to its proper class in the node hierarchy, other nodes in the hierarchy can achieve the 
same effect:

    >>> PyNode('lambert1')
    Lambert(u'lambert1')
    >>> DependNode('lambert1')
    Lambert(u'lambert1')

If the determined type does not match the requested type, an error will be raised.  For example, a lambert node is not
a DAG node:

    >>> DagNode( 'lambert1' )
    Traceback (most recent call last):
    ...
    TypeError: Determined type is Lambert, which is not a subclass of desired type DagNode

This is useful because it can be used as a quick way to assert that a given node is of the desire type.

    >>> try:
    ...    DagNode( selected()[0] )
    ... except TypeError:
    ...    print "Please select a DAG node"
    
 
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
directory.  Pymel ensures that using python outside of Maya is as close as possible to python inside Maya.  When pymel detects that it is being imported in a standalone
interpreter it performs these operations:

    1. initializes maya.standalone ( which triggers importing userSetup.py )
    2. parses your Maya.env and adds variables to your environment
    3. sources userSetup.mel
     
Because of these improvements, working in this standalone environment 
is nearly identical to working in interactive mode, except of course you can't create windows.  However, there are two caveats
that you must be aware of.  

    - scriptJobs do not work: use callbacks derived from `api.MMessage` instead
    - maya.cmds does not work inside userSetup.py (and thus any function in pymel that relies on maya.cmds)

The second one might seem a little tricky, but we've already come up with the solution: a utility function called `pymel.mayahook.executeDeferred`.
Jump to the docs for the function for more information on how to use it.


=======================================
    Special Thanks
=======================================

Special thanks to those studios with the foresight to support an open-source project of this nature:  Luma Pictures, 
Attitude Studio, and ImageMovers Digital.

"""


__version__ = '0.9.0'
__authors__ = ['Chad Dombrova', 'Olivier Renouard', 'Ofer Koren', 'Paul Molodowitch']
# not maya dependant
#import util
#print "imported utils"


import sys

import mayahook
import mayahook.plogging as plogging
logger = plogging.getLogger(__name__)
logger.debug( 'imported mayahook' )

import api
logger.debug( 'imported api' )


# will check for the presence of an initilized Maya / launch it
from mayahook import mayaInit as _mayaInit
assert _mayaInit() 

#import tools
#print "imported tools"
#
import core.factories as factories
logger.debug( 'imported factories' )

from core import *
logger.debug( 'imported core' )

# should not spend startup time with tests unless we are debugging
#from util.test import pymel_test

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

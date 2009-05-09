
=======================================
What's New in Version 0.9
=======================================

----------------------
API Hybridization
----------------------

PyMEL 0.9 is a dramatic leap forward in the evolution of python in Maya.  The node and attribute classes have been rewritten 
from the ground up to use the python API as their foundation, increasing the speed and fidelity of PyMEL's object-oriented design.  

PyMEL harnesses the API to create a name-independent representation of your object.  
This means that the annoying inconsistencies of string comparisons are over: no more worrying about short names versus long names, DAG paths, unique paths,
instance paths...  it's all handled intelligently for you.  And what's more, if *anything* causes the name of your object to change it 
will automatically be reflected in your python object.

Below, we make a camera, rename it, and then group and instance it, to demonstrate how the name changes are constantly reflected. Keep in mind
that the changes could have just as easily been performed by the user interacting with objects through the GUI.

    >>> cam, shape = camera()
    >>> print cam
    camera1
    >>> cam.rename('renderCam')
    Transform(u'renderCam')
    >>> print cam
    renderCam
    >>> grp = group(cam)
    >>> instance(grp)
    [Transform(u'group2')]
    >>> print cam
    group1|renderCam
    >>> cam.getInstances()
    [Transform(u'group1|renderCam'), Transform(u'group2|renderCam')]

Comparing attributes is just as easy.  

    >>> # long and short names retrieve the same attribute
    >>> cam.t == cam.translate    
    True
    >>> cam.tx == cam.translate.translateX
    True

Like MEL, PyMEL will also look up shape attributes from a transform:

    >>> cam  # confirm that cam is a transform
    Transform(u'group1|renderCam')
    >>> cam.focalLength  # get the focalLength of the shape
    Attribute(u'group1|renderCam|renderCamShape.focalLength')
    >>> cam.focalLength == cam.getShape().focalLength
    True
    
Beyond this new purity of behavior, PyMEL node classes now include hundreds of new methods derived from the API, but with the same intuitive and unified design as before.
With PyMEL you get the benefits of API speed and versatility without the advanced learning curve.

--------------------
BSD License
--------------------
    
PyMEL is released under the BSD license, which is as open as open source gets.  Your studio can freely use, contribute to, and 
modify this module with no strings attached.


------------------------------
Improved Standalone Support
------------------------------

Unlike the maya module, PyMEL behaves the same in a standalone interpreter as it does in an GUI session.
When PyMEL detects that it is being imported in a standalone
interpreter it performs these operations:

    #. initializes maya.standalone
    #. parses your Maya.env and adds variables to your environment
    #. sources Autodesk's initialization MEL scripts
    #. sources user preferences
    #. sources userSetup.mel

This will save you a lot of time and headache when using Maya in a standalone environment.

--------------------------------
Tighter MEL Integration
--------------------------------

Calling MEL from python is still an unfortunate necessity, so PyMEL makes it as easy as possible.  

MEL Tracebacks and Line Numbers
===============================

In the new release, when a MEL script called from PyMEL raises an error, you will get the specific mel error message in the python traceback, along with line numbers!
    
For example, here's a procedure "myScript" with a line that will result in an error:

    >>> mel.eval( '''global proc myScript( string $stringArg, float $floatArray[] ){ 
    ...     float $donuts = `ls -type camera`;}''')
    
When we call it, we can quickly determine the problem:

    >>> commandEcho(lineNumbers=1)  # turn line numbers on
    >>> mel.myScript( 'foo', [] )
    Traceback (most recent call last):
        ...
    MelConversionError: Error occurred during execution of MEL script: line 2: Cannot convert data of type string[] to type float.

Global Variables Dictionary
===========================

Also, getting and setting MEL global variables is accomplished via a special dictionary-like object:

    >>> melGlobals['$gMainFileMenu'] #doctest: +SKIP
    'mainFileMenu'
    >>> melGlobals['$gGridDisplayGridLinesDefault'] = 2   #doctest: +SKIP 
    
    
--------------------------------
Easily Compare Maya Versions
--------------------------------

    >>> if Version.current > Version.v2008:
    ...     print "The current version is later than Maya 2008"
    The current version is later than Maya 2008
       
--------------------------------
Other Improvements
--------------------------------

    - New and improved math classes
    - Expanded documentation
    - Loads of useful utilities
    - Commands and classes created by plugins are now added to pymel namespace on load and removed on unload
    - Name-independent dictionary hashing for nodes in maya 2009: see section `Using PyNodes as Keys in Dictionaries`_
    - Added `DagNode.addChild` as well an addChild operator  ``|`` for DAG objects: `DagNode.__or__`
    - The `Version` class simplifies comparison of Maya versions
    - New mesh component classes `MeshVertex`, `MeshEdge`, and `MeshFace` add many new methods, as well as extended slice syntax
 
   
---------------------------------------
Non-Backward Compatible Changes
---------------------------------------
    - Attribute disconnection operator has changed from ``<>`` to ``//``
        ``<>`` operator corresponds to ``__ne__`` method, whose other operator is ``!=`` and we need that to mean 'not equal'.
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
    - data classes like `Vector` and `Matrix` are now found in the `datatypes` namespace to avoid conflicts with node types


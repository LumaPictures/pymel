
=======================================
    Design Philosophy
=======================================

---------------------------------------
    Background
---------------------------------------
    
        
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

Enter PyMEL.  The primary reasons for pymel's existence are threefold:

    1. to fix bugs in ``maya.cmds``
    2. to modify the behavior of maya.cmds to improve workflow and make it more pythonic ( like returning an empty list instead of None )
    3. to provide a complete object-oriented design for working with nodes, attributes, and other maya structures

If you're still not sure you're ready to make the jump to object-oriented programming, the first two points alone
are reason enough to use pymel, but the object-oriented design is where PyMEL really shines.  PyMEL 
strikes a balance between the complicated yet powerful API, and straightforward but unruly MEL. 


---------------------------------------
Procedural (``maya.cmds``)
---------------------------------------

When approaching the reorganization of the existing commands provided by ``maya.cmds``, PyMEL follows these practical guidelines:

    - a value returned by a query flag should be accepted as a valid argument by the corresponding edit flag
        - example: ``camera( 'persp', e=1, focalLength = camera( 'persp', q=1, focalLength=1)   )``
    - a function which returns a list should return an empty list (not None) if it finds no matches 
        - example: `ls`, `listRelatives` 
    - a function which always returns a single item should not return that item in a list or tuple 
        - example: `spaceLocator`
    - wherever possible, pymel/python objects should be returned
        - example: pretty much every command
    - a function which provides a mapping mechanism should have a dictionary-like PyMEL counterpart 
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

In constructing the PyNode classes, PyMEL follows these design rules:

    - node classes should never use properties -- all behavior should be placed in methods to differentiate them from shorthand attribute syntax
        - ( ex. ``foo.bar`` retrieves an ``Attribute`` class, ``foo.bar()`` executes a function )
    - node classes are named after the nodes they control, not the mel commands that they proxy  
        - ( ex. ``nt.Locator`` vs. ``spaceLactor`` )
    - a value returned by a get* function should be accepted as a valid argument by the corresponding set* function




=============================================
Why PyMEL?
=============================================

.. _why_wrappers:

---------------------------------------------
The Nature of the Beast
---------------------------------------------

Rather than reinvent the wheel, Autodesk opted to provide "wrappers" around their pre-existing toolsets: the :term:`C++ API` and :term:`MEL`.  By wrapping them they provided an alternate python interface for each, but the core code that comprises the API and MEL remained largely the same.  The wrappers serve as a (hopefully) thin layer to communicate between python and the Maya code being wrapped. The nature of the wraps is slightly different for each.  

``maya.OpenMaya``
	In the case of the C++ API, Autodesk went with an open source wrapper called `swig <http://www.swig.org/exec.html>`_ which generates python functions and classes from C++ counterparts. The python layer rests on top of C++, which remains the native execution language. During execution, swig marshals data back and forth between python and C++. 

MEL itself is split into two components: commands, and everything else.

``maya.cmds``
	In the case of MEL commands, which are (effectively) written using the C++ API, Autodesk wrote the wrapping mechanism themselves such that MEL commands could also be registered and used in python as functions. The same command executed in MEL and python ultimately end up triggering the same underlying C++ API calls. 

``maya.mel.eval``
	In order to allow execution of arbitrary MEL code such as procedures, Autodesk provided high level access to the MEL interpreter. This is as simple of a wrapper as you can get: evaluate a string representing a chunk of MEL code in the MEL interpreter and convert the result to a python object (string, float, int, and lists thereof).


..
	(this is not completely accurate, as some of the older core commands bypass the API, but we'll ignore that for the sake of conceptual simplicity).

	====================== ==================================================
	                       Python Module
	====================== ==================================================
	API classes            ``maya.OpenMaya``, ``maya.OpenMayaAnim``, ...
	MEL commands           ``maya.cmds``
	MEL                    ``maya.mel``
	====================== ==================================================


So now that python is available in Maya all of our problems are solved, right?  Well, not quite.  Since these new modules are just wraps of the same underlying API and MEL code that we've had all along and neither were intended to eventually become "pythonified", the syntax that results from this layering of python over MEL and C++ tends to be awkward, especially to those familiar with python's idioms. 

This syntactical awkwardness, particularly in ``maya.cmds``, was one of the initial inspirations behind PyMEL. Think of it this way: would you rather read a book that was translated from japanese into english by a software program like babelfish or by a  human who is fluent in both languages? That is a key difference between an automatic wrap like ``maya.cmds`` and a "restructured wrap" like PyMEL, which uses the maya python modules as building blocks to construct an intuitive, insightful, and pythonic API.

---------------------------------------------
The Paradigm Shift
---------------------------------------------

MEL is a procedural language, meaning it provides the ability to encapsulate code into reusable "procedures" ( aka "functions" ).  (This is probably old news to you, but bear with me, there's a mildly entertaining analogy coming up ). The term "procedural programming" is used primarily in the context of distinguishing a language from the newer, object-oriented paradigm. 

Object-oriented programming adds organization by creating logical groupings of functions which are accessed from a common "object".  If you have used MEL extensively you know you can get pretty far with procedural programming alone, but there is often an exponential relationship between the complexity of a task and the amount of code it will take to complete in MEL.  In other words, progress breaks down once the task at hand becomes too complicated. Object-oriented code tends to be easier to read and write, provides the ability to easily create new data types and reuse code, and ultimately scales better to complex tasks. 

To prove my point, here's a quick example that we'll cover in more depth later.

procedural::

	cmds.getAttr( cmds.listRelatives( cmds.ls(type='camera')[0], p=1 )[0] + '.translate' )[0][2]

object oriented::

	pymel.ls(type='camera')[0].getParent().translate.get().z
	
See how nicely that reads from left to right? Object oriented programming isn't necessarily about brevity, it's about legibility derived from structure. 

A quick perusal of the more than three thousand MEL commands in the Maya documentation will give you an idea why object-oriented groupings are a good idea.  MEL is like a tool chest, a wardrobe, and a kitchen set all dumped into a bathtub -- everything in there is useful in the proper context, but you've really got to know what you're looking for to get anything done.  The shame of it is that Maya's great innovation is that it is itself inherently object-oriented -- every scene represents networks of nodes, each with its own unique abilities and those that it inherits from its super-classes.  Maya's API is object-oriented, too.  So how did MEL end up so crippled?

The original idea behind MEL and the API was to create a tiered relationship where complex tasks, or tasks where execution time is of great concern, were to be performed using the C++ API and bundled into easy-to-use MEL commands.  These commands were in turn to become the building blocks of more generalized tasks performed in MEL.  The API would be the toolset of the superuser -- with access to complex types and external libraries --  whereas the scope of MEL would be much more limited and thus more accessible to the average user.  

The advent of python in Maya brought a common language to MEL and the API, and as a result, the clarity of this tiered structure has become muddied.  API classes, MEL commands, and MEL procedures can be used within the same python script, completely outside the context of a plugin.  Moreover, python manages to borrow the strengths of both languages: like C++, it is object-oriented and extensible through third party libraries and custom types, but like MEL, python is easy to learn, protects the user from certain daunting programming concepts, and compiles at runtime.  Having managed to provide an object-oriented design without a steep learning curve, python makes the simplicity of MEL seem like an unfortunate over-simplification.

So, on the one hand we have the C++ API, now easily accessible from within Python, object-oriented, but too cryptic and verbose for everyday tasks, and on the other hand, we have a host of thousands of MEL-commands-turned-python-functions, too valuable to do without, but woefully unorganized and "unpythonic". Which do we use?  How can they work together?  PyMEL bridges this gap by forging a new object-oriented API that's as powerful and easy to use as python is.  



..
	When I began designing PyMEL, I started by sifting through every... single... MEL command and, if possible, associating it with a node type. This is the fundamental precept of object-oriented design -- group your functions around a common object.  It was the first step in the right direction.

	
	It has a hierarchy of classes that roughly mirror the nodes available in Maya. MEL, being by design a simple procedural language accessible to your average artist, had most of these concepts stripped from it. 

	The primary reasons for PyMEL's existence are threefold:

	    1. to fix bugs in maya.cmds
	    2. to modify the behavior of maya.cmds to improve workflow and make it more pythonic ( like returning an empty list instead of None )
	    3. to provide a complete object-oriented design for working with nodes, attributes, and other maya structures

	If you're still not sure you're ready to make the jump to object-oriented programming, the first two points alone are reason enough to use pymel, but the object-oriented design is where PyMEL really shines.  PyMEL strikes a balance between the complicated yet powerful API, and straightforward but unruly MEL. 



	Originally, the gap was intentional, but now we find ourselves asking "how can we bridge the gap?".  How can we use what 


	Further emphasizing this tiered structure, MEL commands could be executed from the API, but the reverse, executing API from MEL, was neither possible nor desirable, except indirectly by calling registered commands. 



	Through the use of classes and modules, python makes sure that everything is in its right place.



	..
		Only a few fundamental types are supported in MEL, and the ability to access the API from MEL was fundamentally prohibited, except through pre-compiled commands.  This hides the complexity of coding and compiling C++ code from the average scripter. 
		Unlike Python, it cannot operate without an instance of Maya running. 


		Fast-forward 10 years to the present.  Scripting languages like python and perl have become commonplace in VFX and animation studios for performing everyday pipeline tasks such as moving, manipulating, and parsing files, communicating with databases, and building standalone user interfaces.  Unlike MEL, these languages are not tied to any particular application and have benefitted from years of active development. In comparison, MEL seems downright antiquated and restrictive.

		So, as you well know, Autodesk has added python to Maya, but you may still be wondering what exactly that means. First and foremost, it means providing access to python's interpreter within Maya ( The interpreter is the software responsible for executing python code ). The second step is to provide modules with functions and classes for working with maya objects and user interfaces. 





	============================= =============================
	MEL                           Python
	============================= =============================
	script (*.mel)                module (*.py)
	procedure                     function
	command                       builtin function
	============================= =============================


---------------------------------------
Glossary
---------------------------------------

.. glossary::

	MEL
		short for Maya Embedded Language, is a scripting language written for Maya, and with which much of Maya's functionality and user interface is built. It was designed to be concise, simple, and Maya-specific.  

	C++ API
		provides deeper access to Maya's internals.  With the API you can create new node types and new MEL commands. Prior to the introduction of python in Maya, the API could only be used with C++. 


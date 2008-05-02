
"""
Mel To Python Translator
========================

Convert mel scripts into python scripts


Known Limitations
=================

array index assignment
----------------------	

In mel, you can directly assign the value of any element in an array, and all intermediate elements will be 
automatically filled. This is not the case in python: if the list index is out of range an IndexError will be 
raised. I've added fixes for several common array assignment conventions:

append new element
~~~~~~~~~~~~~~~~~~

MEL::

	$strArray[`size $strArray`] = "foo";
	
Python
	>>> strArray.append("foo")

assignment relative to end of array
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MEL::

	strArray[`size $strArray`-3] = "foo";
	
Python	
	>>> strArray[-3] = "foo"

However, since the translator does not track values of variables, it does not know if any given index is out of
range or not. so, the following would raise a 'list assignment index out of range' error when converted to
python and would need to be manually fixed::

	string $strArray[];
	for ($i=0; $i<5; $i++)
		$strArray[$i] = "foo"
	
				
for(init; condition; update)
----------------------------

	the closest equivalent to this in python is something akin to:

		>>> for i in range(start, end)
		
	in order for this type of for loop to be translated into a python for loop it must meet several requirements:
	
		1. the initialization, condition, and update expressions must not be empty.
			
			not translatable::
			
			  	for(; ; $i++) print $i;
		
		2. there can be only one conditional expression.   
			
			not translatable::
			
			  	for($i=0; $i<10, $j<20; $i++) print $i;
		
		3. the variable which is being updated and tested in the condition (aka, the iterator) must exist alone on one
			side of the	conditional expression. this one is easy enough to fix, just do some algebra:
			
			not translatable::
			
			  	for($i=0; ($i-2)<10, $i++) print $i;
	
			translatable::
			
			  	for($i=0; $i<(10+2), $i++) print $i;
		
		4. the iterator can appear only once in the update expression:
			
			not translatable::
			
			  	for($i=0; $i<10; $i++, $i+=2) print $i;
			  	
	if these conditions are not met, the for loop will be converted into a while loop:
	
		>>> i=0
		>>> while 1:
		>>> 	if not ( (i - 2)<10 ):
		>>> 		break			
		>>> 	print i			
		>>> 	i+=1
			

Inconveniences
==============

Switch Statements
-----------------		
Alas, switch statements are not supported by python. the translator will convert them into an if/elif/else statement.


Global Variables
----------------		

Global variables are not shared between mel and python.  two functions have been added to pymel for this purpose:
`getMelGlobal` and `setMelGlobal`. by default, the translator will convert mel global variables into python global 
variables AND intialize them to the value of their corresponding mel global variable using getMelGlobal(). if your 
python global variable does not need to be shared with other mel scripts, you can remove the get- and
setMelGlobals lines (for how to filter global variables, see below). however, if it does need to be shared, it is very
important that you manually add setMelGlobal() to update the variable in the mel environment before calling any mel 
procedures that will use the global variable. 

In order to hone the accuracy of the translation of global variables, you will find two dictionary parameters below --
`global_var_include_regex` and `global_var_exclude_regex` -- which you can use to set a regular expression string
to tell the translator which global variables to share with the mel environment (i.e. which will use the get and set
methods described above) and which to not.  for instance, in my case, it is desirable for all of maya's global 
variables to be initialized from their mel value but for our in-house variables not to be, since the latter are often
used to pass values within a single script. see below for the actual regular expressions used to accomplish this.
						
						
Command Callbacks
-----------------

one common point of confusion is command callbacks with ui elements. There are several different ways to handle 
command callbacks on user interface widgets:  
						
Function Name as String
~~~~~~~~~~~~~~~~~~~~~~~

maya will try to execute this as a python command, but unless you know the namespace it will
be imported into, the function will not be recognized. notice how the namespace must be hardwired
into the command:

	>>> button( c="myCommand" )

or

	>>> button( c="myModule.myCommand" )

this method is not recommended.

Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is referenced by the command flag.  also, keep in mind many ui widgets such as radioButtonGrp
pass args to the function (to mimic the "myCommand #1" functionality in mel), which your function must accommodate. The
tricky part is that different ui elements pass differing numbers of args to their callbacks, and some pass none at all.
This is why it is best for your command to use the *args syntax to accept any quantity of args, and then deal with them
in the function.

	>>> def myCommand( *args ): print args # this definition must come first

	>>> button( c=myCommand )
				
Lambda Functions
~~~~~~~~~~~~~~~~
In my experience this is the best way to handle most command callbacks.  You can choose exactly which args you want
to pass along to your function and order of definition does not matter.

	>>> button( c= lambda *args: myCommand(args[0]) )

	>>> def myCommand( arg ): print "running", arg 

						
						
Comments
--------
Rules on where comments may be placed is more strict in python, so expect your comments to be shifted around a bit
after translation.


Formatting
----------
				
Much of the formatting of your original script will be lost. I apologize for this, but python is much more strict
about formatting than mel, so the conversion is infinitely simpler when the formatting is largely discarded
and reconstructed based on pythonic rules.


Solutions and Caveats
=====================

catch and catchQuiet	
--------------------

There is no direct equivalent in python to the catch and catchQuiet command and it does not exist in maya.cmds so i wrote two
python commands of the same name and put them into pymel. these are provided primarily for compatibility with 
automatically translated scripts. try/except statements should be used instead of catch or catchQuiet if coding
from scratch.

for( $elem in $list )
---------------------
	
This variety of for loop has a direct syntactical equivalent in python.  the only catch here is that maya.cmds 
functions which are supposed to return lists, return None when there are no matches. life would be much simpler 
if they returned empty lists instead.  the solution currently lies in pymel, where i have begun
correcting all of these command to return proper results.  i've started with the obvious ones, but there 
are many more that i need to fix.  you'll know you hit the problem when you get this error: 'TypeError: iteration
over non-sequence'. just email me with commands that are giving you problems and i'll fix them as
quickly as i can.   						

"""


from melparse import *
import pymel.core.pmtypes.path as path
from pymel.util.external.ply.lex import LexError
"""
This is a dictionary for custom remappings of mel procedures into python functions, classes, etc. If you are like me you probably have a
library of helper mel scripts to make your life a bit easier. you will probably find that python has a built-in equivalent for many of
these.

i've provided a few entries as examples to show you how to implement remappings in mel2py. the first procedure in the dictionary is
'firstElem', which simply returns the first element of a string array, useful when the first element of a command is all you need. as you
can see, the key in the dictionary is the procedure name, and the value is a function which takes two inputs: a list of arguments to the
procedure being remapped, and a ply yacc token object, which you probably will not need to use. the function should return a string
representing the new command. also, note that the list of arguments will all be strings and will already be converted into their python
equivalents. in the case of 'firstElem', it will perform conversions like the following:
	
		firstElem( ls(sl=1) ) 	--> 	ls(sl=1)[0]
		
		firstElem( myListVar )	-->		myListVar[0]
	
"""



custom_proc_remap = { 
		'firstElem' 			: lambda args, t: '%s[0]' 				% (args[0]),
		'firstFloatElem' 		: lambda args, t: '%s[0]' 				% (args[0]),
		'firstElem' 			: lambda args, t: '%s[0]' 				% (args[0]),
		'stringArrayAppend'		: lambda args, t: '%s + %s' 			% (args[0], args[1]),
		'stringInArray'			: lambda args, t: '%s in %s' 			% (args[0], args[1]),
		'stringInStringArray'	: lambda args, t: '%s in %s' 			% (args[0], args[1]),
		'stringArrayPrefix'		: lambda args, t: '[ %s + x for x in %s ]' 	% (args[0], args[1]),
		'stringArraySuffix'		: lambda args, t: '[ x + %s for x in %s ]' 	% (args[0], args[1]),
		'addPad' 				: lambda args, t: "'%0" +  args[1] + "d' % " + args[0],
		'getRefFileFromObject'	: lambda args, t: '%s.referenceFile()'	% (args[0])
		}
		
# do not change the following line !!!
proc_remap.update(custom_proc_remap)



def mel2pyStr( data, currentModule=None, pymelNamespace='', verbosity=0 ):
	"""
	convert a string representing mel code into a string representing python code
	
		>>> import pymel.mel2py as mel2py
		>>> print mel2py.mel2pyStr('paneLayout -e -configuration "top3" test;')
		paneLayout('test',configuration="top3",e=1)
		
	Note that when converting single lines, the lines must end in a semi-colon, otherwise it is techincally
	invalid syntax.
	
	The currentModule argument is the name of the module that the hypothetical code is executing in. In most cases you will
	leave it at its default, the __main__ namespace.
	
	"""
	
	mparser = MelParser()
	mparser.build(currentModule, pymelNamespace=pymelNamespace, verbosity=verbosity)
	return mparser.parse( data )

def mel2py( melfile, outputDir=None, pymelNamespace='', verbosity=0 ):
	"""
	Convert a mel script into a python script. 
	
		>>> import pymel.mel2py
		>>> pymel.mel2py.mel2py( 'scriptEditor.mel', '~/Documents' )
		
	if no output directory is specified, the python script will be written to the same directory as the input mel file. 
	
	if only the name of the mel file is	passed, mel2py will attempt to determine the location of the file using the 'whatIs' mel command,
	which relies on the script already being sourced by maya.
	"""
	
	global currentFiles
	
	if not currentFiles:
		currentFiles = [melfile]
	
	
	melfile = path.path( melfile )
	if not melfile.exists():
		try:
			import pymel
			melfile = path.path( pymel.mel.whatIs( melfile ).split(': ')[-1] )
		except:
			pass
	data = melfile.bytes()
	print "converting mel script", melfile
	converted = mel2pyStr( data, melfile.namebase, pymelNamespace=pymelNamespace, verbosity=verbosity )
	header = "%s from mel file:\n# %s\n\n" % (tag, melfile) 
	
	converted = header + converted
	
	if outputDir is None:
		outputDir = melfile.parent

	pyfile = path.path(outputDir + os.sep + melfile.namebase + '.py')	
	print "writing converted python script: %s" % pyfile
	pyfile.write_bytes(converted)
	

def mel2pyBatch( processDir, outputDir=None, pymelNamespace='', verbosity=0 , test=False):
	"""batch convert an entire directory"""
	processDir = path.path(processDir)
	
	global currentFiles
	#currentFiles = filter( lambda x: not x.name.startswith('.'), processDir.files( '*.mel') )
	currentFiles = processDir.files( '[a-zA-Z]*.mel')
	
	"""
	for f in currentFiles:
		try:
			mel2py( f, outputDir, False, True, verbosity )
		except:
			pass
	global global_procs
	print 'Found %d procedures'	% len(global_procs)
	"""
	
	succCnt = 0
	importCnt = 0
	for f in currentFiles:
		try:
			mel2py( f, outputDir, pymelNamespace=pymelNamespace, verbosity=verbosity )
			succCnt += 1
		except (ValueError, IndexError, TypeError, LexError), msg:
			print 'failed:', msg
		
		if test:
			try:
				__import__(f.namebase)
			except (SyntaxError, IndentationError):
				print 'A syntax error exists in this file that will need to be manually fixed'
			except RuntimeError:
				print 'This file has code which executed on import and failed'
			except ImportError:
				pass
			except:
				print 'This file has code which executed on import and failed'
			else:
				importCnt += 1
	
	print "%d total processed for conversion" % len(currentFiles)
	print "%d files succeeded" % succCnt
	print "%d files failed" % (len(currentFiles)-succCnt)
	if test:
		print "%d files imported without error" % (importCnt)
	
	succCnt = 0
	
	
	
	

if __name__ == '__main__':
	import sys
	if len(sys.argv) == 2:
		mel2py(sys.argv[1], verbosity=1)
	elif len(sys.argv) == 3:
		mel2py(sys.argv[1], sys.argv[2], verbosity=1)

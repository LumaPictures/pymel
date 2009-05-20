
==================================================
Seting Up PyMEL Autocompletion in Eclipse
==================================================

--------------------------------------------------
Before You Begin
--------------------------------------------------

	* `Download <http://download.eclipse.org/eclipse/downloads>`_ and install the Eclipse SDK.
	* Use Eclipse's **Software Update** window (under help) to install `PyDev <http://pydev.sourceforge.net/download.html>`_
	* You may also want to install a trial of `PyDev Extensions <http://fabioz.com/pydev/index.html>`_. I can't live without its `Mark Occurrences <http://fabioz.com/pydev/manual_adv_markoccurrences.html>`_ feature.

--------------------------------------------------
OSX	Leopard
--------------------------------------------------

Setting up auto-completion on OSX and Linux is more involved than on Windows. Follow along closely.

Adding The Maya Python Interpreter
==================================

	1.	With Eclipse open, click on the **Eclipse** menu, then **Preferences...**
	2.	In the left pane, drop down to **Pydev > Interpreter-Python**
	3.	Click the **New..** button at the top right of the **Python Interpreters** preferences window
	4.	In the browser that comes up, you want to choose Maya's python interpreter.  The problem is that it's buried within Maya.app and Python.app, which you cannot access in this simple browser (thanks Apple!).  Here's a trick that will save you many times over: hold down Command+Shift+G to bring up a box to enter a path (that's the Apple "Comand" button, plus Shift, plus the letter G). 
	
		.. image:: images/pymel_eclipse_104.png
		
		This shortcut works in the finder as well. Now, due to a bug on Eclipse's part, you can't *paste* a path in here, so you'll have to arduously type it out ( however, it does have some basic tab completion to help you along ).  Type in this path::
	
			/Applications/Autodesk/maya2009/Maya.app/Contents/Frameworks/Python.framework/Versions/2.5/Resources/Python.app/Contents/MacOS/Python
	
	5.	Once you choose the "Python" binary, you'll get this window:
	
		.. image:: images/pymel_eclipse_105.png
		
		Check the first two libraries, as I have done in the image.  I have some other "egg" folders listed here that you probably don't have -- just ignore them.
	
	6.	Next, add the path to our Maya python site-packages directory.  Click the **New Folder** button to bring up the browser again. Navigate to::
	
			/Applications/Autodesk/maya2009/Maya.app/Contents/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages
	
	7.	Finally, add the directory *above* your pymel folder to the list of System Libs. The final result should look like this:
	
		.. image:: images/pymel_eclipse_107.png
			:height: 598
			:width: 987
		
		The last path in the image above is the directory above my pymel folder

Adding Forced Builtins
======================

Because PyMEL contains many dynamically created functions and classes, simply parsing its modules is not sufficient to produce the full set of completions.  Luckily, Pydev has a special list of modules that it inspects more thoroughly.  Starting from where we left off in the Pydev preferences under Python Interpreters...

	1.	Change to the **Forced Builtins** tab.
	2.	Add each of the following PyMEL builtins::

			pymel.api.allapi
			pymel.core.animation
			pymel.core.datatypes
			pymel.core.effects
			pymel.core.general
			pymel.core.language
			pymel.core.modeling
			pymel.core.nodetyeps
			pymel.core.other
			pymel.core.rendering
			pymel.core.system
			pymel.core.windows

		.. note::
			I've left a few modules out that are less often used, such as ``pymel.core.runtime`` and ``pymel.core.context``.  Feel free to add these, too.
			
	3.	If you plan on doing any Maya plugin development you should also add these to your builtins (or at least OpenMaya and OpenMayaMPx)::

			maya.OpenMaya
			maya.OpenMayaAnim
			maya.OpenMayaCloth
			maya.OpenMayaFX
			maya.OpenMayaMPx
			maya.OpenMayaRender

		.. image:: images/pymel_eclipse_203.png
			:height: 598
			:width: 987

Adding Environment Variables
============================

The last step is to add the environment variables that enable the python interpreter to properly load Maya's libs

	1.	Change to the **Environment** tab.
	2.	Add each of the following variables:
	
		=======================  ================================================================ 
		Name                     Value
		=======================  ================================================================
		``MAYA_LOCATION``        ``/Applications/Autodesk/maya2009/Maya.app/Contents``
		``DYLD_LIBRARY_PATH``    ``/Applications/Autodesk/maya2009/Maya.app/Contents/MacOS``
		``DYLD_FRAMEWORK_PATH``  ``/Applications/Autodesk/maya2009/Maya.app/Contents/Frameworks``
		=======================  ================================================================

		.. image:: images/pymel_eclipse_302.png
			:height: 537
			:width: 947
	
	3.	Double check that your environment variables points to the same version of Maya	as the Maya site-packages directory under **Libraries**	
	4.	Press **OK** and wait while Pydev to parse all your python files


Testing That It Worked
======================

	1.	Restart Eclipse
	2.	Create a new file from within eclipse ( **File / New / File** ) named foo.py 
	3.	Add the following line::
		
			import pymel
	
	4.	Now type::
	
			pymel.bin
			
		There should be a pause at the period, and you should see a Python app open up in you dock. This is good. It means eclipse is initializing maya and doing a full inspection of PyMEL.  When it completes, you should get ``bindSkin()`` as a completion.  Don't worry, this long pause will only happen once.

		.. image:: images/pymel_eclipse_404.png
			:height: 493
			:width: 816
			
.. note::
	
	If you like to import everything from pymel, aka ``from pymel import *``, then you should open the Eclipse preferences, go to **Pydev > Editor > Code Completion**, and enable **Autocomplete on all letter chars and '_'**
	
Troubleshooting
~~~~~~~~~~~~~~~
	
If you're still not getting completion:
	
	* Restart Eclipse and retry steps 3 and 4 above
	* Go to Eclipse preferences under **Pydev > Editor > Code Completion** and increase **Timeout to connect to shell** to 30 seconds.
	* Open a log view (**Window / Show View / Error Log**) and if you see any suspicious errors, post for help at the `Pydev suport forum <https://sourceforge.net/forum/forum.php?forum_id=293649>`_




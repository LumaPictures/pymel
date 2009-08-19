
==================================================
Seting Up PyMEL Autocompletion in Eclipse
==================================================

--------------------------------------------------
Before You Begin
--------------------------------------------------

	* `Download <http://download.eclipse.org/eclipse/downloads>`_ and install the Eclipse SDK.
	* Use Eclipse's **Software Update** window (under help) to install `PyDev <http://pydev.sourceforge.net/download.html>`_
	* You may also want to install a trial of `PyDev Extensions <http://fabioz.com/pydev/index.html>`_. I can't live without its `Mark Occurrences <http://fabioz.com/pydev/manual_adv_markoccurrences.html>`_ feature.

These instructions are updated for Pydev 1.4.6, and should work on either Eclipse 3.4.x or 3.5.x


--------------------------------------------------
Adding The Maya Python Interpreter
--------------------------------------------------

	1.	Open the Eclipse preferences window.

		============================================== ==============================================
		Windows                                        OSX
		============================================== ==============================================
		under the **Window** menu:                         under the **Eclipse** menu:
		
		.. image:: images/pymel_eclipse_win_101.png    .. image:: images/pymel_eclipse_osx_101.png
		============================================== ==============================================

			
	2.	In the left pane, drop down to **Pydev > Interpreter-Python**
	3.	Click the **New..** button at the top right of the **Python Interpreters** preferences window
	4.	In the window that comes up give your interpreter a name (such as maya2009-osx). 
	5.  Next, you can either copy and paste the path to your maya interpreter (aka ``mayapy``) or you can click 'Browse' and navigate to it.  

		.. note:: On OSX, browsing to ``mayapy`` is not as easy as it should be. The problem is that it's buried within Maya.app, which you cannot access in a file browser (thanks Apple!).  To get to it, hold down **Command+Shift+G** to bring up a box to enter a path (that's the Apple "Command" button, plus Shift, plus the letter G). You can't use Command-V to *paste* a path in this browser, but you *can* right click in the path entry box and choose Paste.

		
		.. |win_104| image:: images/pymel_eclipse_win_104.png  
						:width: 452                                          
						:height: 344
						
		.. |osx_104| image:: images/pymel_eclipse_osx_104.png
		  				:width: 481
		  				:height: 361
		  
		====================================================== ==================================================================
		Windows                                                OSX
		====================================================== ==================================================================
		``C:\Program Files\Autodesk\Maya2009\bin\mayapy.exe``  ``/Applications/Autodesk/maya2009/Maya.app/Contents/bin/mayapy``
		
		|win_104|                                              |osx_104|
		====================================================== ==================================================================
		
		..
			**default mayapy locations:**
			
			=======================  =================================================================
			OS                       LOCATION
			=======================  =================================================================
			Windows                  ``C:\Program Files\Autodesk\Maya2009\bin\mayapy.exe``
			OSX                      ``/Applications/Autodesk/maya2009/Maya.app/Contents/bin/mayapy``
			Linux (32 bit)           ``/usr/autodesk/maya2009/bin/mayapy``
			Linux (64 bit)           ``/usr/autodesk/maya2009-x64/bin/mayapy``
			=======================  =================================================================
	
	5.	Once you choose the "mayapy" binary, you'll get this window:

		.. |win_105| image:: images/pymel_eclipse_win_105.png  
						:width: 466                                          
						:height: 432
						
		.. |osx_105| image:: images/pymel_eclipse_osx_105.png
		  				:width: 914
		  				:height: 484
		
		====================================================== ==================================================================
		Windows                                                OSX
		====================================================== ==================================================================
		|win_105|                                              |osx_105|
		====================================================== ==================================================================
		
		on windows: add a check beside ``python25.zip``.
		
		If you installed PyMEL using the :ref:`install_setuptools` method, you'll see the pymel "egg" in the list of automatically detected site packages.
		Press "OK" and skip down to the next section.
		
		If you installed PyMEL using the :ref:`install_manual` method, then you will have to add the directory *above* your pymel folder to the
		list of System Libs. To do this, first click "OK" to confirm the automatically detected libs. After it finishes parsing the directories
		click the **New Folder** button and browse to the directory above your pymel folder.

--------------------------------------------------
Adding Forced Builtins
--------------------------------------------------

Because PyMEL contains many dynamically created functions and classes, simply parsing its modules is not sufficient to produce the full set of completions.  Luckily, Pydev has a special list of modules that it inspects more thoroughly.  Starting from where we left off in the Pydev preferences under Python Interpreters...

	1.	Change to the **Forced Builtins** tab.
	2.	Add each of the following PyMEL builtins (you can copy and paste the whole list at once)::

			pymel.api.allapi, pymel.core.animation, pymel.core.datatypes, pymel.core.effects, pymel.core.general, pymel.core.language, pymel.core.modeling, pymel.core.nodetyeps, pymel.core.other, pymel.core.rendering, pymel.core.system, pymel.core.windows

		.. note::
			I've left a few modules out that are less often used, such as ``pymel.core.runtime`` and ``pymel.core.context``.  Feel free to add these, too.
			
	3.	If you plan on doing any Maya plugin development you should also add these to your builtins (or at least OpenMaya and OpenMayaMPx)::

			maya.OpenMaya, maya.OpenMayaAnim, maya.OpenMayaCloth, maya.OpenMayaFX, maya.OpenMayaMPx, maya.OpenMayaRender

		
		.. image:: images/pymel_eclipse_win_203.png
			:height: 504
			:width: 723

--------------------------------------------------
Adding Environment Variables
--------------------------------------------------

The last step is to add the environment variables that enable the python interpreter to properly load Maya's libs. 

	.. note:: On Windows this step is optional if you properly :ref:`setup your environment <install_system_env>`.

	1.	Change to the **Environment** tab.
	2.	Add the following variables, using the proper path for your installation of Maya:
		
		**Windows Variables:**
		
		=======================  ================================================================ 
		Name                     Example Value
		=======================  ================================================================
		``MAYA_LOCATION``        ``C:\Program Files\Autodesk\Maya2009``
		=======================  ================================================================

		.. image:: images/pymel_eclipse_win_302.png
			:height: 504
			:width: 723
			
		**OSX Variables:**

		=======================  ================================================================ 
		Name                     Example Value
		=======================  ================================================================
		``MAYA_LOCATION``        ``/Applications/Autodesk/maya2009/Maya.app/Contents``
		``DYLD_LIBRARY_PATH``    ``/Applications/Autodesk/maya2009/Maya.app/Contents/MacOS``
		``DYLD_FRAMEWORK_PATH``  ``/Applications/Autodesk/maya2009/Maya.app/Contents/Frameworks``
		=======================  ================================================================
			
		.. image:: images/pymel_eclipse_osx_302.png
			:height: 537
			:width: 947


	3.	Double check that your environment variable points to the same version of Maya	as the Maya site-packages directory under the **Libraries**	tab
	4.	Press **OK** in the Preference window and wait while Pydev parses all your python files. 


--------------------------------------------------
Testing That It Worked
--------------------------------------------------

	1.	Restart Eclipse
	2.	Create a new file from within eclipse ( **File / New / File** ) named foo.py or whatever you want ( just make sure to include the .py )
	3.	Add the following line::
		
			import pymel
	
	4.	Now type::
	
			pymel.bin
			
		There should be a pause at the period.  ( If you are using OSX, you should see a Python app open up in your dock. This is good. It means eclipse is initializing maya and doing a full inspection of PyMEL. ) Afterwards, you should get ``bindSkin()`` as a completion.  Don't worry, this long pause will only happen once per eclipse session.

		.. image:: images/pymel_eclipse_osx_404.png
			:height: 493
			:width: 816
			
.. note::
	
	If you like to import everything from pymel, aka ``from pymel import *``, then you should open the Eclipse preferences, go to **Pydev > Editor > Code Completion**, and enable **Autocomplete on all letter chars and '_'**

--------------------------------------------------	
Troubleshooting
--------------------------------------------------
	
If you're still not getting completion:

	* Go to Eclipse preferences under **Pydev > Editor > Code Completion** and increase **Timeout to connect to shell** to 30 seconds or more.
	* Restart Eclipse and retry steps 3 and 4 above
	* Open a log view (**Window / Show View / Error Log**) and if you see any suspicious errors, post for help at the `Pydev suport forum <https://sourceforge.net/forum/forum.php?forum_id=293649>`_



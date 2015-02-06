

=======================================
Installation
=======================================

---------------------------------------
Supported Platforms
---------------------------------------

Our goal is to support the 3 latest versions of Maya.

---------------------------------------
PyMEL Package
---------------------------------------

.. _install_setuptools:

Easy Install
============

As of version 0.9.1 PyMEL supports installation via setuptools, which makes it a lot easier to get started if you're not well-versed in the intricacies of the ``PYTHONPATH``.  If you don't already have setuptools installed it will be downloaded for you when you run the install command below, but in order for this to all go smoothly you must have the following things:

    * a connection to the internet
    * write permission to your Maya installation directory
    
If you fall short on either of these you can always perform a `Manual Install`_ of PyMEL.

Installation on OSX
-------------------

    #.  Open a shell: you'll find the Terminal app in ``/Applications/Utilities``
        
    #.  ``cd`` to the directory where you extracted the pymel zip file. A file called "setup.py" should exist directly below this directory.
        For example, I downloaded and extracted mine to my "Downloads" folder::
    
            cd ~/Downloads/pymel-1.0.0
       
        .. note:: On OSX and Linux you have to escape spaces in folder names ( or you can press the Tab key to auto-complete paths ). Here is an
            example of escaping a space in a folder name (notice the backslash after ``Image``)::
       
                cd /Applications/Image\ Capture.app
    
    #.  Next, from the shell, run the installation for each version of Maya that you have installed::

            sudo /Applications/Autodesk/maya2008/Maya.app/Contents/bin/mayapy setup.py install
            sudo /Applications/Autodesk/maya2009/Maya.app/Contents/bin/mayapy setup.py install
            sudo /Applications/Autodesk/maya2010/Maya.app/Contents/bin/mayapy setup.py install

        You should be able to drag and drop the mayapy executable from the finder into the shell to get the path.


Installation on Windows
-----------------------

    #.  Open a shell: from the Start menu go to "Run...", then type in ``cmd`` and press "OK"
	
		.. note:: On Windows Vista and above you will need to open ``cmd`` as administrator.  To do this right-click the ``Command Prompt``
			and select ``Run as administrator``.
     
    #.  ``cd`` to the directory where you extracted the pymel zip file. A file called "setup.py" should exist directly below this directory.
        For example, I downloaded and extracted mine to my desktop::
    
            cd "C:\Desktop\pymel-1.0.0"

    #.  Next, from the shell, run the installation for each version of Maya that you have installed::

            "C:\Program Files\Autodesk\Maya2008\bin\mayapy.exe" setup.py install
            "C:\Program Files\Autodesk\Maya2009\bin\mayapy.exe" setup.py install
            "C:\Program Files\Autodesk\Maya2010\bin\mayapy.exe" setup.py install

        You should be able to drag and drop the mayapy.exe executable from windows explorer into the shell to get the path. Don't forget to wrap it in quotes.
        
        .. note:: Be sure to use the proper path to *your* mayapy.exe.  For example, if you have 32-bit maya installed on 64-bit windows, it will be installed to ``C:\Program Files (x86)`` instead of ``C:\Program Files``
                    
.. _install_manual:

Manual Install
==============


If the easy install did not turn out to be so easy, PyMEL can always be manually installed like any other python module or package. The process is simple in concept:

    1. put the extracted ``pymel`` folder somewhere
    2. tell python where to find it

To find available modules, python searches directories set in an environment variable called ``PYTHONPATH``.  This environment variable can be set for each Maya installation using the Maya.env file, or it can be set at the system level, which will set it for all instances of python, including those bundled with each Maya installation (aka "mayapy"). 


============================================================ ========================================== ==========================================
..                                                           :ref:`Maya.env <install_maya_env>`         :ref:`System-Level <install_system_env>`
============================================================ ========================================== ==========================================
allows per-maya configuration of environment variables       YES                                        NO
------------------------------------------------------------ ------------------------------------------ ------------------------------------------
allows easy execution of ``maya`` and ``mayapy`` in a shell  NO                                         YES
============================================================ ========================================== ==========================================


.. note:: If you set your ``PYTHONPATH`` at the system level it will override any values for ``PYTHONPATH`` set in Maya.env, except on OSX when launching Maya from it's application bundle (an application bundle is the icon you click on to launch Maya).


.. _install_maya_env:

Manual Method 1: Setting Up Your Environment Using Maya.env
------------------------------------------------------------

The instructions below on setting up your python environment are essential to learning how to properly deploy any python module, not just PyMEL, and mastering them is also key to using the :doc:`standalone`.

.. warning:: installation instructions have changed since version 0.9, so pay attention. PyMEL now includes a partial override of the maya package.  This means that both the ``pymel`` and ``maya`` sub-directories must be on the python path, and they must come **before** the standard maya package in the search path. To keep things simple, we are now recommending that the top-level ``pymel-1.0.x`` directory be added to the ``PYTHONPATH`` instead of copying the ``pymel`` sub-directory. 

..

  1. extract the pymel zip file that you downloaded.  The directory structure should look something like this::
     
        pymel-1.0.0
        |-- docs
        |-- examples
        |-- extras
        |-- maya*
        |   `-- app
        |       `-- startup
        |-- pymel*
        |   |-- api
        |   |-- cache
        |   |-- core
        |   |-- internal
        |   |-- tools
        |   |   |-- bin
        |   |   |-- mel2py
        |   |   `-- scriptEditor
        |   `-- util
        |       `-- external
        |           `-- ply
        `-- tests
     
    The folders marked with an asterisk are the required pymel packages, which must be on the PYTHONPATH.  **If you wish to relocate PyMEL, be sure to move both the pymel and maya folders.**

  2. Locate the Maya.env for the desired version of Maya and open it in your favorite text editor. Maya.env can be found in your ``MAYA_APP_DIR`` under a sub-directory for each version of Maya.

    ================= =================================================
    OS                MAYA_APP_DIR
    ================= =================================================
    Linux             ~/maya
    ----------------- -------------------------------------------------
    OSX               ~/Library/Preferences/Autodesk/maya
    ----------------- -------------------------------------------------
    Windows           drive:\\My Documents\\maya
    ================= =================================================

  3. Once open, add a line to set ``PYTHONPATH`` to the top-level directory where you extracted pymel (the directory that contains both pymel and maya folders).  The ``PYTHONPATH`` variable is a list of paths separated by semi-colons (on windows) or colons (on osx and linux).  For example:

    On Windows::

        PYTHONPATH = C:\path\to\pymel-1.0.0;C:\path\to\something_else
    
    On OSX and Linux::

        PYTHONPATH = /path/to/pymel-1.0.0:/path/to/something_else

.. _install_system_env:


Manual Method 2: Setting Up Your System Environment
---------------------------------------------------

OSX and Linux
~~~~~~~~~~~~~

Setting up your python paths at the system level on OSX and Linux is a little bit involved.  I will focus on OSX here, because Linux users tend to be more technical. 

When you open a terminal on OSX ( ``/Applications/Utilites/Terminal.app`` ), your shell may be using one of several different scripting languages.   (You can easily tell which is being used by looking at the label on the top bar of the terminal window, or the name of the tab, if you have more than one open. ) It will most likely say "bash", which is the default, so that is what I will explain here.  

To set up python at the system level using bash, first create a new file called ``.profile`` in your home directory ( usually something like ``/Users/yourname`` and denoted in a shell with the shortcut ``~/`` ).  Inside this file paste the following, being sure to set the desired Maya version::

    export MAYA_LOCATION=/Applications/Autodesk/maya2009/Maya.app/Contents
    export PATH=$MAYA_LOCATION/bin:$PATH
    export PYTHONPATH=/path/to/pymel-1.0.0

Here's a line-by-line breakdown of what you just did:

    1.  set ``MAYA_LOCATION``, a special Maya environment variable that helps Maya determine which version to use when working via the command line ( be sure to point it to the correct Maya version).  
    2.  the ``PATH`` environment variable is a list of paths that will be searched for executables. Each path is separated by a colon ``:``.By adding ``$MAYA_LOCATION/bin`` you can access all the executables in the Maya bin directory from a shell without using the full path. For example, you can launch Maya by typing ``maya``, or open a Maya python interpreter by typing ``mayapy``. 
        
        If you manually installed pymel and `ipymel`_, include the path to the directory where the ipymel script resides. For example, if the path to the ipymel script is ``/path/to/pymel-1.0.0/pymel/tools/bin/ipymel``, the line might look like the following::

            export PATH=$MAYA_LOCATION/bin:/path/to/pymel-1.0.0/pymel/tools/bin:$PATH

    3.  finally, set the ``PYTHONPATH`` to ensure that python will see the ``pymel`` and ``maya`` packages.  Like the ``PATH`` environment variable, ``PYTHONPATH`` is a list of paths separated by colons ``:``.



Windows XP
~~~~~~~~~~

    1.  Open the Start Menu, right-click on "My Computer" and then click on "Properties".  This will open the "System Properties" window.  
    2.  Changed to the "Advanced" tab, then click on the "Environment Variables" button at the bottom.  
    3.  In the new window that pops up, search through your "User Varaibles" on top and your "System Variables" on 
        the bottom, looking to see if the ``PYTHONPATH`` variable is set anywhere.
        
        If it is not set, make a new variable for either your user or the system (if you have permission).  Use ``PYTHONPATH`` for the name and for the the value use the directory *above* the ``pymel`` directory.  So, for example, if the pymel directory is ``C:\My Documents\pymel-1.0.0\pymel`` copy and paste in the value ``C:\My Documents\pymel-1.0.0`` from an explorer window.
        
        If ``PYTHONPATH`` is already set, select it and click "Edit".  This value is a list of paths separated by semi-colons.  Scroll to the end of the value and add a semi-colon ``;`` and after this add the directory *above* the pymel directory to the end of the existing path. For example, let's say the starting value is::
            
            C:\Python25\lib
        
        If the top-level pymel directory is ``C:\My Documents\pymel-1.0.0\pymel``, the edited value would be::
        
            C:\Python25\lib;C:\My Documents\pymel-1.0.0

    4.  Add and set your ``MAYA_LOCATION``.  For example, for 2008 it would be::
    
            C:\Program Files\Autodesk\Maya2008

    5.  Next, find and edit your ``PATH`` variable. Append the following to the end of the existing value::
    
            %MAYA_LOCATION%\bin
        
        Don't forget to put a semi-colon ``;`` between the existing paths and the new ones that you are adding.
        
        *If installing ipymel* include the path to your ipymel bin directory. For example, if you manually installed PyMEL, the line should look like the following::

            %MAYA_LOCATION%\bin;C:\My Documents\pymel-1.0.0\pymel\tools\bin  

Manual Method 3: sitecustomize
------------------------------

If you have don't write permission to your Maya installation directory and you can't change your ``PYTHONPATH`` then you've come to the right place. This method relies on a special module in python called ``sitecustomize`` to dynamically insert PyMEL into the path when python starts.

An advantage of this approach is that it allows for an arbitrary block of code to execute, which means you can use whatever logic you like to determine in what cases to add PyMEL, what version to use, etc.

A potential disadvantage of this approach is that it adds PyMEL to the python path system-wide, instead of just inside Maya. However, there are a number of utilities in ``pymel.util`` that are useful outside of Maya as well, so this could be an advantage as well.

Here's how to setup PyMEL using sitecustomize:

 1. open your favorite text editor

 2. paste in the text below::

        import sys
        sys.path.insert(0,'/path/to/top-pymel-dir')

 3. Replace the ``/path/to/top-pymel-dir`` line with the path to the folder where you extracted PyMEL. The folder you want should contain both 'pymel' and 'maya' folders directly below it

 4. save this file as ``sitecustomize.py`` somewhere in your system python path. If you are unsure what your python path is, you can run this from the python tab in the script editor to find out. ::

        import sys
        for i in sys.path: print i

.. note:: If your studio is already using ``sitecustomize.py`` and you can't edit it, you can use the same instructions with the filename ``usercustomize.py`` instead. usercustomize is loaded immediately after sitecustomize and is intended for this situation.


---------------------------------------
ipymel
---------------------------------------

ipymel is an extension of the ultra-customizable IPython interpreter, which enables it to easily work with mayapy and PyMEL.  It adds tab completion of maya depend nodes, dag nodes, and attributes, as well as automatic import of PyMEL at startup.  Many more features to come. 

ipymel Easy Install
===================

As of version 0.9.2 ipymel is automatically installed when "easy" installing PyMEL, but you may have to do a few extra steps to get it working properly on Windows.
 
Windows Only:
        * Install python on your system. Install only the exact versions of python that come with Maya ( see `Versions of Maya and Python`_ ) 
        * Install pyreadline for windows from the `IPython <http://ipython.scipy.org/dist>`_ website. By default it will install to your system copy of Python.
        * Copy the pyreadline directory, and all the pyreadline.* files from your system site-packages directory 
          ( ex. ``C:\Python25\Lib\site-packages`` ) to your Maya site-packages directory ( ex. ``C:\Program Files\Autodesk\Maya2008\Python\lib\site-packages`` ). 
       
To Run: In a new shell, run the following command::
    
        ipymel

.. note:: The "easy" installation method produces an invalid ``ipymel.exe`` on 64-bit windows systems.  As of this writing I'm still looking into this.

.. note:: Though not a requirement for ipymel to work, it's best to read up on :ref:`install_system_env`
   
          
ipymel Manual Install
=====================

OSX and Linux
-------------

    #. Follow the installation instructions above for :ref:`install_system_env`
    #. Install IPython.  For a manual install, I recommend downloading the tarball, not the egg file. 
       Unzip the tar.gz and put the sub-directory named IPython somewhere on your ``PYTHONPATH``,
       or just put it directly into your python site-packages directory
    #. Open a terminal and run::
    
        chmod 777 `which ipymel`
        
    #. then run::
    
        ipymel


Windows
-------

    #. Follow the installation instructions above for :ref:`install_system_env`
    #. Install python for windows, if you have not already.
    #. Install `IPython <http://ipython.scipy.org/dist>`_ using their windows installer.  The installer will most likely not find the maya python install, 
       so install IPython to your system Python instead (from step 1).
    #. Install pyreadline for windows, also from the IPython website
    #. Copy the IPython directory, pyreadline directory, and all the pyreadline.* files from your system site-packages directory 
       ( ex. ``C:\Python25\Lib\site-packages`` ) to your Maya site-packages directory ( ex. ``C:\Program Files\Autodesk\Maya2008\Python\lib\site-packages`` ). 
    #. open a command prompt ( go to Start menu, then click 'Run...', then enter ``cmd`` ).  Once it is open execute the following line to start ipymel::
    
        ipymel.bat


---------------------------------------
Troubleshooting
---------------------------------------

Linux
=====

If you encounter an error installing on linux, you may have to fix a few symlinks. Here's how you check.  ``cd`` to the directory where you unzipped pymel (you should be in the same directory where ``setup.py`` is).  start up maya's standalone interpreter by typing ``mayapy`` (or provide the full path to mayapy script if you do not have Maya's bin directory on your ``PATH``) at the prompt.  now import setup.py as a module and run one of it's tests::

    import setup
    setup.test_dynload_modules()
    
This will print out any compiled modules that do not work on your platform.  This occurs because the flavor and/or distribution of Linux that you are running has different versions of certain system libraries than the one that Maya was compiled on. The easiest way to fix the problem is to create symbolic links from your existing libraries to those that Maya expects to find.
    
For example, in my case hashlib won't import because it can't find ``libssl.so.4``.  So, since I'm on a 64-bit version of linux, I check my ``/lib64/`` ( on a 32 bit OS, check ``/lib/`` ) ::

    cd /lib64
    ls -la libssl*

I see the following returned::
    
    -rwxr-xr-x 1 root root 302552 Nov 30  2006 libssl.so.0.9.8b
    lrwxrwxrwx 1 root root     16 Jul 16  2007 libssl.so.6 -> libssl.so.0.9.8b

In my case, Maya expects ``libssl.so.4``, but instead I have ``libssl.so.0.9.8b`` and a symbolic link ``libssl.so.6`` pointing to ``libssl.so.0.9.8b``.  So, I have to create a symbolic link **from the real library to the missing library**::
    
    sudo ln -s libssl.so.0.9.8b libssl.so.4

I've found that the same thing must sometimes be done for ``libcrypto`` as well.


---------------------------------------
userSetup files
---------------------------------------


Next, to avoid having to import pymel every time you startup, you can create a userSetup.py file and add the line::

    from pymel.core import *

---------------------------------------
Script Editor
---------------------------------------
PyMEL includes a replacement for the script editor window that provides the option to translate all mel history into python. 
Currently this feature is beta and works only in versions beginning with Maya 8.5 SP1.

.. warning:: this feature is still considered experimental

The script editor is comprised of two files located in the pymel/tools/scriptEditor directory: scriptEditorPanel.mel and pymelScrollFieldReporter.py.  

    #. Place the mel file into your scripts directory, and the python file into your Maya plugins directory. 
    #. Open Maya, go-to **Window** --> **Settings/Preferences** --> **Plug-in Manager** and load pymelScrollFieldReporter.  Be sure to also check "Auto Load" for this plugin. 
    #. Next, open the Script Editor and go to **History** --> **History Output** --> **Convert Mel to Python**. Now all output will be reported in python, regardless of whether the input is mel or python.




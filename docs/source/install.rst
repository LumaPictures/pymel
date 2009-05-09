

=======================================
Installation
=======================================

---------------------------------------
Supported Platforms
---------------------------------------

PyMEL is supported on any OS that Maya is supported on.  Our goal is to support the 3 latest versions of Maya.  At the time of this
writing, that means 2009, 2008, and 8.5 ( on 8.5 Service Pack 1 is required ).  However, python in Maya 8.5 is very buggy,
even with the service pack so as a result there are two aspects of PyMEL that will not work on 8.5:

	- No API Undo: node class methods that derive from API will not be undoable
	- Data class properties are read-only: operations such as ``Color().r=1.0`` or ``Vector().x=2.0`` will have no effect 


---------------------------------------
PyMEL Package
---------------------------------------

Easy Install
============

As of version 0.9.1 PyMEL supports installation via setuptools, which makes it a lot easier to get started if you're not well-versed in the intricacies of
the PYTHONPATH.  If you don't already have setuptools installed it will be downloaded for you when you run the install command below, but in order
for this to all go smoothly you must have the following things:

    * a connection to the internet
    * write permission to your Maya installation directory
    
If you fall short on either of these you can always perform a `Manual Install`_ of PyMEL.


    #.  Open a shell
        * on osx you'll find the Terminal app in /Applications/Utilities
        * on Windows, open the Start menu then go to "Run...", then put in ``cmd`` and press "OK"
        
    #.  ``cd`` to the directory where you extracted the pymel zip file. A file called setup.py should exist directly below this directory.
        For example, I downloaded and extracted mine to my "Downloads" folder on OSX::
    
            cd ~/Downloads/pymel-0.9.1
       
        NOTE: On OSX and Linux you have to escape spaces in folder names ( or you can press the Tab key to auto-complete paths ). Here is an
        example of escaping a space in a folder name (notice the backslash after ``Image``)::
       
           cd /Applications/Image\ Capture.app
           
        On Windows you can copy the path from Explorer and paste into the shell by right clicking.  You don't need to escape spaces.
        
    #.  Now run the installation for each version of Maya that you have installed using Maya's own python interpreter -- aka mayapy. 
        This ensure's that PyMEL is installed to the site-packages directory of each, and that it will always be on your PYTHONPATH when using Maya.
        
        On OSX::
       
            /Applications/Autodesk/maya2009/Maya.app/Contents/bin/mayapy setup.py install

        On Windows wrap the path in double quotes::
        
            "C:\Program Files (x86)\Autodesk\Maya2009\bin\mayapy.exe" setup.py install


Manual Install
==============

PyMEL can be installed like any other python module or package.
To find available modules, python searches directories set in an 
environment variable called PYTHONPATH.  This environment variable can be set for each Maya installation using the Maya.env 
file, or it can be set at the system level, which will set it for all instances of python, including those built into Maya (aka "mayapy").  
Each of these methods have their pros and cons.
    
    * Maya.env: 
        * allows per-maya configuration
        * does not allow easy execution of ``maya`` and ``mayapy`` in a shell
        
    * System install
        * only allows one configuration for all copies of Maya
        * will override values set in Maya.env ( except on OSX if you launch Maya from from an application bundle )
        * allows easy execution of ``maya`` and ``mayapy`` in a shell

On OSX you can get the best of both worlds if you set your PYTHONPATH at both the system level
level and the Maya.env level because the system settings will be ignored when launching Maya from its application bundle. On other operating systems
and when launching Maya from a shell on OSX, be aware that if you set your PYTHONPATH at the system level it will override any values found
in Maya.env.



Setting Up Your Environment Using Maya.env
==========================================

OSX and Linux
-------------

If on linux or osx, the simplest way to install pymel is to place the unzipped pymel folder in your Maya "scripts" directory. This 
will allow you to immediately use PyMEL from within Maya.  However, it is usually a good idea to create a separate directory for your own python 
modules so that you can organize them independently of your mel scripts.  

Let's say that you decide to create your python development directory ``~/dev/python``.  The pymel *folder* would go within this 
directory at ``~/dev/python/pymel``. Then you would add this line to your Maya.env::
 
    PYTHONPATH = ~/dev/python

Windows
-------

On, Windows you might create a directory for python development at ``C:\My Documents\python``. 
Then you would add this line to your Maya.env::

    PYTHONPATH = C:\My Documents\python


Setting Up Your System Environment
==================================

OSX and Linux
-------------

Setting up your python paths for the system on OSX and Linux is a little bit involved.  I will focus on OSX here, because Linux users
tend to be more technical. 

When you open a terminal on OSX ( /Applications/Utilites/Terminal.app ), your shell may be using
several different scripting languages.   (You can easily tell which is being used by looking at the label on the top bar of the terminal 
window, or the name of the tab, if you have more than one open. ) It will most likely say "bash", which is the default, so that 
is what I will explain here.  

To set up python at the system level using bash, first create a new file called ``.profile``
in your home directory ( ~/ ).  Inside this file paste the following, being sure to set the desired Maya version::

    export PYTHONDEV=~/dev/python
    export MAYA_LOCATION=/Applications/Autodesk/maya2009/Maya.app/Contents
    export PATH=$MAYA_LOCATION/bin:$PATH
    export PYTHONPATH=$PYTHONPATH:$PYTHONDEV

Here's a line-by-line breakdown of what you just did:

    1.  set your custom python directory. You can change this to whatever you want, but if you are not using the `Easy Install`_ method make 
        sure your pymel directory is immediately below this path (The variable ``PYTHONDEV`` does not have a special meaning to python or maya: 
        we're creating it so that we can reuse its value in the next few lines).
    2.  set a special Maya environment variable that helps Maya determine which version to use when working via the command
        line ( be sure to point it to the correct Maya version).  
    3.  this line allows you to access all the executables in the Maya bin
        directory from a shell without using the full path.
        For example, you can launch Maya by typing ``maya``, or open a Maya python interpreter by typing ``mayapy``. 
        
        *If installing ipymel* include the path to your ipymel bin directory. For example, if you manually installed PyMEL, the line should look like
        the following::

            export PATH=$MAYA_LOCATION/bin:$PYTHONDEV/pymel/tools/bin:$PATH

    4.  we set the ``PYTHONPATH`` to ensure that python will see your python dev directory, where PyMEL resides.



Windows
-------

    1.  Open the Start Menu, right-click on "My Computer" and then click on "Properties".  This will open the "System Properties" window.  
    2.  Changed to the "Advanced" tab, then click on the "Environment Variables" button at the bottom.  
    3.  In the new window that pops up, search through your "User Varaibles" on top and your "System Variables" on 
        the bottom, looking to see if the ``PYTHONPATH`` variable is set anywhere.
        
        If it is not set, make a new variable for either your user or the system (if you have permission).  Use ``PYTHONPATH`` for 
        the name and for the the value use the directory *above* the pymel directory.  So, for example, if the pymel directory is 
        ``C:\My Documents\python\pymel`` copy and paste in the value ``C:\My Documents\python`` from an explorer window.
        
        If ``PYTHONPATH`` is already set, select it and click "Edit".  This value is a list of paths separated by semi-colons.  Scroll to 
        the end of the value and add a semi-colon ( ; ) and after this add the 
        directory *above* the pymel directory to the end of the existing path. For example, let's say the starting value is::
            
            C:\Python25\lib
        
        If the pymel directory is ``C:\My Documents\python\pymel``, the edited value would be::
        
            C:\Python25\lib;C:\My Documents\python

    4.  Add and set your ``MAYA_LOCATION``.  For example, for 2008 it would be::
    
            C:\Program Files\Autodesk\Maya2008

    5.  Next, find and edit your ``PATH`` variable. Append the following to the end of the existing value::
    
            %MAYA_LOCATION%\bin
        
        Don't forget to put a semi-colon (;) between the existing paths and the new ones that you are adding.
        
        *If installing ipymel* include the path to your ipymel bin directory. For example, if you manually installed PyMEL, the line should look like
        the following::

            %MAYA_LOCATION%\bin;C:\My Documents\python\pymel\tools\bin  
            
---------------------------------------
ipymel
---------------------------------------

ipymel is an extension of the ultra-customizable IPython interpreter, which enables it to easily work with mayapy and PyMEL.  It adds tab completion of maya depend nodes,
dag nodes, and attributes, as well as automatic import of PyMEL at startup.  Many more features to come. 

ipymel Easy Install
===================


    #. Follow the installation instructions above for `Setting Up Your System Environment`_
    #. Start a new shell to ensure that all our newly set environment variables are refreshed.
    #. Next, we will use setuptools to automaticallly download ipython and install
       the ipymel binary to your Maya bin directory. As a bonus over the manual install, on Windows the ipymel script will become 
       an executable, ipymel.exe, instead of a batch file:

       On OSX and Linux::
            
            mayapy setup.py easy_install --script-dir=$MAYA_LOCATION/bin . pymel[ipymel]
    
       On Windows::
        
            mayapy setup.py easy_install --script-dir="%MAYA_LOCATION%\bin" . pymel[ipymel]

    #. Windows Only: 
        * Install pyreadline for windows from the `IPython <http://ipython.scipy.org/dist>`_ website
        * Copy the IPython directory, pyreadline directory, and all the pyreadline.* files from your system site-packages directory 
          ( ex. ``C:\Python25\Lib\site-packages`` ) to your Maya site-packages directory ( ex. ``C:\Program Files\Autodesk\Maya2008\Python\lib\site-packages`` ). 
       
    #. run::
    
        ipymel
        
ipymel Manual Install
=====================

OSX and Linux
-------------

    #. Follow the installation instructions above for `Setting Up Your System Environment`_
    #. Install IPython.  For a manual install, I recommend downloading the tarball, not the egg file. 
       Unzip the tar.gz and put the sub-directory named IPython somewhere on your ``PYTHONPATH``,
       or just put it directly into your python site-packages directory
    #. Open a terminal and run::
    
        chmod 777 `which ipymel`
        
    #. then run::
    
        ipymel


Windows
-------

    #. Follow the installation instructions above for `Setting Up Your System Environment`_
    #. Install python for windows, if you have not already.
    #. Install `IPython <http://ipython.scipy.org/dist>`_ using their windows installer.  The installer will most likely not find the maya python install, 
       so install IPython to your system Python instead (from step 1).
    #. Install pyreadline for windows, also from the IPython website
    #. Copy the IPython directory, pyreadline directory, and all the pyreadline.* files from your system site-packages directory 
       ( ex. ``C:\Python25\Lib\site-packages`` ) to your Maya site-packages directory ( ex. ``C:\Program Files\Autodesk\Maya2008\Python\lib\site-packages`` ). 
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


---------------------------------------
userSetup files
---------------------------------------


Next, to avoid having to import pymel every time you startup, you can create a userSetup.mel
file, place it in your Maya scipts directory and add this line::

    python("from pymel import *");

Alternately, you can create a userSetup.py file and add the line::

    from pymel import *

---------------------------------------
Script Editor
---------------------------------------
PyMEL includes a replacement for the script editor window that provides the option to translate all mel history into python. 
Currently this feature is beta and works only in versions beginning with Maya 8.5 SP1.

The script editor is comprised of two files located in the pymel/tools/scriptEditor directory: scriptEditorPanel.mel and pymelScrollFieldReporter.py.  

    #. Place the mel file into your scripts directory, and the python file into your Maya plugins directory. 
    #. Open Maya, go-to **Window** --> **Settings/Preferences** --> **Plug-in Manager** and load pymelScrollFieldReporter.  Be sure to also check "Auto Load" for this plugin. 
    #. Next, open the Script Editor and go to **History** --> **History Output** --> **Convert Mel to Python**. Now all output will be reported in python, regardless of whether the input is mel or python.


=======================================
    Standalone Maya Python
=======================================

To use maya functions in an external python interpreter, maya provides a handy executable called mayapy.  You can find it in the maya bin 
directory.  PyMEL ensures that using python outside of Maya is as close as possible to python inside Maya.  When PyMEL detects that it is being imported in a standalone
interpreter it performs these operations:

    #. initializes maya.standalone
    #. parses your Maya.env and adds variables to your environment
    #. sources Autodesk's initialization MEL scripts
    #. sources user preferences
    #. sources userSetup.mel

Because of these improvements, working in this standalone environment 
is nearly identical to working in interactive mode, except of course you can't create windows.  However, there are two caveats
that you must be aware of.  

    - scriptJobs do not work: use callbacks derived from `api.MMessage` instead
    - maya.cmds does not work inside userSetup.py (and thus any function in PyMEL that relies on maya.cmds)

The second one might seem a little tricky, but we've already come up with the solution: a utility function called `pymel.mayahook.executeDeferred`.
Jump to the docs for the function for more information on how to use it.




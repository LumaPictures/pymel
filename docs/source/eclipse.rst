
==================================================
Seting Up PyMEL Autocompletion in Eclipse
==================================================

The methodology for setting up auto-completion has been dramatically simplified with this release.  We now include "stub" files which can be used with almost any IDE to provide code completion.  These stub files comprise "dummy" versions of the pymel and maya packages: they contain all the function and class definitions along with their documentation strings, but do not contain any functional code.  This method (first brought to my attention by Ron Bublitz) has many advantages over using the "real" pymel package for completion:

    1. easier to setup
    2. faster and more reliable
    3. completes ui commands
    4. completes maya.cmds and maya.OpenMaya

The only disadvantage that has come to my attention is that IDE tools that reveal the source of a function will direct you to the stub packages, which contain no real code and therefore won't be particularly helpful. However, this is really only a concern for those who are brave enough to delve into pymel code.
 
--------------------------------------------------
Before You Begin
--------------------------------------------------

    * `Download <http://www.eclipse.org/downloads/>`_ and install the Eclipse Classic SDK.
    * Use Eclipse's **Software Update** window (under help) to install `PyDev <http://pydev.org/download.html>`_

These instructions are updated for Pydev 1.4.6, and should work on either Eclipse 3.4.x or 3.5.x

.. note:: If you checked out PyMEL from our git repo then you will need to generate the stubs first.

    To generate stubs:

        1. be sure that pymel is on the path by following the :ref:`install_manual` method.
        2. open a Maya GUI and run the following in a python tab of the script editor::
    
            import maintenance.stubs
            maintenance.stubs.pymelstubs()
    

--------------------------------------------------
Adding The Maya Python Interpreter
--------------------------------------------------

.. note:: with the introduction of the new completion stubs, it is no longer necessary to use mayapy as your interpreter -- any python interpreter will do. However, it's still a good idea to use Maya's interpreter to ensure that the site-packages within it are the same as when you are using Maya.


1.  Open the Eclipse preferences window.

    ============================================== ==============================================
    Windows                                        OSX
    ============================================== ==============================================
    under the **Window** menu:                         under the **Eclipse** menu:
    
    .. image:: images/pymel_eclipse_win_101.png    .. image:: images/pymel_eclipse_osx_101.png
    ============================================== ==============================================

        
2.  In the left pane, drop down to **Pydev > Interpreter-Python**
3.  Click the **New..** button at the top right of the **Python Interpreters** preferences window
4.  In the window that comes up give your interpreter a name (such as maya2009-osx). 
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

5.  Once you choose the "mayapy" binary, you'll get this window:

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
    
    
    On windows: add a check beside ``python25.zip``
    
    then press "OK"
    
5.  From the list, select the one path that ends with ``site-packages`` and click the "remove" button. Remember this path because we are going to re-add it later.

6.  If you installed PyMEL using the :ref:`install_setuptools` method: you'll see the pymel "egg" in the list of automatically detected site packages. **Remove the pymel egg** 
    
7.  Click on the "New Folder" button.  In the browser that pops up, navigate to the directory where you extracted the pymel zip file.  Under it, there is a folder called ``extras``, under that a folder called ``completion``, and then finally one called ``py``.  Choose the ``py`` folder and press "OK".

8.  Click the "New Folder" button again, and add the ``site-packages`` directory you removed earlier. We did this in order to ensure that the stub maya package is found before the real maya package. When you're done, the main ``site-packages`` directory should be somewhere *below* the ``extras/completion/py`` folder you just added.
    

--------------------------------------------------
Testing That It Worked
--------------------------------------------------

1.  Restart Eclipse
2.  Create a new file from within eclipse ( **File / New / File** ) named foo.py or whatever you want ( just make sure to include the .py )
3.  Add the following line::
    
        import pymel.core as pm

4.  Save the file. Sometimes this helps force pydev to begin performing completion
5.  Now type::

        pm.bin
        
    you should get ``bindSkin()`` as a completion. 

    .. image:: images/pymel_eclipse_osx_404.png
        :height: 493
        :width: 816
            
.. note::
    
    If you like to import everything from pymel, aka ``from pymel.core import *``, then you should open the Eclipse preferences, go to **Pydev > Editor > Code Completion**, and enable **Autocomplete on all letter chars and '_'**

--------------------------------------------------  
Troubleshooting
--------------------------------------------------
    
If you're still not getting completion:

    * Go to Eclipse preferences under **Pydev > Editor > Code Completion** and increase **Timeout to connect to shell** to 30 seconds or more.
    * Restart Eclipse and retry steps 3-5 above
    * Open a log view (**Window / Show View / Error Log**) and if you see any suspicious errors, post for help at the `Pydev suport forum <https://sourceforge.net/forum/forum.php?forum_id=293649>`_



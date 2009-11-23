.. currentmodule:: pymel

=======================================
What's New in Version 1.0.0
=======================================

----------------------
New Package Layout
----------------------

One of the tenets of PyMEL's design is that it should add object-oriented programming while still being easy for a novice to use.  One way that PyMEL attempts to keeps things simple is by providing access to all  of its sub-modules with a single top-level import. in the years since this design was first implemented, we've come to realize that this has certain ugly drawbacks.  The primary disadvantage is efficiency: importing all sub-modules means that parts of PyMEL that may not be explicitly required by the task at hand are still initialized, which takes time.  This problem is particularly pronounced in batch mode, where importing ``pymel`` triggers maya's full startup sequence, which, though often very useful, can be a nuisance if one only requires ``pymel.api`` or ``pymel.util``, which need no initialization.  Between the untangling of the automatic imports and several additional optimizations -- including compressed caches, and lazy loading of classes and docstrings -- we've reduced PyMEL's import time from 4 to 2 seconds.

Sub-Packages
============

PyMEL 1.0 retains the same overall package layout of 0.9, which provides a very clear dependency chain, however, in the current version, the user must explicitly import the sub-package they wish to use.  The sub-packages are:
    
    - `pymel.util`: independent of Maya
    - `pymel.api`: OpenMaya classes; requires maya, but does not require initialization of ``maya.standalone``
    - `pymel.internal`: (formally ``mayahook``) the machinery required to fuse ``maya.OpenMaya`` and ``maya.cmds`` into `pymel.core`
    - `pymel.core`: the primary sub-package; importing this module initializes maya.standalone in batch mode


Upgrading
=========

To keep things simple and to provide an easy upgrade path, PyMEL 1.0 adds a new module, ``pymel.all``, which imports all sub-modules in exactly the same way that the primary ``pymel`` module does in previous versions.  PyMEL also includes a new tool, `pymel.tools.upgradeScripts`, which will find and upgrade existing pymel scripts, converting all imports of ``pymel`` into imports of ``pymel.all``.  Additionally, PyMEL 0.9.3 will be forward compatible with 1.0, meaning it will also provide a ``pymel.all`` module so that "upgraded" code is interoperable between versions.

We don't take breaking backward compatibility lightly, but we feel strongly that these changes need to be made to ensure the long-term health of the package, and now is the best time to make them, before PyMEL's rapidly growing user-base gets any larger.

----------------------
MEL GUI Creation
----------------------
 
Layout Class
============


Streamlined GUI Creation
========================

Anyone who has coded GUIs in Maya using both MEL and python will tell you that if there is one thing they miss about MEL (and only one thing), it is the use of indentation to organize layout hierarchy. this is not possible in python because tabs are a syntactical element, indicating code blocks. In this release, PyMEL harnesses python's ``with`` statement, which not only allows indentation during GUI creation, it also streamlines the process.

Here is a comparison of the `uiTemplate` example from the Maya docs.

First, the original::

    import maya.cmds as cmds

    if cmds.uiTemplate( 'ExampleTemplate', exists=True ):
    	cmds.deleteUI( 'ExampleTemplate', uiTemplate=True )

    cmds.uiTemplate( 'ExampleTemplate' )

    cmds.button( defineTemplate='ExampleTemplate', width=100, height=40, align='left' )
    cmds.frameLayout( defineTemplate='ExampleTemplate', borderVisible=True, labelVisible=False )

    window = cmds.window()
    cmds.setUITemplate( 'ExampleTemplate', pushTemplate=True )
    cmds.columnLayout( rowSpacing=5 )

    cmds.frameLayout()
    cmds.columnLayout()
    cmds.button( label='One' )
    cmds.button( label='Two' )
    cmds.button( label='Three' )
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.frameLayout()
    cmds.columnLayout()
    cmds.button( label='Red' )
    cmds.button( label='Green' )
    cmds.button( label='Blue' )
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setUITemplate( popTemplate=True )

    cmds.showWindow( window )


Now, with PyMEL::

    from pymel.core import *
    
    template = uiTemplate( 'ExampleTemplate', force=True )
    
    template.define( button, width=100, height=40, align='left' )
    template.define( frameLayout, borderVisible=True, labelVisible=False )
    
    with window():
        with template:
            with columnLayout( rowSpacing=5 ):
                with frameLayout():
                    with columnLayout():
                        button( label='One' )
                        button( label='Two' )
                        button( label='Three' )
                
                with frameLayout():
                    with columnLayout():
                        button( label='Red' )
                        button( label='Green' )
                        button( label='Blue' )


Python's ``with`` statement was added in version 2.5.  It's purpose is to provide automatic "enter" and "exit" functions for class instances that are designed to support it.  This is perfect for MEL GUI creation: when we "enter" the ``with`` block using a PyMEL layout class, the layout sets itself to the active default parent, and when the code block ends, it restores the default parent to it's own parent. There is now almost never the need to call `setParent`.  As you can see in the example, the ``with`` statement also works with windows and templates:  windows call ``setParent`` and ``showWindow``, and templates are automatically "pushed" and "popped".



---------------------------
Components
---------------------------

all component types supported

---------------------------
Tighter Maya Integration
---------------------------

 - safe to use pymel inside userSetup.py in python standalone
 - fixes bug where certain commands don't return a result the first time they are called
 - shared root logger with status-line error and warning colorization

---------------------------
IDE Autocompletion
---------------------------

PyMEL Auto-completion in your favorite IDE -- such as Eclipse, Wing, and Komodo -- is now fast, reliable, and easy to setup. This is accomplished by providing pre-baked ``maya`` and ``pymel`` "stub" packages, which contain all of the classes and functions of the originals, stripped down to only definitions and documentation strings.  Add the path to these packages to your IDE ``PYTHONPATH`` and you're ready to go.


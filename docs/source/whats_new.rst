.. currentmodule:: pymel

=======================================
What's New in Version 1.0.0
=======================================

----------------------
New Package Layout
----------------------

PyMEL 1.0 introduces a very big backward incompatibility: importing ``pymel`` no longer imports sub-packages, meaning ``pymel`` is strictly an entry point for its sub-modules.  The user must now explicitly import the sub-modules they wish to use. ``pymel.core`` remains the primary module and importing it in batch mode triggers Maya's full startup sequence, just as importing the top-level ``pymel`` module did in previous versions.

Sub-Modules with their own namespace
====================================

    - `pymel.util`: independent of Maya
    - `pymel.api`: OpenMaya classes; requires maya, but does not require initialization of ``maya.standalone``
    - `pymel.internal`: (formally ``mayahook``) the machinery required to fuse ``maya.OpenMaya`` and ``maya.cmds`` into `pymel.core`
    - `pymel.core`: the primary sub-package; importing this module initializes maya.standalone in batch mode
    - `pymel.core.nodetypes`: contains all node classes, including custom nodes. also available as ``pymel.core.nt``
    - `pymel.core.uitypes`: contains all UI classes. also available as ``pymel.core.ui``
    - `pymel.core.datatypes`: contains all data classes. also available as ``pymel.core.dt``
    - `pymel.versions`: 
    - `pymel.mayautils`:


But Why?!
=========


One of the tenets of PyMEL's design is that it should add object-oriented programming while still being easy for a novice to use.  One way that we tried to accomplish this was by providing access to all of its sub-modules with a single top-level import. However, in the years since this design was first implemented, we've come to realize that this has certain ugly drawbacks.  The new layout has several advantages:

1. load time:  our new layout uses lazy loading for `pymel.core.uitypes` and `pymel.core.nodetypes`, which delays the creation of classes and methods until they are accessed.  This lazy loading dramatically speeds up PyMEL's load time, but it only works if the classes that are being lazily loaded stay in their own namespace.  For example, if you do a ``from pymel.core.nodetypes import *``, this forces every class within that module to be loaded.

2. API segregation: `pymel.api` will grow into a robust set of utilities for API development. under the new design, importing `pymel.api` has very little overhead and will not import any core commands, which could be dangerous to use in the context of a plugin.

3. util accessibility:  `pymel.util` contains functions and classes that are not Maya-dependent or even Maya-related so they are useful in many contexts. However, in the old layout you could not import ``pymel.util`` from a command-line script without initializing all of Maya. Similarly, there are two new modules -- `pymel.versions` and `pymel.mayautils` -- which can be used in batch mode without initializing Maya to do things like find user directories, determine what version of Maya the current mayapy corresponds to, etc, then make some decisions based on this info *before* `pymel.core` is imported and all of Maya is initialized.

4. namespace safety: node classes have been moved into their own namespace ``pymel.core.nodetypes``.  Without a separate namespace for nodes, user created nodes and commands have the potential to clash with each other, preventing one or the other from being accessible (we're not being paranoid here, we've already had a user approach us with this exact problem).

Upgrading
=========

To keep things simple and to provide an easy upgrade path, PyMEL 1.0 adds a new module, ``pymel.all``, which imports all sub-modules in exactly the same way that the primary ``pymel`` module does in previous versions.  PyMEL also includes a new tool, `pymel.tools.upgradeScripts`, which will find and upgrade existing PyMEL scripts, converting all imports of ``pymel`` into imports of ``pymel.all``.  Additionally, PyMEL 0.9.3 is forward compatible with 1.0, meaning it will also provide a ``pymel.all`` module so that "upgraded" code is interoperable between versions.

We don't take breaking backward compatibility lightly, but we feel strongly that these changes need to be made to ensure the long-term health of the package, and now is the best time to make them, before PyMEL's rapidly growing user-base gets any larger.

.. note:: keep in mind that importing ``pymel.all`` negates all of the load time improvements that have been made with 1.0.  Importing ``pymel.core`` is now the preferred method.

----------------------
MEL GUI Creation
----------------------


Streamlined GUI Creation
========================

Anyone who has coded GUIs in Maya using both MEL and python will tell you that if there is one thing they miss about MEL (and only one thing), it is the use of indentation to organize layout hierarchy. this is not possible in python because tabs are a syntactical element, indicating code blocks. In this release, PyMEL harnesses python's ``with`` statement to use indentation to streamlines the process of GUI creation.

Here is a comparison of the `uiTemplate` example from the Maya docs.

First, using ``maya.cmds``::

    import maya.cmds as cmds

    if cmds.uiTemplate( 'ExampleTemplate', exists=True ):
        cmds.deleteUI( 'ExampleTemplate', uiTemplate=True )
    cmds.uiTemplate( 'ExampleTemplate' )
    cmds.button( defineTemplate='ExampleTemplate', width=100, height=40, align='left' )
    cmds.frameLayout( defineTemplate='ExampleTemplate', borderVisible=True, labelVisible=False )

    window = cmds.window(menuBar=True,menuBarVisible=True)

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
    cmds.optionMenu()
    menuItem( label='Red' )
    menuItem( label='Green' )
    menuItem( label='Blue' )
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setUITemplate( popTemplate=True )

    cmds.showWindow( window )

    menu()
    menuItem(label='One')
    menuItem(label='Two')
    menuItem(label='Sub', subMenu=True)
    menuItem(label='A')
    menuItem(label='B')
    setParent('..', menu=1)
    menuItem(label='Three')


Now, with PyMEL::

    from __future__ import with_statement # this line is only needed for 2008 and 2009
    from pymel.core import *

    template = uiTemplate( 'ExampleTemplate', force=True )
    template.define( button, width=100, height=40, align='left' )
    template.define( frameLayout, borderVisible=True, labelVisible=False )

    with window(menuBar=True,menuBarVisible=True) as win:
        # start the template block
        with template:
            with columnLayout( rowSpacing=5 ):
                with frameLayout():
                    with columnLayout():
                        button( label='One' )
                        button( label='Two' )
                        button( label='Three' )
                with frameLayout():
                    with optionMenu():
                        menuItem( label='Red' )
                        menuItem( label='Green' )
                        menuItem( label='Blue' )
    # add a menu to an existing window
    with win:
        with menu():
            menuItem(label='One')
            menuItem(label='Two')
            with subMenuItem(label='Sub'):
                menuItem(label='A')
                menuItem(label='B')
            menuItem(label='Three')


Python's ``with`` statement was added in version 2.5 (Maya 2008 and 2009).  It's purpose is to provide automatic "enter" and "exit" functions for class instances that are designed to support it.  This is perfect for MEL GUI creation: for example, when we enter the ``with`` block using a PyMEL `ui.Layout` class or a command that creates one, the layout object sets itself to the active default parent, and when the code block ends, it restores the default parent to it's own parent. There is now little need to ever call `setParent`.  As you can see in the example, the ``with`` statement also works with windows, menus, and templates:  windows call ``setParent`` and ``showWindow``, and templates are automatically "pushed" and "popped".

Layout Class
============

Support for python's 'with' statement is made possible by the new `Layout` class. Layouts also provide a number of methods for walking UI hierarchies. Continuing from our previous example::

    # hide all children of the window
    for ctrl in win.walkChildren():
        print ctrl.setVisible(False)

---------------------------
Components
---------------------------

all component types supported

--------------------------- 
Tighter Maya Integration
---------------------------

    - safe to use PyMEL inside userSetup.py in python standalone
    - fixes bug where certain commands don't return a result the first time they are called
    - shared root logger with status-line error and warning colorization

---------------------------
IDE Autocompletion
---------------------------

PyMEL Auto-completion in your favorite IDE -- such as Eclipse, Wing, and Komodo -- is now fast, reliable, and easy to setup. This is accomplished by providing pre-baked ``maya`` and ``pymel`` "stub" packages, which contain all of the classes and functions of the originals, stripped down to only definitions and documentation strings.  Add the path to these packages to your IDE ``PYTHONPATH`` and you're ready to go.


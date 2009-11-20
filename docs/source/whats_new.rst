.. currentmodule:: pymel

=======================================
What's New in Version 0.9
=======================================

----------------------
New Package Layout
----------------------

one of the tenets of pymel's design is that it should add object-oriented programming while still being easy for a novice to use.  one way that pymel attempts to keeps things simple is by providing access to all  of its sub-modules with a single top-level import. in the years since this design was first implemented, we've come to realize that this has certain ugly drawbacks.  The primary disadvantage is efficiency: importing all sub-modules means that parts of pymel that may not be explicitly required by the task at hand are still initialized, which takes time.  This problem is particularly pronounced in batch mode, where importing pymel triggers maya's full startup sequence, which, though often very useful, can be a nuisance if one only requires pymel.api or pymel.util, which need no initialization.  Between the untangling of the automatic imports and several additional optimizations -- including compressed caches, and lazy loading of classes and docstrings -- we've reduced pymel's import time from 4 to 2 seconds.

Sub-Packages
============

pymel 1.0 retains the same overall package layout, which provides a very clear dependency chain, but the user must now explicitly import the sub-package they wish to use.  The sub-packages are:
    
    - pymel.util: independent of maya
    - pymel.api: OpenMaya classes; requires maya, but does not require initialization of maya.standalone
    - pymel.internal: (formally 'mayahook') the machinery required to fuse maya.OpenMaya and maya.cmds into pymel.core
    - pymel.core: the primary pymel sub-package; importing this module initializes maya.standalone in batch mode


Upgrading
=========

to keep things simple and to provide an easy upgrade path, pymel 1.0 adds a new module, pymel.all, which imports all modules in exactly the same way that the primary ``pymel`` module does in 0.9.  pymel also includes a new tool, ``pymel.tools.upgradeScripts``, which will find and upgrade existing pymel scripts, converting all imports of ``pymel`` into imports of ``pymel.all``.  Lastly, pymel 0.9.3 will be forward compatible with 1.0, meaning it will also provide a ``pymel.all`` module so that you can write code that is interoperable between versions, which should further ease your transition.

We don't take breaking backward compatibility lightly, but we feel strongly that these changes need to be made to ensure the long-term health of the package, and now is the best time to make them, before pymel's rapidly growing user-base gets any larger.

    
gui
    Layout class
    streamlined, indented gui creation

Anyone who has coded GUIs in Maya using both MEL and python will tell you that if there is one thing they miss about MEL (and only one thing), it is the use of indentation to organize layout hierarchy. this is not possible in python because tabs are a syntactical element, indicating code blocks. In this release, pymel harnesses python's ``with`` statement, which will not only allow indentation, but will also streamline GUI creation.


all component types supported

maya package
    safe to use pymel inside userSetup.py in python standalone
    fixes bug where certain commands don't return results on first call
    shared root logger with error and warning colorization



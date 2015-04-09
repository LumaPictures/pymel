.. currentmodule:: pymel

=============================================
For Developers
=============================================

---------------------------------------------
An Overview of PyMEL's Wrapping Mechanisms
---------------------------------------------

Parsed Caches and Maintained Constants
======================================

In order to fuse the many disparate parts of maya's python package into a cohesive whole PyMEL requires a great deal of data describing how each MEL command and API class works: the arguments they require, the results they return, and their relationships to each other.  Some of this data is parsed and cached, while other bits are manually maintained.

Below is a description of how each major cache is created.

MEL Commands
------------

1. gather MEL function data
    * parse data from MEL documentation
    * merge this with info from MEL ``help`` command
2. create a dictionary of MEL-commands to the maya nodes they create, query, and edit
3. create a dictionary of MEL-commands to the ui elements they create, query, and edit
4. run tests on node commands to gather additional information required to ensure values returned by queries are compatible with values required for edits
5. pickle this info into two separate caches: one used for auto-wraps and the other for doc strings.  the latter data can be lazily loaded on request since it is not required for the wrap itself.

Nodes and API Classes
---------------------

1. gather API class data
    * parse API docs
    * correct erroneous docs based on documentation
2. gather node hierarchy data
    * parse maya node hierarchy docs
    * determine MFn-to-maya-node mappings
    * determine apiType-to-maya-node mappings
3. pickle this info into two separate caches: one for auto-wraps and the other for doc strings

Bridge
------

A special control-panel GUI is used to manage a dictionary controlling how MEL and API interact to produce PyNode classes. It is known as the bridge. The bridge allows us to:

1. create manual overrides to correct input and output types
2. create mappings between MEL commands and API commands that perform the same task
3. specify whether MEL or API should be used to generate each PyMEL method
4. specify the name of the method that will be produced

Run Time Function and Class Factories
=====================================

When PyMEL is imported it uses the cached data to generate the wrapped functions and classes you've come to know and love. Here's how in a nutshell.

Functions
---------

Every command is wrapped in up to 3 stages.

1. Data Compatibility Wrap
~~~~~~~~~~~~~~~~~~~~~~~~~~

``pymel.internal.pmcmds`` wraps every function in ``maya.cmds`` such that any arguments that are passed to it are first converted into datatypes that ``maya.cmds`` will accept (string, int, float, or list/tuple thereof).  The way we do this is simple yet powerful:  if the argument has a ``__melobject__`` method, we evaluate it and use the result in place of the original value.  It is the responsibility of this method to return a "MEL-friendly" representation of the object's data.  For example, `core.PyNode.__melobject__` returns its object's name as a string, and `datatypes.Matrix.__melobject__` returns itself converted into a flat 16-item list.

2. Manual Wrap
~~~~~~~~~~~~~~

Optional manual wraps are created for cases that cannot be handled automatically or semi-automatically (below).  They can use the auto-wrapped function in ``pmcmds`` as a starting point

3. Automatic Wrap
~~~~~~~~~~~~~~~~~

Certain wraps are applied automatically based on information attained during parsing. If a manual wrap of the function is found, it is used as the starting point, otherwise the lower-level ``pmcmds`` wrap is used.

For each function:

1. add open-ended time ranges to appropriate flags:  (1,None), (1,), slice(1,None), "1:", etc
2. cast results to ``PyNode`` or ``PyUI`` if it is a node or UI command, correcting where determined necessary in tests
3. fix UI callbacks to return proper python objects instead of 'true', 'false', '1', '0', etc
4. perform simple wraps:  these are manually maintained, semi-automatic wraps of commands that are altered in standard and straightforward ways. For example, a command that should return a ``PyNode`` on a particular query is a wrap that can be handled easily through this mechanism.
5. add docstrings based on cached data


Classes
-------

1. manually create classes that need custom methods
2. add the appropriate ``__metaclass__`` attribute:  `internal.factories.MetaMayaNodeWrapper` or `internal.factories.MetaMayaUIWrapper`

for each node and UI type:

1. choose the appropriate metaclass
2. add methods:
    * use bridge to determine whether to use MEL or API
    * skip if it has already been manually added

---------------------------------------------
Contributing
---------------------------------------------

Getting Started with Git
========================

The PyMEL project hosts its code on github.

 1. Sign up for a `Github <http://github.com>`_ account
 2. Check out the `Github Guides <http://github.com/guides/home>`_ for instructions on how to setup git for your OS
 3. Download a GUI front-end: `SmartGit <http://www.syntevo.com/smartgit/index.html>`_ and `TortoiseGit <http://code.google.com/p/tortoisegit/>`_ are by far my favorites
 4. Make a fork of the main `PyMEL repository <http://github.com/LumaPictures/pymel>`_, and start hacking

To get maya to use the version of pymel you have just checked out, either manually add it to your PYTHONPATH environment variable, or cd into the directory, then run::

    PATH/TO/MAYA/INSTALL/bin/mayapy setup.py develop
 
When you "push" your changes up to Github, we'll be able to track them, give you feedback, and cherry-pick what we like. You, in turn, will be able to easily pull new changes from our repo into yours.

Running the Tests
=================

PyMEL has a suite of unit tests. You should write a test for every major addition or change that you make. To run the tests, you need 'nose', which is a discovery-based test runner, that builds on python's ``unittest`` module and makes writing running a lot of tests a lot easier.  Here's the easiest way to get nose.

On linux/osx::

    sudo mayapy setup.py easy_install nose

On windows::

    mayapy.exe setup.py easy_install nose

This assumes that you've properly setup your environment, which you should definitely know how to do before contributing to PyMEL.


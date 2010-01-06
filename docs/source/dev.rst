=============================================
For Developers: How PyMEL Works
=============================================

---------------------------------------------
An Overview of PyMEL's Wrapping Mechanisms
---------------------------------------------

Parsed Caches and Maintained Constants
======================================

In order to fuse the many disparate parts of maya's python package into a cohesive whole PyMEL requires a great deal of data describing how each MEL command and API class within Maya works: the arguments they require, the results they return, and their relationships to each other.  Some of this data is parsed and cached, while other bits are manually maintained.

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
6. create a dictionary of commands and flags that should be altered in known ways.  these "simple" wraps cannot be determined automatically, but need not be written by hand.  for example, a command that should return PyNodes on a particular query is a wrap that can be handled easily through this mechanism

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

A special control-panel GUI is used to create a dictionary controlling how MEL and API interact to produce PyNode classes. It is known as the bridge. The control panel allows us to edit the bridge to:

1. create manual overrides to correct input and output types
2. create mappings between MEL commands and API commands that perform the same task
3. specify whether MEL or API should be used to generate each PyMEL method
4. specify the name of the method that will be produced

Run Time Function and Class Factories
=====================================

When PyMEL is imported it uses the cached data to generate the wrapped functions and classes you've come to know and love. Here's how in a nutshell.

Functions
---------

for each function:
1. add open-ended time ranges to appropriate flags:  (1,None), (1,), slice(1,None), "1:", etc
2. cast results to PyNode or PyUI if it is a node or UI command, correcting where determined necessary in tests
3. fix UI callbacks to return proper python objects instead of 'true', 'false', '1', '0', etc
4. perform simple wraps (described above)
5. add docstrings


Classes
-------

1. manually create classes that need custom methods
2. add the appropriate ``__metaclass__`` attribute:  `internal.factories.MetaMayaNodeWrapper` or `internal.factories.MetaMayaUIWrapper`

for each node and UI type:
1. choose the appropriate metaclass
2. add methods:
	* use bridge to determine whether to use MEL or API
	* skip if it has already been manually added

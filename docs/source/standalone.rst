
=======================================
  Standalone Maya Python Interpreter
=======================================

Maya's standalone interpreter can be useful for both development and batch processing, as an alternative to ``maya -batch``.
To use maya functions in an external python interpreter, maya provides a handy executable called ``mayapy``, which you can find in the maya bin directory.  Before using ``maya.cmds`` in this interpreter, you must first initialize Maya::

	import maya.standalone
	maya.standalone.initialize(name='python')
	import maya.cmds as cmds

The problem with this is that it does not fully initialize Maya the way that it would be when using ``maya -batch`` or the Maya UI, and as a result, certain scripts and plugins will not be available.  This can lead to errors since many developers test their code in a Maya GUI session, assuming that ``mayapy`` will behave the same.

PyMEL ensures that using python within ``mayapy`` is as close as possible to using maya in batch mode.  When PyMEL detects that it is being imported in a standalone interpreter it performs these operations:

    #. initializes maya.standalone
    #. sources Autodesk's initialization MEL scripts
    #. sources user preferences
    #. sources userSetup.mel

Because of these improvements, working in this standalone environment is nearly identical to working in interactive mode, except of course you can't create windows.  

.. warning:: There is one caveat that you must be aware of: scriptJobs do not work: use callbacks derived from `api.MMessage` instead.

In order to use ``mayapy`` you must first properly :ref:`setup your system environment <install_system_env>`.

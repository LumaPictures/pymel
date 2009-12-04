
=======================================
  Standalone Maya Python Interpreter
=======================================

Maya's standalone interpreter can be useful for both development and batch processing, as an alternative to ``maya -batch``.
To use maya functions in an external python interpreter, maya provides a handy executable called ``mayapy``.  You can find it in the maya bin directory.  PyMEL ensures that using python outside of Maya is as close as possible to python inside Maya.  When PyMEL detects that it is being imported in a standalone interpreter it performs these operations:

    #. initializes maya.standalone
    #. sources Autodesk's initialization MEL scripts
    #. sources user preferences
    #. sources userSetup.mel

Because of these improvements, working in this standalone environment is nearly identical to working in interactive mode, except of course you can't create windows.  However, there is one caveat that you must be aware of: scriptJobs do not work: use callbacks derived from `api.MMessage` instead.

In order to use ``mayapy`` you must first properly :ref:`setup your system environment <install_system_env>`. 
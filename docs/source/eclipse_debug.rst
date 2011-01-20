
==================================================
Seting Up PyMEL Debugging in Eclipse
==================================================

(VERY rough instructions still - need to refine)

1. Set up a new interpreter like in `Seting Up PyMEL AutoCompletion in Eclipse`,
    but use new .pypredefs (TODO - add code to maintenance.stubs to make these),
    added under 'predefined' instead of python path; set the MAYA_LOCATION;
2. Set LD_LIBRARY_PATH env. var for interpreter to MAYA_LOCATION/lib (only
    hard-code maya location - ie, /usr/autodesk/maya2012-x64/lib)
3. Set up a python 'run' configuration, pointing to tests/eclipseDebug.py,
    and using our special pymel debugger interpreter
"""
This module is always imported during Maya's startup.  It is imported from
both the maya.app.startup.batch and maya.app.startup.gui scripts
"""

# We don't have to want to keep maintaining this module... ideally, we'd get
# autodesk to eventually incorporate our "siteSetup.py" change, or just
# drop support for it from pymel... but for now we have backwards compatibility
# to worry about, so... we first branch based on whether maya version is
# < 2014.59, when they changed where executeUserSetup() was run...

import maya.OpenMaya

if maya.OpenMaya.MGlobal.apiVersion() >= 201459:
    import types

    # On newer versions of maya, executeUserSetup() isn't run inside of
    # maya.app.startup.basic... and since that's the only part we really wish
    # to change, we can monkey-patch it...

    # FIRST, try to run the "real" maya.app.startup.basic...
    import maya.utils
    maya.utils.runOverriddenModule(__name__, lambda: None, globals())

    # ok, we've excuted the real module... now modify it!

    # first, we need to make a version of executeUserSetup() that instead
    # runs siteSetup.py...
    executeUserSetupOnly = executeUserSetup  # @UndefinedVariable

    # do this by copying executeUserSetup, except replace the constant
    # 'userSetup.py' with 'siteSetup.py'
    old_code = executeUserSetupOnly.func_code
    new_consts = tuple('siteSetup.py' if x == 'userSetup.py' else x
                       for x in old_code.co_consts)
    new_code = types.CodeType(old_code.co_argcount,
                              old_code.co_nlocals,
                              old_code.co_stacksize,
                              old_code.co_flags,
                              old_code.co_code,
                              new_consts,
                              old_code.co_names,
                              old_code.co_varnames,
                              old_code.co_filename,
                              'executeSiteSetup',
                              old_code.co_firstlineno,
                              old_code.co_lnotab,
                              old_code.co_freevars,
                              old_code.co_cellvars)
    executeSiteSetup = types.FunctionType(new_code,
                                          executeUserSetupOnly.func_globals,
                                          'executeSiteSetup',
                                          executeUserSetupOnly.func_defaults,
                                          executeUserSetupOnly.func_closure)

    # ok, now we have executeSiteSetup, make our "new" executeUserSetup

    def executeUserSetup():
        # need to run siteSetup first...
        executeSiteSetup()
        executeUserSetupOnly()

    # ...and we're done

else:
    # we have an older version of maya... well, we know this isn't going to
    # change, so just copy / paste the "old" alteration in here... get rid of
    # this once we don't need to support 2014...

    import atexit
    import os.path
    import sys
    import traceback
    import maya
    import maya.app
    import maya.app.commands
    from maya import cmds, utils

    def setupScriptPaths():
        """
        Add Maya-specific directories to sys.path
        """
        # Extra libraries
        #
        try:
            # Tkinter libraries are included in the zip, add that subfolder
            p = [p for p in sys.path if p.endswith('.zip')][0]
            sys.path.append(os.path.join(p, 'lib-tk'))
        except:
            pass

        # Per-version prefs scripts dir (eg .../maya8.5/prefs/scripts)
        #
        prefsDir = cmds.internalVar(userPrefDir=True)
        sys.path.append(os.path.join(prefsDir, 'scripts'))

        # Per-version scripts dir (eg .../maya8.5/scripts)
        #
        scriptDir = cmds.internalVar(userScriptDir=True)
        sys.path.append(os.path.dirname(scriptDir))

        # User application dir (eg .../maya/scripts)
        #
        appDir = cmds.internalVar(userAppDir=True)
        sys.path.append(os.path.join(appDir, 'scripts'))

    def executeSetup(filename):
        """
        Look for the given file name in the search path and execute it in the "__main__"
        namespace
        """
        try:
            for path in sys.path[:]:
                scriptPath = os.path.join(path, filename)
                if os.path.isfile(scriptPath):
                    import __main__
                    execfile(scriptPath, __main__.__dict__)
        except Exception, err:
            # err contains the stack of everything leading to execfile,
            # while sys.exc_info returns the stack of everything after execfile
            try:
                # extract the stack trace for the current exception
                etype, value, tb = sys.exc_info()
                tbStack = traceback.extract_tb(tb)
            finally:
                del tb  # see warning in sys.exc_type docs for why this is deleted here
            sys.stderr.write("Failed to execute %s\n" % filename)
            sys.stderr.write("Traceback (most recent call last):\n")
            # format the traceback, excluding our current level
            result = traceback.format_list(tbStack[1:]) + traceback.format_exception_only(etype, value)
            sys.stderr.write(''.join(result))

    def executeUserSetup():
        executeSetup('userSetup.py')

    def executeSiteSetup():
        executeSetup('siteSetup.py')

    # Set up sys.path to include Maya-specific user script directories.
    setupScriptPaths()

    # Set up string table instance for application
    maya.stringTable = utils.StringTable()

    # Set up auto-load stubs for Maya commands implemented in libraries which are not yet loaded
    maya.app.commands.processCommandList()

    # Set up the maya logger before userSetup.py runs, so that any custom scripts that
    # use the logger will have it available
    utils.shellLogHandler()

    if not os.environ.has_key('MAYA_SKIP_USERSETUP_PY'):
        # Run the user's userSetup.py if it exists
        executeSiteSetup()
        executeUserSetup()

    # Register code to be run on exit
    atexit.register(maya.app.finalize)
    # Copyright (C) 1997-2013 Autodesk, Inc., and/or its licensors.
    # All rights reserved.
    #
    # The coded instructions, statements, computer programs, and/or related
    # material (collectively the "Data") in these files contain unpublished
    # information proprietary to Autodesk, Inc. ("Autodesk") and/or its licensors,
    # which is protected by U.S. and Canadian federal copyright law and by
    # international treaties.
    #
    # The Data is provided for use exclusively by You. You have the right to use,
    # modify, and incorporate this Data into other products for purposes authorized
    # by the Autodesk software license agreement, without fee.
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. AUTODESK
    # DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTIES
    # INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF NON-INFRINGEMENT,
    # MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR ARISING FROM A COURSE
    # OF DEALING, USAGE, OR TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS
    # LICENSORS BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
    # DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK AND/OR ITS
    # LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY OR PROBABILITY OF SUCH DAMAGES.

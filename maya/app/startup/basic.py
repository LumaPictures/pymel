"""
This module is always imported during Maya's startup.  It is imported from
both the maya.app.startup.batch and maya.app.startup.gui scripts
"""

# We don't have to want to keep maintaining this module... ideally, we'd get
# autodesk to eventually incorporate our "siteSetup.py" change, or just
# drop support for it from pymel... but for now we have backwards compatibility
# to worry about, so...

import maya.OpenMaya

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
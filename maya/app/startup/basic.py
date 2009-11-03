
#    module: maya.app.startup.basic
#
#    This module is always imported during Maya's startup.  It is imported from
#    both the maya.app.startup.batch and maya.app.startup.gui scripts
#

import maya, maya.app, maya.app.commands, maya.utils, maya.app.startup.common
import os, atexit
 
# Set up sys.path to include Maya-specific user script directories.
maya.app.startup.common.setupScriptPaths()

# Set up auto-load stubs for Maya commands implemented in libraries which are not yet loaded
maya.app.commands.processCommandList()

# Set up string table instance for application 
# This must be done before executing userSetup in case something in maya.app is imported there
maya.stringTable = maya.utils.StringTable()

# Set up the maya logger before userSetup.py runs, so that any custom scripts that
# use the logger will have it available
maya.utils.shellLogger()

if not os.environ.has_key('MAYA_SKIP_USERSETUP_PY'):
    # Run the user's userSetup.py if it exists
    maya.app.startup.common.executeUserSetup()

# Register code to be run on exit
atexit.register( maya.app.finalize )


# Copyright (C) 1997-2006 Autodesk, Inc., and/or its licensors.
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


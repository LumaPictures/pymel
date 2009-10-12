
# module: maya.app.gui
#
# This module is imported during the startup of Maya in GUI mode.
#
print "maya.app.startup.gui"
import os
alternate = os.environ.get('MAYA_PY_INIT_GUI')
if alternate:
    try:
        __import__(alternate)
    except Exception, err:
        print "Failed importing custom startup module %s (using default): %s" % (alternate, err)
        alternate = None

if not alternate:
    import maya.app.startup.basic
    maya.app.startup.basic.run()
    
    import maya.app.baseUI, maya.utils, sys
    
    # Replace sys.stdin with a GUI version that will request input from the user
    sys.stdin = maya.app.baseUI.StandardInput()
    
    # Replace sys.stdout and sys.stderr with versions that can output to Maya's
    # GUI
    sys.stdout = maya.utils.Output()
    sys.stderr = maya.utils.Output( error=1 )
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


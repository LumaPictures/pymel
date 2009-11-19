"""functions related to modeling"""

import pymel.mayahook.factories as _factories
import pymel.mayahook.pmcmds as cmds
import general as _general

def pointPosition( *args, **kwargs ):
    return _general.datatypes.Point( cmds.pointPosition(*args, **kwargs) )

_factories.createFunctions( __name__, _general.PyNode )
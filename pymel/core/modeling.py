"""functions related to modeling"""

import factories as _factories
import general as _general
import pmcmds as cmds

def pointPosition( *args, **kwargs ):
    return _general.datatypes.Point( cmds.pointPosition(*args, **kwargs) )

_factories.createFunctions( __name__, _general.PyNode )
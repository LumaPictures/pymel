"""functions related to modeling"""

import factories as _factories
import general
import pmcmds as cmds

def pointPosition( *args, **kwargs ):
    return general.MPoint( cmds.pointPosition(*args, **kwargs) )

_factories.createFunctions( __name__, general.PyNode )
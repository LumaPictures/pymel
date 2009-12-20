"""functions related to modeling"""

import pymel.internal.factories as _factories
import pymel.internal.pmcmds as cmds
import general as _general

def pointPosition( *args, **kwargs ):
    return _general.datatypes.Point( cmds.pointPosition(*args, **kwargs) )

def curve( *args, **kwargs ):
    """
Maya Bug Fix:
  - name parameter only applied to transform. now applies to shape as well
    """
    # curve returns a transform
    name = kwargs.pop('name', kwargs.pop('n', None))
    res = _general.PyNode( cmds.curve(*args, **kwargs) )
    if name:
        res.rename(name)
    return res

def surface( *args, **kwargs ):
    """
Maya Bug Fix:
  - name parameter only applied to transform. now applies to shape as well
    """
    # surface returns a shape
    name = kwargs.pop('name', kwargs.pop('n', None))
    res = _general.PyNode( cmds.surface(*args, **kwargs) )
    if name:
        res.getParent().rename(name)
    return res

_factories.createFunctions( __name__, _general.PyNode )
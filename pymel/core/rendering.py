"""Functions related to rendering"""

import pymel.util as _util
import pymel.internal.factories as _factories
import general as _general
import language as _language
import pymel.internal.pmcmds as cmds



def shadingNode( *args, **kwargs):
    res = cmds.shadingNode( *args, **kwargs )
    if res is not None:
        return _general.PyNode( res )

def createSurfaceShader( shadertype, name=None ):
    """
    create a shader and shading group


    """
    classification = _general.getClassification( shadertype )
    #print classification

    newShader = None
    import nodetypes
    #if 'shader/surface' in classification:
    if 'rendernode/mentalray/material' in classification:
        newShader = nodetypes.DependNode(_language.mel.mrCreateCustomNode( "-asShader", "", shadertype))
    else:
        newShader = nodetypes.DependNode(_language.mel.renderCreateNode( "-asShader", "surfaceShader", shadertype, "", 0, 0, 0, 1, 0, ""))
    #else:
    #    raise TypeError, "%s is not a valid surface shader type. shader must be classified as 'shader/surface'" % shadertype
    sg = newShader.shadingGroups()[0]
    if name:
        newShader = newShader.rename(name)
        sg = sg.rename( name + 'SG')
    return newShader, sg

def lsThroughFilter( *args, **kwargs):
    """
Modifications:
  - returns an empty list when the result is None
  - returns wrapped classes
    """
    return map(_general.PyNode, _util.listForNone(cmds.lsThroughFilter(*args, **kwargs)))

def pointLight(*args,**kwargs):
    """
Maya Bug Fix:
  - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.pointLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.pointLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return _general.PyNode( cmds.listRelatives( tmp, shapes=1)[0] )

    return _general.PyNode( cmds.pointLight(*args, **kwargs)  )

def spotLight(*args,**kwargs):
    """
Maya Bug Fix:
  - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.spotLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.spotLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return _general.PyNode( cmds.listRelatives( tmp, shapes=1)[0])

    return _general.PyNode( cmds.spotLight(*args, **kwargs)  )

def directionalLight(*args,**kwargs):
    """
Maya Bug Fix:
  - name flag was ignored
    """

    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.directionalLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.directionalLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return _general.PyNode( cmds.listRelatives( tmp, shapes=1)[0] )

    return _general.PyNode( cmds.directionalLight(*args, **kwargs)  )

def ambientLight(*args,**kwargs):
    """
Maya Bug Fix:
  - name flag was ignored
    """
    if kwargs.get('query', kwargs.get('q', False)) or kwargs.get('edit', kwargs.get('e', False)):
        return cmds.ambientLight(*args, **kwargs)

    else:
        name = kwargs.pop('name', kwargs.pop('n', False ) )
        if name:
            tmp = cmds.ambientLight(*args, **kwargs)
            tmp = cmds.rename( cmds.listRelatives( tmp, parent=1)[0], name)
            return _general.PyNode( cmds.listRelatives( tmp, shapes=1)[0] )

    return _general.PyNode( cmds.ambientLight(*args, **kwargs)  )

#def createRenderLayer(*args, **kwargs):
#    return _general.PyNode( cmds.createRenderLayer(*args, **kwargs) )
#
#def createDisplayLayer(*args, **kwargs):
#    return _general.PyNode( cmds.createDisplayLayer(*args, **kwargs) )

_factories.createFunctions( __name__, _general.PyNode )

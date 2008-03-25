
import pymel.core.general
import pymel.util.factories
try:
    import maya.cmds as cmds
    import maya.mel as mm
except ImportError:
    pass


def shadingNode( *args, **kwargs):
    return pymel.core.general.PyNode( cmds.shadingNode( *args, **kwargs ) )

def createSurfaceShader( shadertype, name=None ):
    classification = getClassification( shadertype )
    #print classification
    
    newShader = None
    #if 'shader/surface' in classification:        
    if 'rendernode/mentalray/material' in classification:
        newShader = pymel.core.general.DependNode(mel.mrCreateCustomNode( "-asShader", "", shadertype))
    else:
        newShader = pymel.core.general.DependNode(mel.renderCreateNode( "-asShader", "surfaceShader", shadertype, "", 0, 0, 0, 1, 0, ""))
    #else:
    #    raise TypeError, "%s is not a valid surface shader type. shader must be classified as 'shader/surface'" % shadertype
    sg = newShader.shadingGroups()[0]
    if name:
        newShader = newShader.rename(name)        
        sg = sg.rename( name + 'SG')
    return newShader, sg



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
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'pointLight' )
    
    return PyNode( cmds.pointLight(*args, **kwargs), 'pointLight'  )

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
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'spotLight' )
    
    return PyNode( cmds.spotLight(*args, **kwargs), 'spotLight'  )

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
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'directionalLight' )
    
    return PyNode( cmds.directionalLight(*args, **kwargs), 'directionalLight'  )

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
            return PyNode( cmds.listRelatives( tmp, shapes=1)[0], 'ambientLight' )
    
    return PyNode( cmds.ambientLight(*args, **kwargs), 'ambientLight'  )

pymel.util.factories.createFunctions( __name__ )

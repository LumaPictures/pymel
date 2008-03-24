
import pymel.core.node

def shadingNode( *args, **kwargs):
    return pymel.core.node.PyNode( cmds.shadingNode( *args, **kwargs ) )

def createSurfaceShader( shadertype, name=None ):
    classification = getClassification( shadertype )
    #print classification
    
    newShader = None
    #if 'shader/surface' in classification:        
    if 'rendernode/mentalray/material' in classification:
        newShader = pymel.core.node.DependNode(mel.mrCreateCustomNode( "-asShader", "", shadertype))
    else:
        newShader = pymel.core.node.DependNode(mel.renderCreateNode( "-asShader", "surfaceShader", shadertype, "", 0, 0, 0, 1, 0, ""))
    #else:
    #    raise TypeError, "%s is not a valid surface shader type. shader must be classified as 'shader/surface'" % shadertype
    sg = newShader.shadingGroups()[0]
    if name:
        newShader = newShader.rename(name)        
        sg = sg.rename( name + 'SG')
    return newShader, sg

import pymel.util.factories
pymel.util.factories.createFunctions( __name__, None )

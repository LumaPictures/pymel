
import pymel.util.factories

try:
    import maya.cmds as cmds
    import maya.mel as mm
except ImportError:
    pass
#import pymel.core.general


def joint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, limitSwitch*, stiffness*, and angle* flags returned lists of values instead 
        of single values. Values are now properly unpacked
    """
    
    res = cmds.joint(*args, **kwargs)
    
    #if kwargs.pop('query',False) or kwargs.pop('q',False):

    if kwargs.get('query', kwargs.get( 'q', False)):
        args = [
        'limitSwitchX', 'lsx',
        'limitSwitchY', 'lsy',
        'limitSwitchZ', 'lsz',
        'stiffnessX', 'stx',
        'stiffnessY', 'sty',
        'stiffnessZ', 'stz',
        'angleX', 'ax',
        'angleY', 'ay',
        'angleZ', 'az'
        ]
        if filter( lambda x: x in args, kwargs.keys()):
            res = res[0]
    elif res is not None:    
        res = PyNode(res)
    return res

def _constraint( func ):

    def constraint(*args, **kwargs):
        """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
Modifications:
    - added new syntax for querying the weight of a target object, by passing the constraint first::
    
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
        """
        if kwargs.get( 'query', kwargs.get('q', False) ) :
            attrs = [
            'upVector', 'u',
            'worldUpVector', 'wu',
            'aimVector', 'a' ]
            
            for attr in attrs:
                if attr in kwargs:
                    return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                    
            
        if len(args)==1:
            
            try:        
                # this will cause a KeyError if neither flag has been set. this quickly gets us out of if section if
                # we're not concerned with weights
                targetObjects = kwargs.get( 'weight', kwargs['w'] ) 
                constraint = args[0]
                if 'constraint' in cmds.cmds.nodeType( constraint, inherited=1 ):
                    print constraint
                    if not pymel.util.isIterable( targetObjects ):
                        targetObjects = [targetObjects]
                    elif not targetObjects:
                        targetObjects = func( constraint, q=1, targetList=1 )
    
                    constraintObj = cmds.listConnections( constraint + '.constraintParentInverseMatrix', s=1, d=0 )[0]    
                    args = targetObjects + [constraintObj]
                    kwargs.pop('w',None)
                    kwargs['weight'] = True
            except: pass
                
        res = func(*args, **kwargs)
        return res
    
    constraint.__name__ = func.__name__
    return constraint

#aimConstraint = _constraint( cmds.aimConstraint )
#geometryConstraint = _constraint( cmds.geometryConstraint )
#normalConstraint = _constraint( cmds.normalConstraint )
#orientConstraint = _constraint( cmds.orientConstraint )
#pointConstraint = _constraint( cmds.pointConstraint )
#scaleConstraint = _constraint( cmds.scaleConstraint )


def aimConstraint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
Modifications:
    - added new syntax for querying the weight of a target object, by passing the constraint first::
    
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
    """
    
    if kwargs.get( 'query', kwargs.get('q', False) ) :
        attrs = [
        'upVector', 'u',
        'worldUpVector', 'wu',
        'aimVector', 'a' ]
        
        for attr in attrs:
            if attr in kwargs:
                return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                
        
    if len(args)==1:
        
        try:        
            # this will cause a KeyError if neither flag has been set. this quickly gets us out of if section if
            # we're not concerned with weights
            targetObjects = kwargs.get( 'weight', kwargs['w'] ) 
            constraint = args[0]
            if 'constraint' in cmds.cmds.nodeType( constraint, inherited=1 ):
                print constraint
                if not pymel.util.isIterable( targetObjects ):
                    targetObjects = [targetObjects]
                elif not targetObjects:
                    targetObjects = cmds.aimConstraint( constraint, q=1, targetList=1 )

                constraintObj = cmds.listConnections( constraint + '.constraintParentInverseMatrix', s=1, d=0 )[0]    
                args = targetObjects + [constraintObj]
                kwargs.pop('w',None)
                kwargs['weight'] = True
        except: pass
            
    res = cmds.aimConstraint(*args, **kwargs)
    return res


def normalConstraint(*args, **kwargs):
    """
Maya Bug Fix:
    - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values
    """
    if 'query' in kwargs or 'q' in kwargs:
        
        attrs = [
        'upVector', 'u',
        'worldUpVector', 'wu',
        'aimVector', 'a' ]
        
        for attr in attrs:
            if attr in kwargs:
                return pymel.core.core.Vector( getAttr(args[0] + "." + attr ) )
                
            
    res = cmds.normalConstraint(*args, **kwargs)
    return res


pymel.util.factories.createFunctions( __name__ )



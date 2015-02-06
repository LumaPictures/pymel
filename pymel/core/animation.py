"""functions related to animation"""

import pymel.util as _util
import pymel.internal.factories as _factories
import general as _general
import pymel.versions as versions

import pymel.internal.pmcmds as cmds

def currentTime(*args, **kwargs):
    """
Modifications:
    - if no args are provided, the command returns the current time
    """

    if not args and not kwargs:
        return cmds.currentTime(q=1)
    else:
        return cmds.currentTime(*args, **kwargs)

def getCurrentTime():
    """get the current time as a float"""
    return cmds.currentTime(q=1)

def setCurrentTime(time):
    """set the current time """
    return cmds.currentTime(time)

def listAnimatable(*args, **kwargs):
    """
Modifications:
    - returns an empty list when the result is None
    - returns wrapped classes
    """
    return map(_general.PyNode, _util.listForNone(cmds.listAnimatable(*args, **kwargs)))

def keyframe(*args, **kwargs):
    """
Modifications:
    - returns an empty list when the result is None
    - if both valueChange and timeChange are queried, the result will be a list of (time,value) pairs
    """
    res = _util.listForNone(cmds.keyframe(*args, **kwargs))
    if kwargs.get('query', kwargs.get('q', False) ) and \
            kwargs.get('valueChange', kwargs.get('vc', False)) and kwargs.get('timeChange', kwargs.get('tc', False)):
        return list(_util.pairIter(res))
    return res

def deformer(*args, **kwargs):
    return map(_general.PyNode, cmds.deformer(*args, **kwargs))

def _constraint(func):
    def constraintWithWeightSyntax(*args, **kwargs):
        """
Maya Bug Fix:
  - when queried, angle offsets would be returned in radians, not current angle unit

Modifications:
  - added new syntax for querying the weight of a target object, by passing the constraint first::

        aimConstraint( 'pCube1_aimConstraint1', q=1, weight ='pSphere1' )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =['pSphere1', 'pCylinder1'] )
        aimConstraint( 'pCube1_aimConstraint1', q=1, weight =[] )
        """
        if kwargs.get('query', kwargs.get('q', False) and len(args) == 1):
            # Fix the big with angle offset query always being in radians
            if kwargs.get('offset', kwargs.get('o', None)):
                return _general.getAttr(str(args[0]) + ".offset")

            # try seeing if we can apply the new weight query syntax
            targetObjects = kwargs.get('weight', kwargs.get('w', None))
            if targetObjects is not None:
                # old way caused KeyError if 'w' not in kwargs, even if 'weight' was!
                # targetObjects = kwargs.get( 'weight', kwargs['w'] )
                constraint = args[0]
                if 'constraint' in cmds.nodeType(constraint, inherited=1):
                    if not _util.isIterable(targetObjects):
                        targetObjects = [targetObjects]
                    elif not targetObjects:
                        targetObjects = func(constraint, q=1, targetList=1)

                    constraintObj = cmds.listConnections(constraint + '.constraintParentInverseMatrix', s=1, d=0)[0]
                    args = targetObjects + [constraintObj]
                    kwargs.pop('w', None)
                    kwargs['weight'] = True
        res = func(*args, **kwargs)
        if kwargs.get('query', kwargs.get('q', False) and len(args) == 1):
            if kwargs.get('weightAliasList', kwargs.get('wal', None)):
                res = [_general.Attribute(args[0] + '.' + attr) for attr in res]
            elif kwargs.get('worldUpObject', kwargs.get('wuo', None)):
                res = _factories.unwrapToPyNode(res)
            elif kwargs.get('targetList', kwargs.get('tl', None)):
                res = _factories.toPyNodeList(res)
        return res

    constraint = constraintWithWeightSyntax
    if versions.current() < versions.v2009:
        def constraintWithVectorFix(*args, **kwargs):
            """
    Maya Bug Fix:
      - when queried, upVector, worldUpVector, and aimVector returned the name of the constraint instead of the desired values

            """
            if kwargs.get('query', kwargs.get('q', False) and len(args) == 1):

                # Fix the big with upVector, worldUpVector, and aimVector
                attrs = [
                    'upVector', 'u',
                    'worldUpVector', 'wu',
                    'aimVector', 'a']

                for attr in attrs:
                    if attr in kwargs:
                        return _general.datatypes.Vector(_general.getAttr(str(args[0]) + "." + attr))
            return constraintWithWeightSyntax(*args, **kwargs)
        constraintWithVectorFix.__doc__ += constraintWithWeightSyntax.__doc__
        constraint = constraintWithVectorFix

    constraint.__name__ = func.__name__
    return constraint

for contstraintCmdName in ('''aimConstraint geometryConstraint normalConstraint
                              orientConstraint parentConstraint pointConstraint
                              pointOnPolyConstraint poleVectorConstraint
                              scaleConstraint tangentConstraint''').split():
    cmd = getattr(cmds, contstraintCmdName, None)
    if cmd:
        globals()[contstraintCmdName] = _constraint(cmd)

_factories.createFunctions(__name__, _general.PyNode)

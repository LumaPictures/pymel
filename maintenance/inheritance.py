import maya.cmds as cmds
import pymel.internal.cmdcache as cmdcache
import pymel.core as pm
import pymel.internal.apicache as apicache
    
lsTypes = cmds.ls(nodeTypes=1)
num = len(lsTypes)
lsTypes = set(lsTypes)
assert num == len(lsTypes)
print num

allTypes = cmds.allNodeTypes()
num = len(allTypes)
allTypes = set(allTypes)
assert num == len(allTypes)
print num

assert lsTypes == allTypes

realTypes = lsTypes

abstractSuffix = ' (abstract)'
rawRealAndAbstract = cmds.allNodeTypes(includeAbstract=True)
realAndAbstract = set()
for x in rawRealAndAbstract:
    if x.endswith(abstractSuffix):
        x = x[:-len(abstractSuffix)]
    assert x not in realAndAbstract
    realAndAbstract.add(x)

abstractTypes = realAndAbstract - realTypes
assert len(abstractTypes) + len(realTypes) == len(realAndAbstract)

mobjDict = {}
dagMod = api.MDagModifier()
dgMod = api.MDGModifier()
for nodeType in realTypes:
    mobjDict[nodeType] = apicache._makeDgModGhostObject(nodeType, dagMod, dgMod)
dagMod.doIt()
dgMod.doIt()

mfnDag = api.MFnDagNode()
mfnDep = api.MFnDependencyNode()
dagTypes = set()
depTypes = set()
for nodeType, mobj in mobjDict.iteritems():
    mobj.
    

nodeDict = {}
for nodeType in realTypes:
    result = cmds.createNode(nodeType)
    nodeDict[nodeType] = result
    
assert len(nodeDict) == len(realTypes)

pynodeDict = {}
for nodeType, node in nodeDict.iteritems():
    pynodeDict[nodeType] = pm.PyNode(node)

inheritances = {}
badInheritances = {}
goodInheritances = {}
for nodeType, node in nodeDict.iteritems():
    inheritance = cmds.nodeType( node, inherited=1)
    inheritances[nodeType] = inheritance
    if not inheritance:
        badInheritances[nodeType] = inheritance
    else:
        goodInheritances[nodeType] = inheritance
        
assert len(inheritances) == len(realTypes) == len(badInheritances) + len(goodInheritances)

for nodeType, val in badInheritances.iteritems():
    if val is not None:
        print "Non-none bad value for %s: %s" % (nodeType, val)
    if not ('Manip' in nodeType or nodeType.startswith('manip')):
        print "Non-manip bad value for %s: %s" % (nodeType, val)
        
unknownNodes = set()
for nodeType, inheritance in goodInheritances.iteritems():
    assert inheritance[-1] == nodeType
    for x in inheritance:
        if x not in realAndAbstract:
            unknownNodes.add(x)
assert not unknownNodes, "%s nodes not in realAndAbstract" % ', '.join(unknownNodes)
        
def compareTrees(tree1, tree2):
    def convertTree(oldTree):
        if isinstance(oldTree, dict):
            return oldTree
        newTree = {}
        for key, parents, children in oldTree:
            newTree[key] = [parents, set(children)]
        return newTree
    t1set = set(tree1)
    t2set = set(tree2)
    both = t1set & t2set
    only1 = t1set - both
    only2 = t2set - both
    diff = {}
    for nodeType in both:
        n1 = tree1[nodeType]
        n2 = tree2[nodeType]
        if n1 != n2:
            if n1[0] == n2[0]: 
                parentDiff = 'same'
            else:
                parentDiff = (n1[0], n2[0])
            if n1[1] == n2[1]: 
                childDiff = 'same'
            else:
                childDiff = (n1[1] - n2[1], n2[1] - n1[1])
        diff[nodeType] = (parentDiff, childDiff)
    return only1, only2, diff

nodeTypeTree = {}
for nodeType in realAndAbstract:
    nodeTypeTree[nodeType] = [ None, set() ]
for nodeType, inheritance in goodInheritances.iteritems():
    assert inheritance[-1] == nodeType
    # len - 1 b/c final item is this nodeType
    for i in xrange(len(inheritance) - 1):
        parent = inheritance[i]
        child = inheritance[i + 1]
        
        # add the child to the parent
        nodeTypeTree[parent][1].add(child)
        
        # set the parents for the child
        parents = list(reversed(inheritance[:i+1]))
        if nodeTypeTree[child][0] is not None:
            assert nodeTypeTree[child][0] == parents
        else:
            nodeTypeTree[child][0] = parents
    

print "trees equal?"
print compareTrees(nodeTypeTree, cmdcache.nodeHierarchy)

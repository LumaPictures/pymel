from pprint import pprint

import maya.cmds as cmds
import pymel.api as api
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache
    
lsTypes = cmds.ls(nodeTypes=1)
num = len(lsTypes)
lsTypes = set(lsTypes)
assert num == len(lsTypes)
print num

realTypes = lsTypes

try:
    allTypes = cmds.allNodeTypes()
except RuntimeError:
    allTypes = None
    realAndAbstract = lsTypes
    abstractTypes = None
else:
    num = len(allTypes)
    allTypes = set(allTypes)
    assert num == len(allTypes)
    print num
    
    assert lsTypes == allTypes
    
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

nodeDict = {}
mfnDag = api.MFnDagNode()
mfnDep = api.MFnDependencyNode()
nonMelQueryableApiTypes = [api.MFn.kManipContainer, api.MFn.kManip2DContainer,
                           api.MFn.kManipulator3D, api.MFn.kManipulator2D,
                           api.MFn.kPolyToolFeedbackShape]
nonMelQueryableTypes = set()
melQueryableTypes = set()
dagTypes = set()
depTypes = set()
for nodeType, mobj in mobjDict.iteritems():
    if mfnDag.hasObj(mobj):
        dagTypes.add(nodeType)
        mfnDag.setObject(mobj)
        nodeDict[nodeType] = mfnDag.fullPathName()
    else:
        depTypes.add(nodeType)
        mfnDep.setObject(mobj)
        nodeDict[nodeType] = mfnDep.name()
    for manipApi in nonMelQueryableApiTypes:
        if mobj.hasFn(manipApi):
            nonMelQueryableTypes.add(nodeType)
            break
    else:
        melQueryableTypes.add(nodeType)
print "num non queryable types:", len(nonMelQueryableTypes)
        
#nodeDict = {}
#for nodeType in realTypes:
#    result = cmds.createNode(nodeType)
#    nodeDict[nodeType] = result
    
assert len(nodeDict) == len(realTypes)
assert len(nonMelQueryableTypes) + len(melQueryableTypes) == len(realTypes)
assert nonMelQueryableTypes | melQueryableTypes == realTypes

inheritances = {}
badInheritances = {}
goodInheritances = {}
for nodeType in melQueryableTypes:
    node = nodeDict[nodeType]
    try:
        inheritance = cmds.nodeType( node, inherited=True)
    except Exception, e:
        print "error caught:"
        print e
        inheritance = e
    inheritances[nodeType] = inheritance
    if not inheritance or isinstance(inheritance, Exception):
        badInheritances[nodeType] = inheritance
    else:
        goodInheritances[nodeType] = inheritance

def getApiTypes(mobj):
    apiTypes = []
    for apiTypeStr, apiType in apicache.apiTypesToApiEnums.iteritems():
        if mobj.hasFn(apiType):
            apiTypes.append(apiTypeStr)
    return apiTypes

#print getApiTypes(mobjDict['polyMoveUVManip'])
        
discoveredNodes = set()
for nodeType, inheritance in goodInheritances.iteritems():
    assert inheritance[-1] == nodeType
    for x in inheritance:
        if x not in realAndAbstract:
            discoveredNodes.add(x)
if discoveredNodes:
    print "#" * 60
    print "Warning!!!"
    print "%s nodes were not in realAndAbstract" % ', '.join(discoveredNodes)
    print "#" * 60
allKnownNodes = realAndAbstract | discoveredNodes
        
def compareTrees(tree1, tree2):
    def convertTree(oldTree):
        if isinstance(oldTree, dict):
            return oldTree
        newTree = {}
        for key, parents, children in oldTree:
            newTree[key] = [parents, set(children)]
        return newTree
    tree1 = convertTree(tree1)
    tree2 = convertTree(tree2)
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
for nodeType in allKnownNodes:
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

only1, only2, diff = compareTrees(nodeTypeTree, cmdcache.nodeHierarchy)

print
print "-" * 60
print "only1:"
pprint(list(only1))
print "-" * 60
print

print
print "-" * 60
print "only2:"
pprint(list(only2))
print "-" * 60
print

print
print "-" * 60
print "diff:"
pprint(diff)
print "-" * 60
print
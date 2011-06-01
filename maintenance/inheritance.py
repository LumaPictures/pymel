from pprint import pprint

import maya.cmds as cmds
import pymel.api as api
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache
import pymel.internal.factories as factories

cmds.file(new=1, f=1)
lsTypes = cmds.ls(nodeTypes=1)
num = len(lsTypes)
lsTypes = set(lsTypes)
assert num == len(lsTypes), "The result of ls(nodeTypes=1) contained duplicates"
print num

print 'got ls(nodeTypes=1), confirmed no dupes'

realTypes = lsTypes

try:
    allTypes = cmds.allNodeTypes()
except RuntimeError:
    print "Error calling allNodeTypes() !!"
    allTypes = None
    realAndAbstract = lsTypes
    abstractTypes = None
else:

    num = len(allTypes)
    allTypes = set(allTypes)
    assert num == len(allTypes), "The result of allNodeTypes() contained duplicates"
    print num
    
    print 'got allNodeTypes(), confirmed no dupes'

    assert lsTypes == allTypes, "ls(nodeTypes=1) and allNodeTypes() returned different result"
    
    print 'confirmed allNodeTypes() == ls(nodeTypes=1)'
    
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
    
    print 'got allNodeTypes(includeAbstract=True), separated nodes into real + abstract'

# To do - make and load a plugin which makes one of every possible plugin node
# type...

# with 2012, we have nodeType(isTypeName), so no longer need to add nodes!

#print 'about to make nodes...'
#mobjDict = {}
#dagMod = api.MDagModifier()
#dgMod = api.MDGModifier()
#for nodeType in realTypes:
#    #print 'making nodeType %s...' % nodeType,
#    mobjDict[nodeType] = apicache._makeDgModGhostObject(nodeType, dagMod, dgMod)
#    #print 'success!'
#dagMod.doIt()
#dgMod.doIt()
#
#print 'made nodes!'
#
#nodeDict = {}
#mfnDag = api.MFnDagNode()
#mfnDep = api.MFnDependencyNode()
#nonMelQueryableApiTypes = [api.MFn.kManipContainer, api.MFn.kManip2DContainer,
#                           api.MFn.kManipulator3D, api.MFn.kManipulator2D,
#                           api.MFn.kPolyToolFeedbackShape]
#nonMelQueryableTypes = set()
#melQueryableTypes = set()
#dagTypes = set()
#depTypes = set()
#for nodeType, mobj in mobjDict.iteritems():
#    if mfnDag.hasObj(mobj):
#        dagTypes.add(nodeType)
#        mfnDag.setObject(mobj)
#        nodeDict[nodeType] = mfnDag.fullPathName()
#    else:
#        depTypes.add(nodeType)
#        mfnDep.setObject(mobj)
#        nodeDict[nodeType] = mfnDep.name()
#    for manipApi in nonMelQueryableApiTypes:
#        if mobj.hasFn(manipApi):
#            nonMelQueryableTypes.add(nodeType)
#            break
#    else:
#        melQueryableTypes.add(nodeType)
#print "num non queryable types:", len(nonMelQueryableTypes)
#        
##nodeDict = {}
##for nodeType in realTypes:
##    result = cmds.createNode(nodeType)
##    nodeDict[nodeType] = result
#    
#assert len(nodeDict) == len(realTypes)
#assert len(nonMelQueryableTypes) + len(melQueryableTypes) == len(realTypes)
#assert nonMelQueryableTypes | melQueryableTypes == realTypes

inheritances = {}
badInheritances = {}
goodInheritances = {}
#for nodeType in melQueryableTypes:
for nodeType in allTypes:
    try:
        inheritance = cmds.nodeType( nodeType, inherited=True, isTypeName=True)
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

only1, only2, diff = compareTrees(nodeTypeTree, factories.nodeHierarchy)

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
#pprint(diff)
print "-" * 60
print

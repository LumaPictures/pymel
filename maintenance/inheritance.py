from pprint import pprint

import maya.cmds as cmds
import pymel.api as api
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache

cmds.file(new=1, f=1)
lsTypes = cmds.ls(nodeTypes=1)
num = len(lsTypes)
lsTypes = set(lsTypes)
assert num == len(lsTypes), "The result of ls(nodeTypes=1) contained duplicates"
print num

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
    
    assert lsTypes == allTypes, "ls(nodeTypes=1) and allNodeTypes() returned different result"
    
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
    

#print "trees equal?"
#
#only1, only2, diff = compareTrees(nodeTypeTree, cmdcache.nodeHierarchy)
#
#print
#print "-" * 60
#print "only1:"
#pprint(list(only1))
#print "-" * 60
#print
#
#print
#print "-" * 60
#print "only2:"
#pprint(list(only2))
#print "-" * 60
#print
#
#print
#print "-" * 60
#print "diff:"
#pprint(diff)
#print "-" * 60
#print
#
#
##==============================================================================
## Cache building comparison
##==============================================================================
#
#
#import pymel.internal.apicache
#reload(pymel.internal.apicache)
#
#def dummyFunc(*args, **kwargs):pass
#
#old_save = pymel.internal.apicache.ApiCache.save
#old_buildClass = pymel.internal.apicache.ApiCache._buildApiClassInfo
#
#pymel.internal.apicache.ApiCache.save = dummyFunc
#pymel.internal.apicache.ApiCache._buildApiClassInfo = dummyFunc
#
## cache1 will hold results from loading the cache on disk
## cache2 will hold results from rebuilding
##    (with exception of apiClassInfo, which is copied from cache1)
#
#cache1 = pymel.internal.apicache.ApiCache()
#cache1.build()
#for mayaType, apiType in cache1.mayaTypesToApiTypes.iteritems() :
#    cache1.addMayaType( mayaType, apiType )
#
#cache2 = pymel.internal.apicache.ApiCache()
#cache2.apiClassInfo = cache1.apiClassInfo
#cache2.rebuild()
#cache2._subCaches[pymel.internal.apicache.ApiMelBridgeCache].build()
#
#def compareDicts(dict1, dict2, showDiff=True, showOnlys=False, indent=0):
#    if isinstance(dict1, (list, tuple)):
#        dict1 = dict(enumerate(dict1))
#    if isinstance(dict2, (list, tuple)):
#        dict2 = dict(enumerate(dict2))
#    v1 = set(dict1)
#    v2 = set(dict2)
#    both = v1 & v2
#    only1 = v1 - both
#    only2 = v2 - both
#    print "\t" * indent, "both:", len(both)
#    print "\t" * indent, "only1:", len(only1)
#    print "\t" * indent, "only2:", len(only2)
#    
#    differences = {}
#    for mayaType in both:
#        if dict1[mayaType] != dict2[mayaType]:
#            differences[mayaType] = (dict1[mayaType], dict2[mayaType])
#    print "\t" * indent, "differences:", len(differences)
#    
#    #print "\t" * indent, "*" * 60
#    if showDiff and differences:
#        print "\t" * indent, "different: (%d)" % len(differences)
#        for key in sorted(differences):
#            print "\t" * indent, key, ':',
#            diff1, diff2 = differences[key]
#            subDict1 = subDict2 = None
#            if type(diff1) == type(diff2) and isinstance(diff1, (dict, list, tuple)):
#                print
#                compareDicts(diff1, diff2, showDiff=showDiff, showOnlys=showOnlys, indent=indent+1)
#            else:
#                print diff1, '-', diff2
#        #print "\t" * indent, "*" * 60
#    if showOnlys:
#        if only1:
#            print "\t" * indent, "only1: (%d)" % len(only1)
#            for x in only1:
#                print "\t" * indent, x
#            #print "\t" * indent, "*" * 60
#        if only2:
#            print "\t" * indent, "only2: (%d)" % len(only2)
#            for x in only2:
#                print "\t" * indent, x
#    #print "\t" * indent, "*" * 60
#    return both, only1, only2, differences
#
#unequals = {}
#names = cache1.cacheNames() + cache1.EXTRA_GLOBAL_NAMES
#for name in names:
#    val1 = getattr(cache1, name)
#    val2 = getattr(cache2, name)
#    areEqual = val1 == val2
#    print "%s equal? %s" % (name,  areEqual ),
#    if not areEqual:
#        unequals[name] = (val1, val2)
#        print "(%d, %d)" % (len(val1), len(val2)),
#    print
#
#for key, (val1, val2) in unequals.iteritems():
#    print '*' * 80
#    print key
#    compareDicts(val1, val2, showDiff=True)
#    print key
#    print '*' * 80
#
#
#pymel.internal.apicache.ApiCache.save = old_save
#pymel.internal.apicache.ApiCache._buildApiClassInfo = old_buildClass
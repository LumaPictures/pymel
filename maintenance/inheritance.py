from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import *
import re
import itertools
from pprint import pprint

import maya.cmds as cmds
import pymel.util as util
import pymel.util.trees as trees
import pymel.api as api
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache
import pymel.internal.factories as factories

#===============================================================================
# maya node type hierarchy info
#===============================================================================

cmds.file(new=1, f=1)
lsTypes = cmds.ls(nodeTypes=1)
num = len(lsTypes)
lsTypes = set(lsTypes)
assert num == len(lsTypes), "The result of ls(nodeTypes=1) contained duplicates"
print(num)

print('got ls(nodeTypes=1), confirmed no dupes')

realTypes = lsTypes

try:
    allTypesReal = cmds.allNodeTypes()
except RuntimeError:
    print("Error calling allNodeTypes() !!")
    allTypesReal = None
    realAndAbstract = lsTypes
    abstractTypes = None
else:

    num = len(allTypesReal)
    allTypesReal = set(allTypesReal)
    assert num == len(allTypesReal), "The result of allNodeTypes() contained duplicates"
    print(num)

    print('got allNodeTypes(), confirmed no dupes')

    assert lsTypes == allTypesReal, "ls(nodeTypes=1) and allNodeTypes() returned different result"

    print('confirmed allNodeTypes() == ls(nodeTypes=1)')

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


    print('got allNodeTypes(includeAbstract=True), separated nodes into real + abstract')
# TODO - make and load a plugin which makes one of every possible plugin node
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
for nodeType in realAndAbstract:
    try:
        inheritance = cmds.nodeType( nodeType, inherited=True, isTypeName=True)
    except Exception as e:
        print("error caught:")
        print(e)
        inheritance = e
    inheritances[nodeType] = inheritance
    if not inheritance or isinstance(inheritance, Exception):
        badInheritances[nodeType] = inheritance
    else:
        goodInheritances[nodeType] = inheritance

if badInheritances:
    print("#" * 60)
    print("Warning!!!")
    print("errors in getting inheritance for following node types:")
    for x in badInheritances:
        print("   ", x)
    print("#" * 60)

#print getApiTypes(mobjDict['polyMoveUVManip'])

discoveredNodes = set()
for nodeType, inheritance in goodInheritances.items():
    assert inheritance[-1] == nodeType
    for x in inheritance:
        if x not in realAndAbstract:
            discoveredNodes.add(x)
if discoveredNodes:
    print("#" * 60)
    print("Warning!!!")
    print("%s nodes were not in realAndAbstract" % ', '.join(discoveredNodes))
    print("#" * 60)
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
    nodeTypeTree[nodeType] = [ [], set() ]
for nodeType, inheritance in goodInheritances.items():
    assert inheritance[-1] == nodeType
    # len - 1 b/c final item is this nodeType
    for i in range(len(inheritance) - 1):
        parent = inheritance[i]
        child = inheritance[i + 1]

        # add the child to the parent
        nodeTypeTree[parent][1].add(child)

        # set the parents for the child
        parents = list(reversed(inheritance[:i+1]))
        if nodeTypeTree[child][0]:
            assert nodeTypeTree[child][0] == parents
        else:
            nodeTypeTree[child][0] = parents

#eliminate manipulators
nonManipTree = {}
manipulators = set()
for name, data in nodeTypeTree.items():
    parents = data[0]
    if parents is not None and ('manip3D' in parents or name == 'manip3D'):
        manipulators.add(name)
    else:
        nonManipTree[name] = data

nonManipNonPlugin = {}
for name, data in nonManipTree.items():
    parents = data[0]
    if parents is not None:
        if (any(x.startswith('TH') for x in parents)
                or name.startswith('TH')):
            continue
    nonManipNonPlugin[name] = data

print("trees equal?")

only1, only2, diff = compareTrees(nonManipNonPlugin, factories.nodeHierarchy)

print()
print("-" * 60)
print("only1:")
pprint(list(only1))
print("-" * 60)
print()

print()
print("-" * 60)
print("only2:")
pprint(list(only2))
print("-" * 60)
print()

print()
print("-" * 60)
print("diff:")
#pprint(diff)
print("-" * 60)
print()

#===============================================================================
# api type hierarchy info
#===============================================================================

def getApiTypes(mobj):
    apiTypes = []
    for apiTypeStr, apiType in factories.apiTypesToApiEnums.items():
        if mobj.hasFn(apiType):
            apiTypes.append(apiTypeStr)
    return apiTypes

mayaToApi = {}
mayaToAllApi = {}
unknownTypes = set()
#toCreate = set(nonManipTree)
toCreate = set(realTypes) - manipulators - set(apicache.ApiCache.CRASH_TYPES)
with apicache._GhostObjMaker(toCreate, manipError=False, multi=True) as typeToObj:
    for mayaType in toCreate:
        obj = typeToObj[mayaType]
        if obj :
            apiType = obj.apiTypeStr()
            mayaToApi[mayaType] = apiType
            mayaToAllApi[mayaType] = getApiTypes(obj)
        else:
            unknownTypes.add(mayaType)

assert mayaToApi.get('containerBase') == 'kContainerBase'

if unknownTypes:
    print("#" * 60)
    print("Warning!!!")
    print("could not create the following node types (which SHOULD be createable):")
    for x in sorted(unknownTypes):
        print("   ", x)
    print("#" * 60)

ac = apicache.ApiCache()
ac._buildApiTypesList()
allApiTypes = set(ac.apiTypesToApiEnums)

#===============================================================================
# First attempt at querying hierarchy info, by finding common types in children,
# and filtering types found in parents
#===============================================================================

#missingApiInfo = set(nonManipTree) - set(mayaToApi)
##missingNonAbstract = missingApiInfo - abstractTypes
#
## To try to find what the apiType for a maya type is, first find all api types
## that are shared by all it's children (it should have children, because if we
## can't create the node type, it should be abstract...
#
#sharedByChildren = {}
#noSharedByChildren = set()
#for missingType in missingApiInfo:
#    common = None
#    for otherType, apiTypes in mayaToAllApi.iteritems():
#        if nodeTypeTree[otherType][0] is None:
#            print 'type %s had None parent' % otherType
#        if missingType in nodeTypeTree[otherType][0]:
#            if common is None:
#                common = set(apiTypes)
#            else:
#                common = common & set(apiTypes)
#    if common:
#        sharedByChildren[missingType] = common
#    else:
#        noSharedByChildren.add(missingType)
#
## these are strange, because every node should at least all have things like
## kBase, kNamedObject, kDependencyNode...
#if noSharedByChildren:
#    print "#" * 60
#    print "Warning!!!"
#    print "could not find any common api types in children of the following node types:"
#    for x in sorted(noSharedByChildren):
#        print "   ", x
#    print "#" * 60
#
## these are api types which are shared by all dependency nodes
#baseApiTypes = set(['kBase', 'kNamedObject', 'kDependencyNode'])
#
#possibilities = {}
## Now, remove api types which are shared by any parents
#for mayaType, possibleApiTypes in sharedByChildren.iteritems():
#    filtered = set(possibleApiTypes)
#    for parent in nodeTypeTree[mayaType][0]:
#        if parent in mayaToApi:
#            filtered -= set([mayaToApi[parent]])
#        elif parent in sharedByChildren:
#            filtered -= sharedByChildren[parent]
#    filtered -= baseApiTypes
#    possibilities[mayaType] = filtered



#===============================================================================
# Second attempt at querying hierarchy info, by finding common types in children,
# then filtering types found in parents... AND using common ancestry information
#===============================================================================

# build up some information about our hierarchy

def commonAncestor(mayaType1, mayaType2):
    if None in (mayaType1, mayaType2):
        return None

    def reversedParents(mayaType):
        # want the parents in order from most generic to most specific - that
        # way, we can go from left to right, comparing items until we get to one
        # that doesn't match
        return list(reversed(nodeTypeTree[mayaType][0])) + [mayaType]
    parents1 = reversedParents(mayaType1)
    parents2 = reversedParents(mayaType2)

    commonAncestor = None
    for i in range(min(len(parents1), len(parents2))):
        if parents1[i] == parents2[i]:
            commonAncestor = parents1[i]
        else:
            break
    return commonAncestor

apiTypeToRealMayaTypes = {}

# for a given api type, find the "most specific" maya type that can be an
# ancestor of all maya types that "contain" that api type
apiTypeToCommonMayaAncestor = {}
for mayaType, apiTypes in mayaToAllApi.items():
    for apiType in apiTypes:
        apiTypeToRealMayaTypes.setdefault(apiType, []).append(mayaType)
        if apiType not in apiTypeToCommonMayaAncestor:
            apiTypeToCommonMayaAncestor[apiType] = mayaType
        else:
            apiTypeToCommonMayaAncestor[apiType] = commonAncestor(mayaType,
                                                              apiTypeToCommonMayaAncestor[apiType])

# now build the reverse dict - from maya type to a list of all api types that
# it is the common ancestor for
commonMayaAncestorToApiTypes = {}
for apiType, mayaType in apiTypeToCommonMayaAncestor.items():
    commonMayaAncestorToApiTypes.setdefault(mayaType, []).append(apiType)

# now, get a list of maya types for which there is only ONE api type that has
# it as it's most-specific-common-ancestor...
commonMayaAncestorToSingleApi = {}
for mayaType, apiTypes in commonMayaAncestorToApiTypes.items():
    if len(apiTypes) == 1:
        commonMayaAncestorToSingleApi[mayaType] = apiTypes[0]

# these are api types which are shared by all dependency nodes
baseApiTypes = set(['kBase', 'kNamedObject', 'kDependencyNode'])

parentDict = dict((mayaType, parents[0])
                  for mayaType, (parents, children) in nodeTypeTree.items()
                  if parents)
nodeTreeObj =  trees.treeFromDict(parentDict)
#orderedTree = [ (x.value, tuple(y.value for y in x.parents()), tuple(y.value for y in x.childs()) ) \
#                for x in nodeTreeObj.preorder() ]

guessedByCommonAncestor = {}
guessedByName = {}
nameAncestorConflicts = {}
guessedByUnique = {}
multiplePossibilities = {}
noUnique = {}

noChildIntersection = set()
childIntersections = {}
childUnions = {}
parentUnions = {}
childPreorders = {}

def nodeToApiName(nodeName):
    return 'k' + util.capitalize(nodeName)

def getLowerCaseMapping(names):
    uniqueLowerNames = {}
    multiLowerNames = {}
    for name in names:
        lowerType = name.lower()
        if lowerType in multiLowerNames:
            multiLowerNames[lowerType].append(name)
        elif lowerType in uniqueLowerNames:
            multiLowerNames[lowerType] = [uniqueLowerNames.pop(lowerType), name]
        else:
            uniqueLowerNames[lowerType] = name
    return uniqueLowerNames, multiLowerNames

uniqueLowerMaya, multiLowerMaya = getLowerCaseMapping(allKnownNodes)
uniqueLowerApi, multiLowerApi = getLowerCaseMapping(allApiTypes)

if multiLowerMaya:
    print("#" * 60)
    print("Warning!!!")
    print("maya node names differed only in case:")
    for types in multiLowerMaya.values():
        print("    %s" % ', '.join(types))
    print("#" * 60)

if multiLowerApi:
    print("#" * 60)
    print("Warning!!!")
    print("api type names differed only in case:")
    for types in multiLowerApi.values():
        print("    %s" % ', '.join(types))
    print("#" * 60)

modifiers = {
             'base':'',
             'abstract':'',
             'node':'',
             'shape':'',
             'mod(?!(ify|ifier))':'modify',
             'mod(?!(ify|ifier))':'modifier',
             'modifier':'mod',
             'modify':'mod',
             'poly(?!gon)':'polygon',
             'polygon':'poly',
             'vert(?!(ex|ice))':'vertex',
             'vert(?!(ex|ice))':'vertice',
             'vertice':'vert',
             'vertex':'vert',
             'subd(?!iv)':'subdiv',
             'subd(?!iv)':'subdivision',
             'subdiv(?!ision)':'subd',
             'subdiv(?!ision)':'subdivision',
             'subdivision':'subd',
             'subdivision':'subdiv',
             '^th(custom)?':'plugin',
            }
modifiers = [(re.compile(find), replace)
             for find, replace in modifiers.items()]

apiSuffixes = ['', 'node', 'shape', 'shapenode']

def guessApiTypeByName(nodeName, debug=False):
    # first, try the easy case...
    apiName = nodeToApiName(nodeName)
    if apiName in allApiTypes:
        if debug:
            print('basic transform worked!')
        return apiName

    lowerNode = nodeName.lower()
    if lowerNode not in uniqueLowerMaya:
        if debug:
            print('lower-case node name not unique...')
        return None

    # now, try with various modifications...
    possibleApiNames = set()

    possibleModifications = [(find, replace) for find, replace in modifiers
                             if find.search(lowerNode)]

    # find all possible combinations of all possible modifications
    for modifyNum in range(len(possibleModifications) + 1):
        for modifyCombo in itertools.combinations(possibleModifications, modifyNum):
            baseName = lowerNode
            for find, replace in modifyCombo:
                baseName = find.sub(replace, baseName)
            if debug:
                print([x[0].pattern for x in modifyCombo], baseName)
            if not baseName:
                # if we've eliminated the name with our changes - ie,
                # 'shape' would go to '' - then skip
                continue
            if baseName != lowerNode and (baseName in uniqueLowerMaya
                                          or baseName in multiLowerMaya):
                # if after modification, our new name is the name of another
                # maya node, skip
                continue
            apiLower = 'k' + baseName
            if apiLower in uniqueLowerApi:
                possibleApiNames.add(uniqueLowerApi[apiLower])
            else:
                for suffix in apiSuffixes:
                    apiWithSuffix = apiLower + suffix
                    if apiWithSuffix in uniqueLowerApi:
                        possibleApiNames.add(uniqueLowerApi[apiWithSuffix])
    if debug:
        print(possibleApiNames)

    if len(possibleApiNames) == 1:
        return list(possibleApiNames)[0]
    return None

#def guessApiTypeByName(nodeName):
#    def isApiType(apiName):
#        return isinstance(getattr(api.MFn, apiName, None), int)
#
#    for suffix in ('', 'node', 'shape', 'shapenode'):
#        if suffix:
#            if not nodeName.lower().endswith(suffix):
#                continue
#            baseName = nodeName[:-len(suffix)]
#        else:
#            baseName = nodeName
#        if not baseName:
#            continue
#        apiName = nodeToApiName(baseName)
#        if isApiType(apiName):
#            return apiName
#    return None

# now going from bases to leaves,
for currentTree in nodeTreeObj.preorder():
    mayaType = currentTree.value
    if mayaType is None:
        continue

    if mayaType in manipulators:
        continue

    # find nodes for which we don't have an api type for yet...
    if mayaType in mayaToApi:
        assert mayaType in mayaToAllApi, "type %s was in mayaToApi but not mayaToAllApi" % mayaType
        continue

    uniqueApiTypes = set()

    # find intersection of all types shared by all children (for which we have info)
    childIntersection = None
    childUnion = set()
    childPreorder = []
    for childTreeNode in currentTree.preorder():
        childType = childTreeNode.value
        if childType == mayaType:
            continue
        childPreorder.append(childType)
        allChildApiTypes = mayaToAllApi.get(childType)
        if allChildApiTypes is not None:
            allChildApiTypes = set(allChildApiTypes)
            if childIntersection is None:
                childIntersection = allChildApiTypes
            else:
                childIntersection &= allChildApiTypes
            childUnion |= allChildApiTypes
    if childIntersection:
        childIntersections[mayaType] = childIntersection
    else:
        if childIntersection is None:
            childIntersection = set()
        noChildIntersection.add(mayaType)
    childUnions[mayaType] = childUnion
    childPreorders[mayaType] = childPreorder

    # find union of parent types
    parentUnion = set(baseApiTypes)
    for parentTreeNode in currentTree.parents():
        parentType = parentTreeNode.value
        if parentType is not None:
            parentUnion |= set(mayaToAllApi[parentType])
    parentUnions[mayaType] = parentUnion

    # unique types were found in children, but weren't found in parents
    uniqueApiTypes = childIntersection - parentUnion

    # information gathering is done... now try to figure out the apiType!
    apiType = None

    # see if there's exactly one api type that this maya type is the
    # most-specific-common-ancestor of...
    commonAncestorGuess = commonMayaAncestorToSingleApi.get(mayaType, None)

    # ...and see if we can guess by name...
    apiNameGuess = guessApiTypeByName(mayaType)

    if apiNameGuess:
        apiType = apiNameGuess
        guessedByName[mayaType] = apiType
        if commonAncestorGuess and commonAncestorGuess != apiNameGuess:
            nameAncestorConflicts[mayaType] = (apiNameGuess, commonAncestorGuess)
    elif commonAncestorGuess:
        apiType = commonAncestorGuess
        guessedByCommonAncestor[mayaType] = apiType
    elif uniqueApiTypes:
        # if we did have unique types...
        if len(uniqueApiTypes) == 1:
            # ...we're golden if there was only 1...
            apiType = list(uniqueApiTypes)[0]
            guessedByUnique[mayaType] = apiType
        else:
            # ...but a little stuck if there's more.
            multiplePossibilities[mayaType] = uniqueApiTypes
    else:
        # if name guess failed, and we have no unique ApiTypes, we'll have to
        # fall back on using the parent type
        parentType = currentTree.parent.value
        if parentType is None:
            apiType = 'kDependencyNode'
        else:
            apiType = mayaToApi.get(parentType)
        noUnique[mayaType] = apiType

    allApi = uniqueApiTypes | parentUnion
    if apiType is not None:
        allApi |= set([apiType])
        mayaToApi[mayaType] = apiType
    mayaToAllApi[mayaType] = sorted(allApi)

if nameAncestorConflicts:
    print("#" * 60)
    print("Warning!!!")
    print("had conflicting name / common ancestor guess for these maya nodes:")
    for mayaType, (nameGuess, ancestorGuess) in nameAncestorConflicts.items():
        print("    %20s - %20s / %s" % (mayaType, nameGuess, ancestorGuess))
    print("#" * 60)

if multiplePossibilities:
    print("#" * 60)
    print("Warning!!!")
    print("could not find a unique api type for these nodes:")
    for mayaType in sorted(multiplePossibilities):
        print("    %20s - %s" % (mayaType, ', '.join(sorted(multiplePossibilities[mayaType]))))
    print("#" * 60)
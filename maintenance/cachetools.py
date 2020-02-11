from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
#from pymel.core import factories
#from pymel.all import mayautils
from builtins import input
from builtins import range
from past.builtins import basestring
from builtins import *
from builtins import object
import pprint
import os.path
import re
import copy

import pymel.core as pm
import pymel.internal.factories as factories
#import pymel.internal.mayautils as mayautils
import pymel.internal.startup as startup
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache
import pymel.util as util

def separateExampleCache():
    examples = {}
    succ = fail = 0
    for cmdName, cmdInfo in factories.cmdlist.items():
        try:
            examples[cmdName] = cmdInfo.pop('example')
            succ += 1
        except KeyError:
            fail += 1
            pass
    print("succeeded", succ)
    print("failed   ", fail)

    mayautils.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds),
                          'mayaCmdsList', 'the list of Maya commands', compressed=False )

    mayautils.writeCache( examples,
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=False )

def separateApiDocs():
    data = list(mayautils.loadCache('mayaApi',compressed=True))
    apiClassInfo = data[7]
    newApiDocs = {}
    for mfn, mfnInfo in apiClassInfo.items():
        #print mfn, type(mfnInfo)
        if isinstance(mfnInfo, dict):
            #print mfn
            newAllMethodsInfo = {}
            for method, methodInfoList in mfnInfo['methods'].items():
                newMethodInfoList = []
                for i, methodInfo in enumerate(methodInfoList):
                    newMethodInfo = {}
                    if 'doc' in methodInfo:
                        newMethodInfo['doc'] = methodInfo.pop('doc')
                    newArgInfo = {}
                    for arg, argInfo in methodInfo['argInfo'].items():
                        if 'doc' in argInfo:
                            newArgInfo[arg] = {'doc': argInfo.pop('doc')}
                    if newArgInfo:
                        newMethodInfo['argInfo'] = newArgInfo
                    newMethodInfoList.append(newMethodInfo)
                if newMethodInfoList:
                    newAllMethodsInfo[method] = newMethodInfoList
            if newAllMethodsInfo:
                newApiDocs[mfn] = {'methods': newAllMethodsInfo }
        else:
            pass
            #print mfn, type(mfnInfo)
    #pprint.pprint(newApiDocs['MFnTransform'])
    data[7] = apiClassInfo

    mayautils.writeCache( tuple(data),
                          'mayaApi', compressed=True )

    mayautils.writeCache( newApiDocs,
                          'mayaApiDocs',compressed=True )

def upgradeCmdCaches():
    import pymel.internal.cmdcache as cmdcache

    data = list(mayautils.loadCache('mayaCmdsList',compressed=False))
    cmdlist = data[0]
    nodeHierarchy = data[1]
    cmdDocList = {}
    examples = {}
    succ = fail = 0
    for cmdName, cmdInfo in cmdlist.items():

        flags = cmdcache.getCallbackFlags(cmdInfo)
        if flags:
            cmdlist[cmdName]['callbackFlags'] = flags

        try:
            examples[cmdName] = cmdInfo.pop('example')
        except KeyError:
            pass

        newCmdInfo = {}
        if 'description' in cmdInfo:
            newCmdInfo['description'] = cmdInfo.pop('description')
        newFlagInfo = {}
        if 'flags' in cmdInfo:
            for flag, flagInfo in cmdInfo['flags'].items():
                newFlagInfo[flag] = { 'docstring' : flagInfo.pop('docstring') }
            newCmdInfo['flags'] = newFlagInfo

        if newCmdInfo:
            cmdDocList[cmdName] = newCmdInfo

        if 'shortFlags' in cmdInfo:
            d = {}
            #print cmdName
            for flag, flagInfo in cmdInfo['shortFlags'].items():
                if isinstance(flagInfo, dict):
                    d[flag] = flagInfo['longname']
                elif isinstance(flagInfo, basestring):
                    d[flag] = flagInfo
                else:
                    raise TypeError
            cmdInfo['shortFlags'] = d

    hierarchy = [ (x.key, tuple( [y.key for y in x.parents()]), tuple( [y.key for y in x.childs()] ) ) \
                   for x in nodeHierarchy.preorder() ]

    data[0] = cmdlist
    data[1] = hierarchy

    mayautils.writeCache( tuple(data),
                          'mayaCmdsList', 'the list of Maya commands',compressed=True )

    mayautils.writeCache( cmdDocList,
                          'mayaCmdsDocs', 'the Maya command documentation',compressed=True )

    mayautils.writeCache( examples,
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=True )

#    for cache, useVersion in [ ('mayaApiMelBridge',False), ('mayaApi',True) ]:
#        data = mayautils.loadCache(cache, useVersion=useVersion, compressed=False)
#        mayautils.writeCache(data, cache, useVersion=useVersion, compressed=True)

def addCallbackFlags():
    data = list(mayautils.loadCache('mayaCmdsList',compressed=True))
    cmdlist = data[0]
    succ = 0
    for cmdName, cmdInfo in cmdlist.items():
        flags = factories.getCallbackFlags(cmdInfo)
        if flags:
            cmdlist[cmdName]['callbackFlags'] = flags
            succ += 1

    data[0] = cmdlist
    mayautils.writeCache( tuple(data),
                          'mayaCmdsList', 'the list of Maya commands',compressed=True )

def reduceShortFlags():
    succ = 0
    for cmdName, cmdInfo in factories.cmdlist.items():
        if 'shortFlags' in cmdInfo:
            d = {}
            print(cmdName)
            for flag, flagInfo in cmdInfo['shortFlags'].items():
                if isinstance(flagInfo, dict):
                    d[flag] = flagInfo['longname']
                elif isinstance(flagInfo, basestring):
                    d[flag] = flagInfo
                else:
                    raise TypeError
            cmdInfo['shortFlags'] = d
            succ += 1
    print("reduced", succ)
    mayautils.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds),
                          'mayaCmdsList', 'the list of Maya commands' )

def flattenNodeHier():

    hierarchy = [ (x.key, tuple( [y.key for y in x.parents()]) ) for x in factories.nodeHierarchy.preorder() ]
    factories.nodeHierarchy = hierarchy
    mayautils.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds),
                          'mayaCmdsList', 'the list of Maya commands' )

caches = [ ('mayaCmdsList', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]
def mergeAll():
    data = []
    for cache, useVersion in caches:
        data.append( mayautils.loadCache(cache, useVersion=useVersion))

    mayautils.writeCache( tuple(data), 'mayaAll' )


import time
def mergedTest():
    s1 = time.time()
    for cache, useVersion in caches:
        mayautils.loadCache(cache, useVersion=useVersion)
    print(time.time()-s1)

    s2 = time.time()
    mayautils.loadCache('mayaAll')
    print(time.time() - s2)


def compressAll():
    for cache, useVersion in caches + [('mayaCmdsListAll', True), ('mayaCmdsDocs', True) ]:
        compress(cache, useVersion)

def compress(cache, useVersion=True):
    useVersion = dict(caches).get(cache,useVersion)
    data = mayautils.loadCache(cache, useVersion=useVersion, compressed=False)
    mayautils.writeCache(data, cache, useVersion=useVersion, compressed=True)

def decompress():
    caches2 = [ ('mayaCmdsListAll', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]

    num = 3

    s = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=False)
    print("compress=0, docstrings=1:", time.time()-s)

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=False)
    print("compress=0, docstrings=0:", time.time()-s1)

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=True)
    print("compress=1, docstrings=1:", time.time()-s1)

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=True)
    print("compress=1, docstrings=0:", time.time()-s1)

def prepdiff(cache, outputDir='' ):
    pprintCache(cache, True, outputDir)
    pprintCache(cache, False, outputDir)

def pprintCache(cache, compressed, outputDir):
    useVersion = dict(caches).get(cache,True)
    data = mayautils.loadCache(cache, useVersion=useVersion, compressed=compressed)
    fname = os.path.realpath(os.path.join('', cache+ ('_zip.txt' if compressed else '_bin.txt') ) )
    print("writing to", fname)
    f = open(fname, 'w')

    pprint.pprint( data, f)
    f.close()

def compareDicts(dict1, dict2, showDiff=True, showOnlys=False, indent=0):
    if isinstance(dict1, (list, tuple)):
        dict1 = dict(enumerate(dict1))
    if isinstance(dict2, (list, tuple)):
        dict2 = dict(enumerate(dict2))
    v1 = set(dict1)
    v2 = set(dict2)
    both = v1 & v2
    only1 = v1 - both
    only2 = v2 - both
    print("\t" * indent, "both:", len(both))
    print("\t" * indent, "only1:", len(only1))
    print("\t" * indent, "only2:", len(only2))

    differences = {}
    for mayaType in both:
        if dict1[mayaType] != dict2[mayaType]:
            differences[mayaType] = (dict1[mayaType], dict2[mayaType])
    print("\t" * indent, "differences:", len(differences))

    #print "\t" * indent, "*" * 60
    if showDiff and differences:
        print("\t" * indent, "different: (%d)" % len(differences))
        for key in sorted(differences):
            print("\t" * indent, key, ':', end=' ')
            diff1, diff2 = differences[key]
            subDict1 = subDict2 = None
            if type(diff1) == type(diff2) and isinstance(diff1, (dict, list, tuple)):
                print()
                compareDicts(diff1, diff2, showDiff=showDiff, showOnlys=showOnlys, indent=indent+1)
            else:
                print(diff1, '-', diff2)
        #print "\t" * indent, "*" * 60
    if showOnlys:
        if only1:
            print("\t" * indent, "only1: (%d)" % len(only1))
            for x in only1:
                print("\t" * indent, x)
            #print "\t" * indent, "*" * 60
        if only2:
            print("\t" * indent, "only2: (%d)" % len(only2))
            for x in only2:
                print("\t" * indent, x)
    #print "\t" * indent, "*" * 60
    return both, only1, only2, differences


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

def _getClassEnumDicts(pickleData, parser):
    classInfos = pickleData[-1]
    classEnums = {}; classPyEnums = {}
    for className, classInfo in classInfos.items():
        enums = classInfo.get('enums')
        if enums:
            enums = dict( (enumName, data['values']) for enumName, data in enums.items())
            classEnums[className] = enums
        pyEnums = classInfo.get('pymelEnums')
        if pyEnums:
            classPyEnums[className] = pyEnums
    assert(set(classEnums.keys()) == set(classPyEnums.keys()))
    return classEnums, classPyEnums

def checkEnumConsistency(pickleData, docLocation=None, parser=None):
    '''Check that the pymelEnums and enums have consistent index mappings
    '''
    class NotFound(object):
        def __repr__(self):
            return ':NOTFOUND:'
    notFound = NotFound()

    if parser is None:
        import pymel.internal.parsers as parsers
        import maya.OpenMaya as om
        parser = parsers.ApiDocParser(om, docLocation=docLocation)
    classEnums, classPyEnums = _getClassEnumDicts(pickleData, parser)

    badByEnum = {}

    for className, enums in classEnums.items():
        for enumName, enum in enums.items():
            fullEnumName = "%s.%s" % (className, enumName)
            badThisEnum = {}
            try:
                #print fullEnumName
                #print enum
                pyEnum = classPyEnums[className][enumName]
                #print pyEnum
                enumToPyNames = parser._apiEnumNamesToPymelEnumNames(enum)
                for apiName, val in enum._keys.items():
                    pyName = enumToPyNames[apiName]
                    try:
                        pyIndex = pyEnum.getIndex(pyName)
                    except ValueError:
                        pyIndex = notFound
                    try:
                        apiIndex = enum.getIndex(apiName)
                    except ValueError:
                        apiIndex = notFound
                    if pyIndex != apiIndex:
                        badThisEnum.setdefault('mismatch', []).append(
                                    {'api':(apiName, apiIndex),
                                     'py':(pyName, pyIndex)})
                    if pyIndex is None:
                        badThisEnum.setdefault('badPyIndex', []).append((pyName, pyIndex))
                    if apiIndex is None:
                        badThisEnum.setdefault('badApiIndex', []).append((apiName, apiIndex))

            except Exception:
                import traceback
                badThisEnum['exception'] = traceback.format_exc()
            if badThisEnum:
                badByEnum[fullEnumName] = badThisEnum
    return classEnums, classPyEnums, badByEnum
#    if bad:
#        print
#        print "!" * 80
#        print "Bad results:"
#        print '\n'.join(bad)
#        print "!" * 80
#        raise ValueError("inconsistent pickled enum data")

# made a change to enums in apiClassInfo[apiClassName]['pymelEnums'] such that
# they now have as keys BOTH the api form (kSomeName) and the python form
# (someName) - this method converts over old caches on disk to the new format
def convertPymelEnums(docLocation=None):
    # Compatibility for pre-2012 caches... see note after ApiEnum def in
    # apicache
    import pymel.api
    pymel.api.Enum = apicache.ApiEnum
    apicache.Enum = apicache.ApiEnum

    import pymel.internal.parsers as parsers
    import maya.OpenMaya as om
    parser = parsers.ApiDocParser(om, docLocation=docLocation)

    dummyCache = apicache.ApiCache()
    dummyCache.version = '[0-9.]+'
    cachePattern = pm.Path(dummyCache.path())
    caches = sorted(cachePattern.parent.files(re.compile(cachePattern.name)))
    rawCaches = {}
    badByCache = {}
    enumsByCache = {}
    for cachePath in caches:
        print("checking enum data for: %s" % cachePath)
        raw = pm.util.picklezip.load(str(cachePath))
        rawCaches[cachePath] = raw
        classEnums, classPyEnums, bad = checkEnumConsistency(raw, parser=parser)
        if bad:
            badByCache[cachePath] = bad
        enumsByCache[cachePath] = {'api':classEnums, 'py':classPyEnums}
    if badByCache:
        pprint.pprint(badByCache)
        print("Do you want to continue converting pymel enums? (y/n)")
        print("(Pymel values will be altered to match the api values)")
        answer = input().lower().strip()
        if not answer or answer[0] != 'y':
            print("aborting cache update")
            return
    fixedKeys = []
    deletedEnums = []
    for cachePath, raw in rawCaches.items():
        print('=' * 60)
        print("Fixing: %s" % cachePath)
        apiClassInfo = raw[-1]
        apiEnums = enumsByCache[cachePath]['api']
        pyEnums = enumsByCache[cachePath]['py']
        assert(set(apiEnums.keys()) == set(pyEnums.keys()))
        for className, apiEnumsForClass in apiEnums.items():
            pyEnumsForClass = pyEnums[className]
            assert(set(apiEnumsForClass.keys()) == set(pyEnumsForClass.keys()))
            for enumName, apiEnum in apiEnumsForClass.items():
                fullEnumName = '%s.%s' % (className, enumName)
                print(fullEnumName)

                # first, find any "bad" values - ie, values whose index is None
                # - and delete them
                badKeys = [key for key, index in apiEnum._keys.items()
                           if index is None]
                if badKeys:
                    print("!!!!!!!!")
                    print("fixing bad keys in %s - %s" % (fullEnumName, badKeys))
                    print("!!!!!!!!")
                    assert(None in apiEnum._values)
                    valueDocs =  apiClassInfo[className]['enums'][enumName]['valueDocs']
                    for badKey in badKeys:
                        valueDocs.pop(badKey, None)
                        del apiEnum._keys[badKey]
                    del apiEnum._values[None]

                    if not apiEnum._keys:
                        print("enum empty after removing bad keys - deleting...")
                        del apiClassInfo[className]['enums'][enumName]
                        del apiClassInfo[className]['pymelEnums'][enumName]
                        deletedEnums.append(fullEnumName)
                        continue
                    else:
                        fixedKeys.append(fullEnumName)
                else:
                    assert(None not in apiEnum._values)

                try:
                    pyEnums[className] = parser._apiEnumToPymelEnum(apiEnum)
                except Exception:
                    globals()['rawCaches'] = rawCaches
                    globals()['apiEnum'] = apiEnum
                    raise

    # After making ALL changes, if there were NO errors, write them all out...
    for cachePath, raw in rawCaches.items():
        pm.util.picklezip.dump(raw, str(cachePath))

def apiPymelWrapData(keepDocs=False, keepReturnQualifiers=True):
    '''
    Return a dict with info about which api methods were actually wrapped

    Supposed to help detect if changes to the api wraps (or api parsing, etc)
    have affected something that "matters" - ie, a class which is actually
    warpped by pymel, and a method overload that is actually used.

    ***WARNING***
    To work, you will first have to edit factories.py and set _DEBUG_API_WRAPS
    to True
    '''
    # make sure we trigger loading of all dynamic modules, and all their
    # members...
    import pymel.all

    apiClassInfo = factories.apiClassInfo
    usedMethods = {}
    for apiClassName, classMethods in factories._apiMethodWraps.items():
        for methodName, methodWraps in classMethods.items():
            for methodWrapInfo in methodWraps:
                func = methodWrapInfo['funcRef']
                if func is None:
                    continue
                index = methodWrapInfo['index']
                usedClassMethods = usedMethods.setdefault(apiClassName, {})
                methodInfo = apiClassInfo[apiClassName]['methods'][methodName][index]

                # copy the methodInfo, we (might be) modifying it
                methodInfo = copy.deepcopy(methodInfo)
                if not keepDocs:
                    # the docs aren't really necessary for comparing
                    # compatibility... get rid of them..
                    methodInfo.pop('doc', None)
                    for argData in methodInfo.get('argInfo', {}).values():
                        argData.pop('doc', None)
                    methodInfo.get('returnInfo', {}).pop('doc', None)
                if not keepReturnQualifiers:
                    methodInfo.get('returnInfo', {}).pop('qualifiers', None)
                usedClassMethods.setdefault(methodName, {})[index] = methodInfo
    return usedMethods

def findApiWrapRegressions(oldWraps, newWraps):
    '''Given api wrap data from apiPymelWrapData for an old and new version,
    tries to find changes that would cause backwards-compatibility problems /
    regressions.
    '''
    def setClassProblem(className, issue):
        problems[className] = issue

    def getClassProblems(className):
        return problems.setdefault(className, {})

    def setMethodProblem(className, methodName, issue):
        getClassProblems(className)[methodName] = issue

    def getMethodProblems(className, methodName):
        return getClassProblems(className).setdefault(methodName, {})

    def setIndexProblem(className, methodName, index, issue):
        getMethodProblems(className, methodName)[index] = issue

    problems = {}
    for className, oldMethodNames in oldWraps.items():
        if className not in newWraps:
            setClassProblem(className, '!!!Class missing!!!')
            continue
        newMethodNames = newWraps[className]

        for methodName, oldMethodWraps in oldMethodNames.items():
            if methodName not in newMethodNames:
                setMethodProblem(className, methodName, '!!!Method missing!!!')
                continue
            newMethodWraps = newMethodNames[methodName]

            for i, oldWrap in oldMethodWraps.items():
                try:
                    newWrap = newMethodWraps[i]
                except KeyError:
                    setIndexProblem(className, methodName, i, '!!!Overload index missing!!!')
                    continue
                if newWrap == oldWrap:
                    continue
                else:
                    diff = util.compareCascadingDicts(oldWrap, newWrap)
                    setIndexProblem(className, methodName, i, ('Overload differed',
                                                               diff[1:]))
    return problems



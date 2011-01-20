#from pymel.core import factories
#from pymel.all import mayautils
import pprint
import os.path
import pymel.internal.factories as factories
#import pymel.internal.mayautils as mayautils
import pymel.internal.startup as startup
import pymel.internal.cmdcache as cmdcache
import pymel.internal.apicache as apicache

def separateExampleCache():
    examples = {}
    succ = fail = 0
    for cmdName, cmdInfo in factories.cmdlist.iteritems():
        try:
            examples[cmdName] = cmdInfo.pop('example')
            succ += 1
        except KeyError:
            fail += 1
            pass
    print "succeeded", succ
    print "failed   ", fail

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
    for mfn, mfnInfo in apiClassInfo.iteritems():
        #print mfn, type(mfnInfo)
        if isinstance(mfnInfo, dict):
            #print mfn
            newAllMethodsInfo = {}
            for method, methodInfoList in mfnInfo['methods'].iteritems():
                newMethodInfoList = []
                for i, methodInfo in enumerate(methodInfoList):
                    newMethodInfo = {}
                    if 'doc' in methodInfo:
                        newMethodInfo['doc'] = methodInfo.pop('doc')
                    newArgInfo = {}
                    for arg, argInfo in methodInfo['argInfo'].iteritems():
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
    for cmdName, cmdInfo in cmdlist.iteritems():
        
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
            for flag, flagInfo in cmdInfo['flags'].iteritems():
                newFlagInfo[flag] = { 'docstring' : flagInfo.pop('docstring') }
            newCmdInfo['flags'] = newFlagInfo
        
        if newCmdInfo:
            cmdDocList[cmdName] = newCmdInfo
            
        if 'shortFlags' in cmdInfo:
            d = {}
            #print cmdName
            for flag, flagInfo in cmdInfo['shortFlags'].iteritems():
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
    for cmdName, cmdInfo in cmdlist.iteritems():
        flags = factories.getCallbackFlags(cmdInfo)
        if flags:
            cmdlist[cmdName]['callbackFlags'] = flags
            succ += 1
    
    data[0] = cmdlist
    mayautils.writeCache( tuple(data), 
                          'mayaCmdsList', 'the list of Maya commands',compressed=True )
      
def reduceShortFlags():
    succ = 0
    for cmdName, cmdInfo in factories.cmdlist.iteritems():
        if 'shortFlags' in cmdInfo:
            d = {}
            print cmdName
            for flag, flagInfo in cmdInfo['shortFlags'].iteritems():
                if isinstance(flagInfo, dict):
                    d[flag] = flagInfo['longname']
                elif isinstance(flagInfo, basestring):
                    d[flag] = flagInfo
                else:
                    raise TypeError
            cmdInfo['shortFlags'] = d
            succ += 1
    print "reduced", succ
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
    print time.time()-s1
    
    s2 = time.time()
    mayautils.loadCache('mayaAll')
    print time.time() - s2
    

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
    print "compress=0, docstrings=1:", time.time()-s
    
    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=False)
    print "compress=0, docstrings=0:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=1:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayautils.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=0:", time.time()-s1

def prepdiff(cache, outputDir='' ):
    pprintCache(cache, True, outputDir)
    pprintCache(cache, False, outputDir)
     
def pprintCache(cache, compressed, outputDir):
    useVersion = dict(caches).get(cache,True)
    data = mayautils.loadCache(cache, useVersion=useVersion, compressed=compressed)
    fname = os.path.realpath(os.path.join('', cache+ ('_zip.txt' if compressed else '_bin.txt') ) )
    print "writing to", fname
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
    print "\t" * indent, "both:", len(both)
    print "\t" * indent, "only1:", len(only1)
    print "\t" * indent, "only2:", len(only2)
    
    differences = {}
    for mayaType in both:
        if dict1[mayaType] != dict2[mayaType]:
            differences[mayaType] = (dict1[mayaType], dict2[mayaType])
    print "\t" * indent, "differences:", len(differences)
    
    #print "\t" * indent, "*" * 60
    if showDiff and differences:
        print "\t" * indent, "different: (%d)" % len(differences)
        for key in sorted(differences):
            print "\t" * indent, key, ':',
            diff1, diff2 = differences[key]
            subDict1 = subDict2 = None
            if type(diff1) == type(diff2) and isinstance(diff1, (dict, list, tuple)):
                print
                compareDicts(diff1, diff2, showDiff=showDiff, showOnlys=showOnlys, indent=indent+1)
            else:
                print diff1, '-', diff2
        #print "\t" * indent, "*" * 60
    if showOnlys:
        if only1:
            print "\t" * indent, "only1: (%d)" % len(only1)
            for x in only1:
                print "\t" * indent, x
            #print "\t" * indent, "*" * 60
        if only2:
            print "\t" * indent, "only2: (%d)" % len(only2)
            for x in only2:
                print "\t" * indent, x
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
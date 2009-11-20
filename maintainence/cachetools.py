#from pymel.core import factories
from pymel.all import mayahook
import pprint
import os.path
import pymel.core.factories as factories
import pymel.util as util

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

    internal.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands', compressed=False )
    
    internal.writeCache( examples, 
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=False )

def separateApiDocs():
    data = list(internal.loadCache('mayaApi',compressed=True))
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
    
    internal.writeCache( tuple(data), 
                          'mayaApi', compressed=True )
    
    internal.writeCache( newApiDocs, 
                          'mayaApiDocs',compressed=True )
    
def upgradeCmdCaches():
    data = list(internal.loadCache('mayaCmdsList',compressed=False))
    cmdlist = data[0]
    nodeHierarchy = data[1]
    cmdDocList = {}
    examples = {}
    succ = fail = 0
    for cmdName, cmdInfo in cmdlist.iteritems():
        
        flags = factories.getCallbackFlags(cmdInfo)
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
    
    internal.writeCache( tuple(data), 
                          'mayaCmdsList', 'the list of Maya commands',compressed=True )
    
    internal.writeCache( cmdDocList, 
                          'mayaCmdsDocs', 'the Maya command documentation',compressed=True )

    internal.writeCache( examples, 
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=True )

#    for cache, useVersion in [ ('mayaApiMelBridge',False), ('mayaApi',True) ]:
#        data = internal.loadCache(cache, useVersion=useVersion, compressed=False)
#        internal.writeCache(data, cache, useVersion=useVersion, compressed=True)
        
def addCallbackFlags():
    data = list(internal.loadCache('mayaCmdsList',compressed=True))
    cmdlist = data[0]
    succ = 0
    for cmdName, cmdInfo in cmdlist.iteritems():
        flags = factories.getCallbackFlags(cmdInfo)
        if flags:
            cmdlist[cmdName]['callbackFlags'] = flags
            succ += 1
    
    data[0] = cmdlist
    internal.writeCache( tuple(data), 
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
    internal.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands' )

def flattenNodeHier():
    
    hierarchy = [ (x.key, tuple( [y.key for y in x.parents()]) ) for x in factories.nodeHierarchy.preorder() ]
    factories.nodeHierarchy = hierarchy
    internal.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands' )

caches = [ ('mayaCmdsList', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]
def mergeAll():
    data = []
    for cache, useVersion in caches:
        data.append( internal.loadCache(cache, useVersion=useVersion))

    internal.writeCache( tuple(data), 'mayaAll' )


import time
def mergedTest():
    s1 = time.time()
    for cache, useVersion in caches:
        internal.loadCache(cache, useVersion=useVersion)
    print time.time()-s1
    
    s2 = time.time()
    internal.loadCache('mayaAll')
    print time.time() - s2
    

def compressAll():
    for cache, useVersion in caches + [('mayaCmdsListAll', True), ('mayaCmdsDocs', True) ]:
        compress(cache, useVersion)

def compress(cache, useVersion=True):
    useVersion = dict(caches).get(cache,useVersion)
    data = internal.loadCache(cache, useVersion=useVersion, compressed=False)
    internal.writeCache(data, cache, useVersion=useVersion, compressed=True)
    
def decompress():
    caches2 = [ ('mayaCmdsListAll', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]
    
    num = 3
    
    s = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = internal.loadCache(cache, useVersion=useVersion, compressed=False)
    print "compress=0, docstrings=1:", time.time()-s
    
    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = internal.loadCache(cache, useVersion=useVersion, compressed=False)
    print "compress=0, docstrings=0:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = internal.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=1:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = internal.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=0:", time.time()-s1

def prepdiff(cache, outputDir='' ):
    pprintCache(cache, True, outputDir)
    pprintCache(cache, False, outputDir)
     
def pprintCache(cache, compressed, outputDir):
    useVersion = dict(caches).get(cache,True)
    data = internal.loadCache(cache, useVersion=useVersion, compressed=compressed)
    fname = os.path.realpath(os.path.join('', cache+ ('_zip.txt' if compressed else '_bin.txt') ) )
    print "writing to", fname
    f = open(fname, 'w')

    pprint.pprint( data, f)
    f.close()

def moveEnums():
    import pymel.internal.apicache
    data = list(mayahook.loadCache('mayaApiMelBridge',useVersion=False))
    apiClassOverrides = data[1]
    v = apiClassOverrides['MFnMesh']['methods']['setPoints'][0]['args'][1]
    v = (v[0], pymel.internal.apicache.Enum(v[1]), v[2])
    apiClassOverrides['MFnMesh']['methods']['setPoints'][0]['args'][1]= v

    v = apiClassOverrides['MFnMesh']['methods']['setPoints'][1]['args'][1]
    v = (v[0], pymel.internal.apicache.Enum(v[1]), v[2])
    apiClassOverrides['MFnMesh']['methods']['setPoints'][1]['args'][1]= v
    
    data[1] = apiClassOverrides
    mayahook.writeCache(data, 'mayaApiMelBridge', useVersion=False, compressed=True)
    
#def moveEnums(newModule):
#    data = list(internal.loadCache('mayaApiMelBridge',useVersion=False))
#    apiClassOverrides = data[1]
#    for mfn, mfnInfo in apiClassOverrides.iteritems():
#        #print mfn, type(mfnInfo)
#        if isinstance(mfnInfo, dict):
#            #print mfn
#            newAllMethodsInfo = {}
#            for method, methodInfoList in mfnInfo['methods'].iteritems():
#                for i, methodInfo in methodInfoList.iteritems():
#                    for arg, argInfo in methodInfo['args'].iteritems():
#                        if 'doc' in argInfo:
#                            newArgInfo[arg] = {'doc': argInfo.pop('doc')}
#                    if newArgInfo:
#                        newMethodInfo['argInfo'] = newArgInfo
#                    newMethodInfoList.append(newMethodInfo)
#                if newMethodInfoList:
#                    newAllMethodsInfo[method] = newMethodInfoList
#            if newAllMethodsInfo:
#                newApiDocs[mfn] = {'methods': newAllMethodsInfo }
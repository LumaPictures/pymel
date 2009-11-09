#from pymel.core import factories
from pymel import mayahook
        
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

    mayahook.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands', compressed=False )
    
    mayahook.writeCache( examples, 
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=False )

def upgradeCaches():
    data = list(mayahook.loadCache('mayaCmdsList',compressed=False))
    cmdlist = data[0]
    nodeHierarchy = data[1]
    cmdDocList = {}
    examples = {}
    succ = fail = 0
    for cmdName, cmdInfo in cmdlist.iteritems():
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
    
    mayahook.writeCache( tuple(data), 
                          'mayaCmdsList', 'the list of Maya commands',compressed=True )
    
    mayahook.writeCache( cmdDocList, 
                          'mayaCmdsDocs', 'the Maya command documentation',compressed=True )

    mayahook.writeCache( examples, 
                          'mayaCmdsExamples', 'the list of Maya command examples',compressed=True )

#    for cache, useVersion in [ ('mayaApiMelBridge',False), ('mayaApi',True) ]:
#        data = mayahook.loadCache(cache, useVersion=useVersion, compressed=False)
#        mayahook.writeCache(data, cache, useVersion=useVersion, compressed=True)
        
def addCallbackFlags():
    succ = 0
    for cmdName, cmdInfo in factories.cmdlist.iteritems():
        flags = factories.getCallbackFlags(cmdInfo)
        if flags:
            factories.cmdlist[cmdName]['callbackFlags'] = flags
            succ += 1
    print "added", succ
    mayahook.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands' )
    
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
    mayahook.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands' )

def simplifyArgs():
    succ = 0
    for cmdName, cmdInfo in factories.cmdlist.iteritems():
        if 'flags' in cmdInfo:
            cmdInfo['description'] = 0
            for flag, flagInfo in cmdInfo['flags'].iteritems():
                flagInfo['args'] = 0
                flagInfo['docstring'] = 0

def flattenNodeHier():
    
    hierarchy = [ (x.key, tuple( [y.key for y in x.parents()]) ) for x in factories.nodeHierarchy.preorder() ]
    factories.nodeHierarchy = hierarchy
    mayahook.writeCache( (factories.cmdlist,
                          factories.nodeHierarchy,
                          factories.uiClassList,
                          factories.nodeCommandList,
                          factories.moduleCmds), 
                          'mayaCmdsList', 'the list of Maya commands' )

caches = [ ('mayaCmdsList', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]
def mergeAll():
    data = []
    for cache, useVersion in caches:
        data.append( mayahook.loadCache(cache, useVersion=useVersion))

    mayahook.writeCache( tuple(data), 'mayaAll' )


import time
def mergedTest():
    s1 = time.time()
    for cache, useVersion in caches:
        mayahook.loadCache(cache, useVersion=useVersion)
    print time.time()-s1
    
    s2 = time.time()
    mayahook.loadCache('mayaAll')
    print time.time() - s2
    

def compress():
    for cache, useVersion in caches + [('mayaCmdsListAll', True), ('mayaCmdsDocs', True) ]:
        data = mayahook.loadCache(cache, useVersion=useVersion, compressed=False)
        mayahook.writeCache(data, cache, useVersion=useVersion, compressed=True)

def decompress():
    caches2 = [ ('mayaCmdsListAll', True), ('mayaApiMelBridge',False), ('mayaApi',True) ]
    
    num = 3
    
    s = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = mayahook.loadCache(cache, useVersion=useVersion, compressed=False)
    print "compress=0, docstrings=1:", time.time()-s
    
    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayahook.loadCache(cache, useVersion=useVersion, compressed=False)
    print "compress=0, docstrings=0:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches2:
            data = mayahook.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=1:", time.time()-s1

    s1 = time.time()
    for i in range(num):
        for cache, useVersion in caches:
            data = mayahook.loadCache(cache, useVersion=useVersion, compressed=True)
    print "compress=1, docstrings=0:", time.time()-s1


     
                    
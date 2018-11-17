#!/usr/bin/env mayapy
import pymel.internal.apicache as apicache
import pymel.internal.cmdcache as cmdcache
print apicache
import pymel.internal.startup
print pymel.internal.startup

logger = pymel.internal.startup._logger

cacheClasses = (
#   apicache.ApiMelBridgeCache,
   apicache.ApiCache,
   cmdcache.CmdExamplesCache,
   cmdcache.CmdDocsCache,
    cmdcache.CmdCache,
)

#version = '2017'
version = None

for cacheClass in cacheClasses:
    def getCache():
        cacheInst = cacheClass()
        if version is not None:
            cacheInst.version = version
        return cacheInst

    cacheInst = getCache()
    data = cacheInst.read(ext='.zip')

    newExt = '.py'
    newZipExt = newExt + '.zip'
    cacheInst.write(data, ext=newExt)

    cacheInst2 = getCache()
    newData = cacheInst2.read(ext=newExt)

    cacheInst.write(data, ext=newZipExt)
    cacheInst3 = getCache()
    newZipData = cacheInst3.read(ext=newZipExt)
    assert newZipData == newData

    from pymel.util.arguments import compareCascadingDicts
    from pprint import pprint, pformat

    diffs = compareCascadingDicts(data, newData)[-1]

    if not diffs:
        print "Yay!!! no diffs!"
    else:
        print "Boo... still diffs..."

        diffPath = cacheInst.path(ext='.diff')
        with open(diffPath, 'w') as f:
            f.write(pformat(diffs))
        print "wrote diffs to: {}".format(diffPath)
        break



from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
#!/usr/bin/env mayapy
import inspect
import os
import sys

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)
PYMEL_ROOT = os.path.dirname(THIS_DIR)

sys.path.insert(0, PYMEL_ROOT)

import pymel.internal.apicache as apicache
import pymel.internal.startup

import pymel.util as _util

logger = pymel.internal.startup._logger

bridgeCache = apicache.ApiMelBridgeCache()
bridgeCache.load()
print("read: {}".format(bridgeCache.path()))

for version in apicache.ApiCache.allVersions():
    cacheInst = apicache.ApiCache()
    cacheInst.version = version
    cacheInst.load()

    print("updating: {}".format(cacheInst.path()))
    _util.mergeCascadingDicts(bridgeCache.apiClassOverrides, cacheInst.apiClassInfo,
                              allowDictToListMerging=True)
    cacheInst.save()



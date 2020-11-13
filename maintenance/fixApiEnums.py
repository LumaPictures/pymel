#!/usr/bin/env mayapy

import inspect
import os

import pymel.internal.apicache as apicache
# import pymel.versions as versions
#
# pymel_file = os.normpath(os.abspath(inspect.getsourcefile(pymel)))
# pymel_dir = os.dirname(pymel_file)
# cache_dir = os.path.join(pymel_dir, 'cache')
#
# maya_ver_num = str(versions.current())[:4]
# api_cache_filename = 'mayaApi{}.py'.format(maya_ver_num)
# api_cache_path = os.path.join(cache_dir, api_cache_filename)

cacheInst = apicache.ApiCache()
cacheInst.load()
cacheInst._buildApiTypesList()
cacheInst.save()


"""
General utilities which are pymel-independent.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import sys
import codecs
import os
import os.path
import re
import platform

from collections import *

from .common import *
from .arguments import (
    isIterable, isScalar, isNumeric, isSequence, isMapping, clsname, convertListArgs,
    expandArgs, preorderArgs, postorderArgs, breadthArgs, iterateArgs,
    preorderIterArgs, postorderIterArgs, breadthIterArgs, preorder, postorder,
    breadth, listForNone, pairIter, reorder, RemovedKey, AddedKey, ChangedKey,
    compareCascadingDicts, mergeCascadingDicts, setCascadingDictItem,
    getCascadingDictItem, deepPatch, deepPatchAltered, sequenceToSlices,
    izip_longest)
from .utilitytypes import (
    Singleton, defaultdict, metaStatic, defaultlist, ModuleInterceptor,
    readonly, metaReadOnlyAttr, proxyClass, ProxyUnicode, universalmethod,
    LazyLoadModule, LazyDocStringError, LazyDocString, addLazyDocString, TwoWayDict,
    EquivalencePairs, alias, propertycache)
from .arrays import *
from .enum import *
from .path import *
from .decoration import *
from .shell import *

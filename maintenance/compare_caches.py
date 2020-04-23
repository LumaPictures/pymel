#execfile(r'D:\Projects\Dev\pymel\maintenance\compare_caches.py')

import os
import re
import types

import pymel.internal.apicache as apicache
import pymel.internal.parsers as parsers
import pymel.internal.startup
import pymel.util.arguments as arguments

from pprint import pprint

from pymel.util.enum import Enum
from pymel.util.arguments import AddedKey, ChangedKey, RemovedKey

cachedir = r'D:\Projects\Dev\pymel\pymel\cache'

names = {
    'old': 'mayaApi2020.py',
    'new': 'mayaApi2021.py',
}

DO_PREPROCESS = False

def preprocess(cache):
    apiClassInfo = cache[-1]
    # remove skipped entries
    for clsname in list(apiClassInfo):
        if parsers.ApiDocParser.shouldSkip(clsname):
            apiClassInfo.pop(clsname, None)
    for clsname, methName in parsers.XmlApiDocParser.SKIP_PARSING_METHODS:
        apiClassInfo.get(clsname, {})['methods'].pop(methName, None)

    for clsInfo in apiClassInfo.values():
        for overloads in clsInfo['methods'].values():
            for methInfo in overloads:
                argInfo = methInfo['argInfo']
                quals = methInfo.get('typeQualifiers', {})
                for argName, argQuals in list(quals.items()):
                    if argName not in argInfo or not argQuals:
                        del quals[argName]

    return cache

caches = {}
for key, cachename in names.items():
    cachepath = os.path.join(cachedir, cachename)
    cache_globals = {}
    cacheInst = apicache.ApiCache()
    data = cacheInst.read(path=cachepath)
    if DO_PREPROCESS:
        data = preprocess(data)
        cachepath_namebase, cachepath_ext = os.path.splitext(cachepath)
        preprocessed_path = cachepath_namebase + '.preprocessed' + cachepath_ext
        cacheInst.write(data, path=preprocessed_path)
    caches[key] = data

# we only care about the diffs of the classInfo
both, onlyOld, onlyNew, diffs = arguments.compareCascadingDicts(
    caches['old'][-1],
    caches['new'][-1],
    useAddedKeys=True, useChangedKeys=True)

#eliminate known diffs

################################################################################

# # {'methods': {'className': {0: {'doc': ChangedKey('Class name.', 'Returns the name of this class.'),
#                                'returnInfo': {'doc': ChangedKey('', 'Name of this class.')},
#                                'static': ChangedKey(False, True)}},
#              'type': {0: {'doc': ChangedKey('Function set type.', 'Function set type'),
#                           'returnInfo': {'doc': ChangedKey('', 'the class type.')}}}}}


# Doc for 'className' method got more verbose, and it became static
#'className': {0: {'doc': ChangedKey('Class name.', 'Returns the name of this class.')

for clsname, clsDiffs in diffs.items():
    if not isinstance(clsDiffs, dict):
        continue
    methods = clsDiffs.get('methods')
    if not methods:
        continue
    methodDiffs = methods.get('className')
    if not methodDiffs:
        continue
    for overloadIndex, overloadDiffs in methodDiffs.iteritems():
        docDiff = overloadDiffs.get('doc')
        if docDiff and isinstance(docDiff, ChangedKey):
            if set([
                        docDiff.oldVal.lower().rstrip('.'),
                        docDiff.newVal.lower().rstrip('.'),
                    ]) == set([
                        'class name',
                        'returns the name of this class',
                    ]):
                del overloadDiffs['doc']
        staticDiff = overloadDiffs.get('static')
        if (isinstance(staticDiff, ChangedKey)
                and not staticDiff.oldVal
                and staticDiff.newVal):
            del overloadDiffs['static']

################################################################################

# It's ok if it didn't use to have a doc, and now it does
def hasNewDoc(arg):
    if not isinstance(arg, dict):
        return False
    doc = arg.get('doc')
    if not doc:
        return False
    if isinstance(doc, AddedKey):
        return True
    if isinstance(doc, ChangedKey):
        if not doc.oldVal:
            return True
    return False

def removeDocDiff(arg):
    del arg['doc']
    return arg
arguments.deepPatchAltered(diffs, hasNewDoc, removeDocDiff)

################################################################################

# It's ok if the doc is now longer
# (as long as it doesn't now include "\param" or "\return" codes)
def hasLongerDoc(arg):
    if not isinstance(arg, dict):
        return False
    doc = arg.get('doc')
    if not doc:
        return False
    if isinstance(doc, ChangedKey):
        if not doc.newVal.startswith(doc.oldVal):
            return False
        extraDoc = doc.newVal[len(doc.oldVal):]
        return '\\param' not in extraDoc and '\\return' not in extraDoc
    return False

arguments.deepPatchAltered(diffs, hasLongerDoc, removeDocDiff)

################################################################################

# It's ok if the doc is now shorter, if it seems to have been truncated at a
# sentence end.
def wasTrimmedToSentence(arg):
    if not isinstance(arg, dict):
        return False
    doc = arg.get('doc')
    if not doc:
        return False
    if isinstance(doc, ChangedKey):
        if not doc.oldVal.startswith(doc.newVal):
            return False
        if not doc.newVal.endswith('.'):
            return False
        return doc.oldVal[len(doc.newVal)] == ' '
    return False

arguments.deepPatchAltered(diffs, wasTrimmedToSentence, removeDocDiff)

################################################################################

# ignore changes in only capitalization or punctuation
# ...also strip out any "\\li " or <b>/</b> items
# ...or whitespace length...
PUNCTUATION = """;-'"`,."""
def strip_punctuation(input):
    return input.translate(None, PUNCTUATION)

MULTI_SPACE_RE = re.compile('\s+')

def normalize_str(input):
    result = strip_punctuation(input.lower())
    result = result.replace(' \\li ', ' ')
    result = result.replace('<b>', '')
    result = result.replace('</b>', '')
    result = result.replace('\n', '')
    result = MULTI_SPACE_RE.sub(' ', result)
    return result

def same_after_normalize(input):
    if not isinstance(input, ChangedKey):
        return False
    if not isinstance(input.oldVal, basestring) or not isinstance(input.newVal, basestring):
        return False
    return normalize_str(input.oldVal) == normalize_str(input.newVal)

def returnNone(input):
    return None

arguments.deepPatchAltered(diffs, same_after_normalize, returnNone)

################################################################################

# {'enums': {'ColorTable': {'valueDocs': {'activeColors': RemovedKey('Colors for active objects.'),
#                                         'backgroundColor': RemovedKey('Colors for background color.'),
#                                         'dormantColors': RemovedKey('Colors for dormant objects.'),
#                                         'kActiveColors': RemovedKey('Colors for active objects.'),
#                                         'kBackgroundColor': RemovedKey('Colors for background color.'),
#                                         'kDormantColors': RemovedKey('Colors for dormant objects.'),
#                                         'kTemplateColor': RemovedKey('Colors for templated objects.'),
#                                         'templateColor': RemovedKey('Colors for templated objects.')}},

# enums are now recorded in a way where there's no documentation for values...
for clsname, clsDiffs in diffs.items():
    if not isinstance(clsDiffs, dict):
        continue
    enums = clsDiffs.get('enums')
    if not enums:
        continue
    for enumName in list(enums):
        enumDiffs = enums[enumName]
        if not isinstance(enumDiffs, dict):
            continue
        valueDocs = enumDiffs.get('valueDocs')
        if not valueDocs:
            continue
        if all(isinstance(val, arguments.RemovedKey) for val in valueDocs.values()):
            del enumDiffs['valueDocs']
        if not enumDiffs:
            del enums[enumName]
    if not enums:
        del clsDiffs['enums']
    if not clsDiffs:
        del diffs[clsname]

################################################################################
# Enums that have new values added are ok
def enums_with_new_values(input):
    if not isinstance(input, ChangedKey):
        return False
    oldVal = input.oldVal
    newVal = input.newVal
    if not (isinstance(oldVal, Enum) and isinstance(newVal, Enum)):
        return False
    if oldVal.name != newVal.name:
        return False
    oldKeys = set(oldVal._keys)
    newKeys = set(newVal._keys)
    if not newKeys.issuperset(oldKeys):
        return False
    onlyNewKeys = newKeys - oldKeys
    prunedNewKeyDict = dict(newVal._keys)
    prunedNewDocDict = dict(newVal._docs)
    for k in onlyNewKeys:
        del prunedNewKeyDict[k]
        prunedNewDocDict.pop(k, None)
    if not prunedNewKeyDict == oldVal._keys:
        return False
    if not prunedNewDocDict == oldVal._docs:
        return False
    return True


arguments.deepPatchAltered(diffs, enums_with_new_values, returnNone)
################################################################################

# new methods are ok
for clsname, clsDiffs in diffs.items():
    if not isinstance(clsDiffs, dict):
        continue
    methods = clsDiffs.get('methods')
    if not methods or not isinstance(methods, dict):
        continue
    to_remove = []
    for methodName in list(methods):
        methodDiff = methods[methodName]
        if isinstance(methodDiff, AddedKey):
            del methods[methodName]

################################################################################

# new classes are ok
for clsname, clsDiffs in list(diffs.items()):
    if isinstance(clsDiffs, AddedKey):
        del diffs[clsname]

################################################################################

# Lost docs

# these params or methods no longer have documentation in the xml... not great,
# but nothing the xml parser can do about that

# LOST_ALL_DETAIL_DOCS = {
#     ('MColor', 'methods', 'get', 1,),
#     ('MColor', 'methods', 'get', 2,),
# }
#
# for multiKey in LOST_ALL_DETAIL_DOCS:
#     try:
#         overloadInfo = arguments.getCascadingDictItem(diffs, multiKey)
#     except KeyError:
#         continue
#     if not isinstance(overloadInfo, dict):
#         continue
#
#     # deal with missing returnInfo doc
#     returnInfo = overloadInfo.get('returnInfo')
#     if isinstance(returnInfo, dict):
#         doc = returnInfo.get('doc')
#         if (isinstance(doc, arguments.RemovedKey)
#                 or (isinstance(doc, ChangedKey)
#                     and not doc.newVal)):
#             del returnInfo['doc']
#
#     # deal with missing param docs
#     argInfo = overloadInfo.get('argInfo')
#     if not isinstance(argInfo, dict):
#         continue
#     for argName, argDiff in argInfo.items():
#         if not isinstance(argDiff, dict):
#             continue
#         doc = argDiff.get('doc')
#         if (isinstance(doc, arguments.RemovedKey)
#                 or (isinstance(doc, ChangedKey)
#                     and not doc.newVal)):
#             del argDiff['doc']

# Temp - ignore all doc deletion diffs

for clsDiff in diffs.values():
    if not isinstance(clsDiff, dict):
        continue
    methods = clsDiff.get('methods')
    if not isinstance(methods, dict):
        continue
    for methodsDiff in methods.values():
        if not isinstance(methodsDiff, dict):
            continue
        for overloadDiff in methodsDiff.values():
            if not isinstance(overloadDiff, dict):
                continue
            # ignore method doc removal
            doc = overloadDiff.get('doc')
            if (isinstance(doc, arguments.RemovedKey)
                    or (isinstance(doc, ChangedKey)
                        and not doc.newVal)):
                del overloadDiff['doc']

            # ignore returnInfo doc removal
            returnInfo = overloadDiff.get('returnInfo')
            if isinstance(returnInfo, dict):
                doc = returnInfo.get('doc')
                if (isinstance(doc, arguments.RemovedKey)
                        or (isinstance(doc, ChangedKey)
                            and not doc.newVal)):
                    del returnInfo['doc']

            # ignore param doc removal
            argInfo = overloadDiff.get('argInfo')
            if not isinstance(argInfo, dict):
                continue
            for argName, argDiff in argInfo.items():
                if not isinstance(argDiff, dict):
                    continue
                doc = argDiff.get('doc')
                if (isinstance(doc, arguments.RemovedKey)
                        or (isinstance(doc, ChangedKey)
                            and not doc.newVal)):
                    del argDiff['doc']

################################################################################

# Can ignore

def delDiff(multiKey):
    dictsAndKeys = []
    currentItem = diffs
    for piece in multiKey:
        dictsAndKeys.append((currentItem, piece))
        currentItem = currentItem[piece]

    for currentItem, piece in reversed(dictsAndKeys):
        del currentItem[piece]
        if currentItem:
            break

KNOWN_IGNORABLE = [
    # MFn.Type has a bunch of changes each year...
    ('MFn', 'enums', 'Type'),
    ('MFn', 'pymelEnums', 'Type'),
]

for multiKey in KNOWN_IGNORABLE:
    delDiff(multiKey)

################################################################################

# MFnDependencyNode.isNameLocked/setNameLocked haven't existed on the node
# since 2017 (though they still appeared in the xml in 2019). They never
# seem to have been in the official docs...

mfnDepDiffs = diffs.get('MFnDependencyNode', {})
methodDiffs = mfnDepDiffs.get('methods', {})
for methName in ('isNameLocked', 'setNameLocked'):
    methDiff = methodDiffs.get(methName)
    if isinstance(methDiff, arguments.RemovedKey):
        del methodDiffs[methName]
invertDiffs = mfnDepDiffs.get('invertibles', {})
if (invertDiffs.get(4) == {0: ChangedKey('setNameLocked', 'setUuid'),
                           1: ChangedKey('isNameLocked', 'uuid')}
        and invertDiffs.get(5) == RemovedKey(('setUuid', 'uuid'))):
    del invertDiffs[4]
    del invertDiffs[5]

################################################################################

# KNOWN PROBLEMS

KNOWN_PROBLEMS = [
    # These methods got removed - need to figure out why
    ('MColor', 'methods', '__imul__'),
    ('MColor', 'methods', '__mul__'),
    ('MEulerRotation', 'methods', '__imul__'),
    ('MEulerRotation', 'methods', '__mul__'),
    ('MFloatMatrix', 'methods', '__imul__'),
    ('MFloatMatrix', 'methods', '__mul__'),
    ('MFloatPoint', 'methods', '__imul__'),
    ('MFloatPoint', 'methods', '__mul__'),
    ('MFloatVector', 'methods', '__imul__'),
    ('MFloatVector', 'methods', '__mul__'),
    ('MTime', 'methods', '__imul__'),
    ('MTime', 'methods', '__isub__'),
    ('MTime', 'methods', '__mul__'),
    ('MTime', 'methods', '__ne__'),
    ('MTime', 'methods', '__sub__'),
]

for multiKey in KNOWN_PROBLEMS:
    delDiff(multiKey)


################################################################################

# clean up any diff dicts that are now empty
def pruneEmpty(diffs):
    def isempty(arg):
        return isinstance(arg, (dict, list, tuple, set, types.NoneType)) and not arg

    def hasEmptyChildren(arg):
        if not isinstance(arg, dict):
            return False
        return any(isempty(child) for child in arg.values())

    def pruneEmptyChildren(arg):
        keysToDel = []
        for key, val in arg.items():
            if isempty(val):
                keysToDel.append(key)
        for key in keysToDel:
            del arg[key]
        return arg

    altered = True        

    while altered:
        diffs, altered = arguments.deepPatchAltered(diffs, hasEmptyChildren, pruneEmptyChildren)
    return diffs

# afterPrune = pruneEmpty({'foo': 7, 'bar': {5:None, 8:None}})
# print(afterPrune)
diffs = pruneEmpty(diffs)
diff_classes = sorted(diffs)

print('###########')
print("Num diffs: {}".format(len(diffs)))
print('###########')
print("diff_classes:")
for cls in diff_classes:
    print("  " + str(cls))
print('###########')
print(diff_classes[0])
pprint(diffs[diff_classes[0]])
print('###########')

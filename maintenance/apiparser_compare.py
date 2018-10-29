#!/usr/bin/env mayapy
'''Tools for writing out the apiClassInfo parsed from docs, and comparing

Written for transitioning to doxygen-xml docs, so we can compare to old results'''

import argparse
import inspect
import os
import re
import sys

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)

pymelSrcDir = os.path.dirname(THIS_DIR)

if sys.path[0] != pymelSrcDir:
    sys.path.insert(0, pymelSrcDir)

import pymel.internal.parsers as parsers
from pymel.internal.parsers import ApiDocParser, _logger
from pymel.util import compareCascadingDicts, AddedKey, ChangedKey, RemovedKey

try:
    from pymel.internal.parsers import HtmlApiDocParser, XmlApiDocParser
    isOld = False
except ImportError:
    isOld = True
    XmlApiDocParser = HtmlApiDocParser = None

import pymel.api as api


DEFAULT_BASE_DIR = os.path.expanduser('~/Desktop/parserOutput')


# copied from apicache
class ApiEnum(tuple):

    def __str__(self):
        return '.'.join([str(x) for x in self])

    def __repr__(self):
        return '%s( %s )' % (self.__class__.__name__, super(ApiEnum, self).__repr__())

    def pymelName(self):
        import pymel.internal.factories as factories
        parts = list(self)
        pymelName = factories.apiClassNameToPymelClassName(self[0])
        if pymelName is not None:
            parts[0] = pymelName
        return '.'.join([str(x) for x in parts])


def writeClassInfo(classInfo, path):
    from pprint import pformat
    with open(path, "w") as f:
        f.write(pformat(classInfo))


def readClassInfo(path):
    import pymel.util
    with open(path, 'r') as f:
        contents = f.read()
    # we compile + exec, instead of just doing "eval", to get a more informative
    # traceback
    contents = 'result = {}\n'.format(contents)
    compiled = compile(contents, path, 'single')
    locals = {
        'Enum': pymel.util.Enum,
        'EnumValue': pymel.util.EnumValue,
    }
    exec(compiled, globals(), locals)
    return locals['result']


def iterItemsRecursive(thisValue, parents=None, parentKeys=None,
                       leavesOnly=True):
    if parents is None:
        parents = []
    if parentKeys is None:
        parentKeys = []

    def isListLike(item):
        return (isinstance(item, list) or
                (isinstance(item, tuple) and not isinstance(item, ApiEnum)))

    if not leavesOnly or not (isListLike(thisValue)
                            or isinstance(thisValue, dict)):
        yield (thisValue, parents, parentKeys)

    if isListLike(thisValue):
        # iterate backwards, so if child deletes item, iteration is still valid
        indicesItems = list(enumerate(thisValue))
        for i, subVal in reversed(indicesItems):
            newParents = parents + [thisValue]
            newParentKeys = parentKeys + [i]
            for subItem in iterItemsRecursive(subVal,
                                              parents=newParents,
                                              parentKeys=newParentKeys,
                                              leavesOnly=leavesOnly):
                yield subItem
    elif isinstance(thisValue, dict):
        # need to use items, because we may change thisValue while iterating
        # children...
        for key, subVal in thisValue.items():
            newParents = parents + [thisValue]
            newParentKeys = parentKeys + [key]
            for subItem in iterItemsRecursive(subVal,
                                              parents=newParents,
                                              parentKeys=newParentKeys,
                                              leavesOnly=leavesOnly):
                yield subItem


def parse(parsers=None, classes=None, baseDir=None, verbose=False):
    from pprint import pformat

    if not parsers:
        if isOld:
            parsers = ('html',)
        else:
            parsers = ('html', 'xml')

    classInfoByType = {}

    parserTypesLookup = {
        'html': ApiDocParser if isOld else HtmlApiDocParser,
        'xml': XmlApiDocParser,
    }
    if 'xml' in parsers and isOld:
        raise RuntimeError(
            "May not specify xml parser - current version of pymel does not"
            " support it")

    parserTypes = [parserTypesLookup[x] for x in parsers]

    verbose = False

    for parserType in parserTypes:
        parserName = parserType.__name__
        print("Starting building classInfo: {}...".format(parserName))
        apiClassInfo = {}
        classInfoByType[parserName] = apiClassInfo

        parser = parserType(api, enumClass=ApiEnum, verbose=verbose)

        if classes:
            classes = set(classes)

            def predicate(x):
                return type(x) == type and x.__name__ in classes
        else:
            def predicate(x):
                return type(x) == type and x.__name__.startswith('M') \
                    and not x.__name__.startswith('MPx')

        # for name, obj in [(name, getattr(api, name)) for name in ["MColor", "MFnMesh", "MFnMeshData", "MItMeshEdge", "MItMeshFaceVertex", "MItMeshPolygon", "MItMeshVertex", "MMeshIntersector", "MMeshIsectAccelParams", "MMeshSmoothOptions",]]:
        for name, obj in inspect.getmembers(api, predicate):
            try:
                info = parser.parse(name)
                apiClassInfo[name] = info
            except (IOError, OSError, ValueError, IndexError), e:
                import errno

                baseMsg = "failed to parse docs for %r:" % name
                if isinstance(e, (IOError, OSError)) and e.errno == errno.ENOENT:
                    # If we couldn't parse because we couldn't find the
                    # file, only raise a warning... there are many classes
                    # (ie, MClothTriangle) that don't have a doc page...
                    _logger.warning(baseMsg)
                    _logger.warning("%s: %s" % (name, e))
                else:
                    import traceback

                    _logger.error(baseMsg)
                    _logger.error(traceback.format_exc())

        print("...Finished building classInfo: {}".format(parserName))

    #
    for parserType, apiClassInfo in classInfoByType.iteritems():
        dirName = parserType
        if isOld:
            dirName += 'Old'
        outputDir = os.path.join(baseDir, dirName)
        if not os.path.isdir(outputDir):
            os.makedirs(outputDir)
        for className, classData in apiClassInfo.iteritems():
            classFile = os.path.join(outputDir, className + '.py')
            print "writing: {}".format(classFile)
            writeClassInfo(classData, classFile)
    print "done"


class Transform(object):
    """Individual transform applied to an apiClassInfo"""
    LEAVES_ONLY = True
    def xform(self, classInfo):
        for item, parents, parentKeys in iterItemsRecursive(
                classInfo, leavesOnly=self.LEAVES_ONLY):
            self.xformItem(item, parents, parentKeys)

    def xformItem(self, item, parents, parentKeys):
        raise NotImplementedError

# Do this first, as it will then allow other Transforms to alter items inside of
# tuples
class TuplesToLists(Transform):
    LEAVES_ONLY = False

    def xformItem(self, item, parents, parentKeys):
        if (isinstance(item, tuple) and not isinstance(item, ApiEnum)
                and parents):
            parents[-1][parentKeys[-1]] = list(item)


class CleanupWhitespace(Transform):
    def xformItem(self, item, parents, parentKeys):
        if isinstance(item, basestring) and parents:
            parents[-1][parentKeys[-1]] = ' '.join(item.strip().split())


class RegexpTransform(Transform):
    def __init__(self, find, replace, keyFilter=None):
        if not isinstance(find, re._pattern_type):
            find = re.compile(find)
        self.find = find
        self.replace = replace
        self.keyFilter = keyFilter

    def xformItem(self, item, parents, parentKeys):
        if isinstance(item, basestring) and parents:
            parents[-1][parentKeys[-1]] = self.fine.sub(self.replace, item)


class RemoveNoScriptDocs(Transform):
    def xformItem(self, item, parents, parentKeys):
        if (parentKeys[-1] == 'doc' and isinstance(item, basestring)
                and 'NO SCRIPT SUPPORT' in item and len(parents) > 1):
            del parents[-2][parentKeys[-2]]


class Processor(object):
    """Used to massage / format raw classInfo data to make for easier
    comparisons."""
    AUTO_TUPLES_TO_LISTS = True

    def __init__(self, xforms):
        self.xforms = list(xforms)
        if self.AUTO_TUPLES_TO_LISTS:
            self.xforms.insert(0, TuplesToLists())

    def processDir(self, dir, classes=None):
        processedItems = {}
        if classes is not None:
            classes = set(classes)
        outputDir = dir + '_processed'
        if not os.path.isdir(outputDir):
            os.makedirs(outputDir)

        contents = os.listdir(dir)
        for filename in contents:
            base, ext = os.path.splitext(filename)
            if ext == '.py' and (classes is None or base in classes):
                path = os.path.join(dir, filename)
                if os.path.isfile(path):
                    processedItems[base] = self.processFile(path, outputDir)
        return processedItems

    def processFile(self, path, outputDir):
        outPath = os.path.join(outputDir, os.path.basename(path))
        print "Processing: {}...".format(path),
        try:
            classInfo = readClassInfo(path)
            self.applyXforms(classInfo)
            writeClassInfo(classInfo, outPath)
            print "Wrote {}".format(outPath),
            return outPath
        finally:
            # add the newline
            print

    def applyXforms(self, classInfo):
        for xform in self.xforms:
            xform.xform(classInfo)


PRE_PROCESSORS = {
    'ApiDocParserOld': Processor([
        RemoveNoScriptDocs(),
        CleanupWhitespace(),
    ]),
    'HtmlApiDocParser': Processor([
    ]),
    'XmlApiDocParser': Processor([
    ]),
}


class DiffProcessor(Processor):
    AUTO_TUPLES_TO_LISTS = False

    @classmethod
    def countChanges(cls, diffDict):
        '''Recursively count number of added, removed, and changed items'''
        if not isinstance(diffDict, dict):
            raise TypeError(diffDict)
        added = 0
        removed = 0
        changed = 0
        for val in diffDict.itervalues():
            if isinstance(val, dict):
                subAdded, subRemoved, subChanged = cls.countChanges(val)
                added += subAdded
                removed += subRemoved
                changed += subChanged
            elif isinstance(val, AddedKey):
                added += 1
            elif isinstance(val, RemovedKey):
                removed += 1
            else:
                changed += 1
        return (added, removed, changed)


class DiffTransform(Transform):
    @classmethod
    def deleteEmptyRecursive(cls, item):
        '''Recursively prunes a differences dict of now-empty items

        Returns True if the given item is now completely empty, False otherwise'''
        if not isinstance(item, dict):
            return False

        isEmpty = True
        for key in list(item):
            subItem = item[key]
            if cls.deleteEmptyRecursive(subItem):
                del item[key]
            else:
                isEmpty = False
        return isEmpty

    def xform(self, diffDict):
        super(DiffTransform, self).xform(diffDict)
        # go through and remove any items that have only empty children
        self.deleteEmptyRecursive(diffDict)


class IgnoreMissingDocsInOld(DiffTransform):
    def xformItem(self, item, parents, parentKeys):
        if parentKeys[-2:] == ['returnInfo', 'doc']:
            if (isinstance(item, AddedKey)
                    or (isinstance(item, ChangedKey) and item.oldVal == '')):
                del parents[-1][parentKeys[-1]]


DIFF_PROCESSORS = {
    ('ApiDocParserOld', 'XmlApiDocParser') : DiffProcessor([
        IgnoreMissingDocsInOld()
    ]),
}


def compare(dir1, dir2, classes=None, baseDir=None):

    dirs = [os.path.join(baseDir, d) for d in (dir1, dir2)]
    processors = []
    parserTypes = []
    for inputDir in dirs:
        parserType = os.path.basename(inputDir)
        try:
            processors.append(PRE_PROCESSORS[parserType])
        except KeyError:
            raise KeyError("Unrecognized dir name: {}".format(parserType))
        parserTypes.append(parserType)

    # we need the dirs/processors in a standard order to use as a key...
    if parserTypes[1] < parserTypes[1]:
        parserTypes.reverse()
        processors.reverse()
        dirs.reverse()
    # convert parserTypes to tuple, for use as key
    parserTypes = tuple(parserTypes)

    processedItems = []
    for inputDir, processor in zip(dirs, processors):
        processedItems.append(processor.processDir(inputDir, classes=classes))

    print "finished pre-processing..."

    names = [set(x) for x in processedItems]
    combined = names[0].intersection(names[1])

    foundAnyMissing = False
    for dirNames, sourceDir in zip(names, dirs):
        missing = dirNames - combined
        if missing:
            foundAnyMissing = True
            print "Following items were missing in {}:".format(sourceDir)
            for name in sorted(dirNames):
                print '  {}'.format(name)

    foundAnyDiffs = False
    for name in sorted(combined):
        classInfos = [readClassInfo(items[name]) for items in processedItems]
        diffs = compareCascadingDicts(
            classInfos[0], classInfos[1], useAddedKeys=True,
            useChangedKeys=True)[-1]
        if not diffs:
            continue

        processor = DIFF_PROCESSORS.get(parserTypes)
        if processor is not None:
            processor.applyXforms(diffs)

        if diffs:
            if not foundAnyDiffs:
                foundAnyDiffs = True
                print "Following items had differences:"
            changeCounts = DiffProcessor.countChanges(diffs)
            print '  {0} ({1[0]} added, {1[1]} removed, {1[2]} changed)'.format(
                name, changeCounts)
            # from pprint import pprint
            # pprint(diffs)

    if not foundAnyMissing and not foundAnyDiffs:
        print "All items identical!"


def parse_cmd(args):
    parse(parsers=args.parsers, classes=args.classes, baseDir=args.base_dir,
          verbose=args.verbose)


def compare_cmd(args):
    compare(args.dir1, args.dir2, classes=args.classes, baseDir=args.base_dir)


def getParser():
    def addCommonArgs(parser):
        parser.add_argument('--base-dir', default=DEFAULT_BASE_DIR,
            help='top-level directory in which to read/write parsed output'
                 ' (default: %(default)s)')
        parser.add_argument('--classes', default='',
            help='comma-separated list of api class names to parse/compare')

    parser = argparse.ArgumentParser(description=__doc__)
    addCommonArgs(parser)
    subparsers = parser.add_subparsers(dest='mode')

    parse_subparser = subparsers.add_parser(
        'parse', help='parse docs and write out apiClassInfo for each class')
    addCommonArgs(parse_subparser)
    parse_subparser.add_argument(
        '--parser', action='append', dest='parsers', choices=('xml', 'html'),
        help='What parsers to write out data for; note that xml will only be'
             ' available if using the new pymel branch that supports it; if no'
             ' parsers are specified, will default to "html" on "old" pymel,'
             ' and "xml" and "html" on "new" python')
    parse_subparser.add_argument('-v', '--verbose', action='store_true',
                                 help='output more info when parsing')
    parse_subparser.set_defaults(func=parse_cmd)

    compare_subparser = subparsers.add_parser(
        'compare', help='compare written out apiClassInfos')
    addCommonArgs(compare_subparser)
    compare_subparser.add_argument(
        'dir1', help='First directory of parsed class infos to compare;'
                     ' if a relative dir, taken relative to BASE_DIR')
    compare_subparser.add_argument(
        'dir2', help='Second directory of parsed class infos to compare;'
                     ' if a relative dir, taken relative to BASE_DIR')
    compare_subparser.set_defaults(func=compare_cmd)
    return parser

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = getParser()
    args = parser.parse_args(argv)

    # handle arg cleanup for common args
    args.classes = [x.strip() for x in args.classes.split(',') if x.strip()]
    # call the function specified by the subparser
    args.func(args)

if __name__ == '__main__':
    main()
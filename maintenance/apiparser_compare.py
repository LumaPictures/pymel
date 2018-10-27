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
    # need these in the local namespace for the eval
    from pymel.util import Enum, EnumValue
    with open(path, 'r') as f:
        contents = f.read()
    return eval(contents)


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
    def __init__(self, xforms, autoTuplesToLists=True):
        self.xforms = list(xforms)
        if autoTuplesToLists:
            self.xforms.insert(0, TuplesToLists())

    def processDir(self, dir, classes=None):
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
                    self.processFile(path, outputDir)
        return outputDir

    def processFile(self, path, outputDir):
        outPath = os.path.join(outputDir, os.path.basename(path))
        print "Processing: {}...".format(path),
        try:
            classInfo = readClassInfo(path)
            for xform in self.xforms:
                xform.xform(classInfo)
            writeClassInfo(classInfo, outPath)
            print "Wrote {}".format(outPath),
        finally:
            # add the newline
            print


PROCESSORS = {
    'ApiDocParserOld': Processor([
        RemoveNoScriptDocs(),
        CleanupWhitespace(),
    ]),
    'HtmlApiDocParser': Processor([
    ]),
    'XmlApiDocParser': Processor([
    ]),
}



def compare(dir1, dir2, classes=None, baseDir=None):
    dir1 = os.path.join(baseDir, dir1)
    dir2 = os.path.join(baseDir, dir2)
    processors = []
    for inputDir in (dir1, dir2):
        basename = os.path.basename(inputDir)
        try:
            processors.append(PROCESSORS[basename])
        except KeyError:
            raise KeyError("Unrecognized dir name: {}".format(basename))
    outputDirs = []
    for inputDir, processor in zip((dir1, dir2), processors):
        outputDirs.append(processor.processDir(inputDir, classes=classes))


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
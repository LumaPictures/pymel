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
                       yieldParents=False, yieldLeaves=True):
    if parents is None:
        parents = []
    if parentKeys is None:
        parentKeys = []

    def isListLike(item):
        return (isinstance(item, list) or
                (isinstance(item, tuple) and not isinstance(item, ApiEnum)))

    yieldItem = (thisValue, parents, parentKeys)
    if isListLike(thisValue) or isinstance(thisValue, dict):
        if yieldParents:
            msg = (yield yieldItem)
            if msg is not None:
                # if msg is not None, a "send" command was issued, which also
                # acts like it's own next, so we need another yield... this way,
                # the "next()" issued by the for loop will get the "correct"
                # next yield, as well as handle a potential StopIteration
                # properly

                # because this tripped me a up: a yield statement that handles
                # a potential send, like this:
                #
                #     foo = yield yieldItem
                #
                # consists of two parts - the yield, and the setting of foo to
                # a value from a send (or to None, if "next()" was invoked).
                # However, the "yield" part is excecuted first, and the storing
                # of foo (from a potential send) happens second, the NEXT TIME
                # A SEND() OR NEXT() happens. That is, execution happens
                # something like this:
                #
                #   - calling func calls generator.next() / send()
                #       - generator runs statements up to yield
                #       - "yield yieldItem" portion runs
                #   - calling func gets control back
                #   - calling func calls generator.send('blah')
                #       - generator stores foo = 'blah', then continues
                #         execution until NEXT yield
                #
                # That is, the yield and the store part of the statement get
                # broken up into different "execution blocks", triggered by
                # different next() / send() statements!
                yield
            if msg == StopIteration:
                return

        if isinstance(thisValue, dict):
            # need to use items, because we may change thisValue while iterating
            # children... use list for python-3 forward compatibility
            subItems = list(thisValue.items())
        else:
            subItems = list(enumerate(thisValue))
            # iterate backwards, so if child deletes item, iteration is still valid
            subItems.reverse()

        for key, subVal in subItems:
            newParents = parents + [thisValue]
            newParentKeys = parentKeys + [key]
            subGenerator = iterItemsRecursive(subVal,
                                              parents=newParents,
                                              parentKeys=newParentKeys,
                                              yieldParents=yieldParents,
                                              yieldLeaves=yieldLeaves)
            for subItem in subGenerator:
                msg = (yield subItem)
                # if they sent a StopIteration to the toplevel generator, they
                # actually want to send it to the current lowest generator, so
                # pass the message along
                if msg is not None:
                    # still need to "consume" the send
                    yield
                    subGenerator.send(msg)


    elif yieldLeaves:
        msg = yield yieldItem
        # generally speaking, a user shouldn't call send  after a leaf item,
        # since the only message we handle is StopIteration, and that makes no
        # sense for a leaf item, which has no items to yield... but just in case
        # they do...
        if msg is not None:
            yield


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
    YIELD_PARENTS = False
    YIELD_LEAVES = True

    def xform(self, classInfo, className):
        self.currentClass = className
        self.classInfo = classInfo
        self._doXform()

    def _doXform(self):
        raise NotImplementedError

    def delAndRemoveEmptyParents(self, parents, parentKeys, startLevel=1):
        if len(parents) >= startLevel:
            del parents[-startLevel][parentKeys[-startLevel]]
        nextLevel = startLevel + 1
        while len(parents) >= nextLevel:
            if not parents[-nextLevel][parentKeys[-nextLevel]]:
                del parents[-nextLevel][parentKeys[-nextLevel]]
                nextLevel += 1
            else:
                break


class IterTransform(Transform):
    def _doXform(self):
        self.iterator = iterItemsRecursive(
            self.classInfo, yieldParents=self.YIELD_PARENTS,
            yieldLeaves=self.YIELD_LEAVES)
        for item, parents, parentKeys in self.iterator:
            self.xformItem(item, parents, parentKeys)

    def xformItem(self, item, parents, parentKeys):
        raise NotImplementedError


# Do this first, as it will then allow other Transforms to alter items inside of
# tuples
class TuplesToLists(IterTransform):
    YIELD_PARENTS = True
    YIELD_LEAVES = False

    def xformItem(self, item, parents, parentKeys):
        if (isinstance(item, tuple) and not isinstance(item, ApiEnum)
                and parents):
            parents[-1][parentKeys[-1]] = list(item)


class CleanupWhitespace(IterTransform):
    def xformItem(self, item, parents, parentKeys):
        if isinstance(item, basestring) and parents:
            # replace 'non-breaking space'
            newString = item.replace('\xc2\xa0', ' ')
            parents[-1][parentKeys[-1]] = ' '.join(newString.strip().split())


class RemoveEmptyEnumDocs(Transform):
    def _doXform(self):
        enums = self.classInfo.get('enums')
        if not enums:
            return
        for enumInfo in enums.itervalues():
            valueDocs = enumInfo.get('valueDocs')
            if not valueDocs:
                continue
            toDel = [key for key, val in valueDocs.iteritems() if val == '']
            for k in toDel:
                del valueDocs[k]
            if not valueDocs:
                del enumInfo['valueDocs']


class RegexpTransform(IterTransform):
    def __init__(self, find, replace, keyFilter=None):
        if not isinstance(find, re._pattern_type):
            find = re.compile(find)
        self.find = find
        self.replace = replace
        self.keyFilter = keyFilter

    def xformItem(self, item, parents, parentKeys):
        if isinstance(item, basestring) and parents:
            if self.keyFilter is None or self.keyFilter(parentKeys):
                parents[-1][parentKeys[-1]] = self.find.sub(self.replace, item)


class MethodTransform(Transform):
    def _doXform(self):
        self.methods = self.classInfo.get('methods')
        if not self.methods:
            return
        for self.methodName, self.overrides in list(self.methods.items()):
            # for DiffProcessor, self.overrides will be a dict, while
            # for a "normal" classInfo, it should be a list
            if isinstance(self.overrides, dict):
                indices = list(self.overrides.keys())
            elif isinstance(self.overrides, list):
                indices = range(len(self.overrides))
                indices.reverse()
            else:
                continue
            for self.overrideIndex in indices:
                self.methodInfo = self.overrides[self.overrideIndex]
                self.parents = [self.classInfo, self.methods,
                           self.overrides]
                self.parentKeys = ['methods', self.methodName,
                                   self.overrideIndex]
                self.methodXform()

    def methodXform(self):
        raise NotImplementedError

    def delCurrentMethod(self):
        self.delAndRemoveEmptyParents(self.parents, self.parentKeys)


class RemoveNoScriptDocs(MethodTransform):
    def methodXform(self):
        doc = self.methodInfo.get('doc')
        if isinstance(doc, basestring) and 'NO SCRIPT SUPPORT' in doc:
            self.delCurrentMethod()


class FixFloatDefaultStrings(MethodTransform):
    def methodXform(self):
        '''Change "2.0f" to 2.0'''
        defaults = self.methodInfo.get('defaults')
        if not isinstance(defaults, dict):
            return
        for varname, defVal in defaults.iteritems():
            if isinstance(defVal, basestring) and defVal[-1] == 'f':
                try:
                    floatVal = float(defVal[:-1])
                except ValueError:
                    pass
                else:
                    defaults[varname] = floatVal


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
        if classes:
            classes = set(classes)
        outputDir = dir + '_processed'
        if not os.path.isdir(outputDir):
            os.makedirs(outputDir)

        contents = os.listdir(dir)
        for filename in contents:
            base, ext = os.path.splitext(filename)
            if ext == '.py' and (not classes or base in classes):
                path = os.path.join(dir, filename)
                if os.path.isfile(path):
                    processedItems[base] = self.processFile(base, path,
                                                            outputDir)
        return processedItems

    def processFile(self, className, path, outputDir):
        outPath = os.path.join(outputDir, os.path.basename(path))
        print "Processing: {}...".format(path),
        try:
            classInfo = readClassInfo(path)
            self.applyXforms(className, classInfo)
            writeClassInfo(classInfo, outPath)
            print "Wrote {}".format(outPath),
            return outPath
        finally:
            # add the newline
            print

    def applyXforms(self, className, classInfo):
        for xform in self.xforms:
            xform.xform(classInfo, className)


class CleanUpInvertibles(MethodTransform):
    '''After other Transforms remove items, invertibles might no longer be
    valid - remove them'''
    def _doXform(self):
        invertibles = self.classInfo.get('invertibles')
        if invertibles:
            methods = self.classInfo.get('methods', {})

            for i in reversed(range(len(invertibles))):
                setter, getter = invertibles[i]
                if setter not in methods or getter not in methods:
                    del invertibles[i]
        super(CleanUpInvertibles, self)._doXform()

    def methodXform(self):
        inverse = self.methodInfo.get('inverse')
        if isinstance(inverse, (list, tuple)) and inverse[0] not in self.methods:
            del self.methodInfo['inverse']


PRE_PROCESSORS = {
    'ApiDocParserOld': Processor([
        RemoveNoScriptDocs(),
        CleanupWhitespace(),
        FixFloatDefaultStrings(),
        RemoveEmptyEnumDocs(),
        # clean up, ie, "myFunc() ." => "myFunc()."
        RegexpTransform(r'([\])}]) ([\.;\(\)\[\],])',
                        r'\1\2',
                        keyFilter=lambda keys: keys and keys[-1] == 'doc'),
        # clean up "MFnMesh ." => "MFnMesh."
        RegexpTransform(r'''([\w'"]) ([\.;,])''',
                        r'\1\2',
                        keyFilter=lambda keys: keys and keys[-1] == 'doc'),
        CleanUpInvertibles(),
    ]),
    'HtmlApiDocParser': Processor([
    ]),
    'XmlApiDocParser': Processor([
        RegexpTransform(r'This method is obsolete. \[From Maya 2019\]',
                        r'This method is obsolete.'),
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


class IgnoreMissingDocsInOld(MethodTransform):
    def methodXform(self):
        if not isinstance(self.methodInfo, dict):
            return
        returnInfo = self.methodInfo.get('returnInfo')
        if not isinstance(returnInfo, dict):
            return
        doc = returnInfo.get('doc')
        if (isinstance(doc, AddedKey)
                or (isinstance(doc, ChangedKey) and doc.oldVal == '')):
            parents = self.parents + [self.methodInfo, returnInfo]
            parentKeys = self.parentKeys + ['returnInfo', 'doc']
            self.delAndRemoveEmptyParents(parents, parentKeys)


class IgnoreKnownNew2019Funcs(Transform):
    NEW_METHODS = {
        'MFnMesh': {
            'create': [6],
            'createColorSetDataMesh': True,
            'createColorSetWithNameDataMesh': True,
            'createUVSetDataMesh': True,
            'createUVSetDataMeshWithName': True,
            'objectChanged': True,
        }
    }

    def _doXform(self):
        newClassMethods = self.NEW_METHODS.get(self.currentClass)
        if not newClassMethods:
            return
        allMethodChanges = self.classInfo.get('methods', {})
        if not allMethodChanges:
            return
        for methodName, overrides in newClassMethods.iteritems():
            methodChanges = allMethodChanges.get(methodName)
            if methodChanges is None:
                continue
            if isinstance(methodChanges, AddedKey) and overrides is True:
                del allMethodChanges[methodName]
            elif isinstance(methodChanges, dict):
                for overrideIndex in overrides:
                    overrideChanges = methodChanges.get(overrideIndex)
                    if isinstance(overrideChanges, AddedKey):
                        del methodChanges[overrideIndex]
                if not methodChanges:
                    del allMethodChanges[methodName]
            if not allMethodChanges:
                del self.classInfo['methods']


DIFF_PROCESSORS = {
    ('ApiDocParserOld', 'XmlApiDocParser') : DiffProcessor([
        IgnoreMissingDocsInOld(),
        IgnoreKnownNew2019Funcs(),
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
            processor.applyXforms(name, diffs)

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
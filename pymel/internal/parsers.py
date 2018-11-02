import re
import os.path
import platform
from abc import ABCMeta, abstractmethod
from HTMLParser import HTMLParser
import xml.etree.cElementTree as ET

import pymel.util as util
import pymel.versions as versions
import plogging
from pymel.mayautils import getMayaLocation

try:
    from pymel.util.external.BeautifulSoup import BeautifulSoup, NavigableString
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup, NavigableString
    except ImportError:
        BeautifulSoup = None
        NavigableString = None

from keyword import iskeyword as _iskeyword

FLAGMODES = ('create', 'query', 'edit', 'multiuse')

_logger = plogging.getLogger(__name__)

def mayaIsRunning():
    """
    Returns True if maya.cmds have  False otherwise.

    Early in interactive startup it is possible for commands to exist but for Maya to not yet be initialized.

    Returns
    -------
    bool
    """

    # Implementation is essentially just a wrapper for getRunningMayaVersionString -
    # this function was included for clearer / more readable code

    try:
        from maya.cmds import about
        about(version=True)
        return True
    except:
        return False

def mayaDocsLocation(version=None):
    docLocation = os.environ.get('MAYA_DOC_DIR')

    if (not docLocation and (version is None or version == versions.installName())
            and mayaIsRunning()):
        # Return the doc location for the running version of maya
        from maya.cmds import showHelp
        docLocation = showHelp("", q=True, docs=True)

        # Older implementations had no trailing slash, but the result returned by
        # showHelp has a trailing slash... so eliminate any trailing slashes for
        # consistency
        while docLocation != "" and os.path.basename(docLocation) == "":
            docLocation = os.path.dirname(docLocation)

    # Want the docs for a different version, or maya isn't initialized yet
    if not docLocation or not os.path.isdir(docLocation):
        docBaseDir = os.environ.get('MAYA_DOC_BASE_DIR')
        if not docBaseDir:
            docBaseDir = getMayaLocation(version)  # use original version
            if docBaseDir is None and version is not None:
                docBaseDir = getMayaLocation(None)
                _logger.warning("Could not find an installed Maya for exact version %s, using first installed Maya location found in %s" % (version, docBaseDir))

            if platform.system() == 'Darwin':
                docBaseDir = os.path.dirname(os.path.dirname(docBaseDir))
            docBaseDir = os.path.join(docBaseDir, 'docs')

        if version:
            short_version = versions.parseVersionStr(version, extension=False)
        else:
            short_version = versions.shortName()
        docLocation = os.path.join(docBaseDir, 'Maya%s' % short_version, 'en_US')

    return os.path.realpath(docLocation)


def iterXmlTextAndElem(element):
    '''Like Element.itertext, except returns a tuple of (text, element, isTail)'''
    tag = element.tag
    if not isinstance(tag, basestring) and tag is not None:
        return
    if element.text:
        yield (element.text, element, False)
    for e in element:
        for s in iterXmlTextAndElem(e):
            yield s
        if e.tail:
            yield (e.tail, e, True)


def getFirstText(element, ignore=('ref', 'bold', 'emphasis')):
    '''Finds a non-empty text element, then stops once it hits not first non-filtered sub-element

    >>> getFirstText(ET.fromstring('<top>Some text. <sub>Blah</sub> tail.</top>'))
    'Some text.'
    >>> getFirstText(ET.fromstring('<top><sub>Blah blah</sub> More stuff</top>'))
    'Blah blah'
    >>> getFirstText(ET.fromstring('<top> <sub>Blah blah <ref>someRef</ref> More stuff</sub> The end</top>'))
    'Blah blah someRef More stuff'
    '''
    chunks = []
    foundText = False

    for text, elem, isTail in iterXmlTextAndElem(element):
        if foundText:
            if elem.tag not in ignore:
                break
        elif text.strip():
            foundText = True
        chunks.append(text)

    return ''.join(chunks).strip()


def xmlText(element, strip=True, allowNone=True):
    '''Given an xml Element object, returns it's full text (with children)

    If predicate is given, and it returns False for this element or any child,
    then text generation will be terminated at that point.
    '''
    if allowNone and element is None:
        return ''
    text = "".join(element.itertext())
    if strip:
        text = text.strip()
    return text


def standardizeWhitespace(text):
    return ' '.join(text.strip().split())

# Thanks to Eloff for this snippet: https://stackoverflow.com/a/925630/920545
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


#---------------------------------------------------------------
#        Doc Parser
#---------------------------------------------------------------
class CommandDocParser(HTMLParser):

    _lettersRe = re.compile('([a-zA-Z]+)')

    def __init__(self, command):
        self.command = command
        self.flags = {}  # shortname, args, docstring, and a list of modes (i.e. edit, create, query)
        self.currFlag = ''
        # iData is used to track which type of data we are putting into flags, and corresponds with self.datatypes
        self.iData = 0
        self.pcount = 0
        self.active = False  # this is set once we reach the portion of the document that we want to parse
        self.description = ''
        self.example = ''
        self.emptyModeFlags = []  # when flags are in a sequence ( lable1, label2, label3 ), only the last flag has queryedit modes. we must gather them up and fill them when the last one ends
        HTMLParser.__init__(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.command)

    def startFlag(self, data):
        #_logger.debug(self, data)
        #assert data == self.currFlag
        self.iData = 0
        self.flags[self.currFlag] = {'longname': self.currFlag, 'shortname': None, 'args': None,
                                     'numArgs': None, 'docstring': '', 'modes': []}

    def addFlagData(self, data):
        # encode our non-unicode 'data' string to unicode
        data = data.decode('utf-8')
        # now saftely encode it to non-unicode ascii, ignorning unknown characters
        data = data.encode('ascii', 'ignore')
        # Shortname
        if self.iData == 0:
            self.flags[self.currFlag]['shortname'] = data.lstrip('-\r\n')

        # Arguments
        elif self.iData == 1:
            typemap = {
                'string': unicode,
                'float': float,
                'double': float,
                'linear': float,
                'angle': float,
                'int': int,
                'uint': int,
                'int64': int,
                'index': int,
                'integer': int,
                'boolean': bool,
                'script': 'script',
                'name': 'PyNode',
                'select': 'PyNode',
                'time': 'time',
                'timerange': 'timerange',
                'floatrange': 'floatrange',
                '...': '...'  # means that there is a variable number of args. we don't do anything with this yet
            }
            args = [x.strip() for x in data.replace('[', '').replace(']', '').split(',') if x.strip()]
            for i, arg in enumerate(args):
                if arg not in typemap:
                    _logger.error("%s: %s: unknown arg type %r" % (self, self.currFlag, arg))
                else:
                    args[i] = typemap[arg]
            numArgs = len(args)
            if numArgs == 0:
                args = bool
                #numArgs = 1
                # numArgs will stay at 0, which is the number of mel arguments.
                # this flag should be renamed to numMelArgs
            elif numArgs == 1:
                args = args[0]

            self.flags[self.currFlag]['args'] = args
            self.flags[self.currFlag]['numArgs'] = numArgs

        # Docstring
        else:
            #self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).strip() + " "
            data = data.replace('In query mode, this flag needs a value.', '')
            data = data.replace('Flag can appear in Create mode of command', '')
            data = data.replace('Flag can appear in Edit mode of command', '')
            data = data.replace('Flag can appear in Query mode of command', '')
            data = data.replace('\r\n', ' ').lstrip()
            data = data.replace('\n', ' ').lstrip()
            data = data.strip('{}\t')
            data = data.replace('*', '\*')  # for reStructuredText
            self.flags[self.currFlag]['docstring'] += data
        self.iData += 1

    def endFlag(self):
        # cleanup last flag
        #data = self.flags[self.currFlag]['docstring']

        #_logger.debug(("ASSERT", data.pop(0), self.currFlag))
        try:
            if not self.flags[self.currFlag]['modes']:
                self.emptyModeFlags.append(self.currFlag)
            elif self.emptyModeFlags:
                    #_logger.debug("past empty flags:", self.command, self.emptyModeFlags, self.currFlag)
                basename = self._lettersRe.match(self.currFlag).groups()[0]
                modes = self.flags[self.currFlag]['modes']
                self.emptyModeFlags.reverse()
                for flag in self.emptyModeFlags:
                    if self._lettersRe.match(flag).groups()[0] == basename:
                        self.flags[flag]['modes'] = modes
                    else:
                        break

                self.emptyModeFlags = []
        except KeyError, msg:
            pass
            #_logger.debug(self.currFlag, msg)

    def handle_starttag(self, tag, attrs):
        #_logger.debug("begin: %s tag: %s" % (tag, attrs))
        attrmap = dict(attrs)
        if not self.active:
            if tag == 'a':
                name = attrmap.get('name', None)
                if name == 'hFlags':
                    #_logger.debug('ACTIVE')
                    self.active = 'flag'
                elif name == 'hExamples':
                    #_logger.debug("start examples")
                    self.active = 'examples'
        elif tag == 'a' and 'name' in attrmap:
            self.endFlag()
            newFlag = attrmap['name'][4:]
            newFlag = newFlag.lstrip('-')
            self.currFlag = newFlag
            self.iData = 0
            #_logger.debug("NEW FLAG", attrs)
            #self.currFlag = attrs[0][1][4:]

        elif tag == 'img':
            mode = attrmap.get('title', None)
            if mode in FLAGMODES:
                #_logger.debug("MODES", attrs[1][1])
                self.flags[self.currFlag]['modes'].append(mode)
        elif tag == 'h2':
            self.active = False

    def handle_endtag(self, tag):
        #if tag == 'p' and self.active == 'command': self.active = False
        #_logger.debug("end: %s" % tag)
        if not self.active:
            if tag == 'p':
                if self.pcount == 3:
                    self.active = 'command'
                else:
                    self.pcount += 1
        elif self.active == 'examples' and tag == 'pre':
            self.active = False

    def handle_entityref(self, name):
        if self.active == 'examples':
            self.example += r'"'

    def handle_data(self, data):
        if not self.active:
            return
        elif self.active == 'flag':
            if self.currFlag:
                stripped = data.strip()
                if stripped == 'Return value':
                    self.active = False
                    return

                if data and stripped and stripped not in ['(', ')', '=', '], [']:
                    #_logger.debug("DATA", data)

                    if self.currFlag in self.flags:
                        self.addFlagData(data)
                    else:
                        self.startFlag(data)
        elif self.active == 'command':
            data = data.replace('\r\n', ' ')
            data = data.replace('\n', ' ')
            data = data.lstrip()
            data = data.strip('{}')
            data = data.replace('*', '\*')  # for reStructuredText
            if '{' not in data and '}' not in data:
                self.description += data
            #_logger.debug(data)
            #self.active = False
        elif self.active == 'examples' and data != 'Python examples':
            #_logger.debug("Example\n")
            #_logger.debug(data)
            data = data.replace('\r\n', '\n')
            self.example += data
            #self.active = False


# class MayaDocsLoc(str) :
#    """ Path to the Maya docs, cached at pymel start """
#    __metaclass__ = util.Singleton

# TODO : cache doc location or it's evaluated for each getCmdInfo !
# MayaDocsLoc(mayaDocsLocation())

class NodeHierarchyDocParser(HTMLParser):

    def parse(self):
        docloc = mayaDocsLocation(self.version)
        if not os.path.isdir(docloc):
            raise IOError, "Cannot find maya documentation. Expected to find it at %s" % docloc

        f = open(os.path.join(docloc, 'Nodes/index_hierarchy.html'))
        try:
            rawdata = f.read()
        finally:
            f.close()

        if versions.v2011 <= versions.current() < versions.v2012:
            # The maya 2011 doc doesn't parse correctly with HTMLParser - the
            # '< < <' lines get left out.  Use beautiful soup instead.
            soup = BeautifulSoup(rawdata, convertEntities='html')
            for tag in soup.findAll(['tt', 'a']):
                # piggypack on current handle_starttag / handle_data
                self.handle_starttag(tag.name, tag.attrs)
                data = tag.string
                if data is not None:
                    self.handle_data(data)
        else:
            self.feed(rawdata)
        return self.tree

    def __init__(self, version=None):
        self.version = version
        self.currentTag = None
        self.depth = 0
        self.lastDepth = -1
        self.tree = None
        self.currentLeaves = []

        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        #_logger.debug("%s - %s" % (tag, attrs))
        self.currentTag = tag

    def handle_data(self, data):
        _logger.debug("data %r" % data)
        if self.currentTag == 'tt':
            self.depth = data.count('>')
            #_logger.debug("lastDepth: %s - depth: %s" % (self.lastDepth, self.depth))

        elif self.currentTag == 'a':
            data = data.lstrip()

            if self.depth == 0:
                if self.tree is None:
                    #_logger.debug("starting brand new tree: %s %s" % (self.depth, data))
                    self.tree = [data]
                else:
                    #_logger.debug("skipping %s", data)
                    return

            elif self.depth == self.lastDepth and self.depth > 0:
                #_logger.debug("adding to current level", self.depth, data)
                self.tree[self.depth].append(data)

            elif self.depth > self.lastDepth:
                #_logger.debug("starting new level: %s %s" % (self.depth, data))
                self.tree.append([data])

            elif self.depth < self.lastDepth:

                for i in range(0, self.lastDepth - self.depth):
                    branch = self.tree.pop()
                    #_logger.debug("closing level %s - %s - %s" % (self.lastDepth, self.depth, self.tree[-1]))
                    currTree = self.tree[-1]
                    # if isinstance(currTree, list):
                    currTree.append(branch)
                    # else:
                    #    _logger.info("skipping", data)
                    #    self.close()
                    #    return

                #_logger.debug("adding to level", self.depth, data)
                self.tree[self.depth].append(data)
            else:
                return
            self.lastDepth = self.depth
            # with 2009 and the addition of the MPxNode, the hierarchy closes all the way out ( i.e. no  >'s )
            # this prevents the depth from getting set properly. as a workaround, we'll set it to 0 here,
            # then if we encounter '> >' we set the appropriate depth, otherwise it defaults to 0.
            self.depth = 0


def printTree(tree, depth=0):
    for branch in tree:
        if util.isIterable(branch):
            printTree(branch, depth + 1)
        else:
            _logger.info('%s %s' % ('> ' * depth, branch))


class CommandModuleDocParser(HTMLParser):

    def parse(self):

        f = open(os.path.join(self.docloc, 'Commands/cat_' + self.category + '.html'))
        self.feed(f.read())
        f.close()
        return self.cmdList

    def __init__(self, category, version=None):
        self.cmdList = []
        self.category = category
        self.version = version

        docloc = mayaDocsLocation('2009' if self.version == '2008' else self.version)
        self.docloc = docloc
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        try:
            attrs = attrs[0]
            #_logger.debug(attrs)
            if tag == 'a' and attrs[0] == 'href':
                cmd = attrs[1].split("'")[1].split('.')[0]
                self.cmdList.append(cmd)
                #_logger.debug(cmd)
        except IndexError:
            return

class ApiDocParser(object):
    __metaclass__ = ABCMeta

    NO_PYTHON_MSG = ['NO SCRIPT SUPPORT.', 'This method is not available in Python.']
    DEPRECATED_MSG = ['This method is obsolete.', 'Deprecated:']

    # in enums with multiple keys per int value, which (pymel) key name to use
    # as the default - ie, in MSpace, both object and preTransformed map to 2;
    # since 'object' is in PYMEL_ENUM_DEFAULTS['Space'], that is preferred
    PYMEL_ENUM_DEFAULTS = {'Space': ('object',)}

    MISSING_TYPES = ['MUint64', 'MInt64', 'MGLfloat', 'MGLdouble']
    OTHER_TYPES = ['void', 'char', 'uchar',
                   'double', 'double2', 'double3', 'double4',
                   'float', 'float2', 'float3', 'float4',
                   'bool',
                   'int', 'int2', 'int3', 'int4',
                   'uint', 'uint2', 'uint3', 'uint4',
                   'short', 'short2', 'short3', 'short4',
                   'long', 'long2', 'long3',
                   'MString', 'MStringArray', 'MStatus']
    NOT_TYPES = ['MCallbackId']

    _anonymousEnumRe = re.compile(r'^@[0-9]+$')
    _bracketRe = re.compile(r'\[|\]')
    _capitalizedWithNumsRe = re.compile('([A-Z0-9][a-z0-9]*)')
    _isMethodNameRe = re.compile('is[A-Z].*')
    _capitalizedRe = re.compile('([A-Z][a-z]*)')
    _fillStorageResultRe = re.compile(r'\b([fF]ill|[sS]tor(age)|(ing))|([rR]esult)')
    _setMethodNameRe = re.compile('set([A-Z].*)')
    _getMethodNameRe = re.compile('get[A-Z]')

    def __new__(cls, apiModule, version=None, *args, **kwargs):
        # temp transition - use XML for 2019+
        installVersion = versions.installName() if version is None else version
        # for 2019+, installVersion should be just a number string...
        if (cls == ApiDocParser):
            try:
                versionNum = float(installVersion)
            except ValueError:
                parserCls = HtmlApiDocParser
            else:
                if versionNum >= 2019:
                    parserCls = XmlApiDocParser
                else:
                    parserCls = HtmlApiDocParser
            return parserCls.__new__(parserCls, apiModule, version, *args, **kwargs)
        else:
            return super(ApiDocParser, cls).__new__(cls)

    def __init__(self, apiModule, version=None, verbose=False, enumClass=tuple,
                 docLocation=None, strict=False):
        self.version = versions.installName() if version is None else version
        self.apiModule = apiModule
        self.verbose = verbose
        if docLocation is None:
            docLocation = mayaDocsLocation(self.version)
        self.docloc = docLocation
        self.enumClass = enumClass
        if not os.path.isdir(self.docloc):
            raise IOError, "Cannot find maya documentation. Expected to find it at %s" % self.docloc
        self.strict = strict

        self.enums = {}
        self.pymelEnums = {}
        self.methods = util.defaultdict(list)
        self.currentMethodName = None
        self.currentRawMethod = None
        self.badEnums = []

    def __repr__(self):
        return '%s.%s(%s, %r, %r, %s.%s, %r)' % (__name__,
                                                 self.__class__.__name__,
                                                 self.apiModule.__name__,
                                                 self.version,
                                                 self.verbose,
                                                 self.enumClass.__module__,
                                                 self.enumClass.__name__,
                                                 self.docloc)

    def fullMethodName(self):
        className = self.apiClassName or "<no class>"
        methodName = self.currentMethodName or "<no method>"
        return className + '.' + methodName

    def formatMsg(self, *args):
        return self.fullMethodName() + ': ' + ' '.join([str(x) for x in args])

    def xprint(self, *args):
        if self.verbose:
            print self.formatMsg(*args)

    def getPymelMethodNames(self):
        pymelNames = {}
        pairs = {}
        pairsList = []

        def addSetGetPair(setmethod, getMethod):
            pairsList.append((setMethod, getMethod))
            # pair 'set' with 'is/get'
            pairs[setMethod] = getMethod
            for info in self.methods[setMethod]:
                info['inverse'] = (getMethod, True)

            # pair 'is/get' with 'set'
            pairs[getMethod] = setMethod
            for info in self.methods[getMethod]:
                info['inverse'] = (setMethod, False)

        for member in self.methods:
            m = self._setMethodNameRe.match(member)
            if m:
                # MFn api naming convention usually uses setValue(), value() convention for its set and get methods, respectively
                # setSomething()  &  something()  becomes  setSomething() & getSomething()
                # setIsSomething() & isSomething() becomes setSomething() & isSomething()
                basename = m.group(1)
                origGetMethod = util.uncapitalize(basename)
                setMethod = member  # for name clarity
                if origGetMethod in self.methods:
                    # fix set
                    if self._isMethodNameRe.match(origGetMethod):
                        newSetMethod = 'set' + origGetMethod[2:]  # remove 'is' #member[5:]
                        pymelNames[setMethod] = newSetMethod
                        for info in self.methods[setMethod]:
                            info['pymelName'] = newSetMethod
                        addSetGetPair(setMethod, origGetMethod)

                    # fix get
                    else:
                        newGetMethod = 'g' + setMethod[1:]  # remove 's'
                        pymelNames[origGetMethod] = newGetMethod
                        for info in self.methods[origGetMethod]:
                            info['pymelName'] = newGetMethod
                        addSetGetPair(setMethod, origGetMethod)

                else:
                    getMethod = 'get' + basename
                    isMethod = 'is' + basename
                    if getMethod in self.methods:
                        addSetGetPair(setMethod, getMethod)
                    elif isMethod in self.methods:
                        addSetGetPair(setMethod, isMethod)

        return pymelNames, sorted(pairsList)

    def getClassFilename(self):
        filename = 'class'
        for tok in self._capitalizedRe.split(self.apiClassName):
            if tok:
                if tok[0].isupper():
                    filename += '_' + tok.lower()
                else:
                    filename += tok
        return filename

    def _apiEnumNamesToPymelEnumNames(self, apiEnumNames):
        """remove all common prefixes from list of enum values"""
        if isinstance(apiEnumNames, util.Enum):
            apiEnumNames = apiEnumNames._keys.keys()
        if len(apiEnumNames) > 1:
            # We first aim to remove all similar 'camel-case-group' prefixes, ie:
            # if our enums look like:
            #    kFooBar
            #    kFooSomeThing
            #    kFooBunnies
            # we want to get Bar, SomeThing, Bunnies

            # {'kFooBar':0, 'kFooSomeThing':1}
            #     => [['k', 'Foo', 'Some', 'Thing'], ['k', 'Foo', 'Bar']]
            splitEnums = [[y for y in self._capitalizedWithNumsRe.split(x) if y] for x in apiEnumNames]

            # [['k', 'Invalid'], ['k', 'Pre', 'Transform']]
            #     => [('k', 'k'), ('Foo', 'Foo'), ('Some', 'Bar')]
            splitZip = zip(*splitEnums)
            for partList in splitZip:
                if tuple([partList[0]] * len(partList)) == partList:
                    [x.pop(0) for x in splitEnums]
                else:
                    break
            # splitEnums == [['Some', 'Thing'], ['Bar']]

            joinedEnums = [util.uncapitalize(''.join(x), preserveAcronymns=True) for x in splitEnums]
            for i, enum in enumerate(joinedEnums):
                if _iskeyword(enum):
                    joinedEnums[i] = enum + '_'
                    self.xprint("bad enum", enum)
                elif enum[0].isdigit():
                    joinedEnums[i] = 'k' + enum
                    self.xprint("bad enum", enum)

                    # print joinedEnums
                    # print enumList
                    # break

            return dict(zip(apiEnumNames, joinedEnums))
        else:
            # if only 1 name or less, name is unaltered
            return dict((name, name) for name in apiEnumNames)

    def _apiEnumToPymelEnum(self, apiEnum, apiToPymelNames=None):
        defaultsSet = self.PYMEL_ENUM_DEFAULTS.get(apiEnum.name, set())
        defaults = {}
        if apiToPymelNames is None:
            apiToPymelNames = self._apiEnumNamesToPymelEnumNames(apiEnum)
        pymelKeyDict = {}
        docs = dict(apiEnum._docs)
        for apiName, val in apiEnum._keys.iteritems():
            # want to include docs, so make dict (key, doc) => val
            pymelKeyDict[apiName] = val
            pymelName = apiToPymelNames[apiName]
            pymelKeyDict[pymelName] = val

            doc = apiEnum._docs.get(apiName)
            if doc:
                docs[pymelName] = doc

            # in the pymel dict, the pymel name should always be the default
            # key for a value... but the original dict may also have multiple
            # keys for a value... so:
            #   if there is an entry in PYMEL_ENUM_DEFAULTS for this
            #     class/pymelName, then use that as the default
            #   otherwise, use the pymel equivalent of whatever the original
            #     api default was
            if (pymelName in defaultsSet
                    # need to check val not in defaults, or else we can override
                    # a value set due to defaultsSet
                    or (val not in defaults and apiName == apiEnum.getKey(val))):
                defaults[val] = pymelName
        return util.Enum(apiEnum.name, pymelKeyDict, multiKeys=True,
                         defaultKeys=defaults)

    def isBadEnum(self, type):
        return (type[0].isupper() and 'Ptr' not in type
                and not hasattr(self.apiModule, type)
                and type not in self.OTHER_TYPES + self.MISSING_TYPES + self.NOT_TYPES)

    def handleEnums(self, type):
        if type is None:
            return type

        # the enum is on another class
        if '::' in type:
            self.xprint('type is an enum on another class', type)
            type = self.enumClass(type.split('::'))

        # the enum is on this class
        elif type in self.enums:
            self.xprint('type is in self.enums', type)
            type = self.enumClass([self.apiClassName, type])

        elif self.isBadEnum(type):
            type = self.enumClass([self.apiClassName, type])
            if type not in self.badEnums:
                self.badEnums.append(type)
                _logger.warn("Suspected Bad Enum: %s", type)
        else:
            type = str(type)
        return type

    def handleEnumDefaults(self, default, type):

        if default is None:
            return default

        if isinstance(type, self.enumClass):

            # the enum is on another class
            if '::' in default:
                apiClass, enumConst = default.split('::')
                assert apiClass == type[0]
            else:
                enumConst = default

            return self.enumClass([type[0], type[1], enumConst])

        return default

    def getOperatorName(self, methodName):
        op = methodName[8:]
        # print "operator", methodName, op
        if op == '=':
            methodName = None
        else:

            methodName = {
                '*=': '__rmult__',
                '*': '__mul__',
                '+=': '__radd__',
                '+': '__add__',
                '-=': '__rsub__',
                '-': '__sub__',
                '/=': '__rdiv__',
                '/': '__div__',
                '==': '__eq__',
                '!=': '__neq__',
                '[]': '__getitem__'}.get(op, None)
        return methodName

    def isSetMethod(self):
        return bool(self._setMethodNameRe.match(self.currentMethodName))

    def isGetMethod(self):
        return bool(self._getMethodNameRe.match(self.currentMethodName))

    def parseValue(self, rawValue, valueType):
        try:
            # Constants
            return {
                'true': True,
                'false': False,
                'NULL': None
            }[rawValue]
        except KeyError:
            pass

        try:
            if valueType in ['int', 'uint', 'long', 'uchar']:
                return int(rawValue.rstrip('UuLl'))
            elif valueType in ['float', 'double']:
                # '1.0 / 24.0'
                if isinstance(rawValue, basestring) and rawValue.count('/') == 1:
                    numerator, divisor = rawValue.split('/')
                    return self.parseValue(numerator) / self.parseValue(divisor)
                # '1.0e-5F'  --> '1.0e-5'
                elif rawValue.endswith(('F', 'f')):
                    return float(rawValue[:-1])
                else:
                    return float(rawValue)
        except (ValueError, TypeError):
            pass

        if rawValue in self.constants:
            return self.constants[rawValue]
        return self.handleEnumDefaults(rawValue, valueType)

    def parseType(self, tokens):
        for i, each in enumerate(tokens):
            if each not in ['*', '&', 'const', 'unsigned']:
                argtype = tokens.pop(i)
                assert isinstance(argtype, str), "%r is not a string" % (argtype,)
                break
        else:
            # We didn't find any arg type - therefore everything
            # in buf is in the set('*', '&', 'const', 'unsigned')
            # ... so it's implicitly an unsigned int
            argtype = 'int'

        if 'unsigned' in tokens and argtype in ('char', 'int', 'int2',
                                                'int3', 'int4'):
            argtype = 'u' + argtype

        argtype = self.handleEnums(argtype)
        return argtype, tokens

    def parseEnum(self, enumData):
        try:
            parsedEnumData = self._parseEnum(enumData)
            if not parsedEnumData:
                return
            enumDocs = parsedEnumData['docs']

            apiEnum = util.Enum(parsedEnumData['name'],
                                parsedEnumData['values'], multiKeys=True)
            apiToPymelNames = self._apiEnumNamesToPymelEnumNames(apiEnum)
            pymelEnum = self._apiEnumToPymelEnum(apiEnum,
                                                 apiToPymelNames=apiToPymelNames)
            for apiName, pymelName in apiToPymelNames.iteritems():
                apiDoc = enumDocs.get(apiName)
                if apiDoc is not None:
                    enumDocs[pymelName] = apiDoc

            enumInfo = {'values': apiEnum,
                        'valueDocs': enumDocs,
                        }
            self.enums[parsedEnumData['name']] = enumInfo
            self.pymelEnums[parsedEnumData['name']] = pymelEnum
        except Exception as msg:
            if self.strict:
                raise
            _logger.error("FAILED ENUM: %s", msg)
            import traceback
            _logger.debug(traceback.format_exc())

    def parseMethod(self, rawMethod):
        self.currentRawMethod = rawMethod
        methodName, returnType, returnQualifiers = self.getMethodNameAndOutput()
        if methodName is None:
            return

        # Old html parser filtered these from returnQualifiers, so we enforce this
        # too, for consistency
        returnQualifiers = [x for x in returnQualifiers if x not in ['const', 'unsigned'] and x]

        # skip constructors and destructors
        if methodName.startswith('~') or methodName == self.apiClassName:
            return

        # convert operators to python special methods
        if methodName.startswith('operator'):
            methodName = self.getOperatorName(methodName)
            if methodName is None:
                return

        # no MStatus in python
        if returnType in ['MStatus', 'void']:
            returnType = None

        # convert to unicode
        self.currentMethodName = str(methodName)

        result = self._parseMethod(returnType, returnQualifiers)

        # used to reset these to none using a try/finally, but then some
        # error handlers couldn't use them, reducing their usefulness
        self.currentMethodName = None
        self.currentRawMethod = None
        return result

    def _parseMethod(self, returnType, returnQualifiers):
        self.xprint("RETURN", returnType)

        if self.hasNoPython():
            return

        names, types, typeQualifiers, defaults = self.parseArgTypes()

        try:
            directions, docs, methodDoc, returnDoc, deprecated = self.parseMethodArgs(returnType, names, types, typeQualifiers)
        except AssertionError, msg:
            if self.strict:
                raise
            _logger.error(self.formatMsg("FAILED", str(msg)))
            return
        except AttributeError:
            if self.strict:
                raise
            import traceback
            _logger.error(self.formatMsg(traceback.format_exc()))
            return

        argInfo = {}
        argList = []
        inArgs = []
        outArgs = []

        for argname in names[:]:
            type = types[argname]
            if argname not in directions:
                self.xprint("Warning: assuming direction is 'in'")
                directions[argname] = 'in'
            direction = directions[argname]
            doc = docs.get(argname, '')

            if type == 'MStatus':
                types.pop(argname)
                defaults.pop(argname, None)
                directions.pop(argname, None)
                docs.pop(argname, None)
                idx = names.index(argname)
                names.pop(idx)
            else:
                if direction == 'in':
                    inArgs.append(argname)
                else:
                    outArgs.append(argname)
                argInfo[argname] = {'type': type, 'doc': standardizeWhitespace(doc)}

        # correct bad outputs
        if self.isGetMethod() and not returnType and not outArgs:
            for argname in names:
                if '&' in typeQualifiers[argname]:
                    doc = docs.get(argname, '')
                    directions[argname] = 'out'
                    idx = inArgs.index(argname)
                    inArgs.pop(idx)
                    outArgs.append(argname)

                    _logger.warn("%s.%s(%s): Correcting suspected output argument '%s' because there are no outputs and the method is prefixed with 'get' ('%s')" % (
                        self.apiClassName, self.currentMethodName, ', '.join(names), argname, doc))

        # now that the directions are correct, make the argList
        for argname in names:
            type = types[argname]
            self.xprint("DIRECTIONS", directions)
            direction = directions[argname]
            data = (argname, type, direction)
            self.xprint("ARG", data)
            argList.append(data)

        if returnType is None:
            returnDoc = ''

        methodInfo = {'argInfo': argInfo,
                      'returnInfo': {'type': returnType,
                                     'doc': standardizeWhitespace(returnDoc),
                                     'qualifiers': returnQualifiers},
                      'args': argList,
                      'returnType': returnType,
                      'inArgs': inArgs,
                      'outArgs': outArgs,
                      'doc': standardizeWhitespace(methodDoc),
                      'defaults': defaults,
                      #'directions' : directions,
                      'types': types,
                      'static': self.isStaticMethod(),
                      'typeQualifiers': typeQualifiers,
                      'deprecated': deprecated}
        self.methods[self.currentMethodName].append(methodInfo)
        return methodInfo

    def setClass(self, apiClassName):
        self.enums = {}
        self.pymelEnums = {}
        self.methods = util.defaultdict(list)
        self.currentMethodName = None
        self.badEnums = []
        self.constants = {}

        self.apiClassName = apiClassName
        self.apiClass = getattr(self.apiModule, self.apiClassName)
        self.docfile = self.getClassPath()

        _logger.info("parsing file %s", self.docfile)

    def parse(self, apiClassName):
        self.setClass(apiClassName)
        try:
            self.parseBody()
        except:
            print "To reproduce run:\n%r.parse(%r)" % (self, apiClassName)
            print self.formatMsg("Unknown error")
            raise

        pymelNames, invertibles = self.getPymelMethodNames()
        parsed = {
            'methods': dict(self.methods),
            'enums': self.enums,
            'pymelEnums': self.pymelEnums,
            'pymelMethods': pymelNames,
            'invertibles': invertibles,
        }
        if self.constants:
            parsed['constants'] = self.constants
        return parsed

    @abstractmethod
    def parseArgTypes(self):
        raise NotImplementedError()

    @abstractmethod
    def _parseEnum(self, enumData):
        raise NotImplementedError()

    @abstractmethod
    def hasNoPython(self):
        raise NotImplementedError()

    @abstractmethod
    def isStaticMethod(self):
        raise NotImplementedError()

    @abstractmethod
    def parseMethodArgs(self, returnType, names, types, typeQualifiers):
        raise NotImplementedError()

    @abstractmethod
    def getMethodNameAndOutput(self):
        raise NotImplementedError()

    @abstractmethod
    def getClassPath(self):
        raise NotImplementedError()

    @abstractmethod
    def parseBody(self):
        raise NotImplementedError()


class XmlApiDocParser(ApiDocParser):
    _backslashTagRe = re.compile(r'(?:^|(?<=\s))\\(\S+)\s+', re.MULTILINE)
    _paramDirRe = re.compile(r'^param\[(?P<dir>in|out|in,out|inout)\]$')

    def fullMethodName(self):
        fullName = super(XmlApiDocParser, self).fullMethodName()
        if self.currentRawMethod is not None:
            line = ''
            location = self.currentRawMethod.find('location')
            if location is not None:
                line = location.attrib.get('line', '')
            if line:
                fullName += ':' + line
        return fullName

    def setClass(self, apiClassName):
        super(XmlApiDocParser, self).setClass(apiClassName)
        self.tree = ET.parse(self.docfile)
        self.root = self.tree.getroot()
        self.cdef = self.root.find(".//compounddef[@kind='class'][@id='{}']".format(self.baseFilename))
        self.numAnonymousEnums = 0

    def parseArgTypes(self):
        names = []
        types = {}
        defaults = {}
        typeQualifiers = {}

        def returnEmtpy():
            return [], {}, {}, {}

        foundUnknownName = False

        # TYPES
        for param in self.currentRawMethod.findall('param'):
            paramNameElem = param.find('defname')
            if paramNameElem is None:
                paramNameElem = param.find('declname')
            paramName = xmlText(paramNameElem)
            if paramName == '':
                if foundUnknownName:
                    # if we find more than one uknown param name, we abort
                    return returnEmtpy()
                foundUnknownName = True

            rawType = xmlText(param.find('type'))
            parsedType, qualifiers = self.parseType(rawType.split())
            names.append(paramName)

            arrayInfo = param.find('array')
            if arrayInfo is not None:
                brackets = xmlText(arrayInfo)
                if brackets:
                    numbuf = self._bracketRe.split(brackets)
                    if len(numbuf) > 1:
                        if not isinstance(parsedType, str):
                            if isinstance(parsedType, self.enumClass):
                                raise TypeError("%s should be a string, but it has been marked as an enum. "
                                                "Check if it is a new type which should be added to "
                                                "OTHER_TYPES or MISSING_TYPES on this class." % (parsedType,))
                            else:
                                raise TypeError("%r should be a string" % (parsedType,))
                        # Note that these two args need to be cast differently:
                        #   int2 foo;
                        #   int bar[2];
                        # ... so, instead of storing the type of both as
                        # 'int2', we make the second one 'int__array2'
                        parsedType = parsedType + '__array' + numbuf[1]
                    else:
                        print "this is not a bracketed number", repr(brackets), parsedType

            types[paramName] = parsedType
            typeQualifiers[paramName] = qualifiers

            defaultElem = param.find('defval')
            if defaultElem is not None:
                default = xmlText(defaultElem)
                if default:
                    default = self.parseValue(default, parsedType)
                    # default must be set here, because 'NULL' may mean default is set to back to None,
                    # but in this case it is meaningful (ie, doesn't mean "there was no default")
                    self.xprint('DEFAULT', default)
                    defaults[paramName] = default
        # filter myFunc(void) type funcs - this also gets stuff like "myFunc(void) const"
        if types == {'': 'void'}:
            return returnEmtpy()

        return names, types, typeQualifiers, defaults

    def _parseEnum(self, enumData):
        enumValues = {}
        enumDocs = {}
        enumName = xmlText(enumData.find('name'))
        self.currentMethodName = enumName
        self.xprint("ENUM", enumName)

        for enumValue in enumData.findall('enumvalue'):
            enumKey = xmlText(enumValue.find('name'))
            try:
                enumVal = getattr(self.apiClass, enumKey)
            except:
                _logger.warn("%s.%s of enum %s does not exist" % (self.apiClassName, enumKey, self.currentMethodName))
                continue
            enumValues[enumKey] = enumVal
            # TODO:
            # do we want to feed the docstrings to the Enum object itself
            # (which seems to have support for docstrings)? Currently, we're
            # not...
            docs = []
            for docType in ('briefdescription', 'detaileddescription'):
                docElem = enumValue.find(docType)
                if docElem is not None:
                    docText = xmlText(docElem)
                    if docText:
                        docs.append(docText)
            if docs:
                enumDocs[enumKey] = '\n\n'.join(docs)
        if not enumValues:
            return

        if self._anonymousEnumRe.match(enumName):
            # for an example of an anonymous enum, see MFnDagNode.kNextPos
            for key, value in enumValues.viewitems():
                self.constants[key] = value
            return

        return {'values': enumValues, 'docs': enumDocs, 'name': enumName}

    def hasNoPython(self):
        for text in self.currentRawMethod.itertext():
            if any(badMsg in text for badMsg in self.NO_PYTHON_MSG):
                self.xprint("NO PYTHON")
                self.currentMethodName = None
                return True
        return False

    def isDeprecated(self):
        for text in self.currentRawMethod.itertext():
            if any(badMsg in text for badMsg in self.DEPRECATED_MSG):
                self.xprint("DEPRECATED")
                return True
        return False

    def isStaticMethod(self):
        return self.currentRawMethod.attrib.get('static') == "yes"

    @classmethod
    def iterBackslashTags(cls, text, subTags=('li',)):
        r"""Iterator that parses text with tags like: "\tag Some text for tag"

        Sometimes detail text does not parse parameters properly, and we end up with text like this,
        from 2019 MFnMesh.addPolygon 2nd overload (with 6 args):

        If we are adding to an existing polygonal mesh then parentOrOwner is
        ignored and the geometry is returned.

        \param[in] vertexArray Array of ordered vertices that make up the polygon.
        \param[in] loopCounts Array of vertex loop counts.
        \param[out] faceIndex Index of the newly added polygon.
        \param[in] mergeVertices If true then if a vertex falls within
                                                            pointTolerance of an existing vertex then the
                                                            existing vertex is reused.
        \param[in] pointTolerance Specifies how close verticies have to be to
                                                            before they are &lt;i&gt;merged&lt;/i&gt;.  This merging is
                                                            only done if &lt;i&gt;mergeVerticies&lt;/i&gt; is true.
        \param[in] parentOrOwner The DAG parent or kMeshData the new
                                                            surface will belong to.
        \param[out] ReturnStatus Status code.

        \return
        The transform if one is created, otherwise the geometry.

        This code will iterate through, finding lines that start with a "backslash tag", and issuing tuples like this:

        ("param[in]", "vertexArray Array of ordered vertices that make up the polygon.\n")
        ("param[in]", "loopCounts Array of vertex loop counts.\n")

        The text before we find the first tag will be ignored.
        """
        currentTag = None
        currentTextChunks = []
        lastPosition = 0
        for match in cls._backslashTagRe.finditer(text):
            currentTextChunks.append(text[lastPosition:match.start()])
            lastPosition = match.end()
            newTag = match.group(1)
            if newTag in subTags:
                currentTextChunks.append(' ')
                continue

            yield (currentTag, ''.join(currentTextChunks))
            currentTextChunks = []
            currentTag = newTag

        currentTextChunks.append(text[lastPosition:])
        yield (currentTag, ''.join(currentTextChunks))

    @classmethod
    def parseBackslashTags(cls, text):
        info = {
            'params': {},
            'returnDoc': '',
        }
        foundSomething = False
        remainingPieces = []
        for tag, tagText in cls.iterBackslashTags(text):
            if tag is None:
                remainingPieces.append(tagText)
            else:
                paramMatch = cls._paramDirRe.match(tag)
                if paramMatch is not None:
                    splitText = tagText.strip().split()
                    name = splitText[0]
                    paramInfo = {
                        'direction': paramMatch.group('dir'),
                        # Because this didn't parse correctly, it may have some tags
                        # still in the text - ie, "<i>merged</i>" (which gets encoded
                        # in the xml as: "&lt;i&gt;merged&lt;/i&gt")
                        'doc': strip_tags(' '.join(splitText[1:])),
                    }
                    info['params'][name] = paramInfo
                    foundSomething = True
                elif tag == 'return':
                    info['returnDoc'] = strip_tags(tagText)
                    foundSomething = True
                else:
                    remainingPieces.append('{} {}'.format(tag, tagText))
        if foundSomething:
            info['remainingText'] = strip_tags(''.join(remainingPieces))
            return info

    def parseMethodArgs(self, returnType, names, types, typeQualifiers):
        directions = {}
        docs = {
            # we have returnDoc in here so it can be modified by internal funcs
            '<returnDoc>': ''
        }
        deprecated = self.isDeprecated()
        methodDoc = ''

        brief = self.currentRawMethod.find('briefdescription')
        if brief is not None:
            briefText = getFirstText(brief)
            if briefText not in self.DEPRECATED_MSG and briefText not in self.NO_PYTHON_MSG:
                methodDoc = briefText

        detail = self.currentRawMethod.find('detaileddescription')

        if not methodDoc and detail is not None:
            for para in detail.findall('para'):
                paraText = getFirstText(para)
                if paraText:
                    methodDoc = paraText
                    break

        if returnType and detail is not None:
            returnElem = detail.find(".//simplesect[@kind='return']")
            docs['<returnDoc>'] = xmlText(returnElem)

        paramDescriptions = []
        if detail is not None:
            paramList = detail.find(".//parameterlist[@kind='param']")
            if paramList is not None:
                paramDescriptions = paramList.findall('parameteritem')

        def parseRawTagInfo(text):
            parsedTags = self.parseBackslashTags(text)
            foundSomething = False
            if parsedTags:
                for paramName, paramInfo in parsedTags['params'].iteritems():
                    if paramName not in docs:
                        docs[paramName] = paramInfo['doc']
                        directions[paramName] = paramInfo['direction']
                        missingParamDocs.remove(paramName)
                        foundSomething = True
                if not docs['<returnDoc>']:
                    docs['<returnDoc>'] = parsedTags['returnDoc']
                    foundSomething = True
            if foundSomething:
                return parsedTags['remainingText']

        if len(paramDescriptions) > len(names):
            msg = "found more ({}) parameter descriptions than parameter declarations ({})".format(
                len(paramDescriptions), len(names))
            raise ValueError(self.formatMsg(msg))

        paramDescriptionNames = []
        missingParamDocs = set(names)
        foundParamNameOnce = {}
        foundParamNameRepeated = {}

        for i, param in enumerate(paramDescriptions):
            allNames = param.find('parameternamelist').findall('parametername')

            # Don't have an example of nameList > 1, so error for now
            if len(allNames) > 1:
                raise ValueError(self.formatMsg("found more than 1 name for parameter {!r}".format(name)))

            name = xmlText(allNames[0])
            paramDescriptionNames.append(name)
            try:
                missingParamDocs.remove(name)
            except KeyError:
                # if it's in foundParamNameOnce / foundParamNameRepeated,
                # it's a repeat, we'll deal with that later
                if name in foundParamNameRepeated:
                    foundParamNameRepeated[name].append(i)
                elif name in foundParamNameOnce:
                    foundParamNameRepeated[name] = [foundParamNameOnce.pop(name), i]
                else:
                    # otherwise, we have a totally unexpected name...
                    msg = "Found parameter description with name {}, but no matching declaration".format(name)
                    raise ValueError(self.formatMsg(msg))
            else:
                foundParamNameOnce[name] = i

        # check for repeats
        if foundParamNameRepeated:
            # if all the names that show up onlyOnce match the names at the
            # same positions of "names", then just use "names" to fill in
            # the remaining names
            uniquesMatch = True
            for name, i in foundParamNameOnce.iteritems():
                if names[i] != name:
                    uniquesMatch = False
                    break
            if uniquesMatch:
                paramDescriptionNames = names[:len(paramDescriptions)]
                # note we may still have missing names if
                # len(paramDescriptions) < len(names)
                missingParamDocs = set(names) - set(paramDescriptionNames)
            else:
                # otherwise, we error (for now)
                raise ValueError("Found repeated param names, and non-repated"
                                 " name placement did not match declared names:"
                                " {}".format(", ".join(sorted(foundParamNameRepeated))))

        for name, param in zip(paramDescriptionNames, paramDescriptions):
            allNames = param.find('parameternamelist').findall('parametername')

            directions[name] = allNames[0].attrib['direction']
            docs[name] = xmlText(param.find('parameterdescription'))

            # sometimes backslash tags get placed in the description of other
            # parameters. check for that...
            #
            # As an example, this happens in the 2019 xml docs,
            # MCameraSetMessage.addCameraLayerCallback - the docs for
            # 'clientData' appear inside the docs for 'func'
            remainingText = parseRawTagInfo(docs[name])
            if remainingText:
                docs[name] = remainingText

        if missingParamDocs or (returnType and not docs['<returnDoc>']):
            # Sometimes, "parameteritem" xml objects may not be properly created,
            # but (manually) parsable information still exists in the detaileddescription
            # ie, this happens in the 2019 MFnMesh.addPolygon 2nd overload (with 6 args)
            if detail is not None:
                parseRawTagInfo(xmlText(detail))

        if missingParamDocs:
            wereMissingAll = len(missingParamDocs) == len(names)
            for missing in list(missingParamDocs):
                if (types[missing] == 'MStatus'
                        and ('*' in typeQualifiers[missing]
                             or '&' in typeQualifiers[missing])):
                    missingParamDocs.remove(missing)
                    directions[missing] = 'out'
                    continue
            if not wereMissingAll and missingParamDocs:
                msg = "found parameters that were missing documentation: {}".format(
                    ", ".join(sorted(missingParamDocs)))
                raise ValueError(self.formatMsg(msg))

        for name, dir in directions.iteritems():
            doc = docs.get(name, '')
            if dir == 'in':
                # attempt to correct bad in/out docs
                if self._fillStorageResultRe.search(doc):
                    _logger.warn("%s.%s(%s): Correcting suspected output argument '%s' based on doc '%s'" % (
                        self.apiClassName, self.currentMethodName, ', '.join(names), name, doc))
                    dir = 'out'
                elif not self.isSetMethod() and '&' in typeQualifiers[name] and types[name] in ['int', 'double', 'float', 'uint', 'uchar']:
                    _logger.warn("%s.%s(%s): Correcting suspected output argument '%s' based on reference type '%s &' ('%s')'" % (
                        self.apiClassName, self.currentMethodName, ', '.join(names), name, types[name], doc))
                    dir = 'out'
            elif dir == 'out':
                if types[name] == 'MAnimCurveChange':
                    _logger.warn("%s.%s(%s): Setting MAnimCurveChange argument '%s' to an input arg (instead of output)" % (
                        self.apiClassName, self.currentMethodName, ', '.join(names), name))
                    dir = 'in'
            elif dir in ('in,out', 'inout'):
                # it makes the most sense to treat these types as inputs
                # maybe someday we can deal with dual-direction args...?
                dir = 'in'
            else:
                raise ValueError("direction must be either 'in', 'out', 'inout', or 'in,out'. got {!r}".format(dir))

            assert name in names
            directions[name] = dir
            docs[name] = doc.replace('\n\r', ' ').replace('\n', ' ')

        returnDoc = docs.pop('<returnDoc>')
        return directions, docs, methodDoc, returnDoc, deprecated

    def getMethodNameAndOutput(self):
        methodName = self.currentRawMethod.find("name").text

        returnType = xmlText(self.currentRawMethod.find("type"))
        returnType, returnQualifiers = self.parseType(returnType.split())

        return methodName, returnType, returnQualifiers

    def getClassPath(self):
        self.baseFilename = self.getClassFilename()
        filename = self.baseFilename + '.xml'
        apiBase = os.path.join(self.docloc, 'xml')
        return os.path.join(apiBase, filename)

    def parseBody(self):
        for enum in self.cdef.findall("./*/memberdef[@kind='enum'][@prot='public']"):
            self.parseEnum(enum)

        for func in self.cdef.findall("./*/memberdef[@kind='function']"):
            # We take public functions, and protected virtual functions
            # Protected virtual funcs may not be exposed if the method they override
            # isn't public, but better to be overly inclusive
            protection = func.attrib.get('prot')
            if (protection == 'public' or
                    (protection == 'protected' and func.attrib.get('virt') == 'virtual')):
                self.parseMethod(func)


class HtmlApiDocParser(ApiDocParser):
    NO_PYTHON_MSG = ['NO SCRIPT SUPPORT.', 'This method is not available in Python.']
    DEPRECATED_MSG = ['This method is obsolete.', 'Deprecated:']

    _enumRe = re.compile('Enumerator')
    _paramPostNameRe = re.compile('([^=]*)(?:\s*=\s*(.*))?')

    def parseArgTypes(self):
        defaults = {}
        names = []
        types = {}
        typeQualifiers = {}
        tmpTypes = []
        # TYPES
        for paramtype in self.currentRawMethod.findAll('td', **{'class': 'paramtype'}):
            buf = []
            for x in paramtype.findAll(text=True):
                buf.extend(x.split())
                # if x.strip() not in ['', '*', '&', 'const', 'unsigned'] ]
            buf = [x.strip().encode('ascii', 'ignore') for x in buf if x.strip()]
            tmpTypes.append(self.parseType(buf))

        # ARGUMENT NAMES
        i = 0
        for paramname in self.currentRawMethod.findAll('td', **{'class': 'paramname'}):
            buf = [x.strip().encode('ascii', 'ignore') for x in paramname.findAll(text=True) if x.strip() not in['', ',']]
            if not buf:
                continue
            argname = buf[0]
            data = buf[1:]

            type, qualifiers = tmpTypes[i]
            default = None
            joined = ''.join(data).strip()

            if joined:
                joined = joined.encode('ascii', 'ignore')
                # break apart into index and defaults :  '[3] = NULL'
                brackets, default = self._paramPostNameRe.search(joined).groups()

                if brackets:
                    numbuf = self._bracketRe.split(brackets)
                    if len(numbuf) > 1:
                        if not isinstance(type, str):
                            if isinstance(type, self.enumClass):
                                raise TypeError("%s should be a string, but it has been marked as an enum. "
                                                "Check if it is a new type which should be added to "
                                                "OTHER_TYPES or MISSING_TYPES on this class." % (type,))
                            else:
                                raise TypeError("%r should be a string" % (type,))
                        # Note that these two args need to be cast differently:
                        #   int2 foo;
                        #   int bar[2];
                        # ... so, instead of storing the type of both as
                        # 'int2', we make the second one 'int__array2'
                        type = type + '__array' + numbuf[1]
                    else:
                        print "this is not a bracketed number", repr(brackets), joined

                if default is not None:
                    default = self.parseValue(default, type)
                    # default must be set here, because 'NULL' may mean default is set to back to None,
                    # but in this case it is meaningful (ie, doesn't mean "there was no default")
                    self.xprint('DEFAULT', default)
                    defaults[argname] = default

            types[argname] = type
            typeQualifiers[argname] = qualifiers
            names.append(argname)
            i += 1
        assert sorted(names) == sorted(types.keys()), 'name-type mismatch %s %s' % (sorted(names), sorted(types.keys()))
        return names, types, typeQualifiers, defaults

    def _parseEnum(self, rawEnum):
        enumValues = {}
        enumDocs = {}

        # get the doc portion...
        memdoc = rawEnum.findNextSibling('div', 'memdoc')
        # ...then search through it's dl items, looking for one with text that
        # says "Enumerator"...
        for dl in memdoc.findAll('dl'):
            if dl.find(text=self._enumRe):
                break
        else:
            raise RuntimeError("couldn't find list of Enumerator items in enum %s" % self.currentMethodName)
        # ...and each "em" in that should be the enumerator values...
        for em in dl.findAll('em'):
            enumKey = str(em.contents[-1])
            try:
                enumVal = getattr(self.apiClass, enumKey)
            except:
                _logger.warn("%s.%s of enum %s does not exist" % (self.apiClassName, enumKey, self.currentMethodName))
                enumVal = None
            enumValues[enumKey] = enumVal
            # TODO:
            # do we want to feed the docstrings to the Enum object itself
            # (which seems to have support for docstrings)? Currently, we're
            # not...
            docItem = em.next.next.next.next.next

            if isinstance(docItem, NavigableString):
                enumDocs[enumKey] = str(docItem).strip()
            else:
                enumDocs[enumKey] = str(docItem.contents[0]).strip()

        return {'values': enumValues, 'docs': enumDocs, 'name': self.currentMethodName}

    def hasNoPython(self):
        # ARGUMENT DIRECTION AND DOCUMENTATION
        addendum = self.currentRawMethod.findNextSiblings('div', limit=1)[0]
        # try: self.xprint( addendum.findAll(text=True ) )
        # except: pass

        # if addendum.findAll( text = re.compile( '(This method is obsolete.)|(Deprecated:)') ):

        if addendum.findAll(text=lambda x: any(badMsg in x for badMsg in self.NO_PYTHON_MSG)):
            self.xprint("NO PYTHON")
            self.currentMethodName = None
            return True
        return False

    def isStaticMethod(self):
        try:
            res = self.currentRawMethod.findAll('code')
            if res:
                code = res[-1].string
                if code and code.strip() == '[static]':
                    return True
        except IndexError:
            pass
        return False

    def parseMethodArgs(self, returnType, names, types, typeQualifiers):
        directions = {}
        docs = {}
        deprecated = False
        returnDoc = ''

        addendum = self.currentRawMethod.findNextSiblings('div', 'memdoc', limit=1)[0]
        if addendum.findAll(text=lambda x: any(badMsg in x for badMsg in self.DEPRECATED_MSG)):
            self.xprint("DEPRECATED")
            # print self.apiClassName + '.' + self.currentMethodName + ':' + ' DEPRECATED'
            deprecated = True

        methodDoc = addendum.p
        if methodDoc:
            methodDoc = ' '.join(methodDoc.findAll(text=True)).encode('ascii', 'ignore')
        else:
            methodDoc = ''

        tmpDirs = []
        tmpNames = []
        tmpDocs = []

        #extraInfo = addendum.dl.table
        # if self.version and int(self.version.split('-')[0]) < 2013:

        # 2012 introduced a new Doxygen version, which changed the api doc
        # format; also, even in 2013/2014, some pre-release builds of he docs
        # have used the pre-2012 format; so we can't just go by maya version...
        format2012 = self.doxygenVersion >= (1, 7)

        if format2012:
            extraInfos = addendum.findAll('table', **{'class': 'params'})
        else:
            #extraInfos = addendum.findAll(lambda tag: tag.name == 'table' and ('class', 'params') in tag.attrs)
            extraInfos = addendum.findAll(lambda tag: tag.name == 'dl' and ('class', 'return') not in tag.attrs and ('class', 'user') not in tag.attrs)
        if extraInfos:
            # print "NUMBER OF TABLES", len(extraInfos)
            if format2012:
                for extraInfo in extraInfos:
                    for tr in extraInfo.findAll('tr', recursive=False):
                        assert tr, "could not find name tr"
                        tds = tr.findAll('td', recursive=False)
                        assert tds, "could not find name td"
                        assert len(tds) == 3, "td list is unexpected length: %d" % len(tds)

                        paramDir = tds[0]
                        paramName = tds[1]

                        assert dict(paramDir.attrs).get('class') == 'paramdir', "First element in param table row was not a paramdir"
                        assert dict(paramName.attrs).get('class') == 'paramname', "Second element in param table row was not a paramname"

                        tmpDirs.append(paramDir.find(text=True).encode('ascii', 'ignore'))
                        tmpNames.append(paramName.find(text=True).encode('ascii', 'ignore'))
                        doc = ''.join(tds[2].findAll(text=True))
                        tmpDocs.append(doc.encode('ascii', 'ignore'))
            else:
                for extraInfo in extraInfos:
                    table = extraInfo.find('table')
                    if not table:
                        continue
                    for tr in table.findAll('tr', recursive=False):
                        assert tr, "could not find name tr"
                        tds = tr.findAll('td', recursive=False)
                        assert tds, "could not find name td"
                        assert len(tds) == 3, "td list is unexpected length: %d" % len(tds)

                        tt = tds[0].find('tt')
                        dir = tt.findAll(text=True, limit=1)[0]
                        tmpDirs.append(dir.encode('ascii', 'ignore'))

                        name = tds[1].findAll(text=True, limit=1)[0]
                        tmpNames.append(name.encode('ascii', 'ignore'))

                        doc = ''.join(tds[2].findAll(text=True))
                        tmpDocs.append(doc.encode('ascii', 'ignore'))

            assert len(tmpDirs) == len(tmpNames) == len(tmpDocs), \
                'names, types, and docs are of unequal lengths: %s vs. %s vs. %s' % (tmpDirs, tmpNames, tmpDocs)
            assert sorted(tmpNames) == sorted(typeQualifiers.keys()), 'name-typeQualifiers mismatch %s %s' % (sorted(tmpNames), sorted(typeQualifiers.keys()))
            #self.xprint(  sorted(tmpNames), sorted(typeQualifiers.keys()), sorted(typeQualifiers.keys()) )

            for name, dir, doc in zip(tmpNames, tmpDirs, tmpDocs):
                if dir == '[in]':
                    # attempt to correct bad in/out docs
                    # TODO: fix? see MFnMesh.booleanOp(useLegacy)
                    if self._fillStorageResultRe.search(doc):
                        _logger.warn("%s.%s(%s): Correcting suspected output argument '%s' based on doc '%s'" % (
                            self.apiClassName, self.currentMethodName, ', '.join(names), name, doc))
                        dir = 'out'
                    elif not self.isSetMethod() and '&' in typeQualifiers[name] and types[name] in ['int', 'double', 'float', 'uint', 'uchar']:
                        _logger.warn("%s.%s(%s): Correcting suspected output argument '%s' based on reference type '%s &' ('%s')'" % (
                            self.apiClassName, self.currentMethodName, ', '.join(names), name, types[name], doc))
                        dir = 'out'
                    else:
                        dir = 'in'
                elif dir == '[out]':
                    if types[name] == 'MAnimCurveChange':
                        _logger.warn("%s.%s(%s): Setting MAnimCurveChange argument '%s' to an input arg (instead of output)" % (
                            self.apiClassName, self.currentMethodName, ', '.join(names), name))
                        dir = 'in'
                    else:
                        dir = 'out'
                elif dir == '[in,out]':
                    # it makes the most sense to treat these types as inputs
                    # maybe someday we can deal with dual-direction args...?
                    dir = 'in'
                else:
                    raise ValueError("direction must be either '[in]', '[out]', or '[in,out]'. got %r" % dir)

                assert name in names
                directions[name] = dir
                docs[name] = doc.replace('\n\r', ' ').replace('\n', ' ')

            # Documentation for Return Values
            if returnType:
                try:
                    returnDocBuf = addendum.findAll('dl', limit=1, **{'class': 'return'})[0].findAll(text=True)
                except IndexError:
                    pass
                else:
                    if returnDocBuf:
                        returnDoc = ''.join(returnDocBuf[1:]).replace('\n\r', ' ').replace('\n', ' ').encode('ascii', 'ignore')
                    self.xprint('RETURN_DOC', repr(returnDoc))
        #assert len(names) == len(directions), "name lenght mismatch: %s %s" % (sorted(names), sorted(directions.keys()))
        return directions, docs, methodDoc, returnDoc, deprecated

    TYPEDEF_RE = re.compile('^typedef(\s|$)')

    def getMethodNameAndOutput(self):
        # NAME AND RETURN TYPE
        memb = self.currentRawMethod.find('td', **{'class': 'memname'})
        buf = []
        for text in memb.findAll(text=True):
            text = text.strip().encode('ascii', 'ignore')
            buf.extend(text.split())
        buf = [x for x in buf if x]

        assert buf, "could not parse a method name"

        methodName = returnType = returnQualifiers = None

        # typedefs aren't anything we care about (ie, may be a typedef of a
        # method - see MQtUtil.UITypeCreatorFn)
        if not self.TYPEDEF_RE.match(buf[0]):
            returnTypeToks = buf[:-1]
            methodName = buf[-1]

            methodName = methodName.split('::')[-1]
            returnType, returnQualifiers = self.parseType(returnTypeToks)

        return methodName, returnType, returnQualifiers

    def _parseMethod(self, returnType, returnQualifiers):
        if self.currentMethodName == 'void(*':
            return

        # ENUMS
        if returnType == 'enum':
            self.xprint("ENUM", returnType)
            # print returnType, methodName
            self.parseEnum(self.currentRawMethod)
            return

        super(HtmlApiDocParser, self)._parseMethod(returnType, returnQualifiers)

    DOXYGEN_VER_RE = re.compile('Generated by Doxygen ([0-9.]+)')

    def getDoxygenVersion(self, soup):
        doxyComment = soup.find(text=self.DOXYGEN_VER_RE)
        match = self.DOXYGEN_VER_RE.search(unicode(doxyComment))
        verStr = match.group(1)
        return tuple(int(x) for x in verStr.split('.'))

    def getClassPath(self):
        filename = self.getClassFilename() + '.html'
        apiBase = os.path.join(self.docloc, 'API')
        path = os.path.join(apiBase, filename)
        if not os.path.isfile(path):
            path = os.path.join(apiBase, 'cpp_ref', filename)
        return path

    def setClass(self, apiClassName):
        super(HtmlApiDocParser, self).setClass(apiClassName)

        with open(self.docfile) as f:
            self.soup = BeautifulSoup(f.read(), convertEntities='html')
        self.doxygenVersion = self.getDoxygenVersion(self.soup)

    def parseBody(self):
        for proto in self.soup.body.findAll('div', **{'class': 'memproto'}):
            self.parseMethod(proto)



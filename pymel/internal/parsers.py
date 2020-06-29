from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import zip
from builtins import chr, range
from past.builtins import basestring
from builtins import object
import builtins
import functools
import html.entities
import re
import os.path
import platform
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from html.parser import HTMLParser
import xml.etree.cElementTree as ET

import pymel.util as util
import pymel.versions as versions
from . import plogging
from pymel.mayautils import getMayaLocation
from future.utils import PY2, with_metaclass

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    # Allow import to succeed, even without bs4 - this allows unittesting to
    # import this, and test docstrings (ie, getFirstText)
    pass

from keyword import iskeyword as _iskeyword

FLAGMODES = ('create', 'query', 'edit', 'multiuse')

_logger = plogging.getLogger(__name__)

class MethodParseError(ValueError):
    '''Signal that there was a error parsing a method

    No cache data will be created for the current method, though parsing of
    other methods in the class will continue (unless in strict mode)
    '''
    pass

class UnmatchedNameError(ValueError):
    pass


def mayaIsRunning():
    # type: () -> bool
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


# The docs sometime contain entities as tags, like <lsquo />, instead of &lsquo;
# these methods help deal with that
def decodeEntity(tagname):
    codepoint = html.entities.name2codepoint.get(tagname)
    if codepoint is not None:
        return chr(codepoint)


def iterXmlTextAndElem(element):
    '''Like Element.itertext, except returns a tuple of (text, element, isEntity)

    Also handles entity-refs-as-tags, like <lsquo />
    '''
    tag = element.tag
    if not isinstance(tag, basestring) and tag is not None:
        return
    if len(element) == 0 and not element.text:
        # If this is an empty element - no text, no children - check if it's an
        # entity
        entityChar = decodeEntity(tag)
        if entityChar:
            yield (entityChar, element, True)
        return
    if element.text:
        yield (element.text, element, False)
    for e in element:
        isEntity = None
        for s in iterXmlTextAndElem(e):
            yield s
            # if e is an entity, then it will yield exactly one result,
            # whose isEntity will be True - so set isEntity based on first
            # returned result
            if isEntity is None:
                isEntity = s[-1]
        if e.tail:
            # bool isEntity is just so we return False, not None
            yield (e.tail, e, bool(isEntity))


# The docs sometime contain entities as tags, like <lsquo />, instead of &lsquo;
# these methods help deal with that
def decodeEntity(tagname):
    import html.entities
    codepoint = html.entities.name2codepoint.get(tagname)
    if codepoint is not None:
        return chr(codepoint)


def getFirstText(element, ignore=('ref', 'bold', 'emphasis', 'verbatim')):
    '''Finds a non-empty text element, then stops once it hits not first non-filtered sub-element

    >>> getFirstText(ET.fromstring('<top>Some text. <sub>Blah</sub> tail.</top>'))
    'Some text.'
    >>> getFirstText(ET.fromstring('<top><sub>Blah blah</sub> More stuff</top>'))
    'Blah blah'
    >>> getFirstText(ET.fromstring('<top> <sub>Blah blah <lsquo /><ref>someRef</ref><rsquo /> More stuff</sub> The end</top>'))
    u'Blah blah \u2018someRef\u2019 More stuff'
    '''
    chunks = []
    foundText = False

    for text, elem, isEntity in iterXmlTextAndElem(element):
        if not isEntity:
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
    # use iterXmlTextAndElem instead of element.itertext just so we decode
    # things like <lsquo />
    text = "".join(x[0] for x in iterXmlTextAndElem(element))
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
        if PY2:
            # python-2 won't error if we skip the init, while python-3 will
            # However, in python-2, we can't call super, because HTMLParser
            # is an "old-style" class
            return
        super(MLStripper, self).__init__()

    def handle_data(self, d):
        self.fed.append(d)

    def handle_startendtag(self, tag, attrs):
        entityChar = decodeEntity(tag)
        if entityChar:
            self.fed.append(entityChar)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

# This is mostly because python-2 doctest doesn't deal with unicode
def standardizeUnicodeChars(input):
    if PY2:
        if isinstance(input, str):
            return input
    return input.translate({
        0xb6: ord('\n'),  # the paragraph mark
        0x2018: ord("'"),  # single left quote
        0x2019: ord("'"),  # single right quote
        0x201C: ord('"'),  # double left quote
        0x201D: ord('"'),  # double right quote
    })


def standardizeDoc(input):
    return standardizeWhitespace(standardizeUnicodeChars(strip_tags(input)))


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
        self.internal = False  # True if this is marked as in the internal category
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
        if PY2:
            # encode our non-unicode 'data' string to unicode
            data = data.decode('utf-8')
            # now saftely encode it to non-unicode ascii, ignoring unknown characters
            data = data.encode('ascii', 'ignore')
        # Shortname
        if self.iData == 0:
            self.flags[self.currFlag]['shortname'] = data.lstrip('-\r\n')

        # Arguments
        elif self.iData == 1:
            typemap = {
                'string': str,
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
            data = data.replace('*', r'\*')  # for reStructuredText
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
        except KeyError as msg:
            pass
            #_logger.debug(self.currFlag, msg)

    def handle_starttag(self, tag, attrs):
        from future.moves.urllib.parse import urlparse

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
                else:
                    path = urlparse(attrmap.get('href', '')).path
                    if path.split('/')[-1] == 'cat_Internal.html':
                        # this is an internal command, and should be skipped...
                        self.internal = True
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

    if PY2:
        # Python-3 has a new convert_charrefs arg, which handles this much more
        # elegantly...
        def handle_entityref(self, name):
            appendFunc = None

            if self.active == 'examples':
                def appendFunc(decodedEntity):
                    self.example += decodedEntity
            elif self.active == 'flag':
                if self.currFlag and self.currFlag in self.flags and self.iData > 1:
                    # we're decoding a flag docstring
                    def appendFunc(decodedEntity):
                        self.flags[self.currFlag]['docstring'] += decodedEntity

            if appendFunc is not None:
                result = self.unescape("&" + name + ";")
                if isinstance(result, unicode):
                    try:
                        result = result.encode("ascii")
                    except UnicodeEncodeError:
                        pass
                appendFunc(result)

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
            data = data.replace('*', r'\*')  # for reStructuredText
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


# TODO : cache doc location or it's evaluated for each getCmdInfo !
# MayaDocsLoc(mayaDocsLocation())

class NodeHierarchyDocParser(HTMLParser):

    def parse(self):
        docloc = mayaDocsLocation(self.version)
        if not os.path.isdir(docloc):
            raise IOError("Cannot find maya documentation. Expected to find it at %s" % docloc)

        f = open(os.path.join(docloc, 'Nodes/index_hierarchy.html'))
        try:
            rawdata = f.read()
        finally:
            f.close()

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


# Use a class, instead of `NO_DEFAULT = object()`, because it's pickleable and
# printable
class NO_DEFAULT(object):
    '''Indicates that there was no default

    For situations where None is meaningful (ie, may be a standin for NULL)'''
    def __repr__(self):
        return type(self).__name__


class ParamInfo(object):
    __slots__ = ('defName', 'declName', 'type', 'typeQualifiers', 'default',
                 'direction', '_doc')

    def __init__(self, defName=None, declName=None, type=None,
                 typeQualifiers=(), default=NO_DEFAULT, direction='in', doc=''):
        self.defName = defName
        self.declName = declName
        self.type = type
        self.typeQualifiers = tuple(typeQualifiers)
        self.default = default
        self.direction = direction
        self.doc = doc

    def __repr__(self):
        import inspect
        argstrs = []
        argspec = inspect.getargspec(self.__init__)
        # ignore self
        args = argspec.args[1:]
        # all args have defaults
        assert len(args) == len(argspec.defaults)
        for name, default in zip(args, argspec.defaults):
            val = getattr(self, name)
            if val != default:
                argstrs.append('{}={!r}'.format(name, val))
        return '{}({})'.format(type(self).__name__, ', '.join(argstrs))

    # traditionally, we've preferred the defName, both because that name is
    # featured more prominently in the maya api help docs, and because it's
    # generally more descriptive
    @property
    def name(self):
        if self.defName:
            return self.defName
        return self.declName

    @name.setter
    def name(self, val):
        self.defName = val
        self.declName = val

    # force standardizeWhitespace for doc
    @property
    def doc(self):
        return self._doc

    @doc.setter
    def doc(self, rawVal):
        self._doc = standardizeDoc(rawVal)

    def qualifiedTypeName(self):
        if not self.type:
            raise ValueError('No type specified')
        parts = [str(self.type)]
        for qual in self.typeQualifiers:
            if qual == 'unsigned':
                parts.insert(0, 'unsigned ')
            elif qual == 'const':
                parts.append(' const')
            else:
                parts.append(qual)
        return ''.join(parts)


class ApiDocParser(with_metaclass(ABCMeta, object)):
    NO_PYTHON_MSG = ['NO SCRIPT SUPPORT.', 'This method is not available in Python.']
    DEPRECATED_MSG = ['This method is obsolete.', 'Deprecated', 'Obsolete -']

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
    BASIC_NUMERIC_TYPES = ['int', 'double', 'float', 'uint', 'uchar']

    NON_MFN_FULL_PARSE_CLASSES = {
        'MAngle',
        'MBoundingBox',
        'MColor',
        'MDistance',
        'MEulerRotation',
        'MFloatMatrix',
        'MFloatPoint',
        'MFloatVector',
        'MItCurveCV',
        'MItMeshEdge',
        'MItMeshPolygon',
        'MItMeshVertex',
        'MMatrix',
        'MPlug',
        'MPoint',
        'MQuaternion',
        'MSelectionList',
        'MSpace',
        'MTime',
        'MTransformationMatrix',
        'MVector',
    }

    SKIP_PARSING_METHODS = {
        # Not documented anywhere at all, so presumably private, and no name
        # available for params
        ('MFnBase', 'objectChanged'),
        ('MFnFluid', 'objectChanged'),
        ('MFnLattice', 'objectChanged'),
        ('MFnNurbsCurve', 'objectChanged'),
        ('MFnNurbsSurface', 'objectChanged'),
        ('MFnParticleSystem', 'objectChanged'),
        ('MFnTransform', 'objectChanged'),
    }

    CPP_OPERATOR_TO_PY = {
        '*=': '__imul__',
        '*': '__mul__',
        '+=': '__iadd__',
        '+': '__add__',
        '-=': '__isub__',
        '-': '__sub__',
        '/=': '__itruediv__',
        '/': '__truediv__',
        '==': '__eq__',
        '!=': '__ne__',
        '[]': '__getitem__'
    }

    PY_OPERATOR_DEFAULT_NAMES = {val: 'other' for (key, val)
                                 in CPP_OPERATOR_TO_PY.items()}
    PY_OPERATOR_DEFAULT_NAMES['__getitem__'] = 'key'

    # Sometimes the defnames don't show up in the xmls for some reason... can
    # add manual (and hopefully temporary?) overrides here
    DEFNAMES = {
    }

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
            raise IOError("Cannot find maya documentation. Expected to find it at %s" % self.docloc)
        self.strict = strict

        self.enums = {}
        self.pymelEnums = {}
        self.methods = util.defaultdict(list)
        self.currentMethodName = None
        self._currentRawMethod = None
        self._methodCache = {}
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

    @classmethod
    def shouldSkip(cls, apiClsName):
        # in theroy, we could move these into shoudParseEnumOnly, but
        # traditionally these were always skipped, and see no reason to increase
        # the sizes of the caches...
        return apiClsName.startswith('MPx')

    @classmethod
    def shouldParseEnumOnly(cls, apiClsName):
        if apiClsName.startswith('MFn'):
            return False
        return apiClsName not in cls.NON_MFN_FULL_PARSE_CLASSES

    @classmethod
    def splitArrayType(cls, origType):
        # type: (Union[str, ApiEnum]) -> Tuple[str, Optional[int]]
        '''Given a typeName like double__array3, returns ('double', 3)

        Returns
        -------
        str
            The base name of the type, without any array suffix
        Optional[int]
            The size of the array, or None if not an array type
        '''
        if isinstance(origType, str):
            splitName = origType.rsplit('__array', 1)
            if len(splitName) == 2:
                try:
                    arraySize = int(splitName[1])
                    return (splitName[0], arraySize)
                except ValueError:
                    pass
        return (origType, None)

    @classmethod
    def isGettableArg(cls, param):
        # type: (ParamInfo) -> bool
        if '&' in param.typeQualifiers:
            return True
        baseType, arraySize = cls.splitArrayType(param.type)
        if arraySize is not None and baseType in cls.BASIC_NUMERIC_TYPES:
            return True
        return False

    # We use a property here just to make sure that _methodCache is cleared
    # when method changes
    @property
    def currentRawMethod(self):
        return self._currentRawMethod

    @currentRawMethod.setter
    def currentRawMethod(self, val):
        self._methodCache = {}
        self._currentRawMethod = val

    # property for defining retrievers that are cached per method
    @staticmethod
    def methodcached(getter):
        name = getter.__name__

        @functools.wraps(getter)
        def cached_getter(self, *args, **kwargs):
            if name not in self._methodCache:
                self._methodCache[name] = getter(self, *args, **kwargs)
            return self._methodCache[name]

        return cached_getter

    def fullMethodName(self, paramInfos=None):
        className = self.apiClassName or "<no class>"
        methodName = self.currentMethodName or "<no method>"
        result = className + '.' + methodName
        if paramInfos:
            types = ', '.join(x.qualifiedTypeName() for x in paramInfos)
            result = '{}({})'.format(result, types)
        return result

    def formatMsg(self, *args):
        return self.fullMethodName() + ': ' + ' '.join([str(x) for x in args])

    def xprint(self, *args):
        if self.verbose:
            print(self.formatMsg(*args))

    def getPymelMethodNames(self):
        pymelNames = {}
        pairsList = []

        def addSetGetPair(setmethod, getMethod):
            # if None of the setMethods has any args, it's not usable in a get /
            # set pair...
            if not any(info['args'] for info in self.methods[setMethod]):
                return

            pairsList.append((setMethod, getMethod))
            # pair 'set' with 'is/get'
            for info in self.methods[setMethod]:
                info['inverse'] = (getMethod, True)

            # pair 'is/get' with 'set'
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
                        addSetGetPair(setMethod, origGetMethod)

                    # fix get
                    else:
                        newGetMethod = 'g' + setMethod[1:]  # remove 's'
                        pymelNames[origGetMethod] = newGetMethod
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
            apiEnumNames = list(apiEnumNames._keys.keys())
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
            splitZip = list(zip(*splitEnums))
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
        pymelKeyDict = OrderedDict()
        docs = dict(apiEnum._docs)
        for apiName, val in apiEnum._keys.items():
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
                _logger.warning("Suspected Bad Enum: %s", type)
        else:
            type = str(type)
        return type

    def handleEnumDefaults(self, default, type):

        if default is None:
            return default

        if isinstance(type, self.enumClass):

            # the enum is on another class
            if '::' in default:
                splitDefault = default.split('::')
                apiClass = splitDefault[:-1]
                enumConst = splitDefault[-1]
                # For old-style (int-based) enums, we may have:
                #    type = ('MSpace', 'Space')
                #    default = 'MSpace::kObject'
                # For new style (class-based) enums, we may have:
                #    type = ('MFnGeometryData', 'GroupTagCategory')
                #    default = 'MFnGeometryData::GroupTagCategory::kAuto'
                # This check should work for either...
                assert tuple(apiClass) == tuple(type)[:len(apiClass)]
            else:
                enumConst = default

            return self.enumClass([type[0], type[1], enumConst])

        return default

    def getOperatorName(self, methodName):
        op = methodName[len('operator'):].strip()
        # print "operator", methodName, op
        return self.CPP_OPERATOR_TO_PY.get(op, None)

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
                'NULL': None,
                'nullptr': None,
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
                    return (self.parseValue(numerator, valueType)
                            / self.parseValue(divisor, valueType))
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
        return ParamInfo(type=argtype, typeQualifiers=tokens)

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
            for apiName, pymelName in apiToPymelNames.items():
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
        methodName, returnInfo = self.getMethodNameAndOutput()
        if methodName is None:
            return

        if (self.apiClassName, methodName) in self.SKIP_PARSING_METHODS:
            return

        # Old html parser filtered these from returnQualifiers, so we enforce
        # this too, for consistency
        returnInfo.typeQualifiers = [x for x in returnInfo.typeQualifiers
                                     if x not in ['const', 'unsigned'] and x]

        # skip constructors and destructors
        if methodName.startswith('~') or methodName == self.apiClassName:
            return

        # convert operators to python special methods
        if methodName.startswith('operator'):
            methodName = self.getOperatorName(methodName)
            if methodName is None:
                return

        # no MStatus in python
        if returnInfo.type in ['MStatus', 'void']:
            returnInfo.type = None

        # convert to unicode
        self.currentMethodName = str(methodName)

        result = self._parseMethod(returnInfo)

        # used to reset these to none using a try/finally, but then some
        # error handlers couldn't use them, reducing their usefulness
        self.currentMethodName = None
        self.currentRawMethod = None
        return result

    def _parseMethod(self, returnInfo):
        # There's no central point (in both Html and Xml) before here where
        # we know it's not an enum... so we do the check here
        if self.shouldParseEnumOnly(self.apiClassName):
            return

        self.xprint("RETURN", returnInfo.type)

        if self.hasNoPython():
            return

        paramInfos = self.parseArgTypes()

        try:
            deprecated = self.isDeprecated()
            methodDoc = self.getMethodDoc()
            paramInfos, returnInfo = self.parseMethodArgs(paramInfos, returnInfo)
        except MethodParseError as msg:
            if self.strict:
                raise
            _logger.error(self.formatMsg("FAILED", str(msg)))
            return

        paramInfos = [x for x in paramInfos if x.type != 'MStatus']

        # correct bad outputs
        if (self.isGetMethod() and (not returnInfo.type
                                    or returnInfo.type =='MStatus')
                and not any(x.direction == 'out' for x in paramInfos)):
            for param in paramInfos:
                if self.isGettableArg(param):
                    _logger.warning("%s.%s(%s): Correcting suspected output argument '%s' because there are no outputs and the method is prefixed with 'get' ('%s')" % (
                        self.apiClassName, self.currentMethodName,
                        ', '.join(x.name for x in paramInfos), param.name,
                        param.doc))
                    param.direction = 'out'

        if returnInfo.type is None:
            returnInfo.doc = ''

        # TODO: eliminate all the redundant data - all we really need is:
        #       - args (as list of ParamInfos - make them serializable to/from a sparse dict)
        #       - return (as a ParamInfo)
        #       - doc
        #       - static
        #       - deprecated
        #    Ideally, encapsulate this in a MethodInfo class (also serializable
        #    to a sparse dict)
        #    Will probably need to version up PY_CACHE_FORMAT_VERSION as well

        # build out dicts / lists from paramInfos
        argInfo = {}
        types = {}
        typeQualifiers = {}
        defaults = {}
        argList = []
        inArgs = []
        outArgs = []

        for param in paramInfos:
            argInfo[param.name] = {'type': param.type, 'doc': param.doc}
            types[param.name] = param.type
            if param.typeQualifiers:
                typeQualifiers[param.name] = list(param.typeQualifiers)
            if param.default is not NO_DEFAULT:
                defaults[param.name] = param.default
            argList.append((param.name, param.type, param.direction))
            if param.direction == 'in':
                inArgs.append(param.name)
            else:
                outArgs.append(param.name)

        # sanity check that we didn't have some weird collision between
        # declNames and defNames
        assert len(types) == len(paramInfos)
        assert set(types) == set(x.name for x in paramInfos)

        methodInfo = {'argInfo': argInfo,
                      'returnInfo': {'type': returnInfo.type,
                                     'doc': returnInfo.doc,
                                     'qualifiers': returnInfo.typeQualifiers},
                      'args': argList,
                      'returnType': returnInfo.type,
                      'inArgs': inArgs,
                      'outArgs': outArgs,
                      'doc': standardizeDoc(methodDoc),
                      'defaults': defaults,
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
            print("To reproduce run:\n%r.parse(%r)" % (self, apiClassName))
            print(self.formatMsg("Unknown error"))
            raise

        pymelNames = invertibles = None
        if not self.shouldParseEnumOnly(apiClassName):
            pymelNames, invertibles = self.getPymelMethodNames()

        parsed = {
            'methods': dict(self.methods),
            'enums': self.enums,
            'pymelEnums': self.pymelEnums,
        }
        if pymelNames:
            parsed['pymelMethods'] = pymelNames
        if invertibles:
            parsed['invertibles'] = invertibles
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
    def isDeprecated(self):
        raise NotImplementedError()

    @abstractmethod
    def getMethodDoc(self):
        raise NotImplementedError()

    @abstractmethod
    def parseMethodArgs(self, paramInfos, returnInfo):
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
    _backslashTagRe = re.compile(r'(?:^|(?<=\s))\\(\S+)(?:$|\s+)', re.MULTILINE)
    _paramDirRe = re.compile(r'^param\[(?P<dir>in|out|in,out|inout)\]$')

    def fullMethodName(self, paramInfos=None):
        fullName = super(XmlApiDocParser, self).fullMethodName(paramInfos)
        if not paramInfos and self.currentRawMethod is not None:
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
        paramInfos = []

        # TYPES
        for param in self.currentRawMethod.findall('param'):
            rawType = xmlText(param.find('type'))
            paramInfo = self.parseType(rawType.split())

            paramInfo.defName = xmlText(param.find('defname'))
            paramInfo.declName = xmlText(param.find('declname'))

            arrayInfo = param.find('array')
            if arrayInfo is not None:
                brackets = xmlText(arrayInfo)
                if brackets:
                    numbuf = self._bracketRe.split(brackets)
                    if len(numbuf) > 1:
                        if not isinstance(paramInfo.type, str):
                            if isinstance(paramInfo.type, self.enumClass):
                                raise TypeError("%s should be a string, but it has been marked as an enum. "
                                                "Check if it is a new type which should be added to "
                                                "OTHER_TYPES or MISSING_TYPES on this class." % (paramInfo.type,))
                            else:
                                raise TypeError("%r should be a string" % (paramInfo.type,))
                        # Note that these two args need to be cast differently:
                        #   int2 foo;
                        #   int bar[2];
                        # ... so, instead of storing the type of both as
                        # 'int2', we make the second one 'int__array2'
                        paramInfo.type = paramInfo.type + '__array' + numbuf[1]
                    else:
                        print("this is not a bracketed number", repr(brackets), paramInfo.type)

            # can't use None, which may indicate 'NULL'
            paramInfo.default = NO_DEFAULT
            defaultElem = param.find('defval')
            if defaultElem is not None:
                default = xmlText(defaultElem)
                if paramInfo.default:
                    paramInfo.default = self.parseValue(default, paramInfo.type)
                    self.xprint('DEFAULT', default)
            paramInfos.append(paramInfo)
        # filter myFunc(void) type funcs - this also gets stuff like "myFunc(void) const"
        if all(x.defName == '' and x.declName == '' and x.type == 'void'
                for x in paramInfos):
            return []

        return paramInfos

    def isMayaEnumFunc(self, element):
        return bool(element.find("./[name='OPENMAYA_ENUM']"))

    def _parseEnum(self, enumData):
        kind = enumData.attrib.get('kind')
        if kind == 'enum':
            results = self._parseEnum_normal(enumData)
        elif kind == 'function' and self.isMayaEnumFunc(enumData):
            results = self._parseEnum_func(enumData)
        else:
            raise ValueError("Got unrecognized enum: {}".format(enumData))

        if not results['values']:
            return

        if self._anonymousEnumRe.match(results['name']):
            # for an example of an anonymous enum, see MFnDagNode.kNextPos
            for key, value in results['values'].items():
                self.constants[key] = value
            return
        return results

    def _parseEnum_normal(self, enumData):
        # use OrderedDict so that the first-parsed name for a given int-enum-
        # value will become the default. This seems as good a pick as any for
        # the default, and it will make python2+3 behavior consistent
        enumValues = OrderedDict()
        enumDocs = {}
        enumName = xmlText(enumData.find('name'))
        self.currentMethodName = enumName
        self.xprint("ENUM", enumName)

        for enumValue in enumData.findall('enumvalue'):
            enumKey = xmlText(enumValue.find('name'))
            try:
                enumVal = getattr(self.apiClass, enumKey)
            except:
                _logger.warning("%s.%s of enum %s does not exist" % (self.apiClassName, enumKey, self.currentMethodName))
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

        return {'values': enumValues, 'docs': enumDocs, 'name': enumName}

    def _parseEnum_func(self, enumData):
        '''Parse an OPENMAYA_ENUM style enum declaration'''

        enumName = None
        # use OrderedDict so that the first-parsed name for a given int-enum-
        # value will become the default. This seems as good a pick as any for
        # the default, and it will make python2+3 behavior consistent
        enumValues = OrderedDict()

        self.currentMethodName = 'OPENMAYA_ENUM' # placeholder
        self.xprint("ENUM", enumName)

        for param in enumData.findall("./param"):
            enumKey = param.find('type')
            if enumKey is None:
                raise ValueError("Unable to process OPENMAYA_ENUM - one of the"
                    " params had no type tag: {}".format(enumData))
            enumKey = xmlText(enumKey)
            if enumName is None:
                # the first param is actually the enum name
                enumName = enumKey
                self.currentMethodName = enumName
                continue

            try:
                enumVal = getattr(self.apiClass, enumKey)
            except:
                _logger.warning("%s.%s of enum %s does not exist" % (self.apiClassName, enumKey, self.currentMethodName))
                continue
            enumValues[enumKey] = enumVal

        if enumName is None:
            raise ValueError(
                "Unable to process OPENMAYA_ENUM - no name found: {}".format(
                    enumData))

        # it seems that OPENMAYA_ENUM style enums never have docs for
        # enum values - as an example, see M3dView::TextPosition - in
        # the 2019 docs, we can see a description of each enum value:
        #   http://help.autodesk.com/cloudhelp/2019/CHS/Maya-SDK-MERGED/cpp_ref/class_m3d_view.html#a8e0d441725a81d2bbdebbea09078260e
        # ...but nothing similar can be found in 2020 docs:
        #   http://help.autodesk.com/view/MAYAUL/2020/ENU/?guid=Maya_SDK_MERGED_cpp_ref_class_m3d_view_html
        return {'values': enumValues, 'docs': {}, 'name': enumName}

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
                currentTextChunks.append(' - ')
                continue

            yield (currentTag, ''.join(currentTextChunks))
            currentTextChunks = []
            currentTag = newTag

        currentTextChunks.append(text[lastPosition:])
        yield (currentTag, ''.join(currentTextChunks))

    @classmethod
    def parseBackslashTags(cls, text, allTags=True):
        info = {
            'params': OrderedDict(),
            'returnDoc': '',
        }
        remainingPieces = []
        for tag, tagText in cls.iterBackslashTags(text):
            if tag is None:
                remainingPieces.append(tagText)
            else:
                paramMatch = cls._paramDirRe.match(tag)
                if paramMatch is not None:
                    splitText = tagText.strip().split()
                    name = splitText[0]
                    paramInfo = ParamInfo(
                        defName=name,
                        direction=paramMatch.group('dir'),
                        # Because this didn't parse correctly, it may have some tags
                        # still in the text - ie, "<i>merged</i>" (which gets encoded
                        # in the xml as: "&lt;i&gt;merged&lt;/i&gt")
                        doc=strip_tags(' '.join(splitText[1:]))
                    )
                    info['params'][name] = paramInfo
                elif tag == 'return':
                    info['returnDoc'] = strip_tags(tagText)
                else:
                    if allTags:
                        info.setdefault(tag, []).append(tagText)
                    else:
                        remainingPieces.append('{} {}'.format(tag, tagText))
        info['remainingText'] = strip_tags(''.join(remainingPieces)).strip()
        return info

    @ApiDocParser.methodcached
    def findDetailedDescription(self):
        return self.currentRawMethod.find('detaileddescription')

    def getMethodDoc(self):
        brief = self.currentRawMethod.find('briefdescription')
        if brief is not None:
            briefText = getFirstText(brief)
            if briefText and briefText not in self.DEPRECATED_MSG \
                    and briefText not in self.NO_PYTHON_MSG:
                return briefText

        detail = self.findDetailedDescription()

        doc = ''
        if detail is not None:
            for para in detail.findall('para'):
                paraText = getFirstText(para)
                if paraText:
                    doc = paraText
                    doc = self.parseBackslashTags(doc, allTags=True)['remainingText']
                    if doc:
                        break
        return doc

    def parseMethodArgs(self, oldParamInfos, returnInfo):
        detail = self.findDetailedDescription()

        if returnInfo.type and detail is not None:
            returnElem = detail.find(".//simplesect[@kind='return']")
            returnInfo.doc = xmlText(returnElem)

        paramDescriptions = []
        if detail is not None:
            # for some reason, some clases (ie, MFnMesh) have multiple
            # parameter lists...
            for paramList in detail.findall(".//parameterlist[@kind='param']"):
                paramDescriptions.extend(paramList.findall('parameteritem'))

        paramElemsAndInfos = []
        paramsByName = {}
        for paramElem in paramDescriptions:
            allNames = paramElem.find('parameternamelist').findall('parametername')

            # Don't have an example of nameList > 1, so error for now
            if len(allNames) > 1:
                raise ValueError(self.formatMsg("found more than 1 name for parameter {!r}".format(name)))

            name = xmlText(allNames[0])
            doc = xmlText(paramElem.find('parameterdescription'))
            direction = allNames[0].attrib['direction']
            paramInfo = ParamInfo(name, doc=doc, direction=direction)
            paramsByName[name] = paramInfo
            paramElemsAndInfos.append((paramElem, paramInfo))

        if len(paramDescriptions) > len(oldParamInfos):
            # make sure there isn't an extra MStatus throwing things off - this
            # happened in, ie, MDagPath::matchTransform
            if (len(paramDescriptions) == len(oldParamInfos) + 1
                    and paramElemsAndInfos[-1][1].defName == 'ReturnStatus'):
                del paramsByName['ReturnStatus']
                del paramDescriptions[-1]
                del paramElemsAndInfos[-1]
            else:
                msg = "found more ({}) parameter descriptions than parameter " \
                      "declarations ({})".format(
                    len(paramDescriptions), len(oldParamInfos))
                raise ValueError(self.formatMsg(msg))

        paramsByPosition = []

        def parseRawTagInfo(text, prepend=False):
            # if we parse, and FIND an existing item, any new items we find
            # should be inserted after that... otherwise, we insert at beginning
            # if prepend=True, else append at end
            if prepend:
                insertPosition = 0
            else:
                insertPosition = None
            parsedTags = self.parseBackslashTags(text)
            for paramName, paramInfo in parsedTags['params'].items():
                existingParam = paramsByName.get(paramName)
                if not existingParam:
                    paramsByName[paramName] = paramInfo
                    if insertPosition is None:
                        paramsByPosition.append(paramInfo)
                    else:
                        paramsByPosition.insert(insertPosition, paramInfo)
                        insertPosition += 1
                else:
                    insertPosition = paramsByPosition.index(existingParam) + 1

            if not returnInfo.doc and parsedTags['returnDoc']:
                returnInfo.doc = parsedTags['returnDoc']
            return parsedTags['remainingText']

        # sometimes the param docs don't get parsed correctly, with the result
        # that the parameter list jumps from param5 to param7, and the docstring
        # for param5 contains the (unparsed) info for param6.
        #
        # As an example, this happens in the 2019 xml docs,
        # MCameraSetMessage.addCameraLayerCallback - the docs for
        # 'clientData' appear inside the docs for 'func'
        #
        # To deal with this, after doing an initial pass, where we record all
        # the known names, we then go back and do a second pass, looking for
        # missing params that can be parsed from the docstrings
        for paramElem, paramInfo in paramElemsAndInfos:
            paramsByPosition.append(paramInfo)
            paramInfo.doc = parseRawTagInfo(paramInfo.doc)

        # Sometimes, "parameteritem" xml objects may not be properly created,
        # but (manually) parsable information still exists in the
        # detaileddescription ie, this happens in the 2019 MFnMesh.addPolygon
        # 2nd overload (with 6 args)
        if detail is not None:
            # Params found this way generally need to go at start, so prepend
            parseRawTagInfo(xmlText(detail), prepend=True)

        assert len(paramsByPosition) <= len(oldParamInfos)
        assert all(x.name for x in paramsByPosition)

        if len(paramsByPosition) != len(paramsByName):
            # Ok, we have at least one name that was doubled - it's possible
            # this is a type or copy / paste error, that can be fixed, if only
            # one item was doubled, and we can safely map back to oldParamInfos
            #
            # For an example of where this correction applies, see docs for
            # MFnNumericAttribute.getMin in 2019 - min3 is repeated twice
            # (second should be min4)
            #
            # start by finding all doubles
            positionsByName = {}
            for i, paramInfo in enumerate(paramsByPosition):
                positionsByName.setdefault(paramInfo.name, []).append(i)

            multiVals = [(name, positions) for name, positions
                         in positionsByName.items() if len(positions) > 1]
            if len(multiVals) > 1:
                multiValNames = sorted(x[0] for x in multiVals)
                msg = 'Found more than one param name in <parameterlist> that' \
                      ' was repeated: {}'.format(', '.join(multiValNames))
                raise ValueError(self.formatMsg(msg))
            repeatedName, positions = multiVals[0]
            if len(positions) > 2:
                msg = 'Param repeated more than twice in <parameterlist>: {}' \
                    .format(repeatedName)
                raise ValueError(self.formatMsg(msg))

            # Ok, was only one param name that got repeated twice - see if
            # we can find a param with a matching name at the same position
            # within oldParamInfos, for only one of those positions
            oldPositionMatches = [i for i, param in enumerate(oldParamInfos)
                                  if (param.declName == repeatedName or
                                      param.defName == repeatedName)]
            if len(oldPositionMatches) == 1 \
                    and oldPositionMatches[0] in positions:
                # check to make sure the param at the other position has a name,
                # that isn't used
                matchedPos = oldPositionMatches[0]
                positions.remove(matchedPos)
                unmatchedPos = positions[0]
                otherParam = oldParamInfos[unmatchedPos]
                names = [x for x in [otherParam.declName, otherParam.defName]
                         if x]
                if names and all(x not in paramsByName for x in names):
                    # ok, the param at the other position had a name we haven't
                    # seen. Replace the name with this
                    paramsByPosition[unmatchedPos].defName = otherParam.name
                    paramsByName[otherParam.name] = paramsByPosition[unmatchedPos]
                    # also make sure that the original, duped name refers to
                    # the matched pos - it may be referring to the one whose
                    # name we just fixed
                    matchedParam = paramsByPosition[matchedPos]
                    paramsByName[matchedParam.name] = matchedParam
            assert len(paramsByPosition) == len(paramsByName)

        # Ok, we now have two ordered lists of parameters:
        # - oldParamInfos
        #   - parsed from <param> tags
        #   - post 2019, missing <defname> - and may be missing declname too
        #   - no docs
        #   - information mostly filled in via C++ syntax parsing, so what's
        #     there should be fairly reliable
        # - paramsByPosition
        #   - parsed from <parameteritem> within the <parameterlist>
        #   - filled in from doxygen parsing of docstrings, so less reliable
        #     (a lot of docstring formatting errors)
        #   - however, usually may be only source of defnames (since Autodesk's
        #     doxygen comments generally seem to be from the .cpp)... and pymel
        #     prefers defnames (they're more emphasized in official docs, plus
        #     the names are generally more descriptive... also, need to keep
        #     using defnames for backward compatibility)
        #   - should always have a name
        #   - generally only source of doc (though may be missing)

        # So, without defnames in oldParamInfos, there's no guaranteed way to
        # link up the two lists, and we need to cross-correllate... so we hope
        # that the number of parameters is the same

        if len(oldParamInfos) != len(paramsByPosition):
            # first, try removing MStatus params, since those will get stripped
            # out later anyway
            nonMStatus = [x for x in oldParamInfos if x.type != 'MStatus']
            if len(nonMStatus) == len(paramsByPosition):
                oldParamInfos = nonMStatus
            elif len(paramsByPosition):
                msg = "Was at least one <parameteritem> in <parameterlist>, " \
                      "but total number did not match number found when " \
                      "parsing <param> items"
                raise ValueError(self.formatMsg(msg))

        # if a param name appears in both lists, it should be at the same
        # position...

        try:
            for i, oldParam in enumerate(oldParamInfos):
                for nameType in ('declName', 'defName'):
                    oldName = getattr(oldParam, nameType)
                    if oldName in paramsByName:
                        newName = paramsByPosition[i].defName
                        if newName != oldName:
                            msg = "param list names did not match - {i}'th " \
                                  "<param> had {nameType} {oldName}, " \
                                  "but {i}'th <parameteritem> had name " \
                                  "{newName} "\
                                .format(**locals())
                            raise UnmatchedNameError(self.formatMsg(msg))
                        break
        except UnmatchedNameError as e:
            # the oldParams have the definitive ordering, since they're pulled
            # from C++ parsing.  See if there's at most one param in the new
            # params that we can't definitively link to the old params, and if
            # so, just use the old param ordering.

            defIndices = {x.defName: i for i, x in enumerate(oldParamInfos)}
            declIndices = {x.declName: i for i, x in enumerate(oldParamInfos)}
            remappedPositions = [None] * len(paramsByPosition)
            for i, newParam in enumerate(paramsByPosition):
                defI = defIndices.pop(newParam.defName, None)
                declI = declIndices.pop(newParam.defName, None)
                bothIndices = set([defI, declI])
                if defI is None:
                    if declI is not None:
                        remappedPositions[i] = declI
                else:
                    if declI is None or defI == declI:
                        remappedPositions[i] = defI
            canRemap = False
            numMissing = remappedPositions.count(None)
            if numMissing == 0:
                canRemap = True
            elif numMissing == 1:
                missingIndex = set(range(len(oldParamInfos))) \
                               - set(remappedPositions.values())
                assert len(missingIndex) == 1
                missingIndex = missingIndex.pop()
                remappedPositions[remappedPositions.index(None)] = missingIndex
                canRemap = True
            if canRemap:
                reorderedParams = [None] * len(paramsByPosition)
                for i, param in enumerate(paramsByPosition):
                    reorderedParams[remappedPositions[i]] = param
                assert None not in reorderedParams
                paramsByPosition = reorderedParams
            else:
                UnmatchedNameError.msg += ' (and could not reorder)'
                raise UnmatchedNameError

        assert (not paramsByPosition
                or len(paramsByPosition) == len(oldParamInfos))

        methodSignature = self.fullMethodName(oldParamInfos)
        bakedDefNames = self.DEFNAMES.get(methodSignature)
        if bakedDefNames:
            assert len(bakedDefNames) == len(oldParamInfos)
            for param, defName in zip(oldParamInfos, bakedDefNames):
                param.defName = defName
            if not(paramsByPosition):
                # do this so the arg direction correction code will run
                paramsByPosition = list(oldParamInfos)

        # all the newParams and oldParams should line up now - go through
        # and fill in all oldParams with names, directions, and docs from
        # newParams
        for newParam, oldParam in zip(paramsByPosition, oldParamInfos):
            if oldParam.defName:
                assert oldParam.defName == newParam.defName
            else:
                oldParam.defName = newParam.defName
            assert oldParam.name
            oldParam.doc = newParam.doc

            fullName = self.fullMethodName(oldParamInfos)
            if newParam.direction == 'in':

                # attempt to correct bad in/out docs
                if self._fillStorageResultRe.search(newParam.doc):
                    _logger.warning(
                        "{}: Correcting suspected output argument '{}' based on doc '{}'".format(
                        fullName, newParam.name, newParam.doc))
                    newParam.direction = 'out'
                elif not self.isSetMethod() and '&' in oldParam.typeQualifiers \
                        and oldParam.type in self.BASIC_NUMERIC_TYPES:
                    _logger.warning(
                        "{}: Correcting suspected output argument '{}' based on reference type '{} &' ('{}')".format(
                        fullName, newParam.name, oldParam.type, newParam.doc))
                    newParam.direction = 'out'
            elif newParam.direction == 'out':
                if oldParam.type == 'MAnimCurveChange':
                    _logger.warning(
                        "{}: Setting MAnimCurveChange argument '{}' to an input arg (instead of output)".format(
                        fullName, newParam.name))
                    newParam.direction = 'in'
            elif newParam.direction in ('in,out', 'inout'):
                # it makes the most sense to treat these types as inputs
                # maybe someday we can deal with dual-direction args...?
                newParam.direction = 'in'
            elif newParam.direction is not None:
                raise ValueError("direction must be either 'in', 'out', 'inout', or 'in,out'. got {!r}".format(newParam.direction))

            oldParam.direction = newParam.direction

        noNames = [i for i, param in enumerate(oldParamInfos) if not param.name]
        if noNames:
            defaultName = self.PY_OPERATOR_DEFAULT_NAMES.get(
                self.currentMethodName)
            if defaultName is not None and noNames == [0]:
                oldParamInfos[0].name = defaultName
            else:
                msg = "unable to determine a name for parameters at these " \
                      "indices: {}".format(', '.join(str(x) for x in noNames))
                raise MethodParseError(self.formatMsg(msg))

        return oldParamInfos, returnInfo


    def getMethodNameAndOutput(self):
        methodName = self.currentRawMethod.find("name").text

        returnType = xmlText(self.currentRawMethod.find("type"))
        returnInfo = self.parseType(returnType.split())

        return methodName, returnInfo

    def getClassPath(self):
        self.baseFilename = self.getClassFilename()
        filename = self.baseFilename + '.xml'
        apiBase = os.path.join(self.docloc, 'xml')
        return os.path.join(apiBase, filename)

    def parseBody(self):
        for enum in self.cdef.findall("./*/memberdef[@kind='enum'][@prot='public']"):
            self.parseEnum(enum)

        for enumFunc in self.cdef.findall("./*/memberdef[@kind='function'][name='OPENMAYA_ENUM']"):
            self.parseEnum(enumFunc)

        # This is an optimization - _parseMethod will skip all functions if
        # shouldParseEnumOnly is True, but if we exit here, we can save some
        # time (and potentially avoid some errors). Sadly, Html parser can't
        # do a similar early exit
        if self.shouldParseEnumOnly(self.apiClassName):
            return

        for func in self.cdef.findall("./*/memberdef[@kind='function']"):
            # skip OPENMAYA_ENUM, those are handled by parseEnum, above
            if self.isMayaEnumFunc(func):
                continue

            # We take public functions, and protected virtual functions
            # Protected virtual funcs may not be exposed if the method they override
            # isn't public, but better to be overly inclusive
            protection = func.attrib.get('prot')
            if (protection == 'public' or
                    (protection == 'protected' and func.attrib.get('virt') == 'virtual')):
                self.parseMethod(func)


class HtmlApiDocParser(ApiDocParser):
    _enumRe = re.compile('Enumerator')
    _paramPostNameRe = re.compile(r'([^=]*)(?:\s*=\s*(.*))?')

    def parseArgTypes(self):
        tmpTypes = []
        # TYPES
        for paramtype in self.currentRawMethod.findAll('td', **{'class': 'paramtype'}):
            buf = []
            for x in paramtype.findAll(text=True):
                buf.extend(x.split())
                # if x.strip() not in ['', '*', '&', 'const', 'unsigned'] ]
            buf = [x.strip().encode('ascii', 'ignore') for x in buf if x.strip()]
            tmpTypes.append(self.parseType(buf))

        paramInfos = []

        # ARGUMENT NAMES
        i = 0
        for paramname in self.currentRawMethod.findAll('td', **{'class': 'paramname'}):
            buf = [x.strip().encode('ascii', 'ignore') for x in paramname.findAll(text=True) if x.strip() not in['', ',']]
            if not buf:
                continue
            defName = declName = buf[0]
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
                        print("this is not a bracketed number", repr(brackets), joined)

                if default is not None:
                    default = self.parseValue(default, type)
                    # default must be set here, because 'NULL' may mean default is set to back to None,
                    # but in this case it is meaningful (ie, doesn't mean "there was no default")
                    self.xprint('DEFAULT', default)

            paramInfos.append(ParamInfo(defName=defName, declName=declName,
                                        type=type,
                                        typeQualifiers=qualifiers,
                                        default=default))
            i += 1
        return paramInfos

    def _parseEnum(self, rawEnum):
        # use OrderedDict so that the first-parsed name for a given int-enum-
        # value will become the default. This seems as good a pick as any for
        # the default, and it will make python2+3 behavior consistent
        enumValues = OrderedDict()
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
                _logger.warning("%s.%s of enum %s does not exist" % (self.apiClassName, enumKey, self.currentMethodName))
                enumVal = None
            enumValues[enumKey] = enumVal
            # TODO:
            # do we want to feed the docstrings to the Enum object itself
            # (which seems to have support for docstrings)? Currently, we're
            # not...
            docItem = em.next.next.next.next.__next__

            if isinstance(docItem, NavigableString):
                enumDocs[enumKey] = str(docItem).strip()
            else:
                enumDocs[enumKey] = str(docItem.contents[0]).strip()

        return {'values': enumValues, 'docs': enumDocs, 'name': self.currentMethodName}

    def hasNoPython(self):
        # ARGUMENT DIRECTION AND DOCUMENTATION
        addendum = self.findAddendum()
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

    @ApiDocParser.methodcached
    def findAddendum(self):
        return self.currentRawMethod.findNextSiblings('div', 'memdoc', limit=1)[0]

    def isDeprecated(self):
        addendum = self.findAddendum()
        if addendum.findAll(text=lambda x: any(badMsg in x for badMsg in self.DEPRECATED_MSG)):
            self.xprint("DEPRECATED")
            # print self.apiClassName + '.' + self.currentMethodName + ':' + ' DEPRECATED'
            return True
        return False

    def getMethodDoc(self):
        addendum = self.findAddendum()

        methodDoc = addendum.p
        if methodDoc:
            return ' '.join(methodDoc.findAll(text=True)).encode('ascii', 'ignore')
        return ''

    def parseMethodArgs(self, returnType, names, types, typeQualifiers):
        directions = {}
        docs = {}
        returnDoc = ''

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
                        _logger.warning("%s.%s(%s): Correcting suspected output argument '%s' based on doc '%s'" % (
                            self.apiClassName, self.currentMethodName, ', '.join(names), name, doc))
                        dir = 'out'
                    elif not self.isSetMethod() and '&' in typeQualifiers[name] and types[name] in ['int', 'double', 'float', 'uint', 'uchar']:
                        _logger.warning("%s.%s(%s): Correcting suspected output argument '%s' based on reference type '%s &' ('%s')'" % (
                            self.apiClassName, self.currentMethodName, ', '.join(names), name, types[name], doc))
                        dir = 'out'
                    else:
                        dir = 'in'
                elif dir == '[out]':
                    if types[name] == 'MAnimCurveChange':
                        _logger.warning("%s.%s(%s): Setting MAnimCurveChange argument '%s' to an input arg (instead of output)" % (
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
        return directions, docs, returnDoc

    TYPEDEF_RE = re.compile(r'^typedef(\s|$)')

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

        return methodName, ParamInfo(type=returnType,
                                     typeQualifiers=returnQualifiers)

    def _parseMethod(self, returnInfo):
        if self.currentMethodName == 'void(*':
            return

        # ENUMS
        if returnInfo.type == 'enum':
            self.xprint("ENUM", returnInfo.type)
            # print returnType, methodName
            self.parseEnum(self.currentRawMethod)
            return

        super(HtmlApiDocParser, self)._parseMethod(returnInfo)

    DOXYGEN_VER_RE = re.compile('Generated by Doxygen ([0-9.]+)')

    def getDoxygenVersion(self, soup):
        doxyComment = soup.find(text=self.DOXYGEN_VER_RE)
        match = self.DOXYGEN_VER_RE.search(builtins.str(doxyComment))
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



from __future__ import absolute_import, print_function

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import zip
from builtins import object
import os.path
import sys
import pprint

import pymel.util
import pymel.util.py2to3 as util2to3

from pymel.util import picklezip, universalmethod
from collections import namedtuple

from future.utils import PY2

from . import plogging

_logger = plogging.getLogger(__name__)

try:
    import pickle as pickle
except:
    _logger.warning("using pickle instead of cPickle: load performance will be affected")
    import pickle

TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Tuple, Type


def _moduleJoin(*args):
    # type: (*str) -> str
    """
    Joins with the base pymel directory.
    :rtype: string
    """
    moduleDir = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))
    return os.path.realpath(os.path.join(moduleDir, *args))


def _pickledump(data, filename, protocol=-1):
    with open(filename, mode='wb') as file:
        pickle.dump(data, file, protocol)


def _pickleload(filename):
    with open(filename, mode='rb') as file:
        res = pickle.load(file)
    return res

# NOTE: currently, there is no support for pymel to read or write formats
# other than the current.  This is here for documentation, and in case we want
# to add that ability at some point in the future.

# (1, 0) - initial version, that used "eval" instead of exec - didn't contain
#          explicit version
# (1, 1) - version that uses "exec" - ie, data = [...]; has a version as well
# (1, 2) - like (1, 2), but has potential unicode characters in utf-8 encoding,
#          and builtin types are now encoded as '<type bool>' instead of
#          '<type __builtin__.bool>'
PY_CACHE_FORMAT_VERSION = (1, 2)


# In python3, the PrettyPrinter will wrap long strings to match the width.
# The string wrapping in some cases looks better, but in many cases it
# results in strings with only a few characters per line, ie:
#                                                               foo: "This "
#                                                                    "is "
#                                                                    "bad."
# So, we use a custom PrettyPrinter to override string wrapping (giving results
# like we used to get in python2)

# Thanks to Martijn Pieters:
#   https://stackoverflow.com/a/31485450/920545

class NoStringWrappingPrettyPrinter(pprint.PrettyPrinter):
    def _format(self, object, *args):
        if isinstance(object, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super()._format(object, *args)
            finally:
                self._width = width
        else:
            super()._format(object, *args)

py_pformat = NoStringWrappingPrettyPrinter().pformat

if PY2:
    # just use the normal PrettyPrinter
    py_pformat = pprint.pformat


def _pyformatdump(data):
    strdata = 'version = {!r}\n\ndata = {}'.format(PY_CACHE_FORMAT_VERSION,
                                                   py_pformat(data))
    if PY2:
        if not isinstance(strdata, unicode):
            return strdata
    return strdata.encode('utf-8')


def _pycodeload(code):
    globs = {}
    exec(code, globs)
    # we ignore globs['version'] for now... there for potential future changes
    return globs['data']


def _pydump(data, filename):
    with open(filename, mode='wb') as file:
        file.write(_pyformatdump(data))


def _pyload(filename):
    with open(filename, mode='rb') as file:
        text = file.read()
    return _pycodeload(compile(text, filename, "exec"))


def _getpycbytes(source):
    import py_compile
    import tempfile

    # tried using NamedTemporaryFile, but got perm errors from
    # py_compile.compile
    pyfd, pyPath = tempfile.mkstemp(suffix='.py', prefix="py_cache_temp")
    try:
        with os.fdopen(pyfd, "wb") as pyf:
            pyf.write(source)
        pycfd, pycPath = tempfile.mkstemp(suffix='.pyc',
                                          prefix="pyc_cache_temp")
        os.close(pycfd)
        try:
            py_compile.compile(pyPath, pycPath, doraise=True)
            with open(pycPath, 'rb') as pycf:
                return pycf.read()
        finally:
            os.remove(pycPath)
    finally:
        os.remove(pyPath)


def _pyczipdump(data, filename, pyc=True):
    import zipfile
    inZipPath = os.path.basename(filename)
    if inZipPath.lower().endswith('.zip'):
        inZipPath = inZipPath[:-len('.zip')]

    bytes = _pyformatdump(data)
    if pyc:
        bytes = _getpycbytes(bytes)
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inZipPath, bytes)


def _pyzipdump(data, filename):
    return _pyczipdump(data, filename, pyc=False)


def _pyzipload(filename):
    import zipimport
    importer = zipimport.zipimporter(filename)
    moduleName = os.path.basename(filename).split('.')[0]
    return _pycodeload(importer.get_code(moduleName))


CacheFormat = namedtuple('CacheFormat', ['ext', 'reader', 'writer'])


class PymelCache(object):
    """
    Base class for a cache file to be loaded by the pymel cache system
    """

    # override these
    NAME = ''   # ie, 'mayaApi'
    DESC = ''   # ie, 'the API cache' - used in error messages, etc

    FORMATS = [
        CacheFormat('.py', _pyload, _pydump),
        CacheFormat('.pyc.zip', _pyzipload, _pyczipdump),
        CacheFormat('.py.zip', _pyzipload, _pyzipdump),
        CacheFormat('.bin', _pickleload, _pickledump),
        CacheFormat('.zip', picklezip.load, picklezip.dump),
    ]
    EXTENSIONS = {x.ext: x for x in FORMATS}
    DEFAULT_EXT = '.py'

    # whether to add the version to the filename when writing out the cache
    USE_VERSION = True

    _lastReadPath = None
    _lastWritePath = None

    def fromRawData(self, rawData):
        '''If a subclass needs to modify data as it is read from the cache
        on disk, do it here'''
        return rawData

    def toRawData(self, data):
        '''If a subclass needs to modify data before it is written to the cache
        on disk, do it here'''
        if PY2:
            # the written out .py cache will not include 'u' prefixes, which
            # makes it easier to diff to python-3-built caches; initially, just
            # using this is caches where we think it's unlikely to affect client
            # code
            isUnicode = lambda x: isinstance(x, unicode)
            data = pymel.util.deepPatch(data, isUnicode, util2to3.trystr)
        return data

    def read(self, path=None, ext=None, ignoreError=False):
        if path is not None and ext is None:
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = None
        if ext is None:
            formats = self.FORMATS
        else:
            formats = [self.EXTENSIONS[ext]]

        for format in formats:
            # if the user provided an explicit ext (or path with ext), we want
            # to use that EXACTLY (ie, might differ in case) - otherwise, we
            # use the standard ext from format.ext
            if path is not None:
                formatPath = path
            else:
                formatPath = self.path(ext=format.ext)

            if not os.path.isfile(formatPath):
                _logger.debug(self._actionMessage(
                    'Unable to open', 'from nonexistant path', formatPath))
                continue

            func = format.reader
            _logger.debug(self._actionMessage('Loading', 'from', formatPath))
            try:
                finalData = self.fromRawData(func(formatPath))
            except Exception as e:
                self._errorMsg('read', 'from', formatPath, e)
                if not ignoreError:
                    raise
            else:
                self._lastReadPath = formatPath
                return finalData

    def write(self, data, path=None, ext=None, ignoreError=False):
        # type: (T, Optional[str], Optional[str], bool) -> None
        import copy
        # when writing data, we dont' actually want to modify the passed in
        # data, as it may be in use... so we make a deepcopy
        data = copy.deepcopy(data)

        if path is not None and ext is None:
            ext = os.path.splitext(path)[1]
        if not ext:
            ext = self.DEFAULT_EXT
        if not path:
            path = self.path(ext=ext)
        format = self.EXTENSIONS[ext]
        func = format.writer
        _logger.info(self._actionMessage('Saving', 'to', path))

        try:
            func(self.toRawData(data), path)
        except Exception as e:
            self._errorMsg('write', 'to', path, e)
            if not ignoreError:
                raise
        else:
            self._lastWritePath = path

    @universalmethod
    def path(self, version=None, ext=None):
        # type: (Optional[str], Optional[str]) -> str
        if ext is None:
            ext = self.DEFAULT_EXT
        if self.USE_VERSION:
            if version is not None:
                short_version = str(version)
            elif hasattr(self, 'version'):
                short_version = str(self.version)
            else:
                import pymel.versions
                short_version = pymel.versions.shortName()
        else:
            short_version = ''

        newPath = _moduleJoin('cache', self.NAME + short_version)
        return newPath + ext

    @classmethod
    def allVersions(cls, allowEmpty=False):
        # type: (bool) -> List[str]
        import itertools
        import re

        # unlikely they'll have a path with PLACEHOLDER, but better safe than
        # sorry...
        placeholderBase = 'PLACEHOLDER'
        i = 0
        for i in itertools.count():
            placeholder = placeholderBase + str(i)
            fullPath = cls.path(placeholder)
            if fullPath.count(placeholder) == 1:
                break
        dirname, filePattern = os.path.split(fullPath)
        filePattern = re.escape(filePattern)
        filePattern = filePattern.replace(placeholder, '(.*)')
        filePatternRe = re.compile('^' + filePattern + '$')
        versions = []
        for filename in os.listdir(dirname):
            if not os.path.isfile(os.path.join(dirname, filename)):
                continue
            match = filePatternRe.match(filename)
            if match:
                version = match.group(1)
                if allowEmpty or version != '':
                    versions.append(version)
        return sorted(versions)

    @classmethod
    def _actionMessage(cls, action, direction, location):
        '''_actionMessage('eat', 'at', 'Joes') =>
            "eat cls.DESC at 'Joes'"
        '''
        description = cls.DESC
        if description:
            description = ' ' + description
        return "%s%s %s %r" % (action, description, direction, location)

    @classmethod
    def _errorMsg(cls, action, direction, path, error):
        '''_errorMessage('eat', 'at', 'Joes') =>
            'Unable to eat cls.DESC at Joes: error.msg'
        '''
        actionMsg = cls._actionMessage(action, direction, path)
        _logger.raiseLog(_logger.WARNING,
                         "Unable to %s: %s" % (actionMsg, error))
        import traceback
        _logger.debug(traceback.format_exc())


# Considered using named_tuple, but wanted to make data stored in cache
# have as few dependencies as possible - ie, just a simple tuple
class SubItemCache(PymelCache):

    '''Used to store various maya information

    ie, api / cmd data parsed from docs

    To implement, create a subclass, which overrides at least the NAME, DESC,
    and _CACHE_NAMES attributes, and implements the rebuild method.

    Then to access data, you should initialize an instance, then call build;
    build will load the data from the cache file if possible, or call rebuild
    to build the data from scratch if not.  If the data had to be rebuilt,
    a new file cache will be saved.

    The data may then be accessed through attributes on the instance, with
    the names given in _CACHE_NAMES.

    >>> class NodeCache(SubItemCache):
    ...     NAME = 'mayaNodes'
    ...     DESC = 'the maya nodes cache'
    ...     _CACHE_NAMES = ['nodeTypes']
    ...     AUTO_SAVE = False
    ...     def rebuild(self):
    ...         import maya.cmds
    ...         self.nodeTypes = maya.cmds.allNodeTypes(includeAbstract=True)
    >>> cacheInst = NodeCache()
    >>> cacheInst.build()
    >>> 'polyCube' in cacheInst.nodeTypes
    True
    '''
    # Provides a front end for a pickled file, which should contain a
    # tuple of items; each item in the tuple is associated with a name from
    # _CACHE_NAMES

    # override this with a list of names for the items within the cache
    _CACHE_NAMES = []

    # Set this to the initialization contructor for each cache item;
    # if a given cache name is not present in ITEM_TYPES, DEFAULT_TYPE is
    # used
    # These are the types that the contents will 'appear' to be to the end user
    # (ie, the types returned by contents).
    # Should be constructors which can either take no arguments, or
    # a single argument to initialize an instance.
    ITEM_TYPES = {}  # type: Dict[str, Type]
    DEFAULT_TYPE = dict  # type: Type
    AUTO_SAVE = True

    def __init__(self):
        for name in self._CACHE_NAMES:
            self.initVal(name)

    @classmethod
    def cacheNames(cls):
        # type: () -> Tuple[str, ...]
        return tuple(cls._CACHE_NAMES)

    @classmethod
    def itemType(cls, name):
        # type: (str) -> Type
        return cls.ITEM_TYPES.get(name, cls.DEFAULT_TYPE)

    @classmethod
    def itemIndex(cls, name):
        # type: (str) -> int
        return cls._CACHE_NAMES.index(name)

    def initVal(self, name):
        # type: (str) -> None
        itemType = self.itemType(name)
        if itemType is None:
            val = None
        else:
            val = itemType()
        setattr(self, name, val)

    def build(self):
        # type: () -> None
        """
        Used to rebuild cache, either by loading from a cache file, or
        rebuilding from scratch.
        """
        data = self.load()
        if data is None:
            self.rebuild()
            if self.AUTO_SAVE:
                self.save()

    # override this...
    def rebuild(self):
        # type: () -> None
        """Rebuild cache from scratch

        Unlike 'build', this does not attempt to load a cache file, but always
        rebuilds it by parsing the docs, etc.
        """
        pass

    def update(self, obj, cacheNames=None):
        '''Update all the various data from the given object, which should
        either be a dictionary, a list or tuple with the right number of items,
        or an object with the caches stored in attributes on it.
        '''
        if cacheNames is None:
            cacheNames = self.cacheNames()

        if isinstance(obj, dict):
            for key, val in obj.items():
                setattr(self, key, val)
        elif isinstance(obj, (list, tuple)):
            if len(obj) != len(cacheNames):
                raise ValueError('length of update object (%d) did not match '
                                 'length of cache names (%d)' %
                                 (len(obj), len(cacheNames)))
            for newVal, name in zip(obj, cacheNames):
                setattr(self, name, newVal)
        else:
            for cacheName in cacheNames:
                setattr(self, cacheName, getattr(obj, cacheName))

    def load(self):
        # type: () -> T
        '''Attempts to load the data from the cache on file.

        If it succeeds, it will update itself, and return the loaded items;
        if it fails, it will return None
        '''
        data = self.read(ignoreError=True)
        if data is not None:
            data = tuple(data)
            self.update(data, cacheNames=self._CACHE_NAMES)
        return data

    def save(self, obj=None, ext=None):
        '''Saves the cache

        Will optionally update the caches from the given object (which may be
        a dictionary, or an object with the caches stored in attributes on it)
        before saving
        '''
        if obj is not None:
            self.update(obj)
        data = self.contents()
        self.write(data, ext=ext)

    # was called 'caches'
    def contents(self):
        # type: () -> T
        return tuple(getattr(self, x) for x in self.cacheNames())

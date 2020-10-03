
"""
Functions and classes relating to files, references, and system calls.

In particular, the system module contains the functionality of maya.cmds.file. The file command should not be imported into
the default namespace because it conflicts with python's builtin file class. Since the file command has so many flags,
we decided to kill two birds with one stone: by breaking the file command down into multiple functions -- one for each
primary flag -- the resulting functions are more readable and allow the file command's functionality to be used directly
within the pymel namespace.

for example, instead of this:

    >>> res = cmds.file( 'test.ma', exportAll=1, preserveReferences=1, type='mayaAscii', force=1 ) # doctest: +SKIP

you can do this:

    >>> expFile = exportAll( 'test.ma', preserveReferences=1, force=1)

some of the new commands were changed slightly from their flag name to avoid name clashes and to add to readability:

    >>> importFile( expFile )  # flag was called import, but that's a python keyword
    >>> ref = createReference( expFile )
    >>> ref # doctest: +ELLIPSIS
    FileReference('...test.ma', refnode='testRN')

Notice that the 'type' flag is set automatically for you when your path includes a '.mb' or '.ma' extension.

Paths returned by these commands are either a `Path` or a `FileReference`, so you can use object-oriented path methods with
the results::

    >>> expFile.exists()
    True
    >>> expFile.remove() # doctest: +ELLIPSIS
    Path('...test.ma')

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from past.builtins import cmp
from builtins import zip
from builtins import range
from builtins import str
from past.builtins import basestring
from builtins import object
import sys
import os
import warnings
import abc

import maya.mel as _mel
import maya.OpenMaya as _OpenMaya

from pymel.util.scanf import fscanf
from pymel.util.decoration import decorator
import pymel.util as _util
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as versions
from future.utils import PY2, with_metaclass

if PY2:
    # formerly made a dummy namespace, collections.abc, and added
    # collections.abc.MutableMapping; unfortunately, other python packages (ie,
    # jinja) tried to do "from collections import abc", and ended up using
    # our (useless) dummy module. So just doing an if/else, which shouldn't
    # have other side effects...
    from collections import MutableMapping
else:
    from collections.abc import MutableMapping

if False:
    from typing import *
    from maya import cmds
    import pymel.core.nodetypes as nt
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]

_logger = _internal.getLogger(__name__)


try:
    from pymel.internal.startup import pymel_options as _pymel_options
    # attempt to import a custom path class to use as the base for pymel's Path class
    basePathName = _pymel_options['path_class']
    buf = basePathName.split('.')
    moduleName = '.'.join(buf[:-1])
    className = buf[-1]
    try:
        pathModule = __import__(moduleName, globals(), locals(), [''])
    except Exception as e:
        _logger.warning("Could not import %r module containing custom base Path class: %s" % (moduleName, e))
        raise AssertionError

    try:
        pathClass = getattr(pathModule, className)
        _logger.info("Using custom path class %s" % (basePathName))
    except AttributeError as e:
        _logger.warning("Custom path class %s could not be found in module %s" % (className, pathModule))
        raise AssertionError
except (KeyError, AssertionError):
    pathClass = _util.path


def _getTypeFromExtension(path, mode='write'):
    # type: (str, str) -> str
    """
    Parameters
    ----------
    path : str
        path from with to pull the extension from - note that it may NOT be
        ONLY the extension - ie, "obj" and ".obj", will not work, but
        "foo.obj" will
    mode : str
        {'write', 'read'}
        the type is basically a string name of a file translator, which can
        have different ones registered for reading or writing; this specifies
        whether you're looking for the read or write translator

    Returns
    -------
    str
    """
    ext = Path(path).ext
    return str(Translator.fromExtension(ext, mode=mode))


def _setTypeKwargFromExtension(path, kwargs, mode='write'):
    if 'type' not in kwargs and 'typ' not in kwargs:
        try:
            fileType = _getTypeFromExtension(path, mode=mode)
        except Exception:
            pass
        else:
            if fileType and fileType != 'None':
                kwargs['type'] = fileType

# Bring the MGlobal.display* methods into this namespace, for convenience
displayError = _OpenMaya.MGlobal.displayError
displayWarning = _OpenMaya.MGlobal.displayWarning
displayInfo = _OpenMaya.MGlobal.displayInfo


def feof(fileid):
    """Reproduces the behavior of the mel command of the same name. if writing pymel scripts from scratch,
    you should use a more pythonic construct for looping through files:

    >>> f = open('myfile.txt') # doctest: +SKIP
    ... for line in f:
    ...     print(line)

    This command is provided for python scripts generated by mel2py"""

    pos = fileid.tell()
    fileid.seek(0, 2)  # goto end of file
    end = fileid.tell()  # get final position
    fileid.seek(pos)
    return pos == end


@_factories.addMelDocs('file', 'sceneName')
def sceneName():
    # We don't just use cmds.file(q=1, sceneName=1)
    # because it was sometimes returning an empty string,
    # even when there was a valid file
    name = Path(_OpenMaya.MFileIO.currentFile())
    if name.basename().startswith(untitledFileName()) and \
            cmds.file(q=1, sceneName=1) == '':
        return Path()
    else:
        return name


def untitledFileName():
    """
    Obtain the base filename used for untitled scenes. In localized environments, this string will contain a translated value.
    """
    return _mel.eval('untitledFileName()')


class UndoChunk(object):

    """Context manager for encapsulating code in a single undo.

    Use in a with statement
    Wrapper for cmds.undoInfo(openChunk=1)/cmds.undoInfo(closeChunk=1)

    >>> import pymel.core as pm
    >>> pm.ls("MyNode*", type='transform')
    []
    >>> with pm.UndoChunk():
    ...     res = pm.createNode('transform', name="MyNode1")
    ...     res = pm.createNode('transform', name="MyNode2")
    ...     res = pm.createNode('transform', name="MyNode3")
    >>> pm.ls("MyNode*", type='transform')
    [nt.Transform('MyNode1'), nt.Transform('MyNode2'), nt.Transform('MyNode3')]
    >>> pm.undo() # Due to the undo chunk, all three are undone at once
    >>> pm.ls("MyNode*", type='transform')
    []
    """

    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        if self.name:
            cmds.undoInfo(openChunk=1, chunkName=self.name)
        else:
            cmds.undoInfo(openChunk=1)
        return self

    def __exit__(*args, **kwargs):
        cmds.undoInfo(closeChunk=1)


# ==============================================================================
# Namespace
# ==============================================================================
class Namespace(str):

    @classmethod
    def getCurrent(cls):
        # type: () -> Namespace
        """
        Returns
        -------
        Namespace
        """
        return cls(cmds.namespaceInfo(cur=1))

    @classmethod
    def create(cls, name):
        # type: (Any) -> Namespace
        """
        Returns
        -------
        Namespace
        """
        ns = cmds.namespace(add=name)
        return cls(ns)

    def __new__(cls, namespace, create=False):
        namespace = ":" + namespace.strip(":")
        if not cmds.namespace(exists=namespace):
            if not create:
                raise ValueError("Namespace '%s' does not exist" % namespace)
            else:
                current = Namespace.getCurrent()
                Namespace(":").setCurrent()
                for part in namespace.split(":")[1:]:
                    if not cmds.namespace(exists=part):
                        cmds.namespace(add=part)
                    cmds.namespace(set=part)
                current.setCurrent()

        self = super(Namespace, cls).__new__(cls, namespace)
        return self

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(Namespace, self).__repr__())

    def __add__(self, other):
        return "%s:%s" % (self.rstrip(':'), other.lstrip(":"))

    def __cmp__(self, other):
        return cmp(self.strip(":"), str(other).strip(":"))

    __eq__ = lambda self, other: self.__cmp__(other) == 0
    __ne__ = lambda self, other: self.__cmp__(other) != 0
    __le__ = lambda self, other: self.__cmp__(other) <= 0
    __lt__ = lambda self, other: self.__cmp__(other) < 0
    __ge__ = lambda self, other: self.__cmp__(other) >= 0
    __gt__ = lambda self, other: self.__cmp__(other) > 0

    def __hash__(self):
        return hash(str(self).strip(':'))

    def splitAll(self):
        # type: () -> List[str]
        """
        Returns
        -------
        List[str]
        """
        return self.strip(":").split(":")

    def shortName(self):
        # type: () -> str
        """
        Returns
        -------
        str
        """
        return self.splitAll()[-1]

    def getParent(self):
        # type: () -> Optional[Namespace]
        """
        Returns
        -------
        Optional[Namespace]
        """
        if (str(self) != ":"):
            return self.__class__(':'.join(self.splitAll()[:-1]))
        else:
            return None

    def ls(self, pattern="*", **kwargs):
        # type: (Any, **Any) -> List[general.PyNode]
        """
        Returns
        -------
        List[general.PyNode]
        """
        return general.ls(self + pattern, **kwargs)

    def getNode(self, nodeName, verify=True):
        # type: (Any, Any) -> general.PyNode
        """
        Returns
        -------
        general.PyNode
        """
        node = general.PyNode(self + nodeName)
        if verify and not node.exists():
            raise Exception("Node '%s' does not exist" % node)
        return node

    def listNamespaces(self, recursive=False, internal=False):
        # type: (bool, bool) -> List[Namespace]
        """List the namespaces contained within this namespace.

        Parameters
        ----------
        recursive : bool
            Set to True to enable recursive search of sub (and sub-sub, etc)
            namespaces
        internal : bool
            By default, this command filters out certain automatically created
            maya namespaces (ie, :UI, :shared); set to True to show these
            internal namespaces as well

        Returns
        -------
        List[Namespace]
        """
        curNS = Namespace.getCurrent()

        self.setCurrent()
        try:
            # workaround: namespaceInfo sometimes returns duplicates
            seen = set()
            namespaces = [self.__class__(ns)
                for ns in (cmds.namespaceInfo(listOnlyNamespaces=True) or [])
                if not (ns in seen or seen.add(ns))]

            if not internal:
                for i in [":UI", ":shared"]:
                    if i in namespaces:
                        namespaces.remove(i)

            if recursive:
                childNamespaces = []
                for ns in namespaces:
                    childNamespaces.extend(ns.listNamespaces(recursive, internal))
                namespaces.extend(childNamespaces)
        finally:
            curNS.setCurrent()

        return namespaces

    def listNodes(self, recursive=False, internal=False):
        # type: (bool, bool) -> List[general.PyNode]
        """List the nodes contained within this namespace.

        Parameters
        ----------
        recursive : bool
            Set to True to enable recursive search of sub (and sub-sub, etc)
            namespaces
        internal : bool
            By default, this command filters out nodes in certain automatically
            created maya namespaces (ie, :UI, :shared); set to True to show
            these internal namespaces as well

        Returns
        -------
        List[general.PyNode]
        """
        curNS = Namespace.getCurrent()

        self.setCurrent()
        try:
            if not internal:
                # Default for recursive is false
                nodes = namespaceInfo(listOnlyDependencyNodes=True, dagPath=True)
                if recursive:
                    namespaces = self.listNamespaces(recursive=False, internal=internal)

                    for ns in namespaces:
                        nodes.extend(ns.listNodes(recursive=recursive,
                                                  internal=internal))
            else:
                nodes = namespaceInfo(listOnlyDependencyNodes=True, dagPath=True,
                                      recurse=recursive)
        finally:
            curNS.setCurrent()

        return nodes

    def setCurrent(self):
        cmds.namespace(set=self)

    def clean(self, haltOnError=True, reparentOtherChildren=True):
        # type: (bool, bool) -> None
        """Deletes all nodes in this namespace

        Parameters
        ----------
        haltOnError : bool
            If true, and reparentOtherChildren is set, and there is an error in
            reparenting, then raise an Exception (no rollback is performed);
            otherwise, ignore the failed reparent, and continue
        reparentOtherChildren : bool
            If True, then if any transforms in this namespace have children NOT
            in this namespace, then will attempt to reparent these children
            under world (errors during these reparenting attempts is controlled
            by haltOnError)
        """
        cur = Namespace.getCurrent()
        self.setCurrent()
        toDelete = cmds.namespaceInfo(ls=1, dp=1) or []
        cur.setCurrent()

        if toDelete:
            if reparentOtherChildren:
                for o in general.ls(toDelete, transforms=True):
                    # Note that we only need to check IMMEDIATE children...
                    # because we're iterating through ALL transforms in this
                    # namespace
                    for c in o.getChildren(fullPath=True, type='transform'):
                        if self != c.namespace():
                            _logger.warning("Preserving %r, which was parented under %r" % (c, o))
                            try:
                                c.setParent(world=True)
                            except Exception as e:
                                if haltOnError:
                                    raise
                                _logger.error("Could not preserve %r (%s)" % (c, e))

                toDelete = general.ls(toDelete)
            if toDelete:
                _logger.debug("Deleting %d nodes from namespace '%s'" % (len(toDelete), self))
                for n in toDelete:
                    _logger.log(5, "\t%s" % n)
                    n.unlock()
                general.delete(toDelete)

    def move(self, other, force=False):
        cmds.namespace(moveNamespace=(self, other), force=force)

    # TODO:
    # - add in "proper" handling for new 2013 flags:
    #    deleteNamespaceContent (if False, error if non-empty)
    #    mergeNamespaceWithRoot
    #    mergeNamespaceWithParent
    # - need to investigate exact way in which 2013 flags work (with sub-
    #   namespaces, with children in other namespaces, etc), and possibly
    #   add in support for flags to control recursive behavior, and handling of
    #   children of transforms that are NOT in this namespace
    def remove(self, haltOnError=True, reparentOtherChildren=True):
        # type: (bool, bool) -> None
        """Removes this namespace

        Recursively deletes any nodes and sub-namespaces

        Parameters
        ----------
        haltOnError : bool
            If true, and reparentOtherChildren is set, and there is an error in
            reparenting, then raise an Exception (no rollback is performed);
            otherwise, ignore the failed reparent, and continue
        reparentOtherChildren : bool
            If True, then if any transforms in this namespace have children NOT
            in this namespace, then will attempt to reparent these children
            under world (errors during these reparenting attempts is controlled
            by haltOnError)
        """
        self.clean(haltOnError=haltOnError,
                   reparentOtherChildren=reparentOtherChildren)
        for subns in self.listNamespaces():
            subns.remove(haltOnError=haltOnError,
                         reparentOtherChildren=reparentOtherChildren)
        cmds.namespace(removeNamespace=self)


def listNamespaces_old():
    """
    Deprecated
    Returns a list of the namespaces of referenced files.
    REMOVE In Favor of listReferences('dict') ?"""
    try:
        return [cmds.file(x, q=1, namespace=1) for x in cmds.file(q=1, reference=1)]
    except:
        return []


def listNamespaces(root=None, recursive=False, internal=False):
    # type: (Any, Any, Any) -> List[Namespace]
    """Returns a list of the namespaces in the scene

    Returns
    -------
    List[Namespace]
    """
    return Namespace(root or ":").listNamespaces(recursive, internal)


def namespaceInfo(*args, **kwargs):
    """
    Modifications:
        - returns an empty list when the result is None
        - returns wrapped classes for listOnlyDependencyNodes
    """
    pyNodeWrap = kwargs.get('lod', kwargs.get('listOnlyDependencyNodes', False))
    if pyNodeWrap:
        kwargs.pop('dp', False)
        kwargs['dagPath'] = True

    res = cmds.namespaceInfo(*args, **kwargs)

    if any(kwargs.get(x, False) for x in ('ls', 'listNamespace',
                                          'lod', 'listOnlyDependencyNodes',
                                          'lon', 'listOnlyNamespaces')):
        res = _util.listForNone(res)

    if pyNodeWrap:
        import pymel.core.general
        nodes = []
        for x in res:
            try:
                nodes.append(general.PyNode(x))
            except general.MayaNodeError:
                # some ui objects/tools - like '|CubeCompass' -
                # get returned... so just ignore any nodes we can't create
                pass
        res = nodes

    return res


# ----------------------------------------------
#  Translator Class
# ----------------------------------------------

class Translator(object):

    """
    Provides information about a Maya translator, which is used for reading
    and/or writing file formats.

    >>> ascii = Translator('mayaAscii')
    >>> ascii.ext
    'ma'
    >>> bin = Translator.fromExtension( 'mb' )
    >>> bin
    Translator('mayaBinary')
    >>> bin.name
    'mayaBinary'
    >>> bin.hasReadSupport()
    True
    """

    @staticmethod
    def listRegistered():
        return cmds.translator(q=1, list=1)

    @staticmethod
    def fromExtension(ext, mode=None, caseSensitive=False):
        # type: (str, str, bool) -> Optional[Translator]
        """
        Parameters
        ----------
        ext : str
        mode : str
            {'read', 'write'}
        caseSensitive : bool

        Returns
        -------
        Optional[Translator]
        """
        if mode is not None and mode not in ('read', 'write'):
            raise ValueError('mode must be either "read" or "write"')

        if ext.startswith('.'):
            ext = ext[1:]

        caseInsensitiveMatch = None
        for k in Translator.listRegistered():
            t = Translator(k)
            if mode == 'read':
                if not t.hasReadSupport():
                    continue
            elif mode == 'write':
                if not t.hasWriteSupport():
                    continue
            tExt = t.ext
            if ext == tExt:
                return t
            elif (not caseSensitive and caseInsensitiveMatch is None and
                    tExt.lower() == ext.lower()):
                # we always PREFER a match that is case-exact, even if
                # caseSensitive is False, so try all translators before
                # returning the caseInsensitiveMatch
                caseInsensitiveMatch = t
        if caseInsensitiveMatch is not None:
            return caseInsensitiveMatch
        else:
            return None

    def __init__(self, name):
        assert name in cmds.translator(q=1, list=1), "%s is not the name of a registered translator" % name
        self._name = str(name)

    def __str__(self):
        return self._name

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._name)

    def extension(self):
        return cmds.translator(self._name, q=1, ext=1)
    ext = property(extension)
    name = property(__str__)

    def filter(self):
        return cmds.translator(self._name, q=1, filter=1)

    def optionsScript(self):
        return cmds.translator(self._name, q=1, optionsScript=1)

    def hasReadSupport(self):
        return bool(cmds.translator(self._name, q=1, readSupport=1))

    def hasWriteSupport(self):
        return (cmds.translator(self._name, q=1, writeSupport=1))

    def getDefaultOptions(self):
        return cmds.translator(self._name, q=1, defaultOptions=1)

    def setDefaultOptions(self, options):
        cmds.translator(self._name, e=1, defaultOptions=options)

    def getFileCompression(self):
        return cmds.translator(self._name, q=1, fileCompression=1)

    def setFileCompression(self, compression):
        cmds.translator(self._name, e=1, fileCompression=compression)


# ----------------------------------------------
#  Workspace Class
# ----------------------------------------------

class WorkspaceEntryDict(object):

    def __init__(self, entryType):
        self.entryType = entryType

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.entryType)

    def __getitem__(self, item):
        res = cmds.workspace(**{self.entryType + 'Entry': item})
        if not res:
            raise KeyError(item)
        return res

    def __setitem__(self, item, value):
        return cmds.workspace(**{self.entryType: [item, value]})

    def __contains__(self, key):
        return key in self.keys()

    def items(self):
        entries = _util.listForNone(cmds.workspace(**{'q': 1, self.entryType: 1}))
        res = []
        for i in range(0, len(entries), 2):
            res.append((entries[i], entries[i + 1]))
        return res

    def keys(self):
        return cmds.workspace(**{'q': 1, self.entryType + 'List': 1})

    def values(self):
        entries = _util.listForNone(cmds.workspace(**{'q': 1, self.entryType: 1}))
        res = []
        for i in range(0, len(entries), 2):
            res.append(entries[i + 1])
        return res

    def get(self, item, default=None):
        try:
            return self.__getitem__(item)
        except KeyError:
            return default

    def __iter__(self):
        return iter(self.keys())
    has_key = __contains__


class Workspace(with_metaclass(_util.Singleton, object)):

    """
    This class is designed to lend more readability to the often confusing workspace command.
    The four types of workspace entries (objectType, fileRule, renderType, and variable) each
    have a corresponding dictiony for setting and accessing these mappings.

        >>> from pymel.all import *
        >>> workspace.fileRules['mayaAscii']
        'scenes'
        >>> workspace.fileRules.keys() # doctest: +ELLIPSIS
        [...'mayaAscii', 'mayaBinary',...]
        >>> 'mayaBinary' in workspace.fileRules
        True
        >>> workspace.fileRules['super'] = 'data'
        >>> workspace.fileRules.get( 'foo', 'some_default' )
        'some_default'

    the workspace dir can be confusing because it works by maintaining a current working directory that is persistent
    between calls to the command.  In other words, it works much like the unix 'cd' command, or python's 'os.chdir'.
    In order to clarify this distinction, the names of these flags have been changed in their class method counterparts
    to resemble similar commands from the os module.

    old way (still exists for backward compatibility)
        >>> proj = workspace(query=1, dir=1)
        >>> proj  # doctest: +ELLIPSIS
        '...'
        >>> workspace(create='mydir')
        >>> workspace(dir='mydir') # move into new dir
        >>> workspace(dir=proj) # change back to original dir

    new way
        >>> proj = workspace.getcwd()
        >>> proj  # doctest: +ELLIPSIS
        Path('...')
        >>> workspace.mkdir('mydir')
        >>> workspace.chdir('mydir')
        >>> workspace.chdir(proj)

    All paths are returned as an pymel.core.system.Path class, which makes it easy to alter or join them on the fly.
        >>> workspace.path / workspace.fileRules['mayaAscii']  # doctest: +ELLIPSIS
        Path('...')

    """

    objectTypes = WorkspaceEntryDict('objectType')
    fileRules = WorkspaceEntryDict('fileRule')
    renderTypes = WorkspaceEntryDict('renderType')
    variables = WorkspaceEntryDict('variable')

#    def __init__(self):
#        self.objectTypes = WorkspaceEntryDict( 'objectType' )
#        self.fileRules     = WorkspaceEntryDict( 'fileRule' )
#        self.renderTypes = WorkspaceEntryDict( 'renderType' )
#        self.variables     = WorkspaceEntryDict( 'variable' )

    @classmethod
    def open(self, workspace):
        return cmds.workspace(workspace, openWorkspace=1)

    @classmethod
    def save(self):
        return cmds.workspace(saveWorkspace=1)

    @classmethod
    def update(self):
        return cmds.workspace(update=1)

    @classmethod
    def new(self, workspace):
        return cmds.workspace(workspace, newWorkspace=1)

    @classmethod
    def getName(self):
        return cmds.workspace(q=1, act=1)

    @classmethod
    def getPath(self):
        return Path(cmds.workspace(q=1, fullName=1))

    @classmethod
    def chdir(self, newdir):
        return cmds.workspace(dir=newdir)

    @classmethod
    def getcwd(self):
        return Path(cmds.workspace(q=1, dir=1))

    @classmethod
    def mkdir(self, newdir):
        return cmds.workspace(cr=newdir)

    @property
    def path(self):
        return Path(cmds.workspace(q=1, fullName=1))

    @property
    def name(self):
        return cmds.workspace(q=1, act=1)

    def __call__(self, *args, **kwargs):
        """provides backward compatibility with cmds.workspace by allowing an instance
        of this class to be called as if it were a function"""
        return cmds.workspace(*args, **kwargs)

    def expandName(self, path):
        return cmds.workspace(expandName=path)


workspace = Workspace()


# ----------------------------------------------
#  FileInfo Class
# ----------------------------------------------

class SingletonABCMeta(_util.Singleton, abc.ABCMeta):
    """
    Simple subclass of the abstract base metaclass, and the Pymel Singleton.
    Needed to deal with the fact that Python doesn't let you have multiple metaclasses.
    """
    pass

class FileInfo(with_metaclass(SingletonABCMeta, MutableMapping)):

    """
    store and get custom data specific to this file:

        >>> from pymel.all import *
        >>> fileInfo['lastUser'] = env.user()

    if the python structures have valid __repr__ functions, you can
    store them and reuse them later:

        >>> fileInfo['cameras'] = str( ls( cameras=1) )
        >>> camList = eval(fileInfo['cameras'])
        >>> camList[0]
        nt.Camera('frontShape')

    for backward compatibility it retains it's original syntax as well:

        >>> fileInfo( 'myKey', 'myData' )

    Updated to have a fully functional dictiony interface.


    """

    def __getitem__(self, item):
        # type: (str) -> str
        result = cmds.fileInfo(item, q=1)
        if not result:
            raise KeyError(item)
        elif len(result) > 1:
            raise RuntimeError("error getting fileInfo for key %r - "
                               "more than one value returned" % item)
        else:
            value = result[0]
            if PY2:
                if isinstance(value, bytes):
                    return value.decode('string_escape')
                else:
                    # unicode
                    return value.decode('unicode_escape')
            else:
                return value

    def __setitem__(self, item, value):
        cmds.fileInfo(item, value)

    def __delitem__(self, item):
        cmds.fileInfo(remove=item)

    def __call__(self, *args, **kwargs):
        if kwargs.get('query', kwargs.get('q', False)):
            if not args:
                return list(self.items())
            else:
                return self[args[0]]
        else:
            cmds.fileInfo(*args, **kwargs)

    def items(self):
        return list(zip(self.keys(), self.values()))

    def keys(self):
        return cmds.fileInfo(q=True)[::2]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    has_key = MutableMapping.__contains__

fileInfo = FileInfo()


# ----------------------------------------------
#  File Classes
# ----------------------------------------------

class Path(pathClass):

    """A basic Maya file class. it gets most of its power from the path class written by Jason Orendorff.
    see path.py for more documentation."""

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self)

    getTypeName = _factories.makeQueryFlagMethod(cmds.file, 'type')
    setSubType = _factories.makeQueryFlagMethod(cmds.file, 'subType', 'setSubType')
#
# class CurrentFile(Path):
#    getRenameToSave = classmethod( _factories.makeQueryFlagMethod( cmds.file, 'renameToSave', 'getRenameToSave'))
#    setRenameToSave = classmethod( _factories.make_factories.createflagMethod( cmds.file, 'renameToSave', 'setRenameToSave'))
#    anyModified = classmethod( _factories.makeQueryFlagMethod( cmds.file, 'anyModified'))
#    @classmethod
#    @_factories.addMelDocs( 'file', 'lockFile')
#    def lock(self):
#        return cmds.file( lockFile=True)
#
#    @classmethod
#    @_factories.addMelDocs( 'file', 'lockFile')
#    def unlock(self):
#        return cmds.file( lockFile=False)
#    isModified = classmethod( _factories.makeQueryFlagMethod( cmds.file, 'modified', 'isModified'))
#    setModified = classmethod( _factories.make_factories.createflagMethod( cmds.file, 'modified', 'setModified'))
#
#    isWritableInScene = _factories.makeQueryFlagMethod( cmds.file, 'writable' )
#    @classmethod
#    @_factories.addMelDocs( 'file', 'sceneName')
#    def name(self):
#        return Path( _OpenMaya.MFileIO.currentFile() )


# ==============================================================================
# FileReference
# ==============================================================================

def iterReferences(parentReference=None, recursive=False, namespaces=False,
                   refNodes=False, references=True, recurseType='depth',
                   loaded=None, unloaded=None):
    # type: (Union[str, Path, FileReference], bool, bool, bool, bool, str, Optional[bool], Optional[bool]) -> Iterator[Union[FileReference, Tuple[unicode, FileReference], Tuple[unicode, FileReference, nt.Reference]]]
    """
    returns references in the scene as a list of value tuples.

    The values in the tuples can be namespaces, refNodes (as PyNodes), and/or
    references (as FileReferences), and are controlled by their respective
    keywords (and are returned in that order).  If only one of the three options
    is True, the result will not be a list of value tuples, but will simply be a
    list of values.

    Parameters
    ----------
    parentReference : Union[str, Path, FileReference]
        a reference to get sub-references from. If None (default), the current
        scene is used.
    recursive : bool
        recursively determine all references and sub-references
    namespaces : bool
        controls whether namespaces are returned
    refNodes : bool
        controls whether reference PyNodes are returned
    references : bool
        controls whether FileReferences returned
    recurseType : str
        if recursing, whether to do a 'breadth' or 'depth' first search;
        defaults to a 'depth' first
    loaded : Optional[bool]
        whether to return loaded references in the return result; if both of
        loaded/unloaded are not given (or None), then both are assumed True;
        if only one is given, the other is assumed to have the opposite boolean
        value
    unloaded : Optional[bool]
        whether to return unloaded references in the return result; if both of
        loaded/unloaded are not given (or None), then both are assumed True;
        if only one is given, the other is assumed to have the opposite boolean
        value

    Returns
    -------
    Iterator[Union[FileReference, Tuple[unicode, FileReference], Tuple[unicode, FileReference, nt.Reference]]]
    """
    import pymel.core.general

    validRecurseTypes = ('breadth', 'width')
    if recurseType not in validRecurseTypes:
        ValueError('%s was not an acceptable value for recurseType - must '
                   'be one of %s' % (recurseType, ', '.join(validRecurseTypes)))

    if parentReference is None:
        refs = cmds.file(q=1, reference=1)
    else:
        refs = cmds.file(parentReference, q=1, reference=1)

    if loaded is None and unloaded is None:
        loaded = True
        unloaded = True
    elif loaded is None:
        loaded = not unloaded
    elif unloaded is None:
        unloaded = not loaded

    if not (loaded or unloaded):
        return

    # print "reference", parentReference
    while refs:
        # if recursive and recurseType == 'breadth':
        ref = refs.pop(0)
        row = []

        refNode = cmds.referenceQuery(ref, referenceNode=1)
        refNode = general.PyNode(refNode)

        wasLoaded = cmds.referenceQuery(refNode, isLoaded=1)

        # If we are only looking for loaded, and this isn't, we can bail
        # immediately... any child references will also be unloaded
        if not unloaded and not wasLoaded:
            continue

        refObj = None
        if namespaces:
            refObj = FileReference(refNode)
            row.append(refObj.fullNamespace)
        if refNodes:
            row.append(refNode)
        if references:
            if refObj is None:
                refObj = FileReference(refNode)
            row.append(refObj)
        if len(row) == 1:
            row = row[0]
        else:
            row = tuple(row)

        if ((loaded and wasLoaded) or (unloaded and not wasLoaded)):
            yield row
        if recursive and wasLoaded:
            if recurseType == 'depth':
                for x in iterReferences(parentReference=ref,
                                        recursive=True,
                                        namespaces=namespaces,
                                        refNodes=refNodes,
                                        references=references,
                                        loaded=loaded,
                                        unloaded=unloaded):
                    yield x
            elif recurseType == 'breadth':
                refs.extend(cmds.file(ref, q=1, reference=1))


def listReferences(parentReference=None, recursive=False, namespaces=False,
                   refNodes=False, references=True, loaded=None, unloaded=None):
    # type: (Union[str, Path, FileReference], bool, bool, bool, bool, Optional[bool], Optional[bool]) -> List[Union[FileReference, Tuple[unicode, FileReference], Tuple[unicode, FileReference, nt.Reference]]]
    """
    Like iterReferences, except returns a list instead of an iterator.

    Parameters
    ----------
    parentReference : Union[str, Path, FileReference]
        a reference to get sub-references from. If None (default), the current
        scene is used.
    recursive : bool
        recursively determine all references and sub-references
    namespaces : bool
        controls whether namespaces are returned
    refNodes : bool
        controls whether reference PyNodes are returned
    references : bool
        controls whether FileReferences returned
    loaded : Optional[bool]
        whether to return loaded references in the return result; if both of
        loaded/unloaded are not given (or None), then both are assumed True;
        if only one is given, the other is assumed to have the opposite boolean
        value
    unloaded : Optional[bool]
        whether to return unloaded references in the return result; if both of
        loaded/unloaded are not given (or None), then both are assumed True;
        if only one is given, the other is assumed to have the opposite boolean
        value

    Returns
    -------
    List[Union[FileReference, Tuple[unicode, FileReference], Tuple[unicode, FileReference, nt.Reference]]]
    """
    return list(iterReferences(parentReference=parentReference,
                               recursive=recursive,
                               namespaces=namespaces,
                               refNodes=refNodes,
                               references=references,
                               loaded=loaded,
                               unloaded=unloaded))

listReferences.__doc__ += iterReferences.__doc__

# def getReferences( reference=None, recursive=False, namespaces=True, refNodes=False, asDict=True ):
#    """
#    returns references in the scene as (namespace, FileReference) pairs
#
#    :param reference: a reference to get sub-references from. If None (default), the current scene is used.
#    :type reference: string, `Path`, or `FileReference`
#
#    :param recursive: recursively determine all references and sub-references
#    :type recursive: bool
#
#    """
#    import pymel.core.general
#    from pymel.core import other
# if asDict:
##        assert not (namespaces and refNodes)
#
#    res = []
#    if reference is None:
#        refs = zip( cmds.file( q=1, reference=1), cmds.file( q=1, reference=1, unresolvedName=1) )
#    else:
#        refs = zip( cmds.file( reference, q=1, reference=1), cmds.file( reference, q=1, reference=1, unresolvedName=1) )
#
#    for ref, unresolvedRef in refs:
#        row = []
#        print ref, cmds.file( ref, q=1, namespace=1)
#        refNode = cmds.file( ref, q=1, referenceNode=1)
#
#        fileRef = FileReference(ref, unresolvedPath=unresolvedRef)
#        if namespaces:
#            row.append( other.DependNodeName( refNode ).namespace() + cmds.file( ref, q=1, namespace=1)  )
#        if refNodes:
#            row.append( general.PyNode( refNode ) )
#        row.append( fileRef )
#        res.append( row )
#        if recursive:
#            res += getReferences(reference=ref, recursive=True, namespaces=namespaces, refNodes=refNodes)
#
#    return res


def getReferences(parentReference=None, recursive=False):
    # type: (Any, Any) -> Dict[unicode, FileReference]
    """
    Returns
    -------
    Dict[unicode, FileReference]
    """
    return dict(iterReferences(parentReference=parentReference,
                               recursive=recursive, namespaces=True,
                               refNodes=False))

#@decorator
# def suspendReferenceUpdates(func):
#    def suspendedRefUpdateFunc(*args, **kw):
#        ReferenceCache.deferReferenceUpdates(True)
#        try:
#            ret = func(*args, **kw)
#        finally:
#            ReferenceCache.deferReferenceUpdates(False)
#        return ret
#    return suspendedRefUpdateFunc
#
# class ReferenceCache(object):
#    """
#    For the sake of speeding up the process of identifying File References in the scene
#    and properly associating with their respective namespace/reference-node/fullpath,
#    a set of API callbacks is set-up which triggers a file-reference cache refresh.
#
#    This callback mechanism can be suspended temporarily, which is useful when a process
#    needs to change the state of several references at once (loading/unloading, adding/removing).
#    Use the 'deferReferenceUpdates' function or the 'suspendReferenceUpdates' decorator
#    """
#
#    _deferReferenceUpdates = False
#    _callbacks = []
#    _allFiles = []
#    byNamespace = {}
#    byRefNode = {}
#    byFullPath = {}
#    callbacksEnabled = False
#
#    @classmethod
#    def deferReferenceUpdates(cls, state):
#        if state:
#            msg = "SUSPENDING "
#        else:
#            msg = "Enabling"
#        _logger.debug("%s Reference Updates" % (msg))
#        cls._deferReferenceUpdates = state
#
#
#    @classmethod
#    def refresh(cls):
#
#        import pymel.core.general
#        from pymel.core import other
#
#        cls.byNamespace.clear()
#        cls.byRefNode.clear()
#        cls.byFullPath.clear()
#
#        def getRefs(reference=None, currNamespace='' ):
#            res = []
#            args = []
#            if reference is not None:
#                args.append(reference)
#
#            resolved = cmds.file(  q=1, reference=1, *args )
#            unresolved = cmds.file( q=1, reference=1, unresolvedName=1, *args )
#
#            assert len(resolved) == len(unresolved)
#
#            for ref, unresolvedRef in zip( resolved, unresolved ):
#                row = []
#                # we cannot reliably get refNode in a nested reference scenario, but it's ok
#                # we can get the refFile directly from refNode using MFileIO.getReferenceFileByNode()
#                # so there's no real need to keep a dictionary
#
#                namespace = cmds.file( ref, q=1, namespace=1)
#                fullNamespace = currNamespace + namespace
#                row.append( ref )
#                row.append( unresolvedRef )
#                #row.append( refNode )
#                res.append( row )
#                row.append( fullNamespace )
#
#                res += getRefs(ref, fullNamespace + ':' )
#
#            return res
#
#        refData = getRefs()
#        _logger.info("Refreshing %s references..." % len(refData))
#
#        for path, unresolvedPath, namespace in refData:
#
#            #fr = ( fullpath, unresolvedPath )
#
#            _logger.debug("Found %s" % path)
#            #refNode = general.PyNode( refNode )
#            data = ( path, unresolvedPath )
#            # The FileReference Object is inserted into the dictionray under multiple keys
#            # so that it can be easily found using a full-namespace, a reference-node name, or a filepath
#            cls.byNamespace[namespace] = data
#            #cls.byRefNode[refNode] = data
#            cls.byFullPath[path.replace("/","\\")] = data
#            cls.byFullPath[path.replace("\\","/")] = data
#
#    @classmethod
#    def _getAllFileReferences(cls):
#        ret =  [v for (k,v) in cls.byNamspace.iteritems() ]
#        if not ret:
#            cls.refresh()
#            ret =  [v for (k,v) in cls.byNamspace.iteritems()]
#        return ret
#
#    @classmethod
#    def setupFileReferenceCallbacks(cls):
#        cls.callbacksEnabled = True
#
#        def refererencesUpdated(*args):
#            if cls._deferReferenceUpdates:
#                return
#            cls.refresh()
#
#        messages = ['kAfterReference', 'kAfterRemoveReference', 'kAfterImportReference', 'kAfterExportReference', 'kSceneUpdate']
#        for msg in messages:
#            _logger.debug("Setting up File-Reference Callback: %s" % msg)
#            cb = _OpenMaya.MSceneMessage.addCallback(getattr(_OpenMaya.MSceneMessage,msg), refererencesUpdated, None)
#            if hasattr(cb, 'disown'):
#                cb.disown()     # suppresses those swig 'memory leak' warnings
#            cls._callbacks.append(cb)
#
#    @classmethod
#    def getPaths(cls, path=None, namespace=None):
#
#        # there's no guarantee that:
#        #  the namespace has not changed since the last cache refresh
#        #  the refNode has not been renamed since the last cache refresh (doesn't matter if we're using > 2009, where node hashing is not based on name)
#        if not cls.callbacksEnabled or namespace:
#            # force refresh (only need to try once)
#            attempts=1
#            cls.refresh()
#        else:
#            # try twice (refresh if failed the first time)
#            attempts = 2
#
#        while attempts:
#            try:
#                if path:
#                    resolvedPath, unresolvedPath = cls.byFullPath[path]
# elif refnode:
##                    refnode = general.PyNode(refnode)
##                    data = ReferenceCache.byRefNode[refnode]
#                elif namespace:
#                    resolvedPath, unresolvedPath = cls.byNamespace[namespace]
#
#                return resolvedPath, unresolvedPath
#            except KeyError:
#                attempts -= 1
#                if attempts:
#                    ReferenceCache.refresh()
#        raise ValueError("Could not find FileReference (args: %s)" % [path, namespace])


class FileReference(object):

    """
    A class for manipulating references which inherits Path and path.  you can create an
    instance by supplying the path to a reference file, its namespace, or its reference node to the
    appropriate keyword. The namespace and reference node of the reference can be retreived via
    the namespace and refNode properties. The namespace property can also be used to change the namespace
    of the reference.

    Use listReferences command to return a list of references as instances of the FileReference class.

    It is important to note that instances of this class will have their copy number stripped off
    and stored in an internal variable upon creation.  This is to maintain compatibility with the numerous methods
    inherited from the path class which requires a real file path. When calling built-in methods of FileReference,
    the path will automatically be suffixed with the copy number before being passed to maya commands, thus ensuring
    the proper results in maya as well.

    """

#    the reference class now uses a reference node as it's basis, because if we store the refNode as a PyNode, we can
#    quickly and automatically get any updates made to its name through outside methods.  almost any reference info can be queried using the
#    refNode (without resorting to a path, which might change without us knowing), including resolved and unresolved
#    paths.  namespaces are still the one weak spot, for which we must first get a path with copy number.  the use of
#    a refNode precludes the need for the caching system, so long as a) using referenceQuery to get file paths from a refNode
#    provides adequate performance, and b) using referenceQuery in __init__ to get a refNode from a path is os agnostic.
#    in general, since almost all the internal queries use the refNode,
#    there should be little need for the paths, except for displaying to the user.

    def __init__(self, pathOrRefNode=None, namespace=None, refnode=None):
        import pymel.core.general
        from . import nodetypes
        # for speed reasons, we use raw maya.cmds, instead of pmcmds, for some
        # calls here...
        import maya.cmds as mcmds
        self._refNode = None
        if pathOrRefNode:
            if isinstance(pathOrRefNode, (basestring, Path)):
                try:
                    self._refNode = general.PyNode(mcmds.referenceQuery(str(pathOrRefNode), referenceNode=1))
                except RuntimeError:
                    pass
            if not self._refNode:
                if isinstance(pathOrRefNode, nodetypes.Reference):
                    self._refNode = pathOrRefNode
                else:
                    try:
                        self._refNode = general.PyNode(pathOrRefNode)
                    except general.MayaObjectError:
                        pathOrRefNode = str(pathOrRefNode)
                        try:
                            refNodeName = mcmds.file(pathOrRefNode, q=1, referenceNode=1)
                        except RuntimeError:
                            # referenceQuery command is more stable in certain edge cases, like
                            # while a file is loading
                            refNodeName = mcmds.referenceQuery(pathOrRefNode, referenceNode=1)
                        self._refNode = general.PyNode(refNodeName)

        elif namespace:
            namespace = ':' + namespace.strip(':')
            # purposefully not using iterReferences to avoid recursion for speed
            references = mcmds.ls(references=True)
            if references is not None:
                for iRefNode in references:
                    try:
                        if namespace == mcmds.referenceQuery(iRefNode, namespace=True):
                            self._refNode = general.PyNode(iRefNode)
                            break
                    except RuntimeError:
                        # Despite what the docs say, cmds.ls(references=True)
                        # WILL return shared references for refs that have
                        # subrefs; however, these shared sub-reference nodes
                        # won't be queryable... so skip error (don't know of
                        # way to test / filter out shared nodes...)
                        pass
            if self._refNode is None:
                raise RuntimeError("Could not find a reference with the namespace %r" % namespace)

        elif refnode:
            self._refNode = general.PyNode(refnode)

        assert self._refNode.type() == 'reference'

#        def create(path, unresolvedPath ):
#            """Actually create the FileReference object"""
#            def splitCopyNumber(path):
#                """Return a tuple with the path and the copy number. Second element will be None if no copy number"""
#                buf = path.split('{')
#                try:
#                    return ( buf[0], int(buf[1][:-1]) )
#                except:
#                    return (path, None)
#
#            path, copyNumber = splitCopyNumber(path)
#            unresolvedPath, copyNumber2 = splitCopyNumber(unresolvedPath)
#            assert copyNumber == copyNumber2, "copy number of %s is not the same as %s" % ( path, unresolvedPath )
#            self._file = Path(path)
#            self._copyNumber = copyNumber
#            self._unresolvedPath = Path(unresolvedPath)
#            #self._refNode = refNode
#            #return self
#
#        # Direct mappings:
#        # refNode --> refFile:  MFileIO.getReferenceFileByNode( refNode )
#        # refFile --> refNode:  cmds.file( refFile, q=1, referenceNode=1)
#        # refFile --> namespace:  refNode.namespace() + cmds.file( refFile, q=1, namespace=1)
#        self._refNode = None
#
#        import pymel.core.general
#        if unresolvedPath:
#            # check to ensure it's legit
#            assert path in ReferenceCache.byFullPath,  "%s is not a valid reference file" % path
#            return create(path, unresolvedPath)
#
#        if refnode:
#            refNode = general.PyNode(refnode)
#            self._refNode = refNode
#            # refNode is all we need for now. we can get anything else from this when it is asked for
#            return
#
#
#
#        resolvedPath, unresolvedPath = ReferenceCache.getPaths( path, namespace )
#        create( resolvedPath, unresolvedPath )

    def __melobject__(self):
        return self.withCopyNumber()

    def __repr__(self):
        return u'%s(%r, refnode=%r)' % (self.__class__.__name__,
                                        self.withCopyNumber(),
                                        self.refNode.name())

    def __str__(self):
        return self.withCopyNumber()

    def __gt__(self, other):
        return self.withCopyNumber().__gt__(str(other))

    def __ge__(self, other):
        return self.withCopyNumber().__ge__(str(other))

    def __lt__(self, other):
        return self.withCopyNumber().__lt__(str(other))

    def __le__(self, other):
        return self.withCopyNumber().__le__(str(other))

    def __eq__(self, other):
        return self.withCopyNumber().__eq__(str(other))

    def __ne__(self, other):
        return self.withCopyNumber().__ne__(str(other))

    def __hash__(self):
        return hash(self.withCopyNumber())

    def subReferences(self):
        # type: () -> Dict[unicode, FileReference]
        """
        Returns
        -------
        Dict[unicode, FileReference]
        """
        namespace = self.namespace + ':'
        res = {}
        for x in cmds.file(self, q=1, reference=1):
            try:
                res[namespace + cmds.file(x, q=1, namespace=1)] = FileReference(x)
            except Exception as e:
                _logger.warning("Could not get namespace for '%s': %s" % (x, e))
        return res

    @_factories.addMelDocs('namespace', 'exists')
    def namespaceExists(self):
        return cmds.namespace(ex=self.namespace)

    def _getNamespace(self):
        return cmds.file(self.withCopyNumber(), q=1, ns=1)

    def _setNamespace(self, namespace):
        return cmds.file(self.withCopyNumber(), e=1, ns=namespace)
    namespace = property(_getNamespace, _setNamespace)

    @property
    def fullNamespace(self):
        # type: () -> unicode
        """
        Returns
        -------
        unicode
        """
        if self.refNode.isReferenced():
            # getting the fullnamespace for a referenced node is actually a
            # little tricky... initially, we just used the namespace of the
            # reference node itself, and tacked on the namespace associated with
            # this reference

            # Unfortunately, this doesn't work, because it's possible for the
            # reference node itself to be placed in a namespace other than
            # the root.

            # As an example, say we have a "cube.ma", which contains a node,
            # "cubeShape", and we reference that into another scene, creating a
            # reference node called "cubeRN", and associating a namespace
            # "cubeNS".

            # So, the cube node would be ":cubeNS:cubeShape", and the reference
            # node would be ":cubeRN"

            # However, it is actually possible for the reference node itself to
            # be in some other, totally non-related namespace - say,
            # "dead_parrot_NS". In this situation, we would have:
            #    :dead_parrot_NS:cubeRN
            #    :cubeNS:cubeShape
            # Note that cubeShape did NOT inherit the dead_parrot_NS of the
            # reference node which created it!

            # also, we can't use cmds.referenceQuery(parentNamespace=1), as this
            # also does the "wrong" thing, and returns the namespace of the
            # reference node - ie, it would return "dead_parrot_NS"...
            parentFile = cmds.referenceQuery(str(self.refNode), parent=1,
                                             filename=1)
            parentNamespace = FileReference(parentFile).fullNamespace
            if not parentNamespace.endswith(':'):
                parentNamespace += ':'
        else:
            parentNamespace = ''
        return "%s%s" % (parentNamespace, self.namespace)

    @property
    def refNode(self):
        return self._refNode

    @property
    def path(self):
        # type: () -> Path
        """
        Returns
        -------
        Path
        """
        # TODO: check in cache to see if this has changed
        #        if not ReferenceCache.callbacksEnabled or _internal.Version.current < _internal.Version.v2009:
        #            ReferenceCache.refresh()
        #
        #        return ReferenceCache[ self.refNode ]._file

        #path = self.withCopyNumber().split('{')[0]
        path = cmds.referenceQuery(self.refNode, filename=1, withoutCopyNumber=1)
        return Path(path)

    def withCopyNumber(self):
        # type: () -> unicode
        """return the path with the copy number at the end

        Returns
        -------
        unicode
        """
        # the file path is subject to change
        path = cmds.referenceQuery(self.refNode, filename=1)
        return path

#        if self._copyNumber is not None:
#            return u'%s{%d}' % (self.path(), self._copyNumber)
#        return unicode( self.path() )

    def unresolvedPath(self):
        # type: () -> Path
        """
        Returns
        -------
        Path
        """
        path = cmds.referenceQuery(self.refNode, filename=1, unresolvedName=1, withoutCopyNumber=1)
        return Path(path)

    def parent(self):
        # type: () -> Optional[FileReference]
        """Returns the parent FileReference object, or None

        Returns
        -------
        Optional[FileReference]
        """
        parentNode = cmds.referenceQuery(self.refNode, referenceNode=1,
                                         parent=1)
        if parentNode is None:
            return None
        else:
            return FileReference(refnode=parentNode)


#    @_factories.createflag('file', 'importReference')
#    def importContents(self, **kwargs):
#        return cmds.file( self.withCopyNumber(), **kwargs )

    @_factories.addMelDocs('file', 'importReference')
    def importContents(self, removeNamespace=False):
        ns = self.namespace
        res = cmds.file(rfn=self.refNode, importReference=1)
        #res = cmds.file( rfn=self.refNode, importReference=1 )
        if removeNamespace:
            cmds.namespace(mv=(ns, ':'), f=1)
            cmds.namespace(rm=ns)
        return res

#    @_factories.createflag('file', 'removeReference')
#    def remove(self, **kwargs):
#        return cmds.file( self.withCopyNumber(), **kwargs )

    @_factories.addMelDocs('file', 'removeReference')
    def remove(self, **kwargs):
        return cmds.file(rfn=self.refNode, removeReference=1, **kwargs)

#    @_factories.addMelDocs('file', 'unloadReference')
#    def unload(self):
#        return cmds.file( self.withCopyNumber(), unloadReference=1 )

    @_factories.addMelDocs('file', 'unloadReference')
    def unload(self):
        return cmds.file(rfn=self.refNode, unloadReference=1)

    @_factories.addMelDocs('file', 'loadReference')
    def load(self, newFile=None, **kwargs):
        if not newFile:
            args = ()
        else:
            args = (newFile,)
        return cmds.file(loadReference=self.refNode, *args, **kwargs)

    @_factories.addMelDocs('file', 'loadReference')
    def replaceWith(self, newFile, **kwargs):
        return self.load(newFile, **kwargs)

    @_factories.addMelDocs('file', 'cleanReference')
    def clean(self, **kwargs):
        return cmds.file(cleanReference=self.refNode, **kwargs)

    @_factories.addMelDocs('file', 'lockReference')
    def lock(self):
        return cmds.file(self.withCopyNumber(), lockReference=1)

    @_factories.addMelDocs('file', 'lockReference')
    def unlock(self):
        return cmds.file(self.withCopyNumber(), lockReference=0)

#    @_factories.addMelDocs('file', 'deferReference')
#    def isDeferred(self):
#        return cmds.file( self.withCopyNumber(), q=1, deferReference=1 )

    @_factories.addMelDocs('file', 'deferReference')
    def isDeferred(self):
        return cmds.file(rfn=self.refNode, q=1, deferReference=1)

    @_factories.addMelDocs('file', 'deferReference')
    def isLoaded(self):
        return not cmds.file(rfn=self.refNode, q=1, deferReference=1)

    @_factories.addMelDocs('referenceQuery', 'nodes')
    def nodes(self, recursive=False):
        import pymel.core.general
        nodes = cmds.referenceQuery(str(self.refNode), nodes=1, dagPath=1)
        if not nodes:
            nodes = []
        nodes = [general.PyNode(x) for x in nodes]
        if not recursive:
            return nodes
        for ref in iterReferences(parentReference=self, recursive=True):
            nodes.extend(ref.nodes(recursive=False))
        return nodes

    @_factories.addMelDocs('file', 'copyNumberList')
    def copyNumberList(self):
        """returns a list of all the copy numbers of this file"""
        return cmds.file(self, q=1, copyNumberList=1)

    @_factories.addMelDocs('file', 'selectAll')
    def selectAll(self):
        return cmds.file(self.withCopyNumber(), selectAll=1)

    @_factories.addMelDocs('file', 'usingNamespaces')
    def isUsingNamespaces(self):
        return cmds.file(self.withCopyNumber(), q=1, usingNamespaces=1)

    @_factories.addMelDocs('file', 'exportAnimFromReference')
    def exportAnim(self, exportPath, **kwargs):
        kwargs['exportAnimFromReference'] = 1
        _setTypeKwargFromExtension(exportPath, kwargs)
        return Path(cmds.file(exportPath, rfn=self.refNode, **kwargs))

    @_factories.addMelDocs('file', 'exportSelectedAnimFromReference')
    def exportSelectedAnim(self, exportPath, **kwargs):
        kwargs['exportSelectedAnimFromReference'] = 1
        _setTypeKwargFromExtension(exportPath, kwargs)
        return Path(cmds.file(exportPath, rfn=self.refNode, **kwargs))

    def getReferenceEdits(self, **kwargs):
        """Get a list of ReferenceEdit objects for this node

        Adapted from:
        referenceQuery -editString -onReferenceNode <self.refNode>

        Notes
        -----
        By default, removes all edits. If neither of successfulEdits or
        failedEdits is given, they both default to True. If only one is given,
        the other defaults to the opposite value.
        """

        kwargs.pop('editStrings', None)
        kwargs.pop('es', None)
        edits = referenceQuery(self.refNode, editStrings=True,
                               onReferenceNode=self.refNode, **kwargs)
        return edits

    def removeReferenceEdits(self, editCommand=None, force=False, **kwargs):
        # type: (str, bool, **Any) -> None
        """Remove edits from the reference.

        Parameters
        ----------
        editCommand : str
            If specified, remove only edits of a particular type: addAttr,
            setAttr, connectAttr, disconnectAttr or parent
        force : bool
            Unload the reference if it is not unloaded already
        successfulEdits : bool
            Whether to remove successful edits
        failedEdits : bool
            Whether to remove failed edits

        Notes
        -----
        By default, removes all edits. If neither of successfulEdits or
        failedEdits is given, they both default to True. If only one is given,
        the other defaults to the opposite value. This will only succeed on
        unapplied edits (ie, on unloaded nodes, or failed edits)... However,
        like maya.cmds.file/maya.cmds.referenceEdit, no error will be raised
        if there are no unapplied edits to work on. This may change in the
        future, however...
        """

        if force and self.isLoaded():
            self.unload()

        if editCommand:
            kwargs['editCommand'] = editCommand

        _translateEditFlags(kwargs)
        kwargs.pop('r', None)
        kwargs['removeEdits'] = True
        cmds.referenceEdit(str(self.refNode), **kwargs)


def _translateEditFlags(kwargs, addKwargs=True):
    """Given the pymel values for successfulEdits/failedEdits (which may be
    True, False, or None), returns the corresponding maya.cmds values to use
    """
    successful = kwargs.pop('successfulEdits', kwargs.pop('scs', None))
    failed = kwargs.pop('failedEdits', kwargs.pop('fld', None))

    if successful is None and failed is None:
        successful = True
        failed = True
    elif successful is None:
        successful = not failed
    elif failed is None:
        failed = not successful

    if addKwargs:
        kwargs['successfulEdits'] = successful
        kwargs['failedEdits'] = failed
    return successful, failed


def referenceQuery(*args, **kwargs):
    """
    Modifications:
    - When queried for 'es/editStrings', returned a list of ReferenceEdit objects
    - By default, returns all edits. If neither of successfulEdits or
      failedEdits is given, they both default to True. If only one is given,
      the other defaults to the opposite value.
    """
    if kwargs.get("editStrings", kwargs.get("es")):
        from .general import PyNode, MayaNodeError, MayaAttributeError

        fr = None
        if isinstance(args[0], FileReference):
            fr = args[0]
        else:
            target = None
            try:
                target = PyNode(args[0])
            except (MayaNodeError, MayaAttributeError):
                pass

            if target:
                if target.type() == 'reference':
                    fr = FileReference(refnode=target)
                else:
                    fr = target.referenceFile()
            else:
                target = Path(args[0])
                if target.isfile():
                    fr = FileReference(target)

            if not isinstance(fr, FileReference):
                # Last ditch - just try casting to a FileReference
                fr = FileReference(args[0])

        successfulEdits, failedEdits = _translateEditFlags(kwargs,
                                                           addKwargs=False)

        modes = []
        if failedEdits:
            modes.append(False)
        if successfulEdits:
            modes.append(True)

        allEdits = []
        for mode in modes:
            # print "cmds.referenceQuery(%r, failedEdits=%r, successfulEdits=%r, **%r)" % (fr.refNode, not mode, mode, kwargs)
            edits = cmds.referenceQuery(fr.refNode,
                                        failedEdits=not mode,
                                        successfulEdits=mode,
                                        **kwargs)
            if edits is None:
                edits = []
            allEdits.extend(ReferenceEdit(edit, fr, mode) for edit in edits)
        return allEdits
    else:
        if isinstance(args[0], FileReference):
            args = list(args)
            args[0] = args[0].refNode
        return cmds.referenceQuery(*args, **kwargs)

import pymel.core.general as general
import pymel.core.other as other


def _safeEval(s):
    try:
        return eval(s)
    except:
        return s


def _safePyNode(n):
    try:
        return general.PyNode(_safeEval(n))
    except:
        if "." in n:
            return other.AttributeName(n)
        else:
            return other.DependNodeName(n)


class ReferenceEdit(str):

    """
    Parses a reference edit command string into various components based on the edit type.
    This is the class returned by pymel's version of the 'referenceQuery' command.
    """

    def __new__(cls, editStr, fileReference=None, successful=None):
        self = str.__new__(cls, editStr)
        self.type = self.split()[0]
        self.fileReference = fileReference
        self.successful = successful
        return self

    def _getNamespace(self):
        # Lazy load the namespace as it can be expensive to query
        return self.fileReference and self.fileReference.namespace

    def _getFullNamespace(self):
        return self.fileReference and self.fileReference.fullNamespace

    namespace = _util.cacheProperty(_getNamespace, "_namespace")
    fullNamespace = _util.cacheProperty(_getFullNamespace, "_fullNamespace")

    def _getRawEditData(self):
        import pymel.tools.mel2py as mel2py
        pyCmd = "".join(mel2py.mel2pyStr(self + ";").splitlines()[1:])  # chop off the 'import pymel' line
        args, kwargs = eval("dummy" + "".join(pyCmd.partition("(")[1:]), {}, dict(dummy=lambda *x, **y: (x, y)))
        editData = {}
        editData['args'] = args
        editData['kwargs'] = kwargs
        return editData

    def _getEditData(self):
        """
        Returns a dictionary with the relevant data for this reference edit.
        Each edit type will have a different set of keys.
        """
        if self.fileReference:
            def _safeRefPyNode(n):
                n = _safePyNode(_safeEval(n))
                if self.namespace in str(n):
                    ns = self.fileReference.refNode.namespace()
                    if not ns == ":":
                        n = n.addPrefix(ns)
                return n
        else:
            def _safeRefPyNode(n):
                return _safePyNode(_safeEval(n))

        editData = self.rawEditData

        elements = self.split()
        elements.pop(0)

        if self.type == "addAttr":
            editData['node'] = _safeRefPyNode(elements.pop(-1))
            editData['attribute'] = elements.pop(1)
        elif self.type == "setAttr":
            editData['node'] = _safeRefPyNode(elements.pop(0))
            editData['value'] = " ".join(elements)
        elif self.type == "parent":
            editData['node'] = _safeRefPyNode(elements.pop(-1))
            if elements[-1] == "-w":
                editData['child'] = '<World>'
            else:
                editData['child'] = _safePyNode(elements.pop(-1))
        elif self.type == "disconnectAttr":
            if elements[0].startswith("-"):
                elements.append(elements.pop(0))
            refNode, otherNode = [_safeRefPyNode(x) for x in elements[:2]]
            editData['sourceNode'] = refNode
            editData['targetNode'] = otherNode
            otherNode, refNode = sorted([otherNode, refNode], key=lambda n: self.namespace in n)
            editData['node'] = refNode
            del elements[:2]
        elif self.type == "connectAttr":
            if elements[0].startswith("-"):
                elements.append(elements.pop(0))
            refNode, otherNode = [_safeRefPyNode(x) for x in elements[:2]]
            editData['sourceNode'] = refNode
            editData['targetNode'] = otherNode
            otherNode, refNode = sorted([otherNode, refNode], key=lambda n: self.namespace in n)
            editData['node'] = refNode
            del elements[:2]
        else:
            editData['node'] = _safeRefPyNode(elements.pop(0))
        editData['parameters'] = [str(x) for x in elements]

        return editData

    def remove(self, force=False):
        """Remove the reference edit. if 'force=True' then the reference will be unloaded from the scene (if it is not already unloaded)"""
        if self.fileReference.isLoaded():
            if not force:
                raise Exception("Cannon remove edits while reference '%s' is loaded. Unload the reference first, or use the 'force=True' flag." % self.fileReference)
            self.fileReference.unload()
        cmds.referenceEdit(self.editData['node'], removeEdits=True, successfulEdits=True, failedEdits=True, editCommand=self.type)

    editData = _util.cacheProperty(_getEditData, "_editData")
    rawEditData = _util.cacheProperty(_getRawEditData, "_rawEditData")


# TODO: anyModified, modified, errorStatus, executeScriptNodes, lockFile, lastTempFile, renamingPrefixList, renameToSave ( api : mustRenameToSave )
# From API: isReadingFile, isWritingFile, isOpeningFile, isNewingFile, isImportingFile

def _correctPath(path):
    # make paths absolute
    if not os.path.isabs(path) and path != '' and path != untitledFileName():
        path = os.path.normpath(cmds.workspace(q=1, fullName=1) + '/' + path)
    return path


@_factories.addMelDocs('file', 'reference')
def createReference(filepath, **kwargs):
    kwargs['reference'] = True
    res = cmds.file(filepath, **kwargs)
    if kwargs.get('returnNewNodes', kwargs.get('rnn', False)):
        return [general.PyNode(x) for x in res]
    return FileReference(res)


@_factories.addMelDocs('file', 'loadReference')
def loadReference(filepath, **kwargs):
    kwargs['loadReference'] = True
    res = cmds.file(filepath, **kwargs)
    if res is None:
        # TODO:
        # in some situations, a reference may fail to load, but not raise an
        # error - ie, if a kBeforeLoadReferenceCheck callback rejects the load.
        # In these situations, cmds.file will return None. pymel would
        # previously error (with an AttributeError) when it tried to convert the
        # None to a FileReference (or a TypeError if returnNewNodes was True).

        # For backwards compatibility, this still raises an error, but it's
        # been changed to a slightly more informative error... would be nice to
        # unify behavior between this and FileReference.load (which currently
        # returns the results of cmds.file() unaltered) - maybe with a kwarg
        # to control what to do here? - but this would mean a
        # backwards-incompatible change for either this or FileReference.load...
        raise RuntimeError("Unable to load reference for %r" % filepath)

    if kwargs.get('returnNewNodes', kwargs.get('rnn', False)):
        return [general.PyNode(x) for x in res]
    return FileReference(res)


@_factories.addMelDocs('file', 'exportAll')
def exportAll(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportAll'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'exportAsReference')
def exportAsReference(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportAsReference'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        return FileReference(exportPath)
    return FileReference(res)


@_factories.addMelDocs('file', 'exportSelected')
def exportSelected(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportSelected'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'exportAnim')
def exportAnim(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportAnim'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'exportSelectedAnim')
def exportSelectedAnim(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportSelectedAnim'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'exportAnimFromReference')
def exportAnimFromReference(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportAnimFromReference'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'exportSelectedAnimFromReference')
def exportSelectedAnimFromReference(exportPath, **kwargs):
    _setTypeKwargFromExtension(exportPath, kwargs)
    kwargs['exportSelectedAnimFromReference'] = True
    res = cmds.file(exportPath, **kwargs)
    if res is None:
        res = exportPath
    return Path(_correctPath(res))


@_factories.addMelDocs('file', 'i')
def importFile(filepath, **kwargs):
    kwargs['i'] = True
    res = cmds.file(filepath, **kwargs)
    if kwargs.get('returnNewNodes', kwargs.get('rnn', False)):
        return [general.PyNode(x) for x in res]
    # does not return anything


@_factories.createflag('file', 'newFile')
def newFile(**kwargs):
    """
Modifications:
    - returns empty string, for consistency with sceneName()
      ...if you wish to know the untitled scene name, use untitledFileName()
    """
    kwargs.pop('type', kwargs.pop('typ', None))
    cmds.file(**kwargs)
    return ''


@_factories.createflag('file', 'open')
def openFile(filepath, **kwargs):
    res = cmds.file(filepath, **kwargs)
    if kwargs.get('returnNewNodes', kwargs.get('rnn', False)):
        return [general.PyNode(x) for x in res]
    # this command seems to return the last accessed file, which may be a reference
    # i think we're better off spitting the passed path back out
#    if res is None:
#        return Path(filepath)
#    return Path(res)
    return sceneName()


@_factories.addMelDocs('file', 'rename')
def renameFile(newname, *args, **kwargs):
    # we take args and kwargs just for backward compatibility... (only kwarg
    # we use is type/typ)

    # maya retains some sense of whether a file is .ma or .mb, independent of
    # the file name - you can confirm this by doing:
    #    >> cmds.file(new=1, f=1)
    #    >> print cmds.file(q=1, type=1)
    #    ['mayaBinary']
    #    >> cmds.file(rename='foo.ma')
    #    >> print cmds.file(q=1, type=1)
    #    ['mayaBinary']
    #    >> cmds.file(type='mayaAscii')
    #    >> print cmds.file(q=1, type=1)
    #    ['mayaAscii']

    # therefore, we need to set the type OURSELVES when renaming, since this
    # is what is normally desired...

    _setTypeKwargFromExtension(newname, kwargs)
    # for backwards compatability, and because the rename flag cannot be used
    # with any other flags, we mostly throw out the given kwargs...
    fileType = kwargs.get('type', kwargs.get('typ'))
    if fileType is not None:
        cmds.file(type=fileType)
    return Path(cmds.file(rename=newname))


@_factories.addMelDocs('file', 'save')
def saveFile(**kwargs):
    kwargs.pop('s', None)
    kwargs['save'] = True

    # maya sometimes gets in a messed up state, where some methods don't think
    # the scene has a name, and others do - ie, doing
    #     cmds.file(q=1, sceneName=1)
    # will return an empty string, but the titlebar at the top shows a scene
    # name, and OpenMaya.MFileIO.currentFile() returns a valid filname
    # so, putting in a check here for that situation, and just doing a rename
    # if this is the case
    if sceneName() and not cmds.file(q=1, sceneName=1):
        cmds.file(rename=sceneName())
    return Path(cmds.file(**kwargs))


def saveAs(newname, **kwargs):
    # type: (Any, **Any) -> Path
    """
    Returns
    -------
    Path
    """
    _setTypeKwargFromExtension(newname, kwargs)
    cmds.file(rename=newname)
    kwargs['save'] = True
    cmds.file(**kwargs)
    return Path(newname)


def isModified():
    return cmds.file(q=True, modified=True)

# ReferenceCache.setupFileReferenceCallbacks()

#createReference = _factories.make_factories.createflagCmd( 'createReference', cmds.file, 'reference', __name__, returnFunc=FileReference )
#loadReference = _factories.make_factories.createflagCmd( 'loadReference', cmds.file, 'loadReference',  __name__, returnFunc=FileReference )
#exportAnim = _factories.make_factories.createflagCmd( 'exportAnim', cmds.file, 'exportAnim',  __name__, returnFunc=Path )
#exportAnimFromReference = _factories.make_factories.createflagCmd( 'exportAnimFromReference', cmds.file, 'exportAnimFromReference',  __name__, returnFunc=Path )
#exportSelectedAnim = _factories.make_factories.createflagCmd( 'exportSelectedAnim', cmds.file, 'exportSelectedAnim',  __name__, returnFunc=Path )
#exportSelectedAnimFromReference = _factories.make_factories.createflagCmd( 'exportSelectedAnimFromReference', cmds.file, 'exportSelectedAnimFromReference', __name__,  returnFunc=Path )
#importFile = _factories.make_factories.createflagCmd( 'importFile', cmds.file, 'i',  __name__, returnFunc=Path )
#newFile = _factories.make_factories.createflagCmd( 'newFile', cmds.file, 'newFile',  __name__, returnFunc=Path )
#openFile = _factories.make_factories.createflagCmd( 'openFile', cmds.file, 'open',  __name__, returnFunc=Path )
#renameFile = _factories.make_factories.createflagCmd( 'renameFile', cmds.file, 'rename',  __name__, returnFunc=Path )

# ------ Do not edit below this line --------

aaf2fcp = _factories.getCmdFunc('aaf2fcp')

allNodeTypes = _factories.getCmdFunc('allNodeTypes')

assignInputDevice = _factories.getCmdFunc('assignInputDevice')

attachDeviceAttr = _factories.getCmdFunc('attachDeviceAttr')

attrCompatibility = _factories.getCmdFunc('attrCompatibility')

audioTrack = _factories.getCmdFunc('audioTrack')

autoSave = _factories.getCmdFunc('autoSave')

cacheFile = _factories.getCmdFunc('cacheFile')

cacheFileCombine = _factories.getCmdFunc('cacheFileCombine')

cacheFileMerge = _factories.getCmdFunc('cacheFileMerge')

cacheFileTrack = _factories.getCmdFunc('cacheFileTrack')

clearCache = _factories.getCmdFunc('clearCache')

cmdFileOutput = _factories.getCmdFunc('cmdFileOutput')

convertUnit = _factories.getCmdFunc('convertUnit')

crashInfo = _factories.getCmdFunc('crashInfo')

dagObjectCompare = _factories.getCmdFunc('dagObjectCompare')

date = _factories.getCmdFunc('date')

dbcount = _factories.getCmdFunc('dbcount')

dbfootprint = _factories.getCmdFunc('dbfootprint')

dbmessage = _factories.getCmdFunc('dbmessage')

dbpeek = _factories.getCmdFunc('dbpeek')

dbtrace = _factories.getCmdFunc('dbtrace')

detachDeviceAttr = _factories.getCmdFunc('detachDeviceAttr')

deviceEditor = _factories.getCmdFunc('deviceEditor')

@_factories.addCmdDocs
def devicePanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.devicePanel(*args, **kwargs)
    return res

dgInfo = _factories.getCmdFunc('dgInfo')

dgValidateCurve = _factories.getCmdFunc('dgValidateCurve')

dgdirty = _factories.getCmdFunc('dgdirty')

dgeval = _factories.getCmdFunc('dgeval')

dgfilter = _factories.getCmdFunc('dgfilter')

dgmodified = _factories.getCmdFunc('dgmodified')

dgtimer = _factories.getCmdFunc('dgtimer')

dirmap = _factories.getCmdFunc('dirmap')

diskCache = _factories.getCmdFunc('diskCache')

displayString = _factories.getCmdFunc('displayString')

dynamicLoad = _factories.getCmdFunc('dynamicLoad')

error = _factories.getCmdFunc('error')

@_factories.addCmdDocs
def exportEdits(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.exportEdits(*args, **kwargs)
    return res

fcheck = _factories.getCmdFunc('fcheck')

@_factories.addCmdDocs
def fileBrowserDialog(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['fc', 'fileCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.fileBrowserDialog(*args, **kwargs)
    return res

fileDialog = _factories.getCmdFunc('fileDialog')

@_factories.addCmdDocs
def fileDialog2(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['fileTypeChanged', 'ftc', 'oc2', 'oca', 'ocm', 'ocr', 'oin', 'optionsUICancel', 'optionsUICommit', 'optionsUICommit2', 'optionsUICreate', 'optionsUIInit', 'sc', 'selectionChanged']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.fileDialog2(*args, **kwargs)
    return res

fileInfo = _factories.addCmdDocs(fileInfo, cmdName='fileInfo')

filePathEditor = _factories.getCmdFunc('filePathEditor')

findType = _factories.getCmdFunc('findType')

flushUndo = _factories.getCmdFunc('flushUndo')

getFileList = _factories.getCmdFunc('getFileList')

getInputDeviceRange = _factories.getCmdFunc('getInputDeviceRange')

getModifiers = _factories.getCmdFunc('getModifiers')

getModulePath = _factories.getCmdFunc('getModulePath')

hardware = _factories.getCmdFunc('hardware')

hitTest = _factories.getCmdFunc('hitTest')

imfPlugins = _factories.getCmdFunc('imfPlugins')

internalVar = _factories.getCmdFunc('internalVar')

launch = _factories.getCmdFunc('launch')

launchImageEditor = _factories.getCmdFunc('launchImageEditor')

listDeviceAttachments = _factories.getCmdFunc('listDeviceAttachments')

listInputDeviceAxes = _factories.getCmdFunc('listInputDeviceAxes')

listInputDeviceButtons = _factories.getCmdFunc('listInputDeviceButtons')

listInputDevices = _factories.getCmdFunc('listInputDevices')

loadModule = _factories.getCmdFunc('loadModule')

@_factories.addCmdDocs
def loadPlugin(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ac', 'addCallback', 'rc', 'removeCallback']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.loadPlugin(*args, **kwargs)
    return res

melInfo = _factories.getCmdFunc('melInfo')

memory = _factories.getCmdFunc('memory')

moduleInfo = _factories.getCmdFunc('moduleInfo')

mouse = _factories.getCmdFunc('mouse')

namespace = _factories.getCmdFunc('namespace')

namespaceInfo = _factories.addCmdDocs(namespaceInfo)

ogs = _factories.getCmdFunc('ogs')

openCLInfo = _factories.getCmdFunc('openCLInfo')

openGLExtension = _factories.getCmdFunc('openGLExtension')

openMayaPref = _factories.getCmdFunc('openMayaPref')

pluginDisplayFilter = _factories.getCmdFunc('pluginDisplayFilter')

@_factories.addCmdDocs
def pluginInfo(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'cc', 'changedCommand', 'cnc', 'command', 'constraintCommand', 'controlCommand', 'ctc', 'mec', 'modelEditorCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.pluginInfo(*args, **kwargs)
    return res

@_factories.addCmdDocs
def preloadRefEd(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['sc', 'selectCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.preloadRefEd(*args, **kwargs)
    return res

profiler = _factories.getCmdFunc('profiler')

profilerTool = _factories.getCmdFunc('profilerTool')

recordAttr = _factories.getCmdFunc('recordAttr')

redo = _factories.getCmdFunc('redo')

@_factories.addCmdDocs
def reference(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.reference(*args, **kwargs)
    return res

@_factories.addCmdDocs
def referenceEdit(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.referenceEdit(*args, **kwargs)
    return res

_referenceQuery = referenceQuery

@_factories.addCmdDocs
def referenceQuery(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = _referenceQuery(*args, **kwargs)
    return res

rehash = _factories.getCmdFunc('rehash')

reloadImage = _factories.getCmdFunc('reloadImage')

requires = _factories.getCmdFunc('requires')

@_factories.addCmdDocs
def saveImage(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.saveImage(*args, **kwargs)
    return res

@_factories.addCmdDocs
def sceneEditor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['sc', 'selectCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.sceneEditor(*args, **kwargs)
    return res

sceneUIReplacement = _factories.getCmdFunc('sceneUIReplacement')

scriptNode = _factories.getCmdFunc('scriptNode')

selLoadSettings = _factories.getCmdFunc('selLoadSettings')

setAttrMapping = _factories.getCmdFunc('setAttrMapping')

setInputDeviceMapping = _factories.getCmdFunc('setInputDeviceMapping')

shotTrack = _factories.getCmdFunc('shotTrack')

showHelp = _factories.getCmdFunc('showHelp')

sysFile = _factories.getCmdFunc('sysFile')

timer = _factories.getCmdFunc('timer')

timerX = _factories.getCmdFunc('timerX')

translator = _factories.getCmdFunc('translator')

unassignInputDevice = _factories.getCmdFunc('unassignInputDevice')

undo = _factories.getCmdFunc('undo')

undoInfo = _factories.getCmdFunc('undoInfo')

unknownNode = _factories.getCmdFunc('unknownNode')

unknownPlugin = _factories.getCmdFunc('unknownPlugin')

@_factories.addCmdDocs
def unloadPlugin(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ac', 'addCallback', 'rc', 'removeCallback']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.unloadPlugin(*args, **kwargs)
    return res

warning = _factories.getCmdFunc('warning')

whatsNewHighlight = _factories.getCmdFunc('whatsNewHighlight')

workspace = _factories.addCmdDocs(workspace, cmdName='workspace')

xpmPicker = _factories.getCmdFunc('xpmPicker')

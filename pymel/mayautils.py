"""Utilities for getting Maya resource directories, sourcing scripts, and executing deferred.

These do not require initialization of maya.standalone"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from past.builtins import execfile
from builtins import next
from builtins import str
from past.builtins import basestring
import os
import sys
import re
import platform
import pymel.versions as versions
import pymel.internal as _internal
_logger = _internal.getLogger(__name__)
from pymel.util import path as _path

if False:
    from typing import *

sep = os.path.pathsep


def source(file, searchPath=None, recurse=False):
    # type: (Any, Iterable[str], bool) -> None
    """
    Execute a python script.

    Search for a python script in the specified path and execute it using
    ``execfile``.

    Parameters
    ----------
    searchPath : Iterable[str]
        list of directories in which to search for ``file``.
        uses ``sys.path`` if no path is specified
    recurse : bool
        whether to recurse into directories in ``searchPath``
    """
    filepath = str(file)
    filename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)

    if searchPath is None:
        searchPath = sys.path
    if isinstance(searchPath, basestring):
        searchPath = [searchPath]
    itpath = iter(searchPath)
    _logger.debug("looking for file as: " + filepath)
    while not os.path.exists(filepath):
        try:
            p = os.path.abspath(os.path.realpath(next(itpath)))
            filepath = os.path.join(p, filename)
            _logger.debug('looking for file as: ' + filepath)
            if recurse and not filepath.exists():
                itsub = os.walk(p)
                while not os.path.exists(filepath):
                    try:
                        root, dirs, files = next(itsub)
                        itdirs = iter(dirs)
                        while not os.path.exists(filepath):
                            try:
                                filepath = os.path.join(root, next(itdirs), filename)
                                _logger.debug('looking for file as: ' + filepath)
                            except:
                                pass
                    except:
                        pass
        except:
            raise ValueError("File '" + filename + "' not found in path")
            # In case the raise exception is replaced by a warning don't
            # forget to return here
            return
    # _logger.debug("Executing: "+filepath)
    return execfile(filepath)


def getMayaLocation(version=None):
    # type: (bool) -> Optional[str]
    """
    Get the path to the Maya install directory.

    .. note:: The Maya location is defined as the directory above /bin.

    Uses the ``MAYA_LOCATION`` environment variable and ``sys.executable`` path.

    Returns None if not found.

    Parameters
    ----------
    version : bool
        if passed, will attempt to find a matching Maya location.  If the
        version found above does not match the requested version,
        this function uses a simple find/replace heuristic to modify the path and test
        if the desired version exists.

    Returns
    -------
    Optional[str]
    """
    try:
        loc = os.path.realpath(os.environ['MAYA_LOCATION'])
    except:
        loc = os.path.dirname(os.path.dirname(sys.executable))
    # get the path of a different maya version than current
    if version:
        # note that a recursive loop between getMayaLocation / getMayaVersion
        # is avoided because getMayaVersion always calls getMayaLocation with
        # version == None
        actual_long_version = versions.installName()
        actual_short_version = versions.shortName()
        if version != actual_long_version:
            short_version = versions.parseVersionStr(version, extension=False)
            if version == short_version:
                try_version = actual_long_version.replace(actual_short_version,
                                                          short_version)
            else:
                try_version = version
            try_loc = loc.replace(actual_long_version, try_version)
            if os.path.exists(try_loc):
                loc = try_loc
            else:
                _logger.warning("No Maya found for version %s" % version)
                return None

    return loc


def getMayaAppDir(versioned=False):
    # type: (bool) -> Optional[str]
    """
    Get the path to the current user's Maya application directory.

    First checks ``MAYA_APP_DIR``, then tries OS-specific defaults.

    Returns None, if not found

    Parameters
    ----------
    versioned : bool
        if True, the current Maya version including '-x64' suffix, if
        applicable, will be appended.

    Returns
    -------
    Optional[str]
    """
    appDir = os.environ.get('MAYA_APP_DIR', None)
    if appDir is None:
        if os.name == 'nt':
            appDir = os.environ.get('USERPROFILE', os.environ.get('HOME', None))
            if appDir is None:
                return None

            # Vista or newer... version() returns "6.x.x"
            if int(platform.version().split('.')[0]) > 5:
                appDir = os.path.join(appDir, 'Documents')
            else:
                appDir = os.path.join(appDir, 'My Documents')
        else:
            appDir = os.environ.get('HOME', None)
            if appDir is None:
                return None

        if platform.system() == 'Darwin':
            appDir = os.path.join(appDir, 'Library/Preferences/Autodesk/maya')
        else:
            appDir = os.path.join(appDir, 'maya')

    if versioned and appDir:
        appDir = os.path.join(appDir, versions.installName())

    return appDir


def getUserPrefsDir():
    """Get the prefs directory below the Maya application directory"""
    appDir = getMayaAppDir(versioned=True)
    if appDir:
        return os.path.join(appDir, 'prefs')


def getUserScriptsDir():
    """Get the scripts directory below the Maya application directory"""
    appDir = getMayaAppDir(versioned=True)
    if appDir:
        return os.path.join(appDir, 'scripts')


def executeDeferred(func, *args, **kwargs):
    """
    This is a wrap for maya.utils.executeDeferred.  Maya's version does not
    execute at all when in batch mode, so this function does a simple check to
    see if we're in batch or interactive mode.  In interactive it runs
    `maya.utils.executeDeferred`, and if we're in batch mode, it just executes
    the function.

    Use this function in your userSetup.py file if:
        1. you are importing pymel there
        2. you want to execute some code that relies on maya.cmds
        3. you want your userSetup.py to work in both interactive and
           standalone mode

    Example userSetup.py file::

        from pymel.all import *
        def delayedStartup():
           print "executing a command"
           pymel.about(apiVersion=1)
        mayautils.executeDeferred( delayedStartup )

    Takes a single parameter which should be a callable function.
    """
    import maya.utils
    import maya.OpenMaya
    if maya.OpenMaya.MGlobal.mayaState() == maya.OpenMaya.MGlobal.kInteractive:
        maya.utils.executeDeferred(func, *args, **kwargs)
    else:
        if isinstance(func, basestring):
            if args or kwargs:
                raise ValueError('if passing a string to be executed, no '
                                 'additional args may be passed')
            exec(func)
        else:
            func(*args, **kwargs)


def recurseMayaScriptPath(roots=[], verbose=False, excludeRegex=None,
                          errors='warn', prepend=False):
    # type: (Union[str, List[str], Tuple[str]], bool, str, Any, Any) -> None
    """
    Given a path or list of paths, recurses through directories appending to
    the ``MAYA_SCRIPT_PATH`` environment variable any found directories
    containing mel scripts.

    The root directories, if given, are always added to the
    ``MAYA_SCRIPT_PATH``, even if they don't contain any mel scripts.

    Parameters
    ----------
    roots : Union[str, List[str], Tuple[str]]
        a single path or list of paths to recurse. if left to its default,
        will use the current ``MAYA_SCRIPT_PATH`` values
    verbose : bool
        verbose on or off
    excludeRegex : str
        string to be compiled to a regular expression of paths to skip.
        This regex only needs to match the folder name
    """

    regex = '[.]|(obsolete)'

    if excludeRegex:
        assert isinstance(excludeRegex, basestring), \
            "please pass a regular expression as a string"
        regex = regex + '|' + excludeRegex

    includeRegex = "(?!(" + regex + "))"  # add a negative lookahead assertion

    scriptPath = os.environ["MAYA_SCRIPT_PATH"]
    varList = scriptPath.split(os.path.pathsep)
    initalLen = len(varList)

    def addDir(toAdd):
        if toAdd not in varList:
            if prepend:
                _logger.debug("Prepending script path directory %s" % toAdd)
                varList.insert(0, toAdd)
            else:
                _logger.debug("Appending script path directory %s" % toAdd)
                varList.append(toAdd)

    if roots:
        if isinstance(roots, list) or isinstance(roots, tuple):
            rootVars = list(roots)
        else:
            rootVars = [roots]
        # Roots are always added to the script path, even if they don't have
        # .mel files
        for d in rootVars:
            addDir(d)
    # else expand the whole  environment  currently set
    else:
        rootVars = varList[:]

    _logger.debug("Recursing Maya script path")
    _logger.debug("Only directories which match %s will be traversed" %
                  includeRegex)
    for rootVar in rootVars:
        root = _path(rootVar)
        if re.match(includeRegex, root.name) and root.exists():
            _logger.debug("Searching for all valid script directories "
                          "below %s" % rootVar)
            for f in root.walkdirs(errors=errors, regex=includeRegex):
                try:
                    if len(f.files("*.mel")):
                        addDir(str(f))
                except OSError:
                    pass

    if len(varList) > initalLen:
        os.environ["MAYA_SCRIPT_PATH"] = os.path.pathsep.join(varList)
        _logger.info("Added %d directories to Maya script path" %
                     (len(varList) - initalLen))
    else:
        _logger.info("Maya script path recursion did not find any paths to add")

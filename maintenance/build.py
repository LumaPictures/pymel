'''
Regenerate the core modules using parsed data and templates
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import zip
from builtins import range
from builtins import open
from past.builtins import basestring
from builtins import object
import compileall
import inspect
import keyword
import os.path
import re
import sys
import types
from collections import defaultdict, OrderedDict
from future.utils import PY2

from jinja2 import Environment, PackageLoader

import pymel.util as util
import pymel.versions as versions
from pymel.util.conditions import Always
from pymel.internal import factories
from pymel.internal import plogging
from pymel.internal import pmcmds
from pymel.internal import apicache

import maintenance.buildutil

if False:
    from typing import *

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)

_logger = plogging.getLogger(__name__)

START_MARKER = '# ------ Do not edit below this line --------'
END_MARKER =   '# ------ Do not edit above this line --------'


env = Environment(loader=PackageLoader('maintenance', 'templates'),
                  trim_blocks=True, lstrip_blocks=True)


def makeTypeComment(signature):
    # type: (factories.Annotations) -> str
    args = signature.get('args')
    if args is not None:
        argSig = ', '.join(args)
    else:
        argSig = '...'
    comment = '# type: (%s)' % argSig
    result = signature.get('result')
    if result is None:
        result = 'Any'
    return comment + ' -> ' + result


class NewOverrideError(RuntimeError):
    def __init__(self, methodNamesToBridgeKeys):
        self.methodNamesToBridgeKeys = methodNamesToBridgeKeys

    def __str__(self):
        methodsAndKeys = []
        for method in sorted(self.methodNamesToBridgeKeys):
            bridgeKey = self.methodNamesToBridgeKeys[method]
            methodsAndKeys.append('  {!r} / {!r}'.format(method, bridgeKey))
        methodsAndKeys = '\n'.join(methodsAndKeys)

        return (
            "Found api methods with the same name as an already-implemented method\n"
            "higher in the hierarchy. You must decide what you want to do, and\n"
            "record it in the ApiMelBridgeCache.apiToMelData. For each method,\n"
            "either:\n"
            "  a) you want to override the earlier implementation, in which\n"
            "     case you should use {'override': True}\n"
            "  b) you want to ignore the override, in which case you should use\n"
            "     {'enable': False}\n"
            "  c) you want to rename the method so there is no conflict, in which\n"
            "     case you should use {'useName': 'newName'}\n"
            "Found methods / apiToMelData-keys:\n"
            + methodsAndKeys)


def underscoreSortKey(val):
    '''Sort key to make underscores come before numbers / letters'''
    if isinstance(val, basestring):
        # 07 is the "bell" character - shouldn't generally be in strings!
        return val.replace('_', '\x07')
    return val


class Literal(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        # +1 is just so we get a different hash than self.value
        return hash(self.value) + 1


def methodNames(cls, apicls=None):
    # type: (Type, Optional[Type]) -> Set[str]
    if apicls:
        herited = set()
        for base in inspect.getmro(cls):
            if base is apicls:
                continue
            for attr, obj in base.__dict__.items():
                if PY2:
                    if inspect.ismethod(obj):
                        herited.add(attr)
                else:
                    if inspect.function(obj):
                        herited.add(attr)
        return herited
    else:
        if PY2:
            return set([name for name, obj in inspect.getmembers(cls)
                        if inspect.ismethod(obj)])
        else:
            return set([name for name, obj in inspect.getmembers(cls)
                        if inspect.isfunction(obj)])


def importableName(func, module=None, moduleMap=None):
    try:
        name = func.__name__
    except AttributeError:
        name = func.__class__.__name__

    if name == '<lambda>':
        raise ValueError("received lambda function")

    builtin_mod_name = 'builtins'
    if PY2:
        builtin_mod_name = '__builtin__'
    if func.__module__ == builtin_mod_name:
        path = name
    else:
        if module:
            moduleName = module
        elif moduleMap:
            moduleName = moduleMap.get(func.__module__, func.__module__)
        else:
            moduleName = func.__module__
        if moduleName:
            path = "{}.{}".format(moduleName, name)
        else:
            path = name
    return path


def _setRepr(s):
    # type: (Iterable) -> str
    return '{' + ', '.join([repr(s) for s in sorted(s)]) + '}'


def _listRepr(s):
    # type: (Iterable) -> str
    # we use tuple because they are faster to construct than lists and we have
    # a lot of big lists of flags
    return '(' + ', '.join([repr(s) for s in sorted(s)]) + ')'


def functionTemplateFactory(funcName, module, returnFunc=None,
                            rename=None, uiWidget=False):
    # type: (str, types.ModuleType, Optional[str], Optional[str], bool) -> str
    """
    Parameters
    ----------
    funcName : str
    module : types.ModuleType
    returnFunc : Optional[str]
    rename : Optional[str]
    uiWidget : bool

    Returns
    -------
    str
    """
    inFunc, funcName, customFunc = factories._getSourceFunction(funcName, module)
    if inFunc is None:
        return ''

    cmdInfo = factories.cmdlist[funcName]
    funcType = type(inFunc)

    if funcType == types.BuiltinFunctionType:
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                _logger.warning("Function found in module %s has different name "
                                "than desired: %s != %s. simple fix? %s" %
                                (inFunc.__module__, funcName, newFuncName,
                                funcType == types.FunctionType and
                                returnFunc is None))
        except AttributeError:
            _logger.warning("%s had no '__name__' attribute" % inFunc)

    timeRangeFlags = factories._getTimeRangeFlags(funcName)
    if timeRangeFlags:
        timeRangeFlags = _listRepr(timeRangeFlags)
    # some refactoring done here - to avoid code duplication (and make things
    # clearer), we now ALWAYS do things in the following order:
    # 1. Perform operations which modify the execution of the function (ie,
    #    adding return funcs)
    # 2. Modify the function descriptors - ie, __doc__, __name__, etc

    # FIXME: merge the unpack case with maybeConvert case in the template:
    #  both test for 'not query'

    # create a repr for a set of flags (but make it ordered so it's stable)
    # unpackFlags = []
    # flags = cmdInfo.get('flags', {})
    # for flag in sorted(flags):
    #     flagInfo = flags[flag]
    #     if flagInfo.get('resultNeedsUnpacking', False):
    #         unpackFlags.append(repr(flagInfo.get('longname', flag)))
    #         unpackFlags.append(repr(flagInfo.get('shortname', flag)))

    unpackFlags = set()
    for flag, flagInfo in cmdInfo.get('flags', {}).items():
        if flagInfo.get('resultNeedsUnpacking', False):
            unpackFlags.add(flagInfo.get('longname', flag))
            unpackFlags.add(flagInfo.get('shortname', flag))

    if unpackFlags:
        unpackFlags = _setRepr(unpackFlags)

    # if funcName in factories.simpleCommandWraps:
    #     # simple wraps: we only do these for functions which have not been
    #     # manually customized
    #     wraps = factories.simpleCommandWraps[funcName]
    #     doc = 'Modifications:\n'
    #     for func, wrapCondition in wraps:
    #         if wrapCondition != Always:
    #             # use only the long flag name
    #             flags = ' for flags: ' + str(wrapCondition)
    #         elif len(wraps) > 1:
    #             flags = ' for all other flags'
    #         else:
    #             flags = ''
    #         if func.__doc__:
    #             funcString = func.__doc__.strip()
    #         else:
    #             funcString = pmcmds.getCmdName(func) + '(result)'
    #         doc += '  - ' + funcString + flags + '\n'

    existing = inFunc.__module__ == module.__name__
    resultNeedsUnpacking = cmdInfo.get('resultNeedsUnpacking', False)
    callbackFlags = cmdInfo.get('callbackFlags', None)
    if callbackFlags:
        callbackFlags = _listRepr(callbackFlags)
    isWrapped = funcName in factories.simpleCommandWraps
    if any([timeRangeFlags, returnFunc, resultNeedsUnpacking, unpackFlags,
            isWrapped, callbackFlags]):
        sourceFuncName = importableName(inFunc,
                                        moduleMap={'pymel.internal.pmcmds': 'cmds'})

        result = ''
        if existing:
            if isinstance(inFunc.__doc__, util.LazyDocString):
                # inFunc was already decorated with @addCmdDocs
                _logger.warning("Warning: %s.%s is decorated with "
                                "@addCmdDocs but it will be re-wrapped" %
                                (inFunc.__module__, funcName))

            sourceFuncName = sourceFuncName.rsplit('.', 1)[1]
            result += '\n_{func} = {func}\n'.format(func=sourceFuncName)
            sourceFuncName = '_' + sourceFuncName

        template = env.get_template('commandfunc.py')
        rendered = template.render(
            funcName=rename or funcName,
            commandName=funcName,
            timeRangeFlags=timeRangeFlags,
            sourceFuncName=sourceFuncName,
            returnFunc=returnFunc,
            resultNeedsUnpacking=resultNeedsUnpacking,
            unpackFlags=unpackFlags,
            simpleWraps=isWrapped,
            callbackFlags=callbackFlags,
            uiWidget=uiWidget)
        if PY2:
            rendered = rendered.encode()
        return result + rendered
    else:
        if existing:
            guessedName = factories._guessCmdName(inFunc)
            if isinstance(inFunc.__doc__, util.LazyDocString):
                # inFunc was already decorated with @addCmdDocs
                return ''

            _logger.warning("%s.%s should be decorated with @addCmdDocs to "
                            "generate better stubs" %
                            (inFunc.__module__, guessedName))

            if guessedName != funcName:
                # for, ie, fileInfo = FileInfo(), optionVar = OptionVar(),
                # workspace = Workspace()
                explicitCmdName = ', cmdName={!r}'.format(funcName)
            else:
                explicitCmdName = ''
            return "\n{newName} = _factories.addCmdDocs({origName}{explicitCmdName})\n".format(
                newName=rename or funcName,
                origName=funcName,
                explicitCmdName=explicitCmdName)
        else:
            # no doc in runtime module
            if module.__name__ == 'pymel.core.runtime':
                return "\n{newName} = getattr(cmds, '{origName}', None)\n".format(
                    newName=rename or funcName,
                    origName=funcName)
            else:
                return "\n{newName} = _factories.getCmdFunc('{origName}')\n".format(
                    newName=rename or funcName,
                    origName=funcName)

    # FIXME: THIS IS UNREACHABLE
    #   handle these!
    # Check if we have not been wrapped yet. if we haven't and our input
    # function is a builtin or we're renaming then we need a wrap. otherwise
    # we can just change the __doc__ and __name__ and move on
    # if newFunc == inFunc and (type(newFunc) == types.BuiltinFunctionType or rename):
    #     # we'll need a new function: we don't want to touch built-ins, or
    #     # rename an existing function, as that can screw things up... just modifying docs
    #     # of non-builtin should be fine, though
    #     def newFunc(*args, **kwargs):
    #         return inFunc(*args, **kwargs)
    #
    # # 2. Modify the function descriptors - ie, __doc__, __name__, etc
    # if customFunc:
    #     # copy over the exisitng docs
    #     if not newFunc.__doc__:
    #         newFunc.__doc__ = inFunc.__doc__
    #     elif inFunc.__doc__:
    #         newFunc.__doc__ = inFunc.__doc__
    # addCmdDocs(newFunc, cmdName=funcName)


def _getModulePath(module):
    if isinstance(module, basestring):
        this = sys.modules[__name__]
        root = os.path.dirname(os.path.dirname(this.__file__))
        return os.path.join(root, *module.split('.')) + '.py'
    else:
        return module.__file__.rsplit('.', 1)[0] + '.py'


def _getSourceStartEndLines(object):
    srclines, startline = inspect.getsourcelines(object)
    endline = startline + len(srclines) - 1
    return startline, endline


# right now, we only support versioning for Enums, because that's the only
# thing that really "needs" it - other things (classes, methods, and flags) will
# just raise an error if someone tries to use them from a version that doesn't
# have them.  Enums change between versions, and will potentially silently
# have the "wrong" info.
class VersionedCaches(object):
    _symbolicVersions = None

    def __init__(self):
        self.allStrVersions = apicache.ApiCache.allVersions()
        self.strVersionsToApiVersions = {}  # type: Dict[str, int]
        self.apiVersionsToStrVersions = {}  # type: Dict[int, str]
        for strVersion in self.allStrVersions:
            apiVersion = self.strVersionToApi(strVersion)
            self.strVersionsToApiVersions[strVersion] = apiVersion
            self.apiVersionsToStrVersions[apiVersion] = strVersion
        self.allApiVersions = sorted(self.apiVersionsToStrVersions)
        self.apiCachesByVersion = OrderedDict()  # type: OrderedDict[int, Optional[apicache.ApiCache]]
        # insert None's just to get the order right
        for apiVersion in self.allApiVersions:
            self.apiCachesByVersion[apiVersion] = None

    @classmethod
    def strVersionToApi(cls, strVersion):
        # type: (str) -> int
        mainVersion = int(strVersion.split('.')[0])
        if mainVersion < 2018:
            return mainVersion * 100
        else:
            return mainVersion * 10000

    @classmethod
    def apiVersion(cls, version):
        # type: (Union[str, int]) -> int
        if isinstance(version, basestring):
            return cls.strVersionToApi(version)
        elif isinstance(version, int) and version > 200000:
            return version
        else:
            raise ValueError(version)

    def _getApiSubCache(self, version, subcacheName):
        # type: (Union[str, int], str) -> Any
        apiCache = self.getApiCache(version)
        return getattr(apiCache, subcacheName)

    # def getApiClassInfo(self, version):
    #     return self._getApiSubCache(version, 'apiClassInfo')

    def getApiCache(self, version):
        # type: (Union[str, int]) -> apicache.ApiCache
        apiVersion = self.apiVersion(version)
        cacheInst = self.apiCachesByVersion[apiVersion]
        if cacheInst is None:
            strVersion = self.apiVersionsToStrVersions[apiVersion]
            cacheInst = apicache.ApiCache()
            cacheInst.version = strVersion
            cacheInst.build()
            self.apiCachesByVersion[apiVersion] = cacheInst
        return cacheInst

    def _getAllApiSubCaches(self, subcacheName):
        # type: (str) -> OrderedDict[int, Any]
        """
        Get the subcache keyed by maya version.
        """
        result = OrderedDict()
        for version in self.allApiVersions:
            # skip versions greater than our current - trying to load them
            # will probably bring in objects that we don't have in this version,
            # resulting in an import error, and attempting to rebuild...
            if versions.current() < version:
                continue
            result[version] = self._getApiSubCache(version, subcacheName)
        return result

    def getAllApiClassInfos(self):
        # type: () -> OrderedDict[int, Dict[str, Any]]
        """
        Get the apiClassInfo keyed by maya version.
        """
        return self._getAllApiSubCaches('apiClassInfo')

    def getAllApiTypesToApiEnums(self):
        # type: () -> OrderedDict[int, Dict[str, int]]
        """
        Get the apiTypesToApiEnums keyed by maya version.
        """
        return self._getAllApiSubCaches('apiTypesToApiEnums')

    def getVersionedClassInfo(self, apiClsName):
        # type: (str) -> OrderedDict[int, Optional[Dict[str, Any]]]
        verClassInfo = OrderedDict()
        for version, classInfo in self.getAllApiClassInfos().items():
            verClassInfo[version] = classInfo.get(apiClsName)
        return verClassInfo

    def getVersionedClassCategory(self, apiClsName, category):
        # type: (str, str) -> OrderedDict[str, OrderedDict[int, Any]]
        '''
        Given versionedClassInfo that looks like:

            {
                2017: {
                    'MFnAwesome': {
                        'functions': {
                            'foo': 1,
                        }
                    }, ...
                },
                2018: {
                    'MFnAwesome': {
                        'functions': {
                            'foo': 1,
                            'bar': 10,
                        }
                    }, ...
                },
                2019: {
                    'MFnAwesome': {
                        'functions': {
                            'foo': 2,
                            'bar': 10,
                        }
                    }, ...
                },
            }

        then getVersionedClassCategory('MFnAwesome', 'functions') would return:

            {
                'foo': {2017: 1, 2018: 1, 2019: 2},
                'bar': {2017: None, 2018: 10, 2019: 10},
            }
        '''
        categoryByVersion = {}  # type: Dict[int, Dict[str, Any]]
        allCategoryNames = set()
        for version, classInfo in \
                versionedCaches.getVersionedClassInfo(apiClsName).items():
            if classInfo is None:
                categoryInfo = {}
            else:
                categoryInfo = classInfo.get(category, {})
            categoryByVersion[version] = categoryInfo
            allCategoryNames.update(categoryInfo)

        allCategoryNames = sorted(allCategoryNames)

        categoryByName = OrderedDict()  # type: OrderedDict[str, OrderedDict[int, Any]]
        for name in allCategoryNames:
            byVersion = OrderedDict()  # type: OrderedDict[int, Any]
            for version, verEnums in categoryByVersion.items():
                byVersion[version] = verEnums.get(name)
            categoryByName[name] = byVersion
        return categoryByName

    @classmethod
    def assignmentFromVersionDict(cls, name, byVersion, noExistClause=None):
        # type: (str, Mapping[int, Any], Optional[Any]) -> Statement
        # check if the object exists and is the same for all versions...
        allVariations = set(byVersion.values())
        if len(allVariations) == 1:
            # make sure that value isn't None, indicating it didn't exist
            value = allVariations.pop()
            if value is None:
                raise ValueError("must exist in at least one version")
            # easy case...
            return Assignment(name, value)

        # ok, things differ. first check to see which versions it exists in
        if None in allVariations:
            # it was missing in at least some variations. make a conditional
            # for the versions it exists in, and a subconditional for assigning
            # the value
            existsVersions = []
            missingVersions = []
            for version, val in byVersion.items():
                if val is None:
                    missingVersions.append(version)
                else:
                    existsVersions.append(version)
            existsCondition = Conditional.conditionFromVersions(
                    existsVersions, missingVersions)
            existsByVersion = {ver : byVersion[ver]
                               for ver in existsVersions}
            conditions = [
                (existsCondition,
                 cls.assignmentFromVersionDict(name, existsByVersion)),
            ]

            if noExistClause:
                # add an else clause, if it doesn't exist
                conditions.append((True, noExistClause))
            return Conditional(conditions)

        # ok, it exists in all versions... now create branching conditional,
        # based on version...
        conditionPairs = []
        remainingVersions = sorted(byVersion)
        while remainingVersions:
            ver = remainingVersions.pop()
            currentValue = byVersion[ver]
            allVariations.remove(currentValue)
            if not allVariations:
                # this was the last value, can use an 'else' statement
                conditionPairs.append((True, Assignment(name, currentValue)))
                break

            trueVersions = [ver]
            # remove other versions with this value
            for i in range(len(remainingVersions) - 1, -1, -1):
                ver = remainingVersions[i]
                if byVersion[ver] == currentValue:
                    trueVersions.append(ver)
                    del remainingVersions[i]
            if allVariations and not remainingVersions:
                raise RuntimeError("oh noes - remainingVersions :{}".format(remainingVersions))
            conditionExpr = Conditional.conditionFromVersions(
                trueVersions, remainingVersions)
            assignment = Assignment(name, currentValue)
            conditionPairs.append((conditionExpr, assignment))
        return Conditional(conditionPairs)

    @classmethod
    def assignDefaultIfMissingFromVersionDict(cls, name, byVersion, default):
        # type: (str, Mapping[int, Any], Any) -> Conditional
        missingVersions = []
        foundVersions = []
        for ver, val in byVersion.items():
            if val is None:
                missingVersions.append(ver)
            else:
                foundVersions.append(ver)
        if not missingVersions:
            return None
        conditionExpr = Conditional.conditionFromVersions(
            missingVersions, foundVersions)
        assignment = Assignment(name, default)
        return Conditional([(conditionExpr, assignment)])

    @classmethod
    def symbolicVersionName(cls, versionNum):
        # type: (str) -> str
        if cls._symbolicVersions is None:
            cls._symbolicVersions = {}
            for name, val in inspect.getmembers(versions):
                if name.startswith('v') and isinstance(val, int):
                    cls._symbolicVersions[val] = name
        name = cls._symbolicVersions.get(versionNum)
        if name is not None:
            return 'versions.{}'.format(name)
        return versionNum


versionedCaches = VersionedCaches()


class Statement(object):
    indent = ' ' * 4

    def getLines(self):
        # type: () -> Iterable[str]
        raise NotImplementedError


class Assignment(Statement):
    def __init__(self, name, value):
        # type: (str, Any) -> None
        self.name = name
        self.value = value

    def getLines(self):
        # type: () -> Iterable[str]
        if self.name == '__melcmd__':
            return ['{} = staticmethod({})'.format(self.name, self.value)]
        else:
            return ['{} = {!r}'.format(self.name, self.value)]


class Method(object):
    TEMPLATES_BY_TYPE = {
        'query': 'querymethod.py',
        'edit': 'editmethod.py',
        'getattribute': 'getattribute.py',
        'api': 'apimethod.py',
    }

    def __init__(self, classname, pymelname, data=None, **kwargs):
        self.classname = classname
        self.pymelname = pymelname
        if data is None:
            self.data = {}
        else:
            self.data = dict(data)
        self.data.update(kwargs)
        if 'name' not in data:
            self.data['name'] = self.pymelname
        self.data['classname'] = self.classname

    def __getitem__(self, key):
        return self.data[key]

    def getLines(self):
        # type: () -> List[str]
        templateName = self.TEMPLATES_BY_TYPE[self.data['type']]
        template = env.get_template(templateName)
        text = template.render(method=self.data,
                               classname=self.classname)
        return text.splitlines()


class Conditional(Statement):
    def __init__(self, conditionValuePairs):
        # type: (List[Tuple[Union[str, Literal[True]], Union[Any, Statement]]]) -> None
        assert all(len(x) == 2 for x in conditionValuePairs)
        self.conditionValuePairs = list(conditionValuePairs)

    def getLines(self):
        # type: () -> Iterator[str]
        for i, (conditionExpr, value) in enumerate(self.conditionValuePairs):
            # first yield the if / elif
            if conditionExpr is True:
                # we allow this only as the final element, ie, as an "else"
                if i != len(self.conditionValuePairs) - 1:
                    raise ValueError(
                        "unconditional 'True' only allowed as last condition")
                if i == 0:
                    raise ValueError(
                        "unconditional 'True' not allowed as first condition")
                yield 'else:'
            elif i == 0:
                yield 'if {}:'.format(conditionExpr)
            else:
                yield 'elif {}:'.format(conditionExpr)

            # then yield the indented substatement
            if isinstance(value, Statement):
                for line in value.getLines():
                    yield self.indent + line
            else:
                yield self.indent + repr(value)

    @classmethod
    def conditionFromVersions(cls, versionsTrue, versionsFalse):
        versionsTrue = sorted(versionsTrue)
        versionsFalse = sorted(versionsFalse)
        if not versionsTrue:
            raise ValueError("must have at least one true version")
        if not versionsFalse:
            raise ValueError("must have at least one false version")
        if versionsTrue[-1] < versionsFalse[0]:
            # versionsTrue < versionsFalse
            # note that if
            #    versionsTrue = [201600, 201700]
            #    versionsFalse = [20180000]
            # we want 201703 to be True,  and 20180100 to be False,
            # so we compare < minFalse
            minFalse = VersionedCaches.symbolicVersionName(versionsFalse[0])
            return 'versions.current() < {}'.format(minFalse)
        elif versionsFalse[-1] < versionsTrue[0]:
            # versionsTrue > versionsFalse
            # note that if
            #    versionsTrue = [201700, 20180000]
            #    versionsFalse = [201600]
            # we want 201703 to be True,  and 201603 to be False,
            # so we compare >= minTrue
            minTrue = VersionedCaches.symbolicVersionName(versionsTrue[0])
            return 'versions.current() >= {}'.format(minTrue)
        elif all(x < versionsTrue[0] or x > versionsTrue[-1]
                 for x in versionsFalse):
            # now see if trueVersions forms a "continuous range", not interruped
            # by any false versions
            lowerBound = VersionedCaches.symbolicVersionName(versionsTrue[0])
            # since versionsFalse is sorted, the first one we find > maxTrue
            # is the one we want for comparison
            for val in versionsFalse:
                if val > versionsTrue[-1]:
                    upperBound = val
                    break
            return '{} <= versions.current() < {}'.format(
                lowerBound, upperBound)
        elif all(x < versionsFalse[0] or x > versionsFalse[-1]
                 for x in versionsTrue):
            # now see if falseVersions forms a "continuous range", not interruped
            # by any true versions
            lowerBound = VersionedCaches.symbolicVersionName(versionsFalse[0])
            # since versionsTrue is sorted, the first one we find > maxFalse
            # is the one we want for comparison
            for val in versionsTrue:
                if val > versionsFalse[-1]:
                    upperBound = val
                    break
            return 'versions.current() < {} or versions.current() >= {}'.format(
                lowerBound, upperBound)
        else:
            # this is unlikely, so I'll code it when / if it comes up...
            raise ValueError("haven't implemented interspersed versions yet")


class ModuleGenerator(object):
    def __init__(self):
        # keyed by module name:
        self.moduleLines = {}  # type: Dict[str, List[str]]
        # keyed by full class name (including module):
        self.classInsertLocations = {}  # type: Dict[str, int]
        # keyed by full class name (including module):
        self.classSuffixes = {}  # type: Dict[str, str]

    @staticmethod
    def getClassLocations(moduleName):
        # type: (str) -> List[Tuple[int, int, str]]
        """
        Inspect the passed module to determine the start and end line numbers
        for all classes defined within it.
        """
        moduleObject = sys.modules[moduleName]
        classLocations = []
        for clsname, clsobj in inspect.getmembers(moduleObject, inspect.isclass):
            try:
                print('.', end='', file=sys.__stdout__)
                clsmodule = inspect.getmodule(clsobj)
                if clsmodule != moduleObject:
                    continue
                start, end = _getSourceStartEndLines(clsobj)
            except IOError:
                # some classes, you won't be able to get source for - ignore
                # these
                continue

            classLocations.append((start, end, clsname))
        classLocations.sort()
        return classLocations

    def reset(self, module):
        # type: (str) -> None
        """
        Remove generated code from the given module and re-save the contents,
        and add the starting content to the moduleLines cache.
        """
        if module in self.moduleLines:
            raise RuntimeError("You probably don't want to reset an already-"
                               "reset or edited module")

        # this part can be very slow
        print("Finding all class locations for module %s" % module, file=sys.__stdout__)
        classLocations = self.getClassLocations(module)
        print(file=sys.__stdout__)

        source = _getModulePath(module)
        with open(source, 'r', newline='\n') as f:
            text = f.read()

        lines = text.split('\n')

        self.totalTrimmed = 0

        def doTrim(trimStart, trimEnd):
            # type: (int, int) -> None
            # see if we're in the middle of a class
            for clsStart, clsEnd, clsName in classLocations:
                clsStart -= self.totalTrimmed
                clsEnd -= self.totalTrimmed
                if clsStart > trimEnd:
                    break
                if clsStart < trimStart and trimEnd <= clsEnd:
                    # we're trimming inside a class - save the insert
                    # location, and also trim off any class definition AFTER
                    # the end marker, but store it away so it may be inserted
                    # later.
                    #
                    # We do this because any custom code which is AFTER the
                    # auto-generated class code will generally rely on
                    # members defined in the auto-generated code.  This means
                    # that it will fail when we import the module if we simply
                    # remove the sections inbetween the start / end markers.
                    #
                    # Thus, when resetting the module, we also trim off any
                    # portion in the class "suffix", so the class will import
                    # properly, then append it back at the "end"
                    clsSuffix = lines[trimEnd + 1:clsEnd + 1]
                    fullClsName = module + '.' + clsName
                    self.classInsertLocations[fullClsName] = trimStart
                    if clsSuffix:
                        self.classSuffixes[fullClsName] = clsSuffix
                    trimEnd = clsEnd
                    break
            _logger.debug("Trimming lines: (original range: {}-{} -"
                          " new range: {}-{})".format(
                trimStart + 1 + self.totalTrimmed,
                trimEnd + 1 + self.totalTrimmed,
                trimStart + 1, trimEnd + 1))
            lines[trimStart:trimEnd + 1] = []
            self.totalTrimmed += (trimEnd + 1 - trimStart)

        def trim(begin):
            # type: (int) -> Optional[int]
            start = None
            e = None
            for i, line in enumerate(lines[begin:]):
                i = begin + i
                e = i
                if start is None and  START_MARKER in line:
                    _logger.debug("Found start marked (original line: {} /"
                                  " new file line: {})".format(
                        i + self.totalTrimmed + 1, i + 1))
                    start = i

                elif END_MARKER in line:
                    _logger.debug("Found end marked (original line: {} /"
                                  " new file line: {})".format(
                        i + self.totalTrimmed + 1, i + 1))
                    assert start is not None
                    doTrim(start, i)
                    return start

            # end of lines
            if start is not None:
                doTrim(start, e)
            return None

        begin = 0
        while begin is not None:
            begin = trim(begin)

        del self.totalTrimmed

        lines.append(START_MARKER)

        print("writing reset %s" % source, file=sys.__stdout__)
        with open(source, 'w', newline='\n') as f:
            f.write('\n'.join(lines))
        self.moduleLines[module] = lines

    def _writeToModule(self, new, module):
        # type: (str, Union[types.ModuleType, str]) -> None
        """
        Write the `new` text to `module`, and save it into moduleLines cache.
        """
        if isinstance(module, types.ModuleType):
            moduleName = module.__name__
        else:
            moduleName = module
        lines = self.moduleLines[moduleName]

        # trim off last START_MARKER and anything after
        for i in range(len(lines) - 1, -1, -1):
            if lines[i] == START_MARKER:
                del lines[i:]
                break

        # by modifying the lines list, we ensure that any subsequent calls
        # have the updated lines
        if lines[-1] != '':
            lines.append('')
        lines.append(START_MARKER)
        lines.extend(new.split('\n'))

        path = _getModulePath(module)
        print("writing to", path)
        with open(path, 'w', newline='\n') as f:
            f.write('\n'.join(lines))

    def generateFunctions(self, moduleName, returnFunc=None):
        # type: (str, Optional[str]) -> None
        """
        Render templates for mel functions in `moduleName` into its module file.
        """
        module = sys.modules[moduleName]
        moduleShortName = moduleName.split('.')[-1]

        new = ''
        for funcName in factories.moduleCmds[moduleShortName]:
            if funcName in factories.nodeCommandList:
                new += functionTemplateFactory(funcName, module,
                                               returnFunc=returnFunc)
            else:
                new += functionTemplateFactory(funcName, module, returnFunc=None)
        self._writeToModule(new, module)

    def generateUIFunctions(self):
        # type: () -> None
        new = ''
        module = sys.modules['pymel.core.windows']
        moduleShortName = 'windows'

        for funcName in factories.uiClassList:
            # Create Class
            classname = util.capitalize(funcName)
            new += functionTemplateFactory(funcName, module,
                                           returnFunc='uitypes.' + classname,
                                           uiWidget=True)

        nonClassFuncs = set(factories.moduleCmds[moduleShortName]).difference(
            factories.uiClassList)
        for funcName in sorted(nonClassFuncs):
            new += functionTemplateFactory(funcName, module, returnFunc=None)

        new += '\nautoLayout.__doc__ = formLayout.__doc__\n'
        self._writeToModule(new, module)

    def generateTypes(self,
                      iterator,  # type: Iterable[Tuple[str, BaseGenerator]]
                      module,  # type: str
                      suffix=None  # type: Optional[str]
                      ):
        # type: (...) -> None
        """
        Utility to append type templates below their class within a given module.
        """
        source = _getModulePath(module)

        lines = self.moduleLines[module]

        # tally of additions made in middle of code
        offsets = {}

        def computeOffset(start):
            result = start
            for st, off in offsets.items():
                if st < start:
                    result += off
            return result

        for text, template in iterator:
            newlines = text.split('\n')
            if template.existingClass:
                # if there is an existing class, slot the new lines after the class

                # trailing newlines
                if newlines[-2:] == ['', '']:
                    newlines = newlines[:-2]

                if not newlines:
                    continue

                startline, endline = _getSourceStartEndLines(template.existingClass)

                clsName = module + '.' + template.existingClass.__name__
                insertLine = self.classInsertLocations.get(clsName, endline)
                offsetInsertLine = computeOffset(insertLine)
                classSuffix = self.classSuffixes.get(clsName)

                newlines = [START_MARKER] + newlines + [END_MARKER]
                if classSuffix:
                    newlines += classSuffix
                lines[offsetInsertLine:offsetInsertLine] = newlines
                offsets[insertLine] = len(newlines)
            else:
                lines += newlines

        text = '\n'.join(lines)

        if suffix:
            text += suffix

        print("writing to", source)
        with open(source, 'w', newline='\n') as f:
            f.write(text)


def getApiTemplateData(apiClass, apiMethodName, newName=None, proxy=True,
                       overloadIndex=None, deprecated=False, aliases=(),
                       properties=()):
    # type: (Type, str, str, bool, Optional[int], bool, Any, Any) -> Optional[dict]
    """
    Get data to provide to apimethod.py template.

    Regarding Undo
    --------------

    The API provides many methods which are pairs -- one sets a value
    while the other one gets the value.  the naming convention of these
    methods follows a fairly consistent pattern.  so what I did was
    determine all the get and set pairs, which I can use to automatically
    register api undo items:  prior to setting something, we first *get*
    it's existing value, which we can later use to reset when undo is
    triggered.

    This API undo is only for PyMEL methods which are derived from API
    methods.  it's not meant to be used with plugins.  and since it just
    piggybacks maya's MEL undo system, it won't get cross-mojonated.

    Take `MFnTransform.setTranslation`, for example. PyMEL provides a wrapped
    copy of this as `Transform.setTranslation`.
    when pymel.Transform.setTranslation is called, here's what happens in
    relation to undo:

        #. process input args, if any
        #. call MFnTransform.getTranslation() to get the current translation.
        #. append to the api undo queue, with necessary info to undo/redo
           later (the current method, the current args, and the current
           translation)
        #. call MFnTransform.setTranslation() with the passed args
        #. process result and return it


    Parameters
    ----------
    apiClass : Type
        the api class
    apiMethodName : str
        the name of the api method
    newName : str
        optionally provided if a name other than that of api method is desired
    proxy : bool
        If True, then __apimfn__ function used to retrieve the proxy class.
        If False, then we assume that the class being wrapped inherits from the
         underlying api class.
    overloadIndex : Optional[int]
        which of the overloaded C++ signatures to use as the basis of our
        wrapped function.

    Returns
    -------
    Optional[dict]
    """
    apiClassName = apiClass.__name__
    if not hasattr(apiClass, apiMethodName):
        # pre-2019 caches had some entries that should have been stripped
        # ('NO CACHE SUPPORT') when parsing, but weren't...
        return

    argHelper = factories.ApiArgUtil(apiClassName, apiMethodName, overloadIndex)

    pymelName = argHelper.getPymelName()

    if newName is None:
        newName = pymelName

    if not argHelper.canBeWrapped():
        return

    inArgs = argHelper.inArgs()
    outArgs = argHelper.outArgs()
    argList = argHelper.argList()
    unitType = argHelper.methodInfo['returnInfo'].get('unitType', None)
    returnType = argHelper.methodInfo['returnType']
    argInfo = argHelper.methodInfo['argInfo']

    inArgs = [arg for arg in inArgs
              if argInfo[arg]['type'] != 'MAnimCurveChange']

    # undoType controls how/if we get an UndoItem
    # ...and also whether we print a warning in the docs
    undoType = None
    getterArgHelper = argHelper.getGetterInfo()
    if getterArgHelper is not None:
        undoType = 'getter'
    numCurveChanges = 0
    for argName, argType, direction in argList:
        if argType == 'MAnimCurveChange' and direction == 'in':
            numCurveChanges += 1
    if numCurveChanges == 1:
        undoType = 'MAnimCurveChange'

    if argHelper.hasOutput():
        # query method ( getter )
        getterInArgs = []
    else:
        # edit method ( setter )
        if getterArgHelper is None:
            getterInArgs = []
        else:
            getterInArgs = getterArgHelper.inArgs()

    # format EnumValue defaults
    defaults = []
    for default in argHelper.getDefaults():
        if isinstance(default, util.EnumValue):
            defaults.append(str(default))
        else:
            defaults.append(default)

    # FIXME: replace with inspect.formatargspec
    signature = util.format_signature(['self'] + inArgs, defaults=defaults)

    def convertTypeArg(t):
        if isinstance(t, tuple):  # apiEnum
            return tuple(t)
        elif t is not None:
            return str(t)

    def getUnit(n):
        return argInfo[n].get('unitType', None)

    return {
        'type': 'api',
        'name': newName,
        'apiName': apiMethodName,
        'apiClass': apiClassName,
        'getter': getterArgHelper.getPymelName() if getterArgHelper else None,
        'overloadIndex': overloadIndex,
        'inArgs': ', '.join(inArgs),
        'outArgs': outArgs,
        'argList': [(name, convertTypeArg(typ), dir, getUnit(name))
                    for name, typ, dir in argList],
        'classmethod': argHelper.isStatic(),
        'getterInArgs': getterInArgs,
        'proxy': proxy,
        'undoType': undoType,
        'returnType': repr(convertTypeArg(returnType)) if returnType else None,
        'unitType': repr(str(unitType)) if unitType else None,
        'deprecated': deprecated,
        'signature': signature,
        'typeComment': makeTypeComment(argHelper.getAnnotations()),
        'aliases': aliases,
        'properties': properties,  # property aliases
    }


class BaseGenerator(object):
    """
    Generate code for a single class
    """

    classToMethodTypes = util.defaultdict(dict)  # type: Dict[str, Dict[str, str]]
    for method in methodNames(util.ProxyUnicode):
        classToMethodTypes['DependNode'][method] = 'str'

    def __init__(self, classname, existingClass, parentClasses, parentMethods,
                 moduleName):
        # type: (str, Type, Sequence[str], Iterable[str], Optional[str]) -> None
        self.classname = classname
        self.parentClassname = parentClasses[0] if parentClasses else None
        self.herited = parentMethods
        self.parentClasses = parentClasses
        self.existingClass = existingClass
        self.moduleName = moduleName
        self.attrs = {}  # type: Dict[str, Statement]
        self.methods = {}  # type: Dict[str, Method]

    def getTemplateData(self):
        # type: () -> None
        raise NotImplementedError

    def setDefault(self, key, value, directParentOnly=True):
        # type: (str, Union[Any, Statement], bool) -> None
        if isinstance(value, Statement):
            statement = value
        else:
            statement = Assignment(key, value)
        if directParentOnly:
            if self.existingClass is None or key not in self.existingClass.__dict__:
                self.attrs.setdefault(key, statement)
        else:
            if self.existingClass is None or not hasattr(self.existingClass, key):
                self.attrs.setdefault(key, statement)

    def assign(self, name, value, force=False):
        # type: (str, Any, bool) -> None
        if (force or self.existingClass is None
                or name not in self.existingClass.__dict__):
            self.attrs[name] = Assignment(name, value)

    def addMethod(self, name, methodType, data=None, **kwargs):
        # type: (str, str, Optional[Dict[str, Any]], **Any) -> None
        self.classToMethodTypes[self.classname][name] = methodType
        self.methods[name] = Method(self.classname, name, data=data, **kwargs)

    def addMelMethod(self, name, data=None, **kwargs):
        # type: (str, Optional[Dict[str, Any]], **Any) -> None
        # _logger.debug("Adding mel derived method %s.%s()" % (self.classname, name))
        return self.addMethod(name, 'mel', data=data, **kwargs)

    def addApiMethod(self, name, baseName, data=None, **kwargs):
        # type: (str, str, Optional[Dict[str, Any]], **Any) -> None
        overrideData = factories._getApiOverrideData(self.classname, baseName)
        melName = overrideData.get('melName')
        if melName:
            self.classToMethodTypes[self.classname][melName] = 'api'
        return self.addMethod(name, 'api', data=data, **kwargs)

    def render(self):
        # type: () -> Tuple[str, Set[str]]
        """
        Return the code and the names of the new methods created.
        """
        self.getTemplateData()

        methodNames = set(self.methods)
        if self.existingClass:
            # add methods that exist *directly* on the existing class
            methodNames.update(
                name for name, obj in self.existingClass.__dict__.items()
                if inspect.isfunction(obj))

        attrs = [self.attrs[k] for k in sorted(self.attrs,
                                               key=underscoreSortKey)]
        methods = [self.methods[k] for k in sorted(self.methods,
                                                   key=underscoreSortKey)]
        template = env.get_template('nodeclass.py')
        text = template.render(methods=methods, attrs=attrs,
                               classname=self.classname,
                               parents=self.parentClassname,
                               existing=self.existingClass is not None)

        return text, methodNames

    def addMelMethods(self):
        # type: () -> None
        """
        Add methods from MEL functions
        """
        #_logger.debug( 'BaseGenerator: %s' % classname )

        # ------------------------
        #   MEL Methods
        # ------------------------
        melCmdName, isInfoCmd = self.getMelCmd()

        try:
            helper = maintenance.buildutil.MelFunctionHelper(melCmdName,
                                                             self.moduleName)
        except KeyError:
            pass
            #_logger.debug("No MEL command info available for %s" % melCmdName)
        else:
            # FIXME: this old behavior implies that sometimes we used unwrapped
            #  commands, but it's unclear how this would happen.  Was it a
            #  load order thing? Confirm on old version.
            # pmSourceFunc = False
            # try:
            #     cmdModule = __import__('pymel.core.' + cmdInfo['type'], globals(), locals(), [''])
            #     func = getattr(cmdModule, melCmdName)
            #     pmSourceFunc = True
            # except (AttributeError, TypeError):
            #     func = getattr(pmcmds, melCmdName)

            pmSourceFunc = True
            cmdPath = '%s.%s' % (helper.info['type'], melCmdName)

            # FIXME: add documentation
            # classdict['__doc__'] = util.LazyDocString((newcls, self.docstring, (melCmdName,), {}))

            self.assign('__melcmd__', cmdPath)
            self.assign('__melcmdname__', melCmdName)
            self.assign('__melcmd_isinfo__', isInfoCmd)

            # base set of disallowed methods (for MEL)
            filterAttrs = {'name', 'getName', 'setName'}
            # already created attributes for this class:
            filterAttrs.update(self.attrs.keys())
            # already created methods for this class:
            filterAttrs.update(self.methods.keys())
            # filter methods on parent classes, if they're not from MEL
            #   we always override mel-generated flags, as there's no guarantee
            #   that, ie, rowLayout -dragCallback won't have
            #   some extra functionality as compared to layout -dragCallback.
            filterAttrs.update(x for x in self.herited
                               if self.methodType(x) not in ('str', 'mel'))
            # # instead, we only filter out a specific set of methods, if they're
            # # implemented on ancestors
            # filterAttrs.update({'getParent'}.intersection(self.herited))

            def getMelName(methodName):
                # type: (str) -> Optional[str]
                bridgeInfo = factories._getApiOverrideData(self.classname,
                                                           methodName)
                melName = bridgeInfo.get('melName', methodName)

                methodType = self.methodType(melName)
                if methodType == 'api':
                    return None
                if melName in filterAttrs:
                    return None
                if (hasattr(self.existingClass, melName)
                        and methodType not in ('mel', 'str')):
                    return None

                if not self.isMelEnabled(methodName):
                    return None
                return melName

            for flag, flagInfo in helper.info['flags'].items():
                # don't create methods for query or edit, or for flags which
                # only serve to modify other flags
                if flag in ['query', 'edit'] or 'modified' in flagInfo:
                    continue

                if 'modes' not in flagInfo:
                    continue

                # flags which are not in maya docs will have not have a
                # modes list unless they have passed through testNodeCmds
                # continue
                modes = flagInfo['modes']

                # query command
                if 'query' in modes:
                    methodName = 'get' + util.capitalize(flag)
                    methodName = getMelName(methodName)

                    if methodName:
                        # as a rule of thumb, using the flag type as the
                        # result holds true if the flag supports both query/edit
                        if 'edit' in modes:
                            resultType = helper.getFlagType(flagInfo, asResult=True)
                        else:
                            resultType = 'Any'
                        annotations = {
                            'result': resultType
                        }

                        self.addMelMethod(methodName, {
                            'command': melCmdName,
                            'type': 'query',
                            'flag': flag,
                            'returnFunc': (importableName(flagInfo['args'])
                                           if flagInfo.get('resultNeedsCasting', False)
                                           else None),
                            'func': cmdPath,
                            'typeComment': makeTypeComment(annotations),
                        })

                # edit command
                if 'edit' in modes or (isInfoCmd and 'create' in modes):
                    # if there is a corresponding query we use the 'set' prefix.
                    if 'query' in modes:
                        methodName = 'set' + util.capitalize(flag)
                    # if there is not a matching 'set' and 'get' pair, we
                    # use the flag name as the method name
                    else:
                        methodName = flag
                    methodName = getMelName(methodName)

                    if methodName:
                        # FIXME: shouldn't we be able to use the wrapped
                        #  pymel command, which is already fixed?
                        # FIXME: the 2nd argument is wrong, so I think this
                        #  is broken
                        # fixedFunc = fixCallbacks(func, melCmdName)
                        annotations = {
                            'args': [helper.getFlagType(flagInfo, asResult=False), '**Any'],
                            'result': 'None'
                        }

                        self.addMelMethod(methodName, {
                            'command': melCmdName,
                            'type': 'edit',
                            'flag': flag,
                            'func': cmdPath,
                            'typeComment': makeTypeComment(annotations),
                        })

    def getMelCmd(self):
        # type: () -> Tuple[str, bool]
        """
        Retrieves the name of the mel command the generated class wraps, and
        whether it is an info command.

        Intended to be overridden in derived generators.
        """
        raise NotImplementedError

    def classnameMRO(self):
        # type: () -> Iterator[str]
        yield self.classname
        for parent in self.parentClasses:
            yield parent

    def methodType(self, methodName):
        # type: (str) -> Optional[str]
        for classname in self.classnameMRO():
            methodType = self.classToMethodTypes[classname].get(methodName)
            if methodType is not None:
                return methodType
        return None

    def isMelEnabled(self, methodName, default=True):
        # type: (str, bool) -> bool
        for parentClass in self.classnameMRO():
            overrideData = factories._getApiOverrideData(parentClass,
                                                         methodName)
            melEnabled = overrideData.get('melEnabled')
            if melEnabled is not None:
                # if we ever get any result for melEnabled, before we find an
                # api-enabled result, then that takes precedence
                return melEnabled
            apiEnabled = overrideData.get('enabled')
            if apiEnabled is not None:
                return not apiEnabled
        if methodName in factories.EXCLUDE_METHODS:
            return False
        return default

    def isApiEnabled(self, methodName, default=True):
        # type: (str, bool) -> bool
        for parentClass in self.classnameMRO():
            overrideData = factories._getApiOverrideData(parentClass,
                                                         methodName)
            apiEnabled = overrideData.get('enabled')
            if apiEnabled is not None:
                return apiEnabled
        if methodName in factories.EXCLUDE_METHODS:
            return False
        return default

    def docstring(self, melCmdName):
        # type: (str) -> str
        try:
            cmdInfo = factories.cmdlist[melCmdName]
        except KeyError:
            #_logger.debug("No MEL command info available for %s" % melCmdName)
            classdoc = ''
        else:
            factories.loadCmdDocCache()
            classdoc = 'class counterpart of mel function `%s`\n\n%s\n\n' % \
                       (melCmdName, cmdInfo['description'])
        return classdoc


# FIXME: don't inherit here, treat as a Mixin
class ApiMethodsGenerator(BaseGenerator):

    VALID_NAME = re.compile('[a-zA-Z_][a-zA-Z0-9_]*$')
    proxy = True

    def __init__(self, classname, existingClass, parentClasses,
                 parentMethods, parentApicls, childClasses=(), moduleName=None):
        # type: (str, Type, Iterable[str], Iterable[str], Optional[Type], Iterable[str], Optional[str]) -> None
        super(ApiMethodsGenerator, self).__init__(classname, existingClass,
                                                  parentClasses, parentMethods,
                                                  moduleName=moduleName)
        self.parentApicls = parentApicls
        self.existingClass = existingClass
        self.childClasses = childClasses
        self.apicls = self.getApiCls()
        self.overrideErrors = []

    def methodWasFormerlyEnabled(self, pymelName):
        # type: (str) -> bool
        """
        previous versions of pymel erroneously included disabled methods on
        some child classes which possessed the same apicls as their parent.
        We will deprecate them in order to allow users to transition.
        """
        # this is one place we don't need to check recursively up the chain,
        # since it was a one-time thing we added exactly where needed
        overrideData = factories._getApiOverrideData(self.classname, pymelName)
        return overrideData.get('backwards_compatibility_enabled', False)

    def getApiCls(self):
        # type: () -> Optional[Type]
        if self.existingClass is not None:
            try:
                return self.existingClass.__dict__['__apicls__']
            except KeyError:
                pass

    def getApiClsByVersion(self):
        # type: () -> Dict[int, Type]
        if self.apicls is None:
            return {}
        apiTypeName = factories._apiCacheInst.getMfnClsToApiType(self.apicls)
        versionedApiTypes = versionedCaches.getAllApiTypesToApiEnums()
        byVersion = OrderedDict()
        for version, apiTypesToApiEnums in versionedApiTypes.items():
            if apiTypeName in apiTypesToApiEnums:
                byVersion[version] = self.apicls
            else:
                byVersion[version] = None
        return byVersion

    def addEnums(self):
        # type: () -> None
        enumsByNameVersion = versionedCaches.getVersionedClassCategory(
            self.apicls.__name__, 'pymelEnums')
        for enumName, byVersion in enumsByNameVersion.items():
            self.attrs[enumName] = VersionedCaches.assignmentFromVersionDict(
                enumName, byVersion)

    def _hasExistingImplementation(self, apiName, pymelName):
        # type: (str, str) -> bool
        # First, check to see if there's a manual override of this method
        # on the existing class.
        if (self.existingClass is not None
                and pymelName in self.existingClass.__dict__):
            return True

        # if we've already made a method for THIS class
        if pymelName in self.methods:
            return True

        if pymelName not in self.herited:
            return False

        # ok, it was in the list of herited methods - check if it's an
        # explicit override on this apicls
        if apiName not in self.apicls.__dict__:
            return False

        # If it's inherited from ProxyUnicode, we still want to override it
        if self.methodType(pymelName) == 'str':
            return False

        # Even if a method is already in a super-class, we still may
        # want to wrap it, if it's an explicit override of the the
        # parent class's method. For instance, suppose we have
        # MFnTriceratops which inherits from MFnDinosaur, both of which
        # implement an .isAKiller() method.  (MFnDinosaur.isAKiller()
        # returns True if the dinosaur is a carnivore, but
        # MFnTriceratops overrides that behavior to return True if it's
        # killed a TRex in one-on-one combat!) When wrapping
        # pm.nt.Triceratops, we may still want to wrap
        # MFnTriceratops.isAKiller, even though we already have an
        # implementation from pm.nt.Dinosaur / MFnDinosaur.

        # Of course, it's also possible that the two functions represent
        # two totally different things - maybe
        # MFnTriceratops.isAKiller() returns True iff the dino in
        # question is a member of the rock band, "The Killers". (Which
        # everyone knows has a strict Triceratops-only-members rule.)
        # If this is the case, we may want to provide an alternate name
        # for the new method, instead of override the parent
        # implementation, so both methods are accessible.  These
        # overrides come up infrequently enough that we require the user
        # to manually specify what they want when it happens - either
        # by setting the override to enable=False (in which case it will
        # use the inherited parent implementation), override=True (in
        # which case it will re-wrap and override the parent), or by providing
        # a rename with, ie, useName='isMemberOfKillersBand'.

        # Note: the only current place this happens is with
        # MFnDependencyNode.isLocked / MFnReference.isLocked, so this
        # code is more about flagging any future occurrences of this.

        # check if we've explicitly flagged this as an override
        overrideData = factories._getApiOverrideData(self.classname, pymelName)
        if overrideData.get('override'):
            return False

        # We don't know what to do - raise an error, ask user to decide
        methodsToBridgeKeys = {
            '{}.{}'.format(self.apicls.__name__, apiName): (self.classname,
                                                            pymelName),
        }
        raise NewOverrideError(methodsToBridgeKeys)

    def addApiMethods(self):
        # type: () -> None
        """
        Add methods from API functions
        """

        self.removeAttrs = []

        _logger.info('%s: %s: %s' % (self.__class__, self.classname, self.apicls))

        if self.apicls is None:
            return

        if self.apicls.__name__ not in factories.apiClassNamesToPyNodeNames:
            factories.apiClassNamesToPyNodeNames[self.apicls.__name__] = self.classname

        classShouldBeSkipped = False
        if inspect.isclass(self.parentApicls) and issubclass(self.parentApicls,
                                                             self.apicls):
            # check if our apiCls is same as parentApicls, OR is a parent
            # it may seem odd / impossible for our apicls to be the parent of
            # the parentApicls - we'd be going from more specific to less
            # specific. However, in same cases due to bugs in maya, a given node
            # may not support all of it's parent node's MFns / methods... so
            # we would need to "roll back" it's MFn

            # If it is the same or a subclss, the methods are already
            # handled... so we SHOULD skip skip this class, and return
            # immediately. However, "old" pymel did not have this check,
            # so instead we continue, but mark ALL methods that we end up
            # wrapping here as deprecated
            classShouldBeSkipped = True

            # FIXME: should this be extended to check all parent classes?
            # FIXME: assert that there is nothing explicit in the mel-api bridge
            # return

        # if not proxy and apicls not in self.bases:
        #     #_logger.debug("ADDING BASE %s" % self.attrs['apicls'])
        #     bases = self.bases + (self.attrs['apicls'],)
        try:
            classInfo = factories.apiClassInfo[self.apicls.__name__]
        except KeyError:
            _logger.info("No api information for api class %s" % (self.apicls.__name__))
        else:
            # -----------------------
            # API Wrap
            # -----------------------

            # FIXME:
            # Find out methods herited from other bases than apicls to avoid
            # unwanted overloading
            # herited = {}
            # for base in bases:
            #     if base is not apicls:
            #         # basemro = inspect.getmro(base)
            #         for attr in dir(base):
            #             if attr not in herited:
            #                 herited[attr] = base

            ##_logger.debug("Methods info: %(methods)s" % classInfo)

            # Class Methods

            # iterate over the methods so that we get all non-deprecated
            # methods first
            # This is because, if two api methods map to the same pymel
            # method name, then the first one "wins" - and we want to prefer
            # non-deprecated.
            def non_deprecated_methods_first():

                deprecated = []
                for methodName, info in classInfo['methods'].items():

                    try:
                        basePymelName = classInfo.get('pymelMethods', {})[methodName]
                        self.removeAttrs.append(methodName)
                    except KeyError:
                        basePymelName = methodName
                    pymelName, overrideData, renamed = factories._getApiOverrideNameAndData(
                        self.classname, basePymelName)

                    # if 'addAttribute' in (pymelName, basePymelName, methodName):
                    #     print self.classname, pymelName, basePymelName, methodName, renamed, overrideData

                    if not self.VALID_NAME.match(pymelName) or keyword.iskeyword(pymelName):
                        print("Invalid name", self.classname, methodName, info)
                        continue

                    overloadIndex = overrideData.get('overloadIndex', 0)

                    if overloadIndex is None:
                        continue

                    # make sure we know how to deal with all args
                    unknownType = False
                    for argName, argType in info[overloadIndex]['types'].items():
                        if isinstance(argType, tuple):
                            # it's an enum, check next arg
                            continue
                        if not factories.ApiTypeRegister.isRegistered(argType):
                            # TODO: either handle or ignore optional args
                            # we don't know how to handle

                            # we currently wrap some functions where we don't
                            # know how to handle the args (ie,
                            # MFnMesh.createColorSetWithName - wrapped as
                            # create colorSet - where we don't know how to
                            # handle the MDGModifier arg, but it's optional.

                            # we should handle this properly, by either dropping
                            # the arg from our pymel wrap, or adding support
                            # for that arg type, but for now, to avoid
                            # backward compatibilities, I'm preserving old
                            # behavior
                            if argName not in info[overloadIndex].get('defaults', {}):
                                unknownType = True
                                break
                    if unknownType:
                        continue

                    aliases = overrideData.get('aliases', [])
                    properties = overrideData.get('properties', [])
                    yieldTuple = (methodName, pymelName, basePymelName,
                                  overloadIndex, aliases, properties)

                    def handleBackwardsCompatibilityFix():
                        '''check to see if it was formerly (erroneously) enabled
                        in older versions of pymel.

                        if so, we keep it, but mark it deprecated'''
                        wasEnabled = self.methodWasFormerlyEnabled(basePymelName)
                        if wasEnabled:
                            deprecationCall = "@_f.deprecated"
                            if isinstance(wasEnabled, basestring):
                                deprecationCall += "({!r})".format(wasEnabled)
                            _logger.info(
                                "{}.{}: Adding disabled method as deprecated."
                                " Used by older versions of pymel".format(
                                    self.classname, pymelName))
                            deprecated.append(yieldTuple + (deprecationCall,))
                        return wasEnabled

                    if classShouldBeSkipped:
                        # if we're doing a class which "should" be skipped,
                        # the ONLY reason we should wrap it is to deal
                        # with backwards-compatibility enabled methods
                        handleBackwardsCompatibilityFix()
                    elif not self.isApiEnabled(basePymelName):
                        if not handleBackwardsCompatibilityFix():
                            _logger.debug(
                                "{}.{} has been manually disabled, skipping"
                                .format(self.classname, pymelName))
                    elif info[overloadIndex].get('deprecated', False):
                        deprecated.append(yieldTuple + ("@_f.maya_deprecated",))
                    else:
                        yield yieldTuple + (False,)

                for yieldTuple in deprecated:
                    yield yieldTuple

            for (methodName, pymelName, basePymelName, overloadIndex, aliases,
                 properties, deprecated) \
                    in non_deprecated_methods_first():
                assert isinstance(pymelName, str), \
                    "%s.%s: %r is not a valid name" % (self.classname, methodName, pymelName)

                try:
                    if not self._hasExistingImplementation(methodName, pymelName):
                        data = getApiTemplateData(
                            self.apicls, methodName, newName=pymelName,
                            proxy=self.proxy, overloadIndex=overloadIndex,
                            deprecated=deprecated, aliases=aliases,
                            properties=properties)
                        if data:
                            self.addApiMethod(pymelName, basePymelName, data)
                except NewOverrideError as e:
                    self.overrideErrors.append(e)
                    continue

            # no reason to re-add enums for backward compatibility
            if not classShouldBeSkipped:
                self.addEnums()


class ApiDataTypesGenerator(ApiMethodsGenerator):
    """
    M* data classes
    """

    proxy = False

    def getApiCls(self):
        # type: () -> Optional[Type]
        if self.existingClass is not None:
            try:
                return self.existingClass.__dict__['apicls']
            except KeyError:
                pass

    def getTemplateData(self):
        # type: () -> None
        # first populate API methods.  they take precedence.
        self.setDefault('__slots__', ())
        self.addApiMethods()

    def addApiMethods(self):
        # type: () -> None
        """
        Add methods from API functions
        """
        super(ApiDataTypesGenerator, self).addApiMethods()

        if self.removeAttrs:
            _logger.info("%s: removing attributes %s" % (self.classname, self.removeAttrs))

        if self.apicls is None:
            return

        if self.removeAttrs:
            # because datatype classes inherit from their API classes, if a
            # method is renamed, we must also remove the inherited API method.
            self.addApiMethod('__getattribute__', '__getattribute__', {
                'type': 'getattribute',
                'removeAttrs': _setRepr(self.removeAttrs),
            })

        # if we imported using old, non-template-generated maya, then
        # it may have fixed the setattr bug on the OpenMaya class itself - undo
        # this!
        setattr = self.apicls.__dict__.get('__setattr__')
        if setattr is not None and getattr(setattr, '__name__', None) == 'apiSetAttrWrap':
            internal_vars = dict(zip(setattr.__code__.co_freevars,
                                     (x.cell_contents for x in
                                      setattr.__closure__)))
            origSetAttr = internal_vars['origSetAttr']
            self.apicls.__setattr__ = origSetAttr

        # shortcut for ensuring that our class constants are the same type as
        # the class we are creating
        def makeClassConstant(attr):
            print("make constant", self.classname, self.existingClass, attr)
            return Literal('_f.ClassConstant(%r)' % list(attr))

        # -----------------------
        # Class Constants
        # -----------------------
        # build some constants on the class
        constant = {}
        # constants in class definition will be converted from api class to created class
        for name, attr in self.existingClass.__dict__.items():
            # to add the wrapped api class constants as attributes on the wrapping class,
            # convert them to own class
            if isinstance(attr, self.apicls):
                if name not in constant:
                    constant[name] = Assignment(name, makeClassConstant(attr))
        # we'll need the api class dict to automate some of the wrapping
        # can't get argspec on SWIG creation function of type built-in or we
        # could automate more of the wrapping
        # defining class properties on the created class
        for name, attr in inspect.getmembers(self.apicls):
            # to add the wrapped api class constants as attributes on the wrapping class,
            # convert them to own class
            if isinstance(attr, self.apicls):
                if name not in constant:
                    constant[name] = Assignment(name, makeClassConstant(attr))
        # FIXME:
        # update the constant dict with herited constants
        # mro = inspect.getmro(self.existingClass)
        # for parentCls in mro:
        #     if isinstance(parentCls, MetaMayaTypeGenerator):
        #         for name, attr in parentCls.__dict__.iteritems():
        #             if isinstance(attr, MetaMayaTypeGenerator.ClassConstant):
        #                 if not name in constant:
        #                     constant[name] = makeClassConstant(attr.value)

        self.attrs.update(constant)


class NodeTypeGenerator(ApiMethodsGenerator):
    """
    MFn* classes which correspond to a node type
    """

    def __init__(self, classname, existingClass, parentClasses,
                 parentMethods, parentApicls, childClasses=(), mayaType=None,
                 moduleName=None):
        # type: (str, Type, Iterable[str], Iterable[str], Type, Iterable[str], str, Optional[str]) -> None
        # mayaType must be set first
        self.mayaType = mayaType
        super(NodeTypeGenerator, self).__init__(
            classname, existingClass, parentClasses, parentMethods,
            parentApicls, childClasses, moduleName=moduleName)

    def render(self):
        # type: () -> Tuple[str, Set[str]]
        # we conditionally assign a default 'None' to _api.MFnClassName
        # if the MFn doesn't exist in a given version of maya. We do this
        # because it will be used both to assign to __apicls__, and in various
        # addApiDocs calls, ie:
        #    @_f.addApiDocs(_api.MFnStandardSurfaceShader, 'base')
        # We could put the entire class behind an "if" branch, but that would
        # change the indentation depending on whether the class was available
        # in all versions of maya, which would both look ugly, and result in
        # big diffs.
        #
        # So instead we insert a statement like this just before the class is
        # defined:
        #    if versions.current() < versions.v2020:
        #        _api.MFnClassName = None

        text, methodNames = super(NodeTypeGenerator, self).render()

        if self.apicls is not None and self.apicls is not self.parentApicls:
            # _api.MFnSomeClass may not exist in all versions of maya we
            # support... so we need to do some versioned conditionals
            apiClsByVersion = self.getApiClsByVersion()
            conditionalAssignment = \
                VersionedCaches.assignDefaultIfMissingFromVersionDict(
                                '_api.' + self.apicls.__name__, apiClsByVersion,
                                Literal('None'))
            if conditionalAssignment:
                lines = list(conditionalAssignment.getLines())
                lines.append('')
                lines.append('')
                lines.append(text)
                text = '\n'.join(lines)
        return text, methodNames

    def getApiCls(self):
        if self.mayaType is not None:
            return factories.toApiFunctionSet(self.mayaType)

        return super(NodeTypeGenerator, self).getApiCls()

    def getTemplateData(self):
        # type: () -> None
        self.setDefault('__slots__', ())

        self.assign('__melnode__', self.mayaType)

        if self.apicls is not None and self.apicls is not self.parentApicls:
            self.assign('__apicls__', Literal('_api.' + self.apicls.__name__))

        # FIXME:
        isVirtual = False
        # isVirtual = '_isVirtual' in self.attrs or any(hasattr(b, '_isVirtual')
        #                                              for b in self.bases)
        # if nodeType is None:
        #     # check for a virtual class...
        #     if isVirtual:
        #         for b in bases:
        #             if hasattr(b, '__melnode__'):
        #                 nodeType = b.__melnode__
        #                 break
        #         else:
        #             raise RuntimeError("Could not determine mel node type for virtual class %r" % self.classname)
        #     else:
        #         # not a virtual class, just use the classname
        #         nodeType = util.uncapitalize(self.classname)
        #     self.assign('__melnode__', nodeType)

        from pymel.core.nodetypes import mayaTypeNameToPymelTypeName, \
            pymelTypeNameToMayaTypeName

        # mapping from pymel type to maya type should always be made...
        oldMayaType = pymelTypeNameToMayaTypeName.get(self.classname)
        if oldMayaType is None:
            pymelTypeNameToMayaTypeName[self.classname] = self.mayaType
        elif oldMayaType != self.mayaType:
            _logger.raiseLog(_logger.WARNING,
                             'creating new pymel node class %r for maya node '
                             'type %r, but a pymel class with the same name '
                             'already existed for maya node type %r' % (
                                 self.classname, self.mayaType, oldMayaType))

        # mapping from maya type to pymel type only happens if it's NOT a
        # virtual class...
        if not isVirtual:
            oldPymelType = mayaTypeNameToPymelTypeName.get(self.mayaType)
            if oldPymelType is None:
                mayaTypeNameToPymelTypeName[self.mayaType] = self.classname
            elif oldPymelType != self.classname:
                _logger.raiseLog(_logger.WARNING,
                                 'creating new pymel node class %r for maya node '
                                 'type %r, but there already existed a pymel'
                                 'class %r for the same maya node type' % (
                                     self.classname, self.mayaType, oldPymelType))

        factories.addMayaType(self.mayaType)

        # first populate API methods.  they take precedence.
        self.addApiMethods()
        # next, populate MEL methods
        self.addMelMethods()

        # FIXME:
        # PyNodeType = super(ApiMethodsGenerator, self).render()
        # ParentPyNode = [x for x in bases if issubclass(x, util.ProxyUnicode)]
        # factories.addPyNodeType(PyNodeType, ParentPyNode)
        # return PyNodeType

    def getMelCmd(self):
        # type: () -> Tuple[str, bool]
        """
        Retrieves the name of the mel command for the node that the generated
        class wraps, and whether it is an info command.

        Derives the command name from the mel node name - so '__melnode__' must
        already be set in classdict.
        """
        nodeCmd = None
        if self.existingClass is not None:
            nodeCmd = getattr(self.existingClass, '__melcmdname__', None)
        if nodeCmd:
            isInfoCmd = getattr(self.existingClass, '__melcmd_isinfo__', False)
        else:
            isInfoCmd = False
            try:
                nodeCmd = factories.cmdcache.nodeTypeToNodeCommand[self.mayaType]
            except KeyError:
                try:
                    nodeCmd = factories.nodeTypeToInfoCommand[self.mayaType]
                    isInfoCmd = True
                except KeyError:
                    nodeCmd = self.mayaType
        return nodeCmd, isInfoCmd


class ApiUnitsGenerator(ApiDataTypesGenerator):

    def getTemplateData(self):
        # type: () -> None
        self.addEnums()


class ApiTypeGenerator(ApiMethodsGenerator):
    """
    MFn* classes which do not correspond to a node type
    """
    def getTemplateData(self):
        # type: () -> None
        self.setDefault('__slots__', ())

        if self.apicls is not None and self.apicls is not self.parentApicls:
            self.setDefault('__apicls__',
                            Literal('_api.' + self.apicls.__name__))

        # first populate API methods.  they take precedence.
        self.addApiMethods()


class UITypeGenerator(BaseGenerator):

    """
    A metaclass for creating classes based on on a maya UI type/command.
    """

    def getTemplateData(self):
        # type: () -> None
        self.setDefault('__slots__', ())
        # If the class explicitly gives it's mel ui command name, use that -
        # otherwise, assume it's the name of the PyNode, uncapitalized
        self.setDefault('__melui__', util.uncapitalize(self.classname))

        # TODO: implement a option at the cmdlist level that triggers listForNone
        # TODO: create labelArray for *Grp ui elements, which passes to the
        #  correct arg ( labelArray3, labelArray4, etc ) based on length of
        #  passed array
        self.addMelMethods()

    def getMelCmd(self):
        # type: () -> Tuple[str, bool]
        cmd = getattr(self.existingClass, '__melui__', None)
        if not cmd:
            # we're assuming that __melui__ isn't a conditional... for now, only
            # enums should be conditional.
            cmd = self.attrs['__melui__'].value
        return cmd, False


def getPyNodeGenerator(mayaType, existingClass, pyNodeTypeName, parentMayaTypes,
                       childMayaTypes, parentMethods, parentApicls):
    # type: (str, Optional[type], str, List[str], Any, Any, Any) -> NodeTypeGenerator
    """
    create a PyNode type for a maya node.

    Parameters
    ----------
    mayaType : str
    parentMayaTypes : List[str]

    Returns
    -------
    NodeTypeGenerator
    """
    import pymel.core.nodetypes as nt

    def getCachedPymelType(nodeType):
        # type: (str) -> str
        result = nt.mayaTypeNameToPymelTypeName.get(nodeType)
        if result is None:
            # FIXME:
            # _logger.raiseLog(_logger.WARNING,
            #                  'trying to create PyNode for maya type %r, but could'
            #                  ' not find a registered PyNode for parent type %r' % (
            #                      mayaType, parentMayaType))
            # unicode is not liked by metaNode
            return str(util.capitalize(nodeType))
        else:
            return result

    parentPymelTypes = [getCachedPymelType(p) for p in parentMayaTypes]
    childPymelTypes = [getCachedPymelType(c) for c in childMayaTypes]

    return NodeTypeGenerator(pyNodeTypeName, existingClass,
                             parentPymelTypes, parentMethods, parentApicls,
                             childPymelTypes, mayaType,
                             moduleName='pymel.core.nodetypes')


def iterApiTypeText():
    # type: () -> Iterator[Tuple[str, ApiTypeGenerator]]
    """generate code for MFn types in pymel.core.general"""
    import pymel.core.general
    # FIXME: handle herited methods
    types = [
        pymel.core.general.Attribute,
        pymel.core.general.AttributeSpec,
        pymel.core.general.MeshVertex,
        pymel.core.general.MeshEdge,
        pymel.core.general.MeshFace,
        pymel.core.general.NurbsCurveCV,
    ]
    for cls in types:
        parentMethods = methodNames(cls)
        parentApicls = None
        parentPymelTypes = [x.__name__ for x in cls.mro()[1:]]
        template = ApiTypeGenerator(
            cls.__name__, cls, parentPymelTypes, parentMethods, parentApicls)

        text, methods = template.render()
        yield text, template


def dependentOrder(classes, seen=None):
    if seen is None:
        seen = set()
    for cls in classes:
        if cls in seen:
            continue

        seen.add(cls)
        for parent in dependentOrder(cls.__bases__, seen):
            yield parent
        yield cls


def iterModuleDataClasses(module):
    # type: (types.ModuleType) -> Iterator[Type]
    classes = [obj for name, obj in sorted(
                    inspect.getmembers(module,
                                       inspect.isclass))]
    for cls in dependentOrder(classes):
        if hasattr(cls, 'apicls') and cls.__module__ == module.__name__:
            yield cls


def iterModuleApiDataTypeText(module):
    # type: (types.ModuleType) -> Iterator[Tuple[str, Union[ApiDataTypesGenerator, ApiUnitsGenerator]]]
    import pymel.core.datatypes

    heritedMethods = {}

    for obj in iterModuleDataClasses(module):
        cls = obj
        parentApicls = None
        parentMethods = set()
        isIgnoredClass = lambda x: x in (obj.apicls, object)
        parentPymelTypes = [x.__name__ for x in cls.mro()[1:]
                            if not isIgnoredClass(x)]
        for parentCls in cls.__bases__:
            if isIgnoredClass(parentCls):
                continue
            thisParentMethods = heritedMethods.get(parentCls.__name__)
            if thisParentMethods is None:
                thisParentMethods = methodNames(parentCls)
                heritedMethods[parentCls.__name__] = thisParentMethods
            parentMethods.update(thisParentMethods)

        # we check for type registry metaclass because some datatypes (Time, Distance)
        # don't have a metaclass (and never did).  I'm not sure if that was a
        # mistake, but adding the metaclass causes errors.
        if issubclass(type(obj), factories.MetaMayaTypeRegistry):
            templateGenerator = ApiDataTypesGenerator
        elif issubclass(obj, pymel.core.datatypes.Unit):
            templateGenerator = ApiUnitsGenerator
        else:
            templateGenerator = None

        if templateGenerator:
            template = templateGenerator(
                cls.__name__, cls, parentPymelTypes, parentMethods, parentApicls,
                moduleName=module.__name__)
            text, methods = template.render()
            yield text, template
        else:
            methods = set()

        heritedMethods[cls.__name__] = parentMethods.union(methods)


def iterApiDataTypeText():
    # type: () -> Iterator[Tuple[str, Union[ApiDataTypesGenerator, ApiUnitsGenerator]]]
    """generate code for pymel.core.datatypes"""
    import pymel.core.datatypes
    for item in iterModuleApiDataTypeText(pymel.core.datatypes):
        yield item


def iterPyNodeText():
    # type: () -> Iterator[Tuple[str, BaseGenerator]]
    """generate code for pymel.core.nodetypes"""
    import pymel.core.general
    import pymel.core.nodetypes as nt

    # Generate Classes
    heritedMethods = {
        'general.PyNode': methodNames(pymel.core.general.PyNode)
    }
    apiClasses = {
        'general.PyNode': None
    }

    # the children in factories.nodeHierarchy is not complete, but the parents
    # are.
    realChildren = defaultdict(set)
    if versions.current() < versions.v2019:
        # for caches before this, we didn't sort the node hierarchy, so we need
        # to do it here, to get easily comparable / diffable results
        import pymel.util.trees as trees

        parentDict = {node: parents[0] for node, parents, children in
                      factories.nodeHierarchy if parents}
        nodeHierarchyTree = trees.treeFromDict(parentDict)
        nodeHierarchyTree.sort()
        newHier = [(x.value, tuple(y.value for y in x.parents()),
                    tuple(y.value for y in x.childs()))
                   for x in nodeHierarchyTree.preorder()]
        factories.nodeHierarchy = newHier

    parentsDict = {}
    for mayaType, parents, children in factories.nodeHierarchy:
        for parent in parents:
            realChildren[parent].add(mayaType)
        parentsDict[mayaType] = parents

    # accumulate OverrideErrors so we can print them all out at once
    overrideErrors = []

    for mayaType, parents, _ in factories.nodeHierarchy:
        children = realChildren[mayaType]

        pyNodeTypeName = factories.getPymelTypeName(mayaType)
        existingClass = getattr(nt, pyNodeTypeName, None)

        if mayaType == 'dependNode':
            parents = []
        elif existingClass is not None:
            # sometimes - ie, due to maya bugs where a node type isn't
            # compatible with the MFn class of one of it's parents - we'll
            # manually define the parent pynode class of a pynode class
            # different than it's normal maya type parent.  Check for this.s
            existingParent = existingClass.__bases__[0]
            existingParentType = \
                factories.pymelTypeNameToMayaTypeName.get(
                    existingParent.__name__)
            if existingParentType and existingParentType != parents[0]:
                parents = [existingParentType] + list(parentsDict[existingParentType])

        if parents:
            parentMayaType = parents[0]
        else:
            assert mayaType == 'dependNode'
            parentMayaType = 'general.PyNode'
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue

        if factories.isMayaType(mayaType) or mayaType == 'dependNode':
            parentMethods = heritedMethods[parentMayaType]
            parentApicls = apiClasses[parentMayaType]
            template = getPyNodeGenerator(mayaType,
                                          existingClass,
                                          pyNodeTypeName,
                                          parents,
                                          children,
                                          parentMethods,
                                          parentApicls)
            if template:
                text, methods = template.render()
                yield text, template
                heritedMethods[mayaType] = parentMethods.union(methods)
                apiClasses[mayaType] = template.apicls
                overrideErrors.extend(template.overrideErrors)

    # wrap any other datatype classes that don't correspond to a depend node
    # ...ie, SelectionSet / MSelectionList
    for text, template in iterModuleApiDataTypeText(pymel.core.nodetypes):
        yield text, template

    if overrideErrors:
        allMethodsToKeys = {}
        for e in overrideErrors:
            allMethodsToKeys.update(e.methodNamesToBridgeKeys)
        raise NewOverrideError(allMethodsToKeys)


def iterUIText():
    # type: () -> Iterator[Tuple[str, UITypeGenerator]]
    """generate code for pymel.core.uitypees"""
    import pymel.core.uitypes
    import pymel.util.trees as trees

    heritedMethods = {
        'PyUI': methodNames(pymel.core.uitypes.PyUI),
        'Layout': methodNames(pymel.core.uitypes.Layout),
        'Panel': methodNames(pymel.core.uitypes.Panel),
    }

    parentDict = {}
    for funcName in factories.uiClassList:
        classname = util.capitalize(funcName)
        if classname in ('Layout', 'Panel'):
            parentType = 'PyUI'
        elif classname.endswith(('Layout', 'Grp')):
            parentType = 'Layout'
        elif classname.endswith('Panel'):
            parentType = 'Panel'
        else:
            parentType = 'PyUI'
        parentDict[classname] = parentType

    uiTypeTree = trees.treeFromDict(parentDict)
    uiTypeTree.sort()

    for uiNode in uiTypeTree.preorder():
        classname = uiNode.value
        if classname == 'PyUI':
            continue
        parentType = uiNode.parent.value

        # Create Class
        if classname == 'MenuItem':
            existingClass = pymel.core.uitypes.CommandMenuItem
        else:
            existingClass = getattr(pymel.core.uitypes, classname, None)

        parentMethods = heritedMethods[parentType]
        template = UITypeGenerator(classname, existingClass, [parentType],
                                   parentMethods,
                                   moduleName='pymel.core.uitypes')
        if template:
            text, methods = template.render()
            yield text, template
            heritedMethods[classname] = parentMethods.union(methods)


def _deleteImportedCoreModules():
    # type: () -> None
    import linecache

    pymelCore = sys.modules.get('pymel.core')

    for name in list(sys.modules):
        splitname = name.split('.')
        if len(splitname) >= 2 and splitname[:2] == ['pymel', 'core']:
            del sys.modules[name]
            assert name not in sys.modules
            if len(splitname) == 3 and pymelCore is not None:
                try:
                    delattr(pymelCore, splitname[2])
                except AttributeError:
                    pass
    linecache.clearcache()

    pymel = sys.modules.get('pymel')
    if pymel is not None:
        if hasattr(pymel, 'core'):
            del pymel.core


def generateAll(allowNonWindows=False):
    # type: (bool) -> None
    import copy
    import linecache

    print("check console for output (script editor does regularly flush output)",
          file=sys.__stdout__)

    # by default, we only allow building these from windows, because we need to
    # test for the __setattr__ bug that only happens on windows.
    if not allowNonWindows and os.name != 'nt':
        raise ValueError("must build on windows - for testing, set allowNonWindows=True")

    origBridgeData = copy.deepcopy(factories._apiMelBridgeCacheInst.contents())
    factories.building = True
    try:

        factories.loadCmdCache()

        # import pymel.core, so resetter can read class source info
        import pymel.core

        print("resetting modules", file=sys.__stdout__)

        # Reset modules, before import
        generator = ModuleGenerator()
        for module, _ in maintenance.buildutil.CORE_CMD_MODULES:
            generator.reset(module)

        generator.reset('pymel.core.windows')
        generator.reset('pymel.core.nodetypes')
        generator.reset('pymel.core.uitypes')
        generator.reset('pymel.core.datatypes')

        print("reloading pymel.core", file=sys.__stdout__)
        # "Reload" pymel.core modules, so we use the reset versions
        _deleteImportedCoreModules()
        import pymel.core

        # these are populated when core.general is imported, but they can be
        # blanked out if the factory module has been reloaded. make sure
        # they are still present
        assert {'MObject', 'MDagPath', 'MPlug'}.issubset(
            factories.ApiTypeRegister.inCast.keys())

        # Generate Functions
        for module, returnFunc in maintenance.buildutil.CORE_CMD_MODULES:
            print("generating %s" % module, file=sys.__stdout__)
            generator.generateFunctions(module, returnFunc)

        print("generating pymel.core.windows", file=sys.__stdout__)
        generator.generateUIFunctions()

        print("generating pymel.core.nodetypes", file=sys.__stdout__)
        generator.generateTypes(iterPyNodeText(),
                                'pymel.core.nodetypes',
                                suffix='\ndynModule = _addTypeNames()\n')

        print("generating pymel.core.uitypes", file=sys.__stdout__)
        generator.generateTypes(iterUIText(),
                                'pymel.core.uitypes',
                                suffix='\n_addTypeNames()\n')

        print("generating pymel.core.general", file=sys.__stdout__)
        generator.generateTypes(iterApiTypeText(), 'pymel.core.general')

        print("generating pymel.core.datatypes", file=sys.__stdout__)
        generator.generateTypes(iterApiDataTypeText(), 'pymel.core.datatypes')

        compileall.compile_dir(os.path.dirname(pymel.core.__file__),
                               force=True)
    finally:
        factories.building = False

    # check to see if bridge data change, write it out if it did
    if origBridgeData != factories._apiMelBridgeCacheInst.contents():
        factories._apiMelBridgeCacheInst.save()


def getParser():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--non-windows', action='store_true',
                        help='Set to allow running on non-windows boxes; final'
                             ' generation should always be done on windows')
    return parser


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    print("Only use this for testing - for final generation, use a GUI maya")
    pymeldir = os.path.dirname(THIS_DIR)
    sys.path.insert(0, pymeldir)

    parser = getParser()
    args = parser.parse_args(argv)

    import maya.standalone
    maya.standalone.initialize()
    generateAll(allowNonWindows=args.non_windows)


if __name__ == '__main__':
    main()
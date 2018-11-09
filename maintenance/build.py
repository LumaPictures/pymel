import compileall
import inspect
import keyword
import os.path
import re
import sys
import types
from collections import defaultdict

from jinja2 import Environment, PackageLoader

import pymel.util as util
from pymel.util.conditions import Always
from pymel.internal import factories
from pymel.internal import plogging
from pymel.internal import pmcmds

if False:
    from typing import *

_logger = plogging.getLogger(__name__)

START_MARKER = '# ------ Do not edit below this line --------'
END_MARKER =   '# ------ Do not edit above this line --------'

CORE_CMD_MODULES = [
    ('pymel.core.animation', '_general.PyNode'),
    ('pymel.core.context', None),
    ('pymel.core.effects', '_general.PyNode'),
    ('pymel.core.general', 'PyNode'),
    ('pymel.core.language', None),
    ('pymel.core.modeling', '_general.PyNode'),
    ('pymel.core.other', None),
    ('pymel.core.rendering', '_general.PyNode'),
    ('pymel.core.runtime', None),
    ('pymel.core.system', None),
]

env = Environment(loader=PackageLoader('maintenance', 'templates'),
                  trim_blocks=True, lstrip_blocks=True)


class Literal(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


def methodNames(cls, apicls=None):
    if apicls:
        herited = set()
        for base in inspect.getmro(cls):
            if base is apicls:
                continue
            for attr, obj in base.__dict__.items():
                if inspect.ismethod(obj):
                    herited.add(attr)
        return herited
    else:
        return set([name for name, obj in inspect.getmembers(cls)
                    if inspect.ismethod(obj)])


def importableName(func, module=None, moduleMap=None):
    try:
        name = func.__name__
    except AttributeError:
        name = func.__class__.__name__

    if name == '<lambda>':
        raise ValueError("received lambda function")

    if func.__module__ == '__builtin__':
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
    return '{' + ', '.join([repr(s) for s in sorted(s)]) + '}'


def _listRepr(s):
    return '[' + ', '.join([repr(s) for s in sorted(s)]) + ']'


def functionTemplateFactory(funcName, module, returnFunc=None,
                            rename=None, uiWidget=False):
    inFunc, funcName, customFunc = factories._getSourceFunction(funcName, module)
    if inFunc is None:
        return ''

    cmdInfo = factories.cmdlist[funcName]
    funcType = type(inFunc)

    if funcType == types.BuiltinFunctionType:
        try:
            newFuncName = inFunc.__name__
            if funcName != newFuncName:
                _logger.warn("Function found in module %s has different name "
                             "than desired: %s != %s. simple fix? %s" %
                             (inFunc.__module__, funcName, newFuncName,
                              funcType == types.FunctionType and
                              returnFunc is None))
        except AttributeError:
            _logger.warn("%s had no '__name__' attribute" % inFunc)

    timeRangeFlags = factories._getTimeRangeFlags(funcName)
    if timeRangeFlags:
        timeRangeFlags = _listRepr(timeRangeFlags)
    # some refactoring done here - to avoid code duplication (and make things clearer),
    # we now ALWAYS do things in the following order:
    # 1. Perform operations which modify the execution of the function (ie, adding return funcs)
    # 2. Modify the function descriptors - ie, __doc__, __name__, etc

    # FIXME: merge the unpack case with maybeConvert case in the template: both test for 'not query'

    # create a repr for a set of flags (but make it ordered so it's stable)
    # unpackFlags = []
    # flags = cmdInfo.get('flags', {})
    # for flag in sorted(flags):
    #     flagInfo = flags[flag]
    #     if flagInfo.get('resultNeedsUnpacking', False):
    #         unpackFlags.append(repr(flagInfo.get('longname', flag)))
    #         unpackFlags.append(repr(flagInfo.get('shortname', flag)))

    unpackFlags = set()
    for flag, flagInfo in cmdInfo.get('flags', {}).iteritems():
        if flagInfo.get('resultNeedsUnpacking', False):
            unpackFlags.add(flagInfo.get('longname', flag))
            unpackFlags.add(flagInfo.get('shortname', flag))

    if unpackFlags:
        unpackFlags = _setRepr(unpackFlags)

    if funcName in factories.simpleCommandWraps:
        # simple wraps: we only do these for functions which have not been
        # manually customized
        wraps = factories.simpleCommandWraps[funcName]
        doc = 'Modifications:\n'
        for func, wrapCondition in wraps:
            if wrapCondition != Always:
                # use only the long flag name
                flags = ' for flags: ' + str(wrapCondition)
            elif len(wraps) > 1:
                flags = ' for all other flags'
            else:
                flags = ''
            if func.__doc__:
                funcString = func.__doc__.strip()
            else:
                funcString = pmcmds.getCmdName(func) + '(result)'
            doc += '  - ' + funcString + flags + '\n'

    existing = inFunc.__module__ == module.__name__
    resultNeedsUnpacking = cmdInfo.get('resultNeedsUnpacking', False)
    callbackFlags = cmdInfo.get('callbackFlags', None)
    if callbackFlags:
        callbackFlags = _listRepr(callbackFlags)
    wrapped = funcName in factories.simpleCommandWraps
    if any([timeRangeFlags, returnFunc, resultNeedsUnpacking, unpackFlags, wrapped, callbackFlags]):
        sourceFuncName = importableName(inFunc,
                                        moduleMap={'pymel.internal.pmcmds': 'cmds'})

        result = ''
        if existing:
            sourceFuncName = sourceFuncName.rsplit('.', 1)[1]
            result += '\n_{func} = {func}\n'.format(func=sourceFuncName)
            sourceFuncName = '_' + sourceFuncName

        template = env.get_template('commandfunc.py')
        return result + template.render(
            funcName=rename or funcName,
            commandName=funcName, timeRangeFlags=timeRangeFlags,
            sourceFuncName=sourceFuncName,
            returnFunc=returnFunc,
            resultNeedsUnpacking=resultNeedsUnpacking,
            unpackFlags=unpackFlags,
            simpleWraps=wrapped,
            callbackFlags=callbackFlags, uiWidget=uiWidget).encode()
    else:
        if existing:
            return "\n{newName} = _factories.addCmdDocs({origName})\n".format(
                newName=rename or funcName,
                origName=funcName)
        # no doc in runtime module
        if module.__name__ == 'pymel.core.runtime':
            return "\n{newName} = getattr(cmds, '{origName}', None)\n".format(
                newName=rename or funcName,
                origName=funcName)
        else:
            return "\n{newName} = _factories.getCmdFunc('{origName}')\n".format(
                newName=rename or funcName,
                origName=funcName)


    # FIXME: handle these!
    # Check if we have not been wrapped yet. if we haven't and our input function is a builtin or we're renaming
    # then we need a wrap. otherwise we can just change the __doc__ and __name__ and move on
    if newFunc == inFunc and (type(newFunc) == types.BuiltinFunctionType or rename):
        # we'll need a new function: we don't want to touch built-ins, or
        # rename an existing function, as that can screw things up... just modifying docs
        # of non-builtin should be fine, though
        def newFunc(*args, **kwargs):
            return inFunc(*args, **kwargs)

    # 2. Modify the function descriptors - ie, __doc__, __name__, etc
    if customFunc:
        # copy over the exisitng docs
        if not newFunc.__doc__:
            newFunc.__doc__ = inFunc.__doc__
        elif inFunc.__doc__:
            newFunc.__doc__ = inFunc.__doc__
    addCmdDocs(newFunc, funcName)


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


class ModuleGenerator(object):
    def __init__(self):
        self.moduleLines = {}
        self.classInsertLocations = {}
        self.classSuffixes = {}

    @classmethod
    def getClassLocations(cls, moduleName):
        moduleObject = sys.modules[moduleName]
        classLocations = []
        for clsname, clsobj in inspect.getmembers(moduleObject, inspect.isclass):
            try:
                clsmodule = inspect.getmodule(clsobj)
                if clsmodule != moduleObject:
                    continue
                start, end = _getSourceStartEndLines(clsobj)
            except IOError:
                # some classes, you won't be able to get source for - ignore
                #these
                continue

            classLocations.append((start, end, clsname))
        classLocations.sort()
        return classLocations

    def getModuleLines(self, module):
        if isinstance(module, types.ModuleType):
            module = module.__name__
        return self.moduleLines[module]

    def reset(self, module):
        if module in self.moduleLines:
            raise RuntimeError("You probably don't want to reset an already-"
                               "reset or edited module")

        classLocations = self.getClassLocations(module)

        source = _getModulePath(module)
        with open(source, 'r') as f:
            text = f.read()

        lines = text.split('\n')

        self.totalTrimmed = 0

        def doTrim(trimStart, trimEnd):
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
                    # This, we resetting the module, we also trim off any
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
            start = None
            for i, line in enumerate(lines[begin:]):
                i = begin + i
                if start is None and line == START_MARKER:
                    _logger.debug("Found start marked (original line: {} /"
                                  " new file line: {})".format(
                        i + self.totalTrimmed + 1, i + 1))
                    start = i

                elif line == END_MARKER:
                    _logger.debug("Found end marked (original line: {} /"
                                  " new file line: {})".format(
                        i + self.totalTrimmed + 1, i + 1))
                    assert start is not None
                    doTrim(start, i)
                    return start

            # end of lines
            if start is not None:
                doTrim(start, i)
            return None

        begin = 0
        while begin is not None:
            begin = trim(begin)

        del self.totalTrimmed

        lines.append(START_MARKER)

        print "writing reset", source
        with open(source, 'w') as f:
            f.write('\n'.join(lines))
        self.moduleLines[module] = lines


    def _writeToModule(self, new, module):
        if isinstance(module, types.ModuleType):
            moduleName = module.__name__
        else:
            moduleName = module
        lines = self.moduleLines[moduleName]

        # trim off last START_MARKER and anything after
        for i in xrange(len(lines) - 1, -1, -1):
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
        print "writing to", path
        with open(path, 'w') as f:
            f.write('\n'.join(lines))


    def generateFunctions(self, moduleName, returnFunc=None):
        """
        Render templates for mel functions in `moduleName` into its module file.
        """
        module = sys.modules[moduleName]
        moduleShortName = moduleName.split('.')[-1]

        new = ''
        for funcName in factories.moduleCmds[moduleShortName]:
            if funcName in factories.nodeCommandList:
                new += functionTemplateFactory(funcName, module, returnFunc=returnFunc)
            else:
                new += functionTemplateFactory(funcName, module, returnFunc=None)
        self._writeToModule(new, module)


    def generateUIFunctions(self):
        new = ''
        module = sys.modules['pymel.core.windows']
        moduleShortName ='windows'

        for funcName in factories.uiClassList:
            # Create Class
            classname = util.capitalize(funcName)
            new += functionTemplateFactory(funcName, module,
                                           returnFunc='uitypes.' + classname,
                                           uiWidget=True)

        nonClassFuncs = set(factories.moduleCmds[moduleShortName]).difference(factories.uiClassList)
        for funcName in nonClassFuncs:
            new += functionTemplateFactory(funcName, module, returnFunc=None)

        new += '\nautoLayout.__doc__ = formLayout.__doc__\n'
        self._writeToModule(new, module)

    def generateTypes(self, iterator, module, suffix=None):
        """
        Utility for append type templates below their class within a given module.

        Parameters
        ----------
        iterator
        module
        suffix
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

        print "writing to", source
        with open(source, 'w') as f:
            f.write(text)

def wrapApiMethod(apiClass, apiMethodName, newName=None, proxy=True,
                  overloadIndex=None, deprecated=False, aliases=(),
                  properties=()):
    # type: (Type, str, str, bool, Optional[int], Any, Any, Any) -> Optional[dict]
    """
    create a wrapped, user-friendly API method that works the way a python method should: no MScriptUtil and
    no special API classes required.  Inputs go in the front door, and outputs come out the back door.


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

    Take `MFnTransform.setTranslation`, for example. PyMEL provides a wrapped copy of this as
    `Transform.setTranslation`.   when pymel.Transform.setTranslation is
    called, here's what happens in relation to undo:

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
        If True, then __apimfn__ function used to retrieve the proxy class. If False,
        then we assume that the class being wrapped inherits from the underlying api class.
    overloadIndex : Optional[int]
        which of the overloaded C++ signatures to use as the basis of our wrapped function.

    Returns
    -------
    Optional[dict]
    """
    apiClassName = apiClass.__name__
    argHelper = factories.ApiArgUtil(apiClassName, apiMethodName, overloadIndex)
    undoable = True  # controls whether we print a warning in the docs

    pymelName = argHelper.getPymelName()

    if newName is None:
        newName = pymelName

    if not argHelper.canBeWrapped():
        return

    inArgs = argHelper.inArgs()
    outArgs = argHelper.outArgs()
    argList = argHelper.argList()

    getterArgHelper = argHelper.getGetterInfo()

    if argHelper.hasOutput():
        # query method ( getter )
        getterInArgs = []
    else:
        # edit method ( setter )
        if getterArgHelper is None:
            #_logger.debug( "%s.%s has no inverse: undo will not be supported" % ( apiClassName, methodName ) )
            getterInArgs = []
            undoable = False
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

    unitType = argHelper.methodInfo['returnInfo'].get('unitType', None)
    returnType = argHelper.methodInfo['returnType']
    argInfo = argHelper.methodInfo['argInfo']

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
        'undoable': getterArgHelper is not None,
        'returnType': repr(convertTypeArg(returnType)) if returnType else None,
        'unitType': repr(str(unitType)) if unitType else None,
        'deprecated': deprecated,
        'signature': signature,
        'aliases': aliases,
        'properties': properties,  # property aliases
    }

    wrappedApiFunc.__name__ = newName

    _addApiDocs(wrappedApiFunc, apiClass, apiMethodName, overloadIndex, undoable)

    if defaults:
        pass
        #_logger.debug("defaults: %s" % defaults)

    wrappedApiFunc = util.interface_wrapper(wrappedApiFunc, ['self'] + inArgs, defaults=defaults)
    wrappedApiFunc._argHelper = argHelper

    global _DEBUG_API_WRAPS
    if _DEBUG_API_WRAPS:
        import weakref
        global _apiMethodWraps
        classWraps = _apiMethodWraps.setdefault(apiClassName, {})
        methodWraps = classWraps.setdefault(apiMethodName, [])
        methodWraps.append({'index': argHelper.methodIndex,
                            'funcRef': weakref.ref(wrappedApiFunc),
                            })

    # do the debug stuff before turning into a classmethod, because you
    # can't create weakrefs of classmethods (don't ask me why...)
    if argHelper.isStatic():
        wrappedApiFunc = classmethod(wrappedApiFunc)

    if argHelper.isDeprecated():
        argDescriptions = []
        for arg in argList:
            argName = arg[0]
            argType = arg[1]
            if isinstance(argType, apicache.ApiEnum):
                argType = argType[0]
            elif inspect.isclass(argType):
                argType = argType.__name__
            argDescriptions.append('{} {}'.format(argType, argName))
        argStr = ', '.join(argDescriptions)
        methodDesc = "{}.{}({})".format(apiClassName, apiMethodName, argStr)
        beforeDeprecationGenerator = wrappedApiFunc

        def wrappedApiFunc(*args, **kwargs):
            import warnings
            warnings.warn("{} is deprecated".format(methodDesc),
                          DeprecationWarning, stacklevel=2)
            return beforeDeprecationGenerator(*args, **kwargs)
    return wrappedApiFunc


class MelMethodGenerator(object):

    def __init__(self, classname, existingClass, parentClasses, parentMethods):
        # type: (str, Type, Iterable[str], Iterable[str]) -> None
        """
        Parameters
        ----------
        classname : str
        existingClass : Type
        parentClasses : Iterable[str]
        parentMethods : Iterable[str]
        """
        self.classname = classname
        self.parentClassname = parentClasses[0] if parentClasses else None
        self.herited = parentMethods
        self.parentClasses = parentClasses
        self.existingClass = existingClass
        self.attrs = {}
        self.methods = {}
        self.prefixLines = []

    def setDefault(self, key, value, directParentOnly=True):
        if directParentOnly:
            if self.existingClass is None or key not in self.existingClass.__dict__:
                self.attrs.setdefault(key, value)
        else:
            if self.existingClass is None or not hasattr(self.existingClass, key):
                self.attrs.setdefault(key, value)

    def render(self):
        self.getTemplateData()

        # self.setDefault('__metaclass__', Literal('_f.MetaMayaTypeRegistry'))

        methodNames = set(self.methods)
        if self.existingClass:
            # add methods that exist *directly* on the existing class
            methodNames.update(
                name for name, obj in self.existingClass.__dict__.items()
                if inspect.isfunction(obj))

        def toStr(k, v):
            if k == '__melcmd__':
                return 'staticmethod(%s)' % v
            else:
                return repr(v)

        attrs = [{'name': k, 'value': toStr(k, self.attrs[k])} for k in sorted(self.attrs)]

        allMethodLines = []
        for methodName in sorted(self.methods):
            allMethodLines.append(self.getMethodLines(methodName))
        print "{}: found {} methods".format(self.classname, len(allMethodLines))

        template = env.get_template('nodeclass.py')
        text = template.render(methods=allMethodLines, attrs=attrs,
                               classname=self.classname,
                               parents=self.parentClassname,
                               existing=self.existingClass is not None,
                               prefixLines=self.prefixLines)

        return text, methodNames

    def getMethodLines(self, methodName):
        methodInfo = self.methods[methodName]
        templateName = {
            'query': 'querymethod.py',
            'edit': 'editmethod.py',
            'getattribute': 'getattribute.py',
            'api': 'apimethod.py',
        }[methodInfo['type']]
        template = env.get_template(templateName)
        text = template.render(method=methodInfo,
                               classname=self.classname)
        return text.splitlines()

    def getMELData(self):
        """
        Add methods from MEL functions
        """
        #_logger.debug( 'MelMethodGenerator: %s' % classname )

        # ------------------------
        #   MEL Methods
        # ------------------------
        melCmdName, infoCmd = self.getMelCmd()

        try:
            cmdInfo = factories.cmdlist[melCmdName]
        except KeyError:
            pass
            #_logger.debug("No MEL command info available for %s" % melCmdName)
        else:
            # FIXME: this old behavior implies that sometimes we used unwrapped commands,
            # but it's unclear how this would happen.  Was it a load order thing? Confirm on old version.
            # pmSourceFunc = False
            # try:
            #     cmdModule = __import__('pymel.core.' + cmdInfo['type'], globals(), locals(), [''])
            #     func = getattr(cmdModule, melCmdName)
            #     pmSourceFunc = True
            # except (AttributeError, TypeError):
            #     func = getattr(pmcmds, melCmdName)

            pmSourceFunc = True
            cmdPath = '%s.%s' % (cmdInfo['type'], melCmdName)

            # FIXME: add documentation
            # classdict['__doc__'] = util.LazyDocString((newcls, self.docstring, (melCmdName,), {}))

            self.attrs['__melcmd__'] = cmdPath
            self.attrs['__melcmdname__'] = melCmdName
            self.attrs['__melcmd_isinfo__'] = infoCmd

            # base set of disallowed methods (for MEL)
            filterAttrs = {'name', 'getName', 'setName'}
            # already created attributes for this class:
            filterAttrs.update(self.attrs.keys())
            # already created methods for this class:
            filterAttrs.update(self.methods.keys())
            # methods on parent classes:
            filterAttrs.update(self.herited)
            filterAttrs.update(factories.overrideMethods.get(self.parentClassname, []))

            for flag, flagInfo in cmdInfo['flags'].items():
                # don't create methods for query or edit, or for flags which only serve to modify other flags
                if flag in ['query', 'edit'] or 'modified' in flagInfo:
                    continue

                if flagInfo.has_key('modes'):
                    # flags which are not in maya docs will have not have a modes list unless they
                    # have passed through testNodeCmds
                    # continue
                    modes = flagInfo['modes']

                    # query command
                    if 'query' in modes:
                        methodName = 'get' + util.capitalize(flag)

                        factories.classToMelMap[self.classname].append(methodName)

                        if methodName not in filterAttrs and \
                                (not hasattr(self.existingClass, methodName) or self.isMelMethod(methodName)):

                            # 'enabled' refers to whether the API version of this method will be used.
                            # if the method is enabled that means we skip it here.
                            bridgeInfo = factories.apiToMelData.get((self.classname, methodName))
                            if (not bridgeInfo
                                    or bridgeInfo.get('melEnabled', False)
                                    or not bridgeInfo.get('enabled', True)):
                                returnFunc = None

                                if flagInfo.get('resultNeedsCasting', False):
                                    returnFunc = flagInfo['args']

                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                self.methods[methodName] = {
                                    'name': methodName,
                                    'command': melCmdName,
                                    'type': 'query',
                                    'flag': flag,
                                    'returnFunc': importableName(returnFunc) if returnFunc else None,
                                    'func': cmdPath,
                                }
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled or overridden by API" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))
                    # edit command:
                    if 'edit' in modes or (infoCmd and 'create' in modes):
                        # if there is a corresponding query we use the 'set' prefix.
                        if 'query' in modes:
                            methodName = 'set' + util.capitalize(flag)
                        # if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
                        else:
                            methodName = flag

                        factories.classToMelMap[self.classname].append(methodName)

                        if methodName not in filterAttrs and \
                                (not hasattr(self.existingClass, methodName) or self.isMelMethod(methodName)):
                            bridgeInfo = factories.apiToMelData.get((self.classname, methodName))
                            if (not bridgeInfo
                                    or bridgeInfo.get('melEnabled', False)
                                    or not bridgeInfo.get('enabled', True)):

                                # FIXME: shouldn't we be able to use the wrapped pymel command, which is already fixed?
                                # FIXME: the 2nd argument is wrong, so I think this is broken
                                # fixedFunc = fixCallbacks(func, melCmdName)

                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                self.methods[methodName] = {
                                    'name': methodName,
                                    'command': melCmdName,
                                    'type': 'edit',
                                    'flag': flag,
                                    'func': cmdPath,
                                }
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))

    def getMelCmd(self):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.

        Intended to be overridden in derived metaclasses.
        """
        raise NotImplementedError
        # return util.uncapitalize(self.classname), False

    def isMelMethod(self, methodName):
        """
        Determine if the passed method name exists on a parent class as a mel method
        """
        for classname in self.parentClasses:
            if methodName in factories.classToMelMap.get(classname, ()):
                return True
        return False

    def docstring(self, melCmdName):
        try:
            cmdInfo = factories.cmdlist[melCmdName]
        except KeyError:
            #_logger.debug("No MEL command info available for %s" % melCmdName)
            classdoc = ''
        else:
            factories.loadCmdDocCache()
            classdoc = 'class counterpart of mel function `%s`\n\n%s\n\n' % (melCmdName, cmdInfo['description'])
        return classdoc


# FIXME: don't inherit here, treat as a Mixin
class ApiMethodGenerator(MelMethodGenerator):

    VALID_NAME = re.compile('[a-zA-Z_][a-zA-Z0-9_]*$')
    proxy = True

    def __init__(self, classname, existingClass, parentClasses,
                 parentMethods, parentApicls, childClasses=()):
        # type: (str, Type, Iterable[str], Iterable[str], Optional[Type], Iterable[str]) -> None
        """
        Parameters
        ----------
        classname : str
        existingClass : Type
        parentClasses : Iterable[str]
        parentMethods : Iterable[str]
        parentApicls : Optional[Type]
        childClasses : Iterable[str]
        """
        super(ApiMethodGenerator, self).__init__(classname, existingClass, parentClasses, parentMethods)
        self.parentApicls = parentApicls
        self.existingClass = existingClass
        self.childClasses = childClasses
        self.apicls = self.getApiCls()

    def methodIsEnabledOnChildren(self, pymelName):
        """
        previous versions of pymel erroneously included disabled methods on
        child classes which possessed the same apicls as their parent.
        We will deprecate them in order to allow users to transition.
        """
        enabled = []
        # cycle through child classes and test overrides for this method
        for childClassName in self.childClasses:
            _, overrides, _ = factories._getApiOverrideNameAndData(
                childClassName, pymelName)
            if overrides.get('overloadIndex', None) is None:
                continue
            elif not overrides.get('enabled', True):
                continue
            # enabled!
            enabled.append(childClassName)
        return enabled

    def getApiCls(self):
        if self.existingClass is not None:
            try:
                return self.existingClass.__dict__['__apicls__']
            except KeyError:
                pass

    def addEnums(self, classInfo):
        if 'pymelEnums' in classInfo:
            # Enumerators
            for enumName, enum in classInfo['pymelEnums'].items():
                self.attrs[enumName] = enum

    def getAPIData(self):
        """
        Add methods from API functions
        """

        self.removeAttrs = []

        _logger.info('%s: %s: %s' % (self.__class__, self.classname, self.apicls))

        if self.apicls is None:
            return

        if self.apicls.__name__ not in factories.apiClassNamesToPyNodeNames:
            factories.apiClassNamesToPyNodeNames[self.apicls.__name__] = self.classname

        if self.apicls is self.parentApicls:
            # If this class's api class is the same as the parent, the methods
            # are already handled.
            # FIXME: should this be extended to check all parent classes?
            # FIXME: assert that there is nothing explicit in the mel-api bridge
            return

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
                for methodName, info in classInfo['methods'].iteritems():
                    # don't rewrap if already herited from a base class that is not the apicls
                    # _logger.debug("Checking method %s" % (methodName))

                    try:
                        basePymelName = info[0]['pymelName']
                        self.removeAttrs.append(methodName)
                    except KeyError:
                        basePymelName = methodName
                    pymelName, overrideData, renamed = factories._getApiOverrideNameAndData(
                        self.classname, basePymelName)

                    # if 'addAttribute' in (pymelName, basePymelName, methodName):
                    #     print self.classname, pymelName, basePymelName, methodName, renamed, overrideData

                    if not self.VALID_NAME.match(pymelName) or keyword.iskeyword(pymelName):
                        print "Invalid name", self.classname, methodName, info
                        continue

                    overloadIndex = overrideData.get('overloadIndex', None)

                    aliases = overrideData.get('aliases', [])
                    properties = overrideData.get('properties', [])
                    yieldTuple = (methodName, self.classname, pymelName,
                                  overloadIndex, aliases, properties)

                    if overloadIndex is None:
                        #_logger.debug("%s.%s has no wrappable methods, skipping" % (apicls.__name__, methodName))
                        continue
                    if not overrideData.get('enabled', True):
                        #_logger.debug("%s.%s has been manually disabled, skipping" % (apicls.__name__, methodName))
                        # FIXME: add unique deprecation message
                        if methodName in factories.EXCLUDE_METHODS:
                            continue
                        usedByChildren = self.methodIsEnabledOnChildren(pymelName)
                        if not usedByChildren:
                            print self.classname, pymelName, "not on any children"
                            continue
                        else:
                            _logger.info("%s.%s: Adding disabled method as "
                                         "deprecated. Used by children %s" %
                                         (self.classname, pymelName, usedByChildren))
                            deprecated.append(yieldTuple)
                    elif info[overloadIndex].get('deprecated', False):
                        deprecated.append(yieldTuple)
                    else:
                        yield yieldTuple + (False,)

                    if renamed:
                        print "Adding renamed as deprecated", self.classname, methodName, pymelName
                        # FIXME: previous versions of pymel erroneously included
                        # renamed/remapped methods on child classes which possessed the same apicls as their parent.
                        # We should include them as deprecated.
                        deprecated.append(
                            (methodName, self.classname,
                             basePymelName, overloadIndex, [], []))

                for yieldTuple in deprecated:
                    yield yieldTuple + (True,)

            for (methodName, classname, pymelName, overloadIndex, aliases, properties, deprecated) \
                    in non_deprecated_methods_first():
                assert isinstance(pymelName, str), "%s.%s: %r is not a valid name" % (classname, methodName, pymelName)

                # TODO: some methods are being wrapped for the base class,
                # and all their children - ie, MFnTransform.transformation()
                # gets wrapped for Transform, Place3dTexture,
                # HikGroundPlane, etc...
                # Figure out why this happens, and stop it!
                if pymelName not in self.herited and (self.existingClass is None or pymelName not in self.existingClass.__dict__):
                    if pymelName not in self.methods:
                        #_logger.debug("%s.%s autowrapping %s.%s usng proxy %r" % (classname, pymelName, apicls.__name__, methodName, proxy))
                        doc = wrapApiMethod(self.apicls, methodName, newName=pymelName,
                                            proxy=self.proxy, overloadIndex=overloadIndex,
                                            deprecated=deprecated, aliases=aliases,
                                            properties=properties)
                        if doc:
                            self.methods[pymelName] = doc
                        #else: _logger.info("%s.%s: wrapApiMethod failed to create method" % (apicls.__name__, methodName ))
                    #else: _logger.info("%s.%s: already defined, skipping" % (apicls.__name__, methodName))
                #else: _logger.info("%s.%s already herited, skipping (existingClass %s)" % (apicls.__name__, methodName, hasattr(self.existingClass, pymelName)))

            self.addEnums(classInfo)


class ApiDataTypeGenerator(ApiMethodGenerator):
    """
    M* data classes
    """

    proxy = False

    def getApiCls(self):
        if self.existingClass is not None:
            try:
                return self.existingClass.__dict__['apicls']
            except KeyError:
                pass

    def getTemplateData(self):
        # first populate API methods.  they take precedence.
        self.setDefault('__slots__', ())
        self.getAPIData()

    def getAPIData(self):
        """
        Add methods from API functions
        """
        super(ApiDataTypeGenerator, self).getAPIData()

        _logger.info("%s: removing attributes %s" % (self.classname, self.removeAttrs))

        if self.apicls is None:
            return

        if self.removeAttrs:
            # because datatype classes inherit from their API classes, if a
            # method is renamed, we must also remove the inherited API method.
            self.methods['__getattribute__'] = {
                'type': 'getattribute',
                'removeAttrs': _setRepr(self.removeAttrs),
            }

        # if we imported using old, non-template-generated maya, then
        # it may have fixed the setattr bug on the OpenMaya class itself - undo
        # this!
        setattr = self.apicls.__dict__.get('__setattr__')
        if setattr is not None and getattr(setattr, '__name__', None) == 'apiSetAttrWrap':
            internal_vars = dict(zip(setattr.func_code.co_freevars,
                                     (x.cell_contents for x in
                                      setattr.func_closure)))
            origSetAttr = internal_vars['origSetAttr']
            self.apicls.__setattr__ = origSetAttr
        if factories.MetaMayaTypeWrapper._hasApiSetAttrBug(self.apicls):
            if os.name != 'nt':
                # we should only see this in windows - if we see it elsewhere,
                # raise an error so we can decide what to do
                raise ValueError("saw setattr bug on non-windows!")
            self.prefixLines.extend([
                r"""if os.name == 'nt':""",
                r"""    __setattr__ = _f.MetaMayaTypeWrapper.setattr_fixed_forDataDescriptorBug""",
            ])

        # shortcut for ensuring that our class constants are the same type as the class we are creating
        def makeClassConstant(attr):
            print "make constant", self.classname, self.existingClass, attr
            return Literal('_f.ClassConstant(%r)' % list(attr))

        # -----------------------
        # Class Constants
        # -----------------------
        # build some constants on the class
        constant = {}
        # constants in class definition will be converted from api class to created class
        for name, attr in self.existingClass.__dict__.iteritems():
            # to add the wrapped api class constants as attributes on the wrapping class,
            # convert them to own class
            if isinstance(attr, self.apicls):
                if name not in constant:
                    constant[name] = makeClassConstant(attr)
        # we'll need the api class dict to automate some of the wrapping
        # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping
        # defining class properties on the created class
        for name, attr in inspect.getmembers(self.apicls):
            # to add the wrapped api class constants as attributes on the wrapping class,
            # convert them to own class
            if isinstance(attr, self.apicls):
                if name not in constant:
                    constant[name] = makeClassConstant(attr)
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


class NodeTypeGenerator(ApiMethodGenerator):
    """
    MFn* classes which correspond to a node type
    """

    def __init__(self, classname, existingClass, parentClasses,
                 parentMethods, parentApicls, childClasses=(), mayaType=None):
        # type: (str, Type, Iterable[str], Iterable[str], Type, Iterable[str], str) -> None
        """
        Parameters
        ----------
        classname : str
        existingClass : Type
        parentClasses : Iterable[str]
        parentMethods : Iterable[str]
        parentApicls : Type
        childClasses : Iterable[str]
        mayaType : str
        """
        # mayaType must be set first
        self.mayaType = mayaType
        super(NodeTypeGenerator, self).__init__(
            classname, existingClass, parentClasses, parentMethods,
            parentApicls, childClasses)

    def getApiCls(self):
        if self.mayaType is not None:
            return factories.toApiFunctionSet(self.mayaType)

        return super(NodeTypeGenerator, self).getApiCls()

    def getTemplateData(self):
        self.setDefault('__slots__', ())

        self.attrs['__melnode__'] = self.mayaType

        if self.apicls is not None and self.apicls is not self.parentApicls:
            self.setDefault('__apicls__',
                            Literal('_api.' + self.apicls.__name__))

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
        #     self.attrs['__melnode__'] = nodeType

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
        self.getAPIData()
        # next, populate MEL methods
        self.getMELData()

        # FIXME:
        # PyNodeType = super(ApiMethodGenerator, self).render()
        # ParentPyNode = [x for x in bases if issubclass(x, util.ProxyUnicode)]
        # assert len(ParentPyNode), "%s did not have exactly one parent PyNode: %s (%s)" % (self.classname, ParentPyNode, self.bases)
        # factories.addPyNodeType(PyNodeType, ParentPyNode)
        # return PyNodeType

    def getMelCmd(self):
        """
        Retrieves the name of the mel command for the node that the generated class wraps,
        and whether it is an info command.

        Derives the command name from the mel node name - so '__melnode__' must already be set
        in classdict.
        """
        infoCmd = False
        try:
            nodeCmd = factories.cmdcache.nodeTypeToNodeCommand[self.mayaType]
        except KeyError:
            try:
                nodeCmd = factories.nodeTypeToInfoCommand[self.mayaType]
                infoCmd = True
            except KeyError:
                nodeCmd = self.mayaType
        return nodeCmd, infoCmd


class ApiUnitsGenerator(ApiDataTypeGenerator):

    def getTemplateData(self):
        classInfo = factories.apiClassInfo[self.apicls.__name__]
        self.addEnums(classInfo)


class ApiTypeGenerator(ApiMethodGenerator):
    """
    MFn* classes which do not correspond to a node type
    """
    def getTemplateData(self):
        self.setDefault('__slots__', ())

        if self.apicls is not None and self.apicls is not self.parentApicls:
            self.setDefault('__apicls__',
                            Literal('_api.' + self.apicls.__name__))

        # first populate API methods.  they take precedence.
        self.getAPIData()


class UITypeGenerator(MelMethodGenerator):

    """
    A metaclass for creating classes based on on a maya UI type/command.
    """

    def getTemplateData(self):
        self.setDefault('__slots__', ())
        # If the class explicitly gives it's mel ui command name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        self.attrs.setdefault('__melui__', util.uncapitalize(self.classname))

        # TODO: implement a option at the cmdlist level that triggers listForNone
        # TODO: create labelArray for *Grp ui elements, which passes to the correct arg ( labelArray3, labelArray4, etc ) based on length of passed array
        self.getMELData()

    def getMelCmd(self):
        return self.attrs['__melui__'], False


def getPyNodeGenerator(mayaType, parentMayaTypes, childMayaTypes, parentMethods, parentApicls):
    # type: (str, List[str], Any, Any, Any) -> NodeTypeGenerator
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

    def getPymelTypeName(mayaTypeName):
        # type: (str) -> str
        pymelTypeName = nt.mayaTypeNameToPymelTypeName.get(mayaTypeName)
        if pymelTypeName is None:
            pymelTypeName = str(util.capitalize(mayaTypeName))
            pymelTypeNameBase = pymelTypeName
            num = 1
            while pymelTypeName in nt.pymelTypeNameToMayaTypeName:
                num += 1
                pymelTypeName = pymelTypeNameBase + str(num)
            nt.mayaTypeNameToPymelTypeName[mayaTypeName] = pymelTypeName
            nt.pymelTypeNameToMayaTypeName[pymelTypeName] = mayaTypeName
        return pymelTypeName

    def getCachedPymelType(nodeType):
        # type: (str) -> str
        if nodeType == 'general.PyNode':
            assert mayaType == 'dependNode'
            return 'general.PyNode'
        else:
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
    pyNodeTypeName = getPymelTypeName(mayaType)
    existingClass = getattr(nt, pyNodeTypeName, None)

    return NodeTypeGenerator(pyNodeTypeName, existingClass,
                             parentPymelTypes, parentMethods, parentApicls,
                             childPymelTypes, mayaType)


def iterApiTypeText():
    import pymel.core.general
    # FIXME: handle herited methods
    types = [
        pymel.core.general.Attribute,
        pymel.core.general.AttributeDefaults,
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


def iterApiDataTypeText():
    import pymel.core.datatypes

    heritedMethods = {
        'VectorN': methodNames(pymel.core.datatypes.VectorN),
        'MatrixN': methodNames(pymel.core.datatypes.MatrixN),
        'Array': methodNames(pymel.core.datatypes.Array),
    }

    def dependentOrder(objects, seen):
        for obj in objects:
            if obj in seen:
                continue

            seen.add(obj)
            for child in dependentOrder(obj.__bases__, seen):
                yield child

            if hasattr(obj, 'apicls') and obj.__module__ == 'pymel.core.datatypes':
                yield obj

    classes = [obj for name, obj in inspect.getmembers(pymel.core.datatypes)
               if inspect.isclass(obj)]
    for obj in dependentOrder(classes, set()):
        # we check for type registry metaclass because some datatypes (Time, Distance)
        # don't have a metaclass (and never did).  I'm not sure if that was a
        # mistake, but adding the metaclass causes errors.
        if issubclass(getattr(obj, '__metaclass__', type), factories.MetaMayaTypeRegistry):
            cls = obj
            # parentMethods = methodNames(cls, apicls=obj.apicls)
            parentApicls = None
            parentPymelTypes = [x.__name__ for x in cls.mro()[1:]
                                if x not in (obj.apicls, object)]
            if parentPymelTypes:
                parentMethods = heritedMethods[parentPymelTypes[0]]
            else:
                parentMethods = set()
            template = ApiDataTypeGenerator(
                cls.__name__, cls, parentPymelTypes, parentMethods, parentApicls)

            text, methods = template.render()
            yield text, template
            heritedMethods[cls.__name__] = parentMethods.union(methods)

        elif issubclass(obj, pymel.core.datatypes.Unit):
            cls = obj
            parentMethods = set()
            parentApicls = None
            parentPymelTypes = [x.__name__ for x in cls.mro()[1:]]
            template = ApiUnitsGenerator(
                cls.__name__, cls, parentPymelTypes, parentMethods, parentApicls)

            text, methods = template.render()
            yield text, template


def iterPyNodeText():
    import pymel.core.general

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
    for mayaType, parents, children in factories.nodeHierarchy:
        for parent in parents:
            realChildren[parent].add(mayaType)

    for mayaType, parents, _ in factories.nodeHierarchy:
        children = realChildren[mayaType]

        if mayaType == 'dependNode':
            parents = ['general.PyNode']

        parentMayaType = parents[0]
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue

        if factories.isMayaType(mayaType) or mayaType == 'dependNode':
            parentMethods = heritedMethods[parentMayaType]
            parentApicls = apiClasses[parentMayaType]
            template = getPyNodeGenerator(mayaType, parents, children, parentMethods, parentApicls)
            if template:
                text, methods = template.render()
                yield text, template
                heritedMethods[mayaType] = parentMethods.union(methods)
                apiClasses[mayaType] = template.apicls


def iterUIText():
    import pymel.core.uitypes

    heritedMethods = {
        'PyUI': methodNames(pymel.core.uitypes.PyUI),
        'Layout': methodNames(pymel.core.uitypes.Layout),
        'Panel': methodNames(pymel.core.uitypes.Panel),
    }

    for funcName in factories.uiClassList:
        # Create Class
        classname = util.capitalize(funcName)
        if classname == 'MenuItem':
            existingClass = pymel.core.uitypes.CommandMenuItem
        else:
            existingClass = getattr(pymel.core.uitypes, classname, None)

        if classname.endswith(('Layout', 'Grp')):
            parentType = 'Layout'
        elif classname.endswith('Panel'):
            parentType = 'Panel'
        else:
            parentType = 'PyUI'

        parentMethods = heritedMethods[parentType]
        template = UITypeGenerator(classname, existingClass, [parentType], parentMethods)
        if template:
            text, methods = template.render()
            yield text, template
            heritedMethods[classname] = parentMethods.union(methods)


def _deleteImportedCoreModules():
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
    import linecache

    # by default, we only allow building these from windows, because we need to
    # test for the __setattr__ bug that only happens on windows.
    if not allowNonWindows and os.name != 'nt':
        raise ValueError("must build on windows - for testing, set allowNonWindows=True")

    factories.building = True
    factories.loadCmdCache()

    try:
        # FIXME: save this into the caches

        # these don't exist on the API classes, as '__rmult__' or '__rmul__'
        factories.apiClassInfo['MEulerRotation']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MMatrix']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MFloatMatrix']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MQuaternion']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MVector']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MFloatVector']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MColor']['methods'].pop('__rmult__', None)
        factories.apiClassInfo['MPoint']['methods'].pop('__rmult__', None)

        factories.apiToMelData[('DependNode', 'setName')] = {'enabled': True, 'overloadIndex': 0, 'useName': 'API'}
        factories.apiToMelData[('DependNode', 'getName')] = {'enabled': True, 'overloadIndex': 0, 'useName': 'API'}
        # this prevents NurbsCurve from growing a deprecated `cv` method,
        # which conflicts with its cv component attribute
        factories.apiToMelData[('BezierCurve', 'cv')] = {'enabled': False, 'overloadIndex': 0, 'useName': 'API'}

        doc = factories.apiToMelData[('Attribute', 'logicalIndex')]
        doc['aliases'] = ['item', 'index']

        doc = factories.apiToMelData[('Attribute', 'elementByLogicalIndex')]
        doc['aliases'] = ['__getitem__']

        doc = factories.apiToMelData[('Attribute', 'isArray')]
        doc['aliases'] = ['isMulti']

        doc = factories.apiToMelData[('DependNode', 'isFromReferencedFile')]
        doc['aliases'] = ['isReadOnly']

        # import pymel.core, so resetter can read class source info
        import pymel.core

        # Reset modules, before import
        generator = ModuleGenerator()
        for module, _ in CORE_CMD_MODULES:
            generator.reset(module)

        generator.reset('pymel.core.windows')
        generator.reset('pymel.core.nodetypes')
        generator.reset('pymel.core.uitypes')
        generator.reset('pymel.core.datatypes')

        # "Reload" pymel.core modules, so we use the reset versions
        _deleteImportedCoreModules()
        import pymel.core

        # these are populated when core.general is imported, but they can be
        # blanked out if the factory module has been reloaded. make sure
        # they are still present
        assert {'MObject', 'MDagPath', 'MPlug'}.issubset(factories.ApiTypeRegister.inCast.keys())

        # Generate Functions
        for module, returnFunc in CORE_CMD_MODULES:
            generator.generateFunctions(module, returnFunc)

        generator.generateUIFunctions()

        generator.generateTypes(iterPyNodeText(), 'pymel.core.nodetypes', suffix='\n_addTypeNames()\n')
        generator.generateTypes(iterUIText(), 'pymel.core.uitypes', suffix='\n_addTypeNames()\n')
        generator.generateTypes(iterApiTypeText(), 'pymel.core.general')
        generator.generateTypes(iterApiDataTypeText(), 'pymel.core.datatypes')

        compileall.compile_dir(os.path.dirname(pymel.core.__file__),
                               force=True)
    finally:
        factories.building = False

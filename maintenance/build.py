import compileall
import inspect
import os.path
import sys
import types

from jinja2 import Environment, PackageLoader

import pymel.util as util
from pymel.util.conditions import Always
from pymel.internal import factories
from pymel.internal import plogging
from pymel.internal import pmcmds

_logger = plogging.getLogger(__name__)

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


def functionTemplateFactory(funcName, returnFunc=None, module=None,
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
            return "\n{newName} = _factories._addCmdDocs({origName})\n".format(
                newName=rename or funcName,
                origName=funcName)
        # no doc in runtime module
        if module.__name__ == 'pymel.core.runtime':
            return "\n{newName} = getattr(cmds, '{origName}', None)\n".format(
                newName=rename or funcName,
                origName=funcName)
        else:
            return "\n{newName} = _factories._addCmdDocs('{origName}')\n".format(
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
    _addCmdDocs(newFunc, funcName)


def _getModulePath(module):
    if isinstance(module, basestring):
        this = sys.modules[__name__]
        root = os.path.dirname(os.path.dirname(this.__file__))
        return os.path.join(root, *module.split('.')) + '.py'
    else:
        return module.__file__.rsplit('.', 1)[0] + '.py'


START_MARKER = '# ------ Do not edit below this line --------'
END_MARKER =   '# ------ Do not edit above this line --------'


def _resetModule(module):
    source = _getModulePath(module)
    with open(source, 'r') as f:
        text = f.read()

    lines = text.split('\n')

    def trim(begin):
        start = None
        for i, line in enumerate(lines[begin:]):
            i = begin + i
            if start is None and line == START_MARKER:
                start = i

            elif line == END_MARKER:
                assert start is not None
                lines[start:i + 1] = []
                return start

        # end of lines
        if start is not None:
            lines[start:] = []
        return None

    begin = 0
    while begin is not None:
        begin = trim(begin)

    lines.append(START_MARKER)

    print "writing to", source
    with open(source, 'w') as f:
        f.write('\n'.join(lines))
    return lines


def _writeToModule(new, module):
    source = _getModulePath(module)
    with open(source, 'r') as f:
        text = f.read()

    pos = text.find(START_MARKER)
    if pos != -1:
        text = text[:pos]

    text += START_MARKER + new

    print "writing to", source
    with open(source, 'w') as f:
        f.write(text)
    return text


def generateFunctions(moduleName, returnFunc=None):
    """
    Render templates for mel functions in `moduleName` into its module file.
    """
    module = sys.modules[moduleName]
    moduleShortName = moduleName.split('.')[-1]

    new = ''
    for funcName in factories.moduleCmds[moduleShortName]:
        if funcName in factories.nodeCommandList:
            new += functionTemplateFactory(funcName, returnFunc=returnFunc, module=module)
        else:
            new += functionTemplateFactory(funcName, returnFunc=None, module=module)
    _writeToModule(new, module)


def generateUIFunctions():
    new = ''
    module = sys.modules['pymel.core.windows']
    moduleShortName ='windows'

    for funcName in factories.uiClassList:
        # Create Class
        classname = util.capitalize(funcName)
        new += functionTemplateFactory(funcName,
                                       returnFunc='uitypes.' + classname,
                                       module=module, uiWidget=True)

    nonClassFuncs = set(factories.moduleCmds[moduleShortName]).difference(factories.uiClassList)
    for funcName in nonClassFuncs:
        new += functionTemplateFactory(funcName, returnFunc=None, module=module)

    new += '''
autoLayout.__doc__ = formLayout.__doc__
# Now that we've actually created all the functions, it should be safe to import
# uitypes... 
# FIXME: commented out to avoid cyclic import!!!!
# from uitypes import objectTypeUI, toQtObject, toQtLayout, toQtControl, toQtMenuItem, toQtWindow
'''
    _writeToModule(new, module)


def wrapApiMethod(apiClass, apiMethodName, newName=None, proxy=True,
                  overloadIndex=None, deprecated=False):
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


    :Parameters:

        apiClass : class
            the api class
        apiMethodName : string
            the name of the api method
        newName : string
            optionally provided if a name other than that of api method is desired
        proxy : bool
            If True, then __apimfn__ function used to retrieve the proxy class. If False,
            then we assume that the class being wrapped inherits from the underlying api class.
        overloadIndex : None or int
            which of the overloaded C++ signatures to use as the basis of our wrapped function.


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
        'argList': [(name, convertTypeArg(typ), dir, getUnit(name)) for name, typ, dir in argList],
        'classmethod': argHelper.isStatic(),
        'getterInArgs': getterInArgs,
        'proxy': proxy,
        'undoable': getterArgHelper is not None,
        'returnType': repr(convertTypeArg(returnType)) if returnType else None,
        'unitType': repr(str(unitType)) if unitType else None,
        'deprecated': deprecated,
        'signature': signature
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


class _MetaMayaCommandGenerator(object):
    _classDictKeyForMelCmd = None

    def __init__(self, classname, existingClass, parentClasses, parentMethods):
        self.classname = classname
        self.parentClassname = parentClasses[0]
        self.herited = parentMethods
        self.parentClasses = parentClasses
        self.existingClass = existingClass

    def render(self):
        attrs, methods = self.getTemplateData()

        methodNames = set(methods)
        if self.existingClass:
            # add methods that exist *directly* on the existing class
            methodNames.union(
                name for name, obj in self.existingClass.__dict__.items()
                if inspect.ismethod(obj))

        def toStr(k, v):
            if k == '__apicls__':
                return '_api.' + v.__name__
            elif k == '__melcmd__':
                return 'staticmethod(%s)' % v
            else:
                return repr(v)

        attrs = [{'name': k, 'value': toStr(k, attrs[k])} for k in sorted(attrs)]
        methods = [methods[methodName] for methodName in sorted(methods)]

        template = env.get_template('nodeclass.py')
        text = template.render(methods=methods, attrs=attrs,
                               classname=self.classname,
                               parents=self.parentClassname,
                               existing=self.existingClass is not None)
        return text, methodNames

    def getMELData(self, attrs, methods):
        """
        Add methods from MEL functions
        """
        #_logger.debug( '_MetaMayaCommandGenerator: %s' % classname )

        #-------------------------
        #   MEL Methods
        #-------------------------
        melCmdName, infoCmd = self.getMelCmd(attrs)

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

            attrs['__melcmd__'] = cmdPath
            attrs['__melcmdname__'] = melCmdName
            attrs['__melcmd_isinfo__'] = infoCmd

            # base set of disallowed methods (for MEL)
            filterAttrs = {'name', 'getName', 'setName'}
            # already created attributes for this class:
            filterAttrs.update(attrs.keys())
            # already created methods for this class:
            filterAttrs.update(methods.keys())
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
                                methods[methodName] = {
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
                                methods[methodName] = {
                                    'name': methodName,
                                    'command': melCmdName,
                                    'type': 'edit',
                                    'flag': flag,
                                    'func': cmdPath,
                                }
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))

        return attrs, methods

    def getMelCmd(self, attrs):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.

        Intended to be overridden in derived metaclasses.
        """
        raise NotImplementedError
        # return util.uncapitalize(self.classname), False

    def isMelMethod(self, methodName):
        """
        Deteremine if the passed method name exists on a parent class as a mel method
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


class MetaMayaNodeGenerator(_MetaMayaCommandGenerator):

    """ A metaclass to wrap Maya api types, with support for class constants """

    _originalApiSetAttrs = {}

    class ClassConstant(object):

        """Class constant"""

        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return '%s.%s(%s)' % (self.__class__.__module__, self.__class__.__name__, repr(self.value))

        def __str__(self):
            return self.__repr__()

        def __get__(self, instance, owner):
            # purposedly authorize notation MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None:
                # note that conversion to the correct type is done here
                return owner(self.value)
            else:
                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)

        def __set__(self, instance, value):
            raise AttributeError, "class constant cannot be set"

        def __delete__(self, instance):
            raise AttributeError, "class constant cannot be deleted"

    def __init__(self, classname, existingClass, mayaType, parentClasses, parentMethods, parentApicls):
        super(MetaMayaNodeGenerator, self).__init__(classname, existingClass, parentClasses, parentMethods)
        self.mayaType = mayaType
        self.parentApicls = parentApicls
        self.existingClass = existingClass
        self.apicls = factories.toApiFunctionSet(self.mayaType)

    def getAPIData(self, attrs, methods):
        """
        Add methods from API functions
        """

        removeAttrs = []
        # define __slots__ if not defined
        if '__slots__' not in attrs:
            attrs['__slots__'] = ()

        if self.existingClass is not None:
            try:
                apicls = self.existingClass.__dict__['apicls']
                proxy = False
            except KeyError:
                try:
                    apicls = self.existingClass.__dict__['__apicls__']
                    proxy = True
                except KeyError:
                    apicls = self.apicls
                    proxy = True

                    if self.apicls is not None:
                        attrs['__apicls__'] = self.apicls
        else:
            apicls = self.apicls
            proxy = True

        _logger.debug('MetaMayaTypeGenerator: %s: %s (proxy=%s)' % (self.classname, apicls.__name__, proxy))

        if apicls is not None:
            if apicls.__name__ not in factories.apiClassNamesToPyNodeNames:
                #_logger.debug("ADDING %s to %s" % (apicls.__name__, classname))
                factories.apiClassNamesToPyNodeNames[apicls.__name__] = self.classname

            if apicls is self.parentApicls:
                # If this class's api class is the same as the parent, the methods
                # are already handled.
                # FIXME: should this be extended to check all parent classes?
                # FIXME: assert that there is nothing explicit in the mel-api bridge
                return attrs, methods

            # if not proxy and apicls not in self.bases:
            #     #_logger.debug("ADDING BASE %s" % attrs['apicls'])
            #     bases = self.bases + (attrs['apicls'],)
            try:
                classInfo = factories.apiClassInfo[apicls.__name__]
            except KeyError:
                _logger.info("No api information for api class %s" % (apicls.__name__))
            else:
                #------------------------
                # API Wrap
                #------------------------

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
                            removeAttrs.append(methodName)
                        except KeyError:
                            basePymelName = methodName
                        pymelName, overrideData, renamed = factories._getApiOverrideNameAndData(
                            self.classname, basePymelName)


                        overloadIndex = overrideData.get('overloadIndex', None)

                        yieldTuple = (methodName, info, self.classname, pymelName,
                                      overloadIndex)

                        if overloadIndex is None:
                            #_logger.debug("%s.%s has no wrappable methods, skipping" % (apicls.__name__, methodName))
                            continue
                        if not overrideData.get('enabled', True):
                            #_logger.debug("%s.%s has been manually disabled, skipping" % (apicls.__name__, methodName))
                            # FIXME: previous versions of pymel erroneously included
                            # disabled methods on child classes which possessed the same apicls as their parent.
                            # We will deprecate them in order to allow users to transition.
                            # FIXME: add unique depcrecation message
                            if methodName in factories.EXCLUDE_METHODS:
                                continue
                            else:
                                deprecated.append(yieldTuple)
                        elif info[overloadIndex].get('deprecated', False):
                            deprecated.append(yieldTuple)
                        else:
                            yield yieldTuple + (False,)

                        if renamed:
                            # FIXME: previous versions of pymel erroneously included
                            # renamed/remapped methods on child classes which possessed the same apicls as their parent.
                            # We should include them as deprecated.
                            deprecated.append(
                                (methodName, info, self.classname,
                                 basePymelName, overloadIndex))

                    for yieldTuple in deprecated:
                        yield yieldTuple + (True,)

                for (methodName, info, classname, pymelName, overloadIndex, deprecated) \
                        in non_deprecated_methods_first():
                    assert isinstance(pymelName, str), "%s.%s: %r is not a valid name" % (classname, methodName, pymelName)

                    # TODO: some methods are being wrapped for the base class,
                    # and all their children - ie, MFnTransform.transformation()
                    # gets wrapped for Transform, Place3dTexture,
                    # HikGroundPlane, etc...
                    # Figure out why this happens, and stop it!
                    if pymelName not in self.herited and not hasattr(self.existingClass, pymelName):
                        if pymelName not in methods:
                            #_logger.debug("%s.%s autowrapping %s.%s usng proxy %r" % (classname, pymelName, apicls.__name__, methodName, proxy))
                            doc = wrapApiMethod(apicls, methodName, newName=pymelName,
                                                proxy=proxy, overloadIndex=overloadIndex,
                                                deprecated=deprecated)
                            if doc:
                                methods[pymelName] = doc
                            # else: #_logger.debug("%s.%s: wrapApiMethod failed to create method" % (apicls.__name__, methodName ))
                        # else: #_logger.debug("%s.%s: already defined, skipping" % (apicls.__name__, methodName ))
                    # else: #_logger.debug("%s.%s already herited from %s, skipping" % (apicls.__name__, methodName, herited[pymelName]))

                if 'pymelEnums' in classInfo:
                    # Enumerators

                    for enumName, enum in classInfo['pymelEnums'].items():
                        attrs[enumName] = enum

            # FIXME:
            # if not proxy:
            #     # if removeAttrs:
            #     #    #_logger.debug( "%s: removing attributes %s" % (classname, removeAttrs) )
            #     def __getattribute__(self, name):
            #         #_logger.debug(name )
            #         if name in removeAttrs and name not in factories.EXCLUDE_METHODS:  # tmp fix
            #             #_logger.debug("raising error")
            #             raise AttributeError, "'" + classname + "' object has no attribute '" + name + "'"
            #         #_logger.debug("getting from %s" % bases[0])
            #         # newcls will be defined by the time this is called...
            #         return super(newcls, self).__getattribute__(name)
            #
            #     classdict['__getattribute__'] = __getattribute__
            #
            #     if self._hasApiSetAttrBug(apicls):
            #         # correct the setAttr bug by wrapping the api's
            #         # __setattr__ to handle data descriptors...
            #         origSetAttr = apicls.__setattr__
            #         # in case we need to restore the original setattr later...
            #         # ... as we do in a test for this bug!
            #         self._originalApiSetAttrs[apicls] = origSetAttr
            #
            #         def apiSetAttrWrap(self, name, value):
            #             if hasattr(self.__class__, name):
            #                 if hasattr(getattr(self.__class__, name), '__set__'):
            #                     # we've got a data descriptor with a __set__...
            #                     # don't use the apicls's __setattr__
            #                     return super(apicls, self).__setattr__(name, value)
            #             return origSetAttr(self, name, value)
            #         apicls.__setattr__ = apiSetAttrWrap

        # shortcut for ensuring that our class constants are the same type as the class we are creating
        def makeClassConstant(attr):
            try:
                # return MetaMayaTypeGenerator.ClassConstant(newcls(attr))
                return MetaMayaNodeGenerator.ClassConstant(attr)
            except Exception, e:
                _logger.warn("Failed creating %s class constant (%s): %s" % (classname, attr, e))
        #------------------------
        # Class Constants
        #------------------------
        # FIXME:
        # if hasattr(newcls, 'apicls'):
        #     # type (api type) used for the storage of data
        #     apicls = newcls.apicls
        #     if apicls is not None:
        #         # build some constants on the class
        #         constant = {}
        #         # constants in class definition will be converted from api class to created class
        #         for name, attr in newcls.__dict__.iteritems():
        #             # to add the wrapped api class constants as attributes on the wrapping class,
        #             # convert them to own class
        #             if isinstance(attr, apicls):
        #                 if name not in constant:
        #                     constant[name] = makeClassConstant(attr)
        #         # we'll need the api clas dict to automate some of the wrapping
        #         # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping
        #         apiDict = dict(inspect.getmembers(apicls))
        #         # defining class properties on the created class
        #         for name, attr in apiDict.iteritems():
        #             # to add the wrapped api class constants as attributes on the wrapping class,
        #             # convert them to own class
        #             if isinstance(attr, apicls):
        #                 if name not in constant:
        #                     constant[name] = makeClassConstant(attr)
        #         # update the constant dict with herited constants
        #         mro = inspect.getmro(newcls)
        #         for parentCls in mro:
        #             if isinstance(parentCls, MetaMayaTypeGenerator):
        #                 for name, attr in parentCls.__dict__.iteritems():
        #                     if isinstance(attr, MetaMayaTypeGenerator.ClassConstant):
        #                         if not name in constant:
        #                             constant[name] = makeClassConstant(attr.value)
        #
        #         # store constants as class attributes
        #         for name, attr in constant.iteritems():
        #             type.__setattr__(newcls, name, attr)
        #
        #     # else :   raise TypeError, "must define 'apicls' in the class definition (which Maya API class to wrap)"
        #
        # if hasattr(newcls, 'apicls') and not ApiTypeRegister.isRegistered(newcls.apicls.__name__):
        #     ApiTypeRegister.register(newcls.apicls.__name__, newcls)

        return attrs, methods

    def _hasApiSetAttrBug(self, apiClass):
        """
        Maya has a bug on windows where some api objects have a __setattr__
        that bypasses properties (and other data descriptors).

        This tests if the given apiClass has such a bug.
        """
        class MyClass1(object):

            def __init__(self):
                self._bar = 'not set'

            def _setBar(self, val):
                self._bar = val

            def _getBar(self):
                return self._bar
            bar = property(_getBar, _setBar)

        class MyClass2(MyClass1, apiClass):
            pass

        foo2 = MyClass2()
        foo2.bar = 7
        # Here, on windows, MMatrix's __setattr__ takes over, and
        # (after presumabably determining it didn't need to do
        # whatever special case thing it was designed to do)
        # instead of calling the super's __setattr__, which would
        # use the property, inserts it into the object's __dict__
        # manually
        if foo2.bar != 7:
            return True

        # Starting in Maya2018 (at least on windows?), many wrapped datatypes
        # define a __setattr__ which will work in the "general" case tested
        # above, but will still take precedence if a "_swig_property" is
        # defined - ie, MEulerRotation.order.  Check to see if the apicls has
        # any properties, and ensure that our property still overrides theirs...
        for name, member in inspect.getmembers(apiClass,
                                               lambda x: isinstance(x, property)):
            setattr(MyClass1, name, MyClass1.__dict__['bar'])
            try:
                setattr(foo2, name, 1.23456)
            except Exception:
                return True
            if getattr(foo2, name) != 1.23456:
                return True
            # only check for one property - we assume that all apicls properties
            # will behave the same way...
            break
        return False

    def getTemplateData(self, attrs=None, methods=None):
        if attrs is None:
            attrs = {}
        if methods is None:
            methods = {}

        attrs['__melnode__'] = self.mayaType

        # FIXME:
        isVirtual = False
        # isVirtual = '_isVirtual' in attrs or any(hasattr(b, '_isVirtual')
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
        #     attrs['__melnode__'] = nodeType

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
        attrs, methods = self.getAPIData(attrs, methods)
        # next, populate MEL methods
        attrs, methods = self.getMELData(attrs, methods)
        return attrs, methods

        # FIXME:
        # PyNodeType = super(MetaMayaNodeGenerator, self).render()
        # ParentPyNode = [x for x in bases if issubclass(x, util.ProxyUnicode)]
        # assert len(ParentPyNode), "%s did not have exactly one parent PyNode: %s (%s)" % (self.classname, ParentPyNode, self.bases)
        # factories.addPyNodeType(PyNodeType, ParentPyNode)
        # return PyNodeType

    def getMelCmd(self, attrs):
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


class MetaMayaUIGenerator(_MetaMayaCommandGenerator):

    """
    A metaclass for creating classes based on on a maya UI type/command.
    """

    def getTemplateData(self, attrs=None, methods=None):
        if attrs is None:
            attrs = {}
        if methods is None:
            methods = {}

        # If the class explicitly gives it's mel ui command name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        attrs.setdefault('__melui__', util.uncapitalize(self.classname))

        # TODO: implement a option at the cmdlist level that triggers listForNone
        # TODO: create labelArray for *Grp ui elements, which passes to the correct arg ( labelArray3, labelArray4, etc ) based on length of passed array
        attrs, methods = self.getMELData(attrs, methods)
        return attrs, methods

    def getMelCmd(self, attrs):
        return attrs['__melui__'], False


def getPyNodeGenerator(mayaType, parentMayaTypes, parentMethods, parentApicls):
    """
    create a PyNode type for a maya node.

    Parameters
    ----------
    mayaType : str
    parentMayaTypes : List[str]
    """
    import pymel.core.nodetypes as nt

    def getPymelTypeName(mayaTypeName):
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
    pyNodeTypeName = getPymelTypeName(mayaType)
    existingClass = getattr(nt, pyNodeTypeName, None)
    if existingClass and hasattr(existingClass, '__metaclass__'):
        return None

    return MetaMayaNodeGenerator(pyNodeTypeName, existingClass, mayaType,
                                 parentPymelTypes, parentMethods, parentApicls)


def iterPyNodeText():
    import pymel.core.general

    # Generate Classes
    heritedMethods = {
        'general.PyNode': set(
            name for name, obj in inspect.getmembers(pymel.core.general.PyNode)
            if inspect.ismethod(obj))
    }
    apiClasses = {
        'general.PyNode': None
    }

    for mayaType, parents, children in factories.nodeHierarchy:

        if mayaType == 'dependNode':
            # This seems like the more 'correct' way of doing it - only node types
            # that are currently available have PyNodes created for them - but
            # changing it so some PyNodes are no longer available until their
            # plugin is loaded may create backwards incompatibility issues...
            #        if (mayaType == 'dependNode'
            #                or mayaType not in _factories.mayaTypesToApiTypes):
            # FIXME: temporarily enabling dependNode
            #continue
            parents = ['general.PyNode']

        parentMayaType = parents[0]
        if parentMayaType is None:
            _logger.warning("could not find parent node: %s", mayaType)
            continue

        if factories.isMayaType(mayaType) or mayaType == 'dependNode':
            parentMethods = heritedMethods[parentMayaType]
            parentApicls = apiClasses[parentMayaType]
            template = getPyNodeGenerator(mayaType, parents, parentMethods, parentApicls)
            if template:
                text, methods = template.render()
                yield text, template
                heritedMethods[mayaType] = parentMethods.union(methods)
                apiClasses[mayaType] = template.apicls


def iterUIText():
    import pymel.core.uitypes

    heritedMethods = {}

    for funcName in factories.uiClassList:
        # Create Class
        classname = util.capitalize(funcName)
        if classname == 'MenuItem':
            # FIXME: !!!
            continue

        existingClass = getattr(pymel.core.uitypes, classname, None)

        if classname.endswith(('Layout', 'Grp')):
            base = 'Layout'
        elif classname.endswith('Panel'):
            base = 'Panel'
        else:
            base = 'PyUI'

        template = MetaMayaUIGenerator(classname, existingClass, [base], set())
        text, methods = template.render()
        yield text, template
        # heritedMethods[mayaType] = parentMethods.union(methods)


def generateTypes(lines, iterator, module):
    # tally of additions made in middle of codde
    offsets = {}

    def computeOffset(start):
        result = 0
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

            try:
                srclines, startline = inspect.getsourcelines(template.existingClass)
            except IOError:
                print template.existingClass, dir(template.existingClass)
                raise

            endline = startline + len(srclines) - 1

            endline += computeOffset(startline)
            newlines = [START_MARKER] + newlines + [END_MARKER]
            lines[endline:endline] = newlines
            offsets[startline] = len(newlines)
        else:
            lines += newlines

    source = _getModulePath(module)

    text = '\n'.join(lines)

    text += '''
_addTypeNames()
    '''
    print "writing to", source
    with open(source, 'w') as f:
        f.write(text)


def generateAll():
    factories.building = True
    try:
        # Reset modules, before import
        for module, _ in CORE_CMD_MODULES:
            _resetModule(module)

        _resetModule('pymel.core.uitypes')
        _resetModule('pymel.core.windows')

        nodeLines = _resetModule('pymel.core.nodetypes')
        uiLines = _resetModule('pymel.core.uitypes')

        # Import to populate existing objects
        import pymel.core

        # these are populated by core.general and can be blanked when reloading factory module
        assert {'MObject', 'MDagPath', 'MPlug'}.issubset(factories.ApiTypeRegister.inCast.keys())

        # Generate Functions
        for module, returnFunc in CORE_CMD_MODULES:
            generateFunctions(module, returnFunc)

        generateUIFunctions()

        generateTypes(nodeLines, iterPyNodeText(), 'pymel.core.nodetypes')
        generateTypes(uiLines, iterUIText(), 'pymel.core.uitypes')

        compileall.compile_dir(os.path.dirname(pymel.core.__file__))
    finally:
        factories.building = False

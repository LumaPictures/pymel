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

env = Environment(loader=PackageLoader('maintenance', 'templates'),
                  trim_blocks=True, lstrip_blocks=True)


def importableName(func, module=None):
    try:
        name = func.__name__
    except AttributeError:
        name = func.__class__.__name__

    if func.__module__ == '__builtin__':
        path = name
    else:
        path = "{}.{}".format(
            module or func.__module__,
            name
        )
    return path


def _setRepr(s):
    return '{' + ', '.join([repr(s) for s in sorted(s)]) + '}'


def _listRepr(s):
    return '[' + ', '.join([repr(s) for s in sorted(s)]) + ']'


def functionTemplateFactory(funcNameOrObject, returnFunc=None, module=None,
                            rename=None, uiWidget=False):
    """
    create a new function, apply the given returnFunc to the results (if any)
    Use pre-parsed command documentation to add to __doc__ strings for the
    command.
    """

    # if module is None:
    #   module = _thisModule
    inFunc, funcName, customFunc = factories._getSourceFunction(funcNameOrObject, module)
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

    resultNeedsUnpacking = cmdInfo.get('resultNeedsUnpacking', False)
    callbackFlags = cmdInfo.get('callbackFlags', None)
    if callbackFlags:
        callbackFlags = _listRepr(callbackFlags)
    wrapped = funcName in factories.simpleCommandWraps
    if any([timeRangeFlags, returnFunc, resultNeedsUnpacking, unpackFlags, wrapped, callbackFlags]):
        if inFunc is not None:
            sourceFuncName = importableName(inFunc)
            sourceFuncName = sourceFuncName.replace('pymel.internal.pmcmds.', 'cmds.')
        else:
            sourceFuncName = None

        template = env.get_template('commandfunc.py')
        return template.render(
            funcName=rename or funcName,
            commandName=funcName, timeRangeFlags=timeRangeFlags,
            sourceFuncName=sourceFuncName,
            returnFunc=returnFunc,
            resultNeedsUnpacking=resultNeedsUnpacking,
            unpackFlags=unpackFlags,
            simpleWraps=wrapped,
            callbackFlags=callbackFlags, uiWidget=uiWidget).encode()
    else:
        # bind the
        return '\n{newName} = _factories._addCmdDocs(cmds.{origName})\n'.format(
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


def _writeToModule(new, module):
    if new:
        if isinstance(module, basestring):
            this = sys.modules[__name__]
            root = os.path.dirname(os.path.dirname(this.__file__))
            source = os.path.join(root, *module.split('.')) + '.py'
        else:
            source = module.__file__.rsplit('.', 1)[0] + '.py'

        if os.path.exists(source):
            with open(source, 'r') as f:
                text = f.read()
        else:
            text = ''

        marker = '# ------ Do not edit below this line --------'

        pos = text.find(marker)
        if pos != -1:
            text = text[:pos]

        text += marker + new

        print "writing to", source
        with open(source, 'w') as f:
            f.write(text)


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
from uitypes import objectTypeUI, toQtObject, toQtLayout, toQtControl, toQtMenuItem, toQtWindow
'''
    _writeToModule(new, module)


def generateAllFunctions():
    """
    Render templates for all mel functions into their respective module files.
    """
    generateFunctions('pymel.core.animation', '_general.PyNode')
    generateFunctions('pymel.core.context')
    generateFunctions('pymel.core.effects', '_general.PyNode')
    generateFunctions('pymel.core.general', 'PyNode')
    generateFunctions('pymel.core.language')
    generateFunctions('pymel.core.modeling', '_general.PyNode')
    generateFunctions('pymel.core.other')
    generateFunctions('pymel.core.rendering', '_general.PyNode')
    generateFunctions('pymel.core.runtime')
    generateFunctions('pymel.core.system')
    generateUIFunctions()


def wrapApiMethod(apiClass, apiMethodName, newName=None, proxy=True, overloadIndex=None, deprecated=False):
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

    signature = util.format_signature(['self'] + inArgs, defaults=defaults)

    def convert(t):
        if isinstance(t, tuple):  # apiEnum
            return tuple(t)
        else:
            return str(t)

    return {
        'type': 'api',
        'name': newName,
        'apiName': apiMethodName,
        'apiClass': apiClassName,
        'getter': pymelName,
        'overloadIndex': overloadIndex,
        'inArgs': ', '.join(inArgs),
        'outArgs': outArgs,
        'argList': [(name, convert(typ), dir) for name, typ, dir in argList],
        'classmethod': argHelper.isStatic(),
        'getterInArgs': getterInArgs,
        'proxy': proxy,
        'undoable': getterArgHelper is not None,
        'returnType': argHelper.methodInfo['returnType'],
        'unitType': argHelper.methodInfo['returnInfo'].get('unitType', None),
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
        beforeDeprecationWrapper = wrappedApiFunc

        def wrappedApiFunc(*args, **kwargs):
            import warnings
            warnings.warn("{} is deprecated".format(methodDesc),
                          DeprecationWarning, stacklevel=2)
            return beforeDeprecationWrapper(*args, **kwargs)
    return wrappedApiFunc


class MetaMayaTypeWrapper(object):

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

    def __init__(self, classname, parentClassname, parentMethods, parentApicls):
        self.classname = classname
        self.parentClassname = parentClassname
        self.herited = parentMethods
        self.parentApicls = parentApicls

    def getTemplateData(self, attrs, methods):
        """ Create a new class of metaClassConstants type """

        removeAttrs = []
        # define __slots__ if not defined
        if '__slots__' not in attrs:
            attrs['__slots__'] = ()
        try:
            apicls = attrs['apicls']
            proxy = False
            raise ValueError("This doesn't seem to be supported any more")
        except KeyError:
            try:
                apicls = attrs['__apicls__']
                proxy = True
            except KeyError:
                apicls = None

        _logger.debug('MetaMayaTypeWrapper: %s: %s (proxy=%s)' % (self.classname, apicls.__name__, proxy))

        if apicls is not None:
            if apicls.__name__ not in factories.apiClassNamesToPyNodeNames:
                #_logger.debug("ADDING %s to %s" % (apicls.__name__, classname))
                factories.apiClassNamesToPyNodeNames[apicls.__name__] = self.classname

            if apicls is self.parentApicls:
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
                            pymelName = info[0]['pymelName']
                            removeAttrs.append(methodName)
                        except KeyError:
                            pymelName = methodName
                        pymelName, overrideData = factories._getApiOverrideNameAndData(
                            self.classname, pymelName)

                        # if classname == 'DependNode' and pymelName in ('setName','getName'):
                        #                        raise Exception('debug')

                        overloadIndex = overrideData.get('overloadIndex', None)

                        yieldTuple = (methodName, info, self.classname, pymelName,
                                      overloadIndex)

                        if overloadIndex is None:
                            #_logger.debug("%s.%s has no wrappable methods, skipping" % (apicls.__name__, methodName))
                            # FIXME: previous versions of pymel erroneously included
                            # renamed/remapped methods on child classes which possessed the same apicls as their parent.
                            # We should include them as deprecated.
                            continue
                        if not overrideData.get('enabled', True):
                            #_logger.debug("%s.%s has been manually disabled, skipping" % (apicls.__name__, methodName))
                            # FIXME: previous versions of pymel erroneously included
                            # disabled methods on child classes which possessed the same apicls as their parent.
                            # We will deprecate them in order to allow users to transition.
                            # FIXME: determine if methods in factories.EXCLUDE_METHODS were ever added
                            # FIXME: add unique depcrecation message
                            deprecated.append(yieldTuple)
                        elif info[overloadIndex].get('deprecated', False):
                            deprecated.append(yieldTuple)
                        else:
                            yield yieldTuple + (False,)
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
                    if pymelName not in self.herited:
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
                # return MetaMayaTypeWrapper.ClassConstant(newcls(attr))
                return MetaMayaTypeWrapper.ClassConstant(attr)
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
        #             if isinstance(parentCls, MetaMayaTypeWrapper):
        #                 for name, attr in parentCls.__dict__.iteritems():
        #                     if isinstance(attr, MetaMayaTypeWrapper.ClassConstant):
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


class _MetaMayaCommandWrapper(MetaMayaTypeWrapper):

    """
    A metaclass for creating classes based on a maya command.

    Not intended to be used directly; instead, use the descendants: MetaMayaNodeWrapper, MetaMayaUIWrapper
    """

    _classDictKeyForMelCmd = None

    def getTemplateData(self, attrs, methods):
        #_logger.debug( '_MetaMayaCommandWrapper: %s' % classname )

        attrs, methods = super(_MetaMayaCommandWrapper, self).getTemplateData(attrs, methods)

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
            pmSourceFunc = False
            try:
                cmdModule = __import__('pymel.core.' + cmdInfo['type'], globals(), locals(), [''])
                func = getattr(cmdModule, melCmdName)
                pmSourceFunc = True
            except (AttributeError, TypeError):
                func = getattr(pmcmds, melCmdName)

            # add documentation
            # classdict['__doc__'] = util.LazyDocString((newcls, self.docstring, (melCmdName,), {}))
            # classdict['__melcmd__'] = staticmethod(func)
            attrs['__melcmdname__'] = melCmdName
            attrs['__melcmd_isinfo__'] = infoCmd

            filterAttrs = {'name', 'getName', 'setName'}.union(attrs.keys())
            filterAttrs.update(factories.overrideMethods.get(self.parentClassname, []))

            # parentClasses = [x.__name__ for x in inspect.getmro(newcls)[1:]]
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

                        if methodName not in filterAttrs: # and \
                                #(not hasattr(newcls, methodName) or self.isMelMethod(methodName, parentClasses)):

                            # 'enabled' refers to whether the API version of this method will be used.
                            # if the method is enabled that means we skip it here.
                            if (not factories.apiToMelData.has_key((self.classname, methodName))
                                    or factories.apiToMelData[(self.classname, methodName)].get('melEnabled', False)
                                    or not factories.apiToMelData[(self.classname, methodName)].get('enabled', True)):
                                returnFunc = None

                                if flagInfo.get('resultNeedsCasting', False):
                                    returnFunc = flagInfo['args']

                                # don't unpack if the source i
                                if (flagInfo.get('resultNeedsUnpacking', False)
                                        and not pmSourceFunc):
                                    if returnFunc:
                                        # can't do:
                                        #   returnFunc = lambda x: returnFunc(x[0])
                                        # ... as this would create a recursive function!
                                        origReturnFunc = returnFunc
                                        returnFunc = lambda x: origReturnFunc(x[0])
                                    else:
                                        returnFunc = lambda x: x[0]

                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                methods[methodName] = {
                                    'name': methodName,
                                    'command': pmcmds.getCmdName(func),
                                    'type': 'query',
                                    'flag': flag,
                                    'returnFunc': importableName(returnFunc) if returnFunc else None
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

                        if methodName not in filterAttrs: # and \
                                #(not hasattr(newcls, methodName) or self.isMelMethod(methodName, parentClasses)):
                            if not factories.apiToMelData.has_key((self.classname, methodName)) \
                                    or factories.apiToMelData[(self.classname, methodName)].get('melEnabled', False) \
                                    or not factories.apiToMelData[(self.classname, methodName)].get('enabled', True):

                                # FIXME: shouldn't we be able to use the wrapped pymel command, which is already fixed?
                                # FIXME: the 2nd argument is wrong, so I think this is broken
                                # fixedFunc = fixCallbacks(func, melCmdName)

                                #_logger.debug("Adding mel derived method %s.%s()" % (classname, methodName))
                                methods[methodName] = {
                                    'name': methodName,
                                    'command': pmcmds.getCmdName(func),
                                    'type': 'edit',
                                    'flag': flag,
                                }
                            # else: #_logger.debug(("skipping mel derived method %s.%s(): manually disabled" % (classname, methodName)))
                        # else: #_logger.debug(("skipping mel derived method %s.%s(): already exists" % (classname, methodName)))

        return attrs, methods

    def getMelCmd(self, attrs):
        """
        Retrieves the name of the mel command the generated class wraps, and whether it is an info command.

        Intended to be overridden in derived metaclasses.
        """
        return util.uncapitalize(self.classname), False

    def isMelMethod(self, methodName, parentClassList):
        """
        Deteremine if the passed method name exists on a parent class as a mel method
        """
        for classname in parentClassList:
            if methodName in factories.classToMelMap[classname]:
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


class MetaMayaNodeWrapper(_MetaMayaCommandWrapper):

    """
    A metaclass for creating classes based on node type.  Methods will be added to the new classes
    based on info parsed from the docs on their command counterparts.
    """
    def render(self, attrs=None, methods=None):
        if attrs is None:
            attrs = {}
        if methods is None:
            methods = {}

        # If the class explicitly gives it's mel node name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        #_logger.debug( 'MetaMayaNodeWrapper: %s' % classname )
        nodeType = attrs.get('__melnode__')

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
            pymelTypeNameToMayaTypeName[self.classname] = nodeType
        elif oldMayaType != nodeType:
            _logger.raiseLog(_logger.WARNING,
                             'creating new pymel node class %r for maya node '
                             'type %r, but a pymel class with the same name '
                             'already existed for maya node type %r' % (
                                 self.classname, nodeType, oldMayaType))

        # mapping from maya type to pymel type only happens if it's NOT a
        # virtual class...
        if not isVirtual:
            oldPymelType = mayaTypeNameToPymelTypeName.get(nodeType)
            if oldPymelType is None:
                mayaTypeNameToPymelTypeName[nodeType] = self.classname
            elif oldPymelType != self.classname:
                _logger.raiseLog(_logger.WARNING,
                                 'creating new pymel node class %r for maya node '
                                 'type %r, but there already existed a pymel'
                                 'class %r for the same maya node type' % (
                                     self.classname, nodeType, oldPymelType))

        factories.addMayaType(nodeType)
        apicls = factories.toApiFunctionSet(nodeType)
        if apicls is not None:
            attrs['__apicls__'] = apicls

        attrs, methods = self.getTemplateData(attrs, methods)
        methodNames = set(methods)

        def toStr(k, v):
            if k == '__apicls__':
                return '_api.' + v.__name__
            else:
                return repr(v)

        attrs = [{'name': k, 'value': toStr(k, attrs[k])} for k in sorted(attrs)]
        methods = [methods[methodName] for methodName in sorted(methods)]

        template = env.get_template('nodeclass.py')
        text = template.render(methods=methods, attrs=attrs,
                               classname=self.classname,
                               parents=self.parentClassname)
        return text, methodNames, apicls
        # FIXME:
        # PyNodeType = super(MetaMayaNodeWrapper, self).render()
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
        nodeType = attrs['__melnode__']
        infoCmd = False
        try:
            nodeCmd = factories.cmdcache.nodeTypeToNodeCommand[nodeType]
        except KeyError:
            try:
                nodeCmd = factories.nodeTypeToInfoCommand[nodeType]
                infoCmd = True
            except KeyError:
                nodeCmd = nodeType
        return nodeCmd, infoCmd


class MetaMayaUIWrapper(_MetaMayaCommandWrapper):

    """
    A metaclass for creating classes based on on a maya UI type/command.
    """

    def getTemplateData(self, attrs, methods):
        # If the class explicitly gives it's mel ui command name, use that - otherwise, assume it's
        # the name of the PyNode, uncapitalized
        attrs.setdefault('__melui__', util.uncapitalize(self.classname))

        # TODO: implement a option at the cmdlist level that triggers listForNone
        # TODO: create labelArray for *Grp ui elements, which passes to the correct arg ( labelArray3, labelArray4, etc ) based on length of passed array

        return super(MetaMayaUIWrapper, self).getTemplateData(attrs, methods)

    def getMelCmd(self, attrs):
        return attrs['__melui__'], False


def generatePyNode(dynModule, mayaType, parentMayaType, parentMethods, parentApicls, extraAttrs=None):
    """
    create a PyNode type for a maya node.

    Parameters
    ----------
    mayaType : str
    parentMayaType : str
    """
    # dynModule is generally pymel.core.nodetypes, but don't want to rely on
    # that for pymel.core.nodetypes.mayaTypeNameToPymelTypeName...
    from pymel.core.nodetypes import mayaTypeNameToPymelTypeName,\
        pymelTypeNameToMayaTypeName

    def getPymelTypeName(mayaTypeName):
        pymelTypeName = mayaTypeNameToPymelTypeName.get(mayaTypeName)
        if pymelTypeName is None:
            pymelTypeName = str(util.capitalize(mayaTypeName))
            pymelTypeNameBase = pymelTypeName
            num = 1
            while pymelTypeName in pymelTypeNameToMayaTypeName:
                num += 1
                pymelTypeName = pymelTypeNameBase + str(num)
            mayaTypeNameToPymelTypeName[mayaTypeName] = pymelTypeName
            pymelTypeNameToMayaTypeName[pymelTypeName] = mayaTypeName
        return pymelTypeName

    if parentMayaType == 'general.PyNode':
        parentPyNodeTypeName = 'general.PyNode'
    else:
        # unicode is not liked by metaNode
        parentPyNodeTypeName = mayaTypeNameToPymelTypeName.get(parentMayaType)
        if parentPyNodeTypeName is None:
            # FIXME:
            # _logger.raiseLog(_logger.WARNING,
            #                  'trying to create PyNode for maya type %r, but could'
            #                  ' not find a registered PyNode for parent type %r' % (
            #                      mayaType, parentMayaType))
            parentPyNodeTypeName = str(util.capitalize(parentMayaType))
    pyNodeTypeName = getPymelTypeName(mayaType)

    classDict = {'__melnode__': mayaType}
    if extraAttrs:
        classDict.update(extraAttrs)

    template = MetaMayaNodeWrapper(pyNodeTypeName, parentPyNodeTypeName, parentMethods, parentApicls)
    return template.render(classDict)


def generatePyNodes():
    #submodules = ('transform', 'shadingDependNode', 'shape', 'abstractBaseCreate', 'polyBase', 'dependNode')

    code = ''

    heritedMethods = {
        'general.PyNode': set()
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
            text, methods, apicls = generatePyNode(None, mayaType, parentMayaType, parentMethods, parentApicls)
            code += text
            heritedMethods[mayaType] = parentMethods.union(methods)
            apiClasses[mayaType] = apicls

    _writeToModule(code, 'pymel.core.nodetypes')

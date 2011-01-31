"""
Defines common types and type related utilities:  Singleton, etc.
These types can be shared by other utils modules and imported into util main namespace for use by other pymel modules
"""

import inspect, types, operator, sys, warnings

class Singleton(type):
    """ Metaclass for Singleton classes.

        >>> class DictSingleton(dict) :
        ...    __metaclass__ = Singleton
        ...
        >>> DictSingleton({'A':1})
        {'A': 1}
        >>> a = DictSingleton()
        >>> a
        {'A': 1}
        >>> b = DictSingleton({'B':2})
        >>> a, b, DictSingleton()
        ({'B': 2}, {'B': 2}, {'B': 2})
        >>> a is b and a is DictSingleton()
        True

        >>> class StringSingleton(str) :
        ...    __metaclass__ = Singleton
        ...
        >>> StringSingleton("first")
        'first'
        >>> a = StringSingleton()
        >>> a
        'first'
        >>> b = StringSingleton("changed")
        >>> a, b, StringSingleton()
        ('first', 'first', 'first')
        >>> a is b and a is StringSingleton()
        True

        >>> class DictSingleton2(DictSingleton):
        ...     pass
        ...
        >>> DictSingleton2({'A':1})
        {'A': 1}
        >>> a = DictSingleton2()
        >>> a
        {'A': 1}
        >>> b = DictSingleton2({'B':2})
        >>> a, b, DictSingleton2()
        ({'B': 2}, {'B': 2}, {'B': 2})
        >>> a is b and a is DictSingleton2()
        True

    """
    def __new__(mcl, classname, bases, classdict):

        # newcls =  super(Singleton, mcl).__new__(mcl, classname, bases, classdict)

        # redefine __new__
        def __new__(cls, *p, **k):
            if '_the_instance' not in cls.__dict__:
                cls._the_instance = super(newcls, cls).__new__(cls, *p, **k)
            return cls._the_instance
        newdict = { '__new__': __new__}
        # define __init__ if it has not been defined in the class being created
        def __init__(self, *p, **k):
            cls = self.__class__
            if p :
                if hasattr(self, 'clear') :
                    self.clear()
                else :
                    super(newcls, self).__init__()
                super(newcls, self).__init__(*p, **k)
        if '__init__' not in classdict :
            newdict['__init__'] = __init__
        # Note: could have defined the __new__ method like it is done in Singleton but it's as easy to derive from it
        for k in classdict :
            if k in newdict :
                warnings.warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
            else :
                newdict[k] = classdict[k]

        newcls =  super(Singleton, mcl).__new__(mcl, classname, bases, newdict)

        return newcls

class metaStatic(Singleton) :
    """ A static (immutable) Singleton metaclass to quickly build classes
        holding predefined immutable dicts

        >>> class FrozenDictSingleton(dict) :
        ...    __metaclass__ = metaStatic
        ...
        >>> FrozenDictSingleton({'A':1})
        {'A': 1}
        >>> a = FrozenDictSingleton()
        >>> a
        {'A': 1}
        >>> b = FrozenDictSingleton()
        >>> a, b
        ({'A': 1}, {'A': 1})
        >>> a is b
        True

        >>> b = FrozenDictSingleton({'B':2})
        Traceback (most recent call last):
            ...
        TypeError: 'FrozenDictSingleton' object does not support redefinition

        >>> a['A']
        1
        >>> a['A'] = 2   #doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: '<class '...FrozenDictSingleton'>' object does not support item assignation

        >>> a.clear()
        Traceback (most recent call last):
            ...
        AttributeError: 'FrozenDictSingleton' object has no attribute 'clear'

        >>> a, b, FrozenDictSingleton()
        ({'A': 1}, {'A': 1}, {'A': 1})
        >>> a is b and a is FrozenDictSingleton()
        True

        >>> class StaticTest(FrozenDictSingleton):
        ...     pass
        ...
        >>> StaticTest({'A': 1})
        {'A': 1}
        >>> a = StaticTest()
        >>> a
        {'A': 1}
        >>> b = StaticTest()
        >>> a, b
        ({'A': 1}, {'A': 1})

        >>> class StaticTest2( StaticTest ):
        ...     pass
        ...
        >>> StaticTest2({'B': 2})
        {'B': 2}
        >>> a = StaticTest2()
        >>> a
        {'B': 2}
        >>> b = StaticTest2()
        >>> a, b
        ({'B': 2}, {'B': 2})

    """
    def __new__(mcl, classname, bases, classdict):
        """
        """
        # redefine __init__
        def __init__(self, *p, **k):
            cls = self.__class__
            # Can only create once)
            if p :
                # Can only init once
                if not self:
                    return super(newcls, self).__init__(*p, **k)
                else :
                    raise TypeError, "'"+classname+"' object does not support redefinition"
        newdict = { '__init__':__init__}
        # hide methods with might herit from a mutable base
        def __getattribute__(self, name):
            if name in newcls._hide :
                raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'"
            else :
                return super(newcls, self).__getattribute__(name)
        newdict['__getattribute__'] = __getattribute__
        _hide = ('clear', 'update', 'pop', 'popitem', '__setitem__', '__delitem__', 'append', 'extend' )
        newdict['_hide'] = _hide
        # prevent item assignation or deletion
        def __setitem__(self, key, value) :
            raise TypeError, "'%s' object does not support item assignation" % (self.__class__)
        newdict['__setitem__'] = __setitem__
        def __delitem__(self, key):
            raise TypeError, "'%s' object does not support item deletion" % (self.__class__)
        newdict['__delitem__'] = __delitem__
        # Now add methods of the defined class, as long as it doesn't try to redefine
        # Note: could have defined the __new__ method like it is done in Singleton but it's as easy to derive from it
        for k in classdict :
            if k in newdict :
                warnings.warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
            else :
                newdict[k] = classdict[k]

        newcls = super(metaStatic, mcl).__new__(mcl, classname, bases, newdict)

        return newcls

try:
    from collections import defaultdict
except:
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)
        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value
        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.iteritems()
        def copy(self):
            return self.__copy__()
        def __copy__(self):
            return type(self)(self.default_factory, self)
        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))

        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))

class defaultlist(list):

    def __init__(self, default_factory, *args, **kwargs ):
        if (default_factory is not None and
            not hasattr(default_factory, '__call__')):
            raise TypeError('first argument must be callable')
        list.__init__(self,*args, **kwargs)
        self.default_factory = default_factory

    def __setitem__( self, index, item ):
        try:
            list.__setitem__(self, index, item)
        except IndexError:
            diff = index - len(self) - 1
            assert diff > 0
            self.extend( [self.default_factory() ] * diff + [item] )

    def __getitem__(self, index):
        try:
            return list.__getitem__(self, index)
        except IndexError:
            return self.default_factory()


class ModuleInterceptor(object):
    """
    This class is used to intercept an unset attribute of a module to perfrom a callback. The
    callback will only be performed if the attribute does not exist on the module. Any error raised
    in the callback will cause the original AttributeError to be raised.

        def cb( module, attr):
             if attr == 'this':
                 print "intercepted"
             else:
                 raise ValueError
        import sys
        sys.modules[__name__] = ModuleInterceptor(__name__, cb)
        intercepted

    The class does not work when imported into the main namespace.
    """
    def __init__(self, moduleName, callback):
        self.module = __import__( moduleName , globals(), locals(), [''] )
        self.callback = callback
    def __getattr__(self, attr):
        try:
            return getattr(self.module, attr)
        except AttributeError, msg:
            try:
                self.callback( self.module, attr)
            except:
                raise AttributeError, msg

# read only decorator
def readonly(f) :
    """ Marks a class member as protected, allowing metaProtected to prevent re-assignation on the classes it generates """
    f.__readonly__ = None
    return f

class metaReadOnlyAttr(type) :
    """ A metaclass to allow to define read-only class attributes, accessible either on the class or it's instances
        and protected against re-write or re-definition.
        Read only attributes are stored in the class '__readonly__' dictionary.
        Any attribute can be marked as read only by including its name in a tuple named '__readonly__' in the class
        definition. Alternatively methods can be marked as read only with the @readonly decorator and will then get
        added to the dictionary at class creation """

    def __setattr__(cls, name, value):
        """ overload __setattr__ to forbid modification of read only class info """
        readonly = {}
        for c in inspect.getmro(cls) :
            if hasattr(c, '__readonly__') :
                readonly.update(c.__readonly__)
        if name in readonly :
            raise AttributeError, "attribute %s is a read only class attribute and cannot be modified on class %s" % (name, cls.__name__)
        else :
            super(metaReadOnlyAttr, cls).__setattr__(name, value)


    def __new__(mcl, classname, bases, classdict):
        """ Create a new metaReadOnlyAttr class """

        # checks for protected members, in base classes on in class to be created
        readonly = {}
        # check for protected members in class definition
        if '__readonly__' in classdict :
            readonly.update(dict((a, None) for a in classdict['__readonly__']))
        for a in classdict :
            if hasattr(classdict[a], '__readonly__') :
                readonly[a] = None
        readonly['__readonly__'] = None
        classdict['__readonly__'] = readonly

        # the use of __slots__ protects instance attributes
#        slots = []
#        if '__slots__' in classdict :
#            slots = list(classdict['__slots__'])

        # create the new class
        newcls = super(metaReadOnlyAttr, mcl).__new__(mcl, classname, bases, classdict)

#        if hasattr(newcls, '__slots__') :
#            for s in newcls.__slots__ :
#                if s not in slots :
#                    slots.append(s)
#        type.__setattr__(newcls, '__slots__', slots)

        # unneeded through the use of __slots__
#        def __setattr__(self, name, value):
#            """ overload __setattr__ to forbid overloading of read only class info on a class instance """
#            try :
#                readonly = newcls.__readonly__
#            except :
#                readonly = {}
#            if name in readonly :
#                raise AttributeError, "attribute '%s' is a read only class attribute of class %s and cannot be overloaded on an instance of class %s" % (name, self.__class__.__name__, self.__class__.__name__)
#            else :
#                super(newcls, self).__setattr__(name, value)
#
#        type.__setattr__(newcls, '__setattr__', __setattr__)

        return newcls

NOT_PROXY_WRAPPED = ['__new__', '__getattribute__', '__getattr__', '__setattr__',
                     '__class__', '__weakref__', '__subclasshook__',
                     '__reduce_ex__', '__reduce__', '__dict__', '__sizeof__',
                     '__module__', '__init__', '__doc__']
def proxyClass( cls, classname, dataAttrName = None, dataFuncName=None,
                remove=(), makeDefaultInit = False, sourceIsImmutable=True ):
    """
    This function will generate a proxy class which keeps the internal data separate from the wrapped class. This
    is useful for emulating immutable types such as str and tuple, while using mutable data.  Be aware that changing data
    will break hashing.  not sure the best solution to this, but a good approach would be to subclass your proxy and implement
    a valid __hash__ method.

    :Parameters:
    cls : `type`
        The class to wrap
    classname : `string`
        The name to give the resulting proxy class
    dataAttrName : `string`
        The name of an attribute on which an instance of the wrapped class will
        be stored.
        Either dataAttrname or dataFuncName must be given, but not both.
    dataFuncName : `string`
        The name of an attribute on which reside a function, which takes no
        arguments, and when called, will return an instance of the wrapped
        class.
        Either dataAttrname or dataFuncName must be given, but not both.
    remove : `string` iterable
        An iterable of name of attributes which should NOT be wrapped.
        Note that certain attributes will never be wrapped - the list of
        such items is found in the NOT_PROXY_WRAPPED constant.
    makeDefaultInit : `bool`
        If True and dataAttrName is True, then a 'default' __init__ function
        will be created, which creates an instance of the wrapped class, and
        assigns it to the dataAttr. Defaults to False
        If dataAttrName is False, does nothing
    sourceIsImmutable : `bool`
        This parameter is included only for backwards compatibility - it is
        ignored.

    :rtype: `type`
    """

    assert not ( dataAttrName and dataFuncName ), 'Cannot use attribute and function for data storage. Choose one or the other.'

    if dataAttrName:
        class ProxyAttribute(object):
            def __init__(self, name):
                self.name = name

            def __get__(self, proxyInst, proxyClass):
                if proxyInst is None:
                    return getattr(cls, self.name)
                else:
                    return getattr(getattr(proxyInst, dataAttrName),
                                   self.name)

        def _methodWrapper( method ):
            def wrapper(self, *args, **kwargs):
                return method( getattr(self, dataAttrName), *args, **kwargs )

            wrapper.__doc__ = method.__doc__
            wrapper.__name__ = method.__name__
            return wrapper

    elif dataFuncName:
        class ProxyAttribute(object):
            def __init__(self, name):
                self.name = name

            def __get__(self, proxyInst, proxyClass):
                if proxyInst is None:
                    return getattr(cls, self.name)
                else:
                    return getattr(getattr(proxyInst, dataFuncName)(),
                                   self.name)

        def _methodWrapper( method ):
            #print method
            #@functools.wraps(f)
            def wrapper(self, *args, **kwargs):
                return method( getattr(self, dataFuncName)(), *args, **kwargs )

            wrapper.__doc__ = method.__doc__
            wrapper.__name__ = method.__name__
            return wrapper
    else:
        raise TypeError, 'Must specify either a dataAttrName or a dataFuncName'

    class Proxy(object):
        # make a default __init__ which sets the dataAttr...
        # if __init__ is in remove, or dataFuncName given,
        # user must supply own __init__, and set the dataAttr/dataFunc
        # themselves
        if makeDefaultInit and dataAttrName:
            def __init__(self, *args, **kwargs):
                # We may wrap __setattr__, so don't use 'our' __setattr__!
                object.__setattr__(self, dataAttrName, cls(*args, **kwargs))

        # For 'type' objects, you can't set the __doc__ outside of
        # the class definition, so do it here:
        if '__doc__' not in remove:
            __doc__ = cls.__doc__

    remove = set(remove)
    remove.update(NOT_PROXY_WRAPPED)
    #remove = [ '__init__', '__getattribute__', '__getattr__'] + remove
    for attrName, attrValue in inspect.getmembers(cls):
        if attrName not in remove:
            # We wrap methods using _methodWrapper, because if someone does
            #    unboundMethod = MyProxyClass.method
            # ...they should be able to call unboundMethod with an instance
            # of MyProxyClass as they expect (as opposed to an instance of
            # the wrapped class, which is what you would need to do if
            # we used ProxyAttribute)

            # ...the stuff with the cls.__dict__ is just to check
            # we don't have a classmethod - since it's a data descriptor,
            # we have to go through the class dict...
            if ((inspect.ismethoddescriptor(attrValue) or
                 inspect.ismethod(attrValue)) and
                not isinstance(cls.__dict__.get(attrName, None),
                               (classmethod, staticmethod))):
                try:
                    setattr(  Proxy, attrName, _methodWrapper(attrValue) )
                except AttributeError:
                    print "proxyClass: error adding proxy method %s.%s" % (classname, attrName)
            else:
                try:
                    setattr(  Proxy, attrName, ProxyAttribute(attrName) )
                except AttributeError:
                    print "proxyClass: error adding proxy attribute %s.%s" % (classname, attrName)

    Proxy.__name__ = classname
    return Proxy


# Note - for backwards compatibility reasons, PyNodes still inherit from
# ProxyUnicode, even though we are now discouraging their use 'like strings',
# and ProxyUnicode itself has now had so many methods removed from it that
# it's no longer really a good proxy for unicode.

# NOTE: This may move back to core.general, depending on whether the __getitem__ bug was fixed in 2009, since we'll have to do a version switch there
#ProxyUnicode = proxyClass( unicode, 'ProxyUnicode', dataFuncName='name', remove=['__getitem__', 'translate']) # 2009 Beta 2.1 has issues with passing classes with __getitem__
ProxyUnicode = proxyClass( unicode, 'ProxyUnicode', dataFuncName='name',
            remove=[ '__doc__', '__getslice__', '__contains__',  '__len__',
            '__mod__', '__rmod__', '__mul__', '__rmod__', '__rmul__', # reserved for higher levels
            'expandtabs', 'translate', 'decode', 'encode', 'splitlines',
            'capitalize', 'swapcase', 'title',
            'isalnum', 'isalpha', 'isdigit', 'isspace', 'istitle',
            'zfill' ])

class universalmethod(object):
#    """
#    a decorator which is similar to builtin classmethod, but which leaves the method unmodified when called
#    as a normal instance method:
#        - when the wrapped method is called as a class method, the first argument will be the class.
#        - when the wrapped method is called as an instance method, the first argument will be the instance.
#
#        >>> import inspect
#        >>> class D(object):
#        ...    @universalmethod
#        ...    def f( obj ):
#        ...        if inspect.isclass(obj):
#        ...            print "doing something class related"
#        ...        else:
#        ...            print "doing something instance related"
#        ...
#        >>> D.f()
#        doing something class related
#        >>> d = D()
#        >>> d.f()
#        doing something instance related
#
#    """

    def __init__(self, f):
        self.f = f

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)
        if instance is None:
            instance = cls
        def newfunc(*args, **kwargs):
            return self.f(instance, *args, **kwargs)
        return newfunc

def LazyLoadModule(name, contents):
    """
    :param name: name of the module
    :param contents: dictionary of initial module globals

    This function returns a special module type with one method `_addattr`.  The signature
    of this method is:

        _addattr(name, creator, *creatorArgs, **creatorKwargs)

    Attributes added with this method will not be created until the first time that
    they are accessed, at which point a callback function will be called to generate
    the attribute's value.

    :param name: name of the attribute to lazily add
    :param creator: a function that create the

    Example::

        import sys
        mod = LazyLoadModule(__name__, globals())
        mod._addattr( 'foo', str, 'bar' )
        sys.modules[__name__] = mod

    One caveat of this technique is that if a user imports everything from your
    lazy module ( .e.g from module import * ), it will cause all lazy attributes
    to be evaluated.

    Also, if any module-level expression needs to reference something that only
    exists in the LazyLoadModule, it will need to be stuck in after the creation of the
    LazyLoadModule.  Then, typically, after defining all functions/classes/etc
    which rely on the LazyLoadModule attributes, you will wish to update the
    LazyLoadModule with the newly-created functions - typically, this is done
    with the _updateLazyModule method.

    Finally, any functions which reference any LazyLoadModule-only attributes,
    whether they are defined after OR before the creation of the LazyLoadModule,
    will have to prefix it with a reference to the LazyLoadModule.

    Example::

        import sys

        def myFunc():
            # need to preface foo with 'lazyModule',
            # even though this function is defined before
            # the creation of the lazy module!
            print 'foo is:', lazyModule.foo

        mod = lazyLoadModule(__name__, globals())
        mod._addattr( 'foo', str, 'bar' )
        sys.modules[__name__] = mod

        # create a reference to the LazyLoadModule in this module's
        # global space
        lazyModule = sys.modules[__name__]

        # define something which relies on something in the lazy module
        fooExpanded = lazyModule.foo + '... now with MORE!'

        # update the lazyModule with our new additions (ie, fooExpanded)
        lazyModule._updateLazyModule(globals())
    """
    class _LazyLoadModule(types.ModuleType):
        class LazyLoader(object):
            """
            A data descriptor that delays instantiation of an object
            until it is first accessed.
            """
            def __init__(self, name, creator, *creatorArgs, **creatorKwargs):
                self.creator = creator
                self.args = creatorArgs
                self.kwargs = creatorKwargs
                self.name = name

            def __get__(self, obj, objtype):
                # In case the LazyLoader happens to get stored on more
                # than one object, cache the created object so the exact
                # same one will be returned
                if not hasattr(self, 'newobj'):
                    # use the callback to create the object that will replace us
                    self.newobj = self.creator(*self.args, **self.kwargs)
                    if isinstance(obj, types.ModuleType) and hasattr(self.newobj, '__module__'):
                        self.newobj.__module__ = obj.__name__
                #print "Lazy-loaded object:", self.name
                #delattr( obj.__class__, self.name) # should we overwrite with None?
                # overwrite ourselves with the newly created object
                setattr( obj, self.name, self.newobj)
                return self.newobj

        def __init__(self, name, contents):
            types.ModuleType.__init__(self, name)
            self.__dict__.update(contents)
            self._lazyGlobals = contents # globals of original module
            # add ourselves to sys.modules, overwriting the original module
            sys.modules[name] = self
            # the above line assigns a None value to all entries in the original globals.
            # luckily, we have a copy on this module we can use to restore it.
            self._lazyGlobals.update( self.__dict__ )
        @property
        def __all__(self):
            public = [ x for x in self.__dict__.keys() + self.__class__.__dict__.keys() if not x.startswith('_') ]
            return public

        @classmethod
        def _lazyModule_addAttr(cls, name, creator, *creatorArgs, **creatorKwargs):
            lazyObj = cls.LazyLoader(name, creator, *creatorArgs, **creatorKwargs)
            setattr( cls, name, lazyObj )
            return lazyObj

        def __setitem__(self, attr, args):
            """
            dynModule['attrName'] = ( callbackFunc, ( 'arg1', ), {} )
            """
            # args will either be a single callable, or will be a tuple of
            # ( callable, (args,), {kwargs} )
            if hasattr( args, '__call__'):
                callback = args
            elif isinstance( args, (tuple, list) ):
                if len(args) >= 1:
                    assert hasattr( args[0], '__call__' ), 'first argument must be callable'
                    callback = args[0]
                else:
                    raise ValueError, "must supply at least one argument"
                if len(args) >= 2:
                    assert hasattr( args[1], '__iter__'), 'second argument must be iterable'
                    cb_args = args[1]
                else:
                    cb_args = ()
                    cb_kwargs = {}
                if len(args) == 3:
                    assert operator.isMappingType(args[2]), 'third argument must be a mapping type'
                    cb_kwargs = args[2]
                else:
                    cb_kwargs = {}
                if len(args) > 3:
                    raise ValueError, "if args and kwargs are desired, they should be passed as a tuple and dictionary, respectively"
            else:
                raise ValueError, "the item must be set to a callable, or to a 3-tuple of (callable, (args,), {kwargs})"
            self._lazyModule_addAttr(attr, callback, *cb_args, **cb_kwargs)

        def __getitem__(self, attr):
            """
            return a LazyLoader without initializing it, or, if a LazyLoader does not exist with this name,
            a real object
            """
            try:
                return self.__class__.__dict__[attr]
            except KeyError:
                return self.__dict__[attr]

        # Sort of a cumbersome name, but we want to make sure it doesn't conflict with any
        # 'real' entries in the module
        def _lazyModule_update(self):
            """
            Used to update the contents of the LazyLoadModule with the contents of another dict.
            """
            # For debugging, print out a list of things in the _lazyGlobals that
            # AREN'T in __dict__
#            print "_lazyModule_update:"
#            print "only in dynamic module:", [x for x in
#                                              (set(self.__class__.__dict__) | set(self.__dict__))- set(self._lazyGlobals)
#                                              if not x.startswith('__')]
            self.__dict__.update(self._lazyGlobals)


    return _LazyLoadModule(name, contents)

# Note - since anything referencing attributes that only exist on the lazy module
# must be prefaced with a ref to the lazy module, if we are converting a pre-existing
# module to include LazyLoaded objects, we must manually go through and edit
# any references to those objects to have a 'lazyModule' prefix (or similar).
# To aid in this process, I recommend:
# 1. Uncommenting out the final print statement in _updateLazyModule
# 2. Grabbing the output of the print statement, throw it into a text editor with
#    regexp find/replace capabilities
# 3. You should have a python list of names.
#    Replace the initial and final bracket and quote - [' and '] - with opening
#    and closing parentheses - ( and )
#    Then find / replace all occurrences of:
#          ', '
#    with:
#          |
#    ...and you should be left with a regular expression you can use to find and replace
#   in your original code...
#   (you may also want to put (?<=\W) / (?=\W) in front / behind the regexp...)
#   Don't do the regexp find / replace on the source code blindly, though!
# ...also, when you make the call to _updateLazyModule that prints out the list of
# dynamic-module-only attributes, you should do it from a GUI maya - there are some objects
# that only exist in GUI-mode...

class LazyDocStringError(Exception): pass

class LazyDocString(types.StringType):
    """
    Set the __doc__ of an object to an object of this class in order to have
    a docstring that is dynamically generated when used.

    Due to restrictions of inheriting from StringType (which is necessary,
    as the 'help' function does a check to see if __doc__ is a string),
    the creator can only take a single object.

    Since the object initialization requires multiple parameters, the
    LazyDocString should be fed an sliceable-iterable on creation,
    of the following form:

        LazyDocString( [documentedObj, docGetter, arg1, arg2, ...] )

    documentedObj should be the object on which we are placing the docstring

    docGetter should be a function which is used to retrieve the 'real'
    docstring - it's args will be documentedObj and any extra args
    passed to the object on creation.

    Example Usage:

    >>> def getDocStringFromDict(obj):
    ...     returnVal = docStringDict[obj]
    ...     return returnVal
    >>>
    >>> # In order to alter the doc of a class, we need to use a metaclass
    >>> class TestMetaClass(type): pass
    >>>
    >>> class TestClass(object):
    ...     __metaclass__ = TestMetaClass
    ...
    ...     def aMethod(self):
    ...         pass
    ...
    ...     aMethod.__doc__ = LazyDocString( (aMethod, getDocStringFromDict, (aMethod,)) )
    >>>
    >>> TestClass.__doc__ = LazyDocString( (TestClass, getDocStringFromDict, (TestClass,)) )
    >>>
    >>>
    >>> docStringDict = {TestClass:'New Docs for PynodeClass!',
    ...                  TestClass.aMethod.im_func:'Method docs!'}
    >>>
    >>> TestClass.__doc__
    'New Docs for PynodeClass!'
    >>> TestClass.aMethod.__doc__
    'Method docs!'


    Note that new-style classes (ie, instances of 'type') and instancemethods
    can't have their __doc__ altered.

    In the case of classes, you can get around this by using a metaclass for
    the class whose docstring you wish to alter.

    In the case of instancemethods, just set the __doc__ on the function
    underlying the method (ie, myMethod.im_func). Note that if the __doc__
    for the method is set within the class definition itself, you will
    already automatically be modifying the underlying function.
    """

    def __init__(self, argList):
        if len(argList) < 2:
            raise LazyDocStringError('LazyDocString must be initialized with an iterable of the form: LazyDocString( [documentedObj, docGetter, arg1, arg2, ...] )')
        documentedObj = argList[0]
        docGetter = argList[1]
        if len(argList) > 2:
            args = argList[2]
            if len(argList) == 4:
                kwargs = argList[3]
            else:
                kwargs = {}
        else:
            args = ()
            kwargs = {}

        try:
            # put in a placeholder docstring, and check to make
            # sure we can change the __doc__ of this object!
            documentedObj.__doc__ = 'LazyDocString placeholder'
        except AttributeError:
            raise LazyDocStringError('cannot modify the docstring of %r objects' % documentedObj.__class__.__name__)
        self.documentedObj = documentedObj
        self.docGetter = docGetter
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        #print "creating docstrings", self.docGetter, self.args, self.kwargs
        self.documentedObj.__doc__ = self.docGetter(*self.args, **self.kwargs)
        return self.documentedObj.__doc__
    def __repr__(self):
        return repr(str(self))

for _name, _method in inspect.getmembers(types.StringType, inspect.isroutine):
    if _name.startswith('_'):
        continue

    def makeMethod(name):
        def LazyDocStringMethodWrapper(self, *args, **kwargs):
            return getattr(str(self), name)(*args, **kwargs)
        return LazyDocStringMethodWrapper
    setattr(LazyDocString, _name, makeMethod(_name) )

def addLazyDocString( object, creator, *creatorArgs, **creatorKwargs):
    """helper for LazyDocString.  Equivalent to :

        object.__doc__ = LazyDocString( (object, creator, creatorArgs, creatorKwargs) )
    """
    object.__doc__ = LazyDocString( (object, creator, creatorArgs, creatorKwargs) )

class TwoWayDict(dict):
    """
    A dictionary that can also map in reverse: value to key.

    >>> twd = TwoWayDict( {3:'foobar'} )
    >>> twd[3]
    'foobar'
    >>> twd.get_key('foobar')
    3

    Entries in both sets (keys and values) must be unique within that set, but
    not necessarily across the two sets - ie, you may have 12 as both a key and
    a value, but you may not have two keys which both map to 12 (or, as with a
    regular dict, two key entries for 12).

    If a key is updated to a new value, get_key for the old value will raise
    a KeyError:

    >>> twd = TwoWayDict( {3:'old'} )
    >>> twd[3] = 'new'
    >>> twd[3]
    'new'
    >>> twd.get_key('new')
    3
    >>> twd.get_key('old')
    Traceback (most recent call last):
        ...
    KeyError: 'old'

    Similarly, if a key is updated to an already-existing value, then the old key
    will be removed from the dictionary!

    >>> twd = TwoWayDict( {'oldKey':'aValue'} )
    >>> twd['newKey'] = 'aValue'
    >>> twd['newKey']
    'aValue'
    >>> twd.get_key('aValue')
    'newKey'
    >>> twd['oldKey']
    Traceback (most recent call last):
        ...
    KeyError: 'oldKey'

    If a group of values is fed to the TwoWayDict (either on initialization, or
    through 'update', etc) that is not consistent with these conditions, then the
    resulting dictionary is indeterminate; however, it is guaranteed to be a valid/
    uncorrupted TwoWayDict.
    (This is similar to how dict will allow, for instance, {1:'foo', 1:'bar'}).

    >>> twd = TwoWayDict( {1:'foo', 1:'bar'} )
    >>> # Is twd[1] 'foo' or 'bar'?? Nobody knows!
    >>> # ...however, one of these is guaranteed to raise an error...
    >>> twd.get_key('foo') + twd.get_key('bar')   #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    KeyError: (either 'bar' or 'foo')
    >>> twd = TwoWayDict( {1:'foo', 2:'foo'} )
    >>> # Is twd.get_key('foo') 1 or 2? Nobody knows!
    >>> # ...however, one of these is guaranteed to raise an error...
    >>> twd[1] + twd[2]   #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    KeyError: (either 1 or 2)

    Obviously, such shenannigans should be avoided - at some point in the future, this may
    cause an error to be raised...
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._reverse = {}
        self.update(*args, **kwargs)

    def __setitem__(self, k, v):
        # Maintain the 1-1 mapping
        if dict.__contains__(self, k):
            del self._reverse[self[k]]
        if v in self._reverse:
            dict.__delitem__(self, self.get_key(v))
        dict.__setitem__(self, k, v)
        self._reverse[v] = k

    def has_value(self, v):
        return self._reverse.has_key(v)

    def __delitem__(self, k):
        del self._reverse[self[k]]
        dict.__delitem__(self, k)

    def clear(self):
        self._reverse.clear()
        dict.clear(self)

    def copy(self):
        return TwoWayDict(self)

    def pop(self, k):
        del self._reverse[self[k]]
        return self.pop(k)

    def popitem(self, **kws):
        raise NotImplementedError()

    def setdefault(self, **kws):
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        if not (args or kwargs):
            return
        if len(args) > 1:
            raise TypeError('update expected at most 1 arguments, got %d' % len(args))
        # since args may be a couple different things, cast it to a dict to
        # simplify things...
        if args:
            tempDict = dict(args[0])
        else:
            tempDict = {}
        tempDict.update(kwargs)
        for key, val in tempDict.iteritems():
            self[key] = val

    def get_key(self, v):
        return self._reverse[v]

class EquivalencePairs(TwoWayDict):
    """
    A mapping object similar to a TwoWayDict, with the addition that indexing
    and '__contains__' can now be used with keys OR values:

    >>> eq = EquivalencePairs( {3:'foobar'} )
    >>> eq[3]
    'foobar'
    >>> eq['foobar']
    3
    >>> 3 in eq
    True
    >>> 'foobar' in eq
    True

    This is intended to be used where there is a clear distinction between
    keys and values, so there is little likelihood of the sets of keys
    and values intersecting.

    The dictionary has the same restrictions as a TwoWayDict, with the added restriction
    that an object must NOT appear in both the keys and values, unless it maps to itself.
    If a new item is set that would break this restriction, the old keys/values will be
    removed from the mapping to ensure these restrictions are met.

    >>> eq = EquivalencePairs( {1:'a', 2:'b', 3:'die'} )
    >>> eq['a']
    1
    >>> eq['b']
    2
    >>> eq[1]
    'a'
    >>> eq[2]
    'b'
    >>> del eq['die']
    >>> eq[3]
    Traceback (most recent call last):
        ...
    KeyError: 3
    >>> eq[2] = 1
    >>> eq[1]
    2
    >>> eq[2]
    1
    >>> eq['a']
    Traceback (most recent call last):
        ...
    KeyError: 'a'
    >>> eq['b']
    Traceback (most recent call last):
        ...
    KeyError: 'b'

    # Even though 2 is set as a VALUE, since it already
    # exists as a KEY, the 2:'b' mapping is removed,
    # so eq['b'] will be invalid...
    >>> eq = EquivalencePairs( {1:'a', 2:'b'} )
    >>> eq['new'] = 2
    >>> eq['new']
    2
    >>> eq[2]
    'new'
    >>> eq['b']
    Traceback (most recent call last):
        ...
    KeyError: 'b'

    # Similarly, if you set as a KEy something that
    # already exists as a value...
    >>> eq = EquivalencePairs( {1:'a', 2:'b'} )
    >>> eq['b'] = 3
    >>> eq['b']
    3
    >>> eq[3]
    'b'
    >>> eq[2]
    Traceback (most recent call last):
        ...
    KeyError: 2

    If a group of values is fed to the EquivalencePairs (either on initialization, or
    through 'update', etc) that is not consistent with it's restrictions, then the
    resulting dictionary is indeterminate; however, it is guaranteed to be a valid/
    uncorrupted TwoWayDict.

    (This is somewhat similar to the behavior of the dict object itself, which will allow
    a definition such as {1:2, 1:4} )

    Obviously, such shenannigans should be avoided - at some point in the future, this may
    even cause an error to be raised...

    Finally, note that a distinction between keys and values IS maintained, for compatibility
    with keys(), iter_values(), etc.
    """
    def __setitem__(self, k, v):
        if k in self:
            # this will check if k is in the keys OR values...
            del self[k]
        if v in self:
            del self[v]
        dict.__setitem__(self, k, v)
        self._reverse[v] = k

    def __delitem__(self, key):
        if dict.__contains__(self, key):
            super(EquivalencePairs, self).__delitem__(key)
        elif key in self._reverse:
            dict.__delitem__(self, self[key])
            del self._reverse[key]
        else:
            raise KeyError(key)

    def __getitem__(self, key):
        if dict.__contains__(self, key):
            return super(EquivalencePairs, self).__getitem__(key)
        elif key in self._reverse:
            return self._reverse[key]
        else:
            raise KeyError(key)

    def __contains__(self, key):
        return (dict.__contains__(self, key) or
                key in self._reverse)
        
    def get(self, key, d=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return d

def alias(origAttrName):
    """
    Returns a property which is simply an alias for another property.

    Acts simply to provide another name to reference the same
    underlying attribute; useful when subclassing, where a subclass
    might have a more descriptive name for an attribute that has the
    same function.

    The only purpose of this function is to produce more readable code.

    Example:

    >>> class GenericExporter(object):
    ...     def __init__(self, outFile):
    ...         self.outFile = outFile
    ...
    >>> class CowExporter(GenericExporter):
    ...     cowFile = alias('outFile')
    ...
    >>> CowExporter('bessie.cow').cowFile
    'bessie.cow'
    """
    def getter(self):
        return getattr(self, origAttrName)
    getter.__name__ = "get_" + origAttrName

    def setter(self, value):
        setattr(self, origAttrName, value)

    setter.__name__ = "set_" + origAttrName
    return property(getter, setter)

class propertycache(object):
    '''Class for creating properties where the value is initially calculated then stored.
    
    Intended for use as a descriptor, ie:

    class MyClass(object):
        @propertycache
        def aValue(self):
            return calcValue()
    c = MyClass()
    c.aValue
    
    '''
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
    def __get__(self, ownerInstance, ownerCls=None):
        result = self.func(ownerInstance)
        setattr(ownerInstance, self.name, result)
        return result

# unit test with doctest
if __name__ == '__main__' :
    import doctest
    doctest.testmod()

"""
Defines common types and type related utilities:  Singleton, etc.
These types can be shared by other utils modules and imported into util main namespace for use by other pymel modules
"""

import inspect
from pwarnings import *

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
                warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
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
                warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
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

    
def proxyClass( cls, classname, dataAttrName = None, dataFuncName=None, remove=[] ):
    """this function will generate a proxy class which keeps the internal data separate from the wrapped class. This 
    is useful for emulating immutable types such as str and tuple, while using mutable data.  Be aware that changing data
    will break hashing.  not sure the best solution to this, but a good approach would be to subclass your proxy and implement
    a valid __hash__ method."""

    assert not ( dataAttrName and dataFuncName ), 'Cannot use attribute and function for data storage. Choose one or the other.'

    if dataAttrName:
        def _methodWrapper( method ):
            #print method
            #@functools.wraps(f)
            def wrapper(self, *args, **kwargs):
                return method( cls( getattr(self, dataAttrName) ), *args, **kwargs )

            wrapper.__doc__ = method.__doc__
            wrapper.__name__ = method.__name__
            return wrapper
        
    elif dataFuncName:
        def _methodWrapper( method ):
            #print method
            #@functools.wraps(f)
            def wrapper(self, *args, **kwargs):
                return method( cls( getattr(self, dataFuncName)() ), *args, **kwargs )

            wrapper.__doc__ = method.__doc__
            wrapper.__name__ = method.__name__
            return wrapper
    else:
        raise TypeError, 'Must specify either a dataAttrName or a dataFuncName'
          
    remove = ['__new__', '__init__', '__getattribute__', '__getattr__'] + remove
    #remove = [ '__init__', '__getattribute__', '__getattr__'] + remove
    class Proxy(object):
        pass
        #def __new__(cls, *args, **kwargs):
        #    return super(Proxy, cls).__new__(cls)
        #def __init__(self, data):
        #    setattr( self, dataAttrName, cls( data ) )

    for methodName, method in cls.__dict__.items():
        if methodName not in remove:
            try:            
                setattr(  Proxy, methodName, _methodWrapper(method) )
            except AttributeError:
                print "proxyClass: error adding proxy method %s.%s" % (classname, methodName)
                
    Proxy.__name__ = classname
    return Proxy

# NOTE: This may move back to core.general, depending on whether the __getitem__ bug was fixed in 2009, since we'll have to do a version switch there
#ProxyUnicode = proxyClass( unicode, 'ProxyUnicode', dataFuncName='name', remove=['__getitem__', 'translate']) # 2009 Beta 2.1 has issues with passing classes with __getitem__
ProxyUnicode = proxyClass( unicode, 'ProxyUnicode', dataFuncName='name', remove=[ 'translate', '__doc__', '__getslice__', 
                        ]) 

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
        def newfunc(*args):
            return self.f(instance, *args)
        return newfunc
      
# unit test with doctest
if __name__ == '__main__' :
    import doctest
    doctest.testmod() 

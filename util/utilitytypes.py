"""
Defines common types and type related utilities:  Singleton, etc.
These types can be shared by other utils modules and imported into util main namespace for use by other pymel modules
"""

import warnings, inspect

class Singleton(object) :
    """
Singleton classes can be derived from this class
You can derive from other classes as long as Singleton comes first (and class doesn't override __new__

    >>> class uniqueImmutableDict(Singleton, dict) :
    >>>     def __init__(self, value) :
    >>>        # will only be initialied once
    >>>        if not len(self):
    >>>            super(uniqueDict, self).update(value)
    >>>        else :
    >>>            raise TypeError, "'"+self.__class__.__name__+"' object does not support redefinition"
    >>>   # You'll want to override or get rid of dict herited set item methods
    """
    def __new__(cls, *p, **k):
        if not '_the_instance' in cls.__dict__:
            cls._the_instance = super(Singleton, cls).__new__(cls)
        return cls._the_instance

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
        
        >>> def cb( module, attr):
        >>>     if attr == 'this':
        >>>         print "intercepted"
        >>>     else:
        >>>         raise ValueError        
        >>> sys.modules[__name__] = ModuleInterceptor(__name__, cb)
    
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
            
class metaStatic(type) :
    """Static singleton dictionnary metaclass to quickly build classes
    holding predefined immutable dicts"""
    def __new__(mcl, classname, bases, classdict):
        # Class is a Singleton and some base class (dict or list for instance), Singleton must come first so that it's __new__
        # method takes precedence
        base = bases[0]
        if Singleton not in bases :
            bases = (Singleton,)+bases        
        # Some predefined methods
        def __init__(self, value=None):
            # Can only create once)       
            if value is not None :
                # Can only init once
                if not self:
                    # Use the ancestor class dict method to init self
                    # base.update(self, value)
                    # self = base(value)
                    base.__init__(self, value)
                else :
                    raise TypeError, "'"+classname+"' object does not support redefinition"
        # delete the setItem methods of dict we don't want (read only dictionary)
        def __getattribute__(self, name):         
            remove = ('clear', 'update', 'pop', 'popitem', '__setitem__', 'append', 'extend' )
            if name in remove :
                raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'" 
#            elif self.__dict__.has_key(name) :
#                return self.__dict__[name]
            else :
                return base.__getattribute__(self, name)
        # Cnnot set an item of the read only dict or list
        def __setitem__(self,key,val) :
            raise TypeError, "'"+classname+"' object does not support item assignation"           
        # Now add methods of the defined class, as long as it doesn't try to redefine
        # __new__, __init__, __getattribute__ or __setitem__
        newdict = { '__slots__':[], '__dflts__':{}, '__init__':__init__, '__getattribute__':__getattribute__, '__setitem__':__setitem__ }
        # Note: could have defined the __new__ method like it is done in Singleton but it's as easy to derive from it
        for k in classdict :
            if k.startswith('__') and k.endswith('__') :
                # special methods, copy to newdict unless they conflict with pre-defined methods
                if k in newdict :
                    warnings.warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
                else :
                    newdict[k] = classdict[k]
            else :
                # class variables
                newdict['__slots__'].append(k)
                newdict['__dflts__'][k] = classdict[k]
        return super(metaStatic, mcl).__new__(mcl, classname, bases, newdict)

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
        
        # create the new class   
        newcls = super(metaReadOnlyAttr, mcl).__new__(mcl, classname, bases, classdict)
        
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

    
def proxyClass( cls, classname, dataAttrName = None, dataFuncName=None ):
    """this function will generate a proxy class which keeps the internal data separate from the wrapped class. This 
    is useful for emulating immutable types such as str and tuple, while using mutable data.  Be aware that changing data
    will breaking hashing.  not sure the best solution to this, but a good approach would be to subclass your proxy and implement
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
          
    remove = ('__new__', '__init__', '__getattribute__', '__getattr__')
    class Proxy(object):
        pass
        #def __init__(self, data):
        #    setattr( self, dataAttrName, cls( data ) )

    for methodName, method in cls.__dict__.items():
        if methodName not in remove:
            try:            
                setattr(  Proxy, methodName, _methodWrapper(method) )
            except AttributeError:
                print "error making", methodName
                
    Proxy.__name__ = classname
    return Proxy

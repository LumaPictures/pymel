"""
A generic n-dimensionnal Array class serving as base for arbitrary length Vector and Matrix classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the reat multi index slicing, get / setitem and item indexing for iterators,
# and tried to make the method names match so that it will be easier to include Numpy instead if desired.
# See http://www.numpy.org/

# TODO : try a numpy import and fallback to the included class if not successful ?


import operator, itertools, copy, inspect, sys

from arguments import isNumeric, clsname
from utilitytypes import readonly, metaReadOnlyAttr
from math import pi, exp
eps = 1e-10
import math, mathutils
from __builtin__ import sum as _sum, min as _min, max as _max, abs as _abs
# 2.5 only for any and all
try :
    from __builtin__ import all as _all, any as _any
except :
    def _all(iterable):
        """ Return True if all elements of the iterable are true """
        for element in iterable:
            if not element:
                return False
            return True
    def _any(iterable):
        """ Return True if any element of the iterable is true """
        for element in iterable:
            if element:
                return True
        return False

_thisModule = sys.modules[__name__]

# internal utilities

def _toCompOrArray(value) :
    if hasattr(value, '__iter__') :
        if type(value) is not Array :
            value = Array(value)
    elif isNumeric(value) :
        # a single numeric value
        pass 
    else :
        raise TypeError, "invalid value type %s cannot be converted to Array" % (clsname(value))
    
    return value

def _toCompOrArrayInstance(value) :
    if hasattr(value, '__iter__') :
        if not isinstance(value, Array) :
            value = Array(value)
    elif isNumeric(value) :
        # a single numeric value
        pass 
    else :
        raise TypeError, "invalid value type %s cannot be converted to Array" % (clsname(value))
    
    return value

def _shapeInfo(value) :
    if isinstance(value, Array) :
        shape = value.shape
        dim = value.ndim
        size = value.size        
    elif isNumeric(value) :
        shape = ()
        dim = 0
        size = 1
    else:
        raise TypeError, "can only query shape information on Array or Array component (numeric), not %s" % (clsname(value))
    
    return shape, dim, size

 
# override math and mathutils functions to make them accept iterables and operate element-wise on iterables

def _patchfn(basefn) :
    """ Patch the given base function to have it accept iterators """
    def fn(*args) :      
        maxarg = Array([])
        args = list(args)
        ln = len(args)
        for i in xrange(ln) :
            args[i] = _toCompOrArrayInstance(args[i])
            a = args[i]
            if isinstance(a, Array) :
                if a.size > maxarg.size :
                    maxarg = a
        if maxarg.size > 0 :
            try :
                for i in xrange(ln) :
                    maxarg, args[i] = coerce(maxarg, args[i])
            except :
                return NotImplemented
            allargs = zip(*args)
            res = _toCompOrArray(fn(*a) for a in allargs)
            if isinstance(res, Array) :
                res = maxarg.__class__._convert(res)
            return res
        else :
            return basefn(*args)
    fn.__name__ = basefn.__name__
    if basefn.__doc__ is None :
        basedoc = "No doc string was found on base function"
    else :
        basedoc = basefn.__doc__
    fn.__doc__ = basedoc + "\nThis function has been overriden from %s.%s to work element-wise on iterables" % (basefn.__module__, basefn.__name__)
    return fn
    
mathfn = inspect.getmembers(math, inspect.isbuiltin)
for mfn in mathfn :
    fname = mfn[0]
    basefn = mfn[1]
    newfn = _patchfn(basefn)
    _thisModule.__setattr__(fname, newfn) 
  
mathutilsfn = inspect.getmembers(mathutils, inspect.isfunction)
for mfn in mathutilsfn :
    fname = mfn[0]
    basefn = mfn[1]
    newfn = _patchfn(basefn)
    _thisModule.__setattr__(fname, newfn)   
  
# some functions operating on Arrays or derived classes

def sum(a, start=0, **kwargs):
    """ sum(a[, start[, axis=None]]) --> numeric or Array
        Returns the sum of all the components of a, an iterable of numeric values, plus start.
        If a is an Array and axis are specified will return an Array of sum(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return reduce(operator.add, a.axisiter(*axis), start)
    elif hasattr(a, '__iter__') :
        return _sum(a, start)
    else :
        return a+start
    
def prod(a, start=1, **kwargs):
    """ prod(a[, start[, axis=None]]) --> numeric or Array
        Returns the product of all the components of a, an iterable of numeric values, times start.
        If axis are specified will return an Array of prod(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)       
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return reduce(operator.mul, a.axisiter(*axis), start)
    elif hasattr(a, '__iter__') :
        return reduce(operator.mul, a, start)   
    else :
        return a*start

def any(*args, **kwargs):
    """ any(a [,axis=None]) --> bool or Array of booleans
        Returns True if any of the components of a, an iterable of numeric values, is True.
        If axis are specified will return an Array of any(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)
    if len(args) == 1 :
        a = args[0]
    else :
        a = args           
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        it = a.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return _any(it)
        else :
            return Array(map(_any, zip(*it)), shape=subshape)
    elif hasattr(a, '__iter__') :
        return _any(a)     
    else :
        return bool(a)
    
def all(*args, **kwargs):
    """ all(a, [,axis=None]) --> bool or Array of booleans
        Returns True if all the components of a, an iterable of numeric values, are True.
        If axis are specified will return an Array of all(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)
    if len(args) == 1 :
        a = args[0]
    else :
        a = args               
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        it = a.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return _all(it)
        else :
            return Array(map(_all, zip(*it)), shape=subshape)
    elif hasattr(a, '__iter__') :
        return _all(a)     
    else :
        return bool(a)

def min(*args, **kwargs):
    """ min(iterable[, key=func]) -> value
        min(a, b, c, ...[, key=func]) -> value
    
        With a single iterable argument, return its smallest item.
        With two or more arguments, return the smallest argument.
        If the iterable argument is an Array instance, returns the smallest component of iterable.
        If axis are specified will return an Array of element-wise min(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)
    key=kwargs.get('key', None)
    opt = {}
    if key is not None :
        opt['key'] = key
    if len(args) == 1 :
        a = args[0]
    else :
        a = args    
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        it = a.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return _min(it, **opt)
        else :
            return Array(map(lambda x:_min(x, **opt), zip(*it)), shape=subshape)
    elif hasattr(a, '__iter__') :
        return _min(a, **opt)    
    else :
        return a
    
def max(*args, **kwargs):
    """ max(iterable[, key=func]) -> value
        max(a, b, c, ...[, key=func]) -> value
    
        With a single iterable argument, return its largest item.
        With two or more arguments, return the largest argument.
        If the iterable argument is an Array instance, returns the largest component of iterable.
        If axis are specified will return an Array of element-wise max(x) for x in a.axisiter(*axis) """
    axis=kwargs.get('axis', None)
    key=kwargs.get('key', None)
    opt = {}
    if key is not None :
        opt['key'] = key
    if len(args) == 1 :
        a = args[0]
    else :
        a = args    
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        it = a.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return _max(it, **opt)
        else :
            return Array(map(lambda x:_max(x, **opt), zip(*it)), shape=subshape)
    elif hasattr(a, '__iter__') :
        return _max(a, **opt) 
    else :
        return a 

def sqlength(a, axis=None):
    """ sqlength(a, axis) --> numeric or Array
        Returns square length of a, a*a or the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis) """
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        it = a.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return reduce(operator.add, map(lambda x:x*x, a.flat)) 
        else :
            return map(sqlength, a.axisiter(*axis))      
    elif hasattr(a, '__iter__') :
        return reduce(operator.add, map(lambda x:x*x, a))   
    else :
        return a*a

def length(a, axis=None):
    """ sqlength(a, axis) --> numeric or Array
        Returns length of a, sqrt(a*a) or the square root of the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis) """
    return sqrt(sqlength(a, axis))

def normal(a, axis=None): 
    """ normal(a, axis) --> Array
        Return a normalized copy of self: self/length(self, axis) """
    a = _toCompOrArrayInstance(a)    
    return a / length(a, axis)
    
def dist(a, b, axis=None):
    """ dist(a, b, axis) --> float or Array
         Returns the distance between a and b, the length of b-a """
    a = _toCompOrArrayInstance(a)
    b = _toCompOrArrayInstance(b)
    return length(b-a, axis)
   
def difmap(fn, a, b):
    """ maps a function on two iterable classes of possibly different sizes,
        mapping on smallest size then filling to largest size with unmodified remnant of largest list.
        Will cast the result to the largest class type or to the a class in case of equal size.
        Classes must support iteration and __getslice__ """    
    l1 = len(a)
    l2 = len(b)
    if l1<l2 :
        return b.__class__(map(fn, a, b[:l1])+b[l1:l2])
    elif l1>l2 :
        return a.__class__(map(fn, a[:l2], b)+a[l2:l1])
    else :
        return a.__class__(map(fn, a, b))   
                
def amap(fn, *args) :
    """ A map like function that maps fn element-wise on every argument Arrays """  
    if args :
        args = [_toCompOrArrayInstance(a) for a in args]
        shapes = [_shapeInfo(a) for a in args]
        shapes.sort(cmp, lambda x:x[2])
        maxshape = shapes[-1][0]
        iters = [Array.filled(a, maxshape).flat for a in args]
        return Array(map(fn, *iters), maxshape)
    else :
        return fn()


# iterator classes on a specific Array axis, supporting __getitem__ and __setitem__
# in a numpy like way
          
class ArrayIter(object):
    def __init__(self, data, *args) :
        if len(args) == 1 and hasattr(args[0], '__iter__') :
            args = tuple(args[0]) 
        if isinstance(data, Array) :
            if args :
                axis = [int(x) for x in args]
            else :
                axis = [0]                    
            ndim = len(axis)
            size = 1
            coords = [slice(None)]*data.ndim
            shape = []
            for x in axis :
                if x < 0 or x >= data.ndim :
                    raise ValueError, "%s has %s dimensions, cannot iterate on axis %s" % (clsname(data), data.ndim, x)
                elif axis.count(x) > 1 :
                    raise ValueError, "axis %s is present more than once in ArrayIter axis list %s" % (x, axis)
                else :
                    coords[x] = 0
                    size *= data.shape[x]
                    shape.append(data.shape[x])
            itemshape = []
            for x in xrange(data.ndim) : 
                if not x in axis :
                    itemshape.append(data.shape[x]) 
            
            self.base = data
            self.ndim = ndim 
            self.size = size         
            self.coords = coords  
            self.axis = tuple(axis)               
            self.shape = tuple(shape)
            self.itemshape = tuple(itemshape) 
            self.itemdim = len(itemshape) 
            self.subsizes = [reduce(operator.mul, shape[i+1:], 1) for i in xrange(ndim)]  
            #print "Base shape %s, Axis %s, Iter shape %s, iter dim %s, iter size %s, item shape %s, item dim %s, subsizes %s"\
            #         % (self.base.shape, self.axis, self.shape, self.ndim, self.size, self.itemshape, self.itemdim, self.subsizes)                
        else :
            raise TypeError, "%s can only be built on Array" % clsname(self)
    def __length_hint__(self) :
        return self.size
    def __len__(self) :
        return self.size    
    def __iter__(self) :
        return self 
    
    def next(self):
        for i in range(len(self.axis)-1, 0, -1) :
            if self.coords[self.axis[i]] == self.shape[i] :
                self.coords[self.axis[i]] = 0
                self.coords[self.axis[i-1]] += 1
        if self.coords[self.axis[0]] >= self.shape[0] : 
            raise StopIteration

        val =  self.base.__getitem__(tuple(self.coords))
        self.coords[self.axis[-1]] += 1
        return val       

    # fast internal version without checks or negative index / slice support
    def _toArrayCoords(self, item, default=None):
        owncoords = []
        for s in self.subsizes :
            c = item//s
            item -= c*s
            owncoords.append(c)
        coords = [default]*self.base.ndim
        for i,c in enumerate(owncoords) :
            coords[self.axis[i]] = c
        # remove trailing ":" slices or None coords, leaving a minimum of one coord   
        while len(coords) > 1 and (coords[-1] == None or coords[-1] == slice(None)) :
            del coords[-1]
        return tuple(coords)
        
    def toArrayCoords(self, item, default=None):
        """ Converts an iterator item index (nth item) for that Array iterator to a tuple of axis coordinates for that Array, 
            returns a single coordinates tuple or a list of coordinate tuples if item index was a slice """
        if isinstance(item, slice) :
            return [self._toArrayCoords(f, default) for f in range(self.size)[item]]
        else :
            item = int(item)
            if item < 0 :
                item = self.size + item
            if item>=0 and item<self.size :
                return self._toArrayCoords(item, default)
            else :
                raise IndexError, "item number %s for iterator of %s items is out of bounds" % (item, self.size)

    def __getitem__(self, index) :
        """ Returns a single sub-Array or component corresponding to the iterator item item, or an Array of values if index is a slice """      
        coords = self.toArrayCoords(index, default=slice(None))
        if type(coords) is list :
            return self.base.__class__._convert(self.base.__getitem__(c) for c in coords)
            # return Array(self.base.__getitem__(c) for c in coords)
        else :
            return self.base.__getitem__(coords)
        
    def __delitem__(self, index):
        """ Do not use __delitem__ during iteration """
        coords = self.toArrayCoords(index, default=None)
        if type(coords) is list :
            for c in coords :
                self.base.__delitem__(c)
        else :
            self.base.__delitem__(coords)
        # update iterator
        self.__init__(self.base, *self.axis)        

    def __setitem__(self, index, value) :
        """ Returns a single sub-Array or component corresponding to the iterator item item, or an Array of values if index is a slice """
        coords = self.toArrayCoords(index, default=slice(None))

        # print "expected item shape: %s" % list(self.itemshape)
        value = _toCompOrArray(value)
        valueshape, valuedim, valuesize = _shapeInfo(value)
                     
        if type(coords) is list :
            if valueshape == self.itemshape :
                for c in coords :
                    self.base.__setitem__(c, value)
            elif hasattr(value, '__iter__') and valueshape[1:] == self.itemshape :
                lv = len(value)
                lc = len(coords)                            
                for i in xrange(lc) :
                    # repeat values if number of values < number of coords
                    self.base.__setitem__(coords[i], value[i%lv])
            else :
                raise ValueError, "value must be a single item (Array or component) of shape matching the iterated items shape, or an iterable of items, each of shape matching the iterated items shape"
        else :
            if valueshape == self.itemshape :
                self.base.__setitem__(coords, value)
            else :
                raise ValueError, "iterated items shape and value shape do not match"
    

    
# A generic multi dimensional Array class
# NOTE : Numpy Array class could be used instead, just implemented the bare minimum inspired from it
class Array(object):
    """ A generic n-dimensional array class using nested lists for storage """
    __metaclass__ = metaReadOnlyAttr
    __slots__ = ['_data', '_shape', '_ndim', '_size']
    __readonly__ = ('stype', 'data', 'shape', 'ndim', 'size')
    
    stype = list
    # cache shape and size to save time
    def _cacheshape(self):
        shape = []
        sub = self.data
        while sub is not None :
            try :
                shape.append(len(sub))
                sub = sub[0]
            except :
                sub = None
        self._shape = tuple(shape) 
        self._ndim = len(shape)
        self._size = reduce(operator.mul, shape, 1)                    
    def _getshape(self):
        return self._shape
    def _setshape(self, newshape):
        self.resize(newshape)
        
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Array (number of dimensions and number of components in each dimension")    
    ndim = property(lambda x : x._ndim, None, None, "Number of dimensions of the Array")
    size = property(lambda x : x._size, None, None, "Total size of the Array (number of individual components)")
    def _getdata(self):
        return self._data
    def _setdata(self, data):
        if isinstance(data, self.__class__.stype) :
            self._data = data
        else :
            self._data = self.stype(data)
        self._cacheshape() 
    def _deldata(self):
        del self._data[:]
        self._cacheshape()     
    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
    
    def isIterable(self):
        """ True if array is iterable (has a dimension of more than 0) """
        return self.ndim > 0

    @classmethod
    def _shapecheck(cls, shape):
        """ A check for fixed ndim / shape classes """
        if shape is not None :
            try :
                shape = cls._expandshape(shape)
                if -1 in shape :
                    return False
            except :
                return False
            
        return True     
        
    @classmethod
    def _expandshape(cls, shape=None, size=None):
        """ Expands shape that contains at most one undefined number of components for one dimension (-1) using known size """ 
        
        # check if class has fixed shape or dimensions
        cls_shape = cls_ndim = cls_size = None   
        try :
            cls_shape = tuple(cls.shape)
            cls_ndim = len(cls_shape)
            cls_size = reduce(operator.mul, cls_shape, 1)
        except :
            try : 
                cls_ndim = int(cls.ndim)
            except :
                pass 
            try : 
                cls_size = int(cls.size)
            except :
                pass 
                                
        if shape is None :
            if cls_shape is not None :
                newshape = list(cls_shape)
            elif cls_ndim is not None :
                newshape = [-1]*cls_ndim
            else :
                newshape = []
        else :
            if not hasattr(shape, '__iter__') :
                newshape = [shape]
            else :
                newshape = list(shape)               
        if size is None :
            if cls_size is not None :
                size = cls_size        
        newdim = len(newshape)
        
        # check for conformity with class constants
        if cls_size is not None and size != cls_size :
            raise TypeError, "class %s has a fixed size %s and it cannot be changed" % (cls.__name__, cls_size)              
        if cls_ndim is not None and newdim != cls_ndim :
            raise TypeError, "class %s has a fixed number of dimensions %s and it cannot be changed" % (cls.__name__, cls_ndim)       
#            if newdim < cls_ndim :
#                newshape = tuple([1]*(cls_ndim-newdim) + newshape)
#                newdim = cls_ndim
#            else :
#                raise TypeError, "class %s has a fixed number of dimensions %s and it cannot be changed" % (cls.__name__, cls_ndim)
        if cls_shape is not None and tuple(newshape) != cls_shape :
            raise TypeError, "class %s has a fixed shape %s and it cannot be changed" % (cls.__name__, cls_shape)           
    
        # expands unknown dimension sizes (-1) if size is known
        if size is not None :
            newsize = 1
            unknown = None
            for i, dim in enumerate(newshape) :
                idim = int(dim)
                if idim == -1 :
                    if unknown == None :
                        unknown = i
                    else :
                        raise ValueError, "can only specify one unknown dimension"
                else :
                    newsize *= idim
            if unknown is not None :
                if newsize :
                    newshape[unknown] = size / newsize
                else :
                    newshape[unknown] = 0
            if newsize != size :
                raise ValueError, "unable to match the required size %s with shape %s" % (size, newshape)
        
        return tuple(newshape)
    
    @classmethod
    def default(cls, shape=None, size=None):
        """ cls.default([shape])
            Returns the default instance (of optional shape form shape) for that Array class """
        
        try :
            shape = cls._expandshape(shape, size)
            if -1 in shape :
                raise ValueError, "cannot get the size of undefined dimension in shape %s without the total size" % (shape) 
        except :
            raise TypeError, "shape %s is incompatible with class %s" % (shape, cls.__name__)        
        if shape : 
            if not hasattr(shape, '__iter__') :
                shape = (shape,)               
            defval = 0
            for d in reversed(shape) :
                defval = [defval]*d
        else :
            defval = cls.stype()
            
        return cls(defval)
        
    @classmethod
    def filled(cls, value=None, shape=None, size=None):
        """ cls.filled([value[, shape[, size]]]) :
            Returns a cls instance of the given shape filled with value for the given shape,
            if no value is given, a default instance of that shape is returned.
            Value will be expended with the class default values to the nearest matching sub array
            of the class, then repeated.
            Value can't be truncated and will raise an error if of a size superior to the size of
            the nearest matching sub array of the class, to avoid improper casts """
        
        new = None
        try :
            shape = cls._expandshape(shape, size)
            if -1 in shape :
                raise ValueError, "cannot get the size of undefined dimension in shape %s without the total size" % (shape) 
        except :
            raise TypeError, "shape %s is incompatible with class %s" % (shape, cls.__name__)  
         
        if value is not None :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if not shape :
                if vshape :
                    return cls(value)
                else :
                    return cls([value])            
            dim = len(shape)  
            size = reduce(operator.mul, shape, 1)          

            if vdim <= dim and vsize <= size:
                subshape = shape[dim-vdim:]
                if subshape != vshape :
                    subsize = reduce(operator.mul, subshape, 1)
                    if subsize >= vsize :
                        value.resize(subshape)
                    else :
                        raise ValueError, "value of shape %s cannot be fit in a %s of shape %s, some data would be lost" % (vshape, cls.__name__, shape)
                if vdim < dim :
                    new = cls.default(shape)                 
                    iter = new.subiter(vdim)
                    for i in xrange(len(iter)) :
                        iter[i] = value    
                else :
                    new = cls(value.resize(shape))  
            else :
                raise ValueError, "fill value has more dimensions or is larger than the specified desired shape"
        else :
            if shape :
                new = cls(shape=shape)
            else :
                new = cls()
            
        return new 
        
    def fill(self, value=None, shape=None, size=None):     
        """ a.fill([value[, shape[, size]]])  :
            Fills the array in place with the given value, if no value is given a is set to the default class instance of same shape """
        if shape is None :
            shape = self.shape            
        new = self.__class__.filled(value, shape, size)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))            
                                                            
    def __new__(cls, *args, **kwargs ):
        """ Creates a new Array instance from one or several nested lists or numeric values """
        new = super(Array, cls).__new__(cls)
        new._data=[]
        new._cacheshape()
        return new
     
    def __init__(self, *args, **kwargs):
        """ Initialize an Array from one or several nested lists or numeric values """
        cls = self.__class__
        shape = kwargs.get('shape', None)
        size = kwargs.get('size', None)
        shape = cls._expandshape(shape, size)
                   
        data = None       
        if args :
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            if isinstance (args, Array) :
                # copy constructor
                data = copy.copy(list(args))
            elif hasattr(args, '__iter__') :
                data = []
                subshapes = []
                for arg in args :
                    sub = _toCompOrArray(arg)
                    subshape, subdim, subsize = _shapeInfo(sub)                    
                    data.append(sub)
                    subshapes.append(subshape)
                if not reduce(lambda x, y : x and y == subshapes[0], subshapes, True) :
                    raise ValueError, "all sub-arrays must have same shape"                          
            elif isNumeric(args) :
                data = cls.filled(args, shape).data
#                if shape :
#                    # can initialize an array from a single numeric value if a shape is specified
#                    data = cls.filled(args, shape).data
#                else :
#                    raise TypeError, "an %s cannot be initialized from a single value without specifying a shape, need at least 2 components or an iterable" % cls.__name__
            else :
                raise TypeError, "an %s element can only be another Array or an iterable" % cls.__name__
        else :
            data = cls.default(shape).data
            
        if data is not None :
            # generic Array for new as it's not yet correctly reshaped
            # new = super(Array, cls).__new__(cls)
            new = Array.__new__(Array)
            new.data = data
            # can re-shape on creation if a shape keyword is specified or the class has a fixed shape
            if shape and shape != new.shape :
                # accept expanding but not shrinking to catch casting errors
                ndim = len(shape)
                if size is None :
                    unknown = list(shape).count(-1)
                    if unknown > 1 :
                        shape = cls._expandshape(new.shape[:ndim], new.size)
                    elif unknown == 1 :
                        shape = cls._expandshape(shape, new.size)
                    size = reduce(operator.mul, shape, 1)
                if size >= new.size :                   
                    if ndim == new.ndim and reduce(operator.and_, map(operator.ge, shape, new.shape), True) :
                        new.retrim(shape)
                    else :
                        try :
                            new.fill(data, shape)
                        except :                            
                            new.resize(shape)
                else :
                    if isinstance (args, Array) :
                        raise TypeError, "cannot cast a %s of shape %s to a %s of shape %s, some data would be lost" % (clsname(args), args.shape, cls.__name__, shape)
                    else :
                        raise ValueError, "cannot initialize a %s of shape %s from %s, some data would be lost" % (cls.__name__, shape, args)                          
                        
            # check that the shape is compatible with the class, as some Array sub classes have fixed shapes / ndim
            if not cls._shapecheck(new.shape) :
                raise TypeError, "shape %s is incompatible with class %s" % (new.shape, cls.__name__)            

            self.data = new.data
        else :
            raise ValueError, "could not initialize a %s from the provided arguments %s" % (cls.__name__, args)

    def appended(self, other, axis=0):
        """ Append other on the given axis """
        shape, dim, size = _shapeInfo(self)
        other = _toCompOrArrayInstance(other)
        oshape, odim, osize = _shapeInfo(other)

        axis = self._getaxis(axis)
        assert len(axis) == 1, "only one axis can be specified on which to append"
        axis = axis[0]
        itself = self.axisiter(axis);    
        itemshape = itself.itemshape
        if size :
            other = Array.filled(other, itemshape)
            if axis > 0 :
                staxis = range(axis, -1, -1)+range(axis+1, dim)
                # print "staxis", staxis
                nself = self.transpose(staxis)
                otaxis = staxis[1:]
                for i, a in enumerate(otaxis) :
                    if a > axis :
                        otaxis[i] = a-1
                # print "otaxis", otaxis
                nother = other.transpose(otaxis)
                new = Array(list(nself)+[nother]).transpose(staxis)
            else :
                new = Array(list(self)+[other])
            return self.__class__._convert(new)            
        elif odim == 0 :
            return self.__class__._convert([other])
         
        raise ValueError, "cannot append a %s of shape %s on axis %s of %s of shape %s" % (clsname(other), oshape, axis, clsname(self), shape)
    
    def append(self, other, axis=0):
        """ Appends other to self on the given axis """
        new = self.appended(other, axis)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new appended shape %s is not compatible with class %s" % (shape, clsname(self))

    def stacked(self, other, axis=0):
        """ Concatenates Arrays on the given axis """
        shape, dim, size = _shapeInfo(self)
        other = _toCompOrArrayInstance(other)
        oshape, odim, osize = _shapeInfo(other)
        if odim == dim :
            axis = self._getaxis(axis)
            assert len(axis) == 1, "only one axis can be specified on which to concatenate"
            axis = axis[0]            
            itself = self.axisiter(axis);
            itother = other.axisiter(axis)
            if itself.itemshape == itother.itemshape :
                if axis > 0 :
                    taxis = range(axis, -1, -1)+range(axis+1, dim)
                    nself = self.transpose(taxis)
                    nother = other.transpose(taxis)
                    new = Array(list(nself)+list(nother)).transpose(taxis)
                else :
                    new = Array(list(self)+list(other))               
                return self.__class__._convert(new)
        
        raise ValueError, "cannot stack %s of shape %s and %s of shape %s on axis %s" % (clsname(self), shape, clsname(other), oshape, axis)

    def stack(self, other, axis=0):
        """ Concatenates Arrays on the given axis """
        new = self.stacked(other, axis)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new concatenated shape %s is not compatible with class %s" % (shape, clsname(self))
                     
    def hstacked(self, other) :
        return self.stacked(other, -1)

    def hstack(self, other) :
        self.stack(other, -1)

    def vstacked(self, other) :
        return self.stacked(other, 1)

    def vstack(self, other) :
        return self.stack(other, 1)

#    def repeated(self, repeat, axis):
#    # alow repeat onn multiple axis ..
#        pass
#    
#    def repeat(self, repeat, axis):
#        pass
 
    def toshape(self, shape):
        """ a.toshape(shape)
            Returns the Array as reshaped according to the shape argument """
        size = self.size
        try :
            newshape = self.__class__._expandshape(shape, size)
        except :
            raise TypeError, "shape %s is incompatible with class %s" % (shape, clsname(self))   
        newsize = reduce(operator.mul, newshape, 1)
        if newsize != size :
            raise ValueError, "total size of new Array must be unchanged"
        
        return self.tosize(tuple(newshape))
    
    def reshape(self, shape):
        """ a.reshape(shape)
            Performs in-place reshape of array a """
        new = self.toshape(shape)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))
              
    def tosize(self, shape, value=None):
        """ a.tosize([shape [, value]])
            Returns the Array as resized according to the shape argument.          
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        cls = self.__class__
        try :
            newshape = cls._expandshape(shape, None)
            if -1 in newshape :
                raise ValueError, "cannot get the size of undefined dimension in shape %s without the total size" % (shape)             
        except :
            raise TypeError, "shape %s is incompatible with class %s" % (shape, clsname(self))   
      
        new = None
        for c in inspect.getmro(cls) :
            if issubclass(c, Array) :
                try :
                    new = c.filled(value, newshape)
                    break
                except :
                    pass
                
        if new is not None :
            flatIter = self.flat
            newIter = new.flat
            ln = min(len(flatIter), len(newIter))
            for i in xrange(ln) :
                newIter[i] = flatIter[i]
            return new
        else :
            if value is not None :
                raise TypeError, "%s cannot be initialized to shape %s with value %s, and has no base class that can" % (clsname(self), shape, value)
            else :
                raise TypeError, "%s cannot be initialized to shape %s, and has no base class that can" % (clsname(self), shape)

    def resize(self, shape, value=None):
        """ a.resize(shape)
            Performs in-place resize of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        new = self.tosize(shape, value)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))

    def _trimmedcopy(self, other):
        ls = len(self)
        lo = len(other)
        l = min(ls, lo)
        if self.ndim > 1 :
            for i in xrange(l) :
                # print repr(self[i])
                # print repr(other[i])
                self.data[i]._trimmedcopy(other.data[i])
        else :
            for i in xrange(l) :
                other[i] = self[i]
                            
    def trim(self, shape, value=None):
        """ a.trim([shape [, value]])
            Returns the Array as "trimmed", re-sized according to the shape argument.
            The difference with a resize is that each dimension will be resized individually,
            thus the shape argument must have the same number of dimensions as the Array a.
            A value of -1 or None for a shape dimension size will leave it unchanged         
            An optional value argument can be passed and will be used to fill
            the newly created components if the trim results in a size increase. """
        cls = self.__class__
        if shape is None :
            newshape = ()
        else :
            newshape = shape
        newndim = len(newshape)
        if newndim != self.ndim :
            raise ValueError, "can only trim using a new shape of same number of dimensions as Array"
        oldshape = self.shape
        for i in xrange(newndim) :
            if newshape[i] == -1 or newshape[i] is None :
                newshape[i] = oldshape[i]
              
        new = None
        for c in inspect.getmro(cls) :
            if issubclass(c, Array) :
                try :
                    new = c.filled(value, newshape)
                    break
                except :
                    pass
                
        if new is not None :
            self._trimmedcopy(new)
            return new
        else :
            if value is not None :
                raise TypeError, "%s cannot be initialized to shape %s with value %s, and has no base class that can" % (clsname(self), shape, value)
            else :
                raise TypeError, "%s cannot be initialized to shape %s, and has no base class that can" % (clsname(self), shape)

    def retrim(self, shape, value=None):
        """ a.retrim(shape)
            Performs in-place trimming of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        new = self.trim(shape, value)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))    
    
    def copy(self):
        return copy.copy(self)
    
    def deepcopy(self):
        return copy.deepcopy(self)
    
    # display      
    def __str__(self):
        try :
            return "[%s]" % ", ".join( map(str,self) )
        except :
            return "%s" % self.data
    def __unicode__(self):
        try :
            return u"[%s]" % u", ".join( map(unicode,self) )
        except :
            return u"%s" % self.data        
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self)) 
    
    def _formatloop(self, level=0):
        subs = []
        try :
            for a in self :
                depth, substr = a._formatloop(level+1)
                subs.append(substr)
            if depth :
                msg = "[%s]" % (","+"\n"*depth+" "*(level+1)).join(subs)
            else :
                msg = "[%s]" % ", ".join(subs)
            return depth+1, msg                
        except :
            return 1, str(self)
               
    def formated(self):
        return self._formatloop()[1]
    
    # wrap of list-like access methods
    def __len__(self):
        """ Length of the first dimension of the array """
        try :
            # return len(self.data)
            return self.size
        except :
            raise TypeError, "len() of unsized object"
        
    @staticmethod
    def _extract(x, index) :
        if isinstance(x, Array) :
            res = x.data[index]
        else :
            res = [Array._extract(a, index) for a in x]
        return res
    
    def __getitem__(self, index):
        """ Get value from either a single (first dimension) or multiple index, support for slices"""
        # TODO : Numpy like support for indices Arrays ?
        if not hasattr(index, '__iter__') :
            index = [index]
        else :
            index = list(index)     
        if len(index) > self.ndim :
            raise valueError, "%s coordinates provided for an Array of dimension %s" % (len(index), self.ndim)   
        
        value = reduce(lambda x, y: Array._extract(x, y), index, self)
        # print "value and id", value, id(value)
        value = self._toCompOrConvert(value)
        # print "value and id", value, id(value)
        # value = _toCompOrArray(reduce(lambda x, y: Array._extract(x, y), index, self))
        return value

    def _inject(self, index, value) :
        indices = range(self.shape[0])[index[0]]
        if not hasattr(indices, '__iter__') :
            indices = [indices]
        ni = len(indices)
        shape = self.shape
        dim = self.ndim
        if len(index) == 1 : 
            # last check and assign        
            values = []
            valueshape, valuedim, valuesize = _shapeInfo(value)
            subshape = tuple(shape[1:])
            subdim = dim-1
            if valuedim > subdim :
                # a list of different values to assign, check if it fits 
                if len(value) == ni and tuple(valueshape[1:]) == subshape :
                    values = value                  
            elif valuedim == subdim :
                # a single component or sub-array used for each assign
                if valueshape == subshape :
                    values = [value]*ni
            else :
                # need to expand single value to a valid sub Array and use it for each assign
                try :
                    value = Array.filled(value, subshape)
                    values = [value]*ni
                except :
                    pass                                                    
                
            if values :           
                for i in xrange(ni) :
                    self.data[indices[i]] = values[i]
            else :
                raise ValueError, "shape mismatch between value(s) and Array components or sub Arrays designated by the indexing"
        else :
            # in case value is an iterable of values to be assigned to each sub-item
            values = []
            valueshape, valuedim, valuesize = _shapeInfo(value)
            if valuedim :      
                subexpected = self.__getitem__(index)
                subshape, subdim, subsize = _shapeInfo(subexpected)
                if valueshape == subshape :
                    if ni > 1 :
                        values = value
                    else :
                        values = [value]
                elif valuedim < subdim :   
                    values = [value]*ni
                else :
                    raise ValueError, "shape mismatch between value(s) and Array components or sub Arrays designated by the indexing"           
            else :
                # a single component value
                values = [value]*ni                                
           
            nextindex = index[1:]
            for i in xrange(ni) :
                self.data[indices[i]]._inject(nextindex, values[i])


    def __setitem__(self, index, value):
        """ Set value from either a single (first dimension) or multiple index, support for slices"""

        if not hasattr(index, '__iter__') :
            index = [index]
        else :
            index = list(index)           
        if len(index) > self.ndim :
            raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), self.ndim)  
        value = _toCompOrArray(value)
                    
        self._inject(index, value)

#    @staticmethod             
#    def _remove(a, index) :
#        # a = list(a)
#        la = len(a)
#        li = len(index)
#        if la and li :
#            next = li > 1
#            # data = self.data
#            for i in xrange(la-1, -1, -1) :
#                if i in index[0] :
#                    del a[i]
#                elif next :      
#                    Array._remove(a[i], index[1:])
#            if len(a) == 1 and hasattr(a[0], '__iter__') :
#                a[:] = list(a[0])

    def _delete(self, index) :
        ls = len(self)
        li = len(index)
        if ls and li :
            next = li > 1
            data = self.data
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    del data[i]
                elif next :      
                    data[i]._delete(index[1:])
            self.data = data
                
    def __delitem__(self, index) :
        """ Delete elements that match index from the Array """
        index = self._getindex(index, default=None, expand=True)
        if index :
            # a = self.data
            # Array._remove(a, index)
            a = self
            a._delete(index)
            try :
                # b = self.__class__(a)
                self = self.__class__(a.data)
            except :
                raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))
            # self.data = a

    def deleted(self, index):
        """ Returns a copy of self with the index elements deleted as in __delitem__ """
        index = self._getindex(index, default=None, expand=True)
        if index :
            a = self.deepcopy()
            a._delete(index)
            return self.__class__._convert(a)

    def _strip(self, index) :
        ls = len(self)
        li = len(index)
        if ls and li :
            next = li > 1
            data = self.data
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    del data[i]
                elif next :      
                    data[i]._strip(index[1:])
            if len(data) == 1 and hasattr(data[0], '__iter__') :
                self.data = data[0]
            else :
                self.data = data

    def strip(self, index) :
        """ Strip elements that match index from the Array, extra dimensions will be stripped  """
        index = self._getindex(index, default=None, expand=True)
        if index :
            # a = self.data
            # Array._remove(a, index)
            a = self
            a._strip(index)
            try :
                # b = self.__class__(a)
                self = self.__class__(a.data)
            except :
                raise TypeError, "stripping %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))
    
    def stripped(self, index):
        """ Returns a copy of self without the index elements, extra dimensions will be stripped """
        index = self._getindex(index, default=None, expand=True)
        if index :
            a = self.deepcopy()
            a._strip(index)
            return self.__class__._convert(a)
                        
    def __iter__(self, *args) :
        """ Default Array iterator on first dimension """
        return iter(self.data)
        # return self.subiter() 
     
    def axisiter(self, *args) :
        """ Returns an iterator using a specific axis or list of ordered axis,
            it is equivalent to transposing the Array using these ordered axis and iterating on the new Array
            for the remaining sub array dimension """
        return ArrayIter(self, *args)
    
    def subiter(self, dim=None) :
        """ Returns an iterator on all sub Arrays for a specific sub Array dimension,
            self.subiter(0) is equivalent to self.flat list sub-arrays of dimension 0, ie components
            self.subiter() is equivalent to self.subiter(self.ndim-1) and thus to self.__iter__() """
        ndim = self.ndim
        if dim is None :
            dim = ndim - 1
        iter_ndim = ndim - dim
        if iter_ndim > 0 :
            axis = tuple(x for x in xrange(iter_ndim))
            # print "subiter called on dim = %s, axis %s" % (dim, axis)
            return ArrayIter(self, axis)
        else :
            raise ValueError, "can only iterate for a sub-dimension inferior to Array's number of dimensions %s" % (ndim)       

    @property    
    def flat(self):
        """ Flat iterator on the Array components """
        return self.subiter(0)   

    def tolist(self):
        """ Returns that Array converted to a nested list """
        l = []
        for sub in self :
            if isinstance(sub, Array) :
                l.append(sub.tolist())
            else :
                l.append(sub)
        return l
    
    def ravel(self):
        """ Returns that Array flattened as to a one-dimensional array """
        return Array(self.flat)     
        
    # operators    
        
    def __eq__(self, other):  
        if not isinstance(other, self.__class__) :
            try :
                other = self.__class__(other)
            except :
                return False
        if self.shape == other.shape :
            return reduce(lambda x, y : x and y[0]==y[1], itertools.izip(self, other), True )
        else :
            return False
                 
    def __contains__(self, other):
        """ True if at least one of the Array sub-Arrays (down to individual components) is equal to the argument """
        if self == other :
            return True
        else :
            for sub in self :
                if hasattr(sub, '__iter__') :
                    if other in sub :
                        return True
                else :
                    if other == sub :
                        return True
        return False


    def count(self, value):
        """ a.count(b)
            Returns the number of occurrences of b in a """
        res = 0
        shape = self.shape
        dim = self.ndim
        if shape != () :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim <= dim :
                if self.shape[dim-vdim:] == vshape[:] :
                    for sub in self.subiter(vdim) :
                        if sub == value :
                            res += 1

        return res

    def index(self, value) :
        """ a.index(b)
            Returns the index of the first occurrence of b in a """    
        shape = self.shape
        dim = self.ndim
        if shape != () :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim <= dim and self.shape[dim-vdim:] == vshape[:] :
                iter = self.subiter(vdim)
                for i, sub in enumerate(iter) :
                    if sub == value :
                        return iter.toArrayCoords(i)

        raise ValueError, "%s.index(x): x not in %s" % (clsname(self), clsname(self)) 

    # common operators
    
    # convert to class or closest base class
    @classmethod
    def _convert(cls, value): 
        for c in inspect.getmro(cls) :
            if issubclass(c, Array) :
                try :
                    value = c(value)
                    break
                except :
                    pass
        if isinstance(value, Array) :
            return value
        else :
            return NotImplemented

    @classmethod
    def _toCompOrConvert(cls, value):
        if isinstance(value, cls) :
            return value
        if hasattr(value, '__iter__') :
            return cls._convert(value)
        elif isNumeric(value) :
            # a single numeric value
            return value
        else :
            raise TypeError, "invalid value type %s cannot be converted to %s or Array" % (clsname(value), cls.__name__)

    def __coerce__(self, other):
        """ coerce(x, y) -> (x1, y1)
        
            Return a tuple consisting of the two numeric arguments converted to
            a common type and shape, using the same rules as used by arithmetic operations.
            If coercion is not possible, return NotImplemented. """ 
            
        # print "coerce Array"
        if type(other) == type(self) :
            if other.shape == self.shape :
                return self, other
        else :
            try :    
                other = _toCompOrArrayInstance(other)
            except :
                return NotImplemented
            
        mro = inspect.getmro(self.__class__)
        nself = None
        nother = None            
        for c in mro :
            if issubclass(c, Array) :
                try :
                    nself = c(self)
                    nother = c(other, shape=self.shape)
                    break;
                except :
                    pass 

        if nself is not None and nother is not None :
            return nself, nother
        else :
            # that way if not able to to self.__oper__(other) (like if other is larger than self), it will try other.__roper__(self) next 
            return NotImplemented
            # raise TypeError, "%s and %s cannot be converted to an common Array instance of same shape" % (clsname(self), clsname(other))
        
    def __abs__(self):
        """ a.__abs__() <==> abs(a)
            Element-wise absolute value of a """         
        return self.__class__(abs(x) for x in self) 
    def __pos__(self):
        """ a.__pos__() <==> pos(a)
            Element-wise positive of a """         
        return self.__class__(x.__pos__ for x in self)         
    def __invert__(self):
        """ a.__invert__() <==> ~a
            Element-wise invert of a """         
        return self.__class__(operator.invert(x) for x in self)    
    
    # would define __round__ if the round() function was using it
    def round(self, ndigits=0):
        """ a.round([ndigits]) <==> around(a[, ndigits])
            Element-wise round to given precision in decimal digits (default 0 digits).
            This always returns an Array of floating point numbers.  Precision may be negative. """  
        return self.__class__(round(x, ndigits) for x in self)                     
    def __neg__(self):
        """ a.__neg__() <==> -a
            Element-wise negation of a """        
        return self.__class__(x.__neg__() for x in self)      
    def __add__(self, other) :
        """ a.__add__(b) <==> a+b
            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value """ 
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.add, nself, nother)
        return self.__class__._convert(res)         
    def __radd__(self, other) :
        """ a.__radd__(b) <==> b+a
            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value """        
        return self.__add__(other)  
    def __iadd__(self, other):
        """ a.__iadd__(b) <==> a += b
            In place addition of a and b, see __add__, result must fit a's type """
        return self.__class__(self.__add__(other))
    def __sub__(self, other) :
        """ a.__sub__(b) <==> a-b
            Returns the result of the element wise substraction of b from a if b is convertible to Array,
            substracts b from every component of a if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.sub, nself, nother)
        return self.__class__._convert(res)  
    def __rsub__(self, other) :
        """ a.__rsub__(b) <==> b-a
            Returns the result of the element wise substraction of a from b if b is convertible to Array,
            replace every component c of a by b-c if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.sub, nother, nself)
        return self.__class__._convert(res)     
    def __isub__(self, other):
        """ a.__isub__(b) <==> a -= b
            In place substraction of a and b, see __sub__, result must fit a's type """
        return self.__class__(self.__sub__(other))
    def __mul__(self, other) :
        """ a.__mul__(b) <==> a*b
            Returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.mul, nself, nother)
        return self.__class__._convert(res)    
    def __rmul__(self, other):
        """ a.__mul__(b) <==> b*a
            Returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """ 
        return self.__mul__(other) 
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of a and b, see __mul__, result must fit a's type """
        return self.__class__(self.__mul__(other))           
    def __pow__(self, other, modulo=None):
        """ a.__pow__(b[, modulo]) <==> a**b or (a**b) % modulo
            With two arguments, equivalent to a**b.  With three arguments, equivalent to (a**b) % modulo, but may be more efficient (e.g. for longs).
            Returns the result of the element wise elevation to power of a by b if b is convertible to Array,
            elevates every component of a to power b if b is a single numeric value """
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(lambda x,y:x.__pow__(y, modulo), nself, nother)
        return self.__class__._convert(res)          
    def __rpow__(self, other):
        """ a.__rpow__(b[, modulo]) <==> b**a or (b**a) % modulo
            With two arguments, equivalent to b**a.  With three arguments, equivalent to (b**a) % modulo, but may be more efficient (e.g. for longs).
            Returns the result of the element wise elevation to power of b by a if b is convertible to Array,
            replaces every component c of a by b elevated to power c if b is a single numeric value """        
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(lambda x,y:x.__pow__(y, modulo), nother, nself)
        return self.__class__._convert(res)          
    def __ipow__(self, other, modulo=None):
        """ a.__ipow__(b[, modulo]) <==> a**=b or a = (a**b) % modulo
            In place elevation to power of a by b, see __pow__, result must fit a's type """        
        return self.__class__(self.__pow__(other, modulo))
    def __div__(self, other) :
        """ a.__div__(b) <==> a/b
            The division operator (/) is implemented by these methods. The __truediv__() method is used
            when __future__.division is in effect, otherwise __div__() is used.
            Returns the result of the element wise division of a by b if b is convertible to Array,
            divides every component of a by b if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.div, nself, nother)
        return self.__class__._convert(res)    
    def __rdiv__(self, other) :
        """ a.__rdiv__(b) <==> b/a
            The division operator (/) is implemented by these methods. The __truediv__() method is used
            when __future__.division is in effect, otherwise __div__() is used.        
            Returns the result of the element wise division of b by a if b is convertible to Array,
            replaces every component c of a by b/c if b is a single numeric value """        
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.div, nother, nself)
        return self.__class__._convert(res)     
    def __idiv__(self, other):
        """ a.__idiv__(b) <==> a /= b
            The division operator (/) is implemented by these methods. The __truediv__() method is used
            when __future__.division is in effect, otherwise __div__() is used.        
            In place division of a by b, see __div__, result must fit a's type """
        return self.__class__(self.__div__(other))
    def __truediv__(self, other) :
        """ a.__truediv__(b) <==> a/b
            The division operator (/) is implemented by these methods. The __truediv__() method is used
            when __future__.division is in effect, otherwise __div__() is used.        
            Returns the result of the element wise true division of a by b if b is convertible to Array,
            performs true division of every component of a by b if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.truediv, nself, nother)
    def __rtruediv__(self, other) :
        """ a.__rtruediv__(b) <==> b/a
            The division operator (/) is implemented by these methods. The __rtruediv__() method is used
            when __future__.division is in effect, otherwise __rdiv__() is used.         
            Returns the result of the element wise true division of b by a if b is convertible to Array,
            replaces every component c of a by b/c if b is a single numeric value """        
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.truediv, nother, nself)  
    def __itruediv__(self, other):
        """ a.__itruediv__(b) <==> a /= b
            In place true division of a by b, see __truediv__, result must fit a's type """
        return self.__class__(self.__truediv__(other))
    def __floordiv__(self, other) :
        """ a.__floordiv__(b) <==> a//b      
            Returns the result of the element wise floor division of a by b if b is convertible to Array,
            performs floor division of every component of a by b if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.floordiv, nself, nother)
    def __rfloordiv__(self, other) :
        """ a.__rfloordiv__(b) <==> b//a       
            Returns the result of the element wise floor division of b by a if b is convertible to Array,
            replaces every component c of a by b//c if b is a single numeric value """        
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.floordiv, nother, nself)    
    def __ifloordiv__(self, other):
        """ a.__ifloordiv__(b) <==> a //= b
            In place true division of a by b, see __floordiv__, result must fit a's type """
        return self.__class__(self.__floordiv__(other))    
    def __mod__(self, other) :
        """ a.__mod__(b) <==> a%b      
            Returns the result of the element wise modulo of a by b if b is convertible to Array,
            performs modulo of every component of a by b if b is a single numeric value """       
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.mod, nself, nother)
    def __rmod__(self, other) :
        """ a.__rmod__(b) <==> b%a       
            Returns the result of the element wise modulo of b by a if b is convertible to Array,
            replaces every component c of a by b%c if b is a single numeric value """        
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        res = map(operator.mod, nother, nself)      
    def __imod__(self, other):
        """ a.__imod__(b) <==> a %= b
            In place modulo of a by b, see __mod__, result must fit a's type """
        return self.__class__(self.__mod__(other)) 

    # more could be wrapped the same way, __divmod__, etc 

    # additional methods
    
    def _getindex(self, index=None, **kwargs):
        """ check and expand index on array,
            example :
            >>> a = Array(1, shape=(3, 3, 3))
            >>> a._getindex((slice(2,8),-1), default=slice(None))
            >>> a._getindex((slice(2,8),-1), default=slice(None), expand=True)
        """  
        default = kwargs.get('default',None)
        expand = kwargs.get('expand',False)            
        shape = self.shape
        ndim = self.ndim     
        if index is None:
            index = []
        elif hasattr(index, '__iter__') :
            if len(index) == 1 and hasattr(index[0], '__iter__') :
                index = list(index[0])
            else :
                index = list(index)
        else :
            index = [index]
                
        if index :        
            assert len(index)<=ndim, "Array has %s dimensions, cannot specify %s indices" % (ndim, l)
            if default is not None :
                index = index + [default]*(ndim-len(index))      
            for i in xrange(len(index)) :
                ind = index[i]
                if ind is None :
                    ind = default
                if ind is None :
                    if expand :
                        ind = []
                elif isinstance(ind, slice) :
                    if expand :
                        ind = range(shape[i])[ind]
                    else :
                        ind = slice(*ind.indices(shape[i]))
                else :
                    ind = int(ind)
                    if ind<0 :
                        ind = shape[i]+ind
                    if ind<0 or ind>= shape[i] :
                        raise ValueError, "Array has %s components on axis %s, index %s from %s is out of bounds" % (shape[i], i, ind, index)
                    if expand :
                        ind = [ind]
                index[i] = ind
         
        return tuple(index) 

    def _getaxis(self, axis=None, **kwargs):
        fill = kwargs.get('fill',False)
        reverse = kwargs.get('reverse',False)
        ndim = self.ndim     
        if axis is None :
            axis = []
        if not hasattr(axis, '__iter__') :
            axis = [axis]
            
        if len(axis) == 0 : 
            if fill :
                if reverse :
                    axis = range(ndim-1, -1, -1)
                else :
                    axis = range(0, ndim, 1)
        else :
            if len(axis) == 1 and hasattr(axis[0], '__iter__') :
                axis = [range(ndim)[x] for x in axis[0]]
            else :
                axis = [range(ndim)[x] for x in axis]
            if not reduce(operator.and_, map(lambda x:axis.count(x)==1, axis), True) :
                raise ValueError, "axis %s is present more than once in axis list %s" % (x, tuple(axis))                
         
        return tuple(axis)       
        
    def sum(self, *args):
        """ Returns the sum of the components of self """
        return sum(self, start=0, axis=args)
 
    def prod(self, *args):
        """ Returns the product of the components of self """
        return prod(self, start=1, axis=args) 
 
    # __nonzero__ not defined, use any or all
    def any(self, *args):
        return any(self, axis=args)
 
    def all(self, *args):
        return all(self, axis=args) 
 
    def min(self, *args, **kwargs):
        return min(self, axis=args, **kwargs)  
    
    def max(self, *args, **kwargs):
        return max(self, axis=args, **kwargs)  
 
    def sqlength(self, *args):
        return sqlength(self, axis=args)  
    
    def length(self, *args):
        return length(self, axis=args) 
    
    def normal(self, *args):
        return normal(self, axis=args)
    
    def dist(self, other, *args):
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return dist(nself, nother, axis=args)          
  
    def isEquivalent(self, other, tol):
        """ Returns True if both arguments have same shape and distance between both Array arguments is inferior or equal to tol """
        if isinstance(other, Array) :
            try :
                nself, nother = coerce(self, other)
            except :
                try : 
                    nother, nself = coerce(other, self)
                except :
                    return False
            if nself.shape == nother.shape :      
                return dist(nself, nother) <= tol
        
        return False  
        
    def transpose(self, *args):
        """ a.transpose(*axes)
        
            Returns a with axes transposed. If no axes are given,
            or None is passed, switches the order of the axes. For a 2-d
            array, this is the usual matrix transpose. If axes are given,
            they describe how the axes are permuted.  """
        axis = self._getaxis(args, fill=True, reverse=True)
        if len(axis) != self.ndim :
            raise ValueError, "Transpose axis %s do not match array shape %s" % (axis, self.shape) 
        else :       
            return self.__class__._convert(Array([s for s in self.axisiter(*axis)], shape=(self.shape[x] for x in axis)))
    
    T = property(transpose, None, None, """The transposed array""") 

    # arrays of complex values
    def conjugate(self):
        """ Returns the element-wise complex.conjugate() of the Array """
        return self.__class__(conjugate(x) for x in self)
    def real(self):
        """ Returns the real part of the Array """
        return self.__class__(real(x) for x in self)
    def imag(self):
        """ Returns the imaginary part of the Array """
        return self.__class__(imag(x) for x in self) 
    
# functions that work on Matrix

def det(value):
    if isinstance(value, Matrix) :
        return value.det()
    elif isNumeric(value) :
        return value
    else :
        try :
            value = Matrix(value)
            return value.det()
        except :
            raise TypeError, "cannot compute a determinant on invalid value type %s" % (clsname(value))

class Matrix(Array):
    """
    A generic size Matrix class, basically a 2 dimensional Array
    """
    __slots__ = ['_data', '_shape', '_size']    
    
    #A Matrix is a two-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 2
           
    def _getshape(self):
        if self.data :
            return (len(self.data), len(self.data[0]))
        else :
            return (0, 0)
    def _setshape(self, newshape):
        self.resize(newshape)
        
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Matrix, a tuple of the sizes of its two dimensions")    
    size = property(lambda x : x.shape[0]*x.shape[1], None, None, "Total size of the Array (number of individual components)")

    def is_square(self):
        return self.shape[0] == self.shape[1]
 
    @classmethod
    def identity(cls, n):
        return cls([[float(i==j) for i in xrange(n)] for j in xrange(n)])
 
    # row and column size properties
    def _getnrow(self):
        return self.shape[0]
    def _setnrow(self, m):
        self.retrim((m, self.shape[1]))
    nrow = property(_getnrow, _setnrow, None, "Number of rows in this Matrix")          
    def _getncol(self):
        return self.shape[1]
    def _setncol(self, n):
        self.retrim((self.shape[0], n))
    ncol = property(_getncol, _setncol, None, "Number of columns in this Matrix")      

    # specific iterators
    @property
    def row(self):
        """ Iterator on the Matrix rows """
        return self.axisiter(0)  
    @property
    def col(self):
        """ Iterator on the Matrix columns """
        return self.axisiter(1) 
    
    # overloaded Array operators

#    def __coerce__(self, other):
#        """ coerce(x, y) -> (x1, y1)
#        
#            Return a tuple consisting of the two numeric arguments converted to
#            a common type and shape, using the same rules as used by arithmetic operations.
#            If coercion is not possible, return NotImplemented. """ 
#            
#        print "coerce Matrix"
#        if type(other) == type(self) :
#            if other.shape == self.shape :
#                return self, other
#        else :
#            try :    
#                other = _toCompOrArrayInstance(other)
#            except :
#                return NotImplemented
#            
#        mro = inspect.getmro(self.__class__)
#        nself = None
#        nother = None            
#        for c in mro :
#            if issubclass(c, Array) :
#                try :
#                    nself = c(self)
#                    # nother = c(other, shape=self.shape)
#                    nother = c(other)
#                    break;
#                except :
#                    pass 
#
#        if nself is not None and nother is not None :
#            return nself, nother
#        else :
#            # that way if not able to to self.__oper__(other) (like if other is larger than self), it will try other.__roper__(self) next 
#            return NotImplemented
#            # raise TypeError, "%s and %s cannot be converted to an common Array instance of same shape" % (clsname(self), clsname(other))

    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a Matrix, __mul__ is mapped to matrix multiplication, if b is a Vector, to Matrix by Vector multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, Matrix) :
            return self.__class__._convert( [ [ dot(row,col) for col in other.col ] for row in self.row ] )
        elif isinstance(other, Vector) :
            return other.__rmul__(self)
        else :
            return Array.__mul__(self, other)
            # return super(Array, self).__mul__(other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a Matrix, __rmul__ is mapped to matrix multiplication, if b is a Vector, to Matrix by Vector multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """        
        if isinstance(other, Matrix) :
            return Matrix( [ [ dot(row,col) for col in self.col ] for row in other.row ] )
        elif isinstance(other, Vector) :
            return other.__mul__(self)
        else :
            return Array.__rmul__(self, other)
            #return super(Array, self).__mul__(other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of Matrix a and b, see __mul__, result must fit a's type """      
        return self.__class__(self*other)        

    
    # specific methods
    
    def diagonal(self, offset=0, *args, **kwargs) :
        """ a.diagonal([offset=0[, wrap=False]]) -> diagonal
            Returns the diagonal of the Matrix with the given offset,
            i.e., the collection of elements of the form a[i,i+offset].
            If keyword wrap=True will wrap out of bounds indices
            
            Examples

            >>> a = Array(range(4), shape=(2, 2))
            >>> a.formated()
            >>> a.diagonal()
            >>> a.diagonal(1)
            >>> a.diagonal(1, wrap=True)
            >>> a.diagonal(-1, wrap=True)
        """
        if self.ndim != 2 :
            raise ValueError, "can only calculate diagonal on Array or sub Arrays of dimension 2"    

        wrap = kwargs.get('wrap', False)
        shape = self.shape
        #axis = self._getaxis(args, fill=True)
        #it = self.axisiter(axis)
        #print self.transpose(axis).formated()
        if wrap :
            return Array([self[i,(i+offset)%shape[1]] for i in xrange(shape[0])])
        else :
            l = []
            for i in xrange(shape[0]) :
                if (i+offset) < shape[1] :
                    l.append(self[i, (i+offset)])     
            return Array(l)
                
    def trace(self, offset=0, *args, **kwargs) :
        """ a.trace([offset=0[, wrap=False]]) -> diagonal
            Returns the sum of the components on the diagonal """
        return sum(self.diagonal(offset, *args, **kwargs))
    
    def minor(self, i, j):
        index = self._getindex((i, j), default=None)
        m = self.deleted(index)
        return m
    
    def cofactor(self, i, j):
        return ((-1)**(i+j))*self.minor(i, j).det()
    
    # sometimes called adjoint
    def adjugate(self):
        nr, nc = self.shape
        assert nc == nr, "Adjugate Matrix can only be computed for a square Matrix"
        m = self.__class__([[self.cofactor(j, i) for j in xrange(nc)] for i in xrange(nr)])
        return m
        
    def _gauss_jordan(self):
        nr, nc = self.shape
        assert nc >= nr, "Matrix needs to have at least as much columns as rows to do a Gauss-Jordan elimination"            
        m = self.deepcopy()   
        nbperm = 0  
        for i in xrange(nr) :
            maxr = i
            for j in xrange(i+1,nr) :
                if abs(m[j,i]) > abs(m[maxr,i]):
                    maxr = j
            # swap rows
            if maxr != i :
                m[i], m[maxr] = m[maxr], m[i]
                nbperm += 1
            if abs(m[i,i]) < eps :
                raise ValueError, "Matrix is singular"
            d = float(m[i,i])
            for j in xrange(i+1,nr) :
                # eliminate lower rows
                if abs(m[j,i]) >= eps :
                    f = m[j,i] / d
                    for k in xrange(i, nc) :
                        m[j,k] -= f * m[i,k]
                        # print m.formated()
                    # print m.formated()  
        return m, nbperm

    def gauss(self):
        """ m.gauss() --> Matrix
            returns the triangular matrix obtained by Gauss-Jordan elimination on m
            will raise a ValueError if m is singular """
        return self._gauss_jordan()[0]

    def reduced(self):
        """ m.gauss() --> Matrix
            returns the reduced row echelon form of the matrix a by Gauss-Jordan elimination,
            followed by back substitution """
        m = self.gauss()
        nr, nc = m.shape
        for i in range(nr-1, -1, -1):
            # print m.formated()
            d  = float(m[i, i])
            for j in range(i):
                for k in range(nc-1, i-1, -1):
                    m[j,k] -=  m[i,k] * m[j, i] / d
                # print m.formated()
            m[i, i] /= d
            for j in range(nr, nc):
                m[i, j] /= d               
        # print m.formated()
        return m
    
    def det(self):
        assert self.is_square(), "determinant is defined for square Matrix"
        n = self.nrow
        if n == 1:
            return self[0,0]
        elif n == 2:
            return self[0,0]*self[1,1] - self[1,0]*self[0,1]
        elif n == 3:
            # direct Leibniz formula
            return   self[0,0]*self[1,1]*self[2,2] + self[0,2]*self[1,0]*self[2,1] + self[0,1]*self[1,2]*self[2,0] \
                   - self[0,2]*self[1,1]*self[2,0] - self[0,0]*self[1,2]*self[2,1] - self[0,1]*self[1,0]*self[2,2]
        elif n < 6 :
            # cofactors
            d = 0
            for j in xrange(n) :
               d += self[0,j]*self.cofactor(0, j)  # ((-1)**j)*self.minor(0,j).det() 
            return d
        else :
            # Gauss-Jordan elimination
            try :
                m, nbperm = self._gauss_jordan()
                return prod(m.diagonal(), (-1)**nbperm) 
            except ValueError :
                # singular
                return 0.0           
   
    def inverse(self): 
        nr, nc = self.shape
        if nr < 4 and nc < 4 :
            # by cofactors expansion
            try :
                return self.adjugate()/float(self.det())
            except ZeroDivisionError :
                raise ValueError, "Matrix is singular"      
        else :
            # by gauss-jordan elimination
            id = Matrix.identity(nr)        
            m = self.hstacked(id).reduced()
            return self.__class__(m[:, nr:])

    I = property(inverse, None, None, """The inverse Matrix""")

# functions that work on Vectors or 1-d Arrays

def dot(a, b):
    """ dot(a, b):
        dot product of a and b, a and b should be iterables of numeric values """
    a = _toCompOrArray(a)
    b = _toCompOrArray(b)
    return sum(a*b)

def outer(a, b):
    """ outer(a, b) :
        outer product of vectors a and b """
    return Array([b*x for x in a])

def cross(a, b, axis=None):
    """ cross(a, b):
        cross product of a and b, a and b should be iterables of 3 numeric values  """
    assert len(a) == len(b) == 3, 'cross product is only defined for two Vectors of size 3'
    return Vector([a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]])

def cotan(a, b, c) :
    """ cotan(a, b, c) :
        cotangent of the (b-a), (c-a) angle, a, b, and c should support substraction, dot, cross and length operations """
    return dot(c - b,a - b)/length(cross(c - b, a - b))  

class Vector(Array):
    """
        A generic size Vector class derived from Array, basically a 1 dimensional Array
    """
    __slots__ = ['_data', '_shape', '_size']    
    
    #A Vector is a one-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 1

       
    def _getshape(self):
        return (len(self.data),)
    def _setshape(self, newshape):
        self.resize(newshape)    
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Vector, as Vectors are one-dimensional Arrays: v.shape = (v.size,)")    
    ndim = property(lambda x : 1, None, None, "A Vector is a one-dimensional Array")
    size = property(lambda x : len(x.data), None, None, "Number of components of the Vector")
    def _getdata(self):
        return self._data
    def _setdata(self, data):
        if isinstance(data, list) :
            self._data = data
        else :
            self._data = list(data)
    def _deldata(self):
        del self._data[:]   
    data = property(_getdata, _setdata, _deldata, "The list storage for the Vector data") 
    
    # common operators are herited from Arrays
           
    # overloaded operators
    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a Vector, __mul__ is mapped to the dot product of the two vectors a and b,
            If b is a Matrix, __mul__ is mapped to Vector a by Matrix b multiplication (post multiplication or transformation of a by b),
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, Vector) :
            return self.dot(other)
        elif isinstance(other, Matrix) :
            if self.size == other.shape[0] :
                return self.__class__._convert( [ dot(self, col) for col in other.col ] )
            else :
                raise ValueError, "vector of size %s and matrix of shape %s are not conformable for a Vector * Matrix multiplication" % (self.size, other.shape) 
        else :
            # will defer to Array.__mul__
            return Array.__mul__(self, other)
            # return super(Array, self).__mul__(other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a Vector, __rmul__ is mapped to the dot product of the two vectors a and b,
            If b is a Matrix, __rmul__ is mapped to Matrix b by Vector a multiplication,
            otherwise, returns the result of the element wise multiplication of b and a if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """       
        if isinstance(other, Vector) :
            return self.dot(other)
        elif isinstance(other, Matrix) :
            if self.size == other.shape[1] :
                return self.__class__._convert( [ dot(row, self) for row in other.row ] )
            else :
                raise ValueError, "vector of size %s and matrix of shape %s are not conformable for a Matrix * Vector multiplication" % (self.size, other.shape)             
        else :
            return Array.__rmul__(self, other)
            # return super(Array, self).__mul__(other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of Vector a and b, see __mul__, result must fit a's type """      
        return self.__class__(self*other)  
          
                  
    # special operators
    def __xor__(self, other):
        """ a.__xor__(b) <==> a^b
            Defines the cross product operator between two vectors,
            if b is a Matrix, a^b is equivalent to transforming a by the inverse transpose Matrix of b,
            often used to transform normals """
        if isinstance(other, Vector) :
            return self.cross(other)  
        elif isinstance(other, Matrix) :
            return self.transformAsNormal(other)
        else :
            return NotImplemented
    def __ixor__(self, other):
        """ a.__xor__(b) <==> a^=b
            Inplace cross product or transformation by inverse transpose Matrix of b is v is a Matrix """        
        self = self.__xor__(other) 
                
    # additional methods
 
    def dot(self, other):
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return dot(nself, nother)   

    def cross(self, other):
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return self.__class__._convert(cross(nself, nother))

    def outer(self, other):
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return Matrix(outer(nself, nother))
    
    def transformAsNormal(self, other):
        if isinstance(other, Matrix) :
            return self.__mul__(other.transpose().inverse())
        else :
            return NotImplemented
        
    def normal(self): 
        """ Return a normalized copy of self. To be consistant with Maya API and MEL unit command,
            does not raise an exception if self if of zero length, instead returns a copy of self """
        try :
            return self/self.length()
        except :
            return self
    unit = normal
    
    def normalize(self):
        """ Performs an in place normalization of self """
        self.data = self.normal().data

    def distanceTo(self, other):
        return self.dist(other)  



   
def _testArray() :  
#    A = Array(2)
#    print A
#    print repr(A)
#    print A.formated()
#    print A.shape
#    print A.ndim
#    print A.size
#    print A.data


    A = Array([2])
    print A
    print repr(A)
    print A.formated()
    print A.shape
    print A.ndim
    print A.size
    print A.data 
    A = Array()
    print A.formated()
    print A.shape
    print A.ndim
    print A.size
    print A.data
    A = Array.default()
    print A.formated()
    A = Array([[[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]]])
    print A
    print A.formated()
    print A.shape
    print A.ndim
    print A.size
    print A.data    
    A = Array([[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]])
    print A
    print A.formated()
    B = Array(1, 2, 3)
    print B
    B = Array([1], [2], [3])
    print B
    B = Array([[1], [2], [3]])
    print B
    B = Array([[[1], [2], [3]]])
    print B
       
    # append (hstack, vstack)
    A = Array([])
    A.append(1)
    print A.formated()
    # [1]
    print A.appended(2)
    # [1, 2]
    A.stack([2])
    print A.formated()
    # [1, 2]
    A = Array([A])
    print A.formated()
    # [[1, 2]]
    A.append([4, 5],0)
    print A.formated()
    # [[1, 2],
    # [4, 5]]
    A.append([3, 6], 1)
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6]]    
    A.append([7, 8, 9])
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9]]    
    A.stack([[0, 0, 0]])
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9],
    # [0, 0, 0]]    
    print A.stacked([[0], [0], [0], [1]], 1).formated()
    #[[1, 2, 3, 0],
    # [4, 5, 6, 0],
    # [7, 8, 9, 0],
    # [0, 0, 0, 1]]    
    A.append([0, 0, 0, 1], 1)
    print A.formated()
    #[[1, 2, 3, 0],
    # [4, 5, 6, 0],
    # [7, 8, 9, 0],
    # [0, 0, 0, 1]] 
           
    A = Array(range(1, 7), shape=(2, 3))
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6]]    
    B = Array(range(1, 5), shape=(2, 2))
    print B.formated()
    #[[1, 2],
    # [3, 4]]    
    A.stack(B, 1)
    print A.formated()
    #[[1, 2, 3, 1, 2],
    # [4, 5, 6, 3, 4]]    
    A.append(range(1,6), 0)
    print A.formated()
    #[[1, 2, 3, 1, 2],
    # [4, 5, 6, 3, 4],
    # [1, 2, 3, 4, 5]]    
    B = Array(range(10), shape=(2, 5)) 
    print B.formated()
    #[[0, 1, 2, 3, 4],
    # [5, 6, 7, 8, 9]]    
    print A.stacked(B, 0).formated()
    #[[1, 2, 3, 1, 2],
    # [4, 5, 6, 3, 4],
    # [1, 2, 3, 4, 5],
    # [0, 1, 2, 3, 4],
    # [5, 6, 7, 8, 9]]    
    B.resize((3, 5), 1)
    print B.formated()
    #[[0, 1, 2, 3, 4],
    # [5, 6, 7, 8, 9],
    # [1, 1, 1, 1, 1]]    
    print A.stacked(B, 1).formated()
    #[[1, 2, 3, 1, 2, 0, 1, 2, 3, 4],
    # [4, 5, 6, 3, 4, 5, 6, 7, 8, 9],
    # [1, 2, 3, 4, 5, 1, 1, 1, 1, 1]]
    
    A = Array(range(1, 9), shape=(2, 2, 2))
    print A.formated()
    #[[[1, 2],
    #  [3, 4]],
    #
    # [[5, 6],
    #  [7, 8]]]    
    A.append([9, 9], 1)
    print A.formated()
    #[[[1, 2],
    #  [3, 4],
    #  [9, 9]],
    #
    # [[5, 6],
    #  [7, 8],
    #  [9, 9]]]    
    B = Array(range(-1, -7, -1), shape=(2, 3, 1))
    print B.formated()
    #[[[-1],
    #  [-2],
    #  [-3]],
    #
    # [[-4],
    #  [-5],
    #  [-6]]]    
    A.stack(B, 2)
    print A.formated()
    #[[[1, 2, -1],
    #  [3, 4, -2],
    #  [9, 9, -3]],
    #
    # [[5, 6, -4],
    #  [7, 8, -5],
    #  [9, 9, -6]]]   
    A.append([0, 0, 0], 1)
    print A.formated()  
    #[[[1, 2, -1],
    #  [3, 4, -2],
    #  [9, 9, -3],
    #  [0, 0, 0]],
    #
    # [[5, 6, -4],
    #  [7, 8, -5],
    #  [9, 9, -6],
    #  [0, 0, 0]]]    
    A.append([0, 0, 0, 1], 2)
    print A.formated()  
    #[[[1, 2, -1, 0],
    #  [3, 4, -2, 0],
    #  [9, 9, -3, 0],
    #  [0, 0, 0, 1]],
    #
    # [[5, 6, -4, 0],
    #  [7, 8, -5, 0],
    #  [9, 9, -6, 0],
    #  [0, 0, 0, 1]]]    
             
    # fills and init with shape    
    A = Array.filled([0, 1, 2], 5)
    print "Array.filled([0, 1, 2], 5)"
    print A.formated() 
    # [0, 1, 2, 0, 0]
    A = Array.filled(2, (5,))
    print "A = Array.filled(2, (5,))"
    print A.formated()
    # [2, 2, 2, 2, 2]      
    A = Array.default((2, 2))
    print "A = Array.default((2, 2))"
    print A.formated()
    # [[0, 0],
    #  [0, 0]]
    A = Array.filled(1, (2, 2)) 
    print "A = Array.filled(1, (2, 2))"
    print A.formated()
    #[[1, 1],
    # [1, 1]]    
    A = Array.filled([1, 2, 3], (3, 3)) 
    print "A = Array.filled([1, 2, 3], (3, 3)) "
    print A.formated()
    #[[1, 2, 3],
    # [1, 2, 3],
    # [1, 2, 3]]    
    A = Array.filled([1, 2], (3, 3)) 
    print "Array.filled([1, 2], (3, 3))"
    print A.formated()  
    #[[1, 2, 0],
    # [1, 2, 0],
    # [1, 2, 0]]
    print "Array([1,2,3])"
    A = Array([1,2,3])
    print A.formated()
    # [1, 2, 3]
    print "Array([1,2,3], shape=(3, 3))"
    A = Array([1,2,3], shape=(3, 3))
    print A.formated()
    #[[1, 2, 3],
    # [1, 2, 3],
    # [1, 2, 3]]   
    print "Array([1,2,3], shape=(4, 4))"
    A = Array([1,2,3], shape=(4, 4))
    print A.formated()
    #[[1, 2, 3, 0],
    # [1, 2, 3, 0],
    # [1, 2, 3, 0],
    # [1, 2, 3, 0]]
    print "Array([[1,2,3]], shape=(4, 4))"  
    A = Array([[1,2,3]], shape=(4, 4))
    print A.formated()
    #[[1, 2, 3, 0],
    # [0, 0, 0, 0],
    # [0, 0, 0, 0],
    # [0, 0, 0, 0]]    
    print "A = Array([1, 2, 3, 4, 5], shape=(4, 4))"
    A = Array([1, 2, 3, 4, 5], shape=(4, 4))
    print A.formated()
    #[[1, 2, 3, 4],
    # [5, 0, 0, 0],
    # [0, 0, 0, 0],
    # [0, 0, 0, 0]]    
    print "A = Array([1, 2, 3, 4, 5], shape=(2, 2))"
    try :
        A = Array([1, 2, 3, 4, 5], shape=(2, 2))
    except :
        print "Would raise a ValueError: value of shape (5,) cannot be fit in a Array of shape (2, 2), some data would be lost"
       
    # copies and references
    B = Array([[1,1,1],[4,4,3],[7,8,5]])
    print B.formated()
    # init is a shallow copy
    C = Array(B) 
    print C.formated()
    print C == B
    # True    
    print C is B
    # False
    print C.data is B.data
    # False
    print C.data[0] is B.data[0]
    # True
    print C[0] is B[0]
    # True
    
    C = Array([B]) 
    print C.formated()
    print C[0] is B
    # True
    print C[0,0] is B[0]   
    # True  
        
    #shallow copy
    C = B.copy()
    print C.formated()
    print C == B
    # True     
    print C is B
    # False
    print C[0] is B[0]
    # True
    
    #deep copy   
    C = B.deepcopy()
    print C.formated()
    print C == B
    # True     
    print C is B
    # False
    print C[0] is B[0] 
    # False

        
    # indexing     
    A = Array([[[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]]])
    print A
    print repr(A)
    print repr(list(A))
    print repr(A.tolist())
    print repr(A.ravel())
    print "A:"
    print A.formated()
    #[[[1, 1, 1],
    #  [4, 4, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]    
    print "a = A[0]:"
    a = A[0]
    print a.formated()
    #[[1, 1, 1],
    # [4, 4, 3],
    # [7, 8, 5]]
    a[1, 1] = 5
    print "a[1, 1] = 5:"
    print a.formated()
    #[[1, 1, 1],
    # [4, 5, 3],
    # [7, 8, 5]]
    print "A[0]:"
    print A[0].formated()
    #[[1, 1, 1],
    # [4, 5, 3],
    # [7, 8, 5]]
    print "A[-1]:"
    print A[-1].formated()
    #[[10, 10, 10],
    # [40, 40, 30],
    # [70, 80, 50]]
    print "A[0, 2, 1]:"
    print A[0, 2, 1]
    # 8
    a = A[0, 2]
    print "a = A[0, 2]:"
    print a
    # [7, 8, 5]
    a[1] = 9
    print "a[1] = 9:"
    print a
    # [7, 9, 5]
    print "A[0, 2]:"
    print A[0, 2].formated()
    # [7, 9, 5]
    print "a = A[0, :, 1]:"
    a = A[0, :, 1]
    print a
    # [1 5 9]
    a[1] = 6
    print "a[1] = 6:"
    print a
    # [1 6 9]
    # not changing value because array had to be reconstructed
    print "A[0, :]:"
    print A[0, :].formated()
    #[[1 1 1]
    # [4 5 3]
    # [7 9 5]]
    # do it this way 
    A[0, :, 1] = [1, 6, 9]
    print "A[0, :, 1] = [1, 6, 9]"
    print A[0, :].formated()
    #[[1, 1, 1],
    # [4, 6, 3],
    # [7, 9, 5]]    
    print "A[0, :, 1:2]:"
    print A[0, :, 1:2].formated()
    #[[1]
    # [6]
    # [9]]
    print "A[0, 1:2, 1:2]:"
    print A[0, 1:2, 1:2].formated()
    #[[6]]
    print "A[0, :, 1:3]:"
    print A[0, :, 1:3].formated()
    #[[1 1]
    # [6 3]
    # [9 5]]
    print "A[:, :, 1:3]:"
    print A[:, :, 1:3].formated()
    #[[[ 1  1]
    #  [ 6  3]
    #  [ 9  5]]
    #
    # [[10 10]
    #  [40 30]
    #  [80 50]]]
    print "A[:, :, 1:2]:"
    print A[:, :, 1:2].formated()
    #[[[ 1]
    #  [ 6]
    #  [ 9]]
    #
    # [[10]
    #  [40]
    #  [80]]]
    
    # delete or strip items
    print "A="
    A = Array(xrange(1, 28), shape=(3, 3, 3))
    print A.formated()
    #[[[1, 2, 3],
    #  [4, 5, 6],
    #  [7, 8, 9]],
    #
    # [[10, 11, 12],
    #  [13, 14, 15],
    #  [16, 17, 18]],
    #
    # [[19, 20, 21],
    #  [22, 23, 24],
    #  [25, 26, 27]]]
    B = A[0]
    print "del A[1]"
    del A[1]
    print A.formated()
    #[[[1, 2, 3],
    #  [4, 5, 6],
    #  [7, 8, 9]],
    #
    # [[19, 20, 21],
    #  [22, 23, 24],
    #  [25, 26, 27]]]   
    C = A[0]
    print B is C
    # True
    B = A[0][0]
    print "del A[-1]"
    del A[-1]
    print A.formated()
    #[[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9]]]      
    C = A[0, 0]
    print B is C
    # True
    print "del A[None, None, 1:3]"
    del  A[None, None, 1:3]
    print A.formated()
    #[[[1],
    # [4],
    # [7]]]    
    print "del A[-1]"
    del A[-1]
    print A.formated()    
    # []
    
    print "A="
    A = Array(xrange(1, 28), shape=(3, 3, 3))
    print A.formated()
    #[[[1, 2, 3],
    #  [4, 5, 6],
    #  [7, 8, 9]],
    #
    # [[10, 11, 12],
    #  [13, 14, 15],
    #  [16, 17, 18]],
    #
    # [[19, 20, 21],
    #  [22, 23, 24],
    #  [25, 26, 27]]]
    B = A[0]
    print "A.strip(1)"
    A.strip(1)
    print A.formated()
    #[[[1, 2, 3],
    #  [4, 5, 6],
    #  [7, 8, 9]],
    #
    # [[19, 20, 21],
    #  [22, 23, 24],
    #  [25, 26, 27]]]   
    C = A[0]
    print B is C
    # True
    B = A[0][0]
    print "A.strip(-1)"
    A.strip(-1)
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9]]      
    C = A[0]
    print B is C
    # True
    print "A.strip(None, slice(1,3))"
    A.strip((None, slice(1,3)))
    print A.formated()
    #[[1],
    # [4],
    # [7]]    
    print "A.strip(-1)"
    A.strip(-1)
    print A.formated()
    #[[1],
    # [4]]  
    print "A.strip(-1)"
    A.strip(-1)
    print A.formated()   
    #[1]   
    print "A.strip(-1)"
    A.strip(-1)
    print A.formated()  
    #[]
    
    # iterators
    
    A = Array([[[1, 1, 1], [4, 6, 3], [7, 9, 5]], [[10, 10, 10], [40, 40, 30], [70, 80, 50]]])
    print "A:\n", A
    # [[[1, 1, 1], [4, 6, 3], [7, 9, 5]], [[10, 10, 10], [40, 40, 30], [70, 80, 50]]]
    print "list(A.flat):\n",list(A.flat)
    # [1, 1, 1, 4, 6, 3, 7, 9, 5, 10, 10, 10, 40, 40, 30, 70, 80, 50]
    print "A.flat[7]:\n", A.flat[7]
    # 9
    print "A.flat[2:12]:\n", A.flat[2:12]
    # [1, 4, 6, 3, 7, 9, 5, 10, 10, 10]
    A.flat[7] = 8
    print "A.flat[7] = 8"
    print A.formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]
        
    print "Array([a for a in A])"
    print Array([a for a in A]).formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]    
    print "Array([a for a in A.subiter()])"
    print Array([a for a in A.subiter()]).formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]] 
    print "Array([a for a in A.subiter(0)])"
    print Array([a for a in A.subiter(0)]).formated()
    # [1, 1, 1, 4, 6, 3, 7, 8, 5, 10, 10, 10, 40, 40, 30, 70, 80, 50]
    print "Array([a for a in A.subiter(1)])"
    print Array([a for a in A.subiter(1)]).formated()
    #[[1, 1, 1],
    # [4, 6, 3],
    # [7, 8, 5],
    # [10, 10, 10],
    # [40, 40, 30],
    # [70, 80, 50]]    
    print "Array([a for a in A.subiter(2)])"
    print Array([a for a in A.subiter(2)]).formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]   
    print "Array([a for a in A.axisiter()])"
    print Array([a for a in A.axisiter()]).formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]] 
    print "Array([a for a in A.axisiter(0)])"
    print Array([a for a in A.axisiter(0)]).formated() 
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]  
    print "Array([a for a in A.axisiter(0,1)])"
    print Array([a for a in A.axisiter(0,1)]).formated()   
    #[[1, 1, 1],
    # [4, 6, 3],
    # [7, 8, 5],
    # [10, 10, 10],
    # [40, 40, 30],
    # [70, 80, 50]] 
    print "Array([a for a in A.axisiter(0,1,2)])"
    print Array([a for a in A.axisiter(0,1,2)]).formated()   
    # [1, 1, 1, 4, 6, 3, 7, 8, 5, 10, 10, 10, 40, 40, 30, 70, 80, 50]
    print "Array([a for a in A.axisiter(2)])"
    print Array([a for a in A.axisiter(2)]).formated() 
    #[[[1, 4, 7],
    #  [10, 40, 70]],
    #
    # [[1, 6, 8],
    #  [10, 40, 80]],
    #
    # [[1, 3, 5],
    #  [10, 30, 50]]]  
    print "Array([a for a in A.axisiter(2,1)])"
    print Array([a for a in A.axisiter(2,1)]).formated()   
    #[[1, 10],
    # [4, 40],
    # [7, 70],
    # [1, 10],
    # [6, 40],
    # [8, 80],
    # [1, 10],
    # [3, 30],
    # [5, 50]] 
    print "Array([a for a in A.axisiter(2,1,0)])"
    print Array([a for a in A.axisiter(2,1,0)]).formated()   
    #[1, 10, 4, 40, 7, 70, 1, 10, 6, 40, 8, 80, 1, 10, 3, 30, 5, 50]

    # all iterator support item indexation
    
    print "A[0, 1, :] = [11, 66, 88]"
    A[0, :, 1] = [11, 66, 88]
    print A.formated()
    #[[[1, 11, 1],
    #  [4, 66, 3],
    #  [7, 88, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]     
    print "Array([a for a in A.axisiter(0,2)])"
    print Array([a for a in A.axisiter(0,2)]).formated() 
    #[[1, 4, 7],
    # [11, 66, 88],
    # [1, 3, 5],
    # [10, 40, 70],
    # [10, 40, 80],
    # [10, 30, 50]]
    print "A.axisiter(0,2)[1]"
    print A.axisiter(0,2)[1]
    # [11, 66, 88]
    print "A.axisiter(0,2)[1] = [1, 6, 8]"
    A.axisiter(0,2)[1] = [1, 6, 8]
    print A.formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]],
    #
    # [[10, 10, 10],
    #  [40, 40, 30],
    #  [70, 80, 50]]]
 
    
    # count, index
    
    print "A[:,:,1] = 2"
    A[:,:,1] = 2
    print A.formated()
    #[[[1, 2, 1],
    #  [4, 2, 3],
    #  [7, 2, 5]],
    #
    # [[10, 2, 10],
    #  [40, 2, 30],
    #  [70, 2, 50]]]        
    print "70 in A\n", 70 in A
    # True
    print "[4, 2, 3] in A\n", [4, 2, 3] in A
    # True
    print "A.count(2)\n", A.count(2)
    # 6
    print "A.index(2)\n", A.index(2)
    # (0, 0, 1)
    print "A.count([7, 2, 5])\n", A.count([7, 2, 5])
    # 1    
    print "A.index([7, 2, 5])\n", A.index([7, 2, 5])
    # (0, 2)
    print "A[0,2]\n", A[0,2]
    # [7, 2, 5]
    print "A.index([[10, 2, 10],[40, 2, 30],[70, 2, 50]])\n", A.index([[10, 2, 10],[40, 2, 30],[70, 2, 50]])
    # (1,)

    # resising and reshaping
    
    print "B=Array([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])"
    B = Array([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]     
    print "B.toshape((2, 2, 2, 2)):"
    print B.toshape((2, 2, 2, 2)).formated()
    #[[[[ 1  2]
    #   [ 3  4]]
    #
    #  [[ 5  6]
    #   [ 7  8]]]
    #
    #
    # [[[ 9 10]
    #   [11 12]]
    #
    #  [[13 14]
    #   [15 16]]]] 
    print "B.reshape((2, 2, 4)) or B.shape = (2, 2, 4)"
    B.reshape((2, 2, 4))
    print B.formated()
    #[[[1, 2, 3, 4],
    #  [5, 6, 7, 8]],
    #
    # [[9, 10, 11, 12],
    #  [13, 14, 15, 16]]]       
    print "B.tosize((4, 5)):"
    print B.tosize((4, 5)).formated()
    #[[ 1  2  3  4  5]
    # [ 6  7  8  9 10]
    # [11 12 13 14 15]
    # [16  0  0  0  0]]
    print "B.tosize((4, 5), 1):"
    print B.tosize((4, 5), 1).formated()
    #[[ 1  2  3  4  5]
    # [ 6  7  8  9 10]
    # [11 12 13 14 15]
    # [16  1  1  1  1]] 
    print "B.resize((2, 3, 3))"
    B.resize((2, 3, 3))
    print B.formated()
#    [[[1, 2, 3],
#      [4, 5, 6],
#      [7, 8, 9]],
#    
#     [[10, 11, 12],
#      [13, 14, 15],
#      [16, 0, 0]]] 
    print "B.resize((4, 4))"
    B.resize((4, 4))    
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]  
    print "B.trim((5, 5))"
    print B.trim((5, 5)).formated()
    #[[1, 2, 3, 4, 0],
    # [5, 6, 7, 8, 0],
    # [9, 10, 11, 12, 0],
    # [13, 14, 15, 16, 0],
    # [0, 0, 0, 0, 0]]
    print "B.trim((3, 2))"
    print B.trim((3, 2)).formated()
    #[[1, 2],
    # [5, 6],
    # [9, 10]]
    print "C = Array(B, shape=(5, 5))"
    C = Array(B, shape=(5, 5))
    print C.formated()       
    #[[1, 2, 3, 4, 0],
    # [5, 6, 7, 8, 0],
    # [9, 10, 11, 12, 0],
    # [13, 14, 15, 16, 0],
    # [0, 0, 0, 0, 0]]    
    print "C = Array(B, shape=(2, 4, 4))"
    C = Array(B, shape=(2, 4, 4))
    print C.formated()  
    #[[[1, 2, 3, 4],
    #  [5, 6, 7, 8],
    #  [9, 10, 11, 12],
    #  [13, 14, 15, 16]],
    #
    # [[1, 2, 3, 4],
    #  [5, 6, 7, 8],
    #  [9, 10, 11, 12],
    #  [13, 14, 15, 16]]]
    print "C = Array(B, shape=(3, 5))"
    C = Array(B, shape=(3, 6))
    print C.formated()     
    #[[1, 2, 3, 4, 5, 6],
    # [7, 8, 9, 10, 11, 12],
    # [13, 14, 15, 16, 0, 0]]   
    
              
    print "A = A + 2"
    A = A + 2
    print A.formated()
    #[[[3, 4, 3],
    #  [6, 4, 5],
    #  [9, 4, 7]],
    #
    # [[12, 4, 12],
    #  [42, 4, 32],
    #  [72, 4, 52]]]  
    print "1 + A" 
    print (1 + A).formated()
    #[[[4, 5, 4],
    #  [7, 5, 6],
    #  [10, 5, 8]],
    #
    # [[13, 5, 13],
    #  [43, 5, 33],
    #  [73, 5, 53]]]   
    print "B = Array(range(1, 17), shape=(4, 4))"    
    B = Array(range(1, 17), shape=(4, 4))     
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]        
    print "B = 2 * B:"
    B = 2 * B
    print B.formated()
    #[[2, 4, 6, 8],
    # [10, 12, 14, 16],
    # [18, 20, 22, 24],
    # [26, 28, 30, 32]] 
    print "Array(B, shape=A.shape):"
    print Array(B, shape=A.shape).formated()
    #[[[2, 4, 6],
    #  [8, 10, 12],
    #  [14, 16, 18]],
    #
    # [[20, 22, 24],
    #  [26, 28, 30],
    #  [32, 0, 0]]]          
    print "A+B:"
    print (A+B).formated()
    #[[[5, 8, 9],
    #  [14, 14, 17],
    #  [23, 20, 25]],
    #
    # [[32, 26, 36],
    #  [68, 32, 62],
    #  [104, 4, 52]]]  
    # always line on the larger Array to avoir truncating data       
    print "B+A"
    print (B+A).formated()
    #[[[5, 8, 9],
    #  [14, 14, 17],
    #  [23, 20, 25]],
    #
    # [[32, 26, 36],
    #  [68, 32, 62],
    #  [104, 4, 52]]]
    print "A-B:"
    print (A-B).formated()
    #[[[1, 0, -3],
    #  [-2, -6, -7],
    #  [-5, -12, -11]],
    #
    # [[-8, -18, -12],
    #  [16, -24, 2],
    #  [40, 4, 52]]]
    # always line on the larger Array to avoir truncating data       
    print "B-A"
    print (B-A).formated()
    #[[[-1, 0, 3],
    #  [2, 6, 7],
    #  [5, 12, 11]],
    #
    # [[8, 18, 12],
    #  [-16, 24, -2],
    #  [-40, -4, -52]]]
    print "A*B"
    print (A*B).formated()
    #[[[6, 16, 18],
    #  [48, 40, 60],
    #  [126, 64, 126]],
    #
    # [[240, 88, 288],
    #  [1092, 112, 960],
    #  [2304, 0, 0]]]         
    # smaller arrays are expanded, valid sub-arrays are repeated
    print "A+[100, 200]:"
    print (A+[100, 200]).formated()    
    #[[[103, 204, 3],
    #  [106, 204, 5],
    #  [109, 204, 7]],
    #
    # [[112, 204, 12],
    #  [142, 204, 32],
    #  [172, 204, 52]]]  
        
    print "-B"
    print (-B).formated()    
    #[[-2, -4, -6, -8],
    # [-10, -12, -14, -16],
    # [-18, -20, -22, -24],
    # [-26, -28, -30, -32]]   

    print "-B/2.0"
    print (-B/2.0).formated()    
    #[[-1.0, -2.0, -3.0, -4.0],
    # [-5.0, -6.0, -7.0, -8.0],
    # [-9.0, -10.0, -11.0, -12.0],
    # [-13.0, -14.0, -15.0, -16.0]]
         
    try : 
        print A+"abc"
    except TypeError :
        print "A+\"abc\" will raise TypeError: unsupported operand type(s) for +: 'Array' and 'str'"  
    
    # overriden math functions
    print "A = Array([[0, pi/4.0], [pi/2.0, 3.0*pi/4.0], [pi, 5.0*pi/4.0], [3.0*pi/2.0, 7.0*pi/4.0]])"
    A = Array([[0, pi/4.0], [pi/2.0, 3.0*pi/4.0], [pi, 5.0*pi/4.0], [3.0*pi/2.0, 7.0*pi/4.0]])
    print round(A,2).formated()
    #[[0.0, 0.79],
    # [1.57, 2.36],
    # [3.14, 3.93],
    # [4.71, 5.5]]   
    print "degrees(A)"
    print degrees(A).formated()
    #[[0.0, 45.0],
    # [90.0, 135.0],
    # [180.0, 225.0],
    # [270.0, 315.0]]    
    print "sin(A)"
    print round(sin(A), 2).formated()
    # [[0.0, 0.71],
    # [1.0, 0.71],
    # [0.0, -0.71],
    # [-1.0, -0.71]]
    print "A = clamp(Array([[0.0,0.5,1.0],[1.5,2.0,2.5]]), 0, 1)"
    print clamp(Array([[0.0,0.5,1.0],[1.5,2.0,2.5]]), 0.0, 1.0).formated()
    #[[0.0, 0.5, 1.0],
    # [1.0, 1.0, 1.0]]    
    print "A = gamma(Array([[0.0,0.5,1.0],[1.5,2.0,2.5]]), [0.0, 1.0, 2.0]"
    print gamma(Array([[0.0,0.5,1.0],[1.5,2.0,2.5]]), [1.0, 2.0, 3.0]).formated()
    #[[0.0, 0.25, 1.0],
    # [1.5, 4.0, 15.625]]
    # complex arrays
    print "A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]]) :"
    A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]])  
    print A.formated()
    #[[(1+2j), (2+3j)],
    # [(4+5j), (6+7j)]]      
    print "A.conjugate()"
    print A.conjugate().formated()
    #[[(1-2j), (2-3j)],
    # [(4-5j), (6-7j)]]    
    print "A.real() or real(A)"
    print A.real().formated()
    #[[1.0, 2.0],
    # [4.0, 6.0]]    
    print "A.imag() or imag(A)"
    print A.imag().formated()
    #[[2.0, 3.0],
    # [5.0, 7.0]]    
    print "abs(A)"
    print abs(A).formated() 
    #[[2.2360679775, 3.60555127546],
    # [6.40312423743, 9.21954445729]]
    
    # other methods

    A = Array([[1,2,3],[4,5,6]])    
    print A.formated()
    #[[1, 2, 3],
    # [4, 5, 6]]   
    print "A.sum() or A.sum(0,1) or sum(A) or sum(A, axis=(0,1))" 
    print A.sum()
    #21
    print "A.sum(0) or sum(A, axis=0)" 
    print A.sum(0)
    #[5, 7, 9]
    print sum(A, axis=0)
    #[5, 7, 9]
    print "A.sum(1) or sum(A, axis=1)" 
    print A.sum(1)
    #[6, 15]   
    print "A.prod() or prod(A)"
    print A.prod()
    #720
    print A.prod(0)
    #[4, 10, 18]
    print A.prod(1)    
    #[6, 120]
    
    A = Array([[6,3,4],[1,5,0.5]])
    print A.formated()
    #[[6, 3, 4],
    # [1, 5, 0.5]]    
    print min(A)
    #0.5
    print max(A)
    #6
    print list(A.axisiter(0))
    #[Array([6, 3, 4]), Array([1, 5, 0.5])]
    print A.min(0)
    #[1, 3, 0.5]
    print A.max(0)
    #[6, 5, 4]
    print list(A.axisiter(1))
    #[Array([6, 1]), Array([3, 5]), Array([4, 0.5])]
    print A.min(1)
    #[3, 0.5]
    print A.max(1)
    #[6, 5] 
    
    A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0]])
    print A.formated()  
    print round(A.length(), 2)
    print list(A.axisiter(0))
    print round(A.length(0), 2)
    print list(A.axisiter(1))
    print round(A.length(1), 2) 

    B = Array([[0.51,0.49,-0.71],[0.71,-0.70,0]])
    
    print sum([A, -B])
    
    print A.dist(B)
    print A.dist(B,0)
    print A.dist(B,1)
    
        
    C = Array([[0.501,0.499,-0.706],[0.706,-0.708,0.01]])
    print A.dist(C)
    print A.isEquivalent(C, 0.015)
    # True
    print A.isEquivalent(B, 0.015)
    # False
    print A.isEquivalent(B, 0.02)
    # True
    
    # boolean any and all
    
    A = Array([[True,True,True],[False,True,False]])
    print A.formated()
    print A.any()
    # True
    print A.all()
    # False
    print list(A.axisiter(0))
    # [Array([True, True, True]), Array([False, True, False])]
    print A.any(0)
    # [True, True, True]
    print A.all(0)
    # [False  True False]
    print list(A.axisiter(1))
    # [Array([True, False]), Array([True, True]), Array([True, False])]
    print A.any(1)
    # [True, True]
    print A.all(1)
    # [True, False]
               
               
    # transpose
    A = Array(range(18), shape=(2,3,3))
    print "Array(range(18), shape=(2,3,3))"
    print A.formated()
     
    
    print "B=A[0]"
    B=A[0]
    print B.formated()
 
 
    print "B.transpose()"
    print B.transpose().formated()
     
    print "A.transpose(0,2,1)"    
    print A.transpose(0,2,1).formated() 
  
    print "A.transpose(2,1,0)"
    print A.transpose(2,1,0).formated()




    # should fail
    print "B = Array([[1,2,3],[4,5,6],[7,8]])"
    try :
        B = Array([[1,2,3],[4,5,6],[7,8]])
    except :
        print "Will raise a ValueError: all sub-arrays must have same shape"
    B = Array([[1,2,3],[4,5,6],[7,8,9]])
    print "B = Array([[1,2,3],[4,5,6],[7,8,9]])"
    print B.formated()
    print "B[1] = [4, 5]"
    try :
        B[1] = [4, 5]
    except :
        print "Will raise a ValueError: shape mismatch between value(s) and Array components or sub Arrays designated by the indexing"

    print "end Array tests"
 
 
def _testMatrix() :   
    # Matrix and Vector
    
    # should fail
    print "M.resize((2, 2, 3))"
    try :
        M.resize((2, 2, 3))
    except :
        print "Will raise TypeError: shape (2, 2, 3) is incompatible with class Matrix"

    print "M = Matrix([[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])"
    try :
        M = Matrix([[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])
    except :
        print "Will raise TypeError: shape (2, 2, 3) is incompatible with class Matrix"
        
    print "M = Matrix([0, 1, 2])"
    try :
        M = Matrix([0, 1, 2])
    except :
        print "Will raise TypeError, class Matrix has a fixed number of dimensions 2 and it cannot be changed"
          
    # init and append
    print "M = Matrix([[0, 1, 2], [3, 4, 5]])"
    M = Matrix([[0, 1, 2], [3, 4, 5]])
    print M.formated()
    #[[0, 1, 2],
    # [3, 4, 5]]    
    print "M.append([6, 7, 8])"
    M.append([6, 7, 8])
    print M.formated()  
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]    
    # row and column
    print M.nrow
    M.nrow = 4
    print M.formated() 
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8],
    # [0, 0, 0]]    
    print M.ncol
    M.ncol = 4
    print M.formated()  
    #[[0, 1, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]
    print Array(M.row).formated()
    #[[0, 1, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]   
    print repr(M.row[0])
    # Array([0, 1, 2, 0])     
    print repr(M.row[0:2])
    # Matrix([[0, 1, 2, 0], [3, 4, 5, 0]])
    print Array(M.col).formated() 
    #[[0, 3, 6, 0],
    # [1, 4, 7, 0],
    # [2, 5, 8, 0],
    # [0, 0, 0, 0]]    
    print repr(M.col[-3:-1])
    # Matrix([[1, 4, 7, 0], [2, 5, 8, 0]])
    M.col[-1]  = [0, 0, 0, 1]
    print M.formated()
    #[[0, 1, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 1]] 
    print repr(M[:3, :3])
    # Matrix([[0, 1, 2], [3, 4, 5], [6, 7, 8]])
    print repr(M[:2, :2])
    # Matrix([[0, 1], [3, 4]])

    M = Matrix(range(1,10), shape=(3, 3))
    M.retrim((4, 4))
    M[3, 3] = 1
    print M.formated()
    #[[1, 2, 3, 0],
    # [4, 5, 6, 0],
    # [7, 8, 9, 0],
    # [0, 0, 0, 1]]   
    del M.col[3]
    print M.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9],
    # [0, 0, 0]]    
    del M.row[3]
    print M.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9]]
 
    # herited methods
    
    M = Matrix(range(0,9), shape=(3, 3))
    M.retrim((4, 4))
    M[3, 3] = 1
    print M.formated()
    #[[0, 1, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 1]]       
    print "2+M"
    print (2+M).formated() 
    #[[2, 3, 4, 2],
    # [5, 6, 7, 2],
    # [8, 9, 10, 2],
    # [2, 2, 2, 3]]
    print "M/2.0"
    print (M/2.0).formated() 
    #[[0.0, 0.5, 1.0, 0.0],
    # [1.5, 2.0, 2.5, 0.0],
    # [3.0, 3.5, 4.0, 0.0],
    # [0.0, 0.0, 0.0, 0.5]]     
    print "M*2"
    print (M*2).formated() 
    #[[0, 2, 4, 0],
    # [6, 8, 10, 0],
    # [12, 14, 16, 0],
    # [0, 0, 0, 2]]      
    N = Matrix(range(1,10), shape=(3, 3))
    print N.formated()
    # [[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9]]         
    print "M+N"  
    print (M+N).formated() 
    #[[1, 3, 5, 0],
    # [7, 9, 11, 0],
    # [13, 15, 17, 0],
    # [0, 0, 0, 1]]    

    #overloaded methods
    # matrix mult
    M = Matrix(range(1,13), shape=(4, 3))
    N = Matrix(range(0,120,10), shape=(3, 4))
    print "M:"
    print M.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9],
    # [10, 11, 12]]    
    print "*N:"
    print N.formated()
    #[[0, 10, 20, 30],
    # [40, 50, 60, 70],
    # [80, 90, 100, 110]]    
    print "M*N="    
    print (M*N).formated()
    #[[320, 380, 440, 500],
    # [680, 830, 980, 1130],
    # [1040, 1280, 1520, 1760],
    # [1400, 1730, 2060, 2390]]    
    print "N*M="
    print (N*M).formated()
    #[[480, 540, 600],
    # [1360, 1580, 1800],
    # [2240, 2620, 3000]]    
    
    # diagonal and trace
    M = Matrix(range(1,10), shape=(3, 3))
    M.nrow=4
    M.ncol=4
    M[3, 3]=1
    print M.formated()
    #[[1, 2, 3, 0],
    # [4, 5, 6, 0],
    # [7, 8, 9, 0],
    # [0, 0, 0, 1]]    
    print "M.diagonal()"
    print M.diagonal()
    #[1, 5, 9, 1]
    print M.trace()
    #16
    print M.diagonal(1)
    #[2, 6, 0]
    print M.trace(1)
    #8
    print M.diagonal(3, wrap=True)
    #[0, 4, 8, 0]
    print M.trace(3, wrap=True)
    #12

    M = Matrix([[1, 2],[3, 4]])
    print "M = Matrix([[1, 2],[3, 4]])"
    print M.formated()
    #[[1, 2],
    # [3, 4]]    
    print "M.adjugate()"  
    print M.adjugate().formated()
    #[[4.0, 2.0],
    # [3.0, 1.0]]      
    print "det(M)"  
    print det(M)
    # -2.0   
    print "M.inverse()"
    print M.inverse().formated()
    #[[-2.   1. ]
    # [ 1.5 -0.5]]
        
    M = Matrix([[0.5, 1, 2],[1, 1, 1],[0.5, 0.5, 2]])
    print "M = Matrix([[0.5, 1, 2],[1, 1, 1],[0.5, 0.5, 2]])"
    print M.formated()
    #[[0.5, 1, 2],
    # [1, 1, 1],
    # [0.5, 0.5, 2]] 
    print "M.adjugate()"
    print M.adjugate().formated()  
    #[[1.5, 1.0, -1],
    # [1.5, 0.0, -1.5],
    # [0.0, -0.25, -0.5]]         
    print "M.inverse()"
    print M.inverse().round(2).formated()
    #[[-2.0, 1.33, 1.33],
    # [2.0, 0.0, -2.0],
    # [0.0, -0.33, 0.67]]    

            
    M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])
    print "M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])"
    print M.formated()
    #[[1.5, 1.5, -2.12, 0.0],
    # [-0.29, 1.71, 1.0, 0.0],
    # [0.85, -0.15, 0.5, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]       
    print "M.inverse()"
    print M.inverse().round(2).formated()
    #[[0.17, -0.07, 0.85, 0.0],
    # [0.17, 0.43, -0.15, 0.0],
    # [-0.24, 0.25, 0.5, 0.0],
    # [0.21, -1.53, -2.06, 1.0]]    
  
    M = Matrix([ [1.0/(i+j) for i in xrange(1,7)] for j in xrange(6) ])
    print "M = Matrix([ [1.0/(i+j) for i in xrange(1,7)] for j in xrange(6) ])"
    print M.round(2).formated()
    #[[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
    # [0.5, 0.33, 0.25, 0.2, 0.17, 0.14],
    # [0.33, 0.25, 0.2, 0.17, 0.14, 0.13],
    # [0.25, 0.2, 0.17, 0.14, 0.13, 0.11],
    # [0.2, 0.17, 0.14, 0.13, 0.11, 0.1],
    # [0.17, 0.14, 0.13, 0.11, 0.1, 0.09]]    
    print M[:2, :2].gauss().round(2).formated()
    #[[1.0, 0.5],
    # [0.0, 0.08]]    
    print M[:2, :2].reduced().round(2).formated()
    #[[1.0, 0.0],
    # [0.0, 1.0]]    
    print M[:2, :2].det()
    #0.0833333333333
    print M[:2, :2].inverse().formated()
    #[[4.0, -6.0],
    # [-6.0, 12.0]]    
    
    print M[:3, :3].gauss().round(2).formated()
    #[[1.0, 0.5, 0.33],
    # [0.0, 0.08, 0.09],
    # [0.0, 0.0, -0.01]]    
    print M[:3, :3].reduced().round(2).formated()
    #[[1.0, 0.0, 0.0],
    # [0.0, 1.0, -0.0],
    # [0.0, 0.0, 1.0]]    
    print M[:3, :3].det()
    #0.000462962962963
    print M[:3, :3].inverse().formated()
    #[[   9.  -36.   30.]
    # [ -36.  192. -180.]
    # [  30. -180.  180.]] 
         
    print M[:4, :4].gauss().round(2).formated()
    #[[1.0, 0.5, 0.33, 0.25],
    # [0.0, 0.08, 0.09, 0.08],
    # [0.0, 0.0, -0.01, -0.01],
    # [0.0, 0.0, 0.0, 0.0]]    
    print M[:4, :4].reduced().round(2).formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, -0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]    
    print M[:4, :4].det()
    #1.65343915344e-07
    print M[:4, :4].inverse().round(0).formated()
    #[[16.0, -120.0, 240.0, -140.0],
    # [-120.0, 1200.0, -2700.0, 1680.0],
    # [240.0, -2700.0, 6480.0, -4200.0],
    # [-140.0, 1680.0, -4200.0, 2800.0]] 
    
    print M[:5, :5].gauss().round(2).formated()
    #[[1.0, 0.5, 0.33, 0.25, 0.2],
    # [0.0, 0.08, 0.09, 0.08, 0.08],
    # [0.0, 0.0, -0.01, -0.01, -0.01],
    # [0.0, 0.0, 0.0, 0.0, 0.0],
    # [0.0, 0.0, 0.0, -0.0, -0.0]]    
    print M[:5, :5].reduced().round(2).formated()
    #[[1.0, 0.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, -0.0, 0.0, -0.0],
    # [0.0, 0.0, 1.0, 0.0, -0.0],
    # [0.0, 0.0, 0.0, 1.0, -0.0],
    # [0.0, 0.0, 0.0, -0.0, 1.0]]    
    print M[:5, :5].det()
    #3.74929513252e-12
    print M[:5, :5].inverse().round(0).formated()
    #[[25.0, -300.0, 1050.0, -1400.0, 630.0],
    # [-300.0, 4800.0, -18900.0, 26880.0, -12600.0],
    # [1050.0, -18900.0, 79380.0, -117600.0, 56700.0],
    # [-1400.0, 26880.0, -117600.0, 179200.0, -88200.0],
    # [630.0, -12600.0, 56700.0, -88200.0, 44100.0]]    
    
    print M[:6, :6].gauss().round(2).formated()
    #[[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
    # [0.0, 0.08, 0.09, 0.08, 0.08, 0.07],
    # [0.0, 0.0, 0.01, 0.01, 0.01, 0.01],
    # [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    # [0.0, 0.0, 0.0, 0.0, -0.0, -0.0],
    # [0.0, 0.0, 0.0, 0.0, 0.0, -0.0]]    
    print M[:6, :6].reduced().round(2).formated()
    #[[1.0, 0.0, 0.0, 0.0, -0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0, -0.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]    
    print M[:6, :6].det()
    #5.36729988682e-18
    print M[:6, :6].inverse().round(0).formated()
    #[[36.0, -630.0, 3360.0, -7560.0, 7560.0, -2772.0],
    # [-630.0, 14700.0, -88200.0, 211680.0, -220500.0, 83160.0],
    # [3360.0, -88200.0, 564480.0, -1411200.0, 1512000.0, -582120.0],
    # [-7560.0, 211680.0, -1411200.0, 3628800.0, -3969000.0, 1552320.0],
    # [7560.0, -220500.0, 1512000.0, -3969000.0, 4410000.0, -1746360.0],
    # [-2772.0, 83160.0, -582120.0, 1552320.0, -1746360.0, 698544.0]]     
        
    print "end tests Matrix"
    
def _testVector() :
    
    U = Vector(1, 2, 3)
    print "U = Vector(1, 2, 3)"
    print U
    # [1, 2, 3]
    M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])
    print "M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])"
    print M.formated()
    #[[1.5, 1.5, -2.12, 0.0],
    # [-0.29, 1.71, 1.0, 0.0],
    # [0.85, -0.15, 0.5, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]  
    print "V = U*M[:3, :3]"
    V = U*M[:3, :3]
    print V
    # [3.47, 4.47, 1.38]
    print U*V
    # 16.55
    N = U^V
    print N
    # [-10.65, 9.03, -2.47]
    print N.normal()
    # [-0.751072956189, 0.63682523891, -0.17419250721]
    print U.dist(V)
    # 3.8504804895
    
    print M[:3, :3]*U
    # [-1.86, 6.13, 2.05]
    print U^M[:3, :3]
    # [2.59076337407, 0.574934882789, 1.76818272891]
    print (U^M[:3, :3]).normal()   
    # [0.812431999034, 0.180292612136, 0.554480676809]
 
    
    print V*M[:3, :3].inverse()
    # [1.0, 2.0, 3.0]
    print U*2
    # [2, 4, 6]
        
    # Vector of size 4 for Point
    P = Vector(1, 2, 3, 1)
    print "P = Vector(1, 2, 3, 1)"
    print P
    # [1, 2, 3, 1]
    print "Q = P*M"
    Q = P*M
    print Q
    # [4.47, 6.47, 4.38, 1.0]
    print P.dist(Q)
    # 5.82462015929    
    
    P*=M
    print P
    # [4.47, 6.47, 4.38, 1.0]    
    try :
        M*=P
    except :
        print "Will raise TypeError: class Matrix has a fixed number of dimensions 2 and it cannot be changed"
    
        
    print "end tests Vector"
    
    

if __name__ == '__main__' :
    _testArray()   
    _testMatrix()
    _testVector()
     
"""
A generic n-dimensionnal Array class serving as base for arbitrary length Vector and Matrix classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the neat multi index slicing, __getitem__ and __setitem__ as well
# as and item indexing for iterators,
# Tried to make the method names match so that it will be easier to include Numpy instead if desired.
# See http://www.numpy.org/

# TODO : try a numpy import and fallback to the included class if not successful ?

# TODO : trim should preserve sub-element identity, trimmed should a copy or deepcopy ? (resize / reshape should be checked as well

import operator, itertools, copy, inspect, sys

from arguments import isNumeric, clsname
from utilitytypes import readonly, metaReadOnlyAttr
from math import pi, exp
import math, mathutils, sys
eps = 1.0/sys.maxint
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

def _toCompOrArrayInstance(value, cls=None) :
    if cls == None :
        cls = Array
    if hasattr(value, '__iter__') :
        if not isinstance(value, cls) :
            value = cls(value)
    elif isNumeric(value) :
        # a single numeric value
        pass 
    else :
        raise TypeError, "invalid value type %s cannot be converted to %s" % (clsname(value), cls.__name__)   
    return value

def _shapeInfo(value) :
    shape, dim, size = None, None, None
    if isinstance(value, Array) :
        shape = value.shape
        dim = value.ndim
        size = value.size       
    elif hasattr(value, '__iter__') :
        value = Array(value)
        shape = value.shape
        dim = value.ndim
        size = value.size        
    elif isNumeric(value) :
        shape = ()
        dim = 0
        size = 1
    
    if shape is None :
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
  
# some other math functions operating on Arrays or derived classes

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

# Array specific functions that also exist as methods on the Array classes

def sqlength(a, axis=None):
    """ sqlength(a, axis) --> numeric or Array
        Returns square length of a, a*a or the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis) """
    a = Vector._convert(a)
    if isinstance(a, Vector) :
        # axis not used but this catches invalid axis errors
        # only valid axis for Vector is (0,)
        if axis is not None :
            try :
                axis = a._getaxis(axis, fill=True)
            except :
                raise ValueError, "axis 0 is the only valid axis for a MVector, %s invalid" % (axis)
        return a.sqlength()
    elif isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return a.sqlength(*axis)
    else :
        raise NotImplemented, "sqlength not implemented for %s" % (clsname(a))     

def length(a, axis=None):
    """ length(a, axis) --> numeric or Array
        Returns length of a, sqrt(a*a) or the square root of the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis) """
    return sqrt(sqlength(a, axis))

def normal(a, axis=None): 
    """ normal(a, axis) --> Array
        Return a normalized copy of self: self/length(self, axis) """
    a = Vector._convert(a)
    if isinstance(a, Vector) :
        # axis not used but this catches invalid axis errors
        # only valid axis for Vector is (0,)
        if axis is not None :
            try :
                axis = a._getaxis(axis, fill=True)
            except :
                raise ValueError, "axis 0 is the only valid axis for a MVector, %s invalid" % (axis)
        return a.normal()
    elif isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return a.normal(*axis)
    else :
        raise NotImplemented, "normal not implemented for %s" % (clsname(a))            
    
def dist(a, b, axis=None):
    """ dist(a, b, axis) --> float or Array
         Returns the distance between a and b, the length of b-a """
    a = Vector._convert(a)
    if isinstance(a, Vector) :
        # axis not used but this catches invalid axis errors
        # only valid axis for Vector is (0,)
        if axis is not None :
            try :
                axis = a._getaxis(axis, fill=True)
            except :
                raise ValueError, "axis 0 is the only valid axis for a MVector, %s invalid" % (axis)
        return a.dist()
    elif isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return a.dist(b, *axis)
    else :
        raise NotImplemented, "dist not implemented for %s" % (clsname(a))             

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
    """ A generic n-dimensional array class using nested lists for storage.
    
        Arrays can be built from numeric values, iterables, nested lists or other Array instances
    
        >>> A = Array()
        >>> A
        Array([])
        >>> A = Array(2)
        >>> A
        Array([2])
        >>> A = Array([[1, 2], [3, 4]])
        >>> print A.formated()
        [[1, 2],
         [3, 4]]
        >>> A = Array([1, 2], [3, 4])
        >>> print A.formated()
        [[1, 2],
         [3, 4]]
        >>> A = Array([[1, 2]])
        >>> print A.formated()
        [[1, 2]]
        >>> A = Array([1], [2], [3])
        >>> print A.formated()
        [[1],
         [2],
         [3]]
        >>> A = Array([[[1], [2], [3]]])
        >>> print A.formated()
        [[[1],
          [2],
          [3]]]
            
        You can query some Array characteristics with the properties shape, ndim (number of dimensions) and size,
        the total number of numeric components
        
        >>> A = Array(range(1, 10), shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9]]
        >>> A.shape
        (3, 3)
        >>> A.ndim
        2
        >>> A.size
        9
        
        Arrays are stored as nested lists and derive from the 'list' class.
        >>> list(A)
        [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
            
        You can pass optional shape information at creation with the keyword arguments
        shape, ndim and size. The provided data will be expanded to fit the desirable shape,
        either repeating it if it's a valid sub-array of the requested shape, or padding it with
        the Array default value (0 unless defined otherwise in an Array sub-class).
        
        Value will be repeated if it is a valid sub-array of the Array requested
        
        >>> A = Array(1, shape=(2, 2))
        >>> print A.formated()
        [[1, 1],
         [1, 1]]
         
        It will be padded otherwise 
         
        >>> A = Array(1, 2, shape=(4,))
        >>> print A.formated()
        [1, 2, 0, 0]
        
        Or a combination of both, first pad it to a valid sub-array then repeat it
        
        >>> A = Array(1, 2, shape=(4, 3))
        >>> print A.formated()
        [[1, 2, 0],
         [1, 2, 0],
         [1, 2, 0],
         [1, 2, 0]]

        To avoid repetition, you can use a nested list of the desired number of dimensions

        >>> A = Array([1,2,3], shape=(2, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [1, 2, 3]]
        >>> A = Array([[1,2,3]], shape=(2, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [0, 0, 0]]
        
        If sub-array and requested array have same number of dimensions, padding with row / columns
        will be used (useful for the Matrix sub-class or Array) 
        
        >>> A = Array(range(1, 10), shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9]]
        >>> B = Array(A, shape=(4, 4))
        >>> print B.formated()
        [[1, 2, 3, 0],
         [4, 5, 6, 0],
         [7, 8, 9, 0],
         [0, 0, 0, 0]]
            
        Initialization will not allow to truncate data, if you provide more arguments than the
        requested array shape can fit, it will raise an exception.
        Use an explicit trim / resize or item indexing if you want to extract a sub-array
  
        >>> A = Array([1, 2, 3, 4, 5], shape=(2, 2))
        Traceback (most recent call last):
            ...
        ValueError: cannot initialize a Array of shape (2, 2) from [1, 2, 3, 4, 5], some information would be lost, use an explicit resize or trim
     """
     
    __metaclass__ = metaReadOnlyAttr
    __slots__ = ['_data', '_shape', '_ndim', '_size']
    __readonly__ = ('apicls', 'data', 'shape', 'ndim', 'size')
    # internal storage type, is expected to have __iter__, __len__,__getitem__, __setitem__, __delitem__ methods
    apicls = list
    
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

    # When wrapping a class we can't or don't want to subclass, store it in _data
    # and only access it through the standard data property (as derived classes or base
    # classes of this class might directly subclass the class they wrap and not have a _data attribute)
    # no check is done on the validity of data 
    def _getdata(self):
        return self._data
    def _setdata(self, value):
        if isinstance(value, self.apicls) :
            self._data = value
        else :
            self._data = self.apicls(value)
        self._cacheshape() 
    def _deldata(self):
        del self._data[:]
        self._cacheshape()     
    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
    
    # for compatibility with herited types like MVector and MMatrix :
    # assign sets internal storage value (apicls) from an iterable
    def assign(self, value):
        if type(value) == type(self) :
            self.data = value.data
        else :
            self.data = self.__class__(value).data
        return self   
    # get returns internal storage value as a raw tuple / nested tuple
    # it's a raw dump of the stored components    
    def get(self):
        res = []
        for a in self :
            if isinstance(a, Array) :
                res.append(a.get())
            else :
                res.append(a)               
        return tuple(res)

    def isIterable(self):
        """ True if array is iterable (has a dimension of more than 0) """
        return self.ndim > 0

    @classmethod
    def _shapecheck(cls, shape):
        """ A check for fixed ndim / shape classes """
        try :
            shape, ndim, size = cls._defaultshape(shape, None, None)
            return True
        except :
            return False             

    @classmethod
    def _defaultshape(cls, shape=None, ndim=None, size=None):
        """ Checks provided shape and size vs class shape, dim and size,
            returns provided shape, dim and size if valid or
            class's default shape, dim, size tuple if they exist and none are provided """
            
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
                                
        if shape is not None :
            if not hasattr(shape, '__iter__') :
                newshape = (shape,)
            else :
                newshape = tuple(shape)
        else :
            if cls_shape is not None :
                newshape = cls_shape
            elif cls_ndim is not None :
                newshape = (-1,)*cls_ndim
            else :
                newshape = ()
        shapesize = shapedim = None
        if newshape :
            shapedim = len(newshape)
            if newshape and not list(newshape).count(-1) :
                shapesize = reduce(operator.mul, newshape, 1)
            
        if ndim is not None :
            newndim = ndim
        else :
            newndim = cls_ndim
                
        if newndim is not None :
            if not shapedim :
                newshape = newshape + (-1,)*newndim
            shapedim = len(newshape)
        else :
            newndim = shapedim
                                   
        if size is not None :
            newsize = size
        else :
            if shapesize is not None :
                newsize = shapesize
            else :
                newsize = cls_size     
            
        # check for conformity with class constants
        if cls_size is not None and newsize != cls_size :
            raise TypeError, "class %s has a fixed size %s and it cannot be changed" % (cls.__name__, cls_size)              
        if cls_ndim is not None and newndim != cls_ndim :
            raise TypeError, "class %s has a fixed number of dimensions %s and it cannot be changed" % (cls.__name__, cls_ndim)       
#            if newdim < cls_ndim :
#                newshape = tuple([1]*(cls_ndim-newdim) + newshape)
#                newdim = cls_ndim
#            else :
#                raise TypeError, "class %s has a fixed number of dimensions %s and it cannot be changed" % (cls.__name__, cls_ndim)
        if cls_shape is not None and newshape != cls_shape :
            raise TypeError, "class %s has a fixed shape %s and it cannot be changed" % (cls.__name__, cls_shape)  

        # check for coherence
        if newndim != shapedim :
            raise ValueError, "provided number of dimensions %s is incompatible with shape %s" % (newndim, newshape)        
        if shapesize is not None and newsize != shapesize :
            raise ValueError, "provided size %s is incompatible with shape %s" % (newsize, newshape)
        
        return newshape, newndim, newsize
                
    @classmethod
    def _expandshape(cls, shape=None, ndim=None, size=None, reference=None):
        """ Expands shape that contains at most one undefined number of components for one dimension (-1) using known size """ 
        
        # check shape vs class attributes   
        shape, ndim, size = cls._defaultshape(shape, ndim, size)         
    
        # default to ndim = 1 if none specified and not a class constant
        # ndim = 0 would mean a single numeric value and we don't convert them to Arrays
        if not shape :
            if not ndim :
                ndim = 1
            shape = (-1,)*ndim
        if not ndim :
            ndim = len(shape)
        newshape = list(shape)
        nb = newshape.count(-1)
        if size is None :
            if nb > 0 :
                raise ValueError, "cannot expand shape %s without an indication of size" % (shape,) 
            else :
                size = reduce(operator.mul, shape, 1)                    

        # expands unknown dimension sizes (-1) if size is known          
        if nb > 0 :
            if nb > 1 :
                # ambiguous specification, more than one unknown dimension, means multiple ways to conform to size
                # unless size is 0
                if size == 0 :
                    newshape = [0]*ndim
                    newsize = 0                 
                else :
                    raise ValueError, "can only specify one unknown dimension on shape %s to try and fit it to size %s" % (shape, size)
            else :
                newsize = 1
                for i, dim in enumerate(newshape) :
                    idim = int(dim)
                    if idim == -1 :
                        unknown = i
                        break
                    else :
                        newsize *= idim
                if newsize :
                    newshape[unknown] = size / newsize
                else :
                    newshape[unknown] = 0                      
                newsize = reduce(operator.mul, newshape, 1)
            if newsize != size :
                raise ValueError, "unable to match the required size %s with shape %s" % (size, shape)
            shape = tuple(newshape)                          
     
        if not cls._shapecheck(shape) :
            raise TypeError, "shape %s is incompatible with class %s" % (shape, cls.__name__)  
       
        return shape, ndim, size
                                                            
    def __new__(cls, *args, **kwargs ):
        """ Creates a new Array instance from one or several nested lists or numeric values """
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        
        # for new default size to 0 if not specified or class constant
        if size is None and not shape :
            size = 0
        shape, ndim, size = cls._expandshape(shape, ndim, size)
            
        # default value is set here (0 or [] for Arrays)  
        defval = 0
                                 
        new = super(Array, Array).__new__(Array)
        if shape :
            new.data = [defval]*shape[-1]
        else :
            new.data = []
        for d in reversed(shape[:-1]) :
            next = super(Array, Array).__new__(Array)
            if d :
                # warning doing this means all sub-arrays would actually be the same object
                # next.data = [new]*d
                next.data = [copy.deepcopy(new) for i in range(d)]
            else :
                next.data = [new]
            new = next
           
        result = super(Array, cls).__new__(cls)
        result.data = new.data
        return result
     
    def __init__(self, *args, **kwargs):
        """ __init__(...)
            a.__init__(...) initializes Array a from one or more iterable, nested lists or numeric values,
            see help(Array) for more information.
        """
                
        if args :
            cls = self.__class__
       
            data = None
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            # to accommodate some herited Maya api classes
            if hasattr(args, 'asMatrix') :
                args = args.asMatrix()                
            # if isinstance (args, Array) :
            if type(args) in (Array, Matrix, Vector) :
                # copy constructor
                data = super(Array, Array).__new__(Array)
                data.data = args
            elif hasattr(args, '__iter__') :
                largs = []
                subshapes = []
                for arg in args :
                    # sub is either also an Array or a single numeric value
                    sub = _toCompOrArray(arg)
                    subshape, subdim, subsize = _shapeInfo(sub)                    
                    largs.append(sub)
                    subshapes.append(subshape)
                if not reduce(lambda x, y : x and y == subshapes[0], subshapes, True) :
                    raise ValueError, "all sub-arrays must have same shape"
                data = super(Array, Array).__new__(Array)
                data.data = largs              
            elif isNumeric(args) :
                # allow initialize from a single numeric value
                data = args  
            else :
                raise TypeError, "an %s element can only be another Array, an iterable of numerics or a numeric value" % (cls.__name__)
            
            if data is not None :
                # can re-shape on creation if self if of a specific diferent shape
                dshape, dndim, dsize = _shapeInfo(data)
                shape, ndim, size = _shapeInfo(self)
                if not size :
                    # if self was initialized by __new__ with a zero size, then if will adapt to the argument size,
                    # if class restrictions allow
                    shape, ndim, size = cls._defaultshape(None, None, None)                  
                if not size :
                    size = dsize                     
                if not shape :
                    if dshape :
                        # data is an Array
                        shape = dshape
                    else :
                        # data is single numeric
                        shape = (1,) 
                if not ndim :
                    ndim = len(shape)
                                                           
                if shape != dshape :
                    # accept expanding but not shrinking to catch casting errors
                    # will initialize self to at least an empty Array or an array of one numeric value, 

                    # multiple -1 (Matrix init for instance)
                    shape = list(shape)
                    unknown = shape.count(-1)
                    # multiple unknown dimensions can't be expanded with the size info, we'll use the new shape instead
                    if unknown > 1 :
                        difdim = max(ndim-dndim, 0)
                        # replace extra unknown dimensions with 1 from first dimensions
                        for i in range(difdim) :
                            if unknown > 1 :
                                if shape[i] == -1 :
                                    shape[i] = 1
                                    unknown -= 1
                            else :
                                break                        
                        # then for the last unkown dimensions, consider them common to the target class and data, copy data's
                        for i in range(difdim, ndim) :
                            if unknown > 1 :
                                if shape[i] == -1 :
                                    shape[i] = dshape[i+difdim]
                                    unknown -= 1
                            else :
                                break
                    shape = tuple(shape)
                     
                    shape, ndim, size = cls._expandshape(shape, ndim, size)
                    
                    # reshape / resize / retrim if needed
                    if shape != dshape :
                        if not dshape : 
                            data = Array.filled(data, shape)
                        else :
                            if size >= dsize and ndim >= dndim :                   
                                if ndim == dndim and reduce(operator.and_, map(operator.ge, shape, dshape), True) :
                                    data = data.trimmed(shape)
                                else :
                                    try :
                                        data = Array.filled(data, shape)
                                    except :                            
                                        data = data.resized(shape)
                            else :
                                if isinstance (args, Array) :
                                    raise TypeError, "cannot cast a %s of shape %s to a %s of shape %s, some information would be lost, use an explicit resize or trim" % (clsname(args), args.shape, cls.__name__, shape)
                                else :
                                    raise ValueError, "cannot initialize a %s of shape %s from %s, some information would be lost, use an explicit resize or trim" % (cls.__name__, shape, args)                          
                            
                # check that the shape is compatible with the class, as some Array sub classes have fixed shapes / ndim
                if not cls._shapecheck(data.shape) :
                    raise TypeError, "shape of arguments %s is incompatible with class %s" % (data.shape, cls.__name__)            
    
                self.data = data.data
            else :
                raise ValueError, "could not initialize a %s from the provided arguments %s" % (cls.__name__, args)

    @classmethod
    def filled(cls, value=None, shape=None, size=None):
        """ cls.filled([value[, shape[, size]]]) :
            Returns a cls instance of the given shape filled with value for the given shape,
            if no value is given, a default instance of that shape is returned.
            Value will be expended with the class default values to the nearest matching sub array
            of the class, then repeated.
            Value can't be truncated and will raise an error if of a size superior to the size of
            the nearest matching sub array of the class, to avoid improper casts """
        
        shape, ndim, size = cls._expandshape(shape, None, size)
        new = cls(shape=shape) 
        
        if value is not None :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if not shape :
                return cls(value, shape=vshape)               

            if vdim <= ndim and vsize <= size:
                subshape = shape[ndim-vdim:]
                if subshape != vshape :
                    subsize = reduce(operator.mul, subshape, 1)
                    if subsize >= vsize :
                        value.resize(subshape)
                    else :
                        raise ValueError, "value of shape %s cannot be fit in a %s of shape %s, some data would be lost" % (vshape, cls.__name__, shape)
                if vdim < ndim :                
                    iter = new.subiter(vdim)
                    for i in xrange(len(iter)) :
                        iter[i] = value    
                else :
                    new = cls(value, shape=shape)  
            else :
                raise ValueError, "fill value has more dimensions or is larger than the specified desired shape"
            
        return new 
        
    def fill(self, value=None, shape=None, size=None):     
        """ a.fill([value[, shape[, size]]])  :
            Fills the array in place with the given value, if no value is given a is set to the default class instance of same shape """
        if shape is None :
            shape = self.shape            
        new = self.__class__.filled(value, shape, size)
        if type(new) is type(self) :
            self.assign(new)
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))    

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
        itemdim = len(itemshape)
        if itemshape :
            other = Array.filled(other, itemshape)
        else :
            other = Array(other)
        if size :
            if axis > 0 :
                staxis = range(axis, -1, -1)+range(axis+1, dim)
                nself = self.transpose(staxis)          
                otaxis = staxis[1:]
                for i, a in enumerate(otaxis) :
                    if a > axis :
                        otaxis[i] = a-1
                nother = other.transpose(otaxis)
                if nother.ndim == itemdim :
                    nother = Array([nother])                              
                new = Array(list(nself)+list(nother))
                new = new.transpose(staxis)           
            else :
                if other.ndim == itemdim :
                    other = Array([other])                       
                new = Array(list(self)+list(other))        
        elif odim == 0 :
            if other.ndim == itemdim :
                other = Array([other])                   
            new = other
        
        try :
            return self.__class__._convert(new)
        except :
            raise ValueError, "cannot append a %s of shape %s on axis %s of %s of shape %s" % (clsname(other), oshape, axis, clsname(self), shape)
    
    def append(self, other, axis=0):
        """ Appends other to self on the given axis """
        new = self.appended(other, axis)
        if type(new) is type(self) :
            self.assign(new)
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
            self.assign(new)
        else :
            raise ValueError, "new concatenated shape %s is not compatible with class %s" % (shape, clsname(self))
                     
    def hstacked(self, other) :
        return self.stacked(other, -1)

    def hstack(self, other) :
        self.stack(other, -1)

    def vstacked(self, other) :
        return self.stacked(other, 0)

    def vstack(self, other) :
        self.stack(other, 0)
    
    def extended(self, other):
        return self.stacked(other, 0)

    def extend(self, other):
        return self.stack(other, 0)

#    def repeated(self, repeat, axis):
#    # alow repeat onn multiple axis ..
#        pass
#    
#    def repeat(self, repeat, axis):
#        pass
    
    # TODO : override and redefine these list herited methods for Arrays
    def insert(self, index, other):
        raise NotImplemented, "insert is not implemented for class %s" % (clsname(self))

    def __reversed__(self, axis=None):
        raise NotImplemented, "__reversed__ is not implemented for class %s" % (clsname(self))
    
    def reverse(self, axis=None):
        raise NotImplemented, "reverse is not implemented for class %s" % (clsname(self))    
    
    def pop(self, index):
        raise NotImplemented, "pop is not implemented for class %s" % (clsname(self))  

    def remove(self, value):
        raise NotImplemented, "remove is not implemented for class %s" % (clsname(self))  
    
    def sort(self, axis=None):
        raise NotImplemented, "sort is not implemented for class %s" % (clsname(self))      
 
    def reshaped(self, shape=None):
        """ a.reshaped(shape)
            Returns the Array as reshaped according to the shape argument """
        ndim = None
        size = self.size
        newshape, newndim, newsize = self.__class__._expandshape(shape, ndim, size)
        if newsize != size :
            raise ValueError, "total size of new Array must be unchanged"
        
        return self.resized(tuple(newshape))
    
    def reshape(self, shape=None):
        """ a.reshape(shape)
            Performs in-place reshape of array a """
        new = self.reshaped(shape)
        if type(new) is type(self) :
            self.assign(new)
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))
              
    def resized(self, shape=None, value=None):
        """ a.resized([shape [, value]])
            Returns the Array as resized according to the shape argument.          
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        cls = self.__class__
        newshape, newndim, nsize = cls._expandshape(shape, None, None)           
      
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

    def resize(self, shape=None, value=None):
        """ a.resize(shape)
            Performs in-place resize of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        new = self.resized(shape, value)
        if type(new) is type(self) :
            self.assign(new)
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))

    def _fitloop(self, source):       
        ldst = len(self)
        lsrc = len(source)
        lmin = min(ldst, lsrc)
        ndim = min(source.ndim, self.ndim)
            
        # copy when common
        for i in xrange(lmin) :
            if ndim > 1 :
                self[i]._fitloop(source[i])
            else :
                self[i] = source[i]

    def fitted(self, other): 
        """ a.fitted(b) --> Aray
            Returns the result of fitting the Array b in a.
            For every component of a that exists in b (there is a component of same coordinates in b),
            replace it with the value of the corresponding component in b.
            Both Arrays a and b must have same number of dimensions """           
        new = self.deepcopy()
        new.fit(other)
        return new    
        
    def fit(self, other): 
        """ a.fit(b)
            Fits the Array b in a.
            For every component of a that exists in b (there is a component of same coordinates in b),
            replace it with the value of the corresponding component in b.
            Both Arrays a and b must have same number of dimensions """   
        other = Array(other)
        if self.ndim != other.ndim :
            raise ValueError, "can only fit one Array in another if they have the same number of dimensions"
        self._fitloop(other)
           
    def _trimloop(self, source): 
        ldst = len(self)
        lsrc = len(source)
        lmin = min(ldst, lsrc)
        ndim = min(source.ndim, self.ndim) 

        # trim sub dimensions when common
        if ndim > 1 :
            for i in xrange(lmin) :
                self[i]._trimloop(source[i])  
                # lst = list(self) 
        self._cacheshape()        
                                 
        # add if needed
        for i in range(ldst, lsrc) :
            self.append(source[i])
        # or remove if needed
        for i in range(ldst-1, lsrc-1, -1) :
            del self[i]
        # update shape
        self._cacheshape() 
        # self.data = lst          
                                            
    def trimmed(self, shape=None, value=None):
        """ a.trimmed([shape [, value]]) --> Array
            Returns the Array as "trimmed", re-sized according to the shape argument.
            The difference with a resize is that each dimension will be resized individually,
            thus the shape argument must have the same number of dimensions as the Array a.
            A value of -1 or None for a shape dimension size will leave it unchanged         
            An optional value argument can be passed and will be used to fill
            the newly created components if the trimmed results in a size increase. """
        if shape is None :
            newshape = []
        else :
            newshape = list(shape)
        newndim = len(newshape)
        if newndim != self.ndim :
            raise ValueError, "can only trim using a new shape of same number of dimensions as Array"
        oldshape = self.shape
        for i in xrange(newndim) :
            if newshape[i] == -1 or newshape[i] is None :
                newshape[i] = oldshape[i]
              
        new = Array.filled(value, newshape)
        new._fitloop(self)
        new = self.__class__._convert(new)

        return new
    
    def trim(self, shape=None, value=None):
        """ a.trim(shape)
            Performs in-place trimming of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        if shape is None :
            newshape = []
        else :
            newshape = list(shape)
        newndim = len(newshape)
        if newndim != self.ndim :
            raise ValueError, "can only trim using a new shape of same number of dimensions as Array"
        oldshape = self.shape
        for i in xrange(newndim) :
            if newshape[i] == -1 or newshape[i] is None :
                newshape[i] = oldshape[i]
         
        if self.__class__._shapecheck(newshape) :   
            source = self.__class__.filled(value, newshape)
            self._trimloop(source)
        else :
            raise TypeError, "new shape %s is not compatible with class %s" % (shape, clsname(self)) 
  
    def __reduce__(self):
        return (self.__class__, tuple(self))
    
#    def __getnewargs__(self):
#        return tuple(self)    
 
    def copy(self):
        return copy.copy(self)
    
    def deepcopy(self):
        return copy.deepcopy(self) 
    
    # display      
    def __str__(self):
        return "[%s]" % ", ".join( map(str,self) )

    def __unicode__(self):
        return u"[%s]" % u", ".join( map(unicode,self) )
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self)) 
    
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
        """ Length of the first dimension of the array, ie len of the array considered as list """
        return self.apicls.__len__(self.data)
        
    @staticmethod
    def _extract(x, index) :
        if isinstance(x, Array) :
            res = x.apicls.__getitem__(x.data, index)
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
        value = self.__class__._toCompOrConvert(value)
        # value = _toCompOrArray(value)
        # print "value and id", value, id(value)
        return value

    # deprecated and __getitem__ should accept slices anyway
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start, end))

    def _inject(self, index, value) :
        indices = range(self.shape[0])[index[0]]
        if not hasattr(indices, '__iter__') :
            indices = [indices]
        ni = len(indices)
        shape = self.shape
        dim = self.ndim
        if len(index) == 1 : 
            # single dimension index last check and assign        
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
                    self.apicls.__setitem__(self.data, indices[i], values[i])
            else :
                raise ValueError, "shape mismatch between value(s) and Array components or sub Arrays designated by the indexing"
        else :
            # multi dimension index
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
                self[indices[i]]._inject(nextindex, values[i])

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

    # deprecated and __setitem__ should accept slices anyway
    def __setslice__(self, start, end, value):
        self.__setitem__(slice(start, end), value)

    def _delete(self, index) :
        ls = len(self)
        li = len(index)
        if ls and li :
            next = li > 1
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    self.apicls.__delitem__(self.data, i)
                elif next :      
                    self[i]._delete(index[1:])
                
    def __delitem__(self, index) :
        """ Delete elements that match index from the Array """
        index = self._getindex(index, default=None, expand=True)
        # TODO : check what shape it would yield first
        if index :
            self._delete(index)
            self._cacheshape()
            if not self.__class__._shapecheck(self.shape) :
                raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    # deprecated and __setitem__ should accept slices anyway
    def __delslice__(self, start):
        self.__delitem__(slice(start, end))

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
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    self.apicls.__delitem__(self.data, i)
                elif next :      
                    self[i]._strip(index[1:])
            if len(self) == 1 and hasattr(self[0], '__iter__') :
                self.assign(self[0])

    def strip(self, index) :
        """ Strip elements that match index from the Array, extra dimensions will be stripped  """
        index = self._getindex(index, default=None, expand=True)
        # TODO : check what shape it would yield first
        if index :
            self._strip(index)
            self._cacheshape()
            if not self.__class__._shapecheck(self.shape) :
                raise TypeError, "stripping %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))
    
    def stripped(self, index):
        """ Returns a copy of self without the index elements, extra dimensions will be stripped """
        index = self._getindex(index, default=None, expand=True)
        if index :
            a = self.deepcopy()
            a._strip(index)
            return self.__class__._convert(a)
                        
    def __iter__(self, *args, **kwargs) :
        """ Default Array iterator on first dimension """
        return self.apicls.__iter__(self.data, *args, **kwargs)
     
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
        """ a.__equ__(b) <==> a == b
            Equivalence operator, will only work for exact same type of a and b, check isEquivalent method to have it
            convert a and b to a common type (if possible) """
        if type(self) != type(other) :
            return False
        if self.shape != other.shape :
            return False
        return reduce(lambda x, y : x and y[0]==y[1], itertools.izip(self, other), True )
    def __ne__(self, other):
        return (not self.__eq__(other))           
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
    def _convert(cls, value, preserveShape=True): 
        if preserveShape :
            try :
                array = Array(value)
                shape = array.shape
            except :
                raise TypeError, "%s cannot be converted to Array or any Array sub-class" % (clsname(value))
        else :
            shape = None
        for c in inspect.getmro(cls) :
            if issubclass(c, Array) :
                if isinstance(value, c) :
                    # return value directly so we don't add a shallow copy if type is already ok
                    return value
                else :
                    try :
                        # use array as if value was a generator, it would not be able to iterate again
                        return c(array, shape=shape)
                    except :
                        pass
        raise TypeError, "%s cannot be converted to %s" % (clsname(value), cls.__name__)

    @classmethod
    def _toCompOrConvert(cls, value):
        if isinstance(value, cls) :
            return value
        elif hasattr(value, '__iter__') :
            return cls._convert(value, preserveShape=True)
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
        """ check and expand index on Array,
        
            >>> A = Array(1, shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 1, 1],
              [1, 1, 1],
              [1, 1, 1]],
            <BLANKLINE>
             [[1, 1, 1],
              [1, 1, 1],
              [1, 1, 1]],
            <BLANKLINE>
             [[1, 1, 1],
              [1, 1, 1],
              [1, 1, 1]]]
            >>> A._getindex((slice(2,8),-1), default=slice(None))
            (slice(2, 3, 1), 2, slice(0, 3, 1))
            >>> A._getindex((slice(2,8),-1), default=slice(None), expand=True)
            ([2], [2], [0, 1, 2])
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
        axis = self._getaxis(args, fill=True)
        it = self.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return reduce(operator.add, map(lambda x:x*x, it)) 
        else :
            return Array(a.sqlength() for a in it)          
    def length(self, *args):
        return sqrt(self.sqlength(*args))    
    def normal(self, *args):
        try :
            return self / self.length(*args)
        except :
            return self  
    def normalize(self, *args):
        """ Performs an in place normalization of self """
        self.assign(self.normal(*args))       
    def dist(self, other, *args):
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return (nother-nself).length(*args)            
    def distanceTo(self, other):
        return self.dist(other)
  
    def isEquivalent(self, other, tol=eps):
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
                return nself.dist(nother) <= tol
        
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
    def blend(self, other, weight=0.5):
        """ u.blend(v, weight) returns the result of blending from Array instance u to v according to
            either a scalar weight where it yields u*(1-weight) + v*weight Array,
            or a an iterable of up to 3 (x, y, z) independent weights """
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented             
        return self.__class__._convert(blend(self, other, weight))      
    def clamp(self, low=0.0, high=1.0):
        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
            or the corresponding components of low and high if low and high are sequences of scalars """
        return self.__class__._convert(clamp(self, low, high))
        
# functions that work on Matrix

def det(value):
    if isinstance(value, Matrix) :
        return value.det()
    elif isNumeric(value) :
        return value
    else :
        try :
            value = Matrix(value)
        except :
            raise TypeError, "%s not convertible to Matrix" % (clsname(value))
        return value.determinant()
    
def inv(value):
    if isinstance(value, Matrix) :
        return value.inverse()
    elif isNumeric(value) :
        return 1.0 / value
    else :
        try :
            value = Matrix(value)
        except :
            raise TypeError, "%s not convertible to Matrix" % (clsname(value))
        return value.inverse()
    
class Matrix(Array):
    """
    A generic size Matrix class, basically a 2 dimensional Array
    """
    __slots__ = ['_data', '_shape', '_size']    
    
    #A Matrix is a two-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 2
           
    def _getshape(self):
        if len(self) :
            return (len(self), len(self[0]))
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
    
    @classmethod
    def basis(cls, u, v, normalize=False):
        """ basis(u, v[, normalize=False]) --> Matrix
            Returns the basis Matrix built using u, v and u^v as coordinate axis,
            The a, b, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
                n = u ^ v
                v = n ^ u
            if the normalize keyword argument is set to True, the vectors are also normalized """
        u = Vector(u)
        v = Vector(v)
        assert len(u) == len(v) == 3, 'basis is only defined for two Vectors of size 3'    
        if normalize :
            u = normal(u)
            n = normal(cross(u, v))
            v = cross(n, u)
        else :
            n = cross(u, v)
            v = cross(n, u)
        return cls(Matrix(u, v, n).transpose())
 
    # row and column size properties
    def _getnrow(self):
        return self.shape[0]
    def _setnrow(self, m):
        self.trim((m, self.shape[1]))
    nrow = property(_getnrow, _setnrow, None, "Number of rows in this Matrix")          
    def _getncol(self):
        return self.shape[1]
    def _setncol(self, n):
        self.trim((self.shape[0], n))
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

    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a Matrix, __mul__ is mapped to matrix multiplication, if b is a Vector, to Matrix by Vector multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, Matrix) :
            return self.__class__._convert( [ [ dot(row,col) for col in other.col ] for row in self.row ] )
        elif isinstance(other, Vector) :
            if other.size <= self.shape[1] :
                return other.__class__._convert( [ dot(row, other) for row in self.row ] [:other.size] )
            else :
                raise ValueError, "matrix of shape %s and vector of size %s are not conformable for a Matrix * Vector multiplication" % (self.size, other.shape) 
        else :
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a Matrix, __rmul__ is mapped to matrix multiplication, if b is a Vector, to Vector by Matrix multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """        
        if isinstance(other, Matrix) :
            return Matrix( [ [ dot(row,col) for col in self.col ] for row in other.row ] )
        elif isinstance(other, Vector) :
            if other.size <= self.shape[0] :
                return other.__class__._convert( [ dot(col, other) for col in self.col ] [:other.size] )
            else :
                raise ValueError, "vector of size %s and matrix of shape %s are not conformable for a Vector * Matrix multiplication" % (other.size, self.shape)           
        else :
            return Array.__rmul__(self, other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of Matrix a and b, see __mul__, result must fit a's type """ 
        res = self*other
        if isinstance(res, self.__class__) :
            return self.__class__(res)        
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self)) 
    
    # specific methods
    
    def diagonal(self, offset=0, *args, **kwargs) :
        """ a.diagonal([offset=0[, wrap=False]]) -> diagonal
            Returns the diagonal of the Matrix with the given offset,
            i.e., the collection of elements of the form a[i,i+offset].
            If keyword wrap=True will wrap out of bounds indices
            
            Examples

            >>> M = Matrix(range(4), shape=(2, 2))
            >>> print M.formated()
            [[0, 1],
             [2, 3]]
            >>> M.diagonal()
            Array([0, 3])
            >>> M.diagonal(1)
            Array([1])
            >>> M.diagonal(1, wrap=True)
            Array([1, 2])
            >>> M.diagonal(-1, wrap=True)
            Array([1, 2])
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
        assert self.is_square(), "Adjugate Matrix can only be computed for a square Matrix"
        n = self.nrow
        if n == 1 :
            a = self.__class__([[1]])
        elif n == 2 :
            a = self.__class__( [ [ self[1,1], -self[0,1] ],    \
                                  [-self[1,0], self[0,0] ] ] )
        elif n == 3 :
            a = self.__class__( [ [  (self[1,1]*self[2,2]-self[1,2]*self[2,1]), -(self[0,1]*self[2,2]-self[0,2]*self[2,1]),  (self[0,1]*self[1,2]-self[0,2]*self[1,1]) ], \
                                  [ -(self[1,0]*self[2,2]-self[1,2]*self[2,0]),  (self[0,0]*self[2,2]-self[0,2]*self[2,0]), -(self[0,0]*self[1,2]-self[0,2]*self[1,0]) ], \
                                  [  (self[1,0]*self[2,1]-self[1,1]*self[2,0]), -(self[0,0]*self[2,1]-self[0,1]*self[2,0]),  (self[0,0]*self[1,1]-self[0,1]*self[1,0]) ] ] )         
        else :
            # generic cofactor expansion method
            a = self.__class__([[self.cofactor(j, i) for j in xrange(n)] for i in xrange(n)])
            
        return a
        
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
                raise ZeroDivisionError, "Matrix is singular"
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
    
    def determinant(self):
        assert self.is_square(), "determinant is only defined for a square Matrix"
        n = self.nrow
        if n == 1:
            d = self[0,0]
        elif n == 2:
            d = self[0,0]*self[1,1] - self[0,1]*self[1,0]
        elif n == 3:
            # direct Leibniz formula
            d = self[0,0]*self[1,1]*self[2,2] + self[0,2]*self[1,0]*self[2,1] + self[0,1]*self[1,2]*self[2,0] \
                - self[0,2]*self[1,1]*self[2,0] - self[0,0]*self[1,2]*self[2,1] - self[0,1]*self[1,0]*self[2,2]
        elif n == 4:
            # using Laplace expansion theorem             
            s0 = self[0,0]*self[1,1] - self[0,1]*self[1,0]
            s1 = self[0,0]*self[1,2] - self[0,2]*self[1,0]
            s2 = self[0,0]*self[1,3] - self[0,3]*self[1,0]           
            s3 = self[0,1]*self[1,2] - self[0,2]*self[1,1]   
            s4 = self[0,1]*self[1,3] - self[0,3]*self[1,1] 
            s5 = self[0,2]*self[1,3] - self[0,3]*self[1,2] 
                                                         
            c0 = self[2,2]*self[3,3] - self[2,3]*self[3,2]
            c1 = self[2,1]*self[3,3] - self[2,3]*self[3,1]
            c2 = self[2,1]*self[3,2] - self[2,2]*self[3,1]
            c3 = self[2,0]*self[3,3] - self[2,3]*self[3,0]
            c4 = self[2,0]*self[3,2] - self[2,2]*self[3,0]
            c5 = self[2,0]*self[3,1] - self[2,1]*self[3,0]
              
            d = s0*c0 - s1*c1 + s2*c2 + s3*c3 - s4*c4 + s5*c5                                                         
        elif n < 6 :
            # cofactors, gets slower than Gauss-Jordan for sizes 6 and more
            d = 0
            for j in xrange(n) :
               d += self[0,j]*self.cofactor(0, j)  # ((-1)**j)*self.minor(0,j).det() 
        else :
            # Gauss-Jordan elimination
            try :
                m, nbperm = self._gauss_jordan()
                d = prod(m.diagonal(), (-1)**nbperm) 
            except ZeroDivisionError :
                # singular
                d = 0.0 
        
        return d
              
    det = determinant
    
    def isSingular(self):
        return (self.det() < eps)
    
    def inverse(self): 
        assert self.is_square(), "inverse is only defined for a square Matrix, see leftinverse and rightinverse"
        n = self.nrow
        try :
            if n == 1 :
                i = self.__class__(1.0/self[0, 0])
            elif n < 4 :
                # got direct formulas for both adjugate and determinant if n<4
                i = self.adjugate()/float(self.det())
            elif n < 6 :
                # by cofactors expansion : i = self.adjugate()/float(self.det())
                # here calculate determinant from the adjugate matrix components to avoid computing cofactors twice
                a = self.adjugate() # [[self.cofactor(j, i) for j in xrange(n)] for i in xrange(n)]
                d = 0.0
                for j in xrange(n) :
                    d += self[0,j]*a[j, 0]  
                i = a/float(d)   
            else :
                # by gauss-jordan elimination
                id = Matrix.identity(n)        
                m = self.hstacked(id).reduced()
                i = self.__class__(m[:, n:])
        except ZeroDivisionError :
            raise ValueError, "Matrix is not invertible" 
        
        return i
             
    inv = inverse
    
    I = property(inverse, None, None, """The inverse Matrix""")

    def leftinverse(self):
        nr, nc = self.nrow, self.ncol
        assert nr >= nc, "a Matrix can have an inverse if it is square and a left inverse only if it has more rows than columns"
        if nr == nc :
            return self.I
        else :
            t = self.T
            m = t * self
            return m.I * t
        
    def rightinverse(self):
        nr, nc = self.nrow, self.ncol
        assert nc >= nr, "a Matrix can have an inverse if it is square and a right inverse only if it has more columns than rows"
        if nr == nc :
            return self.I
        else :
            t = self.T
            m = self * t
            return t * m.I
                
# functions that work on Vectors or 1-d Arrays

def angle(u, v):
    """ angle(u, v) --> float
        Returns the angle of rotation between u and v """
    if not isinstance(u, Vector) : 
        try :
            u = Vector(u)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, angle is only defined for two Vectors of size 3" % (clsname(u))   
    return u.angle(v)

def axis(u, v, normalize=False):
    """ axis(u, v[, normalize=False]) --> Vector
        Returns the axis of rotation from u to v as the vector n = u ^ v
        if the normalize keyword argument is set to True, n is also normalized """
    if not isinstance(u, Vector) :
        try :
            u = Vector(u)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, axis is only defined for two Vectors of size 3" % (clsname(u))   
    return u.axis(v, normalize)

def cross(u, v):
    """ cross(u, v) --> Vector :
        cross product of u and v, u and v should be 3 dimensional vectors  """
    if not isinstance(u, Vector) :
        try :
            u = Vector(u)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, cross product is only defined for two Vectors of size 3" % (clsname(u))  
    return u.cross(v) 

def dot(u, v):
    """ dot(u, v) --> float :
        dot product of u and v, u and v should be Vectors of identical size"""
    if not isinstance(u, Vector) :
        try :
            u = Vector(u)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, cross product is only defined for two Vectors of identical size" % (clsname(u))  
    return u.dot(v)

def outer(u, v):
    """ outer(u, v) --> Matrix :
        outer product of vectors u and v """
    if not isinstance(u, Vector) :
        try :
            u = Vector(u)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, outer product is only defined for two Vectors" % (clsname(u))  
    return u.outer(v)        

def cotan(a, b, c=None) :
    """ cotan(a, b[, c]) :
        If only a and b are provided, contangent of the a, b angle, a and b should be 3 dimensional Vectors representing vectors,
        if c is provided, cotangent of the (b-a), (c-a) angle, a, b, and c being be 3 dimensional Vectors representing points """
    if not isinstance(a, Vector) :
        try :
            a = Vector(a)
        except :
            raise NotImplemented, "%s is not convertible to type Vector, cotangent product is only defined for 2 vectors or 3 points" % (clsname(a))  
    return a.cotan(b, c) 

#
#    Vector Class
#

class Vector(Array):
    """
        A generic size Vector class derived from Array, basically a 1 dimensional Array
    """
    __slots__ = ['_data', '_shape', '_size']    
    
    #A Vector is a one-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 1
    
    def _getshape(self):
        return (len(self),)
    def _setshape(self, newshape):
        self.resize(newshape)    
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Vector, as Vectors are one-dimensional Arrays: v.shape = (v.size,)")    
    # ndim = property(lambda x : 1, None, None, "A Vector is a one-dimensional Array")
    size = property(lambda x : len(x), None, None, "Number of components of the Vector")
    
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
            # will defer to Matrix rmul
            return NotImplemented
        else :
            # will defer to Array.__mul__
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a Vector, __rmul__ is mapped to the dot product of the two vectors a and b,
            If b is a Matrix, __rmul__ is mapped to Matrix b by Vector a multiplication,
            otherwise, returns the result of the element wise multiplication of b and a if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """       
        if isinstance(other, Vector) :
            return self.dot(other)
        elif isinstance(other, Matrix) :
            # will defer to Matrix mul
            return NotImplemented
        else :
            # will defer to Array.__rmul__
            return Array.__rmul__(self, other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of Vector a and b, see __mul__, result must fit a's type """      
        res = self*other
        if isinstance(res, self.__class__) :
            return self.__class__(res)        
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))      
                  
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
        res = self.__xor__(other) 
        if isinstance(res, self.__class__) :
            return self.__class__(res)        
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self)) 
                             
    # additional methods

    def angle(self, other):
        """ angle(u, v) --> float
            Returns the angle of rotation between u and v """         
        try :
            nself, nother = coerce(Vector(self), other)
            assert len(nself) == len(nother) == 3
        except :
            raise NotImplemented, "%s not convertible to %s, angle is only defined for two Vectors of size 3" % (clsname(other), clsname(self))
        l = float(nself.length() * nother.length())
        if l > 0 :
            return acos( nself.dot(nother) / l )
        else :
            return 0.0  
    def axis(self, other, normalize=False):
        """ axis(u, v[, normalize=False]) --> Vector
            Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        try :
            nself, nother = coerce(Vector(self), other)
            assert len(nself) == len(nother) == 3
        except :
            raise NotImplemented, "%s not convertible to %s, axis is only defined for two Vectors of size 3" % (clsname(other), clsname(self))           
        if normalize :
            return nself.cross(nother).normal()
        else :
            return nself.cross(nother)
    def cross(self, other):
        """ cross(u, v) --> Vector
            cross product of u and v, u and v should be 3 dimensional vectors  """
        try :
            nself, nother = coerce(Vector(self), other)
            assert len(nself) == len(nother) == 3
        except :
            raise NotImplemented, "%s not convertible to %s, cross product is only defined for two Vectors of size 3" % (clsname(other), clsname(self))     
        return Vector([nself[1]*nother[2] - nself[2]*nother[1],
                nself[2]*nother[0] - nself[0]*nother[2],
                nself[0]*nother[1] - nself[1]*nother[0]])         
    def dot(self, other):
        """ dot(u, v) --> float
            dot product of u and v, u and v should be Vectors of identical size"""
        try :
            nself, nother = coerce(Vector(self), other)
        except :
            raise NotImplemented, "%s not convertible to %s, cross product is only defined for two Vectors of identical size" % (clsname(other), clsname(self))               
        return reduce(operator.add, map(operator.mul, nself, nother)) 
    def outer(self, other):
        """ outer(u, v) --> Matrix :
            outer product of vectors u and v """
        try :
            nself, nother = coerce(Vector(self), other)
        except :
            raise NotImplemented, "%s not convertible to %s, cross product is only defined for two Vectors" % (clsname(other), clsname(self))       
        return Matrix([nother*x for x in nself]) 
    def transformAsNormal(self, other):
        """ u.transformAsNormal(m) --> Vector
            Equivalent to transforming u by the inverse transpose Matrix of m, used to transform normals """ 
        try :
            nother = Matrix(other)
        except :
            raise NotImplemented, "%s not convertible to Matrix" % (clsname(other))                     
        return nother.transpose().inverse().__rmul__(self)
    
    # min, max etc methods derived from array  
        
    # length methods can be more efficient than for Arrays as there is only one axis   
    def sqlength(self):
        return reduce(operator.add, map(lambda x:x**2, self))         
    def length(self):
        return sqrt(self.sqlength())                
    def normal(self): 
        """ Return a normalized copy of self. Overriden to be consistant with Maya API and MEL unit command,
            does not raise an exception if self if of zero length, instead returns a copy of self """
        try :
            return self/self.length()
        except :
            return self
    unit = normal
    def isParallel(self, other, tol=eps):
        """ Returns true if both arguments considered as Vector are parallel within the specified tolerance """
        try :
            nself, nother = coerce(Vector(self), other)
        except :
            raise NotImplemented, "%s not convertible to %s, isParallel is only defined for two Vectors" % (clsname(other), clsname(self))       
        return (abs(nself.dot(nother) - nself.length()*nother.length()) <= tol)     
    def cotan(self, other, third=None):
        """ cotan(a, b[, c]) --> float :
            If only a and b are provided, contangent of the a, b angle, a and b should be 3 dimensional Vectors representing vectors,
            if c is provided, cotangent of the ab, ac angle, a, b, and c being be 3 dimensional Vectors representing points """ 
        if third is None :
            # it's 2 vectors
            # ((v - u)*(-u))/((v - u)^(-u)).length() 
            try :
                nself, nother = coerce(Vector(self), other)
                assert len(nself) == len(nother) == 3
            except :
                raise NotImplemented, "cotan is defined for 2 vectors"
            return (nself.dot(nother)) / (nself.cross(nother)).length()             
        else :
            # it's 3 points a, b, c, cotangent of the angle in a
            # ((b - a)*(c - a))/((b - a)^(c - a)).length()  
            try :
                nself, nother = coerce(Vector(self), other)
                nself, nthird = coerce(nself, third)
                assert len(nself) == len(nother) == len(nthird) == 3
            except :
                raise NotImplemented, "cotan is defined for 3 points"
            return ((nother-nself).dot(nthird-nself)) / ((nother-nself).cross(nthird-nself)).length() 
    
    # blend and clamp derived from Array
             
def _testArray() :  

         
    # init and append (hstack, vstack)
    A = Array()
    print repr(A)
    print A.data
    print A.shape
    print A.ndim
    print A.size
    A = Array(1)
    print repr(A)
    print A.data
    print A.shape
    print A.ndim
    print A.size       
    A = Array(1,2)
    print repr(A) 
    A = Array([1,2])
    print repr(A) 
    A = Array([[1,2], [3, 4]])
    print repr(A)
    print A.formated()
    print A.data
    print A.shape
    print A.ndim
    print A.size       
    A[0,0] = 10
    print A.formated() 
    #[[10, 2],
    # [3, 4]]    
    A[:,1] *= 2  
    print A.formated()
    #[[10, 4],
    # [3, 8]]
    A = Array(1, shape=(2, 2))
    print A.formated()    
    #[[1, 1],
    # [1, 1]]                            
    A = Array(range(1, 5), shape=(2, 2))
    print A.formated()    
    #[[1, 2],
    # [3, 4]]  
    print A.data
    # [Array([1, 2]), Array([3, 4])]
    print A.tolist()
    # [[1, 2], [3, 4]]     
    print A.get()
    # ((1, 2), (3, 4))
    
        
    # Array([])
    A = Array([])
    print repr(A)
    # Array([])
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
    A = Array(shape=(2, 2))
    print "A = Array(shape=(2, 2))"
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

       
    # copies and references
    B = Array([[1,1,1],[4,4,3],[7,8,5]])
    print B.formated()
    #[[1, 1, 1],
    # [4, 4, 3],
    # [7, 8, 5]] 
    # C = B   
    C = B
    print C.formated()
    #[[1, 1, 1],
    # [4, 4, 3],
    # [7, 8, 5]] 
    print C == B
    # True    
    print C is B
    # True
    print C[0] is B[0]
    # True
    # assign is a shallow copy
    C = Array()
    C.assign(B)   
    print C.formated()
    #[[1, 1, 1],
    # [4, 4, 3],
    # [7, 8, 5]] 
    print C == B
    # True    
    print C is B
    # False
    print C[0] is B[0]
    # True           
    # init is a shallow copy
    C = Array(B)    
    print C.formated()
    #[[1, 1, 1],
    # [4, 4, 3],
    # [7, 8, 5]]         
    print C == B
    # True    
    print C is B
    # False
    print C[0] is B[0]
    # True
    
    C = Array([B]) 
    print C.formated()
    #[[[1, 1, 1],
    #  [4, 4, 3],
    #  [7, 8, 5]]]    
    print C[0] is B
    # True
    print C[0,0] is B[0]   
    # True  
        
    #shallow copy
    C = B.copy()
    print C.formated()
    #[[[1, 1, 1],
    #  [4, 4, 3],
    #  [7, 8, 5]]]       
    print C == B
    # True     
    print C is B
    # False
    print C[0] is B[0]
    # True
    
    #deep copy   
    C = B.deepcopy()
    print C.formated()
    #[[[1, 1, 1],
    #  [4, 4, 3],
    #  [7, 8, 5]]]       
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
    a = A[0, 0:2]
    print "a = A[0, 0:2]"
    print a.formated()
    #[[1, 1, 1],
    # [4, 5, 3]]      
    a[0, 1] = 2
    print a.formated()
    #[[1, 2, 1],
    # [4, 5, 3]]    
    print A[0].formated()
    #[[1, 2, 1],
    # [4, 5, 3],
    # [7, 9, 5]]      
    print "a = A[0, :, 1]:"
    a = A[0, :, 1]
    print a
    # [2 5 9]
    a[1] = 6
    print "a[1] = 6:"
    print a
    # [2 6 9]
    # not changing value because array had to be reconstructed
    print "A[0, :]:"
    print A[0, :].formated()
    #[[1, 2, 1],
    # [4, 5, 3],
    # [7, 9, 5]]
    # do it this way 
    A[0, :, 1] = [2, 6, 9]
    print "A[0, :, 1] = [2, 6, 9]"
    print A[0, :].formated()
    #[[1, 2, 1],
    # [4, 6, 3],
    # [7, 9, 5]]    
    print "A[0, :, 1:2]:"
    print A[0, :, 1:2].formated()
    #[[2],
    # [6],
    # [9]]
    print "A[0, 1:2, 1:2]:"
    print A[0, 1:2, 1:2].formated()
    #[[6]]
    print "A[0, :, 1:3]:"
    print A[0, :, 1:3].formated()
    #[[2, 1],
    # [6, 3],
    # [9, 5]]
    print "A[:, :, 1:3]:"
    print A[:, :, 1:3].formated()
    #[[[2, 1],
    #  [6, 3],
    #  [9, 5]],
    #
    # [[10, 10],
    #  [40, 30],
    #  [80, 50]]]
    print "A[:, :, 1:2]:"
    print A[:, :, 1:2].formated()
    #[[[2],
    #  [6],
    #  [9]],
    #
    # [[10],
    #  [40],
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
    
    print "B=Array(range(1, 17), shape=(4, 4))"
    B = B=Array(range(1, 17), shape=(4, 4))
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]     
    print "B.reshaped((2, 2, 2, 2)):"
    print B.reshaped((2, 2, 2, 2)).formated()
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
    print "B.resized((4, 5)):"
    print B.resized((4, 5)).formated()
    #[[ 1  2  3  4  5]
    # [ 6  7  8  9 10]
    # [11 12 13 14 15]
    # [16  0  0  0  0]]
    print "B.resized((4, 5), 1):"
    print B.resized((4, 5), 1).formated()
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
    
    # trim
    
    print "B=Array(range(1, 17), shape=(4, 4))"
    B = B=Array(range(1, 17), shape=(4, 4))
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]      
    A = B[0]
    print "A = B[0]"
    print A.formated()
    # [1, 2, 3, 4]
    print "C = B.trimmed((5, 4))"
    C = B.trimmed((5, 4))
    print C.formated()
    #[[1, 2, 3, 4],
    # [5, 6, 7, 8],
    # [9, 10, 11, 12],
    # [13, 14, 15, 16],
    # [0, 0, 0, 0]]
    print A == C[0]
    # True
    print A is C[0]
    # False
    print "C = B.trimmed((5, 5))"
    C = B.trimmed((5, 5))
    print C.formated()
    #[[1, 2, 3, 4, 0],
    # [5, 6, 7, 8, 0],
    # [9, 10, 11, 12, 0],
    # [13, 14, 15, 16, 0],
    # [0, 0, 0, 0, 0]]
    C = B.trimmed((3, 3))
    print C.formated()
    #[[1, 2, 3],
    # [5, 6, 7],
    # [9, 10, 11]]
       
    print "B=Array(range(1, 17), shape=(4, 4))"
    B = B=Array(range(1, 17), shape=(4, 4))
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]    
    A = B[0]
    print "A = B[0]"
    print A.formated()
    # [1, 2, 3, 4]
    print A == B[0]
    # True
    print A is B[0]
    # True       
    print "B.trim((5, 4))"
    C = B
    B.trim((5, 4))
    print B.formated()
    #[[1, 2, 3, 4],
    # [5, 6, 7, 8],
    # [9, 10, 11, 12],
    # [13, 14, 15, 16],
    # [0, 0, 0, 0]]
    print C.formated()
    #[[1, 2, 3, 4],
    # [5, 6, 7, 8],
    # [9, 10, 11, 12],
    # [13, 14, 15, 16],
    # [0, 0, 0, 0]]    
    print A == B[0]
    # True
    print A is B[0]
    # True  
    print "B.trim((5, 5))"
    B.trim((5, 5))
    print B.formated()
    #[[1, 2, 3, 4, 0],
    # [5, 6, 7, 8, 0],
    # [9, 10, 11, 12, 0],
    # [13, 14, 15, 16, 0],
    # [0, 0, 0, 0, 0]] 
    print A.formated()    
    # [1, 2, 3, 4, 0]    
    print "B.trim((3, 2))"
    B.trim((3, 2))
    print B.formated()
    #[[1, 2],
    # [5, 6],
    # [9, 10]]   
    print A.formated() 
    # [1, 2]
    
    # TODO : test the copy / in place similarly for reshape, append, resize, etc 

    print "B=Array(range(1, 17), shape=(4, 4))"
    B = B=Array(range(1, 17), shape=(4, 4))
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]      
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
    
    # operators
    
    A = Array([[[1, 2, 1], [4, 2, 3], [7, 2, 5]], [[10, 2, 10], [40, 2, 30], [70, 2, 50]]])
    print "A = Array([[[1, 2, 1], [4, 2, 3], [7, 2, 5]], [[10, 2, 10], [40, 2, 30], [70, 2, 50]]])"
    print A.formated()
    #[[[1, 2, 1],
    #  [4, 2, 3],
    #  [7, 2, 5]],
    #
    # [[10, 2, 10],
    #  [40, 2, 30],
    #  [70, 2, 50]]]                
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
    #[[[0, 1, 2],
    #  [3, 4, 5],
    #  [6, 7, 8]],
    #
    # [[9, 10, 11],
    #  [12, 13, 14],
    #  [15, 16, 17]]]        
    print "B=A[0]"
    B=A[0]
    print B.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]] 
    print "B.transpose()"
    print B.transpose().formated()
    #[[0, 3, 6],
    # [1, 4, 7],
    # [2, 5, 8]]     
    print "A.transpose(0,2,1)"    
    print A.transpose(0,2,1).formated() 
    #[[[0, 3, 6],
    #  [1, 4, 7],
    #  [2, 5, 8]],
    #
    # [[9, 12, 15],
    #  [10, 13, 16],
    #  [11, 14, 17]]]  
    print "A.transpose(2,1,0)"
    print A.transpose(2,1,0).formated()
    #[[[0, 9],
    #  [3, 12],
    #  [6, 15]],
    #
    # [[1, 10],
    #  [4, 13],
    #  [7, 16]],
    #
    # [[2, 11],
    #  [5, 14],
    #  [8, 17]]]



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
    
    M = Matrix()
    print repr(M)
    M = Matrix([])
    print repr(M)
    M = Matrix([0, 1, 2])
    print M.formated()
    # [[0, 1, 2]]
    M = Matrix([[0, 1, 2]])
    print M.formated()
    # [[0, 1, 2]]
    M = Matrix([[0], [1], [2]])
    print M.formated()   
    # [[0],
    #  [1],
    #  [2]]       
    M = Matrix([[1, 2, 3], [4, 5, 6]])
    print M.formated()
    # [[1, 2, 3],
    #  [4, 5, 6]]
    # should fail
    print "M = Matrix([[[1, 2, 3], [4, 5, 6]], [[10, 20, 30], [40, 50, 60]]])"
    try :
        M = Matrix([[[1, 2, 3], [4, 5, 6]], [[10, 20, 30], [40, 50, 60]]])
        print M.formated()
    except :
        print "Will raise ValueError: cannot initialize a Matrix of shape (2, 6) from [[[1, 2, 3], [4, 5, 6]], [[10, 20, 30], [40, 50, 60]]], some information would be lost, use an explicit resize or trim"
    # should fail
    print "M.resize((2, 2, 3))"
    try :
        M.resize((2, 2, 3))
        print M.formated()
    except :
        print "Will raise TypeError: shape (2, 2, 3) is incompatible with class Matrix"

    print "M = Matrix([[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])"
    try :
        M = Matrix([[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])
        print M.formated()
    except :
        print "Will raise TypeError: shape (2, 2, 3) is incompatible with class Matrix"
          
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

    # copies and references
    B = Matrix(range(9), shape=(3, 3)) 
    print B.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]] 
    # C = B   
    C = B
    print C.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]] 
    print C == B
    # True    
    print C is B
    # True
    print C[0] is B[0]
    # True
    
    # assign
    C = Matrix()
    C.assign(B)   
    print C.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]] 
    print C == B
    # True    
    print C is B
    # False
    print C[0] is B[0]
    # True   
            
    # init is a shallow copy
    C = Matrix(B)    
    print C.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]    
    print C == B
    # True    
    print C is B
    # False
    print C[0] is B[0]
    # True
    
    C = Array([B]) 
    print C.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]] 
    print C[0] == B
    # True
    # type is different (Matrix vs Array)    
    print C[0] is B
    # False
    print C[0,0] is B[0]   
    # True  
        
    #shallow copy
    C = B.copy()
    print C.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]    
    print C == B
    # True     
    print C is B
    # False
    print C[0] is B[0]
    # True
    
    #deep copy   
    C = B.deepcopy()
    print C.formated()
    #[[1, 1, 1],
    #  [4, 4, 3],
    #  [7, 8, 5]]      
    print C == B
    # True     
    print C is B
    # False
    print C[0] is B[0] 
    # False
        
    # row and column
    M = Matrix(range(9), shape=(3, 3)) 
    print M.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]    
    a = M[0]
    print repr(a)
    # Array([0, 1, 2])
    print a is M[0]
    # True
    a[1] = 2
    print a.formated()
    # [0, 2, 2]
    print M.formated()
    #[[0, 2, 2],
    # [3, 4, 5],
    # [6, 7, 8]]
    a = M[:,1]
    print repr(a)
    # [2, 4, 7]
    print a is M[:,1]
    # False
    a[1] = 2
    print a.formated()
    # [2, 2, 7]
    print M.formated()
    #[[0, 2, 2],
    # [3, 4, 5],
    # [6, 7, 8]]       
    a = M[0:2]
    print a.formated()
    #[[0, 2, 2],
    # [3, 4, 5]]    
    print a is M[0:2]  
    # False
    print a[1] is M[1]  
    # True    
    a[1, 1] = 2
    print a.formated()
    #[[0, 2, 2],
    # [3, 2, 5]]        
    print M.formated()
    #[[0, 2, 2],
    # [3, 2, 5],
    # [6, 7, 8]]    
       
    M = Matrix(range(9), shape=(3, 3)) 
    print M.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]   
    print M.nrow
    # 3
    M.nrow = 4
    print M.formated() 
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8],
    # [0, 0, 0]]    
    print M.ncol
    # 3
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
    M.row[0][1] = 10
    print M.formated()
    #[[0, 10, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]    
    M.row[0:2][1, 1] = 10
    print M.formated()
    #[[0, 10, 2, 0],
    # [3, 10, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]
    
    # doesn't work as columns need rebuilding
    a = M.col[0]
    print repr(a)
    # Array([0, 3, 6, 0])
    a[1] = 10
    print a.formated()
    # [0, 10, 6, 0]
    print M.formated()
    #[[0, 10, 2, 0],
    # [3, 10, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]  
    M.col[0][1] = 10
    print M.formated()
    #[[0, 10, 2, 0],
    # [3, 10, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]      
    M.col[0] = [0, 10, 6, 0]
    print M.formated()
    #[[0, 10, 2, 0],
    # [10, 10, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]  
    M[2:, 2:] = 10
    print M.formated()
    #[[0, 10, 2, 0],
    # [10, 10, 5, 0],
    # [6, 7, 10, 10],
    # [0, 0, 10, 10]]  
          
    M = Matrix(range(9), shape=(3, 3)) 
    M.nrow, M.ncol = 4, 4
    print M.formated()
    #[[0, 1, 2, 0],
    # [3, 4, 5, 0],
    # [6, 7, 8, 0],
    # [0, 0, 0, 0]]          
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
    print M[:3, :3].formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]    

    M = Matrix(range(1,10), shape=(3, 3))
    M.trim((4, 4))
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
    print M.formated()
    #[[0, 1, 2],
    # [3, 4, 5],
    # [6, 7, 8]]          
    M.trim((4, 4))
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
    
    M = Matrix(range(1,10), shape=(3, 3))
    print "M:"
    print M.formated()
    #[[1, 2, 3],
    # [4, 5, 6],
    # [7, 8, 9],    
    V=Vector(1, 10, 100)   
    print "V:"
    print repr(V)
    # Vector([1, 10, 100])
    print "V*M"
    print repr(V*M)
    # Vector([741, 852, 963])   
    print "M*V"
    print repr(M*V)
    # Vector([321, 654, 987])    
      
    M.trim(shape=(4, 4))
    M[3] = [0.25, 0.5, 0.75, 1]
    print "M:"
    print M.formated()
    #[[1, 2, 3, 0],
    # [4, 5, 6, 0],
    # [7, 8, 9, 0],
    # [0.25, 0.5, 0.75, 1]] 
    V=Vector(1, 10, 100)   
    print "V:"
    print repr(V)
    # Vector([1, 10, 100])    
    print "V*M"
    print repr(V*M)
    # Vector([741.0, 852.0, 963.0])    
    print "M*V"
    print repr(M*V)
    # Vector([321, 654, 987])
    
    P=Vector(1, 10, 100, 1)   
    print "P:"
    print repr(P)
    # Vector([1, 10, 100, 1])
    print "P*M"
    print repr(P*M)
    # Vector([741.25, 852.5, 963.75, 1])
    print "M*P"
    print repr(M*P)
    # Vector([321, 654, 987, 81.25])
    
    U=Vector(1, 2, 3, 4, 5)   
    print "U:"
    print repr(U)
    # Vector([1, 2, 3, 4, 5])
    # should fail
    print "U*M"
    try :
        print repr(U*M)
    except :
        print "Will raise ValueError: vector of size 5 and matrix of shape (4, 4) are not conformable for a Vector * Matrix multiplication"
                              
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
    #[[4, -2],
    # [-3, 1]]         
    print "det(M)"  
    print det(M)
    # -2   
    print "M.inverse()"
    print M.inverse().formated()
    #[[-2.0, 1.0],
    # [1.5, -0.5]]
    print M.inverse().transpose().formated()
    #[[-2.0, 1.5],
    # [1.0, -0.5]] 
            
    M = Matrix([[0.5, 1, 2],[1, 1, 1],[0.5, 0.5, 2]])
    print "M = Matrix([[0.5, 1, 2],[1, 1, 1],[0.5, 0.5, 2]])"
    print M.formated()
    #[[0.5, 1, 2],
    # [1, 1, 1],
    # [0.5, 0.5, 2]] 
    print "M.adjugate()"
    print M.adjugate().formated()  
    #[[1.5, -1.0, -1],
    # [-1.5, 0.0, 1.5],
    # [0.0, 0.25, -0.5]]         
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
    #[[9.0, -36.0, 30.0],
    # [-36.0, 192.0, -180.0],
    # [30.0, -180.0, 180.0]]
         
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
 
    U = Vector()
    print "U = Vector()"
    print repr(U)
    # Vector([]) 
    U = Vector(1)
    print "U = Vector(1)"
    print repr(U)
    # Vector([1])
    U = Vector(1, 2)
    print "U = Vector(1, 2)"
    print repr(U)
    # Vector([1, 2])          
    U = Vector(1, 2, 3)
    print "U = Vector(1, 2, 3)"
    print repr(U)
    # Vector([1, 2, 3])
    # should fail
    print "V = Vector([[1, 2], [3, 4]])"    
    try :
        V = Vector([[1, 2], [3, 4]])
    except :
        print "Will raise ValueError: cannot initialize a Vector of shape (4,) from [[1, 2], [3, 4]], some information would be lost, use an explicit resize or trim" 
    print "V = Vector([[1, 2, 3]])"
    try :
        V = Vector([[1, 2, 3]])
    except :
        print "Will raise ValueError: cannot initialize a Vector of shape (3,) from [[1, 2, 3]], some information would be lost, use an explicit resize or trim" 
      
    # herited methods
    
    U = Vector(1, 2, 3)
    print "U:"
    print repr(U)
    # Vector([1, 2, 3]) 
    print repr(U+1)
    # Vector([2, 3, 4])
    print repr(U*2)
    # Vector([2, 4, 6])
    print repr(U*[10, 100, 1000])   
    # Vector([10, 200, 3000]) 
      
    # overloaded methods  

    U = Vector(1, 2, 3)
    print "U:"
    print repr(U)
    # Vector([1, 2, 3])       
    M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])
    print "M = Matrix([[1.5, 1.5, -2.12, 0.0], [-0.29, 1.71, 1.0, 0.0], [0.85, -0.15, 0.5, 0.0], [1.0, 2.0, 3.0, 1.0]])"
    print M.formated()
    #[[1.5, 1.5, -2.12, 0.0],
    # [-0.29, 1.71, 1.0, 0.0],
    # [0.85, -0.15, 0.5, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]  
    print "V = U*M[:3, :3]"
    V = U*M[:3, :3]
    print repr(V)
    # Vector([3.47, 4.47, 1.38])
    print "V = U*M"
    V = U*M
    print repr(V)
    # Vector([3.47, 4.47, 1.38])   
    print U*V
    # 16.55
    N = U^V
    print repr(N)
    # Vector([-10.65, 9.03, -2.47])
    print repr(N.normal())
    # Vector([-0.751072956189, 0.63682523891, -0.17419250721])
    print U.dist(V)
    # 3.8504804895
    
    print repr(M[:3, :3]*U)
    # Vector([-1.86, 6.13, 2.05])
    print repr(U^M[:3, :3])
    # Vector([2.59076337407, 0.574934882789, 1.76818272891])
    print repr((U^M[:3, :3]).normal())
    # Vector([0.812431999034, 0.180292612136, 0.554480676809])  
    print repr(U.normal()^M[:3, :3])
    # Vector([0.692410636856, 0.153657810793, 0.472566712057])      
    print repr(U*M[:3, :3].transpose().inverse())
    # Vector([2.59076337407, 0.574934882789, 1.76818272891])
    print repr((U*M[:3, :3].transpose().inverse()).normal())
    # Vector([0.812431999034, 0.180292612136, 0.554480676809])
    print repr(U.normal()*M[:3, :3].transpose().inverse())
    # Vector([0.692410636856, 0.153657810793, 0.472566712057])
                
    # Vector of size 4 for Point
    P = Vector(1, 2, 3, 1)
    print "P = Vector(1, 2, 3, 1)"
    print repr(P)
    # Vector([1, 2, 3, 1])
    print "Q = P*M"
    Q = P*M
    print repr(Q)
    # Vector([4.47, 6.47, 4.38, 1.0])
    print P.dist(Q)
    # 5.82462015929        
    print M.formated()
    #[[1.5, 1.5, -2.12, 0.0],
    # [-0.29, 1.71, 1.0, 0.0],
    # [0.85, -0.15, 0.5, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]       
    P*=M
    print repr(P)
    # Vector([4.47, 6.47, 4.38, 1.0])          
    print  "M*=P"
    try :
        M*=P
        print M.formated()
    except :
        print "Will raise TypeError: result of in place multiplication of Matrix by Vector is not a Matrix"
         
    print "end tests Vector"
    
def _test():
    import doctest
    doctest.testmod()
    

if __name__ == '__main__' :
    # _test()
    _testArray()   
    _testMatrix()
    _testVector()
     
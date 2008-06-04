
"""
A generic n-dimensionnal Array class serving as base for arbitrary length Vector and Matrix classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the reat multi index slicing, get / setitem and item indexing for iterators,
# and tried to make the method names match so that it will be easier to include Numpy instead if desired.

# TODO : try a Numpy import and fallback to the included class if not successful ?


import operator, itertools, copy, inspect, sys

import arguments as util
from utilitytypes import readonly, metaReadOnlyAttr
from math import pi, exp
import math, mathutils

_thisModule = sys.modules[__name__]

# internal utilities

def _toCompOrArray(value) :
    if hasattr(value, '__iter__') :
        if type(value) is not Array :
            value = Array(value)
    elif util.isNumeric(value) :
        # a single numeric value
        pass 
    else :
        raise TypeError, "invalid value type %s cannot be converted to Array" % (util.clsname(value))
    
    return value

def _toCompOrArrayInstance(value) :
    if hasattr(value, '__iter__') :
        if not isinstance(value, Array) :
            value = Array(value)
    elif util.isNumeric(value) :
        # a single numeric value
        pass 
    else :
        raise TypeError, "invalid value type %s cannot be converted to Array" % (util.clsname(value))
    
    return value

def _shapeInfo(value) :
    if isinstance(value, Array) :
        shape = value.shape
        dim = value.ndim
        size = value.size        
    elif util.isNumeric(value) :
        shape = ()
        dim = 0
        size = 1
    else:
        raise TypeError, "can only query shape information on Array or Array component (numeric), not %s" % (util.clsname(value))
    
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

def dot(a, b):
    """ dot(a, b): dot product of a and b, a and b should be iterables of numeric values """
    return reduce(operator.add, map(operator.mul, list(a)[:lm], list(b)[:lm]), 0.0)

def length(a):
    """ length(a): square root of the absolute value of dot product of a by q, a be an iterable of numeric values """
    return sqrt(abs(dot(a, a)))

def cross(a, b):
    """ cross(a, b): cross product of a and b, a and b should be iterables of 3 numeric values  """
    la = list(a)[:3]
    lb = list(b)[:3]
    return [a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]

def cotan(a, b, c) :
    """ cotangent of the (b-a), (c-a) angle, a, b, and c should support substraction, dot, cross and length operations """
    return dot(c - b,a - b)/length(cross(c - b, a - b))  
   

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
                    raise ValueError, "%s has %s dimensions, cannot iterate on axis %s" % (util.clsname(data), data.ndim, x)
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
            raise TypeError, "%s can only be built on Array" % util.clsname(self)
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
    def _toArrayCoords(self, item):
        owncoords = []
        for s in self.subsizes :
            c = item//s
            item -= c*s
            owncoords.append(c)
        coords = [slice(None)]*self.base.ndim
        for i,c in enumerate(owncoords) :
            coords[self.axis[i]] = c
        # remove trailing ":" slices, leaving a minimum of one coord   
        while len(coords) > 1 and coords[-1] == slice(None) :
            del coords[-1]
        return tuple(coords)
        
    def toArrayCoords(self, item):
        """ Converts an iterator item index (nth item) for that Array iterator to a tuple of axis coordinates for that Array, 
            returns a single coordinates tuple or a list of coordinate tuples if item index was a slice """
        if isinstance(item, slice) :
            return [self._toArrayCoords(f) for f in range(self.size)[item]]
        else :
            item = int(item)
            if item < 0 :
                item = self.size - item
            if item>=0 and item<self.size :
                return self._toArrayCoords(item)
            else :
                raise IndexError, "item numer %s for iterator of %s items is out of bounds" % (item, self.size)

    def __getitem__(self, index) :
        """ Returns a single sub-Array or component corresponding to the iterator item item, or an Array of values if index is a slice """      
        coords = self.toArrayCoords(index)
        if type(coords) is list :
            return Array(self.base.__getitem__(c) for c in coords)
        else :
            return self.base.__getitem__(coords)

    def __setitem__(self, index, value) :
        """ Returns a single sub-Array or component corresponding to the iterator item item, or an Array of values if index is a slice """
        coords = self.toArrayCoords(index)

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
    __readonly__ = ('stype',)
    
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
        if isinstance(data, self.stype) :
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
    def default(cls, shape=None):
        """ cls.default([shape])
            Returns the default instance (of optional shape form shape) for that Array class """
            
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
    def filled(cls, value=None, shape=None):
        """ cls.filled([value[, shape]]) :
            Returns a cls instance of the given shape filled with value for the given shape,
            if no value is given, a default instance of that shape is returned.
            Value will be expended with the class default values to the nearest matching sub array
            of the class, then repeated.
            Value can't be truncated and will raise an error if of a size superior to the size of
            the nearest matching sub array of the class, to avoid improper casts """
        new = cls.default(shape)
        shape = new.shape
        if shape and value is not None :
            dim = new.ndim            
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim <= dim :
                subshape = shape[dim-vdim:]
                if subshape != vshape :
                    subsize = reduce(operator.mul, subshape, 1)
                    if subsize >= vsize :
                        value.resize(subshape)
                    else :
                        raise ValueError, "value of shape %s cannot be fit in a %s of shape %s, some data would be lost" % (vshape, cls.__name__, shape)
                if vdim < dim :
                    iter = new.subiter(vdim)
                    for i in xrange(len(iter)) :
                        iter[i] = value    
                else :
                    new = value      
            else :
                raise ValueError, "fill value has more dimensions that the specified desired shape"
        return new 
        
    def fill(self, value=None, shape=None):     
        """ a.fill([value[, shape]])  :
            Fills the array in place with the given value, if no value is given a is set to the default class instance of same shape """
        if shape is None :
            shape = self.shape
        new = self.__class__.filled(value, shape)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, util.clsname(self))            
                                                            
    def __new__(cls, *args, **kwargs ):
        """ Initialize an Array from one or several nested lists or numeric values """

        shape = kwargs.get('shape', None)
        ndim = None
        if shape is not None :
            if type(shape) is not tuple :
                if hasattr(shape, '__iter__') :
                    shape = tuple(shape)
                else :
                    shape = (shape,)
            ndim = len(shape)
        
        # some Array sub classes have fixed shapes
        try :
            cls_shape = tuple(cls.shape)
            if shape is None :
                shape = cls_shape
                ndim = len(shape)
            elif shape != cls_shape :
                raise ValueError, "class %s has a fixed shape %s and can't accept a different shape at creation" % (cls.__name__, tuple(cls_shape))
        except :
            pass

        # some Array sub classes have a fixed number of dimensions
        try : 
            cls_ndim = int(cls.ndim)
            if shape is None :
                ndim = cls_ndim
            elif ndim != cls_ndim :
                raise ValueError, "class %s has a fixed number of dimensions %s and can't accept shape %s of different dimensions at creation" % (cls.__name__, cls_ndim, tuple(shape))
        except :
            pass
                   
        data = None       
        if args :
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            if isinstance (args, cls) :
                # copy constructor
                data = copy.copy(args.data)
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
            elif util.isNumeric(args) :
                if shape is not None :
                    # can initialize an array from a single numeric value if a shape is specified
                    data = cls.filled(args, shape).data
                else :
                    raise TypeError, "an %s cannot be initialized from a single value without specifying a shape, need at least 2 components or an iterable" % cls.__name__
            else :
                raise TypeError, "an %s element can only be another Array or an iterable" % cls.__name__
        else :
            data = cls.default(shape).data
            
        if data is not None :
            new = super(Array, cls).__new__(cls)
            new.data = data
            # can re-shape on creation if a shape keyword is specified or the class has a fixed shape
            if ndim is not None :
                if shape is None :
                    # we only have a dimension constraint, no specific shape
                    if ndim != new.ndim :
                        # only case we guess shape is when there is no ambiguity (ndim == 1)
                        if ndim == 1 :
                            shape = (ndim,)
                        else :
                            raise ValueError, "cannot initialize a %s of dimension %s from %s without indication of the shape" % (cls.__name__, ndim, args)
                # resize if we have a valid shape
                if shape is not None and shape != new.shape :
                    # accept expanding but not shrinking to catch casting errors
                    shape = cls._expandshape(shape, new.size)
                    size = reduce(operator.mul, shape, 1) 
                    if (size >= new.size) :
                        try :
                            new.fill(data, shape)
                        except :
                            new.resize(shape)
#                        if ndim > new.ndim :
#                            new.fill(data, shape)
#                        elif ndim == new.ndim :
#                            new.resize(shape)
#                        else :
#                            raise TypeError, "cannot cast a %s of shape %s to a %s of shape %s, some data would be lost" % (util.clsname(args), args.shape, cls.__name__, shape)
                    else :
                        if isinstance (args, Array) :
                            raise TypeError, "cannot cast a %s of shape %s to a %s of shape %s, some data would be lost" % (util.clsname(args), args.shape, cls.__name__, shape)
                        else :
                            raise ValueError, "cannot initialize a %s of shape %s from %s, some data would be lost" % (cls.__name__, shape, args)

            return new
        else :
            raise ValueError, "could not initialize a %s from the provided arguments %s" % (cls.__name__, args)
                    
    def append(self, value):
        value = _toCompOrArray(value)
        valueshape, valuedim, valuesize = _shapeInfo(value)        
        if list(valueshape) == self.shape[1:] :
            self._data.append(self, value)
            self._cacheshape()
        else :
            raise TypeError, "argument does not have the correct shape to append to Array"       
 
    @classmethod
    def _expandshape(cls, shape, size):      
        if not hasattr(shape, '__iter__') :
            newshape = [shape]
        else :
            newshape = list(shape)         
           
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
     
        return tuple(newshape)
 
    def toshape(self, shape):
        """ a.toshape(shape)
            Returns the Array as reshaped according to the shape argument """
        
        size = self.size
        newshape = self.__class__._expandshape(shape, size)
        newsize = reduce(operator.mul, newshape, 1)
        if newsize != size :
            raise ValueError, "total size of new array must be unchanged"
        
        return self.tosize(tuple(newshape))
    
    def reshape(self, shape):
        """ a.reshape(shape)
            Performs in-place reshape of array a """
        new = self.toshape(shape)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, util.clsname(self))
              
    def tosize(self, shape, value=None):
        """ a.tosize([shape [, value]])
            Returns the Array as resized according to the shape argument.          
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        newshape = self.__class__._expandshape(shape, self.size)
                   
        new = None
        for cls in inspect.getmro(self.__class__) :
            if issubclass(cls, Array) :
                try :
                    new = cls.filled(value, newshape)
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
                raise TypeError, "%s cannot be initialized to shape %s with value %s, and has no base class that can" % (util.clsname(self), shape, value)
            else :
                raise TypeError, "%s cannot be initialized to shape %s, and has no base class that can" % (util.clsname(self), shape)

    def resize(self, shape, value=None):
        """ a.resize(shape)
            Performs in-place resize of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase. """
        new = self.tosize(shape, value)
        if type(new) is type(self) :
            self.data = new.data
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, util.clsname(self))
        
    # hstack and vstack 

#    concat(     a, b)
#    __concat__(     a, b)
#        Return a + b for a and b sequences.     
#    repeat(     a, b)
#    __repeat__(     a, b)
#        Return a * b where a is a sequence and b is an integer. 
    
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
            return len(self.data)
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

        value = _toCompOrArrayInstance(reduce(lambda x, y: Array._extract(x, y), index, self))
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

    # TODO : not implemented yet
    def __delitem__(self, rc) :
        """ Delete a sub-Array, only possible for a full axis"""
        pass
        
    def __iter__(self, *args) :
        """ Default Array iterator on first dimension """
        # return iter(self.data)
        return self.subiter() 
     
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

        raise ValueError, "%s.index(x): x not in %s" % (util.clsname(self), util.clsname(self)) 

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

    def __coerce__(self, other):
        """ coerce(x, y) -> (x1, y1)
        
            Return a tuple consisting of the two numeric arguments converted to
            a common type, using the same rules as used by arithmetic operations.
            If coercion is not possible, raise TypeError. """ 
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
            # raise TypeError, "%s and %s cannot be converted to an common Array instance of same shape" % (util.clsname(self), util.clsname(other))
        
    def __abs__(self):
        """ a.__abs__() <==> abs(a)
            Element-wise absolute value of a """         
        return self.__class__(abs(x) for x in self) 
    def __pos__(self):
        """ a.__pos__() <==> pos(a)
            Element-wise positive of a """         
        return self.__class__(x.__pos__ for x in self)         
    def __invert__(self):
        """ a.__invert__() <==> invert(a)
            Element-wise invert of a """         
        return self.__class__(invert(x) for x in self) 
    # would define __round__ if the round() function was using it
    def round(self, ndigits=0):
        """ a.round([ndigits]) <==> around(a[, ndigits])
            Element-wise round to given precision in decimal digits (default 0 digits).
            This always returns an Array of floating point numbers.  Precision may be negative. """  
        return self.__class__(around(x, ndigits) for x in self)                     
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

    # more could be wrapped the same way, __divmod__, logical operations etc

    # additional methods
    # a.any(axis=None)
    # a.all(axis=None)
        # min, max, sum, prod
        # __nonzero__
        
#    def sum(self):
#        """ Returns the sum of the components of self """
#        return reduce(operator.add, self, 0)     
  
#    def isEquivalent(self, other, tol):
#        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
#        try :
#            return (other-self).sqLength() <= tol*tol
#        except :
#            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol)  
   


    # arrays of complex values
    def conjugate(self):
        """ Returns the element-wise complex.conjugate() of the Array """
        return self.__class__(x.conjugate() for x in self)
    def real(self):
        """ Returns the real part of the Array """
        return self.__class__(real(x) for x in self)
    def imag(self):
        """ Returns the imaginary part of the Array """
        return self.__class__(imag(x) for x in self) 
        
    # array specific inspired from numpy
    # diagonal, trace ?
        
    def transpose(self, *args):
        """ a.transpose(*axes)
        
            Returns a with axes transposed. If no axes are given,
            or None is passed, switches the order of the axes. For a 2-d
            array, this is the usual matrix transpose. If axes are given,
            they describe how the axes are permuted.  """
        ndim = self.ndim             
        if not args :
            args = range(ndim-1, -1, -1)
        elif len(args) == 1 and hasattr(args[0], '__iter__') :
            args = list(args[0])
        else :
            args = list(args)
        if len(args) != ndim :
            raise ValueError, "Transpose axis %s do not match array shape %s" % (tuple(args), self.shape)      
        shape = []
        for x in args :
            if x<0 or x>= ndim :
                raise ValueError, "Array has %s dimensions, cannot transpose on axis %s" % (ndim, x)
            elif args.count(x) > 1 :
                raise ValueError, "axis %s is present more than once in transpose axis list %s" % (x, args)
            else :            
                shape.append(self.shape[x])
        shape = tuple(shape)
        return self.__class__._convert(Array([s for s in self.axisiter(*args)], shape=shape))
    
    T = property(transpose, None, None, """The transposed array""") 

class Matrix(Array):
    """
    A generic size Matrix class, basically a 2 dimensional Array
    """
    __readonly__ = ('ndim',)
    
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
#    def _getdata(self):
#        return self._data
#    def _setdata(self, data):
#        if isinstance(data, list) :
#            self._data = data
#        else :
#            self._data = list(data)
#    def _deldata(self):
#        del self._data[:]  
#    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
 
    # row and column size properties
    def _getnrow(self):
        return self.shape[0]
    def _setnrow(self, m):
        self.resize((m, self.shape[1]))
    nrow = property(_getnrow, _setnrow, None, "Number of rows in this Matrix")          
    def _getncol(self):
        return self.shape[1]
    def _setncol(self, n):
        self.resize((self.shape[0], n))
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
        """
        Element by element multiplication
        """
        temp = other.transpose()
        return Matrix( [ [ dot(row,col) for col in temp ] for row in self ] )
    def __rmul__(self, other):
        return (self*other)
    def __imul__(self, other):
        return (self*other)        

    
    # specific methods
    

 
#|  diagonal(...)
# |      a.diagonal(offset=0, axis1=0, axis2=1) -> diagonals
# |      
# |      If a is 2-d, return the diagonal of self with the given offset, i.e., the
# |      collection of elements of the form a[i,i+offset]. If a is n-d with n > 2,
# |      then the axes specified by axis1 and axis2 are used to determine the 2-d
# |      subarray whose diagonal is returned. The shape of the resulting array can
# |      be determined by removing axis1 and axis2 and appending an index to the
# |      right equal to the size of the resulting diagonals.
# |      
# |      :Parameters:
# |          offset : integer
# |              Offset of the diagonal from the main diagonal. Can be both positive
# |              and negative. Defaults to main diagonal.
# |          axis1 : integer
# |              Axis to be used as the first axis of the 2-d subarrays from which
# |              the diagonals should be taken. Defaults to first index.
# |          axis2 : integer
# |              Axis to be used as the second axis of the 2-d subarrays from which
# |              the diagonals should be taken. Defaults to second index.
# |      
# |      :Returns:
# |          array_of_diagonals : same type as original array
# |              If a is 2-d, then a 1-d array containing the diagonal is returned.
# |              If a is n-d, n > 2, then an array of diagonals is returned.
# |      
# |      :SeeAlso:
# |          - diag : matlab workalike for 1-d and 2-d arrays.
# |          - diagflat : creates diagonal arrays
# |          - trace : sum along diagonals
# |      
# |      Examples
# |      --------
# |      
# |      >>> a = arange(4).reshape(2,2)
# |      >>> a
# |      array([[0, 1],
# |             [2, 3]])
# |      >>> a.diagonal()
# |      array([0, 3])
# |      >>> a.diagonal(1)
# |      array([1])
# |      
# |      >>> a = arange(8).reshape(2,2,2)
# |      >>> a
# |      array([[[0, 1],
# |              [2, 3]],
# |      
# |             [[4, 5],
# |              [6, 7]]])
# |      >>> a.diagonal(0,-2,-1)
# |      array([[0, 3],
# |             [4, 7]])
#
# |  trace(...)
# |      a.trace(offset=0, axis1=0, axis2=1, dtype=None, out=None)
# |      return the sum along the offset diagonal of the array's indicated
# |      axis1 and axis2.
# |   
    

    def diagonal(self):
        pass
    def trace(self):
        pass
    def det(self):
        pass

    def inverse(self): 
        pass
    def adjoint(self):
        pass    

 #  H
 #      hermitian (conjugate) transpose

    #T = property(transpose, None, None, """The transpose Matrix""")
    I = property(inverse, None, None, """The inverse Matrix""")

class Vector(Array):
    """
        A generic size Vector class deerived from Array, basically a 1 dimensional Array
    """
    __readonly__ = ('ndim',)
    
    #A Vectoris a one-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 1

       
    def _getshape(self):
        return (len(self.data),)
    def _setshape(self, newshape):
        self.resize(newshape)    
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Vector, as Vectors are one-dimensional Arrays: v.shape = (v.size,)")    
    ndim = property(lambda x : 1, None, None, "A Vector is a one-dimensional Array")
    size = property(lambda x : len(self.data), None, None, "Number of components of the Vector")
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
    
    # common operators herited from Arrays
             
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
            to the transformation (post-multiplication) of u by Matrix v when v is an instance of Matrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, self.__class__) :
            # dot product in case of a Vector
            return self.dot(other)
        elif isinstance(other, Matrix) :
            # Vector by Matrix multiplication
            dif = other.shape[1]-self.size
            res = Matrix([list(self) + [1]*dif]) * other 
            return self.__class__(res[0, 0:self.size])
        else :
            return self.__class__(Array.__)   
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix,
            in that case it is pre-multiplication by the Matrix """ 
        if isinstance (other, Matrix) :
            # not commutative with a Matrix
            dif = other.shape[0]-self.size
            res = other * Matrix(map(lambda x:[x], list(self)+[1]*dif))
            return self.__class__(res[0:self.size, 0])            
        else :
            # commutative otherwise
            return self.__mul__(other)
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Makes sense for Vector * Matrix multiplication, in place transformation of u by Matrix v
            or Vector element wise multiplication only """
        self = self.__mul__(other)            
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two vectors,
            if v is a Matrix, u^v is equivalent to transforming u by the adjoint Matrix of v """
        if isinstance(other, Vector) :
            return self.cross(other)  
        else :
            try :
                return self.__mul__(Matrix(other).adjoint())
            except :
                raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (util.clsname(self), util.clsname(other))
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """        
        self = self.__xor__(other) 
                
    # additional methods
    def sum(self):
        """ Returns the sum of the components of self """
        return reduce(operator.add, self, 0)     
    def dot(self, other):
        if isinstance(other, Vector) :
            lm = min(len(self), len(other))
            return reduce(operator.add, map(operator.mul, self[:lm], other[:lm]), 0.0)
        else :
            raise TypeError, "dot product is only defined between two vectors"        
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, Vector) and self.size == 3 and other.size == 3 :
            return self.__class__(self[1]*other[2] - self[2]*other[1],
                                  self[2]*other[0] - self[0]*other[2],
                                  self[0]*other[1] - self[1]*other[0])
        else :
            raise ValueError, "cross product is only defined between two vectors of size 3"
    def length(self):
        """ Length of self """
        return sqrt(abs(self.dot(self)))                        
    def sqLength(self):
        """ Squared length of Vector """
        return self.dot(self)
    def normal(self): 
        """ Return a normalized copy of self. To be consistant with Maya API and MEL unit command,
            does not raise an exception if self if of zero length, instead returns a copy of self """
        try :
            return self/self.length()
        except :
            return self.__class__(self)
    unit = normal
    def normalize(self):
        """ Performs an in place normalization of self """
        self /= self.length()

    def distanceTo(self, other):
        return (other-self).length()   
    def isEquivalent(self, other, tol):
        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
        try :
            return (other-self).sqLength() <= tol*tol
        except :
            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol)  
  


    # vectors of complex values inherit methods from Arrays
    






   
def _test() :  
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

    
    # iterators
    
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
               
    # transpose
    print "B=A[0]"
    B=A[0]
    print B.formated()
    #[[[1, 1, 1],
    #  [4, 6, 3],
    #  [7, 8, 5]]    
    print "B.transpose()"
    print B.transpose().formated()
    #[[1, 4, 7],
    # [1, 6, 8],
    # [1, 3, 5]]        
    print "A.transpose(0,2,1)"    
    print A.transpose(0,2,1).formated() 
    #[[[ 1  4  7]
    #  [ 1  6  8]
    #  [ 1  3  5]]
    #
    # [[10 40 70]
    #  [10 40 80]
    #  [10 30 50]]]    
    print A.transpose(2,1,0).formated() 
    print A.transpose(2,1,0).formated()
    #[[[ 1 10]
    #  [ 4 40]
    #  [ 7 70]]
    #
    # [[ 1 10]
    #  [ 6 40]
    #  [ 8 80]]
    #
    # [[ 1 10]
    #  [ 3 30]
    # [ 5 50]]] 
    
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
    print "A.conjugate()"
    print A.conjugate().formated()
    print "A.real() or real(A)"
    print A.real().formated()
    print "A.imag() or imag(A)"
    print A.imag().formated()    
    
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

    
    # Matrix and Vector
    
    
     
        
    print "end tests"
    

if __name__ == '__main__' :
    _test()    
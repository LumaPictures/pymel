
"""
A generic n-dimensionnal Array class serving as base for arbitrary length Vector and Matrix classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the reat multi index slicing, get / setitem and item indexing for iterators,
# and tried to make the method names match so that it will be easier to include Numpy instead if desired.

# TODO : try a Numpy import and fallback to the included class if not successful ?


import operator, itertools, copy, inspect

import arguments as util
from mathutils import difmap, clamp

def _toCompOrArray(value) :
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

def _tosize(value, *args):
    if len(args) == 1 :
        args = args[0]
    if isinstance(args, int) :
        newshape = [args]
    else :
        newshape = list(args)
        
    if isinstance(value, Array) :
        if value.shape == newshape :
            res = value
        else :
            res = value.resize(newshape)       
    elif util.isNumeric(value) :
        value = Array.fill(newshape, value)
    else:
        raise TypeError, "cannot build Array from %s" % (type(value))    
        
    return res
    
    def __sub__(self, other) :
        """ a.__sub__(b) <==> a-b
            Returns the result of the element wise substraction of b from a if b is convertible to Array,
            substracts b from every component of a if b is a single numeric value """       
        if util.isNumeric(other) :
            return self.__class__(x-other for x in self)
        else :
            shape = self.shape
            if not isinstance(other, Array) :
                try :
                    other = Array(other, shape=shape)
                except :
                    raise TypeError, "unsupported operand type(s) for +: %s and %s" % (type(self), type(other))
            if other.shape != shape :
                try :
                    other = other.resize(shape)
                except :
                    raise ValueError, "shape mismatch: objects cannot be resized to similar shapes"
            res = map(lambda x,y:x - y, self, other)
            try :
                return self.__class__(res)
            except :
                try :
                    return other.__class__(res)
                except :
                    return Array(res)
                
def amap(fn, *args) :
    """ A map like function that maps fn element-wise on every argument Arrays """
    
    maxshape = ()
    if args :
        args = [_toCompOrArray(a) for a in args]
        shapes = [_shapeInfo(a) for a in args]
        shapes.sort(cmp, lambda x:x[2])
        maxshape = shapes[-1][0]
        iters = [_tosize(a, maxshape).flat for a in args]
    
    return Array(map(fn, *iters), maxshape)


# iterator classes on a specific Array dimension, supporting __getitem__
# in a Numpy like way

class ArrayIter(object):
    """ An iterator on Array sub-arrays of given number of dimensions, that support element indexing """
    def __init__(self, data, sub_dim=None) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, Array) :
            self.base = data
            if self.base :
                base_ndim = self.base.ndim
                if sub_dim is None :
                    sub_dim = base_ndim - 1
                ndim = base_ndim - sub_dim
                if ndim > 0 :
                    self.base = data
                    self.ndim = ndim
                    # the shape of the sub array we iterate on             
                    self.shape = tuple(self.base.shape[:ndim])
                    # the shape of the items the iterator will produce (sub arrays or numerics)
                    self.itemshape = tuple(self.base.shape[ndim:])
                    self.size = reduce(operator.mul, self.shape, 1)
                    self.subsizes = [reduce(operator.mul, self.shape[i+1:], 1) for i in xrange(self.ndim)]   
                    self.coords = [0]*self.ndim
                elif ndim == 0 :
                    self = ArrayIter(Array([data]))
                else :
                    self = ArrayIter(Array([]))
            else :
                # empty iterator
                self.ndim = 1
                self.shape = (0,)
                self.size = 0
                self.subsizes = (1,)
                self.coords = (0,)
        else :
            raise TypeError, "%s can only be built on Array" % util.clsname(self)
        
    def __length_hint__(self) :
        return self.size
    def __len__(self) :
        return self.size    
    def __iter__(self) :
        return self 
    
    def next(self):
        for i in range(self.ndim-1, 0, -1) :
            if self.coords[i] == self.shape[i] :
                self.coords[i] = 0
                self.coords[i-1] += 1
        if self.coords[0] >= self.shape[0] : 
            raise StopIteration

        val =  self.base.__getitem__(tuple(self.coords))
        self.coords[-1] += 1
        return val         

    # fast internal version without checks or negative index / slice support
    def _toArrayCoords(self, item):
        coords = []
        for i in xrange(self.ndim) :
            c = item//self.subsizes[i]
            item -= c*self.subsizes[i]
            coords.append(c)
        return tuple(coords)                      
    # fast internal version without checks or negative index / slice support    
    def _toIterItem(self, coords):
        return reduce(lambda x, y: x+y[0]*y[1], zip(coords, self.subsizes), 0)
        
    def toArrayCoords(self, item):
        """ Converts an iterator item index (nth item) for that Array iterator to a tuple of axis coordinates for that Array, 
            returns a single coordinates tuple or a list of coordinate tuples if item index was a slice """
        if isinstance(item, slice) :
            return [self._toArrayCoords(f) for f in range(self.size)[item]]
        elif isinstance(item, int) :
            if item < 0 :
                item = self.size - item
            if item>=0 and item<self.size :
                return self._toArrayCoords(item)
            else :
                raise IndexError, "index %s out of range (%s)" % (item, self.size)
        else :
            raise TypeError, "Arrays iterator item index must be an integer" 
            
    def toIterItem(self, *args):
        """ Converts axis coordinates for that array to an index (nth item) for that Array iterator,
            returns a single item index or a list of item indices if coordinates include slices """
        # TODO : FIXME
        if args :
            shape = self.shape
            ndim = self.ndim
            if len(args) == 1 and util.isIterable(args[0]) :
                args = list(args[0])
            else :
                args = list(args)
            if len(args) > ndim :
                raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(args), ndim)
            allcoords = []
            for i, c in enumerate(args) :
                if isinstance(c, slice) :
                    pass
                elif isinstance(c, int) :
                    if c<0 :
                        c = self.shape[i]-c
                    if c>=0 and c<shape[i] :
                        allcoords.append(c)
                    else :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
                else :
                    raise TypeError, "Arrays indices must be integers"     
        else :
            return 0 

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
            
class ArrayAxisIter(object):
    def __init__(self, data, axis=0) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, Array) :
            self.base = data
            self.shape = self.base.shape
            self.size = self.base.size
            self.ndim = self.base.ndim            
            self.coords = [0]*len(self.shape)
            if onindex in range(self.ndim) :
                self.onindex = onindex                  
            else :
                raise ValueError, "%s has %s dimensions, cannot iterate on index %s" % (util.clsname(self.base), self.base.ndim, onindex)
        else :
            raise TypeError, "%s can only be built on Array" % util.clsname(self)
    def __length_hint__(self) :
        return self.shape[self.onindex]
    def __iter__(self) :
        return self 
    
    def _nextrow(self) :
        if self.coords[0] == self.shape[0] :        
            raise StopIteration
        self.ptr = self.base.Matrix[self.coords[0]]
        val =  tuple(api.MScriptUtil.getDoubleArrayItem(self.ptr, c) for c in xrange(self.shape[1]))
        self.coords[0] += 1
        return val
    def next(self):
        pass     
    def __getitem__(self, i) :
        return tuple(self)[i]
    
# A generic multi dimensional Array class
# NOTE : Numpy Array class could be used instead, just implemented the bare minimum inspired from it
class Array(object):
    """ A generic n-dimensional array class using nested lists for storage """
        
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
        self = self.reshape(newshape)
        
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None, "Shape of the Array (number of dimensions and number of components in each dimension")    
    ndim = property(lambda x : x._ndim, None, None, "Number of dimensions of the Array")
    size = property(lambda x : x._size, None, None, "Total size of the Array (number of individual components)")
    def _getdata(self):
        return self._data
    def _setdata(self, data):
        if isinstance(data, list) :
            self._data = data
        else :
            self._data = list(data)
        self._cacheshape() 
    def _deldata(self):
        del self._data[:]
        self._cacheshape()     
    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
    
    def isIterable(self):
        """ True if array is iterable (has a dimension of more than 0) """
        return self.ndim > 0
    
    @classmethod
    def default(cls, shape=()):
        """ Default Array for a given shape """
        return cls.fill(shape=shape, value=0)
        
    @classmethod
    def fill(cls, shape=(), value=0):
        """ fill(value=0, shape=()) :
            Returns an Array filled with value for the given shape """
        if shape :
            if hasattr(value,'__iter__') :
                value = Array(value)
                new = cls.default()
                dim = new.ndim
                valuedim = value.ndim
                if dim >= valuedim : 
                    subIter = new.subarray(new.ndim-value.ndim)
                    for i in xrange(len(subIter)) :
                        subIter[i] = value
                    return new
                else :
                    raise ValueError, "value has more dimensions that the specified shape"
            elif util.isNumeric(value) :
                for dim in reversed(shape) :
                    value = [value] * dim
                return cls(value)
            else :
                raise ValueError, "fill value can only be a numeric or Array"
        else :
            return cls([])        
                                                
    def __init__(self, *args, **kwargs ):
        """ Initialize an Array from one or several nested lists or numeric values """
                    
        if args :
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            if isinstance (args, self.__class__) :
                # copy constructor
                print "copying %s to self" % (args)
                self.data = copy.copy(args.data)
            elif hasattr(args, '__iter__') :
                self._data = []
                subshapes = []
                for arg in args :
                    sub = _toCompOrArray(arg)
                    subshape, subdim, subsize = _shapeInfo(sub)                    
                    self._data.append(sub)
                    subshapes.append(subshape)
                if not reduce(lambda x, y : x and y == subshapes[0], subshapes, True) :
                    raise ValueError, "all sub-arrays must have same shape"
                self._cacheshape()                           
            elif util.isNumeric(args) :
                raise TypeError, "an Array cannot be initialized from a single value, need at least 2 components or an iterable"
            else :
                raise TypeError, "an Array element can only be another Array or an iterable"
        else :
            self.data = self.__class__.default().data
            
        # can re-shape on creation if a shape keyword is specified
        shape = kwargs.get('shape', None)
        if shape is not None :
            self.resize(shape)
                    
    def append(self, value):
        value = _toCompOrArray(value)
        valueshape, valuedim, valuesize = _shapeInfo(value)        
        if list(valueshape) == self.shape[1:] :
            self._data.append(self, value)
            self._cacheshape()
        else :
            raise TypeError, "argument does not have the correct shape to append to Array"       
 
    def reshape(self, *args):
        """ a.reshape(shape)
            Returns the Array a reshaped according to the shape argument """
        if len(args) == 1 :
            args = args[0]
        if isinstance(args, int) :
            newshape = [args]
        else :
            newshape = list(args)
            
        # print "set shape to %s" % newshape  

        if newshape :
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
                dif = size / newsize
                newshape[unknown] = dif
                newsize *= dif
        else :
            newsize = 0

        if newsize != self.size :
            raise ValueError, "total size of new array must be unchanged"
        
        return self.resize(newshape)
  
    def resize(self, *args):
        """ a.resize(shape)
            Returns the Array a resized according to the shape argument """        
        if len(args) == 1 :
            args = args[0]
        if isinstance(args, int) :
            newshape = [args]
        else :
            newshape = list(args)
           
        new = None
        for cls in inspect.getmro(self.__class__) :
            if issubclass(cls, Array) :
                try :
                    new = cls.default(newshape)
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
            raise TypeError, "%s cannot be initialized to shape %s, and has no base class that can" % (type(self), newshape)
        
    # hstack and vstack 
    
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

        value = _toCompOrArray(reduce(lambda x, y: Array._extract(x, y), index, self))
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
                    value = Array.fill(subshape, value)
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
        
    def __iter__(self) :
        """ Default Array iterator on first dimension """
        # return ArrayIter(self)
        return iter(self.data) 
     
    def axisiter(self, axis=0) :
        """ Returns an iterator using a specific axis of self as first dimension,
            it is equivalent to transposing the Array using that axis and iterating on the new Array first dimension """
        return ArrayAxisIter(self, axis)
    
    def subarray(self, dim=None) :
        """ Returns an iterator on all sub Arrays for a specific sub Array dimension,
            self.subarray(1) is equivalent to self.flat
            self.subarray() is equivalent to self.subarray(self.ndim-1) and thus to self.__iter__() """
        return ArrayIter(self, dim)

    @property    
    def flat(self):
        """ Flat iterator on the Array components """
        return ArrayIter(self, 0)   

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
                if other in sub :
                    return True
        return False

    # common operators
    def __neg__(self):
        """ a.__neg__() <==> -a
            Element-wise negation of a """        
        return self.__class__(-x for x in self)      
    def __add__(self, other) :
        """ a.__add__(b) <==> a+b
            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value """        
        if util.isNumeric(other) :
            return self.__class__(x+other for x in self)
        else :
            shape = self.shape
            if not isinstance(other, Array) :
                try :
                    other = Array(other, shape=shape)
                except :
                    raise TypeError, "unsupported operand type(s) for +: %s and %s" % (type(self), type(other))
            if other.shape != shape :
                try :
                    other = other.resize(shape)
                except :
                    raise ValueError, "shape mismatch: objects cannot be resized to similar shapes"
            res = map(lambda x,y:x + y, self, other)
            try :
                return self.__class__(res)
            except :
                try :
                    return other.__class__(res)
                except :
                    return Array(res)
    def __radd__(self, other) :
        """ a.__radd__(b) <==> b+a
            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value """        
        return self.__add__(other)  
    def __iadd__(self, other):
        """ a.__iadd__(b) <==> a += b
            In place addition of a and b, see __add__, b must be convertible to a's type """
        self = self.__class__(self.__add__(other))
    def __sub__(self, other) :
        """ a.__sub__(b) <==> a-b
            Returns the result of the element wise substraction of b from a if b is convertible to Array,
            substracts b from every component of a if b is a single numeric value """       
        if util.isNumeric(other) :
            return self.__class__(x-other for x in self)
        else :
            shape = self.shape
            if not isinstance(other, Array) :
                try :
                    other = Array(other, shape=shape)
                except :
                    raise TypeError, "unsupported operand type(s) for +: %s and %s" % (type(self), type(other))
            if other.shape != shape :
                try :
                    other = other.resize(shape)
                except :
                    raise ValueError, "shape mismatch: objects cannot be resized to similar shapes"
            res = map(lambda x,y:x - y, self, other)
            try :
                return self.__class__(res)
            except :
                try :
                    return other.__class__(res)
                except :
                    return Array(res)
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a Vector instance,
            replace every component c of u by v-c if v is a scalar """        
        if util.isNumeric(other) :
            return self.__class__(map( lambda x: other-x, self))        
        else :
            return difmap(operator.sub, other, self)     
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        self = self.__class__(self.__sub__(other))        
#    def __div__(self, other):
#        """ u.__div__(v) <==> u/v
#            Returns the result of the element wise division of each component of u by the
#            corresponding component of v if both are convertible to Vector,
#            divide every component of u by v if v is a scalar """  
#        if util.isNumeric(other) :
#            return self.__class__(map(lambda x: x/other, self))
#        else :
#            return difmap(operator.div, self, other)  
#    def __rdiv__(self, other):
#        """ u.__rdiv__(v) <==> v/u
#            Returns the result of the element wise division of each component of v by the
#            corresponding component of u if both are convertible to Vector,
#            invert every component of u and multiply it by v if v is a scalar """
#        if util.isNumeric(other) :
#            return self.__class__(map(lambda x: other/x, self))
#        else :
#            return difmap(operator.div, other, self)  
#    def __idiv__(self, other):
#        """ u.__idiv__(v) <==> u /= v
#            In place division of u by v, see __div__ """        
#        self = self.__class__(self.__div__(other)) 

          
#    # action depends on second object type
#    # NOTE : dot product mapped on mult if both arguments are Vector, else we do element wise mutliplication
#    def __mul__(self, other) :
#        """ u.__mul__(v) <==> u*v
#            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
#            to the transformation (post-multiplication) of u by Matrix v when v is an instance of Matrix,
#            and to element wise multiplication when v is a scalar or a sequence """
#        if isinstance(other, self.__class__) :
#            # dot product in case of a Vector
#            return self.dot(other)
#        elif isinstance(other, Matrix) :
#            # Vector by Matrix multiplication
#            dif = other.shape[1]-self.size
#            res = Matrix([list(self) + [1]*dif]) * other 
#            return self.__class__(res[0, 0:self.size])
#        elif util.isNumeric(other) :
#            # multiply all components by a scalar
#            return self.__class__(map(lambda x: x*other, self))
#        else :
#            # try an element wise multiplication if other is iterable
#            try :
#                other = list(other)
#            except :
#                raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(self), util.clsname(other))
#            lm = min(len(other), len(self))
#            l = map(operator.mul, self[:lm], other[:lm]) + self[lm:len(self)]
#            return self_class__(*l)      
#    def __rmul__(self, other):
#        """ u.__rmul__(v) <==> v*u
#            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix,
#            in that case it is pre-multiplication by the Matrix """ 
#        if isinstance (other, Matrix) :
#            # not commutative with a Matrix
#            dif = other.shape[0]-self.size
#            res = other * Matrix(map(lambda x:[x], list(self)+[1]*dif))
#            return self.__class__(res[0:self.size, 0])            
#        else :
#            # commutative otherwise
#            return self.__mul__(other)
#    def __imul__(self, other):
#        """ u.__imul__(v) <==> u *= v
#            Makes sense for Vector * Matrix multiplication, in place transformation of u by Matrix v
#            or Vector element wise multiplication only """
#        self = self.__mul__(other)            


#                
#    # additional methods

    # additional methods
    
        # min, max, sum, prod
        
        # nonzero
        
#    def sum(self):
#        """ Returns the sum of the components of self """
#        return reduce(operator.add, self, 0)     
  
#    def isEquivalent(self, other, tol):
#        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
#        try :
#            return (other-self).sqLength() <= tol*tol
#        except :
#            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol)  
#    def blend(self, other, blend=0.5):
#        """ u.blend(v, blend) returns the result of blending from Vector instance u to v according to
#            either a scalar blend where it yields u*(1-blend) + v*blend Vector,
#            or a an iterable of independent blend factors """ 
#        try :
#            other = self.__class__(other)
#        except :
#            raise TypeError, "%s is not convertible to a %s, check help(%s)" % (util.clsname(other), util.clsname(self), util.clsname(self))        
#        if util.isNumeric(blend) :
#            l = (self*(1-blend) + other*blend)[:len(other)] + self[len(other):len(self)]
#            return self.__class__(*l)            
#        else :
#            try : 
#                bl = list(blend)
#            except :
#                raise TypeError, "blend can be an iterable (list, tuple, Vector...) of numeric values, or a single numeric value, not a %s" % util.clsname(blend)
#            lm = min(len(bl), len(self), len(other))
#            l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
#            return self.__class__(*l)       
#    def clamp(self, low=0.0, high=1.0):
#        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
#            or the corresponding components of low and high if low and high are sequences of scalars """
#        ln = len(self)
#        if util.isNumeric(low) :
#            low = [low]*ln
#        else :
#            try : 
#                low = list(low)[:ln]
#            except :
#                raise TypeError, "'low' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % util.clsname(low) 
#        if util.isNumeric(high) :
#            high = [high]*ln
#        else :
#            try :  
#                high = list(high)[:ln]
#            except :
#                raise TypeError, "'high' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % util.clsname(high)         
#        lm = min(ln, len(low), len(high))             
#        return self.__class__(map(clamp, self, low, high))    


    # arrays of complex values
    def conjugate(self):
        return self.__class__(x.conjugate() for x in self)
    def ReIm(self):
        """ Returns the real and imaginary parts """
        return [
            self.__class__(map(lambda x: x.real, self)),
            self.__class__(map(lambda x: x.imag, self)),
            ]
    def AbsArg(self):
        """ Returns modulus and phase parts """
        return [
            self.__class__(map(lambda x: abs(x), self)),
            self.__class__(map(lambda x: atan2(x.imag,x.real), self)),
            ]
        

        
#          diagonal(...)
# |      a.diagonal(offset=0, axis1=0, axis2=1) -> diagonals
# |      
# |      If a is 2-d, return the diagonal of self with the given offset, i.e., the
# |      collection of elements of the form a[i,i+offset]. If a is n-d with n > 2,
# |      then the axes specified by axis1 and axis2 are used to determine the 2-d
# |      subarray whose diagonal is returned. The shape of the resulting array can
# |      be determined by removing axis1 and axis2 and appending an index to the
# |      right equal to the size of the resulting diagonals.
  
#     conjugate(...)
# |      a.conjugate()    
   
    def transpose(self, *args):
        ndim = self.ndim
        if not args :
            axis = range(ndim-1, -1, -1)
        else :
            axis = []
            for a in args :
                a = int(a)
                if a in range(ndim) :
                    if not a in axis :
                        axis.append(a)
                    else :
                        raise ValueError, "transpose axis %s specified twice" % a
                else :
                    raise ValueError, "transpose axis %s does not exist for Array of dimension %s" % (a, ndim)
            if len(axis) < ndim :
                for a in range(ndim) :
                    axis.append(a)
        print "transpose axis %s" % axis
        res = self
        return res
    
    T = property(transpose, None, None, """The transposed array""") 


class Vector(Array):
    """
        A generic size Vector class, basically a 1 dimensional Array
    """
    
    shape = property(lambda x : (list.__len__(x),), None, None, "A Vector is a one-dimensional Array of n components")   
    ndim = property(lambda x : 1, None, None, "A Vector is a one-dimensional Array")
    size = property(lambda x : list.__len__(x), None, None, "Size of the Vector (number of components)")

    
    # common operators
    def __neg__(self):
        """ u.__neg__() <==> -u
            Returns the Vector obtained by negating every component of u """        
        return self.__class__(map(operator.neg, self))   
    def __invert__(self):
        """ u.__invert__() <==> ~u
            unary inversion, returns 1 - u for vectors """        
        return self.__class__(map(lambda x: 1.0-x, self))      
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to Vector,
            adds v to every component of u if v is a scalar """        
        if util.isNumeric(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :
            return difmap(operator.add, self, other)  
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to Vector,
            adds v to every component of u if v is a scalar """        
        return self.__add__(other)  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        self = self.__class__(self.__add__(other))
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a Vector instance,
            substract v to every component of u if v is a scalar """        
        if util.isNumeric(other) :
            return self.__class__(map( lambda x: x-other, self))        
        else :
            return difmap(operator.sub, self, other)      
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a Vector instance,
            replace every component c of u by v-c if v is a scalar """        
        if util.isNumeric(other) :
            return self.__class__(map( lambda x: other-x, self))        
        else :
            return difmap(operator.sub, other, self)     
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        self = self.__class__(self.__sub__(other))        
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the element wise division of each component of u by the
            corresponding component of v if both are convertible to Vector,
            divide every component of u by v if v is a scalar """  
        if util.isNumeric(other) :
            return self.__class__(map(lambda x: x/other, self))
        else :
            return difmap(operator.div, self, other)  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to Vector,
            invert every component of u and multiply it by v if v is a scalar """
        if util.isNumeric(other) :
            return self.__class__(map(lambda x: other/x, self))
        else :
            return difmap(operator.div, other, self)  
    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """        
        self = self.__class__(self.__div__(other)) 
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v """
        try :
            return list.__eq__(self, self.__class__(other))
        except :
            return False              
    # action depends on second object type
    # NOTE : dot product mapped on mult if both arguments are Vector, else we do element wise mutliplication
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
        elif util.isNumeric(other) :
            # multiply all components by a scalar
            return self.__class__(map(lambda x: x*other, self))
        else :
            # try an element wise multiplication if other is iterable
            try :
                other = list(other)
            except :
                raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(self), util.clsname(other))
            lm = min(len(other), len(self))
            l = map(operator.mul, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)      
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
    def blend(self, other, blend=0.5):
        """ u.blend(v, blend) returns the result of blending from Vector instance u to v according to
            either a scalar blend where it yields u*(1-blend) + v*blend Vector,
            or a an iterable of independent blend factors """ 
        try :
            other = self.__class__(other)
        except :
            raise TypeError, "%s is not convertible to a %s, check help(%s)" % (util.clsname(other), util.clsname(self), util.clsname(self))        
        if util.isNumeric(blend) :
            l = (self*(1-blend) + other*blend)[:len(other)] + self[len(other):len(self)]
            return self.__class__(*l)            
        else :
            try : 
                bl = list(blend)
            except :
                raise TypeError, "blend can be an iterable (list, tuple, Vector...) of numeric values, or a single numeric value, not a %s" % util.clsname(blend)
            lm = min(len(bl), len(self), len(other))
            l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
            return self.__class__(*l)       
    def clamp(self, low=0.0, high=1.0):
        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
            or the corresponding components of low and high if low and high are sequences of scalars """
        ln = len(self)
        if util.isNumeric(low) :
            low = [low]*ln
        else :
            try : 
                low = list(low)[:ln]
            except :
                raise TypeError, "'low' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % util.clsname(low) 
        if util.isNumeric(high) :
            high = [high]*ln
        else :
            try :  
                high = list(high)[:ln]
            except :
                raise TypeError, "'high' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % util.clsname(high)         
        lm = min(ln, len(low), len(high))             
        return self.__class__(map(clamp, self, low, high))    
    # TODO : can implement Vector smoothstep, setRange, hermite from mathutils the same way  

    # vectors of complex values
    def conjugate(self):
        return self.__class__(map(lambda x: x.conjugate(), self))
    def ReIm(self):
        """ Returns the real and imaginary parts """
        return [
            self.__class__(map(lambda x: x.real, self)),
            self.__class__(map(lambda x: x.imag, self)),
            ]
    def AbsArg(self):
        """ Returns modulus and phase parts """
        return [
            self.__class__(map(lambda x: abs(x), self)),
            self.__class__(map(lambda x: atan2(x.imag,x.real), self)),
            ]

class MatrixIter(ArrayIter):
    pass

class Matrix(Array):
    """
    A generic size Matrix class, basically a 2 dimensional Array
    """

    def _getshape(self):
        lr = list.__len__(self)
        if lr :
            shape = (lr, list.__len__(self[0]))
        else :
            shape = (0,0)
        return shape
    shape = property(_getshape, None, None, "Shape of the Matrix, (m, n)")    
    ndim = property(lambda x : 2, None, None, "A Matrix is a two-dimensional Array")
    size = property(lambda x : x.shape[0]*x.shape[1], None, None, "Size of the Matrix (total number of components)") 
    
    def __init__(self, rowColList = [[0]*4]*4 ):
        for i in range( 0, len(rowColList )):
            rowColList[i] = Vector( rowColList[i] )
        
        list.__init__(self, rowColList)
    
        
    def __add__(self, other):
        try:
            return Matrix(map(lambda x,y: x+y, self, other))
        except:
            return Matrix(map( lambda x: x+other, self))
        
    def __neg__(self):
        return Matrix(map(lambda x: -x, self))
    
    def __sub__(self, other):
        try:
            return Matrix(map(lambda x,y: x-y, self, other))
        except:
            return Matrix(map( lambda x: x-other, self))


    def __mul__(self, other):
        """
        Element by element multiplication
        """
        temp = other.transpose()
        return Matrix( [ [ dot(row,col) for col in temp ] for row in self ] )

    def __rmul__(self, other):
        return (self*other)
        
    def __div__(self, other):
        """
        Element by element division.
        """
        try:
            return Vector(map(lambda x,y: x/y, self, other))
        except:
            return Vector(map(lambda x: x/other, self))

    def __rdiv__(self, other):
        """
        The same as __div__
        """
        try:
            return Vector(map(lambda x,y: x/y, other, self))
        except:
            # other is a const
            return Vector(map(lambda x: other/x, self))
    
    def row(self, row):
        return self[row]
        
    def col(self, col):
        import operator
        return Vector(map(operator.itemgetter(col),self))
    
    def nrows(self):
        len(self)
    
    def ncols(self):
        return len(self.transpose())
    
    def sum(self):
        return reduce(operator.add, self.flat, 0)
    def diag(self):
        pass
    def det(self):
        pass
    def transpose(self):
        return Matrix( apply( map, [None]+self ) )
    def inverse(self): 
        pass
    def adjoint(self):
        pass    

    def flat(self):
        return reduce( lambda x,y: list(x)+list(y), self ) 



   
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
    A = Array.default((2, 2))
    print A.formated()
    A = Array.fill((2, 2), 1) 
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
    B = Array([[1,1,1],[4,4,3],[7,8,5]])
    print B
    print repr(B)
    print B.formated() 
    C = Array(B) 
    print repr(C)
    print C.formated()
    print C is B
    #shallow copy
    print C.data is B.data
    print C.data[0] is B.data[0]
    print C[0] is B[0]
    C = B.copy()
    print repr(C)
    print C.formated()
    print C is B
    #shallow copy
    print C[0] is B[0]    
    C = B.deepcopy()
    print repr(C)
    print C.formated()
    print C is B
    #deep copy
    print C[0] is B[0] 
    
           
    C = Array([C]) 
    print repr(C)
    print C.formated()       
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
    print "A:", A
    # [[[1, 1, 1], [4, 6, 3], [7, 9, 5]], [[10, 10, 10], [40, 40, 30], [70, 80, 50]]]
    print "list(A.flat):",list(A.flat)
    # [1, 1, 1, 4, 6, 3, 7, 9, 5, 10, 10, 10, 40, 40, 30, 70, 80, 50]
    print "A.flat[7]", A.flat[7]
    # 9
    print "A.flat[2:12]", A.flat[2:12]
    # [1, 4, 6, 3, 7, 9, 5, 10, 10, 10]
    A.flat[7] = 8
    print "A.flat[7] = 8", A
    # [[[1, 1, 1], [4, 6, 3], [7, 8, 5]], [[10, 10, 10], [40, 40, 30], [70, 80, 50]]]
    print "A[:,:,1] = 2"
    A[:,:,1] = 2
    print A.formated()
    print "A = A + 2"
    A = A + 2
    print A.formated()

    print "B=Array([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])"
    B = Array([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])
    print B.formated()
    #[[ 1  2  3  4]
    # [ 5  6  7  8]
    # [ 9 10 11 12]
    # [13 14 15 16]]     
    print "B.reshape(2, 2, 2, 2):"
    print B.reshape(2, 2, 2, 2).formated()
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
    print "B.resize(4, 5):"
    print B.resize(4, 5).formated()
    #[[ 1  2  3  4  5]
    # [ 6  7  8  9 10]
    # [11 12 13 14 15]
    # [16  0  0  0  0]]
    print "A"
    print A.formated()
#    [[[3, 4, 3],
#      [6, 4, 5],
#      [9, 4, 7]],
#    
#     [[12, 4, 12],
#      [42, 4, 32],
#      [72, 4, 52]]]    
    print "B"
    print B.formated()
#    [[1, 2, 3, 4],
#     [5, 6, 7, 8],
#     [9, 10, 11, 12],
#     [13, 14, 15, 16]]    
    print "B.resize(2, 3, 3)"
    print B.resize(2, 3, 3).formated()
#    [[[1, 2, 3],
#      [4, 5, 6],
#      [7, 8, 9]],
#    
#     [[10, 11, 12],
#      [13, 14, 15],
#      [16, 0, 0]]]    
    print "A+B"
    print (A+B).formated()
    #[[[4, 6, 6],
    #  [10, 9, 11],
    #  [16, 12, 16]],
    #
    # [[22, 15, 24],
    #  [55, 18, 47],
    #  [88, 4, 52]]]    
    print "B+A"
    print (B+A).formated()
    #[[4, 6, 6, 10],
    # [9, 11, 16, 12],
    # [16, 22, 15, 24],
    # [55, 18, 47, 88]]    
    print "-B"
    print (-B).formated()    
    
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
        
    print "end tests"
    

if __name__ == '__main__' :
    _test()    
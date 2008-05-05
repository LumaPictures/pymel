
"""
A generic n-dimensionnal Array class serving as base for arbitrary length Vector and Matrix classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the reat multi index slicing, get / setitem and item indexing for iterators,
# and tried to make the method names match so that it will be easier to include Numpy instead if desired.

# TODO : try a Numpy import and fallback to the included class if not successful ?


import operator, itertools, copy

import arguments as util
from mathutils import difmap, clamp

def _compOrArray(value) :
    if hasattr(value, '__iter__') :
        # convert values iterables to Array
        value = Array(value)
        shape = value.shape
    elif util.isNumeric(value) :
        # a single numeric value
        shape = () 
    else :
        raise TypeError, "invalid value type %s for Array" % (util.clsname(value))
    
    return value, shape

# iterator classes on a specific Array dimension, supporting __getitem__
# in a Numpy like way

class ArrayIter(object):
    """ An iterator on Array sub-arrays of given number of dimensions, that support element indexing """
    def __init__(self, data, sub_dim=None) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, Array) :
            self.base = data
            if Array :
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

        print "expected item shape: %s" % list(self.itemshape)
        value, shape = _compOrArray(value)
        if hasattr(value, '__iter__') :
            # convert values iterables to Array
            value = Array(value)
            valueshape = value.shape
        elif util.isNumeric(value) :
            # a single numeric value
            valueshape = () 
        else :
            raise TypeError, "invalid value type %s for %s" % (util.clsname(value), util.clsname(self.base))
                     
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
        newsize = reduce(operator.mul, newshape, 1)
        if newsize == self.size :
            pass
        else :
            raise ValueError, "Can only change Array shape to a new shape of same size"
    shape = property(_getshape, _setshape, None, "Shape of the Array (number of dimensions and number of components in each dimension")    
    ndim = property(lambda x : x._ndim, None, None, "Number of dimensions of the Array")
    size = property(lambda x : x._size, None, None, "Total size of the Array (number of individual components)")
    def _getdata(self):
        return self._data
    def _setdata(self, data):
        if util.isNumeric(data) :
            self._data = data
        else :
            self._data = list(data)
    def _deldata(self):
        del self._data            
    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
    
    def isIterable(self):
        return self.ndim > 0
                                      
    def __init__(self, *args ):
        """ Initialize an Array from one or several nested lists or numeric values """

        self.data = []       
        if args :
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            if isinstance (args, self.__class__) :
                self.data = args.data
            if hasattr(args, '__iter__') :
                subshapes = []
                for arg in args :
                    sub, shape = _compOrArray(arg)
                    self.data.append(sub)
                    subshapes.append(shape)
                if not reduce(lambda x, y : x and y == subshapes[0], subshapes, True) :
                    raise ValueError, "all sub-arrays must have same shape"                            
            elif util.isNumeric(args) :
                raise TypeError, "an Array cannot be initialized from a single value, need at least 2 components or an iterable"
            else :
                raise TypeError, "an Array element can only be another Array or a numeric value"

        self._cacheshape()
                    
    def append(self, value):
        # value, shape = _compOrArray(value)
        value, shape = _compOrArray(value)
        if list(shape) == self.shape[1:] :
            self.data.append(self, value)
        else :
            raise TypeError, "argument does not have the correct shape to append to Array"       
        self._cacheshape()
  
    def resize(self, new_shape, refcheck=True, order=False) :
        pass
    
        self._cacheshape()
    
    # hstack and vstack 
    
    def copy(self):
        pass
    
    def deepcopy(self):
        pass
    
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
    def _extract(x, y) :
        if isinstance(x, Array) :
            res = x.data[y]
        else :
            res = [Array._extract(a, y) for a in x]
        return res
  
    # TODO : Numpy like support for index Arrays ?
    def __getitem__(self, index):
        """ Get value from either a single (first dimension) or multiple index, support for slices"""
        # print "index %r", index
        if not hasattr(index, '__iter__') or len(index) == 1 :
            # single index, means on first dimension
            return self.data[index]            
        else :
            # multiple index
            ndim = self.ndim
            shape = self.shape
            coords = [slice(None, None, None)]*ndim  
            # index = list(index)[:ndim]
            if len(index) > ndim :
                raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), ndim)                   
            for i, c in enumerate(index) :
                if isinstance(c, slice) :
                    coords[i] = c
                elif isinstance(c, int) :
                    # bounds check
                    if c < 0 :
                        c = shape[i] - c
                    if c>=0 and c<shape[i] :
                        coords[i] = c
                    else :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
                else :
                    raise TypeError, "Arrays indices must be integers" 
            value, shape = _compOrArray(reduce(lambda x, y: Array._extract(x, y), coords, self))
            return value

    def __setitem__(self, rc, value):
        """ Set value from either a single (first dimension) or multiple index, support for slices"""
        
        # convert value to Array if it's not a component
        if hasattr(value, '__iter__') :
            # convert values iterables to Array
            value = Array(value)
            valueshape = value.shape
        elif util.isNumeric(value) :
            # a single numeric value
            valueshape = () 
        else :
            raise TypeError, "invalid value type %s for %s" % (util.clsname(value), util.clsname(self))        
        if not hasattr(index, '__iter__') or len(index) == 1 :
            # single index, means on first dimension
            return list.__setitem__(self, index)            
        else :
            # multiple index
            ndim = self.ndim
            shape = self.shape
            coords = [slice(None, None, None)]*ndim  
            # index = list(index)[:ndim]
            if len(index) > ndim :
                raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), ndim)                   
            for i, c in enumerate(index) :
                if isinstance(c, slice) :
                    coords[i] = c
                elif isinstance(c, int) :
                    # bounds check
                    if c < 0 :
                        c = shape[i] - c
                    if c>=0 and c<shape[i] :
                        coords[i] = c
                    else :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
                else :
                    raise TypeError, "Arrays indices must be integers" 
            res = reduce(lambda x, y: Array._extract(x, y), coords, self)
            # if isinstance(res, list) :
            #   res = Array(res)
            return res
        
        # numpy like m[:,:] format, we set a sub Matrix
        if util.isScalar(value) :
            for i in range(self.__class__.shape[0])[r] :
                self[i,c] = value            
        else :
            for v, i in enumerate(range(self.__class__.shape[0])[r]) :
                self[i,c] = value[v]

    def __delitem__(self, rc) :
        """ Delete a sub-Array, only possible for a full axis"""
        if not hasattr(index, '__iter__') or len(index) == 1 :
            # single index, means on first dimension
            return list.__delitem__(self, index)            
        else :
            # multiple index
            ndim = self.ndim
            shape = self.shape
            coords = [slice(None, None, None)]*ndim  
            # index = list(index)[:ndim]
            if len(index) > ndim :
                raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), ndim)                   
            for i, c in enumerate(index) :
                if isinstance(c, slice) :
                    if c == slice(None, None, None) :
                        coords[i] = c
                    else :
                        raise ValueError, "can only delete full axis/dimension from an Array"
                elif isinstance(c, int) :
                    # bounds check
                    if c < 0 :
                        c = shape[i] - c
                    if c>=0 and c<shape[i] :
                        coords[i] = c
                    else :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
                else :
                    raise TypeError, "Arrays indices must be integers"
            # all cords must be full slices except the ones to delete 
            res = reduce(lambda x, y: Array._extract(x, y), coords, self)
            # if isinstance(res, list) :
            #   res = Array(res)
            return res
        
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

    def __mul__(self, other):
        """ mul for arrays is mapped to element-wise multiplication, use dot for Matrix like multiplication,
            or convert Arrays to Matrices """
        pass
    
    def __add__(self, other):
        pass
        
    # additional methods
    
        # min, max, sum, prod
        
        # nonzero
        
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
    
    def __str__(self):
        res = ''
        for i in range(0,len(self)):
             res += ', '.join( map( lambda x: "%.03f" % x, self[i]) ) + '\n'
        return res
        
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
    print A
    print repr(A)
    print A.formated()
    print A.shape
    print A.ndim
    print A.size
    print A.data    
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
    B = Array(B) 
    print repr(B)
    print B.formated()
    B = Array([B]) 
    print repr(B)
    print B.formated()       
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
    list.__setitem__(a, 1, Array([4, 5, 3]))
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
    list.__setitem__(a, 1, 9)
    print "a[1] = 9:"
    print a
    # [7, 9, 5]
    print "A[0, 2]:"
    print A[0, 2] #.formated()
    # [7, 9, 5]
    print "a = A[0, :, 1]:"
    a = A[0, :, 1]
    print a
    # [1 5 9]
    list.__setitem__(a, 1, 6)
    print "a[1] = 4:"
    print a
    # [1 6 9]
    print "A[0, :]:"
    print A[0, :] #.formated()
    #[[1 1 1]
    # [4 6 3]
    # [7 9 5]]
    print "A[0, :, 1:2]:"
    print A[0, :, 1:2] # .formated()
    #[[1]
    # [6]
    # [9]]
    print "A[0, 1:2, 1:2]:"
    print A[0, 1:2, 1:2] #.formated()
    #[[6]]
    print "A[0, :, 1:3]:"
    print A[0, :, 1:3] #.formated()
    #[[1 1]
    # [6 3]
    # [9 5]]
    print "A[:, :, 1:3]:"
    print A[:, :, 1:3] #.formated()
    #[[[ 1  1]
    #  [ 6  3]
    #  [ 9  5]]
    #
    # [[10 10]
    #  [40 30]
    #  [80 50]]]
    print "A[:, :, 1:2]:"
    print A[:, :, 1:2] #.formated()
    #[[[ 1]
    #  [ 6]
    #  [ 9]]
    #
    # [[10]
    #  [40]
    #  [80]]]
    print A
    print list(A.flat)
    print A.flat[7]
    print repr(A.flat[2:12])
    A.flat[7] = 8
    print A
    
    
    shape = A.shape
    ndim = A.ndim
    shapefact = [reduce(operator.mul, shape[i+1:], 1) for i in xrange(ndim)]
    print "shape: %s" % list(shape)
    print "sub sizes: %s" % shapefact
    for x in range(A.shape[0]) :
        for y in range(A.shape[1]) :
            for z in range(A.shape[2]) :
                print "------------------------------------"
                print "xyz: %s %s %s" % (x, y, z)
                flat = A.flat.toIterItem (x, y, z)
                print "flat: %s, %s" % (flat, A.flat[flat])
                coords = A.flat.toArrayCoords(flat)
                print "xyz: %s : %s" % (coords, A[coords])
    
    # should fail
    # B = Array([[1,1,1],[4,4,3],[8,5]])

if __name__ == '__main__' :
    _test()    
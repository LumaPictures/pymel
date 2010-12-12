"""
A generic n-dimensionnal Array class serving as base for arbitrary length VectorN and MatrixN classes
"""

# NOTE: modified and added some methods that are closer to how Numpy works, as some people pointed out
# they didn't want non-Python dependencies.
# For instance implemented partially the neat multi index slicing, __getitem__ and __setitem__ as well
# as and item indexing for iterators,
# Tried to make the method names match so that it will be easier to include Numpy instead if desired.
# See http://www.numpy.org/

# TODO : try a numpy import and fallback to the included class if not successful ?

# TODO : trim does preserve sub-element identity, should trimmed do a copy or deepcopy (currently deepcopy)?
# resize / reshape should be checked and set to same behavior as well

import operator, itertools, copy, inspect, sys

from arguments import isNumeric, clsname
from utilitytypes import readonly, metaReadOnlyAttr
from math import pi, exp
import math, mathutils, sys
# 1.0/sys.maxint on 64-bit systems is too precise for maya to manage...
eps = 1.0/(2**30)
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
    shape, ndim, size = None, None, None
    if isinstance(value, Array) :
        shape = value.shape
        ndim = value.ndim
        size = value.size
    elif hasattr(value, '__iter__') :
        value = Array(value)
        shape = value.shape
        ndim = value.ndim
        size = value.size
    elif isNumeric(value) :
        shape = ()
        ndim = 0
        size = 1

    if shape is None :
        raise TypeError, "can only query shape information on Array or Array component (numeric), not %s" % (clsname(value))

    return shape, ndim, size


# override math and mathutils functions to make them accept iterables and operate element-wise on iterables

def _patchfn(basefn) :
    """ Overload the given base function to have it accept iterables """
    def fn(*args, **kwargs) :
        maxarg = Array([])
        maxsize = 0
        maxtype = None
        if args :
            method_name = '__'+basefn.__name__+'__'
            if hasattr(args[0], method_name) :
                return args[0].__getattribute__(method_name)(*args[1:], **kwargs)
            else :
                args = list(args)
                ln = len(args)
                for i in xrange(ln) :
                    if hasattr(args[i], '__iter__') :
                        t = type(args[i])
                        args[i] = Array(args[i])
                        s = args[i].size
                        if s >= maxsize :
                            # for equal sizes give preferences to Array subtypes for conversion
                            if issubclass(t, Array) or s > maxsize :
                                maxarg = args[i]
                                maxsize = maxarg.size
                                maxtype = t
                if maxsize > 0 :
                    try :
                        for i in xrange(ln) :
                            maxarg, args[i] = coerce(maxarg, args[i])
                    except :
                        return NotImplemented
                    allargs = zip(*args)
                    la = len(allargs)
                    # same for keyword arguments if applicable
                    for k in kwargs :
                        ka = kwargs[k]
                        try :
                            maxarg, ka = coerce(maxarg, ka)
                            # ka = Array(ka)
                        except :
                            ka = (ka,)*la
                        # if isinstance (ka, Array) :
                        #    maxarg, ka = coerce(maxarg, ka)
                        kwargs[k] = ka
                    allkw = [dict([(k, kwargs[k][i]) for k in kwargs])  for i in range(la)]
                    res = _toCompOrArray(fn(*a, **allkw[i]) for i, a in enumerate(allargs))
                    if hasattr(res, '__iter__') :
                        try :
                            res = maxtype(res)
                        except :
                            if isinstance(maxtype, Array) :
                                res = maxtype._convert(res)
                    return res

        return basefn(*args, **kwargs)

    fn.__name__ = basefn.__name__
    if basefn.__doc__ is None :
        basedoc = "No doc string was found on base function"
    else :
        basedoc = basefn.__doc__
    fn.__doc__ = basedoc + "\nThis function has been overriden from %s.%s to work element-wise on iterables" % (basefn.__module__, basefn.__name__)
    return fn

def patchMath() :
    """ Overload various math functions to work element-wise on iterables

        >>> A = Array([[0, pi/4.0], [pi/2.0, 3.0*pi/4.0], [pi, 5.0*pi/4.0], [3.0*pi/2.0, 7.0*pi/4.0]])
        >>> print round(A,2).formated()
        [[0.0, 0.79],
         [1.57, 2.36],
         [3.14, 3.93],
         [4.71, 5.5]]
        >>> print degrees(A).formated()
        [[0.0, 45.0],
         [90.0, 135.0],
         [180.0, 225.0],
         [270.0, 315.0]]
        >>> print round(sin(A), 2).formated()
        [[0.0, 0.71],
         [1.0, 0.71],
         [0.0, -0.71],
         [-1.0, -0.71]]
    """
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

    # builtins that do not need to be manually redefined, curently only abs
    _thisModule.__setattr__('abs', _patchfn(_abs))

patchMath()

# some other overriden math or builtin functions operating on Arrays or derived classes
# NOTE : it's not very consistent that min and max accept a variable number of arguments and
# sum, prod, any, all don't? But it's the way it is with the builtins

def sum(a, start=0, axis=None):
    """ sum(a[, start=0[, axis=(axis0, axis1, ...)]]) --> numeric or Array

        Returns the sum of all the components of a, an iterable of values that support the add operator, plus start.
        If a is an Array and axis are specified will return an Array of sum(x) for x in a.axisiter(*axis)

        >>> A = Array([[1,2,3],[4,5,6]])
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 6]]
        >>> sum(A)
        21
        >>> sum(A, axis=(0, 1))
        21
        >>> sum(A, axis=0)
        Array([5, 7, 9])
        >>> sum(A, axis=1)
        Array([6, 15])
    """
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return reduce(operator.add, a.axisiter(*axis), start)
    elif hasattr(a, '__iter__') :
        return _sum(a, start)
    else :
        return a+start

def prod(a, start=1, axis=None):
    """ prod(a[, start=1[, axis=(axis0, axis1, ...)]]) --> numeric or Array

        Returns the product of all the components of a, an iterable of values that support the mul operator, times start.
        If axis are specified will return an Array of prod(x) for x in a.axisiter(*axis).

        >>> A = Array([[1,2,3],[4,5,6]])
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 6]]
        >>> prod(A)
        720
        >>> prod(A, axis=(0, 1))
        720
        >>> prod(A, axis=0)
        Array([4, 10, 18])
        >>> prod(A, axis=1)
        Array([6, 120])
    """
    if isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return reduce(operator.mul, a.axisiter(*axis), start)
    elif hasattr(a, '__iter__') :
        return reduce(operator.mul, a, start)
    else :
        return a*start

def any(a, axis=None):
    """ any(a [,axis=(axis0, axis1, ...)]) --> bool or Array of booleans

        Returns True if any of the components of iterable a evaluate to True.
        If axis are specified will return an Array of any(x) for x in a.axisiter(*axis).

        >>> A = Array([[False,True,True],[False,True,False]])
        >>> print A.formated()
        [[False, True, True],
         [False, True, False]]
        >>> any(A)
        True
        >>> any(A, axis=(0, 1))
        True
        >>> any(A, axis=0)
        Array([False, True, True])
        >>> any(A, axis=1)
        Array([True, True])
    """
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

def all(a, axis=None):
    """ all(a, [,axis=(axis0, axis1, ...)]) --> bool or Array of booleans

        Returns True if all the components of iterable a evaluate to True.
        If axis are specified will return an Array of all(x) for x in a.axisiter(*axis).

        >>> A = Array([[True,True,True],[False,True,False]])
        >>> print A.formated()
        [[True, True, True],
         [False, True, False]]
        >>> all(A)
        False
        >>> all(A, axis=(0, 1))
        False
        >>> all(A, axis=0)
        Array([False, True, False])
        >>> all(A, axis=1)
        Array([True, False])
    """
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
    """ min(iterable[, key=func[, axis=(axis0, axis1, ...)]]) --> value
        min(a, b, c, ...[, key=func[, axis=(axis0, axis1, ...)]]) --> value

        With a single iterable argument, return its smallest item.
        With two or more arguments, return the smallest argument.
        If the iterable argument is an Array instance, returns the smallest component of iterable.
        If axis are specified will return an Array of element-wise min(x) for x in a.axisiter(*axis).

        >>> A = Array([[6,3,4],[1,5,0.5]])
        >>> print A.formated()
        [[6, 3, 4],
         [1, 5, 0.5]]
        >>> min(A)
        0.5
        >>> min(A, axis=(0,1))
        0.5
        >>> min(A, axis=0)
        Array([1, 3, 0.5])
        >>> min(A, axis=1)
        Array([3, 0.5])
    """
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
    """ max(iterable[, key=func[, axis=(axis0, axis1, ...)]]) --> value
        max(a, b, c, ...[, key=func[, axis=(axis0, axis1, ...)]]) --> value

        With a single iterable argument, return its largest item.
        With two or more arguments, return the largest argument.
        If the iterable argument is an Array instance, returns the largest component of iterable.
        If axis are specified will return an Array of element-wise max(x) for x in a.axisiter(*axis).

        >>> A = Array([[6,3,4],[1,5,0.5]])
        >>> print A.formated()
        [[6, 3, 4],
         [1, 5, 0.5]]
        >>> max(A)
        6
        >>> max(A, axis=(0, 1))
        6
        >>> max(A, axis=0)
        Array([6, 5, 4])
        >>> max(A, axis=1)
        Array([6, 5])
    """
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
    """ sqlength(a[, axis=(axis0, axis1, ...)]) --> numeric or Array

        Returns square length of a, ie a*a or the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of sqlength(x) for x in a.axisiter(*axis).

        >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
        >>> print A.formated()
        [[0.5, 0.5, -0.707],
         [0.707, -0.707, 0.0]]
        >>> sqlength(A)
        1.999547
        >>> sqlength(A, axis=(0,1))
        1.999547
        >>> sqlength(A, axis=0)
        Array([0.999849, 0.999698])
        >>> sqlength(A, axis=1)
        Array([0.749849, 0.749849, 0.499849])
    """
    a = VectorN._convert(a)
    if isinstance(a, VectorN) :
        # axis not used but this catches invalid axis errors
        # only valid axis for VectorN is (0,)
        if axis is not None :
            try :
                axis = a._getaxis(axis, fill=True)
            except :
                raise ValueError, "axis 0 is the only valid axis for a VectorN, %s invalid" % (axis)
        return a.sqlength()
    elif isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return a.sqlength(*axis)
    else :
        raise TypeError, "sqlength not implemented for %s" % (clsname(a))

def length(a, axis=None):
    """ length(a[, axis=(axis0, axis1, ...)]) --> numeric or Array

        Returns length of a, sqrt(a*a) or the square root of the sum of x*x for x in a if a is an iterable of numeric values.
        If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis).

        >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
        >>> print A.formated()
        [[0.5, 0.5, -0.707],
         [0.707, -0.707, 0.0]]
        >>> length(A)
        1.4140533936170869
        >>> length(A, axis=(0,1))
        1.4140533936170869
        >>> length(A, axis=0)
        Array([0.99992449715, 0.999848988598])
        >>> length(A, axis=1)
        Array([0.865938219505, 0.865938219505, 0.707])
    """
    return sqrt(sqlength(a, axis))

def normal(a, axis=None):
    """ normal(a[, axis=(axis0, axis1, ...)]) --> Array

        Returns a normalized copy of self: self/length(self, axis).

        >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
        >>> print A.formated()
        [[0.5, 0.5, -0.707],
         [0.707, -0.707, 0.0]]
        >>> print normal(A).formated()
        [[0.353593437318, 0.353593437318, -0.499981120367],
         [0.499981120367, -0.499981120367, 0.0]]
        >>> print normal(A, axis=(0,1)).formated()
        [[0.353593437318, 0.353593437318, -0.499981120367],
         [0.499981120367, -0.499981120367, 0.0]]
        >>> print normal(A, axis=0).formated()
        [[0.5, 0.5, -0.707],
         [0.707, -0.707, 0.0]]
        >>> print normal(A, axis=1).formated()
        [[0.577408397894, 0.577408397894, -1.0],
         [0.816455474623, -0.816455474623, 0.0]]
    """
    a = VectorN._convert(a)
    if isinstance(a, VectorN) :
        # axis not used but this catches invalid axis errors
        # only valid axis for VectorN is (0,)
        if axis is not None :
            try :
                axis = a._getaxis(axis, fill=True)
            except :
                raise ValueError, "axis 0 is the only valid axis for a VectorN, %s invalid" % (axis)
        return a.normal()
    elif isinstance(a, Array) :
        axis = a._getaxis(axis, fill=True)
        return a.normal(*axis)
    else :
        raise TypeError, "normal not implemented for %s" % (clsname(a))

def dist(a, b, axis=None):
    """ dist(a, b[, axis=(axis0, axis1, ...)]) --> float or Array

        Returns the distance between a and b, ie length(b-a, axis)

        >>> A = Array([[0.5, 0.5, -0.707],[0.707, -0.707, 0.0]])
        >>> print A.formated()
        [[0.5, 0.5, -0.707],
         [0.707, -0.707, 0.0]]
        >>> B = Array([[0.51, 0.49, -0.71],[0.71, -0.70, 0.0]])
        >>> print B.formated()
        [[0.51, 0.49, -0.71],
         [0.71, -0.7, 0.0]]
        >>> length(B-A)
        0.016340134638368205
        >>> dist(A, B)
        0.016340134638368205
        >>> dist(A, B, axis=(0, 1))
        0.016340134638368205
        >>> dist(A, B, axis=0)
        Array([0.0144568322948, 0.00761577310586])
        >>> dist(A, B, axis=1)
        Array([0.0104403065089, 0.0122065556157, 0.003])
    """
    a = VectorN._convert(a)
    if isinstance(a, VectorN) :
        # axis not used but this catches invalid axis errors
        # only valid axis for VectorN is (0,)
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
        raise TypeError, "dist not implemented for %s" % (clsname(a))

# iterator classes on a specific Array axis, supporting __getitem__ and __setitem__
# in a numpy like way

class ArrayIter(object):
    """ A general purpose iterator on Arrays.

        ArrayIter allows to iterate on one or more specified axis of an Array, in any order.

        For an Array of n dimensions, iterator on p axis will yield sub-arrays of n-p dimensions,
        numerical components if n-p is 0.

        >>> A = Array(range(1, 28), shape=(3, 3, 3))
        >>> print A.formated()
        [[[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]],
        <BLANKLINE>
         [[10, 11, 12],
          [13, 14, 15],
          [16, 17, 18]],
        <BLANKLINE>
         [[19, 20, 21],
          [22, 23, 24],
          [25, 26, 27]]]
        >>> [a for a in A]
        [Array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), Array([[10, 11, 12], [13, 14, 15], [16, 17, 18]]), Array([[19, 20, 21], [22, 23, 24], [25, 26, 27]])]
        >>> [a for a in ArrayIter(A, 0)]
        [Array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), Array([[10, 11, 12], [13, 14, 15], [16, 17, 18]]), Array([[19, 20, 21], [22, 23, 24], [25, 26, 27]])]
        >>> [a for a in ArrayIter(A, 1)]
        [Array([[1, 2, 3], [10, 11, 12], [19, 20, 21]]), Array([[4, 5, 6], [13, 14, 15], [22, 23, 24]]), Array([[7, 8, 9], [16, 17, 18], [25, 26, 27]])]
        >>> [a for a in ArrayIter(A, 2)]
        [Array([[1, 4, 7], [10, 13, 16], [19, 22, 25]]), Array([[2, 5, 8], [11, 14, 17], [20, 23, 26]]), Array([[3, 6, 9], [12, 15, 18], [21, 24, 27]])]
        >>> [a for a in ArrayIter(A, 0, 1)]
        [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9]), Array([10, 11, 12]), Array([13, 14, 15]), Array([16, 17, 18]), Array([19, 20, 21]), Array([22, 23, 24]), Array([25, 26, 27])]
        >>> [a for a in ArrayIter(A, 0, 2)]
        [Array([1, 4, 7]), Array([2, 5, 8]), Array([3, 6, 9]), Array([10, 13, 16]), Array([11, 14, 17]), Array([12, 15, 18]), Array([19, 22, 25]), Array([20, 23, 26]), Array([21, 24, 27])]
        >>> [a for a in ArrayIter(A, 0, 1, 2)]
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        >>> [a for a in ArrayIter(A, 0, 2, 1)]
        [1, 4, 7, 2, 5, 8, 3, 6, 9, 10, 13, 16, 11, 14, 17, 12, 15, 18, 19, 22, 25, 20, 23, 26, 21, 24, 27]

        ArrayIter iterators support __len__, __getitem__,  __setitem__ and __delitem__ methods, it can be used
        to set whole sub-arrays in any order (for instance rows or columns in MatrixN)

        >>> A = Array(range(1, 10), shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9]]
        >>> [a for a in ArrayIter(A, 0, 1)]
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> len(ArrayIter(A, 0, 1))
        9
        >>> ArrayIter(A, 0, 1)[5:9] = [4, 3, 2, 1]
        >>> print A.formated()
        [[1, 2, 3],
         [4, 5, 4],
         [3, 2, 1]]
        >>> [a for a in ArrayIter(A, 1)]
        [Array([1, 4, 3]), Array([2, 5, 2]), Array([3, 4, 1])]
        >>> len(ArrayIter(A, 1))
        3
        >>> ArrayIter(A, 1)[1] = [7, 8, 9]
        >>> print A.formated()
        [[1, 7, 3],
         [4, 8, 4],
         [3, 9, 1]]
        >>> ArrayIter(A, 0)[1] = 0
        >>> print A.formated()
        [[1, 7, 3],
         [0, 0, 0],
         [3, 9, 1]]
    """
    def __init__(self, data, *args) :
        """ it.__init__(a[, axis1[, axis2[, ...]]])

            Inits this Array iterator on Array a, using the specified list of axis, see ArrayIter help.
        """
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
            self.itemsize = reduce(operator.mul, itemshape, 1)
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
        """ it.next() -> the next value, or raise StopIteration """
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
    def _toArrayCoords(self, item, subindex, default):
        owncoords = []
        for s in self.subsizes :
            c = item//s
            item -= c*s
            owncoords.append(c)
        coords = [default]*self.base.ndim
        # set coordinates that are defined by iterator
        for i,c in enumerate(owncoords) :
            coords[self.axis[i]] = c
        # fill in other coordinates (coords on iterated items)
        ls = len(subindex)
        s = 0
        for i,c in enumerate(coords) :
            if s >= ls :
                break
            if c == default :
                coords[i] = subindex[s]
                s += 1

        # remove useless trailing default coords, leaving a minimum of one coord
        while len(coords) > 1 and coords[-1] == default :
            del coords[-1]
        return tuple(coords)

    def toArrayCoords(self, index, default=None):
        """ it.toArrayCoords(index, default=None) --> list or tuple

            Converts an iterator item index (item of number index in the iterator) for that Array iterator to a tuple of axis coordinates for that Array,
            returns a single coordinates tuple or a list of coordinate tuples if index was a slice.
            If index is a multi-index (a tuple), the first element if index is checked against the iterator and the remaining elements are considered
            indices on the iterated sub-array (s).

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> it = ArrayIter(A, 0, 1)
            >>> it[4]
            5
            >>> it.toArrayCoords(4)
            (1, 1)
            >>> A[1, 1]
            5
            >>> it[1:4]
            Array([2, 3, 4])
            >>> it.toArrayCoords(slice(1, 4))
            [(0, 1), (0, 2), (1, 0)]

            >>> [a for a in ArrayIter(A, 1)]
            [Array([1, 4, 7]), Array([2, 5, 8]), Array([3, 6, 9])]
            >>> it = ArrayIter(A, 1)
            >>> it[0]
            Array([1, 4, 7])
            >>> it.toArrayCoords(0)
            (None, 0)
            >>> it.toArrayCoords(0, default=slice(None))
            (slice(None, None, None), 0)
            >>> A[:, 0]
            Array([1, 4, 7])
            >>> it.toArrayCoords((0, 1))
            (1, 0)
            >>> it[0, 1]
            4
            >>> A[1, 0]
            4
        """
        if hasattr(index, '__iter__') :
            index = tuple(index)
        else :
            index = (index,)
        item = index[0]
        subindex = index[1:]
        # check validity of subindex if any
        if self.itemshape :
            subindex = self.base.__class__._checkindex(index=subindex, shape=self.itemshape, default=default)

        if isinstance(item, slice) :
            return [self._toArrayCoords(f, subindex, default) for f in range(self.size)[item]]
        else :
            item = int(item)
            if item < 0 :
                item = self.size + item
            if item>=0 and item<self.size :
                return self._toArrayCoords(item, subindex, default)
            else :
                raise IndexError, "item number %s for iterator of %s items is out of bounds" % (item, self.size)

    def __getitem__(self, index) :
        """ it.__getitem__(index) <==> it[index]

            Returns a single sub-Array or component corresponding to the iterator item designated by index, or an Array of values if index is a slice.

            Note : if it is an ArrayIter built on Array a, it's equivalent to a[c] for c in it.toArrayCoords(index)

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> ArrayIter(A, 0, 1)[4]
            5
            >>> ArrayIter(A, 0, 1)[0:6]
            Array([1, 2, 3, 4, 5, 6])
            >>> [a for a in ArrayIter(A, 1)]
            [Array([1, 4, 7]), Array([2, 5, 8]), Array([3, 6, 9])]
            >>> ArrayIter(A, 1)[1]
            Array([2, 5, 8])
            >>> ArrayIter(A, 1)[1, 0]
            2
            >>> print ArrayIter(A, 1)[0:2, 0:2].formated()
            [[1, 4],
             [2, 5]]
            >>> print A.transpose()[0:2, 0:2].formated()
            [[1, 4],
             [2, 5]]
        """
        coords = self.toArrayCoords(index, default=slice(None))
        if type(coords) is list :
            return self.base.__class__._convert(self.base.__getitem__(c) for c in coords)
            # return Array(self.base.__getitem__(c) for c in coords)
        else :
            return self.base.__getitem__(coords)

    def __delitem__(self, index):
        """ it.__delitem__(index) <==> del it[index]

            Note : if it is an ArrayIter built on Array a, it's equivalent to del a[c] for c in it.toArrayCoords(index)

            Warning : Do not use __delitem__ during iteration

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> del ArrayIter(A, 0, 1)[1]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [4, 6, 7, 9]
            >>> print A.formated()
            [[4, 6],
             [7, 9]]
            >>> [a for a in ArrayIter(A, 1)]
            [Array([4, 7]), Array([6, 9])]
            >>> del ArrayIter(A, 1)[-1]
            >>> print A.formated()
            [[4],
             [7]]
        """
        coords = self.toArrayCoords(index, default=None)
        if type(coords) is list :
            for c in coords :
                self.base.__delitem__(c)
        else :
            self.base.__delitem__(coords)
        # update iterator
        self.__init__(self.base, *self.axis)

    def __setitem__(self, index, value) :
        """ it.__setitem__(index, value) <==> it[index] = value

            Returns a single sub-Array or component corresponding to the iterator item item, or an Array of values if index is a slice.

            Note : if it is an ArrayIter built on Array a, it's equivalent to a[c]=value for c in it.toArrayCoords(index) or
            a[c] = value[i] for i, c in enumerate(it.toArrayCoords(index)) if an iterable of values of suitable shapes was provided.

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> ArrayIter(A, 0, 1)[4] = 10
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 2, 3, 4, 10, 6, 7, 8, 9]
            >>> print A.formated()
            [[1, 2, 3],
             [4, 10, 6],
             [7, 8, 9]]
            >>> ArrayIter(A, 0, 1)[0:3] = 1
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 1, 1, 4, 10, 6, 7, 8, 9]
            >>> print A.formated()
            [[1, 1, 1],
             [4, 10, 6],
             [7, 8, 9]]
            >>> ArrayIter(A, 0, 1)[5:9] = [4, 3, 2, 1]
            >>> [a for a in ArrayIter(A, 0, 1)]
            [1, 1, 1, 4, 10, 4, 3, 2, 1]
            >>> print A.formated()
            [[1, 1, 1],
             [4, 10, 4],
             [3, 2, 1]]
            >>> [a for a in ArrayIter(A, 1)]
            [Array([1, 4, 3]), Array([1, 10, 2]), Array([1, 4, 1])]
            >>> ArrayIter(A, 1)[1]
            Array([1, 10, 2])
            >>> ArrayIter(A, 1)[1, 1] = 5
            >>> print A.formated()
            [[1, 1, 1],
             [4, 5, 4],
             [3, 2, 1]]
            >>> ArrayIter(A, 1)[-1] = [7, 8, 9]
            >>> print A.formated()
            [[1, 1, 7],
             [4, 5, 8],
             [3, 2, 9]]
            >>> ArrayIter(A, 0)[1] = 0
            >>> print A.formated()
            [[1, 1, 7],
             [0, 0, 0],
             [3, 2, 9]]
        """
        coords = self.toArrayCoords(index, default=slice(None))

        # print "expected item shape: %s" % list(self.itemshape)
        value = _toCompOrArray(value)
        valueshape, valuedim, valuesize = _shapeInfo(value)

        if type(coords) is list :
            if valuedim <= self.itemdim :
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
            if valuedim <= self.itemdim :
                self.base.__setitem__(coords, value)
            else :
                raise ValueError, "iterated items shape and value shape do not match"



# A generic multi dimensional Array class
# NOTE : Numpy Array class could be used instead, just implemented the bare minimum inspired from it
class Array(object):
    """ A generic n-dimensional array class using nested lists for storage.

        Arrays can be built from numeric values, iterables, nested lists or other Array instances

        >>> Array()
        Array([])
        >>> Array(2)
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

        >>> A.data
        [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
        >>> list(A)
        [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]

        Initialization from another Array does a shallow copy, not a deepcopy,
        unless the Array argument is resized / reshaped.

        >>> B = Array(A)
        >>> print B.formated()
        [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9]]
        >>> B == A
        True
        >>> B is A
        False
        >>> B[0] is A[0]
        True
        >>> C = Array([A])
        >>> print C.formated()
        [[[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]]]
        >>> C[0] is A
        True
        >>> C[0,0] is A[0]
        True

        You can pass optional shape information at creation with the keyword arguments
        shape, ndim and size. The provided data will be expanded to fit the desirable shape,
        either repeating it if it's a valid sub-array of the requested shape, or padding it with
        the Array default value (0 unless defined otherwise in an Array sub-class).

        Value will be repeated if it is a valid sub-array of the Array requested

        >>> A = Array(1, shape=(2, 2))
        >>> print A.formated()
        [[1, 1],
         [1, 1]]

        It will be padded otherwise, with the Array class default value

        >>> A = Array(1, 2, shape=(4,))
        >>> print A.formated()
        [1, 2, 0, 0]

        Or a combination of both, first pad it to a valid sub-array then repeat it

        >>> A = Array(1, 2, shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 0],
         [1, 2, 0],
         [1, 2, 0]]

        Repeat can occur in any dimension

        >>> A = Array([1, 2, 3], shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [1, 2, 3],
         [1, 2, 3]]

        TODO :
        #>>> A = Array([[1], [2], [3]], shape=(3, 3))
        #>>> print A.formated()
        #[[1, 1, 1],
        # [2, 2, 2],
        # [3, 3, 3]]

        To avoid repetition, you can use a nested list of the desired number of dimensions

        >>> A = Array([1,2,3], shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [1, 2, 3],
         [1, 2, 3]]
        >>> A = Array([[1,2,3]], shape=(3, 3))
        >>> print A.formated()
        [[1, 2, 3],
         [0, 0, 0],
         [0, 0, 0]]

        If sub-array and requested array have same number of dimensions, padding with row / columns
        will be used (useful for the MatrixN sub-class or Array)

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
        TypeError: cannot initialize a Array of shape (2, 2) from [1, 2, 3, 4, 5] of shape (5,),
        as it would truncate data or reduce the number of dimensions
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
    shape = property(_getshape, _setshape, None,
                     """ a.shape : tuple

                         Shape of the Array (number of dimensions and number of components in each dimension).

                         It can be queried, or set to change the Array's shape similarly to the reshape method.

                         >>> A = Array(range(1, 17), shape=(4, 4))
                         >>> print A.formated()
                         [[1, 2, 3, 4],
                          [5, 6, 7, 8],
                          [9, 10, 11, 12],
                          [13, 14, 15, 16]]
                         >>> S = A[0]
                         >>> A.shape=(2, 2, 4)
                         >>> print A.formated()
                         [[[1, 2, 3, 4],
                           [5, 6, 7, 8]],
                         <BLANKLINE>
                          [[9, 10, 11, 12],
                           [13, 14, 15, 16]]]
                         >>> A.shape=(4, 4)
                         >>> print A.formated()
                         [[1, 2, 3, 4],
                          [5, 6, 7, 8],
                          [9, 10, 11, 12],
                          [13, 14, 15, 16]]

                         Related : see Array.reshape method.
                     """)
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

    # for compatibility with herited api types like MVector and MMatrix
    def assign(self, value):
        """ a.assign(b) --> Array

            Assigns the value of b to a, equivalent to using the data property : a.data = b.
            Besides changing a's value, it also returns the new a to conform to Maya's api assign.

            Note: assign acts as a shallow copy

            >>> A = Array(range(1, 5), shape=(2, 2))
            >>> B = Array()
            >>> B.assign(A)
            Array([[1, 2], [3, 4]])
            >>> print B.formated()
            [[1, 2],
             [3, 4]]
            >>> B == A
            True
            >>> B is A
            False
            >>> B[0] is A[0]
            True
        """
        if type(value) == type(self) :
            self.data = value.data
        else :
            self.data = self.__class__(value).data
        return self
    def get(self):
        """ a.get() --> Tuple

            Returns a's internally stored value as a nested tuple, a raw dump of the stored numeric components.

            >>> A = Array(range(1, 5), shape=(2, 2))
            >>> print A.get()
            ((1, 2), (3, 4))
        """
        res = []
        for a in self :
            if isinstance(a, Array) :
                res.append(a.get())
            else :
                res.append(a)
        return tuple(res)

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

    @classmethod
    def _checkindex(cls, index=None, shape=None, **kwargs):
        """ Check and expand index on Array of given shape,

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
            >>> Array._checkindex((slice(2,8),-1), shape=(3, 3, 3), default=slice(None))
            (slice(2, 3, 1), 2, slice(0, 3, 1))
            >>> Array._checkindex((slice(2,8),-1), shape=(3, 3, 3), default=slice(None), expand=True)
            ([2], [2], [0, 1, 2])
        """
        # shape, ndim, size = cls._expandshape(shape=shape)
        ndim = len(shape)
        default = kwargs.get('default',None)
        expand = kwargs.get('expand',False)
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
            assert len(index)<=ndim, "Array of shape %s has %s dimensions, cannot specify %s indices" % (shape, ndim, l)
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
                        raise ValueError, "Array of shape %s has %s components on axis %s, index %s from %s is out of bounds" % (shape, shape[i], i, ind, index)
                    if expand :
                        ind = [ind]
                index[i] = ind

        return tuple(index)

    def _getindex(self, index=None, **kwargs):
        """ Check and expand index on given Array,

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
        return self.__class__._checkindex(index=index, shape=self.shape, **kwargs)

    @classmethod
    def _checkaxis(cls, axis=None, shape=None, **kwargs):
        """ Check and expand a tuple of axis on Array,

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
            >>> Array._checkaxis(axis=(1,), shape=(3, 3, 3))
            (1,)
            >>> Array._checkaxis(shape=(3, 3, 3), fill=True)
            (0, 1, 2)
            >>> Array._checkaxis(shape=(3, 3, 3), fill=True, reverse=True)
            (2, 1, 0)
            >>> Array._checkaxis(axis=(1, 3), shape=(3, 3, 3))
            Traceback (most recent call last):
                ...
            ValueError: axis 3 in axis list (1, 3) doesn't exist for an Array of shape (3, 3, 3)
            >>> Array._checkaxis(axis=(1, 1, 2), shape=(3, 3, 3))
            Traceback (most recent call last):
                ...
            ValueError: axis 1 is present more than once in axis list (1, 1, 2)

        """
        shape, ndim, size = cls._expandshape(shape=shape)
        fill = kwargs.get('fill',False)
        reverse = kwargs.get('reverse',False)
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
            try :
                if len(axis) == 1 and hasattr(axis[0], '__iter__') :
                    axis = [range(ndim)[x] for x in axis[0]]
                else :
                    axis = [range(ndim)[x] for x in axis]
            except IndexError :
                raise ValueError, "axis %s in axis list %s doesn't exist for an Array of shape %s" % (x, tuple(axis), shape)
            for x in axis :
                if axis.count(x) > 1 :
                    raise ValueError, "axis %s is present more than once in axis list %s" % (x, tuple(axis))

        return tuple(axis)


    def _getaxis(self, axis=None, **kwargs):
        """ Check and expand a tuple of axis on Array,

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
            >>> A._getaxis(axis=(1,))
            (1,)
            >>> A._getaxis(fill=True)
            (0, 1, 2)
            >>> A._getaxis(fill=True, reverse=True)
            (2, 1, 0)
            >>> A._getaxis(axis=(1, 3))
            Traceback (most recent call last):
                ...
            ValueError: axis 3 in axis list (1, 3) doesn't exist for an Array of shape (3, 3, 3)
            >>> A._getaxis(axis=(1, 1, 2))
            Traceback (most recent call last):
                ...
            ValueError: axis 1 is present more than once in axis list (1, 1, 2)

        """
        return self.__class__._checkaxis(axis=axis, shape=self.shape, **kwargs)

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

    def __new__(cls, *args, **kwargs ):
        """ cls.__new__(...) --> cls

            Creates a new Array instance without calling __init__, the created instance will be of the
            class cls (an Array subclass) default shape (if any) and set to the class default value.
            See Array, MatrixN or VectorN help for more information.
        """
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)

        cls_size = getattr(cls, 'size', None)
        # for new default size to 0 if not specified or class constant
        if size is None and not shape and (not cls_size or
                                           inspect.ismethod(cls_size) or
                                           inspect.isdatadescriptor(cls_size)):
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
        """ a.__init__(...)

            Initializes Array a from one or more iterable, nested lists or numeric values,
            See Array, MatrixN or VectorN help for more information.

            Note : __init__ from another Array acts as a shallow copy, not a deepcopy, unless
            the Array argument is resized or reshaped.
        """

        if args :
            cls = self.__class__

            data = None
            # decided not to support Arrays made of a single numeric as opposed to Numpy as it's just confusing
            if len(args) == 1 :
                args = args[0]
            # shortcut for Array subtypes
            if type(args) in (Array, MatrixN, VectorN) :
                # copy constructor
                data = super(Array, Array).__new__(Array)
                data.data = args
            elif hasattr(args, '__iter__') :
                # special cases to accommodate some herited Maya api classes
                # here classes that can convert to MMatrix and classes that don't expose
                # all components of their api base (MPoint)
                #if hasattr(args, 'asMatrix') :
                #    args = args.asMatrix()
                if isinstance(args, Array) and (args.size != len(args)) :
                    args = list(args.data)
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

                    # multiple -1 (MatrixN init for instance)
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
                            # data = Array.filled(data, shape)
                            data = cls(shape=shape).filled(data)
                        else :
                            if size >= dsize and ndim >= dndim :
                                if ndim == dndim and reduce(operator.and_, map(operator.ge, shape, dshape), True) :
                                    data = data.trimmed(shape=shape, value=self)
#                                    if self.shape == shape :
#                                        data = self.fitted(data)
#                                    else :
#                                        data = data.trimmed(shape)
                                else :
                                    try :
                                        data = cls(shape=shape).filled(data)
                                    except :
                                        data = data.resized(shape=shape, value=self)
                            else :
                                if isinstance (args, Array) :
                                    msg = "cannot cast a %s of shape %s to a %s of shape %s,\n" % (clsname(args), args.shape, cls.__name__, shape)
                                else :
                                    msg = "cannot initialize a %s of shape %s from %s of shape %s,\n" % (cls.__name__, shape, args, dshape)
                                msg += "as it would truncate data or reduce the number of dimensions"
                                raise TypeError, msg

                # check that the shape is compatible with the class, as some Array sub classes have fixed shapes / ndim
                if not cls._shapecheck(data.shape) :
                    raise TypeError, "shape of arguments %s is incompatible with class %s" % (data.shape, cls.__name__)

                # Maya 8.5 fix
                # this is a very bad workaround for a python2.4 bug.  datatypes.Vector uses a propert to emulate self.data
                # and ensure that the data is converted to api classes.  unfortunately, in python2.4 these properties are not
                # being called when self.data is set from here.  this workaround can be removed when we drop maya 8.5 support
                if hasattr(self,'_setdata'):
                    self._setdata(data.data)
                else:
                    self.data = data.data
            else :
                raise ValueError, "could not initialize a %s from the provided arguments %s" % (cls.__name__, args)

    def filled(self, value=None):
        """ a.filled([value]) --> Array

            Returns a copy (deepcopy) of a, filled with value for a's shape. If no value is given, a is filled with the class default.
            value will be expended with the class default values to the nearest matching sub array of a, then repeated.
            value can't be truncated and will raise an error if of a size superior to the size of the nearest matching sub array
            of the class, to avoid improper casts.

            Note : value is copied (deepcopy) as many times as it is inserted in a, not referenced.

            Examples:

            >>> Array(shape=(5,)).filled([0, 1, 2])
            Array([0, 1, 2, 0, 0])
            >>> Array(shape=(5,)).filled(2)
            Array([2, 2, 2, 2, 2])
            >>> print Array(shape=(2, 2)).filled(1).formated()
            [[1, 1],
             [1, 1]]
            >>> A = Array(shape=(3, 3)).filled([1, 2, 3])
            >>> print A.formated()
            [[1, 2, 3],
             [1, 2, 3],
             [1, 2, 3]]
            >>> A[0] == A[-1]
            True
            >>> A[0] is A[-1]
            False
            >>> A = Array(shape=(3, 3)).filled([1, 2])
            >>> print A.formated()
            [[1, 2, 0],
             [1, 2, 0],
             [1, 2, 0]]
            >>> Array(shape=(2, 2)).filled([1, 2, 3])
            Traceback (most recent call last):
                ...
            ValueError: value of shape (3,) cannot be fit in a Array of shape (2, 2), some data would be lost
        """
        cls = self.__class__
        shape = self.shape
        ndim = self.ndim
        size = self.size

        new = cls(shape=shape)

        if value is not None :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)

            if not shape or shape == vshape :
                new = cls(copy.deepcopy(value), shape=vshape)
            elif vdim <= ndim and vsize <= size:
                subshape = shape[ndim-vdim:]
                if subshape != vshape :
                    subsize = reduce(operator.mul, subshape, 1)
                    if subsize >= vsize :
                        value.resize(shape=subshape)
                    else :
                        raise ValueError, "value of shape %s cannot be fit in a %s of shape %s, some data would be lost" % (vshape, cls.__name__, shape)
                if vdim < ndim :
                    siter = new.subiter(vdim)
                    for i in xrange(len(siter)) :
                        siter[i] = copy.deepcopy(value)
                else :
                    new = cls(copy.deepcopy(value), shape=shape)
            else :
                raise ValueError, "fill value has more dimensions or is larger than the specified desired shape"

        return new

    def fill(self, value=None):
        """ a.fill([value])

            Fills the array in place with the given value, if no value is given a is filled with the default class values

            Note : value is copied (deepcopy) as many times as it is inserted in a, not referenced.

            Examples:

            >>> A = Array(shape=(3, 3))
            >>> print A.formated()
            [[0, 0, 0],
             [0, 0, 0],
             [0, 0, 0]]
            >>> A.fill(10)
            >>> print A.formated()
            [[10, 10, 10],
             [10, 10, 10],
             [10, 10, 10]]
            >>> A.fill()
            >>> print A.formated()
            [[0, 0, 0],
             [0, 0, 0],
             [0, 0, 0]]
            >>> A.fill([1, 2])
            >>> print A.formated()
            [[1, 2, 0],
             [1, 2, 0],
             [1, 2, 0]]
            >>> A.fill([1, 2, 3])
            >>> print A.formated()
            [[1, 2, 3],
             [1, 2, 3],
             [1, 2, 3]]
            >>> A[0] == A[-1]
            True
            >>> A[0] is A[-1]
            False
        """
        new = self.filled(value=value)
        if type(new) is type(self) :
            self.assign(new)
        else :
            raise ValueError, "new shape %s is not compatible with class %s" % (shape, clsname(self))

    def appended(self, other, axis=0):
        """ a.appended(b[, axis=0]) --> Array

            Returns the Array obtained by appending b at the end of a as iterated on axis.

            Note : returns a deepcopy of a.appends(b[, axis=0]).

            Examples:

            >>> A = Array([])
            >>> print repr(A)
            Array([])
            >>> A = A.appended(1)
            >>> print A.formated()
            [1]
            >>> A = A.appended(2)
            >>> print A.formated()
            [1, 2]
            >>> A = Array([A])
            >>> print A.formated()
            [[1, 2]]
            >>> A = A.appended([4, 5], axis=0)
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A = A.appended([3, 6], axis=1)
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A = A.appended([7, 8, 9])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array([A]).appended(A)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> B[0] == B[1]
            True
            >>> B[0] is B[1]
            False
            >>> A == B[0]
            True
            >>> A is B[0]
            False
            >>> B = B.appended([0, 0, 0], axis=1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]]]
            >>> B = B.appended([0, 0, 0, 1], axis=2)
            >>> print B.formated()
            [[[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]],
            <BLANKLINE>
             [[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]]]

        """
        cls = self.__class__
        new = Array(self.deepcopy())
        new.append(other, axis=axis)
        try :
            new = cls._convert(new)
        except :
            raise ValueError, "cannot append a %s of shape %s on axis %s of %s of shape %s" % (clsname(other), oshape, axis, clsname(self), shape)

        return new

    def append(self, other, axis=0):
        """ a.append(b[, axis=0])

            Modifies a by appending b at its end, as iterated on axis.

            Note : does not work as list append and appends a copy (deepcopy) of b, not a reference to b. However a is appended in place.

            Examples:

            >>> A = Array([])
            >>> print repr(A)
            Array([])
            >>> A.append(1)
            >>> print A.formated()
            [1]
            >>> A.append(2)
            >>> print A.formated()
            [1, 2]
            >>> A = Array([A])
            >>> print A.formated()
            [[1, 2]]
            >>> A.append([4, 5], axis=0)
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A.append([3, 6], axis=1)
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A.append([7, 8, 9])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array([A])
            >>> B.append(A)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> B[0] == B[1]
            True
            >>> B[0] is B[1]
            False
            >>> A == B[0]
            True
            >>> A is B[0]
            True
            >>> B.append([0, 0, 0], axis=1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]]]
            >>> B.append([0, 0, 0, 1], axis=2)
            >>> print B.formated()
            [[[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]],
            <BLANKLINE>
             [[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]]]

        """
        cls = self.__class__
        shape, ndim, size = _shapeInfo(self)
        other = copy.deepcopy(_toCompOrArrayInstance(other))
        oshape, odim, osize = _shapeInfo(other)

        # one axis from 0 to ndim-1
        axis = int(axis)
        if axis < 0 :
            axis += ndim
        if axis not in range(ndim) :
            raise ValueError, "cannot append on axis %s, axis does not exist for %s of shape %s" % (axis, util.clsname(self), shape)
        itself = self.axisiter(axis);
        itemshape = itself.itemshape
        itemdim = len(itemshape)
        if itemshape :
            other = Array(shape=itemshape).filled(other)
        else :
            other = Array(other)
        if size :
            if axis > 0 :
                staxis = range(axis, -1, -1)+range(axis+1, ndim)
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
            new = cls._convert(new)
        except :
            raise ValueError, "cannot append a %s of shape %s on axis %s of %s of shape %s" % (clsname(other), oshape, axis, clsname(self), shape)

        if type(new) is type(self) :
            self.assign(new)
        else :
            raise ValueError, "new appended shape %s is not compatible with class %s" % (shape, clsname(self))

    def stacked(self, other, axis=0):
        """ a.stacked(b[, axis=0]) --> Array

            Returns the Array obtained by concatenating a and b on axis.

            Note : returns a deepcopy of a.stack(b[, axis=0]).

            Examples:

            >>> A = Array([])
            >>> print repr(A)
            Array([])
            >>> A = A.stacked([1])
            >>> print A.formated()
            [1]
            >>> A = A.stacked([2])
            >>> print A.formated()
            [1, 2]
            >>> A = Array([A])
            >>> print A.formated()
            [[1, 2]]
            >>> A = A.stacked([[4, 5]], axis=0)
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A = A.stacked([[3], [6]], axis=1)
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A = A.stacked([[7, 8, 9]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array([A])
            >>> B = B.stacked(B)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> B[0] == B[1]
            True
            >>> B[0] is B[1]
            False
            >>> A == B[0]
            True
            >>> A is B[0]
            False
            >>> B = B.stacked([[[0, 0, 0]], [[0, 0, 0]]], axis=1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]]]
            >>> B = B.stacked([[[0], [0], [0], [1]], [[0], [0], [0], [1]]], axis=2)
            >>> print B.formated()
            [[[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]],
            <BLANKLINE>
             [[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]]]

        """
        cls = self.__class__
        new = Array(self.deepcopy())
        new.stack(other, axis=axis)
        return cls._convert(new)

    def stack(self, other, axis=0):
        """ a.stack(b[, axis=0]) --> Array

            Modifies a by concatenating b at its end, as iterated on axis.

            Note : stacks a copy (deepcopy) of b, not a reference to b. However a is modified in place.

            Examples:

            >>> A = Array([])
            >>> print repr(A)
            Array([])
            >>> A.stack([1])
            >>> print A.formated()
            [1]
            >>> A.stack([2])
            >>> print A.formated()
            [1, 2]
            >>> A = Array([A])
            >>> print A.formated()
            [[1, 2]]
            >>> A.stack([[4, 5]], axis=0)
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A.stack([[3], [6]], axis=1)
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A.stack([[7, 8, 9]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array([A])
            >>> B.stack(B)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> B[0] == B[1]
            True
            >>> B[0] is B[1]
            False
            >>> A == B[0]
            True
            >>> A is B[0]
            True
            >>> B.stack([[[0, 0, 0]], [[0, 0, 0]]], axis=1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]],
            <BLANKLINE>
             [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [0, 0, 0]]]
            >>> B.stack([[[0], [0], [0], [1]], [[0], [0], [0], [1]]], axis=2)
            >>> print B.formated()
            [[[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]],
            <BLANKLINE>
             [[1, 2, 3, 0],
              [4, 5, 6, 0],
              [7, 8, 9, 0],
              [0, 0, 0, 1]]]

        """
        cls = self.__class__
        shape, ndim, size = _shapeInfo(self)
        other = copy.deepcopy(_toCompOrArrayInstance(other))
        oshape, odim, osize = _shapeInfo(other)
        if odim == ndim :
            # one axis from 0 to ndim-1
            axis = int(axis)
            if axis < 0 :
                axis += ndim
            if axis not in range(ndim) :
                raise ValueError, "cannot stack on axis %s, axis does not exist for %s of shape %s" % (axis, util.clsname(self), shape)
            itself = self.axisiter(axis);
            itother = other.axisiter(axis)
            if itself.itemshape == itother.itemshape :
                if axis > 0 :
                    taxis = range(axis, -1, -1)+range(axis+1, ndim)
                    nself = self.transpose(taxis)
                    nother = other.transpose(taxis)
                    new = Array(list(nself)+list(nother)).transpose(taxis)
                else :
                    new = Array(list(self)+list(other))
                new = cls._convert(new)
                if type(new) is type(self) :
                    self.assign(new)
                else :
                    raise ValueError, "new concatenated shape %s is not compatible with class %s" % (shape, clsname(self))
            else :
                raise ValueError, "cannot stack %s of shape %s and %s of shape %s on axis %s" % (clsname(self), shape, clsname(other), oshape, axis)
        else :
            raise ValueError, "cannot stack %s and %s has they have a different number of dimensions %s and %s" % (clsname(self), clsname(other), ndim, odim)

    def hstacked(self, other) :
        """ a.hstacked(b) <==> a.stacked(b, axis=-1)

            Returns the Array obtained by concatenating a and b on last axis.
            For a 2 dimensional Array/MatrixN, it stacks a and b horizontally.

            >>> A = Array([[1, 2], [4, 5]])
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A = A.hstacked([[3], [6]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
        """
        return self.stacked(other, axis=-1)

    def hstack(self, other) :
        """ a.hstack(b) <==> a.stack(b, axis=-1)

            Modifies a by concatenating b at its end, as iterated on last axis.
            For a 2 dimensional Array/MatrixN, it stacks a and b horizontally.

            >>> A = Array([[1, 2], [4, 5]])
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
            >>> A.hstack([[3], [6]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
        """
        self.stack(other, axis=-1)

    def vstacked(self, other) :
        """ a.vstacked(b) <==> a.stacked(b, axis=0)

            Returns the Array obtained by concatenating a and b on first axis.
            For a 2 dimensional Array/MatrixN, it stacks a and b vertically.

            >>> A = Array([[1, 2], [3, 4]])
            >>> print A.formated()
            [[1, 2],
             [3, 4]]
            >>> A = A.vstacked([[5, 6]])
            >>> print A.formated()
            [[1, 2],
             [3, 4],
             [5, 6]]
        """
        return self.stacked(other, axis=0)

    def vstack(self, other) :
        """ a.vstack(b) <==> a.stack(b, axis=0)

            Modifies a by concatenating b at its end, as iterated on first axis.
            For a 2 dimensional Array/MatrixN, it stacks a and b vertically

            >>> A = Array([[1, 2], [3, 4]])
            >>> print A.formated()
            [[1, 2],
             [3, 4]]
            >>> A.vstack([[5, 6]])
            >>> print A.formated()
            [[1, 2],
             [3, 4],
             [5, 6]]
        """
        self.stack(other, axis=0)

    # aliases
    extended = vstacked
    extend = vstack

#    def repeated(self, repeat, axis):
#    # alow repeat onn multiple axis ..
#        pass
#
#    def repeat(self, repeat, axis):
#        pass

    # TODO : override and redefine these list herited methods for Arrays ?
#    def insert(self, index, other):
#        raise TypeError, "insert is not implemented for class %s" % (clsname(self))
#
#    def __reversed__(self, axis=None):
#        raise TypeError, "__reversed__ is not implemented for class %s" % (clsname(self))
#
#    def reverse(self, axis=None):
#        raise TypeError, "reverse is not implemented for class %s" % (clsname(self))
#
#    def pop(self, index):
#        raise TypeError, "pop is not implemented for class %s" % (clsname(self))
#
#    def remove(self, value):
#        raise TypeError, "remove is not implemented for class %s" % (clsname(self))
#
#    def sort(self, axis=None):
#        raise TypeError, "sort is not implemented for class %s" % (clsname(self))

    def reshaped(self, shape=None):
        """ a.reshaped(shape) --> Array

            Returns a copy the Array as reshaped according to the shape argument, without changing the Array's size
            (total number of components)

            Examples :

            >>> A = Array(range(1, 17), shape=(4, 4))
            >>> print A.formated()
            [[1, 2, 3, 4],
             [5, 6, 7, 8],
             [9, 10, 11, 12],
             [13, 14, 15, 16]]
            >>> B = A.reshaped(shape=(2, 2, 4))
            >>> print B.formated()
            [[[1, 2, 3, 4],
              [5, 6, 7, 8]],
            <BLANKLINE>
             [[9, 10, 11, 12],
              [13, 14, 15, 16]]]
            >>> A[0] == B[0, 0]
            True
            >>> A[0] is B[0, 0]
            False

        """
        ndim = None
        size = self.size
        newshape, newndim, newsize = self.__class__._expandshape(shape, ndim, size)
        if newsize != size :
            raise ValueError, "total size of new Array must be unchanged"

        return self.resized(newshape)

    def reshape(self, shape=None):
        """ a.reshaped(shape) <==> a.shape = shape

            Performs in-place reshape of array a according to the shape argument without changing the Array's size
            (total number of components).

            Note : as opposed to trim, reshape will reshuffle components and thus not preserve sub-arrays identity.

            Examples :

            >>> A = Array(range(1, 17), shape=(4, 4))
            >>> print A.formated()
            [[1, 2, 3, 4],
             [5, 6, 7, 8],
             [9, 10, 11, 12],
             [13, 14, 15, 16]]
            >>> S = A[0]
            >>> A.reshape(shape=(2, 2, 4))
            >>> print A.formated()
            [[[1, 2, 3, 4],
              [5, 6, 7, 8]],
            <BLANKLINE>
             [[9, 10, 11, 12],
              [13, 14, 15, 16]]]
            >>> S == A[0, 0]
            True
            >>> S is A[0, 0]
            False

        """
        ndim = None
        size = self.size
        newshape, newndim, newsize = self.__class__._expandshape(shape, ndim, size)
        if newsize != size :
            raise ValueError, "total size of new Array must be unchanged"

        self.resize(newshape)

    def resized(self, shape=None, value=None):
        """ a.resized([shape [, value]]) --> Array

            Returns a copy of the Array resized according to the shape argument.
            An optional value argument can be passed and will be used to fill the extra components
            of the new Array if the resize results in a size increase, otherwise the Array class default values are used.

            Examples :

            >>> A = Array(range(1, 17), shape=(4, 4))
            >>> print A.formated()
            [[1, 2, 3, 4],
             [5, 6, 7, 8],
             [9, 10, 11, 12],
             [13, 14, 15, 16]]
            >>> B = A.resized(shape=(2, 2, 4))
            >>> print B.formated()
            [[[1, 2, 3, 4],
              [5, 6, 7, 8]],
            <BLANKLINE>
             [[9, 10, 11, 12],
              [13, 14, 15, 16]]]
            >>> A[0] == B[0, 0]
            True
            >>> A[0] is B[0, 0]
            False
            >>> B = B.resized(shape=(2, 3, 3))
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 0, 0]]]
            >>> B = B.resized(shape=(4, 5), value=1)
            >>> print B.formated()
            [[1, 2, 3, 4, 5],
             [6, 7, 8, 9, 10],
             [11, 12, 13, 14, 15],
             [16, 0, 0, 1, 1]]

        """
        cls = self.__class__
        newshape, newndim, nsize = cls._expandshape(shape, None, None)

        new = None
        for c in inspect.getmro(cls) :
            if issubclass(c, Array) :
                try :
                    new = c(shape=newshape).filled(value)
                    break
                except :
                    pass

        if new is not None :
            flatIter = self.flat
            newIter = new.flat
            ln = min(len(flatIter), len(newIter))
            for i in xrange(ln) :
                newIter[i] = flatIter[i]
            # return new.deepcopy() not needed
            return new
        else :
            if value is not None :
                raise TypeError, "%s cannot be initialized to shape %s with value %s, and has no base class that can" % (clsname(self), shape, value)
            else :
                raise TypeError, "%s cannot be initialized to shape %s, and has no base class that can" % (clsname(self), shape)

    def resize(self, shape=None, value=None):
        """ a.resize([shape[, value]])

            Performs in-place resize of array a according to the shape argument.
            An optional value argument can be passed and will be used to fill the newly created components
            if the resize results in a size increase, otherwise the Array class default values are used.

            Note : as opposed to trim, resize will reshuffle components and thus not preserve sub-arrays identity.

            Examples :

            >>> A = Array(range(1, 17), shape=(4, 4))
            >>> print A.formated()
            [[1, 2, 3, 4],
             [5, 6, 7, 8],
             [9, 10, 11, 12],
             [13, 14, 15, 16]]
            >>> S = A[0]
            >>> A.resize(shape=(2, 2, 4))
            >>> print A.formated()
            [[[1, 2, 3, 4],
              [5, 6, 7, 8]],
            <BLANKLINE>
             [[9, 10, 11, 12],
              [13, 14, 15, 16]]]
            >>> S == A[0, 0]
            True
            >>> S is A[0, 0]
            False
            >>> A.resize(shape=(2, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 0, 0]]]
            >>> A.resize(shape=(4, 5), value=1)
            >>> print A.formated()
            [[1, 2, 3, 4, 5],
             [6, 7, 8, 9, 10],
             [11, 12, 13, 14, 15],
             [16, 0, 0, 1, 1]]

        """
        cls = self.__class__
        try :
            newshape, newndim, nsize = cls._expandshape(shape, None, None)
            new = cls(shape=newshape).filled(value)
        except :
            raise TypeError, "new shape %s is not compatible with class %s" % (shape, clsname(self))

        flatIter = self.flat
        newIter = new.flat
        ln = min(len(flatIter), len(newIter))
        for i in xrange(ln) :
            newIter[i] = flatIter[i]
        self.assign(new)

    def _fitloop(self, source):
        ldst = len(self)
        lsrc = len(source)
        lmin = min(ldst, lsrc)
        ndim = min(source.ndim, self.ndim)

        # copy when common shape, or recurse down
        for i in xrange(lmin) :
            if ndim == 1 or self[i].shape == source[i].shape :
                self[i] = source[i]
            else :
                self[i]._fitloop(source[i])

    def fitted(self, other):
        """ a.fitted(b) --> Array

            Returns the result of fitting the Array b in a.
            For every component of a that exists in b (there is a component of same coordinates in b),
            replace it with the value of the corresponding component in b.
            Both Arrays a and b must have same number of dimensions.

            Note : returns a copy (deepcopy) of a.fit(b)

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array(shape=(4, 3))
            >>> print B.formated()
            [[0, 0, 0],
             [0, 0, 0],
             [0, 0, 0],
             [0, 0, 0]]
            >>> C = B.fitted(A)
            >>> print C.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [0, 0, 0]]
            >>> C[0] == A[0]
            True
            >>> C[0] is A[0]
            False
            >>> C[-1] == B[-1]
            True
            >>> C[-1] is B[-1]
            False
            >>> B = Array(shape=(4, 4)).fitted(A)
            >>> print B.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 0]]
            >>> B = Array(shape=(2, 2)).fitted(A)
            >>> print B.formated()
            [[1, 2],
             [4, 5]]
        """
        new = self.deepcopy()
        new.fit(other)
        return new

    def fit(self, other):
        """ a.fit(b)

            Fits the Array b in a.
            For every component of a that exists in b (there is a component of same coordinates in b),
            replace it with the value of the corresponding component in b.
            Both Arrays a and b must have same number of dimensions.

            Note : copies (deepcopy) of b sub-arrays are fit in a, not references, but modification of a is done in-place.

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = Array(shape=(4, 3))
            >>> print B.formated()
            [[0, 0, 0],
             [0, 0, 0],
             [0, 0, 0],
             [0, 0, 0]]
            >>> S = B[-1]
            >>> B.fit(A)
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [0, 0, 0]]
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            False
            >>> S == B[-1]
            True
            >>> S is B[-1]
            True
            >>> B = Array(shape=(4, 4))
            >>> B.fit(A)
            >>> print B.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 0]]
            >>> B = Array(shape=(2, 2))
            >>> B.fit(A)
            >>> print B.formated()
            [[1, 2],
             [4, 5]]
        """
        other = Array(other).deepcopy()
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
            A value of -1 or None for a shape dimension size will leave it unchanged.
            An optional value argument can be passed and will be used to fill the newly created
            components if the trimmed results in a size increase, otherwise the class default values
            will be used to fill new components

            Note : returns a copy (deepcopy) of a.trim([shape [, value]])

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B = A.trimmed(shape=(4, 3))
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [0, 0, 0]]
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            False
            >>> B = A.trimmed(shape=(4, 4))
            >>> print B.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 0]]
            >>> B = A.trimmed(shape=(2, 2))
            >>> print B.formated()
            [[1, 2],
             [4, 5]]
        """
        cls = self.__class__
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

        # new will be a copy
        new = Array(shape=newshape).filled(value)
        new._fitloop(self)
        new = cls._convert(new)

        return new.deepcopy()

    def trim(self, shape=None, value=None):
        """ a.trim(shape)
            Performs in-place trimming of array a to given shape.
            An optional value argument can be passed and will be used to fill
            the newly created components if the resize results in a size increase.

            Note : a is modified in-place

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> S = A[0]
            >>> A.trim(shape=(4, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [0, 0, 0]]
            >>> S == A[0]
            True
            >>> S is A[0]
            True
            >>> A.trim(shape=(4, 4))
            >>> print A.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 0]]
            >>> A.trim(shape=(2, 2))
            >>> print A.formated()
            [[1, 2],
             [4, 5]]
        """
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
            source = self.__class__(shape=newshape).filled(value)
            self._trimloop(source)
        else :
            raise TypeError, "new shape %s is not compatible with class %s" % (shape, clsname(self))

    def __reduce__(self):
        """ __reduce__ is defined to allow pickling of Arrays """
        return (self.__class__, self.__getnewargs__())

    def __getnewargs__(self):
        return (tuple(self),)

    def copy(self):
        """ a.copy() <==> copy.copy(a)

            Returns a shallow copy of a

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> B = A.copy()
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print B == A
            True
            >>> print B is A
            False
            >>> print B[0] == A[0]
            True
            >>> print B[0] is A[0]
            True
        """
        return copy.copy(self)

    def deepcopy(self):
        """ a.deepcopy() <==> copy.deepcopy(a)

            Returns a deep copy of a

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> B = A.deepcopy()
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print B == A
            True
            >>> print B is A
            False
            >>> print B[0] == A[0]
            True
            >>> print B[0] is A[0]
            False
        """
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
        """ a.formated() --> str

            Returns a string representing a formated output of Array a

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
        """
        return self._formatloop()[1]

    # wrap of list-like access methods
    def __len__(self):
        """ a.__len__() <==> len(a)

            Length of the first dimension of the array, ie len of the array considered as the top level list,
            thus len(a) == a.shape[0].

            >>> Array(shape=(3, 2)).__len__()
            3
        """
        return self.apicls.__len__(self.data)

    @staticmethod
    def _extract(x, index) :
        if isinstance(x, Array) :
            res = x.apicls.__getitem__(x.data, index)
        else :
            res = [Array._extract(a, index) for a in x]
        return res

    def __getitem__(self, index):
        """ a.__getitem__(index) <==> a[index]

            Get Array element from either a single (integer) or multiple (tuple) indices, supports slices.

            Note : __getitem__ returns reference that can be modified unless the sub-array had to be reconstructed.

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print repr(A[0])
            Array([1, 2, 3])
            >>> print repr(A[-1])
            Array([7, 8, 9])
            >>> print repr(A[0, 0])
            1
            >>> print repr(A[-1, -1])
            9

            Multiple indices and slices are supported :

            >>> B = A[0:2, 0:2]
            >>> print B.formated()
            [[1, 2],
             [4, 5]]

            When sub-arrays are not broken / rebuilt by requested indexing, a reference is returned :

            >>> B = A[0:2]
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            True

            Missing indices are equivalent to slice(None), noted ':', but as with list, a[:] returns
            a copy of a, not a reference to a.

            >>> B = A[0:2, :]
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            False

            When sub-arrays are rebuilt, result is a copy.

            >>> B = A[:, 0:2]
            >>> print B.formated()
            [[1, 2],
             [4, 5],
             [7, 8]]
            >>> print repr(B[:,0])
            Array([1, 4, 7])
            >>> B[:,0] == A[:, 0]
            True
            >>> B[:,0] is A[:, 0]
            False

            Use __setindex__ to change the value of an indexed element in that case

            >>> A[:, 0:2] += 10
            >>> print A.formated()
            [[11, 12, 3],
             [14, 15, 6],
             [17, 18, 9]]
        """
        # TODO : Numpy like support for indices that are Arrays ?
        if not hasattr(index, '__iter__') :
            index = [index]
        else :
            index = list(index)
        if len(index) > self.ndim :
            raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), self.ndim)

        value = reduce(lambda x, y: Array._extract(x, y), index, self)
        # print "value and id", value, id(value)
        value = self.__class__._toCompOrConvert(value)
        # value = _toCompOrArray(value)
        # print "value and id", value, id(value)
        return value

    def __getslice__(self, start, end):
        """ Deprecated and __getitem__ should accept slices anyway """
        return self.__getitem__(slice(start, end))

    def _inject(self, index, value) :
        indices = range(self.shape[0])[index[0]]
        if not hasattr(indices, '__iter__') :
            indices = [indices]
            value = [value]
        ni = len(indices)
        if len(index) == 1 :
            # single dimension index, assign to storage
            for i in xrange(ni) :
                self.apicls.__setitem__(self.data, indices[i], value[i])
        else :
            # multi dimension index
            nextindex = index[1:]
            for i in xrange(ni) :
                self[indices[i]]._inject(nextindex, value[i])

    def __setitem__(self, index, value):
        """ a.__setitem__(index, value) <==> a[index] = value

            Set Array element from either a single (integer) or multiple (tuple) indices, supports slices.

            Note : if value is not reshaped / resized, it's a reference to value that is set at the indexed element,
            use an explicit deepcopy

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]

            If value doesn't have to be rebuilt, the indexed elements will hold a reference to value, otherwise a copy

            >>> S = Array([0, 0, 0])
            >>> A[0] = S
            >>> print A.formated()
            [[0, 0, 0],
             [4, 5, 6],
             [7, 8, 9]]
            >>> A[0] == S
            True
            >>> A[0] is S
            True
            >>> A[:, 2] = S
            >>> print A.formated()
            [[0, 0, 0],
             [4, 5, 0],
             [7, 8, 0]]
            >>> A[:, 2] == S
            True
            >>> A[:, 2] is S
            False

            Multiple indices and slices are supported :

            >>> A[0] = [2, 4, 6]
            >>> print A.formated()
            [[2, 4, 6],
             [4, 5, 0],
             [7, 8, 0]]
            >>> A[1, 1] = 10
            >>> print A.formated()
            [[2, 4, 6],
             [4, 10, 0],
             [7, 8, 0]]
            >>> A[:, -1] = [7, 8, 9]
            >>> print A.formated()
            [[2, 4, 7],
             [4, 10, 8],
             [7, 8, 9]]
            >>> A[:, 0:2] += 10
            >>> print A.formated()
            [[12, 14, 7],
             [14, 20, 8],
             [17, 18, 9]]

            Value is expanded / repeated as necessary to fit the indexed sub-array

            >>> A[0:2, 0:2] = 1
            >>> print A.formated()
            [[1, 1, 7],
             [1, 1, 8],
             [17, 18, 9]]
            >>> A[1:3, :] = [1, 2]
            >>> print A.formated()
            [[1, 1, 7],
             [1, 2, 0],
             [1, 2, 0]]
            >>> A[0:2, 1:3] = [1, 2]
            >>> print A.formated()
            [[1, 1, 2],
             [1, 1, 2],
             [1, 2, 0]]
            >>> A[0:2, 1:3] = [[1], [2]]
            >>> print A.formated()
            [[1, 1, 0],
             [1, 2, 0],
             [1, 2, 0]]

            It cannot be truncated however

            >>> A[0] = [1, 2, 3, 4]
            Traceback (most recent call last):
                ...
            ValueError: shape mismatch between value(s) and Array components or sub Arrays designated by the indexing
        """
        # NUMPY differences: expands by repeating last value
        """
            >>> A[0:2, 1:3] = [[1], [2]]
            >>> print A.formated()
            [[1, 1, 1],
             [1, 2, 2],
             [1, 2, 0]]
        """

        if not hasattr(index, '__iter__') :
            index = [index]
        else :
            index = list(index)
        if len(index) > self.ndim :
            raise ValueError, "%s coordinates provided for an Array of dimension %s" % (len(index), self.ndim)
        value = _toCompOrArray(value)
        vshape, vdim, vsize = _shapeInfo(value)
        subexpected = self.__getitem__(index)
        subshape, subdim, subsize = _shapeInfo(subexpected)
        # if we don't except a single numeric value
        if vshape != subshape :
            try :
                value = Array(value, shape=subshape)
            except :
                raise ValueError, "shape mismatch between value(s) and Array components or sub Arrays designated by the indexing"
        self._inject(index, value)

    def __setslice__(self, start, end, value):
        """ Deprecated and __setitem__ should accept slices anyway """
        self.__setitem__(slice(start, end), value)

    def _delete(self, index) :
        ls = len(self)
        li = len(index)
        if ls and li :
            next = li > 1
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    self.apicls.__delitem__(self.data, i)
                    # self._cacheshape()
                elif next :
                    self[i]._delete(index[1:])

    def __delitem__(self, index) :
        """ a.__delitem__(index) <==> del a[index]

            Delete elements that match index from the Array.

            Note : as opposed to a.strip(index), do not collapse dimensions of the Array
            that end up with only one sub-array.

            >>> A = Array(xrange(1, 28), shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 17, 18]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> A.shape
            (3, 3, 3)
            >>> S = A[0]
            >>> del A[1]
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> A.shape
            (2, 3, 3)
            >>> S == A[0]
            True
            >>> S is A[0]
            True
            >>> del A[-1]
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> A.shape
            (1, 3, 3)
            >>> del A[None, None, 1:3]
            >>> print A.formated()
            [[[1],
              [4],
              [7]]]
            >>> A.shape
            (1, 3, 1)
            >>> del A[None, 1:3]
            >>> print A.formated()
            [[[1]]]
            >>> A.shape
            (1, 1, 1)
            >>> del A[-1]
            >>> print A.formated()
            []
            >>> A.shape
            (0,)
        """
        # TODO : how to interpret slices (get rid of the "None" thing ?)
        #
        # >>> A = Array(xrange(1, 10), shape=(3, 3))
        # >>> print A.formated()
        # [[1, 2, 3],
        #  [4, 5, 6],
        #  [7, 8, 9]]
        # >>> del A[:, -1]
        # >>> print A.formated()
        # [[1, 2],
        #  [4, 5],
        #  [7, 8]]

        index = self._getindex(index, default=None, expand=True)
        # TODO : check what shape it would yield first
        if index :
            self._delete(index)
            self._cacheshape()
            if not self.__class__._shapecheck(self.shape) :
                raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    def __delslice__(self, start):
        """ deprecated and __setitem__ should accept slices anyway """
        self.__delitem__(slice(start, end))

    def deleted(self, *args):
        """ a.deleted(index) --> Array

            Returns a copy (deepcopy) of a with the elements designated by index deleted,
            as in a.__delitem__(index).

            Note : as opposed to a.stripped(index), do not collapse dimensions of the Array
            that end up with only one sub-array.

            >>> A = Array(xrange(1, 28), shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 17, 18]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> A.shape
            (3, 3, 3)
            >>> B = A.deleted(1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> B.shape
            (2, 3, 3)
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            False
            >>> B = B.deleted(-1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]]
            >>> B.shape
            (1, 3, 3)
            >>> B = B.deleted(None, None, slice(1, 3))
            >>> print B.formated()
            [[[1],
              [4],
              [7]]]
            >>> B.shape
            (1, 3, 1)
            >>> B = B.deleted((None, slice(1, 3)))
            >>> print B.formated()
            [[[1]]]
            >>> B.shape
            (1, 1, 1)
            >>> B = B.deleted(-1)
            >>> print B.formated()
            []
            >>> B.shape
            (0,)
        """
        cls = self.__class__
        index = self._getindex(args, default=None, expand=True)
        if index :
            new = Array(self.deepcopy())
            new._delete(index)
            new._cacheshape()
            return cls._convert(new)

    def _strip(self, index) :
        ls = len(self)
        li = len(index)
        if ls and li :
            next = li > 1
            for i in xrange(ls-1, -1, -1) :
                if i in index[0] :
                    self.apicls.__delitem__(self.data, i)
                    # self._cacheshape()
                elif next :
                    self[i]._strip(index[1:])
            if len(self) == 1 and hasattr(self[0], '__iter__') :
                self.assign(self[0])

    def strip(self, *args) :
        """ a.strip(index)

            Strip the elements designated by index from a.

            Note : as opposed to a.__delete__(index), will collapse dimensions of the Array
            that end up with only one sub-array.

            >>> A = Array(xrange(1, 28), shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 17, 18]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> A.shape
            (3, 3, 3)
            >>> S = A[0]
            >>> A.strip(1)
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> S == A[0]
            True
            >>> S is A[0]
            True
            >>> A.strip(-1)
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> S == A
            True
            >>> S is A
            False
            >>> S[0] == A[0]
            True
            >>> S[0] is A[0]
            True
            >>> A.strip(None, slice(1,3))
            >>> print A.formated()
            [[1],
             [4],
             [7]]
            >>> A.strip(-1)
            >>> print A.formated()
            [[1],
             [4]]
            >>> A.strip(-1)
            >>> print A.formated()
            [1]
            >>> A.strip(-1)
            >>> print A.formated()
            []
        """
        index = self._getindex(args, default=None, expand=True)
        # TODO : check what shape it would yield first
        if index :
            self._strip(index)
            self._cacheshape()
            if not self.__class__._shapecheck(self.shape) :
                raise TypeError, "stripping %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    def stripped(self, *args):
        """ a.stripped(index) --> Array

            Returns a copy (deepcopy) of a with the elements designated by index stripped,
            as in a.strip(index)

            Note : as opposed to a.deleted(index), will collapse dimensions of the Array
            that end up with only one sub-array.

            >>> A = Array(xrange(1, 28), shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 17, 18]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> A.shape
            (3, 3, 3)
            >>> B = A.stripped(1)
            >>> print B.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> B[0] == A[0]
            True
            >>> B[0] is A[0]
            False
            >>> B = B.stripped(-1)
            >>> print B.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> B == A[0]
            True
            >>> B is A[0]
            False
            >>> B[0] == A[0, 0]
            True
            >>> B[0] is A[0,0]
            False
            >>> B = B.stripped(None, slice(1,3))
            >>> print B.formated()
            [[1],
             [4],
             [7]]
            >>> B = B.stripped(-1)
            >>> print B.formated()
            [[1],
             [4]]
            >>> B = B.stripped(-1)
            >>> print B.formated()
            [1]
            >>> B = B.stripped(-1)
            >>> print B.formated()
            []
        """
        cls = self.__class__
        index = self._getindex(args, default=None, expand=True)
        if index :
            new = self.deepcopy()
            new._strip(index)
            new._cacheshape()
            return cls._convert(new)

    def __iter__(self, *args, **kwargs) :
        """ a.__iter__(*args, **kwargs) <==> iter(a, *args, **kwargs)

            Default Array storage class iterator, operates on first axis only

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in A]
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
        """
        return self.apicls.__iter__(self.data, *args, **kwargs)

    def axisiter(self, *args) :
        """ a.axisiter([axis1[, axis2[, ...]]]) --> ArrayIter

            Returns an iterator using a specific axis or list of ordered axis.
            It is equivalent to transposing the Array using these ordered axis and iterating
            on the new Array for the remaining sub array dimension

            Note : ArrayIter ierators support __len__, __getitem__ and __setitem__

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in A]
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
            >>> [a for a in A.axisiter(0)]
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
            >>> [a for a in A.axisiter(1)]
            [Array([1, 4, 7]), Array([2, 5, 8]), Array([3, 6, 9])]
            >>> [a for a in A.axisiter(0,1)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> [a for a in A.axisiter(1,0)]
            [1, 4, 7, 2, 5, 8, 3, 6, 9]
        """
        return ArrayIter(self, *args)

    def subiter(self, dim=None) :
        """ a.subiter([dim=None]) --> ArrayIter

            Returns an iterator on all sub Arrays for a specific sub Array number of dimension.

            a.subiter(0) is equivalent to a.flat: lista sub-arrays of dimension 0, ie components
            a.subiter() is equivalent to self.subiter(self.ndim-1) and thus to self.__iter__()

            Note : ArrayIter iterators support __len__, __getitem__ and __setitem__

            >>> A = Array(range(1, 28), shape=(3, 3, 3))
            >>> print A.formated()
            [[[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]],
            <BLANKLINE>
             [[10, 11, 12],
              [13, 14, 15],
              [16, 17, 18]],
            <BLANKLINE>
             [[19, 20, 21],
              [22, 23, 24],
              [25, 26, 27]]]
            >>> [a for a in A.subiter(0)]
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
            >>> [a for a in A.subiter(1)]
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9]), Array([10, 11, 12]), Array([13, 14, 15]), Array([16, 17, 18]), Array([19, 20, 21]), Array([22, 23, 24]), Array([25, 26, 27])]
            >>> [a for a in A.subiter(2)]
            [Array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), Array([[10, 11, 12], [13, 14, 15], [16, 17, 18]]), Array([[19, 20, 21], [22, 23, 24], [25, 26, 27]])]
            >>> [a for a in A.subiter(3)]
            Traceback (most recent call last):
                ...
            ValueError: can only iterate for a sub-dimension inferior to Array's number of dimensions 3
        """
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
        """ a.flat --> ArrayIter

            Flat iterator on all components of the Array

            Note : ArrayIter iterators support __len__, __getitem__ and __setitem__

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> [a for a in A]
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
            >>> [a for a in A.flat]
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> A.flat[5:10] = [4, 3, 2, 1]
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 4],
             [3, 2, 1]]
        """
        return self.subiter(0)

    def tolist(self):
        """ a.tolist() --> list

            Returns that Array converted to a nested list

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print repr(A)
            Array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            >>> print repr(list(A))
            [Array([1, 2, 3]), Array([4, 5, 6]), Array([7, 8, 9])]
            >>> print repr(A.tolist())
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        """
        l = []
        for sub in self :
            if isinstance(sub, Array) :
                l.append(sub.tolist())
            else :
                l.append(sub)
        return l

    def ravel(self):
        """ a.ravel() <==> Array(a.flat)

            Returns that Array flattened as to a one-dimensional array.

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print repr(A.ravel())
            Array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        """
        return Array(self.flat)

    def __contains__(self, value):
        """ a.__contains__(b) <==> b in a

            Returns True if at least one of the sub-Arrays of a (down to individual components) is equal to b,
            False otherwise

            >>> A = Array(list(range(1, 6))+list(range(4, 0, -1)), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 4],
             [3, 2, 1]]
            >>> 5 in A
            True
            >>> [1, 2, 3] in A
            True
            >>> [1, 2] in A
            False
            >>> Array([[1, 2], [4, 5]]) in A
            False

            This behavior is unlike numpy arrays (where it would return True), but like builtin list

            >>> A in A
            False

            TODO :
            #>>> [1, 4, 3] in A
            #True
            #>>> [[1], [4], [3]] in A
            #True
        """
        shape = self.shape
        ndim = self.ndim
        if shape != () :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim < ndim and self.shape[ndim-vdim:] == vshape[:] :
                for sub in self.subiter(vdim) :
                    if sub == value :
                        return True
        return False

    def count(self, value):
        """ a.count(b) --> int

            Returns the number of occurrences of b in a.

            >>> A = Array(list(range(1, 6))+list(range(4, 0, -1)), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 4],
             [3, 2, 1]]
            >>> A.count(5)
            1
            >>> A.count(4)
            2
            >>> A.count([1, 2, 3])
            1
            >>> A.count([1, 2])
            0
        """

        # TODO : like numpy count for column occurrences ?
        # >>> A.count([1, 4, 3])
        # 1
        # >>> A.count([[1], [4], [3]])
        # 1
        # >>> A.count(A)
        # 0


        res = 0
        shape = self.shape
        ndim = self.ndim
        if shape != () :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim < ndim and self.shape[ndim-vdim:] == vshape[:] :
                for sub in self.subiter(vdim) :
                    if sub == value :
                        res += 1
        return res

    def index(self, value) :
        """ a.index(b) --> int or tuple

            Returns the index of the first occurrence of b in a.

            >>> A = Array(list(range(1, 6))+list(range(4, 0, -1)), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 4],
             [3, 2, 1]]
            >>> A.index(5)
            (1, 1)
            >>> A.index(4)
            (1, 0)
            >>> A.index([1, 2, 3])
            (0,)
            >>> A.index([1, 2])
            Traceback (most recent call last):
                ...
            ValueError: Array.index(x): x not in Array
        """

        # TODO : like numpy also search for column occurrences ?
        # >>> A.index([1, 4, 3])
        # 1
        # >>> A.index([[1], [4], [3]])
        # 1
        # >>> A.index(A)
        # Traceback (most recent call last):
        #     ...
        # ValueError: Array.index(x): x not in Array

        shape = self.shape
        ndim = self.ndim
        if shape != () :
            value = _toCompOrArray(value)
            vshape, vdim, vsize = _shapeInfo(value)
            if vdim < ndim and self.shape[ndim-vdim:] == vshape[:] :
                siter = self.subiter(vdim)
                for i, sub in enumerate(siter) :
                    if sub == value :
                        return siter.toArrayCoords(i)
        raise ValueError, "%s.index(x): x not in %s" % (clsname(self), clsname(self))

    # arithmetics and operators

    def __coerce__(self, other):
        """ coerce(a, b) -> (a1, b1)

            Return a tuple consisting of the two numeric arguments converted to
            a common type and shape, using the same rules as used by arithmetic operations.
            If coercion is not possible, return NotImplemented.

            b is cast to Array when possible

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> nA, nB = coerce(A, 1)
            >>> print nA.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print nB.formated()
            [[1, 1, 1],
             [1, 1, 1],
             [1, 1, 1]]
            >>> nA, nB = coerce(A, [1, 2, 3])
            >>> print nA.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print nB.formated()
            [[1, 2, 3],
             [1, 2, 3],
             [1, 2, 3]]

            Arguments can only be expanded, not truncated to avoid silent loss of data.

            >>> A = Array(range(4), shape=(2, 2))
            >>> nA, nB = coerce(A, [1, 2, 3, 4, 5])
            Traceback (most recent call last):
                ...
            TypeError: number coercion failed

            TODO : would be more explicit to get :
            TypeError: Array of shape (2, 2) and Array of shape (5,) cannot be converted to an common Array instance of same shape

            Arrays of dissimular shape are cast to same shape when possible, smallest size is cast to largest

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> B = Array(range(1, 5), shape=(2, 2))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print B.formated()
            [[1, 2],
             [3, 4]]
            >>> nA, nB = coerce(A, B)
            >>> print nA.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print nB.formated()
            [[1, 2, 0],
             [3, 4, 0],
             [0, 0, 0]]

            When coerce(x, y) is not doable, it defers to coerce(y, x)

            >>> nB, nA = coerce(B, A)
            >>> print nA.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print nB.formated()
            [[1, 2, 0],
             [3, 4, 0],
             [0, 0, 0]]

            And does not raise an excepetion like :
                Traceback (most recent call last):
                    ...
                TypeError: Array of shape (2, 2) and Array of shape (3, 3) cannot be converted to an common Array instance of same shape
            as it could be expected without this __coerce__ mechanism.

            When mixing Array derived types, result are cast to the first base class of either argument that accepts both shapes,
            ie 'deepest' derived class is tried first, MatrixN before Array, etc.

            >>> A = Array(range(1, 10), shape=(3, 3))
            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> nA, nM = coerce(A, M)
            >>> print repr(nA)
            MatrixN([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            >>> print repr(nM)
            MatrixN([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            >>> nM, nA = coerce(M, A)
            >>> print repr(nA)
            MatrixN([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            >>> print repr(nM)
            MatrixN([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

            This allows to implement a common behavior for element-wise arithmetics between Arrays of same
            or dissimilar shapes, Arrays and types derived from Arrays, Arrays and numerics or iterables of numerics.

            All operators on Arrays that take 2 operands and work element-wise follow the following rules :

            Operands are cast to Array when possible

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (A).formated()
            [[0, 1],
             [2, 3]]
            >>> print (A+1).formated()
            [[1, 2],
             [3, 4]]
            >>> print (A+[1, 2]).formated()
            [[1, 3],
             [3, 5]]

            Operands can only be expanded, not truncated to avoid silent loss of data.

            >>> print (A+[1, 2, 3, 4, 5]).formated()
            Traceback (most recent call last):
                ...
            TypeError: unsupported operand type(s) for +: 'Array' and 'list'

            TODO : it would be more explicit to get more specific error messages, like :
                TypeError: Array of shape (2, 2) and Array of shape (5,) cannot be converted to an common Array instance of same shape

            Arrays of dissimilar shape are cast to same shape by Array.__coerce__ if possible.

            >>> A = Array(range(9), shape=(3, 3))
            >>> B = Array(range(10, 50, 10), shape=(2, 2))
            >>> print (A+B).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+B)
            Array

            As Array.__coerce__ cannot truncate data, it will defer to the other operand's __coerce__ if it exists,
            then to its 'right operation' (here __radd__) method if it exists and is defined for an Array left operand.

            >>> A = Array(range(10, 50, 10), shape=(2, 2))
            >>> B = Array(range(9), shape=(3, 3))
            >>> print (A+B).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+B)
            Array

            Result is cast to the first applicable Array herited type of either operand

            >>> A = Array(range(9), shape=(3, 3))
            >>> M = MatrixN(range(10, 50, 10), shape=(2, 2))
            >>> print (A+M).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+M)
            MatrixN
            >>> print (M+A).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(M+A)
            MatrixN

            >>> A = Array(range(10, 50, 10), shape=(2, 2))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> print (A+M).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+M)
            MatrixN
            >>> print (M+A).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(M+A)
            MatrixN

            Here result is cast to Array as a MatrixN can't have 3 dimensions

            >>> A = Array(range(10, 190, 10), shape=(2, 3, 3))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> print (A+M).formated()
            [[[10, 21, 32],
              [43, 54, 65],
              [76, 87, 98]],
            <BLANKLINE>
             [[100, 111, 122],
              [133, 144, 155],
              [166, 177, 188]]]
            >>> print clsname(A+M)
            Array
            >>> print (M+A).formated()
            [[[10, 21, 32],
              [43, 54, 65],
              [76, 87, 98]],
            <BLANKLINE>
             [[100, 111, 122],
              [133, 144, 155],
              [166, 177, 188]]]
            >>> print clsname(M+A)
            Array

            There are cases where no type coercion is possible, as it would truncate data or reduce number
            of dimensions in either way, use an explicit conversion (trim, size, etc.) in that case :

            >>> A = Array(range(8), shape=(2, 2, 2))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> print (A+M).formated()
            Traceback (most recent call last):
                ...
            TypeError: unsupported operand type(s) for +: 'Array' and 'MatrixN'

            TODO : return some more explicit messages in these cases

        """

        # print "coerce Array"
        if type(other) == type(self) :
            if len(other) == len(self) and other.shape == self.shape :
                return self, other
        else :
            try :
                other = _toCompOrArrayInstance(other)
            except :
                # returning NotImplemented defers to other.__coerce__(self) if applicable
                # raise TypeError, "%s is not convertible to an Array instance" % (clsname(other))
                return NotImplemented

        ocls = other.__class__
        scls = self.__class__
        # convert to most specific class if possible (MatrixN before Array, etc)
        if issubclass(ocls, scls) :
            mro = inspect.getmro(ocls)
        else :
            mro = inspect.getmro(scls)
        nself = None
        nother = None
        # always try to conform to shape of self, if it fails, will defer to coerce(other, self) anyway
        for c in mro :
            if issubclass(c, Array) :
                try :
                    nself = c(self)
                    nother = c(other, shape=nself.shape)
                    assert len(nself) == len(nother) and nself.shape == nother.shape
                    break;
                except :
                    pass

        if nself is not None and nother is not None :
            return nself, nother
        else :
            # raise TypeError, "%s of shape %s cannot be cast to a %s of shape %s or any common Array derived class of that shape" % (clsname(other), other.shape, clsname(self), self.shape)
            # returning NotImplemented instead of raising an exception defers to other.__coerce__(self) if applicable
            # TOTO : some more explicit error messages ?
            return NotImplemented

    # common operators

    def __eq__(self, other):
        """ a.__equ__(b) <==> a == b

            Equivalence operator, will only work for exact same type of a and b, check isEquivalent method to have it
            convert a and b to a common type (if possible).

            >>> Array(range(4), shape=(4)) == Array(range(4), shape=(1, 4))
            False
            >>> Array(range(4), shape=(2, 2)) == Array(range(4), shape=(2, 2))
            True
            >>> Array(range(4), shape=(2, 2)) == MatrixN(range(4), shape=(2, 2))
            False
        """
        if type(self) != type(other) :
            return False
        if self.shape != other.shape :
            return False
        return reduce(lambda x, y : x and y[0]==y[1], itertools.izip(self, other), True )
    def __ne__(self, other):
        """ a.__ne__(b) <==> a != b

            a.__ne__(b) returns not a.__equ__(b).

            >>> Array(range(4), shape=(4)) != Array(range(4), shape=(1, 4))
            True
            >>> Array(range(4), shape=(2, 2)) != Array(range(4), shape=(2, 2))
            False
            >>> Array(range(4), shape=(2, 2)) != MatrixN(range(4), shape=(2, 2))
            True
        """
        return (not self.__eq__(other))
    __neq__ = __ne__
    def __abs__(self):
        """ a.__abs__() <==> abs(a)

            Element-wise absolute value of a.

            >>> A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]])
            >>> print abs(A).formated()
            [[2.2360679775, 3.60555127546],
             [6.40312423743, 9.21954445729]]
            >>> A = Array(-1, 2, -3)
            >>> print repr(abs(A))
            Array([1, 2, 3])
        """
        return self.__class__(abs(x) for x in self)
    def __invert__(self):
        """ a.__invert__() <==> ~a

            Element-wise invert of a, as with '~', operator 'invert'

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (~A).formated()
            [[-1, -2],
             [-3, -4]]
        """
        return self.__class__(operator.invert(x) for x in self)
    def __round__(self, ndigits=0):
        """ a.__round__([ndigits]) <==> round(a[, ndigits])

            Element-wise round to given precision in decimal digits (default 0 digits).
            This always returns an Array of floating point numbers.  Precision may be negative.

            >>> A = Array([1.0/x for x in range(1, 10)], shape=(3, 3))
            >>> print round(A, 2).formated()
            [[1.0, 0.5, 0.33],
             [0.25, 0.2, 0.17],
             [0.14, 0.13, 0.11]]
        """
        return self.__class__(round(x, ndigits) for x in self)
    def __pos__(self):
        """ a.__pos__() <==> +a

            Element-wise positive of a

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (+A).formated()
            [[0, 1],
             [2, 3]]
        """
        return self.__class__(operator.pos(x) for x in self)
    def __neg__(self):
        """ a.__neg__() <==> -a

            Element-wise negation of a

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (-A).formated()
            [[0, -1],
             [-2, -3]]
        """
        return self.__class__(operator.neg(x) for x in self)
    def __add__(self, other) :
        """ a.__add__(b) <==> a+b

            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value

            Note : when the operands are 2 Arrays of different shapes, both are cast to the shape of largest size
            if possible. Created components are filled with class default value.

            Related : See the Array.__coerce__ method

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (A).formated()
            [[0, 1],
             [2, 3]]
            >>> print (A+1).formated()
            [[1, 2],
             [3, 4]]
            >>> print (A+[1, 2]).formated()
            [[1, 3],
             [3, 5]]
            >>> A = Array(range(9), shape=(3, 3))
            >>> M = MatrixN(range(10, 50, 10), shape=(2, 2))
            >>> print (A+M).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+M)
            MatrixN
            >>> A = Array(range(10, 50, 10), shape=(2, 2))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> print (A+M).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A+M)
            MatrixN
        """
        try :
            nself, nother = coerce(self, other)
        except :
            # returning NotImplemented on self.__oper__(other) defers to other.__roper__(self) UNLESS self and other are of the same type
            return NotImplemented
        res = map(operator.add, nself, nother)
        return nself.__class__._convert(res)
    def __radd__(self, other) :
        """ a.__radd__(b) <==> b+a

            Returns the result of the element wise addition of a and b if b is convertible to Array,
            adds b to every component of a if b is a single numeric value

            Note : when the operands are 2 Arrays of different shapes, both are cast to the shape of largest size
            if possible. Created components are filled with class default value.

            Related : See the Array.__coerce__ method

            >>> A = Array(range(4), shape=(2, 2))
            >>> print (A).formated()
            [[0, 1],
             [2, 3]]
            >>> print (1+A).formated()
            [[1, 2],
             [3, 4]]
            >>> print ([1, 2]+A).formated()
            [[1, 3],
             [3, 5]]
            >>> A = Array(range(9), shape=(3, 3))
            >>> M = MatrixN(range(10, 50, 10), shape=(2, 2))
            >>> print (M+A).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(M+A)
            MatrixN
            >>> A = Array(range(10, 50, 10), shape=(2, 2))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> print (M+A).formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(M+A)
            MatrixN
        """
        return self.__add__(other)
    def __iadd__(self, other):
        """ a.__iadd__(b) <==> a += b

            In place addition of a and b, see __add__, result must fit a's type

            >>> A = Array(range(9), shape=(3, 3))
            >>> M = MatrixN(range(10, 50, 10), shape=(2, 2))
            >>> A += M
            >>> print A.formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(A)
            Array
            >>> A = Array(range(9), shape=(3, 3))
            >>> M = MatrixN(range(10, 50, 10), shape=(2, 2))
            >>> M += A
            >>> print M.formated()
            [[10, 21, 2],
             [33, 44, 5],
             [6, 7, 8]]
            >>> print clsname(M)
            MatrixN

            Result must be castable to the type of a

            >>> A = Array(range(12), shape=(2, 3, 2))
            >>> M = MatrixN(range(9), shape=(3, 3))
            >>> B = M + A
            >>> print B.formated()
            [[[0, 2],
              [4, 6],
              [8, 10]],
            <BLANKLINE>
             [[12, 14],
              [16, 9],
              [10, 11]]]
            >>> print clsname(B)
            Array
            >>> M += A
            Traceback (most recent call last):
                ...
            TypeError: cannot cast a Array of shape (2, 3, 2) to a MatrixN of shape (2, 6),
            as it would truncate data or reduce the number of dimensions
        """
        return self.__class__(self + other)
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

    # additional methods that defer to a generic function patched to accept iterables

    def sum(self, *args, **kwargs):
        """ a.sum([axis0[, axis1[, ...[, start=0]]]]) <=> sum(a, start=start, axis=(axis0, axis1, ...))

            Returns the sum of all the components of a, plus start.
            If axis are specified will return an Array of sum(x) for x in a.axisiter(*axis), else will
            sum on all axis of a.

            >>> A = Array([[1,2,3],[4,5,6]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A.sum()
            21
            >>> A.sum(0, 1)
            21
            >>> A.sum(0)
            Array([5, 7, 9])
            >>> A.sum(1)
            Array([6, 15])
        """
        return sum(self, start=kwargs.get('start', 0), axis=kwargs.get('axis', args))
    def prod(self, *args, **kwargs):
        """ a.prod([axis0[, axis1[, ...[, start=0]]]]) <=> prod(a, start=start, axis=(axis0, axis1, ...))

            Returns the product of all the components of a, an iterable of values that support the mul operator, times start.
            If axis are specified will return an Array of prod(x) for x in a.axisiter(*axis).

            >>> A = Array([[1,2,3],[4,5,6]])
            >>> print A.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> A.prod()
            720
            >>> A.prod(0, 1)
            720
            >>> A.prod(0)
            Array([4, 10, 18])
            >>> A.prod(1)
            Array([6, 120])
        """
        return prod(self, start=kwargs.get('start', 1), axis=kwargs.get('axis', args))
    # __nonzero__ is not defined, use any or all
    def any(self, *args, **kwargs):
        """ a.any([axis0[, axis1[, ...]]]) <=> any(a, axis=(axis0, axis1, ...))

            Returns True if any of the components of iterable a evaluate to True.
            If axis are specified will return an Array of any(x) for x in a.axisiter(*axis).

            >>> A = Array([[False,True,True],[False,True,False]])
            >>> print A.formated()
            [[False, True, True],
             [False, True, False]]
            >>> A.any()
            True
            >>> A.any(0, 1)
            True
            >>> A.any(0)
            Array([False, True, True])
            >>> A.any(1)
            Array([True, True])
        """
        return any(self, axis=kwargs.get('axis', args))
    def all(self, *args, **kwargs):
        """ a.all([axis0[, axis1[, ...]]]) <=> all(a, axis=(axis0, axis1, ...))

            Returns True if all the components of iterable a evaluate to True.
            If axis are specified will return an Array of all(x) for x in a.axisiter(*axis).

            >>> A = Array([[True,True,True],[False,True,False]])
            >>> print A.formated()
            [[True, True, True],
             [False, True, False]]
            >>> A.all()
            False
            >>> A.all(0, 1)
            False
            >>> A.all(0)
            Array([False, True, False])
            >>> A.all(1)
            Array([True, False])
        """
        return all(self, axis=kwargs.get('axis', args))
    def min(self, *args, **kwargs):
        """ a.min([axis0[, axis1[, ...[, key=func]]]])  <==> min(a[, key=func[, axis=(axis0, axis1, ...)]])

            Returns the smallest component of a.
            If axis are specified will return an Array of element-wise min(x) for x in a.axisiter(*axis).

            >>> A = Array([[6,3,4],[1,5,0.5]])
            >>> print A.formated()
            [[6, 3, 4],
             [1, 5, 0.5]]
            >>> A.min()
            0.5
            >>> A.min(0, 1)
            0.5
            >>> A.min(0)
            Array([1, 3, 0.5])
            >>> A.min(1)
            Array([3, 0.5])
        """
        return min(self, axis=kwargs.get('axis', args), key=kwargs.get('key', None))
    def max(self, *args, **kwargs):
        """ a.max([axis0[, axis1[, ...[, key=func]]]])  <==> max(a[, key=func[, axis=(axis0, axis1, ...)]])

            Returns the greatest component of a.
            If axis are specified will return an Array of element-wise max(x) for x in a.axisiter(*axis).

            >>> A = Array([[6,3,4],[1,5,0.5]])
            >>> print A.formated()
            [[6, 3, 4],
             [1, 5, 0.5]]
            >>> A.max()
            6
            >>> A.max(0,1)
            6
            >>> A.max(0)
            Array([6, 5, 4])
            >>> A.max(1)
            Array([6, 5])
        """
        return max(self, axis=kwargs.get('axis', args), key=kwargs.get('key', None))

    # methods that are defined per Array class to allow overloading

    def sqlength(self, *args):
        """ a.sqlength(axis0, axis1, ...) <==> sqlength(a[, axis=(axis0, axis1, ...)])

            Returns square length of a, ie a*a or the sum of x*x for x in a if a is an iterable of numeric values.
            If a is an Array and axis are specified will return a list of sqlength(x) for x in a.axisiter(*axis).

            >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
            >>> print A.formated()
            [[0.5, 0.5, -0.707],
             [0.707, -0.707, 0.0]]
            >>> A.sqlength()
            1.999547
            >>> A.sqlength(0,1)
            1.999547
            >>> A.sqlength(0)
            Array([0.999849, 0.999698])
            >>> A.sqlength(1)
            Array([0.749849, 0.749849, 0.499849])
        """
        axis = self._getaxis(args, fill=True)
        it = self.axisiter(*axis)
        subshape = it.itemshape
        if subshape == () :
            return reduce(operator.add, map(lambda x:x*x, it))
        else :
            return Array(a.sqlength() for a in it)
    def length(self, *args):
        """ a.length(axis0, axis1, ...) <==> length(a[, axis=(axis0, axis1, ...)])

            Returns length of a, sqrt(a*a) or the square root of the sum of x*x for x in a if a is an iterable of numeric values.
            If a is an Array and axis are specified will return a list of length(x) for x in a.axisiter(*axis).

            >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
            >>> print A.formated()
            [[0.5, 0.5, -0.707],
             [0.707, -0.707, 0.0]]
            >>> A.length()
            1.4140533936170869
            >>> A.length(0,1)
            1.4140533936170869
            >>> A.length(0)
            Array([0.99992449715, 0.999848988598])
            >>> A.length(1)
            Array([0.865938219505, 0.865938219505, 0.707])
        """
        return sqrt(self.sqlength(*args))
    def normal(self, *args):
        """ a.normal(axis0, axis1, ...) <==> normal(a[, axis=(axis0, axis1, ...)])

            Returns a normalized copy of self: self/self.length(axis0, axis1, ...).

            >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0.0]])
            >>> print A.formated()
            [[0.5, 0.5, -0.707],
             [0.707, -0.707, 0.0]]
            >>> print A.normal().formated()
            [[0.353593437318, 0.353593437318, -0.499981120367],
             [0.499981120367, -0.499981120367, 0.0]]
            >>> print A.normal(0,1).formated()
            [[0.353593437318, 0.353593437318, -0.499981120367],
             [0.499981120367, -0.499981120367, 0.0]]
            >>> print A.normal(0).formated()
            [[0.5, 0.5, -0.707],
             [0.707, -0.707, 0.0]]
            >>> print A.normal(1).formated()
            [[0.577408397894, 0.577408397894, -1.0],
             [0.816455474623, -0.816455474623, 0.0]]
        """
        try :
            return self / self.length(*args)
        except :
            return self
    def normalize(self, *args):
        """ Performs an in place normalization of self """
        self.assign(self.normal(*args))
    def dist(self, other, *args):
        """ a.dist(b, axis0, axis1, ...) <==> dist(a, b[, axis=(axis0, axis1, ...)])

            Returns the distance between a and b, ie length(b-a, axis)

            >>> A = Array([[0.5, 0.5, -0.707],[0.707, -0.707, 0.0]])
            >>> print A.formated()
            [[0.5, 0.5, -0.707],
             [0.707, -0.707, 0.0]]
            >>> B = Array([[0.51, 0.49, -0.71],[0.71, -0.70, 0.0]])
            >>> print B.formated()
            [[0.51, 0.49, -0.71],
             [0.71, -0.7, 0.0]]
            >>> A.dist(B)
            0.016340134638368205
            >>> A.dist(B, 0, 1)
            0.016340134638368205
            >>> A.dist(B, 0)
            Array([0.0144568322948, 0.00761577310586])
            >>> A.dist(B, 1)
            Array([0.0104403065089, 0.0122065556157, 0.003])
        """
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return (nother-nself).length(*args)
    def distanceTo(self, other):
        """ a.distanceTo(b) <==> a.dist(b)

            Equivalent to the dist method, for compatibility with Maya's API. Does not take axis arguements
        """
        return self.dist(other)

    def isEquivalent(self, other, tol=eps):
        """ a.isEquivalent(b[, tol]) --> bool

            Returns True if both arguments have same shape and distance between both Array arguments is inferior or equal to tol.

            >>> A = Array([[0.5,0.5,-0.707],[0.707,-0.707,0]])
            >>> B = Array([[0.51,0.49,-0.71],[0.71,-0.70,0]])
            >>> C = Array([[0.501,0.499,-0.706],[0.706,-0.708,0.01]])
            >>> A.dist(B)
            0.016340134638368205
            >>> A.dist(C)
            0.010246950765959599
            >>> A.isEquivalent(C, 0.015)
            True
            >>> A.isEquivalent(B, 0.015)
            False
            >>> A.isEquivalent(B, 0.020)
            True
        """
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
        """ a.transpose([axis0[, axis1[, ...]]]) --> Array

            Returns a reordered / transposed along the specified axes.
            If no axes are given,or None is passed, switches the complete axes order.
            For a 2-d array, this is the usual matrix transpose.

            >>> A = Array(range(18), shape=(2,3,3))
            >>> print A.formated()
            [[[0, 1, 2],
              [3, 4, 5],
              [6, 7, 8]],
            <BLANKLINE>
             [[9, 10, 11],
              [12, 13, 14],
              [15, 16, 17]]]
            >>> print A.transpose().formated()
            [[[0, 9],
              [3, 12],
              [6, 15]],
            <BLANKLINE>
             [[1, 10],
              [4, 13],
              [7, 16]],
            <BLANKLINE>
             [[2, 11],
              [5, 14],
              [8, 17]]]
            >>> print A.transpose(0,2,1).formated()
            [[[0, 3, 6],
              [1, 4, 7],
              [2, 5, 8]],
            <BLANKLINE>
             [[9, 12, 15],
              [10, 13, 16],
              [11, 14, 17]]]

            >>> B=MatrixN(range(9), shape=(3, 3))
            >>> print B.formated()
            [[0, 1, 2],
             [3, 4, 5],
             [6, 7, 8]]
            >>> print B.transpose().formated()
            [[0, 3, 6],
             [1, 4, 7],
             [2, 5, 8]]
        """
        axis = self._getaxis(args, fill=True, reverse=True)
        if len(axis) != self.ndim :
            raise ValueError, "Transpose axis %s do not match array shape %s" % (axis, self.shape)
        else :
            return self.__class__._convert(Array([s for s in self.axisiter(*axis)], shape=(self.shape[x] for x in axis)))

    T = property(transpose, None, None, """The transposed array""")

    # arrays of complex values
    def conjugate(self):
        """ a.conjugate() <==> conjugate(a)

            Returns the element-wise complex.conjugate() of the Array.

            >>> A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]])
            >>> print A.formated()
            [[(1+2j), (2+3j)],
             [(4+5j), (6+7j)]]
            >>> print A.conjugate().formated()
            [[(1-2j), (2-3j)],
             [(4-5j), (6-7j)]]
            >>> print conjugate(A).formated()
            [[(1-2j), (2-3j)],
             [(4-5j), (6-7j)]]
            >>> A = Array(range(1, 5), shape=(2, 2))
            >>> print conjugate(A).formated()
            [[1, 2],
             [3, 4]]
        """
        return self.__class__(conjugate(x) for x in self)
    def real(self):
        """ a.real() <==> real(a)

            Returns the element-wise complex real part of the Array.

            >>> A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]])
            >>> print A.formated()
            [[(1+2j), (2+3j)],
             [(4+5j), (6+7j)]]
            >>> print A.real().formated()
            [[1.0, 2.0],
             [4.0, 6.0]]
            >>> print real(A).formated()
            [[1.0, 2.0],
             [4.0, 6.0]]
            >>> A = Array(range(1, 5), shape=(2, 2))
            >>> print real(A).formated()
            [[1, 2],
             [3, 4]]
        """
        return self.__class__(real(x) for x in self)
    def imag(self):
        """ a.real() <==> real(a)

            Returns the element-wise complex imaginary part of the Array.

            >>> A = Array([[complex(1, 2), complex(2, 3)], [complex(4, 5), complex(6, 7)]])
            >>> print A.formated()
            [[(1+2j), (2+3j)],
             [(4+5j), (6+7j)]]
            >>> print A.imag().formated()
            [[2.0, 3.0],
             [5.0, 7.0]]
            >>> print imag(A).formated()
            [[2.0, 3.0],
             [5.0, 7.0]]
            >>> A = Array(range(1, 5), shape=(2, 2))
            >>> print imag(A).formated()
            [[0, 0],
             [0, 0]]
        """
        return self.__class__(imag(x) for x in self)
    def blend(self, other, weight=0.5):
        """ a.blend(b[, weight=0.5]) <==> blend(a, b[, weights=0.5])

            Returns the result of blending from Array instance u to v according to
            either a scalar weight where blend will yield a*(1-weight) + b*weight Array,
            or a an iterable of independent weights.

            >>> A = Array(0, shape=(2, 2))
            >>> print A.formated()
            [[0, 0],
             [0, 0]]
            >>> B = Array(1, shape=(2, 2))
            >>> print B.formated()
            [[1, 1],
             [1, 1]]
            >>> print A.blend(B, weight=0.5).formated()
            [[0.5, 0.5],
             [0.5, 0.5]]
            >>> print blend(A, B).formated()
            [[0.5, 0.5],
             [0.5, 0.5]]
            >>> print blend(A, B, weight=[x/4.0 for x in range(4)]).formated()
            [[0.0, 0.25],
             [0.5, 0.75]]
            >>> print blend(A, B, weight=[[0.0, 0.25],[0.75, 1.0]]).formated()
            [[0.0, 0.25],
             [0.75, 1.0]]
        """
        try :
            nself, nother = coerce(self, other)
        except :
            return NotImplemented
        return self.__class__._convert(blend(self, other, weight=weight))
    def clamp(self, low=0, high=1):
        """ a.clamp([low=0[, high=1]]) <==> clamp (a, low, high)

            Returns the result of clamping each component of a between low and high if low and high are scalars,
            or the corresponding components of low and high if low and high are sequences of scalars

            >>> A = Array(range(4), shape=(2, 2))
            >>> print A.formated()
            [[0, 1],
             [2, 3]]
            >>> print A.clamp(1, 2).formated()
            [[1, 1],
             [2, 2]]
            >>> print clamp(A, 1, 2).formated()
            [[1, 1],
             [2, 2]]
            >>> print clamp(A, 0.0, [x/4.0 for x in range(4)]).formated()
            [[0, 0.25],
             [0.5, 0.75]]
        """
        return self.__class__._convert(clamp(self, low, high))

# functions that work on MatrixN (and just defer to MatrixN methods)

def det(value):
    """ det(m) --> float

        Returns the determinant of m, 0 if m is a singular MatrixN, m must be convertible to MatrixN.

        Related : see MatrixN.det(self) method.
    """
    if isinstance(value, MatrixN) :
        return value.det()
    elif isNumeric(value) :
        return value
    else :
        try :
            value = MatrixN(value)
        except :
            raise TypeError, "%s not convertible to MatrixN" % (clsname(value))
        return value.det()

def inv(value):
    """ inv(m) --> MatrixN

        Returns the inverse of m, if m is invertible, raises ZeroDivisionError otherwise.
        m must be convertible to MatrixN.

        Related : see MatrixN.inverse(self) method and MatrixN.I property
    """
    if isinstance(value, MatrixN) :
        return value.inverse()
    elif isNumeric(value) :
        return 1.0 / value
    else :
        try :
            value = MatrixN(value)
        except :
            raise TypeError, "%s not convertible to MatrixN" % (clsname(value))
        return value.inverse()

class MatrixN(Array):
    """ A generic size MatrixN class, basically a 2 dimensional Array.

        Most methods and behavior are herited from Array, with the limitation that a MatrixN must have
        exactly 2 dimensions.

        >>> M = MatrixN()
        >>> M
        MatrixN([[]])
        >>> M = MatrixN([])
        >>> M
        MatrixN([[]])
        >>> M = MatrixN([0, 1, 2])
        >>> print M.formated()
        [[0, 1, 2]]
        >>> M = MatrixN([[0, 1, 2]])
        >>> print M.formated()
        [[0, 1, 2]]
        >>> M = MatrixN([[0], [1], [2]])
        >>> print M.formated()
        [[0],
         [1],
         [2]]
        >>> M = MatrixN([[1, 2, 3], [4, 5, 6]])
        >>> print M.formated()
        [[1, 2, 3],
         [4, 5, 6]]
        >>> M = MatrixN(range(4), shape=(2, 2))
        >>> print M.formated()
        [[0, 1],
         [2, 3]]

        The MatrixN class has a constant ndim of 2

        >>> MatrixN.ndim
        2
        >>> M.ndim
        2
        >>> MatrixN.ndim = 3
        Traceback (most recent call last):
            ...
        AttributeError: attribute ndim is a read only class attribute and cannot be modified on class MatrixN
        >>> M.ndim = 3
        Traceback (most recent call last):
            ...
        AttributeError: 'MatrixN' object attribute 'ndim' is read-only

        It's protected against initialization or resizing to a shape that wouldn't be a MatrixN anymore

        >>> M = MatrixN([[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])
        Traceback (most recent call last):
            ...
        TypeError: cannot initialize a MatrixN of shape (2, 6) from [[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]] of shape (2, 2, 3),
        as it would truncate data or reduce the number of dimensions

        >>> M.resize((2, 2, 3))
        Traceback (most recent call last):
            ...
        TypeError: new shape (2, 2, 3) is not compatible with class MatrixN

        Other Array types can be cast to MatrixN, but truncating data or reducing dimensions is not allowed
        to avoid silent loss of data in a conversion, use an explicit resize / trim / sub-array extraction

        >>> A = Array(range(9), shape=(3, 3))
        >>> M = MatrixN(A)
        >>> print M.formated()
        [[0, 1, 2],
         [3, 4, 5],
         [6, 7, 8]]
        >>> print clsname(M)
        MatrixN
        >>> A = Array([[[1, 2, 3], [4, 5, 6]], [[10, 20, 30], [40, 50, 60]]])
        >>> M = MatrixN(A)
        Traceback (most recent call last):
            ...
        TypeError: cannot cast a Array of shape (2, 2, 3) to a MatrixN of shape (2, 6),
        as it would truncate data or reduce the number of dimensions

        When initializing from a 1-d Array like a VectorN, dimension is upped to 2 by making it a row

        >>> V = VectorN(1, 2, 3)
        >>> M = MatrixN(V)
        >>> print M.formated()
        [[1, 2, 3]]

        Internally, rows are stored as Array though, not VectorN

        >>> M[0]
        Array([1, 2, 3])

        As for Array, __init__ is a shallow copy

        >>> A = Array(range(9), shape=(3, 3))
        >>> M = MatrixN(A)
        >>> M == A
        False
        >>> M is A
        False
        >>> M.isEquivalent(A)
        True
        >>> M[0] == A[0]
        True
        >>> M[0] is A[0]
        True
    """
    __slots__ = ['_data', '_shape', '_size']

    # A MatrixN is a two-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 2

    def _getshape(self):
        if len(self) :
            return (len(self), len(self[0]))
        else :
            return (0, 0)
    def _setshape(self, newshape):
        self.resize(newshape)

    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None,
                     """ m.shape : tuple of two ints

                         Shape of the MatrixN, the (nrow, ncol) tuple.

                         It can be queried, or set to change the MatrixN's shape similarly to the reshape method.

                         >>> M = MatrixN(range(1, 17), shape=(4, 4))
                         >>> print M.formated()
                         [[1, 2, 3, 4],
                          [5, 6, 7, 8],
                          [9, 10, 11, 12],
                          [13, 14, 15, 16]]
                         >>> M.shape=(2, 8)
                         >>> print M.formated()
                         [[1, 2, 3, 4, 5, 6, 7, 8],
                          [9, 10, 11, 12, 13, 14, 15, 16]]
                         >>> M.shape=(2, 2, 4)
                         Traceback (most recent call last):
                             ...
                         TypeError: new shape (2, 2, 4) is not compatible with class MatrixN

                         Related : see Array.reshape method.
                     """)
    size = property(lambda x : x.shape[0]*x.shape[1], None, None, "Total size of the MatrixN (number of individual components), ie nrow*ncol")

    def is_square(self):
        """ m.is_square() --> bool

            Returns True if m is a square MatrixN, it has the same number of rows and columns.

            >>> M = MatrixN(range(4), shape=(2, 2))
            >>> M.is_square()
            True
            >>> M = MatrixN(range(6), shape=(2, 3))
            >>> M.is_square()
            False
        """
        return self.shape[0] == self.shape[1]

    @classmethod
    def identity(cls, n):
        """ MatrixN.identity(n) --> MatrixN

            Returns the identity MatrixN of size n :
            a square n x n MatrixN of 0.0, with all diagonal components set to 1.0.

            >>> I = MatrixN.identity(4)
            >>> print I.formated()
            [[1.0, 0.0, 0.0, 0.0],
             [0.0, 1.0, 0.0, 0.0],
             [0.0, 0.0, 1.0, 0.0],
             [0.0, 0.0, 0.0, 1.0]]
        """
        return cls([[float(i==j) for i in xrange(n)] for j in xrange(n)])

    @classmethod
    def basis(cls, u, v, normalize=False):
        """ MatrixN.basis(u, v[, normalize=False]) --> MatrixN

            Returns the basis MatrixN built using u, v and u^v as coordinate axis,
            The a, b, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
                n = u ^ v
                v = n ^ u
            if the normalize keyword argument is set to True, the vectors are also normalized

            >>> M = MatrixN.basis(VectorN(0, 1, 0), VectorN(0, 0, 1))
            >>> print M.formated()
            [[0, 0, 1],
             [1, 0, 0],
             [0, 1, 0]]
        """
        u = VectorN(u)
        v = VectorN(v)
        assert len(u) == len(v) == 3, 'basis is only defined for two Vectors of size 3'
        if normalize :
            u = normal(u)
            n = normal(cross(u, v))
            v = cross(n, u)
        else :
            n = cross(u, v)
            v = cross(n, u)
        return cls(MatrixN(u, v, n).transpose())

    # row and column size properties
    def _getnrow(self):
        return self.shape[0]
    def _setnrow(self, m):
        self.trim((m, self.shape[1]))
    nrow = property(_getnrow, _setnrow, None,
                    """ m.nrow : int

                        Number of rows in this MatrixN.

                        It can be queried, or set to reduce / expand the matrix similarly to the trim method.

                        >>> M = MatrixN(range(1, 10), shape=(3, 3))
                        >>> print M.formated()
                        [[1, 2, 3],
                         [4, 5, 6],
                         [7, 8, 9]]
                        >>> M.nrow, M.ncol
                        (3, 3)
                        >>> M.nrow, M.ncol = 4, 4
                        >>> print M.formated()
                        [[1, 2, 3, 0],
                         [4, 5, 6, 0],
                         [7, 8, 9, 0],
                         [0, 0, 0, 0]]
                    """)
    def _getncol(self):
        return self.shape[1]
    def _setncol(self, n):
        self.trim((self.shape[0], n))
    ncol = property(_getncol, _setncol, None,
                    """ m.ncol : int

                        Number of rows in this MatrixN.

                        It can be queried, or set to reduce / expand the matrix similarly to the trim method.

                        >>> M = MatrixN(range(1, 10), shape=(3, 3))
                        >>> print M.formated()
                        [[1, 2, 3],
                         [4, 5, 6],
                         [7, 8, 9]]
                        >>> M.nrow, M.ncol
                        (3, 3)
                        >>> M.nrow, M.ncol = 4, 4
                        >>> print M.formated()
                        [[1, 2, 3, 0],
                         [4, 5, 6, 0],
                         [7, 8, 9, 0],
                         [0, 0, 0, 0]]
                    """)

    # specific iterators
    @property
    def row(self):
        """ m.row --> ArrayIter

            Iterator on the MatrixN rows.
            Being an ArrayIter, it support __len__, __getitem__, __setitem__ and __delitem__

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> M.nrow, M.ncol = 4, 4
            >>> M[-1, -1] = 1
            >>> print M.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]
            >>> [r for r in M.row]
            [Array([1, 2, 3, 0]), Array([4, 5, 6, 0]), Array([7, 8, 9, 0]), Array([0, 0, 0, 1])]

            The row iterator indexing works like the MatrixN indexing and returns references.

            >>> r = M.row[0]
            >>> r
            Array([1, 2, 3, 0])
            >>> r == M[0]
            True
            >>> r is M[0]
            True

            Slices return shallow copies though

            >>> r = M.row[:2]
            >>> print r.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0]]
            >>> print clsname(r)
            MatrixN

            >>> r == M[:2]
            True
            >>> r is M[:2]
            False
            >>> r[0] == M[0]
            True
            >>> r[0] is M[0]
            True

            Results can be indexed again, using Array indexing or MatrixN methods wether they're returned
            as Array (single lines / columns) or MatrixN (2 dimensionnal Array).

            >>> c = r.col[1]
            >>> c
            Array([2, 5])

            Multiple indexing is possible

            >>> M[0, 1]
            2
            >>> M.row[0][1]
            2
            >>> M.row[0, 1]
            2

            Values can be set as with MatrixN indexing

            >>> M.row[:2, 1] = 10
            >>> print M.formated()
            [[1, 10, 3, 0],
             [4, 10, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]
            >>> r = M.row[:2]
            >>> r[:, 1] = [2, 5]
            >>> print M.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]

            Rows can be deleted too

            >>> del M.row[-1]
            >>> del M[None, -1]
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]

        """
        return self.axisiter(0)
    @property
    def col(self):
        """ m.col --> ArrayIter

            Iterator on the MatrixN columns
            Being an ArrayIter, it support __len__, __getitem__, __setitem__ and __delitem__

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> M.nrow, M.ncol = 4, 4
            >>> M[-1, -1] = 1
            >>> print M.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]
            >>> [c for c in M.col]
            [Array([1, 4, 7, 0]), Array([2, 5, 8, 0]), Array([3, 6, 9, 0]), Array([0, 0, 0, 1])]

            The col iterator has to rebuild sub-arrays and thus returns copies and not references.

            >>> c = M.col[0]
            >>> c
            Array([1, 4, 7, 0])
            >>> c == M[:,0]
            True
            >>> c is M[:,0]
            False

            Multiple columns are returned as rows in a new MatrixN

            >>> c = M.col[:2]
            >>> print c.formated()
            [[1, 4, 7, 0],
             [2, 5, 8, 0]]
            >>> print clsname(c)
            MatrixN

            >>> s = M[:,:2]
            >>> print s.formated()
            [[1, 2],
             [4, 5],
             [7, 8],
             [0, 0]]
            >>> print clsname(s)
            MatrixN

            TODO : is it what we want ? If so invert these

            # >>> c == s
            # True
            # >>> c == s.T
            # False

            Results can be indexed again, using Array indexing or MatrixN methods wether they're returned
            as Array (single lines / columns) or MatrixN (2 dimensionnal Array).

            >>> r = c.row[1]
            >>> r
            Array([2, 5, 8, 0])
            >>> r = s.row[1]
            >>> r
            Array([4, 5])

            Multiple indexing is possible

            >>> M[0, 1]
            2
            >>> M.col[1][0]
            2
            >>> M.col[1, 0]
            2

            As results are rebuilt Arrays, values can only b set for full columns

            >>> M.col[1]
            Array([2, 5, 8, 0])

            This won't work :

            >>> M.col[1][:2] = 10
            >>> print M.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]

            But this will :

            >>> M.col[1, :2] = 10
            >>> print M.formated()
            [[1, 10, 3, 0],
             [4, 10, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]

            >>> c = M.col[1]
            >>> c[:2] = [2, 5]
            >>> M.col[1] = c
            >>> print M.formated()
            [[1, 2, 3, 0],
             [4, 5, 6, 0],
             [7, 8, 9, 0],
             [0, 0, 0, 1]]

            Columns can be deleted too

            >>> del M.col[-1]
            >>> del M[-1]
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]

        """
        return self.axisiter(1)

    # overloaded Array operators

    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b

            If b is a MatrixN, __mul__ is mapped to matrix multiplication, if b is a VectorN, to MatrixN by VectorN multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, MatrixN) :
            return self.__class__._convert( [ [ dot(row,col) for col in other.col ] for row in self.row ] )
        elif isinstance(other, VectorN) :
            if other.size <= self.shape[1] :
                return other.__class__._convert( [ dot(row, other) for row in self.row ] [:other.size] )
            else :
                raise ValueError, "matrix of shape %s and vector of size %s are not conformable for a MatrixN * VectorN multiplication" % (self.size, other.shape)
        else :
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a

            If b is a MatrixN, __rmul__ is mapped to matrix multiplication, if b is a VectorN, to VectorN by MatrixN multiplication,
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, MatrixN) :
            return MatrixN( [ [ dot(row,col) for col in self.col ] for row in other.row ] )
        elif isinstance(other, VectorN) :
            if other.size <= self.shape[0] :
                return other.__class__._convert( [ dot(col, other) for col in self.col ] [:other.size] )
            else :
                raise ValueError, "vector of size %s and matrix of shape %s are not conformable for a VectorN * MatrixN multiplication" % (other.size, self.shape)
        else :
            return Array.__rmul__(self, other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b

            In place multiplication of MatrixN a and b, see __mul__, result must fit a's type """
        res = self*other
        if isinstance(res, self.__class__) :
            return self.__class__(res)
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))

    # specific methods

    def diagonal(self, offset=0, wrap=False) :
        """ m.diagonal([offset=0[, wrap=False]]) -> Array

            Returns the diagonal of the MatrixN with the given offset,
            i.e., the collection of elements of the form a[i,i+offset].
            If keyword wrap=True will wrap out of bounds indices

            Examples :

            >>> M = MatrixN([[1, 2], [4, 6]])
            >>> print M.formated()
            [[1, 2],
             [4, 6]]
            >>> M.diagonal()
            Array([1, 6])
            >>> M.diagonal(1)
            Array([2])
            >>> M.diagonal(1, wrap=True)
            Array([2, 4])
            >>> M.diagonal(-1)
            Array([2, 4])
            >>> M.diagonal(-1, wrap=True)
            Array([2, 4])
        """
        assert self.ndim == 2, "can only calculate diagonal on Array or sub Arrays of dimension 2"

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

    def trace(self, offset=0, wrap=False) :
        """ a.trace([offset=0[, wrap=False]]) -> float

            Returns the sum of the components on the diagonal, obtained by calling m.diagonal(offset, wrap).

            >>> M = MatrixN([[1, 2], [4, 6]])
            >>> print M.formated()
            [[1, 2],
             [4, 6]]
            >>> M.trace()
            7
            >>> M.trace(offset=1)
            2
            >>> M.trace(offset=1, wrap=True)
            6
            >>> M.trace(offset=-1)
            6
            >>> M.trace(offset=-1, wrap=True)
            6
        """
        return sum(self.diagonal(offset, wrap))

    def minor(self, i, j):
        """ m.minor(i, j) --> MatrixN

            Returns the MatrixN obtained by deleting row i and column j from m.

            >>> M = MatrixN(range(4), shape=(2, 2))
            >>> print M.formated()
            [[0, 1],
             [2, 3]]
            >>> M.minor(0, 0)
            MatrixN([[3]])
            >>> M.minor(0, 1)
            MatrixN([[2]])
            >>> M.minor(1, 0)
            MatrixN([[1]])
            >>> M.minor(1, 1)
            MatrixN([[0]])

            >>> M = MatrixN.identity(4)
            >>> M[:3, :3] = [float(i) for i in range(1, 10)]
            >>> print M.formated()
            [[1.0, 2.0, 3.0, 0.0],
             [4.0, 5.0, 6.0, 0.0],
             [7.0, 8.0, 9.0, 0.0],
             [0.0, 0.0, 0.0, 1.0]]
            >>> print M.minor(3, 3).formated()
            [[1.0, 2.0, 3.0],
             [4.0, 5.0, 6.0],
             [7.0, 8.0, 9.0]]
        """
        # TODO : the below example fails.  M.minor(0,0) returns an Array instead of MatrixN
        """
            >>> M = MatrixN([1])
            >>> M
            MatrixN([[1]])
            >>> M.minor(0, 0)
            MatrixN([])
        """

        index = self._getindex((i, j), default=None)
        m = self.deleted(index)
        return m

    def cofactor(self, i, j):
        """ m.cofactor(i, j) --> float

            Returns the cofactor of matrix m for index (i, j),
            the determinant of the MatrixN obtained by deleting row i and column j from m (the minor),
            signed by (-1)**(i+j).

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> print M.minor(2, 2).formated()
            [[1, 2],
             [4, 5]]
            >>> M.minor(2, 2).det()
            -3
            >>> M.cofactor(2, 2)
            -3
            >>> print M.minor(0, 1).formated()
            [[4, 6],
             [7, 9]]
            >>> M.minor(0, 1).det()
            -6
            >>> M.cofactor(0, 1)
            6
        """
        return ((-1)**(i+j))*self.minor(i, j).det()

    # sometimes called adjoint
    def adjugate(self):
        """ m.adjugate() --> MatrixN

            Returns the adjugate MatrixN of the square MatrixN m : the MatrixN of the cofactors of m.
            It's a square MatrixN of same size as m, where a component of index (i, j) is set to the value
            of m.cofactor(i, j).

            >>> M = MatrixN([ [100/(i+j) for i in xrange(1,5)] for j in xrange(4) ])
            >>> print M.formated()
            [[100, 50, 33, 25],
             [50, 33, 25, 20],
             [33, 25, 20, 16],
             [25, 20, 16, 14]]
            >>> print M[:1, :1].adjugate().formated()
            [[1]]
            >>> print M[:2, :2].adjugate().formated()
            [[33, -50],
             [-50, 100]]
            >>> print M[:3, :3].adjugate().formated()
            [[35, -175, 161],
             [-175, 911, -850],
             [161, -850, 800]]
            >>> print M[:4, :4].adjugate().formated()
            [[42, -210, 154, 49],
             [-210, 1054, -775, -245],
             [154, -775, 575, 175],
             [49, -245, 175, 63]]
        """
        assert self.is_square(), "Adjugate MatrixN can only be computed for a square MatrixN"
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
        assert nc >= nr, "MatrixN needs to have at least as much columns as rows to do a Gauss-Jordan elimination"
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
                raise ZeroDivisionError, "MatrixN is singular"
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
        """ m.gauss() --> MatrixN

            Returns the triangular matrix obtained by Gauss-Jordan elimination on m,
            will raise a ZeroDivisionError if m cannot be triangulated.

            >>> M = MatrixN([ [1.0/(i+j) for i in xrange(1,7)] for j in xrange(6) ])
            >>> print round(M, 2).formated()
            [[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
             [0.5, 0.33, 0.25, 0.2, 0.17, 0.14],
             [0.33, 0.25, 0.2, 0.17, 0.14, 0.13],
             [0.25, 0.2, 0.17, 0.14, 0.13, 0.11],
             [0.2, 0.17, 0.14, 0.13, 0.11, 0.1],
             [0.17, 0.14, 0.13, 0.11, 0.1, 0.09]]
            >>> print round(M[:1, :1].gauss(), 2).formated()
            [[1.0]]
            >>> print round(M[:2, :2].gauss(), 2).formated()
            [[1.0, 0.5],
             [0.0, 0.08]]
            >>> print round(M[:3, :3].gauss(), 2).formated() # doctest: +SKIP
            [[1.0, 0.5, 0.33],
             [0.0, 0.08, 0.09],
             [0.0, 0.0, -0.01]]
            >>> print round(M[:4, :4].gauss(), 2).formated() # doctest: +SKIP
            [[1.0, 0.5, 0.33, 0.25],
             [0.0, 0.08, 0.09, 0.08],
             [0.0, 0.0, -0.01, -0.01],
             [0.0, 0.0, 0.0, 0.0]]
            >>> print round(M[:5, :5].gauss(), 2).formated()  # doctest: +SKIP
            [[1.0, 0.5, 0.33, 0.25, 0.2],
             [0.0, 0.08, 0.09, 0.08, 0.08],
             [0.0, 0.0, -0.01, -0.01, -0.01],
             [0.0, 0.0, 0.0, 0.0, 0.0],
             [0.0, 0.0, 0.0, -0.0, -0.0]]
            >>> print round(M[:6, :6].gauss(), 2).formated() # doctest: +SKIP
            [[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
             [0.0, 0.08, 0.09, 0.08, 0.08, 0.07],
             [0.0, 0.0, 0.01, 0.01, 0.01, 0.01],
             [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
             [0.0, 0.0, 0.0, 0.0, -0.0, -0.0],
             [0.0, 0.0, 0.0, 0.0, 0.0, -0.0]]

            >>> M = MatrixN([[1, 2, 3], [2, 4, 6], [6, 7, 8]])
            >>> print M.formated()
            [[1, 2, 3],
             [2, 4, 6],
             [6, 7, 8]]
            >>> M.det()
            0
            >>> M.isSingular()
            True
            >>> print M.gauss().formated()
            Traceback (most recent call last):
                ...
            ZeroDivisionError: MatrixN is singular
        """
        return self._gauss_jordan()[0]

    def reduced(self):
        """ m.reduced() --> MatrixN

            Returns the reduced row echelon form of the matrix a by Gauss-Jordan elimination,
            followed by back substitution.

            >>> M = MatrixN([ [1.0/(i+j) for i in xrange(1,7)] for j in xrange(6) ])
            >>> print round(M, 2).formated()
            [[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
             [0.5, 0.33, 0.25, 0.2, 0.17, 0.14],
             [0.33, 0.25, 0.2, 0.17, 0.14, 0.13],
             [0.25, 0.2, 0.17, 0.14, 0.13, 0.11],
             [0.2, 0.17, 0.14, 0.13, 0.11, 0.1],
             [0.17, 0.14, 0.13, 0.11, 0.1, 0.09]]
            >>> print round(M[:1, :1].reduced(), 2).formated()
            [[1.0]]
            >>> print round(M[:2, :2].reduced(), 2).formated()
            [[1.0, 0.0],
             [0.0, 1.0]]
            >>> print round(M[:3, :3].reduced(), 2).formated() # doctest: +SKIP
            [[1.0, 0.0, 0.0],
             [0.0, 1.0, -0.0],
             [0.0, 0.0, 1.0]]
            >>> print round(M[:4, :4].reduced(), 2).formated() # doctest: +SKIP
            [[1.0, 0.0, 0.0, 0.0],
             [0.0, 1.0, -0.0, 0.0],
             [0.0, 0.0, 1.0, 0.0],
             [0.0, 0.0, 0.0, 1.0]]
            >>> print round(M[:5, :5].reduced(), 2).formated() # doctest: +SKIP
            [[1.0, 0.0, 0.0, 0.0, 0.0],
             [0.0, 1.0, -0.0, 0.0, -0.0],
             [0.0, 0.0, 1.0, 0.0, -0.0],
             [0.0, 0.0, 0.0, 1.0, -0.0],
             [0.0, 0.0, 0.0, -0.0, 1.0]]
            >>> print round(M[:6, :6].reduced(), 2).formated() # doctest: +SKIP
            [[1.0, 0.0, 0.0, 0.0, -0.0, 0.0],
             [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
             [0.0, 0.0, 1.0, 0.0, -0.0, 0.0],
             [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
             [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
             [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]

            >>> M = MatrixN([[1, 2, 3], [2, 4, 6], [6, 7, 8]])
            >>> print M.formated()
            [[1, 2, 3],
             [2, 4, 6],
             [6, 7, 8]]
            >>> M.det()
            0
            >>> M.isSingular()
            True
            >>> print M.reduced().formated()
            Traceback (most recent call last):
                ...
            ZeroDivisionError: MatrixN is singular
        """
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
        """ m.det() <==> det(m)

            Returns the determinant of m, 0 if MatrixN is singular.

            >>> M = MatrixN([ [100/(i+j) for i in xrange(1,7)] for j in xrange(6) ])
            >>> print M.formated()
            [[100, 50, 33, 25, 20, 16],
             [50, 33, 25, 20, 16, 14],
             [33, 25, 20, 16, 14, 12],
             [25, 20, 16, 14, 12, 11],
             [20, 16, 14, 12, 11, 10],
             [16, 14, 12, 11, 10, 9]]
            >>> M[:1, :1].det()
            100
            >>> M[:2, :2].det()
            800
            >>> M[:3, :3].det()
            63
            >>> M[:4, :4].det()
            7
            >>> M[:5, :5].det()
            -1199
            >>> M[:6, :6].det()
            452.0

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> M.det()
            0
        """
        assert self.is_square(), "determinant is only defined for a square MatrixN"
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

    def isSingular(self, tol=eps):
        """ m.isSingular([tol]) --> bool

            Returns True if m is singular, ie it's determinant is smaller than the given tolerance.

            >>> M = MatrixN(range(1, 5), shape=(2, 2))
            >>> print M.formated()
            [[1, 2],
             [3, 4]]
            >>> M.det()
            -2
            >>> M.isSingular()
            False

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> M.det()
            0
            >>> M.isSingular()
            True
        """
        return (abs(self.det()) <= tol)

    def inverse(self):
        """ m.inverse() <==> inv(m)

            Returns the inverse MatrixN of m, if m is invertible, will raise a ValueError otherwise.

            >>> M = MatrixN([ [1.0/(i+j) for i in xrange(1,7)] for j in xrange(6) ])
            >>> print round(M, 2).formated()
            [[1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
             [0.5, 0.33, 0.25, 0.2, 0.17, 0.14],
             [0.33, 0.25, 0.2, 0.17, 0.14, 0.13],
             [0.25, 0.2, 0.17, 0.14, 0.13, 0.11],
             [0.2, 0.17, 0.14, 0.13, 0.11, 0.1],
             [0.17, 0.14, 0.13, 0.11, 0.1, 0.09]]
            >>> print round(M[:1, :1].inverse(), 0).formated()
            [[1.0]]
            >>> print round(M[:2, :2].inverse(), 0).formated()
            [[4.0, -6.0],
             [-6.0, 12.0]]
            >>> print round(M[:3, :3].inverse(), 0).formated()
            [[9.0, -36.0, 30.0],
             [-36.0, 192.0, -180.0],
             [30.0, -180.0, 180.0]]
            >>> print round(M[:4, :4].inverse(), 0).formated()
            [[16.0, -120.0, 240.0, -140.0],
             [-120.0, 1200.0, -2700.0, 1680.0],
             [240.0, -2700.0, 6480.0, -4200.0],
             [-140.0, 1680.0, -4200.0, 2800.0]]
            >>> print round(M[:5, :5].inverse(), 0).formated()
            [[25.0, -300.0, 1050.0, -1400.0, 630.0],
             [-300.0, 4800.0, -18900.0, 26880.0, -12600.0],
             [1050.0, -18900.0, 79380.0, -117600.0, 56700.0],
             [-1400.0, 26880.0, -117600.0, 179200.0, -88200.0],
             [630.0, -12600.0, 56700.0, -88200.0, 44100.0]]
            >>> print round(M[:6, :6].inverse(), 0).formated()
            [[36.0, -630.0, 3360.0, -7560.0, 7560.0, -2772.0],
             [-630.0, 14700.0, -88200.0, 211680.0, -220500.0, 83160.0],
             [3360.0, -88200.0, 564480.0, -1411200.0, 1512000.0, -582120.0],
             [-7560.0, 211680.0, -1411200.0, 3628800.0, -3969000.0, 1552320.0],
             [7560.0, -220500.0, 1512000.0, -3969000.0, 4410000.0, -1746360.0],
             [-2772.0, 83160.0, -582120.0, 1552320.0, -1746360.0, 698544.0]]

            >>> M = MatrixN(range(1, 10), shape=(3, 3))
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
            >>> M.det()
            0
            >>> M.isSingular()
            True
            >>> print M.inverse().formated()
            Traceback (most recent call last):
                ...
            ValueError: MatrixN is not invertible
        """
        assert self.is_square(), "inverse is only defined for a square MatrixN, see linverse and rinverse"
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
                id = MatrixN.identity(n)
                m = self.hstacked(id).reduced()
                i = self.__class__(m[:, n:])
        except ZeroDivisionError :
            raise ValueError, "MatrixN is not invertible"

        return i

    inv = inverse

    I = property(inverse, None, None, """The inverse MatrixN""")

    def linverse(self):
        """ m.linverse() --> MatrixN

            Returns the left inverse matrix of m, the matrix n so that n * m = identity, if m is left-invertible,
            otherwise will raise a ValueError.
            If m is invertible then the left inverse of m is also it's right inverse, and it's inverse matrix.

            >>> M = MatrixN([[1, 2], [3, 4], [5, 6]])
            >>> print M.formated()
            [[1, 2],
             [3, 4],
             [5, 6]]
            >>> print round(M.linverse(), 2).formated()
            [[-1.33, -0.33, 0.67],
             [1.08, 0.33, -0.42]]
        """
        nr, nc = self.nrow, self.ncol
        assert nr >= nc, "a MatrixN can have an inverse if it is square and a left inverse only if it has more rows than columns"
        if nr == nc :
            return self.I
        else :
            t = self.T
            m = t * self
            return m.I * t

    def rinverse(self):
        """ m.rinverse() --> MatrixN

            Returns the right inverse matrix of m, the matrix n so that m * n = identity, if m is right-invertible,
            otherwise will raise a ValueError.
            If m is invertible then the right inverse of m is also it's left inverse, and it's inverse matrix.

            >>> M = MatrixN([[1, 2, 3], [4, 5, 6]])
            >>> print M.formated()
            [[1, 2, 3],
             [4, 5, 6]]
            >>> print round(M.rinverse(), 2).formated()
            [[-0.94, 0.44],
             [-0.11, 0.11],
             [0.72, -0.22]]
        """
        nr, nc = self.nrow, self.ncol
        assert nc >= nr, "a MatrixN can have an inverse if it is square and a right inverse only if it has more columns than rows"
        if nr == nc :
            return self.I
        else :
            t = self.T
            m = self * t
            return t * m.I

# functions that work on Vectors or 1-d Arrays

# only on size 3 Vectors

def cross(u, v):
    """ cross(u, v) --> VectorN

        Returns the cross product of u and v, u and v should be 3 dimensional vectors.

        >>> u = VectorN(1.0, 0.0, 0.0)
        >>> v = VectorN(0.0, 1.0, 0.0)
        >>> cross(u, v)
        VectorN([0.0, 0.0, 1.0])
        >>> cross(u, [0.0, 1.0, 0.0])
        VectorN([0.0, 0.0, 1.0])

        Related : see VectorN.cross method.
    """
    if not isinstance(u, VectorN) :
        try :
            u = VectorN(u)
        except :
            raise TypeError, "%s is not convertible to type VectorN, cross product is only defined for two Vectors of size 3" % (clsname(u))
    return u.cross(v)

def dot(u, v):
    """ dot(u, v) --> float

        Returns the dot product of u and v, u and v should be Vectors of identical size.

        >>> u = VectorN(1.0, 0.0, 0.0)
        >>> v = VectorN(0.707, 0.0, -0.707)
        >>> dot(u, v)
        0.70699999999999996
        >>> dot(u, [0.707, 0.0, -0.707])
        0.70699999999999996

        Related : see VectorN.dot method.
    """
    if not isinstance(u, VectorN) :
        try :
            u = VectorN(u)
        except :
            raise TypeError, "%s is not convertible to type VectorN, dot product is only defined for two Vectors of identical size" % (clsname(u))
    return u.dot(v)

def outer(u, v):
    """ outer(u, v) --> MatrixN

        Returns the outer product of vectors u and v.

        >>> u = VectorN(1.0, 2.0, 3.0)
        >>> v = VectorN(10.0, 20.0, 30.0)
        >>> outer(u, v)
        MatrixN([[10.0, 20.0, 30.0], [20.0, 40.0, 60.0], [30.0, 60.0, 90.0]])
        >>> outer(u, [10.0, 20.0, 30.0])
        MatrixN([[10.0, 20.0, 30.0], [20.0, 40.0, 60.0], [30.0, 60.0, 90.0]])

        Related : see VectorN.outer method.
    """
    if not isinstance(u, VectorN) :
        try :
            u = VectorN(u)
        except :
            raise TypeError, "%s is not convertible to type VectorN, outer product is only defined for two Vectors" % (clsname(u))
    return u.outer(v)

def angle(a, b, c=None):
    """ angle(u, v) --> float

        Returns the angle of rotation between u and v.
        u and v should be 3 dimensional Vectors representing 3D vectors.

        Note: this angle is not signed, use axis to know the direction of the rotation.

        >>> u = VectorN(1.0, 0.0, 0.0)
        >>> v = VectorN(0.707, 0.0, -0.707)
        >>> angle(u, v)
        0.78539816339744828
        >>> angle(u, [0.707, 0.0, -0.707])
        0.78539816339744828

        Alternatively can use the form angle(a, b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
        it is then equivalent to angle(b-a, c-a)

        >>> o = VectorN(0.0, 1.0, 0.0, 1.0)
        >>> p = VectorN(1.0, 1.0, 0.0, 1.0)
        >>> q = VectorN(0.707, 1.0, -0.707, 1.0)
        >>> angle(o, p, q)
        0.78539816339744828

        Related : see VectorN.angle method.
    """
    if not isinstance(a, VectorN) :
        try :
            a = VectorN(a)
        except :
            raise TypeError, "%s is not convertible to type VectorN, angle is only defined for 2 vectors or 3 points" % (clsname(a))
    if c is not None :
        return a.angle(b, c)
    else :
        return a.angle(b)

def axis(a, b, c=None, normalize=False):
    """ axis(u, v[, normalize=False]) --> VectorN

        Returns the axis of rotation from u to v as the vector n = u ^ v
        if the normalize keyword argument is set to True, n is also normalized.
        u and v should be 3 dimensional Vectors representing 3D vectors.

        >>> u = VectorN(1.0, 0.0, 0.0)
        >>> v = VectorN(0.707, 0.0, -0.707)
        >>> axis(u, v) == VectorN([0.0, 0.707, 0.0])
        True
        >>> axis(u, [0.707, 0.0, -0.707], normalize=True) == VectorN([-0.0, 1.0, 0.0])
        True

        Alternatively can use the form axis(a, b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
        it is then equivalent to axis(b-a, c-a).

        >>> o = VectorN(0.0, 1.0, 0.0, 1.0)
        >>> p = VectorN(1.0, 1.0, 0.0, 1.0)
        >>> q = VectorN(0.707, 1.0, -0.707, 1.0)
        >>> axis(o, p, q, normalize=True) == VectorN([0.0, 1.0, 0.0])
        True

        Related : see VectorN.axis method.
    """
    if not isinstance(a, VectorN) :
        try :
            a = VectorN(a)
        except :
            raise TypeError, "%s is not convertible to type VectorN, axis is only defined for 2 vectors or 3 points" % (clsname(a))
    if c is not None :
        return a.axis(b, c, normalize=normalize)
    else :
        return a.axis(b, normalize=normalize)

def cotan(a, b, c=None) :
    """ cotan(u, v) --> float :

        Returns the cotangent of the u, v angle, u and v should be 3 dimensional Vectors representing 3D vectors.

        >>> u = VectorN(1.0, 0.0, 0.0)
        >>> v = VectorN(0.707, 0.0, -0.707)
        >>> cotan(u, v)
        1.0
        >>> cotan(u, [0.707, 0.0, -0.707])
        1.0

        Alternatively can use the form cotan(a, b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
        it is then equivalent to cotan(b-a, c-a).

        >>> o = VectorN(0.0, 1.0, 0.0, 1.0)
        >>> p = VectorN(1.0, 1.0, 0.0, 1.0)
        >>> q = VectorN(0.707, 1.0, -0.707, 1.0)
        >>> cotan(o, p, q)
        1.0

        Related : see VectorN.cotan method.
    """
    if not isinstance(a, VectorN) :
        try :
            a = VectorN(a)
        except :
            raise TypeError, "%s is not convertible to type VectorN, cotangent product is only defined for 2 vectors or 3 points" % (clsname(a))
    if c is not None :
        return a.cotan(b, c)
    else :
        return a.cotan(b)

#
#    VectorN Class
#

class VectorN(Array):
    """
        A generic size VectorN class derived from Array, basically a 1 dimensional Array.

        Most methods and behavior are herited from Array, with the limitation that a MatrixN must have
        exactly 2 dimensions.

        >>> V = VectorN()
        >>> V
        VectorN([])
        >>> V = VectorN([0, 1, 2])
        >>> V
        VectorN([0, 1, 2])
        >>> V = VectorN(0, 1, 2)
        >>> V
        VectorN([0, 1, 2])
        >>> M = MatrixN([[0], [1], [2]])
        >>> print M.formated()
        [[0],
         [1],
         [2]]
        >>> V = VectorN(M.col[0])
        >>> V
        VectorN([0, 1, 2])

        The VectorN class has a constant ndim of 1

        >>> VectorN.ndim
        1
        >>> V.ndim
        1
        >>> VectorN.ndim = 2
        Traceback (most recent call last):
            ...
        AttributeError: attribute ndim is a read only class attribute and cannot be modified on class VectorN
        >>> V.ndim = 2
        Traceback (most recent call last):
            ...
        AttributeError: 'VectorN' object attribute 'ndim' is read-only

        It's protected against initialization or resizing to a shape that wouldn't be a VectorN anymore

        >>> V = VectorN([[0, 1], [2, 3]])
        Traceback (most recent call last):
            ...
        TypeError: cannot initialize a VectorN of shape (4,) from [[0, 1], [2, 3]] of shape (2, 2),
        as it would truncate data or reduce the number of dimensions

        >>> V.resize((2, 2))
        Traceback (most recent call last):
            ...
        TypeError: new shape (2, 2) is not compatible with class VectorN

        Other Array types can be cast to VectorN, but truncating data or reducing dimensions is not allowed
        to avoid silent loss of data in a conversion, use an explicit resize / trim / sub-array extraction

        >>> A = Array(range(4), shape=(4,))
        >>> V = VectorN(A)
        >>> V
        VectorN([0, 1, 2, 3])

        >>> A = Array(range(4), shape=(2, 2))
        >>> V = VectorN(A)
        Traceback (most recent call last):
            ...
        TypeError: cannot cast a Array of shape (2, 2) to a VectorN of shape (4,),
        as it would truncate data or reduce the number of dimensions

        As for Array, __init__ is a shallow copy, note that as VectorN don't have sub-arrays,
        shallow and deep copy amounts to the same thing.

        >>> A = Array(range(4), shape=(4,))
        >>> V = VectorN(A)
        >>> V == A
        False
        >>> V is A
        False
        >>> V.isEquivalent(A)
        True
        >>> V[0] == A[0]
        True
        >>> V[0] is A[0]
        True
    """
    __slots__ = ['_data', '_shape', '_size']

    #A VectorN is a one-dimensional Array, ndim is thus stored as a class readonly attribute
    ndim = 1

    def _getshape(self):
        return (len(self),)
    def _setshape(self, newshape):
        self.resize(newshape)
    # shape, ndim, size and data properties
    shape = property(_getshape, _setshape, None,
                     """ v.shape : tuple of one int

                         Shape of the VectorN, as Vectors are one-dimensional Arrays: v.shape = (v.size,).

                         It can be queried, or set to change the VectorN's shape similarly to the resize method,
                         as the only way to change a VectorN's shape is to resize it.

                         >>> V = VectorN(1, 2, 3)
                         >>> V
                         VectorN([1, 2, 3])
                         >>> V.shape=(4)
                         >>> V
                         VectorN([1, 2, 3, 0])
                         >>> V.shape=(2, 2)
                         Traceback (most recent call last):
                             ...
                         TypeError: new shape (2, 2) is not compatible with class VectorN

                         Related : see Array.resize method.
                     """)
    # ndim = property(lambda x : 1, None, None, "A VectorN is a one-dimensional Array")
    size = property(lambda x : len(x), None, None, "Number of components in the VectorN")

    # common operators are herited from Arrays

    # overloaded operators
    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b

            If b is a VectorN, __mul__ is mapped to the dot product of the two vectors a and b,
            If b is a MatrixN, __mul__ is mapped to VectorN a by MatrixN b multiplication (post multiplication or transformation of a by b),
            otherwise, returns the result of the element wise multiplication of a and b if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value
        """
        if isinstance(other, VectorN) :
            return self.dot(other)
        elif isinstance(other, MatrixN) :
            # will defer to MatrixN rmul
            return NotImplemented
        else :
            # will defer to Array.__mul__
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a

            If b is a VectorN, __rmul__ is mapped to the dot product of the two vectors a and b,
            If b is a MatrixN, __rmul__ is mapped to MatrixN b by VectorN a multiplication,
            otherwise, returns the result of the element wise multiplication of b and a if b is convertible to Array,
            multiplies every component of a by b if b is a single numeric value
        """
        if isinstance(other, VectorN) :
            return self.dot(other)
        elif isinstance(other, MatrixN) :
            # will defer to MatrixN mul
            return NotImplemented
        else :
            # will defer to Array.__rmul__
            return Array.__rmul__(self, other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b

            In place multiplication of VectorN a and b, see __mul__, result must fit a's type
        """
        res = self*other
        if isinstance(res, self.__class__) :
            return self.__class__(res)
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))

    # special operators
    def __xor__(self, other):
        """ a.__xor__(b) <==> a^b

            Defines the cross product operator between two vectors,
            if b is a MatrixN, a^b is equivalent to transforming a by the inverse transpose MatrixN of b,
            often used to transform normals
        """
        if isinstance(other, VectorN) :
            return self.cross(other)
        elif isinstance(other, MatrixN) :
            return self.transformAsNormal(other)
        else :
            return NotImplemented
    def __ixor__(self, other):
        """ a.__xor__(b) <==> a^=b

            Inplace cross product or transformation by inverse transpose MatrixN of b is v is a MatrixN
        """
        res = self.__xor__(other)
        if isinstance(res, self.__class__) :
            return self.__class__(res)
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))

    # additional methods

    def cross(self, other):
        """ u.cross(v) <==> cross(u, v)

            cross product of u and v, u and v should be 3 dimensional vectors.

        """
        try :
            nself, nother = coerce(VectorN(self), other)
            assert len(nself) == len(nother) == 3
        except :
            raise TypeError, "%s not convertible to %s, cross product is only defined for two Vectors of size 3" % (clsname(other), clsname(self))
        return VectorN([nself[1]*nother[2] - nself[2]*nother[1],
                nself[2]*nother[0] - nself[0]*nother[2],
                nself[0]*nother[1] - nself[1]*nother[0]])
    def dot(self, other):
        """ u.dot(v) <==> dot(u, v)

            dot product of u and v, u and v should be Vectors of identical size.


        """
        try :
            nself, nother = coerce(VectorN(self), other)
            assert len(nself) == len(nother)
        except :
            raise TypeError, "%s not convertible to %s, dot product is only defined for two Vectors of identical size" % (clsname(other), clsname(self))
        return reduce(operator.add, map(operator.mul, nself, nother))
    def outer(self, other):
        """ u.outer(v) <==> outer(u, v)

            Outer product of vectors u and v
        """
        try :
            nself, nother = coerce(VectorN(self), other)
        except :
            raise TypeError, "%s not convertible to %s, outer product is only defined for two Vectors" % (clsname(other), clsname(self))
        return MatrixN([nother*x for x in nself])
    def transformAsNormal(self, other):
        """ u.transformAsNormal(m) --> VectorN

            Equivalent to transforming u by the inverse transpose MatrixN of m, used to transform normals.

        """
        try :
            nother = MatrixN(other)
        except :
            raise TypeError, "%s not convertible to MatrixN" % (clsname(other))
        return nother.transpose().inverse().__rmul__(self)

    # min, max etc methods derived from array

    # length methods can be more efficient than for Arrays as there is only one axis
    def sqlength(self):
        """ u.sqlength() --> float

            Returns the square length of u, ie u.dot(u).

        """
        return reduce(operator.add, map(lambda x:x**2, self))
    def length(self):
        """ u.length() --> float

            Returns the length of u, ie sqrt(u.dot(u))

        """
        return sqrt(self.sqlength())
    def normal(self):
        """ u.normal() --> VectorN

            Returns a normalized copy of self. Overriden to be consistant with Maya API and MEL unit command,
            does not raise an exception if self if of zero length, instead returns a copy of self

        """
        try :
            return self/self.length()
        except :
            return self
    unit = normal
    def isParallel(self, other, tol=eps):
        """ u.isParallel(v[, tol]) --> bool

            Returns True if both arguments considered as VectorN are parallel within the specified tolerance
        """
        try :
            nself, nother = coerce(VectorN(self), other)
        except :
            raise TypeError, "%s not convertible to %s, isParallel is only defined for two Vectors" % (clsname(other), clsname(self))
        return (abs(nself.dot(nother) - nself.length()*nother.length()) <= tol)
    def angle(self, other, third=None):
        """ u.angle(v) <==> angle(u, v) --> float

            Returns the angle of rotation between u and v, 3 dimensional Vectors representing 3D vectors.

            Note : this angle is not signed, use axis to know the direction of the rotation

            Alternatively can use the form a.angle(b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
            it is then equivalent to angle(b-a, c-a)

        """
        if third is not None :
            try :
                nself, nother = coerce(VectorN(self), other)
                nself, nthird = coerce(VectorN(self), third)
                assert len(nself) == len(nother) == len(nthird) == 4
            except :
                raise TypeError, "angle is defined for 3 vectors of size 4 representing 3D points"
            nself, nother = (nother-nself)[:3], (nthird-nself)[:3]
        else :
            try :
                nself, nother = coerce(VectorN(self), other)
                assert len(nself) == len(nother) == 3
            except :
                raise TypeError, "angle is defined for 2 vectors of size 3 representing 3D vectors"
        l = float(nself.length() * nother.length())
        if l > 0 :
            return acos( nself.dot(nother) / l )
        else :
            return 0.0
    def axis(self, other, third=None, normalize=False):
        """ u.axis(v[, normalize=False]) <==> axis(u, v[, normalize=False])

            Returns the axis of rotation from u to v as the vector n = u ^ v, u and v
            being 3 dimensional Vectors representing 3D vectors.
            If the normalize keyword argument is set to True, n is also normalized.


            Alternatively can use the form a.axis(b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
            it is then equivalent to axis(b-a, c-a).

        """
        if third is not None :
            try :
                nself, nother = coerce(VectorN(self), other)
                nself, nthird = coerce(VectorN(self), third)
                assert len(nself) == len(nother) == len(nthird) == 4
            except :
                raise TypeError, "axis is defined for 3 vectors of size 4 representing 3D points"
            nself, nother = (nother-nself)[:3], (nthird-nself)[:3]
        else :
            try :
                nself, nother = coerce(VectorN(self), other)
                assert len(nself) == len(nother) == 3
            except :
                raise TypeError, "axis is defined for 2 vectors of size 3 representing 3D vectors"
        if normalize :
            return nself.cross(nother).normal()
        else :
            return nself.cross(nother)
    def cotan(self, other, third=None):
        """ u.cotan(v) <==> cotan(u, v)

            Returns the cotangent of the u, v angle, u and v should be 3 dimensional Vectors representing 3D vectors.

            Alternatively can use the form a.cotan(b, c), where a, b, c are 4 dimensional Vectors representing 3D points,
            it is then equivalent to cotan(b-a, c-a)
        """
        if third is not None :
            try :
                nself, nother = coerce(VectorN(self), other)
                nself, nthird = coerce(VectorN(self), third)
                assert len(nself) == len(nother) == len(nthird) == 4
            except :
                raise TypeError, "cotan is defined for 3 vectors of size 4 representing 3D points"
            nself, nother = (nother-nself)[:3], (nthird-nself)[:3]
        else :
            try :
                nself, nother = coerce(VectorN(self), other)
                assert len(nself) == len(nother) == 3
            except :
                raise TypeError, "cotan is defined for 2 vectors of size 3 representing 3D vectors"
        return (nself.dot(nother)) / (nself.cross(nother)).length()

    def projectionOnto(self, other):
        """Returns the projection of this vector onto other vector."""
        try :
            nself, nother = coerce(VectorN(self), other)
        except :
            raise NotImplemented, "%s not convertible to %s" % (clsname(other), clsname(self))
        return VectorN( (nself.dot(nother) /  nother.sqlength()) * nother )
    # blend and clamp derived from Array



if __name__ == '__main__' :
    import doctest
    doctest.testmod(verbose=True)

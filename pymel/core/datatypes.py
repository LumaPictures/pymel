"""
A wrap of Maya's Vector, Point, Color, Matrix, TransformationMatrix, Quaternion, EulerRotation types
"""

import sys
import math
import copy
import operator
import colorsys

import pymel.util as util
import pymel.api as _api
from pymel.util.arrays import *
from pymel.util.arrays import _toCompOrArrayInstance
import pymel.internal.factories as _factories

# in python2.6/maya2010 'as' becomes a keyword.
# TODO:  add a version check:
if sys.version_info >= (2, 6):
    AS_UNITS = 'asUnits'
else:
    AS_UNITS = 'as'

# patch some Maya api classes that miss __iter__ to make them iterable / convertible to list
def _patchMVector():
    def __len__(self):
        """ Number of components in the Maya api Vector, ie 3 """
        return 3
    type.__setattr__(_api.MVector, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api Vector """
        for i in xrange(len(self)):
            yield _api.MVector.__getitem__(self, i)
    type.__setattr__(_api.MVector, '__iter__', __iter__)

def _patchMFloatVector():
    def __len__(self):
        """ Number of components in the Maya api FloatVector, ie 3 """
        return 3
    type.__setattr__(_api.MFloatVector, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api FloatVector """
        for i in xrange(len(self)):
            yield _api.MFloatVector.__getitem__(self, i)
    type.__setattr__(_api.MFloatVector, '__iter__', __iter__)

def _patchMPoint():
    def __len__(self):
        """ Number of components in the Maya api Point, ie 4 """
        return 4
    type.__setattr__(_api.MPoint, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api Point """
        for i in xrange(len(self)):
            yield _api.MPoint.__getitem__(self, i)
    type.__setattr__(_api.MPoint, '__iter__', __iter__)

def _patchMFloatPoint():
    def __len__(self):
        """ Number of components in the Maya api FloatPoint, ie 4 """
        return 4
    type.__setattr__(_api.MFloatPoint, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api FloatPoint """
        for i in xrange(len(self)):
            yield _api.MFloatPoint.__getitem__(self, i)
    type.__setattr__(_api.MFloatPoint, '__iter__', __iter__)

def _patchMColor():
    def __len__(self):
        """ Number of components in the Maya api Color, ie 4 """
        return 4
    type.__setattr__(_api.MColor, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api Color """
        for i in xrange(len(self)):
            yield _api.MColor.__getitem__(self, i)
    type.__setattr__(_api.MColor, '__iter__', __iter__)

def _patchMMatrix():
    def __len__(self):
        """ Number of rows in the Maya api Matrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MMatrix, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api Matrix """
        for r in xrange(4):
            yield Array([_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MMatrix, '__iter__', __iter__)

def _patchMFloatMatrix():
    def __len__(self):
        """ Number of rows in the Maya api FloatMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MFloatMatrix, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api FloatMatrix """
        for r in xrange(4):
            yield Array([_api.MScriptUtil.getFloatArrayItem(_api.MFloatMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MFloatMatrix, '__iter__', __iter__)

def _patchMTransformationMatrix():
    def __len__(self):
        """ Number of rows in the Maya api Matrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MTransformationMatrix, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api TransformationMatrix """
        return self.asMatrix().__iter__()
    type.__setattr__(_api.MTransformationMatrix, '__iter__', __iter__)

def _patchMQuaternion():
    def __len__(self):
        """ Number of components in the Maya api Quaternion, ie 4 """
        return 4
    type.__setattr__(_api.MQuaternion, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api Quaternion """
        for i in xrange(len(self)):
            yield _api.MQuaternion.__getitem__(self, i)
    type.__setattr__(_api.MQuaternion, '__iter__', __iter__)

def _patchMEulerRotation():
    def __len__(self):
        """ Number of components in the Maya api EulerRotation, ie 3 """
        return 3
    type.__setattr__(_api.MEulerRotation, '__len__', __len__)

    def __iter__(self):
        """ Iterates on all components of a Maya api EulerRotation """
        for i in xrange(len(self)):
            yield _api.MEulerRotation.__getitem__(self, i)
    type.__setattr__(_api.MEulerRotation, '__iter__', __iter__)

_patchMVector()
_patchMFloatVector()
_patchMPoint()
_patchMFloatPoint()
_patchMColor()
_patchMMatrix()
_patchMFloatMatrix()
_patchMTransformationMatrix()
_patchMQuaternion()
_patchMEulerRotation()

# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(_factories.MetaMayaTypeWrapper):

    """ A metaclass to wrap Maya array type classes such as Vector, Matrix """

    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as Vector or Matrix """

        if 'shape' in classdict:
            # fixed shape means also fixed ndim and size
            shape = classdict['shape']
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            if 'ndim' not in classdict:
                classdict['ndim'] = ndim
            elif classdict['ndim'] != ndim:
                raise ValueError, "class %s shape definition %s and number of dimensions definition %s do not match" % (classname, shape, ndim)
            if 'size' not in classdict:
                classdict['size'] = size
            elif classdict['size'] != size:
                raise ValueError, "class %s shape definition %s and size definition %s do not match" % (classname, shape, size)

        # create the new class
        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)

        try:
            apicls = newcls.apicls
        except:
            apicls = None
        try:
            shape = newcls.shape
        except:
            shape = None
        try:
            cnames = newcls.cnames
        except:
            cnames = ()

        if shape is not None:
            # fixed shape means also fixed ndim and size
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)

            if cnames:
                # definition for component names
                type.__setattr__(newcls, 'cnames', cnames)
                subsizes = [reduce(operator.mul, shape[i + 1:], 1) for i in xrange(ndim)]
                for index, compname in enumerate(cnames):
                    coords = []
                    for i in xrange(ndim):
                        c = index // subsizes[i]
                        index -= c * subsizes[i]
                        coords.append(c)
                    if len(coords) == 1:
                        coords = coords[0]
                    else:
                        coords = tuple(coords)


#                    def _get(self):
#                        return self.__getitem__(coords)
#                    _get.__name__ = '_get_' + compname
#
#                    # FIXME : the set property does not do anything in python 2.4 !!!  It doesn't even get called.
#
#                    def _set(self, val):
#                        self.__setitem__(coords, val)
#
#                    _set.__name__ = '_set_' + compname
#
#                    p = property( _get, _set, None, 'set and get %s component' % compname )

                    cmd = "property( lambda self: self.__getitem__(%s) ,  lambda self, val: self.__setitem__(%s,val) )" % (coords, coords)
                    p = eval(cmd)

                    if compname not in classdict:
                        type.__setattr__(newcls, compname, p)
                    else:
                        raise AttributeError, "component name %s clashes with class method %r" % (compname, classdict[compname])
        elif cnames:
            raise ValueError, "can only define component names for classes with a fixed shape/size"

        # constants for shape, ndim, size
        if shape is not None:
            type.__setattr__(newcls, 'shape', shape)
        if ndim is not None:
            type.__setattr__(newcls, 'ndim', ndim)
        if size is not None:
            type.__setattr__(newcls, 'size', size)
        #__slots__ = ['_data', '_shape', '_size']
        # add component names to read-only list
        readonly = newcls.__readonly__
        if hasattr(newcls, 'shape'):
            readonly['shape'] = None
        if hasattr(newcls, 'ndim'):
            readonly['ndim'] = None
        if hasattr(newcls, 'size'):
            readonly['size'] = None
        if 'cnames' not in readonly:
            readonly['cnames'] = None
        type.__setattr__(newcls, '__readonly__', readonly)

#        print "created class", newcls
#        print "bases", newcls.__bases__
#        print "readonly", newcls.__readonly__
#        print "slots", newcls.__slots__
        return newcls

# generic math function that can operate on Arrays herited from arrays
# (min, max, sum, prod...)

# Functions that work on vectors will now be inherited from Array and properly defer
# to the class methods


class Vector(VectorN):

    """
    A 3 dimensional vector class that wraps Maya's api Vector class

        >>> from pymel.all import *
        >>> import pymel.core.datatypes as dt
        >>>
        >>> v = dt.Vector(1, 2, 3)
        >>> w = dt.Vector(x=1, z=2)
        >>> z = dt.Vector( dt.Vector.xAxis, z=1)

        >>> v = dt.Vector(1, 2, 3, unit='meters')
        >>> print v
        [1.0, 2.0, 3.0]
    """
    __metaclass__ = MetaMayaArrayTypeWrapper
    __slots__ = ()
    # class specific info
    apicls = _api.MVector
    cnames = ('x', 'y', 'z')
    shape = (3,)
    unit = None

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (3,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on Vector, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)

        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new

    def __init__(self, *args, **kwargs):
        """ __init__ method, valid for Vector, Point and Color classes """
        cls = self.__class__

        if args:
            # allow both forms for arguments
            if len(args) == 1 and hasattr(args[0], '__iter__'):
                args = args[0]
            # shortcut when a direct api init is possible
            try:
                self.assign(args)
            except:
                # special exception to the rule that you cannot drop data in Arrays __init__
                # to allow all conversion from Vector derived classes (MPoint, MColor) to a base class
                # special case for MPoint to cartesianize if necessary
                # note : we may want to premultiply MColor by the alpha in a similar way
                if isinstance(args, _api.MPoint) and args.w != 1.0:
                    args = copy.deepcopy(args).cartesianize()
                if isinstance(args, _api.MColor) and args.a != 1.0:
                    # note : we may want to premultiply Color by the alpha in a similar way
                    pass
                if isinstance(args, _api.MVector) or isinstance(args, _api.MPoint) or isinstance(args, _api.MColor):
                    args = tuple(args)
                    if len(args) > len(self):
                        args = args[slice(self.shape[0])]
                super(Vector, self).__init__(*args)

        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)):
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames):
                if c in kwargs:
                    if float(l[i]) != float(kwargs[c]):
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp:
                try:
                    self.assign(l)
                except:
                    msg = ", ".join(map(lambda x, y: x + "=<" + util.clsname(y) + ">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)

        # units handling
        self.unit = kwargs.get('unit', None)
        if self.unit is not None:
            self.assign([Distance(x, self.unit) for x in self])

    def __repr__(self):
        if hasattr(self, 'unit') and self.unit:
            return "dt.%s(%s, unit='%s')" % (self.__class__.__name__, str(self), self.unit)
        else:
            return "dt.%s(%s)" % (self.__class__.__name__, str(self))

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
    # here, there is no _data attribute as we subclass _api.MVector directly, thus v.data is v
    # for wraps

    def _getdata(self):
        return self.apicls(self)

    def _setdata(self, value):
        self.assign(value)

    def _deldata(self):
        if hasattr(self.apicls, 'clear'):
            self.apicls.clear(self)
        else:
            raise TypeError, "cannot clear stored elements of %s" % (self.__class__.__name__)

    data = property(_getdata, _setdata, _deldata, "The Vector/FloatVector/Point/FloatPoint/Color data")

    # overloads for assign and get though standard way should be to use the data property
    # to access stored values

    def assign(self, value):
        """ Wrap the Vector api assign method """
        # don't accept instances as assign works on exact types
        if type(value) != self.apicls and type(value) != type(self):
            if not hasattr(value, '__iter__'):
                value = (value,)
            value = self.apicls(*value)
        self.apicls.assign(self, value)
        return self

    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the Vector api get method """
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        l = (0,) * self.size
        ms.createFromDouble(*l)
        p = ms.asDoublePtr()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem(p, i) for i in xrange(self.size)])

    def __len__(self):
        """ Number of components in the Vector instance, 3 for Vector, 4 for Point and Color """
        return self.apicls.__len__(self)

    # __getitem__ / __setitem__ override

    # faster to override __getitem__ cause we know Vector only has one dimension
    def __getitem__(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__'):
            i = list(i)
            if len(i) == 1:
                i = i[0]
            else:
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice):
            return _toCompOrArrayInstance(list(self)[i], VectorN)
            try:
                return _toCompOrArrayInstance(list(self)[i], VectorN)
            except:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else:
            if i < 0:
                i = self.size + i
            if i < self.size and not i < 0:
                if hasattr(self.apicls, '__getitem__'):
                    return self.apicls.__getitem__(self, i)
                else:
                    return list(self)[i]
            else:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    # as _api.Vector has no __setitem__ method, so need to reassign the whole Vector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = VectorN(self)
        v.__setitem__(i, a)
        self.assign(v)

    # iterator override

    # TODO : support for optional __iter__ arguments
    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        return self.apicls.__iter__(self.data)

    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()

    # common operators without an api equivalent are herited from VectorN

    # operators using the Maya API when applicable, but that can delegate to VectorN

    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v
            Equivalence test """
        try:
            return bool(self.apicls.__eq__(self, other))
        except Exception:
            return bool(super(Vector, self).__eq__(other))

    def __ne__(self, other):
        """ u.__ne__(v) <==> u != v
            Equivalence test """
        return (not self.__eq__(other))

    def __neg__(self):
        """ u.__neg__() <==> -u
            The unary minus operator. Negates the value of each of the components of u """
        return self.__class__(self.apicls.__neg__(self))

    def __add__(self, other):
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__add__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__add__(other))

    def __radd__(self, other):
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__radd__(other))

    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try:
            return self.__class__(self.__add__(other))
        except Exception:
            return NotImplemented

    def __sub__(self, other):
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is convertible to a VectorN (element-wise substration),
            substract v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__sub__(other))

    def __rsub__(self, other):
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is convertible to a VectorN (element-wise substration),
            replace every component c of u by v-c if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__rsub__(other))

    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        try:
            return self.__class__(self.__sub__(other))
        except Exception:
            return NotImplemented

    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the division of u by v if v is convertible to a VectorN (element-wise division),
            divide every component of u by v if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__div__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__div__(other))

    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of of the division of v by u if v is convertible to a VectorN (element-wise division),
            invert every component of u and multiply it by v if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__rdiv__(self, other))
        except Exception:
            return self.__class__._convert(super(Vector, self).__rdiv__(other))

    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """
        try:
            return self.__class__(self.__div__(other))
        except Exception:
            return NotImplemented
    # action depends on second object type

    def __mul__(self, other):
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the transformation of u by matrix v when v is a MatrixN,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try:
            res = self.apicls.__mul__(self, other)
            assert res is not NotImplemented
        except Exception:
            res = super(Vector, self).__mul__(other)
        if util.isNumeric(res) or res is NotImplemented:
            return res
        else:
            return self.__class__._convert(res)

    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the left side multiplication (pre-multiplication) of u by matrix v when v is a MatrixN,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try:
            res = self.apicls.__rmul__(self, other)
        except:
            res = super(Vector, self).__rmul__(other)
        if util.isNumeric(res):
            return res
        else:
            return self.__class__._convert(res)

    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for Vector * Matrix multiplication, in place transformation of u by Matrix v
            or Vector by scalar multiplication only """
        try:
            return self.__class__(self.__mul__(other))
        except:
            return NotImplemented
    # special operators

    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two 3D vectors,
            if v is a MatrixN, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, VectorN):
            return self.cross(other)
        elif isinstance(other, MatrixN):
            return self.transformAsNormal(other)
        else:
            return NotImplemented

    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a MatrixN """
        try:
            return self.__class__(self.__xor__(other))
        except:
            return NotImplemented

    # wrap of other API MVector methods, we use the api method if possible and delegate to Vector else

    def isEquivalent(self, other, tol=None):
        """ Returns true if both arguments considered as Vector are equal within the specified tolerance """
        if tol is None:
            tol = _api.MVector_kTol
        try:
            nself, nother = coerce(self, other)
        except:
            return False
        if isinstance(nself, Vector):
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else:
            return bool(super(Vector, nself).isEquivalent(nother, tol))

    def isParallel(self, other, tol=None):
        """ Returns true if both arguments considered as Vector are parallel within the specified tolerance """
        if tol is None:
            tol = _api.MVector_kTol
        try:
            return bool(self.apicls.isParallel(Vector(self), Vector(other), tol))
        except:
            return super(Vector, self).isParallel(other, tol)

    def distanceTo(self, other):
        try:
            return self.apicls.distanceTo(Point(self), Point(other))
        except:
            return super(Vector, self).dist(other)

    def length(self):
        """ Return the length of the vector """
        return Vector.apicls.length(Vector(self))

    def sqlength(self):
        """ Return the square length of the vector """
        return self.dot(self)

    def normal(self):
        """ Return a normalized copy of self """
        return self.__class__(Vector.apicls.normal(Vector(self)))

    def normalize(self):
        """ Performs an in place normalization of self """
        if type(self) is Vector:
            Vector.apicls.normalize(self)
        else:
            self.assign(self.normal())

    # additional api methods that work on Vector only, and don't have an equivalent on VectorN

    def rotateTo(self, other):
        """ u.rotateTo(v) --> Quaternion
            Returns the Quaternion that represents the rotation of the Vector u into the Vector v
            around their mutually perpendicular axis. It amounts to rotate u by angle(u, v) around axis(u, v) """
        if isinstance(other, Vector):
            return Quaternion(Vector.apicls.rotateTo(Vector(self), Vector(other)))
        else:
            raise TypeError, "%r is not a Vector instance" % other

    def rotateBy(self, *args):
        """ u.rotateBy(*args) --> Vector
            Returns the result of rotating u by the specified arguments.
            There are several ways the rotation can be specified:
            args is a tuple of one Matrix, TransformationMatrix, Quaternion, EulerRotation
            arg is tuple of 4 arguments, 3 rotation value and an optionnal rotation order
            args is a tuple of one Vector, the axis and one float, the angle to rotate around that axis in radians"""
        if args:
            if len(args) == 2 and isinstance(args[0], Vector):
                return self.__class__(self.apicls.rotateBy(self, Quaternion(Vector(args[0]), float(args[1]))))
            elif len(args) == 1 and isinstance(args[0], Matrix):
                return self.__class__(self.apicls.rotateBy(self, args[0].rotate))
            else:
                return self.__class__(self.apicls.rotateBy(self, EulerRotation(unit='radians', *args)))
        else:
            return self

#    def asUnit(self, unit) :
#        #kUnit = Distance.kUnit(unit)
#        return self.__class__( [ Distance(x).asUnit(unit) for x in self ]  )
#
#    def asUnit(self) :
#        return self.asUnit(self.unit)
#
#    def asUIUnit()nits()self) :
#        return self.asUnit(Distance.getUIUnit())
#
#    def asInternalUnit(self) :
#        return self.asUnit(Distance.getInternalUnit())
#
#    def asMillimeter(self) :
#        return self.asUnit('millimeter')
#    def asCentimeters(self) :
#        return self.asUnit('centimeters')
#    def asKilometers(self) :
#        return self.asUnit('kilometers')
#    def asMeters(self) :
#        return self.asUnit('meters')
#
#    def asInches(self) :
#        return self.asUnit('inches')
#    def asFeet(self) :
#        return self.asUnit('feet')
#    def asYards(self) :
#        return self.asUnit('yards')
#    def asMiles(self) :
#        return self.asUnit('miles')

    # additional api methods that work on Vector only, but can also be delegated to VectorN

    def transformAsNormal(self, other):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, Matrix):
            return self.__class__._convert(Vector.apicls.transformAsNormal(Vector(self), Matrix(other)))
        else:
            return self.__class__._convert(super(Vector, self).transformAsNormal(other))

    def dot(self, other):
        """ dot product of two vectors """
        if isinstance(other, Vector):
            return Vector.apicls.__mul__(Vector(self), Vector(other))
        else:
            return super(Vector, self).dot(other)

    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, Vector):
            return self.__class__._convert(Vector.apicls.__xor__(Vector(self), Vector(other)))
        else:
            return self.__class__._convert(super(Vector, self).cross(other))

    def axis(self, other, normalize=False):
        """ u.axis(v) <==> angle(u, v) --> Vector
            Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, Vector):
            if normalize:
                return self.__class__._convert(Vector.apicls.__xor__(Vector(self), Vector(other)).normal())
            else:
                return self.__class__._convert(Vector.apicls.__xor__(Vector(self), Vector(other)))
        else:
            return self.__class__._convert(super(Vector, self).axis(other, normalize))

    def angle(self, other):
        """ u.angle(v) <==> angle(u, v) --> float
            Returns the angle (in radians) between the two vectors u and v
            Note that this angle is not signed, use axis to know the direction of the rotation """
        if isinstance(other, Vector):
            return Vector.apicls.angle(Vector(self), Vector(other))
        else:
            return super(Vector, self).angle(other)

    # methods without an api equivalent

    # cotan on MVectors only takes 2 arguments
    def cotan(self, other):
        """ u.cotan(v) <==> cotan(u, v) --> float :
            cotangent of the a, b angle, a and b should be MVectors"""
        return VectorN.cotan(self, other)

    # rest derived from VectorN class

class FloatVector(Vector):

    """ A 3 dimensional vector class that wraps Maya's api FloatVector class,
        It behaves identically to Vector, but it also derives from api's FloatVector
        to keep api methods happy
        """
    apicls = _api.MFloatVector

# Point specific functions

def planar(p, *args, **kwargs):
    """ planar(p[, q, r, s (...), tol=tolerance]) --> bool
        Returns True if all provided MPoints are planar within given tolerance """
    if not isinstance(p, Point):
        try:
            p = Point(p)
        except:
            raise TypeError, "%s is not convertible to type Point, planar is only defined for n MPoints" % (util.clsname(p))
    return p.planar(*args, **kwargs)
def center(p, *args):
    """ center(p[, q, r, s (...)]) --> Point
        Returns the Point that is the center of p, q, r, s (...) """
    if not isinstance(p, Point):
        try:
            p = Point(p)
        except:
            raise TypeError, "%s is not convertible to type Point, center is only defined for n MPoints" % (util.clsname(p))
    return p.center(*args)
def bWeights(p, *args):
    """ bWeights(p[, p0, p1, (...), pn]) --> tuple
        Returns a tuple of (n0, n1, ...) normalized barycentric weights so that n0*p0 + n1*p1 + ... = p  """
    if not isinstance(p, Point):
        try:
            p = Point(p)
        except:
            raise TypeError, "%s is not convertible to type Point, bWeights is only defined for n MPoints" % (util.clsname(p))
    return p.bWeights(*args)


class Point(Vector):

    """ A 4 dimensional vector class that wraps Maya's api Point class,
        """
    apicls = _api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a cartesian 3D point """
        return self.cartesian()

#    # base methods are inherited from Vector

    # we only show the x, y, z components on an iter
    def __len__(self):
        l = len(self.data)
        if self.w == 1.0:
            l -= 1
        return l

    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        l = len(self)
        for c in list(self.apicls.__iter__(self.data))[:l]:
            yield c

    # modified operators, when adding 2 Point consider second as Vector
    def __add__(self, other):
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        # prb with coerce when delegating to VectorN, either redefine coerce for Point or other fix
        # if isinstance(other, Point) :
        #    other = Vector(other)
        try:
            other = Vector(other)
        except:
            pass
        try:
            return self.__class__._convert(self.apicls.__add__(self, other))
        except:
            return self.__class__._convert(super(Vector, self).__add__(other))

    def __radd__(self, other):
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        if isinstance(other, Point):
            other = Vector(other)
        try:
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except:
            return self.__class__._convert(super(Point, self).__radd__(other))

    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try:
            return self.__class__(self.__add__(other))
        except:
            return NotImplemented

    # specific api methods
    def cartesianize(self):
        """ p.cartesianize() --> Point
            If the point instance p is of the form P(W*x, W*y, W*z, W), for some scale factor W != 0,
            then it is reset to be P(x, y, z, 1).
            This will only work correctly if the point is in homogenous form or cartesian form.
            If the point is in rational form, the results are not defined. """
        return self.__class__(self.apicls.cartesianize(self))

    def cartesian(self):
        """ p.cartesian() --> Point
            Returns the cartesianized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.cartesianize(t)
        return t

    def rationalize(self):
        """ p.rationalize() --> Point
            If the point instance p is of the form P(W*x, W*y, W*z, W) (ie. is in homogenous or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(x, y, z, W).
            This will only work correctly if the point is in homogenous or cartesian form.
            If the point is already in rational form, the results are not defined. """
        return self.__class__(self.apicls.rationalize(self))

    def rational(self):
        """ p.rational() --> Point
            Returns the rationalized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.rationalize(t)
        return t

    def homogenize(self):
        """ p.homogenize() --> Point
            If the point instance p is of the form P(x, y, z, W) (ie. is in rational or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(W*x, W*y, W*z, W). """
        return self.__class__(self.apicls.homogenize(self))

    def homogen(self):
        """ p.homogen() --> Point
            Returns the homogenized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.homogenize(t)
        return t

    # additionnal methods

    def isEquivalent(self, other, tol=None):
        """ Returns true if both arguments considered as Point are equal within the specified tolerance """
        if tol is None:
            tol = _api.MPoint_kTol
        try:
            nself, nother = coerce(self, other)
        except:
            return False
        if isinstance(nself, Point):
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else:
            return bool(super(Point, nself).isEquivalent(nother, tol))

    def axis(self, start, end, normalize=False):
        """ a.axis(b, c) --> Vector
            Returns the axis of rotation from point b to c around a as the vector n = (b-a)^(c-a)
            if the normalize keyword argument is set to True, n is also normalized """
        return Vector.axis(start - self, end - self, normalize=normalize)

    def angle(self, start, end):
        """ a.angle(b, c) --> float
            Returns the angle (in radians) of rotation from point b to c around a.
            Note that this angle is not signed, use axis to know the direction of the rotation """
        return Vector.angle(start - self, end - self)

    def cotan(self, start, end):
        """ a.cotan(b, c) --> float :
            cotangent of the (b-a), (c-a) angle, a, b, and c should be MPoints representing points a, b, c"""
        return VectorN.cotan(start - self, end - self)

    def planar(self, *args, **kwargs):
        """ p.planar(q, r, s (...), tol=tolerance) --> bool
            Returns True if all provided points are planar within given tolerance """
        if len(args) > 2:
            tol = kwargs.get('tol', None)
            n = (args[0] - self) ^ (args[1] - self)
            return reduce(operator.and_, map(lambda x: n.isParallel(x, tol), [(args[0] - self) ^ (a - self) for a in args[2:]]), True)
        else:
            return True

    def center(self, *args):
        """ p.center(q, r, s (...)) --> Point
            Returns the Point that is the center of p, q, r, s (...) """
        return sum((self,) + args) / float(len(args) + 1)

    def bWeights(self, *args):
        """ p.bWeights(p0, p1, (...), pn) --> tuple
            Returns a tuple of (n0, n1, ...) normalized barycentric weights so that n0*p0 + n1*p1 + ... = p.
            This method works for n points defining a concave or convex n sided face,
            always returns positive normalized weights, and is continuous on the face limits (on the edges),
            but the n points must be coplanar, and p must be inside the face delimited by (p0, ..., pn) """
        if args:
            p = self
            q = list(args)
            np = len(q)
            w = VectorN(0.0, size=np)
            weightSum = 0.0
            pOnEdge = False
            tol = _api.MPoint_kTol
            # all args should be MPoints
            for i in xrange(np):
                if not isinstance(q[i], Point):
                    try:
                        q[i] = Point(q[i])
                    except:
                        raise TypeError, "cannot convert %s to Point, bWeights is defined for n MPoints" % (util.clsname(q[i]))
            # if p sits on an edge, it' a limit case and there is an easy solution,
            # all weights are 0 but for the 2 edge end points
            for i in xrange(np):
                next = (i + 1) % np

                e = ((q[next] - q[i]) ^ (p - q[i])).sqlength()
                l = (q[next] - q[i]).sqlength()
                if e <= (tol * l):
                    if l < tol:
                        # p is on a 0 length edge, point and next point are on top of each other, as is p then
                        w[i] = 0.5
                        w[next] = 0.5
                    else:
                        # p is somewhere on that edge between point and next point
                        di = (p - q[i]).length()
                        w[next] = float(di / sqrt(l))
                        w[i] = 1.0 - w[next]
                    # in both case update the weights sum and mark p as being on an edge,
                    # problem is solved
                    weightSum += 1.0
                    pOnEdge = True
                    break
            # If p not on edge, use the cotangents method
            if not pOnEdge:
                for i in xrange(np):
                    prev = (i + np - 1) % np
                    next = (i + 1) % np

                    lenSq = (p - q[i]).sqlength()
                    w[i] = (q[i].cotan(p, q[prev]) + q[i].cotan(p, q[next])) / lenSq
                    weightSum += w[i]

            # then normalize result
            if abs(weightSum):
                w /= weightSum
            else:
                raise ValueError, "failed to compute bWeights for %s and %s.\nThe point bWeights are computed for must be inside the planar face delimited by the n argument points" % (self, args)

            return tuple(w)
        else:
            return ()


class FloatPoint(Point):

    """ A 4 dimensional vector class that wraps Maya's api FloatPoint class,
        It behaves identically to Point, but it also derives from api's FloatPoint
        to keep api methods happy
        """
    apicls = _api.MFloatPoint


class Color(Vector):

    """ A 4 dimensional vector class that wraps Maya's api Color class,
        It stores the r, g, b, a components of the color, as normalized (Python) floats
        """
    apicls = _api.MColor
    cnames = ('r', 'g', 'b', 'a')
    shape = (4,)
    # modes = ('rgb', 'hsv', 'cmy', 'cmyk')
    modes = ('rgb', 'hsv')

    # constants
    red = _api.MColor(1.0, 0.0, 0.0)
    green = _api.MColor(0.0, 1.0, 0.0)
    blue = _api.MColor(0.0, 0.0, 1.0)
    white = _api.MColor(1.0, 1.0, 1.0)
    black = _api.MColor(0.0, 0.0, 0.0)
    opaque = _api.MColor(0.0, 0.0, 0.0, 1.0)
    clear = _api.MColor(0.0, 0.0, 0.0, 0.0)

    # static methods
    @staticmethod
    def rgbtohsv(c):
        c = tuple(c)
        return tuple(colorsys.rgb_to_hsv(*clamp(c[:3])) + c[3:4])

    @staticmethod
    def hsvtorgb(c):
        c = tuple(c)
        # return colorsys.hsv_to_rgb(clamp(c[0]), clamp(c[1]), clamp(c[2]))
        return tuple(colorsys.hsv_to_rgb(*clamp(c[:3])) + c[3:4])

    # TODO : could define rgb and hsv iterators and allow __setitem__ and __getitem__ on these iterators
    # like (it's more simple) it's done in ArrayIter
    def _getrgba(self):
        return tuple(self)

    def _setrgba(self, value):
        if not hasattr(value, '__iter__'):
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,) * 4
        l = list(self)
        for i, v in enumerate(value[:4]):
            if v is not None:
                l[i] = float(v)
        self.assign(*l)
    rgba = property(_getrgba, _setrgba, None, "The r,g,b,a Color components""")

    def _getrgb(self):
        return self.rgba[:3]

    def _setrgb(self, value):
        if not hasattr(value, '__iter__'):
            value = (value,) * 3
        self.rgba = value[:3]
    rgb = property(_getrgb, _setrgb, None, "The r,g,b Color components""")

    def _gethsva(self):
        return tuple(Color.rgbtohsv(self))

    def _sethsva(self, value):
        if not hasattr(value, '__iter__'):
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,) * 4
        l = list(Color.rgbtohsv(self))
        for i, v in enumerate(value[:4]):
            if v is not None:
                l[i] = float(v)
        self.assign(*Color.hsvtorgb(self))
    hsva = property(_gethsva, _sethsva, None, "The h,s,v,a Color components""")

    def _gethsv(self):
        return tuple(Color.rgbtohsv(self))[:3]

    def _sethsv(self, value):
        if not hasattr(value, '__iter__'):
            value = (value,) * 3
        self.hsva = value[:3]
    hsv = property(_gethsv, _sethsv, None, "The h,s,v,a Color components""")

    def _geth(self):
        return self.hsva[0]

    def _seth(self, value):
        self.hsva = (value, None, None, None)
    h = property(_geth, _seth, None, "The h Color component""")

    def _gets(self):
        return self.hsva[1]

    def _sets(self, value):
        self.hsva = (None, value, None, None)
    s = property(_gets, _sets, None, "The s Color component""")

    def _getv(self):
        return self.hsva[2]

    def _setv(self, value):
        self.hsva = (None, None, value, None)
    v = property(_getv, _setv, None, "The v Color component""")

    # __new__ is herited from Point/Vector, need to override __init__ to accept hsv mode though

    def __init__(self, *args, **kwargs):
        """ Init a Color instance
            Can pass one argument being another Color instance , or the color components """
        cls = self.__class__
        mode = kwargs.get('mode', None)
        if mode is not None and mode not in cls.modes:
            raise ValueError, "unknown mode %s for %s" % (mode, util.clsname(self))
        # can also use the form <componentname>=<number>
        # for now supports only rgb and hsv flags
        hsvflag = {}
        rgbflag = {}
        for a in 'hsv':
            if a in kwargs:
                hsvflag[a] = kwargs[a]
        for a in 'rgb':
            if a in kwargs:
                rgbflag[a] = kwargs[a]
        # can't mix them
        if hsvflag and rgbflag:
            raise ValueError, "can not mix r,g,b and h,s,v keyword arguments in a %s declaration" % util.clsname(self)
        # if no mode specified, guess from what keyword arguments where used, else use 'rgb' as default
        if mode is None:
            if hsvflag:
                mode = 'hsv'
            else:
                mode = 'rgb'
        # can't specify a mode and use keywords of other modes
        if mode is not 'hsv' and hsvflag:
            raise ValueError, "Can not use h,s,v keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        elif mode is not 'rgb' and rgbflag:
            raise ValueError, "Can not use r,g,b keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        # NOTE: do not try to use mode with _api.Color, it seems bugged as of 2008
            #import colorsys
            #colorsys.rgb_to_hsv(0.0, 0.0, 1.0)
            ## Result: (0.66666666666666663, 1.0, 1.0) #
            #c = _api.Color(_api.Color.kHSV, 0.66666666666666663, 1.0, 1.0)
            # print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 0.666666686535 1.0 1.0  #
            #c = _api.Color(_api.Color.kHSV, 0.66666666666666663*360, 1.0, 1.0)
            # print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 240.0 1.0 1.0  #
            #colorsys.hsv_to_rgb(0.66666666666666663, 1.0, 1.0)
            ## Result: (0.0, 0.0, 1.0) #
        # we'll use Color only to store RGB values internally and do the conversion a read/write if desired
        # which I think make more sense anyway
        # quantize (255, 65535, no quantize means colors are 0.0-1.0 float values)
        # Initializing api's Color with int values seems also not to always behave so we quantize first and
        # use a float init always
        quantize = kwargs.get('quantize', None)
        if quantize is not None:
            try:
                quantize = float(quantize)
            except:
                raise ValueError, "quantize must be a numeric value, not %s" % (util.clsname(quantize))
        # can be initilized with a single argument (other Color, Vector, VectorN)
        if len(args) == 1:
            args = args[0]
        # we dont rely much on Color api as it doesn't seem totally finished, and do some things directly here
        if isinstance(args, self.__class__) or isinstance(args, self.apicls):
            # alternatively could be just ignored / output as warning
            if quantize:
                raise ValueError, "Can not quantize a Color argument, a Color is always stored internally as float color" % (mode, util.clsname(self))
            if mode == 'rgb':
                args = VectorN(args)
            elif mode == 'hsv':
                args = VectorN(cls.rgbtohsv(args))
        else:
            # single alpha value, as understood by api will break coerce behavior in operations
            # where other operand is a scalar
            # if not hasattr(args, '__iter__') :
            #    args = VectorN(0.0, 0.0, 0.0, args)
            if hasattr(args, '__len__'):
                shape = (min(len(args), cls.size),)
            else:
                shape = cls.shape
            args = VectorN(args, shape=shape)
            # quantize if needed
            if quantize:
                args /= quantize
            # pad to a full Color size
            args.stack(self[len(args):])

        # apply keywords arguments, and convert if mode is not rgb
        if mode == 'rgb':
            if rgbflag:
                for i, a in enumerate('rgb'):
                    if a in rgbflag:
                        if quantize:
                            args[i] = float(rgbflag[a]) / quantize
                        else:
                            args[i] = float(rgbflag[a])
        elif mode == 'hsv':
            if hsvflag:
                for i, a in enumerate('hsv'):
                    if a in hsvflag:
                        if quantize:
                            args[i] = float(hsvflag[a]) / quantize
                        else:
                            args[i] = float(hsvflag[a])
            args = VectorN(cls.hsvtorgb(args))
        # finally alpha keyword
        a = kwargs.get('a', None)
        if a is not None:
            if quantize:
                args[-1] = float(a) / quantize
            else:
                args[-1] = float(a)

        try:
            self.assign(args)
        except:
            msg = ", ".join(map(lambda x, y: x + "=<" + util.clsname(y) + ">", mode, args))
            raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a 3-component color (RGB) """
        return [self.r, self.g, self.b]

    # overriden operators

    # defined for two MColors only
    def __add__(self, other):
        """ c.__add__(d) <==> c+d
            Returns the result of the addition of MColors c and d if d is convertible to a Color,
            adds d to every component of c if d is a scalar """
        # prb with coerce when delegating to VectorN, either redefine coerce for Point or other fix
        # if isinstance(other, Point) :
        #    other = Vector(other)
        try:
            other = Color(other)
        except:
            pass
        try:
            return self.__class__._convert(self.apicls.__add__(self, other))
        except:
            return self.__class__._convert(super(Vector, self).__add__(other))

    def __radd__(self, other):
        """ c.__radd__(d) <==> d+c
            Returns the result of the addition of MColors c and d if d is convertible to a Color,
            adds d to every component of c if d is a scalar """
        try:
            other = Color(other)
        except:
            pass
        try:
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except:
            return self.__class__._convert(super(Point, self).__radd__(other))

    def __iadd__(self, other):
        """ c.__iadd__(d) <==> c += d
            In place addition of c and d, see __add__ """
        try:
            return self.__class__(self.__add__(other))
        except:
            return NotImplemented

    def __sub__(self, other):
        """ c.__add__(d) <==> c+d
            Returns the result of the substraction of Color d from c if d is convertible to a Color,
            substract d from every component of c if d is a scalar """
        try:
            other = Color(other)
        except:
            pass
        try:
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except:
            return self.__class__._convert(super(Vector, self).__sub__(other))

    def __rsub__(self, other):
        """ c.__rsub__(d) <==> d-c
            Returns the result of the substraction of Color c from d if d is convertible to a Color,
            replace every component c[i] of c by d-c[i] if d is a scalar """
        try:
            other = Color(other)
        except:
            pass
        try:
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except:
            return self.__class__._convert(super(Point, self).__rsub__(other))

    def __isub__(self, other):
        """ c.__isub__(d) <==> c -= d
            In place substraction of d from c, see __sub__ """
        try:
            return self.__class__(self.__sub__(other))
        except:
            return NotImplemented
    # action depends on second object type
    # TODO : would be nice to define LUT classes and allow MColor * LUT transform
    # overloaded operators

    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a 1D sequence (Array, VectorN, Color), __mul__ is mapped to element-wise multiplication,
            If b is a MatrixN, __mul__ is similar to Point a by MatrixN b multiplication (post multiplication or transformation of a by b),
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, MatrixN):
            # will defer to MatrixN rmul
            return NotImplemented
        else:
            # will defer to Array.__mul__
            return Array.__mul__(self, other)

    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a 1D sequence (Array, VectorN, Color), __mul__ is mapped to element-wise multiplication,
            If b is a MatrixN, __mul__ is similar to MatrixN b by Point a matrix multiplication,
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, MatrixN):
            # will defer to MatrixN mul
            return NotImplemented
        else:
            # will defer to Array.__rmul__
            return Array.__rmul__(self, other)

    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of VectorN a and b, see __mul__, result must fit a's type """
        res = self * other
        if isinstance(res, self.__class__):
            return self.__class__(res)
        else:
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))

    # additionnal methods, to be extended
    def over(self, other):
        """ c1.over(c2): Composites c1 over other c2 using c1's alpha, the resulting color has the alpha of c2 """
        if isinstance(other, Color):
            a = self.a
            return Color(Vector(other).blend(Vector(self), self.a), a=other.a)
        else:
            raise TypeError, "over is defined for Color instances, not %s" % (util.clsname(other))
    # return Vector instead ? Keeping alpha doesn't make much sense

    def premult(self):
        """ Premultiply Color r, g and b by it's alpha and resets alpha to 1.0 """
        return self.__class__(Vector(self) * self.a)

    def gamma(self, g):
        """ c.gamma(g) applies gamma correction g to Color c, g can be a scalar and then will be applied to r, g, b
            or an iterable of up to 3 (r, g, b) independant gamma correction values """
        if not hasattr(g, '__iter__'):
            g = (g,) * 3 + (1.0,)
        else:
            g = g[:3] + (1.0,) * (4 - len(g[:3]))
        return gamma(self, g)

    def hsvblend(self, other, weight=0.5):
        """ c1.hsvblend(c2) --> Color
            Returns the result of blending c1 with c2 in hsv space, using the given weight """
        c1 = list(self.hsva)
        c2 = list(other.hsva)
        if abs(c2[0] - c1[0]) >= 0.5:
            if abs(c2[0] - c1[0]) == 0.5:
                c1[1], c2[1] = 0.0, 0.0
            if c1[0] > 0.5:
                c1[0] -= 1.0
            if c2[0] > 0.5:
                c2[0] -= 1.0
        c = blend(c1, c2, weight=weight)
        if c[0] < 0.0:
            c[0] += 1.0
        return self.__class__(c, mode='hsv')


# to specify space of transforms

class Space(_api.MSpace):
    apicls = _api.MSpace
    __metaclass__ = _factories.MetaMayaTypeWrapper
    pass

Spaces = Space.Space

def equivalentSpace(space1, space2, rotationOnly=False):
    '''Compare the two given space values to see if they are equal

    Parameters
    ----------
    space1 : int or str
        the first space to compare (may be either the integer enum value, or the
        api enum name - ie, "kPostTransform" - or the pymel enum name - ie,
        "postTransform" )
    space2 : int or str
        the seoncd space to compare (may be either the integer enum value, or
        the api enum name - ie, "kPostTransform" - or the pymel enum name - ie,
        "postTransform")
    rotationOnly : bool
        If true, then compare the spaces, assuming we are only considering
        rotation - in rotation, transform is the same as preTransform/object
        (the reason being that in maya, preTransform means rotation +
        translation are both defined in the preTransform/object coordinate
        system, while transform means rotation is defined in preTransform/object
        coordinates, while translate is given in the postTransform space...
        which matches the way maya applies transforms)
    '''
    translated = []
    for space in space1, space2:
        space = _factories.ApiArgUtil.castInputEnum('MSpace', 'Space', space)
        if rotationOnly:
            # for the purposes of rotations, maya treats transform and
            # preTransform/object as the same (the reason being that in maya,
            # preTransform means both rotation + translation are both defined in
            # the preTransform/object coordinate system, while transform means
            # rotation is defined in preTransform/object coordinates, while
            # translate is given in the postTransform space... which matches the
            # way maya applies transforms)
            if space == _api.MSpace.kTransform:
                space = _api.MSpace.kPreTransform
            translated.append(space)


# kInvalid
#    kTransform
# Transform matrix (relative) space
#    kPreTransform
# Pre-transform matrix (geometry)
#    kPostTransform
# Post-transform matrix (world) space
#    kWorld
# transform in world space
#    kObject
# Same as pre-transform space
#    kLast

# sadly TransformationMatrix.RotationOrder and EulerRotation.RotationOrder don't match

# class MRotationOrder(int):
#    pass

# kInvalid
#    kXYZ
#    kYZX
#    kZXY
#    kXZY
#    kYXZ
#    kZYX
#    kLast


#    kXYZ
#    kYZX
#    kZXY
#    kXZY
#    kYXZ
#    kZYX

# functions that work on MatrixN (det(), inv(), ...) herited from arrays
# and properly defer to the class methods

# For row, column order, see the definition of a TransformationMatrix in docs :
# T  = |  1    0    0    0 |
#      |  0    1    0    0 |
#      |  0    0    1    0 |
#      |  tx   ty   tz   1 |
# and m(r, c) should return value of cell at r row and c column :
# t = _api.TransformationMatrix()
# t.setTranslation(_api.Vector(1, 2, 3), _api.MSpace.kWorld)
# m = t.asMatrix()
# mm(3,0)
# 1.0
# mm(3,1)
# 2.0
# mm(3,2)
# 3.0

class Matrix(MatrixN):

    """
        A 4x4 transformation matrix based on api Matrix

        >>> from pymel.all import *
        >>> import pymel.core.datatypes as dt
        >>>
        >>> i = dt.Matrix()
        >>> print i.formated()
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]]

        >>> v = dt.Matrix(1, 2, 3)
        >>> print v.formated()
        [[1.0, 2.0, 3.0, 0.0],
         [1.0, 2.0, 3.0, 0.0],
         [1.0, 2.0, 3.0, 0.0],
         [1.0, 2.0, 3.0, 0.0]]


    """
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MMatrix
    shape = (4, 4)
    cnames = ('a00', 'a01', 'a02', 'a03',
              'a10', 'a11', 'a12', 'a13',
              'a20', 'a21', 'a22', 'a23',
              'a30', 'a31', 'a32', 'a33')

    # constants

    identity = _api.MMatrix()

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (4, 4), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on Matrix, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)

        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new

    def __init__(self, *args, **kwargs):
        """ __init__ method, valid for Vector, Point and Color classes """
        cls = self.__class__

        if args:
            # allow both forms for arguments
            if len(args) == 1 and hasattr(args[0], '__iter__'):
                args = args[0]
#            shape = kwargs.get('shape', None)
#            ndim = kwargs.get('ndim', None)
#            size = kwargs.get('size', None)
#            if shape is not None or ndim is not None or size is not None :
#                shape, ndim, size = cls._expandshape(shape, ndim, size)
#                args = MatrixN(args, shape=shape, ndim=ndim, size=size)
            # shortcut when a direct api init is possible
            try:
                self.assign(args)
            except:
                super(MatrixN, self).__init__(*args)
                # value = list(Matrix(value, shape=self.shape).flat)
                # data = self.apicls()
                # _api.MScriptUtil.createMatrixFromList ( value, data )

        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)):
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames):
                if c in kwargs:
                    if float(l[i]) != float(kwargs[c]):
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp:
                try:
                    self.assign(l)
                except:
                    msg = ", ".join(map(lambda x, y: x + "=<" + util.clsname(y) + ">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
    # here, there is no _data attribute as we subclass _api.Vector directly, thus v.data is v
    # for wraps

    def _getdata(self):
        return self

    def _setdata(self, value):
        self.assign(value)

    def _deldata(self):
        if hasattr(self.apicls, 'clear'):
            self.apicls.clear(self)
        else:
            raise TypeError, "cannot clear stored elements of %s" % (self.__class__.__name__)

    data = property(_getdata, _setdata, _deldata, "The Matrix/FloatMatrix/TransformationMatrix/Quaternion/EulerRotation data")

    # set properties for easy acces to translation / rotation / scale of a Matrix or derived class
    # some of these will only yield dependable results if Matrix is a TransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a Quaternion

    def _getTranslate(self):
        t = TransformationMatrix(self)
        return Vector(t.getTranslation(_api.MSpace.kTransform))

    def _setTranslate(self, value):
        t = TransformationMatrix(self)
        t.setTranslation(Vector(value), _api.MSpace.kTransform)
        self.assign(t.asMatrix())
    translate = property(_getTranslate, _setTranslate, None, "The translation expressed in this Matrix, in transform space")

    def _getRotate(self):
        t = TransformationMatrix(self)
        return Quaternion(t.rotation())

    def _setRotate(self, value):
        t = TransformationMatrix(self)
        q = Quaternion(value)
        t.rotateTo(q)
        # values = (q.x, q.y, q.z, q.w)
        # t.setRotationQuaternion(q.x, q.y, q.z, q.w)
        self.assign(t.asMatrix())
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this Matrix, in transform space")

    def _getScale(self):
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        t = TransformationMatrix(self)
        ms = _api.MScriptUtil()
        ms.createFromDouble(1.0, 1.0, 1.0)
        p = ms.asDoublePtr()
        t.getScale(p, _api.MSpace.kTransform)
        return Vector([ms.getDoubleArrayItem(p, i) for i in range(3)])

    def _setScale(self, value):
        t = TransformationMatrix(self)
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        ms.createFromDouble(*Vector(value))
        p = ms.asDoublePtr()
        t.setScale(p, _api.MSpace.kTransform)
        self.assign(t.asMatrix())
    scale = property(_getScale, _setScale, None, "The scale expressed in this Matrix, in transform space")

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a flat list of 16 values """
        return [x for x in self.flat]

    # some Matrix derived classes can actually be represented as matrix but not stored
    # internally as such by the API

    def asMatrix(self, percent=None):
        "The matrix representation for this Matrix/TransformationMatrix/Quaternion/EulerRotation instance"
        if percent is not None and percent != 1.0:
            if type(self) is not TransformationMatrix:
                self = TransformationMatrix(self)
            return Matrix(self.apicls.asMatrix(self, percent))
        else:
            if type(self) is Matrix:
                return self
            else:
                return Matrix(self.apicls.asMatrix(self))

    matrix = property(asMatrix, None, None, "The Matrix representation for this Matrix/TransformationMatrix/Quaternion/EulerRotation instance")

    # overloads for assign and get though standard way should be to use the data property
    # to access stored values
    def assign(self, value):
        # don't accept instances as assign works on exact _api.Matrix type
        data = None
        if type(value) == self.apicls or type(value) == type(self):
            data = value
        elif hasattr(value, 'asMatrix'):
            data = value.asMatrix()
        else:
            value = list(MatrixN(value).flat)
            if len(value) == self.size:
                data = self.apicls()
                if isinstance(data, _api.MFloatMatrix):
                    _api.MScriptUtil.createFloatMatrixFromList(value, data)
                elif isinstance(data, _api.MMatrix):
                    _api.MScriptUtil.createMatrixFromList(value, data)
                else:
                    tmp = _api.MMatrix()
                    _api.MScriptUtil.createMatrixFromList(value, tmp)
                    data = self.apicls(tmp)
            else:
                raise TypeError, "cannot assign %s to a %s" % (value, util.clsname(self))

        self.apicls.assign(self, data)
        return self

    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the Matrix api get method """
        mat = self.matrix
        return tuple(tuple(_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(mat, r), c) for c in xrange(Matrix.shape[1])) for r in xrange(Matrix.shape[0]))
        # ptr = _api.Matrix(self.matrix).matrix
        # return tuple(tuple(_api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(Matrix.shape[1])) for r in xrange(Matrix.shape[0]))

    def __len__(self):
        """ Number of components in the Matrix instance """
        return self.apicls.__len__(self)

    # iterator override
    # TODO : support for optionnal __iter__ arguments
    def __iter__(self, *args, **kwargs):
        """ Iterate on the Matrix rows """
        return self.apicls.__iter__(self.data)
    # contains is herited from Array contains

    # __getitem__ / __setitem__ override
    def __getitem__(self, index):
        """ m.__getitem__(index) <==> m[index]
            Get component index value from self.
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = MatrixN(self)
        # print list(m)
        return m.__getitem__(index)
        # return super(MatrixN, self).__getitem__(index)

    # deprecated and __getitem__ should accept slices anyway
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start, end))

    # as _api.Matrix has no __setitem__ method
    def __setitem__(self, index, value):
        """ m.__setitem__(index, value) <==> m[index] = value
            Set value of component index on self
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = MatrixN(self)
        m.__setitem__(index, value)
        self.assign(m)

    # deprecated and __setitem__ should accept slices anyway
    def __setslice__(self, start, end, value):
        self.__setitem__(slice(start, end), value)

    def __delitem__(self, index):
        """ Cannot delete from a class with a fixed shape """
        raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    def __delslice__(self, start, end):
        self.__delitem__(slice(start, end))

    # TODO : wrap double Matrix:: operator() (unsigned int row, unsigned int col ) const

    # common operators herited from MatrixN

    # operators using the Maya API when applicable
    def __eq__(self, other):
        """ m.__eq__(v) <==> m == v
            Equivalence test """
        try:
            return bool(self.apicls.__eq__(self, other))
        except:
            return bool(super(Matrix, self).__eq__(other))

    def __ne__(self, other):
        """ m.__ne__(v) <==> m != v
            Equivalence test """
        return (not self.__eq__(other))

    def __neg__(self):
        """ m.__neg__() <==> -m
            The unary minus operator. Negates the value of each of the components of m """
        return self.__class__(self.apicls.__neg__(self))

    def __add__(self, other):
        """ m.__add__(v) <==> m+v
            Returns the result of the addition of m and v if v is convertible to a MatrixN (element-wise addition),
            adds v to every component of m if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__add__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__add__(other))

    def __radd__(self, other):
        """ m.__radd__(v) <==> v+m
            Returns the result of the addition of m and v if v is convertible to a MatrixN (element-wise addition),
            adds v to every component of m if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__radd__(other))

    def __iadd__(self, other):
        """ m.__iadd__(v) <==> m += v
            In place addition of m and v, see __add__ """
        try:
            return self.__class__(self.__add__(other))
        except:
            return NotImplemented

    def __sub__(self, other):
        """ m.__sub__(v) <==> m-v
            Returns the result of the substraction of v from m if v is convertible to a MatrixN (element-wise substration),
            substract v to every component of m if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__sub__(other))

    def __rsub__(self, other):
        """ m.__rsub__(v) <==> v-m
            Returns the result of the substraction of m from v if v is convertible to a MatrixN (element-wise substration),
            replace every component c of m by v-c if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__rsub__(other))

    def __isub__(self, other):
        """ m.__isub__(v) <==> m -= v
            In place substraction of m and v, see __sub__ """
        try:
            return self.__class__(self.__sub__(other))
        except:
            return NotImplemented
    # action depends on second object type

    def __mul__(self, other):
        """ m.__mul__(x) <==> m*x
            If x is a MatrixN, __mul__ is mapped to matrix multiplication m*x, if x is a VectorN, to MatrixN by VectorN multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of b by x if x is a single numeric value """
        try:
            return self.__class__._convert(self.apicls.__mul__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__mul__(other))

    def __rmul__(self, other):
        """ m.__rmul__(x) <==> x*m
            If x is a MatrixN, __rmul__ is mapped to matrix multiplication x*m, if x is a VectorN (or Vector or Point or Color),
            to transformation, ie VectorN by MatrixN multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of m by x if x is a single numeric value """
        try:
            return self.__class__._convert(self.apicls.__rmul__(self, other))
        except:
            return self.__class__._convert(super(Matrix, self).__rmul__(other))

    def __imul__(self, other):
        """ m.__imul__(n) <==> m *= n
            Valid for Matrix * Matrix multiplication, in place multiplication of MatrixN m by MatrixN n """
        try:
            return self.__class__(self.__mul__(other))
        except:
            return NotImplemented
    # __xor__ will defer to Vector __xor__

    # API added methods

    def setToIdentity(self):
        """ m.setToIdentity() <==> m = a * b
            Sets MatrixN to the identity matrix """
        try:
            self.apicls.setToIdentity(self)
        except:
            self.assign(self.__class__())
        return self

    def setToProduct(self, left, right):
        """ m.setToProduct(a, b) <==> m = a * b
            Sets MatrixN to the result of the product of MatrixN a and MatrixN b """
        try:
            self.apicls.setToProduct(self.__class__(left), self.__class__(right))
        except:
            self.assign(self.__class__(self.__class__(left) * self.__class__(right)))
        return self

    def transpose(self):
        """ Returns the transposed Matrix """
        try:
            return self.__class__._convert(self.apicls.transpose(self))
        except:
            return self.__class__._convert(super(Matrix, self).transpose())

    def inverse(self):
        """ Returns the inverse Matrix """
        try:
            return self.__class__._convert(self.apicls.inverse(self))
        except:
            return self.__class__._convert(super(Matrix, self).inverse())

    def adjoint(self):
        """ Returns the adjoint (adjugate) Matrix """
        try:
            return self.__class__._convert(self.apicls.adjoint(self))
        except:
            return self.__class__._convert(super(Matrix, self).adjugate())

    def homogenize(self):
        """ Returns a homogenized version of the Matrix """
        try:
            return self.__class__._convert(self.apicls.homogenize(self))
        except:
            return self.__class__._convert(super(Matrix, self).homogenize())

    def det(self):
        """ Returns the determinant of this Matrix instance """
        try:
            return self.apicls.det4x4(self)
        except:
            return super(Matrix, self).det()

    def det4x4(self):
        """ Returns the 4x4 determinant of this Matrix instance """
        try:
            return self.apicls.det4x4(self)
        except:
            return super(Matrix, self[:4, :4]).det()

    def det3x3(self):
        """ Returns the determinant of the upper left 3x3 submatrix of this Matrix instance,
            it's the same as doing det(m[0:3, 0:3]) """
        try:
            return self.apicls.det3x3(self)
        except:
            return super(Matrix, self[:3, :3]).det()

    def isEquivalent(self, other, tol=_api.MVector_kTol):
        """ Returns true if both arguments considered as Matrix are equal within the specified tolerance """
        try:
            nself, nother = coerce(self, other)
        except:
            return False
        if isinstance(nself, Matrix):
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else:
            return bool(super(MatrixN, nself).isEquivalent(nother, tol))

    def isSingular(self):
        """ Returns True if the given Matrix is singular """
        try:
            return bool(self.apicls.isSingular(self))
        except:
            return super(MatrixN, self).isSingular()

    # additionnal methods

    def blend(self, other, weight=0.5):
        """ Returns a 0.0-1.0 scalar weight blend between self and other Matrix,
            blend mixes Matrix as transformation matrices """
        if isinstance(other, Matrix):
            return self.__class__(self.weighted(1.0 - weight) * other.weighted(weight))
        else:
            return blend(self, other, weight=weight)

    def weighted(self, weight):
        """ Returns a 0.0-1.0 scalar weighted blend between identity and self """
        if type(self) is not TransformationMatrix:
            self = TransformationMatrix(self)
        return self.__class__._convert(self.asMatrix(weight))

class FloatMatrix(Matrix):

    """ A 4x4 matrix class that wraps Maya's api FloatMatrix class,
        It behaves identically to Matrix, but it also derives from api's FloatMatrix
        to keep api methods happy
        """
    apicls = _api.MFloatMatrix

class TransformationMatrix(Matrix):
    apicls = _api.MTransformationMatrix

    def _getTranslate(self):
        return Vector(self.getTranslation(_api.MSpace.kTransform))

    def _setTranslate(self, value):
        self.setTranslation(Vector(value), _api.MSpace.kTransform)
    translate = property(_getTranslate, _setTranslate, None, "The translation expressed in this TransformationMatrix, in transform space")

    def _getRotate(self):
        return Quaternion(self.apicls.rotation(self))

    def _setRotate(self, value):
        self.rotateTo(Quaternion(value))
    rotate = property(_getRotate, _setRotate, None, "The quaternion rotation expressed in this TransformationMatrix, in transform space")

    def rotateTo(self, value):
        '''Set to the given rotation (and result self)

        Value may be either a Quaternion, EulerRotation object, or a list of
        floats; if it is floats, if it has length 4 it is interpreted as
        a Quaternion; if 3, as a EulerRotation.
        '''
        if not isinstance(value, (Quaternion, EulerRotation,
                                  _api.MQuaternion, _api.MEulerRotation)):
            if len(value) == 3:
                value = EulerRotation(value)
            elif len(value) == 4:
                value = Quaternion(value)
            else:
                raise ValueError('arg to rotateTo must be a Quaternion, EulerRotation, or an iterable of 3 or 4 floats')
        return self.__class__(self.apicls.rotateTo(self, value))

    def eulerRotation(self):
        return EulerRotation(self.apicls.eulerRotation(self))

    def _getEuler(self):
        return self.eulerRotation()

    def _setEuler(self, value):
        self.rotateTo(EulerRotation(value))
    euler = property(_getEuler, _getEuler, None, "The euler rotation expressed in this TransformationMatrix, in transform space")

    # The apicls getRotation needs a "RotationOrder &" object, which is
    # impossible to make in python...
    # So instead, wrap eulerRotation
    def getRotation(self):
        return self.eulerRotation()

    def setRotation(self, *args):
        self.rotateTo(EulerRotation(*args))

    def _getScale(self):
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        ms.createFromDouble(1.0, 1.0, 1.0)
        p = ms.asDoublePtr()
        self.getScale(p, _api.MSpace.kTransform)
        return Vector([ms.getDoubleArrayItem(p, i) for i in range(3)])

    def _setScale(self, value):
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        ms.createFromDouble(*Vector(value))
        p = ms.asDoublePtr()
        self.setScale(p, _api.MSpace.kTransform)
    scale = property(_getScale, _setScale, None, "The scale expressed in this TransformationMatrix, in transform space")


class EulerRotation(Array):

    """
    unit handling:
    >>> from pymel.all import *
    >>> import pymel.core.datatypes as dt
    >>>
    >>> currentUnit(angle='degree')
    u'degree'
    >>> e = dt.EulerRotation([math.pi,0,0], unit='radians')
    >>> e
    dt.EulerRotation([3.14159265359, 0.0, 0.0], unit='radians')
    >>> e2 = dt.EulerRotation([180,0,0], unit='degrees')
    >>> e2
    dt.EulerRotation([180.0, 0.0, 0.0])
    >>> e.isEquivalent( e2 )
    True
    >>> e == e2
    True

    units are only displayed when they do not match the current ui unit
    >>> dt.Angle.getUIUnit() # check current angular unit
    'degrees'
    >>> e
    dt.EulerRotation([3.14159265359, 0.0, 0.0], unit='radians')
    >>> dt.Angle.setUIUnit('radians')  # change to radians
    >>> e
    dt.EulerRotation([3.14159265359, 0.0, 0.0])


    """
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MEulerRotation
    shape = (3,)
    cnames = ('x', 'y', 'z')

    RotationOrder = _factories.apiClassInfo['MEulerRotation']['pymelEnums']['RotationOrder']

    def _getorder(self):
        return self.RotationOrder[self.apicls.__dict__['order'].__get__(self, self.apicls)]

    def _setorder(self, val):
        self.apicls.__dict__['order'].__set__(self, self.RotationOrder.getIndex(val))
    order = property(_getorder, _setorder)

    def __new__(cls, *args, **kwargs):
        #        shape = kwargs.get('shape', None)
        #        ndim = kwargs.get('ndim', None)
        #        size = kwargs.get('size', None)
        #
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new

    def __init__(self, *args, **kwargs):
        """ __init__ method for EulerRotation """
        self.unit = None
        self.assign(*args, **kwargs)

    def setDisplayUnit(self, unit):
        if unit not in Angle.Unit:
            raise TypeError, "%s is not a valid angular unit.  See Angle.Unit for the list of valid units"
        self.unit = unit

    def __repr__(self):
        argStrs = [str(self)]
        if self.unit != Angle.getUIUnit():
            argStrs.append('unit=%r' % self.unit)
        if self.order != 'XYZ':
            argStrs.append('order=%r' % str(self.order))
        return "dt.%s(%s)" % (self.__class__.__name__, ', '.join(argStrs))

    def __iter__(self):
        for i in range(self.size):
            yield self[i]

    def __getitem__(self, i):
        return Angle(self._getitem(i), 'radians').asUnit(self.unit)

    def __setitem__(self, key, val):
        kwargs = {}
        if key in self.cnames:
            kwargs[key] = val
        else:
            kwargs[self.cnames[key]] = val
        self.assign(**kwargs)

    # faster to override __getitem__ cause we know Vector only has one dimension
    def _getitem(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__'):
            i = list(i)
            if len(i) == 1:
                i = i[0]
            else:
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice):
            return _toCompOrArrayInstance(list(self)[i], VectorN)
            try:
                return _toCompOrArrayInstance(list(self)[i], VectorN)
            except:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else:
            if i < 0:
                i = self.size + i
            if i < self.size and not i < 0:
                if hasattr(self.apicls, '__getitem__'):
                    return self.apicls.__getitem__(self, i)
                else:
                    return list(self)[i]
            else:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    def assign(self, *args, **kwargs):
        """ Wrap the Quaternion api assign method """
        # After processing, we want to have args be in a format such that
        # we may do:
        # apicls.assign(*args)
        # This means that either:
        #   args is a list/tuple of

        if 'unit' in kwargs:
            self.unit = kwargs['unit']
        elif self.unit is None:
            self.unit = Angle.getUIUnit()

        if len(args) == 1 and isinstance(args[0], _api.MTransformationMatrix):
            args = [args[0].asMatrix()]

        # api MEulerRotation assign accepts Matrix, Quaternion and EulerRotation
        validSingleObjs = (_api.MMatrix, _api.MQuaternion, _api.MEulerRotation)
        if len(args) == 1 and isinstance(args[0], validSingleObjs):
            self.unit = 'radians'
            self.apicls.assign(self, args[0])
        elif args:
            if len(args) == 1:
                args = list(args[0])
            elif len(args) == 2 and isinstance(args[1], (basestring, util.EnumValue)):
                args = list(args[0]) + [args[1]]
            else:
                # convert to list, as we may have to do modifications
                args = list(args)

            # If only 3 rotation angles supplied, and current order is
            # not default, make sure we maintain it
            if self.order != 'XYZ' and len(args) == 3:
                args.append(self.apicls.__dict__['order'].__get__(self, self.apicls))

            elif len(args) == 4 and isinstance(args[3], (basestring, util.EnumValue)):
                # allow to initialize directly from 3 rotations and a rotation order as string
                args[3] = self.RotationOrder.getIndex(args[3])

            # In case they do something like pass in a mix of Angle objects and
            # float numbers, convert to correct unit one-by-one...
            for i in xrange(3):
                if isinstance(args[i], Angle):
                    args[i] = args[i].asUnit('radians')
                elif self.unit != 'radians' and not isinstance(args[i], Angle):
                    args[i] = Angle(args[i], self.unit).asUnit('radians')
            self.apicls.setValue(self, *args)

        # We do kwargs as a separate step after args, instead of trying to combine
        # them, in case they do something like pass in a EulerRotation(myMatrix, y=2)
        if hasattr(self, 'cnames') and len(set(self.cnames) & set(kwargs)):
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(self.cnames):
                if c in kwargs:
                    if float(l[i]) != float(kwargs[c]):
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp:
                try:
                    self.assign(l)
                except:
                    msg = ", ".join(map(lambda x, y: x + "=<" + util.clsname(y) + ">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)

        return self

    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MEulerRotation api get method """
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        l = (0,) * self.size
        ms.createFromDouble(*l)
        p = ms.asDoublePtr()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem(p, i) for i in xrange(self.size)])

    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()

    def __len__(self):
        return self.apicls.__len__(self)

    # common operators without an api equivalent are herited from VectorN

    # operators using the Maya API when applicable, but that can delegate to VectorN

    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v
            Equivalence test """
        if isinstance(other, self.apicls):
            return bool(self.apicls.__eq__(self, other))
        else:
            return bool(super(EulerRotation, self).__eq__(other))

    def __ne__(self, other):
        """ u.__ne__(v) <==> u != v
            Equivalence test """
        return (not self.__eq__(other))

    def __neg__(self):
        """ u.__neg__() <==> -u
            The unary minus operator. Negates the value of each of the components of u """
        return self.__class__(self.apicls.__neg__(self))

    def __add__(self, other):
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__add__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__add__(other))

    def __radd__(self, other):
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a VectorN (element-wise addition),
            adds v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__radd__(other))

    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try:
            return self.__class__(self.__add__(other))
        except:
            return NotImplemented

    def __sub__(self, other):
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is convertible to a VectorN (element-wise substration),
            substract v to every component of u if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__sub__(other))

    def __rsub__(self, other):
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is convertible to a VectorN (element-wise substration),
            replace every component c of u by v-c if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__rsub__(other))

    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        try:
            return self.__class__(self.__sub__(other))
        except:
            return NotImplemented

    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the division of u by v if v is convertible to a VectorN (element-wise division),
            divide every component of u by v if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__div__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__div__(other))

    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of of the division of v by u if v is convertible to a VectorN (element-wise division),
            invert every component of u and multiply it by v if v is a scalar """
        try:
            return self.__class__._convert(self.apicls.__rdiv__(self, other))
        except:
            return self.__class__._convert(super(EulerRotation, self).__rdiv__(other))

    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """
        try:
            return self.__class__(self.__div__(other))
        except:
            return NotImplemented
    # action depends on second object type

    def __mul__(self, other):
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the transformation of u by matrix v when v is a MatrixN,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try:
            res = self.apicls.__mul__(self, other)
        except:
            res = super(EulerRotation, self).__mul__(other)
        if util.isNumeric(res):
            return res
        else:
            return self.__class__._convert(res)

    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the left side multiplication (pre-multiplication) of u by matrix v when v is a MatrixN,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try:
            res = self.apicls.__rmul__(self, other)
        except:
            res = super(EulerRotation, self).__rmul__(other)
        if util.isNumeric(res):
            return res
        else:
            return self.__class__._convert(res)

    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for EulerRotation * Matrix multiplication, in place transformation of u by Matrix v
            or EulerRotation by scalar multiplication only """
        try:
            return self.__class__(self.__mul__(other))
        except:
            return NotImplemented
    # special operators
#    def __xor__(self, other):
#        """ u.__xor__(v) <==> u^v
#            Defines the cross product operator between two 3D vectors,
#            if v is a MatrixN, u^v is equivalent to u.transformAsNormal(v) """
#        if isinstance(other, VectorN) :
#            return self.cross(other)
#        elif isinstance(other, MatrixN) :
#            return self.transformAsNormal(other)
#        else :
#            return NotImplemented
#    def __ixor__(self, other):
#        """ u.__xor__(v) <==> u^=v
#            Inplace cross product or transformation by inverse transpose of v is v is a MatrixN """
#        try :
#            return self.__class__(self.__xor__(other))
#        except :
#            return NotImplemented


class Quaternion(Matrix):
    apicls = _api.MQuaternion
    shape = (4,)
    cnames = ('x', 'y', 'z', 'w')

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (4,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on Quaternion, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)

        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new

    def __init__(self, *args, **kwargs):
        """ __init__ method for Quaternion """
        cls = self.__class__

        if args:
            # allow both forms for arguments
            if len(args) == 1 and hasattr(args[0], '__iter__'):
                args = args[0]

            rotate = getattr(args, 'rotate', None)
            # TransformationMatrix, Quaternion, EulerRotation api classes can convert to a rotation Quaternion
            if rotate is not None and not callable(rotate):
                args = args.rotate
                self.unit = 'radians'

            elif len(args) == 4 and isinstance(args[3], (basestring, util.EnumValue)):  # isinstance(args[3], EulerRotation.RotationOrder) ) :
                quat = _api.MQuaternion()
                quat.assign(EulerRotation(*args, **kwargs))
                args = quat
                # allow to initialize directly from 3 rotations and a rotation order

            elif len(args) == 2 and isinstance(args[0], VectorN) and isinstance(args[1], float):
                # some special init cases are allowed by the api class, want to authorize
                # Quaternion(Vector axis, float angle) as well as Quaternion(float angle, Vector axis)
                args = (float(args[1]), Vector(args[0]))
            # shortcut when a direct api init is possible

            try:
                self.assign(args)
            except:
                super(Array, self).__init__(*args)

        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)):
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames):
                if c in kwargs:
                    if float(l[i]) != float(kwargs[c]):
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp:
                try:
                    self.assign(l)
                except:
                    msg = ", ".join(map(lambda x, y: x + "=<" + util.clsname(y) + ">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)

    # set properties for easy acces to translation / rotation / scale of a MMatrix or derived class
    # some of these will only yield dependable results if MMatrix is a MTransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a MQuaternion

    def _getTranslate(self):
        return Vector(0.0, 0.0, 0.0)
    translate = property(_getTranslate, None, None, "The translation expressed in this MMQuaternion, which is always (0.0, 0.0, 0.0)")

    def _getRotate(self):
        return self

    def _setRotate(self, value):
        self.assign(Quaternion(value))
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this Quaternion, in transform space")

    def _getScale(self):
        return Vector(1.0, 1.0, 1.0)
    scale = property(_getScale, None, None, "The scale expressed in this Quaternion, which is always (1.0, 1.0, 1.0)")

    # overloads for assign and get though standard way should be to use the data property
    # to access stored values

    def assign(self, value):
        """ Wrap the Quaternion api assign method """
        # api Quaternion assign accepts Matrix, Quaternion and EulerRotation
        if isinstance(value, Matrix):
            value = value.rotate
        else:
            if not hasattr(value, '__iter__'):
                value = (value,)
            value = self.apicls(*value)
        self.apicls.assign(self, value)
        return self

    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the Quaternion api get method """
        # need to keep a ref to the MScriptUtil alive until
        # all pointers aren't needed...
        ms = _api.MScriptUtil()
        l = (0,) * self.size
        ms.createFromDouble(*l)
        p = ms.asDoublePtr()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem(p, i) for i in xrange(self.size)])

    def __getitem__(self, i):
        return self._getitem(i)

    # faster to override __getitem__ cause we know Quaternion only has one dimension
    def _getitem(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__'):
            i = list(i)
            if len(i) == 1:
                i = i[0]
            else:
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice):
            try:
                return list(self)[i]
            except:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else:
            if i < 0:
                i = self.size + i
            if i < self.size and not i < 0:
                if hasattr(self.apicls, '__getitem__'):
                    res = self.apicls.__getitem__(self, i)
                else:
                    res = list(self)[i]
                return res
            else:
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    # as _api.Vector has no __setitem__ method, so need to reassign the whole Vector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = VectorN(self)
        v.__setitem__(i, a)
        self.assign(v)

    def __iter__(self):
        for i in range(self.size):
            yield self[i]

    def __len__(self):

        # api incorrectly returns 4. this might make sense if it did not simply return z a second time as the fourth element
        return self.size
#
#    # TODO : support for optional __iter__ arguments
#    def __iter__(self, *args, **kwargs):
#        """ Iterate on the api components """
#        return self.apicls.__iter__(self.data)

    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()


class Unit(float):
    __slots__ = ['unit', 'data', 'value', '_unit']

    @classmethod
    def getUIUnit(cls):
        """
            Returns the global UI units currently in use for that type
        """
        return cls.sUnit(cls.apicls.uiUnit())

    @classmethod
    def setUIUnit(cls, unit=None):
        """
            Sets the global UI units currently to use for that type
        """
        if unit is None:
            cls.apicls.setUIUnit(cls.apicls.internalUnit())
        else:
            cls.apicls.setUIUnit(cls.kUnit(unit))

    @classmethod
    def getInternalUnit(cls):
        """
            Returns the inernal units currently in use for that type
        """
        return cls.sUnit(cls.apicls.internalUnit())

    @classmethod
    def uiToInternal(cls, value):
        d = cls(value, cls.getUIUnit())
        return d.asInternalUnit()

    @classmethod
    def kUnit(cls, unit=None):
        """
            Converts a string unit name to the internal int unit enum representation
        """
        if unit:
            return cls.Unit.getIndex(unit)
        else:
            return cls.apicls.uiUnit()

    @classmethod
    def sUnit(cls, unit=None):
        """
            Converts an internal int unit enum representation tp the string unit name
        """
        if unit:
            return cls.Unit.getKey(unit)
        else:
            return str(cls.unit[cls.apicls.uiUnit()])

    def getUnit(self):
        """
            Returns the units currently in effect for this instance
        """
        return self.__class__.sUnit(self._unit)
#    def setUnit(self, unit=None) :
#        """
#            Sets the units currently in effect for this instance
#        """
#        self._unit = self.__class__.kUnit(unit)
    unit = property(getUnit, None, None, "The units currently in effect for this instance")

    def __new__(cls, value, unit=None):
        unit = cls.kUnit(unit)
        if isinstance(value, cls.apicls):
            value = getattr(value, AS_UNITS)(unit)
        elif isinstance(value, cls):
            value = value.asUnit(unit)
        #data = cls.apicls(value, unit)
        # the float representation uses internal units so that arithmetics work
        #newobj = float.__new__(cls, data.asUnit(cls.apicls.internalUnit()))
        #newobj = float.__new__(cls, data.asUnit(unit))
        newobj = float.__new__(cls, value)
        #ewobj._data = data
        newobj._unit = unit
        newobj._data = cls.apicls(value, unit)
        return newobj

    def assign(self, *args):
        if isinstance(args, self.__class__):
            args = (args._data, args._unit)
        self._data.assign(*args)

    def __repr__(self):
        return 'dt.%s(%s, unit=%r)' % (self.__class__.__name__, self, self.unit)

    def asUnit(self, unit):
        # in python2.6/maya2010 'as' becomes a keyword.
        return getattr(self._data, AS_UNITS)(self.__class__.kUnit(unit))

#    def asUnit(self) :
#        return self.asUnit(self.unit)

    def asUIUnit(self):
        return self.asUnit(self.__class__.getUIUnit())

    def asInternalUnit(self):
        return self.asUnit(self.__class__.getInternalUnit())

class Time(Unit):
    apicls = _api.MTime
    Unit = _factories.apiClassInfo['MTime']['pymelEnums']['Unit']


class Distance(Unit):

    """
        >>> from pymel.core import *
        >>> import pymel.core.datatypes as dt
        >>>
        >>> dt.Distance.getInternalUnit()
        'centimeters'
        >>> dt.Distance.setUIUnit('meters')
        >>> dt.Distance.getUIUnit()
        'meters'

        >>> d = dt.Distance(12)
        >>> d.unit
        'meters'
        >>> print d
        12.0
        >>> print repr(d)
        dt.Distance(12.0, unit='meters')
        >>> print d.asUIUnit()
        12.0
        >>> print d.asInternalUnit()
        1200.0

        >>> dt.Distance.setUIUnit('centimeters')
        >>> dt.Distance.getUIUnit()
        'centimeters'
        >>> e = dt.Distance(12)
        >>> e.unit
        'centimeters'
        >>> print e
        12.0
        >>> str(e)
        '12.0'
        >>> print repr(e)
        dt.Distance(12.0, unit='centimeters')
        >>> print e.asUIUnit()
        12.0
        >>> print e.asInternalUnit()
        12.0

        >>> f = dt.Distance(12, 'feet')
        >>> print f
        12.0
        >>> print repr(f)
        dt.Distance(12.0, unit='feet')
        >>> f.unit
        'feet'
        >>> print f.asUIUnit()
        365.76
        >>> dt.Distance.setUIUnit('meters')
        >>> dt.Distance.getUIUnit()
        'meters'
        >>> print f.asUIUnit()
        3.6576
        >>> dt.Distance.getInternalUnit()
        'centimeters'
        >>> print f.asInternalUnit()
        365.76

        >>> print f.asFeet()
        12.0
        >>> print f.asMeters()
        3.6576
        >>> print f.asCentimeters()
        365.76

        >>> dt.Distance.setUIUnit()
        >>> dt.Distance.getUIUnit()
        'centimeters'
    """
    apicls = _api.MDistance
    Unit = _factories.apiClassInfo['MDistance']['pymelEnums']['Unit']

    def asMillimeter(self):
        return self.asUnit('millimeter')

    def asCentimeters(self):
        return self.asUnit('centimeters')

    def asKilometers(self):
        return self.asUnit('kilometers')

    def asMeters(self):
        return self.asUnit('meters')

    def asInches(self):
        return self.asUnit('inches')

    def asFeet(self):
        return self.asUnit('feet')

    def asYards(self):
        return self.asUnit('yards')

    def asMiles(self):
        return self.asUnit('miles')


class Angle(Unit):
    apicls = _api.MAngle
    Unit = _factories.apiClassInfo['MAngle']['pymelEnums']['Unit']

    def asRadians(self):
        return self.asUnit('radians')

    def asDegrees(self):
        return self.asUnit('degrees')

    def asAngMinutes(self):
        return self.asUnit('angMinutes')

    def asAngSeconds(self):
        return self.asUnit('angSeconds')


class BoundingBox(_api.MBoundingBox):
    apicls = _api.MBoundingBox
    __metaclass__ = _factories.MetaMayaTypeWrapper

    def __init__(self, *args):
        if len(args) == 2:
            args = list(args)
            if not isinstance(args[0], _api.MPoint):
                args[0] = Point(args[0])
            if not isinstance(args[1], _api.MPoint):
                args[1] = Point(args[1])
        _api.MBoundingBox.__init__(self, *args)

    def __str__(self):
        return 'dt.%s(%s,%s)' % (self.__class__.__name__, self.min(), self.max())

    def __repr__(self):
        return str(self)

    def __getitem__(self, item):
        if item == 0:
            return self.min()
        elif item == 1:
            return self.max()
        raise IndexError, "Index out of range"

    def __melobject__(self):
        """A flat list of 6 values [minx, miny, minz, maxx, maxy, maxz]"""
        return list(self.min()) + list(self.max())

    repr = __str__
    w = property(_factories.wrapApiMethod(_api.MBoundingBox, 'width'))
    h = property(_factories.wrapApiMethod(_api.MBoundingBox, 'height'))
    d = property(_factories.wrapApiMethod(_api.MBoundingBox, 'depth'))

#_factories.ApiTypeRegister.register( 'MVector', Vector )
#_factories.ApiTypeRegister.register( 'MMatrix', Matrix )
#_factories.ApiTypeRegister.register( 'MPoint', Point )
#_factories.ApiTypeRegister.register( 'MColor', Color )
#_factories.ApiTypeRegister.register( 'MQuaternion', Quaternion )
#_factories.ApiTypeRegister.register( 'MEulerRotation', EulerRotation )
_factories.ApiTypeRegister.register('MTime', Time, inCast=lambda x: Time(x)._data)
_factories.ApiTypeRegister.register('MDistance', Distance, outCast=lambda instance, result: Distance(result, 'centimeters').asUIUnit())
_factories.ApiTypeRegister.register('MAngle', Angle, outCast=lambda instance, result: Angle(result, 'radians').asUIUnit())


#_floatUpConvertDict = {_api.MFloatArray:_api.MDoubleArray,
#                       _api.MFloatMatrix:_api.MMatrix,
#                       _api.MFloatPoint:_api.MPoint,
#                       _api.MFloatPointArray:_api.MPointArray,
#                       _api.MFloatVector:_api.MVector,
#                       _api.MFloatVectorArray:_api.MVectorArray,
#                       FloatMatrix:Matrix,
#                       FloatPoint:Point,
#                       FloatVector:Vector
#                       }
# def _floatUpConvert(input):
#    """Will convert various Float* objects to their corresponding double object
#
#    ie, api.MFloatMatrix => api.MMatrix, FloatPoint => Point
#    """
#    newClass = _floatUpConvertDict.get(input.__class__)
#    if newClass:
#        return newClass(input)
#    else:
#        return input

def getPlugValue(plug):
    """given an MPlug, get its value as a pymel-style object"""

    # if plug.isArray():
    #    raise TypeError, "array plugs of this type are not supported"

    obj = plug.attribute()
    apiType = obj.apiType()

    # Float Pairs
    if apiType in [_api.MFn.kAttribute2Double, _api.MFn.kAttribute2Float]:
        res = []
        for i in range(plug.numChildren()):
            res.append(getPlugValue(plug.child(i)))
        if isinstance(res[0], Distance):
            return Vector(res)
        return res

    # Integer Groups
    elif apiType in [_api.MFn.kAttribute2Short, _api.MFn.kAttribute2Int, _api.MFn.kAttribute3Short, _api.MFn.kAttribute3Int]:
        res = []
        for i in range(plug.numChildren()):
            res.append(getPlugValue(plug.child(i)))
        return res

    # Float Groups
    elif apiType in [_api.MFn.kAttribute3Double, _api.MFn.kAttribute3Float, _api.MFn.kAttribute4Double]:
        res = []
        for i in range(plug.numChildren()):
            res.append(getPlugValue(plug.child(i)))

        if isinstance(res[0], Distance):
            return Vector(res)
        elif _api.MFnAttribute(obj).isUsedAsColor():
            return Color(res)
        return res

    # Compound
    elif apiType in [_api.MFn.kCompoundAttribute]:
        res = []
        for i in range(plug.numChildren()):
            res.append(getPlugValue(plug.child(i)))
        return tuple(res)

    # Distance
    elif apiType in [_api.MFn.kDoubleLinearAttribute, _api.MFn.kFloatLinearAttribute]:
        val = plug.asMDistance()
        unit = _api.MDistance.uiUnit()
        # as becomes a keyword in python 2.6
        return Distance(getattr(val, AS_UNITS)(unit), unit)

    # Angle
    elif apiType in [_api.MFn.kDoubleAngleAttribute, _api.MFn.kFloatAngleAttribute]:
        val = plug.asMAngle()
        unit = _api.MAngle.uiUnit()
        # as becomes a keyword in python 2.6
        return Angle(getattr(val, AS_UNITS), unit)

    # Time
    elif apiType == _api.MFn.kTimeAttribute:
        val = plug.asMTime()
        unit = _api.MTime.uiUnit()
        # as becomes a keyword in python 2.6
        return Time(getattr(val, AS_UNITS), unit)

    elif apiType == _api.MFn.kNumericAttribute:
        nAttr = _api.MFnNumericAttribute(obj)
        dataType = nAttr.unitType()
        if dataType == _api.MFnNumericData.kBoolean:
            return plug.asBool()

        elif dataType in [_api.MFnNumericData.kShort, _api.MFnNumericData.kInt, _api.MFnNumericData.kLong, _api.MFnNumericData.kByte]:
            return plug.asInt()

        elif dataType in [_api.MFnNumericData.kFloat, _api.MFnNumericData.kDouble, _api.MFnNumericData.kAddr]:
            return plug.asDouble()
        raise "%s: unknown numeric attribute type: %s" % (plug.partialName(True, True, True, False, True, True), dataType)

    elif apiType == _api.MFn.kEnumAttribute:
        # TODO : use EnumValue class?
        return plug.asInt()

    elif apiType == _api.MFn.kTypedAttribute:
        tAttr = _api.MFnTypedAttribute(obj)
        dataType = tAttr.attrType()

        if dataType == _api.MFnData.kInvalid:  # 0
            return None

        elif dataType == _api.MFnData.kNumeric:  # 1

            # all of the dynamic mental ray attributes fail here, but i have no idea why they are numeric attrs and not message attrs.
            # cmds.getAttr returns None, so we will too.
            try:
                dataObj = plug.asMObject()
            except:
                return

            try:
                numFn = _api.MFnNumericData(dataObj)
            except RuntimeError:
                if plug.isArray():
                    raise TypeError, "%s: numeric arrays are not supported" % plug.partialName(True, True, True, False, True, True)
                else:
                    raise TypeError, "%s: attribute type is numeric, but its data cannot be interpreted numerically" % plug.partialName(True, True, True, False, True, True)
            dataType = numFn.numericType()

            if dataType == _api.MFnNumericData.kBoolean:
                return plug.asBool()

            elif dataType in [_api.MFnNumericData.kShort, _api.MFnNumericData.kInt, _api.MFnNumericData.kLong, _api.MFnNumericData.kByte]:
                return plug.asInt()

            elif dataType in [_api.MFnNumericData.kFloat, _api.MFnNumericData.kDouble, _api.MFnNumericData.kAddr]:
                return plug.asDouble()

            elif dataType == _api.MFnNumericData.k2Short:
                ptr1 = _api.SafeApiPtr('short')
                ptr2 = _api.SafeApiPtr('short')

                numFn.getData2Short(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType in [_api.MFnNumericData.k2Int, _api.MFnNumericData.k2Long]:
                ptr1 = _api.SafeApiPtr('int')
                ptr2 = _api.SafeApiPtr('int')

                numFn.getData2Int(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == _api.MFnNumericData.k2Float:
                ptr1 = _api.SafeApiPtr('float')
                ptr2 = _api.SafeApiPtr('float')

                numFn.getData2Float(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == _api.MFnNumericData.k2Double:
                ptr1 = _api.SafeApiPtr('double')
                ptr2 = _api.SafeApiPtr('double')

                numFn.getData2Double(ptr1(), ptr2())
                return (ptr1.get(), ptr2.get())

            elif dataType == _api.MFnNumericData.k3Float:
                ptr1 = _api.SafeApiPtr('float')
                ptr2 = _api.SafeApiPtr('float')
                ptr3 = _api.SafeApiPtr('float')

                numFn.getData3Float(ptr1(), ptr2(), ptr3())
                return (ptr1.get(), ptr2.get(), ptr3.get())

            elif dataType == _api.MFnNumericData.k3Double:
                ptr1 = _api.SafeApiPtr('double')
                ptr2 = _api.SafeApiPtr('double')
                ptr3 = _api.SafeApiPtr('double')

                numFn.getData3Double(ptr1(), ptr2(), ptr3())
                return (ptr1.get(), ptr2.get(), ptr3.get())

            elif dataType == _api.MFnNumericData.kChar:
                return plug.asChar()

            raise TypeError, "%s: Unsupported numeric attribute: %s" % (plug.partialName(True, True, True, False, True, True), dataType)

        elif dataType == _api.MFnData.kString:  # 4
            return plug.asString()

        elif dataType == _api.MFnData.kMatrix:  # 5
            return Matrix(_api.MFnMatrixData(plug.asMObject()).matrix())

        elif dataType == _api.MFnData.kStringArray:  # 6
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            array = _api.MFnStringArrayData(dataObj).array()
            return [array[i] for i in range(array.length())]

        elif dataType == _api.MFnData.kDoubleArray:  # 7
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            array = _api.MFnDoubleArrayData(dataObj).array()
            return [array[i] for i in range(array.length())]

        elif dataType == _api.MFnData.kIntArray:  # 8
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            array = _api.MFnIntArrayData(dataObj).array()
            return [array[i] for i in range(array.length())]

        elif dataType == _api.MFnData.kPointArray:  # 9
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            array = _api.MFnPointArrayData(dataObj).array()
            return [Point(array[i]) for i in range(array.length())]

        elif dataType == _api.MFnData.kVectorArray:  # 10
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            array = _api.MFnVectorArrayData(dataObj).array()
            return [Vector(array[i]) for i in range(array.length())]

        # this block crashes maya under certain circumstances
#        elif dataType == _api.MFnData.kComponentList : # 11
#            try:
#                dataObj = plug.asMObject()
#            except RuntimeError:
#                return []
#            array = _api.MFnComponentListData( dataObj )
#            return array
#            #return [ Vector(array[i]) for i in range(array.length()) ]

        raise TypeError, "%s: Unsupported typed attribute: %s" % (plug.partialName(True, True, True, False, True, True), dataType)

    raise TypeError, "%s: Unsupported Type: %s" % (plug.partialName(True, True, True, False, True, True), _factories.apiEnumsToApiTypes.get(apiType, apiType))

def _testMVector():

    print "Vector class:", dir(Vector)
    u = Vector()
    print u
    print "Vector instance:", dir(u)
    print repr(u)
    print Vector.__readonly__
    print Vector.__slots__
    print Vector.shape
    print Vector.ndim
    print Vector.size
    print u.shape
    print u.ndim
    print u.size
    # should fail
    u.shape = 2

    u.assign(Vector(4, 5, 6))
    print repr(u)
    #Vector([4.0, 5.0, 6.0])
    u = Vector(1, 2, 3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    print len(u)
    # 3
    # inherits from VectorN --> Array
    print isinstance(u, VectorN)
    # True
    print isinstance(u, Array)
    # True
    # as well as _api.Vector
    print isinstance(u, _api.MVector)
    # True
    # accepted directly by API methods
    M = _api.MTransformationMatrix()
    M.setTranslation(u, _api.MSpace.kWorld)
    # need conversion on the way back though
    u = Vector(M.getTranslation(_api.MSpace.kWorld))
    print repr(u)
    # Vector([1.0, 2.0, 3.0])

    u = Vector(x=1, y=2, z=3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    u = Vector([1, 2], z=3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    u = Vector(_api.MPoint(1, 2, 3))
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    print "u = Vector(VectorN(1, 2, 3))"
    u = Vector(VectorN(1, 2, 3))
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    u = Vector(1)
    print repr(u)
    # Vector([1.0, 1.0, 1.0])
    u = Vector(1, 2)
    print repr(u)
    # Vector([1.0, 2.0, 0.0])
    u = Vector(VectorN(1, shape=(2,)))
    print repr(u)
    # Vector([1.0, 1.0, 0.0])
    u = Vector(Point(1, 2, 3))
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    u = Vector(Point(1, 2, 3, 1), y=20, z=30)
    print repr(u)
    # Vector([1.0, 20.0, 30.0])
    # should fail
    print "Vector(VectorN(1, 2, 3, 4))"
    try:
        u = Vector(VectorN(1, 2, 3, 4))
    except:
        print "will raise ValueError: could not cast [1, 2, 3, 4] to Vector of size 3, some data would be lost"

    print u.get()
    # (1.0, 20.0, 30.0)
    print u[0]
    1.0
    u[0] = 10
    print repr(u)
    # Vector([10.0, 20.0, 30.0])
    print (10 in u)
    # True
    print list(u)
    # [10.0, 20.0, 30.0]

    u = Vector.xAxis
    v = Vector.yAxis
    print Vector.xAxis
    print str(Vector.xAxis)
    print unicode(Vector.xAxis)
    print repr(Vector.xAxis)

    print "u = Vector.xAxis:"
    print repr(u)
    # Vector([1.0, 0.0, 0.0])
    print "v = Vector.yAxis:"
    print repr(v)
    # Vector([0.0, 1.0, 0.0])
    n = u ^ v
    print "n = u ^ v:"
    print repr(n)
    # Vector([0.0, 0.0, 1.0])
    print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    # n.x=0.0, n.y=0.0, n.z=1.0
    n = u ^ VectorN(v)
    print "n = u ^ VectorN(v):"
    print repr(n)
    # Vector([0.0, 0.0, 1.0])
    n = u ^ [0, 1, 0]
    print "n = u ^ [0, 1, 0]:"
    print repr(n)
    # Vector([0.0, 0.0, 1.0])
    n[0:2] = [1, 1]
    print "n[0:2] = [1, 1]:"
    print repr(n)
    # Vector([1.0, 1.0, 1.0])
    print "n = n * 2 :"
    n = n * 2
    print repr(n)
    # Vector([2.0, 2.0, 2.0])
    print "n = n * [0.5, 1.0, 2.0]:"
    n = n * [0.5, 1.0, 2.0]
    print repr(n)
    # Vector([1.0, 2.0, 4.0])
    print "n * n :"
    print n * n
    # 21.0
    print repr(n.clamp(1.0, 2.0))
    # Vector([1.0, 2.0, 2.0])
    print repr(-n)
    # Vector([-1.0, -2.0, -4.0])
    w = u + v
    print repr(w)
    # Vector([1.0, 1.0, 0.0])
    p = Point(1, 2, 3)
    q = u + p
    print repr(q)
    # Point([2.0, 2.0, 3.0, 1.0])
    q = p + u
    print repr(q)
    # Point([2.0, 2.0, 3.0, 1.0])
    print repr(p + q)
    # Point([3.0, 4.0, 6.0, 1.0])
    w = u + VectorN(1, 2, 3, 4)
    print repr(w)
    # VectorN([2.0, 2.0, 3.0, 4])
    print repr(u + 2)
    # Vector([3.0, 2.0, 2.0])
    print repr(2 + u)
    # Vector([3.0, 2.0, 2.0])
    print repr(p + 2)
    # Point([3.0, 4.0, 5.0, 1.0])
    print repr(2 + p)
    # Point([3.0, 4.0, 5.0, 1.0])
    print repr(p + u)
    # Point([2.0, 2.0, 3.0, 1.0])
    print repr(VectorN(1, 2, 3, 4) + u)
    # VectorN([2.0, 2.0, 3.0, 4])
    print repr([1, 2, 3] + u)
    # Vector([2.0, 2.0, 3.0])

    u = Vector(1, 2, 3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    print u.length()
    # 3.74165738677
    print length(u)
    # 3.74165738677
    print length([1, 2, 3])
    # 3.74165738677
    print length(VectorN(1, 2, 3))
    # 3.74165738677
    print VectorN(1, 2, 3).length()
    # 3.74165738677
    print length(VectorN(1, 2, 3, 4))
    # 5.47722557505
    print VectorN(1, 2, 3, 4).length()
    # 5.47722557505
    print length(1)
    # 1.0
    print length([1, 2])
    # 2.2360679775
    print length([1, 2, 3])
    # 3.74165738677
    print length([1, 2, 3, 4])
    # 5.47722557505
    print length([1, 2, 3, 4], 0)
    # 5.47722557505
    print length([1, 2, 3, 4], (0,))
    # 5.47722557505
    print length([[1, 2], [3, 4]], 1)
    # [3.16227766017, 4.472135955]
    # should fail
    try:
        print length([1, 2, 3, 4], 1)
    except:
        print "Will raise ValueError, \"axis 0 is the only valid axis for a Vector, 1 invalid\""

    u = Vector(1, 2, 3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    print u.sqlength()
    # 14
    print repr(u.normal())
    # Vector([0.267261241912, 0.534522483825, 0.801783725737])
    u.normalize()
    print repr(u)
    # Vector([0.267261241912, 0.534522483825, 0.801783725737])

    u = Vector(1, 2, 3)
    print repr(u)
    # Vector([1.0, 2.0, 3.0])
    w = u + [0.01, 0.01, 0.01]
    print repr(w)
    # Vector([1.01, 2.01, 3.01])
    print (u == u)
    # True
    print (u == w)
    # False
    print (u == Vector(1.0, 2.0, 3.0))
    # True
    print (u == [1.0, 2.0, 3.0])
    # False
    print (u == Point(1.0, 2.0, 3.0))
    # False
    print u.isEquivalent([1.0, 2.0, 3.0])
    # True
    print u.isEquivalent(Vector(1.0, 2.0, 3.0))
    # True
    print u.isEquivalent(Point(1.0, 2.0, 3.0))
    # True
    print u.isEquivalent(w)
    # False
    print u.isEquivalent(w, 0.1)
    # True

    u = Vector(1, 0, 0)
    print repr(u)
    # Vector([1.0, 0.0, 0.0])
    v = Vector(0.707, 0, -0.707)
    print repr(v)
    # Vector([0.707, 0.0, -0.707])
    print repr(axis(u, v))
    # Vector([-0.0, 0.707, 0.0])
    print repr(u.axis(v))
    # Vector([-0.0, 0.707, 0.0])
    print repr(axis(VectorN(u), VectorN(v)))
    # VectorN([-0.0, 0.707, 0.0])
    print repr(axis(u, v, normalize=True))
    # Vector([-0.0, 1.0, 0.0])
    print repr(v.axis(u, normalize=True))
    # Vector([-0.0, -1.0, 0.0])
    print repr(axis(VectorN(u), VectorN(v), normalize=True))
    # VectorN([-0.0, 1.0, 0.0])
    print angle(u, v)
    # 0.785398163397
    print v.angle(u)
    # 0.785398163397
    print angle(VectorN(u), VectorN(v))
    # 0.785398163397
    print cotan(u, v)
    # 1.0
    print repr(u.rotateTo(v))
    # Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(u.axis(v), u.angle(v)))
    # Vector([0.707106781187, 0.0, -0.707106781187])
    q = Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(q))
    # Vector([0.707106781187, 0.0, -0.707106781187])
    print u.distanceTo(v)
    # 0.765309087885
    print u.isParallel(v)
    # False
    print u.isParallel(2 * u)
    # True
    print repr(u.blend(v))
    # Vector([0.8535, 0.0, -0.3535])

    print "end tests Vector"

def _testMPoint():

    print "Point class", dir(Point)
    print hasattr(Point, 'data')
    p = Point()
    print repr(p)
    # Point([0.0, 0.0, 0.0])
    print "Point instance", dir(p)
    print hasattr(p, 'data')
    print repr(p.data)
    # <maya.OpenMaya.Point; proxy of <Swig Object of type 'Point *' at 0x84a1270> >

    p = Point(1, 2, 3)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    v = Vector(p)
    print repr(v)
    # Vector([1.0, 2.0, 3.0])
    V = VectorN(p)
    print repr(V)
    # VectorN([1.0, 2.0, 3.0, 1.0])
    print list(p)
    # [1.0, 2.0, 3.0]
    print len(p)
    # 3
    print p.size
    # 4
    print p.x, p.y, p.z, p.w
    # 1.0 2.0 3.0 1.0
    print p[0], p[1], p[2], p[3]
    # 1.0 2.0 3.0 1.0
    p.get()
    # 1.0 2.0 3.0 1.0

    # accepted by api
    q = _api.MPoint()
    print q.distanceTo(p)
    # 3.74165738677

    # support for non cartesian points still there

    p = Point(1, 2, 3, 2)
    print repr(p)
    # Point([1.0, 2.0, 3.0, 2.0])
    v = Vector(p)
    print repr(v)
    # Vector([0.5, 1.0, 1.5])
    V = VectorN(p)
    print repr(V)
    # VectorN([1.0, 2.0, 3.0, 2.0])
    print list(p)
    # [1.0, 2.0, 3.0, 2.0]
    print len(p)
    # 4
    print p.size
    # 4
    print p.x, p.y, p.z, p.w
    # 1.0 2.0 3.0 2.0
    print p[0], p[1], p[2], p[3]
    # 1.0 2.0 3.0 2.0
    p.get()
    # 1.0 2.0 3.0 2.0

    # accepted by api
    q = _api.MPoint()
    print q.distanceTo(p)
    # 1.87082869339

    p = Point(_api.MPoint())
    print repr(p)
    # Point([0.0, 0.0, 0.0])
    p = Point(1)
    print repr(p)
    # Point([1.0, 1.0, 1.0])
    p = Point(1, 2)
    print repr(p)
    # Point([1.0, 2.0, 0.0])
    p = Point(1, 2, 3)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    p = Point(_api.MPoint(1, 2, 3))
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    p = Point(VectorN(1, 2))
    print repr(p)
    # Point([1.0, 2.0, 0.0])
    p = Point(Vector(1, 2, 3))
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    p = Point(_api.MVector(1, 2, 3))
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    p = Point(VectorN(1, 2, 3, 4))
    print repr(p)
    # Point([1.0, 2.0, 3.0, 4.0])
    print repr(Vector(p))
    # Vector([0.25, 0.5, 0.75])
    print repr(VectorN(p))
    # VectorN([1.0, 2.0, 3.0, 4.0])
    p = Point(p, w=1)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    print repr(Vector(p))
    # Vector([1.0, 2.0, 3.0])
    print repr(VectorN(p))
    # VectorN([1.0, 2.0, 3.0, 1.0])

    p = Point.origin
    print repr(p)
    # Point([0.0, 0.0, 0.0])
    p = Point.xAxis
    print repr(p)
    # Point([1.0, 0.0, 0.0])

    p = Point(1, 2, 3)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    print repr(p + Vector([1, 2, 3]))
    # Point([2.0, 4.0, 6.0])
    print repr(p + Point([1, 2, 3]))
    # Point([2.0, 4.0, 6.0])
    print repr(p + [1, 2, 3])
    # Point([2.0, 4.0, 6.0])
    print repr(p + [1, 2, 3, 1])
    # Point([2.0, 4.0, 6.0])
    print repr(p + Point([1, 2, 3, 1]))
    # Point([2.0, 4.0, 6.0])
    print repr(p + [1, 2, 3, 2])
    # Point([2.0, 4.0, 6.0, 3.0])    TODO : convert to Point always?
    print repr(p + Point([1, 2, 3, 2]))
    # Point([1.5, 3.0, 4.5])

    print repr(Vector([1, 2, 3]) + p)
    # Point([2.0, 4.0, 6.0])
    print repr(Point([1, 2, 3]) + p)
    # Point([2.0, 4.0, 6.0])
    print repr([1, 2, 3] + p)
    # Point([2.0, 4.0, 6.0])
    print repr([1, 2, 3, 1] + p)
    # Point([2.0, 4.0, 6.0])
    print repr(Point([1, 2, 3, 1]) + p)
    # Point([2.0, 4.0, 6.0])
    print repr([1, 2, 3, 2] + p)
    # Point([2.0, 4.0, 6.0, 3.0])
    print repr(Point([1, 2, 3, 2]) + p)
    # Point([1.5, 3.0, 4.5])

    # various operation, on cartesian and non cartesian points

    print "p = Point(1, 2, 3)"
    p = Point(1, 2, 3)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    print "p/2"
    print repr(p / 2)
    # Point([0.5, 1.0, 1.5])
    print "p*2"
    print repr(p * 2)
    # Point([2.0, 4.0, 6.0])
    print "q = Point(0.25, 0.5, 1.0)"
    q = Point(0.25, 0.5, 1.0)
    print repr(q)
    # Point([0.25, 0.5, 1.0])
    print repr(q + 2)
    # Point([2.25, 2.5, 3.0])
    print repr(q / 2)
    # Point([0.125, 0.25, 0.5])
    print repr(p + q)
    # Point([1.25, 2.5, 4.0])
    print repr(p - q)
    # Vector([0.75, 1.5, 2.0])
    print repr(q - p)
    # Vector([-0.75, -1.5, -2.0])
    print repr(p - (p - q))
    # Point([0.25, 0.5, 1.0])
    print repr(Vector(p) * Vector(q))
    # 4.25
    print repr(p * q)
    # 4.25
    print repr(p / q)
    # Point([4.0, 4.0, 3.0])

    print "p = Point(1, 2, 3)"
    p = Point(1, 2, 3)
    print repr(p)
    # Point([1.0, 2.0, 3.0])
    print "p/2"
    print repr(p / 2)
    # Point([0.5, 1.0, 1.5])
    print "p*2"
    print repr(p * 2)
    # Point([2.0, 4.0, 6.0])
    print "q = Point(0.25, 0.5, 1.0, 0.5)"
    q = Point(0.25, 0.5, 1.0, 0.5)
    print repr(q)
    # Point([0.25, 0.5, 1.0, 0.5])
    r = q.deepcopy()
    print repr(r)
    # Point([0.25, 0.5, 1.0, 0.5])
    print repr(r.cartesianize())
    # Point([0.5, 1.0, 2.0])
    print repr(r)
    # Point([0.5, 1.0, 2.0])
    print repr(q)
    # Point([0.25, 0.5, 1.0, 0.5])
    print repr(q.cartesian())
    # Point([0.5, 1.0, 2.0])
    r = q.deepcopy()
    print repr(r)
    # Point([0.25, 0.5, 1.0, 0.5])
    print repr(r.rationalize())
    # Point([0.5, 1.0, 2.0, 0.5])
    print repr(r)
    # Point([0.5, 1.0, 2.0, 0.5])
    print repr(q.rational())
    # Point([0.5, 1.0, 2.0, 0.5])
    r = q.deepcopy()
    print repr(r.homogenize())
    # Point([0.125, 0.25, 0.5, 0.5])
    print repr(r)
    # Point([0.125, 0.25, 0.5, 0.5])
    print repr(q.homogen())
    # Point([0.125, 0.25, 0.5, 0.5])
    print repr(q)
    # Point([0.25, 0.5, 1.0, 0.5])
    print Vector(q)
    # [0.5, 1.0, 2.0]
    print Vector(q.cartesian())
    # [0.5, 1.0, 2.0]
    # ignore w
    print "q/2"
    print repr(q / 2)
    # Point([0.125, 0.25, 0.5, 0.5])
    print "q*2"
    print repr(q * 2)
    # Point([0.5, 1.0, 2.0, 0.5])
    print repr(q + 2)             # cartesianize is done by Vector add
    # Point([2.5, 3.0, 4.0])

    print repr(q)
    # Point([0.25, 0.5, 1.0, 0.5])
    print repr(p + Vector(1, 2, 3))
    # Point([2.0, 4.0, 6.0])
    print repr(q + Vector(1, 2, 3))
    # Point([1.5, 3.0, 5.0])
    print repr(q.cartesian() + Vector(1, 2, 3))
    # Point([1.5, 3.0, 5.0])

    print repr(p - q)
    # Vector([0.5, 1.0, 1.0])
    print repr(p - q.cartesian())
    # Vector([0.5, 1.0, 1.0])
    print repr(q - p)
    # Vector([-0.5, -1.0, -1.0])
    print repr(p - (p - q))
    # Point([0.5, 1.0, 2.0])
    print repr(Vector(p) * Vector(q))
    # 4.25
    print repr(p * q)
    # 4.25
    print repr(p / q)             # need explicit homogenize as division not handled by api
    # Point([4.0, 4.0, 3.0, 2.0])    TODO : what do we want here ?
    # Vector([2.0, 2.0, 1.5])
    # additionnal methods

    print "p = Point(x=1, y=2, z=3)"
    p = Point(x=1, y=2, z=3)
    print p.length()
    # 3.74165738677
    print p[:1].length()
    # 1.0
    print p[:2].length()
    # 2.2360679775
    print p[:3].length()
    # 3.74165738677

    p = Point(1.0, 0.0, 0.0)
    q = Point(0.707, 0.0, -0.707)
    print repr(p)
    # Point([1.0, 0.0, 0.0, 1.0])
    print repr(q)
    # Point([0.707, 0.0, -0.707, 1.0])
    print repr(q - p)
    # Vector([-0.293, 0.0, -0.707])
    print repr(axis(Point.origin, p, q))
    # Vector([-0.0, 0.707, 0.0])
    print repr(Point.origin.axis(p, q))
    # Vector([-0.0, 0.707, 0.0])
    print repr(Point.origin.axis(q, p))
    # Vector([0.0, -0.707, 0.0])
    print angle(Point.origin, p, q)
    # 0.785398163397
    print angle(Point.origin, q, p)
    # 0.785398163397
    print Point.origin.angle(p, q)
    # 0.785398163397
    print p.distanceTo(q)
    # 0.765309087885
    print (q - p).length()
    # 0.765309087885
    print cotan(Point.origin, p, q)
    # 1.0
    # obviously True
    print planar(Point.origin, p, q)
    # True
    r = center(Point.origin, p, q)
    print repr(r)
    # Point([0.569, 0.0, -0.235666666667, 1.0])
    print planar(Point.origin, p, q, r)
    # True
    print planar(Point.origin, p, q, r + Vector(0.0, 0.1, 0.0))
    # False
    print bWeights(r, Point.origin, p, q)
    # (0.33333333333333337, 0.33333333333333331, 0.33333333333333343)

    p = Point([0.33333, 0.66666, 1.333333, 0.33333])
    print repr(round(p, 3))
    # Point([0.333, 0.667, 1.333, 0.333])

    print "end tests Point"

def _testMColor():

    print "Color class", dir(Color)
    print hasattr(Color, 'data')
    c = Color()
    print repr(c)
    # Color([0.0, 0.0, 0.0, 1.0])
    print "Color instance", dir(c)
    print hasattr(c, 'data')
    print repr(c.data)
    # Color([0.0, 0.0, 0.0, 1.0])
    c = Color(_api.MColor())
    print repr(c)
    # Color([0.0, 0.0, 0.0, 1.0])
    # using api convetion of single value would mean alpha
    # instead of VectorN convention of filling all with value
    # which would yield # Color([0.5, 0.5, 0.5, 0.5]) instead
    # This would break coerce behavior for Color
    print "c = Color(0.5)"
    c = Color(0.5)
    print repr(c)
    # Color([0.5, 0.5, 0.5, 0.5])
    print "c = round(Color(128, quantize=255), 2)"
    c = Color(128, quantize=255)
    print repr(c)
    # Color([0.501999974251, 0.501999974251, 0.501999974251, 0.501999974251])
    c = Color(255, 128, b=64, a=32, quantize=255)
    print repr(c)
    # Color([1.0 0.501999974251 0.250999987125 0.125490196078])

    print "c = Color(1, 1, 1)"
    c = Color(1, 1, 1)
    print repr(c)
    # Color([1.0, 1.0, 1.0, 1.0])
    print "c = round(Color(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)"
    c = round(Color(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # Color([1.0, 0.5, 1.0, 1.0])

    print "c = round(Color(255, b=128, quantize=255, mode='rgb'), 2)"
    c = round(Color(255, b=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # Color([1.0, 1.0, 0.5, 1.0])
    print "c = Color(1, 0.5, 2, 0.5)"
    c = Color(1, 0.5, 2, 0.5)
    print repr(c)
    # Color([1.0, 0.5, 2.0, 0.5])
    print "c = Color(0, 65535, 65535, quantize=65535, mode='hsv')"
    c = Color(0, 65535, 65535, quantize=65535, mode='hsv')
    print repr(c)
    # Color([1.0, 0.0, 0.0, 1.0])
    print "c.rgb"
    print repr(c.rgb)
    # (1.0, 0.0, 0.0)
    print "c.hsv"
    print repr(c.hsv)
    # (0.0, 1.0, 1.0)
    d = Color(c, v=0.5, mode='hsv')
    print repr(d)
    # Color([0.5, 0.0, 0.0, 1.0])
    print repr(d.hsv)
    # (0.0, 1.0, 0.5)
    print "c = Color(Color.blue, v=0.5)"
    c = Color(Color.blue, v=0.5)
    print repr(c)
    # Color([0.0, 0.0, 0.5, 1.0])
    print "c.hsv"
    print c.hsv
    # (0.66666666666666663, 1.0, 0.5)
    c.r = 1.0
    print repr(c)
    # Color([1.0, 0.0, 0.5, 1.0])
    print "c.hsv"
    print c.hsv
    # (0.91666666666666663, 1.0, 1.0)

    print "c = Color(1, 0.5, 2, 0.5).clamp()"
    c = Color(1, 0.5, 2, 0.5).clamp()
    print repr(c)
    # Color([1.0, 0.5, 1.0, 0.5])
    print c.hsv
    # (0.83333333333333337, 0.5, 1.0)

    print "Color(c, v=0.5)"
    d = Color(c, v=0.5)
    print repr(d)
    # Color([0.5, 0.25, 0.5, 0.5])
    print "d.hsv"
    print d.hsv
    # (0.83333333333333337, 0.5, 0.5)

    print "c = Color(0.0, 0.5, 1.0, 0.5)"
    c = Color(0.0, 0.5, 1.0, 0.5)
    print repr(c)
    # Color(0.0, 0.5, 1.0, 0.5)
    print "d = c.gamma(2.0)"
    d = c.gamma(2.0)
    print repr(d)
    # Color([0.0, 0.25, 1.0, 0.5])

    print "c = Color.red.blend(Color.blue, 0.5)"
    c = Color.red.blend(Color.blue, 0.5)
    print repr(c)
    # Color([0.5, 0.0, 0.5, 1.0])
    print c.hsv
    # (0.83333333333333337, 1.0, 0.5)
    c = Color.red.hsvblend(Color.blue, 0.5)
    print repr(c)
    # Color([1.0, 0.0, 1.0, 1.0])
    print c.hsv
    # (0.83333333333333337, 1.0, 1.0)

    print "c = Color(0.25, 0.5, 0.75, 0.5)"
    c = Color(0.25, 0.5, 0.75, 0.5)
    print repr(c)
    # Color([0.25, 0.5, 0.75, 0.5])
    print "d = Color.black"
    d = Color.black
    print repr(d)
    # Color([0.0, 0.0, 0.0, 1.0])
    print "c.over(d)"
    print repr(c.over(d))
    # Color([0.125, 0.25, 0.375, 1.0])
    print "d.over(c)"
    print repr(d.over(c))
    # Color([0.0, 0.0, 0.0, 0.5])
    print "c.premult()"
    print repr(c.premult())
    # Color([0.125, 0.25, 0.375, 1.0])

    # herited from Vector

    print "c = Color(0.25, 0.5, 1.0, 1.0)"
    c = Color(0.25, 0.5, 1.0, 1.0)
    print repr(c)
    # Color([0.25, 0.5, 1.0, 1.0])
    print "d = Color(2.0, 1.0, 0.5, 0.25)"
    d = Color(2.0, 1.0, 0.5, 0.25)
    print repr(d)
    # Color([2.0, 1.0, 0.5, 0.25])
    print "-c"
    print repr(-c)
    # Color([-0.25, -0.5, -1.0, 1.0])
    print "e = c*d"
    e = c * d
    print repr(e)
    # Color([0.5, 0.5, 0.5, 0.25])
    print "e + 2"
    print repr(e + 2)
    # Color([2.5, 2.5, 2.5, 0.25])
    print "e * 2.0"               # mult by scalar float is defined in api for colors and also multiplies alpha
    print repr(e * 2.0)
    # Color([1.0, 1.0, 1.0, 0.5])
    print "e / 2.0"               # as is divide, that ignores alpha now for some reason
    print repr(e / 2.0)
    # Color([0.25, 0.25, 0.25, 0.25])
    print "e+Vector(1, 2, 3)"
    print repr(e + Vector(1, 2, 3))
    # Color([1.5, 2.5, 3.5, 0.25])
    # how to handle operations on colors ?
    # here behaves like api but does it make any sense
    # for colors as it is now ?
    print "c+c"
    print repr(c + c)
    # Color([0.5, 1.0, 2.0, 1.0])
    print "c+d"
    print repr(c + d)
    # Color([2.25, 1.5, 1.5, 1.0])
    print "d-c"
    print repr(d - c)
    # Color([1.75, 0.5, -0.5, 0.25])

    print "end tests Color"

def _testMMatrix():

    print "Matrix class", dir(Matrix)
    m = Matrix()
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print m[0, 0]
    # 1.0
    print repr(m[0:2, 0:3])
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print m(0, 0)
    # 1.0
    print "Matrix instance:", dir(m)
    print Matrix.__readonly__
    print Matrix.__slots__
    print Matrix.shape
    print Matrix.ndim
    print Matrix.size
    print m.shape
    print m.ndim
    print m.size
    # should fail
    m.shape = (4, 4)
    m.shape = 2

    print dir(Space)

    m = Matrix.identity
    # inherits from MatrixN --> Array
    print isinstance(m, MatrixN)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.Matrix
    print isinstance(m, _api.MMatrix)
    # True
    # accepted directly by API methods
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print repr(m)
    print repr(n)

    # inits
    m = Matrix(range(16))
    print m.formated()
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]
    M = Array(range(16), shape=(8, 2))
    m = Matrix(M)
    print m.formated()
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]
    M = MatrixN(range(9), shape=(3, 3))
    m = Matrix(M)
    print m.formated()
    #[[0.0, 1.0, 2.0, 0.0],
    # [3.0, 4.0, 5.0, 0.0],
    # [6.0, 7.0, 8.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    # inherits from MatrixN --> Array
    print isinstance(m, MatrixN)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.Matrix
    print isinstance(m, _api.MMatrix)
    # True
    # accepted directly by API methods
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print repr(m)
    print repr(n)
    t = _api.MTransformationMatrix()
    t.setTranslation(Vector(1, 2, 3), _api.MSpace.kWorld)
    m = Matrix(t)
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    m = Matrix(m, a30=10)
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [10.0, 2.0, 3.0, 1.0]]
    # should fail
    print "Matrix(range(20)"
    try:
        m = Matrix(range(20))
        print m.formated()
    except:
        print "will raise ValueError: cannot initialize a Matrix of shape (4, 4) from (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), some information would be lost, use an explicit resize or trim"

    m = Matrix.identity
    M = m.trimmed(shape=(3, 3))
    print repr(M)
    # MatrixN([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    print M.formated()
    #[[1.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0],
    # [0.0, 0.0, 1.0]]
    try:
        m.trim(shape=(3, 3))
    except:
        print "will raise TypeError: new shape (3, 3) is not compatible with class Matrix"

    print m.nrow
    # 4
    print m.ncol
    # 4
    # should fail
    try:
        m.nrow = 3
    except:
        print "will raise TypeError: new shape (3, 4) is not compatible with class Matrix"
    print list(m.row)
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]
    print list(m.col)
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]

    m = Matrix(MatrixN(range(9), shape=(3, 3)).trimmed(shape=(4, 4), value=10))
    print m.formated()
    #[[0.0, 1.0, 2.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]

    print m.get()
    # ((0.0, 1.0, 2.0, 10.0), (3.0, 4.0, 5.0, 10.0), (6.0, 7.0, 8.0, 10.0), (10.0, 10.0, 10.0, 10.0))
    print repr(m[0])
    # [0.0, 1.0, 2.0, 10.0]
    m[0] = 10
    print m.formated()
    #[[10.0, 10.0, 10.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]
    print (10 in m)
    # True
    print list(m)
    # [Array([10.0, 10.0, 10.0, 10.0]), Array([3.0, 4.0, 5.0, 10.0]), Array([6.0, 7.0, 8.0, 10.0]), Array([10.0, 10.0, 10.0, 10.0])]
    print list(m.flat)
    # [10.0, 10.0, 10.0, 10.0, 3.0, 4.0, 5.0, 10.0, 6.0, 7.0, 8.0, 10.0, 10.0, 10.0, 10.0, 10.0]

    u = Vector.xAxis
    v = Vector.yAxis
    print Vector.xAxis
    print str(Vector.xAxis)
    print unicode(Vector.xAxis)
    print repr(Vector.xAxis)

    print "u = Vector.xAxis:"
    print repr(u)

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print "m:"
    print round(m, 2).formated()
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]

    x = Vector.xAxis
    y = Vector.yAxis
    z = Vector.zAxis
    u = Vector(1, 2, 3)
    print "u:"
    print repr(u)
    # Vector([1, 2, 3])
    print "u*m"
    print repr(u * m)
    # Vector([6.31319304794, 0.378937381963, -0.5])
    print "m*u"
    print repr(m * u)
    # Vector([-1.5, 2.19067069768, 0.896575472168])

    p = Point(1, 10, 100, 1)
    print "p:"
    print repr(p)
    # Point([1.0, 10.0, 100.0, 1.0])
    print "p*m"
    print repr(p * m)
    # Point([196.773355709, -40.1045507576, 2.5, 1.0])
    print "m*p"
    print repr(m * p)
    # Point([-50.0, 9.91807730799, -3.24452924947, 322.0])

    print "v = [1, 2, 3]*m"
    v = VectorN([1, 2, 3]) * m
    print repr(v)
    # VectorN([6.31319304794, 0.378937381963, -0.5])
    print "v = [1, 2, 3, 1]*m"
    v = VectorN([1, 2, 3, 1]) * m
    print repr(v)
    # VectorN([7.31319304794, 2.37893738196, 2.5, 1.0])
    # should fail
    print "VectorN([1, 2, 3, 4, 5])*m"
    try:
        v = VectorN([1, 2, 3, 4, 5]) * m
    except:
        print "Will raise ValueError: vector of size 5 and matrix of shape (4, 4) are not conformable for a VectorN * MatrixN multiplication"

    # herited

    print "m = Matrix(range(1, 17))"
    m = Matrix(range(1, 17))
    print m.formated()
    #[[1.0, 2.0, 3.0, 4.0],
    # [5.0, 6.0, 7.0, 8.0],
    # [9.0, 10.0, 11.0, 12.0],
    # [13.0, 14.0, 15.0, 16.0]]
    # element wise
    print "[1, 10, 100]*m"
    print repr([1, 10, 100] * m)
    # Matrix([[1.0, 20.0, 300.0, 0.0], [5.0, 60.0, 700.0, 0.0], [9.0, 100.0, 1100.0, 0.0], [13.0, 140.0, 1500.0, 0.0]])
    print "M = MatrixN(range(20), shape=(4, 5))"
    M = MatrixN(range(1, 21), shape=(4, 5))
    print M.formated()
    #[[1, 2, 3, 4, 5],
    # [6, 7, 8, 9, 10],
    # [11, 12, 13, 14, 15],
    # [16, 17, 18, 19, 20]]
    print "m*M"
    n = m * M
    print (n).formated()
    #[[110.0, 120.0, 130.0, 140.0, 150.0],
    # [246.0, 272.0, 298.0, 324.0, 350.0],
    # [382.0, 424.0, 466.0, 508.0, 550.0],
    # [518.0, 576.0, 634.0, 692.0, 750.0]]
    print util.clsname(n)
    # MatrixN
    print "m*2"
    n = m * 2
    print (n).formated()
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]
    print util.clsname(n)
    # Matrix
    print "2*m"
    n = 2 * m
    print (n).formated()
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]
    print util.clsname(n)
    # Matrix
    print "m+2"
    n = m + 2
    print (n).formated()
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]
    print util.clsname(n)
    # Matrix
    print "2+m"
    n = 2 + m
    print (n).formated()
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]
    print util.clsname(n)
    # Matrix
    try:
        m.setToProduct(m, M)
    except:
        print """Will raise TypeError:  cannot initialize a Matrix of shape (4, 4) from (Array([0, 1, 2, 3, 4]), Array([5, 6, 7, 8, 9]), Array([10, 11, 12, 13, 14]), Array([15, 16, 17, 18, 19])) of shape (4, 5),
                                        as it would truncate data or reduce the number of dimensions"""

    print m.isEquivalent(m * M)
    # False

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print "m:"
    print round(m, 2).formated()
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    print "m.transpose():"
    print round(m.transpose(), 2).formated()
    #[[0.0, 0.26, 1.93, 1.0],
    # [0.0, 0.97, -0.52, 2.0],
    # [-0.5, 0.0, 0.0, 3.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print "m.isSingular():"
    print m.isSingular()
    # False
    print "m.inverse():"
    print round(m.inverse(), 2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, 0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print "m.adjoint():"
    print round(m.adjoint(), 2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print "m.adjugate():"
    print round(m.adjugate(), 2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print "m.homogenize():"
    print round(m.homogenize(), 2).formated()
    #[[0.0, 0.0, -1.0, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [0.97, -0.26, -0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    print "m.det():"
    print m.det()
    # 1.0
    print "m.det4x4():"
    print m.det4x4()
    # 1.0
    print "m.det3x3():"
    print m.det3x3()
    # 1.0
    print "m.weighted(0.5):"
    print round(m.weighted(0.5), 2).formated()
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]
    print "m.blend(Matrix.identity, 0.5):"
    print round(m.blend(Matrix.identity, 0.5), 2).formated()
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]

    print "end tests Matrix"

def _testMTransformationMatrix():

    q = Quaternion()
    print repr(q)
    # Quaternion([0.0, 0.0, 0.0, 1.0])
    q = Quaternion(1, 2, 3, 0.5)
    print repr(q)
    # Quaternion([1.0, 2.0, 3.0, 0.5])
    q = Quaternion(0.785, 0.785, 0.785, "xyz")
    print repr(q)
    # Quaternion([0.191357439088, 0.461717715523, 0.191357439088, 0.844737481223])

    m = Matrix()
    m.rotate = q
    print repr(m)
    # Matrix([[0.500398163355, 0.499999841466, -0.706825181105, 0.0], [-0.146587362969, 0.853529322022, 0.499999841466, 0.0], [0.853295859083, -0.146587362969, 0.500398163355, 0.0], [0.0, 0.0, 0.0, 1.0]])

    print "TransformationMatrix class", dir(TransformationMatrix)
    m = TransformationMatrix()
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print m[0, 0]
    # 1.0
    print m[0:2, 0:3]
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print "TransformationMatrix instance:", dir(m)
    print TransformationMatrix.__readonly__
    print TransformationMatrix.__slots__
    print TransformationMatrix.shape
    print TransformationMatrix.ndim
    print TransformationMatrix.size
    print m.shape
    print m.ndim
    print m.size
    # should fail
    m.shape = (4, 4)
    m.shape = 2

    print dir(Space)

    m = TransformationMatrix.identity
    # inherits from MatrixN --> Array
    print isinstance(m, MatrixN)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.TransformationMatrix and _api.Matrix
    print isinstance(m, _api.MTransformationMatrix)
    # True
    print isinstance(m, _api.MMatrix)
    # True

    # accepted directly by API methods
    n = _api.MMatrix()
    n = n.setToProduct(m, m)
    print repr(n)

    n = _api.MTransformationMatrix()
    n = n.assign(m)
    print repr(n)

    m = TransformationMatrix.identity
    m.rotation = Quaternion()
    print repr(m)
    print m.formated()

    n = TransformationMatrix.identity
    n.translation = Vector(1, 2, 3)
    print n.formated()
    print repr(n)

    o = m * n
    print repr(o)
    print o.formated()

    print "end tests TransformationMatrix"

if __name__ == '__main__':
    print Distance.getInternalUnit()
    # centimeters
    print Distance.getUIUnit()
    # centimeters
    Distance.setUIUnit('meters')
    print Distance.getUIUnit()
    # meters
    d = Distance(12)
    print d.unit
    # meters
    print d
    1200.0
    print repr(d)
    Distance(12.0, unit='meters')
    print d.asUnit()
    12.0
    print d.asInternalUnit()
    1200.0

    import doctest
    doctest.testmod(verbose=True)

    _testMVector()
    _testMPoint()
    _testMColor()
    _testMMatrix()
    _testMTransformationMatrix()

"""
A wrap of Maya's MVector, MPoint, MColor, MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation types
"""

import inspect
import math, copy
import itertools, operator, colorsys

import pymel.util as util
import pymel.mayahook as mayahook
import pymel.api as _api
from pymel.util.arrays import *
import pymel.factories as _factories

# patch some Maya api classes that miss __iter__ to make them iterable / convertible to list
def _patchMVector() :
    def __len__(self):
        """ Number of components in the Maya api MVector, ie 3 """
        return 3
    type.__setattr__(_api.MVector, '__len__', __len__)
    def __iter__(self):
        """ Iterates on all components of a Maya api MVector """
        for i in xrange(len(self)) :
            yield self[i]
    type.__setattr__(_api.MVector, '__iter__', __iter__)

def _patchMPoint() :
    def __len__(self):
        """ Number of components in the Maya api MPoint, ie 4 """
        return 4
    type.__setattr__(_api.MPoint, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MPoint """
        for i in xrange(len(self)) :
            yield self[i]
    type.__setattr__(_api.MPoint, '__iter__', __iter__)
  
def _patchMColor() :
    def __len__(self):
        """ Number of components in the Maya api MColor, ie 4 """
        return 4
    type.__setattr__(_api.MColor, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MColor """
        for i in xrange(len(self)) :
            yield self[i]
    type.__setattr__(_api.MColor, '__iter__', __iter__)  
    
def _patchMMatrix() :
    def __iter__(self):
        """ Iterates on all rows of a Maya api MMatrix """
        for r in xrange(4) :
            yield [_api.MScriptUtil.getDoubleArrayItem(self[r], c) for c in xrange(4)]
    type.__setattr__(_api.MMatrix, '__iter__', __iter__)

def _patchMTransformationMatrix() :
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MTransformationMatrix """
        return self.asMatrix().__iter__()
    type.__setattr__(_api.MTransformationMatrix, '__iter__', __iter__)

_patchMVector()
_patchMPoint()
_patchMColor()
_patchMMatrix()
_patchMTransformationMatrix()

# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(_factories.MetaMayaTypeWrapper) :
    """ A metaclass to wrap Maya array type classes such as MVector, MMatrix """ 
             
    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as MVector or MMatrix """
            
        if 'shape' in classdict :
            # fixed shape means also fixed ndim and size
            shape = classdict['shape']
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            if 'ndim' not in classdict :
                classdict['ndim'] = ndim
            elif classdict['ndim'] != ndim :
                raise ValueError, "class %s shape definition %s and number of dimensions definition %s do not match" % (classname, shape, ndim)
            if 'size' not in classdict :
                classdict['size'] = size
            elif classdict['size'] != size :
                raise ValueError, "class %s shape definition %s and size definition %s do not match" % (classname, shape, size)
                                          
        # create the new class   
        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)

        try :
            apicls = newcls.apicls 
        except :
            apicls = None        
        try :
            shape = newcls.shape 
        except :
            shape = None
        try :
            cnames = newcls.cnames
        except :
            cnames = ()
            
        if shape is not None :
            # fixed shape means also fixed ndim and size
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            
            if cnames :
                # definition for component names
                type.__setattr__(newcls, 'cnames', cnames ) 
                subsizes = [reduce(operator.mul, shape[i+1:], 1) for i in xrange(ndim)]
                for index, compname in enumerate(cnames) :
                    coords = []
                    for i in xrange(ndim) :
                        c = index//subsizes[i]
                        index -= c*subsizes[i]
                        coords.append(c)
                    if len(coords) == 1 :
                        coords = coords[0]
                    else :
                        coords = tuple(coords)
                    p = eval("property( lambda self: self.__getitem__(%s) ,  lambda self, val: self.__setitem__(%s,val) )" % (coords, coords))
                    if compname not in classdict :
                        type.__setattr__(newcls, compname, p)
                    else :
                        raise AttributeError, "component name %s clashes with class method %r" % (compname, classdict[compname])                 
        elif cnames :
            raise ValueError, "can only define component names for classes with a fixed shape/size"
         
        # constants for shape, ndim, size
        if shape is not None :
            type.__setattr__(newcls, 'shape', shape)
        if ndim is not None :
            type.__setattr__(newcls, 'ndim', ndim)
        if size is not None :
            type.__setattr__(newcls, 'size', size)                        
        #__slots__ = ['_data', '_shape', '_size']    
        # add component names to read-only list
        readonly = newcls.__readonly__
        if hasattr(newcls, 'shape') :
            readonly['shape'] = None 
        if hasattr(newcls, 'ndim') :
            readonly['ndim'] = None  
        if hasattr(newcls, 'size') :
            readonly['size'] = None                                 
        if 'cnames' not in readonly :
            readonly['cnames'] = None
        type.__setattr__(newcls, '__readonly__', readonly)      

        print "created class", newcls
        print "bases", newcls.__bases__
        print "readonly", newcls.__readonly__
        print "slots", newcls.__slots__
        return newcls  


# conversion to MVector or a base class of MVector if not possible
def vectorOrArray(value) :
    value = MVector._convert(value)
    
    return value

# same with MMatrix
def matrixOrArray(value) :
    value = MMatrix._convert(value)
    
    return value

# generic math function that can operate on Arrays herited from arrays
# (min, max, sum, prod...)

# Functions that work on vectors will now be inherited from Array and properly defer
# to the class methods
               
class MVector(Vector) :
    """ A 3 dimensional vector class that wraps Maya's api MVector class,
        >>> v = MVector(1, 2, 3)
        >>> w = MVector(x=1, z=2)
        >>> z = MVector(MVector.xAxis, z=1)
        """
    __metaclass__ = MetaMayaArrayTypeWrapper
    __slots__ = ()
    # class specific info
    apicls = _api.MVector
    cnames = ('x', 'y', 'z')
    shape = (3,)

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (3,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on MVector, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)        
        
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        """ __init__ method, valid for MVector, MPoint and MColor classes """
        cls = self.__class__
        
        if args :
            # allow both forms for arguments
            if len(args)==1 and hasattr(args[0], '__iter__') :
                args = args[0]
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                # special exception to the rule that you cannot drop data in Arrays __init__
                # to allow all conversion from MVector derived classes (MPoint, MColor) to a base class           
                if isinstance(args, MVector) or isinstance(args, _api.MVector) or isinstance(args, _api.MPoint) or isinstance(args, _api.MColor) :
                    for a in args :
                        print a
                    largs = list(args)
                    args = tuple(args)
                    if len(args) > len(self) :
                        args = args[slice(self.shape[0])]
                super(Vector, self).__init__(*args)
                    
                    
#                    shape = kwargs.get('shape', None)
#                    ndim = kwargs.get('ndim', None)
#                    size = kwargs.get('size', None)
#                    # must be expanded with class constants, not Vector's
#                    shape, ndim, size = cls._expandshape(shape, ndim, size)                                                 
#                    nargs = Vector(*args, **{'shape':shape})
                    
#                    nbargs = len(nargs)
#                    if nbargs != cls.size :
#                        # to protect from forced casting from longer data
#                        if nbargs > cls.size and not isinstance(args, cls) :
#                            raise ValueError, "could not cast %s to %s of size %s, some data would be lost" % (args, cls.__name__, cls.size)
#                        l = list(self.flat)
#                        for i in xrange(min(nbargs, cls.size)) :
#                            l[i] = float(nargs[i])
#                    else :
#                        l = list(nargs.flat)
#                    try :
#                        self.assign(l)
#                    except :
#                        raise TypeError, "in %s%s, arguments do not fit class definition, check help(%s) " % (cls.__name__, tuple(args), cls.__name__)
#            self.assign(new)
            
        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)) :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    if float(l[i]) != float(kwargs[c]) :
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp :
                try :
                    self.assign(l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__) 

    # for compatibility with base classes Array that actually hold a nested list in their _data attribut
    # here, there is no _data attribute as we subclass api.MVector directly, thus v.data is v
    # for wraps 
                          
    def _getdata(self):
        return self
    def _setdata(self, value):
        self.assign(value) 
    def _deldata(self):
        if hasattr(self.apicls, 'clear') :
            self.apicls.clear(self)  
        else :
            raise NotImplemented, "cannot clear stored elements of %s" % (self.__class__.__name__)
          
    data = property(_getdata, _setdata, _deldata, "The MVector data")                           
                          
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                   
                                                 
    def assign(self, value):
        # don't accept instances as assign works on exact types
        if type(value) != self.apicls :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        ms = _api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)])

    def __len__(self):
        """ Number of components in the MVector instance, 3 for MVector, 4 for MPoint and MColor """
        return self.apicls.__len__(self)
    
    # __getitem__ / __setitem__ override
    def __getitem__(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__') :
            i = list(i)
            if len(i) == 1 :
                i = i[0]
            else :
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice) :
            try :
                return list(self)[i]
            except :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else :
            if i < 0 :
                i = self.size + i
            if i<self.size and not i<0 :
                if hasattr(self.apicls, '__getitem__') :
                    return self.apicls.__getitem__(self, i)
                else :
                    return list(self)[i]
            else :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    # as api.MVector has no __setitem__ method
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
        v.__setitem__(i, a)
        self.assign(v) 
   
    # iterator override
     
    # TODO : support for optionnal __iter__ arguments           
    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        return self.apicls.__iter__(self.data)   
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()  
    
    # common operators herited from Vector
    
    # operators using the Maya API when applicable
    def __neg__(self):
        """ u.__neg__() <==> -u
            The unary minus operator. Negates the value of each of the components of u """        
        return self.__class__(self.apicls.__neg__(self)) 
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__add__(other)) 
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__radd__(other))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented   
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is convertible to a Vector (element-wise substration),
            substract v to every component of u if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__sub__(other))   
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is convertible to a Vector (element-wise substration),
            replace every component c of u by v-c if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__rsub__(other))      
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        try :
            return self.__class__(self.__sub__(other))
        except :
            return NotImplemented     
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the division of u by v if v is convertible to a Vector (element-wise division),
            divide every component of u by v if v is a scalar """  
        try :
            return self.__class__._convert(self.apicls.__div__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__div__(other))    
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of of the division of v by u if v is convertible to a Vector (element-wise division),
            invert every component of u and multiply it by v if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__rdiv__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__rdiv__(other))    
    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """        
        try :
            return self.__class__(self.__div__(other))
        except :
            return NotImplemented   
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v
            Equivalence test """
        try :
            return bool(self.apicls.__eq__(self, other))
        except :
            return bool(super(MVector, self).__eq__(other))             
#    # action depends on second object type
#    # TODO : do we really want to map dot product here as api does, overriding possibility for element wise mult ?
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the transformation of u by matrix v when v is a Matrix,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try :
            res = self.apicls.__mul__(self, other)
        except :
            res = super(MVector, self).__mul__(other)
        if util.isNumeric(res) :
            return res
        else :
            return self.__class__._convert(res)          
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the left side multiplication (pre-multiplication) of u by matrix v when v is a Matrix,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try :
            res = self.apicls.__rmul__(self, other)
        except :
            res = super(MVector, self).__rmul__(other)
        if util.isNumeric(res) :
            return res
        else :
            return self.__class__._convert(res)
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for MVector * MMatrix multiplication, in place transformation of u by MMatrix v
            or MVector by scalar multiplication only """
        try :
            return self.__class__(self.__mul__(other))
        except :
            return NotImplemented         
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two 3D vectors,
            if v is a Matrix, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, Vector) :
            return self.cross(other)
        elif isinstance(other, Matrix) :
            return self.transformAsNormal(other)
        else :
            return NotImplemented
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """
        try :        
            return self.__class__(self.__xor__(other))
        except :
            return NotImplemented        
         
    # wrap of API MVector methods    
    def isEquivalent(self, other, tol=_api.MVector_kTol):
        """ Returns true if both arguments considered as MVector are equal within the specified tolerance """
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MVector) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(MVector, nself).isEquivalent(nother, tol))            
    def isParallel(self, other, tol=_api.MVector_kTol):
        """ Returns true if both arguments considered as MVector are parallel within the specified tolerance """
        try :
            return bool(self.apicls.isParallel(MVector(self), MVector(other), tol))
        except :
            return super(MVector, self).isParallel(other, tol)
    def distanceTo(self, other):
        try :
            return MPoint.apicls.distanceTo(MPoint(self), MPoint(other))
        except :
            return super(MVector, self).dist(other)
    def length(self):
        """ Return the length of the vector """
        return self.apicls.length(self)
    def sqlength(self):
        """ Return the square length of the vector """
        return self.dot(self)    
#   sum herited from api class        
    def normal(self): 
        """ Return a normalized copy of self """ 
        return self.__class__(self.apicls.normal(self))
    def normalize(self):
        """ Performs an in place normalization of self """
        try :
            self.apicls.normalize(self)
        except :
            super(MVector, self).normalize()
    def angle(self, other):
        """  Returns the angle in radians between both arguments considered as MVector """
        if isinstance(other, MVector) :
            return self.apicls.angle(MVector(other))
        else :
            raise TypeError, "%r is not convertible to a MVector, check help(MVector)" % other 
    def rotateTo(self, other):
        """ Returns the Quaternion that represents the rotation of this MVector into the other
            argument considered as MVector about their mutually perpendicular axis """
        if isinstance(other, MVector) :
            return Quaternion(self.apicls.rotateTo(MVector(other)))
        else :
            raise TypeError, "%r is not a MVector instance" % other
    # TODO 
    def rotateBy(self, *args):
        pass    
    def transformAsNormal(self, other):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, MMatrix) :
            return self.__class__._convert(_api.MVector.transformAsNormal(MVector(self), MMatrix(other)))
        else :
            return self.__class__._convert(super(MVector, self).transformAsNormal(other))
        
    # additional methods, work on MVector
    def dot(self, other):
        """ dot product of two vectors """
        if isinstance(other, MVector) :
            return _api.MVector.__mul__(MVector(self), MVector(other))
        else :
            return super(MVector, self).dot(other)       
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, MVector) :
            return self.__class__._convert(_api.MVector.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).cross(other))              
    def axis(self, other, normalize=False):
        """ Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, MVector) :
            return self.__class__._convert(_api.MVector.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).axis(other)) 
    def angle(self, other):
        """ angle between two vectors """
        if isinstance(other, MVector) :
            return _api.MVector.angle(MVector(self), MVector(other))
        else :
            return super(MVector, self).angle(other)                           
    # cotan, blend, clamp are derived from Vector class

           
class MPoint(MVector, _api.MPoint):
    apicls = _api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)
    

#    # base methods are inherited from MVector

               
    # modified operators, when adding 2 MPoint consider second as MVector
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        if isinstance(other, MPoint) :
            other = MVector(other)       
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(MPoint, self).__add__(other)) 
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        if isinstance(other, MPoint) :
            other = MVector(other)                       
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MPoint, self).__radd__(other))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented     
  
          
    # specific api methods
    def cartesianize (self) :
        """ If this point instance is of the form P(W*x, W*y, W*z, W), for some scale factor W != 0,
            then it is reset to be P(x, y, z, 1).
            This will only work correctly if the point is in homogenous form or cartesian form.
            If the point is in rational form, the results are not defined. """
        self.apicls.cartesianize(self)
    def rationalize (self) :
        """ If this point instance is of the form P(W*x, W*y, W*z, W) (ie. is in homogenous or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(x, y, z, W).
            This will only work correctly if the point is in homogenous or cartesian form.
            If the point is already in rational form, the results are not defined. """
        self.apicls.rationalize(self)
    def homogenize (self) :
        """ If this point instance is of the form P(x, y, z, W) (ie. is in rational or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(W*x, W*y, W*z, W). """
        self.apicls.homogenize(self)
    def isEquivalent(self, other, tol=_api.MPoint_kTol):
        """ Returns true if both arguments considered as MPoint are equal within the specified tolerance """
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MPoint) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(MPoint, nself).isEquivalent(nother, tol))           
   
    # TODO
    def planar(self, *args, **kwargs): 
        """ p.planar(q, r, s (...), tol=tolerance) returns True if all provided points are planar within given tolerance """
        # tol = kwargs.get('tol', _api.MPoint_kTol)
        pass
    def center(self, *args): 
        """ p.center(q, r, s (...)) returns the MPoint that is the barycenter of p, q, r, s (...) """
        pass
    def bWeights(self, *args): 
        """ p.barycenter(p0, p1, (...), pn) returns barycentric weights so that  """
        pass                
    
class MColor(MPoint):
    apicls = _api.MColor
    cnames = ('r', 'g', 'b', 'a')
    shape = (4,)
    
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
        return colorsys.rgb_to_hsv(clamp(c[0]), clamp(c[1]), clamp(c[2]))
    @staticmethod
    def hsvtorgb(c):
        return colorsys.hsv_to_rgb(clamp(c[0]), clamp(c[1]), clamp(c[2]))
    @classmethod
    def modes(cls):
        return ('rgb', 'hsv', 'cmy', 'cmyk')
    
    @property
    def rgb(self):
        """ returns the tuple of the r, g, b MColor components """
        return tuple(self[:3])
    @property
    def hsv(self):
        """ returns the tuple of the h, s, v MColor components """
        return self.__class__.rgbtohsv(self[:3])
    @property
    def h(self):
        """ returns the tuple of the h, s, v MColor components """
        return self.__class__.rgbtohsv(self[:3])[0]
    @property
    def s(self):
        """ returns the tuple of the h, s, v MColor components """
        return self.__class__.rgbtohsv(self[:3])[1]
    @property
    def v(self):
        """ returns the tuple of the h, s, v MColor components """
        return self.__class__.rgbtohsv(self[:3])[2]
                            
    def __init__(self, *args, **kwargs):
        """ Init a MColor instance
            Can pass one argument being another MColor instance , or the color components """
         
        mode = kwargs.get('mode', None)
        # can also use the form <componentname>=<number>
        # for now supports only rgb and hsv flags
        hsvflag = (kwargs.get('h', None), kwargs.get('s', None), kwargs.get('v', None))
        rgbflag = (kwargs.get('r', None), kwargs.get('g', None), kwargs.get('b', None))
        noflag = (None, None, None)
        # can't mix them
        if hsvflag != noflag and rgbflag != noflag :
            raise ValueError, "Can not mix r,g,b and h,s,v keyword arguments in %s" % util.clsname(self)
        # if no mode specified, guess from what keyword arguments where used, else use 'rgb' as default
        if mode is None :
            if hsvflag != noflag :
                mode = 'hsv'
            else :
                mode = 'rgb'
        # can't specify a mode and use keywords of other modes
        if mode is not 'hsv' and hsvflag != noflag:
            raise ValueError, "Can not use h,s,v keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        elif mode is not 'rgb' and rgbflag != noflag:
            raise ValueError, "Can not use r,g,b keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        # mode int used by api class        
        try :
            modeInt = list(self.__class__.modes()).index(mode)
        except :
            raise KeyError, "%s has no mode %s" % (util.clsname(self), m)
        # NOTE: do not try to use mode with _api.MColor, it seems bugged as of 2008
            #import colorsys
            #colorsys.rgb_to_hsv(0.0, 0.0, 1.0)
            ## Result: (0.66666666666666663, 1.0, 1.0) # 
            #c = _api.MColor(_api.MColor.kHSV, 0.66666666666666663, 1.0, 1.0)
            #print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 0.666666686535 1.0 1.0  #
            #c = _api.MColor(_api.MColor.kHSV, 0.66666666666666663*360, 1.0, 1.0)
            #print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 240.0 1.0 1.0  #
            #colorsys.hsv_to_rgb(0.66666666666666663, 1.0, 1.0)
            ## Result: (0.0, 0.0, 1.0) #  
        # we'll use MColor only to store RGB values internally and do the conversion a read/write if desired
        # which I think make more sense anyway       
        # quantize (255, 65535, no quantize means colors are 0.0-1.0 float values)
        quantize = kwargs.get('quantize', None)
        if quantize is not None :
            try :
                quantize = float(quantize)
            except :
                raise ValueError, "quantize must be a numeric value, not %s" % (util.clsname(quantize))   
        # removed all catching to get direct api errors until api MColor has evolved a bit more
        if args :
            nbargs = len(args)
            # TODO : differentiate between MColor(1) that takes 1 for alpha (so is api) and MColor([1]) ?
            if nbargs==1 :
                # single argument
                if isinstance(args[0], MVector) :
                    # copy constructor
                    self.data = args[0].color
                elif hasattr(args[0],'__iter__') :
                    # iterable, try to init on elements, will catch MVector and MPoint as well
                    self.__init__(*args[0], **kwargs)
                elif util.isScalar(args[0]) :
                    c = float(args[0])
                    if quantize :
                        c /= quantize
                    self.data = self.apicls(c)
                else :
                    # else see if we can init the api class directly (an _api.MColor or single alpha value)
                    self.fromAPI(args[0])
                                               
            else :
                # a list of components
                l = list(self.__class__())
                for i in xrange(min(nbargs, len(l))) :
                    c = args[i]
                    l[i] = float(args[i])                                          
                    if quantize :
                        l[i] /= quantize
                if mode is not 'rgb' :
                    l = list(self.__class__.hsvtorgb(l[:3]))+l[3:len(l)]
                try :
                    # self._data = self.api(modeInt, *l)
                    self.data = self.apicls(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                    raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (util.clsname(self), msg, util.clsname(self))

            
        if self.data is not None :             
            # override values with whatever h,s,v or r,g,b flags where used
            if mode is 'rgb' and rgbflag != noflag :
                l = list(self.rgb)
                for i in range(len(l)) :
                    c = rgbflag[i]
                    if c is not None :                                      
                        l[i] = float(c)                                          
                        if quantize :
                            l[i] /= quantize
                l.append(self.a)                   
                override = True
            elif mode is 'hsv' and hsvflag != noflag :
                l = list(self.hsv)
                for i in range(len(l)) :
                    c = hsvflag[i]
                    if c is not None :                                      
                        l[i] = float(c)                                          
                        if quantize :
                            l[i] /= quantize
                l = list(self.__class__.hsvtorgb(l))
                l.append(self.a)                   
                override = True
            else :
                override = False
            if override :
                try :
                    # self._data = self.api(modeInt, *l)
                    self.data = self.apicls(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))
            
    # overriden operators
    # action depends on second object type
    # TODO : would be nice to define LUT classes and allow MColor * LUT transform
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to element wise multiplication product when both objects are MColor,
            to the transformation of u by matrix v when v is an instance of MMatrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, MVector) :
            # element wise mult in case of Colors
            return self.__class__(map(lambda x,y:x*y, self, MColor(other)))
        elif isinstance(other, MMatrix) :
            # MMatrix transformation, do we need that ?
            return self.__class__(self.data.__mul__(other.matrix))
        elif util.isScalar(other) :
            # multiply all components by a scalar
            return self.__class__(map(lambda x: x*other, self))
        elif util.isSequence(other) :
            # element wise multiplication by a list or tuple
            lm = min(len(other), len(self))
            l = map(lambda x, y: x*y, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        else :
            raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            This is equivalent to u*v thus u.__mul__(v) unless v is a MMatrix, in that case this operation
            is not defined """ 
        # not possible with a MMatrix
        if isinstance(other, MVector) or util.isScalar(other) or util.isSequence(other) : 
            # in these cases it's commutative         
            return self.__mul__(other)
        elif isinstance (other, MMatrix) :
            # left side MMatrix
            try :
                m = MMatrix(other)
            except :
                return self.__mul__(other)
        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Assgin to u the result of u.__mul__(v), see MColor.__mul__ """
        self._data = self.__mul__(other).data
             
    # additionnal methods, to be extended
    def over(self, other):
        """ c1.over(c2): Composites c1 over other c2 using c1's alpha, the resulting color has the alpha of c2 """
        if isinstance(other, MVector) :
            return self.__class__(MVector(self)*self.a + MColor(other))               
        else :
            raise TypeError, "%s is not convertible to a MColor, check help(%s)" % (util.clsname(other), util.clsname(self))
    # return MVector instead ? Keeping alpha doesn't make much sense
    def premult(self):
        """ Premultiply MColor r, g and b by it's alpha and resets alpha to 1.0 """
        return self.__class__(MVector(self)*self.a)               
    def blend(self, other, blend):
        """ c1.blend(c2, b) blends from color c1 to c2 according to
            either a scalar b where it yields c1*(1-b) + c2*b color,
            or a an iterable of up to 4 (r, g, b, a) independant blend factors """ 
        if isinstance(other, MVector) :
            # len(other) <= len(self)            
            if util.isScalar(blend) :
                lm = len(other)
                l = map(lambda x,y:(1-blend)*x+blend*y, self[:lm], other) + self[lm:len(self)]
                return self.__class__(*l)            
            elif hasattr(blend, '__iter__') : 
                bl = list(blend)
                lm = min(len(bl), len(self), len(other))
                l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
                return self.__class__(*l)

            else :
                raise TypeError, "blend can only be a MVector or a scalar, not a %s" % util.clsname(blend)
        else :
            raise TypeError, "%s is not convertible to a MColor, check help(%s)" % (util.clsname(other), util.clsname(self))            
    def gamma(self, gamma):
        """ c.gamma(g) applies gamma correction g to MColor c, g can be a scalar and then will be applied to r, g, b
            or an iterable of up to 4 (r, g, b, a) independant gamma correction values """             
        if hasattr(gamma, '__iter__') : 
            gamma = list(gamma)
            lm = min(len(gamma), len(self))
            l = map(lambda x,y:x**(1/y), self[:lm], gamma[:lm]) + self[lm:len(self)]
            return self.__class__(*l)
        elif util.isScalar(gamma) :
            l = map(lambda x:x**(1/gamma), self[:MVector.apiSize]) + self[MVector.apiSize:len(self)]
            return self.__class__(*l)
        else :
            raise TypeError, "gamma can only be a MVector or a scalar, not a %s" % util.clsname(gamma)
  
# For row, column order, see the definition of a MTransformationMatrix in docs :
# T  = |  1    0    0    0 |
#      |  0    1    0    0 |
#      |  0    0    1    0 |
#      |  tx   ty   tz   1 |
# and m(r, c) should return value of cell at r row and c column :
# t = _api.MTransformationMatrix()
# t.setTranslation(_api.MVector(1, 2, 3), _api.MSpace.kWorld)
# m = t.asMatrix()
# mm(3,0)
# 1.0
# mm(3,1)
# 2.0
# mm(3,2)
# 3.0  

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

class MMatrix(Matrix):
    """ A 4x4 transformation matrix based on api MMatrix 
        >>> v = self.__class__(1, 2, 3)
        >>> w = self.__class__(x=1, z=2)
        >>> z = self.__class__(_api.Mself.__class__.xAxis, z=1)
        """    
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MMatrix
    shape = (4, 4)
    cnames = ('a00', 'a01', 'a02', 'a03',
               'a10', 'a11', 'a12', 'a13',
               'a20', 'a21', 'a22', 'a23',
               'a30', 'a31', 'a32', 'a33' ) 

    # class methods
    
    # properties
    
    @property
    def matrix(self):
        return self._data
    @property
    def tmatrix(self):
        return _api.MTransformationMatrix(self._data)   
    @property
    def quaternion(self):
        return self.tranform.rotation()
    @property
    def euler(self):
        return self.tranform.eulerRotation() 

    def __init__(self, *args, **kwargs):
        """ Init a MMatrix instance
            Can pass one argument being another MMatrix instance , or the MMatrix components """
        self._data = None
        if args :
            nbargs = len(args)
            if nbargs==1 and not util.isScalar(args[0]):
                # single argument
                if type(args[0]) == type(self) :
                    # copy constructor
                    self.data = args[0].data                
                elif isinstance(args[0], self.__class__) :
                    # derived class, copy and convert to self data
                    self.data = args[0].matrix
                elif not hasattr(args[0],'__iter__') :
                    # else see if we can init the api class directly
                    try :
                        self.data = args[0]
                    except :
                        raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (util.clsname(self), util.clsname(args[0]), util.clsname(self))
            # none of the above
            if self._data is None :
                # We can init a matrix from 3 Vectors (base matrix)
                # a nested list (list of lines, lines being lists of scalar)
                # or a flat list of up to 16 components
                if nbargs == 1 and hasattr(args[0],'__iter__') :
                    pass
                elif nbargs == 3 :
                    pass
                elif nbargs == 4 :
                    pass
                else :
                    # up to 16 flat components
                    if nbargs == self.size :
                        l = args
                    else :
                        l = list(self.__class__())
                        for i in xrange(min(nbargs, len(l))) :
                            l[i] = args[i]
                    self._data = self.__class__()
                    if _api.MScriptUtil.createMatrixFromList ( l, self._data ) :
                        pass
                    else :
                        msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                        raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (util.clsname(self), util.clsname(self))

        else :
            # default init
            try :
                self._data = self.apicls()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (util.clsname(self), util.clsname(self))
               

        if self._data is not None :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)                    # current        
            for i in xrange(self.size) :
                l[i] = kwargs.get(self.__class__.cnames[i], l[i])
            if _api.MScriptUtil.createMatrixFromList ( l, self._data ) :
                pass
            else :
                msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))
            
    # base methods derived from Matrix         

    # wrap of list-like access methods
    def __len__(self):
        """ MMatrix class has a fixed length """
        return self.size
    def get(self):
        """ Wrap the MMatrix api get method """
        ptr = self.matrix.matrix[4][4]
        return tuple(tuple(_api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(self.__class__.shape[1])) for r in xrange(self.__class__.shape[0]))
        
    @property
    def row(self):
        """ Iterator on the MMatrix rows """
        return self.axisiter(0)
        # return [[_api.MScriptUtil.getDoubleArrayItem(self.matrix[r], c) for c in xrange(self.__class__.shape[1])] for r in xrange(self.__class__.shape[0])]        
    @property
    def column(self):
        """ Iterator on the MMatrix columns """
        return self.axisiter(1)
        #return [[self.matrix(r, c) for r in xrange(self.__class__.shape[0])] for c in range(self.__class__.shape[1])]
#    @property
#    def flat(self):
#        """ Flat iterator on all matrix components in row by row consecutive order """
#        return MatrixIter(self, 0)
    
    # behavior made to be close to Numpy or cgkit
    # use flat instead for a single index access to the 16 components
    def __getitem__(self, rc):
        """ Get value from either a (row,column) tuple or a single component index (get a full row) """
        if util.isScalar (rc) :
            r = rc
            c = slice(None, None, None)
        else :
            r,c = rc
        # bounds check
        if util.isScalar(r) and util.isScalar(c) :
            # single element
            if r in range(self.__class__.shape[0]) and c in range(self.__class__.shape[1]) :
                return self.matrix(r, c)
            else :
                raise IndexError, "%s has no element of index [%s,%s]" % (self.__class__.__name__, r, c)
        elif util.isScalar(c) :
            # numpy like m[:,2] format, we return (possibly partial) columns
            if c in range(self.__class__.shape[1]) :
                return tuple([self.matrix(i, c) for i in xrange(self.__class__.shape[0])][r])
            else :
                raise IndexError, "There are only %s columns in class %s" % (self.__class__.shape[1], self.__class__.__name__)
        elif util.isScalar(r) :
            # numpy like m[2,:] format, we return (possibly partial) columns
            if r in range(self.__class__.shape[0]) :
                ptr = self.matrix[r]
                return tuple([_api.MScriptUtil.getDoubleArrayItem(ptr, j) for j in xrange(self.__class__.shape[1])][c])
            else :
                raise IndexError, "There are only %s rows in class %s" % (self.__class__.shape[0], self.__class__.__name__)
        else :
            # numpy like m[:,:] format, we return (possibly partial) rows
            return tuple(row[c] for row in self.row[r])

    def __setitem__(self, rc, value):
        """ Set value at either a (row,column) tuple or a single component index (set a full row) """
        if util.isScalar (rc) :
            r = rc
            c = slice(None, None, None)
        else :
            r,c = rc
        # bounds check
        if util.isScalar(r) and util.isScalar(c) :
            # set a single element
            if r in range(self.__class__.shape[0]) and c in range(self.__class__.shape[1]) :
                ptr = self.matrix[r]
                _api.MScriptUtil.setDoubleArray(ptr, c, value)
            else :
                raise IndexError, "%s has no element of index [%s,%s]" % (self.__class__.__name__, r, c)
        elif util.isScalar(c) :
            # numpy like m[:,2] format, we set (possibly partial) columns
            if c in range(self.__class__.shape[1]) :
                l = list(self.flat)
                if util.isScalar(value) :
                    for i in range(self.__class__.shape[0])[r] :
                        l[i*self.__class__.shape[0] + c] = value 
                elif hasattr(value, '__getitem__') :
                    for v, i in enumerate(range(self.__class__.shape[0])[r]) :
                        # to allow to assign 3 value vectors to rows or columns, 4th cell is left unchanged
                        try :
                            l[i*self.__class__.shape[0] + c] = value[v] 
                        except IndexError :
                            pass
                else :
                    raise TypeError, "You can only assign a single scalar value or a sequence/iterable to a %s column" % self.__class__.__name__                                          
                _api.MScriptUtil.createMatrixFromList ( l, self._data )                 
            else :
                raise IndexError, "There are only %s columns in class %s" % (self.__class__.shape[1], self.__class__.__name__)
        elif util.isScalar(r) :
            # numpy like m[2,:] format, we set (possibly partial) columns
            if r in range(self.__class__.shape[0]) :
                ptr = self.matrix[r]
                if util.isScalar(value) :
                    for j in range(self.__class__.shape[1])[c] :
                        _api.MScriptUtil.setDoubleArray(ptr, j, value)
                elif hasattr(value, '__getitem__') :
                    for v, j in enumerate(range(self.__class__.shape[1])[c]) :
                        # to allow to assign 3 value vectors to rows or columns, 4th cell is left unchanged
                        try :
                            _api.MScriptUtil.setDoubleArray(ptr, j, value[v]) 
                        except IndexError :
                            pass
                else :
                    raise TypeError, "You can only assign a single scalar value or a sequence/iterable to a %s row" % self.__class__.__name__                                                                                                                   
            else :
                raise IndexError, "There are only %s rows in class %s" % (self.__class__.shape[0], self.__class__.__name__)
        else :
            # numpy like m[:,:] format, we set a sub matrix
            if util.isScalar(value) :
                for i in range(self.__class__.shape[0])[r] :
                    self[i,c] = value            
            else :
                for v, i in enumerate(range(self.__class__.shape[0])[r]) :
                    self[i,c] = value[v]

    def __iter__(self):
        """ Default MMatrix iterators iterates on rows """
        for r in xrange(self.__class__.shape[0]) :
            ptr = self.matrix[r]
            yield tuple(_api.MScriptUtil.getDoubleArrayItem(ptr, c) for c in xrange(self.__class__.shape[1]))         
    def __contains__(self, value):
        """ True if at least one of the MMatrix components is equal to the argument,
            can test for the presence of a complete row if argument is a row sequence """
        if util.isScalar(value) :
            return value in self.flat
        else :
            return value in self.row
        # TODO : check for submatrix [[a, b], [c, d]] like inclusion ?

    # convenience row and column get and set       
    def getrow(self, r):
        """ helper to get a row at once """
        return self[r,:]        
    def setrow(self, r, value):
        """ helper to set a row at once """     
        self[r,:] = value      
    def getcolumn(self, c):
        """ helper to get a column at once """
        return self[:,c]                       
    def setcolumn(self, c, value):
        """ helper to set a column at once """    
        self[:,c] = value

    # operators

    def __neg__(self):
        """ m.__neg__() <==> -m
            Returns the result obtained by negating every component of m """        
        return self.__class__(imap(operator.neg, self.flat))   
    def __invert__(self):
        """ m.__invert__() <==> ~m <==> m.inverse()
            unary inversion, returns the inverse of self """        
        return self.__class__(self.matrix.inverse())  
    def __add__(self, other):
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to MMatrix,
            adds v to every component of u if v is a scalar """             
        if instance(other, MMatrix) :
            return self.__class__(self.matrix + other.matrix)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(self), util.clsname(other))          
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to MVector,
            adds v to every component of u if v is a scalar """        
        if instance(other, MMatrix) :
            return self.__class__(other.matrix + self.matrix)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(other), util.clsname(self))         
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        self = self.__add__(other)
    def __sub__(self,other):
        if instance(other, MMatrix) :
            return self.__class__(self.matrix - other.matrix)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))  
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (util.clsname(self), util.clsname(other)) 
                
  

    def __mul__(self, other):
        if isinstance(other, self.__class__) :
            return self.__class__(self.matrix * other.matrix)
        elif isinstance(other, MMatrix) :
            return MMatrix(self.matrix * other.matrix)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x*other, self))             
        elif isinstance(other, Vector3):
            # pre multiply a row by a MMatrix
            pass
        else :            
            raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(self), util.clsname(other)) 

    def __imul__(self,other):
        self = self.__mul__(other)
#    def __div__(self, other):
#        """ u.__div__(v) <==> u/v
#            Returns the result of the element wise division of each component of u by the
#            corresponding component of v if both are convertible to MVector,
#            divide every component of u by v if v is a scalar """  
#        if isinstance(other, MVector) :
#            return self.__class__(map( lambda x, y: x/y, self, other))
#        elif util.isScalar(other) :
#            return self.__class__(self.__class__._api.__div__(self._data,other))
#        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(self), util.clsname(other))  
#    def __rdiv__(self, other):
#        """ u.__rdiv__(v) <==> v/u
#            Returns the result of the element wise division of each component of v by the
#            corresponding component of u if both are convertible to MVector,
#            invert every component of u and multiply it by v if v is a scalar """
#        if isinstance(other, MVector) :
#            return other.__class__(map( lambda x, y: x/y, self, other))
#        elif util.isScalar(other) :
#            return self.__class__(map( lambda y: other/y, self))
#        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
#    def __idiv__(self, other):
#        """ u.__idiv__(v) <==> u /= v
#            In place division of u by v, see __div__ """        
#        self._data = (self.__div__(other))._data
#    def __eq__(self, other):
#        """ u.__eq__(v) <==> u == v """
#        if isinstance(other, self.__class__) :
#            try :
#                if self.__class__(self.__class__._api.__eq__(self._data, self.__class__(other)._data)) :
#                    return True
#            except :
#                pass
#        else :
#            try :
#                return self.__eq__(self.__class__(other))
#            except :
#                pass
#        return False 
    def __eq__(self,other):
        if isinstance(other, MMatrix) :
            return self.matrix == other.matrix
#        elif isinstance(other, MMatrix) :
#            return self.flat == other.flat
        else :
            return false
 
    # API methods
    
    def get(self):
        pass
    def setToIdentity (self) :
        self = self.__class__()      
    def setToProduct ( self, left, right ) :
        self = self.__class__(left * right)
    def transpose(self):
        """ Returns the transposed MMatrix """
        return self.__class__(self.matrix.transpose())
    def inverse(self):
        """ Returns the inverse MMatrix """
        return self.__class__(self.matrix.inverse())
    def adjoint(self):
        """ Returns the adjoint (conjugate transpose, Hermitian transpose) MMatrix """
        return self.__class__(self.matrix.adjoint())
    def homogenize(self):
        """ Returns a homogenized version of the MMatrix """
        return self.__class__(self.matrix.homogenize())
    def det4x4(self):
        """ Returns the 4x4 determinant of this MMatrix instance """
        return self.matrix.det4x4()  
    det = det4x4
    def det3x3(self):
        """ Returns the determinant of the upper left 3x3 submatrix of this MMatrix instance,
            it's the same as doing det(m[0:3, 0:3]) """
        return self.matrix.det3x3()       
    def isEquivalent (self, other, tol = _api.MMatrix_kTol) :
        """ Returns true if both arguments considered as MMatrix are equal  within the specified tolerance """
        try :
            return bool(self.matrix.isEquivalent(MMatrix(other).matrix, tol))
        except :
            raise TypeError, "%s is not convertible to a MMatrix, or tolerance %s is not convertible to a number, check help(MMatrix)" % (other, tol)     
    def isSingular(self) : 
        """ Returns True if the given MMatrix is singular """
        return bool(self.matrix.isSingular()) 
 
    # additionnal methods
 
    def base(self) :
        """ Returns the x, y, z base as transformed by this MMatrix """
        u = MVector.xAxis * self
        v = MVector.yAxis * self
        n = MVector.zAxis * self
        return u, v, n    
    def blend(self, other=None, blend=0.5):
        """ Returns a 0.0-1.0 scalar weight blend between self and other MMatrix """
        if other is None :
            other = self.__class__()
        if isinstance(other, MMatrix) :
            # len(other) <= len(self)            
            if util.isScalar(blend) :
                w = float(blend)
                return self.__class__(self.matrix*(1.0-w)+other.matrix*w) 
            else :
                raise TypeError, "blend can only be a scalar blend weight, not a %s" % util.clsname(blend)
        else :
            raise TypeError, "%s is not convertible to a MMatrix, check help(%s)" % (util.clsname(other), util.clsname(self))     
    def weighted(self, value):
        """ Returns a 0.0-1.0 scalar weighted blend between identity and self """
        if util.isScalar(value) :
            return self.__class__.identity.blend(self, value)
        else :
            raise TypeError, "weighted weight value can only be a scalar blend weight, not a %s" % util.clsname(blend)
   
        
class MQuaternion(MMatrix):
    apicls = _api.MQuaternion
    shape = (4,)
    cnames = ('x', 'y', 'z', 'w')      

    @property
    def matrix(self):
        return self._data.asMatrix()
    @property
    def tmatrix(self):
        return _api.MTransformationMatrix(self.matrix)   
    @property
    def quaternion(self):
        return self._data
    @property
    def euler(self):
        return self._data.asEulerRotation()

    def __str__(self):
        return '(%s)' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'(%s)' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))  

    # wrap of list-like access methods
    def __len__(self):
        """ MVector class is a one dimensional array of a fixed length """
        return self.size
    # API get, actually not faster than pulling _data[i] for such a short structure
#    def get(self):
#        ms = _api.MScriptUtil()
#        ms.createFromDouble ( 0.0, 0.0, 0.0 )
#        p = ms.asDoublePtr ()
#        self._data.get(p)
#        result = [ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)]   
    def __getitem__(self, i):
        """ Get component i value from self """
        if i < 0 :
            i = self.size + i
        if i<self.size and not i<0 :
            return self._data[i]
        else :
            raise KeyError, "%r has no item %s" % (self, i)
    def __setitem__(self, i, a):
        """ Set component i value on self """
        l = list(self)
        l[i] = a
        self._data = self.apicls(*l)
    def __iter__(self):
        """ Iterate on the api components """
        for i in xrange(self.size) :
            yield self._data[i]
    
    def __init__(self, *args) : 
        self._data = self.apicls()

class MEulerRotation(MQuaternion):
    apicls = _api.MEulerRotation
    shape = (4,)   
    cnames = ('x', 'y', 'z', 'o')   
    
    @property
    def matrix(self):
        return self._data.asMatrix()
    @property
    def tmatrix(self):
        return _api.MTransformationMatrix(self.matrix)   
    @property
    def quaternion(self):
        return self._data.asQuaternion()
    @property
    def euler(self):
        return self._data

    def __str__(self):
        return '(%s)' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'(%s)' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))  

#_factories.ApiTypeRegister.register( 'MVector', MVector )
#_factories.ApiTypeRegister.register( 'MMatrix', MMatrix )
#_factories.ApiTypeRegister.register( 'MPoint', MPoint )
#_factories.ApiTypeRegister.register( 'MColor', MColor )
#_factories.ApiTypeRegister.register( 'MQuaternion', MQuaternion )
#_factories.ApiTypeRegister.register( 'MEulerRotation', MEulerRotation )

class MSpace(_api.MSpace):
    apicls = _api.MSpace
    __metaclass__ = _factories.MetaMayaTypeWrapper
    pass

class MTime( _api.MTime ) :
    apicls = _api.MTime
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __str__( self ): return str(float(self))
    def __int__( self ): return int(float(self))
    def __float__( self ): return self.as(self.apicls.uiUnit())
    def __repr__(self): return '%s(%s)' % ( self.__class__.__name__, float(self) )

def _testMVector() :
    
    print "MVector class:", dir(MVector)
    u = MVector()
    print u
    print "MVector instance:", dir(u)
    print repr(u)
    print MVector.__readonly__
    print MVector.__slots__
    print MVector.shape
    print MVector.ndim
    print MVector.size
    print u.shape
    print u.ndim
    print u.size    
    # should fail
    u.shape = 2
    
    u = MVector(1, 2, 3)
    print repr(u)
    print len(u)
    # inherits from Vector --> Array
    print isinstance(u, Vector)
    print isinstance(u, Array)
    # as well as _api.MVector
    print isinstance(u, _api.MVector)
    # accepted directly by API methods
    M = _api.MTransformationMatrix()
    M.setTranslation ( u, _api.MSpace.kWorld )
    # need conversion on the way back though
    u = MVector(M.getTranslation ( _api.MSpace.kWorld ))
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    
    u = MVector(x=1, y=2, z=3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector([1, 2], z=3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector(_api.MPoint(1, 2, 3))
    print repr(u)  
    # MVector([1.0, 2.0, 3.0])
    print "u = MVector(Vector(1, 2, 3))"
    u = MVector(Vector(1, 2, 3))
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector(1)
    print repr(u)   
    # MVector([1.0, 1.0, 1.0])  
    u = MVector(1,2)
    print repr(u)    
    # MVector([1.0, 2.0, 0.0])              
    u = MVector(Vector(1, shape=(2,)))
    print repr(u)  
    # MVector([1.0, 1.0, 0.0])  
    u = MVector(MPoint(1, 2, 3))
    print repr(u) 
    #
    u = MVector(MPoint(1, 2, 3, 1), y=20, z=30)
    print repr(u) 
    #                            
    # should fail
    print "MVector(Vector(1, 2, 3, 4))"
    try :     
        u = MVector(Vector(1, 2, 3, 4))
    except :
        print "will raise ValueError: could not cast [1, 2, 3, 4] to MVector of size 3, some data would be lost"
           
    
            
    print u.get()
    print u[0]
    u[0] = 10
    print u
    print (10 in u)
    print list(u)
    
    u = MVector.xAxis
    v = MVector.yAxis
    print MVector.xAxis
    print str(MVector.xAxis)
    print unicode(MVector.xAxis)
    print repr(MVector.xAxis)
    print u
    print str(u)
    print unicode(u)
    print repr(u)
    print "u = MVector.xAxis:"
    print repr(u)
    # MVector([01 0.0, 0.0])
    print "v = MVector.yAxis:"
    print repr(v)
    # MVector([0.0, 1.0, 0.0])
    n = u ^ v
    print "n = u ^ v:"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])
    print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    # n.x=0.0, n.y=0.0, n.z=1.0
    n = u ^ Vector(v)
    print "n = u ^ Vector(v):"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])
    n = u ^ [0, 1, 0]
    print "n = u ^ [0, 1, 0]:"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])       
    n[0:2] = [1, 1]
    print "n[0:2] = [1, 1]:"
    print repr(n)
    # MVector([1.0, 1.0, 1.0]) 
    print "n = n * 2 :"
    n = n*2
    print repr(n)
    # MVector([2.0, 2.0, 2.0])
    print "n = n * [0.5, 1.0, 2.0]:"
    n = n*[0.5, 1.0, 2.0]    
    print repr(n) 
    # MVector([1.0, 2.0, 4.0])  
    print "n * n :"
    print n * n
    # 21.0
    print repr(n.clamp(1.0, 2.0))
    # MVector([1.0, 2.0, 2.0])
    print repr(-n)
    # MVector([-1.0, -2.0, -4.0])
    w = u + v
    print repr(w)
    # MVector([1.0, 1.0, 0.0])
    p = MPoint(1, 2, 3)
    q = u + p
    print repr(q)
    # MPoint([2.0, 2.0, 3.0, 1.0])
    print repr(p+q)
    # MPoint([3.0, 4.0, 6.0, 1.0])    
    w = u + Vector(1, 2, 3, 4)
    print repr(w)
    # Vector([2.0, 2.0, 3.0, 4])
    print repr(u+2)
    # MVector([3.0, 2.0, 2.0])
    print repr(2+u)
    # MVector([3.0, 2.0, 2.0])
    print repr(p+2)
    # MPoint([3.0, 4.0, 5.0, 3.0])
    print repr(2+p)
    # MPoint([3.0, 4.0, 5.0, 3.0])
    print repr(p + u)
    # MPoint([2.0, 2.0, 3.0, 1.0])
    print repr(Vector(1, 2, 3, 4) + u)
    # Vector([2.0, 2.0, 3.0, 4])
    print repr([1, 2, 3] + u)
    # MVector([2.0, 2.0, 3.0])
    print repr([1, 2, 3] + p)
    # MPoint([2.0, 4.0, 6.0, 1.0])
      
    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    print u.length()
    # 3.74165738677
    print length(u)
    # 3.74165738677
    print length([1, 2, 3])
    # 3.74165738677
    print length(Vector(1, 2, 3))
    # 3.74165738677
    print Vector(1, 2, 3).length()
    # 3.74165738677
    print length(Vector(1, 2, 3, 4))
    # 5.47722557505
    print Vector(1, 2, 3, 4).length() 
    # 5.47722557505
    print length(1)
    # 1.0
    print length([1, 2])
    
    print length([1, 2, 3])
    
    print length([1, 2, 3, 4])
    
    print length([1, 2, 3, 4], 0)
    
    print length([1, 2, 3, 4], (0,))
    
    print length([[1, 2], [3, 4]], 1)
    
    try :
        print length([1, 2, 3, 4], 1)
    except :
        pass
    
    print u.sqlength()
    # 21
    print repr(u.normal())
    # MVector([0.218217890236, 0.436435780472, 0.872871560944])
    u.normalize()
    print repr(u)
    # MVector([0.218217890236, 0.436435780472, 0.872871560944])
    
    w = u + [0.01, 0.01, 0.01]
    print repr(w)
    # MVector([1.01, 0.01, 0.01])
    print (u == u)
    # True
    print (u == w)
    # False
    print (u == [1.0, 0.0, 0.0])
    # True
    print (u == MVector(1.0, 0.0, 0.0))
    # True
    print (u == MPoint(1.0, 0.0, 0.0))
    # False
    print u.isEquivalent([1.0, 0.0, 0.0])
    # True
    print u.isEquivalent(MVector(1.0, 0.0, 0.0))
    
    print u.isEquivalent(MPoint(1.0, 0.0, 0.0))   

    print u.isEquivalent(w)
    # False     
    print u.isEquivalent(w, 0.1)
    # True
    print axis(u, v)
    
    print angle(u,v)    
    
    print cotan(u, v)
    
    print u.rotateTo(v)
    
    print u.distanceTo(v)
    
    print u.isParallel(v)
    
    print u.isParallel(2*u)
    
    print u.basis(v)
    
    print u.blend(v)
  
    # print MMatrix(2, shape=(3,))
    
    print "end tests MVector"

def _testMPoint() :
    
    print "MPoint class", dir(MPoint)
    p = MPoint()
    print repr(p)
    # MPoint([0.0, 0.0, 0.0, 1.0])
    print "MPoint instance", dir(p)
    p = MPoint(_api.MPoint())
    print repr(p) 
    # MPoint([0.0, 0.0, 0.0, 1.0])
    p = MPoint(1)
    print repr(p)
    # MPoint([1.0, 1.0, 1.0, 1.0])
    p = MPoint(1, 2)
    print repr(p)     
    # MPoint([1.0, 2.0, 0.0, 1.0])      
    p = MPoint(1, 2, 3)
    print repr(p)
    # MPoint([1.0, 2.0, 3.0, 1.0])
    p = MPoint(_api.MPoint(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 1.0])
    p = MPoint(Vector(1, 2))
    print repr(p) 
    # MPoint([1.0, 2.0, 0.0, 1.0])       
    p = MPoint(MVector(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 1.0])      
    p = MPoint(_api.MVector(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 1.0])    
    p = MPoint(Vector(1, 2, 3, 4))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 4.0]) 
    
        
    p = MPoint.origin
    q = MPoint(1, 2, 3)
    print "p = MPoint.origin: %r" % p
    print "q = MPoint(1, 2, 3): %r" % q
    r = MPoint([1, 2, 3], y=0)
    print "r = MPoint([1, 2, 3], y=0): %r" % r
    v = u + p
    print "v = u + p: %r" % v
    r = q + u
    print "r = q + u: %r" % r
    
    p = MPoint(x=1, y=2, z=3)
    print "p = MPoint(x=1, y=2, z=3): %r" % p
    
    try :
        p = MPoint(x=1, y=2, z='a')
    except :
        pass
    
    p = MPoint(x=1, y=2, z=3)
    print "p = MPoint(x=1, y=2, z=3): %r" % p
    
    print "length of p: %s" % p.length()
    
    print "end tests MPoint"
 
def _testMColor() :
    
    print "MColor class", dir(MColor)
    
    c1 = MColor(1, 1, 1)
    print "c1 = MColor(1, 1, 1): %r" % c1
    c2 = MColor(255, 0, 0, quantize=255, mode='rgb')
    print "c2 = MColor(255, 0, 0, quantize=255, mode='rgb'): %r" % c2
    # careful MColor takes a solo argument as an alpha
    c3 = MColor(255, b=128, quantize=255, mode='rgb')
    print "c3 = MColor(255, b=128, quantize=255, mode='rgb'): %r" % c3
    c4 = MColor(1, 0.5, 2, 0.5)
    print "c4 = MColor(1, 0.5, 2, 0.5): %r" % c4
    c5 = MColor(0, 65535, 65535, quantize=65535, mode='hsv')
    print "c5 = MColor(0, 65535, 65535, quantize=65535, mode='hsv'): %r" % c5
    a = MVector(c5.rgb)
    print "a = MVector(c5.rgb): %r" % a    
    b = MVector(c5.hsv)
    print "b = MVector(c5.hsv): %r" % b
    c6 = MColor(b, v=0.5, mode='hsv')
    print "c6 = MColor(b, v=0.5, mode='hsv'): %r" % c6
    c7 = MColor(MColor.blue, v=0.5)
    print "c7 = MColor(MColor.blue, v=0.5) as rgb:", c7.rgb    
    print "c7 = MColor(MColor.blue, v=0.5) as hsv:", c7.hsv 
    print "c4.clamp() : %s" % c4.clamp()
    c7 = MColor(c4, v=0.5)
    print "c7 = MColor(c4, v=0.5) : %r" % c7    
    print "c7 = MColor(c4, v=0.5) as hsv:", c7.hsv    
    c7 = c7.gamma([2.2, 2.0, 2.3])
    print "c7 = c7.gamma([2.2, 2.0, 2.3]): %r" % c7
    c8 = MColor(1, 1, 1) * 0.5
    print "c8 = MColor(1, 1, 1) * 0.5: %r" % c8
    c9 = MColor.red.blend(MColor.blue, 0.5) 
    print "c9 = MColor.red.blend(MColor.blue, 0.5): %r" % c9
    c10 = c8.over(c9)
    print "c10 = c8.over(c9): %r" % c10 

    print "end tests MColor"
    
def _testMMatrix() :

    print "MMatrix class", dir(MMatrix)
    t = _api.MTransformationMatrix()
    t.setTranslation(_api.MVector(1, 2, 3), _api.MSpace.kWorld)
    m = MMatrix(t.asMatrix())
    print "m: %s" % m 
    print "m.row[0]: %s" % m.row[0]
    print "list(m.row): %s" % list(m.row)
    print "m.column[0]: %s" % m.column[0]
    print "list(m.column): %s" % list(m.column)
    print "m.flat[0]: %s" % m.flat[0]
    print "list(m.flat): %s" % list(m.flat) 

    print "end tests MMatrix"

    
if __name__ == '__main__' :
    _testMVector()   
    _testMPoint()
    _testMColor()
    _testMMatrix()


    
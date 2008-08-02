"""
A wrap of Maya's MVector, MPoint, MColor, MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation types
"""

import inspect
import math, copy
import itertools, operator, colorsys
import warnings

import pymel.util as util
import pymel.mayahook as mayahook
import pymel.api as _api
from pymel.util.arrays import *
from pymel.util.arrays import _toCompOrArrayInstance
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
            yield _api.MVector.__getitem__(self, i)
    type.__setattr__(_api.MVector, '__iter__', __iter__)

def _patchMFloatVector() :
    def __len__(self):
        """ Number of components in the Maya api MFloatVector, ie 3 """
        return 3
    type.__setattr__(_api.MFloatVector, '__len__', __len__)
    def __iter__(self):
        """ Iterates on all components of a Maya api MFloatVector """
        for i in xrange(len(self)) :
            yield _api.MFloatVector.__getitem__(self, i)
    type.__setattr__(_api.MFloatVector, '__iter__', __iter__)

def _patchMPoint() :
    def __len__(self):
        """ Number of components in the Maya api MPoint, ie 4 """
        return 4
    type.__setattr__(_api.MPoint, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MPoint """
        for i in xrange(len(self)) :
            yield _api.MPoint.__getitem__(self, i)
    type.__setattr__(_api.MPoint, '__iter__', __iter__)
 
def _patchMFloatPoint() :
    def __len__(self):
        """ Number of components in the Maya api MFloatPoint, ie 4 """
        return 4
    type.__setattr__(_api.MFloatPoint, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MFloatPoint """
        for i in xrange(len(self)) :
            yield _api.MFloatPoint.__getitem__(self, i)
    type.__setattr__(_api.MFloatPoint, '__iter__', __iter__) 
  
def _patchMColor() :
    def __len__(self):
        """ Number of components in the Maya api MColor, ie 4 """
        return 4
    type.__setattr__(_api.MColor, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MColor """
        for i in xrange(len(self)) :
            yield _api.MColor.__getitem__(self, i)
    type.__setattr__(_api.MColor, '__iter__', __iter__)  
    
def _patchMMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MMatrix """
        for r in xrange(4) :
            yield Array([_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MMatrix, '__iter__', __iter__)

def _patchMFloatMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MFloatMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MFloatMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MFloatMatrix """
        for r in xrange(4) :
            yield Array([_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MFloatMatrix, '__iter__', __iter__)

def _patchMTransformationMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MTransformationMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MTransformationMatrix """
        return self.asMatrix().__iter__()
    type.__setattr__(_api.MTransformationMatrix, '__iter__', __iter__)

def _patchMQuaternion() :
    def __len__(self):
        """ Number of components in the Maya api MQuaternion, ie 4 """
        return 4
    type.__setattr__(_api.MQuaternion, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all components of a Maya api MQuaternion """
        for i in xrange(len(self)) :
            yield _api.MQuaternion.__getitem__(self, i)
    type.__setattr__(_api.MQuaternion, '__iter__', __iter__)  

def _patchMEulerRotation() :
    def __len__(self):
        """ Number of components in the Maya api MEulerRotation, ie 4 """
        return 4
    type.__setattr__(_api.MEulerRotation, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all components of a Maya api MEulerRotation """
        for i in xrange(len(self)) :
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
                    args = tuple(args)
                    if len(args) > len(self) :
                        args = args[slice(self.shape[0])]
                super(Vector, self).__init__(*args)
            
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

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
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
          
    data = property(_getdata, _setdata, _deldata, "The MVector/MFloatVector/MPoint/MFloatPoint/MColor data")                           
                          
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                   
                                                 
    def assign(self, value):
        """ Wrap the MVector api assign method """
        # don't accept instances as assign works on exact types
        if type(value) != self.apicls and type(value) != type(self) :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MVector api get method """
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
    
    # faster to override __getitem__ cause we know MVector only has one dimension
    def __getitem__(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__') :
            i = list(i)
            if len(i) == 1 :
                i = i[0]
            else :
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice) :
            return _toCompOrArrayInstance(list(self)[i], Vector)
            try :
                return _toCompOrArrayInstance(list(self)[i], Vector)
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

    # as api.MVector has no __setitem__ method, so need to reassign the whole MVector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
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
    
    # common operators without an api equivalent are herited from Vector
    
    # operators using the Maya API when applicable, but that can delegate to Vector
    
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v
            Equivalence test """
        try :
            return bool(self.apicls.__eq__(self, other))
        except :
            return bool(super(MVector, self).__eq__(other))        
    def __ne__(self, other):
        """ u.__ne__(v) <==> u != v
            Equivalence test """
        return (not self.__eq__(other))      
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
            # return self.__class__._convert(super(MVector, self).__add__(other)) 
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
    # action depends on second object type
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
         
    # wrap of other API MVector methods, we use the api method if possible and delegate to Vector else   
    
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
        return MVector.apicls.length(MVector(self))
    def sqlength(self):
        """ Return the square length of the vector """
        return self.dot(self)          
    def normal(self): 
        """ Return a normalized copy of self """ 
        return self.__class__(MVector.apicls.normal(MVector(self)))
    def normalize(self):
        """ Performs an in place normalization of self """
        if type(self) is MVector :
            MVector.apicls.normalize(self)
        else :
            self.assign(v.normal())
        
    # additional api methods that work on MVector only, and don't have an equivalent on Vector

    def rotateTo(self, other):
        """ u.rotateTo(v) --> MQuaternion
            Returns the MQuaternion that represents the rotation of the MVector u into the MVector v
            around their mutually perpendicular axis. It amounts to rotate u by angle(u, v) around axis(u, v) """
        if isinstance(other, MVector) :
            return MQuaternion(MVector.apicls.rotateTo(MVector(self), MVector(other)))
        else :
            raise TypeError, "%r is not a MVector instance" % other
    def rotateBy(self, *args):
        """ u.rotateBy(*args) --> MVector
            Returns the result of rotating u by the specified arguments.
            There are several ways the rotation can be specified:
            args is a tuple of one MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation
            arg is tuple of 4 arguments, 3 rotation value and an optionnal rotation order
            args is a tuple of one MVector, the axis and one float, the angle to rotate around that axis """
        if args :
            if len(args) == 2 and isinstance(args[0], MVector) :
                return self.__class__(self.apicls.rotateBy(self, MQuaternion(MVector(args[0]), float(args[1]))))
            elif len(args) == 1 and isinstance(args[0], MMatrix) :
                return self.__class__(self.apicls.rotateBy(self, args[0].rotate))         
            else :
                return self.__class__(self.apicls.rotateBy(self, MEulerRotation(*args)))
        else :
            return self
    
    # additional api methods that work on MVector only, but can also be delegated to Vector
      
    def transformAsNormal(self, other):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, MMatrix) :
            return self.__class__._convert(MVector.apicls.transformAsNormal(MVector(self), MMatrix(other)))
        else :
            return self.__class__._convert(super(MVector, self).transformAsNormal(other))
    def dot(self, other):
        """ dot product of two vectors """
        if isinstance(other, MVector) :
            return MVector.apicls.__mul__(MVector(self), MVector(other))
        else :
            return super(MVector, self).dot(other)       
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, MVector) :
            return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).cross(other))              
    def axis(self, other, normalize=False):
        """ Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, MVector) :
            if normalize :
                return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)).normal())
            else :
                return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).axis(other, normalize)) 
    def angle(self, other):
        """ angle between two vectors """
        if isinstance(other, MVector) :
            return MVector.apicls.angle(MVector(self), MVector(other))
        else :
            return super(MVector, self).angle(other) 
        
    # methods without an api equivalent    
        
    # cotan on MVectors only takes 2 arguments          
    def cotan(self, other, third=None):
        """ cotan(u, v) --> float :
            cotangent of the a, b angle, a and b should be MVectors"""        
        if third is not None :
            raise NotImplemented, "cotan is only defined for 2 MVectors"
        return Vector.cotan(self, other)
                                   
    # rest derived from Vector class

class MFloatVector(MVector) :
    """ A 3 dimensional vector class that wraps Maya's api MFloatVector class,
        It behaves identically to MVector, but it also derives from api's MFloatVector
        to keep api methods happy
        """
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MFloatVector
               
class MPoint(MVector):
    """ A 4 dimensional vector class that wraps Maya's api MPoint class,
        """    
    apicls = _api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)

#    # base methods are inherited from MVector

               
    # modified operators, when adding 2 MPoint consider second as MVector
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        # prb with coerce when delegating to Vector, either redefine coerce for MPoint or other fix
        # if isinstance(other, MPoint) :
        #    other = MVector(other)   
        try :
             other = MVector(other) 
        except :
            pass   
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(Vector, self).__add__(other)) 
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
    def cotan(self, other, third=None):
        """ cotan(a, b, c) --> float :
            cotangent of the (b-a), (c-a) angle, a, b, and c should be MPoints representing points a, b, c"""        
        if third is None :
            raise NotImplemented, "cotan is only defined for 3 MPoints"
        return Vector.cotan(MVector(self), MVector(other), MVector(third))        
    # TODO
    def planar(self, *args, **kwargs): 
        """ p.planar(q, r, s (...), tol=tolerance) returns True if all provided points are planar within given tolerance """
        # tol = kwargs.get('tol', _api.MPoint_kTol)
        pass
    def center(self, *args): 
        """ p.center(q, r, s (...)) returns the MPoint that is the barycenter of p, q, r, s (...) """
        pass
    def bWeights(self, *args): 
        """ p.barycenter(p0, p1, (...), pn) returns a tuple of (n0, n1, ...) barycentric weights so that
            n0*p0 + n1*p1 + ... = p  """
        pass  
    # need to convert my old C code for bWeights              
    #MStatus weightOnFacePoints (MPoint p, const MPointArray &q, MFloatArray &w)
    #{
    #    MStatus stat;
    #
    #    unsigned int nbPoints = q.length();
    #    w.copy(MFloatArray(nbPoints));
    #
    #    float weightSum = 0.0;
    #    bool isOnEdge = false;
    #
    #    // cas limite sur edge
    #    for (unsigned int i=0; i<nbPoints; i++)
    #    {
    #        unsigned int prev = (i+nbPoints-1)%nbPoints;
    #        unsigned int next = (i+1)%nbPoints;
    #
    #        double e = AM::lengthSquared( (q[next]-q[i]) ^ (p-q[i]) );
    #        double l = AM::lengthSquared( q[next]-q[i] );
    #        if (e <= (kDoubleEpsilon * l) )
    #        {
    #            if (l < kDoubleEpsilon)
    #            {
    #                w[i] = 0.5;
    #                w[next] = 0.5;
    #                weightSum += 1.0;
    #            }
    #            else
    #            {
    #                double di = (p-q[i]).length();
    #                w[next] = float(di / sqrt(l));
    #                w[i] = 1.0f - w[next];
    #                weightSum += 1.0;
    #            }
    #            isOnEdge = true;
    #            break;
    #        }
    #    }
    #
    #    // Pas sur une edge, cotangentes
    #    if (!isOnEdge)
    #        for (unsigned int i=0; i<nbPoints; i++)
    #        {
    #            unsigned int prev = (i+nbPoints-1)%nbPoints;
    #            unsigned int next = (i+1)%nbPoints;
    #
    #            double lenSq = AM::lengthSquared(p - q[i]);
    #            w[i] = float (( AM::cotangent(p,q[i],q[prev]) + AM::cotangent(p,q[i],q[next]) ) / lenSq);
    #            weightSum += w[i];
    #        }
    #
    #    // On normalise
    #    if (fabs(weightSum) > kFloatEpsilon)
    #    {
    #        for (unsigned int i=0; i<nbPoints; i++)
    #            w[i] /= weightSum;
    #        stat = MStatus::kSuccess;
    #    }
    #    else
    #    {
    #        stat = MStatus::kFailure;
    #    }
    #
    #    return stat;
    #}    

class MFloatPoint(MVector) :
    """ A 4 dimensional vector class that wraps Maya's api MFloatPoint class,
        It behaves identically to MPoint, but it also derives from api's MFloatPoint
        to keep api methods happy
        """    
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MFloatPoint    
    
class MColor(MPoint):
    """ A 4 dimensional vector class that wraps Maya's api MColor class,
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
        return tuple(colorsys.rgb_to_hsv(*clamp(c[:3]))+c[3:4])
    @staticmethod
    def hsvtorgb(c):
        c = tuple(c)
        # return colorsys.hsv_to_rgb(clamp(c[0]), clamp(c[1]), clamp(c[2]))
        return tuple(colorsys.hsv_to_rgb(*clamp(c[:3]))+c[3:4])
    
    # TODO : could define rgb and hsv iterators and allow __setitem__ and __getitem__ on these iterators
    # like (it's more simple) it's done in ArrayIter  
    def _getrgba(self):
        return tuple(self)
    def _setrgba(self, value):
        if not hasattr(value, '__iter__') :
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,)*4
        l = list(self)
        for i, v in enumerate(value[:4]) :
            if v is not None :
                l[i] = float(v)
        self.assign(*l)
    rgba = property(_getrgba, _setrgba, None, "The r,g,b,a MColor components""")       
    def _getrgb(self):
        return self.rgba[:3]
    def _setrgb(self, value):
        if not hasattr(value, '__iter__') :
            value = (value,)*3
        self.rgba = value[:3]
    rgb = property(_getrgb, _setrgb, None, "The r,g,b MColor components""")
    
    def _gethsva(self):
        return tuple(MColor.rgbtohsv(self))
    def _sethsva(self, value):
        if not hasattr(value, '__iter__') :
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,)*4
        l = list(MColor.rgbtohsv(self))
        for i, v in enumerate(value[:4]) :
            if v is not None :
                l[i] = float(v)
        self.assign(*MColor.hsvtorgb(self))   
    hsva = property(_gethsva, _sethsva, None, "The h,s,v,a MColor components""") 
    def _gethsv(self):
        return tuple(MColor.rgbtohsv(self))[:3]
    def _sethsv(self, value):
        if not hasattr(value, '__iter__') :
            value = (value,)*3
        self.hsva = value[:3]  
    hsv = property(_gethsv, _sethsv, None, "The h,s,v,a MColor components""")
    def _geth(self):
        return self.hsva[0]
    def _seth(self, value):
        self.hsva = (value, None, None, None)  
    h = property(_geth, _seth, None, "The h MColor component""")            
    def _gets(self):
        return self.hsva[1]
    def _sets(self, value):
        self.hsva = (None, value, None, None)  
    s = property(_gets, _sets, None, "The s MColor component""") 
    def _getv(self):
        return self.hsva[2]
    def _setv(self, value):
        self.hsva = (None, None, value, None)  
    v = property(_getv, _setv, None, "The v MColor component""") 
        
    # __new__ is herited from MPoint/MVector, need to override __init__ to accept hsv mode though    
                           
    def __init__(self, *args, **kwargs):
        """ Init a MColor instance
            Can pass one argument being another MColor instance , or the color components """
        cls = self.__class__
        mode = kwargs.get('mode', None)
        if mode is not None and mode not in cls.modes :
            raise ValueError, "unknown mode %s for %s" % (mode, util.clsname(self))
        # can also use the form <componentname>=<number>
        # for now supports only rgb and hsv flags
        hsvflag = {}
        rgbflag = {}
        for a in 'hsv' :
            if a in kwargs :
                hsvflag[a] = kwargs[a]
        for a in 'rgb' :
            if a in kwargs :
                rgbflag[a] = kwargs[a]
        # can't mix them
        if hsvflag and rgbflag :
            raise ValueError, "can not mix r,g,b and h,s,v keyword arguments in a %s declaration" % util.clsname(self)
        # if no mode specified, guess from what keyword arguments where used, else use 'rgb' as default
        if mode is None :
            if hsvflag :
                mode = 'hsv'
            else :
                mode = 'rgb'
        # can't specify a mode and use keywords of other modes
        if mode is not 'hsv' and hsvflag :
            raise ValueError, "Can not use h,s,v keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        elif mode is not 'rgb' and rgbflag :
            raise ValueError, "Can not use r,g,b keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
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
        # Initializing api's MColor with int values seems also not to always behave so we quantize first and 
        # use a float init always
        quantize = kwargs.get('quantize', None)
        if quantize is not None :
            try :
                quantize = float(quantize)
            except :
                raise ValueError, "quantize must be a numeric value, not %s" % (util.clsname(quantize)) 
        # can be initilized with a single argument (other MColor, MVector, Vector)
        if len(args)==1 :
            args = args[0]              
        # we dont rely much on MColor api as it doesn't seem totally finished, and do some things directly here               
        if isinstance(args, self.__class__) or isinstance(args, self.apicls) :
            if quantize :
                raise ValueError, "Can not quantize a MColor argument, a MColor is always stored internally as float color" % (mode, util.clsname(self))
            if mode == 'rgb' :
                args = Vector(args)
            elif mode == 'hsv' :
                args = Vector(cls.rgbtohsv(args))
        else :
            # single alpha value, as understood by api will break coerce behavior in operations
            # where other operand is a scalar
            #if not hasattr(args, '__iter__') :
            #    args = Vector(0.0, 0.0, 0.0, args)
            if hasattr(args, '__len__') :
                shape = (min(len(args), 4),)
            else :
                shape = (4,)
            args = Vector(args, shape=shape)   

        # quantize if needed
        if quantize :
            args /= quantize   
                     
        # apply keywords arguments, and convert if mode is not rgb   
        if mode == 'rgb' :
            if rgbflag :
                for i, a in enumerate('rgb') :
                    if a in rgbflag :  
                        if quantize :
                            args[i] = float(rgbflag[a] / quantize)
                        else :                                                   
                            args[i] = float(rgbflag[a])                          
        elif mode == 'hsv' :
            if hsvflag :
                for i, a in enumerate('hsv') :
                    if a in hsvflag : 
                        if quantize :
                            args[i] = float(hsvflag[a] / quantize)
                        else :                                                   
                            args[i] = float(hsvflag[a])   
            args = Vector(cls.hsvtorgb(args))
                                  
        try :
            self.assign(args)
        except :
            msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", mode, args))
            raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))                                 

            
    # overriden operators
    # action depends on second object type
    # TODO : would be nice to define LUT classes and allow MColor * LUT transform
    # overloaded operators
    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a 1D sequence (Array, Vector, MColor), __mul__ is mapped to element-wise multiplication,
            If b is a Matrix, __mul__ is similar to Point a by Matrix b multiplication (post multiplication or transformation of a by b),
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, Matrix) :
            # will defer to Matrix rmul
            return NotImplemented
        else :
            # will defer to Array.__mul__
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a 1D sequence (Array, Vector, MColor), __mul__ is mapped to element-wise multiplication,
            If b is a Matrix, __mul__ is similar to Matrix b by Point a matrix multiplication,
            multiplies every component of a by b if b is a single numeric value """     
        if isinstance(other, Matrix) :
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
    def gamma(self, g):
        """ c.gamma(g) applies gamma correction g to MColor c, g can be a scalar and then will be applied to r, g, b
            or an iterable of up to 4 (r, g, b, a) independant gamma correction values """             
        return gamma(self, g)
  
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

# to specify space of transforms

class MSpace(_api.MSpace):
    apicls = _api.MSpace
    __metaclass__ = _factories.MetaMayaTypeWrapper
    pass

#kInvalid
#    kTransform
#Transform matrix (relative) space
#    kPreTransform
#Pre-transform matrix (geometry)
#    kPostTransform
#Post-transform matrix (world) space
#    kWorld
#transform in world space
#    kObject
#Same as pre-transform space
#    kLast 

# sadly MTransformationMatrix.RotationOrder and MEulerRotation.RotationOrder don't match

#class MRotationOrder(int):
#    pass

#kInvalid
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

# functions that work on Matrix (det(), inv(), ...) herited from arrays
# and properly defer to the class methods

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
    
    # constants
    
    identity = _api.MMatrix()

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
            # MTransformationMatrix, MQuaternion, MEulerRotation api classes need conversion to MMatrix
            if hasattr(args, 'asMatrix') :
                args = args.asMatrix()                 
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                super(Matrix, self).__init__(*args)
                # _api.MScriptUtil.createMatrixFromList ( value, self )         
                # super(Matrix, self).__init__(*args)
            
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

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
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
                                
    data = property(_getdata, _setdata, _deldata, "The MMatrix/MFloatMatrix/MTransformationMatrix/MQuaternion/MEulerRotation data") 
    
    # set properties for easy acces to translation / rotation / scale of a MMatrix or derived class
    # some of these will only yield dependable results if MMatrix is a MTransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a MQuaternion
    
    def _getTranslate(self):
        t = MTransformationMatrix(self)
        return MVector(t.getTranslation(MSpace.kTransform))     
    def _setTranslate(self, value):
        t = MTransformationMatrix(self)
        t.setTranslation ( MVector(value), MSpace.kTransform )
        self.assign(t.asMatrix())
    translate = property(_getTranslate, _setTranslate, None, "The translation expressed in this MMatrix, in transform space") 
    def _getRotate(self):
        t = MTransformationMatrix(self)
        return MQuaternion(t.rotation())  
    def _setRotate(self, value):
        t = MTransformationMatrix(self)
        q = MQuaternion(value)
        t.setRotationQuaternion(q.x, q.y, q.z, q.w)
        self.assign(t.asMatrix())
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this MMatrix, in transform space") 
    def _getScale(self):
        t = MTransformationMatrix(self)
        ms = _api.MScriptUtil()
        ms.createFromDouble ( 1.0, 1.0, 1.0 )
        p = ms.asDoublePtr ()
        t.getScale (p, MSpace.kTransform);
        return MVector([ms.getDoubleArrayItem (p, i) for i in range(3)])        
    def _setScale(self, value):
        t = MTransformationMatrix(self)
        ms = _api.MScriptUtil()
        ms.createFromDouble (*MVector(value))
        p = ms.asDoublePtr ()
        t.setScale ( p, MSpace.kTransform)        
        self.assign(t.asMatrix())
    scale = property(_getScale, _setScale, None, "The scale expressed in this MMatrix, in transform space")  
                  
    # some MMatrix derived classes can actually be represented as matrix but not stored
    # internally as such by the API
    
    def asMatrix(self, percent=None):
        "The matrix representation for this MMatrix/MTransformationMatrix/MQuaternion/MEulerRotation instance"
        if percent is not None and percent != 1.0 :
            if type(self) is not MTransformationMatrix :
                self = MTransformationMatrix(self)
            return MMatrix(self.apicls.asMatrix(self, percent))
        else :
            if type(self) is MMatrix :
                return self
            else :
                return MMatrix(self.apicls.asMatrix(self))  
                  
    matrix = property(asMatrix, None, None, "The MMatrix representation for this MMatrix/MTransformationMatrix/MQuaternion/MEulerRotation instance")                 
                          
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                                                                    
    def assign(self, value):
        # don't accept instances as assign works on exact api.MMatrix type
        if type(value) != self.apicls and type(value) != type(self) :
            if not hasattr(value, '__iter__') :
                value = self.apicls(value)
                self.apicls.assign(self, value)
            else :
                if hasattr(value, 'flat') :
                    value = list(value.flat)
                _api.MScriptUtil.createMatrixFromList ( value, self ) 
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MMatrix api get method """
        ptr = self.matrix.matrix[4][4]
        return tuple(tuple(_api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(self.__class__.shape[1])) for r in xrange(self.__class__.shape[0]))

    def __len__(self):
        """ Number of components in the MVector instance, 3 for MVector, 4 for MPoint and MColor """
        return self.apicls.__len__(self)

    # iterator override     
    # TODO : support for optionnal __iter__ arguments           
    def __iter__(self, *args, **kwargs):
        """ Iterate on the MMatrix rows """
        return self.apicls.__iter__(self.data)   
    # contains is herited from Array contains
    
    # __getitem__ / __setitem__ override
    def __getitem__(self, index):
        """ m.__getitem__(index) <==> m[index]
            Get component index value from self.
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = Matrix(self)
        print list(m)
        return m.__getitem__(index)
        # return super(Matrix, self).__getitem__(index)

    # deprecated and __getitem__ should accept slices anyway
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start, end))

    # as api.MMatrix has no __setitem__ method
    def __setitem__(self, index, value):
        """ m.__setitem__(index, value) <==> m[index] = value
            Set value of component index on self
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = Matrix(self)
        m.__setitem__(index, value)
        self.assign(m) 

    # deprecated and __setitem__ should accept slices anyway
    def __setslice__(self, start, end, value):
        self.__setitem__(slice(start, end), value)
        
    def __delitem__(self, index) :
        """ Cannot delete from a class with a fixed shape """
        raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    def __delslice__(self, start):
        self.__delitem__(slice(start, end))           
    
    # TODO : wrap double MMatrix:: operator() (unsigned int row, unsigned int col ) const 

    # common operators herited from Matrix
    
    # operators using the Maya API when applicable   
    def __eq__(self, other):
        """ m.__eq__(v) <==> m == v
            Equivalence test """
        try :
            return bool(self.apicls.__eq__(self, other))
        except :
            return bool(super(MMatrix, self).__eq__(other))        
    def __ne__(self, other):
        """ m.__ne__(v) <==> m != v
            Equivalence test """
        return (not self.__eq__(other))             
    def __neg__(self):
        """ m.__neg__() <==> -m
            The unary minus operator. Negates the value of each of the components of m """        
        return self.__class__(self.apicls.__neg__(self)) 
    def __add__(self, other) :
        """ m.__add__(v) <==> m+v
            Returns the result of the addition of m and v if v is convertible to a Matrix (element-wise addition),
            adds v to every component of m if v is a scalar """ 
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__add__(other)) 
    def __radd__(self, other) :
        """ m.__radd__(v) <==> v+m
            Returns the result of the addition of m and v if v is convertible to a Matrix (element-wise addition),
            adds v to every component of m if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__radd__(other))  
    def __iadd__(self, other):
        """ m.__iadd__(v) <==> m += v
            In place addition of m and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented   
    def __sub__(self, other) :
        """ m.__sub__(v) <==> m-v
            Returns the result of the substraction of v from m if v is convertible to a Matrix (element-wise substration),
            substract v to every component of m if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__sub__(other))   
    def __rsub__(self, other) :
        """ m.__rsub__(v) <==> v-m
            Returns the result of the substraction of m from v if v is convertible to a Matrix (element-wise substration),
            replace every component c of m by v-c if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__rsub__(other))      
    def __isub__(self, other):
        """ m.__isub__(v) <==> m -= v
            In place substraction of m and v, see __sub__ """
        try :
            return self.__class__(self.__sub__(other))
        except :
            return NotImplemented             
    # action depends on second object type
    def __mul__(self, other) :
        """ m.__mul__(x) <==> m*x
            If x is a Matrix, __mul__ is mapped to matrix multiplication m*x, if x is a Vector, to Matrix by Vector multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of b by x if x is a single numeric value """
        try :
            return self.__class__._convert(self.apicls.__mul__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__mul__(other))       
    def __rmul__(self, other):
        """ m.__rmul__(x) <==> x*m
            If x is a Matrix, __rmul__ is mapped to matrix multiplication x*m, if x is a Vector (or MVector or MPoint or MColor),
            to transformation, ie Vector by Matrix multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of m by x if x is a single numeric value """
        try :
            return self.__class__._convert(self.apicls.__rmul__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__rmul__(other))
    def __imul__(self, other):
        """ m.__imul__(n) <==> m *= n
            Valid for MMatrix * MMatrix multiplication, in place multiplication of Matrix m by Matrix n """
        try :
            return self.__class__(self.__mul__(other))
        except :
            return NotImplemented  
    # __xor__ will defer to MVector __xor__ 

    # API added methods

    def setToIdentity (self) :
        """ m.setToIdentity() <==> m = a * b
            Sets Matrix to the identity matrix """
        try :        
            self.apicls.setToIdentity(self)
        except :
            self.assign(self.__class__())
        return self   
    def setToProduct ( self, left, right ) :
        """ m.setToProduct(a, b) <==> m = a * b
            Sets Matrix to the result of the product of Matrix a and Matrix b """
        try :        
            self.apicls.setToProduct(self.__class__(left), self.__class__(right))
        except :
            self.assign(self.__class__(self.__class__(left) * self.__class__(right)))
        return self   
    def transpose(self):
        """ Returns the transposed MMatrix """
        try :
            return self.__class__._convert(self.apicls.transpose(self))
        except :
            return self.__class__._convert(super(MMatrix, self).transpose())    
    def inverse(self):
        """ Returns the inverse MMatrix """
        try :
            return self.__class__._convert(self.apicls.inverse(self))
        except :
            return self.__class__._convert(super(MMatrix, self).inverse())    
    def adjoint(self):
        """ Returns the adjoint (adjugate) MMatrix """
        try :
            return self.__class__._convert(self.apicls.adjoint(self))
        except :
            return self.__class__._convert(super(MMatrix, self).adjugate())   
    def homogenize(self):
        """ Returns a homogenized version of the MMatrix """
        try :
            return self.__class__._convert(self.apicls.homogenize(self))
        except :
            return self.__class__._convert(super(MMatrix, self).homogenize())   
    def det(self):
        """ Returns the determinant of this MMatrix instance """
        try :
            return self.apicls.det4x4(self)
        except :
            return super(MMatrix, self).det()           
    def det4x4(self):
        """ Returns the 4x4 determinant of this MMatrix instance """
        try :
            return self.apicls.det4x4(self)
        except :
            return super(MMatrix, self[:4,:4]).det()    
    def det3x3(self):
        """ Returns the determinant of the upper left 3x3 submatrix of this MMatrix instance,
            it's the same as doing det(m[0:3, 0:3]) """
        try :
            return self.apicls.det3x3(self)
        except :
            return super(MMatrix, self[:3,:3]).det()          
    def isEquivalent(self, other, tol=_api.MVector_kTol):
        """ Returns true if both arguments considered as MMatrix are equal within the specified tolerance """
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MMatrix) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(MMatrix, nself).isEquivalent(nother, tol))      
    def isSingular(self) : 
        """ Returns True if the given MMatrix is singular """
        try :
            return bool(self.apicls.isSingular(self))
        except :
            return super(MMatrix, self).isSingular()     
 
    # additionnal methods
 
    def blend(self, other=None, blend=0.5):
        """ Returns a 0.0-1.0 scalar weight blend between self and other MMatrix,
            blend mixes MMatrix as transformation matrices """
        if other is None :
            other = self.__class__()
        if isinstance(other, MMatrix) :
            return self.__class__(self.weighted(1.0-blend)*other.weighted(blend))
        else :
            return blend(self, other)   
    def weighted(self, weight):
        """ Returns a 0.0-1.0 scalar weighted blend between identity and self """
        if type(self) is not MTransformationMatrix :
            self = MTransformationMatrix(self)
        return self.__class__._convert(self.asMatrix(weight))

class MFloatMatrix(MMatrix) :
    """ A 4x4 matrix class that wraps Maya's api MFloatMatrix class,
        It behaves identically to MMatrix, but it also derives from api's MFloatMatrix
        to keep api methods happy
        """    
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MFloatMatrix   

class MTransformationMatrix(MMatrix):
    apicls = _api.MTransformationMatrix 
        
class MQuaternion(MMatrix):
    apicls = _api.MQuaternion
    shape = (4,)
    cnames = ('x', 'y', 'z', 'w')      

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
            # MTransformationMatrix, MQuaternion, MEulerRotation api classes can convert to a rotation MQuaternion
            if hasattr(args, 'rotate') :
                args = args.rotate
            elif len(args) == 2 and isinstance(args[0], Vector) and isinstance(args[1], float) :
                # some special init cases are allowed by the api class, want to authorize
                # MQuaternion(MVector axis, float angle) as well as MQuaternion(float angle, MVector axis)
                args = (float(args[1]), MVector(args[0]))        
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                super(Vector, self).__init__(*args)
            
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

   # set properties for easy acces to translation / rotation / scale of a MMatrix or derived class
    # some of these will only yield dependable results if MMatrix is a MTransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a MQuaternion
    
    def _getTranslate(self):
        return MVector(0.0, 0.0, 0.0)     
    translate = property(_getTranslate, None, None, "The translation expressed in this MMQuaternion, which is always (0.0, 0.0, 0.0)") 
    def _getRotate(self):
        return self 
    def _setRotate(self, value):
        self.assign(value)
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this MQuaternion, in transform space") 
    def _getScale(self):
        return MVector(1.0, 1.0, 1.0)       
    scale = property(_getScale, None, None, "The scale expressed in this MQuaternion, which is always (1.0, 1.0, 1.0")  
                                           
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                   
                                                 
    def assign(self, value):
        """ Wrap the MQuaternion api assign method """
        # api MQuaternion assign accepts MMatrix, MQuaternion and MEulerRotation
        if isinstance(value, MMatrix) :
            value = value.rotate
        else :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MQuaternion api get method """
        ms = _api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)])

    # faster to override __getitem__ cause we know MQuaternion only has one dimension
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

    # as api.MVector has no __setitem__ method, so need to reassign the whole MVector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
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

class MEulerRotation(MQuaternion):
    apicls = _api.MEulerRotation
    shape = (4,)   
    cnames = ('x', 'y', 'z', 'o')   
    

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
    
    u.assign(MVector(4, 5, 6))
    print repr(u)
    #MVector([4.0, 5.0, 6.0])    
    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    print len(u)
    # 3
    # inherits from Vector --> Array
    print isinstance(u, Vector)
    # True
    print isinstance(u, Array)
    # True
    # as well as _api.MVector
    print isinstance(u, _api.MVector)
    # True
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
    # MVector([1.0, 2.0, 3.0])
    u = MVector(MPoint(1, 2, 3, 1), y=20, z=30)
    print repr(u) 
    # MVector([1.0, 20.0, 30.0])                           
    # should fail
    print "MVector(Vector(1, 2, 3, 4))"
    try :     
        u = MVector(Vector(1, 2, 3, 4))
    except :
        print "will raise ValueError: could not cast [1, 2, 3, 4] to MVector of size 3, some data would be lost"
           
    
            
    print u.get()
    # (1.0, 20.0, 30.0)
    print u[0]
    1.0
    u[0] = 10
    print repr(u)
    # MVector([10.0, 20.0, 30.0])   
    print (10 in u)
    # True
    print list(u)
    # [10.0, 20.0, 30.0]
    
    u = MVector.xAxis
    v = MVector.yAxis
    print MVector.xAxis
    print str(MVector.xAxis)
    print unicode(MVector.xAxis)
    print repr(MVector.xAxis)

    print "u = MVector.xAxis:"
    print repr(u)
    # MVector([1.0, 0.0, 0.0])
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
    q = p + u
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
    try :
        print length([1, 2, 3, 4], 1)
    except :
        print "Will raise ValueError, \"axis 0 is the only valid axis for a MVector, 1 invalid\""

    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])    
    print u.sqlength()
    # 14
    print repr(u.normal())
    # MVector([0.267261241912, 0.534522483825, 0.801783725737])
    u.normalize()
    print repr(u)
    # MVector([0.267261241912, 0.534522483825, 0.801783725737])

    u = MVector(1, 2, 3)
    print repr(u)  
    # MVector([1.0, 2.0, 3.0])  
    w = u + [0.01, 0.01, 0.01]
    print repr(w)
    # MVector([1.01, 2.01, 3.01])
    print (u == u)
    # True
    print (u == w)
    # False
    print (u == MVector(1.0, 2.0, 3.0))
    # True
    print (u == [1.0, 2.0, 3.0])
    # False    
    print (u == MPoint(1.0, 2.0, 3.0))
    # False
    print u.isEquivalent([1.0, 2.0, 3.0])
    # True
    print u.isEquivalent(MVector(1.0, 2.0, 3.0))
    # True
    print u.isEquivalent(MPoint(1.0, 2.0, 3.0))   
    # True
    print u.isEquivalent(w)
    # False     
    print u.isEquivalent(w, 0.1)
    # True
    
    u = MVector(1, 0, 0)
    print repr(u)
    # MVector([1.0, 0.0, 0.0]) 
    v = MVector(0.707, 0, -0.707)
    print repr(v)
    # MVector([0.707, 0.0, -0.707])              
    print repr(axis(u, v))
    # MVector([-0.0, 0.707, 0.0])
    print repr(u.axis(v))
    # MVector([-0.0, 0.707, 0.0])   
    print repr(axis(Vector(u), Vector(v)))
    # Vector([-0.0, 0.707, 0.0])
    print repr(axis(u, v, normalize=True))
    # MVector([-0.0, 1.0, 0.0])
    print repr(u.axis(v, normalize=True))
    # MVector([-0.0, 1.0, 0.0])    
    print repr(axis(Vector(u), Vector(v), normalize=True))
    # Vector([-0.0, 1.0, 0.0])    
    print angle(u,v)    
    # 0.785398163397
    print u.angle(v)
    # 0.785398163397
    print angle(Vector(u), Vector(v))
    # 0.785398163397
    print cotan(u, v)
    # 1.0
    print repr(u.rotateTo(v))
    # MQuaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(u.axis(v), u.angle(v)))
    # MVector([0.707106781187, 0.0, -0.707106781187])
    q = MQuaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(q))
    # MVector([0.707106781187, 0.0, -0.707106781187])
    print u.distanceTo(v)
    # 0.765309087885
    print u.isParallel(v)
    # False
    print u.isParallel(2*u)
    # True
    print repr(u.blend(v))
    # MVector([0.8535, 0.0, -0.3535])
        
    print "end tests MVector"

def _testMPoint() :
    
    print "MPoint class", dir(MPoint)
    print hasattr(MPoint, 'data')
    p = MPoint()
    print repr(p)
    # MPoint([0.0, 0.0, 0.0, 1.0])
    print "MPoint instance", dir(p)
    print hasattr(p, 'data')
    print repr(p.data)
    # MPoint([0.0, 0.0, 0.0, 1.0])
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
    p = MPoint(p, w=1)
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 1.0])    
        
    p = MPoint.origin
    print repr(p)
    # MPoint([0.0, 0.0, 0.0, 1.0])
    p = MPoint.xAxis
    print repr(p) 
    # MPoint([1.0, 0.0, 0.0, 1.0])

    p = MPoint(1, 2, 3)
    print repr(p)
    print repr(p + MVector([1, 2, 3]))
    # MPoint([2.0, 4.0, 6.0, 1.0])
    print repr(p + MPoint([1, 2, 3]))
    # MPoint([2.0, 4.0, 6.0, 1.0])    
    print repr(p + [1, 2, 3])
    # MPoint([2.0, 4.0, 6.0, 1.0])
    print repr(p + [1, 2, 3, 1])
    # MPoint([2.0, 4.0, 6.0, 2.0])
    print repr(p + MPoint([1, 2, 3, 1]))
    # MPoint([2.0, 4.0, 6.0, 1.0])
    
    print repr(MVector([1, 2, 3]) + p)
    # MPoint([2.0, 4.0, 6.0, 1.0])
    print repr(MPoint([1, 2, 3]) + p)
    # MPoint([2.0, 4.0, 6.0, 1.0])    
    print repr([1, 2, 3] + p)
    # MPoint([2.0, 4.0, 6.0, 1.0])
    print repr([1, 2, 3, 1] + p)
    # MPoint([2.0, 4.0, 6.0, 2.0])
    print repr(MPoint([1, 2, 3, 1]) + p)
    # MPoint([2.0, 4.0, 6.0, 1.0])
      
    print "p = MPoint(x=1, y=2, z=3)"        
    p = MPoint(x=1, y=2, z=3)
    print p.length()
    # 3.74165738677
    print p[:1].length()
    # 1.0
    print p[:2].length()
    # 2.2360679775
    print p[:3].length()
    # 3.74165738677
    
    p = MPoint(1.0, 1.0, 1.0)
    q = MPoint(2.0, 1.0, 1.0)
    r = MPoint(1.707, 1.0, 0.293)
    print repr(axis(q, r))
    # MVector([-0.0, 0.707, 0.0])
    print repr(q.axis(r))
    # MVector([-0.0, 0.707, 0.0])    
    print angle(q,r)    
    # 0.785398163397
    print q.angle(r)
    # 0.785398163397    
    print q.distanceTo(r)  
    # 0.765309087885
    print cotan(p, q, r)
    # 1.0
    
    print "end tests MPoint"
 
def _testMColor() :
    
    print "MColor class", dir(MColor)
    print hasattr(MColor, 'data')
    c = MColor()
    print repr(c)
    # MColor([0.0, 0.0, 0.0, 1.0])
    print "MPoint instance", dir(c)
    print hasattr(c, 'data')
    print repr(c.data)
    # MColor([0.0, 0.0, 0.0, 1.0])
    c = MColor(_api.MColor())
    print repr(c)     
    # MColor([0.0, 0.0, 0.0, 1.0])
    # use api convetion of single value means alpha
    # instead of Vector convention of filling all with value
    # which would yield # MColor([0.5, 0.5, 0.5, 0.5]) instead   
    print "c = MColor(0.5)"
    c = MColor(0.5)
    print repr(c)   
    # MColor([0.0, 0.0, 0.0, 0.5])
    print "c = round(MColor(128, quantize=255), 2)"
    c = round(MColor(128, quantize=255), 2)
    print repr(c) 
    # MColor([0.5, 0.5, 0.5, 0.5])
      
    print "c = MColor(1, 1, 1)"
    c = MColor(1, 1, 1)
    print repr(c)
    # MColor([1.0, 1.0, 1.0, 1.0])
    print "c = round(MColor(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)"
    c = round(MColor(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # MColor([1.0, 0.5, 1.0, 1.0])
    
    print "c = round(MColor(255, b=128, quantize=255, mode='rgb'), 2)"
    c = round(MColor(255, b=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # MColor([1.0, 1.0, 0.5, 1.0])
    print "c = MColor(1, 0.5, 2, 0.5)"
    c = MColor(1, 0.5, 2, 0.5)
    print repr(c)
    # MColor([1.0, 0.5, 2.0, 0.5])
    print "c = MColor(0, 65535, 65535, quantize=65535, mode='hsv')"
    c = MColor(0, 65535, 65535, quantize=65535, mode='hsv')
    print repr(c)
    # MColor([1.0, 0.0, 0.0, 1.0])
    print "c.rgb"
    print repr(c.rgb)
    # (1.0, 0.0, 0.0)   
    print "c.hsv"
    print repr(c.hsv)
    # (0.0, 1.0, 1.0)
    d = MColor(c, v=0.5, mode='hsv')
    print repr(d)
    # MColor([0.5, 0.0, 0.0, 1.0])
    print repr(d.hsv)
    # (0.0, 1.0, 0.5) 
    print "c = MColor(MColor.blue, v=0.5)"
    c = MColor(MColor.blue, v=0.5)
    print repr(c)
    # MColor([0.0, 0.0, 0.5, 1.0])
    print "round(c.hsv, 2)"
    print round(c.hsv, 2)
    # (0.67, 1.0, 0.5)
    c.r = 1.0
    print repr(c)
    # MColor([1.0, 0.0, 0.5, 1.0])
    print "round(c.hsv, 2)"
    print round(c.hsv, 2)
    # (0.92, 1.0, 1.0)
            
    print "c = MColor(1, 0.5, 2, 0.5).clamp()"
    c = MColor(1, 0.5, 2, 0.5).clamp()
    print repr(c)
    # MColor([1.0, 0.5, 1.0, 0.5])
    
    print "MColor(c, v=0.5)"
    d = MColor(c, v=0.5)
    print repr(d)
    # MColor([0.5, 0.25, 0.5, 0.5])
    print "round(d.hsv, 2)"
    print round(d.hsv, 2)
    # (0.83, 0.5, 0.5)
    print "d = c.gamma([2.2, 2.0, 2.3])"
    d = c.gamma([2.2, 2.0, 2.3])
    print repr(d)
    # MColor([1.0, 0.25, 1.0, 1.0])
    print "c = MColor(0.25, 0.5, 0.75)"
    c = MColor(0.0, 1,0, 0.0, 0.5)
    print repr(c)
    # MColor([0.0, 1,0, 0.0, 0.5])
    print "d = MColor.red.blend(MColor.blue, 0.5)"
    d = MColor.red.blend(MColor.blue, 0.5)
    print repr(d)
    # MColor([0.5, 0.0, 0.5, 1.0])
    print "c.over(d)"
    print repr(c.over(d))
    # MColor([0.5, 0.5, 0.5, 1.0])
    print "d.over(c)"
    print repr(d.over(c))
    # MColor([0.5, 0.0, 0.5, 1.0])

    # herited
    
    c = MColor(0.25, 0.5, 0.75, 1.0)
    print repr(c)

    d = MColor(1, 1, 1, 0.5)
    print repr(d)
    print "(c*d)/2.0"
    print repr((c*d)/2.0)
    
    print "end tests MColor"
    
def _testMMatrix() :

    print "MMatrix class", dir(MMatrix)
    m = MMatrix()
    print m.formated()
    print m[0, 0]
    print m[0:2, 0:3]
    print m(0, 0)
    print "MMatrix instance:", dir(m)
    print MMatrix.__readonly__
    print MMatrix.__slots__
    print MMatrix.shape
    print MMatrix.ndim
    print MMatrix.size
    print m.shape
    print m.ndim
    print m.size    
    # should fail
    m.shape = (4, 4)
    m.shape = 2
    
    print dir(MSpace)
       
    m = MMatrix.identity    
    # inherits from Matrix --> Array
    print isinstance(m, Matrix)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.MMatrix
    print isinstance(m, _api.MMatrix)
    # True
    # accepted directly by API methods     
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print repr(m)
    print repr(n)
    
    # inits
    m = MMatrix(range(16)) 
    print m.formated()
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]     
    M = Array(range(16), shape=(2, 2, 4))
    m = MMatrix(M)
    print m.formated() 
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]    
    M = Matrix(range(9), shape=(3, 3))
    m = MMatrix(M)
    print m.formated()   
    #[[0.0, 1.0, 2.0, 0.0],
    # [3.0, 4.0, 5.0, 0.0],
    # [6.0, 7.0, 8.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    t = _api.MTransformationMatrix()
    t.setTranslation ( MVector(1, 2, 3), _api.MSpace.kWorld ) 
    m = MMatrix(t)
    print m.formated() 
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    m = MMatrix(m, a30=10)   
    print m.formated() 
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [10.0, 2.0, 3.0, 1.0]]                   
    # should fail
    print "MMatrix(range(20)"
    m = MMatrix(range(20))
    print m.formated()
    try :     
        m = MMatrix(range(20))
        print m.formated()
    except :
        print "will raise ValueError: could not cast [1, 2, 3, 4] to MVector of size 3, some data would be lost"
     
    m = MMatrix.identity
    M = m.trimmed(shape=(3, 3))
    print repr(M)
    # Matrix([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    print M.formated()
    #[[1.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0],
    # [0.0, 0.0, 1.0]]    
    try: 
        m.trim(shape=(3, 3))
    except :
        print "will raise TypeError: new shape (3, 3) is not compatible with class MMatrix"
           
    print m.nrow
    print m.ncol
    # should fail
    m.nrow = 3
    print list(m.row)
    print list(m.col)
    
    m = MMatrix( Matrix(range(9), shape=(3, 3)).resized(shape=(4, 4), value=10) )
    print m.formated()
    
    
    
    print m.get()
    # (1.0, 20.0, 30.0)
    print m[0]
    1.0
    m[0] = 10
    print m.formated()
    # MVector([10.0, 20.0, 30.0])   
    print (10 in m)
    # True
    print list(m)
    # [10.0, 20.0, 30.0]
    print list(m.flat)
    
    
    u = MVector.xAxis
    v = MVector.yAxis
    print MVector.xAxis
    print str(MVector.xAxis)
    print unicode(MVector.xAxis)
    print repr(MVector.xAxis)

    print "u = MVector.xAxis:"
    print repr(u)

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = MMatrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print "m:"
    print m.round(2).formated()


  
    v=MVector(1, 2, 3)   
    print "v:"
    print repr(v)
    # MVector([1, 2, 3])
    print "v*m"
    print repr(v*m)
    # Vector([741, 852, 963])   
    print "m*v"
    print repr(M*V)
    # Vector([321, 654, 987])    
    
    p=MPoint(1, 10, 100, 1)   
    print "p:"
    print repr(p)
    # Vector([1, 10, 100, 1])
    print "p*m"
    print repr(p*m)
    # Vector([741.25, 852.5, 963.75, 1])
    print "m*p"
    print repr(m*p)
    # Vector([321, 654, 987, 81.25])
    
    print "v = [1, 2, 3]*m"
    v = Vector([1, 2, 3])*m
    print repr(v)
    print "v = [1, 2, 3, 1]*m"
    v = Vector([1, 2, 3, 1])*m
    print repr(v)          
    # should fail
    print "Vector([1, 2, 3, 4, 5])*m"
    try :
        v = Vector([1, 2, 3, 4, 5])*m
        print repr(v)
    except :
        print "Will raise ValueError: vector of size 5 and matrix of shape (4, 4) are not conformable for a Vector * Matrix multiplication"        

    # herited

    print "m = MMatrix(range(1, 17))"
    m = MMatrix(range(1, 17))
    print m.formated()
    # element wise
    print "[1, 10, 100]*m"
    print repr([1, 10, 100]*m)
    print "M = Matrix(range(20), shape=(4, 5))"
    M = Matrix(range(20), shape=(4, 5))
    print M.formated()
    print "m*M"
    print (m*M).formated()
    print "m*2"
    print (m*2).formated()
    print "2*m"
    print (2*m).formated()
    print "m+2"
    print (m+2).formated()
    print "2+m"
    print (2+m).formated()
    
    m.setToIdentity()
    print m.formated()
    m.setToProduct(m, M)
    print m.formated()
    
    
    
    print m.isEquivalent(m*M)
    
    print m.transpose().formated()
    
    
    
    print m.isSingular()
    
    print m.inverse()
    
    print m.adjoint()
    
    print m.adjugate()
    
    print m.homogenize()
    
    print m.det()
    
    print m.det4x4()
    
    print m.det3x3()
    
    print m.weighted(0.5)
    
    print m.blend(MMatrix.identity, 0.5)
            
    print "end tests MMatrix"

    
if __name__ == '__main__' :
    _testMVector()   
    _testMPoint()
    _testMColor()
    _testMMatrix()


    
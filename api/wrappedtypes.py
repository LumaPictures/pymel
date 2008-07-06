"""
A wrap of Maya's MVector, MPoint, MColor, MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation types
"""

import inspect
import math, copy
import itertools, operator, colorsys

import pymel.util as util
import pymel.mayahook as mayahook
import allapi as api
from pymel.util.arrays import *

# patch some Maya api classes that miss __iter__ to make them iterable / convertible to list
def _patchMVector() :
    def __iter__(self):
        """ Iterates on all 3 components of a Maya api MVector """
        for i in xrange(3) :
            yield self[i]
    type.__setattr__(api.MVector, '__iter__', __iter__)

def _patchMPoint() :
    def __iter__(self):
        """ Iterates on all 4 components of a Maya api MPoint """
        for i in xrange(4) :
            yield self[i]
    type.__setattr__(api.MPoint, '__iter__', __iter__)
    
def _patchMMatrix() :
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MMatrix """
        for r in xrange(4) :
            yield [api.MScriptUtil.getDoubleArrayItem(self[r], c) for c in xrange(4)]
    type.__setattr__(api.MMatrix, '__iter__', __iter__)

def _patchMTransformationMatrix() :
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MTransformationMatrix """
        return self.asMatrix().__iter__()
    type.__setattr__(api.MTransformationMatrix, '__iter__', __iter__)

_patchMVector()
_patchMPoint()
_patchMMatrix()
_patchMTransformationMatrix()



class MetaMayaTypeWrapper(metaReadOnlyAttr) :
    """ A metaclass to wrap Maya api types, with support for class constants """ 

    class ClassConstant(object):
        """ A data descriptor for user defined constants on the class """
        def __init__(self, value):
            self.value = value
        def __get__(self, instance, owner):
            # purposedly authorize notation MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None :
                return owner(self.value)
            else :
                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)
        def __set__(self, instance, value):
            raise AttributeError, "class constant cannot be set"
        def __delete__(self, instance):
            raise AttributeError, "class constant cannot be deleted"
          
    def __new__(mcl, classname, bases, classdict):
        """ Create a new class of metaClassConstants type """
         
        # define __slots__ if not defined
        if '__slots__' not in classdict :
            classdict['__slots__'] = ()
        if 'apicls' in classdict and not classdict['apicls'] in bases :
            # if not in bases, add to it
            bases = bases + (classdict['apicls'],)
            
        # create the new class   
        newcls = super(MetaMayaTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)
            
        # if hasattr(newcls, 'stype') :
        if hasattr(newcls, 'apicls') :
            # type (api type) used for the storage of data
            apicls  = newcls.apicls
            
            

            # build the data property
            #            def setdata(self, data):
            #                self._data = self.__class__.apicls(data)
            #            def getdata(self):
            #                return self._data
            #            p = property(getdata, setdata, None, "One %s" % apicls.__name__)
            #            type.__setattr__(newcls, 'data', p) 
            
            #    def _getdata(self):
            #        return list(self.get())
            #    def _setdata(self, data):
            #        mat = api.MMatrix()
            #        api.MScriptUtil.createMatrixFromList ( list(data), mat)
            #        self = self.__class__(mat) 
            #    def _deldata(self):
            #        del self     
            #    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data")              
                                     
            # build some constants on the class            
            constant = {}
            # constants in class definition will be converted from api class to created class
            for name, attr in newcls.__dict__.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaTypeWrapper.ClassConstant(attr)                          
            # we'll need the api clas dict to automate some of the wrapping
            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
            apiDict = dict(inspect.getmembers(apicls))            
            # defining class properties on the created class                 
            for name, attr in apiDict.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaTypeWrapper.ClassConstant(attr)
            # update the constant dict with herited constants
            mro = inspect.getmro(newcls)            
            for cls in mro :
                if isinstance(cls, MetaMayaTypeWrapper) :
                    for name, attr in cls.__dict__.iteritems() :
                        if isinstance(attr, MetaMayaTypeWrapper.ClassConstant) :
                            if not name in constant :
                                constant[name] = MetaMayaTypeWrapper.ClassConstant(attr.value)
            
            # build the protected list to make some class ifo and the constants read only class attributes
            # new.__slots__ = ['_data', '_shape', '_ndim', '_size']
            # type.__setattr__(newcls, '__slots__', slots) 
            
            # set class constants as readonly 
            readonly = newcls.__readonly__
            if 'stype' not in readonly :
                readonly['stype'] = None
            if 'apicls' not in readonly :
                readonly['apicls'] = None 
            for c in constant.keys() :
                readonly[c] = None          
            type.__setattr__(newcls, '__readonly__', readonly)          
            # store constants as class attributes
            for name, attr in constant.iteritems() :
                type.__setattr__(newcls, name, attr)
                                           
        else :
            raise TypeError, "must define 'apicls' in the class definition (which Maya API class to wrap)"
        
        return newcls 
 
# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(MetaMayaTypeWrapper) :
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

                 
class MVector(Vector) :
    """ A 3 dimensional vector class that wraps Maya's api MVector class,
        >>> v = MVector(1, 2, 3)
        >>> w = MVector(x=1, z=2)
        >>> z = MVector(MVector.xAxis, z=1)
        """
    __metaclass__ = MetaMayaArrayTypeWrapper
    __slots__ = ['_shape']
    # class specific info
    apicls = api.MVector
    # stype = api.MVector
    cnames = ('x', 'y', 'z')
    shape = (3,)

    def __new__(cls, *args, **kwargs): 
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        
        if len(args)==1 and hasattr(args[0],'__iter__') :
            args = args[0]
        
        shape = kwargs.get('shape', None)
        newapi = None  
        if shape is None : 
            # shortcut when initializing from other api types      
            try :
                newapi = cls.apicls(args)
            except :
                pass
        if newapi is None :
            if shape is None :
                shape = cls.shape
            size = kwargs.get('size', cls.size)
            nargs = Vector(*args, **{'shape':shape, 'size':size})
            nbargs = len(nargs)
            if hasattr(cls, 'size') and nbargs != cls.size :
                # to protect from forced casting from longuer data
                if nbargs > cls.size and not isinstance(args, cls) :
                    raise ValueError, "could not cast %s to %s of size %s, some data would be lost" % (args, cls.__name__, cls.size)
                l = list(cls.apicls())
                for i in xrange(min(nbargs, cls.size)) :
                    l[i] = nargs[i]
            else :
                l = list(nargs)
            try :
                newapi = cls.apicls(*l)
            except :
                pass
        
        if newapi is not None and hasattr(cls, 'cnames') and len(kwargs) :  
            # can also use the form <componentname>=<number>
            l = list(newapi)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    l[i] = float(kwargs[c])
                    setcomp = True
            if setcomp :
                newapi = cls.apicls(*l)
              
        self.apicls.assign(self, newapi)              
        try :        
            self.apicls.assign(self, newapi)
        except :
            if hasattr(cls, 'cnames') and newapi is not None :
                msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, list(newapi)))
                raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)
            else :
                msg = ", ".join(["%r" % (a) for a in args])
                raise TypeError, "in %s(%s), arguments do not fit class definition, check help(%s) " % (cls.__name__, msg, cls.__name__)
            
    # display      
#    def __str__(self):
#        return '[%s]' % ", ".join(map(str, self))
#    def __unicode__(self):
#        return u'[%s]' % ", ".join(map(unicode, self))    
#    def __repr__(self):
#        return '%s(%s)' % (self.__class__.__name__, ", ".join(map(str, self)))          
#
#    # wrap of list-like access methods
#    def __len__(self):
#        """ MVector class is a one dimensional array of a fixed length """
#        return self.size
    
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        ms = api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        # self.data.get(p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)]) 
    # TODO : make Vector methods more generic (list or iterable API class) and get rid of this
    def __getitem__(self, i):
        """ Get component i value from self """
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
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
        v.__setitem__(i, a)
        self.__init__(*v) 
    def _iter(self):
        for i in xrange(len(self)) :
            yield self.apicls.__getitem__(self, i)           
    def __iter__(self):
        """ Iterate on the api components """
        if hasattr(self.apicls, '__iter__') :
            return self.apicls.__iter__(self)
        elif hasattr(self.apicls, '__getitem__') :
            return self._iter
        else :
            raise NotImplemented    
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in list(self)
    
    
    # common operators herited from Vector
    
    # operators using the Maya API when applicable
#    def __neg__(self):
#        """ u.__neg__() <==> -u
#            Returns the MVector obtained by negating every component of u """        
#        return self.__class__(map(lambda x: -x, self))   
#    def __invert__(self):
#        """ u.__invert__() <==> ~u
#            unary inversion, returns 1 - u for Vectors """        
#        return self.__class__(map(lambda x: 1.0-x, self))      
#    def __add__(self, other) :
#        """ u.__add__(v) <==> u+v
#            Returns the result of the addition of u and v if v is convertible to MVector,
#            adds v to every component of u if v is a scalar """        
#        if isinstance(other, MVector) :
#            # return self.__class__(map( lambda x, y: x+y, self[:MVector.size], other[:MVector.size]))
#            # return self.__class__(self.data.__add__(other.vector))
#            return difmap(operator.add, self, other)
#        elif util.isScalar(other) :
#            return self.__class__(map( lambda x: x+other, self))        
#        else :            
#            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
#    def __radd__(self, other) :
#        """ u.__radd__(v) <==> v+u
#            Returns the result of the addition of u and v if v is convertible to MVector,
#            adds v to every component of u if v is a scalar """        
#        if isinstance(other, MVector) :
#            # return self.__class__(map( lambda x, y: x+y, self[:MVector.size], other[:MVector.size]))
#            # return self.__class__(self.data.__add__(other.vector))
#            return difmap(operator.add, other, self)
#        elif util.isScalar(other) :
#            return self.__class__(map( lambda x: x+other, self))        
#        else :            
#            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
#    def __iadd__(self, other):
#        """ u.__iadd__(v) <==> u += v
#            In place addition of u and v, see __add__ """
#        self._data = (self.__add__(other)).data
#    def __sub__(self, other) :
#        """ u.__sub__(v) <==> u-v
#            Returns the result of the substraction of v from u if v is a MVector instance,
#            substract v to every component of u if v is a scalar """        
#        if isinstance(other, MVector) :
#            # difference of two points is a vector, of a vector and a point is a point
#            if len(other) > len(self) :
#                # other is a MPoint or MColor
#                return other.__class__(self.data.__sub__(other.vector))
#            else :
#                return self.__class__(self.data.__sub__(other.data))                     
#        elif util.isScalar(other) :
#            return self.__class__(map( lambda x: x-other, self))
#        else :            
#            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
#    def __rsub__(self, other) :
#        """ u.__rsub__(v) <==> v-u
#            Returns the result of the substraction of u from v if v is a MVector instance,
#            replace every component c of u by v-c if v is a scalar """        
#        if isinstance(other, MVector) :
#            # difference of two points is a vector, of a vector and a point is a point
#            if len(other) > len(self) :
#                # other is a MPoint or MColor
#                return other.__class__(other.data.__sub__(self.data))
#            else :
#                return self.__class__(other.data.__sub__(self.data))                     
#        elif util.isScalar(other) :
#            return self.__class__(map( lambda x: other-x, self))
#        else :            
#            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (util.clsname(other), util.clsname(self))    
#    def __isub__(self, other):
#        """ u.__isub__(v) <==> u -= v
#            In place substraction of u and v, see __sub__ """
#        self._data = (self.__sub__(other)).data        
#    def __div__(self, other):
#        """ u.__div__(v) <==> u/v
#            Returns the result of the element wise division of each component of u by the
#            corresponding component of v if both are convertible to MVector,
#            divide every component of u by v if v is a scalar """  
#        if hasattr(other, '__iter__') :
#            lm = min(len(other), len(self))
#            l = map(lambda x, y: x/y, self[:lm], other[:lm]) + self[lm:len(self)]
#            return self_class__(*l)
#        elif util.isScalar(other) :
#            return self.__class__(map(lambda x: x/other, self))
#        else :
#            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(self), util.clsname(other))  
#    def __rdiv__(self, other):
#        """ u.__rdiv__(v) <==> v/u
#            Returns the result of the element wise division of each component of v by the
#            corresponding component of u if both are convertible to MVector,
#            invert every component of u and multiply it by v if v is a scalar """
#        if hasattr(other, '__iter__') :
#            lm = min(len(other), len(self))
#            l = map(lambda x, y: y/x, self[:lm], other[:lm]) + self[lm:len(self)]
#            return self_class__(*l)
#        elif util.isScalar(other) :
#            return self.__class__(map(lambda x: other/x, self))
#        else :
#            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
#    def __idiv__(self, other):
#        """ u.__idiv__(v) <==> u /= v
#            In place division of u by v, see __div__ """        
#        self._data = (self.__div__(other)).data
#    def __eq__(self, other):
#        """ u.__eq__(v) <==> u == v """
#        if isinstance(other, self.__class__) :
#            return bool( self.data.__eq__(self.__class__(other).data))
#        else :
#            try :
#                return self.__eq__(self.__class__(other))
#            except :
#                return False              
#    # action depends on second object type
#    # TODO : do we really want to map dot product here as api does, overriding possibility for element wise mult ?
#    def __mul__(self, other) :
#        """ u.__mul__(v) <==> u*v
#            The multiply '*' operator is mapped to the dot product when both objects are instances of MVector,
#            to the transformation of u by matrix v when v is an instance of MMatrix,
#            and to element wise multiplication when v is a scalar or a sequence """
#        if isinstance(other, self.__class__) :
#            # dot product in case of a vector
#            return self.data.__mul__(other.data)
#        elif isinstance(other, MMatrix) :
#            # MMatrix transformation
#            return self.__class__(self.data.__mul__(other.matrix))
#        elif util.isScalar(other) :
#            # multiply all components by a scalar
#            return self.__class__(map(lambda x: x*other, self))
#        elif util.isSequence(other) :
#            # element wise multiplication by a list or tuple
#            lm = min(len(other), len(self))
#            l = map(lambda x, y: x*y, self[:lm], other[:lm]) + self[lm:len(self)]
#            return self_class__(*l)
#        else :
#            raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
#    def __rmul__(self, other):
#        """ u.__rmul__(v) <==> v*u
#            This is equivalent to u*v thus u.__mul__(v) unless v is a MMatrix, in that case this operation
#            is not defined """ 
#        # not possible with a MMatrix
#        if isinstance(other, self.__class__) or util.isScalar(other) or util.isSequence(other) : 
#            # in these cases it's commutative         
#            return self.__mul__(other)
#        elif isinstance (other, MMatrix) :
#            # left side MMatrix
#            try :
#                m = MMatrix(other)
#            except :
#                return self.__mul__(other)
#        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
#    def __imul__(self, other):
#        """ u.__imul__(v) <==> u *= v
#            Valid for MVector * MMatrix multiplication, in place transformation of u by MMatrix v
#            or MVector by scalar multiplication only """
#        if isinstance(other, MMatrix) :
#            self._data = self.data.__mul__(other.matrix)
#        elif util.isScalar(other) :
#            self._data = self.__class__(map(lambda x: x.__mul__(other), self)).data
#        else :
#            self._data = self.__mul__(MMatrix(other)).data             
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two 3D vectors,
            if v is a MMatrix, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, Vector) :
            return self.cross(other)
        elif isinstance(other, Matrix) :
            return self.transformAsNormal(other)
        else :
            return NotImplemented
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a MMatrix """        
        return self.__class__(self.__xor__(other))
        
    # wrap of API MVector methods    
    def isEquivalent(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as MVector are equal  within the specified tolerance """
        if isinstance(other, MVector) :
            return bool(self.apicls.isEquivalent(self, self.__class__(other)._data, tol))
        else :
            return bool(super(Vector, self).isEquivalent(other, tol))
    def isParallel(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as MVector are parallel within the specified tolerance """
        try :
            return bool(self._data.isParallel(MVector(other)._data, tol))
        except :
            raise TypeError, "%r is not convertible to a MVector, or tolerance %r is not convertible to a number, check help(MVector)" % (other, tol) 
    def distanceTo(self, other):
        return (other-self).length()
    def length(self):
        """ Length of self """
        return self.vector.length()      
    def normal(self): 
        """ Return a normalized copy of self """ 
        return self.__class__(self.vector.normal())
    def normalize(self):
        """ Performs an in place normalization of self """
        self.data = self.vector.normalize()
    def angle(self, other):
        """  Returns the angle in radians between both arguments considered as MVector """
        if isinstance(other, MVector) :
            return self.vector.angle(other.vector)
        else :
            raise TypeError, "%r is not convertible to a MVector, check help(MVector)" % other 
    def rotateTo(self, other):
        """ Returns the Quaternion that represents the rotation of this MVector into the other
            argument considered as MVector about their mutually perpendicular axis """
        if isinstance(other, MVector) :
            return Quaternion(self.vector.rotateTo(other.vector))
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
            return self.__class__._convert(api.MVector.transformAsNormal(MVector(self), MMatrix(other)))
        else :
            return self.__class__._convert(super(self.__class__, self).transformAsNormal(other))
    # additional methods
    def dot(self, other):
        """ dot product of two vectors """
        if isinstance(other, MVector) :
            return api.MVector.__mul__(MVector(self), MVector(other))
        else :
            return super(self.__class__, self).dot(other)       
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, MVector) :
            return self.__class__._convert(api.MVector.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(self.__class__, self).cross(other))              
    def sqLength(self):
        """ Squared length of vector """
        return self.vector*self.vector
    def sum(self):
        """ Returns the sum of the components of self """
        return reduce(lambda x, y: x+y, self, 0) 
    def axis(self, other, normalize=False):
        """ Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, MVector) :
            if normalize :
                return (self ^ other).normal()
            else :
                return self ^ other
        else :
            raise TypeError, "%r is not a MVector instance" % other                  
    def basis(self, other, normalize=False): 
        """ Returns the basis MMatrix built using u, v and u^v as coordinate axis,
            The u, v, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
                n = u ^ v
                v = n ^ u
            if the normalize keyword argument is set to True, the vectors are also normalized """
        if isinstance(other, MVector) :
            if normalize :
                u = self.normal()
                n = u ^ other.normal()
                v = n ^ u
            else :
                u = self
                n = u ^ other
                v = n ^ u
            return MMatrix(u, v, n, mode='basis')
        else :
            raise TypeError, "%r is not a MVector instance" % other
    def cotan(self, other):
        """ cotangent of the (self, other) angle """
        if isinstance(other, MVector) :
            return (self*self-other*self)/(self^other).length();
        else :
            raise TypeError, "%r is not a MVector instance" % other    
    def blend(self, other, blend=0.5):
        """ u.blend(v, blend) returns the result of blending from MVector instance u to v according to
            either a scalar blend where it yields u*(1-blend) + v*blend MVector,
            or a an iterable of up to 3 (x, y, z) independent blend factors """ 
        if isinstance(other, MVector) :
            other = MVector(other)
            if util.isScalar(blend) :
                l = (self*(1-blend) + other*blend)[:len(other)] + self[len(other):len(self)]
                return self.__class__(*l)            
            elif hasattr(blend, '__iter__') : 
                bl = list(blend)
                lm = min(len(bl), len(self), len(other))
                l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
                return self.__class__(*l)

            else :
                raise TypeError, "blend can only be an iterable (list, tuple, MVector...) of scalars or a scalar, not a %s" % util.clsname(blend)
        else :
            raise TypeError, "%s is not convertible to a %s, check help(%s)" % (util.clsname(other), util.clsname(self), util.clsname(self))          
    def clamp(self, low=0.0, high=1.0):
        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
            or the corresponding components of low and high if low and high are sequences of scalars """
        ln = len(self)
        if util.isScalar(low) :
            low = [low]*ln
        elif hasattr(low, '__iter__') : 
            low = list(low)[:ln]
        else :
            raise TypeError, "'low' can only be an iterable (list, tuple, MVector...) of scalars or a scalar, not a %s" % util.clsname(blend) 
        if util.isScalar(high) :
            high = [high]*ln
        elif hasattr(high, '__iter__') : 
            high = list(high)[:ln]
        else :
            raise TypeError, "'high' can only be an iterable (list, tuple, MVector...) of scalars or a scalar, not a %s" % util.clsname(blend)         
        lm = min(ln, len(low), len(high))             
        return self.__class__(map(clamp, self, low, high))
           
class MPoint(MVector, api.MPoint):
    apicls = api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)
    

#    # base methods are inherited from MVector
#    # define the __new__ method
    def __new__(cls, *args, **kwargs):
        """ A new instance of that MPoint or subtype of MVector class """
        return MVector.__new__(cls, *args, **kwargs) 
        
    def __init__(self, *args, **kwargs):
        """ Init a MPoint instance,
            Can pass one argument being another MVector instance , or the point components """
        MVector.__init__(self, *args, **kwargs)
               
    # modified operators
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a MVector instance,
            substract v to every component of u if v is a scalar.
            The substraction of two Points yields a MVector, of a MPoint and a MVector yields a MPoint """        
        if isinstance(other, MVector) :
            # difference of two points is a vector, of a vector and a point is a point
            if type(other) is MPoint :
                return MVector(self.point.__sub__(other.point))
            else :
                return self.__class__(self.data.__sub__(other.data))                     
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x-other, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a MVector instance,
            replace every component c of u by v-c if v is a scalar """        
        if isinstance(other, MVector) :
            # difference of two points is a vector, of a vector and a point is a point
            if type(other) is MPoint :
                # other is a MPoint or MColor
                return MVector(other.data.__sub__(self.data))
            else :
                return self.__class__(other.data.__sub__(self.data))                     
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: other-x, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (util.clsname(other), util.clsname(self))    
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        self._data = (self.__sub__(other)).data       
    # specific api methods
    def cartesianize (self) :
        """ If this point instance is of the form P(W*x, W*y, W*z, W), for some scale factor W != 0,
            then it is reset to be P(x, y, z, 1).
            This will only work correctly if the point is in homogenous form or cartesian form.
            If the point is in rational form, the results are not defined. """
        self.data = self.point.cartesianize()
    def rationalize (self) :
        """ If this point instance is of the form P(W*x, W*y, W*z, W) (ie. is in homogenous or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(x, y, z, W).
            This will only work correctly if the point is in homogenous or cartesian form.
            If the point is already in rational form, the results are not defined. """
        self.data = self.point.rationalize()
    def homogenize (self) :
        """ If this point instance is of the form P(x, y, z, W) (ie. is in rational or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(W*x, W*y, W*z, W). """
        self.data = self.point.homogenize()
    def distanceTo (self, other):
        """ Return the distance between this MPoint and the MPoint passed as an argument """
        if isinstance(other, self.__class__) :
            return self.point.distanceTo (self.__class__(other)._data)
        else :
            raise TypeError, "%s is not a %s instance" % (other, util.clsname(self))            
    def isEquivalent (other, tol = api.MPoint_kTol) :
        """ p.isEquivalent(q, tol) = True if p and q are equivalent in the given tolerance """ 
        try :
            return bool(self.data.isEquivalent(self.__class__(other)._data, tol))
        except :
            raise TypeError, "%s is not convertible to a %s, or tolerance %s is not convertible to a number, check help(%s)" % (other, util.clsname(self), tol, util.clsname(self)) 
    def cotan(self, q, r) :
        """ p.cotan(q, r ) = cotangent of the (q-p, r-p) angle """
        if isinstance(q, self.__class__) and isinstance(q, self.__class__) :
            return ((r - q)*(self - b))/((r - q)^(self - b)).length();
        else :
            raise TypeError, "%s or %s is not a %s instance" % (q, r, util.clsname(self))       
    # TODO
    def planar(self, *args, **kwargs): 
        """ p.planar(q, r, s (...), tol=tolerance) returns True if all provided points are planar within given tolerance """
        # tol = kwargs.get('tol', api.MPoint_kTol)
        pass
    def center(self, *args): 
        """ p.center(q, r, s (...)) returns the MPoint that is the barycenter of p, q, r, s (...) """
        pass
    def bWeights(self, *args): 
        """ p.barycenter(p0, p1, (...), pn) returns barycentric weights so that  """
        pass                
    
class MColor(MPoint):
    apicls = api.MColor
    cnames = ('r', 'g', 'b', 'a')
    shape = (4,)
    
    # constants
    red = api.MColor(1.0, 0.0, 0.0)
    green = api.MColor(0.0, 1.0, 0.0)
    blue = api.MColor(0.0, 0.0, 1.0)
    white = api.MColor(1.0, 1.0, 1.0)
    black = api.MColor(0.0, 0.0, 0.0)
    opaque = api.MColor(0.0, 0.0, 0.0, 1.0)
    clear = api.MColor(0.0, 0.0, 0.0, 0.0)

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
    def data(self):
        return self._data
    @property
    def vector(self):
        return api.MVector(self._data[0], self._data[1], self._data[2])
    @property
    def point(self):
        return api.MPoint(self._data[0], self._data[1], self._data[2])
    @property
    def color(self):
        return self._data
    
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
        # NOTE: do not try to use mode with api.MColor, it seems bugged as of 2008
            #import colorsys
            #colorsys.rgb_to_hsv(0.0, 0.0, 1.0)
            ## Result: (0.66666666666666663, 1.0, 1.0) # 
            #c = api.MColor(api.MColor.kHSV, 0.66666666666666663, 1.0, 1.0)
            #print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 0.666666686535 1.0 1.0  #
            #c = api.MColor(api.MColor.kHSV, 0.66666666666666663*360, 1.0, 1.0)
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
                    # else see if we can init the api class directly (an api.MColor or single alpha value)
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
# t = api.MTransformationMatrix()
# t.setTranslation(api.MVector(1, 2, 3), api.MSpace.kWorld)
# m = t.asMatrix()
# mm(3,0)
# 1.0
# mm(3,1)
# 2.0
# mm(3,2)
# 3.0  


class MMatrix(Matrix):
    """ A 4x4 transformation matrix based on api MMatrix 
        >>> v = self.__class__(1, 2, 3)
        >>> w = self.__class__(x=1, z=2)
        >>> z = self.__class__(api.Mself.__class__.xAxis, z=1)
        """    
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = api.MMatrix
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
        return api.MTransformationMatrix(self._data)   
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
                    if api.MScriptUtil.createMatrixFromList ( l, self._data ) :
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
            if api.MScriptUtil.createMatrixFromList ( l, self._data ) :
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
        return tuple(tuple(api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(self.__class__.shape[1])) for r in xrange(self.__class__.shape[0]))
        
    @property
    def row(self):
        """ Iterator on the MMatrix rows """
        return self.axisiter(0)
        # return [[api.MScriptUtil.getDoubleArrayItem(self.matrix[r], c) for c in xrange(self.__class__.shape[1])] for r in xrange(self.__class__.shape[0])]        
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
                return tuple([api.MScriptUtil.getDoubleArrayItem(ptr, j) for j in xrange(self.__class__.shape[1])][c])
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
                api.MScriptUtil.setDoubleArray(ptr, c, value)
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
                api.MScriptUtil.createMatrixFromList ( l, self._data )                 
            else :
                raise IndexError, "There are only %s columns in class %s" % (self.__class__.shape[1], self.__class__.__name__)
        elif util.isScalar(r) :
            # numpy like m[2,:] format, we set (possibly partial) columns
            if r in range(self.__class__.shape[0]) :
                ptr = self.matrix[r]
                if util.isScalar(value) :
                    for j in range(self.__class__.shape[1])[c] :
                        api.MScriptUtil.setDoubleArray(ptr, j, value)
                elif hasattr(value, '__getitem__') :
                    for v, j in enumerate(range(self.__class__.shape[1])[c]) :
                        # to allow to assign 3 value vectors to rows or columns, 4th cell is left unchanged
                        try :
                            api.MScriptUtil.setDoubleArray(ptr, j, value[v]) 
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
            yield tuple(api.MScriptUtil.getDoubleArrayItem(ptr, c) for c in xrange(self.__class__.shape[1]))         
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
#            return self.__class__(self.__class__.api.__div__(self._data,other))
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
#                if self.__class__(self.__class__.api.__eq__(self._data, self.__class__(other)._data)) :
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
    def isEquivalent (self, other, tol = api.MMatrix_kTol) :
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
    apicls = api.MQuaternion
    shape = (4,)
    cnames = ('x', 'y', 'z', 'w')      

    @property
    def matrix(self):
        return self._data.asMatrix()
    @property
    def tmatrix(self):
        return api.MTransformationMatrix(self.matrix)   
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
#        ms = api.MScriptUtil()
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
    apicls = api.MEulerRotation
    shape = (4,)   
    cnames = ('x', 'y', 'z', 'o')   
    
    @property
    def matrix(self):
        return self._data.asMatrix()
    @property
    def tmatrix(self):
        return api.MTransformationMatrix(self.matrix)   
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


def _testMVector() :
    
    print "MVector class", dir(MVector)
    
    u = MVector()
    print u
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
    u = MVector(x=1, y=2, z=3)
    print repr(u)
    u = MVector([1, 2], z=3)
    print repr(u)
    u = MVector(api.MPoint(1, 2, 3))
    print u  
    print "u = MVector(Vector(1, 2, 3))"
    u = MVector(Vector(1, 2, 3))
    print u
    u = MVector(1)
    print u     
    u = MVector(1,2)
    print u                  
    u = MVector(Vector(1, shape=(2,)))
    print u        
    # should fail
    print "MVector(Vector(1, 2, 3, 4))"
    try :     
        u = MVector(Vector(1, 2, 3, 4))
    except :
        print "will raise ValueError: could not cast [1, 2, 3, 4] to MVector of size 3, some data would be lost"
    p = MPoint(1, 2, 3)
    u = MVector(p, y=10, z=10)
    print u           
            
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
    print "u = MVector.xAxis: %r" % u
    print "v = MVector.yAxis: %r" % v
    n = u ^ v
    print "n = u ^ v: %r" % n
    # print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    n = u ^ Vector(v)
    print "n = u ^ Vector(v): %r" % n
    n = u ^ [0, 1, 0]
    print "n = u ^ [0, 1, 0]: %r" % n    
    # print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)    
    n[0:2] = [1, 1]
    print "n[0:2] = [1, 1] : %r" % n
    print Array(2, shape=(3,))
    n = n*2
    print "n = n * 2 : %r" % n
    n = n*[0.5, 1.0, 2.0]
    print "n = n * [0.5, 1.0, 2.0] : %r" % n    
    print "n * n : %s" % (n * n)
    # 21
    
    print "end tests MVector"

def _testMPoint() :
    
    print "MPoint class", dir(MPoint)
    
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
    t = api.MTransformationMatrix()
    t.setTranslation(api.MVector(1, 2, 3), api.MSpace.kWorld)
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


    
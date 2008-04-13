"""
A wrap of Maya's MVector type
"""
#import pymel.util as util
#import pymel.api as api
import inspect
import maya.OpenMaya as api
from math import *
from mathutils import *
from copy import *
import operator, colorsys
#from pymel.core.mathutils import *

def isScalar(obj):
    # consider only ints and floats numeric
    return isinstance(obj,int) or isinstance(obj,float)

def isSequence( obj ):
    return type( obj ) is list or type( obj ) is tuple

clsname = lambda x:x.__class__.__name__

# maps a fn on two iterable classes of possibly different sizes,
# mapping on smallest size then filling
# to largest size with unmodified remnant of largest list. Used for operation between vectors
# of different sizes when we want to allow this
def difmap(fn, first, second):
    """ maps a function on two iterable classes of possibly different sizes,
        mapping on smallest size then filling to largest size with unmodified remnant of largest list.
        Will cast the result to the largest class type or to the first class in case of equal size.
        Classes must support iteration and __getslice__ """    
    l1 = len(first)
    l2 = len(second)
    if l1<l2 :
        return second.__class__(map(fn, first, second[:l1])+second[l1:l2])
    elif l1>l2 :
        return first.__class__(map(fn, first[:l2], second)+first[l2:l1])
    else :
        return first.__class__(map(fn, first, second))
        

# the meta class of metaMayaWrapper
class MetaMayaTypeWrapper(type) :
    """ A metaclass to wrap Maya type classes such as MVector, MMatrix """

    def __setattr__(cls, name, value):
        # print "setattr called on class %s.%s = %s" % (cls.__name__, name, value)  
        try :
            protected = cls._protected
        except :
            protected = ()
        if name in protected :
            raise AttributeError, "attribute %s is a %s constant and cannot be modified on class %s" % (name, cls.__name__, cls.__name__)
        else :
            super(MetaMayaTypeWrapper, cls).__setattr__(name, value)
           
    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as MVector or MMatrix """
            
        # define __setattr__ to forbid modification of protected class info
        def __setattr__(self, name, value):
            # print "setattr called on (instance of %s).%s = %s" % (self.__class__.__name__, name, value)
            try :
                protected = self.__class__._protected
            except :
                protected = ()
            if name in protected :
                raise AttributeError, "attribute '%s' is a %s constant and cannot be modified on an instance of class %s" % (name, self.__class__.__name__, self.__class__.__name__)
            else :
                object.__setattr__(self, name, value)
        classdict['__setattr__'] = __setattr__
           
        # create the new class   
        newcls = super(MetaMayaTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)
        
        try :
            apiClass = newcls.apiclass
        except :
            apiClass = None
        if apiClass :
            # build the properties according to component names
            try :
                complist = newcls.apicomp
            except :
                complist = ()
            for i in xrange(len(complist)) :
                p = eval("property( lambda self: self.__getitem__(%s) ,  lambda self, val: self.__setitem__(%s,val) )" % (i, i))
                type.__setattr__(newcls, complist[i], p)
            # build the data property
            def setdata(self, data):
                self._data = self.__class__.apiclass(data)
            def getdata(self):
                return self._data
            p = property(getdata, setdata, None, "One %s" % apiClass.__name__)
            type.__setattr__(newcls, 'data', p)
            # build a property as a shortcut to self.__class__.apiclass
            p = property(lambda self:self.__class__.apiclass, None, None, "The api class to build internal data")
            type.__setattr__(newcls, 'api', p)
            # build some constants on the class            
            constant = {}
            # constants in class definition will be converted from api class to created class
            print "class dict so far", newcls.__dict__
            for name, attr in newcls.__dict__.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apiClass) :
                    print "class constant found: %s" % name
                    if name not in constant :
                        constant[name] = newcls(attr)                          
            # we'll need the api clas dict to automate some of the wrapping
            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
            apiDict = dict(inspect.getmembers(apiClass))            
            # defining class properties on the created class                 
            for name, attr in apiDict.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apiClass) :
                    print "api constant found: %s" % name
                    if name not in constant :
                        constant[name] = newcls(attr)
            # update the constant dict with herited constants
            mro = inspect.getmro(newcls)            
            for cls in mro :
                for name, attr in cls.__dict__.iteritems() :
                    if type(cls) == MetaMayaTypeWrapper and isinstance(attr, cls) :
                        print "herited constant found: %s" % name
                        if not name in constant :
                            constant[name] = newcls(attr)
            print "api class", apiClass
            print "apiDict", apiDict
            print "constant", constant
            
            # build the protected list to make some class ifo and the constants read only class attributes
            protected = tuple(['apiclass', 'apisize', 'apidim', 'apicomp', '_protected'] + constant.keys())
            # store constants as class atributes
            for name, attr in constant.iteritems() :
                type.__setattr__(newcls, name, attr)
            # store protect class read only information                            
            type.__setattr__(newcls, '_protected', protected)          
        else :
            raise TypeError, "no Maya API class specified to wrap"
        
        return newcls

# TODO : how do we want support for n-sized vectors ? Kept the code generic in case we want to share some of it
# Derive a 3 components Vector using api from a generic VectorN using generic methods ?
                 
class Vector(object):
    """ A 3 dimensional vector class that wraps Maya's api MVector class,
        >>> v = self.__class__(1, 2, 3)
        >>> w = self.__class__(x=1, z=2)
        >>> z = self.__class__(api.Mself.__class__.xAxis, z=1)
        """
    __metaclass__ = MetaMayaTypeWrapper
    # class specific info
    apiclass = api.MVector
    apisize = 3
    apidim = 1
    apicomp = ('x', 'y', 'z')
         
    # class methods and properties
    @property
    def vector(self):
        return self._data    
    @property
    def point(self):
        return api.MPoint(self._data)
    @property
    def color(self):
        return api.MColor(self._data[0], self._data[1], self._data[2])
            
    def __init__(self, *args, **kwargs):
        """ Init a Vector instance
            Can pass one argument being another Vector instance , or the vector components """
        if args :
            nbargs = len(args)
            self._data = None
            if nbargs==1 and not isScalar(args[0]) :
                # single argument
                if type(args[0]) == type(self) :
                    # copy constructor
                    self.data = args[0].data
                elif isinstance(args[0], self.__class__) :
                    # a compatible wrapped type
                    self.data = args[0].vector
                elif hasattr(args[0],'__iter__') :
                    # iterable : iterate on elements
                    self.__init__(*args[0], **kwargs)
                else :
                    # else see if we can init the api class directly
                    self.data = args[0]
                    try :
                        self.data = args[0]
                    except :
                        raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (clsname(self), clsname(args[0]), clsname(self))
            else :
                if nbargs == self.__class__.apisize :
                    l = args
                else :
                    l = list(self.__class__())
                    for i in xrange(min(nbargs, len(l))) :
                        l[i] = args[i]
                try :
                    self._data = self.api(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                    raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (clsname(self), msg, clsname(self))
        else :
            try :
                self._data = self.api()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (clsname(self), clsname(self))

        if self._data is not None :  
            # can also use the form <componentname>=<number>
            l = list(self)                     # current
            try :
                for i in xrange(self.__class__.apisize) :
                    l[i] = kwargs.get(self.__class__.apicomp[i], l[i])
                self._data = self.apiclass(*l)
            except :
                msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (clsname(self), msg, clsname(self))
            
    # display      
    def __str__(self):
        return '(%s)' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'(%s)' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))          

    # wrap of list-like access methods
    def __len__(self):
        """ Vector class has a fixed length """
        return self.__class__.apisize
    # API get, actually not faster than pulling _data[i] for such a short structure
#    def get(self):
#        ms = api.MScriptUtil()
#        ms.createFromDouble ( 0.0, 0.0, 0.0 )
#        p = ms.asDoublePtr ()
#        self._data.get(p)
#        result = [ms.getDoubleArrayItem ( p, i ) for i in xrange(self.__class__.apisize)]   
    def __getitem__(self, i):
        """ Get component i value from self """
        if i < 0 :
            i = self.__class__.apisize + i
        if i<self.__class__.apisize and not i<0 :
            return self._data[i]
        else :
            raise KeyError, "%r has no item %s" % (self, i)
    def __setitem__(self, i, a):
        """ Set component i value on self """
        l = list(self)
        l[i] = a
        self._data = self.api(*l)
    def __iter__(self):
        """ Iterate on the api components """
        for i in xrange(self.__class__.apisize) :
            yield self._data[i]
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        for i in xrange(self.__class__.apisize) :
            if self._data[i] == value :
                return True
        return False
    def __getslice__(self, i, j):
        try:
            return list(self).__getslice__(i,j)
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.name, self.__class__.apisize)    
    def __setslice__(self, i, j, s):
        try:
            l = list(self)
            l.__setslice__(i,j, list(s))
            # self._data = self.__class__(*l)._data is short/safer but slower, and all Vector derived class
            # have an api class that supports setting that way
            self._data = self.api(*l[:self.__class__.apisize])
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.__name__, self.__class__.apisize)      
    
    # common operators
    def __neg__(self):
        """ u.__neg__() <==> -u
            Returns the Vector obtained by inverting every component of u """        
        return self.__class__(map(lambda x: -x, self))   
    def __invert__(self):
        """ u.__invert__() <==> ~u
            unary inversion, returns 1 - u for Vectors """        
        return self.__class__(map(lambda x: 1.0-x, self))      
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to Vector,
            adds v to every component of u if v is a scalar """        
        if isinstance(other, Vector) :
            # return self.__class__(map( lambda x, y: x+y, self[:Vector.apisize], other[:Vector.apisize]))
            # return self.__class__(self.data.__add__(other.vector))
            return difmap(operator.add, self, other)
        elif isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to Vector,
            adds v to every component of u if v is a scalar """        
        if isinstance(other, Vector) :
            # return self.__class__(map( lambda x, y: x+y, self[:Vector.apisize], other[:Vector.apisize]))
            # return self.__class__(self.data.__add__(other.vector))
            return difmap(operator.add, other, self)
        elif isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        self._data = (self.__add__(other)).data
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a Vector instance,
            substract v to every component of u if v is a scalar """        
        if isinstance(other, Vector) :
            # difference of two points is a vector, of a vector and a point is a point
            if len(other) > len(self) :
                # other is a Point or Color
                return other.__class__(self.data.__sub__(other.vector))
            else :
                return self.__class__(self.data.__sub__(other.data))                     
        elif isScalar(other) :
            return self.__class__(map( lambda x: x-other, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a Vector instance,
            replace every component c of u by v-c if v is a scalar """        
        if isinstance(other, Vector) :
            # difference of two points is a vector, of a vector and a point is a point
            if len(other) > len(self) :
                # other is a Point or Color
                return other.__class__(other.data.__sub__(self.data))
            else :
                return self.__class__(other.data.__sub__(self.data))                     
        elif isScalar(other) :
            return self.__class__(map( lambda x: other-x, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (clsname(other), clsname(self))    
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        self._data = (self.__sub__(other)).data        
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the element wise division of each component of u by the
            corresponding component of v if both are convertible to Vector,
            divide every component of u by v if v is a scalar """  
        if hasattr(other, '__iter__') :
            lm = min(len(other), len(self))
            l = map(lambda x, y: x/y, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        elif isScalar(other) :
            return self.__class__(map(lambda x: x/other, self))
        else :
            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(self), clsname(other))  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to Vector,
            invert every component of u and multiply it by v if v is a scalar """
        if hasattr(other, '__iter__') :
            lm = min(len(other), len(self))
            l = map(lambda x, y: y/x, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        elif isScalar(other) :
            return self.__class__(map(lambda x: other/x, self))
        else :
            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """        
        self._data = (self.__div__(other)).data
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v """
        if isinstance(other, self.__class__) :
            return bool( self.data.__eq__(self.__class__(other).data))
        else :
            try :
                return self.__eq__(self.__class__(other))
            except :
                return False              
    # action depends on second object type
    # TODO : do we really want to map dot product here as api does, overriding possibility for element wise mult ?
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
            to the transformation of u by matrix v when v is an instance of Matrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, self.__class__) :
            # dot product in case of a vector
            return self.data.__mul__(other.data)
        elif isinstance(other, Matrix) :
            # Matrix transformation
            return self.__class__(self.data.__mul__(other.matrix))
        elif isScalar(other) :
            # multiply all components by a scalar
            return self.__class__(map(lambda x: x*other, self))
        elif isSequence(other) :
            # element wise multiplication by a list or tuple
            lm = min(len(other), len(self))
            l = map(lambda x, y: x*y, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        else :
            raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix, in that case this operation
            is not defined """ 
        # not possible with a Matrix
        if isinstance(other, self.__class__) or isScalar(other) or isSequence(other) : 
            # in these cases it's commutative         
            return self.__mul__(other)
        elif isinstance (other, Matrix) :
            # left side Matrix
            try :
                m = Matrix(other)
            except :
                return self.__mul__(other)
        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for Vector * Matrix multiplication, in place transformation of u by Matrix v
            or Vector by scalar multiplication only """
        if isinstance(other, Matrix) :
            self._data = self.data.__mul__(other.matrix)
        elif isScalar(other) :
            self._data = self.__class__(map(lambda x: x.__mul__(other), self)).data
        else :
            self._data = self.__mul__(Matrix(other)).data             
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two vectors,
            if v is a Matrix, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, Vector) :
            return self.__class__(self.vector.__xor__(other.vector))   
        elif isinstance(other, Matrix) :
            return self.__class__(self.vector.transformAsNormal(other.matrix))
        else :
            raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (clsname(self), clsname(other))
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """        
        self._data = self.__xor__(other).data 
        
    # wrap of API MVector methods    
    def isEquivalent(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
        try :
            return bool(self._data.isEquivalent(Vector(other)._data, tol))
        except :
            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol) 
    def isParallel(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as Vector are parallel within the specified tolerance """
        try :
            return bool(self._data.isParallel(Vector(other)._data, tol))
        except :
            raise TypeError, "%r is not convertible to a Vector, or tolerance %r is not convertible to a number, check help(Vector)" % (other, tol) 
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
        """  Returns the angle in radians between both arguments considered as Vector """
        if isinstance(other, Vector) :
            return self.vector.angle(other.vector)
        else :
            raise TypeError, "%r is not convertible to a Vector, check help(Vector)" % other 
    def rotateTo(self, other):
        """ Returns the Quaternion that represents the rotation of this Vector into the other
            argument considered as Vector about their mutually perpendicular axis """
        if isinstance(other, Vector) :
            return Quaternion(self.vector.rotateTo(other.vector))
        else :
            raise TypeError, "%r is not a Vector instance" % other
    # TODO 
    def rotateBy(self, *args):
        pass    
    def transformAsNormal(self, matrix):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, Matrix) :
            return self.__class__(self.vector.transformAsNormal(other.matrix))
        else :
            raise TypeError, "%r is not a Matrix instance" % matrix
    # additional methods
    def dot(self, other):
        if isinstance(other, Vector) :
            lm = min(len(self), len(other))
            return reduce(operator.add, map(operator.mul, self[:lm], other[:lm]), 0.0)
        else :
            raise TypeError, "%s is not a Vector instance" % other        
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, Vector) :
            return self.__class__(self.vector.__xor__(other.vector))  
        else :
            raise TypeError, "%r is not a Vector instance" % other                 
    def sqLength(self):
        """ Squared length of vector """
        return self.vector*self.vector
    def sum(self):
        """ Returns the sum of the components of self """
        return reduce(lambda x, y: x+y, self, 0) 
    def axis(self, other, normalize=False):
        """ Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, Vector) :
            if normalize :
                return (self ^ other).normal()
            else :
                return self ^ other
        else :
            raise TypeError, "%r is not a Vector instance" % other                  
    def basis(self, other, normalize=False): 
        """ Returns the basis Matrix built using u, v and u^v as coordinate axis,
            The u, v, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
                n = u ^ v
                v = n ^ u
            if the normalize keyword argument is set to True, the vectors are also normalized """
        if isinstance(other, Vector) :
            if normalize :
                u = self.normal()
                n = u ^ other.normal()
                v = n ^ u
            else :
                u = self
                n = u ^ other
                v = n ^ u
            return Matrix(u, v, n, mode='basis')
        else :
            raise TypeError, "%r is not a Vector instance" % other
    def cotan(self, other):
        """ cotangent of the (self, other) angle """
        if isinstance(other, Vector) :
            return (self*self-other*self)/(self^other).length();
        else :
            raise TypeError, "%r is not a Vector instance" % other    
    def blend(self, other, blend=0.5):
        """ u.blend(v, blend) returns the result of blending from Vector instance u to v according to
            either a scalar blend where it yields u*(1-blend) + v*blend Vector,
            or a an iterable of up to 3 (x, y, z) independant blend factors """ 
        if isinstance(other, Vector) :
            other = Vector(other)
            if isScalar(blend) :
                l = (self*(1-blend) + other*blend)[:len(other)] + self[len(other):len(self)]
                return self.__class__(*l)            
            elif hasattr(blend, '__iter__') : 
                bl = list(blend)
                lm = min(len(bl), len(self), len(other))
                l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
                return self.__class__(*l)

            else :
                raise TypeError, "blend can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % clsname(blend)
        else :
            raise TypeError, "%s is not convertible to a %s, check help(%s)" % (clsname(other), clsname(self), clsname(self))          
    def clamp(self, low=0.0, high=1.0):
        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
            or the corresponding components of low and high if low and high are sequences of scalars """
        ln = len(self)
        if isScalar(low) :
            low = [low]*ln
        elif hasattr(low, '__iter__') : 
            low = list(low)[:ln]
        else :
            raise TypeError, "'low' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % clsname(blend) 
        if isScalar(high) :
            high = [high]*ln
        elif hasattr(high, '__iter__') : 
            high = list(high)[:ln]
        else :
            raise TypeError, "'high' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % clsname(blend)         
        lm = min(ln, len(low), len(high))             
        return self.__class__(map(clamp, self, low, high))
        
class Point(Vector):
    apiclass = api.MPoint
    apisize = 4
    apidim = 1
    apicomp = ('x', 'y', 'z', 'w')

    # class methods and properties    
    @property
    def vector(self):
        return api.MVector(self._data)
    @property
    def point(self):
        return self._data
    @property
    def color(self):
        return api.MColor(self._data[0], self._data[1], self._data[2], self._data[3])   

    # base methods are inherited from Vector
    # API get, actually not faster than pulling _data[i] for such a short structure
#    def get(self):
#        ms = api.MScriptUtil()
#        ms.createFromDouble ( 0.0, 0.0, 0.0, 0.0 )
#        p = ms.asDoublePtr ()
#        self._data.get(p)
#        result = [ms.getDoubleArrayItem ( p, i ) for i in xrange(self.__class__.apisize)] 
    
    # modified operators
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a Vector instance,
            substract v to every component of u if v is a scalar.
            The substraction of two Points yields a Vector, of a Point and a Vector yields a Point """        
        if isinstance(other, Vector) :
            # difference of two points is a vector, of a vector and a point is a point
            if type(other) is Point :
                return Vector(self.point.__sub__(other.point))
            else :
                return self.__class__(self.data.__sub__(other.data))                     
        elif isScalar(other) :
            return self.__class__(map( lambda x: x-other, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a Vector instance,
            replace every component c of u by v-c if v is a scalar """        
        if isinstance(other, Vector) :
            # difference of two points is a vector, of a vector and a point is a point
            if type(other) is Point :
                # other is a Point or Color
                return Vector(other.data.__sub__(self.data))
            else :
                return self.__class__(other.data.__sub__(self.data))                     
        elif isScalar(other) :
            return self.__class__(map( lambda x: other-x, self))
        else :            
            raise TypeError, "unsupported operand type(s) for -: '%s' and '%s'" % (clsname(other), clsname(self))    
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
        """ Return the distance between this Point and the Point passed as an argument """
        if isinstance(other, self.__class__) :
            return self.point.distanceTo (self.__class__(other)._data)
        else :
            raise TypeError, "%s is not a %s instance" % (other, clsname(self))            
    def isEquivalent (other, tol = api.MPoint_kTol) :
        """ p.isEquivalent(q, tol) = True if p and q are equivalent in the given tolerance """ 
        try :
            return bool(self.data.isEquivalent(self.__class__(other)._data, tol))
        except :
            raise TypeError, "%s is not convertible to a %s, or tolerance %s is not convertible to a number, check help(%s)" % (other, clsname(self), tol, clsname(self)) 
    def cotan(self, q, r) :
        """ p.cotan(q, r ) = cotangent of the (q-p, r-p) angle """
        if isinstance(q, self.__class__) and isinstance(q, self.__class__) :
            return ((r - q)*(self - b))/((r - q)^(self - b)).length();
        else :
            raise TypeError, "%s or %s is not a %s instance" % (q, r, clsname(self))       
    # TODO
    def planar(self, *args, **kwargs): 
        """ p.planar(q, r, s (...), tol=tolerance) returns True if all provided points are planar within given tolerance """
        # tol = kwargs.get('tol', api.MPoint_kTol)
        pass
    def center(self, *args): 
        """ p.center(q, r, s (...)) returns the Point that is the barycenter of p, q, r, s (...) """
        pass
    def bWeights(self, *args): 
        """ p.barycenter(p0, p1, (...), pn) returns barycentric weights so that  """
        pass                
    
class Color(Point):
    apiclass = api.MColor
    apisize = 4
    apidim = 1
    apicomp = ('r', 'g', 'b', 'a')
    
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
        """ returns the tuple of the r, g, b Color components """
        return tuple(self[:3])
    @property
    def hsv(self):
        """ returns the tuple of the h, s, v Color components """
        return self.__class__.rgbtohsv(self[:3])
    @property
    def h(self):
        """ returns the tuple of the h, s, v Color components """
        return self.__class__.rgbtohsv(self[:3])[0]
    @property
    def s(self):
        """ returns the tuple of the h, s, v Color components """
        return self.__class__.rgbtohsv(self[:3])[1]
    @property
    def v(self):
        """ returns the tuple of the h, s, v Color components """
        return self.__class__.rgbtohsv(self[:3])[2]
                            
    def __init__(self, *args, **kwargs):
        """ Init a Color instance
            Can pass one argument being another Color instance , or the color components """
         
        mode = kwargs.get('mode', None)
        # can also use the form <componentname>=<number>
        # for now supports only rgb and hsv flags
        hsvflag = (kwargs.get('h', None), kwargs.get('s', None), kwargs.get('v', None))
        rgbflag = (kwargs.get('r', None), kwargs.get('g', None), kwargs.get('b', None))
        noflag = (None, None, None)
        # can't mix them
        if hsvflag != noflag and rgbflag != noflag :
            raise ValueError, "Can not mix r,g,b and h,s,v keyword arguments in %s" % clsname(self)
        # if no mode specified, guess from what keyword arguments where used, else use 'rgb' as default
        if mode is None :
            if hsvflag != noflag :
                mode = 'hsv'
            else :
                mode = 'rgb'
        # can't specify a mode and use keywords of other modes
        if mode is not 'hsv' and hsvflag != noflag:
            raise ValueError, "Can not use h,s,v keyword arguments while specifying %s mode in %s" % (mode, clsname(self))
        elif mode is not 'rgb' and rgbflag != noflag:
            raise ValueError, "Can not use r,g,b keyword arguments while specifying %s mode in %s" % (mode, clsname(self))
        # mode int used by api class        
        try :
            modeInt = list(self.__class__.modes()).index(mode)
        except :
            raise KeyError, "%s has no mode %s" % (clsname(self), m)
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
                raise ValueError, "quantize must be a numeric value, not %s" % (clsname(quantize))   
        # removed all catching to get direct api errors until api MColor has evolved a bit more
        if args :
            nbargs = len(args)
            self._data = None
            # TODO : differentiate between Color(1) that takes 1 for alpha (so is api) and Color([1]) ?
            if nbargs==1 :
                # single argument
                if isinstance(args[0], self.__class__) :
                    # copy constructor
                    self._data = args[0].color
                elif hasattr(args[0],'__iter__') :
                    # iterable, try to init on elements, will catch Vector and Point as well
                    self.__init__(*args[0], **kwargs)
                elif isScalar(args[0]) :
                    c = float(args[0])
                    if quantize :
                        c /= quantize
                    self._data = self.api(c)
                else :
                    # else see if we can init the api class directly (an api.MColor or single alpha value)
                    try :
                        self._data = self.api(args[0])
                    except :
                        raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (clsname(self), clsname(args[0]), clsname(self))                                                
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
                    self._data = self.api(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                    raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (clsname(self), msg, clsname(self))
        else :
            try:
                self._data = self.api()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (clsname(self), clsname(self))
            
        if self._data is not None :             
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
                    self._data = self.api(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (clsname(self), msg, clsname(self))
            
    # overriden operators
    # action depends on second object type
    # TODO : would be nice to define LUT classes and allow Color * LUT transform
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to element wise multiplication product when both objects are Color,
            to the transformation of u by matrix v when v is an instance of Matrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, Vector) :
            # element wise mult in case of Colors
            return self.__class__(map(lambda x,y:x*y, self, Color(other)))
        elif isinstance(other, Matrix) :
            # Matrix transformation, do we need that ?
            return self.__class__(self.data.__mul__(other.matrix))
        elif isScalar(other) :
            # multiply all components by a scalar
            return self.__class__(map(lambda x: x*other, self))
        elif isSequence(other) :
            # element wise multiplication by a list or tuple
            lm = min(len(other), len(self))
            l = map(lambda x, y: x*y, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        else :
            raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix, in that case this operation
            is not defined """ 
        # not possible with a Matrix
        if isinstance(other, Vector) or isScalar(other) or isSequence(other) : 
            # in these cases it's commutative         
            return self.__mul__(other)
        elif isinstance (other, Matrix) :
            # left side Matrix
            try :
                m = Matrix(other)
            except :
                return self.__mul__(other)
        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Assgin to u the result of u.__mul__(v), see Color.__mul__ """
        self._data = self.__mul__(other).data
             
    # additionnal methods, to be extended
    def over(self, other):
        """ c1.over(c2): Composites c1 over other c2 using c1's alpha, the resulting color has the alpha of c2 """
        if isinstance(other, Vector) :
            return self.__class__(Vector(self)*self.a + Color(other))               
        else :
            raise TypeError, "%s is not convertible to a Color, check help(%s)" % (clsname(other), clsname(self))
    # return Vector instead ? Keeping alpha doesn't make much sense
    def premult(self):
        """ Premultiply Color r, g and b by it's alpha and resets alpha to 1.0 """
        return self.__class__(Vector(self)*self.a)               
    def blend(self, other, blend):
        """ c1.blend(c2, b) blends from color c1 to c2 according to
            either a scalar b where it yields c1*(1-b) + c2*b color,
            or a an iterable of up to 4 (r, g, b, a) independant blend factors """ 
        if isinstance(other, Vector) :
            # len(other) <= len(self)            
            if isScalar(blend) :
                lm = len(other)
                l = map(lambda x,y:(1-blend)*x+blend*y, self[:lm], other) + self[lm:len(self)]
                return self.__class__(*l)            
            elif hasattr(blend, '__iter__') : 
                bl = list(blend)
                lm = min(len(bl), len(self), len(other))
                l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
                return self.__class__(*l)

            else :
                raise TypeError, "blend can only be a Vector or a scalar, not a %s" % clsname(blend)
        else :
            raise TypeError, "%s is not convertible to a Color, check help(%s)" % (clsname(other), clsname(self))            
    def gamma(self, gamma):
        """ c.gamma(g) applies gamma correction g to Color c, g can be a scalar and then will be applied to r, g, b
            or an iterable of up to 4 (r, g, b, a) independant gamma correction values """             
        if hasattr(gamma, '__iter__') : 
            gamma = list(gamma)
            lm = min(len(gamma), len(self))
            l = map(lambda x,y:x**(1/y), self[:lm], gamma[:lm]) + self[lm:len(self)]
            return self.__class__(*l)
        elif isScalar(gamma) :
            l = map(lambda x:x**(1/gamma), self[:Vector.apiSize]) + self[Vector.apiSize:len(self)]
            return self.__class__(*l)
        else :
            raise TypeError, "gamma can only be a Vector or a scalar, not a %s" % clsname(gamma)
  
   
    

        
class Matrix(object):
    """ A 4x4 transformation matrix based on api MMatrix 
        >>> v = self.__class__(1, 2, 3)
        >>> w = self.__class__(x=1, z=2)
        >>> z = self.__class__(api.Mself.__class__.xAxis, z=1)
        """    
    apiclass = api.MMatrix
    apisize = 16
    apidim = (4, 4)  

    # TODO a00, a01, etc properties ?  
    # class methods
    
    @property
    def matrix(self):
        return self._data
    @property
    def transform(self):
        return api.MTransformationMatrix(self._data)   
    @property
    def quaternion(self):
        return self.tranform.rotation()
    @property
    def euler(self):
        return self.tranform.eulerRotation()
            
    def __init__(self, *args, **kwargs):
        """ Init a Matrix instance
            Can pass one argument being another Matrix instance , or the Matrix components """
        self._data = None
        if args :
            nbargs = len(args)
            if nbargs==1 and not isScalar(arg[0]):
                # single argument
                if type(args[0]) == type(self) :
                    # copy constructor
                    self.data = args[0].data                
                elif isinstance(args[0], self.__class__) :
                    # derived class, copy and convert to self data
                    self.data = args[0].matrix()
                elif not hasattr(args[0],'__iter__') :
                    # else see if we can init the api class directly
                    try :
                        self.data = args[0]
                    except :
                        raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (clsname(self), clsname(args[0]), clsname(self))
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
                    if nbargs == self.__class__.apisize :
                        l = args
                    else :
                        l = list(self.__class__())
                        for i in xrange(min(nbargs, len(l))) :
                            l[i] = args[i]
                    try :
                        self._data = self.api(*l)
                    except :
                        msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                        raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (clsname(self), clsname(self))

        else :
            # default init
            try :
                self._data = self.api()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (clsname(self), clsname(self))
               

        if self._data is not None :  
            # can also use the form <componentname>=<number>
            l = list(self)                     # current
            try :
                for i in xrange(self.__class__.apisize) :
                    l[i] = kwargs.get(self.__class__.apicomp[i], l[i])
                self._data = self.apiclass(*l)
            except :
                msg = ", ".join(map(lambda x,y:x+"=<"+clsname(y)+">", self.__class__.apicomp, l))
                raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (clsname(self), msg, clsname(self))


             
    # display      
    def __str__(self):
        return '(%s)' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'(%s)' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))          

    # wrap of list-like access methods
    def __len__(self):
        """ Matrix class has a fixed length """
        return self.__class__.apisize
    def __getitem__(self, i, j):
        """ Get component i value from self """
#        if i < 0 :
#            i = self.__class__.apisize + i
#        if i<self.__class__.apisize and not i<0 :
#            return self._data[i]
        if True :
            print i, j
        else :
            raise KeyError, "%r has no item %s" % (self, i)
    def __setitem__(self, i, j, a):
        """ Set component i value on self """
        pass
#        l = list(self)
#        l[i] = a
#        self._data = self.__class__(*l)._data
    def __iter__(self):
        """ Iterate on the Matrix components """
        for i in xrange(self.__class__.apidim[0]) :
            for j in xrange(self.__class__.apidim[1]) :            
                yield self[i][j]
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        for i in xrange(self.__class__.apidim[0]) :
            for j in xrange(self.__class__.apidim[1]) :  
                if self[i][j] == value :
                    return True
        return False
    def __getslice__(self, i, j):
        try:
            return self.__class__(list(self).__getslice__(i,j))
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.name, self.__class__.apisize)    
    def __setslice__(self, i, j, l):
        try:
            self._data = self.__class__(list(self).__setslice__(i,j, list(l)))._data
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.name, self.__class__.apisize)      
    
#    # common operators
#    def __neg__(self):
#        """ u.__neg__() <==> -u
#            Returns the Vector obtained by inverting every component of u """        
#        return self.__class__(map(lambda x: -x, self))    
#    def __add__(self, other) :
#        """ u.__add__(v) <==> u+v
#            Returns the result of the addition of u and v if v is convertible to Vector,
#            adds v to every component of u if v is a scalar """        
#        if isinstance(other, Vector) :
#            return self.__class__(map( lambda x, y: x+y, self, other))      
#        elif isScalar(other) :
#            return self.__class__(map( lambda x: x+other, self))
#        else :            
#            try :
#                return self.__add__(self.__class__(other))
#            except :
#                pass
#        raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (clsname(self), clsname(other))    
#    def __iadd__(self, other):
#        """ u.__iadd__(v) <==> u *= v
#            In place addition of u and v, see __add__ """
#        self._data = (self.__add__(other))._data
#    def __div__(self, other):
#        """ u.__div__(v) <==> u/v
#            Returns the result of the element wise division of each component of u by the
#            corresponding component of v if both are convertible to Vector,
#            divide every component of u by v if v is a scalar """  
#        if isinstance(other, Vector) :
#            return self.__class__(map( lambda x, y: x/y, self, other))
#        elif isScalar(other) :
#            return self.__class__(self.__class__.apiclass.__div__(self._data,other))
#        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(self), clsname(other))  
#    def __rdiv__(self, other):
#        """ u.__rdiv__(v) <==> v/u
#            Returns the result of the element wise division of each component of v by the
#            corresponding component of u if both are convertible to Vector,
#            invert every component of u and multiply it by v if v is a scalar """
#        if isinstance(other, Vector) :
#            return other.__class__(map( lambda x, y: x/y, self, other))
#        elif isScalar(other) :
#            return self.__class__(map( lambda y: other/y, self))
#        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(other), clsname(self))  
#    def __idiv__(self, other):
#        """ u.__idiv__(v) <==> u /= v
#            In place division of u by v, see __div__ """        
#        self._data = (self.__div__(other))._data
#    def __eq__(self, other):
#        """ u.__eq__(v) <==> u == v """
#        if isinstance(other, self.__class__) :
#            try :
#                if self.__class__(self.__class__.apiclass.__eq__(self._data, self.__class__(other)._data)) :
#                    return True
#            except :
#                pass
#        else :
#            try :
#                return self.__eq__(self.__class__(other))
#            except :
#                pass
#        return False              
#    # action depends on second object type
#    def __mul__(self, other) :
#        """ u.__mul__(v) <==> u*v
#            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
#            to the transformation of u by matrix v when v is an instance of Matrix,
#            and to element wise multiplication when v is a scalar """
#        if self.__class__ == other.__class__ :
#            return self.__class__(self.__class__.apiclass.__mul__(self._data, other._data))
#        elif other.__class__ == Matrix :
#            return self.__class__(self.__class__.apiclass.__mul__(self._data, other._data))
#        elif isScalar(other) :
#            return self.__class__(map(lambda x: x.__mul__(other), self))
#        else :
#            # try to convert
#            try :
#                return self.__mul__(self.__class__(other))
#            except :
#                pass
#            try :
#                return self.__mul__(Matrix(other))
#            except :
#                pass
#        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(self), clsname(other))    
#    def __rmul__(self, other):
#        """ u.__rmul__(v) <==> v*u
#            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix, in that case this operation
#            is not defined """ 
#        # not possible with a Matrix
#        if isinstance(other, self.__class__) or isScalar(other) :          
#            return self.__mul__(other)
#        else :
#            try :
#                m = Matrix(other)
#            except :
#                return self.__mul__(other)
#        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(other), clsname(self))  
#    def __imul__(self, other):
#        """ u.__imul__(v) <==> u *= v
#            Valid for Vector * Matrix multiplication, in place transformation of u by Matrix v
#            or Vector by scalar multiplication only """
#        if other.__class__ == Matrix :
#            self._data = self.__class__.apiclass.__mul__(self._data, other._data)
#        elif isScalar(other) :
#            self._data = self.__class__(map(lambda x: x.__mul__(other), self))._data
#        else :
#            self._data = self.__mul__(Matrix(other))._data             
#    # special operators
#    def __xor__(self, other):
#        """ u.__xor__(v) <==> u^v
#            Defines the cross product operator between two vectors,
#            if v is a Matrix, u^v is equivalent to u.transformAsNormal(v) """
#        if self.__class__ == other.__class__ :
#            return self.__class__(self.__class__.apiclass.__xor__(self._data, other._data))        
#        else :
#            try :
#                return self.__xor__(self.__class__(other))
#            except :
#                pass
#            try :
#                return self.transformAsNormal(Matrix(other))
#            except :
#                pass            
#        raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (clsname(self), clsname(other))
#    def __ixor__(self, other):
#        """ u.__xor__(v) <==> u^=v
#            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """        
#        self._data = self.__ixor__(other)._data 
#        

#    def isEquivalent(self, other, tol=api.MVector_kTol):
#        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
#        try :
#            return self._data.isEquivalent(Vector(other)._data, tol)
#        except :
#            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol) 
#    def isParallel(self, other, tol=api.MVector_kTol):
#        """ Returns true if both arguments considered as Vector are parallel within the specified tolerance """
#        try :
#            return self._data.isParallel(Vector(other)._data, tol)
#        except :
#            raise TypeError, "%s is not convertible to a Vector, or tolerance %s is not convertible to a number, check help(Vector)" % (other, tol) 
#    def length(self):
#        """ Length of self """
#        return self._data.length()      
#    def normal(self): 
#        """ Return a normalized copy of self """ 
#        return self._data.normal()
#    def normalize(self):
#        """ Performs an in place normalization of self """
#        self._data.normalize()
#    def angle(self, other):
#        """  Returns the angle in radians between both arguments considered as Vector """
#        try :
#            return self._data.angle(Vector(other)._data)
#        except :
#            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other 
#    def rotateTo(self, other):
#        """ Returns the Quaternion that represents the rotation of this Vector into the other
#            argument considered as Vector about their mutually perpendicular axis """
#        try :
#            return Quaternion(self._data.rotateTo(Vector(other)._data))
#        except :
#            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other
#    # TODO 
#    def rotateBy(self, *args):
#        pass    
#    def transformAsNormal(self, matrix):
#        """ Returns the vector transformed by the matrix as a normal
#            Normal vectors are not transformed in the same way as position vectors or points.
#            If this vector is treated as a normal vector then it needs to be transformed by
#            post multiplying it by the inverse transpose of the transformation matrix.
#            This method will apply the proper transformation to the vector as if it were a normal. """
#        try :
#            return self.__class__(self._data.transformAsNormal(Matrix(matrix)._data))
#        except :
#            raise TypeError, "%s is not convertible to a Matrix, check help(Matrix)" % matrix
#    # additional methods
#    def sqLength(self):
#        """ Squared length of vector """
#        return self.__mul__(self)
#    def sum(self):
#        """ Returns the sum of the components of self """
#        return reduce(lambda x, y: x+y, self, 0) 
#    def axis(self, v, normalize=False):
#        """ Returns the axis of rotation from u to v as the vector n = u ^ v
#            if the normalize keyword argument is set to True, n is also normalized """
#        if normalize :
#            return (self ^ Vector(v)).normal()
#        else :
#            return self ^ Vector(v)        
#    def basis(self, v, normalize=False): 
#        """ Returns the basis Matrix built using u, v and u^v as coordinate axis,
#            The u, v, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
#                n = u ^ v
#                v = n ^ u
#            if the normalize keyword argument is set to True, the vectors are also normalized """
#        if normalize :
#            u = Vector(self).normal()
#            n = u ^ Vector(v).normal()
#            v = n ^ u
#        else :
#            u = Vector(self)
#            n = u ^ Vector(v)
#            v = n ^ u
#        return Matrix(u, v, n)  
# MMatrix api wrap

#class mmatrix:
#    def __init__(self, cols=[], omMatrix=None):
#        """ inititalize with list of column vals, or an OpenMaya.MMatrix """
#        if omMatrix:
#            self._mat = omMatrix
#        else:
#            self._mat = api.MMatrix()
#            for i,col in enumerate(cols):
#                self.__setcolumn(i, col)
#
#    def __setcolumn(self, c, vals):
#        """ helper to set a column at once """
#        ptr = om.MMatrix.__getitem__(self._mat,c)
#        for i,val in enumerate(vals):
#            om.MScriptUtil.setDoubleArray(ptr, i, val)
#    
#    def __setitem__(self, rc, value):
#        """ set cell value in (r,c) to value """
#        r,c = rc
#        om.MScriptUtil.setDoubleArray(om.MMatrix.__getitem__(self._mat,r), c, value)
#    
#    def __getitem__(self, rc):
#        """ get coll value from (r,c) """
#        r,c = rc
#        return om.MScriptUtil.getDoubleArrayItem( om.MMatrix.__getitem__(self._mat,r), c )
#
#    def __str__(self):
#        return '\n'.join( [' '.join( [ str(self[(x,y)]) for x in range(4)]) for y in range(4)] )
#
#    def transpose(self):
#        newMatrix = mmatrix()
#        newmat = self._mat.transpose()
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def adjoint(self):
#        newMatrix = mmatrix()
#        newmat = self._mat.adjoint()
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def homogenize(self):
#        newMatrix = mmatrix()
#        newmat = self._mat.homogenize()
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def __add__(self, other):
#        newMatrix = mmatrix()
#        newmat = self._mat + other._mat
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def __sub__(self,other):
#        newMatrix = mmatrix()
#        newmat = self._mat - other._mat
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def __mul__(self, other):
#        if isinstance(other, om.MVector):
#            # vector result
#            return self._math * other
#        newMatrix = mmatrix()
#        newmat = self._mat * other._mat
#        newMatrix._mat = newmat
#        return newMatrix
#
#    def __iadd__(self,other):
#        self._mat += other._mat
#        return self
#        
#    def __isub__(self,other):
#        self._mat += other._mat
#        return self
#
#    def __imul__(self,other):
#        self._mat += other._mat
#        return self
#
#    def __eq__(self,other):
#        return self._mat == other._mat
#    
#  MMatrix      transpose () const
#MMatrix &     setToIdentity ()
#MMatrix &     setToProduct ( const MMatrix & left, const MMatrix & right )
#MMatrix &     operator+= ( const MMatrix & right )
#MMatrix     operator+ ( const MMatrix & right ) const
#MMatrix &     operator-= ( const MMatrix & right )
#MMatrix     operator- ( const MMatrix & right ) const
#MMatrix &     operator*= ( const MMatrix & right )
#MMatrix     operator* ( const MMatrix & right ) const
#MMatrix &     operator*= ( double )
#MMatrix     operator* ( double ) const
#bool     operator== ( const MMatrix & other ) const
#bool     operator!= ( const MMatrix & other ) const
#MMatrix     inverse () const
#MMatrix     adjoint () const
#MMatrix     homogenize () const
#double     det4x4 () const
#double     det3x3 () const
#bool     isEquivalent ( const MMatrix & other, double tolerance = MMatrix_kTol ) const
#bool     isSingular () const
#identity = mmatrix( omMatrix=om.MMatrix.identity )     
        
class Quaternion(Matrix):
    api = api.MQuaternion
    apisize = 4        

    # properties
    x = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
    y = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
    z = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) ) 
    w = property( lambda self: self.__getitem__(3) ,  lambda self, val: self.__setitem__(3,val) )  

class EulerRotation(Matrix):
    api = api.MEulerRotation
    apisize = 4   

    # properties
    x = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
    y = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
    z = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) ) 
    o = property( lambda self: self.__getitem__(3) ,  lambda self, val: self.__setitem__(3,val) )  

def _test() :
    print "Vector class", dir(Vector)
    print "Point  class", dir(Point)
    # print "Color  class", dir(Color)    
    u = Vector.xAxis
    v = Vector.yAxis
    print "u = Vector.xAxis: %r" % u
    print "v = Vector.yAxis: %r" % v
    n = u ^ v
    print "n = u ^ v: %r" % n
    print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    n[0:1] = [1, 1]
    print "n[0:1] = [1, 1] : %r" % n
    n = n*2
    print "n = n * 2 : %r" % n
    print "u * n : %s" % (u * n)
    print "Vector(): %r" % Vector()
    
    print "~u: %r" % (~u)

    p = Point.origin
    q = Point(1, 2, 3)
    print "p = Point.origin: %r" % p
    print "q = Point(1, 2, 3): %r" % q
    r = Point([1, 2, 3], y=0)
    print "r = Point([1, 2, 3], y=0): %r" % r
    v = u + p
    print "v = u + p: %r" % v
    r = q + u
    print "r = q + u: %r" % r
    
    p = Point(x=1, y=2, z=3)
    print "p = Point(x=1, y=2, z=3): %r" % p
    
    try :
        p = Point(x=1, y=2, z='a')
    except :
        pass
    
    p = Point(x=1, y=2, z=3)
    print "p = Point(x=1, y=2, z=3): %r" % p
    
    print "length of p: %s" % p.length()
    
    c1 = Color(1, 1, 1)
    print "c1 = Color(1, 1, 1): %r" % c1
    c2 = Color(255, 0, 0, quantize=255, mode='rgb')
    print "c2 = Color(255, 0, 0, quantize=255, mode='rgb'): %r" % c2
    # careful MColor takes a solo argument as an alpha
    c3 = Color(255, b=128, quantize=255, mode='rgb')
    print "c3 = Color(255, b=128, quantize=255, mode='rgb'): %r" % c3
    c4 = Color(1, 0.5, 2, 0.5)
    print "c4 = Color(1, 0.5, 2, 0.5): %r" % c4
    c5 = Color(0, 65535, 65535, quantize=65535, mode='hsv')
    print "c5 = Color(0, 65535, 65535, quantize=65535, mode='hsv'): %r" % c5
    a = Vector(c5.rgb)
    print "a = Vector(c5.rgb): %r" % a    
    b = Vector(c5.hsv)
    print "b = Vector(c5.hsv): %r" % b
    c6 = Color(b, v=0.5, mode='hsv')
    print "c6 = Color(b, v=0.5, mode='hsv'): %r" % c6
    c7 = Color(Color.blue, v=0.5)
    print "c7 = Color(Color.blue, v=0.5) as rgb:", c7.rgb    
    print "c7 = Color(Color.blue, v=0.5) as hsv:", c7.hsv 
    print "c4.clamp() : %s" % c4.clamp()
    c7 = Color(c4, v=0.5)
    print "c7 = Color(c4, v=0.5) : %r" % c7    
    print "c7 = Color(c4, v=0.5) as hsv:", c7.hsv    
    c7 = c7.gamma([2.2, 2.0, 2.3])
    print "c7 = c7.gamma([2.2, 2.0, 2.3]): %r" % c7
    c8 = Color(1, 1, 1) * 0.5
    print "c8 = Color(1, 1, 1) * 0.5: %r" % c8
    c9 = Color.red.blend(Color.blue, 0.5) 
    print "c9 = Color.red.blend(Color.blue, 0.5): %r" % c9
    c10 = c8.over(c9)
    print "c10 = c8.over(c9): %r" % c10 
    
if __name__ == '__main__' :
    _test()


    

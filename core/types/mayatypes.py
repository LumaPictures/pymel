"""
A wrap of Maya's MVector type
"""
#import pymel.util as util
#import pymel.api as api
import inspect
import maya.OpenMaya as api
from math import *
from copy import *
#from pymel.core.mathutils import *

def isScalar(obj):
    # consider only ints and floats numeric
    return isinstance(obj,int) or isinstance(obj,float)

clsname = lambda x:x.__class__.__name__

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
            # we'll need the api clas dict to automate some of the wrapping
            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
            apiDict = dict(inspect.getmembers(apiClass))            
            constant = {}
            # defining class properties on the created class                 
            for name, attr in apiDict.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apiClass) :
                    if name not in constant :
                        try :
                            constant[name] = newcls(attr)
                        except :
                            pass 
            # update the constant dict with herited constants
            mro = inspect.getmro(newcls)            
            for cls in mro :
                for name, attr in cls.__dict__.iteritems() :
                    if isinstance(attr, cls) and not name in constant :
                        try :
                            constant[name] = newcls(attr)
                        except :
                            pass 
            # buil the protected list to make some class ifo and the constants read only class attributes
            protected = tuple(['apiclass', 'apisize', 'apidim', '_protected'] + constant.keys())
            # store constants as class atributes
            for name, attr in constant.iteritems() :
                type.__setattr__(newcls, name, attr)
            # store protect class read only information                            
            type.__setattr__(newcls, '_protected', protected)
        else :
            raise TypeError, "no Maya API class specified to wrap"
        
        return newcls

# TODO : how do we want support for n-sized vectors ? Kept the code generic in case we want to share some of it
# A vector that uses Maya api when it's dimension is 3  
# note : data is always a tuple even if only of one element to allow storage for additional info, the
# first element is the one used for operations (see how Matrix wraps also MTransformationMatrix for instance)                    
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
         
    # properties for the first 3 elements
    x = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
    y = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
    z = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) )   

    # class methods
    
    def __init__(self, *args, **kwargs):
        """ Init a Vector instance
            Can pass one argument being another Vector instance , or the vector components """
        if args :
            nbargs = len(args)
            self._data = None
            if nbargs==1 :
                # single argument
                if args[0] is None :
                    self.__class__.__init__(self)
                elif type(args[0]) == type(self) :
                    # copy constructor
                    self._data = copy(args[0]._data)
                elif isinstance(args[0], self.__class__) :
                    # a compatible wrapped type
                    try :
                        self._data = (self.__class__.apiclass(args[0]._data[0]),)
                    except :
                        pass
                else :
                    # else see if we can init the api class directly
                    try :
                        self._data = (self.__class__.apiclass(args[0]),)
                    except :
                        # else iterate it and init from the elements
                        if hasattr(args[0],'__iter__') :
                            try :
                                self.__class__.__init__(self, *args[0])
                            except :
                                pass
            # if we didn't succeed yet
            if self._data is None :
                try :
                    self._data = (self.__class__.apiclass(*args),)
                except :
                    l = list(self.__class__())
                    for i in xrange(min(nbargs, len(l))) :
                        l[i] = args[i]
                    try :
                        self._data = (self.__class__.apiclass(*l),)
                        return
                    except :
                        pass
        else :
            try :
                self._data = (self.__class__.apiclass(),)
            except :
                pass
            
        if self._data is None :
            if not nbargs : 
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (clsname(self), clsname(self))
            elif nbargs == 1 :
                raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (clsname(self), clsname(args[0]), clsname(self))                            
            else :
                raise TypeError, "a %s cannot be initialized from the provided arguments, check help(%s) " % (clsname(self), clsname(self))
        else :     
            # can also use the form x=<number>, y=<number>, z=<number>
            try :
                c = kwargs.get('x', self._data[0].x)
                self._data[0].x = c
                c = kwargs.get('y', self._data[0].y)
                self._data[0].y = c
                c = kwargs.get('z', self._data[0].z)
                self._data[0].z = c
            except :
                raise TypeError, "a component of %s can only be numeric, not %s, check help(%s) " % (clsname(self), clsname(c), clsname(self))
            
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
    def __getitem__(self, i):
        """ Get component i value from self """
        if i < 0 :
            i = self.__class__.apisize + i
        if i<self.__class__.apisize and not i<0 :
            return self._data[0][i]
        else :
            raise KeyError, "%r has no item %s" % (self, i)
    def __setitem__(self, i, a):
        """ Set component i value on self """
        l = list(self.get())
        l[i] = a
        self._data = self.__class__(*l)._data
    def __iter__(self):
        """ Iterate on the vector components """
        for i in xrange(self.__class__.apisize) :
            yield self[i]
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        for i in xrange(self.__class__.apisize) :
            if self[i] == value :
                return True
        return False
    def __getslice__(self, i, j):
        try:
            return Vector(list(self).__getslice__(i,j))
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.name, self.__class__.apisize)    
    def __setslice__(self, i, j, s):
        try:
            l = list(self)
            l.__setslice__(i,j, list(s))
            self._data = self.__class__(*l)._data
        except:
            raise IndexError, "%s has only %s elements" % (self.__class__.__name__, self.__class__.apisize)      
    
    # common operators
    def __neg__(self):
        """ u.__neg__() <==> -u
            Returns the Vector obtained by inverting every component of u """        
        return self.__class__(map(lambda x: -x, self))    
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to Vector,
            adds v to every component of u if v is a scalar """        
        if isinstance(other, Vector) :
            return self.__class__(map( lambda x, y: x+y, self[:Vector.apisize], other[:Vector.apisize]))      
        elif isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))
        else :            
            try :
                return self.__add__(self.__class__(other))
            except :
                pass
        raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u *= v
            In place addition of u and v, see __add__ """
        self._data = (self.__add__(other))._data
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the element wise division of each component of u by the
            corresponding component of v if both are convertible to Vector,
            divide every component of u by v if v is a scalar """  
        if isinstance(other, Vector) :
            return self.__class__(map( lambda x, y: x/y, self, other))
        elif isScalar(other) :
            return self.__class__(self.__class__.apiclass.__div__(self._data[0],other))
        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(self), clsname(other))  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to Vector,
            invert every component of u and multiply it by v if v is a scalar """
        if isinstance(other, Vector) :
            return other.__class__(map( lambda x, y: x/y, self, other))
        elif isScalar(other) :
            return self.__class__(map( lambda y: other/y, self))
        raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """        
        self._data = (self.__div__(other))._data
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v """
        if isinstance(other, self.__class__) :
            try :
                if self.__class__(self.__class__.apiclass.__eq__(self._data[0], self.__class__(other)._data[0])) :
                    return True
            except :
                pass
        else :
            try :
                return self.__eq__(self.__class__(other))
            except :
                pass
        return False              
    # action depends on second object type
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
            to the transformation of u by matrix v when v is an instance of Matrix,
            and to element wise multiplication when v is a scalar """
        if isinstance(other, self.__class__) :
            return self.__class__.apiclass.__mul__(self._data[0], other._data[0])
        elif other.__class__ == Matrix :
            return self.__class__(self.__class__.apiclass.__mul__(self._data[0], other._data[0]))
        elif isScalar(other) :
            return self.__class__(map(lambda x: x.__mul__(other), self))
        else :
            # try to convert
            try :
                return self.__mul__(self.__class__(other))
            except :
                pass
            try :
                return self.__mul__(Matrix(other))
            except :
                pass
        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(self), clsname(other))    
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            This is equivalent to u*v thus u.__mul__(v) unless v is a Matrix, in that case this operation
            is not defined """ 
        # not possible with a Matrix
        if isinstance(other, self.__class__) or isScalar(other) :          
            return self.__mul__(other)
        else :
            try :
                m = Matrix(other)
            except :
                return self.__mul__(other)
        raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(other), clsname(self))  
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for Vector * Matrix multiplication, in place transformation of u by Matrix v
            or Vector by scalar multiplication only """
        if other.__class__ == Matrix :
            self._data = (self.__class__.apiclass.__mul__(self._data[0], other._data[0]),)
        elif isScalar(other) :
            self._data = self.__class__(map(lambda x: x.__mul__(other), self))._data
        else :
            self._data = self.__mul__(Matrix(other))._data             
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two vectors,
            if v is a Matrix, u^v is equivalent to u.transformAsNormal(v) """
        if self.__class__ == other.__class__ :
            return self.__class__(self.__class__.apiclass.__xor__(self._data[0], other._data[0]))        
        else :
            try :
                return self.__xor__(self.__class__(other))
            except :
                pass
            try :
                return self.transformAsNormal(Matrix(other))
            except :
                pass            
        raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (clsname(self), clsname(other))
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """        
        self._data = self.__ixor__(other)._data 
        
    # wrap of API MVector methods    
    def get(self):
        ms = api.MScriptUtil()
        p = ms.asDoublePtr ()
        self._data[0].get(p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.__class__.apisize)]) 
    def isEquivalent(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as Vector are equal  within the specified tolerance """
        try :
            return self._data[0].isEquivalent(Vector(other)._data[0])
        except :
            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other 
    def isParallel(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as Vector are parallel within the specified tolerance """
        try :
            return self._data[0].isParallel(Vector(other)._data[0])
        except :
            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other 
    def length(self):
        """ Length of self """
        return self._data[0].length()      
    def normal(self): 
        """ Return a normalized copy of self """ 
        return self._data[0].normal()
    def normalize(self):
        """ Performs an in place normalization of self """
        self._data[0].normalize()
    def angle(self, other):
        """  Returns the angle in radians between both arguments considered as Vector """
        try :
            return self._data[0].angle(Vector(other)._data[0])
        except :
            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other 
    def rotateTo(self, other):
        """ Returns the Quaternion that represents the rotation of this Vector into the other
            argument considered as Vector about their mutually perpendicular axis """
        try :
            return Quaternion(self._data[0].rotateTo(Vector(other)._data[0]))
        except :
            raise TypeError, "%s is not convertible to a Vector, check help(Vector)" % other
    # TODO 
    def rotateBy(self, *args):
        pass    
    def transformAsNormal(self, matrix):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        try :
            return self.__class__(self._data[0].transformAsNormal(Matrix(matrix)._data[0]))
        except :
            raise TypeError, "%s is not convertible to a Matrix, check help(Matrix)" % matrix
    # additional methods
    def sqLength(self):
        """ Squared length of vector """
        return self.__mul__(self)
    def sum(self):
        """ Returns the sum of the components of self """
        return reduce(lambda x, y: x+y, self, 0) 
    def axis(self, v, normalize=False):
        """ Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if normalize :
            return (self ^ Vector(v)).normal()
        else :
            return self ^ Vector(v)        
    def basis(self, v, normalize=False): 
        """ Returns the basis Matrix built using u, v and u^v as coordinate axis,
            The u, v, n vectors are recomputed to obtain an orthogonal coordinate system as follows:
                n = u ^ v
                v = n ^ u
            if the normalize keyword argument is set to True, the vectors are also normalized """
        if normalize :
            u = Vector(self).normal()
            n = u ^ Vector(v).normal()
            v = n ^ u
        else :
            u = Vector(self)
            n = u ^ Vector(v)
            v = n ^ u
        return Matrix(u, v, n)
                  
class Point(Vector):
    apiclass = api.MPoint
    apisize = 4
    apidim = 1

    # properties
    x = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
    y = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
    z = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) ) 
    w = property( lambda self: self.__getitem__(3) ,  lambda self, val: self.__setitem__(3,val) )    

    # base methods are inherited from Vector
    
class Color(Vector):
    apiclass = api.MColor
    apisize = 4
    apidim = 1
        
    # properties
    r = property( lambda self: self.__getitem__(0) ,  lambda self, val: self.__setitem__(0,val) )
    g = property( lambda self: self.__getitem__(1) ,  lambda self, val: self.__setitem__(1,val) )
    b = property( lambda self: self.__getitem__(2) ,  lambda self, val: self.__setitem__(2,val) ) 
    a = property( lambda self: self.__getitem__(3) ,  lambda self, val: self.__setitem__(3,val) )     
    
class Matrix(object):
    apiclass = api.MMatrix
    apisize = 16
    apidim = (4, 4)  

    # TODO a00, a01, etc properties ?  
    # class methods
    
    def __init__(self, *args, **kwargs):
        """ Init a Vector instance
            Can pass one argument being another Vector instance , or the vector components """
        if args :
            nbargs = len(args)
            if nbargs==1 :
                # single argument
                if type(args[0]) == type(self) :
                    # copy constructor
                    self._data = copy(args[0]._data)
                    return
                elif isinstance(args[0], self.__class__) :
                    # a compatible wrapped type
                    try :
                        self._data = (self.__class__.apiclass(args[0]._data),)
                        return
                    except :
                        pass
                elif isinstance(args[0], api.MTransformationMatrix) :
                    # fill _data with all different tranformation matrix
                    pass
                else :
                    # else see if we can init the api class directly
                    try :
                        self._data = self.__class__.apiclass(args[0])
                        return
                    except :
                        # else iterate it and init from the elements
                        if hasattr(args[0],'__iter__') :
                            try :
                                self.__class__.__init__(self, *args[0])
                                return
                            except :
                                pass
            # if we didn't succeed yet
            try :
                self._data = self.__class__.apiclass(*args)
                return
            except :
                l = list(self.__class__())
                for i in xrange(min(nbargs, len(l))) :
                    l[i] = args[i]
                try :
                    self._data = self.__class__.apiclass(*l)
                    return
                except :
                    pass
            # nothing worked
            if nbargs == 1 :
                raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (clsname(self), clsname(args[0]), clsname(self))                            
            else :
                raise TypeError, "a %s cannot be initialized from the provided arguments, check help(%s) " % (clsname(self), clsname(self))
        else :
            try :
                self._data = self.__class__.apiclass()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (clsname(self), clsname(self))
                 
        # can also use the form x=<number>, y=<number>, z=<number>
        try :
            c = kwargs.get('x', self._data.x)
            self._data.x = c
            c = kwargs.get('y', self._data.y)
            self._data.y = c
            c = kwargs.get('z', self._data.z)
            self._data.z = c
        except :
            raise TypeError, "a component of %s can only be numeric, not %s, check help(%s) " % (clsname(self), clsname(c), clsname(self))
            
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
#        l = list(self.get())
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
#    # wrap of API MVector methods    
#    def get(self):
#        ms = api.MScriptUtil()
#        p = ms.asDoublePtr ()
#        self._data.get(p)
#        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.__class__.apisize)]) 
  
  
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
    u = Vector.xAxis
    v = Vector.yAxis
    print "u = Vector.xAxis: %r" % u
    print "v = Vector.yAxis: %r" % v
    n = u ^ v
    print "n = u ^ v: %r" % n
    n[0:1] = [1, 1]
    print "n[0:1] = [1, 1] : %r" % n
    n = n*2
    print "n = n * 2 : %r" % n
    print "u * n : %s" % (u * n)
    print "Vector(): %r" % Vector()
    
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
    
_test()


    

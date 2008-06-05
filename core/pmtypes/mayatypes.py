"""
A wrap of Maya's MVector, MPoint, MColor, MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation types
"""

# Need to derive form the api class to keep api methods working but also from generic Array class
# to allow inter-operation
#class MVector(api.MVector) :
#    def __str__(self):
#        return '(%s, %s, %s)' % (self.x, self.y, self.z)
#class MTransformationMatrix(api.MTransformationMatrix) :
#    def __str__(self):
#    mat = self.asMatrix()
#        return '(%s)' % list(mat(i,j) for i in xrange(4) for j in xrange(4))
#mt = MTransformationMatrix()
#v = MVector(1, 2, 3)
#print mt
#print v
#mt.setTranslation(v, api.MSpace.kTransform)
#print mt


import inspect
import math, copy
import itertools, operator, colorsys

import pymel.api as api

import pymel.util as util
from pymel.util.arrays import Array, Vector, Matrix, metaReadOnlyAttr

# patch some Maya api classes that miss __iter__ to make them iterable / convertible to list
def _patchMVector() :
    def __iter__(self):
        """ Iterates on all 3 components of a Maya api MVector """
        for i in xrange(3) :
            yield self[i]
    type.__setattr__(api.MVector, '__iter__', __iter__)

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
_patchMMatrix()
_patchMTransformationMatrix()




#class MVector(api.MVector, Vector) :
#    __metaclass__ = metaReadOnlyAttr
#    stype = api.MVector
#    ndim = 1
#    shape = (3,)
#    size = 3
#    def __str__(self):
#        return '(%s, %s, %s)' % (self.x, self.y, self.z)
#class MPoint(api.MPoint, MVector) :
#    __metaclass__ = metaReadOnlyAttr
#    pass    
#class MTransformationMatrix(api.MTransformationMatrix, Matrix) :
#    __metaclass__ = metaReadOnlyAttr
#    stype = api.MTransformationMatrix
#    ndim = 2
#    shape = (4,4)
#    size = 16
#    def _getdata(self):
#        return list(self.get())
#    def _setdata(self, data):
#        mat = api.MMatrix()
#        api.MScriptUtil.createMatrixFromList ( list(data), mat)
#        self = self.__class__(mat) 
#    def _deldata(self):
#        del self     
#    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data") 
#    def __new__(cls, *args, **kwargs ):
#        # newcls = super(api.MTransformationMatrix, cls).__new__(cls, *args, **kwargs )
#        # return newcls
#        return api.MTransformationMatrix.__new__(cls, *args, **kwargs )
#    def __init__(self, *args, **kwargs ):
#        mat = api.MMatrix()
#        api.MScriptUtil.createMatrixFromList ( list(args), mat)     
#        # super(api.MTransformationMatrix, self).__init__(mat)
#        api.MTransformationMatrix.__init__(self, mat)
#    @classmethod
#    def default(cls, shape=None):
#        """ cls.default([shape])
#            Returns the default instance (of optional shape form shape) for that Array class """    
#        return cls(api.MTransformationMatrix.identity)  
#    def get(self):
#        """ Wrap the MMatrix api get method """
#        mat = self.asMatrix()
#        ptr = mat.matrix[4][4]
#        return tuple(tuple(api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(self.__class__.shape[1])) for r in xrange(self.__class__.shape[0]))      
#    def __str__(self):
#        mat = self.asMatrix()
#        return '(%s)' % list(mat(i,j) for i in xrange(4) for j in xrange(4))
#mt = MTransformationMatrix()
#v = MVector(1, 2, 3)
#print type(mt), type(v)
#print mt
#print v
#mt.setTranslation(v, api.MSpace.kTransform)
#print mt


class MetaMayaTypeWrapper(metaReadOnlyAttr) :
    """ A metaclass to wrap Maya api types, with support for class constants """ 

#    class ClassConstant(object):
#        """ A data descriptor for user defined constants on the class """
#        def __init__(self, value):
#            self.value = value
#        def __get__(self, instance, owner):
#            # purposedly authorize notation MColor.blue but not MColor().blue,
#            # the constants are a class property and are not defined on instances
#            if instance is None :
#                return owner(self.value)
#            else :
#                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)
#        def __set__(self, instance, value):
#            raise AttributeError, "class constant cannot be set"
#        def __delete__(self, instance):
#            raise AttributeError, "class constant cannot be deleted"
#          
#    def __new__(mcl, classname, bases, classdict):
#        """ Create a new class of metaClassConstants type """
#                   
#        # deriving from api classes does not give us what we need (see comments at file start)
#
#           
#        # create the new class   
#        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)
#            
#        if hasattr(newcls, 'stype') :
#            # type (api type) used for the storage of data
#            apicls  = newcls.apicls
#
#            # build the data property
#            def setdata(self, data):
#                self._data = self.__class__.apicls(data)
#            def getdata(self):
#                return self._data
#            p = property(getdata, setdata, None, "One %s" % apicls.__name__)
#            type.__setattr__(newcls, 'data', p)                           
#            # build some constants on the class            
#            constant = {}
#            # constants in class definition will be converted from api class to created class
#            for name, attr in newcls.__dict__.iteritems() :
#                # to add the wrapped api class constants as attributes on the wrapping class,
#                # convert them to own class         
#                if isinstance(attr, apicls) :
#                    if name not in constant :
#                        constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr)                          
#            # we'll need the api clas dict to automate some of the wrapping
#            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
#            apiDict = dict(inspect.getmembers(apicls))            
#            # defining class properties on the created class                 
#            for name, attr in apiDict.iteritems() :
#                # to add the wrapped api class constants as attributes on the wrapping class,
#                # convert them to own class         
#                if isinstance(attr, apicls) :
#                    if name not in constant :
#                        constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr)
#            # update the constant dict with herited constants
#            mro = inspect.getmro(newcls)            
#            for cls in mro :
#                if isinstance(cls, MetaMayaArrayTypeWrapper) :
#                    for name, attr in cls.__dict__.iteritems() :
#                        if isinstance(attr, MetaMayaArrayTypeWrapper.ClassConstant) :
#                            if not name in constant :
#                                constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr.value)
#            
#            # build the protected list to make some class ifo and the constants read only class attributes
#            protected = tuple(['apicls', 'shape', 'cnames', 'size', 'ndim', '_protected'] + constant.keys())
#            # store constants as class attributes
#            for name, attr in constant.iteritems() :
#                type.__setattr__(newcls, name, attr)
#            # store protect class read only information                            
#            type.__setattr__(newcls, '_protected', protected)          
#        else :
#            raise TypeError, "must define 'apicls' and 'shape' in the class definition (which Maya API class to wrap, and the Array shape)"
#        
#        return newcls 
 
# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(MetaMayaTypeWrapper) :
    """ A metaclass to wrap Maya type classes such as MVector, MMatrix """ 

    class ClassConstant(object):
        """ A data descriptor for user defined constants on the class """
        def __init__(self, value):
            self.value = value
        def __get__(self, instance, owner):
            # purposedly authorize MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None :
                return owner(self.value)
            else :
                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)
        def __set__(self, instance, value):
            raise AttributeError, "class constant cannot be set"
        def __delete__(self, instance):
            raise AttributeError, "class constant cannot be deleted"
  
    def __setattr__(cls, name, value):
        """ overload __setattr__ to forbid modification of protected class info """   
        try :
            protected = cls._protected
        except :
            protected = ()
        if name in protected :
            raise AttributeError, "attribute %s is a %s constant and cannot be modified on class %s" % (name, cls.__name__, cls.__name__)
        else :
            super(MetaMayaArrayTypeWrapper, cls).__setattr__(name, value)
           
    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as MVector or MMatrix """
            
        def __setattr__(self, name, value):
            """ overload __setattr__ to forbid overloading of protected class info on a class instance """
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
        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)

        try :
            apicls = newcls.apicls 
        except :
            apicls = None        
        try :
            shape = newcls.shape 
        except :
            shape = None
            
        if apicls is not None and shape is not None :
            # build the properties according to component names
            try :
                cnames = newcls.cnames
            except :
                cnames = ()
            # constants for shape, ndim, size
            type.__setattr__(newcls, 'shape', shape)
            # ndimensions and size of the array representing the wrapped class                   
            ndim = len(shape)
            type.__setattr__(newcls, 'ndim', ndim)
            size = reduce(operator.mul, shape, 1)
            type.__setattr__(newcls, 'size', size)                 
            # components list 
            type.__setattr__(newcls, 'cnames', cnames )                
            # we'll need properties for data and component names access on the new class
            if cnames :
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
            # build the data property
            def setdata(self, data):
                self._data = self.__class__.apicls(data)
            def getdata(self):
                return self._data
            p = property(getdata, setdata, None, "One %s" % apicls.__name__)
            type.__setattr__(newcls, 'data', p)                           
            # build some constants on the class            
            constant = {}
            # constants in class definition will be converted from api class to created class
            for name, attr in newcls.__dict__.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr)                          
            # we'll need the api clas dict to automate some of the wrapping
            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
            apiDict = dict(inspect.getmembers(apicls))            
            # defining class properties on the created class                 
            for name, attr in apiDict.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr)
            # update the constant dict with herited constants
            mro = inspect.getmro(newcls)            
            for cls in mro :
                if isinstance(cls, MetaMayaArrayTypeWrapper) :
                    for name, attr in cls.__dict__.iteritems() :
                        if isinstance(attr, MetaMayaArrayTypeWrapper.ClassConstant) :
                            if not name in constant :
                                constant[name] = MetaMayaArrayTypeWrapper.ClassConstant(attr.value)
            
            # build the protected list to make some class ifo and the constants read only class attributes
            protected = tuple(['apicls', 'shape', 'cnames', 'size', 'ndim', '_protected'] + constant.keys())
            # store constants as class attributes
            for name, attr in constant.iteritems() :
                type.__setattr__(newcls, name, attr)
            # store protect class read only information                            
            type.__setattr__(newcls, '_protected', protected)          
        else :
            raise TypeError, "must define 'apicls' and 'shape' in the class definition (which Maya API class to wrap, and the Array shape)"
        
        return newcls  

                
# TODO : how do we want support for n-sized vectors ? Kept the code generic in case we want to share some of it
# Derive a 3 components MVector using api from a generic VectorN using generic methods ?
                 
class MVector(Vector):
    """ A 3 dimensional vector class that wraps Maya's api MVector class,
        >>> v = MVector(1, 2, 3)
        >>> w = MVector(x=1, z=2)
        >>> z = MVector(MVector.xAxis, z=1)
        """
    __metaclass__ = MetaMayaArrayTypeWrapper
    # class specific info
    apicls = api.MVector
    cnames = ('x', 'y', 'z')
    shape = (3,)
         
    # class methods and properties
    @property
    def vector(self):
        """ Returns an api.MVector representation of self """
        return self.data    
    @property
    def point(self):
        """ Returns an api.MPoint representation of self """
        return api.MPoint(self.data)
    @property
    def color(self):
        """ Returns an api.MColor representation of self """
        return api.MColor(self.data[0], self.data[1], self.data[2])
    
    def fromAPI (self, value):
        """ Sets self to a wrapped Maya api class instance """
        apiData = None
        try :
            apiData = self.apicls(value)
        except :
            # try a base class of self class in case it can init from that api data
            for cls in self.__class__.__mro__[1:] :
                if issubclass(cls, MVector) :
                    try :
                        apiData = self.__class__(cls(value)).data
                    except :
                        pass
        if apiData is not None :
            self.data = apiData
        else :
            raise TypeError, "a %s cannot be initialized from a single %s, check help(%s) " % (util.clsname(self), util.clsname(value), util.clsname(self))        

    # define the __new__ method
    def __new__(cls, *args, **kwargs):
        """ A new instance of that MVector or subtype of MVector class """
        obj = super(MVector, cls).__new__(cls, *args, **kwargs)
        obj._data = cls.apicls()              
        return obj 
        
    def __init__(self, *args, **kwargs):
        """ Init a MVector instance or subtype of MVector instance
            Can pass one argument being another MVector instance , or the vector components """
        if args :
            nbargs = len(args)
            if nbargs==1 and not util.isScalar(args[0]) :
                # single argument
                if isinstance(args[0], MVector) :
                    # a compatible wrapped type
                    self.data = args[0].vector
                elif hasattr(args[0],'__iter__') :
                    # iterable : iterate on elements
                    self.__init__(*args[0], **kwargs)
                else :
                    # else see if we can init the api class directly
                    self.fromAPI(args[0])
            else :
                if nbargs == self.size :
                    l = args
                else :
                    l = list(self.__class__())
                    for i in xrange(min(nbargs, len(l))) :
                        l[i] = args[i]
                try :
                    self.data = self.apicls(*l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                    raise TypeError, "in %s(%s) the provided arguments do not match the class components, check help(%s) " % (util.clsname(self), msg, util.clsname(self))
        else :
            try :
                self.data = self.apicls()
            except :
                raise TypeError, "a %s cannot be initialized without arguments, check help(%s) " % (util.clsname(self), util.clsname(self))

        if self.data is not None :  
            # can also use the form <componentname>=<number>
            l = list(self)                     # current
            try :
                for i in xrange(self.size) :
                    l[i] = kwargs.get(self.__class__.cnames[i], l[i])
                self.data = self.apicls(*l)
            except :
                msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", self.__class__.cnames, l))
                raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))
            
    # display      
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
    def get(self):
        ms = api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.data.get(p)
        result = tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)]) 
    def __getitem__(self, i):
        """ Get component i value from self """
        if isinstance(i, slice) :
            return list(self)[i]
        else :
            if i < 0 :
                i = self.size + i
            if i<self.size and not i<0 :
                return self._data[i]
            else :
                raise IndexError, "%s has only %s elements" % (self.__class__.__name__, self.size)
    def __setitem__(self, i, a):
        """ Set component i value on self """
        l = list(self)
        l[i] = a
        self.data = self.apicls(*l[:self.size])
    def __iter__(self):
        """ Iterate on the api components """
        for i in xrange(self.size) :
            yield self.data[i]
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        for i in xrange(self.size) :
            if self.data[i] == value :
                return True
        return False
    
    
    # common operators
    def __neg__(self):
        """ u.__neg__() <==> -u
            Returns the MVector obtained by negating every component of u """        
        return self.__class__(map(lambda x: -x, self))   
    def __invert__(self):
        """ u.__invert__() <==> ~u
            unary inversion, returns 1 - u for Vectors """        
        return self.__class__(map(lambda x: 1.0-x, self))      
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to MVector,
            adds v to every component of u if v is a scalar """        
        if isinstance(other, MVector) :
            # return self.__class__(map( lambda x, y: x+y, self[:MVector.size], other[:MVector.size]))
            # return self.__class__(self.data.__add__(other.vector))
            return difmap(operator.add, self, other)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(self), util.clsname(other))    
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to MVector,
            adds v to every component of u if v is a scalar """        
        if isinstance(other, MVector) :
            # return self.__class__(map( lambda x, y: x+y, self[:MVector.size], other[:MVector.size]))
            # return self.__class__(self.data.__add__(other.vector))
            return difmap(operator.add, other, self)
        elif util.isScalar(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :            
            raise TypeError, "unsupported operand type(s) for +: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        self._data = (self.__add__(other)).data
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a MVector instance,
            substract v to every component of u if v is a scalar """        
        if isinstance(other, MVector) :
            # difference of two points is a vector, of a vector and a point is a point
            if len(other) > len(self) :
                # other is a MPoint or MColor
                return other.__class__(self.data.__sub__(other.vector))
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
            if len(other) > len(self) :
                # other is a MPoint or MColor
                return other.__class__(other.data.__sub__(self.data))
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
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the element wise division of each component of u by the
            corresponding component of v if both are convertible to MVector,
            divide every component of u by v if v is a scalar """  
        if hasattr(other, '__iter__') :
            lm = min(len(other), len(self))
            l = map(lambda x, y: x/y, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        elif util.isScalar(other) :
            return self.__class__(map(lambda x: x/other, self))
        else :
            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(self), util.clsname(other))  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to MVector,
            invert every component of u and multiply it by v if v is a scalar """
        if hasattr(other, '__iter__') :
            lm = min(len(other), len(self))
            l = map(lambda x, y: y/x, self[:lm], other[:lm]) + self[lm:len(self)]
            return self_class__(*l)
        elif util.isScalar(other) :
            return self.__class__(map(lambda x: other/x, self))
        else :
            raise TypeError, "unsupported operand type(s) for /: '%s' and '%s'" % (util.clsname(other), util.clsname(self))  
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
            The multiply '*' operator is mapped to the dot product when both objects are instances of MVector,
            to the transformation of u by matrix v when v is an instance of MMatrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, self.__class__) :
            # dot product in case of a vector
            return self.data.__mul__(other.data)
        elif isinstance(other, MMatrix) :
            # MMatrix transformation
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
        if isinstance(other, self.__class__) or util.isScalar(other) or util.isSequence(other) : 
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
            Valid for MVector * MMatrix multiplication, in place transformation of u by MMatrix v
            or MVector by scalar multiplication only """
        if isinstance(other, MMatrix) :
            self._data = self.data.__mul__(other.matrix)
        elif util.isScalar(other) :
            self._data = self.__class__(map(lambda x: x.__mul__(other), self)).data
        else :
            self._data = self.__mul__(MMatrix(other)).data             
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two vectors,
            if v is a MMatrix, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, MVector) :
            return self.__class__(self.vector.__xor__(other.vector))   
        elif isinstance(other, MMatrix) :
            return self.__class__(self.vector.transformAsNormal(other.matrix))
        else :
            raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (util.clsname(self), util.clsname(other))
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a MMatrix """        
        self._data = self.__xor__(other).data 
        
    # wrap of API MVector methods    
    def isEquivalent(self, other, tol=api.MVector_kTol):
        """ Returns true if both arguments considered as MVector are equal  within the specified tolerance """
        try :
            return bool(self._data.isEquivalent(MVector(other)._data, tol))
        except :
            raise TypeError, "%s is not convertible to a MVector, or tolerance %s is not convertible to a number, check help(MVector)" % (other, tol) 
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
    def transformAsNormal(self, matrix):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, MMatrix) :
            return self.__class__(self.vector.transformAsNormal(other.matrix))
        else :
            raise TypeError, "%r is not a MMatrix instance" % matrix
    # additional methods
    def dot(self, other):
        if isinstance(other, MVector) :
            lm = min(len(self), len(other))
            return reduce(operator.add, map(operator.mul, self[:lm], other[:lm]), 0.0)
        else :
            raise TypeError, "%s is not a MVector instance" % other        
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, MVector) :
            return self.__class__(self.vector.__xor__(other.vector))  
        else :
            raise TypeError, "%r is not a MVector instance" % other                 
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
           
class MPoint(MVector):
    apicls = api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)
    
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

    # base methods are inherited from MVector
    # define the __new__ method
    def __new__(cls, *args, **kwargs):
        """ A new instance of that MVector or subtype of MVector class """
        obj = super(MVector, cls).__new__(cls, *args, **kwargs)
        obj._data = cls.apicls()              
        return obj 
        
    def __init__(self, *args, **kwargs):
        """ Init a MVector instance or subtype of MVector instance
            Can pass one argument being another MVector instance , or the vector components """
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


def _test() :
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
    
    print "MVector class", dir(MVector)
    print "MPoint  class", dir(MPoint)
    # print "MColor  class", dir(MColor)    
    u = MVector.xAxis
    v = MVector.yAxis
    print "u = MVector.xAxis: %r" % u
    print "v = MVector.yAxis: %r" % v
    n = u ^ v
    print "n = u ^ v: %r" % n
    print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    n[0:2] = [1, 1]
    print "n[0:2] = [1, 1] : %r" % n
    n = n*2
    print "n = n * 2 : %r" % n
    print "u * n : %s" % (u * n)
    print "MVector(): %r" % MVector()
    
    print "~u: %r" % (~u)

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
    
if __name__ == '__main__' :
    _test()


    
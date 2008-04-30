
"""
List based Vector and Matrix classes that support elementwise mathematical operations
"""

# based on a python Vector class by A. Pletzer 5 Jan 00/11 April 2002
# NOTE: modified and added some methods that are closer to how Numpy works, like the multi index slicing
# through get / setitem for instance and tried to make the method names match so that
# it will be easier to include Numpy instead if desired as a base for n sided Vector and Matrix


import operator

from arguments import isIterable, expandArgs, isScalar, isNumeric, clsname
from mathutils import difmap, clamp

# iterator classes on a specific Array dimension, supporting __getitem__
# in a Numpy like way
class ArrayIter(object):
    def __init__(self, data, onindex=0) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, Array) :
            self.base = data
            self.shape = self.base.shape
            self.size = self.base.size
            self.dim = self.base.dim            
            self.coords = [0]*len(self.shape)
            if onindex in range(self.dim) :
                self.onindex = onindex                  
            else :
                raise ValueError, "%s has %s dimensions, cannot iterate on index %s" % (clsname(self.base), self.base.dim, onindex)
        else :
            raise TypeError, "%s can only be built on Array" % clsname(self)
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

# "Flat" iterator classes on arrays, supporting __getitem__
# in a Numpy like way
class ArrayFlatIter(object):

    def __init__(self, data) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, Array) :
            self.base = data
            self.shape = self.base.shape
            self.size = self.base.size
            self.dim = self.base.dim
            self.coords = [0]*len(self.shape)
        else :
            raise TypeError, "%s can only be built on Array" % clsname(self)
    def __length_hint__(self) :
        return self.size
    def __iter__(self) :
        return self 

    def next(self):
        for i in range(self.dim, 1, -1) :
            if self.coords[i] == self.shape[i] :
                self.coords[i] = 0
                self.coords[i-1] += 1
        if self.coords[0] >= self.shape[0] : 
            raise StopIteration
        print "next for coords: %s" % self.coords
        val =  self.base[self.coords]
        self.coords[-1] += 1
        return val         

    def __getitem__(self, flatindex) :
        if isinstance(flatindex, slice) :
            return [self[i] for i in range(self.size)[flatindex]]
        else :
            flatindex = int(flatindex)
            if flatindex < 0 :
                flatindex = self.size - flatindex
            if flatindex in range(self.size) :
                icoords = [0]*self.dim
                subsize = 1
                for i in range(self.dim, 1, -1) :
                    print "coord %s" % i
                    print "shape[i] %s" % self.shape[i]
                    newsize *= self.shape[i]
                    print "subsize %s" % subsize
                    icoords[i] = (flatindex / subsize) % newsize
                    subsize = newsize
                print "icoords: %s" % icoords
                return self.base(icoords)
            else :
                raise IndexError, "flat index %s is out of bounds" % flatindex
    
# A generic multi dimensional Array class
# NOTE : Numpy Array class could be used instead, just implemented the bare minimum inspired from it
class Array(list):
    """ A generic n-dimensional array class based on nested lists """
    def _getshape(self):
        shape = []
        sub = self
        while sub is not None :
            try :
                shape.append(list.__len__(sub))
                sub = sub[0]
            except :
                sub = None
        return tuple(shape) 
    shape = property(_getshape, None, None, "Shape of the Array (number of dimensions and number of components in each dimension")    
    dim = property(lambda x : len(x.shape), None, None, "Number of dimensions of the Array")
    size = property(lambda x : reduce(operator.mul, x.shape, 1), None, None, "Total size of the Array (number of individual components)")  
    
    def __init__(self, *args ):
        l = []
        if args :
            # print "args: %s" % (list(args))
            if len(args) == 1 and isIterable(args[0]) :
                args = args[0]
            shape = []
            for arg in args :
                if isNumeric(arg) :
                    l.append(arg)
                    shape.append((1,))                  
                elif isIterable(arg) :
                    sub = Array(*arg)
                    l.append(sub)
                    shape.append(sub.shape)
                else :
                    raise TypeError, "an Array element can only be a numeric value"                   
            # check sub arrays dim and size
            # print "subs shape: %s" % shape
            if not reduce(lambda x, y : x and y == shape[0], shape, True) :
                raise ValueError, "all sub-arrays must have same shape"

        list.__init__(self, l)
        
    def append(self, *args):
        pass    
    
    # display      
    def __str__(self):
        return "[%s]" % ", ".join( map(str,self) )
    def __unicode__(self):
        return u"[%s]" % u", ".join( map(unicode,self) )
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self)) 
    
    def _formatloop(self, level=0):
        subs = []
        for a in self :
            if isinstance(a, Array) :
                depth, substr = a._formatloop(level+1)
                subs.append(substr)
            else :
                depth = 0
                subs.append(str(a))
        if depth :
            msg = "[%s]" % (","+"\n"*depth+" "*(level+1)).join(subs)
        else :
            msg = "[%s]" % ", ".join(subs)
        return depth+1, msg                 
    def formated(self):
        return self._formatloop()[1]
    
    # wrap of list-like access methods
    def __len__(self):
        """ Length of the first dimension of the array """
        if self.shape :
            return self.shape[0]
        else :
            return 0
  
    @staticmethod
    def _extract(x, y) :
        if isinstance(x, Array) :
            res = list.__getitem__(x, y)
        else :
            res = [Array._extract(a, y) for a in x]
        return res

    
    def __getitem__(self, index):
        """ Get value from either a single (first dim) or multiple index, support for slices"""
        if hasattr(index, '__iter__') :
            # multiple index
            dim = self.dim
            shape = self.shape
            coords = [slice(None, None, None)]*dim          
            for i, c in enumerate(list(index)[:dim]) :
                coords[i] = c
                if isScalar(c) :
                    # bounds check
                    if c < 0 :
                        c = shape[i] - c
                    if not c in range(shape[i]) :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
            return reduce(lambda x, y: Array._extract(x, y), coords, self)               
        else :
            # single index, means on first dimension
            return list.__getitem__(self, index)


    def __setitem__(self, rc, value):
        """ Set value from either a single (first dim) or multiple index, support for slices"""
        dim = self.dim
        shape = self.shape
        coords = [slice(None, None, None)]*dim
        pivot = None
        if hasattr(indexes, '__iter__') :
            for i, c in eumerate(list(indexes)[:dim]) :
                coords[i] = c
                if isScalar(c) :
                    # bounds check
                    if c < 0 :
                        c = shape[i] - c
                    if c in range(shape[i]) :
                        if pivot is None :
                            pivot = i
                    else :
                        raise IndexError, "index %s for dimension %s is out of bounds" % (c, i)
        else :
            coords[0] = indexes
        if pivot is None :
            pivot = 0
        print "coords: %s, pivot: %s" % (coords, pivot)
        # bounds check
        # return tuple(row[c] for row in self.row[r])
        
        # numpy like m[:,:] format, we set a sub Matrix
        if isScalar(value) :
            for i in range(self.__class__.shape[0])[r] :
                self[i,c] = value            
        else :
            for v, i in enumerate(range(self.__class__.shape[0])[r]) :
                self[i,c] = value[v]

    def __iter__(self):
        """ Default Array iterator on first dimension """
        return list.__iter__(self)  
         
    def __contains__(self, value):
        """ True if at least one of the Matrix components is equal to the argument,
            can test for the presence of a complete row if argument is a row sequence """
        if isScalar(value) :
            return value in self.flat
        else :
            return value in self.row 
           
    def transpose(self, *args):
        dim = self.dim
        if not args :
            axis = range(dim-1, -1, -1)
        else :
            axis = []
            for a in args :
                a = int(a)
                if a in range(dim) :
                    if not a in axis :
                        axis.append(a)
                    else :
                        raise ValueError, "transpose axis %s specified twice" % a
                else :
                    raise ValueError, "transpose axis %s does not exist for Array of dimension %s" % (a, dim)
            if len(axis) < dim :
                for a in range(dim) :
                    axis.append(a)
        print "transpose axis %s" % axis
        res = self
        return res
        
    def flat(self):
        return ArrayFlatIter(self)                 

#A = Array([[[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]]])
#print A
#A = Array([[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]])
#print A
#B = Array(1, 2, 3)
#print B
#B = Array([1], [2], [3])
#print B
#B = Array([[1], [2], [3]])
#print B
#B = Array([[[1], [2], [3]]])
#print B
#B = Array([[1,1,1],[4,4,3],[7,8,5]])
#print B
#print repr(B)
#print B.formated()          
#A = Array([[[1,1,1],[4,4,3],[7,8,5]], [[10,10,10],[40,40,30],[70,80,50]]])
#print A
#print repr(A)
#print A.formated()
#print A[0]
#print A[0, 2, 1]
#print A[0, :, 1]
#print A[0, :]
#print A[0, :, 1:2]
#print A[0, 1:2, 1:2]
#print A[0, :, 1:3]
#print A[:, :, 1:3]
#print A[:, :, 1:2]
#
## should fail
#B = Array([[1,1,1],[4,4,3],[8,5]])

# TODO
# print list(a.flat)
# print a.flat[3]


class Vector(Array):
    """
        A generic size Vector class, basically a 1 dimensional Array
    """
    
    shape = property(lambda x : (list.__len__(x),), None, None, "A Vector is a one-dimensional Array of n components")   
    dim = property(lambda x : 1, None, None, "A Vector is a one-dimensional Array")
    size = property(lambda x : list.__len__(x), None, None, "Size of the Vector (number of components)")
  
    def __init__(self, *args):
        """ Init a Vector instance, from several scalar values """
        list.__init__(self, [])
        self.append(*args)
            
    def append(self, *args):
        """ appends one or more scalar values to that Vector """
        for a in iterateArgs( *args ) :
            if isNumeric(a) :
                list.append(self, a)
            else :
                raise TypeError, "Vector component values can only be numeric values"
                        
    # display      
    def __str__(self):
        return '[%s]' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'[%s]' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))     
    def formated(self):
        return '[%s]' % ", ".join(map(str, self))    

        
    # __len__, __getitem__, __setitem__, __iter__ and __contains__ derived from list
    
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
        if isNumeric(other) :
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
        if isNumeric(other) :
            return self.__class__(map( lambda x: x-other, self))        
        else :
            return difmap(operator.sub, self, other)      
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a Vector instance,
            replace every component c of u by v-c if v is a scalar """        
        if isNumeric(other) :
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
        if isNumeric(other) :
            return self.__class__(map(lambda x: x/other, self))
        else :
            return difmap(operator.div, self, other)  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to Vector,
            invert every component of u and multiply it by v if v is a scalar """
        if isNumeric(other) :
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
        elif isNumeric(other) :
            # multiply all components by a scalar
            return self.__class__(map(lambda x: x*other, self))
        else :
            # try an element wise multiplication if other is iterable
            try :
                other = list(other)
            except :
                raise TypeError, "unsupported operand type(s) for *: '%s' and '%s'" % (clsname(self), clsname(other))
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
                raise TypeError, "unsupported operand type(s) for ^: '%s' and '%s'" % (clsname(self), clsname(other))
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
            raise TypeError, "%s is not convertible to a %s, check help(%s)" % (clsname(other), clsname(self), clsname(self))        
        if isNumeric(blend) :
            l = (self*(1-blend) + other*blend)[:len(other)] + self[len(other):len(self)]
            return self.__class__(*l)            
        else :
            try : 
                bl = list(blend)
            except :
                raise TypeError, "blend can be an iterable (list, tuple, Vector...) of numeric values, or a single numeric value, not a %s" % clsname(blend)
            lm = min(len(bl), len(self), len(other))
            l = map(lambda x,y,b:(1-b)*x+b*y, self[:lm], other[:lm], bl[:lm]) + self[lm:len(self)]
            return self.__class__(*l)       
    def clamp(self, low=0.0, high=1.0):
        """ u.clamp(low, high) returns the result of clamping each component of u between low and high if low and high are scalars, 
            or the corresponding components of low and high if low and high are sequences of scalars """
        ln = len(self)
        if isNumeric(low) :
            low = [low]*ln
        else :
            try : 
                low = list(low)[:ln]
            except :
                raise TypeError, "'low' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % clsname(low) 
        if isNumeric(high) :
            high = [high]*ln
        else :
            try :  
                high = list(high)[:ln]
            except :
                raise TypeError, "'high' can only be an iterable (list, tuple, Vector...) of scalars or a scalar, not a %s" % clsname(high)         
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
    dim = property(lambda x : 2, None, None, "A Matrix is a two-dimensional Array")
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

    
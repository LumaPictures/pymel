
"""
List based vector and matrix classes that support elementwise mathematical operations
"""

# based on a python vector class by A. Pletzer 5 Jan 00/11 April 2002
# NOTE: modified and added some methods that are closer to how Numpy works, like the multi index slicing
# through get / setitem for instance and tried to make the method names match so that
# it will be easier to include Numpy instead if desired as a base for n sided vector and matrix


from operators import *
from arguments import expandArgs, isScalar, isNumeric, clsname
from mathutils import difmap, clamp
import node, core

# iterator classes on a specific array dimension, supporting __getitem__
# in a Numpy like way
class ArrayIter(object):
    def __init__(self, data, onindex=0) :
        # print "type", type(data), "on index", onindex
        if isinstance(data, array) :
            self.base = data
            self.shape = self.base.shape
            self.coords = [0]*len(self.shape)
            if onindex == 0 :
                self._next = self._nextrow
            elif onindex == 1 :
                self._next = self._nextcolumn 
            elif onindex == (0,1) :
                self.ptr = self.base.matrix[0]
                self._next = self._nextflat                           
            else :
                raise ValueError, "%s has %s dimensions, cannot iterate on index %s" % (clsname(self.base), self.base.dim, onindex)
        else :
            raise TypeError, "%s can only be built on array" % clsname(self)
    def __length_hint__(self) :
        return len(self.base)
    def __iter__(self) :
        return self 
    def _nextonindex(self, onindex) :
        if self.coords[onindex] == self.shape[onindex] :        
            raise StopIteration
        # fix
        val =  [self.matrix(r, self.coords[onindex]) for r in xrange(self.shape[0])]
        self.coords[onindex] += 1
        return val       
    def _nextrow(self) :
        if self.coords[0] == self.shape[0] :        
            raise StopIteration
        self.ptr = self.base.matrix[self.coords[0]]
        val =  tuple(api.MScriptUtil.getDoubleArrayItem(self.ptr, c) for c in xrange(self.shape[1]))
        self.coords[0] += 1
        return val
    def _nextcolumn(self) :
        if self.coords[1] == self.shape[1] :        
            raise StopIteration
        val =  tuple(self.base.matrix(r, self.coords[1]) for r in xrange(self.shape[0]))
        self.coords[1] += 1
        return val
    def _nextflat(self) :
        if self.coords[1] == self.shape[1] :
            self.coords[1] = 0
            self.coords[0] += 1
            if self.coords[0] < self.shape[0] : 
                self.ptr = self.base.matrix[self.coords[0]]       
            else :
                raise StopIteration
        val =  api.MScriptUtil.getDoubleArrayItem(self.ptr, self.coords[1])
        self.coords[1] += 1
        return val 
    def next(self):
        return self._next()     
    def __getitem__(self, i) :
        return tuple(self)[i]

# "Flat" iterator classes on arrays, supporting __getitem__
# in a Numpy like way
class ArrayFlatIter(object):
    pass

# A generic multi dimensional array class
# NOTE : Numpy array class could be used instead, just implemented the bare minimum inspired from it
class array(list):

    def _getshape(self):
        shape = []
        sub = self
        while sub is not None :
            try :
                shape.append(len(sub))
                sub = sub[0]
            except :
                sub = None
        return tuple(shape)
    
    shape = property(_getshape)    
    dim = property(lambda x : len(x.shape))
    size = property(lambda x : reduce(operator.mul, x.shape, 1))  
    
    def __init__(self, rowColList = [[0]*4]*4 ):
        for i in range( 0, len(rowColList )):
            rowColList[i] = Vector( rowColList[i] )
        
        list.__init__(self, rowColList)
        
    # display      
    def __str__(self):
        return "[%s]" % ", ".join( imap(str,self.row) )
    def __unicode__(self):
        return u"[%s]" % u", ".join( imap(unicode,self.row) )
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))          
    def formated(self):
        return "[%s]" % "\n".join( imap(str,self.row) )
    
    # wrap of list-like access methods
    def __len__(self):
        """ Matrix class has a fixed length"""
        return self.size
    
    def __getitem__(self, rc):
        """ Get value from either a (row,column) tuple or a single component index (get a full row) """
        if isScalar (rc) :
            r = rc
            c = slice(None, None, None)
        else :
            r,c = rc
        print r,c
        # bounds check
        if isScalar(r) and isScalar(c) :
            # single element
            if r in range(self.__class__.shape[0]) and c in range(self.__class__.shape[1]) :
                return self.matrix(r, c)
            else :
                raise IndexError, "%s has no element of index [%s,%s]" % (self.__class__.__name__, r, c)
        elif isScalar(c) :
            # numpy like m[:,2] format, we return (possibly partial) columns
            if c in range(self.__class__.shape[1]) :
                return tuple([self.matrix(i, c) for i in xrange(self.__class__.shape[0])][r])
            else :
                raise IndexError, "There are only %s columns in class %s" % (self.__class__.shape[1], self.__class__.__name__)
        elif isScalar(r) :
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
        if isScalar (rc) :
            r = rc
            c = slice(None, None, None)
        else :
            r,c = rc
        print r,c
        # bounds check
        if isScalar(r) and isScalar(c) :
            # set a single element
            if r in range(self.__class__.shape[0]) and c in range(self.__class__.shape[1]) :
                ptr = self.matrix[r]
                api.MScriptUtil.setDoubleArray(ptr, c, value)
            else :
                raise IndexError, "%s has no element of index [%s,%s]" % (self.__class__.__name__, r, c)
        elif isScalar(c) :
            # numpy like m[:,2] format, we set (possibly partial) columns
            if c in range(self.__class__.shape[1]) :
                l = list(self.flat)
                if isScalar(value) :
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
        elif isScalar(r) :
            # numpy like m[2,:] format, we set (possibly partial) columns
            if r in range(self.__class__.shape[0]) :
                ptr = self.matrix[r]
                if isScalar(value) :
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
            if isScalar(value) :
                for i in range(self.__class__.shape[0])[r] :
                    self[i,c] = value            
            else :
                for v, i in enumerate(range(self.__class__.shape[0])[r]) :
                    self[i,c] = value[v]

    def __iter__(self):
        """ Default Matrix iterators iterates on rows """
        for r in xrange(self.__class__.shape[0]) :
            ptr = self.matrix[r]
            yield tuple(api.MScriptUtil.getDoubleArrayItem(ptr, c) for c in xrange(self.__class__.shape[1]))         
    def __contains__(self, value):
        """ True if at least one of the Matrix components is equal to the argument,
            can test for the presence of a complete row if argument is a row sequence """
        if isScalar(value) :
            return value in self.flat
        else :
            return value in self.row    
    
    def flat(self):
        return reduce( lambda x,y: list(x)+list(y), self )                  

class vector(array):
    """
        A list based vector class
    """
    
    def __init__(self, *args):
        """ Init a vector instance, from several scalar values """
        l = map(float, expandArgs( *args ))
        list.__init__(self, l)
            
    # display      
    def __str__(self):
        return '(%s)' % ", ".join(map(str, self))
    def __unicode__(self):
        return u'(%s)' % ", ".unicode(map(str, self))    
    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, str(self))     
    
    def append(self, *args):
        """ appends one or more scalar values to that vector """
        l = map(float, expandArgs( *args ))
        for arg in l :
            list.append(self, arg)
        
    # __len__, __getitem__, __setitem__, __iter__ and __contains__ derived from list
    
    # common operators
    def __neg__(self):
        """ u.__neg__() <==> -u
            Returns the vector obtained by negating every component of u """        
        return self.__class__(map(operator.neg, self))   
    def __invert__(self):
        """ u.__invert__() <==> ~u
            unary inversion, returns 1 - u for vectors """        
        return self.__class__(map(lambda x: 1.0-x, self))      
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to vector,
            adds v to every component of u if v is a scalar """        
        if isNumeric(other) :
            return self.__class__(map( lambda x: x+other, self))        
        else :
            return difmap(operator.add, self, other)  
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to vector,
            adds v to every component of u if v is a scalar """        
        return self.__add__(other)  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        self = self.__class__(self.__add__(other))
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is a vector instance,
            substract v to every component of u if v is a scalar """        
        if isNumeric(other) :
            return self.__class__(map( lambda x: x-other, self))        
        else :
            return difmap(operator.sub, self, other)      
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is a vector instance,
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
            corresponding component of v if both are convertible to vector,
            divide every component of u by v if v is a scalar """  
        if isNumeric(other) :
            return self.__class__(map(lambda x: x/other, self))
        else :
            return difmap(operator.div, self, other)  
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of the element wise division of each component of v by the
            corresponding component of u if both are convertible to vector,
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
    # NOTE : dot product mapped on mult if both arguments are vector, else we do element wise mutliplication
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are instances of Vector,
            to the transformation (post-multiplication) of u by matrix v when v is an instance of Matrix,
            and to element wise multiplication when v is a scalar or a sequence """
        if isinstance(other, self.__class__) :
            # dot product in case of a vector
            return self.dot(other)
        elif isinstance(other, matrix) :
            # Vector by Matrix multiplication
            dif = other.shape[1]-self.size
            res = matrix([list(self) + [1]*dif]) * other 
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
        if isinstance (other, matrix) :
            # not commutative with a Matrix
            dif = other.shape[0]-self.size
            res = other * matrix(map(lambda x:[x], list(self)+[1]*dif))
            return self.__class__(res[0:self.size, 0])            
        else :
            # commutative otherwise
            return self.__mul__(other)
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Makes sense for Vector * Matrix multiplication, in place transformation of u by Matrix v
            or vector element wise multiplication only """
        self = self.__mul__(other)            
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two vectors,
            if v is a Matrix, u^v is equivalent to transforming u by the adjoint matrix of v """
        if isinstance(other, vector) :
            return self.cross(other)  
        else :
            try :
                return self.__mul__(matrix(other).adjoint())
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
        if isinstance(other, vector) :
            lm = min(len(self), len(other))
            return reduce(operator.add, map(operator.mul, self[:lm], other[:lm]), 0.0)
        else :
            raise TypeError, "dot product is only defined between two vectors"        
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, vector) and self.size == 3 and other.size == 3 :
            return self.__class__(self[1]*other[2] - self[2]*other[1],
                                  self[2]*other[0] - self[0]*other[2],
                                  self[0]*other[1] - self[1]*other[0])
        else :
            raise ValueError, "cross product is only defined between two vectors of size 3"
    def length(self):
        """ Length of self """
        return sqrt(abs(self.dot(self)))                        
    def sqLength(self):
        """ Squared length of vector """
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
    # TODO : can implement vector smoothstep, setRange, hermite from mathutils the same way  

    # vectors of complex values
    def conjugate(self):
        return vector(map(lambda x: x.conjugate(), self))
    def ReIm(self):
        """ Returns the real and imaginary parts """
        return [
            vector(map(lambda x: x.real, self)),
            vector(map(lambda x: x.imag, self)),
            ]
    def AbsArg(self):
        """ Returns modulus and phase parts """
        return [
            vector(map(lambda x: abs(x), self)),
            vector(map(lambda x: atan2(x.imag,x.real), self)),
            ]



class Matrix(array):
    """
    A list based Matrix class
    """
        
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

    
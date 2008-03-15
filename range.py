# Ranges expressed as one pair of two min and max float value (None for unbounded)
# for continuous ranges or severals pairs of min and max for discontinuous ranges and methods to do union    
# intersection and substraction of Ranges
# (can be used for frame ranges for instance)

class MetaRange(type):
                
    #The type of bounds used in the Range class
    def __get_BoundType(cls):
        return cls._BoundType
    BoundType = property(__get_BoundType, None, None, "The type used for internal bounds and step storage for that Range class.")
    
    def __repr__(cls):
        return "%s<BoundType:%r>" % (cls.__name__, cls.BoundType)
       
    def __new__(cls, classname, bases, classdict):

        boundType = int
        # get the bounds type from first base class that fits requirements
        required = ('__add__', '__sub__', '__eq__', '__ne__', '__gt__', '__lt__')
        for baseClass in bases :
            for reqMethod in required :
                if not hasattr(baseClass,reqMethod) :
                    continue
            boundType = baseClass
            break
        # we always derive from set as a bounded range can be expressed as a set
        if set not in bases :
            bases = bases+(set,)
                             
        # remove what we don't want to expose from bases
        def __getattribute__(self, name):          
            remove = ()
            if name in remove :
                raise AttributeError, "'"+classname+"' object has no attribute '"+name+"'" 
            else :
                return unicode.__getattribute__(self, name)

#len(s)           cardinality of set s
#x in s         test x for membership in s
#x not in s         test x for non-membership in s
#s.issubset(t)     s <= t     test whether every element in s is in t
#s.issuperset(t)     s >= t     test whether every element in t is in s
#s.union(t)     s | t     new set with elements from both s and t
#s.intersection(t)     s & t     new set with elements common to s and t
#s.difference(t)     s - t     new set with elements in s but not in t
#s.symmetric_difference(t)     s ^ t     new set with elements in either s or t but not both
#s.copy()         new set with a shallow copy of s   
#|  __and__(...)
# |      x.__and__(y) <==> x&y
# |  
# |  __cmp__(...)
# |      x.__cmp__(y) <==> cmp(x,y)
# |  
# |  __contains__(...)
# |      x.__contains__(y) <==> y in x.
# |  
# |  __eq__(...)
# |      x.__eq__(y) <==> x==y
# |  
# |  __ge__(...)
# |      x.__ge__(y) <==> x>=y
# |  
# |  __getattribute__(...)
# |      x.__getattribute__('name') <==> x.name
# |  
# |  __gt__(...)
# |      x.__gt__(y) <==> x>y
# |  
# |  __hash__(...)
# |      x.__hash__() <==> hash(x)
# |  
# |  __iand__(...)
# |      x.__iand__(y) <==> x&y
# |  
# |  __init__(...)
# |      x.__init__(...) initializes x; see x.__class__.__doc__ for signature
# |  
# |  __ior__(...)
# |      x.__ior__(y) <==> x|y
# |  
# |  __isub__(...)
# |      x.__isub__(y) <==> x-y
# |  
# |  __iter__(...)
# |      x.__iter__() <==> iter(x)
# |  
# |  __ixor__(...)
# |      x.__ixor__(y) <==> x^y
# |  
# |  __le__(...)
# |      x.__le__(y) <==> x<=y
# |  
# |  __len__(...)
# |      x.__len__() <==> len(x)
# |  
# |  __lt__(...)
# |      x.__lt__(y) <==> x<y
# |  
# |  __ne__(...)
# |      x.__ne__(y) <==> x!=y
# |  
# |  __or__(...)
# |      x.__or__(y) <==> x|y
# |  
# |  __rand__(...)
# |      x.__rand__(y) <==> y&x
# |  
# |  __reduce__(...)
# |      Return state information for pickling.
# |  
# |  __repr__(...)
# |      x.__repr__() <==> repr(x)
# |  
# |  __ror__(...)
# |      x.__ror__(y) <==> y|x
# |  
# |  __rsub__(...)
# |      x.__rsub__(y) <==> y-x
# |  
# |  __rxor__(...)
# |      x.__rxor__(y) <==> y^x
# |  
# |  __sub__(...)
# |      x.__sub__(y) <==> x-y
# |  
# |  __xor__(...)
# |      x.__xor__(y) <==> x^y
# |  
# |  add(...)
# |      Add an element to a set.
# |      
# |      This has no effect if the element is already present.
# |  
# |  clear(...)
# |      Remove all elements from this set.
# |  
# |  copy(...)
# |      Return a shallow copy of a set.
# |  
# |  difference(...)
# |      Return the difference of two sets as a new set.
# |      
# |      (i.e. all elements that are in this set but not the other.)
# |  
# |  difference_update(...)
# |      Remove all elements of another set from this set.
# |  
# |  discard(...)
# |      Remove an element from a set if it is a member.
# |      
# |      If the element is not a member, do nothing.
# |  
# |  intersection(...)
# |      Return the intersection of two sets as a new set.
# |      
# |      (i.e. all elements that are in both sets.)
# |  
# |  intersection_update(...)
# |      Update a set with the intersection of itself and another.
# |  
# |  issubset(...)
# |      Report whether another set contains this set.
# |  
# |  issuperset(...)
# |      Report whether this set contains another set.
# |  
# |  pop(...)
# |      Remove and return an arbitrary set element.
# |  
# |  remove(...)
# |      Remove an element from a set; it must be a member.
# |      
# |      If the element is not a member, raise a KeyError.
# |  
# |  symmetric_difference(...)
# |      Return the symmetric difference of two sets as a new set.
# |      
# |      (i.e. all elements that are in exactly one of the sets.)
# |  
# |  symmetric_difference_update(...)
# |      Update a set with the symmetric difference of itself and another.
# |  
# |  union(...)
# |      Return the union of two sets as a new set.
# |      
# |      (i.e. all elements that are in either set.)
# |  
# |  update(...)
# |      Update a set with the union of itself and another.
 
        # define storage for bounds and steps
        _bounds = ((None, None),)
        _openness = ((True, True),)
        _steps = (boundType(1.0),)
        # define base methods
        def __add__(self, other):
            pass
        
              
        # Now add methods of the defined class, as long as it doesn't try to redefine
        # __new__, __init__, __getattribute__ or __setitem__
        newdict = { '__slots__':[], '__dflts__':{}, '__getattribute__':__getattribute__}
        # set class tree type
        newdict['_boundType'] = boundType

        for k in classdict :
            if k in newdict :
                warnings.warn("Attribute %r is predefined in class %r of type %r and can't be overriden" % (k, classname, mcl.__name__))
            else :
                newdict[k] = classdict[k]
        
        return super(MetaRange, cls).__new__(cls, classname, bases, newdict)

# ranges of int
#class IRange(int):
#    __metaclass__ =  MetaRange        
 
# ranges of float
#class FRange(float):
#    __metaclass__ =  MetaRange  
    
# temp patch until Ranges are done   
IRange = xrange
"""
Defines arguments manipulation utilities, like checking if an argument is iterable, flattening a nested arguments list, etc.
These utility functions can be used by other util modules and are imported in util's main namespace for use by other pymel modules
"""

from collections import deque as _deque
import sys, operator, itertools

from utilitytypes import ProxyUnicode

# some functions used to need to make the difference between strings and non-string iterables when PyNode where unicode derived
# doing a hasattr(obj, '__iter__') test will fail for objects that implement __getitem__, but not __iter__, so try iter(obj)
def isIterable( obj ):
    """
    Returns True if an object is iterable and not a string or ProxyUnicode type, otherwise returns False.

    :rtype: bool"""
    if isinstance(obj,basestring): return False
    elif isinstance(obj,ProxyUnicode): return False
    try:
        iter(obj)
    except TypeError: return False
    else: return True

# consider only ints and floats numeric
def isScalar(obj):
    """
    Returns True if an object is a number or complex type, otherwise returns False.

    :rtype: bool"""
    return operator.isNumberType(obj) and not isinstance(obj,complex)

# TODO : this is unneeded as operator provides it, can call directly to operator methods
def isNumeric(obj):
    """
    Returns True if an object is a number type, otherwise returns False.

    :rtype: bool
    """
    return operator.isNumberType(obj)

def isSequence( obj ):
    """
    same as `operator.isSequenceType`

    :rtype: bool"""
    return operator.isSequenceType(obj)

def isMapping( obj ):
    """
    Returns True if an object is a mapping (dictionary) type, otherwise returns False.

    same as `operator.isMappingType`

    :rtype: bool"""
    return operator.isMappingType(obj)

clsname = lambda x:type(x).__name__

def convertListArgs( args ):
    if len(args) == 1 and isIterable(args[0]):
        return tuple(args[0])
    return args


def expandArgs( *args, **kwargs ) :
    """
    'Flattens' the arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments.

    By default will return elements depth first, from root to leaves.  Set postorder or breadth to control order.

    :Keywords:
        depth : int
            will specify the nested depth limit after which iterables are returned as they are

        type
            for type='list' will only expand lists, by default type='all' expands any iterable sequence

        postorder : bool
             will return elements depth first, from leaves to roots

        breadth : bool
            will return elements breadth first, roots, then first depth level, etc.

    For a nested list represent trees::

        a____b____c
        |    |____d
        e____f
        |____g

    preorder(default) :

        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1 )
        ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'] )
        ('a', 'b', 'c', 'd', 'e', 'f', 'g')

    postorder :

        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True, limit=1)
        ('b', ['c', 'd'], 'a', 'f', 'g', 'e')
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True)
        ('c', 'd', 'b', 'a', 'f', 'g', 'e')

    breadth :

        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1, breadth=True)
        ('a', 'e', 'b', ['c', 'd'], 'f', 'g')
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], breadth=True)
        ('a', 'e', 'b', 'f', 'g', 'c', 'd')


    Note that with default depth (unlimited) and order (preorder), if passed a pymel Tree
    result will be the equivalent of doing a preorder traversal : [k for k in iter(theTree)] """

    tpe = kwargs.get('type', 'all')
    limit = kwargs.get('limit', sys.getrecursionlimit())
    postorder = kwargs.get('postorder', False)
    breadth = kwargs.get('breadth', False)
    if tpe=='list' or tpe==list :
        def _expandArgsTest(arg): return type(arg)==list
    elif tpe=='all' :
        def _expandArgsTest(arg): return isIterable(arg)
    else :
        raise ValueError, "unknown expand type=%s" % str(tpe)

    if postorder :
        return postorderArgs (limit, _expandArgsTest, *args)
    elif breadth :
        return breadthArgs (limit, _expandArgsTest, *args)
    else :
        return preorderArgs (limit, _expandArgsTest, *args)

def preorderArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ returns a list of a preorder expansion of args """
    stack = [(x,0) for x in args]
    result = _deque()
    while stack :
        arg, level = stack.pop()
        if testFn(arg) and level<limit :
            stack += [(x,level+1) for x in arg]
        else :
            result.appendleft(arg)

    return tuple(result)

def postorderArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ returns a list of  a postorder expansion of args """
    if len(args) == 1:
        return (args[0],)
    else:
        deq = _deque((x,0) for x in args)
        stack = []
        result = []
        while deq :
            arg, level = deq.popleft()
            if testFn(arg) and level<limit :
                deq = _deque( [(x, level+1) for x in arg] + list(deq))
            else :
                if stack :
                    while stack and level <= stack[-1][1] :
                        result.append(stack.pop()[0])
                    stack.append((arg, level))
                else :
                    stack.append((arg, level))
        while stack :
            result.append(stack.pop()[0])

        return tuple(result)

def breadthArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ returns a list of a breadth first expansion of args """
    deq = _deque((x,0) for x in args)
    result = []
    while deq :
        arg, level = deq.popleft()
        if testFn(arg) and level<limit :
            for a in arg :
                deq.append ((a, level+1))
        else :
            result.append(arg)

    return tuple(result)

# Same behavior as expandListArg but implemented as an Python iterator, the recursieve approach
# will be more memory efficient, but slower
def iterateArgs( *args, **kwargs ) :
    """ Iterates through all arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments.

    By default will return elements depth first, from root to leaves.  Set postorder or breadth to control order.

    :Keywords:
        depth : int
            will specify the nested depth limit after which iterables are returned as they are

        type
            for type='list' will only expand lists, by default type='all' expands any iterable sequence

        postorder : bool
             will return elements depth first, from leaves to roots

        breadth : bool
            will return elements breadth first, roots, then first depth level, etc.

    For a nested list represent trees::

        a____b____c
        |    |____d
        e____f
        |____g

    preorder(default) :

        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1 ))
        ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'] ))
        ('a', 'b', 'c', 'd', 'e', 'f', 'g')

    postorder :

        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True, limit=1 ))
        ('b', ['c', 'd'], 'a', 'f', 'g', 'e')
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True))
        ('c', 'd', 'b', 'a', 'f', 'g', 'e')

    breadth :

        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1, breadth=True))
        ('a', 'e', 'b', ['c', 'd'], 'f', 'g')
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], breadth=True))
        ('a', 'e', 'b', 'f', 'g', 'c', 'd')

    Note that with default depth (-1 for unlimited) and order (preorder), if passed a pymel Tree
    result will be the equivalent of using a preorder iterator : iter(theTree) """

    tpe = kwargs.get('type', 'all')
    limit = kwargs.get('limit', sys.getrecursionlimit())
    postorder = kwargs.get('postorder', False)
    breadth = kwargs.get('breadth', False)
    if tpe=='list' or tpe==list :
        def _iterateArgsTest(arg): return type(arg)==list
    elif tpe=='all' :
        def _iterateArgsTest(arg): return isIterable(arg)
    else :
        raise ValueError, "unknown expand type=%s" % str(tpe)

    if postorder :
        for arg in postorderIterArgs (limit, _iterateArgsTest, *args) :
            yield arg
    elif breadth :
        for arg in breadthIterArgs (limit, _iterateArgsTest, *args) :
            yield arg
    else :
        for arg in preorderIterArgs (limit, _iterateArgsTest, *args) :
            yield arg

def preorderIterArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ iterator doing a preorder expansion of args """
    if limit :
        for arg in args :
            if testFn(arg) :
                for a in preorderIterArgs (limit-1, testFn, *arg) :
                    yield a
            else :
                yield arg
    else :
        for arg in args :
            yield arg

def postorderIterArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ iterator doing a postorder expansion of args """
    if limit :
        last = None
        for arg in args :
            if testFn(arg) :
                for a in postorderIterArgs (limit-1, testFn, *arg) :
                    yield a
            else :
                if last :
                    yield last
                last = arg
        if last :
            yield last
    else :
        for arg in args :
            yield arg

def breadthIterArgs (limit=sys.getrecursionlimit(), testFn=isIterable, *args) :
    """ iterator doing a breadth first expansion of args """
    deq = _deque((x,0) for x in args)
    while deq :
        arg, level = deq.popleft()
        if testFn(arg) and level<limit :
            for a in arg :
                deq.append ((a, level+1))
        else :
            yield arg

def preorder( iterable, testFn=isIterable, limit=sys.getrecursionlimit()):
    """ iterator doing a preorder expansion of args """
    if limit :
        for arg in iterable :
            if testFn(arg) :
                for a in preorderIterArgs (limit-1, testFn, *arg) :
                    yield a
            else :
                yield arg
    else :
        for arg in iterable :
            yield arg

def postorder( iterable, testFn=isIterable, limit=sys.getrecursionlimit()):
    """ iterator doing a postorder expansion of args """
    if limit :
        last = None
        for arg in iterable :
            if testFn(arg) :
                for a in postorderIterArgs (limit-1, testFn, *arg) :
                    yield a
            else :
                if last :
                    yield last
                last = arg
        if last :
            yield last
    else :
        for arg in iterable :
            yield arg

def breadth( iterable, testFn=isIterable, limit=sys.getrecursionlimit()):
    """ iterator doing a breadth first expansion of args """
    deq = _deque((x,0) for x in iterable)
    while deq :
        arg, level = deq.popleft()
        if testFn(arg) and level<limit :
            for a in arg :
                deq.append ((a, level+1))
        else :
            yield arg

def listForNone( res ):
    "returns an empty list when the result is None"
    if res is None:
        return []
    return res

# for discussion of implementation,
# see http://mail.python.org/pipermail/python-list/2008-January/474369.html for discussion...
def pairIter(sequence):
    '''
    Returns an iterator over every 2 items of sequence.

    ie, [x for x in pairIter([1,2,3,4])] == [(1,2), (3,4)]

    If sequence has an odd number of items, the last item will not be returned in a pair.
    '''
    theIter = iter(sequence)
    return itertools.izip(theIter,theIter)

def reorder( x, indexList=[], indexDict={} ):
    """
    Reorder a list based upon a list of positional indices and/or a dictionary of fromIndex:toIndex.

        >>> l = ['zero', 'one', 'two', 'three', 'four', 'five', 'six']
        >>> reorder( l, [1, 4] ) # based on positional indices: 0-->1, 1-->4
        ['one', 'four', 'zero', 'two', 'three', 'five', 'six']
        >>> reorder( l, [1, None, 4] ) # None can be used as a place-holder
        ['one', 'zero', 'four', 'two', 'three', 'five', 'six']
        >>> reorder( l, [1, 4], {5:6} )  # remapping via dictionary: move the value at index 5 to index 6
        ['one', 'four', 'zero', 'two', 'three', 'six', 'five']
    """

    x = list(x)
    num = len(x)
    popCount = 0
    indexValDict = {}

    for i, index in enumerate(indexList):
        if index is not None:
            val = x.pop( index-popCount )
            assert index not in indexDict, indexDict
            indexValDict[i] = val
            popCount += 1
    for k, v in indexDict.items():
        indexValDict[v] = x.pop(k-popCount)
        popCount += 1

    newlist = []
    for i in range(num):
        try:
            val = indexValDict[i]
        except KeyError:
            val = x.pop(0)
        newlist.append( val )
    return newlist

class RemovedKey(object):
    def __init__(self, oldVal):
        self.oldVal = oldVal
        
    def __eq__(self, other):
        return self.oldVal == other.oldVal
    
    def __ne__(self, other):
        return self.oldVal != other.oldVal

def compareCascadingDicts(dict1, dict2):
    '''compares two cascading dicts

    :rtype: `tuple` of (both, only1, only2, differences)
    both : `set`
        keys that were present in both (non-recursively)
        (both, only1, and only2 should be discrete partitions of all the keys
        present in both dict1 and dict2)
    only1 : `set`
        keys that were present in only1 (non-recursively)
    only2 : `set`
        keys that were present in only2 (non-recursively)
    differences : `dict`
        recursive sparse dict containing information that was 'different' in
        dict2 - either not present in dict1, or having a different value in
        dict2, or removed in dict2 (in which case an instance of 'RemovedKey'
        will be set as the value in differences)
        Values that are different, and both dictionaries, will themselves have
        sparse entries, showing only what is different
        The return value should be such that if you do if you merge the
        differences with d1, you will get d2.
    '''
    if isinstance(dict1, (list, tuple)):
        dict1 = dict(enumerate(dict1))
    if isinstance(dict2, (list, tuple)):
        dict2 = dict(enumerate(dict2))
    v1 = set(dict1)
    v2 = set(dict2)
    both = v1 & v2
    only1 = v1 - both
    only2 = v2 - both
    
    recurseTypes = (dict, list, tuple)
    differences = dict( (key, dict2[key]) for key in only2)
    differences.update( (key, RemovedKey(dict1[key])) for key in only1 )
    for key in both:
        val1 = dict1[key]
        val2 = dict2[key]
        if val1 != val2:
            if isinstance(val1, recurseTypes) and isinstance(val2, recurseTypes):
                subDiffs = compareCascadingDicts(val1, val2)[-1]
                differences[key] = subDiffs
            else:
                differences[key] = val2
    
    return both, only1, only2, differences

def mergeCascadingDicts( from_dict, to_dict, allowDictToListMerging=False,
                         allowNewListMembers=False ):
    """
    recursively update to_dict with values from from_dict.
    
    if any entries in 'from_dict' are instances of the class RemovedKey,
    then the key containing that value will be removed from to_dict
    
    if allowDictToListMerging is True, then if to_dict contains a list,
    from_dict can contain a dictionary with int keys which can be used to
    sparsely update the list.
    
    if allowNewListMembers is True, and allowDictToListMerging is also True,
    then if merging an index into a list that currently isn't long enough to
    contain that index, then the list will be extended to be long enough (with
    None inserted in any intermediate indices)
    
    Note: if using RemovedKey objects and allowDictToList merging, then only
    indices greater than all of any indices updated / added should be removed,
    because the order in which items are updated / removed is indeterminate.
    """
    listMerge = allowDictToListMerging and isinstance(to_dict, list )
    if listMerge:
        contains = lambda key: isinstance(key,int) and 0 <= key < len(to_dict)
    else:
        contains = lambda key: key in to_dict

    for key, from_val in from_dict.iteritems():
        #print key, from_val
        if contains(key):
            if isinstance(from_val, RemovedKey):
                del to_dict[key]
                continue
            to_val = to_dict[key]
            #if isMapping(from_val) and ( isMapping(to_val) or (allowDictToListMerging and isinstance(to_val, list )) ):
            if hasattr(from_val, 'iteritems') and ( hasattr(to_val, 'iteritems')
                                                    or (allowDictToListMerging and isinstance(to_val, list )) ):
                mergeCascadingDicts( from_val, to_val, allowDictToListMerging )
            else:
                to_dict[key] = from_val
        else:
            if isinstance(from_val, RemovedKey):
                continue
            if listMerge and allowNewListMembers and key >= len(to_dict):
                to_dict.extend( (None,) * (key + 1 - len(to_dict)) )
            to_dict[key] = from_val

def setCascadingDictItem( dict, keys, value ):

    currentDict = dict
    for key in keys[:-1]:
        if key not in currentDict:
            currentDict[key] = {}
        currentDict = currentDict[key]
    currentDict[keys[-1]] = value

def getCascadingDictItem( dict, keys, default={} ):

    currentDict = dict
    for key in keys[:-1]:
        if isMapping(currentDict) and key not in currentDict:
            currentDict[key] = {}
        currentDict = currentDict[key]
    try:
        return currentDict[keys[-1]]
    except KeyError:
        return default

def sequenceToSlices( intList, sort=True ):
    """convert a sequence of integers into a tuple of slice objects"""
    slices = []

    if intList:
        if sort:
            intList = sorted(intList)
        start = intList[0]
        stop = None
        step = None
        lastStep = None
        lastVal = start
        for curr in intList[1:]:
            curr = int(curr)
            thisStep = curr - lastVal
            #assert thisStep > 0, "cannot have duplicate values. pass a set to be safe"

#            print
#            print "%s -> %s" % (lastVal, curr)
#            print "thisStep", thisStep
#            print "lastStep", lastStep
#            print "step", step
#            print "lastVal", lastVal
#            print (start, stop, step)
#            print slices

            if lastStep is None:
                # we're here bc the last iteration was the beginning of a new slice
                pass
            elif thisStep > 0 and thisStep == lastStep:
                # we found 2 in a row, they are the beginning of a new slice
                # setting step indicates we've found a pattern
                #print "found a pattern on", thisStep
                step = thisStep
            else:
                if step is not None:
                    # since step is set we know a pattern has been found (at least two in a row with same step)
                    # we also know that the current value is not part of this pattern, so end the old slice at the last value
                    if step == 1:
                        newslice = slice(start, lastVal+1, None)
                    else:
                        newslice = slice(start, lastVal+1, step)
                    thisStep = None
                    start = curr
                else:
                    if lastStep == 1:
                        newslice = slice(start, lastVal+1, lastStep )
                        thisStep = None
                        start = curr
                    else:
                        newslice = slice(start, stop+1 )
                        start = lastVal

#                print "adding", newslice
                slices.append( newslice )
                # start the new

                stop = None
                step = None


            lastStep = thisStep


            stop = lastVal
            lastVal = curr

        if step is not None:
            # end the old slice
            if step == 1:
                newslice = slice(start, lastVal+1, None)
            else:
                newslice = slice(start, lastVal+1, step)

            #print "adding", newslice
            slices.append( newslice )
        else:

            if lastStep == 1:
                slices.append( slice(start, lastVal+1, lastStep ) )

            else:
                slices.append( slice(start, start+1 ) )
                if lastStep is not None:
                    slices.append( slice(lastVal, lastVal+1 ) )

    return slices

def izip_longest(*args, **kwds):
    # izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    fillvalue = kwds.get('fillvalue')
    def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
        yield counter()         # yields the fillvalue, or raises IndexError
    fillers = itertools.repeat(fillvalue)
    iters = [itertools.chain(it, sentinel(), fillers) for it in args]
    try:
        for tup in itertools.izip(*iters):
            yield tup
    except IndexError:
        pass

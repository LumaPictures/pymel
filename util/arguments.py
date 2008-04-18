"""
Defines arguments manipulation utilities, like checking if an argument is iterable, flattening a nested arguments list, etc.
These utility functions can be used by other util modules and are imported in util's main namespace for use by other pymel modules
"""

from collections import deque
import sys

def isIterable( obj ):
    return hasattr(obj,'__iter__') and not isinstance(obj,basestring)

# TODO : name probably badly chosen are there are more types considered as Sequence Types in Python
def isSequence( obj ):
    return type( obj ) is list or type( obj ) is tuple

def isMapping( obj ):
    return isinstance(obj, dict)

def convertListArgs( args ):
    if len(args) == 1 and isIterable(args[0]):
        return tuple(args[0])
    return args     

def pythonArgToMelType(arg):

    if isIterable( arg ):
        try:
            return pythonTypeToMelType( arg[0] ) + '[]'
        except IndexError:
            return 'string[]'
    if isinstance( arg, str ) : return 'string'
    elif isinstance( arg, int ) : return 'int'
    elif isinstance( arg, float ) : return 'float'
    #elif isinstnace( typ, Vector ) : return 'vector'
    #elif isinstnace( typ, Matrix ) : return 'matrix'
# Flatten a multi-list argument so that in can be passed as
# a list of arguments to a command.

def melToPythonWrapper( moduleName, funcName, procName, returnType='', evaluateInputs=True ):
    """This is a work in progress.  It generates and sources a mel procedure which wraps the passed 
    python function.  Theoretically useful for calling your python scripts in scenarios where maya
    does not yet support python callbacks, such as in batch mode.
    
    python functions feature a very versatile argument structure (typeless, variable, defaults), 
    whereas mel does not. As a result there are a number of concessions that must be made for this wrapper to work.
    
        - args without default values default to strings. If 'evaluteInputs' is True, arguments passed to the 
            wrapper procedure will have the python eval command run on them before being passed to your wrapped python
            function. This allows you to include a typecast in the string representing your arg::
                
                myWrapperProc( "int(5)" );
                
        - args with default values will be set to their mel analogue, if it exists
        - varargs : not yet implemented
        - keyword args : not likely to be implemented
    """
    
    import maya.mel as mm
    from inspect import getargspec
    
    melArgs = []
    melCompile = []

    module = __import__(moduleName, globals(), locals(), [''])
    func = getattr( module, funcName )
    getargspec( func )
    
    args, varargs, kwargs, defaults  = getargspec( func )
    try:
        ndefaults = len(defaults)
    except:
        ndefaults = 0
    
    nargs = len(args)
    offset = nargs - ndefaults
    for i, arg in enumerate(args):
    
        if i >= offset:
            melType = pythonTypeToMelType( defaults[i-offset] )
        else:
            melType = 'string' 
    
        melArgs.append( melType + ' $' + arg )
        if melType == 'string':
            compilePart = "'\" + $%s + \"'" %  arg
            if evaluateInputs and i < offset:
                compilePart = 'eval(%s)' % compilePart
            melCompile.append( compilePart )
        else:
            melCompile.append( "\" + $%s + \"" %  arg )
    
    procDef = 'global proc %s %s( %s ){ python("import %s; %s.%s(%s)");}' % (returnType, procName, ', '.join(melArgs), moduleName, moduleName, funcName, ','.join(melCompile) )
    print procDef
    mm.eval( procDef )

def expandArgs( *args, **kwargs ) :
    """ \'Flattens\' the arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments.
    Keyword arguments :
    depth :  will specify the nested depth limit after which iterables are returned as they are
    type : for type='list' will only expand lists, by default type='all' expands any iterable sequence
    order : By default will return elements depth first, from root to leaves)
            with postorder=True will return elements depth first, from leaves to roots
            with breadth=True will return elements breadth first, roots, then first depth level, etc.
    For a nested list represent trees   a____b____c
                                        |    |____d
                                        e____f
                                        |____g
    preorder(default) :
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1 )
        >>> ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'] )
        >>> ('a', 'b', 'c', 'd', 'e', 'f', 'g')
    postorder :
        >>> util.expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True, limit=1)
        >>> ('b', ['c', 'd'], 'a', 'f', 'g', 'e')
        >>> util.expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True)
        >>> ('c', 'd', 'b', 'a', 'f', 'g', 'e')        
    breadth :
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1, breadth=True)
        >>> ('a', 'e', 'b', ['c', 'd'], 'f', 'g') # 
        >>> expandArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], breadth=True)
        >>> ('a', 'e', 'b', 'f', 'g', 'c', 'd') # 
        
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
    result = deque()
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
        deq = deque((x,0) for x in args)
        stack = []
        result = []
        while deq :
            arg, level = deq.popleft()
            if testFn(arg) and level<limit :
                deq = deque( [(x, level+1) for x in arg] + list(deq))
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
    deq = deque((x,0) for x in args)
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
    Keyword arguments :
    depth :  will specify the nested depth limit after which iterables are returned as they are
    type : for type='list' will only expand lists, by default type='all' expands any iterable sequence
    order : By default will return elements depth first, from root to leaves)
            with postorder=True will return elements depth first, from leaves to roots
            with breadth=True will return elements breadth first, roots, then first depth level, etc.
    For a nested list represent trees   a____b____c
                                        |    |____d
                                        e____f
                                        |____g
    preorder(default) :
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1 ))
        >>> ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'] ))
        >>> ('a', 'b', 'c', 'd', 'e', 'f', 'g')
    postorder :
        >>> tuple(k for k in util.iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True, limit=1 ))
        >>> ('b', ['c', 'd'], 'a', 'f', 'g', 'e')
        >>> tuple(k for k in util.iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], postorder=True))
        >>> ('c', 'd', 'b', 'a', 'f', 'g', 'e')    
    breadth :
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], limit=1, breadth=True))
        >>> ('a', 'e', 'b', ['c', 'd'], 'f', 'g') # 
        >>> tuple(k for k in iterateArgs( 'a', ['b', ['c', 'd']], 'e', ['f', 'g'], breadth=True))
        >>> ('a', 'e', 'b', 'f', 'g', 'c', 'd') #         
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
    deq = deque((x,0) for x in args)
    while deq :
        arg, level = deq.popleft()
        if testFn(arg) and level<limit :
            for a in arg :
                deq.append ((a, level+1))
        else :
            yield arg
        
def listForNone( res ):
    if res is None:
        return []
    return res
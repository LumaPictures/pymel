"""
Defines arguments manipulation utilities, like checking if an argument is iterable, flattening a nested arguments list, etc.
These utility functions can be used by other util modules and are imported in util's main namespace for use by other pymel modules
"""

from collections import deque
import inspect, sys
import maya.mel as _mm
from arrays import Vector, Matrix

# some functions used to need to make the difference between strings and non-string iterables when PyNode where unicode derived
def isIterable( obj ):
    return hasattr(obj,'__iter__') and not isinstance(obj,basestring)

# consider only ints and floats numeric
def isScalar(obj):
    return isinstance(obj,int) or isinstance(obj,float)

def isNumeric(obj):
    return isinstance(obj,int) or isinstance(obj,float) or isinstance(obj,long) or isinstance(obj,complex) or isinstance(obj,bool)

# TODO : name probably badly chosen are there are more types considered as Sequence Types in Python
def isSequence( obj ):
    return type( obj ) is list or type( obj ) is tuple

def isMapping( obj ):
    return isinstance(obj, dict)

clsname = lambda x:type(x).__name__

MELTYPES = ['string', 'string[]', 'int', 'int[]', 'float', 'float[]', 'vector', 'vector[]']

def isValidMelType( typStr ):
    return typStr in MELTYPES
   
def convertListArgs( args ):
    if len(args) == 1 and isIterable(args[0]):
        return tuple(args[0])
    return args     

def getMelType( pyObj=None, pyType=None, melVariable=None, exactMelType=False):
    """return the mel type of the passed argument.
    
    When passed a PyObj the command will determine the closest mel type equivalent for a python object
    
    When passed a melVariable, the command will determine the mel type from a mel variable ( ex. '$foo' )
    
    If exactMelType is True, the type will be converted to mel, and if no suitable mel analogue can be found, the function will return None.
    If False, types which do not have an exact mel analogue will return a string representing the python type

    """

    typeStrMap = {   
                 'Vector' : 'vector',
                 'unicode': 'string',
                 'str'    : 'string'
                           }
 
    if pyType is not None:
        assert melVariable is None and pyObj is None, "Please pass only one of pyObj, pyType or melVariable"
    
        if not exactMelType:
            if not isinstance( pyType, basestring ): pyType = pyType.__name__
            return typeStrMap.get(pyType, pyType)   
            
        else:
            if issubclass( pyObj, basestring ) : return 'string'
            #elif not boolIsInt and isinstance( arg, bool ) : return 'bool'
            elif issubclass( pyObj, int ) : return 'int'
            elif issubclass( pyObj, float ) : return 'float'         
            elif issubclass( pyObj, Vector ) : return 'vector'
            elif issubclass( pyObj, Matrix ) : return 'matrix'
            
    elif melVariable is not None:
        assert pyType is None and pyObj is None, "Please pass only one of pyObj, pyType or melVariable"
        if not melVariable.startswith('$'): melVariable = '$' + melVariable
         
        buf = _mm.eval( 'whatIs "%s"' % melVariable ).split()
        try:
            if buf[1] == 'variable':
                return buf[0]
        except: return
    else:
        assert pyType is None and melVariable is None, "Please pass only one of pyObj, pyType or melVariable"
        
        if not exactMelType:
            typeStr = type(pyObj).__name__
            typeStr = typeStrMap.get(typeStr, typeStr)
            return typeStr
        
        else:    
            if isIterable( pyObj ):
                try:
                    return getMelTypeFromPyObj( arg[0] ) + '[]'
                except IndexError:
                    return 'string[]'
                except:
                    return
            if isinstance( pyObj, basestring ) : return 'string'
            #elif not boolIsInt and isinstance( arg, bool ) : return 'bool'
            elif isinstance( pyObj, int ) : return 'int'
            elif isinstance( pyObj, float ) : return 'float'         
            elif isinstance( pyObj, Vector ) : return 'vector'
            elif isinstance( pyObj, Matrix ) : return 'matrix'


def _getFunction( function ):
    # function is a string, so we must import its module and get the function object
    if isinstance( function, basestring):
        buf = function.split()
        funcName = buf.pop(-1)
        moduleName = '.'.join(buf)
        module = __import__(moduleName, globals(), locals(), [''])
        func = getattr( module, funcName )
    # function is a python object    
    elif callable( function ) :
        func = function  
    else:
        raise TypeError, "argument must be a callable python object or the full, dotted path to the callable object as a string."
    
    return func


# Flatten a multi-list argument so that in can be passed as
# a list of arguments to a command.

def getMelArgs( function, exactMelType=True ):
    """
    given a python function, return a tuple of ( ( argName, melType ), { argName : default }, { argName : description } )
    
        function
        This can be a callable python object or the full, dotted path to the callable object as a string.  
        
        If a string representing the python object is passed, it should include all packages and sub-modules, along 
        with the function's name:  'path.to.myFunc'
        
    """

   
    from inspect import getargspec
    
    melArgs = []
    melArgDefaults = {}
    
    parsedTypes = {}
    parsedDescr = {}
   
    function = _getFunction( function )
    
    funcName = function.__name__
    moduleName = function.__module__    

    args, varargs, kwargs, defaults  = getargspec( function )
    
    # epydoc docstring parsing
    try:
        import epydoc.docbuilder
    except ImportError:
        pass
    else:
        try:
            docindex = epydoc.docbuilder.build_doc_index( [moduleName], parse=True, introspect=True, add_submodules=False)
            linker = epydoc.markup.DocstringLinker()
            api_doc = docindex.get_valdoc( moduleName + '.' + funcName )
        except Exception, msg:
            print "epydoc parsing failed: %s" % msg
        else:
            arg_types = api_doc.arg_types
            #print api_doc.arg_descrs
            #print arg_types
            for arg, descr in api_doc.arg_descrs: 
                # filter out args that are not actually in our function.  that means currently no support for *args and **kwargs
                # not yet sure why, but the keys to arg_types are lists
                arg = arg[0]
                if arg in args: # or kwargs:
                    parsedDescr[arg] = descr.to_plaintext( linker )
                    try:
                        argtype = arg_types[ arg ].to_plaintext( linker )
                        parsedTypes[arg] = getMelType( pyType=argtype, exactMelType=exactMelType )
                        #print arg, argtype, parsedTypes.get(arg)
                    except KeyError: pass
            
    
    try:
        ndefaults = len(defaults)
    except:
        ndefaults = 0
    
    #print args, varargs, kwargs, defaults
    
    nargs = len(args)
    offset = nargs - ndefaults
    for i, arg in enumerate(args):
    
        if i >= offset:
            # keyword args with defaults
            default = defaults[i-offset]
            melType = getMelType( pyObj=default, exactMelType=exactMelType )
            # a mel type of None means there is no mel analogue for this python object
#            if not isValidMelType( melType ):
#                # if it's None, then we go to parsed docs
#                if melType is None:
#                    melType = parsedTypes.get( arg, None )
#                try:
#                    default = default.__repr__()
#                except AttributeError:
#                    default = str(default)
            melArgDefaults[arg] = default
        else:
            # args without defaults
            # a mel type of None means there is no mel analogue for this python object
            melType = parsedTypes.get( arg, None )
    
        melArgs.append( ( arg, melType ) )
    
    return tuple(melArgs), melArgDefaults, parsedDescr

def melToPythonWrapper( function, returnType='', procName=None, evaluateInputs=True ):
    """This is a work in progress.  It generates and sources a mel procedure which wraps the passed 
    python function.  Theoretically useful for calling your python scripts in scenarios where maya
    does not yet support python callbacks, such as in batch mode.
    
    The function is inspected in order to generate a mel procedure which relays its
    arguments on to the python function.  However, Python feature a very versatile argument structure whereas 
    mel does not. 
    
        - python args with default values (keyword args) will be set to their mel analogue, if it exists. 
        - normal python args without default values default to strings. If 'evaluteInputs' is True, string arguments passed to the 
            mel wrapper proc will be evaluated as python code before being passed to your wrapped python
            function. This allows you to include a typecast in the string representing your arg::
                
                myWrapperProc( "Transform('perp')" );
                
        - *args : not yet implemented
        - **kwargs : not likely to be implemented
        
     
    function
        This can be a callable python object or the full, dotted path to the callable object as a string.  
        
        If passed as a python object, the object's __name__ and __module__ attribute must point to a valid module
        where __name__ can be found. 
        
        If a string representing the python object is passed, it should include all packages and sub-modules, along 
        with the function's name:  'path.to.myFunc'
        
    procName
        Optional name of the mel procedure to be created.  If None, the name of the function will be used.
    
    evaluateInputs
        If True (default), string arguments passed to the generated mel procedure will be evaluated as python code, allowing
        you to pass a more complex python objects as an argument. For example:
        
        In python:         
            >>> import pymel
            >>> def myFunc( arg ): for x in arg: print x
            >>> pymel.util.melToPythonWrapper( myFunc, procName='myFuncWrapper', evaluateInputs=True )
        
        Then, in mel::
            // execute the mel-to-python wrapper procedure
            myFuncWrapper("[ 1, 2, 3]");
    
        the string "[1,2,3]" will be converted to a python list [1,2,3] before it is executed by the python function myFunc
    """
    
    function = _getFunction( function )
    
    funcName = function.__name__
    moduleName = function.__module__ 

        
    melCompile = []
    melArgs = []
    argList, defaults, description = getMelArgs(function)
    for arg, melType in argList:
        
        if melType == 'string':
            compilePart = "'\" + $%s + \"'" %  arg
            melCompile.append( compilePart )
        elif melType == None:
            melType = 'string'
            compilePart = "'\" + $%s + \"'" %  arg
            compilePart = r'eval(\"\"\"%s\"\"\")' % compilePart
            melCompile.append( compilePart )
        else:
            melCompile.append( "\" + $%s + \"" %  arg )
        melArgs.append( melType + ' $' + arg )
         
    if procName is None:
        procName = funcName 
        
    procDef = 'global proc %s %s( %s ){ python("import %s; %s.%s(%s)");}' % ( returnType, 
                                                                        procName,
                                                                        ', '.join(melArgs), 
                                                                        moduleName, 
                                                                        moduleName, 
                                                                        funcName, 
                                                                        ','.join(melCompile) )
#    procDef = 'global proc %s %s( %s ){ python("import %s; %s.%s(%s)");}' % ( returnType, 
#                                                                                          procName, 
#                                                                                          ', '.join(melArgs), 
#                                                                                          procName, moduleName, 
#                                                                                          moduleName, 
#                                                                                          funcName,
#                                                                                          ','.join(melCompile) )

    print procDef
    _mm.eval( procDef )
    return procName

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
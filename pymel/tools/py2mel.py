
import maya.mel as _mm
import inspect
from pymel.util.arrays import VectorN, MatrixN
from pymel.core.language import getMelType

import pymel.util as util


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
    given a python function, return ( ( argName, melType ), { argName : default }, { argName : description } )
    
        function
        This can be a callable python object or the full, dotted path to the callable object as a string.  
        
        If a string representing the python function is passed, it should include all packages and sub-modules, along 
        with the function's name:  'path.to.myFunc'
        
    """
    
    melArgs = []
    melArgDefaults = {}
    
    parsedTypes = {}
    parsedDescr = {}
   
    function = _getFunction( function )
    
    funcName = function.__name__
    moduleName = function.__module__    

    args, varargs, kwargs, defaults  = inspect.getargspec( function )
    
#    # epydoc docstring parsing
#    try:
#        import epydoc.docbuilder
#    except ImportError:
#        pass
#    else:
#        try:
#            docindex = epydoc.docbuilder.build_doc_index( [moduleName], parse=True, introspect=True, add_submodules=False)
#            linker = epydoc.markup.DocstringLinker()
#            api_doc = docindex.get_valdoc( moduleName + '.' + funcName )
#        except Exception, msg:
#            print "epydoc parsing failed: %s" % msg
#        else:
#            arg_types = api_doc.arg_types
#            #print api_doc.arg_descrs
#            #print arg_types
#            for arg, descr in api_doc.arg_descrs: 
#                # filter out args that are not actually in our function.  that means currently no support for *args and **kwargs
#                # not yet sure why, but the keys to arg_types are lists
#                arg = arg[0]
#                if arg in args: # or kwargs:
#                    parsedDescr[arg] = descr.to_plaintext( linker )
#                    try:
#                        argtype = arg_types[ arg ].to_plaintext( linker )
#                        parsedTypes[arg] = getMelType( pyType=argtype, exactMelType=exactMelType )
#                        #print arg, argtype, parsedTypes.get(arg)
#                    except KeyError: pass
            
    
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
            melType = getMelType( default, exactOnly=exactMelType )
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

def py2melProc( function, returnType='', procName=None, evaluateInputs=True ):
    """This is a work in progress.  It generates and sources a mel procedure which wraps the passed 
    python function.  Theoretically useful for calling your python scripts in scenarios where Maya
    does not yet support python callbacks.
    
    The function is inspected in order to generate a MEL procedure which relays its
    arguments on to the python function.  However, Python features a very versatile argument structure whereas 
    MEL does not. 
    
        - python args with default values (keyword args) will be set to their MEL analogue, if it exists. 
        - normal python args without default values default to strings. If 'evaluteInputs' is True, string arguments passed to the 
            MEL wrapper proc will be evaluated as python code before being passed to your wrapped python
            function. This allows you to include a typecast in the string representing your arg::
                
                myWrapperProc( "Transform('persp')" );
                
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
            >>> import pymel.tools.py2mel as py2mel
            >>> def myFunc( arg ): 
            ...    for x in arg:
            ...       print x
            >>> py2mel.py2melProc( myFunc, procName='myFuncWrapper', evaluateInputs=True )
        
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
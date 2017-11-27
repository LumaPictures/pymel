"""
General utility functions that are not specific to Maya Commands or the 
OpenMaya API.

Note:
By default, handlers are installed for the root logger.  This can be overriden
with env var MAYA_DEFAULT_LOGGER_NAME.
Env vars MAYA_GUI_LOGGER_FORMAT and MAYA_SHELL_LOGGER_FORMAT can be used to 
override the default formatting of logging messages sent to the GUI and 
shell respectively.

"""

# Note that several of the functions in this module are implemented in C++
# code, such as executeDeferred and executeInMainThreadWithResult
 
def runOverriddenModule(modName, callingFileFunc, globals):
    '''Run a module that has been 'overriden' on the python path by another module.

    Ie, if you have two modules in your python path named 'myModule', this can
    be used to execute the code in the myModule that is LOWER in priority on the
    sys.path (the one that would normally not be found).

    Intended to be used like:

    >> import maya.utils
    >> maya.utils.runOverriddenModule(__name__, lambda: None, globals())

    Note that if modName is a sub-module, ie "myPackage.myModule", then calling
    this function will cause "myPackage" to be imported, in order to determine
    myPackage.__path__ (though in most circumstances, it will already have
    been).

    Parameters
    ----------
    modName : str
        The name of the overriden module that you wish to execute
    callingFileFunc : function
        A function that is defined in the file that calls this function; this is
        provided solely as a means to identify the FILE that calls this
        function, through the use of inspect.getsourcefile(callingFileFunc).
        This is necessary because it is possible for this call to get "chained";
        ie, if you have path1/myMod.py, path2/myMod.py, and path3/myMod.py,
        which will be found on the sys.path in that order when you import myMod,
        and BOTH path1/myMod.py AND path2/myMod.py use runOverriddenModule, then
        the desired functionality would be: path1/myMod.py causes
        path2/myMod.py, which causes path3/myMod.py to run.  However, if
        runOverriddenModule only had __name__ (or __file__) to work off of,
        path2/myMod.py would still "think" it was executing in the context of
        path1/myMod.py... resulting in an infinite loop when path2/myMod.py
        calls runOverriddenModule. This parameter allows runOverriddenModule to
        find the "next module down" on the system path. If the file that
        originated this function is NOT found on the system path, an ImportError
        is raised.
    globals : dict
        the globals that the overridden module should be executed with

    Returns
    -------
    str
        The filepath that was executed
    '''
    import inspect
    import os.path
    import sys
    import imp

    try:
        from os.path import samefile
    except ImportError:
        # os.samefile does not exist on Windows (as of Python version < 3k)
        # WARNING: Resorting to a less than ideal method to checking for same file
        # TODO: Add deeper implementation of the samefile hack for windows
        # in future, if possible.
        def samefile(p1, p2):
            return os.stat(p1) == os.stat(p2)

    callingFile = inspect.getsourcefile(callingFileFunc)

    # because the same path might be in the sys.path twice, resulting
    # in THIS EXACT FILE showing up in the search path multiple times, we
    # need to continue until we know the next found path is not this one - or
    # any other path already found by runOverriddenModule.

    # ie, suppose we have TWO modules which both use runOverriddenModule, A
    # and B, and one "base" module they override, C.  Then suppose our sys.path
    # would cause them to be discovered in this order: [A, B, B, A, C].
    # We need to make sure that we get to C even in this scenario! To do this,
    # we store already-executed paths in the globals...

    executedFiles = globals.get('_runOverriddenModule_already_executed')
    if executedFiles is None:
        executedFiles = set()
        globals['_runOverriddenModule_already_executed'] = executedFiles
    executedFiles.add(callingFile)


    # first, determine the path to search for the module...
    packageSplit = modName.rsplit('.', 1)
    if len(packageSplit) == 1:
        # no parent package: use sys.path
        path = sys.path
        baseModName = modName
    else:
        # import the parent package (if any), in order to find it's __path__
        packageName, baseModName = packageSplit
        packageMod = __import__(packageName, fromlist=[''], level=0)
        path = packageMod.__path__

    # now, find which path would result in the callingFile... safest way to do
    # this is with imp.find_module... but we need to know WHICH path caused
    # the module to be found, so we go one-at-a-time...

    for i, dir in enumerate(path):
        dir = path[i]
        try:
            findResults = imp.find_module(baseModName, [dir])
        except ImportError:
            continue
        # close the open file handle..
        if isinstance(findResults[0], file):
            findResults[0].close()
        # ...then check if the found file matched the callingFile
        if any(samefile(findResults[1], oldFile)
               for oldFile in executedFiles):
            continue
        else:
            break
    else:
        # we couldn't find the file - raise an ImportError
        raise ImportError("Couldn't find a version of the file %r that hadn't "
                          "already been executed when using path %r"
                          % (callingFile, path))

    execfile(findResults[1], globals)
    return findResults[1]

# first, run the "real" maya.utils...

runOverriddenModule(__name__, lambda: None, globals())

# ...then monkey patch it!

# first, allow setting of the stream for the shellLogHandler based on an env.
# variable...

_origShellLogHandler = shellLogHandler

def shellLogHandler(*args, **kwargs):
    handler = _origShellLogHandler(*args, **kwargs)
    shellStream = os.environ.get('MAYA_SHELL_LOGGER_STREAM')
    if shellStream is not None:
        shellStream = getattr(sys, shellStream, None)
        if shellStream is not None:
            handler.stream = shellStream
    return handler

# ...then, override the formatGuiException method to better deal with IOError /
# OSError formatting

def formatGuiException(exceptionType, exceptionObject, traceBack, detail=2):
    """
    Format a trace stack into a string.

        exceptionType   : Type of exception
        exceptionObject : Detailed exception information
        traceBack       : Exception traceback stack information
        detail          : 0 = no trace info, 1 = line/file only, 2 = full trace
                          
    To perform an action when an exception occurs without modifying Maya's 
    default printing of exceptions, do the following::
    
        import maya.utils
        def myExceptCB(etype, value, tb, detail=2):
            # do something here...
            return maya.utils._formatGuiException(etype, value, tb, detail)
        maya.utils.formatGuiException = myExceptCB
        
    """
    # originally, this code used
    #    exceptionMsg = unicode(exceptionObject.args[0])
    # Unfortunately, the problem with this is that the first arg is NOT always
    # the string message - ie, witness
    #    IOError(2, 'No such file or directory', 'non_existant.file')
    # So, instead, we always just use:
    #    exceptionMsg = unicode(exceptionObject).strip()
    # Unfortunately, for python 2.6 and before, this has some issues:
    #    >>> str(IOError(2, 'foo', 'bar'))
    #    "[Errno 2] foo: 'bar'"
    #    >>> unicode(IOError(2, 'foo', 'bar'))
    #    u"(2, 'foo')"
    # However, 2014+ uses 2.7, and even for 2013, "(2, 'foo')" is still better
    # than just "2"...

    if issubclass(exceptionType, SyntaxError):
        # syntax errors are unique, in that str(syntaxError) will include line
        # number info, which is what detail == 0 is trying to avoid...
        exceptionMsg = unicode(exceptionObject.args[0])
    else:
        exceptionMsg = unicode(exceptionObject).strip()
    if detail == 0:
        result = exceptionType.__name__ + ': ' + exceptionMsg
    else:
        # extract a process stack from the tracekback object
        tbStack = traceback.extract_tb(traceBack)
        tbStack = _fixConsoleLineNumbers(tbStack)
        if detail == 1:
            # format like MEL error with line number
            if tbStack:
                file, line, func, text = tbStack[-1]
                result = u'%s: file %s line %s: %s' % (exceptionType.__name__, file, line, exceptionMsg)
            else:
                result = exceptionMsg
        else: # detail == 2
            # format the exception
            excLines = _decodeStack(traceback.format_exception_only(exceptionType, exceptionObject))
            # traceback may have failed to decode a unicode exception value
            # if so, we will swap the unicode back in
            if len(excLines) > 0:
                excLines[-1] = re.sub(r'<unprintable.*object>', exceptionMsg, excLines[-1])
            # format the traceback stack
            tbLines = _decodeStack( traceback.format_list(tbStack) )
            if len(tbStack) > 0:
                tbLines.insert(0, u'Traceback (most recent call last):\n')

            # prefix the message to the stack trace so that it will be visible in
            # the command line
            result = ''.join( _prefixTraceStack([exceptionMsg+'\n'] + tbLines + excLines) )
    return result

# store a local unmodified copy
_formatGuiException = formatGuiException
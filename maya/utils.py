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

    callingFile = inspect.getsourcefile(callingFileFunc)

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
        try:
            findResults = imp.find_module(baseModName, [dir])
        except ImportError:
            continue
        # close the open file handle..
        if isinstance(findResults[0], file):
            findResults[0].close()
        # ...then check if the found file matched the callingFile
        if os.path.samefile(findResults[1], callingFile):
            break
    else:
        # we couldn't find the file - raise an ImportError
        raise ImportError("Couldn't find the file %r when using path %r"
                          % (callingFile, path))

    # ok, we found the previous file on the path, now strip out everything from
    # that path and before...
    newPath = path[i + 1:]

    # find the new location of the module, using our shortened path...
    findResults = imp.find_module(baseModName, newPath)
    if isinstance(findResults[0], file):
        findResults[0].close()

    execfile(findResults[1], globals)
    return findResults[1]

import logging
import os
import re
import sys
import traceback
import pydoc
import inspect
from maya import cmds

_shellLogHandler = None
_guiLogHandler = None

appLoggerName = os.environ.get('MAYA_DEFAULT_LOGGER_NAME', '')

def loadStringResourcesForFile( scriptPath, resourceFileName ):
    """
    Load a string resource.
    
    The 'scriptPath' argument must be a string containing the full path of to 
    a language resource file. The 'resourceFileName' is the _res.py that must be loaded.
    
    If the _res.py fails to be found or executed successfully, the method returns False.
    Otherwise it returns True.
    """
    if scriptPath != '':
        localizedPath = os.path.join( scriptPath, 'scripts', resourceFileName )
        try:
            execfile( localizedPath, {} )
        
        # We don't generate any warnings or errors if localized
        # file is not there
        # TODO: we could consider issuing a warning in debug mode
        except IOError:
            pass
            return False
        except Exception, err:
            raise RuntimeError( 'Unexpected error encountered when attempting to load localized string resources for module %s:\n%s' % (moduleName,err))
            return False

        return True

    else:
        return False
			
def loadStringResourcesForModule( moduleName ):
    """
    Load the string resources associated with the given module
    
    Note that the argument must be a string containing the full name of the 
    module (eg "maya.app.utils").  The module of that name must have been 
    previously imported.
    
    The base resource file is assumed to be in the same location as the file
    defining the module and will have the same name as the module except with
    _res.py appended to it.  So, for the module foo, the resource file should
    be foo_res.py.  
    
    If Maya is running in localized mode, then the standard location for 
    localized scripts will also be searched (the location given by the 
    command cmds.about( localizedResourceLocation=True ))
    
    Failure to find the base resources for the given module will trigger an 
    exception. Failure to find localized resources is not an error.
    """
    try:
        module = sys.modules[moduleName]
    except:
        raise RuntimeError( 'Failed to load base string resources for module %s because it has not been imported' % moduleName )
        
    modulePath, moduleFileName = os.path.split( module.__file__ )
    moduleName, extension = os.path.splitext( moduleFileName )
    
    resourceFileName = moduleName + '_res.py'
    
    # Try to find the base version of the file next to the module
    try:
        baseVersionPath = os.path.join( modulePath, resourceFileName )
        execfile( baseVersionPath, {} )
    except Exception, err:
        raise RuntimeError( 'Failed to load base string resources for module %s:\n%s' % (moduleName,err))
    
    if cmds.about( uiLanguageIsLocalized=True ):
        scriptPath = cmds.about( localizedResourceLocation=True )
        if loadStringResourcesForFile(scriptPath, resourceFileName):
            return
		
        separator = ':'
        if cmds.about(win=True):
            separator = ';'
			
        pluginResourcePathEnvironmentVariable = os.environ.get('MAYA_PLUG_IN_RESOURCE_PATH')
        pluginResourcePaths = pluginResourcePathEnvironmentVariable.split(separator)
        for pluginResourcePath in pluginResourcePaths :
            if loadStringResourcesForFile(pluginResourcePath, resourceFileName):
                return
            # On a mac, we need to also look in the .lproj equivalent folder
            if cmds.about(mac=True):
                if loadStringResourcesForFile(pluginResourcePath + ".lproj", resourceFileName):
                    return
				
				
def getPossibleCompletions(input):
    """
    Utility method to handle command completion
    Returns in a list all of the possible completions that apply
    to the input string
    """
    
    import sys
    import rlcompleter
    completer = rlcompleter.Completer()

    listOfMatches=[]
    try:
        for index in xrange(sys.maxint):
            term = completer.complete(input, index)
            if term is None:
                break
            # avoid duplicate entries
            if len(listOfMatches) and listOfMatches[-1] == term:
                continue
            listOfMatches.append(term)
    except:
        pass
    
    return listOfMatches

def helpNonVerbose(thing, title='Python Library Documentation: %s', forceload=0):
    """
    Utility method to return python help in the form of a string
    
    thing - str or unicode name to get help on
    title - format string for help result
    forceload - argument to pydoc.resolve, force object's module to be reloaded from file
    
    returns formated help string 
    """
    result = ""
    try:
        thingStr = thing.encode(cmds.about(codeset=True))
    except:
        thingStr = str(thing)

    try:
        # Possible two-stage object resolution!
        # Sometimes we get docs for strings, other times for objects
        #
        try:
            object, name = pydoc.resolve(thingStr, forceload)
        except:
            # Get an object from a string
            thingObj=eval(thingStr,sys.modules['__main__'].__dict__)
            object, name = pydoc.resolve(thingObj, forceload)
        desc = pydoc.describe(object)
        module = inspect.getmodule(object)
        if name and '.' in name:
            desc += ' in ' + name[:name.rfind('.')]
        elif module and module is not object:
            desc += ' in module ' + module.__name__
        doc = None
        text = pydoc.TextDoc()        
        if not (inspect.ismodule(object) or
                inspect.isclass(object) or
                inspect.isroutine(object) or
                inspect.isgetsetdescriptor(object) or
                inspect.ismemberdescriptor(object) or
                isinstance(object, property)):
            # If the passed object is a piece of data or an instance,
            # document its available methods instead of its value.
            object = type(object)
            desc += ' object'
        # if the object is a maya command without a proper docstring,
        # then tack on the help for it
        elif module is cmds and inspect.isroutine(object): 
            try:
                if len(object.__doc__) == 0:
                    doc = cmds.help(object.__name__)
            except:
                pass
        if not doc:
            doc = text.document(object, name)
        result = pydoc.plain(title % desc + '\n\n' + doc)
        
        # Remove multiple empty lines
        result = "\n".join([ line for line in result.splitlines() if line.strip()])
    except:
        pass
    return result

# ##############################################################################
# Logging 
#

class MayaGuiLogHandler(logging.Handler):
    """
    A python logging handler that displays error and warning
    records with the appropriate color labels within the Maya GUI
    """
    def emit(self, record):
        from maya import OpenMaya
        msg = self.format(record)
        if record.levelno > logging.WARNING:
            # Error (40) Critical (50)
            OpenMaya.MGlobal.displayError(msg)
        elif record.levelno > logging.INFO:
            # Warning (30)
            OpenMaya.MGlobal.displayWarning(msg)
        else:
            # Debug (10) and Info (20) 
            OpenMaya.MGlobal.displayInfo(msg)

def guiLogHandler():
    """
    Adds an additional handler to the root logger to print to
    the script editor.  Sets the shell/outputWindow handler to
    only print 'Critical' records, so that the logger's primary
    output is the script editor.
    Returns the handler.
    """
    global _guiLogHandler
    if _guiLogHandler is not None:
        return _guiLogHandler
    if _shellLogHandler is None:
        shellLogHandler()
    _shellLogHandler.setLevel(logging.CRITICAL)
    _guiLogHandler = MayaGuiLogHandler()
    format = os.environ.get('MAYA_GUI_LOGGER_FORMAT', '%(name)s : %(message)s')
    _guiLogHandler.setFormatter( logging.Formatter(format) )
    log = logging.getLogger(appLoggerName)
    log.addHandler(_guiLogHandler)
    return _guiLogHandler

def shellLogHandler():
    """
    Adds an additional handler to the root logger to print to sys.__stdout__
    Returns the handler.
    """
    global _shellLogHandler
    if _shellLogHandler is not None:
        return _shellLogHandler
    shellStream = os.environ.get('MAYA_SHELL_LOGGER_STREAM', '__stdout__')
    shellStream = getattr(sys, shellStream, sys.__stdout__)
    _shellLogHandler = logging.StreamHandler(shellStream)
    format = os.environ.get('MAYA_SHELL_LOGGER_FORMAT', '%(name)s : %(levelname)s : %(message)s')
    _shellLogHandler.setFormatter( logging.Formatter(format) )
    log = logging.getLogger(appLoggerName)
    log.addHandler(_shellLogHandler)
    log.setLevel(logging.INFO)
    return _shellLogHandler

# ##############################################################################
# Gui Exception Handling 
#

def _guiExceptHook( exceptionType, exceptionObject, traceBack, detail=2 ):
    """
    Whenever Maya receives an error from the command engine it comes into here
    to format the message for display. 
    Formatting is performed by formatGuiException.
        exceptionType   : Type of exception
        exceptionObject : Detailed exception information
        traceBack       : Exception traceback stack information
        detail          : 0 = no trace info, 1 = line/file only, 2 = full trace
    """
    try:
        return formatGuiException(exceptionType, exceptionObject, traceBack, detail)
    except:
        # get the stack and remove our current level
        etype, value, tb = sys.exc_info()
        tbStack = traceback.extract_tb(tb)
        del tb # see warning in sys.exc_type docs for why this is deleted here

        tbLines = []
        tbLines.append("Error in  maya.utils._guiExceptHook:\n")
        tbLines += traceback.format_list( tbStack[1:] ) + traceback.format_exception_only(etype, value)
        
        tbLines.append("\nOriginal exception was:\n")
        tbLines += traceback.format_exception(exceptionType, exceptionObject, traceBack)
        tbLines = _prefixTraceStack(tbLines)
        return ''.join(tbLines)

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

# ###############################################################################
# Formatting helpers

def _prefixTraceStack(tbStack, prefix = '# '):
    """
    prefix with '#', being sure to get internal newlines. do not prefix first line
    as that will be added automatically.
    """
    result = ''.join(tbStack).rstrip().split('\n')
    size = len(result)-1
    for i, line in enumerate(result):
        if i < size:
            line += '\n'
        if i != 0:
            line = prefix + line
        result[i] = line
    return result

def _fixConsoleLineNumbers( tbStack ):
    result = []
    for file, line, func, text in tbStack:
        if file == '<maya console>':
            # In the Maya console the numbering is off by one so adjust
            line -= 1
        result.append( (file, line, func, text) )
    return result

def _decodeStack( tbStack ):
    encoding = cmds.about(codeset=True)
    return [ s.decode(encoding) for s in tbStack ]

# ###############################################################################
# Gui Results Formatting
#
def _guiResultHook(obj):
    """
    In GUI mode, called by the command engine to stringify a result for display.
    """
    return formatGuiResult(obj)

def formatGuiResult(obj):
    """
    Gets a string representation of a result object.

    To perform an action when a result is about to returned to the script editor
    without modifying Maya's default printing of results, do the following:
    
        import maya.utils
        def myResultCallback(obj):
            # do something here...
            return maya.utils._formatGuiResult(obj)
        maya.utils.formatGuiResult = myResultCallback
    """
    if isinstance(obj, str) or isinstance(obj, unicode):
        return obj
    else:
        return repr(obj)

# store a local unmodified copy
_formatGuiResult = formatGuiResult

# crash handling
def _dumpCurrentFrames():
	result = ''
	stack = inspect.stack( 1 )
	for s in reversed( stack[1:] ):
		frame = s[0]
		filename = s[1]
		line = s[2]
		function = s[3]
		context = s[4]
		vals = inspect.getargvalues( frame )
		args = inspect.formatargvalues( vals.args, vals.varargs, vals.keywords, vals.locals )
		result += '  File: "' + filename + '", line ' + str(line) + ', in ' + function + args + '\n'
		if not context == None:
			result += context[0]

	return result
# Copyright (C) 1997-2014 Autodesk, Inc., and/or its licensors.
# All rights reserved.
#
# The coded instructions, statements, computer programs, and/or related
# material (collectively the "Data") in these files contain unpublished
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its licensors,
# which is protected by U.S. and Canadian federal copyright law and by
# international treaties.
#
# The Data is provided for use exclusively by You. You have the right to use,
# modify, and incorporate this Data into other products for purposes authorized 
# by the Autodesk software license agreement, without fee.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. AUTODESK
# DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTIES
# INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF NON-INFRINGEMENT,
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR ARISING FROM A COURSE 
# OF DEALING, USAGE, OR TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS
# LICENSORS BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK AND/OR ITS
# LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY OR PROBABILITY OF SUCH DAMAGES.


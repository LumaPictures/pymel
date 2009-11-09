
"""
General utility functions that are not specific to the Maya Command or the 
OpenMaya API.
"""

# Note that several of the functions in this module are implemented in C++
# code, such as executeDeferred and executeInMainThreadWithResult

import os, warnings, sys, logging, traceback
from maya import cmds

_shellLogHandler = None
_guiLogHandler = None

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
    except:
        raise RuntimeError( 'Failed to load base string resources for module %s' % moduleName )
    
    if cmds.about( uiLanguageIsLocalized=True ):
        scriptPath = cmds.about( localizedResourceLocation=True )
        if scriptPath != '':
            localizedPath = os.path.join( scriptPath, 'scripts', resourceFileName )
            try:
                execfile( localizedPath, {} )
            # We don't generate any warnings or errors if localized
            # file is not there
            # TODO: we could consider issuing a warning in debug mode
            except IOError:
                pass
            except Exception, err:
                raise RuntimeError( 'Unexpected error encountered when attempting to load localized string resources for module %s: %s' % (moduleName,err) )

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
            listOfMatches.append(term)
    except:
        pass
    
    return listOfMatches

def helpNonVerbose(thing, title='Python Library Documentation: %s', forceload=0):
    """
    Utility method to return python help in the form of a string
    (based on the code in pydoc.py)
    Note: only a string (including unicode) should be passed in for "thing"
    """
    
    import pydoc as pydocs
    import inspect
    import string

    result=""

    # Important for converting an incoming c++ unicode character string!
    thingStr=str(thing)

    """Display text documentation, given an object or a path to an object."""
    try:
        # Possible two-stage object resolution!
        # Sometimes we get docs for strings, other times for objects
        #
        try:
            object, name = pydocs.resolve(thingStr, forceload)
        except:
            # Get an object from a string
            thingObj=eval(thingStr)
            object, name = pydocs.resolve(thingObj, forceload)
        desc = pydocs.describe(object)
        module = inspect.getmodule(object)
        if name and '.' in name:
            desc += ' in ' + name[:name.rfind('.')]
        elif module and module is not object:
            desc += ' in module ' + module.__name__
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
        text = pydocs.TextDoc()
        result=pydocs.plain(title % desc + '\n\n' + text.document(object, name))
        
        # Remove multiple empty lines
        result = [ line for line in result.splitlines() if line.strip() ]
        result = string.join(result,"\n")

    except:
        pass

    return result

def formatTraceStack(tbStack):
    """
    Format a traceback stack for use in the Maya GUI. Designed to be compatible with traceback.format_list() 
    to allow users to easily override this function to regain default formatting::
    
        import traceback
        import maya.utils
        maya.utils.formatTraceStack = traceback.format_list
    
    Given a list of tuples as returned by traceback.extract_tb() or traceback.extract_stack(), 
    return a list of strings ready for printing. Each string in the resulting list corresponds to 
    the item with the same index in the argument list. Each string ends in a newline; the strings may
    contain internal newlines as well, for those items whose source text line is not None.
    """
    lines = []
    for file, line, func, text in tbStack:
        if file == "<maya console>":
            result = u"  line %d of %s" % (line, file)
        else:
            result = u"  line %s of file '%s'" % (line, file)
        if func != "<module>":
            result += " in function %s" % func
        result += '\n'
        lines.append(result)
    return lines

_formatTraceStack = formatTraceStack     

def formatTraceback(verbose, baseMsg):
    """
    Extract the current traceback information and send it back in string form.
        verbose : If true then format the entire stack, else just the top level
    """
    return baseMsg

def prefixTraceStack(tbStack, prefix = '# '):
    """prefix with '#', being sure to get internal newlines. do not prefix first line
    as that will be added automatically"""
    result = ''.join(tbStack).rstrip().split('\n')
    size = len(result)-1
    for i, line in enumerate(result):
        if i < size:
            line += '\n'
        if i != 0:
            line = prefix + line
        result[i] = line
    return result

def fixConsoleLineNumbers( tbStack ):
    result = []
    for file, line, func, text in tbStack:
        if file == '<maya console>':
            # In the Maya console the numbering is off by one so adjust
            line -= 1
        result.append( (file, line, func, text) )
    return result

def mayaEncoding():
    import maya.cmds as cmds
    return cmds.about(codeset=True)

def decodeStack( tbStack ):
    encoding = mayaEncoding()
    return [ s.decode(encoding) for s in tbStack ]
             
def guiExceptionCallback(exceptionType, exceptionObject, traceBack, detail=2):
    """
    format a trace stack into a string.

        exceptionType   : Type of exception, RuntimeError is special
        exceptionObject : Detailed exception information
        traceBack       : Exception traceback stack information
                          Only valid for non-RuntimeError exceptionType
        detail          : 0 = no trace info, 1 = line/file only, 2 = full trace
                          Only valid for non-RuntimeError exceptionType
                          
    To perform an action when an exception occurs without modifying Maya's default printing
    of exceptions, do the following::
    
        import maya.utils
        def myExceptCB(etype, value, tb):
            # do something here...
            return maya.utils._guiExceptionCallback(etype, value, tb, detail)
        maya.utils.guiExceptionCallback = myExceptCB
        
    """
    # exceptionObject should really be an instance of an Exception subclass and not a string
    excLines = decodeStack( traceback.format_exception_only(exceptionType, exceptionObject) )
    if detail == 0:
        result = excLines[0].strip()
    else:
        tbStack = traceback.extract_tb(traceBack)
        
        if len(tbStack) > 0:
            # prepare the stack for formatting
            tbStack = fixConsoleLineNumbers(tbStack)
            tbLines = decodeStack( formatTraceStack(tbStack) )
            if detail == 1:
                # Put the line number message before the actual warning/error
                result = u'%s: %s: %s' % (exceptionType.__name__, tbLines[-1].strip(), exceptionObject)
            else: # detail == 2
                # The stack trace is longer so the warning/error might
                # get lost so it needs to be first.
                excLines.append(u'Traceback (most recent call last):\n')
                result = u''.join( prefixTraceStack( excLines + tbLines ) )
        else:
            result = "Trace not available"

    return result

_guiExceptionCallback = guiExceptionCallback

def batchExceptionCallback(exceptionType, exceptionObject, traceBack):
    """
    format a trace stack into a string.
    
    To perform an action when an exception occurs without modifying Maya's default printing
    of exceptions, do the following::
    
        import maya.utils
        def myExceptCB(etype, value, tb):
            # do something here...
            return maya.utils._batchExceptionCallback(etype, value, tb)
        maya.utils.batchExceptionCallback = myExceptCB
    """
    return traceback.format_exception(exceptionType, exceptionObject, traceBack)

# store a local unmodified copy
_batchExceptionCallback = batchExceptionCallback

class MayaLogHandler(logging.Handler):
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

def guiLogger():
    """
    Adds an additional handler to the root logger to print to
    the script editor.  Sets the shell/outputWindow handler to
    only print 'Critical' records, so that the logger's primary
    output is the script editor.
    """
    global _guiLogHandler
    if _guiLogHandler:
        return _guiLogHandler
    log = logging.getLogger('')
    shellLogger().setLevel(logging.CRITICAL)
    _guiLogHandler = MayaLogHandler()
    format = os.environ.get('MAYA_GUI_LOGGER_FORMAT', '%(name)s : %(message)s')
    _guiLogHandler.setFormatter( logging.Formatter(format) )
    log.addHandler(_guiLogHandler)
    return _guiLogHandler

def shellLogger():
    global _shellLogHandler
    if _shellLogHandler:
        return _shellLogHandler
    log = logging.getLogger('')
    _shellLogHandler = logging.StreamHandler()
    format = os.environ.get('MAYA_SHELL_LOGGER_FORMAT', '%(name)s : %(levelname)s : %(message)s')
    _shellLogHandler.setFormatter( logging.Formatter(format) )
    log.addHandler(_shellLogHandler)
    log.setLevel(logging.INFO)
    return _shellLogHandler

# Copyright (C) 1997-2006 Autodesk, Inc., and/or its licensors.
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


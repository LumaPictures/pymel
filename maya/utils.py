
"""
General utility functions that are not specific to the Maya Command or the 
OpenMaya API.
"""

# Note that several of the functions in this module are implemented in C++
# code, such as executeDeferred and executeInMainThreadWithResult

import os, warnings, sys
import traceback
from maya import cmds

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

# Utility method to handle command completion
# Returns in a list all of the possible completions that apply
# to the input string
#
def getPossibleCompletions(input):

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

# Utility method to return python help in the form of a string
# (based on the code in pydoc.py)
# Note: only a string (including unicode) should be passed in for "thing"
#
def helpNonVerbose(thing, title='Python Library Documentation: %s', forceload=0):

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

def formatTracebackLine(line,func,file):
    if file == "<maya console>":
        # In the Maya console the numbering is off by one so adjust
        result = u"line %d of %s" % (int(line)-1, file)
    else:
        result = u"line %s of file '%s'" % (line, file)
    if func != "<module>":
        result += " in function %s" % func
    return result
       
def formatTraceStack(verbose, baseMsg, tbStack):
    """
    format a trace stack into a string.
        verbose : If true then format the entire stack, else just the top level
    """
    baseMsg = baseMsg.rstrip()
    try:
        if len(tbStack) > 0:  
            if (verbose == 0) or (len(tbStack) == 1):
                file, line, func, info = tbStack[0]
                # Put the line number message before the actual warning/error
                result = formatTracebackLine(line, func, file) + ': ' + baseMsg
            else:
                result = "Traceback (most recent call last): "
                for file,line,func,info in tbStack:
                    result += "\n#   "
                    result += formatTracebackLine(line, func, file)
                # The stack trace is longer so the warning/error might
                # get lost so it needs to be first.
                result = baseMsg + "\n# " + result
        else:
            result = "Trace not available: "
    except Exception, err:
        # It would be very bad if any exception were untrapped here since that
        # would create an infinite recursion in the command engine.
        result = "Trace not available (%s): " % str(err)
    return result

def formatTraceback(verbose, baseMsg):
    """
    Extract the current traceback information and send it back in string form.
        verbose : If true then format the entire stack, else just the top level
    """
#    # by definition, this function, formatTraceback, should always be the last on the extracted stack 
#    tbStack = traceback.extract_stack()[:-1]
#    return formatTraceStack(verbose, baseMsg, tbStack)
    print 'formatTraceback', `baseMsg`
    return baseMsg
    
        
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


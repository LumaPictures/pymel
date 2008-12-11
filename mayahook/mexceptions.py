"""
Corrects printing of unicode errors in maya.
"""

import pymel.util as util
from pymel.util.pwarnings import warn, simplefilter
# from warnings import warn, simplefilter

import sys, StringIO, traceback, re, inspect, os.path

_thisModule = sys.modules[__name__]

sysEncoding = sys.getdefaultencoding()
exceptionEncoding = 'utf8'
#
## Need to overload Maya's formatException as it raises an exception on non utf8 systems
#
import maya.app.python

def formatException( exceptionType, exceptionObject, traceBack ):
    """ Maya way of formatting expections, redefined here because of a unicode encoding error """
    # Format the exception into a string        
    stringBuffer = StringIO.StringIO()
    traceback.print_exception( exceptionType, exceptionObject, traceBack,
                               32, stringBuffer )
    # result = stringBuffer.getvalue().decode('utf8')
    result = stringBuffer.getvalue().decode(exceptionEncoding)

    stringBuffer.close()
    
    # Look for stack trace items that are from the Maya Console which will be
    # off-by-one and adjust them
    lines = result.splitlines()
    for i, line in enumerate(lines):
        match = maya.app.python.mayaConsoleExpr.match(line)
        if None != match:
            lineNo = int( match.group('line') ) - 1
            line = line[:match.start('line')] + str(lineNo) + line[match.end('line'):]
        lines[i] = u'# ' + line
        
    # Append another copy of the error message onto the front because the 
    # command line will only display the first line of the error
    lines[0:0] = [unicode(exceptionObject).rstrip()]
    result = u'\n'.join(lines)
    
    # return the error message
    return result

maya.app.python.formatException = formatException

def lastFormattedException():
    """Shorthand for formatException(sys.exc_type, sys.exc_value, sys.exc_traceback)"""
    return formatException(sys.exc_type, sys.exc_value, sys.exc_traceback)

def printLastException():
    """Shorthand for print(lastFormattedException())"""
    print(lastFormattedException())
    
# Filter User Errors, Warnings and Prints by Verbosity

    
# Can define some custom exceptions (errors) as well here

class InvalidAttribute(AttributeError) :
    "Used to indicate attributes that could never be valid"
class MissingModule(StandardError) :
    "Used to indicate a required module was expected to be already loaded and is missing"
class MissingGlobal(MissingModule) :
    "Used to indicate a required global variable was expected to be already defined and is missing"



"""
The maya.app.python module contains utilites which Maya uses to communicate
with Python.  These functions are not part of Maya's public API and may be
subject to change.

Simple test script to exercise these manually:

import maya.cmds as cmds
def e1():
    cmds.error("DUH")
def e2():
    e1()
def e3():
    cmds.ls(duh=1)
def e4():
    e3()
def e5():
    cmds.xform( q=True )
def e6():
    e5()

"""

import sys, StringIO, traceback, re
from maya.utils import formatTraceStack

mayaFileExpr = re.compile('[\t ]*File "(?P<file>[^"]+)", line (?P<line>[0-9]+)')
mayaFileModuleExpr = re.compile('[\t ]*File "(?P<file>[^"]+)", line (?P<line>[0-9]+), in (?P<module>.*)')
mayaExceptionExpr = re.compile('(\w+):\s*(.*)')
mayaCommentExpr = re.compile('^#\s*(.*)')

def formatException( exceptionType, exceptionObject, traceBack, detail=2 ):
    """
    Whenever Maya receives an error from the command engine it comes into here
    to format the message for display. RuntimeError exceptions are treated
    specially since they originate from TcommandEngine::displayError(). The
    sequence of functions that triggers adds in the appropriate line/file or
    stack information via a different mechanism so this code only adds the
    exception data in that case, but adds requested traceback information
    for all other exception types.
        exceptionType   : Type of exception, RuntimeError is special
        exceptionObject : Detailed exception information
        traceBack       : Exception traceback stack information
                          Only valid for non-RuntimeError exceptionType
        detail          : 0 = no trace info, 1 = line/file only, 2 = full trace
                          Only valid for non-RuntimeError exceptionType
    """
#    if exceptionType == RuntimeError:
#        try:
#            result = formatRuntimeException( exceptionType, exceptionObject )
#        except Exception, err:
#            result = 'RuntimeError: Internal Failure "%s"' % str(err)
#    else:
#        try:
#            result = formatOtherException( exceptionType, exceptionObject, traceBack, detail )
#        except Exception, err:
#            result = '%s: Internal Failure "%s"' % (exceptionType.__name__, str(err))
    try:
        result = formatOtherException( exceptionType, exceptionObject, traceBack, detail )
    except Exception, err:
        result = '%s: Internal Failure "%s"' % (exceptionType.__name__, str(err))
        
    return result

def formatOtherException( exceptionType, exceptionObject, traceBack, detail ):
    baseMsg = unicode(exceptionObject)
    if detail > 0:
        tbStack = traceback.extract_tb(traceBack)
        result = formatTraceStack( detail==2, baseMsg, tbStack )
    else:
        result = baseMsg
    return u'%s: %s' % ( exceptionType.__name__, result)
    
def formatRuntimeException( exceptionType, exceptionObject ):
    """
    Return the exception information for RuntimeError exceptions only,
    formatted as a string suitable for user consumption. Traceback
    information for this exception, if requested, is appended through
    the formatTraceback() function.
    """
    # Format the exception into a string        
    stringBuffer = StringIO.StringIO()
    traceback.print_exception( exceptionType, exceptionObject, None,
                               32, stringBuffer )
    result = stringBuffer.getvalue().decode('utf8')
    stringBuffer.close()
    print `result`
    return u'%s' % result.rstrip()

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


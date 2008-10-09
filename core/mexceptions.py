"""
    This module helps to filter feedback prints and warnings based on a global verbosity setting that
    can be set or queried with the verboseLevel([level]) command.
    
    Typically, you'd define several verbosity warnings, like [0..3], using level 0 for the most important
    feedback and warnings, and level 3 for the accessory info that should only be printed in the most verbose mode.
    
    You can then simply use vprint(msg, level) or vwarn(msg, level[, stacklevel]) to output a level 0, 1, 2 or 3
    printed feedback or warning.
    
    The verboseStop([level]) command can also be used to instruct the warnings module to raise an error for warnings
    of a level inferior to the specified verboseStop level, to ease up debugging by stopping on the first warning you
    deem critical.
    
    Note : warnings are filtered when the same warning (same message, line number, module) is issued more than once,
    take care of that when testing
    
    >>> import random
    >>> verboseStop(0)
    0
    >>> verboseLevel(3)
    3
    >>> verboseStop(), verboseLevel()
    (0, 3)
    >>> vprint("level 0 debug print", 0)
    # 0: level 0 debug print
    >>> vprint("level 1 debug print", 1)
    # 1:   level 1 debug print
    >>> vprint("level 2 debug print", 2)
    # 2:     level 2 debug print
    >>> vprint("level 3 debug print", 3)
    # 3:       level 3 debug print

    >>> import sys
    >>> sys.stderr = sys.stdout
    >>> vwarn("random level 0 warning %s" % random.random(), 0) #doctest: +ELLIPSIS
    VerboseWarning0: random level 0 warning...
    >>> vwarn("random level 1 warning %s" % random.random(), 1) #doctest: +ELLIPSIS
    VerboseWarning1: random level 1 warning...
    >>> vwarn("random level 2 warning %s" % random.random(), 2) #doctest: +ELLIPSIS
    VerboseWarning2: random level 2 warning...
    >>> vwarn("random level 3 warning %s" % random.random(), 3) #doctest: +ELLIPSIS 
    VerboseWarning3: random level 3 warning...

    Lowering the verboseLevel will filter less important feedback
    
    >>> verboseLevel(1)
    1
    >>> verboseStop(), verboseLevel()
    (0, 1)
    >>> vprint("level 0 debug print", 0)
    # 0: level 0 debug print
    >>> vprint("level 1 debug print", 1)
    # 1:   level 1 debug print
    >>> vprint("level 2 debug print", 2)

    >>> vprint("level 3 debug print", 3)

    >>> import sys
    >>> sys.stderr = sys.stdout
    >>> vwarn("random level 0 warning %s" % random.random(), 0) #doctest: +ELLIPSIS
    VerboseWarning0: random level 0 warning...
    >>> vwarn("random level 1 warning %s" % random.random(), 1) #doctest: +ELLIPSIS
    VerboseWarning1: random level 1 warning...
    >>> vwarn("random level 2 warning %s" % random.random(), 2) #doctest: +ELLIPSIS

    >>> vwarn("random level 3 warning %s" % random.random(), 3) #doctest: +ELLIPSIS 


    Setting a non zero verboseStop level will raise exceptions on warnings below that level
   
    >>> verboseStop(1)
    1
    >>> verboseLevel(2)
    2
    >>> verboseStop(), verboseLevel()
    (1, 2)
    >>> vprint("level 0 debug print", 0)
    # 0: level 0 debug print
    >>> vprint("level 1 debug print", 1)
    # 1:   level 1 debug print
    >>> vprint("level 2 debug print", 2)
    # 2:     level 2 debug print
    >>> vprint("level 3 debug print", 3)

    >>> import sys
    >>> sys.stderr = sys.stdout 
    >>> vwarn("caught level 0 warning raises exception", 0) #doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    VerboseWarning0: caught level 0 warning raises exception
    >>> vwarn("random level 1 warning %s" % random.random(), 1) #doctest: +ELLIPSIS
    VerboseWarning1: random level 1 warning...
    >>> vwarn("random level 2 warning %s" % random.random(), 2) #doctest: +ELLIPSIS
    VerboseWarning2: random level 2 warning...
    >>> vwarn("random level 3 warning %s" % random.random(), 3) #doctest: +ELLIPSIS
    
            
"""

import pymel.util as util
from pymel.util.pwarnings import warn, simplefilter
# from warnings import warn, simplefilter
import pymel.mayahook as mayahook
from pymel.mayahook.optionvars import *

import sys, StringIO, traceback, re, inspect, os.path

_thisModule = sys.modules[__name__]

from maya.cmds import about as _about
sysEncoding = sys.getdefaultencoding()
mayaEncoding = _about(cs=True)
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

def maxVerboseLevel() :
    """ The maximum verbose level that can be set,
        valid verbose levels are thus [0..maxVerboseLevel()].
    """
#    if globals().has_key('Settings'):
#        default = Settings.optionVars.get('PMmaxVerboseLevel', default)
#    else :
#        warn("Production Settings have not been initialized", UserWarning, 1)    
    return 3

# Define one subclass of UserWarning per non 0 verbose level, AMverboseWarning1, AMverboseWarning2, etc
# Warnings User by verbosity to allow filtering

def _createVerboseWarningClasses (maxVerboseLevel) :
    """ Create the different verbosity warning classes """
    baseName = "VerboseWarning"
    baseDoc = "Warning class using the verbose %s setting in Maya"
    baseCls = UserWarning
    verboseWarningClasses = []
    # create classes [0..maxVerboseLevel]
    for i in range(maxVerboseLevel+1) :
        clsName = baseName + str(i)
        cls = type( clsName, (baseCls,), {'__doc__':(baseDoc % i), 'verbose':i})
        # print "created cls: %s" % cls
        verboseWarningClasses.append (cls)
        setattr( _thisModule, clsName, cls )
        baseCls = cls
    return verboseWarningClasses

# Do the class creation 
_verboseWarningClasses = _createVerboseWarningClasses (maxVerboseLevel())
    
# Can define some custom exceptions (errors) as well here

class InvalidAttribute(AttributeError) :
    "Used to indicate attributes that could never be valid"
class MissingModule(StandardError) :
    "Used to indicate a required module was expected to be already loaded and is missing"
class MissingGlobal(MissingModule) :
    "Used to indicate a required global variable was expected to be already defined and is missing"

# get and set current verbose level

def verboseLevel (level=None) :
    """ verboseLevel (level=None) --> int
        
        Sets the current verbose level to level / leaves it unchanged if level is None.
        Returns the new verbose level.
        
        Valid range for level is [0..maxVerboseLevel()]. 
    """
    maxVerbose = maxVerboseLevel()
    # Directement
    if not globals().has_key('Env') :
        raise MissingGlobal, "The 'Env' class must be intialized to access Maya optionVars dictionary"
    default = 0
#    if globals().has_key('Settings'):
#        default = Settings.optionVars.get('AMprefsVerboseLevel', default)
#    else :
#        warn("Production Settings have not been initialized", UserWarning, 1)

    msg = "valid verbose level values are [0..%i]" % maxVerbose
    if not Env().optionVars.has_key('PMverboseLevel') :
        Env().optionVars['PMverboseLevel'] = default
    var = Env().optionVars.get('PMverboseLevel', default)
    current = util.clamp(var, 0, maxVerbose)
    if current != var :
        Env().optionVars['PMverboseLevel'] = current
        msg += ', PMverboseLevel value %s clamped to %i' % (var, current)
        warn (msg, UserWarning, 2)  
           
    if level is None :
        result = current   
    else :
        try :
            level = int(level)
            assert level in range(maxVerbose+1)
            result = level
        except ValueError :
            result = default
            msg += ', %s defaulted to %i' % (level, result)
            warn (msg, UserWarning, 2)
        except AssertionError :
            result = util.clamp(level, 0, maxVerbose)
            msg += ', %s clamped to %i' % (level, result)
            warn (msg, UserWarning, 2)
        if result != current :
            updateWarnFilters (verbose=result)            
            Env().optionVars['PMverboseLevel'] = result

    return result

def verboseStop (level=None) :
    """ verboseStop (level=None) --> int
        
        Sets the current verbose stop level to level / leaves it unchanged if level is None.
        Returns the new verbose stop level.
    
        A warning of the VerboseWarning classes of a level inferior to the verbose stop level
        will be converted to an error Exception and stop execution.
        
        Valid range for level is [0..maxVerboseLevel()+1].  
    """
    maxStop = maxVerboseLevel()+1
    if not globals().has_key('Env') :
        raise MissingGlobal, "The 'Env' class must be intialized to access Maya optionVars dictionary"
    default = 0
#    if globals().has_key('Settings'):
#        default = Settings.optionVars.get('PMverboseStop', default)
#    else :
#        warn("Production Settings have not been initialized", UserWarning, 1)
    msg = "valid verbose stop level values are [0..%i]" % maxStop
    if not Env().optionVars.has_key('PMverboseStop') :
        Env().optionVars['PMverboseStop'] = default
    var = Env().optionVars.get('PMverboseStop', default)
    current = util.clamp(var, 0, maxStop)
    if current != var :
        Env().optionVars['PMverboseStop'] = current
        msg += ', PMverboseStop value %s clamped to %i' % (var, current)
        warn (msg, UserWarning, 2)  
           
    if level is None :
        result = current   
    else :
        try :
            level = int(level)
            assert level in range(maxStop+1)
            result = level
        except ValueError :
            result = default
            msg += ', %s defaulted to %i' % (level, result)
            warn (msg, UserWarning, 2)
        except AssertionError :
            result = util.clamp(level, 0, maxStop)
            msg += ', %s clamped to %i' % (level, result)
            warn (msg, UserWarning, 2)
        if result != current :
            updateWarnFilters (stop=result)
            Env().optionVars['PMverboseStop'] = result

    return result

def updateWarnFilters (verbose=None, stop=None) :
    """ Update warnings filters when verbosity changes """
    maxVerbose = maxVerboseLevel()
    maxStop = maxVerbose+1
    if verbose is None :
        verbose = verboseLevel()
    else :
        assert verbose in range(0, maxVerbose+1), ("Valid verbose level values are [0..%i]" % maxVerbose)        
    if stop is None :
        stop = verboseStop()
    else :
        assert stop in range(0, maxStop+1), ("Valid verbose stop level values are [0..%i]" % maxStop)
    # redo filters          
    # print "updating filters from %s, %s to %s, %s" % (verboseLevel(), verboseStop(), verbose, stop)
    # catch all
    # simplefilter(action = 'always', category=Exception)
    if stop > 0 :
        simplefilter(action = 'error', category=_verboseWarningClasses[0])
    simplefilter(action = 'always', category=_verboseWarningClasses[stop])            
    if verbose < maxVerbose :
        simplefilter(action = 'ignore', category=_verboseWarningClasses[verbose+1])
        
def vprint (msg, level=0) :
    """ vprint(msg[, level=0])
     
        Displays msg if the current verbosity level is high enough (>= level).
        
        Related : see function verboseLevel       
    """
    maxVerbose = maxVerboseLevel() 
    try :
        assert level in range(0, maxVerbose+1)
    except :
        raise ValueError, "vprint valid level values are [0..%i], %s invalid" % (maxVerbose, level)
    verbose = verboseLevel()
    # filters and formats according to verbose level
    if (level <= verbose) :
        header = u'# %i:'
        if level :
            header += u'  '*level
        header += u' %s'
        print >>sys.stdout, header % (level, msg)

def vwarn (msg, level=0, stacklevel=1) :
    """ vwarn(msg[, level=0[, stacklevel=1]])
     
        Displays warning msg if the current verbosity level is high enough (>= level)       
        Calling warn will also work directly as the warning filters are set within the 'verboseLevel' function.
        
        Note : it is also possible to set the level below which a warning will be treated as an error
        and stop execution with the 'verboseStop' function.
    """
    maxVerbose = maxVerboseLevel()
    # print "verbose warning for (%s, level=%s, stacklevel=%s)" % (msg, level, stacklevel)     
    try :
        assert level in range(0, maxVerbose+1)
    except :
        raise ValueError, "vwarn valid level values are [0..%i], %s invalid" % (maxVerbose, level)
    category = _verboseWarningClasses[level]
    # already filtered by the warnings mechanisms
    # print "trying to set warnings.warn (%s, %s, %s) for level %s" % (msg, category, stacklevel+1, level)
    warn (msg, category, stacklevel+1)
        
# do the first init warning filter
updateWarnFilters(verbose=verboseLevel(), stop=verboseStop())


if __name__ == '__main__' :
    import doctest
    doctest.testmod()

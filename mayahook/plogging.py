import sys
import maya
from logging import *
from logging import basicConfig, getLevelName, root, info, debug, warning, error, critical, getLogger

#===============================================================================
# MAYA 8.5 BUG-FIX
#===============================================================================
logStream = None
if hasattr(maya,"Output") and not hasattr(maya.Output,"flush"):
    class mayaOutput(maya.Output):
        def flush(*args,**kwargs):
            pass
    logStream = mayaOutput()

#===============================================================================
# DEFAULT FORMAT SETUP
#===============================================================================

if sys.version_info[:2] >= (2,5):
    # funcName is only available in python 2.5+
    basicConfig(format='%(levelname)10s | %(name)-25s | %(funcName)s(): %(message)s ',stream=logStream)
else:
    basicConfig(format='%(levelname)10s | %(name)-25s:\t\t%(message)s ',stream=logStream)
    
# keep as a list of tuples (and not a dictionary) so that we can keep the order
logLevels = [(getLevelName(n),n) for n in range(0,CRITICAL+1,10)]

def nameToLevel(level):
    return dict(logLevels).get(level, level)

logger = getLogger(__name__)


#===============================================================================
# DECORATORS
#===============================================================================
def timed(level=DEBUG):
    import time
    def timedWithLevel(func):
        logger = getLogger(func.__module__)
        def timedFunction(*arg, **kwargs):
            t = time.time()
            res = func(*arg, **kwargs)
            t = time.time() - t # convert to seconds float
            strSecs = time.strftime("%M:%S.", time.localtime(t)) + ("%.3f" % t).split(".")[-1]
            logger.log(level, 'Function %s(...) - finished in %s seconds' % (func.func_name, strSecs))
            return res
        timedFunction.__doc__ = func.__doc__
        timedFunction.func_name = func.func_name
        return timedFunction
    return timedWithLevel

def stdOutsRedirected(func):
    def stdOutsRedirectedFunction(*arg, **kwargs):
        redirectStandardOutputs(root)
        origs = (sys.stdout, sys.stderr)
        try:
            ret = func(*arg, **kwargs)
        finally:
            (sys.stdout, sys.stderr) = origs
        return ret
    stdOutsRedirectedFunction.__doc__ = func.__doc__
    stdOutsRedirectedFunction.func_name = func.func_name
    return stdOutsRedirectedFunction


#===============================================================================
# INIT TO USER'S PREFERENCE
#===============================================================================
def setupLevelPreferenceHook():
    """Sets up a callback so that the last used log-level is saved to the user preferences file""" 
    from optionvars import optionVar
    rootHandler = root.handlers[0] 
    func = rootHandler.setLevel
    def setLevelHook(level, *args, **kwargs):
        logger.info("Log Level Changed to '%s'" % level)
        level = nameToLevel(level)
        ret = func(level, *args, **kwargs)
        try:
            import pymel
            optionVar["%s.logLevel" % __name__] = level
        except Exception, e:
            logger.warning("Log Level could not be saved to the user-prefs ('%s')" % e)
        return ret
    rootHandler.setLevel = setLevelHook
    
    
    level =  max(20,int(nameToLevel(optionVar["%s.logLevel" % __name__]))) # no more than INFO level
    rootHandler.setLevel(level)
    logger.info("%s initialized, set to %s" % (__name__, getLevelName(level)))

root.setLevel(0)



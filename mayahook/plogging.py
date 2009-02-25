"pymel logging functions"
import maya
from maya.OpenMaya import MGlobal, MEventMessage, MMessage
import sys, os

import logging
import logging.config
from logging import *
# The python 2.6 version of 'logging' hids these functions, so we need to import explcitly
from logging import basicConfig, getLevelName, root, info, debug, warning, error, critical, getLogger
import pymel.util as util
import maya.utils
import maya.app.python
from pymel.util.decoration import decorator





#===============================================================================
# DEFAULT FORMAT SETUP
#===============================================================================

def _fixMayaOutput():
    if not hasattr( sys.stdout,"flush"):
        def flush(*args,**kwargs): 
            pass
        try:
            sys.stdout.flush = flush
        except AttributeError:
            # second try
            #if hasattr(maya,"Output") and not hasattr(maya.Output,"flush"):
            class MayaOutput(maya.Output):
                def flush(*args,**kwargs):
                    pass
            maya.Output = MayaOutput()
            sys.stdout = maya.Output

class ClassInfo(object):
    def __init__(self, cls):
        self.currentClass = cls

    def __getitem__(self, name):
        """
        To allow this instance to look like a dict.
        """
        if name == "class":
            result = self.currentClass.__name__
        else:
            result = self.__dict__.get(name, "?")
        return result

    def __iter__(self):
        """
        To allow iteration over keys, which will be merged into
        the LogRecord dict before formatting and output.
        """
        keys = ["class"]
        keys.extend(self.__dict__.keys())
        return keys.__iter__()

           

_fixMayaOutput()


configFile = os.path.join(os.path.dirname(__file__),"user_logging.conf")
if not os.path.isfile(configFile):
    configFile = os.path.join(util.moduleDir(),"pymel.conf")

if sys.version_info >= (2,6):
    logging.config.fileConfig(configFile, disable_existing_loggers=0)
else:
    logging.config.fileConfig(configFile)
    # The fileConfig function disables old-loggers, so we need to re-enable them
    for k,v in sorted(logging.root.manager.loggerDict.iteritems()):
        if hasattr(v, 'disabled') and v.disabled:
            v.disabled = 0
    


mainLogger = logging.root

pymelLogger = logging.getLogger("pymel")

# keep as an enumerator so that we can keep the order
logLevels = util.Enum( 'logLevels', dict([(getLevelName(n),n) for n in range(0,CRITICAL+1,10)]) )

def getClassLogger(cls):
    """get a logger for the passed class"""
    logger = logging.getLogger('%s.%s' % cls.__module__, cls.__name__)
    # logging adapter is in 2.6 only
    if sys.version_info[:2] >= (2,6):    
        newlogger = logging.LoggerAdapter( logger, ClassInfo(cls) )
        return newlogger
    
    return logger

def nameToLevel(name):
    return logLevels.getIndex(name)

def levelToName(level):
    return logLevels.getKey(level)

#===============================================================================
# DECORATORS
#===============================================================================
def timed(level=DEBUG):
    import time
    @decorator
    def timedWithLevel(func):
        logger = getLogger(func.__module__)
        def timedFunction(*arg, **kwargs):
            t = time.time()
            res = func(*arg, **kwargs)
            t = time.time() - t # convert to seconds float
            strSecs = time.strftime("%M:%S.", time.localtime(t)) + ("%.3f" % t).split(".")[-1]
            logger.log(level, 'Function %s(...) - finished in %s seconds' % (func.func_name, strSecs))
            return res
        return timedFunction
    return timedWithLevel

@decorator
def stdOutsRedirected(func):
    def stdOutsRedirectedFunction(*arg, **kwargs):
        redirectStandardOutputs(root)
        origs = (sys.stdout, sys.stderr)
        try:
            ret = func(*arg, **kwargs)
        finally:
            (sys.stdout, sys.stderr) = origs
        return ret
    return stdOutsRedirectedFunction

#===============================================================================
# INIT TO USER'S PREFERENCE
#===============================================================================


def _setupLevelPreferenceHook():
    """Sets up a callback so that the last used log-level is saved to the user preferences file""" 
    
    LOGLEVEL_OPTVAR = 'pymel.logLevel'

    # retrieve the preference as a string name, for human readability
    # we need to use MGlobal because cmds.optionVar might not exist yet
    levelName = MGlobal.optionVarStringValue( LOGLEVEL_OPTVAR )
    if levelName:
        level =  min( logging.WARNING, nameToLevel(levelName) ) # no more than WARNING level
        pymelLogger.setLevel(level)
        pymelLogger.debug("setting logLevel to preference: %s (%d)" % (levelName, level) )
    else:
        pymelLogger.debug("setting logLevel to default: %s" % (levelName ) )
        pymelLogger.setLevel(logging.INFO)
        
    func = pymelLogger.setLevel
    def setLevelHook(level, *args, **kwargs):
        
        levelName = levelToName(level)
        level = nameToLevel(level)
        ret = func(level, *args, **kwargs)
        pymelLogger.info("Log Level Changed to '%s'" % levelName)
        try:
            # save the preference as a string name, for human readability
            # we need to use MGlobal because cmds.optionVar might not exist yet
            MGlobal.setOptionVarValue( LOGLEVEL_OPTVAR, levelName )
        except Exception, e:
            pymelLogger.warning("Log Level could not be saved to the user-prefs ('%s')" % e)
        return ret
 
    setLevelHook.__doc__ = func.__doc__
    setLevelHook.__name__ = func.__name__
    pymelLogger.setLevel = setLevelHook
    
    # if we are in batch mode and pymel is imported very early, it will still register as interactive at this point
    if MGlobal.mayaState() == MGlobal.kInteractive and sys.stdout.__class__ == file and hasattr(maya.utils, 'executeDeferred'):
        # stdout has not yet been replaced by maya's custom stream that redirects to the output window.
        # we need to put a callback in place that lets us get maya.Output stream as our StreamHandler.
        pymelLogger.debug( 'setting up callback to redirect logger StreamHandler' )

        maya.utils.executeDeferred( redirectLoggerToMayaOutput )


def redirectLoggerToMayaOutput(*args):
    "run when pymel is imported very early in the load process"
    
    
    if MGlobal.mayaState() == MGlobal.kInteractive:
        if sys.stdout.__class__ == file:
            pymelLogger.warning( 'could not fix sys.stdout %s' %  MGlobal.mayaState())
        else:
            pymelLogger.debug( 'fixing sys.stdout' )
        
            _fixMayaOutput()
            newHandler = StreamHandler(sys.stdout)
            #TODO: get this formatter from the config file
            formatter = logging.Formatter('pymel.%(module)s : %(levelname)s : %(message)s')
            newHandler.setFormatter(formatter)
            #newHandler.setLevel( mainLogger.getEffectiveLevel() )
            mainLogger.addHandler( newHandler )
            # mainLogger.removeHandler(console)

_setupLevelPreferenceHook()


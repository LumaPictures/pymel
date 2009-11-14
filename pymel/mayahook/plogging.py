"pymel logging functions"
import sys, os

import logging
import logging.config
from logging import *
# The python 2.6 version of 'logging' hides these functions, so we need to import explcitly
from logging import getLevelName, root, info, debug, warning, error, critical, getLogger

import maya
import pymel.util as util
import maya.utils
from maya.OpenMaya import MGlobal, MEventMessage, MMessage

from pymel.util.decoration import decorator


PYMEL_CONF_ENV_VAR = 'PYMEL_CONF'


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

_fixMayaOutput()

def getConfigFile():
    if PYMEL_CONF_ENV_VAR in os.environ:
        configFile = os.environ[PYMEL_CONF_ENV_VAR]
        if os.path.isfile(configFile):
            return configFile
    if 'HOME' in os.environ:
        configFile = os.path.join( os.environ['HOME'], "pymel.conf")
        if os.path.isfile(configFile):
            return configFile
    moduleDir = os.path.dirname( os.path.dirname( sys.modules[__name__].__file__ ) )
    configFile = os.path.join(moduleDir,"pymel.conf")
    if os.path.isfile(configFile):
        return configFile
    raise IOError, "Could not find pymel.conf"

def getLogConfigFile():
    configFile = os.path.join(os.path.dirname(__file__),"user_logging.conf")
    if os.path.isfile(configFile):
        return configFile
    return getConfigFile()

if hasattr(maya.utils, 'shellLogger'):
    maya.utils.shellLogger()

#configFile = getLogConfigFile()
#if sys.version_info >= (2,6):
#    logging.config.fileConfig(configFile, disable_existing_loggers=0)
#else:
#    logging.config.fileConfig(configFile)
#    # The fileConfig function disables old-loggers, so we need to re-enable them
#    for k,v in sorted(logging.root.manager.loggerDict.iteritems()):
#        if hasattr(v, 'disabled') and v.disabled:
#            v.disabled = 0
    
rootLogger = logging.root

pymelLogger = logging.getLogger("pymel")

# keep as an enumerator so that we can keep the order
logLevels = util.Enum( 'logLevels', dict([(getLevelName(n),n) for n in range(0,CRITICAL+1,10)]) )



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


#===============================================================================
# INIT TO USER'S PREFERENCE
#===============================================================================


def _setupLevelPreferenceHook():
    """Sets up a callback so that the last used log-level is saved to the user preferences file""" 
    
    LOGLEVEL_OPTVAR = 'pymel.logLevel'

    
    # retrieve the preference as a string name, for human readability.
    # we need to use MGlobal because cmds.optionVar might not exist yet
    # TODO : resolve load order for standalone.  i don't think that userPrefs is loaded yet at this point in standalone.
    levelName = os.environ.get( 'PYMEL_LOGLEVEL', MGlobal.optionVarStringValue( LOGLEVEL_OPTVAR ) )
    if levelName:
        level =  min( logging.WARNING, nameToLevel(levelName) ) # no more than WARNING level
        pymelLogger.setLevel(level)
        pymelLogger.info("setting logLevel to user preference: %s (%d)" % (levelName, level) )
        
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
    


#_setupLevelPreferenceHook()


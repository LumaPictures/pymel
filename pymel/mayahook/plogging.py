"pymel logging functions"
import sys, os

import logging
import logging.config
from logging import *
# The python 2.6 version of 'logging' hides these functions, so we need to import explcitly
from logging import getLevelName, root, info, debug, warning, error, critical, getLogger
import ConfigParser

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

assert hasattr(maya.utils, 'shellLogHandler'), "If you manually installed pymel, ensure " \
    "that pymel comes before Maya's site-packages directory on PYTHONPATH / sys.path.  " \
    "See pymel docs for more info."
    
def pymelLogFileConfig(fname, defaults=None):):
    """
    Reads in a file to set up pymel's loggers.
    
    Like logging.config.fileConfig, but intended only for pymel's loggers,
    and less heavy handed - fileConfig will, for instance, wipe out all
    handlers from logging._handlers, remove all handlers from logging.root, etc
    
    For the root logger, the default behavior for pre-existing handlers is to
    keep them - any handlers given in the config file will be 'prepended' to
    the list of root logger handlers. (Maya will set up a 'default' root
    logger, so adding extra root loggers should only be necessary if you have
    specific needs).
    If you wish to to make the setup REMOVE all pre-existing root handlers,
    add a 'remove_existing_handlers' option to the logger_root section,
    and set it's value to True.
    
    For loggers other than the root logger, the default behavior is the
    opposite - remove all existing handlers; if you wish to keep them,
    set 'remove_existing_handlers' to False.
    
    The format of the config file read in must meet the same requirements
    as for logging.config.fileConfig - it must have the sections [loggers],
    [handlers], and [fomatters], and it must have an entry for [logger_root]...
    even if not options are set for it.
    """
    cp = ConfigParser.ConfigParser(defaults)
    if hasattr(cp, 'readfp') and hasattr(fname, 'readline'):
        cp.readfp(fname)
    else:
        cp.read(fname)

    formatters = _create_formatters(cp)

    # critical section
    logging._acquireLock()
    try:
        # Handlers add themselves to logging._handlers
        handlers = logging.config._install_handlers(cp, formatters)
        # _install_loggers will remove all existing handlers for the
        # root logger, and any other handlers specified... to override
        # this, save the existing handlers first
        root = logging.root
        rootHandlers = rootHandlers
        oldLogHandlers = {}
        for loggerName, logger in root.manager.loggerDict.iteritems():
            oldLogHandlers[loggerName] = logger.handlers
        if sys.version_info >= (2,6):
            logging.config._install_loggers(configFile, handlers,
                                            disable_existing_loggers=0)
        else:
            logging.config._install_loggers(configFile, handlers)
            # The _install_loggers function disables old-loggers, so we need to
            # re-enable them
            for k,v in logging.root.manager.loggerDict.iteritems():
                if hasattr(v, 'disabled') and v.disabled:
                    v.disabled = 0
        # Now re-add any removed handlers, if needed
        secNames = [cp.get('loggers', 'keys').split(',')]
        secNames = ['logger_' + x.strip() for x in secNames if x != 'root']
        _addOldHandlers(root, rootHandlers, 'logger_root', cp, False )
        for secName in secNames:
            logName = cp.get(secName, 'qualname')
            _addOldHandlers(root.manager.loggerDict[logName],
                            oldLogHandlers[logName], secName, cp, True)
    finally:
        logging._releaseLock()
        
def _addOldHandlers(logger, oldHandlers, secName, configParser,
                    removeExistingDefault):
    opts = cp.options(secName)
    if 'remove_existing_handlers' not in opts:
        removeExisting = removeExistingDefault
    else:
        removeExisting = eval(opts['remove_existing_handlers'])
    if not removeExisting:
        for handler in oldHandlers:
            if handler not in logger.handlers:
                logger.addhandler(handler)

maya.utils.shellLogHandler()

pymelLogFileConfig(getLogConfigFile())
    
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


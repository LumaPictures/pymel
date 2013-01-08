"pymel logging functions"
import sys, os

import logging
import logging.config
from logging import *
# The python 2.6 version of 'logging' hides these functions, so we need to import explcitly
from logging import getLevelName, root, info, debug, warning, error, critical
import ConfigParser

import maya
import pymel.util as util
import maya.utils
from maya.OpenMaya import MGlobal, MEventMessage, MMessage

from pymel.util.decoration import decorator


PYMEL_CONF_ENV_VAR = 'PYMEL_CONF'
PYMEL_LOGLEVEL_ENV_VAR = 'PYMEL_LOGLEVEL'
PYMEL_ERRORLEVEL_ENV_VAR = 'PYMEL_ERRORLEVEL'

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
    configFile = os.environ.get(PYMEL_CONF_ENV_VAR)
    if configFile and os.path.isfile(configFile):
        return configFile
    home = os.environ.get('HOME')
    if home:
        configFile = os.path.join( home, "pymel.conf")
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



#    Like logging.config.fileConfig, but intended only for pymel's loggers,
#    and less heavy handed - fileConfig will, for instance, wipe out all
#    handlers from logging._handlers, remove all handlers from logging.root, etc
def pymelLogFileConfig(fname, defaults=None, disable_existing_loggers=False):
    """
    Reads in a file to set up pymel's loggers.

    In most respects, this function behaves similarly to logging.config.fileConfig -
    consult it's help for details. In particular, the format of the config file
    must meet the same requirements - it must have the sections [loggers],
    [handlers], and [fomatters], and it must have an entry for [logger_root]...
    even if not options are set for it.

    It differs from logging.config.fileConfig in the following ways:

    1) It will not disable any pre-existing loggers which are not specified in
    the config file, unless disable_existing_loggers is set to True.

    2) Like logging.config.fileConfig, the default behavior for pre-existing
    handlers on any loggers whose settings are specified in the config file is
    to remove them; ie, ONLY the handlers explicitly given in the config will
    be on the configured logger.
    However, pymelLogFileConfig provides the ability to keep pre-exisiting
    handlers, by setting the 'remove_existing_handlers' option in the appropriate
    section to True.
    """
    cp = ConfigParser.ConfigParser(defaults)
    if hasattr(cp, 'readfp') and hasattr(fname, 'readline'):
        cp.readfp(fname)
    else:
        cp.read(fname)

    formatters = logging.config._create_formatters(cp)

    # _install_loggers will remove all existing handlers for the
    # root logger, and any other handlers specified... to override
    # this, save the existing handlers first
    root = logging.root
    # make sure you get a COPY of handlers!
    rootHandlers = root.handlers[:]
    oldLogHandlers = {}

    # Don't use getLogger while iterating through loggerDict, as that
    # may actually create a logger, and change the size of the dict
    # ...instead, just ignore any PlaceHolder instances we get, as they
    # won't have any handlers to worry about anyway
    # thanks to pierre.augeard for pointing this one out
    for loggerName, logger in root.manager.loggerDict.iteritems():
        # Make sure it's not a PlaceHolder
        if isinstance(logger, logging.Logger):
            # make sure you get a COPY of handlers!
            oldLogHandlers[loggerName] = logger.handlers[:]

    # critical section
    logging._acquireLock()
    try:
        # Handlers add themselves to logging._handlers
        handlers = logging.config._install_handlers(cp, formatters)

        if sys.version_info >= (2,6):
            logging.config._install_loggers(cp, handlers,
                                            disable_existing_loggers=0)
        else:
            logging.config._install_loggers(cp, handlers)
            # The _install_loggers function disables old-loggers, so we need to
            # re-enable them
            for k,v in logging.root.manager.loggerDict.iteritems():
                if hasattr(v, 'disabled') and v.disabled:
                    v.disabled = 0

        # Now re-add any removed handlers, if needed
        secNames = cp.get('loggers', 'keys').split(',')
        secNames = ['logger_' + x.strip() for x in secNames]
        _addOldHandlers(root, rootHandlers, 'logger_root', cp)
        for secName in secNames:
            if secName == 'logger_root':
                logger = root
                oldHandlers = rootHandlers
            else:
                logName = cp.get(secName, 'qualname')
                logger = logging.getLogger(logName)
                oldHandlers = oldLogHandlers.get(logName)
            if oldHandlers:
                _addOldHandlers(logger, oldHandlers, secName, cp)

    finally:
        logging._releaseLock()

def _addOldHandlers(logger, oldHandlers, secName, configParser):
    opts = configParser.options(secName)
    if 'remove_existing_handlers' not in opts:
        removeExisting = True
    else:
        removeExisting = eval(configParser.get(secName, 'remove_existing_handlers'))
    if not removeExisting:
        for handler in oldHandlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)

maya.utils.shellLogHandler()

pymelLogFileConfig(getLogConfigFile())

rootLogger = logging.root

pymelLogger = logging.getLogger("pymel")

def environLogLevelOverride(logger):
    """If PYMEL_LOGLEVEL is set, make sure the logging level is at least that
    much for the given logger.
    """
    # variable must exist AND be non-empty
    environLevel = os.environ.get(PYMEL_LOGLEVEL_ENV_VAR)
    if environLevel:
        environLevel = nameToLevel(environLevel)
        currentLevel = logger.getEffectiveLevel()
        if not currentLevel or currentLevel > environLevel:
            logger.setLevel(environLevel)

def getLogger(name):
    """
    a convenience function that allows any module to setup a logger by simply
    calling `getLogger(__name__)`.  If the module is a package, "__init__" will
    be stripped from the logger name
    """
    suffix = '.__init__'
    if name.endswith(suffix):
        name = name[:-len(suffix)]
    logger = logging.getLogger(name)
    environLogLevelOverride(logger)
    addErrorLog(logger)
    # for convenience, stick 'DEBUG', 'INFO', 'WARNING', etc attributes onto
    # the logger itself
    for logEnumValue in logLevels.values():
        setattr(logger, logEnumValue.key, logEnumValue.index)
    return logger

# keep as an enumerator so that we can keep the order
logLevels = util.Enum( 'logLevels', dict([(getLevelName(n),n) for n in range(0,CRITICAL+1,10)]) )

def nameToLevel(name):
    try:
        return int(name)
    except ValueError:
        return logLevels.getIndex(name)

def levelToName(level):
    if not isinstance(level, int):
        raise TypeError(level)
    try:
        return logLevels.getKey(level)
    except ValueError:
        return str(level)

environLogLevelOverride(pymelLogger)


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
    levelName = os.environ.get( PYMEL_LOGLEVEL_ENV_VAR,
                                MGlobal.optionVarStringValue( LOGLEVEL_OPTVAR ) )
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

#===============================================================================
# ERROR LOGGER
#===============================================================================
ERRORLEVEL = None
ERRORLEVEL_DEFAULT = logging.ERROR
def raiseLog(logger, level, message, errorClass=RuntimeError):
    '''For use in situations in which you may wish to raise an error or simply
    print to a logger.

    Ie, if checking for things that "shouldn't" happen, may want to raise an
    error if a developer, but simply issue a warning and continue as gracefully
    as possible for normal end-users.

    So, if we make a call:
        raiseLog(_logger, _logger.INFO, "oh noes! something weird happened!")
    ...then what happens will depend on what the value of ERRORLEVEL (controlled
    by the environment var %s) is - if it was not set, or set to ERROR, or
    WARNING, then the call will result in issuing a _logger.info(...) call;
    if it was set to INFO or DEBUG, then an error would be raised.

    For convenience, raiseLog is installed onto logger instances created with
    the getLogger function in this module, so you can do:
        _logger.raiseLog(_logger.INFO, "oh noes! something weird happened!")
    '''
    # Initially wanted to have ERROR_LOGLEVEL controlled by the pymel.conf,
    # but I want to be able to use raiseLog in early startup, before pymel.conf
    # is read in pymel.internal.startup, so an environment variable seemed the
    # only way to go
    global ERRORLEVEL
    if ERRORLEVEL is None:
        levelName = os.environ.get(PYMEL_ERRORLEVEL_ENV_VAR)
        if levelName is None:
            ERRORLEVEL = ERRORLEVEL_DEFAULT
        else:
            ERRORLEVEL = nameToLevel(levelName)
    if level >= ERRORLEVEL:
        raise errorClass(message)
    else:
        logger.log(level, message)

def addErrorLog(logger):
    '''Adds an 'raiseLog' method to the given logger instance
    '''
    if 'raiseLog' not in logger.__dict__:
        # because we're installing onto an instance, and not a class, we have to
        # create our own wrapper which sets the logger
        def instanceErrorLog(*args, **kwargs):
            return raiseLog(logger, *args, **kwargs)
        instanceErrorLog.__doc__ = raiseLog.__doc__
        instanceErrorLog.__name__ = 'raiseLog'
        logger.raiseLog = instanceErrorLog
    return logger

#_setupLevelPreferenceHook()


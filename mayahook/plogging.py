"pymel logging functions"
import maya
from maya.OpenMaya import MGlobal, MEventMessage, MMessage
import sys
import logging
from logging import *
import pymel.util as util

# The oython 2.6 version of 'logging' hids these functions, so we need to import explcitly
from logging import basicConfig, getLevelName, root, info, debug, warning, error, critical, getLogger


import maya.app.python

#===============================================================================
# DEFAULT FORMAT SETUP
#===============================================================================

def _fixMayaOutput():
    if not hasattr( sys.stdout,"flush"):
        def flush(*args,**kwargs): pass
        sys.stdout.flush = flush
            
#if sys.version_info[:2] >= (2,5):
#    # funcName is only available in python 2.5+
#    
#    #basicConfig(format='%(levelname)-9s:%(module)s.%(funcName)s(): %(message)s ')#,stream=logStream)
#    basicConfig(format='pymel.%(module)-15s: %(levelname)-7s: %(message)s ')
#    #basicConfig(format='%(name)s: %(levelname)-8s %(message)s ')
#else:
#    basicConfig(format='%(levelname)10s | %(name)-25s:\t\t%(message)s ' ) #,stream=logStream)

_fixMayaOutput()
console = logging.StreamHandler(sys.stdout)


# for some idiotic reason maya does not use a fixed-width font in their script editor, so even spacing won't matter 90% of the time
# when we hook up an option to spit out to file, we can have a different formatting with more info and better spacing
formatter = logging.Formatter('pymel.%(module)s : %(levelname)s : %(message)s')
#formatter = logging.Formatter('%(levelname)s : (pymel.%(module)s) : %(message)s')

console.setFormatter(formatter)

mainLogger = logging.getLogger('pymel')

mainLogger.addHandler(console)

# keep as an enumerator so that we can keep the order
logLevels = util.Enum( dict([(getLevelName(n),n) for n in range(0,CRITICAL+1,10)]) )


global _callbackId

def nameToLevel(name):
    return logLevels.getIndex(name)

def levelToName(level):
    return logLevels.getKey(level)

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


def _setupLevelPreferenceHook():
    """Sets up a callback so that the last used log-level is saved to the user preferences file""" 
    
    LOGLEVEL_OPTVAR = 'pymel.logLevel'

    # retrieve the preference as a string name, for human readability
    # we need to use MGlobal because cmds.optionVar might not exist yet
    levelName = MGlobal.optionVarStringValue( LOGLEVEL_OPTVAR )
    if levelName:
        level =  min( logging.WARNING, nameToLevel(levelName) ) # no more than WARNING level
        mainLogger.setLevel(level)
        mainLogger.info("setting logLevel to preference: %s (%d)" % (levelName, level) )
    else:
        mainLogger.info("setting logLevel to default: %s" % (levelName ) )
        mainLogger.setLevel(logging.INFO) 
        
    func = mainLogger.setLevel
    def setLevelHook(level, *args, **kwargs):
        
        levelName = levelToName(level)
        level = nameToLevel(level)
        ret = func(level, *args, **kwargs)
        mainLogger.info("Log Level Changed to '%s'" % levelName)
        try:
            # save the preference as a string name, for human readability
            # we need to use MGlobal because cmds.optionVar might not exist yet
            MGlobal.setOptionVarValue( LOGLEVEL_OPTVAR, levelName )
        except Exception, e:
            mainLogger.warning("Log Level could not be saved to the user-prefs ('%s')" % e)
        return ret
 
    setLevelHook.__doc__ = func.__doc__
    setLevelHook.__name__ = func.__name__
    mainLogger.setLevel = setLevelHook
    
    # if we are in batch mode and pymel is imported very early, it will still register as interactive at this point
    if MGlobal.mayaState() == MGlobal.kInteractive and sys.stdout.__class__ == file:
        # stdout has not yet been replaced by maya's custom stream that redirects to the output window.
        # we need to put a callback in place that lets us get maya.Output stream as our StreamHandler.
        mainLogger.debug( 'setting up callback to redirect logger StreamHandler' )
        global _callbackId
        _callbackId = MEventMessage.addEventCallback( 'SceneOpened', redirectLoggerToMayaOutput )
        


def redirectLoggerToMayaOutput(*args):
    "run when pymel is imported very early in the load process"
    
    global _callbackId
    MMessage.removeCallback( _callbackId )
    _callbackId.disown()
    
    if MGlobal.mayaState() == MGlobal.kInteractive:
        if sys.stdout.__class__ == file:
            mainLogger.warning( 'could not fix sys.stdout %s' %  MGlobal.mayaState())
        else:
            mainLogger.debug( 'fixing sys.stdout' )
        
            _fixMayaOutput()
            newHandler = StreamHandler(sys.stdout)
            newHandler.setFormatter(formatter)
            #newHandler.setLevel( mainLogger.getEffectiveLevel() )
            mainLogger.addHandler( newHandler )
            mainLogger.removeHandler(console)

_setupLevelPreferenceHook()


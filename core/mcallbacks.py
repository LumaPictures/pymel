""" Manipulate Maya scriptJobs as a global dictionnary """

import sys
import pymel.util
from pymel.util.pwarnings import *

def conditions() :
    """Returns the list of existing Maya conditions as Condition objects"""
    return map(Condition, scriptJob(listConditions=True))
    
def events() :
    """Returns the list of existing Maya events as event objects"""
    return map(Event, scriptJob(listEvents=True))

# Class for Maya Conditions
class Condition(unicode) :
    def __repr__(self) :
        return "%s('%s')" % (self.__class__.__name__, self)
    def __init__(self, condition) :
        if not isinstance (condition, Condition) :
            try :
                cond = unicode(condition)
            except :
                raise ValueError, "Expecting Condition or an existing Maya condition name"
            existingConditions = scriptJob(listConditions=True)
            if cond in existingConditions :
                self = cond
            else :
                raise ValueError, "Condition '"+cond+"' does not exist"
        else :
            self = condition
    def exists(self):
        if self in conditions() :
            return True
        else :
            return False
        
# Class for Maya Events
class Event(unicode) :
    def __repr__(self) :
        return "%s('%s')" % (self.__class__.__name__, self)
    def __init__(self, event) :
        if not isinstance (event, Event) :
            try :
                ev = unicode(event) 
            except :
                raise ValueError, "Expecting Event or an existing Maya event name"                                  
            existingEvents = scriptJob(listEvents=True)
            if ev in existingEvents :
                self = ev
            else :
                raise ValueError, "Event '"+ev+"' does not exist"
        else :
            self = event
    def exists(self):
        if self in events() :
            return True
        else :
            return False

## Classes to represent Maya's scriptJobs
# TODO : Extend with support for more API callbacks (MMessage and derived)

# scriptJobs are organised in sub-types depending on their trigger mechanism (condition, even, attribute etc)
class ScriptJobTrigger (object):
    "Generic trigger for scriptJobs"
    types = None
    valid = None
    options = None
    
#    validTriggers = {'conditionTrue': ScriptJobCondition, 'conditionFalse': ScriptJobCondition, 'conditionChange': ScriptJobCondition,\
#                     'event': ScriptJobEvent, 'idleEvent': ScriptJobEvent, 'timeChange': ScriptJobEvent,\
#                     'attributeChange': ScriptJobAttribute, 'attributeDeleted': ScriptJobAttribute,\
#                     'attributeAdded': ScriptJobAttribute, 'connectionChange': ScriptJobAttribute,
#                     'disregardIndex': ScriptJobAttribute, 'allChildren': ScriptJobAttribute,\
#                     'uiDeleted': ScriptJobUI }
#    def __init__(self, **kwargs):
#        raise ValueError, 'Arguments do not correspond to a known scriptJob trigger type: '+unicode(kwargs.keys())
       
# scriptJobs triggered by the value or change of value of a condition
class ScriptJobCondition(ScriptJobTrigger) :
    "Condition trigger for scriptJobs"
    valid = ('conditionTrue', 'conditionFalse', 'conditionChange')
    options = None
    condition = None
    case = None
    def __repr__(self):
        return "%s(%s=%s)" % (self.__class__.__name__, self.case, self.condition.__repr__())
    def __init__(self, **kwargs):
        """ Supports <conditionCase>='conditionName' syntax,
            valid <conditionCase> values are 'conditionTrue', 'conditionFalse', 'conditionChange'"""       
        if len(kwargs) == 1 :
            arg = kwargs.keys()[0]
            if ScriptJobTrigger.validTriggers.get(arg, None).__name__ == self.__class__.__name__ :
                # accept both Condition and unicode condition name
                v = Condition(unicode(kwargs.get(arg)))
                if v.exists() :
                    self.condition = v
                    self.case = arg
                else :
                    raise ValueError, 'Unknown condition: '+v
            else :
                raise ValueError, 'Invalid argument: '+arg
        else :
            raise ValueError, 'One and only one condition must be specified for a ScriptJobCondition trigger'
    def arguments(self):
        if self.condition is not None and self.case is not None :
            return ["%s=\"%s\"" %(self.case, self.condition)]

    
# scriptJobs triggered by a particular Maya event
class ScriptJobEvent(ScriptJobTrigger):
    "Event trigger for scriptJobs"
    event = None
    def __repr__(self):
        return "%s(event=\"%s\")" % (self.__class__.__name__, self.event.__repr__())
    def __init__(self, **kwargs):
        """ Supports syntax event='eventName' or idleEvent=True or timeChanged=True"""       
        if len(kwargs) == 1 :
            arg = kwargs.keys()[0]
            if ScriptJobTrigger.validTriggers.get(arg, None).__name__ == self.__class__.__name__ :
                # idleEvent or timeChanged specific cases
                v = kwargs[arg]
                # print 'arg: '+arg+' = '+unicode(v)
                if arg == 'idleEvent' and v == True :
                    self.event = Event('idle')
                elif arg == 'timeChange' and v == True : 
                    self.event = Event('timeChanged')
                else :
                    # accept both Event and unicode event name
                    eventName = Event(unicode(v))
                    if eventName.exists() :
                        self.event = eventName
                    else :
                        raise ValueError, 'Unknown event: '+eventName
                if self.event is None :
                    raise ValueError, 'No valid event specified'
            else :
                raise ValueError, 'Invalid argument: '+arg
        else :
            raise ValueError, 'One and only one event must be specified for a ScriptJobCondition trigger'
    def arguments(self) :
        if self.event is not None :
            return ["event=\"%s\"" %(self.event)]
    
# scriptJobs triggered by a change on a Maya attribute
class ScriptJobAttribute(ScriptJobTrigger):
    "Attribute add, change, deletion or connection change trigger for scriptJobs"
    attribute = None
    case = None
    disregardIndex = False
    allChildren = False
    def __repr__(self):
        result = "%s=\"%s\"" % (self.case, self.attribute.__repr__())
        if self.disregardIndex :
            result += ',disregardIndex=True'
        if self.allChildren :
            result += ',allChildren=True'
        return "%s(%s)" % (self.__class__.__name__, result)
    def __init__(self, **kwargs) :
        """ Supports same arguments as used in Maya Python scriptJob command, one of:
            attributeChange = 'plug'
            attributeDeleted = 'plug'
            attributeAdded = 'plug'
            connectionChange = 'plug'
            where plug is a valid Maya plug ('node.attribute') as well as optionnal arguments:
            disregardIndex = True, allChildren = True""" 
        for arg in kwargs.keys() :
            if ScriptJobTrigger.validTriggers.get(arg, None).__name__ == self.__class__.__name__ :
                v = kwargs[arg]
                if arg == 'disregardIndex' and v==True :
                    self.disregardIndex = True
                elif arg == 'allChildren' and v==True :
                    self.allChildren = True
                else :
                    plug = None
                    if not isinstance(v, Attribute) :
                        plug = PyNode(unicode(v))
                    else :
                        plug = v
                    if isinstance(plug, Attribute) and plug.objExists() : 
                        self.case = arg   
                        self.attribute = plug
                    else :
                        raise ValueError, "Plug does not exist: '%s'" % (plug)
            else :
                raise ValueError, 'Invalid argument: '+arg                
        if not isinstance(self.attribute, Attribute) :
            raise ValueError, 'One plug (node.attribute) must be specified for a ScriptJobAttribute trigger'
    def arguments(self) :
        if self.attribute is not None and self.case is not None :
            result = []
            if self.disregardIndex :
                result.append(u'disregardIndex=True')
            if self.allChildren :
                result.append(u'allChildren=True')                
            result.append(u"%s=\"%s.%s\"" %(self.case, self.attribute.node(), self.attribute.plug()))
            return result

# scriptJobs triggered by the deletion on a Maya UI object
class ScriptJobUI(ScriptJobTrigger):
    "Deleted UI trigger for scriptJobs"
    ui = None
    def __repr__(self):
        return "%s(uiDeleted=%s)" % (self.__class__.__name__, self.ui.__repr__())
    def __init__(self, **kwargs):
        if len(kwargs) == 1 :
            arg = kwargs.keys()[0]
            if ScriptJobTrigger.validTriggers.get(arg, None) == self.__class__ :
                # accept both UI and ui name
                ui = UI(unicode(kwargs[arg]))
                if ui.exists() :
                    self.ui = ui
                else :
                    raise ValueError, 'Unknown UI: '+ui                
            else :
                raise ValueError, 'Invalid argument: '+arg
        else :
            raise ValueError, 'One and only one Maya valid UI name must be specified for a ScriptJobUI trigger'
    def arguments(self):
        result = []
        if self.ui is not None :
            result[0] = "uiDeleted=\"%s\"" %(self.ui)
            return result

# Init the scriptJobTypes singleton

#getmembers(pymel, lambda x:isinstance(x, (types.ClassType, type)) and issubclass(x, Node))

def _buildScriptJobTrigger(**kwargs) :
    "Returns a ScriptJobTrigger of the correct type, accepts same arguments as used in the Maya Python scriptJob command"
    triggerType = ScriptJobTrigger
    for arg in kwargs :
        if ScriptJobTrigger.validTriggers.has_key(arg) :
            argType = ScriptJobTrigger.validTriggers[arg]
            if triggerType == ScriptJobTrigger :
                triggerType = argType
            else :
                if triggerType is not argType :
                    raise ValueError, 'These arguments are incompatible and cannot be used together to create a scriptJob: '+unicode(kwargs.keys())
        else :
            raise ValueError, 'Invalid argument: '+arg
    trigger = triggerType(**kwargs)
    # print trigger
    return trigger
      
# Generic scriptJob definition class
class ScriptJob(object) :
    " A class to represent Maya scriptJobs "
    validPrerogatives = ('protected', 'permanent')
    prerogative = None
    killWithScene = False
    runOnce = False
    compressUndo = False
    parentUI = None            # optionnal parent UI object
    trigger = ScriptJobTrigger()
    job = None
    jobLang = None
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(map(lambda x:"%s" % x, self.arguments())) )
    def __init__(self, job=None, **kwargs):
        theJob = job
        # Can be a python or MEL job, specified as a callable (Python) or a code snipper string (Python or Mel)
        if callable(theJob) :
            self.jobLang = 'Python'
            self.job = theJob
        elif isinstance(theJob, basestring) :
            language = kwargs.get('language', None)
            if language is None :
                # default to Python unless parsing below can get us an hint
                language = 'Python'
                # is it MEL (very limited parsing)
                if mm.eval("exists "+theJob.split('()')) :
                    language = 'Mel'
                else :
                    # is it Python
                    try :
                        compile(theJob, '%s(job="%s")' % (self.__class__.__name__, theJob), 'exec')
                        language = 'Python'
                    except :
                        pass
            self.jobLang = language
        else :
            raise TypeError, 'ScriptJob job must be either a Python callable (taking no argument) or a string (a Python or Mel code snippet)'
        # What kind of scriptJob trigger are we using, filter arguments that specify trigger options
        triggerArgs = {}
        for arg in kwargs :
            if ScriptJobTrigger.validTriggers.has_key(arg) :
                triggerArgs[arg] = kwargs[arg]
        self.trigger = _buildScriptJobTrigger(**triggerArgs)
        # Non type specific arguments
        prerogative = kwargs.get('prerogative', None)
        if prerogative is not None :
            if prerogative in self.validPrerogatives :
                self.prerogative = prerogative;
            else :
               raise ValueError, "ScriptJob prerogative can be: "+", ".join(map(lambda x:"'%s'" % x, list))
        parentUI = kwargs.get('parentUI', None)
        if parentUI is not None :        
            self.parentUI = UI(parentUI)
        self.killWithScene = kwargs.get('killWithScene', False);
        self.runOnce = kwargs.get('runOnce', False);
        self.compressUndo = kwargs.get('compressUndo', False);
    def arguments(self):
        result = []
        if self.prerogative is not None :
            result.append('-'+self.prerogative)
        if self.killWithScene :
            result.append('-killWithScene')
        if self.runOnce :
            result.append('-runOnce true')            
        if self.compressUndo :
            result.append('-compressUndo true') 
        if self.parentUI is not None :
            result.append('-parent')
            result.append("\"%s\"" %(self.parentUI))
        result += self.trigger.arguments()
        if self.jobLang is 'Python' :
            if callable(self.job) :
                result.append('"'+cmds.encodeString('python("'+unicode(self.job.__name__)+'()")')+'"')                
            else :
                result.append('"'+cmds.encodeString('python("'+unicode(self.job)+'")')+'"')
        elif self.jobLang is 'Mel' :
            result.append('"'+cmds.encodeString(unicode(self.job))+'"')
        else :
            raise ValueError, 'Job language '+unicode(self.jobLang)+' not supported'        
        return result        
    def string(self):
        "Build the MEL scriptJob definition string corresponding to a ScriptJob object"
        # return ' '.join(map(lambda x:'"'+x+'"', self.arguments()))
        return ' '.join(self.arguments())
    def parse(self, string):
        "Parse a MEL scriptJob definition string and creates the corresponding arguments to create a ScriptJob object"
        result = []
        if self.prerogative is not None :
            result.append('-'+self.prerogative)
        if self.killWithScene :
            result.append('-killWithScene')
        if self.runOnce :
            result.append('-runOnce true')            
        if self.compressUndo :
            result.append('-compressUndo true') 
        return result

# redefine maya.cmds scriptJob in a more logical way (job name, then list of keywords arguments) 

def scriptJob (job = None, **kwargs) :
    pass

# factory function to construct right scriptJob from the MEL scriptJob string

def parseScriptJobMel(s):
    """ Parse a MEL scriptJob definition string and returns arguments to create a ScriptJob object,
        with the job as first argument"""
    result = []
#    if self.prerogative is not None :
#        result.append('-'+self.prerogative)
#    if self.killWithScene :
#        result.append('-killWithScene')
#    if self.runOnce :
#        result.append('-runOnce true')            
#    if self.compressUndo :
#        result.append('-compressUndo true') 
    return result
    
# A faire : etendre pour pouvoir gerer les callbacks API qui ne sont pas disponibles en
# tant que scriptJobs directement
#
#class ActiveScriptJobs(object):
#    "A dictionary-like class for modifying Maya scriptJobs:"
#    def __repr__(self):
#        listJobs = cmds.scriptJob(listJobs=True)
#        for line in listJobs :
#            parts = line.split(':')
#            result.append(parts)
#        return dict(result).__repr__()        
#    def __contains__(self, key):
#        return cmds.scriptJob( exists=key )
#    def __getitem__(self,key):
#        if self.__contains__(key) :
#            istJobs = cmds.scriptJob(listJobs=True)
#            result = ScriptJob();
#            for line in listJobs :
#                parts = line.split(':')
#                if len(parts) > 1 :
#                    if parts[0] == str(key) :
#                        result = parseScriptJob(parts[1])
#            return 
#        else :
#            raise KeyError, 'There is no active scriptJob with id: '+str(key)    
#    def __setitem__(self,key,val):
#        if isinstance( val, ScriptJob):
#            pass
#        else :
#            pass           
#    def __delitem__(self, key) :
#        if key == 'all' :
#            cmds.scriptJob( killAll=true, force=force )
#        elif self.has_key(key) :
#            scriptJob = self.get(key)
#            cmds.scriptJob( kill=key, force=force )
#        else :
#            raise KeyError, 'There is no active scriptJob with id: '+str(key)        
#    def __iter__(self) :
#        return iter(self.keys())
#    def __len__(self) :
#        return len(cmds.scriptJob(listJobs=True))
#    def keys(self):
#        result = []
#        listJobs = cmds.scriptJob(listJobs=True)
#        for line in listJobs :
#            parts = line.split(':')
#            if len(parts) > 0 :
#                result.append(int(parts[0]))
#        return result
#    def find (self, value):
#        listJobs = cmds.scriptJob(listJobs=True)
#        for line in listJobs :
#            parts = line.split(':')
#            if len(parts) > 1 :
#                if parts[1] == value :
#                    return (int(parts[0]))
#    def get(self, key, default=None):
#        if self.has_key(key):
#            return self[key]
#        elif default is not None :
#            return default
#    def has_key(self, key):
#        return cmds.scriptJob( exists=key )
#    def kill(self, key, force=False):
#        if key == 'all' :
#            cmds.scriptJob( killAll=true, force=force )
#        elif seld.has_key(key) :
#            scriptJob = self.get(key)
#            cmds.scriptJob( kill=key, force=force )
#            return scriptJob
#        else :
#            raise IndexError, 'There is no registered scriptJob with id: '+str(key)
#        
## Create the global ActiveScriptJobs dictionary for all scriptJobs currently active in Maya
#activeScriptJobs = ActiveScriptJobs()

from math import *
from pymel.util.mathutils import *
import system
#from pymel.util.arrays import *  # conflicts with wrappedtypes.Vector
from pmtypes.wrappedtypes import *
import pymel.util as util
import maya.mel as mm
import pymel.mayahook.pmcmds as cmds
import os
import pymel.factories as _factories
#--------------------------
# Mel <---> Python Glue
#--------------------------  
  
def pythonToMel(arg):
    if util.isNumeric(arg):
        return str(arg)
    if util.isIterable(arg):
        return '{%s}' % ','.join( map( pythonToMel, arg) )
    
    # in order for PyNodes to get wrapped in quotes we have to treat special cases first,
    # we cannot simply test if arg is an instance of basestring because PyNodes are not  
    return '"%s"' % cmds.encodeString(str(arg))

# TODO : convert array variables to a semi-read-only list ( no append or extend, += is ok ): 
# using append or extend will not update the mel variable 
class MelGlobals( util.Singleton, dict ):
    """ A dictionary-like class for getting and setting global variables between mel and python.
    an instance of the class is created by default in the pymel namespace as melGlobals.
    
    to retrieve existing global variables, just use the name as a key
    
    >>> melGlobals['gMainFileMenu']
    mainFileMenu
    >>> # works with or without $
    >>> melGlobals['$gGridDisplayGridLinesDefault']
    1
    
    creating new variables requires the use of the initVar function to specify the type
    
    >>> melGlobals.initVar( 'string', 'gMyStrVar' )
    >>> melGlobals['gMyStrVar'] = 'fooey'
    
    """
    melTypeToPythonType = {
        'string'    : str,
        'int'       : int,
        'float'     : float,
        'vector'    : MVector
        }

#    class MelGlobalArray1( tuple ):
#        def __new__(cls, type, variable, *args, **kwargs ): 
#             
#            self = tuple.__new__( cls, *args, **kwargs )
#            
#            decl_name = variable
#            if type.endswith('[]'):
#                type = type[:-2]
#                decl_name += '[]'
#                
#            self._setItemCmd = "global %s %s; %s" % ( type, decl_name, variable )
#            self._setItemCmd += '[%s]=%s;'
#            return self
#        
#        def setItem(self, index, value ):
#            mm.eval(self._setItemCmd % (index, value) )

    class MelGlobalArray( util.defaultlist ):
        #__metaclass__ = util.metaStatic
        def __init__(self, type, variable, *args, **kwargs ): 
            
            decl_name = variable
            if type.endswith('[]'):
                type = type[:-2]
                decl_name += '[]'
            
            pyType = MelGlobals.melTypeToPythonType[ type ]
            util.defaultlist.__init__( self, pyType, *args, **kwargs )
             
               
            self._setItemCmd = "global %s %s; %s" % ( type, decl_name, variable )
            self._setItemCmd += '[%s]=%s;'

        
        def setItem(self, index, value ):
            mm.eval(self._setItemCmd % (index, value) )
        
        # prevent these from 
        def append(self, val): raise AttributeError
        def __setitem__(self, item, val): raise AttributeError
        def extend(self, val): raise AttributeError
        
    
    
    typeMap = {}
    validTypes = util.MELTYPES
    def _formatVariable(self, variable):
        # TODO : add validity check
        if not variable.startswith( '$'):
            variable = '$' + variable
        return variable
    
    def getType(self, variable):
        variable = self._formatVariable(variable)
        info = mel.whatIs( variable ).split()
        if len(info)==2 and info[1] == 'variable':
            return info[0]
        raise TypeError, "Cannot determine type for this variable. Use melGlobals.initVar first."
    
    def __getitem__(self, variable ):
        return self.get( variable )
    
    def __setitem__(self, variable, value):
        return self.set( variable, value )
        
    def initVar( self, type, variable ):
        if type not in MelGlobals.validTypes:
            raise TypeError, "type must be a valid mel type: %s" % ', '.join( [ "'%s'" % x for x in MelGlobals.validTypes ] )
        variable = self._formatVariable(variable)
        MelGlobals.typeMap[variable] = type
        return variable
    
    def get( self, variable, type=None  ):
        """get a MEL global variable.  If the type is not specified, the mel ``whatIs`` command will be used
        to determine it.""" 
        
        variable = self._formatVariable(variable)
        if type is None:
            try:
                type = MelGlobals.typeMap[variable]
            except KeyError:
                type = self.getType(variable)
            
        variable = self.initVar(type, variable)
        
        ret_type = type
        decl_name = variable
        
        if type.endswith('[]'):
            array=True
            type = type[:-2]
            proc_name = 'pymel_get_global_' + type + 'Array'
            if not decl_name.endswith('[]'):
                decl_name += '[]'
        else:
            array=False
            proc_name = 'pymel_get_global_' + type
            
        cmd = "global proc %s %s() { global %s %s; return %s; } %s();" % (ret_type, proc_name, type, decl_name, variable, proc_name )
        #print cmd
        res = mm.eval( cmd  )
        if array:
            return MelGlobals.MelGlobalArray(ret_type, variable, res)
        else:
            return res
    
    def set( self, variable, value, type=None ):
        """set a mel global variable""" 
        variable = self._formatVariable(variable)
        if type is None:
            try:
                type = MelGlobals.typeMap[variable]
            except KeyError:
                type = self.getType(variable)
                
        variable = self.initVar(type, variable)
        decl_name = variable
        if type.endswith('[]'):
            type = type[:-2]
            decl_name += '[]'
            
        cmd = "global %s %s; %s=%s;" % ( type, decl_name, variable, pythonToMel(value) )
        #print cmd
        mm.eval( cmd  )
    
    def keys(self):
        """list all global variables"""
        return mel.env()
    
melGlobals = MelGlobals()

# for backward compatibility               
def getMelGlobal(type, variable) :
    return melGlobals.get(variable, type)
def setMelGlobal(type, variable, value) :
    return melGlobals.set(variable, value, type)

    
class Catch(util.Singleton):
    """Reproduces the behavior of the mel command of the same name. if writing pymel scripts from scratch, you should
        really use the try/except structure. This command is provided for python scripts generated by py2mel.  stores the
        result of the function in catch.result.
        
        >>> if not catch( lambda: myFunc( "somearg" ) ):
        >>>    result = catch.result
        >>>    print "succeeded:", result
        
        """
    result = None
    success = None
    def __call__(self, func ):
        try:
            Catch.result = func()
            Catch.success = True
            return 0
        except:
            Catch.success = False
            return 1
        
    def reset(self):
        Catch.result = None
        Catch.success = None 

catch = Catch()
             
#--------------------------
# Maya.mel Wrapper
#--------------------------
    
class Mel(object):
    """This class is a necessity for calling mel scripts from python. It allows scripts to be called
    in a cleaner fashion, by automatically formatting python arguments into a string 
    which is executed via maya.mel.eval().  An instance of this class is already created for you 
    when importing pymel and is called mel.  
    
    default:        
        >>> import maya.mel as mel
        >>> mel.eval( 'myScript("firstArg", 2, 3.0, {"one", "two", "three"})')
            
    pymel:
        >>> from pymel import *
        >>> mel.myScript("firstArg", 2, 3.0, ['one', 'two', 'three'])
        
    the advantages of this method are more readily apparent in a more complicated example:
    
    default:        
        >>> import cmds as cmds
        >>> pymel.core.node = "lambert1"
        >>> color = cmds.getAttr( pymel.core.node + ".color" )[0]
        >>> mel.eval('myScript("%s",{%s,%s,%s})' % (cmds.nodeType(pymel.core.node), color[0], color[1], color[2])    
            
    pymel:
        >>> from pymel import *
        >>> pymel.core.node = DependNode("lambert")
        >>> mel.myScript( type(), color.get() )
    
    from this you can see how pymel.core.mel allows you to pass any python object directly to your mel script as if 
    it were a python script, with no need for formatting arguments.
    """
            
    def __getattr__(self, command):
        if command.startswith('__') and command.endswith('__'):
            return self.__dict__[command]
        def _call(*args):
        
            strArgs = map( pythonToMel, args)
                            
            cmd = '%s(%s)' % ( command, ','.join( strArgs ) )
            #print cmd
            try:
                return mm.eval(cmd)
            except RuntimeError, msg:
                info = self.whatIs( command )
                if info.startswith( 'Presumed Mel procedure'):
                    raise NameError, 'Unknown Mel procedure'
                raise RuntimeError, msg
            
        return _call
    
    def call(self, command, *args ):
        strArgs = map( pythonToMel, args)
                        
        cmd = '%s(%s)' % ( command, ','.join( strArgs ) )

        try:
            return mm.eval(cmd)
        except RuntimeError, msg:
            info = self.whatIs( command )
            if info.startswith( 'Presumed Mel procedure'):
                raise NameError, 'Unknown Mel procedure'
            raise RuntimeError, msg
    
    def mprint(self, *args):
        """mel print command in case the python print command doesn't cut it. i have noticed that python print does not appear
        in certain output, such as the rush render-queue manager."""
        #print r"""print (%s\\n);""" % pythonToMel( ' '.join( map( str, args))) 
        mm.eval( r"""print (%s);""" % pythonToMel( ' '.join( map( str, args))) + '\n' )
        
    def source( self, script, language='mel' ):
        """use this to source mel or python scripts.
        language : 'mel', 'python'
            When set to 'python', the source command will look for the python equivalent of this mel file, if
            it exists, and attempt to import it. This is particularly useful when transitioning from mel to python
            via mel2py, with this simple switch you can change back and forth from sourcing mel to importing python.
            
        """
        
        if language == 'mel':
            mm.eval( """source "%s";""" % script )
            
        elif language == 'python':
            script = _path.path( script )
            modulePath = script.namebase
            folder = script.parent
            print modulePath
            if not sys.modules.has_key(modulePath):
                print "importing"
                module = __import__(modulePath, globals(), locals(), [''])
                sys.modules[modulePath] = module
            
        else:
            raise TypeError, "language keyword expects 'mel' or 'python'. got '%s'" % language
            
    def eval( self, command ):
        # should return a value, like mm.eval
        return mm.eval( command )    
    
    def error( self, msg, showLineNumber=False ):       
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        mm.eval( """error %s %s""" % ( flags, pythonToMel( msg) ) )

    def warning( self, msg, showLineNumber=False ):       
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        mm.eval( """warning %s %s""" % ( flags, pythonToMel( msg) ) )

    def trace( self, msg, showLineNumber=False ):       
        if showLineNumber:
            flags = ' -showLineNumber true '
        else:
            flags = ''
        mm.eval( """trace %s %s""" % ( flags, pythonToMel( msg) ) )
                  
    def tokenize(self, *args ):
        raise NotImplementedError, "Calling the mel command 'tokenize' from python will crash Maya. Use the string split method instead."

mel = Mel()



#-----------------------------------------------
#  Option Variables
#-----------------------------------------------

class OptionVarList(tuple):
    def __init__(self, key, val):
        self.key = key
        tuple.__init__(self, val)
    
    def appendVar( self, val ):
        """ values appended to the OptionVarList with this method will be added to the Maya optionVar at the key denoted by self.key.
        """

        if isinstance( val, basestring):
            return cmds.optionVar( stringValueAppend=[self.key,val] )
        if isinstance( val, int):
            return cmds.optionVar( intValueAppend=[self.key,val] )
        if isinstance( val, float):
            return cmds.optionVar( floatValueAppend=[self.key,val] )
        raise TypeError, 'unsupported datatype: strings, ints, floats and their subclasses are supported'

class OptionVarDict(util.Singleton):
    """ 
    A singleton dictionary-like class for accessing and modifying optionVars.
     
        >>> from pymel import *
        >>> optionVar['test'] = 'dooder'
        >>> print optionVar['test'] 
        u'dooder'
        
        >>> if 'numbers' not in env.optionVars:
        >>>     optionVar['numbers'] = [1,24,7]
        >>> optionVar['numbers'].appendVar( 9 )
        >>> numArray = optionVar.pop('numbers') 
        >>> print numArray
        [1,24,7,9]
        >>> optionVar.has_key('numbers') # previous pop removed the key
        False
    """

    def __contains__(self, key):
        return cmds.optionVar( exists=key )
            
    def __getitem__(self,key):
        val = cmds.optionVar( q=key )
        if isinstance(val, list):
            val = OptionVarList( key, val )
        return val
    def __setitem__(self,key,val):
        if isinstance( val, basestring):
            return cmds.optionVar( stringValue=[key,val] )
        if isinstance( val, int) or isinstance( val, bool):
            return cmds.optionVar( intValue=[key,int(val)] )
        if isinstance( val, float):
            return cmds.optionVar( floatValue=[key,val] )
        if isinstance( val, list ):
            if len(val) == 0:
                return cmds.optionVar( clearArray=key )
            if isinstance( val[0], basestring):
                cmds.optionVar( stringValue=[key,val[0]] ) # force to this datatype
                for elem in val[1:]:
                    if not isinstance( elem, basestring):
                        raise TypeError, 'all elements in list must be of the same datatype'
                    cmds.optionVar( stringValueAppend=[key,elem] )
                return
            if isinstance( val[0], int):
                cmds.optionVar(  intValue=[key,val[0]] ) # force to this datatype
                for elem in val[1:]:
                    if not isinstance( elem, int):
                        raise TypeError,  'all elements in list must be of the same datatype'
                    cmds.optionVar( intValueAppend=[key,elem] )
                return
            if isinstance( val[0], float):
                cmds.optionVar( floatValue=[key,val[0]] ) # force to this datatype
                for elem in val[1:]:
                    if not isinstance( elem, foat):
                        raise TypeError, 'all elements in list must be of the same datatype'
                    cmds.optionVar( floatValueAppend=[key,elem] )
                return

        raise TypeError, 'unsupported datatype: strings, ints, float, lists, and their subclasses are supported'            

    def keys(self):
        return cmds.optionVar( list=True )

    def get(self, key, default=None):
        if self.has_key(key):
            return self[key]
        else:
            return default
        
    def has_key(self, key):
        return cmds.optionVar( exists=key )

    def pop(self, key):
        val = cmds.optionVar( q=key )
        cmds.optionVar( remove=key )
        return val
    
optionVar = OptionVarDict()



class Env(util.Singleton):
    """ A Singleton class to represent Maya current optionVars and settings """
    optionVars = OptionVarDict()
    #grid = Grid()
    #playbackOptions = PlaybackOptions()
    
    # TODO : create a wrapper for os.environ which allows direct appending and popping of individual env entries (i.e. make ':' transparent)
    envVars = os.environ

    def setConstructionHistory( self, state ):
        cmds.constructionHistory( tgl=state )
    def getConstructionHistory(self):
        return cmds.constructionHistory( q=True, tgl=True )    
    def sceneName(self):
        return system.Path(cmds.file( q=1, sn=1))

    def setUpAxis( axis, rotateView=False ):
        """This flag specifies the axis as the world up direction. The valid axis are either 'y' or 'z'."""
        cmds.upAxis( axis=axis, rotateView=rotateView )
    
    def getUpAxis(self):
        """This flag gets the axis set as the world up direction. The valid axis are either 'y' or 'z'."""
        return cmds.upAxis( q=True, axis=True )    

    def user(self):
        return getuser()    
    def host(self):
        return gethostname()
    
    def getTime( self ):
        return cmds.currentTime( q=1 )
    def setTime( self, val ):
        cmds.currentTime( val )    
    time = property( getTime, setTime )

    def getMinTime( self ):
        return cmds.playbackOptions( q=1, minTime=1 )
    def setMinTime( self, val ):
        cmds.playbackOptions( minTime=val )
    minTime = property( getMinTime, setMinTime )

    def getMaxTime( self ):
        return cmds.playbackOptions( q=1, maxTime=1 )
    def setMaxTime( self, val ):
        cmds.playbackOptions( maxTime=val )    
    maxTime = property( getMaxTime, setMaxTime )
            
env = Env()

def conditionExists(conditionName):
	"""
	Returns True if the named condition exists, False otherwise.
	
	Note that 'condition' here refers to the type used by 'isTrue' and 'scriptJob', NOT to the condition NODE.
	"""
	return conditionName in cmds.scriptJob(listConditions=True)
	

_factories.createFunctions( __name__ )

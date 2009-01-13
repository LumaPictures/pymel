import os
import pymel.util as util
import maya.cmds as cmds
#-----------------------------------------------
#  Option Variables
#-----------------------------------------------

class OptionVarList(tuple):
    
    def __new__(cls, val, key):
        self = tuple.__new__(cls, val)
        return self
    
    def __init__(self, val, key):
        tuple.__init__(self, val)
        self.key = key    
        
    
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

    append = appendVar

class OptionVarDict(object):
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
    __metaclass__ = util.Singleton
    def __call__(self, *args, **kwargs):
        return cmds.optionVar(*args, **kwargs)
    
    def __contains__(self, key):
        return self.has_key(key)
        
    def has_key(self, key):
        return cmds.optionVar( exists=key )
                
    def __getitem__(self,key):
        val = cmds.optionVar( q=key )
        if isinstance(val, list):
            val = OptionVarList( val, key )
        return val

    def get(self, key, default=None):
        if self.has_key(key):
            return self[key]
        else:
            return default
    
    def __setitem__(self,key,val):
        if isinstance( val, basestring):
            return cmds.optionVar( stringValue=[key,val] )
        if isinstance( val, (int, bool)):
            return cmds.optionVar( intValue=[key,int(val)] )
        if isinstance( val, float):
            return cmds.optionVar( floatValue=[key,val] )
        if isinstance( val, (list,tuple) ):
            if len(val) == 0:
                return cmds.optionVar( clearArray=key )
            listType = type(val[0])
            if issubclass( listType , basestring):
                flag = 'stringValue'
            elif issubclass( listType , int):
                flag = 'intValue'
            elif issubclass( listType , float):
                flag  = 'floatValue'
            else:
                raise TypeError, ('%r is unsupported; Only strings, ints, float, lists, and their subclasses are supported' % listType)
            
            cmds.optionVar(**{flag:[key,val[0]]}) # force to this datatype
            flag += "Append"
            for elem in val[1:]:
                if not isinstance( elem, listType):
                    raise TypeError, 'all elements in list must be of the same datatype'
                cmds.optionVar( **{flag:[key,elem]} )

    def keys(self):
        return cmds.optionVar( list=True )


    def pop(self, key):
        val = cmds.optionVar( q=key )
        cmds.optionVar( remove=key )
        return val
    
    def __delitem__(self,key):
        self.pop(key)
    
optionVar = OptionVarDict()

class Env(object):
    """ A Singleton class to represent Maya current optionVars and settings """
    __metaclass__ = util.Singleton
    
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

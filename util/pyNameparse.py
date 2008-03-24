import re

#--------------------------
# Basic Name class (valid names)

# Holds the object name as well as basic patterns and regex for valid object names in Maya
# for names parsing
class MayaName(unicode):
    """ Cast a string or unicode to that class to get a Maya name string checked for validity
        ( in the sense of being well formed and not containing invalid characters ), it also defines
        a dictionnary of invalid regular expressions and associated error messages.
        invalid pattern should be searched with re.findall (any occurrence means an error)
        valid pattern should be matched with re.match (must have an exact match) """
    invalid = {}
    invalidChar = r"^(a-z)^(A-Z)^(0-9)^_"
    invalid['invalidChar'] = (re.compile(r"(["+invalidChar+"])+"), "invalid character in name")
    invalidFirstChar = r"^[0-9]+"
    invalid['invalidFirstChar'] = (re.compile(r"("+invalidFirstChar+")"), "first character in name cannot be a number")
    pattern = r"[a-zA-Z_][a-zA-Z0-9_]*"
    valid = re.compile(r"("+pattern+")")
    
class NameSpace(MayaName):
    """ Cast a string or unicode to that class to get a Maya nameSpace string checked for validity
        ( in the sense of being well formed and not containing invalid characters ), it also defines
        a list of invalid regular expressions and associated error messages.
        invalid pattern should be searched with re.findall (any occurrence means an error)
        valid pattern should be matched with re.match (must have an exact match) """
    invalid = {}
    invalidChar = MayaName.invalidChar+"^:"
    invalid['invalidChar'] = (re.compile(r"(["+invalidChar+"])+"), "invalid character in name")
    invalidFirstChar = r":[0-9]+"
    invalid['invalidFirstChar'] = (re.compile(r"("+invalidFirstChar+")"), "first character in name cannot be a number")    
    pattern = r":?((?:"+MayaName.pattern+r":)*)"
    valid = re.compile(pattern)   
     
class ShortObjectName(NameSpace):
    pattern = NameSpace.pattern+r"("+MayaName.pattern+")"
    valid = re.compile(pattern) 
            
class ObjectName(ShortObjectName, NameSpace):
    pattern = r"(:?(?:"+NameSpace.pattern+r")*)("+ShortObjectName.pattern+r")"
    valid = re.compile(pattern)
    
class LongObjectName(ObjectName):
    pass
            
class ShortAttributeName(MayaName):
    pattern = r"([a-zA-Z]+[a-zA-Z0-9_]*)(\[[0-9]+\])?"
    valid = re.compile(pattern)     

class LongAttributeName(ShortAttributeName):
    pattern = r"\.?("+ShortAttributeName.pattern+r")(\."+ShortAttributeName.pattern+r")*"
    valid = re.compile(pattern)   

PlugName = LongAttributeName
        
class UIName(MayaName):
    pass

class GlobName(unicode):
    """ Cast a string or unicode to that class to get a glob name string checked for validity
        ( in the sense of being well formed and not containing invalid characters ) """
    invalidCharPattern = r"[^(a-z)^(A-Z)^(0-9)^_^*^?^:^|]"
    invalid = re.compile(r"("+invalidCharPattern+")+")    
    firstGlob = r"[a-zA-Z_*?]"
    charGlob = r"[a-zA-Z0-9_*?]"
    nameSpaceGlob = ""
    pattern = r"|?:?(?:"+firstGlob+charGlob+"*:)*("
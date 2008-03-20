import re

#--------------------------
# Basic Name class (valid names)

# Holds the object name as well as basic patterns and regex for valid object names in Maya
# for names parsing
class GlobName(unicode):
    """ Cast a string or unicode to that class to get a glob name string checked for validity
        ( in the sense of being well formed and not containing invalid characters ) """
    invalidCharPattern = r"[^(a-z)^(A-Z)^(0-9)^_^*^?^:]"
    validCharPattern = r"[a-zA-Z0-9_]"
    invalid = re.compile(r"("+invalidCharPattern+")+")

class MayaName(unicode):
    """ Cast a string or unicode to that class to get a Maya name name string checked for validity
        ( in the sense of being well formed and not containing invalid characters ) """
    invalidCharPattern = r"[^(a-z)^(A-Z)^(0-9)^_^:]"
    invalid = re.compile(r"("+invalidCharPattern+")+")
    pattern = r"[a-z_][a-zA-Z0-9_]*"
    valid = re.compile(r"("+pattern+")+")
    
class NameSpace(MayaName):
    pattern = r"[a-zA-Z]+[a-zA-Z0-9_]*:"
    valid = re.compile(r"^:?"+"("+pattern+")*")   
     
class ShortObjectName(MayaName):
    pattern = r"[a-zA-Z]+[a-zA-Z0-9_]*"
    valid = re.compile(pattern) 
            
class ObjectName(ShortObjectName, NameSpace):
    pattern = r"(^:?(?:"+NameSpace.pattern+r")*)("+ShortObjectName.pattern+r")$"
    valid = re.compile(pattern)
    
class LongObjectName(ObjectName):
    pass
            
class ShortAttributeName(MayaName):
    pattern = r"([a-zA-Z]+[a-zA-Z0-9_]*)(\[[0-9]+\])?"
    valid = re.compile(pattern)     

class LongAttributeName(ShortAttributeName):
    pattern = r"\.?("+ShortAttributeName.pattern+r")(\."+ShortAttributeName.pattern+r")*"
    valid = re.compile(pattern)   
        
class UIName(MayaName):
    pass
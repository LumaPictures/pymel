"""
    Redefine format warning to avoid getting garbage at end of line when raised directly from Maya console
    and define a UserWarning class that does only print it's message (no line or module info)
"""
import os.path
from warnings import *

def formatwarning(message, category, filename, lineno):
    """Redefined format warning for maya."""
    if issubclass(category, ExecutionWarning) :
        s =  unicode("%s: %s\n") % (category.__name__, message)
    else :
        s =  unicode("%s: %s\n at line: %s in %s\n") % (category.__name__, message, lineno, filename)
        name, ext = os.path.splitext(filename)
        line = None
        if ext == ".py" :
            line = unicode(warnings.linecache.getline(filename, lineno)).strip()
        if line and len(line) > 0 :
            s = s + " " + line + "\n"
    return s


class ExecutionWarning (UserWarning) :
    """ Simple Warning class that doesn't print any information besides warning message """
    

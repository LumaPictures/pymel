"""
    Redefine format warning to avoid getting garbage at end of line when raised directly from Maya console
    and define a UserWarning class that does only print it's message (no line or module info)
    
    >>> import sys
    >>> sys.stderr = sys.stdout
    >>> warn("An ExecutionWarning", ExecutionWarning) #doctest: +ELLIPSIS
    /...ExecutionWarning: An ExecutionWarning...
    
"""

import os.path
from warnings import defaultaction, filters, filterwarnings, formatwarning, linecache, onceregistry, resetwarnings, showwarning, simplefilter, warn, warn_explicit

def formatwarning(message, category, filename, lineno):
    """Redefined format warning for maya."""
    if issubclass(category, ExecutionWarning) :
        s =  unicode("%s: %s\n") % (category.__name__, message)
    else :
        s =  unicode("%s: %s\n at line: %s in %s\n") % (category.__name__, message, lineno, filename)
        name, ext = os.path.splitext(filename)
        line = None
        if ext == ".py" :
            line = unicode(linecache.getline(filename, lineno)).strip()
        if line and len(line) > 0 :
            s = s + " " + line + "\n"
    return s


class ExecutionWarning (UserWarning) :
    """ Simple Warning class that doesn't print any information besides warning message """
  
if __name__ == '__main__' :
    import doctest
    doctest.testmod()   
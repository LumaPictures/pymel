"""
    Redefine format warning to avoid getting garbage at end of line when raised directly from Maya console
    and define a UserWarning class that does only print it's message (no line or module info)
    
    >>> import sys
    >>> sys.stderr = sys.stdout   
    >>> warn("An ExecutionWarning", ExecutionWarning) #doctest: +ELLIPSIS
    ExecutionWarning: An ExecutionWarning
    
"""

import os.path
import warnings
from warnings import formatwarning, linecache, resetwarnings, simplefilter, warn
# from warnings import simplefilter, warn

def formatwarning(message, category, filename, lineno, line=None):
    """Redefined format warning for maya."""
    if issubclass(category, ExecutionWarning) :
        s =  u"%s: %s\n" % (category.__name__, message)
    else :
        # print "category is", category.__name__
        # print "message is ", message
        # print "lineno is ", lineno
        # print "filename is ", filename
        s =  u"%s: %s\n# at line: %s in %s\n" % (category.__name__, message, lineno, filename)
        name, ext = os.path.splitext(filename)
        line = ""
        if ext == ".py" :
            line = unicode(linecache.getline(filename, lineno)).strip()
        if len(line) > 0 :
            # print "adding line %s" % line
            s = s + u"#\t" + line + u"\n"
        # print "s:\n", s
    return s

warnings.formatwarning = formatwarning

class ExecutionWarning (UserWarning) :
    """ Simple Warning class that doesn't print any information besides warning message """
    
def warn(*args, **kwargs):
    """ Default Maya warn which uses ExecutionWarning as the default warning class. """
    if len(args) == 1 and not isinstance(args[0], Warning):
        args = args + (ExecutionWarning,)
    return warnings.warn(*args, **kwargs)

if __name__ == '__main__' :
    import doctest
    doctest.testmod()

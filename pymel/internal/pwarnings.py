"""
Redefine format warning to avoid getting garbage at end of line when raised directly from Maya console
and define a UserWarning class that does only print it's message (no line or module info)


"""
import warnings
from warnings import formatwarning, linecache

def formatwarning(message, category, filename, lineno, line=None):
    """Redefined format warning for maya."""
    if issubclass(category, ExecutionWarning) :
        s =  u"%s: %s\n" % (category.__name__, message)
    else :
        s =  u'%s: %s, at line %s, in "%s"\n' % (category.__name__, message, lineno, filename)
#        name, ext = os.path.splitext(filename)
#        line = ""
#        if ext == ".py" :
#            line = unicode(linecache.getline(filename, lineno)).strip()
#            if line:
#                s += (u"#\t %s" % line)
    return s

warnings.formatwarning = formatwarning

#def showwarning(message, category, filename, lineno, file=None, line=None):
#    msg = warnings.formatwarning(message, category, filename, lineno, line)
#    if file:
#        msg += " >> %r" % file
#    _logger.warning(msg)
#
#warnings.showwarning = showwarning

class ExecutionWarning (UserWarning) :
    """ Simple Warning class that doesn't print any information besides warning message """

def warn(*args, **kwargs):
    """ Default Maya warn which uses ExecutionWarning as the default warning class. """
    if len(args) == 1 and not isinstance(args[0], Warning):
        args = args + (ExecutionWarning,)
    stacklevel = kwargs.pop("stacklevel",1) + 1 # add to the stack-level so that this wrapper func is skipped
    return warnings.warn(stacklevel=stacklevel, *args, **kwargs)

def deprecated(funcOrMessage, className=None):
    """the decorator can either receive parameters or the function directly.

    If passed a message, the message will be appended to the standard deprecation warning and should serve to further
    clarify why the function is being deprecated and/or suggest an alternative function

    the className parameter is optional and should be included if the function is a method, since the name of the class
    cannot be automatically determined.
    """
    #@decorator
    def deprecated2(func):
        info = dict(
            name = func.__name__,
            module = func.__module__)

        def deprecationLoggedFunc(*args, **kwargs):
            warnings.warn(message % info, DeprecationWarning, stacklevel=2)  # add to the stack-level so that this wrapper func is skipped
            return func(*args, **kwargs)

        deprecationLoggedFunc.__name__ = func.__name__
        deprecationLoggedFunc.__module__ = func.__module__
        deprecationLoggedFunc.__doc__ = message % info + '\n'
        if func.__doc__:
            deprecationLoggedFunc.__doc__ += '\n' +  func.__doc__
        return deprecationLoggedFunc

    if className:
        objName = '%(module)s.' + className + '.%(name)s'
    else:
        objName = '%(module)s.%(name)s'
    basemessage = message = "The function '" + objName + "' is deprecated and will become unavailable in future pymel versions"
    # check if the decorator got a 'message' parameter
    if isinstance(funcOrMessage, basestring):
        message = basemessage + '. ' + funcOrMessage
        return deprecated2
    else:
        message = basemessage
        return deprecated2(funcOrMessage)

if __name__ == '__main__' :
    import doctest
    doctest.testmod()

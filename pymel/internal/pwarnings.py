"""
Redefine format warning to avoid getting garbage at end of line when raised directly from Maya console
and define a UserWarning class that does only print it's message (no line or module info)


"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future.utils import PY2
from past.builtins import basestring
import warnings


def formatwarning(message, category, filename, lineno, line=None):
    """Redefined format warning for maya."""
    if issubclass(category, ExecutionWarning):
        s = u"%s: %s\n" % (category.__name__, message)
    else:
        s = u'%s: %s, at line %s, in "%s"\n' % (category.__name__, message, lineno, filename)
#        name, ext = os.path.splitext(filename)
#        line = ""
#        if ext == ".py" :
#            line = unicode(linecache.getline(filename, lineno)).strip()
#            if line:
#                s += (u"#\t %s" % line)
    return s

warnings.formatwarning = formatwarning

# def showwarning(message, category, filename, lineno, file=None, line=None):
#    msg = warnings.formatwarning(message, category, filename, lineno, line)
#    if file:
#        msg += " >> %r" % file
#    _logger.warning(msg)
#
#warnings.showwarning = showwarning

# Subclass just to allow users to configure filtering of pymel-specific
# deprecations
class PymelBaseWarning(Warning):
    pass

class ExecutionWarning (UserWarning, PymelBaseWarning):

    """ Simple Warning class that doesn't print any information besides warning message """

class PymelBaseDeprecationWarning(PymelBaseWarning):
    pass

# Subclass from FutureWarning so it's displayed by default
class PymelFutureWarning(FutureWarning, PymelBaseDeprecationWarning):
    pass

# Subclass from DeprecationWarning so it's not displayed by default
class MayaDeprecationWarning(DeprecationWarning, PymelBaseDeprecationWarning):
    pass


def warn(*args, **kwargs):
    """ Default Maya warn which uses ExecutionWarning as the default warning class. """
    if len(args) == 1 and not isinstance(args[0], Warning):
        args = args + (ExecutionWarning,)
    stacklevel = kwargs.pop("stacklevel", 1) + 1  # add to the stack-level so that this wrapper func is skipped
    return warnings.warn(stacklevel=stacklevel, *args, **kwargs)


def deprecated(funcOrMessage=None, className=None,
               baseMessage="The function '{objName}' is deprecated and will"
                           " become unavailable in future pymel versions",
               warningType=PymelFutureWarning):
    """Decorates a function so that it prints a deprecation warning when called.

    The decorator can either receive parameters or the function directly.

    Parameters
    ----------
    funcOrMessage : Union[str, Callable[..., Any], None]
        If passed a message, the message will be appended to the standard
        deprecation warning and should serve to further clarify why the function
        is being deprecated and/or suggest an alternative function. In this
        case, the return result of this function is another decorator (with the
        ammended message), which then needs to be fed the function to be
        decorated. Otherwise, funcOrMessage should be the func to be decorated,
        and the return result is decorated version of funcOrMessage
    className : Union[str, False, None]
        If given as a str, then the decorated function is asssumed to be method,
        and the name is printed as "module.className.funcName".  If False, it
        is assumed to NOT be a method, and the name is printed as
        "module.funcName".  If None, then the decorator will try to
        automatically determine whether the passed function is a method, and if
        so, what it's className is.
    baseMessage : Optional[str]
        Message which will be combined with the optional message (in
        funcOrMessage) to form the final message. Maybe set to None to ensure
        only the message (in funcOrMessage) is printed.
    warningType : Type[Warning]
        Warning class to raise. Note that DeprecationWarning is ignored by
        default.
    """
    import inspect

    def isClassMethodOrMethod(test_func):
        isClassMethod = False
        isMethod = False
        args = list(inspect.signature(test_func).parameters)
        if args:
            if args[0] == 'cls':
                isClassMethod = True
            elif args[0] == 'self':
                isMethod = True
        return isClassMethod, isMethod

    if PY2:
        def isClassMethodOrMethod(test_func):
            isClassMethod = False
            isMethod = False
            args = inspect.getargspec(test_func).args
            if args:
                if args[0] == 'cls':
                    isClassMethod = True
                elif args[0] == 'self':
                    isMethod = True
            return isClassMethod, isMethod

    #@decorator
    def deprecated2(func):
        useClassName = False
        info = dict(
            name=func.__name__,
            module=func.__module__)

        if className is None:
            isClassMethod, isMethod =isClassMethodOrMethod(func)
            if isClassMethod or isMethod:
                useClassName = True
        elif className is not False:
            useClassName = True
            info['className'] = className

        if useClassName:
            objName = '%(module)s.%(className)s.%(name)s'
        else:
            objName = '%(module)s.%(name)s'
        message2 = message.format(objName=objName)

        def deprecationLoggedFunc(*args, **kwargs):
            if useClassName and className is None:
                if isClassMethod:
                    info['className'] = args[0].__name__
                else:
                    info['className'] = type(args[0]).__name__
            # add to the stack-level so that this wrapper func is skipped
            warnings.warn(message2 % info, warningType, stacklevel=2)
            return func(*args, **kwargs)

        deprecationLoggedFunc.__name__ = func.__name__
        deprecationLoggedFunc.__module__ = func.__module__
        deprecationLoggedFunc.__doc__ = message % info
        deprecationLoggedFunc._func_before_deprecation = func
        if func.__doc__:
            deprecationLoggedFunc.__doc__ += '\n\n' + func.__doc__
        return deprecationLoggedFunc

    # check if the decorator got a 'message' parameter
    if funcOrMessage is None:
        message = baseMessage
        return deprecated2
    elif isinstance(funcOrMessage, basestring):
        if baseMessage is None:
            message = funcOrMessage
        else:
            message = baseMessage + '. ' + funcOrMessage
        return deprecated2
    else:
        message = baseMessage
        return deprecated2(funcOrMessage)


def maya_deprecated(
        funcOrMessage=None, className=None,
        baseMessage="The function '{objName}' has been deprecated by maya and"
                    " may become unavailable in future maya versions",
        warningType=MayaDeprecationWarning):
    return deprecated(funcOrMessage=funcOrMessage, className=className,
                      baseMessage=baseMessage, warningType=warningType)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

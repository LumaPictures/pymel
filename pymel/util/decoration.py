from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


def decorated(origFunc, newFunc, decoration=None):
    """
    Copies the original function's name/docs/signature to the new function, so that the docstrings
    contain relevant information again.
    Most importantly, it adds the original function signature to the docstring of the decorating function,
    as well as a comment that the function was decorated. Supports nested decorations.
    """

    if not hasattr(origFunc, '_decorated'):
        # a func that has yet to be treated - add the original argspec to the docstring
        import inspect
        try:
            newFunc.__doc__ = "Original Arguments: %s\n\n" % inspect.formatargspec(*inspect.getargspec(origFunc))
        except TypeError:
            newFunc.__doc__ = "\n"
        if origFunc.__doc__:
            newFunc.__doc__ += origFunc.__doc__
    else:
        newFunc.__doc__ = origFunc.__doc__
    if decoration:
        newFunc.__doc__ += "\n(Decorated by %s)" % decoration
    newFunc.__name__ = origFunc.__name__
    newFunc.__module__ = origFunc.__module__
    newFunc._decorated = True   # stamp the function as decorated


def decorator(func):
    """
    Decorator for decorators. Calls the 'decorated' function above for the decorated function, to preserve docstrings.
    """
    def decoratorFunc(origFunc):
        newFunc = func(origFunc)
        decorated(origFunc, newFunc, "%s.%s" % (func.__module__, func.__name__))
        return newFunc
    decorated(func, decoratorFunc, "%s.%s" % (__name__, "decorator"))
    return decoratorFunc


def format_signature(args=(), varargs=None, varkw=None, defaults=None):
    kwargs = []
    if defaults is None:
        ndefaults = 0
    else:
        ndefaults = len(defaults)
    offset = len(args) - ndefaults

    if offset < 0:
        raise TypeError("The number of defaults cannot exceed the number of arguments")
    for i, arg in enumerate(args):
        # cannot be unicode
        if i >= offset:
            default = defaults[i - offset]
            if not hasattr(default, '__repr__'):
                raise ValueError("default values must have a __repr__ method")
            defaultStr = repr(default)
            kwargs.append('%s=%s' % (arg, defaultStr))
        else:
            kwargs.append(str(arg))

    if varargs:
        kwargs.append('*' + varargs)
    elif varkw:
        kwargs.append('**' + varkw)
    return ', '.join(kwargs)


def interface_wrapper(doer, args=(), varargs=None, varkw=None, defaults=None):
    """
    A wrapper which allows factories to programatically create functions with
    precise input arguments, instead of using the argument catch-all:

        >>> def f( *args, **kwargs ): #doctest: +SKIP
        ...     pass

    The inputs args, varargs, varkw, and defaults match the outputs of inspect.getargspec

    :param doer: the function to be wrapped.
    :param args: a list of strings to be used as argument names, in proper order
    :param defaults: a list of default values for the arguments. must be less than or equal
        to args in length. if less than, the last element of defaults will be paired with the last element of args,
        the second-to-last with the second-to-last and so on ( see inspect.getargspec ). Arguments
        which pair with a default become keyword arguments.
    """

    # TODO: ensure doer has only an *args parameter

    name = doer.__name__
    storageName = doer.__name__ + '_interfaced'
    g = {storageName: doer}
    signature = format_signature(args, varargs, varkw, defaults)
    defStr = """def {name}( {signature} ):
        return {origFunc}({args})""".format(
        name=name, signature=signature, origFunc=storageName,
        args=','.join(args))

    exec((defStr), g)

    func = g[name]
    func.__doc__ = doer.__doc__
    func.__module__ = doer.__module__
    return func

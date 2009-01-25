

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
    decorated(func,decoratorFunc, "%s.%s" % (__name__, "decorator"))
    return decoratorFunc
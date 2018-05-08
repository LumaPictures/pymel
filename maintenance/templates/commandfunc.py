
@_factories._addCmdDocs
def {{ funcName }}(*args, **kwargs):
    {% if uiWidget %}
    import uitypes
    {% endif %}
    {% if timeRangeFlags %}
    for flag in {{ timeRangeFlags }}:
        try:
            rawVal = kwargs[flag]
        except KeyError:
            continue
        else:
            kwargs[flag] = _factories.convertTimeValues(rawVal)
    {% endif %}
    {% if callbackFlags %}
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in {{ callbackFlags }}:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    {% endif %}
    res = {{ sourceFuncName }}(*args, **kwargs)
    {% if returnFunc %}
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, {{ returnFunc }})
    {% endif %}
    {% if resultNeedsUnpacking and unpackFlags %}
    if isinstance(res, list) and len(res) == 1:
        if kwargs.get('query', kwargs.get('q', False)):
            # unpack for specific query flags
            unpackFlags = {{ unpackFlags }}
            if not unpackFlags.isdisjoint(kwargs):
                res = res[0]
        else:
            # unpack create/edit result
            res = res[0]
    {% elif unpackFlags %}
    if isinstance(res, list) and len(res) == 1:
        # unpack for specific query flags
        unpackFlags = {{ unpackFlags }}
        if kwargs.get('query', kwargs.get('q', False)) and not unpackFlags.isdisjoint(kwargs):
            res = res[0]
    {% elif resultNeedsUnpacking %}
    # unpack create/edit list result
    if isinstance(res, list) and len(res) == 1 and not kwargs.get('query', kwargs.get('q', False)):
        res = res[0]
    {% endif %}
    {% if simpleWraps %}
    wraps = _factories.simpleCommandWraps['{{ commandName }}']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    {% endif %}
    return res


class {{ classname }}({{ parents }}):
{% if methods %}
  {% for method in methods %}
    {% if method.type == 'query' %}
    @_factories.addMelDocs('{{ method.command }}', '{{ method.flag }}')
    def {{ method.name }}(self, *args, **kwargs):
      {% if method.returnFunc %}
        kwargs['query'] = True
        kwargs['{{ method.flag }}'] = True
        return {{ method.returnFunc }}(cmds.{{ method.command }}(self, **kwargs))
      {% else %}
        kwargs['query'] = True
        kwargs['{{ method.flag }}'] = True
        return cmds.{{ method.command }}(self, **kwargs)
      {% endif %}
    {% elif method.type == 'edit' %}
    @_factories.addMelDocs('{{ method.command }}', '{{ method.flag }}')
    def {{ method.name }}(self, val=True, **kwargs):
        {% if callbackFlags %}
        _factories.handleCallbacks(args, kwargs, {{ callbackFlags }})
        {% endif %}
        return _factories.asEdit(cmds.{{ method.command }}, self, kwargs, '{{ method.flag }}', val)
    {% elif method.type == 'api' %}
    {% if method.isStatic %}
    @classmethod
    {% endif %}
    def {{ method.name }}(self, *args, **kwargs):
    {% if method.undoable %}
        undoEnabled = cmds.undoInfo(q=1, state=1) and _factories.apiUndo.cb_enabled
    {% endif %}
    {% if method.argList %}
        argList = {{ method.argList }}
        if len(args) != len(inArgs):
            raise TypeError, "function takes exactly %s arguments (%s given)" % (len(inArgs), len(args))

        argHelper = _factories.ApiArgUtil('{{ method.apiClass }}', '{{ method.apiName }}', {{ method.overloadIndex }})
      {% if method.undoable %}
        if undoEnabled:
            undo = _factories.getUndoArgs(args, argList, self.{{ method.getter }}, {{ method.getterInArgs }})
      {% endif %}
        do, final_do, outTypes = _factories.getDoArgs(self, args, argList, argHelper)
      {% if method.undoable %}
        if undoEnabled:
            apiUndo.append(_factories.ApiUndoItem(self.{{ method.name }}, do, undo))
      {% endif %}
      {% if method.isStatic %}
        result = _api.{{ method.apiClass }}.{{ method.apiName }}(*final_do)
      {% elif method.proxy %}
        mfn = self.__apimfn__()
        if not isinstance(mfn, apiClass):
            mfn = apiClass(self.__apiobject__())
        result = _api.{{ method.apiClass }}.{{ method.apiName }}(mfn, *final_do)
      {% else %}
        result = _api.{{ method.apiClass }}.{{ method.apiName }}(self, *final_do)
      {% endif %}
        return _factories.processApiResult(self, result, {{ method.outArgs }}, outTypes, do, argHelper)
    {% else %}
        if len(args):
            raise TypeError, "%s() takes no arguments (%s given)" % ('{{ method.name }}', len(args))

        argHelper = factories.ApiArgUtil('{{ method.apiClass }}', '{{ method.apiName }}', {{ method.overloadIndex }})
      {% if method.undoable %}
        if undoEnabled:
            undo = _factories.getUndoArgs(args, [], self.{{ method.getter }}, {{ method.getterInArgs }})
      {% endif %}
      {% if method.undoable %}
        if undoEnabled:
            apiUndo.append(_factories.ApiUndoItem(self.{{ method.name }}, [], undo))
      {% endif %}
      {% if method.isStatic %}
        result = _api.{{ method.apiClass }}.{{ method.apiName }}()
      {% elif method.proxy %}
        mfn = self.__apimfn__()
        if not isinstance(mfn, apiClass):
            mfn = apiClass(self.__apiobject__())
        result = _api.{{ method.apiClass }}.{{ method.apiName }}(mfn)
      {% else %}
        result = _api.{{ method.apiClass }}.{{ method.apiName }}(self)
      {% endif %}
        return argHelper.castResult(self, result)
    {% endif %}
    {% endif %}

  {% endfor %}
{% else %}
    pass
{% endif %}

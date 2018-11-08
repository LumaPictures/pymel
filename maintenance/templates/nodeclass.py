{% if not existing %}
class {{ classname }}({{ parents }}):
{% endif %}
{% if prefixLines %}
  {% for line in prefixLines %}
    {{line}}
  {% endfor %}
{% endif %}
{% if attrs %}
  {% for attr in attrs %}
    {{ attr.name }} = {{ attr.value }}
  {% endfor %}
{% endif %}
{% if methods %}

 {% for method in methods %}
  {% if method.type == 'query' %}
    @_f.addMelDocs('{{ method.command }}', '{{ method.flag }}')
    def {{ method.name }}(self, **kwargs):
        res = _f.asQuery(self, {{ method.func }}, kwargs, '{{ method.flag }}')
      {% if method.returnFunc %}
        res = {{ method.returnFunc }}(res)
      {% endif %}
        return res
    {% elif method.type == 'edit' %}
    @_f.addMelDocs('{{ method.command }}', '{{ method.flag }}')
    def {{ method.name }}(self, val=True, **kwargs):
        {% if callbackFlags %}
        _f.handleCallbacks(args, kwargs, {{ callbackFlags }})
        {% endif %}
        return _f.asEdit(self, {{ method.func }}, kwargs, '{{ method.flag }}', val)
    {% elif method.type == 'getattribute' %}
    def __getattribute__(self, name):
        if name in {{ method.removeAttrs }} and name not in _f.EXCLUDE_METHODS:  # tmp fix
            raise AttributeError("'{{ classname }}' object has no attribute '" + name + "'")
        return super({{ classname }}, self).__getattribute__(name)
  {% elif method.type == 'api' %}
   {% if method.classmethod %}
    @classmethod
   {% endif %}
   {% if method.deprecated %}
    @_f.deprecated
   {% else %}
    @_f.addApiDocs(_api.{{ method.apiClass }}, '{{ method.apiName }}')
   {% endif %}
    def {{ method.name }}({{ method.signature }}):
   {% if method.argList %}
      {% if method.undoable %}
        do, final_do, outTypes = _f.processApiArgs([{{ method.inArgs }}], {{ method.argList }}, self.{{ method.getter }}, self.{{ method.name }}, {{ method.getterInArgs}})
      {% else %}
        do, final_do, outTypes = _f.getDoArgs([{{ method.inArgs }}], {{ method.argList }})
      {% endif %}
      {% if method.classmethod %}
        res = _api.{{ method.apiClass }}.{{ method.apiName }}(*final_do)
      {% elif method.proxy %}
        res = _f.getProxyResult(self, _api.{{ method.apiClass }}, '{{ method.apiName }}', final_do)
      {% else %}
        res = _api.{{ method.apiClass }}.{{ method.apiName }}(self, *final_do)
      {% endif %}
      {% if method.returnType %}
        res = _f.ApiArgUtil._castResult(self, res, {{ method.returnType }}, {{ method.unitType }})
      {% endif %}
      {% if method.outArgs %}
        return _f.processApiResult(res, outTypes, do)
      {% else %}
        return res
      {% endif %}
   {% else %}
      {% if method.classmethod %}
        res = _api.{{ method.apiClass }}.{{ method.apiName }}()
      {% elif method.proxy %}
        res = _f.getProxyResult(self, _api.{{ method.apiClass }}, '{{ method.apiName }}')
      {% else %}
        res = _api.{{ method.apiClass }}.{{ method.apiName }}(self)
      {% endif %}
      {% if method.returnType %}
        return _f.ApiArgUtil._castResult(self, res, {{ method.returnType }}, {{ method.unitType }})
      {% else %}
        return res
      {% endif %}
   {% endif %}
   {% for alias in method.aliases %}
    {{ alias }} = {{ method.name }}
   {% endfor %}
   {% for alias in method.properties %}
    {{ alias }} = property({{ method.name }})
   {% endfor %}
  {% endif %}

 {% endfor %}
{% else %}

{% endif %}

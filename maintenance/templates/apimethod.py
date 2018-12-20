{% if method.classmethod %}
@classmethod
{% endif %}
{% if method.deprecated %}
{{ method.deprecated }}
{% else %}
@_f.addApiDocs(_api.{{ method.apiClass }}, '{{ method.apiName }}')
{% endif %}
def {{ method.name }}({{ method.signature }}):
    {{ method.typeComment }}
{% if method.argList %}
  {% if method.undoable %}
    do, final_do, outTypes, undoItem = _f.processApiArgs([{{ method.inArgs }}], {{ method.argList }}, self.{{ method.getter }}, self.{{ method.name }}, {{ method.getterInArgs}})
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
  {% if method.undoable %}
    if undoItem is not None: _f.apiUndo.append(undoItem)
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
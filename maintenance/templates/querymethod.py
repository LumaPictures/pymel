@_f.addMelDocs('{{ method.command }}', '{{ method.flag }}')
def {{ method.name }}(self, **kwargs):
    res = _f.asQuery(self, {{ method.func }}, kwargs, '{{ method.flag }}')
  {% if method.returnFunc %}
    res = {{ method.returnFunc }}(res)
  {% endif %}
    return res
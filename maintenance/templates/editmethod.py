@_f.addMelDocs('{{ method.command }}', '{{ method.flag }}')
def {{ method.name }}(self, val=True, **kwargs):
  {% if callbackFlags %}
    _f.handleCallbacks(args, kwargs, {{ callbackFlags }})
  {% endif %}
    return _f.asEdit(self, {{ method.func }}, kwargs, '{{ method.flag }}', val)
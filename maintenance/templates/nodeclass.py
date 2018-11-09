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

 {% for methodLines in methods %}
  {% for line in methodLines %}
    {{line}}
  {% endfor %}

 {% endfor %}
{% else %}

{% endif %}

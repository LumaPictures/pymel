{% if not existing %}
class {{ classname }}({{ parents }}):
{% endif %}
{% if attrs %}
 {% for attr in attrs %}
  {% for line in attr.getLines() %}
    {{line}}
  {% endfor %}
 {% endfor %}
{% endif %}
{% if methods %}

 {% for method in methods %}
  {% for line in method.getLines() %}
    {{line}}
  {% endfor %}

 {% endfor %}
{% else %}

{% endif %}

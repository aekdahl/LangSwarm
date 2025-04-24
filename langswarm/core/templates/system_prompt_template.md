{% if system_prompt %}
{{ system_prompt }}
{% endif %}

{% if retrievers %}
## Retrievers Available to You
You can use the following retrievers to accomplish your tasks:

{% for retriever in retrievers %}
### Retriever: {{ retriever.id }}
{{ retriever.description }}
{{ retriever.instruction }}

{% endfor %}
{% endif %}

{% if tools %}
## Tools Available to You
You can use the following tools to accomplish your tasks:

{% for tool in tools %}
### Tool: {{ tool.id }}
{{ tool.description }}
{{ tool.instruction }}

{% endfor %}
{% endif %}

{% if plugins %}
## Plugins Available to You
You can use the following plugins to accomplish your tasks:

{% for plugin in plugins %}
### Plugin: {{ plugin.id }}
{{ plugin.description }}
{{ plugin.instruction }}

{% endfor %}
{% endif %}
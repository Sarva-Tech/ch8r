from jinja2 import Template

SMART_ESCALATION_TEMPLATE = """
Smart Human Escalation Alert

Your agent {{ app.name }} was unable to process the user's query.  
Please jump into the conversation:

[Open Chat](https://ch8r.com/applications/{{ app.uuid }}/messages/{{ chatroom_uuid }})

User Identifier: `{{ user_id }}`  
Query: _{{ user_query }}_  
Agent Response:  
{{ agent_response }}
"""

def render_template(template_str: str, context: dict) -> str:
    return Template(template_str).render(**context)


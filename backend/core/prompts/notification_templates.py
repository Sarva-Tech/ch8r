from jinja2 import Template

SMART_ESCALATION_TEMPLATE = """
**Smart Human Escalation Alert**

Your agent **{{ app.name }}** was unable to process the user's query.  
Please jump into the conversation:

[**Open Chatroom**](https://ch8r.com/applications/{{ app.id }}/chatrooms/{{ chat_id }})

**User Identifier:** `{{ user_id }}`  
**Query:** _{{ user_query }}_  
**Agent Response:**  
{{ agent_response }}
"""

KB_UPLOAD_TEMPLATE = """
📚 **{{ count }} Knowledge Base item(s)** have been added to **{{ app.name }}**.

You can view them in the dashboard or continue editing.
"""

def render_template(template_str: str, context: dict) -> str:
    return Template(template_str).render(**context)


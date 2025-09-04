from jinja2 import Template

VERIFICATION_EMAIL_TEMPLATE = """
Hello {{ username }},

Please click the button below to verify your email address:

Verify Email Address
Or copy and paste this link into your browser:

{{ verification_url }}

Note: This link will expire in 24 hours.

After verification, you'll be redirected to the login page where you can sign in.

Thank you!
The CH8R Team
"""

VERIFICATION_EMAIL_HTML_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Verify your email address for CH8R</h2>
    <p>Hello {{ username }},</p>
    <p>Please click the button below to verify your email address:</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ verification_url }}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Verify Email Address</a>
    </div>
    <p>Or copy and paste this link into your browser:</p>
    <p><a href="{{ verification_url }}">{{ verification_url }}</a></p>
    <p><strong>Note:</strong> This link will expire in 24 hours.</p>
    <p>After verification, you'll be redirected to the login page where you can sign in.</p>
    <p>Thank you!<br>The CH8R Team</p>
</div>
"""

def render_template(template_str: str, context: dict) -> str:
    return Template(template_str).render(**context)

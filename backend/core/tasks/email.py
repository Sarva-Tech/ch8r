from celery import shared_task
from django.conf import settings
from core.services.template_loader import TemplateLoader
from mailersend import MailerSendClient, EmailBuilder
import requests

@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id, user_email, username, token, purpose="VERIFY_EMAIL"):
    try:
        base_url = settings.FRONTEND_URL.rstrip('/')
        if purpose == "VERIFY_EMAIL":
            url = f"{base_url}/verify-email/{token}/"
            subject = "Verify your email address for CH8R"
            context = {"username": username, "verification_url": url}
            plain_message = TemplateLoader.render_template('verify_email.txt.j2', context)
            html_message = TemplateLoader.render_template('verify_email.html.j2', context)
        elif purpose == "RESET_PASSWORD":
            url = f"{base_url}/reset-password?token={token}"
            subject = "Reset your password for CH8R"
            context = {"username": username, "reset_url": url}
            plain_message = TemplateLoader.render_template('reset_password.txt.j2', context)
            html_message = TemplateLoader.render_template('reset_password.html.j2', context)
        else:
            raise ValueError("Invalid email purpose")

        ms = MailerSendClient(api_key=settings.MAILERSEND_API_KEY)
        email = (EmailBuilder()
                 .from_email(settings.DEFAULT_FROM_EMAIL, "CH8R Team")
                 .to_many([{"email": user_email, "name": username}])
                 .subject(subject)
                 .text(plain_message)
                 .html(html_message)
                 .build())

        response = ms.emails.send(email)

        if response.success:
            print(f"Email sent successfully to {user_email}, Email ID: {response.id}")
        else:
            raise self.retry(exc=Exception(f"MailerSend error: {response.data}"), countdown=60)

        if response.status_code == 429:
            retry_seconds = response.retry_after or 60
            raise self.retry(exc=Exception("Rate limited by MailerSend"), countdown=retry_seconds)

    except Exception as e:
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_discord_notification_task(self, message):
    webhook_url = settings.DISCORD_SIGNUP_WEBHOOK_URL
    if not webhook_url:
        return
    try:
        response = requests.post(webhook_url, json={"content": message})
        response.raise_for_status()
    except requests.RequestException as e:
        raise self.retry(exc=e, countdown=60)

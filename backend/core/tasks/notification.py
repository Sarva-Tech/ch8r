from celery import shared_task
from enum import Enum
import requests
from django.core.mail import send_mail
from django.conf import settings

class NotificationType(Enum):
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    WHATSAPP = "whatsapp"

@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, Exception),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_notification_task(self, channel_data, message):
    channel_type = channel_data.get("type")
    config = channel_data.get("config")

    try:
        notification_type = NotificationType(channel_type)
    except ValueError:
        print(f"Unsupported notification type: {channel_type}")
        return

    try:
        if notification_type == NotificationType.DISCORD:
            webhook_url = config.get("webhook_url") or config.get("webhookUrl")
            username = config.get('username', 'Ch8r Bot')
            if webhook_url:
                payload = {"content": message, "username": username}
                requests.post(webhook_url, json=payload)

        elif notification_type == NotificationType.SLACK:
            webhook_url = config.get("webhook_url") or config.get("webhookUrl")
            username = config.get("username", "Ch8r Bot")
            if webhook_url:
                payload = {"text": message, "username": username}
                requests.post(webhook_url, json=payload)

        elif notification_type == NotificationType.EMAIL:
            recipient = config.get("email")
            subject = config.get("subject", "Notification from Ch8r")
            if not recipient:
                print("No recipient email configured")
                return
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)

        elif notification_type == NotificationType.WHATSAPP:
            pass
    except Exception as e:
        print(f"Error sending {channel_type} notification: {e}")
        raise

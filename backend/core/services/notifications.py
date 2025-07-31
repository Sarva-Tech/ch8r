from core.prompts import render_template
from core.tasks.notification import send_notification_task

def find_channels(application):
    from core.models import AppNotificationProfile

    return [
        app_profile.notification_profile
        for app_profile in AppNotificationProfile.objects.select_related("notification_profile").filter(application=application)
    ]

def notify_users(application, template_str, context):
    message = render_template(template_str, context)
    channels = find_channels(application)

    if not channels:
        print(f"No notification channels found for application: {application}")
        return

    for channel in channels:
        channel_data = {
            "type": channel.type,
            "config": channel.config,
        }
        send_notification_task.delay(channel_data, message)

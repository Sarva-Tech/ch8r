from django.db import migrations


def migrate_participant_prefixes(apps, schema_editor):
    ChatroomParticipant = apps.get_model('core', 'ChatroomParticipant')

    # Process in batches of 1000
    for participant in ChatroomParticipant.objects.iterator(chunk_size=1000):
        uid = participant.user_identifier

        if uid.startswith('anon_'):
            participant.user_identifier = 'widget_' + uid[len('anon_'):]
            participant.save(update_fields=['user_identifier'])
        elif uid.startswith('reg_'):
            participant.user_identifier = 'dashboard_' + uid[len('reg_'):]
            participant.save(update_fields=['user_identifier'])
        elif uid.startswith('reg:'):
            participant.user_identifier = 'dashboard_' + uid[len('reg:'):]
            participant.save(update_fields=['user_identifier'])
        # Already migrated (widget_ or dashboard_) — skip


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_chatroom_mode'),
    ]

    operations = [
        migrations.RunPython(migrate_participant_prefixes, noop),
    ]

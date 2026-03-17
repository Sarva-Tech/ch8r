from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_remove_chatroomparticipant_unread_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_internal',
            field=models.BooleanField(default=False),
        ),
    ]

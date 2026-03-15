from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_chatroom_ai_provider_chatroom_model'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE core_chatroom DROP COLUMN IF EXISTS chat_type;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

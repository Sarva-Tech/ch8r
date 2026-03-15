from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_chatroomparticipant_has_unread'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SELECT 1",  # column already dropped directly; this is a no-op
            reverse_sql="SELECT 1",
        ),
    ]

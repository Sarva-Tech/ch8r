from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_message_is_internal'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='mode',
            field=models.CharField(
                choices=[('ai', 'AI Mode'), ('direct', 'Direct Mode')],
                default='ai',
                max_length=10,
            ),
        ),
    ]

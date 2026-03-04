# Generated manually for AI Provider Configurability Enhancement - Remove base_url field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_migrate_base_url_to_metadata_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aiprovider',
            name='base_url',
        ),
    ]

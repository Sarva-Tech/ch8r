# Generated manually for AI Provider Configurability Enhancement

from django.db import migrations, models


def migrate_base_url_to_metadata(apps, schema_editor):
    """
    Migrate existing base_url values to metadata field for backward compatibility.
    """
    AIProvider = apps.get_model('core', 'AIProvider')
    
    for provider in AIProvider.objects.all():
        if provider.base_url and not provider.metadata:
            provider.metadata = {'base_url': provider.base_url}
            provider.save()


def reverse_migrate_base_url_to_metadata(apps, schema_editor):
    """
    Reverse migration: extract base_url from metadata if present.
    """
    AIProvider = apps.get_model('core', 'AIProvider')
    
    for provider in AIProvider.objects.all():
        if provider.metadata and isinstance(provider.metadata, dict) and 'base_url' in provider.metadata:
            provider.base_url = provider.metadata['base_url']
            provider.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_migrate_base_url_to_metadata'),
    ]

    operations = [
        migrations.RunPython(
            migrate_base_url_to_metadata,
            reverse_migrate_base_url_to_metadata,
        ),
    ]

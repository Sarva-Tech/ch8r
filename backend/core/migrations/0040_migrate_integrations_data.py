from django.db import migrations


def migrate_integrations_forward(apps, schema_editor):
    Integration = apps.get_model('core', 'Integration')
    AppIntegration = apps.get_model('core', 'AppIntegration')

    # Migrate legacy Integration records (those without a creator)
    for integration in Integration.objects.filter(creator__isnull=True):
        integration.credentials = '{}'
        existing_metadata = integration.metadata or {}
        integration.metadata = {**existing_metadata, 'migrated_from_legacy': True}
        integration.save()

    # Migrate legacy AppIntegration records (those with empty integration_type)
    for app_integration in AppIntegration.objects.filter(integration_type=''):
        app_integration.integration_type = 'project_management'
        existing_metadata = app_integration.metadata or {}
        app_integration.metadata = {**existing_metadata, 'migrated_from_legacy': True}
        app_integration.save()


def migrate_integrations_reverse(apps, schema_editor):
    Integration = apps.get_model('core', 'Integration')
    AppIntegration = apps.get_model('core', 'AppIntegration')

    # Reverse migrated Integration records
    for integration in Integration.objects.all():
        metadata = integration.metadata or {}
        if metadata.get('migrated_from_legacy'):
            integration.creator = None
            metadata.pop('migrated_from_legacy')
            integration.metadata = metadata
            integration.save()

    # Reverse migrated AppIntegration records
    for app_integration in AppIntegration.objects.all():
        metadata = app_integration.metadata or {}
        if metadata.get('migrated_from_legacy'):
            app_integration.integration_type = ''
            metadata.pop('migrated_from_legacy')
            app_integration.metadata = metadata
            app_integration.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_redesign_integration_appintegration'),
    ]

    operations = [
        migrations.RunPython(migrate_integrations_forward, migrate_integrations_reverse),
    ]

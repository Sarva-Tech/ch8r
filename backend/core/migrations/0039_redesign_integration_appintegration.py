# Generated migration for integrations-marketplace redesign

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_merge_20260328_1803'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- Integration model changes ---

        # Remove old fields
        migrations.RemoveField(
            model_name='integration',
            name='type',
        ),
        migrations.RemoveField(
            model_name='integration',
            name='_config',
        ),
        migrations.RemoveField(
            model_name='integration',
            name='owner',
        ),

        # Remove old unique_together on (type, provider)
        migrations.AlterUniqueTogether(
            name='integration',
            unique_together=set(),
        ),

        # Add new fields
        migrations.AddField(
            model_name='integration',
            name='credentials',
            field=models.CharField(max_length=2000, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='integration',
            name='creator',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='integrations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # Make name nullable
        migrations.AlterField(
            model_name='integration',
            name='name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        # --- AppIntegration model changes ---

        # Add new fields
        migrations.AddField(
            model_name='appintegration',
            name='uuid',
            field=models.UUIDField(default=__import__('uuid').uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='appintegration',
            name='integration_type',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='appintegration',
            name='is_active',
            field=models.BooleanField(default=True),
        ),

        # Update unique_together from (application, integration) to (application, integration_type)
        migrations.AlterUniqueTogether(
            name='appintegration',
            unique_together={('application', 'integration_type')},
        ),
    ]

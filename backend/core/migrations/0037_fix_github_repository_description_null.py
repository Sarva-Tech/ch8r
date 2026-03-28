# Generated manually to fix database constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_githubrepository_githubpullrequest_githubissue_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='githubrepository',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]

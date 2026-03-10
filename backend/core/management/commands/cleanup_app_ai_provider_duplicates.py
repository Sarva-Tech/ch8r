from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models.app_ai_provider import AppAIProvider


class Command(BaseCommand):
    help = 'Clean up duplicate AppAIProvider records, keeping only the most recent for each app/context/capability combination'

    def handle(self, *args, **options):
        duplicates = AppAIProvider.objects.values('application', 'context', 'capability') \
            .annotate(count=Count('id')) \
            .filter(count__gt=1)

        total_deleted = 0

        for duplicate_group in duplicates:
            records = AppAIProvider.objects.filter(
                application=duplicate_group['application'],
                context=duplicate_group['context'],
                capability=duplicate_group['capability']
            ).order_by('-updated_at')

            records_to_delete = records[1:]
            count_deleted = records_to_delete.count()

            if count_deleted > 0:
                self.stdout.write(
                    f'Deleting {count_deleted} duplicate records for app={duplicate_group["application"]}, '
                    f'context={duplicate_group["context"]}, capability={duplicate_group["capability"]}'
                )
                records_to_delete.delete()
                total_deleted += count_deleted

        if total_deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {total_deleted} duplicate records')
            )
        else:
            self.stdout.write('No duplicate records found')

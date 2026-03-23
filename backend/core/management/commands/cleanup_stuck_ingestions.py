from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models.github_data import GitHubRepository
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up stuck GitHub repository ingestions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without making changes',
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Mark ingestions as failed if they have been running for more than this many minutes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        minutes = options['minutes']

        cutoff_time = timezone.now() - timezone.timedelta(minutes=minutes)

        stuck_repos = GitHubRepository.objects.filter(
            ingestion_status='running',
            updated_at__lt=cutoff_time
        )

        if not stuck_repos.exists():
            self.stdout.write(
                self.style.SUCCESS(f'No stuck ingestions found (cutoff: {minutes} minutes)')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Found {stuck_repos.count()} stuck ingestions:')
        )

        for repo in stuck_repos:
            age_minutes = (timezone.now() - repo.updated_at).total_seconds() / 60
            self.stdout.write(
                f'  - {repo.full_name} (ID: {repo.id}, '
                f'running for {age_minutes:.1f} minutes, '
                f'last updated: {repo.updated_at})'
            )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('Dry run completed. No changes made.')
            )
            return

        updated_count = stuck_repos.update(ingestion_status='failed')

        self.stdout.write(
            self.style.SUCCESS(
                f'Marked {updated_count} stuck ingestions as failed'
            )
        )

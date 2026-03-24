from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import sys
import time

from core.models import AppIntegration, Integration
from core.utils.github_migration_helper import GitHubMigrationHelper

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test GitHub API migration from REST to GraphQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--owner',
            type=str,
            required=True,
            help='Repository owner'
        )
        parser.add_argument(
            '--repo',
            type=str,
            required=True,
            help='Repository name'
        )
        parser.add_argument(
            '--integration-id',
            type=int,
            help='Integration ID (if not provided, will search for GitHub integration)'
        )
        parser.add_argument(
            '--generate-report',
            action='store_true',
            help='Generate detailed migration report'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of items to test (default: 50)'
        )

    def handle(self, *args, **options):
        owner = options['owner']
        repo = options['repo']
        limit = options['limit']
        generate_report = options['generate_report']
        integration_id = options.get('integration_id')

        try:
            app_integration = self._get_github_integration(integration_id)
            if not app_integration:
                self.stdout.write(
                    self.style.ERROR('GitHub integration not found')
                )
                return

            helper = GitHubMigrationHelper(app_integration)

            self.stdout.write(
                self.style.SUCCESS(f'Testing GitHub API migration for {owner}/{repo}')
            )

            self.stdout.write('\n=== Testing Issues Performance ===')
            issue_results = helper.compare_issue_ingestion_performance(owner, repo, limit)
            self._print_results('Issues', issue_results)

            self.stdout.write('\n=== Testing Pull Requests Performance ===')
            pr_results = helper.compare_pr_ingestion_performance(owner, repo, limit)
            self._print_results('Pull Requests', pr_results)

            if generate_report:
                self.stdout.write('\n=== Generating Migration Report ===')
                report = helper.generate_migration_report(owner, repo)

                report_filename = f'github_migration_report_{owner}_{repo}_{int(time.time())}.md'
                with open(report_filename, 'w') as f:
                    f.write(report)

                self.stdout.write(
                    self.style.SUCCESS(f'Report saved to: {report_filename}')
                )

                self.stdout.write('\n=== Summary ===')
                if issue_results.get('improvement'):
                    imp = issue_results['improvement']
                    self.stdout.write(
                        f'Issues: {imp["time_reduction_percent"]}% faster, {imp["speed_multiplier"]}x speedup'
                    )

                if pr_results.get('improvement'):
                    imp = pr_results['improvement']
                    self.stdout.write(
                        f'PRs: {imp["time_reduction_percent"]}% faster, {imp["speed_multiplier"]}x speedup'
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            logger.exception('Migration test failed')
        finally:
            if 'helper' in locals():
                helper.close()

    def _get_github_integration(self, integration_id=None):
        """Get GitHub integration"""
        try:
            if integration_id:
                return AppIntegration.objects.get(id=integration_id)

            integration = Integration.objects.filter(
                integration_type='github'
            ).first()

            if not integration:
                return None

            return AppIntegration.objects.filter(
                integration=integration
            ).first()

        except Exception as e:
            logger.error(f"Failed to get GitHub integration: {e}")
            return None

    def _print_results(self, entity_type, results):
        self.stdout.write(f'\n{entity_type} Results:')

        if 'error' in results.get('rest_api', {}):
            self.stdout.write(f"  REST API: ERROR - {results['rest_api']['error']}")
        else:
            rest = results['rest_api']
            self.stdout.write(
                f"  REST API: {rest['duration_seconds']}s, "
                f"{rest['api_calls']} calls, "
                f"{rest.get('issues_processed', rest.get('prs_processed', 0))} items"
            )

        if 'error' in results.get('graphql', {}):
            self.stdout.write(f"  GraphQL: ERROR - {results['graphql']['error']}")
        else:
            graphql = results['graphql']
            self.stdout.write(
                f"  GraphQL: {graphql['duration_seconds']}s, "
                f"{graphql['api_calls']} calls, "
                f"{graphql.get('issues_processed', graphql.get('prs_processed', 0))} items"
            )

        if results.get('improvement'):
            imp = results['improvement']
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Improvement: {imp['time_reduction_percent']}% faster, "
                    f"{imp['speed_multiplier']}x speedup, "
                    f"{imp['api_call_reduction']} fewer API calls"
                )
            )
        else:
            self.stdout.write("  No improvement data available")

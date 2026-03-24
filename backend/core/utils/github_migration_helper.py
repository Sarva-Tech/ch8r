import logging
import time
from typing import Dict, List, Optional, Any
from core.services.github_client import GitHubAPIClient
from core.services.github_graphql_client import GitHubGraphQLClient
from core.models import AppIntegration

logger = logging.getLogger(__name__)


class GitHubMigrationHelper:
    def __init__(self, app_integration: AppIntegration):
        self.app_integration = app_integration
        self.rest_client = None
        self.graphql_client = None

    def _get_rest_client(self) -> GitHubAPIClient:
        if not self.rest_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self.rest_client = GitHubAPIClient(token)
        return self.rest_client

    def _get_graphql_client(self) -> GitHubGraphQLClient:
        if not self.graphql_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self.graphql_client = GitHubGraphQLClient(token)
        return self.graphql_client

    def compare_issue_ingestion_performance(self, owner: str, repo: str, limit: int = 50) -> Dict[str, Any]:
        results = {
            'repository': f"{owner}/{repo}",
            'limit': limit,
            'rest_api': {},
            'graphql': {},
            'improvement': {}
        }

        logger.info(f"Starting performance comparison for {owner}/{repo}")

        try:
            logger.info("Testing REST API performance...")
            rest_start = time.time()

            rest_client = self._get_rest_client()
            issues = rest_client.get_issues(owner, repo, state='all')

            issues_to_test = issues[:limit]

            rest_api_calls = 1
            total_comments = 0

            for issue in issues_to_test:
                comments = rest_client.get_issue_comments(owner, repo, issue['number'])
                total_comments += len(comments)
                rest_api_calls += 1

            rest_end = time.time()
            rest_duration = rest_end - rest_start

            results['rest_api'] = {
                'duration_seconds': round(rest_duration, 2),
                'api_calls': rest_api_calls,
                'issues_processed': len(issues_to_test),
                'total_comments': total_comments,
                'avg_time_per_issue': round(rest_duration / len(issues_to_test), 3) if issues_to_test else 0
            }

            logger.info(f"REST API: {rest_api_calls} calls, {rest_duration:.2f}s for {len(issues_to_test)} issues")

        except Exception as e:
            logger.error(f"REST API test failed: {e}")
            results['rest_api']['error'] = str(e)

        try:
            logger.info("Testing GraphQL performance...")
            graphql_start = time.time()

            graphql_client = self._get_graphql_client()
            issues_with_comments = graphql_client.get_all_issues_with_comments(
                owner, repo, states=['OPEN', 'CLOSED']
            )

            issues_to_test = issues_with_comments[:limit]

            graphql_end = time.time()
            graphql_duration = graphql_end - graphql_start

            total_comments = sum(
                len(issue.get('comments', {}).get('edges', []))
                for issue in issues_to_test
            )

            results['graphql'] = {
                'duration_seconds': round(graphql_duration, 2),
                'api_calls': 1,
                'issues_processed': len(issues_to_test),
                'total_comments': total_comments,
                'avg_time_per_issue': round(graphql_duration / len(issues_to_test), 3) if issues_to_test else 0
            }

            logger.info(f"GraphQL: 1 call, {graphql_duration:.2f}s for {len(issues_to_test)} issues")

        except Exception as e:
            logger.error(f"GraphQL test failed: {e}")
            results['graphql']['error'] = str(e)

        if 'duration_seconds' in results['rest_api'] and 'duration_seconds' in results['graphql']:
            rest_time = results['rest_api']['duration_seconds']
            graphql_time = results['graphql']['duration_seconds']

            if rest_time > 0:
                time_improvement = ((rest_time - graphql_time) / rest_time) * 100
                results['improvement'] = {
                    'time_reduction_percent': round(time_improvement, 1),
                    'api_call_reduction': results['rest_api']['api_calls'] - results['graphql']['api_calls'],
                    'speed_multiplier': round(rest_time / graphql_time, 1) if graphql_time > 0 else float('inf')
                }

        return results

    def compare_pr_ingestion_performance(self, owner: str, repo: str, limit: int = 50) -> Dict[str, Any]:
        results = {
            'repository': f"{owner}/{repo}",
            'limit': limit,
            'rest_api': {},
            'graphql': {},
            'improvement': {}
        }

        logger.info(f"Starting PR performance comparison for {owner}/{repo}")

        try:
            logger.info("Testing REST API PR performance...")
            rest_start = time.time()

            rest_client = self._get_rest_client()
            prs = rest_client.get_pull_requests(owner, repo, state='all')

            prs_to_test = prs[:limit]

            rest_api_calls = 1
            total_comments = 0

            for pr in prs_to_test:
                comments = rest_client.get_pull_request_comments(owner, repo, pr['number'])
                total_comments += len(comments)
                rest_api_calls += 1

            rest_end = time.time()
            rest_duration = rest_end - rest_start

            results['rest_api'] = {
                'duration_seconds': round(rest_duration, 2),
                'api_calls': rest_api_calls,
                'prs_processed': len(prs_to_test),
                'total_comments': total_comments,
                'avg_time_per_pr': round(rest_duration / len(prs_to_test), 3) if prs_to_test else 0
            }

            logger.info(f"REST API PRs: {rest_api_calls} calls, {rest_duration:.2f}s for {len(prs_to_test)} PRs")

        except Exception as e:
            logger.error(f"REST API PR test failed: {e}")
            results['rest_api']['error'] = str(e)

        try:
            logger.info("Testing GraphQL PR performance...")
            graphql_start = time.time()

            graphql_client = self._get_graphql_client()
            prs_with_comments = graphql_client.get_all_pull_requests_with_comments(
                owner, repo, states=['OPEN', 'CLOSED', 'MERGED']
            )

            prs_to_test = prs_with_comments[:limit]

            graphql_end = time.time()
            graphql_duration = graphql_end - graphql_start

            total_comments = sum(
                len(pr.get('comments', {}).get('edges', []))
                for pr in prs_to_test
            )

            results['graphql'] = {
                'duration_seconds': round(graphql_duration, 2),
                'api_calls': 1,
                'prs_processed': len(prs_to_test),
                'total_comments': total_comments,
                'avg_time_per_pr': round(graphql_duration / len(prs_to_test), 3) if prs_to_test else 0
            }

            logger.info(f"GraphQL PRs: 1 call, {graphql_duration:.2f}s for {len(prs_to_test)} PRs")

        except Exception as e:
            logger.error(f"GraphQL PR test failed: {e}")
            results['graphql']['error'] = str(e)

        if 'duration_seconds' in results['rest_api'] and 'duration_seconds' in results['graphql']:
            rest_time = results['rest_api']['duration_seconds']
            graphql_time = results['graphql']['duration_seconds']

            if rest_time > 0:
                time_improvement = ((rest_time - graphql_time) / rest_time) * 100
                results['improvement'] = {
                    'time_reduction_percent': round(time_improvement, 1),
                    'api_call_reduction': results['rest_api']['api_calls'] - results['graphql']['api_calls'],
                    'speed_multiplier': round(rest_time / graphql_time, 1) if graphql_time > 0 else float('inf')
                }

        return results

    def generate_migration_report(self, owner: str, repo: str) -> str:
        report = []
        report.append("# GitHub API Migration Report")
        report.append(f"Repository: {owner}/{repo}")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        issue_results = self.compare_issue_ingestion_performance(owner, repo, limit=30)
        report.append("## Issues Performance Comparison")

        if 'error' not in issue_results['rest_api'] and 'error' not in issue_results['graphql']:
            report.append(f"### REST API")
            report.append(f"- Duration: {issue_results['rest_api']['duration_seconds']}s")
            report.append(f"- API Calls: {issue_results['rest_api']['api_calls']}")
            report.append(f"- Issues: {issue_results['rest_api']['issues_processed']}")
            report.append(f"- Comments: {issue_results['rest_api']['total_comments']}")
            report.append("")

            report.append(f"### GraphQL")
            report.append(f"- Duration: {issue_results['graphql']['duration_seconds']}s")
            report.append(f"- API Calls: {issue_results['graphql']['api_calls']}")
            report.append(f"- Issues: {issue_results['graphql']['issues_processed']}")
            report.append(f"- Comments: {issue_results['graphql']['total_comments']}")
            report.append("")

            if issue_results.get('improvement'):
                imp = issue_results['improvement']
                report.append(f"### Improvements")
                report.append(f"- Time Reduction: {imp['time_reduction_percent']}%")
                report.append(f"- API Call Reduction: {imp['api_call_reduction']}")
                report.append(f"- Speed Multiplier: {imp['speed_multiplier']}x faster")
                report.append("")
        else:
            report.append("Error in performance comparison. Check logs for details.")
            report.append("")

        pr_results = self.compare_pr_ingestion_performance(owner, repo, limit=30)
        report.append("## Pull Requests Performance Comparison")

        if 'error' not in pr_results['rest_api'] and 'error' not in pr_results['graphql']:
            report.append(f"### REST API")
            report.append(f"- Duration: {pr_results['rest_api']['duration_seconds']}s")
            report.append(f"- API Calls: {pr_results['rest_api']['api_calls']}")
            report.append(f"- PRs: {pr_results['rest_api']['prs_processed']}")
            report.append(f"- Comments: {pr_results['rest_api']['total_comments']}")
            report.append("")

            report.append(f"### GraphQL")
            report.append(f"- Duration: {pr_results['graphql']['duration_seconds']}s")
            report.append(f"- API Calls: {pr_results['graphql']['api_calls']}")
            report.append(f"- PRs: {pr_results['graphql']['prs_processed']}")
            report.append(f"- Comments: {pr_results['graphql']['total_comments']}")
            report.append("")

            if pr_results.get('improvement'):
                imp = pr_results['improvement']
                report.append(f"### Improvements")
                report.append(f"- Time Reduction: {imp['time_reduction_percent']}%")
                report.append(f"- API Call Reduction: {imp['api_call_reduction']}")
                report.append(f"- Speed Multiplier: {imp['speed_multiplier']}x faster")
                report.append("")
        else:
            report.append("Error in PR performance comparison. Check logs for details.")
            report.append("")

        report.append("## Migration Recommendations")
        report.append("### Benefits of GraphQL:")
        report.append("- ✅ Single API call for issues with comments")
        report.append("- ✅ Single API call for PRs with comments")
        report.append("- ✅ Reduced rate limiting risk")
        report.append("- ✅ Better performance for large repositories")
        report.append("- ✅ Flexible data selection")
        report.append("")

        report.append("### Migration Steps:")
        report.append("1. Install GraphQL client: `pip install gql==3.5.0`")
        report.append("2. Update ingestion service to use GraphQL:")
        report.append("   ```python")
        report.append("   from core.services.github_ingestion import GitHubDataIngestionService")
        report.append("   ")
        report.append("   # Enable GraphQL (default)")
        report.append("   service = GitHubDataIngestionService(app_integration, use_graphql=True)")
        report.append("   ")
        report.append("   # Or disable to fall back to REST")
        report.append("   service = GitHubDataIngestionService(app_integration, use_graphql=False)")
        report.append("   ```")
        report.append("")

        report.append("### Notes:")
        report.append("- GraphQL is used for issues, PRs, and comments")
        report.append("- REST API is still used for PR files (not available in GraphQL)")
        report.append("- Backward compatibility is maintained")
        report.append("- Rate limits are significantly reduced")
        report.append("- Performance improvement is especially noticeable for large repos")

        return "\n".join(report)

    def close(self):
        if self.rest_client:
            self.rest_client.close()
        if self.graphql_client:
            self.graphql_client.close()

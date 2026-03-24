#!/usr/bin/env python
"""
Debug GitHub GraphQL ingestion to identify incomplete ingestion issues
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/home/krrish/projects/ch8r/backend')

try:
    import django
    django.setup()
    
    print("🔍 GitHub Ingestion Diagnostic Tool")
    print("=" * 50)
    
    from core.models.github_data import GitHubRepository, GitHubIssue, GitHubPullRequest
    from core.models import AppIntegration
    
    def check_repository_stats(owner: str, repo: str):
        """Check ingestion statistics for a repository"""
        print(f"\n📊 Statistics for {owner}/{repo}:")
        
        try:
            # Find the repository
            repo_obj = GitHubRepository.objects.filter(
                full_name=f'{owner}/{repo}'
            ).first()
            
            if not repo_obj:
                print(f"❌ Repository not found in database")
                return
            
            print(f"Repository ID: {repo_obj.id}")
            print(f"Ingestion Status: {repo_obj.ingestion_status}")
            print(f"Last Ingested: {repo_obj.last_ingested_at}")
            
            # Count issues
            issue_count = GitHubIssue.objects.filter(repository=repo_obj).count()
            print(f"Issues in database: {issue_count}")
            
            # Count PRs
            pr_count = GitHubPullRequest.objects.filter(repository=repo_obj).count()
            print(f"Pull Requests in database: {pr_count}")
            
            # Count issue comments
            from django.db.models import Count
            issue_comment_count = GitHubIssueComment.objects.filter(
                issue__repository=repo_obj
            ).count()
            print(f"Issue Comments in database: {issue_comment_count}")
            
            # Count PR comments
            pr_comment_count = GitHubPRComment.objects.filter(
                pull_request__repository=repo_obj
            ).count()
            print(f"PR Comments in database: {pr_comment_count}")
            
            # Show recent activity
            recent_issues = GitHubIssue.objects.filter(
                repository=repo_obj
            ).order_by('-created_at')[:5]
            
            if recent_issues:
                print(f"\n📝 Recent Issues:")
                for issue in recent_issues:
                    print(f"  - #{issue.number}: {issue.title[:50]}...")
            
            recent_prs = GitHubPullRequest.objects.filter(
                repository=repo_obj
            ).order_by('-created_at')[:5]
            
            if recent_prs:
                print(f"\n📝 Recent Pull Requests:")
                for pr in recent_prs:
                    print(f"  - #{pr.number}: {pr.title[:50]}...")
            
            print(f"\n💡 Ingestion appears {'complete' if issue_count > 0 and pr_count > 0 else 'incomplete'}")
            
        except Exception as e:
            print(f"❌ Error checking stats: {e}")
    
    def list_available_repositories():
        """List all repositories in database"""
        print(f"\n📚 All Repositories in Database:")
        
        repos = GitHubRepository.objects.all().order_by('-last_ingested_at')[:10]
        
        if not repos:
            print("  No repositories found")
            return
            
        for repo in repos:
            status_emoji = "✅" if repo.ingestion_status == 'completed' else "🔄"
            print(f"  {status_emoji} {repo.full_name} ({repo.ingestion_status})")
            print(f"     Issues: {GitHubIssue.objects.filter(repository=repo).count()}")
            print(f"     PRs: {GitHubPullRequest.objects.filter(repository=repo).count()}")
    
    if len(sys.argv) >= 3:
        command = sys.argv[1]
        
        if command == "stats" and len(sys.argv) >= 4:
            owner, repo = sys.argv[2], sys.argv[3]
            check_repository_stats(owner, repo)
        
        elif command == "list":
            list_available_repositories()
        
        else:
            print("Usage:")
            print("  python debug_github_ingestion.py stats <owner> <repo>")
            print("  python debug_github_ingestion.py list")
    
    else:
        print("Available commands:")
        print("  stats <owner> <repo> - Check ingestion statistics")
        print("  list - List all repositories")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

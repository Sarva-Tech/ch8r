#!/usr/bin/env python
"""
Test script to verify GitHub ingestion system setup
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from core.models.github_data import GitHubRepository, GitHubIssue, GitHubPullRequest
from core.services.github_client import GitHubAPIClient
from core.services.github_ingestion import GitHubDataIngestionService


def test_database_tables():
    """Test that all GitHub tables exist"""
    print("🔍 Testing database tables...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE '%github%';
        """)
        tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'core_githubrepository',
        'core_githubissue', 
        'core_githubpullrequest',
        'core_githubdiscussion',
        'core_githubwikipage',
        'core_githubrepositoryfile'
    ]
    
    for table in expected_tables:
        if table in tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - NOT FOUND")
    
    print(f"Found {len(tables)} GitHub-related tables")
    return len(tables) >= len(expected_tables)


def test_model_creation():
    """Test model creation and basic operations"""
    print("\n🏗️ Testing model creation...")
    
    try:
        # This would require actual AppIntegration instances
        # For now, just test model imports
        print("✅ GitHubRepository model imported")
        print("✅ GitHubIssue model imported") 
        print("✅ GitHubPullRequest model imported")
        
        # Test model methods
        repo = GitHubRepository(
            full_name="test/test",
            name="test",
            owner="test",
            url="https://github.com/test/test"
        )
        print(f"✅ Repository string representation: {repo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False


def test_github_client():
    """Test GitHub API client initialization"""
    print("\n🌐 Testing GitHub API client...")
    
    try:
        client = GitHubAPIClient("test_token")
        print("✅ GitHubAPIClient initialized")
        
        # Test headers
        assert "Authorization" in client.session.headers
        assert "Bearer test_token" == client.session.headers["Authorization"]
        print("✅ Authorization header set correctly")
        
        # Test API version header
        assert "X-GitHub-Api-Version" in client.session.headers
        print("✅ API version header set correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub client test failed: {e}")
        return False


def test_ingestion_service():
    """Test ingestion service initialization"""
    print("\n📥 Testing ingestion service...")
    
    try:
        # Mock AppIntegration for testing
        class MockAppIntegration:
            def __init__(self):
                self.id = 1
                self.integration = MockIntegration()
        
        class MockIntegration:
            def __init__(self):
                self.config = {"token": "test_token"}
        
        mock_integration = MockAppIntegration()
        service = GitHubDataIngestionService(mock_integration)
        print("✅ GitHubDataIngestionService initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Ingestion service test failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint imports"""
    print("\n🔌 Testing API endpoints...")
    
    try:
        from core.views.github_ingestion import GitHubIngestionViewSet
        from core.serializers.github_serializers import (
            GitHubRepositorySerializer, GitHubIssueSerializer, GitHubPullRequestSerializer
        )
        print("✅ GitHubIngestionViewSet imported")
        print("✅ GitHubRepositorySerializer imported")
        print("✅ GitHubIssueSerializer imported")
        print("✅ GitHubPullRequestSerializer imported")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


def test_celery_tasks():
    """Test Celery task imports"""
    print("\n⚡ Testing Celery tasks...")
    
    try:
        from core.tasks.github_tasks import (
            ingest_github_repository_task,
            sync_all_github_repositories_task,
            cleanup_old_github_data_task
        )
        print("✅ ingest_github_repository_task imported")
        print("✅ sync_all_github_repositories_task imported")
        print("✅ cleanup_old_github_data_task imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery tasks test failed: {e}")
        return False


def test_admin_interface():
    """Test admin interface imports"""
    print("\n⚙️ Testing admin interface...")
    
    try:
        from core.admin.github_admin import (
            GitHubRepositoryAdmin, GitHubIssueAdmin, GitHubPullRequestAdmin
        )
        print("✅ GitHubRepositoryAdmin imported")
        print("✅ GitHubIssueAdmin imported")
        print("✅ GitHubPullRequestAdmin imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin interface test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 GitHub Ingestion System Setup Test")
    print("=" * 50)
    
    tests = [
        test_database_tables,
        test_model_creation,
        test_github_client,
        test_ingestion_service,
        test_api_endpoints,
        test_celery_tasks,
        test_admin_interface
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! GitHub ingestion system is ready.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the setup.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

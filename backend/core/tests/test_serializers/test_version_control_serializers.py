import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.serializers.version_control_serializers import (
    VCRepositorySerializer,
    VCIssueCommentSerializer,
    VCIssueSerializer,
    VCPRFileSerializer,
    VCPRCommentSerializer,
    VCPullRequestSerializer,
    VCRepositoryDetailSerializer,
    VCIngestionRequestSerializer,
)
from core.models.version_control import (
    VCRepository, VCIssue, VCIssueComment, VCPullRequest,
    VCPRComment, VCPRFile
)
from core.tests.factories import UserFactory, ApplicationFactory, IntegrationFactory, AppIntegrationFactory


@pytest.mark.unit
class TestVCRepositorySerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )

        serializer = VCRepositorySerializer(repo)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'provider', 'external_id', 'name', 'repo_owner', 'full_name',
                          'description', 'url', 'is_private', 'default_branch', 'last_ingested_at',
                          'ingestion_status', 'metadata', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data

    def test_read_only_fields(self):
        serializer = VCRepositorySerializer()
        assert serializer.fields['id'].read_only
        assert serializer.fields['uuid'].read_only
        assert serializer.fields['created_at'].read_only
        assert serializer.fields['updated_at'].read_only


@pytest.mark.unit
class TestVCIssueCommentSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        issue = VCIssue.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test Issue',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1'
        )
        comment = VCIssueComment.objects.create(
            issue=issue,
            external_id='1',
            body='Test comment',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1#comment-1'
        )

        serializer = VCIssueCommentSerializer(comment)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'external_id', 'body', 'author', 'author_association',
                          'url', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data


@pytest.mark.unit
class TestVCIssueSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        issue = VCIssue.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test Issue',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1'
        )

        serializer = VCIssueSerializer(issue)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'external_id', 'number', 'title', 'body', 'state',
                          'author', 'author_association', 'assignees', 'labels', 'milestone',
                          'locked', 'closed_at', 'url',
                          'comments', 'comment_count', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data

    def test_get_comment_count(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        issue = VCIssue.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test Issue',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1'
        )
        VCIssueComment.objects.create(
            issue=issue,
            external_id='1',
            body='Test comment',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1#comment-1'
        )

        serializer = VCIssueSerializer(issue)
        comment_count = serializer.get_comment_count(issue)

        assert comment_count == 1


@pytest.mark.unit
class TestVCPRFileSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        pr = VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )
        pr_file = VCPRFile.objects.create(
            pull_request=pr,
            filename='test.py',
            status='added'
        )

        serializer = VCPRFileSerializer(pr_file)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'filename', 'status', 'additions', 'deletions',
                          'changes', 'patch', 'blob_url', 'raw_url', 'contents_url',
                          'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data


@pytest.mark.unit
class TestVCPRCommentSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        pr = VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )
        pr_comment = VCPRComment.objects.create(
            pull_request=pr,
            external_id='1',
            body='Test comment',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1#comment-1'
        )

        serializer = VCPRCommentSerializer(pr_comment)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'external_id', 'body', 'author', 'author_association',
                          'url', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data


@pytest.mark.unit
class TestVCPullRequestSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        pr = VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )

        serializer = VCPullRequestSerializer(pr)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'external_id', 'number', 'title', 'body', 'state',
                          'author', 'author_association', 'assignees', 'reviewers', 'labels',
                          'milestone', 'head_branch', 'base_branch', 'merged', 'merged_at',
                          'merge_commit_sha', 'additions', 'deletions', 'changed_files',
                          'closed_at', 'url',
                          'comments', 'files', 'comment_count', 'file_count',
                          'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data

    def test_get_comment_count(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        pr = VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )
        VCPRComment.objects.create(
            pull_request=pr,
            external_id='1',
            body='Test comment',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1#comment-1'
        )

        serializer = VCPullRequestSerializer(pr)
        comment_count = serializer.get_comment_count(pr)

        assert comment_count == 1

    def test_get_file_count(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        pr = VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )
        VCPRFile.objects.create(
            pull_request=pr,
            filename='test.py',
            status='added'
        )

        serializer = VCPullRequestSerializer(pr)
        file_count = serializer.get_file_count(pr)

        assert file_count == 1


@pytest.mark.unit
class TestVCRepositoryDetailSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )

        serializer = VCRepositoryDetailSerializer(repo)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'provider', 'external_id', 'name', 'repo_owner', 'full_name',
                          'description', 'url', 'is_private', 'default_branch', 'last_ingested_at',
                          'ingestion_status', 'metadata', 'created_at', 'updated_at',
                          'issues', 'pull_requests', 'issue_count', 'pr_count']
        for field in expected_fields:
            assert field in data

    def test_get_issue_count(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        VCIssue.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test Issue',
            author='testuser',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/issues/1'
        )

        serializer = VCRepositoryDetailSerializer(repo)
        issue_count = serializer.get_issue_count(repo)

        assert issue_count == 1

    def test_get_pr_count(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration)
        repo = VCRepository.objects.create(
            app_integration=app_integration,
            name='test-repo',
            repo_owner='testuser',
            full_name='testuser/test-repo',
            url='https://github.com/testuser/test-repo'
        )
        VCPullRequest.objects.create(
            repository=repo,
            external_id='1',
            number=1,
            title='Test PR',
            author='testuser',
            head_branch='feature',
            base_branch='main',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            url='https://github.com/testuser/test-repo/pull/1'
        )

        serializer = VCRepositoryDetailSerializer(repo)
        pr_count = serializer.get_pr_count(repo)

        assert pr_count == 1


@pytest.mark.unit
class TestVCIngestionRequestSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = VCIngestionRequestSerializer()
        expected_fields = ['owner', 'repo', 'since', 'application_uuid', 'provider']
        for field in expected_fields:
            assert field in serializer.fields

    def test_owner_max_length(self):
        serializer = VCIngestionRequestSerializer()
        assert serializer.fields['owner'].max_length == 255

    def test_repo_max_length(self):
        serializer = VCIngestionRequestSerializer()
        assert serializer.fields['repo'].max_length == 255

    def test_since_is_optional(self):
        serializer = VCIngestionRequestSerializer()
        assert not serializer.fields['since'].required
        assert serializer.fields['since'].allow_null

    def test_application_uuid_is_required(self):
        serializer = VCIngestionRequestSerializer()
        assert serializer.fields['application_uuid'].required

    def test_provider_max_length(self):
        serializer = VCIngestionRequestSerializer()
        assert serializer.fields['provider'].max_length == 20

    def test_provider_default(self):
        serializer = VCIngestionRequestSerializer()
        assert serializer.fields['provider'].default == 'github_graphql'

    def test_validate_application_uuid_valid(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=application, integration=integration, integration_type='version_control')

        mock_request = Mock()
        mock_request.user = user

        serializer = VCIngestionRequestSerializer(context={'request': mock_request})
        result = serializer.validate_application_uuid(application.uuid)

        assert result == application.uuid

    def test_validate_application_uuid_invalid(self):
        user = UserFactory()
        other_user = UserFactory()
        application = ApplicationFactory(owner=other_user)

        mock_request = Mock()
        mock_request.user = user

        serializer = VCIngestionRequestSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_application_uuid(application.uuid)

        assert "Invalid application_uuid" in str(exc_info.value)

    def test_validate_application_uuid_no_integration(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = VCIngestionRequestSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_application_uuid(application.uuid)

        assert "No version_control integration" in str(exc_info.value)

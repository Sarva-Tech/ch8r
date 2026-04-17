from rest_framework import serializers
from core.models.version_control import (
    VCRepository, VCIssue, VCIssueComment, VCPullRequest,
    VCPRComment, VCPRFile
)


class VCRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VCRepository
        fields = [
            'id', 'uuid', 'provider', 'external_id', 'name', 'repo_owner', 'full_name',
            'description', 'url', 'is_private', 'default_branch', 'last_ingested_at',
            'ingestion_status', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class VCIssueCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VCIssueComment
        fields = [
            'id', 'uuid', 'external_id', 'body', 'author', 'author_association',
            'url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class VCIssueSerializer(serializers.ModelSerializer):
    comments = VCIssueCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = VCIssue
        fields = [
            'id', 'uuid', 'external_id', 'number', 'title', 'body', 'state',
            'author', 'author_association', 'assignees', 'labels', 'milestone',
            'locked', 'closed_at', 'url',
            'comments', 'comment_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()


class VCPRFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VCPRFile
        fields = [
            'id', 'uuid', 'filename', 'status', 'additions', 'deletions',
            'changes', 'patch', 'blob_url', 'raw_url', 'contents_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class VCPRCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = VCPRComment
        fields = [
            'id', 'uuid', 'external_id', 'body', 'author', 'author_association',
            'url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class VCPullRequestSerializer(serializers.ModelSerializer):
    comments = VCPRCommentSerializer(many=True, read_only=True)
    files = VCPRFileSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = VCPullRequest
        fields = [
            'id', 'uuid', 'external_id', 'number', 'title', 'body', 'state',
            'author', 'author_association', 'assignees', 'reviewers', 'labels',
            'milestone', 'head_branch', 'base_branch', 'merged', 'merged_at',
            'merge_commit_sha', 'additions', 'deletions', 'changed_files',
            'closed_at', 'url',
            'comments', 'files', 'comment_count', 'file_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_file_count(self, obj):
        return obj.files.count()


class VCRepositoryDetailSerializer(VCRepositorySerializer):
    issues = VCIssueSerializer(many=True, read_only=True)
    pull_requests = VCPullRequestSerializer(many=True, read_only=True)
    issue_count = serializers.SerializerMethodField()
    pr_count = serializers.SerializerMethodField()

    class Meta(VCRepositorySerializer.Meta):
        fields = VCRepositorySerializer.Meta.fields + [
            'issues', 'pull_requests',
            'issue_count', 'pr_count'
        ]

    def get_issue_count(self, obj):
        return obj.issues.count()

    def get_pr_count(self, obj):
        return obj.pull_requests.count()


class VCIngestionRequestSerializer(serializers.Serializer):
    owner = serializers.CharField(max_length=255)
    repo = serializers.CharField(max_length=255)
    since = serializers.DateTimeField(required=False, allow_null=True)
    application_uuid = serializers.UUIDField()
    provider = serializers.CharField(max_length=20, required=False, default='github_graphql')

    def validate_application_uuid(self, value):
        from core.models import Application, AppIntegration
        request = self.context.get('request')
        try:
            self._application = Application.objects.get(uuid=value, owner=request.user)
        except Application.DoesNotExist:
            raise serializers.ValidationError("Invalid application_uuid or access denied.")
        if not AppIntegration.objects.filter(
            application=self._application, integration_type='version_control'
        ).exists():
            raise serializers.ValidationError(
                "No version_control integration configured for this application"
            )
        return value

from rest_framework import serializers
from core.models.github_data import (
    GitHubRepository, GitHubIssue, GitHubIssueComment, GitHubPullRequest,
    GitHubPRComment, GitHubPRFile, GitHubDiscussion, GitHubDiscussionComment,
    GitHubWikiPage, GitHubRepositoryFile
)


class GitHubRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubRepository
        fields = [
            'id', 'uuid', 'name', 'repo_owner', 'full_name', 'description', 'url',
            'is_private', 'default_branch', 'last_ingested_at', 'ingestion_status',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class GitHubIssueCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIssueComment
        fields = [
            'id', 'uuid', 'github_id', 'body', 'author', 'author_association',
            'created_at', 'updated_at', 'url'
        ]
        read_only_fields = ['id', 'uuid']


class GitHubIssueSerializer(serializers.ModelSerializer):
    comments = GitHubIssueCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = GitHubIssue
        fields = [
            'id', 'uuid', 'github_id', 'number', 'title', 'body', 'state',
            'author', 'author_association', 'assignees', 'labels', 'milestone',
            'locked', 'created_at', 'updated_at', 'closed_at', 'url',
            'comments', 'comment_count'
        ]
        read_only_fields = ['id', 'uuid']

    def get_comment_count(self, obj):
        return obj.comments.count()


class GitHubPRFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubPRFile
        fields = [
            'id', 'uuid', 'filename', 'status', 'additions', 'deletions',
            'changes', 'patch', 'blob_url', 'raw_url', 'contents_url'
        ]
        read_only_fields = ['id', 'uuid']


class GitHubPRCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubPRComment
        fields = [
            'id', 'uuid', 'github_id', 'body', 'author', 'author_association',
            'created_at', 'updated_at', 'url'
        ]
        read_only_fields = ['id', 'uuid']


class GitHubPullRequestSerializer(serializers.ModelSerializer):
    comments = GitHubPRCommentSerializer(many=True, read_only=True)
    files = GitHubPRFileSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = GitHubPullRequest
        fields = [
            'id', 'uuid', 'github_id', 'number', 'title', 'body', 'state',
            'author', 'author_association', 'assignees', 'reviewers', 'labels',
            'milestone', 'head_branch', 'base_branch', 'merged', 'merged_at',
            'merge_commit_sha', 'additions', 'deletions', 'changed_files',
            'created_at', 'updated_at', 'closed_at', 'url',
            'comments', 'files', 'comment_count', 'file_count'
        ]
        read_only_fields = ['id', 'uuid']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_file_count(self, obj):
        return obj.files.count()


class GitHubDiscussionCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = GitHubDiscussionComment
        fields = [
            'id', 'uuid', 'github_id', 'body', 'author', 'author_association',
            'created_at', 'updated_at', 'last_edited_at', 'upvote_count',
            'viewer_has_upvoted', 'parent_comment', 'replies'
        ]
        read_only_fields = ['id', 'uuid']

    def get_replies(self, obj):
        return GitHubDiscussionCommentSerializer(obj.replies.all(), many=True).data


class GitHubDiscussionSerializer(serializers.ModelSerializer):
    comments = GitHubDiscussionCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = GitHubDiscussion
        fields = [
            'id', 'uuid', 'github_id', 'number', 'title', 'body', 'author',
            'author_association', 'category', 'answer_chosen_at', 'answer_chosen_by',
            'upvote_count', 'viewer_has_upvoted', 'created_at', 'updated_at',
            'last_edited_at', 'url', 'comments', 'comment_count'
        ]
        read_only_fields = ['id', 'uuid']

    def get_comment_count(self, obj):
        return obj.comments.count()


class GitHubWikiPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubWikiPage
        fields = [
            'id', 'uuid', 'title', 'content', 'sha', 'html_url',
            'download_url', 'last_modified'
        ]
        read_only_fields = ['id', 'uuid']


class GitHubRepositoryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubRepositoryFile
        fields = [
            'id', 'uuid', 'path', 'name', 'content', 'sha', 'size',
            'content_type', 'encoding', 'html_url', 'download_url', 'last_modified'
        ]
        read_only_fields = ['id', 'uuid']


class GitHubRepositoryDetailSerializer(GitHubRepositorySerializer):
    issues = GitHubIssueSerializer(many=True, read_only=True)
    pull_requests = GitHubPullRequestSerializer(many=True, read_only=True)
    discussions = GitHubDiscussionSerializer(many=True, read_only=True)
    wiki_pages = GitHubWikiPageSerializer(many=True, read_only=True)
    files = GitHubRepositoryFileSerializer(many=True, read_only=True)
    issue_count = serializers.SerializerMethodField()
    pr_count = serializers.SerializerMethodField()
    discussion_count = serializers.SerializerMethodField()
    wiki_page_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()

    class Meta(GitHubRepositorySerializer.Meta):
        fields = GitHubRepositorySerializer.Meta.fields + [
            'issues', 'pull_requests', 'discussions', 'wiki_pages', 'files',
            'issue_count', 'pr_count', 'discussion_count', 'wiki_page_count', 'file_count'
        ]

    def get_issue_count(self, obj):
        return obj.issues.count()

    def get_pr_count(self, obj):
        return obj.pull_requests.count()

    def get_discussion_count(self, obj):
        return obj.discussions.count()

    def get_wiki_page_count(self, obj):
        return obj.wiki_pages.count()

    def get_file_count(self, obj):
        return obj.files.count()


class GitHubIngestionRequestSerializer(serializers.Serializer):
    owner = serializers.CharField(max_length=255)
    repo = serializers.CharField(max_length=255)
    since = serializers.DateTimeField(required=False, allow_null=True)
    app_integration_id = serializers.IntegerField()

    def validate_app_integration_id(self, value):
        from core.models import AppIntegration
        request = self.context.get('request')
        qs = AppIntegration.objects.filter(id=value)
        if request:
            qs = qs.filter(application__owner=request.user)
        if not qs.exists():
            raise serializers.ValidationError("Invalid app_integration_id or access denied.")
        return value

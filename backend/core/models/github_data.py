from django.db import models
from django.contrib.auth.models import User
from core.models.base_model import BaseModel
import uuid


class GitHubRepository(BaseModel):
    """GitHub repository configuration for ingestion"""
    name = models.CharField(max_length=255)
    repo_owner = models.CharField(max_length=255)
    full_name = models.CharField(max_length=511, unique=True)
    description = models.TextField(blank=True)
    url = models.URLField()
    is_private = models.BooleanField(default=False)
    default_branch = models.CharField(max_length=100, default='main')
    last_ingested_at = models.DateTimeField(null=True, blank=True)
    ingestion_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    metadata = models.JSONField(default=dict, blank=True)
    app_integration = models.ForeignKey(
        'AppIntegration',
        on_delete=models.CASCADE,
        related_name='github_repositories'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['app_integration']),
            models.Index(fields=['ingestion_status']),
        ]

    def __str__(self):
        return self.full_name


class GitHubIssue(BaseModel):
    """GitHub issue data"""
    github_id = models.BigIntegerField()
    number = models.IntegerField()
    title = models.CharField(max_length=1024)
    body = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')])
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    assignees = models.JSONField(default=list, blank=True)
    labels = models.JSONField(default=list, blank=True)
    milestone = models.JSONField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    url = models.URLField()
    repository = models.ForeignKey(
        GitHubRepository,
        on_delete=models.CASCADE,
        related_name='issues'
    )

    class Meta:
        unique_together = ['repository', 'github_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'state']),
            models.Index(fields=['github_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.repository.full_name}#{self.number}: {self.title}"


class GitHubIssueComment(BaseModel):
    """Comments on GitHub issues"""
    github_id = models.BigIntegerField()
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    url = models.URLField()
    issue = models.ForeignKey(
        GitHubIssue,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        unique_together = ['issue', 'github_id']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['issue', 'created_at']),
            models.Index(fields=['github_id']),
        ]

    def __str__(self):
        return f"Comment on {self.issue.repository.full_name}#{self.issue.number}"


class GitHubPullRequest(BaseModel):
    """GitHub pull request data"""
    github_id = models.BigIntegerField()
    number = models.IntegerField()
    title = models.CharField(max_length=1024)
    body = models.TextField(blank=True)
    state = models.CharField(
        max_length=20,
        choices=[('open', 'Open'), ('closed', 'Closed'), ('merged', 'Merged')]
    )
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    assignees = models.JSONField(default=list, blank=True)
    reviewers = models.JSONField(default=list, blank=True)
    labels = models.JSONField(default=list, blank=True)
    milestone = models.JSONField(null=True, blank=True)
    head_branch = models.CharField(max_length=255)
    base_branch = models.CharField(max_length=255)
    merged = models.BooleanField(default=False)
    merged_at = models.DateTimeField(null=True, blank=True)
    merge_commit_sha = models.CharField(max_length=40, blank=True)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    changed_files = models.IntegerField(default=0)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    url = models.URLField()
    repository = models.ForeignKey(
        GitHubRepository,
        on_delete=models.CASCADE,
        related_name='pull_requests'
    )

    class Meta:
        unique_together = ['repository', 'github_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'state']),
            models.Index(fields=['github_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['merged']),
        ]

    def __str__(self):
        return f"PR {self.repository.full_name}#{self.number}: {self.title}"


class GitHubPRComment(BaseModel):
    """Comments on GitHub pull requests"""
    github_id = models.BigIntegerField()
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    url = models.URLField()
    pull_request = models.ForeignKey(
        GitHubPullRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        unique_together = ['pull_request', 'github_id']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['pull_request', 'created_at']),
            models.Index(fields=['github_id']),
        ]

    def __str__(self):
        return f"Comment on PR {self.pull_request.repository.full_name}#{self.pull_request.number}"


class GitHubPRFile(BaseModel):
    """Files changed in GitHub pull requests"""
    filename = models.CharField(max_length=1024)
    status = models.CharField(
        max_length=20,
        choices=[('added', 'Added'), ('modified', 'Modified'), ('removed', 'Removed'), ('renamed', 'Renamed')]
    )
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    changes = models.IntegerField(default=0)
    patch = models.TextField(blank=True)
    blob_url = models.URLField(blank=True)
    raw_url = models.URLField(blank=True)
    contents_url = models.URLField(blank=True)
    pull_request = models.ForeignKey(
        GitHubPullRequest,
        on_delete=models.CASCADE,
        related_name='files'
    )

    class Meta:
        unique_together = ['pull_request', 'filename']
        ordering = ['filename']
        indexes = [
            models.Index(fields=['pull_request', 'status']),
            models.Index(fields=['filename']),
        ]

    def __str__(self):
        return f"{self.filename} in PR {self.pull_request.repository.full_name}#{self.pull_request.number}"


class GitHubDiscussion(BaseModel):
    """GitHub discussion data"""
    github_id = models.BigIntegerField()
    number = models.IntegerField()
    title = models.CharField(max_length=1024)
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    category = models.JSONField(default=dict, blank=True)
    answer_chosen_at = models.DateTimeField(null=True, blank=True)
    answer_chosen_by = models.CharField(max_length=255, blank=True)
    upvote_count = models.IntegerField(default=0)
    viewer_has_upvoted = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_edited_at = models.DateTimeField(null=True, blank=True)
    url = models.URLField()
    repository = models.ForeignKey(
        GitHubRepository,
        on_delete=models.CASCADE,
        related_name='discussions'
    )

    class Meta:
        unique_together = ['repository', 'github_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'category']),
            models.Index(fields=['github_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Discussion {self.repository.full_name}#{self.number}: {self.title}"


class GitHubDiscussionComment(BaseModel):
    """Comments in GitHub discussions"""
    github_id = models.BigIntegerField()
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_edited_at = models.DateTimeField(null=True, blank=True)
    upvote_count = models.IntegerField(default=0)
    viewer_has_upvoted = models.BooleanField(default=False)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    discussion = models.ForeignKey(
        GitHubDiscussion,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        unique_together = ['discussion', 'github_id']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['discussion', 'created_at']),
            models.Index(fields=['parent_comment']),
            models.Index(fields=['github_id']),
        ]

    def __str__(self):
        return f"Comment in Discussion {self.discussion.repository.full_name}#{self.discussion.number}"


class GitHubWikiPage(BaseModel):
    """GitHub wiki pages"""
    title = models.CharField(max_length=1024)
    content = models.TextField(blank=True)
    sha = models.CharField(max_length=40)
    html_url = models.URLField()
    download_url = models.URLField(blank=True)
    last_modified = models.DateTimeField()
    repository = models.ForeignKey(
        GitHubRepository,
        on_delete=models.CASCADE,
        related_name='wiki_pages'
    )

    class Meta:
        unique_together = ['repository', 'title']
        ordering = ['title']
        indexes = [
            models.Index(fields=['repository', 'title']),
            models.Index(fields=['last_modified']),
        ]

    def __str__(self):
        return f"Wiki page '{self.title}' in {self.repository.full_name}"


class GitHubRepositoryFile(BaseModel):
    """Repository files (README, Contributing, etc.)"""
    path = models.CharField(max_length=1024)
    name = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    sha = models.CharField(max_length=40)
    size = models.IntegerField(default=0)
    content_type = models.CharField(max_length=100, blank=True)
    encoding = models.CharField(max_length=20, blank=True)
    html_url = models.URLField(blank=True)
    download_url = models.URLField(blank=True)
    last_modified = models.DateTimeField()
    repository = models.ForeignKey(
        GitHubRepository,
        on_delete=models.CASCADE,
        related_name='files'
    )

    class Meta:
        unique_together = ['repository', 'path']
        ordering = ['path']
        indexes = [
            models.Index(fields=['repository', 'path']),
            models.Index(fields=['name']),
            models.Index(fields=['last_modified']),
        ]

    def __str__(self):
        return f"File {self.path} in {self.repository.full_name}"

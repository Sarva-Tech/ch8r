from django.db import models
from django.contrib.auth.models import User
from core.models.base_model import BaseModel
import uuid


class VCRepository(BaseModel):
    PROVIDER_CHOICES = [
        ('github', 'GitHub'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='github')
    external_id = models.CharField(max_length=255, blank=True, help_text="Provider-specific repository ID")
    name = models.CharField(max_length=255)
    repo_owner = models.CharField(max_length=255)
    full_name = models.CharField(max_length=511)
    description = models.TextField(blank=True, null=True)
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
        related_name='vc_repositories'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['app_integration']),
            models.Index(fields=['ingestion_status']),
            models.Index(fields=['provider']),
        ]
        unique_together = ['app_integration', 'full_name', 'provider']

    def __str__(self):
        return f"[{self.provider}] {self.full_name}"


class VCIssue(BaseModel):
    external_id = models.CharField(max_length=255, help_text="Provider-specific issue ID")
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
        VCRepository,
        on_delete=models.CASCADE,
        related_name='issues'
    )

    class Meta:
        unique_together = ['repository', 'external_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'state']),
            models.Index(fields=['external_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.repository.full_name}#{self.number}: {self.title}"


class VCIssueComment(BaseModel):
    external_id = models.CharField(max_length=255, help_text="Provider-specific comment ID")
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    url = models.URLField()
    issue = models.ForeignKey(
        VCIssue,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        unique_together = ['issue', 'external_id']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['issue', 'created_at']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"Comment on {self.issue.repository.full_name}#{self.issue.number}"


class VCPullRequest(BaseModel):
    external_id = models.CharField(max_length=255, help_text="Provider-specific PR/MR ID")
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
        VCRepository,
        on_delete=models.CASCADE,
        related_name='pull_requests'
    )

    class Meta:
        unique_together = ['repository', 'external_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'state']),
            models.Index(fields=['external_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['merged']),
        ]

    def __str__(self):
        return f"PR {self.repository.full_name}#{self.number}: {self.title}"


class VCPRComment(BaseModel):
    """Comments on version control pull/merge requests"""
    external_id = models.CharField(max_length=255, help_text="Provider-specific comment ID")
    body = models.TextField()
    author = models.CharField(max_length=255)
    author_association = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    url = models.URLField()
    pull_request = models.ForeignKey(
        VCPullRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        unique_together = ['pull_request', 'external_id']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['pull_request', 'created_at']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"Comment on PR {self.pull_request.repository.full_name}#{self.pull_request.number}"


class VCPRFile(BaseModel):
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
        VCPullRequest,
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

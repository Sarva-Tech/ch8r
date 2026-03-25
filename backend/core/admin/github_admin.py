from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.models.github_data import (
    GitHubRepository, GitHubIssue, GitHubIssueComment, GitHubPullRequest,
    GitHubPRComment, GitHubPRFile, GitHubDiscussion, GitHubDiscussionComment,
    GitHubWikiPage, GitHubRepositoryFile
)


@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    """Admin interface for GitHub repositories"""
    list_display = [
        'full_name', 'app_integration', 'ingestion_status', 
        'last_ingested_at', 'is_private', 'created_at'
    ]
    list_filter = [
        'ingestion_status', 'is_private', 'created_at', 'app_integration'
    ]
    search_fields = ['full_name', 'name', 'repo_owner', 'description']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Repository Information', {
            'fields': ('full_name', 'name', 'repo_owner', 'description', 'url')
        }),
        ('Configuration', {
            'fields': ('is_private', 'default_branch', 'app_integration')
        }),
        ('Ingestion Status', {
            'fields': ('ingestion_status', 'last_ingested_at')
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('app_integration__application')


class GitHubIssueCommentInline(admin.TabularInline):
    """Inline admin for issue comments"""
    model = GitHubIssueComment
    extra = 0
    readonly_fields = ['github_id', 'author', 'created_at']
    fields = ['github_id', 'author', 'body_preview', 'created_at']
    
    def body_preview(self, obj):
        if obj.body:
            return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
        return ''
    body_preview.short_description = 'Body Preview'


@admin.register(GitHubIssue)
class GitHubIssueAdmin(admin.ModelAdmin):
    """Admin interface for GitHub issues"""
    list_display = [
        'issue_number', 'title', 'repository', 'state', 'author', 
        'created_at', 'comment_count'
    ]
    list_filter = ['state', 'created_at', 'repository']
    search_fields = ['title', 'body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [GitHubIssueCommentInline]
    
    fieldsets = (
        ('Issue Information', {
            'fields': ('github_id', 'number', 'title', 'state', 'repository')
        }),
        ('Content', {
            'fields': ('body', 'author', 'author_association')
        }),
        ('Metadata', {
            'fields': (
                'assignees', 'labels', 'milestone', 'locked',
                'created_at', 'updated_at', 'closed_at'
            ),
            'classes': ('collapse',)
        }),
        ('External Links', {
            'fields': ('url',)
        })
    )
    
    def issue_number(self, obj):
        return f"#{obj.number}"
    issue_number.short_description = 'Issue #'
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('repository')


class GitHubPRCommentInline(admin.TabularInline):
    """Inline admin for PR comments"""
    model = GitHubPRComment
    extra = 0
    readonly_fields = ['github_id', 'author', 'created_at']
    fields = ['github_id', 'author', 'body_preview', 'created_at']
    
    def body_preview(self, obj):
        if obj.body:
            return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
        return ''
    body_preview.short_description = 'Body Preview'


class GitHubPRFileInline(admin.TabularInline):
    """Inline admin for PR files"""
    model = GitHubPRFile
    extra = 0
    readonly_fields = ['filename', 'status', 'additions', 'deletions']
    fields = ['filename', 'status', 'additions', 'deletions', 'changes']
    ordering = ['filename']


@admin.register(GitHubPullRequest)
class GitHubPullRequestAdmin(admin.ModelAdmin):
    """Admin interface for GitHub pull requests"""
    list_display = [
        'pr_number', 'title', 'repository', 'state', 'author',
        'merged', 'created_at', 'comment_count', 'file_count'
    ]
    list_filter = ['state', 'merged', 'created_at', 'repository']
    search_fields = ['title', 'body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [GitHubPRCommentInline, GitHubPRFileInline]
    
    fieldsets = (
        ('PR Information', {
            'fields': ('github_id', 'number', 'title', 'state', 'repository')
        }),
        ('Content', {
            'fields': ('body', 'author', 'author_association')
        }),
        ('Branch Information', {
            'fields': ('head_branch', 'base_branch', 'merged', 'merged_at')
        }),
        ('Statistics', {
            'fields': ('additions', 'deletions', 'changed_files')
        }),
        ('Metadata', {
            'fields': (
                'assignees', 'reviewers', 'labels', 'milestone',
                'created_at', 'updated_at', 'closed_at'
            ),
            'classes': ('collapse',)
        }),
        ('External Links', {
            'fields': ('url',)
        })
    )
    
    def pr_number(self, obj):
        return f"#{obj.number}"
    pr_number.short_description = 'PR #'
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = 'Files'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('repository')


@admin.register(GitHubDiscussion)
class GitHubDiscussionAdmin(admin.ModelAdmin):
    """Admin interface for GitHub discussions"""
    list_display = [
        'discussion_number', 'title', 'repository', 'category_name',
        'author', 'upvote_count', 'created_at', 'comment_count'
    ]
    list_filter = ['created_at', 'repository']
    search_fields = ['title', 'body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Discussion Information', {
            'fields': ('github_id', 'number', 'title', 'repository')
        }),
        ('Content', {
            'fields': ('body', 'author', 'author_association')
        }),
        ('Category', {
            'fields': ('category',)
        }),
        ('Interaction', {
            'fields': ('upvote_count', 'answer_chosen_at', 'answer_chosen_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_edited_at'),
            'classes': ('collapse',)
        }),
        ('External Links', {
            'fields': ('url',)
        })
    )
    
    def discussion_number(self, obj):
        return f"#{obj.number}"
    discussion_number.short_description = 'Discussion #'
    
    def category_name(self, obj):
        if obj.category and isinstance(obj.category, dict):
            return obj.category.get('name', 'N/A')
        return 'N/A'
    category_name.short_description = 'Category'
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('repository')


@admin.register(GitHubWikiPage)
class GitHubWikiPageAdmin(admin.ModelAdmin):
    """Admin interface for GitHub wiki pages"""
    list_display = ['title', 'repository', 'last_modified', 'created_at']
    list_filter = ['last_modified', 'created_at', 'repository']
    search_fields = ['title', 'content']
    readonly_fields = ['uuid', 'sha', 'created_at', 'updated_at']
    ordering = ['title']
    
    fieldsets = (
        ('Wiki Page Information', {
            'fields': ('title', 'repository')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Metadata', {
            'fields': ('sha', 'html_url', 'download_url', 'last_modified'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('repository')


@admin.register(GitHubRepositoryFile)
class GitHubRepositoryFileAdmin(admin.ModelAdmin):
    """Admin interface for GitHub repository files"""
    list_display = ['name', 'path', 'repository', 'size', 'content_type', 'last_modified']
    list_filter = ['content_type', 'last_modified', 'created_at', 'repository']
    search_fields = ['name', 'path', 'content']
    readonly_fields = ['uuid', 'sha', 'size', 'created_at', 'updated_at']
    ordering = ['path']
    
    fieldsets = (
        ('File Information', {
            'fields': ('name', 'path', 'repository')
        }),
        ('Content', {
            'fields': ('content', 'content_type', 'encoding')
        }),
        ('Metadata', {
            'fields': ('sha', 'size', 'html_url', 'download_url', 'last_modified'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('repository')
@admin.register(GitHubIssueComment)
class GitHubIssueCommentAdmin(admin.ModelAdmin):
    """Admin interface for GitHub issue comments"""
    list_display = ['github_id', 'issue', 'author', 'created_at']
    list_filter = ['created_at', 'author_association']
    search_fields = ['body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('issue__repository')


@admin.register(GitHubPRComment)
class GitHubPRCommentAdmin(admin.ModelAdmin):
    """Admin interface for GitHub PR comments"""
    list_display = ['github_id', 'pull_request', 'author', 'created_at']
    list_filter = ['created_at', 'author_association']
    search_fields = ['body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pull_request__repository')


@admin.register(GitHubPRFile)
class GitHubPRFileAdmin(admin.ModelAdmin):
    """Admin interface for GitHub PR files"""
    list_display = ['filename', 'pull_request', 'status', 'additions', 'deletions']
    list_filter = ['status', 'pull_request__repository']
    search_fields = ['filename', 'patch']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    ordering = ['filename']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pull_request__repository')


@admin.register(GitHubDiscussionComment)
class GitHubDiscussionCommentAdmin(admin.ModelAdmin):
    """Admin interface for GitHub discussion comments"""
    list_display = ['github_id', 'discussion', 'author', 'created_at', 'upvote_count']
    list_filter = ['created_at', 'author_association']
    search_fields = ['body', 'author']
    readonly_fields = ['uuid', 'github_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('discussion__repository')

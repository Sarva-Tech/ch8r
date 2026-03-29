import logging

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AppIntegration
from core.models.github_data import GitHubRepository
from core.serializers.github_serializers import (
    GitHubIngestionRequestSerializer,
    GitHubIssueSerializer,
    GitHubPullRequestSerializer,
    GitHubRepositoryDetailSerializer,
    GitHubRepositorySerializer,
)
from core.tasks.github_tasks import ingest_github_repository_task

logger = logging.getLogger(__name__)


def _get_repository_for_user(pk, user):
    """Fetch a GitHubRepository and verify ownership in one place."""
    repo = get_object_or_404(
        GitHubRepository.objects.select_related('app_integration__application__owner'),
        pk=pk,
    )
    if repo.app_integration.application.owner != user:
        return None, Response(
            {'error': 'You do not have access to this repository'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return repo, None


class GitHubIngestionViewSet(viewsets.ViewSet):
    """API endpoints for GitHub data ingestion and retrieval."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Queue async ingestion of a GitHub repository.",
        request_body=GitHubIngestionRequestSerializer,
        responses={
            202: openapi.Response(description="Ingestion queued"),
            400: openapi.Response(description="Invalid parameters"),
            403: openapi.Response(description="Access denied"),
        },
    )
    @action(detail=False, methods=['post'], url_path='ingest-repository')
    def ingest_repository(self, request):
        serializer = GitHubIngestionRequestSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        owner = data['owner']
        repo = data['repo']
        since = data.get('since')
        application_uuid = data['application_uuid']
        full_name = f'{owner}/{repo}'

        from core.models import Application
        application = Application.objects.get(uuid=application_uuid)
        app_integration = AppIntegration.objects.select_related('integration', 'application').get(
            application=application, integration_type='version_control'
        )

        existing_repo = GitHubRepository.objects.filter(
            full_name=full_name,
            app_integration=app_integration,
            ingestion_status='running',
        ).first()

        if existing_repo:
            import datetime
            from django.utils import timezone

            if existing_repo.updated_at and (timezone.now() - existing_repo.updated_at).total_seconds() > 1800:
                logger.warning(f"Found stuck repository ingestion for {full_name}, marking as failed")
                existing_repo.ingestion_status = 'failed'
                existing_repo.save()
            else:
                return Response(
                    {
                        'error': 'Ingestion already in progress for this repository.',
                        'repository_id': existing_repo.id,
                        'status': existing_repo.ingestion_status,
                        'last_updated': existing_repo.updated_at.isoformat() if existing_repo.updated_at else None
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        from core.models import KnowledgeBase
        from core.tasks.kb import send_kb_update
        kb, _ = KnowledgeBase.objects.get_or_create(
            application=app_integration.application,
            source_type='github',
            path=full_name,
            defaults={
                'status': 'pending',
                'metadata': {'source': 'github', 'repository': full_name, 'content': ''},
            }
        )
        send_kb_update(kb, kb.status)

        since_str = since.isoformat() if since else None
        ingest_github_repository_task.delay(app_integration.id, owner, repo, since_str)

        return Response(
            {
                'status': 'queued',
                'repository': full_name,
                'message': 'Repository ingestion started.',
                'kb_uuid': str(kb.uuid),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @swagger_auto_schema(
        operation_description="List all ingested repositories for an app integration.",
        manual_parameters=[
            openapi.Parameter(
                'application_uuid', openapi.IN_QUERY,
                type=openapi.TYPE_STRING, required=True,
            )
        ],
        responses={200: GitHubRepositorySerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='repositories')
    def list_repositories(self, request):
        application_uuid = request.query_params.get('application_uuid')
        if not application_uuid:
            return Response(
                {'error': 'application_uuid is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from core.models import Application
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        app_integration = get_object_or_404(
            AppIntegration, application=application, integration_type='version_control'
        )

        repositories = GitHubRepository.objects.filter(
            app_integration=app_integration
        ).order_by('-created_at')
        return Response(GitHubRepositorySerializer(repositories, many=True).data)

    @swagger_auto_schema(
        operation_description="Get full details of a single ingested repository.",
        responses={200: GitHubRepositoryDetailSerializer()},
    )
    @action(detail=True, methods=['get'], url_path='detail')
    def retrieve_repository(self, request, pk=None):
        repository, err = _get_repository_for_user(pk, request.user)
        if err:
            return err
        return Response(GitHubRepositoryDetailSerializer(repository).data)

    @swagger_auto_schema(
        operation_description="List issues for a repository.",
        manual_parameters=[
            openapi.Parameter(
                'state', openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['open', 'closed', 'all'], default='all',
            )
        ],
        responses={200: GitHubIssueSerializer(many=True)},
    )
    @action(detail=True, methods=['get'], url_path='issues')
    def list_issues(self, request, pk=None):
        repository, err = _get_repository_for_user(pk, request.user)
        if err:
            return err

        state_filter = request.query_params.get('state', 'all')
        issues = repository.issues.prefetch_related('comments').all()
        if state_filter in ('open', 'closed'):
            issues = issues.filter(state=state_filter)

        return Response(GitHubIssueSerializer(issues, many=True).data)

    @swagger_auto_schema(
        operation_description="List pull requests for a repository.",
        manual_parameters=[
            openapi.Parameter(
                'state', openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['open', 'closed', 'merged', 'all'], default='all',
            )
        ],
        responses={200: GitHubPullRequestSerializer(many=True)},
    )
    @action(detail=True, methods=['get'], url_path='pull-requests')
    def list_pull_requests(self, request, pk=None):
        repository, err = _get_repository_for_user(pk, request.user)
        if err:
            return err

        state_filter = request.query_params.get('state', 'all')
        prs = repository.pull_requests.prefetch_related('comments', 'files').all()
        if state_filter in ('open', 'closed', 'merged'):
            prs = prs.filter(state=state_filter)

        return Response(GitHubPullRequestSerializer(prs, many=True).data)




    @swagger_auto_schema(
        operation_description="Queue re-ingestion of an already-ingested repository.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'since': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='ISO datetime — only ingest data after this point (optional)',
                )
            },
        ),
        responses={
            202: openapi.Response(description="Re-ingestion queued"),
            403: openapi.Response(description="Access denied"),
            409: openapi.Response(description="Ingestion already running"),
        },
    )
    @action(detail=True, methods=['post'], url_path='re-ingest')
    def re_ingest_repository(self, request, pk=None):
        repository, err = _get_repository_for_user(pk, request.user)
        if err:
            return err

        if repository.ingestion_status == 'running':
            import datetime
            from django.utils import timezone

            if repository.updated_at and (timezone.now() - repository.updated_at).total_seconds() > 1800:
                logger.warning(f"Found stuck repository ingestion for {repository.full_name}, marking as failed")
                repository.ingestion_status = 'failed'
                repository.save()
            else:
                return Response(
                    {
                        'error': 'Ingestion already in progress for this repository.',
                        'repository_id': repository.id,
                        'status': repository.ingestion_status,
                        'last_updated': repository.updated_at.isoformat() if repository.updated_at else None
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        since = request.data.get('since') or request.query_params.get('since')
        owner, repo = repository.full_name.split('/', 1)
        ingest_github_repository_task.delay(
            repository.app_integration_id, owner, repo, since
        )

        return Response(
            {
                'status': 'queued',
                'repository': repository.full_name,
                'message': 'Repository re-ingestion started.',
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @swagger_auto_schema(
        operation_description="Delete a repository and all its ingested data, including vectors.",
        responses={
            204: openapi.Response(description="Deleted"),
            403: openapi.Response(description="Access denied"),
        },
    )
    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_repository(self, request, pk=None):
        repository, err = _get_repository_for_user(pk, request.user)
        if err:
            return err

        full_name = repository.full_name
        app = repository.app_integration.application

        try:
            from core.models import KnowledgeBase, IngestedChunk
            from core.services.ingestion import delete_vectors_from_qdrant

            kb = KnowledgeBase.objects.filter(
                application=app,
                source_type='github',
                path=full_name,
            ).first()

            if kb:
                chunks = IngestedChunk.objects.filter(knowledge_base=kb)
                qdrant_ids = [str(c.uuid) for c in chunks]
                chunks.delete()
                delete_vectors_from_qdrant(qdrant_ids)
                kb.delete()
                logger.info(f"Deleted KnowledgeBase and {len(qdrant_ids)} vectors for {full_name}")
        except Exception as e:
            logger.warning(f"Failed to clean up KB/vectors for {full_name}: {e}")

        repository.delete()
        logger.info(f"Deleted GitHub repository record: {full_name}")

        return Response(status=status.HTTP_204_NO_CONTENT)

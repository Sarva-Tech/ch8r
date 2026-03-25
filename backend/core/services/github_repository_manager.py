import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

from core.models.github_data import GitHubRepository
from core.models import AppIntegration
from core.services.github_client import GitHubAPIClient
from core.services.github_data_processors import RepositoryDataProcessor

logger = logging.getLogger(__name__)


class GitHubRepositoryManager:
    def __init__(self, app_integration: AppIntegration):
        self.app_integration = app_integration
        self._github_client = None
    
    def get_github_client(self) -> GitHubAPIClient:
        if not self._github_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self._github_client = GitHubAPIClient(token)
        return self._github_client
    
    def get_or_create_repository(self, owner: str, repo: str) -> GitHubRepository:
        full_name = f"{owner}/{repo}"
        
        repository, created = GitHubRepository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'repo_owner': owner,
                'app_integration': self.app_integration,
                'ingestion_status': 'pending'
            }
        )
        
        if created:
            self._enrich_repository_data(repository, owner, repo)
        
        return repository
    
    def _enrich_repository_data(self, repository: GitHubRepository, owner: str, repo: str):
        try:
            client = self.get_github_client()
            repo_info = client.get_repository_info(owner, repo)
            
            processor = RepositoryDataProcessor()
            processed_data = processor.process_data(repo_info)
            
            for field, value in processed_data.items():
                setattr(repository, field, value)
            
            repository.save()
            logger.info(f"Enriched repository record for {repository.full_name}")
            
        except Exception as e:
            logger.error(f"Failed to enrich repository {repository.full_name}: {e}")
            repository.delete()
            raise
    
    def update_ingestion_status(self, repository: GitHubRepository, status: str):
        repository.ingestion_status = status
        repository.last_ingested_at = timezone.now()
        repository.save()
        logger.info(f"Updated ingestion status for {repository.full_name}: {status}")

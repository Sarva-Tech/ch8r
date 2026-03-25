import logging
from typing import Optional
from django.utils import timezone

from core.models import AppIntegration
from core.services.github_graphql_ingestion import GitHubGraphQLIngestionService
from core.services.github_repository_manager import GitHubRepositoryManager
from core.services.github_issue_ingestion_service import GitHubIssueIngestionService
from core.services.github_pr_ingestion_service import GitHubPRIngestionService
from core.services.ingestion import chunk_text, embed_text, embed_sparse
from core.models import IngestedChunk
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import PointStruct
from qdrant_client.models import SparseVector
import uuid

logger = logging.getLogger(__name__)


class GitHubDataIngestionService:
    def __init__(self, app_integration: AppIntegration, use_graphql: bool = True):
        self.app_integration = app_integration
        self.use_graphql = use_graphql
        self._graphql_service = None
        self._repository_manager = None
        self.repository = None

    def _get_graphql_service(self) -> GitHubGraphQLIngestionService:
        if not self._graphql_service:
            self._graphql_service = GitHubGraphQLIngestionService(self.app_integration)
        return self._graphql_service

    def _get_repository_manager(self) -> GitHubRepositoryManager:
        if not self._repository_manager:
            self._repository_manager = GitHubRepositoryManager(self.app_integration)
        return self._repository_manager

    def ingest_repository_data(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            self._get_or_create_repository(owner, repo)
            self._update_repository_status('ingesting')
            
            if self.use_graphql:
                self._ingest_with_graphql(owner, repo, since)
            else:
                self._ingest_with_rest_api(owner, repo, since)
            
            self._create_and_store_embeddings()
            self._update_repository_status('completed')
            
            logger.info(f"Successfully completed ingestion for {owner}/{repo}")
            
        except Exception as e:
            logger.error(f"Failed to ingest repository {owner}/{repo}: {e}")
            self._update_repository_status('failed')
            raise

    def _get_or_create_repository(self, owner: str, repo: str):
        repository_manager = self._get_repository_manager()
        self.repository = repository_manager.get_or_create_repository(owner, repo)
        return self.repository

    def _update_repository_status(self, status: str):
        if self.repository:
            repository_manager = self._get_repository_manager()
            repository_manager.update_ingestion_status(self.repository, status)

    def _ingest_with_graphql(self, owner: str, repo: str, since: Optional[str] = None):
        graphql_service = self._get_graphql_service()
        graphql_service.ingest_repository_data(owner, repo, since)

    def _ingest_with_rest_api(self, owner: str, repo: str, since: Optional[str] = None):
        repository_manager = self._get_repository_manager()
        github_client = repository_manager.get_github_client()
        
        issue_service = GitHubIssueIngestionService(github_client, self.repository)
        issue_service.ingest_issues(owner, repo, since)
        
        pr_service = GitHubPRIngestionService(github_client, self.repository)
        pr_service.ingest_pull_requests(owner, repo, since)

    def _create_and_store_embeddings(self):
        if not self.repository:
            logger.warning("No repository available for embedding creation")
            return
        
        try:
            content = self._create_knowledge_base_content()
            if not content.strip():
                logger.warning("No content available for embedding creation")
                return
            
            chunks = chunk_text(content)
            logger.info(f"Created {len(chunks)} chunks from repository content")
            
            points = []
            for i, chunk in enumerate(chunks):
                dense_embedding = embed_text(chunk)
                sparse_embedding = embed_sparse(chunk)
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=dense_embedding,
                    payload={
                        'text': chunk,
                        'repository_id': str(self.repository.id),
                        'repository_name': self.repository.full_name,
                        'chunk_index': i,
                        'source': 'github_ingestion'
                    }
                )
                
                if sparse_embedding:
                    point.sparse_vector = SparseVector(
                        indices=sparse_embedding['indices'],
                        values=sparse_embedding['values']
                    )
                
                points.append(point)
            
            if points:
                qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                logger.info(f"Successfully stored {len(points)} embeddings in vector database")
            
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            logger.warning("Continuing without embeddings due to error")

    def _create_knowledge_base_content(self) -> str:
        """Create knowledge base content from all ingested data"""
        if not self.repository:
            return ""
        
        content_parts = []
        
        content_parts.append(f"# Repository: {self.repository.full_name}")
        if self.repository.description:
            content_parts.append(f"Description: {self.repository.description}")
        content_parts.append("")
        
        self._add_issues_to_content(content_parts)
        
        self._add_pull_requests_to_content(content_parts)
        
        return "\n".join(content_parts)

    def _add_issues_to_content(self, content_parts: list):
        """Add issues to knowledge base content"""
        issues = self.repository.issues.all().order_by('-created_at')[:50]
        
        if not issues:
            return
        
        content_parts.append("## Issues")
        for issue in issues:
            content_parts.append(f"### Issue #{issue.number}: {issue.title}")
            content_parts.append(f"State: {issue.state}")
            content_parts.append(f"Author: {issue.author}")
            
            if issue.body:
                content_parts.append(f"Description: {issue.body[:500]}...")
            
            if issue.labels:
                content_parts.append(f"Labels: {', '.join(issue.labels)}")
            
            recent_comments = issue.comments.all().order_by('-created_at')[:3]
            if recent_comments:
                content_parts.append("**Recent Comments:**")
                for comment in recent_comments:
                    content_parts.append(f"- {comment.author}: {comment.body[:200]}...")
            
            content_parts.append("")

    def _add_pull_requests_to_content(self, content_parts: list):
        """Add pull requests to knowledge base content"""
        prs = self.repository.pull_requests.all().order_by('-created_at')[:50]
        
        if not prs:
            return
        
        content_parts.append("## Pull Requests")
        for pr in prs:
            content_parts.append(f"### PR #{pr.number}: {pr.title}")
            content_parts.append(f"State: {pr.state}")
            content_parts.append(f"Author: {pr.author}")
            
            if pr.body:
                content_parts.append(f"Description: {pr.body[:500]}...")
            
            if pr.labels:
                content_parts.append(f"Labels: {', '.join(pr.labels)}")
            
            if pr.merged:
                content_parts.append(f"**Merged:** Yes (Commit: {pr.merge_commit_sha[:8]}...)")
            else:
                content_parts.append("**Merged:** No")
            
            recent_comments = pr.comments.all().order_by('-created_at')[:3]
            if recent_comments:
                content_parts.append("**Recent Comments:**")
                for comment in recent_comments:
                    content_parts.append(f"- {comment.author}: {comment.body[:200]}...")
            
            content_parts.append("")

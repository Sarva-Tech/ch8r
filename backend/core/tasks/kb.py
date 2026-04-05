import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from django.utils import timezone

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX
from core.models import KnowledgeBase
from core.models.knowledge_base import KBStatus
from core.services import extract_text_from_file, ingest_kb
from core.services.url_ingestion import URLIngestionService

logger = logging.getLogger(__name__)


def send_kb_update(kb, status):
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning(f"[send_kb_update] Channel layer is None, skipping WS update for kb {kb.uuid}")
            return

        owner_id = kb.application.owner.id
        group_name = f"{LIVE_UPDATES_PREFIX}_{DASHBOARD_USER_ID_PREFIX}_{owner_id}"

        data = {
            "id": str(kb.id),
            "uuid": str(kb.uuid),
            "status": status,
        }

        logger.info(f"[send_kb_update] Sending status={status} for kb={kb.uuid} to group={group_name}")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send.kb.updates",
                "data": data,
            }
        )
        logger.info(f"[send_kb_update] Successfully sent update for kb={kb.uuid}")
    except Exception as e:
        logger.error(f"[send_kb_update] Failed to send WS update for kb={kb.uuid}: {e}", exc_info=True)


class KBProcessor(ABC):
    """Abstract base class for knowledge base processors."""

    @abstractmethod
    def extract_content(self, kb: KnowledgeBase) -> bool:
        """Extract content from knowledge base item."""
        pass

    @abstractmethod
    def should_process(self, kb: KnowledgeBase) -> bool:
        """Check if this processor should handle the given KB item."""
        pass

    def finalize_processing(self, kb: KnowledgeBase) -> bool:
        """Finalize processing after content extraction."""
        kb.refresh_from_db()
        if kb.status != KBStatus.DUPLICATE:
            kb.status = KBStatus.PROCESSED
            kb.save()
            send_kb_update(kb, kb.status)

            kb.status = KBStatus.COMPLETED
            self.post_processing_hook(kb)
            kb.save()
            send_kb_update(kb, kb.status)
        return True

    def post_processing_hook(self, kb: KnowledgeBase):
        """Hook for post-processing actions specific to each processor."""
        pass

    def process(self, kb: KnowledgeBase) -> bool:
        """Complete processing workflow."""
        success = self.extract_content(kb)
        if not success:
            return False

        # Common processing steps
        app = kb.application
        kb.status = KBStatus.PROCESSING
        kb.save()
        send_kb_update(kb, kb.status)

        ingest_kb(kb, app)

        return self.finalize_processing(kb)


class FileProcessor(KBProcessor):
    """Processor for file-based knowledge base items."""

    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'file'

    def extract_content(self, kb: KnowledgeBase) -> bool:
        is_modified = (kb.metadata or {}).get("is_modified_by_user", False)
        if not is_modified:
            kb.status = KBStatus.EXTRACTING
            kb.save()
            send_kb_update(kb, kb.status)

            content = extract_text_from_file(kb.path)

            kb.metadata = kb.metadata or {}
            kb.metadata['content'] = content
            kb.save()
        return True


class TextProcessor(KBProcessor):
    """Processor for text-based knowledge base items."""

    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'text'

    def extract_content(self, kb: KnowledgeBase) -> bool:
        # Text items already have content in metadata, no extraction needed
        return True


class URLProcessor(KBProcessor):
    def __init__(self):
        self.url_service = URLIngestionService()

    def _extract_single_url_content(self, url: str, retry_config) -> List[Dict[str, Any]]:
        try:
            from core.url_modules.url_extractor import URLExtractor
            from core.url_modules.content_extractor import ContentExtractor
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; ch8r-crawler/1.0)'},
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            url_extractor = URLExtractor()
            content_extractor = ContentExtractor(url_extractor)

            content_data = content_extractor.extract_content(soup, url)

            if content_data and content_data.get('content', '').strip():
                return [{
                    'url': url,
                    'title': content_data.get('title', ''),
                    'description': content_data.get('description', ''),
                    'content': content_data.get('content', ''),
                    'content_length': len(content_data.get('content', '')),
                    'content_type': content_data.get('content_type', 'text/html'),
                    'status_code': response.status_code,
                    'depth': 0,
                    'parent_url': None,
                    'links': content_data.get('links', []),
                    'links_count': len(content_data.get('links', [])),
                    'extraction_timestamp': timezone.now().isoformat()
                }]
            else:
                logger.warning(f"No content extracted from URL {url}")
                return []

        except Exception as e:
            logger.error(f"Failed to extract content from URL {url}: {str(e)}")
            return []

    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'url'

    def extract_content(self, kb: KnowledgeBase) -> bool:
        success = self.url_service.extract_url_content(kb)

        if not success:
            return False

        enable_crawling = (kb.metadata or {}).get('crawling_enabled', False)

        if enable_crawling:
            self._handle_crawling(kb)
        else:
            self._handle_no_crawling(kb)

        return True

    def _handle_crawling(self, kb: KnowledgeBase) -> None:
        crawling_config = self._get_crawling_config(kb)
        crawled_data = self._crawl_urls(kb, crawling_config)
        self._process_crawled_data(kb, crawled_data)

    def _handle_no_crawling(self, kb: KnowledgeBase) -> None:
        kb.metadata = kb.metadata or {}
        kb.metadata.update({
            'crawling_status': 'disabled',
            'crawling_timestamp': kb.updated_at.isoformat()
        })
        kb.save(update_fields=['metadata'])

    def _get_crawling_config(self, kb: KnowledgeBase) -> Dict[str, Any]:
        return (kb.metadata or {}).get('crawling_config', {
            'max_depth': 1,
            'max_pages': 50
        })

    def _crawl_urls(self, kb: KnowledgeBase, crawling_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        from core.url_modules.url_crawler import URLCrawler
        from core.url_modules.url_deduplicator import URLDeduplicator

        max_depth = crawling_config.get('max_depth', 1)
        max_pages = crawling_config.get('max_pages', 50)

        retry_config = self._create_retry_config()
        crawler = URLCrawler(max_depth=max_depth, max_pages=max_pages, delay=1.0, retry_config=retry_config)
        deduplicator = URLDeduplicator()

        urls_to_crawl = self._collect_urls_to_crawl(kb, deduplicator)
        crawled_data = self._perform_crawling(urls_to_crawl, crawler, kb.path, retry_config)

        self._update_crawling_metadata(kb, crawled_data, urls_to_crawl)
        return crawled_data

    def _create_retry_config(self) -> 'RetryConfig':
        from core.url_modules.error_handler import RetryConfig
        return RetryConfig(
            max_retries=2,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            jitter=True
        )

    def _collect_urls_to_crawl(self, kb: KnowledgeBase, deduplicator: 'URLDeduplicator') -> List[str]:
        all_urls_to_crawl = []
        visited_urls = set()

        main_url = kb.path
        all_urls_to_crawl.append(main_url)
        visited_urls.add(main_url)

        links = kb.metadata.get('links', [])
        for link in links:
            url = self._extract_url_from_link(link)
            if url and not deduplicator.is_duplicate(url, visited_urls):
                all_urls_to_crawl.append(url)
                visited_urls.add(url)

        sitemap_data = kb.metadata.get('sitemap')
        if sitemap_data and isinstance(sitemap_data, dict):
            sitemap_urls = sitemap_data.get('sitemap_urls', [])
            for url in sitemap_urls:
                if url and not deduplicator.is_duplicate(url, visited_urls):
                    all_urls_to_crawl.append(url)
                    visited_urls.add(url)

        return all_urls_to_crawl

    def _extract_url_from_link(self, link) -> 'Optional[str]':
        if isinstance(link, dict) and 'url' in link:
            return link['url']
        elif isinstance(link, str):
            return link
        return None

    def _perform_crawling(self, urls_to_crawl: List[str], crawler: 'URLCrawler', main_url: str, retry_config: 'RetryConfig') -> List[Dict[str, Any]]:
        crawled_data = []
        max_pages = crawler.crawling_engine.max_pages

        logger.info(f"Starting crawling of {len(urls_to_crawl)} unique URLs (max_pages: {max_pages})")

        for i, url in enumerate(urls_to_crawl):
            if len(crawled_data) >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages}), stopping crawling")
                break

            try:
                logger.info(f"Crawling URL {i+1}/{len(urls_to_crawl)}: {url}")
                url_crawled = self._extract_single_url_content(url, retry_config)

                if url_crawled:
                    crawled_data.extend(url_crawled)
                    logger.info(f"Successfully extracted {len(url_crawled)} pages from {url}")
                else:
                    logger.warning(f"No content extracted from {url}")

            except Exception as e:
                logger.warning(f"Failed to crawl URL {url}: {str(e)}")
                continue

        return crawled_data

    def _update_crawling_metadata(self, kb: KnowledgeBase, crawled_data: List[Dict[str, Any]], urls_to_crawl: List[str]) -> None:
        main_url = kb.path

        for i, page in enumerate(crawled_data):
            page_url = page.get('url', '')

        kb.metadata.update({
            'crawling_status': 'completed',
            'crawling_timestamp': kb.updated_at.isoformat(),
            'crawled_data': {
                'pages_crawled': len(crawled_data),
                'unique_urls_attempted': len(urls_to_crawl),
                'unique_urls_crawled': len(set([page.get('url', '') for page in crawled_data])),
                'main_url': main_url,
                'links_found': len(kb.metadata.get('links', [])),
                'sitemap_urls_found': len(kb.metadata.get('sitemap', {}).get('sitemap_urls', [])) if kb.metadata.get('sitemap') else 0
            }
        })
        kb.save(update_fields=['metadata'])

    def _process_crawled_data(self, kb: KnowledgeBase, crawled_data: List[Dict[str, Any]]) -> None:
        main_url = kb.path

        try:
            from core.services import ingest_kb
            crawled_content_items = []

            for page in crawled_data:
                crawled_kb = self._process_crawled_page(page, main_url, kb)
                if crawled_kb:
                    crawled_content_items.append(crawled_kb)

            if crawled_content_items:
                self._ingest_crawled_content(crawled_content_items, kb)
            else:
                self._handle_no_crawled_content(kb)

        except Exception as e:
            self._handle_crawling_error(kb, str(e))

    def _process_crawled_page(self, page: Dict[str, Any], main_url: str, kb: KnowledgeBase) -> 'Optional[KnowledgeBase]':
        page_content = page.get('content', '')
        page_url = page.get('url', '')
        page_title = page.get('title', '')

        if page_url == main_url:
            return None

        if page_content.strip():
            combined_content = f"URL: {page_url}\nTitle: {page_title}\n\nContent:\n{page_content}"

            crawled_kb = KnowledgeBase.objects.create(
                application=kb.application,
                path=page_url,
                source_type='crawled_url',
                status='pending',
                metadata={
                    'content': combined_content,
                    'original_kb_uuid': str(kb.uuid),
                    'crawled_from_url': page_url,
                    'page_title': page_title,
                    'content_length': len(combined_content),
                    'crawled_at': kb.updated_at.isoformat()
                }
            )

            return crawled_kb
        else:
            return None

    def _ingest_crawled_content(self, crawled_content_items: List[KnowledgeBase], kb: KnowledgeBase) -> None:
        logger.info(f"Created {len(crawled_content_items)} crawled KB items for ingestion for KB {kb.uuid} (excluding main URL)")

        successful_ingestions = 0
        failed_ingestions = 0

        for crawled_kb in crawled_content_items:
            try:
                from core.services import ingest_kb
                ingest_kb(crawled_kb, crawled_kb.application)
                successful_ingestions += 1
                logger.info(f"Successfully ingested crawled page: {crawled_kb.path}")
            except Exception as e:
                failed_ingestions += 1
                logger.error(f"Failed to ingest crawled page {crawled_kb.path}: {str(e)}")
                crawled_kb.delete()

        kb.metadata['crawled_content_ingested'] = True
        kb.metadata['crawled_content_ingested_at'] = kb.updated_at.isoformat()
        kb.metadata['crawled_content_stats'] = {
            'pages_ingested': successful_ingestions,
            'pages_failed': failed_ingestions,
            'total_pages_attempted': len(crawled_content_items),
            'success_rate': successful_ingestions / len(crawled_content_items) if crawled_content_items else 0,
            'main_url_included': True,
            'main_url_separate_ingestion': False
        }
        kb.save(update_fields=['metadata'])

        logger.info(f"Crawled content ingestion complete for KB {kb.uuid}: {successful_ingestions}/{len(crawled_content_items)} pages ingested")

    def _handle_no_crawled_content(self, kb: KnowledgeBase) -> None:
        logger.warning(f"No crawled content found for ingestion for KB {kb.uuid}")
        kb.metadata['crawled_content_ingested'] = False
        kb.metadata['crawled_content_ingestion_error'] = 'No crawled content found for ingestion'
        kb.save(update_fields=['metadata'])

    def _handle_crawling_error(self, kb: KnowledgeBase, error_message: str) -> None:
        logger.error(f"Failed to ingest crawled content for KB {kb.uuid}: {error_message}")
        kb.metadata = kb.metadata or {}
        kb.metadata['crawled_content_ingested'] = False
        kb.metadata['crawled_content_ingestion_error'] = error_message
        kb.save(update_fields=['metadata'])

    def post_processing_hook(self, kb: KnowledgeBase):
        """Update extraction timestamp for URLs when processing completes."""
        if kb.metadata:
            kb.metadata['extraction_timestamp'] = kb.updated_at.isoformat()
            kb.save(update_fields=['metadata'])


def get_processor(kb: KnowledgeBase) -> KBProcessor:
    """Factory function to get appropriate processor for KB item."""
    processors = {
        'file': FileProcessor(),
        'text': TextProcessor(),
        'url': URLProcessor()
    }

    processor = processors.get(kb.source_type)
    if not processor:
        raise ValueError(f"No processor found for source_type: {kb.source_type}")

    return processor


def process_kb_item(kb: KnowledgeBase) -> bool:
    """Process a knowledge base item using appropriate processor."""
    try:
        processor = get_processor(kb)
        return processor.process(kb)

    except Exception as e:
        logger.error(f"Error processing KB {kb.uuid}: {str(e)}")
        metadata = kb.metadata or {}
        metadata['error'] = str(e)
        kb.metadata = metadata
        kb.status = KBStatus.FAILED
        kb.save()
        send_kb_update(kb, kb.status)
        return False

@shared_task
def process_kb(kb_ids):
    kb_items = KnowledgeBase.objects.filter(id__in=kb_ids).select_related('application__owner')

    for kb in kb_items:
        try:
            process_kb_item(kb)
        except Exception as e:
            metadata = kb.metadata or {}
            metadata['error'] = str(e)
            kb.metadata = metadata
            kb.status = KBStatus.FAILED
            kb.save()
            send_kb_update(kb, kb.status)

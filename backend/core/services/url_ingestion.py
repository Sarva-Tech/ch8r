import logging
from typing import Optional, Dict, Any

import requests
from core.models import KnowledgeBase
from core.url_modules.url_extractor import URLExtractor

logger = logging.getLogger(__name__)


class URLIngestionService:
    def __init__(self):
        self.extractor = URLExtractor()

    def create_url_kb(self, application, url, user, crawling_config=None):
        from core.models import KnowledgeBase

        kb = KnowledgeBase.objects.create(
            application=application,
            path=url,
            source_type='url',
            status='pending',
            owner=user,
            metadata={
                'extraction_status': 'pending',
                'crawling_enabled': crawling_config.get('enable_crawling', False) if crawling_config else False,
                'crawling_config': crawling_config if crawling_config else {}
            }
        )

        logger.info(f"Created URL KB {kb.uuid} for {url} with crawling_enabled={kb.metadata.get('crawling_enabled', False)}")
        return kb

    def extract_url_content(self, kb: KnowledgeBase) -> bool:
        if kb.source_type != 'url':
            logger.error(f"KB {kb.uuid} is not a URL source type")
            return False

        url = kb.path
        if not url:
            logger.error(f"KB {kb.uuid} has no URL path")
            return False

        try:
            kb.status = 'extracting'
            kb.save(update_fields=['status'])

            extracted_data = self.extractor.extract_content(url)

            if extracted_data is None:
                logger.error(f"Failed to extract content from URL {url}")
                kb.status = 'failed'
                kb.metadata = kb.metadata or {}
                kb.metadata['extraction_status'] = 'failed'
                kb.metadata['extraction_error'] = 'Failed to extract content from URL'
                kb.save(update_fields=['status', 'metadata'])
                return False

            kb.metadata = kb.metadata or {}
            kb.metadata.update({
                'url': extracted_data['url'],
                'title': extracted_data['title'],
                'description': extracted_data['description'],
                'content': extracted_data['content'],
                'content_length': len(extracted_data.get('content', '')),
                'links': extracted_data['links'],
                'links_count': len(extracted_data.get('links', [])),
                'content_type': extracted_data['content_type'],
                'extraction_status': 'completed',
                'extraction_timestamp': kb.updated_at.isoformat()
            })

            if 'sitemap' in extracted_data:
                kb.metadata['sitemap'] = extracted_data['sitemap']

            kb.status = 'processing'
            kb.save(update_fields=['status', 'metadata'])

            logger.info(f"Successfully extracted content from URL {url} for KB {kb.uuid}")
            return True

        except Exception as e:
            logger.error(f"Error extracting content from URL {url} for KB {kb.uuid}: {str(e)}")
            kb.status = 'failed'
            kb.metadata = kb.metadata or {}
            kb.metadata['extraction_status'] = 'failed'
            kb.metadata['extraction_error'] = str(e)
            kb.save(update_fields=['status', 'metadata'])
            return False

    def enable_crawling_for_kb(self, kb: KnowledgeBase, max_depth: int = 2, max_pages: int = 25):
        if kb.source_type != 'url':
            raise ValueError("Crawling can only be enabled for URL knowledge base items")

        kb.metadata = kb.metadata or {}
        kb.metadata.update({
            'crawling_enabled': True,
            'crawling_config': {
                'max_depth': max_depth,
                'max_pages': max_pages,
                'enabled_at': kb.updated_at.isoformat()
            }
        })
        kb.save(update_fields=['metadata'])
        logger.info(f"Enabled crawling for KB {kb.uuid} with max_depth={max_depth}, max_pages={max_pages}")

    def disable_crawling_for_kb(self, kb: KnowledgeBase):
        if kb.source_type != 'url':
            return

        kb.metadata = kb.metadata or {}
        kb.metadata['crawling_enabled'] = False
        kb.metadata['crawling_config'] = kb.metadata.get('crawling_config', {})
        kb.metadata['crawling_config']['disabled_at'] = kb.updated_at.isoformat()
        kb.save(update_fields=['metadata'])

        logger.info(f"Disabled crawling for URL KB {kb.uuid}")

    def validate_url_before_ingestion(self, url: str, simple_validation: bool = False) -> Dict[str, Any]:
        if not self.extractor.is_valid_url(url):
            return {
                'valid': False,
                'error': 'Invalid URL format'
            }

        if simple_validation:
            return {
                'valid': True,
                'title': None,
                'description': None,
                'content_length': 0,
                'content_type': None,
                'message': 'URL format is valid. Content will be extracted during processing.'
            }

        try:
            extracted_data = self.extractor.extract_content(url)

            if extracted_data is None:
                return {
                    'valid': False,
                    'error': 'URL is not accessible, disallowed by robots.txt, or content extraction failed'
                }

            return {
                'valid': True,
                'title': extracted_data.get('title'),
                'description': extracted_data.get('description'),
                'content_length': len(extracted_data.get('content', '')),
                'links_count': len(extracted_data.get('links', [])),
                'content_type': extracted_data.get('content_type')
            }

        except requests.exceptions.Timeout:
            return {
                'valid': False,
                'error': 'URL validation timed out. The URL may be slow to respond or blocked.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'valid': False,
                'error': 'Could not connect to the URL. Please check if the URL is correct and accessible.'
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                return {
                    'valid': False,
                    'error': 'Access to the URL is forbidden (403). The website may block automated access.'
                }
            elif e.response.status_code == 404:
                return {
                    'valid': False,
                    'error': 'URL not found (404). Please check if the URL is correct.'
                }
            else:
                return {
                    'valid': False,
                    'error': f'HTTP error {e.response.status_code}: {e.response.reason}'
                }
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return {
                'valid': False,
                'error': f'Error accessing URL: {str(e)}'
            }

    def reprocess_url(self, kb: KnowledgeBase) -> bool:
        if kb.source_type != 'url':
            logger.error(f"KB {kb.uuid} is not a URL source type")
            return False

        kb.status = 'reprocessing'
        kb.metadata = kb.metadata or {}
        kb.metadata['extraction_status'] = 'pending'
        if 'extraction_error' in kb.metadata:
            del kb.metadata['extraction_error']
        kb.save(update_fields=['status', 'metadata'])

        return self.extract_url_content(kb)

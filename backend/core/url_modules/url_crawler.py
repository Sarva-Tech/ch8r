import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Dict, Any
import logging

from .url_extractor import URLExtractor
from .url_validator import URLValidator
from .url_deduplicator import URLDeduplicator
from .content_extractor import ContentExtractor
from .crawling_engine import CrawlingEngine
from .crawl_statistics import CrawlStatistics
from .error_handler import RetryConfig

logger = logging.getLogger(__name__)


class URLCrawler:
    def __init__(self, max_depth: int = 1, max_pages: int = 50, delay: float = 1.0,
                 retry_config: RetryConfig = None):
        self.url_extractor = URLExtractor()

        self.validator = URLValidator(self.url_extractor)
        self.deduplicator = URLDeduplicator()
        self.content_extractor = ContentExtractor(self.url_extractor)
        self.crawling_engine = CrawlingEngine(max_depth, max_pages, delay, retry_config)
        self.statistics = CrawlStatistics()

    def crawl(self, start_url: str) -> List[Dict[str, Any]]:
        if not self.crawling_engine.check_robots_with_retry(self.validator, start_url):
            logger.warning(f"Start URL {start_url} is disallowed by robots.txt")
            return []

        self.statistics.reset()

        queue = self.crawling_engine.initialize_crawl(start_url)
        self.statistics.record_visited_url(start_url, 0)

        while queue and len(self.statistics.visited_urls) < self.crawling_engine.max_pages:
            current_url, depth, parent_url, retry_attempt = queue.popleft()

            if not self.crawling_engine.should_process_url(current_url, depth, self.statistics.visited_urls, retry_attempt):
                continue

            try:
                logger.info(f"Crawling URL: {current_url} (depth: {depth}, parent: {parent_url}, attempt: {retry_attempt + 1})")

                response = self.crawling_engine.fetch_page_with_retry(self.url_extractor.session, current_url)
                if not response:
                    continue

                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type:
                    self.statistics.record_visited_url(current_url, depth)
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                page_data = self.content_extractor.extract_content(soup, current_url)
                page_data.update({
                    'depth': depth,
                    'parent_url': parent_url,
                    'retry_attempts': retry_attempt,
                    'status_code': response.status_code,
                    'content_type': content_type
                })

                self.statistics.record_crawled_page(page_data)
                self.statistics.record_visited_url(current_url, depth)
                self.crawling_engine.error_tracker.record_success()

                if parent_url:
                    self.statistics.record_parent_child_relationship(parent_url, current_url)

                if depth < self.crawling_engine.max_depth - 1:
                    links = self.content_extractor.extract_links(soup, current_url)
                    filtered_links = self._filter_links(links, current_url, depth)
                    self.crawling_engine.add_links_to_queue(
                        filtered_links, current_url, depth, queue, self.statistics.url_depth_map
                    )

                self.crawling_engine.apply_rate_limit()

            except Exception as e:
                logger.error(f"Failed to crawl {current_url} (attempt {retry_attempt + 1}): {str(e)}")

                self.crawling_engine.error_tracker.record_error(current_url, e, retry_attempt)

                if not self.crawling_engine.requeue_failed_url(queue, current_url, depth, parent_url, retry_attempt, e):
                    self.statistics.record_visited_url(current_url, depth)

        logger.info(f"Crawling completed. Visited {len(self.statistics.visited_urls)} URLs, extracted {len(self.statistics.crawled_data)} pages")

        error_summary = self.crawling_engine.get_error_summary()
        if error_summary['failed_attempts'] > 0:
            logger.warning(f"Crawling errors: {error_summary['failed_attempts']} failed out of {error_summary['total_attempts']} attempts")
            logger.info(f"Success rate: {error_summary['success_rate']:.2%}")

        return self.statistics.crawled_data

    def _filter_links(self, links: List[str], current_url: str, current_depth: int) -> List[str]:
        """Filter links using validation and deduplication components."""
        base_domain = urlparse(current_url).netloc
        filtered_links = []

        for link in links:
            if (self.validator.should_crawl_url(
                    link, base_domain, current_depth + 1,
                    self.statistics.url_depth_map, self.statistics.visited_urls
                ) and not self.deduplicator.is_duplicate(link, self.statistics.visited_urls)):
                filtered_links.append(link)

        return filtered_links

    def get_crawl_stats(self) -> Dict[str, Any]:
        stats = self.statistics.get_statistics()
        stats['error_summary'] = self.crawling_engine.get_error_summary()
        return stats

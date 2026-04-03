from collections import deque
from urllib.parse import urlparse
from typing import List, Dict, Any, Set, Optional
import logging
import time
from .error_handler import ErrorHandler, RetryConfig, RetryStrategy, CrawlErrorTracker

logger = logging.getLogger(__name__)


class CrawlingEngine:
    def __init__(self, max_depth: int = 1, max_pages: int = 50, delay: float = 1.0,
                 retry_config: RetryConfig = None):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.error_tracker = CrawlErrorTracker()

        self.http_retry_config = retry_config or RetryConfig(
            max_retries=2,
            base_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=True,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )

        self.robots_retry_config = RetryConfig(
            max_retries=2,
            base_delay=0.5,
            max_delay=5.0,
            backoff_multiplier=1.5,
            jitter=True,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF
        )

    def initialize_crawl(self, start_url: str) -> deque:
        queue = deque([(start_url, 0, None, 0)])
        return queue

    def should_process_url(self, current_url: str, depth: int, visited_urls: Set[str], retry_attempt: int) -> bool:
        if depth >= self.max_depth:
            return False
        if current_url in visited_urls:
            return False
        if retry_attempt > self.http_retry_config.max_retries:
            return False
        return True

    def add_links_to_queue(self, links: List[str], current_url: str, current_depth: int,
                          queue: deque, url_depth_map: Dict[str, int]) -> None:
        if current_depth >= self.max_depth - 1:
            return

        base_domain = urlparse(current_url).netloc
        for link in links[:30]:
            existing_depth = url_depth_map.get(link, float('inf'))
            if current_depth + 1 < existing_depth:
                queue.append((link, current_depth + 1, current_url, 0))
                url_depth_map[link] = current_depth + 1

    def apply_rate_limit(self) -> None:
        time.sleep(self.delay)

    def fetch_page_with_retry(self, session, url: str) -> Optional[Any]:
        http_handler = ErrorHandler(self.http_retry_config)

        def _fetch():
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response

        try:
            return http_handler.execute_with_retry(_fetch)
        except Exception as e:
            self.error_tracker.record_error(url, e, 0)
            raise e

    def check_robots_with_retry(self, validator, url: str) -> bool:
        robots_handler = ErrorHandler(self.robots_retry_config)

        def _check_robots():
            return validator.check_robots_txt(url)

        try:
            return robots_handler.execute_with_retry(_check_robots)
        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {url} after retries: {e}")
            return True

    def requeue_failed_url(self, queue: deque, url: str, depth: int, parent_url: str,
                          retry_attempt: int, error: Exception) -> bool:
        error_handler = ErrorHandler(self.http_retry_config)

        if error_handler.should_retry(error, retry_attempt):
            delay = error_handler.calculate_delay(retry_attempt, error)
            logger.warning(f"Requeuing {url} in {delay:.2f}s (attempt {retry_attempt + 1})")

            time.sleep(delay)
            queue.append((url, depth, parent_url, retry_attempt + 1))
            return True

        return False

    def get_error_summary(self) -> Dict[str, Any]:
        return self.error_tracker.get_error_summary()

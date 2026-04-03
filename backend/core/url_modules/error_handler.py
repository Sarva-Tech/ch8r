import time
import random
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"


class ErrorCategory(Enum):
    NETWORK_ERROR = "network_error"
    HTTP_ERROR = "http_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSING_ERROR = "parsing_error"
    ROBOTS_ERROR = "robots_error"
    UNKNOWN_ERROR = "unknown_error"


class RetryConfig:
    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_multiplier: float = 2.0,
                 jitter: bool = True,
                 retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.retry_strategy = retry_strategy


class ErrorHandler:
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.error_retry_map = self._build_error_retry_map()

    def _build_error_retry_map(self) -> Dict[ErrorCategory, RetryStrategy]:
        return {
            ErrorCategory.NETWORK_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.TIMEOUT_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.HTTP_ERROR: RetryStrategy.LINEAR_BACKOFF,
            ErrorCategory.PARSING_ERROR: RetryStrategy.FIXED_DELAY,
            ErrorCategory.ROBOTS_ERROR: RetryStrategy.NO_RETRY,
            ErrorCategory.UNKNOWN_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF
        }

    def categorize_error(self, error: Exception) -> ErrorCategory:
        error_name = error.__class__.__name__.lower()
        error_message = str(error).lower()

        if any(term in error_name for term in ['connection', 'network', 'dns']):
            return ErrorCategory.NETWORK_ERROR

        if any(term in error_name + error_message for term in ['timeout', 'timed out']):
            return ErrorCategory.TIMEOUT_ERROR

        if any(term in error_name for term in ['http', 'response']):
            return ErrorCategory.HTTP_ERROR

        if any(term in error_name for term in ['parse', 'xml', 'html']):
            return ErrorCategory.PARSING_ERROR

        if 'robots' in error_message:
            return ErrorCategory.ROBOTS_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.config.max_retries:
            return False

        category = self.categorize_error(error)
        strategy = self.error_retry_map.get(category, RetryStrategy.NO_RETRY)

        return strategy != RetryStrategy.NO_RETRY

    def calculate_delay(self, attempt: int, error: Exception) -> float:
        category = self.categorize_error(error)
        strategy = self.error_retry_map.get(category, RetryStrategy.EXPONENTIAL_BACKOFF)

        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * (attempt + 1)
        elif strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        else:
            delay = 0

        delay = min(delay, self.config.max_delay)

        if self.config.jitter and delay > 0:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)

        return delay

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                last_error = error

                if not self.should_retry(error, attempt):
                    logger.error(f"Max retries exceeded or non-retryable error: {error}")
                    break

                delay = self.calculate_delay(attempt, error)
                logger.warning(f"Attempt {attempt + 1} failed: {error}. Retrying in {delay:.2f}s...")
                time.sleep(delay)

        raise last_error


class CrawlErrorTracker:
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_urls: Dict[str, List[str]] = {}
        self.total_attempts = 0
        self.successful_attempts = 0

    def record_error(self, url: str, error: Exception, attempt: int):
        self.total_attempts += 1

        error_type = error.__class__.__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        if error_type not in self.error_urls:
            self.error_urls[error_type] = []

        self.error_urls[error_type].append(f"{url} (attempt {attempt + 1})")

    def record_success(self):
        self.total_attempts += 1
        self.successful_attempts += 1

    def get_error_summary(self) -> Dict[str, Any]:
        return {
            'total_attempts': self.total_attempts,
            'successful_attempts': self.successful_attempts,
            'failed_attempts': self.total_attempts - self.successful_attempts,
            'success_rate': self.successful_attempts / self.total_attempts if self.total_attempts > 0 else 0,
            'error_counts': self.error_counts,
            'error_urls': self.error_urls
        }

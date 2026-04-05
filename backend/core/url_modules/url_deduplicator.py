from urllib.parse import urlparse, parse_qs, urlencode
from typing import Set
import logging

logger = logging.getLogger(__name__)


class URLDeduplicator:
    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        url_without_fragment = parsed._replace(fragment='').geturl()

        if parsed.query:
            query_params = parse_qs(parsed.query)
            sorted_params = {k: v[0] if v else '' for k, v in sorted(query_params.items())}
            sorted_query = urlencode(sorted_params)
            url_without_fragment = url_without_fragment.replace(f'?{parsed.query}', f'?{sorted_query}')

        if url_without_fragment.endswith('/') and url_without_fragment.count('/') > 3:
            url_without_fragment = url_without_fragment.rstrip('/')

        return url_without_fragment.lower()

    def is_duplicate(self, url: str, visited_urls: Set[str]) -> bool:
        normalized_url = self.normalize_url(url)
        normalized_visited = {self.normalize_url(visited) for visited in visited_urls}
        return normalized_url in normalized_visited

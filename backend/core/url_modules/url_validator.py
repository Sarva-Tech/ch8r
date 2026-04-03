from urllib.parse import urlparse
from typing import Set, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class URLValidator:
    def __init__(self, url_extractor):
        self.url_extractor = url_extractor

    def is_valid_url(self, url: str, base_domain: str) -> bool:
        return self.url_extractor.is_valid_url(url) and urlparse(url).netloc == base_domain

    def check_robots_txt(self, url: str) -> bool:
        return self.url_extractor._check_robots_txt(url)

    def should_crawl_url(self, url: str, base_domain: str, current_depth: int,
                        url_depth_map: Dict[str, int], visited_urls: Set[str]) -> bool:
        if url in visited_urls:
            return False

        existing_depth = url_depth_map.get(url, float('inf'))
        if current_depth >= existing_depth:
            return False

        if not self.is_valid_url(url, base_domain):
            return False

        if not self.check_robots_txt(url):
            return False

        skip_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.exe',
                          '.dmg', '.jpg', '.png', '.gif', '.css', '.js'}
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        skip_patterns = [
            r'/login', r'/register', r'/logout', r'/admin', r'/dashboard',
            r'/api/', r'/ajax/', r'/static/', r'/assets/', r'/images/',
            r'/css/', r'/js/', r'/fonts/', r'/media/', r'/files/',
            r'\.pdf$', r'\.doc', r'\.xls', r'\.zip', r'\.exe'
        ]

        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        return True

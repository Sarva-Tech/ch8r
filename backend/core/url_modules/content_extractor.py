from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ContentExtractor:
    def __init__(self, url_extractor):
        self.url_extractor = url_extractor

    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = self.url_extractor._extract_title(soup)
        description = self.url_extractor._extract_description(soup)
        content = self.url_extractor._extract_main_content(soup)
        links = self.url_extractor._extract_links(soup, url)

        return {
            'url': url,
            'title': title,
            'description': description,
            'content': content,
            'content_length': len(content),
            'links_count': len(links)
        }

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            if self.url_extractor.is_valid_url(absolute_url):
                links.append(absolute_url)

        return links

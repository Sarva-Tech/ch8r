import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class URLExtractor:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _discover_sitemap(self, base_url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(base_url)
            sitemap_urls = [
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml",
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap_index.xml",
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemaps.xml"
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap",
            ]

            for sitemap_url in sitemap_urls:
                response = self.session.get(sitemap_url, timeout=10)
                if response.status_code == 200 and 'xml' in response.headers.get('content-type', ''):
                    return sitemap_url

            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            robots_response = self.session.get(robots_url, timeout=10)
            if robots_response.status_code == 200:
                for line in robots_response.text.split('\n'):
                    if line.strip().startswith('Sitemap:'):
                        sitemap_from_robots = line.split(':', 1)[1].strip()
                        return sitemap_from_robots

            return None

        except Exception as e:
            logger.debug(f"Failed to discover sitemap for {base_url}: {str(e)}")
            return None

    def _parse_sitemap(self, sitemap_url: str) -> list:
        try:
            response = self.session.get(sitemap_url, timeout=10)
            if response.status_code != 200:
                return []

            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)

            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = []

            if root.tag.endswith('sitemapindex'):
                for sitemap in root.findall('ns:sitemap', namespaces):
                    loc = sitemap.find('ns:loc', namespaces)
                    if loc is not None:
                        urls.extend(self._parse_sitemap(loc.text))

            elif root.tag.endswith('urlset'):
                for url in root.findall('ns:url', namespaces):
                    loc = url.find('ns:loc', namespaces)
                    if loc is not None:
                        urls.append(loc.text)

            return urls[:50]

        except Exception as e:
            logger.debug(f"Failed to parse sitemap {sitemap_url}: {str(e)}")
            return []

    def _check_robots_txt(self, url: str) -> bool:
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)

            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                rp.parse(response.text)

                path = parsed_url.path or '/'
                return rp.can_fetch(self.session.headers['User-Agent'], path)

            return True

        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {url}: {str(e)}")
            return True

    def extract_content(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            if not self._check_robots_txt(url):
                logger.warning(f"URL {url} is disallowed by robots.txt")
                return None

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            title = self._extract_title(soup)
            description = self._extract_description(soup)

            content = self._extract_main_content(soup)

            links = self._extract_links(soup, url)

            sitemap_info = None
            try:
                base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                sitemap_url = self._discover_sitemap(base_url)
                if sitemap_url:
                    sitemap_urls = self._parse_sitemap(sitemap_url)
                    sitemap_info = {
                        'sitemap_url': sitemap_url,
                        'sitemap_urls_count': len(sitemap_urls),
                        'sitemap_urls': sitemap_urls[:50]
                    }
            except Exception as e:
                logger.debug(f"Sitemap discovery failed for {url}: {str(e)}")

            result = {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'links': links,
                'content_type': response.headers.get('content-type', ''),
                'status_code': response.status_code
            }

            if sitemap_info:
                result['sitemap'] = sitemap_info

            return result

        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()

        return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.main-content',
            '#content',
            '#main'
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                return self._clean_text(content_element.get_text())

        body = soup.find('body')
        if body:
            return self._clean_text(body.get_text())

        return ""

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            if urlparse(absolute_url).netloc == base_domain:
                links.append({
                    'url': absolute_url,
                    'text': link.get_text().strip(),
                    'title': link.get('title', '')
                })

        return links[:50]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

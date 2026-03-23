import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Production-grade GitHub API client with rate limiting and error handling"""

    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
            "User-Agent": "Ch8r-GitHub-Ingestion/1.0"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with proper error handling and rate limiting"""
        url = urljoin(self.BASE_URL, endpoint)

        max_retries = 3
        retry_delay = 1
        timeout = 30

        for attempt in range(max_retries):
            try:
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = timeout

                response = self.session.request(method, url, **kwargs)

                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if rate_limit_remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                        wait_time = max(reset_time - time.time(), 1)
                        logger.warning(f"Rate limit hit, waiting {wait_time:.1f} seconds")
                        time.sleep(wait_time)
                        continue

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
                    logger.error(f"GitHub API error: {error_msg}")

                    if response.status_code in [401, 404]:
                        raise requests.exceptions.HTTPError(f"GitHub API error: {error_msg}")
                    elif response.status_code >= 500:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))
                            continue
                        raise requests.exceptions.HTTPError(f"GitHub API server error: {error_msg}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                logger.error(f"Request timeout after {max_retries} attempts: {e}")
                raise

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                raise

        raise requests.exceptions.RequestException("Max retries exceeded")

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        return self._make_request('GET', f'/repos/{owner}/{repo}')

    def get_issues(self, owner: str, repo: str, state: str = 'all',
                   since: Optional[str] = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all issues for a repository"""
        issues = []
        page = 1

        params = {
            'state': state,
            'per_page': per_page,
            'sort': 'created',
            'direction': 'desc'
        }
        if since:
            params['since'] = since

        while True:
            params['page'] = page
            data = self._make_request('GET', f'/repos/{owner}/{repo}/issues', params=params)

            if not data:
                break

            issues.extend([issue for issue in data if 'pull_request' not in issue])

            if len(data) < per_page:
                break

            page += 1

        return issues

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """Get comments for a specific issue"""
        comments = []
        page = 1
        per_page = 100

        while True:
            data = self._make_request(
                'GET',
                f'/repos/{owner}/{repo}/issues/{issue_number}/comments',
                params={'page': page, 'per_page': per_page}
            )

            if not data:
                break

            comments.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return comments

    def get_pull_requests(self, owner: str, repo: str, state: str = 'all',
                         since: Optional[str] = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all pull requests for a repository"""
        prs = []
        page = 1

        params = {
            'state': state,
            'per_page': per_page,
            'sort': 'created',
            'direction': 'desc'
        }
        if since:
            params['since'] = since

        while True:
            params['page'] = page
            data = self._make_request('GET', f'/repos/{owner}/{repo}/pulls', params=params)

            if not data:
                break

            prs.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return prs

    def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get comments for a specific pull request"""
        comments = []
        page = 1
        per_page = 100

        while True:
            try:
                data = self._make_request(
                    'GET',
                    f'/repos/{owner}/{repo}/pulls/{pr_number}/comments',
                    params={'page': page, 'per_page': per_page}
                )

                if not data or len(data) == 0:
                    break

                comments.extend(data)

                if len(data) < per_page:
                    break

                page += 1
            except Exception as e:
                logger.error(f"Failed to fetch PR comments for {owner}/{repo}#{pr_number}, page {page}: {e}")
                break

        return comments

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get files changed in a pull request"""
        files = []
        page = 1
        per_page = 100

        while True:
            try:
                data = self._make_request(
                    'GET',
                    f'/repos/{owner}/{repo}/pulls/{pr_number}/files',
                    params={'page': page, 'per_page': per_page}
                )

                if not data or len(data) == 0:
                    break

                files.extend(data)

                if len(data) < per_page:
                    break

                page += 1
            except Exception as e:
                logger.error(f"Failed to fetch PR files for {owner}/{repo}#{pr_number}, page {page}: {e}")
                break

        return files

    def get_discussions(self, owner: str, repo: str, since: Optional[str] = None,
                       per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all discussions for a repository (requires GraphQL API)"""
        discussions = []
        page = 1

        query = f"repo:{owner}/{repo} is:discussion"
        if since:
            query += f" created:>{since}"

        params = {
            'q': query,
            'per_page': per_page,
            'sort': 'created',
            'order': 'desc'
        }

        while True:
            params['page'] = page
            data = self._make_request('GET', '/search/issues', params=params)

            if not data.get('items'):
                break

            discussions.extend(data['items'])

            if len(data['items']) < per_page:
                break

            page += 1

        return discussions

    def get_discussion_comments(self, owner: str, repo: str, discussion_number: int) -> List[Dict[str, Any]]:
        """Get comments for a discussion (requires GraphQL API)"""
        logger.warning(f"Discussion comments not implemented via REST API for {owner}/{repo}#{discussion_number}")
        return []

    def get_wiki_pages(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        GitHub's REST API does not expose wiki page content directly.
        The wiki is a separate git repo at https://github.com/{owner}/{repo}.wiki.git
        We return an empty list here — wiki content is not available via REST.
        """
        logger.info(f"Wiki pages are not available via GitHub REST API for {owner}/{repo}, skipping.")
        return []

    def get_repository_file(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get content of a specific repository file"""
        try:
            params = {}
            if ref:
                params['ref'] = ref

            return self._make_request('GET', f'/repos/{owner}/{repo}/contents/{path}', params=params)
        except requests.exceptions.HTTPError as e:
            if '404' in str(e):
                logger.info(f"File not found: {path} in {owner}/{repo}")
                return None
            raise

    def get_code_comments(self, owner: str, repo: str, path: str,
                         ref: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get code comments for a specific file"""
        try:
            params = {}
            if ref:
                params['ref'] = ref

            return self._make_request('GET', f'/repos/{owner}/{repo}/commits', params=params)
        except Exception as e:
            logger.error(f"Failed to fetch code comments for {owner}/{repo}/{path}: {e}")
            return []

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return self._make_request('GET', '/rate_limit')

    def close(self):
        """Close the session"""
        self.session.close()

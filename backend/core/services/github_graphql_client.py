import logging
import requests
from typing import Dict, List, Optional, Any
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
import time

logger = logging.getLogger(__name__)


class GitHubGraphQLClient:
    """GitHub GraphQL API v4 client for bulk operations"""

    def __init__(self, token: str):
        self.token = token
        self.endpoint = "https://api.github.com/graphql"
        
        self.transport = RequestsHTTPTransport(
            url=self.endpoint,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v4+json",
                "User-Agent": "Ch8r-GitHub-GraphQL/1.0"
            },
            timeout=30,
            retries=3
        )
        
        self.client = Client(transport=self.transport, fetch_schema_from_transport=False)

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query with error handling and rate limiting"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                query_doc = gql(query)
                result = self.client.execute(query_doc, variable_values=variables)
                return result

            except TransportQueryError as e:
                logger.error(f"GraphQL syntax error: {e}")
                raise

            except TransportServerError as e:
                error_data = str(e)
                
                if "rate limit" in error_data.lower() or "api rate limit exceeded" in error_data.lower():
                    logger.warning(f"Rate limit hit, waiting {retry_delay * (2 ** attempt)} seconds")
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                
                if "bad credentials" in error_data.lower() or "unauthorized" in error_data.lower():
                    logger.error(f"Authentication error: {e}")
                    raise
                
                logger.error(f"GraphQL execution error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise

            except Exception as e:
                logger.warning(f"Request failed, retrying ({attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                logger.error(f"GraphQL request failed after {max_retries} attempts: {e}")
                raise

        raise Exception("Max retries exceeded")

    def get_issues_with_comments(self, owner: str, repo: str, 
                                states: List[str] = None, 
                                since: Optional[str] = None,
                                first: int = 100,
                                after_cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Get issues with their comments in a single GraphQL query
        
        Args:
            owner: Repository owner
            repo: Repository name
            states: List of issue states (OPEN, CLOSED, etc.)
            since: ISO datetime string for filtering by creation date
            first: Number of items per page
            after_cursor: Pagination cursor
        if states is None:
            states = ["OPEN", "CLOSED"]

        state_filter = "[" + ", ".join([f"{state.upper()}" for state in states]) + "]"

        query = """
        query GetIssuesWithComments($owner: String!, $repo: String!, $states: [IssueState!]!, $first: Int!, $after: String, $orderBy: IssueOrder!) {
            repository(owner: $owner, name: $repo) {
                issues(first: $first, after: $after, states: $states, orderBy: $orderBy) {
                    pageInfo {
                        hasNextPage
                        endCursor
                        startCursor
                    }
                    edges {
                        node {
                            id
                            number
                            title
                            body
                            state
                            author {
                                login
                            }
                            authorAssociation
                            assignees(first: 10) {
                                nodes {
                                    login
                                }
                            }
                            labels(first: 20) {
                                nodes {
                                    name
                                }
                            }
                            milestone {
                                title
                            }
                            locked
                            createdAt
                            updatedAt
                            closedAt
                            url
                            comments(first: 100, orderBy: {field: UPDATED_AT, direction: ASC}) {
                                pageInfo {
                                    hasNextPage
                                    endCursor
                                }
                                edges {
                                    node {
                                        id
                                        body
                                        author {
                                            login
                                        }
                                        authorAssociation
                                        createdAt
                                        updatedAt
                                        url
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {
            "owner": owner,
            "repo": repo,
            "states": states,
            "first": first,
            "orderBy": {
                "field": "CREATED_AT",
                "direction": "DESC"
            }
        }
        
        if after_cursor:
            variables["after"] = after_cursor

        return self._execute_query(query, variables)

    def get_all_issues_with_comments(self, owner: str, repo: str, 
                                   states: List[str] = None,
                                   since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all issues with comments, handling pagination automatically
        
        Returns:
            List of all issues with their comments
        """
        all_issues = []
        has_next_page = True
        after_cursor = None

        while has_next_page:
            result = self.get_issues_with_comments(
                owner=owner, 
                repo=repo, 
                states=states,
                since=since,
                after_cursor=after_cursor
            )
            
            repository_data = result.get('repository')
            if not repository_data:
                break
                
            issues_data = repository_data.get('issues', {})
            edges = issues_data.get('edges', [])
            
            for edge in edges:
                issue_node = edge.get('node', {})
                if issue_node:
                    all_issues.append(issue_node)
            
            page_info = issues_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')
            
            logger.info(f"Fetched {len(edges)} issues, total so far: {len(all_issues)}")

        logger.info(f"Total issues fetched: {len(all_issues)}")
        return all_issues

    def get_all_pull_requests_with_comments(self, owner: str, repo: str,
                                           states: List[str] = None,
                                           since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all pull requests with comments, handling pagination automatically
        
        Returns:
            List of all pull requests with their comments
        """
        all_prs = []
        has_next_page = True
        after_cursor = None

        while has_next_page:
            result = self.get_pull_requests_with_comments(
                owner=owner, 
                repo=repo, 
                states=states,
                since=since,
                after_cursor=after_cursor
            )
            
            repository_data = result.get('repository')
            if not repository_data:
                break
                
            prs_data = repository_data.get('pullRequests', {})
            edges = prs_data.get('edges', [])
            
            for edge in edges:
                pr_node = edge.get('node', {})
                if pr_node:
                    all_prs.append(pr_node)
            
            page_info = prs_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')
            
            logger.info(f"Fetched {len(edges)} pull requests, total so far: {len(all_prs)}")

        logger.info(f"Total pull requests fetched: {len(all_prs)}")
        return all_prs

    def get_pull_requests_with_comments(self, owner: str, repo: str,
                                       states: List[str] = None,
                                       since: Optional[str] = None,
                                       first: int = 100,
                                       after_cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Get pull requests with their comments in a single GraphQL query
        
        Args:
            owner: Repository owner
            repo: Repository name
            states: List of PR states (OPEN, CLOSED, MERGED)
            since: ISO datetime string for filtering by creation date
            first: Number of items per page
            after_cursor: Pagination cursor
            
        Returns:
            Dictionary containing pull requests and pagination info
        """
        if states is None:
            states = ["OPEN", "CLOSED", "MERGED"]

        query = """
        query GetPRsWithComments($owner: String!, $repo: String!, $states: [PullRequestState!]!, $first: Int!, $after: String, $orderBy: IssueOrder!) {
            repository(owner: $owner, name: $repo) {
                pullRequests(first: $first, after: $after, states: $states, orderBy: $orderBy) {
                    pageInfo {
                        hasNextPage
                        endCursor
                        startCursor
                    }
                    edges {
                        node {
                            id
                            number
                            title
                            body
                            state
                            author {
                                login
                            }
                            authorAssociation
                            assignees(first: 10) {
                                nodes {
                                    login
                                }
                            }
                            labels(first: 20) {
                                nodes {
                                    name
                                }
                            }
                            milestone {
                                title
                            }
                            headRefName
                            baseRefName
                            merged
                            mergedAt
                            mergeCommit {
                                oid
                            }
                            additions
                            deletions
                            changedFiles
                            createdAt
                            updatedAt
                            closedAt
                            url
                            comments(first: 100, orderBy: {field: UPDATED_AT, direction: ASC}) {
                                pageInfo {
                                    hasNextPage
                                    endCursor
                                }
                                edges {
                                    node {
                                        id
                                        body
                                        author {
                                            login
                                        }
                                        authorAssociation
                                        createdAt
                                        updatedAt
                                        url
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {
            "owner": owner,
            "repo": repo,
            "states": states,
            "first": first,
            "orderBy": {
                "field": "CREATED_AT",
                "direction": "DESC"
            }
        }
        
        if after_cursor:
            variables["after"] = after_cursor

        return self._execute_query(query, variables)

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information using GraphQL"""
        query = """
        query GetRepositoryInfo($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                id
                name
                nameWithOwner
                description
                url
                isPrivate
                defaultBranchRef {
                    name
                }
                createdAt
                updatedAt
                pushedAt
                stargazerCount
                forkCount
                primaryLanguage {
                    name
                }
                licenseInfo {
                    name
                }
            }
        }
        """

        variables = {
            "owner": owner,
            "repo": repo
        }

        result = self._execute_query(query, variables)
        return result.get('repository', {})

    def close(self):
        """Close GraphQL client"""
        if hasattr(self.client, 'close_session'):
            self.client.close_session()

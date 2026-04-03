from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class CrawlStatistics:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[Dict[str, Any]] = []
        self.url_depth_map: Dict[str, int] = {}
        self.parent_child_map: Dict[str, List[str]] = {}

    def reset(self) -> None:
        self.visited_urls.clear()
        self.crawled_data.clear()
        self.url_depth_map.clear()
        self.parent_child_map.clear()

    def record_visited_url(self, url: str, depth: int) -> None:
        self.visited_urls.add(url)
        self.url_depth_map[url] = depth

    def record_crawled_page(self, page_data: Dict[str, Any]) -> None:
        self.crawled_data.append(page_data)

    def record_parent_child_relationship(self, parent_url: str, child_url: str) -> None:
        if parent_url not in self.parent_child_map:
            self.parent_child_map[parent_url] = []
        self.parent_child_map[parent_url].append(child_url)

    def get_statistics(self) -> Dict[str, Any]:
        if not self.crawled_data:
            return {
                'total_pages': 0,
                'total_urls_visited': 0,
                'deduplication_stats': {'duplicates_found': 0}
            }

        total_content_length = sum(page['content_length'] for page in self.crawled_data)
        avg_content_length = total_content_length / len(self.crawled_data)

        depth_distribution = {}
        for page in self.crawled_data:
            depth = page.get('depth', 0)
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1

        total_parent_children = sum(len(children) for children in self.parent_child_map.values())
        avg_children_per_parent = total_parent_children / len(self.parent_child_map) if self.parent_child_map else 0

        total_urls_seen = len(self.url_depth_map)
        duplicates_found = total_urls_seen - len(self.visited_urls)

        return {
            'total_pages': len(self.crawled_data),
            'total_urls_visited': len(self.visited_urls),
            'total_urls_encountered': total_urls_seen,
            'deduplication_stats': {
                'duplicates_found': duplicates_found,
                'deduplication_rate': duplicates_found / total_urls_seen if total_urls_seen > 0 else 0
            },
            'total_content_length': total_content_length,
            'average_content_length': avg_content_length,
            'depth_distribution': depth_distribution,
            'max_depth_reached': max(page.get('depth', 0) for page in self.crawled_data),
            'relationship_stats': {
                'parent_urls': len(self.parent_child_map),
                'total_child_links': total_parent_children,
                'avg_children_per_parent': avg_children_per_parent
            }
        }

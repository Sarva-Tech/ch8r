import re
import logging
import emoji

logger = logging.getLogger(__name__)


class ContentQualityFilter:
    def __init__(self):
        logger.debug("[ContentQualityFilter] Initialized with emoji-only filtering")

    def is_emoji_only(self, content: str) -> bool:
        if not content or not content.strip():
            return False

        content_clean = re.sub(r'\s+', '', content)

        if content_clean == '+1':
            return True

        emoji_chars = emoji.emoji_list(content_clean)

        if not emoji_chars:
            return False

        covered_chars = 0
        for emoji_info in emoji_chars:
            covered_chars += emoji_info['match_end'] - emoji_info['match_start']

        return covered_chars == len(content_clean)

    def is_bot_comment(self, author: str = None, content: str = None) -> bool:
        if not content and not author:
            return False

        bot_patterns = [
            r'dependabot(\[bot\])?',
            r'codecov(\[bot\])?',
            r'github-actions(\[bot\])?',
            r'cla-assistant(\[bot\])?',
            r'snyk(\[bot\])?',
            r'pull-request-review(\[bot\])?',
            r'sonarcloud(\[bot\])?',
            r'codacy(\[bot\])?',
            r'coveralls(\[bot\])?',
            r'this pr was merged',
            r'this pull request was merged',
            r'auto-merge',
            r'merge conflict',
            r'ci/cd',
            r'build passed',
            r'build failed',
            r'tests passed',
            r'tests failed'
        ]

        if author:
            author_lower = author.lower()
            for pattern in bot_patterns:
                if re.search(pattern, author_lower, re.IGNORECASE):
                    logger.debug(f"[QualityFilter] Detected bot author: {author}")
                    return True

        if content:
            content_lower = content.lower()
            for pattern in bot_patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    logger.debug(f"[QualityFilter] Detected bot content: {content[:50]}...")
                    return True

        return False

    def should_ingest(self, content: str, content_type: str = 'text', author: str = None) -> bool:
        if self.is_emoji_only(content):
            logger.info(f"[QualityFilter] Skipping emoji-only content: {content[:50]}...")
            return False

        if self.is_bot_comment(author=author, content=content):
            logger.info(f"[QualityFilter] Skipping bot/automated content: {content[:50]}...")
            return False

        return True

    def remove_emojis(self, content: str) -> str:
        if not content or not content.strip():
            return content

        cleaned = emoji.replace_emoji(content, replace='')
        cleaned = re.sub(r'\+1', '', cleaned)

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

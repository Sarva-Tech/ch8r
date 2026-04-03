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

    def should_ingest(self, content: str, content_type: str = 'text') -> bool:
        if self.is_emoji_only(content):
            logger.info(f"[QualityFilter] Skipping emoji-only content: {content[:50]}...")
            return False

        return True

    def remove_emojis(self, content: str) -> str:
        if not content or not content.strip():
            return content

        cleaned = emoji.replace_emoji(content, replace='')
        cleaned = re.sub(r'\+1', '', cleaned)

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

"""News article parsing helpers built on top of :class:`Sitemap`."""

from typing import Dict, Optional

import html2text
import requests
from bs4 import BeautifulSoup

from .sitemap import Sitemap
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger


class News(Sitemap):
    """Extract article metadata and content from individual pages."""

    def __init__(self, url: str, config: Dict, show_log: bool = False) -> None:
        super().__init__(url)
        self.config = config
        self.logger = setup_logger(__name__, show_log)

    def extract_detail(self, url: str) -> Dict:
        """Fetch title, summary, and metadata for a given article URL."""

        try:
            self.logger.debug("Fetching article: %s", url)
            response = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            details = {
                "title": self._get_text(soup, self.config.get("title_selector")),
                "short_description": self._get_text(
                    soup, self.config.get("short_desc_selector")
                ),
                "publish_time": self._get_text(
                    soup, self.config.get("publish_time_selector")
                ),
                "author": self._get_text(soup, self.config.get("author_selector")),
                "url": url,
            }
            self.logger.debug(
                "Article details extracted successfully: %s", details
            )
            return details
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Failed to fetch or parse article: %s", exc)
            return {"error": f"Failed to fetch or parse article: {exc}"}

    def article_to_markdown(
        self,
        url: str,
        retain_links: bool = True,
        retain_images: bool = True,
    ) -> str:
        """Download an article and convert its content to Markdown."""

        try:
            self.logger.debug("Converting article to Markdown: %s", url)
            response = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            content_selector = self.config.get("content_selector")
            if not content_selector:
                raise ValueError("Missing 'content_selector' in configuration.")

            content = soup.find(
                content_selector["tag"], class_=content_selector["class"]
            )
            if not content:
                raise ValueError("Content not found with the given selector.")

            converter = html2text.HTML2Text()
            converter.ignore_links = not retain_links
            converter.ignore_images = not retain_images
            markdown = converter.handle(str(content))
            self.logger.debug("Article converted to Markdown successfully.")
            return markdown
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Error converting article to Markdown: %s", exc)
            return f"Error converting article to Markdown: {exc}"

    @staticmethod
    def _get_text(
        soup: BeautifulSoup, selector: Optional[Dict]
    ) -> Optional[str]:
        """Return cleaned text using a selector configuration."""

        if not selector:
            return None
        element = soup.find(selector.get("tag"), class_=selector.get("class"))
        return element.get_text(strip=True) if element else None

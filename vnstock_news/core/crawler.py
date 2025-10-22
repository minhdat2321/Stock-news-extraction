"""Core synchronous crawler utilities."""

from typing import Dict, Optional

from .news import News
from vnstock_news.config.sites import SITES_CONFIG
from vnstock_news.utils import setup_logger


class Crawler:
    """Primary interface for fetching news articles from configured sources."""

    def __init__(
        self,
        site_name: Optional[str] = None,
        use_predefined_config: bool = True,
        custom_config: Optional[Dict] = None,
        debug: bool = False,
    ) -> None:
        self.logger = setup_logger(self.__class__.__name__, debug)
        self.logger.debug("Initializing Crawler...")
        self.use_predefined_config = use_predefined_config

        if use_predefined_config:
            if not site_name:
                raise ValueError(
                    "When 'use_predefined_config' is True, 'site_name' must be provided."
                )
            if site_name not in SITES_CONFIG:
                raise ValueError(
                    f"Site '{site_name}' is not supported. Choose from: {list(SITES_CONFIG.keys())}"
                )
            self.logger.info("Using predefined configuration for site: %s", site_name)
            config = SITES_CONFIG[site_name]
            self.sitemap_url = config["sitemap_url"]
            self.config = config["config"]
        else:
            self.logger.warning(
                "No predefined configuration. Using custom configuration instead."
            )
            self.sitemap_url = None
            self.config = custom_config or {}

        self.site_name = site_name
        self.parser = News(self.sitemap_url, self.config)

    def get_latest_articles(self, limit: int = 10) -> list:
        """Return the most recent articles from the configured sitemap."""

        if not self.use_predefined_config:
            raise ValueError(
                "get_latest_articles() requires predefined configuration with a sitemap URL."
            )
        if not self.sitemap_url:
            raise ValueError("No sitemap URL is defined for this site.")

        self.logger.info(
            "Fetching latest %s articles from sitemap: %s", limit, self.sitemap_url
        )
        articles = self.parser.filter_by_date()
        return articles.head(limit).to_dict("records")

    def get_article_details(
        self, url: str, custom_config: Optional[Dict] = None
    ) -> Dict:
        """Retrieve article metadata and optional Markdown content for a URL."""

        self.logger.debug("Fetching article details for URL: %s", url)
        parser = self.parser
        if not self.use_predefined_config and custom_config:
            self.logger.info("Using custom configuration for parsing.")
            parser = News(url="", config=custom_config)

        try:
            details = parser.extract_detail(url)
            details["markdown_content"] = parser.article_to_markdown(url)
            self.logger.info("Successfully fetched details for %s", url)
            return details
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Failed to fetch article details for %s: %s", url, exc)
            return {"error": str(exc)}

    def get_articles_from_feed(self, sources: list, limit_per_feed: int = 10) -> list:
        """Fetch batched articles from RSS or sitemap feeds."""

        self.logger.info(
            "Fetching articles from %s feeds with limit %s per feed.",
            len(sources),
            limit_per_feed,
        )
        from .batch import BatchCrawler

        batch = BatchCrawler(
            site_name=self.site_name,
            custom_config=self.config,
            debug=False,
        )
        result = batch.fetch_articles(
            sources=sources,
            top_n_per_feed=limit_per_feed,
            top_n=None,
        )
        return result.to_dict("records")

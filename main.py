#!/usr/bin/env python3
# news_monitor.py - Enhanced continuous news monitoring script with dedicated trending analysis
# and organized temporary/cache files in the temp_data directory

import os
import time
import asyncio
import schedule
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

# Import from reorganized package structure
from vnstock_news.api.enhanced import EnhancedNewsCrawler
from vnstock_news.utils.cleaner import ContentCleaner
from vnstock_news.utils.cache import Cache
from vnstock_news.config.sites import SITES_CONFIG
from vnstock_news.config.dynamic_config import DynamicConfig
from vnstock_news.config.sitemap_resolver import DynamicSitemapResolver
from vnstock_news.utils.logger import setup_logger

# Import the trending analyzer module
from vnstock_news.trending.analyzer import TrendingAnalyzer

# Configuration
CONFIG = {
    "interval_minutes": 15,
    "output_dir": "output/news",
    "archive_dir": "output/archive",
    "logs_dir": "logs",
    "sites_to_monitor": list(SITES_CONFIG.keys()),  # Monitor all supported sites
    "articles_per_site": 500,
    "time_window": "12h",  # Look for articles in the last 12 hours
    "cache_enabled": True,
    "cache_ttl": 3600,  # 1 hour cache
    "max_concurrency": 8,
    "clean_content": True,
    "debug": False,
    "sitemap_update_interval_hours": 24  # How often to update sitemap URLs
}

# Create necessary directories for output, logs, and temporary/cache files
os.makedirs(CONFIG["output_dir"], exist_ok=True)
os.makedirs(CONFIG["archive_dir"], exist_ok=True)
os.makedirs(CONFIG["logs_dir"], exist_ok=True)
TEMP_DATA_DIR = "temp_data"
os.makedirs(TEMP_DATA_DIR, exist_ok=True)

# Set up logging
def setup_application_logging():
    log_file = os.path.join(CONFIG["logs_dir"], f"news_monitor_{datetime.now().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("news_monitor")

logger = setup_application_logging()

# Initialize components
sitemap_resolver = DynamicSitemapResolver(debug=CONFIG["debug"])
dynamic_config = DynamicConfig(config_file="dynamic_news_config.json", debug=CONFIG["debug"])

crawler = EnhancedNewsCrawler(
    cache_enabled=CONFIG["cache_enabled"],
    cache_ttl=CONFIG["cache_ttl"],
    max_concurrency=CONFIG["max_concurrency"],
    debug=CONFIG["debug"]
)

cleaner = ContentCleaner(debug=CONFIG["debug"])

# Organize temporary/cache files in the temp_data directory
trends_cache = Cache(Cache.SQLITE, db_file=os.path.join(TEMP_DATA_DIR, "news_trends.db"), ttl=86400*7)  # 7-day cache for trends
sitemap_update_cache = Cache(Cache.SQLITE, db_file=os.path.join(TEMP_DATA_DIR, "sitemap_updates.db"), ttl=86400*30)  # Track sitemap updates

# Initialize the Trending Analyzer with the stop words file (ensure the stopwords file is in the correct location)
stop_words_path = "vnnews/config/vietnamese-stopwords.txt"
trending_analyzer = TrendingAnalyzer(stop_words_file=stop_words_path, min_token_length=3)

# Database-like storage for collected articles (stored in temp_data)
class ArticleStore:
    def __init__(self, db_file=os.path.join(TEMP_DATA_DIR, "collected_articles.db")):
        self.cache = Cache(Cache.SQLITE, db_file=db_file, ttl=86400*30)  # 30-day retention

    def add_article(self, article_dict):
        # Use URL as the key
        url = article_dict.get("url")
        if not url:
            return False
        # Store with timestamp
        article_dict["collected_at"] = datetime.now().isoformat()
        self.cache.set(url, article_dict)
        return True

    def get_article(self, url):
        return self.cache.get(url)

    def get_recent_articles(self, hours=24):
        all_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        # Scan all keys (simple method for demo purposes)
        for url in self._get_all_keys():
            article = self.cache.get(url)
            if article:
                collected_at = datetime.fromisoformat(article.get("collected_at", "2000-01-01T00:00:00"))
                if collected_at >= cutoff_time:
                    all_articles.append(article)
        return all_articles

    def _get_all_keys(self):
        return self.cache._get_all_keys() if hasattr(self.cache, "_get_all_keys") else []

# Track the latest articles we've seen to avoid duplicates
seen_articles = set()
article_stats = {
    "total_collected": 0,
    "new_this_run": 0,
    "by_site": {}
}

article_store = ArticleStore()

def update_dynamic_sitemaps():
    """Update dynamic sitemaps for sites with time-dependent URLs"""
    logger.info("Checking for sitemap updates...")
    last_update = sitemap_update_cache.get("last_sitemap_update")
    current_time = datetime.now()
    if last_update:
        hours_since_update = (current_time - datetime.fromisoformat(last_update)).total_seconds() / 3600
        if hours_since_update < CONFIG["sitemap_update_interval_hours"]:
            logger.info(f"Skipping sitemap update - last update was {hours_since_update:.1f} hours ago")
            return

    time_dependent_sites = ["tuoitre", "plo", "ktsg", "baodautu"]
    all_sites = CONFIG["sites_to_monitor"]
    updates_made = 0

    for site in time_dependent_sites:
        if site in all_sites:
            try:
                site_config = SITES_CONFIG.get(site, {})
                original_url = site_config.get("sitemap_url", "")
                if not original_url:
                    continue
                resolved_url = sitemap_resolver.resolve_sitemap_url(site, site_config)
                if resolved_url and resolved_url != original_url:
                    logger.info(f"Updating sitemap URL for {site}: {resolved_url}")
                    dynamic_config.update_sitemap_url(site, resolved_url)
                    updates_made += 1
                else:
                    logger.debug(f"No sitemap update needed for {site}")
            except Exception as e:
                logger.error(f"Error updating sitemap for {site}: {e}")

    for site in all_sites:
        if site not in time_dependent_sites:
            try:
                site_config = SITES_CONFIG.get(site, {})
                original_url = site_config.get("sitemap_url", "")
                if not original_url:
                    continue
                if any(pattern in original_url for pattern in ['-20', 'news-20']):
                    resolved_url = sitemap_resolver.resolve_sitemap_url(site, site_config)
                    if resolved_url and resolved_url != original_url:
                        logger.info(f"Updating sitemap URL for {site}: {resolved_url}")
                        dynamic_config.update_sitemap_url(site, resolved_url)
                        updates_made += 1
            except Exception as e:
                logger.error(f"Error checking sitemap for {site}: {e}")

    sitemap_update_cache.set("last_sitemap_update", current_time.isoformat())
    logger.info(f"Sitemap update check completed - {updates_made} updates made")

async def fetch_news_from_site(site_name, max_articles, time_window):
    """Fetch news from a single site using dynamic sitemap resolution"""
    logger.info(f"Fetching news from {site_name}...")
    site_config = dynamic_config.get_sites_config().get(site_name)
    if not site_config:
        logger.error(f"Site configuration not found for {site_name}")
        return pd.DataFrame()
    sources = []
    if site_config.get("rss") and site_config["rss"].get("urls"):
        sources = site_config["rss"]["urls"]
    elif site_config.get("sitemap_url"):
        sources = [site_config["sitemap_url"]]
    if not sources:
        logger.warning(f"No sources found for {site_name}")
        return pd.DataFrame()
    try:
        articles_df = await crawler.fetch_articles_async(
            sources=sources,
            site_name=site_name,
            max_articles=max_articles,
            time_frame=time_window,
            clean_content=CONFIG["clean_content"],
            sort_order="desc"
        )
        return articles_df
    except Exception as e:
        logger.error(f"Error fetching articles from {site_name}: {e}")
        return pd.DataFrame()

async def process_new_articles(articles_df, site_name):
    """Process newly fetched articles and update trending topics"""
    if articles_df.empty:
        logger.info(f"No articles found for {site_name}")
        return 0

    articles = articles_df.to_dict('records')
    new_count = 0

    for article in articles:
        article['site_name'] = site_name
        url = article.get('url')
        if url and url not in seen_articles:
            seen_articles.add(url)
            new_count += 1
            article_store.add_article(article)
            # Update trending topics using the dedicated analyzer
            text = f"{article.get('title', '')} {article.get('short_description', '')}"
            trending_analyzer.update_trends(text)
    
    article_stats["new_this_run"] += new_count
    article_stats["total_collected"] += len(articles)
    if site_name not in article_stats["by_site"]:
        article_stats["by_site"][site_name] = 0
    article_stats["by_site"][site_name] += new_count

    return new_count

def save_current_data(site_name, articles_df):
    """Save current articles to CSV"""
    if articles_df.empty:
        return
    output_file = os.path.join(CONFIG["output_dir"], f"{site_name}_news.csv")
    articles_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.debug(f"Saved {len(articles_df)} articles to {output_file}")
    archive_date = datetime.now().strftime('%Y%m%d')
    archive_dir = os.path.join(CONFIG["archive_dir"], archive_date)
    os.makedirs(archive_dir, exist_ok=True)
    archive_file = os.path.join(archive_dir, f"{site_name}_{datetime.now().strftime('%H%M')}.csv")
    articles_df.to_csv(archive_file, index=False, encoding="utf-8-sig")

def generate_report():
    """Generate a summary report of collected articles and trending topics"""
    top_trends = trending_analyzer.get_top_trends(20)
    recent_articles = article_store.get_recent_articles(hours=24)
    report = {
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_collected": article_stats["total_collected"],
            "collected_last_24h": len(recent_articles),
            "by_site": article_stats["by_site"]
        },
        "trending_topics": [{"phrase": phrase, "count": count} for phrase, count in top_trends.items()],
        "latest_run": {
            "timestamp": datetime.now().isoformat(),
            "new_articles": article_stats["new_this_run"]
        }
    }
    report_file = os.path.join(CONFIG["output_dir"], "news_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    summary_file = os.path.join(CONFIG["output_dir"], "news_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"News Monitor Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("="*50 + "\n\n")
        f.write("STATISTICS\n")
        f.write("-"*50 + "\n")
        f.write(f"Total articles collected: {article_stats['total_collected']}\n")
        f.write(f"Articles in the last 24 hours: {len(recent_articles)}\n")
        f.write(f"New articles in last run: {article_stats['new_this_run']}\n\n")
        f.write("BY SITE\n")
        f.write("-"*50 + "\n")
        for site, count in article_stats["by_site"].items():
            f.write(f"{site}: {count} articles\n")
        f.write("\nTRENDING TOPICS\n")
        f.write("-"*50 + "\n")
        for idx, (phrase, count) in enumerate(top_trends.items(), 1):
            f.write(f"{idx}. {phrase}: {count} mentions\n")
        f.write("\nSITEMAP STATUS\n")
        f.write("-"*50 + "\n")
        sites_config = dynamic_config.get_sites_config()
        for site_name in CONFIG["sites_to_monitor"]:
            site_config = sites_config.get(site_name, {})
            sitemap_url = site_config.get("sitemap_url", "N/A")
            f.write(f"{site_name}: {sitemap_url}\n")
    logger.info(f"Generated news report with {len(recent_articles)} recent articles")
    return report

async def fetch_all_news():
    """Fetch news from all monitored sites and process articles."""
    article_stats["new_this_run"] = 0
    logger.info(f"Starting news collection at {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"Monitoring {len(CONFIG['sites_to_monitor'])} sites with {CONFIG['articles_per_site']} articles per site")
    tasks = []
    for site_name in CONFIG["sites_to_monitor"]:
        task = fetch_news_from_site(
            site_name=site_name,
            max_articles=CONFIG["articles_per_site"],
            time_window=CONFIG["time_window"]
        )
        tasks.append((site_name, task))
    for site_name, task in tasks:
        try:
            articles_df = await task
            new_count = await process_new_articles(articles_df, site_name)
            logger.info(f"Processed {site_name}: {len(articles_df)} articles ({new_count} new)")
            save_current_data(site_name, articles_df)
        except Exception as e:
            logger.error(f"Error processing results for {site_name}: {e}")
    # Generate report after processing
    report = generate_report()
    logger.info(f"Completed news collection at {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"Collected {article_stats['new_this_run']} new articles this run")
    article_stats["new_this_run"] = 0

def run_news_collection():
    """Run the news collection process."""
    asyncio.run(fetch_all_news())

def daily_maintenance():
    """Perform daily maintenance tasks."""
    logger.info("Running daily maintenance...")
    update_dynamic_sitemaps()
    logger.info("Daily maintenance completed")

def main():
    logger.info("Starting news monitoring service")
    logger.info(f"Interval: {CONFIG['interval_minutes']} minutes")
    logger.info(f"Output directory: {CONFIG['output_dir']}")
    logger.info(f"Monitoring sites: {', '.join(CONFIG['sites_to_monitor'])}")
    update_dynamic_sitemaps()
    schedule.every(CONFIG["interval_minutes"]).minutes.do(run_news_collection)
    schedule.every().day.at("00:05").do(daily_maintenance)
    run_news_collection()
    logger.info("Monitoring service running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("News monitoring service stopped by user")

if __name__ == "__main__":
    main()

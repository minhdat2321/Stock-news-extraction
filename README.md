# Stock-news-extraction

Utilities for crawling and processing Viet Nam stock market news. This package exposes
both synchronous and asynchronous crawlers together with helpers for cleaning and
analyzing fetched articles.

## Installation

```bash
pip install vnstock-news
```

## Usage

```python
from vnstock_news import EnhancedNewsCrawler

crawler = EnhancedNewsCrawler()
articles = crawler.fetch_articles(["https://vnexpress.net/rss/tin-moi-nhat.rss"])
```

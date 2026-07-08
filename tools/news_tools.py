import feedparser

from config import MAX_ARTICLES_PER_FEED, STOCK_NEWS_FEEDS


def fetch_market_news() -> list[dict]:
    articles = []
    for feed_url in STOCK_NEWS_FEEDS:
        parsed = feedparser.parse(feed_url)
        source = parsed.feed.get("title", feed_url)
        for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:400],
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": source,
            })
    return articles


if __name__ == "__main__":
    for a in fetch_market_news():
        print(f"[{a['source']}] {a['title']}")
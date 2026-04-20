"""
Public data fetcher — ALL sources are free, no API keys required.

Sources:
  1. federalreserve.gov RSS  — FOMC statements, press releases, speeches
  2. FRBSF RSS               — SF Fed research and speeches
  3. Reddit public JSON API  — r/economics, r/investing, r/personalfinance, r/FedReserve
  4. News outlet RSS feeds   — CNBC, NY Times, Reuters, Washington Post, MarketWatch,
                               NPR, AP News, Financial Times, Yahoo Finance
"""

import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

TIMEOUT = 15
FED_HEADERS    = {"User-Agent": "FRBSF-AI-Comms/1.0"}
REDDIT_HEADERS = {"User-Agent": "FRBSF-AI-Comms/1.0 (research tool)"}


# ── RSS Feed URLs (all free, no auth) ─────────────────────────────────────────

FED_FEEDS = {
    "fomc_statements":  "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "press_releases":   "https://www.federalreserve.gov/feeds/press_all.xml",
    "speeches":         "https://www.federalreserve.gov/feeds/speeches.xml",
    "frbsf_research":   "https://www.frbsf.org/economic-research/publications/economic-letter/feed/",
    "frbsf_speeches":   "https://www.frbsf.org/news-and-media/speeches/feed/",
}

NEWS_FEEDS = {
    "CNBC Economy":         "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
    "CNBC Finance":         "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "CNBC Top News":        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "NY Times Economy":     "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
    "NY Times Business":    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "Reuters Business":     "https://news.google.com/rss/search?q=Reuters+Federal+Reserve+interest+rate&hl=en-US&gl=US&ceid=US:en",
    "Bloomberg Markets":    "https://news.google.com/rss/search?q=Bloomberg+FOMC+Federal+Reserve&hl=en-US&gl=US&ceid=US:en",
    "Washington Post":      "https://feeds.washingtonpost.com/rss/business",
    "MarketWatch":          "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "NPR Economy":          "https://feeds.npr.org/1006/rss.xml",
    "AP Business":          "https://news.google.com/rss/search?q=AP+News+Federal+Reserve+economy&hl=en-US&gl=US&ceid=US:en",
    "Yahoo Finance":        "https://finance.yahoo.com/news/rssindex",
    "Axios Markets":        "https://news.google.com/rss/search?q=Axios+Federal+Reserve+interest+rate+economy&hl=en-US&gl=US&ceid=US:en",
}

REDDIT_SUBREDDITS = {
    "r/economics":       "https://www.reddit.com/r/economics/search.json",
    "r/investing":       "https://www.reddit.com/r/investing/search.json",
    "r/personalfinance": "https://www.reddit.com/r/personalfinance/search.json",
    "r/FedReserve":      "https://www.reddit.com/r/FedReserve/.json",
    "r/wallstreetbets":  "https://www.reddit.com/r/wallstreetbets/search.json",
}


# ── RSS parser ────────────────────────────────────────────────────────────────

def _parse_rss(url: str, limit: int = 20) -> list[dict]:
    """Fetch and parse an RSS/Atom feed. No credentials required."""
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=FED_HEADERS)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns   = {"atom": "http://www.w3.org/2005/Atom"}
        items = []

        for item in root.findall(".//item")[:limit]:
            items.append({
                "title":       _text(item, "title"),
                "link":        _text(item, "link"),
                "description": _text(item, "description"),
                "pub_date":    _text(item, "pubDate"),
                "category":    _text(item, "category"),
            })

        if not items:
            for entry in root.findall(".//atom:entry", ns)[:limit]:
                link_el = entry.find("atom:link", ns)
                items.append({
                    "title":       _text(entry, "atom:title", ns),
                    "link":        link_el.get("href", "") if link_el is not None else "",
                    "description": _text(entry, "atom:summary", ns),
                    "pub_date":    _text(entry, "atom:updated", ns),
                    "category":    "",
                })
        return items
    except Exception as e:
        return [{"error": str(e), "source": url}]


def _text(element, tag: str, ns: dict = None) -> str:
    found = element.find(tag, ns) if ns else element.find(tag)
    return (found.text or "").strip() if found is not None and found.text else ""


# ── Fed RSS fetchers ──────────────────────────────────────────────────────────

def fetch_fomc_statements(limit: int = 10) -> list[dict]:
    items = _parse_rss(FED_FEEDS["fomc_statements"], limit=limit)
    for item in items:
        item["source_type"] = "fomc_statement"
    return items


def fetch_press_releases(limit: int = 15) -> list[dict]:
    items = _parse_rss(FED_FEEDS["press_releases"], limit=limit)
    for item in items:
        item["source_type"] = "press_release"
    return items


def fetch_speeches(limit: int = 10) -> list[dict]:
    items = _parse_rss(FED_FEEDS["speeches"], limit=limit)
    for item in items:
        item["source_type"] = "speech"
    return items


def fetch_frbsf_research(limit: int = 10) -> list[dict]:
    items = _parse_rss(FED_FEEDS["frbsf_research"], limit=limit)
    for item in items:
        item["source_type"] = "frbsf_research"
    return items


def fetch_frbsf_speeches(limit: int = 10) -> list[dict]:
    items = _parse_rss(FED_FEEDS["frbsf_speeches"], limit=limit)
    for item in items:
        item["source_type"] = "frbsf_speech"
    return items


# ── News outlet RSS fetchers (all free, no auth) ──────────────────────────────

def fetch_news_feeds(limit_per_feed: int = 10,
                     feeds: dict = None) -> list[dict]:
    """
    Fetch news from multiple RSS feeds (CNBC, NYT, Reuters, WaPo, etc.).
    All free, no API key needed.
    Returns articles normalised to the news_articles schema.
    """
    feeds = feeds or NEWS_FEEDS
    all_articles = []
    idx = 0

    for source_name, url in feeds.items():
        items = _parse_rss(url, limit=limit_per_feed)
        for item in items:
            if "error" in item:
                continue
            idx += 1
            all_articles.append({
                "id":             f"NEWS-{idx:05d}",
                "source":         source_name,
                "author":         "",
                "headline":       item.get("title", ""),
                "summary":        item.get("description", "")[:400],
                "url":            item.get("link", ""),
                "sentiment":      None,
                "sentiment_score": None,
                "topic":          _infer_topic(
                                      item.get("title", "") + " " +
                                      item.get("description", "")
                                  ),
                "published_at":   item.get("pub_date", ""),
                "data_source":    f"rss_{source_name.lower().replace(' ', '_')}",
                "source_type":    "news_article",
            })

    return all_articles


# ── Reddit (no auth) ──────────────────────────────────────────────────────────

def fetch_reddit_sentiment(query: str = "Federal Reserve interest rate FOMC",
                           subreddits: list = None,
                           limit: int = 25) -> list[dict]:
    """Public Reddit posts — no auth required."""
    if subreddits is None:
        subreddits = ["economics", "investing", "personalfinance", "FedReserve"]

    results = []
    for sub in subreddits:
        url    = f"https://www.reddit.com/r/{sub}/search.json"
        params = {"q": query, "sort": "new", "limit": min(limit, 25),
                  "restrict_sr": "true", "t": "month"}
        try:
            resp = requests.get(url, params=params,
                                headers=REDDIT_HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                p    = post.get("data", {})
                body = p.get("selftext", "") or ""
                text = f"{p.get('title', '')} {body}".strip()[:500]
                results.append({
                    "id":             f"RD-{p.get('id', '')}",
                    "platform":       "reddit",
                    "subreddit":      f"r/{sub}",
                    "author_type":    "public",
                    "author_handle":  p.get("author", "unknown"),
                    "text":           text,
                    "title":          p.get("title", ""),
                    "url":            f"https://reddit.com{p.get('permalink', '')}",
                    "sentiment":      None,
                    "sentiment_score": None,
                    "topic":          _infer_topic(text),
                    "engagement_score": p.get("score", 0),
                    "reply_count":    p.get("num_comments", 0),
                    "repost_count":   0,
                    "timestamp":      datetime.utcfromtimestamp(
                                          p.get("created_utc", 0)
                                      ).isoformat() + "Z",
                    "hashtags":       [],
                    "source":         "reddit_public",
                })
            time.sleep(0.5)
        except Exception as e:
            results.append({"error": str(e), "subreddit": sub})

    return results


def _infer_topic(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["fomc", "federal open market", "rate decision", "rate hike", "rate cut"]):
        return "fed_rate_decision"
    if any(w in t for w in ["inflation", "cpi", "pce", "price"]):
        return "inflation_data"
    if any(w in t for w in ["unemployment", "jobs", "labor", "employment"]):
        return "employment_report"
    if any(w in t for w in ["treasury", "yield", "bond", "10-year"]):
        return "treasury_yields"
    if any(w in t for w in ["mortgage", "housing", "home price"]):
        return "housing_market"
    if any(w in t for w in ["bank", "regulation", "svb", "fdic"]):
        return "bank_supervision"
    if any(w in t for w in ["powell", "chair", "speech", "testimony"]):
        return "fed_chair_speech"
    if any(w in t for w in ["gdp", "recession", "growth", "economy"]):
        return "economic_forecast"
    return "monetary_policy"

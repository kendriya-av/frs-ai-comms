"""
Data loader — merges data from multiple no-credential sources at startup:
  1. data/ folder     — locally generated JSON files (highest priority)
  2. GitHub sample data
  3. federalreserve.gov + FRBSF RSS  (no auth)
  4. News outlet RSS feeds  — CNBC, NYT, Reuters, WaPo, etc. (no auth)

No API keys are required for any data source.
"""

import json
import os
import pandas as pd
from datetime import datetime

import requests
from config import SAMPLE_DATA

_PREFIX_MAP = {
    "inquiries":          "inquiries",
    "social_media":       "social_media",
    "news_articles":      "news_articles",
    "response_templates": "response_templates",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_local_data_folder() -> dict:
    result = {k: [] for k in _PREFIX_MAP.values()}
    if not os.path.isdir(DATA_DIR):
        return {k: pd.DataFrame() for k in _PREFIX_MAP.values()}
    for fname in sorted(os.listdir(DATA_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        key = next((k for p, k in _PREFIX_MAP.items() if fname.startswith(p)), None)
        if not key:
            continue
        try:
            with open(os.path.join(DATA_DIR, fname), "r") as f:
                records = json.load(f)
            df = pd.DataFrame(records)
            if not df.empty:
                df["data_source"] = "local_generated"
                df["source_file"] = fname
                result[key].append(df)
                print(f"[Local] Loaded {len(df)} records from '{fname}' -> '{key}'")
        except Exception as e:
            print(f"[Local] Failed to load '{fname}': {e}")
    merged = {}
    for key, frames in result.items():
        if frames:
            merged[key] = pd.concat(frames, ignore_index=True)
            if "id" in merged[key].columns:
                merged[key] = merged[key].drop_duplicates(subset=["id"])
        else:
            merged[key] = pd.DataFrame()
    return merged


def load_all_sample_data() -> dict:
    data = {}
    for key, url in SAMPLE_DATA.items():
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            df = pd.DataFrame(resp.json())
            if not df.empty:
                df["data_source"] = "github"
            data[key] = df
            print(f"[GitHub] Loaded {len(df)} records for '{key}'")
        except Exception as e:
            print(f"[GitHub] Failed to load '{key}': {e}")
            data[key] = pd.DataFrame()
    return data


def load_local_json(filepath: str) -> pd.DataFrame:
    with open(filepath, "r") as f:
        return pd.DataFrame(json.load(f))


def _normalise_feeds(items: list, source_type: str) -> pd.DataFrame:
    rows = [
        {
            "id": f"{source_type.upper()}-{abs(hash(i.get('link', '')))}",
            "source": "Federal Reserve" if "fomc" in source_type or "press" in source_type else "FRBSF",
            "author": "", "headline": i.get("title", ""),
            "summary": i.get("description", "")[:400],
            "url": i.get("link", ""), "sentiment": None, "sentiment_score": None,
            "topic": "fed_rate_decision" if "fomc" in source_type else "monetary_policy",
            "published_at": i.get("pub_date", ""), "data_source": source_type,
        }
        for i in items if "error" not in i
    ]
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _merge(base: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if new.empty:
        return base
    if base.empty:
        return new
    combined = pd.concat([base, new], ignore_index=True)
    if "id" in combined.columns:
        combined = combined.drop_duplicates(subset=["id"], keep="first")
    return combined


def load_combined_data(
    include_fomc_feed: bool = True,
    include_news_feeds: bool = True,
    fomc_limit: int = 10,
    news_limit_per_feed: int = 5,
    existing_data: dict = None,
) -> dict:
    """
    Load from all no-credential sources:
      1. data/ folder
      2. GitHub sample data
      3. Fed + FRBSF RSS (no auth)
      4. News outlet RSS — CNBC, NYT, Reuters, WaPo, etc. (no auth)
    """
    from public_data_service import (
        fetch_fomc_statements, fetch_press_releases,
        fetch_frbsf_research, fetch_frbsf_speeches,
        fetch_news_feeds,
    )

    if existing_data:
        data = {k: v.copy() if isinstance(v, pd.DataFrame) else v
                for k, v in existing_data.items()}
        data_sources = list(existing_data.get("data_sources", []))
        load_summary = dict(existing_data.get("load_summary", {}))
    else:
        local   = load_local_data_folder()
        github  = load_all_sample_data()
        data    = {}
        for key in set(list(local.keys()) + list(github.keys())):
            data[key] = _merge(local.get(key, pd.DataFrame()),
                               github.get(key, pd.DataFrame()))
        local_total = sum(len(v) for v in local.values() if isinstance(v, pd.DataFrame))
        data_sources = []
        if local_total:
            data_sources.append(f"Local data/ ({local_total} records)")
        data_sources.append("GitHub sample data")
        load_summary = {
            "local_generated":     local_total,
            "github_inquiries":    len(github.get("inquiries",     pd.DataFrame())),
            "github_social_media": len(github.get("social_media",  pd.DataFrame())),
            "github_news":         len(github.get("news_articles", pd.DataFrame())),
        }

    # ── Fed RSS (no auth) ─────────────────────────────────────────────────
    if include_fomc_feed:
        try:
            print("[Live] Fetching Fed RSS feeds (no auth)...")
            items = (fetch_fomc_statements(fomc_limit) +
                     fetch_press_releases(5) +
                     fetch_frbsf_research(5) +
                     fetch_frbsf_speeches(5))
            feed_df = _normalise_feeds(items, "fomc_statement")
            n = len(feed_df)
            if n:
                data["news_articles"] = _merge(data.get("news_articles", pd.DataFrame()), feed_df)
                data_sources.append(f"Fed RSS ({n} items)")
                load_summary["fed_rss"] = n
                print(f"[Live] Fed RSS: {n} items merged")
        except Exception as e:
            print(f"[Live] Fed RSS failed: {e}")

    # ── News outlet RSS (no auth) ─────────────────────────────────────────
    if include_news_feeds:
        try:
            print("[Live] Fetching news outlet RSS feeds (no auth)...")
            articles = fetch_news_feeds(limit_per_feed=news_limit_per_feed)
            valid = [a for a in articles if "error" not in a]
            if valid:
                news_df = pd.DataFrame(valid)
                data["news_articles"] = _merge(data.get("news_articles", pd.DataFrame()), news_df)
                srcs = set(a.get("source", "") for a in valid)
                data_sources.append(f"News RSS ({len(valid)} articles from {len(srcs)} outlets)")
                load_summary["news_rss"] = len(valid)
                print(f"[Live] News RSS: {len(valid)} articles from {len(srcs)} outlets merged")
        except Exception as e:
            print(f"[Live] News RSS failed: {e}")

    data["data_sources"] = data_sources
    data["load_summary"] = load_summary
    data["loaded_at"]    = datetime.now().isoformat()

    print(f"\n[Combined] inquiries:     {len(data.get('inquiries',     pd.DataFrame()))} rows")
    print(f"[Combined] social_media:  {len(data.get('social_media',  pd.DataFrame()))} rows")
    print(f"[Combined] news_articles: {len(data.get('news_articles', pd.DataFrame()))} rows")
    print(f"[Combined] sources:       {data_sources}")

    return data

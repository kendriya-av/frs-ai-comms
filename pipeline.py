import pandas as pd
from comprehend_service import analyze_sentiment, classify_inquiry, detect_key_phrases
from bedrock_service import draft_response, generate_insights_report, identify_risks
from data_loader import load_all_sample_data, load_combined_data


def process_inquiries(df: pd.DataFrame) -> pd.DataFrame:
    """Classify and analyze sentiment for all inquiries."""
    results = []
    for _, row in df.iterrows():
        text = f"{row.get('subject', '')} {row.get('body', '')}"
        classification = classify_inquiry(text)
        sentiment = analyze_sentiment(text)
        results.append({
            **row.to_dict(),
            "ai_category": classification["category"],
            "ai_category_confidence": classification["confidence"],
            "ai_sentiment": sentiment["sentiment"],
            "ai_sentiment_scores": sentiment["scores"],
        })
    return pd.DataFrame(results)


def process_social_media(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze sentiment and key phrases for social media posts."""
    results = []
    for _, row in df.iterrows():
        text = row.get("text", "")
        sentiment = analyze_sentiment(text)
        key_phrases = detect_key_phrases(text)
        results.append({
            **row.to_dict(),
            "ai_sentiment": sentiment["sentiment"],
            "ai_sentiment_scores": sentiment["scores"],
            "ai_key_phrases": key_phrases[:5],
        })
    return pd.DataFrame(results)


def build_summary(inquiries_df: pd.DataFrame, social_df: pd.DataFrame,
                  news_df: pd.DataFrame = None,
                  data_sources: list = None,
                  load_summary: dict = None) -> dict:
    """Build a rich summary dict for the insights report, merging all data sources."""

    # ── Inquiry category breakdown ────────────────────────────────────────
    cat_col = "ai_category" if "ai_category" in inquiries_df.columns else "category"
    category_counts = {}
    category_details = {}   # per-category: count, priority split, sources, sample subjects

    if cat_col in inquiries_df.columns and not inquiries_df.empty:
        category_counts = inquiries_df[cat_col].value_counts().to_dict()

        for cat, grp in inquiries_df.groupby(cat_col):
            # Priority breakdown
            priority_split = {}
            if "priority" in grp.columns:
                priority_split = grp["priority"].value_counts().to_dict()

            # Source breakdown
            source_split = {}
            if "source" in grp.columns:
                source_split = grp["source"].value_counts().to_dict()

            # Channel breakdown
            channel_split = {}
            if "channel" in grp.columns:
                channel_split = grp["channel"].value_counts().to_dict()

            # Sample subjects (up to 3)
            sample_subjects = []
            if "subject" in grp.columns:
                sample_subjects = grp["subject"].dropna().head(3).tolist()

            # Sentiment for this category
            sent_col = "ai_sentiment" if "ai_sentiment" in grp.columns else "sentiment"
            sentiment_split = {}
            if sent_col in grp.columns:
                sentiment_split = grp[sent_col].value_counts().to_dict()

            category_details[cat] = {
                "count": len(grp),
                "priority_breakdown": priority_split,
                "source_breakdown": source_split,
                "channel_breakdown": channel_split,
                "sentiment_breakdown": sentiment_split,
                "sample_subjects": sample_subjects,
            }

    # ── Social media sentiment ────────────────────────────────────────────
    sent_col = "ai_sentiment" if "ai_sentiment" in social_df.columns else "sentiment"
    sentiment_dist = {}
    if sent_col in social_df.columns:
        sentiment_dist = social_df[sent_col].value_counts().to_dict()

    # Per-topic sentiment breakdown
    topic_sentiment = {}
    if "topic" in social_df.columns and sent_col in social_df.columns:
        for topic, grp in social_df.groupby("topic"):
            topic_sentiment[topic] = {
                "count": len(grp),
                "sentiment": grp[sent_col].value_counts().to_dict(),
                "avg_engagement": round(grp["engagement_score"].mean(), 0)
                    if "engagement_score" in grp.columns else 0,
            }

    # ── Top topics ────────────────────────────────────────────────────────
    top_topics = []
    if "topic" in social_df.columns:
        top_topics = social_df["topic"].value_counts().head(5).index.tolist()

    # ── Priority counts ───────────────────────────────────────────────────
    high_priority = medium_priority = low_priority = 0
    if "priority" in inquiries_df.columns:
        high_priority   = int((inquiries_df["priority"] == "high").sum())
        medium_priority = int((inquiries_df["priority"] == "medium").sum())
        low_priority    = int((inquiries_df["priority"] == "low").sum())

    # ── Source breakdown ──────────────────────────────────────────────────
    source_breakdown = {}
    if "source" in inquiries_df.columns:
        source_breakdown = inquiries_df["source"].value_counts().to_dict()

    # ── Risk areas (negative sentiment topics) ────────────────────────────
    risk_areas = []
    neg_col = "ai_sentiment" if "ai_sentiment" in social_df.columns else "sentiment"
    if neg_col in social_df.columns and "topic" in social_df.columns:
        neg = social_df[social_df[neg_col] == "NEGATIVE"] if "NEGATIVE" in social_df[neg_col].values \
              else social_df[social_df[neg_col] == "negative"]
        risk_areas = neg["topic"].value_counts().head(3).index.tolist()

    # ── Live news / FOMC feed context ────────────────────────────────────
    news_headlines = []
    fomc_headlines = []
    reddit_topics  = []

    if news_df is not None and not news_df.empty:
        # Recent news headlines for context
        news_headlines = news_df["headline"].dropna().head(10).tolist() \
                         if "headline" in news_df.columns else []
        # FOMC-specific items
        if "data_source" in news_df.columns:
            fomc_rows = news_df[news_df["data_source"].isin(
                ["fomc_statement", "press_release", "frbsf_research", "frbsf_speech"]
            )]
            fomc_headlines = fomc_rows["headline"].dropna().head(5).tolist()

    # Reddit-sourced topics from social_df
    if not social_df.empty and "data_source" in social_df.columns:
        reddit_rows = social_df[social_df["data_source"] == "reddit_live"]
        if not reddit_rows.empty and "topic" in reddit_rows.columns:
            reddit_topics = reddit_rows["topic"].value_counts().head(5).index.tolist()

    # Data source breakdown for transparency
    social_source_breakdown = {}
    if not social_df.empty and "data_source" in social_df.columns:
        social_source_breakdown = social_df["data_source"].value_counts().to_dict()
    elif not social_df.empty:
        social_source_breakdown = {"github": len(social_df)}

    news_source_breakdown = {}
    if news_df is not None and not news_df.empty and "data_source" in news_df.columns:
        news_source_breakdown = news_df["data_source"].value_counts().to_dict()

    return {
        "total_inquiries":        len(inquiries_df),
        "total_social_posts":     len(social_df),
        "total_news_items":       len(news_df) if news_df is not None else 0,
        "categories":             category_counts,
        "category_details":       category_details,
        "sentiment_distribution": sentiment_dist,
        "topic_sentiment":        topic_sentiment,
        "top_topics":             top_topics,
        "high_priority":          high_priority,
        "medium_priority":        medium_priority,
        "low_priority":           low_priority,
        "source_breakdown":       source_breakdown,
        "risk_areas":             risk_areas,
        # Live feed context
        "news_headlines":         news_headlines,
        "fomc_headlines":         fomc_headlines,
        "reddit_topics":          reddit_topics,
        "social_source_breakdown": social_source_breakdown,
        "news_source_breakdown":  news_source_breakdown,
        "data_sources":           data_sources or ["GitHub sample data"],
        "load_summary":           load_summary or {},
    }


def run_full_pipeline(use_live_feeds: bool = True):
    """Run the complete pipeline combining GitHub + live feed data."""
    print("Loading combined data (GitHub + live feeds)...")
    data = load_combined_data() if use_live_feeds else load_all_sample_data()

    print("\nProcessing inquiries...")
    inquiries_df = process_inquiries(data["inquiries"])

    print("\nProcessing social media (GitHub + Reddit)...")
    social_df = process_social_media(data["social_media"])

    print("\nBuilding summary...")
    summary = build_summary(
        inquiries_df,
        social_df,
        news_df=data.get("news_articles"),
        data_sources=data.get("data_sources"),
        load_summary=data.get("load_summary"),
    )

    print("\nGenerating insights report...")
    report = generate_insights_report(summary)

    print("\nIdentifying communication risks...")
    risk_texts = data["social_media"]["text"].head(10).tolist()
    risks = identify_risks(risk_texts)

    return {
        "inquiries": inquiries_df,
        "social_media": social_df,
        "summary": summary,
        "report": report,
        "risks": risks,
    }


if __name__ == "__main__":
    results = run_full_pipeline()
    print("\n=== INSIGHTS REPORT ===")
    print(results["report"])
    print("\n=== COMMUNICATION RISKS ===")
    print(results["risks"])

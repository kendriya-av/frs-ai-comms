"""
Synthetic test data generator using Amazon Bedrock (Claude).
Generates inquiries, social media posts, news articles, and response templates
that mimic real FRBSF communications data.
"""

import json
import random
from datetime import datetime, timedelta
from bedrock_service import invoke_claude

# ── Prompts ───────────────────────────────────────────────────────────────────

INQUIRY_PROMPT = """Generate {count} realistic synthetic inquiry records for the Federal Reserve Bank of San Francisco (FRBSF).
Each record must be a JSON object with these exact fields:
- id: string like "INQ-{n:05d}"
- source: one of {sources}
- channel: one of ["email", "web_form", "letter", "phone"]
- subject: realistic subject line
- body: detailed inquiry body (2-4 sentences)
- category: one of {topics}
- priority: one of ["high", "medium", "low"]
- timestamp: ISO 8601 datetime between {date_start} and {date_end}
- sender_name: realistic full name
- sender_organization: realistic organization name

Return ONLY a valid JSON array. No explanation, no markdown, no code fences."""

SOCIAL_MEDIA_PROMPT = """Generate {count} realistic synthetic social media posts about the Federal Reserve / FRBSF monetary policy.
Each record must be a JSON object with these exact fields:
- id: string like "SM-{n:05d}"
- platform: one of ["twitter", "reddit", "linkedin"]
- author_type: one of ["journalist", "financial_analyst", "economist", "public", "policy_commentator"]
- author_handle: realistic handle or name
- text: realistic post text (1-4 sentences, include hashtags for twitter)
- sentiment: one of ["positive", "negative", "neutral"]
- sentiment_score: float between -1.0 and 1.0 matching the sentiment
- topic: one of {topics}
- engagement_score: integer between 10 and 50000
- reply_count: integer
- repost_count: integer
- timestamp: ISO 8601 datetime between {date_start} and {date_end}
- hashtags: array of strings (without #)

Return ONLY a valid JSON array. No explanation, no markdown, no code fences."""

NEWS_PROMPT = """Generate {count} realistic synthetic news article summaries about the Federal Reserve / FRBSF.
Each record must be a JSON object with these exact fields:
- id: string like "NA-{n:05d}"
- source: one of ["Reuters", "Bloomberg", "Wall Street Journal", "Financial Times", "CNBC", "AP", "New York Times"]
- author: realistic journalist name
- headline: realistic news headline
- summary: 2-3 sentence article summary
- sentiment: one of ["positive", "negative", "neutral"]
- sentiment_score: float between -1.0 and 1.0
- topic: one of {topics}
- published_at: ISO 8601 datetime between {date_start} and {date_end}
- url: plausible fake URL

Return ONLY a valid JSON array. No explanation, no markdown, no code fences."""

TEMPLATE_PROMPT = """Generate {count} realistic response templates for the Federal Reserve Bank of San Francisco communications team.
Each record must be a JSON object with these exact fields:
- id: string like "RT-{n:05d}"
- inquiry_category: one of {topics}
- inquiry_example: one sentence describing the type of inquiry this template addresses
- template_subject: email subject line with {{reference_number}} placeholder
- template_body: full professional response body with placeholders like {{sender_name}}, {{inquiry_date}}, {{reference_number}}, {{specific_topic}}
- tone: one of ["formal", "empathetic", "informational", "technical"]
- placeholders: array of placeholder strings used in the template
- approval_status: "approved"
- last_updated: ISO 8601 date
- usage_count: integer between 1 and 500
- category_tags: array of relevant tag strings
- target_audience: one of ["public", "media", "stakeholder", "congressional"]

Return ONLY a valid JSON array. No explanation, no markdown, no code fences."""

# ── Config ────────────────────────────────────────────────────────────────────

DATA_TYPE_CONFIG = {
    "inquiries": {
        "prompt": INQUIRY_PROMPT,
        "default_topics": [
            "monetary_policy", "interest_rates", "inflation", "employment",
            "banking_regulation", "financial_stability", "federal_funds_rate",
            "economic_outlook", "consumer_protection", "quantitative_easing",
        ],
        "extra": {"sources": '["media", "public", "stakeholder"]'},
    },
    "social_media": {
        "prompt": SOCIAL_MEDIA_PROMPT,
        "default_topics": [
            "fed_rate_decision", "inflation_data", "employment_report", "fomc_meeting",
            "quantitative_tightening", "bank_supervision", "economic_forecast",
            "fed_chair_speech", "treasury_yields", "financial_regulation",
        ],
        "extra": {},
    },
    "news_articles": {
        "prompt": NEWS_PROMPT,
        "default_topics": [
            "monetary_policy", "interest_rates", "inflation", "employment",
            "banking_regulation", "fomc_decisions", "economic_indicators",
            "fed_communications", "global_economy", "financial_stability",
        ],
        "extra": {},
    },
    "response_templates": {
        "prompt": TEMPLATE_PROMPT,
        "default_topics": [
            "monetary_policy", "interest_rates", "inflation", "employment",
            "banking_regulation", "general_inquiry", "media_request",
            "foia_request", "congressional_inquiry", "financial_stability",
        ],
        "extra": {},
    },
}


def _parse_json_response(text: str) -> list:
    """Robustly extract a JSON array from Claude's response."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    # Find first [ and last ]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")
    return json.loads(text[start:end + 1])


def generate_data(
    data_type: str,
    count: int = 10,
    topics: list = None,
    date_start: str = "2022-01-01",
    date_end: str = "2025-12-31",
    batch_size: int = 5,
    model_id: str = None,
) -> list:
    """
    Generate synthetic data records using Bedrock.

    Args:
        data_type: one of inquiries, social_media, news_articles, response_templates
        count: total number of records to generate
        topics: list of topics to include (uses defaults if None)
        date_start: start date for timestamps
        date_end: end date for timestamps
        batch_size: records per Bedrock call (keep ≤10 for quality)

    Returns:
        List of generated records
    """
    if data_type not in DATA_TYPE_CONFIG:
        raise ValueError(f"Unknown data type: {data_type}")

    cfg = DATA_TYPE_CONFIG[data_type]
    topics = topics or cfg["default_topics"]
    prompt_template = cfg["prompt"]
    extra = cfg.get("extra", {})

    all_records = []
    offset = 0

    while offset < count:
        batch = min(batch_size, count - offset)
        prompt = prompt_template.format(
            count=batch,
            topics=json.dumps(topics),
            date_start=date_start,
            date_end=date_end,
            n=offset + 1,
            **extra,
        )
        try:
            response = invoke_claude(prompt, max_tokens=4096, model_id=model_id)
            records = _parse_json_response(response)
            # Re-index IDs to avoid duplicates across batches
            prefix_map = {
                "inquiries": "INQ",
                "social_media": "SM",
                "news_articles": "NA",
                "response_templates": "RT",
            }
            prefix = prefix_map.get(data_type, "REC")
            for i, rec in enumerate(records):
                id_field = "id"
                rec[id_field] = f"{prefix}-{offset + i + 1:05d}"
            all_records.extend(records)
            offset += batch
        except Exception as e:
            raise RuntimeError(f"Generation failed at batch offset {offset}: {e}")

    return all_records[:count]

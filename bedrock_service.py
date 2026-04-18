import json
import boto3
from config import AWS_REGION, AWS_PROFILE, BEDROCK_MODEL_ID
from response_templates import get_template
from audit_log import log_action

# Available Bedrock Claude models (id -> display label)
AVAILABLE_MODELS = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "Claude 3.5 Sonnet v2 (Latest)",
    "anthropic.claude-3-5-haiku-20241022-v1:0":  "Claude 3.5 Haiku (Fast)",
    "anthropic.claude-3-sonnet-20240229-v1:0":   "Claude 3 Sonnet",
    "anthropic.claude-3-haiku-20240307-v1:0":    "Claude 3 Haiku (Fastest)",
    "anthropic.claude-3-opus-20240229-v1:0":     "Claude 3 Opus (Most Capable)",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": "Claude 3.5 Sonnet v2 (US cross-region)",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0":  "Claude 3.5 Haiku (US cross-region)",
}


def get_client():
    if AWS_PROFILE:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    else:
        session = boto3.Session(region_name=AWS_REGION)
    return session.client("bedrock-runtime", region_name=AWS_REGION)


def resolve_model(model_id: str = None) -> str:
    """Return model_id if provided, otherwise fall back to env/config value."""
    return model_id if model_id else BEDROCK_MODEL_ID


def invoke_claude(prompt: str, max_tokens: int = 1024, model_id: str = None,
                  action_label: str = "llm_call") -> str:
    """Invoke Claude via Bedrock and return the response text."""
    client = get_client()
    model = resolve_model(model_id)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = client.invoke_model(
        modelId=model,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    text = result["content"][0]["text"]

    # Audit log
    log_action(
        action=action_label,
        model_id=model,
        input_summary=prompt[:200],
        output_summary=text[:200],
    )
    return text


def draft_response(inquiry: dict, template: str = None, model_id: str = None) -> str:
    """
    Generate a draft response for an inquiry using Bedrock.
    Automatically selects the correct category+audience template unless one is explicitly passed.
    """
    category = inquiry.get("category", "other")
    audience = inquiry.get("source", "public")   # source maps to audience

    # Resolve template: explicit override > built-in registry > none
    if template:
        template_block = f"Use this approved template as your structural guide:\n\n{template}"
        tone_guidance  = ""
    else:
        tmpl = get_template(category, audience)
        if tmpl:
            template_block = (
                f"Use the following approved response template as your structural guide.\n"
                f"Fill in all {{{{placeholder}}}} values from the inquiry context.\n\n"
                f"--- TEMPLATE START ---\n"
                f"Subject: {tmpl['subject']}\n\n"
                f"{tmpl['body']}\n"
                f"--- TEMPLATE END ---"
            )
            tone_guidance = (
                f"\nTone: {tmpl['tone']}"
                f"\nGuidance: {tmpl['guidance']}"
            )
        else:
            template_block = ""
            tone_guidance  = ""

    context = f"""You are a communications officer at the Federal Reserve Bank of San Francisco.
Draft a professional response to the following inquiry.

Inquiry Details:
- Source / Audience: {audience}
- Category: {category}
- Subject: {inquiry.get('subject', '')}
- Body: {inquiry.get('body', '')}
{tone_guidance}

{template_block}

Instructions:
- Follow the template structure exactly.
- Replace all {{{{placeholder}}}} values with appropriate content inferred from the inquiry.
- Use {{{{sender_name}}}}, {{{{reference_number}}}}, {{{{inquiry_date}}}}, {{{{officer_name}}}}, {{{{department}}}} as literal placeholders where the template uses them — do not invent values.
- Match the tone appropriate for a {audience} audience.
- Do not add sections not present in the template.
- Output only the final email — no preamble, no explanation."""

    return invoke_claude(context, max_tokens=1500, model_id=model_id,
                         action_label="draft_response")


def generate_insights_report(summary_data: dict, model_id: str = None) -> str:
    """Generate a detailed communication insights report using Bedrock."""

    # Build per-category detail block
    cat_details_text = ""
    for cat, detail in summary_data.get("category_details", {}).items():
        cat_details_text += f"\n  [{cat.replace('_', ' ').upper()}]\n"
        cat_details_text += f"    - Total inquiries: {detail['count']}\n"
        if detail.get("priority_breakdown"):
            cat_details_text += f"    - Priority: {detail['priority_breakdown']}\n"
        if detail.get("source_breakdown"):
            cat_details_text += f"    - Sources: {detail['source_breakdown']}\n"
        if detail.get("channel_breakdown"):
            cat_details_text += f"    - Channels: {detail['channel_breakdown']}\n"
        if detail.get("sentiment_breakdown"):
            cat_details_text += f"    - Sentiment: {detail['sentiment_breakdown']}\n"
        if detail.get("sample_subjects"):
            subjects = "; ".join(f'"{s}"' for s in detail["sample_subjects"])
            cat_details_text += f"    - Sample subjects: {subjects}\n"

    # Build per-topic social media block
    topic_text = ""
    for topic, tdata in summary_data.get("topic_sentiment", {}).items():
        topic_text += (
            f"\n  [{topic.replace('_', ' ').upper()}]  "
            f"Posts: {tdata['count']}  |  "
            f"Avg engagement: {tdata['avg_engagement']}  |  "
            f"Sentiment: {tdata['sentiment']}\n"
        )

    prompt = f"""You are a senior communications analyst at the Federal Reserve Bank of San Francisco.
Generate a comprehensive, structured insights report based on the data below.

=== DATA SOURCES ===
Sources contributing to this analysis: {', '.join(summary_data.get('data_sources', ['GitHub sample data']))}
Load summary: {summary_data.get('load_summary', {})}

=== INQUIRY DATA ===
Total Inquiries: {summary_data.get('total_inquiries', 0)}
Priority Breakdown: High={summary_data.get('high_priority', 0)}, Medium={summary_data.get('medium_priority', 0)}, Low={summary_data.get('low_priority', 0)}
Source Breakdown: {summary_data.get('source_breakdown', {})}
Category Overview: {summary_data.get('categories', {})}

Per-Category Details:
{cat_details_text if cat_details_text else "  No category data available."}

=== SOCIAL MEDIA & PUBLIC SENTIMENT ===
Total Posts Monitored: {summary_data.get('total_social_posts', 0)}
Sources: {summary_data.get('social_source_breakdown', {})}
Overall Sentiment Distribution: {summary_data.get('sentiment_distribution', {})}
Top 5 Topics: {summary_data.get('top_topics', [])}
Reddit-Trending Topics: {summary_data.get('reddit_topics', [])}
Identified Risk Areas (high negative sentiment): {summary_data.get('risk_areas', [])}

Per-Topic Breakdown:
{topic_text if topic_text else "  No topic data available."}

=== NEWS & OFFICIAL FEEDS ===
Total News/Feed Items: {summary_data.get('total_news_items', 0)}
News Sources: {summary_data.get('news_source_breakdown', {})}
Recent Headlines:
{chr(10).join(f"  - {h}" for h in summary_data.get('news_headlines', [])[:8]) or "  None available."}

Recent FOMC/Official Statements:
{chr(10).join(f"  - {h}" for h in summary_data.get('fomc_headlines', [])[:5]) or "  None available."}

=== REPORT REQUIREMENTS ===
Generate a professional report with the following sections. Be specific — reference actual category names, counts, topics, and headlines from the data above.

## 1. Executive Summary
2-3 sentences covering the overall communication landscape across all data sources.

## 2. Inquiry Analysis by Category
For EACH category present in the data, provide:
- Volume and share of total
- Priority and source breakdown
- Dominant sentiment
- Key themes from sample subjects
- Recommended handling approach

## 3. Public Sentiment Analysis
- Overall sentiment trend across social media and Reddit
- Top topics driving public conversation
- Engagement highlights and platform breakdown
- Notable shifts or spikes

## 4. News & Official Feed Context
- Key themes from recent news headlines
- Latest FOMC/official communications context
- How official messaging aligns or contrasts with public sentiment

## 5. Communication Risk Assessment
- Specific risk areas identified
- Topics with highest negative sentiment and engagement
- Urgency rating (High / Medium / Low) for each risk

## 6. Recommended Actions
Concrete, prioritised action items for the communications team.

## 7. Key Metrics Summary
A brief bullet list of the most important numbers from this report."""

    return invoke_claude(prompt, max_tokens=3000, model_id=model_id,
                         action_label="insights_report")


def identify_risks(texts: list, model_id: str = None) -> list:
    """Identify potential communication risks from a list of texts."""
    combined = "\n---\n".join(texts[:10])
    prompt = f"""Review the following public communications about the Federal Reserve.
Identify any potential communication risks, misinformation, or topics requiring urgent response.

Communications:
{combined}

List the top risks in bullet points with a brief explanation for each."""

    return invoke_claude(prompt, model_id=model_id,
                         action_label="risk_detection")

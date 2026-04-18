import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "")  # empty = use IAM role (on AWS) or default creds
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# Sample data URLs from GitHub
SAMPLE_DATA = {
    "inquiries": "https://raw.githubusercontent.com/tjblavakumar/general_share/main/output/inquiries.json",
    "social_media": "https://raw.githubusercontent.com/tjblavakumar/general_share/main/output/social_media_20260409_103503.json",
    "news_articles": "https://raw.githubusercontent.com/tjblavakumar/general_share/main/output/news_articles_20260409_105055.json",
    "response_templates": "https://raw.githubusercontent.com/tjblavakumar/general_share/main/output/response_templates_20260409_105313.json",
}

# Inquiry categories for classification
INQUIRY_CATEGORIES = [
    "monetary_policy",
    "interest_rates",
    "banking_regulation",
    "employment",
    "inflation",
    "federal_funds_rate",
    "media_request",
    "public_inquiry",
    "stakeholder_inquiry",
    "other",
]

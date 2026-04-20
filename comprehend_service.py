import boto3
from config import AWS_REGION, AWS_PROFILE, INQUIRY_CATEGORIES


def get_client():
    if AWS_PROFILE:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    else:
        session = boto3.Session(region_name=AWS_REGION)
    return session.client("comprehend")


def analyze_sentiment(text: str) -> dict:
    """Run sentiment analysis on a single text."""
    client = get_client()
    response = client.detect_sentiment(Text=text[:4900], LanguageCode="en")
    return {
        "sentiment": response["Sentiment"],
        "scores": response["SentimentScore"],
    }


def detect_entities(text: str) -> list:
    """Extract named entities from text."""
    client = get_client()
    response = client.detect_entities(Text=text[:4900], LanguageCode="en")
    return [
        {"text": e["Text"], "type": e["Type"], "score": round(e["Score"], 3)}
        for e in response["Entities"]
    ]


def detect_key_phrases(text: str) -> list:
    """Extract key phrases from text."""
    client = get_client()
    response = client.detect_key_phrases(Text=text[:4900], LanguageCode="en")
    return [p["Text"] for p in response["KeyPhrases"]]


def classify_inquiry(text: str, endpoint_arn: str = None) -> dict:
    """
    Classify inquiry using Comprehend custom classifier.
    Falls back to keyword-based classification if no endpoint is configured.
    """
    if endpoint_arn:
        client = get_client()
        response = client.classify_document(Text=text[:4900], EndpointArn=endpoint_arn)
        top = max(response["Classes"], key=lambda x: x["Score"])
        return {"category": top["Name"], "confidence": round(top["Score"], 3)}

    # Keyword-based fallback
    text_lower = text.lower()
    keyword_map = {
        "monetary_policy": ["monetary policy", "fomc", "federal reserve", "rate decision"],
        "interest_rates": ["interest rate", "federal funds rate", "rate hike", "rate cut", "mortgage rate"],
        "banking_regulation": ["regulation", "basel", "capital requirement", "supervisory", "compliance"],
        "employment": ["employment", "labor market", "jobs", "unemployment", "wage"],
        "inflation": ["inflation", "cpi", "pce", "price stability", "deflation"],
        "media_request": ["press inquiry", "journalist", "reporter", "interview", "media"],
    }
    for category, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            return {"category": category, "confidence": 0.75}
    return {"category": "other", "confidence": 0.5}


def batch_analyze_sentiment(texts: list) -> list:
    """Batch sentiment analysis (up to 25 items per call)."""
    client = get_client()
    results = []
    for i in range(0, len(texts), 25):
        batch = [{"Index": j, "Text": t[:4900]} for j, t in enumerate(texts[i:i+25])]
        response = client.batch_detect_sentiment(TextList=[b["Text"] for b in batch], LanguageCode="en")
        for item in response["ResultList"]:
            results.append({
                "sentiment": item["Sentiment"],
                "scores": item["SentimentScore"],
            })
    return results

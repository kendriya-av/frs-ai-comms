# FRS AI Communications System

AI-powered system for the Federal Reserve Bank of San Francisco External Communications department.

## Features
- **Inquiry Classification** — Categorizes incoming communications using Amazon Comprehend
- **Sentiment Analysis** — Analyzes social media, Reddit, and news sentiment across all sources
- **Response Drafting** — Generates draft responses using Amazon Bedrock (Claude) with category-specific templates
- **Risk Detection** — Identifies trending topics and communication risks across all data sources
- **Insights Reports** — Generates executive-level reports combining all data sources
- **Live Fed Data** — Fetches real-time data from federalreserve.gov, Reddit, NewsAPI, and FRED
- **Test Data Generator** — Generates synthetic FRBSF communications data via Bedrock

## Data Sources

### Used by default (no credentials required)

| Source | What it provides |
|---|---|
| GitHub sample data | Synthetic inquiries, social media, news, templates |
| federalreserve.gov RSS | FOMC statements, press releases, speeches |
| FRBSF RSS | SF Fed research, speeches |
| Reddit public API | r/economics, r/investing, r/personalfinance, r/FedReserve |

### Optional (Live Fed Data UI tab only — require API keys)

| Source | What it provides | Key |
|---|---|---|
| NewsAPI.org | News articles from Reuters, Bloomberg, AP, WSJ | `NEWS_API_KEY` |
| FRED API | FEDFUNDS, CPI, PCE, UNRATE, GDP, Treasury yields | `FRED_API_KEY` |

The optional sources are **never used in the default analysis pipeline**. They are only available in the Live Fed Data page when keys are configured.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
cp .env.example .env
# Edit .env with your values
```

3. `.env` keys:
```
AWS_REGION=us-east-1
AWS_PROFILE=your-sso-profile
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
FRED_API_KEY=          # free at fred.stlouisfed.org/docs/api/api_key.html
NEWS_API_KEY=          # free at newsapi.org
```

4. Log in to AWS SSO:
```bash
aws sso login --profile your-sso-profile
```

## Run the App
```bash
cd frs_ai_comms
python app.py
```
Then open http://localhost:8050

## Run the Pipeline (CLI)
```bash
cd frs_ai_comms
python pipeline.py
```

## AWS Permissions Required
- `comprehend:DetectSentiment`
- `comprehend:DetectEntities`
- `comprehend:DetectKeyPhrases`
- `bedrock:InvokeModel`

## Project Structure
```
frs_ai_comms/
├── app.py                  # Dash UI (10 pages)
├── pipeline.py             # End-to-end processing pipeline
├── data_loader.py          # GitHub + live feed data loading & merging
├── public_data_service.py  # Fed RSS, Reddit, NewsAPI, FRED fetchers
├── comprehend_service.py   # Amazon Comprehend wrapper
├── bedrock_service.py      # Amazon Bedrock (Claude) wrapper
├── datagen_service.py      # Synthetic data generator
├── response_templates.py   # Per-category response templates
├── config.py               # Configuration and constants
├── data/                   # Generated test data (auto-saved)
├── requirements.txt
└── .env.example
```

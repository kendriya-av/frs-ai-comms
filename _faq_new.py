def faq_page():
    """Comprehensive FAQ highlighting every page, how sections work, how values are calculated, and recent changes."""

    def _faq_section(icon, title, items):
        """Render a collapsible FAQ section for a page."""
        return card([
            html.Div([
                html.Span(icon, style={"fontSize": "20px", "marginRight": "10px"}),
                html.Span(title, style={"fontWeight": "700", "fontSize": "15px",
                                        "color": COLORS["navy"]}),
            ], style={"marginBottom": "14px"}),
            html.Div([
                html.Div([
                    html.P(q, style={"fontWeight": "600", "fontSize": "13px",
                                     "color": COLORS["navy"], "marginBottom": "4px"}),
                    html.P(a, style={"fontSize": "13px", "color": COLORS["text"],
                                     "lineHeight": "1.6", "marginBottom": "14px",
                                     "paddingLeft": "12px",
                                     "borderLeft": f"2px solid {COLORS['border']}"}),
                ]) for q, a in items
            ]),
        ], style={"marginBottom": "16px"})

    return html.Div([
        page_header("FAQ & Help",
                    "How each page works, what the sections represent, how values are calculated, and recent changes"),

        # ── Recent Changes ────────────────────────────────────────────────
        _faq_section("🔄", "Recent Changes (April 2026)", [
            ("What changed on April 18?",
             "Reddit Sentiment was removed (not allowed by Fed policy). Live Fed Data validated for sentiment updates "
             "after Fetch Now. AI Draft response now supports template selection by category and audience. "
             "Insights Report and Sentiment Analysis social posts update correctly after data upload. "
             "Word cloud renamed from 'Trending Topics' to 'Fed in News' with improved keyword filtering. "
             "Guardrail added: 'Model ensures no policy predictions made and no financial advice is provided.'"),
            ("What changed on April 17?",
             "Trust & Safety: Responsible AI confidence metrics made responsive with auto-refresh every 10 seconds. "
             "Communications Hub: Trending Topics moved left, Sentiment Analysis moved under Risk Alerts as donut chart. "
             "Chart colors unified across all bar and pie charts. ROI Calculator defaults set to pragmatic values. "
             "Generate Test Data and Scoring & AI Info pages greyed out in nav (developer/test features). "
             "Sentiment by Outlet: added time-period trending (daily, weekly, monthly, quarterly, annually)."),
            ("What changed on April 16?",
             "ROI Calculator added. Report Generator (Insights Report with multi-format export) added. "
             "Communications Hub created as consolidated dashboard. Sentiment Analysis merged news feed and social media tabs. "
             "Upload functionality fixed. Executive summary enhanced to include all data points, trending topics, "
             "word cloud, and deeper AI insights. Audit Log section added. AI Model Config page added."),
        ]),

        # ── Overview ──────────────────────────────────────────────────────
        _faq_section("🏠", "Overview", [
            ("What does the Overview page show?",
             "A high-level summary of the system: the problem statement (manual communications bottleneck), "
             "the AI-powered solution, KPI metric cards (total inquiries, social posts, news items, data sources), "
             "inquiry breakdown charts, sentiment summary, feature cards linking to each module, "
             "the AWS architecture diagram, AI pipeline flow visualization, and Responsible AI notices."),
            ("What AWS services power this system?",
             "Amazon Comprehend (NLP — sentiment analysis, entity extraction, key phrase detection, text classification), "
             "Amazon Bedrock with Claude (LLM — response drafting, insights reports, risk detection, synthetic data generation), "
             "AWS App Runner (container hosting), Amazon ECR (image registry), AWS CodeBuild (CI/CD), "
             "Amazon S3 (source artifacts), and AWS IAM for authentication."),
            ("How many pages does the application have?",
             "15 pages: Overview, Communications Hub, Inquiry & Response, Sentiment Monitor, Insights Report, "
             "Risk Detector, ROI Calculator, Live Fed Data, Upload Data, Audit Log, Trust & Safety, "
             "AI Model Config, Generate Test Data, Scoring & AI Info, and FAQ & Help."),
        ]),

        # ── Communications Hub ────────────────────────────────────────────
        _faq_section("💬", "Communications Hub", [
            ("What does the Communications Hub show?",
             "A single-screen dashboard with: Trending Topics bar chart (left, showing top 12 topics by volume), "
             "Risk & Negative Sentiment Alerts (right, top 3 negative-sentiment topics), "
             "Sentiment Analysis as a donut chart (moved under Risk Alerts per April 17 update), "
             "and summary metric cards (Inquiries, Social Posts, News Items, Sources)."),
            ("How are Trending Topics calculated?",
             "Topics are extracted from the 'topic' field of social media posts. The top 12 topics by volume are displayed "
             "as a horizontal bar chart, ranked by post count. More than 6 lines of topics are now supported."),
            ("How does the Sentiment Donut work?",
             "It aggregates the 'sentiment' field across all social media posts into positive/negative/neutral/mixed categories "
             "and displays them as a donut (pie with hole) chart. Colors are unified across all charts: "
             "green=#2E7D32 (positive), red=#C62828 (negative), navy=#1B2A4A (neutral), orange=#E65100 (mixed)."),
            ("How are Risk Alerts generated?",
             "The system filters social media posts with sentiment='negative', groups them by topic, and shows the top 3 "
             "topics with the highest count of negative posts."),
            ("What was removed from the Communications Hub?",
             "The Inquiry Viewer and AI Draft Response sections were removed per April 18 requirements. "
             "These features are now exclusively on the Inquiry & Response page."),
        ]),

        # ── Inquiry & Response ────────────────────────────────────────────
        _faq_section("📥", "Inquiry & Response", [
            ("What is the Inquiry Queue?",
             "A filterable list of all loaded inquiries. Each inquiry shows its ID, source, channel, subject, sender, "
             "category badge, and priority badge. Filters are available for category, priority, and source. "
             "Click any inquiry to see its full detail and AI-generated draft response."),
            ("How does classification work?",
             "Amazon Comprehend analyzes the inquiry text to determine category (monetary_policy, interest_rates, "
             "banking_regulation, employment, inflation, federal_funds_rate, media_request, public_inquiry, "
             "stakeholder_inquiry, other), sentiment (positive/negative/neutral/mixed), and confidence score (0–100%). "
             "A keyword-based fallback classifier is used when Comprehend custom endpoint is not deployed."),
            ("What does the Classify All button do?",
             "It re-runs Amazon Comprehend classification on every inquiry in the dataset, updating ai_category, "
             "ai_confidence, and ai_sentiment fields. The inquiry list refreshes automatically after completion."),
            ("How are draft responses generated?",
             "Amazon Bedrock (Claude) generates a response using the inquiry's category, source/audience, subject, and body. "
             "You can now select a specific template by choosing a category and audience (public/media/stakeholder). "
             "30+ approved templates cover all category × audience combinations with tone guidance and placeholder support. "
             "Templates include subject lines, body text, tone instructions, and guidance notes."),
            ("Can I re-draft with a different audience?",
             "Yes. The detail panel includes an audience override dropdown. Select a different audience "
             "(public, media, or stakeholder) and click Re-draft to generate a new response using the appropriate template."),
            ("What is the Smart Inbox?",
             "An auto-clustering feature that groups inquiries by (source, category) pairs and shows the top 6 clusters "
             "with their counts, giving a quick overview of inquiry distribution."),
        ]),

        # ── Sentiment Monitor ─────────────────────────────────────────────
        _faq_section("📊", "Sentiment Monitor", [
            ("What data feeds into Sentiment Monitor?",
             "Social media posts and news articles are merged into one consolidated view. Sources include "
             "CNBC, Bloomberg, Axios, Wall Street Journal, Federal Reserve RSS, FRBSF, NY Times, Reuters, "
             "Washington Post, MarketWatch, NPR, AP News, Yahoo Finance, and more (13+ outlets total). "
             "Reddit sentiment was removed per Fed policy (April 18)."),
            ("How is sentiment assigned?",
             "Items with a pre-existing sentiment field (from Comprehend or data generation) keep their value. Items without "
             "sentiment get a keyword-based assignment: words like 'surge', 'rally', 'growth' → positive; 'crash', 'crisis', "
             "'fear' → negative; otherwise → neutral."),
            ("What does 'Sentiment by Outlet' show?",
             "A stacked bar chart showing positive/negative/neutral/mixed counts per news outlet or social platform, "
             "so you can see which outlets skew positive or negative. Chart colors are now unified across all visualizations."),
            ("How does the Sentiment Trend Over Time chart work?",
             "It groups all social media and news items by their date field, resampled at the selected period: "
             "Daily, Weekly, Monthly, Quarterly, or Annually. Each sentiment category is plotted as a separate line, "
             "showing how sentiment volume changes over time. For example, you can see that negative sentiment was 10 "
             "in February, 25 in March, and 35 in April. This helps the Comms team spot rising negative sentiment early "
             "and track trends across any time horizon."),
            ("What is the Topic Distribution chart?",
             "A pie chart showing the proportion of posts/articles per topic across all data."),
        ]),

        # ── Insights Report ───────────────────────────────────────────────
        _faq_section("📈", "Insights Report", [
            ("What does the Insights Report generate?",
             "An AI-generated executive report using Amazon Bedrock (Claude). It summarizes all loaded data — inquiries, "
             "social media, and news — into a 7-section narrative: Executive Summary, Inquiry Analysis by Category, "
             "Public Sentiment Analysis, News & Official Feed Context, Communication Risk Assessment, "
             "Recommended Actions, and Key Metrics Summary."),
            ("How does the date filter work?",
             "The Date From and Date To pickers filter inquiries, social media, and news articles by their date/timestamp "
             "field before generating the report. Only records within the selected range are included in the analysis."),
            ("What is 'Fed in News' (Word Cloud)?",
             "A word cloud generated from all text across inquiries (subject + body), social media (text), and news "
             "(headline + summary). Common stopwords and Fed-specific terms (Fed, Federal, Reserve, Bank, etc.) are filtered "
             "out so the cloud highlights meaningful trending keywords. Renamed from 'Trending Topics' per April 18 update."),
            ("How are Trending Topics tinted by sentiment?",
             "For each topic, the system calculates net sentiment = (positive count − negative count) / total count. "
             "Topics with net > 0.2 are green (positive trend), < −0.2 are red (negative trend), otherwise navy (neutral). "
             "An arrow indicator (↑/↓/→) and percentage are shown on each bar."),
            ("What export formats are available?",
             "Reports can be downloaded in four formats: Markdown (.md), HTML (.html), DOCX (.docx), and PDF (.pdf). "
             "Each format preserves the full report structure and formatting."),
            ("How does the report include social media data?",
             "Social posts from Insights Report and Sentiment Analysis now update correctly after data upload "
             "(fixed in April 18 update). The report includes per-topic sentiment breakdown, engagement metrics, "
             "and platform distribution."),
        ]),

        # ── Risk Detector ─────────────────────────────────────────────────
        _faq_section("⚠️", "Risk Detector", [
            ("How does risk detection work?",
             "Amazon Bedrock (Claude) analyzes a sample of social media posts (configurable: 5–20) and identifies "
             "trending negative topics, misinformation risks, and urgent communication issues. It returns a structured "
             "risk report with severity levels (High/Medium/Low) and recommended actions."),
            ("What is the High-Risk Posts table?",
             "Posts with sentiment_score < −0.5 are filtered and ranked by engagement_score. The top 5 highest-engagement "
             "negative posts are displayed, as these represent the greatest communication risk."),
        ]),

        # ── ROI Calculator ────────────────────────────────────────────────
        _faq_section("💰", "ROI Calculator", [
            ("How is ROI calculated?",
             "The calculator compares manual process costs vs. AI-assisted costs. Manual cost = "
             "(inquiries × classify_time + inquiries × draft_time) × hourly_rate/60 + report_hours × 4 × hourly_rate per month. "
             "AI cost = real AWS resource costs (App Runner, Bedrock tokens, Comprehend units, ECR storage, CodeBuild)."),
            ("What are the AWS cost components?",
             "App Runner (~$25/mo for 1 vCPU, 2GB), Bedrock Claude ($0.003/1K input tokens, $0.015/1K output tokens), "
             "Comprehend ($0.0001/unit of 100 chars), ECR ($0.10/GB/month), CodeBuild ($0.005/build-minute). "
             "These are real AWS pricing defaults that can be adjusted via sliders."),
            ("What are the default pragmatic values?",
             "200 inquiries/month, 3 min to classify manually, 20 min to draft manually, 4 hrs/week for sentiment reports, "
             "$65/hr staff cost. These represent realistic FRBSF communications workload estimates "
             "(updated to pragmatic defaults per April 17 requirements)."),
        ]),

        # ── Live Fed Data ─────────────────────────────────────────────────
        _faq_section("🌐", "Live Fed Data", [
            ("What data sources are used?",
             "Free RSS feeds only — no API keys required. Federal Reserve sources: FOMC statements, press releases, "
             "speeches, FRBSF research, FRBSF speeches. News outlets (13+): CNBC (Economy, Finance, Top News), "
             "NY Times (Economy, Business), Reuters, Bloomberg, Washington Post, MarketWatch, NPR, AP News, "
             "Yahoo Finance, and Axios. All fetched via HTTP/RSS."),
            ("Was Reddit removed?",
             "Yes. Reddit Sentiment was removed per Fed policy (April 18). The public_data_service.py still contains "
             "the Reddit fetcher code but it is no longer called from the Live Fed Data page."),
            ("How does Fetch Now work?",
             "Clicking Fetch Now pulls the latest items from the selected RSS feed, runs them through the sentiment pipeline "
             "(keyword-based classification + optional Comprehend), and merges them into the app's data. "
             "Total items, news articles, and sentiment counts update automatically. "
             "Validated in April 18 that sentiments update correctly after Fetch Now."),
            ("What tabs are available?",
             "Four tabs: FOMC Statements, Press Releases, Speeches, and News Feeds. The News Feeds tab allows "
             "selecting specific outlets and setting item limits per feed."),
        ]),

        # ── Upload Data ───────────────────────────────────────────────────
        _faq_section("📂", "Upload Data", [
            ("What file formats are supported?",
             "JSON files. The data should contain records matching the expected schema for the selected data type: "
             "inquiries, social_media, or news_articles."),
            ("How does uploaded data integrate?",
             "Uploaded records are merged with existing data. New records get re-indexed IDs to avoid collisions with "
             "existing data. All pages (Inquiry Queue, Sentiment Monitor, Insights Report, Communications Hub, etc.) "
             "automatically reflect the new data including social media posts."),
        ]),

        # ── Audit Log ─────────────────────────────────────────────────────
        _faq_section("📋", "Audit Log", [
            ("What is logged?",
             "Every AI action: draft responses, insights reports, risk detections, classifications, and synthetic data generation. "
             "Each entry records timestamp, action type, model ID used, input summary (first 200 chars), "
             "and output summary (first 200 chars) for full traceability."),
            ("Where is the log stored?",
             "In a local JSON file (data/audit_log.json). The log is loaded on app startup and auto-saved after each action. "
             "In production, this would integrate with AWS CloudWatch Logs."),
            ("What metrics are shown?",
             "Total actions, draft responses count, insights reports count, risk detections count, other calls count, "
             "and number of distinct models used."),
        ]),

        # ── Trust & Safety ────────────────────────────────────────────────
        _faq_section("🛡️", "Trust & Safety", [
            ("What does the Responsible AI Posture show?",
             "Live AWS service status (Bedrock, Comprehend, S3, CloudWatch, Secrets Manager) with active/fallback indicators, "
             "classification confidence distribution (High ≥90%, Medium 70–90%, Low <70%), "
             "9 active guardrails with details, and audit trail health metrics."),
            ("How is confidence distribution calculated?",
             "Each inquiry's ai_confidence value (from Comprehend or keyword classifier) is bucketed into High (≥90%), "
             "Medium (70–90%), or Low (<70%). The distribution auto-refreshes every 10 seconds via a callback, "
             "reflecting any new data uploads or classifications (made responsive per April 17 update)."),
            ("What are the 9 active guardrails?",
             "1) Human-in-the-loop — no auto-send path exists. "
             "2) Closed label set — classifier refuses unknown categories. "
             "3) Prompt templating — user input never concatenated into prompts. "
             "4) Template-guided output — responses follow 30+ approved templates. "
             "5) Confidence thresholds — low confidence triggers mandatory human review. "
             "6) Audit trail — every AI action logged with model ID. "
             "7) Bias disclosure — sentiment models may reflect training bias. "
             "8) No PII processing — system does not store personal data. "
             "9) No policy predictions — model ensures no monetary policy predictions made and no financial advice provided "
             "(added per April 18 requirements)."),
        ]),

        # ── AI Model Config ───────────────────────────────────────────────
        _faq_section("🤖", "AI Model Config", [
            ("How do I change the AI model?",
             "Select a model from the dropdown on the AI Model Config page and click Save. The selected model is stored "
             "in browser session storage and used for all subsequent Bedrock calls (drafting, insights, risk detection, "
             "data generation). Leave blank to use the model defined in your .env file."),
            ("What models are available?",
             "7 Claude models via Amazon Bedrock: "
             "Claude 3.5 Sonnet v2 (Latest), Claude 3.5 Haiku (Fast), Claude 3 Sonnet, Claude 3 Haiku (Fastest), "
             "Claude 3 Opus (Most Capable), Claude 3.5 Sonnet v2 (US cross-region), and Claude 3.5 Haiku (US cross-region). "
             "If no model is selected, the system falls back to the BEDROCK_MODEL_ID environment variable "
             "(default: anthropic.claude-3-sonnet-20240229-v1:0)."),
        ]),

        # ── Generate Test Data ────────────────────────────────────────────
        _faq_section("🧪", "Generate Test Data", [
            ("What does this page do?",
             "Uses Amazon Bedrock (Claude) to generate realistic synthetic FRBSF communications data. "
             "This is a developer/test feature (greyed out in navigation) used for demos and testing."),
            ("What data types can be generated?",
             "Four types: Inquiries (with source, channel, category, priority, sender info), "
             "Social Media Posts (with platform, sentiment, engagement, hashtags), "
             "News Articles (with source, headline, summary, sentiment), "
             "and Response Templates (with category, tone, placeholders, approval status)."),
            ("How do I configure generation?",
             "Set the data type, number of records (5–50), batch size (2–10 records per Bedrock call), "
             "date range, and optionally select specific topics. Check 'Load generated data into app automatically' "
             "to merge results into the active dataset immediately."),
            ("Where is generated data saved?",
             "JSON files are saved to the data/ folder with timestamped filenames "
             "(e.g., inquiries_20260414_115326.json). The Saved Files table at the bottom shows all files in data/."),
        ]),

        # ── Scoring & AI Info ─────────────────────────────────────────────
        _faq_section("🏆", "Scoring & AI Info", [
            ("What does this page show?",
             "Maps every hackathon scoring criterion to concrete features in the app. "
             "This is a developer/test feature (greyed out in navigation). It covers 5 categories: "
             "Business Value & Impact (25 pts), Technical Innovation & Quality (25 pts), "
             "User Experience & Design (20 pts), Teamwork & Execution (15 pts), "
             "and AI Literacy & Learning (15 pts)."),
            ("What is the AI Model Transparency section?",
             "Two side-by-side panels showing what the AI CAN do (classify, detect sentiment, extract entities, "
             "draft responses, generate reports, identify risks, generate test data, monitor sentiment in real-time) "
             "and what it CANNOT do (make policy predictions, replace human judgment, guarantee factual accuracy, "
             "process PII safely, detect sarcasm reliably, classify unseen categories, operate without oversight, "
             "ensure zero bias)."),
            ("What are the Success Metrics?",
             "Classification Accuracy: 75–95% (keyword fallback ~75%, Comprehend custom classifier 85–95%). "
             "Draft Quality: template-guided with 30+ approved templates. "
             "Sentiment Accuracy: Amazon Comprehend production SLA. "
             "Actionable Insights: 7-section structured report."),
        ]),

        # ── System Architecture ───────────────────────────────────────────
        _faq_section("🏗️", "System Architecture & Data Flow", [
            ("What is the data pipeline?",
             "At startup, the Data Loader merges data from 4 sources: local JSON files (data/ folder), "
             "GitHub sample data, Federal Reserve RSS feeds, and 13+ news outlet RSS feeds. "
             "All sources are free and require no API keys."),
            ("How does the processing pipeline work?",
             "1) Load combined data → 2) Classify inquiries via Comprehend → 3) Analyze sentiment → "
             "4) Build summary statistics → 5) Generate insights report via Bedrock → 6) Detect risks via Bedrock. "
             "Each step is modular and can be run independently."),
            ("What are the key service modules?",
             "bedrock_service.py (LLM gateway), comprehend_service.py (NLP gateway), "
             "public_data_service.py (RSS fetcher for 13+ outlets), data_loader.py (multi-source data merger), "
             "response_templates.py (30+ approved templates), datagen_service.py (synthetic data generator), "
             "audit_log.py (action tracking), wordcloud_util.py (word cloud image generation), "
             "pipeline.py (end-to-end orchestration), config.py (AWS region, model, environment variables)."),
            ("Where are the architecture diagrams?",
             "Three diagrams are available in the project root: "
             "C1 System Context Diagram (c1_context_diagram.png/pdf/drawio), "
             "C4 Container Diagram (c4_container_diagram.png/pdf/drawio), "
             "and Component Diagram (component_diagram.png/pdf/drawio). "
             "Markdown versions with Mermaid syntax are also available (.md files)."),
        ]),
    ])

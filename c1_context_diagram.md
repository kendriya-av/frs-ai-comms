# C1 — System Context Diagram
## FRBSF AI Communications Intelligence System

```mermaid
C4Context
    title System Context Diagram — FRBSF AI Communications Intelligence System

    Person(comms_officer, "Communications Officer", "FRBSF External Communications staff. Reviews AI-generated drafts, monitors sentiment, acts on risk alerts.")
    Person(leadership, "Leadership / Executives", "Consumes executive insights reports, monitors sentiment trends and risk areas.")
    Person(public, "Public / Media / Stakeholders", "Sends inquiries via email, web form, letter, or phone. Receives official FRBSF responses.")

    System(frs_ai_comms, "FRBSF AI Communications System", "AI-powered platform that classifies inquiries, monitors public sentiment, drafts responses, detects risks, and generates executive reports.")

    System_Ext(comprehend, "Amazon Comprehend", "AWS NLP service — sentiment analysis, entity extraction, key phrase detection, text classification.")
    System_Ext(bedrock, "Amazon Bedrock (Claude)", "AWS LLM service — response drafting, insights report generation, risk identification.")
    System_Ext(rss_feeds, "Public RSS Feeds", "Federal Reserve (FOMC, press releases, speeches), CNBC, Reuters, Bloomberg, NY Times, Washington Post, NPR, AP News, etc.")
    System_Ext(github, "GitHub Sample Data", "Pre-loaded sample inquiries, social media posts, and news articles for demonstration.")
    System_Ext(apprunner, "AWS App Runner", "Managed container hosting — runs the Dash web application.")
    System_Ext(ecr, "Amazon ECR", "Container image registry — stores Docker images built by CodeBuild.")
    System_Ext(codebuild, "AWS CodeBuild", "CI/CD — builds Docker images from source and pushes to ECR.")
    System_Ext(s3, "Amazon S3", "Source artifact storage — holds deployment zip files.")

    Rel(public, frs_ai_comms, "Sends inquiries", "Email, Web Form, Letter, Phone")
    Rel(comms_officer, frs_ai_comms, "Uses", "Web Browser (HTTPS)")
    Rel(leadership, frs_ai_comms, "Views reports", "Web Browser (HTTPS)")

    Rel(frs_ai_comms, comprehend, "Classifies text, analyzes sentiment", "AWS SDK / boto3")
    Rel(frs_ai_comms, bedrock, "Generates drafts, reports, risk analysis", "AWS SDK / boto3")
    Rel(frs_ai_comms, rss_feeds, "Fetches live data", "HTTP/RSS")
    Rel(frs_ai_comms, github, "Loads sample data", "HTTPS")

    Rel(codebuild, ecr, "Pushes Docker image", "AWS API")
    Rel(codebuild, s3, "Reads source zip", "AWS API")
    Rel(apprunner, ecr, "Pulls container image", "AWS API")
    Rel(apprunner, frs_ai_comms, "Hosts", "HTTPS")
```

## Actors

| Actor | Role | Interaction |
|-------|------|-------------|
| Communications Officer | Primary user — reviews AI drafts, monitors sentiment, manages inquiry queue | Web browser → Dash app |
| Leadership / Executives | Consumes insights reports, monitors trends | Web browser → Insights Report page |
| Public / Media / Stakeholders | Sends inquiries to FRBSF | Email, web form, letter, phone → Inquiry data |

## External Systems

| System | Purpose | Protocol |
|--------|---------|----------|
| Amazon Comprehend | NLP: sentiment, classification, key phrases, entities | boto3 SDK |
| Amazon Bedrock (Claude) | LLM: draft responses, insights reports, risk detection | boto3 SDK |
| Public RSS Feeds | Live news and Fed data (FOMC, speeches, press releases, news outlets) | HTTP/RSS |
| GitHub | Sample demonstration data | HTTPS |
| AWS App Runner | Managed container hosting | HTTPS |
| Amazon ECR | Docker image registry | AWS API |
| AWS CodeBuild | CI/CD pipeline | AWS API |
| Amazon S3 | Source artifact storage | AWS API |

## Data Flow Summary

1. **Inbound**: Inquiries arrive from public/media/stakeholders → loaded via Upload or Generate
2. **Classification**: Text → Amazon Comprehend → category, sentiment, confidence, key phrases
3. **Drafting**: Inquiry + template → Amazon Bedrock (Claude) → AI draft response
4. **Monitoring**: RSS feeds → keyword sentiment → merged into Sentiment Monitor
5. **Reporting**: All data → Amazon Bedrock → executive insights report
6. **Risk Detection**: Social media posts → Amazon Bedrock → risk analysis
7. **Deployment**: Source zip → S3 → CodeBuild → ECR → App Runner

"""
Response templates for FRBSF External Communications.

Each template is keyed by (category, audience) where audience is one of:
  public | media | stakeholder

Templates use double-brace placeholders: {{sender_name}}, {{reference_number}},
{{inquiry_date}}, {{specific_topic}}, {{officer_name}}, {{department}}

Tone guide:
  public      — plain English, empathetic, educational, no jargon
  media       — factual, concise, on-record language, directs to official sources
  stakeholder — formal, technical, policy-precise, acknowledges expertise
"""

# ── Template registry ─────────────────────────────────────────────────────────
# Key: (category, audience)  →  dict with subject, body, tone, guidance

TEMPLATES: dict[tuple[str, str], dict] = {

    # ── MONETARY POLICY ───────────────────────────────────────────────────────
    ("monetary_policy", "public"): {
        "tone": "empathetic, plain English",
        "guidance": "Avoid jargon. Explain the dual mandate simply. Acknowledge the real-world impact on everyday people.",
        "subject": "Re: Your Question About Federal Reserve Monetary Policy — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for reaching out to the Federal Reserve Bank of San Francisco. We received your inquiry on {{inquiry_date}} and appreciate you taking the time to share your question.

The Federal Reserve's primary goal is to keep prices stable and help as many Americans as possible find good jobs — what we call our "dual mandate." When inflation rises too quickly, the Fed may raise interest rates to slow spending and bring prices back down. We understand this can make borrowing more expensive in the short term, and we recognize the real impact that has on families and households.

We encourage you to visit frbsf.org, where you'll find plain-language explainers on how monetary policy works and how it affects everyday financial decisions. The Board of Governors also maintains a helpful consumer resource page at federalreserve.gov/consumerscommunities.

If you have further questions, please don't hesitate to contact our Public Affairs office. We value your engagement.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("monetary_policy", "media"): {
        "tone": "factual, concise, on-record",
        "guidance": "Direct to official FOMC statements. Do not speculate on future policy. Offer spokesperson availability if appropriate.",
        "subject": "FRBSF Response to Media Inquiry — Monetary Policy — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting the Federal Reserve Bank of San Francisco Communications and Media Relations office regarding {{specific_topic}}.

All official commentary on monetary policy decisions is contained in FOMC statements, meeting minutes, and Chair press conferences, available at federalreserve.gov/monetarypolicy. Speeches and public remarks by FRBSF leadership are published at frbsf.org/news-and-media.

We are unable to provide on-record characterisation of future policy actions beyond what has been disclosed through official Federal Reserve channels. Should you require a spokesperson for background context, please reply to this message with your publication deadline and we will do our best to accommodate your timeline.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("monetary_policy", "stakeholder"): {
        "tone": "formal, policy-precise, technically informed",
        "guidance": "Acknowledge the stakeholder's expertise. Reference specific FOMC communications. Offer follow-up engagement where appropriate.",
        "subject": "Federal Reserve Bank of San Francisco — Response to Inquiry Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your correspondence dated {{inquiry_date}} regarding {{specific_topic}}. We appreciate your continued engagement with the Federal Reserve System on matters of monetary policy.

The Federal Open Market Committee's policy framework, including the Statement on Longer-Run Goals and Monetary Policy Strategy, provides the foundational guidance for current policy decisions. All FOMC deliberations, projections, and forward guidance are communicated through official statements, the Summary of Economic Projections, and the Chair's post-meeting press conferences, all of which are publicly available at federalreserve.gov.

Should you wish to discuss specific aspects of the FRBSF's economic research or regional perspectives on monetary policy transmission, we would welcome the opportunity to arrange a meeting with the appropriate staff. Please contact our External Engagement office to schedule.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── INTEREST RATES ────────────────────────────────────────────────────────
    ("interest_rates", "public"): {
        "tone": "empathetic, plain English, practical",
        "guidance": "Acknowledge the personal financial impact. Explain the connection between Fed rate and consumer rates simply. Point to consumer resources.",
        "subject": "Re: Your Question About Interest Rates — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for writing to us. We received your inquiry on {{inquiry_date}} and understand that changes in interest rates have a direct and meaningful impact on your finances.

When the Federal Reserve adjusts the federal funds rate — the rate banks charge each other for overnight loans — it influences the interest rates consumers see on mortgages, car loans, credit cards, and savings accounts. Rate increases are intended to slow inflation by making borrowing more expensive, which reduces spending and helps bring prices down over time.

We know this is difficult for many households, and we want you to have access to good information. The Consumer Financial Protection Bureau (consumerfinance.gov) offers practical tools for managing borrowing costs. You can also find educational resources at frbsf.org.

Thank you again for reaching out.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("interest_rates", "media"): {
        "tone": "factual, brief, source-directed",
        "guidance": "Cite the most recent FOMC decision. Do not forecast. Offer data references.",
        "subject": "FRBSF — Media Inquiry Response: Interest Rates — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your inquiry regarding {{specific_topic}}.

The most recent FOMC decision and accompanying statement are available at federalreserve.gov/monetarypolicy/fomccalendars.htm. Historical rate data and economic projections are published in the Summary of Economic Projections following each quarterly meeting.

FRBSF economists publish regular research on interest rate dynamics and regional economic conditions at frbsf.org/economic-research. We are happy to connect you with a research contact for background if helpful — please provide your deadline.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("interest_rates", "stakeholder"): {
        "tone": "formal, data-informed, collaborative",
        "guidance": "Reference the rate decision and SEP. Acknowledge the stakeholder's sector-specific concerns. Offer engagement.",
        "subject": "FRBSF Response — Interest Rate Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your letter dated {{inquiry_date}} concerning {{specific_topic}}.

The Federal Open Market Committee's current target range for the federal funds rate, along with the Committee's economic projections and policy rationale, are detailed in the most recent FOMC statement and Summary of Economic Projections, available at federalreserve.gov. The FRBSF's own economic research on interest rate transmission and regional credit conditions is published regularly at frbsf.org/economic-research.

We recognise the significance of rate policy for your organisation's planning and operations. If it would be helpful, we would welcome the opportunity to discuss the FRBSF's regional economic outlook with your team. Please contact our External Engagement office to arrange a meeting.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── INFLATION ─────────────────────────────────────────────────────────────
    ("inflation", "public"): {
        "tone": "empathetic, validating, educational",
        "guidance": "Validate the lived experience of inflation. Explain CPI vs PCE simply. Be honest about the timeline.",
        "subject": "Re: Your Question About Inflation — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting us. We received your message on {{inquiry_date}} and want you to know that your concerns about the cost of living are heard and taken seriously.

Inflation means that the prices of goods and services are rising over time. The Federal Reserve monitors several measures of inflation — including the Consumer Price Index (CPI) and the Personal Consumption Expenditures (PCE) index — to understand how quickly prices are changing across the economy. Our goal is to keep inflation near 2% over the long run, which supports stable prices and predictable financial planning for households and businesses.

Bringing inflation down takes time, and we understand that the process is difficult for many families. We are committed to using our tools carefully to restore price stability without causing unnecessary harm to the job market.

For more information, please visit frbsf.org or federalreserve.gov/faqs.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("inflation", "media"): {
        "tone": "data-driven, precise, source-directed",
        "guidance": "Reference the latest PCE/CPI data. Point to FRBSF inflation research. Do not speculate on future path.",
        "subject": "FRBSF — Media Inquiry: Inflation — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your inquiry regarding {{specific_topic}}.

The latest inflation data, including PCE and CPI releases, are published by the Bureau of Economic Analysis and Bureau of Labor Statistics respectively. The FRBSF publishes ongoing inflation research and commentary at frbsf.org/economic-research, including the widely referenced Underlying Inflation Gauge (UIG).

For on-record statements regarding the Fed's inflation outlook, please refer to the most recent FOMC statement and Chair press conference transcript at federalreserve.gov. We are unable to provide forward-looking commentary beyond official communications.

Please let us know if we can connect you with a research economist for background context.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("inflation", "stakeholder"): {
        "tone": "analytical, policy-precise, forward-looking within bounds",
        "guidance": "Reference PCE target, current trajectory, and FRBSF research. Acknowledge sector-specific inflation dynamics if relevant.",
        "subject": "FRBSF Response — Inflation Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your correspondence dated {{inquiry_date}} regarding {{specific_topic}}.

The Federal Reserve's longer-run inflation goal of 2%, as measured by the PCE price index, remains the anchor for monetary policy decisions. The FRBSF contributes actively to the System's understanding of inflation dynamics through published research on topics including supply-chain inflation, shelter costs, and wage-price interactions, all available at frbsf.org/economic-research.

We appreciate your perspective on how current inflation dynamics are affecting your sector. Should you wish to engage further with FRBSF economists on this topic, we would be pleased to facilitate that conversation through our External Engagement office.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── BANKING REGULATION ────────────────────────────────────────────────────
    ("banking_regulation", "public"): {
        "tone": "reassuring, plain English, safety-focused",
        "guidance": "Reassure about deposit safety. Explain FDIC coverage simply. Avoid regulatory jargon.",
        "subject": "Re: Your Question About Banking Regulation — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting the Federal Reserve Bank of San Francisco. We received your inquiry on {{inquiry_date}} and are happy to provide information about bank regulation and consumer protections.

The Federal Reserve, along with other federal agencies, supervises banks to ensure they operate safely and treat customers fairly. Deposits at FDIC-insured banks are protected up to $250,000 per depositor, per institution. You can verify whether your bank is insured and check coverage details at fdic.gov.

For questions about your rights as a bank customer or to file a complaint, the Consumer Financial Protection Bureau (consumerfinance.gov) and the FDIC (fdic.gov/consumers) are excellent resources.

If you have a specific concern about a bank supervised by the Federal Reserve, you may submit it through our consumer complaint process at federalreserve.gov/consumerscommunities/consumer_complaint.htm.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("banking_regulation", "media"): {
        "tone": "factual, measured, source-directed",
        "guidance": "Reference the specific rule or supervisory action. Direct to official NPR or supervisory guidance. Do not comment on individual institutions.",
        "subject": "FRBSF — Media Inquiry: Banking Regulation — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your inquiry regarding {{specific_topic}}.

The Federal Reserve's supervisory and regulatory activities, including proposed rulemakings and final rules, are published at federalreserve.gov/supervisionreg. For matters related to the Basel III Endgame or other capital framework proposals, the relevant Notices of Proposed Rulemaking and comment letters are available through the same portal.

We are unable to comment on the supervisory status of individual institutions. For questions about specific regulatory proposals, we can arrange background conversations with our supervisory policy staff — please provide your publication deadline.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("banking_regulation", "stakeholder"): {
        "tone": "formal, technically precise, collaborative",
        "guidance": "Acknowledge the specific regulation cited. Reference the NPR and comment period. Offer a meeting with supervisory staff.",
        "subject": "FRBSF Response — Banking Regulation Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your formal correspondence dated {{inquiry_date}} regarding {{specific_topic}}.

The Federal Reserve takes seriously the concerns of supervised institutions and industry stakeholders regarding proposed regulatory changes. The Notice of Proposed Rulemaking referenced in your letter, along with all supporting materials and the comment submission portal, is available at federalreserve.gov/supervisionreg.

We would welcome the opportunity to meet with your team to discuss the specific provisions of concern and the anticipated implementation timeline. Please contact our Supervisory Policy office to arrange a meeting at your convenience. A written response to your specific questions will follow within the timeframe indicated in our acknowledgement.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── EMPLOYMENT ────────────────────────────────────────────────────────────
    ("employment", "public"): {
        "tone": "accessible, hopeful, data-grounded",
        "guidance": "Explain the maximum employment mandate simply. Connect labor market data to everyday experience.",
        "subject": "Re: Your Question About Employment and the Federal Reserve — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for writing to us on {{inquiry_date}}. Your question about employment and the Federal Reserve's role is one we hear often, and we're glad to explain.

One of the Federal Reserve's two main goals — our "dual mandate" — is to support maximum employment, meaning we aim to help as many people as possible find good jobs. We monitor a wide range of labor market indicators, including the unemployment rate, job openings, wage growth, and labor force participation, to understand the health of the job market.

When we raise interest rates to fight inflation, we are aware that this can slow hiring. We try to balance these two goals carefully. The FRBSF publishes regular research on labor market conditions at frbsf.org/economic-research.

Thank you for your engagement.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("employment", "media"): {
        "tone": "data-precise, source-directed",
        "guidance": "Reference the latest jobs report and FRBSF labor market research. Do not forecast.",
        "subject": "FRBSF — Media Inquiry: Employment — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your inquiry regarding {{specific_topic}}.

The Bureau of Labor Statistics publishes monthly employment data at bls.gov. The FRBSF publishes ongoing labor market research, including analysis of wage dynamics, labor force participation, and regional employment trends, at frbsf.org/economic-research.

For on-record statements regarding the Fed's employment outlook, please refer to the most recent FOMC statement and Chair press conference at federalreserve.gov. We can arrange a background conversation with a labor economist if helpful — please share your deadline.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("employment", "stakeholder"): {
        "tone": "formal, analytically engaged",
        "guidance": "Reference the dual mandate and current labor market conditions. Acknowledge sector-specific workforce concerns.",
        "subject": "FRBSF Response — Employment Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your correspondence dated {{inquiry_date}} regarding {{specific_topic}}.

The Federal Reserve's maximum employment mandate directs us to consider a broad range of labor market indicators in our policy deliberations. The FRBSF contributes to the System's understanding of labor market dynamics through published research on topics including wage growth, labor supply constraints, and regional employment conditions, available at frbsf.org/economic-research.

We appreciate your perspective on workforce conditions within your sector. If you would like to discuss the FRBSF's regional labor market outlook in more detail, we would welcome the opportunity to engage through our External Affairs office.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── MEDIA REQUEST ─────────────────────────────────────────────────────────
    ("media_request", "media"): {
        "tone": "professional, responsive, deadline-aware",
        "guidance": "Acknowledge the request promptly. Confirm what can and cannot be provided. Offer a spokesperson or background call.",
        "subject": "FRBSF Media Relations — Response to Your Request — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting the Federal Reserve Bank of San Francisco Media Relations office. We have received your request dated {{inquiry_date}} regarding {{specific_topic}}.

We are reviewing your request and will respond as promptly as possible. In the meantime, you may find relevant background materials — including speeches, economic letters, and press releases — at frbsf.org/news-and-media.

Please note that all on-record statements from FRBSF leadership are coordinated through this office. We are unable to facilitate unscheduled direct contact with Bank officers. If your request involves a publication deadline, please reply with that information so we can prioritise accordingly.

We appreciate your interest in the Federal Reserve Bank of San Francisco.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    # ── FEDERAL FUNDS RATE ────────────────────────────────────────────────────
    ("federal_funds_rate", "public"): {
        "tone": "plain English, practical, reassuring",
        "guidance": "Explain what the federal funds rate is in one sentence. Connect to consumer rates. Avoid implying the Fed sets mortgage rates directly.",
        "subject": "Re: Your Question About the Federal Funds Rate — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your message received on {{inquiry_date}}.

The federal funds rate is the interest rate at which banks lend money to each other overnight. While the Fed does not directly set mortgage rates, credit card rates, or savings rates, changes to the federal funds rate influence borrowing costs across the economy. When the Fed raises this rate, banks typically pass some of that increase on to consumers through higher loan rates.

We understand this has a real impact on household budgets. For tools to help you understand and manage your borrowing costs, we recommend visiting consumerfinance.gov or federalreserve.gov/consumerscommunities.

Thank you for reaching out.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("federal_funds_rate", "media"): {
        "tone": "precise, source-directed",
        "guidance": "Reference the current target range. Direct to FOMC calendar and statements.",
        "subject": "FRBSF — Media Inquiry: Federal Funds Rate — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your inquiry regarding {{specific_topic}}.

The current federal funds rate target range and the rationale for the most recent decision are detailed in the FOMC statement available at federalreserve.gov/monetarypolicy/fomccalendars.htm. Historical rate data and the Fed's policy framework are also available through that portal.

We are unable to provide forward guidance beyond what has been communicated through official FOMC channels. Please let us know if a background conversation with an economist would be helpful.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("federal_funds_rate", "stakeholder"): {
        "tone": "formal, technically precise",
        "guidance": "Reference the current target range and SEP dot plot. Acknowledge the stakeholder's interest in the rate path.",
        "subject": "FRBSF Response — Federal Funds Rate Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your correspondence dated {{inquiry_date}} regarding {{specific_topic}}.

The Federal Open Market Committee's current target range for the federal funds rate, along with individual participant projections as reflected in the Summary of Economic Projections, are published following each quarterly FOMC meeting at federalreserve.gov. The FRBSF's regional economic outlook, which informs our President's participation in FOMC deliberations, is published periodically at frbsf.org.

We appreciate your interest in the policy rate outlook. Should you wish to discuss the FRBSF's economic perspective in more detail, please contact our External Engagement office.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    # ── GENERAL / OTHER ───────────────────────────────────────────────────────
    ("other", "public"): {
        "tone": "warm, helpful, redirecting",
        "guidance": "Acknowledge the inquiry warmly. Direct to the most relevant resource. Offer to help further.",
        "subject": "Re: Your Inquiry to the Federal Reserve Bank of San Francisco — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting the Federal Reserve Bank of San Francisco. We received your message on {{inquiry_date}} and appreciate you reaching out.

We want to make sure your question reaches the right team. Based on your inquiry, you may find helpful information at frbsf.org or federalreserve.gov. If your question relates to a specific Federal Reserve service or publication, our website's search function can help you locate the relevant resource quickly.

If you would like to speak with someone directly, our Public Affairs office can be reached through the contact information on our website. We are happy to help direct your inquiry to the appropriate department.

Thank you for your interest in the Federal Reserve.

Sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },

    ("other", "media"): {
        "tone": "professional, redirecting",
        "guidance": "Acknowledge and redirect to the appropriate contact or resource.",
        "subject": "FRBSF Media Relations — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for contacting the Federal Reserve Bank of San Francisco Media Relations office regarding {{specific_topic}}.

We have received your inquiry and will direct it to the appropriate team. In the meantime, our full library of press releases, speeches, and economic publications is available at frbsf.org/news-and-media.

Please reply with your publication deadline so we can prioritise your request accordingly.

Regards,
{{officer_name}}
Media Relations
Federal Reserve Bank of San Francisco""",
    },

    ("other", "stakeholder"): {
        "tone": "formal, courteous, redirecting",
        "guidance": "Acknowledge formally and route to the correct department.",
        "subject": "Federal Reserve Bank of San Francisco — Acknowledgement of Inquiry — Ref {{reference_number}}",
        "body": """Dear {{sender_name}},

Thank you for your correspondence dated {{inquiry_date}}. We have received your inquiry and are directing it to the appropriate department within the Federal Reserve Bank of San Francisco for review and response.

You can expect a substantive reply within 10 business days. Should your matter be time-sensitive, please indicate that in a follow-up message and we will prioritise accordingly.

We appreciate your engagement with the Federal Reserve System.

Yours sincerely,
{{officer_name}}
{{department}}
Federal Reserve Bank of San Francisco""",
    },
}

# ── Fallback chain ────────────────────────────────────────────────────────────
# If exact (category, audience) not found, try (category, "public"), then ("other", audience)

def get_template(category: str, audience: str) -> dict | None:
    """
    Look up the best matching template for a given category and audience.
    Returns the template dict or None if no match at all.
    """
    key = (category, audience)
    if key in TEMPLATES:
        return TEMPLATES[key]
    # Try same category with public audience
    fallback1 = (category, "public")
    if fallback1 in TEMPLATES:
        return TEMPLATES[fallback1]
    # Try other category with requested audience
    fallback2 = ("other", audience)
    if fallback2 in TEMPLATES:
        return TEMPLATES[fallback2]
    # Last resort
    return TEMPLATES.get(("other", "public"))


def list_categories() -> list[str]:
    """Return all unique categories that have templates."""
    return sorted({cat for cat, _ in TEMPLATES.keys()})


def list_audiences() -> list[str]:
    return ["public", "media", "stakeholder"]

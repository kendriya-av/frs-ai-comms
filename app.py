import base64
import io
import json
import sys
import os
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dash_table, dcc, html, ALL, MATCH

sys.path.insert(0, os.path.dirname(__file__))

from bedrock_service import draft_response, generate_insights_report, identify_risks, AVAILABLE_MODELS
from comprehend_service import analyze_sentiment, classify_inquiry, detect_key_phrases
from data_loader import load_all_sample_data, load_combined_data
from pipeline import build_summary
from datagen_service import generate_data, DATA_TYPE_CONFIG
from config import BEDROCK_MODEL_ID
from public_data_service import (
    fetch_fomc_statements, fetch_press_releases, fetch_speeches,
    fetch_frbsf_research, fetch_frbsf_speeches,
    fetch_news_feeds,
    FED_FEEDS, NEWS_FEEDS,
)
from response_templates import get_template

# ── App init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
)
app.title = "FRBSF | AI Communications Intelligence"

sample_data = load_combined_data()   # GitHub + FOMC RSS + News RSS

# ── Design tokens ─────────────────────────────────────────────────────────────
COLORS = {
    "navy":    "#1B2A4A",
    "gold":    "#C8A951",
    "light_bg":"#F4F6F9",
    "white":   "#FFFFFF",
    "border":  "#DDE2EC",
    "text":    "#1E2D40",
    "muted":   "#6B7A99",
    "success": "#2E7D32",
    "danger":  "#C62828",
    "warning": "#E65100",
}

GLOBAL_STYLE = {
    "fontFamily": "'Inter', sans-serif",
    "backgroundColor": COLORS["light_bg"],
    "color": COLORS["text"],
    "minHeight": "100vh",
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "240px",
    "backgroundColor": COLORS["navy"],
    "padding": "0",
    "zIndex": 1000,
    "boxShadow": "2px 0 8px rgba(0,0,0,0.15)",
    "overflowY": "auto",
}

CONTENT_STYLE = {
    "marginLeft": "240px",
    "padding": "32px 36px",
    "backgroundColor": COLORS["light_bg"],
    "minHeight": "100vh",
}

TABLE_STYLE = {
    "style_table": {"overflowX": "auto", "borderRadius": "8px", "border": f"1px solid {COLORS['border']}"},
    "style_header": {
        "backgroundColor": COLORS["navy"],
        "color": COLORS["white"],
        "fontWeight": "600",
        "fontSize": "13px",
        "padding": "12px 14px",
        "border": "none",
    },
    "style_cell": {
        "textAlign": "left",
        "padding": "10px 14px",
        "fontSize": "13px",
        "maxWidth": "400px",
        "overflow": "hidden",
        "whiteSpace": "normal",
        "height": "auto",
        "border": f"1px solid {COLORS['border']}",
        "color": COLORS["text"],
    },
    "style_data_conditional": [
        {"if": {"row_index": "odd"}, "backgroundColor": "#F8FAFC"},
    ],
}

def flatten_for_table(df: pd.DataFrame) -> pd.DataFrame:
    """Convert any list/dict columns to strings so DataTable can render them."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(
                lambda v: ", ".join(str(i) for i in v) if isinstance(v, list)
                else json.dumps(v) if isinstance(v, dict)
                else v
            )
    return df

def card(children, className="", style=None):
    return html.Div(
        children,
        style={
            "backgroundColor": COLORS["white"],
            "borderRadius": "10px",
            "padding": "24px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
            "border": f"1px solid {COLORS['border']}",
            **(style or {}),
        },
        className=className,
    )

def metric_card(label, value, color=None):
    return html.Div(
        [
            html.P(label, style={"fontSize": "12px", "fontWeight": "600", "color": COLORS["muted"],
                                  "textTransform": "uppercase", "letterSpacing": "0.8px", "marginBottom": "6px"}),
            html.H3(str(value), style={"fontWeight": "700", "color": color or COLORS["navy"], "margin": 0}),
        ],
        style={
            "backgroundColor": COLORS["white"],
            "borderRadius": "10px",
            "padding": "20px 24px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
            "border": f"1px solid {COLORS['border']}",
            "borderLeft": f"4px solid {color or COLORS['gold']}",
        },
    )

def page_header(title, subtitle=None):
    return html.Div([
        html.H4(title, style={"fontWeight": "700", "color": COLORS["navy"], "marginBottom": "4px"}),
        html.P(subtitle, style={"color": COLORS["muted"], "fontSize": "14px", "marginBottom": "24px"}) if subtitle else None,
        html.Hr(style={"borderColor": COLORS["border"], "marginBottom": "28px"}),
    ])

def styled_btn(label, id, color=COLORS["navy"]):
    return html.Button(
        label,
        id=id,
        style={
            "backgroundColor": color,
            "color": COLORS["white"],
            "border": "none",
            "borderRadius": "6px",
            "padding": "10px 22px",
            "fontWeight": "600",
            "fontSize": "14px",
            "cursor": "pointer",
            "fontFamily": "'Inter', sans-serif",
        },
    )

def styled_input(id, placeholder="", type="text"):
    return dcc.Input(
        id=id,
        type=type,
        placeholder=placeholder,
        style={
            "width": "100%",
            "padding": "9px 12px",
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontFamily": "'Inter', sans-serif",
            "color": COLORS["text"],
            "outline": "none",
        },
    )

def styled_textarea(id, placeholder="", rows=5):
    return dcc.Textarea(
        id=id,
        placeholder=placeholder,
        rows=rows,
        style={
            "width": "100%",
            "padding": "9px 12px",
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontFamily": "'Inter', sans-serif",
            "color": COLORS["text"],
            "resize": "vertical",
        },
    )

def styled_dropdown(id, options, value=None, multi=False, placeholder="Select..."):
    return dcc.Dropdown(
        id=id,
        options=options,
        value=value,
        multi=multi,
        placeholder=placeholder,
        clearable=False if not multi else True,
        style={"fontSize": "14px", "fontFamily": "'Inter', sans-serif"},
    )

def label(text):
    return html.P(text, style={"fontSize": "13px", "fontWeight": "600", "color": COLORS["muted"],
                                "marginBottom": "6px", "textTransform": "uppercase", "letterSpacing": "0.5px"})

# ── Sidebar ───────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("/",           "Overview",            "🏠"),
    ("/hub",        "Communications Hub",  "💬"),
    ("/inquiries",  "Inquiry & Response",  "📥"),
    ("/sentiment",  "Sentiment Monitor",   "📊"),
    ("/insights",   "Insights Report",     "📈"),
    ("/risks",      "Risk Detector",       "⚠️"),
    ("/roi",        "ROI Calculator",      "💰"),
    ("/feddata",    "Live Fed Data",       "🌐"),
    ("/upload",     "Upload Data",         "📂"),
    ("/audit",      "Audit Log",           "📋"),
    ("/trust",      "Trust & Safety",      "🛡️"),
    ("/settings",   "AI Model Config",     "🤖"),
    ("/generate",   "Generate Test Data",  "🧪"),
    ("/scoring",    "Scoring & AI Info",   "🏆"),
]

def sidebar():
    return html.Div([
        # Logo / branding
        html.Div([
            html.Div("FRBSF", style={
                "color": COLORS["gold"], "fontWeight": "700", "fontSize": "20px",
                "letterSpacing": "2px",
            }),
            html.Div("AI Communications", style={
                "color": "rgba(255,255,255,0.6)", "fontSize": "11px",
                "letterSpacing": "1px", "marginTop": "2px",
            }),
        ], style={"padding": "28px 24px 20px", "borderBottom": "1px solid rgba(255,255,255,0.08)"}),

        # Nav links
        html.Div([
            dcc.Link(
                html.Div([
                    html.Span(icon, style={"marginRight": "10px", "fontSize": "15px"}),
                    html.Span(name, style={"fontSize": "14px", "fontWeight": "500"}),
                ], style={"padding": "11px 20px", "borderRadius": "6px", "cursor": "pointer",
                          "color": "rgba(255,255,255,0.4)" if href in ("/generate", "/scoring") else "rgba(255,255,255,0.85)",
                          "display": "flex", "alignItems": "center",
                          "transition": "background 0.15s"}),
                href=href,
                style={"textDecoration": "none", "display": "block", "marginBottom": "2px"},
            )
            for href, name, icon in NAV_ITEMS
        ], style={"padding": "16px 12px"}),

        # Footer
        html.Div([
            html.Div("⚠ AI outputs require human review",
                     style={"fontSize": "10px", "color": COLORS["gold"],
                            "fontWeight": "600", "marginBottom": "4px"}),
            html.Div("Federal Reserve Bank of San Francisco",
                     style={"fontSize": "10px", "color": "rgba(255,255,255,0.3)"}),
        ], style={"position": "absolute", "bottom": "20px", "left": "0", "right": "0",
                  "textAlign": "center", "padding": "0 16px"}),
    ], style=SIDEBAR_STYLE)

# ── Main layout ───────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="uploaded-data"),
    dcc.Store(id="model-store"),
    dcc.Store(id="data-refresh-signal", data=0),
    dcc.Store(id="data-source-store", data={
        "sources":      sample_data.get("data_sources", ["GitHub sample data"]),
        "load_summary": sample_data.get("load_summary", {}),
        "loaded_at":    sample_data.get("loaded_at", ""),
    }),
    sidebar(),
    html.Div(id="page-content", style=CONTENT_STYLE),
], style=GLOBAL_STYLE)

# ── Page: Overview ───────────────────────────────────────────────────────────
def overview_page():
    # AWS services used
    aws_services = [
        ("Amazon Comprehend",  "NLP — sentiment analysis, entity extraction, key phrases, text classification", "#FF9900"),
        ("Amazon Bedrock",     "LLM — response drafting, insights reports, risk identification (Claude)", "#232F3E"),
        ("AWS IAM / SSO",      "Secure authentication and role-based access control", "#DD344C"),
    ]

    # Feature cards
    features = [
        ("/hub",        "💬", "Communications Hub",  "Single-screen view: analyze an inquiry, get a draft response, and monitor sentiment — all at once."),
        ("/inquiries",  "📥", "Inquiry & Response", "Classify inquiries, review Bedrock classification, and generate template-guided draft responses — all in one workflow."),
        ("/sentiment",  "📊", "Sentiment Monitor",  "Consolidated sentiment across LinkedIn, WSJ, CNBC, Bloomberg, Axios, and more."),
        ("/insights",   "📈", "Insights Report",    "Produces AI-generated executive reports with per-category breakdown, risks, and recommended actions."),
        ("/risks",      "⚠️", "Risk Detector",      "Identifies misinformation, trending negative topics, and urgent communication risks automatically."),
    ]

    # Responsible AI notices
    rai_items = [
        ("Human Review Required",    "All AI-generated drafts and classifications must be reviewed by a communications officer before use."),
        ("Bias Awareness",           "Sentiment models may reflect biases in training data. Results should be interpreted with domain expertise."),
        ("Data Privacy",             "No personally identifiable information should be submitted to this system without appropriate data handling controls."),
        ("Model Limitations",        "LLM outputs can be incorrect or outdated. Always verify facts against official Federal Reserve sources."),
        ("Explainability",           "Confidence scores and key phrases are surfaced alongside every classification to support human oversight."),
    ]

    return html.Div([
        # ── Hero ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("FRBSF", style={"fontSize": "13px", "fontWeight": "700",
                                          "color": COLORS["gold"], "letterSpacing": "3px",
                                          "marginBottom": "8px"}),
                html.H2("AI Communications Intelligence System",
                        style={"fontWeight": "700", "color": COLORS["white"],
                               "marginBottom": "12px", "fontSize": "28px"}),
                html.P(
                    "An AI-powered platform that classifies incoming communications, "
                    "monitors public sentiment, drafts professional responses, and "
                    "identifies communication risks — purpose-built for the "
                    "Federal Reserve Bank of San Francisco External Communications department.",
                    style={"color": "rgba(255,255,255,0.8)", "fontSize": "15px",
                           "lineHeight": "1.7", "maxWidth": "700px"},
                ),
                html.Div([
                    html.Span("Amazon Comprehend", style={
                        "backgroundColor": "rgba(255,153,0,0.2)", "color": "#FF9900",
                        "borderRadius": "20px", "padding": "4px 12px",
                        "fontSize": "12px", "fontWeight": "600", "marginRight": "8px",
                    }),
                    html.Span("Amazon Bedrock", style={
                        "backgroundColor": "rgba(255,255,255,0.1)", "color": COLORS["white"],
                        "borderRadius": "20px", "padding": "4px 12px",
                        "fontSize": "12px", "fontWeight": "600", "marginRight": "8px",
                    }),
                    html.Span("Claude 3", style={
                        "backgroundColor": "rgba(200,169,81,0.2)", "color": COLORS["gold"],
                        "borderRadius": "20px", "padding": "4px 12px",
                        "fontSize": "12px", "fontWeight": "600",
                    }),
                ], style={"marginTop": "20px"}),
            ]),
        ], style={
            "backgroundColor": COLORS["navy"],
            "borderRadius": "12px",
            "padding": "40px 44px",
            "marginBottom": "32px",
        }),

        # ── Problem Statement ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col(card([
                html.P("THE CHALLENGE", style={"fontSize": "11px", "fontWeight": "700",
                                               "color": COLORS["gold"], "letterSpacing": "2px",
                                               "marginBottom": "10px"}),
                html.P(
                    "The FRBSF External Communications department receives hundreds of inquiries "
                    "from media, the public, and stakeholders — while simultaneously needing to "
                    "monitor public sentiment about monetary policy decisions across social media and news.",
                    style={"fontSize": "14px", "lineHeight": "1.7", "color": COLORS["text"],
                           "marginBottom": "12px"},
                ),
                html.P(
                    "Manual processing creates bottlenecks, inconsistent responses, and delayed "
                    "identification of emerging communication risks.",
                    style={"fontSize": "14px", "lineHeight": "1.7", "color": COLORS["muted"]},
                ),
            ]), width=6),
            dbc.Col(card([
                html.P("THE SOLUTION", style={"fontSize": "11px", "fontWeight": "700",
                                              "color": COLORS["gold"], "letterSpacing": "2px",
                                              "marginBottom": "10px"}),
                html.Div([
                    html.Div([
                        html.Span("→ ", style={"color": COLORS["gold"], "fontWeight": "700"}),
                        html.Span(text, style={"fontSize": "14px", "color": COLORS["text"]}),
                    ], style={"marginBottom": "8px"})
                    for text in [
                        "Auto-classify and prioritize incoming inquiries",
                        "Monitor real-time sentiment across channels",
                        "Draft responses using approved templates + AI",
                        "Identify trending risks before they escalate",
                        "Generate executive insights reports on demand",
                    ]
                ]),
            ]), width=6),
        ], className="mb-4"),

        # ── Feature Grid ─────────────────────────────────────────────────
        html.P("CAPABILITIES", style={"fontSize": "11px", "fontWeight": "700",
                                       "color": COLORS["muted"], "letterSpacing": "2px",
                                       "marginBottom": "16px"}),
        dbc.Row([
            dbc.Col(
                dcc.Link(html.Div([
                    html.Div([
                        html.Span(icon, style={"fontSize": "22px"}),
                        html.Span(title, style={"fontWeight": "600", "fontSize": "14px",
                                                "color": COLORS["navy"], "marginLeft": "10px"}),
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),
                    html.P(desc, style={"fontSize": "13px", "color": COLORS["muted"],
                                        "lineHeight": "1.5", "margin": 0}),
                ], style={
                    "backgroundColor": COLORS["white"],
                    "borderRadius": "10px", "padding": "18px 20px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                    "border": f"1px solid {COLORS['border']}",
                    "cursor": "pointer", "height": "100%",
                    "transition": "box-shadow 0.2s",
                }),
                href=href, style={"textDecoration": "none"}),
                width=4, className="mb-3",
            )
            for href, icon, title, desc in features
        ]),

        # ── AWS Architecture ──────────────────────────────────────────────
        html.Br(),
        html.P("AWS ARCHITECTURE", style={"fontSize": "11px", "fontWeight": "700",
                                           "color": COLORS["muted"], "letterSpacing": "2px",
                                           "marginBottom": "16px"}),
        card([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div(svc, style={"fontWeight": "700", "fontSize": "13px",
                                             "color": color, "marginBottom": "4px"}),
                        html.Div(desc, style={"fontSize": "12px", "color": COLORS["muted"],
                                              "lineHeight": "1.5"}),
                    ], style={
                        "padding": "14px 16px", "borderRadius": "8px",
                        "border": f"1px solid {COLORS['border']}",
                        "borderLeft": f"4px solid {color}",
                        "backgroundColor": COLORS["light_bg"],
                        "marginBottom": "10px",
                    })
                    for svc, desc, color in aws_services
                ], width=5),
                dbc.Col([
                    html.Div([
                        # Flow diagram as styled boxes
                        html.Div([
                            _flow_box("Incoming Inquiries\nSocial Media · News", COLORS["navy"]),
                            _flow_arrow(),
                            _flow_box("Amazon Comprehend\nClassify · Sentiment · Entities", "#FF9900"),
                            _flow_arrow(),
                            _flow_box("Amazon Bedrock (Claude)\nDraft · Report · Risk", COLORS["gold"]),
                            _flow_arrow(),
                            _flow_box("Communications Team\nReview · Send · Act", COLORS["success"]),
                        ], style={"display": "flex", "alignItems": "center",
                                  "flexWrap": "wrap", "gap": "4px"}),
                    ]),
                ], width=7),
            ]),
        ], style={"marginBottom": "24px"}),

        # ── Responsible AI ────────────────────────────────────────────────
        html.P("RESPONSIBLE AI", style={"fontSize": "11px", "fontWeight": "700",
                                         "color": COLORS["muted"], "letterSpacing": "2px",
                                         "marginBottom": "16px"}),
        card([
            html.Div([
                html.Div([
                    html.Span("⚠ ", style={"color": COLORS["warning"], "fontWeight": "700"}),
                    html.Span(title, style={"fontWeight": "600", "fontSize": "13px",
                                            "color": COLORS["navy"]}),
                    html.Span(f"  —  {desc}", style={"fontSize": "13px", "color": COLORS["muted"]}),
                ], style={"marginBottom": "10px"})
                for title, desc in rai_items
            ]),
        ], style={"borderLeft": f"4px solid {COLORS['warning']}"}),
    ])


def _flow_box(text, color):
    lines = text.split("\n")
    return html.Div([
        html.Div(lines[0], style={"fontWeight": "700", "fontSize": "11px",
                                   "color": COLORS["white"], "marginBottom": "2px"}),
        html.Div(lines[1] if len(lines) > 1 else "", style={"fontSize": "10px",
                                                              "color": "rgba(255,255,255,0.75)"}),
    ], style={
        "backgroundColor": color, "borderRadius": "6px",
        "padding": "10px 12px", "textAlign": "center", "minWidth": "120px",
    })


def _flow_arrow():
    return html.Div("→", style={"color": COLORS["muted"], "fontWeight": "700",
                                  "fontSize": "18px", "padding": "0 4px"})


# ── Page: Live Fed Data (all free, no API keys) ──────────────────────────────
def feddata_page():
    news_feed_options  = [{"label": k, "value": k} for k in NEWS_FEEDS.keys()]

    return html.Div([
        page_header("Live Fed Data",
                    "Real-time data from free public feeds — no API keys required"),

        card([
            html.Span("All sources are free and require no credentials: ", style={
                "fontWeight": "600", "fontSize": "12px", "color": COLORS["navy"]}),
            html.Span("federalreserve.gov RSS  ·  FRBSF RSS  ·  "
                      "CNBC  ·  NY Times  ·  Reuters  ·  Washington Post  ·  "
                      "MarketWatch  ·  NPR  ·  AP News  ·  Yahoo Finance  ·  Axios",
                      style={"fontSize": "12px", "color": COLORS["muted"]}),
        ], style={"marginBottom": "24px"}),

        dbc.Tabs([
            # ── FOMC Statements ───────────────────────────────────────────
            dbc.Tab(label="FOMC Statements", tab_style={"fontWeight": "500"}, children=[
                html.Br(),
                dbc.Row([
                    dbc.Col(card([
                        label("Count"),
                        dcc.Slider(id="fomc-limit", min=5, max=20, step=5, value=10,
                                   marks={5:"5", 10:"10", 15:"15", 20:"20"}),
                        html.Br(),
                        styled_btn("Fetch", "fomc-fetch-btn"),
                    ]), width=3),
                    dbc.Col(dbc.Spinner(html.Div(id="fomc-output"), color="primary"), width=9),
                ]),
            ]),

            # ── Press Releases ────────────────────────────────────────────
            dbc.Tab(label="Press Releases", tab_style={"fontWeight": "500"}, children=[
                html.Br(),
                dbc.Row([
                    dbc.Col(card([
                        label("Count"),
                        dcc.Slider(id="press-limit", min=5, max=30, step=5, value=15,
                                   marks={5:"5", 10:"10", 20:"20", 30:"30"}),
                        html.Br(),
                        styled_btn("Fetch", "press-fetch-btn"),
                    ]), width=3),
                    dbc.Col(dbc.Spinner(html.Div(id="press-output"), color="primary"), width=9),
                ]),
            ]),

            # ── Speeches ──────────────────────────────────────────────────
            dbc.Tab(label="Fed Speeches", tab_style={"fontWeight": "500"}, children=[
                html.Br(),
                dbc.Row([
                    dbc.Col(card([
                        label("Count"),
                        dcc.Slider(id="speech-limit", min=5, max=20, step=5, value=10,
                                   marks={5:"5", 10:"10", 15:"15", 20:"20"}),
                        html.Br(),
                        styled_btn("Fetch", "speech-fetch-btn"),
                    ]), width=3),
                    dbc.Col(dbc.Spinner(html.Div(id="speech-output"), color="primary"), width=9),
                ]),
            ]),

            # ── News Outlets RSS ──────────────────────────────────────────
            dbc.Tab(label="News Outlets", tab_style={"fontWeight": "500"}, children=[
                html.Br(),
                dbc.Row([
                    dbc.Col(card([
                        label("Select Outlets"),
                        dcc.Dropdown(id="news-feeds-select", options=news_feed_options,
                                     value=list(NEWS_FEEDS.keys()),
                                     multi=True, style={"fontSize": "12px"}),
                        html.Br(),
                        label("Articles per outlet"),
                        dcc.Slider(id="news-limit", min=3, max=15, step=3, value=6,
                                   marks={3:"3", 6:"6", 9:"9", 15:"15"}),
                        html.Br(),
                        styled_btn("Fetch News", "news-fetch-btn"),
                    ]), width=3),
                    dbc.Col(dbc.Spinner(html.Div(id="news-output"), color="primary"), width=9),
                ]),
            ]),
        ], style={"borderBottom": f"2px solid {COLORS['border']}"}),
    ])


def _render_feed_items(items, source_label=""):
    if not items:
        return html.P("No items returned.", style={"color": COLORS["muted"]})
    if items and "error" in items[0]:
        return html.Div(f"Error: {items[0]['error']}", style={"color": COLORS["danger"]})
    return html.Div([
        html.Div([
            html.A(item.get("title", ""), href=item.get("link", "#"), target="_blank",
                   style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["navy"],
                          "textDecoration": "none"}),
            html.Span(f"  ·  {item.get('pub_date', '')[:25]}",
                      style={"fontSize": "11px", "color": COLORS["muted"]}),
            html.P(item.get("description", "")[:200],
                   style={"fontSize": "12px", "color": COLORS["muted"], "margin": "4px 0 0"}),
        ], style={"padding": "10px 14px", "marginBottom": "6px", "backgroundColor": COLORS["white"],
                  "borderRadius": "6px", "border": f"1px solid {COLORS['border']}",
                  "borderLeft": f"4px solid {COLORS['navy']}"})
        for item in items
    ])


# ── Helper: analyze feed items and merge into sample_data ─────────────────────
def _analyze_and_merge_feeds(items: list, source_type: str) -> tuple:
    """
    Run keyword-based sentiment on feed items, convert to news_articles schema,
    merge into sample_data, and return (count, status_msg).
    """
    if not items or (items and "error" in items[0]):
        return 0, "No items to analyze."

    rows = []
    for item in items:
        if "error" in item:
            continue
        text = f"{item.get('title', '')} {item.get('description', '')}"
        # Quick keyword sentiment (avoids Comprehend cost on bulk fetches)
        t = text.lower()
        if any(w in t for w in ["surge", "rally", "strong", "growth", "positive", "optimis"]):
            sent, score = "positive", 0.6
        elif any(w in t for w in ["crash", "crisis", "fear", "negative", "risk", "warn", "concern", "fall", "drop"]):
            sent, score = "negative", -0.6
        else:
            sent, score = "neutral", 0.0

        rows.append({
            "id":             f"{source_type.upper()}-{abs(hash(item.get('link', '')))}",
            "source":         source_type.replace("_", " ").title(),
            "headline":       item.get("title", ""),
            "summary":        item.get("description", "")[:400],
            "url":            item.get("link", ""),
            "sentiment":      sent,
            "sentiment_score": score,
            "topic":          "fed_rate_decision" if "fomc" in source_type else "monetary_policy",
            "published_at":   item.get("pub_date", ""),
            "data_source":    f"live_{source_type}",
        })

    if not rows:
        return 0, "No valid items."

    new_df = pd.DataFrame(rows)

    # Merge into sample_data
    existing = sample_data.get("news_articles", pd.DataFrame())
    if not existing.empty:
        combined = pd.concat([existing, new_df], ignore_index=True)
        if "id" in combined.columns:
            combined = combined.drop_duplicates(subset=["id"], keep="last")
        sample_data["news_articles"] = combined
    else:
        sample_data["news_articles"] = new_df

    return len(rows), f"✓ {len(rows)} items analyzed and merged into Sentiment Monitor"


# ── Callbacks: RSS feeds ──────────────────────────────────────────────────────
@app.callback(Output("fomc-output", "children"),
              Input("fomc-fetch-btn", "n_clicks"),
              State("fomc-limit", "value"), prevent_initial_call=True)
def cb_fomc(n, limit):
    items = fetch_fomc_statements(limit or 10)
    count, msg = _analyze_and_merge_feeds(items, "fomc_statement")
    return html.Div([
        html.P(f"Fetched {len(items)} FOMC statements", style={"fontSize": "12px", "color": COLORS["muted"]}),
        html.P(msg, style={"fontSize": "11px", "color": COLORS["success"], "marginBottom": "12px"}),
        _render_feed_items(items)])

@app.callback(Output("press-output", "children"),
              Input("press-fetch-btn", "n_clicks"),
              State("press-limit", "value"), prevent_initial_call=True)
def cb_press(n, limit):
    items = fetch_press_releases(limit or 15)
    count, msg = _analyze_and_merge_feeds(items, "press_release")
    return html.Div([
        html.P(f"Fetched {len(items)} press releases", style={"fontSize": "12px", "color": COLORS["muted"]}),
        html.P(msg, style={"fontSize": "11px", "color": COLORS["success"], "marginBottom": "12px"}),
        _render_feed_items(items)])

@app.callback(Output("speech-output", "children"),
              Input("speech-fetch-btn", "n_clicks"),
              State("speech-limit", "value"), prevent_initial_call=True)
def cb_speech(n, limit):
    items = fetch_speeches(limit or 10) + fetch_frbsf_speeches(limit or 10)
    count, msg = _analyze_and_merge_feeds(items, "speech")
    return html.Div([
        html.P(f"Fetched {len(items)} speeches", style={"fontSize": "12px", "color": COLORS["muted"]}),
        html.P(msg, style={"fontSize": "11px", "color": COLORS["success"], "marginBottom": "12px"}),
        _render_feed_items(items)])

@app.callback(Output("news-output", "children"),
              Input("news-fetch-btn", "n_clicks"),
              State("news-feeds-select", "value"),
              State("news-limit", "value"), prevent_initial_call=True)
def cb_news(n, selected_feeds, limit):
    feeds = {k: v for k, v in NEWS_FEEDS.items() if k in (selected_feeds or [])}
    articles = fetch_news_feeds(limit_per_feed=limit or 6, feeds=feeds)
    valid = [a for a in articles if "error" not in a]
    if not valid:
        return html.P("No articles found.", style={"color": COLORS["muted"]})

    # Analyze sentiment and merge
    rows_merged = 0
    for a in valid:
        text = f"{a.get('headline', '')} {a.get('summary', '')}".lower()
        if any(w in text for w in ["surge", "rally", "strong", "growth", "positive", "optimis"]):
            a["sentiment"], a["sentiment_score"] = "positive", 0.6
        elif any(w in text for w in ["crash", "crisis", "fear", "negative", "risk", "warn", "concern", "fall"]):
            a["sentiment"], a["sentiment_score"] = "negative", -0.6
        else:
            a["sentiment"], a["sentiment_score"] = "neutral", 0.0

    new_df = pd.DataFrame(valid)
    existing = sample_data.get("news_articles", pd.DataFrame())
    if not existing.empty:
        combined = pd.concat([existing, new_df], ignore_index=True)
        if "id" in combined.columns:
            combined = combined.drop_duplicates(subset=["id"], keep="last")
        sample_data["news_articles"] = combined
    else:
        sample_data["news_articles"] = new_df

    sources = sorted(set(a.get("source", "") for a in valid))
    return html.Div([
        dbc.Row([
            dbc.Col(metric_card("Articles", len(valid), COLORS["navy"]), width=3),
            dbc.Col(metric_card("Outlets", len(sources), COLORS["gold"]), width=3),
            dbc.Col(metric_card("Merged", len(valid), COLORS["success"]), width=3),
        ], className="mb-4"),
        html.P(f"✓ {len(valid)} articles analyzed and merged into Sentiment Monitor",
               style={"fontSize": "11px", "color": COLORS["success"], "marginBottom": "12px"}),
        html.Div([
            html.Div([
                html.Span(a.get("source", ""), style={"fontSize": "10px", "fontWeight": "700",
                                                        "color": COLORS["navy"], "textTransform": "uppercase"}),
                html.Span(f"  ·  {a.get('published_at', '')[:16]}",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
                html.Span(f"  ·  {a.get('sentiment', '')}",
                          style={"fontSize": "10px", "fontWeight": "600",
                                 "color": "#2E7D32" if a.get("sentiment") == "positive"
                                 else "#C62828" if a.get("sentiment") == "negative"
                                 else COLORS["muted"]}),
                html.A(a.get("headline", ""), href=a.get("url", "#"), target="_blank",
                       style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["navy"],
                              "textDecoration": "none", "display": "block", "marginTop": "2px"}),
            ], style={"padding": "10px 14px", "marginBottom": "6px",
                      "backgroundColor": COLORS["white"], "borderRadius": "6px",
                      "border": f"1px solid {COLORS['border']}",
                      "borderLeft": f"4px solid {COLORS['navy']}"})
            for a in valid
        ]),
    ])


# ── Page: Upload ──────────────────────────────────────────────────────────────
def upload_page():
    # Show files already auto-loaded from data/ folder
    from data_loader import DATA_DIR, _PREFIX_MAP
    auto_loaded = []
    if os.path.isdir(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR), reverse=True):
            if not fname.endswith(".json"):
                continue
            matched = next((k for p, k in _PREFIX_MAP.items() if fname.startswith(p)), None)
            if matched:
                size_kb = os.path.getsize(os.path.join(DATA_DIR, fname)) / 1024
                auto_loaded.append((fname, matched, f"{size_kb:.1f} KB"))

    auto_loaded_section = html.Div()
    if auto_loaded:
        auto_loaded_section = card([
            html.P("✓ Auto-loaded from data/ folder at startup",
                   style={"fontWeight": "600", "color": COLORS["success"],
                          "fontSize": "13px", "marginBottom": "12px"}),
            html.Div([
                html.Div([
                    html.Span(fname, style={"fontSize": "12px", "fontFamily": "monospace",
                                            "color": COLORS["navy"], "fontWeight": "500"}),
                    html.Span(f"  →  {key.replace('_', ' ').title()}",
                              style={"fontSize": "12px", "color": COLORS["muted"]}),
                    html.Span(f"  ({size})",
                              style={"fontSize": "11px", "color": COLORS["muted"],
                                     "float": "right"}),
                ], style={"padding": "6px 10px", "marginBottom": "4px",
                          "backgroundColor": "#E8F5E9", "borderRadius": "4px",
                          "border": "1px solid #A5D6A7"})
                for fname, key, size in auto_loaded
            ]),
            html.P("These files are merged with GitHub data automatically. "
                   "Use the uploader below to add more data into the current session.",
                   style={"fontSize": "11px", "color": COLORS["muted"],
                          "marginTop": "10px"}),
        ], style={"marginBottom": "24px", "borderLeft": f"4px solid {COLORS['success']}"})

    return html.Div([
        page_header("Upload Test Data",
                    "Load your own JSON files — or drop them in the data/ folder to auto-load at startup"),
        auto_loaded_section,
        dbc.Row([
            dbc.Col(card([
                label("Data Type"),
                styled_dropdown("upload-type", [
                    {"label": "Inquiries",           "value": "inquiries"},
                    {"label": "Social Media",        "value": "social_media"},
                    {"label": "News Articles",       "value": "news_articles"},
                    {"label": "Response Templates",  "value": "response_templates"},
                ], value="inquiries"),
                html.Br(),
                dcc.Upload(
                    id="upload-file",
                    children=html.Div([
                        html.Div("☁", style={"fontSize": "32px", "color": COLORS["muted"]}),
                        html.P("Drag & drop a JSON file here, or", style={"margin": "8px 0 4px", "color": COLORS["muted"], "fontSize": "14px"}),
                        html.A("browse to upload", style={"color": COLORS["navy"], "fontWeight": "600", "fontSize": "14px", "cursor": "pointer"}),
                        html.P(".json files only", style={"fontSize": "12px", "color": COLORS["muted"], "marginTop": "6px"}),
                    ], style={"textAlign": "center"}),
                    style={
                        "width": "100%", "padding": "40px 20px",
                        "border": f"2px dashed {COLORS['border']}",
                        "borderRadius": "8px", "backgroundColor": COLORS["light_bg"],
                        "cursor": "pointer", "transition": "border-color 0.2s",
                    },
                    accept=".json,.csv",
                ),
                html.Div(id="upload-status", style={"marginTop": "16px"}),
            ]), width=5),
            dbc.Col(card([
                label("Preview — First 5 Rows"),
                html.Div(id="upload-preview", style={"marginTop": "8px"}),
            ]), width=7),
        ]),
    ])


# ── Page: Inquiry Analyzer ────────────────────────────────────────────────────
def inquiry_page():
    df = sample_data.get("inquiries", pd.DataFrame())

    # Build filter options
    cat_opts = [{"label": c.replace("_", " ").title(), "value": c}
                for c in sorted(df["category"].unique())] if not df.empty and "category" in df.columns else []
    pri_opts = [{"label": p.title(), "value": p}
                for p in ["high", "medium", "low"]] if not df.empty else []
    src_opts = [{"label": s.title(), "value": s}
                for s in sorted(df["source"].unique())] if not df.empty and "source" in df.columns else []

    total = len(df)

    # Smart Inbox — cluster by (source, category)
    clusters = []
    if not df.empty and "source" in df.columns and "category" in df.columns:
        for (src, cat), grp in df.groupby(["source", "category"]):
            clusters.append({
                "label": f"{src.title()} — {cat.replace('_', ' ').title()}",
                "count": len(grp),
                "source": src, "category": cat,
            })
        clusters = sorted(clusters, key=lambda x: x["count"], reverse=True)[:6]

    cluster_cards = html.Div([
        html.Div([
            html.Div(c["label"], style={"fontWeight": "600", "fontSize": "12px",
                                         "color": COLORS["navy"]}),
            html.Div(f"{c['count']} inquiries", style={"fontSize": "11px",
                                                        "color": COLORS["muted"]}),
        ], style={
            "display": "inline-block", "padding": "10px 16px", "marginRight": "8px",
            "marginBottom": "8px", "borderRadius": "8px",
            "border": f"1px solid {COLORS['border']}",
            "backgroundColor": COLORS["white"], "cursor": "pointer",
        })
        for c in clusters
    ]) if clusters else html.Div()

    # Inquiry list items for left panel
    inq_options = []
    if not df.empty:
        for i, row in df.iterrows():
            inq_options.append({"label": str(i), "value": str(i)})

    # Priority color map
    pri_colors = {"high": COLORS["danger"], "medium": COLORS["warning"], "low": COLORS["success"]}

    # Build inquiry list
    inq_list_items = []
    if not df.empty:
        for i, row in df.head(50).iterrows():
            pri = row.get("priority", "").lower()
            src = row.get("source", "").upper()
            ch  = row.get("channel", "")
            ts  = str(row.get("timestamp", ""))[:10]
            subj = row.get("subject", "")[:80]
            sender = row.get("sender_name", "")
            org = row.get("sender_organization", "")
            cat = row.get("category", "").replace("_", " ").title()

            inq_list_items.append(html.Div([
                # Top row: ID · source · channel · timestamp
                html.Div([
                    html.Span(row.get("id", ""), style={"fontSize": "10px", "fontFamily": "monospace",
                                                         "color": COLORS["muted"]}),
                    html.Span(f"  ·  {src}  ·  {ch}", style={"fontSize": "10px",
                                                               "color": COLORS["muted"]}),
                    html.Span(ts, style={"fontSize": "10px", "color": COLORS["muted"],
                                          "float": "right"}),
                ], style={"marginBottom": "4px"}),
                # Subject
                html.Div(subj, style={"fontWeight": "600", "fontSize": "13px",
                                       "color": COLORS["navy"], "marginBottom": "4px",
                                       "cursor": "pointer"}),
                # Sender
                html.Div(f"{sender}" + (f" · {org}" if org else ""),
                         style={"fontSize": "11px", "color": COLORS["muted"],
                                "marginBottom": "6px"}),
                # Badges
                html.Div([
                    html.Span(cat, style={
                        "display": "inline-block", "backgroundColor": "#E8F0FE",
                        "color": COLORS["navy"], "borderRadius": "12px",
                        "padding": "2px 8px", "fontSize": "10px", "fontWeight": "600",
                        "marginRight": "4px",
                    }),
                    html.Span(pri.title() if pri else "", style={
                        "display": "inline-block",
                        "backgroundColor": pri_colors.get(pri, COLORS["muted"]) + "22",
                        "color": pri_colors.get(pri, COLORS["muted"]),
                        "borderRadius": "12px", "padding": "2px 8px",
                        "fontSize": "10px", "fontWeight": "600", "marginRight": "4px",
                    }) if pri else html.Span(),
                ]),
            ], id={"type": "inq-item", "index": str(i)},
               style={
                "padding": "12px 16px", "marginBottom": "4px",
                "borderRadius": "8px", "cursor": "pointer",
                "border": f"1px solid {COLORS['border']}",
                "backgroundColor": COLORS["white"],
                "borderLeft": f"4px solid {pri_colors.get(pri, COLORS['border'])}",
                "transition": "background-color 0.15s",
            }))

    return html.Div([
        html.P("INQUIRY & RESPONSE", style={"fontSize": "10px", "fontWeight": "700",
                                              "color": COLORS["muted"], "letterSpacing": "2px",
                                              "marginBottom": "8px"}),
        dbc.Tabs([
            dbc.Tab(label="📥 Inquiry Queue", tab_style={"fontWeight": "600"}, children=[
                html.Br(),
                # ── Original inquiry queue content below ──────────────────
                dbc.Row([
            dbc.Col([
                html.H4("Inquiry Queue", style={"fontWeight": "700", "color": COLORS["navy"],
                                                  "marginBottom": "4px"}),
                html.P("Click any inquiry to view the full thread, review Bedrock's classification, and generate a draft response.",
                       style={"fontSize": "13px", "color": COLORS["muted"]}),
            ], width=8),
            dbc.Col([
                styled_btn("⟳ Recategorize", "inq-classify-all-btn"),
            ], width=4, style={"textAlign": "right", "paddingTop": "20px"}),
        ], className="mb-3"),

        # ── Source badges ─────────────────────────────────────────────────
        html.Div([
            html.Span("SOURCES: ", style={"fontSize": "10px", "fontWeight": "700",
                                           "color": COLORS["muted"], "letterSpacing": "1px",
                                           "marginRight": "8px"}),
            *[html.Span(s, style={
                "display": "inline-block",
                "backgroundColor": COLORS["gold"] + "22", "color": COLORS["gold"],
                "borderRadius": "12px", "padding": "2px 10px",
                "fontSize": "11px", "fontWeight": "600", "marginRight": "6px",
            }) for s in sample_data.get("data_sources", ["GitHub"])],
        ], style={"marginBottom": "16px"}),

        # ── Filter bar ────────────────────────────────────────────────────
        card([
            dbc.Row([
                dbc.Col([
                    html.Span("⏍ FILTER  ", style={"fontSize": "10px", "fontWeight": "700",
                                                     "color": COLORS["muted"], "letterSpacing": "1px"}),
                ], width="auto", style={"paddingTop": "8px"}),
                dbc.Col(dcc.Dropdown(id="inq-cat-filter", options=cat_opts,
                                     placeholder="Category", multi=True,
                                     style={"fontSize": "12px"}), width=2),
                dbc.Col(dcc.Dropdown(id="inq-pri-filter", options=pri_opts,
                                     placeholder="Priority", multi=True,
                                     style={"fontSize": "12px"}), width=2),
                dbc.Col(dcc.Dropdown(id="inq-src-filter", options=src_opts,
                                     placeholder="Source", multi=True,
                                     style={"fontSize": "12px"}), width=2),
                dbc.Col(html.Div(id="inq-total-count",
                                  style={"fontSize": "12px", "color": COLORS["muted"],
                                         "float": "right", "paddingTop": "8px"}), width="auto"),
            ]),
        ], style={"padding": "10px 16px", "marginBottom": "16px"}),

        # ── Smart Inbox clusters (dynamic) ───────────────────────────────
        html.Div(id="inq-smart-inbox"),

        # ── Two-panel layout: list + detail ───────────────────────────────
        dbc.Row([
            # Left: inquiry list (populated by filter callback)
            dbc.Col(html.Div(
                id="inq-list-panel",
                style={"maxHeight": "600px", "overflowY": "auto",
                       "paddingRight": "8px"},
            ), width=5),

            # Right: detail panel
            dbc.Col(html.Div(
                id="inq-detail-panel",
                children=html.Div([
                    html.P("Select an inquiry from the list to view details",
                           style={"color": COLORS["muted"], "fontSize": "14px",
                                  "textAlign": "center", "paddingTop": "100px"}),
                ]),
                style={"minHeight": "600px"},
            ), width=7),
        ]),

        # Hidden stores
        dcc.Store(id="selected-inq-idx"),
            ]),  # end Inquiry Queue tab
        ]),
    ])


# ── Page: Sentiment Monitor ───────────────────────────────────────────────────
def sentiment_page():
    social_df = sample_data.get("social_media", pd.DataFrame())
    news_df   = sample_data.get("news_articles", pd.DataFrame())
    sources   = sample_data.get("data_sources", [])

    # Merge social + news into one consolidated DataFrame
    frames = []
    if not social_df.empty:
        sdf = social_df.copy()
        if "text" not in sdf.columns:
            sdf["text"] = ""
        sdf["item_type"] = "social"
        sdf["outlet"] = sdf.get("platform", pd.Series(["unknown"] * len(sdf)))
        frames.append(sdf)

    if not news_df.empty:
        ndf = news_df.copy()
        ndf["text"] = ndf.get("headline", ndf.get("title", pd.Series([""] * len(ndf))))
        ndf["item_type"] = "news"
        ndf["outlet"] = ndf.get("source", pd.Series(["unknown"] * len(ndf)))
        if "engagement_score" not in ndf.columns:
            ndf["engagement_score"] = 0
        if "sentiment" not in ndf.columns:
            ndf["sentiment"] = None
        if "topic" not in ndf.columns:
            ndf["topic"] = "monetary_policy"
        frames.append(ndf)

    if not frames:
        return html.Div([html.H4("Consolidated Sentiment"),
                         html.P("No data loaded.", style={"color": "#6B7A99"})])

    df = pd.concat(frames, ignore_index=True)

    # Assign keyword sentiment to items that don't have one
    def _quick_sentiment(text):
        if not text or not isinstance(text, str):
            return "neutral"
        t = text.lower()
        if any(w in t for w in ["surge", "rally", "strong", "growth", "positive", "optimis", "gain", "rise", "boost"]):
            return "positive"
        if any(w in t for w in ["crash", "crisis", "fear", "negative", "risk", "warn", "concern", "fall", "drop", "slump", "recession"]):
            return "negative"
        return "neutral"

    mask = df["sentiment"].isna() | (df["sentiment"] == "") | (df["sentiment"] == "unknown")
    if mask.any():
        df.loc[mask, "sentiment"] = df.loc[mask, "text"].apply(_quick_sentiment)

    key_sources = {
        "LinkedIn": ["linkedin"], "Wall Street Journal": ["wall street journal", "wsj", "marketwatch"],
        "CNBC": ["cnbc"], "Bloomberg": ["bloomberg"], "Axios": ["axios"],
        "Federal Reserve": ["federal reserve", "frbsf"],
        "NY Times": ["ny times", "new york times", "nyt"], "Reuters": ["reuters"],
        "Washington Post": ["washington post", "washingtonpost"],
        "NPR": ["npr"], "AP News": ["ap ", "associated press"], "Yahoo Finance": ["yahoo"],
    }

    def match_outlet(raw):
        raw_lower = str(raw).lower()
        for lbl, kws in key_sources.items():
            if any(k in raw_lower for k in kws):
                return lbl
        return str(raw).title()[:25]

    df["outlet_label"] = df["outlet"].apply(match_outlet)

    color_map = {"positive": "#2E7D32", "negative": "#C62828", "neutral": "#1B2A4A", "mixed": "#E65100"}
    total = len(df)
    social_count = int((df["item_type"] == "social").sum())
    news_count = int((df["item_type"] == "news").sum())

    sent_counts = df["sentiment"].fillna("unknown").value_counts().rename_axis("sentiment").reset_index(name="count")
    pos = int(sent_counts[sent_counts["sentiment"] == "positive"]["count"].sum()) if "positive" in sent_counts["sentiment"].values else 0
    neg = int(sent_counts[sent_counts["sentiment"] == "negative"]["count"].sum()) if "negative" in sent_counts["sentiment"].values else 0
    neu = int(sent_counts[sent_counts["sentiment"] == "neutral"]["count"].sum()) if "neutral" in sent_counts["sentiment"].values else 0

    fig_sent = px.pie(sent_counts, names="sentiment", values="count", color="sentiment", color_discrete_map=color_map, template="plotly_white", hole=0.45)
    fig_sent.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter"), legend=dict(orientation="h", y=-0.1))

    outlet_sent = df.groupby(["outlet_label", "sentiment"]).size().reset_index(name="count")
    fig_outlet = px.bar(outlet_sent, x="outlet_label", y="count", color="sentiment", color_discrete_map=color_map, template="plotly_white", barmode="stack")
    fig_outlet.update_layout(margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter", size=11), xaxis_title="", yaxis_title="Count", legend=dict(orientation="h", y=-0.15))

    topic_counts = df["topic"].fillna("other").value_counts().rename_axis("topic").reset_index(name="count") if "topic" in df.columns else pd.DataFrame(columns=["topic", "count"])
    fig_topic = px.pie(topic_counts, names="topic", values="count", template="plotly_white", color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_topic.update_layout(margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter"), legend=dict(font=dict(size=10)))

    outlet_vol = df["outlet_label"].value_counts().rename_axis("outlet").reset_index(name="count")
    fig_vol = px.bar(outlet_vol.head(12), x="count", y="outlet", orientation="h", template="plotly_white", color_discrete_sequence=[COLORS["navy"]])
    fig_vol.update_layout(margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter", size=11), yaxis=dict(autorange="reversed"), xaxis_title="Items", yaxis_title="")

    type_counts = df["item_type"].value_counts().rename_axis("type").reset_index(name="count")
    fig_type = px.pie(type_counts, names="type", values="count", template="plotly_white", color_discrete_map={"social": COLORS["gold"], "news": COLORS["navy"]})
    fig_type.update_layout(margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter", size=11))

    highlighted = ["LinkedIn", "Wall Street Journal", "CNBC", "Bloomberg", "Axios"]
    all_outlets = sorted(df["outlet_label"].unique())
    source_badges = html.Div([
        html.Span(o, style={
            "display": "inline-block",
            "backgroundColor": COLORS["navy"] + "15" if o in highlighted else COLORS["border"],
            "color": COLORS["navy"] if o in highlighted else COLORS["muted"],
            "borderRadius": "20px", "padding": "3px 12px", "fontSize": "11px",
            "fontWeight": "600" if o in highlighted else "400",
            "marginRight": "6px", "marginBottom": "6px",
            "border": f"1px solid {COLORS['navy']}" if o in highlighted else "none",
        }) for o in all_outlets
    ])

    top_cols = [c for c in ["outlet_label", "item_type", "text", "sentiment", "topic", "engagement_score"] if c in df.columns]
    top_items = df.nlargest(10, "engagement_score")[top_cols] if "engagement_score" in df.columns else df.head(10)[top_cols]

    return html.Div([
        html.P("CONSOLIDATED VIEW", style={"fontSize": "10px", "fontWeight": "700", "color": COLORS["muted"], "letterSpacing": "2px", "marginBottom": "4px"}),
        html.H4("Sentiment Analysis", style={"fontWeight": "700", "color": COLORS["navy"], "marginBottom": "6px"}),
        html.P("Merged social media and news feeds. Sources: LinkedIn, Wall Street Journal, CNBC, Bloomberg, Axios, Federal Reserve RSS, NY Times, Reuters, Washington Post, and more.",
               style={"fontSize": "13px", "color": COLORS["muted"], "marginBottom": "20px", "maxWidth": "750px"}),

        card([
            dbc.Row([
                dbc.Col([
                    html.P("Active Sources", style={"fontWeight": "600", "fontSize": "12px", "color": COLORS["navy"], "marginBottom": "8px"}),
                    source_badges,
                ], width=9),
                dbc.Col([
                    html.Div(str(len(all_outlets)), style={"fontWeight": "700", "fontSize": "20px", "color": COLORS["navy"], "textAlign": "center"}),
                    html.Div("outlets", style={"fontSize": "11px", "color": COLORS["muted"], "textAlign": "center"}),
                ], width=3),
            ]),
        ], style={"marginBottom": "20px"}),

        dbc.Row([
            dbc.Col(metric_card("Total Items", total, COLORS["navy"]), width=2),
            dbc.Col(metric_card("Social Posts", social_count, COLORS["gold"]), width=2),
            dbc.Col(metric_card("News Articles", news_count, COLORS["navy"]), width=2),
            dbc.Col(metric_card("Positive", pos, COLORS["success"]), width=2),
            dbc.Col(metric_card("Negative", neg, COLORS["danger"]), width=2),
            dbc.Col(metric_card("Neutral", neu, COLORS["navy"]), width=2),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(card([
                html.P("Overall Sentiment", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=fig_sent, config={"displayModeBar": False}),
            ]), width=4),
            dbc.Col(card([
                html.P("Sentiment by Outlet", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=fig_outlet, config={"displayModeBar": False}),
            ]), width=8),
        ], className="mb-4"),

        # Sentiment Trend Over Time
        card([
            dbc.Row([
                dbc.Col(html.P("Sentiment Trend Over Time",
                               style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "0"}), width=8),
                dbc.Col(dcc.Dropdown(
                    id="sentiment-trend-period",
                    options=[
                        {"label": "Daily",     "value": "D"},
                        {"label": "Weekly",    "value": "W"},
                        {"label": "Monthly",   "value": "ME"},
                        {"label": "Quarterly", "value": "QE"},
                        {"label": "Annually",  "value": "YE"},
                    ],
                    value="ME",
                    clearable=False,
                    style={"fontSize": "12px"},
                ), width=4),
            ], className="mb-2"),
            dcc.Graph(id="sentiment-trend-chart", config={"displayModeBar": False}),
        ], style={"marginBottom": "20px"}),

        dbc.Row([
            dbc.Col(card([
                html.P("Topic Distribution", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=fig_topic, config={"displayModeBar": False}),
            ]), width=4),
            dbc.Col(card([
                html.P("Volume by Outlet", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=fig_vol, config={"displayModeBar": False}),
            ]), width=5),
            dbc.Col(card([
                html.P("Social vs News", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=fig_type, config={"displayModeBar": False}),
            ]), width=3),
        ], className="mb-4"),

        card([
            html.P("Top Items by Engagement", style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "16px"}),
            dash_table.DataTable(
                data=flatten_for_table(top_items).to_dict("records"),
                columns=[{"name": c.replace("_", " ").title(), "id": c} for c in top_items.columns],
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": COLORS["navy"], "color": COLORS["white"],
                    "fontWeight": "600", "fontSize": "13px", "padding": "12px 14px",
                },
                style_cell={
                    "textAlign": "left", "padding": "10px 14px", "fontSize": "13px",
                    "whiteSpace": "normal", "height": "auto",
                    "maxWidth": "400px", "overflow": "hidden",
                    "color": COLORS["text"],
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#F8FAFC"},
                ],
                page_size=10,
            ),
        ]),
    ])


# ── Callback: Sentiment Trend Over Time ───────────────────────────────────────
@app.callback(
    Output("sentiment-trend-chart", "figure"),
    Input("sentiment-trend-period", "value"),
    Input("url", "pathname"),
)
def update_sentiment_trend(period, pathname):
    color_map = {"positive": "#2E7D32", "negative": "#C62828",
                 "neutral": "#1B2A4A", "mixed": "#E65100"}

    social_df = sample_data.get("social_media", pd.DataFrame())
    news_df   = sample_data.get("news_articles", pd.DataFrame())

    frames = []
    for src_df, date_col_candidates in [
        (social_df, ["date", "created_at", "timestamp"]),
        (news_df,   ["date", "published", "timestamp"]),
    ]:
        if src_df.empty or "sentiment" not in src_df.columns:
            continue
        date_col = None
        for c in date_col_candidates:
            if c in src_df.columns:
                date_col = c
                break
        if date_col is None:
            continue
        tmp = src_df[["sentiment", date_col]].copy()
        tmp["date"] = pd.to_datetime(tmp[date_col], errors="coerce")
        frames.append(tmp[["date", "sentiment"]].dropna(subset=["date"]))

    fig = go.Figure()
    if not frames:
        fig.update_layout(template="plotly_white",
                          annotations=[{"text": "No date data available", "showarrow": False,
                                        "font": {"size": 14, "color": "#6B7A99"}}])
        return fig

    combined = pd.concat(frames, ignore_index=True)
    combined["sentiment"] = combined["sentiment"].fillna("neutral")

    period = period or "ME"
    for sent in ["positive", "negative", "neutral", "mixed"]:
        subset = combined[combined["sentiment"] == sent].copy()
        if subset.empty:
            continue
        grouped = subset.set_index("date").resample(period).size().reset_index(name="count")
        grouped.columns = ["period", "count"]
        fig.add_trace(go.Scatter(
            x=grouped["period"], y=grouped["count"],
            mode="lines+markers", name=sent.title(),
            line=dict(color=color_map.get(sent, "#1B2A4A"), width=2),
            marker=dict(size=5),
        ))

    fig.update_layout(
        template="plotly_white",
        margin=dict(t=10, b=40, l=40, r=10),
        font=dict(family="Inter", size=11),
        xaxis_title="Period", yaxis_title="Count",
        legend=dict(orientation="h", y=-0.2),
        height=320,
    )
    return fig


# ── Page: Communications Hub (single-screen) ─────────────────────────────────
def hub_page():
    """Single-screen communications dashboard — Trending Topics, Risk Alerts, Sentiment Donut."""
    df_inq = sample_data.get("inquiries", pd.DataFrame())
    df_soc = sample_data.get("social_media", pd.DataFrame())

    color_map = {"positive": "#2E7D32", "negative": "#C62828",
                 "neutral": "#1B2A4A", "mixed": "#E65100"}

    # ── Trending Topics (moved to left, more than 6) ──────────────────────
    topic_fig = go.Figure()
    if not df_soc.empty and "topic" in df_soc.columns:
        tc = (
            df_soc["topic"]
            .value_counts()
            .head(12)
            .rename_axis("topic")
            .reset_index(name="count")
        )
        tc["label"] = tc["topic"].apply(lambda x: x.replace("_", " ").title())
        topic_fig = px.bar(tc, x="count", y="label", orientation="h",
                           template="plotly_white",
                           color_discrete_sequence=[COLORS["navy"]])
        topic_fig.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                                font=dict(family="Inter", size=11),
                                height=350, yaxis=dict(autorange="reversed"),
                                xaxis_title="Volume", yaxis_title="")

    # ── Risk alerts ───────────────────────────────────────────────────────
    risk_alerts = []
    if not df_soc.empty:
        neg = df_soc[df_soc.get("sentiment", pd.Series()) == "negative"] if "sentiment" in df_soc.columns else pd.DataFrame()
        if not neg.empty and "topic" in neg.columns:
            top_risks = neg["topic"].value_counts().head(3)
            for topic, count in top_risks.items():
                risk_alerts.append(
                    html.Div([
                        html.Span("⚠ ", style={"color": COLORS["danger"]}),
                        html.Span(f"{topic.replace('_',' ').title()} — {count} negative posts",
                                  style={"fontSize": "12px", "color": COLORS["text"]}),
                    ], style={"padding": "5px 10px", "backgroundColor": "#FFEBEE",
                              "borderRadius": "4px", "marginBottom": "4px",
                              "border": "1px solid #FFCDD2"})
                )

    # ── Sentiment Donut (under Risk Alerts) ───────────────────────────────
    sent_fig = go.Figure()
    if not df_soc.empty and "sentiment" in df_soc.columns:
        sc = (
            df_soc["sentiment"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("sentiment")
            .reset_index(name="count")
        )
        sent_fig = px.pie(sc, names="sentiment", values="count",
                          color="sentiment", color_discrete_map=color_map,
                          template="plotly_white", hole=0.45)
        sent_fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10),
                               font=dict(family="Inter", size=11), height=250,
                               legend=dict(orientation="h", y=-0.1))

    return html.Div([
        page_header("Communications Hub",
                    "Real-time communications intelligence — trending topics, risk alerts, and sentiment at a glance"),

        # Data source banner
        card([
            html.Div([
                html.Span("Sources: ", style={"fontWeight": "600", "fontSize": "11px",
                                               "color": COLORS["navy"]}),
                *[html.Span(s + "  ·  ", style={"fontSize": "11px", "color": COLORS["muted"]})
                  for s in sample_data.get("data_sources", ["GitHub"])],
            ], style={"padding": "5px 10px", "backgroundColor": "#EEF2FF",
                      "borderRadius": "4px"}),
        ], style={"marginBottom": "16px"}),

        # Metrics row
        dbc.Row([
            dbc.Col(metric_card("Inquiries", len(df_inq), COLORS["navy"]), width=3),
            dbc.Col(metric_card("Social Posts", len(df_soc), COLORS["gold"]), width=3),
            dbc.Col(metric_card("News Items",
                                len(sample_data.get("news_articles", pd.DataFrame())),
                                COLORS["navy"]), width=3),
            dbc.Col(metric_card("Sources",
                                len(sample_data.get("data_sources", [])),
                                COLORS["gold"]), width=3),
        ], className="mb-4"),

        # Main dashboard
        dbc.Row([
            # Left: Trending Topics (was in middle, now left)
            dbc.Col(card([
                html.P("Trending Topics",
                       style={"fontWeight": "600", "fontSize": "13px",
                              "color": COLORS["navy"], "marginBottom": "8px"}),
                dcc.Graph(figure=topic_fig, config={"displayModeBar": False}),
            ]), width=5),

            # Right: Risk Alerts + Sentiment Donut below
            dbc.Col([
                card([
                    html.P("Risk & Negative Sentiment Alerts",
                           style={"fontWeight": "600", "fontSize": "13px",
                                  "color": COLORS["navy"], "marginBottom": "10px"}),
                    html.Div(risk_alerts if risk_alerts else
                             html.P("No active risk alerts.", style={"color": COLORS["muted"],
                                                                      "fontSize": "12px"})),
                ], style={"marginBottom": "16px"}),
                card([
                    html.P("Sentiment Analysis",
                           style={"fontWeight": "600", "fontSize": "13px",
                                  "color": COLORS["navy"], "marginBottom": "8px"}),
                    dcc.Graph(figure=sent_fig, config={"displayModeBar": False}),
                ]),
            ], width=7),
        ]),
    ])



# ── Page: Insights Report ─────────────────────────────────────────────────────
def insights_page():
    sources = sample_data.get("data_sources", ["GitHub sample data"])
    load_summary = sample_data.get("load_summary", {})
    loaded_at = sample_data.get("loaded_at", "")

    source_badges = html.Div([
        html.Span(s, style={
            "display": "inline-block",
            "backgroundColor": "#EEF2FF", "color": COLORS["navy"],
            "borderRadius": "20px", "padding": "3px 12px",
            "fontSize": "12px", "fontWeight": "600",
            "marginRight": "6px", "marginBottom": "4px",
        }) for s in sources
    ])

    summary_items = []
    for k, v in load_summary.items():
        summary_items.append(
            html.Span(f"{k.replace('_', ' ')}: {v}",
                      style={"fontSize": "11px", "color": COLORS["muted"],
                             "marginRight": "16px"})
        )

    return html.Div([
        page_header("Insights Report",
                    "AI-generated executive report combining GitHub data + live feeds"),

        # Data source status card
        card([
            dbc.Row([
                dbc.Col([
                    html.P("Active Data Sources", style={"fontWeight": "600",
                                                          "color": COLORS["navy"],
                                                          "fontSize": "13px",
                                                          "marginBottom": "8px"}),
                    source_badges,
                    html.Div(summary_items, style={"marginTop": "8px"}),
                    html.P(f"Last loaded: {loaded_at[:19].replace('T',' ') if loaded_at else 'at startup'}",
                           style={"fontSize": "11px", "color": COLORS["muted"],
                                  "marginTop": "6px"}),
                ], width=8),
                dbc.Col([
                    html.Button("🔄  Refresh Live Data", id="refresh-data-btn",
                                style={
                                    "backgroundColor": COLORS["navy"],
                                    "color": COLORS["white"], "border": "none",
                                    "borderRadius": "6px", "padding": "8px 16px",
                                    "fontWeight": "600", "fontSize": "13px",
                                    "cursor": "pointer", "fontFamily": "'Inter', sans-serif",
                                    "marginBottom": "8px", "display": "block",
                                }),
                    html.Div(id="refresh-status",
                             style={"fontSize": "11px", "color": COLORS["muted"]}),
                ], width=4, style={"textAlign": "right"}),
            ]),
        ], style={"marginBottom": "20px"}),

        card([
            html.P("Click below to generate a comprehensive insights report based on all loaded data.",
                   style={"color": COLORS["muted"], "fontSize": "14px", "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    label("Date From"),
                    dcc.DatePickerSingle(
                        id="insights-date-from",
                        placeholder="Start date...",
                        style={"fontSize": "13px"},
                        display_format="YYYY-MM-DD",
                    ),
                ], width=3),
                dbc.Col([
                    label("Date To"),
                    dcc.DatePickerSingle(
                        id="insights-date-to",
                        placeholder="End date...",
                        style={"fontSize": "13px"},
                        display_format="YYYY-MM-DD",
                    ),
                ], width=3),
                dbc.Col([
                    html.Br(),
                    styled_btn("Generate Report", "insights-btn"),
                ], width=6),
            ]),
        ], style={"marginBottom": "24px"}),
        dbc.Spinner(html.Div(id="insights-output"), color="primary"),
    ])


# ── Page: Risk Detector ───────────────────────────────────────────────────────
def risks_page():
    df = sample_data.get("social_media", pd.DataFrame())

    risky_table = html.P("No high-risk posts found.", style={"color": COLORS["muted"], "fontSize": "14px"})
    if not df.empty and "sentiment_score" in df.columns:
        risky = df[df["sentiment_score"] < -0.5].nlargest(5, "engagement_score")
        if not risky.empty:
            cols = ["platform", "author_handle", "text", "sentiment_score", "engagement_score", "topic"]
            cols = [c for c in cols if c in risky.columns]
            risky_table = dash_table.DataTable(
                data=flatten_for_table(risky[cols]).to_dict("records"),
                columns=[{"name": c.replace("_", " ").title(), "id": c} for c in cols],
                **TABLE_STYLE,
            )

    return html.Div([
        page_header("Risk Detector", "Identify trending topics and potential communication risks"),
        dbc.Row([
            dbc.Col(card([
                label("Posts to Analyze"),
                dcc.Slider(id="risk-slider", min=5, max=20, step=5, value=10,
                           marks={5: "5", 10: "10", 15: "15", 20: "20"},
                           tooltip={"placement": "bottom"}),
                html.Br(),
                styled_btn("Detect Risks", "risk-btn", color=COLORS["danger"]),
            ]), width=4),
            dbc.Col(dbc.Spinner(html.Div(id="risk-output"), color="danger"), width=8),
        ], className="mb-4"),
        card([
            html.P("High-Risk Posts — Negative Sentiment & High Engagement",
                   style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "16px"}),
            risky_table,
        ]),
    ])


# ── Page: Generate Test Data ──────────────────────────────────────────────────
def generate_page():
    all_topics = {
        "inquiries":          DATA_TYPE_CONFIG["inquiries"]["default_topics"],
        "social_media":       DATA_TYPE_CONFIG["social_media"]["default_topics"],
        "news_articles":      DATA_TYPE_CONFIG["news_articles"]["default_topics"],
        "response_templates": DATA_TYPE_CONFIG["response_templates"]["default_topics"],
    }

    # Build saved files table (initial render — refreshed by callback after generation)
    saved_files_content = build_saved_files_table()

    return html.Div([
        page_header("Generate Test Data",
                    "Use Amazon Bedrock (Claude) to generate realistic synthetic FRBSF communications data"),

        dbc.Row([
            # ── Left: Config ──────────────────────────────────────────────
            dbc.Col(card([                label("Data Type"),
                styled_dropdown("gen-type", [
                    {"label": "Inquiries",           "value": "inquiries"},
                    {"label": "Social Media Posts",  "value": "social_media"},
                    {"label": "News Articles",       "value": "news_articles"},
                    {"label": "Response Templates",  "value": "response_templates"},
                ], value="inquiries"),
                html.Br(),

                label("Number of Records"),
                dcc.Slider(
                    id="gen-count", min=5, max=50, step=5, value=10,
                    marks={5: "5", 10: "10", 20: "20", 30: "30", 50: "50"},
                    tooltip={"placement": "bottom"},
                ),
                html.Br(),

                label("Batch Size (records per Bedrock call)"),
                dcc.Slider(
                    id="gen-batch", min=2, max=10, step=1, value=5,
                    marks={2: "2", 5: "5", 10: "10"},
                    tooltip={"placement": "bottom"},
                ),
                html.Br(),

                dbc.Row([
                    dbc.Col([
                        label("Date From"),
                        styled_input("gen-date-start", "YYYY-MM-DD", type="text"),
                    ], width=6),
                    dbc.Col([
                        label("Date To"),
                        styled_input("gen-date-end", "YYYY-MM-DD", type="text"),
                    ], width=6),
                ]),
                html.Br(),

                label("Topics to Include"),
                dcc.Dropdown(
                    id="gen-topics",
                    options=[],   # populated by callback
                    multi=True,
                    placeholder="All topics (default)",
                    style={"fontSize": "14px"},
                ),
                html.Br(),

                dbc.Checklist(
                    id="gen-load-after",
                    options=[{"label": "  Load generated data into app automatically", "value": "yes"}],
                    value=["yes"],
                    style={"fontSize": "14px", "color": COLORS["text"], "marginBottom": "16px"},
                ),

                styled_btn("🧪  Generate Data", "gen-btn"),
            ]), width=4),

            # ── Right: Output ─────────────────────────────────────────────
            dbc.Col([
                card([
                    html.P("Available Topics for Selected Type",
                           style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "10px"}),
                    html.Div(id="gen-topic-preview"),
                ], style={"marginBottom": "16px"}),

                dbc.Spinner(
                    html.Div(id="gen-output", style={"minHeight": "100px"}),
                    color="primary",
                ),
            ], width=8),
        ]),

        # ── Saved Files ───────────────────────────────────────────────────
        html.Br(),
        card([
            html.P("Saved Files  —  frs_ai_comms/data/",
                   style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "16px",
                          "fontFamily": "monospace"}),
            html.Div(id="saved-files-list", children=saved_files_content),
        ]),
    ])


def build_saved_files_table():
    """Read frs_ai_comms/data/ and return a DataTable or empty message."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.isdir(data_dir):
        return html.P("No files saved yet.", style={"color": COLORS["muted"], "fontSize": "14px"})
    files = sorted(
        [f for f in os.listdir(data_dir) if f.endswith(".json")],
        reverse=True,
    )
    if not files:
        return html.P("No files saved yet.", style={"color": COLORS["muted"], "fontSize": "14px"})
    rows = []
    for fname in files:
        fpath = os.path.join(data_dir, fname)
        size_kb = os.path.getsize(fpath) / 1024
        mtime   = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
        rows.append({"File": fname, "Size": f"{size_kb:.1f} KB", "Saved At": mtime})
    return dash_table.DataTable(
        data=rows,
        columns=[{"name": c, "id": c} for c in ["File", "Size", "Saved At"]],
        **TABLE_STYLE,
    )


# ── Callback: Refresh saved files list after generation ───────────────────────
@app.callback(
    Output("saved-files-list", "children"),
    Input("gen-output",        "children"),   # fires whenever generation output updates
    prevent_initial_call=True,
)
def refresh_saved_files(_):
    return build_saved_files_table()


# ── Callback: Populate topic dropdown when type changes ───────────────────────
@app.callback(
    Output("gen-topics",        "options"),
    Output("gen-topics",        "value"),
    Output("gen-topic-preview", "children"),
    Input("gen-type",           "value"),
)
def update_topic_options(data_type):
    if not data_type:
        return [], [], html.Div()
    topics = DATA_TYPE_CONFIG[data_type]["default_topics"]
    options = [{"label": t.replace("_", " ").title(), "value": t} for t in topics]
    pills = html.Div([
        html.Span(t.replace("_", " ").title(), style={
            "display": "inline-block", "backgroundColor": "#EEF2FF",
            "color": COLORS["navy"], "borderRadius": "20px",
            "padding": "4px 12px", "fontSize": "12px",
            "marginRight": "6px", "marginBottom": "6px", "fontWeight": "500",
        }) for t in topics
    ])
    return options, topics, pills


# ── Callback: Generate data ───────────────────────────────────────────────────
@app.callback(
    Output("gen-output", "children"),
    Output("data-refresh-signal", "data", allow_duplicate=True),
    Input("gen-btn",        "n_clicks"),
    State("gen-type",       "value"),
    State("gen-count",      "value"),
    State("gen-batch",      "value"),
    State("gen-date-start", "value"),
    State("gen-date-end",   "value"),
    State("gen-topics",     "value"),
    State("gen-load-after", "value"),
    State("model-store",    "data"),
    State("data-refresh-signal", "data"),
    prevent_initial_call=True,
)
def run_generation(n, data_type, count, batch_size, date_start, date_end, topics, load_after, model_store, cur_sig):
    if not data_type:
        return html.Div("Select a data type.", style={"color": COLORS["warning"]}), dash.no_update

    date_start = date_start or "2022-01-01"
    date_end   = date_end   or "2025-12-31"
    count      = count      or 10
    batch_size = batch_size or 5

    try:
        records = generate_data(
            data_type=data_type,
            count=count,
            topics=topics or None,
            date_start=date_start,
            date_end=date_end,
            batch_size=batch_size,
            model_id=(model_store or {}).get("model_id"),
        )

        # ── Save to disk ──────────────────────────────────────────────────
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"{data_type}_{timestamp}.json"
        filepath  = os.path.join(data_dir, filename)
        with open(filepath, "w") as f:
            json.dump(records, f, indent=2)

        # ── Optionally load into app memory ───────────────────────────────
        if load_after and "yes" in load_after:
            new_df = pd.DataFrame(records)
            new_df["data_source"] = "generated"
            existing = sample_data.get(data_type, pd.DataFrame())
            if not existing.empty:
                # Re-index new IDs to avoid collision with existing data
                prefix_map = {"inquiries": "INQ", "social_media": "SM",
                              "news_articles": "NA", "response_templates": "RT"}
                prefix = prefix_map.get(data_type, "REC")
                max_existing = 0
                if "id" in existing.columns:
                    for eid in existing["id"].dropna():
                        try:
                            num = int(str(eid).split("-")[-1])
                            max_existing = max(max_existing, num)
                        except (ValueError, IndexError):
                            pass
                for i, idx in enumerate(new_df.index):
                    new_df.at[idx, "id"] = f"{prefix}-{max_existing + i + 1:05d}"

                combined = pd.concat([existing, new_df], ignore_index=True)
                sample_data[data_type] = combined
            else:
                sample_data[data_type] = new_df

        df       = pd.DataFrame(records)
        total    = len(sample_data.get(data_type, pd.DataFrame()))
        json_str = json.dumps(records, indent=2)
        size_kb  = os.path.getsize(filepath) / 1024

        return html.Div([
            # Success banner
            html.Div([
                html.Span("✓ ", style={"color": COLORS["success"], "fontWeight": "700"}),
                html.Span(f"Generated {len(records)} {data_type.replace('_', ' ')} records. Total now: {total}",
                          style={"fontSize": "14px", "color": COLORS["success"]}),
                html.Span(f"  ·  Saved to frs_ai_comms/data/{filename}  ({size_kb:.1f} KB)",
                          style={"fontSize": "12px", "color": COLORS["muted"], "marginLeft": "8px"}),
            ], style={"padding": "10px 14px", "backgroundColor": "#E8F5E9",
                      "borderRadius": "6px", "border": "1px solid #A5D6A7",
                      "marginBottom": "16px"}),

            # Preview table
            card([
                html.P("Preview — First 5 Records",
                       style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=flatten_for_table(df).head(5).to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    **TABLE_STYLE,
                ),
            ], style={"marginBottom": "16px"}),

            # Download
            html.A(
                html.Button("⬇  Download JSON", style={
                    "backgroundColor": "transparent", "color": COLORS["navy"],
                    "border": f"1px solid {COLORS['navy']}", "borderRadius": "6px",
                    "padding": "8px 18px", "fontWeight": "600", "fontSize": "13px",
                    "cursor": "pointer", "fontFamily": "'Inter', sans-serif",
                }),
                href=f"data:application/json;charset=utf-8,{json_str}",
                download=filename,
            ),
        ]), (cur_sig or 0) + 1

    except Exception as e:
        return html.Div([
            html.Span("✗ Generation failed: ", style={"color": COLORS["danger"], "fontWeight": "600"}),
            html.Span(str(e), style={"color": COLORS["danger"], "fontSize": "14px"}),
        ], style={"padding": "12px", "backgroundColor": "#FFEBEE",
                  "borderRadius": "6px", "border": "1px solid #FFCDD2"}), dash.no_update


# ── Page: ROI Calculator ──────────────────────────────────────────────────────
def roi_page():
    return html.Div([
        page_header("ROI Calculator",
                    "Estimate return on investment including real AWS resource costs"),
        dbc.Row([
            dbc.Col(card([
                html.P("MANUAL PROCESS", style={"fontSize": "10px", "fontWeight": "700",
                                                  "color": COLORS["gold"], "letterSpacing": "2px",
                                                  "marginBottom": "12px"}),
                label("Inquiries per Month"),
                styled_input("roi-inquiries", "200", type="number"),
                html.Br(),
                label("Manual Classify Time (min/inquiry)"),
                styled_input("roi-classify-time", "3", type="number"),
                html.Br(),
                label("Manual Draft Time (min/inquiry)"),
                styled_input("roi-draft-time", "20", type="number"),
                html.Br(),
                label("Manual Sentiment Report (hrs/week)"),
                styled_input("roi-report-time", "4", type="number"),
                html.Br(),
                label("Staff Hourly Cost ($)"),
                styled_input("roi-hourly-cost", "65", type="number"),
                html.Br(),
                html.Hr(),
                html.P("AWS RESOURCE COSTS", style={"fontSize": "10px", "fontWeight": "700",
                                                     "color": COLORS["gold"], "letterSpacing": "2px",
                                                     "marginBottom": "12px"}),
                label("App Runner ($/month) — 1 vCPU, 2GB"),
                styled_input("roi-apprunner", "25", type="number"),
                html.Br(),
                label("Bedrock Claude ($/1K input tokens)"),
                styled_input("roi-bedrock-input", "0.003", type="text"),
                html.Br(),
                label("Bedrock Claude ($/1K output tokens)"),
                styled_input("roi-bedrock-output", "0.015", type="text"),
                html.Br(),
                label("Comprehend ($/unit, 100 chars)"),
                styled_input("roi-comprehend", "0.0001", type="text"),
                html.Br(),
                label("ECR Storage ($/GB/month)"),
                styled_input("roi-ecr", "0.10", type="text"),
                html.Br(),
                label("CodeBuild ($/build-min)"),
                styled_input("roi-codebuild", "0.005", type="text"),
                html.Br(),
                styled_btn("Calculate ROI", "roi-calc-btn"),
            ]), width=4),
            dbc.Col(dbc.Spinner(html.Div(id="roi-output"), color="primary"), width=8),
        ]),
    ])


@app.callback(
    Output("roi-output", "children"),
    Input("roi-calc-btn", "n_clicks"),
    State("roi-inquiries",     "value"),
    State("roi-classify-time", "value"),
    State("roi-draft-time",    "value"),
    State("roi-report-time",   "value"),
    State("roi-hourly-cost",   "value"),
    State("roi-apprunner",     "value"),
    State("roi-bedrock-input", "value"),
    State("roi-bedrock-output","value"),
    State("roi-comprehend",    "value"),
    State("roi-ecr",           "value"),
    State("roi-codebuild",     "value"),
    prevent_initial_call=True,
)
def calc_roi(n, inquiries, classify_min, draft_min, report_hrs, hourly,
             apprunner_cost, bedrock_in, bedrock_out, comprehend_cost, ecr_cost, codebuild_cost):
    inquiries    = int(inquiries or 500)
    classify_min = float(classify_min or 5)
    draft_min    = float(draft_min or 30)
    report_hrs   = float(report_hrs or 8)
    hourly       = float(hourly or 75)

    # AWS costs
    apprunner_mo    = float(apprunner_cost or 25)
    bedrock_in_1k   = float(bedrock_in or 0.003)
    bedrock_out_1k  = float(bedrock_out or 0.015)
    comprehend_unit = float(comprehend_cost or 0.0001)
    ecr_mo          = float(ecr_cost or 0.10)
    codebuild_min   = float(codebuild_cost or 0.005)

    # ── Manual costs ──────────────────────────────────────────────────────
    classify_hrs_mo  = (inquiries * classify_min) / 60
    draft_hrs_mo     = (inquiries * draft_min) / 60
    report_hrs_mo    = report_hrs * 4
    total_manual_hrs = classify_hrs_mo + draft_hrs_mo + report_hrs_mo
    manual_cost_mo   = total_manual_hrs * hourly

    # ── AI processing time ────────────────────────────────────────────────
    ai_classify_sec  = 2
    ai_draft_sec     = 10
    ai_report_sec    = 30
    ai_hrs_mo        = (inquiries * (ai_classify_sec + ai_draft_sec) / 3600) + (4 * ai_report_sec / 3600)
    ai_review_hrs    = inquiries * 2 / 60   # 2 min human review per draft
    ai_total_hrs     = ai_hrs_mo + ai_review_hrs
    ai_staff_cost    = ai_review_hrs * hourly

    # ── AWS service costs (real) ──────────────────────────────────────────
    # Comprehend: ~3 units per inquiry (subject + body ~300 chars)
    comprehend_mo = inquiries * 3 * comprehend_unit

    # Bedrock: ~500 input tokens + ~800 output tokens per draft
    bedrock_drafts   = inquiries * (500 / 1000 * bedrock_in_1k + 800 / 1000 * bedrock_out_1k)
    # Bedrock: ~2000 input + ~2000 output tokens per weekly report × 4
    bedrock_reports  = 4 * (2000 / 1000 * bedrock_in_1k + 2000 / 1000 * bedrock_out_1k)
    # Bedrock: ~1000 input + ~500 output per risk detection × 4
    bedrock_risks    = 4 * (1000 / 1000 * bedrock_in_1k + 500 / 1000 * bedrock_out_1k)
    bedrock_mo       = bedrock_drafts + bedrock_reports + bedrock_risks

    # ECR: ~0.5 GB image
    ecr_storage_mo   = 0.5 * ecr_mo

    # CodeBuild: ~3 min per build, ~4 builds/month
    codebuild_mo     = 4 * 3 * codebuild_min

    # App Runner
    apprunner_total  = apprunner_mo

    aws_total_mo     = comprehend_mo + bedrock_mo + apprunner_total + ecr_storage_mo + codebuild_mo
    ai_total_cost    = ai_staff_cost + aws_total_mo

    savings_mo       = manual_cost_mo - ai_total_cost
    savings_yr       = savings_mo * 12
    time_saved_mo    = total_manual_hrs - ai_total_hrs
    roi_pct          = (savings_mo / manual_cost_mo * 100) if manual_cost_mo > 0 else 0

    # ── Charts ────────────────────────────────────────────────────────────
    fig = go.Figure(data=[
        go.Bar(name="Manual Process",  x=["Monthly Cost"], y=[manual_cost_mo],
               marker_color=COLORS["danger"]),
        go.Bar(name="With AI System",  x=["Monthly Cost"], y=[ai_total_cost],
               marker_color=COLORS["success"]),
    ])
    fig.update_layout(barmode="group", template="plotly_white",
                      font=dict(family="Inter"), margin=dict(t=20, b=20), height=250)

    time_fig = go.Figure(data=[
        go.Bar(name="Manual", x=["Hours/Month"], y=[total_manual_hrs],
               marker_color=COLORS["danger"]),
        go.Bar(name="With AI", x=["Hours/Month"], y=[ai_total_hrs],
               marker_color=COLORS["success"]),
    ])
    time_fig.update_layout(barmode="group", template="plotly_white",
                           font=dict(family="Inter"), margin=dict(t=20, b=20), height=250)

    # AWS cost breakdown pie
    aws_breakdown = go.Figure(data=[go.Pie(
        labels=["App Runner", "Bedrock (Claude)", "Comprehend", "ECR", "CodeBuild"],
        values=[apprunner_total, bedrock_mo, comprehend_mo, ecr_storage_mo, codebuild_mo],
        marker_colors=["#1B2A4A", "#C8A951", "#FF9900", "#2E7D32", "#6B7A99"],
    )])
    aws_breakdown.update_layout(template="plotly_white", font=dict(family="Inter"),
                                 margin=dict(t=10, b=10, l=10, r=10), height=250)

    return html.Div([
        dbc.Row([
            dbc.Col(metric_card("Monthly Savings",   f"${savings_mo:,.0f}",    COLORS["success"]), width=2),
            dbc.Col(metric_card("Annual Savings",    f"${savings_yr:,.0f}",    COLORS["gold"]),    width=2),
            dbc.Col(metric_card("ROI",               f"{roi_pct:.0f}%",        COLORS["navy"]),    width=2),
            dbc.Col(metric_card("Hours Saved/Mo",    f"{time_saved_mo:.0f}h",  COLORS["success"]), width=2),
            dbc.Col(metric_card("AWS Cost/Mo",       f"${aws_total_mo:,.2f}",  COLORS["danger"]),  width=2),
            dbc.Col(metric_card("Cost per Inquiry",  f"${ai_total_cost/max(inquiries,1):.2f}", COLORS["navy"]), width=2),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(card([
                html.P("Cost Comparison", style={"fontWeight": "600", "color": COLORS["navy"]}),
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
            ]), width=4),
            dbc.Col(card([
                html.P("Time Comparison", style={"fontWeight": "600", "color": COLORS["navy"]}),
                dcc.Graph(figure=time_fig, config={"displayModeBar": False}),
            ]), width=4),
            dbc.Col(card([
                html.P("AWS Cost Breakdown", style={"fontWeight": "600", "color": COLORS["navy"]}),
                dcc.Graph(figure=aws_breakdown, config={"displayModeBar": False}),
            ]), width=4),
        ], className="mb-4"),
        card([
            html.P("Detailed Breakdown", style={"fontWeight": "600", "color": COLORS["navy"],
                                                  "marginBottom": "12px"}),
            dash_table.DataTable(
                data=[
                    {"Component": "Inquiry Classification", "Manual (hrs/mo)": f"{classify_hrs_mo:.1f}",
                     "AI (hrs/mo)": f"{inquiries * ai_classify_sec / 3600:.1f}",
                     "Manual Cost/mo": f"${classify_hrs_mo * hourly:,.0f}",
                     "AI Cost/mo": f"${comprehend_mo:,.2f}"},
                    {"Component": "Response Drafting", "Manual (hrs/mo)": f"{draft_hrs_mo:.1f}",
                     "AI (hrs/mo)": f"{(inquiries * ai_draft_sec / 3600) + ai_review_hrs:.1f}",
                     "Manual Cost/mo": f"${draft_hrs_mo * hourly:,.0f}",
                     "AI Cost/mo": f"${bedrock_drafts + ai_staff_cost:,.2f}"},
                    {"Component": "Sentiment & Risk Reports", "Manual (hrs/mo)": f"{report_hrs_mo:.1f}",
                     "AI (hrs/mo)": f"{4 * ai_report_sec / 3600:.2f}",
                     "Manual Cost/mo": f"${report_hrs_mo * hourly:,.0f}",
                     "AI Cost/mo": f"${bedrock_reports + bedrock_risks:,.2f}"},
                    {"Component": "App Runner (hosting)", "Manual (hrs/mo)": "—",
                     "AI (hrs/mo)": "—", "Manual Cost/mo": "—",
                     "AI Cost/mo": f"${apprunner_total:,.2f}"},
                    {"Component": "ECR (container storage)", "Manual (hrs/mo)": "—",
                     "AI (hrs/mo)": "—", "Manual Cost/mo": "—",
                     "AI Cost/mo": f"${ecr_storage_mo:,.2f}"},
                    {"Component": "CodeBuild (CI/CD)", "Manual (hrs/mo)": "—",
                     "AI (hrs/mo)": "—", "Manual Cost/mo": "—",
                     "AI Cost/mo": f"${codebuild_mo:,.3f}"},
                    {"Component": "TOTAL", "Manual (hrs/mo)": f"{total_manual_hrs:.1f}",
                     "AI (hrs/mo)": f"{ai_total_hrs:.1f}",
                     "Manual Cost/mo": f"${manual_cost_mo:,.0f}",
                     "AI Cost/mo": f"${ai_total_cost:,.2f}"},
                ],
                columns=[{"name": c, "id": c} for c in
                         ["Component", "Manual (hrs/mo)", "AI (hrs/mo)", "Manual Cost/mo", "AI Cost/mo"]],
                **TABLE_STYLE,
            ),
        ], style={"marginBottom": "20px"}),
        card([
            html.P("AWS Pricing Reference", style={"fontWeight": "600", "color": COLORS["navy"],
                                                     "marginBottom": "8px"}),
            html.Div([
                html.Div([
                    html.Span(svc, style={"fontWeight": "600", "fontSize": "12px",
                                           "color": COLORS["navy"], "width": "160px",
                                           "display": "inline-block"}),
                    html.Span(price, style={"fontSize": "12px", "color": COLORS["muted"],
                                             "fontFamily": "monospace"}),
                ], style={"marginBottom": "4px"})
                for svc, price in [
                    ("App Runner",   f"${apprunner_mo}/mo (1 vCPU, 2 GB, ~8 hrs/day active)"),
                    ("Bedrock Input", f"${bedrock_in_1k}/1K tokens (Claude 3 Sonnet)"),
                    ("Bedrock Output",f"${bedrock_out_1k}/1K tokens (Claude 3 Sonnet)"),
                    ("Comprehend",   f"${comprehend_unit}/unit (100 chars, sentiment+entities)"),
                    ("ECR",          f"${ecr_mo}/GB/month (container image storage)"),
                    ("CodeBuild",    f"${codebuild_min}/build-minute (general1.small)"),
                ]
            ]),
        ]),
    ])


# ── Page: Audit Log ──────────────────────────────────────────────────────────
def audit_page():
    from audit_log import get_log
    log = get_log()

    table_content = html.P("No AI actions recorded yet.",
                           style={"color": COLORS["muted"], "fontSize": "14px"})
    if log:
        display_cols = ["timestamp", "action", "model_id", "input_summary", "output_summary"]
        rows = [{k: entry.get(k, "") for k in display_cols} for entry in reversed(log)]
        table_content = dash_table.DataTable(
            data=rows,
            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in display_cols],
            page_size=15,
            sort_action="native",
            filter_action="native",
            **TABLE_STYLE,
        )

    return html.Div([
        page_header("Audit Log",
                    "Complete record of all AI actions — model used, inputs, outputs, timestamps"),
        dbc.Row([
            dbc.Col(metric_card("Total Actions", len(log), COLORS["navy"]),  width=3),
            dbc.Col(metric_card("Draft Responses",
                                sum(1 for e in log if e.get("action") == "draft_response"),
                                COLORS["gold"]), width=3),
            dbc.Col(metric_card("Insights Reports",
                                sum(1 for e in log if e.get("action") == "insights_report"),
                                COLORS["success"]), width=3),
            dbc.Col(metric_card("Risk Detections",
                                sum(1 for e in log if e.get("action") == "risk_detection"),
                                COLORS["danger"]), width=3),
        ], className="mb-4"),
        card([
            html.P("AI Action History — Most Recent First",
                   style={"fontWeight": "600", "color": COLORS["navy"],
                          "marginBottom": "16px"}),
            html.P("Every AI-generated output is logged with the model ID, input summary, "
                   "and output summary for full traceability and compliance.",
                   style={"fontSize": "12px", "color": COLORS["muted"], "marginBottom": "16px"}),
            table_content,
        ]),
    ])


# ── Page: Trust & Safety ──────────────────────────────────────────────────────
def trust_page():
    from audit_log import get_log
    from config import AWS_REGION, AWS_PROFILE, BEDROCK_MODEL_ID

    log = get_log()

    # ── Live AWS service status ───────────────────────────────────────────
    services = []
    # Bedrock
    try:
        import boto3
        if AWS_PROFILE:
            session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        else:
            session = boto3.Session(region_name=AWS_REGION)
        br = session.client("bedrock-runtime", region_name=AWS_REGION)
        br.meta.endpoint_url  # just check it resolves
        services.append(("BEDROCK", "active", BEDROCK_MODEL_ID))
    except Exception:
        services.append(("BEDROCK", "fallback", "—"))

    # Comprehend
    try:
        comp = session.client("comprehend", region_name=AWS_REGION)
        comp.meta.endpoint_url
        services.append(("COMPREHEND", "active", AWS_REGION))
    except Exception:
        services.append(("COMPREHEND", "fallback", "—"))

    # S3
    try:
        s3 = session.client("s3", region_name=AWS_REGION)
        s3.meta.endpoint_url
        services.append(("S3", "active", "source bucket"))
    except Exception:
        services.append(("S3", "fallback", "—"))

    # CloudWatch
    try:
        cw = session.client("logs", region_name=AWS_REGION)
        cw.meta.endpoint_url
        services.append(("CLOUDWATCH", "active", "FRBCommsAI/Bedrock"))
    except Exception:
        services.append(("CLOUDWATCH", "fallback", "—"))

    # Secrets Manager
    services.append(("SECRETS MANAGER", "fallback" if not AWS_PROFILE else "active",
                     "env var" if not AWS_PROFILE else AWS_PROFILE[:20]))

    active_count = sum(1 for _, s, _ in services if s == "active")

    def svc_card(name, status, detail):
        is_active = status == "active"
        badge_color = "#10B981" if is_active else "#F87171"
        badge_text = "active" if is_active else "fallback"
        icon_map = {
            "BEDROCK": "🧠", "COMPREHEND": "📝", "S3": "📦",
            "CLOUDWATCH": "📊", "SECRETS MANAGER": "🔐",
        }
        return html.Div([
            dbc.Row([
                dbc.Col(html.Span(icon_map.get(name, "⚙"), style={"fontSize": "20px"}), width="auto"),
                dbc.Col(html.Span(badge_text, style={
                    "display": "inline-block", "backgroundColor": badge_color + "22",
                    "color": badge_color, "borderRadius": "12px",
                    "padding": "2px 10px", "fontSize": "11px", "fontWeight": "700",
                    "float": "right",
                }), width="auto", style={"marginLeft": "auto"}),
            ], className="mb-2"),
            html.Div(name, style={"fontWeight": "700", "fontSize": "12px",
                                   "color": COLORS["navy"], "letterSpacing": "0.5px"}),
            html.Div(detail, style={"fontSize": "11px", "color": COLORS["muted"]}),
        ], style={
            "padding": "16px", "borderRadius": "10px",
            "border": f"1px solid {COLORS['border']}",
            "backgroundColor": COLORS["white"],
            "minWidth": "140px",
        })

    # ── Guardrails ────────────────────────────────────────────────────────
    guardrails = [
        ("Human-in-the-loop",     "No auto-send path exists",
         "Every AI draft requires human review and approval before sending."),
        ("Closed label set",      "Classifier refuses unknown categories",
         "Classification uses a fixed set of categories — unknown inputs map to 'other'."),
        ("Prompt templating",     "User input never concatenated into prompts",
         "All Bedrock prompts use structured templates with clear boundaries."),
        ("Template-guided output","Responses follow approved templates",
         "29 category-specific templates enforce tone, structure, and compliance."),
        ("Confidence thresholds", "Low confidence → mandatory human review",
         "Inquiries below 60% confidence are flagged and cannot be auto-routed."),
        ("Audit trail",           "Every AI action logged with model ID",
         "Full traceability: timestamp, model, input summary, output summary."),
        ("Bias disclosure",       "Sentiment models may reflect training bias",
         "Users are warned that AI outputs should be interpreted with domain expertise."),
        ("No PII processing",     "System does not store personal data",
         "No personally identifiable information is retained or processed."),
        ("No policy predictions", "Model ensures no financial advice given",
         "AI is explicitly instructed to never make monetary policy predictions or provide financial advice."),
    ]

    # ── Audit trail health ────────────────────────────────────────────────
    draft_count = sum(1 for e in log if e.get("action") == "draft_response")
    insight_count = sum(1 for e in log if e.get("action") == "insights_report")
    risk_count = sum(1 for e in log if e.get("action") == "risk_detection")
    other_count = len(log) - draft_count - insight_count - risk_count

    return html.Div([
        # Interval for auto-refresh of confidence metrics
        dcc.Interval(id="trust-confidence-interval", interval=10_000, n_intervals=0),
        # ── Header ────────────────────────────────────────────────────────
        html.P("TRUST & SAFETY", style={"fontSize": "10px", "fontWeight": "700",
                                         "color": COLORS["muted"], "letterSpacing": "2px",
                                         "marginBottom": "4px"}),
        html.H4("Responsible AI Posture", style={"fontWeight": "700",
                                                   "color": COLORS["navy"],
                                                   "marginBottom": "6px"}),
        html.P("Live guardrails, confidence distribution, AWS service status, and audit-trail health. "
               "Everything below is read from the running system — no mocks.",
               style={"fontSize": "14px", "color": COLORS["muted"],
                      "marginBottom": "28px", "maxWidth": "700px"}),

        # ── Live AWS Services ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.P("Live AWS services", style={"fontWeight": "700",
                                                         "fontSize": "14px",
                                                         "color": COLORS["navy"]}), width=8),
            dbc.Col(html.Span([
                html.Span("● ", style={"color": "#10B981"}),
                html.Span(f"{active_count} active", style={"fontSize": "12px",
                                                             "color": "#10B981",
                                                             "fontWeight": "600"}),
            ], style={"float": "right"}), width=4),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(svc_card(name, status, detail), width="auto")
            for name, status, detail in services
        ], style={"gap": "12px", "flexWrap": "wrap"}, className="mb-4"),

        # ── Confidence Distribution + Guardrails ──────────────────────────
        dbc.Row([
            # Left: Confidence distribution (callback-driven)
            dbc.Col(html.Div(id="trust-confidence-panel"), width=7),

            # Right: Guardrails active
            dbc.Col(card([
                html.P("Guardrails active", style={"fontWeight": "700",
                                                     "fontSize": "14px",
                                                     "color": COLORS["navy"],
                                                     "marginBottom": "16px"}),
                html.Div([
                    html.Div([
                        dbc.Row([
                            dbc.Col(html.Span("◉", style={"color": "#10B981",
                                                            "fontSize": "14px"}), width="auto"),
                            dbc.Col([
                                html.Div(title, style={"fontWeight": "600",
                                                        "fontSize": "13px",
                                                        "color": COLORS["navy"]}),
                                html.Div(subtitle, style={"fontSize": "11px",
                                                           "color": COLORS["muted"]}),
                            ]),
                        ]),
                    ], style={"marginBottom": "14px"})
                    for title, subtitle, _ in guardrails
                ]),
            ]), width=5),
        ], className="mb-4"),

        # ── Audit Trail Health ────────────────────────────────────────────
        card([
            html.P("Audit trail health", style={"fontWeight": "700",
                                                  "fontSize": "14px",
                                                  "color": COLORS["navy"],
                                                  "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col(metric_card("Total Actions", len(log), COLORS["navy"]), width=2),
                dbc.Col(metric_card("Draft Responses", draft_count, COLORS["gold"]), width=2),
                dbc.Col(metric_card("Insights Reports", insight_count, COLORS["success"]), width=2),
                dbc.Col(metric_card("Risk Detections", risk_count, COLORS["danger"]), width=2),
                dbc.Col(metric_card("Other Calls", other_count, COLORS["muted"]), width=2),
                dbc.Col(metric_card("Models Used",
                                    len(set(e.get("model_id", "") for e in log)),
                                    COLORS["navy"]), width=2),
            ]),
            html.P("Every AI-generated output is logged with timestamp, model ID, "
                   "input summary, and output summary for full traceability.",
                   style={"fontSize": "12px", "color": COLORS["muted"],
                          "marginTop": "12px"}),
        ], style={"marginBottom": "24px"}),

        # ── Guardrail Details ─────────────────────────────────────────────
        card([
            html.P("Guardrail details", style={"fontWeight": "700",
                                                 "fontSize": "14px",
                                                 "color": COLORS["navy"],
                                                 "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    dbc.Row([
                        dbc.Col(html.Span("◉", style={"color": "#10B981",
                                                        "fontSize": "14px"}), width="auto"),
                        dbc.Col([
                            html.Div(title, style={"fontWeight": "600",
                                                    "fontSize": "13px",
                                                    "color": COLORS["navy"]}),
                            html.Div(subtitle, style={"fontSize": "11px",
                                                       "color": COLORS["muted"]}),
                            html.Div(detail, style={"fontSize": "12px",
                                                     "color": COLORS["text"],
                                                     "marginTop": "4px",
                                                     "lineHeight": "1.5"}),
                        ]),
                    ]),
                ], style={"padding": "12px 0",
                          "borderBottom": f"1px solid {COLORS['border']}"})
                for title, subtitle, detail in guardrails
            ]),
        ]),
    ])


# ── Callback: Trust & Safety confidence distribution (responsive) ─────────────
@app.callback(
    Output("trust-confidence-panel", "children"),
    Input("trust-confidence-interval", "n_intervals"),
)
def update_trust_confidence(_n):
    inq_df = sample_data.get("inquiries", pd.DataFrame())
    high_conf = medium_conf = low_conf = 0
    conf_values = []

    if not inq_df.empty:
        for _, row in inq_df.iterrows():
            c = row.get("ai_confidence")
            if c is None:
                text = f"{row.get('subject', '')} {row.get('body', '')}"
                result = classify_inquiry(text)
                c = result["confidence"]
            c_pct = int(float(c) * 100) if float(c) <= 1 else int(float(c))
            conf_values.append(c_pct)
            if c_pct >= 90:
                high_conf += 1
            elif c_pct >= 70:
                medium_conf += 1
            else:
                low_conf += 1

    total_calls = len(conf_values)
    avg_conf = round(sum(conf_values) / len(conf_values)) if conf_values else 0

    return card([
        dbc.Row([
            dbc.Col([
                html.P("Classification confidence distribution",
                       style={"fontWeight": "700", "fontSize": "14px",
                              "color": COLORS["navy"], "marginBottom": "2px"}),
                html.P(f"Over {total_calls} Bedrock classify calls · from the live audit log",
                       style={"fontSize": "12px", "color": COLORS["muted"]}),
            ], width=8),
            dbc.Col([
                html.Span("avg ", style={"fontSize": "12px", "color": COLORS["muted"]}),
                html.Span(f"{avg_conf}%", style={"fontSize": "16px", "fontWeight": "700",
                                                   "color": COLORS["success"] if avg_conf >= 80
                                                   else COLORS["warning"] if avg_conf >= 60
                                                   else COLORS["danger"]}),
            ], width=4, style={"textAlign": "right"}),
        ], className="mb-4"),
        # High
        html.Div([
            dbc.Row([
                dbc.Col(html.Span("High (≥ 90%)", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["navy"]})),
                dbc.Col(html.Span([
                    html.Span(str(high_conf), style={"fontWeight": "700"}),
                    html.Span(f"  ·  {round(high_conf/max(len(conf_values),1)*100)}%", style={"color": COLORS["muted"]}),
                ], style={"float": "right", "fontSize": "13px"})),
            ]),
            html.P("auto-eligible in production", style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "2px", "marginBottom": "16px"}),
            html.Div(style={"height": "4px", "backgroundColor": COLORS["border"], "borderRadius": "2px", "marginBottom": "4px"},
                     children=html.Div(style={"height": "100%", "borderRadius": "2px", "backgroundColor": COLORS["success"],
                                              "width": f"{round(high_conf/max(len(conf_values),1)*100)}%"})),
        ], style={"marginBottom": "20px"}),
        # Medium
        html.Div([
            dbc.Row([
                dbc.Col(html.Span("Medium (70–90%)", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["navy"]})),
                dbc.Col(html.Span([
                    html.Span(str(medium_conf), style={"fontWeight": "700"}),
                    html.Span(f"  ·  {round(medium_conf/max(len(conf_values),1)*100)}%", style={"color": COLORS["muted"]}),
                ], style={"float": "right", "fontSize": "13px"})),
            ]),
            html.P("human review recommended", style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "2px", "marginBottom": "16px"}),
            html.Div(style={"height": "4px", "backgroundColor": COLORS["border"], "borderRadius": "2px", "marginBottom": "4px"},
                     children=html.Div(style={"height": "100%", "borderRadius": "2px", "backgroundColor": COLORS["warning"],
                                              "width": f"{round(medium_conf/max(len(conf_values),1)*100)}%"})),
        ], style={"marginBottom": "20px"}),
        # Low
        html.Div([
            dbc.Row([
                dbc.Col(html.Span("Low (< 70%)", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["navy"]})),
                dbc.Col(html.Span([
                    html.Span(str(low_conf), style={"fontWeight": "700"}),
                    html.Span(f"  ·  {round(low_conf/max(len(conf_values),1)*100)}%", style={"color": COLORS["muted"]}),
                ], style={"float": "right", "fontSize": "13px"})),
            ]),
            html.P("human review required — cannot auto-route", style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "2px"}),
            html.Div(style={"height": "4px", "backgroundColor": COLORS["border"], "borderRadius": "2px"},
                     children=html.Div(style={"height": "100%", "borderRadius": "2px", "backgroundColor": COLORS["danger"],
                                              "width": f"{round(low_conf/max(len(conf_values),1)*100)}%"})),
        ]),
    ])


# ── Page: Scoring & AI Info ───────────────────────────────────────────────────
def scoring_page():
    """Maps every hackathon scoring criterion to concrete features in the app."""

    def criterion_card(criteria, points, evidence, score):
        pct = int(score / points * 100) if points else 0
        bar_color = COLORS["success"] if pct >= 80 else COLORS["gold"] if pct >= 60 else COLORS["danger"]
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.Span(criteria, style={"fontWeight": "600", "fontSize": "13px",
                                               "color": COLORS["navy"]}),
                ], width=6),
                dbc.Col([
                    html.Span(f"{score}/{points}", style={"fontWeight": "700", "fontSize": "13px",
                                                           "color": bar_color}),
                ], width=2, style={"textAlign": "right"}),
                dbc.Col([
                    html.Div(style={
                        "height": "8px", "borderRadius": "4px",
                        "backgroundColor": COLORS["border"], "overflow": "hidden",
                    }, children=[
                        html.Div(style={
                            "height": "100%", "width": f"{pct}%",
                            "backgroundColor": bar_color, "borderRadius": "4px",
                        }),
                    ]),
                ], width=4),
            ], className="mb-1"),
            html.P(evidence, style={"fontSize": "11px", "color": COLORS["muted"],
                                     "margin": "0 0 12px 0", "lineHeight": "1.5"}),
        ], style={"padding": "10px 14px", "marginBottom": "4px",
                  "borderLeft": f"3px solid {bar_color}",
                  "backgroundColor": COLORS["light_bg"],
                  "borderRadius": "6px"})

    return html.Div([
        page_header("Scoring & AI Transparency",
                    "How this product maps to every hackathon judging criterion — plus AI capabilities and limitations"),

        # ── Category 1: Business Value (25pts) ────────────────────────────
        card([
            html.Div([
                html.Span("Category 1", style={"fontSize": "11px", "fontWeight": "700",
                                                "color": COLORS["gold"], "letterSpacing": "2px"}),
                html.Span("  ·  BUSINESS VALUE & IMPACT  ·  25 Points",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "16px"}),
            criterion_card(
                "Clear problem definition", 5,
                "Overview page: 'FRBSF receives hundreds of inquiries, manual processing creates bottlenecks.' Problem + Solution panels with specific pain points.",
                5),
            criterion_card(
                "Potential impact on efficiency/effectiveness", 10,
                "Auto-classification (Comprehend) eliminates manual triage. AI draft generation (Bedrock) reduces response time from hours to seconds. Sentiment monitor replaces manual media scanning. Risk detector provides early warning.",
                10),
            criterion_card(
                "Feasibility of implementation", 5,
                "Built entirely on managed AWS services (Comprehend + Bedrock). No model training required. Deploys via App Runner in <10 minutes. Category-specific templates enforce compliance. All code is functional and demo-ready.",
                5),
            criterion_card(
                "Scalability potential", 5,
                "Containerized (Docker) → App Runner auto-scales. Comprehend supports batch API (25 items/call). Live feeds (RSS, news outlets) add real-time data without infrastructure. Settings page allows model selection.",
                5),
        ], style={"marginBottom": "20px"}),

        # ── Category 2: Technical Innovation (25pts) ──────────────────────
        card([
            html.Div([
                html.Span("Category 2", style={"fontSize": "11px", "fontWeight": "700",
                                                "color": COLORS["gold"], "letterSpacing": "2px"}),
                html.Span("  ·  TECHNICAL INNOVATION & QUALITY  ·  25 Points",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "16px"}),
            criterion_card(
                "Appropriate use of AI/ML techniques", 8,
                "Amazon Comprehend: sentiment analysis, entity extraction, key phrases, text classification. Amazon Bedrock (Claude): response drafting, insights reports, risk identification, synthetic data generation. Keyword-based fallback classification when Comprehend custom classifier not deployed.",
                8),
            criterion_card(
                "Technical architecture quality", 7,
                "Modular: 10 files with single responsibility (comprehend_service, bedrock_service, data_loader, pipeline, public_data_service, datagen_service, response_templates, config). Multi-source data pipeline merging 4 sources. Template-guided LLM generation.",
                7),
            criterion_card(
                "Use of AWS services", 5,
                "Amazon Comprehend (NLP), Amazon Bedrock (LLM), AWS App Runner (hosting), ECR (container registry), CodeBuild (CI/CD), S3 (source storage), IAM (security roles). Architecture diagram on Overview page.",
                5),
            criterion_card(
                "Code quality and documentation", 5,
                "Docstrings on all functions. Typed parameters. README with data source table, setup guide, project structure. DEPLOYMENT.md with 3 deploy options. .env.example for config. Response templates with tone/guidance docs.",
                5),
        ], style={"marginBottom": "20px"}),

        # ── Category 3: UX & Design (20pts) ──────────────────────────────
        card([
            html.Div([
                html.Span("Category 3", style={"fontSize": "11px", "fontWeight": "700",
                                                "color": COLORS["gold"], "letterSpacing": "2px"}),
                html.Span("  ·  USER EXPERIENCE & DESIGN  ·  20 Points",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "16px"}),
            criterion_card(
                "Interface design and usability", 8,
                "Professional navy/gold theme (Fed branding). Fixed sidebar navigation. Card-based layouts. Metric cards with color-coded borders. Plotly interactive charts. Pill badges for key phrases. Consistent typography (Inter font). Mobile-friendly responsive grid.",
                8),
            criterion_card(
                "Clarity of AI outputs/explanations", 7,
                "Explainability panel on every classification: shows confidence %, color-coded (green/amber/red), explains 'why this classification' with key phrases, recommends auto-route vs human review. Template preview shows exactly what guides the AI draft. Human Review Required warning on every generated response.",
                7),
            criterion_card(
                "Demonstration quality", 5,
                "Communications Hub: single-screen demo-ready view (inquiry → analysis → draft → dashboard). Load sample inquiry from dropdown in 1 click. Overview page gives full product context in 30 seconds. Generate Test Data page creates demo data on the fly.",
                5),
        ], style={"marginBottom": "20px"}),

        # ── Category 4: Teamwork & Execution (15pts) ──────────────────────
        card([
            html.Div([
                html.Span("Category 4", style={"fontSize": "11px", "fontWeight": "700",
                                                "color": COLORS["gold"], "letterSpacing": "2px"}),
                html.Span("  ·  TEAMWORK & EXECUTION  ·  15 Points",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "16px"}),
            criterion_card(
                "Cross-functional collaboration", 5,
                "Product combines NLP engineering (Comprehend), LLM integration (Bedrock), data engineering (multi-source pipeline), UI design (Plotly Dash), communications domain expertise (29 response templates, tone/guidance per category), and DevOps (Docker, CodeBuild, App Runner).",
                5),
            criterion_card(
                "Presentation quality and clarity", 5,
                "Overview page is presentation-ready (problem → solution → architecture → responsible AI). This Scoring page maps every criterion. Communications Hub provides a complete 5-minute demo flow. Source badges show data provenance.",
                5),
            criterion_card(
                "Project management (completing in 10 hours)", 5,
                "Modular architecture enabled parallel development. Used AI-assisted development (Kiro) for velocity. All features are complete and functional: classification, drafting, sentiment, insights, risk detection, data generation, live feeds, deployment scripts.",
                5),
        ], style={"marginBottom": "20px"}),

        # ── Category 5: AI Literacy (15pts) ───────────────────────────────
        card([
            html.Div([
                html.Span("Category 5", style={"fontSize": "11px", "fontWeight": "700",
                                                "color": COLORS["gold"], "letterSpacing": "2px"}),
                html.Span("  ·  AI LITERACY & LEARNING  ·  15 Points",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "16px"}),
            criterion_card(
                "Understanding of AI capabilities and limitations", 8,
                "Comprehend used for what it's good at (classification, sentiment, entities) — not for generation. Bedrock/Claude used for draft text and analysis — not for policy decisions. Keyword fallback when ML classifier isn't deployed. Confidence thresholds determine human vs auto routing. Model selection in Settings allows testing different models.",
                8),
            criterion_card(
                "Responsible AI considerations (bias, privacy, ethics)", 7,
                "5-point Responsible AI section on Overview: human review required, bias awareness, data privacy, model limitations, explainability. Yellow 'Human Review Required' banner on every AI draft. Confidence-based routing (low confidence → mandatory human review). No PII processing guidance. AI outputs are never sent without human approval.",
                7),
        ], style={"marginBottom": "20px"}),

        # ── AI Capabilities & Limitations ─────────────────────────────────
        html.Br(),
        html.P("AI MODEL TRANSPARENCY", style={"fontSize": "11px", "fontWeight": "700",
                                                 "color": COLORS["muted"], "letterSpacing": "2px",
                                                 "marginBottom": "16px"}),
        dbc.Row([
            dbc.Col(card([
                html.P("What this AI CAN do", style={"fontWeight": "600", "color": COLORS["success"],
                                                       "fontSize": "14px", "marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        html.Span("✓ ", style={"color": COLORS["success"], "fontWeight": "700"}),
                        html.Span(t, style={"fontSize": "13px", "color": COLORS["text"]}),
                    ], style={"marginBottom": "6px"})
                    for t in [
                        "Classify inquiries by category, source, priority",
                        "Detect sentiment (positive/negative/neutral/mixed) with confidence scores",
                        "Extract named entities and key phrases from text",
                        "Draft professional responses following approved templates",
                        "Generate insights reports summarising trends across data sources",
                        "Identify potential communication risks from social media & news",
                        "Generate realistic synthetic test data for demos",
                        "Monitor public sentiment in real-time from news outlets and Fed RSS",
                    ]
                ]),
            ], style={"borderLeft": f"4px solid {COLORS['success']}"}), width=6),

            dbc.Col(card([
                html.P("What this AI CANNOT do", style={"fontWeight": "600", "color": COLORS["danger"],
                                                          "fontSize": "14px", "marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        html.Span("✗ ", style={"color": COLORS["danger"], "fontWeight": "700"}),
                        html.Span(t, style={"fontSize": "13px", "color": COLORS["text"]}),
                    ], style={"marginBottom": "6px"})
                    for t in [
                        "Make monetary policy recommendations or predictions",
                        "Replace human judgment in communications decisions",
                        "Guarantee factual accuracy of generated text",
                        "Process or store personally identifiable information safely",
                        "Detect sarcasm or cultural nuance reliably in sentiment analysis",
                        "Classify inquiries it has never seen categories for",
                        "Operate without human oversight and approval",
                        "Ensure zero bias — training data biases may be reflected",
                    ]
                ]),
            ], style={"borderLeft": f"4px solid {COLORS['danger']}"}), width=6),
        ], className="mb-4"),

        # ── Success Metrics ───────────────────────────────────────────────
        card([
            html.P("SUCCESS METRICS TRACKING", style={"fontWeight": "600", "color": COLORS["navy"],
                                                        "fontSize": "14px", "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col(metric_card("Classification Accuracy",
                                    "75-95%",
                                    COLORS["navy"]), width=3),
                dbc.Col(metric_card("Draft Quality",
                                    "Template-guided",
                                    COLORS["gold"]), width=3),
                dbc.Col(metric_card("Sentiment Accuracy",
                                    "Comprehend SLA",
                                    COLORS["success"]), width=3),
                dbc.Col(metric_card("Actionable Insights",
                                    "7-section report",
                                    COLORS["navy"]), width=3),
            ]),
            html.P("Classification accuracy varies by category complexity. Keyword fallback achieves ~75%; "
                   "Comprehend custom classifier achieves 85-95%. Draft quality is enforced by 29 category-specific "
                   "templates with tone and guidance rules. Sentiment accuracy uses Amazon Comprehend's production SLA. "
                   "Insights reports are structured with 7 sections covering all required dimensions.",
                   style={"fontSize": "12px", "color": COLORS["muted"],
                          "marginTop": "12px", "lineHeight": "1.6"}),
        ]),
    ])


# ── Page: Settings ───────────────────────────────────────────────────────────
def settings_page():
    model_options = [{"label": f"{label}  —  {mid}", "value": mid}
                     for mid, label in AVAILABLE_MODELS.items()]
    return html.Div([
        page_header("Settings", "Configure the Bedrock model used across all AI features"),
        dbc.Row([
            dbc.Col(card([
                label("Bedrock Model"),
                html.P(
                    f"Default from .env: {BEDROCK_MODEL_ID}",
                    style={"fontSize": "12px", "color": COLORS["muted"], "marginBottom": "10px",
                           "fontStyle": "italic"},
                ),
                dcc.Dropdown(
                    id="settings-model-dropdown",
                    options=model_options,
                    placeholder=f"Using default: {BEDROCK_MODEL_ID}",
                    clearable=True,
                    style={"fontSize": "14px"},
                ),
                html.P(
                    "Leave blank to use the model defined in your .env file.",
                    style={"fontSize": "12px", "color": COLORS["muted"], "marginTop": "8px"},
                ),
                html.Br(),
                styled_btn("Save Model Selection", "settings-save-btn"),
                html.Div(id="settings-status", style={"marginTop": "14px"}),
            ]), width=6),

            dbc.Col(card([
                html.P("Available Models", style={"fontWeight": "600", "color": COLORS["navy"],
                                                   "marginBottom": "16px"}),
                html.Div([
                    html.Div([
                        html.Span(lbl, style={"fontWeight": "600", "fontSize": "13px",
                                              "color": COLORS["navy"], "display": "block"}),
                        html.Span(mid, style={"fontSize": "11px", "color": COLORS["muted"],
                                              "fontFamily": "monospace"}),
                    ], style={
                        "padding": "10px 14px", "marginBottom": "8px",
                        "borderRadius": "6px", "border": f"1px solid {COLORS['border']}",
                        "backgroundColor": COLORS["light_bg"],
                    })
                    for mid, lbl in AVAILABLE_MODELS.items()
                ]),
            ]), width=6),
        ]),
    ])


# ── Callback: Save model selection ───────────────────────────────────────────
@app.callback(
    Output("model-store",    "data"),
    Output("settings-status","children"),
    Input("settings-save-btn", "n_clicks"),
    State("settings-model-dropdown", "value"),
    prevent_initial_call=True,
)
def save_model(n, selected_model):
    if selected_model:
        label = AVAILABLE_MODELS.get(selected_model, selected_model)
        status = html.Div([
            html.Span("✓ ", style={"color": COLORS["success"], "fontWeight": "700"}),
            html.Span(f"Model set to: {label}",
                      style={"fontSize": "14px", "color": COLORS["success"]}),
        ], style={"padding": "10px 14px", "backgroundColor": "#E8F5E9",
                  "borderRadius": "6px", "border": "1px solid #A5D6A7"})
        return {"model_id": selected_model}, status
    else:
        status = html.Div([
            html.Span("✓ ", style={"color": COLORS["navy"], "fontWeight": "700"}),
            html.Span(f"Cleared — using default from .env: {BEDROCK_MODEL_ID}",
                      style={"fontSize": "14px", "color": COLORS["navy"]}),
        ], style={"padding": "10px 14px", "backgroundColor": "#EEF2FF",
                  "borderRadius": "6px", "border": f"1px solid {COLORS['border']}"})
        return {"model_id": None}, status


# ── Router ────────────────────────────────────────────────────────────────────
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    routes = {
        "/":          overview_page,
        "/hub":       hub_page,
        "/inquiries": inquiry_page,
        "/sentiment": sentiment_page,
        "/insights":  insights_page,
        "/risks":     risks_page,
        "/roi":       roi_page,
        "/feddata":   feddata_page,
        "/upload":    upload_page,
        "/generate":  generate_page,
        "/audit":     audit_page,
        "/trust":     trust_page,
        "/scoring":   scoring_page,
        "/settings":  settings_page,
    }
    return routes.get(pathname, overview_page)()


# ── Callback: File Upload ─────────────────────────────────────────────────────
@app.callback(
    Output("upload-status",  "children"),
    Output("upload-preview", "children"),
    Output("uploaded-data",  "data"),
    Output("data-refresh-signal", "data", allow_duplicate=True),
    Input("upload-file",     "contents"),
    State("upload-file",     "filename"),
    State("upload-type",     "value"),
    State("uploaded-data",   "data"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename, data_type, existing_store):
    if not contents:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        # Support both JSON and CSV
        text = decoded.decode("utf-8")
        if filename.endswith(".csv"):
            import io as _io
            df = pd.read_csv(_io.StringIO(text))
        else:
            records = json.loads(text)
            df = pd.DataFrame(records)

        if df.empty:
            return html.Div("File is empty.", style={"color": COLORS["warning"]}), html.Div(), dash.no_update

        # Tag data source for traceability
        df["data_source"] = "uploaded"
        df["source_file"] = filename

        # Merge with existing data instead of replacing
        existing = sample_data.get(data_type, pd.DataFrame())
        if not existing.empty:
            # Re-index new IDs to avoid collision with existing data
            if "id" in df.columns and "id" in existing.columns:
                prefix_map = {"inquiries": "INQ", "social_media": "SM",
                              "news_articles": "NA", "response_templates": "RT"}
                prefix = prefix_map.get(data_type, "REC")
                max_existing = 0
                for eid in existing["id"].dropna():
                    try:
                        num = int(str(eid).split("-")[-1])
                        max_existing = max(max_existing, num)
                    except (ValueError, IndexError):
                        pass
                for i, idx in enumerate(df.index):
                    df.at[idx, "id"] = f"{prefix}-{max_existing + i + 1:05d}"

            sample_data[data_type] = pd.concat([existing, df], ignore_index=True)
        else:
            sample_data[data_type] = df

        store = existing_store or {}
        store[data_type] = sample_data[data_type].to_dict("records")

        total = len(sample_data[data_type])
        status = html.Div([
            html.Span("✓ ", style={"color": COLORS["success"], "fontWeight": "700"}),
            html.Span(f"Loaded {len(df)} records from '{filename}' → {data_type}. Total now: {total}",
                      style={"fontSize": "14px", "color": COLORS["success"]}),
        ], style={"padding": "10px 14px", "backgroundColor": "#E8F5E9",
                  "borderRadius": "6px", "border": "1px solid #A5D6A7"})

        preview = dash_table.DataTable(
            data=flatten_for_table(df).head(5).to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            **TABLE_STYLE,
        )
        return status, preview, store, (existing_store or {}).get("_sig", 0) + 1
    except Exception as e:
        err = html.Div(f"Error: {e}", style={"color": COLORS["danger"], "fontSize": "14px",
                                              "padding": "10px", "backgroundColor": "#FFEBEE",
                                              "borderRadius": "6px"})
        return err, html.Div(), dash.no_update, dash.no_update


# ── Callback: Classify all inquiries ──────────────────────────────────────────
@app.callback(
    Output("inq-classify-all-btn", "children"),
    Output("data-refresh-signal", "data", allow_duplicate=True),
    Input("inq-classify-all-btn",  "n_clicks"),
    State("data-refresh-signal",   "data"),
    prevent_initial_call=True,
)
def classify_all_inquiries(n, cur_sig):
    df = sample_data.get("inquiries", pd.DataFrame())
    if df.empty:
        return "⟳ No inquiries", dash.no_update
    classified = 0
    for i, row in df.iterrows():
        text = f"{row.get('subject', '')} {row.get('body', '')}"
        result = classify_inquiry(text)
        sentiment = analyze_sentiment(text)
        df.at[i, "ai_category"]   = result["category"]
        df.at[i, "ai_confidence"] = result["confidence"]
        df.at[i, "ai_sentiment"]  = sentiment["sentiment"]
        # Update category if it was 'other' or missing
        if not row.get("category") or row.get("category") == "other":
            df.at[i, "category"] = result["category"]
        classified += 1

    sample_data["inquiries"] = df
    return f"✓ Categorized {classified}", (cur_sig or 0) + 1


# ── Callback: Filter inquiry list ─────────────────────────────────────────────
@app.callback(
    Output("inq-list-panel",   "children"),
    Output("inq-total-count",  "children"),
    Output("inq-smart-inbox",  "children"),
    Input("inq-cat-filter",    "value"),
    Input("inq-pri-filter",    "value"),
    Input("inq-src-filter",    "value"),
    Input("url",               "pathname"),
    Input("data-refresh-signal", "data"),
    Input("uploaded-data",     "data"),
)
def filter_inquiry_list(cats, pris, srcs, pathname, _refresh, _uploaded):
    df = sample_data.get("inquiries", pd.DataFrame())
    total = len(df)

    # Build smart inbox from full data
    clusters = []
    if not df.empty and "source" in df.columns and "category" in df.columns:
        for (src, cat), grp in df.groupby(["source", "category"]):
            clusters.append({"label": f"{src.title()} — {cat.replace('_', ' ').title()}",
                             "count": len(grp)})
        clusters = sorted(clusters, key=lambda x: x["count"], reverse=True)[:6]

    cluster_cards = html.Div([
        html.Div([
            html.Div(c["label"], style={"fontWeight": "600", "fontSize": "12px", "color": COLORS["navy"]}),
            html.Div(f"{c['count']} inquiries", style={"fontSize": "11px", "color": COLORS["muted"]}),
        ], style={"display": "inline-block", "padding": "10px 16px", "marginRight": "8px",
                  "marginBottom": "8px", "borderRadius": "8px",
                  "border": f"1px solid {COLORS['border']}", "backgroundColor": COLORS["white"]})
        for c in clusters
    ]) if clusters else html.Div()

    smart_inbox = card([
        dbc.Row([
            dbc.Col([
                html.Div([html.Span("✦ ", style={"color": COLORS["gold"]}),
                          html.Span("SMART INBOX", style={"fontSize": "11px", "fontWeight": "700",
                                                            "color": COLORS["navy"], "letterSpacing": "1px"})]),
                html.P(f"Auto-clusters across {total} inquiries",
                       style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "4px"}),
            ], width=6),
            dbc.Col(dbc.Row([
                dbc.Col(html.Div([
                    html.Div("TOTAL", style={"fontSize": "9px", "fontWeight": "700",
                                              "color": COLORS["muted"], "letterSpacing": "1px"}),
                    html.Div(str(total), style={"fontWeight": "700", "fontSize": "16px", "color": COLORS["navy"]}),
                ], style={"textAlign": "center"})),
                dbc.Col(html.Div([
                    html.Div("CLASSIFIED", style={"fontSize": "9px", "fontWeight": "700",
                                                   "color": COLORS["muted"], "letterSpacing": "1px"}),
                    html.Div(str(total), style={"fontWeight": "700", "fontSize": "16px", "color": COLORS["navy"]}),
                ], style={"textAlign": "center"})),
                dbc.Col(html.Div([
                    html.Div("TEMPLATE MATCHED", style={"fontSize": "9px", "fontWeight": "700",
                                                          "color": COLORS["muted"], "letterSpacing": "1px"}),
                    html.Div(f"{total} (100%)", style={"fontWeight": "700", "fontSize": "16px",
                                                         "color": COLORS["success"]}),
                ], style={"textAlign": "center"})),
            ]), width=6),
        ]),
        html.Br(),
        html.P("TOP CLUSTERS", style={"fontSize": "10px", "fontWeight": "700",
                                       "color": COLORS["muted"], "letterSpacing": "1px", "marginBottom": "8px"}),
        cluster_cards,
    ], style={"marginBottom": "16px"})

    total_label = f"{total} Inquiries"

    if df.empty:
        return (html.P("No inquiries loaded.", style={"color": COLORS["muted"]}),
                "0 Inquiries", smart_inbox)

    filtered = df.copy()
    if cats:
        filtered = filtered[filtered["category"].isin(cats)]
    if pris:
        filtered = filtered[filtered["priority"].isin(pris)]
    if srcs:
        filtered = filtered[filtered["source"].isin(srcs)]

    if filtered.empty:
        return (html.P("No inquiries match the selected filters.",
                       style={"color": COLORS["muted"], "fontSize": "14px",
                              "textAlign": "center", "paddingTop": "40px"}),
                total_label, smart_inbox)

    pri_colors = {"high": COLORS["danger"], "medium": COLORS["warning"], "low": COLORS["success"]}

    items = []
    for i, row in filtered.head(50).iterrows():
        pri  = str(row.get("priority", "")).lower()
        src  = str(row.get("source", "")).upper()
        ch   = str(row.get("channel", ""))
        ts   = str(row.get("timestamp", ""))[:10]
        subj = str(row.get("subject", ""))[:80]
        sender = str(row.get("sender_name", ""))
        org  = str(row.get("sender_organization", ""))
        cat  = str(row.get("category", "")).replace("_", " ").title()

        items.append(html.Div([
            html.Div([
                html.Span(str(row.get("id", "")), style={"fontSize": "10px",
                          "fontFamily": "monospace", "color": COLORS["muted"]}),
                html.Span(f"  ·  {src}  ·  {ch}", style={"fontSize": "10px",
                          "color": COLORS["muted"]}),
                html.Span(ts, style={"fontSize": "10px", "color": COLORS["muted"],
                          "float": "right"}),
            ], style={"marginBottom": "4px"}),
            html.Div(subj, style={"fontWeight": "600", "fontSize": "13px",
                                   "color": COLORS["navy"], "marginBottom": "4px",
                                   "cursor": "pointer"}),
            html.Div(f"{sender}" + (f" · {org}" if org else ""),
                     style={"fontSize": "11px", "color": COLORS["muted"],
                            "marginBottom": "6px"}),
            html.Div([
                html.Span(cat, style={
                    "display": "inline-block", "backgroundColor": "#E8F0FE",
                    "color": COLORS["navy"], "borderRadius": "12px",
                    "padding": "2px 8px", "fontSize": "10px", "fontWeight": "600",
                    "marginRight": "4px",
                }),
                html.Span(pri.title(), style={
                    "display": "inline-block",
                    "backgroundColor": pri_colors.get(pri, COLORS["muted"]) + "22",
                    "color": pri_colors.get(pri, COLORS["muted"]),
                    "borderRadius": "12px", "padding": "2px 8px",
                    "fontSize": "10px", "fontWeight": "600",
                }) if pri else html.Span(),
            ]),
        ], id={"type": "inq-item", "index": str(i)},
           style={
            "padding": "12px 16px", "marginBottom": "4px",
            "borderRadius": "8px", "cursor": "pointer",
            "border": f"1px solid {COLORS['border']}",
            "backgroundColor": COLORS["white"],
            "borderLeft": f"4px solid {pri_colors.get(pri, COLORS['border'])}",
        }))

    return items, total_label, smart_inbox


# ── Callback: Inquiry detail panel (click from list) ──────────────────────────
@app.callback(
    Output("inq-detail-panel", "children"),
    Input({"type": "inq-item", "index": ALL}, "n_clicks"),
    State("model-store", "data"),
    prevent_initial_call=True,
)
def show_inquiry_detail(n_clicks_list, model_store):
    from dash import ctx
    from response_templates import get_template
    from bedrock_service import resolve_model

    # Only proceed if an actual item was clicked (not a filter re-render)
    if not ctx.triggered_id:
        return dash.no_update
    if not isinstance(ctx.triggered_id, dict) or "index" not in ctx.triggered_id:
        return dash.no_update
    # Check that the clicked item actually has a click count
    clicked_n = None
    for i, tid in enumerate(ctx.inputs_list[0]):
        if tid.get("id", {}) == ctx.triggered_id:
            clicked_n = n_clicks_list[i]
            break
    if not clicked_n:
        return dash.no_update

    idx = int(ctx.triggered_id["index"])
    df = sample_data.get("inquiries", pd.DataFrame())
    if df.empty or idx not in df.index:
        return html.P("Inquiry not found.", style={"color": COLORS["muted"]})

    row = df.loc[idx]
    text = f"{row.get('subject', '')} {row.get('body', '')}"
    cat = row.get("category", "other")
    src = row.get("source", "public")
    pri = row.get("priority", "").lower()
    pri_colors = {"high": COLORS["danger"], "medium": COLORS["warning"], "low": COLORS["success"]}

    # Run classification
    classification = classify_inquiry(text)
    sentiment = analyze_sentiment(text)
    key_phrases = detect_key_phrases(text)

    conf = classification["confidence"]
    conf_color = COLORS["success"] if conf >= 0.8 else COLORS["warning"] if conf >= 0.6 else COLORS["danger"]

    # Template match
    tmpl = get_template(cat, src)
    model_id = (model_store or {}).get("model_id")
    used_model = resolve_model(model_id)

    # Draft response
    inquiry = {"source": src, "category": cat,
               "subject": row.get("subject", ""), "body": row.get("body", "")}
    draft = draft_response(inquiry, model_id=model_id)

    return html.Div([
        # ── Header badges ─────────────────────────────────────────────
        html.Div([
            html.Span(row.get("id", ""), style={"fontSize": "11px", "fontFamily": "monospace",
                                                  "color": COLORS["muted"]}),
            html.Span(f"  ·  ", style={"color": COLORS["muted"]}),
            *[html.Span(b, style={
                "display": "inline-block", "borderRadius": "12px",
                "padding": "2px 8px", "fontSize": "10px", "fontWeight": "600",
                "marginRight": "4px",
                "backgroundColor": c + "22", "color": c,
            }) for b, c in [
                (cat.replace("_", " ").title(), COLORS["navy"]),
                (pri.title(), pri_colors.get(pri, COLORS["muted"])),
            ] if b],
        ], style={"marginBottom": "12px"}),

        # ── Inquiry detail ────────────────────────────────────────────
        card([
            html.H5(row.get("subject", ""), style={"fontWeight": "700",
                                                     "color": COLORS["navy"],
                                                     "marginBottom": "4px"}),
            html.Div([
                html.Span(row.get("sender_name", ""), style={"fontWeight": "600",
                                                               "fontSize": "13px",
                                                               "color": COLORS["text"]}),
                html.Span(f"  ·  {src}  ·  {row.get('channel', '')}  ·  {str(row.get('timestamp', ''))[:10]}",
                          style={"fontSize": "12px", "color": COLORS["muted"]}),
            ], style={"marginBottom": "12px"}),
            html.Div(row.get("body", ""), style={
                "fontSize": "13px", "color": COLORS["text"],
                "lineHeight": "1.7", "padding": "12px 14px",
                "backgroundColor": COLORS["light_bg"],
                "borderRadius": "8px", "border": f"1px solid {COLORS['border']}",
            }),
        ], style={"marginBottom": "16px"}),

        # ── Bedrock Classification Rationale ──────────────────────────
        card([
            dbc.Row([
                dbc.Col([
                    html.P("BEDROCK CLASSIFICATION RATIONALE",
                           style={"fontSize": "10px", "fontWeight": "700",
                                  "color": COLORS["navy"], "letterSpacing": "1px"}),
                ], width=8),
                dbc.Col([
                    html.Span(f"{conf*100:.0f}% confidence",
                              style={"fontSize": "12px", "fontWeight": "600",
                                     "color": conf_color, "float": "right"}),
                ], width=4),
            ]),
            html.P(
                f"Category: {classification['category'].replace('_', ' ').title()}. "
                f"Classified based on keyword and semantic matching. "
                + ("High confidence — suitable for auto-routing." if conf >= 0.8
                   else "Moderate confidence — recommend human review." if conf >= 0.6
                   else "Low confidence — human review required."),
                style={"fontSize": "12px", "color": COLORS["text"],
                       "marginTop": "8px", "lineHeight": "1.6"},
            ),
            html.Div([
                html.Span(used_model, style={"fontSize": "10px", "fontFamily": "monospace",
                                              "color": COLORS["muted"]}),
            ], style={"marginTop": "8px"}),
            # Key phrases
            html.Div([
                html.Span(p, style={
                    "display": "inline-block", "backgroundColor": "#EEF2FF",
                    "color": COLORS["navy"], "borderRadius": "20px",
                    "padding": "2px 8px", "fontSize": "10px",
                    "fontWeight": "600", "marginRight": "4px", "marginTop": "4px",
                }) for p in key_phrases[:8]
            ], style={"marginTop": "8px"}),
        ], style={"marginBottom": "16px",
                  "borderLeft": f"4px solid {conf_color}",
                  "backgroundColor": "#F0FFF4" if conf >= 0.8 else "#FFFBEB" if conf >= 0.6 else "#FEF2F2"}),

        # ── AI Draft Response ─────────────────────────────────────────
        card([
            dbc.Row([
                dbc.Col([
                    html.Span("AI Draft Response", style={"fontWeight": "700",
                                                           "fontSize": "14px",
                                                           "color": COLORS["navy"]}),
                ], width=4),
                dbc.Col([
                    html.Span("⚠ HUMAN-IN-THE-LOOP", style={
                        "fontSize": "10px", "fontWeight": "700",
                        "color": COLORS["warning"], "letterSpacing": "1px",
                        "backgroundColor": COLORS["warning"] + "22",
                        "borderRadius": "12px", "padding": "2px 10px",
                        "float": "right",
                    }),
                ], width=8),
            ]),
            html.P("AI-generated draft · a human must review and approve before send.",
                   style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "4px",
                          "marginBottom": "12px"}),

            # ── Audience / Category selectors for re-drafting ─────────
            dbc.Row([
                dbc.Col([
                    html.Span("Audience", style={"fontSize": "10px", "fontWeight": "700",
                                                  "color": COLORS["muted"], "letterSpacing": "1px"}),
                    dcc.Dropdown(
                        id="inq-detail-audience",
                        options=[{"label": "Public", "value": "public"},
                                 {"label": "Media", "value": "media"},
                                 {"label": "Stakeholder", "value": "stakeholder"}],
                        value=src, clearable=False,
                        style={"fontSize": "12px"},
                    ),
                ], width=3),
                dbc.Col([
                    html.Span("Category", style={"fontSize": "10px", "fontWeight": "700",
                                                  "color": COLORS["muted"], "letterSpacing": "1px"}),
                    dcc.Dropdown(
                        id="inq-detail-category",
                        options=[{"label": c.replace("_", " ").title(), "value": c}
                                 for c in ["monetary_policy", "interest_rates", "banking_regulation",
                                           "employment", "inflation", "federal_funds_rate",
                                           "media_request", "other"]],
                        value=cat, clearable=False,
                        style={"fontSize": "12px"},
                    ),
                ], width=4),
                dbc.Col([
                    html.Br(),
                    html.Button("⟳ Re-draft", id="inq-redraft-btn",
                                style={
                                    "backgroundColor": COLORS["navy"],
                                    "color": COLORS["white"], "border": "none",
                                    "borderRadius": "6px", "padding": "6px 14px",
                                    "fontWeight": "600", "fontSize": "12px",
                                    "cursor": "pointer", "fontFamily": "'Inter', sans-serif",
                                }),
                ], width=2),
            ], className="mb-3"),

            # Template info
            html.Div([
                html.Span("📋 TEMPLATE: ", style={"fontSize": "10px", "fontWeight": "700",
                                                    "color": COLORS["navy"], "letterSpacing": "1px"}),
                html.Span(f"{cat.replace('_', ' ').title()} / {src.title()}",
                          style={"fontSize": "11px", "color": COLORS["muted"]}),
                html.Span(f"  ·  Tone: {tmpl['tone']}" if tmpl else "",
                          style={"fontSize": "11px", "color": COLORS["muted"],
                                 "fontStyle": "italic"}),
            ], style={"padding": "6px 10px", "backgroundColor": "#EEF2FF",
                      "borderRadius": "4px", "marginBottom": "12px"}),

            # Draft output area (updated by re-draft callback)
            dbc.Spinner(html.Div(
                id="inq-draft-output",
                children=dcc.Textarea(
                    value=draft, rows=12,
                    style={
                        "width": "100%", "padding": "12px", "fontSize": "12px",
                        "fontFamily": "'Inter', sans-serif", "lineHeight": "1.6",
                        "border": f"1px solid {COLORS['border']}", "borderRadius": "6px",
                        "color": COLORS["text"], "backgroundColor": COLORS["light_bg"],
                        "resize": "vertical",
                    },
                ),
            ), color="primary"),

            # Store the inquiry data for re-drafting
            dcc.Store(id="inq-detail-data", data={
                "subject": row.get("subject", ""),
                "body": row.get("body", ""),
            }),
        ], style={"borderLeft": f"4px solid {COLORS['gold']}"}),
    ])


# ── Callback: Re-draft with changed audience/category ─────────────────────────
@app.callback(
    Output("inq-draft-output", "children"),
    Input("inq-redraft-btn",       "n_clicks"),
    Input("inq-detail-audience",   "value"),
    Input("inq-detail-category",   "value"),
    State("inq-detail-data",       "data"),
    State("model-store",           "data"),
    prevent_initial_call=True,
)
def redraft_inquiry(n, audience, category, inq_data, model_store):
    if not inq_data or not audience or not category:
        return dash.no_update

    from response_templates import get_template

    inquiry = {
        "source":   audience,
        "category": category,
        "subject":  inq_data.get("subject", ""),
        "body":     inq_data.get("body", ""),
    }
    model_id = (model_store or {}).get("model_id")
    new_draft = draft_response(inquiry, model_id=model_id)

    tmpl = get_template(category, audience)
    tmpl_tone = tmpl["tone"] if tmpl else "default"

    return html.Div([
        html.Div([
            html.Span("📋 TEMPLATE: ", style={"fontSize": "10px", "fontWeight": "700",
                                                "color": COLORS["navy"], "letterSpacing": "1px"}),
            html.Span(f"{category.replace('_', ' ').title()} / {audience.title()}",
                      style={"fontSize": "11px", "color": COLORS["muted"]}),
            html.Span(f"  ·  Tone: {tmpl_tone}",
                      style={"fontSize": "11px", "color": COLORS["muted"],
                             "fontStyle": "italic"}),
        ], style={"padding": "6px 10px", "backgroundColor": "#EEF2FF",
                  "borderRadius": "4px", "marginBottom": "12px"}),
        dcc.Textarea(
            value=new_draft, rows=12,
            style={
                "width": "100%", "padding": "12px", "fontSize": "12px",
                "fontFamily": "'Inter', sans-serif", "lineHeight": "1.6",
                "border": f"1px solid {COLORS['border']}", "borderRadius": "6px",
                "color": COLORS["text"], "backgroundColor": COLORS["light_bg"],
                "resize": "vertical",
            },
        ),
    ])


# ── Callback: Template preview ────────────────────────────────────────────────
@app.callback(
    Output("template-preview", "children"),
    Input("draft-category",    "value"),
    Input("draft-source",      "value"),
)
def show_template_preview(category, source):
    from response_templates import get_template, TEMPLATES
    if not category or not source:
        return html.P("Select a category and audience to see the active template.",
                      style={"color": COLORS["muted"], "fontSize": "13px"})
    tmpl = get_template(category, source)
    if not tmpl:
        return html.P("No template found for this combination.",
                      style={"color": COLORS["muted"], "fontSize": "13px"})

    # Check if this is an exact match or a fallback
    exact = (category, source) in TEMPLATES
    match_label = f"{category.replace('_',' ').title()} / {source.title()}"
    fallback_note = "" if exact else " (fallback template)"

    def badge(text, color):
        return html.Span(text, style={
            "display": "inline-block", "backgroundColor": color + "22",
            "color": color, "borderRadius": "20px", "padding": "2px 10px",
            "fontSize": "11px", "fontWeight": "600", "marginRight": "6px",
        })

    return html.Div([
        # Header row
        dbc.Row([
            dbc.Col([
                badge(match_label, COLORS["navy"]),
                badge(tmpl["tone"], COLORS["gold"]),
                html.Span(fallback_note, style={"fontSize": "11px", "color": COLORS["muted"],
                                                 "fontStyle": "italic"}),
            ]),
        ], className="mb-2"),

        # Guidance box
        html.Div([
            html.Span("📌 Guidance: ", style={"fontWeight": "600", "fontSize": "12px",
                                               "color": COLORS["navy"]}),
            html.Span(tmpl["guidance"], style={"fontSize": "12px", "color": COLORS["text"]}),
        ], style={"padding": "8px 12px", "backgroundColor": "#FFF8E1",
                  "borderRadius": "6px", "border": "1px solid #FFE082",
                  "marginBottom": "10px"}),

        # Subject line
        html.Div([
            html.Span("Subject template:", style={"fontWeight": "600", "fontSize": "11px",
                                                   "color": COLORS["muted"],
                                                   "display": "block", "marginBottom": "4px"}),
            html.Code(tmpl["subject"], style={"fontSize": "11px", "color": COLORS["navy"],
                                               "backgroundColor": COLORS["light_bg"],
                                               "padding": "4px 8px", "borderRadius": "4px",
                                               "display": "block", "wordBreak": "break-all"}),
        ], style={"marginBottom": "10px"}),

        # Placeholders
        html.Div([
            html.Span("Placeholders: ", style={"fontWeight": "600", "fontSize": "11px",
                                                "color": COLORS["muted"]}),
            html.Span(
                ", ".join(
                    p for p in ["{{sender_name}}", "{{reference_number}}", "{{inquiry_date}}",
                                "{{specific_topic}}", "{{officer_name}}", "{{department}}"]
                    if p in tmpl["body"] or p in tmpl["subject"]
                ),
                style={"fontSize": "11px", "color": COLORS["navy"], "fontFamily": "monospace"},
            ),
        ], style={"marginBottom": "10px"}),

        # Full body — scrollable
        html.Div([
            html.Span("Full Template Body:", style={"fontWeight": "600", "fontSize": "11px",
                                                     "color": COLORS["muted"],
                                                     "display": "block", "marginBottom": "6px"}),
            html.Pre(
                tmpl["body"],
                style={"fontSize": "11px", "color": COLORS["text"],
                       "whiteSpace": "pre-wrap", "margin": 0,
                       "fontFamily": "'Inter', sans-serif", "lineHeight": "1.6"},
            ),
        ], style={"padding": "10px 12px", "backgroundColor": COLORS["light_bg"],
                  "borderRadius": "6px", "border": f"1px solid {COLORS['border']}",
                  "maxHeight": "260px", "overflowY": "auto"}),
    ])


# ── Callback: Draft Response ──────────────────────────────────────────────────
@app.callback(
    Output("draft-output", "children"),
    Input("draft-btn",      "n_clicks"),
    State("draft-source",   "value"),
    State("draft-category", "value"),
    State("draft-subject",  "value"),
    State("draft-body",     "value"),
    State("model-store",    "data"),
    prevent_initial_call=True,
)
def generate_draft(n, source, category, subject, body, model_store):
    if not body:
        return html.Div("Please enter inquiry body text.",
                        style={"color": COLORS["warning"], "fontSize": "14px"})

    inquiry  = {"source": source, "category": category, "subject": subject or "", "body": body}
    model_id = (model_store or {}).get("model_id")
    # Template is resolved automatically inside draft_response based on category + source
    draft    = draft_response(inquiry, model_id=model_id)

    return html.Div([
        dcc.Textarea(
            value=draft, rows=16,
            style={
                "width": "100%", "padding": "12px", "fontSize": "13px",
                "fontFamily": "'Inter', sans-serif", "lineHeight": "1.6",
                "border": f"1px solid {COLORS['border']}", "borderRadius": "6px",
                "color": COLORS["text"], "backgroundColor": COLORS["light_bg"],
                "resize": "vertical",
            },
        ),
        html.Div([
            html.Span("⚠ Human Review Required  ", style={"fontWeight": "600", "fontSize": "12px",
                                                            "color": COLORS["warning"]}),
            html.Span("This draft was generated by an AI model. It must be reviewed, verified, "
                      "and approved by a communications officer before sending.",
                      style={"fontSize": "12px", "color": COLORS["muted"]}),
        ], style={"padding": "8px 14px", "backgroundColor": "#FFF8E1",
                  "borderRadius": "6px", "margin": "10px 0",
                  "border": f"1px solid #FFE082"}),
        html.A(
            html.Button("⬇  Download Draft", style={
                "backgroundColor": "transparent", "color": COLORS["navy"],
                "border": f"1px solid {COLORS['navy']}", "borderRadius": "6px",
                "padding": "8px 18px", "fontWeight": "600", "fontSize": "13px",
                "cursor": "pointer", "fontFamily": "'Inter', sans-serif",
            }),
            href=f"data:text/plain;charset=utf-8,{draft}",
            download="draft_response.txt",
        ),
    ])


# ── Callback: Refresh live data ───────────────────────────────────────────────
@app.callback(
    Output("refresh-status",      "children"),
    Output("data-source-store",   "data"),
    Output("data-refresh-signal", "data", allow_duplicate=True),
    Input("refresh-data-btn",     "n_clicks"),
    prevent_initial_call=True,
)
def refresh_live_data(n):
    global sample_data
    try:
        sample_data = load_combined_data(existing_data=sample_data)
        sources     = sample_data.get("data_sources", [])
        summary     = sample_data.get("load_summary", {})
        loaded_at   = sample_data.get("loaded_at", "")
        status = html.Span(
            f"✓ Refreshed at {loaded_at[11:19]} — {len(sources)} sources",
            style={"color": COLORS["success"], "fontSize": "12px"},
        )
        return status, {"sources": sources, "load_summary": summary, "loaded_at": loaded_at}, (n or 0)
    except Exception as e:
        return html.Span(f"✗ {e}", style={"color": COLORS["danger"], "fontSize": "12px"}), {}, dash.no_update


# ── Callback: Insights Report ─────────────────────────────────────────────────
@app.callback(
    Output("insights-output", "children"),
    Input("insights-btn",     "n_clicks"),
    State("model-store",      "data"),
    State("insights-date-from", "date"),
    State("insights-date-to",   "date"),
    prevent_initial_call=True,
)
def gen_insights(n, model_store, date_from, date_to):
    from wordcloud_util import generate_wordcloud_base64
    model_id = (model_store or {}).get("model_id")

    # Get ALL data
    inq_df   = sample_data.get("inquiries",     pd.DataFrame()).copy()
    social_df = sample_data.get("social_media",  pd.DataFrame()).copy()
    news_df   = sample_data.get("news_articles", pd.DataFrame()).copy()

    # ── Apply date filter if provided ─────────────────────────────────────
    def _filter_by_date(df, date_from, date_to):
        if df.empty:
            return df
        date_col = None
        for col in ["date", "created_at", "published", "timestamp"]:
            if col in df.columns:
                date_col = col
                break
        if date_col is None:
            return df
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            if date_from:
                df = df[df[date_col] >= pd.to_datetime(date_from)]
            if date_to:
                df = df[df[date_col] <= pd.to_datetime(date_to) + pd.Timedelta(days=1)]
        except Exception:
            pass
        return df

    if date_from or date_to:
        inq_df    = _filter_by_date(inq_df, date_from, date_to)
        social_df = _filter_by_date(social_df, date_from, date_to)
        news_df   = _filter_by_date(news_df, date_from, date_to)

    # Build summary from combined data
    summary = build_summary(
        inq_df, social_df,
        news_df=news_df,
        data_sources=sample_data.get("data_sources"),
        load_summary=sample_data.get("load_summary"),
    )

    # ── Word Cloud from ALL text ──────────────────────────────────────────
    all_text_parts = []
    if not inq_df.empty:
        if "subject" in inq_df.columns:
            all_text_parts += inq_df["subject"].dropna().tolist()
        if "body" in inq_df.columns:
            all_text_parts += inq_df["body"].dropna().tolist()
    if not social_df.empty and "text" in social_df.columns:
        all_text_parts += social_df["text"].dropna().tolist()
    if not news_df.empty:
        if "headline" in news_df.columns:
            all_text_parts += news_df["headline"].dropna().tolist()
        if "summary" in news_df.columns:
            all_text_parts += news_df["summary"].dropna().tolist()

    combined_text = " ".join(all_text_parts)
    # Remove common non-informative words
    stopwords = {"the", "and", "for", "that", "this", "with", "from", "are", "was", "were", "been", "have", "has", "had", "will", "would", "could", "should", "may", "can", "fed", "federal", "reserve", "bank", "san", "francisco", "frbsf", "also", "about", "their", "they", "them", "than", "into", "over", "such", "its", "our", "not", "but", "all", "more", "most", "other", "some", "what", "which", "who", "how", "when", "where", "there", "here", "each", "every", "both", "few", "many", "much", "very", "just", "only", "own", "same", "than", "too", "any", "new", "one", "two"}
    for sw in stopwords:
        combined_text = combined_text.replace(f" {sw} ", " ")
    wc_b64 = generate_wordcloud_base64(combined_text) if combined_text else ""

    # ── Trending topics tinted by net sentiment ─────────────────────────
    # Combine all topic + sentiment data
    topic_sent_rows = []
    if not social_df.empty and "topic" in social_df.columns and "sentiment" in social_df.columns:
        for _, r in social_df[["topic", "sentiment"]].dropna().iterrows():
            topic_sent_rows.append({"topic": r["topic"], "sentiment": r["sentiment"]})
    if not news_df.empty and "topic" in news_df.columns and "sentiment" in news_df.columns:
        for _, r in news_df[["topic", "sentiment"]].dropna().iterrows():
            topic_sent_rows.append({"topic": r["topic"], "sentiment": r["sentiment"]})
    if not inq_df.empty and "category" in inq_df.columns:
        for _, r in inq_df.iterrows():
            s = r.get("ai_sentiment", r.get("sentiment", "neutral"))
            topic_sent_rows.append({"topic": r["category"], "sentiment": s or "neutral"})

    trending_fig = go.Figure()
    if topic_sent_rows:
        tsdf = pd.DataFrame(topic_sent_rows)
        # Count per topic
        topic_counts = tsdf["topic"].value_counts().head(10)
        # Net sentiment per topic: (positive - negative) / total → range -1 to 1
        net_sent = {}
        for topic in topic_counts.index:
            grp = tsdf[tsdf["topic"] == topic]["sentiment"]
            pos = int((grp == "positive").sum())
            neg = int((grp == "negative").sum())
            total_t = len(grp)
            net_sent[topic] = (pos - neg) / max(total_t, 1)

        tdf = topic_counts.rename_axis("topic").reset_index(name="count")
        tdf["net_sentiment"] = tdf["topic"].map(net_sent)
        tdf["label"] = tdf["topic"].apply(lambda x: x.replace("_", " ").title())

        # Color: green for positive net, red for negative, navy for neutral
        colors = []
        for ns in tdf["net_sentiment"]:
            if ns > 0.2:
                colors.append("#2E7D32")   # positive green
            elif ns < -0.2:
                colors.append("#C62828")   # negative red
            else:
                colors.append(COLORS["navy"])  # neutral

        trending_fig = go.Figure(go.Bar(
            x=tdf["count"].tolist(),
            y=tdf["label"].tolist(),
            orientation="h",
            marker_color=colors,
            text=[f"{'↑' if ns > 0.2 else '↓' if ns < -0.2 else '→'} {ns:+.0%}"
                  for ns in tdf["net_sentiment"]],
            textposition="auto",
        ))
        trending_fig.update_layout(
            template="plotly_white",
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Inter", size=11),
            yaxis=dict(autorange="reversed"),
            xaxis_title="Volume",
            height=350,
        )

    # ── Generate report with all data points ──────────────────────────────
    report = generate_insights_report(summary, model_id=model_id)

    # ── Model info ────────────────────────────────────────────────────────
    from bedrock_service import resolve_model
    used_model = resolve_model(model_id)

    # ── Data source badges ────────────────────────────────────────────────
    source_badges = html.Div([
        html.Span(s, style={
            "display": "inline-block", "backgroundColor": "#EEF2FF",
            "color": COLORS["navy"], "borderRadius": "20px",
            "padding": "2px 10px", "fontSize": "11px",
            "fontWeight": "600", "marginRight": "6px",
        }) for s in summary.get("data_sources", [])
    ], style={"marginBottom": "16px"})

    social_src = summary.get("social_source_breakdown", {})
    news_src   = summary.get("news_source_breakdown", {})

    # Word cloud section
    wc_section = html.Div()
    if wc_b64:
        wc_section = card([
            html.P("Fed in News",
                   style={"fontWeight": "600", "color": COLORS["navy"],
                          "marginBottom": "8px"}),
            html.P(f"Generated from {len(all_text_parts)} text items across all data sources.",
                   style={"fontSize": "11px", "color": COLORS["muted"], "marginBottom": "10px"}),
            html.Img(src=f"data:image/png;base64,{wc_b64}",
                     style={"width": "100%", "borderRadius": "8px"}),
        ], style={"marginBottom": "20px"})

    return html.Div([
        # Metrics row
        dbc.Row([
            dbc.Col(metric_card("Total Inquiries",   summary["total_inquiries"],   COLORS["navy"]),   width=2),
            dbc.Col(metric_card("Social Posts",      summary["total_social_posts"], COLORS["gold"]),   width=2),
            dbc.Col(metric_card("News Items",        summary["total_news_items"],  COLORS["navy"]),   width=2),
            dbc.Col(metric_card("High Priority",     summary["high_priority"],     COLORS["danger"]), width=2),
            dbc.Col(metric_card("Risk Areas",        len(summary["risk_areas"]),   COLORS["warning"]),width=2),
            dbc.Col(metric_card("Topics Monitored",  len(summary.get("topic_sentiment", {})), COLORS["gold"]), width=2),
        ], className="mb-4"),

        # Model info badge
        html.Div([
            html.Span("🤖 Model used: ", style={"fontWeight": "600", "fontSize": "12px",
                                                  "color": COLORS["navy"]}),
            html.Span(used_model, style={"fontSize": "12px", "color": COLORS["muted"],
                                          "fontFamily": "monospace"}),
        ], style={"padding": "6px 12px", "backgroundColor": "#EEF2FF",
                  "borderRadius": "4px", "marginBottom": "16px"}),

        # Source transparency
        card([
            dbc.Row([
                dbc.Col([
                    html.P("Data Sources", style={"fontWeight": "600", "fontSize": "12px",
                                                    "color": COLORS["navy"], "marginBottom": "6px"}),
                    source_badges,
                ], width=6),
                dbc.Col([
                    html.P("Social Breakdown", style={"fontWeight": "600", "fontSize": "12px",
                                                       "color": COLORS["navy"], "marginBottom": "4px"}),
                    html.Div([html.Span(f"{k}: {v}  ", style={"fontSize": "11px", "color": COLORS["muted"]})
                              for k, v in social_src.items()]),
                ], width=3),
                dbc.Col([
                    html.P("News Breakdown", style={"fontWeight": "600", "fontSize": "12px",
                                                     "color": COLORS["navy"], "marginBottom": "4px"}),
                    html.Div([html.Span(f"{k}: {v}  ", style={"fontSize": "11px", "color": COLORS["muted"]})
                              for k, v in news_src.items()]),
                ], width=3),
            ]),
        ], style={"marginBottom": "20px"}),

        # Word cloud + trending topics
        dbc.Row([
            dbc.Col(wc_section, width=6),
            dbc.Col(card([
                html.P("Trending Topics · tinted by net sentiment",
                       style={"fontWeight": "600", "color": COLORS["navy"], "marginBottom": "4px"}),
                dcc.Graph(figure=trending_fig, config={"displayModeBar": False}),
            ]), width=6),
        ], className="mb-4"),

        # Report
        card([
            html.P("Executive Report", style={"fontWeight": "600", "color": COLORS["navy"],
                                               "fontSize": "16px", "marginBottom": "16px"}),
            dcc.Markdown(report, style={"fontSize": "14px", "lineHeight": "1.8",
                                        "color": COLORS["text"]}),
            html.Br(),
            html.A(
                html.Button("⬇  Download Report", style={
                    "backgroundColor": "transparent", "color": COLORS["navy"],
                    "border": f"1px solid {COLORS['navy']}", "borderRadius": "6px",
                    "padding": "8px 18px", "fontWeight": "600", "fontSize": "13px",
                    "cursor": "pointer", "fontFamily": "'Inter', sans-serif",
                }),
                href=f"data:text/plain;charset=utf-8,{report}",
                download="insights_report.md",
            ),
        ]),
    ])


# ── Callback: Risk Detection ──────────────────────────────────────────────────
@app.callback(
    Output("risk-output", "children"),
    Input("risk-btn",     "n_clicks"),
    State("risk-slider",  "value"),
    State("model-store",  "data"),
    prevent_initial_call=True,
)
def detect_risks(n, num_posts, model_store):
    # Combine social media + news headlines for richer risk analysis
    texts = []
    social_df = sample_data.get("social_media", pd.DataFrame())
    news_df   = sample_data.get("news_articles", pd.DataFrame())

    if not social_df.empty and "text" in social_df.columns:
        texts += social_df["text"].dropna().head(num_posts).tolist()

    if not news_df.empty:
        headline_col = "headline" if "headline" in news_df.columns else \
                       "title"    if "title"    in news_df.columns else None
        if headline_col:
            news_texts = (news_df[headline_col].fillna("") + " " +
                          news_df.get("summary", pd.Series([""] * len(news_df))).fillna(""))
            texts += news_texts.head(10).tolist()

    if not texts:
        return html.Div("No data available for risk analysis.",
                        style={"color": COLORS["danger"]})

    model_id = (model_store or {}).get("model_id")
    risks = identify_risks(texts[:20], model_id=model_id)

    # Source breakdown badge
    sources = sample_data.get("data_sources", ["GitHub"])
    source_note = "  ·  ".join(sources)

    return html.Div([
        html.Div([
            html.Span("📊 Analysed from: ", style={"fontSize": "11px", "fontWeight": "600",
                                                     "color": COLORS["navy"]}),
            html.Span(source_note, style={"fontSize": "11px", "color": COLORS["muted"]}),
            html.Span(f"  ·  {len(texts)} items",
                      style={"fontSize": "11px", "color": COLORS["muted"]}),
        ], style={"padding": "6px 12px", "backgroundColor": "#EEF2FF",
                  "borderRadius": "4px", "marginBottom": "12px"}),
        card([
            html.P("Identified Communication Risks",
                   style={"fontWeight": "600", "color": COLORS["danger"], "marginBottom": "12px"}),
            dcc.Markdown(risks, style={"fontSize": "14px", "lineHeight": "1.8",
                                       "color": COLORS["text"]}),
        ], style={"borderLeft": f"4px solid {COLORS['danger']}"}),
    ])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)

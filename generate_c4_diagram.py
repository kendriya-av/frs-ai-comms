"""
Generate C4 Container Diagram for FRBSF AI Communications System.
Outputs: c4_container_diagram.png, c4_container_diagram.pdf, c4_container_diagram.drawio
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import xml.etree.ElementTree as ET

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY    = "#0A1628"
GOLD    = "#C8A951"
BLUE    = "#1B65A6"
GREEN   = "#2E7D32"
ORANGE  = "#E65100"
GRAY    = "#6B7A99"
LIGHT   = "#EEF2FF"
WHITE   = "#FFFFFF"
TEAL    = "#00695C"
DARK_BG = "#232F3E"
PURPLE  = "#5E35B1"
RED     = "#C62828"
CYAN    = "#0277BD"

fig, ax = plt.subplots(1, 1, figsize=(26, 20))
ax.set_xlim(0, 26)
ax.set_ylim(0, 20)
ax.axis("off")
fig.patch.set_facecolor("#FAFBFE")


def draw_box(x, y, w, h, label, sublabel, color, text_color=WHITE, fontsize=8, alpha=0.95):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor=color, linewidth=1.5, alpha=alpha)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + 0.2, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, family="sans-serif")
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.2, sublabel, ha="center", va="center",
                fontsize=6, color=text_color, alpha=0.85, family="sans-serif", style="italic")


def draw_person(x, y, label, sublabel, color=NAVY):
    circle = plt.Circle((x, y + 0.55), 0.22, color=color, zorder=5)
    ax.add_patch(circle)
    ax.plot([x, x], [y + 0.33, y + 0.0], color=color, lw=2, zorder=5)
    ax.plot([x-0.25, x+0.25], [y+0.18, y+0.18], color=color, lw=2, zorder=5)
    ax.plot([x-0.18, x], [y-0.25, y+0.0], color=color, lw=2, zorder=5)
    ax.plot([x+0.18, x], [y-0.25, y+0.0], color=color, lw=2, zorder=5)
    ax.text(x, y - 0.5, label, ha="center", va="center",
            fontsize=7.5, fontweight="bold", color=color, family="sans-serif")
    ax.text(x, y - 0.75, sublabel, ha="center", va="center",
            fontsize=6, color=GRAY, family="sans-serif", style="italic")


def draw_arrow(x1, y1, x2, y2, label="", color=GRAY, style="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                                linestyle=style, connectionstyle="arc3,rad=0.0"))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.18, label, ha="center", va="center",
                fontsize=5.5, color=color, family="sans-serif",
                bbox=dict(boxstyle="round,pad=0.15", facecolor=WHITE, edgecolor="none", alpha=0.92))


def draw_boundary(x, y, w, h, label):
    rect = plt.Rectangle((x, y), w, h, linewidth=1.5, edgecolor=NAVY,
                          facecolor=LIGHT, linestyle="--", alpha=0.3, zorder=0)
    ax.add_patch(rect)
    ax.text(x + 0.3, y + h - 0.3, label, fontsize=9, fontweight="bold",
            color=NAVY, family="sans-serif", alpha=0.7)


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(13, 19.5, "C4 — Container Diagram", ha="center", fontsize=18,
        fontweight="bold", color=NAVY, family="sans-serif")
ax.text(13, 19.1, "FRBSF AI Communications Intelligence System", ha="center",
        fontsize=11, color=GOLD, family="sans-serif", fontweight="bold")

# ── Persons ───────────────────────────────────────────────────────────────────
draw_person(5, 17.5, "Communications\nOfficer", "Reviews drafts, monitors sentiment", NAVY)
draw_person(13, 17.5, "Leadership", "Views insights reports", NAVY)
draw_person(21, 17.5, "Public / Media /\nStakeholders", "Sends inquiries", BLUE)

# ── System Boundary ──────────────────────────────────────────────────────────
draw_boundary(1.5, 5.5, 23, 10.5, "FRBSF AI Communications System")

# ── Row 1: Dash App (top of boundary) ────────────────────────────────────────
draw_box(7, 13.8, 12, 1.6,
         "Dash Web Application",
         "Python, Dash/Plotly — 15-page SPA: Overview, Hub, Inquiries, Sentiment, Insights, Risks, ROI, Fed Data, Upload, Audit, Trust, Settings, Generate, Scoring, FAQ",
         NAVY, WHITE, fontsize=10)

# ── Row 2: Core services ─────────────────────────────────────────────────────
draw_box(2, 11.0, 4.2, 1.4,
         "Processing Pipeline",
         "pipeline.py — Orchestrates full flow",
         TEAL, WHITE, fontsize=8)

draw_box(7, 11.0, 4.2, 1.4,
         "Data Loader",
         "data_loader.py — Merges all sources",
         TEAL, WHITE, fontsize=8)

draw_box(12, 11.0, 4.2, 1.4,
         "Response Templates",
         "30+ templates by (category, audience)",
         TEAL, WHITE, fontsize=8)

draw_box(17, 11.0, 4.2, 1.4,
         "Data Gen Service",
         "datagen_service.py — Synthetic data",
         TEAL, WHITE, fontsize=8)

# ── Row 3: AI services + utilities ───────────────────────────────────────────
draw_box(2, 8.5, 4.8, 1.4,
         "Bedrock Service",
         "bedrock_service.py — LLM gateway (boto3)",
         ORANGE, WHITE, fontsize=8)

draw_box(7.5, 8.5, 4.8, 1.4,
         "Comprehend Service",
         "comprehend_service.py — NLP gateway (boto3)",
         ORANGE, WHITE, fontsize=8)

draw_box(13, 8.5, 4.2, 1.4,
         "Public Data Service",
         "public_data_service.py — RSS fetcher",
         GREEN, WHITE, fontsize=8)

draw_box(17.8, 8.5, 4.2, 1.4,
         "Word Cloud Utility",
         "wordcloud_util.py — PNG as base64",
         PURPLE, WHITE, fontsize=8)

# ── Row 4: Storage ───────────────────────────────────────────────────────────
draw_box(5, 6.2, 4.5, 1.2,
         "Audit Log",
         "audit_log.py — Tracks all AI actions",
         GRAY, WHITE, fontsize=8)

draw_box(11, 6.2, 4.5, 1.2,
         "Local Data Store",
         "data/ folder — JSON files",
         GRAY, WHITE, fontsize=8)

draw_box(17.5, 6.2, 4.5, 1.2,
         "Config",
         "config.py — AWS region, model, env vars",
         GRAY, WHITE, fontsize=8)

# ── External Systems ─────────────────────────────────────────────────────────
draw_box(0.3, 3.0, 4.5, 1.2,
         "Amazon Comprehend",
         "Sentiment · Classification · Key Phrases",
         ORANGE, WHITE, fontsize=8)

draw_box(5.5, 3.0, 4.5, 1.2,
         "Amazon Bedrock (Claude)",
         "Drafting · Reports · Risk · Data Gen",
         DARK_BG, WHITE, fontsize=8)

draw_box(10.8, 3.0, 4.5, 1.2,
         "Federal Reserve RSS",
         "FOMC, Press, Speeches, Research",
         GREEN, WHITE, fontsize=8)

draw_box(16, 3.0, 4.5, 1.2,
         "News Outlet RSS",
         "CNBC, NYT, Reuters, Bloomberg...",
         GREEN, WHITE, fontsize=8)

draw_box(21.2, 3.0, 4.5, 1.2,
         "GitHub Sample Data",
         "Demo inquiries, social, news",
         GRAY, WHITE, fontsize=8)

# ── Infrastructure (bottom) ──────────────────────────────────────────────────
draw_box(2.5, 0.8, 3.5, 1.0,
         "AWS App Runner",
         "Container hosting",
         BLUE, WHITE, fontsize=7.5)

draw_box(7, 0.8, 3.5, 1.0,
         "Amazon ECR",
         "Image registry",
         BLUE, WHITE, fontsize=7.5)

draw_box(11.5, 0.8, 3.5, 1.0,
         "AWS CodeBuild",
         "CI/CD pipeline",
         BLUE, WHITE, fontsize=7.5)

draw_box(16, 0.8, 3.5, 1.0,
         "Amazon S3",
         "Source artifacts",
         BLUE, WHITE, fontsize=7.5)

# ── Arrows: Persons → Dash App ───────────────────────────────────────────────
draw_arrow(5, 16.7, 10, 15.4, "Uses (HTTPS)", NAVY)
draw_arrow(13, 16.7, 13, 15.4, "Views reports", NAVY)
draw_arrow(21, 16.7, 16, 15.4, "Sends inquiries", BLUE)

# ── Arrows: Dash App → Row 2 ─────────────────────────────────────────────────
draw_arrow(9, 13.8, 4.1, 12.4, "Triggers", TEAL)
draw_arrow(11, 13.8, 9.1, 12.4, "Loads data", TEAL)
draw_arrow(15, 13.8, 14.1, 12.4, "Selects templates", TEAL)
draw_arrow(17, 13.8, 19.1, 12.4, "Generates test data", TEAL)

# ── Arrows: Dash App → Row 3 ─────────────────────────────────────────────────
draw_arrow(8, 13.8, 4.4, 9.9, "Drafts / Reports", ORANGE)
draw_arrow(12, 13.8, 9.9, 9.9, "Classifies / Sentiment", ORANGE)
draw_arrow(17, 13.8, 19.9, 9.9, "Word clouds", PURPLE)

# ── Arrows: Pipeline → services ──────────────────────────────────────────────
draw_arrow(4.1, 11.0, 4.4, 9.9, "LLM calls", ORANGE, "--")
draw_arrow(4.1, 11.5, 7.5, 9.9, "NLP calls", ORANGE, "--")
draw_arrow(2.5, 11.0, 7.5, 12.0, "", TEAL, "--")

# ── Arrows: Data Loader → sources ────────────────────────────────────────────
draw_arrow(9.1, 11.0, 15.1, 9.9, "Fetches feeds", GREEN, "--")

# ── Arrows: Services → External ──────────────────────────────────────────────
draw_arrow(4.4, 8.5, 2.5, 4.2, "detect_sentiment\nclassify_document", ORANGE)
draw_arrow(9.9, 8.5, 7.7, 4.2, "", ORANGE)
draw_arrow(4.4, 8.5, 7.7, 4.2, "invoke_model\n(boto3)", DARK_BG)
draw_arrow(15.1, 8.5, 13, 4.2, "HTTP/RSS", GREEN)
draw_arrow(15.1, 8.5, 18.2, 4.2, "HTTP/RSS", GREEN)
draw_arrow(9.1, 11.0, 23.4, 4.2, "HTTPS", GRAY)

# ── Arrows: Bedrock Svc → Audit ──────────────────────────────────────────────
draw_arrow(4.4, 8.5, 7.2, 7.4, "Logs calls", GRAY, "--")

# ── Arrows: Data Loader → Local Store ────────────────────────────────────────
draw_arrow(9.1, 11.0, 13.2, 7.4, "Reads JSON", GRAY, "--")

# ── Arrows: Infrastructure ───────────────────────────────────────────────────
draw_arrow(4.2, 1.8, 7, 1.3, "Pulls image", BLUE, "--")
draw_arrow(11.5, 1.3, 10.5, 1.3, "Pushes image", BLUE, "--")
draw_arrow(16, 1.3, 15, 1.3, "Reads source", BLUE, "--")
draw_arrow(4.2, 1.8, 13, 5.5, "Hosts app", BLUE, "--")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    (NAVY, "Core App"), (TEAL, "Service Layer"), (ORANGE, "AWS AI Gateway"),
    (GREEN, "Data Fetcher"), (PURPLE, "Utility"), (GRAY, "Storage/Config"),
    (BLUE, "AWS Infra"), (DARK_BG, "External AI"),
]
ax.text(0.3, 0.15, "Legend:", fontsize=7, fontweight="bold", color=NAVY, family="sans-serif")
for i, (clr, lbl) in enumerate(legend_items):
    rx = 2.0 + i * 2.8
    rect = FancyBboxPatch((rx, 0.0), 0.35, 0.25,
                          boxstyle="round,pad=0.05", facecolor=clr, edgecolor="none")
    ax.add_patch(rect)
    ax.text(rx + 0.45, 0.12, lbl, fontsize=6, color=NAVY, va="center", family="sans-serif")

plt.tight_layout()
plt.savefig("c4_container_diagram.png", dpi=200, bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig("c4_container_diagram.pdf", bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.close()
print("✓ Generated: c4_container_diagram.png and c4_container_diagram.pdf")

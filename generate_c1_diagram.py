"""
Generate a C1 System Context Diagram for FRBSF AI Communications System.
Run: python generate_c1_diagram.py
Output: c1_context_diagram.png, c1_context_diagram.pdf
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 15))
ax.set_xlim(0, 20)
ax.set_ylim(0, 15)
ax.axis("off")
fig.patch.set_facecolor("#FAFBFE")

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY = "#0A1628"
GOLD = "#C8A951"
BLUE = "#1B65A6"
GREEN = "#2E7D32"
ORANGE = "#E65100"
GRAY = "#6B7A99"
LIGHT = "#EEF2FF"
WHITE = "#FFFFFF"
DARK_BG = "#232F3E"


def draw_box(x, y, w, h, label, sublabel, color, text_color=WHITE, fontsize=9):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor=color, linewidth=1.5, alpha=0.95)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + 0.2, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, family="sans-serif")
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.2, sublabel, ha="center", va="center",
                fontsize=6.5, color=text_color, alpha=0.8, family="sans-serif",
                style="italic", wrap=True)


def draw_person(x, y, label, sublabel, color=NAVY):
    circle = plt.Circle((x, y + 0.6), 0.25, color=color, zorder=5)
    ax.add_patch(circle)
    ax.plot([x, x], [y + 0.35, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.plot([x - 0.3, x + 0.3], [y + 0.2, y + 0.2], color=color, linewidth=2, zorder=5)
    ax.plot([x - 0.2, x], [y - 0.3, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.plot([x + 0.2, x], [y - 0.3, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.text(x, y - 0.55, label, ha="center", va="center",
            fontsize=8, fontweight="bold", color=color, family="sans-serif")
    ax.text(x, y - 0.85, sublabel, ha="center", va="center",
            fontsize=6, color=GRAY, family="sans-serif", style="italic")


def draw_arrow(x1, y1, x2, y2, label="", color=GRAY, style="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                                linestyle=style, connectionstyle="arc3,rad=0.0"))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.18, label, ha="center", va="center",
                fontsize=6, color=color, family="sans-serif",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=WHITE,
                          edgecolor="none", alpha=0.9))


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(10, 14.6, "C1 — System Context Diagram", ha="center", fontsize=16,
        fontweight="bold", color=NAVY, family="sans-serif")
ax.text(10, 14.2, "FRBSF AI Communications Intelligence System", ha="center",
        fontsize=10, color=GOLD, family="sans-serif", fontweight="bold")

# ── Persons (top) ─────────────────────────────────────────────────────────────
draw_person(3.5, 12.2, "Communications\nOfficer",
            "Reviews drafts, selects templates,\nmonitors sentiment, tracks ROI", NAVY)
draw_person(10, 12.2, "Leadership /\nExecutives",
            "Views insights reports & exports,\nmonitors trends and risk areas", NAVY)
draw_person(16.5, 12.2, "Public / Media /\nStakeholders",
            "Sends inquiries, receives\ntemplate-based responses", BLUE)

# ── Central System ────────────────────────────────────────────────────────────
draw_box(4.5, 8.2, 11, 2.2,
         "FRBSF AI Communications System",
         "15-page Dash app · Classifies inquiries · Template-based drafting · Sentiment monitoring\n"
         "Risk detection · Executive reports with word clouds · ROI calculator · Audit trail · Trust & Safety",
         NAVY, WHITE, fontsize=11)

# ── Arrows from persons to system ─────────────────────────────────────────────
draw_arrow(3.5, 11.3, 7.5, 10.4, "Uses (HTTPS)", NAVY)
draw_arrow(10, 11.3, 10, 10.4, "Views reports & exports", NAVY)
draw_arrow(16.5, 11.3, 13.5, 10.4, "Sends inquiries", BLUE)

# ── AWS AI Services (left) ────────────────────────────────────────────────────
draw_box(0.3, 5.0, 4.2, 1.4,
         "Amazon Comprehend",
         "Sentiment · Classification · Key Phrases\nEntities · Batch analysis",
         ORANGE, WHITE, fontsize=9)

draw_box(0.3, 3.0, 4.2, 1.4,
         "Amazon Bedrock (Claude)",
         "Drafting · Reports · Risk Detection\nTest Data Gen · 7 model options",
         DARK_BG, WHITE, fontsize=9)

# ── Data Sources (right) ─────────────────────────────────────────────────────
draw_box(15.5, 5.0, 4.2, 1.4,
         "Public RSS Feeds",
         "Fed, FRBSF, CNBC, Reuters, Bloomberg\nNYT, WaPo, MarketWatch, NPR, AP,\nYahoo Finance, Axios (13+ outlets)",
         GREEN, WHITE, fontsize=8)

draw_box(15.5, 3.0, 4.2, 1.4,
         "GitHub Sample Data",
         "Demo inquiries, social posts,\nnews articles, response templates",
         GRAY, WHITE, fontsize=8)

# ── AWS Infrastructure (bottom) ──────────────────────────────────────────────
draw_box(2.0, 0.5, 3.2, 1.0,
         "AWS App Runner",
         "Container hosting",
         BLUE, WHITE, fontsize=8)

draw_box(6.0, 0.5, 3.0, 1.0,
         "Amazon ECR",
         "Image registry",
         BLUE, WHITE, fontsize=8)

draw_box(9.8, 0.5, 3.2, 1.0,
         "AWS CodeBuild",
         "CI/CD pipeline",
         BLUE, WHITE, fontsize=8)

draw_box(13.8, 0.5, 3.0, 1.0,
         "Amazon S3",
         "Source artifacts",
         BLUE, WHITE, fontsize=8)

# ── Arrows: System ↔ AWS AI ──────────────────────────────────────────────────
draw_arrow(4.5, 8.8, 4.5, 6.4, "Classify / Sentiment /\nEntities / Key Phrases (boto3)", ORANGE)
draw_arrow(4.5, 8.4, 4.5, 4.4, "Draft / Report / Risk /\nTest Data Gen (boto3)", DARK_BG)

# ── Arrows: System ↔ Data Sources ────────────────────────────────────────────
draw_arrow(15.5, 8.8, 15.5, 6.4, "Fetch live data\n13+ outlets (HTTP/RSS)", GREEN)
draw_arrow(15.5, 8.4, 15.5, 4.4, "Load samples\n(HTTPS)", GRAY)

# ── Arrows: Infrastructure ───────────────────────────────────────────────────
draw_arrow(10, 8.2, 3.6, 1.5, "Hosted on", BLUE, style="--")
draw_arrow(3.6, 1.0, 6.0, 1.0, "Pulls image", BLUE, style="--")
draw_arrow(9.8, 1.0, 9.0, 1.0, "Pushes image", BLUE, style="--")
draw_arrow(13.8, 1.0, 13.0, 1.0, "Reads source", BLUE, style="--")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_y = 0.0
ax.text(0.3, legend_y, "Legend:", fontsize=7, fontweight="bold", color=NAVY,
        family="sans-serif")
for i, (clr, lbl) in enumerate([
    (NAVY, "Core System"), (ORANGE, "AWS AI Service"), (DARK_BG, "AWS LLM"),
    (GREEN, "External Data"), (BLUE, "AWS Infrastructure"), (GRAY, "Sample Data"),
]):
    rect = FancyBboxPatch((2.0 + i * 2.8, legend_y - 0.15), 0.4, 0.3,
                          boxstyle="round,pad=0.05", facecolor=clr, edgecolor="none")
    ax.add_patch(rect)
    ax.text(2.5 + i * 2.8, legend_y, lbl, fontsize=6.5, color=NAVY,
            va="center", family="sans-serif")

plt.tight_layout()
plt.savefig("c1_context_diagram.png", dpi=200, bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig("c1_context_diagram.pdf", bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
print("✓ Generated: c1_context_diagram.png and c1_context_diagram.pdf")

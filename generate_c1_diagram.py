"""
Generate a C1 System Context Diagram for FRBSF AI Communications System.
Run: python generate_c1_diagram.py
Output: c1_context_diagram.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 13))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
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
RED = "#C62828"

# ── Helper: draw a box ───────────────────────────────────────────────────────
def draw_box(ax, x, y, w, h, label, sublabel, color, text_color=WHITE, fontsize=9):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor=color, linewidth=1.5, alpha=0.95)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + 0.18, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, family="sans-serif")
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.22, sublabel, ha="center", va="center",
                fontsize=7, color=text_color, alpha=0.8, family="sans-serif",
                style="italic", wrap=True)

def draw_person(ax, x, y, label, sublabel, color=NAVY):
    circle = plt.Circle((x, y + 0.6), 0.25, color=color, zorder=5)
    ax.add_patch(circle)
    ax.plot([x, x], [y + 0.35, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.plot([x - 0.3, x + 0.3], [y + 0.2, y + 0.2], color=color, linewidth=2, zorder=5)
    ax.plot([x - 0.2, x], [y - 0.3, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.plot([x + 0.2, x], [y - 0.3, y + 0.0], color=color, linewidth=2, zorder=5)
    ax.text(x, y - 0.55, label, ha="center", va="center",
            fontsize=8, fontweight="bold", color=color, family="sans-serif")
    ax.text(x, y - 0.8, sublabel, ha="center", va="center",
            fontsize=6.5, color=GRAY, family="sans-serif", style="italic")

def draw_arrow(ax, x1, y1, x2, y2, label="", color=GRAY, style="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                                linestyle=style, connectionstyle="arc3,rad=0.0"))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha="center", va="center",
                fontsize=6, color=color, family="sans-serif",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=WHITE, edgecolor="none", alpha=0.9))

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(9, 12.6, "C1 — System Context Diagram", ha="center", fontsize=16,
        fontweight="bold", color=NAVY, family="sans-serif")
ax.text(9, 12.25, "FRBSF AI Communications Intelligence System", ha="center",
        fontsize=10, color=GOLD, family="sans-serif", fontweight="bold")

# ── Persons (top) ─────────────────────────────────────────────────────────────
draw_person(ax, 3.5, 10.5, "Communications\nOfficer", "Reviews drafts, monitors sentiment", NAVY)
draw_person(ax, 9, 10.5, "Leadership", "Views insights reports", NAVY)
draw_person(ax, 14.5, 10.5, "Public / Media /\nStakeholders", "Sends inquiries", BLUE)

# ── Central System ────────────────────────────────────────────────────────────
draw_box(ax, 5.5, 7.0, 7, 2.0,
         "FRBSF AI Communications System",
         "Classifies inquiries · Monitors sentiment · Drafts responses · Detects risks · Generates reports",
         NAVY, WHITE, fontsize=11)

# ── Arrows from persons to system ─────────────────────────────────────────────
draw_arrow(ax, 3.5, 9.6, 7.0, 9.0, "Uses (HTTPS)", NAVY)
draw_arrow(ax, 9, 9.6, 9, 9.0, "Views reports", NAVY)
draw_arrow(ax, 14.5, 9.6, 12.0, 9.0, "Sends inquiries", BLUE)

# ── AWS AI Services (left) ────────────────────────────────────────────────────
draw_box(ax, 0.3, 4.2, 3.8, 1.2,
         "Amazon Comprehend",
         "Sentiment · Classification · Key Phrases",
         ORANGE, WHITE, fontsize=9)

draw_box(ax, 0.3, 2.4, 3.8, 1.2,
         "Amazon Bedrock (Claude)",
         "Drafting · Reports · Risk Detection",
         "#232F3E", WHITE, fontsize=9)

# ── Data Sources (right) ─────────────────────────────────────────────────────
draw_box(ax, 13.8, 4.2, 3.8, 1.2,
         "Public RSS Feeds",
         "Fed, CNBC, Reuters, Bloomberg, NYT...",
         GREEN, WHITE, fontsize=9)

draw_box(ax, 13.8, 2.4, 3.8, 1.2,
         "GitHub Sample Data",
         "Demo inquiries, social posts, news",
         GRAY, WHITE, fontsize=9)

# ── AWS Infrastructure (bottom) ──────────────────────────────────────────────
draw_box(ax, 2.5, 0.3, 2.8, 1.0,
         "AWS App Runner",
         "Container hosting",
         BLUE, WHITE, fontsize=8)

draw_box(ax, 6.0, 0.3, 2.5, 1.0,
         "Amazon ECR",
         "Image registry",
         BLUE, WHITE, fontsize=8)

draw_box(ax, 9.2, 0.3, 2.8, 1.0,
         "AWS CodeBuild",
         "CI/CD pipeline",
         BLUE, WHITE, fontsize=8)

draw_box(ax, 12.7, 0.3, 2.5, 1.0,
         "Amazon S3",
         "Source artifacts",
         BLUE, WHITE, fontsize=8)

# ── Arrows: System ↔ AWS AI ──────────────────────────────────────────────────
draw_arrow(ax, 5.5, 7.5, 4.1, 5.4, "Classify / Sentiment\n(boto3)", ORANGE)
draw_arrow(ax, 5.5, 7.2, 4.1, 3.6, "Draft / Report / Risk\n(boto3)", "#232F3E")

# ── Arrows: System ↔ Data Sources ────────────────────────────────────────────
draw_arrow(ax, 12.5, 7.5, 13.8, 5.4, "Fetch live data\n(HTTP/RSS)", GREEN)
draw_arrow(ax, 12.5, 7.2, 13.8, 3.6, "Load samples\n(HTTPS)", GRAY)

# ── Arrows: Infrastructure ───────────────────────────────────────────────────
draw_arrow(ax, 9, 7.0, 3.9, 1.3, "Hosted on", BLUE, style="--")
draw_arrow(ax, 3.9, 0.8, 6.0, 0.8, "Pulls image", BLUE, style="--")
draw_arrow(ax, 9.2, 0.8, 8.5, 0.8, "Pushes image", BLUE, style="--")
draw_arrow(ax, 12.7, 0.8, 12.0, 0.8, "Reads source", BLUE, style="--")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_y = 0.0
ax.text(0.3, legend_y, "Legend:", fontsize=7, fontweight="bold", color=NAVY, family="sans-serif")
for i, (clr, lbl) in enumerate([
    (NAVY, "Core System"), (ORANGE, "AWS AI Service"),
    (GREEN, "External Data"), (BLUE, "AWS Infrastructure"), (GRAY, "Sample Data"),
]):
    rect = FancyBboxPatch((2.0 + i * 2.8, legend_y - 0.15), 0.4, 0.3,
                          boxstyle="round,pad=0.05", facecolor=clr, edgecolor="none")
    ax.add_patch(rect)
    ax.text(2.5 + i * 2.8, legend_y, lbl, fontsize=6.5, color=NAVY, va="center", family="sans-serif")

plt.tight_layout()
plt.savefig("c1_context_diagram.png", dpi=200, bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig("c1_context_diagram.pdf", bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
print("✓ Generated: c1_context_diagram.png and c1_context_diagram.pdf")

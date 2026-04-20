"""
Generate Component Diagram for FRBSF AI Communications System.
Outputs: component_diagram.png, component_diagram.pdf, component_diagram.drawio
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

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
CYAN    = "#0277BD"
PINK    = "#AD1457"

fig, ax = plt.subplots(1, 1, figsize=(30, 22))
ax.set_xlim(0, 30)
ax.set_ylim(0, 22)
ax.axis("off")
fig.patch.set_facecolor("#FAFBFE")


def draw_box(x, y, w, h, label, sublabel, color, text_color=WHITE, fontsize=7.5, alpha=0.95):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                         facecolor=color, edgecolor=color, linewidth=1.2, alpha=alpha)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + 0.18, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, family="sans-serif")
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.15, sublabel, ha="center", va="center",
                fontsize=5.5, color=text_color, alpha=0.85, family="sans-serif", style="italic")


def draw_arrow(x1, y1, x2, y2, label="", color=GRAY, style="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9,
                                linestyle=style, connectionstyle="arc3,rad=0.0"))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.15, label, ha="center", va="center",
                fontsize=5, color=color, family="sans-serif",
                bbox=dict(boxstyle="round,pad=0.12", facecolor=WHITE, edgecolor="none", alpha=0.92))


def draw_boundary(x, y, w, h, label):
    rect = plt.Rectangle((x, y), w, h, linewidth=1.5, edgecolor=NAVY,
                          facecolor=LIGHT, linestyle="--", alpha=0.25, zorder=0)
    ax.add_patch(rect)
    ax.text(x + 0.3, y + h - 0.3, label, fontsize=9, fontweight="bold",
            color=NAVY, family="sans-serif", alpha=0.7)


def draw_section_label(x, y, label, color=NAVY):
    ax.text(x, y, label, fontsize=8, fontweight="bold", color=color,
            family="sans-serif", alpha=0.6)


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(15, 21.5, "Component Diagram — Dash Web Application", ha="center",
        fontsize=18, fontweight="bold", color=NAVY, family="sans-serif")
ax.text(15, 21.1, "FRBSF AI Communications Intelligence System", ha="center",
        fontsize=11, color=GOLD, family="sans-serif", fontweight="bold")

# ── Main Boundary ────────────────────────────────────────────────────────────
draw_boundary(0.5, 3.5, 29, 17, "Dash Web Application (app.py)")

# ── Section: Sidebar + Stores ────────────────────────────────────────────────
draw_section_label(1.2, 19.8, "Navigation & State")
draw_box(1, 18.8, 3.5, 0.9, "Sidebar Navigation", "15-item nav menu", NAVY, WHITE, 7.5)
draw_box(5, 18.8, 4.5, 0.9, "Client-Side Stores", "uploaded-data, model-store, refresh-signal, data-source", PURPLE, WHITE, 7)

# ── Section: UI Pages — Row 1 (Primary) ──────────────────────────────────────
draw_section_label(1.2, 18.0, "Primary Pages")

pages_row1 = [
    (1,   "Overview", "/ — KPI dashboard"),
    (4.8, "Communications Hub", "/hub — Trends, Alerts"),
    (8.6, "Inquiry & Response", "/inquiries — Queue, Drafts"),
    (12.4,"Sentiment Monitor", "/sentiment — Charts, Trends"),
    (16.2,"Insights Report", "/insights — AI Report, Export"),
    (20,  "Risk Detector", "/risks — Risk scanning"),
    (23.8,"ROI Calculator", "/roi — Cost savings"),
]
for x, name, sub in pages_row1:
    draw_box(x, 16.8, 3.5, 1.0, name, sub, BLUE, WHITE, 7)

# ── Section: UI Pages — Row 2 (Secondary) ────────────────────────────────────
draw_section_label(1.2, 16.0, "Secondary Pages")

pages_row2 = [
    (1,   "Live Fed Data", "/feddata — RSS feeds"),
    (4.8, "Upload Data", "/upload — JSON upload"),
    (8.6, "Audit Log", "/audit — AI action log"),
    (12.4,"Trust & Safety", "/trust — Guardrails"),
    (16.2,"AI Model Config", "/settings — Model select"),
]
for x, name, sub in pages_row2:
    draw_box(x, 14.8, 3.5, 1.0, name, sub, CYAN, WHITE, 7)

# ── Section: UI Pages — Row 3 (Developer/Test — greyed out in app) ───────────
draw_section_label(1.2, 14.0, "Developer / Test Pages (greyed out in nav)")

pages_row3 = [
    (1,   "Generate Test Data", "/generate — Synthetic data"),
    (4.8, "Scoring & AI Info", "/scoring — Methodology"),
    (8.6, "FAQ & Help", "/faq — User guide"),
]
for x, name, sub in pages_row3:
    draw_box(x, 12.8, 3.5, 1.0, name, sub, GRAY, WHITE, 7)

# ── Section: Callback Handlers ───────────────────────────────────────────────
draw_section_label(1.2, 12.0, "Backend Callback Handlers")

handlers = [
    (1,   "Upload Handler", "Parse + validate JSON", PINK),
    (4.8, "Classification\nHandler", "Batch classify all", PINK),
    (8.6, "Draft Handler", "AI draft + template", PINK),
    (12.4,"Insights Generator", "Build summary + report", PINK),
    (16.2,"Risk Detector\nHandler", "Social media risks", PINK),
    (20,  "Live Data Refresh", "Fetch RSS + sentiment", PINK),
    (23.8,"Report Exporter", "MD/HTML/DOCX/PDF", PINK),
]
for x, name, sub, clr in handlers:
    draw_box(x, 10.8, 3.5, 1.0, name, sub, clr, WHITE, 7)

# ── External Service Modules (below boundary) ────────────────────────────────
draw_section_label(1.2, 3.0, "Service Modules (external to app.py)")

services = [
    (0.5,  "Bedrock Service", "bedrock_service.py\nLLM gateway → Bedrock", ORANGE),
    (4.5,  "Comprehend Service", "comprehend_service.py\nNLP gateway → Comprehend", ORANGE),
    (8.5,  "Public Data Service", "public_data_service.py\nRSS fetcher (13+ outlets)", GREEN),
    (12.5, "Data Loader", "data_loader.py\nMerges all data sources", TEAL),
    (16.5, "Response Templates", "response_templates.py\n30+ templates", TEAL),
    (20.5, "Data Gen Service", "datagen_service.py\nSynthetic data via Bedrock", TEAL),
    (24.5, "Audit Log / WordCloud\n/ Config / Pipeline", "audit_log.py, wordcloud_util.py\nconfig.py, pipeline.py", GRAY),
]
for x, name, sub, clr in services:
    draw_box(x, 1.0, 3.8, 1.6, name, sub, clr, WHITE, 7)

# ── Arrows: Sidebar → Pages ──────────────────────────────────────────────────
for x, _, _ in pages_row1:
    draw_arrow(2.75, 18.8, x + 1.75, 17.8, "", NAVY, "--")

# ── Arrows: Pages → Handlers ─────────────────────────────────────────────────
# Upload → Upload Handler
draw_arrow(6.55, 14.8, 2.75, 11.8, "File upload", PINK)
# Inquiry → Classification Handler
draw_arrow(10.35, 16.8, 6.55, 11.8, "Classify All", PINK)
# Inquiry → Draft Handler
draw_arrow(10.35, 16.8, 10.35, 11.8, "Generate Draft", PINK)
# Insights → Insights Generator
draw_arrow(17.95, 16.8, 14.15, 11.8, "Generate Report", PINK)
# Risks → Risk Handler
draw_arrow(21.75, 16.8, 17.95, 11.8, "Detect Risks", PINK)
# Fed Data → Live Refresh
draw_arrow(2.75, 14.8, 21.75, 11.8, "Fetch Now", PINK)
# Insights → Report Exporter
draw_arrow(17.95, 16.8, 25.55, 11.8, "Download", PINK)

# ── Arrows: Handlers → Services ──────────────────────────────────────────────
# Classification Handler → Comprehend
draw_arrow(6.55, 10.8, 6.4, 2.6, "Classify + sentiment", ORANGE)
# Draft Handler → Bedrock
draw_arrow(10.35, 10.8, 2.4, 2.6, "Generate draft", ORANGE)
# Draft Handler → Templates
draw_arrow(10.35, 10.8, 18.4, 2.6, "Select template", TEAL)
# Insights Generator → Bedrock
draw_arrow(14.15, 10.8, 2.4, 2.6, "", ORANGE, "--")
# Insights Generator → WordCloud (in combined box)
draw_arrow(14.15, 10.8, 26.4, 2.6, "Word cloud", GRAY, "--")
# Risk Handler → Bedrock
draw_arrow(17.95, 10.8, 2.4, 2.6, "", ORANGE, "--")
# Live Refresh → Public Data Service
draw_arrow(21.75, 10.8, 10.4, 2.6, "Fetch RSS", GREEN)
# Live Refresh → Comprehend
draw_arrow(21.75, 10.8, 6.4, 2.6, "", ORANGE, "--")
# Generate page → Data Gen Service
draw_arrow(2.75, 12.8, 22.4, 2.6, "Generate data", TEAL)
# Upload Handler → Stores
draw_arrow(2.75, 11.8, 7.25, 18.8, "Update store", PURPLE, "--")
# Overview → Data Loader
draw_arrow(2.75, 16.8, 14.4, 2.6, "Load data", TEAL, "--")
# Audit page → Audit service
draw_arrow(10.35, 14.8, 26.4, 2.6, "Read log", GRAY, "--")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    (BLUE, "Primary Page"), (CYAN, "Secondary Page"), (GRAY, "Dev/Test Page"),
    (PINK, "Callback Handler"), (ORANGE, "AWS AI Service"), (GREEN, "Data Fetcher"),
    (TEAL, "Service Module"), (PURPLE, "Client Store"),
]
ax.text(0.5, 0.2, "Legend:", fontsize=7, fontweight="bold", color=NAVY, family="sans-serif")
for i, (clr, lbl) in enumerate(legend_items):
    rx = 2.2 + i * 3.3
    rect = FancyBboxPatch((rx, 0.05), 0.35, 0.25,
                          boxstyle="round,pad=0.05", facecolor=clr, edgecolor="none")
    ax.add_patch(rect)
    ax.text(rx + 0.45, 0.17, lbl, fontsize=6, color=NAVY, va="center", family="sans-serif")

plt.tight_layout()
plt.savefig("component_diagram.png", dpi=200, bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig("component_diagram.pdf", bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.close()
print("✓ Generated: component_diagram.png and component_diagram.pdf")

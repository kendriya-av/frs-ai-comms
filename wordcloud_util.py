"""
Generate word cloud image as base64 for embedding in Dash.
"""

import base64
import io
from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_wordcloud_base64(text: str, width: int = 600, height: int = 300,
                               bg_color: str = "white",
                               colormap: str = "Blues") -> str:
    """Generate a word cloud PNG from text and return as base64 string."""
    if not text or not text.strip():
        return ""

    wc = WordCloud(
        width=width, height=height,
        background_color=bg_color,
        colormap=colormap,
        max_words=80,
        prefer_horizontal=0.7,
        min_font_size=10,
    ).generate(text)

    buf = io.BytesIO()
    plt.figure(figsize=(width / 100, height / 100), dpi=100)
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

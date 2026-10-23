import re
from markdownify import markdownify as md
from content.clean_html import clean_html


KEEP_IMAGES_IN = [
    "td",
    "th",
    "p",
    "a",
    "strong",
    "b",
    "em",
    "i",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "figure",
]

INVISIBLE_CHARS = ["\u200b", "\u200c", "\u200d", "\ufeff"]


def normalize_spaces(text: str) -> str:
    text = text.replace("\u00a0", " ")
    for char in INVISIBLE_CHARS:
        text = text.replace(char, "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def html_to_md(html: str) -> str:
    cleaned_html = clean_html(html)
    markdown = md(
        cleaned_html,
        heading_style="ATX",
        bullets="-",
        keep_inline_images_in=KEEP_IMAGES_IN,
        escape_underscores=False,
    )
    markdown = normalize_spaces(markdown)
    return markdown.strip() + "\n"


if __name__ == "__main__":
    with open("tests/scraper/article_body.html", "r", encoding="utf-8") as f:
        html = f.read()
    print(html_to_md(html))

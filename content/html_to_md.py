from markdownify import markdownify as md
from content.clean_html import clean_html


def html_to_md(html: str) -> str:
    cleaned_html = clean_html(html)
    markdown = md(cleaned_html, heading_style="ATX", bullets="-")
    return markdown.strip() + "\n"


if __name__ == "__main__":
    with open("tests/scraper/article_body.html", "r", encoding="utf-8") as f:
        html = f.read()
    print(html_to_md(html))

import hashlib
from content.html_to_md import html_to_md


def make_slug(htmlUrl: str) -> str:
    lastPart = htmlUrl.rstrip("/").split("/")[-1]
    return lastPart.lower()


def render_article(article: dict) -> str:
    bodyMd = html_to_md(article["body"])
    lastUpdated = article["edited_at"][:10]
    header = (
        f"# {article['title']}\n"
        f"\n"
        f"Article URL: {article['html_url']}\n"
        f"Last updated: {lastUpdated}\n"
        f"\n"
    )
    return header + bodyMd


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    with open("tests/scraper/article_body.html", "r", encoding="utf-8") as f:
        body = f.read()

    article = {
        "title": "How to Use the Eventbrite Events App",
        "html_url": "https://support.optisigns.com/hc/en-us/articles/56498391179667-How-to-Use-the-Eventbrite-Events-App",
        "edited_at": "2026-10-16T21:21:54Z",
        "body": body,
    }

    text = render_article(article)
    print(text[:400])
    print("slug:", make_slug(article["html_url"]))
    print("hash:", content_hash(text))

from content.article_file import content_hash, make_slug, render_article

ARTICLE = {
    "title": "How to Use the Eventbrite Events App",
    "html_url": "https://support.optisigns.com/hc/en-us/articles/56498391179667-How-to-Use-the-Eventbrite-Events-App",
    "edited_at": "2026-10-16T21:21:54Z",
    "body": "<h2>Display</h2><p>Shows events.</p>",
}


def test_make_slug():
    assert make_slug(ARTICLE["html_url"]) == "56498391179667-how-to-use-the-eventbrite-events-app"
    assert make_slug("https://x.com/hc/en-us/articles/1-Abc/") == "1-abc"


def test_render_article_header():
    text = render_article(ARTICLE)
    assert text.startswith("# How to Use the Eventbrite Events App\n\n")
    assert "Article URL: " + ARTICLE["html_url"] in text
    assert "Last updated: 2026-10-16" in text
    assert "## Display" in text


def test_content_hash_is_stable_and_sensitive():
    text = render_article(ARTICLE)
    assert content_hash(text) == content_hash(render_article(ARTICLE))
    assert len(content_hash(text)) == 64
    assert content_hash(text) != content_hash(text + " ")

from content.clean_html import clean_html, slugify

FIXTURE_PATH = "tests/scraper/article_body.html"


def read_fixture() -> str:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_slugify_matches_github_heading_ids():
    assert slugify("What You'll Need") == "what-youll-need"
    assert (
        slugify("  Creating an Eventbrite Events App ")
        == "creating-an-eventbrite-events-app"
    )


def test_removes_noise_attributes_and_wrappers():
    cleaned = clean_html(
        '<h3 id="h_01"><span style="color:#434343">Display</span></h3>'
        '<li data-list-item-id="x"><a href="https://x.com" target="_blank">Link</a></li>'
    )
    assert cleaned == '<h3>Display</h3><li><a href="https://x.com">Link</a></li>'


def test_rewrites_anchor_links_and_drops_markers():
    html = (
        '<a href="#Need">Need</a><p><a name="Need"></a></p><h2>What You\'ll Need</h2>'
    )
    cleaned = clean_html(html)
    assert 'href="#what-youll-need"' in cleaned
    assert "name=" not in cleaned
    assert "<p></p>" not in cleaned


def test_heading_id_target_is_rewritten():
    cleaned = clean_html('<a href="#h_01">go</a><h2 id="h_01">Display</h2>')
    assert 'href="#display"' in cleaned


def test_one_column_table_becomes_blockquote():
    html = (
        "<figure><table><tr><td><p><strong>NOTE</strong></p></td></tr>"
        "<tr><td>Eventbrite has no search.</td></tr></table></figure>"
    )
    cleaned = clean_html(html)
    assert "<table" not in cleaned
    assert "<blockquote>" in cleaned
    assert "Eventbrite has no search." in cleaned


def test_multi_column_table_is_kept():
    cleaned = clean_html(
        "<table><tr><td>Plan</td><td>Price</td></tr><tr><td>Pro</td><td>$15</td></tr></table>"
    )
    assert "<table>" in cleaned
    assert "<blockquote>" not in cleaned


def test_base64_image_replaced_by_alt_or_removed():
    cleaned = clean_html(
        '<p><img alt="QR menu" src="data:image/png;base64,AAAA"/></p>'
        '<p><img src="data:image/png;base64,BBBB"/></p>'
    )
    assert "data:image" not in cleaned
    assert "QR menu" in cleaned


def test_iframe_becomes_link():
    cleaned = clean_html('<iframe src="//www.youtube.com/embed/abc"></iframe>')
    assert (
        '<a href="https://www.youtube.com/embed/abc">Embedded content (www.youtube.com)</a>'
        in cleaned
    )


def test_empty_heading_removed_and_heading_bold_unwrapped():
    cleaned = clean_html("<h2> </h2><h4><strong>1. Prepare</strong></h4>")
    assert cleaned == "<h4>1. Prepare</h4>"


def test_fixture_has_no_leftover_noise():
    cleaned = clean_html(read_fixture())
    for noise in ["style=", "id=", "data-list-item-id", "<span", "name="]:
        assert noise not in cleaned
    assert cleaned.count('href="#') == 6

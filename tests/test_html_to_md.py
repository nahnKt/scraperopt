from content.html_to_md import html_to_md, normalize_spaces


def test_headings_lists_links_and_images():
    markdown = html_to_md(
        '<h2>Display</h2><ul><li><a href="#x">One</a></li></ul>'
        '<p><img alt="Screen" src="https://x.com/a.png"/></p>'
    )
    assert "## Display" in markdown
    assert "- [One](#x)" in markdown
    assert "![Screen](https://x.com/a.png)" in markdown


def test_images_inside_tables_are_kept():
    markdown = html_to_md(
        "<table><tr><td>A</td><td>B</td></tr>"
        '<tr><td><figure><img src="https://x.com/a.png"/></figure></td>'
        '<td><p><img src="https://x.com/b.png"/></p></td></tr></table>'
    )
    assert "![](https://x.com/a.png)" in markdown
    assert "![](https://x.com/b.png)" in markdown


def test_underscores_are_not_escaped():
    assert "access_token" in html_to_md("<p>Use the access_token value.</p>")


def test_normalize_spaces():
    assert normalize_spaces("a b​c\n\n\n\nd") == "a bc\n\nd"


def test_output_ends_with_single_newline():
    markdown = html_to_md("<p>Hello</p>")
    assert markdown == "Hello\n"

from bs4 import BeautifulSoup
import re

KEEP_ATTRS = {"href", "src", "alt"}
HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
CALLOUT_LABELS = {"NOTE", "TIP", "WARNING", "IMPORTANT", "CAUTION"}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def anchor_keys(tag) -> list[str]:
    keys = []
    if tag.has_attr("id"):
        keys.append(tag["id"])
    if tag.name == "a" and tag.has_attr("name"):
        keys.append(tag["name"])
    return keys


def is_empty_marker(tag) -> bool:
    return (
        tag.name == "a"
        and not tag.has_attr("href")
        and tag.get_text(strip=True) == ""
        and tag.find() is None
    )


# Rewrite in-page hrefs to the heading slug
def fix_link_targets(soup: BeautifulSoup) -> None:
    mapping = {}  # old name or id -> heading slug
    markers = []  # list of <a name> tags to be removed

    for tag in soup.find_all(True):
        keys = anchor_keys(tag)
        if not keys:
            continue

        # id on the heading itself, or an empty <a name> before it.
        if tag.name in HEADINGS:
            heading = tag
        else:
            heading = tag.find_next(HEADINGS)

        if heading is not None:
            for key in keys:
                # Slug comes from the heading text. Duplicate headings share one slug.
                mapping[key] = slugify(heading.get_text())

        if is_empty_marker(tag):
            markers.append(tag)

    for marker in markers:
        parent = marker.parent
        marker.decompose()
        if (
            parent.name == "p"
            and parent.get_text(strip=True) == ""
            and parent.find() is None
        ):
            parent.decompose()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Only #fragments. The new href matches GitHub's heading id.
        if href.startswith("#") and href[1:] in mapping:
            link["href"] = "#" + mapping[href[1:]]


def clean_callouts(soup: BeautifulSoup) -> None:
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) != 2:
            continue

        label = rows[0].get_text(strip=True).upper().rstrip(":")
        if label not in CALLOUT_LABELS:
            continue

        bodyCell = rows[1].find(["td", "th"])
        if bodyCell is None:
            continue

        quote = soup.new_tag("blockquote")
        title = soup.new_tag("strong")
        title.string = label + ":"
        quote.append(title)
        quote.append(" ")
        for child in list(bodyCell.contents):
            quote.append(child)

        if table.parent is not None and table.parent.name == "figure":
            table.parent.replace_with(quote)
        else:
            table.replace_with(quote)


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    fix_link_targets(soup)
    clean_callouts(soup)
    for tag in soup.find_all(["span", "font"]):
        tag.unwrap()

    for tag in soup.find_all(True):
        new_attrs = {}
        for key, value in tag.attrs.items():
            if key in KEEP_ATTRS:
                new_attrs[key] = value
        tag.attrs = new_attrs

    return str(soup)


if __name__ == "__main__":
    with open("tests/scraper/article_body.html", "r", encoding="utf-8") as f:
        html = f.read()
    print(clean_html(html))

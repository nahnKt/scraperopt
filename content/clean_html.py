from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

KEEP_ATTRS = {"href", "src", "alt"}
HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


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
        if len(rows) == 0:
            continue

        cells = []
        for row in rows:
            rowCells = row.find_all(["td", "th"])
            if len(rowCells) != 1:
                cells = []
                break
            cells.append(rowCells[0])
        if not cells:
            continue

        quote = soup.new_tag("blockquote")

        if len(cells) >= 2:
            labelText = cells[0].get_text(" ", strip=True)
            if labelText != "":
                titleLine = soup.new_tag("p")
                title = soup.new_tag("strong")
                title.string = labelText
                titleLine.append(title)
                quote.append(titleLine)
            bodyCells = cells[1:]
        else:
            bodyCells = cells

        for cell in bodyCells:
            part = soup.new_tag("div")
            for child in list(cell.contents):
                part.append(child)
            quote.append(part)

        if table.parent is not None and table.parent.name == "figure":
            table.parent.replace_with(quote)
        else:
            table.replace_with(quote)


def clean_media(soup: BeautifulSoup) -> None:
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:"):
            altText = img.get("alt", "").strip()
            if altText:
                img.replace_with(altText)
            else:
                img.decompose()

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "").strip()
        if src.startswith("//"):
            src = "https:" + src
        if src == "":
            iframe.decompose()
            continue

        domain = urlparse(src).netloc
        link = soup.new_tag("a", href=src)
        link.string = "Embedded content (" + domain + ")"
        line = soup.new_tag("p")
        line.append(link)
        iframe.replace_with(line)


def clean_headings(soup: BeautifulSoup) -> None:
    for heading in soup.find_all(HEADINGS):
        if heading.get_text(strip=True) == "" and heading.find("img") is None:
            heading.decompose()
            continue

        for boldTag in heading.find_all(["strong", "b"]):
            boldTag.unwrap()


def strip_formatting(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["span", "font"]):
        tag.unwrap()

    for tag in soup.find_all(True):
        newAttrs = {}
        for key, value in tag.attrs.items():
            if key in KEEP_ATTRS:
                newAttrs[key] = value
        tag.attrs = newAttrs


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    fix_link_targets(soup)
    clean_callouts(soup)
    clean_media(soup)
    clean_headings(soup)
    strip_formatting(soup)
    return str(soup)


if __name__ == "__main__":
    with open("tests/scraper/article_body.html", "r", encoding="utf-8") as f:
        html = f.read()
    print(clean_html(html))

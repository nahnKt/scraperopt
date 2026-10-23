import os
from content.article_file import render_article, make_slug
from source.zendesk import fetch_all_articles, BASE_URL, NUMBER_OF_ARTICLES_PER_PAGE

OUTPUT_DIR = "articles"


def save_article(article: dict) -> str:
    slug = make_slug(article["html_url"])
    text = render_article(article)
    path = os.path.join(OUTPUT_DIR, slug + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    articles = fetch_all_articles(BASE_URL, NUMBER_OF_ARTICLES_PER_PAGE)
    saved_count = 0
    draft_count = 0

    for article in articles:
        if article["draft"]:
            draft_count += 1
            continue
        save_article(article)
        saved_count += 1
    print(f"Saved {saved_count} articles")
    print(f"Drafts: {draft_count}")


if __name__ == "__main__":
    main()

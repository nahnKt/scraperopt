import time
import requests

BASE_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json"


def fetch_articles(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_all_articles(paramUrl, paramPerPage, paramLimit):
    articles = []
    url = paramUrl + "?per_page=" + str(paramPerPage)
    while url and len(articles) < paramLimit:
        data = fetch_articles(url)
        articles.extend(data["articles"])
        print("Da lay", len(articles), "/", data["count"])
        url = data["next_page"]
    return articles


if __name__ == "__main__":
    start_time = time.time()
    articles = fetch_all_articles(BASE_URL, 100, 10)
    end_time = time.time()
    first = articles[0]
    with open("tests/scraper/article_body.html", "w", encoding="utf-8") as f:
        f.write(first["body"])
    print("Da luu :", first["title"])

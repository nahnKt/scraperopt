import requests

BASE_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json"
NUMBER_OF_ARTICLES_PER_PAGE = 100


def fetch_articles(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_all_articles(paramUrl, paramPerPage):
    articles = []
    totalCount = 0
    url = paramUrl + "?per_page=" + str(paramPerPage)
    while url:
        data = fetch_articles(url)
        articles.extend(data["articles"])
        totalCount = data["count"]
        print("Da lay", len(articles), "/", totalCount)
        url = data["next_page"]
    return articles, totalCount


if __name__ == "__main__":
    articles, totalCount = fetch_all_articles(BASE_URL, NUMBER_OF_ARTICLES_PER_PAGE)

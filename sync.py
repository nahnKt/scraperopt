# in case of multiple files for the same article, group them by article, handle duplicates when uploading, not removing files from the vector store yet
def group_by_article(remoteFiles: list[dict]) -> dict:
    filesByArticle = {}
    for file in remoteFiles:
        articleId = file["attributes"].get("article_id")
        if articleId is None:
            continue
        if articleId not in filesByArticle:
            filesByArticle[articleId] = []
        filesByArticle[articleId].append(file)
    return filesByArticle


def decide_action(remoteFiles: list[dict], uploadHash: str, configHash: str) -> str:
    if len(remoteFiles) == 0:
        return "add"
    for oldFile in remoteFiles:
        attributes = oldFile["attributes"]
        if (
            oldFile["status"] == "completed"
            and attributes.get("upload_hash") == uploadHash
            and attributes.get("index_config_hash") == configHash
        ):
            return "skip"
    return "update"


def is_source_complete(articles: list[dict], expectedCount: int) -> bool:
    articleIds = set()
    for article in articles:
        articleIds.add(str(article["id"]))
    noDuplicates = len(articleIds) == len(articles)
    return noDuplicates and len(articleIds) == expectedCount


def plan_removals(filesByArticle: dict, sourceIds: set, isComplete: bool) -> tuple:
    missingIds = []
    for articleId in filesByArticle:
        if articleId not in sourceIds:
            missingIds.append(articleId)

    if len(missingIds) == 0:
        return [], ""
    if not isComplete:
        return [], "source fetch incomplete"

    return missingIds, ""

from datetime import datetime, timezone
import json
import os
import sys
import time

from content.article_file import content_hash, make_slug, render_article
from source.zendesk import BASE_URL, NUMBER_OF_ARTICLES_PER_PAGE, fetch_all_articles
from store.openai_store import (
    count_chunks,
    index_config_hash,
    list_files,
    remove_file,
    upload_article,
    update_file_attributes,
    update_store_metadata,
)
from sync import decide_action, group_by_article, plan_removals, is_source_complete


OUTPUT_DIR = "articles"
VECTOR_STORE_ID = os.environ["VECTOR_STORE_ID"]
ARTICLE_LIMIT = 30


def save_article(slug: str, text: str) -> None:
    path = os.path.join(OUTPUT_DIR, slug + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> int:
    startTime = time.time()
    configHash = index_config_hash()

    # group files by article on the openai vector store
    filesByArticle = group_by_article(list_files(VECTOR_STORE_ID))
    chunksByArticle = {}
    for articleId, files in filesByArticle.items():
        chunksByArticle[articleId] = int(files[0]["attributes"].get("chunk_count", 0))

    # fetch all articles from zendesk, then cut off at the ARTICLE_LIMIT
    articles, expectedCount = fetch_all_articles(BASE_URL, NUMBER_OF_ARTICLES_PER_PAGE)
    isComplete = is_source_complete(articles, expectedCount)
    articles = [article for article in articles if not article["draft"]]

    sourceIds = set()
    for article in articles:
        sourceIds.add(str(article["id"]))
    if ARTICLE_LIMIT > 0:
        articles = articles[:ARTICLE_LIMIT]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = {"added": 0, "updated": 0, "skipped": 0, "failed": 0, "chunks_uploaded": 0}

    for article in articles:
        articleId = str(article["id"])
        slug = make_slug(article["html_url"])
        text = render_article(article)
        save_article(slug, text)

        uploadHash = content_hash(text)
        oldFiles = filesByArticle.get(articleId, [])
        action = decide_action(oldFiles, uploadHash, configHash)

        if action == "skip":
            report["skipped"] += 1
            continue

        attributes = {
            "article_id": articleId,
            "upload_hash": uploadHash,
            "index_config_hash": configHash,
        }

        try:
            uploaded = upload_article(
                VECTOR_STORE_ID, "optibot-" + articleId + ".md", text, attributes
            )
        except Exception as error:
            print("FAILED", articleId, error)
            report["failed"] += 1
            continue

        if uploaded["status"] != "completed":
            print("FAILED", articleId, uploaded["status"], uploaded["error"])
            report["failed"] += 1
            continue

        chunkCount = count_chunks(VECTOR_STORE_ID, articleId, uploadHash)
        report["chunks_uploaded"] += chunkCount
        attributes["chunk_count"] = chunkCount
        chunksByArticle[articleId] = chunkCount
        update_file_attributes(VECTOR_STORE_ID, uploaded["file_id"], attributes)

        for oldFile in oldFiles:
            try:
                remove_file(VECTOR_STORE_ID, oldFile["file_id"])
            except Exception as error:
                print("WARN could not remove", oldFile["file_id"], error)

        if action == "add":
            report["added"] += 1
        else:
            report["updated"] += 1
        print(action.upper(), articleId, slug)

    removeIds, blockedReason = plan_removals(filesByArticle, sourceIds, isComplete)
    report["removed"] = 0
    for articleId in removeIds:
        for oldFile in filesByArticle[articleId]:
            remove_file(VECTOR_STORE_ID, oldFile["file_id"])
        report["removed"] += 1
        chunksByArticle.pop(articleId, None)
        print("REMOVE", articleId)
    report["removal_blocked"] = blockedReason
    report["source_complete"] = isComplete
    report["articles"] = len(articles)
    report["duration_s"] = round(time.time() - startTime)
    totalChunks = sum(chunksByArticle.values())
    report["files_in_store"] = len(chunksByArticle)
    report["chunks_in_store"] = totalChunks

    update_store_metadata(
        VECTOR_STORE_ID,
        {
            "total_chunks": str(totalChunks),
            "last_run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "last_run_added": str(report["added"]),
            "last_run_updated": str(report["updated"]),
            "last_run_removed": str(report["removed"]),
        },
    )
    print(json.dumps(report))

    if report["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

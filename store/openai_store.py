import os
import hashlib
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()

CHUNKING = {
    "type": "static",
    "static": {"max_chunk_size_tokens": 600, "chunk_overlap_tokens": 200},
}


def create_vector_store(name: str) -> str:
    vectorStore = client.vector_stores.create(name=name)
    return vectorStore.id


def upload_article(
    vectorStoreId: str, fileName: str, text: str, attributes: dict
) -> dict:
    vectorFile = client.vector_stores.files.upload_and_poll(
        vector_store_id=vectorStoreId,
        file=(fileName, text.encode("utf-8")),
        attributes=attributes,
        chunking_strategy=CHUNKING,
        max_wait_seconds=300,
    )
    return {
        "file_id": vectorFile.id,
        "status": vectorFile.status,
        "error": str(vectorFile.last_error) if vectorFile.last_error else "",
    }


# remove a file from the vector store
def remove_file(vectorStoreId: str, fileId: str) -> None:
    client.vector_stores.files.delete(fileId, vector_store_id=vectorStoreId)
    client.files.delete(fileId)


def count_chunks(vectorStoreId: str, articleId: str, uploadHash: str) -> int:
    results = client.vector_stores.search(
        vectorStoreId,
        query="article",
        filters={
            "type": "and",
            "filters": [
                {"type": "eq", "key": "article_id", "value": articleId},
                {"type": "eq", "key": "upload_hash", "value": uploadHash},
            ],
        },
        max_num_results=50,
        ranking_options={"score_threshold": 0.0},
    )
    chunkCount = 0
    for result in results:
        chunkCount += len(result.content)
    return chunkCount


# calculate the hash of the index configuration
def index_config_hash() -> str:
    configText = json.dumps(CHUNKING, sort_keys=True)
    return hashlib.sha256(configText.encode("utf-8")).hexdigest()


# list all files in the vector store
def list_files(vectorStoreId: str) -> list[dict]:
    files = []
    for vectorFile in client.vector_stores.files.list(vectorStoreId, limit=100):
        files.append(
            {
                "file_id": vectorFile.id,
                "status": vectorFile.status,
                "created_at": vectorFile.created_at,
                "attributes": vectorFile.attributes or {},
            }
        )
    return files


def update_file_attributes(vectorStoreId: str, fileId: str, attributes: dict) -> None:
    client.vector_stores.files.update(
        fileId, vector_store_id=vectorStoreId, attributes=attributes
    )


def update_store_metadata(vectorStoreId: str, metadata: dict) -> None:
    client.vector_stores.update(vectorStoreId, metadata=metadata)


if __name__ == "__main__":
    vectorStoreId = os.getenv("VECTOR_STORE_ID", "")
    if vectorStoreId == "":
        newId = create_vector_store("optibot-docs")
        print("Created vector store:", newId)
        print("Copy this id into .env as VECTOR_STORE_ID.")
    else:
        print("Files in store:", len(list_files(vectorStoreId)))

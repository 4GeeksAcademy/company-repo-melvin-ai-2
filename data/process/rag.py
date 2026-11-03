"""Chunk Brasaland manuals and turn one text into an embedding.

`embed` calls the embeddings model only. The generation model lives in
`data.pipelines.rag` and must be a different model id.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

COLLECTION = "brasaland_knowledge"
COMPANY = "brasaland"
LANGUAGE = "en"
ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "docs" / "company-knowledge-base"

SOURCE_SLUGS = {
    "brasaland-loyalty-program.en.md": "loyalty-program",
    "brasaland-waste-protocol.en.md": "waste-protocol",
    "brasaland-menu-allergens.en.md": "menu-allergens",
    "brasaland-supplier-ordering.en.md": "supplier-ordering",
}

_HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
_LABEL = re.compile(r"^[A-Z][^:\n]{0,80}:\s*$")
_NAMESPACE = uuid.UUID("6b1f5a2e-7c4d-4e1a-9b3f-8a0d6c2e4f17")


class ModelSettings:
    def __init__(self, base_url: str, api_key: str, embedding_model: str, generation_model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.generation_model = generation_model


def model_settings() -> ModelSettings:
    """Read the two 4Geeks model ids. They are not allowed to be the same model."""
    embedding_model = os.environ.get("RAG_EMBEDDING_MODEL", "").strip()
    generation_model = os.environ.get("RAG_GENERATION_MODEL", "").strip()
    base_url = os.environ.get("RAG_BASE_URL", "").strip()
    api_key = os.environ.get("RAG_API_KEY", "").strip()
    if not embedding_model or not generation_model or not base_url or not api_key:
        raise RuntimeError(
            "Set RAG_BASE_URL, RAG_API_KEY, RAG_EMBEDDING_MODEL, and RAG_GENERATION_MODEL "
            "from the 4Geeks student LLM access."
        )
    if embedding_model == generation_model:
        raise RuntimeError("The embedding model and the generation model must be different ids.")
    return ModelSettings(base_url, api_key, embedding_model, generation_model)


def embed(text: str) -> list[float]:
    """Vector for one chunk or one question. This never calls the generation model."""
    settings = model_settings()
    payload = _post_json(
        f"{settings.base_url}/embeddings",
        settings.api_key,
        {"model": settings.embedding_model, "input": text},
    )
    vector = payload["data"][0]["embedding"]
    if not isinstance(vector, list) or not vector:
        raise RuntimeError("The embeddings model returned an empty vector.")
    return [float(value) for value in vector]


def load_chunks(folder: Path | None = None) -> list[dict]:
    """Read the four manuals and split them on section boundaries."""
    directory = folder or KNOWLEDGE_DIR
    chunks: list[dict] = []
    for filename, source in SOURCE_SLUGS.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing knowledge document: {path}")
        index = -1
        for index, (section, text) in enumerate(semantic_chunks(path.read_text(encoding="utf-8"))):
            chunks.append(
                {
                    "id": chunk_id(source, index),
                    "company": COMPANY,
                    "source_document": source,
                    "section": section,
                    "language": LANGUAGE,
                    "chunk_index": index,
                    "text": text,
                }
            )
        if index < 2:
            raise ValueError(f"{filename} produced fewer than 3 chunks.")
    return chunks


def semantic_chunks(markdown: str) -> list[tuple[str, str]]:
    """Split a manual into self-contained sections. A sentence is never cut in half."""
    section = "Introduction"
    lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []

    def flush() -> None:
        if any(line.strip() for line in lines):
            sections.append((section, list(lines)))
        lines.clear()

    for raw in markdown.splitlines():
        heading = _HEADING.match(raw.strip())
        if heading:
            flush()
            section = heading.group(1).strip().strip('"')
            continue
        if _LABEL.match(raw.strip()) and lines:
            flush()
            section = raw.strip().rstrip(":")
        lines.append(raw)
    flush()

    chunks: list[tuple[str, str]] = []
    for title, block in sections:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", "\n".join(block)) if part.strip()]
        for paragraph in paragraphs:
            body = paragraph if paragraph.lower().startswith(title.lower()) else f"{title}\n{paragraph}"
            chunks.append((title, body.strip()))
    return chunks


def chunk_id(source_document: str, chunk_index: int) -> str:
    """Stable id so indexing the same manuals again replaces the same points."""
    return str(uuid.uuid5(_NAMESPACE, f"{COMPANY}:{source_document}:{chunk_index}"))


def setup(folder: Path | None = None, client=None) -> int:
    """Create `brasaland_knowledge` again and upsert every chunk. Safe to run twice."""
    chunks = load_chunks(folder)
    vectors = [embed(chunk["text"]) for chunk in chunks]
    qdrant = client or connect_qdrant()
    _replace_collection(qdrant, len(vectors[0]))
    from qdrant_client.models import PointStruct

    qdrant.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(id=chunk["id"], vector=vector, payload=_payload(chunk))
            for chunk, vector in zip(chunks, vectors)
        ],
    )
    return len(chunks)


def connect_qdrant():
    from qdrant_client import QdrantClient

    return QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))


def _replace_collection(client, dimension: int) -> None:
    from qdrant_client.models import Distance, VectorParams

    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )


def _payload(chunk: dict) -> dict:
    return {
        "company": chunk["company"],
        "source_document": chunk["source_document"],
        "section": chunk["section"],
        "language": chunk["language"],
        "chunk_index": chunk["chunk_index"],
        "text": chunk["text"],
    }


def _post_json(url: str, api_key: str, body: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code == 429 and attempt < 3:
                time.sleep(_retry_wait_seconds(detail))
                continue
            raise RuntimeError(f"The model request failed ({exc.code}). {detail}") from exc
    raise RuntimeError("The model request failed after repeated rate limits.")


def _retry_wait_seconds(detail: str) -> float:
    """Wait until the gateway's reset time, then try the same request again."""
    marker = "Limit resets at: "
    start = detail.find(marker)
    if start < 0:
        return 65
    stamp = detail[start + len(marker) :].split('"', 1)[0].strip()
    try:
        reset = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
    except ValueError:
        return 65
    return max(1.0, min((reset - datetime.now(timezone.utc)).total_seconds() + 1, 120))

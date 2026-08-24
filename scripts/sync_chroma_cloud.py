#!/usr/bin/env python3
"""Idempotently sync all public Markdown pages into INV Chroma Cloud.

Credentials are loaded from INV_CHROMA_API_KEY, INV_CHROMA_TENANT, and
INV_CHROMA_DATABASE in the environment or ~/.hermes/.env. No credential is
printed or written to a receipt.
"""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, os, re, sys
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "site" / "pages"
COLLECTION = "inv_public_site_pages"
CORPUS = "idea-nexus-public"
MAX_CHARS = 12000


def load_env_file():
    path = Path.home() / ".hermes" / ".env"
    values = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("INV_CHROMA_API_KEY", "INV_CHROMA_TENANT", "INV_CHROMA_DATABASE"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    missing = [key for key in ("INV_CHROMA_API_KEY", "INV_CHROMA_TENANT", "INV_CHROMA_DATABASE") if not values.get(key)]
    if missing:
        raise SystemExit("Missing required Chroma credentials: " + ", ".join(missing))
    return values


def parse_frontmatter(text):
    meta = {}
    body = text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')
    return meta, body.strip()


def chunk(text):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if current and len(candidate) > MAX_CHARS:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text[:MAX_CHARS]]


def page_records():
    records = []
    for path in sorted(PAGES.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text())
        slug = meta.get("slug", path.stem)
        title = meta.get("title", path.stem.replace("-", " ").title())
        route = "/" if slug == "index" else f"/{slug}/"
        digest = hashlib.sha256(body.encode()).hexdigest()[:16]
        for index, text in enumerate(chunk(body)):
            record_id = "page__" + re.sub(r"[^a-zA-Z0-9_-]", "_", slug) + f"__{index}"
            document = f"Title: {title}\nRoute: {route}\n\n{text}"
            records.append({
                "id": record_id,
                "document": document,
                "metadata": {
                    "corpus": CORPUS,
                    "page_slug": slug,
                    "route": route,
                    "title": title,
                    "kind": meta.get("kind", "page"),
                    "chunk_index": index,
                    "content_hash": digest,
                },
            })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="how do you measure human capability?")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    credentials = load_env_file()
    records = page_records()
    print(f"Prepared {len(records)} page chunks from {len(list(PAGES.glob('*.md')))} Markdown pages.")
    client = chromadb.CloudClient(api_key=credentials["INV_CHROMA_API_KEY"], tenant=credentials["INV_CHROMA_TENANT"], database=credentials["INV_CHROMA_DATABASE"])
    if args.check_only:
        collections = client.list_collections()
        print(json.dumps({"cloud_connection": "ok", "collection_count": len(collections)}, indent=2))
        return
    collection = client.get_or_create_collection(COLLECTION, metadata={"corpus": CORPUS, "embedding_provider": "chroma_default_onnx"})
    ef = DefaultEmbeddingFunction()
    ids = [r["id"] for r in records]
    documents = [r["document"] for r in records]
    embeddings = ef(documents)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=[r["metadata"] for r in records])
    existing = collection.get(where={"corpus": CORPUS}, limit=300, include=["metadatas"])
    existing_ids = set(existing.get("ids", []))
    stale = sorted(existing_ids - set(ids))
    if stale:
        collection.delete(ids=stale)
    query_embedding = ef([args.query])
    result = collection.query(query_embeddings=query_embedding, n_results=min(5, len(records)), include=["documents", "metadatas", "distances"])
    top = []
    for metadata, distance in zip(result["metadatas"][0], result["distances"][0]):
        top.append({"route": metadata["route"], "title": metadata["title"], "distance": round(float(distance), 6)})
    print(json.dumps({"cloud_connection": "ok", "collection": COLLECTION, "upserted": len(records), "stale_deleted": len(stale), "count": collection.count(), "query": args.query, "top_results": top}, indent=2))


if __name__ == "__main__":
    main()

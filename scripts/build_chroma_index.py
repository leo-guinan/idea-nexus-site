#!/usr/bin/env python3
"""Build and query Marvin's local Chroma retrieval index.

The index is intentionally local-first and ignored by Git. It is a retrieval
substrate for authoring/tests until a server-side query boundary is deployed.
"""
from pathlib import Path
import json, shutil
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / ".local" / "chroma"
COLLECTION = "marvin_public_knowledge"


def load_documents():
    data = json.loads((ROOT / "site/marvin.json").read_text())
    docs, metas, ids = [], [], []
    for entry in data["entries"]:
        docs.append(f"{entry['answer']} Source: {entry['label']} {entry['source']}")
        metas.append({"source": entry["source"], "label": entry["label"], "kind": "marvin-entry"})
        ids.append(f"entry-{entry['id']}")
    humanpower = (ROOT / "site/pages/humanpower.md").read_text()
    docs.append(humanpower)
    metas.append({"source": "/humanpower/", "label": "Humanpower", "kind": "page"})
    ids.append("page-humanpower")
    return docs, metas, ids


def main():
    INDEX.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(INDEX))
    ef = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        COLLECTION,
        embedding_function=ef,
        metadata={"purpose": "Idea Nexus public Marvin guide", "version": 1},
    )
    docs, metas, ids = load_documents()
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    question = "how do you measure human capability?"
    result = collection.query(query_texts=[question], n_results=3)
    rows = []
    for doc, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        rows.append({"label": meta["label"], "source": meta["source"], "distance": round(float(distance), 6), "preview": doc[:180]})
    receipt = {"collection": COLLECTION, "path": str(INDEX), "count": collection.count(), "query": question, "top_results": rows}
    (ROOT / "agents/marvin-chroma-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

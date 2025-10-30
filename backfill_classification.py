#!/usr/bin/env python3
"""
Backfill classification for recent documents missing classification fields.
Fetches recent docs from Elasticsearch, calls PV Classification batch endpoint,
and writes normalized fields expected by the UI.
"""

import sys
import json
from datetime import datetime, timezone
import requests

ES = "http://localhost:9200"
PV = "http://localhost:8012"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_unclassified(limit: int = 25):
    query = {
        "size": limit,
        "sort": [{"created_at": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [{"match_all": {}}],
                "must_not": {"exists": {"field": "classification"}},
            }
        },
        "_source": [
            "title",
            "abstract",
            "content",
            "metadata.mesh_terms",
            "metadata.publication_types",
        ],
    }
    r = requests.post(f"{ES}/documents/_search", json=query, timeout=30)
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    docs = []
    for h in hits:
        _id = h.get("_id")
        src = h.get("_source", {})
        title = src.get("title") or ""
        abstract = src.get("abstract") or src.get("content") or ""
        mesh = (src.get("metadata") or {}).get("mesh_terms") or []
        pub_types = (src.get("metadata") or {}).get("publication_types") or []
        if not title and not abstract:
            continue
        docs.append({
            "id": _id,
            "title": title,
            "abstract": abstract,
            "mesh_terms": mesh,
            "publication_types": pub_types,
        })
    return docs


def classify_batch(docs):
    if not docs:
        return []
    payload = {"documents": docs}
    r = requests.post(f"{PV}/api/v1/classify/ensemble/batch", json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])


def update_es(doc_id: str, cls_result: dict):
    cls_block = cls_result.get("classification", {})
    meta = cls_result.get("ensemble_metadata", {})
    update = {
        "doc": {
            "classification": cls_block.get("classification"),
            "classification_confidence": cls_block.get("confidence", 0.0),
            "classification_reasoning": cls_block.get("reasoning", ""),
            "classification_entities": cls_block.get("key_entities", []),
            "regulatory_elements": cls_block.get("regulatory_elements", {}),
            "ensemble_models_used": meta.get("models_used", []),
            "processing_time_ms": meta.get("processing_time_ms", 0),
            "classification_cost": meta.get("cost_estimate", 0.0),
            "processing_status": "classified",
            "ai_processed": True,
            "classified_at": iso_now(),
            "updated_at": iso_now(),
        }
    }
    r = requests.post(f"{ES}/documents/_update/{doc_id}", json=update, timeout=30)
    r.raise_for_status()


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    docs = fetch_unclassified(limit)
    print(f"Found {len(docs)} unclassified docs")
    if not docs:
        return
    results = classify_batch(docs)
    # Map results by document_id
    by_id = {r.get("document_id"): r for r in results}
    updated = 0
    for d in docs:
        rid = d["id"]
        if rid in by_id:
            try:
                update_es(rid, by_id[rid])
                updated += 1
            except Exception as e:
                print(f"Failed to update {rid}: {e}")
    print(f"Updated {updated}/{len(docs)} documents")


if __name__ == "__main__":
    main()



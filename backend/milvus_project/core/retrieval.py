"""Helpers for searching and normalizing Milvus knowledge results."""

from __future__ import annotations

from typing import Any

from milvus_project.core.milvus_client import KNOWLEDGE_COLLECTION, milvus_client


DEFAULT_OUTPUT_FIELDS = ["id", "content", "data_type", "source", "metadata"]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def display_score(value: Any) -> float:
    score = safe_float(value)
    return max(0.0, min(score, 1.0))


def normalize_hit(hit: Any, rank: int) -> dict[str, Any]:
    if isinstance(hit, dict):
        entity = hit.get("entity") or {}
        hit_id = hit.get("id") or entity.get("id")
        raw_score = hit.get("score", hit.get("distance"))
    else:
        entity = getattr(hit, "entity", {}) or {}
        hit_id = getattr(hit, "id", None) or entity.get("id")
        raw_score = getattr(hit, "score", None)
        if raw_score is None:
            raw_score = getattr(hit, "distance", None)

    doc = dict(entity)
    if hit_id is not None:
        doc["id"] = hit_id

    retrieval_score = safe_float(raw_score)
    doc["rank"] = rank
    doc["retrieval_score"] = retrieval_score
    doc["score"] = display_score(retrieval_score)
    doc.setdefault("metadata", {})
    return doc


def normalize_search_results(search_res: Any) -> list[dict[str, Any]]:
    if not search_res or not search_res[0]:
        return []
    return [normalize_hit(hit, rank=index + 1) for index, hit in enumerate(search_res[0])]


def search_knowledge_by_vector(
    query_vector: list[float],
    *,
    limit: int = 10,
    output_fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    search_res = milvus_client.search(
        collection_name=KNOWLEDGE_COLLECTION,
        data=[query_vector],
        anns_field="dense_vector",
        limit=limit,
        output_fields=output_fields or DEFAULT_OUTPUT_FIELDS,
    )
    return normalize_search_results(search_res)

"""Format retrieved knowledge into frontend reference groups."""

from __future__ import annotations

import re
from typing import Any

from milvus_project.core.retrieval import display_score, safe_float


def image_url_from_doc(doc: dict[str, Any]) -> str:
    metadata = doc.get("metadata") or {}
    if isinstance(metadata, dict):
        return metadata.get("image_url") or metadata.get("thumbnail") or ""
    return ""


def title_from_content(content: str) -> str:
    if not content:
        return "草药图片"

    patterns = [
        r"药材名称[:：]\s*([^\n，,。；;]+)",
        r"中药名称[:：]\s*([^\n，,。；;]+)",
        r"名称[:：]\s*([^\n，,。；;]+)",
        r"证型名称[:：]\s*([^\n，,。；;]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()

    first_line = content.splitlines()[0].strip()
    return first_line[:18] if first_line else "草药图片"


def field_from_content(content: str, labels: list[str]) -> str:
    for label in labels:
        match = re.search(rf"{label}[:：]\s*([^\n]+)", content or "")
        if match:
            return match.group(1).strip()
    return ""


def image_result_from_doc(doc: dict[str, Any]) -> dict[str, Any]:
    content = doc.get("content") or ""
    score = display_score(doc.get("score", doc.get("retrieval_score")))
    image_url = image_url_from_doc(doc)

    return {
        "id": doc.get("id"),
        "name": title_from_content(content),
        "content": content,
        "source": doc.get("source") or "未知来源",
        "image_url": image_url,
        "thumbnail": image_url,
        "score": score,
        "retrieval_score": safe_float(doc.get("retrieval_score", score)),
        "rerank_score": doc.get("rerank_score"),
        "rerank_status": doc.get("rerank_status"),
        "properties": field_from_content(content, ["性味归经", "性味", "四气五味"]),
        "meridian": field_from_content(content, ["归经"]),
        "effect": field_from_content(content, ["功效", "功能主治", "主治"]),
        "visual_features": field_from_content(content, ["图像特征", "外观特征", "鉴别特征"]),
        "metadata": doc.get("metadata") or {},
    }


def split_reference_docs(docs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text_chunks: list[dict[str, Any]] = []
    image_results: list[dict[str, Any]] = []

    for doc in docs:
        if image_url_from_doc(doc) or doc.get("data_type") == "image":
            image_results.append(image_result_from_doc(doc))
        else:
            text_chunks.append(doc)

    return text_chunks, image_results

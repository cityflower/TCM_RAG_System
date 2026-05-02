import os
import logging
from typing import Any

import torch
from src.models.qwen3_vl_reranker import Qwen3VLReranker
from milvus_project.core.retrieval import display_score, safe_float

MODEL_ID = "./models/Qwen3-VL-Reranker-2B"
logger = logging.getLogger(__name__)
RERANK_DOCUMENT_IMAGES = os.getenv("TCM_RERANK_DOCUMENT_IMAGES", "0") == "1"

_model: Qwen3VLReranker | None = None


def get_reranker() -> Qwen3VLReranker:
    global _model
    if _model is None:
        logger.info("Loading Qwen3-VL reranker from %s", MODEL_ID)
        _model = Qwen3VLReranker(
            model_name_or_path=MODEL_ID,
            device_map="mps",
            torch_dtype=torch.bfloat16,
        )
    return _model


def _doc_image_url(doc: dict[str, Any]) -> str:
    metadata = doc.get("metadata") or {}
    if isinstance(metadata, dict):
        return metadata.get("image_url") or ""
    return ""


def _fallback_results(
    retrieved_docs: list[dict[str, Any]],
    top_k: int,
    reason: str,
    status: str = "fallback",
) -> list[dict[str, Any]]:
    logger.warning("Rerank fallback: %s", reason)
    docs = []
    for doc in retrieved_docs:
        item = dict(doc)
        retrieval_score = safe_float(item.get("retrieval_score", item.get("score")))
        item["rerank_score"] = None
        item["score"] = display_score(retrieval_score)
        item["rerank_status"] = status
        if status == "fallback":
            item["rerank_error"] = reason
        docs.append(item)
    docs.sort(key=lambda x: safe_float(x.get("retrieval_score", x.get("score"))), reverse=True)
    return docs[:top_k]


def rerank_results(
    query_text: str,
    query_image_path: str | None,
    retrieved_docs: list[dict[str, Any]],
    top_k: int = 3,
    enable_rerank: bool = True,
) -> list[dict[str, Any]]:
    """Rerank Milvus hits and expose a frontend-friendly score field."""
    if not retrieved_docs:
        return []

    if not enable_rerank:
        return _fallback_results(retrieved_docs, top_k, "rerank disabled", status="disabled")

    try:
        model = get_reranker()
    except Exception as exc:
        return _fallback_results(retrieved_docs, top_k, f"model load failed: {exc}")

    query_dict = {"text": query_text if query_text else "请帮我看看这个。"}
    if query_image_path and os.path.exists(query_image_path):
        query_dict["image"] = query_image_path

    reranked_docs = []
    for doc in retrieved_docs:
        item = dict(doc)
        doc_content = item.get("content") or ""
        image_url = _doc_image_url(item)

        doc_input = {"text": doc_content if doc_content else "图片资料"}
        # 候选文档图片已经在 Milvus 多模态召回阶段参与了相似度计算。
        # 部分 webp/本地 MinIO 图片继续传入 reranker 会触发模型侧张量索引错误，
        # 因此默认只用文档文字描述重排；需要实验时可设置环境变量打开。
        if image_url and RERANK_DOCUMENT_IMAGES:
            doc_input["image"] = image_url

        inputs = {
            "query": query_dict,
            "documents": [doc_input],
        }

        try:
            scores = model.process(inputs)
            rerank_score = scores[0].item() if hasattr(scores[0], "item") else scores[0]
            rerank_score = safe_float(rerank_score)
            item["rerank_score"] = rerank_score
            item["score"] = display_score(rerank_score)
            item["rerank_status"] = "ok"
        except Exception as exc:
            retrieval_score = safe_float(item.get("retrieval_score", item.get("score")))
            item["rerank_score"] = None
            item["score"] = display_score(retrieval_score)
            item["rerank_status"] = "fallback"
            item["rerank_error"] = str(exc)
            logger.warning("Rerank failed for source=%s: %s", item.get("source"), exc)
        reranked_docs.append(item)

    reranked_docs.sort(
        key=lambda x: (
            safe_float(x.get("rerank_score"), -1.0)
            if x.get("rerank_score") is not None
            else safe_float(x.get("retrieval_score", x.get("score")))
        ),
        reverse=True,
    )
    return reranked_docs[:top_k]

# ==========================================
# 🧪 随堂小测试 保持原样即可
# ==========================================

# ==========================================
# 🧪 随堂小测试
# ==========================================
if __name__ == "__main__":
    print("\n✅ 裁判就位！来做个小测试：")
    
    test_query = "人参有什么功效？"
    mock_retrieved_docs = [
        {"id": 1, "data_type": "text", "content": "枸杞子，味甘性平，主滋肾润肺。"}, 
        {"id": 2, "data_type": "text", "content": "人参，味甘微寒。主补五脏，安精神，定魂魄。"}, 
        {"id": 3, "data_type": "text", "content": "今天天气真不错，适合去爬山挖草药。"}
    ]
    
    print(f"用户提问: {test_query}")
    print("粗筛结果共 3 条，正在请求裁判重新打分筛选...")
    
    best_results = rerank_results(query_text=test_query, query_image_path=None, retrieved_docs=mock_retrieved_docs, top_k=1)
    
    print("\n🏆 裁判最终选出的最优解：")
    for res in best_results:
        print(f"得分: {res.get('score', 0):.4f} | 内容: {res.get('content')}")

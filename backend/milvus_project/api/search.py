from fastapi import APIRouter, Query

from milvus_project.core.embedding import get_multimodal_embedding
from milvus_project.core.retrieval import search_knowledge_by_vector
from milvus_project.core.rerank import rerank_results

router = APIRouter()


@router.get("/search")
async def debug_search(
    query: str = Query(..., min_length=1, description="要检索的症状、证型或中医问题"),
    limit: int = Query(5, ge=1, le=20, description="返回结果数量"),
    recall_limit: int = Query(10, ge=1, le=50, description="Milvus 初筛数量"),
    rerank: bool = Query(True, description="是否启用 Qwen3-VL reranker 重排"),
):
    """检索调试接口：只返回 Top-K 资料，不调用大模型生成回答。"""
    recall_limit = max(recall_limit, limit)
    query_vector = get_multimodal_embedding(text=query)
    retrieved_docs = search_knowledge_by_vector(query_vector, limit=recall_limit)
    results = rerank_results(
        query_text=query,
        query_image_path=None,
        retrieved_docs=retrieved_docs,
        top_k=limit,
        enable_rerank=rerank,
    )
    return {
        "query": query,
        "limit": limit,
        "recall_limit": recall_limit,
        "rerank": rerank,
        "total_recalled": len(retrieved_docs),
        "results": results,
    }

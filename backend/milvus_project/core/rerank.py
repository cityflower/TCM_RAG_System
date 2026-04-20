# backend/milvus_project/core/rerank.py
import os
import torch
from src.models.qwen3_vl_reranker import Qwen3VLReranker

MODEL_ID = "./models/Qwen3-VL-Reranker-2B"

print("⚖️ 正在通过阿里官方专属通道加载 Qwen3-VL 多模态重排裁判...")
model = Qwen3VLReranker(
    model_name_or_path=MODEL_ID,
    device_map="mps",
    torch_dtype=torch.bfloat16      # 👈 开启半精度加速
)

def rerank_results(query_text: str, query_image_path: str, retrieved_docs: list, top_k: int = 3) -> list:
    """终极多模态重排裁判 (提取云相册 + 逐条防崩版)"""
    if not retrieved_docs:
        return []

    # 1. 组装提问 (哪怕只发图片，也给它垫一句话防报错)
    query_dict = {"text": query_text if query_text else "请帮我看看这个。"}
    if query_image_path and os.path.exists(query_image_path):
        query_dict["image"] = query_image_path

    # 2. 逐一打分！(彻底破解底层批量处理图文的 Bug)
    for doc in retrieved_docs:
        doc_content = doc.get('content', '')
        # 🌟 关键：把存进去的 MinIO 链接给挖出来！
        metadata = doc.get('metadata', {})
        image_url = metadata.get('image_url', '')

        # 组装这篇古籍的专属格式
        doc_input = {"text": doc_content if doc_content else "图片资料"}
        if image_url:
            # 官方大模型非常聪明，直接喂给它 MinIO 的网址它也能看懂！
            doc_input["image"] = image_url  

        # 每次只传 1 篇进去，大模型绝不崩溃！
        inputs = {
            "query": query_dict,
            "documents": [doc_input]
        }

        try:
            scores = model.process(inputs)
            doc['rerank_score'] = scores[0].item() if hasattr(scores[0], 'item') else scores[0]
        except Exception as e:
            print(f"⚠️ 裁判打分异常: {e}")
            doc['rerank_score'] = -999.0

    # 3. 按得分从高到低排序，截取前 top_k
    retrieved_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
    return retrieved_docs[:top_k]

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
        print(f"得分: {res.get('rerank_score', 0):.4f} | 内容: {res.get('content')}")
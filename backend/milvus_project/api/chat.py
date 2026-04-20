# backend/api/chat.py
import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

# 把咱们前面练成绝世武功的四大天王全都请出来
from milvus_project.core.embedding import get_multimodal_embedding
from milvus_project.core.milvus_client import milvus_client, KNOWLEDGE_COLLECTION
from milvus_project.core.rerank import rerank_results
from milvus_project.core.llm import generate_rag_response_stream
from milvus_project.core.minio_client import upload_image_to_minio

router = APIRouter()

# 建一个临时文件夹，用来给模型飞速读取图片用
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/chat")
async def chat_with_tcm(
    query: str = Form(...), 
    image: UploadFile = File(None)
):
    """
    终极图文问诊接口！
    前端传文字和图片过来，我们返回老中医的流式解答。
    """
    local_img_path = None
    minio_img_url = None

    # ==========================================
    # 步骤 1：处理上传的图片 (存本地缓存 + 上传 MinIO)
    # ==========================================
    if image:
        # 给图片起个不重复的名字
        ext = image.filename.split('.')[-1]
        unique_filename = f"img_{uuid.uuid4().hex[:8]}.{ext}"
        local_img_path = os.path.join(TEMP_DIR, unique_filename)
        
        # 1. 存到本地临时文件夹 (为了给 Qwen-VL 极速读取)
        with open(local_img_path, "wb") as f:
            f.write(await image.read())
            
        # 2. 扔给 MinIO 云相册 (为了给前端展示和存入数据库备用)
        minio_img_url = upload_image_to_minio(local_img_path, unique_filename)
        print(f"📸 收到图片，已备份至 MinIO: {minio_img_url}")

    # ==========================================
    # 步骤 2：翻译官上阵 (提取 2048 维向量)
    # ==========================================
    print("🧠 翻译官正在提取特征...")
    # 💡 无论有没有图，调用这同一个函数就搞定了！
    query_vector = get_multimodal_embedding(text=query, image_path=local_img_path)

    # ==========================================
    # 步骤 3：Milvus 大库捞针 (粗筛)
    # ==========================================
    print("🗄️ 正在知识库中进行初步匹配...")
    search_res = milvus_client.search(
        collection_name=KNOWLEDGE_COLLECTION,
        data=[query_vector],
        anns_field="dense_vector",
        limit=10, # 先捞 10 条出来
        output_fields=["content", "data_type", "source", "metadata"]
    )
    
    # 把捞出来的结果整理成一个干净的字典列表
    retrieved_docs = []
    if search_res and len(search_res[0]) > 0:
        retrieved_docs = [hit['entity'] for hit in search_res[0]]

    # ==========================================
    # 步骤 4：铁面裁判重排 (精筛)
    # ==========================================
    print("⚖️ 裁判正在进行严苛打分...")
    # 把图文和捞出来的 10 条古籍交给裁判，只留最精华的 3 条！
    best_docs = rerank_results(
        query_text=query, 
        query_image_path=local_img_path, 
        retrieved_docs=retrieved_docs, 
        top_k=3
    )

    # ==========================================
    # 步骤 5：老中医接诊 (流式输出给前端)
    # ==========================================
    print("🤖 老中医开始流式解答...")
    image_info = f"MinIO云端图片 ({minio_img_url})" if minio_img_url else None
    
    # 包装成生成器，FastAPI 才能一段一段地发给前端
    def stream_generator():
        # 发送参考资料给前端（溯源数据）
        refs_data = {
            "type": "references",
            "content": {"text_chunks": best_docs}
        }
        yield f"data: {json.dumps(refs_data, ensure_ascii=False)}\n\n"
        
        for chunk in generate_rag_response_stream(query, best_docs, image_info):
            # 将普通文本打包成前端规定的 JSON 格式
            chunk_data = {
                "type": "text",
                "content": chunk
            }
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            
        # 补上结束信号
        yield "data: [DONE]\n\n"

    # 返回 Server-Sent Events 流式响应！
    return StreamingResponse(stream_generator(), media_type="text/event-stream")
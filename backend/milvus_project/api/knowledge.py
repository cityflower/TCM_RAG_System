# backend/milvus_project/api/knowledge.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form

# 依然是叫醒咱们的四大天王
from milvus_project.core.embedding import get_multimodal_embedding
from milvus_project.core.milvus_client import milvus_client, KNOWLEDGE_COLLECTION
from milvus_project.core.minio_client import upload_image_to_minio

router = APIRouter()

# 临时文件夹
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/upload_knowledge")
async def insert_knowledge(
    content: str = Form(..., description="古籍里的文字，或者对这味药的详细描述"),
    source: str = Form("未知古籍", description="出处，比如《本草纲目》或 某某医生录入"),
    image: UploadFile = File(None, description="可选：如果这味药有清晰的照片，就传上来")
):
    """
    📚 知识库录入接口：
    把文字和图片翻译成 2048 维向量，然后极其优雅地存入 Milvus 藏书阁！
    """
    minio_img_url = ""
    local_img_path = None
    data_type = "text"

    # ==========================================
    # 步骤 1：如果有图片，依然交给 MinIO 云相册托管
    # ==========================================
    if image:
        ext = image.filename.split('.')[-1]
        unique_filename = f"knowledge_{uuid.uuid4().hex[:8]}.{ext}"
        local_img_path = os.path.join(TEMP_DIR, unique_filename)

        # 存本地临时文件
        with open(local_img_path, "wb") as f:
            f.write(await image.read())

        # 传给 MinIO
        minio_img_url = upload_image_to_minio(local_img_path, unique_filename)
        data_type = "image"  # 标记这条知识是带图的
        print(f"📸 知识库收到高清图片，已归档至 MinIO: {minio_img_url}")

    # ==========================================
    # 步骤 2：翻译官提取 2048 维向量
    # ==========================================
    print("🧠 翻译官正在为新知识提取特征...")
    vector = get_multimodal_embedding(text=content, image_path=local_img_path)

    # ==========================================
    # 步骤 3：准备打包存入 Milvus
    # ==========================================
    # 💡 注意：这里咱们不需要手动算 sparse_vector(BM25)，因为咱们建表的时候配置了自动生成！
    insert_data = {
        "data_type": data_type,
        "content": content,
        "source": source,
        "dense_vector": vector,
        "metadata": {"image_url": minio_img_url} if minio_img_url else {}
    }

    # ==========================================
    # 步骤 4：落锤！存入大库！
    # ==========================================
    print("🗄️ 正在刻录进 2048 维藏书阁...")
    res = milvus_client.insert(
        collection_name=KNOWLEDGE_COLLECTION,
        data=[insert_data]
    )

    # 兼容不同版本 Milvus 的返回格式，超级安全取 ID 法
    inserted_ids = res.get("ids", []) if isinstance(res, dict) else getattr(res, 'primary_keys', [])
    safe_id = inserted_ids[0] if inserted_ids else "未知ID"

    return {
        "message": "✅ 知识录入成功！大模型的脑容量又增加了！",
        "insert_id": safe_id,
        "image_url": minio_img_url if minio_img_url else "上传失败，请检查 MinIO 状态"
    }


# ==========================================
# 📋 知识库分页查询接口
# ==========================================
@router.get("/knowledge_list")
async def list_knowledge(page: int = 1, page_size: int = 20):
    """
    📋 分页查询知识库内容
    返回 total (总数) 和 data (当前页数据)，不返回高维向量字段以节省带宽
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询总数（用 count 表达式）
        count_result = milvus_client.query(
            collection_name=KNOWLEDGE_COLLECTION,
            filter="",
            output_fields=["count(*)"],
        )
        total = count_result[0].get("count(*)", 0) if count_result else 0

        # 分页查询数据（不返回向量字段）
        results = milvus_client.query(
            collection_name=KNOWLEDGE_COLLECTION,
            filter="",
            output_fields=["id", "content", "source", "data_type", "metadata"],
            limit=page_size,
            offset=offset,
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": results
        }
    except Exception as e:
        return {"error": f"查询失败: {str(e)}", "total": 0, "data": []}


# ==========================================
# 🗑️ 知识库删除接口
# ==========================================
@router.delete("/knowledge/{item_id}")
async def delete_knowledge(item_id: str):
    """
    🗑️ 根据主键 ID 删除一条知识记录
    """
    try:
        milvus_client.delete(
            collection_name=KNOWLEDGE_COLLECTION,
            pks=[item_id],
        )
        return {"message": f"✅ 记录 {item_id} 已从藏书阁中彻底抹除！"}
    except Exception as e:
        return {"error": f"删除失败: {str(e)}"}


# ==========================================
# ✏️ 知识库更新接口
# ==========================================
@router.put("/knowledge/{item_id}")
async def update_knowledge(
    item_id: str,
    content: str = Form(..., description="更新后的文字内容"),
    source: str = Form("未知古籍", description="更新后的出处"),
):
    """
    ✏️ 更新一条知识记录
    修改 content/source 后重新计算 embedding 向量，然后通过先删后插实现覆盖更新
    """
    try:
        # 1. 先查出旧记录的元数据（主要保留 image_url、data_type）
        old_records = milvus_client.query(
            collection_name=KNOWLEDGE_COLLECTION,
            filter=f'id == "{item_id}"',
            output_fields=["data_type", "metadata"],
        )
        if not old_records:
            return {"error": f"未找到 ID 为 {item_id} 的记录"}

        old = old_records[0]
        data_type = old.get("data_type", "text")
        metadata = old.get("metadata", {})

        # 2. 重新计算新文本的 embedding 向量
        print(f"🧠 正在为更新后的内容重新提取 2048 维特征...")
        vector = get_multimodal_embedding(text=content)

        # 3. 先删除旧记录
        milvus_client.delete(
            collection_name=KNOWLEDGE_COLLECTION,
            pks=[item_id],
        )

        # 4. 插入新记录（Milvus 会自动分配新 ID，因为是 auto_id）
        insert_data = {
            "data_type": data_type,
            "content": content,
            "source": source,
            "dense_vector": vector,
            "metadata": metadata,
        }
        res = milvus_client.insert(
            collection_name=KNOWLEDGE_COLLECTION,
            data=[insert_data],
        )
        inserted_ids = res.get("ids", []) if isinstance(res, dict) else getattr(res, 'primary_keys', [])
        new_id = inserted_ids[0] if inserted_ids else "未知ID"

        return {
            "message": "✅ 知识更新成功！向量特征已重新计算！",
            "old_id": item_id,
            "new_id": new_id,
        }
    except Exception as e:
        return {"error": f"更新失败: {str(e)}"}
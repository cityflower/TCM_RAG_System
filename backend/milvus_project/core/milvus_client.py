# milvus_project/core/milvus_client.py
import logging
from pymilvus import MilvusClient, DataType, Function, FunctionType
from ..config import MILVUS_URI, MILVUS_TOKEN, MILVUS_DB_NAME, VECTOR_DIM

logger = logging.getLogger(__name__)

# 全局 Milvus 客户端实例 (完全照搬你的原版)
milvus_client = MilvusClient(
    uri=MILVUS_URI, 
    token=MILVUS_TOKEN, 
    db_name=MILVUS_DB_NAME
)

# 多模态知识库名称
KNOWLEDGE_COLLECTION = "TCM_Knowledge"

def init_collection():
    """初始化 Milvus 集合，若不存在则创建大一统图文知识库"""
    

    if milvus_client.has_collection(KNOWLEDGE_COLLECTION):
        milvus_client.load_collection(KNOWLEDGE_COLLECTION)
        logger.info("Collection %s loaded.", KNOWLEDGE_COLLECTION)
    else:
        # 1. 定义 Schema (依然保留你原版的 jieba 分词器配置)
        analyzer = {"tokenizer": {"type": "jieba", "mode": "search"}}
        schema = MilvusClient.create_schema()
        
        # 基础主键
        schema.add_field("id", DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100)

        # 💡 新增核心字段：数据类型！用来区分这条记录是 "text" 还是 "image"
        schema.add_field("data_type", DataType.VARCHAR, max_length=50)

       # 内容字段：如果是 text 就存古籍段落，如果是 image 就存图片本地路径
        schema.add_field("content", DataType.VARCHAR, max_length=65535,
                         analyzer_params=analyzer, enable_analyzer=True, enable_match=True)

        # 来源说明：比如《神农本草经》或者 "用户上传草药图"
        schema.add_field("source", DataType.VARCHAR, max_length=255)

        # 向量字段 (注意这里调用了 config 里的 2048 维！)
        schema.add_field("sparse_vector", DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field("dense_vector", DataType.FLOAT_VECTOR, dim=VECTOR_DIM) 
        schema.add_field("metadata", DataType.JSON)

        # 添加 BM25 函数 (利用 Milvus 2.4+ 内置计算稀疏向量，极其省算力)
        schema.add_function(Function(
            name="bm25", function_type=FunctionType.BM25,
            input_field_names=["content"], output_field_names="sparse_vector"))

        # 2. 定义 Index
        idx = MilvusClient.prepare_index_params()
        idx.add_index("sparse_vector", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")
        idx.add_index("dense_vector", index_type="FLAT", metric_type="IP")

        # 3. 创建集合
        milvus_client.create_collection(KNOWLEDGE_COLLECTION, schema=schema, index_params=idx)
        print(f"\n🎉 终极多模态集合 {KNOWLEDGE_COLLECTION} (维度:{VECTOR_DIM}) 创建成功！")
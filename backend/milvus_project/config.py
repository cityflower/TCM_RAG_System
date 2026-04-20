# backend/milvus_project/config.py
import os

# ==========================================
# Milvus 数据库连接配置
# ==========================================
# 这里使用我们之前定好的 19531 端口
MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19531")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "")
MILVUS_DB_NAME = os.getenv("MILVUS_DB_NAME", "default")

# ==========================================
# 向量维度配置
# ==========================================
VECTOR_DIM = 2048  # 图文统一维度

LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")
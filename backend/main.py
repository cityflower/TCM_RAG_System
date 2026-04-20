# backend/main.py
import logging
from fastapi import FastAPI
import uvicorn

# 引入 MinIO 初始化和咱们刚写的核心路由
from milvus_project.core.minio_client import init_minio
from milvus_project.api.chat import router as chat_router
from milvus_project.api.knowledge import router as knowledge_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="中医多模态 RAG 系统 API", version="2.0.0")

# 把 chat 接口挂载到 /api 路径下     
app.include_router(chat_router, prefix="/api")

app.include_router(knowledge_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 正在启动中医系统后端...")
    # 唤醒 MinIO 管家
    init_minio()
    logger.info("✅ 后端服务准备就绪！")

@app.get("/")
def read_root():
    return {"message": "欢迎来到中医 RAG 系统！前端对接请访问 /docs 查看接口文档哦~"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
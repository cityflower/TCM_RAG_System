# backend/core/minio_client.py
import os
import logging
from minio import Minio

logger = logging.getLogger(__name__)

# MinIO 的默认配置 (跟咱们 docker-compose.yml 里的一致)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9003")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "tcm-images"

# 初始化客户端
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False # 本地开发不用 https
)

def init_minio():
    """系统启动时，检查并创建存储桶"""
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            
            # 设置策略：让前端网页可以直接通过链接读取图片 (公开读权限)
            policy = f'{{"Version":"2012-10-17","Statement":[{{"Effect":"Allow","Principal":{{"AWS":["*"]}},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::{BUCKET_NAME}/*"]}}]}}'
            minio_client.set_bucket_policy(BUCKET_NAME, policy)
            logger.info(f"🪣 MinIO 云相册 '{BUCKET_NAME}' 创建成功，并已开放前端访问权限！")
        else:
            logger.info(f"🪣 MinIO 云相册 '{BUCKET_NAME}' 已就绪。")
    except Exception as e:
        logger.error(f"❌ MinIO 连接失败，请检查 Docker 容器是否开启: {e}")

def upload_image_to_minio(local_file_path: str, file_name: str) -> str:
    """把本地图片上传到 MinIO，并返回专属下载链接"""
    try:
        minio_client.fput_object(BUCKET_NAME, file_name, local_file_path)
        # 组装出前端可以直接访问的图片 URL
        url = f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/{file_name}"
        return url
    except Exception as e:
        logger.error(f"上传图片到 MinIO 失败: {e}")
        return ""

if __name__ == "__main__":
    # 配置一下日志，不然终端里啥也看不见
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    print("\n🛠️ 正在单独呼叫 MinIO 云相册服务器...")
    init_minio()
    print("✅ 测试结束！\n")
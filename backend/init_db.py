# backend/init_db.py
from milvus_project.core.milvus_client import init_collection

if __name__ == "__main__":
    print("🚀 准备初始化 Milvus 数据库...")
    
    # 调用咱们前面写好的大一统建库逻辑
    init_collection()
    
    print("✅ 数据库创建完毕！以后你只要不删库，就再也不用运行这个文件啦！")
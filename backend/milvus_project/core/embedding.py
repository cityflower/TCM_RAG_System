# backend/core/embedding.py (或你的对应路径)
import os
import torch

from torch import device

# 🌟 见证奇迹：我们直接调用阿里官方写好的超强翻译官类！
from src.models.qwen3_vl_embedding import Qwen3VLEmbedder

# 指向咱们本地下载好的 2B Embedding 模型
MODEL_ID = "./models/Qwen3-VL-Embedding-2B" 

print("🌟 正在通过阿里官方专属通道加载 Qwen3-VL 多模态翻译官...")

# 官方的类极其强大，内部自动搞定了所有的 M4 加速、图文占位符拼接！
model = Qwen3VLEmbedder(
    model_name_or_path=MODEL_ID,
    device_map="mps",
    torch_dtype=torch.bfloat16      # 👈 开启半精度加速
)

def get_multimodal_embedding(text: str = None, image_path: str = None) -> list:
    """
    终极多模态提取函数！(官方 API 版)
    无论你传什么，它都能完美吐出 2048 维向量！
    """
    if text is None and image_path is None:
        raise ValueError("文字和图片至少得传一个吧，闺蜜！")

    # 1. 严格按照官方 README 的格式组装字典
    input_data = {}
    if text:
        input_data["text"] = text
    if image_path and os.path.exists(image_path):
        input_data["image"] = image_path

    # 2. 一键扔给官方的 process 处理！(注意官方要求外面套一个列表)
    embeddings = model.process([input_data])
    
    # 3. 拿到第一条数据的张量，转成普通的 Python 列表返回
    return embeddings[0].tolist()

# ==========================================
# 🧪 随堂小测试：让翻译官大显身手！
# ==========================================
if __name__ == "__main__":
    print("\n✅ Qwen3-VL 翻译官准备就绪！开始测试：")
    
    # ---------------------------
    # 测试 1：纯文本提取
    # ---------------------------
    print("\n[测试 1] 正在将文字翻译成向量...")
    test_text = "人参，味甘微寒。主补五脏，安精神。"
    vec_text = get_multimodal_embedding(text=test_text)
    print(f"📝 文本翻译成功！维度是: {len(vec_text)} 维！")
    print(f"👀 偷偷看一眼前 3 个数字: {vec_text[:3]}")
    
    # ---------------------------
    # 测试 2：纯图片提取
    # ---------------------------
    # 请确保你的代码同级目录下有一张叫 test.jpg 的图片哦！(或者填你刚刚的 image (1).png)
    image_file = "image (1).png" 
    
    if os.path.exists(image_file):
        print(f"\n[测试 2] 正在将图片 {image_file} 翻译成向量...")
        vec_image = get_multimodal_embedding(image_path=image_file)
        print(f"🖼️ 图片翻译成功！维度依然是: {len(vec_image)} 维！")
        print(f"👀 偷偷看一眼前 3 个数字: {vec_image[:3]}")
        
        # ---------------------------
        # 测试 3：图文双拼提取
        # ---------------------------
        print("\n[测试 3] 正在把图和文字揉在一起翻译...")
        vec_mix = get_multimodal_embedding(text="帮我看看这是不是人参", image_path=image_file)
        print(f"🍲 混合翻译成功！维度必须也是: {len(vec_mix)} 维！")
    else:
        print(f"\n[测试 2/3] ⚠️ 没找到 {image_file}，确保图片名字和路径是对的哦！")

    print("\n🎉 恭喜，你的多模态特征提取器火力全开！")
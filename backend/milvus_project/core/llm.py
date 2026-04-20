# backend/milvus_project/core/llm.py
import os
from openai import OpenAI

# 初始化 OpenAI 客户端，指向你本地的 LM Studio 服务
# 默认端口通常是 1234，请根据你的 LM Studio 顶部显示的 Server 端口为准
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

def generate_rag_response_stream(query, best_docs, image_info=None):
    """流式生成回答，并完美截获大模型的深度思考过程"""
    
    # ==========================================
    # 1. 组装参考资料与提示词
    # ==========================================
    context_text = ""
    if best_docs:
        for i, doc in enumerate(best_docs):
            content = doc.get('content', '')
            source = doc.get('source', '未知古籍')
            context_text += f"\n--- 资料 {i+1} ({source}) ---\n{content}\n"

    # 拼接最终发送给大模型的内容
    prompt = f"患者提问: {query}\n"
    if image_info:
        prompt += f"附带图片线索: {image_info}\n"
    if context_text:
        prompt += f"\n请严格参考以下从本地知识库检索到的古籍资料进行解答：\n{context_text}"

    messages = [
        {"role": "system", "content": "你是一位资深、专业的老中医。请根据提供的资料，用温和、易懂的语气解答患者的疑惑。"},
        {"role": "user", "content": prompt}
    ]

    # ==========================================
    # 2. 向 LM Studio 发起请求
    # ==========================================
    try:
        response = client.chat.completions.create(
            model="local-model", # 💡 市花注意：在 LM Studio 中，模型名填 "local-model" 即可万能适配
            messages=messages,
            temperature=0.7,
            stream=True
            # 已经去掉了 extra_body，让它自由思考，我们在下面用代码拦截！
        )

        is_thinking = False # 状态标记：记录模型当前是否处于“深度思考”模式

        # ==========================================
        # 3. 逐字解析流式响应，完美排版输出
        # ==========================================
        for chunk in response:
            if getattr(chunk, 'choices', None) is None or len(chunk.choices) == 0:
                continue
                
            delta = chunk.choices[0].delta

            # 🕵️‍♀️ 拦截方案 A：针对主流标准 (reasoning_content 字段)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                if not is_thinking:
                    yield "\n\n🤔 **[老中医正在翻阅医书，深度思考中...]**\n> "
                    is_thinking = True
                # 给每行思考加上 '>'，变成 Markdown 引用格式
                yield delta.reasoning_content.replace('\n', '\n> ')
                continue

            # 📢 拦截方案 B：针对常规文本混杂 <think> 标签 (content 字段)
            if hasattr(delta, 'content') and delta.content:
                content_text = delta.content
                
                # 1. 捕捉到了 <think> 开始标签
                if "<think>" in content_text:
                    if not is_thinking:
                        yield "\n\n🤔 **[老中医正在翻阅医书，深度思考中...]**\n> "
                        is_thinking = True
                    content_text = content_text.replace("<think>", "")
                    
                # 2. 捕捉到了 </think> 结束标签
                if "</think>" in content_text:
                    yield "\n\n✅ **[思考完毕，以下是正式诊断结果]**\n\n"
                    is_thinking = False
                    content_text = content_text.replace("</think>", "")

                # 3. 状态自然切换：前一秒还在 reasoning_content 里思考，这一秒突然开始吐普通 content 了
                if is_thinking and content_text.strip() != "":
                    yield "\n\n✅ **[思考完毕，以下是正式诊断结果]**\n\n"
                    is_thinking = False
                
                # 4. 保证输出格式排版干净
                if is_thinking and content_text:
                     yield content_text.replace('\n', '\n> ')
                else:
                    yield content_text

    except Exception as e:
        yield f"\n\n❌ 呼叫老中医时发生异常: {str(e)}"
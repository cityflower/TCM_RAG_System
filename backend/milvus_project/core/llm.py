# backend/milvus_project/core/llm.py
import os
from openai import OpenAI

# 初始化 OpenAI 客户端，指向你本地的 LM Studio 服务
# 默认端口通常是 1234，请根据你的 LM Studio 顶部显示的 Server 端口为准
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")


def _doc_title(doc):
    content = doc.get("content", "")
    for label in ("药材名称", "中药名称", "名称", "证型名称"):
        marker = f"{label}："
        if marker in content:
            return content.split(marker, 1)[1].splitlines()[0].strip()
    return (doc.get("source", "候选项").split("/")[-1] or "候选项").strip()


def _format_doc_line(doc, index):
    content = doc.get("content", "")
    source = doc.get("source", "未知来源")
    score = doc.get("score", doc.get("retrieval_score", ""))
    score_text = f"；相关度：{float(score):.3f}" if isinstance(score, (int, float)) else ""
    return f"\n--- 资料 {index}（{source}{score_text}）---\n{content}\n"


def _format_image_result_line(item, index):
    content = item.get("content", "")
    score = item.get("score", item.get("retrieval_score", ""))
    score_text = f"，相似度 {float(score):.3f}" if isinstance(score, (int, float)) else ""
    return f"\n--- 候选药材 {index}：{item.get('name') or _doc_title(item)}{score_text} ---\n{content}\n"


def generate_rag_response_stream(query, best_docs, image_info=None, image_results=None):
    """流式生成回答，并完美截获大模型的深度思考过程"""
    
    # ==========================================
    # 1. 组装参考资料与提示词
    # ==========================================
    is_image_query = bool(image_info)
    image_results = image_results or []

    context_text = ""
    if is_image_query and image_results:
        for i, item in enumerate(image_results[:5]):
            context_text += _format_image_result_line(item, i + 1)
    elif best_docs:
        for i, doc in enumerate(best_docs):
            context_text += _format_doc_line(doc, i + 1)

    if is_image_query:
        system_prompt = (
            "你是“本草智询”的中医药图文问答助手。"
            "回答要像一个靠谱、直接的助手：先说结论，再用简短依据说明，不寒暄、不客套、不写鉴定报告腔。"
            "不要提到知识库、检索、资料来源、系统召回等内部过程；把可用信息自然地组织成回答。"
            "不要编造未给出的药材、功效或禁忌。"
        )
        prompt = f"""用户问题：{query or "请识别图片中的中药材，并说明相关功效。"}
图片线索：用户上传了一张待识别药材图片。
{f"图片存储位置：{image_info}" if image_info else ""}

可用参考信息如下，仅供你组织回答时使用，禁止在回答中提到“参考信息”“知识库”“检索结果”等字样：
{context_text or "未检索到可靠资料。"}

请用自然助手风格回答，遵守这些要求：
1. 不要以“您好”“从您提供的图片来看”“希望这个回答对您有所帮助”“如果有任何其他问题”开头或结尾。
2. 不要说“在用药前最好咨询专业中医师的建议，确保安全合理地使用”这类模板话。
3. 第一句话直接给结论，药材名必须优先取排名第一的候选药材；不要照抄示例，不要固定回答某一种药材。
4. 接着用 2-3 句话说明依据，重点写颜色、形态、纹理、切片/果皮/根茎等特征。
5. 使用 Markdown 的三级标题：### 初步识别、### 识别依据、### 功效、### 注意事项。
6. 功效和注意事项用简短项目符号列出，每部分 2-3 条即可。
7. 如果资料中有禁忌，只写具体禁忌；没有就不要泛泛提醒。
8. 最终回答里不要出现“知识库”“检索”“资料”“参考信息”“系统”等词。
9. 总字数控制在 250 字以内。"""
    else:
        system_prompt = (
            "你是“本草智询”的中医药知识问答助手。"
            "先给结论，再给依据，回答要自然像助手，不要暴露知识库、检索、资料来源、系统召回等内部过程。"
            "涉及用药、诊断和禁忌时必须谨慎，提醒用户咨询专业医师。"
        )
        prompt = f"""用户问题：{query}

可用参考信息如下，仅供你组织回答时使用，禁止在回答中提到“参考信息”“知识库”“检索结果”等字样：
{context_text or "未检索到可靠资料。"}

请按下面结构回答：

### 简要结论
直接回答用户最关心的问题。

### 依据说明
自然说明原因，不要写“根据资料”“根据知识库”“检索显示”等表达。

### 注意事项
涉及用药、体质、剂量或诊断时，给出谨慎提醒。

要求：不要编造未给出的信息；不要输出冗长客套话；不要出现“知识库”“检索”“资料”“参考信息”“系统”等词；回答控制在 500 字以内，除非用户要求详细解释。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # ==========================================
    # 2. 向 LM Studio 发起请求
    # ==========================================
    try:
        response = client.chat.completions.create(
            model="qwen2.5-vl-7b-instruct", # 💡 已经为你切换为 qwen2.5-vl-7b-instruct
            messages=messages,
            temperature=0.3,
            stream=True
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

/**
 * 流式对话 API
 * 调用后端 FastAPI 的 /api/chat/stream 端点
 *
 * @param {Object} payload - 请求体
 * @param {string} payload.query - 用户问题
 * @param {string|null} payload.session_id - 会话 ID
 * @param {File|null} payload.image_file - 图片文件对象（可选）
 * @param {Function} onChunk - 每收到一个字符串片段时的回调 (chunk: string) => void
 * @param {Function} onReferences - 收到 references 元数据时的回调 (refs: Object) => void
 * @param {Function} onDone - 流结束时的回调 () => void
 * @param {Function} onError - 发生错误时的回调 (error: Error) => void
 * @returns {AbortController} - 可调用 .abort() 取消请求
 */
export function streamChat({ query, session_id = null, image_file = null }, onChunk, onReferences, onDone, onError) {
  const controller = new AbortController()

  const formData = new FormData()
  formData.append('query', query)
  if (session_id) formData.append('session_id', session_id)
  if (image_file) formData.append('image', image_file)

  fetch('/api/chat', {
    method: 'POST',
    body: formData,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 按 SSE 行协议解析：每行以 "data: " 开头
        const lines = buffer.split('\n')
        buffer = lines.pop() // 保留最后一行（可能不完整）

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data:')) continue

          const raw = line.slice(5).trim() // 去掉 "data: " 前缀
          if (raw === '[DONE]') {
            onDone()
            return
          }

          try {
            const parsed = JSON.parse(raw)
            // 服务端约定：{ type: "text", content: "..." } 或 { type: "references", content: {...} }
            if (parsed.type === 'text') {
              onChunk(parsed.content)
            } else if (parsed.type === 'references') {
              onReferences(parsed.content)
            }
          } catch {
            // 如果解析失败，当作纯文本处理
            onChunk(raw)
          }
        }
      }

      onDone()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err)
      }
    })

  return controller
}

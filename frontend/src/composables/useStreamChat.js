import { ref, nextTick } from 'vue'
import { streamChat } from '@/api/chat.js'
import { fileToBase64 } from '@/api/upload.js'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

// 配置 marked 支持语法高亮
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

/**
 * 核心聊天 composable
 */
export function useStreamChat() {
  const messages = ref([])     // 消息列表
  const isLoading = ref(false) // 是否正在等待/流式输出
  const references = ref({     // 溯源数据
    textChunks: [],
    imageResults: [],
  })
  const sessionId = ref(null)  // 会话 ID

  let abortController = null   // 用于中断请求

  /**
   * 将 Markdown 字符串渲染成安全 HTML
   */
  function renderMarkdown(text) {
    const dirty = marked(text || '')
    return DOMPurify.sanitize(dirty)
  }

  /**
   * 发送消息
   * @param {string} query - 用户文字输入
   * @param {File|null} imageFile - 可选图片文件
   * @param {Function} scrollToBottomFn - 触发滚动的回调
   */
  async function sendMessage(query, imageFile = null, scrollToBottomFn = null) {
    if (isLoading.value || (!query.trim() && !imageFile)) return

    // 构建图片信息（预览用）
    let imagePreview = null
    let imageBase64 = null
    if (imageFile) {
      imageBase64 = await fileToBase64(imageFile)
      imagePreview = imageBase64 // data URL 直接用于 <img>
    }

    // 添加用户消息
    messages.value.push({
      id: Date.now(),
      role: 'user',
      text: query.trim(),
      imagePreview,
      time: new Date(),
    })

    // 清空溯源面板
    references.value = { textChunks: [], imageResults: [] }

    // 添加 AI 占位消息（流式填充）
    const aiMsgId = Date.now() + 1
    messages.value.push({
      id: aiMsgId,
      role: 'assistant',
      text: '',
      html: '',
      streaming: true,
      time: new Date(),
    })

    isLoading.value = true
    await nextTick()
    scrollToBottomFn?.()

    const aiMsg = messages.value.find(m => m.id === aiMsgId)

    abortController = streamChat(
      {
        query: query.trim() || '请根据图片识别这味草药',
        session_id: sessionId.value,
        image_file: imageFile, 
      },
      // onChunk: 接收文本片段
      (chunk) => {
        if (!aiMsg) return
        aiMsg.text += chunk
        aiMsg.html = renderMarkdown(aiMsg.text)
        scrollToBottomFn?.()
      },
      // onReferences: 接收溯源数据
      (refs) => {
        if (refs.session_id) sessionId.value = refs.session_id
        if (refs.text_chunks) references.value.textChunks = refs.text_chunks
        if (refs.image_results) references.value.imageResults = refs.image_results
      },
      // onDone
      () => {
        if (aiMsg) {
          aiMsg.streaming = false
          aiMsg.html = renderMarkdown(aiMsg.text)
        }
        isLoading.value = false
        scrollToBottomFn?.()
      },
      // onError
      (err) => {
        if (aiMsg) {
          aiMsg.text = `⚠️ 请求失败：${err.message}`
          aiMsg.html = `<p class="text-red-500">⚠️ 请求失败：${err.message}</p>`
          aiMsg.streaming = false
        }
        isLoading.value = false
      }
    )
  }

  /**
   * 中断当前流式请求
   */
  function abortChat() {
    abortController?.abort()
    isLoading.value = false
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
      lastMsg.streaming = false
    }
  }

  /**
   * 清空对话
   */
  function clearChat() {
    abortChat()
    messages.value = []
    references.value = { textChunks: [], imageResults: [] }
    sessionId.value = null
  }

  return {
    messages,
    isLoading,
    references,
    sessionId,
    sendMessage,
    abortChat,
    clearChat,
    renderMarkdown,
  }
}

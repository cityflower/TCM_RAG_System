import { computed, nextTick, ref, watch } from 'vue'
import { streamChat } from '@/api/chat.js'
import { fileToBase64 } from '@/api/upload.js'
import { readStorage, writeStorage } from '@/utils/storage.js'
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
  const STORAGE_KEY = 'tcm.chat.sessions.v1'
  const ACTIVE_KEY = 'tcm.chat.activeSessionId.v1'
  const HISTORY_LIMIT = 30

  function createSession() {
    const id = `local_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`
    return {
      id,
      backendSessionId: null,
      title: '新问诊',
      messages: [],
      references: { textChunks: [], imageResults: [] },
      isLoading: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  }

  function hydrateSessions() {
    const cached = readStorage(STORAGE_KEY, [])
    if (!Array.isArray(cached) || cached.length === 0) return [createSession()]

    return cached.map((session) => ({
      ...createSession(),
      ...session,
      messages: Array.isArray(session.messages)
        ? session.messages.map((msg) => ({
            ...msg,
            streaming: false,
            time: msg.time || session.updatedAt || new Date().toISOString(),
          }))
        : [],
      references: session.references || { textChunks: [], imageResults: [] },
      isLoading: false,
    }))
  }

  function getSessionTitle(session) {
    const firstUserMessage = session.messages.find((msg) => msg.role === 'user' && msg.text)
    if (!firstUserMessage) return '新问诊'
    return firstUserMessage.text.replace(/\s+/g, ' ').slice(0, 24)
  }

  function isBlankSession(session) {
    return !session?.messages?.length && !session?.backendSessionId
  }

  const sessions = ref(hydrateSessions())
  const cachedActiveId = localStorage.getItem(ACTIVE_KEY)
  const activeSessionId = ref(
    sessions.value.some((session) => session.id === cachedActiveId)
      ? cachedActiveId
      : sessions.value[0].id
  )

  const activeSession = computed(() => {
    return sessions.value.find((session) => session.id === activeSessionId.value) || sessions.value[0]
  })

  const messages = computed(() => activeSession.value?.messages || [])
  const references = computed(() => activeSession.value?.references || { textChunks: [], imageResults: [] })
  const sessionId = computed(() => activeSession.value?.backendSessionId || null)
  const isLoading = computed(() => Boolean(activeSession.value?.isLoading))
  const chatHistory = computed(() => (
    sessions.value
      .filter((session) => session.messages.length > 0)
      .map((session) => ({
        id: session.id,
        title: session.title || getSessionTitle(session),
        updatedAt: session.updatedAt,
        messageCount: session.messages.length,
        isLoading: Boolean(session.isLoading),
      }))
      .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
  ))

  const abortControllers = new Map() // 按会话保存中断器
  let persistTimer = null

  function persistSessions() {
    const data = sessions.value
      .filter((session) => session.messages.length > 0 || session.id === activeSessionId.value)
      .map((session) => ({
        ...session,
        isLoading: false,
        messages: session.messages.map((msg) => ({ ...msg, streaming: false })),
      }))
      .slice()
      .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
      .slice(0, HISTORY_LIMIT)
    writeStorage(STORAGE_KEY, data)
    localStorage.setItem(ACTIVE_KEY, activeSessionId.value)
  }

  function schedulePersist() {
    clearTimeout(persistTimer)
    persistTimer = setTimeout(persistSessions, 250)
  }

  watch(sessions, schedulePersist, { deep: true })
  watch(activeSessionId, schedulePersist)

  function touchSession(session) {
    session.updatedAt = new Date().toISOString()
    session.title = getSessionTitle(session)
  }

  function setActiveSession(id) {
    if (!sessions.value.some((session) => session.id === id)) return
    activeSessionId.value = id
  }

  function ensureActiveSession() {
    if (activeSession.value) return activeSession.value
    const session = createSession()
    sessions.value.unshift(session)
    activeSessionId.value = session.id
    return session
  }

  function shouldScrollSession(sessionId) {
    return activeSessionId.value === sessionId
  }

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
    const currentSession = ensureActiveSession()
    if (currentSession.isLoading || (!query.trim() && !imageFile)) return
    const currentSessionId = currentSession.id

    // 构建图片信息（预览用）
    let imagePreview = null
    let imageBase64 = null
    if (imageFile) {
      imageBase64 = await fileToBase64(imageFile)
      imagePreview = imageBase64 // data URL 直接用于 <img>
    }

    // 添加用户消息
    currentSession.messages.push({
      id: Date.now(),
      role: 'user',
      text: query.trim(),
      imagePreview,
      time: new Date(),
    })

    // 清空溯源面板
    currentSession.references = { textChunks: [], imageResults: [] }

    // 添加 AI 占位消息（流式填充）
    const aiMsgId = Date.now() + 1
    currentSession.messages.push({
      id: aiMsgId,
      role: 'assistant',
      text: '',
      html: '',
      streaming: true,
      time: new Date(),
    })
    touchSession(currentSession)

    currentSession.isLoading = true
    await nextTick()
    if (shouldScrollSession(currentSessionId)) scrollToBottomFn?.()

    const aiMsg = currentSession.messages.find(m => m.id === aiMsgId)

    const controller = streamChat(
      {
        query: query.trim() || '请根据图片识别这味草药',
        session_id: currentSession.backendSessionId,
        image_file: imageFile, 
      },
      // onChunk: 接收文本片段
      (chunk) => {
        if (!aiMsg) return
        aiMsg.text += chunk
        aiMsg.html = renderMarkdown(aiMsg.text)
        touchSession(currentSession)
        if (shouldScrollSession(currentSessionId)) scrollToBottomFn?.()
      },
      // onReferences: 接收溯源数据
      (refs) => {
        if (refs.session_id) currentSession.backendSessionId = refs.session_id
        if (refs.text_chunks) currentSession.references.textChunks = refs.text_chunks
        if (refs.image_results) currentSession.references.imageResults = refs.image_results
        touchSession(currentSession)
      },
      // onDone
      () => {
        if (aiMsg) {
          aiMsg.streaming = false
          aiMsg.html = renderMarkdown(aiMsg.text)
        }
        currentSession.isLoading = false
        abortControllers.delete(currentSessionId)
        touchSession(currentSession)
        if (shouldScrollSession(currentSessionId)) scrollToBottomFn?.()
      },
      // onError
      (err) => {
        if (aiMsg) {
          aiMsg.text = `⚠️ 请求失败：${err.message}`
          aiMsg.html = `<p class="text-red-500">⚠️ 请求失败：${err.message}</p>`
          aiMsg.streaming = false
        }
        currentSession.isLoading = false
        abortControllers.delete(currentSessionId)
        touchSession(currentSession)
      }
    )
    abortControllers.set(currentSessionId, controller)
  }

  /**
   * 中断当前流式请求
   */
  function abortChat() {
    const session = activeSession.value
    if (!session) return

    abortControllers.get(session.id)?.abort()
    abortControllers.delete(session.id)
    session.isLoading = false
    const lastMsg = session.messages[session.messages.length - 1]
    if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
      lastMsg.streaming = false
    }
    touchSession(session)
  }

  function abortSession(id) {
    const session = sessions.value.find((item) => item.id === id)
    if (!session) return

    abortControllers.get(id)?.abort()
    abortControllers.delete(id)
    session.isLoading = false
    const lastMsg = session.messages[session.messages.length - 1]
    if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
      lastMsg.streaming = false
    }
    touchSession(session)
  }

  /**
   * 清空对话
   */
  function clearChat() {
    abortChat()
    const session = ensureActiveSession()
    session.messages = []
    session.references = { textChunks: [], imageResults: [] }
    session.backendSessionId = null
    session.title = '新问诊'
    touchSession(session)
  }

  function newChat() {
    const blankSession = sessions.value.find((session) => isBlankSession(session))
    if (blankSession) {
      activeSessionId.value = blankSession.id
      return
    }

    const session = createSession()
    sessions.value.unshift(session)
    activeSessionId.value = session.id
  }

  function deleteSession(id) {
    abortSession(id)
    const nextSessions = sessions.value.filter((session) => session.id !== id)
    sessions.value = nextSessions.length > 0 ? nextSessions : [createSession()]
    if (activeSessionId.value === id) {
      activeSessionId.value = sessions.value[0].id
    }
  }

  return {
    messages,
    isLoading,
    references,
    sessionId,
    activeSessionId,
    chatHistory,
    sendMessage,
    abortChat,
    clearChat,
    newChat,
    setActiveSession,
    deleteSession,
    renderMarkdown,
  }
}

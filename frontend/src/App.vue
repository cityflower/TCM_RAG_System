<template>
  <div class="app-layout">

    <!-- ======== 左侧边栏 ======== -->
    <Sidebar
      :active-view="activeView"
      :active-session-id="activeSessionId"
      :chat-history="chatHistory"
      @switch-view="switchView"
      @new-chat="handleNewChat"
      @select-chat="handleSelectChat"
      @delete-chat="handleDeleteChat"
    />

    <!-- ======== 右侧主工作区 ======== -->
    <div class="app-main">

      <!-- ====== 视图 A：问诊工作台 ====== -->
      <template v-if="activeView === 'chat'">
        <!-- 顶部 Header -->
        <header class="chat-header">
          <div class="flex items-center gap-3">
            <div>
              <h1 class="text-base font-bold text-tcm-800 leading-none">中医智能问诊</h1>
              <p class="text-xs text-tcm-500 leading-tight mt-0.5">基于 Milvus 向量检索的知识增强问答</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <!-- 连接状态 -->
            <div class="flex items-center gap-1.5">
              <span :class="['w-2 h-2 rounded-full', activeChatLoading ? 'bg-amber-400 animate-pulse' : 'bg-green-400']"></span>
              <span class="text-xs text-gray-500">{{ activeChatLoading ? '生成中…' : '就绪' }}</span>
            </div>

            <!-- 会话 ID -->
            <span v-if="sessionId" class="hidden sm:block text-xs text-gray-300 font-mono">
              {{ sessionId.slice(0, 8) }}…
            </span>

            <!-- 清空对话 -->
            <button
              @click="handleClear"
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg border border-gray-200 hover:border-red-200 transition-all duration-200"
              title="清空当前对话"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              清空
            </button>
          </div>
        </header>

        <!-- 主内容区：左右分栏 -->
        <div class="flex flex-1 overflow-hidden">
          <!-- 左侧：对话区 -->
          <div class="flex flex-col flex-[3] min-w-0 border-r border-tcm-100 overflow-hidden">
            <ChatBox
              ref="chatBoxRef"
              :messages="messages"
              @quick-ask="handleQuickAsk"
              class="flex-1"
            />
            <div class="relative flex-shrink-0">
              <ChatInput
                ref="chatInputRef"
                :is-loading="activeChatLoading"
                :draft-key="`chat-draft-${activeSessionId}`"
                @send="handleSend"
                @abort="abortChat"
              />
            </div>
          </div>

          <!-- 右侧：知识溯源面板 -->
          <div class="flex-[1.4] min-w-0 hidden sm:flex flex-col overflow-hidden">
            <ReferencePanel
              :text-chunks="references.textChunks"
              :image-results="references.imageResults"
              :is-loading="activeChatLoading"
            />
          </div>
        </div>
      </template>

      <!-- ====== 视图 B：知识库管理 ====== -->
      <template v-else-if="activeView === 'knowledge'">
        <KnowledgeManager />
      </template>

      <!-- ====== 视图 C：症状辨证 ====== -->
      <template v-else-if="activeView === 'differentiation'">
        <SymptomDifferentiation v-show="activeView === 'differentiation'" />
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import ChatBox from '@/components/ChatBox.vue'
import ChatInput from '@/components/ChatInput.vue'
import ReferencePanel from '@/components/ReferencePanel.vue'
import KnowledgeManager from '@/components/KnowledgeManager.vue'
import SymptomDifferentiation from '@/components/SymptomDifferentiation.vue'
import { useStreamChat } from '@/composables/useStreamChat.js'

const chatBoxRef = ref(null)
const chatInputRef = ref(null)

// 视图切换
const activeView = ref(localStorage.getItem('activeView') || 'chat') // 'chat' | 'knowledge' | 'differentiation'

function switchView(view) {
  activeView.value = view
  localStorage.setItem('activeView', view)
}

// 聊天逻辑
const {
  messages,
  references,
  sessionId,
  isLoading: activeChatLoading,
  activeSessionId,
  chatHistory,
  sendMessage,
  abortChat,
  clearChat,
  newChat,
  setActiveSession,
  deleteSession,
} = useStreamChat()

function handleSend({ text, imageFile }) {
  sendMessage(text, imageFile, () => chatBoxRef.value?.scrollToBottom())
}

function handleQuickAsk(tip) {
  const cleanTip = tip.replace(/^[^\w\u4e00-\u9fff]+/, '').trim()
  chatInputRef.value?.setQuickQuestion(cleanTip)
}

function handleClear() {
  if (messages.value.length === 0) return
  if (confirm('确定要清空当前对话吗？')) {
    clearChat()
  }
}

function handleNewChat() {
  switchView('chat')
  newChat()
}

function handleSelectChat(id) {
  switchView('chat')
  setActiveSession(id)
}

function handleDeleteChat(id) {
  if (confirm('确定要删除这条历史会话吗？')) {
    deleteSession(id)
  }
}
</script>

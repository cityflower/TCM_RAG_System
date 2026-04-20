<template>
  <div class="flex flex-col h-screen bg-tcm-50 overflow-hidden">

    <!-- 顶部 Header -->
    <header class="flex items-center justify-between px-6 py-3 bg-white border-b border-tcm-100 shadow-sm flex-shrink-0 z-10">
      <!-- Logo + 标题 -->
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-tcm-400 to-tcm-700 flex items-center justify-center shadow-md">
          <span class="text-xl">🌿</span>
        </div>
        <div>
          <h1 class="text-lg font-bold text-tcm-800 leading-none">本草智询</h1>
          <p class="text-xs text-tcm-500 leading-tight mt-0.5">中医药知识检索增强问答系统</p>
        </div>
      </div>

      <!-- 系统状态指示器 + 操作按钮 -->
      <div class="flex items-center gap-3">
        <!-- 连接状态 -->
        <div class="flex items-center gap-1.5">
          <span :class="['w-2 h-2 rounded-full', isLoading ? 'bg-amber-400 animate-pulse' : 'bg-green-400']"></span>
          <span class="text-xs text-gray-500">{{ isLoading ? '生成中…' : '就绪' }}</span>
        </div>

        <!-- 会话 ID 显示 -->
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

      <!-- ======== 左侧：对话区 ======== -->
      <div class="flex flex-col flex-[3] min-w-0 border-r border-tcm-100 overflow-hidden">

        <!-- 消息展示区 -->
        <ChatBox
          ref="chatBoxRef"
          :messages="messages"
          @quick-ask="handleQuickAsk"
          class="flex-1"
        />

        <!-- 输入区 -->
        <div class="relative flex-shrink-0">
          <ChatInput
            ref="chatInputRef"
            :is-loading="isLoading"
            @send="handleSend"
            @abort="abortChat"
          />
        </div>
      </div>

      <!-- ======== 右侧：知识溯源面板 ======== -->
      <div class="flex-[1.4] min-w-0 hidden sm:flex flex-col overflow-hidden">
        <ReferencePanel
          :text-chunks="references.textChunks"
          :image-results="references.imageResults"
          :is-loading="isLoading"
        />
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatBox from '@/components/ChatBox.vue'
import ChatInput from '@/components/ChatInput.vue'
import ReferencePanel from '@/components/ReferencePanel.vue'
import { useStreamChat } from '@/composables/useStreamChat.js'

const chatBoxRef = ref(null)
const chatInputRef = ref(null)

const { messages, isLoading, references, sessionId, sendMessage, abortChat, clearChat } = useStreamChat()

/**
 * 处理发送消息
 */
function handleSend({ text, imageFile }) {
  sendMessage(text, imageFile, () => chatBoxRef.value?.scrollToBottom())
}

/**
 * 处理快捷提问点击
 */
function handleQuickAsk(tip) {
  // 去除 emoji 前缀填入输入框
  const cleanTip = tip.replace(/^[^\w\u4e00-\u9fff]+/, '').trim()
  chatInputRef.value?.setQuickQuestion(cleanTip)
}

/**
 * 清空对话
 */
function handleClear() {
  if (messages.value.length === 0) return
  if (confirm('确定要清空当前对话吗？')) {
    clearChat()
  }
}
</script>

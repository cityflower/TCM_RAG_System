<template>
  <!-- 消息列表滚动区 -->
  <div
    ref="scrollRef"
    class="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 space-y-5"
  >
    <!-- 空状态欢迎屏 -->
    <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full gap-6 text-center select-none">
      <div class="w-24 h-24 rounded-full bg-gradient-to-br from-tcm-300 to-tcm-600 flex items-center justify-center shadow-xl">
        <span class="text-5xl">🌿</span>
      </div>
      <div>
        <h2 class="text-2xl font-bold text-tcm-800 mb-2">本草智询</h2>
        <p class="text-tcm-600 text-sm max-w-xs leading-relaxed">
          基于 Milvus 向量检索的中医药知识问答系统<br/>
          可提问中医理论、上传草药图片进行"看图识药"
        </p>
      </div>
      <!-- 快捷提示词 -->
      <div class="grid grid-cols-2 gap-2 max-w-md w-full mt-2">
        <button
          v-for="tip in quickTips"
          :key="tip"
          @click="$emit('quick-ask', tip)"
          class="px-3 py-2 text-xs text-tcm-700 bg-white border border-tcm-200 rounded-xl hover:bg-tcm-50 hover:border-tcm-400 transition-all duration-200 text-left shadow-sm"
        >
          {{ tip }}
        </button>
      </div>
    </div>

    <!-- 消息气泡列表 -->
    <template v-else>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex animate-fade-in"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- AI 头像 -->
        <div
          v-if="msg.role === 'assistant'"
          class="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-tcm-400 to-tcm-700 flex items-center justify-center mr-2.5 mt-0.5 shadow-md"
        >
          <span class="text-lg">🌿</span>
        </div>

        <!-- 气泡内容 -->
        <div
          class="max-w-[78%] rounded-2xl px-4 py-3 shadow-sm"
          :class="msg.role === 'user'
            ? 'bg-gradient-to-br from-tcm-100 to-tcm-200 text-gray-800 rounded-tr-sm'
            : 'bg-white text-gray-800 rounded-tl-sm border border-gray-100'"
        >
          <!-- 用户图片预览 -->
          <div v-if="msg.imagePreview" class="mb-2">
            <img
              :src="msg.imagePreview"
              class="max-h-36 max-w-full rounded-xl object-cover border border-tcm-200"
              alt="上传的图片"
            />
          </div>

          <!-- 用户文字 -->
          <p v-if="msg.role === 'user' && msg.text" class="text-sm leading-relaxed whitespace-pre-wrap break-words">{{ msg.text }}</p>

          <!-- AI 回答（Markdown 渲染） -->
          <div v-if="msg.role === 'assistant'">
            <!-- 加载中（等待首个字符） -->
            <div v-if="msg.streaming && !msg.text" class="flex items-center gap-1 py-1 loading-dots">
              <span></span><span></span><span></span>
            </div>
            <!-- 流式/完成输出 -->
            <div
              v-else
              class="markdown-content text-sm"
              :class="{ 'typing-cursor': msg.streaming }"
              v-html="msg.html || escapeHtml(msg.text)"
            ></div>
          </div>

          <!-- 消息时间 -->
          <p class="text-xs mt-1.5 opacity-40 text-right select-none">
            {{ formatTime(msg.time) }}
          </p>
        </div>

        <!-- 用户头像 -->
        <div
          v-if="msg.role === 'user'"
          class="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 flex items-center justify-center ml-2.5 mt-0.5 shadow-md"
        >
          <span class="text-lg">👤</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['quick-ask'])

const scrollRef = ref(null)

const quickTips = [
  '🌿 黄芪的功效与禁忌是什么？',
  '🔍 如何区分真假西洋参？',
  '📷 上传图片，帮我识别这味草药',
  '💊 六味地黄丸的组方是什么？',
]

function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

function escapeHtml(text) {
  return (text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/**
 * 暴露给父组件调用的滚动方法
 */
function scrollToBottom(smooth = true) {
  nextTick(() => {
    const el = scrollRef.value
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'instant' })
  })
}

// 消息列表或流式内容变化时自动滚动
watch(
  () => props.messages.map(m => m.text).join('|'),
  () => scrollToBottom(true),
  { flush: 'post' }
)

defineExpose({ scrollToBottom })
</script>

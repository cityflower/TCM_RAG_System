<template>
  <div class="flex flex-col gap-2 p-3 border-t border-tcm-100 bg-white">
    <!-- 图片预览区 -->
    <div
      v-if="imagePreview"
      class="flex items-start gap-2 px-2 py-2 bg-tcm-50 border border-tcm-200 rounded-xl animate-slide-up"
    >
      <img
        :src="imagePreview"
        class="h-20 w-20 object-cover rounded-lg border border-tcm-300 flex-shrink-0"
        alt="待上传图片预览"
      />
      <div class="flex flex-col flex-1 min-w-0">
        <p class="text-xs font-medium text-tcm-700 truncate">{{ imageFile?.name || '上传的图片' }}</p>
        <p class="text-xs text-tcm-500">{{ formatFileSize(imageFile?.size) }}</p>
      </div>
      <button
        @click="removeImage"
        class="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-gray-200 hover:bg-red-100 hover:text-red-600 text-gray-500 text-xs transition-colors duration-200"
        title="删除图片"
      >
        ✕
      </button>
    </div>

    <!-- 拖拽提示遮罩 -->
    <div
      v-if="isDragging"
      class="absolute inset-0 bg-tcm-500/10 border-2 border-dashed border-tcm-500 rounded-2xl flex items-center justify-center z-50 backdrop-blur-sm pointer-events-none"
    >
      <div class="flex flex-col items-center gap-2 text-tcm-700">
        <span class="text-4xl">🖼️</span>
        <p class="font-semibold text-sm">松开鼠标上传图片</p>
      </div>
    </div>

    <!-- 输入行 -->
    <div
      class="flex items-end gap-2 bg-gray-50 rounded-2xl border border-gray-200 px-3 py-2 transition-all duration-200 focus-within:border-tcm-400 focus-within:shadow-md focus-within:shadow-tcm-100"
      :class="{ 'border-tcm-400': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <!-- 图片上传按钮 -->
      <label
        class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-xl hover:bg-tcm-100 text-tcm-500 hover:text-tcm-700 cursor-pointer transition-colors duration-200"
        title="上传草药图片（支持拖拽）"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="handleFileChange"
        />
      </label>

      <!-- 文字输入框 -->
      <textarea
        ref="textareaRef"
        v-model="inputText"
        :placeholder="imagePreview ? '可追加文字描述，或直接发送图片...' : '询问中医药知识，或上传草药图片进行识别...'"
        :disabled="isLoading"
        rows="1"
        class="flex-1 bg-transparent resize-none outline-none text-sm text-gray-700 placeholder-gray-400 leading-6 max-h-32 overflow-y-auto scrollbar-thin py-0.5 disabled:opacity-50"
        @keydown.enter.prevent="handleEnter"
        @input="autoResize"
      ></textarea>

      <!-- 发送/停止按钮 -->
      <button
        @click="isLoading ? $emit('abort') : handleSend()"
        :disabled="!isLoading && !inputText.trim() && !imageFile"
        class="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-xl transition-all duration-200 shadow-sm"
        :class="isLoading
          ? 'bg-red-400 hover:bg-red-500 text-white'
          : (inputText.trim() || imageFile)
            ? 'bg-tcm-500 hover:bg-tcm-600 text-white hover:shadow-md'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
        :title="isLoading ? '停止生成' : '发送'"
      >
        <!-- Loading 动画 -->
        <svg v-if="isLoading" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="4" height="4" rx="1"/>
          <rect x="14" y="6" width="4" height="4" rx="1"/>
          <rect x="6" y="14" width="4" height="4" rx="1"/>
          <rect x="14" y="14" width="4" height="4" rx="1"/>
        </svg>
        <!-- 发送箭头 -->
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
            d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <p class="text-xs text-gray-400 text-center select-none">
      Enter 发送 · Shift+Enter 换行 · 支持拖拽图片上传
    </p>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  isLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'abort'])

const inputText = ref('')
const imageFile = ref(null)
const imagePreview = ref(null)
const isDragging = ref(false)
const textareaRef = ref(null)
const fileInputRef = ref(null)

function formatFileSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function handleEnter(e) {
  if (e.shiftKey) {
    // Shift+Enter 换行
    inputText.value += '\n'
    nextTick(autoResize)
    return
  }
  handleSend()
}

function handleSend() {
  if (props.isLoading) return
  if (!inputText.value.trim() && !imageFile.value) return

  emit('send', {
    text: inputText.value.trim(),
    imageFile: imageFile.value,
  })

  // 清空输入
  inputText.value = ''
  removeImage()
  nextTick(() => {
    autoResize()
    textareaRef.value?.focus()
  })
}

function removeImage() {
  imageFile.value = null
  imagePreview.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) setImage(file)
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    setImage(file)
  }
}

function setImage(file) {
  imageFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => { imagePreview.value = e.target.result }
  reader.readAsDataURL(file)
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 128) + 'px'
}

/**
 * 供父组件触发快捷提问
 */
function setQuickQuestion(text) {
  inputText.value = text
  nextTick(() => {
    autoResize()
    textareaRef.value?.focus()
  })
}

defineExpose({ setQuickQuestion })
</script>

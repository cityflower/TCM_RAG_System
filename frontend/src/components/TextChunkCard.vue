<template>
  <!-- 文本片段卡片 -->
  <div class="group bg-white border border-gray-100 rounded-xl p-3 hover:border-tcm-300 hover:shadow-md transition-all duration-200 animate-fade-in">
    <!-- 来源标签行 -->
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-1.5">
        <span class="text-xs font-bold text-tcm-600 bg-tcm-50 px-2 py-0.5 rounded-md border border-tcm-100">
          {{ chunk.source || '未知来源' }}
        </span>
        <span v-if="chunk.chapter" class="text-xs text-gray-400 truncate max-w-20">{{ chunk.chapter }}</span>
      </div>
      <!-- 序号徽章 -->
      <span class="text-xs text-gray-300 font-mono">#{{ index }}</span>
    </div>

    <!-- 相关度分数 -->
    <div v-if="chunk.score" class="flex items-center gap-1 mb-2">
      <div class="flex-1 bg-gray-100 rounded-full h-1">
        <div
          class="bg-gradient-to-r from-tcm-400 to-tcm-600 h-1 rounded-full transition-all duration-500"
          :style="{ width: Math.min(chunk.score * 100, 100) + '%' }"
        ></div>
      </div>
      <span class="text-xs text-gray-400">{{ (chunk.score * 100).toFixed(0) }}%</span>
    </div>

    <!-- 原文内容 -->
    <p class="text-xs text-gray-600 leading-relaxed line-clamp-4 group-hover:line-clamp-none transition-all duration-300">
      {{ chunk.content || chunk.text || '暂无内容' }}
    </p>

    <!-- 展开按钮（可选） -->
    <button
      v-if="(chunk.content || chunk.text || '').length > 120"
      class="mt-1.5 text-xs text-tcm-500 hover:text-tcm-700 transition-colors"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起 ▲' : '展开全文 ▼' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  chunk: { type: Object, required: true },
  index: { type: Number, default: 1 },
})

const expanded = ref(false)
</script>

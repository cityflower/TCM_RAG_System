<template>
  <div class="h-full flex flex-col bg-white border-l border-tcm-100">
    <!-- 面板标题 -->
    <div class="flex items-center gap-3 px-4 py-4 border-b border-tcm-100 bg-gradient-to-r from-tcm-50 to-white flex-shrink-0">
      <div class="w-8 h-8 rounded-lg bg-tcm-100 flex items-center justify-center">
        <svg class="w-4 h-4 text-tcm-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-bold text-tcm-800">知识溯源</h3>
        <p class="text-xs text-tcm-500">回答参考依据</p>
      </div>

      <!-- 来源数量徽章 -->
      <div v-if="totalCount > 0" class="ml-auto">
        <span class="text-xs bg-tcm-100 text-tcm-700 px-2 py-0.5 rounded-full font-medium">
          {{ totalCount }} 条来源
        </span>
      </div>
    </div>

    <!-- 内容区（可滚动） -->
    <div class="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-4">

      <!-- 空状态 -->
      <div v-if="totalCount === 0 && !isLoading" class="flex flex-col items-center justify-center h-40 gap-3 text-center">
        <div class="w-12 h-12 rounded-full bg-tcm-50 flex items-center justify-center">
          <svg class="w-6 h-6 text-tcm-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <p class="text-xs text-gray-400 leading-relaxed max-w-36">
          发起问答后，系统检索到的参考依据将在此显示
        </p>
      </div>

      <!-- Loading 占位 -->
      <div v-if="isLoading && totalCount === 0" class="space-y-3">
        <div v-for="n in 3" :key="n" class="animate-pulse space-y-2">
          <div class="h-3 bg-tcm-100 rounded w-1/3"></div>
          <div class="h-3 bg-gray-100 rounded w-full"></div>
          <div class="h-3 bg-gray-100 rounded w-5/6"></div>
          <div class="h-3 bg-gray-100 rounded w-4/6"></div>
        </div>
      </div>

      <!-- 文本依据区 -->
      <section v-if="textChunks.length > 0">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold text-tcm-700 uppercase tracking-wide">📖 文献依据</span>
          <span class="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-md">{{ textChunks.length }}</span>
        </div>
        <div class="space-y-2.5">
          <TextChunkCard
            v-for="(chunk, i) in textChunks"
            :key="i"
            :chunk="chunk"
            :index="i + 1"
          />
        </div>
      </section>

      <!-- 图像依据区 -->
      <section v-if="imageResults.length > 0">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold text-tcm-700 uppercase tracking-wide">🌿 草药图像</span>
          <span class="text-xs bg-green-50 text-green-600 px-1.5 py-0.5 rounded-md">{{ imageResults.length }}</span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <ImageResultCard
            v-for="(img, i) in imageResults"
            :key="i"
            :item="img"
          />
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TextChunkCard from './TextChunkCard.vue'
import ImageResultCard from './ImageResultCard.vue'

const props = defineProps({
  textChunks:   { type: Array, default: () => [] },
  imageResults: { type: Array, default: () => [] },
  isLoading:    { type: Boolean, default: false },
})

const totalCount = computed(() => props.textChunks.length + props.imageResults.length)
</script>

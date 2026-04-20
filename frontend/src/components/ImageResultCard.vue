<template>
  <!-- 草药图片结果卡片 -->
  <div class="bg-white border border-gray-100 rounded-xl overflow-hidden hover:border-tcm-300 hover:shadow-md transition-all duration-200 animate-fade-in">
    <!-- 图片 -->
    <div class="relative aspect-square bg-tcm-50 overflow-hidden">
      <img
        v-if="item.image_url || item.thumbnail"
        :src="item.image_url || item.thumbnail"
        :alt="item.name || '草药图片'"
        class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
      />
      <!-- 无图占位 -->
      <div v-else class="w-full h-full flex items-center justify-center text-4xl">🌿</div>
      <!-- 相关度角标 -->
      <div v-if="item.score" class="absolute top-1.5 right-1.5 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded-md backdrop-blur-sm">
        {{ (item.score * 100).toFixed(0) }}%
      </div>
    </div>

    <!-- 元数据 -->
    <div class="p-2.5">
      <h4 class="text-xs font-bold text-tcm-800 truncate mb-1">{{ item.name || '未知草药' }}</h4>
      <!-- 性味归经 -->
      <div v-if="item.properties" class="flex flex-wrap gap-1">
        <span
          v-for="tag in propertiesTags"
          :key="tag"
          class="text-xs bg-tcm-50 text-tcm-600 border border-tcm-100 px-1.5 py-0.5 rounded-md leading-none"
        >{{ tag }}</span>
      </div>
      <p v-if="item.meridian" class="text-xs text-gray-400 mt-1 truncate">归经：{{ item.meridian }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

const propertiesTags = computed(() => {
  if (!props.item.properties) return []
  // 支持字符串 "辛温" 或数组 ["辛", "温"]
  if (Array.isArray(props.item.properties)) return props.item.properties
  return props.item.properties.split(/[，,、\s]+/).filter(Boolean)
})
</script>

<template>
  <!-- 草药图片结果卡片 -->
  <div class="image-result-card">
    <!-- 图片 -->
    <div class="image-result-media">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="title"
      />
      <!-- 无图占位 -->
      <div v-else class="image-result-placeholder">🌿</div>
      <!-- 相关度角标 -->
      <div v-if="displayScore !== null" class="image-result-score">
        {{ (displayScore * 100).toFixed(0) }}%
      </div>
    </div>

    <!-- 元数据 -->
    <div class="image-result-body">
      <h4>{{ title }}</h4>
      <p v-if="item.source" class="image-result-source">{{ item.source }}</p>

      <div v-if="propertiesTags.length" class="image-result-tags">
        <span
          v-for="tag in propertiesTags"
          :key="tag"
        >{{ tag }}</span>
      </div>

      <p v-if="item.effect" class="image-result-line">功效：{{ item.effect }}</p>
      <p v-else-if="item.visual_features" class="image-result-line">特征：{{ item.visual_features }}</p>
      <p v-else-if="item.content" class="image-result-line">{{ item.content }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

const imageUrl = computed(() => props.item.image_url || props.item.thumbnail || '')

const title = computed(() => {
  if (props.item.name) return props.item.name
  const sourceTitle = (props.item.source || '').split('/').pop()
  if (sourceTitle) return sourceTitle
  const match = (props.item.content || '').match(/(?:药材名称|中药名称|名称)[:：]\s*([^\n，,。；;]+)/)
  return match ? match[1].trim() : '草药图片'
})

const displayScore = computed(() => {
  const value = props.item.score ?? props.item.rerank_score ?? props.item.retrieval_score
  if (value === undefined || value === null || value === '') return null
  const num = Number(value)
  if (Number.isNaN(num)) return null
  return Math.max(0, Math.min(num, 1))
})

const propertiesTags = computed(() => {
  if (!props.item.properties) return []
  // 支持字符串 "辛温" 或数组 ["辛", "温"]
  if (Array.isArray(props.item.properties)) return props.item.properties
  return props.item.properties.split(/[，,、\s]+/).filter(Boolean)
})
</script>

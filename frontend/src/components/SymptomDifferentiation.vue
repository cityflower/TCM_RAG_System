<template>
  <div class="diff-container">
    <header class="diff-header">
      <div>
        <h2 class="diff-title">症状辨证</h2>
        <p class="diff-subtitle">根据症状描述检索可能相关的中医证型</p>
      </div>
      <div class="diff-status" :class="{ 'diff-status--loading': loading }">
        <span></span>
        {{ loading ? '检索中' : '就绪' }}
      </div>
    </header>

    <main class="diff-main">
      <section class="diff-query-panel">
        <div class="diff-section-title">症状描述</div>
        <textarea
          v-model="query"
          class="diff-textarea"
          rows="7"
          placeholder="输入症状，如：心烦失眠，耳鸣，腰膝酸软，口干咽燥..."
          @keydown.enter.meta.prevent="handleSearch"
          @keydown.enter.ctrl.prevent="handleSearch"
        ></textarea>

        <div class="diff-examples">
          <button
            v-for="example in examples"
            :key="example"
            class="diff-example-btn"
            @click="useExample(example)"
          >
            {{ example }}
          </button>
        </div>

        <div class="diff-controls">
          <label class="diff-toggle">
            <input v-model="useRerank" type="checkbox" />
            <span>启用重排</span>
          </label>

          <label class="diff-limit">
            <span>返回</span>
            <select v-model.number="limit">
              <option :value="3">3 条</option>
              <option :value="5">5 条</option>
              <option :value="8">8 条</option>
            </select>
          </label>
        </div>

        <button
          class="diff-search-btn"
          :disabled="loading || !query.trim()"
          @click="handleSearch"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 110-15 7.5 7.5 0 010 15z" />
          </svg>
          开始辨证
        </button>
      </section>

      <section class="diff-results">
        <div class="diff-results-head">
          <div>
            <h3>候选证型</h3>
            <p v-if="lastQuery">“{{ lastQuery }}”</p>
          </div>
          <span v-if="results.length" class="diff-count">{{ results.length }} 条</span>
        </div>

        <div v-if="loading" class="diff-loading">
          <div v-for="n in 4" :key="n" class="diff-skeleton">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>

        <div v-else-if="error" class="diff-empty diff-empty--error">
          {{ error }}
        </div>

        <div v-else-if="!results.length" class="diff-empty">
          输入症状后，将在这里显示最相关的证型依据
        </div>

        <div v-else class="diff-result-list">
          <article v-for="(item, idx) in results" :key="item.id || idx" class="diff-result-card">
            <div class="diff-card-top">
              <div>
                <div class="diff-rank">#{{ idx + 1 }}</div>
                <h4>{{ getTitle(item) }}</h4>
              </div>
              <div class="diff-score">
                <strong>{{ formatScore(item.score) }}</strong>
                <span>{{ item.rerank_status === 'ok' ? '重排' : '召回' }}</span>
              </div>
            </div>

            <div class="diff-scorebar">
              <span :style="{ width: `${Math.round(normalizeScore(item.score) * 100)}%` }"></span>
            </div>

            <p class="diff-source">{{ item.source || '未知来源' }}</p>
            <p class="diff-content">{{ item.content }}</p>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchKnowledge } from '@/api/search.js'
import { readStorage, writeStorage } from '@/utils/storage.js'

const examples = [
  '心烦失眠，耳鸣，腰膝酸软',
  '咳嗽痰黄，胸闷气喘，舌红苔黄腻',
  '小便黄赤，肛门灼热，大便急迫',
  '食欲不振，腹胀便溏，神疲乏力',
]

const STORAGE_KEY = 'tcm.differentiation.state.v1'
const cachedState = readStorage(STORAGE_KEY, {})

const query = ref(cachedState.query || '')
const lastQuery = ref(cachedState.lastQuery || '')
const results = ref(Array.isArray(cachedState.results) ? cachedState.results : [])
const loading = ref(false)
const error = ref(cachedState.error || '')
const useRerank = ref(cachedState.useRerank ?? true)
const limit = ref(cachedState.limit || 5)

watch(
  [query, lastQuery, results, error, useRerank, limit],
  () => {
    writeStorage(STORAGE_KEY, {
      query: query.value,
      lastQuery: lastQuery.value,
      results: results.value,
      error: error.value,
      useRerank: useRerank.value,
      limit: limit.value,
    })
  },
  { deep: true }
)

function useExample(text) {
  query.value = text
  handleSearch()
}

async function handleSearch() {
  const text = query.value.trim()
  if (!text || loading.value) return

  loading.value = true
  error.value = ''
  lastQuery.value = text

  try {
    const data = await searchKnowledge({
      query: text,
      limit: limit.value,
      recallLimit: Math.max(10, limit.value * 2),
      rerank: useRerank.value,
    })
    results.value = data.results || []
  } catch (err) {
    results.value = []
    error.value = `检索失败：${err.message}`
  } finally {
    loading.value = false
  }
}

function normalizeScore(score) {
  const value = Number(score)
  if (Number.isNaN(value)) return 0
  return Math.max(0, Math.min(value, 1))
}

function formatScore(score) {
  return `${Math.round(normalizeScore(score) * 100)}%`
}

function getTitle(item) {
  const sourceTitle = (item.source || '').split('/').pop()
  if (sourceTitle) return sourceTitle

  const match = (item.content || '').match(/证型名称[:：]\s*([^\n]+)/)
  return match ? match[1] : '候选证型'
}
</script>

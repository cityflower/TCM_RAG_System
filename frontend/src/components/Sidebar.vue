<template>
  <aside class="sidebar">
    <!-- Logo 区 -->
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">
        <span>🌿</span>
      </div>
      <div class="sidebar-logo-text">
        <h1>本草智询</h1>
        <p>TCM RAG System</p>
      </div>
    </div>

    <!-- 新建问诊 -->
    <button class="sidebar-new-btn" @click="$emit('new-chat')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      新建问诊
    </button>

    <!-- 导航切换 -->
    <nav class="sidebar-nav">
      <button
        class="sidebar-nav-item"
        :class="{ 'sidebar-nav-item--active': activeView === 'chat' }"
        @click="$emit('switch-view', 'chat')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span>中医问诊</span>
      </button>
      <button
        class="sidebar-nav-item"
        :class="{ 'sidebar-nav-item--active': activeView === 'differentiation' }"
        @click="$emit('switch-view', 'differentiation')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12l2 2 4-4M7 4h10a2 2 0 012 2v14l-4-2-4 2-4-2-4 2V6a2 2 0 012-2z" />
        </svg>
        <span>症状辨证</span>
      </button>
      <button
        class="sidebar-nav-item"
        :class="{ 'sidebar-nav-item--active': activeView === 'knowledge' }"
        @click="$emit('switch-view', 'knowledge')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-3-3v6" />
        </svg>
        <span>知识库管理</span>
      </button>
    </nav>

    <!-- 历史会话区（预留） -->
    <div class="sidebar-history">
      <div class="sidebar-history-header">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">历史会话</span>
      </div>
      <div class="sidebar-history-list scrollbar-thin">
        <div v-if="chatHistory.length === 0" class="sidebar-history-empty">
          <svg class="w-5 h-5 text-gray-300 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-xs text-gray-300">暂无历史记录</p>
          <p class="text-xs text-gray-300 mt-0.5">开始问诊后会自动保存</p>
        </div>

        <div v-else class="sidebar-history-items">
          <div
            v-for="item in chatHistory"
            :key="item.id"
            class="sidebar-history-item"
            :class="{ 'sidebar-history-item--active': item.id === activeSessionId }"
          >
            <button class="sidebar-history-main" @click="$emit('select-chat', item.id)">
              <span class="sidebar-history-title">{{ item.title }}</span>
              <span class="sidebar-history-meta">
                <span v-if="item.isLoading" class="sidebar-history-dot"></span>
                {{ item.isLoading ? '生成中' : formatHistoryTime(item.updatedAt) }}
              </span>
            </button>
            <button
              class="sidebar-history-delete"
              title="删除会话"
              @click.stop="$emit('delete-chat', item.id)"
            >
              ×
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部用户区（预留） -->
    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="sidebar-avatar">👤</div>
        <div class="sidebar-user-info">
          <span class="text-xs font-medium text-gray-300">访客用户</span>
          <span class="text-xs text-gray-500">登录功能即将上线</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  activeView: { type: String, default: 'chat' },
  activeSessionId: { type: String, default: '' },
  chatHistory: { type: Array, default: () => [] },
})

defineEmits(['switch-view', 'new-chat', 'select-chat', 'delete-chat'])

function formatHistoryTime(value) {
  if (!value) return ''
  const date = new Date(value)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  if (isToday) {
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

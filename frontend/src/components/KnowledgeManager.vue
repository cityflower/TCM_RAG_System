<template>
  <div class="km-container">
    <!-- 顶部工具栏 -->
    <div class="km-toolbar">
      <div class="km-toolbar-left">
        <div class="km-toolbar-icon">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-3-3v6" />
          </svg>
        </div>
        <div>
          <h2 class="km-toolbar-title">知识库管理</h2>
          <p class="km-toolbar-sub">Milvus 向量数据库可视化管理 · 共 {{ totalCount }} 条记录</p>
        </div>
      </div>
      <button class="km-add-btn" @click="openAddModal">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        录入新知识
      </button>
    </div>

    <!-- 数据表格 -->
    <div class="km-table-wrapper scrollbar-thin">
      <!-- 加载状态 -->
      <div v-if="loading" class="km-loading">
        <div class="km-loading-spinner"></div>
        <p>正在从 Milvus 藏书阁中检索数据...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="list.length === 0" class="km-empty">
        <div class="km-empty-icon">📚</div>
        <h3>知识库暂无数据</h3>
        <p>点击右上角「录入新知识」开始构建你的中医药知识图谱</p>
      </div>

      <!-- 数据列表 -->
      <table v-else class="km-table">
        <thead>
          <tr>
            <th class="km-th" style="width: 60px">#</th>
            <th class="km-th" style="width: 80px">类型</th>
            <th class="km-th">内容摘要</th>
            <th class="km-th" style="width: 140px">出处</th>
            <th class="km-th" style="width: 80px">图片</th>
            <th class="km-th" style="width: 130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in list" :key="item.id" class="km-row">
            <td class="km-td km-td-index">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
            <td class="km-td">
              <span class="km-badge" :class="item.data_type === 'image' ? 'km-badge--image' : 'km-badge--text'">
                {{ item.data_type === 'image' ? '📷 图文' : '📝 文本' }}
              </span>
            </td>
            <td class="km-td km-td-content" :title="item.content">
              {{ truncate(item.content, 120) }}
            </td>
            <td class="km-td km-td-source">{{ item.source || '未知' }}</td>
            <td class="km-td">
              <img
                v-if="getImageUrl(item)"
                :src="getImageUrl(item)"
                class="km-thumb"
                alt="缩略图"
                @error="(e) => e.target.style.display = 'none'"
              />
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
            <td class="km-td">
              <div class="km-actions">
                <button class="km-action-btn km-action-btn--edit" @click="openEditModal(item)" title="编辑">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  编辑
                </button>
                <button class="km-action-btn km-action-btn--delete" @click="confirmDelete(item)" title="删除">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页栏 -->
    <div v-if="totalPages > 1" class="km-pagination">
      <div class="km-pagination-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ totalCount }} 条
      </div>
      <div class="km-pagination-btns">
        <button
          class="km-page-btn"
          :disabled="currentPage <= 1"
          @click="goPage(currentPage - 1)"
        >‹ 上一页</button>

        <template v-for="p in visiblePages" :key="p">
          <button
            v-if="p === '...'"
            class="km-page-btn km-page-ellipsis"
            disabled
          >...</button>
          <button
            v-else
            class="km-page-btn"
            :class="{ 'km-page-btn--active': p === currentPage }"
            @click="goPage(p)"
          >{{ p }}</button>
        </template>

        <button
          class="km-page-btn"
          :disabled="currentPage >= totalPages"
          @click="goPage(currentPage + 1)"
        >下一页 ›</button>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <KnowledgeFormModal
      :visible="formModalVisible"
      :is-edit="isEditMode"
      :edit-data="editTarget"
      @submit="handleFormSubmit"
      @cancel="formModalVisible = false"
    />

    <!-- 删除确认弹窗 -->
    <ConfirmModal
      :visible="deleteModalVisible"
      title="⚠️ 确认删除"
      :message="`确定要永久删除这条知识记录吗？\n\n「${deleteTarget?.content?.slice(0, 50) || ''}...」\n\n此操作不可撤销，向量数据将从 Milvus 中彻底抹除。`"
      confirm-text="确认删除"
      type="danger"
      @confirm="handleDelete"
      @cancel="deleteModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchKnowledgeList, createKnowledge, deleteKnowledge, updateKnowledge } from '@/api/knowledge.js'
import KnowledgeFormModal from './KnowledgeFormModal.vue'
import ConfirmModal from './ConfirmModal.vue'

// 数据状态
const list = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)

// 弹窗状态
const formModalVisible = ref(false)
const isEditMode = ref(false)
const editTarget = ref({})
const deleteModalVisible = ref(false)
const deleteTarget = ref(null)

// 计算属性
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages = []
  pages.push(1)
  if (cur > 3) pages.push('...')
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) {
    pages.push(i)
  }
  if (cur < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const res = await fetchKnowledgeList(currentPage.value, pageSize.value)
    list.value = res.data || []
    totalCount.value = res.total || 0
  } catch (e) {
    console.error('加载知识库失败:', e)
    list.value = []
  } finally {
    loading.value = false
  }
}

function goPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadData()
}

// 工具函数
function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function getImageUrl(item) {
  if (item.metadata && item.metadata.image_url) return item.metadata.image_url
  return null
}

// 新增
function openAddModal() {
  isEditMode.value = false
  editTarget.value = {}
  formModalVisible.value = true
}

// 编辑
function openEditModal(item) {
  isEditMode.value = true
  editTarget.value = { id: item.id, content: item.content, source: item.source }
  formModalVisible.value = true
}

// 表单提交
async function handleFormSubmit(data) {
  try {
    if (isEditMode.value) {
      await updateKnowledge(data.id, { content: data.content, source: data.source })
    } else {
      await createKnowledge({ content: data.content, source: data.source, image: data.image })
    }
    formModalVisible.value = false
    // 💡 延迟 800ms 等待后端 Milvus 向量库把数据落盘刷入后再去查询，否则会查不到刚插入的数据
    await new Promise(resolve => setTimeout(resolve, 800))
    await loadData()
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

// 删除
function confirmDelete(item) {
  deleteTarget.value = item
  deleteModalVisible.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  try {
    await deleteKnowledge(deleteTarget.value.id)
    deleteModalVisible.value = false
    deleteTarget.value = null
    // 如果当前页删完了，自动回退一页
    if (list.value.length === 1 && currentPage.value > 1) {
      currentPage.value--
    }
    // 💡 延迟 800ms 等待数据库把旧数据彻底抹除
    await new Promise(resolve => setTimeout(resolve, 800))
    await loadData()
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

onMounted(loadData)
</script>

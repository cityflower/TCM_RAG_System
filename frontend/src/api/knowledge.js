/**
 * 知识库管理 API
 * 对接后端 FastAPI 的知识库 CRUD 接口
 */

const API_BASE = '/api'

/**
 * 分页查询知识库列表
 * @param {number} page - 当前页码
 * @param {number} pageSize - 每页条数
 * @returns {Promise<{total: number, page: number, page_size: number, data: Array}>}
 */
export async function fetchKnowledgeList(page = 1, pageSize = 20) {
  const res = await fetch(`${API_BASE}/knowledge_list?page=${page}&page_size=${pageSize}`)
  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
  return res.json()
}

/**
 * 新增知识条目（图文）
 * @param {Object} params
 * @param {string} params.content - 文字内容
 * @param {string} params.source - 出处
 * @param {File|null} params.image - 可选图片文件
 */
export async function createKnowledge({ content, source, image = null }) {
  const formData = new FormData()
  formData.append('content', content)
  formData.append('source', source)
  if (image) formData.append('image', image)

  const res = await fetch(`${API_BASE}/upload_knowledge`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
  return res.json()
}

/**
 * 删除一条知识记录
 * @param {string} id - 主键 ID
 */
export async function deleteKnowledge(id) {
  const res = await fetch(`${API_BASE}/knowledge/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
  return res.json()
}

/**
 * 更新一条知识记录
 * @param {string} id - 主键 ID
 * @param {Object} params
 * @param {string} params.content - 新的文字内容
 * @param {string} params.source - 新的出处
 */
export async function updateKnowledge(id, { content, source }) {
  const formData = new FormData()
  formData.append('content', content)
  formData.append('source', source)

  const res = await fetch(`${API_BASE}/knowledge/${id}`, {
    method: 'PUT',
    body: formData,
  })
  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
  return res.json()
}

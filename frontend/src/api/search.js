/**
 * 症状辨证检索 API
 * 只检索知识库，不等待大模型生成回答。
 */

const API_BASE = '/api'

export async function searchKnowledge({ query, limit = 5, recallLimit = 10, rerank = true }) {
  const params = new URLSearchParams({
    query,
    limit: String(limit),
    recall_limit: String(recallLimit),
    rerank: String(rerank),
  })

  const res = await fetch(`${API_BASE}/search?${params.toString()}`)
  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
  return res.json()
}

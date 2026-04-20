/**
 * 图片上传 API
 * 调用后端 FastAPI 的 /api/upload/image 端点
 *
 * @param {File} file - 用户上传的图片文件
 * @returns {Promise<{image_base64: string, filename: string}>}
 */
export async function uploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/upload/image', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: '上传失败' }))
    throw new Error(err.detail || '图片上传失败')
  }

  return response.json()
}

/**
 * 将本地图片 File 转为 base64 字符串（本地转换，无需上传）
 * @param {File} file
 * @returns {Promise<string>} base64 字符串（含 data URL 前缀）
 */
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

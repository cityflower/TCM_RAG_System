export function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (err) {
    console.warn(`读取本地缓存失败：${key}`, err)
    return fallback
  }
}

export function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (err) {
    console.warn(`写入本地缓存失败：${key}`, err)
    return false
  }
}

export function removeStorage(key) {
  try {
    localStorage.removeItem(key)
  } catch (err) {
    console.warn(`删除本地缓存失败：${key}`, err)
  }
}

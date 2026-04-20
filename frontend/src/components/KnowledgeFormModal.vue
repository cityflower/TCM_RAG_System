<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
        <div class="knowledge-form-box">
          <!-- 标题栏 -->
          <div class="form-header">
            <h3 class="form-title">{{ isEdit ? '✏️ 编辑知识条目' : '📥 录入新知识' }}</h3>
            <button class="form-close" @click="handleCancel" title="关闭">✕</button>
          </div>

          <!-- 表单内容 -->
          <div class="form-body">
            <!-- 文字内容 -->
            <div class="form-group">
              <label class="form-label">📝 文字内容 <span class="text-red-400">*</span></label>
              <textarea
                v-model="formData.content"
                class="form-textarea"
                rows="6"
                placeholder="请输入中医药知识内容，如药材描述、古籍段落等..."
              ></textarea>
            </div>

            <!-- 出处 -->
            <div class="form-group">
              <label class="form-label">📖 出处来源</label>
              <input
                v-model="formData.source"
                class="form-input"
                type="text"
                placeholder="如：《本草纲目》、《神农本草经》..."
              />
            </div>

            <!-- 图片上传 (仅新增模式) -->
            <div v-if="!isEdit" class="form-group">
              <label class="form-label">🖼️ 附带图片（可选）</label>
              <div class="form-upload-area" @click="$refs.fileInput.click()">
                <div v-if="imagePreview" class="form-upload-preview">
                  <img :src="imagePreview" alt="预览" />
                  <button class="form-upload-remove" @click.stop="removeImage">✕</button>
                </div>
                <div v-else class="form-upload-placeholder">
                  <svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p class="text-xs text-gray-400 mt-1">点击选择草药图片</p>
                </div>
              </div>
              <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange" />
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="form-footer">
            <button class="confirm-btn confirm-btn--cancel" @click="handleCancel" :disabled="submitting">取消</button>
            <button
              class="confirm-btn confirm-btn--primary"
              @click="handleSubmit"
              :disabled="!formData.content.trim() || submitting"
            >
              <span v-if="submitting" class="form-spinner"></span>
              {{ submitting ? '提交中...' : (isEdit ? '保存修改' : '录入知识库') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible:  { type: Boolean, default: false },
  isEdit:   { type: Boolean, default: false },
  editData: { type: Object, default: () => ({}) },  // { id, content, source }
})

const emit = defineEmits(['submit', 'cancel'])

const formData = ref({ content: '', source: '', image: null })
const imagePreview = ref(null)
const submitting = ref(false)

// 编辑模式下填充旧数据
watch(() => props.visible, (val) => {
  if (val && props.isEdit && props.editData) {
    formData.value.content = props.editData.content || ''
    formData.value.source = props.editData.source || ''
    formData.value.image = null
    imagePreview.value = null
  } else if (val && !props.isEdit) {
    formData.value = { content: '', source: '', image: null }
    imagePreview.value = null
  }
})

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  formData.value.image = file
  const reader = new FileReader()
  reader.onload = (ev) => { imagePreview.value = ev.target.result }
  reader.readAsDataURL(file)
}

function removeImage() {
  formData.value.image = null
  imagePreview.value = null
}

async function handleSubmit() {
  if (!formData.value.content.trim()) return
  submitting.value = true
  try {
    await emit('submit', {
      id: props.editData?.id,
      content: formData.value.content.trim(),
      source: formData.value.source.trim() || '未知古籍',
      image: formData.value.image,
    })
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  if (!submitting.value) emit('cancel')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
        <div class="confirm-box">
          <!-- 图标 -->
          <div class="confirm-icon" :class="type === 'danger' ? 'confirm-icon--danger' : 'confirm-icon--info'">
            <svg v-if="type === 'danger'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h3 class="confirm-title">{{ title }}</h3>
          <p class="confirm-message">{{ message }}</p>

          <div class="confirm-actions">
            <button class="confirm-btn confirm-btn--cancel" @click="handleCancel">取消</button>
            <button
              class="confirm-btn"
              :class="type === 'danger' ? 'confirm-btn--danger' : 'confirm-btn--primary'"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  visible:     { type: Boolean, default: false },
  title:       { type: String, default: '确认操作' },
  message:     { type: String, default: '确定要执行此操作吗？' },
  confirmText: { type: String, default: '确定' },
  type:        { type: String, default: 'danger' }, // 'danger' | 'info'
})

const emit = defineEmits(['confirm', 'cancel'])

function handleConfirm() { emit('confirm') }
function handleCancel()  { emit('cancel') }
</script>

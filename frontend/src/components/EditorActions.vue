<template>
  <div class="editor-actions">
    <button v-if="showSave" class="ea-save" :disabled="!canSave" @click="$emit('save')">
      {{ saveLabel }}
    </button>
    <button v-if="deletable" class="ea-delete" :class="{ danger: pendingDelete }" @click="$emit('delete')">
      {{ pendingDelete ? cancelDeleteLabel : deleteLabel }}
    </button>
  </div>
</template>

<script setup>
/**
 * Блок действий редактора («Сохранить» / «Удалить») — переиспользуется на
 * страницах конфигуратора. «Удалить» — двухшаговое: при pendingDelete
 * кнопка становится «Отменить удаление» и подсвечивается красным.
 */
defineProps({
  showSave: { type: Boolean, default: true },
  canSave: { type: Boolean, default: true },
  saveLabel: { type: String, default: 'Сохранить' },
  deletable: { type: Boolean, default: true },
  deleteLabel: { type: String, default: 'Удалить' },
  cancelDeleteLabel: { type: String, default: 'Отменить удаление' },
  pendingDelete: { type: Boolean, default: false },
})
defineEmits(['save', 'delete'])
</script>

<style scoped>
.editor-actions { display: flex; gap: 8px; margin-left: auto; }
.editor-actions button {
  padding: 6px 14px; cursor: pointer; border-radius: 4px; font-size: 13px;
  border: 1px solid #ccc; background: #fff;
}
.editor-actions .ea-save { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.editor-actions .ea-save:disabled { background: #9db8d4; border-color: #9db8d4; cursor: not-allowed; }
.editor-actions .ea-delete.danger { background: #c62828; color: #fff; border-color: #c62828; }
</style>

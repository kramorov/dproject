<!-- shared/components/PermissionMatrix.vue -->
<template>
  <div class="perm-matrix" v-if="sections.length">
    <table class="matrix-table">
      <thead>
        <tr>
          <th class="col-label"></th>
          <th
            v-for="s in sections"
            :key="s.code"
            :class="{ 'col-disabled': !isSectionAvailable(s.code) }"
            :title="s.name"
          >
            <span class="col-code">{{ s.code }}</span>
          </th>
        </tr>
        <tr class="org-row" v-if="orgSections && orgSections.length">
          <th class="col-label">Организация</th>
          <td
            v-for="s in sections"
            :key="'org-'+s.code"
            :class="{ 'cell-org-on': orgSections.includes(s.code), 'cell-org-off': !orgSections.includes(s.code) }"
          ></td>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, ri) in rows"
          :key="row[rowIdKey] ?? ri"
          :class="{ 'row-inactive': row.is_active === false }"
        >
          <th class="col-label">
            <span class="row-name">{{ row[rowLabelKey] || row.code || row.login }}</span>
            <span v-if="row.is_default" class="badge-default">по умолч.</span>
            <span v-if="row.user_count !== undefined" class="badge-count">{{ row.user_count }}</span>
          </th>
          <td
            v-for="s in sections"
            :key="s.code"
            :class="{
              'cell-disabled': !isSectionAvailable(s.code),
              'cell-checked': isChecked(row, s.code),
              'cell-inherited': isInherited(row, s.code),
            }"
          >
            <input
              v-if="!readonly && isSectionAvailable(s.code)"
              type="checkbox"
              :checked="isChecked(row, s.code)"
              @change="toggle(row, s.code)"
            />
            <span v-else-if="isChecked(row, s.code)" class="mark-check">✓</span>
            <span v-else-if="isInherited(row, s.code)" class="mark-inherited">◉</span>
            <span v-else class="mark-empty">—</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!readonly" class="hint">◉ = унаследовано от роли. Отмеченные индивидуально переопределяют наследование.</div>
  </div>
  <div v-else class="empty">Нет данных</div>
</template>

<script setup>
const props = defineProps({
  /** Columns: [{ code, name }] */
  sections: { type: Array, default: () => [] },
  /** Data rows */
  rows: { type: Array, default: () => [] },
  /** Key in row for the row label (name) */
  rowLabelKey: { type: String, default: 'name' },
  /** Key in row for unique id */
  rowIdKey: { type: String, default: 'id' },
  /** Key in row for checked section codes */
  checkedKey: { type: String, default: 'section_permissions' },
  /** Key in row for inherited section codes (not directly checked, but from roles) */
  inheritedKey: { type: String, default: null },
  /** Org-level ceiling: codes */
  orgSections: { type: Array, default: null },
  /** Read-only mode */
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle'])

function isSectionAvailable(code) {
  if (!props.orgSections || !props.orgSections.length) return true
  return props.orgSections.includes(code)
}

function isChecked(row, code) {
  const checked = row[props.checkedKey]
  return Array.isArray(checked) && checked.includes(code)
}

function isInherited(row, code) {
  if (!props.inheritedKey || isChecked(row, code)) return false
  const inh = row[props.inheritedKey]
  return Array.isArray(inh) && inh.includes(code)
}

function toggle(row, code) {
  emit('toggle', row, code)
}
</script>

<style scoped>
.perm-matrix {
  overflow-x: auto;
  font-size: 13px;
}
.matrix-table {
  border-collapse: collapse;
  width: 100%;
  min-width: 600px;
}
.matrix-table th, .matrix-table td {
  border: 1px solid var(--cat-border-light, #e0dcd6);
  padding: 5px 8px;
  text-align: center;
  white-space: nowrap;
}
.col-label {
  text-align: left !important;
  min-width: 160px;
  background: var(--cat-bg, #f5f2ed);
  position: sticky;
  left: 0;
  z-index: 1;
}
.col-code {
  font-size: 11px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  max-height: 80px;
  display: inline-block;
}
.col-disabled {
  background: #f0f0f0;
  color: var(--cat-muted-light, #a0a0a0);
}
.row-inactive {
  opacity: 0.5;
}
.row-name {
  font-weight: 500;
}
.badge-default {
  font-size: 10px;
  background: var(--cat-primary-light, #e8f0f8);
  color: var(--cat-primary, #5785b5);
  padding: 1px 5px;
  border-radius: 3px;
  margin-left: 4px;
}
.badge-count {
  font-size: 10px;
  color: var(--cat-muted, #7a7a7a);
  margin-left: 4px;
}
.cell-disabled {
  background: #f8f8f8;
}
.cell-checked {
  background: #e8f5e9;
}
.cell-inherited {
  background: #fff8e1;
}
.cell-org-on {
  background: #e3f2fd;
}
.cell-org-off {
  background: #f5f5f5;
}
.mark-check { color: #2e7d32; font-weight: bold; }
.mark-inherited { color: #f9a825; }
.mark-empty { color: var(--cat-muted-light, #ccc); }

.org-row td {
  height: 12px;
  padding: 2px;
}
.org-row th {
  font-size: 11px;
  color: var(--cat-muted, #7a7a7a);
}

input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}
.hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--cat-muted, #7a7a7a);
}
.empty {
  padding: 40px;
  text-align: center;
  color: var(--cat-muted-light, #a0a0a0);
}
</style>

<template>
  <div class="storage-page">
    <h1>{{ t('storage.title') }}</h1>
    <p class="lead">{{ t('storage.lead') }}</p>

    <!-- Последняя/активная задача: прогресс + журнал + результат -->
    <section v-if="displayJob" class="panel job-panel">
      <h2>
        {{ t('storage.job.title') }}
        <span class="badge" :class="'badge--' + displayJob.state">
          {{ t('storage.job.state.' + displayJob.state) }}
        </span>
        <span v-if="displayJob.kind" class="badge badge--kind">{{ t('storage.job.kind.' + displayJob.kind) }}</span>
      </h2>

      <div class="progress">
        <div class="progress__fill" :style="{ width: (displayJob.percent || 0) + '%' }"></div>
        <span class="progress__label">{{ displayJob.percent || 0 }}%</span>
      </div>

      <div class="job-meta">
        <span>{{ t('storage.job.phase.' + displayJob.phase) }}</span>
        <span v-if="displayJob.total">{{ t('storage.job.progress', { current: displayJob.current, total: displayJob.total }) }}</span>
        <span v-if="displayJob.phase === 'downloading'">{{ t('storage.job.downloaded') }}: {{ displayJob.processed }}</span>
        <span v-else-if="displayJob.phase === 'uploading'">{{ t('storage.job.uploaded') }}: {{ displayJob.processed }}</span>
        <span v-if="displayJob.skipped">{{ t('storage.job.skipped') }}: {{ displayJob.skipped }}</span>
        <span v-if="displayJob.failed" class="job-failed">{{ t('storage.job.failed') }}: {{ displayJob.failed }}</span>
        <span v-if="displayJob.bytes">{{ t('storage.job.totalSize') }}: {{ fmtSize(displayJob.bytes) }}</span>
        <span v-if="displayJob.speed">{{ t('storage.job.speed') }}: {{ fmtSize(displayJob.speed) }}/c</span>
      </div>

      <pre v-if="displayJob.logs && displayJob.logs.length" class="log">{{ displayJob.logs.slice(-40).join('\n') }}</pre>
      <p v-if="displayJob.error" class="error-text">{{ t('storage.job.error') }}{{ displayJob.error }}</p>

      <div class="row">
        <button v-if="displayJob.state === 'running'" class="btn btn--danger" @click="cancelJob">
          {{ t('storage.job.cancel') }}
        </button>
      </div>

      <div v-if="displayJob.state === 'done' && displayJob.result" class="dry-run-result">
        <h3>{{ t(resultTitleKey) }}</h3>
        <p v-if="displayJob.result.total_objects !== undefined">
          {{ t('storage.job.objects') }}: <b>{{ displayJob.result.total_objects }}</b> ·
          {{ t('storage.job.totalSize') }}: <b>{{ fmtSize(displayJob.result.total_size_bytes) }}</b> ·
          {{ t('storage.job.downloaded') }}: {{ displayJob.result.downloaded }} ·
          {{ t('storage.job.skipped') }}: {{ displayJob.result.skipped }} ·
          {{ t('storage.job.failed') }}: {{ displayJob.result.failed }}
        </p>
        <p v-if="displayJob.result.total !== undefined">
          {{ t('storage.job.objects') }}: <b>{{ displayJob.result.total }}</b> ·
          {{ t('storage.job.uploaded') }}: <b>{{ displayJob.result.uploaded }}</b> ·
          {{ t('storage.job.skipped') }}: {{ displayJob.result.skipped }} ·
          {{ t('storage.job.failed') }}: {{ displayJob.result.failed }} ·
          {{ t('storage.job.totalSize') }}: {{ fmtSize(displayJob.result.bytes) }}
        </p>
        <details v-if="displayJob.result.sample_keys && displayJob.result.sample_keys.length">
          <summary>{{ t('storage.job.sampleKeys') }}</summary>
          <ul class="sample-keys">
            <li v-for="k in displayJob.result.sample_keys" :key="k">{{ k }}</li>
          </ul>
        </details>
      </div>
    </section>

    <!-- Бэкап -->
    <section class="panel">
      <h2>{{ t('storage.backup.title') }}</h2>
      <p class="desc">{{ t('storage.backup.desc') }}</p>
      <div class="row">
        <label class="grow">
          {{ t('storage.prefix.label') }}
          <input v-model="backupPrefix" type="text" :placeholder="t('storage.prefix.placeholder')" />
        </label>
      </div>
      <div class="row">
        <button class="btn btn--primary" :disabled="busy" @click="startBackup(false)">
          {{ t('storage.backup.start') }}
        </button>
        <button class="btn" :disabled="busy" @click="startBackup(true)">
          {{ t('storage.backup.dryrun') }}
        </button>
      </div>
      <p class="hint">{{ t('storage.backup.dryrunDesc') }}</p>
    </section>

    <!-- Восстановление -->
    <section class="panel">
      <h2>{{ t('storage.restore.title') }}</h2>
      <p class="desc">{{ t('storage.restore.desc') }}</p>
      <div class="row">
        <label>
          {{ t('storage.restore.folder') }}
          <select v-model="restoreFolder" :disabled="busy">
            <option value="" disabled>{{ t('storage.restore.choose') }}</option>
            <option v-for="b in backups" :key="b.folder" :value="b.folder">
              {{ b.folder }} ({{ fmtSize(b.total_size_bytes) }})
            </option>
          </select>
        </label>
        <label class="check"><input v-model="restoreOverwrite" type="checkbox" :disabled="busy" /> {{ t('storage.restore.overwrite') }}</label>
        <label class="check"><input v-model="restoreDryRun" type="checkbox" :disabled="busy" /> {{ t('storage.restore.dryrun') }}</label>
      </div>
      <div class="row">
        <button class="btn btn--primary" :disabled="busy || !restoreFolder" @click="startRestore">
          {{ t('storage.restore.start') }}
        </button>
      </div>
      <p class="hint">{{ t('storage.restore.dryrunDesc') }}</p>
    </section>

    <!-- Локальные бэкапы -->
    <section class="panel">
      <h2>{{ t('storage.backups.title') }}</h2>
      <p class="desc">{{ t('storage.backups.desc') }}</p>
      <p v-if="!backups.length" class="hint">{{ t('storage.backups.empty') }}</p>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{{ t('storage.backups.folder') }}</th>
              <th>{{ t('storage.backups.date') }}</th>
              <th class="num">{{ t('storage.backups.objects') }}</th>
              <th class="num">{{ t('storage.backups.size') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in backups" :key="b.folder">
              <td>{{ b.folder }}</td>
              <td>{{ fmtDate(b.backup_date) }}</td>
              <td class="num">{{ b.total_objects }}</td>
              <td class="num">{{ fmtSize(b.total_size_bytes) }}</td>
              <td class="actions">
                <button class="btn btn--small" @click="openManifest(b.folder)">{{ t('storage.backups.manifest') }}</button>
                <button class="btn btn--small" @click="downloadManifest(b.folder)">{{ t('storage.backups.download') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Описания команд -->
    <section class="panel">
      <h2>{{ t('storage.commands.title') }}</h2>
      <dl class="commands">
        <div>
          <dt>{{ t('storage.commands.backup.name') }}</dt>
          <dd>{{ t('storage.commands.backup.desc') }}</dd>
        </div>
        <div>
          <dt>{{ t('storage.commands.dryrun.name') }}</dt>
          <dd>{{ t('storage.commands.dryrun.desc') }}</dd>
        </div>
        <div>
          <dt>{{ t('storage.commands.restore.name') }}</dt>
          <dd>{{ t('storage.commands.restore.desc') }}</dd>
        </div>
        <div>
          <dt>{{ t('storage.commands.restoreDryrun.name') }}</dt>
          <dd>{{ t('storage.commands.restoreDryrun.desc') }}</dd>
        </div>
        <div>
          <dt>{{ t('storage.commands.manifest.name') }}</dt>
          <dd>{{ t('storage.commands.manifest.desc') }}</dd>
        </div>
      </dl>
    </section>

    <!-- Модалка манифеста -->
    <div v-if="manifestView" class="modal-backdrop" @click.self="manifestView = null">
      <div class="modal">
        <div class="modal__head">
          <h3>{{ t('storage.manifest.title', { folder: manifestView.folder }) }}</h3>
          <button class="btn btn--small" @click="manifestView = null">{{ t('storage.manifest.close') }}</button>
        </div>
        <pre class="modal__json">{{ manifestView.json }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import api from '@/shared/api'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

const backups = ref([])
const jobs = ref([])
const error = ref('')
const backupPrefix = ref('')
const restoreFolder = ref('')
const restoreOverwrite = ref(false)
const restoreDryRun = ref(false)
const manifestView = ref(null)
let pollTimer = null

const activeJob = computed(() => jobs.value.find(j => j.state === 'running') || null)
const busy = computed(() => !!activeJob.value)
// Панель показывает бегущую задачу, а после завершения — последнюю (результат/журнал/ошибки не пропадают).
const displayJob = computed(() => activeJob.value || jobs.value[0] || null)
const resultTitleKey = computed(() => {
  const kind = displayJob.value?.kind
  if (kind === 'backup' || kind === 'backup_dry_run') return 'storage.job.backupResult'
  if (kind === 'restore') return 'storage.job.restoreResult'
  return 'storage.job.dryRunResult'
})

function fmtSize(bytes) {
  if (bytes === null || bytes === undefined) return '—'
  const units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']
  let v = bytes
  for (const u of units) {
    if (v < 1024) return `${v.toFixed(1)} ${u}`
    v /= 1024
  }
  return `${v.toFixed(1)} ПБ`
}

function fmtDate(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 19)
}

async function refreshBackups() {
  try {
    const { data } = await api.get('/admin/storage/backups/')
    backups.value = data.backups || []
    if (!restoreFolder.value && backups.value.length) {
      restoreFolder.value = backups.value[0].folder
    }
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

async function refreshJobs() {
  try {
    const { data } = await api.get('/admin/storage/jobs/')
    jobs.value = data.jobs || []
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

function startPolling(id) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const { data } = await api.get(`/admin/storage/jobs/${id}/`)
      const idx = jobs.value.findIndex(j => j.id === id)
      if (idx >= 0) jobs.value[idx] = data
      else jobs.value.unshift(data)
      if (data.state !== 'running') {
        stopPolling()
        refreshBackups()
        refreshJobs()
      }
    } catch (e) {
      stopPolling()
      error.value = e.displayMessage || t('storage.errors.unknown')
      refreshJobs()
    }
  }, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function startBackup(dryRun) {
  error.value = ''
  try {
    const { data } = await api.post(`/admin/storage/backup/${dryRun ? 'dry-run' : 'start'}/`, {
      prefix: backupPrefix.value.trim(),
    })
    startPolling(data.job_id)
    refreshJobs()
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

async function startRestore() {
  error.value = ''
  try {
    const { data } = await api.post('/admin/storage/restore/start/', {
      folder: restoreFolder.value,
      overwrite: restoreOverwrite.value,
      dry_run: restoreDryRun.value,
    })
    startPolling(data.job_id)
    refreshJobs()
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

async function cancelJob() {
  if (!activeJob.value) return
  try {
    await api.post(`/admin/storage/jobs/${activeJob.value.id}/cancel/`)
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

async function openManifest(folder) {
  error.value = ''
  try {
    const { data } = await api.get(`/admin/storage/backups/${folder}/manifest/`)
    manifestView.value = { folder, json: JSON.stringify(data.manifest, null, 2) }
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

async function downloadManifest(folder) {
  error.value = ''
  try {
    const { data } = await api.get(`/admin/storage/backups/${folder}/manifest/`)
    const blob = new Blob([JSON.stringify(data.manifest, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `manifest-${folder}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.displayMessage || t('storage.errors.unknown')
  }
}

onMounted(async () => {
  await refreshBackups()
  await refreshJobs()
  if (activeJob.value) startPolling(activeJob.value.id)
})

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.storage-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px;
  color: #1f2430;
}

.lead { color: #5a6270; margin-bottom: 20px; }

.panel {
  background: #fff;
  border: 1px solid #e3e6ec;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}

.panel h2 { margin: 0 0 10px; font-size: 18px; }

.desc { color: #5a6270; margin: 0 0 12px; }
.hint { color: #8a92a2; font-size: 13px; margin: 10px 0 0; }

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}
.row label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #5a6270; }
.row .grow { flex: 1; min-width: 260px; }
.row .check { flex-direction: row; align-items: center; gap: 6px; }

input[type='text'], select {
  padding: 8px 10px;
  border: 1px solid #cfd4dd;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}
input[type='text']:focus, select:focus { outline: none; border-color: #3b6fe0; }

.btn {
  padding: 9px 16px;
  border: 1px solid #cfd4dd;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  color: #1f2430;
}
.btn:hover:not(:disabled) { background: #f4f6fa; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--primary { background: #3b6fe0; border-color: #3b6fe0; color: #fff; }
.btn--primary:hover:not(:disabled) { background: #2f5cc4; }
.btn--danger { background: #d92d20; border-color: #d92d20; color: #fff; }
.btn--danger:hover:not(:disabled) { background: #b42318; }
.btn--small { padding: 4px 10px; font-size: 13px; }

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  margin-left: 8px;
  vertical-align: middle;
}
.badge--running { background: #e8f0fe; color: #2f5cc4; }
.badge--done { background: #e6f4ea; color: #1e7f3c; }
.badge--failed { background: #fdecea; color: #b42318; }
.badge--cancelled { background: #f4f6fa; color: #5a6270; }
.badge--kind { background: #f4f6fa; color: #8a92a2; }

.progress {
  position: relative;
  height: 26px;
  background: #eef1f5;
  border-radius: 6px;
  overflow: hidden;
  margin: 12px 0;
}
.progress__fill {
  height: 100%;
  background: linear-gradient(90deg, #3b6fe0, #58a6ff);
  transition: width 0.4s ease;
}
.progress__label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #1f2430;
}

.job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  font-size: 13px;
  color: #5a6270;
  margin-bottom: 10px;
}
.job-failed { color: #b42318; font-weight: 600; }

.log {
  background: #0f172a;
  color: #cbd5e1;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 260px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-text { color: #b42318; font-weight: 600; }

.dry-run-result {
  margin-top: 14px;
  padding: 12px;
  background: #f4f6fa;
  border-radius: 6px;
  font-size: 14px;
}
.dry-run-result h3 { margin: 0 0 8px; font-size: 14px; }
.sample-keys { margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: #5a6270; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eef1f5; }
th { color: #5a6270; font-weight: 600; font-size: 13px; }
.num { text-align: right; }
.actions { text-align: right; white-space: nowrap; }

.commands { margin: 0; }
.commands div { padding: 8px 0; border-bottom: 1px dashed #e3e6ec; }
.commands div:last-child { border-bottom: none; }
.commands dt { font-weight: 600; margin-bottom: 4px; }
.commands dd { margin: 0; color: #5a6270; font-size: 14px; }

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: #fff;
  border-radius: 10px;
  width: min(900px, 92vw);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}
.modal__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #e3e6ec;
}
.modal__head h3 { margin: 0; font-size: 16px; }
.modal__json {
  margin: 0;
  padding: 16px 18px;
  overflow: auto;
  font-size: 12px;
  background: #f8fafc;
  flex: 1;
}
</style>

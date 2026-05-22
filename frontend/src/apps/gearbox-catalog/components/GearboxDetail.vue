<template>
  <div class="detail" v-if="data">
    <!-- Кнопка назад -->
    <button class="back" @click="$emit('close')">← Назад к каталогу</button>

    <!-- Заголовок -->
    <h1 class="title">{{ data.name || data.code || 'Редуктор' }}</h1>

    <div class="detail-grid">
      <!-- Фотогалерея -->
      <div class="gallery">
        <div class="main-image">
          <img
            v-if="currentImage"
            :src="currentImage"
            :alt="data.image_alt || 'Редуктор'"
          />
          <div v-else class="placeholder">Нет фото</div>
        </div>
        <div class="thumbs" v-if="data.images && data.images.length > 1">
          <button
            v-for="(img, i) in data.images"
            :key="img.id"
            :class="{active: activeImageIdx === i}"
            @click="activeImageIdx = i"
          >
            <img :src="img.preview_url || img.url" :alt="data.image_alt" />
          </button>
        </div>
      </div>

      <!-- Правая колонка: цена + краткие характеристики -->
      <div class="info">
        <div class="price-block">
          <div class="price" v-if="price">
            {{ formatPrice(price.price) }} {{ price.currency_symbol || '$' }}
          </div>
          <div class="price-na" v-else>Цена по запросу</div>
        </div>

        <div class="quick-specs">
          <div class="spec-row" v-if="data.model_line?.brand?.name">
            <span class="spec-label">Бренд</span>
            <span class="spec-val">{{ data.model_line.brand.name }}</span>
          </div>
          <div class="spec-row" v-if="data.model_line?.gearbox_variety">
            <span class="spec-label">Тип</span>
            <span class="spec-val">{{ data.model_line.gearbox_variety }}</span>
          </div>
          <div class="spec-row" v-if="data.model_line?.gearbox_output_variety">
            <span class="spec-label">Выход</span>
            <span class="spec-val">{{ data.model_line.gearbox_output_variety }}</span>
          </div>
          <div class="spec-row" v-if="data.ip">
            <span class="spec-label">IP</span>
            <span class="spec-val">{{ data.ip.name }}</span>
          </div>
          <div class="spec-row" v-if="data.body?.transmission_variety">
            <span class="spec-label">Передача</span>
            <span class="spec-val">{{ data.body.transmission_variety }}</span>
          </div>
          <div class="spec-row" v-if="data.body?.reduction_ratio_text">
            <span class="spec-label">Передат. число</span>
            <span class="spec-val">{{ data.body.reduction_ratio_text }}</span>
          </div>
          <div class="spec-row" v-if="data.body?.max_output_torque">
            <span class="spec-label">Макс. момент</span>
            <span class="spec-val">{{ data.body.max_output_torque }} Нм</span>
          </div>
          <div class="spec-row" v-if="data.body?.weight">
            <span class="spec-label">Вес</span>
            <span class="spec-val">{{ data.body.weight }} кг</span>
          </div>
        </div>

        <div class="code-block" v-if="data.code">
          Код: {{ data.code }}
        </div>
      </div>
    </div>

    <!-- Вкладки -->
    <div class="tabs-section">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.key"
          :class="{active: activeTab === t.key}"
          @click="activeTab = t.key"
        >{{ t.label }}</button>
      </div>

      <div class="tab-content">
        <!-- Характеристики -->
        <div v-if="activeTab === 'specs'" class="tab-specs">
          <h3>Характеристики</h3>
          <table v-if="specs.length">
            <tr v-for="s in specs" :key="s.label">
              <td>{{ s.label }}</td>
              <td>{{ s.value }}</td>
            </tr>
          </table>
          <p v-else>Нет данных</p>
        </div>

        <!-- Документы -->
        <div v-if="activeTab === 'docs'" class="tab-docs">
          <h3>Документы</h3>
          <div v-if="data.tech_docs && data.tech_docs.length" class="doc-list">
            <a
              v-for="doc in data.tech_docs"
              :key="doc.id"
              :href="doc.url"
              target="_blank"
              class="doc-link"
            >
              📄 {{ doc.title || doc.file_name || 'Документ' }}
            </a>
          </div>
          <p v-else>Нет документов</p>
        </div>

        <!-- Сертификаты -->
        <div v-if="activeTab === 'certs'" class="tab-certs">
          <h3>Сертификаты</h3>
          <div v-if="data.cert_docs && data.cert_docs.length" class="doc-list">
            <a
              v-for="doc in data.cert_docs"
              :key="doc.id"
              :href="doc.url"
              target="_blank"
              class="doc-link"
            >
              📜 {{ doc.title || doc.file_name || 'Сертификат' }}
            </a>
          </div>
          <p v-else>Нет сертификатов</p>
        </div>

        <!-- Краткое описание -->
        <div v-if="activeTab === 'brief'" class="tab-brief">
          <h3>Краткое описание</h3>
          <div class="brief-fields">
            <div class="brief-field">
              <label>Название</label>
              <div class="brief-value copyable" @click="copyText(data.name)">
                {{ data.name }}
                <span class="copy-hint">Нажмите, чтобы скопировать</span>
              </div>
            </div>
            <div class="brief-field">
              <label>Описание</label>
              <div class="brief-value copyable" @click="copyText(data.description || '')">
                {{ data.description || '—' }}
                <span class="copy-hint">Нажмите, чтобы скопировать</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="loading" v-else-if="loading">Загрузка...</div>
  <div class="error" v-else>Не удалось загрузить редуктор</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import gearboxApi from '../api'

const props = defineProps({ id: [Number, String] })
defineEmits(['close'])

const data = ref(null)
const price = ref(null)
const loading = ref(true)
const activeImageIdx = ref(0)
const activeTab = ref('specs')

const tabs = [
  { key: 'specs', label: 'Характеристики' },
  { key: 'docs', label: 'Документы' },
  { key: 'certs', label: 'Сертификаты' },
  { key: 'brief', label: 'Краткое описание' },
]

const currentImage = computed(() => {
  if (!data.value?.images?.length) return null
  const idx = Math.min(activeImageIdx.value, data.value.images.length - 1)
  return data.value.images[idx]?.url || null
})

const specs = computed(() => {
  if (!data.value) return []
  const d = data.value
  const body = d.body || {}
  const rows = []

  const add = (label, value) => { if (value != null && value !== '') rows.push({ label, value }) }

  add('Бренд', d.model_line?.brand?.name)
  add('Серия', d.model_line?.name)
  add('Тип редуктора', d.model_line?.gearbox_variety)
  add('Тип выхода', d.model_line?.gearbox_output_variety)
  add('Код', d.code)
  add('IP', d.ip?.name)
  add('Температура', d.work_temp_min != null && d.work_temp_max != null
    ? `${d.work_temp_min}…${d.work_temp_max} °С`
    : null)
  add('Расцепляемый', d.is_declutchable_display)
  add('Механизм отключения', d.override_mechanism?.name)
  add('Механизм блокировки', d.locking_mechanism?.name)
  add('Материал корпуса', d.body_material_text)
  add('Тип передачи', body.transmission_variety)
  add('Передаточное число', body.reduction_ratio_text)
  add('Коэффициент усиления', body.amplification_factor)
  add('КПД', body.efficiency != null ? `${body.efficiency}` : null)
  add('Макс. входной момент', body.max_input_torque ? `${body.max_input_torque} Нм` : null)
  add('Макс. рабочий момент', body.max_work_torque ? `${body.max_work_torque} Нм` : null)
  add('Макс. выходной момент', body.max_output_torque ? `${body.max_output_torque} Нм` : null)
  add('Усилие на штурвале', body.handwheel_force_nominal ? `${body.handwheel_force_nominal} Н` : null)
  add('Диаметр штурвала', body.handwheel_diameter ? `${body.handwheel_diameter} мм` : null)
  add('Вес', body.weight ? `${body.weight} кг` : null)
  add('Монтажная площадка (верх)', body.mounting_plate_top_list_text)
  add('Монтажная площадка (низ)', body.mounting_plate_bottom_list_text)
  add('Шток к приводу', body.stem_shape_top ? `${body.stem_shape_top} ${body.stem_size_top || ''}`.trim() : null)
  add('Шток к арматуре', body.stem_shape_bottom ? `${body.stem_shape_bottom} ${body.stem_size_bottom || ''}`.trim() : null)

  return rows
})

function formatPrice(val) {
  if (val == null) return ''
  const n = Number(val)
  if (isNaN(n)) return ''
  return n.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function copyText(text) {
  if (!text) return
  navigator.clipboard.writeText(text).catch(() => {})
}

async function load() {
  loading.value = true
  try {
    const r = await gearboxApi.getDetail(props.id)
    data.value = r.data

    // Цена
    if (r.data.sku?.code) {
      try {
        const pr = await gearboxApi.getPrices([r.data.sku.code])
        if (pr.data?.snapshots) {
          price.value = pr.data.snapshots[r.data.sku.code] || null
        }
      } catch {}
    }
  } catch (e) {
    console.error('Failed to load detail', e)
    data.value = null
  }
  loading.value = false
}

onMounted(load)
watch(() => props.id, load)
</script>

<style scoped>
.detail{max-width:1200px;margin:0 auto}
.back{
  display:inline-flex;align-items:center;gap:6px;
  padding:8px 0;font-size:14px;color:#6b7280;background:none;border:none;cursor:pointer;margin-bottom:16px
}
.back:hover{color:#1a1a1a}
.title{font-size:28px;font-weight:700;line-height:1.3;margin-bottom:24px}
.detail-grid{display:grid;grid-template-columns:1fr 340px;gap:32px;margin-bottom:40px}

/* Галерея */
.gallery{}
.main-image{
  background:#f9fafb;border-radius:12px;overflow:hidden;
  aspect-ratio:4/3;display:flex;align-items:center;justify-content:center
}
.main-image img{max-width:100%;max-height:100%;object-fit:contain;padding:16px}
.placeholder{color:#d1d5db;font-size:16px}
.thumbs{display:flex;gap:8px;margin-top:12px;overflow-x:auto}
.thumbs button{
  width:64px;height:64px;padding:4px;border:2px solid #e5e7eb;border-radius:8px;
  background:#fff;cursor:pointer;flex-shrink:0;overflow:hidden
}
.thumbs button.active{border-color:#2563eb}
.thumbs button img{width:100%;height:100%;object-fit:contain}

/* Инфо */
.info{}
.price-block{margin-bottom:20px}
.price{font-size:32px;font-weight:800;color:#dc2626}
.price-na{font-size:18px;color:#9ca3af}
.quick-specs{margin-bottom:20px}
.spec-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f3f4f6;font-size:14px}
.spec-label{color:#6b7280;flex-shrink:0;margin-right:12px}
.spec-val{text-align:right;font-weight:500}
.code-block{font-size:13px;color:#9ca3af;padding:8px 0}

/* Вкладки */
.tabs-section{border-top:1px solid #e5e7eb;padding-top:24px}
.tabs{display:flex;gap:0;border-bottom:2px solid #e5e7eb;margin-bottom:24px}
.tabs button{
  padding:12px 24px;font-size:15px;font-weight:500;
  background:none;border:none;border-bottom:2px solid transparent;
  margin-bottom:-2px;cursor:pointer;color:#6b7280
}
.tabs button:hover{color:#1a1a1a}
.tabs button.active{color:#2563eb;border-bottom-color:#2563eb}
.tab-content{min-height:200px}
.tab-content h3{margin-bottom:16px;font-size:20px}

/* Характеристики */
.tab-specs table{width:100%;border-collapse:collapse}
.tab-specs td{padding:10px 14px;border-bottom:1px solid #f3f4f6;font-size:14px}
.tab-specs td:first-child{color:#6b7280;width:40%}
.tab-specs td:last-child{font-weight:500}

/* Документы и сертификаты */
.doc-list{display:flex;flex-direction:column;gap:10px}
.doc-link{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#f9fafb;border-radius:8px;
  text-decoration:none;color:#2563eb;font-size:14px;transition:background .15s}
.doc-link:hover{background:#eff6ff}

/* Краткое описание */
.brief-fields{display:flex;flex-direction:column;gap:16px}
.brief-field label{display:block;font-size:13px;font-weight:500;color:#6b7280;margin-bottom:6px}
.brief-value{
  background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;
  padding:12px 14px;font-size:14px;line-height:1.5;position:relative;cursor:pointer;
  min-height:44px
}
.copyable:hover{background:#eff6ff;border-color:#93c5fd}
.copy-hint{display:none;position:absolute;top:6px;right:10px;font-size:11px;color:#2563eb}
.copyable:hover .copy-hint{display:inline}

/* Состояния */
.loading,.error{text-align:center;padding:60px 20px;color:#9ca3af;font-size:16px}

@media(max-width:860px){
  .detail-grid{grid-template-columns:1fr}
  .title{font-size:22px}
}
</style>

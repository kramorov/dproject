<!-- PaSelectionPage.vue — Подбор пневмопривода по параметрам арматуры -->
<template>
  <div class="pa-selector">
    <h1>🔧 Подбор пневматического привода</h1>

    <!-- ========== Параметры арматуры ========== -->
    <section class="section">
      <h2>📋 Параметры арматуры</h2>
      <div class="grid-3">
        <div class="field">
          <label>Тип арматуры</label>
          <select v-model="form.valve_type_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.valve_types" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>DN</label>
          <select v-model="form.dn_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.dn_varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>PN</label>
          <select v-model="form.pn_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.pn_varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>
      <div class="grid-3">
        <div class="field">
          <label>Монтажная площадка</label>
          <select v-model="form.mounting_plate_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.mounting_plates" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Форма штока</label>
          <select v-model="form.stem_shape_id" @change="onStemShapeChange">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.stem_shapes" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Шток</label>
          <select v-model="form.stem_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in filteredStems" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>
    </section>

    <!-- ========== Расчёт момента ========== -->
    <section class="section">
      <h2>⚙️ Расчёт крутящего момента</h2>
      <div class="grid-3">
        <div class="field">
          <label>Момент без запаса (Нм)</label>
          <input type="number" v-model.number="form.torque_without_safety" min="0" step="1" />
        </div>
        <div class="field">
          <label>Коэффициент запаса</label>
          <input type="number" v-model.number="form.safety_factor" min="1.0" step="0.1" />
        </div>
        <div class="field">
          <label>Момент с запасом (Нм)</label>
          <input type="number" :value="torqueWithSafety" disabled class="readonly" />
        </div>
      </div>
    </section>

    <!-- ========== Требования к приводу ========== -->
    <section class="section">
      <h2>🔧 Требования к приводу</h2>
      <div class="grid-2">
        <div class="field">
          <label>Серия моделей</label>
          <select v-model="form.model_line_id" @change="onModelLineChange">
            <option :value="null">— Все серии —</option>
            <option v-for="v in refs.model_lines" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Вид привода (DA/SR)</label>
          <select v-model="form.actuator_variety_id" @change="onVarietyChange">
            <option :value="null">— Выберите —</option>
            <option v-for="v in actuatorVarieties" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>
      <div class="grid-3">
        <div class="field">
          <label>Положение безопасности</label>
          <select v-model="form.safety_position_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in safetyPositions" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Давление в пневмосистеме</label>
          <select v-model="form.air_pressure_id">
            <option :value="null">— Выберите —</option>
            <option v-for="v in refs.air_pressure" :key="v.id" :value="v.id" :disabled="v.code === 'spring'">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>IP защита</label>
          <select v-model="form.ip_id">
            <option :value="null">— Не выбрано —</option>
            <option v-for="v in actuatorOptions.ip_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>
      <div class="grid-3">
        <div class="field">
          <label>Exd взрывозащита</label>
          <select v-model="form.exd_id">
            <option :value="null">— Не выбрано —</option>
            <option v-for="v in actuatorOptions.exd_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Покрытие корпуса</label>
          <select v-model="form.coating_id">
            <option :value="null">— Не выбрано —</option>
            <option v-for="v in actuatorOptions.coating_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Ручной дублёр</label>
          <select v-model="form.hand_wheel_id">
            <option :value="null">— Не выбрано —</option>
            <option v-for="v in actuatorOptions.hand_wheel_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>
      <div class="grid-2">
        <div class="field">
          <label>Температура мин. (°C)</label>
          <input type="number" v-model.number="form.temp_min" step="1" />
        </div>
        <div class="field">
          <label>Температура макс. (°C)</label>
          <input type="number" v-model.number="form.temp_max" step="1" />
        </div>
      </div>
    </section>

    <!-- ========== Кнопки ========== -->
    <div class="actions">
      <button class="btn-primary" @click="search" :disabled="searching">
        {{ searching ? 'Поиск...' : '🔍 Подобрать привод' }}
      </button>
      <button class="btn-secondary" @click="reset">🗑 Очистить фильтры</button>
    </div>

    <!-- ========== Ошибки ========== -->
    <div v-if="error" class="error-msg">❌ {{ error }}</div>

    <!-- ========== Результаты ========== -->
    <section v-if="results.length" class="section results">
      <h2>📊 Результаты подбора ({{ results.length }} серий)</h2>
      <div v-for="ml in results" :key="ml.model_line_name" class="result-group">
        <h3>📁 {{ ml.model_line_name }} <code>{{ ml.model_line_code }}</code></h3>
        <div v-for="(item, idx) in ml.model_line_items" :key="idx" class="result-card">
          <div class="result-header">
            <strong>{{ idx + 1 }}. {{ item.model_line_item_name }}</strong>
            <code>{{ item.model_line_item_code }}</code>
          </div>
          <div class="result-metrics">
            <span>🏭 {{ item.body_name }} ({{ item.body_code }})</span>
            <span>📌 {{ item.actuator_variety_code }}</span>
            <span>⭐ Score: {{ item.score?.toFixed(1) }}</span>
            <span>📊 Запас: {{ item.spring_margin?.toFixed(0) }} Нм</span>
          </div>
          <div v-if="item.actuator_variety_code === 'SR'" class="result-springs">
            Пружины: {{ item.spring_qty_name }} |
            BTO/ETO: {{ item.spring_bto?.toFixed(0) }}/{{ item.spring_eto?.toFixed(0) }} (пруж.)
            {{ item.pressure_bto?.toFixed(0) }}/{{ item.pressure_eto?.toFixed(0) }} (возд.)
          </div>
          <div v-else class="result-springs">
            💨 BTO: {{ item.spring_bto?.toFixed(0) }} Нм
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import api from '@/shared/api'

export default {
  name: 'PaSelectionPage',
  data() {
    return {
      refs: {
        valve_types: [], dn_varieties: [], pn_varieties: [],
        mounting_plates: [], stem_shapes: [], stem_sizes: [],
        air_pressure: [], model_lines: [],
      },
      actuatorOptions: {
        actuator_varieties: [], safety_positions: [],
        ip_options: [], exd_options: [], coating_options: [], hand_wheel_options: [],
      },
      form: {
        valve_type_id: null, dn_id: null, pn_id: null,
        mounting_plate_id: null, stem_shape_id: null, stem_id: null,
        torque_without_safety: 0, safety_factor: 1.5,
        model_line_id: null,
        actuator_variety_id: null, safety_position_id: null,
        air_pressure_id: null, ip_id: null, exd_id: null,
        coating_id: null, hand_wheel_id: null,
        temp_min: 0, temp_max: 0,
      },
      results: [],
      error: '',
      searching: false,
    }
  },
  computed: {
    torqueWithSafety() {
      return (this.form.torque_without_safety * this.form.safety_factor).toFixed(1)
    },
    filteredStems() {
      if (!this.form.stem_shape_id) return this.refs.stem_sizes
      return this.refs.stem_sizes.filter(s => s.stem_shape_id === this.form.stem_shape_id)
    },
    actuatorVarieties() {
      return this.actuatorOptions.actuator_varieties || []
    },
    safetyPositions() {
      return this.actuatorOptions.safety_positions || []
    },
  },
  async mounted() {
    await this.loadInitialData()
  },
  methods: {
    async loadInitialData() {
      try {
        const { data } = await api.get('/pneumatic_actuators/selector/initial-data/')
        this.refs = { ...this.refs, ...data }
      } catch (e) {
        this.error = 'Ошибка загрузки справочников: ' + (e.displayMessage || e.message)
      }
    },
    async loadActuatorOptions() {
      try {
        const params = {}
        if (this.form.model_line_id) params.model_line_id = this.form.model_line_id
        if (this.form.actuator_variety_id) params.actuator_variety_id = this.form.actuator_variety_id
        const { data } = await api.get('/pneumatic_actuators/options/', { params })
        this.actuatorOptions = data
      } catch (e) {
        // silently ignore — options are optional
      }
    },
    async onModelLineChange() {
      this.actuatorOptions.safety_positions = []
      await this.loadActuatorOptions()
    },
    onStemShapeChange() {
      this.form.stem_id = null
    },
    async onVarietyChange() {
      await this.loadActuatorOptions()
    },
    async search() {
      this.error = ''
      this.results = []

      if (!this.form.valve_type_id) { this.error = 'Не выбран тип арматуры'; return }
      if (!this.form.torque_without_safety || this.form.torque_without_safety <= 0) { this.error = 'Укажите момент без запаса'; return }
      if (!this.form.air_pressure_id) { this.error = 'Не указано давление в пневмосистеме'; return }
      if (!this.form.actuator_variety_id) { this.error = 'Не выбран тип привода (DA/SR)'; return }

      const varietyObj = this.actuatorVarieties.find(v => v.id === this.form.actuator_variety_id)
      const actuator_variety_code = varietyObj?.code || 'DA'

      if (actuator_variety_code === 'SR' && !this.form.safety_position_id) {
        this.error = 'Для SR привода выберите положение безопасности (NO/NC)'
        return
      }

      this.searching = true
      try {
        const payload = {
          ...this.form,
          actuator_variety_code,
          torque_with_safety: parseFloat(this.torqueWithSafety),
        }
        const { data } = await api.post('/pneumatic_actuators/selector/search/', payload)
        this.results = data.search_results || []
        if (!this.results.length) this.error = 'Не найдено подходящих приводов'
      } catch (e) {
        this.error = e.response?.data?.error || e.displayMessage || 'Ошибка подбора'
      } finally {
        this.searching = false
      }
    },
    reset() {
      this.form = {
        valve_type_id: null, dn_id: null, pn_id: null,
        mounting_plate_id: null, stem_shape_id: null, stem_id: null,
        torque_without_safety: 0, safety_factor: 1.5,
        model_line_id: null, model_line_item_id: null,
        actuator_variety_id: null, safety_position_id: null,
        air_pressure_id: null, ip_id: null, exd_id: null,
        coating_id: null, hand_wheel_id: null,
        temp_min: 0, temp_max: 0,
      }
      this.results = []
      this.error = ''
      this.modelLineItems = []
    },
  },
}
</script>

<style scoped>
.pa-selector {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
  font-family: system-ui, sans-serif;
}
h1 { font-size: 1.6rem; margin-bottom: 20px; }
h2 { font-size: 1.15rem; color: #555; margin: 16px 0 10px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
h3 { margin: 12px 0 4px; }
code { background: #f0f0f0; padding: 1px 6px; border-radius: 3px; font-size: 0.85em; }
.section { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 8px; }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.field { display: flex; flex-direction: column; }
.field label { font-size: 0.8rem; color: #666; margin-bottom: 4px; font-weight: 500; }
.field select, .field input { padding: 7px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 0.9rem; }
.field input.readonly { background: #f5f5f5; color: #888; }
.actions { display: flex; gap: 12px; margin: 20px 0; }
.btn-primary { padding: 10px 28px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { padding: 10px 20px; background: #fff; border: 1px solid #ccc; border-radius: 6px; cursor: pointer; }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
.results { background: #fff; }
.result-group { margin-bottom: 16px; }
.result-card { border: 1px solid #e8e8e8; border-radius: 6px; padding: 12px; margin: 8px 0; background: #fafbff; }
.result-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.result-metrics { display: flex; gap: 20px; font-size: 0.85rem; color: #555; flex-wrap: wrap; }
.result-springs { font-size: 0.82rem; color: #777; margin-top: 4px; }
</style>

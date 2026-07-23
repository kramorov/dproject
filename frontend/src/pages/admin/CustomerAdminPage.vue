<template>
  <div class="customer-admin">
    <h2>Администрирование клиентов</h2>
    <div v-if="!editing">
      <button class="btn-primary" @click="createNew">+ Добавить клиента</button>
      <table v-if="customers.length" class="cust-table">
        <thead><tr><th>Название</th><th>Email</th><th>Польз.</th><th>Ключей</th><th>Активен</th><th></th></tr></thead>
        <tbody><tr v-for="c in customers" :key="c.id">
          <td>{{ c.name }}</td><td>{{ c.email }}</td>
          <td>{{ c.users_count }}</td><td>{{ c.api_keys_count }}</td>
          <td>{{ c.is_active ? '✅' : '❌' }}</td>
          <td><button @click="editCustomer(c.id)">Редактировать</button></td>
        </tr></tbody>
      </table>
    </div>

    <div v-else class="edit-form">
      <button @click="editing=null; load()">← К списку</button>
      <h3>{{ isNew ? 'Новый клиент' : data.name }}</h3>

      <fieldset><legend>Основное</legend>
        <label>Название: <input v-model="data.name" /></label>
        <label>Краткое: <input v-model="data.short_name" /></label>
        <label>Email: <input v-model="data.email" /></label>
        <label>Телефон: <input v-model="data.phone" /></label>
        <label><input type="checkbox" v-model="data.is_active" /> Активен</label>
        <label>Доступ до: <input type="date" v-model="data.access_until" /></label>
      </fieldset>

      <fieldset><legend>Видимые разделы сайта</legend>
        <label v-for="s in allSections" :key="s.code"><input type="checkbox" :value="s.code" v-model="data.visible_sections" /> {{ s.name }}</label>
      </fieldset>

      <!-- Роли (определения) -->
      <fieldset><legend>Роли (назначаются пользователям)</legend>
        <div v-for="(r,i) in data.roles" :key="i" class="row">
          <input v-model="r.code" placeholder="код" size="12" />
          <input v-model="r.name" placeholder="название" size="16" />
          <label><input type="checkbox" v-model="r.is_default" /> По умолч.</label>
          <select v-model="r.django_user"><option value="">— нет —</option>
            <option v-for="du in djangoUsers" :key="du.id" :value="du.username">{{ du.username }}</option>
          </select>
          <span>Разделы:</span>
          <label v-for="s in allSections" :key="'rs'+i+s.code"><input type="checkbox" :value="s.code" v-model="r.section_permissions" /> {{ s.name }}</label>
          <button class="btn-sm-del" @click="data.roles.splice(i,1)">✕</button>
        </div>
        <button class="btn-sm" @click="data.roles.push({code:'',name:'',is_default:false,django_user:null,section_permissions:[]})">+ Роль</button>
      </fieldset>

      <!-- Пользователи -->
      <fieldset><legend>Пользователи</legend>
        <div v-for="(u,i) in data.users" :key="i" class="row">
          <input v-model="u.login" placeholder="логин" size="12" />
          <input v-model="u.first_name" placeholder="Имя" size="10" />
          <input v-model="u.last_name" placeholder="Фамилия" size="12" />
          <input v-model="u.email" placeholder="email" size="18" />
          <input v-model="u.phone" placeholder="тел" size="10" />
          <label><input type="checkbox" v-model="u.is_active" /> Активен</label>
          <span>Роли:</span>
          <select v-model="u.roles" multiple size="3">
            <option v-for="r in data.roles" :key="r.code||i" :value="r.code">{{ r.name||r.code }}</option>
          </select>
          <button class="btn-sm-del" @click="deleteUser(u, i)">✕</button>
        </div>
        <div class="new-row">
          <input v-model="newUser.login" placeholder="логин" size="12" />
          <input v-model="newUser.first_name" placeholder="Имя" size="10" />
          <input v-model="newUser.last_name" placeholder="Фамилия" size="12" />
          <input v-model="newUser.email" placeholder="email" size="18" />
          <input v-model="newUser.password" type="password" placeholder="пароль" size="10" />
          <button class="btn-sm" @click="addUser">+</button>
        </div>
      </fieldset>

      <!-- API-ключи -->
      <fieldset><legend>API-ключи</legend>
        <div v-for="(k,i) in data.api_keys" :key="i" class="row">
          <strong>{{ k.key_prefix }}***</strong>
          <span>{{ k.name }}</span>
          <label><input type="checkbox" v-model="k.is_active" /> Активен</label>
          <span>Приложения:</span>
          <label v-for="a in allApps" :key="'ka'+i+a.code"><input type="checkbox" :value="a.code" v-model="k.allowed_apps" /> {{ a.name }}</label>
          <button class="btn-sm-del" @click="deleteKey(k, i)">✕</button>
        </div>
        <div class="new-row">
          <input v-model="newKey.name" placeholder="Название ключа" size="20" />
          <button class="btn-sm" @click="addKey">+ Ключ</button>
          <span v-if="newKey.raw" class="raw-key">RAW: {{ newKey.raw }}</span>
        </div>
      </fieldset>

      <!-- Доступ к мини-приложениям -->
      <fieldset><legend>Доступ к мини-приложениям</legend>
        <div v-for="(a,i) in data.app_access" :key="i" class="row">
          <strong>{{ a.app_name }}</strong>
          <select v-model="a.brand_filter"><option value="all">Все бренды</option><option value="selected">Выбранные</option></select>
          <label><input type="checkbox" v-model="a.is_active" /> Активен</label>
          <template v-if="a.brand_filter==='selected'">
            <span class="brand-list">
              <label v-for="b in allBrands" :key="b.id" style="font-size:11px">
                <input type="checkbox" :value="b.id" v-model="a.brands" /> {{ b.name }}
              </label>
            </span>
          </template>
          <button class="btn-sm-del" @click="data.app_access.splice(i,1)">✕</button>
        </div>
        <div class="new-row">
          <select v-model="newAccess.app_code">
            <option value="">— приложение —</option>
            <option v-for="a in allApps" :key="a.code" :value="a.code">{{ a.name }}</option>
          </select>
          <button class="btn-sm" @click="addAccess">+</button>
        </div>
      </fieldset>

      <!-- Email -->
      <fieldset><legend>Email для уведомлений</legend>
        <div v-for="(e,i) in data.notification_emails" :key="i" class="row">
          <select v-model="e.email_type"><option value="requests">Заявки</option><option value="invoices">Счета</option><option value="support">Техподдержка</option></select>
          <input v-model="e.email" placeholder="email" size="25" />
          <label><input type="checkbox" v-model="e.is_active" /> Активен</label>
          <button class="btn-sm-del" @click="data.notification_emails.splice(i,1)">✕</button>
        </div>
        <div class="new-row">
          <select v-model="newEmail.type"><option value="requests">Заявки</option><option value="invoices">Счета</option><option value="support">Техподдержка</option></select>
          <input v-model="newEmail.email" placeholder="email" size="25" />
          <button class="btn-sm" @click="addEmail">+</button>
        </div>
      </fieldset>

      <button class="btn-primary" @click="save" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
      <p v-if="saveMsg" :class="saveErr?'err':''">{{ saveMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '@/shared/api'

const customers = ref([])
const editing = ref(null); const isNew = ref(false)
const data = ref({}); const saving = ref(false)
const saveMsg = ref(''); const saveErr = ref(false)
const allSections = ref([]); const allApps = ref([]); const allBrands = ref([]); const djangoUsers = ref([])

const newUser = reactive({login:'',first_name:'',last_name:'',email:'',password:''})
const newKey = reactive({name:'',raw:''})
const newAccess = reactive({app_code:''})
const newEmail = reactive({type:'requests',email:''})

async function load() {
  const r = await api.get('/admin/customers/')
  customers.value = r.data.customers
  const s = await api.get('/core/sections/'); allSections.value = s.data.sections||[]
  const a = await api.get('/core/allowed-apps/'); allApps.value = a.data.apps||[]
  const u = await api.get('/core/django-users/'); djangoUsers.value = u.data.users||[]
  const b = await api.get('/core/brands/'); allBrands.value = b.data.brands||[]
}

function createNew() {
  isNew.value = true
  data.value = {name:'',short_name:'',email:'',phone:'',is_active:true,access_until:null,visible_sections:[],roles:[],users:[],api_keys:[],app_access:[],notification_emails:[]}
  editing.value = 'new'
}

async function editCustomer(id) {
  isNew.value = false
  const r = await api.get(`/admin/customers/${id}/`); data.value = r.data; editing.value = id
}

async function save() {
  saving.value = true; saveMsg.value = ''; saveErr.value = false
  try {
    if (isNew.value) { await api.post('/admin/customers/', data.value) }
    else { await api.post(`/admin/customers/${editing.value}/`, data.value) }
    saveMsg.value = 'Сохранено'; editing.value = null; await load()
  } catch(e) { saveMsg.value = 'Ошибка: '+(e.response?.data?.error||e.message); saveErr.value = true }
  finally { saving.value = false }
}

async function addUser() {
  if (!newUser.login) return
  try {
    const r = await api.post(`/admin/customers/${editing.value}/users/`, {...newUser, roles:[]})
    data.value.users.push({id:r.data.id, login:newUser.login, first_name:newUser.first_name, last_name:newUser.last_name, email:newUser.email, phone:'', position:'', is_active:true, roles:[], section_permissions:[]})
    Object.assign(newUser, {login:'',first_name:'',last_name:'',email:'',password:''})
  } catch(e) { saveMsg.value = 'Ошибка: '+(e.response?.data?.error||e.message); saveErr.value = true }
}

async function deleteUser(u, i) {
  if (!u.id) { data.value.users.splice(i,1); return }
  try { await api.delete(`/admin/customers/${editing.value}/users/`, {data:{id:u.id}}); data.value.users.splice(i,1) }
  catch(e) { saveMsg.value = 'Ошибка: '+(e.response?.data?.error||e.message); saveErr.value = true }
}

async function addKey() {
  if (!newKey.name) return
  try {
    const r = await api.post(`/admin/customers/${editing.value}/keys/`, {name:newKey.name})
    newKey.raw = r.data.raw_key
    data.value.api_keys.push({id:r.data.id, name:newKey.name, key_prefix:r.data.key_prefix, is_active:true, access_until:null, allowed_apps:[], ip_whitelist:'', llm_endpoint:''})
    newKey.name = ''
  } catch(e) { saveMsg.value = 'Ошибка: '+(e.response?.data?.error||e.message); saveErr.value = true }
}

async function deleteKey(k, i) {
  if (!k.id) { data.value.api_keys.splice(i,1); return }
  try { await api.delete(`/admin/customers/${editing.value}/keys/`, {data:{id:k.id}}); data.value.api_keys.splice(i,1) }
  catch(e) { saveMsg.value = 'Ошибка: '+(e.response?.data?.error||e.message); saveErr.value = true }
}

function addAccess() {
  if (!newAccess.app_code) return
  const app = allApps.value.find(a => a.code === newAccess.app_code)
  data.value.app_access.push({app_code:newAccess.app_code, app_name:app?.name||newAccess.app_code, brand_filter:'all', is_active:true, brands:[]})
  newAccess.app_code = ''
}

function addEmail() {
  if (!newEmail.email) return
  data.value.notification_emails.push({email_type:newEmail.type, email:newEmail.email, is_active:true})
  newEmail.email = ''
}

onMounted(load)
</script>

<style scoped>
.customer-admin{max-width:1100px;margin:0 auto;padding:20px}
.btn-primary{background:var(--site-primary,#2563eb);color:#fff;border:none;padding:8px 18px;border-radius:6px;cursor:pointer;font-size:14px;margin-bottom:16px}
.btn-sm{background:#10b981;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px}
.btn-sm-del{background:#ef4444;color:#fff;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:12px}
.cust-table{width:100%;border-collapse:collapse;margin-top:12px}
.cust-table th,.cust-table td{border:1px solid #e5e7eb;padding:8px 12px;text-align:left}
.cust-table th{background:#f9fafb}
.edit-form{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px}
.edit-form h3{margin-top:8px}
fieldset{border:1px solid #e5e7eb;border-radius:6px;padding:12px 16px;margin:12px 0}
fieldset legend{font-weight:600;padding:0 6px}
label{display:inline-block;margin-right:12px;margin-bottom:6px;font-size:13px}
input[type=text],input[type=date],input[type=password],select{border:1px solid #d1d5db;border-radius:4px;padding:4px 8px;font-size:13px}
.row,.new-row{padding:8px 0;border-bottom:1px solid #f3f4f6;display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.new-row{background:#f0fdf4}
.raw-key{background:#fef3c7;padding:2px 8px;border-radius:4px;font-family:monospace;font-size:12px}
.err{color:#dc2626}
</style>

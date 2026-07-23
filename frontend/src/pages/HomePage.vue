<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">Промышленное оборудование<br>для трубопроводной арматуры</h1>
        <p class="hero-subtitle">Подбор по параметрам, конфигураторы, сертификаты, документация — всё в одном месте</p>
        <div class="hero-actions">
          <router-link to="/catalog/gearbox" class="hero-btn hero-btn-primary">Перейти в каталог</router-link>
          <router-link to="/login" class="hero-btn hero-btn-outline">Войти</router-link>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-stats">
          <div class="hs-item"><span class="hs-num">10+</span><span class="hs-label">категорий</span></div>
          <div class="hs-item"><span class="hs-num">500+</span><span class="hs-label">моделей</span></div>
          <div class="hs-item"><span class="hs-num">10+</span><span class="hs-label">брендов</span></div>
        </div>
      </div>
    </section>

    <!-- Каталоги оборудования -->
    <section class="categories">
      <div class="section-header"><h2>Каталоги оборудования</h2></div>
      <div class="cat-grid">
        <router-link v-for="cat in catalogItems" :key="cat.to" :to="cat.to" class="cat-card">
          <div class="cat-img">
            <img v-if="cat.img" :src="cat.img" :alt="cat.name" class="cat-pic" @error="$event.target.style.display='none'" />
          </div>
          <h3 class="cat-name">{{ cat.name }}</h3>
        </router-link>
      </div>
    </section>

    <!-- Арматура -->
    <section class="categories">
      <div class="section-header"><h2>Арматура</h2></div>
      <div class="cat-grid">
        <router-link v-for="cat in valveItems" :key="cat.to" :to="cat.to" class="cat-card">
          <div class="cat-img">
            <img v-if="cat.img" :src="cat.img" :alt="cat.name" class="cat-pic" @error="$event.target.style.display='none'" />
          </div>
          <h3 class="cat-name">{{ cat.name }}</h3>
        </router-link>
      </div>
    </section>

    <!-- Готовые решения -->
    <section class="categories">
      <div class="section-header"><h2>Готовые решения</h2></div>
      <div class="cat-grid">
        <router-link v-for="cat in solutionItems" :key="cat.to" :to="cat.to" class="cat-card">
          <div class="cat-img">
            <img v-if="cat.img" :src="cat.img" :alt="cat.name" class="cat-pic" @error="$event.target.style.display='none'" />
          </div>
          <h3 class="cat-name">{{ cat.name }}</h3>
        </router-link>
      </div>
    </section>

    <!-- Возможности -->
    <section class="features">
      <div class="section-header"><h2>Возможности</h2></div>
      <div class="feat-grid">
        <div class="feat-card" v-for="f in features" :key="f.title">
          <span class="feat-icon">{{ f.icon }}</span>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <div class="cta-content">
        <h2>Не нашли нужное?</h2>
        <p>Отправьте заявку — подберём оборудование под ваш проект</p>
        <router-link to="/login" class="hero-btn hero-btn-primary">Войти в личный кабинет</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
function img(path) { return `/img/catalog/${path}` }

const catalogItems = [
  { to:'/catalog/pneumatic-fittings', label:'ПФ', name:'Пневмофитинги', color:'#3b82f6', img:img('pneumatic-fittings.webp') },
  { to:'/catalog/filter-regulator', label:'ФР', name:'Фильтр-регуляторы', color:'#0ea5e9', img:img('filter-regulator.webp') },
  { to:'/catalog/cable-glands', label:'КВ', name:'Кабельные вводы', color:'#06b6d4', img:img('cable-glands.webp') },
  { to:'/catalog/pa-actuators', label:'ПП', name:'Пневмоприводы', color:'#8b5cf6', img:img('pa-actuators.webp') },
  { to:'/catalog/gearbox', label:'РД', name:'Ручные дублёры', color:'#f59e0b', img:img('gearbox.webp') },
  { to:'/catalog/ea-reducers', label:'РЭ', name:'Редукторы к ЭП (проф)', color:'#ef4444', img:img('ea-reducers.webp') },
  { to:'/catalog/solenoid-valves', label:'СК', name:'Соленоидные клапаны', color:'#10b981', img:img('solenoid-valves.webp') },
  { to:'/catalog/positioners', label:'ЭПП', name:'Электропневматические позиционеры', color:'#6366f1', img:img('positioners.webp') },
  { to:'/catalog/limit-switch', label:'БКВ', name:'Блоки концевых выключателей', color:'#ec4899', img:img('limit-switch.webp') },
  { to:'/catalog/ea-actuators', label:'ЭП', name:'Электроприводы', color:'#f97316', img:img('ea-actuators.webp') },
  { to:'/catalog/ea-cabinets', label:'ШУ', name:'Шкафы управления ЭП (проф)', color:'#d97706', img:img('ea-cabinets.webp') },
  { to:'/catalog/mounting-kits', label:'МК', name:'Монтажные комплекты и адаптации (проф)', color:'#14b8a6', img:img('mounting-kits.webp') },
]

const valveItems = [
  { to:'/catalog/butterfly-valves', label:'ДЗ', name:'Дисковые затворы', color:'#2563eb', img:img('butterfly-valves.webp') },
  { to:'/catalog/ball-valves', label:'ШК', name:'Шаровые краны', color:'#7c3aed', img:img('ball-valves.webp') },
  { to:'/catalog/gate-valves', label:'КЗ', name:'Клиновые задвижки', color:'#dc2626', img:img('gate-valves.webp') },
  { to:'/catalog/knife-gate-valves', label:'ШЗ', name:'Шиберные задвижки', color:'#0891b2', img:img('knife-gate-valves.webp') },
]

const solutionItems = [
  { to:'/solutions/butterfly-ea', label:'ДЗ+ЭП', name:'Сборки Затворов дисковых с Электроприводами', color:'#1e40af', img:img('solutions/butterfly-ea.webp') },
  { to:'/solutions/butterfly-pa', label:'ДЗ+ПП', name:'Сборки Затворов дисковых с Пневмоприводами', color:'#1d4ed8', img:img('solutions/butterfly-pa.webp') },
  { to:'/solutions/ball-ea', label:'ШК+ЭП', name:'Сборки Кранов шаровых с Электроприводами', color:'#5b21b6', img:img('solutions/ball-ea.webp') },
  { to:'/solutions/ball-pa', label:'ШК+ПП', name:'Сборки Кранов шаровых с Пневмоприводами', color:'#6d28d9', img:img('solutions/ball-pa.webp') },
  { to:'/solutions/gate-pa', label:'КЗ+ПП', name:'Сборки Клиновых задвижек с Пневмоприводами', color:'#b91c1c', img:img('solutions/gate-pa.webp') },
  { to:'/solutions/gate-ea', label:'КЗ+ЭП', name:'Сборки Клиновых задвижек с Электроприводами', color:'#991b1b', img:img('solutions/gate-ea.webp') },
  { to:'/solutions/knife-ea', label:'ШЗ+ЭП', name:'Сборки Шиберных задвижек с Электроприводами', color:'#155e75', img:img('solutions/knife-ea.webp') },
  { to:'/solutions/knife-pa', label:'ШЗ+ПП', name:'Сборки Шиберных задвижек с Пневмоприводами', color:'#0e7490', img:img('solutions/knife-pa.webp') },
]

const features = [
  { icon:'🎯', title:'Подбор по параметрам', desc:'Фильтры по техническим характеристикам: давление, температура, материал, взрывозащита' },
  { icon:'⚙️', title:'Конфигураторы', desc:'Пошаговый подбор приводов, редукторов, шкафов управления и сборок' },
  { icon:'📜', title:'Сертификаты и документация', desc:'Паспорта, сертификаты соответствия, чертежи и инструкции' },
  { icon:'🤝', title:'Виджеты для партнёров', desc:'Встраивайте каталог на свой сайт — клиенты подбирают оборудование без ухода с вашей страницы' },
]
</script>

<style scoped>
/* Hero */
.hero{display:flex;align-items:center;justify-content:space-between;gap:48px;padding:48px 40px;background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);border-radius:16px;color:#fff;margin-bottom:48px}
.hero-content{flex:1;min-width:0}
.hero-title{font-size:36px;font-weight:800;line-height:1.2;margin:0 0 16px}
.hero-subtitle{font-size:16px;opacity:.85;margin:0 0 28px;line-height:1.5;max-width:520px}
.hero-actions{display:flex;gap:12px}
.hero-btn{display:inline-flex;align-items:center;padding:12px 28px;border-radius:8px;font-size:15px;font-weight:600;text-decoration:none;transition:all .15s}
.hero-btn-primary{background:#fff;color:#1e3a5f}
.hero-btn-primary:hover{background:#e5e7eb}
.hero-btn-outline{background:transparent;color:#fff;border:1.5px solid rgba(255,255,255,.4)}
.hero-btn-outline:hover{background:rgba(255,255,255,.1)}
.hero-visual{flex-shrink:0}
.hero-stats{display:flex;gap:32px}
.hs-item{text-align:center}
.hs-num{display:block;font-size:40px;font-weight:800;line-height:1}
.hs-label{display:block;font-size:13px;opacity:.7;margin-top:4px}

/* Sections */
.section-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:24px}
.section-header h2{font-size:24px;font-weight:700;color:#1f2937}

/* Category grid */
.categories{margin-bottom:48px}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}
.cat-card{display:flex;flex-direction:column;padding:0 0 12px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;text-decoration:none;transition:box-shadow .15s,border-color .15s,transform .15s;overflow:hidden}
.cat-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.08);border-color:#2563eb;transform:translateY(-2px)}
.cat-img{height:100px;display:flex;align-items:center;justify-content:center;margin-bottom:10px;position:relative;overflow:hidden;background:#f3f4f6}
.cat-pic{width:100%;height:100%;object-fit:contain;position:absolute;top:0;left:0}
.cat-name{font-size:13px;font-weight:600;color:#1f2937;margin:0;padding:0 10px;line-height:1.3;text-align:center}

/* Features */
.features{margin-bottom:48px}
.feat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.feat-card{padding:24px;background:#fff;border:1px solid #f3f4f6;border-radius:12px}
.feat-icon{font-size:32px;display:block;margin-bottom:12px}
.feat-card h3{font-size:15px;font-weight:600;color:#1f2937;margin:0 0 8px}
.feat-card p{font-size:13px;color:#6b7280;margin:0;line-height:1.5}

/* CTA */
.cta{background:#f9fafb;border-radius:16px;padding:48px;text-align:center;margin-bottom:48px}
.cta-content h2{font-size:28px;font-weight:700;color:#1f2937;margin:0 0 8px}
.cta-content p{font-size:16px;color:#6b7280;margin:0 0 24px}
.cta .hero-btn-primary{background:#2563eb;color:#fff}
.cta .hero-btn-primary:hover{background:#1d4ed8}
</style>

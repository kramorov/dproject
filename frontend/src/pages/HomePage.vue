<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">Каталог промышленного<br>оборудования</h1>
        <p class="hero-subtitle">Трубопроводная арматура, приводы, системы управления — подбор по параметрам, сертификаты, документация</p>
        <div class="hero-actions">
          <router-link to="/catalog/gearbox" class="hero-btn hero-btn-primary">Перейти в каталог</router-link>
          <router-link to="/catalog/filter-regulator" class="hero-btn hero-btn-outline">Все категории</router-link>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-stats">
          <div class="hs-item"><span class="hs-num">5+</span><span class="hs-label">категорий</span></div>
          <div class="hs-item"><span class="hs-num">100+</span><span class="hs-label">моделей</span></div>
          <div class="hs-item"><span class="hs-num">10+</span><span class="hs-label">брендов</span></div>
        </div>
      </div>
    </section>

    <!-- Категории -->
    <section class="categories">
      <div class="section-header">
        <h2>Каталог оборудования</h2>
        <router-link to="/catalog/gearbox" class="see-all">Смотреть все →</router-link>
      </div>
      <div class="cat-grid">
        <router-link v-for="cat in categories" :key="cat.to" :to="cat.to" class="cat-card">
          <span class="cat-icon">{{ cat.icon }}</span>
          <h3 class="cat-name">{{ cat.name }}</h3>
          <p class="cat-desc">{{ cat.desc }}</p>
          <span class="cat-count" v-if="cat.count">{{ cat.count }} товаров</span>
        </router-link>
      </div>
    </section>

    <!-- Возможности -->
    <section class="features">
      <div class="section-header"><h2>Возможности</h2></div>
      <div class="feat-grid">
        <div class="feat-card">
          <span class="feat-icon">🎯</span>
          <h3>Подбор по параметрам</h3>
          <p>Фильтры по техническим характеристикам: давление, температура, материал, взрывозащита</p>
        </div>
        <div class="feat-card">
          <span class="feat-icon">⚙️</span>
          <h3>Конфигуратор</h3>
          <p>Пошаговый подбор пневмо- и электроприводов под ваши задачи</p>
        </div>
        <div class="feat-card">
          <span class="feat-icon">📜</span>
          <h3>Сертификаты и документация</h3>
          <p>Паспорта, сертификаты соответствия, чертежи и инструкции по каждому оборудованию</p>
        </div>
        <div class="feat-card">
          <span class="feat-icon">🤝</span>
          <h3>Виджеты для партнёров</h3>
          <p>Встраивайте каталог на свой сайт — клиенты подбирают оборудование без ухода с вашей страницы</p>
        </div>
      </div>
    </section>

    <!-- Призыв к действию -->
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
const categories = [
  { to:'/catalog/gearbox', icon:'⚙️', name:'Ручные дублёры', desc:'Червячные, цилиндрические, конические редукторы', count:'12' },
  { to:'/catalog/filter-regulator', icon:'🔧', name:'Фильтр-регуляторы', desc:'Подготовка сжатого воздуха для пневмосистем', count:'8' },
  { to:'/catalog/limit-switch', icon:'🔌', name:'Блоки концевых выключателей', desc:'Механические, индуктивные, магнитные датчики', count:'15' },
  { to:'/catalog/solenoid-valves', icon:'🔀', name:'Распределительные клапаны', desc:'3/2, 5/2, 5/3 — управление пневмоприводами', count:'10' },
  { to:'/catalog/pneumatic-fittings', icon:'🔩', name:'Пневматические фитинги', desc:'Цанговые, обжимные, резьбовые соединения', count:'20' },
]
</script>

<style scoped>
/* ═══ Hero ═══ */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--cat-gap-4xl);
  padding: 48px 40px;
  background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
  border-radius: var(--cat-radius-2xl);
  color: #fff;
  margin-bottom: var(--cat-gap-3xl);
}
.hero-content { flex: 1; min-width: 0 }
.hero-title {
  font-size: 36px;
  font-weight: 800;
  line-height: 1.2;
  margin: 0 0 16px;
}
.hero-subtitle {
  font-size: var(--cat-text-lg);
  opacity: .85;
  margin: 0 0 28px;
  line-height: 1.5;
  max-width: 520px;
}
.hero-actions { display: flex; gap: var(--cat-gap-md) }
.hero-btn {
  display: inline-flex;
  align-items: center;
  padding: 12px 28px;
  border-radius: var(--cat-radius-md);
  font-size: var(--cat-text-base);
  font-weight: 600;
  text-decoration: none;
  transition: all .15s;
}
.hero-btn-primary { background: #fff; color: #1e3a5f }
.hero-btn-primary:hover { background: #e5e7eb }
.hero-btn-outline { background: transparent; color: #fff; border: 1.5px solid rgba(255,255,255,.4) }
.hero-btn-outline:hover { background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.6) }
.hero-visual { flex-shrink: 0 }
.hero-stats { display: flex; gap: 32px }
.hs-item { text-align: center }
.hs-num { display: block; font-size: 40px; font-weight: 800; line-height: 1 }
.hs-label { display: block; font-size: var(--cat-text-sm); opacity: .7; margin-top: 4px }

/* ═══ Sections ═══ */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--cat-gap-xl);
}
.section-header h2 {
  font-size: var(--cat-text-3xl);
  font-weight: 700;
  color: var(--cat-text);
}
.see-all {
  font-size: var(--cat-text-base);
  color: var(--cat-primary);
  text-decoration: none;
  font-weight: 500;
}
.see-all:hover { text-decoration: underline }

/* ═══ Categories ═══ */
.categories { margin-bottom: var(--cat-gap-4xl) }
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--cat-gap-lg);
}
.cat-card {
  display: flex;
  flex-direction: column;
  padding: var(--cat-gap-2xl) var(--cat-gap-xl);
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-xl);
  text-decoration: none;
  transition: box-shadow .15s, border-color .15s, transform .15s;
}
.cat-card:hover {
  box-shadow: var(--cat-shadow-card-hover);
  border-color: var(--cat-primary);
  transform: translateY(-2px);
}
.cat-icon { font-size: 36px; margin-bottom: var(--cat-gap-md) }
.cat-name { font-size: var(--cat-text-md); font-weight: 600; color: var(--cat-text); margin: 0 0 6px }
.cat-desc { font-size: var(--cat-text-sm); color: var(--cat-muted); margin: 0 0 auto; line-height: 1.4 }
.cat-count { font-size: var(--cat-text-xs); color: var(--cat-primary); margin-top: var(--cat-gap-md); font-weight: 500 }

/* ═══ Features ═══ */
.features { margin-bottom: var(--cat-gap-4xl) }
.feat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--cat-gap-lg);
}
.feat-card {
  padding: var(--cat-gap-2xl);
  background: var(--cat-surface);
  border: 1px solid var(--cat-border-light);
  border-radius: var(--cat-radius-xl);
}
.feat-icon { font-size: 32px; display: block; margin-bottom: var(--cat-gap-md) }
.feat-card h3 { font-size: var(--cat-text-md); font-weight: 600; color: var(--cat-text); margin: 0 0 8px }
.feat-card p { font-size: var(--cat-text-sm); color: var(--cat-muted); margin: 0; line-height: 1.5 }

/* ═══ CTA ═══ */
.cta {
  background: var(--cat-bg);
  border-radius: var(--cat-radius-xl);
  padding: 40px;
  text-align: center;
  margin-bottom: var(--cat-gap-3xl);
}
.cta-content h2 { font-size: var(--cat-text-2xl); font-weight: 700; color: var(--cat-text); margin: 0 0 8px }
.cta-content p { font-size: var(--cat-text-base); color: var(--cat-muted); margin: 0 0 20px }
.cta-content .hero-btn-primary { background: var(--cat-primary); color: #fff }
.cta-content .hero-btn-primary:hover { background: var(--cat-primary-hover) }

/* ═══ Responsive ═══ */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
    padding: 32px 24px;
  }
  .hero-title { font-size: 26px }
  .hero-subtitle { max-width: 100% }
  .hero-actions { justify-content: center; flex-wrap: wrap }
  .hero-stats { gap: 20px }
  .hs-num { font-size: 28px }
  .cat-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)) }
  .feat-grid { grid-template-columns: 1fr }
}
</style>
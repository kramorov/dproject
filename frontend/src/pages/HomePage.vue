<!-- pages/HomePage.vue — главная страница -->
<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">Агрегатор технической информации<br>Трубопроводная арматура и управление арматурой</h1>
        <p class="hero-subtitle">Подбор по параметрам, конфигураторы, сертификаты, документация — всё в одном месте</p>
<!--        <div class="hero-actions">-->
<!--          <router-link to="/catalogs/equipment" class="hero-btn hero-btn-primary">Перейти в каталог</router-link>-->
<!--          <router-link to="/login" class="hero-btn hero-btn-outline">Войти</router-link>-->
<!--        </div>-->
      </div>
      <div class="hero-visual">
        <div class="hero-stats">
          <div class="hs-item"><span class="hs-num">10+</span><span class="hs-label">категорий</span></div>
          <div class="hs-item"><span class="hs-num">500+</span><span class="hs-label">моделей</span></div>
          <div class="hs-item"><span class="hs-num">10+</span><span class="hs-label">брендов</span></div>
        </div>
      </div>
    </section>

    <!-- О проекте -->
    <section class="hp-about">
      <router-link to="/about" class="hp-about-card">
        <div class="hp-about-bg"></div>
        <div class="hp-about-body">
          <h2>О проекте</h2>
          <p>Агрегатор технической информации: умный поиск, подбор, КП, документация. Узнайте о возможностях и преимуществах системы.</p>
          <span class="hp-about-link">Подробнее →</span>
        </div>
      </router-link>
    </section>

    <!-- Каталоги — 3 плитки в ряд -->
    <section class="hp-catalogs">
      <h2>Каталоги</h2>
      <div class="hp-cat-grid">
        <router-link to="/catalogs/equipment" class="hp-cat-tile hp-cat-eq">
          <div class="hp-cat-bg"></div>
          <div class="hp-cat-body">
            <h3>Каталоги оборудования</h3>
            <p>Пневмофитинги, фильтр-регуляторы, кабельные вводы, пневмоприводы, дублёры, клапаны, позиционеры, БКВ, электроприводы, шкафы управления, монтажные комплекты</p>
          </div>
        </router-link>
        <router-link to="/catalogs/valves" class="hp-cat-tile hp-cat-va">
          <div class="hp-cat-bg"></div>
          <div class="hp-cat-body">
            <h3>Каталоги арматуры</h3>
            <p>Дисковые затворы, шаровые краны, клиновые и шиберные задвижки</p>
          </div>
        </router-link>
        <router-link to="/catalogs/solutions" class="hp-cat-tile hp-cat-so">
          <div class="hp-cat-bg"></div>
          <div class="hp-cat-body">
            <h3>Каталог готовых решений</h3>
            <p>Сборки арматуры с пневмо- и электроприводами: затворы, краны, задвижки</p>
          </div>
        </router-link>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <div class="cta-content">
<!--        <h2>Не нашли нужное?</h2>-->
<!--        <p>Отправьте заявку — подберём оборудование под ваш проект</p>-->
        <router-link to="/login" class="hero-btn hero-btn-primary">Войти в личный кабинет</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
// No data needed — all content is static
</script>

<style scoped>
/* === Hero === */
.home-page { max-width: 1440px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; padding: 48px 0; gap: 40px; margin-bottom: 32px; }
.hero-content { flex: 1; min-width: 0; }
.hero-title { font-size: 36px; font-weight: 800; color: #1f2937; line-height: 1.2; margin: 0 0 16px; }
.hero-subtitle { font-size: 17px; color: #6b7280; line-height: 1.5; margin: 0 0 24px; }
.hero-actions { display: flex; gap: 12px; }
.hero-btn { padding: 10px 24px; border-radius: 8px; font-size: 15px; font-weight: 600; text-decoration: none; transition: all .15s; }
.hero-btn-primary { background: #2563eb; color: #fff; }
.hero-btn-primary:hover { background: #1d4ed8; }
.hero-btn-outline { border: 1px solid #d1d5db; color: #374151; }
.hero-btn-outline:hover { border-color: #2563eb; color: #2563eb; }
.hero-stats { display: flex; gap: 32px; }
.hs-item { text-align: center; }
.hs-num { display: block; font-size: 40px; font-weight: 800; line-height: 1; color: #1f2937; }
.hs-label { display: block; font-size: 13px; color: #6b7280; margin-top: 4px; }

/* === About block === */
.hp-about { margin-bottom: 36px; }
.hp-about-card {
  position: relative; display: block; border-radius: 16px; overflow: hidden;
  text-decoration: none; min-height: 120px; isolation: isolate;
  transition: transform .25s, box-shadow .25s;
}
.hp-about-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.1); }
.hp-about-bg {
  position: absolute; inset: 0; z-index: 0;
  background: linear-gradient(135deg, #1e1b4b 0%, #3730a3 100%);
}
.hp-about-bg::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle at 20% 50%, rgba(168,85,247,0.2) 0%, transparent 50%),
              radial-gradient(circle at 80% 50%, rgba(99,102,241,0.15) 0%, transparent 50%);
}
.hp-about-body {
  position: relative; z-index: 1;
  padding: 28px 32px;
  display: flex; flex-direction: column; justify-content: center;
}
.hp-about-body h2 { font-size: 20px; font-weight: 700; color: #fff; margin: 0 0 6px; }
.hp-about-body p { font-size: 14px; color: rgba(255,255,255,0.7); margin: 0 0 8px; line-height: 1.5; max-width: 600px; }
.hp-about-link { font-size: 13px; color: #a855f7; font-weight: 600; }

/* === Catalog tiles === */
.hp-catalogs { margin-bottom: 36px; }
.hp-catalogs h2 { font-size: 20px; font-weight: 700; color: #1f2937; margin: 0 0 16px; }
.hp-cat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.hp-cat-tile {
  position: relative; display: flex; flex-direction: column; justify-content: flex-end;
  min-height: 200px; border-radius: 16px; overflow: hidden;
  text-decoration: none; isolation: isolate;
  transition: transform .25s, box-shadow .25s;
}
.hp-cat-tile:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
.hp-cat-bg { position: absolute; inset: 0; z-index: 0; }
.hp-cat-body {
  position: relative; z-index: 1; padding: 20px 22px;
  background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.7) 100%);
}
.hp-cat-body h3 { font-size: 16px; font-weight: 700; color: #fff; margin: 0 0 4px; }
.hp-cat-body p { font-size: 12px; color: rgba(255,255,255,0.7); margin: 0; line-height: 1.4; }

/* Tile backgrounds */
.hp-cat-eq .hp-cat-bg {
  background: linear-gradient(135deg, #3b0764 0%, #7c3aed 100%),
              radial-gradient(circle at 30% 70%, rgba(168,85,247,0.3) 0%, transparent 40%);
}
.hp-cat-eq .hp-cat-bg::after {
  content: ''; position: absolute; top: 24px; right: 20px;
  width: 70px; height: 70px; border: 2px solid rgba(255,255,255,0.1); border-radius: 50%;
  box-shadow: 0 0 0 18px rgba(255,255,255,0.04), 0 0 0 36px rgba(255,255,255,0.02);
}
.hp-cat-va .hp-cat-bg {
  background: linear-gradient(135deg, #042f2e 0%, #0f766e 100%),
              radial-gradient(circle at 70% 30%, rgba(20,184,166,0.25) 0%, transparent 40%);
}
.hp-cat-va .hp-cat-bg::after {
  content: ''; position: absolute; top: 24px; right: 24px;
  width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.4);
  box-shadow: -28px 12px 0 rgba(255,255,255,0.2), -56px -4px 0 rgba(255,255,255,0.12);
}
.hp-cat-so .hp-cat-bg {
  background: linear-gradient(135deg, #451a03 0%, #b45309 100%),
              repeating-linear-gradient(180deg, transparent, transparent 12px, rgba(255,255,255,0.04) 12px, rgba(255,255,255,0.04) 14px);
}
.hp-cat-so .hp-cat-bg::after {
  content: ''; position: absolute; left: 20px; bottom: 45%;
  width: 40px; height: 5px; border-radius: 3px; background: rgba(255,255,255,0.15);
  box-shadow: 0 14px 0 rgba(255,255,255,0.08), 0 28px 0 rgba(255,255,255,0.04);
}

/* === CTA === */
.cta { background: #f9fafb; border-radius: 16px; padding: 40px; text-align: center; }
.cta-content h2 { font-size: 24px; font-weight: 700; color: #1f2937; margin: 0 0 8px; }
.cta-content p { font-size: 15px; color: #6b7280; margin: 0 0 20px; }
.cta .hero-btn-primary { background: #2563eb; color: #fff; }
.cta .hero-btn-primary:hover { background: #1d4ed8; }

@media (max-width: 768px) {
  .hero { flex-direction: column; text-align: center; }
  .hero-stats { justify-content: center; }
  .hp-cat-grid { grid-template-columns: 1fr; }
  .hp-cat-tile { min-height: 140px; }
}
</style>

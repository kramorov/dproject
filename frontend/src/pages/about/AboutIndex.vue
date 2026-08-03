<!-- pages/about/AboutIndex.vue — главная страница раздела «О проекте» -->
<template>
  <div class="about-index">
    <span class="debug-tag">AboutIndex</span>

    <Breadcrumbs :items="breadcrumbs" />

    <!-- Intro -->
    <section class="ai-intro">
      <h1 class="ai-title">О проекте</h1>
      <p class="ai-mission">
        <strong>Агрегатор технической информации:</strong> лёгкость получения технической информации,
        умный поиск оборудования, быстрое получение информации об остатках и ценах,
        формирование пакета документов для клиентов. Переход на возможность для покупателей
        делать закупки через ИИ-агентов.
      </p>
    </section>

    <!-- Эффективность — выделенный бокс -->
    <section class="ai-efficiency">
      <div class="ai-eff-box">
        <div class="ai-eff-badge">Эффективность</div>
        <div class="ai-eff-grid">
          <div class="ai-eff-col">
            <h3>Продавать</h3>
            <ul>
              <li>Как можно больше</li>
              <li>Как можно дороже</li>
              <li>Как можно чаще</li>
              <li>Как можно большему количеству клиентов</li>
            </ul>
          </div>
          <div class="ai-eff-col ai-eff-col-cost">
            <h3>Затрачивая меньше ресурсов на</h3>
            <ul>
              <li>Маркетинг, рекламу и техдокументацию</li>
              <li>Подготовку КП</li>
              <li>Комплектацию</li>
              <li>Изготовление</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- Разделы — сетка 2×2 с фонами -->
    <section class="ai-sections">
      <h2>Разделы</h2>
      <div class="ai-grid">
        <router-link to="/about/architecture" class="ai-tile ai-tile-arch">
          <div class="ai-tile-bg"></div>
          <div class="ai-tile-body">
            <span class="ai-tile-label">01</span>
            <h3>Архитектура системы и основные понятия</h3>
            <p>ИТ-продукты, ролевая модель участников, терминология BOM</p>
          </div>
        </router-link>
        <router-link to="/about/capabilities" class="ai-tile ai-tile-cap">
          <div class="ai-tile-bg"></div>
          <div class="ai-tile-body">
            <span class="ai-tile-label">02</span>
            <h3>Возможности системы</h3>
            <p>Каталог, поиск, КП, инженерные инструменты, ИИ-модуль, интеграции</p>
          </div>
        </router-link>
        <router-link to="/about/benefits-users" class="ai-tile ai-tile-bu">
          <div class="ai-tile-bg"></div>
          <div class="ai-tile-body">
            <span class="ai-tile-label">03</span>
            <h3>Преимущества для пользователей</h3>
            <p>Что получают производители, инжиниринговые компании, дилеры, партнёры, потребители</p>
          </div>
        </router-link>
        <router-link to="/about/benefits-types" class="ai-tile ai-tile-bt">
          <div class="ai-tile-bg"></div>
          <div class="ai-tile-body">
            <span class="ai-tile-label">04</span>
            <h3>Преимущества по типам потребителей</h3>
            <p>Сводная таблица: преимущество и его суть для каждого типа</p>
          </div>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'

const breadcrumbs = [
  { name: 'Главная', to: '/' },
  { name: 'О проекте' },
]
</script>

<style scoped>
.about-index { max-width: 860px; margin: 0 auto; }

/* === Intro === */
.ai-intro { margin-bottom: 24px; }
.ai-title { font-size: 28px; font-weight: 800; color: var(--cat-text, #1f2937); margin: 0 0 10px; }
.ai-mission { font-size: 15px; line-height: 1.55; color: var(--cat-text-secondary, #4b5563); margin: 0; }

/* === Efficiency box === */
.ai-efficiency { margin-bottom: 32px; }
.ai-eff-box {
  position: relative;
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #3730a3 100%);
  border-radius: 20px;
  padding: 38px 30px 26px;
  box-shadow: 0 8px 40px rgba(55,48,163,0.25);
  overflow: hidden;
}
.ai-eff-box::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(168,85,247,0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(99,102,241,0.18) 0%, transparent 50%),
    linear-gradient(45deg, transparent 48%, rgba(255,255,255,0.03) 48%, rgba(255,255,255,0.03) 52%, transparent 52%),
    linear-gradient(-45deg, transparent 48%, rgba(255,255,255,0.02) 48%, rgba(255,255,255,0.02) 52%, transparent 52%);
  background-size: 100% 100%, 100% 100%, 60px 60px, 60px 60px;
  pointer-events: none;
}
.ai-eff-badge {
  position: absolute;
  top: 10px; left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #a855f7, #7c3aed);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 6px 24px;
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(124,58,237,0.4);
}
.ai-eff-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  position: relative;
  z-index: 1;
}
.ai-eff-col h3 {
  font-size: 15px; font-weight: 700;
  color: rgba(255,255,255,0.9);
  margin: 0 0 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.12);
}
.ai-eff-col ul { margin: 0; padding: 0; list-style: none; }
.ai-eff-col li {
  font-size: 14px; color: rgba(255,255,255,0.7);
  padding: 5px 0;
  display: flex; align-items: center; gap: 8px;
}
.ai-eff-col li::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #a855f7;
  flex-shrink: 0;
}
.ai-eff-col-cost li::before { background: #f59e0b; }

/* === Sections grid 2×2 === */
.ai-sections { margin-bottom: 24px; }
.ai-sections h2 { font-size: 20px; font-weight: 700; color: var(--cat-text, #1f2937); margin: 0 0 14px; }
.ai-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.ai-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 170px;
  border-radius: 16px;
  overflow: hidden;
  text-decoration: none;
  transition: transform 0.25s, box-shadow 0.25s;
  isolation: isolate;
}
.ai-tile:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.ai-tile-bg {
  position: absolute; inset: 0; z-index: 0;
}
.ai-tile-body {
  position: relative; z-index: 1;
  padding: 18px 20px;
  background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.05) 40%, rgba(0,0,0,0.65) 100%);
}
.ai-tile-label {
  display: inline-block;
  font-size: 11px; font-weight: 700;
  color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.12);
  padding: 2px 10px; border-radius: 10px;
  margin-bottom: 10px;
}
.ai-tile-body h3 { font-size: 16px; font-weight: 700; color: #fff; margin: 0 0 4px; }
.ai-tile-body p { font-size: 13px; color: rgba(255,255,255,0.75); margin: 0; line-height: 1.4; }

/* Tile backgrounds — CSS-only illustrations */
.ai-tile-arch .ai-tile-bg {
  background:
    linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%),
    repeating-linear-gradient(0deg, transparent, transparent 4px, rgba(255,255,255,0.03) 4px, rgba(255,255,255,0.03) 5px),
    repeating-linear-gradient(90deg, transparent, transparent 4px, rgba(255,255,255,0.03) 4px, rgba(255,255,255,0.03) 5px);
}
.ai-tile-arch .ai-tile-bg::after {
  content: ''; position: absolute; top: 20px; right: 20px;
  width: 80px; height: 80px;
  border: 2px solid rgba(255,255,255,0.08);
  border-radius: 50%;
  box-shadow:
    0 0 0 20px rgba(255,255,255,0.03),
    0 0 0 40px rgba(255,255,255,0.02);
}

.ai-tile-cap .ai-tile-bg {
  background:
    linear-gradient(135deg, #3b0764 0%, #6b21a8 100%),
    radial-gradient(circle at 30% 70%, rgba(168,85,247,0.3) 0%, transparent 40%),
    radial-gradient(circle at 70% 30%, rgba(139,92,246,0.2) 0%, transparent 40%);
}
.ai-tile-cap .ai-tile-bg::before {
  content: ''; position: absolute; top: 16px; right: 16px;
  width: 60px; height: 60px;
  border: 2px solid rgba(255,255,255,0.1);
  border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
}
.ai-tile-cap .ai-tile-bg::after {
  content: ''; position: absolute; bottom: 20px; left: 20px;
  width: 50px; height: 50px;
  border: 2px solid rgba(255,255,255,0.07);
  border-radius: 50%;
}

.ai-tile-bu .ai-tile-bg {
  background:
    linear-gradient(135deg, #042f2e 0%, #0f766e 100%),
    radial-gradient(circle at 25% 60%, rgba(20,184,166,0.25) 0%, transparent 35%),
    radial-gradient(circle at 75% 40%, rgba(45,212,191,0.15) 0%, transparent 40%);
}
.ai-tile-bu .ai-tile-bg::before {
  content: ''; position: absolute;
  top: 25%; right: 20px; width: 8px; height: 8px; border-radius: 50%;
  background: rgba(255,255,255,0.4);
  box-shadow:
    -30px 15px 0 rgba(255,255,255,0.25),
    -60px -5px 0 rgba(255,255,255,0.15),
    -20px -30px 0 rgba(255,255,255,0.2);
}

.ai-tile-bt .ai-tile-bg {
  background:
    linear-gradient(135deg, #451a03 0%, #92400e 100%),
    repeating-linear-gradient(180deg,
      transparent, transparent 14px,
      rgba(255,255,255,0.04) 14px, rgba(255,255,255,0.04) 16px);
}
.ai-tile-bt .ai-tile-bg::after {
  content: ''; position: absolute; left: 16px; bottom: 40%;
  width: 50px; height: 6px; border-radius: 3px;
  background: rgba(255,255,255,0.15);
  box-shadow:
    0 18px 0 rgba(255,255,255,0.08),
    0 36px 0 rgba(255,255,255,0.05);
}

@media (max-width: 768px) {
  .ai-eff-grid { grid-template-columns: 1fr; }
  .ai-grid { grid-template-columns: 1fr; }
  .ai-tile { min-height: 150px; }
}
</style>

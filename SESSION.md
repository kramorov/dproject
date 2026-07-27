# SESSION.md — 2026-07-27

## Где остановились

Две фазы пайплайна работают: decompose строит дерево типов, extract извлекает параметры для каждого узла. Extract вызывается автоматически внутри decompose.

Decompose v4 (минимальный) + extract-промпты для 9 типов оборудования созданы и привязаны к PipelineSkills через конфигуратор.

## Что работает

- **Decompose** — `POST /decompose/` → дерево (`id`, `type`, `depends_on`, `quantity`) + auto-extract
- **Extract** — вызывается из decompose для всех узлов с `equipment_type`, результаты в `data.extracted`
- **Pipeline Configurator** — `/admin/pipeline-config`: 5 вкладок CRUD, 3 режима JSON (Tree/Table/Raw), селекторы для Equipment Type, Schema, Model Role
- **Классификатор** — 9 интентов, роутинг в DecomposeView
- **Прогресс-бар** — компонент `ProgressBar.vue`, текст «Анализ и подбор параметров», расчёт времени из статистики скилла
- **Логирование** — `AITokenUsage.customer`, `latency_ms`, `PipelineSkill.avg_latency_ms`
- **Маршрутизация** — `resolve_customer()`: source → ProjectCustomer (anonymous_web, email, api_key)
- **45 тестов**, 15 миграций

## Что нужно доделать

- [ ] Фазы 3-5 (filter → select → compare) — не реализованы, только скелет в tree_processor
- [ ] Decompose промпт галлюцинирует при нестандартных запросах — нужно улучшить анти-галлюцинационные правила
- [ ] Extract промпты написаны для 9 типов, но не оттестированы на реальных данных
- [ ] Улучшить decompose-промпт: для электропривода — извлекать features (limit_switches, etc.)
- [ ] `mounting-kit` EquipmentType не создан в core
- [ ] Reverse-миграция core.0004 требует внимания
- [ ] Разметить 8 AIQuerySample для регрессионного тестирования
- [ ] Наполнить каталоги реальным контентом
- [ ] Конфигураторы сборок арматуры + приводов
- [ ] Заявки клиентов (client_requests)

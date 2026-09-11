# Кабельные вводы — мини-приложение каталога (Vue 3)

Просмотр каталога кабельных вводов: по сериям, инженерный подбор, быстрый подбор, мастер подбора, AI-подбор.

**Стек:** Vue 3 `<script setup>`, Vite 6.

## Страницы

- **Просмотр по сериям** (`CatalogSection`) — сетка серий (выводится из списка, серия = `model_line`).
- **Инженерный подбор** (`EngineerSelection`) — фильтры + карточки.
- **Детальная** (`CatalogDetail`) — галерея, характеристики, документы, сертификаты.
- **Серия** (`CatalogModelLine`) — товары внутри серии.
- **Быстрый подбор** (`QuickSelect`) — чипсы (резьба, материал, Exd, IP, диаметр кабеля, температура).
- **Мастер подбора** (`WizardSelection`) — `equipment_type_id=12`.
- **AI-подбор** (`AiSelectionPage`) — `equipment-code="cable-gland"`.

## API

| Метод | URL |
|-------|-----|
| GET | `/api/cable-glands/catalog/` |
| GET | `/api/cable-glands/catalog/<id>/` |
| GET | `/api/cable-glands/filters/` |
| GET | `/api/cable-glands/engineer/` |
| GET | `/api/cable-glands/engineer/filters/` |
| GET | `/api/cable-glands/quickselect/` |
| GET | `/api/cable-glands/meta/` |

## Подключение

1. `cable_glands/urls.py` → каталоговые эндпоинты (уже добавлены).
2. `frontend/vite.config.js` → `'cable-gland-catalog': resolve(__dirname, 'src/apps/cable-gland-catalog/index.html')`.
3. `frontend/src/shared/endpoints.js` → `ENDPOINTS.cableGlands`.

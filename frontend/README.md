# Frontend — структура проекта

Vue 3 + Vite + Pinia. Мини-приложения в `src/apps/`, переиспользуемое в `src/shared/`.

---

## `src/shared/` — общие модули (проанализировано, 2026-05-18)

| Путь | Назначение |
|------|-----------|
| `shared/config.js` | API_URL, API_PREFIX |
| `shared/api.js` | Axios-инстанс с перехватчиком ошибок |
| `shared/components/BaseButton.vue` | Кнопка (primary/danger, loading-спиннер) |
| `shared/components/BaseModal.vue` | Модальное окно (show/title/close/slot) |

---

## `src/apps/media-library/` — мини-приложение «Медиабиблиотека» (создано 2026-05-18)

| Путь | Назначение |
|------|-----------|
| `index.html` | Точка сборки Vite (multi-page) |
| `main.js` | `createApp(App).mount('#media-app')` |
| `App.vue` | Корень: хедер, переключение грид/загрузка, модалка редактирования |
| `api.js` | API-вызовы: upload, update, patch, replaceFile, remove, list, detail |
| `components/MediaGrid.vue` | Сетка карточек + фильтры (поиск, категория) |
| `components/MediaUpload.vue` | Drag&drop загрузка + форма (название, категория, keywords…) |
| `components/MediaEdit.vue` | Модалка: редактирование полей, замена файла, удаление |

Мини-приложение автономно: не зависит от `router/`, `App.vue`, `services/`.  
Сборка: `vite build` → отдельный HTML/JS/CSS.  
Dev: `npm run dev`, открыть `/src/apps/media-library/index.html`.

---

## `src/` — корень (проанализировано выборочно)

| Путь | Статус | Назначение |
|------|--------|-----------|
| `main.js` | Проанализирован | Точка входа SPA: Pinia, router, axiosPlugin → `#app` |
| `App.vue` | Проанализирован | Общий layout: header + `<router-view>` + индикатор загрузки |
| `App2.vue` | Не просмотрен | Вариант App |
| `App_old.vue` | Не просмотрен | Старый вариант App |
| `style.css` | Не просмотрен | Глобальные стили |
| `w3.css` | Не просмотрен | W3.CSS framework |

---

## `src/components/` — общие компоненты (выборочно)

| Путь | Статус | Назначение |
|------|--------|-----------|
| `AppLayout.vue` | Не просмотрен | Общий layout-контейнер |
| `AppButton.vue` | Проанализирован | Кнопка с иконкой (Options API) |
| `AppActionButton.vue` | Не просмотрен | Кнопка действия |
| `SortableTable.vue` | Не просмотрен | Таблица с сортировкой |
| `UnsortedTable.vue` | Не просмотрен | Таблица без сортировки |
| `UnsortedTableItem.vue` | Не просмотрен | Строка таблицы |
| `OldSortedTable.vue` | Не просмотрен | Старая таблица |
| `ParamValueTable.vue` | Не просмотрен | Таблица параметров |
| `EditModal.vue` | Проанализирован | Модалка редактирования (Options API, завязана на «материалы») |
| `EditListItem.vue` | Не просмотрен | Редактирование элемента списка |
| `ErrorModal.vue` | Проанализирован | Модалка ошибки (Options API) |
| `GetUrl.vue` | Не просмотрен | Получение URL |
| `Icon.vue` | Не просмотрен | Компонент иконки |
| `MountingPlates.vue` | Не просмотрен | Монтажные пластины |
| `ActuatorEdit.vue` | Не просмотрен | Редактор привода (v1) |
| `ActuatorEdit1.vue` | Не просмотрен | Редактор привода (v2) |
| `Dictionary.vue` | Не просмотрен | Компонент словаря |
| `RightSidebar.vue` | Не просмотрен | Боковая панель |
| `HelloWorld.vue` | Не просмотрен | Заглушка |

### `src/components/header/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `Header.vue` | Не просмотрен | Шапка |
| `Logo.vue` | Не просмотрен | Логотип |
| `TopMenu.vue` | Не просмотрен | Верхнее меню |
| `Auth.vue` | Не просмотрен | Блок авторизации |

### `src/components/cable_glands/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `CableGlandItemType.vue` | Не просмотрен | Тип кабельного ввода |
| `CableGlandItemEditForm.vue` | Не просмотрен | Форма редактирования |
| `CgTypeAdapterForm.vue` | Не просмотрен | Форма адаптера |
| `CgTypeCableGlandForm.vue` | Не просмотрен | Форма кабельного ввода |
| `CgTypeGroundRingForm.vue` | Не просмотрен | Форма кольца заземления |
| `CgTypePlugForm.vue` | Не просмотрен | Форма заглушки |

### `src/components/client_requests/`

Пустая директория. Компоненты заявок лежат в `src/pages/client_request/`.

### `src/components/ett/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `EttDecodePage.vue` | Не просмотрен | Страница декодирования ETT |

---

## `src/pages/` — страницы (выборочно)

| Путь | Статус | Назначение |
|------|--------|-----------|
| `HomePage.vue` | Не просмотрен | Главная страница |
| `AboutPage.vue` | Не просмотрен | О проекте |
| `NewPage.vue` | Не просмотрен | Новая страница |

### `src/pages/electric_actuators/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `ActualActuatorEditPage.vue` | Не просмотрен | Редактор подобранного привода |
| `ActuatorList.vue` | Не просмотрен | Список приводов |
| `DriveDataMainPage.vue` | Не просмотрен | Данные привода |
| `DriveSelectionPage.vue` | Не просмотрен | Подбор привода |

### `src/pages/cable_glands/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `CableGlandBodyMaterial.vue` | Не просмотрен | Материалы корпуса |
| `CableGlandEditPage.vue` | Не просмотрен | Редактор кабельного ввода |
| `CableMainPage.vue` | Не просмотрен | Главная кабельных вводов |

### `src/pages/client_request/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `ClientRequestMainPage.vue` | Не просмотрен | Главная заявок |
| `ClientRequestDetail.vue` | Не просмотрен | Детали заявки |
| `ClientRequestEditPage.vue` | Не просмотрен | Редактор заявки |
| `ClientRequestForm.vue` | Не просмотрен | Форма заявки |
| `ClientRequestForm_old.vue` | Не просмотрен | Старая форма |
| `ClientRequestItem.vue` | Не просмотрен | Элемент заявки |
| `ClientRequestType.vue` | Не просмотрен | Тип заявки |
| `RequestLineItem.vue` | Не просмотрен | Строка заявки |
| `ClientRequest.vue` | Не просмотрен | Заявка |
| `ClientRequest_before.vue` | Не просмотрен | Старая версия |
| `scenario.txt` | Не просмотрен | Сценарий |
| `components/` | Не просмотрен | Вложенные компоненты |

### `src/pages/adaptation/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `AdaptationMainPage.vue` | Не просмотрен | Страница адаптации |

### `src/pages/auth/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `LoginMainPage.vue` | Не просмотрен | Страница входа |
| `RegisterMainPage.vue` | Не просмотрен | Страница регистрации |

---

## `src/router/` (проанализирован)

| Путь | Статус | Назначение |
|------|--------|-----------|
| `index.js` | Проанализирован | Все маршруты SPA в одном файле |

---

## `src/services/` (выборочно)

| Путь | Статус | Назначение |
|------|--------|-----------|
| `api.js` | Проанализирован | Axios-инстанс + доменные API-функции (EA, params…) |
| `axios.js` | Проанализирован | Плагин axios для Options API |
| `apiErrorHandler.js` | Проанализирован | Обработчик ошибок сети/сервера |
| `store.js` | Не просмотрен | Хранилище (Pinia/Vuex) |
| `GlobalDataLoader.vue` | Не просмотрен | Глобальный загрузчик данных |
| `stores/dictionaryStore.ts` | Не просмотрен | Хранилище словарей (Pinia) |
| `stores/models.ts` | Не просмотрен | Модели данных |

---

## `src/composables/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `useHttp.js` | Не просмотрен | Composable для HTTP-запросов |

---

## `src/config/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `api.js` | Проанализирован | `API_URL = 'http://localhost:8000'` |

---

## `src/views/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `HomeView.vue` | Не просмотрен | Home view |

---

## `src/assets/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `icons/` | Не просмотрен | Иконки |
| `vue.svg` | Не просмотрен | Логотип Vue |

---

## Корень `frontend/`

| Путь | Статус | Назначение |
|------|--------|-----------|
| `index.html` | Проанализирован | Точка входа SPA: `<div id="app">` |
| `vite.config.js` | Обновлён (2026-05-18) | Multi-page build: `main` + `media-library`, proxy `/api` → Django |
| `package.json` | Проанализирован | vue 3.5, vite 6, @vitejs/plugin-vue 5 |
| `tsconfig.json` | Не просмотрен | Конфигурация TypeScript |
| `README.md` | Этот файл | — |

---

---

## Инструкция: создание нового каталога

Все каталоги используют унифицированные Generic-компоненты из `shared/components/catalog/`. Для добавления нового каталога (например, `electric_actuators`):

### 1. Создать директорию `src/apps/electric-actuator-catalog/`

### 2. `api.js` — API-клиент

```js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'
const E = ENDPOINTS.electricActuator
export default {
  list(params)        { return api.get(E.catalog, { params }) },
  getDetail(id)       { return api.get(E.detail(id)) },
  getFilters()        { return api.get(E.filters) },
  getQuickSelect(mlId, f = {}) { return api.get(E.quickselect, { params: { model_line_id: mlId, ...f } }) },
}
```

### 3. `App.vue` — точка входа

Копировать структуру из любого существующего каталога. Обязательно:
- Импортировать `CatalogSection/List/Detail/Brand` из `@/shared/components/catalog/`
- Импортировать `QuickSelect` из `@/shared/components/catalog/QuickSelect.vue`
- Использовать `useCatalogRouter` из `@/shared/composables/useCatalogRouter.js`
- Определить `labels` с названиями, иконками, filterLabels для QuickSelect

### 4. `index.html` + `main.js`

```html
<!-- src/apps/electric-actuator-catalog/index.html -->
<div id="electric-actuator-app"></div>
<script type="module" src="./main.js"></script>
```
```js
// main.js
import { createApp } from 'vue'
import App from './App.vue'
createApp(App).mount('#electric-actuator-app')
```

### 5. Обновить `shared/endpoints.js`

Добавить секцию для нового каталога:
```js
electricActuator: {
  catalog: '/electric_actuators/catalog/',
  detail: id => `/electric_actuators/catalog/${id}/`,
  filters: '/electric_actuators/filters/',
  quickselect: '/electric_actuators/quickselect/',
},
```

### 6. Обновить `vite.config.js`

Добавить точку входа в `rollupOptions.input`:
```js
'electric-actuator-catalog': path.resolve(__dirname, 'src/apps/electric-actuator-catalog/index.html'),
```

### 7. Обновить виджет (`widget/App.vue`)

Добавить 5 блоков `<QuickSelect / CatalogSection / CatalogList / CatalogDetail / CatalogBrand>` с условием `route.catalog === 'electric_actuator'`. Импортировать API-клиент и добавить labels в объект `labels`.

### 8. Обновить `widget/CatalogIndex.vue`

Добавить запись в объект `catalogs`:
```js
electric_actuator: { id: 'electric_actuator', name: 'Электроприводы', icon: '⚡', ... }
```

---

## Легенда статусов

- **Создано (дата)** — файл написан в рамках рефакторинга
- **Обновлён (дата)** — существующий файл изменён
- **Проанализирован** — содержимое изучено, комментарий актуален
- **Не просмотрен** — содержимое не анализировалось, описание предположительное

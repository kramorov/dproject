# Image Processor — обработка изображений и PDF

Переиспользуемые инструменты для загрузки, обрезки, удаления фона, ресайза по профилям и рендеринга PDF-страниц.

## API

| Метод | Эндпоинт | Content-Type | Описание |
|-------|----------|-------------|----------|
| `POST` | `/api/image-processor/upload/` | multipart/form-data | Загрузить файл (изображение или PDF) → `session_id`, размеры |
| `POST` | `/api/image-processor/preview/` | application/json | Превью crop-области → base64 JPEG на шахматном фоне |
| `POST` | `/api/image-processor/crop/` | application/json | Обработка: crop + rembg + профильные варианты |

### POST /crop/ — профильный режим

```json
// Запрос (изображение)
{
  "session_id": 1,
  "crop_x": 120.5, "crop_y": 80.0, "crop_size": 800.0,
  "background_color": "#F0F0F0",
  "remove_background": true,
  "category_code": "PRODUCT_GALLERY"
}

// Запрос (PDF — crop-параметры необязательны)
{
  "session_id": 2,
  "category_code": "CERTIFICATE"
}

// Ответ (изображение)
{
  "category": "PRODUCT_GALLERY",
  "profile": {...},
  "variants": {
    "icon":  {"50":  {"data": "data:image/webp;base64,...", "size": 1234}},
    "thumb": {"80": {...}, "150": {...}},
    "card":  {"400": {...}, "800": {...}}
  }
}

// Ответ (PDF)
{
  "category": "CERTIFICATE",
  "pages": [
    {"n": 1, "icon": {"50": {...}}, "page": {"600": {...}}},
    {"n": 2, "icon": {"50": {...}}, "page": {"600": {...}}}
  ],
  "total_pages": 2,
  "original_size": 245760,
  "email_pdf": {
    "100": {"data": "data:application/pdf;base64,...", "size": 180224, "dpi": 100, "pages": 2}
  }
}
```

## Pipeline

### Изображения
```
Оригинал (JPEG/PNG/WebP)
  │
  ├─ [опционально] rembg (U2Net) → RGBA с прозрачностью
  │
  ├─ crop_and_pad() — квадрат по рамке + добивка
  │   └─ fill mode: холст RGB + bgColor (альфа заливается)
  │   └─ remove mode: холст RGBA (прозрачный)
  │
  └─ resize_and_encode() для каждого варианта из профиля
      └─ WebP/JPEG/PNG, качество и размеры из профиля
```

### PDF
```
Оригинал PDF
  │
  ├─ Постраничный рендер: render_pdf_page() через PyMuPDF (fitz)
  │   └─ dpi из профиля (150 для сертификатов, 72 для фото)
  │
  ├─ Постраничные варианты: icon, page (WebP)
  │
  └─ Email PDF (если роль 'email' в профиле):
      ├─ Повторный рендер с email_dpi (100)
      ├─ Сохранение исходных размеров страниц (A4)
      ├─ JPEG quality=60 внутри PDF
      └─ Все страницы → один PDF с deflate-сжатием
```

## Профили (MediaCategory.PRESENTATION_PROFILES)

Обработка управляется профилем категории из `media_library/models.py`:

| Категория | Роли | multi_page | dpi |
|-----------|------|------------|-----|
| PRODUCT_GALLERY | icon(50), thumb(80,150), card(400,800) | нет | 72 |
| CERTIFICATE | icon(50), page(600), email→PDF(100dpi) | да | 150 |
| TECH_DOC | icon(50), page(800), email→PDF(100dpi) | да | 150 |
| BANNER | full(1200,1920) | нет | 72 |
| SCHEMA/DRAWING/DIAGRAM | icon + card/full | нет | 150 |

## Ключевые функции (`services.py`)

| Функция | Назначение |
|---------|-----------|
| `resize_and_encode(img, width, fmt, quality)` | Ресайз + кодирование в WebP/JPEG/PNG |
| `render_pdf_page(pdf_bytes, page_num, dpi)` | Рендер одной страницы PDF в PIL Image |
| `generate_webp_variants(image)` | Устаревший: sm/md/lg WebP (для старого режима) |
| `crop_and_pad(...)` | Обрезка + добивка фона |
| `_remove_background(img)` | Удаление фона через rembg (U2Net) |
| `process_crop_session(session)` | Старый pipeline (sm/md/lg, сохраняет в БД) |
| `process_with_profile(session, category_code)` | Новый pipeline: изображения и PDF по профилю |
| `_process_pdf_with_profile(pdf_bytes, profile, code)` | Рендер PDF-страниц + профильные варианты |

## Модель

`ImageCropSession` — временная сессия:
- `original_file` — ManagedFileField (Cloud.ru), поддерживает JPG/PNG/WebP/PDF
- `crop_x`, `crop_y`, `crop_size` — координаты рамки
- `background_color` — цвет добивки, default `#F0F0F0`
- `remove_background` — флаг rembg
- `result_sm`, `result_md`, `result_lg` — WebP-результаты (старый режим)

## Фронтенд

`ImageCropper.vue`:
- **Загрузка**: кнопка выбора файла → `fetch()` с CSRF
- **Рамка**: фиксированный квадрат, drag + колёсико для зума
- **Фон**: селектор «Убрать фон» / «Наложить фон» + color picker
- **Альфа-канал**: автоопределение при загрузке (зелёный бейдж)
- **Лог**: консоль с таймстемпами
- **Пропс**: `categoryCode` — передаётся в `/crop/` для профильной обработки

Тестовая страница: `/tools/image-processor` → `ImageProcessorTest.vue`
- Выбор категории из списка (PRODUCT_GALLERY, CERTIFICATE, TECH_DOC, BANNER...)
- Для PDF-категорий: загрузка PDF → автообработка → страницы + email PDF
- Для фото-категорий: интерактивная обрезка + профильные варианты
- Сравнение исходного и сжатого размера для PDF

## Зависимости

```bash
pip install rembg onnxruntime    # удаление фона
pip install PyMuPDF              # рендеринг PDF (fitz)
```

## Интеграция с MediaVariant

Начиная с 2026-06-01, `media_library/services.py` использует `image_processor` для генерации:
- Постраничных вариантов (icon, page) — WebP
- Email PDF — комбинированный сжатый PDF (email_dpi, JPEG quality=60, deflate)

Email сохраняется как один `MediaVariant` с `role='email', format='pdf'`.

## Ограничения

- `rembg` (U2Net) хорошо работает на однородном фоне. На сложном — частично.
- RGBA WebP на 30-50% больше RGB.
- PDF email: растровый (не векторный), но с JPEG quality=60 — адекватный размер для A4.
- Data URI не работают для PDF в Chrome (about:blank#blocked) — используем Blob URL.

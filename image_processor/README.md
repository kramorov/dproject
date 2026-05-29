# Image Processor — интерактивная обрезка изображений

Отдельное Django-приложение. Позволяет загрузить фото, обрезать, удалить фон нейросетью и получить WebP-варианты с прозрачностью.

## API

| Метод | Эндпоинт | Content-Type | Описание |
|-------|----------|-------------|----------|
| `POST` | `/api/image-processor/upload/` | multipart/form-data | Загрузить оригинал → `session_id`, размеры, URL |
| `POST` | `/api/image-processor/preview/` | application/json | Превью crop-области → base64 JPEG на шахматном фоне |
| `POST` | `/api/image-processor/crop/` | application/json | Применить crop + удаление фона → WebP sm/md/lg |

### POST /crop/

```json
// Запрос
{
  "session_id": 1,
  "crop_x": 120.5,
  "crop_y": 80.0,
  "crop_size": 800.0,
  "background_color": "#F0F0F0",
  "remove_background": true
}

// Ответ
{
  "session_id": 1,
  "original_size": 143872,
  "cropped_size": 17612,
  "bg_removed_full_pct": 86.3,
  "bg_removed_crop_pct": 35.1,
  "results": {
    "sm": { "url": "...", "size": 5120 },
    "md": { "url": "...", "size": 20480 },
    "lg": { "url": "...", "size": 102400 }
  }
}
```

## Pipeline

```
Оригинал (JPEG/PNG)
  │
  ├─ [опционально] rembg (U2Net) → RGBA с прозрачностью
  │
  ├─ crop_and_pad() — квадрат по рамке + добивка
  │   └─ без удаления: холст RGB + bgColor
  │   └─ с удалением: холст RGBA (прозрачный)
  │
  └─ generate_webp_variants() → sm(150w), md(400w), lg(800w)
      └─ lossy WebP quality=80, с альфа-каналом при наличии
```

## Модель

`ImageCropSession` — временная сессия обрезки:
- `original_file` — ManagedFileField (Cloud.ru)
- `crop_x`, `crop_y`, `crop_size` — координаты рамки (px оригинала)
- `background_color` — цвет добивки, default `#F0F0F0`
- `remove_background` — флаг удаления фона (rembg)
- `result_sm`, `result_md`, `result_lg` — WebP-результаты

## Фронтенд

`ImageCropper.vue` (`frontend/src/shared/components/`) — canvas-компонент:
- **Загрузка**: кнопка выбора файла → `fetch()` с CSRF
- **Рамка**: фиксированный квадрат по центру
- **Изображение**: drag для перемещения, колёсико для зума
- **Фон**: color picker + чекбокс «Убрать фон» (rembg)
- **Лог**: консоль-панель с таймстемпами (загрузка, rembg, превью, WebP, ошибки)
- **Превью**: base64 JPEG на шахматном фоне (проверка прозрачности)

Тестовая страница: `/tools/image-processor` → `ImageProcessorTest.vue`

## Зависимости

```bash
pip install rembg onnxruntime
```

При первом запуске rembg качает модель U2Net (~170 MB) в `%USERPROFILE%\.u2net`.

## Ограничения

- `rembg` (U2Net) хорошо работает на однородном фоне (белый, серый). На сложном фоне — частично.
- RGBA WebP с прозрачностью на 30-50% больше RGB (альфа-канал + полупрозрачные края).
- Для карточек каталога использовать `sm` (150w, ~5 KB) или `md` (400w, ~8 KB).
- JPEG не поддерживает прозрачность — превью на шахматном фоне.

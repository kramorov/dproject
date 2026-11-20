# Перевод «报价系统» (система расчёта приводов) на русский

Инструменты перевода GUI-строк скомпилированного PyInstaller-приложения
(Python 3.11, PySide6) без декомпиляции байткода в исходный код.

> Описание самой системы — где что лежит, как связаны данные и что из неё
> переносить в наш проект, — вынесено в **`arun.md`**.

## Что здесь

| Файл | Назначение |
|---|---|
| `arun.md` | Описание китайской системы и карта данных (для переноса в наш проект) |
| `dump_strings.json` | Дамп китайских строк из кода (486 уникальных, с локациями) |
| `translate.json` | Перевод строк кода: китайский → русский (486 пар) |
| `translate_data.json` | Перевод строк справочников: китайский → русский (84 пары) |
| `extract_strings.py` | Дамп строк из извлечённых `.pyc` |
| `pyc_strings.py` | Библиотека: чтение/замена строковых констант в code-объектах |
| `apply_translation.py` | Заливка перевода в exe (патчит qt_app + engine, пересобирает PYZ/CArchive) |
| `translate_data.py` | Перевод `data.json` (рекурсивно, включая ключи) |
| `translate_db.py` | Перевод локальной SQLite `quotation.db` |
| `data_ru.json` | Готовый переведённый `data.json` |
| `app_ru.exe` | Готовая русская программа |

## Требования

- **Python 3.11** (той версии, под которой собран exe) — `C:\Python311\python.exe`.
  Marshal-формат code-объектов привязан к версии Python.
- Для извлечения/проверки: `pip install pyinstxtractor-ng` (любая версия Python).

## Использование

### 1. Дамп строк кода

```powershell
C:\Python311\python.exe extract_strings.py app.exe_extracted dump_strings.json
```

### 2. Заливка перевода в exe

```powershell
C:\Python311\python.exe apply_translation.py app.exe translate.json app_ru.exe
```

### 3. Перевод справочника data.json

```powershell
python translate_data.py "_internal\data.json" translate_data.json data_ru.json
```

### 4. Перевод локальной БД

```powershell
python translate_db.py "%LOCALAPPDATA%\QuotationSystem\quotation.db" translate_data.json "%LOCALAPPDATA%\QuotationSystem\data.json"
```

Точные пути, схема данных и порядок установки (`_internal/data.json`,
`%LOCALAPPDATA%\QuotationSystem\...`) — в `arun.md` (§2–3).

## Проверка результата

```powershell
python -m pyinstxtractor_ng -d app_ru.exe
C:\Python311\python.exe extract_strings.py app_ru.exe_extracted dump_check.json
# должно быть: «Уникальных китайских строк: 0»
```

## Что переведено

- `qt_app` (главное окно): 599 вхождений русских строк.
- `engine` (движок): 56 вхождений.
- Итого 486 уникальных китайских строк кода → заменены.
- Справочники `data.json`: 84 уникальные строки → заменены (типы клапанов, опции
  наценок, имена листов/файлов-источников, статусы).

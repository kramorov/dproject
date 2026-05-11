# DeepSeek Tools

Утилиты для навигации по кодовой базе. Используются DeepSeek Agent в терминале.

## Основные скрипты

| Скрипт | Назначение | Пример |
|---|---|---|
| `show_lines.py` | Показать диапазон строк файла | `python deepseek-tools/show_lines.py models.py 50 70` |
| `find_class.py` | Показать класс целиком | `python deepseek-tools/find_class.py models.py DirectionValve` |
| `list_model_fields.py` | Только поля модели | `python deepseek-tools/list_model_fields.py models.py DirectionValve` |
| `dump_model_range.py` | Класс + N строк после | `python deepseek-tools/dump_model_range.py models.py DirectionValve 50` |

## Одноразовые скрипты

Файлы `_*.py`, `_*.txt` — временные, созданные в ходе сессий. Можно удалить.

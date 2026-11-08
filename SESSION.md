# SESSION.md — 2026-11-08 (конец дня)

Рабочая ветка: `office-work`. Канон данных — **рабочая БД** (`db.sqlite3`,
коммитится); сид удалён (вариант C, решение пользователя).

## Состояние на конец дня

- Тесты: `python manage.py test ea_control -v 1 --keepdb --noinput` на копии
  БД — **90/90 OK** (без сида). Перед прогоном:
  `Copy-Item db.sqlite3 test_db.sqlite3 -Force` (см. `run_tests.bat`).
- Канон: 45 слотов (41 object / 4 value), 5 БУ (basic AR21 / INT/N / INT/L /
  INT/O / posi-4-20), 142 опции, 331 строка матрицы, 152 правила
  (132 пользовательских).
- Справочники: 0-10В (формы/команды/ОС), 9 протоколов, 10 устройств ОС
  (EWG_01_1/RWG_4020), размещение BUILT_IN/MOUNTED/SEPARATE.
- Фронт: общие компоненты `components/admin/DictEditor.vue` (CRUD +
  «Копировать»), `FieldInput.vue`, `shared/uniqueCode.js`; вкладка
  «Справочники» — все 17 справочников.

## Как гонять тесты

`run_tests.bat` (копия БД + прогон) либо вручную:
`Copy-Item db.sqlite3 test_db.sqlite3 -Force` →
`python manage.py test ea_control -v 1 --keepdb --noinput`.
test_db.sqlite3 — в .gitignore.

## Отложено

- Переделка «Датчики»/«Сигналы ОС»: датчик = набор слотов; сухой/мокрый —
  атрибут сигнала. Сироты справочников и emits-дыры — отложены.
- Кодировки encoding/ext_encoding, bu_template.md, pa_controls/0050.

## Незакоммичено

db.sqlite3; dictionaries.py; tests*.py; frontend (EaControlAdminPage.vue,
EaControlStructure.vue, 3 локали, DictEditor.vue, FieldInput.vue,
uniqueCode.js); slots.md; удалены seed_cu_demo.py и
reconcile_cu_structure.py (git покажет D).

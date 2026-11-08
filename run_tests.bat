@echo off
rem Тесты ea_control на копии рабочей БД (вариант C: канон — БД, сида нет).
rem test_db.sqlite3 — в .gitignore; схема готова, поэтому --keepdb без миграций.
copy /Y db.sqlite3 test_db.sqlite3 >nul
python manage.py test ea_control -v 1 --keepdb --noinput

"""
Показать только поля Django-модели (строки с '= models.').

Использование:
    python deepseek-tools/list_model_fields.py <путь> <ИмяКласса>

Пример:
    python deepseek-tools/list_model_fields.py cert_doc/models.py CertData

Выводит строки с номерами — только объявления полей, без методов и Meta.
"""
import sys, re, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = sys.argv[1]
class_name = sys.argv[2]

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_class = False
indent = None
for i, line in enumerate(lines):
    if re.match(rf'^class {class_name}\(', line):
        in_class = True
        indent = len(line) - len(line.lstrip())
        continue
    if in_class:
        stripped = line.strip()
        # Выход по следующему классу
        if stripped.startswith('class ') and len(line) - len(line.lstrip()) <= indent:
            break
        # Показываем только поля
        if '= models.' in line or '= models\n' in line:
            print(f"{i+1}:{line}", end='')
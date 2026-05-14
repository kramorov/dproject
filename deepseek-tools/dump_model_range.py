"""
Вывести определение класса + опциональный хвост строк после него.

Умнее чем show_lines — принимает имя класса, сам находит его границы.

Использование:
    python deepseek-tools/dump_model_range.py <путь> <ИмяКласса> [отступ]

Без отступа — только строки класса (от class до следующего class).
С отступом=50 — класс + 50 строк после его закрытия.

Пример:
    python deepseek-tools/dump_model_range.py cert_doc/models.py CertData
    python deepseek-tools/dump_model_range.py cert_doc/models.py CertData 50
"""
import sys, re, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = sys.argv[1]
class_name = sys.argv[2]
padding = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
indent = None
end_line = None
for i, line in enumerate(lines):
    if re.match(rf'^class {class_name}\(', line):
        found = True
        indent = len(line) - len(line.lstrip())
        start = i
        continue
    if found and end_line is None:
        stripped = line.strip()
        if stripped and not line.startswith(' ' * (indent + 1)):
            if stripped.startswith('class '):
                end_line = i

if found:
    if end_line is None:
        end_line = len(lines)
    end_line = min(end_line + padding, len(lines))
    for i in range(start, end_line):
        print(f"{i+1}:{lines[i]}", end='')
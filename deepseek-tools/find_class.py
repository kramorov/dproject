# deepseek-tools/find_class.py
# Найти класс по имени и показать его содержимое (поля, Meta, __str__)
# Использование: python deepseek-tools/find_class.py path ClassName [show_all]
import sys, re, io

# Windows: перекодируем вывод чтобы не падать на спецсимволах
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = sys.argv[1]
class_name = sys.argv[2]
show_all = len(sys.argv) > 3 and sys.argv[3] == 'all'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
indent = None
for i, line in enumerate(lines):
    if re.match(rf'^class {class_name}\(', line):
        found = True
        indent = len(line) - len(line.lstrip())
        print(f"=== {i+1}:{line}", end='')
        continue
    if found:
        # Определяем конец класса: непустая строка с меньшим или равным отступом
        stripped = line.strip()
        if stripped and not line.startswith(' ' * (indent + 1)) and not line.startswith(' ' * indent + ' '):
            # Может быть @property, def method того же уровня, или следующий class
            if stripped.startswith('@') or stripped.startswith('def ') or stripped.startswith('class '):
                if stripped.startswith('class '):
                    break
                if not show_all:
                    break
        print(f"{i+1}:{line}", end='')
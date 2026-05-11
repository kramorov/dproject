# deepseek-tools/show_lines.py
# Показать строки файла в диапазоне [start, end] с номерами
# Использование: python deepseek-tools/show_lines.py path start end
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = sys.argv[1]
start = int(sys.argv[2])
end = int(sys.argv[3])

with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if i > end:
            break
        if i >= start:
            print(f"{i}:{line}", end='')
import sys
import os

print("Python path:", sys.executable)
print("Working directory:", os.getcwd())

# Попробуйте импортировать pandas
try:
    import pandas as pd

    print("SUCCESS: Pandas version", pd.__version__)
except ImportError as e:
    print("ERROR:", e)

# Проверим пути импорта
print("\nPython path:")
for path in sys.path:
    print(" ", path)
with open('solenoid_valves/models.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 234 <= i <= 300:
            print(f"{i}:{line}", end='')

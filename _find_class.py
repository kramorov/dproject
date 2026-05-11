with open('solenoid_valves/models.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'class DirectionValve' in line:
            print(f"{i}:{line}", end='')

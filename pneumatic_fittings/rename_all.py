from pneumatic_fittings.models import PneumaticFitting

# Считаем все объекты
total = PneumaticFitting.objects.count()
print(f"Всего объектов: {total}")

updated = 0
errors = 0

for i, obj in enumerate(PneumaticFitting.objects.all(), 1):
    try:
        old_name = obj.name
        obj.save()  # Триггерит save() миксина
        updated += 1

        if old_name != obj.name:
            print(f"[{i}/{total}] Обновлен ID {obj.id}: '{old_name}' -> '{obj.name}'")
        else:
            print(f"[{i}/{total}] ID {obj.id}: имя не изменилось")

    except Exception as e:
        errors += 1
        print(f"[{i}/{total}] Ошибка ID {obj.id}: {e}")

print(f"\nГотово! Обновлено: {updated}, Ошибок: {errors}")
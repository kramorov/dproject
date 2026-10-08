from pneumatic_fittings.models import PneumaticFitting, PneumaticSilencer, PneumaticPlug

MODELS = (PneumaticFitting, PneumaticSilencer, PneumaticPlug)

total = sum(Model.objects.count() for Model in MODELS)
print(f"Всего объектов: {total}")

updated = 0
errors = 0
i = 0

for Model in MODELS:
    for obj in Model.objects.all():
        i += 1
        try:
            old_name = obj.name
            obj.save()  # Триггерит save() миксина
            updated += 1

            if old_name != obj.name:
                print(f"[{i}/{total}] Обновлен {Model.__name__} ID {obj.id}: '{old_name}' -> '{obj.name}'")
            else:
                print(f"[{i}/{total}] {Model.__name__} ID {obj.id}: имя не изменилось")
        except Exception as e:
            errors += 1
            print(f"[{i}/{total}] Ошибка {Model.__name__} ID {obj.id}: {e}")

print(f"\nГотово! Обновлено: {updated}, Ошибок: {errors}")

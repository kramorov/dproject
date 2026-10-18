"""
Перенос 21 связки ControlUnitWiring в EaWiringDiagramBinding (фаза 5).

Схемы привязываются к КОРПУСАМ (ElectricActuatorBody): клеммник/схема у моделей
общего корпуса (QUI-варианты) одинакова. Скоуп связки определяется по коду:
- «AR01-...»  → все корпуса серии AR01E;
- «AR19-...»/«AR21E-..._007-100» → корпуса AR21E007/010/020/050/060-100;
- «AR21E-...» без диапазона → все корпуса серии AR21E.

Подпись (signals) = стандартные строки матрицы корпуса для пары БУ×напряжение
связки + строки слота HEATER_* с heater_supply связки. Шинные варианты БУ
(int-n-hr/mb/pb) матчатся на базовый int-n (шина — слот PROTOCOL, не БУ).

Ограничения текущих данных (в отчёт):
- строки матрицы залиты только для 220-AC и 6 корпусов (v1 заливки) — привязки
  создаются только там, где подпись непустая; остальные — в отчёт «пропущено»;
- профиль связки используется как эталон типового набора (все std-строки);
- перегрев/авария/готовность/команды не залиты → в подпись не входят.

Идемпотентность: существующие EaWiringDiagramBinding удаляются перед созданием.

Использование:
    python manage.py transfer_ea_wirings
"""
from django.core.management.base import BaseCommand

from electric_actuators.models import (
    ControlUnitWiring, EaWiringDiagramBinding, EaSignalMatrixEntry,
    ElectricActuatorBody,
)


class Command(BaseCommand):
    help = 'Перенос ControlUnitWiring → EaWiringDiagramBinding (через корпус)'

    def handle(self, *args, **options):
        EaWiringDiagramBinding.objects.all().delete()

        bodies_ar01 = list(ElectricActuatorBody.objects.filter(
            model_line__code='AR01E'))
        bodies_ar21 = list(ElectricActuatorBody.objects.filter(
            model_line__code='AR21E'))
        # «_007-100» → весь ряд 007..100
        bodies_ar21_7100 = [b for b in bodies_ar21
                            if b.name in ('AR21E007', 'AR21E010', 'AR21E020',
                                          'AR21E050', 'AR21E060-100')]

        created, skipped = [], []
        for w in ControlUnitWiring.objects.select_related(
                'control_unit', 'power_supply', 'heater_supply').all():
            code = w.code
            if code.startswith('AR01-'):
                bodies = bodies_ar01
            elif '_007-100' in w.name or code.startswith('AR19-'):
                bodies = bodies_ar21_7100
            else:
                bodies = bodies_ar21

            # Шинные варианты БУ → базовый (шина — слот PROTOCOL)
            cu_code = w.control_unit.code
            if cu_code.startswith('int-n-'):
                cu_code = 'int-n'

            for body in bodies:
                rows = list(EaSignalMatrixEntry.objects.filter(
                    body=body, control_unit__code=cu_code,
                    power_supply=w.power_supply))
                if w.heater_supply_id:
                    rows += list(EaSignalMatrixEntry.objects.filter(
                        body=body, control_unit__code=cu_code,
                        power_supply=w.power_supply,
                        heater_supply=w.heater_supply))
                std_rows = [r for r in rows if r.availability == 'std']
                if not std_rows:
                    skipped.append((w.code, body.name, cu_code,
                                    w.power_supply.code))
                    continue
                binding = EaWiringDiagramBinding.objects.create(
                    body=body,
                    control_unit=w.control_unit if cu_code == w.control_unit.code
                    else None,  # шинный вариант: привязка не зависит от шины
                    power_supply=w.power_supply,
                    name=w.name,
                    diagram=w.wiring_diagram,
                    match_type='exact',
                )
                binding.signals.set(std_rows)
                created.append((w.code, body.name, len(std_rows)))

        self.stdout.write(self.style.SUCCESS(
            f'Создано привязок: {len(created)}'))
        for wcode, body, n in created:
            self.stdout.write(f'  {wcode} → {body} ({n} строк)')
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'Пропущено (нет std-строк в матрице): {len(skipped)}'))
            for wcode, body, cu, ps in skipped[:25]:
                self.stdout.write(f'  {wcode} → {body} ({cu} {ps})')

# ea_control/management/commands/enrich_cu_feedback_signals.py
"""
Идемпотентная доводка справочника CuFeedbackSignal до канонической схемы.

Что делает (только справочник «Сигналы ОС», слоты/матрицу не трогает):

- направленные контакты (концевые/путевые/моментные ОТКРЫТО/ЗАКРЫТО) —
  форма в коде сигнала: FB_<ROLE>_SPDT и FB_<ROLE>_DPDT (SPDT из ЭП + DPDT);
- добавляет остальные роли из EaFeedbackSignal: TORQUE_ANALOG, TURN_COUNTER,
  STOP, SELECTOR_POSITION, PHASE_LOSS;
- объединяет дубли «Авария» (FB_ALARM + FB_ALARM_SPDT) и «Перегрев»
  (FB_OVERHEAT_NC + FB_OVERHEAT_SPST_NC) в канонические FB_ALARM / FB_OVERHEAT;
- переименовывает FB_REMOTE_NO → FB_LOCAL_REMOTE, FB_READY_NO → FB_READY.

Ссылки (CuSlotOption/CuMatrixEntry/CuFeedbackDevice.emits/ControlUnit.emits)
перенаправляются со старых записей на канонические перед удалением дублей.

Запуск: python manage.py enrich_cu_feedback_signals
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ea_control.models import (
    CuFeedbackSignal, CuFeedbackSignalForm, CuFeedbackDevice, CuSlotOption,
    CuMatrixEntry, ControlUnit,
)

class Command(BaseCommand):
    help = ('Доводит справочник CuFeedbackSignal до канонической схемы '
            '(недостающие роли + объединение дублей + правка форм/норм).')

    def handle(self, *args, **options):
        forms = self._forms()

        with transaction.atomic():
            added = self._add_missing(forms)
            renamed_dir, created_dir = self._add_direction_form_variants(forms)
            merged_alarm = self._merge_alarm(forms)
            merged_overheat = self._merge_overheat(forms)
            renamed_remote_ready = self._rename_remote_and_ready(forms)

        created_total = len(added) + len(created_dir)
        renamed_total = len(renamed_dir) + len(renamed_remote_ready)
        merged_total = len(merged_alarm) + len(merged_overheat)
        self.stdout.write(self.style.SUCCESS(
            'Готово: +%d записей, переименовано %d, объединено %d.' % (
                created_total, renamed_total, merged_total,
            )))

    # ── Справочник форм (существует из seed, создаём при необходимости) ──
    def _forms(self):
        specs = {
            'DRY_SPST': ('Сухой контакт SPST', 'dry_output'),
            'DRY_SPDT': ('Сухой контакт SPDT', 'dry_output'),
            'DRY_DPDT': ('Сухой контакт DPDT', 'dry_output'),
            'AN_4_20_ACTIVE': ('Петля 4-20 мА, активная', 'current_4_20'),
            'AN_4_20_PASSIVE': ('Петля 4-20 мА, пассивная', 'current_4_20'),
            'RES_POTENTIOMETER': ('Потенциометр', 'resistance'),
        }
        out = {}
        for code, (name, category) in specs.items():
            out[code], _ = CuFeedbackSignalForm.objects.get_or_create(
                code=code, defaults={'name': name, 'category': category})
        return out

    # ── Канонический набор сигналов ──────────────────────────────────────
    def _role(self, code):
        from electric_actuators.models import EaFeedbackSignalRole
        return EaFeedbackSignalRole.objects.get_or_create(
            code=code, defaults={'name': code})[0]

    def _normal(self, code):
        from electric_actuators.models import EaContactNormal
        return EaContactNormal.objects.get_or_create(
            code=code, defaults={'name': code})[0]

    def _signal(self, code, **fields):
        if fields.get('role') and not hasattr(fields['role'], 'pk'):
            fields['role'] = self._role(fields['role'])
        if fields.get('contact_normal') and not hasattr(fields['contact_normal'], 'pk'):
            fields['contact_normal'] = self._normal(fields['contact_normal'])
        obj, created = CuFeedbackSignal.objects.update_or_create(
            code=code, defaults=fields)
        return obj, created

    def _add_missing(self, f):
        """Остальные недостающие роли из EaFeedbackSignal (одна запись)."""
        specs = [
            # code, name, role, category, form, contact_normal, max_v, max_a
            ('FB_STOP', 'Останов (NO)', 'STOP',
             'contact', f['DRY_SPST'], 'NO', 250, Decimal('5')),
            ('FB_TURN_COUNTER', 'Счётчик оборотов (NO)', 'TURN_COUNTER',
             'contact', f['DRY_SPST'], 'NO', 250, Decimal('0.5')),
            ('FB_SELECTOR_POSITION', 'Положение ключа-селектора',
             'SELECTOR_POSITION', 'contact', f['DRY_SPDT'], 'CHANGEOVER',
             250, Decimal('5')),
            ('FB_PHASE_LOSS', 'Авария: потеря фазы', 'PHASE_LOSS',
             'contact', f['DRY_SPST'], 'NO', 250, Decimal('5')),
        ]
        created = []
        for (code, name, role, category, form, normal, max_v, max_a) in specs:
            obj, is_new = self._signal(code, name=name, role=role,
                                       category=category, form=form,
                                       contact_normal=normal,
                                       max_voltage=max_v, max_current=max_a)
            if is_new:
                created.append(code)
        # Аналоговый момент — отдельно (нет контактных полей).
        obj, is_new = self._signal(
            'FB_TORQUE_4_20MA', name='Аналоговый момент 4-20 мА',
            role='TORQUE_ANALOG', category='analog',
            form=f['AN_4_20_ACTIVE'], wires=2)
        if is_new:
            created.append('FB_TORQUE_4_20MA')
        return created

    def _add_direction_form_variants(self, f):
        """Направленные контакты: форма в коде — FB_<ROLE>_SPDT/_DPDT.

        SPDT — существующие/старые форм-агностичные записи (FB_END_OPEN →
        FB_END_OPEN_SPDT), DPDT — новые варианты из EaFeedbackSignal.
        """
        specs = [
            ('END_OPEN', 'Конечное «Открыто»'),
            ('END_CLOSE', 'Конечное «Закрыто»'),
            ('WAY_OPEN', 'Промежуточное (открытие)'),
            ('WAY_CLOSE', 'Промежуточное (закрытие)'),
            ('TORQUE_OPEN', 'Моментный «Открыто»'),
            ('TORQUE_CLOSE', 'Моментный «Закрыто»'),
        ]
        renamed = []
        created = []
        for role, base in specs:
            spdt = f'FB_{role}_SPDT'
            dpdt = f'FB_{role}_DPDT'
            if self._rename(f'FB_{role}', spdt, name=f'{base}, SPDT',
                            role=role, category='contact', form=f['DRY_SPDT'],
                            contact_normal='CHANGEOVER', max_voltage=250,
                            max_current=Decimal('5')):
                renamed.append(f'FB_{role}')
            obj, is_new = self._signal(spdt, name=f'{base}, SPDT', role=role,
                                       category='contact', form=f['DRY_SPDT'],
                                       contact_normal='CHANGEOVER',
                                       max_voltage=250,
                                       max_current=Decimal('5'))
            if is_new:
                created.append(spdt)
            obj, is_new = self._signal(dpdt, name=f'{base}, DPDT', role=role,
                                       category='contact', form=f['DRY_DPDT'],
                                       contact_normal='CHANGEOVER',
                                       max_voltage=250,
                                       max_current=Decimal('5'))
            if is_new:
                created.append(dpdt)
        return renamed, created

    # ── Перенаправление ссылок перед удалением дубля ────────────────────
    def _repoint(self, old, new):
        CuSlotOption.objects.filter(feedback_signal=old).update(
            feedback_signal=new)
        CuMatrixEntry.objects.filter(feedback_signal=old).update(
            feedback_signal=new)
        for cu in list(old.control_units.all()):
            cu.emits.remove(old)
            cu.emits.add(new)
        for dev in list(old.devices.all()):
            dev.emits.remove(old)
            dev.emits.add(new)

    def _merge_alarm(self, f):
        """FB_ALARM + FB_ALARM_SPDT → FB_ALARM (SPDT, перекидной)."""
        merged = []
        keep, _ = self._signal(
            'FB_ALARM', name='Авария (SPDT: НЗ + НО)', role='ALARM',
            category='contact', form=f['DRY_SPDT'],
            contact_normal='CHANGEOVER', max_voltage=250,
            max_current=Decimal('5'))
        dup = CuFeedbackSignal.objects.filter(code='FB_ALARM_SPDT').first()
        if dup and dup.pk != keep.pk:
            self._repoint(dup, keep)
            dup.delete()
            merged.append('FB_ALARM_SPDT')
        return merged

    def _merge_overheat(self, f):
        """FB_OVERHEAT_NC + FB_OVERHEAT_SPST_NC → FB_OVERHEAT (SPST, NC)."""
        merged = []
        keep, _ = self._signal(
            'FB_OVERHEAT', name='Перегрев, SPST (НЗ)', role='OVERHEAT',
            category='contact', form=f['DRY_SPST'], contact_normal='NC',
            max_voltage=250, max_current=Decimal('5'))
        for old_code in ('FB_OVERHEAT_NC', 'FB_OVERHEAT_SPST_NC'):
            dup = CuFeedbackSignal.objects.filter(code=old_code).first()
            if dup and dup.pk != keep.pk:
                self._repoint(dup, keep)
                dup.delete()
                merged.append(old_code)
        return merged

    def _rename(self, old_code, new_code, **updates):
        old = CuFeedbackSignal.objects.filter(code=old_code).first()
        if not old:
            return None
        existing = CuFeedbackSignal.objects.filter(code=new_code).first()
        if existing and existing.pk != old.pk:
            # Целевой код уже есть — сливаем: доводим целевой до канона,
            # перенаправляем ссылки со старого и удаляем старый.
            for k, v in updates.items():
                setattr(existing, k, v)
            existing.save()
            self._repoint(old, existing)
            old.delete()
            return new_code
        for k, v in updates.items():
            setattr(old, k, v)
        if old.code != new_code:
            old.code = new_code
        old.save()
        return new_code

    def _rename_remote_and_ready(self, f):
        renamed = []
        if self._rename('FB_REMOTE_NO', 'FB_LOCAL_REMOTE',
                        name='Местное/удалённое (SPST НО)',
                        role='LOCAL_REMOTE', category='contact',
                        form=f['DRY_SPST'], contact_normal='NO',
                        max_voltage=250, max_current=Decimal('5')):
            renamed.append('FB_REMOTE_NO')
        if self._rename('FB_READY_NO', 'FB_READY',
                        name='Готовность (NO)', role='READY',
                        category='contact', form=f['DRY_SPST'],
                        contact_normal='NO', max_voltage=250,
                        max_current=Decimal('5')):
            renamed.append('FB_READY_NO')
        return renamed

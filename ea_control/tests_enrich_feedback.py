# ea_control/tests_enrich_feedback.py
"""Тесты команды enrich_cu_feedback_signals.

setUp сбрасывает и старые, и канонические коды сигналов (чтобы тест не
зависел от того, прогнана ли уже команда по БД --keepdb), затем создаёт
исходное «до команды» состояние с дублями и форм-агностичными направленными
сигналами. Ссылки для проверки перенаправления создаются внутри тестов с
уникальными кодами (транзакция TestCase откатывается).
"""
from django.core.management import call_command
from django.test import TestCase

from ea_control.models import (
    CuFeedbackSignal, CuFeedbackSignalForm, CuFeedbackDevice, CuSlotOption,
    CuSlot, CuSectionNode, CuMatrixEntry,
)

DIRECTIONS = [
    ('END_OPEN', 'Конечное «Открыто»'),
    ('END_CLOSE', 'Конечное «Закрыто»'),
    ('WAY_OPEN', 'Промежуточное (открытие)'),
    ('WAY_CLOSE', 'Промежуточное (закрытие)'),
    ('TORQUE_OPEN', 'Моментный «Открыто»'),
    ('TORQUE_CLOSE', 'Моментный «Закрыто»'),
]


def _reset_feedback_signals(codes):
    """Удаляет сигналы по кодам, предварительно сняв PROTECT-ссылки."""
    CuSlotOption.objects.filter(feedback_signal__code__in=codes).update(
        feedback_signal=None)
    CuMatrixEntry.objects.filter(feedback_signal__code__in=codes).update(
        feedback_signal=None)
    CuFeedbackSignal.objects.filter(code__in=codes).delete()


class EnrichCuFeedbackSignalsTests(TestCase):
    def setUp(self):
        self.dry_spst, _ = CuFeedbackSignalForm.objects.get_or_create(
            code='DRY_SPST', defaults={'name': 'SPST', 'category': 'dry_output'})
        self.dry_spdt, _ = CuFeedbackSignalForm.objects.get_or_create(
            code='DRY_SPDT', defaults={'name': 'SPDT', 'category': 'dry_output'})
        self.an_active, _ = CuFeedbackSignalForm.objects.get_or_create(
            code='AN_4_20_ACTIVE',
            defaults={'name': '4-20 active', 'category': 'current_4_20'})

        # Сбрасываем и старые, и канонические коды — тест не должен зависеть
        # от того, прогнана ли уже команда по БД (--keepdb).
        codes = [
            'FB_ALARM', 'FB_ALARM_SPDT', 'FB_OVERHEAT_NC',
            'FB_OVERHEAT_SPST_NC', 'FB_REMOTE_NO', 'FB_READY_NO',
            'FB_OVERHEAT', 'FB_LOCAL_REMOTE', 'FB_READY',
            'FB_TORQUE_4_20MA', 'FB_TURN_COUNTER', 'FB_STOP',
            'FB_SELECTOR_POSITION', 'FB_PHASE_LOSS',
        ]
        for role, _ in DIRECTIONS:
            codes += [f'FB_{role}', f'FB_{role}_SPDT', f'FB_{role}_DPDT']
        _reset_feedback_signals(codes)

        # Исходное (до команды) состояние: дубли и нестыковки.
        CuFeedbackSignal.objects.create(
            code='FB_ALARM', name='Авария', role='ALARM', category='contact',
            form=self.dry_spdt, contact_normal=None)
        CuFeedbackSignal.objects.create(
            code='FB_ALARM_SPDT', name='Авария SPDT', role='ALARM',
            category='contact', form=self.dry_spdt, contact_normal='CHANGEOVER')
        CuFeedbackSignal.objects.create(
            code='FB_OVERHEAT_NC', name='Перегрев NC', role='OVERHEAT',
            category='contact', form=self.dry_spdt, contact_normal='NC')
        CuFeedbackSignal.objects.create(
            code='FB_OVERHEAT_SPST_NC', name='Перегрев SPST NC', role='OVERHEAT',
            category='contact', form=self.dry_spst, contact_normal='NC')
        CuFeedbackSignal.objects.create(
            code='FB_REMOTE_NO', name='Удалённое', role='LOCAL_REMOTE',
            category='contact', form=self.dry_spst, contact_normal='NO')
        CuFeedbackSignal.objects.create(
            code='FB_READY_NO', name='Готовность', role='READY',
            category='contact', form=self.dry_spdt, contact_normal='NO')

        # Направленные сигналы — старые форм-агностичные коды, которые
        # команда должна переименовать в *_SPDT (и довести норму контакта).
        for role, base in DIRECTIONS:
            CuFeedbackSignal.objects.create(
                code=f'FB_{role}', name=base, role=role, category='contact',
                form=self.dry_spdt, contact_normal=None)

    def _make_references(self):
        """Ссылки на дубли, которые команда должна перенаправить."""
        dev = CuFeedbackDevice.objects.create(
            code='T_THERMO', name='Термо', kind='THERMAL_SENSOR',
            technology='ELECTRONIC')
        fb_overheat_nc = CuFeedbackSignal.objects.get(code='FB_OVERHEAT_NC')
        fb_overheat_spst = CuFeedbackSignal.objects.get(
            code='FB_OVERHEAT_SPST_NC')
        dev.emits.add(fb_overheat_nc, fb_overheat_spst)

        node = CuSectionNode.objects.create(code='T_FB', name='T_FB')
        slot = CuSlot.objects.create(code='T_ALARM_SLOT', section=node)
        opt = CuSlotOption.objects.create(
            code='T_ALARM_SPDT', slot=slot, kind='signal',
            feedback_signal=CuFeedbackSignal.objects.get(code='FB_ALARM_SPDT'))
        return dev, opt

    def test_enrich_produces_canonical_dictionary(self):
        call_command('enrich_cu_feedback_signals')

        # Направленные контакты: форма в коде — SPDT и DPDT.
        for role, _ in DIRECTIONS:
            self.assertFalse(CuFeedbackSignal.objects.filter(
                code=f'FB_{role}').exists(), f'FB_{role}')
            spdt = CuFeedbackSignal.objects.get(code=f'FB_{role}_SPDT')
            self.assertEqual(spdt.form.code, 'DRY_SPDT')
            self.assertEqual(spdt.contact_normal, 'CHANGEOVER')
            dpdt = CuFeedbackSignal.objects.get(code=f'FB_{role}_DPDT')
            self.assertEqual(dpdt.form.code, 'DRY_DPDT')
            self.assertEqual(dpdt.contact_normal, 'CHANGEOVER')

        # Остальные роли.
        for code in ('FB_TORQUE_4_20MA', 'FB_TURN_COUNTER', 'FB_STOP',
                     'FB_SELECTOR_POSITION', 'FB_PHASE_LOSS'):
            self.assertTrue(CuFeedbackSignal.objects.filter(code=code).exists(),
                            code)

        self.assertFalse(CuFeedbackSignal.objects.filter(
            code='FB_ALARM_SPDT').exists())
        alarm = CuFeedbackSignal.objects.get(code='FB_ALARM')
        self.assertEqual(alarm.contact_normal, 'CHANGEOVER')
        self.assertEqual(alarm.form.code, 'DRY_SPDT')

        self.assertFalse(CuFeedbackSignal.objects.filter(
            code='FB_OVERHEAT_NC').exists())
        self.assertFalse(CuFeedbackSignal.objects.filter(
            code='FB_OVERHEAT_SPST_NC').exists())
        overheat = CuFeedbackSignal.objects.get(code='FB_OVERHEAT')
        self.assertEqual(overheat.contact_normal, 'NC')
        self.assertEqual(overheat.form.code, 'DRY_SPST')

        self.assertFalse(CuFeedbackSignal.objects.filter(
            code='FB_REMOTE_NO').exists())
        self.assertTrue(CuFeedbackSignal.objects.filter(
            code='FB_LOCAL_REMOTE').exists())
        self.assertFalse(CuFeedbackSignal.objects.filter(
            code='FB_READY_NO').exists())
        ready = CuFeedbackSignal.objects.get(code='FB_READY')
        self.assertEqual(ready.form.code, 'DRY_SPST')
        self.assertEqual(ready.contact_normal, 'NO')

        torque_analog = CuFeedbackSignal.objects.get(code='FB_TORQUE_4_20MA')
        self.assertEqual(torque_analog.role, 'TORQUE_ANALOG')
        self.assertEqual(torque_analog.category, 'analog')
        self.assertEqual(torque_analog.form.code, 'AN_4_20_ACTIVE')

    def test_repoint_references_before_delete(self):
        dev, opt = self._make_references()
        call_command('enrich_cu_feedback_signals')

        dev.refresh_from_db()
        self.assertEqual(set(dev.emits.values_list('code', flat=True)),
                         {'FB_OVERHEAT'})

        opt.refresh_from_db()
        self.assertEqual(opt.feedback_signal.code, 'FB_ALARM')

    def test_idempotent(self):
        call_command('enrich_cu_feedback_signals')
        n1 = CuFeedbackSignal.objects.count()
        call_command('enrich_cu_feedback_signals')
        n2 = CuFeedbackSignal.objects.count()
        self.assertEqual(n1, n2)

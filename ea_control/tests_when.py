# ea_control/tests_when.py
"""Тесты условной строки матрицы (slots.md §6) — на копии рабочей БД.

Тесты создают условные строки и полагаются на откат транзакции TestCase
(рабочую БД не изменяют; прогоняются на ``test_db.sqlite3`` — копии).
"""
from types import SimpleNamespace

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase

from ea_control.models import ControlUnit, CuMatrixEntry, CuSlot, CuSlotOption
from ea_control.services.cu_matrix import (_conditional_order,
                                           get_profile_defaults, resolve_slots,
                                           validate_selection)


def _edge(src, dst):
    """Синтетическая условная строка для проверки графа зависимостей."""
    return SimpleNamespace(
        when_slot_id=1, option_id=1,
        when_slot=SimpleNamespace(code=src),
        option=SimpleNamespace(slot=SimpleNamespace(code=dst)))


class CuConditionalOrderTests(TestCase):
    """Топологический порядок и детекция циклов (без БД)."""

    def test_cascade_order(self):
        self.assertEqual(
            _conditional_order([_edge('A', 'B'), _edge('B', 'C')]),
            ['A', 'B', 'C'])

    def test_cycle_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            _conditional_order([_edge('A', 'B'), _edge('B', 'A')])

    def test_no_conditional_rows(self):
        self.assertEqual(_conditional_order([]), [])


class CuConditionalRowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unit = ControlUnit.objects.get(code='INT-N-TORQUE')
        defaults = get_profile_defaults(cls.unit)
        default_code = defaults.get('CMD_WIRING')
        ws_qs = CuSlotOption.objects.filter(slot__code='CMD_WIRING')
        cls.ws_default = ws_qs.get(code=default_code)
        cls.ws_other = ws_qs.exclude(code=default_code).first()
        cls.ts_opt = CuSlotOption.objects.filter(slot__code='CMD_OPEN').first()
        cls.ts_code = cls.ts_opt.slot.code

    def _row(self, when_opt, op, availability='na', priority=0, option=None):
        target = option or self.ts_opt
        row = CuMatrixEntry.objects.create(
            slot=target.slot, option=target, control_unit=self.unit,
            availability=availability, when_slot=when_opt.slot,
            when_operator=op, priority=priority)
        if op != 'is_set':
            row.when_options.set([when_opt])
        return row

    def _codes(self, snapshot=None):
        return [p['option_code']
                for p in resolve_slots(self.unit, snapshot=snapshot).get(
                    self.ts_code, [])]

    def test_na_when_satisfied(self):
        self._row(self.ws_other, 'in', 'na')
        self.assertNotIn(self.ts_opt.code,
                         self._codes({'CMD_WIRING': self.ws_other.code}))
        self.assertIn(self.ts_opt.code,
                      self._codes({'CMD_WIRING': self.ws_default.code}))

    def test_not_in(self):
        self._row(self.ws_other, 'not_in', 'na')
        self.assertNotIn(self.ts_opt.code,
                         self._codes({'CMD_WIRING': self.ws_default.code}))
        self.assertIn(self.ts_opt.code,
                      self._codes({'CMD_WIRING': self.ws_other.code}))

    def test_is_set(self):
        self._row(self.ws_other, 'is_set', 'na')
        # is_set: любое значение (включая дефолт) → условие истинно
        self.assertNotIn(self.ts_opt.code,
                         self._codes({'CMD_WIRING': self.ws_other.code}))
        self.assertNotIn(self.ts_opt.code, self._codes({}))

    def test_priority_among_conditional(self):
        self._row(self.ws_other, 'in', 'na', priority=5)
        self._row(self.ws_other, 'in', 'opt', priority=10)
        # opt с большим priority перекрывает na
        self.assertIn(self.ts_opt.code,
                      self._codes({'CMD_WIRING': self.ws_other.code}))

    def test_single_std_invariant(self):
        # условный std на другую опцию слота вытесняет безусловный std
        other = (CuSlotOption.objects.filter(slot__code=self.ts_code)
                 .exclude(pk=self.ts_opt.pk).first())
        self._row(self.ws_other, 'in', 'std', option=other)
        payloads = resolve_slots(
            self.unit, snapshot={'CMD_WIRING': self.ws_other.code})[self.ts_code]
        stds = [p['option_code'] for p in payloads if p['availability'] == 'std']
        self.assertEqual(stds, [other.code])

    def test_clean_when_operator_required(self):
        row = CuMatrixEntry(
            slot=self.ts_opt.slot, option=self.ts_opt, control_unit=self.unit,
            when_slot=self.ws_other.slot)
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_clean_when_subtype_forbidden(self):
        subtype_slot = CuSlot.objects.get(slot_kind='subtype')
        row = CuMatrixEntry(
            slot=self.ts_opt.slot, option=self.ts_opt, control_unit=self.unit,
            when_slot=subtype_slot, when_operator='is_set')
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_clean_when_self_slot_forbidden(self):
        row = CuMatrixEntry(
            slot=self.ts_opt.slot, option=self.ts_opt, control_unit=self.unit,
            when_slot=self.ts_opt.slot, when_operator='is_set')
        with self.assertRaises(ValidationError):
            row.full_clean()

    def test_clean_when_options_membership(self):
        other_slot_opt = CuSlotOption.objects.filter(
            slot__code='CMD_CLOSE').first()
        row = CuMatrixEntry(
            slot=self.ts_opt.slot, option=self.ts_opt, control_unit=self.unit,
            when_slot=self.ws_other.slot, when_operator='in')
        row.save()
        row.when_options.add(other_slot_opt)
        with self.assertRaises(ValidationError):
            row.clean_when_options()

    def test_validate_selection_na_chosen(self):
        self._row(self.ws_other, 'in', 'na')
        before = resolve_slots(
            self.unit, snapshot={'CMD_WIRING': self.ws_default.code})
        selected = [p for p in before.get(self.ts_code, [])
                    if p['option_code'] == self.ts_opt.code]
        after = resolve_slots(
            self.unit, snapshot={'CMD_WIRING': self.ws_other.code})
        available = [p for payloads in after.values() for p in payloads]
        errors = validate_selection(selected, available)
        self.assertTrue(any('недоступна' in e for e in errors))

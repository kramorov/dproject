"""Тесты точечного (4/6-точечного) подбора и длинного формата таблицы моментов."""
from django.test import TestCase

from pneumatic_actuators.models import (
    PneumaticActuatorBody,
    BodyThrustTorqueTable,
)
from pneumatic_actuators.services.pointwise_selector import PointwiseSelector
from valve_data.models import (
    TorquePoint, TorqueThrustCharacteristics, ValveTorqueCoefficient,
    SealType, ValveSupportType,
)
from params.models import PneumaticAirSupplyPressure, ValveTypes


class TorquePointTests(TestCase):

    def test_seed_points(self):
        self.assertEqual(TorquePoint.objects.count(), 6)
        for code in ('bto', 'rto', 'eto', 'btc', 'rtc', 'etc'):
            self.assertTrue(TorquePoint.objects.filter(code=code).exists())

    def test_positions_pairing(self):
        bto = TorquePoint.objects.get(code='bto')
        etc = TorquePoint.objects.get(code='etc')
        self.assertEqual(bto.position, etc.position)          # start
        self.assertNotEqual(bto.direction, etc.direction)    # open vs close
        self.assertEqual(bto.counterpart().code, 'etc')
        self.assertEqual(TorquePoint.objects.get(code='btc').counterpart().code, 'eto')


class PointwiseSelectorTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.pressure_6 = PneumaticAirSupplyPressure.objects.get(code='6')
        cls.pressure_spring = PneumaticAirSupplyPressure.objects.get(code='spring')
        cls.factors = {
            'bto': 1.0, 'rto': 0.6, 'eto': 0.9,
            'btc': 0.9, 'rtc': 0.6, 'etc': 1.0,
        }

    def test_compute_required_curve(self):
        curve = PointwiseSelector.compute_required_curve(100.0, 1.3, self.factors)
        self.assertEqual(curve['bto'], 130.0)
        self.assertEqual(curve['rto'], 78.0)
        self.assertEqual(curve['etc'], 130.0)

    def test_select_da_finds_bodies(self):
        curve = PointwiseSelector.compute_required_curve(100.0, 1.3, self.factors)
        found = PointwiseSelector.select(
            table_model=BodyThrustTorqueTable,
            body_model=PneumaticActuatorBody,
            required=curve,
            actuator_variety='DA',
            safety_position='nc',
            work_pressure_id=self.pressure_6.id,
            max_bodies=50,
        )
        self.assertTrue(found, 'должны найтись DA-тела под 130 Нм при 6 бар')
        for r in found:
            self.assertEqual(r['type'], 'DA')
            self.assertGreaterEqual(r['margin'], 0)
            self.assertIn(r['critical_position'], ('start', 'mid', 'end'))

    def test_select_sr_nc(self):
        curve = PointwiseSelector.compute_required_curve(100.0, 1.3, self.factors)
        found = PointwiseSelector.select(
            table_model=BodyThrustTorqueTable,
            body_model=PneumaticActuatorBody,
            required=curve,
            actuator_variety='SR',
            safety_position='nc',
            work_pressure_id=self.pressure_6.id,
            max_bodies=50,
        )
        for r in found:
            self.assertEqual(r['type'], 'SR')
            self.assertNotEqual(r['spring_qty_code'], 'DA')
            self.assertGreaterEqual(r['margin'], 0)

    def test_required_curve_matches_coefficient_rows(self):
        """Кривая из коэффициентов: база × запас × factor (по данным rotary-6)."""
        char = TorqueThrustCharacteristics.objects.filter(code='rotary-6').first()
        if char is None:
            self.skipTest('набор rotary-6 не импортирован')
        ball = ValveTypes.objects.get(code='ball-valve')
        floating = ValveSupportType.objects.get(code='floating')
        soft = SealType.objects.get(code='soft')
        curve = ValveTorqueCoefficient.get_curve(char.id, ball.id, floating.id, soft.id)
        self.assertEqual(set(curve), {'bto', 'rto', 'eto', 'btc', 'rtc', 'etc'})
        self.assertEqual(curve['bto'], 1.0)
        self.assertEqual(curve['etc'], 1.0)
        self.assertLess(curve['rto'], 1.0)


class TorqueTablePivotTests(TestCase):

    def test_pivot_spring_reversed_to_display(self):
        """Пружина в длинном формате хранится под close-точками; в отображении
        разворачивается обратно: bto←etc, rto←rtc, eto←btc."""
        body = PneumaticActuatorBody.objects.filter(code='RT105').first()
        if body is None:
            self.skipTest('нет тела RT105 в тестовой БД')
        data = BodyThrustTorqueTable.get_torque_thrust_values(
            current_body=body, ncno_code='nc',
            construction_variety_code='RP', da_sr_code='SR')
        self.assertIn('data', data)
        by_spring = data['data']['by_spring']
        self.assertTrue(by_spring, 'таблица тела должна быть непустой')
        for code, grp in by_spring.items():
            if code == 'DA':
                continue
            spring_vals = grp['pressures'].get('spring')
            if spring_vals:
                # поля отображения — только bto/rto/eto
                self.assertTrue(set(spring_vals) <= {'bto', 'rto', 'eto'})

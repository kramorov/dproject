"""Тесты расшифровки кодов ЕТТ.

Тесты самодостаточны: перед прогоном удаляются записи с используемыми
символьными кодами, поэтому не зависят от наполнения тестовой БД.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    MtrType,
    DnType,
    PnType,
    EttActuatorType,
    EttClimaticOption,
    EttOpenTime,
    EttSeismicOption,
    EttElectricOptionsCombination,
    EttControlOptionsCombination,
    EttOtherOptionsCombination,
    EttStatusSignal,
    EttControlSignal,
    EttFeedbackSignal,
    EttControlUnitHeater,
    EttControlUnitType,
    EttControlUnitDisplayType,
    EttCableGlandType,
)
from params.models import IpOption, PowerSupplies
from .services import decode_ett


MANUAL_CODE = 'ЗК100*16-СП-Х-К0-12-К50/РР/Н/С0'
ELECTRIC_CODE = 'ЗК100*16-СП-Х-К0-12-К50/ЭПДА1/Н/С0'

# Символьные коды, по которым идёт lookup (могут существовать в тестовой БД).
_USED_CODES = {
    MtrType: ['ЗК'],
    DnType: ['100'],
    PnType: ['16'],
    EttClimaticOption: ['Х'],
    EttSeismicOption: ['С0'],
    EttActuatorType: ['РР', 'ЭП'],
    EttElectricOptionsCombination: ['Д'],
    EttControlOptionsCombination: ['А'],
    EttOtherOptionsCombination: ['1'],
}


class EttDecodeServiceTests(TestCase):
    def setUp(self):
        # Чистим конфликтующие записи, чтобы lookup вернул ровно наши фикстуры.
        for model, codes in _USED_CODES.items():
            model.objects.filter(symbolic_code__in=codes).delete()

    def _seed_common(self):
        mtr = MtrType.objects.create(symbolic_code='ЗК', text_description='Задвижка клиновая')
        dn = DnType.objects.create(symbolic_code='100', valve_dn_value=100, pipe_dn_value=0)
        pn = PnType.objects.create(symbolic_code='16', valve_pn_value=16)
        EttClimaticOption.objects.create(
            symbolic_code='Х',
            work_temp_min=-60,
            work_temp_max=40,
            extremal_temp_min=-70,
            extremal_temp_max=45,
            text_description='ХЛ',
        )
        EttSeismicOption.objects.create(symbolic_code='С0', text_description='Не сейсмостойкое')
        return mtr, dn, pn

    def test_empty_code_raises(self):
        with self.assertRaises(ValueError):
            decode_ett('')

    def test_wrong_field_count_raises(self):
        with self.assertRaises(ValueError):
            decode_ett('abc')

    def test_unknown_reference_raises(self):
        # Формат валиден (10 полей), но справочники пустые.
        with self.assertRaises(ValueError):
            decode_ett(MANUAL_CODE)

    def test_decode_manual(self):
        self._seed_common()
        EttActuatorType.objects.create(
            symbolic_code='РР',
            actuator_type='Ручной',
            actuator_speed='Стандарт',
            text_description='Ручной с редуктором',
        )

        result = decode_ett(MANUAL_CODE)
        table = {row['param_name']: row['param_value'] for row in result['desc_table']}

        self.assertEqual(table['Вид МТР'], 'Задвижка клиновая')
        self.assertEqual(table['DN, мм'], 100)
        self.assertEqual(table['Номинальное давление PN, кгс/см²'], 16)
        self.assertEqual(table['Тип привода'], 'Ручной с редуктором')
        self.assertEqual(table['Сейсмичность района размещения'], 'Не сейсмостойкое')
        # У ручного привода нет комбинаций ЭП.
        self.assertNotIn('Напряжение питания, В', table)

    def test_decode_electric(self):
        mtr, dn, pn = self._seed_common()
        EttActuatorType.objects.create(
            symbolic_code='ЭП',
            actuator_type='Электро',
            actuator_speed='Стандарт',
            text_description='Электропривод стандартный',
        )
        open_time = EttOpenTime.objects.create(
            symbolic_code='ЗК',
            dn_from=9,
            dn_up_to=300,
            time_to_open_min=0,
            time_to_open_max=60,
            actuator_speed='Стандарт',
        )
        open_time.mtr_type.add(mtr)

        ip = IpOption.objects.create(name='IP54', code='IP54', ip_rank=1)
        power = PowerSupplies.objects.create(
            name='220/50', code='220-AC', voltage_value=220, voltage_type='AC')
        EttElectricOptionsCombination.objects.create(
            symbolic_code='Д', ip_choice=ip, power_choice=power, exd_choice=None)

        status = EttStatusSignal.objects.create(
            symbolic_code='24 В с.к.', text_description='24 В сухой контакт')
        control = EttControlSignal.objects.create(
            symbolic_code='24 В', text_description='тип управляющего сигнала 24 В')
        feedback = EttFeedbackSignal.objects.create(
            symbolic_code='Не требуется', text_description='Не требуется')
        EttControlOptionsCombination.objects.create(
            symbolic_code='А',
            status_signal_choice=status,
            control_signal_choice=control,
            feedback_signal_choice=feedback,
        )

        cu_type = EttControlUnitType.objects.create(
            symbolic_code='НЭ', text_description='Установлен на электроприводе')
        cu_heater = EttControlUnitHeater.objects.create(
            symbolic_code='Да', text_description='ЭП оснащен встроенным электрообогревом блока управления')
        display = EttControlUnitDisplayType.objects.create(
            symbolic_code='Д', text_description='С дисплеем')
        cg = EttCableGlandType.objects.create(
            symbolic_code='Б', text_description='Для бронированного кабеля')
        EttOtherOptionsCombination.objects.create(
            symbolic_code='1',
            cu_location_choice=cu_type,
            cu_heater_choice=cu_heater,
            display_choice=display,
            cg1_choice=cg,
            cg23_choice=cg,
        )

        result = decode_ett(ELECTRIC_CODE)
        table = {row['param_name']: row['param_value'] for row in result['desc_table']}

        self.assertEqual(table['Время открытия макс, с'], 60)
        self.assertEqual(table['Напряжение питания, В'], '220/50')
        self.assertEqual(table['Исполнение по пылевлагозащите, не ниже'], 'IP54')
        self.assertEqual(table['Исполнение по взрывозащите'], '—')
        self.assertEqual(table['Сигнал обратной связи / Протокол'], 'Не требуется')
        self.assertEqual(table['Тип привода'], 'Электропривод стандартный')


class EttDecodeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_empty_code_returns_400(self):
        resp = self.client.post('/api/ett/decode/', {'code': ''}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)

    def test_wrong_format_returns_400(self):
        resp = self.client.post('/api/ett/decode/', {'code': 'abc'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)

    def test_non_dict_body_returns_400_not_500(self):
        # Валидный JSON, но не объект — не должен падать с 500.
        resp = self.client.post('/api/ett/decode/', ['not', 'an', 'object'], format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.data)

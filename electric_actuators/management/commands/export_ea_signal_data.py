"""
Выгрузка сигнальных данных электроприводов в JSON-снапшот (фаза 1 плана переезда).

Что выгружает
--------------
1. `ControlUnitSignalProfile` + `ControlUnitSignalProfileEntry` — профили сигналов:
   роль (SignalRole) → датчик (pa_controls.SensorComponent) или входной сигнал
   (params.InputSignalSpec), флаг калибровки.
2. `ControlUnitWiring` — связки «БУ × напряжение → профиль → схема подключения
   (медиабиблиотека) + питание обогрева». Флаг `verified` = True, когда схема
   прописана (в таких случаях данные о сигналах и формах проверены);
   модели без wiring-строки считаются НЕпроверенными (их нет в выгрузке).
3. Через-опции переключателей (End/Way/Torque) на model_line_item —
   encoding/ext_encoding/is_default/sorting_order + коды справочников.
4. `ElectricControlUnitOption` / `ElectricPowerSupplyOption` — объявленные пары
   БУ×напряжение (для валидации F5 при заливке в матрицу).
5. Маппинг-таблицы (F6 из ревью №2): SignalRole / InputSignalSpec / датчики →
   концепты новой схемы (роли/формы/протоколы) + отчёт «не распознано».

Использование
-------------
    python manage.py export_ea_signal_data [--output ea_signals_export.json]

JSON-структура
--------------
    meta          — дата выгрузки, счётчики, источник
    mapping       — словари F6: signal_role, input_signal, sensor (правила по имени)
    profiles      — профили с entries (role_code, sensor/input_signal, калибровка)
    wirings       — связки БУ×напряжение→схема (verified=True — схема прописана)
    control_unit_options  — пары БУ×напряжение (серия/item, коды, encoding/ext)
    power_supply_options  — напряжения по моделям (компактно)
    switches      — end/way/torque через-опции
    unmapped      — роли/входы/датчики без правила маппинга (требуют решения)
"""
import json

from django.core.management.base import BaseCommand
from django.apps import apps


# --- Маппинг-таблицы F6 (SignalRole → концепты новой схемы) ---

ROLE_TO_EA = {
    # Выходные роли
    'OUTPUT_OPEN': {'role': 'END_OPEN', 'direction': 'output'},
    'OUTPUT_CLOSE': {'role': 'END_CLOSE', 'direction': 'output'},
    'OUTPUT_WAY_SWITCH': {'role': 'WAY', 'direction': 'output',
                          'note': 'один промежуточный контакт'},
    'OUTPUT_WAY_SWITCH_X2': {'role': 'WAY', 'direction': 'output',
                             'note': 'два промежуточных контакта (два сигнала)'},
    'OUTPUT_TORQUE_OPEN': {'role': 'TORQUE_OPEN', 'direction': 'output'},
    'OUTPUT_TORQUE_CLOSE': {'role': 'TORQUE_CLOSE', 'direction': 'output'},
    'OUTPUT_CURRENT_POSITION': {'role': 'POSITION', 'direction': 'output',
                                'form_by_sensor': True},
    'OUTPUT_POTENTIOMETER': {'role': 'POSITION', 'direction': 'output',
                             'form': 'RES_POTENTIOMETER'},
    'OUTPUT_ALARM': {'role': 'ALARM', 'direction': 'output'},
    'OUTPUT_ALARM_2': {'role': 'ALARM', 'direction': 'output',
                       'note': 'второй контакт аварии'},
    'OUTPUT_REMOTE_CONTROL': {'role': 'READY', 'direction': 'output',
                              'note': 'подтверждение дистанционного режима '
                                      '(LOCAL/REMOTE indication)'},
    'OUTPUT_OVERHEAT': {'role': 'OVERHEAT', 'direction': 'output'},
    # Входные роли (форма — по InputSignalSpec)
    'INPUT_OPEN': {'role': 'CMD_OCS', 'direction': 'input', 'form_by_input_signal': True},
    'INPUT_STOP': {'role': 'CMD_OCS', 'direction': 'input', 'form_by_input_signal': True},
    'INPUT_CLOSE': {'role': 'CMD_OCS', 'direction': 'input', 'form_by_input_signal': True},
    'INPUT_POSITION': {'role': 'CMD_4_20MA', 'direction': 'input',
                       'form_by_input_signal': True},
    'INPUT_ESD': {'role': 'CMD_EMERGENCY', 'direction': 'input',
                  'form_by_input_signal': True},
    # Двунаправленные (шины / HART)
    'HART_DIAG': {'protocol': 'HART', 'note': 'диагностика/конфигурация HART'},
    'HART_POS': {'protocol': 'HART', 'note': 'положение с HART (hart=True на POSITION)'},
    'IN_OUT_DP_HART': {'protocol': 'HART', 'note': 'вх/вых 4-20 мА + HART'},
    'MODBUS_CTRL': {'protocol': 'MODBUS', 'note': 'RTU или TCP — по InputSignalSpec'},
    'PROFINET_CTRL': {'protocol': 'PROFINET', 'note': ''},
    'PROFIBUS_DP_CTRL': {'protocol': 'PROFIBUS_DP', 'note': ''},
    'FF_CTRL': {'protocol': 'FOUNDATION_FIELDBUS', 'note': ''},
}

INPUT_SIGNAL_TO_EA = {
    'CU_DI_24V_DC': {'form': 'DISC_DC', 'voltage': 24},
    'CU_DI_220V_AC': {'form': 'DISC_AC', 'voltage': 220},
    'CU_DI_ESD_NC': {'form': 'DISC_DC', 'voltage': 24,
                     'note': 'нормально-замкнутый, контроль обрыва цепи'},
    'CU_AI_4_20MA_PASSIVE': {'form': 'AN_4_20_PASSIVE'},
    'CU_AI_4_20MA_ACTIVE': {'form': 'AN_4_20_ACTIVE'},
    'MODBUS_RTU': {'protocol': 'MODBUS_RTU', 'transport': 'rs485'},
    'MODBUS_TCP': {'protocol': 'MODBUS_TCP', 'transport': 'ethernet'},
    'PROFIBUS_DP': {'protocol': 'PROFIBUS_DP', 'transport': 'rs485'},
    'PROFINET': {'protocol': 'PROFINET', 'transport': 'ethernet'},
    'HART': {'protocol': 'HART', 'note': 'hart=True на петле 4-20 мА'},
    'FOUNDATION_FIELDBUS': {'protocol': 'FOUNDATION_FIELDBUS', 'transport': 'h1'},
}

# Правила по подстроке имени датчика (SensorComponent)
SENSOR_NAME_RULES = [
    ('ЭП DPDT', {'form': 'DRY_DPDT'}),
    ('ЭП SPDT', {'form': 'DRY_SPDT'}),
    ('ЭП SPST-NO', {'form': 'DRY_SPST', 'contact': 'NO'}),
    ('ЭП SPST-NC', {'form': 'DRY_SPST', 'contact': 'NC'}),
    ('ЭП 4-20 мА, активный', {'form': 'AN_4_20_ACTIVE'}),
    ('ЭП 4-20 мА, пассивный', {'form': 'AN_4_20_PASSIVE'}),
    ('ЭП Потенциометр', {'form': 'RES_POTENTIOMETER'}),
    ('Токовый 9-28VDC, пассивный', {'form': 'AN_4_20_PASSIVE',
                                    'note': 'аварийный токовый выход'}),
]


def _code(obj):
    """Код объекта или его строковое представление (защита от отсутствия code)."""
    code = getattr(obj, 'code', None)
    if code:
        return str(code)
    return str(obj)


def _map_sensor(name):
    """Правило маппинга датчика по подстроке имени; None — не распознано."""
    for needle, rule in SENSOR_NAME_RULES:
        if needle in name:
            return rule
    return None


class Command(BaseCommand):
    help = 'Выгрузка сигнальных данных ЭП в JSON-снапшот (фаза 1 плана переезда)'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default=None,
                            help='Путь к выходному JSON (по умолчанию '
                                 'ea_signals_export_<дата>.json в корне проекта)')

    def handle(self, *args, **options):
        from params.models import ControlUnitSignalProfile
        from electric_actuators.models import ControlUnitWiring

        Profile = ControlUnitSignalProfile
        Wiring = ControlUnitWiring
        EndOpt = apps.get_model('electric_actuators', 'ElectricEndSwitchesOption')
        WayOpt = apps.get_model('electric_actuators', 'ElectricWaySwitchesOption')
        TorqueOpt = apps.get_model('electric_actuators', 'ElectricTorqueSwitchesOption')
        CUOpt = apps.get_model('electric_actuators', 'ElectricControlUnitOption')
        PSOpt = apps.get_model('electric_actuators', 'ElectricPowerSupplyOption')

        snapshot = {'meta': {}, 'mapping': {}, 'profiles': [], 'wirings': [],
                    'control_unit_options': [], 'power_supply_options': [],
                    'switches': {'end': [], 'way': [], 'torque': []},
                    'unmapped': {'roles': [], 'input_signals': [], 'sensors': [],
                                 'foreign_sensors': []}}

        # --- 1. Профили сигналов ---
        profiles = []
        for p in Profile.objects.prefetch_related('entries').all():
            entries = []
            for e in p.entries.select_related('signal_role', 'sensor', 'input_signal').all():
                rec = {
                    'role_code': e.signal_role.code,
                    'role_direction': e.signal_role.direction,
                    'is_default_calibration': e.is_default_calibration,
                }
                if e.sensor_id:
                    rec['sensor'] = {'id': e.sensor_id, 'name': e.sensor.name,
                                     'code': getattr(e.sensor, 'code', None)}
                    if e.signal_role.code not in ROLE_TO_EA:
                        snapshot['unmapped']['roles'].append(e.signal_role.code)
                    rec['sensor_map'] = _map_sensor(e.sensor.name)
                    if rec['sensor_map'] is None:
                        if e.sensor.name.startswith('ЭП'):
                            snapshot['unmapped']['sensors'].append(e.sensor.name)
                        else:
                            # Датчики БКВ/позиционеров — вне скоупа миграции ЭП
                            snapshot['unmapped']['foreign_sensors'].append(
                                e.sensor.name)
                if e.input_signal_id:
                    rec['input_signal'] = {'id': e.input_signal_id,
                                           'code': e.input_signal.code,
                                           'name': e.input_signal.name,
                                           'category': e.input_signal.signal_category,
                                           'specs': e.input_signal.electrical_specs,
                                           'wires': e.input_signal.wires_count}
                    if e.input_signal.code not in INPUT_SIGNAL_TO_EA:
                        snapshot['unmapped']['input_signals'].append(
                            e.input_signal.code)
                entries.append(rec)
            profiles.append({'id': p.id, 'code': p.code, 'name': p.name,
                             'description': p.description, 'entries': entries})
        snapshot['profiles'] = profiles

        # --- 2. Связки БУ×напряжение→схема ---
        wirings = []
        for w in Wiring.objects.select_related(
                'control_unit', 'power_supply', 'signal_profile',
                'wiring_diagram', 'heater_supply').all():
            diagram = None
            if w.wiring_diagram_id:
                diagram = {'id': w.wiring_diagram_id,
                           'code': getattr(w.wiring_diagram, 'code', None),
                           'name': w.wiring_diagram.name}
            wirings.append({
                'code': w.code, 'name': w.name,
                'control_unit': {'id': w.control_unit_id,
                                 'code': w.control_unit.code,
                                 'name': w.control_unit.name},
                'power_supply': {'id': w.power_supply_id,
                                 'code': _code(w.power_supply),
                                 'name': str(w.power_supply)},
                'signal_profile': {'id': w.signal_profile_id,
                                   'code': w.signal_profile.code,
                                   'name': w.signal_profile.name},
                'wiring_diagram': diagram,
                'heater_supply': {'id': w.heater_supply_id,
                                  'code': _code(w.heater_supply),
                                  'name': str(w.heater_supply)}
                if w.heater_supply_id else None,
                # Схема прописана => данные о сигналах/формах проверены
                'verified': diagram is not None,
            })
        snapshot['wirings'] = wirings

        # --- 3. Пары БУ×напряжение (F5) ---
        cu_options = []
        for o in CUOpt.objects.select_related(
                'power_supply_option__model_line_item__model_line',
                'power_supply_option__power_supply',
                'control_unit', 'control_unit_wiring').all():
            item = o.power_supply_option.model_line_item
            line = item.model_line
            cu_options.append({
                'series_code': getattr(line, 'code', None) or str(line),
                'series_name': str(line),
                'item': getattr(item, 'code', None) or str(item),
                'power_supply': _code(o.power_supply_option.power_supply),
                'control_unit': o.control_unit.code,
                'wiring': o.control_unit_wiring.code if o.control_unit_wiring_id else None,
                'encoding': o.encoding, 'ext_encoding': o.ext_encoding,
                'is_default': o.is_default,
            })
        snapshot['control_unit_options'] = cu_options

        ps_options = []
        for o in PSOpt.objects.select_related(
                'model_line_item__model_line', 'power_supply').all():
            ps_options.append({
                'series_code': getattr(o.model_line_item.model_line, 'code', None)
                or str(o.model_line_item.model_line),
                'item': getattr(o.model_line_item, 'code', None)
                or str(o.model_line_item),
                'power_supply': _code(o.power_supply),
                'encoding': o.encoding, 'ext_encoding': o.ext_encoding,
                'is_default': o.is_default,
            })
        snapshot['power_supply_options'] = ps_options

        # --- 4. Через-опции переключателей ---
        for key, model in (('end', EndOpt), ('way', WayOpt), ('torque', TorqueOpt)):
            rows = []
            ref_field = {'end': 'end_switches_option',
                         'way': 'way_switches_option',
                         'torque': 'torque_switches_option'}[key]
            qs = model.objects.select_related(
                'model_line_item__model_line', ref_field).all()
            for o in qs:
                ref = getattr(o, ref_field)
                rows.append({
                    'series_code': getattr(o.model_line_item.model_line, 'code', None)
                    or str(o.model_line_item.model_line),
                    'item': getattr(o.model_line_item, 'code', None)
                    or str(o.model_line_item),
                    'reference': {'id': ref.id, 'code': _code(ref),
                                  'name': str(ref)},
                    'encoding': o.encoding, 'ext_encoding': o.ext_encoding,
                    'is_default': o.is_default,
                    'sorting_order': o.sorting_order,
                    'is_active': o.is_active,
                })
            snapshot['switches'][key] = rows

        # --- 5. Маппинг и мета ---
        snapshot['mapping'] = {
            'signal_role': ROLE_TO_EA,
            'input_signal': INPUT_SIGNAL_TO_EA,
            'sensor_name_rules': [{'needle': n, 'rule': r}
                                  for n, r in SENSOR_NAME_RULES],
        }
        snapshot['meta'] = {
            'exported_at': None,  # заполняется ниже (часовой пояс приложения)
            'profiles': len(profiles),
            'wirings': len(wirings),
            'wirings_verified': sum(1 for w in wirings if w['verified']),
            'control_unit_options': len(cu_options),
            'power_supply_options': len(ps_options),
            'switches_end': len(snapshot['switches']['end']),
            'switches_way': len(snapshot['switches']['way']),
            'switches_torque': len(snapshot['switches']['torque']),
        }
        from django.utils import timezone
        snapshot['meta']['exported_at'] = timezone.now().isoformat()

        # Уникализация unmapped
        for k in snapshot['unmapped']:
            snapshot['unmapped'][k] = sorted(set(snapshot['unmapped'][k]))

        # --- Запись ---
        out_path = options.get('output')
        if not out_path:
            out_path = 'ea_signals_export_{}.json'.format(
                timezone.now().strftime('%Y-%m-%d'))
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(snapshot, fh, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(
            'Снапшот записан: {}'.format(out_path)))
        self.stdout.write(
            'profiles={} wirings={} (verified={}) cu_options={} '
            'ps_options={} switches end/way/torque={}/{}/{}'.format(
                len(profiles), len(wirings),
                sum(1 for w in wirings if w['verified']),
                len(cu_options), len(ps_options),
                len(snapshot['switches']['end']),
                len(snapshot['switches']['way']),
                len(snapshot['switches']['torque'])))
        self.stdout.write(
            'unmapped: roles={} input_signals={} sensors={} foreign_sensors={}'.format(
                len(snapshot['unmapped']['roles']),
                len(snapshot['unmapped']['input_signals']),
                len(snapshot['unmapped']['sensors']),
                len(snapshot['unmapped']['foreign_sensors'])))
        if snapshot['unmapped']['roles']:
            self.stdout.write(self.style.WARNING(
                '  роли без маппинга: ' + ', '.join(snapshot['unmapped']['roles'])))
        if snapshot['unmapped']['sensors']:
            self.stdout.write(self.style.WARNING(
                '  ЭП-датчики без маппинга: ' + '; '.join(snapshot['unmapped']['sensors'])))
        if snapshot['unmapped']['foreign_sensors']:
            self.stdout.write(
                '  чужие датчики (БКВ/позиционеры, вне скоупа ЭП): ' +
                '; '.join(snapshot['unmapped']['foreign_sensors']))
        if snapshot['unmapped']['input_signals']:
            self.stdout.write(self.style.WARNING(
                '  входы без маппинга: ' + ', '.join(snapshot['unmapped']['input_signals'])))

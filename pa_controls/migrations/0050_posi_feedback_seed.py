# pa_controls/migrations/0050_posi_feedback_seed.py
"""Стартовое наполнение обратной связи позиционеров (серия TS):

- Noname-датчики позиционеров (бренд Tissin), отдельно от датчиков БКВ/ЭП:
    POSI-PT-420  — трансмиттер 4-20 мА (встроенный, конкретная марка неизвестна)
    POSI-LS-SPDT — концевой выключатель SPDT (считаем, что Limit Switch = SPDT)
- Профили сигналов обратной связи (codes с префиксом POSI-TS), каждый включает
  стандартный вход 4-20 мА (INPUT_POSITION → CU_AI_4_20MA_PASSIVE) и варианты
  обратной связи из каталога TS:
    POSI-TS-PT           Position transmitter (4~20mA DC)
    POSI-TS-HART         HART
    POSI-TS-HART-PT      HART and Position transmitter (4~20mA DC)
    POSI-TS-W-LS         With Limit Switch
    POSI-TS-W-LS-EX      With Limit Switch (Explosion proof type)
    POSI-TS-W-PT-LS      With Position transmitter and Limit Switch
    POSI-TS-W-PT-LS-EX   With Position transmitter and Limit Switch (Explosion proof type)
    POSI-TS-W-EXT-LS     With external Limit switch mounting device
    POSI-TS-W-PT-EXT-LS  With Position transmitter and external Limit switch mounting device

Ex-варианты отличаются только названием/кодом: Ex — свойство исполнения
позиционера, связывается с опцией взрывозащиты через флаг only_non_ex
на through-опциях серии (см. 0049).
"""
from django.db import migrations


SENSORS = [
    {
        'code': 'POSI-PT-420',
        'name': 'Трансмиттер 4-20 мА (позиционер)',
        'variety': 'TRANS',
        'signal_type': 'ANALOG',
        'contact_form': 'NONE',
        'contact_state': 'NONE',
        'electrical_specs': '4-20 мА DC, 2-проводное подключение',
        'wires_count': 2,
    },
    {
        'code': 'POSI-LS-SPDT',
        'name': 'Концевой выключатель SPDT (позиционер)',
        'variety': 'MECH',
        'signal_type': 'DRY',
        'contact_form': 'SPDT',
        'contact_state': 'CO',
        'electrical_specs': 'SPDT (перекидной контакт)',
        'wires_count': 3,
    },
]

# (code, name, description, [(role_code, sensor_code|None, input_signal_code|None)])
PROFILES = [
    (
        'POSI-TS-PT',
        'Position transmitter (4~20mA DC)',
        'Обратная связь: позиционный трансмиттер 4-20 мА.',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_CURRENT_POSITION', 'POSI-PT-420', None),
        ],
    ),
    (
        'POSI-TS-HART',
        'HART',
        'Обратная связь: HART.',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('HART_POS', None, 'HART'),
        ],
    ),
    (
        'POSI-TS-HART-PT',
        'HART and Position transmitter (4~20mA DC)',
        'Обратная связь: HART + позиционный трансмиттер 4-20 мА.',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('HART_POS', None, 'HART'),
            ('OUTPUT_CURRENT_POSITION', 'POSI-PT-420', None),
        ],
    ),
    (
        'POSI-TS-W-LS',
        'With Limit Switch',
        'Обратная связь: концевой выключатель SPDT.',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
    (
        'POSI-TS-W-LS-EX',
        'With Limit Switch (Explosion proof type)',
        'Обратная связь: концевой выключатель SPDT (взрывозащищённое исполнение).',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
    (
        'POSI-TS-W-PT-LS',
        'With Position transmitter and Limit Switch',
        'Обратная связь: трансмиттер 4-20 мА + концевой выключатель SPDT.',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_CURRENT_POSITION', 'POSI-PT-420', None),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
    (
        'POSI-TS-W-PT-LS-EX',
        'With Position transmitter and Limit Switch (Explosion proof type)',
        'Обратная связь: трансмиттер 4-20 мА + концевой выключатель SPDT '
        '(взрывозащищённое исполнение).',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_CURRENT_POSITION', 'POSI-PT-420', None),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
    (
        'POSI-TS-W-EXT-LS',
        'With external Limit switch mounting device',
        'Обратная связь: концевой выключатель SPDT (внешнее устройство монтажа).',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
    (
        'POSI-TS-W-PT-EXT-LS',
        'With Position transmitter and external Limit switch mounting device',
        'Обратная связь: трансмиттер 4-20 мА + концевой выключатель SPDT '
        '(внешнее устройство монтажа).',
        [
            ('INPUT_POSITION', None, 'CU_AI_4_20MA_PASSIVE'),
            ('OUTPUT_CURRENT_POSITION', 'POSI-PT-420', None),
            ('OUTPUT_OPEN', 'POSI-LS-SPDT', None),
            ('OUTPUT_CLOSE', 'POSI-LS-SPDT', None),
        ],
    ),
]


def fill_posi_feedback_seed(apps, schema_editor):
    SensorComponent = apps.get_model('pa_controls', 'SensorComponent')
    LimitSwitchSensorVariety = apps.get_model('pa_controls', 'LimitSwitchSensorVariety')
    SignalType = apps.get_model('pa_controls', 'SignalType')
    ContactForm = apps.get_model('pa_controls', 'ContactForm')
    ContactState = apps.get_model('pa_controls', 'ContactState')
    Brands = apps.get_model('producers', 'Brands')
    ControlUnitSignalProfile = apps.get_model('params', 'ControlUnitSignalProfile')
    ControlUnitSignalProfileEntry = apps.get_model('params', 'ControlUnitSignalProfileEntry')
    SignalRole = apps.get_model('params', 'SignalRole')
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')

    brand = Brands.objects.filter(name='Tissin').first()

    # Словари на свежей БД могут отсутствовать (наполняются отдельными сидами/
    # командами) — создаём при необходимости, чтобы SensorComponent не получал
    # NULL в NOT NULL-поля (slots.md §5.10).
    variety_by_code = {}
    for code, name in (('TRANS', 'Трансмиттер'), ('MECH', 'Механический')):
        variety_by_code[code], _ = LimitSwitchSensorVariety.objects.get_or_create(
            code=code, defaults={'name': name, 'is_active': True})
    signal_type_by_code = {}
    for code, name in (('ANALOG', 'Аналоговый'), ('DRY', 'Сухой контакт')):
        signal_type_by_code[code], _ = SignalType.objects.get_or_create(
            code=code, defaults={'name': name, 'is_active': True})
    contact_form_by_code = {}
    for code, name, wires in (('NONE', 'Нет', 0),
                              ('SPDT', 'Однополюсный перекидной', 3)):
        contact_form_by_code[code], _ = ContactForm.objects.get_or_create(
            code=code, defaults={'name': name, 'wires_required': wires,
                                 'is_active': True})
    contact_state_by_code = {}
    for code, name in (('NONE', 'Нет'), ('CO', 'Перекидной')):
        contact_state_by_code[code], _ = ContactState.objects.get_or_create(
            code=code, defaults={'name': name, 'is_active': True})

    sensor_by_code = {}
    for item in SENSORS:
        sensor, _ = SensorComponent.objects.get_or_create(
            code=item['code'],
            defaults={
                'name': item['name'],
                'brand': brand,
                'variety': variety_by_code.get(item['variety']),
                'signal_type': signal_type_by_code.get(item['signal_type']),
                'contact_form': contact_form_by_code.get(item['contact_form']),
                'contact_state': contact_state_by_code.get(item['contact_state']),
                'electrical_specs': item['electrical_specs'],
                'wires_count': item['wires_count'],
                'is_active': True,
            },
        )
        sensor_by_code[item['code']] = sensor

    for order, (code, name, description, entries) in enumerate(PROFILES, start=1):
        profile, _ = ControlUnitSignalProfile.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'sorting_order': 200 + order,
                'is_active': True,
            },
        )
        for role_code, sensor_code, spec_code in entries:
            role = SignalRole.objects.filter(code=role_code).first()
            if not role:
                continue
            defaults = {'is_default_calibration': True}
            if sensor_code:
                defaults['sensor'] = sensor_by_code.get(sensor_code)
            if spec_code:
                defaults['input_signal'] = InputSignalSpec.objects.filter(
                    code=spec_code).first()
            ControlUnitSignalProfileEntry.objects.get_or_create(
                profile=profile,
                signal_role=role,
                defaults=defaults,
            )


def reverse_fill_posi_feedback_seed(apps, schema_editor):
    SensorComponent = apps.get_model('pa_controls', 'SensorComponent')
    ControlUnitSignalProfile = apps.get_model('params', 'ControlUnitSignalProfile')

    ControlUnitSignalProfile.objects.filter(
        code__in=[p[0] for p in PROFILES]
    ).delete()
    SensorComponent.objects.filter(
        code__in=[s['code'] for s in SENSORS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pa_controls', '0049_posibodyconnectionoption_only_non_ex_and_more'),
        ('params', '0069_add_way_switch_x2_role'),
    ]

    operations = [
        migrations.RunPython(fill_posi_feedback_seed, reverse_fill_posi_feedback_seed),
    ]

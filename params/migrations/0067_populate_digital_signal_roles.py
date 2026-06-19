# Generated manually — add digital protocol SignalRole entries
from django.db import migrations


def create_digital_roles(apps, schema_editor):
    SignalRole = apps.get_model('params', 'SignalRole')

    roles = [
        {
            'name': 'Управление и диагностика Modbus RTU/TCP',
            'code': 'MODBUS_CTRL',
            'direction': 'bidirectional',
            'description': (
                'Цифровой обмен данными по протоколу Modbus (RTU или TCP). '
                'Вход: команды управления (ОТКРЫТЬ/ЗАКРЫТЬ/СТОП/ПОЗИЦИЯ). '
                'Выход: текущее положение, состояние, момент, аварии, диагностика.'
            ),
            'sorting_order': 110,
            'is_active': True,
        },
        {
            'name': 'Циклический обмен Profibus DP',
            'code': 'PROFIBUS_DP_CTRL',
            'direction': 'bidirectional',
            'description': (
                'Циклический обмен данными по Profibus DP между Master (ПЛК) и Slave (БУ). '
                'Вход: управляющее слово, уставка положения. '
                'Выход: слово состояния, текущее положение, момент, диагностика DP-V1.'
            ),
            'sorting_order': 120,
            'is_active': True,
        },
        {
            'name': 'Управление и диагностика Profinet',
            'code': 'PROFINET_CTRL',
            'direction': 'bidirectional',
            'description': (
                'Обмен данными по Profinet RT/IRT между контроллером и БУ. '
                'Вход: управляющее слово, уставка положения. '
                'Выход: слово состояния, текущее положение, момент, диагностика.'
            ),
            'sorting_order': 130,
            'is_active': True,
        },
        {
            'name': 'Диагностика и конфигурация HART',
            'code': 'HART_DIAG',
            'direction': 'bidirectional',
            'description': (
                'Цифровой HART-протокол поверх аналоговой токовой петли 4-20мА. '
                'Вход: конфигурация, калибровка, команды диагностики. '
                'Выход: диагностические данные, журнал событий, версия ПО. '
                'Аналоговый сигнал положения идёт отдельной ролью (выход 4-20мА).'
            ),
            'sorting_order': 140,
            'is_active': True,
        },
        {
            'name': 'Управление и диагностика Foundation Fieldbus',
            'code': 'FF_CTRL',
            'direction': 'bidirectional',
            'description': (
                'Обмен данными по Foundation Fieldbus H1. '
                'Вход: Function Block-команды (AO, DO), уставки. '
                'Выход: Function Block-обратная связь (AI, DI), диагностика, тревоги. '
                'Поддерживает Control in the Field — ПИД-регулятор выполняется в БУ.'
            ),
            'sorting_order': 150,
            'is_active': True,
        },
        {
            'name': 'Текущее положение с HART',
            'code': 'HART_POS',
            'direction': 'bidirectional',
            'description': (
                'Аналоговый сигнал 4-20мА положения + цифровой HART-протокол. '
                '4-20мА: 4 мА = 0% (закрыто), 20 мА = 100% (открыто). '
                'HART: диагностика, конфигурация, до 4 переменных процесса. '
                'Используется для современных БУ с поддержкой HART 5/6/7.'
            ),
            'sorting_order': 160,
            'is_active': True,
        },
    ]

    for role in roles:
        SignalRole.objects.get_or_create(
            code=role['code'],
            defaults=role,
        )


def remove_digital_roles(apps, schema_editor):
    SignalRole = apps.get_model('params', 'SignalRole')
    codes = [
        'MODBUS_CTRL', 'PROFIBUS_DP_CTRL', 'PROFINET_CTRL',
        'HART_DIAG', 'FF_CTRL', 'HART_POS',
    ]
    SignalRole.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0066_fix_modbus_rtu'),
    ]
    operations = [
        migrations.RunPython(create_digital_roles, remove_digital_roles),
    ]

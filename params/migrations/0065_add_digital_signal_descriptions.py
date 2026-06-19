# Generated manually — add descriptions to digital InputSignalSpec entries
from django.db import migrations


def add_descriptions(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')

    descriptions = {
        'MODBUS_RTU': (
            'Последовательный протокол, стандарт де-факто для электроприводной арматуры. '
            'Master-Slave по RS-485, открытый стандарт (Modbus Organization). '
            'До 247 устройств на одной шине. Поддерживается всеми ПЛК и SCADA-системами '
            '(Siemens, Schneider, ОВЕН, Текон, Emerson). Дальность до 1200 м без повторителей. '
            'Простота реализации — требуется только витая пара (A/B) и терминаторы 120 Ом по краям.'
        ),
        'MODBUS_TCP': (
            'Modbus поверх Ethernet TCP/IP. Быстрее RTU, неограниченная дальность (сеть предприятия). '
            'Удобен для интеграции с верхним уровнем (SCADA, DCS). Требует IP-адресации. '
            'Поддерживается теми же SCADA/ПЛК что и Modbus RTU. Рекомендуется для новой стройки '
            'с Ethernet-инфраструктурой до уровня полевых устройств.'
        ),
        'PROFIBUS_DP': (
            'Промышленная шина Siemens, циклический обмен данными между Master и Slaves. '
            'Стандарт IEC 61158. Скорость до 12 Мбит/с. GSD-файл описывает профиль устройства '
            '(загружается в конфигуратор ПЛК). Распространён в Европе на крупных АСУ ТП: '
            'химия, нефтегаз, металлургия. Требует Profibus-мастер (CP 342-5, CP 443-5 и т.д.).'
        ),
        'PROFINET': (
            'Промышленный Ethernet Siemens, преемник Profibus DP. Полный дуплекс, '
            'поддержка RT (Real-Time, < 10 мс) и IRT (Isochronous Real-Time, < 1 мс). '
            'Совместим с Profibus через прокси-переходники (IE/PB Link). Поддерживает '
            'топологии: звезда, кольцо, линия. Рекомендуется для новых объектов Siemens.'
        ),
        'HART': (
            'Highway Addressable Remote Transducer — цифровой протокол, наложенный '
            'на аналоговую токовую петлю 4-20мА методом частотной модуляции (Bell 202 FSK: '
            'логическая «1» — 1.2 кГц, «0» — 2.2 кГц). Совместим с существующей аналоговой '
            'инфраструктурой — работает по тем же двум проводам. Передаёт диагностику, '
            'конфигурацию и до 4 переменных процесса одновременно с аналоговым током. '
            'Двунаправленный — не требует отдельной входной и выходной роли. '
            'Поддерживается Emerson, Siemens, ABB, Metso, AUMA, Rotork. HART 7 — до 256 приборов на шине.'
        ),
        'FOUNDATION_FIELDBUS': (
            'Цифровая полевая шина для процессной автоматики (стандарт IEC 61158). '
            'Manchester-кодирование, 31.25 кбит/с. Питание устройств осуществляется '
            'по сигнальной линии (power on signal) через Fieldbus Power Supply. '
            'Поддерживает Function Blocks — логика управления выполняется непосредственно '
            'в полевых устройствах (Control in the Field). Распространён на НПЗ и химических '
            'производствах (Emerson DeltaV, Yokogawa Centum, Honeywell Experion). Требует '
            'терминаторов на концах сегмента и согласующих устройств (Power Conditioner).'
        ),
    }

    for code, desc in descriptions.items():
        InputSignalSpec.objects.filter(code=code).update(description=desc)


def remove_descriptions(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')
    codes = [
        'MODBUS_RTU', 'MODBUS_TCP', 'PROFIBUS_DP', 'PROFINET',
        'HART', 'FOUNDATION_FIELDBUS',
    ]
    InputSignalSpec.objects.filter(code__in=codes).update(description='')


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0064_populate_digital_signal_specs'),
    ]
    operations = [
        migrations.RunPython(add_descriptions, remove_descriptions),
    ]

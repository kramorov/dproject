# electric_actuators/services/ea_ext_code.py
"""
Таблицы ext-кодировок привода (позиции артикула).

Позиционная система сборки/расшифровки ext-кода заказа (`coding_rules`,
`build_ext_code`, `decode_ext_code`, `option_position_code`, `CU_EXT`) удалена
вместе с legacy сигнальной матрицей (фаза 4, 2026-11-26). Ext-код привода
теперь собирается по ``model_line.ext_encoding_template`` в
``ElectricActuatorConstructor.generated_ext_code`` /
``ElectricActuatorCatalogItem.generated_ext_code``, вклад БУ — из
``ea_control.services.cu_code``.

Здесь остаются только статические таблицы кодов, которые используют
конструктор и карточка каталога.
"""

# Напряжение мотора → код позиции {ps}
PS_EXT = {'220-AC': '220AC', '380-AC': '380AC', '24-DC': '24DC'}

# Температурное исполнение → базовый код позиции {temp}
# (суффикс 'M' добавляется при обогреве от цепей двигателя MOTOR_CIRCUIT).
TEMP_BASE = {'STD': 'ST', 'LT': 'L', 'VLT': 'V'}

# Положение безопасности → код позиции {sp}
SP_EXT = {'fl': 'FL', 'nc': 'NC', 'no': 'NO', 'nc-no-fl': 'BAT'}

# Устройство ограничения доступа → код позиции {ad}
AD_EXT = {'NO_DEVICE': 'AD0', 'DEVICE': 'AD1'}

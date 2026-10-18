"""
Модели приложения electric_actuators.

Импорт всех моделей для обнаружения Django.
Файлы моделей:
    ea_model_line.py            — ElectricActuatorModelLine (серия)
    ea_model_line_item.py       — ElectricActuatorModelLineItem (модель в серии)
    ea_model_line_item_options.py — Through-опции уровня model_line_item
    ea_options.py               — Through-опции уровня model_line
    ea_allowed_options.py       — Allowed*Option (кодировки опций для серии)
    ea_model_body.py            — ModelBody (корпус)
    ea_body.py                  — ElectricActuatorBody (таблица корпусов)
    ea_cg_holes_set.py          — CableGlandHolesSet (кабельные вводы)
    ea_actuator_constructor.py  — Конструктор (пошаговый подбор)
    ea_actuator_selected.py     — Сохранённая конфигурация
    ea_data.py                  — Технические данные
    ea_signal_form.py           — EaSignalForm (формы сигналов)
    ea_signals.py               — EaControlSignal / EaFeedbackSignal
    ea_comm_protocol.py         — EaCommProtocol (шины)
    ea_feedback_device.py       — EaFeedbackDevice (устройства ОС)
    ea_signal_slot.py           — EaSignalSlot (слоты матрицы)
    ea_signal_matrix.py         — EaSignalMatrixEntry, EaWiringDiagramBinding
"""
from .ea_model_line import *
from .ea_data import *
from .ea_model_body import *
from .ea_access_device import *
from .ea_cg_holes_set import *
from .ea_options import *
from .ea_body import *
from .ea_model_line_item_options import *
from .ea_allowed_options import *
from .ea_model_line_item import *
from .ea_actuator_selected import *
from .ea_actuator_constructor import *
from .ea_signal_form import *
from .ea_signals import *
from .ea_comm_protocol import *
from .ea_feedback_device import *
from .ea_slot_option import *
from .ea_signal_slot import *
from .ea_signal_matrix import *

__all__ = [
    # все модели, которые должны быть доступны извне
    'ElectricActuatorModelLine',
    'ModelLine',
    'ElectricActuatorData',
    'ModelBody',
    'CableGlandHolesSet',
    'ElectricHandWheelOption',
    'ElectricTemperatureOption',
    'ElectricIpOption',
    'ElectricExdOption',
    'ElectricBodyCoatingOption',
    'ElectricTurnAngleOption',
    'ElectricPowerSupplyOption',
    'ElectricSafetyPositionOption',
    'ElectricActuatorBody',
    'ElectricActuatorModelLineItem',
    'ElectricActuatorSelected',
    'CableGlandHolesSetBodyOption',
    'ElectricActuatorBodyTable',
    'ElectricBodyColorOption',
    'ElectricActuatorConstructor',
    'AllowedControlUnitOption',
    'AllowedTurnCounterOption',
    'EaSignalForm',
    'EaControlSignal',
    'EaFeedbackSignal',
    'EaCommProtocol',
    'EaFeedbackDevice',
    'EaSignalSlot',
    'EaSignalMatrixEntry',
    'EaWiringDiagramBinding',
    'EaSlotOption',

]
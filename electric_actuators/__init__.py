"""
Приложение electric_actuators — каталог и конфигуратор электроприводов.

Архитектура:
- ModelLine → ModelLineItem → PowerSupplyOption → ControlUnitOption
- Through-модели хранят encoding и is_default для каждой пары (серия, опция)
- Allowed*Option — единый источник кодировок на уровне model_line
- Конструктор (ElectricActuatorConstructor) — пошаговый подбор с FK на реальные опции
- Selected (ElectricActuatorSelected) — сохранённая конфигурация с артикулом
"""

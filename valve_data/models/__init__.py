# valve_data/models/__init__.py
# Сначала импортируем модели из dimensions
from .base_models import (
    AllowedDnTemplate, ValveConnectionToPipe, ValveVariety,
    ConstructionVariety, PortQty, ValveModelDataTable,
    ValveModelKvDataTable, ValveLineModelKvData, ValveLineModelData,
    ValveLineBodyColor, EAVAttribute, EAVValue, ValveVarietyAttribute,
    # WeightDimensionParameter  # ← ДОБАВЬТЕ ЭТО
)

# Импорты из подпапки dimensions с относительными путями
from .dimensions.valve_dimension_data import ValveDimensionData
from .dimensions.valve_dimension_table import ValveDimensionTable
from .dimensions.dimension_table_parameter import DimensionTableParameter
from .dimensions.dimension_table_drawing_item import DimensionTableDrawingItem
from .dimensions.weight_dimension_parameter_variety import WeightDimensionParameterVariety

# Потом импортируем ValveLine (теперь ValveDimensionTable уже загружен)
from .valve_line import ValveLine

# from .drawing_models import DimensionTableDrawing
__all__ = [
    'AllowedDnTemplate', 'ValveConnectionToPipe', 'ValveVariety',
    'ConstructionVariety', 'PortQty', 'ValveModelDataTable',
    'ValveModelKvDataTable', 'ValveLineModelKvData', 'ValveLineModelData',
    'ValveLineBodyColor', 'EAVAttribute', 'EAVValue', 'ValveVarietyAttribute',
    'ValveDimensionTable',
    'ValveDimensionData',
    'DimensionTableParameter',
    'DimensionTableDrawingItem',
    'WeightDimensionParameterVariety',
    'ValveLine'
]
# pneumatic_actuators/api/views.py
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)


class OptionAPIView(APIView):
    """
    Публичный API для получения опций пневмопривода.

    Поддерживает два режима:
    1. Параметры model_line_id / model_line_item_id / actuator_variety_id —
       возвращает опции через get_actuator_options() (каскадная фильтрация).
    2. Параметр model_id — создаёт временный PneumaticActuatorSelected
       и возвращает опции через get_available_options() (админка).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/pneumatic_actuators/options/
        Query params: model_line_id, model_line_item_id, actuator_variety_id, model_id.
        """
        model_line_id = request.GET.get('model_line_id')
        model_line_item_id = request.GET.get('model_line_item_id')
        actuator_variety_id = request.GET.get('actuator_variety_id')

        model_id = request.GET.get('model_id')
        if model_id:
            from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
            from pneumatic_actuators.models import PneumaticActuatorSelected
            model = PneumaticActuatorModelLineItem.objects.get(id=int(model_id))
            temp_actuator = PneumaticActuatorSelected(selected_model_line_item=model)
            return JsonResponse(temp_actuator.get_available_options())

        # Все остальные случаи (включая пустой запрос) — каскадная фильтрация
        from pneumatic_actuators.actuator_selector_handler import get_actuator_options
        options = get_actuator_options(
            model_line_id=int(model_line_id) if model_line_id else None,
            model_line_item_id=int(model_line_item_id) if model_line_item_id else None,
            actuator_variety_id=int(actuator_variety_id) if actuator_variety_id else None,
        )
        return JsonResponse(options)


class SelectorAPIView(APIView):
    """
    Публичный API подбора пневмопривода по параметрам арматуры.

    GET  — справочники для загрузки страницы (модели, DN, PN, штоки и т.д.).
    POST — поиск подходящих приводов по заданным параметрам.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/pneumatic_actuators/selector/initial-data/
        Возвращает справочные данные: model_lines, dn_varieties, pn_varieties,
        air_pressure, mounting_plates, stem_shapes, stem_sizes, valve_types.
        """
        from pneumatic_actuators.actuator_selector_handler import get_initial_data
        return JsonResponse(get_initial_data())

    def post(self, request):
        """
        POST /api/pneumatic_actuators/selector/search/
        Принимает JSON с параметрами арматуры и требованиями к приводу,
        валидирует, вызывает BodyThrustTorqueTable.find_suitable_actuators(),
        возвращает {success, search_results, total_found}.
        """
        params = request.data
        from pneumatic_actuators.actuator_selector_handler import process_selection_params
        result = process_selection_params(params)
        if result.get('success'):
            return JsonResponse(result)
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=400)

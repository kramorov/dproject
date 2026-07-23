# pneumatic_actuators/api/views.py
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)


class OptionAPIView(View):
    def get(self, request):
        model_line_id = request.GET.get('model_line_id')
        model_line_item_id = request.GET.get('model_line_item_id')
        actuator_variety_id = request.GET.get('actuator_variety_id')

        if model_line_id or model_line_item_id or actuator_variety_id:
            from pneumatic_actuators.actuator_selector_handler import get_actuator_options
            options = get_actuator_options(
                model_line_id=int(model_line_id) if model_line_id else None,
                model_line_item_id=int(model_line_item_id) if model_line_item_id else None,
                actuator_variety_id=int(actuator_variety_id) if actuator_variety_id else None,
            )
            return JsonResponse(options)

        model_id = request.GET.get('model_id')
        if not model_id:
            return JsonResponse({'error': 'model_id or model_line_id required'}, status=400)
        try:
            from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
            from pneumatic_actuators.models import PneumaticActuatorSelected
            model = PneumaticActuatorModelLineItem.objects.get(id=int(model_id))
            temp_actuator = PneumaticActuatorSelected(selected_model_line_item=model)
            return JsonResponse(temp_actuator.get_available_options())
        except PneumaticActuatorModelLineItem.DoesNotExist:
            return JsonResponse({'error': 'Model not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SelectorAPIView(View):
    """API для подбора пневмопривода по параметрам арматуры."""

    def get(self, request):
        from pneumatic_actuators.actuator_selector_handler import get_initial_data
        return JsonResponse(get_initial_data())

    def post(self, request):
        try:
            params = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        from pneumatic_actuators.actuator_selector_handler import process_selection_params
        result = process_selection_params(params)
        if result.get('success'):
            return JsonResponse(result)
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=400)

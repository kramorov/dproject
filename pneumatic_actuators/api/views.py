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
        print(f"OptionAPIView - get called. REquest:{request}")
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        model_id = request.GET.get('model_id')
        if not model_id:
            return JsonResponse({'error': 'model_id required'}, status=400)

        try:
            from pneumatic_actuators.models import PneumaticActuatorSelected
            model = PneumaticActuatorModelLineItem.objects.get(id=int(model_id))
            print(f"Trying to get model id=:{int(model_id)}")

            temp_actuator = PneumaticActuatorSelected(selected_model_line_item=model)
            options = temp_actuator.get_available_options()

            return JsonResponse(options)

        except PneumaticActuatorModelLineItem.DoesNotExist:
            return JsonResponse({'error': 'Model PneumaticActuatorModelLineItem not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SelectorAPIView(View):
    """API для подбора пневмопривода по параметрам арматуры."""

    def get(self, request):
        """GET /selector/initial-data/ — начальные данные для формы."""
        from pneumatic_actuators.actuator_selector_handler import get_initial_data
        data = get_initial_data()
        return JsonResponse(data)

    def post(self, request):
        """POST /selector/search/ — подбор привода по параметрам."""
        try:
            params = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

        from pneumatic_actuators.actuator_selector_handler import process_selection_params
        result = process_selection_params(params)

        if result.get('success'):
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'error_fields': result.get('error_fields', []),
            }, status=400)
# pneumatic_actuators/api/views.py
from django.http import JsonResponse
from django.views import View

import logging
logger = logging.getLogger(__name__)


class OptionAPIView(View):
    def get(self, request):
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        model_id = request.GET.get('model_id')
        if not model_id:
            return JsonResponse({'error': 'model_id required'}, status=400)

        try:
            from pneumatic_actuators.models import PneumaticActuatorSelected
            model = PneumaticActuatorModelLineItem.objects.get(id=int(model_id))

            temp_actuator = PneumaticActuatorSelected(selected_model=model)
            options = temp_actuator.get_available_options()

            return JsonResponse(options)

        except PneumaticActuatorModelLineItem.DoesNotExist:
            return JsonResponse({'error': 'Model PneumaticActuatorModelLineItem not found'}, status=404)
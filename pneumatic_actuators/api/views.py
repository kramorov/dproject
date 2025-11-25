# pneumatic_actuators/api/views.py
from django.http import JsonResponse
from django.views import View
from ..services.option_service import OptionService


class OptionAPIView(View) :
    """API для получения опций - прообраз GraphQL резолвера"""

    def get(self , request) :
        model_id = request.GET.get('model_id')
        if not model_id :
            return JsonResponse({'error' : 'model_id required'} , status=400)

        options = OptionService.get_available_options(int(model_id))
        return JsonResponse(options)
# pneumatic_actuators/api/views.py
from django.http import JsonResponse
from django.views import View


class OptionAPIView(View) :
    def get(self , request) :
        model_id = request.GET.get('model_id')  # ID PneumaticActuatorModelLineItem
        if not model_id :
            return JsonResponse({'error' : 'model_id required'} , status=400)

        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem

        try :
            # Находим КОНКРЕТНУЮ МОДЕЛЬ привода (PneumaticActuatorModelLineItem)
            model = PneumaticActuatorModelLineItem.objects.get(id=int(model_id))

            # Создаем временный объект PneumaticActuatorSelected для получения опций
            from pneumatic_actuators.models.pa_actuator_selected import PneumaticActuatorSelected
            temp_actuator = PneumaticActuatorSelected(selected_model=model)

            # Получаем все доступные опции для этой модели
            options = temp_actuator.get_available_options()
            return JsonResponse(options)

        except PneumaticActuatorModelLineItem.DoesNotExist :
            return JsonResponse({'error' : 'Model not found'} , status=404)
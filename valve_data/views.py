# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .models import ValveLine, EAVAttribute , EAVValue
# from .serializers import ValveLineSerializer
# from django.http import JsonResponse
#
#
# def get_eav_values_for_attribute(request, attribute_id):
#     """API для получения значений атрибута"""
#     try:
#         attribute = EAVAttribute.objects.get(id=attribute_id)
#         values = EAVValue.objects.filter(
#             attribute=attribute,
#             is_active=True
#         ).order_by('order', 'display_name')
#
#         data = {
#             'values': [
#                 {
#                     'id': value.id,
#                     'display_name': value.display_name or str(value),
#                     'value': value.value
#                 } for value in values
#             ]
#         }
#         return JsonResponse(data)
#     except EAVAttribute.DoesNotExist:
#         return JsonResponse({'values': []})
#
# # class ValveModelDataAPIView(APIView):
# #     def get(self, request, pk, *args, **kwargs):
# #         try:
# #             valve_model = ValveModelData.objects.get(pk=pk)
# #             serializer = ValveModelDataSerializer(valve_model)
# #             return Response(serializer.data)
# #         except ValveModelData.DoesNotExist:
# #             return Response({'error': 'Модель не найдена'}, status=404)
#
# class ValveLineAPIView(APIView):
#     def get(self, request, pk, *args, **kwargs):
#         try:
#             valve_line = ValveLine.objects.get(pk=pk)
#             serializer = ValveLineSerializer(valve_line)
#             return Response(serializer.data)
#         except ValveLine.DoesNotExist:
#             return Response({'error': 'Модель не найдена'}, status=404)
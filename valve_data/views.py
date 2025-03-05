from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ValveLine, ValveModelData
from .serializers import ValveLineSerializer, ValveModelDataSerializer

class ValveModelDataAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        try:
            valve_model = ValveModelData.objects.get(pk=pk)
            serializer = ValveModelDataSerializer(valve_model)
            return Response(serializer.data)
        except ValveModelData.DoesNotExist:
            return Response({'error': 'Модель не найдена'}, status=404)

class ValveLineAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        try:
            valve_line = ValveLine.objects.get(pk=pk)
            serializer = ValveLineSerializer(valve_line)
            return Response(serializer.data)
        except ValveLine.DoesNotExist:
            return Response({'error': 'Модель не найдена'}, status=404)
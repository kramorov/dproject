from django.db.models import CharField
from rest_framework.serializers import ModelSerializer, StringRelatedField, DateField, IntegerField
from rest_framework import serializers

from .models import ClientRequestItem, ValveRequirement, ElectricActuatorRequirement

from .models import ClientRequest, ClientRequestItem, ValveRequirement, ElectricActuatorRequirement

from client_request.models import ClientRequestType, ClientRequest, ClientRequestItem, ElectricActuatorRequirement, \
    ValveRequirement


class ClientRequestTypeSerializer(ModelSerializer):
    class Meta:
        model = ClientRequestType
        depth = 4
        fields = '__all__'


class ValveRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValveRequirement
        fields = ['id', 'get_text_description']  # Добавьте другие поля, если необходимо


class ElectricActuatorRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricActuatorRequirement
        fields = ['id']  # Добавьте другие поля, если необходимо



# Выводит список строк запроса клиента, каждая строка содержит поля requrements
# class ClientRequestItemListView(APIView):
# path('clientrequestitemlist/', views.ClientRequestItemListView.as_view()),
class ClientRequestItemListSerializer(serializers.Serializer):
    request_parent = serializers.IntegerField()

    @staticmethod
    def validate_request_parent(self, value):
        # Проверка, что request_parent существует
        if not ClientRequest.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"ClientRequest с ID={value} не существует.")
        return value

    def to_representation(self, instance):
        request_parent = instance['request_parent']
        items = ClientRequestItem.objects.filter(request_parent=request_parent)
        return ClientRequestItemSerializer(items, many=True).data


class ClientRequestListSerializer(ModelSerializer):
    symbolic_code = StringRelatedField()  # Покажет строковое представление модели
    request_type = StringRelatedField()  # Покажет строковое представление модели
    request_from_client_company = StringRelatedField()  # Покажет строковое представление модели
    request_responsible_person = StringRelatedField()
    formatted_request_date_str = serializers.SerializerMethodField()
    formatted_created_at_str = serializers.SerializerMethodField()
    formatted_updated_at_str = serializers.SerializerMethodField()

    class Meta:
        model = ClientRequest
        fields = ['id', 'symbolic_code', 'request_type', 'request_from_client_company',
                  'request_responsible_person', 'formatted_request_date_str', 'formatted_created_at_str',
                  'formatted_updated_at_str']
        depth = 1  # Ограничиваем глубину вложенности

    @staticmethod
    def get_formatted_request_date_str(obj):
        return obj.request_date.strftime('%Y-%m-%d')

    @staticmethod
    def get_formatted_created_at_str(obj):
        return obj.created_at.strftime('%Y-%m-%d')

    @staticmethod
    def get_formatted_updated_at_str(obj):
        return obj.updated_at.strftime('%Y-%m-%d')


class ClientRequestSerializer(ModelSerializer):
    class Meta:
        model = ClientRequest
        depth = 4
        fields = '__all__'


class ClientRequestItemSerializer(ModelSerializer):
    class Meta:
        model = ClientRequestItem
        depth = 4
        fields = '__all__'


class ElectricActuatorRequirementSerializer(ModelSerializer):
    class Meta:
        model = ElectricActuatorRequirement
        depth = 4
        fields = '__all__'


class ValveRequirementSerializer(ModelSerializer):
    class Meta:
        model = ValveRequirement
        depth = 4
        fields = '__all__'

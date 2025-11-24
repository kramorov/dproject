from django.db.models import CharField
from rest_framework.serializers import ModelSerializer, StringRelatedField, DateField, IntegerField
from rest_framework import serializers

from clients.models import Company, CompanyPerson
from djangoProject1.common_models.abstract_serializers import FormDataSerializer
from .models import ClientRequests, ClientRequestsType, ClientRequestItem, ElectricActuatorRequirement, ClientRequestsStatus



class ClientRequestTypeSerializer(FormDataSerializer):
    default_value = serializers.SerializerMethodField()
    class Meta:
        model = ClientRequestsType
        depth = 4
        fields = [f.name for f in
                  ClientRequestsType._meta.get_fields() if not f.is_relation  # Исключаем связанные поля
                 ] + ['default_value']

    def get_default_value(self, obj):
        return 3

class ClientRequestStatusSerializer(FormDataSerializer):
    default_value = serializers.SerializerMethodField()
    class Meta:
        model = ClientRequestsStatus
        depth = 4
        fields = [f.name for f in ClientRequestsStatus._meta.get_fields() if not f.is_relation  # Исключаем связанные поля
                 ] + ['default_value']
    def get_default_value(self, obj):
        return 3


class ClientRequestItemSerializer_Short(serializers.ModelSerializer):
    valve_requirement = serializers.SerializerMethodField()
    electric_actuator_requirement = serializers.SerializerMethodField()
    request_parent_id = serializers.PrimaryKeyRelatedField(read_only=True)
    # request_parent_id = serializers.IntegerField(source='request_parent.id', read_only=True)

    class Meta:
        model = ClientRequestItem
        # fields = ['id', 'request_parent_id']  # Явно указываем только нужные поля
        fields = [
            'id',
            'request_parent_id',  # Используем вместо request_parent
            'item_no',
            'request_line_number',
            'source_request_line_number',
            'request_line_text',
            'request_line_ol',
            'valve_requirement',
            'electric_actuator_requirement'
        ]

    @staticmethod
    # def get_valve_requirement(obj):
    #     try:
    #         valve_requirement = obj.valve_requirement_for_request_line
    #         return ValveRequirementSerializer(valve_requirement).data
    #     except ValveRequirement.DoesNotExist:
    #         return None

    @staticmethod
    def get_electric_actuator_requirement(obj):
        try:
            electric_actuator_requirement = obj.electric_actuator_requirement_for_request_line
            return ElectricActuatorRequirementSerializer(electric_actuator_requirement).data
        except ElectricActuatorRequirement.DoesNotExist:
            return None

# Выводит список строк запроса клиента, каждая строка содержит поля requrements
# class ClientRequestItemListView(APIView):
# path('clientrequestitemlist/', views.ClientRequestItemListView.as_view()),
class ClientRequestItemListSerializer(serializers.Serializer):
    request_parent = serializers.IntegerField()

    @staticmethod
    def validate_request_parent(self, value):
        # Проверка, что request_parent существует
        if not ClientRequests.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"ClientRequest с ID={value} не существует.")
        return value

    def to_representation(self, instance):
        request_parent = instance['request_parent']
        items = ClientRequestItem.objects.filter(request_parent=request_parent)
        return ClientRequestItemSerializer(items, many=True).data


# class ClientRequestListSerializer(ModelSerializer):
class ClientRequestListSerializer(FormDataSerializer):
    class Meta(FormDataSerializer.Meta):
        abstract = False  # Делаем конкретным сериализатором
        model = ClientRequests
        fields = ['id', 'symbolic_code', 'request_type', 'request_from_client_company', 'request_status', 'end_customer',
                  'request_responsible_person', 'request_date', 'created_at',
                  'updated_at']
        depth = 1  # Ограничиваем глубину вложенности

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     print(f"Serializing: {instance.id} -> {data}")  # Для дебага
    #     return data

class ClientRequestSaveSerializer(ModelSerializer):
    request_type = serializers.PrimaryKeyRelatedField(queryset=ClientRequestsType.objects.all())
    request_from_client_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    request_responsible_person = serializers.PrimaryKeyRelatedField(queryset=CompanyPerson.objects.all())
    request_status = serializers.PrimaryKeyRelatedField(queryset=ClientRequestsStatus.objects.all())
    class Meta:
        model = ClientRequests
        fields = ['id', 'symbolic_code', 'request_type', 'request_from_client_company', 'request_status', 'end_customer',
                  'request_responsible_person', 'request_date', 'created_at',
                  'updated_at']
        depth = 2  # Ограничиваем глубину вложенности

class ClientRequestsSerializer(FormDataSerializer):
    class Meta:
        model = ClientRequests
        depth = 4
        fields = '__all__'


class ClientRequestItemSerializer(ModelSerializer):
    class Meta:
        model = ClientRequestItem
        depth = 4
        fields = '__all__'


class ElectricActuatorRequirementSerializer(ModelSerializer):
    client_request_line_item_parent_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ElectricActuatorRequirement
        depth = 4
        fields = ['id',
                  'time_to_open', 'rotations_to_open', 'rotations_angle', 'stem_shape',
                  'stem_size', 'safety_position', 'time_to_open_measure_unit',
                  'rotations_to_open_measure_unit', 'ip', 'body_coating',
                  'exd', 'temperature','mechanical_indicator','cable_glands_holes','blinker',
                  'end_switches','way_switches','torque_switches','output_type',
                  'digital_protocol_support','control_unit_type','control_unit_installed','control_unit_location',
                  'operating_mode',
                  'client_request_line_item_parent_id']

#
# class ValveRequirementSerializer(ModelSerializer):
#     client_request_line_item_parent_id = serializers.PrimaryKeyRelatedField(read_only=True)
#     valve_requirement_text_description = serializers.SerializerMethodField()
#     class Meta:
#         model = ValveRequirement
#         depth = 4
#         # fields = '__all__'
#         fields = ['id','valve_requirement_text_description',
#                   'valve_model_dn', 'valve_model_pn', 'valve_model_pn_delta', 'valve_model_torque_to_open',
#                   'valve_model_torque_to_close', 'valve_model_rotations_to_open', 'valve_stem_retract_type',
#                   'valve_model_model_line_str', 'valve_model_pn_measure_unit', 'valve_model_pn_delta_measure_unit',
#                   'valve_model_stem_size', 'valve_type',
#                   'client_request_line_item_parent_id']
#
#     def get_valve_requirement_text_description(self, obj):
#         return obj.get_text_description()

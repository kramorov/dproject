from rest_framework import serializers

from client_requests.models import (
    ClientRequest,
    ClientRequestItem,
    RequestItemType,
)


class RequestItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItemType
        fields = '__all__'


class ClientRequestSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_blank=True)
    status_code = serializers.SerializerMethodField()

    class Meta:
        model = ClientRequest
        fields = '__all__'

    def get_status_code(self, obj):
        return obj.request_status.code if obj.request_status else None


class ClientRequestItemSerializer(serializers.ModelSerializer):
    item_type_code = serializers.SerializerMethodField()

    class Meta:
        model = ClientRequestItem
        fields = '__all__'

    def get_item_type_code(self, obj):
        return obj.item_type.symbolic_code if obj.item_type else None

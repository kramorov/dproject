from rest_framework import viewsets

from core.permissions import SystemObjectPermission
from client_requests.models import (
    ClientRequest,
    ClientRequestItem,
    RequestItemType,
)
from .serializers import (
    ClientRequestSerializer,
    ClientRequestItemSerializer,
    RequestItemTypeSerializer,
)


class ClientRequestViewSet(viewsets.ModelViewSet):
    """CRUD для ClientRequest (заявка клиента)."""
    queryset = ClientRequest.objects.select_related(
        'request_status', 'request_from_client_company',
    ).order_by('-request_date', '-created_at')
    serializer_class = ClientRequestSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'client_requests.admin'
    required_action = 'edit'
    search_fields = ['code', 'name', 'client_request_number', 'end_customer']


class ClientRequestItemViewSet(viewsets.ModelViewSet):
    """CRUD для ClientRequestItem (позиция заявки)."""
    queryset = ClientRequestItem.objects.select_related(
        'request_parent', 'item_type',
    ).order_by('request_parent', 'item_no', '-version')
    serializer_class = ClientRequestItemSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'client_requests.admin'
    required_action = 'edit'
    filterset_fields = ['request_parent', 'status', 'is_current']


class RequestItemTypeViewSet(viewsets.ModelViewSet):
    """CRUD для RequestItemType (тип подбора)."""
    queryset = RequestItemType.objects.all().order_by('sort_order', 'symbolic_code')
    serializer_class = RequestItemTypeSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'client_requests.admin'
    required_action = 'edit'

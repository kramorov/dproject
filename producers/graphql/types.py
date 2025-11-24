import graphene
from graphene_django import DjangoObjectType

from producers.models import Brands , Producer


class BrandsNode(DjangoObjectType):
    class Meta:
        model = Brands
        fields = (
            'id',       # Автоматически создаваемый ID
            'name',     # CharField (название бренда)
        )

class ProducerNode(DjangoObjectType):
    class Meta:
        model = Producer
        fields = ('id', 'organization', 'brands')
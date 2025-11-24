import graphene
from graphene_django.types import DjangoObjectType

from producers.graphql.types import BrandsNode , ProducerNode
from producers.models import Brands , Producer


class Query(graphene.ObjectType):
    # Запросы для Brands
    producers_all_brands = graphene.List(BrandsNode)
    producers_brand_by_id = graphene.Field(BrandsNode, id=graphene.Int())

    # Запросы для Producer
    producers_all_producers = graphene.List(ProducerNode)
    producers_producer_by_id = graphene.Field(ProducerNode, id=graphene.Int())

    producers_producers_by_organization = graphene.List(
        ProducerNode ,
        name_contains=graphene.String()
    )

    def resolve_producers_producers_by_organization(self , info , name_contains=None , **kwargs) :
        qs = Producer.objects.all()
        if name_contains :
            qs = qs.filter(organization__icontains=name_contains)
        return qs

    def resolve_producers_all_brands(self, info, **kwargs):
        return Brands.objects.all()

    def resolve_producers_brand_by_id(self, info, id):
        return Brands.objects.get(pk=id)

    def resolve_producers_all_producers(self, info, **kwargs):
        return Producer.objects.all()

    def resolve_producers_producer_by_id(self, info, id):
        return Producer.objects.get(pk=id)
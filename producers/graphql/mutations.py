import graphene
from graphene_django.types import DjangoObjectType
from producers.models import Brands, Producer

# Типы (как у вас уже есть)
class BrandsNode(DjangoObjectType):
    class Meta:
        model = Brands
        fields = ('id', 'name')

class ProducerNode(DjangoObjectType):
    class Meta:
        model = Producer
        fields = ('id', 'organization', 'brands')

# ====================== Brands Mutations ======================
class CreateBrand(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    brand = graphene.Field(BrandsNode)

    def mutate(self, info, name):
        brand = Brands.objects.create(name=name)
        return CreateBrand(brand=brand)

class UpdateBrand(graphene.Mutation):
    class Arguments:
        brand_id = graphene.ID(required=True)
        name = graphene.String()

    brand = graphene.Field(BrandsNode)

    def mutate(self, info, brand_id, name=None):
        brand = Brands.objects.get(pk=brand_id)
        if name:
            brand.name = name
            brand.save()
        return UpdateBrand(brand=brand)

class DeleteBrand(graphene.Mutation):
    class Arguments:
        brand_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, brand_id):
        brand = Brands.objects.get(pk=brand_id)
        brand.delete()
        return DeleteBrand(success=True)

# ====================== Producer Mutations ======================
class CreateProducer(graphene.Mutation):
    class Arguments:
        organization = graphene.String(required=True)
        brand_ids = graphene.List(graphene.ID)  # Список ID брендов

    producer = graphene.Field(ProducerNode)

    def mutate(self, info, organization, brand_ids=None):
        producer = Producer.objects.create(organization=organization)
        if brand_ids:
            producer.brands.set(brand_ids)
        return CreateProducer(producer=producer)

class UpdateProducer(graphene.Mutation):
    class Arguments:
        producer_id  = graphene.ID(required=True)
        organization = graphene.String()
        brand_ids = graphene.List(graphene.ID)

    producer = graphene.Field(ProducerNode)

    def mutate(self, info, producer_id , organization=None, brand_ids=None):
        producer = Producer.objects.get(pk=id)
        if organization:
            producer.organization = organization
        if brand_ids is not None:  # Явная проверка, чтобы очистить список, если brand_ids=[]
            producer.brands.set(brand_ids)
        producer.save()
        return UpdateProducer(producer=producer )

class DeleteProducer(graphene.Mutation):
    class Arguments:
        producer_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, producer_id):
        producer = Producer.objects.get(pk=producer_id)
        producer.delete()
        return DeleteProducer(producer=producer)

# ====================== Объединяем все мутации ======================
class Mutation(graphene.ObjectType):
    producers_create_brand = CreateBrand.Field()
    producers_update_brand = UpdateBrand.Field()
    producers_delete_brand = DeleteBrand.Field()

    producers_create_producer = CreateProducer.Field()
    producers_update_producer = UpdateProducer.Field()
    producers_delete_producer = DeleteProducer.Field()


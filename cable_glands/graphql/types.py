import graphene
from graphene_django import DjangoObjectType
# from graphene_django.filter import DjangoFilterConnectionField

from cable_glands.models import  (
    CableGlandItemType,
    CableGlandBodyMaterial,
    CableGlandModelLine,
    CableGlandItem
)
from params.graphql.types import IpOptionNode


# Типы



# class CableGlandModelLineType(DjangoObjectType):
#     full_description = graphene.List(DescriptionItemType)
#
#     class Meta:
#         model = CableGlandModelLine
#         interfaces = (graphene.relay.Node,)
#         fields = '__all__'
#         filter_fields = {
#             'symbolic_code': ['exact', 'icontains'],
#             'brand__name': ['exact', 'icontains'],
#             'cable_gland_type__name': ['exact', 'icontains'],
#             'for_armored_cable': ['exact'],
#             'for_metal_sleeve_cable': ['exact'],
#             'for_pipelines_cable': ['exact'],
#         }
#
#     def resolve_full_description(self, info):
#         return self.get_full_description()
#
# class CableGlandItemType(DjangoObjectType):
#     full_description = graphene.List(DescriptionItemType)
#
#     class Meta:
#         model = CableGlandItem
#         interfaces = (graphene.relay.Node,)
#         fields = '__all__'
#         filter_fields = {
#             'name': ['exact', 'icontains'],
#             'model_line__symbolic_code': ['exact', 'icontains'],
#             'cable_gland_body_material__name': ['exact', 'icontains'],
#             'exd_same_as_model_line': ['exact'],
#             'temp_min': ['exact', 'gte', 'lte'],
#             'temp_max': ['exact', 'gte', 'lte'],
#         }
#
#     def resolve_full_description(self, info):
#         return self.get_full_description()


class DescriptionItemType(graphene.ObjectType):
    param_name = graphene.String()
    param_text = graphene.String()
    param_value = graphene.String()

class CableGlandModelLineNode(DjangoObjectType):
    flat_ip = graphene.List(IpOptionNode)
    class Meta:
        model = CableGlandModelLine
        # interfaces = (graphene.relay.Node,)
        fields = ["id","symbolic_code","brand","cable_gland_type","ip","exd",
                  "for_armored_cable","for_metal_sleeve_cable","for_pipelines_cable",
                  "thread_external","thread_internal","temp_min","temp_max","gost","text_description"]

    def resolve_flat_ip(self , info) :
        return self.ip.all()

class CableGlandItemNode(DjangoObjectType):

    class Meta:
        model = CableGlandItem
        # interfaces = (graphene.relay.Node,)
        fields = ["id", "name", "model_line", "cable_gland_body_material","exd_same_as_model_line","exd",
                  "thread_a","thread_b","temp_min","temp_max","cable_diameter_inner_min","cable_diameter_inner_max",
                  "cable_diameter_outer_min","cable_diameter_outer_max","dn_metal_sleeve","parent"]  # Явное указание полей лучше

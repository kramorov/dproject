#materials/graphql/types.py
import graphene
from graphene_django import DjangoObjectType

from materials.models import MaterialSpecified , MaterialGeneralMoreDetailed , MaterialGeneral , \
    MaterialCode , MaterialStandard


class MaterialStandardNode(DjangoObjectType) :
    class Meta :
        model = MaterialStandard
        fields = "__all__"


class MaterialCodeNode(DjangoObjectType) :
    standard_code = graphene.String()
    material_name = graphene.String()

    class Meta :
        model = MaterialCode
        fields = "__all__"

    def resolve_standard_code(self , info) :
        return self.standard.code if self.standard else None

    def resolve_material_name(self , info) :
        return self.material_specified.name if self.material_specified else None


# class MaterialAnalogNode(DjangoObjectType) :
#     source_material_code = graphene.String()
#     analog_material_code = graphene.String()
#
#     class Meta :
#         model = MaterialAnalog
#         fields = "__all__"
#
#     def resolve_source_material_code(self , info) :
#         return self.source_material.symbolic_code if self.source_material else None
#
#     def resolve_analog_material_code(self , info) :
#         return self.analog_material.symbolic_code if self.analog_material else None
#

class MaterialGeneralNode(DjangoObjectType) :
    class Meta :
        model = MaterialGeneral
        fields = "__all__"


class MaterialGeneralMoreDetailedNode(DjangoObjectType) :
    class Meta :
        model = MaterialGeneralMoreDetailed
        fields = "__all__"


class MaterialSpecifiedNode(DjangoObjectType) :
    standard_codes = graphene.List(MaterialCodeNode)
    # analogs = graphene.List(MaterialAnalogNode , analog_type=graphene.String() , min_confidence=graphene.Int())
    primary_code = graphene.String()

    class Meta :
        model = MaterialSpecified
        fields = "__all__"

    def resolve_standard_codes(self , info) :
        return self.standard_codes.all()

    # def resolve_analogs(self , info , analog_type=None , min_confidence=70) :
    #     analogs = self.source_analogs.filter(confidence_level__gte=min_confidence)
    #     if analog_type :
    #         analogs = analogs.filter(analog_type=analog_type)
    #     return analogs

    def resolve_primary_code(self , info) :
        primary_code = self.standard_codes.filter(is_primary=True).first()
        return f"{primary_code.standard.code}:{primary_code.code}" if primary_code else None

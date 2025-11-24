#materials/graphql/queries.py
import graphene

from materials.graphql.types import MaterialStandardNode, MaterialCodeNode, MaterialSpecifiedNode, MaterialGeneralNode, \
    MaterialGeneralMoreDetailedNode

class Query(graphene.ObjectType) :
    # MaterialStandard queries
    all_material_standards = graphene.List(MaterialStandardNode)
    material_standard_by_code = graphene.Field(MaterialStandardNode , code=graphene.String(required=True))

    # MaterialCode queries
    all_material_codes = graphene.List(MaterialCodeNode)
    material_codes_by_standard = graphene.List(MaterialCodeNode , standard_code=graphene.String(required=True))
    material_code_by_value = graphene.Field(MaterialCodeNode , standard_code=graphene.String(required=True) ,
                                            code_value=graphene.String(required=True))

    # MaterialAnalog queries
    # all_material_analogs = graphene.List(MaterialAnalogNode)
    # analogs_for_material = graphene.List(MaterialAnalogNode , material_id=graphene.Int(required=True) ,
    #                                      analog_type=graphene.String() , min_confidence=graphene.Int())
    # exact_analogs = graphene.List(MaterialAnalogNode , material_id=graphene.Int(required=True))

    # MaterialSpecified queries
    all_material_specified = graphene.List(MaterialSpecifiedNode)
    material_specified_by_id = graphene.Field(MaterialSpecifiedNode , id=graphene.Int(required=True))
    material_specified_by_symbolic_code = graphene.Field(MaterialSpecifiedNode ,
                                                         symbolic_code=graphene.String(required=True))
    materials_by_standard_code = graphene.List(MaterialSpecifiedNode , standard_code=graphene.String(required=True) ,
                                               code_value=graphene.String())
    materials_by_general_type = graphene.List(MaterialSpecifiedNode , general_type_id=graphene.Int(required=True))
    materials_by_detailed_type = graphene.List(MaterialSpecifiedNode , detailed_type_id=graphene.Int(required=True))
    search_materials = graphene.List(MaterialSpecifiedNode , search_term=graphene.String(required=True))

    # MaterialGeneral queries
    all_material_general = graphene.List(MaterialGeneralNode)
    material_general_by_id = graphene.Field(MaterialGeneralNode , id=graphene.Int(required=True))

    # MaterialGeneralMoreDetailed queries
    all_material_detailed = graphene.List(MaterialGeneralMoreDetailedNode)
    material_detailed_by_id = graphene.Field(MaterialGeneralMoreDetailedNode , id=graphene.Int(required=True))
    detailed_materials_by_general = graphene.List(MaterialGeneralMoreDetailedNode ,
                                                  general_id=graphene.Int(required=True))

    # SealingMaterial queries
    all_sealing_materials = graphene.List(SealingMaterialNode)
    sealing_material_by_id = graphene.Field(SealingMaterialNode , id=graphene.Int(required=True))
    sealing_materials_by_temp_range = graphene.List(SealingMaterialNode , temp_min=graphene.Int() ,
                                                    temp_max=graphene.Int())

    # MaterialStandard resolvers
    def resolve_all_material_standards(self , info) :
        return MaterialStandard.objects.all()

    def resolve_material_standard_by_code(self , info , code) :
        return MaterialStandard.objects.get(code=code)

    # MaterialCode resolvers
    def resolve_all_material_codes(self , info) :
        return MaterialCode.objects.select_related('standard' , 'material_specified').all()

    def resolve_material_codes_by_standard(self , info , standard_code) :
        return MaterialCode.objects.select_related('standard' , 'material_specified').filter(
            standard__code=standard_code)

    def resolve_material_code_by_value(self , info , standard_code , code_value) :
        return MaterialCode.objects.select_related('standard' , 'material_specified').get(standard__code=standard_code ,
                                                                                          code=code_value)

    # MaterialAnalog resolvers
    def resolve_all_material_analogs(self , info) :
        return MaterialAnalog.objects.select_related('source_material' , 'analog_material').all()

    def resolve_analogs_for_material(self , info , material_id , analog_type=None , min_confidence=70) :
        analogs = MaterialAnalog.objects.select_related('source_material' , 'analog_material').filter(
            source_material_id=material_id , confidence_level__gte=min_confidence
        )
        if analog_type :
            analogs = analogs.filter(analog_type=analog_type)
        return analogs

    def resolve_exact_analogs(self , info , material_id) :
        return MaterialAnalog.objects.select_related('source_material' , 'analog_material').filter(
            source_material_id=material_id , analog_type='exact' , confidence_level__gte=90
        )

    # MaterialSpecified resolvers
    def resolve_all_material_specified(self , info) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').all()

    def resolve_material_specified_by_id(self , info , id) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').get(id=id)

    def resolve_material_specified_by_symbolic_code(self , info , symbolic_code) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').get(symbolic_code=symbolic_code)

    def resolve_materials_by_standard_code(self , info , standard_code , code_value=None) :
        materials = MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').filter(
            standard_codes__standard__code=standard_code
        )
        if code_value :
            materials = materials.filter(standard_codes__code=code_value)
        return materials.distinct()

    def resolve_materials_by_general_type(self , info , general_type_id) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').filter(
            material_general_id=general_type_id
        )

    def resolve_materials_by_detailed_type(self , info , detailed_type_id) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').filter(
            material_detailed_id=detailed_type_id
        )

    def resolve_search_materials(self , info , search_term) :
        return MaterialSpecified.objects.select_related('material_general' , 'material_detailed').prefetch_related(
            'standard_codes').filter(
            Q(symbolic_code__icontains=search_term) |
            Q(text_description__icontains=search_term) |
            Q(full_description__icontains=search_term) |
            Q(standard_codes__code__icontains=search_term) |
            Q(material_general__symbolic_code__icontains=search_term) |
            Q(material_detailed__symbolic_code__icontains=search_term)
        ).distinct()

    # MaterialGeneral resolvers
    def resolve_all_material_general(self , info) :
        return MaterialGeneral.objects.all()

    def resolve_material_general_by_id(self , info , id) :
        return MaterialGeneral.objects.get(id=id)

    # MaterialGeneralMoreDetailed resolvers
    def resolve_all_material_detailed(self , info) :
        return MaterialGeneralMoreDetailed.objects.all()

    def resolve_material_detailed_by_id(self , info , id) :
        return MaterialGeneralMoreDetailed.objects.get(id=id)

    def resolve_detailed_materials_by_general(self , info , general_id) :
        return MaterialGeneralMoreDetailed.objects.filter(material_general_id=general_id)

    # SealingMaterial resolvers
    def resolve_all_sealing_materials(self , info) :
        return SealingMaterial.objects.all()

    def resolve_sealing_material_by_id(self , info , id) :
        return SealingMaterial.objects.get(id=id)

    def resolve_sealing_materials_by_temp_range(self , info , temp_min=None , temp_max=None) :
        queryset = SealingMaterial.objects.all()
        if temp_min is not None :
            queryset = queryset.filter(temp_max__gte=temp_min)
        if temp_max is not None :
            queryset = queryset.filter(temp_min__lte=temp_max)
        return queryset
import graphene
from cable_glands.graphql.types import CableGlandItemNode, CableGlandModelLineNode
from cable_glands.models import CableGlandModelLine, CableGlandItem


# Входные типы для мутаций
class CableGlandModelLineInput(graphene.InputObjectType):
    symbolic_code = graphene.String(required=True)
    brand_id = graphene.ID()
    cable_gland_type_id = graphene.ID()
    ip_ids = graphene.List(graphene.ID)
    exd_ids = graphene.List(graphene.ID)
    for_armored_cable = graphene.Boolean()
    for_metal_sleeve_cable = graphene.Boolean()
    for_pipelines_cable = graphene.Boolean()
    thread_external = graphene.Boolean()
    thread_internal = graphene.Boolean()
    temp_min = graphene.Int()
    temp_max = graphene.Int()
    gost = graphene.String()
    text_description = graphene.String()


class CableGlandItemInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    model_line_id = graphene.ID()
    cable_gland_body_material_id = graphene.ID()
    exd_same_as_model_line = graphene.Boolean(default_value=True)
    exd_ids = graphene.List(graphene.ID)
    thread_a_id = graphene.ID()
    thread_b_id = graphene.ID()
    temp_min = graphene.Int()
    temp_max = graphene.Int()
    cable_diameter_inner_min = graphene.Int()
    cable_diameter_inner_max = graphene.Int()
    cable_diameter_outer_min = graphene.Int()
    cable_diameter_outer_max = graphene.Int()
    dn_metal_sleeve = graphene.Int()
    parent_id = graphene.ID()


# Мутации
class CreateCableGlandModelLine(graphene.Mutation):
    class Arguments:
        input = CableGlandModelLineInput(required=True)

    cable_gland_model_line = graphene.Field(CableGlandModelLineNode)

    @classmethod
    def mutate(cls, root, info, input):
        ip = input.pop('ip_ids', [])
        exd = input.pop('exd_ids', [])

        model_line = CableGlandModelLine.objects.create(**input)

        if ip:
            model_line.ip.set(ip)
        if exd:
            model_line.exd.set(exd)

        return CreateCableGlandModelLine(cable_gland_model_line=model_line)


class UpdateCableGlandModelLine(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CableGlandModelLineInput(required=True)

    cable_gland_model_line = graphene.Field(CableGlandModelLineNode)

    @classmethod
    def mutate(cls, root, info, id, input):
        ip = input.pop('ip_ids', None)
        exd = input.pop('exd_ids', None)

        model_line = CableGlandModelLine.objects.get(pk=id)
        for key, value in input.items():
            setattr(model_line, key, value)
        model_line.save()

        if ip is not None:
            model_line.ip.set(ip)
        if exd is not None:
            model_line.exd.set(exd)

        return UpdateCableGlandModelLine(cable_gland_model_line=model_line)


class DeleteCableGlandModelLine(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        try:
            model_line = CableGlandModelLine.objects.get(pk=id)
            model_line.delete()
            return DeleteCableGlandModelLine(success=True)
        except CableGlandModelLine.DoesNotExist:
            return DeleteCableGlandModelLine(success=False)


class CreateCableGlandItem(graphene.Mutation):
    class Arguments:
        input = CableGlandItemInput(required=True)

    cable_gland_item = graphene.Field(CableGlandItemNode)

    @classmethod
    def mutate(cls, root, info, input):
        exd = input.pop('exd_ids', [])

        item = CableGlandItem.objects.create(**input)

        if exd:
            item.exd.set(exd)

        return CreateCableGlandItem(cable_gland_item=item)


class UpdateCableGlandItem(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CableGlandItemInput(required=True)

    cable_gland_item = graphene.Field(CableGlandItemNode)

    @classmethod
    def mutate(cls, root, info, id, input):
        exd = input.pop('exd_ids', None)

        item = CableGlandItem.objects.get(pk=id)
        for key, value in input.items():
            setattr(item, key, value)
        item.save()

        if exd is not None:
            item.exd.set(exd)

        return UpdateCableGlandItem(cable_gland_item=item)


class DeleteCableGlandItem(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        try:
            item = CableGlandItem.objects.get(pk=id)
            item.delete()
            return DeleteCableGlandItem(success=True)
        except CableGlandItem.DoesNotExist:
            return DeleteCableGlandItem(success=False)


class Mutation(graphene.ObjectType):
    cg_create_cable_gland_model_line = CreateCableGlandModelLine.Field()
    cg_update_cable_gland_model_line = UpdateCableGlandModelLine.Field()
    cg_delete_cable_gland_model_line = DeleteCableGlandModelLine.Field()

    cg_create_cable_gland_item = CreateCableGlandItem.Field()
    cg_update_cable_gland_item = UpdateCableGlandItem.Field()
    cg_delete_cable_gland_item = DeleteCableGlandItem.Field()



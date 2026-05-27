# project/graphql/schema.py
import graphene
import importlib

from graphql import extend_schema

from cable_glands.graphql.schema import cableGlandsSchema
from clients.graphql.schema import clientsSchema
from params.graphql.schema import paramsSchema
from producers.graphql.schema import producersSchema
# from electric_actuators.graphql.schema import eaSchema
from valve_data.graphql.schema import valveDataSchema

# from clients.graphql.schema import clientsSchema

APP_SCHEMAS = [
    'params.graphql.schema.paramsSchema',
    'producers.graphql.schema.producersSchema',
    'valve_data.graphql.schema.valveDataSchema',
    # 'client_requests.graphql.schema.clientRequestsSchema',
    # Добавьте другие приложения
]


class Query(
    # paramsSchema.Query,
    clientsSchema.Query,
    cableGlandsSchema.Query,
    producersSchema.Query,
    paramsSchema.Query,
    # eaSchema.Query,
    valveDataSchema.Query,
    graphene.ObjectType
):
    pass

class Mutation(
    # paramsSchema.Mutation,
    clientsSchema.Mutation,
    cableGlandsSchema.Mutation,
    producersSchema.Mutation,
    # eaSchema.Mutation,
    valveDataSchema.Mutation,
    graphene.ObjectType
):
    pass

# Главная схема
schema = graphene.Schema(query=Query, mutation=Mutation)
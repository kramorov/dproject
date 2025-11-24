# project/graphql/schema.py
import graphene
import importlib

from graphql import extend_schema

from cable_glands.graphql.schema import cableGlandsSchema
from client_requests.graphql.schema import clientRequestsSchema
from clients.graphql.schema import clientsSchema
from params.graphql.schema import paramsSchema
from producers.graphql.schema import producersSchema
from electric_actuators.graphql.schema import eaSchema
from valve_data.graphql.schema import valveDataSchema
from media_library.graphql.schema import mediaLibrarySchema

# from clients.graphql.schema import clientsSchema

APP_SCHEMAS = [
    'params.graphql.schema.paramsSchema',
    'clients.graphql.schema.clientsSchema',
    'producers.graphql.schema.producersSchema',
    'valve_data.graphql.schema.valveDataSchema',
    'media_library.graphql.schema.mediaLibrarySchema',
    # 'client_requests.graphql.schema.clientRequestsSchema',
    # Добавьте другие приложения
]


class Query(
    # paramsSchema.Query,
    clientsSchema.Query,
    clientRequestsSchema.Query,
    cableGlandsSchema.Query,
    producersSchema.Query,
    paramsSchema.Query,
    eaSchema.Query,
    valveDataSchema.Query,
    mediaLibrarySchema.MediaLibraryQuery,
    graphene.ObjectType
):
    pass

class Mutation(
    # paramsSchema.Mutation,
    clientsSchema.Mutation,
    clientRequestsSchema.Mutation,
    cableGlandsSchema.Mutation,
    producersSchema.Mutation,
    eaSchema.Mutation,
    valveDataSchema.Mutation,
    mediaLibrarySchema.MediaLibraryMutations,
    graphene.ObjectType
):
    pass

# Главная схема
schema = graphene.Schema(query=Query, mutation=Mutation)

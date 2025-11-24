import graphene
from .mutations import Mutation
from .queries import Query

cableGlandsSchema = graphene.Schema(query=Query, mutation=Mutation)
import graphene
from .mutations import Mutation
from .queries import Query

producersSchema = graphene.Schema(query=Query, mutation=Mutation)
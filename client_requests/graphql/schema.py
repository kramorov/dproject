import graphene
from .mutations import Mutation
from .queries import Query

clientRequestsSchema = graphene.Schema(query=Query, mutation=Mutation)
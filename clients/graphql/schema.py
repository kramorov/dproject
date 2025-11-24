# params/schema.py
import graphene

from .mutations import Mutation
from .queries import Query

clientsSchema =graphene.Schema(query=Query, mutation=Mutation)
# valve_data/graphql/schema.py
import graphene
from .mutations import Mutation
from .queries import Query

valveDataSchema = graphene.Schema(query=Query, mutation=Mutation)
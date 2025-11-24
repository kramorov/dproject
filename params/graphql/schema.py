# params/schema.py
import graphene
from .mutations import Mutation
from .queries import Query

# Экспорт для сборки
paramsSchema = graphene.Schema(query=Query, mutation=Mutation)


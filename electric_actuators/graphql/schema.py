# electric_actuators/schema.py
import graphene
from .mutations import Mutation
from .queries import Query

# Экспорт для сборки
eaSchema = graphene.Schema(query=Query, mutation=Mutation)


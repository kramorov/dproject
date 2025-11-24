# core/graphql_utils.py
from django.db import models  # Добавьте этот импорт
import graphene
from graphene_django.types import DjangoObjectType

from typing import Union, Dict, Type, List


def generate_model_types(
    models_list: List[Union[Type[models.Model], Type[DjangoObjectType]]],
    exclude_models: List[str] = None
) -> Dict[str, Type[DjangoObjectType]]:
    """
    Генерирует GraphQL типы для моделей Django, поддерживая как модели, так и готовые типы

    Args:
        models_list: Список моделей Django или готовых DjangoObjectType
        exclude_models: Список имен моделей для исключения

    Returns:
        Словарь {type_name: DjangoObjectType}
    """
    model_types = {}
    exclude_models = exclude_models or []

    for item in models_list:
        # Обработка готовых DjangoObjectType
        if isinstance(item, type) and issubclass(item, DjangoObjectType):
            model_types[item.__name__] = item
            exclude_models.extend([item.__name__])
            # print(f'Model add {item.__name__}, item {item}, exclude_models={exclude_models}')
            continue

        # Проверка, что это модель Django
        try:
            if not (isinstance(item, type) and issubclass(item, models.Model)):
                continue
        except TypeError:
            continue

        model = item
        if model.__name__ in exclude_models:
            continue

        type_name = f"{model.__name__}Type"

        if type_name in model_types:
            continue

        # Безопасное получение атрибутов Meta
        model_meta = getattr(model, '_meta', {})
        original_meta = {
            'verbose_name': getattr(model_meta, 'verbose_name', None),
            'verbose_name_plural': getattr(model_meta, 'verbose_name_plural', None),
            # 'db_table': getattr(model_meta, 'db_table', None),
        }

        # Конфигурация для GraphQL
        meta_attrs = {
            'model': model,
            'fields': '__all__',
            'convert_choices_to_enum': False,
            **{k: v for k, v in original_meta.items() if v is not None}
        }

        # Создаем тип с обработкой исключений
        try:
            model_types[type_name] = type(
                type_name,
                (DjangoObjectType,),
                {
                    'Meta': type('Meta', (), meta_attrs),
                    '__doc__': model.__doc__ or f"Auto-generated type for {model.__name__}"
                }
            )
        except Exception as e:
            print(f"Failed to create type for {model.__name__}: {str(e)}")
            continue

    return model_types

def generate_query_class(model_types):
    """Генерирует базовый класс Query с автоматическими полями и резолверами"""

    class BaseQuery(graphene.ObjectType):
        pass

    for type_name, type_class in model_types.items():
        model = type_class._meta.model
        model_name_lower = model.__name__.lower()

        # Поле для списка объектов
        list_field = f"all_{model_name_lower}"
        setattr(BaseQuery, list_field, graphene.List(type_class))

        # Резолвер для списка
        def make_list_resolver(model_cls):
            def resolver(self, info, **kwargs):
                return model_cls.objects.all()

            return resolver

        setattr(BaseQuery, f"resolve_{list_field}", make_list_resolver(model))

        # Поле для одного объекта
        single_field = model_name_lower
        setattr(BaseQuery, single_field, graphene.Field(
            type_class,
            id=graphene.Int(required=True)
        ))

        # Резолвер для одного объекта
        def make_single_resolver(model_cls):
            def resolver(self, info, id):
                return model_cls.objects.get(pk=id)

            return resolver

        setattr(BaseQuery, f"resolve_{single_field}", make_single_resolver(model))

    return BaseQuery


def generate_create_mutations(model_types):
    """Генерирует мутации создания для всех типов моделей"""
    mutations = {}

    for type_name, model_type in model_types.items():
        model = model_type._meta.model

        class Arguments:
            pass

        # Добавляем аргументы для всех полей модели
        for field in model._meta.fields:
            print(f'Model :{model.__name__} field.name={field.name}')
            if field.name != 'id':
                field_type = (
                    graphene.String if field.get_internal_type() in ['CharField', 'TextField']
                    else graphene.Int if field.get_internal_type() in ['IntegerField', 'ForeignKey']
                    else graphene.Boolean if field.get_internal_type() == 'BooleanField'
                    else graphene.String
                )
                setattr(Arguments, field.name, field_type())

        class Mutation(graphene.Mutation):
            success = graphene.Boolean()
            errors = graphene.String()
            item = graphene.Field(model_type)

            @classmethod
            def mutate(cls, root, info, **kwargs):
                try:
                    obj = model(**kwargs)
                    obj.save()
                    return cls(success=True, item=obj, errors=None)
                except Exception as e:
                    return cls(success=False, item=None, errors=str(e))

        mutation_name = f"Create{model.__name__}"
        mutations[mutation_name] = type(
            mutation_name,
            (Mutation,),
            {'Arguments': Arguments}
        )

    return mutations
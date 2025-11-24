# common/eav_managers.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Subquery, OuterRef


class EAVSearchManager(models.Manager):
    """Кастомный менеджер для поиска по EAV атрибутам"""

    def with_eav_attributes(self, **kwargs):
        """
        Фильтрация по EAV атрибутам
        Пример: Model.objects.with_eav_attributes(color='red', weight__gt=100)
        """
        from .models import EAVValue, EAVAttribute

        queryset = self.get_queryset()
        content_type = ContentType.objects.get_for_model(self.model)

        for key, value in kwargs.items():
            # Обрабатываем операции: attribute__operation=value
            if '__' in key:
                attr_name, operation = key.split('__', 1)
            else:
                attr_name, operation = key, 'exact'

            # Получаем атрибут
            try:
                attribute = EAVAttribute.objects.get(name=attr_name)
            except EAVAttribute.DoesNotExist:
                # Если атрибут не существует, возвращаем пустой queryset
                return self.none()

            # Создаем подзапрос для значений EAV
            eav_subquery = EAVValue.objects.filter(
                attribute=attribute,
                entity_content_type=content_type,
                entity_object_id=OuterRef('pk')
            )

            # Преобразуем значение в строку для сравнения
            if operation == 'exact':
                value_str = str(value)
                queryset = queryset.filter(
                    pk__in=Subquery(eav_subquery.filter(value=value_str).values('entity_object_id'))
                )
            elif operation == 'icontains':
                value_str = str(value)
                queryset = queryset.filter(
                    pk__in=Subquery(eav_subquery.filter(value__icontains=value_str).values('entity_object_id'))
                )
            elif operation == 'gt':
                try:
                    value_float = float(value)
                    # Для числовых сравнений нужно преобразовать значения
                    eav_numeric = EAVValue.objects.filter(
                        attribute=attribute,
                        entity_content_type=content_type,
                        entity_object_id=OuterRef('pk'),
                        value__regex=r'^\d*\.?\d+$'  # Только числовые значения
                    ).annotate(
                        numeric_value=models.Cast(models.F('value'), models.FloatField())
                    ).filter(numeric_value__gt=value_float)

                    queryset = queryset.filter(
                        pk__in=Subquery(eav_numeric.values('entity_object_id'))
                    )
                except (ValueError, TypeError):
                    continue
            # Добавьте другие операции по необходимости

        return queryset

    def filter_by_eav(self, attributes_dict):
        """Фильтрация по словарю EAV атрибутов"""
        return self.with_eav_attributes(**attributes_dict)

    def search_eav_text(self, search_text):
        """Поиск по тексту в EAV значениях"""
        from .models import EAVValue, EAVAttribute

        content_type = ContentType.objects.get_for_model(self.model)

        # Ищем объекты, у которых есть EAV значения содержащие текст
        matching_objects = EAVValue.objects.filter(
            entity_content_type=content_type,
            value__icontains=search_text
        ).values_list('entity_object_id', flat=True)

        return self.filter(pk__in=matching_objects)
from rest_framework.fields import empty  # Добавьте этот импорт
from rest_framework import serializers
import json
from django.utils import timezone


class FormDataSerializer(serializers.ModelSerializer):
    """
    Абстрактный сериализатор для динамических форм
    Наследуйте этот класс и добавьте свои поля
    """
    # default_value = serializers.SerializerMethodField()
    class Meta:
        abstract = True
        fields = '__all__'  # Более безопасное значение по умолчанию. Должно быть переопределено в дочерних классах
        depth = 1

    @staticmethod
    def handle_empty(value):
        """Преобразует empty в None и проверяет сериализуемость"""
        if value is empty:
            return None
        try:
            json.dumps({'test': value})  # Проверка сериализуемости
            return value
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def get_structure(cls):
        if getattr(cls.Meta, 'abstract', False):
            raise NotImplementedError("Этот метод должен быть реализован в подклассе")

        if not hasattr(cls.Meta, 'model'):
            raise AttributeError("Meta class must specify 'model'")

        structure = {}
        for field_name, field in cls().get_fields().items():
            field_info = {
                # cls.Meta.model._meta.verbose_name
                'type': cls.handle_empty(field.__class__.__name__),
                'model': getattr(getattr(field, 'Meta', None), 'model', None).__name__ if hasattr(field,
                                                                                                  'Meta') else None,
                'required': cls.handle_empty(getattr(field, 'required', False)),
                'label': cls.handle_empty(getattr(field, 'label', field_name)),
                'verbose_name': getattr(getattr(field, 'Meta', None), 'verbose_name', None) if hasattr(field,
                                                                                                  'Meta') else None,
                # 'verbose_name': cls.handle_empty(getattr(field, 'verbose_name', False)),
                'help_text': cls.handle_empty(getattr(field, 'help_text', '')),
                'choices': [cls.handle_empty(choice) for choice in getattr(field, 'choices', [])],
            }
            if hasattr(field, 'default_value'):
                default = field.default_value
                field_info['default_value'] = cls.handle_empty(default) if callable(default) else default
            # else:
            #     field_info['default_value']= None if field.allow_null else ""

            structure[field_name] = field_info
        return structure

    @classmethod
    def get_full_structure(cls):
        if getattr(cls.Meta, 'abstract', False):
            raise NotImplementedError("Этот метод должен быть реализован в подклассе")

        if not hasattr(cls.Meta, 'model'):
            raise AttributeError("Meta class must specify 'model'")

        structure = {}
        for field_name, field in cls().get_fields().items():
            field_info = {
                'type': cls.handle_empty(field.__class__.__name__),
                'model': getattr(getattr(field, 'Meta', None), 'model', None).__name__ if hasattr(field, 'Meta') else None,
                'required': cls.handle_empty(getattr(field, 'required', False)),
                'label': cls.handle_empty(getattr(field, 'label', field_name)),
                'help_text': cls.handle_empty(getattr(field, 'help_text', '')),
                'choices': [cls.handle_empty(choice) for choice in getattr(field, 'choices', [])],
            }
            # print(field_name, field_info)
            # Обработка вложенных полей
            if hasattr(field, 'child'):
                field_info['child_type'] = field.child.__class__.__name__
                if hasattr(field.child, 'get_structure'):
                    field_info['child_structure'] = field.child.get_structure()
                # print('Child:',field_info)
            elif hasattr(field, 'get_fields'):
                nested_structure = {}
                for nested_name, nested_field in field.get_fields().items():
                    nested_structure[nested_name] = {
                        'type': nested_field.__class__.__name__,
                        'required': getattr(nested_field, 'required', False)
                    }
                field_info['nested_structure'] = nested_structure
                # print('nested_structure:', field_info)


            if hasattr(field, 'default'):
                default = field.default
                field_info['default'] = cls.handle_empty(
                    default() if callable(default) else default
                )
                # print('default:', field_info)

            structure[field_name] = field_info

        return structure
    def get_default_value(self, obj):
        """Производное поле на основе существующего"""
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {k: self.handle_empty(v) for k, v in data.items()}

    @classmethod
    def get_default_values(cls):
        if hasattr(cls.Meta, 'abstract'):
            if cls.Meta.abstract:
                raise NotImplementedError("Этот метод должен быть реализован в подклассе")

        defaults = {}
        for field_name, field in cls().get_fields().items():
            if hasattr(field, 'default'):
                defaults[field_name] = field.default() if callable(field.default) else field.default
            elif not field.required:
                defaults[field_name] = None if field.allow_null else ""
        return defaults

    # Переопределение в конкретном сериализаторе:
    #
    # В списке обычно отображаются не все поля, что в детальном представлении:
    # @classmethod
    # def get_structure(cls):
    #     base_structure = super().get_structure()
    #     # Убираем ненужные для списка поля
    #     base_structure.pop('items', None)
    #     base_structure.pop('detailed_description', None)
    #     return base_structure
# 3. Разные метаданные
# Структура может включать дополнительные параметры для списка:
#     base_structure.update({
#         'pagination': {
#             'page_size': 25,
#             'ordering': ['-created_at']
#         }
#     })
#
# 4. Разные требования к валидации
# Поля, обязательные при создании, могут быть необязательными в списке:
# for field in ['required_field1', 'required_field2']:
#     if field in base_structure:
#         base_structure[field]['required'] = False
# 5. Пример полной реализации
#
#
# class ClientRequestListSerializer(FormDataSerializer):
#     class Meta(FormDataSerializer.Meta):
#         model = ClientRequests
#         fields = ['id', 'symbolic_code', 'status', 'created_at']  # Только для списка
#
#     @classmethod
#     def get_structure(cls):
#         base_structure = super().get_structure()
#
#         # Модификация структуры для списка
#         return {
#             **base_structure,
#             'list_specific': {
#                 'batch_actions': ['export', 'archive'],
#                 'default_sort': '-created_at'
#             }
#         }
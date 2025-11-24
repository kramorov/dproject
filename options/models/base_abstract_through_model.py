# options/models/base_abstract_through_model.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import ValidationError
# from typing import List, Optional
#
# class BaseThroughOption(models.Model):
#     """Базовый абстрактный класс для всех сквозных опций"""
#     encoding = models.CharField(
#         max_length=50,
#         blank=True,
#         verbose_name=_("Кодировка"),
#         help_text=_("Код опции для подстановки в артикул")
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name=_("Описание"),
#         help_text=_("Дополнительное описание этой опции")
#     )
#     sorting_order = models.IntegerField(
#         default=0,
#         verbose_name=_("Порядок сортировки")
#     )
#     is_active = models.BooleanField(
#         default=True,
#         verbose_name=_("Активно")
#     )
#     is_default = models.BooleanField(
#         default=False,
#         verbose_name=_("Стандартная опция"),
#         help_text=_("Является ли эта опция стандартной для серии")
#     )
#
#     class Meta:
#         abstract = True
#         ordering = ['sorting_order']
#
#     # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
#
#     def _get_parent_object(self) -> Optional[models.Model]:
#         """Получить родительский объект"""
#         parent_field = self._get_parent_field_name()
#         return getattr(self, parent_field, None) if parent_field else None
#
#     @classmethod
#     def _get_parent_field_name(cls) -> Optional[str]:
#         """Автоматически определить имя поля родительского объекта"""
#         for field in cls._meta.fields:
#             if isinstance(field, models.ForeignKey) and field.name != 'id':
#                 return field.name
#         return None
#
#     # ==================== СВОЙСТВА ====================
#
#     @property
#     def options_list(self) -> List[models.Model]:
#         """Все доступные опции для родительского объекта"""
#         parent = self._get_parent_object()
#         if not parent:
#             return []
#         parent_field = self._get_parent_field_name()
#         if not parent_field:
#             return []
#         return list(self.__class__.objects.filter(**{parent_field: parent, 'is_active': True}))
#
#     @property
#     def default_option(self) -> Optional[models.Model]:
#         """Стандартная опция для родительского объекта"""
#         parent = self._get_parent_object()
#         if not parent:
#             return None
#         parent_field = self._get_parent_field_name()
#         if not parent_field:
#             return None
#         return self.__class__.objects.filter(**{parent_field: parent, 'is_default': True, 'is_active': True}).first()
#
#     # ==================== ВАЛИДАЦИЯ ====================
#
#     def validate_unique_default(self) -> None:
#         """Валидация уникальности стандартной опции"""
#         if self.is_default:
#             parent = self._get_parent_object()
#             if parent:
#                 parent_field = self._get_parent_field_name()
#                 if parent_field:
#                     existing_default = self.__class__.objects.filter(
#                         **{parent_field: parent, 'is_default': True}
#                     ).exclude(pk=self.pk if self.pk else None)
#                     if existing_default.exists():
#                         raise ValidationError('Может быть только одна стандартная опция')
#
#     def validate_unique_encoding(self) -> None:
#         """Валидация уникальности encoding"""
#         if self.encoding and self.encoding.strip():
#             parent = self._get_parent_object()
#             if parent:
#                 parent_field = self._get_parent_field_name()
#                 if parent_field:
#                     existing_encoding = self.__class__.objects.filter(
#                         **{parent_field: parent, 'encoding': self.encoding}
#                     ).exclude(pk=self.pk if self.pk else None)
#                     if existing_encoding.exists():
#                         raise ValidationError('Опция с такой кодировкой уже существует')
#
#     def clean(self) -> None:
#         """Базовая валидация"""
#         self.validate_unique_default()
#         self.validate_unique_encoding()
#
#     def save(self, *args, **kwargs) -> None:
#         """Сохранение с автоматической валидацией"""
#         self.full_clean()
#         super().save(*args, **kwargs)
#
#     # def __str__(self):
#     #     return self.encoding if self.encoding else f"Option {self.id}"
#     def __str__(self) :
#         return self.encoding or "Option"
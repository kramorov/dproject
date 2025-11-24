# products/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from djangoProject1.common_models.eav_abstract_models import AbstractEAVAttribute , AbstractEAVValue
from djangoProject1.common_models.eav_model_mixin import EAVModelMixin


class ProductEAVAttribute(AbstractEAVAttribute) :
    """Атрибуты EAV для продуктов"""

    class Meta :
        db_table = 'products_eav_attributes'
        verbose_name = _('Атрибут продукта')
        verbose_name_plural = _('Атрибуты продуктов')


class ProductEAVValue(AbstractEAVValue) :
    """Значения EAV для продуктов"""
    attribute = models.ForeignKey(
        ProductEAVAttribute ,
        on_delete=models.CASCADE ,
        related_name='values'
    )

    product = models.ForeignKey(
        'Product' ,
        on_delete=models.CASCADE ,
        related_name='eav_values'
    )

    # Добавляем GenericForeignKey для ссылок на модели
    entity_content_type = models.ForeignKey(
        'contenttypes.ContentType' ,
        on_delete=models.CASCADE ,
        related_name='product_eav_values'
    )
    entity_object_id = models.PositiveIntegerField()
    entity = GenericForeignKey('entity_content_type' , 'entity_object_id')

    class Meta :
        db_table = 'products_eav_values'
        verbose_name = _('Значение атрибута продукта')
        verbose_name_plural = _('Значения атрибутов продуктов')
        unique_together = ['attribute' , 'product']


class Product(models.Model , EAVModelMixin) :
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Указываем какие модели использовать для EAV
    eav_attribute_model = ProductEAVAttribute
    eav_value_model = ProductEAVValue
    eav_entity_field = 'product'  # имя поля связи с основной моделью

    def __str__(self) :
        return self.name

# Пример использования:
# product = Product.objects.get(id=1)
# product.set_eav_value('color', 'red')  # Простое значение
# product.set_eav_value('category', category_obj)  # Ссылка на модель
# color = product.get_eav_value('color')
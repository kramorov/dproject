# sku/models/mixins.py
"""
SKUMixin — абстрактная модель для авто-синхронизации с SKU.

Добавляет поле sku (FK → SKU) и метод sync_sku().
Модель вызывает sync_sku() вручную в своём save():

    class MyModel(SKUMixin, models.Model):
        # sku уже есть из миксина

        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            self.sync_sku()
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType


class SKUMixin(models.Model):
    """
    Абстрактная модель. Добавляет FK на SKU и хуки синхронизации.

    **Подключение:**

        from sku.models import SKUMixin

        class MyModel(SKUMixin, models.Model):
            code = models.CharField(...)
            name = models.CharField(...)
            equipment_type = models.ForeignKey(EquipmentType, ...)
            brand = models.ForeignKey(Producer, ...)

            # sku — уже есть из SKUMixin

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)
                self.sync_sku()

    **Хуки (переопределить при необходимости):**
        - get_sku_code()               → self.code
        - get_sku_name()               → str(self)
        - get_sku_description()        → self.description
        - get_equipment_type_for_sku() → self.equipment_type
        - get_brand_for_sku()          → self.brand
    """

    sku = models.OneToOneField(
        'sku.SKU',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name='SKU',
        help_text='Запись в справочнике номенклатуры',
    )

    class Meta:
        abstract = True

    # ── Хуки ──

    def get_sku_code(self):
        return getattr(self, 'code', None)

    def get_sku_name(self):
        name = getattr(self, 'name', '')
        if not name:
            name = self.get_sku_code() or ''  # fallback: код вместо имени
        return name

    def get_sku_description(self):
        return getattr(self, 'description', '')

    def get_equipment_type_for_sku(self):
        return getattr(self, 'equipment_type', None)

    def get_brand_for_sku(self):
        return getattr(self, 'brand', None)

    # ── Синхронизация ──

    def sync_sku(self):
        """Создать или обновить SKU. Вызвать вручную в save() модели."""
        from .sku import SKU

        code = self.get_sku_code()
        if not code:
            return

        name = self.get_sku_name()

        ct = ContentType.objects.get_for_model(self.__class__)
        desc = self.get_sku_description()
        eq_type = self.get_equipment_type_for_sku()
        brand = self.get_brand_for_sku()

        if self.sku_id:
            sku = self.sku
            changed = False
            if sku.name != name[:300]:
                sku.name = name[:300]
                changed = True
            if sku.description != desc:
                sku.description = desc
                changed = True
            if sku.equipment_type != eq_type:
                sku.equipment_type = eq_type
                changed = True
            if sku.brand != brand:
                sku.brand = brand
                changed = True
            if changed:
                sku.save(update_fields=['name', 'description', 'equipment_type', 'brand'])
        else:
            sku, created = SKU.objects.get_or_create(
                code=code,
                defaults={
                    'name': name[:300],
                    'description': desc,
                    'equipment_type': eq_type,
                    'brand': brand,
                    'source_content_type': ct,
                    'source_object_id': self.pk,
                }
            )
            if created:
                self.__class__.objects.filter(pk=self.pk).update(sku=sku)
            else:
                self.__class__.objects.filter(pk=self.pk).update(sku=sku)

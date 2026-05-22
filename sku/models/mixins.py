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
        """
        Создать или обновить SKU. Вызвать вручную в save() модели.

        Логика:
            1. Если модель уже привязана к SKU (self.sku_id) — обновить поля SKU
               (name, description, equipment_type, brand, source_*) из модели.
            2. Если привязки нет — найти SKU по коду (get_or_create).
               - Если код новый → создать SKU с defaults из модели.
               - Если SKU с таким кодом уже существует (standalone-номенклатура
                 для счетов/КП) → «подхватить» её: обогатить поля SKU данными
                 из модели (name, description, equipment_type, brand, source_*).
            3. Если кода нет — выходит молча.
        """
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
            # Уже привязана — обновляем поля SKU из модели
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
            # source_* — обновляем, только если ещё не заполнены
            if sku.source_content_type_id is None or sku.source_object_id is None:
                sku.source_content_type = ct
                sku.source_object_id = self.pk
                changed = True
            if changed:
                sku.save(update_fields=['name', 'description', 'equipment_type', 'brand',
                                        'source_content_type', 'source_object_id'])
        else:
            # Пытаемся найти или создать SKU по коду
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
            if not created:
                # Нашли существующую SKU (созданную ранее как standalone — для счетов/КП).
                # Обогащаем её полями из модели, которая теперь «подхватила» эту номенклатуру.
                update_fields = {}
                if not sku.name or sku.name == sku.code:
                    sku.name = name[:300]
                    update_fields['name'] = sku.name
                if not sku.description and desc:
                    sku.description = desc
                    update_fields['description'] = sku.description
                if sku.equipment_type_id is None and eq_type is not None:
                    sku.equipment_type = eq_type
                    update_fields['equipment_type'] = sku.equipment_type
                if sku.brand_id is None and brand is not None:
                    sku.brand = brand
                    update_fields['brand'] = sku.brand
                # source_* — заполняем, т.к. standalone-SKU создавалась без привязки к модели
                if sku.source_content_type_id is None:
                    sku.source_content_type = ct
                    update_fields['source_content_type'] = sku.source_content_type
                if sku.source_object_id is None:
                    sku.source_object_id = self.pk
                    update_fields['source_object_id'] = sku.source_object_id
                if update_fields:
                    sku.save(update_fields=list(update_fields.keys()))
            # Привязываем модель к SKU
            self.__class__.objects.filter(pk=self.pk).update(sku=sku)
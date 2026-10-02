# core/models/config_hash.py
"""ConfigHashMixin — семантическая идентичность карточки каталога.

``config_hash`` — SHA-256 от канонического кортежа стабильных id конфигурации
(типоразмер + опции). Код-независимая идентичность: смена кодировки/артикула
не меняет хэш, смена опции — меняет. Для карточек без опций
(``config_hash_fields`` пуст) хэш остаётся ``null`` — идентичность тогда сам code.

Правило fork (CATALOG_PATTERN.md):
  - хэш тот же, код другой → та же SKU (переименование);
  - хэш другой → новый продукт → новая SKU.
"""
import hashlib
import json
from typing import Optional

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class ConfigHashMixin(models.Model):
    """Добавляет ``config_hash`` и его вычисление из набора FK-опций модели."""

    config_hash = models.CharField(
        max_length=64, unique=True, blank=True, null=True,
        verbose_name=_("Хэш конфигурации"),
        help_text=_("SHA-256 от типоразмера + опций; ключ дедупа и диффа"),
    )

    # Имена FK-полей, чьи id хэшируются (порядок важен). Модель переопределяет.
    config_hash_fields: tuple = ()

    class Meta:
        abstract = True

    def compute_config_hash(self) -> Optional[str]:
        """SHA-256 от канонического кортежа стабильных id конфигурации.

        В каноническую строку входит ``app_label.model`` (неймспейс модели),
        чтобы хэши разных моделей гарантированно не пересекались. Хэшируются
        только стабильные значения опций, НЕ encoding и не ``code``: смена
        кодировки не меняет хэш. Отсутствующая опция — ``0``.
        """
        if not self.config_hash_fields:
            return None
        parts = [self._hash_part(field_name) for field_name in self.config_hash_fields]
        canonical = f"{self._meta.label_lower}|{'|'.join(parts)}"
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def _hash_part(self, field_name: str) -> str:
        """Каноническое значение одного поля конфигурации.

        FK → id; M2M → отсортированные id; скаляр → значение;
        list/dict (JSON-список, напр. signals/sensors) → каноничный JSON.
        """
        try:
            field = self._meta.get_field(field_name)
        except FieldDoesNotExist:
            field = None

        if field is not None and field.many_to_many:
            try:
                ids = sorted(getattr(self, field_name).values_list('pk', flat=True))
            except Exception:
                ids = []
            return json.dumps(ids, default=str, sort_keys=True)

        if field is not None and field.is_relation:
            val = getattr(self, field_name + '_id', None)
            return str(val if val is not None else 0)

        val = getattr(self, field_name, None)
        if val is None:
            return ''
        if isinstance(val, (list, dict, tuple)):
            return json.dumps(val, default=str, sort_keys=True)
        return str(val)

    def _check_config_hash_unique(self):
        """Блок при коллизии config_hash (одна карточка = одна конфигурация)."""
        h = self.config_hash or self.compute_config_hash()
        if not h:
            return
        qs = type(self).objects.filter(config_hash=h)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                f'Карточка с такой конфигурацией уже существует (config_hash: {h})'
            )


def config_hash_m2m_receiver(sender, instance, action, **kwargs):
    """Пересчитать config_hash после изменения M2M-опций (exd и т.п.).

    M2M пишется после model.save() (form.save_m2m / .set()), поэтому в save()
    хэш не видит итоговые M2M-значения. Приёмник ловит post_add/post_remove/
    post_clear и обновляет только config_hash (без полного save() и без sync_sku).
    """
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    if not isinstance(instance, ConfigHashMixin):
        return
    if not getattr(instance, 'config_hash_fields', None) or not instance.pk:
        return
    try:
        new_hash = instance.compute_config_hash()
    except Exception:
        return
    if new_hash != instance.config_hash:
        type(instance).objects.filter(pk=instance.pk).update(config_hash=new_hash)

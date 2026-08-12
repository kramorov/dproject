"""
ParameterCatalog — глобальный реестр канонических параметров.

Назначение:
    Один и тот же смысловой параметр ('минимальная температура') в разных
    моделях оборудования называется по-разному ('work_temp_min', 'temperature_min',
    'temp_min'). ParameterCatalog задаёт канонический ключ (code), человекочитаемое
    имя (name), группу (namespace) и описание — чтобы на фронте можно было выбрать
    параметр из выпадающего списка, а при необходимости добавить новый.

    Связь с ModelFieldSnapshot:
        ModelFieldSnapshot.param_name → FK на ParameterCatalog.
        Снапшот хранит реальный field_path из Django-модели, а каталог —
        канонический code для AI/UI.

    При переносе в ETP (sync_to_etp) code из каталога становится
    EquipmentTypeParameter.param_name.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ParameterCatalog(models.Model):
    """Глобальная запись канонического параметра."""

    code = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        verbose_name=_("Код"),
        help_text=_("Канонический ключ: 'temp_min', 'ip_id', 'torque_nm'. "
                    "Это же значение попадает в EquipmentTypeParameter.param_name."),
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_("Название"),
        help_text=_("Человекочитаемое имя: 'Минимальная температура'"),
    )
    namespace = models.CharField(
        max_length=64,
        blank=True, null=True, db_index=True,
        verbose_name=_("Namespace"),
        help_text=_("Группировка: 'temperature', 'connection', 'protection', 'ip' — "
                    "для выпадающего списка на фронте"),
    )
    description = models.TextField(
        blank=True, null=True,
        verbose_name=_("Описание"),
        help_text=_("Чтобы не забыть, к чему это: 'Нижний предел рабочей температуры изделия'"),
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Каталог параметров")
        verbose_name_plural = _("Каталог параметров")
        ordering = ["namespace", "code"]
        indexes = [
            models.Index(fields=["namespace", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

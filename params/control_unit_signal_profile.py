# params/control_unit_signal_profile.py
"""
Профили сигналов для конфигурации блока управления.

ControlUnitSignalProfile — типовой набор сигналов:
  «Стандартные механические SPDT», «Интеллектуальный (полный)» и т.д.

ControlUnitSignalProfileEntry — запись внутри профиля:
  роль_сигнала → конкретный датчик из pa_controls.SensorComponent.

Один датчик (например, DPDT-переключатель) может обслуживать несколько ролей
(«Конечный Открыто» и «Конечный Закрыто») в пределах одного профиля.
unique_together = [profile, signal_role] гарантирует, что на одну роль
нельзя назначить два разных датчика.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import OptionListToSelectMixin


class ControlUnitSignalProfile(OptionListToSelectMixin, models.Model):
    """Типовой профиль сигналов для конфигурации БУ.

    Группирует датчики в осмысленные наборы:
    «Стандартные механические SPDT», «Интеллектуальный (полный)», и т.д.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название профиля, например «Стандартные механические SPDT»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код профиля, например «MECH-SPDT-STD»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Состав профиля и примечания")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Порядок в списке профилей сигналов")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли этот профиль в списках выбора")
    )

    class Meta:
        verbose_name = _("Профиль сигналов БУ")
        verbose_name_plural = _("Профили сигналов БУ")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    def get_summary(self) -> str:
        """Сводка для каталога: роли и датчики через запятую."""
        items = [
            f"{entry.signal_role}: {entry.sensor}"
            for entry in self.entries.select_related('signal_role', 'sensor').all()
        ]
        return "; ".join(items) if items else "—"


class ControlUnitSignalProfileEntry(models.Model):
    """Запись в профиле: роль сигнала → конкретный датчик.

    Через эту модель один датчик может быть назначен на несколько ролей
    (например, DPDT-переключатель обслуживает и «Конечный Открыто»,
    и «Конечный Закрыто»).
    """
    profile = models.ForeignKey(
        ControlUnitSignalProfile,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=_("Профиль сигналов")
    )
    signal_role = models.ForeignKey(
        'params.SignalRole',
        on_delete=models.PROTECT,
        verbose_name=_("Роль сигнала"),
        help_text=_("Назначение сигнала: «Конечный Открыто», «Авария» и т.д.")
    )
    sensor = models.ForeignKey(
        'pa_controls.SensorComponent',
        on_delete=models.PROTECT,
        verbose_name=_("Датчик"),
        help_text=_("Конкретный датчик из базы pa_controls")
    )
    is_default_calibration = models.BooleanField(
        default=True,
        verbose_name=_("Стандартная калибровка"),
        help_text=_("Используется ли заводская калибровка для этого датчика")
    )

    class Meta:
        verbose_name = _("Запись профиля сигналов")
        verbose_name_plural = _("Записи профиля сигналов")
        unique_together = ['profile', 'signal_role']
        ordering = ['profile', 'signal_role__sorting_order']

    def __str__(self):
        return f"{self.signal_role} → {self.sensor}"

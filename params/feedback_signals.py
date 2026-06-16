# params/feedback_signals.py
"""
Типовые наборы сигналов обратной связи.

FeedbackSignalSet — справочник из 5–7 записей, группирующий существующие
SensorComponent из pa_controls. Каждый SensorComponent уже содержит:
- signal_type (сухой контакт / NAMUR / 4–20 мА / ...)
- contact_form (SPST / SPDT / DPDT / DPST)
- contact_state (NO / NC / CO)
- electrical_specs, wires_count, искробезопасные параметры

Использование:
- ElectricControlUnitOption.feedback_signal_set → FK
- Конструктор: выбрал БУ+напряжение → набор сигналов определён
- Каталог: get_summary() → «Концевые (2), Моментные (2), 4–20 мА, Авария»
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import OptionListToSelectMixin


class FeedbackSignalSet(OptionListToSelectMixin, models.Model):
    """Типовой набор сигналов обратной связи.

    Группирует существующие SensorComponent из pa_controls в осмысленные
    наборы: «Стандартные механические SPDT», «Интеллектуальный (полный)» и т.д.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название набора сигналов, например «Стандартные механические SPDT»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код набора, например «MECH-SPDT-STD»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Состав набора и примечания")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Порядок в списке наборов сигналов")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли этот набор в списках выбора")
    )

    # ── M2M на существующие SensorComponent из pa_controls ──
    sensors = models.ManyToManyField(
        'pa_controls.SensorComponent',
        blank=True,
        verbose_name=_("Датчики в наборе"),
        help_text=_(
            "Конкретные датчики из базы pa_controls. "
            "Каждый уже содержит тип сигнала, форму и состояние контакта."
        )
    )

    class Meta:
        verbose_name = _("Набор сигналов обратной связи")
        verbose_name_plural = _("Наборы сигналов обратной связи")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    def get_summary(self) -> str:
        """Сводка для каталога: имена датчиков через запятую."""
        names = [s.name for s in self.sensors.all()]
        return ", ".join(names) if names else "—"

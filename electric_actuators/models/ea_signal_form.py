# electric_actuators/models/ea_signal_form.py
"""
Справочник электрических форм сигналов электроприводов.

``EaSignalForm`` — справочник (расширяемый данными, без миграций) электрических
форм, в которых сигнал существует на клеммах:

    DRY_SPST / DRY_SPDT / DRY_DPDT     — сухие контакты (механические переключатели);
    AN_4_20_ACTIVE / AN_4_20_PASSIVE   — токовая петля 4–20 мА (питание от БУ / от петли);
    DISC_AC / DISC_DC                  — дискретные командные цепи (номинал — в поле
                                         voltage сигнала, а не в форме);
    RES_POTENTIOMETER                  — омическая ОС (голый потенциометр).

Категория (``category``) используется для группировки в UI и для валидации
совместимости «категория сигнала × форма» (см. ``EaControlSignal.clean`` /
``EaFeedbackSignal.clean``).

Локализация: ``name``/``description`` — русские базовые поля, переводы — в
``name_i18n``/``description_i18n`` (миксин ``LocalizedDictFieldsMixin``);
коды и аббревиатуры не переводятся.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import (CopyMixin, LocalizedDictFieldsMixin,
                                 OptionListToSelectMixin)


class EaSignalFormCategory(models.TextChoices):
    """Категория электрической формы сигнала."""
    CONTACT = 'contact', _('Сухой контакт')
    ANALOG = 'analog', _('Аналоговый (токовая петля)')
    DISCRETE = 'discrete', _('Дискретная команда (напряжение)')
    RESISTANCE = 'resistance', _('Сопротивление (потенциометр)')


class EaSignalForm(CopyMixin, LocalizedDictFieldsMixin, OptionListToSelectMixin):
    """Электрическая форма сигнала ЭП.

    Одна запись = одна форма на клеммах. Расширяется данными (NAMUR, PNP,
    0–10 В и т.п. добавляются записями, а не миграцией).
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код формы, например «DRY_SPDT», «AN_4_20_PASSIVE»")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название формы, например «Сухой контакт SPDT»")
    )
    category = models.CharField(
        max_length=20, choices=EaSignalFormCategory.choices,
        verbose_name=_("Категория"),
        help_text=_("Категория формы: контакт / аналог / дискретная команда / сопротивление")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Пояснение формы: схема подключения, полярность, особенности")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Порядок в списках выбора")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать в списках выбора")
    )

    class Meta:
        verbose_name = _("Форма сигнала ЭП")
        verbose_name_plural = _("Формы сигналов ЭП")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name

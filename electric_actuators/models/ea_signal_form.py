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


# Единый набор категорий форм (ЭП + БУ).
SIGNAL_FORM_CATEGORIES = (
    ('contact', 'Сухой контакт'),
    ('analog', 'Аналоговый (токовая петля)'),
    ('discrete', 'Дискретная команда (напряжение)'),
    ('resistance', 'Сопротивление (потенциометр)'),
    ('dry_input', 'Сухой контакт (внутренний опрос БУ)'),
    ('voltage_ac', 'Потенциал AC'),
    ('voltage_dc', 'Потенциал DC'),
    ('current_4_20', 'Токовая петля 4–20 мА'),
    ('dry_output', 'Сухой контакт (выход реле)'),
)


class EaSignalFormCategory(CopyMixin, LocalizedDictFieldsMixin,
                           OptionListToSelectMixin):
    """Категория электрической формы сигнала.

    Раньше была ``models.TextChoices`` — заменена на справочную модель.
    Общая для ЭП и БУ: объединяет EaSignalFormCategory (contact/analog/
    discrete/resistance) и CuControlSignalFormCategory/CuFeedbackSignalFormCategory
    (dry_input/voltage_ac/voltage_dc/current_4_20/dry_output).
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Категория формы сигнала")
        verbose_name_plural = _("Категории форм сигналов")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


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
    category = models.ForeignKey(
        EaSignalFormCategory, on_delete=models.PROTECT,
        related_name='signal_forms',
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

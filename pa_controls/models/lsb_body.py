from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import StructuredDataMixin
from electric_actuators.models import CableGlandHolesSet


class LimitSwitchBody(StructuredDataMixin, models.Model):
    """
    Корпус БКВ
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии корпусов БКВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии корпусов БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                 null=True, help_text=_('Вес'),
                                 verbose_name=_("Вес, кг"))
    cable_glands_holes = \
        models.ManyToManyField(CableGlandHolesSet, blank=True,
                               related_name='limit_switch_body_cable_glands_holes',
                               verbose_name=_("Отверстия КВ"),
                               help_text=_('Отверстия под кабельные вводы'))
    # Присоединительные размеры (Many-to-Many с монтажными стандартами)
    mounting = models.ManyToManyField(
        'pa_controls.PaControlMountingStandard',
        blank=True,
        related_name='limit_switch_body_mounting',
        verbose_name=_("Стандарты присоединения"),
        help_text=_("Стандарты присоединения NAMUR, с которыми совместим БКВ")
    )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Корпус БКВ')
        verbose_name_plural = _('Корпуса БКВ')

    def __str__(self):
        return self.name

    @property
    def cable_glands_holes_list_text(self) -> str:
        """
        Возвращает текстовый список отверстий под кабельные вводы.
        Разделитель - слово "или"
        """
        cable_glands = self.cable_glands_holes.all()
        if not cable_glands:
            return ""

        names = [item.name for item in cable_glands]

        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} или {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" или {names[-1]}"

    @property
    def mounting_list_text(self) -> str:
        """
        Возвращает текстовый список стандартов присоединения.
        Разделитель - слово "или"
        """
        mounting_standards = self.mounting.all()
        if not mounting_standards:
            return ""

        names = [item.name for item in mounting_standards]

        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} или {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" или {names[-1]}"

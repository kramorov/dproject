# client_requests/models/request_item_type.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class RequestItemType(models.Model) :
    """
    Тип подбора для позиции запроса
    """
    symbolic_code = models.CharField(
        max_length=50 ,
        unique=True ,
        verbose_name=_("Символьный код") ,
        help_text=_("Код типа подбора (valve_only, actuator_only, full_set)")
    )
    name = models.CharField(
        max_length=200 ,
        verbose_name=_("Название") ,
        help_text=_("Название типа подбора для отображения")
    )
    description = models.TextField(
        blank=True ,
        verbose_name=_("Описание")
    )

    # Флаги, что нужно подбирать для этого типа
    need_valve_selection = models.BooleanField(
        default=False ,
        verbose_name=_("Подбор арматуры")
    )
    need_pneumatic_actuator_selection = models.BooleanField(
        default=False ,
        verbose_name=_("Подбор пневмопривода")
    )
    need_electric_actuator_selection = models.BooleanField(
        default=False ,
        verbose_name=_("Подбор электропривода")
    )
    need_mounting_kit = models.BooleanField(
        default=False ,
        verbose_name=_("Монтажный комплект")
    )
    need_fittings = models.BooleanField(
        default=False ,
        verbose_name=_("Фитинги")
    )
    need_positioner = models.BooleanField(
        default=False ,
        verbose_name=_("Позиционер/распределитель")
    )
    need_air_preparation = models.BooleanField(
        default=False ,
        verbose_name=_("Пневмоподготовка")
    )

    # Порядок сортировки
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta :
        verbose_name = _("Тип подбора позиции")
        verbose_name_plural = _("Типы подбора позиций")
        ordering = ['sort_order' , 'symbolic_code']

    def __str__(self) :
        return self.name

    @classmethod
    def get_choices(cls) :
        """
        Получить список активных типов подбора для выпадающего списка
        """
        return cls.objects.filter(is_active=True).order_by('sort_order' , 'symbolic_code')
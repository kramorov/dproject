# gearbox/models/gb_body.py
from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin , TemplateMixin
from gearbox.models.gb_model_line import GearBoxModelLine
from gearbox.models.gb_options import OverrideMechanism , TransmissionVariety
from params.models import StemSize , StemShapes , MountingPlateTypes


class GearBoxBody(CopyMixin , TemplateMixin , models.Model) :
    """Модель корпуса редуктора с основными механическими свойствами"""
    name = models.CharField(max_length=50 , blank=True ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название модели редуктора'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели редуктора'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    transmission_variety = models.ForeignKey(TransmissionVariety , on_delete=models.SET_NULL , null=True , blank=True ,
                                             related_name='transmission_variety' ,
                                             verbose_name=_("Тип передачи") ,
                                             help_text=_('Тип передачи (трансмисии)'))
    reduction_ratio = models.DecimalField(
        max_digits=7 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Передат.число (i)") ,
        help_text=_("Передаточное число (i) - изменение скорости")
    )
    reduction_ratio_text = models.CharField(max_length=20 , blank=True , null=True ,
                                            verbose_name=_("Передаточное число (текст)") ,
                                            help_text=_('Передаточное число (текст - Например, "40:1")'))
    reduction_ratio_verified = models.DecimalField(
        max_digits=7 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Передат.число проверенное") ,
        help_text=_("Передаточное число (i) проверенное - изменение скорости")
    )

    # Коэффициент усиления (Mechanical Advantage)
    # На сколько реально умножается входной момент
    amplification_factor = models.DecimalField(
        max_digits=7 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("К усиления") ,
        help_text=_("Коэффициент усиления момента (MA)")
    )
    amplification_factor_verified = models.DecimalField(
        max_digits=7 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("К усиления проверенное") ,
        help_text=_("Коэффициент усиления момента (MA)проверенное")
    )
    # КПД / Коэффициент потерь (Efficiency)
    # Значение от 0.00 до 1.00
    efficiency = models.DecimalField(
        max_digits=4 , decimal_places=3 , blank=True , null=True ,
        default=0.400 ,
        verbose_name=_("КПД (η)") ,
        help_text=_("КПД (η) Учитывает потери на трение в передаче")
    )

    # Максимальные моменты
    max_input_torque = models.DecimalField(
        max_digits=10 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Макс. входной момент (Нм)") ,
        help_text=_("Момент, который можно приложить к штурвалу")
    )
    max_output_torque = models.DecimalField(
        max_digits=10 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Макс. выходной момент (Нм)") ,
        help_text=_("Критический момент, который выдержит редуктор")
    )
    handwheel_force_nominal = models.DecimalField(
        max_digits=7 , decimal_places=2 ,
        null=True , blank=True ,
        verbose_name=_("Усилие на штурвале (Н)") ,
        help_text=_("Усилие на ободе штурвала при достижении макс. выходного момента")
    )
    handwheel_diameter = models.PositiveIntegerField(verbose_name=_("Диаметр штурвала (мм)") , blank=True , null=True ,
                                                     help_text=_('Монтажная площадка'))

    # Поля присоединения (ISO 5211 / ISO 5210)
    # Для дублеров важно посадочное место как под привод, так и под арматуру
    mounting_plate_top = models.ManyToManyField(MountingPlateTypes , blank=True ,
                                                related_name='mounting_plate_top' ,
                                                verbose_name=_("Монт.площадка к приводу") ,
                                                help_text=_('Монтажная площадка к приводу'))
    stem_shape_top = models.ForeignKey(StemShapes , on_delete=models.SET_NULL , null=True , blank=True ,
                                       related_name='stem_shape_top' ,
                                       verbose_name=_("Тип штока к приводу") ,
                                       help_text=_('Тип отверстия к приводу'))
    stem_size_top = models.ForeignKey(StemSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                      related_name='stem_size_top' ,
                                      verbose_name=_("Размер штока к приводу") ,
                                      help_text=_('Размер отверстия к приводу'))
    stem_height_top = models.DecimalField(
        max_digits=5 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Высота штока") ,
        help_text=_('Высота штока к приводу'))

    mounting_plate_bottom = models.ManyToManyField(MountingPlateTypes , blank=True ,
                                                   related_name='mounting_plate_bottom' ,
                                                   verbose_name=_("Монт.площадка к арматуре") ,
                                                   help_text=_('Монтажная площадка к арматуре'))
    stem_shape_bottom = models.ForeignKey(StemShapes , on_delete=models.SET_NULL , null=True , blank=True ,
                                          related_name='stem_shape_bottom' ,
                                          verbose_name=_("Тип штока к арматуре") ,
                                          help_text=_('Тип штока к арматуре'))
    stem_size_bottom = models.ForeignKey(StemSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                         related_name='stem_size_bottom' ,
                                         verbose_name=_("Размер штока") ,
                                         help_text=_('Размер отверстия к арматуре'))
    stem_height_bottom = models.DecimalField(
        max_digits=5 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Глубина под шток") ,
        help_text=_('Глубина отверстия под шток арматуры'))
    max_stem_diameter_bottom = models.DecimalField(
        max_digits=5 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Макс шток") ,
        help_text=_('Максимальный диаметр отверстия '
                    'под шток арматуры'))

    # Специфические поля (можно оставлять пустыми в зависимости от типа)
    mechanical_advantage = models.DecimalField(
        max_digits=5 , decimal_places=2 , null=True , blank=True ,
        verbose_name="Механическое преимущество"
    )
    weight = models.DecimalField(max_digits=5 , decimal_places=2 , blank=True ,
                                 null=True , help_text=_('Вес') ,
                                 verbose_name=_("Вес, кг"))

    class Meta :
        verbose_name = _("Корпус редуктора")
        verbose_name_plural = _("Корпуса редукторов")
        ordering = ['sorting_order']
    def __str__(self):
        return f"{self.name}"

    @property
    def mounting_plate_bottom_list_text(self) -> str :
        """
        Возвращает текстовый список стандартов присоединения.
        Разделитель - слово "или"
        """
        return self._get_mounting_plate_list_text(top_or_bottom='BOTTOM')

    @property
    def mounting_plate_top_list_text(self) -> str :
        """
        Возвращает текстовый список стандартов присоединения.
        Разделитель - слово "или"
        """
        return self._get_mounting_plate_list_text(top_or_bottom='TOP')

    def _get_mounting_plate_list_text(self, top_or_bottom='TOP') -> str :
        """
        Возвращает текстовый список стандартов присоединения.
        Разделитель - слово "или"
        """
        mounting_standards = self.mounting_plate_top.all() if top_or_bottom == 'TOP' else self.mounting_plate_bottom.all()

        if not mounting_standards :
            return ""

        names = [item.name for item in mounting_standards]

        if len(names) == 1 :
            return names[0]
        elif len(names) == 2 :
            return f"{names[0]} или {names[1]}"
        else :
            return ", ".join(names[:-1]) + f" или {names[-1]}"
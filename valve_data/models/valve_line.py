from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_models import (
    AllowedDnTemplate, ValveConnectionToPipe, ValveVariety, ConstructionVariety,
    PortQty, ValveModelDataTable, ValveModelKvDataTable, ValveLineBodyColor, BodyColor
)
from producers.models import Producer, Brands
from materials.models import MaterialGeneral, MaterialSpecified
from params.models import (
    ValveFunctionVariety, SealingClass, WarrantyTimePeriodVariety,
    ValveActuationVariety, OptionVariety
)
# from .dimension_models import ValveDimensionTable

from .mixins import (
    # ValveLineInheritanceMixin,
    ValveLineDataGettersMixin,
    ValveLineModelDataMixin,
    ValveLineKvDataMixin,
    ValveLineServiceMixin,
    ValveLineUtilsMixin
)
from .properties import ValveLinePropertiesMixin


class ValveLine(
    ValveLineModelDataMixin,
    ValveLineKvDataMixin,
    ValveLineServiceMixin, # Включает ValveLineInheritanceMixin, и ValveLineDataGettersMixin,
    ValveLineUtilsMixin,
    ValveLinePropertiesMixin,
    models.Model
):
    """Основная модель серии арматуры
    в списке
    allowed_dn_table хранятся допустимые для этой модели Dn. В остальных таблицах могут быть таблицы для
        других моделей серии.
    valve_model_data_table это ссылка на таблицу Dn-Pn-монтажная площадка - для быстрой заливки в БД
        сокращенных данных. Там хранятся данные для всех Dn
    valve_model_dimension_data_table - здесь данные по размерам и весу, монтажным площадкам.
        Данные хранятся для всех Dn,Pn. Также есть изображения (чертежи), в которых также указывается
        для каких Dn
    """

    name = models.CharField(max_length=100, blank=True, null=True,
                            help_text=_("Символьное обозначение (артикул) серии арматуры"),
                            verbose_name=_("Серия"))
    code = models.CharField(max_length=50, blank=True, null=True,
                            help_text=_("Код серии арматуры"),
                            verbose_name=_("Код"))
    original_valve_line = models.ForeignKey(
        'self',
        related_name='derived_valve_lines',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Исходная серия"),
        help_text=_("Серия арматуры, от которой наследуются данные")
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    features_text = models.TextField(blank=True, verbose_name=_("Особенности"))
    application_text = models.TextField(blank=True, verbose_name=_("Где применяется"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    is_approved = models.BooleanField(default=False, verbose_name=_("Проверено"))

    valve_producer = models.ForeignKey(Producer, related_name='valve_line_valve_producer', blank=True, null=True,
                                       on_delete=models.SET_NULL,
                                       help_text=_('Производитель семейства серий арматуры'),
                                       verbose_name=_("Производитель"))
    valve_brand = models.ForeignKey(Brands, related_name='valve_line_valve_brand', blank=True, null=True,
                                    on_delete=models.SET_NULL,
                                    help_text=_('Бренд семейства серий арматуры'),
                                    verbose_name=_("Бренд"))
    valve_variety = models.ForeignKey(ValveVariety, related_name='valve_line_valve_variety', blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Тип арматуры семейства арматуры производителя'),
                                      verbose_name=_("Тип"))
    valve_function = models.ForeignKey(ValveFunctionVariety, related_name='valve_line_valve_function', blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       help_text=_('Тип арматуры - регулирующая, запорная'),
                                       verbose_name=_("Регулирующая/запорная"))
    valve_actuation = models.ForeignKey(
        ValveActuationVariety, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='valve_line_valve_actuation_variety',
        verbose_name=_('Управление'),
        help_text=_("Тип механизма приведения в действие арматуры")
    )
    valve_sealing_class = models.ForeignKey(SealingClass, related_name='valve_line_sealing_class', blank=True,
                                            null=True,
                                            on_delete=models.SET_NULL,
                                            help_text=_('Класс герметичности арматуры'),
                                            verbose_name=_("Класс герметичности"))
    body_material = models.ForeignKey(MaterialGeneral, related_name='valve_line_body_material', blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Тип материала корпуса'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified, related_name='valve_line_body_material',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))
    shut_element_material = models.ForeignKey(MaterialGeneral, related_name='valve_line_shut_element_material',
                                              blank=True, null=True,
                                              on_delete=models.SET_NULL,
                                              help_text=_(
                                                  'Тип материала запорного элемента (диска, шара, ножа, клина)'),
                                              verbose_name=_('Тип материала запорного элемента'))
    shut_element_material_specified = models.ForeignKey(MaterialSpecified,
                                                        related_name='valve_line_shut_element_material_specified',
                                                        blank=True,
                                                        null=True,
                                                        on_delete=models.SET_NULL,
                                                        help_text=_(
                                                            'Марка материала запорного элемента (диска, шара, ножа, клина)'),
                                                        verbose_name=_('Материал запорного элемента'))
    sealing_element_material = models.ForeignKey(
        MaterialGeneral, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='valve_line_sealing_material_general',
        help_text=_('Тип материала уплотнения'),
        verbose_name=_("Тип материала уплотнения")
    )
    sealing_element_material_specified = models.ForeignKey(
        MaterialSpecified, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='valve_line_sealing_material_specified',
        verbose_name=_("Материал уплотнения")
    )

    item_code_template = models.CharField(max_length=100, blank=True, null=True,
                                          help_text=_("Шаблон кодировки для артикула"),
                                          verbose_name=_("Шаблон для артикула"))
    option_variety = models.ForeignKey(
        OptionVariety, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='valve_line_option_variety',
        verbose_name=_("Стандарт или опция")
    )
    work_temp_min = models.IntegerField(
        null=True, blank=True,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб макс, °С')
    )
    temp_min = models.IntegerField(
        null=True, blank=True,
        help_text=_('Минимальная температура, °С'),
        verbose_name=_("Т мин, °С")
    )
    temp_max = models.IntegerField(
        null=True, blank=True,
        help_text=_('Максимальная температура, °С'),
        verbose_name=_("Т макс, °С")
    )

    port_qty = models.ForeignKey(PortQty, related_name='valve_line_port_qty', blank=True, null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Количество портов'),
                                 verbose_name=_("Портов"))
    construction_variety = models.ForeignKey(ConstructionVariety, related_name='valve_line_port_qty', blank=True,
                                             null=True,
                                             on_delete=models.SET_NULL,
                                             help_text=_('Тип конструкции'),
                                             verbose_name=_("Конструкция"))
    allowed_dn_table = models.ForeignKey(
        AllowedDnTemplate,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='valve_line_allowed_dn_table',
        verbose_name=_("Допустимые Dn"),
        help_text=_("Допустимые Dn для этой серии")
    )

    valve_model_data_table = models.ForeignKey(ValveModelDataTable,
                                               related_name='valve_line_valve_model_data_table',
                                               blank=True,
                                               null=True,
                                               on_delete=models.SET_NULL,
                                               verbose_name=_('Шаблон таблицы данных'),
                                               help_text=_('Шаблон таблицы данных моделей арматуры для этой серии'))
    valve_model_kv_data_table = models.ForeignKey(ValveModelKvDataTable,
                                                  related_name='valve_line_valve_model_kv_data_table',
                                                  blank=True,
                                                  null=True,
                                                  on_delete=models.SET_NULL,
                                                  verbose_name=_('Шаблон таблицы данных Kvs'),
                                                  help_text=_(
                                                      'Шаблон таблицы данных Kvs моделей арматуры для этой серии'))

    body_colors = models.ManyToManyField(
        BodyColor,
        through='ValveLineBodyColor',
        through_fields=('valve_line', 'body_color'),
        related_name='valve_line_body_color',
        verbose_name=_("Цвета корпуса"),
        blank=True
    )

    pipe_connection = models.ForeignKey(ValveConnectionToPipe,
                                        related_name='valve_line_pipe_connection',
                                        blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Тип присоединения арматуры к трубе'),
                                        verbose_name=_("Присоединение к трубе"))

    warranty_period_min = models.IntegerField(null=True, blank=True,
                                              help_text=_("Гарантийный срок, мес"),
                                              verbose_name=_("Гарантийный срок мин, мес"))
    warranty_period_min_variety = models.ForeignKey(WarrantyTimePeriodVariety,
                                                    related_name='valve_line_warranty_period_min_variety',
                                                    blank=True, null=True,
                                                    on_delete=models.SET_NULL,
                                                    help_text=_('Гарантийный срок мин описание'),
                                                    verbose_name=_("Гарантийный срок мин описание"))

    warranty_period_max = models.IntegerField(null=True, blank=True,
                                              help_text=_("Гарантийный срок не более, мес"),
                                              verbose_name=_("Гарантийный срок не более, мес"))
    warranty_period_max_variety = models.ForeignKey(WarrantyTimePeriodVariety,
                                                    related_name='valve_line_warranty_period_max_variety',
                                                    blank=True, null=True,
                                                    on_delete=models.SET_NULL,
                                                    help_text=_('Гарантийный срок не более, описание'),
                                                    verbose_name=_("Гарантийный срок не более, описание"))
    valve_in_service_years = models.IntegerField(null=True, blank=True,
                                                 help_text=_("Расчетный срок эксплуатации - не менее, лет"),
                                                 verbose_name=_("Расчетный срок эксплуатации - не менее, лет"))
    valve_in_service_years_comment = models.CharField(max_length=500, blank=True, null=True,
                                                      help_text=_("Условие выработки расчетного срока эксплуатации"),
                                                      verbose_name=_("Условие выработки расчетного срока эксплуатации"))

    valve_in_service_cycles = models.IntegerField(null=True, blank=True,
                                                  help_text=_("Расчетное количество циклов"),
                                                  verbose_name=_("Расчетное количество циклов"))
    valve_in_service_cycles_comment = models.CharField(max_length=500, blank=True, null=True,
                                                       help_text=_("Условие выработки расчетного количества циклов"),
                                                       verbose_name=_("Условие выработки расчетного количества циклов"))
    valve_model_dimension_data_table = models.ForeignKey(
        # ValveDimensionTable,
        'valve_data.ValveDimensionTable',  # ← ИСПОЛЬЗОВАТЬ СТРОКОВУЮ ССЫЛКУ
        related_name='valve_dimension_table',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Таблица ВГХ'),
        help_text=_('Таблица весо-габаритных характеристик для этой серии')

    )
    class Meta:
        ordering = ['valve_variety', 'valve_producer', 'name']
        verbose_name = _("Серия арматуры")
        verbose_name_plural = _("Серии арматуры")

    def debug_service_life(self):
        """Метод для отладки сроков службы"""
        print(f"Текущая модель: {self.name}")
        print(f"warranty_min: {self.warranty_period_min}")
        print(f"effective_warranty_min: {self.effective_warranty_period_min}")
        print(f"original_valve_line: {self.original_valve_line}")
        if self.original_valve_line:
            print(f"original warranty_min: {self.original_valve_line.warranty_period_min}")

    def __str__(self):
        return self.effective_name

    def get_full_data(self, show_data_source=False):
        """Получает полную информацию о ValveLine с учетом original_valve_line"""
        kv_data_info = self.get_kv_data_info(show_data_source)
        dimension_data_info = self.get_dimension_data_info(show_data_source)  # ← ДОБАВЬТЕ ЭТО

        return {
            'basic_info': self.get_basic_info(show_data_source),
            'technical_specs': self.get_technical_specs(show_data_source),
            'temperature_info': self.get_temperature_info(show_data_source),
            'body_colors': self.get_body_colors_info(show_data_source),
            'model_data': self.get_model_data_info(show_data_source),
            'kv_data': kv_data_info,
            'kv_summary': self.get_kv_data_summary(show_data_source),
            'dimension_data': dimension_data_info,  # ← ДОБАВЬТЕ ЭТО
            'descriptions': self.get_descriptions_info(show_data_source),
            'service_life': self.get_service_life_info(show_data_source),
            'status': self.get_status_info(show_data_source),
            'data_source_info': {
                'current_model': self.name,
                'has_original': bool(self.original_valve_line),
                'original_model': getattr(self.original_valve_line, 'name', None) if self.original_valve_line else None
            } if show_data_source else None
        }
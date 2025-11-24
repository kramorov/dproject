from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from djangoProject1.common_models.abstract_models import AbstractValveModel
from djangoProject1.common_models.eav_abstract_models import AbstractEAVAttribute
from params.models import ValveTypes , MeasureUnits , MountingPlateTypes , StemSize , DnVariety , PnVariety , \
    BodyColor , OptionVariety , ValveFunctionVariety , SealingClass , WarrantyTimePeriodVariety , ValveActuationVariety
from producers.models import Producer , Brands
from materials.models import MaterialGeneral , MaterialGeneralMoreDetailed , MaterialStandard , MaterialSpecified


# ValveLine properties

class AllowedDnTemplate(models.Model):
    """Шаблон допустимых Dn - для выбора в ValveLineSealingMaterial, ValveLineValveActuationVariety """
    name = models.CharField(max_length=150, null=True, blank=True, verbose_name=_('Название'),
                            help_text=_('Символьное обозначение шаблона допустимых Dn'))
    code = models.CharField(max_length=50, blank=True, null=True,  # unique=True ,
                            verbose_name=_("Код"),
                            help_text=_('Код шаблона допустимых Dn'))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    dn = models.ManyToManyField(DnVariety, related_name='allowed_dn_template_table',
                                   blank=True,
                                   verbose_name=_('Dn'),
                                   help_text=_('Dn арматуры, мм'))
    class Meta :
        verbose_name = _("Шаблон допустимых Dn")
        verbose_name_plural = _("Шаблоны допустимых Dn")
        ordering = ['is_active' , 'sorting_order' ]
    def __str__(self) :
        return self.name

class ValveConnectionToPipe(models.Model) :
    name = models.CharField(max_length=100 ,
                            help_text=_("Символьное обозначение типа присоединения арматуры к трубе") ,
                            verbose_name=_("Символьное обозначение типа присоединения арматуры к трубе"))
    code = models.CharField(max_length=50 , unique=True ,
                            verbose_name=_("Код типа присоединения арматуры к трубе"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _("Тип присоединения арматуры к трубе")
        verbose_name_plural = _("Типы присоединения арматуры к трубе")

    def __str__(self) :
        return self.name


class ValveVariety(models.Model) :
    symbolic_code = models.CharField(max_length=2 , help_text='Символьное обозначение \
    типа арматуры' , verbose_name=_("Символьное обозначение типа арматуры"))
    actuator_gearbox_combinations = models.CharField(max_length=10 , help_text='Символьное обозначение \
    подходящего типа привода и редуктора' , verbose_name=_("Символьное обозначение \
    подходящего типа привода и редуктора"))
    text_description = models.CharField(max_length=200 , blank=True , help_text='Текстовое описание \
    типа арматуры' , verbose_name=_("Текстовое описание типа арматуры"))

    class Meta :
        ordering = ['text_description']
        verbose_name = _("Тип арматуры")
        verbose_name_plural = _("Типы арматуры")

    def __str__(self) :
        return self.text_description


class ConstructionVariety(models.Model) :
    name = models.CharField(max_length=100 , help_text=_(
        "Название типа конструкции вида арматуры") ,
                            verbose_name=_("Название типа конструкции"))
    valve_variety = models.ForeignKey(ValveVariety , related_name='construction_variety_valve_variety' ,
                                      on_delete=models.CASCADE ,
                                      help_text=_('Тип конструкции вида арматуры') ,
                                      verbose_name=_("Тип конструкции вида арматуры"))
    code = models.CharField(max_length=50 , unique=True ,
                            verbose_name=_("Код типа конструкции"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _("Название типа конструкции вида арматуры")
        verbose_name_plural = _("Названия типа конструкции вида арматуры")

    def __str__(self) :
        return self.name


class PortQty(models.Model) :
    name = models.CharField(max_length=100 , help_text=_(
        "Количество портов арматуры") , verbose_name=_("Количество портов арматуры"))
    code = models.CharField(max_length=50 , unique=True , help_text=_(
        "Код количества портов арматуры") ,
                            verbose_name=_("Код количества портов арматуры"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _("Количество портов арматуры")
        verbose_name_plural = _("Количество портов арматуры")

    def __str__(self) :
        return self.name


# ValveLine
class ValveModelDataTable(models.Model):
    """Шаблон моделей арматуры - для выбора в ValveLine"""
    name = models.CharField(max_length=100, help_text=_('Название шаблона для выбора в списке'),
                            verbose_name=_('Название'))
    code = models.CharField(max_length=50, unique=True,
                            help_text=_('Код шаблона'),
                            verbose_name=_('Код шаблона'))

    valve_brand = models.ForeignKey(Brands, blank=True, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='valve_model_data_table_valve_brand',
                                    help_text=_('Бренд серии арматуры для шаблона тех.данных для серии. Здесь используем для поиска'),
                                    verbose_name=_("Бренд"))
    valve_variety = models.ForeignKey(ValveVariety,  blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      related_name='valve_model_data_table_valve_variety',
                                      help_text=_('Тип арматуры для шаблона тех.данных для серии, здесь используем для поиска'),
                                      verbose_name=_("Тип арматуры"))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    description = models.TextField(blank=True, null=True, verbose_name=_('Описание шаблона'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активный'))

    class Meta:
        verbose_name = _("Шаблон данных серий арматуры")
        verbose_name_plural = _("Шаблоны данных серии  арматуры")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

class ValveModelKvDataTable(models.Model):
    """Шаблон значений Kvs моделей арматуры - для выбора в ValveLine"""
    name = models.CharField(max_length=100, help_text=_('Название шаблона Kvs для выбора в списке'),
                            verbose_name=_('Название'))
    code = models.CharField(max_length=50, unique=True,
                            help_text=_('Код шаблона Kvs'),
                            verbose_name=_('Код шаблона'))

    valve_brand = models.ForeignKey(Brands, blank=True, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='valve_data_kvs_valve_brand',
                                    help_text=_('Бренд серии арматуры для шаблона Kvs для серии. Здесь используем для поиска'),
                                    verbose_name=_("Бренд"))
    valve_variety = models.ForeignKey(ValveVariety,  blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      related_name='valve_data_kvs_valve_variety',
                                      help_text=_('Тип арматуры для шаблона Kvs для серии, здесь используем для поиска'),
                                      verbose_name=_("Тип арматуры"))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    description = models.TextField(blank=True, null=True, verbose_name=_('Описание шаблона'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активный'))

    class Meta:
        verbose_name = _("Шаблон данных Kv для серии арматуры")
        verbose_name_plural = _("Шаблоны данных Kv для серий арматуры")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"


import re
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class ValveLine(models.Model):
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
        AllowedDnTemplate ,
        blank=True , null=True ,
        on_delete=models.SET_NULL ,
        related_name='valve_line_allowed_dn_table' ,
        verbose_name=_("Допустимые Dn") ,
        help_text=_("Допустимые Dn для этой серии")
    )

    valve_model_data_table = models.ForeignKey(ValveModelDataTable,
                                               related_name='valve_line_valve_model_data_table',
                                               blank=True,
                                               null=True,
                                               on_delete=models.SET_NULL,
                                               verbose_name=_('Шаблон таблицы данных'),
                                               help_text=_('Шаблон таблицы данных моделей арматуры для этой серии'))
    valve_model_kv_data_table = models.ForeignKey(ValveModelKvDataTable ,
                                               related_name='valve_line_valve_model_kv_data_table' ,
                                               blank=True ,
                                               null=True ,
                                               on_delete=models.SET_NULL ,
                                               verbose_name=_('Шаблон таблицы данных Kvs') ,
                                               help_text=_('Шаблон таблицы данных Kvs моделей арматуры для этой серии'))

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

    # Effective properties для всех полей с наследованием
    @property
    def effective_name(self):
        # return self.get_field_value_with_fallback('name')
        return self.name

    @property
    def effective_code(self):
        # return self.get_field_value_with_fallback('code')
        return self.code

    @property
    def effective_description(self):
        return self.get_field_value_with_fallback('description')

    @property
    def effective_features_text(self):
        return self.get_field_value_with_fallback('features_text')

    @property
    def effective_application_text(self):
        return self.get_field_value_with_fallback('application_text')

    @property
    def effective_valve_producer(self):
        return self.get_field_value_with_fallback('valve_producer')

    @property
    def effective_valve_brand(self):
        return self.get_field_value_with_fallback('valve_brand')

    @property
    def effective_valve_variety(self):
        return self.get_field_value_with_fallback('valve_variety')

    @property
    def effective_valve_function(self):
        return self.get_field_value_with_fallback('valve_function')

    @property
    def effective_valve_actuation(self):
        return self.get_field_value_with_fallback('valve_actuation')

    @property
    def effective_valve_sealing_class(self):
        return self.get_field_value_with_fallback('valve_sealing_class')

    @property
    def effective_body_material(self):
        return self.get_field_value_with_fallback('body_material')

    @property
    def effective_body_material_specified(self):
        return self.get_field_value_with_fallback('body_material_specified')

    @property
    def effective_shut_element_material(self):
        return self.get_field_value_with_fallback('shut_element_material')

    @property
    def effective_shut_element_material_specified(self):
        return self.get_field_value_with_fallback('shut_element_material_specified')

    @property
    def effective_sealing_element_material(self):
        return self.get_field_value_with_fallback('sealing_element_material')

    @property
    def effective_sealing_element_material_specified(self):
        return self.get_field_value_with_fallback('sealing_element_material_specified')

    @property
    def effective_item_code_template(self):
        return self.get_field_value_with_fallback('item_code_template')

    @property
    def effective_option_variety(self):
        return self.get_field_value_with_fallback('option_variety')

    @property
    def effective_work_temp_min(self):
        return self.get_field_value_with_fallback('work_temp_min')

    @property
    def effective_work_temp_max(self):
        return self.get_field_value_with_fallback('work_temp_max')

    @property
    def effective_temp_min(self):
        return self.get_field_value_with_fallback('temp_min')

    @property
    def effective_temp_max(self):
        return self.get_field_value_with_fallback('temp_max')

    @property
    def effective_allowed_dn_table(self):
        return self.get_field_value_with_fallback('allowed_dn_table')

    @property
    def effective_port_qty(self):
        return self.get_field_value_with_fallback('port_qty')

    @property
    def effective_construction_variety(self):
        return self.get_field_value_with_fallback('construction_variety')

    @property
    def effective_valve_model_data_table(self):
        return self.get_field_value_with_fallback('valve_model_data_table')

    @property
    def effective_pipe_connection(self):
        return self.get_field_value_with_fallback('pipe_connection')

    @property
    def effective_warranty_period_min(self):
        return self.get_field_value_with_fallback('warranty_period_min')

    @property
    def effective_warranty_period_min_variety(self):
        return self.get_field_value_with_fallback('warranty_period_min_variety')

    @property
    def effective_warranty_period_max(self):
        return self.get_field_value_with_fallback('warranty_period_max')

    @property
    def effective_warranty_period_max_variety(self):
        return self.get_field_value_with_fallback('warranty_period_max_variety')

    @property
    def effective_valve_in_service_years(self):
        return self.get_field_value_with_fallback('valve_in_service_years')

    @property
    def effective_valve_in_service_years_comment(self):
        return self.get_field_value_with_fallback('valve_in_service_years_comment')

    @property
    def effective_valve_in_service_cycles(self):
        return self.get_field_value_with_fallback('valve_in_service_cycles')

    @property
    def effective_valve_in_service_cycles_comment(self):
        return self.get_field_value_with_fallback('valve_in_service_cycles_comment')

    # Базовые методы для работы с наследованием
    def get_field_value_with_fallback(self, field_name, show_data_source=False, recursion_level=0, max_recursion=5):
        """
        Рекурсивно получает значение поля с учетом original_valve_line
        """
        if recursion_level >= max_recursion:
            if show_data_source:
                return {
                    'value': None,
                    'source': None,
                    'comment': f"Достигнут максимальный уровень рекурсии ({max_recursion})"
                }
            return None

        # Получаем значение из текущей модели
        current_value = getattr(self, field_name, None)

        # Проверяем, является ли значение "пустым"
        is_empty = self._is_value_empty(current_value)

        # Если значение есть и оно не пустое, возвращаем его
        if not is_empty:
            if show_data_source:
                return {
                    'value': current_value,
                    'source': self,
                    'comment': f"Значение из модели: {self.name}"
                }
            else:
                return current_value

        # Если значения нет, проверяем original_valve_line
        if self.original_valve_line:
            print(f"DEBUG: Checking original_valve_line for {field_name}, recursion_level: {recursion_level}")
            fallback_result = self.original_valve_line.get_field_value_with_fallback(
                field_name, show_data_source, recursion_level + 1, max_recursion
            )
            print(f"DEBUG: fallback_result for {field_name}: {fallback_result}")

            if fallback_result:
                if show_data_source:
                    if isinstance(fallback_result, dict) and fallback_result.get('value') is not None:
                        fallback_result[
                            'comment'] = f"Значение унаследовано из: {self.original_valve_line.name} (уровень {recursion_level + 1})"
                    return fallback_result
                else:
                    return fallback_result

        # Если ничего не найдено
        if show_data_source:
            return {
                'value': None,
                'source': None,
                'comment': "Значение не найдено"
            }
        return None  # Изменил с "Нет данных" на None

    def _is_value_empty(self, value):
        """Проверяет, является ли значение пустым"""
        if value is None:
            return True
        elif isinstance(value, str) and value.strip() == '':
            return True
        # elif isinstance(value, (int, float)) and value == 0:
        #     return True  # 0 считается пустым значением для числовых полей
        elif hasattr(value, 'pk') and not value.pk:
            return True
        return False

    # Упрощенные методы получения данных через effective properties
    def get_basic_info(self, show_data_source=False):
        """Получает основную информацию с учетом наследования"""
        fields = [
            ('name', 'effective_name', 'Название'),
            ('code', 'effective_code', 'Код серии'),
            ('producer', 'effective_valve_producer', 'Производитель'),
            ('brand', 'effective_valve_brand', 'Бренд'),
            ('valve_variety', 'effective_valve_variety', 'Тип арматуры'),
            ('function', 'effective_valve_function', 'Функция'),
            ('option_variety', 'effective_option_variety', 'Стандарт или опция'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value not in [None, '', 'Нет данных']:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_technical_specs(self, show_data_source=False):
        """Получает технические характеристики с учетом наследования"""
        fields = [
            ('sealing_class', 'effective_valve_sealing_class', 'Класс герметичности'),
            ('body_material_type', 'effective_body_material', 'Материал корпуса (тип)'),
            ('body_material_specified', 'effective_body_material_specified', 'Материал корпуса (марка)'),
            ('shut_element_type', 'effective_shut_element_material', 'Материал запорного элемента (тип)'),
            ('shut_element_specified', 'effective_shut_element_material_specified',
             'Материал запорного элемента (марка)'),
            ('sealing_element_type', 'effective_sealing_element_material', 'Тип материала уплотнения'),
            ('sealing_element_specified', 'effective_sealing_element_material_specified', 'Материал уплотнения'),
            ('valve_actuation', 'effective_valve_actuation', 'Тип механизма управления'),
            ('port_qty', 'effective_port_qty', 'Количество портов'),
            ('construction', 'effective_construction_variety', 'Тип конструкции'),
            ('pipe_connection', 'effective_pipe_connection', 'Присоединение к трубе'),
            ('allowed_dn_table', 'effective_allowed_dn_table', 'Допустимые Dn'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value not in [None, '', 'Нет данных']:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_temperature_info(self, show_data_source=False):
        """Получает информацию о температурных характеристиках"""
        fields = [
            ('work_temp_min', 'effective_work_temp_min', 'Минимальная рабочая температура, °С'),
            ('work_temp_max', 'effective_work_temp_max', 'Максимальная рабочая температура, °С'),
            ('temp_min', 'effective_temp_min', 'Минимальная температура, °С'),
            ('temp_max', 'effective_temp_max', 'Максимальная температура, °С'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value is not None:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_body_colors_info(self, show_data_source=False):
        """Получает информацию о цветах корпуса"""
        body_colors = self.valve_line_body_colors.select_related(
            'body_color', 'option_variety'
        ).filter(is_available=True).order_by('option_variety__sorting_order', 'sorting_order')

        colors_data = []
        for color in body_colors:
            color_info = {
                'color_name': color.body_color.name,
                'option_type': color.option_variety.name,
                'additional_cost': float(color.additional_cost),
                'lead_time_days': color.lead_time_days,
                'option_code': color.option_code_template,
                'hex_color': getattr(color.body_color, 'hex_code', '#CCCCCC'),
                'source_comment': f"Цвет из текущей модели: {self.name}" if show_data_source else None
            }
            colors_data.append(color_info)

        if not colors_data and self.original_valve_line:
            return self.original_valve_line.get_body_colors_info(show_data_source)

        return colors_data

    def get_model_data_info(self, show_data_source=False):
        """Получает информацию о модельных данных (DN/PN таблица) с учетом наследования"""
        model_data_table = self.effective_valve_model_data_table
        allowed_dn_table = self.effective_allowed_dn_table

        if not model_data_table or not allowed_dn_table:
            return {
                'model_data': [],
                'has_data': False,
                'source_comment': None
            }

        allowed_dn_ids = allowed_dn_table.dn.values_list('id', flat=True)
        from .models import ValveLineModelData

        model_data_queryset = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table,
            valve_model_dn__id__in=allowed_dn_ids
        ).select_related('valve_model_dn', 'valve_model_pn').order_by(
            'valve_model_dn__sorting_order', 'valve_model_pn__sorting_order'
        )

        model_data = self._get_model_data_table(model_data_queryset)

        return {
            'model_data': model_data,
            'has_data': bool(model_data),
            'source_comment': f"Данные из: {self.name}" if show_data_source else None
        }

    def get_descriptions_info(self, show_data_source=False):
        """Получает описания с учетом наследования"""
        fields = [
            ('description', 'effective_description', 'Описание'),
            ('features', 'effective_features_text', 'Особенности'),
            ('application', 'effective_application_text', 'Применение'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_service_life_info(self, show_data_source=False):
        """Получает информацию о сроках службы с учетом наследования"""
        warranty_min = self.effective_warranty_period_min
        warranty_min_variety = self.effective_warranty_period_min_variety
        warranty_max = self.effective_warranty_period_max
        warranty_max_variety = self.effective_warranty_period_max_variety
        service_years = self.effective_valve_in_service_years
        service_years_comment = self.effective_valve_in_service_years_comment
        service_cycles = self.effective_valve_in_service_cycles
        service_cycles_comment = self.effective_valve_in_service_cycles_comment

        result = []

        # Гарантийные сроки - проверяем только на None
        if warranty_min is not None:
            min_text = f"{warranty_min} мес."
            if warranty_min_variety not in [None, '']:
                min_text += f" ({warranty_min_variety})"
            result.append({
                'label': 'Гарантийный срок мин',
                'value': min_text
            })

        if warranty_max is not None:
            max_text = f"{warranty_max} мес."
            if warranty_max_variety not in [None, '']:
                max_text += f" ({warranty_max_variety})"
            result.append({
                'label': 'Гарантийный срок макс',
                'value': max_text
            })

        # Срок эксплуатации
        if service_years is not None:
            years_text = f"{service_years} лет"
            if service_years_comment not in [None, '']:
                years_text += f" ({service_years_comment})"
            result.append({
                'label': 'Срок эксплуатации',
                'value': years_text
            })

        # Количество циклов
        if service_cycles is not None:
            cycles_text = f"{service_cycles} циклов"
            if service_cycles_comment not in [None, '']:
                cycles_text += f" ({service_cycles_comment})"
            result.append({
                'label': 'Количество циклов',
                'value': cycles_text
            })

        return result

    def get_status_info(self, show_data_source=False):
        """Получает информацию о статусах"""
        return {
            'active': "Активна" if self.is_active else "Не активна",
            'approved': "Проверена" if self.is_approved else "Не проверена",
        }

    # Вспомогательные методы
    def _format_model_data_row(self, data):
        """Формирует строку данных модели арматуры"""
        item_code = f"{self.effective_valve_brand}-{self.effective_code}-{data.valve_model_dn.name}-{data.valve_model_pn.name}"

        return {
            'item_code': item_code,
            'dn': data.valve_model_dn.name,
            'pn': data.valve_model_pn.name,
            'torque_open': data.valve_model_torque_to_open or 0,
            'torque_close': data.valve_model_torque_to_close or 0,
            'thrust_close': data.valve_model_thrust_to_close or 0,
            'rotations': data.valve_model_rotations_to_open or 0,
            'stem_size': data.valve_model_stem_size.name if data.valve_model_stem_size else "",
            'stem_height': data.valve_model_stem_height or 0,
            'construction_length': data.valve_model_construction_length or 0,
            'mounting_plate': data.get_mounting_plates_list_text() if hasattr(data,
                                                                              'get_mounting_plates_list_text') else "",
        }

    def _get_model_data_table(self, model_data_queryset):
        """Вспомогательный метод для форматирования данных моделей"""
        model_data = [
            self._format_model_data_row(data)
            for data in model_data_queryset
        ]
        model_data.sort(key=lambda x: (float(x['pn']), float(x['dn'])))
        return model_data

    def get_model_data_by_dn_pn(self, dn, pn):
        """Получает данные модели по DN и PN с учетом наследования"""
        from .models import ValveLineModelData

        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return None

        try:
            model_data = ValveLineModelData.objects.filter(
                valve_model_data_table=model_data_table,
                valve_model_dn__name=dn,
                valve_model_pn__name=pn
            ).select_related('valve_model_dn', 'valve_model_pn').first()

            if model_data:
                return self._format_model_data_row(model_data)
            return None
        except ValveLineModelData.DoesNotExist:
            return None

    def get_all_models_list(self):
        """Возвращает список всех моделей для использования в других модулях"""
        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return []

        from .models import ValveLineModelData
        model_data_queryset = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table
        ).select_related('valve_model_dn', 'valve_model_pn').order_by(
            'valve_model_dn__sorting_order', 'valve_model_pn__sorting_order'
        )

        return self._get_model_data_table(model_data_queryset)

    # Основной метод для получения полных данных
    def get_full_data(self, show_data_source=False):
        """Получает полную информацию о ValveLine с учетом original_valve_line"""
        return {
            'basic_info': self.get_basic_info(show_data_source),
            'technical_specs': self.get_technical_specs(show_data_source),
            'temperature_info': self.get_temperature_info(show_data_source),
            'body_colors': self.get_body_colors_info(show_data_source),
            'model_data': self.get_model_data_info(show_data_source),
            'descriptions': self.get_descriptions_info(show_data_source),
            'service_life': self.get_service_life_info(show_data_source),
            'status': self.get_status_info(show_data_source),
            'data_source_info': {
                'current_model': self.name,
                'has_original': bool(self.original_valve_line),
                'original_model': getattr(self.original_valve_line, 'name', None) if self.original_valve_line else None
            } if show_data_source else None
        }

    # Методы для работы с артикулами
    def parse_item_code_template(self, template_string, dn=None, pn=None):
        """Парсит шаблон формирования артикула с переменными в формате {%VARIABLE}"""
        if not template_string:
            return ""

        variables = {
            'BRAND': self.effective_valve_brand or "",
            'VALVELINE': self.effective_name or "",
            'CODE': self.effective_code or "",
            'DN': dn or "",
            'PN': pn or "",
            'PRODUCER': self.effective_valve_producer or "",
            'VARIETY': self.effective_valve_variety or "",
        }

        def replace_variable(match):
            variable_name = match.group(1)
            return variables.get(variable_name, "")

        try:
            result = re.sub(r'{%(\w+)}', replace_variable, template_string)
            return result.strip()
        except Exception as e:
            print(f"Error parsing item_code template: {e}")
            return ""

    # Методы форматирования вывода
    def format_text_info(self, show_data_source=False):
        """Форматирует информацию о ValveLine в текстовом виде"""
        data = self.get_full_data(show_data_source)
        lines = []

        lines.append(f"СЕРИЯ АРМАТУРЫ: {self.effective_name or 'Не указано'}")
        lines.append(f"Код серии: {self.effective_code or 'Не указан'}")

        if show_data_source and data.get('data_source_info'):
            lines.append(f"Текущая модель: {data['data_source_info']['current_model']}")
            if data['data_source_info']['has_original']:
                lines.append(f"Наследует из: {data['data_source_info']['original_model']}")

        lines.append("=" * 50)

        # Основная информация
        if data['basic_info']:
            lines.append("ОСНОВНАЯ ИНФОРМАЦИЯ:")
            lines.append("-" * 20)
            for item in data['basic_info']:
                lines.append(f"{item['label']}: {item['value']}")
            lines.append("")

        # Технические характеристики
        if data['technical_specs']:
            lines.append("ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:")
            lines.append("-" * 30)
            for spec in data['technical_specs']:
                lines.append(f"{spec['label']}: {spec['value']}")
            lines.append("")

        # Температурные характеристики
        if data['temperature_info']:
            lines.append("ТЕМПЕРАТУРНЫЕ ХАРАКТЕРИСТИКИ:")
            lines.append("-" * 30)
            for temp in data['temperature_info']:
                lines.append(f"{temp['label']}: {temp['value']}°C")
            lines.append("")

        # Цвета корпуса
        if data['body_colors']:
            lines.append("ДОСТУПНЫЕ ЦВЕТА КОРПУСА:")
            lines.append("-" * 25)
            for color in data['body_colors']:
                color_info = f"  • {color['color_name']} ({color['option_type']})"
                if color['additional_cost'] > 0:
                    color_info += f" +{color['additional_cost']} руб."
                if color['lead_time_days'] > 0:
                    color_info += f" +{color['lead_time_days']} дн."
                if color['option_code']:
                    color_info += f" [код: {color['option_code']}]"
                lines.append(color_info)
            lines.append("")

        # Таблица модельных данных
        if data['model_data']['has_data']:
            lines.append("ТАБЛИЦА МОДЕЛЬНЫХ ДАННЫХ (DN/PN):")
            lines.append("-" * 35)

            lines.append(
                "  DN   |  PN   | Момент откр | Момент закр | Усилие закр | Обороты | Площадка | Шток | Высота штока | Строит.длина")
            lines.append("  " + "-" * 110)

            for model in data['model_data']['model_data']:
                line = f"  {model['dn']:4} | {model['pn']:5} | " \
                       f"{model['torque_open']:11} | {model['torque_close']:11} | " \
                       f"{model['thrust_close']:10} | {model['rotations']:8} | " \
                       f"{model['mounting_plate']:9} | {model['stem_size']:5} | " \
                       f"{model['stem_height']:11} | {model['construction_length']:12}"
                lines.append(line)
            lines.append("")

        # Описания
        if data['descriptions']:
            lines.append("ОПИСАНИЯ:")
            lines.append("-" * 15)
            for desc in data['descriptions']:
                if desc['value']:
                    lines.append(f"{desc['label'].upper()}:")
                    lines.append("-" * len(desc['label']) + "-")
                    lines.append(desc['value'])
                    lines.append("")

        # Сроки службы
        if data['service_life']:
            lines.append("СРОКИ СЛУЖБЫ:")
            lines.append("-" * 15)
            for service in data['service_life']:
                lines.append(f"{service['label']}: {service['value']}")
            lines.append("")

        # Статусы
        lines.append(f"СТАТУС: {data['status']['active']}, {data['status']['approved']}")

        return "\n".join(lines)

    def format_html_info(self, show_data_source=False):
        """Форматирует информацию о ValveLine в HTML виде для админки"""
        from django.utils.html import format_html
        text_content = self.format_text_info(show_data_source)
        return format_html(f"<pre>{text_content}</pre>")

    # Дополнительные полезные методы
    @property
    def has_technical_data(self):
        return bool(self.get_technical_specs())

    @property
    def has_options(self):
        return bool(self.get_body_colors_info())

    def get_available_dn_pn_combinations(self):
        """Возвращает все доступные комбинации DN/PN"""
        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return []

        from .models import ValveLineModelData
        combinations = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table
        ).values_list('valve_model_dn__name', 'valve_model_pn__name').distinct()

        return [f"{dn}/{pn}" for dn, pn in combinations]

    def clean(self):
        """Валидация модели перед сохранением"""
        super().clean()

        errors = {}

        # Проверка обязательных полей
        if not self.name and not self.original_valve_line:
            errors['name'] = 'Название серии обязательно, если не указана исходная серия'

        if not self.code and not self.original_valve_line:
            errors['code'] = 'Код серии обязателен, если не указана исходная серия'

        if not self.valve_brand and not self.original_valve_line:
            errors['valve_brand'] = 'Бренд обязателен, если не указана исходная серия'

        if not self.valve_producer and not self.original_valve_line:
            errors['valve_producer'] = 'Производитель обязателен, если не указана исходная серия'

        # Проверка циклических ссылок
        if self.original_valve_line and self.original_valve_line == self:
            errors['original_valve_line'] = 'Нельзя указывать текущую серию как исходную'

        # Проверка глубины наследования
        if self.original_valve_line:
            depth = self._get_inheritance_depth()
            if depth > 5:
                errors[
                    'original_valve_line'] = f'Слишком глубокая цепочка наследования ({depth} уровней). Максимум 5 уровней.'

        if errors:
            raise ValidationError(errors)

    def _get_inheritance_depth(self, current_level=0, max_level=10):
        """Рекурсивно вычисляет глубину цепочки наследования"""
        if current_level >= max_level:
            return current_level

        if self.original_valve_line:
            return self.original_valve_line._get_inheritance_depth(current_level + 1, max_level)

        return current_level

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической проверки"""
        self.full_clean()  # Вызывает clean() и другие валидации
        super().save(*args, **kwargs)

    def get_missing_required_fields(self):
        """Возвращает список обязательных полей, которые не заполнены и не наследуются"""
        missing_fields = []

        if not self.name and not self._will_inherit('name'):
            missing_fields.append('name')

        if not self.code and not self._will_inherit('code'):
            missing_fields.append('code')

        if not self.valve_brand and not self._will_inherit('valve_brand'):
            missing_fields.append('valve_brand')

        if not self.valve_producer and not self._will_inherit('valve_producer'):
            missing_fields.append('valve_producer')

        return missing_fields

    def _will_inherit(self, field_name):
        """Проверяет, будет ли поле унаследовано от original_valve_line"""
        if not self.original_valve_line:
            return False

        # Проверяем, есть ли значение в цепочке наследования
        current = self.original_valve_line
        visited = set()
        depth = 0

        while current and depth < 10:  # Защита от бесконечной рекурсии
            if current.id in visited:
                break
            visited.add(current.id)

            value = getattr(current, field_name, None)
            if value not in [None, '']:
                return True

            if not current.original_valve_line:
                break

            current = current.original_valve_line
            depth += 1

        return False

    @property
    def has_required_data(self):
        """Проверяет, есть ли все обязательные данные (прямо или через наследование)"""
        return len(self.get_missing_required_fields()) == 0

    def get_validation_warnings(self):
        """Возвращает предупреждения о потенциальных проблемах"""
        warnings = []

        # Проверка обязательных полей
        missing_fields = self.get_missing_required_fields()
        if missing_fields:
            warnings.append(f"Обязательные поля не заполнены и не будут унаследованы: {', '.join(missing_fields)}")

        # Проверка глубины наследования
        if self.original_valve_line:
            depth = self._get_inheritance_depth()
            if depth > 3:
                warnings.append(f"Глубокая цепочка наследования ({depth} уровней), что может замедлить работу")

        # Проверка на одинаковые названия в цепочке наследования
        if self.name and self.original_valve_line:
            current = self.original_valve_line
            while current:
                if current.name == self.name:
                    warnings.append("Название совпадает с одним из родителей в цепочке наследования")
                    break
                current = current.original_valve_line

        return warnings


class ValveLineBodyColor(models.Model) :
    """Связь серии арматуры с цветами корпуса и типами исполнения"""
    valve_line = models.ForeignKey(
        ValveLine ,
        on_delete=models.CASCADE ,
        related_name='valve_line_body_colors' ,
        verbose_name=_("Серия арматуры")
    )
    body_color = models.ForeignKey(
        BodyColor ,
        on_delete=models.CASCADE ,
        related_name='valve_line_body_color_usages' ,
        verbose_name=_("Цвет корпуса")
    )
    option_variety = models.ForeignKey(
        OptionVariety ,
        on_delete=models.CASCADE ,
        related_name='valve_line_body_color_option_variety' ,
        verbose_name=_("Стандарт или опция")
    )
    option_code_template = models.CharField(max_length=100 , blank=True , null=True ,
                                            help_text=_("Шаблон кодировки для опции") ,
                                            verbose_name=_("Шаблон кодировки для опции"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_available = models.BooleanField(default=True , verbose_name=_("Доступно"))
    additional_cost = models.DecimalField(
        max_digits=10 ,
        decimal_places=2 ,
        default=0 ,
        verbose_name=_("Дополнительная стоимость") ,
        help_text=_("Дополнительная стоимость для этого цвета и типа исполнения")
    )
    lead_time_days = models.IntegerField(
        default=0 ,
        verbose_name=_("Срок изготовления (дни)") ,
        help_text=_("Дополнительное время изготовления в днях")
    )
    notes = models.TextField(blank=True , verbose_name=_("Примечания"))

    class Meta :
        ordering = ['valve_line' , 'option_variety__sorting_order' , 'sorting_order']
        verbose_name = _("Цвет корпуса серии")
        verbose_name_plural = _("Цвета корпусов серий")
        unique_together = ['valve_line' , 'body_color' , 'option_variety']

    def __str__(self) :
        return f"{self.valve_line} - {self.body_color} ({self.option_variety})"

    def clean(self) :
        """Валидация связи цвета и типа исполнения"""
        # Можно добавить дополнительные проверки, если нужно
        super().clean()


# EAV


class EAVAttribute(models.Model) :
    """Атрибут EAV системы"""
    name = models.CharField(max_length=100 , verbose_name=_("Название атрибута"))
    code = models.CharField(max_length=50 , unique=True , verbose_name=_("Код атрибута"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    data_type = models.CharField(
        max_length=20 ,
        choices=[
            ('string' , _('Строка')) ,
            ('integer' , _('Целое число')) ,
            ('float' , _('Десятичное число')) ,
            ('boolean' , _('Да/Нет')) ,
        ] ,
        default='string' ,
        verbose_name=_("Тип данных")
    )
    unit = models.CharField(max_length=20 , blank=True , verbose_name=_("Единица измерения"))

    class Meta :
        verbose_name = _("Атрибут")
        verbose_name_plural = _("Атрибуты")
        ordering = ['name']

    def __str__(self) :
        return f"{self.name}"


class EAVValue(models.Model) :
    """Справочник значений для атрибутов"""
    attribute = models.ForeignKey(
        EAVAttribute ,
        on_delete=models.CASCADE ,
        related_name='possible_values' ,
        verbose_name=_("Атрибут")
    )
    value = models.CharField(max_length=200 , verbose_name=_("Значение"))
    display_name = models.CharField(max_length=200 , verbose_name=_("Отображаемое название"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    order = models.IntegerField(default=0 , verbose_name=_("Порядок"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        verbose_name = _("Значение атрибута")
        verbose_name_plural = _("Значения атрибутов")
        ordering = ['attribute' , 'order' , 'value']
        unique_together = ['attribute' , 'value']

    def __str__(self) :
        return f"{self.display_name}"


class ValveVarietyAttribute(models.Model) :
    """Связь разновидности арматуры с допустимыми атрибутами"""
    valve_variety = models.ForeignKey(
        ValveVariety ,
        on_delete=models.CASCADE ,
        related_name='allowed_attributes' ,
        verbose_name=_("Разновидность арматуры")
    )
    attribute = models.ForeignKey(
        EAVAttribute ,
        on_delete=models.CASCADE ,
        related_name='valve_varieties' ,
        verbose_name=_("Атрибут")
    )
    is_required = models.BooleanField(default=False , verbose_name=_("Обязательный"))
    order = models.IntegerField(default=0 , verbose_name=_("Порядок"))

    class Meta :
        verbose_name = _("Атрибут разновидности")
        verbose_name_plural = _("Атрибуты разновидностей")
        ordering = ['valve_variety' , 'order']
        unique_together = ['valve_variety' , 'attribute']

    def __str__(self) :
        return f"{self.attribute}"

class ValveLineModelData(models.Model) :

    """Таблица с данными для шаблона моделей арматуры ValveModelDataTable, а он - для выбора в ValveLine"""
    name = models.CharField(max_length=50 , null=True, blank=True, verbose_name=_('Артикул') ,
                            help_text=_('Символьное обозначение (артикул)\
         модели арматуры производителя'))

    valve_model_data_table = models.ForeignKey(ValveModelDataTable,
                                                  related_name='model_data',
                                                  blank=True ,
                                                  null=True ,
                                                  on_delete=models.CASCADE,
                                                  verbose_name=_('Шаблон моделей'),
                                                  help_text=_('Шаблон моделей арматуры'))
    valve_model_dn = models.ForeignKey(DnVariety , related_name='valve_line_model_dn_data' ,
                                       blank=True ,
                                       null=True ,
                                       on_delete=models.SET_NULL ,
                                       verbose_name=_('Dn') ,
                                       help_text=_('Dn арматуры, мм'))
    valve_model_pn = models.ForeignKey(PnVariety , related_name='valve_line_model_pn_data' ,
                                       blank=True ,
                                       null=True ,
                                       on_delete=models.SET_NULL ,
                                       verbose_name=_('Pn') ,
                                       help_text=_('Pn арматуры, бар'))
    valve_model_torque_to_open = models.DecimalField(max_digits=5 , decimal_places=0 , null=True , default=0 ,
                                                     verbose_name=_("Момент откр") ,
                                                     help_text=_('Момент на открытие, Н'))
    valve_model_torque_to_close = models.DecimalField(max_digits=5 , decimal_places=0 ,null=True , default=0 ,
                                                      verbose_name=_("Момент закр") ,
                                                      help_text=_('Момент на открытие, Н'))
    valve_model_thrust_to_close = models.DecimalField(max_digits=8 , decimal_places=0 , null=True , default=0 ,
                                                      help_text=_('Усилие на закрытие, Н') ,
                                                      verbose_name=_("Усилие закр"))
    valve_model_rotations_to_open = models.DecimalField(max_digits=5 , decimal_places=1 ,null=True , default=0 ,
                                                        verbose_name=_('Обороты') ,
                                                        help_text=_('Число оборотов на открытие'))
    valve_model_stem_size = models.ForeignKey(StemSize , related_name='valve_line_model_stem_size' ,
                                              blank=True ,
                                              null=True ,
                                              on_delete=models.SET_NULL ,
                                              verbose_name=_('Шток') ,
                                              help_text=_('Размер штока модели арматуры'))
    valve_model_stem_height = models.DecimalField(max_digits=6 , decimal_places=1 ,null=True , default=0 ,
                                                  verbose_name=_('Высота штока') ,
                                                  help_text=_('Высота штока, мм'))
    valve_model_construction_length = models.DecimalField(max_digits=6 , decimal_places=1 ,null=True , default=0 ,
                                                          verbose_name=_('Строит.длина') ,
                                                          help_text=_('Строительная длина, мм'))
    valve_model_mounting_plate = models.ManyToManyField(MountingPlateTypes , blank=True ,
                                                        related_name='valve_line_model_mount_data' ,
                                                        verbose_name=_('Монт.площадка') ,
                                                        help_text='Монтажная площадка модели арматуры')

    class Meta :
        verbose_name = _("Данные модели арматуры")
        verbose_name_plural = _("Данные моделей арматуры")
        ordering = ['valve_model_data_table' , 'valve_model_pn' , 'valve_model_dn']

    def __str__(self) :
        if self.name is None and self.valve_model_dn is None:
            return "No data"
        return f"Данные для Dn={self.valve_model_dn.name} Pn={self.valve_model_pn.name}" if self.name=="" else self.name

class ValveLineModelKvData(models.Model) :
    valve_model_kv_data_table = models.ForeignKey(ValveModelKvDataTable,
                                                  related_name='valve_model_kv_data_table',
                                                  on_delete=models.CASCADE,
                                                  verbose_name=_('Шаблон моделей'),
                                                  help_text=_('Шаблон моделей арматуры'))
    valve_model_dn = models.ForeignKey(DnVariety , related_name='valve_model_kv_data_table_dn_data' ,
                                       blank=True ,
                                       null=True ,
                                       on_delete=models.SET_NULL ,
                                       verbose_name=_('Dn') ,
                                       help_text=_('Dn арматуры, мм'))
    valve_model_pn = models.ForeignKey(PnVariety , related_name='valve_model_kv_data_table_pn_data' ,
                                       blank=True ,
                                       null=True ,
                                       on_delete=models.SET_NULL ,
                                       verbose_name=_('Pn') ,
                                       help_text=_('Pn арматуры, бар'))
    valve_model_openinig_angle = models.DecimalField(max_digits=5 , decimal_places=1 , null=True , default=0 ,
                                         verbose_name=_("Угол") ,
                                         help_text=_('Угол открытия арматуры, градусов °'))
    valve_model_kv = models.DecimalField(max_digits=8 , decimal_places=1 , null=True , default=0 ,
                                                     verbose_name=_("Kv,м3/час") ,
                                                     help_text=_('Kv,м3/час, при открытии на угол градусов'))

    class Meta :
        verbose_name = _("Данные Kv серии арматуры")
        verbose_name_plural = _("Данные Kv серии арматуры")
        ordering = ['valve_model_kv_data_table' , 'valve_model_pn' , 'valve_model_dn']


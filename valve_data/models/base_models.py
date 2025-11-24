from django.db import models
from django.utils.translation import gettext_lazy as _
from params.models import (
    ValveTypes, MeasureUnits, MountingPlateTypes, StemSize, DnVariety, PnVariety,
    BodyColor, OptionVariety, ValveFunctionVariety, SealingClass,
    WarrantyTimePeriodVariety, ValveActuationVariety
)
from producers.models import Producer, Brands
from materials.models import MaterialGeneral, MaterialSpecified


class AllowedDnTemplate(models.Model):
    """Шаблон допустимых Dn - для выбора в ValveLineSealingMaterial, ValveLineValveActuationVariety """
    name = models.CharField(max_length=150, null=True, blank=True, verbose_name=_('Название'),
                            help_text=_('Символьное обозначение шаблона допустимых Dn'))
    code = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_('Код шаблона допустимых Dn'))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    dn = models.ManyToManyField(DnVariety, related_name='allowed_dn_template_table',
                                blank=True,
                                verbose_name=_('Dn'),
                                help_text=_('Dn арматуры, мм'))

    class Meta:
        verbose_name = _("Шаблон допустимых Dn")
        verbose_name_plural = _("Шаблоны допустимых Dn")
        ordering = ['is_active', 'sorting_order']

    def __str__(self):
        return self.name


class ValveConnectionToPipe(models.Model):
    name = models.CharField(max_length=100,
                            help_text=_("Символьное обозначение типа присоединения арматуры к трубе"),
                            verbose_name=_("Символьное обозначение типа присоединения арматуры к трубе"))
    code = models.CharField(max_length=50, unique=True,
                            verbose_name=_("Код типа присоединения арматуры к трубе"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _("Тип присоединения арматуры к трубе")
        verbose_name_plural = _("Типы присоединения арматуры к трубе")

    def __str__(self):
        return self.name


class ValveVariety(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа арматуры', verbose_name=_("Символьное обозначение типа арматуры"))
    actuator_gearbox_combinations = models.CharField(max_length=10, help_text='Символьное обозначение \
    подходящего типа привода и редуктора', verbose_name=_("Символьное обозначение \
    подходящего типа привода и редуктора"))
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа арматуры', verbose_name=_("Текстовое описание типа арматуры"))

    class Meta:
        ordering = ['text_description']
        verbose_name = _("Тип арматуры")
        verbose_name_plural = _("Типы арматуры")

    def __str__(self):
        return self.text_description


class ConstructionVariety(models.Model):
    name = models.CharField(max_length=100, help_text=_(
        "Название типа конструкции вида арматуры"),
                            verbose_name=_("Название типа конструкции"))
    valve_variety = models.ForeignKey(ValveVariety, related_name='construction_variety_valve_variety',
                                      on_delete=models.CASCADE,
                                      help_text=_('Тип конструкции вида арматуры'),
                                      verbose_name=_("Тип конструкции вида арматуры"))
    code = models.CharField(max_length=50, unique=True,
                            verbose_name=_("Код типа конструкции"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _("Название типа конструкции вида арматуры")
        verbose_name_plural = _("Названия типа конструкции вида арматуры")

    def __str__(self):
        return self.name


class PortQty(models.Model):
    name = models.CharField(max_length=100, help_text=_(
        "Количество портов арматуры"), verbose_name=_("Количество портов арматуры"))
    code = models.CharField(max_length=50, unique=True, help_text=_(
        "Код количества портов арматуры"),
                            verbose_name=_("Код количества портов арматуры"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _("Количество портов арматуры")
        verbose_name_plural = _("Количество портов арматуры")

    def __str__(self):
        return self.name


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
                                    help_text=_(
                                        'Бренд серии арматуры для шаблона тех.данных для серии. Здесь используем для поиска'),
                                    verbose_name=_("Бренд"))
    valve_variety = models.ForeignKey(ValveVariety, blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      related_name='valve_model_data_table_valve_variety',
                                      help_text=_(
                                          'Тип арматуры для шаблона тех.данных для серии, здесь используем для поиска'),
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
                                    help_text=_(
                                        'Бренд серии арматуры для шаблона Kvs для серии. Здесь используем для поиска'),
                                    verbose_name=_("Бренд"))
    valve_variety = models.ForeignKey(ValveVariety, blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      related_name='valve_data_kvs_valve_variety',
                                      help_text=_(
                                          'Тип арматуры для шаблона Kvs для серии, здесь используем для поиска'),
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


class ValveLineModelKvData(models.Model):
    valve_model_kv_data_table = models.ForeignKey(ValveModelKvDataTable,
                                                  related_name='valve_model_kv_data_table',
                                                  on_delete=models.CASCADE,
                                                  verbose_name=_('Шаблон моделей'),
                                                  help_text=_('Шаблон моделей арматуры'))
    valve_model_dn = models.ForeignKey(DnVariety, related_name='valve_model_kv_data_table_dn_data',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       verbose_name=_('Dn'),
                                       help_text=_('Dn арматуры, мм'))
    valve_model_pn = models.ForeignKey(PnVariety, related_name='valve_model_kv_data_table_pn_data',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       verbose_name=_('Pn'),
                                       help_text=_('Pn арматуры, бар'))
    valve_model_openinig_angle = models.DecimalField(max_digits=5, decimal_places=1, null=True, default=0,
                                                     verbose_name=_("Угол"),
                                                     help_text=_('Угол открытия арматуры, градусов °'))
    valve_model_kv = models.DecimalField(max_digits=8, decimal_places=1, null=True, default=0,
                                         verbose_name=_("Kv,м3/час"),
                                         help_text=_('Kv,м3/час, при открытии на угол градусов'))

    class Meta:
        verbose_name = _("Данные Kv серии арматуры")
        verbose_name_plural = _("Данные Kv серии арматуры")
        ordering = ['valve_model_kv_data_table', 'valve_model_pn', 'valve_model_dn']


class ValveLineModelData(models.Model):
    """Таблица с данными для шаблона моделей арматуры ValveModelDataTable, а он - для выбора в ValveLine"""
    name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Артикул'),
                            help_text=_('Символьное обозначение (артикул)\
         модели арматуры производителя'))

    valve_model_data_table = models.ForeignKey(ValveModelDataTable,
                                               related_name='model_data',
                                               blank=True,
                                               null=True,
                                               on_delete=models.CASCADE,
                                               verbose_name=_('Шаблон моделей'),
                                               help_text=_('Шаблон моделей арматуры'))
    valve_model_dn = models.ForeignKey(DnVariety, related_name='valve_line_model_dn_data',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       verbose_name=_('Dn'),
                                       help_text=_('Dn арматуры, мм'))
    valve_model_pn = models.ForeignKey(PnVariety, related_name='valve_line_model_pn_data',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       verbose_name=_('Pn'),
                                       help_text=_('Pn арматуры, бар'))
    valve_model_torque_to_open = models.DecimalField(max_digits=5, decimal_places=0, null=True, default=0,
                                                     verbose_name=_("Момент откр"),
                                                     help_text=_('Момент на открытие, Н'))
    valve_model_torque_to_close = models.DecimalField(max_digits=5, decimal_places=0, null=True, default=0,
                                                      verbose_name=_("Момент закр"),
                                                      help_text=_('Момент на открытие, Н'))
    valve_model_thrust_to_close = models.DecimalField(max_digits=8, decimal_places=0, null=True, default=0,
                                                      help_text=_('Усилие на закрытие, Н'),
                                                      verbose_name=_("Усилие закр"))
    valve_model_rotations_to_open = models.DecimalField(max_digits=5, decimal_places=1, null=True, default=0,
                                                        verbose_name=_('Обороты'),
                                                        help_text=_('Число оборотов на открытие'))
    valve_model_stem_size = models.ForeignKey(StemSize, related_name='valve_line_model_stem_size',
                                              blank=True,
                                              null=True,
                                              on_delete=models.SET_NULL,
                                              verbose_name=_('Шток'),
                                              help_text=_('Размер штока модели арматуры'))
    valve_model_stem_height = models.DecimalField(max_digits=6, decimal_places=1, null=True, default=0,
                                                  verbose_name=_('Высота штока'),
                                                  help_text=_('Высота штока, мм'))
    valve_model_construction_length = models.DecimalField(max_digits=6, decimal_places=1, null=True, default=0,
                                                          verbose_name=_('Строит.длина'),
                                                          help_text=_('Строительная длина, мм'))
    valve_model_mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                                        related_name='valve_line_model_mount_data',
                                                        verbose_name=_('Монт.площадка'),
                                                        help_text='Монтажная площадка модели арматуры')

    class Meta:
        verbose_name = _("Данные модели арматуры")
        verbose_name_plural = _("Данные моделей арматуры")
        ordering = ['valve_model_data_table', 'valve_model_pn', 'valve_model_dn']

    def __str__(self):
        if self.name is None and self.valve_model_dn is None:
            return "No data"
        return f"Данные для Dn={self.valve_model_dn.name} Pn={self.valve_model_pn.name}" if self.name == "" else self.name


class ValveLineBodyColor(models.Model):
    """Связь серии арматуры с цветами корпуса и типами исполнения"""
    valve_line = models.ForeignKey(
        'ValveLine',
        on_delete=models.CASCADE,
        related_name='valve_line_body_colors',
        verbose_name=_("Серия арматуры")
    )
    body_color = models.ForeignKey(
        BodyColor,
        on_delete=models.CASCADE,
        related_name='valve_line_body_color_usages',
        verbose_name=_("Цвет корпуса")
    )
    option_variety = models.ForeignKey(
        OptionVariety,
        on_delete=models.CASCADE,
        related_name='valve_line_body_color_option_variety',
        verbose_name=_("Стандарт или опция")
    )
    option_code_template = models.CharField(max_length=100, blank=True, null=True,
                                            help_text=_("Шаблон кодировки для опции"),
                                            verbose_name=_("Шаблон кодировки для опции"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_available = models.BooleanField(default=True, verbose_name=_("Доступно"))
    additional_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Дополнительная стоимость"),
        help_text=_("Дополнительная стоимость для этого цвета и типа исполнения")
    )
    lead_time_days = models.IntegerField(
        default=0,
        verbose_name=_("Срок изготовления (дни)"),
        help_text=_("Дополнительное время изготовления в днях")
    )
    notes = models.TextField(blank=True, verbose_name=_("Примечания"))

    class Meta:
        ordering = ['valve_line', 'option_variety__sorting_order', 'sorting_order']
        verbose_name = _("Цвет корпуса серии")
        verbose_name_plural = _("Цвета корпусов серий")
        unique_together = ['valve_line', 'body_color', 'option_variety']

    def __str__(self):
        return f"{self.valve_line} - {self.body_color} ({self.option_variety})"

    def clean(self):
        """Валидация связи цвета и типа исполнения"""
        super().clean()


class EAVAttribute(models.Model):
    """Атрибут EAV системы"""
    name = models.CharField(max_length=100, verbose_name=_("Название атрибута"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код атрибута"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', _('Строка')),
            ('integer', _('Целое число')),
            ('float', _('Десятичное число')),
            ('boolean', _('Да/Нет')),
        ],
        default='string',
        verbose_name=_("Тип данных")
    )
    unit = models.CharField(max_length=20, blank=True, verbose_name=_("Единица измерения"))

    class Meta:
        verbose_name = _("Атрибут")
        verbose_name_plural = _("Атрибуты")
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class EAVValue(models.Model):
    """Справочник значений для атрибутов"""
    attribute = models.ForeignKey(
        EAVAttribute,
        on_delete=models.CASCADE,
        related_name='possible_values',
        verbose_name=_("Атрибут")
    )
    value = models.CharField(max_length=200, verbose_name=_("Значение"))
    display_name = models.CharField(max_length=200, verbose_name=_("Отображаемое название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    order = models.IntegerField(default=0, verbose_name=_("Порядок"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        verbose_name = _("Значение атрибута")
        verbose_name_plural = _("Значения атрибутов")
        ordering = ['attribute', 'order', 'value']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.display_name}"


class ValveVarietyAttribute(models.Model):
    """Связь разновидности арматуры с допустимыми атрибутами"""
    valve_variety = models.ForeignKey(
        ValveVariety,
        on_delete=models.CASCADE,
        related_name='allowed_attributes',
        verbose_name=_("Разновидность арматуры")
    )
    attribute = models.ForeignKey(
        EAVAttribute,
        on_delete=models.CASCADE,
        related_name='valve_varieties',
        verbose_name=_("Атрибут")
    )
    is_required = models.BooleanField(default=False, verbose_name=_("Обязательный"))
    order = models.IntegerField(default=0, verbose_name=_("Порядок"))

    class Meta:
        verbose_name = _("Атрибут разновидности")
        verbose_name_plural = _("Атрибуты разновидностей")
        ordering = ['valve_variety', 'order']
        unique_together = ['valve_variety', 'attribute']

    def __str__(self):
        return f"{self.attribute}"

#
# class WeightDimensionParameter(models.Model):
#     """Параметр весо-габаритных характеристик"""
#     name = models.CharField(
#         max_length=100,
#         verbose_name=_("Название параметра"),
#         help_text=_("Название параметра ВГХ")
#     )
#     code = models.CharField(
#         max_length=50,
#         unique=True,
#         verbose_name=_("Код параметра"),
#         help_text=_("Уникальный код параметра")
#     )
#     sorting_order = models.IntegerField(
#         default=0,
#         verbose_name=_("Порядок сортировки")
#     )
#     valve_variety = models.ForeignKey(
#         ValveVariety,
#         blank=True,
#         null=True,
#         on_delete=models.SET_NULL,
#         related_name='weight_dimension_parameters',
#         verbose_name=_("Тип арматуры"),
#         help_text=_("Тип арматуры для отбора значений в выпадающий список")
#     )
#
#     class Meta:
#         verbose_name = _("Параметр ВГХ")
#         verbose_name_plural = _("Параметры ВГХ")
#         ordering = ['sorting_order', 'name']
#
#     def __str__(self):
#         return f"{self.name} ({self.code})"


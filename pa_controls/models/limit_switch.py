# pa_controls/models/limit_switch.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List, Optional, Tuple, Any, Dict, Union

import logging

from core.models import StructuredDataMixin
from core.models.mixins import TemplateGeneratorMixin
from electric_actuators.models import CableGlandHolesSet
from materials.models import MaterialGeneral, MaterialSpecified
# from pa_controls.models import PaControlMountingStandard
from producers.models import Brands, Producer

logger = logging.getLogger(__name__)

from params.models import IpOption
from params.exd_models import ExdOption


# ============================================================
# БЛОК КОНЦЕВЫХ ВЫКЛЮЧАТЕЛЕЙ (Limit Switch Box)
# ============================================================

class LimitSwitchSensorVariety(models.Model):
    """Тип сенсора концевого выключателя (механический, индуктивный, магнитный, пневматический)"""
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа сенсора БКВ")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа сенсора БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа сенсораа БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _("Тип сенсора БКВ")
        verbose_name_plural = _("Типы сенсоров БКВ")

    def __str__(self):
        return self.name

    @classmethod
    def get_choices(cls):
        """
        Возвращает список кортежей для использования в выпадающем списке
        Returns: [(id, name), ...] или [(0, "— Выберите —"), (id, name), ...]
        """
        choices = cls.objects.filter(is_active=True).order_by('sorting_order', 'name')
        return [(item.id, item.name) for item in choices]

    @classmethod
    def get_select_choices(cls, include_empty=True):
        """
        Возвращает список кортежей с пустым значением для selectbox
        Args:
            include_empty: добавить ли пустой вариант "-- Выберите --"
        Returns: [(0, "— Выберите —"), (id, name), ...] или [(id, name), ...]
        """
        choices = cls.get_choices()

        if include_empty:
            return [(0, "— Выберите —")] + choices

        return choices

    @classmethod
    def get_choice_by_id(cls, choice_id):
        """ Получить название по ID """
        if not choice_id:
            return None

        try:
            item = cls.objects.get(id=choice_id, is_active=True)
            return item.name
        except cls.DoesNotExist:
            return None


class LimitSwitchOutput(models.Model):
    """Электрическая схема и тип сигнала БКВ """
    SIGNAL_CHOICES = [
        ('DRY', _('Сухой контакт (Passive)')),
        ('PNP', _('PNP (Active)')),
        ('NPN', _('NPN (Active)')),
        ('NAMUR', _('NAMUR (Ex)')),
        ('NAMUR_S', _('NAMUR с функцией безопасности')),  # Для серий SN / S1N (безопасность)
        ('SS_2W', _('2-проводной бесконтактный (AC/DC)')),  # Для серии NBB...-Z
        ('ANALOG', _('Аналоговый выход (4-20мА)')),
        ('PNEUM', _('Пневматический')),
        ('ANALOG_DRY', _('Аналог (4-20мА) + Сухой контакт')),
        ('ANALOG_NAMUR', _('Аналог (4-20мА) + NAMUR (Ex)')),
    ]

    CONTACT_CHOICES = [
        ('NO', _('SPST (Нормально открытый)')),
        ('NC', _('SPST (Нормально замкнутый)')),
        ('SPDT', _('SPDT (Перекидной)')),
        ('DPST', _('DPST (2 линии Вкл/Выкл)')),
        ('DPDT', _('DPDT (2 перекидных)')),
        ('NONE', _('Нет (для аналоговых/пневмо)')),
        ('ANALOG_SPDT', _('1xАналог + 2xSPDT')),
        ('ANALOG_SPST', _('1xАналог + 2xSPST')),
    ]
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа выходного сигнала БКВ")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа выходного сигнала БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа выходного сигнала БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    contact_form = models.CharField(
        max_length=50, null=True, blank=True,
        choices=CONTACT_CHOICES, default='SPDT',
        verbose_name=_("Форма контактов")
    )
    signal_type = models.CharField(
        max_length=50, choices=SIGNAL_CHOICES, default='DRY', verbose_name=_("Тип сигнала")
    )
    wires_per_sensor = models.PositiveSmallIntegerField(
        default=2,
        verbose_name=_("Проводов на 1 датчик"),
        help_text=_("Сколько жил кабеля занимает один датчик в блоке")
    )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Тип выхода БКВ")
        verbose_name_plural = _("Типы выходов БКВ")
        ordering = ['sorting_order', 'name']

    def __str__(self):
        # if self.contact_form:
        #     return f"{self.name} ({self.contact_form})"
        return f"{self.name}"

    @property
    def signal_type_text(self) -> str:
        return self.get_signal_type_display()

    @property
    def contact_form_text(self) -> str:
        return self.get_contact_form_display()

    @property
    def output_type_text(self) -> str:
        """Возвращает человеко-читаемое значение типа выхода"""
        text = f'Тип контактов: {self.get_contact_form_display()}, Тип сигнала: {self.get_signal_type_display()}, проводов на 1 датчик: {self.wires_per_sensor}'
        return text

    # @property
    # def signal_type_display(self) -> str:
    #     """Возвращает человеко-читаемое значение сигнала"""
    #     return dict(self.SIGNAL_CHOICES).get(self.signal_type, self.signal_type)

    @classmethod
    def get_choices(cls):
        """Возвращает список кортежей для выпадающего списка"""
        choices = cls.objects.filter(is_active=True).order_by('sorting_order', 'name')
        return [(item.id, str(item)) for item in choices]

    @classmethod
    def get_select_choices(cls, include_empty=True, empty_label="— Выберите —"):
        """Возвращает список с пустым значением для selectbox"""
        choices = cls.get_choices()

        if include_empty:
            return [(0, empty_label)] + choices

        return choices

    @classmethod
    def get_choice_by_id(cls, choice_id):
        """Получить название по ID"""
        try:
            item = cls.objects.get(id=choice_id, is_active=True)
            return str(item)
        except cls.DoesNotExist:
            return None


class LimitSwitchBody(StructuredDataMixin, models.Model):
    """
    Корпус БКВ
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии БКВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии БКВ'))
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


class LimitSwitchModelLine(StructuredDataMixin, models.Model):
    """
    Серия БКВ
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии БКВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии БКВ'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия БКВ'))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='limit_switch_model_line_producer', blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель БКВ'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='limit_switch_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд БКВ'),
                              verbose_name=_("Бренд"))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Серия БКВ')
        verbose_name_plural = _('Серии БКВ')

    def __str__(self):
        return self.name


class SignalType(models.Model):
    """Тип сигнала (NAMUR, PNP, Сухой контакт, 4-20мА и т.д.)"""
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    code = models.CharField(max_length=50, verbose_name=_("Код"))
    is_ex = models.BooleanField(default=False, help_text=_(
        "Флаг определяет, требуется ли для данного сигнала расчет искробезопасных параметров и барьер"),
                                verbose_name="Взрывозащищенный (Ex)")
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Подробное описание физического принципа работы сигнала'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Тип сигнала"
        verbose_name_plural = "Типы сигналов"

    def __str__(self): return self.name


class ContactForm(models.Model):
    """Форма контактов (SPST, SPDT, DPDT)"""
    name = models.CharField(max_length=100,
                            help_text=_("Техническое наименование (например, 'Однополюсный перекидной')"),
                            verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True, help_text=_("Международное сокращение (SPST, SPDT, DPDT, DPST)"
                                                                    ), verbose_name=_("Код"))
    wires_required = models.PositiveSmallIntegerField(
        help_text=_("Минимальное количество жил кабеля для подключения одной единицы (напр. SPDT = 3 провода)"
                    ), verbose_name="Базовое кол-во проводов")
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Схематичное описание работы или примечания по монтажу'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _("Форма контактов")
        verbose_name_plural = _("Формы контактов")

    def __str__(self): return f'{self.name}/{self.code}'


class ContactState(models.Model):
    """Состояние контакта (НО, НЗ, Перекидной)"""
    name = models.CharField(max_length=100, help_text=_("Пользовательское описание (например, 'Нормально разомкнутый')"
                                                        ), verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True,
                            help_text=_("Технический код состояния: NO (разомкнут), NC (замкнут), CO (перекидной)"
                                        ), verbose_name=_("Код"))  # NO, NC, CHANGE_OVER
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_(
                                       "Описание состояния контакта в 'нормальном' (невозбужденном) положении датчика"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Состояние контакта"
        verbose_name_plural = "Состояния контактов"

    def __str__(self): return self.name


class SensorComponent(models.Model):
    """База данных конкретных моделей датчиков и трансмиттеров"""
    name = models.CharField(max_length=200,
        verbose_name=_("Название"),
        help_text=_('Текстовое название модели датчика'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели датчика"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели датчика'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    brand = models.ForeignKey(Brands, related_name='sensor_component_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд'),
                              verbose_name=_("Бренд датчика"))
    # Ссылки на созданные ранее справочники
    variety = models.ForeignKey(LimitSwitchSensorVariety, on_delete=models.PROTECT, verbose_name=_("Тип сенсора"))
    signal_type = models.ForeignKey(SignalType, on_delete=models.PROTECT, verbose_name=_("Тип сигнала"))
    contact_form = models.ForeignKey(ContactForm, on_delete=models.PROTECT, verbose_name=_("Форма контактов"))
    contact_state = models.ForeignKey(ContactState, on_delete=models.PROTECT, verbose_name=_("Состояние контакта"))

    # Электрические параметры строкой (как в паспорте)
    electrical_specs = models.CharField(
        max_length=255,
        verbose_name=_("Электрические характеристики"),
        help_text=_("Например: '8.2В / 25мА' или '250В (AC) / 1.0А' или '24В / 4-20мА'")
    )

    wires_count = models.PositiveSmallIntegerField(
        default=2,
        verbose_name=_("Кол-во проводов"),
        help_text=_("Фактическое количество жил для подключения этого датчика")
    )

    # Искробезопасные параметры (отдельные поля для расчетов)
    ui = models.FloatField(null=True, blank=True, verbose_name="Ui (В)")
    ii = models.FloatField(null=True, blank=True, verbose_name="Ii (мА)")
    pi = models.FloatField(null=True, blank=True, verbose_name="Pi (мВт)")
    ci = models.FloatField(null=True, blank=True, verbose_name="Ci (нФ)")
    li = models.FloatField(null=True, blank=True, verbose_name="Li (мкГн)")

    # Всё остальное (материалы, частота, гистерезис, SIL, МДС)
    extra_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Дополнительные параметры"),
        help_text=_("Специфические данные: материал, частота, SIL, МДС, погрешность и т.д.")
    )

    class Meta:
        verbose_name = _("Датчик (компонент)")
        verbose_name_plural = _("Датчики (компоненты)")

    def __str__(self):
        return f"{self.name}"

class LimitSwitchBox(TemplateGeneratorMixin, models.Model):
    """Модель блока концевых выключателей (каталог)
    points: int,
        1 точка - один датчик (обычно только на закрыто)
        2 точки - два датчика (на открыто и на закрыто) - самый распространенный вариант
        3 точки - три датчика (открыто, закрыто, промежуточное положение)
        4 точки - четыре датчика (два промежуточных положения + концевые)
    """
    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название БКВ'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(LimitSwitchModelLine, related_name='limit_switch_box_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия БКВ'),
                                   verbose_name=_("Серия"))
    body = models.ForeignKey(LimitSwitchBody, related_name='limit_switch_box_body', blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text=_('Корпус БКВ'),
                             verbose_name=_("Корпус"))
    # Характеристики
    sensor_variety = models.ForeignKey(
        LimitSwitchSensorVariety, on_delete=models.SET_NULL, null=True,
        help_text=_('Тип сенсора'),
        verbose_name=_("Тип сенсора")
    )
    # Добавляем Many-to-Many связь с датчиками
    sensor_components = models.ManyToManyField(
        SensorComponent,
        blank=True,
        verbose_name=_("Датчики"),
        help_text=_("Установленные датчики"),
        related_name='limit_switch_boxes'  # обратная связь от датчика к корпусам
    )
    output_type = models.ForeignKey(
        LimitSwitchOutput, on_delete=models.SET_NULL, null=True,
        related_name='limit_switch_box_sensor_variety',
        help_text=_('Тип выходного сигнала'),
        verbose_name=_("Выходной сигнал")
    )
    points = models.IntegerField(default=2,
                                 verbose_name=_("Количество датчиков"),
                                 help_text=_("Количество точек переключения (датчиков)")
                                 )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='limit_switch_box_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='limit_switch_boxes',
        help_text=_('Степень взрывозащиты (можно выбрать несколько вариантов)'),
        verbose_name=_("Взрывозащита")
    )

    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='limit_switch_box_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='limit_switch_box_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))

    # Дополнительные характеристики
    is_pneumatic = models.BooleanField(default=False, verbose_name=_("Пневматический"))
    has_namur_interface = models.BooleanField(default=False, verbose_name=_("NAMUR интерфейс"))
    has_visual_indicator = models.BooleanField(default=False, verbose_name=_("Визуальный индикатор"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Блок концевых выключателей")
        verbose_name_plural = _("Блоки концевых выключателей")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    def copy(self, suffix=" (Копия)", code_suffix="_copy"):
        """
        Создает копию текущего объекта

        Args:
            suffix: суффикс для name
            code_suffix: суффикс для code

        Returns:
            LimitSwitchBox: Скопированный объект
        """
        # Генерируем новые имена с суффиксом
        original_name = self.name or ""
        original_code = self.code or ""

        # Для name
        if suffix in original_name:
            base_name = original_name.replace(suffix, "")
            new_name = f"{base_name}{suffix}"
        else:
            new_name = f"{original_name}{suffix}"

        # Для code
        if original_code:
            if code_suffix in original_code:
                # Увеличиваем номер копии
                import re
                match = re.search(rf"{code_suffix}(\d+)$", original_code)
                if match:
                    num = int(match.group(1)) + 1
                    new_code = re.sub(rf"{code_suffix}\d+$", f"{code_suffix}{num}", original_code)
                else:
                    new_code = f"{original_code}{code_suffix}1"
            else:
                new_code = f"{original_code}{code_suffix}"
        else:
            new_code = None

        # Создаем копию
        copy = LimitSwitchBox(
            name=new_name,
            code=new_code,
            description=f"Копия: {self.description}" if self.description else "Копия",
            sorting_order=self.sorting_order + 100,
            is_active=self.is_active,
            model_line=self.model_line,
            body=self.body,
            sensor_variety=self.sensor_variety,
            output_type=self.output_type,
            points=self.points,
            ip=self.ip,
            work_temp_min=self.work_temp_min,
            work_temp_max=self.work_temp_max,
            body_material=self.body_material,
            body_material_specified=self.body_material_specified,
            is_pneumatic=self.is_pneumatic,
            has_namur_interface=self.has_namur_interface,
            has_visual_indicator=self.has_visual_indicator,
            extra_params=self.extra_params if self.extra_params else {}
        )
        copy.save()

        # Копируем ManyToMany поле exd
        copy.exd.set(self.exd.all())

        return copy

    @property
    def exd_display(self):
        """Возвращает отображаемую маркировку взрывозащиты"""
        if not self.exd.exists():
            return "Нет"
        return ", ".join([req.name for req in self.exd.all()])

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Исп. {exd} Т.окр. {work_temp_min}..{work_temp_max} °С"
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Исп. {exd} Т.окр. {work_temp_min}..{work_temp_max} °С, {output_type_name}, Материал корпуса: {body_material_specified}, вес {weight}кг., Отверстия под КВ:{cable_glands_holes}, Монтаж:{mounting}"
        return default_description_template

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{sensor_variety}': 'sensor_variety',
            '{contact_form}': 'output_type__contact_form_text',
            '{signal_type}': 'output_type__signal_type_text',
            '{wires_per_sensor}': "output_type__wires_per_sensor",
            '{output_type_name}': 'output_type__output_type_text',
            '{points}': 'points',
            '{body_material}': 'body_material',
            '{body_material_specified}': 'body_material_specified',
            '{weight}': 'body__weight',
            '{cable_glands_holes}': 'body__cable_glands_holes_list_text',
            '{mounting}': 'body__mounting_list_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{exd}': 'exd_display',
            '{ip}': 'ip',
        }

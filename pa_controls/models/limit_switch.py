# pa_controls/models/limit_switch.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List, Optional, Tuple, Any, Dict, Union

import logging

from core.models import StructuredDataMixin
from core.models.mixins import TemplateFillerMixin , GetChoicesMixin , \
    TemplateMixin
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

# class LimitSwitchSensorVariety(TemplateFillerMixin,GetChoicesMixin, models.Model):
class LimitSwitchSensorVariety(TemplateFillerMixin, GetChoicesMixin, models.Model):
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
    name_template = models.TextField(blank=True , null=True ,
                                     verbose_name=_("Шаблон названия") ,
                                     help_text=_('Шаблон для текстового названия сенсора'))
    description_template = models.TextField(blank=True , null=True ,
                                            verbose_name=_("Шаблон описания") ,
                                            help_text=_('Шаблон для описания сенсора'))
    class Meta:
        verbose_name = _("Тип сенсора БКВ")
        verbose_name_plural = _("Типы сенсоров БКВ")

    def __str__(self):
        return self.name

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


class SensorComponent(TemplateMixin, GetChoicesMixin, models.Model):
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
    ui = models.FloatField(null=True, blank=True, verbose_name=_("Ui (В)"), help_text=_('Максимальное входное напряжение Ui (В): Это предел напряжения, который может быть подан на устройство без нарушения его искробезопасности. Если стоит 0, значит, прибор не сертифицирован как «искробезопасный аппарат».'))
    ii = models.FloatField(null=True, blank=True, verbose_name=_("Ii (мА)"), help_text=_('Максимальный входной ток Ii (мА): Максимальный ток, который может выдержать внутренняя схема датчика при сохранении безопасности.'))
    pi = models.FloatField(null=True, blank=True, verbose_name=_("Pi (мВт)"), help_text=_('Максимальная входная мощность Pi (мВт): Лимит мощности, которую устройство может рассеивать, чтобы не вызвать воспламенение окружающей среды.'))
    ci = models.FloatField(null=True, blank=True, verbose_name=_("Ci (нФ)"), help_text=_('Внутренняя емкость Ci (нФ): Суммарная емкость всех компонентов внутри датчика. При проектировании систем автоматики её учитывают вместе с емкостью кабеля, чтобы избежать накопления энергии.'))
    li = models.FloatField(null=True, blank=True, verbose_name=_("Li (мкГн)"), help_text=_('Внутренняя индуктивность Li (мкГн): Суммарная индуктивность датчика. Её учитывают для предотвращения искрового разряда при размыкании цепи.'))
    # Ui(В): {ui}, Ii (мА):{ii}, Pi (мВт):{pi}, Li (мкГн):{li}
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

    @property
    def get_exi_params(self):
        exi_template="Максимальное входное напряжение Ui(В): {ui}, Максимальный входной ток Ii(мА): {ii}, Максимальная входная мощность Pi(мВт): {pi}, Внутренняя емкость Ci (нФ): {ci}, Внутренняя индуктивность Li(мкГн): {li}"
        # Временно сохраняем оригинальные значения
        # и создаем словарь только с нужными полями

        # Получаем значения и преобразуем в float (None -> 0)
        def safe_float(val):
            try:
                return float(val) if val not in (None, '') else 0.0
            except (ValueError, TypeError):
                return 0.0

        values = [safe_float(self._get_value(field)) for field in ['ui', 'ii', 'pi', 'ci', 'li']]

        if any(v != 0 for v in values):
            # Используем существующий метод
            return self._fill_template(exi_template,self._get_data_dict())
        else:
            return "Датчик не является искробезопасным электрооборудованием и не требует использования барьеров искрозащиты"

    @property
    def get_brand_name(self):
        print(f'get_brand_name self.brand.name {self.brand.name }')
        return self.brand.name if self.brand else "OEM"

    def _get_data_dict(self) -> Dict[str , str] :
        """
        Словарь соответствий плейсхолдеров и путей к атрибутам для SensorComponent
        """
        return {
            # Основные поля
            '{model_code}' : 'code' ,
            '{name}' : 'name' ,
            '{brand}' : 'get_brand_name',
            # Тип сенсора (sensor_variety)
            '{sensor_variety}' : 'variety__name' ,
            # Тип сигнала
            '{signal_type}' : 'signal_type__name' ,
            # Форма контактов
            '{contact_form}' : 'contact_form__name' ,
            '{contact_form_code}': 'contact_form__code',
            # Состояние контакта
            '{contact_state}' : 'contact_state__name' ,
            # Электрические параметры
            '{electrical_specs}' : 'electrical_specs' ,
            '{wires_count}' : 'wires_count' ,
            # Искробезопасные параметры
            '{ui}' : 'ui' ,
            '{ii}' : 'ii' ,
            '{pi}' : 'pi' ,
            '{ci}' : 'ci' ,
            '{li}' : 'li' ,
            '{exi_params}' : 'get_exi_params',
            '{extra_params}': 'get_extra_params',
            # JSON параметры (через .)
            # '{material}' : 'extra_params.material' ,
            # '{frequency}' : 'extra_params.frequency' ,
            # '{hysteresis}' : 'extra_params.hysteresis' ,
            # '{sil}' : 'extra_params.sil' ,
            # '{mds}' : 'extra_params.mds' ,
            # '{accuracy}' : 'extra_params.accuracy' ,
            # '{temperature_drift}' : 'extra_params.temperature_drift' ,
            # '{response_time}' : 'extra_params.response_time' ,
            # '{certification}' : 'extra_params.certification' ,
        }
    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.variety.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.variety.description_template or None

    def _get_default_name_template(self) -> str :
        """Шаблон названия по умолчанию"""
        return self.variety.name_template if self.variety else None

    def _get_default_description_template(self) -> str :
        """Шаблон описания по умолчанию"""
        # Искробезопасность: Ui={ui}В Ii={ii}мА Pi={pi}мВт Ci={ci}нФ Li={li}мкГн. Материал: {material}, частота: {frequency}, SIL: {sil}"
        return self.variety.description_template if self.variety else None

    def save(self, *args, **kwargs):
        # skip_auto_generate = kwargs.pop('skip_auto_generate', False)
        print(f'save from SenSorComponent')
        self.update_description()
        super().save(skip_auto_generate=True, *args, **kwargs)

class LimitSwitchBox(TemplateMixin, models.Model):
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
        # Копируем ManyToMany поле sensor_components
        copy.exd.set(self.sensor_components.all())
        return copy

    # def save(self , *args , **kwargs) :
    #     print(f"[DEBUG] ========== SAVE CALLED ==========")
    #     print(f"[DEBUG] self.name до генерации: {self.name}")
    #     print(f"[DEBUG] self.description до генерации: {self.description}")
    #
    #     # Генерируем название и описание
    #     if self.model_line :
    #         if self.model_line.name_template :
    #             new_name = self.generated_model_name_description('name')
    #             print(f"[DEBUG] сгенерированное name: {new_name}")
    #             if new_name :
    #                 self.name = new_name
    #
    #         if self.model_line.description_template :
    #             new_description = self.generated_model_name_description('description')
    #             print(f"[DEBUG] сгенерированное description: {new_description}")
    #             if new_description :
    #                 self.description = new_description
    #
    #     print(f"[DEBUG] self.name после генерации: {self.name}")
    #     print(f"[DEBUG] ========== SAVE FINISHED ==========")
    #     super().save(*args , **kwargs)
    @property
    def exd_display(self):
        """Возвращает отображаемую маркировку взрывозащиты"""
        if not self.exd.exists():
            return "Нет"

        return ", ".join([req.name for req in self.exd.all()])

    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand};  {points} датчика, тип датчика: {sensor_variety}; {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Датчик: {sensors}, Отверстия под КВ:{cable_glands_holes}, вес {weight} кг."
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Отверстия под КВ:{cable_glands_holes}, Монтаж:{mounting}, вес {weight}кг. Датчики: {sensors_description}"
        return default_description_template

    @property
    def get_sensors_description_list(self) -> str:
        """
        Возвращает  список поля description датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.sensor_components.all()
        if not sensor_components:
            return ""

        names = [item.description for item in sensor_components]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]}; + {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" + {names[-1]}"
    @property
    def get_sensors_names_list(self) -> str :
        """
        Возвращает текстовый список датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.sensor_components.all()
        if not sensor_components :
            return ""

        names = [item.generate_name() for item in sensor_components]

        if len(names) == 1 :
            return names[0]
        elif len(names) == 2 :
            return f"{names[0]}; + {names[1]}"
        else :
            return ", ".join(names[:-1]) + f" + {names[-1]}"

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{sensor_variety}': 'sensor_variety',
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
            # M2M поле - вызов метода get_sensors_list с подшаблоном
            # В подшаблоне можно использовать поля из SensorComponent (name, brand, signal_type, electrical_specs и т.д.)
            '{sensors}' : 'get_sensors_names_list' ,
            '{sensors_description}': 'get_sensors_description_list',
        }

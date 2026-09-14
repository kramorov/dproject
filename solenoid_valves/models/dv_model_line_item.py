# solenoid_valves/models/dv_model_line_item.py

from django.db import models
import math
from django.utils.translation import gettext_lazy as _

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.mixins import TemplateMixin, CopyMixin
from core.models.catalog_serializer import CatalogSerializerMixin
# TemplateGeneratorMixin удалён 2026-09-01 — DirectionValve использует единый TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin

from .dv_model_line import DirectionalValveModelLine
from .dv_body import DirectionValveBody
from .sv_options import ValveFunction, ValveActuationVariety, ManualOverride
from .dv_item_fields import DV_ITEM_TEMPLATE_FIELDS
from materials.models import MaterialGeneral, MaterialSpecified
from params.models import PowerSupplies, PneumaticConnection, ThreadSize
from producers.models import Brands, Producer
from electric_actuators.models import CableGlandHolesSet
from sku.models import SKUMixin
class DirectionValve(CatalogSerializerMixin,
                     ImageGalleryMixin,
                     TechDocMixin,
                     SKUMixin, CopyMixin, TemplateMixin,
                     SmartCatalogMixin, EquipmentTypeMixin, models.Model):
    """
    Распределительный клапан (конкретный артикул каталога).

    Определяет финальный Part Number и цену. Связан с DirectionalValveModelLine
    (серия/DNA клапана) и DirectionValveBody (корпус).

    Наследует:
      - SmartCatalogMixin — фильтрация, поиск, exact/compatible split
      - CatalogSerializerMixin — структурированная сериализация (to_dict/to_values_dict)
      - ImageGalleryMixin — галерея изображений
      - TechDocMixin — техническая документация
      - TemplateMixin — шаблоны названий/описаний (единый контракт)
      - SKUMixin — учётная номенклатура
      - CopyMixin — копирование в админке
      - EquipmentTypeMixin — тип оборудования

    Основные поля:
      - function: ValveFunction (3/2, 5/2, 5/3)
      - actuation: ValveActuationVariety (моно/бистабильный)
      - manual_override: ManualOverride (ручной дублёр)
      - body: DirectionValveBody (корпус, вес, KB, пневмоприсоединения)
      - kv, dn: пропускная способность
      - pressure_min/max, work_temp_min/max, medium_density_max: рабочие параметры
      - power_supply, power_consumption_*: электрические характеристики
      - body_material, sealing, solenoid_body_material: материалы
      - ip, exd: защита
      - pneumatic_connection, pneumatic_connection_thread, cable_glands_holes: присоединения
    """

    # ── Реестр полей (единый источник правды) — dv_item_fields.py ──
    TEMPLATE_FIELDS = DV_ITEM_TEMPLATE_FIELDS

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'function', 'actuation', 'construction',
        'operation', 'manual_override', 'working_medium', 'kv', 'dn',
        'pressure_min', 'pressure_max', 'pressure_range',
        'body_material', 'body_material_specified', 'sealing_material_specified',
        'solenoid_body_material', 'solenoid_body_material_specified', 'weight',
        'pneumatic_connection', 'pneumatic_connection_thread', 'cable_glands_holes',
        'power_supply', 'power_consumption_start', 'power_consumption_hot',
        'power_consumption_hold', 'solenoid_insulation_class', 'ip', 'exd',
        'temperature_range', 'medium_density_max', 'work_temp_min', 'work_temp_max',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'function',
        'actuation', 'construction', 'operation', 'working_medium',
        'solenoid_insulation_class', 'manual_override', 'kv', 'dn', 'ip', 'exd',
        'power_supply', 'power_consumption_start', 'power_consumption_hot',
        'power_consumption_hold', 'body_material', 'body_material_specified',
        'sealing_material_specified', 'solenoid_body_material',
        'solenoid_body_material_specified', 'pneumatic_connection',
        'pneumatic_connection_thread', 'cable_glands_holes',
        'pressure_min', 'pressure_max', 'medium_density_max', 'weight',
        'work_temp_min', 'work_temp_max', 'temperature_range', 'pressure_range',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'function', 'actuation', 'construction',
    #     'operation', 'manual_override', 'working_medium', 'kv', 'dn',
    #     'pressure_min', 'pressure_max', 'pressure_range',
    #     'body_material', 'body_material_specified', 'sealing_material_specified',
    #     'solenoid_body_material', 'solenoid_body_material_specified', 'weight',
    #     'pneumatic_connection', 'pneumatic_connection_thread', 'cable_glands_holes',
    #     'power_supply', 'power_consumption_start', 'power_consumption_hot',
    #     'power_consumption_hold', 'solenoid_insulation_class', 'ip', 'exd',
    #     'temperature_range', 'medium_density_max',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'flow': 'Пропускная способность',
    #     'pressure': 'Давление',
    #     'body': 'Корпус и материалы',
    #     'connections': 'Присоединения',
    #     'electric': 'Электрические параметры',
    #     'protection': 'Защита',
    #     'conditions': 'Условия эксплуатации',
    # }

    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название клапана'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности клапана'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    model_line = models.ForeignKey(DirectionalValveModelLine, related_name='direction_valve_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия клапана'),
                                   verbose_name=_("Серия"))
    producer = models.ForeignKey(Producer, related_name='direction_valve_producer', blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель клапана'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='direction_valve_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд клапанов'),
                              verbose_name=_("Бренд"))

    function = models.ForeignKey(ValveFunction,
                                 related_name='direction_valve_function',
                                 blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Схема (Функция)'),
                                 verbose_name=_("Схема (Функция) клапана"))
    ip = models.ForeignKey('params.IpOption', blank=True, null=True, default=65,
                           on_delete=models.SET_NULL, related_name='direction_valve_ip', verbose_name=_("IP"),
                           help_text=_('Степень IP для модели клапана'))
    exd = models.ForeignKey('params.ExdOption', blank=True, null=True,
                            related_name='direction_valve_exd',
                            on_delete=models.SET_NULL, verbose_name=_("Exd"),
                            help_text=_('Степень взрывозащиты для модели клапана'))
    actuation = models.ForeignKey(ValveActuationVariety,
                                  related_name='direction_valve_actuation',
                                  blank=True,
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  help_text=_('Управление'),
                                  verbose_name=_("Вариант управления"))
    manual_override = models.ForeignKey(ManualOverride,
                                        related_name='direction_valve_manual_override',
                                        blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Ручной дублер'),
                                        verbose_name=_("Ручной дублер"))

    body = \
        models.ForeignKey(DirectionValveBody, blank=True, null=True,
                          related_name='direction_valve_body',
                          on_delete=models.SET_NULL,
                          help_text=_('Корпус'),
                          verbose_name=_("Корпус модели клапана"))

    kv = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                             null=True, help_text=_('Kv, м3/ч'),
                             verbose_name=_("Kv, м3/ч"))
    dn = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                             null=True, help_text=_('Dn'),
                             verbose_name=_("Диаметр, мм"))
    power_supply = models.ForeignKey(PowerSupplies,
                                     related_name='direction_valve_power_supply',
                                     blank=True,
                                     null=True,
                                     on_delete=models.SET_NULL,
                                     help_text=_('Напряжение'),
                                     verbose_name=_("Напряжение питания"))
    power_consumption_start = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                  null=True, help_text=_('Мощность хол, Вт'),
                                                  verbose_name=_("Мощность пусковая, Вт"))
    power_consumption_hot = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                null=True, help_text=_('Мощность ном, Вт'),
                                                verbose_name=_("Мощность номинальная, Вт"))
    power_consumption_hold = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                 null=True, help_text=_('Мощность удерж, Вт'),
                                                 verbose_name=_("Мощность удержания, Вт"))
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    medium_density_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                             null=True, help_text=_('Вязкость среды, сСт'),
                                             verbose_name=_("Вязкость среды, сСт (мм2/с)"))
    pressure_min = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=0,
                                       help_text=_('Минимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.мин, бар'))

    pressure_max = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=40,
                                       help_text=_('Максимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.макс, бар'))
    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='direction_valve_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='direction_valve_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))
    sealing_material_specified = models.ForeignKey(MaterialSpecified,
                                                   related_name='direction_valve_sealing_material_specified',
                                                   blank=True,
                                                   null=True,
                                                   on_delete=models.SET_NULL,
                                                   help_text=_('Уплотнение'),
                                                   verbose_name=_('Материал уплотнения'))

    solenoid_body_material = models.ForeignKey(MaterialGeneral, related_name='direction_valve_solenoid_body_material',
                                               blank=True,
                                               null=True,
                                               on_delete=models.SET_NULL,
                                               help_text=_('Тип материала соленоида'),
                                               verbose_name=_('Тип материала соленоида'))
    solenoid_body_material_specified = models.ForeignKey(MaterialGeneral,
                                                         related_name='direction_valve_solenoid_body_material_specified',
                                                         blank=True,
                                                         null=True,
                                                         on_delete=models.SET_NULL,
                                                         help_text=_('Материал соленоида'),
                                                         verbose_name=_('Материал соленоида'))

    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                 null=True, help_text=_('Вес'),
                                 verbose_name=_("Вес, кг"))
    pneumatic_connection_thread = models.ForeignKey(ThreadSize, on_delete=models.SET_NULL, null=True, blank=True,
                                                    related_name='direction_valve_body_thread',
                                                    verbose_name=_("Пневмовыход"),
                                                    help_text=_('Резьба выходного отверстия для пневмоподключения'))
    pneumatic_connection = models.ForeignKey(
        PneumaticConnection,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='direction_valve_pneumatic_connection',
        verbose_name=_("Пневмоприсоединение"),
        help_text=_('Тип пневмоприсоединений'))
    cable_glands_holes = \
        models.ForeignKey(CableGlandHolesSet, null=True, blank=True,
                          related_name='direction_valve_cable_glands_holes',
                          on_delete=models.SET_NULL, verbose_name=_("Отверстия КВ"),
                           help_text=_('Отверстия под кабельные вводы'))

    def save(self, *args, **kwargs):
        """Сохраняет модель и синхронизирует номенклатуру (SKU)."""
        super().save(*args, **kwargs)
        self.sync_sku()

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Распределительный клапан')
        verbose_name_plural = _('Распределительные клапаны')

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand if self.model_line else None

    @property
    def operation(self):
        """Принцип действия клапана"""
        return str(self.model_line.operation) if self.model_line else ''

    @property
    def construction(self):
        """Тип конструкции клапана"""
        return str(self.model_line.construction) if self.model_line else ''

    @property
    def solenoid_insulation_class(self):
        """Класс изоляции соленоида"""
        return str(self.model_line.solenoid_insulation_class) if self.model_line else ''

    @property
    def working_medium(self):
        """Рабочая среда"""
        return str(self.model_line.working_medium) if self.model_line else ''

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон давлений"""
        return f'{self.pressure_min}..{self.pressure_max}'

    def _get_default_name_template(self) -> str:
        default_name_template = "{model_code} Пневмораспределитель {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; корпус: {body_material};  катушка: {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; P {pressure_range} бар; T {temperature_range}°С;  {exd}; {ip}; {power_supply};"
        return default_name_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Пневмораспределитель {brand} {operation} {construction} функция {function}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_range} бар; Темп.окр.среды {temperature_range}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного/ном/удерж: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, Вт; Ручной дублер: {manual_override}; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); Класс изоляции соленоида: {solenoid_insulation_class}; макс 5 циклов/сек; вес {weight}"
        return default_description_template

    def _get_title_template_source(self):
        """Переопределить в модели: вернуть шаблон заголовка или None."""
        title_template = "{model_code} {function}; {temperature_range}°С; {exd}; {ip}; {power_supply}; {operation}; {construction}"
        return title_template

    def _get_name_template_source(self):
        """Шаблон названия из model_line (единый контракт, 2026-09-01)."""
        if not self.model_line:
            return None
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Шаблон описания из model_line (единый контракт, 2026-09-01)."""
        if not self.model_line:
            return None
        return self.model_line.description_template or None

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        return {
            'id': self.model_line.id,
            'name': self.model_line.name,
            'code': getattr(self.model_line, 'code', '') or '',
            'description': self.model_line.description or '',
            'construction': self.model_line.construction.name if self.model_line.construction else None,
            'operation': self.model_line.operation.name if self.model_line.operation else None,
            'brand': {
                'id': self.model_line.brand.id,
                'name': self.model_line.brand.name,
            } if self.model_line.brand else None,
        }

    def __str__(self):
        return self.name or ''

    def calculate_flow_rate(self, kv, p1_bar, p2_bar=None, medium='air', temp_c=20):
        """
        Расчет объемного расхода Q через коэффициент Kv.

        :param kv: Коэффициент пропускной способности (м3/ч)
        :param p1_bar: Давление на входе (абсолютное, бар)
        :param p2_bar: Давление на выходе (абсолютное, бар).
                       Если None, берем стандартный перепад для пневматики (p1-1)
        :param medium: 'air' (воздух) или 'water' (вода)
        :param temp_c: Температура среды (°C)
        :return: Расход Q (л/мин для воздуха, м3/ч для воды)
        Пример использования для воздуха (6 бар на входе, 5 на выходе):
            print(calculate_flow_rate(kv=0.5, p1_bar=6, medium='air'))
            Давление: В расчетах всегда используйте абсолютное давление (манометрическое + 1 бар), иначе при 0 бар на выходе (выхлоп в атмосферу) формула выдаст ошибку или 0.
            Для воздуха: Результат обычно выдается в Nl/min (нормальные литры в минуту). Именно это значение пишут в каталогах рядом с
            .
            Для воды: Результат обычно в м³/ч. Если нужны л/мин, просто умножьте на 16.67.
        """
        # Переводим в абсолютное давление (приблизительно +1 бар к манометрическому)
        # Если на входе 6 бар по манометру, то p1_abs = 7
        p1 = p1_bar + 1.013

        if p2_bar is None:
            p2 = p1 - 1.0  # Стандартный перепад в 1 бар для тестов
        else:
            p2 = p2_bar + 1.013

        delta_p = p1 - p2
        if delta_p <= 0:
            return 0

        if medium == 'water':
            # Формула для воды: Q = Kv * sqrt(delta_p)
            # Результат в м3/ч
            return kv * math.sqrt(delta_p)

        elif medium == 'air':
            # Упрощенная инженерная формула для воздуха (нормальные л/мин)
            # T_abs = Температура в Кельвинах
            t_abs = temp_c + 273.15

            # Проверка на критический перепад (p2 < 0.528 * p1)
            # Если перепад большой, расход "запирается" на скорости звука
            if p2 < 0.528 * p1:
                # Критическое течение
                q_nm3h = 243 * kv * p1 * math.sqrt(1 / t_abs)
            else:
                # Докритическое течение
                q_nm3h = 484 * kv * math.sqrt(delta_p * p2 / t_abs)

            # Перевод из м3/ч в л/мин: (Q * 1000) / 60
            return (q_nm3h * 1000) / 60
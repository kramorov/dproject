# solenoid_valves/models.py

from django.db import models
import math
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.mixins import TemplateGeneratorMixin, CatalogDictMixin, TemplateMixin, CopyMixin

from .dv_model_line import DirectionalValveModelLine
from .dv_body import DirectionValveBody
from .sv_options import ValveFunction, ValveActuationVariety, ManualOverride
from materials.models import MaterialGeneral, MaterialSpecified, WorkingMedium
from params.models import ThreadSize, ThreadInnerOuter, SealingClass, PowerSupplies, PneumaticConnection
from producers.models import Brands, Producer
from electric_actuators.models import CableGlandHolesSet
from params.exd_models import ExdOption
from params.models import IpOption
from sku.models import SKUMixin
class DirectionValve(CatalogDictMixin,
                     ImageGalleryMixin,
                     TechDocMixin,
                     TemplateMixin,
                     SKUMixin, CopyMixin, TemplateGeneratorMixin, models.Model):
    '''
    DirectionValve (Характеристики конкретного артикула)  Это то, что определяет финальный «Part Number» и цену.
        function - ValveFunction (3/2, 5/2, 5/3).
        actuation - ValveActuationVariety (Моно / Бистабильный).
        manual_override - ManualOverride (Тип ручного дублера).
        pneumatic_connection - ThreadSize (Резьбы: 1/8", 1/4", 1/2", NAMUR).
        DN (Проходное сечение, мм).
        kv Kv (м³/ч) и FlowRate (л/мин) — они меняются в зависимости от размера портов.
        pressure_min,pressure_max (Важно: у 3/2 и 5/2 в одной серии может быть разный порог срабатывания пилота).
        work_temp_min, work_temp_maxTemperatureRange: (Напр. исполнение для -60°C часто идет как отдельный артикул с особыми уплотнениями).
        power_supply Voltage (12V, 24V, 220V).
        power_consumption_start, power_consumption_hot PowerConsumption (Пусковая/рабочая мощность).
        body - корпус (вес, КВ, пневмоприсоединения), туда же привяжется чертеж.
        Что я бы уточнил (Советы):
        Уплотнения: Если в одной серии можно заказать клапан либо с NBR (-20°C), либо с Viton (+120°C), то поле MaterialSeals должно быть и в ModelLine (как список доступных), и в SolenoidValve (как конкретный выбор).
        Kv и л/мин: В Django-модели SolenoidValve лучше хранить Kv как числовое поле (для расчетов), а л/мин можно сделать property, который вычисляется автоматически по нашей функции.
        Порты NAMUR: В соленоидных клапанах часто важно, крепится он «на трубах» или «на приводе» (NAMUR стандарт). Стоит добавить булево поле is_namur.

    '''

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

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Распределительный клапан')
        verbose_name_plural = _('Распределительные клапаны')

    @property
    def operation(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.operation}'

    @property
    def construction(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.construction}'

    @property
    def solenoid_insulation_class(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.solenoid_insulation_class}'

    @property
    def working_medium(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.working_medium}'

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.pressure_min}..{self.pressure_max}'

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Пневмораспределитель {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; корпус: {body_material};  катушка: {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; P {pressure_range} бар; T {temperature_range}°С;  {exd}; {ip}; {power_supply};"
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Пневмораспределитель {brand} {operation} {construction} функция {function}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_range} бар; Темп.окр.среды {temperature_range}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного/ном/удерж: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, Вт; Ручной дублер: {manual_override}; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); Класс изоляции соленоида: {solenoid_insulation_class}; макс 5 циклов/сек; вес {weight}"
        return default_description_template

    # Замена переменных
    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{function}': 'function',
            '{operation}': 'operation',
            '{actuation}': 'actuation',
            '{construction}': 'construction',
            '{solenoid_insulation_class}': 'solenoid_insulation_class',
            '{pneumatic_connection}': 'pneumatic_connection',
            '{pneumatic_connection_thread}': 'pneumatic_connection_thread',
            '{kv}': 'kv',
            '{body_material}': 'body_material',
            '{body_material_specified}': 'body_material_specified',
            '{solenoid_body_material}': 'solenoid_body_material',
            '{solenoid_body_material_specified}': 'solenoid_body_material_specified',
            '{sealing_material_specified}': 'sealing_material_specified',
            '{pressure_min}': 'pressure_min',
            '{pressure_max}': 'pressure_max',
            '{dn}': 'dn',
            '{power_supply}': 'power_supply',
            '{power_consumption_start}': 'power_consumption_start',
            '{power_consumption_hot}': 'power_consumption_hot',
            '{power_consumption_hold}': 'power_consumption_hold',
            '{medium_density_max}': 'medium_density_max',
            '{working_medium}': 'working_medium',
            '{manual_override}': 'manual_override',
            '{temperature_range}': 'temperature_range_display',
            '{pressure_range}': 'pressure_range_display',
            '{weight}': 'body__weight',
            '{cable_glands_holes}': 'cable_glands_holes',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{exd}': 'exd',
            '{ip}': 'ip',
        }

    # def generated_model_name_description(self , name_or_description) :
    #     """Сгенерировать название фитинга по шаблону из model_line"""
    #     if not self.model_line :
    #         return self.name or ""
    #     if name_or_description == 'name' :
    #         template = self.model_line.name_template
    #         if not template :
    #             print('Ошибка при формировании названия фитинга - в model_line нет шаблона')
    #             return self.name or ""
    #     else :
    #         template = self.model_line.description_template
    #         if not template :
    #             print('Ошибка при формировании описания фитинга - в model_line нет шаблона')
    #             return self.description or ""
    #     '''
    #         {model_code} Пневмораспределитель {operation} функция {function}; Тип действия: {operation}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_min}-{pressure_max} бар; Темп.окр.среды {work_temp_min}..{work_temp_max}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного {power_consumption_start}, Вт; Мощность ном. {power_consumption_hot}, Вт; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); вес {weight}
    #         '''
    #
    #     replacements = {
    #         '{model_code}' : self._get_value('code') ,
    #         '{function}': self._get_value('function'),
    #         '{operation}': self._get_value('operation'),
    #         '{actuation}': self._get_value('actuation'),
    #         '{construction}': self._get_value('construction'),
    #         '{solenoid_insulation_class}': self._get_value('solenoid_insulation_class'),
    #         '{pneumatic_connection}': self._get_value('pneumatic_connection'),
    #         '{pneumatic_connection_thread}': self._get_value('pneumatic_connection_thread'),
    #         '{kv}': self._get_value('kv'),
    #         '{body_material}': self._get_value('body_material'),
    #         '{body_material_specified}': self._get_value('body_material_specified'),
    #         '{solenoid_body_material}': self._get_value('solenoid_body_material'),
    #         '{solenoid_body_material_specified}': self._get_value('solenoid_body_material_specified'),
    #         '{sealing_material_specified}': self._get_value('sealing_material_specified'),
    #         '{pressure_min}': self._get_value('pressure_min'),
    #         '{pressure_max}': self._get_value('pressure_min'),
    #         '{work_temp_min}': self._get_value('work_temp_min'),
    #         '{work_temp_max}': self._get_value('work_temp_max'),
    #         '{cable_glands_holes}': self._get_value('cable_glands_holes'),
    #         '{exd}': self._get_value('exd'),
    #         '{ip}': self._get_value('ip'),
    #         '{dn}': self._get_value('dn'),
    #         '{power_supply}': self._get_value('power_supply'),
    #         '{power_consumption_start}': self._get_value('power_consumption_start'),
    #         '{power_consumption_hot}': self._get_value('power_consumption_hot'),
    #         '{power_consumption_hold}' : self._get_value('power_consumption_hold') ,
    #         '{medium_density_max}': self._get_value('medium_density_max'),
    #         '{working_medium}': self._get_value('working_medium'),
    #         '{manual_override}': self._get_value('manual_override'),
    #         '{weight}': self._get_value('weight'),
    #         '{temperature_range}' : self._get_value('temperature_range_display') ,
    #         '{pressure_range}' : self._get_value('pressure_range_display') ,
    #     }
    #
    #     # Заменяем все плейсхолдеры
    #     result = template
    #     for placeholder , value in replacements.items() :
    #         result = result.replace(placeholder , str(value) if value else '')
    #
    #     return result

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'kv': float(self.kv) if self.kv else None,
            'work_temp_min': self.work_temp_min,
            'work_temp_max': self.work_temp_max,
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'brand': {'id': self.brand.id, 'name': self.brand.name}
                if self.brand else None,
            'model_line': {'id': self.model_line.id, 'name': self.model_line.name}
                if self.model_line else None,
            'function': {'id': self.function.id, 'name': self.function.name}
                if self.function else None,
            'ip': {'id': self.ip.id, 'name': self.ip.name}
                if self.ip else None,
            'exd': {'id': self.exd.id, 'name': self.exd.name}
                if self.exd else None,
            'power_supply': {'id': self.power_supply.id, 'name': self.power_supply.name}
                if self.power_supply else None,
            'body_material': {'id': self.body_material.id, 'name': self.body_material.name}
                if self.body_material else None,
            'solenoid_body_material': {'id': self.solenoid_body_material.id, 'name': self.solenoid_body_material.name}
                if self.solenoid_body_material else None,
            'pneumatic_connection': {'id': self.pneumatic_connection.id, 'name': self.pneumatic_connection.name}
                if self.pneumatic_connection else None,
        }

    def __str__(self):
        return self.name

    # def save(self , *args , **kwargs) :
    #     from django.core.exceptions import ValidationError
    #
    #     # Получаем оригинальный объект
    #     original = None
    #     if self.pk :
    #         try :
    #             original = self.__class__._default_manager.get(pk=self.pk)
    #         except self.__class__.DoesNotExist :
    #             pass
    #
    #     # Автозаполнение полей name description
    #     self.name = self.generated_model_name_description('name')
    #     self.description = self.generated_model_name_description('description')
    #
    #     # Сохраняем
    #     super().save(*args , **kwargs)

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
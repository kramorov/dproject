# pneumatic_fittings/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import Dict , List , Optional , Any
from core.models.mixins import StructuredDataMixin, TemplateMixin, CopyMixin, CatalogDictMixin
from core.models import ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin , FilterDefinition , FilterType , DataSourceType
from materials.models import MaterialGeneral
from params.models import ThreadSize , ThreadInnerOuter , ThreadTypes
from producers.models import Brands , Producer
from sku.models import SKUMixin

'''
Фитинги
Тип фитинга:
    Обжим трубки - резьба наружная  Штуцер: метрическая трубка - резьба NPT (коническая)
    Обжим трубки - резьба внутр (не исп)
Форма фитинга:
    прямой
    угловой
    угловой 45
Диаметры трубки (метрическая, дюймовая)
Материал трубки
Материал фитинга
Резьба - тип резьбы, шаг
Цанговый фитинг и классический обжимной фитинг (компрессионный) часто путают, так как они оба обеспечивают герметичность за счет сжатия трубы. Однако ключевое отличие заключается в способе фиксации, необходимости инструмента и возможности многократного использования. 
Основные отличия:
Цанговый фитинг (Push-in / Push-fit):
Принцип: Трубка просто вставляется до упора. Зубцы цанги (разрезного кольца) врезаются в трубу, удерживая её, а уплотнительное кольцо обеспечивает герметичность.
Монтаж: Не требует инструментов.
Разборность: Легко демонтируется нажатием на фиксирующее кольцо.
Применение: Чаще используется в пневматике, водоочистителях (быстрый монтаж).
Обжимной фитинг (Компрессионный):
Принцип: Состоит из корпуса, обжимного кольца (оливкового кольца) и гайки. Гайка затягивается ключом, сдавливая кольцо на трубе.
Монтаж: Требует применения гаечных ключей.
Разборность: Многократно разборный, но при каждом монтаже кольцо деформируется сильнее.
Применение: Широко используется для металлопластиковых и медных труб в системах водоснабжения и отопления
Сравнение:
Характеристика 	Цанговый (быстрый) фитинг	Обжимной (компрессионный) фитинг
Монтаж	Вручную (Push-in)	Гаечными ключами
Фиксация	Зубцы цанги	Обжимное кольцо ("оливка")
Разборность	Да, многократно	Да, многократно
Скорость	Очень высокая	Низкая
Вибростойкость	Зависит от модели, есть спец. высокопрочные	Высокая, если хорошо затянут
1. Накидная гайка («Ёлочка» с гайкой)
Трубка надевается на неподвижный конусообразный штуцер (ёлочку), а сверху затягивается накидной гайкой.
Плюсы: Исключительно высокая надежность. Трубку практически невозможно вырвать давлением или вибрацией.
Минусы: Монтаж дольше, чем у цанги; требует калиброванного размера трубки.
Где встречается: В местах с сильной вибрацией или там, где самопроизвольное отсоединение критично.
2. Ниппельное соединение (Стандартная «Ёлочка»)
Самый простой вариант: трубка просто натягивается на зазубренный штуцер. Для фиксации часто используется внешний червячный или силовой хомут.
Плюсы: Дешевизна, универсальность (подходит для шлангов разного качества).
Минусы: Сложный демонтаж (часто трубку приходится срезать), риск повреждения мягких трубок зубцами.
Где встречается: Магистрали с гибкими резиновыми шлангами, бюджетное оборудование.
3. Резьбовые фитинги с врезным кольцом (DIN 2353)
Похожи на компрессионные, но вместо простого обжима стальное кольцо с острой кромкой буквально «врезается» в поверхность трубки при затягивании гайки.
Плюсы: Выдерживают экстремально высокое давление (сотни бар).
Минусы: Требуют жестких трубок (медь, сталь, жесткий нейлон) и точной затяжки. Соединение практически неразборное (кольцо остается на трубке навсегда).
Где встречается: Тяжелая пневматика высокого давления и гидропневматические системы.
4. БРС (Быстроразъемные соединения / «Рапид»)
Это механизмы «папа-мама» с подпружиненным клапаном. При отсоединении клапан сразу перекрывает воздух.
Плюсы: Позволяют менять инструмент «на лету» без отключения компрессора.
Минусы: Громоздкость, со временем могут начать травить воздух через уплотнения.
Где встречается: Подключение пневмоинструмента (дрели, гайковерты) к шлангам.
'''


# )
# PowerSupplies, ExdOption, IpOption, BodyCoatingOption,BlinkerOption,SwitchesParameters, EnvTempParameters, \
# DigitalProtocolsSupportOption, ControlUnitInstalledOption,ActuatorType, ValveTypes, GearBoxTypes, \
# HandWheelInstalledOption, OperatingModeOption

class FittingShape(StructuredDataMixin , models.Model) :
    name = models.CharField(max_length=100 , verbose_name=_("Название формы"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Особенности применения"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Форма фитинга"
        verbose_name_plural = "Формы фитингов"

    def __str__(self) :
        return self.name


class FittingFixationMethod(StructuredDataMixin , models.Model) :
    name = models.CharField(max_length=100 , verbose_name=_("Название способа"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Описание для подсказок"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Способ фиксации фитинга"
        verbose_name_plural = "Способы фиксации фитингов"

    def __str__(self) :
        return self.name


class PneumaticFittingVariety(StructuredDataMixin , models.Model) :
    """
    Разновидности конструкций фитингов
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название разновидности конструкции'))
    code = models.CharField(max_length=20 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код разновидности конструкции привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание разновидности конструкции фитинга'))
    fixation_method = models.ForeignKey(FittingFixationMethod , on_delete=models.PROTECT)
    shape = models.ForeignKey(FittingShape , on_delete=models.PROTECT)
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Название разновидности конструкции фитинга')
        verbose_name_plural = _('Названия разновидностей конструкции фитинга')

    def __str__(self) :
        return self.name


class PneumaticFittingModelLine(ImageGalleryMixin, TechDocMixin,
                                CertDocMixin,
                                EquipmentTypeMixin,
                                StructuredDataMixin, CopyMixin, models.Model):
    """
    Серия пневматических фитингов.

    Определяет общие характеристики линейки: производитель, бренд, тип фитинга,
    материалы корпуса/трубки, рабочие температуры и давления.

    Наследует:
      - ImageGalleryMixin — галерея изображений серии
      - TechDocMixin — техническая документация
      - EquipmentTypeMixin — тип оборудования (для SKU)
    """

    name = models.CharField(max_length=100 ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название фитинга'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код фитинга"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание разновидности серии фитингов'))
    name_template = models.CharField(max_length=300 ,
                                     verbose_name=_("Шаблон названия") ,
                                     help_text=_('Шаблон для текстового названия фитинга'))
    description_template = models.TextField(blank=True , verbose_name=_("Шаблон описания") ,
                                            help_text=_('Шаблон для описания фитинга'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer , related_name='pneumatic_fitting_model_line_producer' , blank=True ,
                                 null=True ,
                                 on_delete=models.SET_NULL ,
                                 help_text=_('Производитель фитингов') ,
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands , related_name='pneumatic_fitting_model_line_brand' , blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              help_text=_('Бренд фитингов') ,
                              verbose_name=_("Бренд"))
    is_swivel = models.BooleanField(default=False ,
                                    verbose_name=_("Поворотный") ,
                                    help_text=_('Поворотное исполнение серии фитингов'))


    #     body_material_specified = models.ForeignKey(MaterialSpecified, related_name='valve_line_body_material',
    #                                                 blank=True, null=True,
    #                                                 on_delete=models.SET_NULL,
    #                                                 help_text=_('Материал корпуса арматуры'),
    #                                                 verbose_name=_('Материал корпуса'))

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия пневматических фитингов')
        verbose_name_plural = _('Серии пневматических фитингов')

    def __str__(self) :
        return self.name



class PneumaticFitting(CatalogDictMixin, SmartCatalogMixin,
                       ImageGalleryMixin, TechDocMixin,
                       SKUMixin, EquipmentTypeMixin,
                       StructuredDataMixin, TemplateMixin, CopyMixin, models.Model):
    """
    Пневматический фитинг (конкретный артикул каталога).

    Наследует:
      - CatalogDictMixin — структурированная сериализация (to_dict/to_values_dict)
      - SmartCatalogMixin — фильтрация, поиск, exact/compatible split
      - ImageGalleryMixin — галерея изображений
      - TechDocMixin — техническая документация
      - SKUMixin — учётная номенклатура (автосинхронизация через save())
      - EquipmentTypeMixin — тип оборудования
      - TemplateMixin — шаблоны названий/описаний
      - CopyMixin — копирование в админке

    Основные поля:
      - model_line: PneumaticFittingModelLine (серия)
      - fitting_variety: тип фитинга
      - pipe_diameter, pipe_material: параметры трубки
      - thread, thread_inner_outer: резьбовое соединение
      - body_material: материал корпуса
    """

    name = models.CharField(max_length=300 ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название фитинга'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код фитинга"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание разновидности конструкции фитинга'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(PneumaticFittingModelLine , related_name='pneumatic_fitting_model_line_new' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия фитинга') ,
                                   verbose_name=_("Серия"))
    fitting_variety = models.ForeignKey(PneumaticFittingVariety , related_name='pneumatic_fitting_variety' ,
                                        blank=True ,
                                        null=True ,
                                        on_delete=models.SET_NULL ,
                                        help_text=_('Тип фитинга') ,
                                        verbose_name=_("Тип"))

    body_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_body_material' , blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Корпус') ,
                                      verbose_name=_('Тип материала корпуса'))
    pipe_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_pipe_material' , blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Трубка') ,
                                      verbose_name=_('Тип материала трубки'))
    pipe_diameter = (models.IntegerField(blank=True ,
                                         null=True ,
                                         help_text=_('Диаметр') ,
                                         verbose_name=_('Диаметр трубки, мм')))
    thread = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                               related_name='pneumatic_fitting_thread' ,
                               verbose_name=_("Резьба") ,
                               help_text=_('Резьба фитинга'))

    thread_inner_outer = models.ForeignKey(ThreadInnerOuter , on_delete=models.SET_NULL , null=True , blank=True ,
                                           related_name='pneumatic_fitting_thread_in_out' ,
                                           verbose_name=_("Резьба наружная или внутренняя") ,
                                           help_text=_('Резьба наружная или внутренняя'))
    # ==================== ПОЛЯ ДЛЯ ГЛУШИТЕЛЕЙ ====================

    # Пропускная способность (л/мин или м³/ч)
    flow_rate = models.DecimalField(
        max_digits=10 ,
        decimal_places=2 ,
        blank=True , null=True ,
        verbose_name=_("Пропускная способность") ,
        help_text=_('Пропускная способность глушителя (Норм.л/мин)')
    )

    # Уровень шума (дБ)
    noise_level = models.DecimalField(
        max_digits=5 ,
        decimal_places=1 ,
        blank=True , null=True ,
        verbose_name=_("Уровень шума") ,
        help_text=_('Уровень шума глушителя (дБ)')
    )

    # Рабочее давление (бар)
    operating_pressure = models.DecimalField(
        max_digits=8 ,
        decimal_places=2 ,
        blank=True , null=True ,
        verbose_name=_("Рабочее давление") ,
        help_text=_('Максимальное рабочее давление (бар)')
    )

    pressure_min = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True ,
                                       help_text=_('Минимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.мин, бар'))
    pressure_max = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True ,
                                       help_text=_('Максимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.макс, бар'))
    temp_min = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.мин") ,
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.макс") ,
                                        help_text=_('Максимальная температура окружающей среды'))

    class Meta :
        ordering = ['pipe_diameter' , 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand if self.model_line else None

    def save(self, *args, **kwargs):
        """Сохраняет модель и синхронизирует номенклатуру (SKU)."""
        super().save(*args, **kwargs)
        self.sync_sku()

    def clean(self):
        """Вид артикула должен совпадать с видом серии (вид = свойство серии)."""
        super().clean()
        if self.model_line_id and self.equipment_type_id:
            ml_eq = self.model_line.equipment_type if self.model_line else None
            if ml_eq is not None and ml_eq.pk != self.equipment_type_id:
                raise ValidationError({
                    'equipment_type': _(
                        'Тип оборудования артикула (%(item)s) не совпадает с типом серии (%(line)s). '
                        'Вид определяется серией — исправьте серию или тип артикула.'
                    ) % {'item': self.equipment_type.code, 'line': ml_eq.code},
                })

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        if self.temp_min is not None and self.temp_max is not None :
            return f'{self.temp_min}..{self.temp_max}'
        return ''

    @property
    def pressure_range_display(self) :
        """Отображаемый диапазон рабочих давлений"""
        if self.pressure_min is not None and self.pressure_max is not None :
            return f'{self.pressure_min}..{self.pressure_max}'
        if self.operating_pressure is not None :
            return str(self.operating_pressure)
        return ''

    @property
    def swivel_display(self) :
        """Текстовое обозначение поворотности для шаблонов."""
        if self.model_line is None :
            return ''
        return 'поворотный' if self.model_line.is_swivel else 'неповоротный'

    def _get_name_template_source(self) :
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template if self.model_line else None

    def _get_description_template_source(self) :
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template if self.model_line else None

    def _get_default_name_template(self) -> str :
        default_description_template = "{model_code} {fitting_variety} {brand}"
        return default_description_template

    def _get_default_description_template(self) -> str :
        default_description_template = "{model_code} {fitting_variety} {brand}, {thread_inner_outer} резьба {thread}, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар"
        return default_description_template

    def _get_data_dict(self) -> Dict[str , str] :
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены
        Шаблон названия:

        Шаблон описания

        """
        return {
            '{model_code}' : 'code' ,
            '{brand}' : 'model_line__brand' ,
            '{temperature_range}' : 'temperature_range_display' ,
            '{fitting_variety}' : 'fitting_variety__name' ,
            '{shape}' : 'fitting_variety__fixation_method' ,
            '{fixation_method}' : 'fitting_variety__fixation_method' ,
            '{swivel}' : 'swivel_display' ,
            '{pressure_range}' : 'pressure_range_display' ,
            '{pipe_diameter}' : 'pipe_diameter' ,
            '{thread}' : 'thread' ,
            '{thread_inner_outer}' : 'thread_inner_outer' ,
            '{operating_pressure}' : 'operating_pressure' ,
            '{noise_level}' : 'noise_level' ,
            '{flow_rate}' : 'flow_rate' ,
        }

    def __str__(self) :
        return self.name

    # def copy(self, save_copy: bool = False, copy_relations: bool = False) -> 'PneumaticFitting':
    #     """
    #     Создает копию объекта PneumaticFitting
    #
    #     Args:
    #         save_copy: Сохранить копию в БД (если False - возвращает несохраненный объект)
    #         copy_relations: Скопировать связанные объекты (ManyToMany и обратные связи)
    #
    #     Returns:
    #         Новый объект PneumaticFitting (сохраненный или нет)
    #
    #     Example:
    #         # В админке или shell
    #         original = PneumaticFitting.objects.get(id=1)
    #         copy_obj = original.copy(save_copy=True)
    #         copy_obj.name = f"Копия {original.name}"
    #         copy_obj.save()
    #     """
    #     # Получаем все поля текущего объекта
    #     all_fields = self._meta.fields
    #
    #     # Создаем словарь для нового объекта, исключая первичный ключ
    #     new_data = {}
    #     for field in all_fields:
    #         if field.name != self._meta.pk.name:
    #             value = getattr(self, field.name)
    #
    #             # Для ForeignKey полей (кроме null=True, blank=True)
    #             if isinstance(field, models.ForeignKey):
    #                 # Если поле не пустое, копируем ссылку
    #                 if value is not None:
    #                     new_data[field.name] = value
    #                 else:
    #                     new_data[field.name] = None
    #             else:
    #                 new_data[field.name] = value
    #
    #     # Изменяем уникальные/специальные поля для копии
    #     new_data['name'] = f"{self.name} (копия)"
    #     new_data['code'] = f"{self.code}_copy"
    #     new_data['sorting_order'] = self.sorting_order + 1
    #
    #     # Создаем новый объект
    #     new_copy = PneumaticFitting(**new_data)
    #
    #     if save_copy:
    #         new_copy.save()
    #
    #     return new_copy

    # @classmethod
    # def get_thread_types(cls, active_only: bool = True) -> List[Dict]:
    #     """
    #     Получить уникальные типы резьб (M, NPT, G, R)
    #     """
    #     from params.models import ThreadTypes
    #
    #     queryset = ThreadTypes.objects.all()
    #     if active_only:
    #         queryset = queryset.filter(is_active=True)
    #
    #     return [{'id': t.id, 'name': t.name, 'code': t.code or ''} for t in queryset]
    #
    @classmethod
    def get_filtered_threads(cls, thread_type_id: int = None) -> List[Dict]:
        """
        Получить резьбы с опциональной фильтрацией по типу резьбы
        """
        from params.models import ThreadSize

        queryset = ThreadSize.objects.filter(is_active=True)

        if thread_type_id:
            queryset = queryset.filter(thread_type_id=thread_type_id)

        # Сортируем для удобства
        queryset = queryset.order_by('thread_type', 'sorting_order')

        return [{'id': t.id, 'name': t.name, 'code': t.code or ''} for t in queryset]

    # ========== КОНФИГУРАЦИЯ ДЛЯ SmartCatalogMixin ==========

    FILTER_DEFINITIONS = [
        # --- Прямые ForeignKey ---
        FilterDefinition(
            param_name='brand_id' ,
            model_field='model_line__brand' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Бренд' ,
            order=1
        ) ,
        FilterDefinition(
            param_name='model_line_id' ,
            model_field='model_line' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Серия' ,
            order=2
        ) ,
        FilterDefinition(
            param_name='fitting_variety_id' ,
            model_field='fitting_variety' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Тип фитинга' ,
            order=3
        ) ,
        FilterDefinition(
            param_name='body_material_id' ,
            model_field='body_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал корпуса' ,
            order=4
        ) ,
        FilterDefinition(
            param_name='pipe_material_id' ,
            model_field='pipe_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал трубки' ,
            order=5
        ) ,

        # --- Прямое поле (диаметр трубки) ---
        FilterDefinition(
            param_name='pipe_diameter' ,
            model_field='pipe_diameter' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Диаметр трубки' ,
            order=6
        ) ,

        # --- Резьба и её тип ---
        FilterDefinition(
            param_name='thread_type_id' ,
            model_field='thread' ,
            is_parent_filter=True ,  # ← всегда режим «тип резьбы»
            filter_type=FilterType.THREAD_COMPATIBLE ,  # ← специализированный
            data_source_type=DataSourceType.GLOBAL_MODEL ,
            source_model=ThreadTypes ,
            label='Тип резьбы' ,
            order=7
        ) ,
        FilterDefinition(
            param_name='thread_id' ,
            model_field='thread' ,
            filter_type=FilterType.THREAD_COMPATIBLE ,  # ← специализированный
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Резьба' ,
            order=8
        ) ,
        FilterDefinition(
            param_name='thread_inner_outer_id' ,
            model_field='thread_inner_outer' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FOREIGN_KEY ,
            label='Тип резьбы (нар/внут)' ,
            order=9
        ) ,

        # --- Температура ---
        FilterDefinition(
            param_name='temp_min' ,
            model_field='temp_min' ,
            filter_type=FilterType.TEMP_MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Мин. температура (≤)' ,
            order=10
        ) ,

        # --- Поворотность ---
        FilterDefinition(
            param_name='swivel' ,
            model_field='model_line__is_swivel' ,
            filter_type=FilterType.BOOLEAN ,
            data_source_type=DataSourceType.CHOICES ,
            choices=[('true', 'Поворотный'), ('false', 'Неповоротный')] ,
            label='Поворотность' ,
            order=11
        ) ,
    ]

    SEARCH_FIELDS = ['code']  # только поиск по коду
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' , 'fitting_variety' ,
        'body_material' , 'pipe_material' , 'thread' , 'thread_inner_outer'
    ]

    def to_values_dict(self) -> dict:
        """Облегчённая сериализация для списков."""
        first_img = self._get_first_image() if hasattr(self, '_get_first_image') else None
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'pipe_diameter': self.pipe_diameter,
            'fitting_variety': {
                'id': self.fitting_variety.id,
                'name': self.fitting_variety.name,
            } if self.fitting_variety else None,
            'body_material': {
                'id': self.body_material.id,
                'name': self.body_material.name,
            } if self.body_material else None,
            'pipe_material': {
                'id': self.pipe_material.id,
                'name': self.pipe_material.name,
            } if self.pipe_material else None,
            'thread_name': str(self.thread) if self.thread else None,
            'thread_inner_outer_name': str(self.thread_inner_outer) if self.thread_inner_outer else None,
            'images': [first_img] if first_img else [],
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': self.model_line.code,
            } if self.model_line else None,
            'sku': {
                'id': self.sku_id,
                'code': self.sku.code if self.sku else None,
                'name': self.sku.name if self.sku else None,
            } if self.sku_id else None,
        }

    def _safe_m2m(self, method_name):
        try:
            return getattr(self, method_name)()
        except Exception:
            import logging
            logging.getLogger('pneumatic_fittings').warning(
                'Section %s failed for PneumaticFitting #%s', method_name, self.pk, exc_info=True)
            return []

    def _get_docs_section(self) -> list:
        docs = []
        seen = set()
        for doc in self.tech_docs.all():
            if doc.media_file and doc.id not in seen:
                seen.add(doc.id)
                has_email = doc.variants.filter(role='email').exists()
                docs.append({
                    'id': doc.id, 'name': getattr(doc, 'name', '') or '',
                    'url': f"/api/media/{doc.id}/download/",
                    'file_name': getattr(doc, 'name', '') or '',
                    'preview_url': f"/api/media/{doc.id}/view/",
                    'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                })
        if self.model_line and hasattr(self.model_line, 'tech_docs'):
            for doc in self.model_line.tech_docs.all():
                if doc.media_file and doc.id not in seen:
                    seen.add(doc.id)
                    has_email = doc.variants.filter(role='email').exists()
                    docs.append({
                        'id': doc.id, 'name': getattr(doc, 'name', '') or '',
                        'url': f"/api/media/{doc.id}/download/",
                        'file_name': getattr(doc, 'name', '') or '',
                        'preview_url': f"/api/media/{doc.id}/view/",
                        'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                    })
        return docs

    def _get_certs_section(self) -> list:
        certs = []
        if self.model_line and hasattr(self.model_line, 'cert_docs'):
            cert_ids = list(
                self.model_line.cert_docs
                .filter(is_active=True)
                .values_list('id', flat=True)
            )
            if cert_ids:
                from cert_doc.models import CertData
                from urllib.parse import quote
                import re as _re
                for cert in CertData.objects.filter(id__in=cert_ids).select_related('media_item', 'cert_variety'):
                    media = getattr(cert, 'media_item', None)
                    if not media:
                        continue
                    has_email = media.variants.filter(role='email').exists()
                    variety_name = str(cert.cert_variety) if cert.cert_variety else ''
                    cert_code = getattr(cert, 'code', '') or ''
                    ml_name = self.model_line.name if self.model_line else ''
                    base_name = _re.sub(r'[\\/*?:"<>|]', '_', f"{variety_name} {cert_code} для {ml_name}".strip())
                    dl_name = f"{base_name}.pdf"
                    email_name = f"{base_name} (сжат).pdf"
                    certs.append({
                        'id': media.id,
                        'name': getattr(cert, 'name', '') or '',
                        'file_name': dl_name,
                        'email_file_name': email_name,
                        'url': f"/api/media/{media.id}/download/?filename={quote(dl_name)}",
                        'preview_url': f"/api/media/{media.id}/view/",
                        'email_url': f"/api/media/{media.id}/download/?variant=email&filename={quote(email_name)}" if has_email else None,
                    })
        return certs

    def _build_detail_sections(self) -> list:
        specs_fields = []

        def f(key, label, value, unit='', type_='text'):
            return {'key': key, 'label': label, 'value': value, 'unit': unit,
                    'type': type_, 'order': len(specs_fields) + 1}

        specs_fields.append(f('model_line', 'Серия', self.model_line.name if self.model_line else ''))
        specs_fields.append(f('brand', 'Бренд', self.model_line.brand.name if self.model_line and self.model_line.brand else ''))
        specs_fields.append(f('fitting_variety', 'Тип фитинга', str(self.fitting_variety) if self.fitting_variety else ''))
        specs_fields.append(f('thread', 'Резьба', str(self.thread) if self.thread else ''))
        specs_fields.append(f('thread_inner_outer', 'Резьба нар/внутр', str(self.thread_inner_outer) if self.thread_inner_outer else ''))
        specs_fields.append(
            f('body_material' , 'Материал корпуса' , str(self.body_material) if self.body_material else ''))
        specs_fields.append(f('temperature' , 'Т раб., °С' , self.temperature_range_display))
        silencer_plug = ['fitting-silencer' , 'fitting-plug']
        if not self.equipment_type.code in silencer_plug:
            specs_fields.append(f('pipe_diameter', 'Диаметр трубки, мм', self.pipe_diameter if self.pipe_diameter is not None else '', type_='number'))
            specs_fields.append(f('pipe_material' , 'Материал трубки' , str(self.pipe_material) if self.pipe_material else ''))
            specs_fields.append(f('pressure' , 'Р раб., бар' , self.pressure_range_display))
        else:
            if self.operating_pressure is not None :
                specs_fields.append({'key' : 'operating_pressure' , 'label' : 'P раб.макс, бар' ,
                                     'value' : str(self.operating_pressure) , 'unit' : '' , 'type' : 'number' ,
                                     'order' : 3})
            if self.flow_rate is not None :
                specs_fields.append(
                    {'key' : 'flow_rate' , 'label' : 'Пропускная способность, Нл/мин' , 'value' : str(self.flow_rate) ,
                     'unit' : '' , 'type' : 'number' , 'order' : 1})
            if self.noise_level is not None :
                specs_fields.append(
                    {'key' : 'noise_level' , 'label' : 'Уровень шума, дБ' , 'value' : str(self.noise_level) ,
                     'unit' : '' , 'type' : 'number' , 'order' : 2})


        #
        #
        # silencer_fields = []
        # if self.flow_rate is not None:
        #     silencer_fields.append({'key': 'flow_rate', 'label': 'Пропускная способность, Нл/мин', 'value': str(self.flow_rate), 'unit': '', 'type': 'number', 'order': 1})
        # if self.noise_level is not None:
        #     silencer_fields.append({'key': 'noise_level', 'label': 'Уровень шума, дБ', 'value': str(self.noise_level), 'unit': '', 'type': 'number', 'order': 2})
        # if self.operating_pressure is not None:
        #     silencer_fields.append({'key': 'operating_pressure', 'label': 'P раб.макс, бар', 'value': str(self.operating_pressure), 'unit': '', 'type': 'number', 'order': 3})
        #
        groups = [{'key': 'general', 'title': 'Основные', 'order': 1, 'fields': specs_fields}]
        # if silencer_fields:
        #     groups.append({'key': 'silencer', 'title': 'Глушитель', 'order': 2, 'fields': silencer_fields})

        return [
            {'key': 'images', 'title': 'Изображения', 'type': 'gallery', 'order': 1, 'data': self._safe_m2m('_get_images_section')},
            {'key': 'specs', 'title': 'Характеристики', 'type': 'specs', 'order': 2, 'groups': groups},
            {'key': 'docs', 'title': 'Документация', 'type': 'files', 'order': 3, 'data': self._safe_m2m('_get_docs_section')},
            {'key': 'certs', 'title': 'Сертификаты', 'type': 'files', 'order': 4, 'data': self._safe_m2m('_get_certs_section')},
            {'key': 'description', 'title': 'Описание', 'type': 'text', 'order': 5, 'data': self.description or ''},
        ]

    def to_dict(self) -> Dict[str , Any] :
        """
        Конвертировать объект в словарь для API

        Returns:
            Dict: структурированные данные фитинга
        """
        return {
            'id' : self.id ,
            'name' : self.name ,
            'code' : self.code ,
            'description' : self.description ,
            'temp_min' : self.temp_min ,
            'temp_max' : self.temp_max ,
            'pipe_diameter' : self.pipe_diameter ,
            'flow_rate' : float(self.flow_rate) if self.flow_rate else None ,
            'noise_level' : float(self.noise_level) if self.noise_level else None ,
            'operating_pressure' : float(self.operating_pressure) if self.operating_pressure else None ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'brand' : {
                'id' : self.model_line.brand.id ,
                'name' : self.model_line.brand.name ,
                'code' : self.model_line.brand.code
            } if self.model_line and self.model_line.brand else None ,
            'model_line' : {
                'id' : self.model_line.id ,
                'name' : self.model_line.name ,
                'code' : self.model_line.code ,
                'description': self.model_line.description or ''
            } if self.model_line else None ,
            'fitting_variety' : {
                'id' : self.fitting_variety.id ,
                'name' : self.fitting_variety.name ,
                'code' : self.fitting_variety.code
            } if self.fitting_variety else None ,
            'body_material' : {
                'id' : self.body_material.id ,
                'name' : self.body_material.name
            } if self.body_material else None ,
            'pipe_material' : {
                'id' : self.pipe_material.id ,
                'name' : self.pipe_material.name
            } if self.pipe_material else None ,
            'thread' : {
                'id' : self.thread.id ,
                'name' : self.thread.name ,
                'code' : self.thread.code ,
                'thread_type' : {  # ← новый блок
                    'id' : self.thread.thread_type.id ,
                    'name' : self.thread.thread_type.name ,
                    'code' : self.thread.thread_type.code
                } if self.thread and self.thread.thread_type else None
            } if self.thread else None ,
            'thread_inner_outer' : {
                'id' : self.thread_inner_outer.id ,
                'name' : self.thread_inner_outer.name ,
                'code' : self.thread_inner_outer.code
            } if self.thread_inner_outer else None ,

            'sections' : self._build_detail_sections() ,
        }

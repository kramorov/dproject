# pneumatic_fittings/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict , List , Optional , Any
from core.models.mixins import StructuredDataMixin , TemplateGeneratorMixin , TemplateMixin , CopyMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin , FilterDefinition , FilterType , DataSourceType
from materials.models import MaterialGeneral
from params.models import ThreadSize , ThreadInnerOuter , ThreadTypes
from producers.models import Brands , Producer

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
    is_swivel = models.BooleanField(
        default=False ,
        verbose_name=_("Поворотный") ,
        help_text=_("Можно ли вращать корпус относительно резьбовой части")
    )
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


class PneumaticFittingModelLine(StructuredDataMixin , CopyMixin , models.Model) :
    """
    Серия пневматических фитингов
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
    fitting_variety = models.ForeignKey(PneumaticFittingVariety , related_name='pneumatic_fitting_model_line_variety' ,
                                        blank=True ,
                                        null=True ,
                                        on_delete=models.SET_NULL ,
                                        help_text=_('Тип фитинга') ,
                                        verbose_name=_("Тип"))

    body_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_model_line_body_material' ,
                                      blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Корпус') ,
                                      verbose_name=_('Тип материала корпуса'))
    pipe_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_model_line_pipe_material' ,
                                      blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Трубка') ,
                                      verbose_name=_('Тип материала трубки'))

    #     body_material_specified = models.ForeignKey(MaterialSpecified, related_name='valve_line_body_material',
    #                                                 blank=True, null=True,
    #                                                 on_delete=models.SET_NULL,
    #                                                 help_text=_('Материал корпуса арматуры'),
    #                                                 verbose_name=_('Материал корпуса'))
    work_temp_min = models.IntegerField(
        null=True , blank=True , default=-40 ,
        help_text=_('Минимальная рабочая температура, °С') ,
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True , blank=True , default=120 ,
        help_text=_('Максимальная рабочая температура, °С') ,
        verbose_name=_('Т раб.макс, °С'))

    pressure_min = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True , default=0 ,
                                       help_text=_('Минимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.мин, бар'))

    pressure_max = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True , default=40 ,
                                       help_text=_('Максимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.макс, бар'))

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия пневматических фитингов')
        verbose_name_plural = _('Серии пневматических фитингов')

    def __str__(self) :
        return self.name

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        return f'{self.pressure_min}..{self.pressure_max}'

    # def copy(self, save_copy: bool = False, copy_relations: bool = False) -> 'PneumaticFittingModelLine':
    #     """
    #     Создает копию объекта PneumaticFittingModelLine
    #
    #     Args:
    #         save_copy: Сохранить копию в БД (если False - возвращает несохраненный объект)
    #         copy_relations: Скопировать связанные объекты (ManyToMany и обратные связи)
    #
    #     Returns:
    #         Новый объект PneumaticFittingModelLine (сохраненный или нет)
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
    #     new_copy = PneumaticFittingModelLine(**new_data)
    #     #
    #     # if save_copy:
    #     #     new_copy.save()
    #
    #     return new_copy


class PneumaticFitting(SmartCatalogMixin , StructuredDataMixin , TemplateMixin , CopyMixin , models.Model) :
    """
    Пневматические фитинги
    """
    temp_min = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.мин") ,
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.макс") ,
                                        help_text=_('Максимальная температура окружающей среды'))
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
    producer = models.ForeignKey(Producer , related_name='pneumatic_fitting_producer' , blank=True , null=True ,
                                 on_delete=models.SET_NULL ,
                                 help_text=_('Производитель фитингов') ,
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands , related_name='pneumatic_fitting_brand' , blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              help_text=_('Бренд фитингов') ,
                              verbose_name=_("Бренд"))

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

    class Meta :
        ordering = ['pipe_diameter' , 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.work_temp_min}..{self.model_line.work_temp_max}'

    @property
    def pressure_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.pressure_min}..{self.model_line.pressure_max}'

    def _get_name_template_source(self) :
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self) :
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str :
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Исп. {exd} Т.окр. {work_temp_min}..{work_temp_max} °С"
        return default_description_template

    def _get_default_description_template(self) -> str :
        default_description_template = "{model_code} {fitting_variety} {brand}, {thread_inner_outer} резьба {thread}, цанговый зажим для трубки из металла наружн.диам. {pipe_diameter} мм, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар, корпус - Нержавеющая сталь 304, в сборе с уплотнительным кольцом, трубки для присоединения: нержавеющая сталь, медь"
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
            model_field='brand' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Бренд' ,
            order=1
        ) ,
        FilterDefinition(
            param_name='fitting_model_line_id' ,
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
    ]

    SEARCH_FIELDS = ['code']  # только поиск по коду
    SELECT_RELATED_FIELDS = [
        'brand' , 'model_line' , 'fitting_variety' ,
        'body_material' , 'pipe_material' , 'thread' , 'thread_inner_outer'
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
                'id' : self.brand.id ,
                'name' : self.brand.name ,
                'code' : self.brand.code
            } if self.brand else None ,
            'model_line' : {
                'id' : self.model_line.id ,
                'name' : self.model_line.name ,
                'code' : self.model_line.code
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
        }
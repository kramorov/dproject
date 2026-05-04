# pneumatic_fittings/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import StructuredDataMixin, TemplateGeneratorMixin, TemplateMixin
from materials.models import MaterialGeneral
from params.models import ThreadSize, ThreadInnerOuter
from producers.models import Brands, Producer

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

class FittingShape(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название формы"))
    code = models.SlugField(max_length=50, unique=True, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True, verbose_name=_("Особенности применения"))
    is_swivel = models.BooleanField(
        default=False,
        verbose_name=_("Поворотный"),
        help_text=_("Можно ли вращать корпус относительно резьбовой части")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Форма фитинга"
        verbose_name_plural = "Формы фитингов"

    def __str__(self):
        return self.name


class FittingFixationMethod(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Название способа"))
    code = models.SlugField(max_length=50, unique=True, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    help_text_content = models.TextField(blank=True, verbose_name=_("Описание для подсказок"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Способ фиксации фитинга"
        verbose_name_plural = "Способы фиксации фитингов"

    def __str__(self):
        return self.name


class PneumaticFittingVariety(StructuredDataMixin, models.Model):
    """
    Разновидности конструкций фитингов
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название разновидности конструкции'))
    code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код разновидности конструкции привода"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности конструкции фитинга'))
    fixation_method = models.ForeignKey(FittingFixationMethod, on_delete=models.PROTECT)
    shape = models.ForeignKey(FittingShape, on_delete=models.PROTECT)
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Название разновидности конструкции фитинга')
        verbose_name_plural = _('Названия разновидностей конструкции фитинга')

    def __str__(self):
        return self.name


class PneumaticFittingModelLine(StructuredDataMixin, models.Model):
    """
    Серия пневматических фитингов
    """

    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название фитинга'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код фитинга"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности серии фитингов'))
    name_template = models.CharField(max_length=300,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия фитинга'))
    description_template = models.TextField(blank=True, verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания фитинга'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='pneumatic_fitting_model_line_producer', blank=True, null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель фитингов'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='pneumatic_fitting_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд фитингов'),
                              verbose_name=_("Бренд"))
    fitting_variety = models.ForeignKey(PneumaticFittingVariety, related_name='pneumatic_fitting_model_line_variety',
                                        blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Тип фитинга'),
                                        verbose_name=_("Тип"))

    body_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_model_line_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    pipe_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_model_line_pipe_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Трубка'),
                                      verbose_name=_('Тип материала трубки'))

    #     body_material_specified = models.ForeignKey(MaterialSpecified, related_name='valve_line_body_material',
    #                                                 blank=True, null=True,
    #                                                 on_delete=models.SET_NULL,
    #                                                 help_text=_('Материал корпуса арматуры'),
    #                                                 verbose_name=_('Материал корпуса'))
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    pressure_min = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=0,
                                       help_text=_('Минимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.мин, бар'))

    pressure_max = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=40,
                                       help_text=_('Максимальное рабочее давление, бар'),
                                       verbose_name=_('P раб.макс, бар'))

    class Meta:
        ordering = ['brand', 'code']
        verbose_name = _('Серия пневматических фитингов')
        verbose_name_plural = _('Серии пневматических фитингов')

    def __str__(self):
        return self.name

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.pressure_min}..{self.pressure_max}'

    def copy(self, save_copy: bool = False, copy_relations: bool = False) -> 'PneumaticFittingModelLine':
        """
        Создает копию объекта PneumaticFittingModelLine

        Args:
            save_copy: Сохранить копию в БД (если False - возвращает несохраненный объект)
            copy_relations: Скопировать связанные объекты (ManyToMany и обратные связи)

        Returns:
            Новый объект PneumaticFittingModelLine (сохраненный или нет)

        Example:
            # В админке или shell
            original = PneumaticFitting.objects.get(id=1)
            copy_obj = original.copy(save_copy=True)
            copy_obj.name = f"Копия {original.name}"
            copy_obj.save()
        """
        # Получаем все поля текущего объекта
        all_fields = self._meta.fields

        # Создаем словарь для нового объекта, исключая первичный ключ
        new_data = {}
        for field in all_fields:
            if field.name != self._meta.pk.name:
                value = getattr(self, field.name)

                # Для ForeignKey полей (кроме null=True, blank=True)
                if isinstance(field, models.ForeignKey):
                    # Если поле не пустое, копируем ссылку
                    if value is not None:
                        new_data[field.name] = value
                    else:
                        new_data[field.name] = None
                else:
                    new_data[field.name] = value

        # Изменяем уникальные/специальные поля для копии
        new_data['name'] = f"{self.name} (копия)"
        new_data['code'] = f"{self.code}_copy"
        new_data['sorting_order'] = self.sorting_order + 1

        # Создаем новый объект
        new_copy = PneumaticFittingModelLine(**new_data)
        #
        # if save_copy:
        #     new_copy.save()

        return new_copy


class PneumaticFitting(StructuredDataMixin, TemplateMixin, models.Model):
    """
    Пневматические фитинги
    """
    temp_min = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.мин"),
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.макс"),
                                        help_text=_('Максимальная температура окружающей среды'))
    name = models.CharField(max_length=300,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название фитинга'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код фитинга"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности конструкции фитинга'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='pneumatic_fitting_producer', blank=True, null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель фитингов'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='pneumatic_fitting_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд фитингов'),
                              verbose_name=_("Бренд"))

    model_line = models.ForeignKey(PneumaticFittingModelLine, related_name='pneumatic_fitting_model_line_new',
                                   blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия фитинга'),
                                   verbose_name=_("Серия"))
    fitting_variety = models.ForeignKey(PneumaticFittingVariety, related_name='pneumatic_fitting_variety', blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Тип фитинга'),
                                        verbose_name=_("Тип"))

    body_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_body_material', blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    pipe_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_pipe_material', blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Трубка'),
                                      verbose_name=_('Тип материала трубки'))
    pipe_diameter = (models.IntegerField(blank=True,
                                         null=True,
                                         help_text=_('Диаметр'),
                                         verbose_name=_('Диаметр трубки, мм')))
    thread = models.ForeignKey(ThreadSize, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='pneumatic_fitting_thread',
                               verbose_name=_("Резьба"),
                               help_text=_('Резьба фитинга'))

    thread_inner_outer = models.ForeignKey(ThreadInnerOuter, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='pneumatic_fitting_thread_in_out',
                                           verbose_name=_("Резьба наружная или внутренняя"),
                                           help_text=_('Резьба наружная или внутренняя'))
    # ==================== ПОЛЯ ДЛЯ ГЛУШИТЕЛЕЙ ====================

    # Пропускная способность (л/мин или м³/ч)
    flow_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True, null=True,
        verbose_name=_("Пропускная способность"),
        help_text=_('Пропускная способность глушителя (Норм.л/мин)')
    )

    # Уровень шума (дБ)
    noise_level = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True, null=True,
        verbose_name=_("Уровень шума"),
        help_text=_('Уровень шума глушителя (дБ)')
    )

    # Рабочее давление (бар)
    operating_pressure = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True, null=True,
        verbose_name=_("Рабочее давление"),
        help_text=_('Максимальное рабочее давление (бар)')
    )

    class Meta:
        ordering = ['pipe_diameter', 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.work_temp_min}..{self.model_line.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.model_line.pressure_min}..{self.model_line.pressure_max}'
    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Исп. {exd} Т.окр. {work_temp_min}..{work_temp_max} °С"
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} {fitting_variety} {brand}, {thread_inner_outer} резьба {thread}, цанговый зажим для трубки из металла наружн.диам. {pipe_diameter} мм, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар, корпус - Нержавеющая сталь 304, в сборе с уплотнительным кольцом, трубки для присоединения: нержавеющая сталь, медь"
        return default_description_template

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены
        Шаблон названия:

        Шаблон описания

        """
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{temperature_range}': 'temperature_range_display',
            '{fitting_variety}': 'fitting_variety__name',
            '{shape}': 'fitting_variety__fixation_method',
            '{fixation_method}': 'fitting_variety__fixation_method',
            '{pressure_range}': 'pressure_range_display',
            '{pipe_diameter}': 'pipe_diameter',
            '{thread}': 'thread',
            '{thread_inner_outer}': 'thread_inner_outer',
            '{operating_pressure}': 'operating_pressure',
            '{noise_level}': 'noise_level',
            '{flow_rate}': 'flow_rate',
        }

    def __str__(self):
        return self.name

    def copy(self, save_copy: bool = False, copy_relations: bool = False) -> 'PneumaticFitting':
        """
        Создает копию объекта PneumaticFitting

        Args:
            save_copy: Сохранить копию в БД (если False - возвращает несохраненный объект)
            copy_relations: Скопировать связанные объекты (ManyToMany и обратные связи)

        Returns:
            Новый объект PneumaticFitting (сохраненный или нет)

        Example:
            # В админке или shell
            original = PneumaticFitting.objects.get(id=1)
            copy_obj = original.copy(save_copy=True)
            copy_obj.name = f"Копия {original.name}"
            copy_obj.save()
        """
        # Получаем все поля текущего объекта
        all_fields = self._meta.fields

        # Создаем словарь для нового объекта, исключая первичный ключ
        new_data = {}
        for field in all_fields:
            if field.name != self._meta.pk.name:
                value = getattr(self, field.name)

                # Для ForeignKey полей (кроме null=True, blank=True)
                if isinstance(field, models.ForeignKey):
                    # Если поле не пустое, копируем ссылку
                    if value is not None:
                        new_data[field.name] = value
                    else:
                        new_data[field.name] = None
                else:
                    new_data[field.name] = value

        # Изменяем уникальные/специальные поля для копии
        new_data['name'] = f"{self.name} (копия)"
        new_data['code'] = f"{self.code}_copy"
        new_data['sorting_order'] = self.sorting_order + 1

        # Создаем новый объект
        new_copy = PneumaticFitting(**new_data)

        if save_copy:
            new_copy.save()

        return new_copy

    @classmethod
    def get_thread_types(cls, active_only: bool = True) -> List[Dict]:
        """
        Получить уникальные типы резьб (M, NPT, G, R)
        """
        from params.models import ThreadTypes

        queryset = ThreadTypes.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)

        return [{'id': t.id, 'name': t.name, 'code': t.code or ''} for t in queryset]

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

    # ==================== МЕТОДЫ ДЛЯ ФИЛЬТРАЦИИ И API ====================

    @classmethod
    def get_distinct_values(cls, field_name: str, active_only: bool = True) -> List[Dict]:
        """
        Получить уникальные значения поля для фильтров

        Args:
            field_name: имя поля (поддерживает связанные поля через __)
            active_only: только активные значения

        Returns:
            List[Dict]: список словарей {id, name, code}
        """
        from django.db.models import F

        # Разбираем путь для связанных полей
        if '__' in field_name:
            parts = field_name.split('__')
            base_field = parts[0]
            related_field = parts[1]

            # Получаем связанную модель
            related_model = cls._meta.get_field(base_field).remote_field.model

            queryset = related_model.objects.filter(**{f"{related_field}__isnull": False})
            if active_only:
                queryset = queryset.filter(is_active=True)

            values = queryset.values_list('id', 'name', 'code').distinct()
            return [{'id': v[0], 'name': v[1], 'code': v[2] or ''} for v in values]
        else:
            # Простое поле модели
            queryset = cls.objects.filter(**{f"{field_name}__isnull": False})
            values = queryset.values_list(field_name, flat=True).distinct().order_by(field_name)

            if field_name in ['pipe_diameter']:
                return [{'id': v, 'name': str(v), 'code': ''} for v in values if v is not None]

            # Для ForeignKey полей
            field = cls._meta.get_field(field_name)
            if field.many_to_one:
                related_model = field.remote_field.model
                ids = queryset.values_list(field_name, flat=True).distinct()
                result = []
                for obj_id in ids:
                    obj = related_model.objects.filter(id=obj_id).first()
                    if obj:
                        result.append({'id': obj.id, 'name': obj.name, 'code': obj.code or ''})
                return result

            return [{'id': v, 'name': str(v), 'code': ''} for v in values if v is not None]

    @classmethod
    def get_filter_options(cls) -> Dict[str, List[Dict]]:
        """
        Получить все доступные опции для фильтрации

        Returns:
            Dict: словарь с опциями для каждого поля фильтра
        """
        result = {
            'brands': cls.get_distinct_values('brand'),
            'model_lines': cls.get_distinct_values('model_line'),
            'varieties': cls.get_distinct_values('fitting_variety'),
            'body_materials': cls.get_distinct_values('body_material'),
            'pipe_materials': cls.get_distinct_values('pipe_material'),
            'pipe_diameters': cls.get_distinct_values('pipe_diameter'),
            'thread_types': cls.get_thread_types(),
            'threads': cls.get_distinct_values('thread'),
            'thread_inner_outers': cls.get_distinct_values('thread_inner_outer'),
        }

        return result

    @classmethod
    def filter_by_params(cls, params: Dict) -> Dict:
        """
        Фильтрация по параметрам

        Args:
            params: словарь с параметрами фильтрации
                {
                    'temp_min': int,
                    'code': str,
                    'brand_id': int,
                    'model_line_id': int,
                    'fitting_variety_id': int,
                    'body_material_id': int,
                    'pipe_material_id': int,
                    'pipe_diameter': int,
                    'thread_id': int,
                    'thread_inner_outer_id': int,
                    'is_active': bool,
                    'limit': int,
                    'offset': int
                }

        Returns:
            Dict: {
                'data': List[Dict],
                'total': int,
                'filters_applied': Dict
            }
        """
        queryset = cls.objects.select_related(
            'brand', 'model_line', 'fitting_variety',
            'body_material', 'pipe_material', 'thread', 'thread_inner_outer'
        )

        filters_applied = {}

        # Фильтр по минимальной температуре (<=)
        temp_min = params.get('temp_min')
        if temp_min is not None and temp_min != '':
            try:
                temp_min_value = int(temp_min)
                queryset = queryset.filter(temp_min__lte=temp_min_value)
                filters_applied['temp_min'] = temp_min_value
            except (ValueError, TypeError):
                pass

        # Фильтр по коду (поиск по подстроке)
        code = params.get('code', '')
        if code:
            queryset = queryset.filter(code__icontains=code)
            filters_applied['code'] = code

        # Фильтр по бренду
        brand_id = params.get('brand_id')
        if brand_id and brand_id != 'all':
            queryset = queryset.filter(brand_id=brand_id)
            filters_applied['brand_id'] = brand_id

        # Фильтр по серии
        model_line_id = params.get('model_line_id')
        if model_line_id and model_line_id != 'all':
            queryset = queryset.filter(model_line_id=model_line_id)
            filters_applied['model_line_id'] = model_line_id

        # Фильтр по типу
        variety_id = params.get('fitting_variety_id')
        if variety_id and variety_id != 'all':
            queryset = queryset.filter(fitting_variety_id=variety_id)
            filters_applied['fitting_variety_id'] = variety_id

        # Фильтр по материалу корпуса
        body_material_id = params.get('body_material_id')
        if body_material_id and body_material_id != 'all':
            queryset = queryset.filter(body_material_id=body_material_id)
            filters_applied['body_material_id'] = body_material_id

        # Фильтр по материалу трубки
        pipe_material_id = params.get('pipe_material_id')
        if pipe_material_id and pipe_material_id != 'all':
            queryset = queryset.filter(pipe_material_id=pipe_material_id)
            filters_applied['pipe_material_id'] = pipe_material_id

        # Фильтр по диаметру трубки
        pipe_diameter = params.get('pipe_diameter')
        if pipe_diameter and pipe_diameter != 'all':
            try:
                queryset = queryset.filter(pipe_diameter=pipe_diameter)
                filters_applied['pipe_diameter'] = pipe_diameter
            except (ValueError, TypeError):
                pass
        # Фильтр по типу резьбы (через связанное поле)
        thread_type_id = params.get('thread_type_id')
        if thread_type_id and thread_type_id != 'all':
            queryset = queryset.filter(thread__thread_type_id=thread_type_id)
            filters_applied['thread_type_id'] = thread_type_id
        # Фильтр по резьбе
        thread_id = params.get('thread_id')
        if thread_id and thread_id != 'all':
            queryset = queryset.filter(thread_id=thread_id)
            filters_applied['thread_id'] = thread_id

        # Фильтр по типу резьбы (наружная/внутренняя)
        thread_inner_outer_id = params.get('thread_inner_outer_id')
        if thread_inner_outer_id and thread_inner_outer_id != 'all':
            queryset = queryset.filter(thread_inner_outer_id=thread_inner_outer_id)
            filters_applied['thread_inner_outer_id'] = thread_inner_outer_id

        # Фильтр по активности
        is_active = params.get('is_active')
        if is_active is not None and is_active != '':
            if is_active in [True, 'true', 'True', 1, '1']:
                queryset = queryset.filter(is_active=True)
                filters_applied['is_active'] = True
            elif is_active in [False, 'false', 'False', 0, '0']:
                queryset = queryset.filter(is_active=False)
                filters_applied['is_active'] = False

        # Пагинация
        total = queryset.count()
        limit = params.get('limit', 100)
        offset = params.get('offset', 0)
        queryset = queryset[offset:offset + limit]

        # Формируем результат
        data = []
        for obj in queryset:
            data.append(obj.to_dict())

        return {
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертировать объект в словарь для API

        Returns:
            Dict: структурированные данные фитинга
        """
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'temp_min': self.temp_min,
            'temp_max': self.temp_max,
            'pipe_diameter': self.pipe_diameter,
            'flow_rate': float(self.flow_rate) if self.flow_rate else None,
            'noise_level': float(self.noise_level) if self.noise_level else None,
            'operating_pressure': float(self.operating_pressure) if self.operating_pressure else None,
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'brand': {
                'id': self.brand.id,
                'name': self.brand.name,
                'code': self.brand.code
            } if self.brand else None,
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': self.model_line.code
            } if self.model_line else None,
            'fitting_variety': {
                'id': self.fitting_variety.id,
                'name': self.fitting_variety.name,
                'code': self.fitting_variety.code
            } if self.fitting_variety else None,
            'body_material': {
                'id': self.body_material.id,
                'name': self.body_material.name
            } if self.body_material else None,
            'pipe_material': {
                'id': self.pipe_material.id,
                'name': self.pipe_material.name
            } if self.pipe_material else None,
            'thread': {
                'id': self.thread.id,
                'name': self.thread.name,
                'code': self.thread.code
            } if self.thread else None,
            'thread_inner_outer': {
                'id': self.thread_inner_outer.id,
                'name': self.thread_inner_outer.name,
                'code': self.thread_inner_outer.code
            } if self.thread_inner_outer else None,
        }

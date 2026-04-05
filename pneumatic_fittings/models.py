#pneumatic_fittings/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import StructuredDataMixin
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


'''


# )
# PowerSupplies, ExdOption, IpOption, BodyCoatingOption,BlinkerOption,SwitchesParameters, EnvTempParameters, \
# DigitalProtocolsSupportOption, ControlUnitInstalledOption,ActuatorType, ValveTypes, GearBoxTypes, \
# HandWheelInstalledOption, OperatingModeOption

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
    fitting_variety = models.ForeignKey(PneumaticFittingVariety, related_name='pneumatic_fitting_model_line_variety', blank=True,
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        help_text=_('Тип фитинга'),
                                        verbose_name=_("Тип"))

    body_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_model_line_body_material', blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    pipe_material = models.ForeignKey(MaterialGeneral, related_name='pneumatic_fitting_model_line_pipe_material', blank=True,
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
        null=True , blank=True , default=-40,
        help_text=_('Минимальная рабочая температура, °С') ,
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True , blank=True , default=120,
        help_text=_('Максимальная рабочая температура, °С') ,
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

class PneumaticFitting(StructuredDataMixin, models.Model):
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

    fitting_model_line= models.ForeignKey(PneumaticFittingModelLine, related_name='pneumatic_fitting_model_line', blank=True,
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

    #     body_material_specified = models.ForeignKey(MaterialSpecified, related_name='valve_line_body_material',
    #                                                 blank=True, null=True,
    #                                                 on_delete=models.SET_NULL,
    #                                                 help_text=_('Материал корпуса арматуры'),
    #                                                 verbose_name=_('Материал корпуса'))
    # work_temp_min = models.IntegerField(
    #     null=True , blank=True ,
    #     help_text=_('Минимальная рабочая температура, °С') ,
    #     verbose_name=_('Т раб мин, °С')
    # )
    # work_temp_max = models.IntegerField(
    #     null=True , blank=True ,
    #     help_text=_('Максимальная рабочая температура, °С') ,
    #     verbose_name=_('Т раб макс, °С')
    # ==================== ПОЛЯ ДЛЯ ГЛУШИТЕЛЕЙ ====================

    # Пропускная способность (л/мин или м³/ч)
    flow_rate = models.DecimalField(
        max_digits=10 ,
        decimal_places=2 ,
        blank=True , null=True ,
        verbose_name=_("Пропускная способность") ,
        help_text=_('Пропускная способность глушителя (л/мин)')
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
    class Meta:
        ordering = ['pipe_diameter', 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.fitting_model_line.work_temp_min}..{self.fitting_model_line.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.fitting_model_line.pressure_min}..{self.fitting_model_line.pressure_max}'

    def generated_model_name_description(self, name_or_description):
        """Сгенерировать название фитинга по шаблону из model_line"""
        if not self.fitting_model_line:
            return self.name or ""
        if name_or_description=='name':
            template = self.fitting_model_line.name_template
            if not template:
                print('Ошибка при формировании названия фитинга - в model_line нет шаблона')
                return self.name or ""
        else:
            template = self.fitting_model_line.description_template
            if not template:
                print('Ошибка при формировании описания фитинга - в model_line нет шаблона')
                return self.description or ""

        # Замена переменных
        replacements = {
            '{model_code}': self._get_value('code'),
            '{temperature_range}': self._get_value('temperature_range_display'),
            '{pressure_range}': self._get_value('pressure_range_display'),
            '{pipe_diameter}': self._get_value('pipe_diameter'),
            '{thread}': self._get_value('thread'),
            '{thread_inner_outer}': self._get_value('thread_inner_outer'),
        }

        # Заменяем все плейсхолдеры
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, str(value) if value else '')

        return result

    def __str__(self):
        return self.name

    def save(self , *args , **kwargs) :
        from django.core.exceptions import ValidationError

        # Получаем оригинальный объект
        original = None
        if self.pk :
            try :
                original = self.__class__._default_manager.get(pk=self.pk)
            except self.__class__.DoesNotExist :
                pass

        # Автозаполнение полей name description
        self.name = self.generated_model_name_description('name')
        self.description = self.generated_model_name_description('description')

        # Сохраняем
        super().save(*args , **kwargs)

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

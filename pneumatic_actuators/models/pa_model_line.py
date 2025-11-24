# pneumatic_actuators/models/pa_model_line.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError


from params.models import MountingPlateTypes , StemShapes , StemSize , ActuatorGearboxOutputType , IpOption , \
    BodyCoatingOption , ExdOption , EnvTempParameters , HandWheelInstalledOption
from pneumatic_actuators.models import PneumaticActuatorBody
from pneumatic_actuators.models.pa_params import PneumaticActuatorVariety, PneumaticActuatorConstructionVariety

from producers.models import Brands


class PneumaticActuatorModelLine(models.Model) :
    """
    Серия пневмоприводов - DA и SR -
    Объединяет в себе общие для всех моделей серии свойства
    и доступные опции
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название серии'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели корпуса привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    brand = models.ForeignKey(Brands , blank=True , null=True ,
                              related_name='pneumatic_model_line_brand' ,
                              on_delete=models.SET_NULL ,
                              help_text='Бренд производителя')
    default_output_type = \
        models.ForeignKey(ActuatorGearboxOutputType , blank=True , null=True ,
                          related_name='pneumatic_model_line_default_output_type' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Тип работы серии приводов'))

    pneumatic_actuator_construction_variety = \
        models.ForeignKey(PneumaticActuatorConstructionVariety , blank=True , null=True ,
                          related_name='pneumatic_model_line_pneumatic_actuator_variety' ,
                          on_delete=models.SET_NULL ,
                          verbose_name='' ,
                          help_text=_('Тип конструкции привода - кулисный или шестерня-рейка'))

    # Убираем прямые связи с опциями, используем through-модели
    default_hand_wheel = \
        models.ForeignKey(HandWheelInstalledOption , blank=True , null=True ,
                          related_name='pneumatic_model_line_default_hand_wheel' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Стандартно установленный ручной дублер для серии'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Серия моделей пневмоприводов')
        verbose_name_plural = _('Серии моделей пневмоприводов')

    def __str__(self) :
        return self.name

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ОПЦИЯМИ ====================
    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Автоматически определить имя поля родительского объекта"""
        # Ищем поле, которое ссылается на основную модель (не на справочники опций)
        parent_fields = []
        for field in cls._meta.fields :
            if isinstance(field , models.ForeignKey) :
                # Исключаем поля, которые ссылаются на справочники опций
                if (field.related_model and
                        field.related_model._meta.app_label == 'params' and
                        field.related_model._meta.model_name in ['ipoption' , 'exdoption' , 'bodycoatingoption']) :
                    continue
                # Исключаем поле id
                if field.name != 'id' :
                    parent_fields.append(field.name)

        # Возвращаем первое подходящее поле (обычно это model_line)
        return parent_fields[0] if parent_fields else None
    def ensure_all_default_options_exist(self) :
        """Создать все необходимые опции по умолчанию"""
        """Создать все необходимые опции по умолчанию с трассировкой"""
        import traceback
        print(">>> ensure_all_default_options_exist CALLED")
        print(f">>> For object: {self} (PK: {self.pk})")

        from .pa_options import (
            PneumaticTemperatureOption ,
            PneumaticIpOption ,
            PneumaticExdOption ,
            PneumaticBodyCoatingOption
        )

        option_classes = [
            PneumaticTemperatureOption ,
            PneumaticIpOption ,
            PneumaticExdOption ,
            PneumaticBodyCoatingOption
        ]
        for option_class in option_classes :
            print(f">>> Processing {option_class.__name__}")
            try :
                was_created = option_class.ensure_default_exists(self)
                print(f">>> {option_class.__name__}: was_created = {was_created}")
            except Exception as e :
                print(f">>> ERROR in {option_class.__name__}: {e}")
                import traceback
                traceback.print_exc()

        print(">>> ensure_all_default_options_exist COMPLETED")
        # for option_class in option_classes :
        #     option_class.ensure_default_exists(self)

    def get_default_temperature_option(self) :
        """Получить стандартную температурную опцию"""
        from .pa_options import PneumaticTemperatureOption
        return PneumaticTemperatureOption.get_or_create_default(self)

    def get_default_ip_option(self) :
        """Получить стандартную IP опцию"""
        from .pa_options import PneumaticIpOption
        return PneumaticIpOption.get_or_create_default(self)

    def get_default_exd_option(self) :
        """Получить стандартную Exd опцию"""
        from .pa_options import PneumaticExdOption
        return PneumaticExdOption.get_or_create_default(self)

    def get_default_body_coating_option(self) :
        """Получить стандартную опцию покрытия корпуса"""
        from .pa_options import PneumaticBodyCoatingOption
        return PneumaticBodyCoatingOption.get_or_create_default(self)

    # ==================== СВОЙСТВА ДЛЯ ШАБЛОНОВ И API ====================

    @property
    def temperature_options_list(self) :
        """Список всех температурных опций"""
        return self.temperature_options.all()

    @property
    def ip_options_list(self) :
        """Список всех IP опций"""
        return self.ip_options.all()

    @property
    def exd_options_list(self) :
        """Список всех Exd опций"""
        return self.exd_options.all()

    @property
    def body_coating_options_list(self) :
        """Список всех опций покрытия корпуса"""
        return self.body_coating_options.all()

    @property
    def default_temperature(self) :
        """Стандартная температурная опция"""
        return self.get_default_temperature_option()

    @property
    def default_ip(self) :
        """Стандартная IP опция"""
        return self.get_default_ip_option()

    @property
    def default_exd(self) :
        """Стандартная Exd опция"""
        return self.get_default_exd_option()

    @property
    def default_body_coating(self) :
        """Стандартная опция покрытия корпуса"""
        return self.get_default_body_coating_option()

    # ==================== ОТОБРАЖАЕМЫЕ СВОЙСТВА ====================

    @property
    def ip_display(self) :
        """Отображаемое имя стандартной IP опции"""
        default_ip = self.default_ip
        if default_ip and default_ip.ip_option :
            return default_ip.ip_option.name
        return "Не указано"

    @property
    def exd_display(self) :
        """Отображаемое имя стандартной Exd опции"""
        default_exd = self.default_exd
        if default_exd and default_exd.exd_option :
            return default_exd.exd_option.name
        return "Не указано"

    @property
    def body_coating_display(self) :
        """Отображаемое имя стандартной опции покрытия"""
        default_coating = self.default_body_coating
        if default_coating and default_coating.body_coating_option :
            return default_coating.body_coating_option.name
        return "Не указано"



    def get_option_info(self) :
        """Полная информация о всех опциях серии"""
        return {
            'temperature' : {
                'default' : self.default_temperature.get_option_info() if self.default_temperature else None ,
                'options' : [opt.get_option_info() for opt in self.temperature_options_list]
            } ,
            'ip' : {
                'default' : self.default_ip.get_option_info() if self.default_ip else None ,
                'options' : [opt.get_option_info() for opt in self.ip_options_list]
            } ,
            'exd' : {
                'default' : self.default_exd.get_option_info() if self.default_exd else None ,
                'options' : [opt.get_option_info() for opt in self.exd_options_list]
            } ,
            'body_coating' : {
                'default' : self.default_body_coating.get_option_info() if self.default_body_coating else None ,
                'options' : [opt.get_option_info() for opt in self.body_coating_options_list]
            }
        }

    def save(self , *args , **kwargs) :
        """Сохранение с трассировкой для диагностики"""
        import traceback
        print("=" * 50)
        print("SAVE METHOD CALLED")
        print(f"Object: {self}")
        print(f"PK: {self.pk}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")

        # Выводим значения всех полей
        print("FIELD VALUES:")
        for field in self._meta.fields :
            field_name = field.name
            field_value = getattr(self , field_name , None)
            print(f"  {field_name}: {field_value} (type: {type(field_value)})")

        # Выводим трассировку
        print("TRACEBACK:")
        for line in traceback.format_stack() :
            if "django" not in line and "lib" not in line :  # Фильтруем стандартные вызовы
                print(line.strip())

        print("=" * 50)

        # Вызываем оригинальный save
        is_new = self.pk is None
        super().save(*args , **kwargs)

        # После создания новой серии создаем опции по умолчанию
        if is_new :
            print("CREATING DEFAULT OPTIONS FOR NEW OBJECT")
            self.ensure_all_default_options_exist()

    def get_brand_name(self):
        """Название бренда"""
        return self.brand.name if self.brand else ""

    def get_construction_type(self):
        """Тип конструкции"""
        return str(self.pneumatic_actuator_construction_variety) if self.pneumatic_actuator_construction_variety else ""

    # Упрощенные методы для работы с опциями
    def _get_options_manager(self, relation_name):
        """Получить менеджер опций для доступа к методам BaseThroughOption"""
        options = getattr(self, relation_name, None)
        return options.first() if options and options.exists() else None

    # Общие свойства для всех типов опций
    @property
    def has_optional_options(self) :
        """Есть ли опционные исполнения (кроме стандартных)"""
        option_relations = [
            self.temperature_options_list ,
            self.ip_options_list ,
            self.exd_options_list ,
            self.body_coating_options_list
        ]

        for options in option_relations :
            if options.count() > 1 :
                return True
        return False

    # Удобные свойства для шаблонов и API
    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон стандартной температуры"""
        default_temp = self.default_temperature
        if default_temp :
            return default_temp.get_display_name()
        return "Не указано"

    @property
    def default_ip_display(self):
        """Отображаемое имя стандартной IP опции"""
        manager = self._get_options_manager('ip_options')
        if manager and manager.default_option:
            return manager.default_option.get_display_name()
        return "Не указано"

@receiver(post_save, sender=PneumaticActuatorModelLine)
def create_default_options(sender, instance, created, **kwargs):
    """Резервное создание опций по умолчанию (на случай если save не сработал)"""
    if created:
        # Вызываем метод модели для создания опций
        instance.ensure_all_default_options_exist()

# ======================================  Модель в серии ==================================
class PneumaticActuatorModelLineItem(models.Model) :
    """
    Модель в серии пневмоприводов - DA или SR -
    Объединяет в себе общие для всех моделей серии свойства
    и доступные опции
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название модели'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_line = \
        models.ForeignKey(PneumaticActuatorModelLine , blank=True , null=True ,
                          related_name='model_line_item_model_line' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Серия'))
    body = \
        models.ForeignKey(PneumaticActuatorBody , blank=True , null=True ,
                          related_name='pneumatic_model_line_item_body' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Корпус модели'))

    pneumatic_actuator_variety = \
        models.ForeignKey(PneumaticActuatorVariety , blank=True , null=True ,
                          related_name='pneumatic_model_line_item_actuator_variety' ,
                          on_delete=models.SET_NULL ,
                          verbose_name='DA/SR' ,
                          help_text=_('Вид пневмопривода - DA/SR'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Серия моделей пневмоприводов')
        verbose_name_plural = _('Серии моделей пневмоприводов')

    def __str__(self) :
        return self.name

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ОПЦИЯМИ ====================
    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Автоматически определить имя поля родительского объекта"""
        # Ищем поле, которое ссылается на основную модель (не на справочники опций)
        parent_fields = []
        for field in cls._meta.fields :
            if isinstance(field , models.ForeignKey) :
                # Исключаем поля, которые ссылаются на справочники опций
                if (field.related_model and
                        field.related_model._meta.app_label == 'params' and
                        field.related_model._meta.model_name in ['ipoption' , 'exdoption' , 'bodycoatingoption']) :
                    continue
                # Исключаем поле id
                if field.name != 'id' :
                    parent_fields.append(field.name)

        # Возвращаем первое подходящее поле (обычно это model_line)
        return parent_fields[0] if parent_fields else None

    # ==================== ГЕТТЕРЫ С ПРИОРИТЕТОМ ИЗ MODEL_LINE ИЛИ BODY ====================

    @property
    def brand(self) :
        """Бренд из model_line"""
        return self.model_line.brand if self.model_line else None

    @property
    def pneumatic_actuator_construction_variety(self) :
        """Тип конструкции из model_line"""
        return self.model_line.pneumatic_actuator_construction_variety if self.model_line else None

    @property
    def default_hand_wheel(self) :
        """Ручной дублер по умолчанию из model_line"""
        return self.model_line.default_hand_wheel if self.model_line else None

    @property
    def default_output_type(self) :
        """Тип работы по умолчанию из model_line"""
        return self.model_line.default_output_type if self.model_line else None

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ОПЦИЯМИ (С ПРИОРИТЕТОМ) ====================

    def get_default_temperature_option(self) :
        """Получить стандартную температурную опцию из model_line"""
        return self.model_line.get_default_temperature_option() if self.model_line else None

    def get_default_ip_option(self) :
        """Получить стандартную IP опцию из model_line"""
        return self.model_line.get_default_ip_option() if self.model_line else None

    def get_default_exd_option(self) :
        """Получить стандартную Exd опцию из model_line"""
        return self.model_line.get_default_exd_option() if self.model_line else None

    def get_default_body_coating_option(self) :
        """Получить стандартную опцию покрытия корпуса из model_line"""
        return self.model_line.get_default_body_coating_option() if self.model_line else None

    # ==================== СВОЙСТВА ДЛЯ ШАБЛОНОВ И API (С ПРИОРИТЕТОМ) ====================

    @property
    def temperature_options_list(self) :
        """Список всех температурных опций из model_line"""
        return self.model_line.temperature_options_list if self.model_line else None

    @property
    def ip_options_list(self) :
        """Список всех IP опций из model_line"""
        return self.model_line.ip_options_list if self.model_line else None

    @property
    def exd_options_list(self) :
        """Список всех Exd опций из model_line"""
        return self.model_line.exd_options_list if self.model_line else None

    @property
    def body_coating_options_list(self) :
        """Список всех опций покрытия корпуса из model_line"""
        return self.model_line.body_coating_options_list if self.model_line else None

    @property
    def default_temperature(self) :
        """Стандартная температурная опция из model_line"""
        return self.model_line.default_temperature if self.model_line else None

    @property
    def default_ip(self) :
        """Стандартная IP опция из model_line"""
        return self.model_line.default_ip if self.model_line else None

    @property
    def default_exd(self) :
        """Стандартная Exd опция из model_line"""
        return self.model_line.default_exd if self.model_line else None

    @property
    def default_body_coating(self) :
        """Стандартная опция покрытия корпуса из model_line"""
        return self.model_line.default_body_coating if self.model_line else None

    # ==================== ОТОБРАЖАЕМЫЕ СВОЙСТВА (С ПРИОРИТЕТОМ) ====================

    @property
    def ip_display(self) :
        """Отображаемое имя стандартной IP опции из model_line"""
        return self.model_line.ip_display if self.model_line else "Не указано"

    @property
    def exd_display(self) :
        """Отображаемое имя стандартной Exd опции из model_line"""
        return self.model_line.exd_display if self.model_line else "Не указано"

    @property
    def body_coating_display(self) :
        """Отображаемое имя стандартной опции покрытия из model_line или своя"""
        return self.model_line.body_coating_display if self.model_line else "Не указано"

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон стандартной температуры из model_line"""
        return self.model_line.temperature_range_display if self.model_line else "Не указано"

    @property
    def default_ip_display(self) :
        """Отображаемое имя стандартной IP опции из model_line"""
        return self.model_line.default_ip_display if self.model_line else "Не указано"

    # ==================== ФУНКЦИЯ КОПИРОВАНИЯ ====================

    def create_copy(self) :
        """Создать копию элемента с добавлением ' Копия' к name и code"""
        # Создаем копию объекта
        copy_obj = PneumaticActuatorModelLineItem()

        # Копируем все поля кроме первичного ключа
        for field in self._meta.fields :
            if field.name not in ['id' , 'pk'] :
                setattr(copy_obj , field.name , getattr(self , field.name))

        # Добавляем " Копия" к name и code
        if copy_obj.name :
            copy_obj.name = f"{copy_obj.name} Копия"
        if copy_obj.code :
            copy_obj.code = f"{copy_obj.code} Копия"

        # Сохраняем копию
        copy_obj.save()

        # Копируем связанные опции
        self._copy_related_options(copy_obj)

        return copy_obj

    def _copy_related_options(self , copy_obj) :
        """Копировать связанные опции для скопированного объекта"""
        # Копируем температурные опции
        for temp_opt in self.temperature_options.all() :
            temp_opt.pk = None
            temp_opt.model_line_item = copy_obj
            temp_opt.save()

        # Копируем IP опции
        for ip_opt in self.ip_options.all() :
            ip_opt.pk = None
            ip_opt.model_line_item = copy_obj
            ip_opt.save()

        # Копируем Exd опции
        for exd_opt in self.exd_options.all() :
            exd_opt.pk = None
            exd_opt.model_line_item = copy_obj
            exd_opt.save()

        # Копируем опции покрытия
        for coating_opt in self.body_coating_options.all() :
            coating_opt.pk = None
            coating_opt.model_line_item = copy_obj
            coating_opt.save()

    # ==================== МЕТОД ДЛЯ АДМИНКИ ====================

    def copy_item_action(self) :
        """Метод для вызова из админки"""
        from django.urls import reverse
        from django.utils.html import format_html
        return format_html(
            '<a class="button" href="{}">Копировать</a>' ,
            reverse('admin:copy_model_line_item' , args=[self.pk])
        )

    def _create_safety_position_options(self) :
        """Создать опции положения безопасности"""
        from .pa_options import PneumaticSafetyPositionOption
        from params.models import SafetyPositionOption

        # Получаем опции безопасности
        nc_option = SafetyPositionOption.objects.filter(code='NC').first()
        no_option = SafetyPositionOption.objects.filter(code='NO').first()

        if not nc_option or not no_option :
            return

        # Создаем опцию NC как дефолтную
        PneumaticSafetyPositionOption.objects.create(
            model_line_item=self ,
            safety_position=nc_option ,
            encoding='NC' ,
            description='Нормально закрытый' ,
            is_default=True ,
            sorting_order=0 ,
            is_active=True
        )

        # Создаем опцию NO
        PneumaticSafetyPositionOption.objects.create(
            model_line_item=self ,
            safety_position=no_option ,
            encoding='NO' ,
            description='Нормально открытый' ,
            is_default=False ,
            sorting_order=1 ,
            is_active=True
        )

    def _create_springs_qty_options(self) :
        """Создать опции количества пружин на основе BodyThrustTorqueTable"""
        from .pa_options import PneumaticSpringsQtyOption
        from .pa_params import PneumaticActuatorSpringsQty

        if not self.body :
            return

        # Определяем тип привода
        is_da = (self.pneumatic_actuator_variety and
                 self.pneumatic_actuator_variety.code == 'DA')

        if is_da :
            # Для DA приводов - только опция с кодом DA
            da_spring = PneumaticActuatorSpringsQty.objects.filter(code='DA').first()
            if da_spring :
                PneumaticSpringsQtyOption.objects.create(
                    model_line_item=self ,
                    springs_qty=da_spring ,
                    encoding='DA' ,
                    description='Двойного действия' ,
                    is_default=True ,
                    sorting_order=0 ,
                    is_active=True
                )
        else :
            # Для SR приводов - все пружины из BodyThrustTorqueTable для этого body
            from pneumatic_actuators.models.pa_torque import BodyThrustTorqueTable

            # Получаем уникальные spring_qty для этого body
            spring_qtys = BodyThrustTorqueTable.objects.filter(
                body=self.body
            ).exclude(
                spring_qty__isnull=True
            ).values_list(
                'spring_qty' , flat=True
            ).distinct()

            # Создаем опции для каждой пружины
            default_set = False
            for i , spring_qty_id in enumerate(spring_qtys) :
                try :
                    spring_qty = PneumaticActuatorSpringsQty.objects.get(pk=spring_qty_id)

                    # Определяем дефолтную опцию
                    is_default = False
                    if not default_set :
                        # Первая опция становится дефолтной
                        is_default = True
                        default_set = True
                    elif spring_qty.code == '12' :
                        # Опция с кодом 12 становится дефолтной если есть
                        is_default = True

                    PneumaticSpringsQtyOption.objects.create(
                        model_line_item=self ,
                        springs_qty=spring_qty ,
                        encoding=spring_qty.code ,
                        description=spring_qty.name ,
                        is_default=is_default ,
                        sorting_order=i ,
                        is_active=True
                    )
                except PneumaticActuatorSpringsQty.DoesNotExist :
                    continue

            # Если не нашли подходящих пружин, создаем базовую опцию
            if not default_set :
                default_spring = PneumaticActuatorSpringsQty.objects.filter(code='12').first()
                if default_spring :
                    PneumaticSpringsQtyOption.objects.create(
                        model_line_item=self ,
                        springs_qty=default_spring ,
                        encoding='12' ,
                        description=default_spring.name ,
                        is_default=True ,
                        sorting_order=0 ,
                        is_active=True
                    )

    copy_item_action.short_description = "Копировать элемент"

# ==================== СИГНАЛ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ОПЦИЙ ====================

@receiver(post_save, sender=PneumaticActuatorModelLineItem)
def create_model_line_item_options(sender, instance, created, **kwargs):
    """Создать опции безопасности и количества пружин после создания элемента"""
    if created:
        instance._create_safety_position_options()
        instance._create_springs_qty_options()
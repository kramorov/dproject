# pneumatic_actuators/models/pa_model_line.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError

from cert_doc.models import AbstractCertRelation
from params.models import MountingPlateTypes , StemShapes , StemSize , ActuatorGearboxOutputType , IpOption , \
    BodyCoatingOption , ExdOption , EnvTempParameters , HandWheelInstalledOption
from pneumatic_actuators.models import PneumaticActuatorBody
from pneumatic_actuators.models.pa_params import PneumaticActuatorVariety, PneumaticActuatorConstructionVariety

from producers.models import Brands
import logging

logger = logging.getLogger(__name__)

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
    model_item_code_template = models.CharField(max_length=500 ,blank=True , null=True ,
                            verbose_name=_("Шаблон артикула") ,
                            help_text=_('Шаблон артикула для конкретной модели серии'))
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
        verbose_name = _('Модель пневмопривода')
        verbose_name_plural = _('Модели пневмоприводов в серии')

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

    def create_copy(self):
        """Создать копию элемента с добавлением ' Копия' к name и code"""
        # Создаем копию объекта
        copy_obj = PneumaticActuatorModelLineItem()

        # Копируем все поля кроме первичного ключа
        for field in self._meta.fields:
            if field.name not in ['id', 'pk']:
                setattr(copy_obj, field.name, getattr(self, field.name))

        # Добавляем " Копия" к name и code
        if copy_obj.name:
            copy_obj.name = f"{copy_obj.name} Копия"
        if copy_obj.code:
            copy_obj.code = f"{copy_obj.code} Копия"

        # Сохраняем копию
        copy_obj.save()

        # Копируем связанные опции
        self._copy_related_options(copy_obj)

        return copy_obj

    def _copy_related_options(self, copy_obj):
        """Копировать связанные опции для скопированного объекта"""
        # Список всех through-моделей для копирования
        through_models = [
            ('safety_position_option_model_line_item', None),
            ('springs_qty_option_model_line_item', None),
        ]

        for relation_name, fk_field_name in through_models:
            if hasattr(self, relation_name):
                related_objects = getattr(self, relation_name).all()
                for obj in related_objects:
                    obj.pk = None

                    # Определяем поле для связи
                    if fk_field_name:
                        setattr(obj, fk_field_name, copy_obj)
                    else:
                        # Если поле не указано, используем стандартное имя
                        setattr(obj, 'model_line_item', copy_obj)

                    # Добавляем суффикс к encoding для уникальности
                    if hasattr(obj, 'encoding') and obj.encoding:
                        obj.encoding = f"{obj.encoding}_copy"

                    obj.save()

    def _create_safety_position_options(self):
        """Создать опции положения безопасности, если их еще нет"""
        from .pa_options import PneumaticSafetyPositionOption
        from params.models import SafetyPositionOption

        logger.debug(f"Проверка опций безопасности для модели: {self.name} (id={self.id})")
        if self.pneumatic_actuator_variety.code=='DA':
            logger.debug(f"Для модели: {self.name} (id={self.id}) опции безопасности не создаем, так как модель DA")
            return False
        # Проверяем, есть ли уже опции для этой модели
        existing_options = PneumaticSafetyPositionOption.objects.filter(model_line_item=self)
        if existing_options.exists():
            logger.debug(
                f"Опции безопасности уже существуют для модели {self.name}: {existing_options.count()} записей")
            return False

        logger.info(f"Создание опций безопасности для модели: {self.name}")

        # Получаем опции безопасности
        nc_option = SafetyPositionOption.objects.filter(code='nc').first()
        no_option = SafetyPositionOption.objects.filter(code='no').first()

        if not nc_option:
            logger.error("Не найдена опция безопасности NC в базе данных")
            return False
        if not no_option:
            logger.error("Не найдена опция безопасности NO в базе данных")
            return False

        try:
            # Создаем опцию NC как дефолтную
            nc_safety_option = PneumaticSafetyPositionOption.objects.create(
                model_line_item=self,
                safety_position=nc_option,
                encoding='',
                description='Нормально закрытый',
                is_default=True,
                sorting_order=0,
                is_active=True
            )
            logger.debug(f"Создана опция безопасности NC: {nc_safety_option}")

            # Создаем опцию NO
            no_safety_option = PneumaticSafetyPositionOption.objects.create(
                model_line_item=self,
                safety_position=no_option,
                encoding='NO',
                description='Нормально открытый',
                is_default=False,
                sorting_order=1,
                is_active=True
            )
            logger.debug(f"Создана опция безопасности NO: {no_safety_option}")

            logger.info(f"Успешно созданы 2 опции безопасности для модели {self.name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при создании опций безопасности для модели {self.name}: {str(e)}", exc_info=True)
            return False

    def _create_springs_qty_options(self):
        """Создать опции количества пружин, если их еще нет"""
        from .pa_options import PneumaticSpringsQtyOption
        from .pa_params import PneumaticActuatorSpringsQty

        logger.debug(f"Проверка опций количества пружин для модели: {self.name} (id={self.id})")

        # Проверяем, есть ли уже опции для этой модели
        existing_options = PneumaticSpringsQtyOption.objects.filter(model_line_item=self)
        if existing_options.exists():
            logger.debug(
                f"Опции количества пружин уже существуют для модели {self.name}: {existing_options.count()} записей")
            return False

        logger.info(f"Создание опций количества пружин для модели: {self.name}")

        if not self.body:
            logger.warning(f"Не указан корпус для модели {self.name}, невозможно создать опции пружин")
            return False

        # Определяем тип привода
        is_da = (self.pneumatic_actuator_variety and
                 self.pneumatic_actuator_variety.code == 'DA')

        logger.debug(
            f"Тип привода для модели {self.name}: {'DA' if is_da else 'SR'}, корпус: {self.body.name if self.body else 'не указан'}")

        try:
            if is_da:
                # Для DA приводов - только опция с кодом DA
                da_spring = PneumaticActuatorSpringsQty.objects.filter(code='DA').first()
                if da_spring:
                    da_option = PneumaticSpringsQtyOption.objects.create(
                        model_line_item=self,
                        springs_qty=da_spring,
                        encoding='DA',
                        description='Двойного действия',
                        is_default=True,
                        sorting_order=0,
                        is_active=True
                    )
                    logger.debug(f"Создана опция пружин DA: {da_option}")
                    logger.info(f"Успешно создана 1 опция пружин DA для модели {self.name}")
                    return True
                else:
                    logger.error("Не найдена опция пружин DA в базе данных")
                    return False
            else:
                # Для SR приводов - все пружины из BodyThrustTorqueTable для этого body
                from pneumatic_actuators.models.pa_torque import BodyThrustTorqueTable

                # Получаем уникальные spring_qty для этого body
                spring_qtys = BodyThrustTorqueTable.objects.filter(
                    body=self.body
                ).exclude(
                    spring_qty__isnull=True
                ).exclude(
                    spring_qty__code='DA'  # Исключаем пружины с кодом 'DA'
                ).values_list(
                    'spring_qty', flat=True
                ).distinct()

                logger.debug(f"Найдено уникальных spring_qty для корпуса {self.body.name}: {list(spring_qtys)}")

                created_count = 0
                default_set = False

                for i, spring_qty_id in enumerate(spring_qtys):
                    try:
                        spring_qty = PneumaticActuatorSpringsQty.objects.get(pk=spring_qty_id)
                        logger.debug(f"Обработка пружины: {spring_qty.name} (id={spring_qty_id})")

                        # Определяем дефолтную опцию
                        is_default = False
                        if spring_qty.code == '12':
                            # Опция с кодом 12 становится дефолтной если есть
                            is_default = True
                            default_set = True
                            logger.debug(f"Установлена пружина {spring_qty.name} как дефолтная (код 12)")

                        spring_option = PneumaticSpringsQtyOption.objects.create(
                            model_line_item=self,
                            springs_qty=spring_qty,
                            encoding=spring_qty.code,
                            description=spring_qty.name,
                            is_default=is_default,
                            sorting_order=i,
                            is_active=True
                        )
                        created_count += 1
                        logger.debug(f"Создана опция пружин: {spring_option}")

                    except PneumaticActuatorSpringsQty.DoesNotExist:
                        logger.warning(f"Пружина с id={spring_qty_id} не найдена в базе данных")
                        continue
                    except Exception as e:
                        logger.error(f"Ошибка при создании опции пружины {spring_qty_id}: {str(e)}")
                        continue

                # Если не нашли подходящих пружин, создаем базовую опцию
                if created_count == 0:
                    logger.warning(f"Не найдено подходящих пружин для корпуса {self.body.name}, создаем базовую опцию")
                    default_spring = PneumaticActuatorSpringsQty.objects.filter(code='12').first()
                    if default_spring:
                        default_option = PneumaticSpringsQtyOption.objects.create(
                            model_line_item=self,
                            springs_qty=default_spring,
                            encoding='12',
                            description=default_spring.name,
                            is_default=True,
                            sorting_order=0,
                            is_active=True
                        )
                        created_count = 1
                        logger.debug(f"Создана базовая опция пружин: {default_option}")

                logger.info(f"Успешно создано {created_count} опций пружин для модели {self.name}")
                return created_count > 0

        except Exception as e:
            logger.error(f"Ошибка при создании опций пружин для модели {self.name}: {str(e)}", exc_info=True)
            return False

    # Добавляем метод для ручной проверки и создания опций
    def ensure_options_exist(self):
        """Гарантировать существование опций (для вызова вручную)"""
        logger.info(f"Ручной вызов ensure_options_exist для модели: {self.name} (id={self.id})")

        from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
        safety_exists = PneumaticSafetyPositionOption.objects.filter(model_line_item=self).exists()
        from pneumatic_actuators.models.pa_options import PneumaticSpringsQtyOption
        springs_exists = PneumaticSpringsQtyOption.objects.filter(model_line_item=self).exists()

        logger.info(f"Текущее состояние опций - безопасность: {safety_exists}, пружины: {springs_exists}")

        if not safety_exists:
            logger.info("Создание отсутствующих опций безопасности...")
            self._create_safety_position_options()

        if not springs_exists:
            logger.info("Создание отсутствующих опций пружин...")
            self._create_springs_qty_options()

        logger.info(f"Завершение ensure_options_exist для модели: {self.name}")

# ==================== СИГНАЛ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ОПЦИЙ ====================

@receiver(post_save, sender=PneumaticActuatorModelLineItem)
def create_model_line_item_options(sender, instance, created, **kwargs):
    """Создать опции безопасности и количества пружин после создания/обновления элемента"""
    logger.info(
        f"Сигнал post_save для PneumaticActuatorModelLineItem: id={instance.id}, name='{instance.name}', created={created}")

    try:
        from .pa_options import PneumaticSafetyPositionOption, PneumaticSpringsQtyOption

        # Проверяем существующие опции
        safety_options_exist = PneumaticSafetyPositionOption.objects.filter(model_line_item=instance).exists()
        springs_options_exist = PneumaticSpringsQtyOption.objects.filter(model_line_item=instance).exists()

        logger.info(
            f"Текущее состояние опций для модели {instance.name}: безопасность={safety_options_exist}, пружины={springs_options_exist}")

        # Создаем опции, если их нет (независимо от created)
        if not safety_options_exist:
            logger.info(f"Создание отсутствующих опций безопасности для модели: {instance.name}")
            safety_created = instance._create_safety_position_options()
            if safety_created:
                logger.info(f"Успешно созданы опции положения безопасности для модели: {instance.name}")
            else:
                logger.warning(f"Не удалось создать опции положения безопасности для модели: {instance.name}")
        else:
            logger.debug(f"Опции безопасности уже существуют для модели: {instance.name}")

        if not springs_options_exist:
            logger.info(f"Создание отсутствующих опций количества пружин для модели: {instance.name}")
            springs_created = instance._create_springs_qty_options()
            if springs_created:
                logger.info(f"Успешно созданы опции количества пружин для модели: {instance.name}")
            else:
                logger.warning(f"Не удалось создать опции количества пружин для модели: {instance.name}")
        else:
            logger.debug(f"Опции количества пружин уже существуют для модели: {instance.name}")

        # Дополнительная проверка для новых моделей
        if created and (safety_options_exist or springs_options_exist):
            logger.info(
                f"Модель создана, но некоторые опции уже существуют: безопасность={safety_options_exist}, пружины={springs_options_exist}")

        logger.info(f"Завершение обработки опций для модели: {instance.name}")

    except Exception as e:
        logger.error(f"Ошибка при создании/проверке опций для модели {instance.name}: {str(e)}", exc_info=True)

class PneumaticActuatorModelLineCertRelation(AbstractCertRelation) :
    """
    Связь сертификатов с сериями пневмоприводов.
    """
    model_line = models.ForeignKey(
        PneumaticActuatorModelLine,  # Замените на реальный путь к модели Project
        on_delete=models.CASCADE ,
        verbose_name=_("Проект") ,
        related_name='cert_relations'
    )

    class Meta(AbstractCertRelation.Meta) :
        verbose_name = _("Связь сертификата с серией пневмоприводов")
        verbose_name_plural = _("Связи сертификатов с сериями пневмоприводов")
        unique_together = ['cert_data' , 'model_line']
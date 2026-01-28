# electric_actuators/models/ea_model_line_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from typing import List , Optional , Tuple , Any , Dict , Union
from django.core.exceptions import ValidationError

from cert_doc.models import AbstractCertRelation
from core.models import StructuredDataMixin
from params.models import MountingPlateTypes , StemShapes , StemSize , ActuatorGearboxOutputType , IpOption , \
    BodyCoatingOption , ExdOption , EnvTempParameters , HandWheelInstalledOption
from pneumatic_actuators.models import PneumaticActuatorBody
from pneumatic_actuators.models.pa_options import PneumaticHandWheelOption
from pneumatic_actuators.models.pa_params import PneumaticActuatorVariety , PneumaticActuatorConstructionVariety

from producers.models import Brands
import logging

logger = logging.getLogger(__name__)

# ======================================  Модель в серии ==================================
class ElectricActuatorModelLineItem(models.Model) :
    """
    Модель в серии электроприводов - DA или SR -
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
        models.ForeignKey(ElectricActuatorModelLine , blank=True , null=True ,
                          related_name='model_line_item_model_line' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Серия'))
    body = \
        models.ForeignKey(ElectricActuatorBody , blank=True , null=True ,
                          related_name='electric_model_line_item_body' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Корпус модели'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Модель пневмопривода')
        verbose_name_plural = _('Модели пневмоприводов в серии')

    def __str__(self) :
        return self.name

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
    def default_output_type(self) :
        """Тип работы по умолчанию из model_line"""
        return self.model_line.default_output_type if self.model_line else None

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
        # Список всех through-моделей для копирования
        through_models = [
            ('safety_position_option_model_line_item' , None) ,
            ('springs_qty_option_model_line_item' , None) ,
        ]

        for relation_name , fk_field_name in through_models :
            if hasattr(self , relation_name) :
                related_objects = getattr(self , relation_name).all()
                for obj in related_objects :
                    obj.pk = None

                    # Автоматически находим поле ForeignKey к модели
                    for field in obj._meta.fields :
                        if isinstance(field , models.ForeignKey) :
                            # Проверяем, ссылается ли поле на нужную модель
                            if field.related_model == PneumaticActuatorModelLineItem :
                                setattr(obj , field.name , copy_obj)
                                break

                    # Добавляем суффикс к encoding для уникальности
                    if hasattr(obj , 'encoding') and obj.encoding :
                        obj.encoding = f"{obj.encoding}_copy"

                    obj.save()

    def _create_safety_position_options(self) :
        """Создать опции положения безопасности, если их еще нет"""
        from .pa_options import PneumaticSafetyPositionOption
        from params.models import SafetyPositionOption

        logger.debug(f"Проверка опций безопасности для модели: {self.name} (id={self.id})")
        if self.pneumatic_actuator_variety.code == 'DA' :
            logger.debug(f"Для модели: {self.name} (id={self.id}) опции безопасности не создаем, так как модель DA")
            return False
        # Проверяем, есть ли уже опции для этой модели
        existing_options = PneumaticSafetyPositionOption.objects.filter(model_line_item=self)
        if existing_options.exists() :
            logger.debug(
                f"Опции безопасности уже существуют для модели {self.name}: {existing_options.count()} записей")
            return False

        logger.info(f"Создание опций безопасности для модели: {self.name}")

        # Получаем опции безопасности
        from pneumatic_actuators.models import SAFETY_POSITION_NC_DEFAULT_CODE
        nc_option = SafetyPositionOption.objects.filter(code=SAFETY_POSITION_NC_DEFAULT_CODE).first()
        from pneumatic_actuators.models import SAFETY_POSITION_NO_DEFAULT_CODE
        no_option = SafetyPositionOption.objects.filter(code=SAFETY_POSITION_NO_DEFAULT_CODE).first()
        from pneumatic_actuators.models import SAFETY_POSITION_FL_DEFAULT_CODE
        fl_option = SafetyPositionOption.objects.filter(code=SAFETY_POSITION_FL_DEFAULT_CODE).first()

        if not nc_option :
            logger.error("Не найдена опция безопасности NC в базе данных")
            return False
        if not no_option :
            logger.error("Не найдена опция безопасности NO в базе данных")
            return False
        if not fl_option :
            logger.error("Не найдена опция безопасности NO в базе данных")
            return False

        try :
            # Создаем опцию NC как дефолтную
            nc_safety_option = PneumaticSafetyPositionOption.objects.create(
                model_line_item=self ,
                safety_position=nc_option ,
                encoding='' ,
                description='Нормально закрытый' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
            logger.debug(f"Создана опция безопасности NC: {nc_safety_option}")

            # Создаем опцию NO
            no_safety_option = PneumaticSafetyPositionOption.objects.create(
                model_line_item=self ,
                safety_position=no_option ,
                encoding='NO' ,
                description='Нормально открытый' ,
                is_default=False ,
                sorting_order=1 ,
                is_active=True
            )
            logger.debug(f"Создана опция безопасности NO: {no_safety_option}")

            logger.info(f"Успешно созданы 2 опции безопасности для модели {self.name}")
            return True

        except Exception as e :
            logger.error(f"Ошибка при создании опций безопасности для модели {self.name}: {str(e)}" , exc_info=True)
            return False

    def _create_springs_qty_options(self) :
        """Создать опции количества пружин, если их еще нет"""
        from .pa_options import PneumaticSpringsQtyOption
        from .pa_params import PneumaticActuatorSpringsQty

        logger.debug(f"Проверка опций количества пружин для модели: {self.name} (id={self.id})")

        # Проверяем, есть ли уже опции для этой модели
        existing_options = PneumaticSpringsQtyOption.objects.filter(model_line_item=self)
        if existing_options.exists() :
            logger.debug(
                f"Опции количества пружин уже существуют для модели {self.name}: {existing_options.count()} записей")
            return False

        logger.info(f"Создание опций количества пружин для модели: {self.name}")

        if not self.body :
            logger.warning(f"Не указан корпус для модели {self.name}, невозможно создать опции пружин")
            return False

        # Определяем тип привода
        is_da = (self.pneumatic_actuator_variety and
                 self.pneumatic_actuator_variety.code == 'DA')

        logger.debug(
            f"Тип привода для модели {self.name}: {'DA' if is_da else 'SR'}, корпус: {self.body.name if self.body else 'не указан'}")

        try :
            if is_da :
                # Для DA приводов - только опция с кодом DA
                da_spring = PneumaticActuatorSpringsQty.objects.filter(code='DA').first()
                if da_spring :
                    da_option = PneumaticSpringsQtyOption.objects.create(
                        model_line_item=self ,
                        springs_qty=da_spring ,
                        encoding='DA' ,
                        description='Двойного действия' ,
                        is_default=True ,
                        sorting_order=0 ,
                        is_active=True
                    )
                    logger.debug(f"Создана опция пружин DA: {da_option}")
                    logger.info(f"Успешно создана 1 опция пружин DA для модели {self.name}")
                    return True
                else :
                    logger.error("Не найдена опция пружин DA в базе данных")
                    return False
            else :
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
                    'spring_qty' , flat=True
                ).distinct()

                logger.debug(f"Найдено уникальных spring_qty для корпуса {self.body.name}: {list(spring_qtys)}")

                created_count = 0
                default_set = False

                for i , spring_qty_id in enumerate(spring_qtys) :
                    try :
                        spring_qty = PneumaticActuatorSpringsQty.objects.get(pk=spring_qty_id)
                        logger.debug(f"Обработка пружины: {spring_qty.name} (id={spring_qty_id})")

                        # Определяем дефолтную опцию
                        is_default = False
                        if spring_qty.code == '12' :
                            # Опция с кодом 12 становится дефолтной если есть
                            is_default = True
                            default_set = True
                            logger.debug(f"Установлена пружина {spring_qty.name} как дефолтная (код 12)")

                        spring_option = PneumaticSpringsQtyOption.objects.create(
                            model_line_item=self ,
                            springs_qty=spring_qty ,
                            encoding=spring_qty.code ,
                            description=spring_qty.name ,
                            is_default=is_default ,
                            sorting_order=i ,
                            is_active=True
                        )
                        created_count += 1
                        logger.debug(f"Создана опция пружин: {spring_option}")

                    except PneumaticActuatorSpringsQty.DoesNotExist :
                        logger.warning(f"Пружина с id={spring_qty_id} не найдена в базе данных")
                        continue
                    except Exception as e :
                        logger.error(f"Ошибка при создании опции пружины {spring_qty_id}: {str(e)}")
                        continue

                # Если не нашли подходящих пружин, создаем базовую опцию
                if created_count == 0 :
                    logger.warning(f"Не найдено подходящих пружин для корпуса {self.body.name}, создаем базовую опцию")
                    default_spring = PneumaticActuatorSpringsQty.objects.filter(code='12').first()
                    if default_spring :
                        default_option = PneumaticSpringsQtyOption.objects.create(
                            model_line_item=self ,
                            springs_qty=default_spring ,
                            encoding='12' ,
                            description=default_spring.name ,
                            is_default=True ,
                            sorting_order=0 ,
                            is_active=True
                        )
                        created_count = 1
                        logger.debug(f"Создана базовая опция пружин: {default_option}")

                logger.info(f"Успешно создано {created_count} опций пружин для модели {self.name}")
                return created_count > 0

        except Exception as e :
            logger.error(f"Ошибка при создании опций пружин для модели {self.name}: {str(e)}" , exc_info=True)
            return False

    # Добавляем метод для ручной проверки и создания опций
    def ensure_options_exist(self) :
        """Гарантировать существование опций через get_or_create_default"""
        logger.info(f"Ручной вызов ensure_options_exist для модели: {self.name} (id={self.id})")

        from pneumatic_actuators.models.pa_options import (
            PneumaticSafetyPositionOption ,
            PneumaticSpringsQtyOption
        )

        # Используем get_or_create_default для получения/создания дефолтных опций
        safety_default = PneumaticSafetyPositionOption.get_or_create_default(self)
        springs_default = PneumaticSpringsQtyOption.get_or_create_default(self)

        logger.info(
            f"Опции безопасности: {'создана' if safety_default else 'не создана'}, "
            f"Пружины: {'создана' if springs_default else 'не создана'}"
        )

        logger.info(f"Завершение ensure_options_exist для модели: {self.name}")
        return safety_default or springs_default


# ==================== СИГНАЛ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ОПЦИЙ ====================

@receiver(post_save , sender=PneumaticActuatorModelLineItem)
def create_model_line_item_options(sender , instance , created , **kwargs) :
    """Создать дефолтные опции после создания элемента"""
    logger.info(
        f"Сигнал post_save для PneumaticActuatorModelLineItem: id={instance.id}, name='{instance.name}', created={created}")

    # Создаем дефолтные опции только если они нужны
    from .pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption

    # Проверяем, есть ли уже опции
    safety_exists = PneumaticSafetyPositionOption.objects.filter(model_line_item=instance).exists()
    springs_exists = PneumaticSpringsQtyOption.objects.filter(model_line_item=instance).exists()

    # Создаем только дефолтные опции, если их нет
    if not safety_exists :
        default_safety = PneumaticSafetyPositionOption.get_or_create_default(instance)
        logger.info(f"Создана дефолтная опция безопасности: {default_safety}")

    if not springs_exists :
        default_springs = PneumaticSpringsQtyOption.get_or_create_default(instance)
        logger.info(f"Создана дефолтная опция пружин: {default_springs}")
#

class ElectricActuatorModelLineCertRelation(AbstractCertRelation) :
    """
    Связь сертификатов с сериями пневмоприводов.
    """
    model_line = models.ForeignKey(
        ElectricActuatorModelLine ,  # Замените на реальный путь к модели Project
        on_delete=models.CASCADE ,
        verbose_name=_("Серия пневмоприводов") ,
        related_name='cert_data_model_line'
    )

    class Meta(AbstractCertRelation.Meta) :
        verbose_name = _("Связь сертификата с серией пневмоприводов")
        verbose_name_plural = _("Связи сертификатов с сериями пневмоприводов")
        unique_together = ['cert_data' , 'model_line']

    def get_related_object(self) :
        return self.model_line
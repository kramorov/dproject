# options/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List , Optional , Tuple , Any , Dict , Union

import logging

# from electric_actuators.models import CableGlandHolesSet

logger = logging.getLogger(__name__)


class BaseThroughOptionNoDefault(models.Model) :
    """Базовый абстрактный класс для всех сквозных опций"""
    encoding = models.CharField(
        max_length=50 ,
        blank=True ,
        verbose_name=_("Кодировка") ,
        help_text=_("Код опции для подстановки в артикул")
    )
    description = models.TextField(
        blank=True ,
        verbose_name=_("Описание") ,
        help_text=_("Дополнительное описание этой опции")
    )
    sorting_order = models.IntegerField(
        default=0 ,
        verbose_name=_("Порядок сортировки")
    )
    is_active = models.BooleanField(
        default=True ,
        verbose_name=_("Активно")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _get_parent_object(self) -> Optional[models.Model] :
        """Получить родительский объект"""
        parent_field = self._get_parent_field_name()
        return getattr(self , parent_field , None) if parent_field else None

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Автоматически определить имя поля родительского объекта"""
        for field in cls._meta.fields :
            if isinstance(field , models.ForeignKey) and field.name != 'id' :
                return field.name
        return None

    def get_option_info(self , option_instance: Optional['BaseThroughOption'] = None) -> Dict[str , Any] :
        """Полная информация об опции"""
        current_instance = option_instance or self
        return {
            'id' : current_instance.id ,
            'encoding' : current_instance.encoding ,
            'description' : current_instance.description ,
            'display_name' : str(current_instance) ,
            'is_default' : current_instance.is_default ,
            'is_active' : current_instance.is_active ,
            'sorting_order' : current_instance.sorting_order ,
            'has_encoding' : bool(current_instance.encoding and current_instance.encoding.strip()) ,
        }

    # ==================== СВОЙСТВА ====================

    @property
    def options_list(self) -> List[models.Model] :
        """Все доступные опции для родительского объекта"""
        parent = self._get_parent_object()
        if not parent :
            return []
        parent_field = self._get_parent_field_name()
        if not parent_field :
            return []
        return list(self.__class__.objects.filter(**{parent_field : parent , 'is_active' : True}))

    def is_option_allowed(self , option_to_check) -> bool :
        """
        Проверяет, входит ли переданная опция в список допустимых опций для этого родительского объекта.

        Args:
            option_to_check: Экземпляр опции для проверки
                             (может быть id, экземпляр модели или None)

        Returns:
            bool: True если опция допустима, False если нет
        """
        if option_to_check is None :
            return True  # None всегда допустим (опциональная опция)

        # Получаем родительский объект текущего экземпляра
        current_parent = self._get_parent_object()
        if not current_parent :
            return False

        # Определяем id опции для проверки
        if isinstance(option_to_check , models.Model) :
            # Если передан экземпляр модели, проверяем его класс
            if not isinstance(option_to_check , self.__class__) :
                return False
            option_id_to_check = option_to_check.id
        elif isinstance(option_to_check , (int , str)) :
            try :
                option_id_to_check = int(option_to_check)
            except (ValueError , TypeError) :
                return False
        else :
            return False

        # Получаем родительский объект проверяемой опции
        try :
            # Получаем проверяемую опцию из БД
            option_instance = self.__class__.objects.filter(
                id=option_id_to_check ,
                is_active=True
            ).first()

            if not option_instance :
                return False

            # Получаем родительский объект проверяемой опции
            checked_parent = option_instance._get_parent_object()
            if not checked_parent :
                return False

            # Проверяем, что родительские объекты совпадают
            return current_parent.id == checked_parent.id

        except self.__class__.DoesNotExist :
            return False

    @classmethod
    def is_option_allowed_for_parent(cls , parent_obj , option_to_check) -> bool :
        """
        Проверяет, входит ли переданная опция в список допустимых опций
        для указанного родительского объекта.
        """
        if option_to_check is None :
            return True  # None всегда допустим

        if parent_obj is None :
            return False

        # Получаем имя поля, связывающего с родителем
        parent_field_name = cls._get_parent_field_name()
        if not parent_field_name :
            return False

        # Формируем фильтр для поиска опции
        filter_kwargs = {
            'is_active' : True ,
            parent_field_name : parent_obj
        }

        # В зависимости от типа option_to_check
        if isinstance(option_to_check , models.Model) :
            if not isinstance(option_to_check , cls) :
                return False
            filter_kwargs['id'] = option_to_check.id
        elif isinstance(option_to_check , (int , str)) :
            try :
                filter_kwargs['id'] = int(option_to_check)
            except (ValueError , TypeError) :
                return False
        else :
            return False

        # Проверяем, существует ли такая опция у родителя
        return cls.objects.filter(**filter_kwargs).exists()

    def validate_unique_encoding(self) :
        """
        Проверка уникальности кодирования - только для сохраненных объектов
        """
        if not self.encoding :
            return

        # Если объект еще не сохранен, пропускаем проверку
        if self._state.adding :
            return

        # Получаем родительское поле
        parent_field_name = self._get_parent_field_name()

        if not parent_field_name :
            return

        parent = getattr(self , parent_field_name , None)

        if parent is not None and hasattr(parent , 'pk') and parent.pk is not None :
            try :
                query = {parent_field_name : parent , 'encoding' : self.encoding}
                existing_encoding = self.__class__.objects.filter(
                    **query
                ).exclude(pk=self.pk)

                if existing_encoding.exists() :
                    raise ValidationError({
                        'encoding' : _(
                            'Кодирование "%(encoding)s" уже существует. '
                            'Пожалуйста, выберите другое значение.'
                        ) % {'encoding' : self.encoding}
                    })
            except Exception as e :
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Ошибка при проверке уникальности кодирования: {e}")

    def clean(self) -> None :
        """Только базовая валидация"""
        self.validate_unique_encoding()  # Оставляем только безопасные проверки

    def save(self , *args , **kwargs) :
        """Простое сохранение"""
        self.full_clean()
        super().save(*args , **kwargs)

    def __str__(self) :
        return str(self.encoding) if self.encoding else _("Опция без имени")


class BaseThroughOption(BaseThroughOptionNoDefault) :
    """Базовый абстрактный класс для всех сквозных опций"""

    is_default = models.BooleanField(
        default=False ,
        verbose_name=_("Стандартная опция") ,
        help_text=_("Является ли эта опция стандартной для серии")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    # ==================== МЕТОДЫ ДЛЯ ОПЦИЙ ПО УМОЛЧАНИЮ ====================

    @classmethod
    def ensure_default_exists(cls , parent_obj) -> bool :
        """
        Гарантировать наличие дефолтной опции для родительского объекта
        Для этого проверяем, есть ли дефолтная опция у родительского объекта.
        Если нет - то делаем дефолтной первую попавшуюся, или просто создаем.

        Возвращает True если была создана новая опция
        """
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return False

        # Проверяем, есть ли уже дефолтная опция
        existing_default = cls.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        ).first()

        if existing_default :
            return False  # Дефолтная опция уже существует

        # Если есть опции, но нет дефолтной - делаем первую активную опцию дефолтной
        first_active_option = cls.objects.filter(
            **{parent_field : parent_obj , 'is_active' : True}
        ).first()

        if first_active_option :
            first_active_option.is_default = True
            first_active_option.save()
            return False

        # Если нет опций вообще - создаем дефолтную
        if hasattr(cls , 'create_default_option') :
            cls.create_default_option(parent_obj)
            return True
        else :
            # Базовая реализация если нет специфичного метода
            return cls._create_basic_default_option(parent_obj)

    @classmethod
    def get_or_create_default(cls , parent_obj) :
        """Получить или создать дефолтную опцию"""
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return None

        # Сначала гарантируем наличие дефолтной опции
        cls.ensure_default_exists(parent_obj)

        # Возвращаем дефолтную опцию
        return cls.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        ).first()

    @classmethod
    def get_default_or_any_allowed(cls , parent_obj) :
        """
        Получить дефолтную опцию  у родительского объекта

        Args:
            parent_obj: PneumaticActuatorModelLineItem как правило

        Returns:
            Дефолтная опция или None
        """
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return None

        # ВАЖНО: НЕ создаем опцию, если ее нет - просто возвращаем существующую дефолтную
        # Оключаем ensure_default_exists, чтобы не создавалась новая
        # cls.ensure_default_exists(parent_obj)

        # Ищем дефолтную опцию у родительского объекта
        default_option = cls.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        ).first()

        # Если дефолтной нет, берем первую активную
        if not default_option :
            default_option = cls.objects.filter(
                **{parent_field : parent_obj , 'is_active' : True}
            ).first()

            if default_option :
                # Делаем ее дефолтной
                default_option.is_default = True
                default_option.save()

        return default_option

    @classmethod
    def _create_basic_default_option(cls , parent_obj) -> bool :
        """Базовая реализация создания опции по умолчанию"""
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return False

        try :
            cls.objects.create(
                **{parent_field : parent_obj} ,
                encoding='STD' ,
                description='Стандартная опция' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
            return True
        except Exception :
            return False

    @property
    def default_option(self) -> Optional[models.Model] :
        """Стандартная опция для родительского объекта"""
        parent = self._get_parent_object()
        if not parent :
            return None
        parent_field = self._get_parent_field_name()
        if not parent_field :
            return None
        return self.__class__.objects.filter(
            **{parent_field : parent , 'is_default' : True , 'is_active' : True}).first()

    # ==================== ВАЛИДАЦИЯ ====================

    def validate_unique_default(self) -> None :
        """Пустая валидация - проверку делаем после сохранения"""
        pass

    def __str__(self) :
        """Безопасный __str__ с логированием"""
        print("BaseThroughOption.__str__  called")
        try :
            result = str(self.encoding) if self.encoding else _("Опция")
            logger.debug(f"BaseThroughOption.__str__ для {self.__class__.__name__}: {result}")

            # Проверяем, что результат - строка
            if result is None :
                logger.error(
                    f"BaseThroughOption.__str__ ВОЗВРАЩАЕТ None! Класс: {self.__class__.__name__}, ID: {self.id}")
                return "Опция"

            if not isinstance(result , str) :
                logger.error(
                    f"BaseThroughOption.__str__ ВОЗВРАЩАЕТ {type(result)}! Класс: {self.__class__.__name__}, ID: {self.id}")
                return "Опция"

            return result

        except Exception as e :
            logger.error(f"Ошибка в BaseThroughOption.__str__: {e}" , exc_info=True)
            return "Опция"


class BaseTemperatureThroughOption(BaseThroughOption) :
    """
    Универсальная through-модель для температурных опций
    Наследует от BaseThroughOption и добавляет температурные поля
    """
    work_temp_min = models.IntegerField(
        default=0 ,
        verbose_name=_('Т мин, °С') ,
        help_text=_('Минимальная рабочая температура, °С')
    )
    work_temp_max = models.IntegerField(
        default=0 ,
        verbose_name=_('Т макс, °С') ,
        help_text=_('Максимальная рабочая температура, °С')
    )

    class Meta :
        abstract = True
        ordering = ['is_default' , 'sorting_order']  # Сначала стандартные опции

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную температурную опцию"""
        parent_field = cls._get_parent_field_name()
        return cls.objects.create(
            **{parent_field : parent_obj} ,
            work_temp_min=-20 ,
            work_temp_max=80 ,
            encoding='' ,  # Пустая кодировка для стандартного исполнения
            description='Стандартный температурный диапазон' ,
            is_default=True ,
            sorting_order=0 ,
            is_active=True
        )

    def get_display_name(self) :
        if self.encoding and self.encoding.strip() :
            name_str = f"{self.encoding} ({self.work_temp_min}...{self.work_temp_max}°C)"
        else :
            name_str = f"{self.work_temp_min}...{self.work_temp_max}°C"

        # Исправлено: используем self.is_default вместо self.default_option
        is_default = getattr(self , 'is_default' , False)
        return f"{name_str} (Стандарт)" if is_default else f"{name_str} (Опция)"

    def get_option_info(self , option_instance: Optional['BaseTemperatureThroughOption'] = None) -> Dict[str , Any] :
        """Полная информация об опции с температурными данными"""
        # Вызываем родительский метод
        info = super().get_option_info(option_instance)

        # Определяем, с каким экземпляром работаем
        current_instance = option_instance or self

        # Добавляем температурные данные
        info.update({
            'work_temp_min' : current_instance.work_temp_min ,
            'work_temp_max' : current_instance.work_temp_max ,
            'temperature_range' : f"{current_instance.work_temp_min}...{current_instance.work_temp_max}°C" ,
        })
        return info
    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для рабочих температур"""
        data = {
            'work_temp_min' : {'display_name' : 'Минимальная рабочая температура, °С' , 'value' : self.work_temp_min} ,
            'work_temp_max' : {'display_name' : 'Максимальная рабочая температура, °С' , 'value' : self.work_temp_max} ,
            'temperature_range': {'display_name': 'Вид защиты IP', 'value': f"{self.work_temp_min}...{self.work_temp_max}°C"},
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    def validate_unique_encoding(self) -> None :
        """Валидация уникальности encoding для температурных опций"""
        if self.encoding and self.encoding.strip() :
            parent = self._get_parent_object()
            if parent :
                parent_field = self._get_parent_field_name()
                if parent_field :
                    existing_encoding = self.__class__.objects.filter(
                        **{parent_field : parent , 'encoding' : self.encoding}
                    ).exclude(pk=self.pk if self.pk else None)
                    if existing_encoding.exists() :
                        raise ValidationError('Температурная опция с такой кодировкой уже существует')

    def clean(self) :
        """Дополнительная валидация для температурных опций"""
        # Сначала вызываем базовую валидацию
        super().clean()

        # Валидация температурного диапазона
        if self.work_temp_min and self.work_temp_max :
            if self.work_temp_min >= self.work_temp_max :
                raise ValidationError({
                    'work_temp_max' : _('Максимальная температура должна быть больше минимальной')
                })

    def __str__(self) :
        return self.get_display_name()


class CableGlandHolesSetThroughOption(BaseThroughOption) :
    """Модель для сквозных опций CableGlandHolesSet"""
    cg_set = models.ForeignKey(
        'electric_actuators.CableGlandHolesSet' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Отверстия под КВ") ,
        help_text=_("Отверстия под кабельные вводы")
    )

    class Meta :
        verbose_name = _("Опция кабельных вводов")
        verbose_name_plural = _("Опции кабельных вводов")
        ordering = ['sorting_order']

    def get_display_name(self) :
        """Отображаемое имя для путевых выключателей"""
        if self.cg_set :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.cg_set.name})"
            return self.cg_set.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для набора кабельных вводов"""
        data = {
            'cg_set' : {'display_name' : 'Кабельные вводы' , 'value' : self.cg_set.name} ,
            'cg1' : {'display_name' : 'Отверстие под КВ1' , 'value' : self.cg_set.cg1 if self.cg_set.cg1 else None} ,
            'cg2' : {'display_name' : 'Отверстие под КВ2' , 'value' : self.cg_set.cg1 if self.cg_set.cg1 else None} ,
            'cg3': {'display_name': 'Отверстие под КВ3', 'value': self.cg_set.cg1 if self.cg_set.cg1 else None},
            'cg4': {'display_name': 'Отверстие под КВ4', 'value': self.cg_set.cg1 if self.cg_set.cg1 else None},
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data


class BaseBodyCoatingThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций покрытия корпуса"""
    body_coating_option = models.ForeignKey(
        'params.BodyCoatingOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Опция покрытия корпуса"))

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для покрытия корпуса"""
        # print(f"EA IP OPTION print get_description_data")
        data = {
            'body_coating_option' : {'display_name' : 'Покрытие корпуса' , 'value' : self.body_coating_option.name} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        # print(data)
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную опцию покрытия корпуса"""
        from django.apps import apps

        BodyCoatingOption = apps.get_model('params' , 'BodyCoatingOption')  # Ленивая загрузка
        # Инициализируем переменную
        std_coating = None
        # Последовательно ищем подходящее покрытие
        possible_codes = ['STD' , 'STANDARD' , 'DEFAULT']

        for code in possible_codes :
            std_coating = BodyCoatingOption.objects.filter(
                code=code ,
                is_active=True
            ).first()
            if std_coating :
                break

        # Если не нашли по кодам, берем первое активное
        if not std_coating :
            std_coating = BodyCoatingOption.objects.filter(is_active=True).first()

        if std_coating :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                body_coating_option=std_coating ,
                encoding=std_coating.code ,
                description='Стандартное покрытие корпуса' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для покрытия корпуса"""
        if self.body_coating_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.body_coating_option.name})"
            return self.body_coating_option.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()


class BaseExdThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций Exd"""
    exd_option = models.ForeignKey(
        'params.ExdOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Опция взрывозащиты")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для взрывозащиты"""
        # print(f"EA IP OPTION print get_description_data")
        data = {
            'exd_option' : {'display_name' : 'Тип взрывозащиты' , 'value' : self.exd_option.name} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        # print(data)
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную Exd опцию (STD)"""
        from django.apps import apps

        ExdOption = apps.get_model('params' , 'ExdOption')  # Ленивая загрузка

        try :
            std_option = ExdOption.objects.get(code='STD')
        except ExdOption.DoesNotExist :
            std_option = ExdOption.objects.filter(is_active=True).first()

        if std_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                exd_option=std_option ,
                encoding='STD' ,
                description='Стандартное исполнение взрывозащиты' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для взрывозащиты"""
        if self.exd_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.exd_option.name})"
            return self.exd_option.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()


class BaseIpThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций IP"""
    ip_option = models.ForeignKey(
        'params.IpOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Опция IP")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для IP корпуса"""
        # print(f"EA IP OPTION print get_description_data")
        data = {
            'ip_option' : {'display_name' : 'Вид защиты IP' , 'value' : self.ip_option.name} ,
            'ip_rank' : {'display_name' : 'Степень IP' , 'value' : self.ip_rank if self.ip_rank else None} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        print(data)
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную IP опцию (IP54)"""
        from django.apps import apps

        IpOption = apps.get_model('params' , 'IpOption')  # Ленивая загрузка

        try :
            ip54_option = IpOption.objects.get(code='IP54')
        except IpOption.DoesNotExist :
            ip54_option = IpOption.objects.filter(is_active=True).first()

        if ip54_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                ip_option=ip54_option ,
                encoding='IP54' ,
                description='Стандартная степень защиты IP54' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    # Специфичные методы для IP опций
    @property
    def ip_rank(self) :
        """Ранг IP защиты"""
        return getattr(self.ip_option , 'ip_rank' , 0) if self.ip_option else 0

    def get_display_name(self) :
        is_default = getattr(self , 'is_default' , False)
        return f"{self.ip_option} (Стандарт)" if is_default else f"{self.ip_option} (Опция)"

    # def get_display_name(self):
    #     """Простая безопасная версия"""
    #     # Сначала проверяем encoding
    #     if self.encoding and self.encoding.strip():
    #         encoding_part = self.encoding
    #     else:
    #         encoding_part = None
    #
    #     # Пытаемся получить имя ip_option без исключений
    #     ip_name = None
    #     try:
    #         # Проверяем через безопасный доступ
    #         if hasattr(self, 'ip_option_id') and self.ip_option_id:
    #             # Объект существует в БД
    #             if not hasattr(self, '_ip_option_cache'):
    #                 # Не загружен, но мы можем не загружать для __str__
    #                 ip_name = f"[IP#{self.ip_option_id}]"
    #             elif self.ip_option:
    #                 ip_name = getattr(self.ip_option, 'name', None)
    #     except Exception:
    #         pass
    #
    #     # Формируем результат
    #     if encoding_part and ip_name:
    #         return f"{encoding_part} ({ip_name})"
    #     elif encoding_part:
    #         return encoding_part
    #     elif ip_name:
    #         return ip_name
    #
    #     return "IP опция"

    def __str__(self) :
        """Всегда возвращаем строку"""
        return self.get_display_name()


class BasePneumaticConnectionThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций пневматического подключения"""
    pneumatic_connection = models.ForeignKey(
        'params.PneumaticConnection' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Пневмоподключения") ,
        help_text=_('Возможные типы пневмоподключений'))

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную IP опцию (IP54)"""
        from django.apps import apps

        PneumaticConnection = apps.get_model('params' , 'PneumaticConnection')  # Ленивая загрузка

        try :
            pipe_option = PneumaticConnection.objects.get(code='pipe')
        except PneumaticConnection.DoesNotExist :
            pipe_option = PneumaticConnection.objects.filter(is_active=True).first()

        if pipe_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                pneumatic_connection=pipe_option ,
                encoding='pipe' ,
                description='Подключение трубкой через фитинг' ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None


class BaseSafetyPositionThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций положения безопасности НО/НЗ/оставаться..."""

    safety_position = models.ForeignKey(
        'params.SafetyPositionOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Положение безопасности") ,
        help_text=_('Положения безопасности'))

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для набора кабельных вводов"""
        data = {
            'safety_position' : {'display_name' : 'Положения функции безопасности' , 'value' : self.safety_position.description} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data
class BaseTurnAngleThroughOption(BaseThroughOption) :
    """
    Универсальная through-модель для опций угла поворота однооборотного привода
    Наследует от BaseThroughOption и добавляет поля угол поворота, диапазон регулировок
    """

    turn_angle = models.IntegerField(
        default=90 ,
        verbose_name=_('Поворот, °') ,
        help_text=_('Угол поворота, °')
    )

    turn_angle_deviation_limit = models.IntegerField(
        default=0 ,
        verbose_name=_('Угол ±, °') ,
        help_text=_('Предел регулировки угла поворота, °')
    )

    class Meta :
        abstract = True
        ordering = ['is_default' , 'sorting_order']  # Сначала стандартные опции

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную температурную опцию"""
        parent_field = cls._get_parent_field_name()
        return cls.objects.create(
            **{parent_field : parent_obj} ,
            turn_angle=90 ,
            turn_angle_deviation_limit=4 ,
            encoding='' ,  # Пустая кодировка для стандартного исполнения
            description='Угол поворота 90° ±4°' ,
            is_default=True ,
            sorting_order=0 ,
            is_active=True
        )
    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для угла поворота"""
        data = {
            'turn_angle' : {'display_name' : 'Угол поворота, °' , 'value' : self.turn_angle} ,
            'turn_angle_deviation_limit': {'display_name': 'Предел регулировки угла поворота, °', 'value': self.turn_angle},
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    def get_display_name(self) :
        if self.encoding and self.encoding.strip() :
            name_str = f"{self.encoding} (Угол поворота {self.turn_angle}° ±{self.turn_angle_deviation_limit}°)"
        else :
            name_str = f"Угол поворота {self.turn_angle}° ±{self.turn_angle_deviation_limit}°"

        is_default = getattr(self , 'is_default' , False)
        return f"{name_str} (Стандарт)" if is_default else f"{name_str} (Опция)"

    def get_option_info(self , option_instance: Optional['BaseTemperatureThroughOption'] = None) -> Dict[str , Any] :
        """Полная информация об опции угла поворота"""
        # Вызываем родительский метод
        info = super().get_option_info(option_instance)

        # Определяем, с каким экземпляром работаем
        current_instance = option_instance or self

        # Добавляем инфо о угле поворота
        info.update({
            'turn_angle' : current_instance.turn_angle ,
            'turn_angle_deviation_limit' : current_instance.turn_angle_deviation_limit ,
            'turn_angle_text' : f"Угол поворота {self.turn_angle}° ±{self.turn_angle_deviation_limit}°" ,
        })
        return info

    def validate_unique_encoding(self) -> None :
        """Валидация уникальности encoding опций угла поворота"""
        if self.encoding and self.encoding.strip() :
            parent = self._get_parent_object()
            if parent :
                parent_field = self._get_parent_field_name()
                if parent_field :
                    existing_encoding = self.__class__.objects.filter(
                        **{parent_field : parent , 'encoding' : self.encoding}
                    ).exclude(pk=self.pk if self.pk else None)
                    if existing_encoding.exists() :
                        raise ValidationError('Опция угла поворота с такой кодировкой уже существует')

    def clean(self) :
        """Дополнительная валидация для топций угла поворота"""
        # Сначала вызываем базовую валидацию
        super().clean()

        # Валидация опций угла поворота
        if self.turn_angle and self.turn_angle_deviation_limit :
            if self.turn_angle_deviation_limit >= self.turn_angle :
                raise ValidationError({
                    'turn_angle_deviation_limit' : _('Отклонение угла поворота должно быть быть меньше самого угла')
                })

    def __str__(self) :
        return self.get_display_name()


class BaseSpringsQtyThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций положения безопасности НО/НЗ/оставаться..."""
    # from .pa_params import PneumaticActuatorSpringsQty
    springs_qty = models.ForeignKey(
        'pneumatic_actuators.PneumaticActuatorSpringsQty' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Количество пружин") ,
        help_text=_('Количество пружин'))

    class Meta :
        abstract = True
        ordering = ['sorting_order']


class BaseHandWheelThroughOption(BaseThroughOption) :
    """Базовая модель для опции ручного дублера"""
    hand_wheel_option = models.ForeignKey(
        'params.HandWheelInstalledOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Ручной дублер") ,
        help_text=_("Тип установленного ручного дублера")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для набора кабельных вводов"""
        data = {
            'hand_wheel_option' : {'display_name' : 'Тип установленного на корпусе ручного дублера' , 'value' : self.hand_wheel_option} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную IP опцию (IP54)"""
        from django.apps import apps

        HandWheelInstalledOption = apps.get_model('params' , 'HandWheelInstalledOption')  # Ленивая загрузка

        try :
            no_hand_wheel_option = HandWheelInstalledOption.objects.get(code='none')
        except HandWheelInstalledOption.DoesNotExist :
            no_hand_wheel_option = HandWheelInstalledOption.objects.filter(is_active=True).first()

        if no_hand_wheel_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                hand_wheel_option=no_hand_wheel_option ,
                encoding='' ,
                description=no_hand_wheel_option.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для ручного дублера"""
        if self.hand_wheel_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.hand_wheel_option.name})"
            return self.hand_wheel_option.name
        return "Не указано"

    def __str__(self) :
        name = self.get_display_name()
        if self.is_default :
            return f"{name} (Стандарт)"
        return name


class BaseBlinkerThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций Blinker"""
    blinker_option = models.ForeignKey(
        'params.BlinkerOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Блинкер") ,
        help_text=_("Тип установленного блинкера")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную Blinker)"""
        from django.apps import apps

        BlinkerOption = apps.get_model('params' , 'BlinkerOption')  # Ленивая загрузка

        try :
            no_blinker_option = BlinkerOption.objects.get(code='none')
        except BlinkerOption.DoesNotExist :
            no_blinker_option = BlinkerOption.objects.filter(is_active=True).first()

        if no_blinker_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                blinker_option=no_blinker_option ,
                encoding='' ,
                description=no_blinker_option.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None
    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для блинкера"""
        data = {
            'blinker_option' : {'display_name' : 'Тип установленного блинкера' , 'value' : self.blinker_option} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    def get_display_name(self) :
        """Отображаемое имя для блинкера"""
        if self.blinker_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.blinker_option.name})"
            return self.blinker_option.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()


class BaseControlUnitInstalledThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций для блока управления"""
    control_unit_option = models.ForeignKey(
        'params.ControlUnitInstalledOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Блок управления") ,
        help_text=_("Тип блока управления")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для блока управления"""
        data = {
            'control_unit_option' : {'display_name' : 'Тип установленного блока управления' , 'value' : self.control_unit_option} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную опцию блока управления"""
        from django.apps import apps

        ControlUnitInstalledOption = apps.get_model('params' , 'ControlUnitInstalledOption')

        try :
            no_control_unit_option = ControlUnitInstalledOption.objects.get(code='none')
        except ControlUnitInstalledOption.DoesNotExist :
            no_control_unit_option = ControlUnitInstalledOption.objects.filter(is_active=True).first()

        if no_control_unit_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                control_unit_option=no_control_unit_option ,
                encoding='' ,
                description=no_control_unit_option.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для блока управления"""
        if self.control_unit_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.control_unit_option.name})"
            return self.control_unit_option.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()


class BaseWaySwitchesThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций путевых выключателей"""
    way_switches_option = models.ForeignKey(
        'params.SwitchesParameters' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Путевые выключатели") ,
        help_text=_("Путевые выключатели")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для путевых выключателей"""
        data = {
            'way_switches_option' : {'display_name' : 'Путевые выключатели' , 'value' : self.way_switches_option} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную WaySwitches)"""
        from django.apps import apps

        SwitchesParameters = apps.get_model('params' , 'SwitchesParameters')  # Ленивая загрузка

        try :
            no_way_switches_option = SwitchesParameters.objects.get(code='none')
        except SwitchesParameters.DoesNotExist :
            no_way_switches_option = SwitchesParameters.objects.filter(is_active=True).first()

        if no_way_switches_option :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                way_switches_option=no_way_switches_option ,
                encoding='' ,
                description=no_way_switches_option.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для путевых выключателей"""
        if self.way_switches_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.way_switches_option.name})"
            return self.way_switches_option.name
        return "Не указано"

    def __str__(self) :
        return self.get_display_name()


class BaseOperatingModeThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций режима работы двигателя"""
    operating_mode_option = models.ForeignKey(
        'params.OperatingModeOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Режим работы") ,
        help_text=_("Режим работы двигателя")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для режима работы двигателя"""
        data = {
            'operating_mode_option' : {'display_name' : 'Режим работы двигателя' ,
                                       'value' : self.operating_mode_option.name} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную опцию режима работы"""
        from django.apps import apps

        OperatingModeOption = apps.get_model('params' , 'OperatingModeOption')

        # Ищем стандартный режим работы
        try :
            # Обычно стандартный режим - S2 15min или S4 25%
            default_mode = OperatingModeOption.objects.filter(
                code='S2_15min' ,  # или другой стандартный код
                is_active=True
            ).first()
            if not default_mode :
                default_mode = OperatingModeOption.objects.filter(is_active=True).first()
        except Exception :
            default_mode = OperatingModeOption.objects.filter(is_active=True).first()

        if default_mode :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                operating_mode_option=default_mode ,
                encoding=default_mode.code if default_mode.code else '' ,
                description=default_mode.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Безопасная версия для механического индикатора"""
        # Безопасно проверяем наличие mechanical_indicator_option
        try :
            # Проверяем через ID чтобы избежать RelatedObjectDoesNotExist
            if hasattr(self , 'mechanical_indicator_option_id') and self.mechanical_indicator_option_id :
                # Если есть ID, но объект не загружен
                if not hasattr(self , '_mechanical_indicator_option_cache') :
                    # Пытаемся получить объект
                    from django.apps import apps
                    MechanicalIndicatorInstalledOption = apps.get_model('params' , 'MechanicalIndicatorInstalledOption')
                    try :
                        self.mechanical_indicator_option = MechanicalIndicatorInstalledOption.objects.get(
                            pk=self.mechanical_indicator_option_id
                        )
                    except MechanicalIndicatorInstalledOption.DoesNotExist :
                        pass

            # Теперь безопасно проверяем
            if hasattr(self , 'mechanical_indicator_option') and self.mechanical_indicator_option :
                option_name = getattr(self.mechanical_indicator_option , 'name' , None)
                if option_name :
                    if self.encoding and self.encoding.strip() :
                        return f"{self.encoding} ({option_name})"
                    return option_name
        except Exception :
            # Если произошла ошибка, продолжаем
            pass

        # Fallback - если нет связанного объекта или ошибка
        if self.encoding and self.encoding.strip() :
            return f"{self.encoding} (Механический индикатор)"

        return "Механический индикатор"

    def __str__(self) :
        name = self.get_display_name()
        if self.is_default :
            return f"{name} (Стандарт)"
        return name


class BaseMechanicalIndicatorThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций механического индикатора"""
    mechanical_indicator_option = models.ForeignKey(
        'params.MechanicalIndicatorInstalledOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Механический индикатор") ,
        help_text=_("Тип механического индикатора")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для механического индикатора"""
        data = {
            'mechanical_indicator_option' : {'display_name' : 'Механической индикатор положения' ,
                                       'value' : self.mechanical_indicator_option.name} ,
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
        }
        return data
    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартную опцию механического индикатора"""
        from django.apps import apps

        MechanicalIndicatorInstalledOption = apps.get_model('params' , 'MechanicalIndicatorInstalledOption')

        # Ищем стандартный вариант - обычно "нет индикатора" или "стандартный"
        try :
            default_indicator = MechanicalIndicatorInstalledOption.objects.filter(
                code='none' ,  # или 'standard', 'std'
                is_active=True
            ).first()
            if not default_indicator :
                default_indicator = MechanicalIndicatorInstalledOption.objects.filter(is_active=True).first()
        except Exception :
            default_indicator = MechanicalIndicatorInstalledOption.objects.filter(is_active=True).first()

        if default_indicator :
            parent_field = cls._get_parent_field_name()
            return cls.objects.create(
                **{parent_field : parent_obj} ,
                mechanical_indicator_option=default_indicator ,
                encoding=default_indicator.code if default_indicator.code else '' ,
                description=default_indicator.description ,
                is_default=True ,
                sorting_order=0 ,
                is_active=True
            )
        return None

    def get_display_name(self) :
        """Отображаемое имя для механического индикатора"""
        if self.mechanical_indicator_option :
            if self.encoding and self.encoding.strip() :
                return f"{self.encoding} ({self.mechanical_indicator_option.name})"
            return self.mechanical_indicator_option.name
        return "Не указано"

    def __str__(self) :
        name = self.get_display_name()
        if self.is_default :
            return f"{name} (Стандарт)"
        return name

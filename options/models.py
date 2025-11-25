# options/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List, Optional, Tuple, Any, Dict, Union

from pneumatic_actuators.models import PneumaticActuatorSpringsQty


class BaseThroughOption(models.Model) :
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

    def validate_unique_encoding(self) -> None :
        """Валидация уникальности encoding (оставляем, так как она безопасна)"""
        if self.encoding and self.encoding.strip() :
            parent = self._get_parent_object()
            if parent :
                parent_field = self._get_parent_field_name()
                if parent_field :
                    existing_encoding = self.__class__.objects.filter(
                        **{parent_field : parent , 'encoding' : self.encoding}
                    ).exclude(pk=self.pk if self.pk else None)
                    if existing_encoding.exists() :
                        raise ValidationError('Опция с такой кодировкой уже существует')

    def clean(self) -> None :
        """Только базовая валидация"""
        self.validate_unique_encoding()  # Оставляем только безопасные проверки

    def save(self , *args , **kwargs) :
        """Простое сохранение"""
        self.full_clean()
        super().save(*args , **kwargs)

    def __str__(self) :
        return self.encoding or "Option"

class BaseTemperatureThroughOption(BaseThroughOption):
    """
    Универсальная through-модель для температурных опций
    Наследует от BaseThroughOption и добавляет температурные поля
    """
    work_temp_min = models.IntegerField(
        default=0,
        verbose_name=_('Т мин, °С'),
        help_text=_('Минимальная рабочая температура, °С')
    )
    work_temp_max = models.IntegerField(
        default=0,
        verbose_name=_('Т макс, °С'),
        help_text=_('Максимальная рабочая температура, °С')
    )

    class Meta:
        abstract = True
        ordering = ['is_default', 'sorting_order']  # Сначала стандартные опции

    @classmethod
    def create_default_option(cls, parent_obj):
        """Создать стандартную температурную опцию"""
        parent_field = cls._get_parent_field_name()
        return cls.objects.create(
            **{parent_field: parent_obj},
            work_temp_min=-20,
            work_temp_max=80,
            encoding='',  # Пустая кодировка для стандартного исполнения
            description='Стандартный температурный диапазон',
            is_default=True,
            sorting_order=0,
            is_active=True
        )

    def get_display_name(self):
        """Отображаемое имя с кодировкой или без"""
        if self.encoding and self.encoding.strip():
            return f"{self.encoding} ({self.work_temp_min}...{self.work_temp_max}°C)"
        else:
            return f"{self.work_temp_min}...{self.work_temp_max}°C"

    def get_option_info(self, option_instance: Optional['BaseTemperatureThroughOption'] = None) -> Dict[str, Any]:
        """Полная информация об опции с температурными данными"""
        # Вызываем родительский метод
        info = super().get_option_info(option_instance)

        # Определяем, с каким экземпляром работаем
        current_instance = option_instance or self

        # Добавляем температурные данные
        info.update({
            'work_temp_min': current_instance.work_temp_min,
            'work_temp_max': current_instance.work_temp_max,
            'temperature_range': f"{current_instance.work_temp_min}...{current_instance.work_temp_max}°C",
        })
        return info

    def validate_unique_encoding(self) -> None:
        """Валидация уникальности encoding для температурных опций"""
        if self.encoding and self.encoding.strip():
            parent = self._get_parent_object()
            if parent:
                parent_field = self._get_parent_field_name()
                if parent_field:
                    existing_encoding = self.__class__.objects.filter(
                        **{parent_field: parent, 'encoding': self.encoding}
                    ).exclude(pk=self.pk if self.pk else None)
                    if existing_encoding.exists():
                        raise ValidationError('Температурная опция с такой кодировкой уже существует')

    def clean(self):
        """Дополнительная валидация для температурных опций"""
        # Сначала вызываем базовую валидацию
        super().clean()

        # Валидация температурного диапазона
        if self.work_temp_min and self.work_temp_max:
            if self.work_temp_min >= self.work_temp_max:
                raise ValidationError({
                    'work_temp_max': _('Максимальная температура должна быть больше минимальной')
                })

    def __str__(self):
        return self.get_display_name()

class BaseBodyCoatingThroughOption(BaseThroughOption) :
    """Базовая модель для сквозных опций покрытия корпуса"""
    body_coating_option = models.ForeignKey(
        'params.BodyCoatingOption' ,
        on_delete=models.CASCADE ,
        verbose_name=_("Опция покрытия корпуса"))

    class Meta :
        abstract = True
        ordering = ['sorting_order']

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

class BasePneumaticConnectionThroughOption(BaseThroughOption):
    """Базовая модель для сквозных опций пневматического подключения"""
    pneumatic_connection = models.ForeignKey(
        'params.PneumaticConnection',
        on_delete=models.CASCADE,
        verbose_name=_("Пневмоподключения") ,
        help_text=_('Возможные типы пневмоподключений'))

    class Meta:
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

class BaseSafetyPositionThroughOption(BaseThroughOption):
    """Базовая модель для сквозных опций положения безопасности НО/НЗ/оставаться..."""
    safety_position = models.ForeignKey(
        'params.SafetyPositionOption',
        on_delete=models.CASCADE,
        verbose_name=_("Положение безопасности") ,
        help_text=_('Положения безопасности'))

    class Meta:
        abstract = True
        ordering = ['sorting_order']

class BaseSpringsQtyThroughOption(BaseThroughOption):
    """Базовая модель для сквозных опций положения безопасности НО/НЗ/оставаться..."""
    # from .pa_params import PneumaticActuatorSpringsQty
    springs_qty = models.ForeignKey(
        PneumaticActuatorSpringsQty,
        on_delete=models.CASCADE,
        verbose_name=_("Количество пружин") ,
        help_text=_('Количество пружин'))

    class Meta:
        abstract = True
        ordering = ['sorting_order']
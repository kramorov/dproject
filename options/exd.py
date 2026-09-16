# options/exd.py
"""Exd-опция: базовые классы through-строк и миксины потребителей.

См. exd-option.md (корень репозитория) - контракт и инвентаризация.
Вынесено из options/models.py для гигиены модуля; классы реэкспортируются
обратно из options.models, поэтому старые импорты продолжают работать.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List , Optional , Tuple , Any , Dict , Union

import logging

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



class ExdFormattingMixin:
    """Форматирование и признаки взрывозащиты (Exd). Без полей — только поведение.

    Общий слой для двух потребителей списка видов взрывозащиты:

    * through-строка ``BaseM2MExdThroughOption`` — одна строка = одна кодировка,
      внутри которой M2M видов;
    * item/каталог (``ExdOptionsConsumerMixin``) — виды денормализованы в M2M-поле
      и копируются из through-строки серии.

    Миксин не наследует ``models.Model``, поэтому подмешивается и к моделям, и к
    обычным классам. Он рассчитывает, что на объекте есть M2M-поле с видами,
    имя которого задаётся атрибутом ``exd_m2m_field`` (по умолчанию ``'exd_options'``;
    например, у ``LimitSwitchBox`` это ``'exd'``).

    ``EXD_RELATED`` — кортеж связанных справочников для ``select_related``, чтобы
    форматирование не порождало N+1 запросов.

    Точки расширения:
      * ``get_exd_options()`` — эффективный список видов; по умолчанию читает M2M,
        потребитель переопределяет под ``_selected_exd_row`` и фолбэк на строку серии;
      * ``has_exd()`` — признак взрывозащищённого исполнения;
      * ``get_exd_list`` / ``get_exd_short_list`` — текстовые представления
        (полное с группировкой температур / короткое уникальных видов).
    """

    EXD_RELATED = (
        'explosion_protection_class', 'hazardous_group',
        'temperature_class', 'explosion_protection_level',
    )
    exd_m2m_field = 'exd_options'   # имя M2M-поля на объекте (item/строка)

    def _get_exd_m2m(self):
        """Менеджер M2M-поля с видами взрывозащиты для текущего объекта."""
        return getattr(self, self.exd_m2m_field)

    def get_exd_options(self):
        """Эффективный список ``ExdOption`` с подгруженными справочниками.

        Базовая реализация читает M2M-поле напрямую. ``ExdOptionsConsumerMixin``
        переопределяет метод, добавляя источник через ``_selected_exd_row``
        и фолбэк на строку серии по умолчанию.
        """
        return list(self._get_exd_m2m().all().select_related(*self.EXD_RELATED))

    def has_exd(self) -> bool:
        """Выбрано ли взрывозащищённое исполнение.

        True, если среди эффективных видов есть хотя бы один с непустым ``code``.
        Для «общепром»-строк M2M пуст либо заполнен записью без кода — вернёт False.
        """
        return any(bool(v.code) for v in self.get_exd_options())

    @staticmethod
    def _exd_group_key(exd):
        """Ключ группы «одинаковые степени, разная температура» (без X/U)."""
        return (
            exd.explosion_protection_class_id,
            exd.hazardous_group_id,
            exd.explosion_protection_level_id,
        )

    @staticmethod
    def _exd_temperature_token(exd) -> str:
        gas_temps = {'T1', 'T2', 'T3', 'T4', 'T5', 'T6'}
        if exd.temperature_class_id:
            code = exd.temperature_class.code
            return code if code in gas_temps else f'{code}°C'
        if exd.dust_temperature is not None:
            return f'T{exd.dust_temperature}°C'
        return ''

    @classmethod
    def _format_exd_group(cls, exds) -> str:
        """Одна группа: Ex db IIB T5/T6 (X/U — один раз на группу)."""
        first = exds[0]
        parts = []
        if first.explosion_protection_class_id:
            parts.append(str(first.explosion_protection_class))
        if first.hazardous_group_id:
            parts.append(str(first.hazardous_group))
        temps = []
        for exd in exds:
            token = cls._exd_temperature_token(exd)
            if token and token not in temps:
                temps.append(token)
        if temps:
            parts.append('/'.join(temps))
        if first.explosion_protection_level_id:
            parts.append(str(first.explosion_protection_level))
        if any(exd.has_x_suffix for exd in exds):
            parts.append('X')
        if any(exd.has_u_suffix for exd in exds):
            parts.append('U')
        return ' '.join(parts)

    @property
    def get_exd_list(self) -> str:
        """Полный список видов взрывозащиты (текст).

        Одинаковые степени с разными температурными классами объединяются:
        «Ex db IIB T5» и «Ex db IIB T6» → «Ex db IIB T5/T6».
        """
        groups = {}
        order = []
        for exd in self.get_exd_options():
            if not exd.explosion_protection_class_id:
                continue
            key = self._exd_group_key(exd)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(exd)
        return ', '.join(self._format_exd_group(groups[key]) for key in order)

    @property
    def get_exd_short_list(self) -> str:
        """Уникальные виды взрывозащиты, например «Ex d / Ex ia»."""
        seen = set()
        result = []
        for exd in self.get_exd_options():
            if not exd.explosion_protection_class_id:
                continue
            name = str(exd.explosion_protection_class)
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return ' / '.join(result)



class BaseM2MExdThroughOption(BaseThroughOption, ExdFormattingMixin):
    """Абстрактная through-строка взрывозащиты: одна строка = одна кодировка.

    В отличие от FK-схемы ``BaseExdThroughOption`` (одна строка = один вид
    ``ExdOption``), здесь внутри одной кодировки перечислено несколько видов
    через M2M ``exd_options``:

      * «Общепром» — строка с собственным encoding, M2M пустой (или ссылка на
        запись «общепром» справочника);
      * «Ex» — строка с encoding 'Ex', в M2M — все доступные виды Exd, которые
        делят этот encoding.

    Кодировка уникальна в пределах родительской серии (``validate_unique_encoding``),
    поэтому один encoding нельзя завести дважды — виды добавляются в существующую
    строку.

    Поле ``exd_options`` объявлено здесь с ``related_name='%(class)s_exd_rows'``,
    чтобы у каждого подкласса был уникальный обратный доступ с ``params.ExdOption``.

    Контракт подкласса:
      * объявить ``model_line = models.ForeignKey(...)`` на свою серию;
      * задать ``Meta.verbose_name`` / ``Meta.verbose_name_plural``;
      * при необходимости переопределить ``_get_parent_field_name()``
        (по умолчанию автоопределяется первый FK).
    """

    exd_options = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='%(class)s_exd_rows',
        verbose_name=_('Виды взрывозащиты'),
    )

    class Meta:
        abstract = True
        ordering = ['sorting_order']

    def validate_unique_encoding(self) -> None:
        """Одна строка на кодировку в пределах родителя (серии).

        Базовая реализация пропускает НЕсохранённые объекты (adding) — для
        M2M-схемы это дыра, поэтому проверяем и при создании, и при правке.
        """
        if not (self.encoding and self.encoding.strip()):
            return
        parent = getattr(self, self._get_parent_field_name(), None)
        if parent is None or getattr(parent, 'pk', None) is None:
            return
        existing = self.__class__.objects.filter(
            **{self._get_parent_field_name(): parent, 'encoding': self.encoding}
        ).exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError({
                'encoding': _('Кодировка "%(encoding)s" уже используется '
                              'в этой серии — добавьте вид в существующую строку.') % {
                    'encoding': self.encoding}
            })

    def get_display_name(self) -> str:
        """Читаемое имя строки: «Серия → encoding: виды».

        Для несохранённой/удалённой строки M2M-менеджер требует pk, поэтому
        возвращаем только encoding с пометкой «(удалено)» — это защищает от
        рекурсивного ``__str__`` при ошибках M2M.
        """
        if self.pk is None:
            return f"{self.encoding or '—'} (удалено)"
        values = ', '.join(e.name for e in self.exd_options.all()) or '—'
        parent = self._get_parent_object()
        return f"{parent} → {self.encoding}: {values}"

    def __str__(self) -> str:
        return self.get_display_name()

    def get_description_data(self) -> Dict[str, Any]:
        """Структурированные данные для рендера (формат BaseExdThroughOption).

        Ключ ``exd_option`` сохранён для совместимости с универсальным рендером
        (electric_actuators/utils/universal_renderer.py): value — короткий список
        видов «Ex db / Ex ta», is_default — признак стандарта.
        """
        return {
            'exd_option' : {
                'display_name' : _('Тип взрывозащиты') ,
                'value' : self.get_exd_short_list or self.get_exd_list or '' ,
            } ,
            'is_default' : {'display_name' : _('Стандарт') , 'value' : self.is_default} ,
        }

    @classmethod
    def get_effective_row(cls, parent=None, parent_id=None):
        """Эффективная строка взрывозащиты для родителя (серии).

        Приоритет: активная строка с ``is_default=True``; если её нет — первая
        активная. ``parent`` и ``parent_id`` взаимоисключаемы; если передан
        ``parent_id``, лишний запрос к родителю не делается. Возвращает ``None``,
        если родитель не задан или подходящих строк нет.
        """
        parent_field = cls._get_parent_field_name()
        if not parent_field:
            return None
        qs = cls.objects.filter(is_active=True)
        if parent_id is not None:
            qs = qs.filter(**{f'{parent_field}_id': parent_id})
        elif parent is not None:
            qs = qs.filter(**{parent_field: parent})
        else:
            return None
        return qs.filter(is_default=True).first() or qs.first()



class ExdOptionsConsumerMixin(ExdFormattingMixin):
    """Поведение item'а: денормализованный M2M взрывозащиты и синхронизация.

    Подмешивается к каталоговой модели (``PosiModelLineItem``, ``LimitSwitchBox``),
    у которой есть M2M-поле с видами ``params.ExdOption`` и FK на серию. Источник
    истины — through-строка серии (``BaseM2MExdThroughOption``); M2M item'а —
    денормализованная копия, поддерживаемая в актуальном состоянии при создании.

    Настройки через атрибуты класса:
      * ``exd_through_model`` — строка ``'app.Model'`` через-модели серии
        (ленивая загрузка через ``apps.get_model``, без циклических импортов);
      * ``exd_parent_field`` — имя FK на серию у item'а (по умолчанию ``'model_line'``);
      * ``exd_m2m_field`` — имя M2M-поля с видами (из ``ExdFormattingMixin``,
        по умолчанию ``'exd_options'``, у БКВ — ``'exd'``).

    Динамический атрибут ``_selected_exd_row`` (ставится конструктором/превью)
    позволяет показать несохранённому item'у кодировку и список видов выбранной
    строки до сохранения.
    """

    exd_through_model = 'pa_controls.PosiExdOption'
    exd_parent_field = 'model_line'

    @classmethod
    def _get_exd_through_model(cls):
        """Лениво резолвит through-модель из ``exd_through_model``."""
        from django.apps import apps
        return apps.get_model(cls.exd_through_model)

    def get_exd_options(self):
        """Эффективный список видов взрывозащиты для item'а.

        Источники (по приоритету):
          1. ``_selected_exd_row`` — через-строка, переданная конструктором/превью;
          2. денормализованный M2M item'а (для сохранённого объекта);
          3. строка серии по умолчанию (``is_default``, фолбэк — первая активная).

        Для всех путей подгружаются связанные справочники из ``EXD_RELATED``.
        """
        row = getattr(self, '_selected_exd_row', None)
        if row is not None:
            return list(row.exd_options.all().select_related(*self.EXD_RELATED))
        if self.pk:
            return list(self._get_exd_m2m().all().select_related(*self.EXD_RELATED))
        parent_id = getattr(self, f'{self.exd_parent_field}_id', None)
        if not parent_id:
            return []
        row = self._get_exd_through_model().get_effective_row(parent_id=parent_id)
        return list(row.exd_options.all().select_related(*self.EXD_RELATED)) if row else []

    def _sync_exd_options_from_model_line(self):
        """Скопировать в M2M item'а виды из эффективной строки серии.

        Вызывается при создании item'а, чтобы денормализованное поле совпадало
        с through-строкой по умолчанию (``is_default``, иначе первая активная).
        """
        parent_id = getattr(self, f'{self.exd_parent_field}_id', None)
        row = self._get_exd_through_model().get_effective_row(parent_id=parent_id)
        if row is None:
            return
        self._get_exd_m2m().set(row.exd_options.all())

    @property
    def exd_encoding(self) -> str:
        """Кодировка взрывозащиты для артикула.

        Для превью берётся encoding переданной ``_selected_exd_row``. Для
        сохранённого item строка не хранится — кодировка выводится по набору
        видов: если есть Ex-виды, ищем строку с непустым M2M, иначе строку
        «общепром» с пустым M2M.
        """
        row = getattr(self, '_selected_exd_row', None)
        if row is not None:
            return row.encoding or ''
        parent_id = getattr(self, f'{self.exd_parent_field}_id', None)
        if not parent_id:
            return ''
        exd_ids = {v.id for v in self.get_exd_options()}
        rows = self._get_exd_through_model().objects.filter(
            **{f'{self.exd_parent_field}_id': parent_id}, is_active=True
        ).prefetch_related('exd_options')
        if exd_ids:
            for row in rows:
                if row.exd_options.filter(id__in=exd_ids).exists():
                    return row.encoding or ''
        else:
            for row in rows:
                if not row.exd_options.exists():
                    return row.encoding or ''
        return ''

    @property
    def exd_display(self) -> str:
        """Группированное текстовое представление, «Нет» для общепром-исполнения.

        Удобно для шаблонов каталога и админки: пустой список (нет видов с
        кодом) отображается как «Нет».
        """
        return self.get_exd_list or 'Нет'


class ChosenExdRowMixin(ExdFormattingMixin):
    """Потребитель с FK на through-строку (CableGland, DirectionValve).

    Унифицирует поведение «выбор опции из списка серии»: эффективная строка,
    полный/короткий списки видов, кодировка для артикула и валидация
    принадлежности строки серии. См. exd-option.md §6.2.

    Настройки через атрибуты класса:
      * ``exd_row_field`` — имя FK на through-строку (по умолчанию
        ``'exd_option'``);
      * ``exd_through_model`` — строка ``'app.Model'`` через-модели серии
        (обязателен; ленивая загрузка через ``apps.get_model``);
      * ``exd_parent_field`` — имя FK на серию (по умолчанию ``'model_line'``).
    """

    exd_row_field = 'exd_option'
    exd_through_model = None
    exd_parent_field = 'model_line'

    @classmethod
    def _get_exd_through_model(cls):
        """Лениво резолвит through-модель из ``exd_through_model``."""
        from django.apps import apps
        if not cls.exd_through_model:
            raise AttributeError(
                f'{cls.__name__} не задал exd_through_model'
            )
        return apps.get_model(cls.exd_through_model)

    def _get_effective_exd_row(self):
        """Эффективная through-строка: выбранная (exd_row_field) или дефолт серии."""
        row = getattr(self, self.exd_row_field, None)
        parent_id = getattr(self, f'{self.exd_parent_field}_id', None)
        if row is None and parent_id:
            try:
                row = self._get_exd_through_model().get_effective_row(parent_id=parent_id)
            except Exception:
                row = None
        return row

    def get_exd_options(self):
        """Эффективный список ``ExdOption`` (из выбранной/дефолтной строки)."""
        row = self._get_effective_exd_row()
        if row is None:
            return []
        return list(row.exd_options.all().select_related(*self.EXD_RELATED))

    @property
    def get_exd_display(self) -> str:
        """Взрывозащита: список имён видов через « / » (для ``{exd}``)."""
        row = self._get_effective_exd_row()
        if row is None:
            return ''
        items = []
        for x in row.exd_options.all():
            items.append(x.name or x.code or x.description or str(x))
        return ' / '.join(items)

    @property
    def get_exd_short_list(self) -> str:
        """Короткий список видов «Ex db / Ex ta» (для ``{exd_short}``)."""
        row = self._get_effective_exd_row()
        return row.get_exd_short_list if row else ''

    @property
    def exd_encoding(self) -> str:
        """Кодировка выбранной/дефолтной строки (для ``code_path`` артикула)."""
        row = self._get_effective_exd_row()
        return row.encoding if (row and row.encoding) else ''

    def clean(self):
        """Валидация: опция взрывозащиты должна относиться к той же серии."""
        super().clean()
        errors = {}
        row_id = getattr(self, f'{self.exd_row_field}_id', None)
        parent_id = getattr(self, f'{self.exd_parent_field}_id', None)
        if row_id and parent_id:
            row = getattr(self, self.exd_row_field, None)
            if row is not None and getattr(row, f'{self.exd_parent_field}_id') != parent_id:
                errors[self.exd_row_field] = _('Взрывозащита относится к другой серии.')
        if errors:
            raise ValidationError(errors)



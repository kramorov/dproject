# params/exd_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import TextDescriptionMixin, OptionListToSelectMixin


class HazardousGroup(models.Model) :
    """Группа взрывоопасной среды (газ и пыль в одном справочнике)"""

    class GroupType(models.TextChoices) :
        GAS = 'GAS' , _('Газ')
        DUST = 'DUST' , _('Пыль')

    code = models.CharField(max_length=5 , unique=True)  # IIA, IIB, IIC, IIIA, IIIB, IIIC
    name = models.CharField(max_length=100 , blank=True)
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое группы взрывоопасной среды'))
    group_type = models.CharField(max_length=5 , choices=GroupType.choices)
    rating = models.IntegerField(help_text="Чем выше рейтинг, тем более опасная среда")
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Группа опасности")
        verbose_name_plural = _("Exd Группа опасности")
        ordering = ['group_type' , 'rating']

    def __str__(self) :
        return self.code

    def is_compatible(self , required_code) :
        """
        Проверяет, подходит ли данная группа для требуемой
        Оборудование с IIC (рейтинг 3) подходит для IIB (рейтинг 2)
        """
        if not required_code :
            return True

        try :
            required = HazardousGroup.objects.get(code=required_code , group_type=self.group_type)
            return self.rating >= required.rating
        except HazardousGroup.DoesNotExist :
            return False

class TemperatureClass(models.Model, TextDescriptionMixin):
    """Температурный класс (T1-T6)"""
    name = models.CharField(max_length=10, verbose_name=_("Название"))
    code = models.CharField(max_length=10, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    temperature_class = models.CharField(max_length=5, verbose_name=_("Класс"))
    # Ранг строгости: T6=6, T5=5, ..., T1=1
    strictness_rating = models.IntegerField(default=0, blank=True)

    max_surface_temp = models.IntegerField(verbose_name=_("Макс. температура поверхности, °C"))
    gas_ignition_temp = models.IntegerField(
        null=True, blank=True,
        verbose_name=_("Температура воспламенения газа, °C")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Температурный класс")
        verbose_name_plural = _("Exd Температурные классы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.temperature_class}"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем ранг на основе кода
        if self.temperature_class and not self.strictness_rating:
            rank_map = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4, 'T5': 5, 'T6': 6}
            self.strictness_rating = rank_map.get(self.temperature_class, 0)
        super().save(*args, **kwargs)

    def get_text_description(self) -> str:
        """Генерирует описание температурного класса"""
        return _(
            "Максимальная температура поверхности %(temp)s°C, допустима для газов с температурой воспламенения выше %(ignition)s°C"
        ) % {
            'temp': self.max_surface_temp,
            'ignition': self.max_surface_temp
        }
class ExplosionProtectionMethod(models.Model):
    """Общий метод (Вид) взрывозащиты: d, e, i, m, p, t и т.д."""
    code = models.CharField(max_length=10, unique=True) # Например: 'i'
    name = models.CharField(max_length=100) # Искробезопасная электрическая цепь
    description = models.TextField()
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Общий метод (Вид) взрывозащиты")
        verbose_name_plural = _("Exd Общие методы (Виды) взрывозащиты")
        ordering = ['sorting_order']
    def __str__(self):
        return f"Ex {self.code}"

class ExplosionProtectionType(models.Model, TextDescriptionMixin):
    """Тип взрывозащиты (Ex d, Ex e, Ex i, etc.)"""

    class ProtectionCategory(models.TextChoices):
        GAS = 'GAS', _('Газ')
        DUST = 'DUST', _('Пыль')

    code = models.CharField(max_length=10, verbose_name=_("Код"))
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    method = models.ForeignKey(ExplosionProtectionMethod, null=True, blank=True, on_delete=models.CASCADE,
        related_name='explosion_protection_class_for_exd' ,
        verbose_name=_("Разновидность вида взрывозащиты") ,
        help_text=_("Разновидность вида взрывозащиты (Ex d, Ex ia...)")
    )
    category = models.CharField(
        max_length=10,
        choices=ProtectionCategory.choices,
        default=ProtectionCategory.GAS,
        verbose_name=_("Категория")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _("Разновидность вида взрывозащиты")
        verbose_name_plural = _("Exd Разновидности вида взрывозащиты")
        ordering = ['sorting_order']
    def __str__(self):
        return f"Ex {self.code}"

    def get_text_description(self) -> str:
        """Генерирует описание типа взрывозащиты"""
        descriptions = {
            'd': _("Взрывонепроницаемая оболочка - оборудование выдерживает внутреннее давление взрыва"),
            'e': _("Повышенная надежность - отсутствие искр и дуг в нормальном режиме"),
            'i': _("Искробезопасная электрическая цепь - энергия ограничена"),
            'ia': _("Искробезопасная цепь - очень высокая степень защиты"),
            'ib': _("Искробезопасная цепь - высокая степень защиты"),
            'n': _("Неискрящее оборудование для Зоны 2"),
            'nA': _("Неискрящее оборудование для Зоны 2"),
            'm': _("Герметизация компаундом"),
            'p': _("Заполнение или продувка оболочки под избыточным давлением"),
            't': _("Защита оболочкой для пыли"),
            'tb': _("Защита оболочкой для пыли - высокая степень"),
        }
        return descriptions.get(self.code, self.description or self.name)


class ExplosionProtectionLevel(models.Model, TextDescriptionMixin):
    """Уровень взрывозащиты (Ga, Gb, Gc, Da, Db, Dc)"""
    name = models.CharField(max_length=10, verbose_name=_("Название"))
    code = models.CharField(max_length=10, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    equipment_category = models.CharField(
        max_length=20,
        choices=[
            ('MINING', _('Горнорудная')),
            ('SURFACE', _('Поверхностная')),
        ],
        verbose_name=_("Категория оборудования")
    )
    zone = models.CharField(
        max_length=10,
        blank=True,
        help_text=_("Зона взрывоопасности")
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Уровень взрывозащиты")
        verbose_name_plural = _("Exd Уровни взрывозащиты")

    def __str__(self):
        return self.code

    def get_text_description(self) -> str:
        """Генерирует описание уровня взрывозащиты"""
        descriptions = {
            'Ga': _("Оборудование для Зоны 0 - очень высокая степень защиты"),
            'Gb': _("Оборудование для Зоны 1 - высокая степень защиты"),
            'Gc': _("Оборудование для Зоны 2 - нормальная степень защиты"),
            'Da': _("Оборудование для Зоны 20 - очень высокая степень защиты"),
            'Db': _("Оборудование для Зоны 21 - высокая степень защиты"),
            'Dc': _("Оборудование для Зоны 22 - нормальная степень защиты"),
        }
        return descriptions.get(self.code, self.description or self.name)


class ExdOption(models.Model, OptionListToSelectMixin):
    """Тип взрывозащиты (расширенная версия)"""

    class EquipmentType(models.TextChoices):
        GAS = 'GAS', _('Газовое оборудование')
        DUST = 'DUST', _('Пылевое оборудование')
        # BOTH = 'BOTH', _('Газовое и пылевое (двойная маркировка)')
        SIMPLE = 'SIMPLE', _('Простая маркировка')

    # Существующие поля
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение вида взрывозащиты"))
    code = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Код вида взрывозащиты"))
    description = models.TextField(blank=True,
                                   verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание вида взрывозащиты'))
    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    exd_full_code = models.CharField(max_length=200, blank=True,  # Добавлен blank=True
                                     verbose_name=_('Полный код взрывозащиты'),
                                     help_text=_('Полный код вида взрывозащиты'))

    explosion_protection_class = models.ForeignKey(
        'params.ExplosionProtectionType' ,  # Исправлено
        on_delete=models.SET_NULL ,
        null=True ,
        blank=True ,
        related_name='explosion_protection_class_for_exd' ,
        verbose_name=_("Разновидность вида взрывозащиты") ,
        help_text=_("Разновидность вида взрывозащиты (Ex d, Ex ia...)")
    )
    explosion_protection_level = models.ForeignKey(
        'params.ExplosionProtectionLevel',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='explosion_protection_level_for_exd',
        verbose_name=_("Уровень взрывозащиты"),
        help_text=_("Уровень взрывозащиты(Gb,Db ...)")
    )
    # Для газа и пыли используются разные поля: для газа TemperatureClass, для пыли - dust_temperature
    # Разная логика совместимости (газ: T6 подходит для T1-T6, пыль: 200°C подходит для 85°C) - чем больше, тем лучше
    # Для газа
    temperature_class = models.ForeignKey(
        'params.TemperatureClass',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temp_class_for_exd',
        verbose_name=_("Температурный класс"),
        help_text=_("Температурный класс")
    )
    # Для пыли
    dust_temperature = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Температура для пыли, °C"),
        help_text=_("Максимальная температура поверхности (например, 85, 95, 100)")
    )
    # Кэшированный ранг температуры (для быстрой фильтрации)
    temperature_rating = models.IntegerField(null=True, blank=True)
    # Для пылевой взрывозащиты
    hazardous_group = models.ForeignKey(
        'params.HazardousGroup' ,  # Исправлено
        on_delete=models.SET_NULL ,
        null=True ,
        blank=True ,
        related_name='hazardous_group' ,
        verbose_name=_("Группа взрывоопасной среды") ,
        help_text=_("Группа взрывоопасной среды (газ и пыль в одном справочнике)")
    )

    # Специальные обозначения
    has_x_suffix = models.BooleanField(
        default=False,
        verbose_name=_("Специальные условия (X)"),
        help_text=_("Добавить X в конце маркировки")
    )

    has_u_suffix = models.BooleanField(
        default=False,
        verbose_name=_("Только компонент (U)"),
        help_text=_("Добавить U для компонентов")
    )

    # Автоматически генерируемое полное название
    generated_full_code = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Сгенерированный полный код"),
        help_text=_("Автоматически сгенерированная маркировка")
    )

    class Meta:
        verbose_name = _('Тип взрывозащиты')
        verbose_name_plural = _('Exd Типы взрывозащиты')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name or self.exd_full_code or "Exd"

    def get_formatted_ex_code(self, option='name'):
        """
        Формирует строку маркировки

        Args:
            option: 'name' - для отображения (с пробелами, с °C для пыли)
                    'code' - для кода (все маленькие буквы, разделитель "-")

        Returns:
            str: Отформатированная строка
        """
        parts = []

        # Определяем разделитель и форматирование в зависимости от option
        if option == 'code':
            separator = '-'

            # Функция форматирования для code
            def fmt_code(value):
                return str(value).lower()
        else:  # option == 'name'
            separator = ' '

            # Функция форматирования для name (без изменений)
            def fmt_code(value):
                return str(value)

        # 1. Вид защиты (Ex db, Ex ia...)
        if self.explosion_protection_class:
            if option == 'code':
                # Извлекаем код без "Ex " (например, "db" из "Ex db")
                class_code = str(self.explosion_protection_class.code).lower()
                parts.append(class_code)
            else:
                parts.append(str(self.explosion_protection_class.name))

        # 2. Группа среды (IIC, IIIC...)
        if self.hazardous_group:
            parts.append(fmt_code(self.hazardous_group.code))

        # 3. Температурный класс
        if self.temperature_class:
            temp_code = self.temperature_class.code
            gas_temps = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']

            if option == 'code':
                parts.append(temp_code.lower())
            else:  # option == 'name'
                if temp_code in gas_temps:
                    parts.append(temp_code)
                else:
                    parts.append(f"{temp_code}°C")
        elif self.dust_temperature:
            if option == 'code':
                parts.append(f"t{self.dust_temperature}")
            else:
                parts.append(f"T{self.dust_temperature}°C")

        # 4. Уровень взрывозащиты (Ga, Gb, Da...)
        if self.explosion_protection_level:
            if option == 'code':
                parts.append(str(self.explosion_protection_level.code).lower())
            else:
                parts.append(str(self.explosion_protection_level.code))

        # 5. Спец-символы
        if self.has_x_suffix:
            parts.append('x' if option == 'code' else 'X')
        if self.has_u_suffix:
            parts.append('u' if option == 'code' else 'U')

        # Склеиваем с соответствующим разделителем
        full_string = separator.join(filter(None, parts))

        return full_string.strip()

    def save(self, *args, **kwargs):
        # Устанавливаем temperature_rating
        if self.temperature_class:
            self.temperature_rating = self.temperature_class.strictness_rating
        elif self.dust_temperature:
            self.temperature_rating = self.dust_temperature
        else:
            self.temperature_rating = None

        self.name = self.get_formatted_ex_code(option='name')
        self.code = self.get_formatted_ex_code(option='code')
        super().save(*args, **kwargs)

    @classmethod
    def get_structured_choices(cls) -> Dict:
        """
        Возвращает словарь с иерархическими данными для выбора взрывозащиты.
        Структура:
        {
            "methods": [
                {"id": 1, "code": "d", "name": "Взрывонепроницаемая оболочка", "types": [...]},
                ...
            ],
            "gas_groups": [...],
            "dust_groups": [...],
            "temperature_classes": [...],
            "protection_levels": {"gas": [...], "dust": [...]}
        }
        """

        # 1. Методы взрывозащиты + связанные типы
        methods_qs = ExplosionProtectionMethod.objects.filter(is_active=True).order_by('sorting_order')
        methods = []
        for method in methods_qs:
            # Типы, связанные с этим методом
            types = ExplosionProtectionType.objects.filter(
                method=method,
                is_active=True
            ).order_by('sorting_order')

            methods.append({
                'id': method.id,
                'code': method.code,
                'name': method.name,
                'description': method.description,
                'types': [
                    {'id': t.id, 'code': t.code, 'name': t.name, 'description': t.description}
                    for t in types
                ]
            })

        # 2. Группы газа и пыли
            # 2. Группы - объединяем газ и пыль в один список
        gas_groups = [
            {'id': g.id, 'code': g.code, 'name': g.name, 'rating': g.rating, 'group_type': 'GAS', 'description': g.description}
            for g in HazardousGroup.objects.filter(group_type='GAS', is_active=True).order_by('rating')
        ]
        dust_groups = [
            {'id': g.id, 'code': g.code, 'name': g.name, 'rating': g.rating, 'group_type': 'DUST', 'description': g.description}
            for g in HazardousGroup.objects.filter(group_type='DUST', is_active=True).order_by('rating')
        ]
        all_groups = gas_groups + dust_groups  # просто складываем списки
        # 3. Температурные классы
        temp_classes = [
            {
                'id': t.id,
                'code': t.temperature_class,
                'name': t.name,
                'description': t.description,
                'max_temp': t.max_surface_temp,
                'strictness_rating': t.strictness_rating
            }
            for t in TemperatureClass.objects.filter(is_active=True).order_by('sorting_order')
        ]

        # 4. Уровни взрывозащиты
        protection_levels = [
            {'id': l.id, 'code': l.code, 'name': l.name}
            for l in ExplosionProtectionLevel.objects.filter(
                code__in=['Ga', 'Gb', 'Gc', 'Da', 'Db', 'Dc']
            ).order_by('code')
        ]
        return {
            'methods': methods,
            'groups': all_groups,
            'gas_groups': gas_groups,
            'dust_groups': dust_groups,
            'temperature_classes': temp_classes,
            'protection_levels': protection_levels,
        }

    def get_compatible_ids(self) -> set:
        """
        Возвращает ID всех ExdOption, совместимых с текущим
        Вход: Объект ExdOption	Выход: ID совместимых	Когда использовать: Когда уже выбран конкретный ExdOption
        """
        queryset = ExdOption.objects.filter(is_active=True)

        # 1. Фильтр по методу взрывозащиты (через ForeignKey)
        if self.explosion_protection_class and self.explosion_protection_class.method:
            # Ищем все типы с таким же методом
            queryset = queryset.filter(
                explosion_protection_class__method=self.explosion_protection_class.method
            )

        # 2. Фильтр по группе (rating >= текущей)
        if self.hazardous_group:
            queryset = queryset.filter(
                hazardous_group__rating__gte=self.hazardous_group.rating,
                hazardous_group__group_type=self.hazardous_group.group_type
            )

        # 3. Фильтр по температуре
        if self.temperature_class:
            queryset = queryset.filter(
                temperature_rating__gte=self.temperature_class.strictness_rating
            )
        elif self.dust_temperature:
            queryset = queryset.filter(
                temperature_rating__lte=self.dust_temperature
            )

        return set(queryset.values_list('id', flat=True))

    @classmethod
    def get_compatible_ids_by_components(cls, method_id: int = None, type_id: int = None,
                                         group_id: int = None,temp_id: int = None) -> set:
        """
        Возвращает ID всех ExdOption, совместимых с выбранными компонентами.

        Args:
            method_id: ID метода взрывозащиты (ExplosionProtectionMethod)
            type_id: ID типа взрывозащиты (ExplosionProtectionType)
            gas_group_id: ID газовой группы (HazardousGroup)
            dust_group_id: ID пылевой группы (HazardousGroup)
            temp_id: ID температурного класса (TemperatureClass)
        Вход: Параметры (method_id, type_id...)	Выход: ID совместимых	Когда использовать: Когда пользователь выбирает через UI компоненты
        Returns:
            set: множество ID совместимых ExdOption
        """
        print(f"DEBUG: get_compatible_ids_by_components called with:")
        print(f"  method_id={method_id}, type_id={type_id}")
        print(f"  group_id={group_id}")
        print(f"  temp_id={temp_id}")

        queryset = cls.objects.filter(is_active=True)
        print(f"  Initial queryset count: {queryset.count()}")

        if type_id:
            queryset = queryset.filter(explosion_protection_class_id=type_id)
            print(f"  After type filter (id={type_id}): {queryset.count()}")
        elif method_id:
            type_ids = ExplosionProtectionType.objects.filter(
                method_id=method_id, is_active=True
            ).values_list('id', flat=True)
            print(f"  Found type_ids for method {method_id}: {list(type_ids)}")
            queryset = queryset.filter(explosion_protection_class_id__in=type_ids)
            print(f"  After method filter: {queryset.count()}")

        if group_id:
            group = HazardousGroup.objects.get(id=group_id)
            queryset = queryset.filter(
                hazardous_group__rating__gte=group.rating,
                hazardous_group__group_type=group.group_type
            )
            print(f"  After gas/dust group filter: {queryset.count()}")

        if temp_id:
            is_dust = False
            if group_id:
                try:
                    group = HazardousGroup.objects.get(id=group_id)
                    is_dust = group.group_type == 'DUST'
                except HazardousGroup.DoesNotExist:
                    pass
            if not is_dust:
                temp_class = TemperatureClass.objects.get(id=temp_id)
                print(f"  Temp class: {temp_class.code}, strictness_rating={temp_class.strictness_rating}")
                queryset = queryset.filter(
                    temperature_rating__gte=temp_class.strictness_rating
                )
                print(f"  After temp filter: {queryset.count()}")

        result = set(queryset.values_list('id', flat=True))
        print(f"  Final compatible IDs: {result}")
        return result
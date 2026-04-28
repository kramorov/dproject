# params/exd_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import TextDescriptionMixin, OptionListToSelectMixin


class ExdRequirementsMixin(models.Model):
    """
    Миксин для добавления требований к взрывозащите в модель.
    Позволяет выбрать тип взрывозащиты двумя способами:
    1. Быстрый выбор: из предустановленных популярных типов
    2. Расширенный: сконструировать свой тип через связи
    """

    # Быстрый выбор - популярные типы взрывозащиты
    QUICK_EXD_CHOICES = [
        ('NONE', _('Не требуется')),
        ('EXD_SIMPLE', _('Exd (взрывонепроницаемая оболочка)')),
        ('EXE_SIMPLE', _('Exe (повышенная надежность)')),
        ('EXI_SIMPLE', _('Exi (искробезопасная цепь)')),
        ('EXIA_SIMPLE', _('Exia (искробезопасная - высшая степень)')),
        ('EXNA_SIMPLE', _('ExnA (неискрящее)')),
        ('EXD_IIB_T4_GB', _('Ex d IIB T4 Gb')),
        ('EXD_IIC_T6_GB', _('Ex d IIC T6 Gb')),
        ('EXE_IIC_GB', _('Ex e IIC Gb')),
        ('EXTB_IIIC_DB', _('Ex tb IIIC Db (пыль)')),
        ('EXD_IIC_T6_GB_EXTB_IIIC_DB', _('Ex d IIC T6 Gb + Ex tb IIIC Db (газ+пыль)')),
    ]

    # Способ выбора: быстрый или расширенный
    exd_selection_mode = models.CharField(
        max_length=20,
        choices=[('QUICK', _('Быстрый выбор')), ('ADVANCED', _('Расширенный конструктор'))],
        default='QUICK',
        verbose_name=_("Способ выбора взрывозащиты"),
        help_text=_("Быстрый выбор - из популярных типов, Расширенный - сконструировать свой")
    )

    # Быстрый выбор - предустановленный тип
    quick_exd_type = models.CharField(
        max_length=50,
        choices=QUICK_EXD_CHOICES,
        default='NONE',
        verbose_name=_("Быстрый выбор взрывозащиты"),
        help_text=_("Выберите тип взрывозащиты из популярных вариантов")
    )

    # Расширенный выбор - связи с существующими типами
    custom_exd_option = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_related',
        verbose_name=_("Конструктор взрывозащиты"),
        help_text=_("Выберите сконструированный тип взрывозащиты")
    )

    # Отдельные компоненты для расширенного конструирования (опционально)
    custom_gas_protection_types = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='%(app_label)s_%(class)s_gas_types',
        limit_choices_to={'equipment_type': 'SIMPLE',
                          'name__in': ['Ex d', 'Ex e', 'Ex i', 'Ex ia', 'Ex ib', 'Ex n', 'Ex nA', 'Ex m', 'Ex p']},
        verbose_name=_("Типы газовой взрывозащиты"),
        help_text=_("Ex d, Ex e, Ex i и т.д.")
    )

    custom_gas_group = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_gas_group',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__in': ['IIA', 'IIB', 'IIC']},
        verbose_name=_("Группа газа"),
        help_text=_("IIA, IIB, IIC")
    )

    custom_temperature_class = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_temp_class',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__startswith': 'T'},
        verbose_name=_("Температурный класс"),
        help_text=_("T1-T6")
    )

    custom_gas_protection_level = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_gas_level',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__in': ['Ga', 'Gb', 'Gc']},
        verbose_name=_("Уровень газовой защиты"),
        help_text=_("Ga, Gb, Gc")
    )

    custom_dust_protection_types = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='%(app_label)s_%(class)s_dust_types',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__in': ['Ex t', 'Ex tb', 'Ex p', 'Ex i']},
        verbose_name=_("Типы пылевой взрывозащиты"),
        help_text=_("Ex t, Ex tb, Ex p и т.д.")
    )

    custom_dust_group = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_dust_group',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__in': ['IIIA', 'IIIB', 'IIIC']},
        verbose_name=_("Группа пыли"),
        help_text=_("IIIA, IIIB, IIIC")
    )

    custom_dust_temperature = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Температура для пыли, °C"),
        help_text=_("Максимальная температура поверхности")
    )

    custom_dust_protection_level = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_dust_level',
        limit_choices_to={'equipment_type': 'SIMPLE', 'name__in': ['Da', 'Db', 'Dc']},
        verbose_name=_("Уровень пылевой защиты"),
        help_text=_("Da, Db, Dc")
    )

    custom_has_x_suffix = models.BooleanField(
        default=False,
        verbose_name=_("Специальные условия (X)"),
        help_text=_("Добавить X в конце маркировки")
    )

    class Meta:
        abstract = True

    def get_exd_requirement(self):
        """
        Возвращает объект ExdOption на основе выбранного способа.
        Если выбран быстрый тип - возвращает соответствующий объект.
        Если расширенный - возвращает custom_exd_option или создает временный объект.
        """
        if self.exd_selection_mode == 'QUICK':
            return self._get_quick_exd_object()
        else:
            return self.custom_exd_option

    def _get_quick_exd_object(self):
        """Возвращает объект ExdOption для быстрого выбора"""
        mapping = {
            'EXD_SIMPLE': {'name': 'Ex d', 'equipment_type': 'SIMPLE'},
            'EXE_SIMPLE': {'name': 'Ex e', 'equipment_type': 'SIMPLE'},
            'EXI_SIMPLE': {'name': 'Ex i', 'equipment_type': 'SIMPLE'},
            'EXIA_SIMPLE': {'name': 'Ex ia', 'equipment_type': 'SIMPLE'},
            'EXNA_SIMPLE': {'name': 'Ex nA', 'equipment_type': 'SIMPLE'},
            'EXD_IIB_T4_GB': {'name': 'Ex d IIB T4 Gb', 'equipment_type': 'GAS'},
            'EXD_IIC_T6_GB': {'name': 'Ex d IIC T6 Gb', 'equipment_type': 'GAS'},
            'EXE_IIC_GB': {'name': 'Ex e IIC Gb', 'equipment_type': 'GAS'},
            'EXTB_IIIC_DB': {'name': 'Ex tb IIIC Db', 'equipment_type': 'DUST'},

        }

        if self.quick_exd_type == 'NONE':
            return None

        mapping_data = mapping.get(self.quick_exd_type)
        if mapping_data:
            return ExdOption.objects.filter(
                name=mapping_data['name'],
                equipment_type=mapping_data['equipment_type']
            ).first()

        return None

    def get_exd_display(self) -> str:
        """Возвращает отображаемое название взрывозащиты"""
        exd_obj = self.get_exd_requirement()
        if exd_obj:
            return exd_obj.name or exd_obj.exd_full_code
        return _("Не требуется")

    def get_exd_description(self) -> str:
        """Возвращает описание взрывозащиты"""
        exd_obj = self.get_exd_requirement()
        if exd_obj:
            return exd_obj.description or ""
        return ""

    def get_exd_code(self) -> str:
        """Возвращает код взрывозащиты"""
        exd_obj = self.get_exd_requirement()
        if exd_obj:
            return exd_obj.code or ""
        return ""


class SimpleExdMixin(models.Model):
    """
    Упрощенный миксин - только одно поле для выбора ExdOption.
    Используйте когда не нужен конструктор, только готовые типы.
    """

    exd_requirement = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Требования к взрывозащите"),
        help_text=_("Выберите тип взрывозащиты")
    )

    class Meta:
        abstract = True

    def get_exd_display(self) -> str:
        return self.exd_requirement.name if self.exd_requirement else _("Не требуется")

    def get_exd_description(self) -> str:
        return self.exd_requirement.description if self.exd_requirement else ""

    def get_exd_code(self) -> str:
        return self.exd_requirement.code if self.exd_requirement else ""

class GasGroup(models.Model, TextDescriptionMixin):
    """Группа газа (IIA, IIB, IIC, etc.)"""
    name = models.CharField(max_length=10, verbose_name=_("Название"))
    code = models.CharField(max_length=10, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    class Meta:
        verbose_name = _("Группа газа")
        verbose_name_plural = _("Группы газов")

    def __str__(self):
        return self.code

    def get_text_description(self) -> str:
        """Генерирует описание группы газа"""
        descriptions = {
            'IIA': _("пропан, метан, аммиак (наименее опасная)"),
            'IIB': _("этилен, коксовый газ (средняя опасность)"),
            'IIC': _("водород, ацетилен, сероуглерод (наиболее опасная)"),
        }
        return descriptions.get(self.code, self.description or self.name)


class DustGroup(models.Model, TextDescriptionMixin):
    """Группа пыли (IIIA, IIIB, IIIC)"""
    name = models.CharField(max_length=10, verbose_name=_("Название"))
    code = models.CharField(max_length=10, verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    class Meta:
        verbose_name = _("Группа пыли")
        verbose_name_plural = _("Группы пыли")

    def __str__(self):
        return self.code

    def get_text_description(self) -> str:
        """Генерирует описание группы пыли"""
        descriptions = {
            'IIIA': _("легковоспламеняющиеся летучие частицы (мука, зерно)"),
            'IIIB': _("непроводящая пыль (древесная, угольная)"),
            'IIIC': _("проводящая пыль (металлическая, графитовая)"),
        }
        return descriptions.get(self.code, self.description or self.name)


class TemperatureClass(models.Model, TextDescriptionMixin):
    """Температурный класс (T1-T6)"""
    temperature_class = models.CharField(max_length=5, verbose_name=_("Класс"))
    max_surface_temp = models.IntegerField(verbose_name=_("Макс. температура поверхности, °C"))
    gas_ignition_temp = models.IntegerField(
        null=True, blank=True,
        verbose_name=_("Температура воспламенения газа, °C")
    )

    class Meta:
        verbose_name = _("Температурный класс")
        verbose_name_plural = _("Температурные классы")

    def __str__(self):
        return f"{self.temperature_class}"

    def get_text_description(self) -> str:
        """Генерирует описание температурного класса"""
        return _(
            "Максимальная температура поверхности %(temp)s°C, допустима для газов с температурой воспламенения выше %(ignition)s°C"
        ) % {
            'temp': self.max_surface_temp,
            'ignition': self.max_surface_temp
        }


class ExplosionProtectionType(models.Model, TextDescriptionMixin):
    """Тип взрывозащиты (Ex d, Ex e, Ex i, etc.)"""

    class ProtectionCategory(models.TextChoices):
        GAS = 'GAS', _('Газ')
        DUST = 'DUST', _('Пыль')

    code = models.CharField(max_length=10, verbose_name=_("Код"))
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    category = models.CharField(
        max_length=10,
        choices=ProtectionCategory.choices,
        default=ProtectionCategory.GAS,
        verbose_name=_("Категория")
    )

    class Meta:
        verbose_name = _("Тип взрывозащиты")
        verbose_name_plural = _("Типы взрывозащиты")

    def __str__(self):
        return f"Ex{self.code}"

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

    class Meta:
        verbose_name = _("Уровень взрывозащиты")
        verbose_name_plural = _("Уровни взрывозащиты")

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

    # Новые поля для конструирования
    equipment_type = models.CharField(
        max_length=10,
        choices=EquipmentType.choices,
        default=EquipmentType.SIMPLE,
        verbose_name=_("Тип оборудования")
    )

    # Для газовой взрывозащиты - используем строковые ссылки с указанием приложения
    gas_protection_types = models.ManyToManyField(
        'params.ExdOption',  # Исправлено: 'app_label.ModelName'
        blank=True,
        symmetrical=False,
        related_name='gas_protection_for',
        verbose_name=_("Типы взрывозащиты (газ)"),
        help_text=_("Ex d, Ex e, Ex i, Ex n, Ex m и т.д.")
    )

    gas_group = models.ForeignKey(
        'params.ExdOption',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gas_group_for',
        verbose_name=_("Группа газа"),
        help_text=_("IIA, IIB, IIC (хранятся как отдельные записи с equipment_type='SIMPLE')")
    )

    temperature_class = models.ForeignKey(
        'params.ExdOption',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temp_class_for',
        verbose_name=_("Температурный класс"),
        help_text=_("T1-T6 (хранятся как отдельные записи с equipment_type='SIMPLE')")
    )

    gas_protection_level = models.ForeignKey(
        'params.ExdOption',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gas_level_for',
        verbose_name=_("Уровень взрывозащиты (газ)"),
        help_text=_("Ga, Gb, Gc (хранятся как отдельные записи с equipment_type='SIMPLE')")
    )

    # Для пылевой взрывозащиты
    dust_protection_types = models.ManyToManyField(
        'params.ExdOption',  # Исправлено
        blank=True,
        symmetrical=False,
        related_name='dust_protection_for',
        verbose_name=_("Типы взрывозащиты (пыль)"),
        help_text=_("Ex t, Ex p, Ex i и т.д.")
    )

    dust_group = models.ForeignKey(
        'params.ExdOption',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dust_group_for',
        verbose_name=_("Группа пыли"),
        help_text=_("IIIA, IIIB, IIIC (хранятся как отдельные записи с equipment_type='SIMPLE')")
    )

    dust_temperature = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Температура для пыли, °C"),
        help_text=_("Максимальная температура поверхности (например, 85, 95, 100)")
    )

    dust_protection_level = models.ForeignKey(
        'params.ExdOption',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dust_level_for',
        verbose_name=_("Уровень взрывозащиты (пыль)"),
        help_text=_("Da, Db, Dc (хранятся как отдельные записи с equipment_type='SIMPLE')")
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
        verbose_name_plural = _('Типы взрывозащиты')
        ordering = ['sorting_order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_exd_full_code = self.exd_full_code

    def _generate_gas_marking(self) -> str:
        """Генерирует маркировку для газового оборудования"""
        if not self.gas_protection_types.exists():
            return ""

        # Ex + типы взрывозащиты (через пробел)
        protection_types = " ".join([p.name for p in self.gas_protection_types.all()])

        # Группа газа
        group = f" {self.gas_group.name}" if self.gas_group else ""

        # Температурный класс
        temp_class = f" {self.temperature_class.name}" if self.temperature_class else ""

        # Уровень взрывозащиты
        level = f" {self.gas_protection_level.name}" if self.gas_protection_level else ""

        return f"{protection_types}{group}{temp_class}{level}"

    def _generate_dust_marking(self) -> str:
        """Генерирует маркировку для пылевого оборудования"""
        if not self.dust_protection_types.exists():
            return ""

        # Ex + типы взрывозащиты
        protection_types = " ".join([p.name for p in self.dust_protection_types.all()])

        # Группа пыли
        group = f" {self.dust_group.name}" if self.dust_group else ""

        # Температурный класс
        temp_class = f" T{self.dust_temperature}°C" if self.dust_temperature else ""

        # Уровень взрывозащиты
        level = f" {self.dust_protection_level.name}" if self.dust_protection_level else ""

        return f"{protection_types}{group}{temp_class}{level}"

    def generate_full_code(self) -> str:
        """Генерирует полную маркировку взрывозащиты"""
        # Простая маркировка (Exd, ExnA, Exia и т.д.)
        if self.equipment_type == self.EquipmentType.SIMPLE:
            return self.name or self.exd_full_code or ""

        markings = []

        # Газовое оборудование
        if self.equipment_type == self.EquipmentType.GAS:
            gas_marking = self._generate_gas_marking()
            if gas_marking:
                markings.append(gas_marking)

        # Пылевое оборудование
        if self.equipment_type == self.EquipmentType.DUST:
            dust_marking = self._generate_dust_marking()
            if dust_marking:
                markings.append(dust_marking)

        # Суффиксы
        suffix = ""
        if self.has_x_suffix:
            suffix = " X"
        if self.has_u_suffix:
            suffix = " U"

        result = ", ".join(markings) + suffix
        return result.strip()

    def _generate_description(self) -> str:
        """Генерирует текстовое описание взрывозащиты"""
        if self.equipment_type == self.EquipmentType.SIMPLE:
            return self._get_simple_description()

        descriptions = []

        # Газовое оборудование
        if self.equipment_type == self.EquipmentType.GAS:
            gas_desc = self._get_gas_description()
            if gas_desc:
                descriptions.append(gas_desc)

        # Пылевое оборудование
        if self.equipment_type == self.EquipmentType.DUST:
            dust_desc = self._get_dust_description()
            if dust_desc:
                descriptions.append(dust_desc)

        # Суффиксы
        suffix_desc = self._get_suffix_description()
        if suffix_desc:
            descriptions.append(suffix_desc)

        return " | ".join(descriptions)

    def _get_simple_description(self) -> str:
        """Описание для простой маркировки"""
        descriptions = {
            'Ex d': str(_("Взрывонепроницаемая оболочка - корпус выдерживает внутреннее давление взрыва")),
            'Ex e': str(_("Повышенная надежность - исключены искры и опасные температуры в нормальном режиме")),
            'Ex i': str(_("Искробезопасная цепь - энергия искры ограничена безопасным уровнем")),
            'Ex ia': str(_("Искробезопасная цепь (ia) - очень высокая степень защиты для Зоны 0")),
            'Ex ib': str(_("Искробезопасная цепь (ib) - высокая степень защиты для Зоны 1")),
            'Ex n': str(_("Неискрящее оборудование - искры не возникают в нормальном режиме")),
            'Ex nA': str(_("Неискрящее оборудование (nA) - для Зоны 2")),
            'Ex m': str(_("Герметизация компаундом - искроопасные части залиты компаундом")),
            'Ex p': str(_("Заполнение под избыточным давлением - внутри оболочки поддерживается избыточное давление")),
            'Ex t': str(_("Защита оболочкой для пыли - пыленепроницаемая оболочка")),
            'Ex tb': str(_("Защита оболочкой для пыли (tb) - высокая степень защиты для Зоны 21")),
        }
        return descriptions.get(self.name, self.description or self.name)

    def _get_gas_description(self) -> str:
        """Описание газовой взрывозащиты"""
        parts = []

        # Типы защиты
        if self.gas_protection_types.exists():
            types = [p.name for p in self.gas_protection_types.all()]
            parts.append(str(_("Взрывозащита: %(types)s") % {'types': ", ".join(types)}))

        # Группа газа
        if self.gas_group:
            gas_descriptions = {
                'IIA': str(_("группа IIA - пропан, метан (наименее опасная)")),
                'IIB': str(_("группа IIB - этилен (средняя опасность)")),
                'IIC': str(_("группа IIC - водород, ацетилен (наиболее опасная)")),
            }
            parts.append(gas_descriptions.get(self.gas_group.name, self.gas_group.description or ""))

        # Температурный класс
        if self.temperature_class:
            temp_value = getattr(self.temperature_class, 'max_surface_temp', 0)
            parts.append(str(_("температурный класс %(class)s - макс. температура поверхности %(temp)s°C") % {
                'class': self.temperature_class.name,
                'temp': temp_value
            }))

        # Уровень защиты
        if self.gas_protection_level:
            level_descriptions = {
                'Ga': str(_("уровень Ga - очень высокая степень защиты для Зоны 0")),
                'Gb': str(_("уровень Gb - высокая степень защиты для Зоны 1")),
                'Gc': str(_("уровень Gc - нормальная степень защиты для Зоны 2")),
            }
            parts.append(
                level_descriptions.get(self.gas_protection_level.name, self.gas_protection_level.description or ""))

        return " (" + " | ".join(parts) + ")" if parts else ""

    def _get_dust_description(self) -> str:
        """Описание пылевой взрывозащиты"""
        parts = []

        # Типы защиты
        if self.dust_protection_types.exists():
            types = [p.name for p in self.dust_protection_types.all()]
            parts.append(str(_("Пылезащита: %(types)s") % {'types': ", ".join(types)}))

        # Группа пыли
        if self.dust_group:
            dust_descriptions = {
                'IIIA': str(_("группа IIIA - легковоспламеняющиеся летучие частицы (мука, зерно)")),
                'IIIB': str(_("группа IIIB - непроводящая пыль (древесная, угольная)")),
                'IIIC': str(_("группа IIIC - проводящая пыль (металлическая, графитовая)")),
            }
            parts.append(dust_descriptions.get(self.dust_group.name, self.dust_group.description or ""))

        # Температура
        if self.dust_temperature:
            parts.append(str(_("максимальная температура поверхности: %(temp)s°C") % {'temp': self.dust_temperature}))

        # Уровень защиты
        if self.dust_protection_level:
            level_descriptions = {
                'Da': str(_("уровень Da - очень высокая степень защиты для Зоны 20")),
                'Db': str(_("уровень Db - высокая степень защиты для Зоны 21")),
                'Dc': str(_("уровень Dc - нормальная степень защиты для Зоны 22")),
            }
            parts.append(
                level_descriptions.get(self.dust_protection_level.name, self.dust_protection_level.description or ""))

        return " (" + " | ".join(parts) + ")" if parts else ""

    def _get_suffix_description(self) -> str:
        """Описание суффиксов"""
        suffixes = []
        if self.has_x_suffix:
            suffixes.append(str(_("X - специальные условия безопасной эксплуатации")))  # Обернуть в str()
        if self.has_u_suffix:
            suffixes.append(str(_("U - только компонент взрывозащищенного оборудования")))  # Обернуть в str()
        return " | ".join(suffixes) if suffixes else ""

    def save(self, *args, **kwargs):
        """При сохранении генерируем код, название и описание"""

        # Получаем параметр skip_auto_generate
        skip_auto_generate = kwargs.pop('skip_auto_generate', False)

        if not skip_auto_generate:
            # Генерируем полный код (маркировку)
            generated = self.generate_full_code()
            if generated:
                self.generated_full_code = generated

                # Если exd_full_code не заполнен вручную, используем сгенерированный
                if not self.exd_full_code or self.exd_full_code == getattr(self, '_old_exd_full_code', ''):
                    self.exd_full_code = generated

            # Формируем name (код взрывозащиты) - это человекочитаемая маркировка
            if self.exd_full_code:
                self.name = self.exd_full_code
            elif generated:
                self.name = generated
            elif not self.name:
                self.name = "Exd"

            # Формируем description (текстовое описание)
            if not self.description:
                self.description = self._generate_description()

            # Формируем code (уникальный идентификатор из параметров)
            if not self.code:
                base_code = self._generate_code_from_params()
                self.code = self._ensure_unique_code(base_code)

        super().save(*args, **kwargs)

    def _generate_code_from_params(self) -> str:
        """Генерирует код из параметров взрывозащиты"""
        if self.equipment_type == self.EquipmentType.SIMPLE:
            code = self.name or self.exd_full_code or ""
            return code.replace(' ', '').replace('°C', '').replace('°', '')

        parts = []

        if self.equipment_type == self.EquipmentType.GAS:
            gas_code = self._generate_gas_code()
            if gas_code:
                parts.append(gas_code)

        if self.equipment_type== self.EquipmentType.DUST:
            dust_code = self._generate_dust_code()
            if dust_code:
                parts.append(dust_code)

        result = "__".join(parts)

        if self.has_x_suffix:
            result += "-X"
        if self.has_u_suffix:
            result += "-U"

        return result

    def _generate_gas_code(self) -> str:
        """Генерирует код для газовой взрывозащиты"""
        code_parts = []

        if self.gas_protection_types.exists():
            types = [p.name.replace(' ', '') for p in self.gas_protection_types.all()]
            code_parts.append(''.join(types))

        if self.gas_group:
            code_parts.append(self.gas_group.name)

        if self.temperature_class:
            code_parts.append(self.temperature_class.name)

        if self.gas_protection_level:
            code_parts.append(self.gas_protection_level.name)

        return ''.join(code_parts)

    def _generate_dust_code(self) -> str:
        """Генерирует код для пылевой взрывозащиты"""
        code_parts = []

        if self.dust_protection_types.exists():
            types = [p.name.replace(' ', '') for p in self.dust_protection_types.all()]
            code_parts.append(''.join(types))

        if self.dust_group:
            code_parts.append(self.dust_group.name)

        if self.dust_temperature:
            code_parts.append(f"T{self.dust_temperature}")

        if self.dust_protection_level:
            code_parts.append(self.dust_protection_level.name)

        return ''.join(code_parts)

    def _ensure_unique_code(self, base_code: str) -> str:
        """Обеспечивает уникальность кода"""
        if not base_code:
            base_code = f"exd-{self.id}" if self.id else "exd-temp"

        # Проверяем, существует ли такой код у других записей
        existing = ExdOption.objects.filter(code=base_code).exclude(id=self.id)

        if not existing.exists():
            return base_code

        # Если код существует, добавляем номер
        counter = 1
        while ExdOption.objects.filter(code=f"{base_code}-{counter}").exclude(id=self.id).exists():
            counter += 1

        return f"{base_code}-{counter}"

    def __str__(self):
        return self.name or self.exd_full_code or "Exd"

    def __eq__(self, other):
        """Сравнение двух типов взрывозащиты"""
        if isinstance(other, ExdOption):
            return self.generated_full_code == other.generated_full_code
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.generated_full_code)
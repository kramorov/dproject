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

    class Meta :
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

    explosion_protection_class = models.ForeignKey(
        'params.ExplosionProtectionType' ,  # Исправлено
        on_delete=models.SET_NULL ,
        null=True ,
        blank=True ,
        related_name='explosion_protection_class_for_exd' ,
        verbose_name=_("Температурный класс") ,
        help_text=_("T1-T6 (хранятся как отдельные записи с equipment_type='SIMPLE')")
    )

    temperature_class = models.ForeignKey(
        'params.TemperatureClass',  # Исправлено
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temp_class_for_exd',
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

    def __str__(self):
        return self.name or self.exd_full_code or "Exd"


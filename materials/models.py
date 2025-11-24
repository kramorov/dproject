# materials/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# from djangoProject1.common_models.eav_mixins import EAVMixin

class WorkingMedium(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название рабочей среды")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код рабочей среды"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание рабочей среды'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Название рабочей среды')
        verbose_name_plural = _('Название рабочей среды')

    def __str__(self):
        return self.name

class MaterialGeneral(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Общее название типа материала")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа материала"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа материала'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Общее название типа материала')
        verbose_name_plural = _('Общие названия типов материалов')

    def __str__(self):
        return self.name


class MaterialGeneralMoreDetailed(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название уточненного типа материала")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код уточненного типа материала"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание уточненного типа материала'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    material_general = models.ForeignKey(
        MaterialGeneral,
        on_delete=models.CASCADE,
        related_name='detailed_materials',
        verbose_name=_("Общий тип материала"),
        help_text=_("Общая категория материала")
    )

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Уточненный тип материала')
        verbose_name_plural = _('Уточненные типы материалов')

    def __str__(self):
        return self.name


class MaterialStandard(models.Model):
    """Справочник стандартов (ГОСТ, AISI, DIN, ASTM, EN, etc.)"""
    name = models.CharField(max_length=50, verbose_name=_("Название стандарта"))
    code = models.CharField(max_length=10, verbose_name=_("Код стандарта"), unique=True)
    description = models.CharField(max_length=200, blank=True, verbose_name=_("Описание стандарта"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        ordering = ['sorting_order']
        verbose_name = _("Стандарт материала")
        verbose_name_plural = _("Стандарты материалов")

    def __str__(self):
        return f"{self.name} ({self.code})"


class MaterialSpecified(models.Model):
    """Уточненная спецификация материала"""
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Автоматически генерируется из основной кодировки, если указан стандарт")
                            )
    code = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа материала"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа материала'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    # ---------------- End new data
    work_temp_min = models.IntegerField(
        default=-50,  # Добавлено значение по умолчанию
        help_text=_('Минимальная рабочая температура уточненного типа материала, °С'),
        verbose_name=_('Минимальная рабочая температура уточненного типа материала, °С')
    )
    work_temp_max = models.IntegerField(
        default=150,  # Добавлено значение по умолчанию
        help_text=_('Максимальная рабочая температура уточненного типа материала, °С'),
        verbose_name=_('Максимальная рабочая температура уточненного типа материала, °С')
    )
    temp_min = models.IntegerField(
        default=-50,  # Добавлено значение по умолчанию
        verbose_name=_("Минимальная температура уточненного типа материала, °С")
    )
    temp_max = models.IntegerField(
        default=150,  # Добавлено значение по умолчанию
        verbose_name=_("Максимальная температура уточненного типа материала, °С")
    )
    material_general = models.ForeignKey(
        MaterialGeneral,
        on_delete=models.CASCADE,
        related_name='specified_materials',
        verbose_name=_("Общий тип материала")
    )
    material_detailed = models.ForeignKey(
        MaterialGeneralMoreDetailed,
        on_delete=models.CASCADE,
        related_name='specified_materials',
        verbose_name=_("Уточненный тип материала")
    )
    features_text = models.TextField(blank=True , verbose_name=_("Особенности"))
    application_text = models.TextField(blank=True , verbose_name=_("Где применяется"))

    class Meta:
        ordering = ['sorting_order','material_general', 'material_detailed']
        verbose_name = _("Спецификация материала")
        verbose_name_plural = _("Спецификации материалов")
        indexes = [
            models.Index(fields=['material_general']),
            models.Index(fields=['material_detailed']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name or f"Material-{self.id}"

    def clean(self):
        """Валидация температур"""
        if self.temp_min >= self.temp_max:
            raise ValidationError(_("Минимальная температура должна быть меньше максимальной"))

    def get_primary_code(self):
        """Получить основную кодировку материала"""
        primary_code = self.standard_codes.filter(is_primary=True).first()
        return primary_code.code if primary_code else _("Без кода")

    def get_all_codes(self):
        """Получить все кодировки материала"""
        return {code.standard.code: code.code for code in self.standard_codes.all()}

    def update_name(self):
        """Обновить symbolic_code на основе кодов в стандартах"""
        # Получаем все коды материала
        codes = self.standard_codes.select_related('standard').filter(code__isnull=False).exclude(code='')

        if not codes.exists():
            # Если нет валидных кодов
            # if self.material_detailed and self.material_detailed.symbolic_code:
            #     self.symbolic_code = self.material_detailed.symbolic_code
            # else:
            #     self.symbolic_code = f"Material-{self.id}"
            return

        # Разделяем и сортируем коды
        primary_codes = []
        other_codes = []

        for code in codes:
            if code.is_primary:
                primary_codes.append(code)
            else:
                other_codes.append(code)

        # Сортируем other_codes по имени стандарта
        other_codes.sort(key=lambda x: x.standard.name)

        # Объединяем (primary first, затем остальные)
        all_codes = primary_codes + other_codes

        # Формируем symbolic_code
        code_parts = []
        for code in all_codes:
            if code.code:  # Проверяем что код не пустой
                code_parts.append(f"{code.standard.name}: {code.code}")

        if code_parts:
            self.name = ", ".join(code_parts)
        else:
            # Если все коды оказались пустыми
            self.name = self.material_detailed.name if self.material_detailed else f"Material-{self.id}"

        # print(f'MaterialSpecified.update_name: {self.symbolic_code}')

class MaterialChemicalResistance(models.Model):
    class ResistanceType(models.TextChoices):
        EXCELLENT = '4', _('Отлично')
        GOOD = '3', _('Хорошо')
        POSSIBLE = '2', _('Нежелательно, но возможно')
        NOT_ALLOWED = '1', _('Не применяется')
        NO_NOT_USE = '0', _('Не указано')

    resistance_type = models.CharField(
        max_length=20,
        choices=ResistanceType.choices,
        default=ResistanceType.NO_NOT_USE,
        verbose_name=_('Применимость')
    )
    material_specified = models.ForeignKey(
        MaterialSpecified,
        on_delete=models.CASCADE,
        related_name='material_chemical_resistance',
        verbose_name=_("Материал"))
    working_medium = models.ForeignKey(
        WorkingMedium,
        on_delete=models.CASCADE,
        related_name='material_chemical_resistance',
        verbose_name=_("Рабочая среда"))

    class Meta:
        verbose_name = _('Возможность применения материала в рабочей среде')
        verbose_name_plural = _('Применимость материалов к рабочей среде')

    def __str__(self):
        return f"{self.material_specified.name}:{self.resistance_type}"

class MaterialCode(models.Model):
    """Кодировка материала в конкретном стандарте"""
    material_specified = models.ForeignKey(
        MaterialSpecified,
        on_delete=models.CASCADE,
        related_name='standard_codes',
        verbose_name=_("Спецификация материала")
    )
    standard = models.ForeignKey(
        MaterialStandard,
        on_delete=models.CASCADE,
        related_name='material_codes',
        verbose_name=_("Стандарт")
    )
    code = models.CharField(max_length=50, verbose_name=_("Код в стандарте"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Основная кодировка"))

    class Meta:
        ordering = ['standard', 'code']
        unique_together = ['material_specified', 'standard', 'code']  # Исправлено
        verbose_name = _("Код материала в стандарте")
        verbose_name_plural = _("Коды материалов в стандартах")

    def __str__(self):
        return f"{self.standard.code}:{self.code}"

    def clean(self):
        """Валидация: только один primary код на материал"""
        if self.is_primary:
            existing_primary = MaterialCode.objects.filter(
                material_specified=self.material_specified,
                is_primary=True
            ).exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(_("Может быть только один основной код для материала"))


class MaterialService:
    """Сервис для работы с материалами и аналогами"""

    @staticmethod
    def find_material_by_standard(standard_code, material_code):
        """Найти материал по коду в стандарте"""
        try:
            material_code_obj = MaterialCode.objects.select_related(
                'material_specified'
            ).get(
                standard__code=standard_code,
                code=material_code
            )
            return material_code_obj.material_specified
        except MaterialCode.DoesNotExist:
            return None
    @staticmethod
    def create_material_with_codes(material_data, standard_codes, primary_standard=None):
        """Создать материал с кодировками в стандартах"""
        # Сначала создаем материал без symbolic_code
        material_data = material_data.copy()
        material_data.pop('symbolic_code', None)  # Удаляем symbolic_code если есть

        material = MaterialSpecified.objects.create(**material_data)

        # Создаем коды
        for standard_code, code_value in standard_codes.items():
            try:
                standard = MaterialStandard.objects.get(code=standard_code)
                is_primary = (primary_standard and standard_code == primary_standard) or (
                        not primary_standard and standard_code == 'GOST'
                )

                MaterialCode.objects.create(
                    material_specified=material,
                    standard=standard,
                    code=code_value,
                    is_primary=is_primary
                )
            except MaterialStandard.DoesNotExist:
                continue

        # Обновляем symbolic_code
        material.update_name()
        material.save()
        return material


@receiver(post_save, sender=MaterialCode)
def update_material_on_code_save(sender, instance, **kwargs):
    """Обновить symbolic_code материала при изменении кодов"""
    if instance.material_specified_id:  # Проверяем что материал сохранен
        try:
            instance.material_specified.update_name()
            instance.material_specified.save()
        except:
            pass  # Игнорируем ошибки при обновлении


@receiver(post_save, sender=MaterialSpecified)
def update_material_on_save(sender, instance, **kwargs):
    """Обновить symbolic_code при сохранении материала"""
    if instance.pk and not instance.name:  # Проверяем что объект сохранен
        try:
            instance.update_name()
            instance.save()
        except:
            pass  # Игнорируем ошибки при обновлении

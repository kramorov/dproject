# valve_data/models/dimension_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from core.models.mixins import LocalizedDictFieldsMixin

class WeightDimensionParameterVariety(LocalizedDictFieldsMixin):
    """Справочник параметров предопределенных параметров ВГХ - выбирается  DimensionTableParameter
        Нужен для сравнения моделей, отбора по значениям параметра, формирования паспорта на изделие и
        технички на серию"""

    # Предопределенные категории с иконками, описанием и порядком
    PREDEFINED_PARAMETERS = [
        ('WEIGHT', 'Вес изделия, кг'),
        ('L-face-to-face-length', 'L - строительная длина,мм'),
        ('L0-overall-length', 'L0 - габаритная длина, мм'),
        ('Lh-handle-length-from-axis', 'Lh - длина рукоятки от оси, мм'),
        ('D1-disk-diameter', 'D1 - диаметр диска, мм'),
        ('D2-center-distance-connecting-flanges', 'D2-межосевое расстояние присоединительных отверстий (фланцев), мм'),
        ('D3-outer-diameter-connecting-flange', 'D3-внешний диаметр присоединительного фланца, мм'),
        ('N-bolt-hole-diameter', 'NxD4- кол-во и диаметр присоединительных отверстий (фланцев), мм'),
        ('D5-outer-diameter-connecting-flange', 'D5-внешний диаметр присоединительного выступа, фланцев, мм'),
        ('C-flange-thickness', 'C-толщина фланцев, мм'),
        ('D6-diameter-gearbox-steering-wheel', 'D6 - диаметр штурвала редуктора, мм'),
        ('Hl', 'Высота штока, мм'),
        ('H1', 'H1 - расстояние от оси трубопроводода до нижней части, мм'),
        ('H2', 'H2 - расстояние от оси трубопроводода до оси редуктора, мм'),
        ('A', 'A - расстояние от оси трубопроводода до верха монтажной площадки, мм'),
        ('B1', 'B1 - диаметр штока, мм'),
        ('B2', 'B2 - шпонка, мм'),
        ('B3', 'B3 - квадрат штока, мм'),
        ('mounting-plate', 'Тип верхнего монтажного фланца по ISO 5210 (ISO 5211)'),
    ]

    PREDEFINED_CODES = [code for code, name in PREDEFINED_PARAMETERS]  # список кодов

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_("Название"),
        help_text=_("Уникальное название параметра")
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код параметра (латинские буквы, цифры, подчеркивания)")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Подробное описание параметра")
    )

    is_predefined = models.BooleanField(
        default=False,
        verbose_name=_("Предопределенная"),
        help_text=_("Предопределенный параметр - удалять нельзя, могут быть ссылки на него"),
        editable=False
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активна")
    )
    class Meta:
        verbose_name = _("Параметр ВГХ")
        verbose_name_plural = _("Параметры ВГХ")
        ordering = ['name']
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self):
        predefined_marker = "⚙️ " if self.is_predefined else "📁 "
        return f"{predefined_marker}{self.name}"

    def save(self, *args, **kwargs):
        # Автоматически определяем предопределенные категории
        self.is_predefined = self.code in self.PREDEFINED_CODES

        # Валидация кода
        if not self._validate_code():
            raise ValidationError(_("Код должен содержать только латинские буквы, цифры и подчеркивания"))

        super().save(*args, **kwargs)

    def _validate_code(self) :
        """Валидация формата кода"""
        # Разрешаем латинские буквы, цифры, подчеркивания И дефисы
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        print(self.code)
        return bool(re.match(pattern , self.code))

    def clean(self):
        """Дополнительная валидация"""
        errors = {}
        if self.code in self.PREDEFINED_PARAMETERS and not self.is_predefined:
            errors['code'] = _('Код "%(code)s" зарезервирован для предопределенного параметра') % {'code': self.code}

        if errors:
            raise ValidationError(errors)

    @classmethod
    def get_or_create_predefined(cls):
        """Создает предопределенные категории при необходимости"""
        for code, name in cls.PREDEFINED_PARAMETERS:
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_predefined': True,
                }
            )

    @property
    def is_user_defined(self):
        """Является ли категория пользовательской"""
        return not self.is_predefined

    @property
    def can_delete(self):
        """Можно ли удалить категорию"""
        # return not self.is_predefined and not self.media_items.exists()
        return not self.is_predefined
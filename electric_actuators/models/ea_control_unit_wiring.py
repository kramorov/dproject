# electric_actuators/models/ea_control_unit_wiring.py
"""
ControlUnitWiring — справочник связок БУ+напряжение+профиль+схема.

Одна запись = один вариант схемы подключения для конкретной комбинации
(тип БУ, напряжение питания, профиль сигналов, изображение схемы).

Переиспользуется между model_line_item через ElectricControlUnitOption.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.mixins import CopyMixin


class ControlUnitWiring(CopyMixin, models.Model):
    """Справочник: БУ + напряжение + профиль сигналов + изображение схемы."""

    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption',
        on_delete=models.CASCADE,
        related_name='control_unit_wirings',
        verbose_name=_("Блок управления"),
        help_text=_("Тип блока управления")
    )
    power_supply = models.ForeignKey(
        'params.PowerSupplies',
        on_delete=models.CASCADE,
        related_name='control_unit_wirings',
        verbose_name=_("Напряжение питания"),
        help_text=_("Напряжение питания, для которого актуальна схема")
    )
    signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile',
        on_delete=models.CASCADE,
        related_name='control_unit_wirings',
        verbose_name=_("Профиль сигналов"),
        help_text=_("Профиль сигналов, отражённый на схеме")
    )
    wiring_diagram = models.ForeignKey(
        'media_library.MediaLibraryItem',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'category__code': 'SCHEMA'},
        related_name='control_unit_wirings',
        verbose_name=_("Изображение схемы"),
        help_text=_("Изображение из медиабиблиотеки (категория «Схема»)")
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название схемы, например «INT 380В станд. (обогрев отд.кабель)»")
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код схемы, например «I38-STD-SEP»")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Дополнительное описание особенностей схемы")
    )

    cached_json = models.JSONField(
        blank=True, null=True,
        verbose_name=_("Кешированные данные"),
        help_text=_("Автоматически собираемые данные для быстрого чтения фронтом")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать в списках выбора")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    class Meta:
        verbose_name = _("Схема подключения БУ")
        verbose_name_plural = _("Схемы подключения БУ")
        ordering = ['sorting_order', 'code']
        indexes = [
            models.Index(fields=['control_unit', 'power_supply']),
            models.Index(fields=['signal_profile']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}" if self.code else self.name

    def refresh_cached_json(self):
        data = {
            'control_unit': {
                'id': self.control_unit_id,
                'name': self.control_unit.name if self.control_unit_id else None,
            },
            'power_supply': {
                'id': self.power_supply_id,
                'name': str(self.power_supply) if self.power_supply_id else None,
            },
            'signal_profile': {
                'id': self.signal_profile_id,
                'name': self.signal_profile.name if self.signal_profile_id else None,
                'description': self.signal_profile.description if self.signal_profile_id else None,
            },
            'wiring_diagram': None,
        }
        if self.wiring_diagram_id:
            img = self.wiring_diagram
            data['wiring_diagram'] = {
                'id': img.id,
                'name': img.name,
                'code': img.code,
                'preview_url': getattr(img, 'preview_url', None),
                'serve_url': img.get_serve_url() if hasattr(img, 'get_serve_url') else None,
            }
        self.cached_json = data

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        fk_fields = {'control_unit_id', 'power_supply_id', 'signal_profile_id', 'wiring_diagram_id'}
        if update_fields is None or fk_fields & set(update_fields) or self.cached_json is None:
            self.refresh_cached_json()
        super().save(*args, **kwargs)

    def copy(self, suffix=' (копия)', **kwargs):
        """Копия с гарантией уникальности кода.

        Если code + suffix уже занят, перебирает (копия 2), (копия 3)...
        """
        from django.db import IntegrityError

        attempt = 0
        while True:
            try:
                s = suffix if attempt == 0 else f' (копия {attempt + 1})'
                return super().copy(suffix=s, **kwargs)
            except IntegrityError:
                attempt += 1
                if attempt > 100:
                    raise

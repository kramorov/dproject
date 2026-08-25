# pa_controls/models/positioner_item.py
"""
PosiModelLineItem — модель позиционера (собирается из опций серии).

Основа — структура БКВ (LimitSwitchBox): те же миксины, шаблоны названий,
сериализация для каталога. Опции берутся из through-моделей PosiModelLine
(разрешённые варианты серии), в item хранятся выбранные значения.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TechDocMixin, ImageGalleryMixin
from core.models.mixins import TemplateMixin, CopyMixin, CatalogDictMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from sku.models import SKUMixin

from .posi_model_line import PosiModelLine
from .posi_options import ActingType, LeverOption, SmartCapabilitySet


# Стандартный профиль сигналов позиционера: вход 4-20 мА (добавляется по умолчанию)
DEFAULT_SIGNAL_PROFILE_CODE = 'POS-STD-4-20'


class PosiModelLineItem(CatalogDictMixin,
                        ImageGalleryMixin,
                        TechDocMixin,
                        SmartCatalogMixin,
                        TemplateMixin,
                        SKUMixin, CopyMixin, models.Model):
    """Модель позиционера (артикул каталога), собранная из опций серии.

    Основа — структура БКВ (LimitSwitchBox): те же миксины, шаблоны названий
    и описаний, сериализация для каталога (to_dict/to_values_dict).

    Выбранные опции — FK-полями (варианты из through-моделей серии):
      acting_type, exd, body_connection (присоединения корпуса),
      lever (рычаг), alarm и signal_profile (профили сигналов), ip.

    Наследование из серии:
      - body_material и weight — свойства get_body_material/get_weight (по ссылке
        из серии: есть серии, отличающиеся только материалом, вес зависит от него);
      - supply_pressure_min/max — свойство get_supply_pressure_range (из серии);
      - actuator_action — свойство get_actuator_action_display_text (DA/SR/оба);
      - smart_capability_set — если у модели не задан, берётся от серии
        (get_smart_capability_set / get_smart_capabilities, сортировка по sorting_order).

    Сигналы: для всех моделей по умолчанию подставляется профиль POS-STD-4-20
    (вход 4-20 мА) — см. save() и DEFAULT_SIGNAL_PROFILE_CODE; отключить можно
    флагом skip_default_signal_profile.

    air_consumption, linearity, hysteresis — в extra_params серии, в item их нет.
    """

    name = models.TextField(verbose_name=_("Название"),
                            help_text=_('Текстовое название позиционера'))
    code = models.CharField(max_length=150, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Код позиционера"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание позиционера'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(PosiModelLine, related_name='positioner_items',
                                   blank=True, null=True, on_delete=models.SET_NULL,
                                   help_text=_('Серия позиционеров'),
                                   verbose_name=_("Серия"))

    # ── Опции, выбранные для item (из разрешённых в серии) ──
    acting_type = models.ForeignKey(ActingType, related_name='positioner_items',
                                    blank=True, null=True, on_delete=models.SET_NULL,
                                    help_text=_('Линейный или ротационный'),
                                    verbose_name=_("Тип действия"))
    exd = models.ForeignKey('params.ExdOption', related_name='positioner_items',
                            blank=True, null=True, on_delete=models.SET_NULL,
                            help_text=_('Степень взрывозащиты'),
                            verbose_name=_("Взрывозащита"))
    body_connection = models.ForeignKey(
        'pa_controls.PosiBodyConnections', related_name='positioner_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_('Присоединения корпуса: резьбы пневмовхода/выхода и отверстие КВ'),
        verbose_name=_("Присоединения корпуса"))
    lever = models.ForeignKey(LeverOption, related_name='positioner_items',
                              blank=True, null=True, on_delete=models.SET_NULL,
                              help_text=_('Длина и тип рычага'),
                              verbose_name=_("Рычаг"))
    alarm = models.ForeignKey(
        'params.ControlUnitSignalProfile', related_name='positioner_alarm_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_('Сигнал тревоги — профиль сигналов с ролью «Вых. Авария»'),
        verbose_name=_("Сигнал тревоги"))
    signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile', related_name='positioner_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_('Профиль сигналов: вход 4-20/HART + обратная связь'),
        verbose_name=_("Профиль сигналов"))

    # ── Характеристики ──
    ip = models.ForeignKey('params.IpOption', related_name='positioner_items',
                           blank=True, null=True, on_delete=models.SET_NULL,
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP"))
    work_temp_min = models.IntegerField(null=True, blank=True, default=-40,
                                        help_text=_('Минимальная рабочая температура, °С'),
                                        verbose_name=_('Т раб.мин, °С'))
    work_temp_max = models.IntegerField(null=True, blank=True, default=80,
                                        help_text=_('Максимальная рабочая температура, °С'),
                                        verbose_name=_('Т раб.макс, °С'))
    # Набор смарт-возможностей: если у модели не задан — наследуется от серии
    smart_capability_set = models.ForeignKey(
        SmartCapabilitySet,
        related_name='posi_items',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Набор смарт-возможностей")
    )
    extra_params = models.JSONField(default=dict, blank=True,
                                    verbose_name=_("Параметры"),
                                    help_text=_("Дополнительные параметры"))

    class Meta:
        verbose_name = _("Позиционер")
        verbose_name_plural = _("Позиционеры")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return f"{self.name}"

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        return self.model_line.brand if self.model_line else None

    def clean(self):
        """Валидация опций item.

        - рычаг должен соответствовать типу позиционера;
        - варианты с флагом «Только общепром» запрещены при взрывозащите.
        """
        from django.core.exceptions import ValidationError

        errors = {}
        if (self.acting_type_id and self.lever_id
                and self.lever.acting_type_id
                and self.lever.acting_type_id != self.acting_type_id):
            errors['lever'] = _('Рычаг не соответствует типу позиционера: '
                                'для линейного нужен линейный рычаг, '
                                'для ротационного — ротационный.')
        for conflict in self.get_ex_only_conflicts():
            errors.setdefault(conflict['field'], conflict['message'])
        if errors:
            raise ValidationError(errors)
        super().clean()

    def get_ex_only_conflicts(self) -> list:
        """Конфликты «Только общепром» при выбранной взрывозащите.

        Если у item выбрана взрывозащита (exd с непустым code — у строки
        «общепром» code пустой), проверяет through-опции серии с флагом
        only_non_ex: профиль обратной связи, присоединения корпуса,
        температурное исполнение.

        Возвращает список конфликтов: [{'field': ..., 'message': ...}].
        Используется clean() (админка/формы) и может вызываться
        конфигуратором/API напрямую.
        """
        if not (self.exd_id and self.exd and self.exd.code):
            return []

        conflicts = []
        if self.signal_profile_id and self.model_line_id:
            if self.model_line.signal_profile_options.filter(
                signal_profile_id=self.signal_profile_id,
                only_non_ex=True,
            ).exists():
                conflicts.append({
                    'field': 'signal_profile',
                    'message': _('Выбранный профиль обратной связи доступен '
                                 'только в общепромышленном исполнении.'),
                })

        if self.body_connection_id and self.model_line_id:
            if self.model_line.body_connection_options.filter(
                body_connection_id=self.body_connection_id,
                only_non_ex=True,
            ).exists():
                conflicts.append({
                    'field': 'body_connection',
                    'message': _('Выбранные присоединения корпуса доступны '
                                 'только в общепромышленном исполнении.'),
                })

        if (self.model_line_id
                and self.work_temp_min is not None
                and self.work_temp_max is not None):
            if self.model_line.temperature_options.filter(
                work_temp_min=self.work_temp_min,
                work_temp_max=self.work_temp_max,
                only_non_ex=True,
            ).exists():
                conflicts.append({
                    'field': 'work_temp_min',
                    'message': _('Выбранное температурное исполнение доступно '
                                 'только в общепромышленном варианте.'),
                })

        return conflicts

    def save(self, *args, **kwargs):
        # Для всех моделей по умолчанию — входной 4-20 мА (стандартный профиль)
        if not self.signal_profile_id and not kwargs.get('skip_default_signal_profile'):
            from params.models import ControlUnitSignalProfile
            default_profile = ControlUnitSignalProfile.objects.filter(
                code=DEFAULT_SIGNAL_PROFILE_CODE
            ).first()
            if default_profile:
                self.signal_profile = default_profile
        super().save(*args, **kwargs)
        self.sync_sku()

    # ── Шаблоны (TemplateMixin) ──

    def _get_name_template_source(self):
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        return ("{model_code} Позиционер {brand}, {acting_type}; {exd}; "
                "Т.окр. {work_temp_min}..{work_temp_max} °С; Присоединения: {body_connection}; "
                "Рычаг: {lever}; "
                "Материал корпуса: {body_material}")

    def _get_default_description_template(self) -> str:
        return ("{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}; "
                "Т.окр. {work_temp_min}..{work_temp_max} °С; "
                "Присоединения корпуса: {body_connection}; "
                "Рычаг: {lever}; Материал корпуса: {body_material}, вес {weight} кг; "
                "Питание: {supply_pressure_range} бар; "
                "Пневмопривод: {actuator_action}; "
                "Сигнал тревоги: {alarm}. Сигналы: {signal_profile_summary}")

    def _get_title_template_source(self):
        return "{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}"

    def _get_data_dict(self) -> dict:
        """Словарь соответствий плейсхолдеров и атрибутов."""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand__name',
            '{acting_type}': 'acting_type',
            '{exd}': 'exd',
            '{ip}': 'ip',
            '{body_connection}': 'body_connection',
            '{lever}': 'lever',
            '{alarm}': 'alarm',
            '{body_material}': 'get_body_material',
            '{weight}': 'get_weight',
            '{actuator_action}': 'get_actuator_action_display_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{supply_pressure_range}': 'get_supply_pressure_range',
            '{signal_profile_summary}': 'get_signal_profile_summary',
        }

    # ── Свойства, читающие характеристики из серии ──

    @property
    def get_body_material(self):
        """Материал корпуса — по ссылке из серии."""
        return self.model_line.body_material if self.model_line_id else None

    @property
    def get_weight(self):
        """Вес — из серии (зависит от материала корпуса)."""
        return self.model_line.weight if self.model_line_id else None

    @property
    def get_actuator_action_display_text(self) -> str:
        """Тип пневмопривода (DA/SR/оба) — из серии, в виде текста."""
        if not self.model_line_id:
            return ''
        return {
            'da': 'DA',
            'sr': 'SR',
            'both': 'DA/SR',
        }.get(self.model_line.actuator_action, '')

    @property
    def get_supply_pressure_range(self) -> str:
        """Диапазон давления питания — из серии."""
        ml = self.model_line
        if not ml or (ml.supply_pressure_min is None and ml.supply_pressure_max is None):
            return ''
        parts = [str(ml.supply_pressure_min) if ml.supply_pressure_min is not None else '—',
                 str(ml.supply_pressure_max) if ml.supply_pressure_max is not None else '—']
        return f"{parts[0]}..{parts[1]}"

    def get_smart_capability_set(self):
        """Набор смарт-возможностей: свой у модели, иначе — от серии."""
        if self.smart_capability_set_id:
            return self.smart_capability_set
        if self.model_line_id:
            return self.model_line.smart_capability_set
        return None

    def get_smart_capabilities(self):
        """Возможности эффективного набора, отсортированные по sorting_order, code."""
        capability_set = self.get_smart_capability_set()
        if not capability_set:
            return []
        return list(capability_set.get_capabilities())

    @property
    def get_signal_profile_summary(self) -> str:
        """Текстовая сводка сигналов по профилю (как в БКВ)."""
        if self.signal_profile_id:
            entries = self.signal_profile.entries.select_related(
                'signal_role', 'sensor__signal_type', 'sensor__contact_form',
                'input_signal',
            ).all()
            parts = []
            for e in entries:
                if e.sensor_id:
                    if e.sensor.contact_form_id and e.sensor.contact_form.code != 'NONE':
                        marker = e.sensor.contact_form.code
                    elif e.sensor.signal_type_id:
                        marker = e.sensor.signal_type.name
                    else:
                        marker = None
                    parts.append(f"{e.signal_role.name} — {marker}" if (marker and e.signal_role_id) else (str(e.signal_role) if e.signal_role_id else '—'))
                elif e.input_signal_id:
                    parts.append(f"{e.signal_role.name} — {e.input_signal.name}" if e.signal_role_id else e.input_signal.name)
            return "; ".join(parts) if parts else "—"
        return "—"

    # ── Сериализация каталога ──

    def to_dict(self) -> dict:
        tv = {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': self.model_line.name if self.model_line else '',
            'brand_name': self.model_line.brand.name if self.model_line and self.model_line.brand else '',
            'acting_type': self.acting_type.name if self.acting_type else '',
            'exd': self.exd.name if self.exd else '',
            'ip': self.ip.name if self.ip else '',
            'body_connection': self.body_connection.name if self.body_connection_id else '',
            'lever': self.lever.name if self.lever else '',
            'alarm': self.alarm.name if self.alarm else '',
            'work_temp': f'{self.work_temp_min}...+{self.work_temp_max} °С' if self.work_temp_min is not None else '',
            'body_material': self.get_body_material.name if self.get_body_material else '',
            'weight': str(self.get_weight) if self.get_weight is not None else '',
            'actuator_action': self.get_actuator_action_display_text,
            'smart_capabilities': "; ".join(c.name for c in self.get_smart_capabilities()),
            'supply_pressure': self.get_supply_pressure_range,
            'signal_profile': self.signal_profile.name if self.signal_profile_id else '',
            'signal_profile_summary': self.get_signal_profile_summary,
        }
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'description': self.description or '',
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': {'id': self.model_line.id, 'name': self.model_line.name} if self.model_line else None,
            'sku': {'id': self.sku.id, 'code': self.sku.code, 'name': self.sku.name}
                   if hasattr(self, 'sku') and self.sku else None,
            'template_vars': tv,
            'sections': [
                {
                    'key': 'specs', 'title': 'Характеристики', 'type': 'specs',
                    'order': 1, 'groups': [
                        {
                            'key': 'general', 'title': 'Основные', 'order': 1,
                            'fields': [
                                {'key': 'model_line_name', 'label': 'Серия', 'value': tv['model_line_name'],
                                 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'brand_name', 'label': 'Бренд', 'value': tv['brand_name'],
                                 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'acting_type', 'label': 'Тип действия', 'value': tv['acting_type'],
                                 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'exd', 'label': 'Взрывозащита', 'value': tv['exd'],
                                 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'ip', 'label': 'IP', 'value': tv['ip'],
                                 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'work_temp', 'label': 'Рабочая температура', 'value': tv['work_temp'],
                                 'unit': '', 'type': 'text', 'order': 6},
                                {'key': 'body_material', 'label': 'Материал корпуса', 'value': tv['body_material'],
                                 'unit': '', 'type': 'text', 'order': 7},
                                {'key': 'weight', 'label': 'Вес', 'value': tv['weight'],
                                 'unit': 'кг', 'type': 'number', 'order': 8},
                                {'key': 'actuator_action', 'label': 'Пневмопривод', 'value': tv['actuator_action'],
                                 'unit': '', 'type': 'text', 'order': 9},
                                {'key': 'smart_capabilities', 'label': 'Возможности',
                                 'value': tv['smart_capabilities'], 'unit': '', 'type': 'text', 'order': 10},
                            ]
                        },
                        {
                            'key': 'connections', 'title': 'Присоединения', 'order': 2,
                            'fields': [
                                {'key': 'body_connection', 'label': 'Присоединения корпуса', 'value': tv['body_connection'],
                                 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'lever', 'label': 'Рычаг', 'value': tv['lever'],
                                 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'supply_pressure', 'label': 'Давление питания', 'value': tv['supply_pressure'],
                                 'unit': 'бар', 'type': 'text', 'order': 3},
                            ]
                        },
                        {
                            'key': 'signals', 'title': 'Сигналы', 'order': 3,
                            'fields': [
                                {'key': 'signal_profile', 'label': 'Профиль сигналов', 'value': tv['signal_profile'],
                                 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'signal_profile_summary', 'label': 'Сигналы (по ролям)',
                                 'value': tv['signal_profile_summary'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'alarm', 'label': 'Сигнал тревоги', 'value': tv['alarm'],
                                 'unit': '', 'type': 'text', 'order': 3},
                            ]
                        },
                    ]
                },
                {
                    'key': 'docs', 'title': 'Документация', 'type': 'files',
                    'order': 2, 'data': []
                },
                {
                    'key': 'description', 'title': 'Описание', 'type': 'text',
                    'order': 3, 'data': self.description or '',
                },
            ],
        }

    def to_values_dict(self) -> dict:
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'model_line': {'id': self.model_line.id, 'name': self.model_line.name} if self.model_line else None,
            'sku': {'id': self.sku.id, 'code': self.sku.code, 'name': self.sku.name}
                   if hasattr(self, 'sku') and self.sku else None,
        }

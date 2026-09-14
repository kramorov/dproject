# pa_controls/models/positioner_item.py
"""
PosiModelLineItem — модель позиционера (собирается из опций серии).

Основа — структура БКВ (LimitSwitchBox): те же миксины, шаблоны названий,
сериализация для каталога. Опции берутся из through-моделей PosiModelLine
(разрешённые варианты серии), в item хранятся выбранные значения.
"""
import re

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TechDocMixin, ImageGalleryMixin
from core.models.mixins import TemplateMixin, CopyMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from sku.models import SKUMixin

from options.models import ExdOptionsConsumerMixin

from .posi_model_line import PosiModelLine
from .posi_options import ActingType, LeverOption, SmartCapabilitySet
from .posi_item_fields import POSI_ITEM_TEMPLATE_FIELDS


# Стандартный профиль сигналов позиционера: вход 4-20 мА (добавляется по умолчанию)
DEFAULT_SIGNAL_PROFILE_CODE = 'POS-STD-4-20'


class PosiModelLineItem(CatalogSerializerMixin,
                        ImageGalleryMixin,
                        TechDocMixin,
                        SmartCatalogMixin,
                        TemplateMixin,
                        SKUMixin, CopyMixin, ExdOptionsConsumerMixin, models.Model):
    """Модель позиционера (артикул каталога), собранная из опций серии.

    Основа — структура БКВ (LimitSwitchBox): те же миксины, шаблоны названий
    и описаний, сериализация для каталога (to_dict/to_values_dict).

    Выбранные опции — FK-полями (варианты из through-моделей серии):
      acting_type, body_connection (присоединения корпуса),
      lever (рычаг), alarm и signal_profile (профили сигналов);
      exd_options — M2M видов взрывозащиты (копируется из PosiExdOption серии).

    Наследование из серии:
      - body_material и weight — свойства get_body_material/get_weight (по ссылке
        из серии: есть серии, отличающиеся только материалом, вес зависит от него);
      - supply_pressure_min/max — свойство get_supply_pressure_range (из серии);
      - actuator_action — свойство get_actuator_action_display_text (DA/SR/оба);
      - ip — степень защиты IP (из серии PosiModelLine.ip);
      - smart_capability_set — если у модели не задан, берётся от опции
        «Профиль сигналов» (PosiSignalProfileOption.smart_capability_set;
        get_smart_capability_set / get_smart_capabilities, сортировка по sorting_order).

    Сигналы: для всех моделей по умолчанию подставляется профиль POS-STD-4-20
    (вход 4-20 мА) — см. save() и DEFAULT_SIGNAL_PROFILE_CODE; отключить можно
    флагом skip_default_signal_profile.

    air_consumption, linearity, hysteresis — в extra_params серии, в item их нет.
    """

    required_model_line_fields = (
        'name_template', 'description_template', 'model_item_code_template',
    )

    # Реестр полей вынесен в posi_item_fields.py.
    TEMPLATE_FIELDS = POSI_ITEM_TEMPLATE_FIELDS

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'acting_type', 'exd', 'exd_short', 'ip',
        'body_connection', 'pneumatic_connection', 'cable_gland_hole',
        'lever', 'alarm', 'body_material', 'weight', 'actuator_action',
        'work_temp_min', 'work_temp_max', 'supply_pressure',
        'signal_profile_summary', 'alarm_signal_profile_summary',
        'smart_capabilities',
    )

    CODE_FIELD_KEYS = (
        'code', 'acting_type', 'body_connection', 'lever', 'temperature',
        'signal_profile', 'alarm', 'exd', 'ip', 'smart',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'acting_type',
        'exd', 'ip', 'body_connection', 'pneumatic_connection',
        'cable_gland_hole', 'lever', 'alarm', 'work_temp', 'body_material',
        'weight', 'actuator_action', 'smart_capabilities', 'supply_pressure',
        'signal_profile', 'signal_profile_summary',
        'alarm_signal_profile_summary',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'acting_type', 'exd', 'ip',
    #     'work_temp', 'body_material', 'weight', 'actuator_action',
    #     'smart_capabilities', 'pneumatic_connection', 'cable_gland_hole',
    #     'lever', 'supply_pressure', 'signal_profile',
    #     'signal_profile_summary', 'alarm', 'alarm_signal_profile_summary',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'connections': 'Присоединения',
    #     'signals': 'Сигналы',
    # }

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
    exd_options = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='positioner_items',
        help_text=_('Виды взрывозащиты (копируется из PosiExdOption серии)'),
        verbose_name=_("Виды взрывозащиты")
    )
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
        """Конфликты опций по доступности взрывозащиты.

        При выбранной взрывозащите (Ex) недоступны опции с
        exd_availability='non_ex'; в общепромышленном исполнении недоступны
        опции с exd_availability='ex'. Проверяет through-опции серии:
        профиль обратной связи, присоединения корпуса, температурное исполнение.

        Возвращает список конфликтов: [{'field': ..., 'message': ...}].
        Используется clean() (админка/формы) и может вызываться
        конфигуратором/API напрямую.
        """
        conflicts = []
        if not self.model_line_id:
            return conflicts

        is_ex = self.has_exd()
        availability = 'non_ex' if is_ex else 'ex'
        if is_ex:
            signal_msg = _('Выбранный профиль обратной связи доступен только в общепромышленном исполнении.')
            body_msg = _('Выбранные присоединения корпуса доступны только в общепромышленном исполнении.')
            temp_msg = _('Выбранное температурное исполнение доступно только в общепромышленном варианте.')
        else:
            signal_msg = _('Выбранный профиль обратной связи доступен только во взрывозащищённом исполнении (Ex).')
            body_msg = _('Выбранные присоединения корпуса доступны только во взрывозащищённом исполнении (Ex).')
            temp_msg = _('Выбранное температурное исполнение доступно только во взрывозащищённом варианте (Ex).')

        if self.signal_profile_id:
            if self.model_line.signal_profile_options.filter(
                signal_profile_id=self.signal_profile_id,
                exd_availability=availability,
            ).exists():
                conflicts.append({'field': 'signal_profile', 'message': signal_msg})

        if self.body_connection_id:
            if self.model_line.body_connection_options.filter(
                body_connection_id=self.body_connection_id,
                exd_availability=availability,
            ).exists():
                conflicts.append({'field': 'body_connection', 'message': body_msg})

        if self.work_temp_min is not None and self.work_temp_max is not None:
            if self.model_line.temperature_options.filter(
                work_temp_min=self.work_temp_min,
                work_temp_max=self.work_temp_max,
                exd_availability=availability,
            ).exists():
                conflicts.append({'field': 'work_temp_min', 'message': temp_msg})

        return conflicts

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Для всех моделей по умолчанию — входной 4-20 мА (стандартный профиль)
        if not self.signal_profile_id and not kwargs.get('skip_default_signal_profile'):
            from params.models import ControlUnitSignalProfile
            default_profile = ControlUnitSignalProfile.objects.filter(
                code=DEFAULT_SIGNAL_PROFILE_CODE
            ).first()
            if default_profile:
                self.signal_profile = default_profile
        # Артикул генерируется из model_line.model_item_code_template, если не задан
        if not self.code:
            self.code = self.generated_model_item_code or None
        super().save(*args, **kwargs)
        if is_new and self.model_line_id:
            self._sync_exd_options_from_model_line()
        self.sync_sku()

    def copy(self, suffix=' Копия', **kwargs):
        """Копия item-а с уникальным кодом и SKU.

        Имя и описание не трогаем: TemplateMixin.save() перегенерирует их
        из шаблона серии при сохранении (skip_auto_generate не передаём),
        и код с суффиксом попадает в имя через плейсхолдер {model_code}.

        SKU привязывается по коду (sync_sku), поэтому повторные копии
        должны получать уникальный код: перебираем «Копия», «Копия 2»…
        Проверка занятости SKU выполняется до сохранения, а каждая попытка
        — в отдельном atomic-блоке, чтобы IntegrityError не ломала внешнюю
        транзакцию (например, при массовом импорте).
        """
        from django.db import IntegrityError, transaction

        from sku.models import SKU

        base_code = self.code or self.name or ''

        attempt = 0
        while True:
            s = suffix if attempt == 0 else f'{suffix} {attempt + 1}'

            # Код занят (SKU уже существует) — пробуем следующий суффикс
            if SKU.objects.filter(code=f'{base_code}{s}').exists():
                attempt += 1
                if attempt > 100:
                    raise RuntimeError('Не удалось подобрать уникальный код копии')
                continue

            try:
                with transaction.atomic():
                    new_obj = super().copy(suffix=s, **kwargs)
                return new_obj
            except IntegrityError:
                # Страховка от гонок: суффикс успел занять другой процесс
                attempt += 1
                if attempt > 100:
                    raise
                with transaction.atomic():
                    PosiModelLineItem.objects.filter(
                        code=f'{base_code}{s}', sku__isnull=True
                    ).delete()

    # ── Артикул (паттерн электроприводов/пневмоприводов: шаблон на серии +
    #    encodings through-опций) ──

    @property
    def generated_model_item_code(self) -> str:
        """Артикул по шаблону model_line.model_item_code_template."""
        template = getattr(self.model_line, 'model_item_code_template', None) if self.model_line else None
        if not template:
            return self._generate_fallback_code()
        result = self._fill_template(template, self._get_code_data_dict())
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        return result.strip('. ')

    def _generate_fallback_code(self) -> str:
        parts = [
            self.model_line.code if self.model_line else '',
            self.acting_type_encoding, self.body_connection_encoding, self.lever_encoding,
            self.temperature_encoding, self.signal_profile_encoding, self.alarm_encoding,
            self.exd_encoding, self.ip_code, self.smart_code,
        ]
        return '.'.join(filter(None, parts))

    def _get_option_encoding(self, through_model_name: str, through_attr: str, value) -> str:
        """Encoding through-опции серии для выбранного значения item'а."""
        if not (self.model_line_id and value):
            return ''
        from . import posi_model_line as pml
        model = getattr(pml, through_model_name)
        row = model.objects.filter(
            model_line_id=self.model_line_id, **{through_attr: value}
        ).first()
        return row.encoding if row and row.encoding else ''

    @property
    def acting_type_encoding(self) -> str:
        """Тип действия — прямой FK: code справочника (свой у модели или от серии)."""
        at = self.acting_type or (self.model_line.acting_type if self.model_line else None)
        return at.code if at else ''

    @property
    def body_connection_encoding(self) -> str:
        return self._get_option_encoding('PosiBodyConnectionOption', 'body_connection', self.body_connection)

    @property
    def lever_encoding(self) -> str:
        return self._get_option_encoding('PosiLeverOption', 'lever', self.lever)

    @property
    def temperature_encoding(self) -> str:
        """Температурная опция, выбранная для item.

        Опция ищется по work_temp_min/max item'а (конструктор сохраняет
        выбранный диапазон); если диапазон не задан или не найден —
        дефолтная опция серии (is_default, фолбэк — первая активная).
        """
        from .posi_model_line import PosiTemperatureOption
        if not self.model_line_id:
            return ''
        qs = PosiTemperatureOption.objects.filter(
            model_line_id=self.model_line_id, is_active=True
        )
        opt = None
        if self.work_temp_min is not None and self.work_temp_max is not None:
            opt = (qs.filter(work_temp_min=self.work_temp_min,
                             work_temp_max=self.work_temp_max)
                   .order_by('-is_default', 'sorting_order').first())
        if not opt:
            opt = qs.order_by('-is_default', 'sorting_order').first()
        return opt.encoding if opt and opt.encoding else ''

    @property
    def signal_profile_encoding(self) -> str:
        """Encoding профиля сигналов.

        Один профиль может повторяться в серии с разными наборами
        смарт-возможностей (и encodings) — предпочитаем through-строку,
        чей smart_capability_set совпадает с item'ом; иначе первая строка.
        """
        if not (self.model_line_id and self.signal_profile_id):
            return ''
        from .posi_model_line import PosiSignalProfileOption
        qs = PosiSignalProfileOption.objects.filter(
            model_line_id=self.model_line_id,
            signal_profile_id=self.signal_profile_id,
        )
        row = None
        if self.smart_capability_set_id:
            row = qs.filter(
                smart_capability_set_id=self.smart_capability_set_id
            ).first()
        if not row:
            row = qs.first()
        return row.encoding if row and row.encoding else ''

    @property
    def alarm_encoding(self) -> str:
        return self._get_option_encoding('PosiAlarmOption', 'alarm', self.alarm)

    @property
    def ip_code(self) -> str:
        return self.model_line.ip.code if self.model_line and self.model_line.ip else ''

    @property
    def smart_code(self) -> str:
        s = self.get_smart_capability_set()
        return (s.code or '') if s else ''

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
                "Сигнал тревоги: {alarm}. Сигналы: {signal_profile_summary}; "
                "Смарт-возможности: {smart_capabilities}")

    def _get_title_template_source(self):
        return "{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}"

    # ── Резьбы присоединений корпуса (для шаблонов и каталога) ──

    @property
    def get_pneumatic_connection(self) -> str:
        """Резьба пневмоподключения (единая для входа/выхода)."""
        bc = self.body_connection
        return str(bc.pneumatic_thread) if bc and bc.pneumatic_thread else ''

    @property
    def get_cable_gland_hole(self) -> str:
        """Резьба отверстия под кабельный ввод."""
        bc = self.body_connection
        return str(bc.cable_gland_hole) if bc and bc.cable_gland_hole else ''

    @property
    def get_acting_type(self):
        """Тип действия: свой у модели, иначе — от серии (FK)."""
        return self.acting_type or (self.model_line.acting_type if self.model_line else None)

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

    @property
    def get_work_temp_display(self) -> str:
        """Диапазон рабочей температуры для отображения."""
        if self.work_temp_min is None:
            return ''
        return f'{self.work_temp_min}...+{self.work_temp_max} °С'

    def get_smart_capability_set(self):
        """Набор смарт-возможностей: свой у модели, иначе — от опции «Профиль сигналов»."""
        if self.smart_capability_set_id:
            return self.smart_capability_set
        if self.model_line_id and self.signal_profile_id:
            from .posi_model_line import PosiSignalProfileOption
            option = PosiSignalProfileOption.objects.filter(
                model_line_id=self.model_line_id,
                signal_profile_id=self.signal_profile_id,
            ).select_related('smart_capability_set').first()
            if option:
                return option.smart_capability_set
        return None

    def get_smart_capabilities(self):
        """Возможности эффективного набора, отсортированные по sorting_order, code."""
        capability_set = self.get_smart_capability_set()
        if not capability_set:
            return []
        return list(capability_set.get_capabilities())

    @property
    def get_smart_capabilities_display(self) -> str:
        """Текстовая сводка смарт-возможностей для шаблонов ({smart_capabilities})."""
        return "; ".join(c.name for c in self.get_smart_capabilities())

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

    @property
    def get_alarm_signal_profile_summary(self) -> str:
        """Текстовая сводка сигналов по профилю тревоги (аналог get_signal_profile_summary)."""
        if self.alarm_id:
            entries = self.alarm.entries.select_related(
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



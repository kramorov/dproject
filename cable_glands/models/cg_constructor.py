# cable_glands/models/cg_constructor.py
"""Конструктор кабельных вводов (CableGlandConstructor).

Паттерн — как у позиционеров (PositionerConstructor) и электроприводов
(ElectricActuatorConstructor):

    * Форма конструктора хранит ВЫБРАННЫЕ опции прямыми FK на through-строки:
      - selected_thread_option        → CableGlandThreadOption (родитель — корпус),
      - selected_body_material_option → CableGlandBodyMaterialOption (родитель — серия),
      - selected_exd_option           → CableGlandExdOption (родитель — серия).
      Через-строка = одна кодировка, поэтому артикул берёт encoding напрямую,
      без обратного поиска.
    * build_preview_item() собирает ВРЕМЕННЫЙ CableGland и делегирует ему
      генерацию code/name/description (единый источник истины).
    * materialize() создаёт/возвращает эталонный CableGland (+SKU через
      CableGland.save() → sync_sku()).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .cg_actual import CableGland
from .cg_thread_option import CableGlandThreadOption
from .cg_body_material_option import CableGlandBodyMaterialOption
from .cg_exd_option import CableGlandExdOption


class CableGlandConstructor(models.Model):
    """Сохранённая конфигурация конструктора кабельного ввода (форма)."""

    name = models.CharField(max_length=200, blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Название кабельного ввода — формируется автоматически'))
    code = models.CharField(max_length=150, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_('Код кабельного ввода — формируется автоматически'))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Описание кабельного ввода — формируется автоматически'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Сортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    is_unique = models.BooleanField(default=True, verbose_name=_("Уникальная конфигурация"),
                                    help_text=_('Есть ли уже такая же конфигурация'))

    # Шаг 1: серия (фильтрует модели и опции материала/взрывозащиты)
    selected_model_line = models.ForeignKey(
        'CableGlandModelLine',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_configs',
        verbose_name=_("Серия"),
        help_text=_('Серия кабельных вводов'))

    # Шаг 2: модель в серии (корпус + крепление МР + вес)
    selected_model_line_item = models.ForeignKey(
        'CableGlandModelLineItem',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_configs',
        verbose_name=_("Модель"),
        help_text=_('Модель кабельного ввода (корпус/металлорукав/вес)'))

    # Шаг 3: опции — прямые FK на through-строки (источник encoding)
    selected_thread_option = models.ForeignKey(
        'CableGlandThreadOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_configs',
        verbose_name=_("Опция резьбы"),
        help_text=_('Выбранная опция резьбы корпуса'))
    selected_body_material_option = models.ForeignKey(
        'CableGlandBodyMaterialOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_configs',
        verbose_name=_("Опция материала корпуса"),
        help_text=_('Выбранная опция материала корпуса'))
    selected_exd_option = models.ForeignKey(
        'CableGlandExdOption',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constructor_configs',
        verbose_name=_("Опция взрывозащиты"),
        help_text=_('Выбранная опция взрывозащиты серии'))

    class Meta:
        verbose_name = _("Конструктор кабельного ввода")
        verbose_name_plural = _("Конструктор кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name or self.code or '—'

    # ──────────────────────────────────────────────────────────────────
    # ДОСТУПНЫЕ ОПЦИИ (для эндпоинта /options/)
    # ──────────────────────────────────────────────────────────────────

    def get_available_options(self) -> dict:
        """Доступные опции для выбранной серии/модели.

        Ключи: thread_options, body_material_options, exd_options.
        Каждая запись: id (through-строка), encoding, name, is_default.
        """
        result = {
            'thread_options': [],
            'body_material_options': [],
            'exd_options': [],
        }
        mli = self.selected_model_line_item
        ml = self.selected_model_line or (mli.model_line if mli else None)

        if mli and mli.body_id:
            qs = CableGlandThreadOption.objects.filter(
                cable_gland_body_id=mli.body_id, is_active=True
            ).select_related('thread_size').order_by('sorting_order')
            result['thread_options'] = [
                {
                    'id': row.id,
                    'option_id': row.thread_size_id,
                    'encoding': row.encoding or '',
                    'name': str(row.thread_size),
                    'thread_size_id': row.thread_size_id,
                    'is_default': row.is_default,
                }
                for row in qs
            ]

        if ml:
            bm_qs = CableGlandBodyMaterialOption.objects.filter(
                model_line=ml, is_active=True
            ).select_related('body_material').order_by('sorting_order')
            result['body_material_options'] = [
                {
                    'id': row.id,
                    'option_id': row.body_material_id,
                    'encoding': row.encoding or '',
                    'name': str(row.body_material),
                    'body_material_id': row.body_material_id,
                    'is_default': row.is_default,
                }
                for row in bm_qs
            ]

            exd_qs = CableGlandExdOption.objects.filter(
                model_line=ml, is_active=True
            ).order_by('sorting_order')
            result['exd_options'] = [
                {
                    'id': row.id,
                    'encoding': row.encoding or '',
                    'is_default': row.is_default,
                    'variants': [
                        {'id': v.id, 'name': v.name, 'code': v.code}
                        for v in row.exd_options.all()
                    ],
                }
                for row in exd_qs
            ]

        return result

    # ──────────────────────────────────────────────────────────────────
    # ВАЛИДАЦИЯ / ПРЕВЬЮ
    # ──────────────────────────────────────────────────────────────────

    def _ensure_valid_options(self):
        """Консистентность выбранных through-строк с корпусом/серией."""
        mli = self.selected_model_line_item
        ml = self.selected_model_line or (mli.model_line if mli else None)
        if mli and not ml:
            self.selected_model_line = mli.model_line

        errors = {}
        if self.selected_thread_option_id and mli and mli.body_id:
            if self.selected_thread_option.cable_gland_body_id != mli.body_id:
                errors['selected_thread_option'] = _('Резьба не относится к корпусу выбранной модели.')
        if self.selected_body_material_option_id and ml:
            if self.selected_body_material_option.model_line_id != ml.id:
                errors['selected_body_material_option'] = _('Материал не относится к выбранной серии.')
        if self.selected_exd_option_id and ml:
            if self.selected_exd_option.model_line_id != ml.id:
                errors['selected_exd_option'] = _('Взрывозащита не относится к выбранной серии.')
        if errors:
            raise ValidationError(errors)

    def build_preview_item(self):
        """Временный CableGland из выбранных опций (без сохранения).

        Код/имя/описание генерирует именно артикул — так превью и сохранённый
        артикул гарантированно совпадают.
        """
        mli = self.selected_model_line_item
        if not self.selected_model_line_id and mli and mli.model_line_id:
            self.selected_model_line = mli.model_line
        if not self.selected_model_line_id:
            return None

        item = CableGland(
            model_line=self.selected_model_line,
            model_line_item=self.selected_model_line_item,
            thread_option=self.selected_thread_option,
            body_material_option=self.selected_body_material_option,
            exd_option=self.selected_exd_option,
        )
        item.code = item.generated_model_item_code
        item.name = item.generated_model_name_description('name') or ''
        item.description = item.generated_model_name_description('description') or ''
        return item

    @property
    def generated_model_item_code(self) -> str:
        item = self.build_preview_item()
        return item.code if item else ''

    # ──────────────────────────────────────────────────────────────────
    # МАТЕРИАЛИЗАЦИЯ В АРТИКУЛ
    # ──────────────────────────────────────────────────────────────────

    def materialize(self):
        """Создать/вернуть эталонный CableGland (+SKU) из конфигурации.

        Дедупликация по коду артикула; повторный вызов с тем же набором опций
        возвращает тот же CableGland.
        """
        preview = self.build_preview_item()
        if preview is None:
            raise ValidationError({'selected_model_line': _('Серия кабельных вводов не выбрана.')})

        defaults = {
            'model_line': self.selected_model_line,
            'model_line_item': self.selected_model_line_item,
            'thread_option': self.selected_thread_option,
            'body_material_option': self.selected_body_material_option,
            'exd_option': self.selected_exd_option,
        }
        code = preview.code or None
        if not code:
            raise ValidationError({'code': _('Не удалось сформировать артикул.')})
        item = None
        if code:
            item = CableGland.objects.filter(code=code).first()
        if item is None:
            item, _created = CableGland.objects.get_or_create(
                defaults=defaults, code=code,
            )
        else:
            needs_save = False
            if not item.is_active:
                item.is_active = True
                needs_save = True
            for field, value in defaults.items():
                if getattr(item, f'{field}_id') != (value.id if value else None):
                    setattr(item, field, value)
                    needs_save = True
            if needs_save:
                item.save()
        item.refresh_from_db()
        return item, getattr(item, 'sku', None)

    # ──────────────────────────────────────────────────────────────────
    # SAVE
    # ──────────────────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        self._ensure_valid_options()
        preview = self.build_preview_item()
        if preview:
            self.name = preview.name or ''
            self.code = preview.code or None
            self.description = preview.description or ''
        super().save(*args, **kwargs)

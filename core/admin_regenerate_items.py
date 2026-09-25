# core/admin_regenerate_items.py
"""Mixin для админок серий (model_line): кнопка перегенерации name/description.

Добавляет в карточку просмотра серии кнопку, которая проходит по всем
элементам серии (model_line_item) и вызывает ``update_from_templates(save=True)``,
перезаписывая name/description из шаблонов серии.

Использование:

    from core.admin_regenerate_items import RegenerateSeriesItemsAdminMixin

    @admin.register(MyModelLine)
    class MyModelLineAdmin(RegenerateSeriesItemsAdminMixin, admin.ModelAdmin):
        regenerate_items_related_name = 'my_model_line_items'  # обратная связь к items
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _


class RegenerateSeriesItemsAdminMixin:
    """Кнопка «Перегенерировать name/description» в change-form серии."""

    # Имя обратной связи от model_line к его элементам (например 'filter_model_line').
    regenerate_items_related_name = None
    change_form_template = 'admin/regenerate_items_change_form.html'

    def _get_regenerate_items(self, obj):
        rel = self.regenerate_items_related_name
        if not rel or not hasattr(obj, rel):
            return None
        return getattr(obj, rel).all()

    def get_urls(self):
        urls = super().get_urls()
        info = self.opts.app_label, self.opts.model_name
        custom_urls = [
            path(
                '<path:object_id>/regenerate-items/',
                self.admin_site.admin_view(self.regenerate_items_view),
                name='%s_%s_regenerate_items' % info,
            ),
        ]
        return custom_urls + urls

    def regenerate_items_view(self, request, object_id):
        opts = self.opts
        obj = self.get_object(request, object_id)
        if obj is None:
            self.message_user(request, _('Объект не найден'), level=messages.ERROR)
            return redirect('admin:%s_%s_changelist' % (opts.app_label, opts.model_name))

        qs = self._get_regenerate_items(obj)
        if qs is None:
            self.message_user(
                request,
                _('Не задан regenerate_items_related_name или связь с элементами не найдена'),
                level=messages.ERROR,
            )
        else:
            total = qs.count()
            updated = 0
            errors = 0
            for item in qs:
                try:
                    if item.update_from_templates(save=True):
                        updated += 1
                except Exception as exc:
                    errors += 1
                    self.message_user(
                        request,
                        _('Ошибка на элементе id=%s: %s') % (item.pk, exc),
                        level=messages.ERROR,
                    )
            self.message_user(
                request,
                _('♻️ Перегенерировано name/description: обновлено %(updated)d из %(total)d, ошибок %(errors)d')
                % {'updated': updated, 'total': total, 'errors': errors},
                level=messages.SUCCESS,
            )

        return redirect('admin:%s_%s_change' % (opts.app_label, opts.model_name), object_id)

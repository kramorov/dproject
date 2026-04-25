#client_requests/admin/snapshot_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from ..models import RequestSnapshot

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from ..models import RequestSnapshot


@admin.register(RequestSnapshot)
class RequestSnapshotAdmin(admin.ModelAdmin) :
    list_display = [
        'request' ,
        'snapshot_number' ,
        'is_approved' ,
        'snapshot_comment_preview' ,
        'total_items' ,
        'approved_at'
    ]

    list_filter = [
        'is_approved' ,
        'approved_at'
    ]

    search_fields = [
        'request__request_number' ,
        'snapshot_comment'
    ]

    readonly_fields = [
        'snapshot_number' ,
        'snapshot_data_preview'
    ]

    fieldsets = (
        (_('Заявка') , {
            'fields' : ('request' ,)
        }) ,
        (_('Снимок') , {
            'fields' : ('snapshot_number' , 'snapshot_comment' , 'snapshot_data_preview')
        }) ,
        (_('Согласование') , {
            'fields' : ('is_approved' , 'approved_at')
        }) ,
    )

    def snapshot_comment_preview(self , obj) :
        """Предпросмотр комментария"""
        if len(obj.snapshot_comment) > 50 :
            return obj.snapshot_comment[:50] + '...'
        return obj.snapshot_comment or '-'

    snapshot_comment_preview.short_description = _("Комментарий")

    def total_items(self , obj) :
        """Количество позиций в снапшоте"""
        if obj.snapshot_data :
            return obj.snapshot_data.get('total_items' , 0)
        return 0

    total_items.short_description = _("Позиций")

    def snapshot_data_preview(self , obj) :
        """Предпросмотр данных снапшота"""
        if obj.snapshot_data :
            items = obj.snapshot_data.get('items' , [])
            return format_html(
                '<details><summary>{} позиций</summary><pre style="max-height:300px; overflow:auto;">{}</pre></details>' ,
                len(items) ,
                obj.snapshot_data
            )
        return "-"

    snapshot_data_preview.short_description = _("Данные снапшота")

    actions = ['approve_snapshots']

    @admin.action(description=_("Утвердить выбранные снимки"))
    def approve_snapshots(self , request , queryset) :
        from django.utils import timezone
        count = queryset.update(is_approved=True , approved_at=timezone.now())
        self.message_user(request , f"Утверждено {count} снимков")
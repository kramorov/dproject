#client_requests/admin/comment_admin.pychange_log_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import RequestChangeLog


@admin.register(RequestChangeLog)
class RequestChangeLogAdmin(admin.ModelAdmin) :
    list_display = [
        'request' ,
        'change_type' ,
        'change_comment_preview' ,
        'changed_at' ,
        'affected_items_count'
    ]

    list_filter = [
        'change_type' ,
        'changed_at'
    ]

    search_fields = [
        'request__request_number' ,
        'change_comment'
    ]

    readonly_fields = [
        'changed_at' ,
        'affected_items_list'
    ]

    fieldsets = (
        (_('Заявка') , {
            'fields' : ('request' ,)
        }) ,
        (_('Изменение') , {
            'fields' : ('change_type' , 'change_comment')
        }) ,
        (_('Затронутые позиции') , {
            'fields' : ('affected_items_list' ,)
        }) ,
        (_('Результат') , {
            'fields' : ('resulting_snapshot' ,)
        }) ,
        (_('Системное') , {
            'fields' : ('changed_at' ,)
        }) ,
    )

    def change_comment_preview(self , obj) :
        """Предпросмотр комментария"""
        if len(obj.change_comment) > 50 :
            return obj.change_comment[:50] + '...'
        return obj.change_comment or '-'

    change_comment_preview.short_description = _("Комментарий")

    def affected_items_count(self , obj) :
        return obj.affected_items.count()

    affected_items_count.short_description = _("Затронуто позиций")

    def affected_items_list(self , obj) :
        """Список затронутых позиций"""
        items = obj.affected_items.all()
        if not items :
            return "-"
        return ", ".join([str(item) for item in items])

    affected_items_list.short_description = _("Затронутые позиции")

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'request' , 'resulting_snapshot'
        ).prefetch_related('affected_items')
#client_requests/admin/comment_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import CommentType , ClientRequestComment , RequestItemComment


@admin.register(CommentType)
class CommentTypeAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'sorting_order' , 'is_active']
    list_filter = ['is_active']
    search_fields = ['name' , 'code']
    list_editable = ['sorting_order' , 'is_active']


@admin.register(ClientRequestComment)
class ClientRequestCommentAdmin(admin.ModelAdmin) :
    list_display = ['request' , 'comment_preview' , 'comment_type' , 'created_at']
    list_filter = ['comment_type' , 'created_at']
    search_fields = ['request__request_number' , 'comment_text']
    readonly_fields = ['created_at']

    fieldsets = (
        (_('Заявка') , {
            'fields' : ('request' ,)
        }) ,
        (_('Комментарий') , {
            'fields' : ('comment_text' , 'comment_type')
        }) ,
        (_('Системное') , {
            'fields' : ('created_at' ,)
        }) ,
    )

    def comment_preview(self , obj) :
        """Предпросмотр комментария"""
        if len(obj.comment_text) > 50 :
            return obj.comment_text[:50] + '...'
        return obj.comment_text or '-'

    comment_preview.short_description = _("Комментарий")


@admin.register(RequestItemComment)
class RequestItemCommentAdmin(admin.ModelAdmin) :
    list_display = ['request_item' , 'comment_preview' , 'comment_type' , 'parent_request_comment' , 'created_at']
    list_filter = ['comment_type' , 'created_at']
    search_fields = ['request_item__request_parent__request_number' , 'comment_text']
    readonly_fields = ['created_at']

    fieldsets = (
        (_('Позиция') , {
            'fields' : ('request_item' ,)
        }) ,
        (_('Комментарий') , {
            'fields' : ('comment_text' , 'comment_type' , 'parent_request_comment')
        }) ,
        (_('Результат') , {
            'fields' : ('resulting_version' ,)
        }) ,
        (_('Системное') , {
            'fields' : ('created_at' ,)
        }) ,
    )

    def comment_preview(self , obj) :
        """Предпросмотр комментария"""
        if len(obj.comment_text) > 50 :
            return obj.comment_text[:50] + '...'
        return obj.comment_text or '-'

    comment_preview.short_description = _("Комментарий")
# cart/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)
    fields = ('content_type', 'object_id', 'quantity', 'price_snapshot', 'notes', 'added_at')
    autocomplete_fields = []

    def has_add_permission(self, request, obj=None):
        return True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'cart_type', 'status',
        'project_customer', 'user', 'item_count',
        'updated_at',
    )
    list_filter = ('cart_type', 'status', 'project_customer')
    search_fields = ('name', 'user__email', 'project_customer__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'item_count')
    inlines = [CartItemInline]
    fieldsets = (
        (_('Основное'), {
            'fields': (
                'cart_type', 'name', 'status',
            ),
        }),
        (_('Владелец'), {
            'fields': (
                'user', 'session_key',
                'project_customer', 'employee',
            ),
        }),
        (_('Заказ'), {
            'fields': ('client_request',),
        }),
        (_('Системное'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cart', 'sku', 'quantity', 'added_at')
    list_filter = ('sku', 'added_at')
    search_fields = ('cart__name', 'notes')
    readonly_fields = ('added_at',)
    autocomplete_fields = ['cart']

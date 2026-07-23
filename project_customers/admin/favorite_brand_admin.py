# project_customers/admin/favorite_brand_admin.py
from django.contrib import admin
from ..models.favorite_brand import FavoriteBrand


@admin.register(FavoriteBrand)
class FavoriteBrandAdmin(admin.ModelAdmin):
    list_display = ['user', 'brand', 'priority']
    list_filter = ['brand']
    search_fields = ['user__last_name', 'user__first_name', 'brand__name']

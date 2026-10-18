from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Brands, Producer


@admin.register(Brands)
class BrandsAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_editable = ['code', 'sorting_order', 'is_active']
    search_fields = ['name', 'code']


admin.site.register(Producer)

from django.db import models# from django.db import models
from django.utils.translation import gettext_lazy as _

class Brands(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.CharField(max_length=50, blank=True, null=True, #unique=True,
                            verbose_name=_("Код бренда"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    def __str__(self):
        return self.name


class Producer(models.Model):

    name = models.CharField(max_length=100,
                            verbose_name=_("Название производителя"))
    code = models.CharField(max_length=50, blank=True, null=True,# unique=True,
                            verbose_name=_("Код производителя"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    organization = models.CharField(max_length=100, blank=True, verbose_name='Организация')
    brands = models.ManyToManyField(Brands, related_name='producer_brands', verbose_name='Бренды')
    def __str__(self):
        return self.name

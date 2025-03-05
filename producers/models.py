from django.db import models


class Brands(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')

    def __str__(self):
        return self.name


class Producer(models.Model):
    organization = models.CharField(max_length=100, blank=True, verbose_name='Организация')
    brands = models.ManyToManyField(Brands, related_name='producer_brands', verbose_name='Бренды')

    def __str__(self):
        return self.organization

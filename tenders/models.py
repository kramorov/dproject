# OpenRouter API key
'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'

# models.py
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone


class Procurement(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('canceled', 'Отменена'),
        ('completed', 'Завершена'),
        ('draft', 'Черновик'),
        ('rejected', 'Отсев'),
        ('not_actual', 'Не актуально'),
    ]

    PROCUREMENT_TYPE_CHOICES = [
        ('single_lot', 'Иной однолотовый способ'),
        ('price_request', 'Запрос цен'),
        ('proposal_request', 'Запрос предложений'),
        ('auction', 'Аукцион'),
        ('competition', 'Конкурс'),
        ('other', 'Другой'),
    ]

    # Основные поля
    subject = models.TextField(verbose_name='Предмет закупки', db_index=True)
    procurement_number = models.CharField(
        max_length=100,
        verbose_name='№ Закупки',
        validators=[MinLengthValidator(1)],
        db_index=True
    )
    end_date = models.DateTimeField(verbose_name='Дата окончания', db_index=True)

    # Ссылки и доп. информация
    link = models.URLField(verbose_name='Ссылка', blank=True, null=True)
    specification_link = models.URLField(
        verbose_name='ТЗ (если недоступно по основной ссылке)',
        blank=True,
        null=True
    )

    # Статус и управление
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Статус',
        default='active'
    )
    manager = models.CharField(max_length=100, verbose_name='Менеджер', blank=True)
    rejection_reason = models.TextField(verbose_name='Причина отсева', blank=True)

    # Информация о площадке и заказчике
    platform = models.CharField(
        max_length=200,
        verbose_name='Закон или комм.площадка',
        blank=True
    )
    customer = models.CharField(max_length=300, verbose_name='Заказчик', blank=True)
    procurement_type = models.CharField(
        max_length=50,
        choices=PROCUREMENT_TYPE_CHOICES,
        verbose_name='Тип проведения',
        blank=True
    )

    # Финансовые показатели
    nmc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='НМЦ',
        blank=True,
        null=True
    )
    application_guarantee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Обеспечение заявки',
        blank=True,
        null=True
    )
    contract_guarantee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Обеспечение контракта',
        blank=True,
        null=True
    )
    currency = models.CharField(
        max_length=10,
        verbose_name='Валюта',
        blank=True
    )

    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Закупка'
        verbose_name_plural = 'Закупки'
        unique_together = ['subject', 'procurement_number', 'end_date']
        indexes = [
            models.Index(fields=['subject', 'procurement_number']),
            models.Index(fields=['end_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.procurement_number}: {self.subject[:50]}..."


class ImportLog(models.Model):
    IMPORT_STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('partial', 'Частично'),
        ('failed', 'Неудачно'),
    ]

    filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField()
    imported_rows = models.IntegerField()
    skipped_rows = models.IntegerField()
    warnings = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    status = models.CharField(max_length=10, choices=IMPORT_STATUS_CHOICES)

    class Meta:
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'
        ordering = ['-imported_at']

    def __str__(self):
        return f"Импорт {self.filename} - {self.status}"
# image_processor/models.py
"""
ImageCropSession — временная сессия обрезки изображения.

Хранит оригинал, координаты crop-рамки и цвет фона.
После обработки НЕ используется для хранения — только на время сессии.
"""
from django.db import models
from storage_manager.fields import ManagedFileField
from storage_manager.services import file_service


class ImageCropSession(models.Model):
    """Временная сессия: загруженный оригинал + параметры кропа."""

    original_file = ManagedFileField(
        upload_to='image_processor/originals/',
        verbose_name='Оригинал',
    )

    # Crop-рамка: координаты относительно original_file
    # Все в пикселях, float для sub-pixel точности
    crop_x = models.FloatField(null=True, blank=True, verbose_name='X рамки')
    crop_y = models.FloatField(null=True, blank=True, verbose_name='Y рамки')
    crop_size = models.FloatField(null=True, blank=True, verbose_name='Размер рамки (квадрат)')

    # Цвет фона для добивки (HEX, например '#FFFFFF')
    background_color = models.CharField(
        max_length=9, default='#F0F0F0',
        verbose_name='Цвет фона',
    )

    # Удаление фона нейросетью
    remove_background = models.BooleanField(
        default=False,
        verbose_name='Убрать фон (нейросеть)',
    )

    # Результаты обработки (заполняются после /crop/)
    result_sm = ManagedFileField(upload_to='image_processor/results/sm/', blank=True, null=True)
    result_md = ManagedFileField(upload_to='image_processor/results/md/', blank=True, null=True)
    result_lg = ManagedFileField(upload_to='image_processor/results/lg/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сессия обрезки'
        verbose_name_plural = 'Сессии обрезки'

    def __str__(self):
        return f'Crop session #{self.id} ({self.created_at:%Y-%m-%d %H:%M})'

    def delete_files(self):
        """Удалить файлы из Cloud.ru (без удаления записи БД)."""
        fields = ['original_file', 'result_sm', 'result_md', 'result_lg']
        for field_name in fields:
            f = getattr(self, field_name)
            if f and f.name:
                try:
                    file_service.delete_file(f.name)
                except Exception:
                    pass

    def delete(self, *args, **kwargs):
        """Удаляет запись БД и файлы из облака."""
        self.delete_files()
        super().delete(*args, **kwargs)

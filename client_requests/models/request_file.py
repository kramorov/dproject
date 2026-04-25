import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from clients.models import CompanyPerson


class RequestFile(models.Model) :
    """
    Прикрепленные файлы к заявке
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request = models.ForeignKey(
        'ClientRequest' ,
        on_delete=models.CASCADE ,
        related_name='attached_files' ,
        verbose_name=_("Запрос клиента")
    )

    # Файл
    file = models.FileField(
        upload_to='client_requests/%Y/%m/%d/' ,
        verbose_name=_("Файл")
    )

    FILE_TYPES = [
        ('questionnaire' , 'Опросный лист') ,
        ('drawing' , 'Чертеж') ,
        ('specification' , 'Спецификация') ,
        ('photo' , 'Фотография') ,
        ('other' , 'Другое') ,
    ]

    file_type = models.CharField(
        max_length=30 ,
        choices=FILE_TYPES ,
        default='other' ,
        verbose_name=_("Тип файла")
    )

    description = models.CharField(
        max_length=255 ,
        blank=True ,
        verbose_name=_("Описание") ,
        help_text=_("Например: 'Опросный лист от 10.04.2025'")
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата загрузки")
    )

    uploaded_by = models.ForeignKey(
        CompanyPerson ,
        on_delete=models.SET_NULL ,
        null=True ,
        verbose_name=_("Кто загрузил")
    )

    class Meta :
        verbose_name = _("Файл заявки")
        verbose_name_plural = _("Файлы заявок")
        ordering = ['-uploaded_at']

    def __str__(self) :
        return f"{self.request.request_number} - {self.file.name}"

    def filename(self) :
        return self.file.name.split('/')[-1]
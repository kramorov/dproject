#client_requests/models/request_change_log.py
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class RequestChangeLog(models.Model) :
    """
    Журнал изменений заявки (аудит)
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request = models.ForeignKey(
        'ClientRequest' ,
        on_delete=models.CASCADE ,
        related_name='change_logs' ,
        verbose_name=_("Запрос клиента")
    )

    change_comment = models.TextField(
        verbose_name=_("Комментарий изменения") ,
        help_text=_("Что и почему изменилось")
    )

    changed_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата изменения")
    )

    # Какие позиции изменились
    affected_items = models.ManyToManyField(
        'ClientRequestItem' ,
        blank=True ,
        related_name='change_logs' ,
        verbose_name=_("Затронутые позиции") ,
        help_text= _("Позиции, которые были изменены в этом логе"))

    # Ссылка на снапшот, если изменение привело к созданию нового
    resulting_snapshot = models.ForeignKey(
        'RequestSnapshot' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='source_change_logs' ,
        verbose_name=_("Результирующий снапшот")
    )

    # Тип изменения
    CHANGE_TYPES = [
        ('create_request' , 'Создание заявки') ,
        ('add_item' , 'Добавление позиции') ,
        ('modify_item' , 'Изменение позиции') ,
        ('delete_item' , 'Удаление позиции') ,
        ('restore_item' , 'Восстановление позиции') ,
        ('create_snapshot' , 'Создание снапшота') ,
        ('approve_snapshot' , 'Утверждение снапшота') ,
        ('change_status' , 'Изменение статуса') ,
        ('general_edit' , 'Общее редактирование') ,
    ]

    change_type = models.CharField(
        max_length=30 ,
        choices=CHANGE_TYPES ,
        default='general_edit' ,
        verbose_name=_("Тип изменения")
    )

    class Meta :
        verbose_name = _("Журнал изменений")
        verbose_name_plural = _("Журнал изменений")
        ordering = ['-changed_at']

    def __str__(self) :
        return f"{self.request.code} - {self.changed_at.strftime('%Y-%m-%d %H:%M')}"
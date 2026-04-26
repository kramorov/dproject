import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class RequestSnapshot(models.Model) :
    """
    Снимок состояния заявки на момент согласования
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request = models.ForeignKey(
        'ClientRequest' ,
        on_delete=models.CASCADE ,
        related_name='snapshots' ,
        verbose_name=_("Запрос клиента")
    )

    snapshot_number = models.IntegerField(
        verbose_name=_("Номер снапшота") ,
        help_text=_("Порядковый номер версии (1, 2, 3...)")
    )

    snapshot_comment = models.TextField(
        verbose_name=_("Комментарий") ,
        help_text=_("Что зафиксировано в этой версии (например, 'Предварительное согласование')")
    )

    # Флаг утверждения
    is_approved = models.BooleanField(
        default=False ,
        verbose_name=_("Утвержден") ,
        help_text=_("Означает, что эта версия согласована с клиентом")
    )

    approved_at = models.DateTimeField(
        null=True , blank=True ,
        verbose_name=_("Дата утверждения")
    )

    # Денормализованные данные (для скорости)
    snapshot_data = models.JSONField(
        null=True , blank=True ,
        verbose_name=_("Данные снапшота") ,
        help_text=_("Полная копия всех актуальных версий позиций на момент снимка")
    )

    class Meta :
        verbose_name = _("Снимок заявки")
        verbose_name_plural = _("Снимки заявок")
        unique_together = [['request' , 'snapshot_number']]
        ordering = ['-snapshot_number']

    def __str__(self) :
        return f"{self.request.code} - Версия {self.snapshot_number}"

    def save_snapshot(self) :
        """
        Сохранить текущее состояние заявки в снапшот
        """
        items = self.request.request_lines.filter(is_current=True , status='active').order_by('item_no')

        snapshot_items = []
        for item in items :
            snapshot_items.append({
                'item_no' : item.item_no ,
                'version' : item.version ,
                'request_line_text' : item.request_line_text ,
                'request_line_ol' : item.request_line_ol ,
                'status' : item.status ,
                'change_comment' : item.change_comment ,
                'changed_at' : item.changed_at.isoformat() if item.changed_at else None ,
                'requirements' : None ,  # будет заполнено позже, когда добавим требования
                'selection' : None ,  # будет заполнено позже
            })

        self.snapshot_data = {
            'snapshot_number' : self.snapshot_number ,
            'snapshot_comment' : self.snapshot_comment ,
            'items' : snapshot_items ,
            'total_items' : len(snapshot_items)
        }
        self.save()
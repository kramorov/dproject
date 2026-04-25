import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class CommentType(models.Model) :
    """
    Справочник типов комментариев
    """
    name = models.CharField(
        max_length=100 ,
        verbose_name=_("Название") ,
        help_text=_("Название типа комментария для отображения")
    )
    code = models.CharField(
        max_length=30 ,
        unique=True ,
        verbose_name=_("Символьный код") ,
        help_text=_("Код типа комментария (email, internal, change, approval)")
    )

    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Описание типа комментария'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = _("Тип комментария")
        verbose_name_plural = _("Типы комментариев")
        ordering = ['sorting_order' ]

    def __str__(self) :
        return self.name


class ClientRequestComment(models.Model) :
    """
    Комментарий к заявке в целом
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request = models.ForeignKey(
        'ClientRequest' ,
        on_delete=models.CASCADE ,
        related_name='comments' ,
        verbose_name=_("Заявка")
    )

    comment_text = models.TextField(
        verbose_name=_("Текст комментария")
    )

    comment_type = models.ForeignKey(
        CommentType ,
        on_delete=models.SET_NULL ,
        null=True ,
        verbose_name=_("Тип комментария")
    )

    created_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата создания")
    )

    class Meta :
        verbose_name = _("Комментарий к заявке")
        verbose_name_plural = _("Комментарии к заявкам")
        ordering = ['created_at']

    def __str__(self) :
        return f"{self.request.request_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class RequestItemComment(models.Model) :
    """
    Комментарий к позиции запроса
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request_item = models.ForeignKey(
        'ClientRequestItem' ,
        on_delete=models.CASCADE ,
        related_name='comments' ,
        verbose_name=_("Позиция запроса")
    )

    comment_text = models.TextField(
        verbose_name=_("Текст комментария")
    )

    comment_type = models.ForeignKey(
        CommentType ,
        on_delete=models.SET_NULL ,
        null=True ,
        verbose_name=_("Тип комментария")
    )

    # Связь с комментарием к заявке (если этот комментарий является уточнением/частью общего комментария)
    parent_request_comment = models.ForeignKey(
        ClientRequestComment ,
        on_delete=models.CASCADE ,
        null=True , blank=True ,
        related_name='item_comments' ,
        verbose_name=_("Родительский комментарий к заявке")
    )

    # Ссылка на версию, если комментарий привел к изменению
    resulting_version = models.ForeignKey(
        'ClientRequestItem' ,
        null=True , blank=True ,
        on_delete=models.SET_NULL ,
        related_name='version_comments' ,
        verbose_name= _("Результирующая версия")
    )

    created_at = models.DateTimeField(
    auto_now_add = True ,
    verbose_name = _("Дата создания")

)

class Meta :
    verbose_name = _("Комментарий к позиции")
    verbose_name_plural = _("Комментарии к позициям")
    ordering = ['created_at']


def __str__(self) :
    return f"{self.request_item.request_parent.request_number} - Поз.{self.request_item.item_no} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
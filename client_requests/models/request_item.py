# client_requests/models/request_item.py
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver

from clients.models import CompanyPerson


class ClientRequestItem(models.Model) :
    """
    Позиция запроса клиента (с поддержкой версионирования)
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    # Связь с заявкой
    request_parent = models.ForeignKey(
        'ClientRequest' ,
        on_delete=models.CASCADE ,
        related_name="request_lines" ,
        verbose_name=_("Запрос клиента")
    )

    # === ТИП ПОДБОРА ДЛЯ ЭТОЙ ПОЗИЦИИ ===
    item_type = models.ForeignKey(
        'RequestItemType' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Тип подбора") ,
        help_text=_("Что нужно подобрать для этой позиции (арматура, привод, полностью)")
    )

    # === ОСНОВНЫЕ ПОЛЯ ===
    item_no = models.IntegerField(
        default=0 ,
        verbose_name=_("Номер позиции") ,
        help_text=_("Номер позиции в заявке (1, 2, 3...)")
    )

    # Исходные данные из запроса клиента
    source_request_line_number = models.IntegerField(
        null=True , blank=True ,
        verbose_name=_("Номер строки в исходном запросе") ,
        help_text=_("Номер строки в первичном тексте запроса")
    )

    request_line_ol = models.CharField(
        max_length=255 ,
        null=True , blank=True ,
        verbose_name=_("Номер ОЛ") ,
        help_text=_("Идентификатор (номер) опросного листа")
    )

    request_line_text = models.TextField(
        null=True , blank=True ,
        verbose_name=_("Исходный текст") ,
        help_text=_("Исходный текст запроса по этой позиции")
    )

    # === ПОЛЯ ДЛЯ ВЕРСИОНИРОВАНИЯ ===
    version = models.IntegerField(
        default=1 ,
        verbose_name=_("Версия") ,
        help_text=_("Версия требований по этой позиции")
    )

    is_current = models.BooleanField(
        default=True ,
        verbose_name=_("Актуальная версия") ,
        help_text=_("Отмечает текущую активную версию")
    )

    parent_version = models.ForeignKey(
        'self' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='child_versions' ,
        verbose_name=_("Предыдущая версия") ,
        help_text=_("Ссылка на предыдущую версию этой позиции")
    )

    # === МЕТАДАННЫЕ ИЗМЕНЕНИЯ ===
    change_comment = models.TextField(
        null=True , blank=True ,
        verbose_name=_("Комментарий к изменению") ,
        help_text=_("Что и почему изменилось в этой версии")
    )

    changed_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата изменения")
    )

    changed_by = models.ForeignKey(
        CompanyPerson ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Кто изменил") ,
        help_text=_("Сотрудник, внесший изменение")
    )

    # === СТАТУС ПОЗИЦИИ ===
    STATUS_CHOICES = [
        ('active' , 'Активна') ,
        ('deleted' , 'Удалена') ,
        ('replaced' , 'Заменена') ,
        ('merged' , 'Объединена') ,
        ('split' , 'Разделена') ,
    ]

    status = models.CharField(
        max_length=20 ,
        default='active' ,
        choices=STATUS_CHOICES ,
        verbose_name=_("Статус позиции") ,
        help_text=_("Текущий статус позиции")
    )

    class Meta :
        verbose_name = _("Позиция запроса")
        verbose_name_plural = _("Позиции запроса")
        unique_together = [['request_parent' , 'item_no' , 'version']]
        ordering = ['item_no' , '-version']

    def __str__(self) :
        type_name = self.item_type.name if self.item_type else "Не определен"
        return f"{self.request_parent.request_number} - Поз.{self.item_no} ({type_name}) v{self.version}"

    def create_new_version(self , change_comment , changed_by , **updated_fields) :
        """
        Создать новую версию позиции на основе текущей
        """
        # Помечаем текущую как неактивную
        self.is_current = False
        self.status = 'replaced'
        self.save()

        # Создаем новую версию
        new_version = ClientRequestItem.objects.create(
            request_parent=self.request_parent ,
            item_no=self.item_no ,
            version=self.version + 1 ,
            is_current=True ,
            parent_version=self ,
            item_type=self.item_type ,  # копируем тип
            source_request_line_number=self.source_request_line_number ,
            request_line_ol=self.request_line_ol ,
            request_line_text=self.request_line_text ,
            change_comment=change_comment ,
            changed_by=changed_by ,
            status='active' ,
            **updated_fields
        )

        return new_version

    def delete_item(self , change_comment , changed_by) :
        """
        Пометить позицию как удаленную
        """
        self.is_current = False
        self.status = 'deleted'
        self.change_comment = change_comment
        self.changed_by = changed_by
        self.save()

    def get_full_request_text(self) :
        """Получить полный текст запроса с учетом общих требований заявки"""
        texts = []
        if self.request_parent.request_text :
            texts.append(self.request_parent.request_text)
        if self.request_line_text :
            texts.append(self.request_line_text)
        return "\n\n".join(texts)

    @property
    def selection_summary(self) :
        """Краткое описание того, что нужно подобрать"""
        if not self.item_type :
            return "Тип подбора не указан"

        items = []
        if self.item_type.need_valve_selection :
            items.append("арматуру")
        if self.item_type.need_pneumatic_actuator_selection :
            items.append("пневмопривод")
        if self.item_type.need_electric_actuator_selection :
            items.append("электропривод")
        if self.item_type.need_mounting_kit :
            items.append("монтажный комплект")
        if self.item_type.need_fittings :
            items.append("фитинги")
        if self.item_type.need_positioner :
            items.append("позиционер")
        if self.item_type.need_air_preparation :
            items.append("пневмоподготовку")

        if not items :
            return "Нет требований к подбору"

        return f"Подобрать: {', '.join(items)}"


@receiver(pre_save , sender=ClientRequestItem)
def set_item_number(sender , instance , **kwargs) :
    """
    Автоматически установить номер позиции при создании первого экземпляра
    """
    if instance.item_no == 0 :
        max_item_no = ClientRequestItem.objects.filter(
            request_parent=instance.request_parent ,
            version=1
        ).aggregate(Max('item_no'))['item_no__max']

        instance.item_no = max_item_no + 1 if max_item_no is not None else 1
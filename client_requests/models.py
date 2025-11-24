import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from clients.models import Company, CompanyPerson
from djangoProject1.common_models.abstract_models import AbstractValveModel, AbstractElectricActuator, UpdatedAtMixin, \
    CreatedAtMixin
from valve_data.models import ValveLine


class ClientRequestsType(models.Model):
    symbolic_code = models.CharField(max_length=100, help_text='Название типа запроса')
    need_valve_selection = models.BooleanField(default=False)
    need_electric_actuator_selection = models.BooleanField(default=False)
    need_pneumatic_actuator_selection = models.BooleanField(default=False)

    def __str__(self):
        return self.symbolic_code

class ClientRequestsStatus(models.Model):
    symbolic_code = models.CharField(max_length=30, help_text='Символьное обозначение статуса запроса ')
    text_description = models.CharField(max_length=100, help_text='Название статуса запроса для отображения')
    def __str__(self):
        return self.text_description

class ClientRequests(CreatedAtMixin, UpdatedAtMixin):
    REQUEST_STATUS = [
        ('New', 'Новый'),
        ('In progress', 'В работе'),
        ('Processed', 'Обработан'),
        ('Archived', 'Архив'),
        ('Deleted', 'Удален'),
    ]
    request_status = models.ForeignKey(ClientRequestsStatus, on_delete=models.CASCADE, null=True, blank=True,
                                     help_text='Выбор статуса запроса')
    symbolic_code = models.CharField(null=True, blank=True,max_length=100, help_text='Название запроса')
    end_customer = models.CharField(null=True, blank=True, max_length=200, help_text='Конечный заказчик')
    request_type = models.ForeignKey(ClientRequestsType, on_delete=models.CASCADE, null=True, blank=True,
                                     help_text='Выбор типа запроса - что подбираем')
    request_text = models.TextField(null=True, blank=True,
                                         help_text='Текст запроса клиента',
                                         verbose_name="Текст запроса клиента")
    request_from_client_company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True,
                                                    help_text='Выбор компании клиента - для кого подбираем')
    request_responsible_person = models.ForeignKey(CompanyPerson, on_delete=models.CASCADE, null=True, blank=True,
                                                   help_text='Выбор ответственного лица компании клиента')
    request_date = models.DateField()

    def __str__(self):
        if self.symbolic_code:
            return self.symbolic_code
        return f"Запрос #{self.id or 'новый'}"

# class ClientRequestLine(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     request_parent = models.ForeignKey(ClientRequest, on_delete=models.CASCADE, related_name="client_request_line_parent",
#                                        verbose_name="Запрос клиента")
#     current_line_number = models.IntegerField(default=0, help_text='Номер строки в таблице запроса',
#                                   verbose_name="Номер строки в таблице запроса")
#     source_request_line_number = models.IntegerField(null=True, blank=True, help_text='Номер строки в запросе клиента',
#                                               verbose_name="Номер строки в запросе клиента")
#     request_line_text=models.TextField(null=True, blank=True,
#                                        help_text='Текстовое описание строки запроса. Сюда можно скопировать текст, чтобы потом перенести в поля требований',
#                                        verbose_name="Текстовое описание строки запроса. Сюда можно скопировать текст, чтобы потом перенести в поля требований")
#     request_line_ol = models.CharField(max_length=100, null=True, blank=True,
#                                        help_text='Идентификатор (номер) ОЛ для этой строки в запросе клиента',
#                                        verbose_name="Идентификатор (номер) ОЛ для этой строки в запросе клиента")
#
#     class Meta:
#         verbose_name: 'Строка запроса клиента'
#         verbose_name_plural: 'Строки запроса клиента'


class ClientRequestItem(models.Model):
    request_parent = models.ForeignKey(ClientRequests, on_delete=models.CASCADE, related_name="request_lines",
                                       verbose_name="Запрос клиента")
    item_no = models.IntegerField(default=0, help_text='Номер строки в таблице запроса',
                                  verbose_name="Номер строки в таблице запроса")
    request_line_number = models.IntegerField(null=True, blank=True, help_text='Номер строки в запросе клиента',
                                              verbose_name="Номер строки в запросе клиента")
    request_line_ol = models.CharField(max_length=255, null=True, blank=True,
                                       help_text='Идентификатор (номер) ОЛ для этой строки в запросе клиента',
                                       verbose_name="Идентификатор (номер) ОЛ для этой строки в запросе клиента")
    source_request_line_number = models.IntegerField(null=True, blank=True, help_text='Номер строки в запросе клиента',
                                                     verbose_name="Номер строки в запросе клиента")
    request_line_text = models.TextField(null=True, blank=True,
                                         help_text='Текстовое описание строки запроса. Сюда можно скопировать текст, чтобы потом перенести в поля требований',
                                         verbose_name="Текстовое описание строки запроса. Сюда можно скопировать текст, чтобы потом перенести в поля требований")

    class Meta:
        verbose_name: 'Строка запроса клиента'
        verbose_name_plural: 'Строки запроса клиента'


# Сигнал для увеличения item_no перед сохранением
@receiver(pre_save, sender=ClientRequestItem)
def set_item_no(sender, instance, **kwargs):
    # if instance.item_no == 0:  # Проверяем, что item_no еще не установлен
    #     # Находим максимальный item_no для данного request_ptr
    #     max_item_no = \
    #         ClientRequestItem.objects.filter(request_parent=instance.request_parent).aggregate(models.Max('item_no'))[
    #             'item_no__max']
    #     # Если записи с таким request_ptr уже существуют, увеличиваем максимальный item_no на 1, иначе ставим 1
    #     instance.current_line_number = max_item_no + 1 if max_item_no is not None else 1
    max_item_no = \
        ClientRequestItem.objects.filter(request_parent=instance.request_parent).aggregate(models.Max('item_no'))[
            'item_no__max']
    # Если записи с таким item_no уже существуют, увеличиваем максимальный item_no на 1, иначе ставим 1
    instance.item_no = max_item_no + 1 if max_item_no is not None else 1

class ElectricActuatorRequirement(AbstractElectricActuator):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_request_line_item_parent = models.OneToOneField(ClientRequestItem, on_delete=models.CASCADE,
                                                           related_name="electric_actuator_requirement_for_request_line",
                                                           verbose_name="Запрос клиента")

#
# class ValveRequirement(AbstractValveModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     client_request_line_item_parent = models.OneToOneField(ClientRequestItem, on_delete=models.CASCADE,
#                                                            related_name="valve_requirement_for_request_line",
#                                                            verbose_name="Запрос клиента")
#     valve_model_model_line = models.ForeignKey(ValveModelData, related_name='valve_model_model_line_for_request_line',
#                                                blank=True,
#                                                null=True,
#                                                on_delete=models.CASCADE, help_text='Требования к арматуре')
#     valve_model_model_line_str = models.CharField(
#         max_length=255, blank=True, null=True, help_text='Серия арматуры (строковое значение)'
#     )
#
#     def get_text_description(self):
#         if not self.valve_model_model_line:
#             desc_model = self.valve_model_model_line_str
#         else:
#             desc_model = self.valve_model_model_line.name
#         dn = self.valve_model_dn
#         pn = self.valve_model_pn
#         valve_type = self.valve_type.text_description
#         desc_str = f'{valve_type} Модель:{desc_model} Dn:{dn} Pn{pn}'
#         return desc_str
#
#     # def save_model(self, request, obj, form, change):
#     #     # Получаем значения DN и PN из формы
#     #     dn = obj.valve_model_dn
#     #     pn = obj.valve_model_pn
#     #
#     #     # Ищем модель ValveModel по DN и PN
#     #     if dn and pn:
#     #         try:
#     #             valve_model = ValveModelData.objects.get(dn=dn, pn=pn)
#     #             obj.valve_model_model_line = valve_model
#     #         except ValveModelData.DoesNotExist:
#     #             # Если модель не найдена, очищаем поле
#     #             obj.valve_model_model_line = None
#     #     else:
#     #         # Если DN или PN не заполнены, очищаем поле
#     #         obj.valve_model_model_line = None
#     #
#     #     # Сохраняем объект
#     #     super().save_model(request, obj, form, change)
#
#     def clean(self):
#         if not self.valve_model_model_line and not self.valve_model_model_line_str:
#             raise ValidationError("Необходимо указать либо серию арматуры через ссылку, либо через строку.")
#
#         if self.valve_model_model_line and self.valve_model_model_line_str:
#             raise ValidationError("Нельзя указывать оба поля: ссылку и строку для серии арматуры.")
#
# class ValveSelection(AbstractValveModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     client_request_line_item_parent = models.ManyToManyField(ClientRequestItem,
#                                                            related_name="valve_selection_for_request_line",
#                                                            verbose_name="Запрос клиента")
#     valve_model_model_line = models.ForeignKey(ValveModelData,
#                                                related_name='valve_selection_for_request_line',
#                                                blank=True,
#                                                null=True,
#                                                on_delete=models.CASCADE, help_text='Требования к арматуре')
#     valve_model_model_line_str = models.CharField(
#         max_length=255, blank=True, null=True, help_text='Серия арматуры (строковое значение)'
#     )
#


class AbstractRequirement(CreatedAtMixin, UpdatedAtMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_parent = models.ForeignKey(ClientRequests, on_delete=models.CASCADE, related_name="%(class)s_for_request",
                                       verbose_name="Запрос клиента")
    client_request_line_parent = models.ForeignKey(ClientRequestItem, on_delete=models.CASCADE,
                                                           related_name="%(class)s_for_request_line",
                                                           verbose_name="Требования по строке запроса клиента")
    class Meta:
        abstract = True

class AbstractSelection(CreatedAtMixin, UpdatedAtMixin):
    is_active = models.BooleanField(default=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_parent = models.ForeignKey(ClientRequests, on_delete=models.CASCADE, related_name="%(class)s_for_request",
                                       verbose_name="Запрос клиента")
    client_request_line_parent = models.ForeignKey(ClientRequestItem, on_delete=models.CASCADE,
                                                           related_name="%(class)s_for_request_line",
                                                           verbose_name="Подбор по строке запроса клиента")
    client_request_line_number = models.PositiveIntegerField(blank=True, null=True,)
    class Meta:
        abstract = True
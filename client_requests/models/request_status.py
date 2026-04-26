from django.db import models
from django.utils.translation import gettext_lazy as _

import logging
logger = logging.getLogger(__name__)


class ClientRequestStatus(models.Model) :
    """
    Статус обработки заявки клиента
    """
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название статуса запроса для отображения")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
        help_text=_("Символьное обозначение статуса запроса (new, in_progress, processed, archived, deleted)")
    )

    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание статуса запроса для отображения'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = _("Статус запроса клиента")
        verbose_name_plural = _("Статусы запросов клиентов")
        ordering = ['sorting_order']

    def __str__(self) :
        return self.name

    @classmethod
    def get_choices(cls) :
        """Получить список статусов для выпадающего списка"""
        return cls.objects.filter(is_active=True).order_by('sorting_order')

    @classmethod
    def get_default_status(cls) :
        """Получить статус по умолчанию (Новый)"""
        logger.error(f"get_default_status")
        try :
            found=cls.objects.get(code='new')
            logger.error(f'get_default_status found={found}')
            return found
        except cls.DoesNotExist :
            return cls.objects.first()
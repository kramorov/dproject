# project_customers/models/user_parameter.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist


class UserParameter(models.Model) :
    """
    Произвольные параметры/настройки пользователя
    """
    user = models.ForeignKey(
        'ProjectCustomerUser' ,
        on_delete=models.CASCADE ,
        related_name='parameters' ,
        verbose_name=_("Пользователь")
    )

    # Название и код параметра
    name = models.CharField(max_length=200 , verbose_name=_("Название параметра"))
    code = models.CharField(max_length=100 , verbose_name=_("Код параметра"))

    # Значение параметра (текст)
    value = models.TextField(blank=True , verbose_name=_("Значение"))

    # Признак системного (неудаляемого) параметра
    is_system = models.BooleanField(default=False , verbose_name=_("Системный"))

    # Описание (необязательно)
    description = models.TextField(blank=True , verbose_name=_("Описание"))

    class Meta :
        verbose_name = _("Параметр пользователя")
        verbose_name_plural = _("Параметры пользователей")
        unique_together = [['user' , 'code']]  # У одного пользователя код уникален

    def __str__(self) :
        return f"{self.user.get_full_name()} - {self.name}"


# Функция для получения параметра
def get_user_parameter(user , parameter_code , default_value=None) :
    """
    Получить значение параметра пользователя по коду

    Args:
        user: объект ProjectCustomerUser
        parameter_code: код параметра (строка)
        default_value: значение по умолчанию, если параметр не найден

    Returns:
        str: значение параметра или default_value
    """
    try :
        param = UserParameter.objects.get(user=user , code=parameter_code)
        return param.value
    except ObjectDoesNotExist :
        return default_value


# Функция для установки параметра
def set_user_parameter(user , parameter_code , value , name=None , is_system=False , description=None) :
    """
    Установить значение параметра пользователя

    Args:
        user: объект ProjectCustomerUser
        parameter_code: код параметра
        value: значение
        name: название (если не указано, используется parameter_code)
        is_system: системный ли параметр
        description: описание
    """
    param , created = UserParameter.objects.get_or_create(
        user=user ,
        code=parameter_code ,
        defaults={
            'name' : name or parameter_code ,
            'value' : value ,
            'is_system' : is_system ,
            'description' : description or ''
        }
    )
    if not created :
        param.value = value
        param.save()
    return param
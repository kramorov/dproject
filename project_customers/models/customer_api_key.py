# project_customers/models/customer_api_key.py
import hashlib
import secrets
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerApiKey(models.Model):
    """
    API-ключ для доступа к мини-приложениям (виджетам на сайтах клиентов).
    """
    customer = models.ForeignKey(
        'ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name=_("Организация")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название ключа"),
        help_text=_("Например: «Виджет НТА-Пром» или «LLM-агент Архимед»")
    )
    key_hash = models.CharField(
        max_length=128,
        verbose_name=_("Хэш ключа"),
        help_text=_("SHA-256(raw_key)")
    )
    key_prefix = models.CharField(
        max_length=12,
        default="proj_live_",
        verbose_name=_("Префикс ключа")
    )

    allowed_apps = models.ManyToManyField(
        'AllowedApp',
        blank=True,
        verbose_name=_("Разрешённые мини-приложения"),
        help_text=_("Подмножество от CustomerAppAccess организации")
    )

    # Дополнительный фильтр брендов (сужает org-level CustomerAppAccess)
    # Формат: {"limit_switch": [1, 3], "gearbox": "all"}
    brand_filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Фильтры брендов"),
        help_text=_('{"app_code": "all" | [brand_id, ...]} — сужает org-level доступ')
    )

    ip_whitelist = models.TextField(
        blank=True,
        verbose_name=_("IP whitelist"),
        help_text=_("Список IP/подсетей через запятую. Пусто = без ограничений.")
    )
    access_until = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Доступ до"),
        help_text=_("Ограничение по времени действия ключа")
    )

    # Будущее: своя LLM клиента
    llm_endpoint = models.URLField(
        blank=True,
        verbose_name=_("LLM endpoint"),
        help_text=_("URL своей LLM клиента (заготовка на будущее)")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Создан")
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Последнее использование")
    )

    class Meta:
        verbose_name = _("API-ключ")
        verbose_name_plural = _("API-ключи")

    def __str__(self):
        return f"{self.name} ({self.customer.name})"

    @classmethod
    def generate_key(cls, customer, name):
        """
        Генерирует новый ключ, возвращает (instance, raw_key).
        raw_key показывается ТОЛЬКО один раз при создании.
        """
        raw = f"proj_live_{secrets.token_hex(16)}"
        instance = cls(
            customer=customer,
            name=name,
            key_prefix="proj_live_",
            key_hash=hashlib.sha256(raw.encode()).hexdigest()
        )
        instance._raw_key = raw
        instance.save()
        return instance, raw

    @classmethod
    def lookup(cls, raw_key):
        """
        Найти активный ключ по сырому значению.
        Возвращает CustomerApiKey или None (в т.ч. если истёк срок).
        """
        from datetime import date
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            key = cls.objects.select_related('customer').get(
                key_hash=key_hash,
                is_active=True,
            )
            if key.access_until and key.access_until < date.today():
                return None
            return key
        except cls.DoesNotExist:
            return None

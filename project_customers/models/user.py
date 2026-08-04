#project_customers/models/user.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password


class ProjectCustomerUser(models.Model):
    """
    Пользователь клиента — самостоятельная точка входа.
    Django User используется только для superuser/staff (админка Django).
    """
    # Связь с Django User — только для superuser/staff (админка)
    # Для обычных пользователей клиента — NULL
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='customer_profile',
        verbose_name=_("Пользователь Django"),
        help_text=_("Только для администраторов системы. Для клиентских пользователей — пусто.")
    )

    customer = models.ForeignKey(
        'ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Клиент")
    )

    # Логин — основной идентификатор для входа
    login = models.CharField(
        max_length=100,
        default='',
        verbose_name=_("Логин"),
        help_text=_("Используется для входа в систему")
    )

    # Контактные данные
    first_name = models.CharField(max_length=100, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=100, verbose_name=_("Фамилия"))
    middle_name = models.CharField(max_length=100, blank=True, verbose_name=_("Отчество"))

    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Телефон"))

    # Должность
    position = models.CharField(max_length=200, blank=True, verbose_name=_("Должность"))

    # Дефолтное юридическое лицо (для КП и счетов)
    default_legal_entity = models.ForeignKey(
        'LegalEntity',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Юридическое лицо по умолчанию")
    )

    # === Аутентификация ===
    password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_("Пароль (хэш)"),
        help_text=_("Хранится в хэшированном виде")
    )
    last_login = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_("Последний вход")
    )

    # === Системные права ===
    system_groups = models.ManyToManyField(
        'SystemGroup',
        blank=True,
        related_name='members',
        verbose_name=_("Системные группы"),
    )

    # === Организационные права ===
    roles = models.ManyToManyField(
        'Role',
        blank=True,
        related_name='users',
        verbose_name=_("Роли")
    )
    section_permissions = models.ManyToManyField(
        'SiteSection',
        blank=True,
        related_name='users',
        verbose_name=_("Индивидуальный доступ к разделам"),
        help_text=_("Дополнительные разрешения поверх ролей (не могут превысить права организации)")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # === Аутентификация: свойства для совместимости с Django auth ===
    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    class Meta:
        verbose_name = _("Пользователь клиента")
        verbose_name_plural = _("Пользователи клиентов")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.customer.name})"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # === Системные права ===

    def has_system_perm(self, codename: str, action: str = 'view') -> bool:
        for group in self.system_groups.all():
            perms = group.object_permissions.get(codename, [])
            if action in perms or 'manage' in perms:
                return True
        return False

    def get_object_permissions(self) -> dict:
        result = {}
        for group in self.system_groups.all():
            for obj, actions in group.object_permissions.items():
                result.setdefault(obj, set()).update(actions)
        return {k: list(v) for k, v in result.items()}

    # === Организационные права ===

    def get_effective_section_permissions(self):
        """
        Effective section permissions = org_roles + individual.
        Does NOT exceed customer.visible_sections.
        """
        from project_customers.models import SiteSection
        role_sections = SiteSection.objects.filter(role__users=self)
        individual = self.section_permissions.all()
        return (role_sections | individual).distinct()

    def get_effective_brands(self):
        fav_qs = self.favorite_brands.select_related('brand').order_by('priority')
        if fav_qs.exists():
            return [fb.brand for fb in fav_qs]
        return list(self.customer.visible_brands.all())

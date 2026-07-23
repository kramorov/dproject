#project_customers/admin/user_admin.py
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from ..models.user import ProjectCustomerUser


class CustomerProfileInline(admin.StackedInline):
    model = ProjectCustomerUser
    extra = 0
    filter_horizontal = ['roles', 'section_permissions']
    fields = ['customer', 'first_name', 'last_name', 'middle_name',
              'email', 'phone', 'position', 'roles', 'section_permissions',
              'is_active']


# Расширенная админка Django User — показывает профиль клиента
admin.site.unregister(User)
@admin.register(User)
class ExtendedUserAdmin(DjangoUserAdmin):
    inlines = [CustomerProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'get_customer', 'get_roles']
    list_filter = ['is_active', 'is_staff', 'is_superuser']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'customer_profile__customer',
            'customer_profile__roles',
        )

    def get_customer(self, obj):
        try:
            return obj.customer_profile.customer.name
        except ProjectCustomerUser.DoesNotExist:
            return '-'
    get_customer.short_description = 'Организация'

    def get_roles(self, obj):
        try:
            return ', '.join(r.name for r in obj.customer_profile.roles.all())
        except ProjectCustomerUser.DoesNotExist:
            return '-'
    get_roles.short_description = 'Роли'


# Админка ProjectCustomerUser
@admin.register(ProjectCustomerUser)
class ProjectCustomerUserAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'customer', 'email', 'get_roles_display',
                    'get_django_user', 'is_active']
    list_filter = ['customer', 'is_active', 'roles']
    search_fields = ['last_name', 'first_name', 'email', 'user__username']
    filter_horizontal = ['roles', 'section_permissions']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    actions = ['create_django_user']
    fieldsets = [
        (None, {'fields': ['customer', 'user', 'is_active']}),
        ('Данные', {'fields': ['first_name', 'last_name', 'middle_name',
                               'email', 'phone', 'position']}),
        ('Пароль', {'fields': ['password'],
                    'description': 'Хранится в хэшированном виде. Для входа также нужен Django User (поле выше).'}),
        ('Права', {'fields': ['roles', 'section_permissions']}),
        ('Служебное', {'fields': ['created_at', 'updated_at', 'last_login']}),
    ]

    def get_roles_display(self, obj):
        return ', '.join(r.name for r in obj.roles.all())
    get_roles_display.short_description = 'Роли'

    def get_django_user(self, obj):
        if obj.user:
            return obj.user.username
        return '—'
    get_django_user.short_description = 'Django User'

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            raw_pwd = form.cleaned_data['password']
            if raw_pwd and not raw_pwd.startswith('pbkdf2_'):
                obj.set_password(raw_pwd)
        super().save_model(request, obj, form, change)

    @admin.action(description='Создать Django User для выбранных пользователей')
    def create_django_user(self, request, queryset):
        created = 0
        skipped = 0
        for profile in queryset:
            if profile.user_id:
                skipped += 1
                continue
            django_user = User.objects.create_user(
                username=f'cu_{profile.email.split("@")[0]}',
                email=profile.email,
                first_name=profile.first_name,
                last_name=profile.last_name,
                is_active=True,
                is_staff=False,
                password=None,
            )
            django_user.set_unusable_password()
            django_user.save()
            profile.user = django_user
            profile.save(update_fields=['user'])
            created += 1

        if created:
            self.message_user(request, f'Создано Django User: {created}.', messages.SUCCESS)
        if skipped:
            self.message_user(request, f'Пропущено (уже есть): {skipped}.', messages.WARNING)

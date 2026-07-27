# Create system customer "anonymous_web" for unauthenticated website users.

from django.db import migrations


def create_anonymous(apps, schema_editor):
    ProjectCustomer = apps.get_model("project_customers", "ProjectCustomer")
    if not ProjectCustomer.objects.filter(name__startswith="Неавторизованный").exists():
        ProjectCustomer.objects.create(
            name="Неавторизованный пользователь сайта",
            short_name="Anonymous",
            is_active=True,
        )


def remove_anonymous(apps, schema_editor):
    ProjectCustomer = apps.get_model("project_customers", "ProjectCustomer")
    ProjectCustomer.objects.filter(name__startswith="Неавторизованный").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0013_fix_token_field_names"),
        ("project_customers", "__first__"),
    ]
    operations = [
        migrations.RunPython(create_anonymous, remove_anonymous),
    ]

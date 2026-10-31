# options/migrations/0002_create_cablegland_through_model.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('options', '0001_cablegland_through_model'),
        ('electric_actuators', '0029_alter_electricactuatormodelline_description_and_more'),
    ]

    operations = [
        # Модель CableGlandHolesSetThroughOption уже создана в options/0001
        # (с тем же определением) — повторный CreateModel падает на свежей БД
        # «table already exists». Миграция остаётся пустой: состояние после
        # 0001 уже содержит модель, а депенденси сохраняют порядок.
    ]

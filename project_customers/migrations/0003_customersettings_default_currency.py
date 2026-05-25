# Generated migration: add default_currency to CustomerSettings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project_customers', '0002_userparameter'),
        ('price', '__first__'),
    ]

    operations = [
        migrations.AddField(
            model_name='customersettings',
            name='default_currency',
            field=models.ForeignKey(
                blank=True,
                help_text='В какой валюте показывать цены в каталоге (RUB, USD, ...)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='price.currency',
                verbose_name='Валюта каталога',
            ),
        ),
    ]

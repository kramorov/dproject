# Generated manually — adds variants JSONField to MediaLibraryItem

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_library', '0012_imagegalleryset_imagegallerysetitem_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='medialibraryitem',
            name='variants',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Сгенерированные варианты: размеры, страницы PDF',
                verbose_name='Варианты',
            ),
        ),
    ]

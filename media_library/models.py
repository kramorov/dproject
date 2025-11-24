# media_library/models.py
import os
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from storage_manager.fields import ManagedFileField
from storage_manager.services import file_service

User = get_user_model()
logger = logging.getLogger(__name__)


class MediaCategory(models.Model):
    """Категория медиаматериалов"""

    # Предопределенные категории с иконками, описанием и порядком
    PREDEFINED_CATEGORIES = [
        ('DRAWING', 'Чертеж', '📐', 'Чертежи и технические схемы изделий', 1),
        ('PHOTO', 'Изображение', '📷', 'Фотографии и изображеия изделий и компонентов', 2),
        ('SCHEMA', 'Схема', '🔌', 'Электрические и гидравлические схемы', 3),
        ('DIAGRAM', 'Диаграмма', '📊', 'Графики и диаграммы', 4),
        ('MANUAL', 'Инструкция', '📖', 'Инструкции по сборке и настройке', 5),
        ('USER_MANUAL', 'Руководство по эксплуатации', '📚', 'Руководства по эксплуатации оборудования', 6),
        ('WORD_TEMPLATE', 'Шаблон документа Word', '📝', 'Шаблоны документов Microsoft Word', 7),
        ('EXCEL_TEMPLATE', 'Шаблон документа Excel', '📊', 'Шаблоны таблиц Microsoft Excel', 8),
        ('CERTIFICATE', 'Сертификат', '🏆', 'Сертификаты соответствия и качества', 9),
        ('TECH_DOC', 'Техдокументация', '📋', 'Техническая документация', 10),
        ('PRESENTATION', 'Презентация', '📽️', 'Презентации и демонстрационные материалы', 11),
        ('VIDEO', 'Видео', '🎬', 'Видео материалы и обучающие ролики', 12),
        ('BROCHURE', 'Листовка', '📄', 'Рекламные листовки и буклеты', 13),
        ('CATALOG', 'Каталог', '📑', 'Каталоги продукции и комплектующих', 14),
        ('AUDIO', 'Аудио', '🎵', 'Аудио материалы', 15),
        ('OTHER', 'Другое', '📁', 'Прочие медиа материалы', 100),
    ]

    PREDEFINED_CODES = [code for code, name, icon, desc, order in PREDEFINED_CATEGORIES]

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Название"),
        help_text=_("Уникальное название категории")
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Код категории"),
        help_text=_("Уникальный код категории (заглавные латинские буквы, цифры, подчеркивания)")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Подробное описание категории")
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        default="📁",
        verbose_name=_("Иконка"),
        help_text=_("Emoji или код иконки для отображения")
    )

    is_predefined = models.BooleanField(
        default=False,
        verbose_name=_("Предопределенная"),
        editable=False
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активна")
    )

    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Категория медиа")
        verbose_name_plural = _("Категории медиа")
        ordering = ['sorting_order', 'name']
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self):
        predefined_marker = "⚙️ " if self.is_predefined else "📁 "
        return f"{predefined_marker}{self.name}"

    def save(self, *args, **kwargs):
        # Автоматически определяем предопределенные категории
        self.is_predefined = self.code in self.PREDEFINED_CODES

        # Валидация кода
        if not self._validate_code():
            raise ValidationError(_("Код должен содержать только заглавные латинские буквы, цифры и подчеркивания"))

        super().save(*args, **kwargs)

    def _validate_code(self):
        """Валидация формата кода"""
        code_clean = self.code.replace('_', '')
        return code_clean.isalnum() and self.code.isupper()

    def clean(self):
        """Дополнительная валидация"""
        errors = {}

        # Проверка уникальности кода (кроме текущего объекта)
        if MediaCategory.objects.filter(code=self.code).exclude(pk=self.pk).exists():
            errors['code'] = _('Категория с кодом "%(code)s" уже существует') % {'code': self.code}

        if self.code in self.PREDEFINED_CODES and not self.is_predefined:
            errors['code'] = _('Код "%(code)s" зарезервирован для предопределенной категории') % {'code': self.code}

        if errors:
            raise ValidationError(errors)

    @classmethod
    def get_or_create_predefined(cls):
        """Создает предопределенные категории при необходимости"""
        for code, name, icon, description, sorting_order in cls.PREDEFINED_CATEGORIES:
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'icon': icon,
                    'description': description,
                    'sorting_order': sorting_order,
                    'is_predefined': True,
                }
            )

    @property
    def is_user_defined(self):
        """Является ли категория пользовательской"""
        return not self.is_predefined

    @property
    def can_delete(self):
        """Можно ли удалить категорию"""
        return not self.is_predefined and not self.media_items.exists()

    @property
    def media_items_count(self):
        """Количество медиа элементов в категории"""
        return self.media_items.count()


class MediaTag(models.Model):
    """Теги для медиаматериалов"""

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Название тега"),
        help_text=_("Уникальное название тега")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Тег медиа")
        verbose_name_plural = _("Теги медиа")
        ordering = ['name']

    def __str__(self):
        return self.name


class MediaLibraryItem(models.Model):
    """Элемент медиабиблиотеки"""

    title = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название медиа элемента")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Подробное описание содержимого")
    )

    # Файл через ManagedFileField
    media_file = ManagedFileField(
        # upload_to='media_library/',
        category='media_library',
        blank=True,
        null=True,
        verbose_name=_("Медиафайл"),
        help_text=_("Загрузите медиафайл")
    )

    # Превью для изображений
    preview_file = ManagedFileField(
        # upload_to='media_library/previews/',
        category='media_library_previews',
        blank=True,
        null=True,
        verbose_name=_("Превью"),
        help_text=_("Автоматически создаваемое превью для изображений"),
        editable=False
    )

    # Классификация
    category = models.ForeignKey(
        MediaCategory,
        on_delete=models.PROTECT,
        related_name='media_items',
        verbose_name=_("Категория")
    )

    tags = models.ManyToManyField(
        MediaTag,
        blank=True,
        related_name='media_items',
        verbose_name=_("Теги")
    )

    # MIME-тип для определения типа контента
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("MIME-тип"),
        help_text=_("Тип содержимого файла (определяется автоматически)")
    )

    # Системные поля
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )

    is_public = models.BooleanField(
        default=True,
        verbose_name=_("Публичный"),
        help_text=_("Доступен для всех пользователей")
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_media_items',
        verbose_name=_("Кто создал")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Элемент медиабиблиотеки")
        verbose_name_plural = _("Элементы медиабиблиотеки")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.category.name})"

    def save(self, *args, **kwargs):
        """
        Автоматически заполняем поля при сохранении
        """
        # Определяем MIME-тип ДО сохранения
        if self.media_file and not self.mime_type:
            self.mime_type = self._detect_mime_type()
            logger.info(f"Определен MIME-тип: {self.mime_type} для файла {self.media_file.name}")

        # Сохраняем объект чтобы получить pk
        super().save(*args, **kwargs)

        # Создаем превью ПОСЛЕ сохранения (когда есть pk)
        if self.is_image() and self.media_file and not self.preview_file:
            logger.info(f"Создание превью для {self.pk}")
            if self.create_preview():
                # Сохраняем снова чтобы обновить preview_file
                super().save(update_fields=['preview_file'])
                logger.info(f"Превью создано для {self.pk}")
            else:
                logger.warning(f"Не удалось создать превью для {self.pk}")


    def _detect_mime_type(self):
        """Определяет MIME-тип файла по расширению"""
        if not self.media_file:
            return ''

        extension = os.path.splitext(self.media_file.name)[1].lower()

        mime_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.bmp': 'image/bmp', '.svg': 'image/svg+xml',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.mp4': 'video/mp4', '.avi': 'video/x-msvideo', '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
            '.zip': 'application/zip', '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.txt': 'text/plain', '.rtf': 'application/rtf', '.csv': 'text/csv',
        }

        return mime_types.get(extension, 'application/octet-stream')

    def clean(self):
        """Валидация"""
        if self.media_file and self.media_file.size > 100 * 1024 * 1024:  # 100MB limit
            raise ValidationError({
                'media_file': _('Размер файла не должен превышать 100 МБ')
            })

    @property
    def filename(self):
        """Имя файла без пути"""
        if self.media_file:
            return os.path.basename(self.media_file.name)
        return ""

    @property
    def file_extension(self):
        """Расширение файла"""
        if self.media_file:
            return os.path.splitext(self.media_file.name)[1].lower().replace('.', '')
        return ""

    @property
    def file_size_display(self):
        """Размер файла в читаемом формате"""
        if self.media_file:
            size = self.media_file.size
            if size == 0:
                return "0 Б"

            units = ['Б', 'КБ', 'МБ', 'ГБ']
            for unit in units:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0

            return f"{size:.1f} ТБ"
        return "0 Б"

    @property
    def download_url(self):
        """URL для скачивания файла"""
        if self.media_file:
            return self.media_file.url
        return ""

    def get_absolute_url(self):
        """Абсолютный URL для детальной страницы"""
        from django.urls import reverse
        return reverse('media_library:media_detail', kwargs={'pk': self.pk})

    def is_image(self) :
        """Проверяет, является ли файл изображением"""
        if not self.media_file :
            return False

        # Проверяем по расширению файла
        image_extensions = {'.jpg' , '.jpeg' , '.png' , '.gif' , '.bmp' , '.webp' , '.svg'}
        file_extension = f".{self.file_extension}".lower() if self.file_extension else ""

        # Также проверяем по MIME-типу для надежности
        image_mime_types = {
            'image/jpeg' , 'image/png' , 'image/gif' , 'image/bmp' ,
            'image/webp' , 'image/svg+xml'
        }

        is_image_by_extension = file_extension in image_extensions
        is_image_by_mime = self.mime_type in image_mime_types if self.mime_type else False

        logger.debug(f"is_image проверка для {self.pk}: "
                     f"расширение={file_extension}, MIME={self.mime_type}, "
                     f"по расширению={is_image_by_extension}, по MIME={is_image_by_mime}")

        return is_image_by_extension or is_image_by_mime

    def is_video(self):
        """Проверяет, является ли файл видео"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        return self.file_extension.lower() in video_extensions

    def is_document(self):
        """Проверяет, является ли файл документом"""
        document_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        return self.file_extension.lower() in document_extensions

    def create_preview(self) :
        """Создает превью для изображений с улучшенной диагностикой"""
        if not self.is_image() or not self.media_file :
            logger.warning(f"Превью не создается: не изображение или нет файла")
            return False

        try :
            from PIL import Image
            from io import BytesIO
            import os

            logger.info(f"Создание превью для {self.pk}, файл: {self.media_file.name}")

            # Проверяем существование файла в хранилище
            if not self.media_file.storage.exists(self.media_file.name) :
                logger.error(f"Оригинальный файл не существует: {self.media_file.name}")
                return False

            # Открываем оригинальный файл
            with self.media_file.storage.open(self.media_file.name , 'rb') as original_file :
                img = Image.open(original_file)
                logger.info(f"Изображение открыто: {img.format}, {img.mode}, {img.size}")

                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA' , 'P' , 'LA') :
                    img = img.convert('RGB')
                    logger.info(f"Конвертировано в RGB")
                elif img.mode != 'RGB' :
                    img = img.convert('RGB')
                    logger.info(f"Конвертировано в RGB из {img.mode}")

                # Определяем размеры превью
                max_size = (400 , 300)
                img.thumbnail(max_size , Image.Resampling.LANCZOS)
                logger.info(f"Размер превью: {img.size}")

                # Сохраняем в буфер
                buffer = BytesIO()
                img.save(buffer , format='JPEG' , quality=85 , optimize=True)
                buffer.seek(0)

                # Генерируем имя для превью
                original_name = os.path.basename(self.media_file.name)
                name_without_ext = os.path.splitext(original_name)[0]
                preview_filename = f"{name_without_ext}_preview.jpg"

                # Сохраняем превью
                from django.core.files import File
                django_file = File(buffer , name=preview_filename)

                self.preview_file.save(preview_filename , django_file , save=False)
                logger.info(f"Превью сохранено: {self.preview_file.name}")

                buffer.close()
                return True

        except ImportError :
            logger.error("PIL (Pillow) не установлен")
            return False
        except Exception as e :
            logger.error(f"Ошибка создания превью: {str(e)}" , exc_info=True)
            return False

    def recreate_preview(self) :
        """
        Принудительно пересоздает превью для изображения
        """
        if not self.is_image() or not self.media_file :
            return False , "Файл не является изображением или отсутствует"

        try :
            # Удаляем старое превью если есть
            if self.preview_file :
                old_preview_name = self.preview_file.name
                self.preview_file.delete(save=False)
                logger.info(f"Удалено старое превью: {old_preview_name}")

            # Создаем новое превью
            success = self.create_preview()
            if success :
                self.save(update_fields=['preview_file'])
                return True , "Превью успешно создано"
            else :
                return False , "Не удалось создать превью"

        except Exception as e :
            logger.error(f"Ошибка при пересоздании превью для {self.pk}: {str(e)}")
            return False , f"Ошибка: {str(e)}"
    def replace_file(self , new_file , create_preview=True) :
        """Заменяет файл используя ManagedFileField"""
        try :
            logger.info(f"Замена файла для {self.pk}")

            # Удаляем старые файлы через сервис
            old_media_path = self.media_file.name if self.media_file else None
            old_preview_path = self.preview_file.name if self.preview_file else None

            # Просто сохраняем новый файл - ManagedFileField сам все обработает
            self.media_file = new_file
            self.mime_type = self._detect_mime_type()

            # Сохраняем чтобы сгенерировалось имя файла
            self.save()

            # Удаляем старые файлы
            if old_media_path :
                file_service.delete_file(old_media_path)
            if old_preview_path :
                file_service.delete_file(old_preview_path)

            # Создаем превью если нужно
            if create_preview and self.is_image() :
                self.create_preview()
                self.save(update_fields=['preview_file'])

            return True
        except Exception as e :
            logger.error(f"Ошибка замены файла: {str(e)}")
            return False

    def _update_file_info(self):
        """Обновляет информацию о файле после замены"""
        if self.media_file:
            import os
            from django.core.files.storage import default_storage

            # Обновляем информацию о файле
            self.filename = os.path.basename(self.media_file.name)
            self.file_size = self.media_file.size

            # Определяем MIME тип
            try:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(self.media_file.name)
                self.mime_type = mime_type or 'application/octet-stream'
            except:
                self.mime_type = 'application/octet-stream'

            # Обновляем описание если оно стандартное
            if not self.description or self.description.startswith("Файл: "):
                filename_without_ext = os.path.splitext(self.filename)[0]
                separators = ['_', '-', '.', ',', ';', '—', '–']
                for sep in separators:
                    filename_without_ext = filename_without_ext.replace(sep, ' ')
                self.description = f"Файл: {filename_without_ext.strip()}"


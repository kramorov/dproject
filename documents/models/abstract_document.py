# documents/models/abstract_document.py
"""
AbstractDocument — абстрактный класс документа.

Общие поля для всех документов: name, code, description, status,
document_date, created_at, updated_at, sorting_order, is_active.

Подклассы ОБЯЗАНЫ переопределить:
    - register_changes()   — проведение (создать движения по регистрам)
    - unregister_changes() — отмена проведения (удалить движения)
    - get_items_related_name() — имя related_name строк документа

Концепция как в 1С: документ → проведение → движения по регистрам.

Статусная модель:
    DRAFT → ON_APPROVAL → POSTED
    Любой статус → DELETED (с авто-отменой проведения)
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class AbstractDocument(models.Model):
    """
    Абстрактный документ — заголовок.

    Поля:
        name          — название документа
        code          — код (из нумератора или ручной)
        description   — комментарий
        status        — черновик / на согласовании / проведён / удалён
        document_date — дата документа
        created_at    — дата создания записи
        updated_at    — дата изменения записи
        sorting_order — порядок сортировки
        is_active     — активно (soft delete)

    Атрибуты класса:
        NUMERATOR_PREFIX — префикс нумератора (подкласс задаёт)
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        ON_APPROVAL = 'on_approval', _('На согласовании')
        POSTED = 'posted', _('Проведён')
        DELETED = 'deleted', _('Удалён')

    # ── Префикс нумератора (подкласс переопределяет) ──
    NUMERATOR_PREFIX = None

    # ── Основные реквизиты ──
    name = models.CharField(
        max_length=200,
        verbose_name=_('Название документа'),
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Код'),
        help_text=_('Уникальный код документа (из нумератора или ручной)'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Комментарий'),
    )

    # ── Статус ──
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Статус'),
        help_text=_('Черновик → На согласовании → Проведён → Удалён'),
    )

    # ── Даты ──
    document_date = models.DateField(
        default=now,
        verbose_name=_('Дата документа'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Создан'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Изменён'),
    )

    # ── Служебные ──
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_('Сортировка'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно'),
    )

    class Meta:
        abstract = True
        ordering = ['-document_date']

    # ── save ──

    def save(self, *args, **kwargs):
        """При первом сохранении автоматически присвоить код из нумератора."""
        if not self.code and self.NUMERATOR_PREFIX:
            # Не присваиваем код при частичном сохранении (update_fields)
            # иначе нумератор инкрементится, а save может откатиться
            if not kwargs.get('update_fields'):
                self.assign_code(self.NUMERATOR_PREFIX)
        super().save(*args, **kwargs)

    # ── __str__ ──

    def __str__(self):
        labels = {
            'draft': '✎',
            'on_approval': '⟳',
            'posted': '✓',
            'deleted': '✕',
        }
        label = labels.get(self.status, '?')
        code_part = f' [{self.code}]' if self.code else ''
        return f"{label} {self.name}{code_part} ({self.document_date})"

    # ── Properties ──

    @property
    def is_posted(self):
        """Проведён ли документ (и не удалён)."""
        return self.status == self.Status.POSTED

    @property
    def is_deleted(self):
        """Помечен ли документ на удаление."""
        return self.status == self.Status.DELETED

    # ── Статусные переходы ──

    @classmethod
    def get_allowed_status_transitions(cls):
        """
        Разрешённые переходы статусов.

        Возвращает set of (from_status, to_status).
        Переопределите в подклассе, если нужны другие переходы.
        """
        return {
            (cls.Status.DRAFT, cls.Status.ON_APPROVAL),
            (cls.Status.ON_APPROVAL, cls.Status.POSTED),
            # Любой статус можно пометить на удаление
            (cls.Status.DRAFT, cls.Status.DELETED),
            (cls.Status.ON_APPROVAL, cls.Status.DELETED),
            (cls.Status.POSTED, cls.Status.DELETED),
            # Из удалённых можно восстановить
            (cls.Status.DELETED, cls.Status.DRAFT),
        }

    def can_transition_to(self, new_status):
        """Проверить, разрешён ли переход в new_status."""
        return (self.status, new_status) in self.get_allowed_status_transitions()

    # ── get_compact_data ──

    @classmethod
    def get_available_features(cls):
        """
        Какие действия поддерживает этот тип документа.

        Автоматически определяет, переопределены ли методы в подклассе.
        Если метод переопределён — фича доступна (True).

        Подкласс МОЖЕТ переопределить этот метод для ручного контроля,
        но обычно достаточно переопределить сами export/print/import методы.

        Фронтенд использует features в ответе API чтобы скрыть
        недоступные кнопки (печать, экспорт, импорт).

        Returns:
            dict: {'print': False, 'export_word': False, 'export_excel': False,
                   'export_pdf': False, 'import': False}
        """
        return {
            'print': cls.get_print_html is not AbstractDocument.get_print_html,
            'export_word': cls.export_word is not AbstractDocument.export_word,
            'export_excel': cls.export_excel is not AbstractDocument.export_excel,
            'export_pdf': cls.export_pdf is not AbstractDocument.export_pdf,
            'import': cls.import_from_file is not AbstractDocument.import_from_file,
        }

    def get_compact_data(self):
        """
        Минимальные данные для списков / журналов.

        Подклассы ДОЛЖНЫ вызывать super().get_compact_data()
        и дополнять словарь своими полями.
        """
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code or '',
            'description': self.description,
            'status': self.status,
            'status_label': self.get_status_display(),
            'is_posted': self.is_posted,
            'is_deleted': self.is_deleted,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sorting_order': self.sorting_order,
            'is_active': self.is_active,
            'features': self.get_available_features(),
        }

    # ── Нумератор ──

    def assign_code(self, numerator_prefix):
        """
        Присвоить код из нумератора.

        Вызывается при первом сохранении (когда code ещё пуст).

        Args:
            numerator_prefix: str — префикс нумератора ('ДОК', 'ЦЕН', ...)
        """
        if not self.code:
            from documents.models.document_numerator import DocumentNumerator
            self.code = DocumentNumerator.get_next_code(numerator_prefix)

    # ── Абстрактные методы ──

    def register_changes(self):
        """
        Провести документ — создать движения по регистрам.

        Метод должен:
        1. Создать/обновить записи в регистрах (PriceHistory, ...)
        2. Установить self.status = self.Status.POSTED
        3. Вызвать self.save(update_fields=['status'])

        Должен быть обёрнут в transaction.atomic() в подклассе
        или вызываться внутри атомарного контекста.
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать register_changes()'
        )

    def unregister_changes(self):
        """
        Отменить проведение — удалить движения по регистрам.

        Метод должен:
        1. Удалить/деактивировать записи в регистрах
        2. Установить self.status = self.Status.DRAFT
        3. Вызвать self.save(update_fields=['status'])

        Должен быть обёрнут в transaction.atomic() в подклассе
        или вызываться внутри атомарного контекста.
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать unregister_changes()'
        )

    def get_items_related_name(self):
        """
        Имя related_name для строк документа.

        Пример: 'items', 'rows', 'positions'.
        Используется базовыми views для доступа к табличной части.
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать get_items_related_name()'
        )

    # ── Удаление (soft) ──

    @transaction.atomic
    def mark_deleted(self):
        """
        Пометить документ на удаление.

        Если документ проведён — сначала отменить проведение.
        Затем установить статус DELETED.
        Идемпотентен: повторный вызов не делает ничего.

        Само физическое удаление из БД делается отдельно
        (админ-действие, cron, команда управления).
        """
        # Блокируем строку и получаем актуальное состояние
        self.__class__.objects.select_for_update().get(pk=self.pk)
        self.refresh_from_db()

        if self.status == self.Status.DELETED:
            return  # уже удалён — идемпотентно

        if self.status == self.Status.POSTED:
            self.unregister_changes()
            # unregister_changes должен был установить status=DRAFT
            self.refresh_from_db()
            if self.status != self.Status.DRAFT:
                raise RuntimeError(
                    f'{self.__class__.__name__}.unregister_changes() '
                    f'не установил status=DRAFT (текущий: {self.status})'
                )

        self.status = self.Status.DELETED
        self.is_active = False
        self.save(update_fields=['status', 'is_active', 'updated_at'])

    # ── Печать и экспорт ──

    def get_print_data(self):
        """
        Данные для печатной формы.

        Возвращает dict с переменными для шаблона печати.
        Подкласс переопределяет под свою структуру.

        Returns:
            dict — переменные для рендеринга печатной формы
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать get_print_data()'
        )

    def get_print_html(self):
        """
        HTML печатной формы.

        Рендерит шаблон на основе get_print_data().
        Подкласс переопределяет: использует Django-шаблон
        или собирает HTML руками.

        Returns:
            str — готовый HTML для отображения/печати
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать get_print_html()'
        )

    def export_word(self):
        """
        Экспорт документа в Word (.docx).

        Подкласс переопределяет: генерирует .docx через python-docx
        или аналогичную библиотеку.

        Returns:
            bytes — содержимое .docx-файла
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать export_word()'
        )

    def export_excel(self):
        """
        Экспорт табличной части в Excel (.xlsx).

        Подкласс переопределяет: генерирует .xlsx через openpyxl
        или xlsxwriter.

        Returns:
            bytes — содержимое .xlsx-файла
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать export_excel()'
        )

    def export_pdf(self):
        """
        Экспорт документа в PDF.

        Подкласс переопределяет: генерирует PDF из HTML (WeasyPrint / wkhtmltopdf)
        или через ReportLab.

        Returns:
            bytes — содержимое .pdf-файла
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать export_pdf()'
        )

    def import_from_file(self, uploaded_file):
        """
        Импорт данных в этот документ из файла.

        Подкласс переопределяет: читает Excel/CSV, создаёт строки
        привязанные к self (этому документу).

        Args:
            uploaded_file: InMemoryUploadedFile — загруженный файл

        Returns:
            dict — {'created': N, 'updated': N, 'errors': [...]}
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} должен реализовать import_from_file()'
        )

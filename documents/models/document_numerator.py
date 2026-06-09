# documents/models/document_numerator.py
"""
DocumentNumerator — универсальный нумератор документов.

Обеспечивает сквозную нумерацию с префиксом и опциональным
сбросом счётчика ежегодно / ежемесячно.

Формат кода: {prefix}-{номер}, например: ДОК-000042

Использование:
    code = DocumentNumerator.get_next_code('ДОК')
    # → 'ДОК-000042'

Принцип: атомарный инкремент через F() expression.
"""
from django.db import models, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _


class DocumentNumerator(models.Model):
    """
    Универсальный нумератор.

    Одна запись = один префикс (+ опционально год/месяц).
    При вызове get_next_code() счётчик атомарно увеличивается.

    Поля:
        prefix     — буквенный префикс кода ('ДОК', 'ЦЕН', 'ЗАП', ...)
        counter    — текущее значение счётчика
        year       — год (если указан — счётчик свой для каждого года)
        month      — месяц (если указан — счётчик свой для каждого месяца)
        pad_length — ширина числовой части (по умолчанию 6 → 000042)
    """

    prefix = models.CharField(
        max_length=10,
        verbose_name=_('Префикс'),
        help_text=_('Буквенная часть кода: ДОК, ЦЕН, ЗАП, ...'),
    )
    counter = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Счётчик'),
        help_text=_('Текущее значение (увеличивается автоматически)'),
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Год'),
        help_text=_('Если указан — нумерация своя для каждого года'),
    )
    month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Месяц'),
        help_text=_('Если указан — нумерация своя для каждого месяца'),
    )
    pad_length = models.PositiveSmallIntegerField(
        default=6,
        verbose_name=_('Ширина номера'),
        help_text=_('До какой длины дополнить номер нулями'),
    )

    class Meta:
        verbose_name = _('Нумератор документов')
        verbose_name_plural = _('Нумераторы документов')
        unique_together = [('prefix', 'year', 'month')]
        indexes = [
            models.Index(fields=['prefix', 'year', 'month']),
        ]

    def __str__(self):
        parts = [self.prefix]
        if self.year:
            parts.append(str(self.year))
        if self.month:
            parts.append(f'{self.month:02d}')
        parts.append(str(self.counter))
        return f'{"-".join(parts)} (pad={self.pad_length})'

    # ── API ──

    @classmethod
    @transaction.atomic
    def get_next_code(cls, prefix, year=None, month=None):
        """
        Получить следующий код для заданного префикса.

        Атомарно увеличивает счётчик и возвращает отформатированный код.

        Args:
            prefix: str — префикс ('ДОК', 'ЦЕН', ...)
            year:   int или None — год для yearly-сброса
            month:  int или None — месяц для monthly-сброса

        Returns:
            str — 'ДОК-000042'

        Примеры:
            DocumentNumerator.get_next_code('ДОК')
            DocumentNumerator.get_next_code('ЦЕН', year=2026)
            DocumentNumerator.get_next_code('ЗАП', year=2026, month=6)
        """
        counter, created = cls.objects.select_for_update().get_or_create(
            prefix=prefix,
            year=year,
            month=month,
            defaults={'counter': 0, 'pad_length': 6},
        )

        # Атомарный инкремент
        counter.counter = F('counter') + 1
        counter.save(update_fields=['counter'])
        counter.refresh_from_db(fields=['counter'])

        # Форматирование
        number = str(counter.counter).zfill(counter.pad_length)
        return f'{prefix}-{number}'

    @classmethod
    def peek_next_code(cls, prefix, year=None, month=None):
        """
        Посмотреть следующий код БЕЗ инкремента.

        Полезно для preview.
        """
        try:
            counter = cls.objects.get(prefix=prefix, year=year, month=month)
            number = str(counter.counter + 1).zfill(counter.pad_length)
        except cls.DoesNotExist:
            number = '1'.zfill(6)
        return f'{prefix}-{number}'

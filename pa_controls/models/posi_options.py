# pa_controls/models/posi_options.py
"""
Справочники опций позиционера.

ActingType          — тип действия: Линейный или Ротационный
LeverOption         — длина и тип рычага
SmartCapabilityOption — возможности смарт-позиционера (диагностика, HART, LCD...)

Сигнал тревоги — не отдельный справочник: он описывается профилем сигналов
(params.ControlUnitSignalProfile, роль «Вых. Авария»).

SMART_CAPABILITY_SEED — стартовое наполнение справочника возможностей
(по Tissin TS700, Emerson Fisher FIELDVUE DVC6200, Siemens SIPART PS2).
Разворачивается data-миграцией после создания таблиц.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin


class ActingType(models.Model):
    """Тип действия позиционера: линейный или ротационный.

    Справочник опций. Использование:
      - PosiModelLine через PosiActingTypeOption (разрешённые типы серии, encoding);
      - PosiModelLineItem.acting_type — выбранное значение для модели.

    Стартовые записи (data-миграция): LINEAR «Линейный», ROTARY «Ротационный».
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Например: «Линейный», «Ротационный»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например LINEAR / ROTARY")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к типу действия")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок сортировки в списке")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Тип действия позиционера")
        verbose_name_plural = _("Типы действия позиционеров")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class LeverOption(models.Model):
    """Рычаг позиционера: тип (линейный/ротационный) + диапазон хода штока.

    Справочник опций. Использование:
      - PosiModelLine через PosiLeverOption (разрешённые рычаги серии, encoding);
      - PosiModelLineItem.lever — выбранный рычаг для модели.

    acting_type — тип позиционера (линейный или ротационный).
    stroke_min_mm / stroke_max_mm — мин. и макс. ход штока в миллиметрах
    (у ротационных может быть пустой, например NAMUR или вилочковый M6).

    Стартовые записи: Линейный 10~80, Линейный 40~/70~/100~,
    Вращающийся M6×39L (Вилочковый), Вращающийся NAMUR.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Рычаг 100 мм, прямой»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например LEVER-100-STRAIGHT")
    )
    acting_type = models.ForeignKey(
        ActingType,
        on_delete=models.PROTECT,
        related_name='lever_options',
        verbose_name=_("Тип позиционера"),
        help_text=_("Линейный или ротационный")
    )
    stroke_min_mm = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("Мин. ход штока, мм"),
        help_text=_("Минимальный ход штока в миллиметрах (только для линейного типа)")
    )
    stroke_max_mm = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("Макс. ход штока, мм"),
        help_text=_("Максимальный ход штока в миллиметрах (только для линейного типа)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Тип рычага и примечания")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок сортировки в списке")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Рычаг позиционера")
        verbose_name_plural = _("Рычаги позиционеров")
        ordering = ['acting_type', 'stroke_min_mm', 'sorting_order', 'code']

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация: мин./макс. ход штока задаётся только для линейного типа."""
        from django.core.exceptions import ValidationError

        if self.acting_type_id and self.acting_type.code != 'LINEAR':
            errors = {}
            if self.stroke_min_mm is not None:
                errors['stroke_min_mm'] = _('Ход штока имеет смысл только для линейного типа.')
            if self.stroke_max_mm is not None:
                errors['stroke_max_mm'] = _('Ход штока имеет смысл только для линейного типа.')
            if errors:
                raise ValidationError(errors)
        super().clean()


class SmartCapabilityOption(models.Model):
    """Возможность смарт-позиционера: диагностика, HART, LCD, автонастройка и т.д.

    Единый справочник возможностей — наборы (SmartCapabilitySet) собираются из
    этих записей и привязываются к серии/модели через FK smart_capability_set.

    Вывод всегда сортируется по sorting_order, code. Специальная запись
    «Нет смарт возможностей» (code=NONE) выражает отсутствие возможностей.

    Наполнение (SMART_CAPABILITY_SEED) собрано по Tissin TS700,
    Emerson Fisher FIELDVUE DVC6200 и Siemens SIPART PS2.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Автокалибровка», «HART-коммуникация», «LCD-дисплей»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код, например AUTO-CALIBRATION / HART-COMM")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Примечания к возможности")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок сортировки в списке")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли в списках выбора")
    )

    class Meta:
        verbose_name = _("Возможность смарт-позиционера")
        verbose_name_plural = _("Возможности смарт-позиционеров")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name


class SmartCapabilitySet(CopyMixin, models.Model):
    """Набор смарт-возможностей.

    Серия (PosiModelLine.smart_capability_set) и модель
    (PosiModelLineItem.smart_capability_set) привязывают готовый набор —
    так проще редактировать и сравнивать составы. У модели набор не обязателен:
    если не задан, наследуется от серии (см. PosiModelLineItem.get_smart_capability_set).

    Отдельный набор «Нет смарт возможностей» (SMART-NONE, только запись NONE)
    выражает явное отсутствие возможностей — вместо пустого набора.

    capabilities — M2M на SmartCapabilityOption; get_capabilities() возвращает
    отсортированный список.

    Стартовые наборы (SMART_CAPABILITY_SET_SEED): SMART-NONE, TISSIN-TS700,
    SIEMENS-PS2, EMERSON-DVC6200.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Например: «Смарт (полный)», «Базовый», «Нет смарт возможностей»")
    )
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код набора, например SMART-FULL / SMART-NONE")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Состав набора и примечания")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Сортировка"),
        help_text=_("Порядок сортировки наборов в списке")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активно"),
        help_text=_("Показывать ли набор в списках выбора")
    )
    capabilities = models.ManyToManyField(
        SmartCapabilityOption,
        blank=True,
        related_name='capability_sets',
        verbose_name=_("Возможности")
    )

    class Meta:
        verbose_name = _("Набор смарт-возможностей")
        verbose_name_plural = _("Наборы смарт-возможностей")
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name

    def get_capabilities(self):
        """Возможности набора, отсортированные по sorting_order, code."""
        return self.capabilities.order_by('sorting_order', 'code')


# ── Стартовое наполнение справочника возможностей ──
# Источники: Tissin TS700, Emerson Fisher FIELDVUE DVC6200, Siemens SIPART PS2.
SMART_CAPABILITY_SEED = [
    {
        'code': 'NONE',
        'name': 'Нет смарт возможностей',
        'description': 'Специальная запись: позиционер без смарт-возможностей.',
        'sorting_order': 0,
    },
    {
        'code': 'AUTO-CALIBRATION',
        'name': 'Автокалибровка',
        'description': 'Автоматическая настройка: нулевая точка, пределы хода, '
                       'чувствительность и время отклика без ручной регулировки '
                       '(инициализация, автонастройка хода).',
        'sorting_order': 10,
    },
    {
        'code': 'PST',
        'name': 'Тест частичного хода (PST)',
        'description': 'Периодическая проверка подвижности отсечных/ESD-клапанов '
                       'в узком диапазоне без остановки технологического процесса.',
        'sorting_order': 20,
    },
    {
        'code': 'SELF-DIAGNOSTICS',
        'name': 'Встроенная самодиагностика',
        'description': 'Встроенная проверка собственного состояния устройства.',
        'sorting_order': 30,
    },
    {
        'code': 'PERFORMANCE-MONITORING',
        'name': 'Онлайн-мониторинг производительности',
        'description': 'Непрерывный мониторинг работы клапана в реальном времени: '
                       'сигнатуры клапана, динамическая зона погрешности, ступенчатый отклик, '
                       'проверка хода (Performance Diagnostics).',
        'sorting_order': 40,
    },
    {
        'code': 'DIAGNOSTIC-VALUES',
        'name': 'Диагностические значения с трендами',
        'description': 'Регистрация трендов и гистограмм, контроль утечек и изменения трения, '
                       'предиктивное обслуживание (Diagnostics Values).',
        'sorting_order': 50,
    },
    {
        'code': 'PC-CONFIG-SOFTWARE',
        'name': 'ПО для настройки и диагностики',
        'description': 'Программное обеспечение для глубокой настройки, калибровки и сбора '
                       'диагностики (ValveLink, SIMATIC PDM).',
        'sorting_order': 60,
    },
    {
        'code': 'HART-COMM',
        'name': 'HART-коммуникация',
        'description': 'Двухпроводная связь по протоколу HART для удалённой настройки, '
                       'мониторинга и доступа к диагностике из сигнальной петли.',
        'sorting_order': 70,
    },
    {
        'code': 'FOUNDATION-FIELDBUS',
        'name': 'Foundation Fieldbus',
        'description': 'Поддержка протокола Foundation Fieldbus для интеграции в системы управления.',
        'sorting_order': 80,
    },
    {
        'code': 'PROFIBUS-PA',
        'name': 'Profibus PA',
        'description': 'Поддержка протокола Profibus PA для параметризации и диагностики.',
        'sorting_order': 90,
    },
    {
        'code': 'LCD-DISPLAY',
        'name': 'ЖК-дисплей',
        'description': 'Встроенный локальный экран с кнопками: настройка параметров, '
                       'переключение режимов, чтение ошибок на месте установки.',
        'sorting_order': 100,
    },
    {
        'code': 'FAIL-FREEZE',
        'name': 'Фиксация положения при потере сигнала',
        'description': 'Функция Fail freeze: при потере управляющего сигнала позиционер '
                       'удерживает последнее положение.',
        'sorting_order': 110,
    },
    {
        'code': 'ZERO-AIR-STANDBY',
        'name': 'Нулевой расход воздуха в ожидании',
        'description': 'Нулевое потребление воздуха в режиме ожидания.',
        'sorting_order': 120,
    },
    {
        'code': 'EXTERNAL-EXHAUST',
        'name': 'Внешний выхлоп воздуха',
        'description': 'Защита платы от коррозии за счёт внешнего выхлопа воздуха.',
        'sorting_order': 130,
    },
    {
        'code': 'AIR-FILTER',
        'name': 'Встроенный воздушный фильтр',
        'description': 'Встроенный фильтр (5 мкм) для защиты пьезоклапана.',
        'sorting_order': 140,
    },
    {
        'code': 'VIBRATION-RESISTANT',
        'name': 'Вибро-/ударостойкость',
        'description': 'Повышенная стойкость к вибрации и ударным воздействиям.',
        'sorting_order': 150,
    },
    {
        'code': 'LOSS-OF-SIGNAL',
        'name': 'Loss of Signal (LoS)',
        'description': 'Падение или полное исчезновение управляющего сигнала (например, ниже 3.6 мА).',
        'sorting_order': 160,
    },
    {
        'code': 'LOSS-OF-POWER',
        'name': 'Loss of Power (LoP)',
        'description': 'Отключение основного питания (актуально для четырехпроводных схем '
                       'или позиционеров с шинной организацией вроде Fieldbus).',
        'sorting_order': 170,
    },
    {
        'code': 'LOSS-OF-AIR',
        'name': 'Loss of Air (LoA)',
        'description': 'Падение давления питания сжатого воздуха ниже критического уровня '
                       '(контролируется встроенным датчиком давления).',
        'sorting_order': 180,
    },
    {
        'code': 'INTERNAL-FAULT',
        'name': 'Internal Fault',
        'description': 'Внутренний сбой самого позиционера (ошибка процессора, '
                       'заклинивание внутреннего пилотного клапана).',
        'sorting_order': 190,
    },
]

# ── Стартовые наборы смарт-возможностей ──
# capabilities — коды из SMART_CAPABILITY_SEED.
SMART_CAPABILITY_SET_SEED = [
    {
        'code': 'SMART-NONE',
        'name': 'Нет смарт возможностей',
        'description': 'Пустой набор: позиционер без смарт-возможностей.',
        'sorting_order': 0,
        'capabilities': ['NONE'],
    },
    {
        'code': 'TISSIN-TS700',
        'name': 'Tissin TS700',
        'description': 'Набор возможностей смарт-позиционера Tissin TS700.',
        'sorting_order': 10,
        'capabilities': [
            'AUTO-CALIBRATION',
            'PST',
            'SELF-DIAGNOSTICS',
            'LCD-DISPLAY',
            'FAIL-FREEZE',
            'ZERO-AIR-STANDBY',
            'EXTERNAL-EXHAUST',
            'AIR-FILTER',
            'VIBRATION-RESISTANT',
        ],
    },
    {
        'code': 'SIEMENS-PS2',
        'name': 'Siemens SIPART PS2',
        'description': 'Набор возможностей смарт-позиционера Siemens SIPART PS2.',
        'sorting_order': 20,
        'capabilities': [
            'AUTO-CALIBRATION',
            'DIAGNOSTIC-VALUES',
            'PC-CONFIG-SOFTWARE',
            'HART-COMM',
            'PROFIBUS-PA',
            'FOUNDATION-FIELDBUS',
            'PST',
            'LCD-DISPLAY',
        ],
    },
    {
        'code': 'EMERSON-DVC6200',
        'name': 'Emerson FIELDVUE DVC6200',
        'description': 'Набор возможностей цифрового контроллера Emerson Fisher FIELDVUE DVC6200.',
        'sorting_order': 30,
        'capabilities': [
            'AUTO-CALIBRATION',
            'PERFORMANCE-MONITORING',
            'PC-CONFIG-SOFTWARE',
            'PST',
            'HART-COMM',
            'FOUNDATION-FIELDBUS',
            'LCD-DISPLAY',
        ],
    },
]

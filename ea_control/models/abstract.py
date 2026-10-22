# ea_control/models/abstract.py
"""
Абстрактные модели паттерна «узлы, слоты, матрицы, правила» (slots.md).

Отлаживаются на блоке управления ЭП (приложение ea_control), затем переезжают
в ``core`` и становятся базой для наследников в других приложениях.

Соглашение об именах (slots.md): суффикс роли в паттерне — ``Node``, ``Slot``,
``Option``, ``MatrixEntry``, ``Rule``, ``Snapshot``; физические модели — без
суффикса.

Правила наследования:

- Абстрактные модели объявляют **только скалярные поля и общую логику**
  (методы, TextChoices). Связные поля (FK/M2M на конкретные справочники,
  скоуп, контекст) объявляет наследник — физика у каждой предметной области
  своя (slots.md, Decision Log №4: типизированные FK + kind).
- i18n-поля (``name_i18n``/``description_i18n``) наследник получает миксином
  ``core.models.mixins.LocalizedDictFieldsMixin`` (как EaSignalSlot) —
  абстрактная база объявляет только ru-поля ``name``/``description``
  (рабочий язык админки; i18n — для локализации сайта: названий, текстов,
  фильтров).
- ``kind`` и ``when_operator`` объявлены без жёстких choices (или с
  отладочным словарём): конкретные значения задаёт наследник переопределением
  поля или финальным словарём при переносе в core.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin
from core.utils.localization import localize_service_word


# ── Общие словари (TextChoices) ─────────────────────────────────────────────

class ConfigSelectionMode(models.TextChoices):
    """Семантика выбора в слоте."""
    SINGLE = 'single', _('Одиночный выбор')
    MULTI = 'multi', _('Мультивыбор')
    XOR = 'xor', _('Взаимоисключающий (одна опция из набора)')
    BUNDLE = 'bundle', _('Пакет (атомарный набор строк с общим кодом)')


class ConfigSlotKind(models.TextChoices):
    """Род значения слота (slots.md, глоссарий)."""
    VALUE = 'value', _('Значение')
    OBJECT = 'object', _('Объект (типизированный FK на физическую модель)')
    SUBTYPE = 'subtype', _('Подтип оборудования (EquipmentType)')


class ConfigAvailability(models.TextChoices):
    """Доступность опции в матрице (Паттерн А)."""
    STD = 'std', _('Стандарт')
    OPT = 'opt', _('Опция')
    NA = 'na', _('Недоступно')


class ConfigRuleAction(models.TextChoices):
    """Действие правила динамики (Паттерн В)."""
    SHOW = 'show', _('Показать')
    HIDE = 'hide', _('Скрыть')
    BLOCK = 'block', _('Заблокировать')
    REQUIRE = 'require', _('Сделать обязательным')
    SET_DEFAULT = 'set_default', _('Выставить по умолчанию')


class ConfigRuleOperator(models.TextChoices):
    """Оператор сравнения when-условия (отладочный словарь).

    Финальный словарь выравнивается с семантикой фильтров/требований:
    ``core.FilterDefinition.FilterType`` (exact/icontains/gte/lte…) и
    ``configurator.ParameterRule.match_type`` (exact/hierarchy/compatible…).
    """
    EXACT = 'exact', _('Равно')
    NOT_EXACT = 'not_exact', _('Не равно')
    CONTAINS = 'icontains', _('Содержит')
    GTE = 'gte', _('Не меньше')
    LTE = 'lte', _('Не больше')
    IN = 'in', _('В списке')
    NOT_IN = 'not_in', _('Не в списке')
    IS_SET = 'is_set', _('Значение задано')


# ── Узел ─────────────────────────────────────────────────────────────────────

class AbstractConfigNode(CopyMixin, models.Model):
    """Узел-секция — группировка слотов в дерево конфигурации (роль ``Node``).

    Место в схеме: дерево секций конфигуратора, например БУ → «Сигналы
    управления» → слоты LOCAL_CONTROL/CMD/SETPOINT. Узлы вкладываются друг
    в друга через ``parent`` и образуют структуру, по которой фронт рисует
    разделы конфигуратора. Узел не хранит данные конфигурации — только
    декларирует структуру: слоты крепятся к нему полем ``section`` у
    наследника слота.

    Поля:

    - ``code`` — системный уникальный код узла (не локализуется);
    - ``name`` — ru-название секции (админка); переводы — ``name_i18n`` у
      наследника (LocalizedDictFieldsMixin);
    - ``parent`` — self-FK: вложенность узлов (null — корневой);
    - ``description`` — пояснение секции;
    - ``sorting_order`` — порядок отрисовки;
    - ``is_active`` — выключенный узел скрыт из конфигуратора.

    Наследник должен:

    - добавить LocalizedDictFieldsMixin (i18n) и задать Meta.verbose_name.

    Наследник может:

    - переопределить ``ordering``; добавить обратные связи на слоты
      (``related_name='slots'``).
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код узла, например «CONTROL_SIGNALS»"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Название"),
        help_text=_("Название секции, например «Сигналы управления»"),
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children',
        verbose_name=_("Родительский узел"),
        help_text=_("Вложенность: узлы образуют дерево секций конфигуратора"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        abstract = True
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name or self.code


# ── Слот ─────────────────────────────────────────────────────────────────────

class AbstractConfigSlot(CopyMixin, models.Model):
    """Слот — точка конфигурации изделия (роль ``Slot``); обобщение EaSignalSlot.

    Место в схеме: лист дерева конфигуратора; декларирует «розетку», в
    которую выбирается опция. Слот не хранит выбранное значение — только тип
    точки (``slot_kind``) и правила выбора (``selection_mode``, ``required``).
    Выбранные значения живут в снимке (``AbstractConfigSnapshot``); доступные
    опции — в матрице (``AbstractSlotMatrixEntry``).

    Поля:

    - ``code`` — системный уникальный код слота (ключ в config_snapshot);
    - ``name`` — ru-название группы (админка); i18n — у наследника;
    - ``selection_mode`` — single (одна опция) | multi (несколько, напр. CMD)
      | xor (одна из взаимоисключающих) | bundle (атомарный пакет строк
      матрицы с общим bundle-кодом);
    - ``slot_kind`` — value (простое значение) | object (типизированный FK
      опции на физическую модель) | subtype (подтип оборудования
      EquipmentType; в БУ-отладке не используется — slots.md «Решение:
      граница»);
    - ``required`` — в слоте должна быть хотя бы одна доступная опция;
    - ``description``/``sorting_order``/``is_active`` — как у узла.

    Наследник должен:

    - объявить связное поле ``section`` (FK на свой узел-секцию) — без него
      слот не попадает в дерево;
    - добавить LocalizedDictFieldsMixin (i18n).

    Наследник может:

    - переопределить ``ordering``; добавить свои связи.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код слота, например «POSITION_FEEDBACK»"),
    )
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Название группы, например «Позиционная обратная связь»"),
    )
    selection_mode = models.CharField(
        max_length=10, choices=ConfigSelectionMode.choices,
        default=ConfigSelectionMode.SINGLE,
        verbose_name=_("Режим выбора"),
        help_text=_("single — одна опция; multi — несколько (CMD); xor — одна "
                    "из взаимоисключающих; bundle — атомарный пакет строк "
                    "матрицы с общим bundle-кодом"),
    )
    slot_kind = models.CharField(
        max_length=10, choices=ConfigSlotKind.choices,
        default=ConfigSlotKind.VALUE,
        verbose_name=_("Род значения"),
        help_text=_("value — простое значение; object — ссылка на физическую "
                    "модель (типизированный FK опции); subtype — подтип "
                    "оборудования (EquipmentType)"),
    )
    required = models.BooleanField(
        default=False,
        verbose_name=_("Обязательный"),
        help_text=_("В слоте должна быть хотя бы одна доступная опция"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        abstract = True
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name or self.code


# ── Опция ────────────────────────────────────────────────────────────────────

class AbstractSlotOption(CopyMixin, models.Model):
    """Опция — вариант заполнения слота (роль ``Option``); обобщение EaSlotOption.

    Место в схеме: справочник возможных значений слота. Опция не хранит
    доступность (где и когда она выбирается) — это строки матрицы
    (``AbstractSlotMatrixEntry``). Опция описывает «что это за вариант»:
    имя, код позиции артикула и ссылку на физическую сущность по ``kind``.

    Поля:

    - ``code`` — системный уникальный код опции;
    - ``kind`` — тип опции; объявлен без choices: наследник переопределяет
      поле своими значениями (у ЭП: signal/heater/none/pair; у БУ — свои);
    - ``name`` — ru-имя (для none-строк и особых случаев); i18n — у
      наследника;
    - ``encoding``/``ext_encoding`` — справочные вклады опции в основной/
      расширенный артикул (опция «сама себя кодирует»); фактические коды в
      точке конфигурации могут переопределяться строками матрицы
      (AbstractSlotMatrixEntry.encoding/ext_encoding) — приоритет матрицы;
    - ``description``/``sorting_order``/``is_active`` — как у узла.

    Наследник должен:

    - объявить ``slot`` (FK на свой слот);
    - объявить типизированные FK-полезные нагрузки по ``kind`` (у БУ:
      control_signal → CuControlSignal, feedback_signal → CuFeedbackSignal,
      protocol → CuCommProtocol, heater_supply → CuHeaterSupply,
      device → CuFeedbackDevice, control_unit → ControlUnit,
      signal_power/logic/signal_type → свои справочники);
    - переопределить ``kind`` своими choices и добавить валидацию (clean):
      ровно одна полезная нагрузка на kind (образец: EaSlotOption.clean).

    Наследник может:

    - добавить LocalizedDictFieldsMixin (i18n) и собственные поля.
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Код"),
        help_text=_("Уникальный код опции, например «END_SPDT», «BLINKER»"),
    )
    kind = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name=_("Тип опции"),
        help_text=_("Конкретные значения задаёт наследник переопределением "
                    "поля (у ЭП: signal/heater/none/pair; у БУ — свои)"),
    )
    name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Название"),
        help_text=_("Имя опции (для none-строк и особых случаев)"),
    )
    encoding = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name=_("Кодировка"),
        help_text=_("Справочный вклад опции в основной артикул; "
                    "переопределяется строкой матрицы"),
    )
    ext_encoding = models.CharField(
        max_length=10, blank=True, default='',
        verbose_name=_("Ext-код"),
        help_text=_("Код позиции расширенного кода заказа; пусто — позиция "
                    "не кодируется; переопределяется строкой матрицы"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        abstract = True
        ordering = ['sorting_order', 'code']

    def __str__(self):
        return self.name or self.code


# ── Матрица ──────────────────────────────────────────────────────────────────

class AbstractSlotMatrixEntry(CopyMixin, models.Model):
    """Строка матрицы доступности (Паттерн А); обобщение EaSignalMatrixEntry.

    Место в схеме: источник ответа «доступна ли опция X в точке Y». Точка Y —
    контекст строки (скоуп + координаты), который объявляет наследник. Строка
    декларирует: какая опция, в каком слоте, с какой доступностью
    (std/opt/na), предвыбор (is_default), атомарность (bundle), парные
    запреты (conflicts) и вклад в артикул (encoding/ext_encoding). Строки с
    пустым скоупом — профиль шаблона (дефолты типа БУ).

    Поля:

    - ``availability`` — std (стандарт) | opt (опция) | na (запрет
      унаследованной строки на специфичном уровне);
    - ``is_default`` — предвыбор в слоте; std-строки всегда предвыбраны
      (реализовано в save());
    - ``bundle`` — код пакета: строки с общим кодом выбираются атомарно
      (MWG = три строки в трёх слотах); если хоть одна недоступна — пакет
      недоступен целиком;
    - ``conflicts`` — симметричный M2M-self: парный запрет одновременного
      выбора (составные запреты — правилами/clean наследника);
    - ``encoding``/``ext_encoding`` — вклад в основной/ext артикул;
    - ``name``/``description`` — для none-строк («Без переключателей») и
      особых случаев; иначе имя выводится из полезной нагрузки;
    - ``sorting_order`` — порядок строк в слоте.

    Методы:

    - ``save()`` — std → is_default=True;
    - ``localized_name(locale)`` — имя + суффикс «(Стандарт)/(Опция)»;
    - ``_base_name(locale)`` — хук имени: наследник переопределяет, чтобы
      выводить имя из своей полезной нагрузки (сигнал/устройство/слот).

    Наследник должен:

    - объявить ``slot`` (FK на свой слот) и ``option`` (FK на свою опцию);
    - объявить контекст: скоуп (brand/model_line/body/model_line_item —
      ровно один или все пустые для профильных строк) и координаты
      (control_unit/power_supply/mode);
    - объявить типизированные полезные нагрузки строки (сигнал/протокол/
      обогрев/устройство/БУ) и валидацию clean + CheckConstraint «один
      скоуп» (образец: EaSignalMatrixEntry).

    Наследник может:

    - переопределить ``_base_name``/``clean``; добавить свои
      constraints/индексы.
    """
    availability = models.CharField(
        max_length=10, choices=ConfigAvailability.choices,
        default=ConfigAvailability.OPT,
        verbose_name=_("Доступность"),
        help_text=_("std — стандарт, opt — опция, na — запрет унаследованной "
                    "строки"),
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Предвыбор в слоте (std-строки всегда предвыбраны)"),
    )
    bundle = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Пакет"),
        help_text=_("Код пакета: строки с общим bundle выбираются атомарно"),
    )
    conflicts = models.ManyToManyField(
        'self', blank=True, symmetrical=True,
        verbose_name=_("Конфликты"),
        help_text=_("Парный запрет одновременного выбора"),
    )
    encoding = models.CharField(
        max_length=50, blank=True, verbose_name=_("Кодировка"),
        help_text=_("Вклад в основной артикул"),
    )
    ext_encoding = models.CharField(
        max_length=50, blank=True, verbose_name=_("Расширенная кодировка"),
        help_text=_("Вклад в ext-часть артикула (позиция кода заказа)"),
    )
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    name = models.CharField(
        max_length=200, blank=True, verbose_name=_("Название"),
        help_text=_("Для none-строк и особых случаев; иначе имя выводится из "
                    "полезной нагрузки"),
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    class Meta:
        abstract = True
        ordering = ['sorting_order', 'id']

    def __str__(self):
        return self.name or self.localized_name()

    def save(self, *args, **kwargs):
        """std-строки всегда помечаются предвыбором (is_default=True)."""
        if self.availability == ConfigAvailability.STD:
            self.is_default = True
        super().save(*args, **kwargs)

    def _base_name(self, locale=None):
        """Базовое имя строки; наследник уточняет (сигнал/устройство/слот)."""
        slot = getattr(self, 'slot', None)
        return self.name or (str(slot) if slot else f'#{self.pk or "?"}')

    def localized_name(self, locale=None):
        """Имя + суффикс (Стандарт)/(Опция) — на лету, локализованный."""
        base = self._base_name(locale)
        if self.availability == ConfigAvailability.STD:
            return f'{base} {localize_service_word("(Стандарт)", locale)}'
        if self.availability == ConfigAvailability.OPT:
            return f'{base} {localize_service_word("(Опция)", locale)}'
        return base


# ── Правило ──────────────────────────────────────────────────────────────────

class AbstractSlotRule(CopyMixin, models.Model):
    """Правило динамики конфигуратора (Паттерн В) — событийный UI.

    Место в схеме: плоская логика «если значение слота-условия [оператор]
    значение → применить действие к слоту-цели». Отвечает на «как меняется
    доступность/обязательность полей при выборе опции». В отличие от матрицы
    (Паттерн А — статичная доступность по контексту) правило срабатывает на
    выбранное значение. Хардкод-логика резолвера (ЭП: профиль БУ → слоты,
    HART ↔ SETPOINT, MWG-пакеты) заменяется декларативными правилами.

    Поля:

    - ``when_operator`` — оператор сравнения значения when-слота; отладочный
      словарь ConfigRuleOperator (exact/icontains/gte/lte/in/not_in/is_set),
      финальный выравнивается с FilterType/ParameterRule.match_type;
    - ``when_value`` — JSON-значение для сравнения (строка/число/список);
    - ``action`` — show | hide | block | require | set_default для
      target-слота;
    - ``action_value`` — JSON-значение действия (для set_default — что
      выставить слоту-цели: код опции/значение);
    - ``priority`` — больше — раньше; при конфликте правил побеждает
      больший;
    - ``is_active`` — выключенное правило не применяется;
    - ``description`` — пояснение.

    Наследник должен:

    - объявить ``when_slot`` (FK на свой слот-условие) и ``target_slot``
      (FK на свой слот-действие).

    Наследник может:

    - переопределить ``when_operator`` словарём домена; добавить связь на
      конкретную опцию-условие (когда условие — конкретная опция, а не
      значение слота); реализовать ``evaluate(current_value) -> bool`` с
      семантикой домена.
    """
    when_operator = models.CharField(
        max_length=20, blank=True, default=ConfigRuleOperator.EXACT,
        verbose_name=_("Оператор"),
        help_text=_("Оператор сравнения значения when-слота"),
    )
    when_value = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Значение условия"),
        help_text=_("JSON-значение для сравнения (строка/число/список)"),
    )
    action_value = models.JSONField(
        null=True, blank=True,
        verbose_name=_("Значение действия"),
        help_text=_("Для action=set_default — значение, выставляемое "
                    "слоту-цели (код опции/значение); для остальных действий "
                    "не используется"),
    )
    action = models.CharField(
        max_length=20, choices=ConfigRuleAction.choices,
        verbose_name=_("Действие"),
        help_text=_("show/hide/block/require/set_default для target-слота"),
    )
    priority = models.IntegerField(
        default=0,
        verbose_name=_("Приоритет"),
        help_text=_("Больше — раньше; при конфликте правил побеждает больший"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))

    class Meta:
        abstract = True
        ordering = ['-priority', 'id']

    def __str__(self):
        return f'#{self.pk or "?"}: {self.action}'


# ── Снимок ───────────────────────────────────────────────────────────────────

class AbstractConfigSnapshot(CopyMixin, models.Model):
    """Снимок выбора конфигурации (роль ``Snapshot``) — портируемый результат.

    Место в схеме: материализованный плоский JSON {slot_code: value}
    выбранной конфигурации (slots.md §4 «Контракт транзакций»). Источник
    истины — связи носителя (M2M matrix_rows / отдельные FK); снимок —
    портируемая копия + гарантия обратной совместимости: новые слоты не
    требуют регенерации старых инстансов (apply_defaults подставляет
    дефолты профиля).

    Поля:

    - ``config_snapshot`` — JSONField {slot_code: value}; значения — коды
      опций или ссылки (id/код) на объектные опции.

    Методы:

    - ``set_option``/``get_option`` — запись/чтение (запись не сохраняет —
      вызвать save());
    - ``apply_defaults(defaults)`` — дополняет отсутствующие ключи
      дефолтами профиля, существующие не перетирает;
    - ``full_code(parts)`` — отладочная склейка вкладов
      ({'encoding','ext_encoding'}) в артикул; боевая версия — сервис
      (ea_ext_code), здесь — простейшая для отладки паттерна.

    Наследник должен:

    - (по необходимости) объявить связи-источники истины (M2M на строки
      матрицы) и переопределить сохранение снимка при их изменении.

    Наследник может:

    - переопределить ``full_code`` / добавить свою сборку артикула.
    """
    config_snapshot = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Снимок конфигурации"),
        help_text=_("Плоские пары {slot_code: value}; дефолты подставляются "
                    "из профиля для отсутствующих ключей"),
    )

    class Meta:
        abstract = True

    def set_option(self, slot_code, value):
        """Записать значение слота в снимок (не сохраняет — вызвать save())."""
        self.config_snapshot[slot_code] = value

    def get_option(self, slot_code, default=None):
        return self.config_snapshot.get(slot_code, default)

    def apply_defaults(self, defaults):
        """Дополняет снимок дефолтами для отсутствующих ключей (fallback).

        ``defaults`` — словарь {slot_code: default_value} (профиль шаблона).
        Существующие значения не перетираются.
        """
        for key, value in (defaults or {}).items():
            self.config_snapshot.setdefault(key, value)

    def full_code(self, parts):
        """Склейка вкладов опций в артикул (отладочная версия).

        ``parts`` — итератор словарей {'encoding', 'ext_encoding'}. Итоговый
        артикул в проекте собирает сервис (ea_ext_code); здесь — простейшая
        версия для отладки паттерна.
        """
        base, ext = [], []
        for part in parts or []:
            if not part:
                continue
            if part.get('encoding'):
                base.append(part['encoding'])
            if part.get('ext_encoding'):
                ext.append(part['ext_encoding'])
        return ''.join(base + ext)

"""Локализация контента (ru/en/cn).

Форма хранения — дополнительный JSONField ``<field>_i18n`` рядом с базовым RU-полем:

    title_template       = models.TextField(...)          # RU, рабочее поле (редактируется)
    title_template_i18n  = models.JSONField(default=dict) # {"ru": ..., "en": ..., "cn": ...}

При сохранении ``ru`` синхронизируется в ``_i18n["ru"]``. Чтение — всегда через
``pick_i18n`` (fallback: locale → ru → "").
"""

LOCALES = ("ru", "en", "cn")
DEFAULT_LOCALE = "ru"

# Accept-Language → внутренний код локали (zh, zh-CN, zh-Hans → cn)
_ACCEPT_PREFIXES = (("zh", "cn"), ("en", "en"))


def pick_i18n(i18n, locale=None, fallback=DEFAULT_LOCALE):
    """Вернуть строку для ``locale`` с fallback на ``fallback``, затем ''.

    - ``fallback`` по умолчанию — ключ локали ``'ru'`` (fallback: locale → ru → '').
    - Если ``fallback`` передан значением (не кодом локали), при отсутствии перевода
      возвращается это значение (RU-шаблон/строка).
    - Устойчив к случаю, когда вместо dict пришёл plain-строка (поле ещё не локализовано).
    """
    if not isinstance(i18n, dict):
        return i18n or (fallback if fallback not in LOCALES else "")
    loc = locale or DEFAULT_LOCALE
    for candidate in (loc, fallback):
        value = i18n.get(candidate)
        if value:
            return value
    if fallback not in LOCALES:
        return fallback
    return ""


def sync_ru(i18n, ru_value):
    """Вернуть новый dict с обновлённым ``ru`` (исходный не мутируется)."""
    out = dict(i18n) if isinstance(i18n, dict) else {}
    out["ru"] = ru_value or ""
    return out


def set_locale(i18n, locale, value):
    """Вернуть новый dict с установленным переводом для ``locale`` (исходный не мутируется)."""
    out = dict(i18n) if isinstance(i18n, dict) else {}
    out[locale] = value or ""
    return out


def locale_from_accept_language(header):
    """'Accept-Language' → 'ru' | 'en' | 'cn'."""
    header = (header or "").lower()
    for prefix, locale in _ACCEPT_PREFIXES:
        if header.startswith(prefix):
            return locale
    return DEFAULT_LOCALE


def localized_name(obj, locale=None):
    """Название справочника с переводом: obj.name_i18n[locale] → obj.name.

    Для объектов без ``name_i18n`` (или без перевода) возвращается RU-имя.
    """
    name = getattr(obj, 'name', '') or ''
    i18n = getattr(obj, 'name_i18n', None)
    return pick_i18n(i18n, locale or DEFAULT_LOCALE, fallback=name)


# Служебные RU-слова, вычисляемые в коде (exd_display и т.п.), без _i18n.
_SERVICE_WORDS = {
    'Нет': {'en': 'No', 'cn': '无'},
    'Да': {'en': 'Yes', 'cn': '有'},
    'Не указано': {'en': 'Not specified', 'cn': '未指定'},
    'Общепромышленное': {'en': 'General-purpose', 'cn': '通用'},
}

# Подстроковые замены для не-RU локалей (единицы, соединители).
_SERVICE_REPLACES = (
    ('°С', {'en': '°C', 'cn': '°C'}),
    ('кг', {'en': 'kg', 'cn': 'kg'}),
    (' или ', {'en': ' or ', 'cn': ' 或 '}),
    ('квадрат', {'en': 'square', 'cn': '方'}),
    ('кв.', {'en': 'sq.', 'cn': '方'}),
)


def localize_service_word(value, locale=None):
    """Локализовать служебные RU-слова/единицы; иначе значение как есть."""
    if not isinstance(value, str) or not locale or locale == DEFAULT_LOCALE:
        return value
    word = _SERVICE_WORDS.get(value)
    if word is not None:
        return word.get(locale, value)
    for src, variants in _SERVICE_REPLACES:
        if src in value:
            value = value.replace(src, variants.get(locale, src))
    return value

"""Локализация контента (ru/en/zh).

Форма хранения — дополнительный JSONField ``<field>_i18n`` рядом с базовым RU-полем:

    title_template       = models.TextField(...)          # RU, рабочее поле (редактируется)
    title_template_i18n  = models.JSONField(default=dict) # {"ru": ..., "en": ..., "zh": ...}

При сохранении ``ru`` синхронизируется в ``_i18n["ru"]``. Чтение — всегда через
``pick_i18n`` (fallback: locale → ru → "").
"""

LOCALES = ("ru", "en", "zh")
DEFAULT_LOCALE = "ru"

# Accept-Language → внутренний код локали
_ACCEPT_PREFIXES = (("zh", "zh"), ("en", "en"))


def pick_i18n(i18n, locale=None, fallback=DEFAULT_LOCALE):
    """Вернуть строку для ``locale`` с fallback на ``fallback`` (обычно ru), затем ''.

    Устойчив к случаю, когда вместо dict пришёл plain-строка (поле ещё не локализовано).
    """
    if not isinstance(i18n, dict):
        return i18n or ""
    loc = locale or DEFAULT_LOCALE
    for candidate in (loc, fallback):
        value = i18n.get(candidate)
        if value:
            return value
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
    """'Accept-Language' → 'ru' | 'en' | 'zh'."""
    header = (header or "").lower()
    for prefix, locale in _ACCEPT_PREFIXES:
        if header.startswith(prefix):
            return locale
    return DEFAULT_LOCALE

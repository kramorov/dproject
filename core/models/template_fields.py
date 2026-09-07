# core/models/template_fields.py
"""Типизированная спецификация поля шаблонного реестра.

``TemplateFieldSpec`` описывает один «факт» об объекте каталога и используется
как единый источник правды для:

  * ``_get_data_dict()``      — имя/описание (``path``);
  * ``_get_code_data_dict()`` — артикул (``code_path``, фолбэк ``path``);
  * ``_get_template_vars()``  — плоские значения для API/MCP;
  * ``_get_spec_sections()``  — структурированные характеристики.

Один вариант значения = одна спецификация. Например, у Exd это отдельные ключи
``exd_list``, ``exd_short`` (display) и соответствующий ``code_path`` (encoding).
Состав каждого словаря задаётся списками ключей в модели
(``NAME_FIELD_KEYS``, ``CODE_FIELD_KEYS``, ``VARS_FIELD_KEYS``, ``SPEC_FIELD_KEYS``).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateFieldSpec:
    """Спецификация одного поля шаблона/сериализации."""

    key: str
    placeholder: str = ''

    # Путь к отображаемому значению (атрибутный путь с ``__``/``.``, как в _get_value).
    path: str | None = None
    # Отдельный путь для подстановки в имя/описание (если отличается от display-пути).
    name_path: str | None = None
    # Путь к encoding-значению для шаблона артикула.
    code_path: str | None = None
    # Имя callable-а на модели вместо ``path`` (для сложных значений).
    resolver: str | None = None

    # Метаданные для ``_get_spec_sections()``.
    label: str = ''
    unit: str = ''
    type: str = 'text'
    order: int = 0
    group: str = ''

    @classmethod
    def from_dict(cls, raw):
        """Нормализовать dict в TemplateFieldSpec, давая понятную ошибку."""
        if not isinstance(raw, dict):
            raise TypeError(
                f"ожидается dict, получен {type(raw).__name__}"
            )
        try:
            return cls(**raw)
        except TypeError as e:
            raise ValueError(f"некорректная спецификация: {e}") from e

# core/models/catalog_serializer.py
"""Единый контракт сериализации каталога для API/MCP.

Объединяет общую обвязку ``to_dict()`` / ``to_values_dict()`` и типовые секции
(галерея, характеристики, документация, сертификаты, описание), которые раньше
дублировались в каждой модели каталога (PosiModelLineItem, LimitSwitchBox и т.п.).

Модель, подключающая ``CatalogSerializerMixin``, переопределяет только:

  * ``_get_template_vars()`` — плоский словарь готовых значений для шаблонов и секций;
  * ``_get_spec_sections()`` — список групп характеристик
    ``[{key, title, order, fields: [{key, label, value, unit, type, order}]}]``.

Наследуемый ``CatalogDictMixin.to_values_dict()`` уже умеет извлекать плоские
значения и изображения из ``to_dict()``, поэтому модель больше не должна
переопределять ``to_values_dict()`` (это унифицирует выдачу списков для MCP).
"""

import re
from urllib.parse import quote

from django.apps import apps
from django.core import checks
from django.utils.translation import gettext_lazy as _

from .mixins import CatalogDictMixin
from ..utils.localization import DEFAULT_LOCALE, pick_i18n


# Заголовки секций to_dict() по локалям (вместо gettext — локаль данных из Accept-Language).
_SECTION_TITLES = {
    'ru': {'images': 'Изображения', 'specs': 'Характеристики', 'docs': 'Документация',
           'certs': 'Сертификаты', 'description': 'Описание', 'main': 'Основные', 'article': 'Артикул'},
    'en': {'images': 'Images', 'specs': 'Specifications', 'docs': 'Technical documentation',
           'certs': 'Certificates', 'description': 'Description', 'main': 'General', 'article': 'Article'},
    'cn': {'images': '图片', 'specs': '技术参数', 'docs': '技术文档',
           'certs': '证书', 'description': '描述', 'main': '基本', 'article': '型号'},
}


class CatalogSerializerMixin(CatalogDictMixin):
    """Единый каркас ``to_dict()`` для моделей каталога.

    Каноническая структура ``to_dict()``:

      id, code, name, title, description, is_active, sorting_order,
      model_line, sku, template_vars, sections.

    Порядок секций фиксирован (для стабильной JSON-схемы MCP):
      images=0, specs=1, docs=2, certs=3, description=4.
    """

    # Маркер для system check catalog.E003: модель обязана объявить TEMPLATE_FIELDS.
    requires_template_fields = True

    # ── Хуки, которые переопределяет модель ──

    def _get_template_vars(self, fields=None) -> dict:
        """Плоский словарь готовых значений (единый источник — TEMPLATE_FIELDS).

        ``fields`` — подмножество ключей; иначе — ``VARS_FIELD_KEYS`` (дефолт —
        все поля с ``path``). Значения резолвятся с мемоизацией.
        """
        specs = self._get_field_specs()
        if not specs:
            return {
                placeholder.strip('{}'): self._get_value(path)
                for placeholder, path in self._get_data_dict().items()
            }
        keys = fields if fields is not None else getattr(self, 'VARS_FIELD_KEYS', None)
        selected = self._lookup_specs(keys) if keys is not None else specs
        return {f.key: self._resolve_field(f) for f in selected if f.key}

    def _get_spec_template_from_model_line(self):
        """JSON-шаблон спецификации из серии (model_line)."""
        ml = getattr(self, 'model_line', None)
        if ml is None:
            return None
        return getattr(ml, 'spec_template', None) or None

    def _get_spec_template(self):
        """Итоговый JSON-шаблон спецификации.

        Приоритет: ``model_line.spec_template`` →
        ``EquipmentType.spec_template`` → None (фоллбэк на реестр).
        """
        template = self._get_spec_template_from_model_line()
        if template:
            return template
        getter = getattr(self, '_get_equipment_type_template', None)
        if getter is not None:
            template = getter('spec_template')
            if template:
                return template
        return None

    def _parse_spec_template(self, data):
        """Нормализовать JSON-шаблон спецификации в dict (иначе None)."""
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except Exception:
                return None
        if not isinstance(data, dict):
            return None
        return data

    def _build_spec_sections_from_template(self, template, locale=None):
        """Разворачивает вложенный spec_template в ``{группа: {подпись: значение}}``.

        Формат шаблона::

            {"Основные": {"Температура, °С": "temp_range", "IP": "ip"}}

        Ключ — готовая подпись, значение — ключ поля реестра. Порядок — по
        вставке ключей (без ``order``). Значения локализуются для ``locale``.
        """
        by_key = {f.key: f for f in self._get_field_specs()}
        result = {}
        for group_title, fields in template.items():
            if not isinstance(fields, dict):
                continue
            group_fields = {}
            for label, key in fields.items():
                spec = by_key.get(key)
                if spec is None:
                    continue
                value = self._format_spec_value(spec, locale=locale)
                if value in (None, '') or value == []:
                    continue
                group_fields[label] = value
            if group_fields:
                result[group_title] = group_fields
        return result

    def _build_model_code_spec(self, locale=None):
        """Фоллбэк-спецификация: только артикул (``{model_code}``)."""
        code_spec = None
        for f in self._get_field_specs():
            if f.key == 'code' or f.placeholder == '{model_code}':
                code_spec = f
                break
        if code_spec is None:
            return {}
        value = self._resolve_field(code_spec)
        if value in (None, ''):
            return {}
        titles = _SECTION_TITLES.get(locale or DEFAULT_LOCALE, _SECTION_TITLES[DEFAULT_LOCALE])
        return {titles['main']: {titles['article']: value}}

    def _get_spec_template_i18n(self):
        """Переводы spec_template из ТОГО ЖЕ источника, откуда взят RU-шаблон.

        Цепочка как в ``_get_spec_template``: model_line.spec_template →
        EquipmentType.spec_template. Возвращает dict ({"ru": {...}, "en": {...}, ...})
        или None.
        """
        ml = getattr(self, 'model_line', None)
        if ml is not None and getattr(ml, 'spec_template', None):
            i18n = getattr(ml, 'spec_template_i18n', None)
            if isinstance(i18n, dict):
                return i18n
            return None
        et = self._get_equipment_type()
        if et is not None:
            i18n = getattr(et, 'spec_template_i18n', None)
            if isinstance(i18n, dict):
                return i18n
        return None

    def _get_spec_sections(self, fields=None, locale=None) -> dict:
        """Характеристики в виде ``{группа: {подпись: значение}}``.

        Если задан ``spec_template`` (model_line или EquipmentType) — строит из
        него; иначе — фоллбэк на ``{model_code}`` (один артикул). Для не-RU
        локали берётся ``spec_template_i18n[locale]`` (подписи переводятся).
        """
        locale = locale or DEFAULT_LOCALE
        template = self._parse_spec_template(self._get_spec_template())
        if locale != DEFAULT_LOCALE:
            i18n = self._get_spec_template_i18n()
            if isinstance(i18n, dict):
                loc_template = self._parse_spec_template(i18n.get(locale))
                if loc_template:
                    template = loc_template
        if template:
            return self._build_spec_sections_from_template(template, locale=locale)
        return self._build_model_code_spec(locale=locale)

    # ── Общие вспомогательные ──

    @staticmethod
    def _safe_m2m(instance, method_name):
        """Безопасный вызов секций M2M.

        На несохранённом инстансе (превью) M2M-менеджер требует pk — возвращаем [].
        """
        try:
            return getattr(instance, method_name)()
        except Exception:
            return []

    def _build_doc_dict(self, doc) -> dict:
        name = getattr(doc, 'name', '') or ''
        has_email = doc.variants.filter(role='email').exists()
        return {
            'id': doc.id,
            'name': name,
            'url': f"/api/media/{doc.id}/download/",
            'file_name': name,
            'preview_url': f"/api/media/{doc.id}/view/",
            'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
        }

    def _get_docs_section(self) -> list:
        """Техдокументация: своя → из серии (дедуп по id).

        На несохранённом инстансе (превью конструктора) собственная M2M
        недоступна — пропускаем её, но документы серии берём.
        """
        docs = []
        seen = set()
        if self.pk is not None:
            for doc in self.tech_docs.all():
                if doc.media_file and doc.id not in seen:
                    seen.add(doc.id)
                    docs.append(self._build_doc_dict(doc))
        if self.model_line and hasattr(self.model_line, 'tech_docs'):
            for doc in self.model_line.tech_docs.all():
                if doc.media_file and doc.id not in seen:
                    seen.add(doc.id)
                    docs.append(self._build_doc_dict(doc))
        return docs

    def _get_certs_section(self) -> list:
        """Сертификаты — из серии (у позиции нет своего поля)."""
        certs = []
        if self.model_line and hasattr(self.model_line, 'cert_docs'):
            cert_ids = list(
                self.model_line.cert_docs.filter(is_active=True).values_list('id', flat=True)
            )
            if cert_ids:
                from cert_doc.models import CertData
                for cert in CertData.objects.filter(id__in=cert_ids).select_related(
                        'media_item', 'cert_variety'):
                    media = getattr(cert, 'media_item', None)
                    if not media:
                        continue
                    has_email = media.variants.filter(role='email').exists()
                    variety_name = str(cert.cert_variety) if cert.cert_variety else ''
                    cert_code = getattr(cert, 'code', '') or ''
                    ml_name = self.model_line.name if self.model_line else ''
                    base_name = re.sub(r'[\\/*?:"<>|]', '_',
                                       f"{variety_name} {cert_code} для {ml_name}".strip())
                    dl_name = f"{base_name}.pdf"
                    email_name = f"{base_name} (сжат).pdf"
                    certs.append({
                        'id': media.id,
                        'name': getattr(cert, 'name', '') or '',
                        'file_name': dl_name,
                        'email_file_name': email_name,
                        'url': f"/api/media/{media.id}/download/?filename={quote(dl_name)}",
                        'preview_url': f"/api/media/{media.id}/view/",
                        'email_url': f"/api/media/{media.id}/download/?variant=email&filename={quote(email_name)}" if has_email else None,
                    })
        return certs

    def _get_model_line_summary(self, locale=None) -> dict:
        if not self.model_line:
            return None
        ml = self.model_line
        locale = locale or DEFAULT_LOCALE
        return {
            'id': ml.id,
            'name': ml.name,
            'code': getattr(ml, 'code', '') or '',
            'description': pick_i18n(
                getattr(ml, 'description_i18n', None), locale, fallback=ml.description or ''
            ),
            'brand': {
                'id': ml.brand.id,
                'name': ml.brand.name,
            } if getattr(ml, 'brand', None) else None,
        }

    def _get_sku_summary(self) -> dict:
        if not hasattr(self, 'sku') or not self.sku:
            return None
        return {
            'id': self.sku.id,
            'code': self.sku.code,
            'name': self.sku.name,
        }

    # ── Сборка to_dict ──

    def _get_display_i18n(self, locale) -> dict:
        """display_i18n[locale] айтема или None (нет поля/локали → fallback на RU-поля)."""
        di = getattr(self, 'display_i18n', None)
        if isinstance(di, dict):
            entry = di.get(locale)
            if isinstance(entry, dict):
                return entry
        return None

    def to_dict(self, locale=None) -> dict:
        locale = locale or DEFAULT_LOCALE
        disp = self._get_display_i18n(locale)
        name = (disp.get('name') if disp else None) or self.name or ''
        description = (disp.get('description') if disp else None) or self.description or ''
        title = (disp.get('title') if disp else None) or self.generate_title(locale)
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': name,
            'title': title,
            'image_alt': name,
            'description': description,
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(locale=locale),
            'sku': self._get_sku_summary(),
            'spec_download_url': self._get_spec_download_url(),
            'template_vars': tv,
            'sections': self._build_sections(tv, description=description, locale=locale),
        }

    def _get_spec_download_url(self) -> str:
        """URL для скачивания спецификации в .docx (или '')."""
        if not self.pk:
            return ''
        return (
            f'/api/core/catalog/spec-docx/'
            f'{self._meta.app_label}/{self._meta.model_name}/{self.pk}/'
        )

    def _build_sections(self, tv, description=None, locale=None) -> list:
        titles = _SECTION_TITLES.get(locale or DEFAULT_LOCALE, _SECTION_TITLES[DEFAULT_LOCALE])
        return [
            self._build_gallery_section(titles),
            self._build_specs_section(titles, locale),
            self._build_files_section('docs', titles['docs'],
                                      self._safe_m2m(self, '_get_docs_section'), 2),
            self._build_files_section('certs', titles['certs'],
                                      self._safe_m2m(self, '_get_certs_section'), 3),
            self._build_text_section('description', titles['description'],
                                     description if description is not None else (self.description or ''), 4),
        ]

    def _build_gallery_section(self, titles) -> dict:
        return {
            'key': 'images', 'title': titles['images'], 'type': 'gallery',
            'order': 0, 'data': self._safe_m2m(self, '_get_images_section'),
        }

    def _build_specs_section(self, titles, locale=None) -> dict:
        return {
            'key': 'specs', 'title': titles['specs'], 'type': 'specs',
            'order': 1, 'data': self._get_spec_sections(locale=locale),
        }

    def _build_files_section(self, key: str, title: str, data: list, order: int) -> dict:
        return {'key': key, 'title': title, 'type': 'files', 'order': order, 'data': data}

    def _build_text_section(self, key: str, title: str, data: str, order: int) -> dict:
        return {'key': key, 'title': title, 'type': 'text', 'order': order, 'data': data}


@checks.register('catalog')
def check_template_fields_declared(app_configs, **kwargs):
    """Требует явного TEMPLATE_FIELDS у моделей с ``requires_template_fields``."""
    errors = []
    for model in apps.get_models():
        if not getattr(model, 'requires_template_fields', False) or model._meta.abstract:
            continue
        if not getattr(model, 'TEMPLATE_FIELDS', None):
            errors.append(checks.Error(
                f"{model.__name__} должен явно определить TEMPLATE_FIELDS.",
                hint=("Добавьте TEMPLATE_FIELDS = (...) в модель или в отдельный "
                      "модуль *_fields.py и импортируйте его."),
                obj=model,
                id='catalog.E003',
            ))
    return errors

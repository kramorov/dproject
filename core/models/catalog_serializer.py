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

    def _get_spec_sections(self, fields=None) -> list:
        """Группы характеристик, выведенные из TEMPLATE_FIELDS (по ``group``).

        ``fields`` — подмножество ключей; иначе — ``SPEC_FIELD_KEYS`` (дефолт —
        все поля с ``group``). label/unit/type/order берутся из спецификации.
        """
        specs = self._get_field_specs()
        if not specs:
            return []
        keys = fields if fields is not None else getattr(self, 'SPEC_FIELD_KEYS', None)
        selected = self._lookup_specs(keys) if keys is not None else specs
        groups = {}
        order = []
        titles = getattr(self, 'SPEC_GROUP_TITLES', None) or {}
        for f in selected:
            if not f.group:
                continue
            if f.group not in groups:
                groups[f.group] = {
                    'key': f.group,
                    'title': titles.get(f.group, f.group),
                    'order': len(order) + 1,
                    'fields': [],
                }
                order.append(f.group)
            groups[f.group]['fields'].append({
                'key': f.key,
                'label': f.label or f.key,
                'value': self._resolve_field(f),
                'unit': f.unit,
                'type': f.type,
                'order': f.order,
            })
        return [groups[g] for g in order]

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
        """Техдокументация: своя → из серии (дедуп по id)."""
        docs = []
        seen = set()
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

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        ml = self.model_line
        return {
            'id': ml.id,
            'name': ml.name,
            'code': getattr(ml, 'code', '') or '',
            'description': ml.description or '',
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

    def to_dict(self) -> dict:
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'image_alt': self.name or '',
            'description': self.description or '',
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
            'template_vars': tv,
            'sections': self._build_sections(tv),
        }

    def _build_sections(self, tv) -> list:
        return [
            self._build_gallery_section(),
            self._build_specs_section(),
            self._build_files_section('docs', _('Документация'),
                                      self._safe_m2m(self, '_get_docs_section'), 2),
            self._build_files_section('certs', _('Сертификаты'),
                                      self._safe_m2m(self, '_get_certs_section'), 3),
            self._build_text_section('description', _('Описание'), self.description or '', 4),
        ]

    def _build_gallery_section(self) -> dict:
        return {
            'key': 'images', 'title': _('Изображения'), 'type': 'gallery',
            'order': 0, 'data': self._safe_m2m(self, '_get_images_section'),
        }

    def _build_specs_section(self) -> dict:
        return {
            'key': 'specs', 'title': _('Характеристики'), 'type': 'specs',
            'order': 1, 'groups': self._get_spec_sections(),
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

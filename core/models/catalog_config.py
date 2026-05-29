# core/models/catalog_config.py
"""
Unified catalog configuration.

FilterSet  — which filters, scoped or global, exact/compatible flag.
CatalogConfig — all configuration for one equipment type:
                model classes, filter sets per page, ORM hints, labels.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

from django.db.models import Model, QuerySet

from core.models.filter_definition import FilterDefinition


@dataclass
class FilterSet:
    """A named set of filter definitions for a specific page/scope.

    Attributes:
        definitions: FilterDefinition objects to expose on this page.
        scoped: If True, filter option values are limited to a model_line
                (queryset filtered by model_line_id).
        show_compatible: If True, the frontend may request exact/compatible
                         splitting via ?show_compatible=true.
    """
    definitions: List[FilterDefinition]
    scoped: bool = False
    show_compatible: bool = False


@dataclass
class CatalogConfig:
    """Complete configuration for one equipment catalog.

    Usage (gearbox example):

        GEARBOX_CONFIG = CatalogConfig(
            model_class=GearBox,
            model_line_class=GearBoxModelLine,
            filter_sets={
                'list': FilterSet(
                    definitions=[fd_ip, fd_temp_min, ...],
                    scoped=False,
                    show_compatible=True,
                ),
                'model_line': FilterSet(
                    definitions=[fd_ip, fd_temp_min, ...],  # no brand_id
                    scoped=True,
                    show_compatible=True,
                ),
                'quickselect': FilterSet(
                    definitions=[fd_material, fd_torque, fd_plate],
                    scoped=True,
                    show_compatible=False,
                ),
            },
            select_related=[...],
            prefetch_fields=[...],
            search_fields=[...],
            labels={'title': 'Редукторы', ...},
        )

    Visibility scope:
        Override apply_visibility_scope() to restrict queryset by partner
        or site settings (allowed brands/series).
    """

    # ── Models ──
    model_class: Type[Model]
    model_line_class: Optional[Type[Model]] = None

    # ── Filters per page (positive definition, no scope_exclude) ──
    filter_sets: Dict[str, FilterSet] = field(default_factory=dict)

    # ── ORM optimization hints ──
    select_related: List[str] = field(default_factory=list)
    prefetch_fields: List[str] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)

    # ── UI labels ──
    labels: Dict[str, str] = field(default_factory=dict)

    # ── Visibility scope (Layer 0) ──

    def apply_visibility_scope(self, queryset: QuerySet, request) -> QuerySet:
        """
        Restrict queryset to allowed brands/series before user filters.

        Default: no restrictions (all equipment visible).

        TODO: Implement partner/site settings.
              When CustomerSettings.catalog_scope is available, restrict by:
                - allowed brand IDs
                - allowed model_line IDs
              Example:
                partner = get_partner_from_request(request)
                allowed = partner.settings.get('catalog_scope', {})
                scope = allowed.get('gearbox', {})
                if scope.get('brands'):
                    queryset = queryset.filter(model_line__brand_id__in=scope['brands'])
                if scope.get('series'):
                    queryset = queryset.filter(model_line_id__in=scope['series'])
        """
        return queryset

    def get_filter_set(self, scope: str) -> FilterSet:
        """Return the FilterSet for a given scope, or the 'list' default."""
        return self.filter_sets.get(scope, self.filter_sets.get('list'))

    def get_scoped_queryset(self, model_line_id=None) -> QuerySet:
        """Return base queryset, optionally scoped to model_line."""
        qs = self.model_class.objects.filter(is_active=True)
        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)
        return qs
